#!/usr/bin/env python3
"""gestionnaires.py : tables de sauts par decor (longs, 40 entrees dans Upper / 4 dans Hyper) : cibles distinctes,
routine Upper, partenaire Hyper (inverse_ro5.pkl) et couverture K=12 (couv_k.pkl) -> gestionnaires.tsv"""
import os, sys, struct, pickle, collections
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as K
DIR = "<workspace>/anthology_extract/decompressed"; BASE = 0x1F0000
B = {m: open(os.path.join(DIR, "%s_usa_prog68k.bin" % m), "rb").read() for m in ("ro5", "ro9")}
inv = pickle.load(open("<workspace>/work/etude_upper_hyper/inverse_ro5.pkl", "rb"))
cov = pickle.load(open("<workspace>/work/etude_upper_hyper/couv_k.pkl", "rb"))
T = [("ordre de mise a jour des plans (arcade ~$1749A)", 0x6147B0, 0x5C50D0),
     ("gestionnaire scroll1 ($17532)", 0x614850, 0x5C50E0),
     ("gestionnaire scroll2 ($17C6C)", 0x6149B0, 0x5C5100),
     ("gestionnaire scroll3 ($18000)", 0x614AD0, 0x5C5180),
     ("effet par decor ($19BA8 ; + $C174/$C176)", 0x6135A0, 0x5C9E30),
     ("defilement scenes Arcade (0x2CAC0)", 0x60B400, None)]
H = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(H, "gestionnaires.tsv"), "w")
out.write("table\tT_upper\tdecors\tcible_upper(fichier)\tcouv_k\tpartenaire_ro9\tclasse\tdans_table_hyper\n")
for nom, t5, t9 in T:
    v5 = [struct.unpack_from('<I', B["ro5"], t5 - BASE + 4 * k)[0] for k in range(40)]
    v9 = [struct.unpack_from('<I', B["ro9"], t9 - BASE + 4 * k)[0] for k in range(4)] if t9 else []
    c9 = {x - BASE for x in v9}
    by = collections.defaultdict(list)
    for k, v in enumerate(v5): by[v - BASE].append(2 * k)
    nabs = 0
    for f, decs in sorted(by.items()):
        r = K.func_of("ro5", f); a = r[0] if r else f
        p = inv.get(a, {}); pa = p.get('partenaire'); cl = p.get('classe', '?'); cv = cov.get(a, -1)
        ok = pa in c9
        if cv < 0.5: nabs += 1
        out.write("%s\t%x\t%s\t%x\t%.2f\t%s\t%s\t%s\n" % (nom, t5, ' '.join('$%02X' % d for d in decs), f, cv,
                  ('%x' % pa) if pa else '-', cl, 'oui' if ok else ''))
    print("%-48s Upper %x : %2d cibles distinctes, %d absentes (couv < 50 %%) | Hyper %s : %s" % (nom, t5, len(by), nabs,
          ('%x' % t9) if t9 else '-', ' '.join('%x' % (x - BASE) for x in v9)))
out.close()
