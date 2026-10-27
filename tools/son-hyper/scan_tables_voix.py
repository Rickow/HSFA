#!/usr/bin/env python3
"""Cherche les tables « sons par pas » (champ $E6) : entrees de 8 octets BE [code, code_alt, 0, 0].
Usage : scan_tables_voix.py <fichier> [code_min] [code_max] [min_entrees]"""
import sys, numpy as np
f = sys.argv[1]; lo = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x200; hi = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x6ff
mn = int(sys.argv[4]) if len(sys.argv) > 4 else 6
d = np.frombuffer(open(f, 'rb').read(), np.uint8)
for al in (0, 2, 4, 6):
    n = (len(d) - al) // 8
    w = d[al:al + 8 * n].reshape(n, 4, 2).astype(np.uint32)
    w = (w[:, :, 0] << 8) | w[:, :, 1]
    c, a = w[:, 0], w[:, 1]
    ok = (w[:, 2] == 0) & (w[:, 3] == 0) & ((c == 0) | ((c >= lo) & (c <= hi))) & ((a == 0) | ((a >= lo) & (a <= hi)))
    i = 0
    while i < n:
        if not ok[i]: i += 1; continue
        j = i
        while j < n and ok[j]: j += 1
        nz = int((c[i:j] != 0).sum())
        if j - i >= mn and nz >= mn - 1:
            print('%06x %d %s' % (al + 8 * i, j - i, ' '.join('%04x' % x if x == y else '%04x/%04x' % (x, y) for x, y in zip(c[i:j], a[i:j]))))
        i = j
