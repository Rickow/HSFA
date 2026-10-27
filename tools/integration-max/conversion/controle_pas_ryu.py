#!/usr/bin/env python3
"""Contrôle octet à octet de la règle des pas de 20 o (convertit_max.permute_bloc('pas'), employée pour
tables_explicites_*.s, anims_*.s et fin_anims_*.s) : les pas de Ryu de l'arcade (à partir de $146402, 1re entrée de sa
table $2B0 en $146218) passent par la règle, puis sont comparés à leur copie dans l'image d'Upper ($231BB8), hors
pointeurs (frame +$4, reprise +$14 : adresses PS2 relogées, mais leur place et leur SWAP sont vérifiés).
Données arcade : ~/.cache/sfa3max/sfa3ud_donnees.bin (vue DONNÉES de sfa3ud). Lecture seule."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convertit_max as C

ARC = os.path.expanduser('~/.cache/sfa3max/sfa3ud_donnees.bin')
A0, I0, N = 0x146402, 0x231BB8, 400

def main():
    arc = open(ARC, 'rb').read(); img = C.charge_image(C.ROMS_DEF)
    a, i, n_ok, n_oct = A0, I0, 0, 0
    for k in range(N):
        b = arc[a:a + 20]; rep = b[1] & 0x80
        el = [(1, '$%02x' % x, '', 0) for x in b[:4]] + [(4, '$%08x' % struct.unpack('>I', b[4:8])[0], '', 0)] \
            + [(1, '$%02x' % x, '', 0) for x in b[8:20]]
        if rep: el.append((4, '$%08x' % struct.unpack('>I', arc[a + 20:a + 24])[0], '', 0))
        octs = []
        for l in C.Convertisseur.permute_bloc(None, 'pas', el):
            l = l.strip()
            if l.startswith('dc.b'): octs += [int(x.strip()[1:], 16) for x in l[4:].split(',')]
            else: octs += [None] * 4                                 # long (pointeur) : SWAP, valeur relogée
        im = img[i:i + len(octs)]
        if len(octs) != 20 + (4 if rep else 0) or any(x is not None and x != y for x, y in zip(octs, im)):
            break
        # pointeurs : rangés SWAP dans l'image (mot fort de l'adresse PS2 en second)
        if not (im[6:8] == b'\x00\x7a' or im[6:8] == b'\x00\x79'):
            break
        n_ok += 1; n_oct += sum(1 for x in octs if x is not None)
        a += len(octs); i += len(octs)
    print('pas de Ryu : %d pas consécutifs conformes (%d octets hors pointeurs) ; arrêt en arcade $%X '
          '(écart propre à Upper au-delà : durée modifiée)' % (n_ok, n_oct, a))
    sys.exit(0 if n_ok >= 100 else 1)

if __name__ == '__main__':
    main()
