#!/usr/bin/env python3
"""planche.py TRACE IMAGES... SORTIE : assemble les captures (n-ieme ligne SNAP du journal = snap/sfa3hx/NNNN.png)
des images demandees en une planche annotee."""
import sys, os
from PIL import Image, ImageDraw
tr = sys.argv[1]; want = [int(x) for x in sys.argv[2].split(',')]; out = sys.argv[3]
snaps = [l.split() for l in open(os.path.join(tr, 'journal.txt')) if l.startswith('SNAP ')]
sel = []
for w in want:
    best = min(range(len(snaps)), key=lambda i: abs(int(snaps[i][1]) - w))
    sel.append((best, snaps[best]))
ims = [Image.open(os.path.join(tr, 'snap/sfa3hx/%04d.png' % i)).convert('RGB') for i, _ in sel]
w, h = ims[0].size; cols = 4; rows = (len(ims) + cols - 1) // cols
P = Image.new('RGB', (cols * w, rows * (h + 14)), 'black'); d = ImageDraw.Draw(P)
for k, (im, (i, s)) in enumerate(zip(ims, sel)):
    x, y = (k % cols) * w, (k // cols) * (h + 14)
    P.paste(im, (x, y + 14)); d.text((x + 2, y + 1), ' '.join(s[1:]), fill='yellow')
P.save(out)
