/* Compatibilite glibc pour ROCKNIX (glibc 2.40-2.41) quand on compile avec une glibc plus recente (Ubuntu 2.43).
   atan2f a recu une nouvelle version de symbole dans glibc 2.43 : on se lie a l'ancienne (GLIBC_2.17). */
#if defined(__aarch64__) && defined(__linux__)
__asm__(".symver atan2f,atan2f@GLIBC_2.17");
#endif
