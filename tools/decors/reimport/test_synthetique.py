#!/usr/bin/env python3
"""TEST DU CIRCUIT : copie du PSD du pilote dont les bandes « à combler » sont remplies par un remplissage
SYNTHETIQUE (miroir des colonnes voisines), puis passage de reimport.py.

  bande gauche  x 0-63   (canevas) = miroir des colonnes 64-127   (x -> 127 - x)
  bande droite  x 832-895          = miroir des colonnes 768-831  (x -> 1663 - x)
Seules les cases jamais composees (null dans carte_tuiles.json) sont remplies ; le reste du PSD est recopie
tel quel (arbre, noms, visibilites) avec l'ecrivain du pilote (py/psdwriter.py).

Usage : venv/bin/python reimport/test_synthetique.py [--tramage ordonne] [--sortie DIR]
"""
import sys, os, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(D, "py"), os.path.join(D, "export")]
import numpy as np
from psd_tools import PSDImage
from psdwriter import Layer, Group, write_psd
import reimport

SRC = os.path.join(D, "out/decors_sfa3.psd")
EXP = os.path.join(D, "out/decor0C_temple_cloche")


def copie_arbre(grp, W, H, modif):
    out = []
    for l in reversed(list(grp)):                       # psdwriter : du HAUT vers le BAS
        if l.is_group():
            out.append(Group(l.name, copie_arbre(l, W, H, modif), hidden=not l.visible))
            continue
        rgba = np.zeros((H, W, 4), np.uint8)
        im = l.topil()
        if im is not None:
            a = np.asarray(im.convert("RGBA"))
            rgba[l.top:l.top + a.shape[0], l.left:l.left + a.shape[1]] = a
        rgba = modif(l.name, rgba)
        out.append(Layer(l.name, rgba, hidden=not l.visible, opacity=l.opacity))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sortie", default=os.path.join(HERE, "test_0C"))
    ap.add_argument("--tramage", default="aucun")
    ap.add_argument("--zone", default="tout")
    ap.add_argument("--perturber", action="store_true",
                    help="couleurs du remplissage alterees (teinte froide + degrade) : force la creation de palettes")
    a, reste = ap.parse_known_args(); a.reste = reste
    os.makedirs(a.sortie, exist_ok=True)
    carte = json.load(open(os.path.join(EXP, "carte_tuiles.json")))
    p = PSDImage.open(SRC)
    W, H = p.width, p.height
    noms = {cp["nom"]: (L, cp) for L, cp in carte["plans"].items()}

    def modif(nom, rgba):
        cle = [k for k in noms if nom.startswith(k)]
        if not cle: return rgba
        L, cp = noms[cle[0]]
        ts = cp["taille_tuile"]; ox, oy = cp["origine_dans_canevas_psd"]
        inconnu = np.zeros((H, W), bool)
        for r, row in enumerate(cp["cases"]):
            for c, e in enumerate(row):
                if e is None:
                    inconnu[max(0, oy + r*ts):max(0, oy + (r+1)*ts), max(0, ox + c*ts):max(0, ox + (c+1)*ts)] = True
        out = rgba.copy()
        xs = np.arange(W)
        src = np.where(xs < 64, 127 - xs, np.where(xs >= 832, 1663 - xs, xs))
        mir = rgba[:, src].copy()
        if a.perturber:                                   # degrade horizontal + teinte : couleurs hors palettes
            g = (np.abs(xs - 448) / 448.0)[None, :, None]
            rgb = mir[:, :, :3].astype(np.float64)
            rgb = rgb * (0.75 + 0.25 * g) + np.array([10, 25, 60]) * g
            mir[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        out[inconnu] = mir[inconnu]
        print("  %s : %d px remplis par miroir" % (nom[:40], int((inconnu & (mir[:, :, 3] > 0)).sum())))
        return out

    arbre = copie_arbre(p, W, H, modif)
    dst = os.path.join(a.sortie, "decors_sfa3_test_miroir.psd")
    write_psd(dst, W, H, arbre)
    print("PSD de test :", dst)
    return reimport.main(["--psd", dst, "--sortie", a.sortie, "--tramage", a.tramage, "--zone", a.zone] + a.reste)


if __name__ == "__main__":
    sys.exit(main())
