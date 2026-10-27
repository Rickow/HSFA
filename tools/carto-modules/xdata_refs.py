#!/usr/bin/env python3
"""Tables de numeros d'entrees X_DATA dans les DONNEES de chaque module : suites de >= 5 mots u16 (ou u32) tous dans
[203, 552] (au moins 3 valeurs distinctes). Rend, par module, les tables et l'ensemble des entrees citees, classees par
groupe (b, ro1...ro9 du manifeste)."""
import sys, struct, collections, csv
sys.path.insert(0, '.')
import commun as C
G = [(203, 'b'), (206, 'ro1'), (224, 'ro2'), (253, 'ro3'), (348, 'ro4'), (350, 'ro5'), (526, 'ro6'), (536, 'ro7'), (543, 'ro8'), (544, 'ro9'), (553, None)]
def grp(i):
    for k in range(len(G) - 1):
        if G[k][0] <= i < G[k+1][0]: return G[k][1]
man = {int(r['idx']): r for r in csv.DictReader(open('<workspace>/anthology_extract/manifest.csv'))}
def runs(d, a0, sz):
    fmt = '<H' if sz == 2 else '<I'; n = (len(d) - a0) // sz; o = a0; out = []
    while o < len(d) - sz:
        v = struct.unpack_from(fmt, d, o)[0]
        if 203 <= v <= 552:
            k = o; vs = []
            while k < len(d) - sz:
                w = struct.unpack_from(fmt, d, k)[0]
                if 203 <= w <= 552: vs.append(w); k += sz
                else: break
            if len(vs) >= 5 and len(set(vs)) >= 3: out.append((o, vs))
            o = k
        else: o += sz
    return out
for m in sys.argv[1:] or ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
    d = C.load(m); e = C.header(m)['code_end'] + 0x40
    tous = collections.Counter()
    print('=== %s' % m)
    for sz in (2, 4):
        for o, vs in runs(d, e, sz):
            s = sorted(set(vs)); tous.update(s)
            print('  u%d exec %#x (fichier %#x) n=%d : %s' % (8 * sz, o + 0x1F0000, o, len(vs), ' '.join('e%d' % v for v in vs[:48])))
    par = collections.defaultdict(list)
    for v in sorted(tous): par[grp(v)].append(v)
    print('  -> entrees citees par groupe : ' + ' ; '.join('%s: %s' % (g, ','.join(str(v) for v in vs)) for g, vs in par.items()))
