#!/usr/bin/env python3
"""preuve mécanique que l'intégration MAX pose les MÊMES modifications sur deux bases d'Upper dont le
code est décalé (v160 / v161) : pour chaque va MIPS de la carte, « l'intégration a-t-elle changé cette instruction ? »
doit avoir la même réponse sur A et sur B ; hors carte (données, talons), les plages modifiées sont comparées par adresse.
Usage : equiv_integration.py baseA maxA baseB maxB   (dossiers avec carte_image.txt et roms_ro5/sfa3ud)
Sortie : sites modifiés d'un seul côté (= dépendance à une adresse), et sites modifiés des deux côtés dont les octets
diffèrent (à lire : adresses relogées attendues)."""
import sys, os
PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
def image(d):
    b = bytearray()
    for n in PRG: b += open(os.path.join(d, "roms_ro5", "sfa3ud", n), "rb").read()
    b[0::2], b[1::2] = b[1::2], b[0::2]; return bytes(b)
def carte(d):
    """liste (adresse image, va) dans l'ordre du fichier ; plusieurs lignes par va possibles"""
    L = []
    for l in open(os.path.join(d, "carte_image.txt"), encoding="utf-8", errors="replace"):
        c = l.split()
        try: L.append((int(c[0], 16), int(c[1], 16)))
        except (ValueError, IndexError): pass
    return L
def par_va(d):
    """va -> octets de toutes les instructions 68K issues de cette va (concaténés), et plage couverte"""
    img = image(d); L = carte(d); r = {}; couv = []
    for i, (o, v) in enumerate(L):
        f = L[i + 1][0] if i + 1 < len(L) else o
        if f < o or f - o > 64: f = o + 2
        r.setdefault(v, []).append((o, img[o:f])); couv.append((o, f))
    return img, r, couv
bA, mA, bB, mB = [par_va(d) for d in sys.argv[1:5]]
def modifs(b, m):
    """va -> (octets base, octets max, adresse max) pour les va dont les octets changent ; va absentes d'un côté"""
    r = {}
    for v in set(b[1]) | set(m[1]):
        x = b"".join(t for _, t in b[1].get(v, [])); y = b"".join(t for _, t in m[1].get(v, []))
        if x != y: r[v] = (x, y, m[1][v][0][0] if v in m[1] else -1)
    return r
dA = modifs(bA, mA); dB = modifs(bB, mB)
print("# va modifiées par l'intégration : A %d, B %d" % (len(dA), len(dB)))
seul = 0
for v in sorted(set(dA) ^ set(dB)):
    c, n = (dA, "A") if v in dA else (dB, "B"); x, y, o = c[v]; seul += 1
    print("SEUL %s  va 0x%06X  image max $%06X : %s -> %s" % (n, v, o, x.hex()[:48], y.hex()[:48]))
dif = 0
for v in sorted(set(dA) & set(dB)):
    if dA[v][1] != dB[v][1]:
        dif += 1; print("DIFF   va 0x%06X  A $%06X %s | B $%06X %s" % (v, dA[v][2], dA[v][1].hex()[:40], dB[v][2], dB[v][1].hex()[:40]))
print("# sites d'un seul côté : %d ; sites communs aux octets différents (adresses relogées ?) : %d" % (seul, dif))
# hors carte : plages modifiées par adresse (données de l'image, zone des talons, code MAX)
def hors(b, m):
    cv = bytearray(len(m[0]))
    for o, f in m[2]: cv[o:f] = b"\1" * (f - o)
    for o, f in b[2]: cv[o:f] = b"\1" * (f - o)
    P = []; x, y = b[0], m[0]; i = 0; n = min(len(x), len(y))
    while i < n:
        if x[i] != y[i] and not cv[i]:
            j = i
            while j < n and (x[j] != y[j] or (j + 8 < n and x[j:j + 8] != y[j:j + 8])) and not cv[j]: j += 1
            P.append((i, j)); i = j
        else: i += 1
    return P
hA = hors(bA, mA); hB = hors(bB, mB)
print("# hors carte : plages modifiées A %d, B %d ; identiques (mêmes bornes) %d" % (len(hA), len(hB), len(set(hA) & set(hB))))
for p in sorted(set(hA) ^ set(hB))[:200]:
    print("HORS %s  $%06X-$%06X (%d o)" % ("A" if p in hA else "B", p[0], p[1], p[1] - p[0]))
