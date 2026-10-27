#!/usr/bin/env python3
"""Rendu de frames et analyse des sprites composites.
  python3 sprites.py pl00 0 40 317        # frames choisies d'un perso -> $SFA3MAX_CACHE/sprites/
  python3 sprites.py --ingrid              # structure d'Ingrid + planche de poses recomposées (haut + bas)
Ingrid (pl29) : frames regroupées par sous-palette (attr & 3) : 0 = haut du corps (687), 1 = bas du corps (687),
2 = poses complètes (8), 3 = effets (431). Pose k = haut k + bas k, même ancre."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import collections
from PIL import Image, ImageDraw
from render import Char
OUT = os.path.join(paths.CACHE, "sprites"); os.makedirs(OUT, exist_ok=True)
def blocks(ch):
    dom = []
    for fr in ch.F:
        c = collections.Counter(x[1] & 3 for x in fr["cells"] if x)
        dom.append(c.most_common(1)[0][0] if c else None)
    runs, s = [], 0
    for i in range(1, len(dom) + 1):
        if i == len(dom) or dom[i] != dom[s]: runs.append((s, i - 1, dom[s])); s = i
    return dom, runs
def ingrid():
    ch = Char(os.path.join(paths.pac_dir(), "pl29_e.pac"))
    dom, runs = blocks(ch)
    multi = sum(1 for fr in ch.F if len({x[1] & 3 for x in fr["cells"] if x}) > 1)
    print(f"Ingrid : {len(ch.F)} frames, {len(ch.P)} palettes ; frames à plusieurs sous-palettes : {multi}")
    print("blocs (début, fin, sous-palette) :", runs)
    print("par sous-palette :", dict(collections.Counter(dom)))
    upper = [n for n, p in enumerate(dom) if p == 0]; lower = [n for n, p in enumerate(dom) if p == 1]
    print(f"haut {len(upper)} / bas {len(lower)} ; ancres identiques par paire : "
          f"{sum(1 for u, l in zip(upper, lower) if (ch.F[u]['a'], ch.F[u]['c']) == (ch.F[l]['a'], ch.F[l]['c']))}/{len(upper)}")
    ks = (0, 40, 150, 300, 450, 600)
    sheet = Image.new("RGBA", (len(ks)*190, 250), (20, 20, 20, 255)); d = ImageDraw.Draw(sheet)
    for i, k in enumerate(ks):
        cv = Image.new("RGBA", (180, 230), (40, 40, 40, 255))
        for n in (lower[k], upper[k]):
            fr = ch.F[n]; cv.alpha_composite(ch.frame(n, bg=(0, 0, 0, 0)), (max(0, 90 - fr["a"]), max(0, 200 - fr["c"])))
        sheet.paste(cv, (i*190, 20)); d.text((i*190, 2), f"pose {k}", fill=(255, 255, 0))
    p = os.path.join(OUT, "ingrid_poses.png"); sheet.save(p); print("->", p)
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--ingrid": ingrid()
    elif len(sys.argv) > 2:
        ch = Char(os.path.join(paths.pac_dir(), f"{sys.argv[1]}_e.pac"))
        for n in map(int, sys.argv[2:]):
            p = os.path.join(OUT, f"{sys.argv[1]}_f{n}.png"); ch.frame(n).save(p); print("->", p)
    else: print(__doc__)
