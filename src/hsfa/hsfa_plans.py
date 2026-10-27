#!/usr/bin/env python3
"""(HANDOFF §120) MEMOIRES DE DECOR rangees TELLES QUELLES dans la ROM graphique etendue du fork (jeu sfa3hx) : le pilote
lit le code brut de chaque plan comme un indice LOCAL a partir de la base du plan ($804200-$804205, unites de 64 Ko).
Plus de tables de renumerotation ni de prise sur les tilemaps (banc_plans.lua : HSFA_PLANS).

  scroll1 (8x8)   : memoire de decor (MWo3) vue en tuiles 8x8, 64 o par element (moitie gauche ET droite : le pilote
                    choisit la moitie selon la parite de la colonne) ............................ $3000000 (base $300)
  scroll2 (16x16) : meme memoire vue en tuiles 16x16, 128 o ........................................ $3400000 (base $340)
  scroll3 (32x32) : conteneur 32x32 du module (e312 / e525), 512 o (= 4 tuiles 16x16 de la ROM) ..... $3A00000 (base $3A0)
Les objets de l'emplacement 1 (memoire de decor, table plan2) pointent sur la zone 16x16 : banques_hx/plan2.bin
= $68000 + indice local.

Usage : MODULE=ro5 hsfa_plans.py   -> <travail>/hsfa_plans.bin (a charger en $3000000 : HSFA_GFX=...,hsfa_plans.bin@3000000)"""
import os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import banques, anthgfx, profils
from hsfa_gfx import encode
sys.path.insert(0, "<workspace>/anthology_extract")
from mwo3_codec import decompress

ORG = 0x3000000
OFF = {1: 0x0000000, 2: 0x0400000, 3: 0x0A00000}          # relatifs a ORG
BASES = {k: (ORG + v) >> 16 for k, v in OFF.items()}

def main():
    W = profils.P['travail']; MOD = banques.MOD
    x = np.frombuffer(bytes(decompress(banques.fichier(MOD['decor']))), np.uint8)
    px = np.stack([x & 0xF, x >> 4], -1).reshape(-1)
    blob = bytearray(OFF[3] + 0x400000)
    # scroll1 : 8x8 -> bloc 16x8 [tuile | tuile], 8 premieres lignes d'un encodage 16x16 (64 o)
    n1 = min(len(px) // 64, 0x10000)
    for m in range(n1):
        t = px[64*m:64*m+64].reshape(8, 8)
        b = np.zeros((16, 16), np.uint8); b[:8, :8] = t; b[:8, 8:] = t
        o = OFF[1] + 64 * m; blob[o:o+64] = encode(b)[:64]
    # scroll2 : 16x16
    n2 = len(px) // 256
    assert OFF[2] + 128 * n2 <= OFF[3], "zone 16x16 trop petite"
    for m in range(n2):
        o = OFF[2] + 128 * m; blob[o:o+128] = encode(px[256*m:256*m+256].reshape(16, 16))
    # scroll3 : conteneur 32x32 -> 4 tuiles 16x16 de la ROM (anthgfx.to_slots), 512 o
    buf = banques.fichier(MOD['b32']); n3 = 0
    # (agent_ro9) tuile VIDE du conteneur (entree 0 de la table = « toute a 15, transparent brut », anthgfx) : rangee en
    # pen 15 (transparente) et non en zeros (pen 0 = couleur 0 OPAQUE). Hyper : le haut des decors ZERO 2 / ZERO 3 est
    # en code 0 sur scroll3 -> aplat gris / bleu qui masquait le ciel. Defaut : actif pour ro5 et ro9 (Upper : tuile 32x32 de code 0 opaque = blocs de couleur sur 16 decors, HANDOFF §141)
    VIDE15 = os.environ.get("HSFA_PLANS_VIDE15", "1" if profils.NOM in ("ro5", "ro9") else "0") == "1"
    for k, m, p in anthgfx.tiles(buf):
        if k != 2 or (p is None and not VIDE15): continue
        if p is None: p = np.full((32, 32), 15, np.uint8)
        s = anthgfx.to_slots(2, p).astype(np.uint8).reshape(4, 16, 16)
        o = OFF[3] + 512 * m
        if o + 512 > len(blob): blob.extend(bytes(o + 512 - len(blob)))
        blob[o:o+512] = b"".join(encode(s[q]) for q in range(4)); n3 = max(n3, m + 1)
    open(os.path.join(W, "hsfa_plans.bin"), "wb").write(bytes(blob).rstrip(b"\0"))
    # objets de l'emplacement 1 : table identite vers la zone 16x16
    hx = banques.OUT.rstrip('/') + '_hx'
    os.makedirs(hx, exist_ok=True)
    (np.arange(n2, dtype=np.uint32) + ((ORG + OFF[2]) >> 7)).astype('<u4').tofile(os.path.join(hx, "plan2.bin"))
    print("scroll1 %d tuiles 8x8, scroll2 %d tuiles 16x16, scroll3 %d tuiles 32x32 (e%d) ; %.1f Mo" %
          (n1, n2, n3, MOD['b32'], len(blob) / 2**20))
    print("bases : HSFA_PLANS=%x,%x,%x ; objets emplacement 1 -> codes $%x+" % (BASES[1], BASES[2], BASES[3], (ORG + OFF[2]) >> 7))

if __name__ == "__main__":
    main()
