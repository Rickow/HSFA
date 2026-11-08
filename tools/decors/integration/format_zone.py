#!/usr/bin/env python3
"""format_zone.py — briques communes du format « HSFADC01 » (lot de décors d'une famille, zone des décors de ro9a).

Conventions (celles de la zone des décors, greffe_arcade/e31/DECORS-ZONE.md) :
  - ORDRE PS2 : mots et longs en petit-boutiste (le cœur / banc sert ext_<y>.bin octets échangés par mot ; un MOVE.W 68K
    lit donc la valeur ; un MOVE.L lit les deux mots permutés : SWAP, comme pour toutes les données PS2 de la greffe) ;
  - pointeurs = longs LE ÉTIQUETÉS : $01000000 | adresse 68K (HSFA_ZONES_68K, plages RETAG24) ; 0 = aucun ;
  - chaque lot commence à une adresse 16-alignée.
TLV (annexes) : 0 None, 1 False, 2 True, 3 entier (varint zigzag), 4 réel (double LE), 5 chaîne (n° dans la table des
chaînes, rangée HORS du lot dans annexe_chaines.json), 6 liste (n, éléments), 7 dict (n, (n° de clé, valeur))."""
import struct

TAG = 0x01000000


class Ecrivain:
    def __init__(self, base):
        self.base = base            # adresse 68K (non étiquetée) du 1er octet
        self.b = bytearray(); self.fix = []; self.lab = {}

    def ici(self): return len(self.b)
    def aligne(self, n=4):
        while len(self.b) % n: self.b.append(0)
    def u8(self, v): self.b += struct.pack("<B", v & 0xFF)
    def u16(self, v): self.b += struct.pack("<H", v & 0xFFFF)
    def s16(self, v):
        assert -0x8000 <= v < 0x8000, v
        self.b += struct.pack("<h", v)
    def u32(self, v): self.b += struct.pack("<I", v & 0xFFFFFFFF)
    def s32(self, v): self.b += struct.pack("<i", v)
    def octets(self, x): self.b += bytes(x)
    def etiquette(self, cle):
        assert cle not in self.lab, cle
        self.lab[cle] = len(self.b)
    def ptr(self, cle):
        """long étiqueté vers l'étiquette cle (None -> 0), résolu par fin()"""
        self.fix.append((len(self.b), cle)); self.u32(0)
    def poke16(self, pos, v): struct.pack_into("<H", self.b, pos, v & 0xFFFF)
    def adr(self, cle): return TAG | (self.base + self.lab[cle])
    def fin(self):
        for pos, cle in self.fix:
            struct.pack_into("<I", self.b, pos, 0 if cle is None else self.adr(cle))
        self.aligne(16)
        return bytes(self.b)


class Lecteur:
    def __init__(self, data, base):
        self.d = data; self.base = base
    def u8(self, o): return self.d[o]
    def u16(self, o): return struct.unpack_from("<H", self.d, o)[0]
    def s16(self, o): return struct.unpack_from("<h", self.d, o)[0]
    def u32(self, o): return struct.unpack_from("<I", self.d, o)[0]
    def s32(self, o): return struct.unpack_from("<i", self.d, o)[0]
    def ptr(self, o):
        """long étiqueté -> décalage dans le lot (None si 0) ; vérifie l'étiquette et la borne"""
        v = self.u32(o)
        if v == 0: return None
        assert v & 0xFF000000 == TAG, hex(v)
        r = (v & 0xFFFFFF) - self.base
        assert 0 <= r < len(self.d), (hex(v), hex(self.base))
        return r


# --- TLV des annexes ---------------------------------------------------------------------------------------------------
def _varint(out, n):
    while True:
        x = n & 0x7F; n >>= 7
        if n: out.append(x | 0x80)
        else: out.append(x); return

def _zz(n): return (n << 1) ^ (n >> 63) if n < 0 else n << 1

def tlv_ecrit(v, chaines):
    out = bytearray(); idx = {s: i for i, s in enumerate(chaines)}
    def st(s):
        if s not in idx: idx[s] = len(chaines); chaines.append(s)
        return idx[s]
    def rec(x):
        if x is None: out.append(0)
        elif x is False: out.append(1)
        elif x is True: out.append(2)
        elif isinstance(x, int): out.append(3); _varint(out, _zz(x) if x >= 0 else ((-x) << 1) - 1)
        elif isinstance(x, float): out.append(4); out.extend(struct.pack("<d", x))
        elif isinstance(x, str): out.append(5); _varint(out, st(x))
        elif isinstance(x, list): out.append(6); _varint(out, len(x)); [rec(y) for y in x]
        elif isinstance(x, dict):
            out.append(7); _varint(out, len(x))
            for k, y in x.items(): _varint(out, st(k)); rec(y)
        else: raise TypeError(type(x))
    rec(v); return bytes(out)

def tlv_lit(data, chaines):
    pos = [0]
    def vi():
        n = 0; s = 0
        while True:
            b = data[pos[0]]; pos[0] += 1; n |= (b & 0x7F) << s; s += 7
            if not b & 0x80: return n
    def rec():
        t = data[pos[0]]; pos[0] += 1
        if t == 0: return None
        if t == 1: return False
        if t == 2: return True
        if t == 3:
            z = vi(); return (z >> 1) if not z & 1 else -((z + 1) >> 1)
        if t == 4:
            v = struct.unpack_from("<d", data, pos[0])[0]; pos[0] += 8; return v
        if t == 5: return chaines[vi()]
        if t == 6: return [rec() for _ in range(vi())]
        if t == 7:
            n = vi(); d = {}
            for _ in range(n):
                k = chaines[vi()]; d[k] = rec()
            return d
        raise ValueError(t)
    return rec()


# --- tuiles au format interne MAME / FBNeo (= hsfa_gfx.encode) ----------------------------------------------------------
import numpy as np

def encode(px):
    px = np.asarray(px, np.uint8).reshape(16, 16)
    out = np.zeros((16, 2, 4), np.uint8)
    for h in range(2):
        blk = px[:, 8 * h:8 * h + 8]
        for b in range(4):
            out[:, h, b] = np.packbits((blk >> b) & 1, axis=1)[:, 0]
    return out.tobytes()

def decode(by):
    a = np.frombuffer(bytes(by), np.uint8).reshape(16, 2, 4)
    px = np.zeros((16, 16), np.uint8)
    for h in range(2):
        for b in range(4):
            px[:, 8 * h:8 * h + 8] |= (np.unpackbits(a[:, h, b][:, None], axis=1) << b).astype(np.uint8)
    return px
