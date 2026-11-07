"""Tables de physique des persos MAX lues dans l'EBOOT (2026-11-07, script_uppermax ; remplace les commandes ponctuelles
du 07/10 qui avaient produit donnees_sauts_max.s et physique_max_arcade.json).
PSP (image = EBOOT + 0x74, entrées $00-$29) :
  - sauts : 3 tables (une par ism) 0x21C3BE / 0x21C8FE / 0x21CE3E, 32 o par perso = 4 fiches {vx, vy, ax, ay} en mots
    8.8 signés ;
  - marche : 3 tables 0x21C1C6 / 0x21C26E / 0x21C316 (juste avant), 4 o par perso = 2 mots (recul, avance).
Sorties (dans ce dossier) :
  - donnees_sauts_max.s : les 3 tables de sauts recopiées en gros-boutiste (TAB_SAUT_PSP_A/B/C), pour le code MAX qui
    les lit au format PSP (champ 0x2C4 -> $34A) ;
  - physique_max_arcade.json : entrées $26-$29 au format arcade (longs 16.16 = mot PSP << 8) des tables de sauts
    $DD792 / $DDF92 / $DE792 et de marche $DD492 / $DD592 / $DD692 (rang de la table PSP = rang de la table arcade ;
    les valeurs des 3 ism sont identiques pour les persos MAX).
Usage : python3 sauts_max.py"""
import os, sys, json, struct
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "tools", "max"))
from relocs import img

SAUTS = (0x21C3BE, 0x21C8FE, 0x21CE3E)
MARCHE = (0x21C1C6, 0x21C26E, 0x21C316)
CLES_SAUTS = ("$DD792 (saut, $132=0)", "$DDF92 (saut, $132 autre)", "$DE792 (saut, $132=$FF)")
CLES_MARCHE = ("$DD492 (marche, $132=0)", "$DD592 (marche, $132 autre)", "$DD692 (marche, $132=$FF)")


def source_sauts():
    L = ["; Tables de physique PSP (sauts, 32 o par perso : 4 fiches {vx,vy,ax,ay} en mots 8.8) recopiées en gros-boutiste",
         "; pour le code MAX qui les lit au format PSP (Eagle : champ 0x2C4 -> $34A) — 2026-10-07. Arcade équivalent : $2D4(A6)",
         "; -> $DD792 / $DDF92 / $DE792 (longs 16.16 = mot PSP << 8, 64 o par perso)."]
    for lettre, a in zip("ABC", SAUTS):
        L.append("TAB_SAUT_PSP_%s:   ; PSP %#x, entrées $00-$29" % (lettre, a))
        for i in range(0x2A):
            L.append("        dc.w    %s   ; $%02x" % (", ".join("$%04x" % x for x in struct.unpack_from("<16H", img, a + 32 * i)), i))
    return "\n".join(L) + "\n"


def physique():
    arc = lambda v: "%08X" % ((v << 8) & 0xFFFFFFFF)
    J = {}
    for cle, a in zip(CLES_SAUTS, SAUTS):
        J[cle] = {"%x" % i: [arc(x) for x in struct.unpack_from("<16h", img, a + 32 * i)] for i in range(0x26, 0x2A)}
    for cle, a in zip(CLES_MARCHE, MARCHE):
        J[cle] = {"%x" % i: [arc(x) for x in struct.unpack_from("<2h", img, a + 4 * i)] for i in range(0x26, 0x2A)}
    return J


if __name__ == "__main__":
    open(os.path.join(ICI, "donnees_sauts_max.s"), "w").write(source_sauts())
    json.dump(physique(), open(os.path.join(ICI, "physique_max_arcade.json"), "w"), indent=1)
    print("donnees_sauts_max.s (3 tables × 42) ; physique_max_arcade.json ($26-$29)")
