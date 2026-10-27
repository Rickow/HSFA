// HSFA : « carte musique » du coeur FBNeo (docs/rapports/PLAN-PARTITIONS-HYPER.md). Les musiques ZERO (SFA1) et
// ZERO 2 (SFA2) d'Hyper sont jouees par leurs pilotes son Z80 d'origine (e221 / e250 de X_DATA.BIN) sur un QSound
// dedie (hsfa_qsound.h) qui lit les echantillons dans la ROM du rejeu (e222 en +0, e251 en +4 Mo).
// C++98, en-tete seul, sans dependance au coeur : le Z80 est fourni par l'hote (classe processeur ; coeur FBNeo : Zet,
// banc : z80.h de kosarev). Deterministe : meme suite de commandes et d'images -> meme sortie.
//
// Deroulement (comme le banc tools/son-hyper/mesure_boucles.py, valide) :
//   - au chargement, chaque pilote demarre une fois : poignee de main (CFFD = 0x88, CFFF = 0xFF, C00F = 0xFF) puis
//     1 s d'initialisation ; son etat (registres, RAM C000-CFFF / F000-FFFF, banque, QSound) est photographie ;
//   - a la commande d'un morceau : photo du pilote restauree, commande postee (C000-C001 = code, C00F = 0) au rendu
//     suivant ; le Z80 principal recoit FF05 (sa musique s'arrete) ;
//   - Z80 a 8 MHz, IRQ tenue toutes les 32 000 cycles (250 Hz) ; ecritures QSound (D000/D001 donnee, D002 registre)
//     datees au cycle et appliquees avant l'echantillon QSound de leur instant (24 038 Hz) ; sortie reechantillonnee
//     vers la frequence de l'hote et ajoutee (saturee) ;
//   - FF00/05 arret, FF06/07 fondu en p images vers v/255, FF0C/0D fondu a 0, niveau 0 = pause (Z80 et QSound
//     geles) : meme logique que le lecteur de flux (hsfa_flux.h), donc que le pilote natif PS2.
#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <vector>
#include "hsfa_qsound.h"

namespace hsfa_mus {

enum { PASSE = 0, REMPLACE_FF05 = 1 };
static const int32_t CYC_IRQ = 32000;                // 8 MHz / 250 Hz
static const double CYC_ECH = 332.8;                 // cycles Z80 par echantillon QSound : 8 MHz * 2496 / 60 MHz
static const int64_t PAS_QS = int64_t(60000000.0 / 2496.0 * 65536.0 + 0.5);   // 24 038,46 Hz en 16.16 (1 575 385)

// Z80 de l'hote. La carte donne la memoire : ROM 0000-7FFF, banque 8000-BFFF, RAM C000-CFFF et F000-FFFF ;
// D000-DFFF passe par carte::io_lit / io_ecrit (a appeler par l'hote).
class processeur {
public:
	virtual ~processeur() {}
	virtual void memoire(const uint8_t *rom, const uint8_t *banque, uint8_t *ram_c0, uint8_t *ram_f0) = 0;
	virtual void banque(const uint8_t *p) = 0;        // peut etre appele pendant execute()
	virtual void reset() = 0;
	virtual void irq() = 0;                           // ligne IRQ tenue jusqu'a sa prise en compte (RST 38)
	virtual void execute(int32_t cycles) = 0;         // au moins `cycles` cycles (fin d'instruction)
	virtual int32_t ecoules() = 0;                    // cycles faits depuis le debut du dernier execute()
	virtual size_t taille_etat() = 0;
	virtual void lit_etat(uint8_t *d) = 0;
	virtual void ecrit_etat(const uint8_t *d) = 0;
};

struct ecriture { int64_t cyc; uint16_t val; uint8_t reg, pad; };

enum { N_ECR = 512, N_ATT = 8 };

// etat sauvegardable (types simples)
struct etat_t {
	int32_t actif, pilote, pause;
	int32_t niveau, f_debut, f_cible, f_duree, f_reste, cpt_tick;
	int32_t gain;                                     // % du morceau (table)
	float g_prec;
	int32_t banque;
	int32_t cyc_irq;                                  // cycles avant la prochaine IRQ
	int64_t cyc;                                      // horloge Z80 depuis le debut du morceau
	int64_t ech;                                      // echantillons QSound produits depuis le debut du morceau
	int32_t frac;                                     // reechantillonnage (16.16)
	int16_t prec[2], cour[2];
	uint8_t hi, lo, pad[2];
	int32_t n_att; int32_t att[N_ATT];                // a faire au prochain rendu : (pilote << 16) | code ; -1 arret
	int32_t n_ecr, i_ecr; ecriture ecr[N_ECR];        // ecritures QSound en attente (cycle > dernier echantillon)
	etat_t() { memset(this, 0, sizeof(*this)); pilote = -1; niveau = 127; }
};

struct pilote_t {
	std::string nom;
	std::vector<uint8_t> image;                       // region audiocpu au format MAME (banques en 0x10000 + 0x4000 b)
	uint32_t rom_off, rom_tai;                        // echantillons dans la ROM fournie (rejeu : SFA1 0, SFA2 4 Mo)
	int pret;
	std::vector<uint8_t> photo_cpu, photo_c0, photo_f0;
	int32_t photo_banque;
	hsfa_qs::etat_t photo_qs;
	pilote_t() : rom_off(0), rom_tai(0), pret(0), photo_banque(0) { memset(&photo_qs, 0, sizeof(photo_qs)); }
};

struct entree { int32_t pilote; uint16_t code; int32_t gain; entree() : pilote(-1), code(0), gain(100) {} };

class carte {
public:
	etat_t e;
	uint8_t ram_c0[0x1000], ram_f0[0x1000];
	hsfa_qs::qsound qs;
	std::vector<pilote_t> pilotes;
	std::string erreur;
	float gain;                                       // gain global (coeur : Cps2Volume / 39)
	int taux;                                         // frequence de sortie
	int actif_global;                                 // 0 : la carte ne prend aucune commande

	carte() : gain(1.0f), taux(48000), actif_global(1), m_p(NULL), m_rom(NULL), m_rom_tai(0), m_tab(0x1200)
	{ memset(ram_c0, 0, sizeof ram_c0); memset(ram_f0, 0, sizeof ram_f0); }

	// --- configuration -----------------------------------------------------------------------------------------
	// table texte : « PILOTE nom decalage taille crc32 rom_off rom_tai » (images dans `donnees`) puis
	// « code_hyper nom_pilote code_pilote gain_% » ; # = commentaire. Rend false et `erreur` si invalide.
	bool ouvre(const char *texte, size_t n, const uint8_t *donnees, size_t taille_donnees)
	{
		const char *p = texte, *fin = texte + n;
		char l[256];
		while (p < fin && *p) {
			size_t k = 0;
			while (p < fin && *p && k + 1 < sizeof l) { char c = *p++; l[k++] = c; if (c == '\n') break; }
			l[k] = 0;
			if (l[0] == '#' || l[0] == '\r' || l[0] == '\n' || !l[0]) continue;
			char nom[32]; unsigned dec, tai, crc, ro, rt, code, cp, g;
			if (sscanf(l, "PILOTE %31s %x %x %x %x %x", nom, &dec, &tai, &crc, &ro, &rt) == 6) {
				if (size_t(dec) + tai > taille_donnees || tai < 0x8000) { erreur = std::string("pilote hors donnees : ") + nom; return false; }
				if (crc32(donnees + dec, tai) != crc) { erreur = std::string("CRC du pilote ") + nom; return false; }
				pilote_t pl; pl.nom = nom; pl.image.assign(donnees + dec, donnees + dec + tai);
				if (pl.image.size() < 0x50000) pl.image.resize(0x50000, 0);
				pl.rom_off = ro; pl.rom_tai = rt;
				pilotes.push_back(pl);
			} else if (sscanf(l, "%x %31s %x %u", &code, nom, &cp, &g) == 4 && code < m_tab.size()) {
				int32_t k2 = indice(nom);
				if (k2 < 0) { erreur = std::string("pilote inconnu dans la table : ") + nom; return false; }
				m_tab[code].pilote = k2; m_tab[code].code = uint16_t(cp); m_tab[code].gain = int32_t(g);
			}
		}
		if (pilotes.empty()) { erreur = "aucun pilote"; return false; }
		return true;
	}
	size_t nb_codes() const { size_t k = 0; for (size_t i = 0; i < m_tab.size(); i++) if (m_tab[i].pilote >= 0) k++; return k; }
	bool connait(uint16_t code) const { return code < m_tab.size() && m_tab[code].pilote >= 0 && pilotes[m_tab[code].pilote].pret; }

	// ROM d'echantillons (rejeu) et Z80 de l'hote, puis demarrage et photo de chaque pilote
	bool demarre(processeur *p, const uint8_t *rom, uint32_t taille)
	{
		m_p = p; m_rom = rom; m_rom_tai = taille;
		for (size_t k = 0; k < pilotes.size(); k++) {
			pilote_t &pl = pilotes[k];
			if (size_t(pl.rom_off) + pl.rom_tai > taille) { erreur = "echantillons hors ROM : " + pl.nom; return false; }
			e = etat_t();
			memset(ram_c0, 0, sizeof ram_c0); memset(ram_f0, 0, sizeof ram_f0);
			memset(&qs.c, 0, sizeof(qs.c));                       // QSound neuf (pas de copie : reg_map pointe dans qs.c)
			qs.fixe_rom(rom + pl.rom_off, pl.rom_tai); qs.reset();
			e.pilote = int32_t(k); e.banque = 0;
			m_p->memoire(&pl.image[0], banque_ptr(0), ram_c0, ram_f0);
			m_p->reset();
			avance_libre(int64_t(CYC_IRQ) * 25);                  // 0,1 s : le pilote ecrit 0x77 en CFFF et attend
			ram_c0[0xFFD] = 0x88; ram_c0[0xFFF] = 0xFF; ram_c0[0x00F] = 0xFF;
			avance_libre(int64_t(CYC_IRQ) * 250);                 // 1 s d'initialisation
			pl.photo_cpu.resize(m_p->taille_etat()); m_p->lit_etat(&pl.photo_cpu[0]);
			pl.photo_c0.assign(ram_c0, ram_c0 + 0x1000); pl.photo_f0.assign(ram_f0, ram_f0 + 0x1000);
			pl.photo_banque = e.banque; pl.photo_qs = qs.c;
			pl.pret = 1;
		}
		e = etat_t();
		return true;
	}

	// --- commandes (posees par le 68K, $61801F = 0) -------------------------------------------------------------
	// musique : le code est une musique connue d'un autre lecteur (flux) ; la carte s'arrete alors.
	int commande(uint16_t cmd, uint8_t v, uint16_t p, bool musique)
	{
		if (cmd >= 0xFF00) {
			if (!e.actif) return PASSE;
			int32_t dur = p ? int32_t(0xFFFF / p) : 0;
			switch (cmd & 0xFF) {
			case 0x00: case 0x05: arrete(); break;
			case 0x06: if (p) { fondu(dur, v); e.pause = 0; } break;
			case 0x07: if (p) fondu(dur, v); break;
			case 0x0C: case 0x0D: if (p) fondu(dur, 0); break;
			}
			return PASSE;
		}
		if (actif_global && connait(cmd)) {
			const entree &x = m_tab[cmd];
			e.actif = 1; e.pause = 0; e.niveau = 127; e.f_reste = 0; e.gain = x.gain;
			e.g_prec = cible_gain();
			if (e.n_att < N_ATT) e.att[e.n_att++] = (x.pilote << 16) | x.code;
			return REMPLACE_FF05;
		}
		if (musique) arrete();
		return PASSE;
	}
	void arrete() { e.actif = 0; e.n_att = 0; }

	// --- rendu : n echantillons stereo a `taux`, ajoutes (satures) a out (out peut etre NULL : temps qui passe) ----
	void rend(int16_t *out, int n)
	{
		if (!m_p) return;
		for (int32_t a = 0; a < e.n_att; a++) {
			int32_t k = e.att[a] >> 16, code = e.att[a] & 0xFFFF;
			if (k >= 0 && size_t(k) < pilotes.size() && pilotes[k].pret) restaure(k, uint16_t(code));
		}
		e.n_att = 0;
		int32_t lt = taux / 60;
		int32_t pas = int32_t((PAS_QS + taux / 2) / taux);
		for (int i = 0; i < n; i++) {
			if (++e.cpt_tick >= lt) { e.cpt_tick = 0; tick(); }
			if (!e.actif || e.pause) continue;
			float g1 = cible_gain();
			float g = e.g_prec + (g1 - e.g_prec) * (float(e.cpt_tick) / float(lt));
			e.frac += pas;
			while (e.frac >= 0x10000) {
				e.frac -= 0x10000;
				e.prec[0] = e.cour[0]; e.prec[1] = e.cour[1];
				echantillon(e.cour);
			}
			if (!out) continue;
			float t = float(e.frac) / 65536.f;
			for (int c = 0; c < 2; c++) {
				float s = (e.prec[c] + (e.cour[c] - e.prec[c]) * t) * g;
				int32_t o = int32_t(out[2 * i + c]) + int32_t(s >= 0 ? s + 0.5f : s - 0.5f);
				out[2 * i + c] = int16_t(o > 32767 ? 32767 : (o < -32768 ? -32768 : o));
			}
		}
	}

	// --- acces memoire du Z80 (D000-DFFF) -------------------------------------------------------------------------
	uint8_t io_lit(uint16_t a) { return a == 0xD007 ? 0x80 : 0x00; }   // QSound toujours pret (comme le banc)
	void io_ecrit(uint16_t a, uint8_t v)
	{
		switch (a) {
		case 0xD000: e.hi = v; break;
		case 0xD001: e.lo = v; break;
		case 0xD002: {
			ecriture w; w.cyc = e.cyc + m_p->ecoules(); w.reg = v; w.val = uint16_t((e.hi << 8) | e.lo); w.pad = 0;
			if (e.n_ecr >= N_ECR) { qs.ecrit(w.reg, w.val); break; }      // ne devrait pas arriver
			e.ecr[e.n_ecr++] = w;
			break;
		}
		case 0xD003: e.banque = v & 0x0F; m_p->banque(banque_ptr(e.banque)); break;
		}
	}

	// --- etat ---------------------------------------------------------------------------------------------------
	// bloc unique, de taille fixe pour un processeur donne : etat, RAM, QSound, registres du Z80
	size_t taille_etat() const { return sizeof(e) + sizeof(ram_c0) + sizeof(ram_f0) + sizeof(qs.c) + (m_p ? m_p->taille_etat() : 0); }
	void sauve(uint8_t *d)
	{
		memcpy(d, &e, sizeof e); d += sizeof e;
		memcpy(d, ram_c0, sizeof ram_c0); d += sizeof ram_c0;
		memcpy(d, ram_f0, sizeof ram_f0); d += sizeof ram_f0;
		memcpy(d, &qs.c, sizeof qs.c); d += sizeof qs.c;
		if (m_p) m_p->lit_etat(d);
	}
	void charge(const uint8_t *d)
	{
		memcpy(&e, d, sizeof e); d += sizeof e;
		memcpy(ram_c0, d, sizeof ram_c0); d += sizeof ram_c0;
		memcpy(ram_f0, d, sizeof ram_f0); d += sizeof ram_f0;
		memcpy(&qs.c, d, sizeof qs.c); d += sizeof qs.c;
		if (m_p) m_p->ecrit_etat(d);
		apres_chargement();
	}
	// remet en place la memoire du pilote courant (apres un chargement d'etat fait par l'hote)
	void apres_chargement()
	{
		if (!m_p || e.pilote < 0 || size_t(e.pilote) >= pilotes.size()) return;
		pilote_t &pl = pilotes[e.pilote];
		qs.fixe_rom(m_rom + pl.rom_off, pl.rom_tai);
		m_p->memoire(&pl.image[0], banque_ptr(e.banque), ram_c0, ram_f0);
	}

	static uint32_t crc32(const uint8_t *d, size_t n)
	{
		uint32_t c = 0xFFFFFFFFu;
		for (size_t i = 0; i < n; i++) {
			c ^= d[i];
			for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
		}
		return ~c;
	}

private:
	processeur *m_p;
	const uint8_t *m_rom; uint32_t m_rom_tai;
	std::vector<entree> m_tab;

	int32_t indice(const char *nom) const
	{
		for (size_t k = 0; k < pilotes.size(); k++) if (pilotes[k].nom == nom) return int32_t(k);
		return -1;
	}
	const uint8_t *banque_ptr(int32_t b) const
	{
		const pilote_t &pl = pilotes[e.pilote < 0 ? 0 : e.pilote];
		size_t o = 0x10000 + size_t(b) * 0x4000;
		if (o + 0x4000 > pl.image.size()) o = 0x10000;
		return &pl.image[o];
	}
	void restaure(int32_t k, uint16_t code)
	{
		pilote_t &pl = pilotes[k];
		int32_t actif = e.actif, pause = e.pause, niveau = e.niveau, gain_m = e.gain, cpt = e.cpt_tick;
		int32_t fd = e.f_debut, fc = e.f_cible, fdu = e.f_duree, fr = e.f_reste;
		float gp = e.g_prec;
		e.pilote = k; e.banque = pl.photo_banque;
		memcpy(ram_c0, &pl.photo_c0[0], 0x1000); memcpy(ram_f0, &pl.photo_f0[0], 0x1000);
		qs.c = pl.photo_qs; qs.fixe_rom(m_rom + pl.rom_off, pl.rom_tai);
		m_p->memoire(&pl.image[0], banque_ptr(e.banque), ram_c0, ram_f0);
		m_p->ecrit_etat(&pl.photo_cpu[0]);
		e.cyc = 0; e.ech = 0; e.cyc_irq = 0; e.frac = 0x10000; e.n_ecr = e.i_ecr = 0;
		e.prec[0] = e.prec[1] = e.cour[0] = e.cour[1] = 0;
		e.actif = actif; e.pause = pause; e.niveau = niveau; e.gain = gain_m; e.cpt_tick = cpt;
		e.f_debut = fd; e.f_cible = fc; e.f_duree = fdu; e.f_reste = fr; e.g_prec = gp;
		ram_c0[0x000] = uint8_t(code >> 8); ram_c0[0x001] = uint8_t(code); ram_c0[0x00F] = 0;
	}
	// Z80 jusqu'au cycle `jusqu` (par tranches qui s'arretent aux IRQ)
	void z80_jusqu(int64_t jusqu)
	{
		while (e.cyc < jusqu) {
			if (e.cyc_irq <= 0) { m_p->irq(); e.cyc_irq += CYC_IRQ; }
			int32_t d = e.cyc_irq;
			if (jusqu - e.cyc < d) d = int32_t(jusqu - e.cyc);
			m_p->execute(d);
			int32_t f = m_p->ecoules();
			e.cyc += f; e.cyc_irq -= f;
		}
	}
	// echantillon QSound suivant : Z80 jusqu'a son instant, ecritures dues appliquees, puis le QSound
	void echantillon(int16_t *s)
	{
		double t = double(e.ech) * CYC_ECH;
		z80_jusqu(int64_t(t) + 1);
		while (e.i_ecr < e.n_ecr && double(e.ecr[e.i_ecr].cyc) <= t) { qs.ecrit(e.ecr[e.i_ecr].reg, e.ecr[e.i_ecr].val); e.i_ecr++; }
		if (e.i_ecr == e.n_ecr) e.i_ecr = e.n_ecr = 0;
		else if (e.i_ecr > N_ECR / 2) {                              // tasse la file
			memmove(&e.ecr[0], &e.ecr[e.i_ecr], size_t(e.n_ecr - e.i_ecr) * sizeof(ecriture));
			e.n_ecr -= e.i_ecr; e.i_ecr = 0;
		}
		qs.echantillon();
		e.ech++;
		s[0] = qs.c.out[0]; s[1] = qs.c.out[1];
	}
	// demarrage : Z80 et QSound avancent ensemble, sortie jetee
	void avance_libre(int64_t cycles)
	{
		int64_t fin = e.cyc + cycles;
		int16_t s[2];
		while (double(e.ech) * CYC_ECH < double(fin)) echantillon(s);
		z80_jusqu(fin);
		while (e.i_ecr < e.n_ecr) { qs.ecrit(e.ecr[e.i_ecr].reg, e.ecr[e.i_ecr].val); e.i_ecr++; }
		e.i_ecr = e.n_ecr = 0;
	}
	void fondu(int32_t dur, uint8_t v)
	{
		e.f_debut = e.niveau;
		e.f_cible = 127 * v / 255;
		e.f_duree = e.f_reste = dur;
	}
	void tick()
	{
		e.g_prec = cible_gain();
		if (!e.actif || e.f_reste <= 0) return;
		e.f_reste--;
		int32_t s = (e.f_debut << 8) + (e.f_cible - e.f_debut) * ((e.f_duree - e.f_reste) << 8) / e.f_duree;
		e.niveau = s >= 0 ? s >> 8 : (s + 0xFF) >> 8;
		if (e.niveau > 127) e.niveau = 127;
		if (s == 0) e.pause = 1;
	}
	float cible_gain() const { return gain * float(e.gain) / 100.f * float(e.niveau) / 127.f; }
};

} // namespace hsfa_mus
