#!/usr/bin/env python3
"""(etape B) BILAN DU JOURNAL DES TALONS (journal_conv.lua de l'etape A) pour un dossier de construction :
  bilan_journal.py <dossier> journal1.txt [journal2.txt ...]
Par talon (donnees $400.., code $3FF000..) : appels, valeurs de CODE PS2 vues (cle de la table de hachage dans la plage
du code PS2), conversions de code faites ; sites qui voient encore du code PS2 (site = JSR qui appelle le talon)."""
import sys, os, struct, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image import image
W = sys.argv[1]
import glob
IMG = image(glob.glob(os.path.join(W, "roms_*", "sfa3ud"))[0])
CARTE = []
for l in open(os.path.join(W, "carte_image.txt")):
    a, va, mn = l.rstrip("\n").split(" ", 2); CARTE.append((int(a, 16), int(va, 16), mn))
CK = [c[0] for c in CARTE]
def carte(a):
    if a < 0x1000: return "noyau68k"
    k = bisect.bisect_right(CK, a) - 1
    return ("%07x %s" % (CARTE[k][1], CARTE[k][2])) if k >= 0 else "?"
CODE_LO, CODE_HI = struct.unpack_from(">I", IMG, 0x3FF004)[0], struct.unpack_from(">I", IMG, 0x3FF00E)[0]
HASH = {}
for i in range(1 << 14):
    k, v = struct.unpack_from(">II", IMG, 0x3C0000 + 8 * i)
    if k: HASH[k] = v
def site_of(pc):
    if pc >= 4 and struct.unpack_from(">H", IMG, pc - 4)[0] == 0x4EB8: return pc - 4
    if pc >= 6 and struct.unpack_from(">H", IMG, pc - 6)[0] == 0x4EB9: return pc - 6
    return pc
RAMPS2 = range(0x900000, 0x910000)
tot = collections.Counter(); sites = collections.Counter(); sitesps2 = collections.Counter(); nimg = 0
for j in sys.argv[2:]:
    for l in open(j):
        if l.startswith("#"): nimg += int(l.split()[2]); continue
        _, pc, talon, v, a, f, w1, w2, n = l.split()
        pc, talon, v, n = int(pc, 16), int(talon), int(v, 16), int(n)
        cl = "code" if talon >= 10 else "donnees"
        ps2 = CODE_LO <= v < CODE_HI and v in HASH
        tot[cl, "appels"] += n
        if ps2: tot[cl, "code PS2"] += n
        if ps2 and v >= 0x3C0000: tot[cl, "code PS2 certain"] += n      # au-dela des donnees ROM 68K : pas ambigu
        if talon < 10 and v in RAMPS2: tot[cl, "RAM PS2"] += n
        s = site_of(pc); sites[cl, s] += n
        if ps2: sitesps2[cl, s] += n
print("images %d (%s)" % (nimg, ", ".join(os.path.basename(x) for x in sys.argv[2:])))
for cl in ("donnees", "code"):
    print("  talons de %-7s : %9d appels, %9d avec une adresse de code PS2 (dont %d >= $3C0000, hors chevauchement avec les"
          " donnees ROM 68K), %d avec RAM PS2 ; %d sites actifs, %d avec code PS2" % (cl, tot[cl, "appels"], tot[cl, "code PS2"],
          tot[cl, "code PS2 certain"], tot[cl, "RAM PS2"], sum(1 for k in sites if k[0] == cl), sum(1 for k in sitesps2 if k[0] == cl)))
print("sites qui voient encore une adresse de code PS2 :")
for (cl, s), n in sitesps2.most_common():
    print("  %-7s $%06x %9d / %9d  %s" % (cl, s, n, sites[cl, s], carte(s)[:110]))
