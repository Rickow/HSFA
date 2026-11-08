/* hsfa_oggenc -- PCM s16le stereo -> Ogg Vorbis (libvorbis VBR), memes octets sur tous les systemes.
   Projet HSFA (MIT). Construit par construit_oggenc.sh avec libvorbis 1.3.7 / libogg 1.3.6 (BSD-3, Xiph.Org) et les
   fonctions mathematiques de musl 1.1.21 (MIT), en IEEE strict : voir hsfa_portable.h.

   usage : hsfa_oggenc ENTREE.raw SORTIE.ogg FREQ QUALITE [CLE=VALEUR ...]
           hsfa_oggenc --signal SORTIE.ogg      (signal d'essai synthetique, calcule en entiers : test de portabilite)
           hsfa_oggenc --version
   QUALITE : comme ffmpeg -q:a / oggenc -q (-1 a 10, decimales permises : 2, 2.5) ; numero de serie Ogg fixe. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <vorbis/vorbisenc.h>

#define VERSION_HSFA "hsfa_oggenc 1"
#define TRAME 1024                      /* echantillons par appel a vorbis_analysis_buffer (fixe : memes blocs partout) */

/* qualite "2", "-1", "2.5" -> dixiemes de l'echelle vorbis (2 -> 0.2f), sans strtod (arrondis des libc) */
static int qualite(const char *s, float *q)
{
	int signe = 1, ent = 0, frac = 0, den = 1, n = 0;
	if (*s == '-') { signe = -1; s++; }
	while (*s >= '0' && *s <= '9') { ent = ent * 10 + (*s++ - '0'); n++; }
	if (*s == '.') { s++; while (*s >= '0' && *s <= '9' && den < 1000) { frac = frac * 10 + (*s++ - '0'); den *= 10; n++; } }
	if (*s || !n) return -1;
	double v = signe * (ent + (double)frac / den);
	if (v < -1 || v > 10) return -1;
	*q = (float)(v / 10.0);
	return 0;
}

/* signal d'essai : silence, carre (beaucoup d'egaux : ordre du tri), dents de scie, bruit, melange ; 20 s a 48 kHz */
static uint32_t graine = 12345;
static int hasard(void) { graine = graine * 1103515245u + 12345u; return (int)((graine >> 16) & 0x7fff) - 16384; }
static void essai_signal(int16_t *g, int16_t *d, long i)
{
	long s = i / 48000, t = i % 48000;
	int a = 0, b = 0;
	switch (s % 10) {
	case 0: a = b = 0; break;                                                  /* silence */
	case 1: a = (t / 55) % 2 ? 12000 : -12000; b = (t / 73) % 2 ? 9000 : -9000; break;   /* carres */
	case 2: a = (int)((t * 37) % 32768) - 16384; b = (int)((t * 59) % 32768) - 16384; break; /* dents de scie */
	case 3: a = hasard(); b = hasard(); break;                                 /* bruit */
	case 4: a = hasard() / 64; b = a; break;                                   /* bruit faible, mono */
	case 5: { long p = (t * (100 + t / 200)) % 2000; a = (int)(p < 1000 ? p : 2000 - p) * 30 - 15000; b = -a; } break;
	case 6: a = (t % 4800) < 10 ? 30000 : 0; b = (t % 2400) < 5 ? -30000 : 0; break;      /* impulsions */
	case 7: a = ((t / 100) % 2 ? 1 : -1) * (int)(t % 997) * 8 + hasard() / 16; b = a / 2; break;
	case 8: a = (t * 7919) % 65536 - 32768; b = (t / 3) % 2 ? 32767 : -32768; break;      /* pleine echelle */
	default: a = hasard() / 2 + ((t / 40) % 2 ? 8000 : -8000); b = hasard() / 3; break;
	}
	*g = (int16_t)(a > 32767 ? 32767 : a < -32768 ? -32768 : a);
	*d = (int16_t)(b > 32767 ? 32767 : b < -32768 ? -32768 : b);
}

static int ecrit(FILE *f, ogg_page *og)
{
	return fwrite(og->header, 1, og->header_len, f) != (size_t)og->header_len ||
	       fwrite(og->body, 1, og->body_len, f) != (size_t)og->body_len;
}

int main(int argc, char **argv)
{
	int essai = argc == 3 && !strcmp(argv[1], "--signal");
	if (argc == 2 && !strcmp(argv[1], "--version")) { printf("%s ; %s\n", VERSION_HSFA, vorbis_version_string()); return 0; }
	if (!essai && argc < 5) {
		fprintf(stderr, "usage : hsfa_oggenc ENTREE.raw SORTIE.ogg FREQ QUALITE [CLE=VALEUR ...]\n"
		                "        hsfa_oggenc --signal SORTIE.ogg | --version\n");
		return 2;
	}
	FILE *in = NULL, *out;
	long freq = 48000; float q = 0.2f;
	if (!essai) {
		char *fin; freq = strtol(argv[3], &fin, 10);
		if (*fin || freq < 8000 || freq > 192000) { fprintf(stderr, "frequence invalide : %s\n", argv[3]); return 2; }
		if (qualite(argv[4], &q)) { fprintf(stderr, "qualite invalide : %s\n", argv[4]); return 2; }
		if (!(in = fopen(argv[1], "rb"))) { perror(argv[1]); return 1; }
	}
	if (!(out = fopen(argv[2], "wb"))) { perror(argv[2]); return 1; }
	vorbis_info vi; vorbis_info_init(&vi);
	if (vorbis_encode_init_vbr(&vi, 2, freq, q)) { fprintf(stderr, "vorbis_encode_init_vbr\n"); return 1; }
	vorbis_comment vc; vorbis_comment_init(&vc);
	for (int i = 5; !essai && i < argc; i++) vorbis_comment_add(&vc, argv[i]);
	if (essai) vorbis_comment_add(&vc, "HSFA_ESSAI=signal");
	vorbis_dsp_state vd; vorbis_block vb; ogg_stream_state os; ogg_page og; ogg_packet op, oh, oc, ot;
	vorbis_analysis_init(&vd, &vi); vorbis_block_init(&vd, &vb);
	ogg_stream_init(&os, 0x48534641);                         /* "HSFA" : numero de serie fixe */
	vorbis_analysis_headerout(&vd, &vc, &oh, &oc, &ot);
	ogg_stream_packetin(&os, &oh); ogg_stream_packetin(&os, &oc); ogg_stream_packetin(&os, &ot);
	int err = 0;
	while (ogg_stream_flush(&os, &og)) err |= ecrit(out, &og);
	static unsigned char brut[4 * TRAME];
	long pos = 0, total = essai ? 20L * 48000 : -1;
	int eos = 0;
	while (!eos) {
		long n;
		if (essai) n = total - pos < TRAME ? total - pos : TRAME;
		else n = (long)fread(brut, 4, TRAME, in);
		if (n <= 0) vorbis_analysis_wrote(&vd, 0);
		else {
			float **b = vorbis_analysis_buffer(&vd, (int)n);
			for (long i = 0; i < n; i++) {
				int16_t g, d;
				if (essai) essai_signal(&g, &d, pos + i);
				else {                                            /* petit-boutiste, quel que soit le systeme */
					g = (int16_t)(brut[4 * i] | brut[4 * i + 1] << 8);
					d = (int16_t)(brut[4 * i + 2] | brut[4 * i + 3] << 8);
				}
				b[0][i] = g / 32768.f; b[1][i] = d / 32768.f;
			}
			vorbis_analysis_wrote(&vd, (int)n);
			pos += n;
		}
		while (vorbis_analysis_blockout(&vd, &vb) == 1) {
			vorbis_analysis(&vb, NULL); vorbis_bitrate_addblock(&vb);
			while (vorbis_bitrate_flushpacket(&vd, &op)) {
				ogg_stream_packetin(&os, &op);
				while (ogg_stream_pageout(&os, &og)) {
					err |= ecrit(out, &og);
					if (ogg_page_eos(&og)) eos = 1;
				}
			}
		}
	}
	if (in && ferror(in)) { fprintf(stderr, "lecture %s\n", argv[1]); err = 1; }
	ogg_stream_clear(&os); vorbis_block_clear(&vb); vorbis_dsp_clear(&vd); vorbis_comment_clear(&vc); vorbis_info_clear(&vi);
	if (in) fclose(in);
	if (fclose(out) || err) { fprintf(stderr, "ecriture %s\n", argv[2]); return 1; }
	return 0;
}
