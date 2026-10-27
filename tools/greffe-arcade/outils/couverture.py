#!/usr/bin/env python3
"""Couverture d'execution par routine (GRAIN=routine de carto_ro9) a partir des prises sur l'espace opcodes
(traces/<nom>/couv.txt de tournee_greffe.lua ou ram_hyper.lua).
  - mot 68K lu -> instruction de la carte d'image (carte_image.txt du module) -> va MIPS -> routine ;
  - PRELECTURE : le 68000 lit 1-2 mots au-dela de la derniere instruction executee. Un mot lu dans les 4 premiers
    octets d'un bloc contigu d'une routine qui suit le bloc d'une autre routine ne compte pas ; une routine est
    executee si au moins un mot lu « franc » lui appartient. Les routines dont tous les blocs font <= 4 octets sont
    marquees « courte » (indecidable par ce critere).
Usage (bibliotheque) : charge(mod, trace) -> dict routine -> {'k0': 1re image, 'etats': {nom d'etat: 1re image}}"""
import os, sys, bisect, pickle, functools, collections
G = "<workspace>/work/greffe_arcade"
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
CARTE = {'ro5': "<workspace>/work/greffe_arcade/fige/ro5/carte_image.txt", 'ro9': "<workspace>/work/greffe_arcade/fige/ro9/carte_image.txt"}

@functools.lru_cache(None)
def carte(mod):
    off, va = [], []
    for l in open(CARTE[mod]):
        p = l.split(None, 2); off.append(int(p[0], 16)); va.append(int(p[1], 16))          # va MIPS = decalage FICHIER
    st = C.starts(mod)
    rt = [st[bisect.bisect_right(st, v) - 1] if bisect.bisect_right(st, v) else None for v in va]
    # debut de bloc contigu (meme routine que l'instruction precedente ?) et longueur du bloc
    blk = [0] * len(off); deb = 0
    for i in range(len(off)):
        if i == 0 or rt[i] != rt[i - 1]: deb = off[i]
        blk[i] = deb
    fin_blk = {}
    for i in range(len(off)):
        nxt = off[i + 1] if i + 1 < len(off) else off[i] + 2
        fin_blk[blk[i]] = max(fin_blk.get(blk[i], 0), nxt)
    prec_autre = {}
    for i in range(len(off)):
        if blk[i] == off[i]: prec_autre[off[i]] = (i > 0 and rt[i - 1] != rt[i])
    return off, va, rt, blk, fin_blk, prec_autre

def charge(mod, trace):
    off, va, rt, blk, fin_blk, prec = carte(mod)
    noms = {}; R = {}; courtes = collections.defaultdict(dict)
    f = os.path.join(G, 'traces', trace, 'couv.txt')
    for l in open(f):
        p = l.split()
        if p[0] == 'E': noms[int(p[1])] = ' '.join(p[2:]); continue
        a = int(p[0], 16)
        if len(p) == 3: sid, fr = int(p[1]), int(p[2])
        else: sid, fr = 0, int(p[1])
        i = bisect.bisect_right(off, a) - 1
        if i < 0 or rt[i] is None: continue
        if i + 1 < len(off) and a >= off[i + 1]: continue
        r = rt[i]; b = blk[i]
        if fin_blk[b] - b <= 4:
            e = courtes[r]; e[sid] = min(e.get(sid, 1 << 30), fr); continue
        if a - b < 4 and prec.get(b): continue
        e = R.setdefault(r, {'k0': fr, 'etats': {}}); e['k0'] = min(e['k0'], fr)
        e['etats'][sid] = min(e['etats'].get(sid, 1 << 30), fr)
    for r, e in R.items(): e['etats'] = {noms.get(s, '?'): k for s, k in e['etats'].items()}
    C_ = {r: {noms.get(s, '?'): k for s, k in e.items()} for r, e in courtes.items() if r not in R}
    return R, C_, noms

if __name__ == "__main__":
    mod, tr = sys.argv[1], sys.argv[2]
    R, Cr, noms = charge(mod, tr)
    print("%s %s : %d routines executees, %d courtes seulement, %d etats" % (mod, tr, len(R), len(Cr), len(noms)))
