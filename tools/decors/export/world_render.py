"""Rendu des images monde (pens + palettes) a partir de work/monde.pkl"""
import sys, pickle, collections
sys.path.insert(0, "<workspace>/work/decors_ws/py")
import numpy as np
import cpsgfx as G

def main_entry(counter):
    return max(counter.items(), key=lambda kv: kv[1])[0]

def merged_cells(w):
    """cases vues + cases completees depuis une colonne composee (hors vue verticalement, entree unique)"""
    out = dict(w["cells"]); src = {k: 1 for k in out}
    for k, v in w.get("cells_col", {}).items():
        if k not in out and len(v) == 1:
            out[k] = v; src[k] = 2
    return out, src

def world_pens(W, L, with_src=False):
    """-> pens (HH,WW) uint8 (15 = transparent/inconnu), palette idx (HH,WW), known mask"""
    w = W[L]; ts = w["ts"]
    pen = np.full((w["HH"], w["WW"]), 15, np.uint8); pal = np.zeros((w["HH"], w["WW"]), np.int64)
    known = np.zeros((w["HH"], w["WW"]), bool)
    cells, src = merged_cells(w)
    srcm = np.zeros((w["HH"], w["WW"]), np.uint8)
    for (cc, r), cnt in cells.items():
        code, attr = main_entry(cnt)
        y = r * ts - w["Y0"]; x = cc * ts - w["X0"]
        pen[y:y + ts, x:x + ts] = G.entry_pens(L, code, attr, cc)
        pal[y:y + ts, x:x + ts] = G.LAYERS[L]["pal0"] + (attr & 0x1f)
        known[y:y + ts, x:x + ts] = True
        srcm[y:y + ts, x:x + ts] = src[(cc, r)]
    if with_src: return pen, pal, known, srcm
    return pen, pal, known

def to_rgba(pen, pal, palette, mask=None):
    rgb = palette[pal * 16 + pen]
    a = np.where(pen != 15, 255, 0).astype(np.uint8)
    if mask is not None: a = np.where(mask, a, 0).astype(np.uint8)
    return np.dstack([rgb, a]).astype(np.uint8)
