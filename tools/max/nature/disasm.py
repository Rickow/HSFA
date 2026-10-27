import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import sys, struct
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
buf = open(paths.eboot(), "rb").read()
md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN); md.skipdata = True
def func_bytes(va, maxlen=0x1000):
    """du prologue jusqu'au prologue suivant"""
    k = va + 4
    while k < va + maxlen:
        w = struct.unpack_from("<I", buf, 0x74 + k)[0]
        if w >> 16 == 0x27BD and w & 0x8000: break
        k += 4
    return buf[0x74 + va:0x74 + k]
for a in sys.argv[1:]:
    va = int(a, 16); code = func_bytes(va)
    print(f"===== FUN_{va:x}  ({len(code)//4} instructions)")
    for ins in md.disasm(code, va):
        print(f"  {ins.address:06x}  {ins.mnemonic:<8} {ins.op_str}")
