/* (injection_fork) Copie de hsfa_run.c + SCENARIO de l'essai de decor (essai_fork.lua) : partie, Ryu, decor force
 * ($FF8100 = DEC, ecrit en fin d'image), camera aux deux butees (X des joueurs imposes), captures PPM a chaque butee
 * toutes les 8 images (snap_<butee>_<image>.ppm). Variables : DEC (hexa, defaut 0C), OUTDIR, NF.
 *
 * Lanceur libretro minimal, sans fenetre, pour valider le coeur FBNeo HSFA contre le banc MAME.
 *
 *   hsfa_run <coeur.so> <jeu.zip>
 * Variables (memes conventions que jeu.lua du banc) :
 *   NF=<images>              derniere image (defaut 6000)
 *   INPUTS="a-b:PORT:Champ;a-b%per,dur:PORT:Champ;..."   champs MAME : Coin 1, Coin 2, 1 Player Start,
 *                            2 Players Start, P1 Button 1..6, P1 Up/Down/Left/Right (idem P2)
 *   SNAPS=f1,f2,...          captures (PPM) des images listees, dans OUTDIR (defaut .)
 *   OUT=<journal>            journal "image : $FF8000 $FF8002 $FF8004" a chaque changement
 *   WAV=<fichier>            son complet en WAV 16 bits stereo
 *   SYSDIR=<dossier>         dossier systeme / sauvegardes (defaut OUTDIR)
 */
#include <dlfcn.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "libretro.h"

static void *core;
#define SYM(ret, n, args) ret (*n) args = (ret (*) args)dlsym(core, #n)

static unsigned pixfmt = RETRO_PIXEL_FORMAT_0RGB1555;
static const char *outdir = ".";
static const char *sysdir = ".";
static int frame = 0;

/* --- entrees ------------------------------------------------------------------------------------ */
#define MAXSEQ 256
struct seq { int a, b, per, dur, port, id; } seqs[MAXSEQ];
static int nseq = 0;
static int16_t pad[2][16];

static int champ(const char *f, int *port, int *id)
{
	*port = 0;
	if (!strcmp(f, "Coin 1")) { *id = RETRO_DEVICE_ID_JOYPAD_SELECT; return 1; }
	if (!strcmp(f, "Coin 2")) { *port = 1; *id = RETRO_DEVICE_ID_JOYPAD_SELECT; return 1; }
	if (!strcmp(f, "1 Player Start")) { *id = RETRO_DEVICE_ID_JOYPAD_START; return 1; }
	if (!strcmp(f, "2 Players Start")) { *port = 1; *id = RETRO_DEVICE_ID_JOYPAD_START; return 1; }
	if ((f[0] == 'P') && (f[1] == '1' || f[1] == '2') && f[2] == ' ') {
		*port = f[1] - '1';
		const char *g = f + 3;
		if (!strcmp(g, "Up")) { *id = RETRO_DEVICE_ID_JOYPAD_UP; return 1; }
		if (!strcmp(g, "Down")) { *id = RETRO_DEVICE_ID_JOYPAD_DOWN; return 1; }
		if (!strcmp(g, "Left")) { *id = RETRO_DEVICE_ID_JOYPAD_LEFT; return 1; }
		if (!strcmp(g, "Right")) { *id = RETRO_DEVICE_ID_JOYPAD_RIGHT; return 1; }
		/* disposition FBNeo des jeux CPS2 a 6 boutons : Y X L / B A R (coups faibles, moyens, forts) */
		static const int boutons[6] = { RETRO_DEVICE_ID_JOYPAD_Y, RETRO_DEVICE_ID_JOYPAD_X, RETRO_DEVICE_ID_JOYPAD_L,
		                                RETRO_DEVICE_ID_JOYPAD_B, RETRO_DEVICE_ID_JOYPAD_A, RETRO_DEVICE_ID_JOYPAD_R };
		int n;
		if (sscanf(g, "Button %d", &n) == 1 && n >= 1 && n <= 6) { *id = boutons[n - 1]; return 1; }
	}
	fprintf(stderr, "champ inconnu : %s\n", f);
	return 0;
}

static void lit_inputs(const char *s)
{
	char *c = strdup(s), *save = NULL;
	for (char *it = strtok_r(c, ";", &save); it; it = strtok_r(NULL, ";", &save)) {
		struct seq q = { 0, 0, 0, 0, 0, 0 };
		char port[32], f[64];
		/* forme de jeu.lua : 'a-b::IN0:Champ' ou 'a-b%per,dur::IN0:Champ' (le port commence par ':') */
		if (sscanf(it, "%d-%d%%%d,%d::%31[^:]:%63[^\n]", &q.a, &q.b, &q.per, &q.dur, port, f) == 6 ||
		    (q.per = 0, sscanf(it, "%d-%d::%31[^:]:%63[^\n]", &q.a, &q.b, port, f) == 4)) {
			if (champ(f, &q.port, &q.id) && nseq < MAXSEQ) seqs[nseq++] = q;
		}
	}
	free(c);
}

static void calc_inputs(int frames)
{
	memset(pad, 0, sizeof(pad));
	for (int i = 0; i < nseq; i++) {
		struct seq *q = &seqs[i];
		int on = frames >= q->a && frames <= q->b && (!q->per || (frames - q->a) % q->per < q->dur);
		if (on) pad[q->port][q->id] = 1;
	}
}

static void input_poll(void) {}
static int16_t input_state(unsigned port, unsigned device, unsigned index, unsigned id)
{
	(void)index;
	if (port > 1) return 0;
	if (device == RETRO_DEVICE_JOYPAD && id == RETRO_DEVICE_ID_JOYPAD_MASK) {
		int16_t m = 0;
		for (int i = 0; i < 16; i++) if (pad[port][i]) m |= 1 << i;
		return m;
	}
	if ((device & RETRO_DEVICE_MASK) == RETRO_DEVICE_JOYPAD && id < 16) return pad[port][id];
	return 0;
}

/* --- video / son -------------------------------------------------------------------------------- */
static uint8_t *last = NULL;
static unsigned lw, lh;

static void video_refresh(const void *data, unsigned w, unsigned h, size_t pitch)
{
	if (!data) return;
	lw = w; lh = h;
	last = realloc(last, w * h * 3);
	for (unsigned y = 0; y < h; y++) {
		const uint8_t *row = (const uint8_t *)data + y * pitch;
		for (unsigned x = 0; x < w; x++) {
			uint8_t r, g, b;
			if (pixfmt == RETRO_PIXEL_FORMAT_XRGB8888) {
				uint32_t p = ((const uint32_t *)row)[x];
				r = p >> 16; g = p >> 8; b = p;
			} else if (pixfmt == RETRO_PIXEL_FORMAT_RGB565) {
				uint16_t p = ((const uint16_t *)row)[x];
				r = ((p >> 11) & 31) * 255 / 31; g = ((p >> 5) & 63) * 255 / 63; b = (p & 31) * 255 / 31;
			} else {
				uint16_t p = ((const uint16_t *)row)[x];
				r = ((p >> 10) & 31) * 255 / 31; g = ((p >> 5) & 31) * 255 / 31; b = (p & 31) * 255 / 31;
			}
			uint8_t *o = last + (y * w + x) * 3;
			o[0] = r; o[1] = g; o[2] = b;
		}
	}
}

static FILE *wav = NULL;
static uint32_t wavlen = 0;
static double rms_acc = 0; static long rms_n = 0;

static void audio_sample(int16_t l, int16_t r) { (void)l; (void)r; }
static size_t audio_batch(const int16_t *d, size_t n)
{
	for (size_t i = 0; i < n * 2; i++) { rms_acc += (double)d[i] * d[i]; rms_n++; }
	if (wav) { fwrite(d, 4, n, wav); wavlen += n * 4; }
	return n;
}

static void wav_head(FILE *f, uint32_t rate, uint32_t len)
{
	uint32_t v; uint16_t s;
	fwrite("RIFF", 1, 4, f); v = 36 + len; fwrite(&v, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f);
	v = 16; fwrite(&v, 4, 1, f); s = 1; fwrite(&s, 2, 1, f); s = 2; fwrite(&s, 2, 1, f);
	fwrite(&rate, 4, 1, f); v = rate * 4; fwrite(&v, 4, 1, f); s = 4; fwrite(&s, 2, 1, f); s = 16; fwrite(&s, 2, 1, f);
	fwrite("data", 1, 4, f); fwrite(&len, 4, 1, f);
}

/* --- environnement ------------------------------------------------------------------------------ */
static void logcb(enum retro_log_level level, const char *fmt, ...)
{
	if (level < RETRO_LOG_INFO && !getenv("VERBOSE")) return;
	va_list ap; va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap);
}

static bool environment(unsigned cmd, void *data)
{
	switch (cmd) {
	case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: pixfmt = *(const unsigned *)data; return true;
	case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
	case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data = sysdir; return true;
	case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: ((struct retro_log_callback *)data)->log = logcb; return true;
	case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
	case RETRO_ENVIRONMENT_GET_VARIABLE: {
		struct retro_variable *v = data;
		v->value = NULL;
		if (getenv("CPUSPEED") && !strcmp(v->key, "fbneo-cpu-speed-adjust")) { v->value = getenv("CPUSPEED"); return true; }
		if (!strcmp(v->key, "fbneo-allow-depth-32")) { v->value = "enabled"; return true; }
		return false;
	}
	case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = false; return true;
	case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS: return true;
	case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION: *(unsigned *)data = 0; return true;
	case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS: {
		if (getenv("VERBOSE")) {
			const struct retro_input_descriptor *d = data;
			for (; d->description; d++) fprintf(stderr, "  entree port %u id %u : %s\n", d->port, d->id, d->description);
		}
		return true;
	}
	default: return false;
	}
}

static void snap(int n)
{
	if (!last) return;
	char p[1024];
	snprintf(p, sizeof(p), "%s/snap_%06d.ppm", outdir, n);
	FILE *f = fopen(p, "wb");
	if (!f) return;
	fprintf(f, "P6\n%u %u\n255\n", lw, lh);
	fwrite(last, 3, lw * lh, f);
	fclose(f);
}

static void snapn(const char *n)
{
	if (!last) return;
	char p[1024];
	snprintf(p, sizeof(p), "%s/snap_%s.ppm", outdir, n);
	FILE *f = fopen(p, "wb");
	if (!f) return;
	fprintf(f, "P6\n%u %u\n255\n", lw, lh);
	fwrite(last, 3, lw * lh, f);
	fclose(f);
}

/* --- scenario (programme TRADUIT : octet 68K a de la RAM = ram[a & 0xffff], mot = petit-boutiste) ------ */
static uint8_t *R;
static int u8(int a) { return R[a & 0xffff]; }
static int W16(int a) { return R[a & 0xffff] | (R[(a & 0xffff) + 1] << 8); }
static void S16(int a, int v) { R[a & 0xffff] = v & 0xff; R[(a & 0xffff) + 1] = (v >> 8) & 0xff; }
static int stable = 0, sel = 0, seg = 0, hold = 0, cam = -1, dec = 0x0C;
struct etape { int cible, duree, tag; } chemin[] = { {0x100, 200, 1}, {0x400, 200, 3}, {0x280, 4, 0} };
static int scenario(int k)   /* fin de l'image k : decor, camera, entrees de l'image suivante ; rend 1 a la fin */
{
	memset(pad, 0, sizeof(pad));
	const int J1 = 0xFF8400, J2 = 0xFF8800, GAP = 0x60;
	int jeu = u8(0xFF80A8), mode = W16(0xFF800C);
	int combat = mode == 6 && u8(J1 + 4) == 2 && u8(J2 + 4) == 2;
	if (k >= 1400 && W16(0xFF8100) != 0 && W16(0xFF8100) != dec) S16(0xFF8100, dec);
	if (stable < 120) {
		if (k >= 1500 && k < 1860 && k % 60 < 8) pad[0][RETRO_DEVICE_ID_JOYPAD_SELECT] = 1;
		if (k >= 1900 && k % 40 < 6 && !(jeu & 1)) pad[0][RETRO_DEVICE_ID_JOYPAD_START] = 1;
		int esel = W16(0xFF8000) == 2 && W16(0xFF8004) == 2;
		sel = esel ? sel + 1 : 0;
		if (esel && sel < 120) R[(J1 + 0x102) & 0xffff] = 0;
		if (k >= 2000 && k % 24 < 4 && (jeu & 1) && !combat && (!esel || sel >= 120)) pad[0][RETRO_DEVICE_ID_JOYPAD_Y] = 1;
		stable = combat ? stable + 1 : 0;
		if (stable == 120) fprintf(stderr, "combat stable image %d decor %04X\n", k, W16(0xFF8100));
	} else {
		if (cam < 0) cam = W16(J1 + 0x12) + GAP;
		struct etape *e = &chemin[seg];
		if (cam < e->cible) cam = cam + 2 > e->cible ? e->cible : cam + 2;
		else if (cam > e->cible) cam = cam - 2 < e->cible ? e->cible : cam - 2;
		else {
			hold++;
			if (e->tag && hold >= 16 && hold % 8 == 0) {
				char p[64]; snprintf(p, sizeof(p), "%d_%06d", e->tag, k); snapn(p);
			}
			if (hold >= e->duree) { seg++; hold = 0; if (seg >= 3) return 1; }
		}
		S16(J1 + 0x12, cam - GAP); S16(J2 + 0x12, cam + GAP);
	}
	if (jeu & 1) { S16(J1 + 0x50, 0x90); S16(J1 + 0x52, 0x90); S16(J2 + 0x50, 0x90); S16(J2 + 0x52, 0x90); }
	return 0;
}

int main(int argc, char **argv)
{
	if (argc < 3) { fprintf(stderr, "usage : %s coeur.so jeu.zip\n", argv[0]); return 1; }
	core = dlopen(argv[1], RTLD_NOW);
	if (!core) { fprintf(stderr, "%s\n", dlerror()); return 1; }
	SYM(void, retro_set_environment, (retro_environment_t));
	SYM(void, retro_set_video_refresh, (retro_video_refresh_t));
	SYM(void, retro_set_audio_sample, (retro_audio_sample_t));
	SYM(void, retro_set_audio_sample_batch, (retro_audio_sample_batch_t));
	SYM(void, retro_set_input_poll, (retro_input_poll_t));
	SYM(void, retro_set_input_state, (retro_input_state_t));
	SYM(void, retro_init, (void));
	SYM(bool, retro_load_game, (const struct retro_game_info *));
	SYM(void, retro_get_system_av_info, (struct retro_system_av_info *));
	SYM(void, retro_set_controller_port_device, (unsigned, unsigned));
	SYM(void, retro_run, (void));
	SYM(void, retro_unload_game, (void));
	SYM(void, retro_deinit, (void));
	SYM(void *, retro_get_memory_data, (unsigned));
	SYM(size_t, retro_serialize_size, (void));
	SYM(bool, retro_serialize, (void *, size_t));
	SYM(bool, retro_unserialize, (const void *, size_t));

	if (getenv("OUTDIR")) outdir = getenv("OUTDIR");
	sysdir = getenv("SYSDIR") ? getenv("SYSDIR") : outdir;
	int nf = getenv("NF") ? atoi(getenv("NF")) : 6000;
	if (getenv("INPUTS")) lit_inputs(getenv("INPUTS"));
	static char want[1 << 20];
	if (getenv("SNAPS")) {
		char *c = strdup(getenv("SNAPS"));
		for (char *t = strtok(c, ","); t; t = strtok(NULL, ",")) { int n = atoi(t); if (n > 0 && n < (1 << 20)) want[n] = 1; }
	}
	FILE *log = getenv("OUT") ? fopen(getenv("OUT"), "w") : NULL;

	retro_set_environment(environment);
	retro_set_video_refresh(video_refresh);
	retro_set_audio_sample(audio_sample);
	retro_set_audio_sample_batch(audio_batch);
	retro_set_input_poll(input_poll);
	retro_set_input_state(input_state);
	retro_init();
	struct retro_game_info gi = { argv[2], NULL, 0, NULL };
	if (!retro_load_game(&gi)) { fprintf(stderr, "chargement impossible : %s\n", argv[2]); return 2; }
	retro_set_controller_port_device(0, RETRO_DEVICE_JOYPAD);
	retro_set_controller_port_device(1, RETRO_DEVICE_JOYPAD);
	struct retro_system_av_info av;
	retro_get_system_av_info(&av);
	fprintf(stderr, "video %ux%u, %.3f Hz, son %.0f Hz\n", av.geometry.base_width, av.geometry.base_height, av.timing.fps, av.timing.sample_rate);
	if (getenv("WAV")) { wav = fopen(getenv("WAV"), "wb"); if (wav) wav_head(wav, (uint32_t)av.timing.sample_rate, 0); }

	uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
	char lastst[64] = "";
	clock_t t0 = clock();
	R = ram;
	if (getenv("DEC")) dec = strtol(getenv("DEC"), NULL, 16);
	memset(pad, 0, sizeof(pad));
	for (frame = 1; frame <= nf; frame++) {
		/* entrees : calculees par scenario() a la fin de l'image precedente */
		rms_acc = 0; rms_n = 0;
		retro_run();
		if (ram && log) {
			char st[64];
			#define W(a) (ram[((a) & 0xffff)] | (ram[((a) & 0xffff) + 1] << 8))
			snprintf(st, sizeof(st), "%04x %04x %04x", W(0x8000), W(0x8002), W(0x8004));
			if (strcmp(st, lastst)) { fprintf(log, "%6d : %s\n", frame, st); strcpy(lastst, st); }
		}
		if (log && frame % 60 == 0) fprintf(log, "SON %d %.1f\n", frame, rms_n ? __builtin_sqrt(rms_acc / rms_n) : 0.0);
		if (want[frame]) snap(frame);
		if (scenario(frame)) { fprintf(stderr, "FIN %d\n", frame); break; }
	}
	/* STATETEST=N : etat sauve a l'image N, rejoue jusqu'a NF, image finale comparee a la premiere execution */
	if (getenv("STATETEST")) {
		int n0 = atoi(getenv("STATETEST"));
		/* premiere passe deja faite : on relance depuis le debut avec sauvegarde a n0 */
		uint8_t *imgA = malloc(lw * lh * 3); memcpy(imgA, last, lw * lh * 3);
		retro_unload_game(); retro_load_game(&gi);
		size_t sz = 0; void *st = NULL;
		for (frame = 1; frame <= nf; frame++) {
			calc_inputs(frame - 1); retro_run();
			if (frame == n0) { sz = retro_serialize_size(); st = malloc(sz); retro_serialize(st, sz); }
		}
		int same1 = !memcmp(imgA, last, lw * lh * 3);
		retro_unserialize(st, sz);
		for (frame = n0 + 1; frame <= nf; frame++) { calc_inputs(frame - 1); retro_run(); }
		int same2 = !memcmp(imgA, last, lw * lh * 3);
		fprintf(stderr, "ETAT : %zu octets ; relance identique %s ; apres restauration de l'image %d : %s\n", sz, same1 ? "oui" : "NON", n0, same2 ? "IDENTIQUE" : "DIFFERENT");
	}
	double dt = (double)(clock() - t0) / CLOCKS_PER_SEC;
	fprintf(stderr, "%d images en %.1f s (%.0f images/s)\n", nf, dt, nf / dt);
	if (log) fclose(log);
	if (wav) { fseek(wav, 0, SEEK_SET); wav_head(wav, (uint32_t)av.timing.sample_rate, wavlen); fclose(wav); }
	retro_unload_game();
	retro_deinit();
	return 0;
}
