#!/usr/bin/env python3
"""p2_cmp.py -- graft review (homologues, X6): compare the MIPS body of an Upper routine (ro5) with its Hyper homologue
(ro9), instruction by instruction (unified diff). End of a routine = "jr ra" + delay slot followed by a prologue
(addiu sp,sp,-n) or padding.

Usage:  python3 -I p2_cmp.py U_HEX H_HEX [-v [N]]     (file offsets in ro5 and ro9; -v: show the first N differing lines)
Input:  modules ro5 and ro9 from $HSFA_MODULES (use the same ro9 module as the graft build; see paths.py).
Read only.
"""
import sys, os, struct, difflib
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))   # src/hsfa of the repository (= paths.SRC_HSFA)
from mips import Ins
def corps(mod, a):
    b = paths.lit_module(mod); L = []; k = 0
    while k < 4000:
        w = struct.unpack_from('<I', b, a + 4 * k)[0]; L.append(str(Ins(a + 4 * k, w))); k += 1
        if w == 0x03E00008:   # jr ra : fin si l'instruction apres le delai est un addiu sp,sp,-n ou 0
            L.append(str(Ins(a + 4 * k, struct.unpack_from('<I', b, a + 4 * k)[0]))); k += 1
            w2 = struct.unpack_from('<I', b, a + 4 * k)[0]
            if w2 == 0 or (w2 >> 16) == 0x27BD: break
    return L
u, h = int(sys.argv[1], 16), int(sys.argv[2], 16)
A, B = corps('ro5', u), corps('ro9', h)
d = [l for l in difflib.unified_diff(A, B, 'U %06x' % u, 'H %06x' % h, lineterm='', n=0) if not l.startswith('@@')]
print("U %06x : %d instr ; H %06x : %d instr ; lignes differentes : %d" % (u, len(A), h, len(B), max(0, len(d) - 2)))
if '-v' in sys.argv:
    for l in d[:int(sys.argv[sys.argv.index('-v') + 1]) if len(sys.argv) > sys.argv.index('-v') + 1 else 80]: print("   " + l)
