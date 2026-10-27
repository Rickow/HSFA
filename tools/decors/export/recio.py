"""Lecture des fichiers produits par lua/rec.lua (releve par image + captures ecran)."""
import struct, numpy as np

FRAME_SZ = 12 + 64 + 64 + 0xC00 * 4 + 0x10000

class Frame:
    __slots__ = ("t", "c", "A", "B", "pal", "vram", "mode", "camy", "pages")
    def reg(self, off):            # registre CPS-A (offset octet)
        return int(self.A[off // 2])
    def breg(self, off):
        return int(self.B[off // 2])
    def words(self, addr, n):      # mots de la RAM video ($900000-$90FFFF)
        o = (addr - 0x900000) // 2
        return self.vram[o:o + n]

def read_rec(path):
    data = open(path, "rb").read()
    if data[:4] == b"FRM2":
        return read_rec2(data)
    n = len(data) // FRAME_SZ
    out = []
    for i in range(n):
        b = data[i * FRAME_SZ:(i + 1) * FRAME_SZ]
        assert b[:4] == b"FRM0"
        f = Frame()
        f.t, f.c = struct.unpack(">II", b[4:12])
        p = 12
        f.A = np.frombuffer(b, ">u2", 32, p).astype(np.int64); p += 64
        f.B = np.frombuffer(b, ">u2", 32, p).astype(np.int64); p += 64
        pal = np.frombuffer(b, ">u4", 0xC00, p).astype(np.uint32); p += 0xC00 * 4
        f.pal = np.stack([(pal >> 16) & 255, (pal >> 8) & 255, pal & 255], 1).astype(np.uint8)
        f.vram = np.frombuffer(b, ">u2", 0x8000, p).astype(np.int64)
        out.append(f)
    return out

def read_scr(path):
    """-> dict t -> image RGB uint8 (h, w, 3)"""
    data = open(path, "rb").read()
    p, out = 0, {}
    while p < len(data):
        tag, t, w, h = struct.unpack(">4sIII", data[p:p + 16]); p += 16
        assert tag == b"SCR0"
        a = np.frombuffer(data, np.uint8, w * h * 4, p).reshape(h, w, 4); p += w * h * 4
        out[t] = a[:, :, [2, 1, 0]].copy()
    return out


MODES = {0: "nat", 1: "haut", 2: "cup", 3: "cdn"}

def read_rec2(data):
    """format FRM2 (lua/rec_all.lua) : en-tete 20 o, CPS-A, CPS-B, palette, pages de 64 Ko de RAM video.
    vram = 0x18000 mots (uint16) ; pages non relevees = 0."""
    out, p = [], 0
    N = len(data)
    while p < N:
        assert data[p:p + 4] == b"FRM2", p
        f = Frame()
        f.t, f.c, m, f.camy, pm = struct.unpack(">IIHhH", data[p + 4:p + 18]); p += 18
        f.mode = MODES[m]; f.pages = pm
        f.A = np.frombuffer(data, ">u2", 32, p).astype(np.int64); p += 64
        f.B = np.frombuffer(data, ">u2", 32, p).astype(np.int64); p += 64
        pal = np.frombuffer(data, ">u4", 0xC00, p).astype(np.uint32); p += 0xC00 * 4
        f.pal = np.stack([(pal >> 16) & 255, (pal >> 8) & 255, pal & 255], 1).astype(np.uint8)
        v = np.zeros(0x18000, np.uint16)
        for pg in range(3):
            if pm & (1 << pg):
                v[pg * 0x8000:(pg + 1) * 0x8000] = np.frombuffer(data, ">u2", 0x8000, p); p += 0x10000
        f.vram = v
        out.append(f)
    return out
