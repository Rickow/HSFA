#!/usr/bin/env python3
"""reloge_refs.py roN [detail] -- tables relocated by step B / C (etapeB_reloge.txt, etapeC_ram.txt of the build):
looks in the module's DATA for longs that point INTO a relocated table (possible indirect reader, which
assemble.natif() does not see: it only looks for citations in the mnemonics), and in the map for the lines that cite
the table (T_xxxxxx or [PS2 00xxxxxx]). Any second argument lists the citations. Review E4 (found sound).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re, struct, bisect
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
mod=sys.argv[1]; D=paths.construction(mod)
buf=paths.module(mod)
CODE1=struct.unpack_from('<I',buf,12)[0]; RB=0x1f0000
T=[]
for f,k in (('etapeB_reloge.txt','B'),('etapeC_ram.txt','C')):
    for l in open(os.path.join(D,f),encoding='utf-8'):
        m=re.match(r'table ([0-9a-f]+)-([0-9a-f]+) .*?(ordre 68K)?$',l.rstrip())
        if m: T.append((int(m.group(1),16),int(m.group(2),16),k,bool(m.group(3))))
T.sort(); S=[t[0] for t in T]
def dans(v):
    k=bisect.bisect_right(S,v)-1
    return T[k] if k>=0 and T[k][0]<=v<T[k][1] else None
E=carte.lit(mod)
cite={}
for a,v,t in E:
    for m in re.finditer(r'(?:T_|\[PS2 00)([0-9a-f]{6})',t):
        x=dans(int(m.group(1),16))
        if x: cite.setdefault(x[0],[]).append((a,t))
ptr={}
for o in range(CODE1&~3,len(buf)-3,4):
    v=struct.unpack_from('<I',buf,o)[0]
    x=dans(v)
    if x: ptr.setdefault(x[0],[]).append((o+RB,v))
# mots haut/bas separes (lui/addiu) dans le code hors zone traduite : non cherche
print("%s : %d tables relogees (%d en ordre 68K)"%(mod,len(T),sum(1 for t in T if t[3])))
for p,f,k,nat in T:
    c=cite.get(p,[]); q=ptr.get(p,[])
    print("  %s %06x-%06x %s : %d citations dans la carte, %d pointeurs dans les donnees%s"%(k,p,f,'ordre 68K' if nat else 'echange  ',len(c),len(q),'  <<<' if q else ''))
    for o,v in q[:6]: print("       donnee PS2 %06x -> %06x"%(o,v))
    if len(sys.argv)>2:
        for a,t in c: print("       %06x %s"%(a,t[:110]))
