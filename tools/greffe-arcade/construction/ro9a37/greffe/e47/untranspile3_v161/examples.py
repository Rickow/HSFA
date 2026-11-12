#!/usr/bin/env python3
"""Affiche des EXEMPLES d'effets manques d'une categorie, avec leur contexte MIPS,
pour identifier l'idiome a ajouter au traducteur."""
import sys,os,collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, REG
import translate, census
buf=open(census.RO3,"rb").read()
kind=sys.argv[1]; det=sys.argv[2]; a=int(sys.argv[3],16); b=int(sys.argv[4],16); N=int(sys.argv[5]) if len(sys.argv)>5 else 4
out,_=translate.translate(buf,a,b); em={va for va,_,ws in out if ws}
L=list(decode(buf,a,b)); prov={}; shown=0
for i,ins in enumerate(L):
    m=ins.m
    if m=='lui': prov[ins.rt]=('lui',ins.imm)
    key=None
    if m in ('sb','sh','sw','sd') and prov.get(ins.rs)==('lui',0x7000):
        s=census.slot(ins.imm)
        if s not in ('RES','NFLG'): key=('ecrit-registre',s[0])
    elif m in census.BR: key=('branchement',m)
    elif m=='jalr': key=('appel','jalr (indirect)')
    if key!=(kind,det): continue
    if any(v in em for v in (ins.va-8,ins.va-4,ins.va,ins.va+4)): continue
    print("---- manque @%07x"%ins.va)
    for j in range(max(0,i-9),min(len(L),i+2)):
        x=L[j]; print("   %s %07x  %s"%(">>" if j==i else "  ",x.va,x))
    shown+=1
    if shown>=N: break
