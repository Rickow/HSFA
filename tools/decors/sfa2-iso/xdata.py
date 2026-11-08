"""xdata.py — accès commun à l'ISO de l'Anthology (ISO 9660 -> X_DATA.BIN -> entrées AFS), repris de
decors_sfa1/outils/extrait_sfa1.py (même lecture que hsfa_build.py)."""
import struct, hashlib, sys, os
sys.path.insert(0, os.environ.get("HSFA_SRC", "<workspace>/github/src/hsfa"))
from mwo3_codec import decompress
SECTEUR = 2048

class Echec(Exception):
    pass

def iso_fichiers(iso):
    with open(iso, "rb") as f:
        f.seek(16 * SECTEUR); pvd = f.read(SECTEUR)
        if pvd[1:6] != b"CD001": raise Echec("%s : pas d'ISO 9660" % iso)
        r = pvd[156:190]; lba, t = struct.unpack_from("<I", r, 2)[0], struct.unpack_from("<I", r, 10)[0]
        f.seek(lba * SECTEUR); rep = f.read(t)
    res = {}; o = 0
    while o < len(rep):
        n = rep[o]
        if n == 0: o = (o // SECTEUR + 1) * SECTEUR; continue
        lb, tt = struct.unpack_from("<I", rep, o + 2)[0], struct.unpack_from("<I", rep, o + 10)[0]
        nom = rep[o + 33:o + 33 + rep[o + 32]].decode("ascii", "replace")
        if nom not in ("\x00", "\x01"): res[nom.split(";")[0]] = (lb, tt)
        o += n
    return res

class XData:
    """X_DATA.BIN lu dans l'ISO (ou directement si xdata est donné)"""
    def __init__(self, iso=None, xdata=None):
        if xdata:
            self.f = open(xdata, "rb"); self.base = 0
        else:
            fs = iso_fichiers(iso)
            if "X_DATA.BIN" not in fs: raise Echec("l'ISO ne contient pas X_DATA.BIN (pas l'Anthology)")
            self.f = open(iso, "rb"); self.base = fs["X_DATA.BIN"][0] * SECTEUR
        h = self.lire(0, 8)
        if h[:4] != b"AFS\0": raise Echec("X_DATA.BIN : pas une archive AFS")
        self.n = struct.unpack_from("<I", h, 4)[0]
        self.toc = self.lire(8, 8 * self.n)
    def lire(self, o, n):
        self.f.seek(self.base + o); return self.f.read(n)
    def entree(self, i):
        return self.lire(*struct.unpack_from("<II", self.toc, 8 * i))
    def md5_groupe(self, a, b):
        h = hashlib.md5()
        for i in range(a, b + 1): h.update(self.entree(i))
        return h.hexdigest()
    def mwo3(self, i):
        return bytes(decompress(self.entree(i)))
