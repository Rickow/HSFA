/* Mini-frontal libretro : charge un jeu, fait tourner N images, compte image et son, ecrit la derniere image en BMP. */
#include <windows.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
struct retro_system_info { const char *library_name, *library_version, *valid_extensions; bool need_fullpath, block_extract; };
struct retro_game_info { const char *path; const void *data; size_t size; const char *meta; };
struct retro_game_geometry { unsigned base_width, base_height, max_width, max_height; float aspect_ratio; };
struct retro_system_timing { double fps, sample_rate; };
struct retro_system_av_info { struct retro_game_geometry geometry; struct retro_system_timing timing; };
static const char *sysdir; static int fmt = 0; static long images = 0, echantillons = 0; static double energie = 0;
static unsigned W, H; static size_t P; static uint8_t *dernier;
static bool env(unsigned cmd, void *data) {
  switch (cmd) {
  case 9: case 31: *(const char **)data = sysdir; return true;          /* GET_SYSTEM / SAVE_DIRECTORY */
  case 10: fmt = *(int *)data; return true;                              /* SET_PIXEL_FORMAT */
  case 3: *(bool *)data = false; return true;                            /* GET_CAN_DUPE */
  default: return false;
  }
}
static void video(const void *d, unsigned w, unsigned h, size_t p) {
  if (!d) return; images++; W = w; H = h; P = p;
  dernier = realloc(dernier, p * h); memcpy(dernier, d, p * h);
}
static void audio1(int16_t l, int16_t r) { echantillons++; energie += (double)l * l + (double)r * r; }
static size_t audiob(const int16_t *d, size_t n) { for (size_t i = 0; i < n; i++) audio1(d[2*i], d[2*i+1]); return n; }
static void poll(void) {}
static int16_t entree(unsigned port, unsigned dev, unsigned idx, unsigned id) { return 0; }
static void bmp(const char *f) {
  FILE *o = fopen(f, "wb"); int rs = (W * 3 + 3) & ~3; uint32_t t = 54 + rs * H;
  uint8_t h[54] = {'B','M'}; memcpy(h+2,&t,4); h[10]=54; h[14]=40; memcpy(h+18,&W,4); memcpy(h+22,&H,4); h[26]=1; h[28]=24;
  fwrite(h, 1, 54, o); uint8_t *l = calloc(rs, 1);
  for (int y = H - 1; y >= 0; y--) { for (unsigned x = 0; x < W; x++) {
      uint32_t c; if (fmt == 1) { c = ((uint32_t *)(dernier + y * P))[x]; l[3*x]=c; l[3*x+1]=c>>8; l[3*x+2]=c>>16; }
      else { uint16_t v = ((uint16_t *)(dernier + y * P))[x]; l[3*x]=(v&31)<<3; l[3*x+1]=((v>>5)&63)<<2; l[3*x+2]=(v>>11)<<3; } }
    fwrite(l, 1, rs, o); }
  fclose(o);
}
#define F(n) GetProcAddress(h, n)
int main(int argc, char **argv) {
  HMODULE h = LoadLibraryA(argv[1]); if (!h) { printf("LoadLibrary : %lu\n", GetLastError()); return 1; }
  sysdir = argv[3]; long n = atol(argv[4]);
  ((void (*)(void *))F("retro_set_environment"))(env);
  ((void (*)(void *))F("retro_set_video_refresh"))(video);
  ((void (*)(void *))F("retro_set_audio_sample"))(audio1);
  ((void (*)(void *))F("retro_set_audio_sample_batch"))(audiob);
  ((void (*)(void *))F("retro_set_input_poll"))(poll);
  ((void (*)(void *))F("retro_set_input_state"))(entree);
  ((void (*)(void))F("retro_init"))();
  struct retro_game_info gi = { argv[2], NULL, 0, NULL };
  if (!((bool (*)(struct retro_game_info *))F("retro_load_game"))(&gi)) { printf("retro_load_game a echoue\n"); return 3; }
  struct retro_system_av_info av; ((void (*)(void *))F("retro_get_system_av_info"))(&av);
  printf("jeu charge : %ux%u, %.3f Hz, son %.0f Hz\n", av.geometry.base_width, av.geometry.base_height, av.timing.fps, av.timing.sample_rate);
  DWORD t0 = GetTickCount();
  for (long i = 0; i < n; i++) ((void (*)(void))F("retro_run"))();
  DWORD dt = GetTickCount() - t0;
  printf("%ld images rendues, %ld echantillons stereo (%.1f s de son), niveau RMS %.0f ; %.1f images/s\n", images, echantillons,
         echantillons / av.timing.sample_rate, echantillons ? sqrt(energie / echantillons / 2) : 0, n * 1000.0 / (dt ? dt : 1));
  if (images) bmp(argv[5]);
  ((void (*)(void))F("retro_unload_game"))(); ((void (*)(void))F("retro_deinit"))();
  return 0;
}
