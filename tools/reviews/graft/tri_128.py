#!/usr/bin/env python3
"""tri_128.py -- graft review (R3 c): sort the cells "cible_ABSENTE sans_preuve case_lue/cible_lue" of laisses.txt
(candidate pointers left raw, target not copied, no proof) into DATA (certain), POINTER (real pointer left raw) or
UNDECIDABLE, by objective criteria: odd (a pointer to 68K words is even); ASCII text; low half < $200 and not a code
constant (the graft itself does not take it for a pointer: est_pointeur); small-word neighbourhood (>= 6 of the 8
surrounding words < $400); exact target read by Upper; target = constant of Upper's code; pointer neighbours (table).

Usage:  nice -n 19 python3 -I tri_128.py > sorties/tri_128.txt
Inputs: laisses.txt ($HSFA_REVIEW_OUT, default ./sorties), module ro5 ($HSFA_MODULES), file 390 ($HSFA_F390), read
        recordings of the repository's frozen copy (releves_<state>/greffe/traces). Read only. See paths.py.
Review result (ro9a37): 128 cells, 0 pointer.
"""
import sys, struct, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
BASE = paths.BASE
b5 = paths.module("ro5")
h5 = struct.unpack_from('<7I', b5, 0); CE, HI = h5[3], h5[6]; LO = BASE + CE
F390 = 0xB04000; F390_1 = F390 + os.path.getsize(paths.chemin_f390())
U_DATA_BASE, U_SPLIT, U_EXT = 0xA1000, 0x8E4AE0, 0xC80000
LU = set()
for n in ("journaux_u_lu.tsv", "journaux_defi_lu.tsv", "journaux_objets_lu.tsv"):
    for l in open(os.path.join(paths.traces(), n), encoding="utf-8"):
        if l.startswith('#') or not l.strip(): continue
        p = l.split()[0].split('-')
        for a in range(int(p[0], 16), int(p[-1], 16) + 1, 2):
            if U_DATA_BASE <= a < U_DATA_BASE + (U_SPLIT - LO): LU.add(LO + (a - U_DATA_BASE))
            elif U_EXT <= a < U_EXT + (HI - U_SPLIT): LU.add(U_SPLIT + (a - U_EXT))
            elif F390 <= a < F390_1: LU.add(a)
# constantes de donnees formees par le code d'Upper (lui + addiu/ori/acces)
REFS = set(); lui = {}
for a in range(0x20, CE, 4):
    w = struct.unpack_from('<I', b5, a)[0]; op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; imm = w & 0xffff
    simm = imm - 0x10000 if imm & 0x8000 else imm
    if op == 15: lui[rt] = (imm << 16, a); continue
    if op in (9, 13, 32, 33, 35, 36, 37, 40, 41, 43) and rs in lui and a - lui[rs][1] <= 48:
        REFS.add((lui[rs][0] + (imm if op == 13 else simm)) & 0xffffffff)
    if op in (9, 13) and rt != rs: lui.pop(rt, None)
def W16(a): return struct.unpack_from('<H', b5, a - BASE)[0]
def L32(a): return struct.unpack_from('<I', b5, a - BASE)[0]
def src(v): return LO <= v < HI or F390 <= v < F390_1
cases = []; f = False
for l in open(paths.sortie("laisses.txt"), encoding="utf-8"):
    if l.startswith('## '): f = l.startswith('## cible_ABSENTE sans_preuve case_lue/cible_lue'); continue
    if f and l.strip(): cases.append((int(l.split()[0], 16), int(l.split()[1], 16)))
st = collections.Counter(); out = []
for c, p in cases:
    r = []; lo, hi = p & 0xffff, p >> 16
    b = b5[c - BASE - 5:c - BASE + 4]
    autour = [W16(c + d) for d in (-8, -6, -4, -2, 4, 6, 8, 10)]
    petits = sum(1 for x in autour if x < 0x400 or x >= 0xFC00)
    vois = [L32(c + d) for d in (-4, 4)]
    tab = sum(1 for q in vois if src(q) and not q & 1 and (q & 0xffff) >= 0x200)
    lu2 = (c in LU, (c + 2) in LU)                      # les deux mots du long lus ?
    if p & 1: r.append('impair')
    if all(0x20 <= x <= 0x7E for x in b[5:8]) and b[8] == 0 or sum(1 for x in b[:8] if 0x20 <= x <= 0x7E) >= 7: r.append('texte')
    if lo < 0x200 and p not in REFS: r.append('bas<200')
    if lo >= 0xFE00: r.append('bas_signe')
    if petits >= 6: r.append('petits_mots%d' % petits)
    if lu2 != (True, True): r.append('un_seul_mot_lu')
    pos = []
    if p in REFS: pos.append('cible=const_code')
    if (p & ~1) in LU: pos.append('cible_exacte_lue')
    if tab: pos.append('voisin_ptr%d' % tab)
    certain = [x for x in r if x in ('impair', 'texte', 'un_seul_mot_lu') or x.startswith('petits')]
    if certain and not (('cible=const_code' in pos) and tab): v = 'DONNEE'
    elif r and not tab and 'cible=const_code' not in pos: v = 'DONNEE_PROBABLE'
    elif tab and not r: v = 'POINTEUR_PROBABLE'
    else: v = 'INDECIDABLE'
    st[v] += 1
    out.append("%x %08x %-17s %s | %s | %s" % (c, p, v, ' '.join(r) or '-', ' '.join(pos) or '-', ' '.join('%04x' % x for x in autour[:4]) + ' [%04x %04x] ' % (lo, hi) + ' '.join('%04x' % x for x in autour[4:])))
print("# tri des %d cases (voir la docstring) :" % len(cases), dict(st))
print('\n'.join(out))
