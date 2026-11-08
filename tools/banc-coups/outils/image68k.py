#!/usr/bin/env python3
"""(banc_coups) image 68K de la ROM programme CPS2 (8 fichiers de 512 Ko, octets echanges dans les mots) :
image68k.py <dossier roms sfa3ud> -> objet bytes ; fonctions lw (mot), ll (long tel quel), lps (long PS2 a moities echangees)"""
import os, sys
NOMS = ['sz3ud.03c', 'sz3ud.04c', 'sz3.05c', 'sz3.06c', 'sz3.07c', 'sz3.08c', 'sz3.09c', 'sz3.10b']


def image(d):
    b = bytearray()
    for n in NOMS:
        s = open(os.path.join(d, n), 'rb').read()
        b += bytes(s[i ^ 1] for i in range(len(s)))
    return bytes(b)
