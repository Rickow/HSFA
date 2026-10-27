"""Format graphique CPS2 de la region :gfx de MAME (= format du fork sfa3hx, HSFA_GFX) : encodage / decodage des
tuiles de plans, adresses par code, couleurs CPS2.

Disposition (MAME cps1_v.cpp, verifiee par py/cpsgfx.py : 0 px d'ecart sur 3 plans x 242 images) :
  - une ligne de tuile = groupes de 8 pixels ; groupe = 4 octets, octet b = bit b du pen des 8 pixels,
    pixel 0 = bit de poids fort (0x80) ;
  - scroll2 16x16 : 16 lignes x 2 groupes = 128 o ;  scroll3 32x32 : 32 lignes x 4 groupes = 512 o ;
  - scroll1 8x8 : un CODE = 64 o = 8 lignes x 2 groupes : groupe 0 = tuile des colonnes PAIRES de la tilemap,
    groupe 1 = tuile des colonnes IMPAIRES (MAME : tile_index & 0x20 = parite de colonne) ;
  - pen 15 = transparent.
Adresse dans la region (mappage CPS2 d'origine, gfxrom_bank_mapper/mapper_cps2) :
  scroll1 : $800000 + code*64 (code 16 bits -> $800000-$BFFFFF)
  scroll2 : $800000 + code*128 (-> $800000-$FFFFFF)
  scroll3 : $800000 + (code & $3FFF)*512
Fork sfa3hx avec base de plan ($804200-$804205, unites de 64 Ko) : (base << 16) + code*taille.
"""
import numpy as np

TS = {1: 8, 2: 16, 3: 32}
TB = {1: 64, 2: 128, 3: 512}          # octets par code
PAL0 = {1: 0x20, 2: 0x40, 3: 0x60}
NOM = {1: "scroll1", 2: "scroll2", 3: "scroll3"}
QUART = 0x800000


def offset(plan, code, base=None):
    """code de tilemap -> decalage d'octet dans la region gfx"""
    if base:
        return (base << 16) + code * TB[plan]
    if plan == 3:
        code &= 0x3FFF
    return QUART + (code & 0xFFFF) * TB[plan]


def code_max(plan, base=None):
    return 0x4000 if plan == 3 else 0x10000


def enc_rows(px):
    """pixels (h, w) pens 0-15, w multiple de 8 -> octets (h lignes, w/8 groupes de 4 octets)"""
    px = np.asarray(px, np.uint8)
    h, w = px.shape
    g = px.reshape(h, w // 8, 8)
    out = np.zeros((h, w // 8, 4), np.uint8)
    for b in range(4):
        out[:, :, b] = np.packbits((g >> b) & 1, axis=2)[:, :, 0]
    return out.tobytes()


def dec_rows(raw, h, w):
    a = np.frombuffer(bytes(raw), np.uint8).reshape(h, w // 8, 4)
    px = np.zeros((h, w // 8, 8), np.uint8)
    for b in range(4):
        px |= (np.unpackbits(a[:, :, b:b + 1], axis=2) << b).astype(np.uint8)
    return px.reshape(h, w)


def encode_code(plan, tiles):
    """plan 2/3 : tiles = tableau (ts, ts) ; plan 1 : tiles = (tuile_paire, tuile_impaire), chacune (8,8) ou None"""
    if plan == 1:
        a, b = tiles
        a = np.full((8, 8), 15, np.uint8) if a is None else a
        b = np.full((8, 8), 15, np.uint8) if b is None else b
        return enc_rows(np.concatenate([a, b], 1))
    return enc_rows(tiles)


def decode_all(region, plan, base=None):
    """toutes les tuiles adressables du plan -> (N, [2,] ts, ts) pens. Plan 1 : (N, 2, 8, 8) (paire, impaire)."""
    ts = TS[plan]
    n = code_max(plan)
    o0 = offset(plan, 0, base)
    raw = np.frombuffer(region, np.uint8, n * TB[plan], o0)
    if plan == 1:
        a = raw.reshape(n, 8, 2, 4)
        px = np.zeros((n, 8, 2, 8), np.uint8)
        for b in range(4):
            px |= (np.unpackbits(a[:, :, :, b:b + 1], axis=3) << b).astype(np.uint8)
        return px.transpose(0, 2, 1, 3).copy()          # (n, moitie, ligne, x)
    a = raw.reshape(n, ts, ts // 8, 4)
    px = np.zeros((n, ts, ts // 8, 8), np.uint8)
    for b in range(4):
        px |= (np.unpackbits(a[:, :, :, b:b + 1], axis=3) << b).astype(np.uint8)
    return px.reshape(n, ts, ts)


def decode_tile(region, plan, code, col=0, base=None):
    """tuile (ts, ts) non retournee ; plan 1 : moitie choisie par la parite de la colonne de tilemap"""
    ts = TS[plan]
    o = offset(plan, code, base)
    raw = bytes(region[o:o + TB[plan]])
    if plan == 1:
        px = dec_rows(raw, 8, 16)
        return px[:, 8 * (col & 1):8 * (col & 1) + 8]
    return dec_rows(raw, ts, ts)


def flip(p, fx, fy):
    if fx: p = p[:, ::-1]
    if fy: p = p[::-1, :]
    return p


# ---------------- couleurs CPS2 ----------------
def cps_rgb(w):
    """mot CPS2 (luminosite, R, V, B) -> RGB, formule MAME (controle du pilote : 1536/1536)"""
    w = np.asarray(w, np.int64)
    b = 0x0F + ((w >> 12) << 1)
    return np.stack([(((w >> s) & 15) * 0x11 * b // 0x2D) for s in (8, 4, 0)], -1).clip(0, 255).astype(np.uint8)


_TABLE = None


LUM_F = True    # SFA3 : les palettes de decor sont rangees en 0RGB et chargees avec « or.l #$F000F000 » ($1FD9E)
                # -> une palette nouvelle n'a que des couleurs de luminosite F (4096 couleurs)


def table_couleurs():
    """(rgb distincts (M,3), mot CPS2 retenu pour chacun) ; LUM_F : mots $Fxxx seulement"""
    global _TABLE
    if _TABLE is None:
        w = np.arange(0xF000 if LUM_F else 0, 0x10000, dtype=np.int64)
        w = w[np.argsort(-(w >> 12), kind="stable")]           # luminosite F d'abord
        rgb = cps_rgb(w)
        key = (rgb[:, 0].astype(np.int64) << 16) | (rgb[:, 1].astype(np.int64) << 8) | rgb[:, 2]
        _, first = np.unique(key, return_index=True)
        _TABLE = (rgb[first].astype(np.int32), w[first])
    return _TABLE


def vers_cps2(rgb):
    """couleurs (K,3) -> (mots CPS2 (K,), rgb CPS2 (K,3)) : couleur CPS2 la plus proche"""
    T, W = table_couleurs()
    rgb = np.asarray(rgb, np.int32).reshape(-1, 3)
    out = np.zeros(len(rgb), np.int64)
    for i in range(0, len(rgb), 256):
        c = rgb[i:i + 256]
        d = ((c[:, None, :] - T[None, :, :]) ** 2).sum(2)
        out[i:i + 256] = d.argmin(1)
    return W[out], T[out].astype(np.uint8)
