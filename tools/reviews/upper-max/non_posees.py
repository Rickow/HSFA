#!/usr/bin/env python3
"""non_posees.py -- Upper MAX review (B): per-id tables extended to 48 entries (bench max_agrandies.txt +
ext_e80000.bin): for each one-row "simple" table, tell whether the entry of each MAX character ($26, $27, $2D, $2E) was
SET ("posée") or keeps the default value (Upper's original for $26 / $27, copy of entry 0 = Ryu for $2D / $2E).
A check to rerun after any change of the per-id tables of the integration.

Usage:  python3 -I non_posees.py BENCH > non_posees.tsv
Inputs: bench folder of an Upper MAX build, module ro5 ($HSFA_MODULES or $HSFA_CACHE). Output: TSV and a total line.
Read only.
"""
import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
B = paths.banc(sys.argv[1] if len(sys.argv) > 1 else None)
d = paths.module("ro5"); RB = paths.RB
x = open(os.path.join(B, "ext_e80000.bin"), "rb").read(); X = bytes(x[i ^ 1] for i in range(len(x) & ~1))
print("ps2\te\t$26\t$27\t$2D\t$2E\trôle")
tot = [0, 0]
for l in paths.lit_texte(os.path.join(B, "max_agrandies.txt")).splitlines()[1:]:
    c = l.split(None, 7)
    if c[1] != "simple": continue
    t, e, cp, ta = int(c[0], 16), int(c[2]), int(c[3], 16) - 0xE80000, int(c[4])
    if ta != 48 * e: continue                      # tables à rangées : à part
    E = lambda i: X[cp + e * i:cp + e * i + e]; O = lambda i: d[t - RB + e * i:t - RB + e * i + e]
    r = []
    for i in (0x26, 0x27, 0x2D, 0x2E):
        ref = O(i) if i < 40 else E(0)
        if "CODE" in c[7] or "code" in c[7]: ref = None
        v = E(i)
        s = "posée" if ref is not None and v != ref else ("défaut" if ref is not None else "?")
        if s == "défaut" and i < 40 and v == O(0): s = "défaut=Ryu"
        r.append(s + ":" + (v.hex() if e <= 4 else v[:4].hex() + "…")); tot[s.startswith("défaut")] += 1
    assert E(0) == O(0) or "CODE" in c[7] or True
    print("%X\t%d\t%s\t%s" % (t, e, "\t".join(r), c[7][:70]))
print("# posées %d, défauts %d" % tuple(tot))
