#!/usr/bin/env python3
"""parite_tri.py roN [class] -- SORTING of the byte accesses with a fixed XOR 1 through A0-A4 (review E1).
For each access: linear origin of An, then PROOF of parity by a WORD or LONG access through the same An in the same
scope (an aligned MIPS lh/lw, like a 68000 .W/.L, requires an even address):
  PAIR-fort    proof with no break (RTS/JMP/BRA/table label) between the proof and the access
  PAIR-faible  proof in the linear scope but across a break
  IMPAIR       the proof gives An odd at the access (odd ADDQ / stream in between) -> access proven WRONG
  INCONNU      no proof; to read by hand (detailed list if [class] is given: adda | moveal | lea | inconnue | tout)
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re, collections
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
mod=sys.argv[1]; quoi=sys.argv[2] if len(sys.argv)>2 else None
E=carte.lit(mod)
EA=re.compile(r'(?<![\w$])(?:\$([0-9a-f]{4}))?\(A([0-4])\)(?!\+)')
def defn(h,op):
    """(registre, classe) si la ligne redefinit An"""
    m=re.search(r',A([0-4])(?: ;.*)?$',h)
    if m and not op.endswith('.B') and op.split('.')[0] in ('LEA','MOVEA','ADDA','SUBA','MOVE'):
        r=int(m.group(1))
        if op.startswith('LEA'):
            if re.match(r'^LEA \$[0-9a-f]{4}\(A[567]\),',h): return r,'lea A5/A6 '+('IMPAIR' if int(h[5:9],16)&1 else 'pair')
            if re.match(r'^LEA \$[0-9a-f]{4}\(A[0-4]\),',h): return r,'lea d(An)'
            if '.L,' in h or 'T_' in h: return r,'lea table/absolu'
            return r,'lea indexe'
        if op=='MOVEA.W': return r,'movea.w'
        if op=='MOVEA.L': return r,('moveal' if not re.match(r'^MOVEA\.L A\d,',h) else 'moveal An,Am')
        return r,'adda'
    return None
def delta(h,op,notes,r):
    """changement de parite de An par cette ligne"""
    d=0
    if re.search(r"flux d'octets [^:]*\(A%d\)\+"%r,notes) or (op.endswith('.B') and (('[(A%d)+]'%r) in notes or ('[-(A%d)]'%r) in notes)): d^=1
    if op.endswith('.B'):
        d^=(len(re.findall(r'\(A%d\)\+'%r,h))+len(re.findall(r'-\(A%d\)'%r,h)))&1
    m=re.match(r'^(ADDQ|SUBQ)\.[WL] #(\d),A%d$'%r,h)
    if m and int(m.group(2))&1: d^=1
    m=re.match(r'^LEA \$([0-9a-f]{4})\(A%d\),A%d$'%(r,r),h)
    if m and int(m.group(1),16)&1: d^=1
    return d
def preuve(h,op,r):
    """True si la ligne fait un acces mot/long ALIGNE par An (deplacement pair)"""
    if not (op.endswith('.W') or op.endswith('.L')) or op.startswith('LEA') or op.startswith('PEA'): return False
    if 'non aligne' in h: return False
    for m in re.finditer(r'(?<![\w$])(?:\$([0-9a-f]{4}))?(-?)\(A%d\)(\+?)'%r,h):
        d=int(m.group(1),16) if m.group(1) else 0
        # la destination « ,An » d'un MOVEA n'est pas un acces
        return d&1==0
    return False
RUPT=('RTS','JMP','BRA','RTE')
H=[]; 
for a,v,t in E:
    h=carte.tete(t); H.append((h,h.split(' ')[0],t[len(h):]))
def cherche(k,r,sens):
    """parcourt depuis k dans le sens donne jusqu'a la redefinition de An ; rend (parite relative de la preuve, rupture, k preuve)"""
    par=0; rup=False; j=k
    while True:
        j+=sens
        if j<0 or j>=len(E) or abs(j-k)>400: return None
        h,op,notes=H[j]
        if op.split('.')[0] in RUPT or op.startswith('JMP'): rup=True
        if op in ('MOVEM.L','EXG') or 'prete' in notes: return None
        dd=defn(h,op)
        if sens>0:
            if dd and dd[0]==r:
                # LEA d(An),An garde le lien de parite ; toute autre redefinition ferme la portee
                if not re.match(r'^LEA \$[0-9a-f]{4}\(A%d\),A%d$'%(r,r),h): return None
            if preuve(h,op,r): return par,rup,j
            par^=delta(h,op,notes,r)
        else:
            par^=delta(h,op,notes,r)
            if preuve(h,op,r) and not (dd and dd[0]==r and not op.startswith('LEA')): return par,rup,j
            if dd and dd[0]==r:
                if not re.match(r'^LEA \$[0-9a-f]{4}\(A%d\),A%d$'%(r,r),h): return None
org={r:('inconnue',-1) for r in range(5)}
C=collections.Counter(); L=collections.defaultdict(list)
for k,(a,v,t) in enumerate(E):
    h,op,notes=H[k]
    if op.endswith('.B') and ' ; ' not in h and 'XOR 1 a l' not in notes and 'inverses' not in notes:
        for mm in EA.finditer(h):
            r=int(mm.group(2))
            if ('[(A%d)+]'%r) in notes or ('[-(A%d)]'%r) in notes: continue
            cl,ko=org[r]
            res='INCONNU'; kp=-1
            for sens in (-1,1):
                p=cherche(k,r,sens)
                if p:
                    par,rup,kp=p
                    res='IMPAIR' if par else ('PAIR-faible' if rup else 'PAIR-fort')
                    if par or not rup: break
            C[(cl,res)]+=1; L[(cl,res)].append((k,r,ko,kp))
    dd=defn(h,op)
    if dd: org[dd[0]]=(dd[1],k)
    if op in ('MOVEM.L','EXG') or 'prete' in notes:
        for r in range(5): org[r]=('inconnue',k)
cls=sorted({c for c,_ in C})
print("%s : tri de parite par origine (acces octet a XOR 1 fixe, A0-A4)"%mod)
print("  %-22s %9s %11s %7s %8s"%('origine','PAIR-fort','PAIR-faible','IMPAIR','INCONNU'))
for c in cls: print("  %-22s %9d %11d %7d %8d"%(c,C[(c,'PAIR-fort')],C[(c,'PAIR-faible')],C[(c,'IMPAIR')],C[(c,'INCONNU')]))
def montre(key):
    for k,r,ko,kp in L[key]:
        a,v,t=E[k]
        o=("%06x %s"%(E[ko][0],H[ko][0][:44])) if ko>=0 else '?'
        p=("%06x %s"%(E[kp][0],H[kp][0][:40])) if kp>=0 else ''
        print("   %06x %07x A%d %-34s | org %-52s | %s"%(a,v,r,H[k][0][:34],o,p))
print('--- IMPAIR (toutes origines)')
for c in cls: montre((c,'IMPAIR'))
if quoi:
    for c in cls:
        if quoi=='tout' or quoi in c:
            for res in ('INCONNU','PAIR-faible'):
                print('--- %s / %s'%(c,res)); montre((c,res))
