#!/usr/bin/env python3
"""Tables de données de la ROM programme arcade SFA3 retrouvées dans d'autres binaires.

Image 68K : sz3e.03c, sz3e.04c, sz3.05c..sz3.10b concaténés (4 Mo). ATTENTION : les fichiers du set
sont en mots de 16 bits inversés (le texte 'NELGSI H' redevient 'ENGLISH') -> on remet en big-endian.
Sondes : fenêtres de 16 o prises tous les 32 o, non triviales (>= 6 mots distincts, <= 2 mots nuls).
Chaque cible est testée sous deux formes : BE (tel quel) et LE16 (mots convertis au boutisme hôte).

Usage :
  python3 probe_scan.py scan <fichier> <libellé> [<fichier> <libellé> ...]
  python3 probe_scan.py blocks        # blocs arcade dans l'EBOOT -> $SFA3MAX_CACHE/arcade_blocks_in_eboot.json
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import struct, collections, zipfile, json

PRG = ["sz3e.03c", "sz3e.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]

def arcade_images():
    """-> (image 68K big-endian, même image en mots little-endian)."""
    z = zipfile.ZipFile(paths.sfa3_zip())
    raw = b"".join(z.read(n) for n in PRG)          # = mots LE (fichiers inversés)
    be = bytearray(len(raw)); be[0::2] = raw[1::2]; be[1::2] = raw[0::2]
    return bytes(be), raw

def probes(img, step=32, n=16):
    d = {}
    for off in range(0, len(img) - n, step):
        w = img[off:off+n]; words = struct.unpack(">8H", w)
        if len(set(words)) < 6 or words.count(0) > 2 or words.count(0xFFFF) > 1: continue
        d.setdefault(w, off)
    return d

BE, LE16 = arcade_images()
P_BE, P_LE = probes(BE), probes(LE16)

def scan(path, label, verbose=True):
    data = open(path, "rb").read()
    hits = {"BE": [], "LE16": []}
    for form, P in (("BE", P_BE), ("LE16", P_LE)):
        heads = {k[:4] for k in P}
        for i in range(0, len(data) - 16, 2):
            if data[i:i+4] in heads and data[i:i+16] in P: hits[form].append((P[data[i:i+16]], i))
    if verbose:
        for form in ("BE", "LE16"):
            roms = sorted({r for r, _ in hits[form]})
            b = collections.Counter(r >> 16 for r in roms)
            print(f"  {label:<22} {form:<5} sondes trouvées: {len(roms):6}"
                  + (f"   zones ROM 64K: {len(b)}" if roms else ""))
    return hits

def runs(hits):
    """blocs contigus : sondes successives (pas 32) retrouvées au même pas dans la cible."""
    s = sorted(set(hits)); out = []; cur = [s[0]] if s else []
    for a, b in zip(s, s[1:]):
        if b[0] - cur[-1][0] == 32 and b[1] - cur[-1][1] == 32: cur.append(b)
        else: out.append(cur); cur = [b]
    if cur: out.append(cur)
    return out

if __name__ == "__main__":
    print(f"sondes retenues: {len(P_BE)}")
    if len(sys.argv) >= 2 and sys.argv[1] == "blocks":
        h = scan(paths.eboot(), "EBOOT", verbose=False); blocks = []
        for form in ("BE", "LE16"):
            for x in runs(h[form]):
                if len(x) >= 3:
                    blocks.append({"form": form, "rom": x[0][0], "va_lo": x[0][1] - 0x74,
                                   "va_hi": x[-1][1] + 16 - 0x74, "len": len(x) * 32})
        blocks.sort(key=lambda b: -b["len"])
        out = os.path.join(paths.CACHE, "arcade_blocks_in_eboot.json")
        json.dump(blocks, open(out, "w"), indent=1)
        print(f"{len(blocks)} blocs (>= 96 o) -> {out}")
    elif len(sys.argv) >= 4 and sys.argv[1] == "scan":
        for path, label in zip(sys.argv[2::2], sys.argv[3::2]): scan(path, label)
    else:
        print(__doc__)
