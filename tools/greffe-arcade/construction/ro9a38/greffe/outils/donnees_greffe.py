#!/usr/bin/env python3
"""ETAPE 4 : donnees d'Upper visees par le code a greffer, et leur service dans le ro9 augmente.
Pour chaque constante de donnees (exec Upper) formee par une routine a greffer (graphe_ro5 'data' + balayage) :
  - etendue = jusqu'a la constante de donnees suivante formee par N'IMPORTE QUEL code d'Upper (bornee a 8 Ko) ;
  - recherche du meme contenu dans les donnees d'Hyper (exact ; sinon pointeurs masques) -> REUTILISABLE (adresse ro9) ;
  - sinon A COPIER dans le bloc ajoute, avec la liste des longs a reloger (pointeurs de code / de donnees d'Upper).
Sorties : donnees/donnees_greffe.tsv, donnees/donnees_greffe.pkl {'reutil': {v5: v9}, 'copie': [(v5, taille, ptrs)]}."""
import os, sys, pickle, struct, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import greffe as GR
import commun as C
G = GR.G; EU = GR.EU
GR5 = pickle.load(open(os.path.join(EU, 'graphe_ro5.pkl'), 'rb'))
NOMMEES = {0x60B860: 'scripts de fin', 0x61B7A0: "listes d'adversaires", 0x61BC60: 'tables de scenes 6/8',
           0x61C1E0: 'table des scenes A5+4', 0x61C200: 'table scene 4 (A5+8)', 0x6283C0: 'table du chargeur de fin',
           0x60B380: 'table scene A ($148)', 0x5B61F0: 'rival (ro9)'}

def main():
    L = pickle.load(open(os.path.join(G, 'donnees', 'liste_arcade.pkl'), 'rb'))
    greffer = pickle.load(open(os.path.join(G, 'donnees', 'coeur_greffe.pkl'), 'rb'))     # etape 2 : coeur a greffer
    b5, b9 = C.load('ro5'), C.load('ro9')
    H5, H9 = GR.H5, GR.H9
    d5lo, d5hi = C.BASE + H5['code_end'], H5['data_end']
    d9lo, d9hi = C.BASE + H9['code_end'], H9['data_end']
    tous = sorted({v for s in GR5['data'].values() for v in s})
    refs = collections.defaultdict(set)
    for r in greffer:
        for v in GR5['data'].get(r, ()): refs[v].add(r)
    data9 = b9[H9['code_end']:]
    def est_ptr5(v): return GR.classe_valeur(v, H5) in ('code', 'data')
    lignes = []; reutil = {}; copie = []
    for v in sorted(refs):
        k = bisect.bisect_right(tous, v)
        fin = min(tous[k] if k < len(tous) else d5hi, v + 0x2000, d5hi)
        o = v - C.BASE; seg = b5[o:o + (fin - v)]
        ptrs = [(i, struct.unpack_from('<I', seg, i)[0]) for i in range(0, len(seg) - 3, 4)
                if est_ptr5(struct.unpack_from('<I', seg, i)[0])] if (v & 3) == 0 else []
        trouve = None
        if len(seg) >= 8 and any(seg):
            if not ptrs:
                j = data9.find(seg)
                if j >= 0 and data9.find(seg, j + 1) < 0: trouve = C.BASE + H9['code_end'] + j
                elif j >= 0: trouve = -1
            else:
                # contenu sans les pointeurs : premier morceau sans pointeur de >= 16 o comme ancre
                pos = [i for i, _ in ptrs]; bornes = [0] + [p + 4 for p in pos]; best = None
                for i, a in enumerate(bornes):
                    bb = pos[i] if i < len(pos) else len(seg)
                    if bb - a >= 16 and (best is None or bb - a > best[1] - best[0]): best = (a, bb)
                if best:
                    j = data9.find(seg[best[0]:best[1]])
                    if j >= 0:
                        cand = j - best[0]
                        ok = all(data9[cand + i:cand + i + 4] == seg[i:i + 4] or i in pos for i in range(0, len(seg) - 3, 4)) if cand >= 0 else False
                        if ok: trouve = C.BASE + H9['code_end'] + cand
        nom = next((n for a, n in NOMMEES.items() if v <= a < fin or a == v), '')
        if trouve and trouve > 0: reutil[v] = trouve; dec = 'reutilisable'
        else: copie.append((v, len(seg), ptrs)); dec = 'A COPIER' if trouve != -1 else 'A COPIER (ambigu)'
        nptr_c = sum(1 for _, p in ptrs if GR.classe_valeur(p, H5) == 'code'); nptr_d = len(ptrs) - nptr_c
        lignes.append((v, len(seg), dec, ('0x%X' % trouve) if trouve and trouve > 0 else '', nptr_c, nptr_d,
                       len(refs[v]), ' '.join('0x%X' % r for r in sorted(refs[v])[:4]), nom))
    with open(os.path.join(G, 'donnees', 'donnees_greffe.tsv'), 'w') as f:
        f.write("exec_upper\ttaille\tdecision\texec_hyper\tptr_code\tptr_donnees\tnb_routines\troutines\tnom\n")
        for l in lignes: f.write("0x%X\t%d\t%s\t%s\t%d\t%d\t%d\t%s\t%s\n" % l)
    pickle.dump(dict(reutil=reutil, copie=copie, lignes=lignes), open(os.path.join(G, 'donnees', 'donnees_greffe.pkl'), 'wb'))
    tc = sum(t for _, t, _ in copie); np_ = sum(len(p) for _, _, p in copie)
    print("constantes de donnees visees par le code greffe : %d ; reutilisables dans Hyper : %d ; a copier : %d (%d o, %.1f Ko), %d longs pointeurs a reloger" % (
        len(lignes), len(reutil), len(copie), tc, tc / 1024, np_))

if __name__ == "__main__":
    main()
