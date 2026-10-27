"""Table de RECUL des types de réaction 28-32 (coups MAX), au format d'Upper (2026-10-24, demande de l'agent d'intégration).
Upper : l'octet +9 de la fiche d'attaque va dans $57 de la victime (arcade 0x2331E) ; le recul (arcade 0x2B5CC, Upper
0x52DC8) lit T[$57 × 2 + D6] (arcade $2D0CC, 27 entrées ; Upper 0x61B460, 28 entrées) -> n° de séquence -> tables rel16
(arcade $2D102 / $2D402 selon $26C ; Upper 0x9719C0 / 0x971CC0) -> pas de recul s8 par image, fin au premier octet < 0.
PSP : FUN_0005FE1C, T = 0x214D04 (33 entrées, 0-32 ; victime +0x77), séquences par pointeurs 0x214C8C / 0x214EC4 (+0x24C),
30 séquences chacune. Types 0-27 identiques à Upper ; 28-32 -> séquences 25-29 (mêmes pointeurs dans les deux tables).
Séquences 0-24 : identiques octet pour octet à Upper dans les deux tables, sauf A11 (Upper ajoute une image à 0).
Disposition d'Upper (vérifiée sur les 50 séquences) : octets tels quels, chaque séquence complétée par $FF à une longueur
paire. Types > 26 employés par les fiches MAX (section 12 de [6], 32 o, octet +9 ; section 7 chez Yun) : Eagle 27/30/31,
Yun 28/29, Ingrid 27/32, Maki aucun (≤ 9) ; aucun type 33.
Sortie : <racine SFA3MAX_CACHE>/converti/recul/recul_max.s (RECUL_TYPES : 33 × 2 o ; RECUL_S25-S29, ORDRE IMAGE).
Usage : python recul_max.py"""
import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
VA = 0x74                                               # décalage fichier de .text / .data dans l'EBOOT déchiffré
T_PSP, SEQ_A, SEQ_B, N_T, N_S = 0x214D04, 0x214C8C, 0x214EC4, 33, 30
T_UP, SEQ_UP_A, SEQ_UP_B, RB = 0x61B460, 0x9719C0, 0x971CC0, 0x1F0000


def sequence(e, p):
    o, s = p + VA, bytearray()
    while True:
        s.append(e[o]); o += 1
        if e[o - 1] >= 0x80: return bytes(s)


def controle(e):
    ro5 = open(os.path.join(paths.anthology(), "decompressed", "ro5_usa_prog68k.bin"), "rb").read()
    t = e[T_PSP + VA:T_PSP + VA + 2 * N_T]
    assert ro5[T_UP - RB:T_UP - RB + 56] == t[:56], "types 0-27 : PSP ≠ Upper"
    ecarts = []
    for tp, tu in ((SEQ_A, SEQ_UP_A), (SEQ_B, SEQ_UP_B)):
        P = struct.unpack_from("<%dI" % N_S, e, tp + VA); R = struct.unpack_from("<25h", ro5, tu - RB)
        for k in range(25):
            s = sequence(e, P[k]); a = tu + R[k] - RB
            if ro5[a:a + len(s)] != s: ecarts.append("%s%d" % ("AB"[tp == SEQ_B], k))
    return ecarts


def main():
    e = open(paths.eboot(), "rb").read()
    ecarts = controle(e)
    t = e[T_PSP + VA:T_PSP + VA + 2 * N_T]
    PA = struct.unpack_from("<%dI" % N_S, e, SEQ_A + VA); PB = struct.unpack_from("<%dI" % N_S, e, SEQ_B + VA)
    assert PA[25:] == PB[25:]
    L = ["; recul des types de réaction 28-32 (table Upper 0x61B460, séquences 0x9719C0 / 0x971CC0) — convert/recul_max.py",
         "; ORDRE IMAGE (octets tels quels, comme les séquences 0-24 d'Upper) ; PSP FUN_0005FE1C, T 0x214D04",
         "; types 0-27 = Upper ; séquences 0-24 = Upper sauf %s" % (", ".join(ecarts) or "aucune"), "",
         "        even", "RECUL_TYPES:            ; 33 types × (n° de séquence pour D6 = 0, D6 = 1)"]
    L += ["        dc.b    " + ", ".join("$%02x" % x for x in t[i:i + 16]) for i in range(0, len(t), 16)]
    L += ["; entrées 25-29 des DEUX tables rel16 -> RECUL_S25-S29 (la PSP emploie les mêmes séquences pour $26C = 0 et ≠ 0)"]
    for k in range(25, N_S):
        s = sequence(e, PA[k]); s += b"\xff" * (len(s) % 2)
        L += ["        even", "RECUL_S%d:               ; types %s, %d images" % (k, [i for i in range(N_T) if k in t[2 * i:2 * i + 2]], len(s.rstrip(b"\xff")))]
        L += ["        dc.b    " + ", ".join("$%02x" % x for x in s[i:i + 16]) for i in range(0, len(s), 16)]
    d = os.path.join(paths.CACHE, "converti", "recul"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "recul_max.s"), "w").write("\n".join(L) + "\n")
    print("écrit", os.path.join(d, "recul_max.s"), "; écarts PSP/Upper sur 0-24 :", ecarts or "aucun")


if __name__ == "__main__":
    main()
