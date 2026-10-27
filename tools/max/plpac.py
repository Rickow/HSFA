"""Conteneur plXX_e.pac (SFA3 MAX PSP) : u32 n, u32 total ; n x (u32 type, u32 taille) ;
données à partir de 0x800, chaque entrée alignée sur 0x800."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import struct
def split(d):
    n, tot = struct.unpack_from("<2I", d, 0)
    out, off = [], 0x800
    for i in range(n):
        t, sz = struct.unpack_from("<2I", d, 8 + 8*i)
        out.append((t, d[off:off+sz]))
        off += (sz + 0x7FF) & ~0x7FF
    return out

def extract_from_iso(iso_path=None, outdir=None):
    """Copie tous les plXX_e.pac d'un ISO SFA3 MAX dans outdir (lecture seule de l'ISO)."""
    import os, sys
    sys.path.insert(0, paths.sfa3ws_dir())
    from sfa3_ws_patternpatcher import Iso
    iso_path = iso_path or paths.iso(); outdir = outdir or paths.pac_dir()
    os.makedirs(outdir, exist_ok=True)
    iso = Iso(iso_path); n = 0
    for r in iso.walk():
        if r.name.lower().startswith("pl") and r.name.lower().endswith(".pac"):
            open(os.path.join(outdir, r.name), "wb").write(iso.read_file(r)); n += 1
    return n

if __name__ == "__main__":
    import sys
    n = extract_from_iso(sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2] if len(sys.argv) > 2 else None)
    print(n, "fichiers pl extraits dans", sys.argv[2] if len(sys.argv) > 2 else paths.pac_dir())
