"""Texture GBIX+PVRT des conteneurs plXX (entrée [8] = liste de coups du menu pause).

En-tête : 'GBIX' u32 8, 8 o ; 'PVRT' u32 taille, u8 format (0 = ARGB1555), u8 type (1), u16 0,
u16 largeur, u16 hauteur ; puis les pixels.
ATTENTION : le type vaut 1 (« carré twiddlé » dans la norme Dreamcast) mais les pixels sont en
ordre LINÉAIRE (vérifié visuellement : l'ordre de Morton donne une mosaïque illisible).
Couleur : bit15 = alpha, R = bits 10-14, V = 5-9, B = 0-4."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import struct
from PIL import Image
def untwiddle_index(x, y, bits):
    """Ordre de Morton Dreamcast — conservé pour mémoire, NE s'applique PAS à ces fichiers."""
    i = 0
    for k in range(bits):
        i |= ((y >> k) & 1) << (2*k) | ((x >> k) & 1) << (2*k + 1)
    return i
def decode(b):
    p = b.find(b"PVRT")
    _, fmt, typ, _, w, h = struct.unpack_from("<IBBHHH", b, p + 4)
    assert fmt == 0, fmt
    data = b[p + 16:p + 16 + w*h*2]
    img = Image.new("RGBA", (w, h)); px = img.load()
    for y in range(h):
        for x in range(w):
            v = struct.unpack_from("<H", data, 2*(y*w + x))[0]
            px[x, y] = (((v >> 10) & 31)*255//31, ((v >> 5) & 31)*255//31, (v & 31)*255//31, 255 if v & 0x8000 else 0)
    return img
