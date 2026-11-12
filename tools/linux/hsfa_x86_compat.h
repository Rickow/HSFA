/* Compatibilite glibc pour le coeur Linux x86_64 (Batocera 43 : glibc 2.41 ; Ubuntu 20.04 : 2.31) quand on compile
   avec la glibc d'Ubuntu 2.43. Meme principe que tools/recalbox/recalbox_compat.h (ARM), adapte a x86_64 :
   les fonctions de la libm dont la version de symbole a change apres 2.31 (exp, log, pow : 2.29 ; atan2f : 2.43)
   sont liees a leur version d'origine GLIBC_2.2.5. Inclus en tete de chaque fichier (-include).
   Le reste (stat64 2.33, __isoc23_strto* 2.38) est defini dans hsfa_x86_compat.c.
   Controle : objdump -T <coeur> ne doit montrer aucune version GLIBC au-dela de 2.31. */
#ifndef HSFA_X86_COMPAT_H
#define HSFA_X86_COMPAT_H
#if defined(__linux__) && defined(__x86_64__)
__asm__(".symver exp,exp@GLIBC_2.2.5");
__asm__(".symver log,log@GLIBC_2.2.5");
__asm__(".symver pow,pow@GLIBC_2.2.5");
__asm__(".symver atan2f,atan2f@GLIBC_2.2.5");
#endif
#endif
