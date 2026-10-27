"""Taille usuelle de chaque champ d(A6) côté 68K arcade (sur tout le code des persos) et correspondance PSP -> 68K
complète : zones (chaîne croissante) + champs hors zones à vote majoritaire (ex. 0x334 <-> $1FE)."""
import json, collections, sys
import rosette
from champs import acc68
def tailles():
    T = collections.defaultdict(collections.Counter)
    for c, (ent, lo, hi) in rosette.ARC_ENTRIES.items():
        for e in ent:
            if lo <= e < hi:
                for off, sz, rw in acc68(e, hi): 
                    if sz: T[off][sz] += 1
    return {o: v.most_common(1)[0][0] for o, v in T.items()}
def carte_champs(min_votes=3, part=0.6):
    J = json.load(open("champs_votes.json"))
    votes = {int(o, 16): {int(p, 16): n for p, n in v.items()} for o, v in J["votes"].items()}
    psp2m = {}
    for o, p, k in J["chaine"]: psp2m[p] = (o, "zone")
    inv = collections.defaultdict(collections.Counter)
    for o, v in votes.items():
        for p, n in v.items(): inv[p][o] += n
    for p, v in inv.items():
        if p in psp2m: continue
        (o, n), tot = v.most_common(1)[0], sum(v.values())
        if n >= min_votes and n / tot >= part: psp2m[p] = (o, "vote %d/%d" % (n, tot))
    return psp2m
if __name__ == "__main__":
    t = tailles(); json.dump({"%x" % o: s for o, s in t.items()}, open("tailles68.json", "w"))
    m = carte_champs()
    json.dump({"%x" % p: ["%x" % o, w] for p, (o, w) in m.items()}, open("carte_champs.json", "w"), indent=0)
    print("tailles :", len(t), "; champs PSP -> 68K :", len(m), "dont hors zones :", sum(1 for v in m.values() if v[1] != "zone"))
    print([("0x%x" % p, "$%x" % o, w) for p, (o, w) in sorted(m.items()) if w != "zone"][:40])
