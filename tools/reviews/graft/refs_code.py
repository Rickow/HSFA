#!/usr/bin/env python3
"""refs_code.py -- graft review: find in the MIPS code of a module the constants built by lui + addiu / ori / memory
access that fall in [LO, HI) (PS2 execution addresses): who refers to a table or a data area.

Usage:  python3 -I refs_code.py LO HI [ro5|ro9|path]     (hex; module ro5 by default)
Input:  the module ($HSFA_MODULES). Output: site (file offset, exec address), opcode, value. Read only. See paths.py.
"""
import sys, os, struct
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
mod = sys.argv[3] if len(sys.argv) > 3 else 'ro5'
b = paths.module(mod)
ce = struct.unpack_from('<I', b, 12)[0]
lui = {}
for a in range(0x20, ce, 4):
    w = struct.unpack_from('<I', b, a)[0]; op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; imm = w & 0xffff
    simm = imm - 0x10000 if imm & 0x8000 else imm
    if op == 15: lui[rt] = (imm << 16, a); continue
    if op in (9, 13, 32, 33, 35, 36, 37, 40, 41, 43) and rs in lui and a - lui[rs][1] <= 48:
        v = (lui[rs][0] + (imm if op == 13 else simm)) & 0xffffffff
        if lo <= v < hi: print("%06x (exec %06x) op%d -> %06x" % (a, a + 0x1F0000, op, v))
    if op in (9, 13) and rt != rs: lui.pop(rt, None)
