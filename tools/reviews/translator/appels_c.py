#!/usr/bin/env python3
"""appels_c.py roN -- every 'jal' of the module to a target INSIDE the module: is the target a native C function
(native_at of mame_test)? is it in the list of replaced natives (src/hsfa/hooks_fork_roN.json, type "natif du module")?
Callers classed as recompiled (the caller reads 0x7000xxxx slots) or C.
  C-NON-LISTEE called by recompiled code: the translation of the target (fragments) is executed -> to look at.
Review E2 (C code of the port). Save the output to a file: fragments_c.py and fragments_atteints.py read it.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, json, collections, bisect
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins, CODE0
import carte
mod=sys.argv[1]
buf=paths.module(mod)
CODE1=struct.unpack_from('<I',buf,12)[0]; RB=0x1f0000; CE=RB+CODE1
H=json.load(open(os.path.join(paths.SRC,'hooks_fork_%s.json'%mod),encoding='utf-8'))
LISTE={int(k,16) for k,v in H.items() if v['type']=='natif du module'}
L=[Ins(a,struct.unpack_from('<I',buf,a)[0]) for a in range(CODE0,CODE1,4)]
def F(t):
    r=[]
    for x in L[(t-CODE0)//4:(t-CODE0)//4+0x1000]:
        r.append(x)
        if x.m=='jr' and x.rs==31: break
    return r
memo={}
def native_at(t):
    if t in memo: return memo[t]
    Lf=F(t); a=sum(1 for x in Lf if x.m=='lui' and x.imm==0x7000); n=len(Lf)
    s=sum(1 for x in Lf if x.m in ('sq','lq','mult','multu','div','divu','mfhi','mflo') or (x.m=='addiu' and x.rs==29 and x.rt==29 and -0x400<x.simm<-16 and x.simm%16==0))
    lu={}; relais=False
    for x in Lf:
        if x.m=='lui': lu[x.rt]=x.imm
        elif x.m=='addiu' and x.rs in lu: lu[x.rt]=(lu[x.rs]<<16)+x.simm
        elif (x.m=='jalr' and x.rs in lu and RB+CODE0<=lu[x.rs]<CE) or (x.m=='jal' and RB+CODE0<=x.tgt<CE): relais=True
    if a==0 and (n<=8 or (n<=24 and relais)): r=False
    else: r= a==0 or (s>0 and a*20<n)
    memo[t]=(r,n,a); return memo[t]
starts=sorted({x.tgt-RB for x in L if x.m=='jal' and CODE0<=x.tgt-RB<CODE1})
def appelant(va):
    k=bisect.bisect_right(starts,va)-1
    return starts[k] if k>=0 else CODE0
E=carte.lit(mod); CV=collections.defaultdict(list)
for a,v,t in E: CV[v].append(t)
C=collections.Counter(); det=collections.defaultdict(list)
for x in L:
    if x.m!='jal' or not (CODE0<=x.tgt-RB<CODE1): continue
    t=x.tgt-RB; nat,n,a=native_at(t)
    if not nat: continue
    f=appelant(x.va); fn=native_at(f)[0]
    # l'appelant immediat est-il du code recompile ? (case 0x7000 dans les 40 instructions autour)
    k=(x.va-CODE0)//4; rec=any(y.m=='lui' and y.imm==0x7000 for y in L[max(0,k-40):k+40])
    emis=any(('JSR' in s or 'JMP' in s or 'BSR' in s) for s in CV.get(x.va,[]))
    key=('LISTEE' if t in LISTE else 'C-NON-LISTEE', 'appelant recompile' if rec else 'appelant C', 'appel emis' if emis else 'appel non emis')
    C[key]+=1; det[key].append((x.va,t,n,a))
print("%s : appels jal vers une fonction C native du module"%mod)
for k,v in sorted(C.items()): print("  %4d  %s"%(v,' / '.join(k)))
for key in det:
    if key[0]=='C-NON-LISTEE' and key[1]=='appelant recompile':
        print('---',' / '.join(key))
        for va,t,n,a in det[key][:60]: print("    site %07x -> %06x (n=%d, lui7000=%d) | %s"%(va,t,n,a,' || '.join(s[:60] for s in CV.get(va,[]))))
