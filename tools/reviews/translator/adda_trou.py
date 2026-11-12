#!/usr/bin/env python3
"""adda_trou.py roN -- byte accesses "(An)" (image displacement 0 = PS2 displacement 1) or with two EAs on the same An,
made while byte_after_adda holds An as "parity unknown" (after ADDA.W/L Dk,An, before LEA/MOVEA/break), in a form the
rule did not handle (it only recognised d16(An)). Review E1 ("(An) hole", latent); v161 PARITE_FLOT covers (An).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
import carte
E=carte.lit(sys.argv[1]); dirty={}
for k,(a,v,t) in enumerate(E):
    h=carte.tete(t); op=h.split(' ')[0]; notes=t[len(h):]
    if op.endswith('.B') and dirty and ' ; ' not in h and '[' not in t:
        for r in list(dirty):
            if re.search(r'(?<![\w$])(\$[0-9a-f]{4})?\(A%d\)(?!\+)'%r,h) and not re.search(r'-\(A%d\)'%r,h):
                ko=dirty[r]; print("%06x %07x %-36s | sale depuis %06x %s"%(a,v,h[:36],E[ko][0],carte.tete(E[ko][2])[:40]))
    for part in h.split(' ; '):
        o=part.split(' ')[0]
        m=re.match(r'^ADDA\.[WL] D\d,A(\d)$',part)
        if m: dirty[int(m.group(1))]=k; continue
        m=re.search(r',A(\d)$',part)
        if m and (o.startswith('LEA') or o.startswith('MOVEA')): dirty.pop(int(m.group(1)),None)
        if o in ('RTS','JMP','JSR','BRA') or o.startswith('BRA'): dirty.clear()
