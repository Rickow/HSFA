#!/usr/bin/env python3
"""atteint2.py -- graft review (transitions, E4): closure of the calls of the graft's MIPS from start routines, to tell
whether given sites (e.g. a longjmp) are reachable. Follows jal / j AND the far calls "lui r,H ; addiu r,r,L ; jalr r"
(the form of almost every JSR between Upper's copies and Hyper's code). jalr through a TABLE (lw ; jalr) are not
followed: they are counted (lower bound of what is reachable); give the table entries as start points.
Function starts = targets of jal + targets of lui/addiu/jalr + start points.

Usage:  nice -n 19 python3 -I atteint2.py START[,START...] SITE[,SITE...] [frozen_build]   (FILE offsets, hex)
Input:  ro9a_module.bin of the frozen graft build (third argument or $HSFA_GRAFT_BUILD). See paths.py.
Read only. Supersedes the review's first version (atteint.py, which did not follow the far calls).
"""
import sys, os, struct, bisect
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
C = os.path.join(paths.construction(sys.argv[3] if len(sys.argv) > 3 else None), "ro9a_module.bin")
b = open(C, "rb").read(); BASE = 0x1F0000; FIN = len(b) & ~3
dep = [int(x, 16) for x in sys.argv[1].split(',')]; sites = [int(x, 16) for x in sys.argv[2].split(',')]
W = struct.unpack_from('<%dI' % (FIN // 4), b, 0)
starts = set(dep); loin = {}          # loin[adresse du jalr] = cible fichier
lui = {}
for i, w in enumerate(W):
    a = i * 4; op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; imm = w & 0xffff
    if op == 3:
        t = ((w & 0x3ffffff) << 2) - BASE
        if 0 <= t < FIN: starts.add(t)
    elif op == 15: lui[rt] = [imm << 16, a, False]
    elif op == 9 and rs == rt and rs in lui and a - lui[rs][1] == 4:
        lui[rs] = [lui[rs][0] + (imm - 0x10000 if imm & 0x8000 else imm), a, True]
    elif op == 0 and (w & 0x3f) == 9 and rs in lui and lui[rs][2] and a - lui[rs][1] <= 8:
        t = lui[rs][0] - BASE
        if 0 <= t < FIN and t % 4 == 0: starts.add(t); loin[a] = t
S = sorted(starts)
def fin(a): k = bisect.bisect_right(S, a); return S[k] if k < len(S) else FIN
vu = set(); pile = list(dep); nj = 0; hors = set()
while pile:
    f = pile.pop()
    if f in vu: continue
    vu.add(f)
    for a in range(f, fin(f), 4):
        w = W[a // 4]; op = w >> 26; t = None
        if op in (2, 3):
            t = ((w & 0x3ffffff) << 2) - BASE
            if not 0 <= t < FIN: hors.add(t + BASE); t = None
        elif op == 0 and (w & 0x3f) == 9:
            if a in loin: t = loin[a]
            else: nj += 1
        if t is not None:
            k = bisect.bisect_right(S, t) - 1
            if S[k] not in vu: pile.append(S[k])
print("depart %s : %d fonctions atteintes (jal, j, lui/addiu/jalr), %d jalr par table non suivis, %d cibles hors module" % (sys.argv[1], len(vu), nj, len(hors)))
for s in sites:
    k = bisect.bisect_right(S, s) - 1
    print("site %x (fonction %x) : %s" % (s, S[k], "ATTEINT" if S[k] in vu else "non atteint"))
