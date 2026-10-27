"""Constantes et décodage SFA3 MAX (PSP, EU ULES-00235, module ZERO3 chargé en 0x08804000).

Sources : re/connaissances/max_psp.tsv et champs.tsv. ATTENTION : adresse PSP = 0x08804000 + VA pour le CODE (VA < 0x2D4F30),
mais 0x08804000 + 0x2D4F30 + VA pour les DONNÉES/BSS (ex. structures joueur VA 0x80AF70 -> 0x092E3EA0).
Table des joueurs = 0x08804000 + 0x213F88 (code/rodata : pointeurs 32 bits vers les structures joueur, pas de 0x498).
Constats du banc (mesurés, voir PPSSPP-BANC.md) : ID perso = octet +0x152 (Eagle 0x26, Maki 0x27, Ken 0x01),
X = long 16.16 en +0x10, Y = long 16.16 en +0x14 (sol = 40), pointeur du pas d'animation = +0x1C,
octets d'état = +0x04..+0x07, compteur de durée du pas = +0x48, vie = mot +0x70 (max 0x90, figée en entraînement).
"""
import struct

BASE_MODULE = 0x08804000
TABLE_JOUEURS = BASE_MODULE + 0x213F88
TAILLE_JOUEUR = 0x498
# ID PSP (octet +0x152). Mesuré sur l'écran de sélection de l'entraînement : Eagle 0x26, Maki 0x27, Yun 0x28, Ingrid 0x29.
# (les ID Upper des mêmes persos sont $26, $27, $2D, $2E : ne pas confondre)
PERSOS = {0x01: "Ken", 0x26: "Eagle", 0x27: "Maki", 0x28: "Yun", 0x29: "Ingrid"}
ID_PERSO = {"eagle": 0x26, "maki": 0x27, "yun": 0x28, "ingrid": 0x29, "ken": 0x01, "ryu": 0x00}

# Séquence de navigation (images, déterministe) : démarrage -> écran de sélection de l'ENTRAÎNEMENT.
# (boutons, nombre d'images) ; appui = 3 images.
NAV_SELECTION = [("-", 700), ("up", 3), ("-", 30), ("cross", 3), ("-", 120), ("start", 3), ("-", 120),
                 ("-", 200), ("start", 3), ("-", 100), ("start", 3), ("-", 100), ("-", 200), ("start", 3), ("-", 60),
                 ("start", 3), ("-", 60), ("start", 3), ("-", 60), ("down", 3), ("-", 15), ("down", 3), ("-", 15),
                 ("cross", 3), ("-", 90)]
# Depuis la sélection : curseur sur Eagle (droite puis 5 bas), valider J1, J2 (Ken par défaut), lancer ; ~1500 images.
NAV_EAGLE_KEN = [("right", 3), ("-", 12), ("down", 3), ("-", 12), ("down", 3), ("-", 12), ("down", 3), ("-", 12),
                 ("down", 3), ("-", 12), ("down", 3), ("-", 12), ("cross", 3), ("-", 40), ("cross", 3), ("-", 60),
                 ("cross", 3), ("-", 60), ("cross", 3), ("-", 60), ("cross", 3), ("-", 60), ("-", 200),
                 ("cross", 3), ("-", 60), ("-", 300), ("-", 300)]


def adresses_joueurs(banc):
    """Adresses des structures joueur (J1, J2), lues dans la table du jeu."""
    return struct.unpack("<2I", banc.lire(TABLE_JOUEURS, 8))


def decoder(blob):
    """Champs lisibles d'une structure joueur (blob = octets lus à l'adresse du joueur, >= 0x153)."""
    x, y = struct.unpack_from("<ii", blob, 0x10)
    return {
        "id": blob[0x152], "x": x / 65536.0, "y": y / 65536.0, "pas": struct.unpack_from("<I", blob, 0x1C)[0],
        "etat": blob[4:8].hex(), "compteur": struct.unpack_from("<H", blob, 0x48)[0],
        "vie": struct.unpack_from("<H", blob, 0x70)[0], "mot54": struct.unpack_from("<H", blob, 0x54)[0],
    }
