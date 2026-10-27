"""Entrée [0] des plXX : table de frames puis grilles de tuiles.
En-tête : N enregistrements de 12 o (N = premier offset / 12) :
  u32 offset (dans l'entrée [0]) de la grille ; u8 largeur, u8 hauteur (en tuiles 16x16), u8 a, u8 b ; u32 c
Grille : largeur x hauteur cases, ligne par ligne ; case = 0xff (vide) ou 3 octets
  (numéro de tuile u16 big-endian, octet d'attributs)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import struct
def frames(f0):
    n = struct.unpack_from("<I", f0, 0)[0] // 12
    out = []
    for i in range(n):
        off, w, h, a, b, c = struct.unpack_from("<IBBBBI", f0, 12*i)
        cells, p = [], off
        for _ in range(w*h):
            if f0[p] == 0xFF: cells.append(None); p += 1
            else: cells.append((f0[p] << 8 | f0[p+1], f0[p+2])); p += 3
        out.append({"w": w, "h": h, "a": a, "b": b, "c": c, "cells": cells, "end": p})
    return out
