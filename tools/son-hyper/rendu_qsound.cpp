// Rendu WAV d'une suite d'ecritures QSound (rendu_partitions.py) par hsfa_qsound.h, le QSound du coeur FBNeo HSFA.
//   rendu_qsound <rom_qsound.bin> <ecritures.bin> <secondes> <sortie.wav>
// ecritures.bin : enregistrements de 8 octets petit-boutistes { uint32 cycle Z80 (8 MHz) ; uint8 registre ; uint8 0 ;
// uint16 valeur }, dans l'ordre. Sortie : stereo 16 bits a 24 038 Hz (un echantillon toutes les 2 496 periodes de
// 60 MHz, comme le coeur), sans gain ajoute.
#include "hsfa_qsound.h"
#include <stdio.h>
#include <vector>

static void le32(FILE *f, uint32_t v) { fputc(v, f); fputc(v >> 8, f); fputc(v >> 16, f); fputc(v >> 24, f); }
static void le16(FILE *f, uint16_t v) { fputc(v, f); fputc(v >> 8, f); }

int main(int argc, char **argv)
{
	if (argc != 5) { fprintf(stderr, "usage : %s rom.bin ecritures.bin secondes sortie.wav\n", argv[0]); return 2; }
	std::vector<uint8_t> rom, ecr;
	for (int k = 0; k < 2; k++) {
		FILE *f = fopen(argv[1 + k], "rb");
		if (!f) { fprintf(stderr, "%s introuvable\n", argv[1 + k]); return 1; }
		std::vector<uint8_t> &d = k ? ecr : rom;
		uint8_t b[65536]; size_t n;
		while ((n = fread(b, 1, sizeof b, f)) > 0) d.insert(d.end(), b, b + n);
		fclose(f);
	}
	uint32_t taille = 1;
	while (taille < rom.size()) taille <<= 1;
	rom.resize(taille, 0);
	static hsfa_qs::qsound q;
	q.fixe_rom(&rom[0], taille);
	q.reset();
	const double ns = atof(argv[3]) * 60000000.0 / 2496.0;
	size_t n = size_t(ns), k = 0, ne = ecr.size() / 8;
	std::vector<int16_t> out(2 * n);
	for (size_t i = 0; i < n; i++) {
		// instant de l'echantillon i, en cycles Z80 : i * 2496 / 60 MHz * 8 MHz = i * 332,8
		double t = double(i) * 332.8;
		while (k < ne) {
			const uint8_t *e = &ecr[8 * k];
			uint32_t c = e[0] | (e[1] << 8) | (e[2] << 16) | (uint32_t(e[3]) << 24);
			if (c > t) break;
			q.ecrit(e[4], uint16_t(e[6] | (e[7] << 8)));
			k++;
		}
		q.echantillon();
		out[2 * i] = q.c.out[0]; out[2 * i + 1] = q.c.out[1];
	}
	FILE *o = fopen(argv[4], "wb");
	if (!o) { fprintf(stderr, "ecriture de %s\n", argv[4]); return 1; }
	uint32_t octets = uint32_t(out.size() * 2);
	fwrite("RIFF", 1, 4, o); le32(o, 36 + octets); fwrite("WAVEfmt ", 1, 8, o); le32(o, 16); le16(o, 1); le16(o, 2);
	le32(o, 24038); le32(o, 24038 * 4); le16(o, 4); le16(o, 16); fwrite("data", 1, 4, o); le32(o, octets);
	fwrite(&out[0], 2, out.size(), o);
	fclose(o);
	printf("%zu echantillons, %zu ecritures appliquees sur %zu\n", n, k, ne);
	return 0;
}
