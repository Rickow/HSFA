"""Rendu hors ligne 448x224 (plans seuls) des images capturees par essai_fork.lua (releve FRM0), avec la region du fork
en mode base (hsfa_plans[_decor].bin : scroll1 +0, scroll2 +$400000, scroll3 +$A00000), et comparaisons :
  - centre 384 du rendu vs capture MAME normale (hors sprites/HUD : pixels ou le rendu est opaque et la capture egale
    ailleurs... on compte simplement les ecarts) ;
  - bandes de 32 px du rendu vs apercu 448 de reimport.py : TOUS les pixels (plans seuls, pas de sprites).
Usage : rendu448_fork.py <prefixe essai> <hsfa_plans*.bin> <dossier reimport>"""
import os, sys
sys.path[:0] = ["<workspace>/work/decors_ws/py", "<workspace>/work/decors_ws/reimport"]
import numpy as np
from PIL import Image
from recio import read_rec, read_scr
import cpsgfx as G
import essai_rendu as R

OFF = {1: 0x0000000, 2: 0x0400000, 3: 0x0A00000}
ess, plans, dos = sys.argv[1], sys.argv[2], sys.argv[3]
G.GFX = np.fromfile(plans, np.uint8)
G.GFX = np.concatenate([G.GFX, np.full(OFF[3] + 0x800000 - G.GFX.size, 0, np.uint8)]) if G.GFX.size < OFF[3] + 0x800000 else G.GFX
def phys_base(layer, code):
    if layer == 3: code &= 0x3fff
    return OFF[layer] // G.LAYERS[layer]["tbytes"] + code
G.phys_code = phys_base; G.tile.cache_clear()
scr = read_scr(ess + "_scr.bin")
ok = True
for f in read_rec(ess + "_frm.bin"):
    if f.t not in (1, 3): continue
    side = "gauche" if f.t == 1 else "droite"
    im = R.rendu(f, 448, -32)
    Image.fromarray(im).resize((896, 448), Image.NEAREST).save("%s_rendu448_%s.png" % (ess, side))
    c = int((im[:, 32:416] != scr[f.t]).any(2).sum())
    ap = np.array(Image.open(os.path.join(dos, "apercu_448_%s.png" % side)).convert("RGB"))[::2, ::2]
    sl = slice(0, 32) if side == "gauche" else slice(416, 448)
    n = int((im[:, sl] != ap[:, sl]).any(2).sum()); ok &= n == 0
    # bande du rendu vs capture MAME decalee (sprites/HUD compris : indicatif)
    dec = scr[f.t + 1][:, :32] if side == "gauche" else scr[f.t + 1][:, 352:]
    m = int((im[:, sl] != dec).any(2).sum())
    print("%s %s : bande rendu vs apercu %d px differents / %d ; centre rendu vs capture MAME %d px (sprites/HUD) ; "
          "bande rendu vs capture decalee %d px (sprites/HUD)" % (os.path.basename(ess), side, n, 32 * 224, c, m))
print("RENDU448", "OK" if ok else "ECARTS")
