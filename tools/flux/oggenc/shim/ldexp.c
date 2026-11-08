/* ldexp = scalbn (comme musl src/math/ldexp.c) */
double ldexp(double x, int n) { return scalbn(x, n); }
