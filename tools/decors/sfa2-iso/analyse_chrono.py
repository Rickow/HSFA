#!/usr/bin/env python3
"""analyse_chrono.py (oracle, local) : résume les chronologies MAME (mame/out_chrono/stgXX_chrono.txt, sonde
lua/anim_sfa2.lua) : objets (classe, sous-type, cadres rapportés aux racines de l'arcade), cases de tilemap et couleurs
qui changent, rowscroll, registres. Usage : analyse_chrono.py [STG …]"""
import sys, os, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arcade_anims as AA
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ICI, "mame", "out_chrono")

def lit(stg):
    E = collections.defaultdict(list)
    for li in open(os.path.join(CH, "stg%s_chrono.txt" % stg)):
        p = li.split(); E[p[0]].append(p[1:])
    return E

def racines():
    S = AA.racines_statiques(); I = AA.racines_indirectes()
    tout = {r: v[0] for r, v in S.items()}
    for r, (e, _) in I.items(): tout.setdefault(r, e)
    return tout

if __name__ == "__main__":
    tout = racines(); idx, info = AA.index_cadres(tout)
    stgs = sys.argv[1:] or ["%02X" % s for s in range(0, 0x24, 2)]
    for stg in stgs:
        E = lit(stg); print("=" * 20, stg)
        objs = collections.defaultdict(list)
        for k, pool, slot, act, cls, sub, fr, dur, x, y in E["o"]:
            objs[(pool, int(slot))].append((int(k), cls, sub, int(fr, 16), int(dur, 16)))
        for (pool, slot), L in sorted(objs.items()):
            cs = sorted({(c, s) for _, c, s, _, _ in L})
            frs = [f for _, _, _, f, _ in L]
            rs = collections.Counter()
            for f in frs:
                m = idx.get(f & 0xFFFFFF)
                rs["$%06X/%d" % (m[0], m[1]) if m else "?%06X" % (f & 0xFFFFFF)] += 1
            print(" %s%-2d %s  %d chg  %s" % (pool, slot, " ".join("%s.%s" % c for c in cs), len(L),
                  " ".join("%s×%d" % kv for kv in sorted(rs.items())[:6])))
        for n in "123":
            T = [e for e in E["t"] if e[1] == n]
            if T:
                ks = {int(e[0]) for e in T}; cells = {int(e[2]) for e in T}
                print("  tilemap s%s : %d écritures, %d cases, %d images (%d..%d)" % (n, len(T), len(cells), len(ks), min(ks), max(ks)))
        P = E["p"]
        if P:
            k0 = min(int(e[0]) for e in P)
            pc = collections.Counter(int(e[1]) // 16 for e in P if int(e[0]) > k0)
            print("  palettes (après la 1re image) : " + " ".join("%s%d:%d" % ("o" if p < 14 else "s%d." % ((p - 32) // 32 + 1), p if p < 14 else (p - 32) % 32, n) for p, n in sorted(pc.items())))
        Lr = E["l"]
        if Lr:
            ks = sorted({int(e[0]) for e in Lr}); print("  rowscroll : %d mots changés sur %d images" % (len(Lr), len(ks)))
        R = E["r"]; print("  registres : %d changements" % len(R))
        C = collections.Counter(int(e[1]) for e in E["c"]); print("  tics/image : %s" % dict(C))
