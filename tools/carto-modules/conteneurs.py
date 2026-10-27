#!/usr/bin/env python3
"""Entrees X_DATA des groupes ro1, ro6, ro7 (et ro2 pour comparaison) : conteneur graphique (anthgfx.records) ?
-> nombre de tuiles par taille. Lecture directe de X_DATA.BIN de l'ISO extrait si present, sinon des fichiers extraits."""
import sys, struct, csv, os
sys.path.insert(0, '<workspace>/scripts/untranspile'); sys.path.insert(0, '.')
import anthgfx
man = {int(r['idx']): r for r in csv.DictReader(open('<workspace>/anthology_extract/manifest.csv'))}
import iso
ISO = sys.argv[1] if len(sys.argv) > 1 else '<workspace>/iso/SFA_Anthology_AllUnlocked_WORK.iso'
XD = (ISO, iso.racine(ISO)['X_DATA.BIN'][0])
def lire(i):
    r = man[i]; f = open(ISO, 'rb'); f.seek(XD[1] + int(r['offset'])); return f.read(int(r['size']))
print('X_DATA :', XD)
for i in list(range(206, 224)) + list(range(526, 543)) + list(range(224, 229)) + [249]:
    b = lire(i)
    if b is None: print('e%d illisible' % i); continue
    rec = anthgfx.records(b); ok = anthgfx.is_container(b)
    print('e%d %-5s %9d o  %s  %s' % (i, man[i]['kind'], len(b), 'conteneur' if ok else '-',
          ' '.join('%s:premier=%d n=%d' % ({0: '8x8', 1: '16x16', 2: '32x32'}[k], f, n) for k, f, n, t in rec) if ok else b[:16].hex()))
