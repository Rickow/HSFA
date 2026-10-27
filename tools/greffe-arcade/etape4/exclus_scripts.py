#!/usr/bin/env python3
"""exclus_scripts.py su_XX.txt... : a partir du pointeur du script de fin d'Upper ($8034, journaux outils/scripts_upper.sh),
les plages de SCRIPT parcourues (mots de commande) ; les longs alignes qu'elles contiennent et que le bloc de la greffe
relogerait (pointeur de donnee ou de code) sans PREUVE (conversions d'Upper) sont ajoutes a donnees/ptr_exclus.txt."""
import sys, os, struct
sys.path.insert(0, '<workspace>/work/greffe_arcade/etape2')
import donnees2 as D
EX = '<workspace>/work/greffe_arcade/donnees/ptr_exclus.txt'
deja = set(int(l.split()[0], 16) for l in open(EX) if l.strip() and not l.startswith('#'))
REFS = set(D.PL.refs_donnees5()); nouv = []
def ps2(a):
    if D.U_DATA_BASE <= a < D.U_DATA_BASE + (D.U_SPLIT - D.LO): return D.LO + (a - D.U_DATA_BASE)
    if D.U_EXT <= a < D.U_EXT + (D.HI - D.U_SPLIT): return D.U_SPLIT + (a - D.U_EXT)
    if D.F390 <= a < D.F390_1: return a
for fn in sys.argv[1:]:
    seq = []; lo = {}
    for l in open(fn):
        x = l.split(); a = x[3]; v = int(x[4], 16)
        if a == 'ff0034': lo = v
        elif a == 'ff0036' and lo != {}: seq.append(((v << 16) | lo) & 0xffffff)
    spans = set()
    for p0, p1 in zip(seq, seq[1:]):
        if 0 < p1 - p0 <= 0x40: spans.update(range(p0, p1, 2))
    perso = os.path.basename(fn).split(".")[0].split("_")[-1]; n = 0
    for a in sorted(spans):
        if a & 3 or (a + 2) not in spans: continue
        c = ps2(a)
        if c is None or c in deja or c in D.PREUVES: continue
        v = struct.unpack_from('<I', D.octets(c, 4))[0]
        if D.est_pointeur(c, v, REFS) or D.GR.classe_valeur(v, D.GR.H5) == 'code':
            nouv.append((c, perso, v)); deja.add(c); n += 1
    print("%s : %d mots de script parcourus, %d longs exclus" % (perso, len(spans), n))
with open(EX, 'a') as f:
    for c, p, v in nouv: f.write("%x  fin du perso %s : long $%08x (paire de mots de script)\n" % (c, p, v))
