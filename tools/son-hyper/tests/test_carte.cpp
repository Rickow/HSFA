// Banc de la carte musique (hsfa_musique.h) avec un vrai Z80 (z80.h de kosarev, MIT, C++11) et les pilotes d'origine.
// Aucune donnee de jeu dans le depot : images faites par rendu_partitions.py --zip (sfa_z80.bin, sfa_qs.bin, ...).
//   g++ -O2 -std=c++11 -I tools/son-hyper -I tools/son-hyper/tests -o test_carte tools/son-hyper/tests/test_carte.cpp
//   ./test_carte <dossier contenant sfa_z80.bin sfa_qs.bin sfa2_z80.bin sfa2_qs.bin> [sortie des WAV] [dossier paquet]
//   dossier paquet : hsfa_musique.bin et hsfa_musique_table.txt ecrits par paquet_fbneo.py (au lieu de la table du banc)
#include "z80.h"
#include "hsfa_musique.h"
#include <chrono>
#include <cmath>

using namespace hsfa_mus;
static int echecs = 0;
#define VERIFIE(c, ...) do { if (c) printf("  ok    "); else { printf("  ECHEC "); echecs++; } printf(__VA_ARGS__); printf("\n"); } while (0)

class z80k : public z80::z80_cpu<z80k>, public processeur {
public:
	typedef z80::z80_cpu<z80k> base;
	const uint8_t *rom = nullptr, *bnk = nullptr; uint8_t *c0 = nullptr, *f0 = nullptr;
	carte *ca = nullptr;
	int64_t ticks = 0, t0 = 0; int64_t fait = 0; bool ligne = false, dedans = false;

	z80::fast_u8 on_read(z80::fast_u16 a) {
		if (a < 0x8000) return rom[a];
		if (a < 0xC000) return bnk[a - 0x8000];
		if (a < 0xD000) return c0[a - 0xC000];
		if (a < 0xE000) return ca->io_lit(uint16_t(a));
		if (a < 0xF000) return 0;
		return f0[a - 0xF000];
	}
	void on_write(z80::fast_u16 a, z80::fast_u8 n) {
		if (a >= 0xC000 && a < 0xD000) c0[a - 0xC000] = uint8_t(n);
		else if (a >= 0xD000 && a < 0xE000) ca->io_ecrit(uint16_t(a), uint8_t(n));
		else if (a >= 0xF000) f0[a - 0xF000] = uint8_t(n);
	}
	void on_tick(unsigned t) { ticks += t; }

	void memoire(const uint8_t *r, const uint8_t *b, uint8_t *x, uint8_t *y) override { rom = r; bnk = b; c0 = x; f0 = y; }
	void banque(const uint8_t *p) override { bnk = p; }
	void reset() override { base::on_reset(); ligne = false; }
	void irq() override { ligne = true; }
	void execute(int32_t c) override {
		t0 = ticks; dedans = true;
		while (ticks - t0 < c) {
			if (ligne && on_handle_active_int()) ligne = false;
			on_step();
		}
		dedans = false; fait = ticks - t0;
	}
	int32_t ecoules() override { return int32_t(dedans ? ticks - t0 : fait); }
	size_t taille_etat() override { return sizeof(base) + 1; }
	void lit_etat(uint8_t *d) override { memcpy(d, static_cast<base *>(this), sizeof(base)); d[sizeof(base)] = ligne; }
	void ecrit_etat(const uint8_t *d) override { memcpy(static_cast<base *>(this), d, sizeof(base)); ligne = d[sizeof(base)] != 0; }
};

static std::vector<uint8_t> lit(const std::string &p) {
	std::vector<uint8_t> d; FILE *f = fopen(p.c_str(), "rb");
	if (!f) { fprintf(stderr, "%s introuvable\n", p.c_str()); exit(2); }
	uint8_t b[65536]; size_t n; while ((n = fread(b, 1, sizeof b, f)) > 0) d.insert(d.end(), b, b + n); fclose(f); return d;
}
static void wav(const std::string &p, const std::vector<int16_t> &s, int fr) {
	FILE *o = fopen(p.c_str(), "wb"); uint32_t n = uint32_t(s.size() * 2), v;
	fwrite("RIFF", 1, 4, o); v = 36 + n; fwrite(&v, 4, 1, o); fwrite("WAVEfmt ", 1, 8, o); v = 16; fwrite(&v, 4, 1, o);
	uint16_t h[2] = { 1, 2 }; fwrite(h, 2, 2, o); v = fr; fwrite(&v, 4, 1, o); v = fr * 4; fwrite(&v, 4, 1, o);
	uint16_t h2[2] = { 4, 16 }; fwrite(h2, 2, 2, o); fwrite("data", 1, 4, o); fwrite(&n, 4, 1, o); fwrite(s.data(), 2, s.size(), o); fclose(o);
}

static std::string PAQUET;
struct banc {
	carte c; z80k z;
	std::vector<uint8_t> rom, donnees; std::string table;
	bool prepare(const std::string &d) {
		std::vector<uint8_t> i1 = lit(d + "/sfa_z80.bin"), i2 = lit(d + "/sfa2_z80.bin"), q1 = lit(d + "/sfa_qs.bin"), q2 = lit(d + "/sfa2_qs.bin");
		rom.assign(0x800000, 0); memcpy(&rom[0], q1.data(), std::min<size_t>(q1.size(), 0x400000));
		memcpy(&rom[0x400000], q2.data(), std::min<size_t>(q2.size(), 0x400000));
		donnees = i1; donnees.insert(donnees.end(), i2.begin(), i2.end());
		char l[256];
		snprintf(l, sizeof l, "PILOTE sfa1 0 %zx %x 0 400000\n", i1.size(), carte::crc32(i1.data(), i1.size())); table += l;
		snprintf(l, sizeof l, "PILOTE sfa2 %zx %zx %x 400000 400000\n", i1.size(), i2.size(), carte::crc32(i2.data(), i2.size())); table += l;
		for (int k = 0; k < 12; k++) { snprintf(l, sizeof l, "%04X sfa1 %04X 100\n", 0x41 + k, 1 + k); table += l; }
		table += "004D sfa1 0032 100\n";
		for (int k = 0; k < 18; k++) { snprintf(l, sizeof l, "%04X sfa2 %04X 100\n", 0x51 + k, 1 + k); table += l; }
		table += "0063 sfa2 0035 100\n";
		if (!PAQUET.empty()) { std::vector<uint8_t> t = lit(PAQUET + "/hsfa_musique_table.txt"); table.assign(t.begin(), t.end()); donnees = lit(PAQUET + "/hsfa_musique.bin"); }
		z.ca = &c; c.taux = 48000; c.gain = 1.0f;
		if (!c.ouvre(table.data(), table.size(), donnees.data(), donnees.size())) { printf("table : %s\n", c.erreur.c_str()); return false; }
		return c.demarre(&z, rom.data(), uint32_t(rom.size()));
	}
	std::vector<int16_t> rend(double sec) { std::vector<int16_t> o(size_t(sec * 48000) * 2, 0); c.rend(o.data(), int(o.size() / 2)); return o; }
	std::vector<uint8_t> photo() { std::vector<uint8_t> d(c.taille_etat()); c.sauve(d.data()); return d; }
};
static double rms(const std::vector<int16_t> &v) { double s = 0; for (int16_t x : v) s += double(x) * x; return std::sqrt(s / (v.size() ? v.size() : 1)); }

int main(int argc, char **argv)
{
	if (argc < 2) { fprintf(stderr, "usage : %s dossier [sortie]\n", argv[0]); return 2; }
	std::string out = argc > 2 ? argv[2] : "";
	if (argc > 3) { PAQUET = argv[3]; printf("table et pilotes de %s\n", argv[3]); }
	printf("1. chargement et demarrage des pilotes\n");
	banc b;
	auto t0 = std::chrono::steady_clock::now();
	bool ok = b.prepare(argv[1]);
	double sd = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
	VERIFIE(ok && b.c.pilotes.size() == 2 && b.c.pilotes[0].pret && b.c.pilotes[1].pret, "2 pilotes demarres et photographies (%.2f s) %s", sd, b.c.erreur.c_str());
	VERIFIE(b.c.nb_codes() == 32, "table : %zu codes Hyper", b.c.nb_codes());
	VERIFIE(b.c.commande(0x0123, 0, 0, false) == PASSE, "code inconnu : PASSE");

	printf("2. lecture d'un morceau ZERO (0041 -> SFA1 01)\n");
	VERIFIE(b.c.commande(0x41, 0, 0, false) == REMPLACE_FF05, "0041 -> carte, FF05 au Z80 principal");
	t0 = std::chrono::steady_clock::now();
	std::vector<int16_t> a = b.rend(60);
	double s60 = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
	VERIFIE(rms(a) > 300, "60 s rendues, niveau RMS %.0f", rms(a));
	printf("  info  60 s en %.2f s de calcul (%.2f %% d'un coeur, Z80 de test)\n", s60, s60 / 60 * 100);
	if (!out.empty()) wav(out + "/carte_0041.wav", a, 48000);

	printf("3. changements de morceau : chaque depart repart de la photo du pilote\n");
	b.c.commande(0x51, 0, 0, false); std::vector<int16_t> z2 = b.rend(20);
	VERIFIE(rms(z2) > 300 && b.c.e.pilote == 1, "0051 -> SFA2, RMS %.0f", rms(z2));
	if (!out.empty()) wav(out + "/carte_0051.wav", z2, 48000);
	b.c.commande(0x41, 0, 0, false); std::vector<int16_t> a2 = b.rend(60);
	VERIFIE(a2 == a, "0041 rejoue apres 0051 : sortie identique a l'octet au premier depart");

	printf("4. etats de sauvegarde\n");
	b.c.commande(0x45, 0, 0, false); b.rend(10);
	std::vector<uint8_t> s = b.photo();
	std::vector<int16_t> A = b.rend(5);
	b.c.charge(s.data()); std::vector<int16_t> B = b.rend(5);
	VERIFIE(A == B, "etat recharge dans la meme carte : 5 s identiques (bloc de %zu octets)", s.size());
	banc b2; b2.prepare(argv[1]); b2.c.charge(s.data()); std::vector<int16_t> C = b2.rend(5);
	VERIFIE(A == C, "etat recharge dans une carte neuve : 5 s identiques");

	printf("5. arret, fondu, pause\n");
	b.c.commande(0xFF05, 0, 0, false); std::vector<int16_t> st = b.rend(1);
	VERIFIE(!b.c.e.actif && rms(st) == 0, "FF05 : carte arretee, silence");
	b.c.commande(0x42, 0, 0, false); b.rend(5);
	b.c.commande(0xFF07, 0, 0x0400, false);                      // fondu vers 0 en 63 images
	b.rend(2);
	int64_t gel = b.c.e.cyc;
	std::vector<int16_t> pz = b.rend(2);
	VERIFIE(b.c.e.pause && b.c.e.niveau == 0 && b.c.e.cyc == gel && rms(pz) == 0, "fondu a 0 : pause, Z80 gele (cycle %lld), silence", (long long)gel);
	b.c.commande(0xFF06, 255, 0x0400, false); std::vector<int16_t> rp = b.rend(3);
	VERIFIE(!b.c.e.pause && b.c.e.cyc > gel && rms(rp) > 100, "FF06 : reprise la ou la musique s'etait arretee (RMS %.0f)", rms(rp));
	b.c.commande(0x42, 0, 0, false); b.rend(1);
	b.c.commande(0x0010, 0, 0, true);                             // ZERO 3 : musique du flux ou du Z80 principal
	VERIFIE(!b.c.e.actif, "code musique d'un autre lecteur (flux) : la carte s'arrete");

	printf("6. sortie a 44,1 kHz\n");
	banc b3; b3.prepare(argv[1]); b3.c.taux = 44100; b3.c.commande(0x41, 0, 0, false);
	std::vector<int16_t> o44(size_t(44100 * 20) * 2, 0); b3.c.rend(o44.data(), 44100 * 20);
	VERIFIE(rms(o44) > 300 && std::fabs(double(b3.c.e.ech) / 20.0 - 60000000.0 / 2496.0) < 2, "44,1 kHz : %.1f echantillons QSound par seconde", double(b3.c.e.ech) / 20.0);

	printf("%s : %d echec(s)\n", echecs ? "ECHEC" : "OK", echecs);
	return echecs ? 1 : 0;
}
