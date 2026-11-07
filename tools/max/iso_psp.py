#!/usr/bin/env python3
"""iso_psp.py -- lecture ISO 9660 (UMD PSP) sans dépendance (remplace isoinfo) : liste et extraction par chemin.
  iso_psp.py ISO liste [DOSSIER]      ; iso_psp.py ISO md5 CHEMIN ; iso_psp.py ISO extrait CHEMIN DEST"""
import hashlib, struct, sys
S = 2048
def _rep(f, lba, taille):
    f.seek(lba * S); rep = f.read(taille); res = {}; o = 0
    while o < len(rep):
        n = rep[o]
        if n == 0: o = (o // S + 1) * S; continue
        lba_f, t_f = struct.unpack_from("<I", rep, o + 2)[0], struct.unpack_from("<I", rep, o + 10)[0]
        drap = rep[o + 25]; ln = rep[o + 32]; nom = rep[o + 33:o + 33 + ln].decode("ascii", "replace")
        if nom not in ("\x00", "\x01"): res[nom.split(";")[0].upper()] = (lba_f, t_f, bool(drap & 2))
        o += n
    return res
def trouve(iso, chemin):
    with open(iso, "rb") as f:
        f.seek(16 * S); pvd = f.read(S)
        assert pvd[1:6] == b"CD001", "pas d'ISO 9660"
        r = pvd[156:190]; lba, t, d = struct.unpack_from("<I", r, 2)[0], struct.unpack_from("<I", r, 10)[0], True
        for part in [p for p in chemin.strip("/").split("/") if p]:
            e = _rep(f, lba, t)
            if part.upper() not in e: raise KeyError(chemin)
            lba, t, d = e[part.upper()]
        return lba, t, d
def lit(iso, chemin):
    lba, t, d = trouve(iso, chemin)
    with open(iso, "rb") as f: f.seek(lba * S); return f.read(t)
def liste(iso, chemin=""):
    lba, t, d = trouve(iso, chemin)
    with open(iso, "rb") as f: return _rep(f, lba, t)
if __name__ == "__main__":
    iso, cmd = sys.argv[1], sys.argv[2]
    if cmd == "liste":
        for n, (l, t, d) in sorted(liste(iso, sys.argv[3] if len(sys.argv) > 3 else "").items()):
            print("%s %10d %s" % ("d" if d else "-", t, n))
    elif cmd == "md5":
        b = lit(iso, sys.argv[3]); print(hashlib.md5(b).hexdigest(), len(b))
    elif cmd == "extrait":
        open(sys.argv[4], "wb").write(lit(iso, sys.argv[3]))
