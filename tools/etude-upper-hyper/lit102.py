#!/usr/bin/env python3
"""Lectures de l'identifiant perso $102 (numerotation PS2, lb/lbu d=0x102 sur une case registre A0-A6) dans le code
d'Upper a reporter (voie B) : ces sites indexent des tables a 40 entrees ou comparent l'id ; dans Hyper l'id va
jusqu'a $7F (versions) -> a passer par $116 (perso de base) ou a etendre."""
import os, sys, pickle, collections
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
BA = pickle.load(open(os.path.join(OUT, "bilan_absent.pkl"), "rb"))
def sites(mod, routines, champ=0x102):
    n = collections.Counter()
    F = dict(AT.G(mod)['funcs'])
    for a in routines:
        regs = set()
        for x in C.seg(mod, a, F[a]):
            if x.m == 'lw' and 0x1100 <= x.imm <= 0x1118: regs.add(x.rt); continue
            if x.m in ('lb', 'lbu') and x.rs in regs and x.imm == champ: n[a] += 1
            if x.m in ('sb',) and x.rs in regs and x.imm == champ: n[a] += 0
            d = x.rt if x.m in ('lb','lbu','lh','lhu','lw','andi','lui','ori','addiu') else (x.rd if x.op == 0 else None)
            if d is not None: regs.discard(d)
    return n
groupes = collections.defaultdict(set)
for a, s in BA['scene'].items():
    if BA['etat'][a] == 'absent': groupes['absent / ' + s].add(a)
    elif s != 'autre': groupes['present ou modifie / ' + s].add(a)
for g in sorted(groupes):
    n = sites('ro5', groupes[g])
    print("%-40s %4d routines : %4d lectures de $102 dans %d routines" % (g, len(groupes[g]), sum(n.values()), len(n)))
