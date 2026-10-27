"""Image programme 68000 (4 Mo, ordre naturel gros-boutiste) d'un dossier de ROM traduites (sz3ud.03c..., mots echanges)."""
import os
NOMS = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]

def lit(dossier):
    raw = b"".join(open(os.path.join(dossier, n), "rb").read() for n in NOMS)
    b = bytearray(raw); b[0::2], b[1::2] = raw[1::2], raw[0::2]
    return b

def ecrit(img, dossier, modele=None):
    """ecrit les 8 fichiers (mots echanges) ; liens vers les autres fichiers de 'modele'"""
    os.makedirs(dossier, exist_ok=True)
    sw = bytearray(img); sw[0::2], sw[1::2] = img[1::2], img[0::2]
    for k, n in enumerate(NOMS):
        p = os.path.join(dossier, n)
        if os.path.islink(p): os.unlink(p)
        open(p, "wb").write(sw[k * 0x80000:(k + 1) * 0x80000])
    if modele:
        for f in os.listdir(modele):
            p = os.path.join(dossier, f)
            if f not in NOMS and not os.path.exists(p):
                os.symlink(os.path.realpath(os.path.join(modele, f)), p)
