#!/usr/bin/env python3
"""
p2s_inject_stage.py — injecte un stage Upper (chemin A, écrasement EN PLACE) dans un
savestate PCSX2 (.p2s), pour tester le cross-stage SANS cave (juste un savestate à charger).

.p2s = archive ZIP ; eeMemory.bin y est en zstd (méthode ZIP 93). On :
  1. lit toutes les entrées ZIP (métadonnées via le central directory),
  2. décompresse eeMemory.bin (zstd),
  3. y écrase : bank tuiles -> 0xdb4000, ring SCR2 -> 0xba4000, ring SCR3 -> 0xba8000,
     palette -> 0xbac000  (adresses EE = offset dump, base 0),
  4. recompresse eeMemory.bin (zstd, méthode 93) et reconstruit le ZIP (autres entrées
     copiées à l'identique), CRC32 recalculé.

Le repacker se teste seul (--repack-only) : reconditionne un .p2s sans rien changer ->
doit se recharger identique. À VALIDER avec un vrai .p2s (aucun sous la main à l'écriture).

Usage :
  python p2s_inject_stage.py <base.p2s> <stage_pack_base> <out.p2s>
  python p2s_inject_stage.py <base.p2s> --repack-only <out.p2s>   # test du repacker
    (stage_pack_base = ex. stage_packs/SFA3U_Chun-Li_temple ; lit .bank/.ring_scr2/3/.palette.bin)
"""
import sys, os, struct, zlib, zstandard

EOCD_SIG = 0x06054b50
CDH_SIG  = 0x02014b50
LFH_SIG  = 0x04034b50
Z_METHOD = 93  # Zstandard

# --- écrasements chemin A (EE addr, fichier du pack) ---
PATCHES = [(0xdb4000, "bank"), (0xba4000, "ring_scr2"),
           (0xba8000, "ring_scr3"), (0xbac000, "palette")]
EE_SIZE = 0x2000000


def parse_zip(data):
    """Retourne (entries, cd_off). entries = liste de dict à partir du central directory."""
    # localise l'EOCD (fin, éventuel commentaire)
    i = data.rfind(struct.pack('<I', EOCD_SIG))
    if i < 0:
        raise ValueError("EOCD introuvable (pas un ZIP ?)")
    total, cd_size, cd_off = struct.unpack_from('<HxxxxII', data, i + 8)  # ncd(this), cd_size, cd_off
    # relecture propre des champs EOCD
    _, disk, cd_disk, n_this, n_tot, cd_size, cd_off, clen = struct.unpack_from('<IHHHHIIH', data, i)
    entries = []
    p = cd_off
    for _ in range(n_tot):
        if struct.unpack_from('<I', data, p)[0] != CDH_SIG:
            raise ValueError("central dir corrompu")
        (sig, vmade, vneed, flags, method, mtime, mdate, crc, csize, usize,
         nlen, elen, clen2, dnum, iattr, eattr, lfh) = struct.unpack_from('<IHHHHHHIIIHHHHHII', data, p)
        name = data[p+46:p+46+nlen]
        # localise les données compressées via le LFH
        assert struct.unpack_from('<I', data, lfh)[0] == LFH_SIG, "LFH invalide"
        lnlen, lelen = struct.unpack_from('<HH', data, lfh+26)
        doff = lfh + 30 + lnlen + lelen
        raw = data[doff:doff+csize]
        entries.append(dict(name=name, method=method, flags=flags, mtime=mtime, mdate=mdate,
                            crc=crc, usize=usize, raw=raw, vneed=vneed, vmade=vmade,
                            iattr=iattr, eattr=eattr))
        p += 46 + nlen + elen + clen2
    return entries


def build_zip(entries):
    out = bytearray()
    centrals = []
    for e in entries:
        off = len(out)
        csize = len(e['raw'])
        out += struct.pack('<IHHHHHIIIHH', LFH_SIG, e['vneed'], e['flags'], e['method'],
                           e['mtime'], e['mdate'], e['crc'], csize, e['usize'],
                           len(e['name']), 0)
        out += e['name']
        out += e['raw']
        centrals.append((e, off, csize))
    cd_off = len(out)
    for e, off, csize in centrals:
        out += struct.pack('<IHHHHHHIIIHHHHHII', CDH_SIG, e['vmade'], e['vneed'], e['flags'],
                           e['method'], e['mtime'], e['mdate'], e['crc'], csize, e['usize'],
                           len(e['name']), 0, 0, 0, e['iattr'], e['eattr'], off)
        out += e['name']
    cd_size = len(out) - cd_off
    n = len(centrals)
    out += struct.pack('<IHHHHIIH', EOCD_SIG, 0, 0, n, n, cd_size, cd_off, 0)
    return bytes(out)


def get_ee(entries):
    for e in entries:
        if e['name'] == b'eeMemory.bin':
            if e['method'] != Z_METHOD:
                raise ValueError("eeMemory.bin méthode %d (attendu 93 zstd)" % e['method'])
            ee = zstandard.ZstdDecompressor().decompress(e['raw'], max_output_size=e['usize'])
            return e, bytearray(ee)
    raise ValueError("eeMemory.bin absent du .p2s")


def set_ee(entry, ee_bytes):
    entry['usize'] = len(ee_bytes)
    entry['crc'] = zlib.crc32(ee_bytes) & 0xffffffff
    entry['raw'] = zstandard.ZstdCompressor(level=7).compress(bytes(ee_bytes))


def main():
    base, arg2, out = sys.argv[1], sys.argv[2], sys.argv[3]
    data = open(base, 'rb').read()
    entries = parse_zip(data)
    e_ee, ee = get_ee(entries)
    print("eeMemory.bin : %d o décompressés (%d entrées ZIP)" % (len(ee), len(entries)))
    if len(ee) != EE_SIZE:
        print("  ⚠️ taille eeMemory inattendue (%#x != %#x)" % (len(ee), EE_SIZE))

    if arg2 != '--repack-only':
        for ee_addr, tag in PATCHES:
            fn = arg2 + "." + tag + ".bin"
            blob = open(fn, 'rb').read()
            ee[ee_addr:ee_addr+len(blob)] = blob
            print("  écrit %-9s (%#x o) @ EE %#x" % (tag, len(blob), ee_addr))

    set_ee(e_ee, ee)
    newzip = build_zip(entries)
    open(out, 'wb').write(newzip)

    # --- auto-vérif : relire le .p2s produit et confirmer eeMemory ---
    chk = parse_zip(open(out, 'rb').read())
    _, ee2 = get_ee(chk)
    ok = bytes(ee2) == bytes(ee)
    print("repack -> %s (%d o) ; relecture eeMemory %s" % (out, len(newzip), "OK" if ok else "KO"))
    if not ok:
        sys.exit("VERIF KO — le .p2s produit ne relit pas le bon eeMemory")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(0)
    main()
