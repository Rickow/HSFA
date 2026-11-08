#!/usr/bin/env python3
"""compare_planches.py REF NOUV [SORTIE.tsv] — compare au pixel toutes les images PNG / GIF (toutes les images d'un GIF)
de REF (planches existantes) avec celles de même nom dans NOUV (rendu depuis les lots). Sortie : une ligne par fichier."""
import os, sys
import numpy as np
from PIL import Image, ImageSequence

def images(f):
    im = Image.open(f)
    return [np.asarray(fr.convert("RGB")) for fr in ImageSequence.Iterator(im)]

R, N = sys.argv[1], sys.argv[2]; out = []; tot = [0, 0, 0]
for racine, _, fichiers in os.walk(R):
    for f in sorted(fichiers):
        if not f.endswith((".png", ".gif")): continue
        rel = os.path.relpath(os.path.join(racine, f), R); g = os.path.join(N, rel)
        if not os.path.exists(g): out.append((rel, "absent", "")); tot[2] += 1; continue
        a, b = images(os.path.join(racine, f)), images(g)
        if len(a) != len(b) or any(x.shape != y.shape for x, y in zip(a, b)):
            out.append((rel, "forme", "%d/%d images" % (len(a), len(b)))); tot[1] += 1; continue
        d = sum(int(np.any(x != y, -1).sum()) for x, y in zip(a, b))
        out.append((rel, "identique" if d == 0 else "écart", "%d px sur %d image(s)" % (d, len(a))))
        tot[0 if d == 0 else 1] += 1
txt = "fichier\tverdict\tdetail\n" + "".join("%s\t%s\t%s\n" % l for l in out)
if len(sys.argv) > 3: open(sys.argv[3], "w").write(txt)
print("%s : %d identiques au pixel, %d différents, %d absents" % (N, *tot))
for l in out:
    if l[1] != "identique": print("  ", *l)
