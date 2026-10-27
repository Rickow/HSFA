#!/usr/bin/env python3
"""planche.py DOSSIER IMG0 DEBUT FIN PAS SORTIE [COLONNES] [ECHELLE] : planche contact des captures MAME
(DOSSIER/NNNN.png, la capture n° 0 = image IMG0), images DEBUT..FIN par PAS, legendees du numero d'image."""
import sys, os
from PIL import Image, ImageDraw
d, i0, a, b, p, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
col = int(sys.argv[7]) if len(sys.argv) > 7 else 6
ech = float(sys.argv[8]) if len(sys.argv) > 8 else 0.5
ims = []
for f in range(a, b + 1, p):
    fn = os.path.join(d, "%04d.png" % (f - i0))
    if os.path.exists(fn): ims.append((f, Image.open(fn).convert("RGB")))
w, h = ims[0][1].size; w2, h2 = int(w * ech), int(h * ech)
lig = (len(ims) + col - 1) // col
P = Image.new("RGB", (col * w2, lig * (h2 + 12)), (40, 40, 40))
dr = ImageDraw.Draw(P)
for k, (f, im) in enumerate(ims):
    x, y = (k % col) * w2, (k // col) * (h2 + 12)
    P.paste(im.resize((w2, h2), Image.NEAREST), (x, y + 12)); dr.text((x + 2, y), str(f), fill=(255, 255, 0))
P.save(out); print(out, len(ims))
