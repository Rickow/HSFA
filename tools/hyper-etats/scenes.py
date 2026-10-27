#!/usr/bin/env python3
"""scenes.py trace.tr [...] : pour chaque trace d'une image (debogueur MAME), les aiguillages executes (table, index
visites, cible MIPS fichier) et le nombre d'instructions par zone. Carte : work/mame_ro9/carte_image.txt"""
import re, struct, sys, bisect, collections
C = "<workspace>/work/mame_ro9/carte_image.txt"
b = open("<workspace>/anthology_extract/decompressed/ro9_usa_prog68k.bin", "rb").read()
rows = []
for l in open(C):
    a, va, mn = l.rstrip("\n").split(" ", 2); rows.append((int(a, 16), int(va, 16), mn))
rows.sort(); keys = [r[0] for r in rows]
par_va = collections.defaultdict(list)
for a, va, mn in rows: par_va[va].append(a)
vas = sorted(par_va)
def a68(t):                                   # 68K d'une cible MIPS : premiere ligne de carte dans [t, t+0x40)
    i = bisect.bisect_left(vas, t)
    if i < len(vas) and vas[i] < t + 0x40: return min(par_va[vas[i]])
    return None
disp = []                                     # (68K du JMP, var, table, [(index, cible, 68K)])
for i, (a, va, mn) in enumerate(rows):
    m = re.search(r"(JMP|JSR) T_([0-9a-f]+)\(PC,D\d\.W\).*table de (\d+)", mn)
    if not m: continue
    var = "?"
    for j in range(max(0, i - 4), i):
        mm = re.search(r"MOVE\.[WB] (\(A5\)|\$[0-9a-f]+\(A[0-6]\)),D[01]$", rows[j][2])
        if mm: var = mm.group(1)
    t = int(m.group(2), 16); ent = []
    for k in range(int(m.group(3))):
        v = struct.unpack_from("<I", b, t - 0x1F0000 + 4 * k)[0]
        if 0x1F0000 <= v < 0x5AF180: ent.append((2 * k, v - 0x1F0000, a68(v - 0x1F0000)))
    disp.append((a, va, var, t, ent))
for tr in sys.argv[1:]:
    pcs = collections.Counter()
    for l in open(tr, errors="replace"):
        m = re.match(r"^([0-9A-F]{6}):", l)
        if m: pcs[int(m.group(1), 16)] += 1
    print("== %s : %d instructions" % (tr.split("/")[-1], sum(pcs.values())))
    for a, va, var, t, ent in disp:
        if a not in pcs and (a + 4) not in pcs and not any(x[2] in pcs for x in ent if x[2]): continue
        hit = ["%x->%06x" % (k, c) for k, c, x in ent if x and x in pcs]
        if hit: print("   mips %06x  %-10s T_%x : %s" % (va, var, t, " ".join(hit)))
