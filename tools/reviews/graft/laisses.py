#!/usr/bin/env python3
"""laisses.py -- graft review (R3): candidate pointers LEFT RAW by the graft (from classe.tsv): target copied
(deliberate exclusion?) or not copied (data not followed: Upper's raw pointer would be converted as an address of
Hyper), crossed with the proofs (Upper's conversion log) and Upper's recorded reads.

Usage:  python3 -I laisses.py > sorties/laisses.txt
Inputs: classe.tsv of classe_relogements.py ($HSFA_REVIEW_OUT, default ./sorties), greffe.json of the frozen build
        ($HSFA_GRAFT_BUILD; use the SAME build as for classe.tsv).
Output: counts per (target, proof, read) family, then the lists of the proven families and of the read/read
        families. Read only. See paths.py. The "preuve" families are what R3 fixed (142 cells in ro9a37).
"""
import sys, os, json, bisect, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
J = json.load(open(os.path.join(paths.construction(), "greffe.json"), encoding="utf-8"))
R = sorted((int(a, 16), int(b, 16)) for a, b, o in J['regions']); RA = [a for a, b in R]
RU = {int(k, 16) for k in J['donnees_reutilisees']}
def copie(p):
    k = bisect.bisect_right(RA, p) - 1
    return k >= 0 and R[k][0] <= p < R[k][1]
st = collections.Counter(); L = collections.defaultdict(list)
for l in open(paths.sortie("classe.tsv"), encoding="utf-8"):
    c, s, cl, old, new, t = l.rstrip('\n').split('\t')
    if s != 'LAISSE' or cl not in ('data', '390') or 'T2' in t: continue
    p = int(old, 16)
    ou = 'cible_copiee' if copie(p) else 'cible_reutilisee' if p in RU else 'cible_ABSENTE'
    pr = 'preuve' if 'preuve' in t else 'sans_preuve'
    lu = ('case_lue' if 'case_lue' in t else '-') + '/' + ('cible_lue' if 'cible_lue' in t else '-')
    k = (ou, pr, lu); st[k] += 1; L[k].append((c, old, t))
for k, n in sorted(st.items()): print(n, *k)
for k in sorted(L):
    if k[1] == 'preuve' or (k[2] == 'case_lue/cible_lue' and k[0] != 'cible_copiee'):
        print("\n## %s %s %s (%d)" % (k + (len(L[k]),)))
        for c, old, t in L[k][:400]: print(c, old, t)
