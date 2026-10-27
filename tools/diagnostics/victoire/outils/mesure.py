# mesure.py dossier_snap : par image, pixels "texte vert" de PRESS START (haut droite) et de la replique (bas)
import sys, os
from PIL import Image
d = sys.argv[1]; fs = sorted(f for f in os.listdir(d) if f.endswith('.png'))
def vert(p): r, g, b = p; return g > 150 and r < 170 and b < 150 and g - r > 40
for f in fs:
    im = Image.open(os.path.join(d, f)).convert('RGB'); px = im.load()
    ps = sum(vert(px[x, y]) for x in range(255, 355) for y in range(0, 14))
    q = sum(vert(px[x, y]) for x in range(60, 340) for y in range(180, 216))
    print(f[:-4], ps, q)
