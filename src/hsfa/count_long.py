#!/usr/bin/env python3
"""Compte les formes d'acces LONG a la memoire dans la traduction (cout de la recette
'long = SWAP')."""
import sys,collections,re,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import translate as T
from mips import CODE0, CODE1
buf=open('<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin','rb').read()
c=collections.Counter(); ex={}
x=CODE0
while x<CODE1:
    out,_=T.translate(buf,x,min(x+0x4000,CODE1))
    for va,mn,ws in out:
        if not ws or ' ' not in mn or '.L' not in mn.split()[0]: continue
        ops=mn.split(None,1)[1]
        if not re.search(r'\(A\d\)',ops): continue
        op=mn.split()[0]; parts=ops.split(','); src=parts[0]; dst=parts[-1]
        if op.startswith('MOVE.L') and '(A' in src and '(A' in dst: k='copie memoire->memoire (gratuit)'
        elif op.startswith('MOVE.L') and src.startswith('#'): k='MOVE.L #imm,memoire (gratuit)'
        elif op.startswith('MOVE.L') and '(A' in src: k='MOVE.L memoire,Dn (+1 SWAP)'
        elif op.startswith('MOVE.L') and '(A' in dst: k='MOVE.L Dn,memoire (+2 SWAP)'
        elif op.startswith('MOVEA.L'): k='MOVEA.L memoire,An (pointeur)'
        else: k='%s (operation sur long en memoire)'%op
        c[k]+=1; ex.setdefault(k,mn)
    x+=0x4000
tot=sum(c.values())
print("acces LONG a la memoire dans la traduction de SFA3 : %d"%tot)
for k,v in c.most_common(): print("   %-44s %5d (%4.1f%%)   ex. %s"%(k,v,100*v/max(1,tot),ex[k][:44]))
