"""Signatures d'un moteur 68K recompilé, comptées sur des mots MIPS bruts.
 xor1   : xori rX,rY,1 suivi (<=2 instr.) d'un lb/lbu/sb dont la base est rX
          -> accès octet sur une RAM 68K stockée en mots 16 bits little-endian
 wsb    : wsbh/wsbw (Allegrex uniquement) -> relecture de données big-endian
 ffmask : lui rX,0x00FF puis ori rX,rX,0xFFFF -> masque d'adresse 24 bits du 68K"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import sys, struct
def count(path, lo=0, hi=None):
    b = open(path, "rb").read()[lo:hi]
    W = struct.unpack(f"<{len(b)//4}I", b[:len(b)//4*4])
    x1 = ws = ff = 0
    for i, w in enumerate(W):
        op = w >> 26
        if op == 0x0E and (w & 0xFFFF) == 1:                     # xori rt,rs,1
            rt = (w >> 16) & 31
            for x in W[i+1:i+3]:
                if (x >> 26) in (0x20, 0x24, 0x28) and ((x >> 21) & 31) == rt: x1 += 1; break
        elif op == 0x1F and (w & 0x7FF) in (0x0A0, 0x0E0):      # SPECIAL3/BSHFL wsbh, wsbw
            ws += 1
        elif op == 0x0F and (w & 0xFFFF) == 0x00FF:             # lui 0x00ff
            rt = (w >> 16) & 31
            for x in W[i+1:i+3]:
                if x >> 26 == 0x0D and (x & 0xFFFF) == 0xFFFF and ((x >> 21) & 31) == rt: ff += 1; break
    return len(W), x1, ws, ff
for path, label, lo, hi in [
    (paths.eboot(), "PSP SFA3 MAX (segment code)", 0x74, 0x74 + 0x2d4f30),
    (paths.ee_std(), "Anthology ee_std (EE 32 Mo)", 0, None),
    (paths.ee_hyper(), "Anthology ee_hyper (EE 32 Mo)", 0, None),
]:
    n, x1, ws, ff = count(path, lo, hi)
    print(f"{label:<31} mots={n:>9}  xor1-octet={x1:6}  wsbh/wsbw={ws:4}  masque24={ff:4}")
