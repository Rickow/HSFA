// Banc du branchement de la carte musique au Z80 de FBNeo (classe HsfaMusZet extraite de cps_hsfa.cpp) :
// meme scenario que test_carte.cpp avec z80.h, sorties comparees.
#include "burnint.h"
#include "z80_intf.h"
#include "hsfa_musique.h"
#include <vector>
#include <string>
#include <cmath>
#undef FILE
#undef fopen
#undef fread
#undef fwrite
#undef fclose
static hsfa_mus::carte *HsfaMus = NULL;
#include "zet_extrait.h"                  // classe HsfaMusZet extraite de cps_hsfa.cpp par lance_tests_carte.sh
static std::vector<uint8_t> lit(const std::string &p) { std::vector<uint8_t> d; FILE *f = fopen(p.c_str(), "rb"); uint8_t b[65536]; size_t n; while ((n = fread(b, 1, sizeof b, f)) > 0) d.insert(d.end(), b, b + n); fclose(f); return d; }
int main(int argc, char **argv)
{
	std::string d = argv[1], q = argv[2];
	std::vector<uint8_t> tab = lit(q + "/hsfa_musique_table.txt"), dat = lit(q + "/hsfa_musique.bin");
	std::vector<uint8_t> q1 = lit(d + "/sfa_qs.bin"), q2 = lit(d + "/sfa2_qs.bin"), rom(0x800000, 0);
	memcpy(&rom[0], &q1[0], 0x400000); memcpy(&rom[0x400000], &q2[0], 0x400000);
	ZetInit(0); ZetInit(1);                      // comme le coeur : Z80 principal (0) puis carte (1)
	HsfaMus = new hsfa_mus::carte(); HsfaMusZet *p = new HsfaMusZet();
	if (!HsfaMus->ouvre((const char *)&tab[0], tab.size(), &dat[0], dat.size()) || !HsfaMus->demarre(p, &rom[0], 0x800000)) { printf("ECHEC %s\n", HsfaMus->erreur.c_str()); return 1; }
	HsfaMus->taux = 48000;
	int r = HsfaMus->commande(0x41, 0, 0, false);
	std::vector<int16_t> o(60 * 48000 * 2, 0);
	for (int i = 0; i < 3600; i++) HsfaMus->rend(&o[i * 1600], 800);   // 3 600 images de 800 echantillons
	double s = 0; for (size_t i = 0; i < o.size(); i++) s += double(o[i]) * o[i];
	printf("Zet : commande %d, 60 s, RMS %.0f ; etat %zu octets\n", r, std::sqrt(s / o.size()), HsfaMus->taille_etat());
	FILE *w = fopen(argv[3], "wb"); fwrite(&o[0], 2, o.size(), w); fclose(w);
	std::vector<uint8_t> e(HsfaMus->taille_etat()); HsfaMus->sauve(&e[0]);
	std::vector<int16_t> A(5 * 48000 * 2, 0), B(5 * 48000 * 2, 0);
	HsfaMus->rend(&A[0], 5 * 48000); HsfaMus->charge(&e[0]); HsfaMus->rend(&B[0], 5 * 48000);
	printf("Zet : etat recharge, 5 s %s\n", A == B ? "identiques" : "DIFFERENTES");
	return A == B ? 0 : 1;
}
