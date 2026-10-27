#!/usr/bin/env python3
"""image_z80.py -- construit l'image « audiocpu » (disposition MAME) d'un jeu Capcom depuis le zip de l'utilisateur.

Les ROM restent chez l'utilisateur : ce script lit son zip et ecrit une image de travail, jamais publiee.

Disposition MAME :
  CPS-2 : 1re ROM Z80 -> 0x00000-0x07FFF puis 0x10000 (suite) ; 2e ROM eventuelle -> 0x28000. Image 0x48000 o.
  CPS-1 : ROM Z80 -> 0x00000-0x07FFF puis 0x10000 (suite). Image 0x18000 o.

Usage : python3 image_z80.py jeu fichier.zip sortie.bin      (jeu : sfa, sfa2, ssf2, ssf2t, hsf2, ffight, sf2hf)
"""
import sys, zipfile

JEUX = {   # jeu -> (taille de l'image, [(membre du zip, adresse de chargement)]) ; adresse 0 = coupe 0x8000 / 0x10000
    'sfa':    (0x48000, [('sfz.01', 0), ('sfz.02', 0x28000)]),
    'sfa2':   (0x48000, [('sz2.01a', 0), ('sz2.02a', 0x28000)]),
    'ssf2':   (0x48000, [('ssf-01a', 0)]),
    'ssf2t':  (0x48000, [('sfx.01', 0), ('sfx.02', 0x28000)]),
    'hsf2':   (0x48000, [('hs2.01', 0), ('hs2.02', 0x28000)]),
    'ffight': (0x18000, [('ff_09.12b', 0)]),
    'sf2hf':  (0x18000, [('s92_09.11a', 0)]),
}


def image(jeu, zip_path):
    taille, membres = JEUX[jeu]
    z = bytearray(taille)
    with zipfile.ZipFile(zip_path) as zf:
        for nom, adr in membres:
            d = zf.read(nom)
            if adr == 0:
                z[0:0x8000] = d[:0x8000]
                z[0x10000:0x10000 + len(d) - 0x8000] = d[0x8000:]
            else:
                z[adr:adr + len(d)] = d
    return bytes(z)


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] not in JEUX:
        sys.exit(__doc__)
    open(sys.argv[3], 'wb').write(image(sys.argv[1], sys.argv[2]))
