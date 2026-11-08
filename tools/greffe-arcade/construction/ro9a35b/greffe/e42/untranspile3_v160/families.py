#!/usr/bin/env python3
"""FAMILLES DE ROUTINES = TYPES D'OBJETS, inferees par les aiguillages d'etat.

Chez Capcom, un objet (A6) est pilote par un automate : 'MOVE.B 4(A6),D0 ;
MOVE.W tbl(PC,D0.W),D1 ; JMP tbl(PC,D1.W)'. Toutes les routines d'une meme table
traitent le MEME type d'objet, ainsi que la routine qui fait l'aiguillage. Les
sous-etats (tables appelees depuis une routine d'etat) rejoignent la famille.

Pourquoi : la disposition memoire du recompilateur depend du TYPE d'objet (un meme
deplacement est un long dans un type, un mot dans un autre). Les statistiques de
largeur doivent donc etre prises par famille, pas globalement.

Seuls les aiguillages relient des routines : les appels simples (jal) ne le font pas,
car les routines utilitaires sont partagees entre types et fusionneraient tout.
"""
import sys, os, json, bisect, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify
from mips import decode, CODE0, CODE1

def build(buf):
    # 1) tous les aiguillages : on traduit toute la zone (remplit T.TABLES) en notant
    #    ou se trouve chaque aiguillage
    sites=collections.defaultdict(list)          # table -> [adresses MIPS des sauts]
    x=CODE0
    while x<CODE1:
        out,_=T.translate(buf,x,min(x+0x8000,CODE1))
        for va,mn,ws in out:
            if 'T_' in mn and ws and ws[0] in (0x4efb,0x4ebb):
                sites[int(mn.split('T_')[1][:6],16)].append(va)
        x+=0x8000
    # 2) debuts de fonctions : cibles de jal + cibles de tables d'aiguillage
    starts={x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'}
    for t,ent in T.TABLES.items(): starts.update(e-T.RUNTIME_BASE for e in ent)
    starts=sorted(s for s in starts if CODE0<=s<CODE1)
    def func_of(va):
        k=bisect.bisect_right(starts,va)-1
        return starts[k] if k>=0 else None
    # 3) union-find
    parent={}
    def find(a):
        parent.setdefault(a,a)
        while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
        return a
    def union(a,b): parent[find(a)]=find(b)
    for t,ent in T.TABLES.items():
        members=[e-T.RUNTIME_BASE for e in ent]
        members+= [func_of(v) for v in sites.get(t,[]) if func_of(v) is not None]
        members=[m for m in members if m is not None]
        for m in members[1:]: union(members[0],m)
        if members: find(members[0])
    fam={}
    for a in list(parent): fam[a]=find(a)
    return fam, starts

if __name__=="__main__":
    buf=open(verify.RO3,"rb").read()
    fam,starts=build(buf)
    sizes=collections.Counter(fam.values())
    print("tables d'aiguillage : %d   fonctions rattachees a une famille : %d / %d"%(
        len(T.TABLES),len(fam),len(starts)))
    print("familles : %d   taille mediane %d   plus grandes : %s"%(len(sizes),
        sorted(sizes.values())[len(sizes)//2], ', '.join(str(v) for v in sorted(sizes.values())[-8:])))
    json.dump({"fam":{"%x"%k:"%x"%v for k,v in fam.items()},"starts":starts},
              open(os.path.join(D,"families.json"),"w"))
    print("-> families.json")
