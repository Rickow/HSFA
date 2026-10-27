#!/usr/bin/env python3
"""donnees_decor.py : tables par decor (index $100 = decor x 2) d'Upper (ro5, 40 entrees) et d'Hyper (ro9, 4 entrees,
16 avec la variante $C178) ; pour chaque decor d'Upper, bloc de donnees vise (decalage mot relatif a la table) et
presence de ce bloc dans le module Hyper (recherche d'octets) -> donnees_decor.tsv + resume a l'ecran.
Adresses d'execution (= fichier + 0x1F0000)."""
import os, struct, collections
DIR = "<workspace>/anthology_extract/decompressed"; BASE = 0x1F0000
B = {m: open(os.path.join(DIR, "%s_usa_prog68k.bin" % m), "rb").read() for m in ("ro3", "ro5", "ro9")}
H = os.path.dirname(os.path.abspath(__file__))
def w(m, a): return struct.unpack_from('<h', B[m], a - BASE)[0]
def W(m, a): return struct.unpack_from('<H', B[m], a - BASE)[0]
# (nom, table Upper, table Hyper, nb entrees Hyper, taille max d'un bloc, pas d'index Hyper)
TABLES = [
    ("palettes scroll1 (32 x 32 o)", 0x70E560, 0x660240, 16, 0x400),
    ("palettes scroll2", 0x7147E0, 0x661E60, 16, 0x400),
    ("palettes scroll3 (31 pal.)", 0x71D420, 0x664280, 16, 0x400),
    ("palettes sprites de decor ($90C1E0, 6 pal.)", 0x707D10, None, 0, 0xC0),
    ("listes scroll1", 0x747F30, 0x695FF8, 4, 0x80),
    ("listes scroll2", 0x7480D4, 0x696010, 4, 0x80),
    ("listes scroll3", 0x748344, 0x696048, 4, 0x80),
    ("objet par decor ($105C70)", 0x740B70, None, 0, 0x200),
    ("animations objets de decor ($FDC10)", 0x971E70, None, 0, 0x200),
    ("palettes par decor (anim. $1E4530 ?) $950CE0", 0x950CE0, None, 0, 0x100),
]
def blocs(m, T, n, cap):
    off = [w(m, T + 2 * k) for k in range(n)]
    st = sorted(set(off))
    res = []
    for k, o in enumerate(off):
        nxt = [x for x in st if x > o]
        size = min((nxt[0] - o) if nxt else cap, cap)
        res.append((o, T + o, size))
    return res
out = open(os.path.join(H, "donnees_decor.tsv"), "w")
out.write("table\tdecor\tadr_upper\ttaille\talias_de\tdans_hyper\tdans_sfa3\n")
for nom, T5, T9, n9, cap in TABLES:
    bl = blocs("ro5", T5, 40, cap)
    vu = {}; pres = 0; pres3 = 0; distincts = 0
    for k, (o, a, s) in enumerate(bl):
        d = k * 2
        al = vu.get(a)
        blob = B["ro5"][a - BASE:a - BASE + s]
        f9 = B["ro9"].find(blob) if s >= 8 else -1
        f3 = B["ro3"].find(blob) if s >= 8 else -1
        if al is None:
            vu[a] = d; distincts += 1
            pres += f9 >= 0; pres3 += f3 >= 0
        out.write("%s\t$%02X\t%x\t%d\t%s\t%s\t%s\n" % (nom, d, a, s, ("$%02X" % al) if al is not None else "",
                  ("%x" % (f9 + BASE)) if f9 >= 0 else "-", ("%x" % (f3 + BASE)) if f3 >= 0 else "-"))
    print("%-45s Upper %x : %d blocs distincts / 40 ; dans Hyper : %d ; (dans SFA3 : %d)" % (nom, T5, distincts, pres, pres3))
    if T9:
        b9 = blocs("ro9", T9, n9, cap)
        s9 = sorted(set(a for _, a, _ in b9))
        info = []
        for a in s9:
            s = next(x for _, y, x in b9 if y == a)
            blob = B["ro9"][a - BASE:a - BASE + s]
            f5 = B["ro5"].find(blob); f3 = B["ro3"].find(blob)
            info.append("%x(%d o)%s%s" % (a, s, " =Upper %x" % (f5 + BASE) if f5 >= 0 else "", " =SFA3 %x" % (f3 + BASE) if f3 >= 0 else ""))
        print("   Hyper %x : %d entrees, %d blocs distincts : %s" % (T9, n9, len(s9), "; ".join(info)))
out.close()
