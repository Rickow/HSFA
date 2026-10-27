#!/usr/bin/env python3
"""Ecrivain PSD en Python pur (+ numpy), derive de sfa3-widescreen-android/scripts/assemble_psd.py.

Ajouts par rapport a assemble_psd.py :
  - GROUPES (dossiers) imbriques : section dividers 'lsct' (1 = dossier ouvert, 2 = ferme, 3 = fin de groupe)
  - calques MASQUES (flag visible = bit 1)
  - noms Unicode ('luni', UTF-16) -> accents corrects dans Photoshop/GIMP/Krita
  - compression RLE (PackBits) des canaux de calques (les calques sont surtout transparents)
  - opacite par calque

Arbre de calques : liste ordonnee du HAUT vers le BAS ; chaque element est
  Layer(name, rgba(H,W,4) uint8, hidden=False, opacity=255)
  Group(name, children=[...], hidden=False, closed=False)
"""
import struct
import numpy as np


class Layer:
    """rgba (h,w,4) uint8 place en (top, left) du canevas (rectangle du calque = taille du tableau)"""
    def __init__(self, name, rgba, hidden=False, opacity=255, top=0, left=0):
        self.name, self.rgba, self.hidden, self.opacity = name, rgba, hidden, opacity
        self.top, self.left = top, left
        self.chans = None


class Group:
    def __init__(self, name, children, hidden=False, closed=False):
        self.name, self.children, self.hidden, self.closed = name, children, hidden, closed


def s16(v): return struct.pack(">h", v)
def s32(v): return struct.pack(">i", v)
def u16(v): return struct.pack(">H", v)
def u32(v): return struct.pack(">I", v)


def pascal_pad4(name):
    b = name.encode("latin-1", "replace")[:255]
    s = bytes([len(b)]) + b
    while len(s) % 4:
        s += b"\x00"
    return s


def tagged(key, data):
    if len(data) % 2:
        data += b"\x00"
    return b"8BIM" + key + u32(len(data)) + data


def luni(name):
    u = name.encode("utf-16-be")
    return tagged(b"luni", u32(len(u) // 2) + u)


def packbits_row(row):
    """PackBits d'une ligne (bytes) -> bytes"""
    out = bytearray()
    n = len(row)
    i = 0
    while i < n:
        # cherche une repetition
        j = i + 1
        while j < n and j - i < 128 and row[j] == row[i]:
            j += 1
        if j - i >= 3:
            out.append((257 - (j - i)) & 0xFF)
            out.append(row[i])
            i = j
            continue
        # sequence litterale
        j = i
        while j < n and j - i < 128:
            if j + 2 < n and row[j] == row[j + 1] == row[j + 2]:
                break
            j += 1
        out.append(j - i - 1)
        out += row[i:j]
        i = j
    return bytes(out)


def rle_channel(plane):
    """plane (H,W) uint8 -> donnees canal compression 1 (compte d'octets par ligne + lignes)"""
    H = plane.shape[0]
    rows = []
    for y in range(H):
        r = plane[y]
        if not r.any():
            W = r.shape[0]
            # ligne nulle : runs de 128
            b = bytearray()
            k = W
            while k > 0:
                m = min(128, k)
                if m >= 2:
                    b += bytes([(257 - m) & 0xFF, 0])
                else:
                    b += bytes([0, 0])
                k -= m
            rows.append(bytes(b))
        else:
            rows.append(packbits_row(r.tobytes()))
    return u16(1) + b"".join(u16(len(r)) for r in rows) + b"".join(rows)


def compress_layer(obj, drop=False):
    """compresse les 4 canaux (RLE) ; drop=True libere le tableau (memoire) en gardant la forme"""
    px = obj.rgba
    obj.chans = [rle_channel(np.ascontiguousarray(px[:, :, c])) for c in (0, 1, 2, 3)]
    if drop:
        obj.shape = px.shape[:2]; obj.rgba = None
    return obj.chans


def _flatten(items, out):
    """arbre (haut->bas) -> liste PSD (bas->haut) de tuples (kind, obj)"""
    for it in reversed(items):
        if isinstance(it, Group):
            out.append(("end", it))
            _flatten(it.children, out)
            out.append(("folder", it))
        else:
            out.append(("layer", it))
    return out


def _record(kind, obj, W, H):
    if kind == "layer":
        chans = obj.chans or compress_layer(obj)
        h, w = obj.rgba.shape[:2] if obj.rgba is not None else obj.shape
        rec = s32(obj.top) + s32(obj.left) + s32(obj.top + h) + s32(obj.left + w)
        rec += u16(4)
        for cid, cd in zip((0, 1, 2, -1), chans):
            rec += s16(cid) + u32(len(cd))
        rec += b"8BIM" + b"norm"
        flags = 0x02 if obj.hidden else 0x00
        rec += bytes([obj.opacity, 0, flags, 0])
        extra = u32(0) + u32(0) + pascal_pad4(obj.name) + luni(obj.name)
        rec += u32(len(extra)) + extra
        return rec, b"".join(chans)
    # dossier ou fin de groupe : calque vide
    rec = s32(0) + s32(0) + s32(0) + s32(0) + u16(4)
    for cid in (0, 1, 2, -1):
        rec += s16(cid) + u32(2)
    if kind == "folder":
        name = obj.name
        t = 2 if obj.closed else 1
        flags = 0x02 if obj.hidden else 0x00
        blk = tagged(b"lsct", u32(t) + b"8BIM" + b"pass")
        blend = b"pass"
    else:
        name = "</Layer group>"
        flags = 0x00
        blk = tagged(b"lsct", u32(3))
        blend = b"norm"
    rec += b"8BIM" + blend + bytes([255, 0, flags | 0x08 | 0x10, 0])
    extra = u32(0) + u32(0) + pascal_pad4(name) + luni(name) + blk
    rec += u32(len(extra)) + extra
    return rec, u16(0) * 4


def composite(items, W, H):
    """aplatissement simple (calques visibles, groupes visibles) pour l'image fusionnee / apercu"""
    base = np.zeros((H, W, 4), np.float32)

    def draw(its):
        for it in reversed(its):
            if it.hidden:
                continue
            if isinstance(it, Group):
                draw(it.children)
            else:
                if it.rgba is None: continue
                h, w = it.rgba.shape[:2]
                y0, x0 = it.top, it.left
                ys, xs, ye, xe = max(0, y0), max(0, x0), min(H, y0 + h), min(W, x0 + w)
                if ye <= ys or xe <= xs: continue
                src = it.rgba[ys - y0:ye - y0, xs - x0:xe - x0].astype(np.float32) / 255.0
                a = src[:, :, 3:4] * (it.opacity / 255.0)
                dst = base[ys:ye, xs:xe]
                dst[:, :, :3] = src[:, :, :3] * a + dst[:, :, :3] * (1 - a)
                dst[:, :, 3:4] = a + dst[:, :, 3:4] * (1 - a)
    draw(items)
    return (base * 255 + 0.5).astype(np.uint8)


def write_psd(path, W, H, items, merged=None):
    flat = _flatten(items, [])
    recs, datas = [], []
    for kind, obj in flat:
        r, d = _record(kind, obj, W, H)
        recs.append(r)
        datas.append(d)
    # nombre negatif : le 1er canal alpha contient la transparence de l'image fusionnee
    block = s16(-len(flat)) + b"".join(recs) + b"".join(datas)
    if len(block) % 2:
        block += b"\x00"
    layer_info = u32(len(block)) + block
    lmi = layer_info + u32(0)
    lms = u32(len(lmi)) + lmi
    header = b"8BPS" + u16(1) + b"\x00" * 6 + u16(4) + u32(H) + u32(W) + u16(8) + u16(3)
    if merged is None:
        merged = composite(items, W, H)
    md = u16(0) + b"".join(np.ascontiguousarray(merged[:, :, c]).tobytes() for c in range(4))
    with open(path, "wb") as f:
        f.write(header + u32(0) + u32(0) + lms + md)
    return merged
