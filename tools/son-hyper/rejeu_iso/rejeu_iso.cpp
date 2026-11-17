// hsfa_rejeu_iso -- runs an original CPS2 sound driver (Z80 image of the player's ISO: X_DATA e221 = SFA1, e250 = SFA2)
// offline and logs its QSound register writes, with the same sweep protocol as the workshop measurement that produced
// the replay table (one command every 240 frames after FF00, see gen_rejeu_iso.py). No game data in this file.
//
// Machine (CPS2, as emulated by MAME): Z80 at 8 MHz ; 0000-7FFF fixed ROM, 8000-BFFF bank window (region 0x10000 +
// bank * 0x4000, bank written to D003, 16 entries), C000-CFFF RAM shared with the 68000, D000/D001 QSound data,
// D002 QSound register (write = command to the DSP), D007 QSound status (0x80 = ready), F000-FFFF RAM.
// IRQ 0 every 32 000 cycles (250 Hz), held until taken. Video frame = 512 x 262 pixels at 8 MHz = 134 144 cycles.
// QSound ready model: a write to D002 clears "ready" ; the DSP takes the command at its next sample tick (sample period
// 2 496 clocks at 60 MHz = 41.6 us), which sets "ready" again (--modele 1) ; --modele 0 : always ready.
// All times are integers: Z80 cycles from power-on (journal), DSP phase in 1/120 MHz units (Z80 cycle = 15 units).
//
// Usage: hsfa_rejeu_iso IMAGE CODES JOURNAL [--modele 0|1] [--reset C] [--poignee C] [--image0 C] [--debut N]
//                       [--pas N] [--avance N] [--dsp U] [--cffe V]
//   IMAGE   Z80 image (0x48000 bytes, MAME "audiocpu" region layout)    CODES  commands, hex, separated by , or spaces
//   JOURNAL text, LF: "Q cycle reg value" (QSound write), "F cycle" (FF00 posted), "C cycle code" (command posted),
//           "E cycle" (end of the sweep) ; cycle = Z80 cycles since power-on
// Z80 emulator: z80.h (Ivan Kosarev, MIT, tools/son-hyper/tests/z80.LICENSE).
#include "z80.h"
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>

static const int64_t IRQ_PERIODE = 32000;          // 8 MHz / 250 Hz
static const int64_t IMAGE = 512 * 262;            // cycles per video frame (CPS2 raw screen at 8 MHz)
static const int64_t U_CYCLE = 15;                 // 120 MHz units per Z80 cycle
static const int64_t U_ECHANTILLON = 2496 * 2;     // QSound sample period: 2 496 clocks at 60 MHz, in 120 MHz units

struct reglages {
	int modele = 1;
	int64_t reset = 0;             // Z80 reset released by the 68000 (cycle)
	int64_t poignee = 8000000;     // 68000 handshake: CFFD = 0x88, CFFF = 0xFF, C00F = 0xFF (cycle)
	int64_t image0 = 0;            // frame n ends at image0 + (n - 1) * IMAGE (cycle) ; only its phase against the IRQ
	                               // grid (multiples of IRQ_PERIODE) and the DSP tick matters (see gen_rejeu_iso.py)
	int64_t debut = 1100, pas = 240, avance = 4;
	int64_t dsp = 0;               // phase of the DSP sample tick, 120 MHz units
	int cffe = 0;                  // byte left by the 68000 in CFFE (copied to F040 at each IRQ: 0 = mono)
};

class banc : public z80::z80_cpu<banc> {
public:
	typedef z80::z80_cpu<banc> base;
	std::vector<uint8_t> img;      // 0x50000 bytes
	uint8_t partage[0x1000], ram[0x1000];
	unsigned banque = 0;
	int64_t ticks = 0;
	bool ligne = false;
	int64_t prochaine_irq = 0;
	// QSound
	unsigned haut = 0, bas = 0;
	bool pret = true;
	int64_t pret_u = 0;
	reglages R;
	std::string sortie;

	z80::fast_u8 on_read(z80::fast_u16 a) {
		if (a < 0x8000) return img[a];
		if (a < 0xC000) return img[0x10000 + banque * 0x4000 + (a - 0x8000)];
		if (a < 0xD000) return partage[a - 0xC000];
		if (a == 0xD007) {
			if (!pret && ticks * U_CYCLE >= pret_u) pret = true;
			return pret ? 0x80 : 0x00;
		}
		if (a >= 0xF000) return ram[a - 0xF000];
		return 0;
	}
	void on_write(z80::fast_u16 a, z80::fast_u8 n) {
		if (a >= 0xC000 && a < 0xD000) partage[a - 0xC000] = uint8_t(n);
		else if (a >= 0xF000) ram[a - 0xF000] = uint8_t(n);
		else if (a == 0xD000) haut = n;
		else if (a == 0xD001) bas = n;
		else if (a == 0xD002) {
			ligne_q(n, (haut << 8) | bas);
			if (R.modele == 0) pret = true;
			else {                 // ready again at the first DSP sample tick strictly after the write
				int64_t u = ticks * U_CYCLE, k = (u - R.dsp) / U_ECHANTILLON;
				if (u - R.dsp < 0 && (u - R.dsp) % U_ECHANTILLON) k--;
				pret = false; pret_u = R.dsp + (k + 1) * U_ECHANTILLON;
			}
		}
		else if (a == 0xD003) banque = n & 0x0F;
	}
	void on_tick(unsigned t) { ticks += t; }

	// journal
	static void num(std::string &s, int64_t v) { char b[24]; int n = 0; if (v < 0) { s += '-'; v = -v; }
		do { b[n++] = char('0' + v % 10); v /= 10; } while (v); while (n) s += b[--n]; }
	static void hexa(std::string &s, unsigned v, int w) { static const char *H = "0123456789abcdef";
		for (int i = w - 1; i >= 0; i--) s += H[(v >> (4 * i)) & 15]; }
	void ligne_q(unsigned reg, unsigned val) { sortie += "Q "; num(sortie, ticks); sortie += ' '; hexa(sortie, reg, 2);
		sortie += ' '; hexa(sortie, val, 4); sortie += '\n'; }
	void ligne_e(char e, int code) { sortie += e; sortie += ' '; num(sortie, ticks);
		if (code >= 0) { sortie += ' '; hexa(sortie, unsigned(code), 4); } sortie += '\n'; }

	void tourne_jusqua(int64_t t) {
		while (ticks < t) {
			while (prochaine_irq <= ticks) { ligne = true; prochaine_irq += IRQ_PERIODE; }
			if (ligne && on_handle_active_int()) ligne = false;
			on_step();
		}
	}
	// mailbox as written by the 68000 (workshop sweep: C000 high, C001 low, parameters 0, then C00F = 0)
	void boite(int code) {
		static const int nuls[] = { 0x2, 0x3, 0x4, 0x6, 0x8, 0x9, 0xA, 0xB, 0xC };
		partage[0x000] = uint8_t(code >> 8); partage[0x001] = uint8_t(code);
		for (int o : nuls) partage[o] = 0;
		partage[0x007] = 0;
		partage[0x00F] = 0;
	}
};

static bool lit(const char *p, std::vector<uint8_t> &d) {
	FILE *f = fopen(p, "rb"); if (!f) return false;
	uint8_t b[65536]; size_t n; while ((n = fread(b, 1, sizeof b, f)) > 0) d.insert(d.end(), b, b + n);
	fclose(f); return true;
}

int main(int argc, char **argv) {
	if (argc < 4) {
		fprintf(stderr, "usage: hsfa_rejeu_iso IMAGE CODES JOURNAL [--modele 0|1] [--reset C] [--poignee C] [--image0 C] "
		                "[--debut N] [--pas N] [--avance N] [--dsp U] [--cffe V]\n");
		return 2;
	}
	static banc B;
	reglages &R = B.R;
	for (int i = 4; i + 1 < argc; i += 2) {
		std::string o = argv[i]; int64_t v = strtoll(argv[i + 1], nullptr, 0);
		if (o == "--modele") R.modele = int(v); else if (o == "--reset") R.reset = v; else if (o == "--poignee") R.poignee = v;
		else if (o == "--image0") R.image0 = v; else if (o == "--debut") R.debut = v; else if (o == "--pas") R.pas = v;
		else if (o == "--avance") R.avance = v; else if (o == "--dsp") R.dsp = v; else if (o == "--cffe") R.cffe = int(v);
		else { fprintf(stderr, "option inconnue / unknown option: %s\n", o.c_str()); return 2; }
	}
	std::vector<uint8_t> image, txt;
	if (!lit(argv[1], image) || image.size() != 0x48000) { fprintf(stderr, "%s: Z80 image of 0x48000 bytes expected\n", argv[1]); return 1; }
	if (!lit(argv[2], txt)) { fprintf(stderr, "%s: unreadable\n", argv[2]); return 1; }
	std::vector<int> codes;
	{
		std::string s(txt.begin(), txt.end()), m;
		for (size_t i = 0; i <= s.size(); i++) {
			char c = i < s.size() ? s[i] : ' ';
			if (isxdigit((unsigned char)c)) m += c;
			else if (!m.empty()) { codes.push_back(int(strtol(m.c_str(), nullptr, 16))); m.clear(); }
		}
	}
	if (codes.empty()) { fprintf(stderr, "%s: no command\n", argv[2]); return 1; }
	B.img = image; B.img.resize(0x50000, 0);
	memset(B.partage, 0, sizeof B.partage); memset(B.ram, 0, sizeof B.ram);
	B.on_reset();
	B.ticks = R.reset;
	B.prochaine_irq = (R.reset / IRQ_PERIODE + 1) * IRQ_PERIODE;
	B.partage[0xFFE] = uint8_t(R.cffe);
	B.sortie.reserve(16 << 20);
	auto fin_image = [&](int64_t n) { return R.image0 + (n - 1) * IMAGE; };

	B.tourne_jusqua(R.poignee);
	B.partage[0xFFD] = 0x88; B.partage[0xFFF] = 0xFF; B.partage[0x00F] = 0xFF;
	for (size_t k = 0; k < codes.size(); k++) {
		int64_t n = R.debut + int64_t(k) * R.pas;
		B.tourne_jusqua(fin_image(n)); B.ligne_e('F', -1); B.boite(0xFF00);
		B.tourne_jusqua(fin_image(n + R.avance)); B.ligne_e('C', codes[k]); B.boite(codes[k]);
	}
	B.tourne_jusqua(fin_image(R.debut + int64_t(codes.size()) * R.pas)); B.ligne_e('E', -1);
	FILE *o = fopen(argv[3], "wb");
	if (!o || fwrite(B.sortie.data(), 1, B.sortie.size(), o) != B.sortie.size() || fclose(o) != 0) {
		fprintf(stderr, "%s: write error\n", argv[3]); return 1;
	}
	return 0;
}
