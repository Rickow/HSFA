"""Portraits d'Upper (module ro5) : table 0x484C00 (66 poses : u16 décalages ; blocs de 40 ID × {u32 attributs, u32
ptr frame}) ; frames de TYPE 8 : u16 type, u16 T, u16 n-1, puis n × (u16 code, u16 attributs CPS2, s16 x, s16 y) ;
le constructeur ajoute $1600 au code ; emplacement 1 : code ROM = code + $1600 + $15600 (HSFA §85)."""
import os, sys, struct, collections
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from cps2_tiles import cps2_pixels
from PIL import Image
B5 = open(os.path.join(os.environ["ANTHOLOGY_DIR"], "decompressed", "ro5_usa_prog68k.bin"), "rb").read()
T = 0x484C00; OFFS = struct.unpack_from("<66H", B5, T)
def entree(pose, ID): return struct.unpack_from("<2I", B5, T + OFFS[pose] + 8 * ID)
def frame8(adr):
    o = adr - 0x1F0000
    if not (0 <= o < len(B5) - 8): return None
    t, TT, n1 = struct.unpack_from("<3H", B5, o)
    if t != 8: return None
    return [struct.unpack_from("<HHhh", B5, o + 6 + 8 * k) for k in range(n1 + 1)]
_CP = None
def rendu(objs, code_rom=lambda c: c + 0x1600 + 0x15600):
    global _CP
    _CP = _CP or cps2_pixels()
    xs = [x for _, a, x, _ in objs] + [x + 16 * (((a >> 8) & 15) + 1) for _, a, x, _ in objs]
    ys = [y for _, a, _, y in objs] + [y + 16 * (((a >> 12) & 15) + 1) for _, a, _, y in objs]
    x0, y0 = min(xs), min(ys); im = Image.new("L", (max(xs) - x0, max(ys) - y0), 40); px = im.load()
    for code, a, x, y in objs:
        w, h = ((a >> 8) & 15) + 1, ((a >> 12) & 15) + 1
        for j in range(h):
            for i in range(w):
                ii = (w - 1 - i) if a & 0x20 else i; jj = (h - 1 - j) if a & 0x40 else j
                c = code_rom(code) + ii + 16 * jj
                if c >= len(_CP): continue
                t = _CP[c]
                for yy in range(16):
                    for xx in range(16):
                        v = t[16 * yy + xx]
                        if v == 0: continue                 # FBNeo 0 = transparent (brut 15)
                        X = (15 - xx) if a & 0x20 else xx; Y = (15 - yy) if a & 0x40 else yy
                        px[x - x0 + 16 * i + X, y - y0 + 16 * j + Y] = 40 + v * 13
    return im
if __name__ == "__main__":
    ID = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0
    par = collections.OrderedDict()
    for p in range(66):
        a, f = entree(p, ID)
        if frame8(f) is not None: par.setdefault(f, []).append(p)
    ims = []
    for f, poses in par.items():
        im = rendu(frame8(f)); ims.append((im, poses))
        print("frame %#x poses %s taille %s" % (f, poses, im.size))
    W = sum(i.width for i, _ in ims) + 10 * len(ims); H = max(i.height for i, _ in ims)
    sh = Image.new("L", (W, H), 0); x = 0
    for i, _ in ims: sh.paste(i, (x, 0)); x += i.width + 10
    sh.save("portraits_upper_%02x.png" % ID); print(sh.size)
