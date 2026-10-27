#!/usr/bin/env python3
"""planche.py SORTIE.png IMAGES... [--col N] [--max N] : planche contact (captures du banc)"""
import sys
from PIL import Image
a = sys.argv[1:]; col = 5; mx = 20
if "--col" in a: i = a.index("--col"); col = int(a[i + 1]); del a[i:i + 2]
if "--max" in a: i = a.index("--max"); mx = int(a[i + 1]); del a[i:i + 2]
out, fs = a[0], a[1:][:mx]
ims = [Image.open(f) for f in fs]; w, h = ims[0].size
m = Image.new("RGB", (w * col, h * ((len(ims) + col - 1) // col)))
for k, im in enumerate(ims): m.paste(im, ((k % col) * w, (k // col) * h))
m.save(out)
