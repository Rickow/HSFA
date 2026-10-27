#!/usr/bin/env python3
"""IMAGE PROGRAMME COMPLETE (HANDOFF §56) : code 68K traduit (mode memoire cps2) + donnees du module.
  $000000  vecteurs 68K (SP et PC d'origine : a raccorder au point d'entree traduit)
  $001000  code traduit (tout le module, link.py)
  DATA     section de donnees du module, mots remis en gros-boutiste (coherent avec la recette cps2)
  ROM etendue au-dela de 4 Mo si necessaire (Hyper) : le fork la projette (cf. §55)
Les variables du portage vont dans la RAM propre au fork (PORT_RAM, $F00000). Bilan des adresses
restees hors carte.  Usage : MODULE=ro3 build_rom.py"""
import sys, os, struct, re, collections
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
os.environ.setdefault("MEMMODE", "cps2")
import translate as T
from assemble import assemble
from mips import CODE0

def main():
    mod = os.environ.get("MODULE", "ro3")
    buf = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, "rb").read()
    end = struct.unpack_from('<I', buf, 12)[0]; c0 = 0x22de0 if mod == 'ro9' else CODE0
    T.set_module_bounds(buf)
    CODE = 0x1000
    T.DATA_BASE = 0x200000                                  # provisoire (tailles independantes de sa valeur)
    its, words, unres = assemble(buf, c0, end, base=CODE)
    size = 2 * len(words)
    T.DATA_BASE = (CODE + size + 0xfff) & ~0xfff
    its, words, unres = assemble(buf, c0, end, base=CODE)
    assert 2 * len(words) == size, "la taille du code depend de DATA_BASE"
    data = bytearray(buf[end:])
    import bisect as _b
    _vas=[it.va for it in its]
    def _lab(va):
        k=_b.bisect_left(_vas, va); return its[k].off if k < len(its) else None
    nrel=0
    for o in range(0, len(data) - 3, 4):                    # POINTEURS DE CODE dans les donnees -> nos adresses
        v = struct.unpack_from('<I', data, o)[0]
        if T.is_code_ptr(v):
            a = _lab(v - T.RUNTIME_BASE)
            if a is not None: struct.pack_into('<I', data, o, a); nrel += 1
    data = bytes(data)                                        # donnees du module (fin du code -> fin du fichier)
    data = data[:len(data) // 2 * 2]
    data_be = bytes(b for i in range(0, len(data), 2) for b in (data[i+1], data[i]))
    total = T.DATA_BASE + len(data_be)
    img = bytearray(max(total, 0x400000))
    rom = open('<workspace>/work/cps2/sfa3_prog.bin', 'rb').read()
    img[0:8] = rom[0:8]                                     # SP/PC d'origine (PC a raccorder)
    img[CODE:CODE + size] = struct.pack('>%dH' % len(words), *words)
    img[T.DATA_BASE:T.DATA_BASE + len(data_be)] = data_be
    out = "<workspace>/work/cps2/%s_programme.bin" % mod
    open(out, "wb").write(img)
    hors = collections.Counter()
    for it in its:
        m = re.search(r'HORS CARTE|ZONE NON CONVERTIE', it.mn)
        if m:
            a = re.search(r'\$([0-9a-f]{6})', it.mn)
            hors[(a.group(1)[:2] if a else '??')] += 1
    print("%s : code %#x octets a $%x, donnees %#x octets a $%x, fin $%x (%s 4 Mo)" % (
        mod, size, CODE, len(data_be), T.DATA_BASE, total, "tient dans" if total <= 0x400000 else "DEPASSE"))
    print("   non resolus (appels natifs...) : %d ; acces hors carte restants par zone : %s" % (unres, dict(hors)))
    print("   image :", out)

if __name__ == "__main__":
    main()
