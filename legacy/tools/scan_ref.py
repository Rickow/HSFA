#!/usr/bin/env python3
"""Scanne le dump EE (MIPS R5900 LE) pour le code référençant une constante VA (ex 0xb674f8).
Repère les paires lui/ori|addiu|lw|sw qui composent l'adresse. Sort les VA d'instruction."""
import sys, struct
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

dump = sys.argv[1]
target = int(sys.argv[2], 0)
data = open(dump, "rb").read()
hi = (target >> 16) & 0xffff
lo = target & 0xffff
# si lo a le bit 15, l'assembleur ajuste hi de +1 (extension de signe du addiu/lw/sw)
hi_adj = (hi + 1) & 0xffff if (lo & 0x8000) else hi

md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
md.detail = False

# 1) trouver tous les lui reg, hi ou hi_adj
lui_sites = {}   # va -> reg
for off in range(0, len(data) - 4, 4):
    w = struct.unpack_from("<I", data, off)[0]
    if (w >> 26) == 0x0f:  # lui
        rt = (w >> 16) & 0x1f
        imm = w & 0xffff
        if imm in (hi, hi_adj):
            lui_sites[off] = (rt, imm)

# 2) pour chaque lui, chercher dans les 12 instr suivantes un ori/addiu/lw/sw avec lo et même reg base
hits = []
for off, (rt, imm) in lui_sites.items():
    for k in range(1, 16):
        o2 = off + k*4
        if o2 + 4 > len(data): break
        w = struct.unpack_from("<I", data, o2)[0]
        opc = w >> 26
        rs = (w >> 21) & 0x1f
        imm2 = w & 0xffff
        if rs == rt and imm2 in (lo, lo & 0xffff):
            if opc in (0x0d, 0x09, 0x23, 0x2b, 0x21, 0x25):  # ori/addiu/lw/sw/lh/lhu
                hits.append((0x0 + o2, off, opc))
                break

print("cible %#x : hi=%#x hi_adj=%#x lo=%#x" % (target, hi, hi_adj, lo))
print("%d sites lui candidats, %d paires complètes:" % (len(lui_sites), len(hits)))
opname = {0x0d:'ori',0x09:'addiu',0x23:'lw',0x2b:'sw',0x21:'lh',0x25:'lhu'}
for va, luiva, opc in sorted(hits):
    print("  instr @%#010x (lui @%#x) %s" % (va, luiva, opname.get(opc, hex(opc))))
