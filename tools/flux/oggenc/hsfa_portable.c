/* hsfa_portable.c -- tri fusion stable (remplace qsort : meme ordre partout, egaux compris) */
#include <stdlib.h>
#include <string.h>
static void fusion(unsigned char *a, unsigned char *t, size_t n, size_t k, int (*cmp)(const void *, const void *))
{
	if (n < 2) return;
	size_t m = n / 2, i = 0, j = m, o = 0;
	fusion(a, t, m, k, cmp); fusion(a + m * k, t, n - m, k, cmp);
	while (i < m && j < n) {
		if (cmp(a + j * k, a + i * k) < 0) { memcpy(t + o * k, a + j * k, k); j++; }
		else { memcpy(t + o * k, a + i * k, k); i++; }
		o++;
	}
	if (i < m) memcpy(t + o * k, a + i * k, (m - i) * k), o += m - i;
	if (j < n) memcpy(t + o * k, a + j * k, (n - j) * k);
	memcpy(a, t, n * k);
}
void hsfa_qsort(void *base, size_t n, size_t k, int (*cmp)(const void *, const void *))
{
	if (n < 2 || !k) return;
	unsigned char *t = malloc(n * k);
	if (!t) abort();
	fusion(base, t, n, k, cmp);
	free(t);
}
