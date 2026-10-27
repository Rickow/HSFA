// HSFA : REJEU QSOUND des sons de SFA1 et SFA2 (voix, cris, K.O., annonceur, bruitages simples et en sequence) sur un
// 2e QSound, pour les versions ZERO / ZERO 2 / ALPHA d'Hyper. En-tete seul, C++98 portable (MAME, FBNeo/libretro),
// sans dependance. Aucune donnee de jeu dans le code : la ROM d'echantillons est lue dans le X_DATA.BIN de
// l'utilisateur (ou l'ISO de l'Anthology), les sons sont decrits par une table texte separee (gen_rejeu.py) : pour chaque
// code, les ecritures de registres QSound (temps, registre, valeur) que le pilote Z80 d'origine fait pour la commande.
//
// Principe : a chaque commande posee par le 68K dans la boite aux lettres ($61801F = 0), commande() decide :
//   - code de la table (CODE ou REF) : le son est rejoue sur le 2e QSound ; la commande transmise au Z80 devient un code
//     VIDE du Z80 (aucun effet) ; la priorite et la coupure de voie suivent la regle des pilotes Capcom (v1.05 $046E,
//     v1.71 $05AF) : pour chaque voie du son, si la voie est occupee par un son de priorite plus haute, cette voie
//     n'est pas prise ; sinon le son en cours sur la voie est coupe (ses ecritures suivantes sur la voie sont
//     abandonnees). Une voie se libere a la derniere ecriture du son qui l'occupe ;
//   - ALIAS : la commande transmise au Z80 est remplacee par le code Z80 donne (rien n'est rejoue) ;
//   - FF00 : tout s'arrete (reponse du pilote d'origine a FF00), la commande passe aussi au Z80 ;
//   - le reste passe au Z80 sans changement.
// L'hote fournit le temps en microsecondes emulees, appelle avance() a l'instant prochain() et ecrit chaque registre
// dans son 2e QSound (MAME : qsound_hle_device ; FBNeo : 2e instance du QSound).
#pragma once
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <vector>

namespace hsfa_rejeu {

#if defined(__LIBRETRO_SDK_FILE_STREAM_TRANSFORMS_H)
static inline int fseek64r(FILE *f, uint64_t o) { return fseek(f, (int64_t)o, SEEK_SET) < 0 ? -1 : 0; }
#elif defined(_WIN32)
static inline int fseek64r(FILE *f, uint64_t o) { return _fseeki64(f, (long long)o, SEEK_SET); }
#else
static inline int fseek64r(FILE *f, uint64_t o) { return fseeko(f, (off_t)o, SEEK_SET); }
#endif

enum { NV = 19, NI = 32 };                     // voies (16 PCM + 3 ADPCM), sons simultanes
enum { PASSE = 0, REMPLACE = 1 };
enum { K_SON = 0, K_INIT = 1, K_STOP = 2 };

struct ecriture { uint32_t t; uint16_t val; uint8_t reg; uint8_t voie; };   // voie 0xFF = registre global
struct son { uint16_t code, src; uint8_t jeu, prio; uint32_t debut, n, voies; uint32_t fin[NV]; };
struct source { std::string nom; uint64_t off; uint32_t taille, crc; uint8_t banque; };

// etat sauvegardable (types simples, enregistres un par un par l'hote)
struct instance { int32_t kind, ent; int64_t t0; uint32_t pos, voies; };
struct etat_t {
	instance ins[NI];
	int32_t proprio[NV];                   // instance qui occupe la voie (-1 libre)
	int32_t prio[NV];
	int64_t fin[NV];                       // fin d'occupation (us)
	etat_t() { raz(); }
	void raz() { memset(this, 0, sizeof(*this)); for (int i = 0; i < NI; i++) ins[i].ent = -1; for (int v = 0; v < NV; v++) proprio[v] = -1; }
};

static inline int voie_de(int r)
{
	if (r < 0x80) return ((r & 7) == 0) ? (((r >> 3) + 1) & 15) : (r >> 3);
	if (r >= 0x80 && r <= 0x8F) return r - 0x80;
	if (r >= 0x90 && r <= 0x92) return 16 + r - 0x90;
	if (r >= 0xBA && r <= 0xC9) return r - 0xBA;
	if (r >= 0xCA && r <= 0xD5) return 16 + ((r - 0xCA) >> 2);
	if (r >= 0xD6 && r <= 0xD8) return 16 + r - 0xD6;
	return 0xFF;
}
static inline bool reg_banque(int r) { return (r < 0x80 && (r & 7) == 0) || r == 0xCC || r == 0xD0 || r == 0xD4; }

static inline uint32_t crc32(const uint8_t *p, size_t n, uint32_t c = 0)
{
	c = ~c;
	for (size_t i = 0; i < n; i++) { c ^= p[i]; for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1))); }
	return ~c;
}

class rejeu {
public:
	std::string erreur;
	etat_t e;
	uint16_t vide;                          // code Z80 vide envoye a la place d'un son rejoue
	rejeu() : vide(0x0000), m_j(NULL) {}
	~rejeu() { if (m_j) fclose(m_j); }

	void ouvre_journal(const char *p) { if (p && *p) m_j = fopen(p, "w"); }
	size_t nb_sons() const { return m_sons.size(); }
	size_t nb_codes() const { size_t k = 0; for (size_t i = 0; i < m_code.size(); i++) if (m_code[i] >= 0 || m_alias[i] >= 0) k++; return k; }

	// table : hsfa_rejeu_table.txt ; xdata : X_DATA.BIN, ou ISO (X_DATA.BIN cherche dans la racine ISO9660), ou
	// 'fichier@decalage hexa' (debut de X_DATA.BIN dans le fichier) ; rom : memoire du 2e QSound (banques de 64 Ko)
	bool ouvre(const char *table, const char *xdata, uint8_t *rom, size_t taille_rom)
	{
		if (!lit_table(table)) return false;
		std::string chemin(xdata);
		uint64_t base = 0;
		size_t at = chemin.rfind('@');
		if (at != std::string::npos && at > 0 && chemin.find('/', at) == std::string::npos) { base = strtoull(chemin.c_str() + at + 1, NULL, 16); chemin.resize(at); }
		FILE *f = fopen(chemin.c_str(), "rb");
		if (!f) { erreur = "X_DATA introuvable : " + chemin; return false; }
		uint8_t pvd[6];
		if (base == 0 && lire(f, 0x8000, pvd, 6) && !memcmp(pvd + 1, "CD001", 5)) {
			base = cherche_iso(f, "X_DATA.BIN");
			if (!base) { fclose(f); erreur = "ISO sans X_DATA.BIN"; return false; }
		}
		for (size_t i = 0; i < m_src.size(); i++) {
			const source &s = m_src[i];
			size_t o = size_t(s.banque) << 16;
			if (o + s.taille > taille_rom) { fclose(f); erreur = "ROM du 2e QSound trop petite"; return false; }
			if (!lire(f, base + s.off, rom + o, s.taille)) { fclose(f); erreur = "X_DATA illisible (" + s.nom + ")"; return false; }
			if (crc32(rom + o, s.taille) != s.crc) { fclose(f); erreur = "X_DATA : CRC different pour " + s.nom; return false; }
		}
		fclose(f);
		return true;
	}

	// mise sous tension du 2e QSound : initialisation du pilote d'origine apres 0,1 s (le DSP doit avoir demarre)
	void reset(int64_t maintenant)
	{
		e.raz();
		if (!m_init.empty()) lance(K_INIT, 0, maintenant + 100000, 0);
	}

	// commande posee par le 68K. Rend PASSE ou REMPLACE (*z80 = code a transmettre au Z80 a la place).
	int commande(uint16_t cmd, int64_t maintenant, uint16_t *z80)
	{
		if (m_sons.empty()) return PASSE;
		if (cmd == 0xFF00) {
			for (int i = 0; i < NI; i++) e.ins[i].ent = -1;
			for (int v = 0; v < NV; v++) { e.proprio[v] = -1; e.prio[v] = 0; e.fin[v] = 0; }
			if (!m_stop.empty()) lance(K_STOP, 0, maintenant, 0);
			trace("%lld FF00 : arret\n", (long long)maintenant);
			return PASSE;
		}
		if (m_alias[cmd] >= 0) { *z80 = uint16_t(m_alias[cmd]); trace("%lld %04X -> Z80 %04X\n", (long long)maintenant, cmd, *z80); return REMPLACE; }
		int32_t k = m_code[cmd];
		if (k < 0) return PASSE;
		const son &s = m_sons[k];
		uint32_t prises = 0;
		for (int v = 0; v < NV; v++) {
			if (!(s.voies & (1u << v))) continue;
			bool occupee = e.proprio[v] >= 0 && maintenant < e.fin[v];
			if (occupee && s.prio < e.prio[v]) continue;            // pilote : 'cp (ix+prio) ; jp c,suivante'
			prises |= 1u << v;
		}
		*z80 = vide;
		if (!prises) { trace("%lld %04X (%s %04X prio %02X) refuse : voies occupees\n", (long long)maintenant, cmd, m_src[s.jeu].nom.c_str(), s.src, s.prio); return REMPLACE; }
		int i = lance(K_SON, k, maintenant, prises);
		for (int v = 0; v < NV; v++) {
			if (!(prises & (1u << v))) continue;
			int32_t a = e.proprio[v];
			if (a >= 0 && a != i) e.ins[a].voies &= ~(1u << v);
			e.proprio[v] = i; e.prio[v] = s.prio; e.fin[v] = maintenant + s.fin[v];
		}
		trace("%lld %04X -> %s %04X prio %02X voies %05X\n", (long long)maintenant, cmd, m_src[s.jeu].nom.c_str(), s.src, s.prio, prises);
		return REMPLACE;
	}

	// instant (us) de la prochaine ecriture, ou -1
	int64_t prochain() const
	{
		int64_t m = -1;
		for (int i = 0; i < NI; i++) {
			const instance &x = e.ins[i];
			if (x.ent < 0) continue;
			int64_t t = x.t0 + ecr(x)[x.pos].t;
			if (m < 0 || t < m) m = t;
		}
		return m;
	}

	// ecrit (dans l'ordre des temps) toutes les ecritures dues a l'instant maintenant : W::ecrit(reg, val)
	template <class W> void avance(int64_t maintenant, W &w)
	{
		for (;;) {
			int best = -1; int64_t bt = 0;
			for (int i = 0; i < NI; i++) {
				const instance &x = e.ins[i];
				if (x.ent < 0) continue;
				int64_t t = x.t0 + ecr(x)[x.pos].t;
				if (t <= maintenant && (best < 0 || t < bt)) { best = i; bt = t; }
			}
			if (best < 0) return;
			instance &x = e.ins[best];
			const ecriture &c = ecr(x)[x.pos];
			int jeu = x.kind == K_SON ? m_sons[x.ent].jeu : x.ent;
			bool garde = x.kind != K_SON || (c.voie == 0xFF ? x.voies != 0 : (x.voies & (1u << c.voie)) != 0);
			if (garde) {
				uint16_t v = c.val;
				if (reg_banque(c.reg) && m_src[jeu].banque) v = uint16_t((v & 0x8000) | ((v + m_src[jeu].banque) & 0x7FFF));
				w.ecrit(c.reg, v);
			}
			if (++x.pos >= taille(x)) {
				if (x.kind == K_SON) for (int v = 0; v < NV; v++) if (e.proprio[v] == best) e.proprio[v] = -1;
				x.ent = -1;
			}
		}
	}

private:
	std::vector<son> m_sons;
	std::vector<ecriture> m_ecr, m_init, m_stop;
	std::vector<source> m_src;
	std::vector<int32_t> m_code, m_alias;
	FILE *m_j;

	void trace(const char *fmt, ...)
#if defined(__GNUC__)
		__attribute__((format(printf, 2, 3)))
#endif
	{
		if (!m_j) return;
		va_list ap; va_start(ap, fmt); vfprintf(m_j, fmt, ap); va_end(ap); fflush(m_j);
	}
	const ecriture *ecr(const instance &x) const
	{
		if (x.kind == K_INIT) return &m_init[0];
		if (x.kind == K_STOP) return &m_stop[0];
		return &m_ecr[m_sons[x.ent].debut];
	}
	uint32_t taille(const instance &x) const
	{
		if (x.kind == K_INIT) return uint32_t(m_init.size());
		if (x.kind == K_STOP) return uint32_t(m_stop.size());
		return m_sons[x.ent].n;
	}
	int lance(int kind, int32_t ent, int64_t t0, uint32_t voies)
	{
		int libre = -1;
		for (int i = 0; i < NI; i++) if (e.ins[i].ent < 0) { libre = i; break; }
		if (libre < 0) {                                       // plein : on remplace le son le plus ancien
			libre = 0;
			for (int i = 1; i < NI; i++) if (e.ins[i].t0 < e.ins[libre].t0) libre = i;
			for (int v = 0; v < NV; v++) if (e.proprio[v] == libre) e.proprio[v] = -1;
		}
		instance &x = e.ins[libre];
		x.kind = kind; x.ent = ent; x.t0 = t0; x.pos = 0; x.voies = voies;
		return libre;
	}
	static bool lire(FILE *f, uint64_t o, void *d, size_t n) { return !fseek64r(f, o) && fread(d, 1, n, f) == n; }
	static uint32_t rd32le(const uint8_t *p) { return p[0] | (p[1] << 8) | (p[2] << 16) | (uint32_t(p[3]) << 24); }
	uint64_t cherche_iso(FILE *f, const char *nom)
	{
		uint8_t pvd[2048];
		if (!lire(f, 0x8000, pvd, 2048)) return 0;
		uint32_t lba = rd32le(pvd + 156 + 2), tai = rd32le(pvd + 156 + 10);
		if (tai > 1 << 20) return 0;
		std::vector<uint8_t> d(tai);
		if (!lire(f, uint64_t(lba) * 2048, &d[0], tai)) return 0;
		size_t ln = strlen(nom);
		for (size_t p = 0; p < tai;) {
			uint8_t l = d[p];
			if (!l) { p = (p / 2048 + 1) * 2048; continue; }
			if (p + 33 > tai) break;
			uint8_t nl = d[p + 32];
			if (nl >= ln && !memcmp(&d[p + 33], nom, ln) && (nl == ln || d[p + 33 + ln] == ';')) return uint64_t(rd32le(&d[p + 2])) * 2048;
			p += l;
		}
		return 0;
	}
	int jeu_de(const char *nom) const { for (size_t i = 0; i < m_src.size(); i++) if (m_src[i].nom == nom) return int(i); return -1; }

	bool lit_table(const char *chemin)
	{
		FILE *f = fopen(chemin, "r");
		if (!f) { erreur = std::string("table introuvable : ") + chemin; return false; }
		m_code.assign(65536, -1); m_alias.assign(65536, -1);
		std::vector<std::pair<uint16_t, uint16_t> > refs;
		char l[256], a[64], b[64];
		std::vector<ecriture> *bloc = NULL; int reste = 0; son *cour = NULL;
		while (fgets(l, sizeof(l), f)) {
			if (reste > 0) {
				unsigned t = 0, r = 0, v = 0;
				if (cour) { if (sscanf(l, "%u %x %x", &t, &r, &v) != 3) break; }
				else if (sscanf(l, "%x %x", &r, &v) != 2) break;
				ecriture c; c.t = cour ? t : 0; c.reg = uint8_t(r); c.val = uint16_t(v); c.voie = uint8_t(voie_de(r));
				bloc->push_back(c);
				if (cour && c.voie != 0xFF) { cour->voies |= 1u << c.voie; if (t > cour->fin[c.voie]) cour->fin[c.voie] = t; }
				if (--reste == 0) { if (cour) cour->n = uint32_t(m_ecr.size() - cour->debut); cour = NULL; }
				continue;
			}
			if (l[0] == '#' || l[0] == '\n') continue;
			unsigned x1 = 0, x2 = 0, x3 = 0, x4 = 0; int n = 0;
			if (sscanf(l, "SOURCE %63s %x %x %x %x", a, &x1, &x2, &x3, &x4) == 5) {
				source s; s.nom = a; s.off = x1; s.taille = x2; s.banque = uint8_t(x3); s.crc = x4; m_src.push_back(s);
			} else if (sscanf(l, "INIT %63s %d", a, &n) == 2) { bloc = &m_init; reste = n; cour = NULL; m_init.clear(); }
			else if (sscanf(l, "STOP %63s %d", a, &n) == 2) { bloc = &m_stop; reste = n; cour = NULL; m_stop.clear(); }
			else if (sscanf(l, "CODE %x %63s %x %x %d", &x1, a, &x2, &x3, &n) == 5) {
				int j = jeu_de(a);
				if (j < 0 || n <= 0 || x1 > 0xFFFF) { erreur = std::string("table : ligne invalide ") + l; fclose(f); return false; }
				son s; memset(&s, 0, sizeof(s)); s.code = uint16_t(x1); s.jeu = uint8_t(j); s.src = uint16_t(x2); s.prio = uint8_t(x3);
				s.debut = uint32_t(m_ecr.size());
				m_code[x1] = int32_t(m_sons.size()); m_sons.push_back(s); cour = &m_sons.back();
				bloc = &m_ecr; reste = n;
			} else if (sscanf(l, "REF %x %x", &x1, &x2) == 2) refs.push_back(std::make_pair(uint16_t(x1), uint16_t(x2)));
			else if (sscanf(l, "ALIAS %x %x", &x1, &x2) == 2) m_alias[x1 & 0xFFFF] = int32_t(x2 & 0xFFFF);
			else if (sscanf(l, "VIDE %x", &x1) == 1) vide = uint16_t(x1);
			(void)b;
		}
		fclose(f);
		if (reste) { erreur = "table tronquee"; return false; }
		for (int passe = 0; passe < 4; passe++)                    // REF vers un REF : resolu en quelques passes
			for (size_t i = 0; i < refs.size(); i++) if (m_code[refs[i].second] >= 0) m_code[refs[i].first] = m_code[refs[i].second];
		if (m_sons.empty() || m_src.empty()) { erreur = "table vide"; return false; }
		return true;
	}
};

} // namespace hsfa_rejeu
