"""Ancrages des FLAMMES sur une victime MAX (projectile enflammé), au format de la table d'Upper 0x74C358 (2026-10-24).
Upper : table par ID de la victime -> 16 couples d'octets signés, index = octet +$11 du pas courant & $F (arcade 0x80B3C :
move.b $11(a2) / andi.w #$f, table $DF692[ID]) ; position = victime + (±dx selon le sens, dy). PSP : FUN_00079A58, index =
octet +9 du jeu de boîtes courant de la victime (+0x128 ; = octet +$11 du pas 68K), SANS masque ; couples dans la section
15 de l'entrée [6] du pac plXX (section 10 chez Yun, dont les sections sont décalées de 5), à +0x208 du répertoire, EN
ORDRE IMAGE (octets identiques à ceux d'Upper : contrôlé sur Ryu 14/14 couples, Chun-Li et Sagat 12-14, Zangief 16/16 ;
Upper a ajouté des couples au-delà de la fin PSP). Les persos MAX ont 22 couples et des index jusqu'à 21 (Eagle et Yun ;
Maki et Ingrid 17) : les 22 sont gardés, le & $F d'Upper les replierait (16 -> 0, 21 -> 5). Natifs : index ≤ 16.
Unités : unités de JEU (la position de la flamme suit le X de la victime ; l'étirement ×19/16 n'agit qu'au dessin du
sprite) -> valeurs telles quelles.
Sortie : <racine SFA3MAX_CACHE>/converti/flammes/flammes_max.s (FLAMMES_26 / 27 / 2D / 2E, 44 o, ORDRE IMAGE).
Usage : python flammes_max.py"""
import os, sys, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
import paths
PERSOS = [("26", "pl26", 15), ("27", "pl27", 15), ("2D", "pl28", 10), ("2E", "pl29", 15)]


def section(pl, k):
    b = split(open(os.path.join(paths.pac_dir(), "%s_e.pac" % pl), "rb").read())[6][1]
    offs = [v + 0x208 for v in struct.unpack_from("<67I", b, 0)]
    s = sorted(set(o for o in offs if o < len(b)) | {len(b)})
    a = offs[k]; return b[a:min(x for x in s if x > a)]


def main():
    L = ["; ancrages des flammes sur une victime MAX (Upper 0x74C358 : 16 couples, index = octet +$11 du pas & $F ;",
         ";  PSP FUN_00079A58 : même octet SANS masque, index MAX jusqu'à 21 -> 22 couples)",
         "; ORDRE IMAGE (octets tels quels dans l'image d'Upper = ceux du pac PSP) — généré par convert/flammes_max.py", ""]
    for uid, pl, k in PERSOS:
        d = section(pl, k); assert len(d) == 44, (pl, len(d))
        L += ["        even", "FLAMMES_%s:            ; %s, section %d de l'entrée [6] (%d couples, index 0-%d)" % (uid, pl, k, len(d) // 2, len(d) // 2 - 1)]
        L += ["        dc.b    " + ", ".join("$%02x" % x for x in d[i:i + 16]) for i in range(0, len(d), 16)]
    d = os.path.join(paths.CACHE, "converti", "flammes"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "flammes_max.s"), "w").write("\n".join(L) + "\n")
    print("écrit", os.path.join(d, "flammes_max.s"))


if __name__ == "__main__":
    main()
