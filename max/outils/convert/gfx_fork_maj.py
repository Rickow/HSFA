"""Mise à jour SUR PLACE des tuiles d'un perso MAX dans les fichiers du fork (2026-10-17, demande HSFA après le
correctif du liseré des tirs d'Ingrid) : la numérotation des tuiles existantes ne bouge pas.
Entrées : ~/.cache/sfa3max/fork/{max_gfx.bin, plXX_hx.bin, pYY_portraits_hx.bin, max_portraits_gfx.bin} (état actuel),
converti/plXX/bank.bin (nouveaux pixels), ancien bank.bin du perso (argument) ; ROM SFA3 et hsfa_gfx.bin (index).
Règle, pour chaque tuile locale dont les pixels ont changé :
  1. tuile globale de max_gfx employée SEULEMENT par ce perso, et par des tuiles locales qui ont toutes les mêmes
     nouveaux pixels -> RÉÉCRITE SUR PLACE (même code, même si elle devient transparente) ;
  2. sinon, transparente -> tuile vide de la ROM SFA3 ;
  3. sinon : tuile existante identique (ROM SFA3, Upper, max_gfx, portraits) si elle existe ;
  4. sinon : tuile NEUVE ajoutée dans max_gfx_plus.bin, à concaténer APRÈS max_portraits_gfx.bin (codes suivants ;
     aucun code existant ne bouge).
Seules les entrées des cas 2, 3 et 4 changent dans plXX_hx.bin.
Usage : python gfx_fork_maj.py pl29 <ancien_bank.bin>"""
import os, sys, struct, hashlib, collections, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx_fork as G
from cps2_tiles import cps2_pixels
F = os.path.expanduser("~/.cache/sfa3max/fork/")
md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()


def main(pl, ancien):
    nU = os.path.getsize(G.HSFA_GFX) // 128; base = G.EXT0 + nU
    mg = bytearray(open(F + "max_gfx.bin", "rb").read()); nM = len(mg) // 128
    pg = open(F + "max_portraits_gfx.bin", "rb").read(); nP = len(pg) // 128; base_p = base + nM; base_plus = base_p + nP
    avant = {f: md5(F + f) for f in ("max_gfx.bin", "%s_hx.bin" % pl)}
    tabs = {}
    for f in os.listdir(F):
        if f.endswith("_hx.bin"): tabs[f] = list(struct.unpack("<%dI" % (os.path.getsize(F + f) // 4), open(F + f, "rb").read()))
    nom = "%s_hx.bin" % pl; tab = tabs[nom]
    usagers = collections.defaultdict(set)
    for f, t in tabs.items():
        for k, g in enumerate(t): usagers[g].add((f, k))
    old = np.fromfile(ancien, np.uint8).reshape(-1, 16, 8); new = G.bank_tiles(pl)
    oldpx = np.empty((old.shape[0], 16, 16), np.uint8); oldpx[:, :, 0::2] = old & 15; oldpx[:, :, 1::2] = old >> 4
    chg = [k for k in range(len(new)) if not (new[k] == oldpx[k]).all()]
    # contrôle : les tuiles NON changées ont bien les pixels de leur tuile globale actuelle (max_gfx)
    ctl = sum(1 for k in range(len(new)) if base <= tab[k] < base_p and k not in set(chg)
              and not (G.decode(mg[128 * (tab[k] - base):128 * (tab[k] - base) + 128]) == new[k]).all())
    stats = collections.Counter(); plus = bytearray()
    # 2. réécritures sur place
    par_g = collections.defaultdict(list)
    for k in chg: par_g[tab[k]].append(k)
    sur_place = set()
    for g, ks in par_g.items():
        if not base <= g < base_p: continue
        if any(f != nom for f, _ in usagers[g]): continue
        tous = [k for f, k in usagers[g]]                       # toutes les tuiles locales du perso sur ce code
        if len({new[k].tobytes() for k in tous}) == 1:          # (même devenue transparente : la table ne bouge pas)
            mg[128 * (g - base):128 * (g - base) + 128] = G.encode(new[tous[0]]); sur_place.add(g); stats["réécrites sur place"] += len(ks)
    # index pour les cas 3 / 4 (après réécritures)
    idx = {}
    for c, t in enumerate(cps2_pixels()): idx.setdefault(bytes(15 - v for v in t), c)
    up = open(G.HSFA_GFX, "rb").read()
    for k in range(nU): idx.setdefault(G.decode(up[128 * k:128 * k + 128]).tobytes(), G.EXT0 + k)
    for k in range(nM): idx.setdefault(G.decode(mg[128 * k:128 * k + 128]).tobytes(), base + k)
    for k in range(nP): idx.setdefault(G.decode(pg[128 * k:128 * k + 128]).tobytes(), base_p + k)
    VIDE_ROM = idx[bytes([15] * 256)]
    for k in chg:
        if tab[k] in sur_place: continue
        if not (new[k] != 15).any(): tab[k] = VIDE_ROM; stats["devenues transparentes"] += 1; continue
        cle = new[k].tobytes()
        if cle in idx: tab[k] = idx[cle]; stats["tuile existante identique"] += 1; continue
        c = base_plus + len(plus) // 128; plus += G.encode(new[k]); idx[cle] = c; tab[k] = c; stats["neuves (max_gfx_plus)"] += 1
    for f in ("max_gfx.bin", nom):
        if not os.path.exists(F + f + ".avant_maj"): shutil.copy(F + f, F + f + ".avant_maj")
    open(F + "max_gfx.bin", "wb").write(mg)
    open(F + nom, "wb").write(struct.pack("<%dI" % len(tab), *tab))
    if plus: open(F + "max_gfx_plus.bin", "wb").write(plus)
    ancien_tab = struct.unpack("<%dI" % len(tab), open(F + nom + ".avant_maj", "rb").read())
    diff = sum(1 for a, b in zip(ancien_tab, tab) if a != b)
    apres = {f: md5(F + f) for f in ("max_gfx.bin", nom)}
    print("tuiles locales changées :", len(chg), dict(stats))
    print("contrôle (tuiles non changées dont la tuile globale diffère) :", ctl)
    print("taille max_gfx.bin inchangée :", len(mg) // 128 == nM, "; entrées de %s modifiées : %d / %d" % (nom, diff, len(tab)))
    print("max_gfx_plus.bin : %d tuiles, codes $%X…" % (len(plus) // 128, base_plus) if plus else "max_gfx_plus.bin : aucun")
    for f in avant: print("md5 %s : %s -> %s" % (f, avant[f], apres[f]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
