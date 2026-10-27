#!/usr/bin/env python3
"""preuve_ptrs.py CONSTRUCTION JOURNAL... : pointeurs de donnees PROUVES par le journal des conversions d'Upper
(lua/donnees_conv.lua : talons de donnees CONV_An, case d'origine en ROM) -> adresses exec (PS2) des cases ;
confrontes aux longs reloges dans le bloc de la greffe (constructions/<c>/greffe.json, greffe_donnees.bin).
Ecrit donnees/pointeurs_prouves.txt (cases exec, une par ligne) si SORTIE=1."""
import os, sys, json, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etape2'))
import donnees2 as D2
G = "<workspace>/work/greffe_arcade"
def exec_de(a):
    """adresse image 68K d'Upper (fige/ro5) -> adresse exec PS2 de la donnee"""
    if D2.U_DATA_BASE <= a < 0x3C0000:
        e = D2.LO + (a - D2.U_DATA_BASE); return e if e < D2.U_SPLIT else None
    if D2.U_EXT <= a < D2.U_EXT + 0x100000: return D2.U_SPLIT + (a - D2.U_EXT)
    if D2.F390 <= a < D2.F390_1: return a
    return None
def prouves(journaux):
    P = collections.Counter(); bad = 0
    for j in journaux:
        for l in open(j):
            if not l.startswith('E '): continue
            pc, t, v, a, f = l.split()[1:6]; t = int(t); v = int(v, 16); a = int(a, 16)
            if t >= 10 or f == '-' or not D2.source(v): continue
            e = exec_de(a)
            if e is None: continue
            b = D2.octets(e, 4)
            if len(b) < 4 or struct.unpack('<I', b)[0] != v: bad += 1; continue
            P[e] += 1
    return P, bad
if __name__ == "__main__":
    c = sys.argv[1]; P, bad = prouves(sys.argv[2:])
    print("cases prouvees : %d (incoherentes ecartees : %d)" % (len(P), bad))
    J = json.load(open(os.path.join(G, 'constructions', c, 'greffe.json')))
    blob = open(os.path.join(G, 'constructions', c, 'greffe_donnees.bin'), 'rb').read()
    st = collections.Counter(); copies = set()
    for a, b, o in J['regions']:
        a, b, o = int(a, 16), int(b, 16), int(o, 16)
        src = D2.octets(a, b - a)
        for i in range((-a) & 3, b - a - 3, 4):
            e = a + i; copies.add(e)
            p = struct.unpack_from('<I', src, i)[0]; q = struct.unpack_from('<I', blob, o + i)[0]
            if not D2.source(p): continue
            st[('reloge' if p != q else 'laisse') + (' prouve' if e in P else ' non prouve')] += 1
    for k, n in sorted(st.items()): print("  %-22s %d" % (k, n))
    print("  cases prouvees hors des regions copiees : %d" % sum(1 for e in P if e not in copies))
    if os.environ.get("SORTIE") == "1":
        open(os.path.join(G, 'donnees', 'pointeurs_prouves.txt'), 'w').write(''.join('%x\n' % e for e in sorted(P)))
