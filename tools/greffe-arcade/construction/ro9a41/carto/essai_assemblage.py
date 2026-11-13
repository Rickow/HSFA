#!/usr/bin/env python3
"""Essai a blanc (rien n'est ecrit) : assemblage COMPLET du module en mode cps2 avec assemble.assemble, comme
mame_test.py, externes -> talon RTS, natives = hooks_fork_<mod>_carto.json filtre par mame_test.native_at.
Mesure : nombre d'elements, taille du code 68K, non resolus, aiguillages hors portee, octets apres ADDA..."""
import os, sys, json, struct, time
os.environ["MEMMODE"] = "cps2"
sys.path.insert(0, "@HA_UT@")
import translate as T
from assemble import assemble
import assemble as A
import mame_test as MT
from mips import CODE0
mod = sys.argv[1] if len(sys.argv) > 1 else 'ro9'
buf = open("@HA_EXTRACT@/decompressed/%s_usa_prog68k.bin" % mod, "rb").read()
T.set_module_bounds(buf)
D = os.path.dirname(os.path.abspath(__file__))
NAT = [int(k, 16) for k, v in json.load(open(os.path.join(D, "hooks_fork_%s_carto.json" % mod))).items() if v["type"] == "natif du module"]
NAT = [a for a in NAT if MT.native_at(buf, a)]
T.DATA_BASE = 0x200000
c0 = 0x22de0 if mod == 'ro9' else CODE0
t0 = time.time()
its, words, unres = assemble(buf, c0, T.code_end_translate(buf), base=0x1000, external=lambda t: 0x800, native=NAT)
print("%s : %d elements, code 68K %d o (%.2f Mo), non resolus %d, natives %d, %.0f s" % (mod, len(its), 2*len(words), 2*len(words)/2**20, unres, len(NAT), time.time()-t0))
print("aiguillages hors portee 16 bits -> tremplins : %d" % sum(len(v) for v in A.FAR_ENT.values()))
print("octets via An apres ADDA : %d ; longs par post-increment fusionnes : %d ; operations long echange sans SR : %d" % (T.BYTE_ADDA[0], T.LONG_POSTINC[0], T.LONG_SR[0]))
