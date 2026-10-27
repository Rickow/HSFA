"""PALETTES DE DECOR VRAIMENT LIBRES, par decor et par plan, d'apres les tilemaps COMPLETES reconstruites depuis les
donnees du programme (listes + bibliotheques : tout ce que le jeu peut afficher, au-dela de la course enregistree),
et non d'apres le releve de la course (qui manque les cases visibles seulement quand la camera monte plus haut, ex.
super de Cammy, et les phases d'animation).
  - avec relogement (fork / FBNeo, injection_fork.py) : tout emplacement 0-31 non utilise, sauf scroll3 $7F (forcee
    au blanc par la routine du jeu, qui ne copie que 31 palettes) ;
  - sans relogement (arcade, en place) : seulement les emplacements du bloc PROPRE du decor.
Usage : palettes_libres.py [--module ro3] [--decors 0C,28]  -> palettes_libres_<module>.json"""
import sys, os, json, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import image, blocs_tr as BT
P0 = {1: 0x20, 2: 0x40, 3: 0x60}


def utilisees(d, M, dec):
    return {L: {P0[L] + (a & 0x1F) for (c, a) in BT.cases_tilemap(d, M, L, dec).values()} for L in (1, 2, 3)}


def libres(d, M, dec, reloge=True):
    u = utilisees(d, M, dec); out = {}
    for L in (1, 2, 3):
        n = 32 if reloge else BT.palettes_bloc(d, M, L, dec)[1]
        out[L] = [P0[L] + p for p in range(32) if P0[L] + p not in u[L] and p < n and not (L == 3 and p == 31)]
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--module", default="ro3")
    ap.add_argument("--roms", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trav/roms_tr/sfa3ud"))
    ap.add_argument("--decors", default=None)
    a = ap.parse_args()
    d = image.lit(a.roms); M = BT.MOD[a.module]
    decs = [int(x, 16) for x in a.decors.split(",")] if a.decors else list(range(0, 2 * M["ndec"], 2))
    res = {}
    for dec in decs:
        try:
            r = libres(d, M, dec, True); r0 = libres(d, M, dec, False)
        except Exception as e:
            print("decor %02X : %s" % (dec, e)); continue
        res["%02X" % dec] = {"reloge": {"scroll%d" % L: ["%02X" % p for p in r[L]] for L in (1, 2, 3)},
                             "en_place": {"scroll%d" % L: ["%02X" % p for p in r0[L]] for L in (1, 2, 3)}}
        print("decor %02X : relogees s1 %2d s2 %2d s3 %2d | en place s1 %d s2 %d s3 %d   (%s)" % (
            dec, len(r[1]), len(r[2]), len(r[3]), len(r0[1]), len(r0[2]), len(r0[3]),
            ",".join("%02X" % p for L in (1, 2, 3) for p in r[L])))
    json.dump(res, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "palettes_libres_%s.json" % a.module), "w"), indent=1)
