#!/usr/bin/env python3
"""compare deux constructions Upper MAX (bases décalées) hors du code d'Upper : code MAX de l'image
($3A0000+), talons, données, ext_*.bin. Tout octet différent doit appartenir à un pointeur 32 bits (gros-boutiste, ou
moitiés échangées) dont les valeurs A et B désignent la MÊME va MIPS dans les cartes des deux constructions.
Usage : equiv_pointeurs.py maxA maxB [décalage des données, hex]  -> compte des pointeurs relogés reconnus, et liste des
différences INEXPLIQUÉES. Décalage D (ex. 2000) : la base des données de B est D plus haut (le code a franchi une page) ;
la zone [fin du code, $3A0000) de A est alors comparée à celle de B décalée de D, et un pointeur vers cette zone doit
valoir D de plus dans B."""
import sys, os, glob, struct
PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
def image(d):
    b = bytearray()
    for n in PRG: b += open(os.path.join(d, "roms_ro5", "sfa3ud", n), "rb").read()
    b[0::2], b[1::2] = b[1::2], b[0::2]; return bytes(b)
def carte(d):
    m = {}; fin = 0
    for l in open(os.path.join(d, "carte_image.txt"), encoding="utf-8", errors="replace"):
        c = l.split()
        try: o, v = int(c[0], 16), int(c[1], 16)
        except (ValueError, IndexError): continue
        m.setdefault(o, set()).add(v); fin = max(fin, o)
    return m, fin
A, B = sys.argv[1:3]; DEC = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0; HAUT = 0x3A0000
cA, fA = carte(A); cB, fB = carte(B); iA, iB = image(A), image(B)
def couvert(c, f):
    cv = bytearray(f + 2)
    L = sorted(c)
    for i, o in enumerate(L[:-1]):
        n = L[i + 1]
        if n - o <= 64: cv[o:n] = b"\1" * (n - o)
    return cv
cvA = couvert(cA, fA)
def explique(x, y, d):
    """un pointeur 32 bits contenant l'octet d, dont les valeurs A / B ont la même va ? -> (début, forme) ou None"""
    for s in range(d - 3, d + 1):
        if s < 0 or s + 4 > len(x): continue
        for forme, dec in (("be", lambda t: struct.unpack(">I", t)[0]), ("moities", lambda t: struct.unpack(">I", t[2:] + t[:2])[0])):
            va, vb = dec(x[s:s + 4]) & 0xFFFFFF, dec(y[s:s + 4]) & 0xFFFFFF
            if va == vb: continue
            if DEC and vb == va + DEC and DBA <= va < HAUT - DEC: return s, forme + '+D'
            for k in (0, 2, 4, 6):          # pointeur vers le milieu d'une instruction : même va, même écart
                if va - k in cA and vb - k in cB and cA[va - k] & cB[vb - k]: return s, forme + ("+%d" % k if k else "")
    return None
def compare(nom, x, y, saute=None, org=0):
    if len(x) != len(y): print("TAILLE %s : %d / %d" % (nom, len(x), len(y)))
    n = min(len(x), len(y)); ok = 0; ko = []; d = 0; vu = -1
    while d < n:
        if x[d] != y[d] and d > vu and not (saute and d < len(saute) and saute[d]):
            e = explique(x, y, d)
            if e: ok += 1; vu = e[0] + 3
            else: ko.append(d)
        d += 1
    print("%-16s pointeurs relogés reconnus %5d ; octets différents INEXPLIQUÉS %d" % (nom, ok, len(ko)))
    i = 0
    while i < len(ko) and i < 400:
        j = i
        while j + 1 < len(ko) and ko[j + 1] - ko[j] <= 4: j += 1
        print("   INEXPLIQUÉ %s $%06X-$%06X : A %s | B %s" % (nom, org + ko[i], org + ko[j], x[ko[i]:ko[j] + 1].hex()[:40], y[ko[i]:ko[j] + 1].hex()[:40])); i = j + 1
    return len(ko)
# image : hors du code d'Upper (couvert par la carte de A ; le code d'Upper décalé est l'affaire de equiv_integration.py)
debut = (max(fA, fB) + 0x400) & ~0xFF
DBA = (fA + 0xFFF) & ~0xFFF                      # base des données de A (page suivant la fin du code, talon compris)
print("# image comparée à partir de $%X (fin du code d'Upper : A $%X, B $%X)" % (debut, fA, fB))
if DEC:
    d0 = ((fA + 0x400) & ~0xFF)
    print("# données décalées de $%X : A [$%X, $%X) contre B [$%X, $%X) ; puis $%X et au-delà sans décalage" % (DEC, d0, HAUT - DEC, d0 + DEC, HAUT, HAUT))
    t = compare("image (données)", iA[d0:HAUT - DEC], iB[d0 + DEC:HAUT], org=d0)
    t += compare("image (MAX)", iA[HAUT:], iB[HAUT:], org=HAUT)
else:
    t = compare("image", iA[debut:], iB[debut:], org=debut)
for f in sorted(glob.glob(os.path.join(A, "ext_*.bin")) + glob.glob(os.path.join(A, "max_plus_gfx.bin"))):
    g = os.path.join(B, os.path.basename(f))
    x, y = open(f, "rb").read(), open(g, "rb").read()
    if x == y: print("%-16s identique" % os.path.basename(f)); continue
    t += compare(os.path.basename(f), x, y)
print("# total inexpliqué : %d" % t)
