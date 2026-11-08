/* libm.h minimal (remplace src/internal/libm.h de musl 1.1.21 pour les fonctions retenues ; meme contenu utile) */
#ifndef _LIBM_H
#define _LIBM_H
#include <stdint.h>
#include <float.h>
#include <math.h>
#define FORCE_EVAL(x) do {                        \
	if (sizeof(x) == sizeof(float)) {         \
		volatile float __x; __x = (x);    \
	} else {                                  \
		volatile double __x; __x = (x);   \
	}                                         \
} while(0)
#define EXTRACT_WORDS(hi,lo,d) do { union {double f; uint64_t i;} __u; __u.f = (d); \
	(hi) = __u.i >> 32; (lo) = (uint32_t)__u.i; } while (0)
#define GET_HIGH_WORD(hi,d) do { union {double f; uint64_t i;} __u; __u.f = (d); (hi) = __u.i >> 32; } while (0)
#define GET_LOW_WORD(lo,d) do { union {double f; uint64_t i;} __u; __u.f = (d); (lo) = (uint32_t)__u.i; } while (0)
#define INSERT_WORDS(d,hi,lo) do { union {double f; uint64_t i;} __u; \
	__u.i = ((uint64_t)(hi)<<32) | (uint32_t)(lo); (d) = __u.f; } while (0)
#define SET_HIGH_WORD(d,hi) do { union {double f; uint64_t i;} __u; __u.f = (d); \
	__u.i &= 0xffffffff; __u.i |= (uint64_t)(hi) << 32; (d) = __u.f; } while (0)
#define SET_LOW_WORD(d,lo) do { union {double f; uint64_t i;} __u; __u.f = (d); \
	__u.i &= 0xffffffff00000000ull; __u.i |= (uint32_t)(lo); (d) = __u.f; } while (0)
#define GET_FLOAT_WORD(w,d) do { union {float f; uint32_t i;} __u; __u.f = (d); (w) = __u.i; } while (0)
#define SET_FLOAT_WORD(d,w) do { union {float f; uint32_t i;} __u; __u.i = (w); (d) = __u.f; } while (0)
#endif
