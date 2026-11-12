#!/usr/bin/env python3
"""tailles.py roN [B>W ...] -- for each MIPS write of a Dn slot (sb/sh/sw), size of the 68K instruction emitted at
that address that writes Dn. Matrix (MIPS size, 68K size); the pairs given as arguments ("B>W", "L>RIEN"...) are
listed in detail.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections, re
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
from mips import decode
mod=sys.argv[1]
buf=paths.module(mod)
E=carte.lit(mod); V=collections.defaultdict(list)
for a,v,t in E: V[v].append((a,t))
last=max(V)
end=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if end==0x3bf140 else 0x22b00
l7=set(); M=collections.Counter(); ex=collections.defaultdict(list)
def t68(t,n):
    h=carte.tete(t); op=h.split(' ')[0]
    if ' ; ' in h or h.startswith('[') or h.startswith('('): return 'compose'
    if not re.search(r'D%d$'%n,h) and not (op in ('SWAP','EXT.W','EXT.L','NEG.B','NEG.W','NEG.L','NOT.B','NOT.W','NOT.L','CLR.B','CLR.W','CLR.L','TST.B','TST.W','TST.L') and h.endswith('D%d'%n)): 
        if op=='EXG' and 'D%d'%n in h: return 'L'
        return 'autre:'+op
    if op in ('MOVEQ','SWAP','EXT.L','EXG'): return 'L'
    if op=='EXT.W': return 'W'
    if op in ('MULS.W','MULU.W'): return 'L'
    m=re.search(r'\.([BWL])$',op)
    return m.group(1) if m else '?:'+op
for x in decode(buf,c0,min(end,last+4)):
    if x.m=='lui': (l7.add if x.imm==0x7000 else l7.discard)(x.rt); continue
    d=None
    if x.m in ('lw','lh','lhu','lb','lbu','addiu','andi','ori','xori','slti','sltiu'): d=x.rt
    elif x.op==0 and x.m not in ('jr','jalr','mult','multu','div','divu'): d=x.rd
    if x.m in ('sb','sh','sw') and x.rs in l7 and 0x1124<=x.imm<0x1144:
        n=(x.imm-0x1124)//4; off=(x.imm-0x1124)%4
        ms={'sb':'B','sh':'W','sw':'L'}[x.m]+('+%d'%off if off else '')
        es=V.get(x.va)
        if not es: k=(ms,'RIEN')
        else:
            ts=[t68(t,n) for a,t in es]
            good=[q for q in ts if q in ('B','W','L')]
            k=(ms, good[0] if good else ts[0])
        M[k]+=1
        if len(ex[k])<60: ex[k].append((x.va,[t for a,t in es] if es else None))
    if d is not None: l7.discard(d)
print(mod)
for k,nb in sorted(M.items(), key=lambda t:-t[1]): print("  %-6s -> %-22s %6d"%(k[0],k[1],nb))
if len(sys.argv)>2:
    for k in ex:
        if '%s>%s'%k in sys.argv[2:]:
            print('---',k)
            for va,ts in ex[k]: print("   0x%x %s"%(va,' || '.join(t[:90] for t in ts) if ts else None))
