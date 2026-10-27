// Banc du lecteur de flux (hsfa_flux.h) avec des flux Ogg Vorbis : boucle, etats de sauvegarde, run-ahead, repli,
// non-regression ADX. Aucune donnee de jeu : flux fabriques par fabrique_flux_test.py.
//   gcc -O2 -c -I tools/flux -o stb.o tools/flux/tests/stb_vorbis_impl.c
//   g++ -O2 -DHSFA_FLUX_VORBIS -I tools/flux -o test_flux_vorbis tools/flux/tests/test_flux_vorbis.cpp stb.o
//   ./test_flux_vorbis <dossier des flux de test>      (ou : tools/flux/tests/lance_tests.sh)
#include "hsfa_flux.h"
#include <chrono>

using hsfa_flux::lecteur;
static int echecs = 0;
#define VERIFIE(c, ...) do { if (c) printf("  ok    "); else { printf("  ECHEC "); echecs++; } printf(__VA_ARGS__); printf("\n"); } while (0)

static std::string D;
static bool ouvre(lecteur &l)
{
	bool ok = l.ouvre((D + "/test.afs").c_str(), (D + "/table.txt").c_str());
	l.mode = 2; l.gain = 1.0f; l.taux = 48000;   // 48 kHz -> 48 kHz, gain 1 : la sortie est exactement le flux
	return ok;
}
static std::vector<int16_t> rend(lecteur &l, int n)
{
	std::vector<int16_t> o(2 * size_t(n), 0);
	l.rend(&o[0], n);
	return o;
}
// sortie attendue : flux deplie (boucles) ; a frequence egale, la sortie i est l'echantillon i (premier tire d'emblee)
static std::vector<int16_t> attendu(const std::vector<int16_t> &pcm, int32_t ls, int32_t le, int64_t t0, int n)
{
	std::vector<int16_t> o(2 * size_t(n), 0);
	int64_t ns = int64_t(pcm.size() / 2);
	for (int i = 0; i < n; i++) {
		int64_t t = t0 + i;
		int64_t p = (le && t >= le) ? ls + (t - le) % (le - ls) : t;
		if (p >= ns) break;
		o[2 * i] = pcm[2 * p]; o[2 * i + 1] = pcm[2 * p + 1];
	}
	return o;
}
static int ecart_max(const std::vector<int16_t> &a, const std::vector<int16_t> &b)
{
	int m = 0;
	for (size_t i = 0; i < a.size() && i < b.size(); i++) { int d = abs(a[i] - b[i]); if (d > m) m = d; }
	return a.size() == b.size() ? m : 99999;
}

int main(int argc, char **argv)
{
	if (argc < 2) { fprintf(stderr, "usage : %s dossier\n", argv[0]); return 2; }
	D = argv[1];
	std::vector<int16_t> src;
	{
		FILE *f = fopen((D + "/source.raw").c_str(), "rb");
		int16_t b[4096]; size_t r;
		while ((r = fread(b, 2, 4096, f)) > 0) src.insert(src.end(), b, b + r);
		fclose(f);
	}

	printf("1. decodage complet (pcm_entree)\n");
	lecteur l;
	VERIFIE(ouvre(l), "ouverture de l'AFS et de la table (%s)", l.erreur.c_str());
	std::vector<int16_t> ogg, ogg3, adx; uint32_t fr; int32_t ls, le, a, b;
	VERIFIE(l.pcm_entree(2, ogg, fr, ls, le), "Ogg avec boucle decode");
	VERIFIE(ogg.size() == src.size(), "Ogg : %zu echantillons, source %zu", ogg.size() / 2, src.size() / 2);
	VERIFIE(fr == 48000 && ls == 96000 && le == 720000, "Ogg : %u Hz, boucle [%d, %d)", fr, ls, le);
	double num = 0, d1 = 0, d2 = 0;
	for (size_t i = 0; i < src.size() && i < ogg.size(); i++) { num += double(src[i]) * ogg[i]; d1 += double(src[i]) * src[i]; d2 += double(ogg[i]) * ogg[i]; }
	double cor = num / sqrt(d1 * d2), db = 10 * log10(d2 / d1);
	VERIFIE(cor > 0.99 && fabs(db) < 0.5, "Ogg contre source : correlation %.4f, niveau %+.2f dB", cor, db);
	VERIFIE(l.pcm_entree(3, ogg3, fr, a, b) && a == 0 && b == 0, "Ogg sans boucle : pas de boucle lue");
	VERIFIE(l.pcm_entree(1, adx, fr, a, b) && adx.size() >= src.size(), "ADX decode (%zu echantillons)", adx.size() / 2);

	printf("2. lecture en jeu, boucle depliee (40 s, 2 passages du point de boucle)\n");
	VERIFIE(l.commande(0x42, 0, 0) == hsfa_flux::REMPLACE_FF05, "code 0042 -> flux Ogg, FF05 au Z80");
	std::vector<int16_t> o = rend(l, 40 * 48000);
	int m = ecart_max(o, attendu(ogg, ls, le, 0, 40 * 48000));
	VERIFIE(m == 0, "sortie = decodage continu deplie, a l'echantillon pres (ecart max %d)", m);
	// raccord : apres le point de boucle, la sortie reprend exactement l'echantillon LOOPSTART du decodage continu
	VERIFIE(o[2 * le] == ogg[2 * ls] && o[2 * le + 1] == ogg[2 * ls + 1] && o[2 * (le - 1)] == ogg[2 * (le - 1)],
	        "raccord : echantillon %d = LOOPEND - 1, puis LOOPSTART (%d)", le - 1, ls);

	printf("3. etat de sauvegarde, run-ahead (anneau) et rechargement a froid (seek)\n");
	lecteur l2; ouvre(l2); l2.commande(0x42, 0, 0);
	rend(l2, 1000000);
	hsfa_flux::etat_t s = l2.e;
	std::vector<int16_t> A = rend(l2, 20000);
	l2.e = s; l2.apres_chargement();
	std::vector<int16_t> B = rend(l2, 20000);
	VERIFIE(ecart_max(A, B) == 0, "run-ahead : etat recharge 20 000 echantillons plus tot, sortie identique");
	lecteur l3; ouvre(l3); l3.e = s; l3.apres_chargement();
	std::vector<int16_t> C = rend(l3, 20000);
	m = ecart_max(A, C);
	VERIFIE(m == 0, "rechargement dans un lecteur neuf (seek) : sortie identique (ecart max %d)", m);
	VERIFIE(ecart_max(A, attendu(ogg, ls, le, 1000000, 20000)) == 0, "et conforme au decodage continu");
	// etat loin en arriere (hors anneau) dans le meme lecteur
	rend(l2, 400000);
	l2.e = s; l2.apres_chargement();
	std::vector<int16_t> E = rend(l2, 20000);
	VERIFIE(ecart_max(A, E) == 0, "retour arriere de 8 s (hors anneau, seek) : sortie identique");

	printf("4. flux sans boucle, entree vide, ADX\n");
	lecteur l4; ouvre(l4); l4.commande(0x43, 0, 0);
	rend(l4, 21 * 48000);
	VERIFIE(!l4.e.actif, "Ogg sans boucle : arret a la fin du fichier");
	lecteur l5; ouvre(l5); l5.commande(0x42, 0, 0); rend(l5, 1000);
	VERIFIE(l5.commande(0x44, 0, 0) == hsfa_flux::PASSE && !l5.e.actif, "entree vide : PASSE (repli QSound), flux en cours arrete");
	lecteur l6; ouvre(l6);
	VERIFIE(l6.commande(0x41, 0, 0) == hsfa_flux::REMPLACE_FF05, "code 0041 -> flux ADX");
	std::vector<int16_t> oa = rend(l6, 10 * 48000);
	VERIFIE(ecart_max(oa, attendu(adx, 0, 0, 0, 10 * 48000)) == 0, "ADX : sortie = decodage ADX (non-regression)");
	lecteur l7; ouvre(l7); l7.commande(0x42, 0, 0); rend(l7, 48000);
	l7.commande(0x41, 0, 0); rend(l7, 48000);
	l7.commande(0x42, 0, 0);
	std::vector<int16_t> oo = rend(l7, 48000);
	VERIFIE(ecart_max(oo, attendu(ogg, ls, le, 0, 48000)) == 0, "Ogg -> ADX -> Ogg : chaque flux repart du debut");

	printf("5. fondu (FF07) et reechantillonnage (44,1 kHz)\n");
	lecteur l8; ouvre(l8); l8.commande(0x42, 0, 0); rend(l8, 48000);
	l8.commande(0xFF07, 0, 0x0400);                // fondu vers 0 en 0xFFFF/0x400 = 63 images
	rend(l8, 2 * 48000);
	VERIFIE(l8.e.niveau == 0 && l8.e.pause, "fondu a 0 : niveau %d, pause %d", l8.e.niveau, l8.e.pause);
	lecteur l9; ouvre(l9); l9.taux = 44100; l9.commande(0x42, 0, 0);
	std::vector<int16_t> o9 = rend(l9, 44100 * 25);
	VERIFIE(l9.e.actif && l9.e.boucle_ok >= 1, "44,1 kHz : 25 s jouees, boucle passee (%d)", l9.e.boucle_ok);

	printf("6. cout du decodage\n");
	lecteur lp; ouvre(lp); lp.commande(0x42, 0, 0);
	auto t0 = std::chrono::steady_clock::now();
	rend(lp, 120 * 48000);
	double sec = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
	printf("  info  120 s rendues en %.3f s (decodage + reechantillonnage + mixage), %.2f %% d'un coeur\n", sec, sec / 120 * 100);

	printf("%s : %d echec(s)\n", echecs ? "ECHEC" : "OK", echecs);
	return echecs ? 1 : 0;
}
