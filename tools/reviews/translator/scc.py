#!/usr/bin/env python3
"""scc.py roN -- Scc of the original 68K rendered as 'Bcc ; MOVE.B #$ff,ea ; BRA ; CLR.B ea' (the MOVE and the CLR set
N/Z, Scc does not). Lists those whose flags from BEFORE are still read afterwards (next Bcc, or RTS with no setter in
between). Review B1.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re, collections
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
mod=sys.argv[1]; E=carte.lit(mod)
BCC={'BEQ','BNE','BPL','BMI','BCS','BCC','BGT','BLE','BLT','BGE'}
NEUTRE=('MOVEA','LEA','ADDA','SUBA','EXG','MOVEM','PEA','NOP')
def op(k): return carte.tete(E[k][2]).split(' ')[0]
def cible(k):
    m=re.search(r'\(cible ([0-9a-f]{8})\)',E[k][2]); return int(m.group(1),16) if m else None
n=0; C=collections.Counter(); vivants=[]
for k in range(len(E)-4):
    if op(k) not in BCC: continue
    h1=carte.tete(E[k+1][2]); h3=carte.tete(E[k+3][2])
    m1=re.match(r'^MOVE\.B #\$(?:ff|ffffffff),(.+)$',h1) or re.match(r'^MOVEQ #-1,(.+)$',h1)
    m3=re.match(r'^CLR\.B (.+)$',h3) or re.match(r'^MOVEQ #\$0,(.+)$',h3)
    inv=False
    if not (m1 and m3):
        m1=re.match(r'^CLR\.B (.+)$',h1); m3=re.match(r'^MOVE\.B #\$(?:ff|ffffffff),(.+)$',h3); inv=True
    if not (m1 and m3 and m1.group(1)==m3.group(1) and op(k+2)=='BRA'): continue
    # le Bcc saute sur le 2e bras, le BRA par-dessus
    if not (cible(k) is not None and E[k+2][1] < cible(k) <= E[k+3][1]): continue
    if not (cible(k+2) is not None and cible(k+2) > E[k+3][1]): continue
    n+=1
    b=op(k)
    # condition vraie -> $FF : le Bcc saute vers le CLR quand la condition est FAUSSE (sauf forme inversee)
    INV={'BEQ':'NE','BNE':'EQ','BPL':'MI','BMI':'PL','BCS':'CC','BCC':'CS','BGT':'LE','BLE':'GT','BLT':'GE','BGE':'LT'}
    DIR={'BEQ':'EQ','BNE':'NE','BPL':'PL','BMI':'MI','BCS':'CS','BCC':'CC','BGT':'GT','BLE':'LE','BLT':'LT','BGE':'GE'}
    scc='S'+(DIR[b] if inv else INV[b])
    # consommateur suivant
    j=k+4; cons=None
    while j<len(E) and j<k+14:
        o=op(j); hb=o.split('.')[0]
        if o in BCC: cons=o; break
        if o=='RTS': cons='RTS'; break
        if hb in NEUTRE or carte.tete(E[j][2]).startswith('('): j+=1; continue
        if o in ('JSR','JMP','BRA'): cons=o; break
        break
    C[(scc,cons)]+=1
    if cons in BCC or cons=='RTS':
        ok = (scc=='SNE' and cons in ('BEQ','BNE'))
        vivants.append((k,j,scc,cons,ok))
print("%s : %d Scc reconnus ; (Scc, consommateur suivant sans poseur) : %s"%(mod,n,dict(C)))
for k,j,scc,cons,ok in vivants:
    print("--- %s puis %s : %s"%(scc,cons,'equivalent (SNE + BEQ/BNE)' if ok else ('A VERIFIER (drapeaux rendus ?)' if cons=='RTS' else 'FAUX')))
    for x in range(k-2,j+1): print("     %06x %07x %s"%(E[x][0],E[x][1],E[x][2][:130]))
