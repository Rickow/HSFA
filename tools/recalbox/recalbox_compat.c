/* Definitions de secours pour lier le coeur FBNeo HSFA a une glibc ancienne (<= 2.31) quand on compile avec la
   glibc d'Ubuntu (2.43). Voir recalbox_compat.h et build.sh.
   Ces symboles sont appeles par notre code (stat, __isoc23_strto*) ou par libstdc++.a liee en statique
   (pthread_once, arc4random, __ioctl_time64, __libc_single_threaded), ou par libgcc_eh.a en aarch64
   (_dl_find_object, glibc 2.35). Ils restent locaux au coeur :
   link.T n'exporte que retro_*.
   Pas d en-tete de la libc standard ici (sauf link.h en aarch64) : stdlib.h redirigerait strtol vers __isoc23_strtol.
   A compiler avec -U_TIME_BITS -U_FILE_OFFSET_BITS sur armhf, et -fPIC. */
#if defined(__aarch64__)
# define _GNU_SOURCE 1   /* struct dl_find_object (dlfcn.h, via link.h) */
# include <link.h>
#endif
#include <stddef.h>
#include <stdarg.h>

#if defined(__aarch64__)
# define HSFA_GLIBC_BASE "GLIBC_2.17"
# define HSFA_STAT_VER 0   /* _STAT_VER (generique 64 bits) */
#else
# define HSFA_GLIBC_BASE "GLIBC_2.4"
# define HSFA_STAT_VER 3   /* _STAT_VER_LINUX d'ARM */
#endif

#define HSFA_LOCAL __attribute__((visibility("hidden")))

struct stat;
struct stat64;

/* --- glibc 2.32 : variable lue par libstdc++ (0 = toujours supposer plusieurs fils : sur et correct) --- */
HSFA_LOCAL char __libc_single_threaded = 0;

/* --- glibc 2.33 : stat devient une vraie fonction ; avant, c'etait __xstat(_STAT_VER, ...) --- */
extern int hsfa_xstat_old(int ver, const char *path, struct stat *buf);
__asm__(".symver hsfa_xstat_old,__xstat@" HSFA_GLIBC_BASE);
HSFA_LOCAL int stat(const char *path, struct stat *buf) { return hsfa_xstat_old(HSFA_STAT_VER, path, buf); }
extern int hsfa_xstat64_old(int ver, const char *path, struct stat64 *buf);
__asm__(".symver hsfa_xstat64_old,__xstat64@" HSFA_GLIBC_BASE);
HSFA_LOCAL int stat64(const char *path, struct stat64 *buf) { return hsfa_xstat64_old(HSFA_STAT_VER, path, buf); }

/* --- glibc 2.34 : pthread_once passe de libpthread a libc avec une nouvelle version.
       libstdc++.a l'appelle ; l'edition de liens le detourne (-Wl,--wrap=pthread_once) vers l'ancienne version. --- */
extern int hsfa_pthread_once_old(void *once, void (*fn)(void));
__asm__(".symver hsfa_pthread_once_old,pthread_once@" HSFA_GLIBC_BASE);
HSFA_LOCAL int __wrap_pthread_once(void *once, void (*fn)(void)) { return hsfa_pthread_once_old(once, fn); }

#if defined(__arm__)
/* --- glibc 2.34 (armhf, time_t 64 bits) : libstdc++.a (random_device) appelle __ioctl_time64(fd, RNDGETENTCNT, &int).
       Aucune structure temporelle en jeu : on passe a l'ioctl classique. --- */
extern int ioctl(int fd, unsigned long req, ...);
HSFA_LOCAL int __ioctl_time64(int fd, unsigned long req, ...)
{
  va_list ap;
  void *arg;
  va_start(ap, req);
  arg = va_arg(ap, void *);
  va_end(ap);
  return ioctl(fd, req, arg);
}
#endif

/* --- glibc 2.36 : arc4random (libstdc++.a, std::random_device). getrandom existe depuis 2.25. --- */
extern long getrandom(void *buf, size_t len, unsigned int flags);
HSFA_LOCAL unsigned int arc4random(void)
{
  static unsigned int etat = 0x9E3779B9u;
  unsigned int v = 0;
  if (getrandom(&v, sizeof v, 0) == (long)sizeof v) return v;
  /* repli (ne devrait pas servir) : xorshift */
  etat ^= etat << 13; etat ^= etat >> 17; etat ^= etat << 5;
  return etat;
}

/* --- glibc 2.38 : en C2x / _GNU_SOURCE, strtol & co. deviennent __isoc23_strtol (prefixe 0b en plus).
       Le coeur ne lit pas de nombres en 0b : l'ancienne fonction convient. --- */
extern long strtol(const char *s, char **fin, int base);
extern unsigned long strtoul(const char *s, char **fin, int base);
extern long long strtoll(const char *s, char **fin, int base);
extern unsigned long long strtoull(const char *s, char **fin, int base);
HSFA_LOCAL long __isoc23_strtol(const char *s, char **fin, int base) { return strtol(s, fin, base); }
HSFA_LOCAL unsigned long __isoc23_strtoul(const char *s, char **fin, int base) { return strtoul(s, fin, base); }
HSFA_LOCAL long long __isoc23_strtoll(const char *s, char **fin, int base) { return strtoll(s, fin, base); }
HSFA_LOCAL unsigned long long __isoc23_strtoull(const char *s, char **fin, int base) { return strtoull(s, fin, base); }

#if defined(__aarch64__)
/* --- glibc 2.35 : libgcc_eh.a (deroulement des exceptions C++, aarch64) cherche le PT_GNU_EH_FRAME d'une adresse
       par _dl_find_object. Equivalent par dl_iterate_phdr (le chemin des glibc anciennes). Sans objet sur armhf
       (deroulement EHABI : __gnu_Unwind_Find_exidx). --- */
struct hsfa_dlfo_recherche { ElfW(Addr) pc; struct dl_find_object *res; int trouve; };

static int hsfa_dlfo_rappel(struct dl_phdr_info *info, size_t taille, void *donnees)
{
  struct hsfa_dlfo_recherche *r = (struct hsfa_dlfo_recherche *)donnees;
  const ElfW(Phdr) *eh = NULL;
  ElfW(Addr) bas = ~(ElfW(Addr))0, haut = 0;
  int dedans = 0;
  (void)taille;
  for (ElfW(Half) i = 0; i < info->dlpi_phnum; i++) {
    const ElfW(Phdr) *p = &info->dlpi_phdr[i];
    if (p->p_type == PT_LOAD) {
      ElfW(Addr) d = info->dlpi_addr + p->p_vaddr, f = d + p->p_memsz;
      if (d < bas) bas = d;
      if (f > haut) haut = f;
      if (r->pc >= d && r->pc < f) dedans = 1;
    } else if (p->p_type == PT_GNU_EH_FRAME) eh = p;
  }
  if (!dedans) return 0;
  unsigned char *o = (unsigned char *)r->res;
  for (size_t k = 0; k < sizeof *r->res; k++) o[k] = 0;
  r->res->dlfo_map_start = (void *)bas;
  r->res->dlfo_map_end = (void *)haut;
  r->res->dlfo_eh_frame = eh ? (void *)(info->dlpi_addr + eh->p_vaddr) : NULL;
  r->trouve = 1;
  return 1;
}

HSFA_LOCAL int _dl_find_object(void *pc, struct dl_find_object *res)
{
  struct hsfa_dlfo_recherche r = { (ElfW(Addr))pc, res, 0 };
  dl_iterate_phdr(hsfa_dlfo_rappel, &r);
  return r.trouve ? 0 : -1;
}
#endif
