#!/usr/bin/env python3
"""cibles_natives.py roN -- code pointers used by TRANSLATED code (jump tables T_, tables relocated by step B,
CODE_x constants) whose target is a NATIVE C function of the port in the sense of mame_test.native_at (no 0x7000xxxx
slot, or C markers). Such a target has no valid translation: the label falls on fragments (or on the next emitted
instruction). Also gives what the map emits at the target. Reads etapeB_reloge.txt of the build. Review E2.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, re, collections, bisect
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import Ins, CODE0
import carte
mod=sys.argv[1]; D=paths.construction(mod)
buf=paths.module(mod)
CODE1=struct.unpack_from('<I',buf,12)[0]; RB=0x1f0000; CE=RB+CODE1
def native_at(t):
    L=[]; a0=t
    while a0<min(t+0x4000,len(buf)-4):
        x=Ins(a0,struct.unpack_from('<I',buf,a0)[0]); L.append(x); a0+=4
        if x.m=='jr' and x.rs==31: break
    a=sum(1 for x in L if x.m=='lui' and x.imm==0x7000); n=len(L)
    s=sum(1 for x in L if x.m in ('sq','lq','mult','multu','div','divu','mfhi','mflo') or (x.m=='addiu' and x.rs==29 and x.rt==29 and -0x400<x.simm<-16 and x.simm%16==0))
    lu={}; relais=False
    for x in L:
        if x.m=='lui': lu[x.rt]=x.imm
        elif x.m=='addiu' and x.rs in lu: lu[x.rt]=(lu[x.rs]<<16)+x.simm
        elif (x.m=='jalr' and x.rs in lu and RB+CODE0<=lu[x.rs]<CE) or (x.m=='jal' and RB+CODE0<=x.tgt<CE): relais=True
    if a==0 and (n<=8 or (n<=24 and relais)): return False,n,a
    return (a==0 or (s>0 and a*20<n)),n,a
E=carte.lit(mod); V=[e[1] for e in E]
src=collections.defaultdict(list)
for a,v,t in E:
    m=re.search(r'(JMP|JSR) T_([0-9a-f]{6})\(PC,D\d\.W\)\s+\[table de (\d+) entrees\]',t)
    if m:
        tb=int(m.group(2),16)
        for i in range(int(m.group(3))):
            x=struct.unpack_from('<I',buf,tb-RB+4*i)[0]
            if x: src[x-RB].append('aiguillage T_%06x[%d] (image %06x)'%(tb,i,a))
    m=re.search(r'CODE_([0-9a-f]{6,7})',t)
    if m: src[int(m.group(1),16)-(RB if int(m.group(1),16)>=RB+CODE0 else 0)].append('constante (image %06x)'%a)
for l in open(os.path.join(D,'etapeB_reloge.txt'),encoding='utf-8'):
    m=re.match(r'table ([0-9a-f]+)-([0-9a-f]+)',l)
    if m:
        p,f=int(m.group(1),16),int(m.group(2),16)
        for o in range(p,f,4):
            x=struct.unpack_from('<I',buf,o-RB)[0]
            if x: src[x-RB].append('etape B %06x[%d]'%(p,(o-p)//4))
n=0
print("%s : %d cibles de pointeurs de code"%(mod,len(src)))
for t in sorted(src):
    if not (CODE0<=t<CODE1): print("  HORS CODE %x : %s"%(t,src[t][:2])); continue
    nat,nn,a=native_at(t)
    k=bisect.bisect_left(V,t); prem=E[k] if k<len(E) else None
    if nat:
        n+=1
        print("  NATIVE %06x (n=%d, lui7000=%d) <- %s%s ; 1re emission a mips %07x (+%d) : %s"%(t,nn,a,src[t][0],' (+%d autres)'%(len(src[t])-1) if len(src[t])>1 else '',prem[1],prem[1]-t,prem[2][:50]))
print("  natives : %d"%n)
