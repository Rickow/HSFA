// remplacements minimaux pour lier le Z80 de FBNeo hors du coeur (banc de la carte musique)
#include "burnint.h"
#include <stdarg.h>
UINT8 DebugCPU_ZetInitted = 0;
INT32 (__cdecl *bprintf)(INT32, TCHAR *, ...) = NULL;
static INT32 __cdecl bp(INT32, TCHAR *s, ...) { va_list a; va_start(a, s); vfprintf(stderr, s, a); va_end(a); return 0; }
struct init_bp { init_bp() { bprintf = bp; } } init_bp_;
INT32 (__cdecl *BurnAcb)(struct BurnArea *) = NULL;
UINT8 *_BurnMalloc(INT32 n, char *, INT32) { return (UINT8 *)calloc(1, n); }
void _BurnFree(void *p) { free(p); }
void CpuCheatRegister(INT32, cpu_core_config *) {}
