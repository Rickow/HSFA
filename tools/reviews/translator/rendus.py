#!/usr/bin/env python3
"""rendus.py roN -- FLAGS RETURNED TO THE CALLER. For each function where at least one caller (jal) re-reads RES or C
after the return before rewriting them: at each 'jr ra' of the function, does the last 68K setter emitted before the
RTS match the last MIPS write of RES (position, operand)? Suspect classes listed. Reuses the code of drapeaux.py
(executed up to its main loop). Review angle 3.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections, bisect
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
sys.dont_write_bytecode=True
with open(os.path.join(ICI,'drapeaux.py'),encoding='utf-8') as _f: src=_f.read().split("C=collections.Counter(); S=")[0]
exec(src)                      # carte, I, pose, source_ecrite, derniere_ecriture, E, mod, buf...
e=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if e==0x3bf140 else 0x22b00
JAL=collections.defaultdict(list)
for a in range(c0,e,4):
    x=I(a)
    if x.m=='jal': JAL[x.tgt-0x1f0000].append(a)
starts=sorted(JAL)
def lit_apres(a):
    r=set(); seen=set()
    for k in range(2,40):
        y=I(a+4*k)
        if y.m in ('lw','lh','lb') and y.rs!=29 and y.imm in (RES,CS) and y.imm not in seen: r.add(y.imm)
        if y.m=='sw' and y.rs!=29 and y.imm in (RES,CS): seen.add(y.imm)
        if y.m in ('jal','jalr','jr'): break
    return r
idx=collections.defaultdict(list)
for k,(a,v,t) in enumerate(E): idx[v].append(k)
C=collections.Counter(); out=[]
for f in starts:
    if not (c0<=f<e): continue
    lus=[c for c in JAL[f] if RES in lit_apres(c)]
    if not lus: continue
    C['fonctions dont un appelant relit RES']+=1
    fin=starts[bisect.bisect_right(starts,f)] if bisect.bisect_right(starts,f)<len(starts) else e
    for a in range(f,min(fin,f+0x4000),4):
        x=I(a)
        if not (x.m=='jr' and x.rs==31): continue
        ks=[k for k in idx.get(a,[]) if carte.tete(E[k][2]).split(' ')[0] in ('RTS','JMP')]
        if not ks: C['jr ra sans RTS dans la carte']+=1; continue
        k=ks[-1]; P,appel=derniere_ecriture(a,RES)
        j=k-1; Q=None; neutres=[]
        while j>=0 and k-j<40:
            p=pose(E[j][2])
            if p=='fin': Q=('fin',j); break
            if p in ('oui','oui?','appel','bit','ccr'): Q=(p,j); break
            neutres.append(j); j-=1
        C['retours']+=1
        if Q is None or Q[0]=='fin': C['(chemin non lineaire)']+=1; continue
        qk,qj=Q; qa,qv,qt=E[qj]; cl=None
        if qk=='appel': 
            if not appel and P and P>qv: cl='RES ecrit apres le dernier JSR, rien emis'
        elif P is None: C['(P introuvable)']+=1
        elif appel and qv!=a and P<qv: pass
        elif qv==a: pass
        elif qv>P and I(qv).m not in ('beq','bne','bltz','bgez','bgtz','blez'): cl='poseur emis apres la derniere ecriture de RES'
        else:
            if [x_ for x_ in neutres if qv<E[x_][1]<=P]: cl='RES ecrit apres une instruction neutre'
            else:
                so=source_ecrite(P); qh=carte.tete(qt)
                if so and so[0]=='D' and ('D%d'%so[1]) not in qh: cl='operande D different'
                elif so and so[0]=='mem':
                    off=so[1]&0xffff; cands={'$%04x(A%d)'%(off,so[2]),'$%04x(A%d)'%(off^1,so[2])}
                    if off in (0,1): cands|={'(A%d)'%so[2]}
                    if not any(c in qh for c in cands) and 'XOR' not in qt and 'flux' not in qt and '(A%d)+'%so[2] not in qt: cl='operande memoire different'
        if cl: C[cl]+=1; out.append((cl,f,a,P,k,qj,len(lus),lus[0]))
print(mod,dict(C))
for cl,f,a,P,k,qj,n,c in sorted(out):
    print("--- %s : fonction 0x%x, jr ra 0x%x, P=%s ; %d appelant(s) relisent RES (ex. 0x%x)"%(cl,f,a,'%x'%P if P else None,n,c))
    for x in range(max(qj-1,k-7),k+1): print("     %06x %07x %s"%(E[x][0],E[x][1],E[x][2][:130]))
