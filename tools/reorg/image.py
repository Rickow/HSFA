"""Chargement de l'image programme 68K (8 x 512 Ko, mots inverses) d'un jeu de ROM sfa3ud."""
import os
NOMS = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
def charge(dossier):
    out = bytearray()
    for n in NOMS:
        b = open(os.path.join(dossier, n), "rb").read()
        out += bytes(x for i in range(0, len(b), 2) for x in (b[i+1], b[i]))
    return bytes(out)
