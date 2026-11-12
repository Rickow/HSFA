#!/usr/bin/env python3
"""compare_psp2.py -- Upper MAX review (B): PSP homologues of Upper's per-id tables by BEST ALIGNMENT (numpy: number of
equal bytes between Upper's entries $00-$25 and each position of the EBOOT, area 0x1F0000-0x300000), then comparison of
the MAX entries: Upper MAX build ($26, $27, $2D, $2E of ext_e80000.bin) against the PSP ($26, $27, $28, $29). Pointer
tables do not align (different addresses): "non alignée". Used for the arbitrations of the review's major findings
(which per-id entries differ from the PSP).

Usage:  python3 -I compare_psp2.py BENCH > compare_psp2.tsv
Inputs: bench folder of an Upper MAX build (max_agrandies.txt, ext_e80000.bin), module ro5 ($HSFA_MODULES or
        $HSFA_CACHE), PSP BOOT.BIN ($HSFA_PSP_BOOT or $HSFA_CACHE). Output: TSV (column names in French). Read only.
"""
import sys, os
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
B = paths.banc(sys.argv[1] if len(sys.argv) > 1 else None)
d = paths.module("ro5"); RB = paths.RB
eb = paths.boot()
LO, HI = 0x1F0000, 0x300000
E = np.frombuffer(eb[LO:HI], dtype=np.uint8)
x = open(os.path.join(B, "ext_e80000.bin"), "rb").read(); X = bytes(x[i ^ 1] for i in range(len(x) & ~1))
h = lambda b: b.hex() if len(b) <= 8 else b[:8].hex() + "…"
print("ps2\te\trangées\tPSP\tégaux natifs\tEagle um/psp\tMaki um/psp\tYun um/psp[$28]\tIngrid um/psp[$29]\tverdict\trôle")
for l in paths.lit_texte(os.path.join(B, "max_agrandies.txt")).splitlines()[1:]:
    c = l.split(None, 7)
    if c[1] != "simple": continue
    t, e, cp, ta = int(c[0], 16), int(c[2]), int(c[3], 16) - 0xE80000, int(c[4])
    m = np.frombuffer(d[t - RB:t - RB + e * 0x26], dtype=np.uint8); n = len(m)
    step = max(1, n // 400)                           # grandes tables : échantillon
    idx = range(0, n, step)
    sc = np.zeros(len(E) - n, dtype=np.int32)
    for j in idx: sc += (E[j:j + len(sc)] == m[j])
    o = np.argsort(sc)[::-1][:50]; k = int(o[0]); best = int(sc[k]); second = max((int(sc[q]) for q in o if abs(int(q) - k) >= e), default=0)
    tot = len(idx)
    if best * 100 < 78 * tot or len(set(m.tobytes())) < 2:
        print("%X\t%d\t%d\tnon alignée (%d %%)\t\t\t\t\t\t\t%s" % (t, e, ta // (48 * e), best * 100 // tot, c[7][:60])); continue
    cands = [k]
    for q in o:
        q = int(q)
        if int(sc[q]) * 100 >= 78 * tot and int(sc[q]) >= best - max(2, tot // 20) and all(abs(q - z) >= n for z in cands) and len(cands) < 3: cands.append(q)
    for k in cands:
      best = int(sc[k])
      k += LO; col = []; nd = 0
      for u, q in ((0x26, 0x26), (0x27, 0x27), (0x2D, 0x28), (0x2E, 0x29)):
          a = X[cp + e * u:cp + e * u + e]; p = eb[k + e * q:k + e * q + e]
          col.append("%s %s %s" % (h(a), "=" if a == p else "≠", h(p))); nd += a != p
      print("%X\t%d\t%d\t0x%X\t%d %%\t%s\t%s\t%s" % (t, e, ta // (48 * e), k, best * 100 // tot, "\t".join(col), ("ÉCART ×%d" % nd if nd else "ok") + (" (ambigu : %d candidats)" % len(cands) if len(cands) > 1 else ""), c[7][:60]))
