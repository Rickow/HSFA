#!/usr/bin/env python3
"""ASSEMBLAGE DU PROGRAMME ENTIER (HANDOFF §55) : tout le code 68K recompile d'un module traduit et
assemble comme UNE seule unite -> tous les appels entre fonctions sont internes (nos adresses),
les seules cibles externes sont le code natif du portage (crochets, fonctions PS2). Rend l'image
68K, et le bilan de ce qui reste a raccorder.  Usage : MODULE=ro3 link.py [base_hex]"""
import sys, os, struct, time, collections, json
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import translate as T
from assemble import assemble
from mips import CODE0

def main():
    mod = os.environ.get("MODULE", "ro3")
    buf = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, "rb").read()
    end = struct.unpack_from('<I', buf, 12)[0]
    c0 = 0x22de0 if mod == 'ro9' else CODE0
    base = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x1000
    t0 = time.time()
    ext = collections.Counter()
    def external(t):
        ext[t] += 1
        return None                      # code natif du portage : a raccorder (crochet FBNeo)
    its, words, unres = assemble(buf, c0, end, base=base, external=external)
    dt = time.time() - t0
    img = struct.pack('>%dH' % len(words), *words)
    out = "<workspace>/work/cps2/%s_traduit.bin" % mod
    open(out, "wb").write(img)
    kinds = collections.Counter(it.kind for it in its)
    print("module %s : %d elements, %d mots = %.2f Mo de code 68K (base $%x), %.0f s" % (
        mod, len(its), len(words), len(words) * 2 / 1e6, base, dt))
    print("elements :", dict(kinds))
    print("non resolus : %d ; cibles externes distinctes (code natif / crochets) : %d, appels : %d" % (
        unres, len(ext), sum(ext.values())))
    json.dump({"%x" % k: v for k, v in ext.most_common()}, open(os.path.join(D, "externes_%s.json" % mod), "w"))
    print("image ecrite :", out)

if __name__ == "__main__":
    main()
