# bandes.py sortie.png titre "etiquette:dossier[:decalage]" ... -- images : liste d'indices (relatifs) ; une ligne par dossier
import sys, os
from PIL import Image, ImageDraw
out, titre = sys.argv[1], sys.argv[2]
idx = [int(x) for x in os.environ["IMAGES"].split(",")]
rows = [a.split(":") for a in sys.argv[3:]]
sc = float(os.environ.get("ECH", "0.5")); W, H = int(384 * sc), int(224 * sc); LW = 150
P = Image.new("RGB", (LW + len(idx) * (W + 4), 24 + len(rows) * (H + 14)), (30, 30, 30)); d = ImageDraw.Draw(P)
d.text((4, 4), titre, fill=(255, 255, 255))
for r, row in enumerate(rows):
    lab, dd = row[0], row[1]; dec = int(row[2]) if len(row) > 2 else 0
    y = 24 + r * (H + 14); d.text((4, y + H // 2), lab, fill=(255, 255, 0))
    for c, i in enumerate(idx):
        f = os.path.join(dd, "%04d.png" % (i + dec)); x = LW + c * (W + 4)
        d.text((x, y), "%d" % i, fill=(200, 200, 200))
        if os.path.exists(f): P.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y + 12))
P.save(out)
