/* Frontal libretro de test (Linux) : charge un jeu, N images, journal du coeur sur stderr, son en WAV, images BMP.
   joue_linux coeur.so jeu.zip dossier_system N sortie.wav [image_capture ...] ; entrees : fichier HSFA_ENTREES
   (lignes « image_debut image_fin port bouton », boutons RETRO_DEVICE_ID_JOYPAD_*). HSFA_TOURNEE="00.Z/01.Z2" :
   pilotage d'Hyper (tournee.h, portage de tournee_hyper.lua), journal HSFA_TOURNEE_LOG. HSFA_RAM_DUMP=1 : RAM 68K
   ecrite en ram_<image>.bin aux images capturees. */
#include <dlfcn.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include "tournee.h"
static tournee_t T; static int pilote = 0;
struct retro_system_av_info { struct { unsigned bw, bh, mw, mh; float ar; } g; struct { double fps, sr; } t; };
struct retro_game_info { const char *path; const void *data; size_t size; const char *meta; };
struct retro_log_callback { void (*log)(int, const char *, ...); };
static const char *sysdir; static int fmt = 0; static long image = 0; static FILE *wav; static long ech = 0;
static unsigned W, H; static size_t P; static uint8_t *der; static long capt[16]; static int ncapt;
static struct { long a, b; int port, bouton; } ent[8192]; static int nent;
static struct { int g; long a, b; int port, bouton; } ges[8192]; static int nges, geste = -1; static long t_geste;
static void journal(int niv, const char *f, ...) { va_list a; va_start(a, f); vfprintf(stderr, f, a); va_end(a); }
static bool env(unsigned cmd, void *d) {
  switch (cmd) {
  case 9: case 31: *(const char **)d = sysdir; return true;
  case 10: fmt = *(int *)d; return true;
  case 27: ((struct retro_log_callback *)d)->log = journal; return true;
  default: return false;
  }
}
static void bmp(const char *f) {
  FILE *o = fopen(f, "wb"); int rs = (W * 3 + 3) & ~3; uint32_t t = 54 + rs * H;
  uint8_t h[54] = {'B','M'}; memcpy(h+2,&t,4); h[10]=54; h[14]=40; memcpy(h+18,&W,4); memcpy(h+22,&H,4); h[26]=1; h[28]=24;
  fwrite(h, 1, 54, o); uint8_t *l = calloc(rs, 1);
  for (int y = H - 1; y >= 0; y--) { for (unsigned x = 0; x < W; x++) {
      if (fmt == 1) { uint32_t c = ((uint32_t *)(der + y * P))[x]; l[3*x]=c; l[3*x+1]=c>>8; l[3*x+2]=c>>16; }
      else { uint16_t v = ((uint16_t *)(der + y * P))[x]; l[3*x]=(v&31)<<3; l[3*x+1]=((v>>5)&63)<<2; l[3*x+2]=(v>>11)<<3; } }
    fwrite(l, 1, rs, o); }
  fclose(o); free(l);
}
static void video(const void *d, unsigned w, unsigned h, size_t p) {
  if (!d) return; W = w; H = h; P = p;
  for (int i = 0; i < ncapt; i++) if (capt[i] == image) {
    der = realloc(der, p * h); memcpy(der, d, p * h); char n[64]; snprintf(n, sizeof n, "image_%06ld.bmp", image); bmp(n); }
}
static int16_t *cap; static size_t ncap, mcap;            /* capture du son (essai d'etat) */
static size_t audiob(const int16_t *d, size_t n) {
  if (cap) { if (ncap + n > mcap) { mcap = (ncap + n) * 2; cap = realloc(cap, mcap * 4); } memcpy(cap + 2 * ncap, d, n * 4); ncap += n; return n; }
  fwrite(d, 4, n, wav); ech += n; return n; }
static void audio1(int16_t l, int16_t r) { int16_t s[2] = { l, r }; audiob(s, 1); }
static void *(*mem_data)(unsigned);
/* HSFA_POKE="debut-fin:adresse:valeur,..." : octet 68K ($FFxxxx, ordre de l'hote : ram[(a - $FF0000) ^ 1]) ecrit a chaque
   image de [debut, fin) (essais : forcer un perso, une jauge...) */
static struct { long a, b; unsigned ad, v; } pk[32]; static int npk = -1;
static void pokes(void) {
  if (npk < 0) { npk = 0; const char *e = getenv("HSFA_POKE");
    while (e && *e && npk < 32) { int n = 0;
      if (sscanf(e, "%ld-%ld:%x:%x%n", &pk[npk].a, &pk[npk].b, &pk[npk].ad, &pk[npk].v, &n) >= 4) npk++; else break;
      e += n; if (*e == ',') e++; else break; } }
  if (!npk || !mem_data) return;
  uint8_t *r = mem_data(2); if (!r) return;
  for (int i = 0; i < npk; i++) if (image >= pk[i].a && image < pk[i].b) r[(pk[i].ad - 0xFF0000) ^ 1] = (uint8_t)pk[i].v;
}
static void poll_(void) { pokes(); if (pilote) { if (!T.ram) T.ram = mem_data(2); if (T.ram) tournee_image(&T); } }
static int16_t entree(unsigned port, unsigned dev, unsigned idx, unsigned id) {
  if (geste >= 0) {                                    /* mode gestes : seules les entrees du geste en cours */
    for (int i = 0; i < nges; i++) if (ges[i].g == geste && t_geste >= ges[i].a && t_geste < ges[i].b && (int)port == ges[i].port && (int)id == ges[i].bouton) return 1;
    return 0;
  }
  for (int i = 0; i < nent; i++) if (image >= ent[i].a && image < ent[i].b && (int)port == ent[i].port && (int)id == ent[i].bouton) return 1;
  if (pilote && port < 2 && id < 16 && dev == 1) return (int16_t)T.presse[port][id];
  return 0;
}
#define F(n) dlsym(h, n)
int main(int argc, char **argv) {
  void *h = dlopen(argv[1], RTLD_NOW); if (!h) { printf("%s\n", dlerror()); return 1; }
  sysdir = argv[3]; long n = atol(argv[4]); wav = fopen(argv[5], "wb"); uint8_t z[44] = {0}; fwrite(z, 1, 44, wav);
  for (int i = 6; i < argc && ncapt < 16; i++) capt[ncapt++] = atol(argv[i]);
  const char *fe = getenv("HSFA_ENTREES");
  if (fe) { FILE *f = fopen(fe, "r"); while (f && nent < 8192 && fscanf(f, "%ld %ld %d %d", &ent[nent].a, &ent[nent].b, &ent[nent].port, &ent[nent].bouton) == 4) nent++; if (f) fclose(f); }
  const char *li = getenv("HSFA_TOURNEE");          /* ex. "00.Z/01.Z2" : pilote une selection VERSUS puis les combats */
  if (li) { pilote = 1; tournee_liste(&T, li); T.jl = fopen(getenv("HSFA_TOURNEE_LOG") ? getenv("HSFA_TOURNEE_LOG") : "tournee.log", "w"); }
  mem_data = (void *(*)(unsigned))F("retro_get_memory_data");
  ((void (*)(void *))F("retro_set_environment"))(env);
  ((void (*)(void *))F("retro_set_video_refresh"))(video);
  ((void (*)(void *))F("retro_set_audio_sample"))(audio1);
  ((void (*)(void *))F("retro_set_audio_sample_batch"))(audiob);
  ((void (*)(void *))F("retro_set_input_poll"))(poll_);
  ((void (*)(void *))F("retro_set_input_state"))(entree);
  ((void (*)(void))F("retro_init"))();
  struct retro_game_info gi = { argv[2], NULL, 0, NULL };
  if (!((bool (*)(struct retro_game_info *))F("retro_load_game"))(&gi)) { printf("retro_load_game a echoue\n"); return 3; }
  struct retro_system_av_info av; ((void (*)(void *))F("retro_get_system_av_info"))(&av);
  fprintf(stderr, "== jeu charge : %ux%u, %.3f Hz, son %.0f Hz\n", av.g.bw, av.g.bh, av.t.fps, av.t.sr);
  long et_img = -1, et_n = 0;                          /* HSFA_ETAT_TEST="image,n" : etat sauve a l'image, n images rejouees */
  if (getenv("HSFA_ETAT_TEST")) sscanf(getenv("HSFA_ETAT_TEST"), "%ld,%ld", &et_img, &et_n);
  /* HSFA_GESTES=fichier (lignes « geste debut fin port bouton », temps relatifs) et HSFA_GESTES_DEBUT=image : a cette
     image, l'etat est sauve ; chaque geste repart de cet etat et dure HSFA_GESTES_DUREE images (defaut 150) ; un
     repere « GESTE g » est ecrit sur stderr avant chaque geste (journal du coeur groupe par geste). */
  long g_debut = getenv("HSFA_GESTES_DEBUT") ? atol(getenv("HSFA_GESTES_DEBUT")) : -1;
  long g_duree = getenv("HSFA_GESTES_DUREE") ? atol(getenv("HSFA_GESTES_DUREE")) : 150;
  int ngestes = 0;
  if (getenv("HSFA_GESTES")) { FILE *f = fopen(getenv("HSFA_GESTES"), "r");
    while (f && nges < 8192 && fscanf(f, "%d %ld %ld %d %d", &ges[nges].g, &ges[nges].a, &ges[nges].b, &ges[nges].port, &ges[nges].bouton) == 5) {
      if (ges[nges].g + 1 > ngestes) ngestes = ges[nges].g + 1; nges++; }
    if (f) fclose(f); }
  for (image = 0; image < n; image++) {
    if (image == g_debut && ngestes) {
      size_t t = ((size_t (*)(void))F("retro_serialize_size"))(); void *e = malloc(t);
      ((bool (*)(void *, size_t))F("retro_serialize"))(e, t);
      for (geste = 0; geste < ngestes; geste++) {
        ((bool (*)(const void *, size_t))F("retro_unserialize"))(e, t);
        fprintf(stderr, "GESTE %d\n", geste); fflush(stderr);
        for (t_geste = 0; t_geste < g_duree; t_geste++) ((void (*)(void))F("retro_run"))();
      }
      fprintf(stderr, "GESTE FIN\n"); fflush(stderr);
      geste = -1; free(e); break;
    }
    if (image == et_img) {
      size_t (*taille)(void) = (size_t (*)(void))F("retro_serialize_size");
      bool (*sauve)(void *, size_t) = (bool (*)(void *, size_t))F("retro_serialize");
      bool (*charge)(const void *, size_t) = (bool (*)(const void *, size_t))F("retro_unserialize");
      size_t t = taille(); void *e = malloc(t); bool ok = sauve(e, t);
      tournee_t T0 = T; int16_t *A; size_t na;            /* etat du pilote aussi (entrees rejouees a l'identique) */
      cap = malloc(4); ncap = 0; mcap = 1;
      for (long i = 0; i < et_n; i++) { ((void (*)(void))F("retro_run"))(); }
      A = cap; na = ncap; cap = malloc(4); ncap = 0; mcap = 1;
      bool ok2 = charge(e, t); { uint8_t *ram = T.ram; FILE *jl = T.jl; T = T0; T.ram = ram; T.jl = jl; }
      for (long i = 0; i < et_n; i++) { ((void (*)(void))F("retro_run"))(); }
      long diff = 0; for (size_t i = 0; i < 2 * (na < ncap ? na : ncap); i++) diff += A[i] != cap[i];
      long best = diff; int dec = 0;                      /* meilleur alignement a +-4 echantillons (cadence 800/801) */
      for (int dd = -4; dd <= 4; dd++) { long df = 0; size_t m = (na < ncap ? na : ncap) - 8;
        for (size_t i = 8; i < m; i++) for (int c = 0; c < 2; c++) df += A[2 * i + c] != cap[2 * (i + dd) + c];
        if (df < best) { best = df; dec = dd; } }
      if (getenv("HSFA_ETAT_DUMP")) { char nn[256]; snprintf(nn, sizeof nn, "%s_A.raw", getenv("HSFA_ETAT_DUMP")); FILE *o = fopen(nn, "wb"); fwrite(A, 4, na, o); fclose(o);
        snprintf(nn, sizeof nn, "%s_B.raw", getenv("HSFA_ETAT_DUMP")); o = fopen(nn, "wb"); fwrite(cap, 4, ncap, o); fclose(o); }
      if (dec) fprintf(stderr, "== ETAT : au meilleur alignement (%+d echantillon(s)) : %ld differents\n", dec, best);
      fprintf(stderr, "== ETAT image %ld : %zu octets (sauve %d, recharge %d) ; %ld images rejouees : %zu / %zu echantillons, %ld differents\n",
              image, t, ok, ok2, et_n, na, ncap, diff);
      free(A); free(cap); cap = NULL; free(e);
    }
    ((void (*)(void))F("retro_run"))();
    if (getenv("HSFA_RAM_DUMP") && mem_data)              /* RAM 68K ($FF0000-$FFFFFF) aux images capturees */
      for (int c = 0; c < ncapt; c++) if (capt[c] == image) {
        char nn[64]; snprintf(nn, sizeof nn, "ram_%06ld.bin", image); FILE *o = fopen(nn, "wb");
        if (o) { fwrite(mem_data(2), 1, 0x10000, o); fclose(o); } }
  }
  ((void (*)(void))F("retro_unload_game"))(); ((void (*)(void))F("retro_deinit"))();
  uint32_t sr = (uint32_t)av.t.sr, octets = (uint32_t)(ech * 4), v;
  fseek(wav, 0, SEEK_SET); fwrite("RIFF", 1, 4, wav); v = 36 + octets; fwrite(&v, 4, 1, wav); fwrite("WAVEfmt ", 1, 8, wav);
  v = 16; fwrite(&v, 4, 1, wav); uint16_t a[2] = {1, 2}; fwrite(a, 2, 2, wav); fwrite(&sr, 4, 1, wav); v = sr * 4; fwrite(&v, 4, 1, wav);
  uint16_t b[2] = {4, 16}; fwrite(b, 2, 2, wav); fwrite("data", 1, 4, wav); fwrite(&octets, 4, 1, wav); fclose(wav);
  fprintf(stderr, "== %ld images, %ld echantillons\n", n, ech);
  if (T.jl) { fprintf(T.jl, "FIN %ld selections %d manches %d\n", T.k, T.nsel, T.combats); fclose(T.jl); }
  return 0;
}
