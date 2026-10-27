"""Accès mémoire à adresse absolue (lui rX,hi puis lw/lh/sh/sw/lb/sb d(rX) dans la foulée),
regroupés par adresse. Un moteur 68K recompilé à la Anthology concentre des milliers d'accès
sur quelques slots fixes (banc de registres 68K émulé) ; du C natif garde ses variables
en registres et n'a que des globales ordinaires."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import sys, struct, collections
LS = {0x20:"lb",0x24:"lbu",0x21:"lh",0x25:"lhu",0x23:"lw",0x28:"sb",0x29:"sh",0x2B:"sw"}
def absolute_accesses(path, lo=0, hi=None):
    b = open(path, "rb").read()[lo:hi]
    W = struct.unpack(f"<{len(b)//4}I", b[:len(b)//4*4])
    c = collections.Counter(); n = 0
    for i, w in enumerate(W):
        if w >> 26 != 0x0F: continue
        rt, up = (w >> 16) & 31, (w & 0xFFFF) << 16
        x = W[i+1] if i + 1 < len(W) else 0
        if (x >> 26) in LS and ((x >> 21) & 31) == rt:
            imm = x & 0xFFFF; imm -= 0x10000 if imm & 0x8000 else 0
            c[(up + imm) & 0xFFFFFFFF] += 1; n += 1
    return c, n, len(W)
for path, label, lo, hi in [
    (paths.eboot(), "PSP SFA3 MAX", 0x74, 0x74 + 0x2d4f30),
    (paths.ee_hyper(), "Anthology (Hyper SFA)", 0x100000, 0x800000),
]:
    c, n, nw = absolute_accesses(path, lo, hi)
    top = c.most_common(6); top6 = sum(v for _, v in top)
    print(f"{label:<22} accès absolus: {n:6}  |  top 6 adresses = {top6:6} accès ({100*top6/max(n,1):4.1f} %)")
    for a, v in top: print(f"      {a:#010x}  x{v}")
