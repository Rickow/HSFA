"""Compare des captures SCR0 (decors_ws/py/recio.read_scr) : nb de px differents par capture ; PNG x2 optionnels."""
import sys, os
sys.path.insert(0, "<workspace>/work/decors_ws/py")
import numpy as np
from PIL import Image
from recio import read_scr
def charge(p): return read_scr(p)
def png(scr, prefixe):
    for t, im in scr.items():
        Image.fromarray(im).resize((im.shape[1] * 2, im.shape[0] * 2), Image.NEAREST).save("%s_%d.png" % (prefixe, t))
if __name__ == "__main__":
    a, b = charge(sys.argv[1]), charge(sys.argv[2])
    for t in sorted(a):
        if t not in b: continue
        d = (a[t] != b[t]).any(2)
        cols = np.nonzero(d.any(0))[0]
        print("capture %d : %6d px differents, colonnes %s" % (t, int(d.sum()), "%d-%d" % (cols.min(), cols.max()) if cols.size else "-"))
    if len(sys.argv) > 3:
        png(a, sys.argv[3])
