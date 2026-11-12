#!/usr/bin/env python3
"""drapeaux.py roN -- for each emitted 68K conditional branch, compares
  - MIPS side: the slot read by the branch (RES 0x1150 = Z/N, C 0x1158), the size of the sign extension on reading,
    and P = last linear write of that slot before the branch;
  - 68K side: Q = last emitted instruction before the Bcc that sets the flags, and its size.
Suspect classes:
  ECRASE   Q emitted AFTER P and before the branch (flags of the test overwritten by an intermediate emission)
  PERDU    a neutral instruction emitted between Q and P (RES written after it: the flag setter is missing)
  TAILLE   size of the 68K setter != size re-read by the MIPS
  APPEL    flags of a call (jal between P and the branch) but Q is not the JSR, or the reverse
  OPERANDE, DOUBLE-RES, C-apres-bit: see the code (ADD gives false positives).
Linear analysis (straight-line path): false positives at joins. MAXS = max sites listed per class (default 400).
Review A3 / E7 (lost compares); after v161 no PERDU / TAILLE / APPEL-sans-jal site of the review remains.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, re, struct, collections, os
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
from mips import Ins
mod=sys.argv[1]; E=carte.lit(mod)
buf=paths.module(mod)
def I(a): return Ins(a, struct.unpack_from('<I',buf,a)[0])
RES,CS,XS=0x1150,0x1158,0x1154
BCC={'BEQ','BNE','BPL','BMI','BCS','BCC','BGT','BLE','BLT','BGE','BHI','BLS','BVS','BVC'}
NEUTRE=('MOVEA','LEA','ADDA','SUBA','EXG','MOVEM','PEA','NOP','BRA','JMP','RTS','JSR')
def lit_case(v):
    """branchement MIPS en v : (case, taille relue, registre) en remontant le registre teste"""
    x=I(v)
    if x.m not in ('beq','bne','bltz','bgez','bgtz','blez'): return None
    r=x.rs if x.rs else x.rt
    if x.m in ('beq','bne') and x.rs and x.rt: return ('2reg',None)
    sz='L'; a=v-4; n=0
    while n<14:
        y=I(a); n+=1; a-=4
        if y.m=='lui' or (y.m=='sll' and y.w==0): continue
        d=None
        if y.m in ('lw','lh','lhu','lb','lbu','addiu','andi','ori','xori','slti','sltiu'): d=y.rt
        elif y.op==0 and y.m not in ('jr','jalr','mult','multu','div','divu'): d=y.rd
        if y.m in ('sw','sh','sb','sd'): continue
        if y.m in ('beq','bne','bltz','bgez','bgtz','blez','jal','jalr','jr'): return ('rupture',None)
        if d!=r: continue
        if y.m in ('dsll32','dsra32','sll','sra'):
            if y.m in ('dsra32','sra') and y.sa in (16,24): sz={16:'W',24:'B'}[y.sa]
            r=y.rt; continue
        if y.m=='andi':
            if y.imm==0xff: sz='B' if sz=='L' else sz
            elif y.imm==0xffff: sz='W' if sz=='L' else sz
            else: return ('andi',y.imm)
            r=y.rs; continue
        if y.m in ('lw','lh','lb','lhu','lbu'):
            if I(a+4-4).m=='lui' or True:
                o=y.imm
                if y.rs!=29 and o in (RES,CS,XS): return ({RES:'RES',CS:'C',XS:'X'}[o], sz if y.m=='lw' else {'lh':'W','lhu':'W','lb':'B','lbu':'B'}[y.m])
                return ('mem',y.m)
        return ('autre',y.m)
    return ('loin',None)
def derniere_ecriture(v,slot,lim=400):
    """(P, appel entre P et v ?) ; P = dernier 'sw x,slot(base)' avant v (fichier)"""
    a=v-4; n=0; appel=False
    while n<lim:
        y=I(a)
        if y.m in ('jal','jalr'): appel=True
        if y.m=='sw' and y.imm==slot and y.rs!=29: return a,appel
        if y.m=='jr' and y.rs==31: return None,appel
        a-=4; n+=1
    return None,appel
def taille_ecrite(P):
    x=I(P); r=x.rt; a=P-4; n=0
    if r==0: return 'Z'
    while n<10:
        y=I(a); n+=1; a-=4
        if y.m=='lui' or (y.m=='sll' and y.w==0) or y.m in ('sw','sh','sb','sd'): continue
        d=None
        if y.m in ('lw','lh','lhu','lb','lbu','addiu','andi','ori','xori','slti','sltiu'): d=y.rt
        elif y.op==0 and y.m not in ('jr','jalr','mult','multu','div','divu'): d=y.rd
        if y.m in ('beq','bne','bltz','bgez','bgtz','blez','jal','jalr','jr'): return '?'
        if d!=r: continue
        if y.m in ('dsra32','sra') and y.sa in (16,24): return {16:'W',24:'B'}[y.sa]
        if y.m=='andi' and y.imm in (0xff,0xffff): return 'B' if y.imm==0xff else 'W'
        if y.m in ('lb','lbu'): return 'B'
        if y.m in ('lh','lhu'): return 'W'
        if y.m=='lw': return 'L'
        return '?'
    return '?'
def source_ecrite(P):
    """origine de la valeur rangee dans RES en P : ('D',n) | ('A',n) | ('mem',off,base 'An' ou None) | ('calc',m) | None"""
    x=I(P); r=x.rt; a=P-4; n=0
    if r==0: return ('zero',)
    while n<16:
        y=I(a); n+=1; a-=4
        if y.m=='lui' or (y.m=='sll' and y.w==0) or y.m in ('sw','sh','sb','sd'): continue
        d=None
        if y.m in ('lw','lh','lhu','lb','lbu','addiu','andi','ori','xori','slti','sltiu'): d=y.rt
        elif y.op==0 and y.m not in ('jr','jalr','mult','multu','div','divu'): d=y.rd
        if y.m in ('beq','bne','bltz','bgez','bgtz','blez','jal','jalr','jr'): return None
        if d!=r: continue
        if y.m in ('dsll32','dsra32','sll','sra') and y.sa in (16,24): r=y.rt; continue
        if y.m=='andi' and y.imm in (0xff,0xffff): r=y.rs; continue
        if y.m in ('lb','lbu','lh','lhu','lw'):
            # base : banc de registres ?
            b=y.rs; a2=a; k=0; base=None
            while k<6:
                z=I(a2); k+=1; a2-=4
                if z.m=='lui' and z.rt==b: base=('lui',z.imm); break
                if z.m=='lw' and z.rt==b: base=('slot',z.imm); break
                if z.m in ('addu','addiu') and (z.rd==b if z.m=='addu' else z.rt==b): base=('calc',); break
            if base and base[0]=='lui' and base[1]==0x7000:
                o=y.imm
                if 0x1100<=o<0x1120: return ('A',(o-0x1100)//4)
                if 0x1124<=o<0x1144: return ('D',(o-0x1124)//4)
                return ('case',o)
            if base and base[0]=='slot' and 0x1100<=base[1]<0x1120: return ('mem',y.simm,(base[1]-0x1100)//4,y.m)
            return ('mem?',)
        return ('calc',y.m)
    return None
def taille(h):
    op=h.split(' ')[0]
    m=re.search(r'\.([BWL])$',op)
    if m: return m.group(1)
    if op=='MOVEQ' or op=='SWAP' or op=='EXT': return 'L'
    m=re.search(r'\b[A-Z]+\.([BWL]) ',h)
    return m.group(1) if m else '?'
def pose(t):
    """l'entree pose-t-elle N/Z ? 'oui' | 'non' | 'appel' | 'bit' (Z seul) | 'ccr' (restaure) | 'fin'"""
    h=carte.tete(t); op=h.split(' ')[0]
    if h.startswith('(restauration'): return 'non'
    if op in BCC: return 'non'
    if op in ('RTS','JMP','BRA'): return 'fin'
    if op=='JSR': return 'appel'
    if h.startswith('MOVE (SP)+,CCR') or h.startswith('ANDI #'): return 'ccr'
    if 'prete' in t and ('(SP)' in h): return 'non'
    if 'pile privee' in t: return 'oui' if op.startswith('MOVE.') and not ',A' in h[-3:] else 'non'
    if op in ('BTST','BSET','BCLR','BCHG'): return 'bit'
    b=op.split('.')[0]
    if b in NEUTRE: 
        if ' ; ' in h and 'JSR CONV' not in h: return 'oui?'
        return 'non'
    if b in ('ADDQ','SUBQ') and re.search(r',A\d$',h): return 'non'
    if b=='MOVE' and re.search(r',A\d$',h): return 'non'
    if h.startswith('[realignement'): return 'oui?'
    return 'oui'
C=collections.Counter(); S=collections.defaultdict(list)
for k,(a,v,t) in enumerate(E):
    h=carte.tete(t); op=h.split(' ')[0]
    if op not in BCC: continue
    lc=lit_case(v)
    if lc is None: C['(pas un branchement MIPS en v)']+=1; continue
    case,sz=lc
    if case not in ('RES','C'): C['(case %s)'%case]+=1; continue
    P,appel=derniere_ecriture(v,RES if case=='RES' else CS)
    # cote 68K
    j=k-1; Q=None; neutres=[]
    while j>=0 and k-j<60:
        p=pose(E[j][2])
        if p=='fin': Q=('fin',j); break
        if p in ('oui','oui?','appel','bit','ccr'): Q=(p,j); break
        neutres.append(j); j-=1
    if Q is None: C['(Q introuvable)']+=1; continue
    qk,qj=Q; qa,qv,qt=E[qj]
    if qk=='fin': C['(etiquette : chemin non lineaire)']+=1; continue
    C['total']+=1
    cl=None
    if qk=='appel':
        if not appel: cl='APPEL-sans-jal'
    elif qk=='ccr': pass
    else:
        if P is None: cl=None; C['(P introuvable)']+=1
        elif appel and qv!=v: cl='APPEL-jal-mais-Q=%s'%carte.tete(qt).split(' ')[0].split('.')[0]
        elif qv==v: 
            # test differe emis au branchement : taille
            pass
        elif qv>P and I(qv).m in ('beq','bne','bltz','bgez','bgtz','blez'): pass
        elif qv>P: cl='ECRASE'
        else:
            nn=[x for x in neutres if qv<E[x][1]<=P]
            if nn: cl='PERDU'
            elif case=='RES':
                W=[]; a_=qv+4
                while a_<v:
                    y=I(a_)
                    if y.m=='sw' and y.imm==RES and y.rs!=29:
                        neg=any(I(a_-4*q).m=='subu' and I(a_-4*q).rs==0 for q in range(1,4))
                        if not neg: W.append(a_)
                    if y.m in ('jal','jalr'): W=[]; break
                    a_+=4
                if len(W)>=2: cl='DOUBLE-RES'
        if cl is None and case=='RES' and sz=='L' and P: sz=taille_ecrite(P)
        if cl is None and case=='RES' and qk!='bit' and sz in ('B','W','L') and taille(carte.tete(qt)) not in (sz,'?') and op in ('BEQ','BNE','BPL','BMI','BGT','BLE','BLT','BGE'):
            cl='TAILLE %s lu %s'%(taille(carte.tete(qt)),sz)
        if cl is None and case=='C' and qk=='bit': cl='C-apres-bit'
        if cl is None and case=='RES' and P and qk in ('oui','bit'):
            so=source_ecrite(P); qh=carte.tete(qt); C['src:'+str(so[0] if so else None)+('/differe' if qv==v else '/naturel')]+=1
            if so and so[0]=='D' and ('D%d'%so[1]) not in qh and 'prete' not in qt: cl='OPERANDE-D'
            elif so and so[0]=='mem':
                off=so[1]&0xffff; cands={'$%04x(A%d)'%(off,so[2]),'$%04x(A%d)'%(off^1,so[2])}
                if off in (0,1): cands|={'(A%d)'%so[2]}
                if not any(c in qh for c in cands) and ('(A%d)'%so[2]) not in qt and 'A%d'%so[2] not in qh: cl='OPERANDE-mem'
                elif not any(c in qh for c in cands) and '(A%d)+'%so[2] not in qt and '-(A%d)'%so[2] not in qt and 'flux' not in qt and 'XOR' not in qt: cl='OPERANDE-mem?'
    if cl:
        C[cl]+=1; S[cl].append((k,qj,P,case,sz))
print(mod, dict(C))
for cl in sorted(S):
    print("\n######## %s : %d"%(cl,len(S[cl])))
    for k,qj,P,case,sz in S[cl][:int(os.environ.get('MAXS','400'))]:
        print("--- Bcc image $%06x mips 0x%x lit %s/%s ; P=%s"%(E[k][0],E[k][1],case,sz,'%x'%P if P else None))
        for x in range(max(qj-1,k-9),k+1): print("     %06x %07x %s"%(E[x][0],E[x][1],E[x][2][:140]))
