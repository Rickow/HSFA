"""Contrôle : rendu des portraits MAX depuis les seuls fichiers du paquet (portraits.bin / .json / _palettes.bin),
dans les coordonnées d'Upper (cadres verts : 320x160 x -192..192 y -80..80 ; 128x224 x -64..64 y -120..120)."""
import os, sys, json, struct
from PIL import Image, ImageDraw
C = os.path.expanduser("~/.cache/sfa3max/converti")
def rendu(pl, fam, cadre):
    d = os.path.join(C, pl); J = json.load(open(os.path.join(d, "portraits.json")))
    raw = open(os.path.join(d, "portraits.bin"), "rb").read(); P = open(os.path.join(d, "portraits_palettes.bin"), "rb").read()
    X0, Y0, X1, Y1 = cadre; im = Image.new("RGBA", (X1 - X0 + 32, Y1 - Y0 + 32), (40, 40, 40, 255)); px = im.load()
    for code, a, x, y in reversed(J[fam]["objs"]):                 # premier objet = dessus
        pal = struct.unpack_from("<16H", P, 32 * (a & 0x1F))
        for i in range(((a >> 8) & 15) + 1):
            t = raw[128 * (code + i): 128 * (code + i) + 128]
            for yy in range(16):
                for xx in range(16):
                    v = (t[yy * 8 + xx // 2] >> (4 * (xx & 1))) & 15
                    if v == 15: continue
                    c = pal[v]; X, Y = x + 16 * i + xx - X0 + 16, y + yy - Y0 + 16
                    if 0 <= X < im.width and 0 <= Y < im.height: px[X, Y] = ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17, 255)
    ImageDraw.Draw(im).rectangle([16, 16, X1 - X0 + 15, Y1 - Y0 + 15], outline=(0, 255, 0, 255)); return im
if __name__ == "__main__":
    pls = sys.argv[1:] or ["pl26", "pl27", "pl28", "pl29"]
    sh = Image.new("RGBA", (420 + 176 + 170, 260 * len(pls)), (0, 0, 0, 255))
    for k, pl in enumerate(pls):
        sh.paste(rendu(pl, "320x160", (-192, -80, 192, 80)), (0, 260 * k)); sh.paste(rendu(pl, "128x224", (-64, -120, 64, 120)), (420, 260 * k - 0))
        sh.paste(rendu(pl, "128x48", (-64, -24, 64, 24)), (596, 260 * k)); sh.paste(rendu(pl, "96x48", (-48, -24, 48, 24)), (596, 260 * k + 90))
        sh.paste(rendu(pl, "96x16", (-48, -8, 48, 8)), (596, 260 * k + 180))
    sh.save("portraits_max_paquet.png"); print(sh.size)
