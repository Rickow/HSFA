#!/usr/bin/env python3
"""HOMOLOGUES Upper (ro5) -> Hyper (ro9) PAR PROPAGATION (etape 2 de la greffe).

Le partenaire de l'etude (inverse_ro5, meilleur Jaccard sur instructions masquees) est faux pour les petites routines
toutes semblables (aiguilleurs de 3 instructions : 0x265120 -> 0x9A2C0 au lieu de 0x9A390). Ici :
  1. paires de depart = partenaires d'inverse_ro5 ;
  2. pour chaque paire, alignement des instructions (difflib sur les mots, cibles et moities hautes masquees) ;
     dans les blocs alignes, les cibles de jal/j et les constantes de code/donnees appariees donnent des paires ;
  3. tables de pointeurs de code appariees (constante de donnees Upper <-> Hyper) : entrees appariees par position ;
  4. les nouvelles paires de routines sont alignees a leur tour (point fixe).
Sortie : donnees/homologues.pkl {'code': {va5: (va9, votes, conflits)}, 'donnees': {exec5: (exec9, votes)}}
         donnees/homologues_resume.txt"""
import os, sys, struct, pickle, collections, difflib, bisect
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils")
import greffe as GR
import commun as C
from mips import Ins
G = GR.G; BASE = GR.BASE
b5, b9 = C.load('ro5'), C.load('ro9')
F5, F9 = C.funcs('ro5'), C.funcs('ro9')
S5, S9 = [a for a, _ in F5], [a for a, _ in F9]
E5 = dict(F5); E9 = dict(F9)
H5, H9 = GR.H5, GR.H9

def norm(w):
    op = w >> 26
    if op in (2, 3): return w & 0xFC000000
    if op in (0x0f, 0x09, 0x0d): return w & 0xFFFF0000
    return w

def ins(b, a, e):
    return [Ins(o, struct.unpack_from('<I', b, o)[0]) for o in range(a, e, 4)]

def consts(L):
    """indice -> ('jal', cible) | ('c', valeur 32 bits) (suivi des lui comme le traducteur)"""
    lu = {}; out = {}
    for k, x in enumerate(L):
        if x.m in ('jal', 'j'): out[k] = ('jal', x.tgt)
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if (x.m in GR.MEM or x.m in ('addiu', 'ori')) and x.rs in lu:
            v = (lu[x.rs] | x.imm) if x.m == 'ori' else (lu[x.rs] + x.simm) & 0xffffffff
            out[k] = ('c', v)
        d = GR.dest(x)
        if d is not None: lu.pop(d, None)
    return out

def est_code(v, h): return BASE + 0x22B00 <= v < BASE + h['code_end']
def est_donnee(v, h): return BASE + h['code_end'] <= v < h['data_end']

import functools
@functools.lru_cache(None)
def refs_donnees(mod):
    """constantes de donnees construites par le code (bornes des tables, comme translate.data_refs)"""
    h = H5 if mod == 'ro5' else H9; out = set()
    for a, e in (F5 if mod == 'ro5' else F9):
        for x, v in consts(ins(C.load(mod), a, e)).values() if False else ():
            pass
    lu = {}
    for x in C.instrs(mod):
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if x.m in ('addiu', 'ori') and x.rs in lu:
            v = (lu[x.rs] | x.imm) if x.m == 'ori' else (lu[x.rs] + x.simm) & 0xffffffff
            if est_donnee(v, h): out.add(v)
        d = GR.dest(x)
        if d is not None: lu.pop(d, None)
    return sorted(out)

def table_code(b, h, t, nmax=200):
    """entrees d'une table de pointeurs de code (s'arrete au premier long qui n'est pas du code, trous 0 admis,
    et a la table suivante referencee par le code)"""
    o = t - BASE; out = []
    R = refs_donnees('ro5' if h is H5 else 'ro9'); k = bisect.bisect_right(R, t); lim = R[k] if k < len(R) else 1 << 32
    while 0 <= o <= len(b) - 4 and len(out) < nmax and o + BASE < lim:
        v = struct.unpack_from('<I', b, o)[0]
        if v != 0 and not est_code(v, h): break
        out.append(v); o += 4
    while out and out[-1] == 0: out.pop()
    return out

def aligne(a5, a9):
    """paires (cible Upper, cible Hyper) des jal/constantes dans les blocs alignes de deux routines"""
    e5 = E5.get(a5); e9 = E9.get(a9)
    if e5 is None or e9 is None: return [], [], 0.0
    L5, L9 = ins(b5, a5, e5), ins(b9, a9, e9)
    if len(L5) > 4000 or len(L9) > 4000: return [], [], 0.0
    n5 = [norm(x.w) for x in L5]; n9 = [norm(x.w) for x in L9]
    sm = difflib.SequenceMatcher(None, n5, n9, autojunk=False)
    c5, c9 = consts(L5), consts(L9)
    code, data = [], []
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            p, q = c5.get(i + k), c9.get(j + k)
            if not p or not q or p[0] != q[0]: continue
            v5, v9 = p[1], q[1]
            if p[0] == 'jal' or (est_code(v5, H5) and est_code(v9, H9)):
                if est_code(v5, H5) and est_code(v9, H9): code.append((v5 - BASE, v9 - BASE))
            elif est_donnee(v5, H5) and est_donnee(v9, H9): data.append((v5, v9))
    return code, data, sm.ratio()

def main():
    INV = GR.INV
    votes = collections.defaultdict(collections.Counter); dvotes = collections.defaultdict(collections.Counter)
    file_ = collections.deque(); vu = set(); ratio = {}
    for a, r in INV.items():
        if r['partenaire'] is not None and not r['nat'] and r['taille'] >= 96 and r['score'] >= 0.7:
            file_.append((a, r['partenaire']))
    tours = 0
    while file_:
        a5, a9 = file_.popleft()
        if (a5, a9) in vu or a5 not in E5 or a9 not in E9: continue
        vu.add((a5, a9)); tours += 1
        code, data, rt = aligne(a5, a9); ratio[(a5, a9)] = rt
        if rt < 0.6: continue
        for c5, c9 in code:
            # cible au debut d'une routine des deux cotes : paire de routines
            if c5 in E5 and c9 in E9:
                votes[c5][c9] += 1
                if (c5, c9) not in vu: file_.append((c5, c9))
        for d5, d9 in data:
            dvotes[d5][d9] += 1
            t5, t9 = table_code(b5, H5, d5), table_code(b9, H9, d9)
            if len(t5) >= 2 and len(t5) == len(t9):
                for x5, x9 in zip(t5, t9):
                    if x5 and x9 and (x5 - BASE) in E5 and (x9 - BASE) in E9:
                        votes[x5 - BASE][x9 - BASE] += 1
                        if (x5 - BASE, x9 - BASE) not in vu: file_.append((x5 - BASE, x9 - BASE))
    hom = {}
    for c5, cnt in votes.items():
        (best, n), = cnt.most_common(1)
        hom[c5] = (best, n, sum(cnt.values()) - n)
    dhom = {d5: cnt.most_common(1)[0] + (sum(cnt.values()) - cnt.most_common(1)[0][1],) for d5, cnt in dvotes.items()}
    pickle.dump({'code': hom, 'donnees': dhom, 'ratio': ratio, 'donnees_tous': {d5: dict(c) for d5, c in dvotes.items()}},
                open(os.path.join(G, 'donnees', 'homologues.pkl'), 'wb'))
    # comparaison avec inverse_ro5
    acc = dis = nouv = 0; ex = []
    for c5, (c9, n, cf) in hom.items():
        p = INV.get(c5, {}).get('partenaire')
        if p is None: nouv += 1
        elif p == c9: acc += 1
        else:
            dis += 1
            if len(ex) < 40: ex.append("0x%X : inverse_ro5 0x%X (%s), propage 0x%X (%d votes, %d contre)" % (c5, p, INV[c5]['classe'], c9, n, cf))
    with open(os.path.join(G, 'donnees', 'homologues_resume.txt'), 'w') as f:
        f.write("paires alignees : %d ; routines Upper avec homologue propage : %d (accord inverse_ro5 %d, desaccord %d, nouvelles %d)\n"
                % (tours, len(hom), acc, dis, nouv))
        f.write("constantes de donnees appariees : %d\n" % len(dhom))
        f.write("\n".join(ex) + "\n")
    print(open(os.path.join(G, 'donnees', 'homologues_resume.txt')).read())

if __name__ == "__main__":
    main()
