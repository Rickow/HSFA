#!/usr/bin/env python3
"""Rend la liste de coups (entrée [8]) de chaque perso, et une planche des bandeaux de noms :
c'est ainsi que la correspondance ID -> perso (pl_mapping.json) a été établie.
Sortie dans $SFA3MAX_CACHE/movelists/ (images dérivées du jeu : hors dépôt)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from PIL import Image, ImageDraw
from plpac import split
from pvr import decode
out = os.path.join(paths.CACHE, "movelists"); os.makedirs(out, exist_ok=True)
files = sorted(f for f in os.listdir(paths.pac_dir()) if f.startswith("pl") and f.endswith(".pac"))
sheet = Image.new("RGB", (2*(60+256), ((len(files)+1)//2)*44)); d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = decode(split(open(os.path.join(paths.pac_dir(), f), "rb").read())[8][1]).convert("RGB")
    im.save(os.path.join(out, f.replace(".pac", "_movelist.png")))
    x, y = (i % 2)*(60+256), (i // 2)*44
    d.text((x+4, y+14), f.replace("_e.pac", ""), fill=(255, 255, 0)); sheet.paste(im.crop((0, 46, 256, 90)), (x+56, y))
sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST).save(os.path.join(out, "noms.png"))
print(len(files), "listes de coups ->", out)
