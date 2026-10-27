#!/usr/bin/env python3
"""lecteurs.py MOD : pour chaque routine qui accede a $100/$172/$174/$C178(A5) (sites_a5.tsv), traduction 68K
(translate.py, MEMMODE=cps2) et extrait : lignes autour des acces + constantes LEA/tables (PS2) -> lecteurs_MOD.txt"""
import os, sys, csv, re
mod = sys.argv[1]
os.environ["MODULE"] = mod; os.environ.setdefault("MEMMODE", "cps2"); os.environ.setdefault("GRAIN", "routine")
UT = "<workspace>/scripts/untranspile"; sys.path.insert(0, UT); sys.path.insert(0, "<workspace>/work/carto_ro9")
import census, translate as T, commun as C
buf = open(census.RO3, 'rb').read()
H = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in csv.DictReader(open(os.path.join(H, "sites_a5.tsv")), delimiter='\t') if r['module'] == mod]
routs = sorted({int(r['routine'], 16) for r in rows})
out = open(os.path.join(H, "lecteurs_%s.txt" % mod), "w")
for f in routs:
    a, b = C.func_of(mod, f)
    try: lines, _ = T.translate(buf, max(a - 0x200, 0), b + 0x100)
    except Exception as e: out.write("== %x : erreur %s\n" % (f, e)); continue
    L = [(x, t) for x, t, _ in lines if a <= x < b]
    deps = sorted({r['dep'] for r in rows if int(r['routine'], 16) == f})
    out.write("== %s %x-%x (%d o) %s partenaire=%s\n" % (mod, a, b, b - a, ' '.join(deps),
              next((r['partenaire_ro9'] + ' ' + r['classe'] + ' ' + r['couv_k'] for r in rows if int(r['routine'], 16) == f), '')))
    keep = set()
    for i, (x, t) in enumerate(L):
        if re.search(r"\$(0100|0172|0174|c178|00dc)\(A5\)", t, re.I):
            keep.update(range(max(0, i - 3), min(len(L), i + 8)))
    for i in sorted(keep): out.write("  %07x  %s\n" % L[i])
    consts = sorted({m for _, t in L for m in re.findall(r"PS2 ([0-9a-f]{8})", t)})
    out.write("  constantes PS2 : %s\n" % ' '.join(consts))
out.close()
