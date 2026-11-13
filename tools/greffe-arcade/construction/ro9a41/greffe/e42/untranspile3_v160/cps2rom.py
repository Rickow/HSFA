#!/usr/bin/env python3
"""ROM GRAPHIQUE CPS2 <-> tuiles en valeurs de pixels BRUTES (0..15), dans les deux sens.

Derive exactement du chargement FBNeo (Cps2LoadTiles / Cps2LoadOne / Cps2Load100000 /
Separate, porte dans tools/max/cps2gfx.py), puis inverse :
  - 8 fichiers (ex. SFA3 : 13m 15m 17m 19m | 14m 16m 18m 20m), deux GROUPES de 4 ;
  - dans un groupe, les ROM r0,r1 donnent les pixels 0-7 d'une ligne, r2,r3 les pixels 8-15 ;
    r0 = plans 0,1 (octets pairs/impairs d'un mot), r1 = plans 2,3 ;
  - chaque ROM est lue par blocs de 0x80000 : les mots a 4k alimentent le premier
    0x100000 de tuiles du bloc, les mots a 4k+2 le second ;
  - pixel x d'un octet de plan = bit (7-x).
Valeur BRUTE = ce que stocke l'Anthology (HANDOFF §45) ; FBNeo affiche 15 - brute.

Une LIGNE de tuile (16 pixels) = un « slot » ; tuile 16x16 n = slots 16n..16n+15.
"""
import numpy as np

GROUPS = (("13m", "15m", "17m", "19m"), ("14m", "16m", "18m", "20m"))
BLK = 0x80000

def _slots_shape(L):
    return (L // BLK, 2, BLK // 4)            # (bloc, moitie w, k)

def decode(roms):
    """roms : dict suffixe -> bytes (ex. {'13m': ...}). Rend un tableau (ntuiles,16,16) uint8."""
    out = []
    for grp in GROUPS:
        r = [np.frombuffer(roms[s], dtype=np.uint8) for s in grp]
        L = len(r[0]); nb = L // BLK
        halves = []
        for a, b in ((r[0], r[1]), (r[2], r[3])):
            A = a.reshape(nb, BLK // 4, 4); B = b.reshape(nb, BLK // 4, 4)
            planes = []
            for w in (0, 1):
                p = [A[:, :, 2*w], A[:, :, 2*w+1], B[:, :, 2*w], B[:, :, 2*w+1]]
                planes.append(np.stack(p, -1))                 # (nb, k, 4)
            P = np.stack(planes, 1)                            # (nb, 2, k, 4) : ordre des slots
            bits = np.unpackbits(P[..., None], axis=-1)        # (nb,2,k,4,8) bit7 d'abord = pixel 0
            val = (bits[..., 0, :] | (bits[..., 1, :] << 1) | (bits[..., 2, :] << 2) | (bits[..., 3, :] << 3))
            halves.append(val.reshape(-1, 8))                  # (slots, 8)
        out.append(np.concatenate(halves, axis=1))             # (slots, 16)
    S = np.concatenate(out, 0)
    return S.reshape(-1, 16, 16)

def encode(tiles, rom_len):
    """tiles : (ntuiles,16,16) valeurs brutes 0..15 (ntuiles = 8*rom_len/128). Rend dict suffixe -> bytes."""
    S = np.asarray(tiles, dtype=np.uint8).reshape(-1, 16)
    per = S.shape[0] // 2
    res = {}
    for g, grp in enumerate(GROUPS):
        Sg = S[g*per:(g+1)*per]
        nb = rom_len // BLK
        for hi, (sa, sb) in enumerate(((grp[0], grp[1]), (grp[2], grp[3]))):
            V = Sg[:, 8*hi:8*hi+8].reshape(nb, 2, BLK // 4, 8)     # (bloc, w, k, pixel)
            A = np.zeros((nb, BLK // 4, 4), np.uint8); B = np.zeros_like(A)
            for w in (0, 1):
                pl = [np.packbits(((V[:, w] >> p) & 1).astype(np.uint8), axis=-1)[..., 0] for p in range(4)]
                A[:, :, 2*w] = pl[0]; A[:, :, 2*w+1] = pl[1]; B[:, :, 2*w] = pl[2]; B[:, :, 2*w+1] = pl[3]
            res[sa] = A.tobytes(); res[sb] = B.tobytes()
    return res
