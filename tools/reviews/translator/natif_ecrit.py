#!/usr/bin/env python3
"""natif_ecrit.py roN START... -- for a native function (up to the first 'jr ra'): memory writes classed by target
(absolute lui/addiu address, A5/A6... base re-read from a 0x7000xxxx slot, pointer loaded from a global of the port,
argument; stack excluded) and calls. Tells whether an RTS stub loses an effect on the game's RAM. Review E2.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins
mod=sys.argv[1]
buf=paths.module(mod)
RB=0x1f0000; DE=struct.unpack_from('<I',buf,24)[0]
def slot(o):
    o&=0xffff
    if 0x1100<=o<0x1120: return 'A%d'%((o-0x1100)//4)
    if 0x1124<=o<0x1144: return 'D%d'%((o-0x1124)//4)
    return 'case%x'%o
for s in sys.argv[2:]:
    t=int(s,16); a=t; L=[]
    while a<t+0x4000:
        x=Ins(a,struct.unpack_from('<I',buf,a)[0]); L.append(x); a+=4
        if x.m=='jr' and x.rs==31: break
    reg={}; W=collections.Counter(); J=collections.Counter(); R=collections.Counter()
    for x in L:
        m=x.m
        if m=='lui': reg[x.rt]=('abs',x.imm<<16); continue
        if m in ('addiu','ori') and x.rs in reg and reg[x.rs][0]=='abs': reg[x.rt]=('abs',(reg[x.rs][1]+(x.simm if m=='addiu' else x.imm))&0xffffffff); continue
        if m in ('lw','lb','lbu','lh','lhu'):
            b=reg.get(x.rs)
            if b and b[0]=='abs':
                ad=(b[1]+x.simm)&0xffffffff
                if 0x70001100<=ad<0x70001200: reg[x.rt]=('reg68k',slot(ad)); R[slot(ad)]+=1
                elif m=='lw': reg[x.rt]=('ptr@%x'%ad,0)
                else: reg.pop(x.rt,None)
            else: reg.pop(x.rt,None)
            continue
        if m in ('sb','sh','sw','sd'):
            if x.rs==29: continue
            b=reg.get(x.rs)
            if not b: W['? (registre calcule / argument)']+=1
            elif b[0]=='abs':
                ad=(b[1]+x.simm)&0xffffffff
                if 0x70001100<=ad<0x70001200: W['case de registre 68K %s'%slot(ad)]+=1
                else: W['absolu %s %x'%('MODULE' if RB<=ad<DE else ('RAM-PS2>=fin' if ad>=DE else 'moteur'),ad&~0xfff)]+=1
            elif b[0]=='reg68k': W['%s(%s) = RAM du jeu'%(m,b[1])]+=1
            else: W['via %s'%b[0]]+=1
            continue
        if m=='jal': J['%x'%(x.tgt-RB)]+=1
        if m=='jalr': J['jalr']+=1
        try:
            d=x.rd if m in ('addu','subu','and','or','xor','nor','slt','sltu','sll','srl','sra','dsll32','dsra32','dsrl32','sllv','srlv','srav') else (x.rt if m in ('andi','xori','slti','sltiu','addiu','ori') else None)
        except Exception: d=None
        if d is not None:
            # addu base,index : garde la base si l'un des deux est connu
            if m=='addu' and (reg.get(x.rs) or reg.get(x.rt)): reg[d]=reg.get(x.rs) or reg.get(x.rt)
            else: reg.pop(d,None)
    print("%s %x : %d instructions ; cases 68K lues %s"%(mod,t,len(L),dict(R)))
    for k,n in W.most_common(): print("     ecrit %3d  %s"%(n,k))
    print("     appels :",dict(J))
