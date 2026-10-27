"""Références code -> tables arcade, par reconstruction des paires lui/addiu|ori|lw...
(EBOOT PRX : immédiats 0-based, relogés au chargement ; VA = offset fichier - 0x74)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import json, struct, collections
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
buf = open(paths.eboot(), "rb").read()
EXEC_END = 0x2d4f30                       # filesz du segment exécutable (program header)
code = buf[0x74:0x74 + EXEC_END]
blocks = json.load(open(os.path.join(paths.CACHE, "arcade_blocks_in_eboot.json")))
def block_of(va):
    for b in blocks:
        if b["va_lo"] - 0x40 <= va < b["va_hi"]: return b
W = struct.unpack(f"<{len(code)//4}I", code[:len(code)//4*4])
refs = collections.defaultdict(list)
for i, w in enumerate(W):
    if w >> 26 != 0x0F: continue                 # lui
    rt, hi = (w >> 16) & 31, w & 0xFFFF
    for j in range(i + 1, min(i + 12, len(W))):  # le 'lo' suit de près
        x = W[j]; op = x >> 26; rs = (x >> 21) & 31
        if rs != rt: continue
        imm = x & 0xFFFF
        if op in (0x09, 0x23, 0x21, 0x25, 0x20, 0x24, 0x2B, 0x29, 0x28):   # addiu/lw/lh/lhu/lb/lbu/sw/sh/sb
            va = ((hi << 16) + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF
        elif op == 0x0D:                                                    # ori
            va = (hi << 16) | imm
        else: continue
        b = block_of(va)
        if b: refs[i * 4].append((va, b["form"], b["rom"]))
        break
def func_start(va):
    """remonte jusqu'au prologue 'addiu sp,sp,-N' le plus proche"""
    k = va // 4
    while k > 0:
        w = W[k]
        if w >> 16 == 0x27BD and w & 0x8000: return k * 4
        k -= 1
    return 0
funcs = collections.defaultdict(set)
for site, lst in refs.items():
    for va, form, rom in lst: funcs[func_start(site)].add((form, rom, va, site))
print(f"sites de référence: {len(refs)}   fonctions: {len(funcs)}")
for f, s in sorted(funcs.items(), key=lambda kv: -len(kv[1]))[:20]:
    tabs = sorted({(x[0], hex(x[1])) for x in s})
    print(f"  FUN_{f:x}: {len(s)} réf. -> {tabs[:3]}{' ...' if len(tabs) > 3 else ''}")
json.dump({hex(k): sorted([list(map(str, x)) for x in v]) for k, v in funcs.items()}, open(os.path.join(paths.CACHE, "arcade_consumers.json"), "w"), indent=1)
