"""Petits visages de la barre de vie (HUD) des 4 persos MAX (2026-10-11, questions 5/8 de l'agent d'intégration HSFA).
Source PSP : pit_e.pac (HUD de combat : frames, tuiles 16x16, 40 palettes propres au HUD). Code PSP 0x8B0EC :
  visage J1 = frame 0x17D + T[perso], visage J2 = frame 0x1AA + T[perso], T = octets 0x222D76 (42 entrées ;
  $26-$29 -> 40-43, soit frames 421-424 en J1 et 466-469 en J2). Les cellules ont la palette relative 0 : le visage
  est dessiné avec les palettes DU PERSO (contrôlé à l'œil : palette 0 du groupe de couleur = teint naturel ; Ingrid :
  groupes de 8 sur PSP, de 5 dans palettes_module_upper.bin).
Sortie ~/.cache/sfa3max/converti/plXX/ : hud.bin (tuiles brutes CPS2, 4 bpp, 15 = transparent, numérotation locale ;
blocs de codes consécutifs dans une rangée de 16) et hud.json : {"J1"|"J2": objets [code local, attributs CPS2
((w-1) << 8 | r), x, y]} ; r = palette RELATIVE au groupe du joueur (0 = 1re des 5 palettes copiées par le moteur) ;
x, y = coin haut-gauche de l'objet par rapport au coin haut-gauche de la frame PSP (32x32 ou 48x32)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portraits_max import Sortie, tuiles_calque
from ecrans import Ecran
from relocs import img
PIT = os.path.expanduser("~/.cache/sfa3max/data/pit_e.pac")
NOMS = {0x26: "pl26", 0x27: "pl27", 0x28: "pl28", 0x29: "pl29"}


def main():
    ec = Ecran(PIT); T = img[0x222D76:0x222D76 + 42]
    for cid, pl in NOMS.items():
        S = Sortie(); S.palette = lambda e, p: p           # attribut = palette relative telle quelle (0 = 1re du groupe)
        out = {}
        for cote, base in (("J1", 0x17D), ("J2", 0x1AA)):
            n = base + T[cid]; f = ec.F[n]
            out[cote] = {"frame_psp": n, "taille": [16 * f["w"], 16 * f["h"]], "objs": S.calque(ec, n, 0, 0, 0)}
        d = os.path.expanduser("~/.cache/sfa3max/converti/%s" % pl)
        with open(os.path.join(d, "hud.bin"), "wb") as fo:
            for t in S.tuiles:
                raw = [15 - ((16 - i) % 16) for i in (t or [0] * 256)]
                fo.write(bytes(raw[2 * k] | (raw[2 * k + 1] << 4) for k in range(128)))
        json.dump(out, open(os.path.join(d, "hud.json"), "w"), indent=1)
        print(pl, "tuiles", len(S.tuiles), {k: (v["frame_psp"], len(v["objs"])) for k, v in out.items()})


if __name__ == "__main__":
    main()
