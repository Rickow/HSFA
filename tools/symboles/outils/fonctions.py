#!/usr/bin/env python3
"""Fonctions du module ro3 : débuts MIPS (cibles de jal, comme carto_ro5/commun.py) et leur adresse
dans l'image traduite (carte_image.txt)."""
import struct, bisect, os, re, collections
RO3 = "<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin"
BASE = 0x1F0000
ICI = os.path.dirname(os.path.abspath(__file__))
CARTE = os.environ.get('CARTE', os.path.join(ICI, '..', '_carte_image_snapshot.txt'))

def debuts_mips():
    b = open(RO3, 'rb').read()
    h = struct.unpack_from('<8I', b, 0); fin = h[3]
    n = (fin - 0x20) // 4
    W = struct.unpack_from('<%dI' % n, b, 0x20)
    st = set()
    for w in W:
        if w >> 26 == 3:
            t = ((w & 0x3ffffff) << 2) - BASE
            if 0x22b00 <= t < fin: st.add(t)
    return sorted(st), fin

def carte(path=CARTE):
    """[(trad, va, texte)] dans l'ordre du fichier"""
    L = []
    for l in open(path):
        p = l.rstrip('\n').split(' ', 2)
        if len(p) < 3: p.append('')
        L.append((int(p[0], 16), int(p[1], 16), p[2]))
    return L

def entrees_trad(starts, C):
    """va de début de fonction -> adresse traduite de sa 1re instruction (1re ligne de la carte
    dont le va tombe dans [début, début suivant)), et indicateur 'exact' (va == début)."""
    vas = sorted({c[1] for c in C})
    first = {}
    for t, va, _ in C:
        if va not in first: first[va] = t
    res = {}
    for k, s in enumerate(starts):
        e = starts[k+1] if k+1 < len(starts) else 1 << 40
        i = bisect.bisect_left(vas, s)
        if i < len(vas) and vas[i] < e:
            # plus petite adresse traduite parmi les va de la fonction proches du début
            res[s] = (first[vas[i]], vas[i] == s)
    return res

def bornes_trad(trad_bin=os.path.join(ICI, '..', '_trad.bin')):
    """(fin du code traduit, base des données) de l'image : la base des données est retrouvée en
    cherchant, à une frontière de 4 Ko, les 64 premiers octets de la section de données du module
    (mots remis en gros-boutiste, comme build_rom/mame_test)."""
    img = open(trad_bin, 'rb').read()
    b = open(RO3, 'rb').read()
    h = struct.unpack_from('<8I', b, 0); fin = h[3]
    d = b[fin:fin + 64]; ds = bytes(x for i in range(0, 64, 2) for x in (d[i+1], d[i]))
    for base in range(0x1000, 0x400000, 0x1000):
        if img[base:base + 64] == ds:
            return base, base
    raise RuntimeError('base des données introuvable dans l\'image traduite')
