#!/usr/bin/env python3
"""champ_sites.py MOD DEP [DEP...] : sites MIPS qui lisent/ecrivent le champ d(An) (numerotation PS2) via une case
registre A0-A6, avec la routine et sa classe vs l'autre module."""
import os, sys, pickle
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
mod = sys.argv[1]; deps = [int(x, 16) for x in sys.argv[2:]]
L = [x for x in C.instrs(mod) if x.va >= C.start68k(mod)]
regs = {}
for x in L:
    if x.m == 'lw' and 0x1100 <= x.imm <= 0x1118: regs[x.rt] = (x.imm - 0x1100) // 4; continue
    if x.m in ('lb', 'lbu', 'sb', 'lh', 'lhu', 'sh', 'lw', 'sw') and x.rs in regs and x.imm in deps:
        print("%s %07x %-4s $%X(A%d)  routine %x" % (mod, x.va, x.m, x.imm, regs[x.rs], C.func_of(mod, x.va)[0]))
    d = x.rt if x.m in ('lb','lbu','lh','lhu','lw','andi','lui','ori','addiu') else (x.rd if x.op == 0 else None)
    if d is not None: regs.pop(d, None)
