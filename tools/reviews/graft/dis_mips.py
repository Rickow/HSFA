#!/usr/bin/env python3
"""dis_mips.py -- graft review: disassemble the MIPS of a module with the decoder of the repository (src/hsfa/mips.py).

Usage:  python3 -I dis_mips.py MODULE FILE_OFFSET N
        MODULE = roN ($HSFA_MODULES/roN_usa_prog68k.bin) or the path of a .bin (e.g. ro9a_module.bin of a frozen build);
        FILE_OFFSET in hex; N instructions.
Read only. See paths.py for the variables.
"""
import sys, os, struct
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))   # src/hsfa of the repository (= paths.SRC_HSFA)
from mips import Ins
mod, a, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
b = paths.lit_module(mod)
for k in range(n):
    x = Ins(a + 4 * k, struct.unpack_from('<I', b, a + 4 * k)[0])
    print("%06x %s" % (a + 4 * k, x))
