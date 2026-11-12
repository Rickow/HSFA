#!/usr/bin/env python3
"""parite.py roN -- BYTE accesses d16(An) emitted with the fixed XOR 1 (An assumed even) while the parity of An,
tracked statically in the map (LEA / ADDQ / SUBQ / byte (An)+), is ODD. Cautious analysis: parity forgotten at every
branch target, after JSR, after any unknown write of An. A5, A6, A7 assumed even. OPT=1: optimistic (no reset at
joins / JSR). Review A1 (byte parity); fixed by PARITE_FLOT / PARITE_SITES in v161.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
import os
OPT=os.environ.get('OPT')=='1'
mod=sys.argv[1]; E=carte.lit(mod); T=sorted(carte.cibles(E))
import bisect
def joint(v0,v1):
    k=bisect.bisect_right(T,v0); return k<len(T) and T[k]<=v1
par={}
def reset():
    par.clear(); par.update({5:0,6:0,7:0})
reset()
LEA_D=re.compile(r'^LEA \$([0-9a-f]{4})\(A(\d)\),A(\d)$')
LEA_0=re.compile(r'^LEA \(A(\d)\),A(\d)$')
LEA_ABS=re.compile(r'^LEA \$([0-9a-f]+)\.L,A(\d)$')
LEA_T=re.compile(r'^LEA T_([0-9a-f]+)\(PC\),A(\d)$')
ADDQ=re.compile(r'^(ADDQ|SUBQ)\.[WL] #(\d),A(\d)$')
MVA=re.compile(r'^MOVEA\.L A(\d),A(\d)$')
EA=re.compile(r'(?<![\w$])(?:\$([0-9a-f]{4}))?\(A([0-4])\)(?!\+)')
DSTA=re.compile(r',A(\d)$')
prev=None; n=0; stats={'octets':0,'connus':0}
out=[]
hist=[]
for k,(a,v,t) in enumerate(E):
    if prev is not None and joint(prev,v) and not OPT: reset(); hist=[]
    prev=v
    h=carte.tete(t); notes=t[len(h):]
    hist.append((a,v,t)); hist=hist[-12:]
    op=h.split(' ')[0]
    # acces octet
    if op.endswith('.B') and ' ; ' not in h and 'XOR 1 a l' not in notes and 'inverses' not in notes:
        for m in EA.finditer(h):
            r=int(m.group(2)); stats['octets']+=1
            # (An)+ / -(An) fusionnes : annotation
            if par.get(r) is not None: stats['connus']+=1
            if par.get(r)==1 and ('[(A%d)+]'%r) not in notes and ('[-(A%d)]'%r) not in notes:
                out.append((a,v,t,list(hist)))
    # effets sur la parite
    m=LEA_D.match(h)
    if m: d,s,dst=int(m.group(1),16),int(m.group(2)),int(m.group(3)); par[dst]=None if par.get(s) is None else par[s]^(d&1)
    elif LEA_0.match(h): m=LEA_0.match(h); par[int(m.group(2))]=par.get(int(m.group(1)))
    elif LEA_ABS.match(h): m=LEA_ABS.match(h); par[int(m.group(2))]=int(m.group(1),16)&1
    elif LEA_T.match(h): m=LEA_T.match(h); par[int(m.group(2))]=int(m.group(1),16)&1
    elif ADDQ.match(h):
        m=ADDQ.match(h); r=int(m.group(3))
        if par.get(r) is not None: par[r]^=int(m.group(2))&1
    elif MVA.match(h): m=MVA.match(h); par[int(m.group(2))]=par.get(int(m.group(1)))
    else:
        if op in ('JSR','JMP','RTS','BRA') or op.startswith('MOVEM') or op=='EXG' or ' ; ' in h or h.startswith('[') or h.startswith('('):
            if (op in ('JSR',) and not OPT) or ' ; ' in h or op.startswith('MOVEM') or op=='EXG' or h.startswith('[') or h.startswith('('):
                for r in range(5): par[r]=None
            if op in ('JMP','RTS','BRA'): reset(); hist=[]
        else:
            m=DSTA.search(h)
            if m and (op.startswith('MOVEA') or op.startswith('ADDA') or op.startswith('SUBA') or op.startswith('LEA')): par[int(m.group(1))]=None
            elif 'prete' in notes or '(SP)+,A' in h:
                for r in range(5): par[r]=None
    # octets par (An)+ / -(An) : la parite bascule
    for r in range(5):
        if op.endswith('.B') or 'flux d\'octets' in notes:
            c=notes.count('[(A%d)+]'%r)+notes.count('[-(A%d)]'%r)
            if "flux d'octets" in notes:
                mm=re.search(r"flux d'octets ([^:]*):",notes)
                if mm: c+=mm.group(1).count('(A%d)+'%r)+mm.group(1).count('-(A%d)'%r)
            if c%2 and par.get(r) is not None: par[r]^=1
        elif ('[(A%d)+]'%r) in notes or ('[-(A%d)]'%r) in notes: pass     # mot / long : parite gardee
print("%s : %d acces octet par A0-A4 sans adresse exacte, parite connue pour %d ; IMPAIRE : %d"%(mod,stats['octets'],stats['connus'],len(out)))
for a,v,t,h in out:
    print("--- image $%06x mips(fichier) 0x%x : %s"%(a,v,t))
    for x in h[:-1]: print("       %06x %07x %s"%x)
