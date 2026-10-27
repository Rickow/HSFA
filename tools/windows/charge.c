/* Mini-frontal libretro : charge le coeur comme RetroArch et appelle init / infos / deinit. */
#include <windows.h>
#include <stdio.h>
#include <stdbool.h>
struct retro_system_info { const char *library_name, *library_version, *valid_extensions; bool need_fullpath, block_extract; };
typedef bool (*env_t)(unsigned, void *);
static bool env(unsigned cmd, void *data) { (void)cmd; (void)data; return false; }
int main(int argc, char **argv) {
  HMODULE h = LoadLibraryA(argv[1]);
  if (!h) { printf("LoadLibrary echoue : erreur %lu\n", GetLastError()); return 1; }
  void (*set_env)(env_t) = (void *)GetProcAddress(h, "retro_set_environment");
  void (*init)(void) = (void *)GetProcAddress(h, "retro_init");
  void (*deinit)(void) = (void *)GetProcAddress(h, "retro_deinit");
  unsigned (*api)(void) = (void *)GetProcAddress(h, "retro_api_version");
  void (*info)(struct retro_system_info *) = (void *)GetProcAddress(h, "retro_get_system_info");
  if (!set_env || !init || !deinit || !api || !info) { printf("symbole manquant\n"); return 2; }
  struct retro_system_info si = {0};
  info(&si);
  printf("API %u ; coeur \"%s\" version %s ; extensions %s\n", api(), si.library_name, si.library_version, si.valid_extensions);
  set_env(env); init(); deinit();
  printf("init / deinit : OK\n");
  return 0;
}
