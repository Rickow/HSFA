#!/usr/bin/env python3
"""propage_id.py -- max-tables tracer, step 3: propagation of the ids. A field CARRIES a character id if it receives
(memory write) a value that is exactly a carrying field (no computation: extension / truncation only). Seeds: bytes
$102 and $116 of a structure (PS2). Fixed point over the writes of the graft build (Hyper + copies + stubs) and of
Upper. Field = (offset, 'A5' if based on A5, else 'S').

Usage:  nice -n 19 python3 -I propage_id.py [frozen_build] > sorties/propage_id.txt
Inputs: frozen build (argument or $HSFA_GRAFT_BUILD), module ro5. See paths.py.
Output: stdout, and $HSFA_REVIEW_OUT/porteurs.pkl.
"""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
X = L.charge(sys.argv[1] if len(sys.argv) > 1 else None)
def pur(v):
    """champ source si la valeur est un champ nu (a extension pres), sinon None ; 'tv' = lu dans une table"""
    while v[0] in ('ext',): v = v[2]
    if v[0] == 'ins':
        # octet/mot bas insere dans un registre : prendre la partie basse
        return pur(v[3])
    if v[0] == 'and' and v[3] in (0xff, 0x7f, 0x3f, 0xffff): return pur(v[2])
    if v[0] == 'f': return v
    return None
def cle(f):
    b = f[2]; off = f[3] & 0xffff
    if b[0] == 'r':
        n = b[2].split('~')[0].split('@')[0]
        return (off, 'A5' if n == 'A5' else 'S')
    # base = A5 + constante (zone des joueurs en A5 + $xxx) : structure
    return (off, 'S')
def cle_dest(bs, simm):
    if bs[0] == 'r':
        n = bs[2].split('~')[0].split('@')[0]
        if n[0] != 'A': return None
        return (simm & 0xffff, 'A5' if n == 'A5' else 'S')
    c, T = L.decompose(bs)
    if c is not None and len(T) == 1 and T[0][0] == 'r' and T[0][2].startswith('A5'):
        return None                      # A5 + constante + decalage : adresse de structure fixe, traite a part
    return (simm & 0xffff, 'S') if bs[0] in ('f', 'add') else None
P = {(0x102, 'S'): ('graine', 0), (0x116, 'S'): ('graine', 0)}
for nom, A in (('ro9a', X.A9), ('upper', X.A5)):
    pass
chg = True; tour = 0
W = collections.defaultdict(list)
while chg and tour < 6:
    chg = False; tour += 1
    for nom, A in (('ro9a', X.A9), ('upper', X.A5)):
        for (o, bs, simm, sz, v, rout) in A.sto:
            if sz != 1: continue
            f = pur(v)
            if f is None or f[4] != 1: continue
            k = cle(f)
            if k not in P: continue
            d = cle_dest(bs, simm)
            if d is None: continue
            W[d].append((nom, o, k))
            if d not in P: P[d] = (k, tour); chg = True
print("# champs porteurs d'un id (decalage PS2 ; A5 = global, S = structure) ; source ; tour ; nb d'ecritures (ro9a/upper) ; exemples")
for d, (src, t) in sorted(P.items(), key=lambda kv: (kv[1][1], kv[0][1], kv[0][0])):
    w = W.get(d, []); n9 = sum(1 for x in w if x[0] == 'ro9a'); n5 = len(w) - n9
    ex = ' '.join("%s:%06x<-$%x%s" % (x[0][0], x[1], x[2][0], x[2][1]) for x in w[:5])
    print("$%x(%s)\t%s\t%d\t%d/%d\t%s" % (d[0], d[1], ("$%x(%s)" % src) if t else src, t, n9, n5, ex))
pickle.dump((P, dict(W)), open(paths.sorties('porteurs.pkl'), 'wb'))
