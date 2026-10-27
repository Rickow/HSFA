#!/usr/bin/env python3
"""Rapproche les flux ADX de Y_DATA.BIN des morceaux de packs VGM (VGMRips) par la DUREE DE BOUCLE.

La longueur de boucle depend seulement de la partition et du tempo, pas du rendu (QSound, YM2151,
reechantillonnage) : deux enregistrements d'une meme sequence ont la meme boucle, a quelques
millisecondes pres. C'est un filtre rapide avant l'ecoute ou l'empreinte MFCC + DTW.

Usage :
  python3 -I apparie_vgm.py Y_DATA.BIN packs/ [--flux 433-439,460-529,543-586] [--tol 0.4] [--top 3]
    Y_DATA.BIN : l'AFS de l'ISO (ou l'ISO, avec --decalage 0xAB628800)
    packs/     : dossier contenant des .vgm / .vgz (un sous-dossier par pack)
Sortie : TSV  flux  boucle_s  intro_s  candidat  boucle_vgm_s  ecart_%  (trie par ecart)
"""
import argparse, gzip, os, struct, sys


def u32be(b, o): return struct.unpack_from('>I', b, o)[0]
def u32le(b, o): return struct.unpack_from('<I', b, o)[0]


def entrees_afs(f, base):
    f.seek(base)
    tete = f.read(8)
    if tete[:4] != b'AFS\0':
        sys.exit("pas d'en-tete AFS a %#x (essayer --decalage)" % base)
    n = u32le(tete, 4)
    table = f.read(8 * n)
    return [(base + u32le(table, 8 * i), u32le(table, 8 * i + 4)) for i in range(n)]


def boucle_adx(h):
    """(frequence, total, debut_boucle, fin_boucle) en echantillons, ou None."""
    if len(h) < 0x34 or h[0] != 0x80 or h[1] != 0x00:
        return None
    freq, total, version = u32be(h, 0x08), u32be(h, 0x0C), h[0x12]
    base = {3: 0x18, 4: 0x24}.get(version)
    if base is None or not freq:
        return (freq, total, None, None)
    if not u32be(h, base):
        return (freq, total, None, None)
    return (freq, total, u32be(h, base + 4), u32be(h, base + 12))


def boucle_vgm(chemin):
    with open(chemin, 'rb') as f:
        d = f.read(0x40)
    if d[:2] == b'\x1f\x8b':
        with gzip.open(chemin, 'rb') as g:
            d = g.read(0x40)
    if d[:4] != b'Vgm ':
        return None
    total, boucle = u32le(d, 0x18), u32le(d, 0x20)   # echantillons a 44 100 Hz
    return total / 44100.0, (boucle / 44100.0 if boucle else None)


def plages(txt):
    out = []
    for p in txt.split(','):
        a, _, b = p.partition('-')
        out.extend(range(int(a), int(b or a) + 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ydata'); ap.add_argument('packs')
    ap.add_argument('--flux', default='433-439,460-529,543-586')
    ap.add_argument('--decalage', type=lambda s: int(s, 0), default=0)
    ap.add_argument('--tol', type=float, default=0.4, help='ecart max de boucle, en %%')
    ap.add_argument('--top', type=int, default=3)
    a = ap.parse_args()

    vgms = []
    for rac, _, fics in os.walk(a.packs):
        for n in sorted(fics):
            if n.lower().endswith(('.vgm', '.vgz')):
                c = os.path.join(rac, n)
                r = boucle_vgm(c)
                if r and r[1]:
                    vgms.append((os.path.relpath(c, a.packs), r[0], r[1]))
    if not vgms:
        sys.exit('aucun VGM bouclant trouve dans ' + a.packs)

    print('flux\tboucle_s\tintro_s\tcandidat\tboucle_vgm_s\tecart_%')
    with open(a.ydata, 'rb') as f:
        ent = entrees_afs(f, a.decalage)
        for y in plages(a.flux):
            if y >= len(ent):
                continue
            off, _ = ent[y]
            f.seek(off)
            r = boucle_adx(f.read(0x40))
            if not r or r[2] is None:
                print(f'Y{y}\t-\t-\t(pas de boucle ADX)\t-\t-')
                continue
            freq, _, ls, le = r
            b, intro = (le - ls) / freq, ls / freq
            cands = sorted(((abs(v[2] - b) / b * 100, v) for v in vgms))[:a.top]
            bons = [c for c in cands if c[0] <= a.tol]
            if not bons:
                print(f'Y{y}\t{b:.3f}\t{intro:.3f}\t(aucun <= {a.tol} %)\t-\t-')
            for e, (nom, _, bv) in bons:
                print(f'Y{y}\t{b:.3f}\t{intro:.3f}\t{nom}\t{bv:.3f}\t{e:.2f}')


if __name__ == '__main__':
    main()
