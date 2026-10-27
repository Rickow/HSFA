#!/usr/bin/env python3
"""CARTE DES TYPES PAR CHAMP : pour une base 68K (A6 par defaut), compte les acces MIPS par
deplacement HOTE et par taille (B/W/L, lecture/ecriture). Le recompilateur type chaque champ
(cf. HANDOFF §44) : s32 dont on lit la partie entiere -> mots a d+2 ; tableau d'octets lu en
long -> octets + long au meme endroit ; etc.  Usage : fieldmap.py [An] [max_disp_hex]"""
import sys,os,struct,collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, CODE0
import census
AN=int(sys.argv[1]) if len(sys.argv)>1 else 6
MAXD=int(sys.argv[2],16) if len(sys.argv)>2 else 0x80
SLOT=0x1100+4*AN
def collect(buf, code0):
    end=struct.unpack_from('<I',buf,12)[0]
    acc=collections.defaultdict(collections.Counter)
    base=set(); l7=set()
    for x in decode(buf,code0,end):
        m=x.m
        if m=='lui':
            (l7.add if x.imm==0x7000 else l7.discard)(x.rt); base.discard(x.rt); continue
        if m=='lw' and x.rs in l7 and x.imm==SLOT:
            base.add(x.rt); l7.discard(x.rt); continue
        if m in ('lb','lbu','lh','lhu','lw','sb','sh','sw') and x.rs in base:
            sz={'b':'B','h':'W','w':'L'}[m[1]]; acc[x.simm][('r' if m[0]=='l' else 'w')+sz]+=1
        # toute autre ecriture de registre invalide
        for r in (x.rt if m in ('lb','lbu','lh','lhu','lw','addiu','andi','ori','lui','slti','sltiu') else None,
                  x.rd if m in ('addu','subu','and','or','xor','nor','sll','srl','sra','sllv','dsll32','dsra32','dsrl32','slt','sltu') else None):
            if r is not None and not (m=='lw' and x.rs in l7 and x.imm==SLOT):
                base.discard(r); l7.discard(r)
        if m in ('jal','jalr'): base.clear(); l7.clear()
    return acc
if __name__=="__main__":
    buf=open(census.RO3,'rb').read()
    acc=collect(buf, int(os.environ.get("CODE0","%x"%CODE0),16))
    print("A%d : deplacement hote -> acces (r/w + taille)"%AN)
    for d in range(0,MAXD):
        c=acc.get(d)
        if not c: continue
        print("  $%03x  %s"%(d,'  '.join("%s=%d"%(k,v) for k,v in sorted(c.items()))))
