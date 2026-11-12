#!/usr/bin/env python3
"""voir.py roN FILE_OFFSET [n_before] [n_after] -- MIPS (repository decoder, named slots) + lines of carte_image.txt
emitted at each address. The everyday tool of the review.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, struct, collections, os
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins
MOD=sys.argv[1]
CARTE=paths.chemin_carte(MOD)
SL={0x1150:'RES',0x1154:'X',0x1158:'C',0x114c:'PILE',0x1120:'A8',0x1144:'D8',0x1148:'?1148',0x115c:'?115c'}
def slot(o):
    o&=0xffff
    if 0x1100<=o<0x1120: return 'A%d%s'%((o-0x1100)//4, '' if o%4==0 else '+%d'%(o%4))
    if 0x1124<=o<0x1144: return 'D%d%s'%((o-0x1124)//4, '' if o%4==0 else '+%d'%(o%4))
    for b,n in SL.items():
        if b<=o<b+4: return n+('' if o==b else '+%d'%(o-b))
    return None
def carte(path=CARTE):
    d=collections.defaultdict(list)
    for l in open(path,encoding='utf-8',errors='replace'):
        p=l.rstrip('\n').split(' ',2)
        if len(p)<3: continue
        try: a=int(p[0],16); v=int(p[1],16)
        except ValueError: continue
        d[v].append((a,p[2]))
    return d
def lit(mod=MOD): return paths.module(mod)
def main():
    buf=lit(); C=carte()
    off=int(sys.argv[2],16); na=int(sys.argv[3]) if len(sys.argv)>3 else 8; nb=int(sys.argv[4]) if len(sys.argv)>4 else 24
    l7=set()
    for a in range(off-4*na, off+4*nb, 4):
        x=Ins(a, struct.unpack_from('<I',buf,a)[0])
        t=repr(x) if x.w else 'nop'
        if x.m in ('lb','lbu','lh','lhu','lw','sb','sh','sw','ld','sd') and slot(x.imm) and x.rs not in (29,):
            t+='   ; '+slot(x.imm)
        if x.m in ('beq','bne','blez','bgtz','bltz','bgez'): t+='   -> %x'%(a+4+x.simm*4)
        if x.m=='jal': t+='   (fichier %x)'%(x.tgt-0x1f0000)
        print("%s%07x  %-34s"%('>' if a==off else ' ',a,t), end='')
        e=C.get(a,[])
        print(('  | '+' || '.join('%06x %s'%(q,s) for q,s in e)) if e else '')
if __name__=='__main__': main()
