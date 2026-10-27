#!/usr/bin/env python3
"""planche.py sortie.png img1 img2 ... [--cols N] [--titres t1,t2,...] : planche d'images avec titres"""
import sys
from PIL import Image, ImageDraw
args=sys.argv[1:]; cols=4; titres=None
if '--cols' in args: i=args.index('--cols'); cols=int(args[i+1]); del args[i:i+2]
if '--titres' in args: i=args.index('--titres'); titres=args[i+1].split('|'); del args[i:i+2]
out=args[0]; fs=args[1:]
ims=[Image.open(f).convert('RGB') for f in fs]
w,h=ims[0].size; th=14; rows=(len(ims)+cols-1)//cols
o=Image.new('RGB',(w*cols,(h+th)*rows),(32,32,32)); d=ImageDraw.Draw(o)
for k,im in enumerate(ims):
    x=(k%cols)*w; y=(k//cols)*(h+th)
    o.paste(im,(x,y+th))
    t=titres[k] if titres and k<len(titres) else fs[k].split('/')[-1]
    d.text((x+2,y+1),t,fill=(255,255,0))
o.save(out); print(out, o.size)
