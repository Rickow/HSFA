#!/usr/bin/env python3
"""show.py VA [avant] [apres] : MIPS + traduction cote a cote (nop/lui 0x7000 masques)."""
import sys,os; D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode
import census, translate as T
buf=open(census.RO3,'rb').read()
va=int(sys.argv[1],16); bef=int(sys.argv[2],16) if len(sys.argv)>2 else 0x40; aft=int(sys.argv[3],16) if len(sys.argv)>3 else 0x30
out,_=T.translate(buf,va-bef-0x200,va+aft+0x100)
em={}
for a,t,ws in out: em.setdefault(a,[]).append(t+'  '+' '.join('%04x'%w for w in ws))
def nm(x):
    s=str(x)
    for off,n in ((0x1150,'RES'),(0x1158,'C')): s=s.replace('%d('%off,n+'(')
    for k in range(7): s=s.replace('%d('%(0x1100+4*k),'A%d('%k)
    for k in range(8): s=s.replace('%d('%(0x1124+4*k),'D%d('%k)
    return s
for x in decode(buf,va-bef,va+aft):
    if (x.m=='lui' and x.imm==0x7000) or (x.m=='sll' and x.w==0): continue
    print("%07x%s %-28s %s"%(x.va,'*' if x.va==va else ' ',nm(x),' | '.join(em.get(x.va,[]))))
