#!/usr/bin/env python3
"""retenue.py roN [setter...] -- branch on C (BCS/BCC) or consumer of X (ADDX, ROXR, ABCD) whose last 68K setter is
suspect for the carry: ADDI/ADDQ with a negative immediate (the MIPS 'addiu -n' of a SUBI/SUBQ: inverted carry),
MOVE/TST/CLR/AND/OR/EOR (C = 0), NEG, shifts... Classed by setter; the setters given as arguments are listed in detail.
Review B2.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re, collections, struct
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
mod=sys.argv[1]; E=carte.lit(mod)
NEUTRE=('MOVEA','LEA','ADDA','SUBA','EXG','MOVEM','PEA','NOP')
BCCS={'BEQ','BNE','BPL','BMI','BCS','BCC','BGT','BLE','BLT','BGE'}
C=collections.Counter(); ex=collections.defaultdict(list)
for k,(a,v,t) in enumerate(E):
    h=carte.tete(t); op=h.split(' ')[0]
    if op not in ('BCS','BCC','ADDX.L','ROXR.B','ABCD'): continue
    j=k-1; q=None
    while j>=0 and k-j<30:
        hj=carte.tete(E[j][2]); oj=hj.split(' ')[0]; b=oj.split('.')[0]
        if oj in BCCS or b in NEUTRE or hj.startswith('(') or (b in ('ADDQ','SUBQ','MOVE') and re.search(r',A\d$',hj)) or 'prete' in E[j][2]: j-=1; continue
        q=j; break
    if q is None: continue
    hq=carte.tete(E[q][2]); oq=hq.split(' ')[0]; b=oq.split('.')[0]
    key=b
    if b in ('ADDI','ADDQ') and re.search(r'#\$(ff|[89a-f][0-9a-f]{3}$|ffff)',hq.split(',')[0]): key=b+' negatif'
    if b=='ADDI' and '#$ffff' in hq: key='ADDI negatif'
    C[(op,key)]+=1
    if len(ex[(op,key)])<40: ex[(op,key)].append((k,q))
print(mod)
for (op,key),n in sorted(C.items(), key=lambda t:-t[1]): print("  %-7s apres %-14s %5d"%(op,key,n))
for sel in sys.argv[2:]:
    for (op,key) in ex:
        if key==sel:
            print('---',op,key)
            for k,q in ex[(op,key)]:
                for x in range(q,k+1): print("     %06x %07x %s"%(E[x][0],E[x][1],E[x][2][:120]))
                print()
