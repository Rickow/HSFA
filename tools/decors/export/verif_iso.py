"""Controle : rendu hors ligne d'un plan (releve full.rec) vs capture MAME du plan isole (scr_N.bin)."""
import sys; sys.path.insert(0, "<workspace>/work/decors_ws/py")
from recio import *; import cpsgfx as G; import numpy as np
from PIL import Image
G.load_gfx()
frs = read_rec("<workspace>/work/decors_ws/rec/full.rec")
ts = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else None
tot = 0
for L in (1, 2, 3):
    scr = read_scr("<workspace>/work/decors_ws/rec/scr_%d.bin" % L)
    for t in (ts or sorted(scr)):
        if t < 8: continue      # 1res images : liste de sprites de l'etat charge
        rgb, m = G.render_screen_layer(frs[t], L)
        mine = np.where(m[:, :, None], rgb, 0).astype(np.uint8)
        d = (mine != scr[t]).any(2); tot += d.sum()
        if d.sum() or ts: print("L%d t=%d diff=%d opaque=%d" % (L, t, d.sum(), m.sum()))
        if ts: Image.fromarray(np.concatenate([mine, scr[t]], 1)).save("<workspace>/work/decors_ws/cap/cmp_L%d_t%d.png" % (L, t))
print("TOTAL px differents", tot)
