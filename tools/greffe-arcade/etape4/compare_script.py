#!/usr/bin/env python3
"""compare_script.py UPPER.txt RO9A.txt : suites (image relative, pointeur relatif, commande, parametre) du script de fin
lues dans les journaux surv.lua de $FF0034-$FF003B ($8034 pointeur, $8038 commande, $803A parametre) ; premiere
divergence."""
import sys, os
def lit(f):
    ev = []; f0 = None; p0 = None; ptr = {}
    for l in open(f):
        x = l.split(); im = int(x[1]); a = x[3]; d = int(x[4], 16)
        if f0 is None: f0 = im
        if a in ('ff0034', 'ff0036'):
            ptr[a] = d
            if a == 'ff0036' and 'ff0034' in ptr:
                p = (ptr['ff0036'] << 16 | ptr['ff0034']) & 0xffffff
                if p0 is None: p0 = p
                ev.append((im - f0, 'P', p - p0))
        elif a == 'ff003a': ev.append((im - f0, 'a', d))
    return ev
U, R = lit(sys.argv[1]), lit(sys.argv[2])
for i, (u, r) in enumerate(zip(U, R)):
    if u[1:] != r[1:] or (os.environ.get("TEMPS") == "1" and abs(u[0] - r[0]) > 2):
        print("divergence n°%d : Upper %s / ro9a %s" % (i, u, r))
        print("  Upper :", U[max(0, i - 4):i + 6]); print("  ro9a  :", R[max(0, i - 4):i + 6]); break
else: print("pas de divergence sur %d evenements (Upper %d, ro9a %d)" % (min(len(U), len(R)), len(U), len(R)))
