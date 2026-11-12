#!/usr/bin/env python3
"""r3_creux.py -- graft review (R3): for each PROVEN pointer left raw (laisses.txt, "preuve" families), rebuild the
cause: cell in a copied segment? distance to Upper's nearest recorded read (a bank hole = neither segment nor read
within ~$18, over >= $100); bank (T_619B50); cell in an exclusion list; target copied / reused / absent and, if absent,
distance from the target to the nearest copied region.

Usage:  nice -n 19 python3 -I r3_creux.py > sorties/r3_creux.txt
Inputs: laisses.txt of laisses.py ($HSFA_REVIEW_OUT, default ./sorties), greffe.json of the frozen build
        ($HSFA_GRAFT_BUILD), module ro5 ($HSFA_MODULES), read recordings and exclusion lists of the repository's frozen
        copy (construction/<state>/greffe, releves_<state>/; $HSFA_GRAFT_STATE, default ro9a38). Read only.
Since ro9a38 (R3_CREUX=1 R3_CIBLES=1, journal section 223) these cells are relocated: on a ro9a38 build this is a
regression check (no proven family expected in laisses.txt).
"""
import sys, json, struct, bisect, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
BASE = paths.BASE
C = paths.construction()
b5 = paths.module("ro5")
h5 = struct.unpack_from('<7I', b5, 0); CE, HI = h5[3], h5[6]; LO = BASE + CE
U_DATA_BASE, U_SPLIT, U_EXT = 0xA1000, 0x8E4AE0, 0xC80000
LU = set()
for n in ("journaux_u_lu.tsv", "journaux_defi_lu.tsv", "journaux_objets_lu.tsv"):
    for l in open(os.path.join(paths.traces(), n), encoding="utf-8"):
        if l.startswith('#') or not l.strip(): continue
        p = l.split()[0].split('-')
        for a in range(int(p[0], 16), int(p[-1], 16) + 1, 2):
            if U_DATA_BASE <= a < U_DATA_BASE + (U_SPLIT - LO): LU.add(LO + (a - U_DATA_BASE))
            elif U_EXT <= a < U_EXT + (HI - U_SPLIT): LU.add(U_SPLIT + (a - U_EXT))
LUS = sorted(LU)
J = json.load(open(os.path.join(C, "greffe.json"), encoding="utf-8"))
SEG = sorted((int(a, 16), int(a, 16) + n) for a, n in J['donnees_copiees']); SA = [a for a, b in SEG]
REG = sorted((int(a, 16), int(b, 16)) for a, b, o in J['regions']); RA = [a for a, b in REG]
RU = {int(k, 16) for k in J['donnees_reutilisees']}
TB = sorted(set(x for x in struct.unpack_from('<46I', b5, 0x619B50 - BASE) if LO <= x < HI))
EX = set()
for f in (os.path.join(paths.GREFFE, "e43", "ptr_exclus_e43.txt"), os.path.join(paths.GREFFE, "e42", "ptr_exclus_pal_att.txt"), os.path.join(paths.GREFFE, "donnees", "ptr_exclus_desc.txt")):
    if os.path.exists(f): EX |= {int(l.split()[0], 16) for l in open(f, encoding="utf-8") if l.strip() and not l.startswith('#')}
def dans(L, A, x):
    k = bisect.bisect_right(A, x) - 1
    return k >= 0 and L[k][0] <= x < L[k][1]
def dlu(c):
    k = bisect.bisect_left(LUS, c); d = [abs(LUS[j] - c) for j in (k - 1, k) if 0 <= j < len(LUS)]
    return min(d) if d else 1 << 30
def dreg(p):
    k = bisect.bisect_right(RA, p) - 1; d = []
    if k >= 0: d.append(p - REG[k][1] if p >= REG[k][1] else 0)
    if k + 1 < len(REG): d.append(-(REG[k + 1][0] - p))
    return min(d, key=abs) if d else None
st = collections.Counter(); out = []; f = None
for l in open(paths.sortie("laisses.txt"), encoding="utf-8"):
    if l.startswith('## '): f = l.split()[1] if ' preuve ' in l else None; continue
    if not f or not l.strip(): continue
    c, p = int(l.split()[0], 16), int(l.split()[1], 16)
    seg = dans(SEG, SA, c); d = dlu(c)
    kb = bisect.bisect_right(TB, c) - 1; bq = TB[kb] if kb >= 0 else 0
    cause = []
    if c in EX: cause.append('EXCLUE')
    if not seg and d > 0x18: cause.append('creux_vraisemblable')
    if f == 'cible_ABSENTE': cause.append('cible_non_copiee(dist region %+x)' % dreg(p))
    if not cause: cause.append('INEXPLIQUE')
    st[(f, cause[0].split('(')[0])] += 1
    out.append("%x %08x %s segment=%d lecture_a=%x banque=%x cible_seg=%d cible_reut=%d : %s" % (c, p, f, seg, min(d, 0xfffff), bq, dans(SEG, SA, p), p in RU, ' '.join(cause)))
for k, n in sorted(st.items()): print(n, *k)
print('\n'.join(out))
