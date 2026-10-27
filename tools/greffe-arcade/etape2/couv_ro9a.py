#!/usr/bin/env python3
"""COUVERTURE D'UNE PARTIE ro9a COMPAREE A L'ORACLE UPPER, par etat de scene (A5+0/+4/+8/+C).
  - ro9a : mot lu -> carte_image de la construction -> va MIPS du module augmente -> routine greffee (routine d'Upper
    d'origine, par les blocs de greffe.json) ou routine d'Hyper ;
  - Upper : traces/<trace>/couv.txt sur fige/ro5 (outils/couverture.py).
Pour un etat donne : routines d'Upper executees par Upper dont la contrepartie (copie greffee ou homologue d'Hyper
selon les decisions) n'a PAS ete executee par ro9a dans le meme etat.
Usage : couv_ro9a.py CONSTRUCTION TRACE_RO9A TRACE_UPPER ["0002 0004 0002 0000"]"""
import os, sys, bisect, json, collections
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils")
import couverture as CV
import commun as C
G = CV.G; BASE = 0x1F0000

def charge_ro9a(cons, trace):
    J = json.load(open(os.path.join(G, 'constructions', cons, 'greffe.json')))
    blocs = sorted((int(n, 16), int(a, 16), int(b, 16)) for a, b, n in J['blocs'])
    bn = [n for n, _, _ in blocs]
    synth = {int(v, 16) - BASE: k for k, v in J['synth'].items()}
    off, va = [], []
    for l in open(os.path.join(G, 'constructions', cons, 'b9', 'carte_image.txt')):
        p = l.split(None, 2); off.append(int(p[0], 16)); va.append(int(p[1], 16))
    st9 = C.starts('ro9'); st5 = C.starts('ro5')
    def routine(v):
        k = bisect.bisect_right(bn, v) - 1
        if k >= 0:
            n, a, b = blocs[k]
            if n <= v < n + (b - a):
                f = a + (v - n); return ('U', st5[bisect.bisect_right(st5, f) - 1])
        for s, nm in synth.items():
            if s <= v < s + 0x80: return ('S', nm)
        return ('H', st9[bisect.bisect_right(st9, v) - 1])
    noms = {}; R = collections.defaultdict(dict)
    for l in open(os.path.join(G, 'traces', trace, 'couv.txt')):
        p = l.split()
        if p[0] == 'E': noms[int(p[1])] = ' '.join(p[2:]); continue
        a = int(p[0], 16); sid, fr = int(p[1]), int(p[2])
        i = bisect.bisect_right(off, a) - 1
        if i < 0 or (i + 1 < len(off) and a >= off[i + 1] + 6): continue
        r = routine(va[i]); e = R[r]; n = noms.get(sid, '?')
        e[n] = min(e.get(n, 1 << 30), fr)
    # les noms d'etats sont lus apres : remap
    R2 = collections.defaultdict(dict)
    for r, e in R.items():
        for n, fr in e.items(): R2[r][n] = fr
    return R2, J

def main():
    cons, t9, t5 = sys.argv[1], sys.argv[2], sys.argv[3]
    etat = sys.argv[4] if len(sys.argv) > 4 else None
    R9, J = charge_ro9a(cons, t9)
    dec = {int(f, 16): d for f, d in J['decisions'].items()}
    R5, _, noms5 = CV.charge('ro5', t5)
    vu9 = collections.defaultdict(set)
    for r, e in R9.items():
        for n in e: vu9[n].add(r)
    etats = sorted({n for e in R5.values() for n in e['etats']} if not etat else {etat})
    for n in etats:
        if not n.startswith('0002'): continue
        u = [r for r, e in R5.items() if n in e['etats']]
        manque = []
        for r in sorted(u):
            d = dec.get(r)
            if d is None: continue
            if d[0] == 'GREFFE': ok = ('U', r) in vu9[n]
            elif d[0] == 'HYPER': ok = ('H', int(d[1], 16)) in vu9[n]
            else: continue
            if not ok: manque.append((R5[r]['etats'][n], r, d))
        print("== etat %s : Upper %d routines (%d decidees) ; ro9a %d ; contreparties absentes : %d" % (
            n, len(u), sum(1 for r in u if r in dec), len(vu9[n]), len(manque)))
        for fr, r, d in sorted(manque)[:40]:
            print("   image %6d  0x%06X  %s" % (fr, r, ' '.join(d)))

if __name__ == "__main__":
    main()
