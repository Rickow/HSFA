"""Contrôle du paquet de test : rendu des 20 frames depuis bank_test.bin + frames_test.json SEULS (palette PSP d'Eagle)."""
import sys, os, json
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from PIL import Image, ImageDraw
from plpac import split
from render import palettes
d = os.path.join(paths.CACHE, "converti", "pl26", "test_banc")
raw = open(os.path.join(d, "bank_test.bin"), "rb").read()
bank = [[n for b in raw[128*t:128*t+128] for n in (b & 15, b >> 4)] for t in range(len(raw) // 128)]
P = palettes(split(open(os.path.join(paths.pac_dir(), "pl26_e.pac"), "rb").read())[2][1])
E = json.load(open(os.path.join(d, "frames_test.json")))
W, H = 200, 220
sheet = Image.new("RGBA", (W * 10, H * 2), (40, 40, 40, 255)); dr = ImageDraw.Draw(sheet)
for k, e in enumerate(E):
    ox, oy = (k % 10) * W + W // 2, (k // 10) * H + 190
    for dx, dy, code, attr in e["objs"]:
        w, h = ((attr >> 8) & 15) + 1, ((attr >> 12) & 15) + 1
        pal = P[attr & 3]
        for j in range(h):
            for i in range(w):
                ii = (w - 1 - i) if attr & 0x20 else i
                jj = (h - 1 - j) if attr & 0x40 else j
                t = bank[code + ii + 16 * jj]
                for y in range(16):
                    for x in range(16):
                        sx = (15 - x) if attr & 0x20 else x
                        sy = (15 - y) if attr & 0x40 else y
                        idx = (16 - (15 - t[16 * sy + sx])) % 16
                        if idx: sheet.putpixel((ox + dx + 16 * i + x, oy + dy + 16 * j + y), pal[idx])
    dr.text(((k % 10) * W + 4, (k // 10) * H + 4), f"{e['action'][:14]}\nRyu {e['ryu_psp_frame']} -> E {e['eagle_psp_frame']}", fill=(255, 255, 0, 255))
sheet.save("test_banc_rendu.png"); print("ok")
