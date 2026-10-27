#!/usr/bin/env python3
"""sites_diff.py CARTE_REF CARTE_NOUVELLE : instructions 68K differentes par va MIPS (texte de la carte d'image, adresses
68K ignorees) -> liste des va MIPS touchees, avec avant / apres."""
import sys, collections
def charge(p):
    d = collections.defaultdict(list)
    for l in open(p):
        q = l.split(None, 2)
        if len(q) > 2: d[q[1]].append(q[2].strip())
    return d
A, B = charge(sys.argv[1]), charge(sys.argv[2])
n = 0
for va in sorted(set(A) | set(B), key=lambda x: int(x, 16)):
    if A.get(va) != B.get(va):
        n += 1; print("%s | %s || %s" % (va, ' ; '.join(A.get(va, [])), ' ; '.join(B.get(va, []))))
print("%d va touchees" % n, file=sys.stderr)
