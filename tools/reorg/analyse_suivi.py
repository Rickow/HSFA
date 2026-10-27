#!/usr/bin/env python3
"""ANALYSE DU SUIVI DES ECRIVAINS (passe 2) : pour chaque case RAM qui a fourni un pointeur PS2 converti, qui l'ecrit
et d'ou vient la valeur (copie d'une table ROM / d'une autre case RAM / immediat ou calcul).
Usage : analyse_suivi.py SORTIE suivi1.txt [suivi2.txt ...]"""
import sys, os, collections, json, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse_conv import carte, zone_cell, DATA_ADD, zone_ps2
def main():
    pref = sys.argv[1]; C = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for fn in sys.argv[2:]:
        for l in open(fn):
            _, c, w, pc, v, src, n = l.split()
            c, w, pc, v, src, n = int(c, 16), int(w, 16), int(pc, 16), int(v, 16), int(src, 16), int(n)
            if v == 0: continue                                    # effacements
            z = zone_cell(src) if src else "immediat/calcul"
            C[c][pc][(w, z, src)] += n
    o = open(pref + ".txt", "w"); js = {}
    tot = collections.Counter()
    for c in sorted(C):
        print("case %06x (A5%+05x)" % (c, c - 0xFF8000), file=o); js["%06x" % c] = []
        for pc, cnt in sorted(C[c].items(), key=lambda x: -sum(x[1].values())):
            va, mn = carte(pc)[1], carte(pc)[2]
            zs = collections.Counter()
            for (w, z, src), n in cnt.items(): zs[z] += n
            srcs = collections.Counter()
            for (w, z, src), n in cnt.items():
                if src and w == 0: srcs[src] += n
            ex = ", ".join("%06x%s" % (s, (" (PS2 %06x)" % (s - DATA_ADD)) if 0x93000 <= s < 0x3C0000 else "") for s, _ in srcs.most_common(4))
            print("   ecrivain %06x va %07x %-60s | %s | sources %s" % (pc, va, mn[:60], ", ".join("%s %d" % x for x in zs.most_common()), ex), file=o)
            js["%06x" % c].append({"pc": "%06x" % pc, "va": "%07x" % va, "src": mn[:120], "zones": dict(zs), "sources": ["%06x" % s for s, _ in srcs.most_common(8)]})
            tot[max(zs, key=zs.get)] += 1
    print("\necrivains par provenance dominante : " + ", ".join("%s %d" % x for x in tot.most_common()), file=o)
    o.close(); json.dump(js, open(pref + ".json", "w"), indent=1); print(open(pref + ".txt").read())
if __name__ == "__main__": main()
