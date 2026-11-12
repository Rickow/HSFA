#!/usr/bin/env python3
"""flux_ptr.py roN -- pointers STORED in memory after a byte advance, and byte accesses with a fixed XOR 1 through a
pointer RE-READ from the same field.
 1) stores: MOVE.L An,ea while An advanced by a byte stream ((An)+ byte, odd ADDQ, LEA odd(An),An) since its last
    assignment -> the field ea may hold an ODD address;
 2) for each fixed byte access through An coming from "MOVEA.L ea,An": nearest store of the SAME ea (same text), in map
    lines. Near (< 400 lines) = same or neighbouring routine: serious candidate. Review E1.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re, collections, bisect
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
mod=sys.argv[1]; E=carte.lit(mod)
EA=re.compile(r'(?<![\w$])(?:\$([0-9a-f]{4}))?\(A([0-4])\)(?!\+)')
st={r:[None,0,0,-1] for r in range(7)}   # [ea d'origine, a avance (octet), parite nette, k origine]
W=collections.defaultdict(list)          # ea -> [(k, parite nette, comment)]
S=[]                                      # sites : (k, r, ea origine, k origine)
for k,(a,v,t) in enumerate(E):
    h=carte.tete(t); notes=t[len(h):]; parts=h.split(' ; '); op=parts[0].split(' ')[0]
    # acces octet fixe
    if op.endswith('.B') and len(parts)==1 and 'XOR 1 a l' not in notes and 'inverses' not in notes:
        for mm in EA.finditer(h):
            r=int(mm.group(2))
            if ('[(A%d)+]'%r) in notes or ('[-(A%d)]'%r) in notes: continue
            if st[r][0]: S.append((k,r,st[r][0],st[r][3],st[r][1]))
    # rangement
    m=re.match(r'^MOVE\.L A([0-6]),(.+)$',parts[0])
    if m:
        r=int(m.group(1))
        if st[r][1]: W[m.group(2)].append((k,st[r][2],st[r][1]))
    for r in range(7):
        n=0
        if re.search(r"flux d'octets [^:]*\(A%d\)\+"%r,notes) or (op.endswith('.B') and (('[(A%d)+]'%r) in notes or ('[-(A%d)]'%r) in notes)): n=1
        elif op.endswith('.B'): n=len(re.findall(r'\(A%d\)\+'%r,h))+len(re.findall(r'-\(A%d\)'%r,h))
        mq=re.match(r'^(ADDQ|SUBQ)\.[WL] #(\d),A%d$'%r,h)
        if mq and int(mq.group(2))&1: n=1
        ml=re.match(r'^LEA \$([0-9a-f]{4})\(A%d\),A%d$'%(r,r),h)
        if ml and int(ml.group(1),16)&1: n=1
        if n: st[r][1]+=n; st[r][2]^=n&1
    for p in parts:
        o=p.split(' ')[0]
        m=re.search(r',A([0-6])$',p)
        if m and not o.endswith('.B') and o.split('.')[0] in ('LEA','MOVEA','MOVE'):
            r=int(m.group(1))
            if re.match(r'^LEA \$[0-9a-f]{4}\(A%d\),A%d$'%(r,r),p): continue
            if o=='MOVEA.L' and not re.match(r'^MOVEA\.L A\d,',p): st[r]=[p[8:p.rindex(',')],0,0,k]
            elif o.startswith('LEA') and re.match(r'^LEA \$([0-9a-f]{4})\(A[0-6]\),',p) and int(p[5:9],16)&1: st[r]=[None,1,1,k]   # LEA impair(Ax),Ar : adresse impaire si Ax pair
            else: st[r]=[None,0,0,k]
    if op in ('MOVEM.L','EXG') or 'prete' in notes:
        for r in range(7): st[r]=[None,0,0,k]
print("%s : %d champs recoivent un pointeur avance par octets (%d rangements)"%(mod,len(W),sum(len(x) for x in W.values())))
for ea,l in sorted(W.items(), key=lambda x:-len(x[1])):
    print("  %-14s %3d rangements : %s"%(ea,len(l),' '.join('%06x%s'%(E[k][0],'!' if p else '') for k,p,n in l[:14])))
print("   ('!' = parite nette impaire depuis l'affectation, sur le chemin lineaire)")
print("--- acces octet fixe par un pointeur relu d'un champ qui recoit un pointeur avance (rangement a moins de 400 lignes)")
n=0
for k,r,ea,ko,av in S:
    l=W.get(ea)
    if not l: continue
    ks=[x[0] for x in l]; i=bisect.bisect_left(ks,k)
    d=min(abs(ks[j]-k) for j in (i-1,i) if 0<=j<len(ks))
    if d<400:
        n+=1; j=min((j for j in (i-1,i) if 0<=j<len(ks)), key=lambda j:abs(ks[j]-k))
        print("   %06x %07x A%d %-32s | relu %06x de %-12s | range %06x (%+d lignes)%s"%(E[k][0],E[k][1],r,carte.tete(E[k][2])[:32],E[ko][0],ea,E[ks[j]][0],ks[j]-k,' [avance entre-temps]' if av else ''))
print("   total %d"%n)
