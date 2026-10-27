#!/usr/bin/env python3
"""ROM son au format MAME (decoupage de sfa3ud) a partir des fichiers son d'un module de l'Anthology.

  Z80   : fichier Z80 du groupe (294 912 o = image de la region 'audiocpu' de MAME, 0x00000-0x47FFF)
          sz3.01 = region[0x00000:0x08000] + region[0x10000:0x28000]   (ROM_LOAD 0x8000 + ROM_CONTINUE 0x10000,0x18000)
          sz3.02 = region[0x28000:0x48000]
  QSound: fichier 'GFX' de 8 Mo qui suit le Z80 dans X_DATA = image de la region 'qsound' (octets dans l'ordre
          de la region) ; la ROM est chargee par ROM_LOAD16_WORD_SWAP -> fichier = mots echanges.
          sz3.11m = swap(region[0:4M]), sz3.12m = swap(region[4M:8M])
Verifie sur ro3 : on retrouve sz3.01/02/11m/12m de sfa3ud octet pour octet (option --verif-ro3).

Usage : gen_son.py [ro5|ro3] [dossier_sortie]     (par defaut : ro5 -> ./roms_son_ro5/)
Source : X_DATA.BIN directement (index du manifeste), recoupee avec les fichiers extraits s'ils existent."""
import sys, os, hashlib, zlib
XDATA = "<workspace>/work/xdata/X_DATA.BIN"
EXTRACT = "<workspace>/anthology_extract/"
ARCADE = "<workspace>/work/mame/roms/sfa3ud/"
# (index manifeste Z80, index QSound, fichiers extraits)
MODULES = {
    'ro3': (287, 288, "ro3_usa_z80.bin", "ro3_usa_gfx_e288.bin"),
    'ro5': (388, 389, "ro5_usa_z80.bin", "ro5_usa_gfx_e389.bin"),
}
Z80_SIZE, QS_SIZE = 0x48000, 0x800000

def manifeste():
    m = {}
    for l in open(os.path.join(EXTRACT, "manifest.csv")).read().splitlines()[1:]:
        i, off, n, kind, name = l.split(",", 4)
        m[int(i)] = (int(off), int(n), kind)
    return m

def lire(mod):
    iz, iq, fz, fq = MODULES[mod]
    m = manifeste()
    assert m[iz][2] == "Z80" and m[iz][1] == Z80_SIZE, m[iz]
    assert m[iq][1] == QS_SIZE, m[iq]
    with open(XDATA, "rb") as f:
        f.seek(m[iz][0]); z = f.read(Z80_SIZE)
        f.seek(m[iq][0]); q = f.read(QS_SIZE)
    for nom, d in ((fz, z), (fq, q)):
        p = os.path.join(EXTRACT, nom)
        if os.path.exists(p): assert open(p, "rb").read() == d, "%s differe de X_DATA" % nom
    return z, q

def swap16(b):
    o = bytearray(len(b)); o[0::2] = b[1::2]; o[1::2] = b[0::2]; return bytes(o)

def decoupe(z, q):
    assert z[0x8000:0x10000] == bytes(0x8000), "zone 0x8000-0xFFFF non nulle : non chargee par MAME"
    return {
        "sz3.01": z[0x0000:0x8000] + z[0x10000:0x28000],
        "sz3.02": z[0x28000:0x48000],
        "sz3.11m": swap16(q[:0x400000]),
        "sz3.12m": swap16(q[0x400000:]),
    }

def main():
    mod = sys.argv[1] if len(sys.argv) > 1 else "ro5"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "roms_son_" + mod)
    z, q = lire(mod)
    roms = decoupe(z, q)
    os.makedirs(out, exist_ok=True)
    for n, d in roms.items():
        open(os.path.join(out, n), "wb").write(d)
        print("%-8s %8d o  CRC %08x  SHA1 %s" % (n, len(d), zlib.crc32(d), hashlib.sha1(d).hexdigest()))
    # occupation (dernier octet non nul)
    nz = lambda b: len(b.rstrip(b"\0"))
    print("Z80 : region utilisee jusqu'a 0x%05X ; QSound : dernier octet non nul 0x%06X / 0x%06X" % (nz(z), nz(q), QS_SIZE))
    if mod == "ro3":
        for n, d in roms.items():
            ok = open(os.path.join(ARCADE, n), "rb").read() == d
            print("verif ro3 -> arcade %s : %s" % (n, "IDENTIQUE" if ok else "DIFFERENT"))
    print("ecrit dans", out)

if __name__ == "__main__":
    main()
