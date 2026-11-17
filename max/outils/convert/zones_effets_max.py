"""(PROPOSITION impacts_max, 16/11 — à verser par la session MAX dans max/outils/convert/) POINTS D'EFFETS posés sur
le corps d'une victime MAX, au format des tables d'Upper 0x74C3F8 / 0x74C498 (pointeur par ID -> bloc de mots (dx, dy)).
Upper : lecteurs image $34624 / $3469C ; objets classe $0A (brûlure du feu : Yoga Flame / Fire, etc.), $3A = ID de la
victime, parent $36 = elle ; mot lu = bloc[(zone << 4) + sous-type (0 / 4) + 8 une image sur deux ($B5 bit 0)], zone =
octet image $10 du pas courant (& $1F pour 0x74C3F8, & 1 pour 0x74C498) ; X = victime ± dx (sens), Y = victime + dy.
PSP : bloc = section 20 de l'entrée [6] du pac plXX (Yun : 15, sections décalées de 5) pour 0x74C3F8, section 21 (Yun :
16) pour 0x74C498. Contrôle : les 31 natifs dont le pac a la disposition commune ont des blocs Upper ÉGAUX octet pour
octet à ces sections (impacts_max/essais/verif_sections.txt ; écarts seulement pour pl0b, pl11, pl13, pl18, pl1c,
dont les sections sont numérotées autrement). MAX : 22 zones (0-21) de 16 o ; section 21 = copie de la section 20.
max59 : les MAX ont le bloc de Ryu (14 zones : zone 14 = données de 0x74C498, au-delà = données étrangères), Maki
celui de la place $27 (Cammy / Juli / Juni). Mesure (banc PSP / Upper, Yoga Flame de Dhalsim, zone 14) : écarts de
25 à 48 px par point ; avec ces blocs : identique à la PSP (±1 px).
Unités : unités de JEU (positions relatives au X / Y du joueur, comme les flammes) -> valeurs telles quelles.
Ordre : MOTS 68K (dc.w) : la ROM 68K lit MOVE.W ; positions des mots inchangées par rapport au pac.
Sortie : <racine SFA3MAX_CACHE>/converti/zones/zones_effets_max.s (ZONES_xx et ZONES2_xx, xx = 26 / 27 / 2D / 2E).
Usage : python zones_effets_max.py"""
import os, sys, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
import paths
# (ID Upper, pac, section 0x74C3F8, section 0x74C498)
PERSOS = [("26", "pl26", 20, 21), ("27", "pl27", 20, 21), ("2D", "pl28", 15, 16), ("2E", "pl29", 20, 21)]


def section(pl, k):
    b = split(open(os.path.join(paths.pac_dir(), "%s_e.pac" % pl), "rb").read())[6][1]
    offs = [v + 0x208 for v in struct.unpack_from("<67I", b, 0)]
    s = sorted(set(o for o in offs if o < len(b)) | {len(b)})
    a = offs[k]; return b[a:min(x for x in s if x > a)]


def bloc(label, d, note):
    w = struct.unpack("<%dh" % (len(d) // 2), d)
    L = ["        even", "%s:            ; %s" % (label, note)]
    for z in range(0, len(w), 8):
        L.append("        dc.w    " + ", ".join("%d" % x for x in w[z:z + 8]) + "    ; zone %d" % (z // 8))
    return L


def main():
    L = ["; points d'effets posés sur le corps d'une victime MAX (Upper 0x74C3F8 / 0x74C498 : 4 points (dx, dy) par zone,",
         ";  16 o par zone, zone = octet image $10 du pas) — sections 20 / 21 de l'entrée [6] (Yun : 15 / 16), 22 zones",
         "; MOTS (dc.w) — généré par convert/zones_effets_max.py", ""]
    for uid, pl, k1, k2 in PERSOS:
        d1, d2 = section(pl, k1), section(pl, k2)
        assert len(d1) == 0x160 and len(d2) == 0x160, (pl, len(d1), len(d2))
        L += bloc("ZONES_%s" % uid, d1, "%s, section %d (0x74C3F8, 22 zones)" % (pl, k1))
        if d2 == d1:      # même bloc pour les deux tables : 2e étiquette à la même adresse (pas d'equ : symboles relus par l'intégration)
            L.insert(len(L) - 22, "ZONES2_%s:           ; %s, section %d = section %d (0x74C498)" % (uid, pl, k2, k1))
        else:
            L += bloc("ZONES2_%s" % uid, d2, "%s, section %d (0x74C498)" % (pl, k2))
    d = os.path.join(paths.CACHE, "converti", "zones"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "zones_effets_max.s"), "w").write("\n".join(L) + "\n")
    print("écrit", os.path.join(d, "zones_effets_max.s"))


if __name__ == "__main__":
    main()
