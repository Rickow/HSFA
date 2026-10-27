"""Graphismes des persos MAX pour le FORK MAME d'HSFA (jeu sfa3hx, région graphique de 128 Mo).

Entrées : ~/.cache/sfa3max/converti/plXX/bank.bin (tuiles 16x16, 4 bpp linéaire, valeurs brutes CPS2 = convention de
cps2rom.decode d'HSFA) ; ROM graphique SFA3 (sfa3.zip, via tools/max/cps2_tiles.py : brut = 15 - valeur FBNeo) ;
tuiles d'Upper déjà ajoutées par HSFA (HSFA_GFX = hsfa_gfx.bin, codes $40000…, format interne de MAME).
Sorties (~/.cache/sfa3max/fork/) :
  max_gfx.bin  : tuiles NEUVES des persos MAX au format interne de MAME (128 o/tuile), à concaténer APRÈS hsfa_gfx.bin
                 (premier code = $40000 + nombre de tuiles d'Upper) ;
  plXX_hx.bin  : table locale -> code global (u32 LE ; tuile transparente -> code de la tuile vide de la ROM SFA3),
                 comme banques/f<N>.bin ;
  rapport.txt.
Réutilise d'abord une tuile identique de la ROM SFA3, puis d'Upper, puis d'un autre perso MAX."""
import os, sys, struct, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max")) \
    if os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max")) else None
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from cps2_tiles import cps2_pixels
EXT0 = 0x40000
VIDE = 0xFFFFFFFF
HSFA_GFX = os.environ.get("HSFA_GFX", __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "mame_ro5", "hsfa_gfx.bin"))

def encode(px):
    """identique à tools/untranspile/hsfa_gfx.encode : tuile 16x16 -> 128 o, ligne = 8 o (pixels 0-7 puis 8-15),
    octet b = bit b de la valeur, pixel x au bit 7-x"""
    px = np.asarray(px, np.uint8).reshape(16, 16)
    out = np.zeros((16, 2, 4), np.uint8)
    for h in range(2):
        blk = px[:, 8*h:8*h+8]
        for b in range(4):
            out[:, h, b] = np.packbits((blk >> b) & 1, axis=1)[:, 0]
    return out.tobytes()

def decode(raw):
    """inverse d'encode (pour relire hsfa_gfx.bin)"""
    a = np.frombuffer(raw, np.uint8).reshape(16, 2, 4)
    px = np.zeros((16, 16), np.uint8)
    for h in range(2):
        for b in range(4):
            px[:, 8*h:8*h+8] |= (np.unpackbits(a[:, h, b][:, None], axis=1) << b).astype(np.uint8)
    return px

def bank_tiles(pl):
    b = np.fromfile(os.path.join(paths.CACHE, "converti", pl, "bank.bin"), np.uint8).reshape(-1, 16, 8)
    px = np.empty((b.shape[0], 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
    return px

def main():
    out = os.path.join(paths.CACHE, "fork"); os.makedirs(out, exist_ok=True)
    # 1. index : ROM SFA3 (codes 0…), puis Upper (codes $40000…)
    idx = {}
    for c, t in enumerate(cps2_pixels()):
        idx.setdefault(bytes(15 - v for v in t), c)
    up = open(HSFA_GFX, "rb").read(); n_up = len(up) // 128
    for k in range(n_up): idx.setdefault(decode(up[128*k:128*k+128]).tobytes(), EXT0 + k)
    base = EXT0 + n_up
    VIDE_ROM = idx[bytes([15] * 256)]                  # tuile transparente de la ROM SFA3 (brut 15 partout)
    # contrôle de l'encodage : décoder(encoder(x)) = x
    t0 = np.random.RandomState(0).randint(0, 16, (16, 16)).astype(np.uint8)
    assert (decode(encode(t0)) == t0).all()
    neuf, blob, rap = {}, bytearray(), []
    for pl in ("pl26", "pl27", "pl28", "pl29"):
        px = bank_tiles(pl); tab = np.full(len(px), VIDE, np.uint32)
        n_rom = n_up_ = n_max = n_new = 0
        for l in range(len(px)):
            if not (px[l] != 15).any(): tab[l] = VIDE_ROM; continue  # transparente (brut 15) -> tuile vide de la ROM
            cle = px[l].tobytes()
            if cle in idx:
                c = idx[cle]; tab[l] = c
                if c < EXT0: n_rom += 1
                elif c < base: n_up_ += 1
                else: n_max += 1
                continue
            c = base + len(neuf); neuf[cle] = c; idx[cle] = c; blob += encode(px[l]); tab[l] = c; n_new += 1
        tab.astype("<u4").tofile(os.path.join(out, pl + "_hx.bin"))
        rap.append("%s : %d tuiles locales ; réutilisées ROM SFA3 %d, Upper %d, autre perso MAX %d ; neuves %d"
                   % (pl, len(px), n_rom, n_up_, n_max, n_new))
    open(os.path.join(out, "max_gfx.bin"), "wb").write(blob)
    rap.append("tuiles neuves MAX : %d (%.2f Mo), codes $%X-$%X ; à concaténer après hsfa_gfx.bin (%d tuiles d'Upper)"
               % (len(neuf), len(blob) / 2**20, base, base + len(neuf) - 1, n_up))
    rap.append("tuile transparente -> code ROM $%X" % VIDE_ROM)
    rap.append("place totale de la région étendue utilisée : %.1f / 96 Mo" % ((n_up + len(neuf)) * 128 / 2**20))
    open(os.path.join(out, "rapport.txt"), "w").write("\n".join(rap) + "\n")
    print("\n".join(rap))

if __name__ == "__main__":
    main()
