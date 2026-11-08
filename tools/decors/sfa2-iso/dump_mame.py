"""lecture des vidages DMP1 de mame/lua/sonde.lua"""
import struct, numpy as np
TAILLE = 16 + 128 + 0xC00 * 4 + 0x30000 + 0x400 + 0x80
def lit(chemin):
    b = open(chemin, "rb").read(); res = []
    for o in range(0, len(b), TAILLE):
        r = b[o:o + TAILLE]; assert r[:4] == b"DMP1"
        k = struct.unpack_from(">I", r, 4)[0]; tag = r[8:16].decode().strip()
        A = struct.unpack_from(">32H", r, 16); B = struct.unpack_from(">32H", r, 80)
        pens = np.frombuffer(r[144:144 + 0x3000], ">u4")
        g = r[144 + 0x3000:144 + 0x3000 + 0x30000]
        ram = r[144 + 0x3000 + 0x30000:][:0x400]; ae = r[-0x80:]
        res.append(dict(k=k, tag=tag, A=A, B=B, pens=pens, gfx=g, ram=ram, ae=ae))
    return res
def mots(g, base_reg, n):
    o = (base_reg << 8) & 0x3FFFF
    return np.frombuffer(g[o:o + 2 * n], ">u2")
def tilemap_s2(d):
    """grille [ligne 64][colonne 64] de (code, attr) depuis la VRAM (balayage tilemap1 de MAME)"""
    m = mots(d["gfx"], d["A"][2], 64 * 64 * 2).reshape(-1, 2)
    C = np.zeros((64, 64), np.int64); T = np.zeros((64, 64), np.int64)
    for r in range(64):
        for c in range(64):
            i = (r & 0x0f) + ((c & 0x3f) << 4) + ((r & 0x30) << 6); C[r, c], T[r, c] = m[i]
    return C, T
def tilemap_s3(d):
    m = mots(d["gfx"], d["A"][3], 64 * 64 * 2).reshape(-1, 2)
    C = np.zeros((64, 64), np.int64); T = np.zeros((64, 64), np.int64)
    for r in range(64):
        for c in range(64):
            i = (r & 0x07) + ((c & 0x3f) << 3) + ((r & 0x38) << 6); C[r, c], T[r, c] = m[i]
    return C, T
def tilemap_s1(d):
    m = mots(d["gfx"], d["A"][1], 64 * 64 * 2).reshape(-1, 2)
    C = np.zeros((64, 64), np.int64); T = np.zeros((64, 64), np.int64)
    for r in range(64):
        for c in range(64):
            i = (r & 0x1f) + ((c & 0x3f) << 5) + ((r & 0x20) << 6); C[r, c], T[r, c] = m[i]
    return C, T
