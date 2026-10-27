# grille.py sortie.png echelle "titre" "etiquette1=f1,f2,..." "etiquette2=..." : lignes etiquetees (comparaison)
import sys
from PIL import Image, ImageDraw
out, sc, titre = sys.argv[1], float(sys.argv[2]), sys.argv[3]
rows = [(a.split("=", 1)[0], a.split("=", 1)[1].split(",")) for a in sys.argv[4:]]
im0 = Image.open(rows[0][1][0]); w, h = int(im0.width * sc), int(im0.height * sc)
LW = 110; cols = max(len(r[1]) for r in rows)
P = Image.new("RGB", (LW + cols * (w + 2), 22 + len(rows) * (h + 16)), (30, 30, 30)); d = ImageDraw.Draw(P)
d.text((4, 4), titre, fill=(255, 255, 255))
for j, (lab, fs) in enumerate(rows):
    y = 22 + j * (h + 16)
    d.text((4, y + h // 2), lab, fill=(255, 255, 0))
    for i, f in enumerate(fs):
        if not f: continue
        x = LW + i * (w + 2)
        P.paste(Image.open(f).convert("RGB").resize((w, h)), (x, y + 14))
        d.text((x + 2, y + 1), f.split("/")[-1].split(".")[0].split("@")[-1], fill=(180, 180, 180))
P.save(out)
