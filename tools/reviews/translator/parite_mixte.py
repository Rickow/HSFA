#!/usr/bin/env python3
"""parite_mixte.py roN [window=40] -- same An register (not reassigned in between) used both by a byte stream
(An)+ / -(An) (exact address) AND by a byte access d16(An) with a fixed XOR 1: the parity of An alternates, the fixed
form is wrong one time in two (unless the data guarantee the alignment). Candidates to re-read. Review A1.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
mod=sys.argv[1]; W=int(sys.argv[2]) if len(sys.argv)>2 else 40
E=carte.lit(mod)
EA=re.compile(r'(?<![\w$])(?:\$([0-9a-f]{4}))?\(A([0-4])\)(?!\+)')
REAS=re.compile(r'^(?:LEA|MOVEA\.[WL]) .*,A(\d)(?: ;.*)?$')
flux={}   # reg -> index de la derniere entree flux
plain={}  # reg -> (index, texte)
vus=set(); n=0
def montre(i0,i1,r,quoi):
    global n
    key=(E[i0][0],E[i1][0])
    if key in vus: return
    vus.add(key); n+=1
    print("=== %s A%d : %s"%(mod,r,quoi))
    for k in range(max(0,i0-3),min(len(E),i1+3)):
        print("   %s %06x %07x %s"%('>' if k in (i0,i1) else ' ',E[k][0],E[k][1],E[k][2][:150]))
for k,(a,v,t) in enumerate(E):
    h=carte.tete(t); notes=t[len(h):]; op=h.split(' ')[0]
    m=REAS.match(h)
    hits=[]
    isflux=set()
    if op.endswith('.B') or "flux d'octets" in notes:
        for r in range(5):
            c=('[(A%d)+]'%r in notes) or ('[-(A%d)]'%r in notes)
            mm=re.search(r"flux d'octets ([^:]*):",notes)
            if mm and ('(A%d)+'%r in mm.group(1) or '-(A%d)'%r in mm.group(1)): c=True
            if c: isflux.add(r)
    if op.endswith('.B') and ' ; ' not in h and 'XOR 1 a l' not in notes and 'inverses' not in notes:
        for mm in EA.finditer(h):
            r=int(mm.group(2))
            if r in isflux: continue
            if r in flux and k-flux[r]<=W: montre(flux[r],k,r,"flux puis acces fixe")
            plain[r]=k
    for r in isflux:
        if r in plain and k-plain[r]<=W: montre(plain[r],k,r,"acces fixe puis flux")
        flux[r]=k
    if m:
        r=int(m.group(1)); flux.pop(r,None); plain.pop(r,None)
    if op in ('MOVEM.L',) or 'prete' in notes or op=='EXG':
        flux.clear(); plain.clear()
print("%s : %d candidats"%(mod,n))
