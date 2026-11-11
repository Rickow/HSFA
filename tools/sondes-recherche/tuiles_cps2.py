#!/usr/bin/env python3
"""Mesure de réutilisation des tuiles graphiques d'un jeu CPS-2 (ROM de l'utilisateur, jamais versée).

Usage :
  tuiles_cps2.py DOSSIER_ROM --apercu SORTIE.png     planche de contrôle du décodage
  tuiles_cps2.py DOSSIER_ROM --mesure                comptes : exacts, miroirs, quarts 8x8, décalages

Décodage (d'après le pilote CPS-2 de MAME) : sz3.13m..20m chargés en ROM_LOAD64_WORD (13/15/17/19 aux
octets 0/2/4/6 des 16 premiers Mo, 14/16/18/20 pour les 16 suivants), puis « unshuffle » par banques de
2 Mo. Une tuile 16x16 = 16 lignes de 64 bits ; plans aux bits 24, 16, 8, 0 ; x 0-7 puis x 8-15 à +32.
"""
import sys, os, argparse
import numpy as np

FICHIERS = [("sz3.13m", 0, 0), ("sz3.15m", 0, 2), ("sz3.17m", 0, 4), ("sz3.19m", 0, 6),
            ("sz3.14m", 1, 0), ("sz3.16m", 1, 2), ("sz3.18m", 1, 4), ("sz3.20m", 1, 6)]


def charge(d):
    taille = 4 << 20
    gfx = np.zeros(2 * 4 * taille, dtype=np.uint8)
    for nom, moitie, dec in FICHIERS:
        b = np.fromfile(os.path.join(d, nom), dtype=np.uint8)
        base = moitie * 4 * taille
        v = gfx[base:base + 4 * taille].reshape(-1, 8)
        w = b.reshape(-1, 2)
        v[:, dec] = w[:, 0]
        v[:, dec + 1] = w[:, 1]
    return gfx


def unshuffle(q):  # q : tableau de mots de 64 bits (vue), en place
    n = len(q)
    if n == 2:
        return
    n //= 2
    unshuffle(q[:n])
    unshuffle(q[n:])
    a = q[n // 2:n].copy()
    q[n // 2:n] = q[n:n + n // 2]
    q[n:n + n // 2] = a


def decode(gfx):
    q = gfx.view(np.uint64)
    banque = 0x200000 // 8
    for i in range(0, len(q), banque):
        unshuffle(q[i:i + banque])
    lignes = gfx.reshape(-1, 16, 8)          # tuiles, lignes, octets
    bits = np.unpackbits(lignes, axis=2)     # bit 0 = MSB de l'octet 0
    pix = np.zeros((lignes.shape[0], 16, 16), dtype=np.uint8)
    for p, off in enumerate((24, 16, 8, 0)):
        for x in range(16):
            o = off + (x if x < 8 else 32 + x - 8)
            pix[:, :, x] |= (bits[:, :, o] << p).astype(np.uint8)
    return pix


def cle(t):
    return t.reshape(len(t), -1).tobytes()


def hachage(t):  # empreinte 64 bits par tuile
    v = t.reshape(len(t), -1).astype(np.uint64)
    h = np.zeros(len(t), dtype=np.uint64)
    for i in range(v.shape[1]):
        h = h * np.uint64(1099511628211) ^ v[:, i]
    return h


def mesure(pix):
    n = len(pix)
    vide = ~pix.reshape(n, -1).any(axis=1)
    t = pix[~vide]
    print(f"emplacements : {n}  vides : {vide.sum()}  non vides : {len(t)}")
    h = hachage(t)
    u = np.unique(h)
    print(f"uniques exactes : {len(u)}")
    hx, hy, hxy = hachage(t[:, :, ::-1]), hachage(t[:, ::-1, :]), hachage(t[:, ::-1, ::-1])
    canon = np.minimum(np.minimum(h, hx), np.minimum(hy, hxy))
    uc = np.unique(canon)
    print(f"uniques au miroir près : {len(uc)}  (gain {100*(1-len(uc)/len(u)):.2f} %)")
    q = np.concatenate([t[:, :8, :8], t[:, :8, 8:], t[:, 8:, :8], t[:, 8:, 8:]])
    qn = q[q.reshape(len(q), -1).any(axis=1)]
    uq = np.unique(hachage(qn))
    print(f"quarts 8x8 non vides uniques : {len(uq)}  (équivalent 16x16 : {len(uq)/4:.0f}, "
          f"gain {100*(1-len(uq)/4/len(u)):.2f} % ; borne théorique, la CPS-2 ne dessine pas d'objets en 8x8)")
    return t, u


def decalages(pix, uniques_h):
    """Planches de 16 tuiles de large (codes consécutifs = voisines dans le dessin) ; pour chaque fenêtre 16x16
    hors grille, regarde si son contenu est celui d'une tuile existante. Compte les tuiles uniques retrouvées
    hors grille (signe qu'un autre découpage pourrait les réutiliser)."""
    n = len(pix)
    rangs = n // 16
    planche = pix[:rangs * 16].reshape(rangs, 16, 16, 16).transpose(0, 2, 1, 3).reshape(rangs * 16, 256)
    trouves = set()
    pas = 256  # rangées de tuiles par morceau
    us = np.sort(uniques_h)
    for r0 in range(0, rangs, pas):
        a = planche[r0 * 16: min(rangs, r0 + pas) * 16 + 15].astype(np.uint64)
        H, W = a.shape
        if H < 16:
            break
        # empreinte de chaque fenêtre 16x16 : même formule que hachage(), ligne par ligne
        from numpy.lib.stride_tricks import sliding_window_view
        win = sliding_window_view(a, (16, 16))       # (H-15, W-15, 16, 16)
        hh = np.zeros(win.shape[:2], dtype=np.uint64)
        for y in range(16):
            for x in range(16):
                hh = hh * np.uint64(1099511628211) ^ win[:, :, y, x]
        ys, xs = np.nonzero((np.arange(H - 15)[:, None] % 16 != 0) | (np.arange(W - 15)[None, :] % 16 != 0))
        hv = hh[ys, xs]
        nz = (a > 0).astype(np.int32)
        ii = np.zeros((H + 1, W + 1), dtype=np.int32)
        ii[1:, 1:] = nz.cumsum(0).cumsum(1)
        somme = ii[16:, 16:] - ii[:-16, 16:] - ii[16:, :-16] + ii[:-16, :-16]
        hv = hv[somme[ys, xs] > 0]
        pos = np.searchsorted(us, hv)
        pos[pos >= len(us)] = 0
        ok = us[pos] == hv
        trouves.update(np.unique(hv[ok]).tolist())
        print(f"  rangées {r0}-{min(rangs, r0+pas)} : {len(trouves)} tuiles uniques retrouvées hors grille", flush=True)
    print(f"tuiles uniques dont le contenu existe aussi hors grille : {len(trouves)} "
          f"({100*len(trouves)/len(uniques_h):.2f} %)")


def apercu(pix, sortie, debut=0, nb=1024):
    from PIL import Image
    t = pix[debut:debut + nb]
    c = int(np.ceil(nb / 32))
    img = np.zeros((c * 16, 32 * 16), dtype=np.uint8)
    for i, tu in enumerate(t):
        y, x = divmod(i, 32)
        img[y*16:(y+1)*16, x*16:(x+1)*16] = tu * 17
    Image.fromarray(img).resize((32*16*2, c*16*2), Image.NEAREST).save(sortie)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--apercu")
    ap.add_argument("--debut", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--mesure", action="store_true")
    ap.add_argument("--decalages", action="store_true")
    a = ap.parse_args()
    pix = decode(charge(a.rom))
    if a.apercu:
        apercu(pix, a.apercu, a.debut)
    if a.mesure or a.decalages:
        t, u = mesure(pix)
        if a.decalages:
            decalages(pix, u)
