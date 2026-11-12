#!/usr/bin/env python3
"""fragments_atteints.py roN APPELS_C_FILE -- for each 'jal' of recompiled code to a NON-listed native C function
(section "C-NON-LISTEE / appelant recompile / appel emis" of the saved output of appels_c.py): REAL target of the call
in the translated image (bytes):
  TALON     address < $1000 (kernel: RTS $800, entries, etc.) -> replaced;
  FRAGMENT  the call goes to the label of the C function = fragments emitted by the translator -> executed as is;
  AUTRE     other address.
Needs the build's program ROMs (img.image: IMG or HSFA_BUILD) and capstone (imported by img.py). Review E2.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, re, struct, bisect, os
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte, img
from mips import Ins, CODE0
mod=sys.argv[1]; I=img.image(mod)
buf=paths.module(mod)
E=carte.lit(mod); V=[e[1] for e in E]
def cible(a):
    w=struct.unpack_from('>H',I,a)[0]
    if w in (0x4eb9,0x4ef9): return struct.unpack_from('>I',I,a+2)[0]
    if (w&0xfe00)==0x6000:
        d=w&0xff
        if d==0: return a+2+struct.unpack_from('>h',I,a+2)[0]
        return a+2+(d-256 if d>127 else d)
    return None
T=[]; ok=False
if len(sys.argv)<3: sys.exit(__doc__)
for l in open(sys.argv[2],encoding='utf-8',errors='replace'):
    if l.startswith('---'): ok='C-NON-LISTEE / appelant recompile / appel emis' in l; continue
    m=re.match(r'\s+site ([0-9a-f]+) -> ([0-9a-f]+) \(n=(\d+)',l)
    if m and ok: T.append((int(m.group(1),16),int(m.group(2),16),int(m.group(3))))
res={}
for s,t,n in T:
    k=bisect.bisect_left(V,s); c=None; ai=None
    while k<len(E) and E[k][1]==s:
        h=carte.tete(E[k][2])
        if h.startswith(('JSR','JMP','BSR')): ai=E[k][0]; c=cible(ai)
        k+=1
    kt=bisect.bisect_left(V,t); lab=E[kt][0] if kt<len(E) else None
    cl='?' if c is None else ('TALON $%x'%c if c<0x1000 else ('FRAGMENT' if c==lab else 'AUTRE $%x'%c))
    res.setdefault((t,n),[]).append((s,ai,cl))
print("%s : appels du code recompile vers des fonctions C non listees"%mod)
for (t,n),l in sorted(res.items()):
    print("  cible %06x (%d instr.) : %s"%(t,n,' ; '.join('%x(image %s) %s'%(s,'%06x'%ai if ai else '?',cl) for s,ai,cl in l)))
