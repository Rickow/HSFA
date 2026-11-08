/* hsfa_portable.h -- inclus de force (-include) dans libvorbis, libogg, les fonctions mathematiques de musl et
   hsfa_oggenc.c : memes octets d'Ogg Vorbis sur tous les systemes (Linux, Windows, macOS, x86_64, arm64, WASM).
   Avec -fno-fast-math -ffp-contract=off, les operations de base (+ - * / sqrt, conversions) sont IEEE 754 et donc
   identiques partout. Restent les fonctions de la libm du systeme (glibc, msvcrt/ucrt, libSystem, musl : resultats
   differents au dernier bit) et qsort (ordre des egaux propre a chaque libc) : on les remplace ici par une seule
   implementation compilee avec le programme (fonctions de musl 1.1.21, fdlibm, sans FMA ; tri fusion stable).
   Le nom hsfa_* empeche aussi le compilateur de les evaluer a la compilation (cos(constante) par MPFR...). */
#ifndef HSFA_PORTABLE_H
#define HSFA_PORTABLE_H
#include <stddef.h>
#include <math.h>
#include <stdlib.h>
#include <float.h>
#if !defined(FLT_EVAL_METHOD) || FLT_EVAL_METHOD != 0
#error "hsfa_portable : FLT_EVAL_METHOD doit valoir 0 (SSE2 / ARM / WASM ; pas de x87)"
#endif
#if defined(__FAST_MATH__)
#error "hsfa_portable : compiler sans -ffast-math"
#endif
#define sin    hsfa_sin
#define cos    hsfa_cos
#define exp    hsfa_exp
#define log    hsfa_log
#define pow    hsfa_pow
#define atan   hsfa_atan
#define acos   hsfa_acos
#define floor  hsfa_floor
#define ceil   hsfa_ceil
#define rint   hsfa_rint
#define ldexp  hsfa_ldexp
#define scalbn hsfa_scalbn
#define qsort  hsfa_qsort
#define __sin  hsfa__sin
#define __cos  hsfa__cos
#define __rem_pio2       hsfa__rem_pio2
#define __rem_pio2_large hsfa__rem_pio2_large
double hsfa_sin(double), hsfa_cos(double), hsfa_exp(double), hsfa_log(double), hsfa_pow(double, double);
double hsfa_atan(double), hsfa_acos(double), hsfa_floor(double), hsfa_ceil(double), hsfa_rint(double);
double hsfa_ldexp(double, int), hsfa_scalbn(double, int);
double hsfa__sin(double, double, int), hsfa__cos(double, double);
int hsfa__rem_pio2(double, double *), hsfa__rem_pio2_large(double *, double *, int, int, int);
void hsfa_qsort(void *base, size_t n, size_t taille, int (*cmp)(const void *, const void *));
#endif
