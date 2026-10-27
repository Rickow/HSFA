// Outil hote du lecteur de flux (hsfa_flux.h, meme decodeur que le coeur) pour l'encodeur Vorbis (flux_ogg.py).
//   fluxtool pcm <Y_DATA.BIN | ISO | AFS | fichier@decalage> <entree> <sortie.raw>
//     ecrit le PCM stereo 16 bits entrelace (petit-boutiste) de l'entree entiere, sans repetition de boucle, et affiche
//     « freq echantillons debut_boucle fin_boucle » (fin exclue ; 0 0 sans boucle). Entree ADX ou Ogg Vorbis.
// Compilation : voir flux_ogg.py (g++ -O2 -DHSFA_FLUX_VORBIS -I tools/flux fluxtool.cpp + stb_vorbis_impl.o).
#include "hsfa_flux.h"

int main(int argc, char **argv)
{
	if (argc != 5 || strcmp(argv[1], "pcm")) {
		fprintf(stderr, "usage : %s pcm <Y_DATA|ISO|AFS[@decalage]> <entree> <sortie.raw>\n", argv[0]);
		return 2;
	}
	hsfa_flux::lecteur l;
	if (!l.ouvre_y(argv[2])) { fprintf(stderr, "%s\n", l.erreur.c_str()); return 1; }
	std::vector<int16_t> pcm; uint32_t freq; int32_t d, f;
	if (!l.pcm_entree(atoi(argv[3]), pcm, freq, d, f)) { fprintf(stderr, "entree %s : %s\n", argv[3], l.erreur.c_str()); return 1; }
	FILE *o = fopen(argv[4], "wb");
	if (!o || fwrite(pcm.data(), 2, pcm.size(), o) != pcm.size()) { fprintf(stderr, "ecriture de %s\n", argv[4]); return 1; }
	fclose(o);
	printf("%u %zu %d %d\n", freq, pcm.size() / 2, d, f);
	return 0;
}
