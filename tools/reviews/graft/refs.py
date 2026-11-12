#!/usr/bin/env python3
"""refs.py -- graft review: who references a PS2 EXECUTION address in a MIPS module: jal / j, constants lui+addiu/ori
(simple per-register tracking), aligned data words (file offset = execution address - 0x1F0000).

Usage:  nice -n 19 python3 -I refs.py MODULE ADR_EXEC[,ADR...]     (MODULE = roN or path of a .bin, e.g. ro9a_module.bin
        of a frozen build; addresses in hex)
Input:  $HSFA_MODULES for roN (see paths.py). Read only. For a range of addresses, see refs_code.py.
"""
import sys, os, struct
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
mod = sys.argv[1]; cib = [int(x, 16) for x in sys.argv[2].split(',')]
b = paths.lit_module(mod); n = len(b) // 4; W = struct.unpack_from('<%dI' % n, b, 0)
S = set(cib); lui = {}
for i, w in enumerate(W):
    a = i * 4; op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; imm = w & 0xffff
    if w in S: print("%06x mot      -> %x" % (a, w))
    if op in (2, 3):
        t = (w & 0x3ffffff) << 2
        if t in S: print("%06x %s -> %x" % (a, "jal" if op == 3 else "j  ", t))
    elif op == 15: lui[rt] = (imm << 16, a)
    elif op in (9, 13) and rs in lui and a - lui[rs][1] <= 32:
        v = lui[rs][0] + (imm - 0x10000 if (op == 9 and imm & 0x8000) else imm)
        if v in S: print("%06x lui+imm  -> %x" % (a, v))
