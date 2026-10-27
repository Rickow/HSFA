// HSFA : lecteur de flux musique ADX (Y_DATA.BIN de l'Anthology PS2) pour le banc MAME sfa3hx et le coeur FBNeo HSFA.
// C++98 portable (MAME, FBNeo/libretro, MSVC), sans dependance, en-tete seul. Aucune donnee de jeu dans le code : le flux est lu dans le Y_DATA.BIN
// (ou l'ISO) de l'utilisateur, la correspondance code -> flux dans une table texte separee (gen_table_flux.py).
//
// Principe (comme le pilote son natif PS2 du module, exec. 0x5A9B40) : a chaque commande posee par le 68K dans la
// boite aux lettres QSound ($618001-$618019, $61801F = 0), commande() decide :
//   - code de MUSIQUE de la table, joue en flux (mode 1 : codes sans equivalent QSound ; mode 2 : toutes les musiques
//     sauf drapeau x) -> le flux ADX demarre et la commande transmise au Z80 devient FF05 (arret de la musique
//     QSound ; voix et bruitages intacts, verifie au banc) ;
//   - autre code de musique de la table -> le flux en cours s'arrete, la commande passe au Z80 ;
//   - FFxx -> applique au flux (FF00/FF05 arret, FF06/FF07 fondu en p images vers v/255, FF0C/FF0D fondu a 0) et
//     passe au Z80 ;
//   - le reste (bruitages, voix) passe au Z80 sans changement.
// Volume (pilote PS2, 0x155470) : amplitude = gain * (vol_table/127) * (niveau/127), niveau 0..127 ; fondu lineaire
// (0x155820) de l'indice courant (vol*niveau/127) vers 127*v/255 en 0xFFFF/p images ; niveau 0 => pause.
//
// Flux Ogg Vorbis (HSFA_FLUX_VORBIS, coeur FBNeo ; le fork MAME reste en ADX) : une entree de l'AFS peut etre un fichier
// Ogg Vorbis complet au lieu d'un ADX (reconnu a « OggS »). Boucle : commentaires LOOPSTART / LOOPEND (fin exclue) ou
// LOOPLENGTH, en echantillons, recopies de l'en-tete ADX par l'encodeur (tools/flux/flux_ogg.py). Decodeur stb_vorbis
// en memoire ; fichier charge par blocs en avance sur le decodeur ; boucle par stb_vorbis_seek (exact a l'echantillon).
// Etat : meme structure que l'ADX (etats de sauvegarde inchanges) : pos_abs = echantillon suivant dans le fichier,
// boucle_ok = boucles faites. Un anneau des ~2,7 s decodees evite tout seek au run-ahead et aux petits retours arriere.
#pragma once
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <string>
#include <vector>
#ifdef HSFA_FLUX_VORBIS
#define STB_VORBIS_HEADER_ONLY
#define STB_VORBIS_NO_STDIO
#define STB_VORBIS_NO_PUSHDATA_API
#include "stb_vorbis.c"
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#ifndef M_SQRT2
#define M_SQRT2 1.41421356237309504880
#endif
#if defined(__GNUC__)
#define HSFA_FLUX_PRINTF __attribute__((format(printf, 2, 3)))
#else
#define HSFA_FLUX_PRINTF
#endif

namespace hsfa_flux {

// libretro (file_stream_transforms.h : FILE = RFILE, fseek = rfseek sur 64 bits) ou stdio natif
#if defined(__LIBRETRO_SDK_FILE_STREAM_TRANSFORMS_H)
static inline int fseek64(FILE *f, uint64_t o) { return fseek(f, (int64_t)o, SEEK_SET) < 0 ? -1 : 0; }
#elif defined(_WIN32)
static inline int fseek64(FILE *f, uint64_t o) { return _fseeki64(f, (long long)o, SEEK_SET); }
#else
static inline int fseek64(FILE *f, uint64_t o) { return fseeko(f, (off_t)o, SEEK_SET); }
#endif

enum { PASSE = 0, REMPLACE_FF05 = 1 };
enum { DRAP_QSOUND = 1, DRAP_PAUSE = 2, DRAP_JAMAIS = 4 };

struct entree { int32_t fid; uint8_t vol; uint8_t drap; entree() : fid(-1), vol(0), drap(0) {} };

// etat sauvegardable (types simples, enregistres un par un par l'hote)
struct etat_t {
	int32_t actif, fid, pause;
	int32_t vol;                          // volume de la table (0-127)
	int32_t niveau;                       // niveau 0-127 (fondus)
	int32_t f_debut, f_cible, f_duree, f_reste;
	int32_t trame;                        // trame ADX suivante a decoder
	int32_t hist[2][2];
	int32_t boucle_ok, hist_boucle[2][2];
	int32_t hist_debut[2][2];             // historique AVANT la trame du tampon (reprise d'etat en 1 trame)
	int32_t ech;                          // echantillons (par canal) deja produits dans le tampon de trame courant
	int32_t n_ech;                        // echantillons valides dans le tampon de trame
	int32_t pos_abs;                      // echantillon absolu (par canal) du debut du tampon de trame
	int32_t cpt_tick;                     // echantillons de sortie depuis le dernier tick de 60 Hz
	int32_t frac;                         // reechantillonnage (16.16)
	int16_t prec[2], cour[2];
	float g_prec;                         // gain au tick precedent (rampe)
	etat_t() { memset(this, 0, sizeof(*this)); fid = -1; niveau = 127; }
};

class lecteur {
public:
	int mode;                             // 0 inactif, 1 complement, 2 toutes les musiques (PS2)
	float gain;                           // gain global (HSFA_FLUX_VOL en %)
	int max_niveau;
	int taux;                             // frequence de sortie (Hz)
	std::string erreur, journal_fichier;
	etat_t e;

	lecteur() : mode(0), gain(1.0f), max_niveau(127), taux(48000), m_f(NULL), m_j(NULL), m_charge(0), m_fid_charge(-1),
		m_freq(48000), m_ns(0), m_bs(18), m_can(2), m_spf(32), m_c1(0), m_c2(0), m_bcl(0), m_bdeb(0), m_bfin(0), m_ogg(0),
#ifdef HSFA_FLUX_VORBIS
		m_v(NULL), m_ls(0), m_le(0), m_dec_t(0), m_ann_deb(0), m_fin_t(-1), m_dec_p(0),
#endif
		m_debut(0)
	{ memset(m_trame, 0, sizeof(m_trame)); }
	~lecteur()
	{
		if (m_f) fclose(m_f);
		if (m_j) fclose(m_j);
#ifdef HSFA_FLUX_VORBIS
		if (m_v) stb_vorbis_close(m_v);
#endif
	}

	// ydata : Y_DATA.BIN, ou l'ISO de l'Anthology (Y_DATA.BIN cherche dans la racine ISO9660), ou 'fichier@decalage'
	bool ouvre(const char *ydata, const char *table)
	{
		if (!lit_table(table)) return false;
		return ouvre_y(ydata);
	}
	// table deja en memoire (ex. membre hsfa_flux_table.txt du zip du jeu ; arret au premier octet nul)
	bool ouvre_texte(const char *ydata, const char *texte, size_t n)
	{
		lit_table_texte(texte, n);
		return ouvre_y(ydata);
	}
	// ydata : Y_DATA.BIN, ISO, ou 'fichier@decalage' (AFS a ce decalage : membre hsfa_flux.bin stocke dans le zip)
	bool ouvre_y(const char *ydata)
	{
		if (m_f) { fclose(m_f); m_f = NULL; }
		std::string chemin(ydata);
		uint64_t base = 0;
		size_t at = chemin.rfind('@');
		if (at != std::string::npos && at > 0 && chemin.find('/', at) == std::string::npos) {
			base = strtoull(chemin.c_str() + at + 1, NULL, 16); chemin.resize(at);
		}
		m_f = fopen(chemin.c_str(), "rb");
		if (!m_f) { erreur = "Y_DATA introuvable : " + chemin; return false; }
		uint8_t h[8];
		if (!lire(base, h, 8)) { erreur = "Y_DATA illisible"; return false; }
		if (memcmp(h, "AFS", 4) != 0 && base == 0) {
			uint8_t pvd[6];
			if (lire(0x8000, pvd, 6) && !memcmp(pvd + 1, "CD001", 5)) base = cherche_iso("Y_DATA.BIN");
			if (!base || !lire(base, h, 8)) { erreur = "ni AFS ni ISO contenant Y_DATA.BIN"; return false; }
		}
		if (memcmp(h, "AFS", 4) != 0) { erreur = "en-tete AFS absent"; return false; }
		uint32_t n = rd32le(h + 4);
		if (n == 0 || n > 100000) { erreur = "AFS : nombre d'entrees invalide"; return false; }
		std::vector<uint8_t> t(8 * size_t(n));
		if (!lire(base + 8, t.data(), t.size())) { erreur = "AFS : table illisible"; return false; }
		m_off.resize(n); m_tai.resize(n);
		for (uint32_t i = 0; i < n; i++) { m_off[i] = base + rd32le(&t[8 * i]); m_tai[i] = rd32le(&t[8 * i + 4]); }
		return true;
	}
	size_t nb_flux() const { return m_off.size(); }
	size_t nb_codes() const { size_t k = 0; for (size_t i = 0; i < m_tab.size(); i++) if (m_tab[i].fid >= 0) k++; return k; }
	// code de musique connu de la table des flux (carte musique : un autre lecteur prend la musique)
	bool est_musique(uint16_t c) const { return c < m_tab.size() && m_tab[c].fid >= 0; }
	void ouvre_journal(const char *p) { if (p && *p) m_j = fopen(p, "w"); }

	// commande posee par le 68K (cmd = $618001/3, v = $618005, p = $618007/9). Rend PASSE ou REMPLACE_FF05.
	int commande(uint16_t cmd, uint8_t v, uint16_t p)
	{
		if (!mode || m_off.empty()) return PASSE;
		if (cmd >= 0xFF00) {
			int32_t dur = p ? int32_t(0xFFFF / p) : 0;
			switch (cmd & 0xFF) {
			case 0x00: case 0x05: arrete(); break;
			case 0x06: if (p) { fondu(dur, v); e.pause = 0; } break;
			case 0x07: if (p) fondu(dur, v); break;
			case 0x0C: case 0x0D: if (p) fondu(dur, 0); break;
			}
			trace("%04X p=%04X v=%02X (flux %s)\n", cmd, p, v, e.actif ? "actif" : "-");
			return PASSE;
		}
		if (cmd >= m_tab.size() || m_tab[cmd].fid < 0) return PASSE;
		const entree &x = m_tab[cmd];
		bool flux = !(x.drap & DRAP_JAMAIS) && (mode == 2 || !(x.drap & DRAP_QSOUND));
		if (!flux) { arrete(); trace("%04X -> Z80 (QSound)\n", cmd); return PASSE; }
		if (!demarre(x)) { trace("%04X -> flux Y%d ECHEC %s\n", cmd, x.fid, erreur.c_str()); return PASSE; }
		trace("%04X -> flux Y%d vol %d%s\n", cmd, x.fid, x.vol, e.pause ? " (en pause)" : "");
		return REMPLACE_FF05;
	}

	// mixe n echantillons stereo a la frequence taux (entrelaces) dans out (ajout sature)
	void rend(int16_t *out, int n)
	{
		for (int i = 0; i < n; i++) {
			int32_t lt = taux / 60;            // tick des fondus a 60 Hz (vsync PS2)
			if (++e.cpt_tick >= lt) { e.cpt_tick = 0; tick(); }
			if (!e.actif || e.pause) continue;
			float g1 = cible_gain();
			float g = e.g_prec + (g1 - e.g_prec) * (float(e.cpt_tick) / float(lt));
			// reechantillonnage lineaire (pas = freq du flux / freq de sortie)
			int32_t pas = int32_t((uint64_t(m_freq) << 16) / uint32_t(taux));
			e.frac += pas;
			while (e.frac >= 0x10000) {
				e.frac -= 0x10000;
				e.prec[0] = e.cour[0]; e.prec[1] = e.cour[1];
				if (!suivant(e.cour)) { e.actif = 0; trace("fin du flux Y%d\n", e.fid); break; }
			}
			if (!e.actif) break;
			float t = float(e.frac) / 65536.f;
			for (int c = 0; c < 2; c++) {
				float s = (e.prec[c] + (e.cour[c] - e.prec[c]) * t) * g;
				int32_t o = int32_t(out[2 * i + c]) + int32_t(lrintf(s));
				out[2 * i + c] = int16_t(o > 32767 ? 32767 : (o < -32768 ? -32768 : o));
			}
		}
	}

	// apres chargement d'un etat : recharger l'en-tete si le flux a change, puis redecoder la seule trame du tampon
	// a partir de l'historique d'avant cette trame (cout constant : compatible avec le « run-ahead » de RetroArch)
	void apres_chargement()
	{
		if (!e.actif || e.fid < 0) return;
		etat_t s = e;
		if (m_fid_charge != s.fid && !charge_entete(s.fid)) { e.actif = 0; return; }
		e = s;
#ifdef HSFA_FLUX_VORBIS
		if (m_ogg) {
			// etat ecrit par la version ADX (meme fid) : position = debut de trame + echantillons deja produits
			if (e.n_ech > 0) { e.pos_abs += e.ech; e.ech = e.n_ech = 0; e.boucle_ok = 0; }
			return;                       // suivant_ogg() reprend depuis l'anneau, ou par seek
		}
#endif
		if (e.n_ech > 0) {
			memcpy(e.hist, e.hist_debut, sizeof e.hist);
			if (!decode_trame(e.trame - 1)) { e.actif = 0; return; }
			e = s;
		}
	}

	// PCM stereo entrelace d'une entree entiere (sans repetition de boucle), pour l'encodeur et les controles
	// (tools/flux/fluxtool.cpp) : meme decodeur que la lecture. Rend la frequence et la boucle (fin exclue ; 0, 0 sans).
	bool pcm_entree(int32_t fid, std::vector<int16_t> &pcm, uint32_t &freq, int32_t &debut, int32_t &fin)
	{
		if (!charge_entete(fid)) return false;
		pcm.clear(); freq = m_freq; debut = fin = 0;
#ifdef HSFA_FLUX_VORBIS
		if (m_ogg) {
			if (!charge_jusqu(m_data.size())) { erreur = "lecture du flux"; return false; }
			stb_vorbis_seek_start(m_v);
			short b[4096];
			int r;
			while ((r = stb_vorbis_get_samples_short_interleaved(m_v, 2, b, 4096)) > 0) pcm.insert(pcm.end(), b, b + 2 * r);
			if (m_le) { debut = m_ls; fin = m_le; }
			m_fid_charge = -1;            // decodeur deplace : recharger avant de jouer
			return true;
		}
#endif
		e = etat_t();
		int32_t n = int32_t(m_ns);
		for (int32_t tr = 0; tr * int32_t(m_spf) < n; tr++) {
			if (!decode_trame(tr)) break;
			for (uint32_t j = 0; j < m_spf && tr * int32_t(m_spf) + int32_t(j) < n; j++) {
				pcm.push_back(m_trame[0][j]); pcm.push_back(m_trame[m_can > 1 ? 1 : 0][j]);
			}
		}
		if (m_bcl) { debut = m_bdeb; fin = m_bfin; }
		e = etat_t();
		return true;
	}

private:
	FILE *m_f, *m_j;
	std::vector<uint64_t> m_off; std::vector<uint32_t> m_tai;
	std::vector<entree> m_tab;
	// entree ADX courante
	std::vector<uint8_t> m_data; size_t m_charge; int32_t m_fid_charge;
	uint32_t m_freq, m_ns, m_bs, m_can, m_spf;
	int32_t m_c1, m_c2;
	int32_t m_bcl, m_bdeb, m_bfin;
	int16_t m_trame[2][64];
	int m_ogg;                            // entree courante : 0 ADX, 1 Ogg Vorbis
#ifdef HSFA_FLUX_VORBIS
	enum { ANNEAU = 1 << 17 };            // echantillons (par canal) gardes apres decodage : 2,73 s a 48 kHz
	stb_vorbis *m_v;
	int32_t m_ls, m_le;                   // boucle [m_ls, m_le) ; m_le = 0 : pas de boucle
	std::vector<int16_t> m_anneau;
	int64_t m_dec_t, m_ann_deb, m_fin_t;  // temps continu (boucles depliees) : prochain decode, plus ancien garde, fin
	int32_t m_dec_p;                      // position du decodeur dans le fichier
#endif

	static uint32_t rd32le(const uint8_t *p) { return p[0] | (p[1] << 8) | (p[2] << 16) | (uint32_t(p[3]) << 24); }
	static uint32_t rd32be(const uint8_t *p) { return (uint32_t(p[0]) << 24) | (p[1] << 16) | (p[2] << 8) | p[3]; }
	void trace(const char *fmt, ...) HSFA_FLUX_PRINTF
	{
		if (!m_j) return;
		char b[512]; va_list a; va_start(a, fmt); vsnprintf(b, sizeof(b), fmt, a); va_end(a);
		fwrite(b, 1, strlen(b), m_j); fflush(m_j);
	}
	bool lire(uint64_t o, void *d, size_t n) { return !fseek64(m_f, o) && fread(d, 1, n, m_f) == n; }

	uint64_t cherche_iso(const char *nom)
	{
		uint8_t pvd[2048];
		if (!lire(0x8000, pvd, 2048)) return 0;
		uint32_t lba = rd32le(pvd + 156 + 2), tai = rd32le(pvd + 156 + 10);
		if (tai > 1 << 20) return 0;
		std::vector<uint8_t> d(tai);
		if (!lire(uint64_t(lba) * 2048, d.data(), tai)) return 0;
		size_t ln = strlen(nom);
		for (size_t p = 0; p < tai;) {
			uint8_t l = d[p];
			if (!l) { p = (p / 2048 + 1) * 2048; continue; }
			if (p + 33 > tai) break;
			uint8_t nl = d[p + 32];
			if (nl >= ln && !memcmp(&d[p + 33], nom, ln) && (nl == ln || d[p + 33 + ln] == ';'))
				return uint64_t(rd32le(&d[p + 2])) * 2048;
			p += l;
		}
		return 0;
	}

	bool lit_table(const char *chemin)
	{
		FILE *f = fopen(chemin, "rb");
		if (!f) { erreur = std::string("table introuvable : ") + chemin; return false; }
		std::string t;
		char b[16384];
		size_t n;
		while ((n = fread(b, 1, sizeof b, f)) > 0) t.append(b, n);
		fclose(f);
		lit_table_texte(t.data(), t.size());
		return true;
	}
	void lit_table_texte(const char *texte, size_t taille)
	{
		m_tab.assign(0x1200, entree());
		const char *p = texte, *fin = texte + taille;
		char l[256];
		while (p < fin && *p) {
			size_t k = 0;
			while (p < fin && *p && k + 1 < sizeof l) { char c = *p++; l[k++] = c; if (c == '\n') break; }
			l[k] = 0;
			unsigned code, fid, vol; char dr[32] = "-";
			if (l[0] == '#' || sscanf(l, "%x %u %u %31s", &code, &fid, &vol, dr) < 3 || code >= 0x1200) continue;
			entree &x = m_tab[code];
			x.fid = int32_t(fid); x.vol = uint8_t(vol > 127 ? 127 : vol); x.drap = 0;
			for (char *c = dr; *c; c++) {
				if (*c == 'q') x.drap |= DRAP_QSOUND;
				else if (*c == 'p') x.drap |= DRAP_PAUSE;
				else if (*c == 'x') x.drap |= DRAP_JAMAIS;
			}
		}
	}

	bool charge_entete(int32_t fid)
	{
		if (fid < 0 || size_t(fid) >= m_off.size()) { erreur = "flux hors AFS"; return false; }
		uint32_t t = m_tai[fid];
		uint8_t h[0x40];
		if (t < 0x40 || !lire(m_off[fid], h, 0x40)) { erreur = "entree vide ou illisible"; return false; }
		if (!memcmp(h, "OggS", 4)) return charge_ogg(fid, t);
		if (h[0] != 0x80) { erreur = "en-tete ADX invalide"; return false; }
		uint32_t co = (h[2] << 8) | h[3];
		m_bs = h[5]; m_can = h[7]; m_freq = rd32be(h + 8); m_ns = rd32be(h + 12);
		uint32_t hp = (h[16] << 8) | h[17];
		if (h[4] != 3 || h[6] != 4 || m_bs < 3 || m_bs > 34 || m_can < 1 || m_can > 2 || !m_freq || h[19]) {
			erreur = "ADX non gere (type, chiffrement ou canaux)"; return false;
		}
		m_spf = (m_bs - 2) * 2;
		double z = cos(2.0 * M_PI * hp / m_freq), a = M_SQRT2 - z, b = M_SQRT2 - 1.0;
		double c = (a - sqrt((a + b) * (a - b))) / b;
		m_c1 = int32_t(c * 8192.0); m_c2 = int32_t(c * c * -4096.0);
		m_bcl = 0; m_bdeb = 0; m_bfin = int32_t(m_ns);
		if (h[18] == 4 && co >= 0x2C) { m_bcl = rd32be(h + 0x24); m_bdeb = rd32be(h + 0x28); m_bfin = rd32be(h + 0x30); }
		else if (h[18] == 3 && co >= 0x20) { m_bcl = rd32be(h + 0x18); m_bdeb = rd32be(h + 0x1C); m_bfin = rd32be(h + 0x24); }
		if (m_bcl && (m_bdeb >= m_bfin || uint32_t(m_bfin) > m_ns)) m_bcl = 0;
		if (co + 4 > t) { erreur = "ADX tronque"; return false; }
		m_data.assign(t - co - 4, 0);
		m_charge = 0;
		m_debut = m_off[fid] + co + 4;
		m_fid_charge = fid;
		m_ogg = 0;
		return true;
	}

	bool charge_ogg(int32_t fid, uint32_t t)
	{
#ifdef HSFA_FLUX_VORBIS
		if (m_v) { stb_vorbis_close(m_v); m_v = NULL; }
		m_fid_charge = -1;
		m_data.assign(t, 0); m_charge = 0; m_debut = m_off[fid];
		if (!charge_jusqu(AVANCE)) { erreur = "Ogg illisible"; return false; }
		int err = 0;
		m_v = stb_vorbis_open_memory(&m_data[0], int(t), &err, NULL);
		if (!m_v) { erreur = "Ogg Vorbis invalide"; return false; }
		stb_vorbis_info vi = stb_vorbis_get_info(m_v);
		if (vi.channels < 1 || vi.channels > 2 || !vi.sample_rate) { erreur = "Ogg : canaux ou frequence"; return false; }
		m_freq = vi.sample_rate; m_can = 2;
		m_ls = m_le = 0;
		int32_t lg = 0;
		stb_vorbis_comment c = stb_vorbis_get_comment(m_v);
		for (int i = 0; i < c.comment_list_length; i++) {
			const char *k = c.comment_list[i];
			if (!strncmp(k, "LOOPSTART=", 10) || !strncmp(k, "loopstart=", 10)) m_ls = atoi(k + 10);
			else if (!strncmp(k, "LOOPEND=", 8) || !strncmp(k, "loopend=", 8)) m_le = atoi(k + 8);
			else if (!strncmp(k, "LOOPLENGTH=", 11) || !strncmp(k, "looplength=", 11)) lg = atoi(k + 11);
		}
		if (!m_le && lg > 0) m_le = m_ls + lg;
		if (m_ls < 0 || m_le <= m_ls) m_ls = m_le = 0;
		m_anneau.assign(2 * size_t(ANNEAU), 0);
		m_dec_t = m_ann_deb = 0; m_fin_t = -1; m_dec_p = 0;
		m_fid_charge = fid;
		m_ogg = 1;
		return true;
#else
		(void)fid; (void)t;
		erreur = "flux Ogg Vorbis : coeur compile sans HSFA_FLUX_VORBIS";
		return false;
#endif
	}
	enum { AVANCE = 0x20000 };            // octets lus en avance sur le decodeur (une page Ogg fait au plus ~64 Ko)
	uint64_t m_debut;
	// lecture paresseuse par blocs de 64 Ko (pas d'a-coup au demarrage d'un flux)
	bool charge_jusqu(size_t fin)
	{
		if (fin > m_data.size()) fin = m_data.size();
		while (m_charge < fin) {
			size_t n = m_data.size() - m_charge;
			if (n > 0x10000) n = 0x10000;
			if (!lire(m_debut + m_charge, &m_data[m_charge], n)) return false;
			m_charge += n;
		}
		return true;
	}

	bool demarre(const entree &x)
	{
		if (!charge_entete(x.fid)) { e.actif = 0; return false; }
		e = etat_t();
		e.actif = 1; e.fid = x.fid; e.vol = x.vol; e.niveau = max_niveau;
		e.pause = (x.drap & DRAP_PAUSE) ? 1 : 0;
		e.g_prec = cible_gain();
		e.frac = 0x10000;             // premier echantillon tire immediatement
		return true;
	}
	void arrete() { if (e.actif) trace("arret du flux Y%d\n", e.fid); e.actif = 0; }
	void fondu(int32_t dur, uint8_t v)
	{
		if (!e.actif) return;
		e.f_debut = e.vol * e.niveau / 127;      // le PS2 repart de l'indice courant (0x155630 : +32 = +24)
		e.f_cible = max_niveau * v / 255;
		e.f_duree = e.f_reste = dur;
	}
	void tick()
	{
		e.g_prec = cible_gain();
		if (!e.actif || e.f_reste <= 0) return;
		e.f_reste--;
		int32_t s = (e.f_debut << 8) + (e.f_cible - e.f_debut) * ((e.f_duree - e.f_reste) << 8) / e.f_duree;
		e.niveau = s >= 0 ? s >> 8 : (s + 0xFF) >> 8;
		if (e.niveau > max_niveau) e.niveau = max_niveau;
		if (s == 0) { e.pause = 1; trace("fondu a 0 : pause du flux Y%d\n", e.fid); }
	}
	float cible_gain() const { return gain * float(e.vol) / 127.f * float(e.niveau) / 127.f; }

	bool decode_trame(int32_t tr)
	{
		size_t o = size_t(tr) * m_can * m_bs;
		if (!charge_jusqu(o + m_can * m_bs + 0x10000) || o + m_can * m_bs > m_data.size()) return false;
		if (m_bcl && tr == m_bdeb / int32_t(m_spf) && !e.boucle_ok) {
			memcpy(e.hist_boucle, e.hist, sizeof e.hist); e.boucle_ok = 1;
		}
		for (uint32_t k = 0; k < m_can; k++) {
			const uint8_t *p = &m_data[o + k * m_bs];
			int32_t sc = ((p[0] << 8) | p[1]) + 1, h1 = e.hist[k][0], h2 = e.hist[k][1];
			for (uint32_t j = 0; j < m_bs - 2; j++)
				for (int q = 0; q < 2; q++) {
					int32_t nib = q ? (p[2 + j] & 15) : (p[2 + j] >> 4);
					if (nib > 7) nib -= 16;
					int32_t s = nib * sc + ((m_c1 * h1 + m_c2 * h2) >> 12);
					s = s > 32767 ? 32767 : (s < -32768 ? -32768 : s);
					m_trame[k][2 * j + q] = int16_t(s); h2 = h1; h1 = s;
				}
			e.hist[k][0] = h1; e.hist[k][1] = h2;
		}
		return true;
	}
#ifdef HSFA_FLUX_VORBIS
	// temps continu (boucles depliees) d'une position du fichier apres n boucles
	int64_t temps(int32_t pos, int32_t n) const
	{
		if (!m_le || n <= 0) return pos;
		return int64_t(m_le) + int64_t(n - 1) * (m_le - m_ls) + (pos - m_ls);
	}
	void place(int32_t pos, int64_t t)
	{
		charge_jusqu(m_data.size());
		stb_vorbis_seek(m_v, unsigned(pos < 0 ? 0 : pos));
		m_dec_p = pos; m_dec_t = m_ann_deb = t; m_fin_t = -1;
	}
	bool decode_bloc()
	{
		if (m_fin_t >= 0 && m_dec_t >= m_fin_t) return false;
		int32_t n = 1024;
		if (m_le && m_le - m_dec_p < n) n = m_le - m_dec_p;
		charge_jusqu(size_t(stb_vorbis_get_file_offset(m_v)) + AVANCE);
		short b[2 * 1024];
		int r = n > 0 ? stb_vorbis_get_samples_short_interleaved(m_v, 2, b, 2 * n) : 0;
		if (r <= 0) { m_fin_t = m_dec_t; return false; }
		for (int i = 0; i < r; i++) {
			size_t k = size_t((m_dec_t + i) & (ANNEAU - 1)) * 2;
			m_anneau[k] = b[2 * i]; m_anneau[k + 1] = b[2 * i + 1];
		}
		m_dec_t += r; m_dec_p += r;
		if (m_dec_t - m_ann_deb > ANNEAU) m_ann_deb = m_dec_t - ANNEAU;
		if (m_le && m_dec_p >= m_le) {
			charge_jusqu(m_data.size());
			stb_vorbis_seek(m_v, unsigned(m_ls)); m_dec_p = m_ls;
		}
		return true;
	}
	bool suivant_ogg(int16_t *s)
	{
		int64_t t = temps(e.pos_abs, e.boucle_ok);
		if (t < m_ann_deb || t > m_dec_t + 24000) place(e.pos_abs, t);   // hors de l'anneau : seek
		while (t >= m_dec_t) if (!decode_bloc()) return false;
		size_t k = size_t(t & (ANNEAU - 1)) * 2;
		s[0] = m_anneau[k]; s[1] = m_anneau[k + 1];
		if (++e.pos_abs >= m_le && m_le) { e.pos_abs = m_ls; e.boucle_ok++; }
		return true;
	}
#endif
	// echantillon suivant (stereo) du flux, boucle comprise
	bool suivant(int16_t *s)
	{
#ifdef HSFA_FLUX_VORBIS
		if (m_ogg) return suivant_ogg(s);
#endif
		int32_t fin = m_bcl ? m_bfin : int32_t(m_ns);
		if (e.pos_abs + e.ech >= fin) {
			if (!m_bcl || !e.boucle_ok) return false;
			int32_t tr = m_bdeb / int32_t(m_spf);
			memcpy(e.hist, e.hist_boucle, sizeof e.hist);
			memcpy(e.hist_debut, e.hist, sizeof e.hist);
			if (!decode_trame(tr)) return false;
			e.trame = tr + 1; e.pos_abs = tr * int32_t(m_spf); e.n_ech = m_spf; e.ech = m_bdeb - e.pos_abs;
		}
		if (e.ech >= e.n_ech) {
			memcpy(e.hist_debut, e.hist, sizeof e.hist);
			if (!decode_trame(e.trame)) return false;
			e.pos_abs = e.trame * int32_t(m_spf); e.trame++; e.n_ech = m_spf; e.ech = 0;
		}
		s[0] = m_trame[0][e.ech];
		s[1] = m_trame[m_can > 1 ? 1 : 0][e.ech];
		e.ech++;
		return true;
	}
};

} // namespace hsfa_flux
