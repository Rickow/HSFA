#!/usr/bin/env python3
"""Compare, famille par famille, les instructions 68K de la ROM de SFA3 et celles que produit
le traducteur (toute la zone 68K du MIPS). Les familles tres en dessous = ce qui manque."""
import sys, os, struct, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import m68k, verify, translate as T
from mips import CODE0, CODE1

def klass(w):
    h=w>>12
    if h in (1,2,3):
        return 'MOVEA' if ((w>>6)&7)==1 else 'MOVE.'+{1:'B',3:'W',2:'L'}[h]
    if h==7: return 'MOVEQ'
    if h==6:
        c=(w>>8)&15
        return 'BRA' if c==0 else 'BSR' if c==1 else 'Bcc'
    if h==5:
        if (w&0xf8)==0xc8 and ((w>>6)&3)==3: return 'DBcc'
        if ((w>>6)&3)==3: return 'Scc'
        return 'ADDQ' if not w&0x100 else 'SUBQ'
    if h==0xe: return 'decalage/rotation'
    if h==0x4:
        if w==0x4e75: return 'RTS'
        if w==0x4e73: return 'RTE'
        if (w&0xffc0)==0x4e80: return 'JSR'
        if (w&0xffc0)==0x4ec0: return 'JMP'
        if (w&0xf1c0)==0x41c0: return 'LEA'
        if (w&0xffc0)==0x4840 and (w&0x38)==0: return 'SWAP'
        if (w&0xffc0)==0x4840: return 'PEA'
        if (w&0xfb80)==0x4880 and (w&0x38)==0: return 'EXT'
        if (w&0xfb80)==0x4880: return 'MOVEM'
        if (w&0xff00)==0x4200: return 'CLR'
        if (w&0xff00)==0x4a00: return 'TST'
        if (w&0xff00)==0x4400: return 'NEG'
        if (w&0xff00)==0x4600: return 'NOT'
        if (w&0xff00)==0x4000: return 'NEGX/MOVE SR'
        if (w&0xffc0)==0x4800: return 'NBCD'
        if (w&0xfff0)==0x4e40: return 'TRAP'
        if (w&0xfff8)==0x4e50: return 'LINK'
        if (w&0xfff8)==0x4e58: return 'UNLK'
        if (w&0xfff0)==0x4e60: return 'MOVE USP'
        if (w&0xffc0)==0x46c0: return 'MOVE >SR'
        if (w&0xffc0)==0x44c0: return 'MOVE >CCR'
        if (w&0xffc0)==0x4ac0: return 'TAS'
        return 'autre 4xxx'
    if h==0:
        if w&0x100 or (w&0xff00)==0x0800: return 'bit (BTST/BSET/BCLR/BCHG)'
        return {0:'ORI',2:'ANDI',4:'SUBI',6:'ADDI',0xa:'EORI',0xc:'CMPI'}.get((w>>8)&0xf,'imm?')
    if h==0x8:
        if (w&0x1c0)==0x0c0: return 'DIVU'
        if (w&0x1c0)==0x1c0: return 'DIVS'
        if (w&0x1f0)==0x100: return 'SBCD'
        return 'OR'
    if h==0xc:
        if (w&0x1c0)==0x0c0: return 'MULU'
        if (w&0x1c0)==0x1c0: return 'MULS'
        if (w&0x1f0)==0x100: return 'ABCD'
        if (w&0x130)==0x100: return 'EXG'
        return 'AND'
    if h==0x9 or h==0xd:
        nm='SUB' if h==9 else 'ADD'
        if (w&0xc0)==0xc0: return nm+'A'
        if (w&0x130)==0x100: return nm+'X'
        return nm
    if h==0xb:
        if (w&0xc0)==0xc0: return 'CMPA'
        if (w&0x100) and (w&0x38)==0x08: return 'CMPM'
        if w&0x100: return 'EOR'
        return 'CMP'
    return '?'

if __name__=="__main__":
    k68=open(verify.K68,"rb").read()[:0x100000]; n=len(k68)//2
    kw=struct.unpack('>%dH'%n,k68); rom=collections.Counter(); i=0
    while i<n:
        r=m68k.decode_one(kw,i,n)
        if r is None: i+=1; continue
        rom[klass(kw[i])]+=1; i+=r[0]
    buf=open(verify.RO3,"rb").read(); tr=collections.Counter(); x=CODE0
    while x<CODE1:
        out,_=T.translate(buf,x,min(x+0x8000,CODE1))
        for va,mn,ws in out:
            j=0
            while j<len(ws):
                r=m68k.decode_one(ws,j,len(ws))
                tr[klass(ws[j])]+=1; j+=r[0] if r else 1
        x+=0x8000
    rt=sum(rom.values()); tt=sum(tr.values())
    print("instructions : ROM %d | traduction %d   (rapport global %.2f)"%(rt,tt,tt/rt))
    print("\n%-26s %7s %7s %7s"%("famille","ROM","traduit","rapport"))
    rows=sorted(rom, key=lambda k:-rom[k])
    for k in rows[:45]:
        r=tr[k]/rom[k] if rom[k] else 0
        flag="  <== MANQUE" if rom[k]>=40 and r<0.35 else ""
        print("%-26s %7d %7d %7.2f%s"%(k,rom[k],tr[k],r,flag))
