# planche.py sortie.png colonnes echelle fichier1 [fichier2 ...] : planche contact avec numero
import sys
from PIL import Image, ImageDraw
out, cols, sc = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]); fs = sys.argv[4:]
ims = [Image.open(f).convert("RGB") for f in fs]
w, h = int(ims[0].width * sc), int(ims[0].height * sc)
rows = (len(ims) + cols - 1) // cols
P = Image.new("RGB", (cols * w, rows * (h + 12)), (40, 40, 40))
d = ImageDraw.Draw(P)
for i, (im, f) in enumerate(zip(ims, fs)):
    x, y = (i % cols) * w, (i // cols) * (h + 12)
    P.paste(im.resize((w, h)), (x, y + 12)); d.text((x + 2, y), f.split("/")[-1], fill=(255, 255, 0))
P.save(out)
