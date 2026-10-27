#!/usr/bin/env python3
"""voir.py MOD VA [N] : traduction 68K (carte d'image figee) de la routine contenant VA (ou des N routines suivantes).
MOD = ro5 | ro9 | chemin d'une carte_image.txt (va = fichier)."""
import os, sys, bisect
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
G = "<workspace>/work/greffe_arcade"
mod = sys.argv[1]; va = int(sys.argv[2], 16); n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
carte = {'ro5': G + '/fige/ro5/carte_image.txt', 'ro9': G + '/fige/ro9/carte_image.txt'}.get(mod, mod)
m = 'ro5' if mod == 'ro5' else 'ro9'
st = C.starts(m); k = bisect.bisect_right(st, va) - 1; a = st[k]; b = st[k + n] if k + n < len(st) else a + 0x1000
if os.environ.get("FIN"): b = int(os.environ["FIN"], 16)
for l in open(carte):
    p = l.split(None, 2)
    v = int(p[1], 16)
    if a <= v < b: print(p[0], p[1], p[2].rstrip() if len(p) > 2 else '')
