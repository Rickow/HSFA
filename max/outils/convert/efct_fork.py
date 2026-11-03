"""(2026-11-02, Q30) Tuiles des frames d'efct.pac ajoutées à la banque d'un perso MAX (convert_max.EFCT : onde au sol du
QCB+P de Yun, efct 492-498) -> table du fork plXX_hx.bin PROLONGÉE, sans toucher aux codes existants ni à max_gfx.bin.
Entrées : converti/plXX/bank.bin (avec les cases efct à la fin), fork/plXX_hx.bin (état actuel, une entrée par tuile
locale de l'ancienne banque) ; ROM SFA3, hsfa_gfx.bin, fork/max_gfx.bin, fork/max_portraits_gfx.bin (index).
Pour chaque tuile locale AJOUTÉE (index >= longueur de l'ancienne table) :
  transparente -> tuile vide de la ROM SFA3 ; identique à une tuile existante (ROM SFA3, Upper, max_gfx, portraits) ->
  son code ; sinon -> 0x40000000 | j, tuile j de converti/plXX/efct_tuiles.bin (brut CPS2, 16 rangées × 8 o, quartet bas
  = pixel de gauche), à placer par l'intégration dans max_plus_gfx (même convention que bio/table_tuiles.bin).
Usage : python efct_fork.py pl28   (SFA3MAX_CACHE = cache choisi)"""
import os, sys, struct, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx_fork as G
import paths
from cps2_tiles import cps2_pixels


def main(pl):
    F = os.path.join(paths.CACHE, "fork") + "/"; CV = os.path.join(paths.CACHE, "converti", pl) + "/"
    nom = F + "%s_hx.bin" % pl
    if not os.path.exists(nom + ".avant_efct"): shutil.copy(nom, nom + ".avant_efct")
    tab = list(struct.unpack("<%dI" % (os.path.getsize(nom + ".avant_efct") // 4), open(nom + ".avant_efct", "rb").read()))
    new = G.bank_tiles(pl); n0 = len(tab)
    assert len(new) >= n0, "banque plus courte que la table du fork"
    nU = os.path.getsize(G.HSFA_GFX) // 128; base = G.EXT0 + nU
    mg = open(F + "max_gfx.bin", "rb").read(); nM = len(mg) // 128
    pg = open(F + "max_portraits_gfx.bin", "rb").read(); base_p = base + nM
    idx = {}
    for c, t in enumerate(cps2_pixels()): idx.setdefault(bytes(15 - v for v in t), c)
    up = open(G.HSFA_GFX, "rb").read()
    for k in range(nU): idx.setdefault(G.decode(up[128 * k:128 * k + 128]).tobytes(), G.EXT0 + k)
    for k in range(nM): idx.setdefault(G.decode(mg[128 * k:128 * k + 128]).tobytes(), base + k)
    for k in range(len(pg) // 128): idx.setdefault(G.decode(pg[128 * k:128 * k + 128]).tobytes(), base_p + k)
    VIDE_ROM = idx[bytes([15] * 256)]
    neuves, place, n_vide, n_trouve = [], {}, 0, 0
    def code(k):
        nonlocal n_vide, n_trouve
        cle = new[k].tobytes()
        if not (new[k] != 15).any(): n_vide += 1; return VIDE_ROM
        if cle in idx: n_trouve += 1; return idx[cle]
        if cle not in place: place[cle] = len(neuves); neuves.append(new[k])
        return 0x40000000 | place[cle]
    # cases efct placées à la suite des cases du perso : les premières tombent dans la dernière rangée de l'ancienne
    # banque, sur des tuiles jusque-là VIDES (table = tuile vide de la ROM) qui portent maintenant des pixels
    repris = [k for k in range(n0) if tab[k] == VIDE_ROM and (new[k] != 15).any()]
    for k in repris: tab[k] = code(k)
    for k in range(n0, len(new)): tab.append(code(k))
    open(nom, "wb").write(struct.pack("<%dI" % len(tab), *tab))
    raw = bytearray()
    for t in neuves:
        for y in range(16): raw += bytes(int(t[y, 2 * x]) | int(t[y, 2 * x + 1]) << 4 for x in range(8))
    open(CV + "efct_tuiles.bin", "wb").write(raw)
    print("%s : %d tuiles locales ajoutées (%d -> %d) + %d reprises (vides -> pixels : %s) : transparentes %d, existantes %d, "
          "neuves %d (efct_tuiles.bin)" % (pl, len(new) - n0, n0, len(new), len(repris), repris, n_vide, n_trouve, len(neuves)))


if __name__ == "__main__":
    main(sys.argv[1])
