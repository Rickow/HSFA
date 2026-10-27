#!/usr/bin/env python3
"""dis_elf.py ADRESSE [N] : desassemble l'executable PS2 (SLUS_213.17, segment 0x100000) avec capstone."""
import sys, capstone
E = open("<workspace>/tmp_hdd/SLUS_213.17", "rb").read()
a = int(sys.argv[1], 16); n = int(sys.argv[2]) if len(sys.argv) > 2 else 60
o = a - 0x100000 + 0x200
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 + capstone.CS_MODE_LITTLE_ENDIAN)
for i in md.disasm(E[o:o + 4 * n], a):
    print("%x  %-8s %s" % (i.address, i.mnemonic, i.op_str))
