"""Rendu des plans CPS2 hors ligne, fidele au pilote MAME (cps1.cpp) :
   - region :gfx videe depuis MAME (gfx/gfx_region.bin, 32 Mo)
   - dispositions MAME : 8x8 (2 jeux : moitie gauche/droite d'une ligne de 64 bits, selon la parite
     de colonne), 16x16, 32x32 ; plans {24,16,8,0} ; bit 0x80>>(n%8)
   - pen 15 = transparent pour les plans de tuiles
"""
import numpy as np, functools

GFX = None
def load_gfx(path="<workspace>/work/decors_ws/gfx/gfx_region.bin"):
    global GFX
    GFX = np.fromfile(path, np.uint8)
    return GFX

# Geometrie des 3 plans : (taille tuile, regs base/x/y, scan, base palette, octets/tuile, pas de ligne)
LAYERS = {
    1: dict(ts=8,  base=0x02, rx=0x0c, ry=0x0e, pal0=0x20, tbytes=64,  stride=8),
    2: dict(ts=16, base=0x04, rx=0x10, ry=0x12, pal0=0x40, tbytes=128, stride=8),
    3: dict(ts=32, base=0x06, rx=0x14, ry=0x16, pal0=0x60, tbytes=512, stride=16),
}
TM = 64   # 64x64 tuiles par plan

def scan(layer, col, row):
    """index de tuile dans la tilemap (MAME tilemapN_scan)"""
    if layer == 1: return (row & 0x1f) + ((col & 0x3f) << 5) + ((row & 0x20) << 6)
    if layer == 2: return (row & 0x0f) + ((col & 0x3f) << 4) + ((row & 0x30) << 6)
    return (row & 0x07) + ((col & 0x3f) << 3) + ((row & 0x38) << 6)

def _bits(b):  # octet -> 8 bits MSB d'abord
    return np.unpackbits(np.asarray(b, np.uint8))

def phys_code(layer, code):
    """gfxrom_bank_mapper de MAME, table mapper_cps2 : tout le jeu de tuiles des plans est dans
    la 2e banque (0x20000 unites de 64 o = +8 Mo) ; scroll3 : code & 0x3fff."""
    shift = {1: 0, 2: 1, 3: 3}[layer]
    if layer == 3: code &= 0x3fff
    return (0x20000 + ((code << shift) & 0x1ffff)) >> shift

@functools.lru_cache(maxsize=200000)
def tile(layer, code, half=0):
    """-> tableau (ts,ts) de pens 0..15 (non retourne). half = jeu 8x8 (0 gauche, 1 droite)."""
    L = LAYERS[layer]; ts = L["ts"]
    off = phys_code(layer, code) * L["tbytes"]
    if off + L["tbytes"] > GFX.size:
        return np.full((ts, ts), 15, np.uint8)
    raw = GFX[off:off + L["tbytes"]].reshape(ts, -1)         # ts lignes
    if layer == 1:
        raw = raw[:, 4 * half:4 * half + 4]                      # 8 px = 4 octets (1 par plan)
    pen = np.zeros((ts, ts), np.uint8)
    ngrp = raw.shape[1] // 4
    for g in range(ngrp):
        grp = raw[:, 4 * g:4 * g + 4]                           # octets 0..3 ; plan MSB = octet 3
        for p, byte in ((3, 3), (2, 2), (1, 1), (0, 0)):
            bits = np.unpackbits(grp[:, byte:byte + 1], axis=1)  # (ts, 8)
            pen[:, 8 * g:8 * g + 8] |= (bits << p).astype(np.uint8)
    return pen

def tile_entry(fr, layer, col, row):
    L = LAYERS[layer]
    base = (fr.reg(L["base"]) << 8) & 0xffc000
    idx = scan(layer, col, row)
    w = fr.words(0x900000 + base - 0x900000 + 4 * idx, 2) if False else None
    o = (base - 0x900000) // 2 + 2 * idx
    return int(fr.vram[o]), int(fr.vram[o + 1])

def entry_pens(layer, code, attr, col):
    half = col & 1 if layer == 1 else 0
    p = tile(layer, code, half)
    if attr & 0x20: p = p[:, ::-1]
    if attr & 0x40: p = p[::-1, :]
    return p

def tilemap_pens(fr, layer):
    """tilemap complete (64x64 tuiles) -> (pens HxW uint8, palette HxW uint8)"""
    L = LAYERS[layer]; ts = L["ts"]
    W = TM * ts
    pen = np.empty((W, W), np.uint8); pal = np.empty((W, W), np.uint8)
    base = (fr.reg(L["base"]) << 8) & 0xffc000
    o0 = (base - 0x900000) // 2
    for col in range(TM):
        for row in range(TM):
            o = o0 + 2 * scan(layer, col, row)
            code, attr = int(fr.vram[o]), int(fr.vram[o + 1])
            pen[row*ts:(row+1)*ts, col*ts:(col+1)*ts] = entry_pens(layer, code, attr, col)
            pal[row*ts:(row+1)*ts, col*ts:(col+1)*ts] = L["pal0"] + (attr & 0x1f)
    return pen, pal

def render_screen_layer(fr, layer, tmp=None, xoff=64, yoff=16, rowscroll=True):
    """-> (rgb 224x384x3, mask opaque 224x384) du plan seul, comme le rend MAME"""
    L = LAYERS[layer]; ts = L["ts"]; W = TM * ts
    pen, pal = tmp if tmp is not None else tilemap_pens(fr, layer)
    sx = np.arange(384); sy = np.arange(224)
    scx, scy = fr.reg(L["rx"]), fr.reg(L["ry"])
    ty = (sy + yoff + scy) % W
    rs = np.zeros(224, np.int64)
    if layer == 2 and rowscroll and (fr.reg(0x22) & 1):
        other = (fr.reg(0x08) << 8) & 0xffc000 if False else ((fr.reg(0x08) << 8) & 0xfff800)
        oo = (other - 0x900000) // 2
        rso = fr.reg(0x20)
        idx = (sy + yoff + rso) & 0x3ff
        rs = fr.vram[oo + idx].astype(np.int64)
        rs = np.where(rs >= 0x8000, rs - 0x10000, rs)
    tx = (sx[None, :] + xoff + scx + rs[:, None]) % W
    p = pen[ty[:, None], tx]; q = pal[ty[:, None], tx]
    rgb = fr.pal[q.astype(np.int64) * 16 + p]
    return rgb, p != 15

def layer_order(fr):
    """ordre de dessin des plans (bas -> haut), d'apres le layer control CPS-B (MAME cps2 render_layers)"""
    lc = fr.breg(0x26)
    ls = [(lc >> s) & 3 for s in (6, 8, 10, 12)]
    return [l for l in ls if l != 0]

def render_screen(fr_regs, fr_data, layers=(1, 2, 3)):
    """composite des plans (sans sprites) sur fond noir, comme MAME ; regs de l'image t-1, donnees de t"""
    f = mix(fr_regs, fr_data)
    img = np.zeros((224, 384, 3), np.uint8)
    for L in layer_order(f):
        if L not in layers: continue
        rgb, m = render_screen_layer(f, L)
        img[m] = rgb[m]
    return img

def mix(fr_regs, fr_data):
    """image rendue a t = registres CPS-A/B releves a t-1 + VRAM/palette relevees a t (controle : 0 px d'ecart)"""
    import recio
    f = recio.Frame(); f.t = fr_data.t; f.c = fr_data.c
    f.A = fr_regs.A; f.B = fr_regs.B; f.vram = fr_data.vram; f.pal = fr_data.pal
    return f
