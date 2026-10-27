"""(agent_integration_max) lectures indexées par l'ID trouvées par DIFFÉRENCE de deux espionnages (lua/espion.lua) faits
avec deux ID (A = $26 Eagle, B = $2D ou $2E) : pour un même pc (lisant peu d'adresses), une adresse lue seulement avec B
dont l'homologue à A (écart (B-A)·e) n'est lue qu'avec A -> table lue par ID, base = adresse - B·e. Les copies agrandies
($E80000+) sont écartées. Usage : diff_index.py espion_A espion_B idA idB [table.json des copies : max_agrandies.txt]"""
import sys, collections
def lit(f):
    D = collections.defaultdict(set)
    for l in open(f):
        o, pc = l.split()[:2]; o = int(o, 16)
        if 0xE80000 <= o < 0xF00000: continue
        D[pc].add(o)
    return D
A, B, ia, ib = lit(sys.argv[1]), lit(sys.argv[2]), int(sys.argv[3], 16), int(sys.argv[4], 16)
d = ib - ia
R = collections.defaultdict(set)
for pc, ob in B.items():
    oa = A.get(pc, set())
    if len(ob) > 64 or len(oa) > 64: continue          # copieurs génériques
    for o in ob - oa:
        for e in (2, 4, 8, 16, 32, 64, 128):
            if o - d * e in oa and o - d * e not in ob: R[(o - ib * e, e)].add(pc)
        for dd in (d - 2, d, d + 2):
            if o - dd in oa and o - dd not in ob: R[((o - ib) & ~1, 1)].add(pc)
for (b, e), p in sorted(R.items()):
    ps2 = b - 0xA1000 + 0x60ACC0 if b < 0x3A0000 else b - 0xC80000 + 0x904AE0
    print("%06x (PS2 %06x) e=%d %s" % (b, ps2, e, ",".join(sorted(p))))
