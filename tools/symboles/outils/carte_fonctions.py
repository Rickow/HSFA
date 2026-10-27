#!/usr/bin/env python3
"""Table des fonctions de ro3 dans les trois espaces : MIPS (cibles de jal) -> image traduite
(carte_image.txt) -> ROM arcade (alignement d'instructions, aligne.py ; 2e passe LCS bornée par
les voisines pour les fonctions restées sans ancre). Sortie : _cache/fonctions.json"""
import sys, os, json, pickle, bisect, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aligne as AL, desasm as D, fonctions as F
ICI = os.path.dirname(os.path.abspath(__file__))
CA = os.path.join(ICI, '..', '_cache')

def main():
    table = pickle.load(open(os.path.join(CA, 'reloc_a5.pkl'), 'rb'))
    T, A, tt, ta = AL.charge(table)
    m = pickle.load(open(os.path.join(CA, 'alignement.pkl'), 'rb'))
    tadr = [x[0] for x in T]; aadr = [x[0] for x in A]
    starts, fin = F.debuts_mips(); C = F.carte(); E = F.entrees_trad(starts, C)
    natifs = set(int(x, 16) for x in json.load(open('<workspace>/work/carto_ro5/natifs_ro3.json')))
    cib = set(); prev = set()
    for k, (a, n, mn, ops) in enumerate(A):
        if mn in ('jsr', 'bsr'):
            mm = re.match(r'\$([0-9a-f]+)', ops)
            if mm: cib.add(int(mm.group(1), 16))
        if k and A[k-1][2] in ('rts', 'jmp', 'bra', 'rte'): prev.add(a)
    out = []
    for k, s in enumerate(starts):
        e = starts[k+1] if k+1 < len(starts) else fin
        f = {'mips': s, 'mips_fin': e, 'natif': s in natifs}
        if s in E:
            t0 = E[s][0]; t1 = E[e][0] if e in E else F.bornes_trad()[0]
            # fonctions sans code 68K propre (natives : la carte saute) -> t1 <= t0
            if t1 <= t0: t1 = t0 + 2
            f['trad'] = t0; f['trad_fin'] = t1
            i0 = bisect.bisect_left(tadr, t0); i1 = bisect.bisect_left(tadr, t1)
            n = i1 - i0; al = [tadr[i] for i in range(i0, i1) if tadr[i] in m]
            f['n'] = n; f['score'] = round(len(al) / max(1, n), 3)
            if t0 in m: f['arcade'] = m[t0][0]; f['methode'] = 'aligné'
            else:
                for i in range(i0, min(i1, i0 + 8)):
                    if tadr[i] in m:
                        a = m[tadr[i]][0]; a2 = a - (tadr[i] - t0)
                        # préfixe ajouté par le portage (ex. JSR vers une aide) : l'entrée arcade est la 1re
                        # instruction alignée si elle suit une rupture ou est appelée ; sinon on recule
                        if a in cib or a in prev: f['arcade'] = a; f['methode'] = 'décalé (préfixe du portage)'
                        elif a2 in cib or a2 in prev: f['arcade'] = a2; f['methode'] = 'décalé'
                        else: f['arcade'] = a; f['methode'] = 'décalé (incertain)'
                        break
            if al:
                last = al[-1]; j = bisect.bisect_left(aadr, m[last][0])
                f['arcade_fin'] = A[j][0] + A[j][1]
        out.append(f)
    # 2e passe : fonctions sans ancre, encadrées par deux voisines placées dans l'ordre
    n2 = 0
    for k, f in enumerate(out):
        if 'arcade' in f or 'trad' not in f or f['natif']: continue
        p = next((out[q] for q in range(k-1, max(-1, k-6), -1) if 'arcade' in out[q]), None)
        q_ = next((out[q] for q in range(k+1, min(len(out), k+6)) if 'arcade' in out[q]), None)
        if not p or not q_: continue
        a0 = p.get('arcade_fin', p['arcade']); a1 = q_['arcade']
        if not (0 < a1 - a0 < 0x3000): continue
        i0 = bisect.bisect_left(tadr, f['trad']); i1 = bisect.bisect_left(tadr, f['trad_fin'])
        j0 = bisect.bisect_left(aadr, a0); j1 = bisect.bisect_left(aadr, a1)
        if (i1 - i0) * (j1 - j0) > 400000 or i1 <= i0: continue
        pr = AL.lcs(tt[i0:i1], ta[j0:j1])
        if len(pr) >= max(3, 0.4 * (i1 - i0)):
            x, y = pr[0]
            f['arcade'] = A[j0 + y][0] - (T[i0 + x][0] - f['trad']) if x else A[j0 + y][0]
            f['methode'] = 'lcs-voisines'; f['score'] = round(len(pr) / (i1 - i0), 3)
            x, y = pr[-1]; f['arcade_fin'] = A[j0 + y][0] + A[j0 + y][1]; n2 += 1
    for f in out:
        if 'arcade' in f:
            a = f['arcade']
            f['entree_arcade'] = 'appelée' if a in cib else ('après rupture' if a in prev else 'interne')
    json.dump(out, open(os.path.join(CA, 'fonctions.json'), 'w'), indent=0)
    c = collections.Counter(f.get('methode', 'natif' if f['natif'] else 'aucune') for f in out)
    print(len(out), 'fonctions MIPS ;', dict(c), '; 2e passe', n2)
    c2 = collections.Counter(f.get('entree_arcade') for f in out if 'arcade' in f); print(dict(c2))

if __name__ == '__main__':
    main()
