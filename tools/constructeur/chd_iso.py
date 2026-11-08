#!/usr/bin/env python3
"""chd_iso.py -- image .chd (DVD, chdman createdvd) -> image .iso « creuse » lisible par hsfa_build.py.

Lecture par libchdr (BSD-3-Clause, https://github.com/rtissera/libchdr), chargee par ctypes. Seuls les secteurs utiles
a la construction sont decompresses : descripteur de volume, repertoire racine et les fichiers demandes (par defaut
SYSTEM.CNF, SLUS_213.17, X_DATA.BIN, Y_DATA.BIN) ; le reste de l'image est un trou (fichier creux : ~2 Go sur le
disque au lieu de 4,7). Les fichiers extraits sont identiques a l'octet a ceux de l'ISO d'origine.

Usage : chd_iso.py IMAGE.chd SORTIE.iso [--tout] [--libchdr CHEMIN]
"""
import ctypes, ctypes.util, os, struct, sys, threading

SECTEUR = 2048
FICHIERS = ("SYSTEM.CNF", "SLUS_213.17", "X_DATA.BIN", "Y_DATA.BIN")


class ErreurChd(Exception):
    pass


class _Entete(ctypes.Structure):          # debut de chd_header (libchdr/chd.h) : seuls ces champs sont lus
    _fields_ = [("length", ctypes.c_uint32), ("version", ctypes.c_uint32), ("flags", ctypes.c_uint32),
                ("compression", ctypes.c_uint32 * 4), ("hunkbytes", ctypes.c_uint32),
                ("totalhunks", ctypes.c_uint32), ("logicalbytes", ctypes.c_uint64)]


def charge_libchdr(chemin=None):
    noms = [chemin] if chemin else []
    ici = os.path.dirname(os.path.abspath(__file__))
    base = getattr(sys, "_MEIPASS", ici)
    for n in ("libchdr.so.0", "libchdr.so", "chdr.dll", "libchdr.dll", "libchdr.0.dylib", "libchdr.dylib"):
        noms += [os.path.join(base, "bin", n), os.path.join(ici, n)]
    trouve = ctypes.util.find_library("chdr")
    if trouve: noms.append(trouve)
    for n in noms:
        if n and (os.path.exists(n) or n == trouve):
            lib = ctypes.CDLL(n)
            lib.chd_open.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
            lib.chd_open.restype = ctypes.c_int
            lib.chd_close.argtypes = [ctypes.c_void_p]
            lib.chd_get_header.argtypes = [ctypes.c_void_p]
            lib.chd_get_header.restype = ctypes.POINTER(_Entete)
            lib.chd_read.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
            lib.chd_read.restype = ctypes.c_int
            lib.chd_error_string.argtypes = [ctypes.c_int]
            lib.chd_error_string.restype = ctypes.c_char_p
            lib.chd_get_metadata.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                                             ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32),
                                             ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint8)]
            lib.chd_get_metadata.restype = ctypes.c_int
            return lib
    raise ErreurChd("libchdr introuvable (lecture des images .chd)")


def _tag(s):
    return struct.unpack(">I", s.encode())[0]


class Chd:
    """lecture d'une image CHD par blocs (« hunks ») ; une instance par fil d'execution"""
    def __init__(self, chemin, lib=None):
        self.lib = lib or charge_libchdr()
        self.h = ctypes.c_void_p()
        err = self.lib.chd_open(os.fsencode(chemin), 1, None, ctypes.byref(self.h))   # 1 = CHD_OPEN_READ
        if err:
            raise ErreurChd("%s : %s" % (chemin, self.lib.chd_error_string(err).decode()))
        e = self.lib.chd_get_header(self.h).contents
        self.version, self.bloc, self.nblocs, self.taille = e.version, e.hunkbytes, e.totalhunks, e.logicalbytes
        self.chemin = chemin
        self._tampon = ctypes.create_string_buffer(self.bloc)
        self._cache = (-1, b"")

    def est_dvd(self):
        """metadonnee 'DVD ' (chdman createdvd) ; un CD ('CHT2', 'CHCD'...) a des secteurs de 2 352 o"""
        buf = ctypes.create_string_buffer(256); n = ctypes.c_uint32(); t = ctypes.c_uint32(); f = ctypes.c_uint8()
        if self.lib.chd_get_metadata(self.h, _tag("DVD "), 0, buf, 256, ctypes.byref(n), ctypes.byref(t), ctypes.byref(f)) == 0:
            return True
        for tag in ("CHT2", "CHTR", "CHCD", "CHGD"):
            if self.lib.chd_get_metadata(self.h, _tag(tag), 0, buf, 256, ctypes.byref(n), ctypes.byref(t), ctypes.byref(f)) == 0:
                return False
        return self.bloc % SECTEUR == 0          # sans metadonnee : image brute

    def bloc_n(self, i):
        if self._cache[0] == i: return self._cache[1]
        err = self.lib.chd_read(self.h, i, self._tampon)
        if err:
            raise ErreurChd("%s : bloc %d : %s" % (self.chemin, i, self.lib.chd_error_string(err).decode()))
        d = self._tampon.raw; self._cache = (i, d)
        return d

    def lit(self, pos, n):
        out = bytearray()
        while n > 0:
            i, o = divmod(pos, self.bloc)
            d = self.bloc_n(i)[o:o + n]
            out += d; pos += len(d); n -= len(d)
        return bytes(out)

    def ferme(self):
        if self.h:
            self.lib.chd_close(self.h); self.h = ctypes.c_void_p()


def fichiers_racine(lire):
    """{nom: (lba, taille)} du repertoire racine ISO 9660 (meme logique que hsfa_build.iso_fichiers)"""
    pvd = lire(16 * SECTEUR, SECTEUR)
    if pvd[0] != 1 or pvd[1:6] != b"CD001":
        raise ErreurChd("pas de systeme de fichiers ISO 9660 dans l'image (ce n'est pas un DVD PS2 ?)")
    racine = pvd[156:156 + 34]
    lba, taille = struct.unpack_from("<I", racine, 2)[0], struct.unpack_from("<I", racine, 10)[0]
    rep = lire(lba * SECTEUR, taille)
    res = {}; o = 0
    while o < len(rep):
        n = rep[o]
        if n == 0:
            o = (o // SECTEUR + 1) * SECTEUR; continue
        lba_f, t_f = struct.unpack_from("<I", rep, o + 2)[0], struct.unpack_from("<I", rep, o + 10)[0]
        ln = rep[o + 32]; nom = rep[o + 33:o + 33 + ln].decode("ascii", "replace")
        if nom not in ("\x00", "\x01"):
            res[nom.split(";")[0]] = (lba_f, t_f)
        o += n
    return res, (lba, taille)


def vers_iso(chd_chemin, iso_chemin, tout=False, fichiers=FICHIERS, travaux=None, progres=None, lib=None):
    """ecrit l'ISO (creuse sauf --tout) ; rend la liste des plages ecrites [(debut, fin)] en octets"""
    lib = lib or charge_libchdr()
    c = Chd(chd_chemin, lib)
    try:
        if not c.est_dvd():
            raise ErreurChd("%s : image de CD (chdman createcd), pas de DVD : l'Anthology est un DVD "
                            "(chdman createdvd)" % chd_chemin)
        if c.bloc % SECTEUR:
            raise ErreurChd("%s : blocs de %d o, pas un multiple de 2 048" % (chd_chemin, c.bloc))
        if tout:
            plages = [(0, c.taille)]
        else:
            fs, (rl, rt) = fichiers_racine(c.lit)
            plages = [(0, 17 * SECTEUR), (rl * SECTEUR, rl * SECTEUR + rt)]
            for n in fichiers:
                if n in fs:
                    l, t = fs[n]; plages.append((l * SECTEUR, l * SECTEUR + t))
        taille = c.taille
    finally:
        c.ferme()
    # blocs a decompresser (alignes), partages entre fils d'execution (libchdr relache le GIL dans chd_read)
    B = c.bloc
    blocs = sorted({i for d, f in plages for i in range(d // B, (f + B - 1) // B)})
    tmp = iso_chemin + ".tmp"
    with open(tmp, "wb") as f:
        f.truncate(taille)                      # fichier creux
    travaux = travaux or min(8, os.cpu_count() or 2)
    parts = [blocs[k::travaux] for k in range(travaux)]
    erreurs = []; fait = [0]; verrou = threading.Lock()

    def fil(liste):
        try:
            cc = Chd(chd_chemin, lib)
            with open(tmp, "r+b") as f:
                for i in liste:
                    d = cc.bloc_n(i)
                    f.seek(i * B); f.write(d[:max(0, min(B, taille - i * B))])
                    with verrou:
                        fait[0] += 1
                        if progres and fait[0] % 4096 == 0: progres(fait[0], len(blocs))
            cc.ferme()
        except Exception as x:              # noqa
            erreurs.append(x)
    fils = [threading.Thread(target=fil, args=(p,)) for p in parts if p]
    for t in fils: t.start()
    for t in fils: t.join()
    if erreurs: raise erreurs[0]
    os.replace(tmp, iso_chemin)
    return plages


if __name__ == "__main__":
    import argparse, time
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("chd"); ap.add_argument("iso")
    ap.add_argument("--tout", action="store_true", help="image complete (sinon : seulement les fichiers utiles)")
    ap.add_argument("--libchdr")
    a = ap.parse_args()
    t0 = time.time()
    p = vers_iso(a.chd, a.iso, a.tout, lib=charge_libchdr(a.libchdr),
                 progres=lambda n, t: print("  %d/%d blocs" % (n, t), flush=True))
    print("%s -> %s : %d plages, %.0f s" % (a.chd, a.iso, len(p), time.time() - t0))
