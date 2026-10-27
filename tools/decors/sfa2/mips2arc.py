"""Correspondance MIPS (colonne 2 de carte_image.txt = décalage fichier ; exéc. = +0x1F0000) -> adresse arcade SFA3
d'après scripts/untranspile/map_ro3_sfa3.json (blocs colinéaires, points d'appui). Lecture seule."""
import json, bisect
M = json.load(open("<workspace>/scripts/untranspile/map_ro3_sfa3.json"))
PTS = sorted(p for b in M["blocks"] for p in b["points"])
XS = [p[0] for p in PTS]
def arc(fichier):
    e = fichier + 0x1F0000
    i = bisect.bisect_right(XS, e) - 1
    if i < 0: return None
    m, a = PTS[i]
    return a, e - m          # adresse arcade du point d'appui précédent, distance MIPS
if __name__ == "__main__":
    import sys
    for x in sys.argv[1:]:
        r = arc(int(x, 16)); print(x, "-> arcade $%05X (+%d o MIPS)" % r if r else None)
