/* Definitions de secours pour lier le coeur FBNeo HSFA x86_64 a une glibc ancienne (<= 2.31) quand on compile avec la
   glibc d'Ubuntu (2.43). Voir hsfa_x86_compat.h. Symboles locaux au coeur (link.T n'exporte que retro_*).
   Pas d'en-tete de la libc ici : stdlib.h redirigerait strtol vers __isoc23_strtol. */
#define HSFA_LOCAL __attribute__((visibility("hidden")))
struct stat; struct stat64;

/* glibc 2.33 : stat / stat64 deviennent de vraies fonctions ; avant : __xstat(_STAT_VER_LINUX = 1 sur x86_64, ...) */
extern int hsfa_xstat_old(int ver, const char *path, struct stat *buf);
__asm__(".symver hsfa_xstat_old,__xstat@GLIBC_2.2.5");
HSFA_LOCAL int stat(const char *path, struct stat *buf) { return hsfa_xstat_old(1, path, buf); }
extern int hsfa_xstat64_old(int ver, const char *path, struct stat64 *buf);
__asm__(".symver hsfa_xstat64_old,__xstat64@GLIBC_2.2.5");
HSFA_LOCAL int stat64(const char *path, struct stat64 *buf) { return hsfa_xstat64_old(1, path, buf); }

/* glibc 2.38 : en C2x / _GNU_SOURCE, strtol & co. deviennent __isoc23_strtol (prefixe 0b en plus).
   Le coeur ne lit pas de nombres en 0b : l'ancienne fonction convient. */
extern long strtol(const char *s, char **fin, int base);
extern unsigned long strtoul(const char *s, char **fin, int base);
extern long long strtoll(const char *s, char **fin, int base);
extern unsigned long long strtoull(const char *s, char **fin, int base);
HSFA_LOCAL long __isoc23_strtol(const char *s, char **fin, int base) { return strtol(s, fin, base); }
HSFA_LOCAL unsigned long __isoc23_strtoul(const char *s, char **fin, int base) { return strtoul(s, fin, base); }
HSFA_LOCAL long long __isoc23_strtoll(const char *s, char **fin, int base) { return strtoll(s, fin, base); }
HSFA_LOCAL unsigned long long __isoc23_strtoull(const char *s, char **fin, int base) { return strtoull(s, fin, base); }
