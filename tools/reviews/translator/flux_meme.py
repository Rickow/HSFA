#!/usr/bin/env python3
"""flux_meme.py roN -- byte STREAM pointers in the strict sense: "MOVEA.L ea,An ... byte (An)+ / odd ADDQ ...
MOVE.L An,ea" (same ea re-read then stored, linear scope without reassignment). For each: the byte accesses with a
FIXED XOR 1 made through An between the re-read and the store (wrong one time in two if the pointer advances by an
odd count). Review A1 / E1 (byte parity).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
E=carte.lit(sys.argv[1])
EA=re.compile(r'(?<![\w$])(?:\$([0-9a-f]{4}))?\(A([0-4])\)(?!\+)')
st={r:None for r in range(7)}   # [ea, k, avance, [acces fixes]]
tot=0
for k,(a,v,t) in enumerate(E):
    h=carte.tete(t); notes=t[len(h):]; parts=h.split(' ; '); op=parts[0].split(' ')[0]
    if op.endswith('.B') and len(parts)==1 and 'XOR 1 a l' not in notes and 'inverses' not in notes:
        for mm in EA.finditer(h):
            r=int(mm.group(2))
            if ('[(A%d)+]'%r) in notes or ('[-(A%d)]'%r) in notes: continue
            if st[r]: st[r][3].append(k)
    m=re.match(r'^MOVE\.L A([0-6]),(.+)$',parts[0])
    if m:
        r=int(m.group(1)); s=st[r]
        if s and s[0]==m.group(2) and s[2]:
            tot+=1
            print("flux %-12s A%d relu %06x (mips %07x) range %06x, avance d'octets %d fois ; acces fixes : %d"%(s[0],r,E[s[1]][0],E[s[1]][1],a,s[2],len(s[3])))
            for j in s[3]: print("      %06x %07x %s"%(E[j][0],E[j][1],carte.tete(E[j][2])[:60]))
    for r in range(7):
        if not st[r]: continue
        n=0
        if re.search(r"flux d'octets [^:]*\(A%d\)\+"%r,notes) or ('[(A%d)+]'%r) in notes or ('[-(A%d)]'%r) in notes: n=1 if op.endswith('.B') or 'flux d' in notes else 0
        elif op.endswith('.B'): n=len(re.findall(r'\(A%d\)\+'%r,h))+len(re.findall(r'-\(A%d\)'%r,h))
        mq=re.match(r'^(ADDQ|SUBQ)\.[WL] #(\d),A%d$'%r,h)
        if mq and int(mq.group(2))&1: n=1
        st[r][2]+=n
    for p in parts:
        o=p.split(' ')[0]
        m=re.search(r',A([0-6])$',p)
        if m and not o.endswith('.B') and o.split('.')[0] in ('LEA','MOVEA','MOVE','ADDA','SUBA'):
            r=int(m.group(1))
            if o=='MOVEA.L' and not re.match(r'^MOVEA\.L A\d,',p): st[r]=[p[8:p.rindex(',')],k,0,[]]
            elif o.split('.')[0] in ('ADDA','SUBA') or re.match(r'^LEA \$[0-9a-f]{4}\(A%d\),A%d$'%(r,r),p): pass
            else: st[r]=None
    if op in ('MOVEM.L','EXG') or 'prete' in notes:
        for r in range(7): st[r]=None
print("total %d flux"%tot)
