"""Sites de code qui construisent une adresse (lui+addiu/ori/load) dans [lo,hi)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import sys, struct
b = open(paths.eboot(),"rb").read()
W = struct.unpack_from(f"<{0x2d4f30//4}I", b, 0x74)
def xrefs(lo, hi):
    out = []
    for i, w in enumerate(W):
        if w >> 26 != 0x0F: continue
        rt, hi16 = (w >> 16) & 31, w & 0xFFFF
        for j in range(i+1, min(i+16, len(W))):
            x = W[j]; op = x >> 26
            if ((x >> 21) & 31) != rt: continue
            imm = x & 0xFFFF
            if op == 0x0D: va = (hi16 << 16) | imm
            elif op in (0x09,0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2B): va = ((hi16 << 16) + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF
            else: continue
            if lo <= va < hi: out.append((j*4, va))
            break
    return out
def func_start(va):
    k = va // 4
    while k > 0:
        if W[k] >> 16 == 0x27BD and W[k] & 0x8000: return k*4
        k -= 1
    return 0
if __name__ == "__main__":
    lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    for site, va in xrefs(lo, hi):
        print(f"  site {site:#x} -> {va:#x}   fonction ~{func_start(site):#x}")
