#!/usr/bin/env python3
"""entetes40.py -- max-tables tracer, net 5 (data only, without the code): every HEADER of 40 relative u16 offsets
(first word = $50, 40 words in [$50, $8000), mostly increasing) in Hyper's data and in Upper's data COPIED by the
graft; and the headers of 128 (first word = $100). Marks: in TABLES.tsv or not; readers (constant built by the code);
pointed to by a known table. Finds the tables reached through a pointer.

Usage:  nice -n 19 python3 -I entetes40.py [frozen_build] > sorties/entetes40.txt
Inputs: frozen build (argument or $HSFA_GRAFT_BUILD), $HSFA_REVIEW_OUT/TABLES.tsv (maitre.py). See paths.py.
"""
import sys, os, struct, bisect, collections, csv
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
X = L.charge(sys.argv[1] if len(sys.argv) > 1 else None, upper=False); A9 = X.A9; BASE = L.BASE
rows = list(csv.reader(open(paths.sorties('TABLES.tsv'), encoding='utf-8'), delimiter='\t'))[1:]
connues = {int(r[0][2:], 16): r for r in rows if r[0].startswith('T_')}
def cherche(buf, deb, fin, n, premier):
    out = []
    o = deb
    while o + 2 * n <= fin:
        if buf[o] == (premier & 0xff) and buf[o + 1] == (premier >> 8):
            w = struct.unpack_from('<%dH' % n, buf, o)
            if all(premier <= x < 0x8000 for x in w) and len(set(w)) >= 8 and sum(w[i + 1] >= w[i] for i in range(n - 1)) >= 0.75 * (n - 1):
                out.append(o); o += 2 * n; continue
        o += 2
    return out
res = []
# Hyper : donnees du module
for n, p in ((40, 0x50), (128, 0x100)):
    for o in cherche(X.b9, X.ce9, X.fin9 - BASE, n, p): res.append((o + BASE, n, 'Hyper', None))
    for (cp, lg, u) in X.regs:
        if u - BASE + lg > len(X.b5) or u < BASE: continue
        for o in cherche(X.b5, u - BASE, u - BASE + lg, n, p): res.append((cp + o + BASE - u, n, 'copie', o + BASE))
# pointeurs de donnees vers ces tables : recherche du long dans les donnees (Hyper : adresse ; Upper : adresse d'Upper)
def pointe(adr, buf, deb, fin):
    pat = struct.pack('<I', adr); out = []; i = buf.find(pat, deb)
    while 0 <= i < fin:
        if i % 2 == 0: out.append(i + BASE)
        i = buf.find(pat, i + 1)
    return out
for a, n, cote, u in sorted(res):
    k = connues.get(a)
    lect = collections.Counter(X.cote(o) for o in A9.csite.get(a, ()))
    pts = pointe(a, X.b9, X.ce9, X.fin9 - BASE) if cote == 'Hyper' else pointe(u, X.b5, X.ce5, len(X.b5))
    print("T_%06x %s n=%d %s%s lecteurs=%s pointee_par=%d%s" % (a, cote, n, ('U %06x ' % u) if u else '', 'CONNUE' if k else 'ABSENTE', dict(lect), len(pts), (' ex. %s' % ' '.join('%x' % p for p in pts[:4])) if pts else ''))
