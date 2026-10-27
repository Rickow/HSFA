"""Référence des boîtes de collision PSP d'un perso MAX, pas par pas (2026-10-17, défauts relevés sur console).
Chaîne (vérifiée sur Ryu : 1 033 / 1 059 pas d'Upper ont les octets +8..+19 identiques au jeu de boîtes PSP, les 26 autres
sont des animations retouchées) : pas PSP -> jeu de boîtes de 12 o (section 7 de [6], recopié tel quel dans le pas 68K,
octets +8..+19) -> octet 0 = index dans la table $88 (section 13, 4 o par entrée) -> index des boîtes $90 / $94 / $98 /
$9C (sections 8-11, 4 × s16 par boîte) ; l'attaque éventuelle : table $A0 (section 12). Les boîtes sont rattachées au PAS,
pas à la frame : la fusion haut + bas des frames d'Ingrid ne les touche pas ; coordonnées relatives à l'origine du perso.
Sortie : ~/.cache/sfa3max/converti/plXX/boites_reference.txt (une ligne par pas : table, n°, pas, durée, frame, étiquette
P%02X_x du pas dans anims_XX.s, 12 octets, entrée $88 et boîtes décodées).
Usage : python boites_max.py pl29 [table n]"""
import os, sys, json, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
import paths
C = os.path.expanduser("~/.cache/sfa3max/converti")


def main(pl, filtre=None):
    b6 = split(open(os.path.join(paths.pac_dir(), "%s_e.pac" % pl), "rb").read())[6][1]
    Hs = [v + 0x208 for v in struct.unpack_from("<67I", b6, 0)]
    def section(s):
        lo = Hs[s]; hi = min([x for x in Hs if x > lo] + [len(b6)]); return b6[lo:hi]
    t88 = section(13); bt = {k: section(s) for k, s in (("$90", 8), ("$94", 9), ("$98", 10), ("$9C", 11))}
    boite = lambda k, i: struct.unpack_from("<4h", bt[k], 8 * i) if 8 * i + 8 <= len(bt[k]) else None
    A = json.load(open(os.path.join(C, pl, "animations.json"))); cid = int(pl[2:], 16); out = []
    for t in ("$2B0", "$2B4", "$2B8", "$2BC"):
        for x in A[t]:
            if filtre and (t, x["n"]) != filtre: continue
            for k, st in enumerate(x["steps"] or []):
                if st["A"] is None: continue
                ps = struct.pack("<3I", st["A"], st["B"], st["C"]); i88 = ps[0]
                e = t88[4 * i88:4 * i88 + 4] if 4 * i88 + 4 <= len(t88) else b""
                bx = ["%s#%d=%s" % (nom, j, boite(nom, j)) for nom, j in zip(("$90", "$94", "$98", "$9C"), e) if j]
                lab = "P%02X_%x" % (cid, x.get("pas_psp", 0) + (k if "pas_psp" in x else 0))
                out.append("%s n°%d pas %d : durée %d frame F%02X_%d %s | %s | $88[%d] = %s | %s" % (
                    t, x["n"], k, st["ctl"] & 0xFF, cid, st["frame"], lab, ps.hex(" "), i88, list(e), " ".join(bx) or "aucune boîte"))
    f = os.path.join(C, pl, "boites_reference.txt"); open(f, "w").write("\n".join(out) + "\n")
    return f, len(out)


if __name__ == "__main__":
    pl = sys.argv[1] if len(sys.argv) > 1 else "pl29"
    filtre = (sys.argv[2], int(sys.argv[3])) if len(sys.argv) > 3 else None
    f, n = main(pl, filtre); print(f, n, "pas")
