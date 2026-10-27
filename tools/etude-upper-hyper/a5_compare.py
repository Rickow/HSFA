#!/usr/bin/env python3
"""Variables A5 d'Upper (ro5) et d'Hyper (ro9) : presence, routines, et detection de REEMPLOI d'un meme deplacement
pour un autre usage dans Hyper.
  - acces A5 relevés comme carto_ro9/vars_a5.a5_access (lw 0x1114 puis load/store d(base)) ;
  - coherence d'un deplacement d commun : une routine ro9 qui accede a d a-t-elle un partenaire ro5 qui accede aussi
    a d ? (comparaison_ro9_routine) ; vote ro3 -> ro5 / ro3 -> ro9 (vars_a5.json) : un meme deplacement image d'un
    deplacement ro3 different = collision.
Sorties : a5_ro5_absentes_ro9.tsv, a5_communes_suspectes.tsv, a5.pkl"""
import os, sys, pickle, json, collections
os.environ["GRAIN"] = "routine"
CR9 = "<workspace>/work/carto_ro9"; sys.path.insert(0, CR9)
import commun as C
from vars_a5 import a5_access
OUT = os.path.dirname(os.path.abspath(__file__))
import atteint as AT

def par_dep(mod):
    A = a5_access(mod); D = collections.defaultdict(lambda: dict(n=0, w=0, routines=set(), tailles=collections.Counter()))
    for va, (d, m) in A.items():
        e = D[d]; e['n'] += 1; e['w'] += m.startswith('s'); e['routines'].add(C.func_of(mod, va)[0]); e['tailles'][m] += 1
    return dict(D)

def s16(d): return d - 0x10000 if d >= 0x8000 else d
def cps2(d): return "$%06X" % ((0xFF8000 + s16(d)) & 0xFFFFFF)

def main():
    D5, D9 = par_dep('ro5'), par_dep('ro9')
    CMP9 = pickle.load(open(os.path.join(CR9, "comparaison_ro9_routine.pkl"), "rb"))
    arc = pickle.load(open(os.path.join(OUT, "arcade_upper.pkl"), "rb"))
    V = json.load(open(os.path.join(CR9, "vars_a5.json")))
    # ro3 -> ro5 et ro3 -> ro9 : deplacement d'arrivee -> deplacements ro3 d'origine
    orig = {}
    for m in ('ro5', 'ro9'):
        o = collections.defaultdict(set)
        for d3, c in V[m].items():
            best = max(c.items(), key=lambda kv: kv[1])[0]
            o[int(best, 16)].add(int(d3, 16))
        orig[m] = o
    print("deplacements A5 : ro5 %d, ro9 %d, communs %d, ro5 seul %d, ro9 seul %d" % (
        len(D5), len(D9), len(set(D5) & set(D9)), len(set(D5) - set(D9)), len(set(D9) - set(D5))))
    excl = arc['excl']
    with open(os.path.join(OUT, "a5_ro5_absentes_ro9.tsv"), "w") as f:
        f.write("dep_A5\tcps2\tacces\tecritures\troutines_ro5\tdont_arcade_exclusives\tro3_origine\troutines (8 premieres)\n")
        for d in sorted(set(D5) - set(D9), key=s16):
            e = D5[d]; ra = len(e['routines'] & excl)
            f.write("$%04X\t%s\t%d\t%d\t%d\t%d\t%s\t%s\n" % (d, cps2(d), e['n'], e['w'], len(e['routines']), ra,
                    ','.join('$%04X' % x for x in sorted(orig['ro5'].get(d, ()))),
                    ' '.join('0x%X' % x for x in sorted(e['routines'])[:8])))
    # communs : coherence
    sus = []
    for d in sorted(set(D5) & set(D9), key=s16):
        r9 = D9[d]['routines']; ok = 0; tot = 0
        for a in r9:
            r = CMP9.get(a)
            if not r or r['ro5']['partenaire'] is None: continue
            tot += 1
            if r['ro5']['partenaire'] in D5[d]['routines']: ok += 1
        o5, o9 = orig['ro5'].get(d, set()), orig['ro9'].get(d, set())
        coll = bool(o5 and o9 and not (o5 & o9))
        if coll or (tot and ok == 0):
            sus.append((d, len(r9), tot, ok, o5, o9, coll))
    with open(os.path.join(OUT, "a5_communes_suspectes.tsv"), "w") as f:
        f.write("dep_A5\tcps2\troutines_ro9\tavec_partenaire_ro5\tpartenaire_accede_aussi\tro3_vers_ro5\tro3_vers_ro9\tcollision_ro3\n")
        for d, n9, tot, ok, o5, o9, coll in sus:
            f.write("$%04X\t%s\t%d\t%d\t%d\t%s\t%s\t%s\n" % (d, cps2(d), n9, tot, ok, ','.join('$%04X' % x for x in sorted(o5)),
                    ','.join('$%04X' % x for x in sorted(o9)), 'OUI' if coll else ''))
    print("communs suspects : %d (dont collisions ro3 : %d)" % (len(sus), sum(1 for s in sus if s[6])))
    ab = set(D5) - set(D9)
    print("ro5 seules : %d, dont accedees par des routines arcade exclusives : %d" % (len(ab), sum(1 for d in ab if D5[d]['routines'] & excl)))
    pickle.dump(dict(D5=D5, D9=D9, orig=orig), open(os.path.join(OUT, "a5.pkl"), "wb"))

if __name__ == "__main__":
    main()
