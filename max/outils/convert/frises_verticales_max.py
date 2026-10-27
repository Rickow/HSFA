"""Colonnes VERTICALES « 1P nom 1P nom… » de l'écran de sélection d'Upper pour les 4 persos MAX (2026-10-24, lot 2b21 :
« EAGLE 1P EAGLE… » à l'horizontale en haut de l'écran, alors que « 2P RYU » est une colonne).
Upper (ro5, adresses PS2) : les colonnes de la sélection ne viennent PAS des frises horizontales (type $0C, tables
0x9620B8-0x962478, voir bandeau_noms_max.py) mais de 4 tables {u32 attr, u32 frame} × 40 ID qui les suivent : 1P JP
0x9625B8, 1P US 0x9626F8, 2P JP 0x962838, 2P US 0x962978. Frame de type $0A : u16 $0A, u16 T, u16 n−1, u16 attr ($001C),
[mot 0 d'alignement], u32 positions, n × u16 code ; un objet = UNE lettre de la police (code = ASCII | $80 : « 1 » $B1,
« P » $D0, « R » $D2…), motif « 1P » + nom répété, phase et table de positions selon la longueur du motif (« 1PRYU »
5 lettres : T 20, 0x966058 ; « 1PAKUMA » 7 : T 23, 0x9660A8…). Aucun graphisme nouveau : lettres de la police d'Upper.
Pour chaque perso MAX : frame recopiée du natif dont le motif a la même longueur et que des lettres pleines (pas de « . » ni
de « & », qui ont leurs propres positions), lettres du nom substituées à la même phase ; attr de table = celui du natif
avec le bit $4000 des ID ajoutés par Upper (comme les entrées $26 / $27 d'origine).
Sortie : <racine SFA3MAX_CACHE>/converti/bandeau_noms/frises_verticales_max.s (MAXBV_xx_1P / _2P + entrées des 4 tables,
DISPOSITION IMAGE : mots tels quels, longs à moitiés échangées).
Usage : python frises_verticales_max.py"""
import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
RO5 = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro5_usa_prog68k.bin")
RB = 0x1F0000
TABLES = {("1P", "JP"): 0x9625B8, ("1P", "US"): 0x9626F8, ("2P", "JP"): 0x962838, ("2P", "US"): 0x962978}
# perso MAX -> (ID Upper, nom, ID du natif modèle (table US) : même longueur de motif, lettres pleines)
MAX = [(0x26, "EAGLE", 0x02), (0x27, "MAKI", 0x09), (0x2D, "YUN", 0x00), (0x2E, "INGRID", 0x08)]
B = open(RO5, "rb").read()
L = lambda a: (lambda w0, w1: (w1 << 16) | w0)(*struct.unpack_from("<HH", B, a - RB))


def frame(p):
    o = p - RB; t, T, n1, at = struct.unpack_from("<HHHH", B, o); assert t == 0x0A
    q = o + 8 + (2 if (o + 8) % 4 else 0)
    return {"T": T, "n": n1 + 1, "attr": at, "positions": struct.unpack_from("<I", B, q)[0],
            "codes": list(struct.unpack_from("<%dH" % (n1 + 1), B, q + 4))}


def texte(codes): return "".join(chr(c & 0x7F) for c in codes)


def main():
    sw = lambda v: "$%08X" % (((v & 0xFFFF) << 16) | (v >> 16))
    out = ["; colonnes verticales « 1P / 2P nom » de la sélection, persos MAX (tables 1P JP 0x9625B8, 1P US 0x9626F8,",
           "; 2P JP 0x962838, 2P US 0x962978 ; frames $0A : une lettre de la police par objet, code = ASCII | $80)",
           "; généré par convert/frises_verticales_max.py — DISPOSITION IMAGE (longs à moitiés échangées)", ""]
    entrees = []
    for uid, nom, mod in MAX:
        for j in ("1P", "2P"):
            T_ = TABLES[(j, "US")]; at = L(T_ + 8 * mod); f = frame(L(T_ + 8 * mod + 4))
            s = texte(f["codes"]); motif_mod = j + s.split(j)[1]
            assert len(motif_mod) == len(j + nom) and motif_mod.replace(j, "").isalpha(), (nom, motif_mod)
            phase = s.index(j)                                   # position du 1er « 1P » dans la chaîne du modèle
            motif = j + nom; k0 = (len(motif) - phase) % len(motif)
            neuf = "".join(motif[(k0 + i) % len(motif)] for i in range(len(s)))
            assert [i for i in range(len(s)) if s.startswith(j, i)] == [i for i in range(len(neuf)) if neuf.startswith(j, i)], (s, neuf)
            codes = [0x80 | ord(c) for c in neuf]
            lab = "MAXBV_%02X_%s" % (uid, j)
            out += ["        cnop    0,4", "%s:                ; %s (modèle : ID $%02X « %s »)" % (lab, neuf, mod, s),
                    "        dc.w    $000A, %d, %d, $%04X" % (f["T"], f["n"] - 1, f["attr"]),
                    "        dc.l    %s" % sw(f["positions"])]
            out += ["        dc.w    " + ", ".join("$%04X" % c for c in codes[i:i + 12]) for i in range(0, len(codes), 12)]
            for t in ("JP", "US"): entrees.append((j, t, uid, at | 0x4000, lab))
    out += ["", "; entrées des tables par ID (u32 attr, u32 frame), disposition image ; à poser aux ID $26 / $27 / $2D / $2E"]
    for j, t, uid, at, lab in entrees:
        out += ["MAXBV_E_%s_%s_%02X:   ; table %s %s ($%X), ID $%02X" % (j, t, uid, j, t, TABLES[(j, t)], uid),
                "        dc.l    %s" % sw(at), "        dc.w    (%s)&$ffff, (%s)>>16" % (lab, lab)]
    d = os.path.join(paths.CACHE, "converti", "bandeau_noms"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "frises_verticales_max.s"), "w").write("\n".join(out) + "\n")
    print("écrit", os.path.join(d, "frises_verticales_max.s"))


if __name__ == "__main__":
    main()
