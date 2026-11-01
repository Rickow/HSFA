/* Compatibilite glibc pour Recalbox (Raspberry Pi 3 : armhf ; autres cartes : aarch64) quand on compile avec la
   glibc d'Ubuntu (2.43), bien plus recente que celle de Recalbox 10 (2.39, buildroot 2024.05.3).
   Inclus en tete de chaque fichier (-include) : les fonctions de la libm dont la version de symbole a change apres
   2.31 (exp, log, pow : 2.29 ; atan2f : 2.43) sont liees a leur version d'origine.
   Les autres symboles trop recents (stat 2.33, __isoc23_strto* 2.38, et ceux de libstdc++.a : pthread_once 2.34,
   arc4random 2.36, __ioctl_time64 2.34, __libc_single_threaded 2.32) sont definis dans recalbox_compat.c.
   Sur armhf, compiler aussi avec -U_TIME_BITS -U_FILE_OFFSET_BITS (time_t 32 bits, comme les anciennes glibc).
   Controle : objdump -T <coeur> ne doit montrer aucune version GLIBC au-dela de 2.31. */
#ifndef HSFA_RECALBOX_COMPAT_H
#define HSFA_RECALBOX_COMPAT_H
#if defined(__linux__) && (defined(__arm__) || defined(__aarch64__))
# if defined(__aarch64__)
#  define HSFA_GLIBC_BASE "GLIBC_2.17"
# else
#  define HSFA_GLIBC_BASE "GLIBC_2.4"
# endif
__asm__(".symver exp,exp@" HSFA_GLIBC_BASE);
__asm__(".symver log,log@" HSFA_GLIBC_BASE);
__asm__(".symver pow,pow@" HSFA_GLIBC_BASE);
__asm__(".symver atan2f,atan2f@" HSFA_GLIBC_BASE);
#endif
#endif
