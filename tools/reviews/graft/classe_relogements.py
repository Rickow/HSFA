#!/usr/bin/env python3
"""classe_relogements.py -- graft review (relocation, R1-R5): classify by CONTEXT every aligned long of Upper's data
copied by the graft: relocated or left raw, nature of the value (data, file 390, code, RAM), proofs (Upper's conversion
log), sprite frame, table, reads recorded in Upper. This is the base list of the relocation review (classe.tsv); the
other relocation tools (laisses.py, tri_128.py, r3_creux.py, ctx.py) read it back.

Usage:  nice -n 19 python3 -I classe_relogements.py [frozen_build] > sorties/classe.tsv
Inputs: frozen graft build (argument or $HSFA_GRAFT_BUILD: greffe.json, greffe_donnees.bin, zone_decors.bin), module
        ro5 ($HSFA_MODULES), file 390 ($HSFA_F390), recordings of the repository's frozen copy
        (construction/releves_<state>/greffe/traces, pointeurs_prouves.txt.tsv; state = $HSFA_GRAFT_STATE, ro9a38).
Output: TSV on stdout (one line per relocated cell or raw candidate), counts on stderr. Read only. See paths.py.
After R3 (ro9a38, R3_CREUX=1 R3_CIBLES=1) the proven cells are relocated: a build with R3 on gives no "proof" family
left raw in laisses.py.
"""
import sys, os, json, struct, bisect, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
C = paths.construction(sys.argv[1] if len(sys.argv) > 1 else None)
REL = paths.REL
BASE = paths.BASE
b5 = paths.module("ro5")
h5 = struct.unpack_from('<7I', b5, 0)
CODE_END, FIN_EXEC = h5[3], h5[6]
LO, HI = BASE + CODE_END, FIN_EXEC
RAM = (FIN_EXEC + 0x7ffff) & ~0x7ffff
B390 = open(paths.chemin_f390(), "rb").read()
F390 = 0xB04000; F390_1 = F390 + len(B390)
U_DATA_BASE, U_SPLIT, U_EXT = 0xA1000, 0x8E4AE0, 0xC80000

def source(v):
    if LO <= v < HI: return 'module'
    if F390 <= v < F390_1: return '390'
    return None
def octets(v, n):
    if LO <= v < HI: return b5[v - BASE:v - BASE + n]
    return B390[v - F390:v - F390 + n]
def classe(v):
    if RAM <= v < RAM + 0x80000: return 'ram'
    if F390 <= v < F390_1: return '390'
    if HI <= v < RAM: return 'port'
    if BASE + 0x22B00 <= v < BASE + CODE_END: return 'code'
    if LO <= v < HI: return 'data'
    return None

def lu_tsv(noms):
    out = set()
    for n in noms:
        for l in open(os.path.join(paths.traces(), n), encoding="utf-8"):
            if l.startswith('#') or not l.strip(): continue
            p = l.split()[0].split('-'); a0 = int(p[0], 16); a1 = int(p[-1], 16)
            for a in range(a0, a1 + 1, 2):
                if U_DATA_BASE <= a < U_DATA_BASE + (U_SPLIT - LO): v = LO + (a - U_DATA_BASE)
                elif U_EXT <= a < U_EXT + (HI - U_SPLIT): v = U_SPLIT + (a - U_EXT)
                elif F390 <= a < F390_1: v = a
                else: continue
                out.add(v & ~1)
    return out

def main():
    J = json.load(open(os.path.join(C, "greffe.json"), encoding="utf-8"))
    blob = open(os.path.join(C, "greffe_donnees.bin"), "rb").read()
    zb = open(os.path.join(C, "zone_decors.bin"), "rb").read()
    zl, zh = int(J['zone_decors'][0], 16), int(J['zone_decors'][1], 16)
    zpad = len(zb) - (zh - zl)
    regs = [(int(a, 16), int(b, 16), int(o, 16)) for a, b, o in J['regions']]
    LU = lu_tsv(["journaux_u_lu.tsv", "journaux_defi_lu.tsv", "journaux_objets_lu.tsv"])
    PREUVES = set()
    for l in open(os.path.join(REL, "greffe", "donnees", "pointeurs_prouves.txt.tsv"), encoding="utf-8"):
        if not l.startswith('#') and l.strip(): PREUVES.add(int(l.split()[0], 16))
    # trames de type 2 (toutes tailles)
    T2 = {}
    for a in range(LO, HI - 12, 2):
        o = a - BASE
        w0, w1, w2, w3 = struct.unpack_from('<4H', b5, o)
        if w0 != 2 or w3 != 0 or w2 > 0x3FF: continue
        p = struct.unpack_from('<I', b5, o + 8)[0]
        if not (F390 <= p < F390_1): continue
        n = w2 + 1; deb = a + 12
        for c in range(deb & ~3, min(deb + 4 * n, HI), 4): T2[c] = (a, n)
    # occupation du bloc : une region logee dans le creux d'une autre masque les cases de l'hote
    inter = sorted((o, o + (b - a), a) for a, b, o in regs if not (zl <= a < zh))
    def masquee(a_reg, off):
        for o0, o1, a in inter:
            if a != a_reg and o0 <= off < o1: return True
        return False
    hotes = set()
    for a, b, o in regs:
        for o0, o1, a2 in inter:
            if a2 != a and o <= o0 and o1 <= o + (b - a): hotes.add(a)
    rows = []; st = collections.Counter()
    info = {}
    for a, b, o in regs:
        dz = zl <= a < zh
        src = octets(a, b - a)
        for i in range((-a) & 3, b - a - 3, 4):
            c = a + i
            old = struct.unpack_from('<I', src, i)[0]
            if dz: new = struct.unpack_from('<I', zb, zpad + (c - zl))[0]
            else:
                if a in hotes and masquee(a, o + i): continue
                new = struct.unpack_from('<I', blob, o + i)[0]
            info[c] = (old, new)
    cases = sorted(info)
    def lue(c): return (c in LU) or (c + 2 in LU)
    def cible_lue(p): return any(((p & ~1) + d) in LU for d in range(0, 10, 2))
    for c in cases:
        old, new = info[c]
        cl = classe(old)
        rel = old != new
        if not rel and cl not in ('data', '390', 'code'): continue
        if not rel and (old >> 16) < 0x20: continue
        tags = []
        if c in PREUVES: tags.append('preuve')
        if c in T2: tags.append('T2:%x/n=%d' % T2[c])
        v = [info.get(c - 4), info.get(c + 4)]
        nvr = sum(1 for x in v if x and x[0] != x[1] and classe(x[0]) == cl)
        nvs = sum(1 for x in v if x and classe(x[0]) == cl and (x[0] >> 16) == (old >> 16))
        if nvr: tags.append('voisin_reloge%d' % nvr)
        if nvs: tags.append('voisin_meme_haut%d' % nvs)
        if lue(c): tags.append('case_lue')
        if cl in ('data', '390') and cible_lue(old): tags.append('cible_lue')
        if old & 1: tags.append('impair')
        elif old & 3: tags.append('mod2')
        if zl <= c < zh: tags.append('zone')
        if rel and (old >> 16) == (new >> 16) and (new & 0xffff) >= 0x6C60 and (old & 0xffff) < 0x33F0: tags.append('DECOR_E0?')
        st[('RELOGE' if rel else 'LAISSE', cl)] += 1
        rows.append((c, 'RELOGE' if rel else 'LAISSE', cl, old, new, tags))
    for c, s, cl, old, new, tags in rows:
        print("%x\t%s\t%s\t%08x\t%08x\t%s" % (c, s, cl, old, new, ' '.join(tags)))
    for k, n in sorted(st.items(), key=str): print(k, n, file=sys.stderr)
    print("cases examinees", len(cases), "lu", len(LU), "preuves", len(PREUVES), "T2 cases", len(T2), "hotes", len(hotes), file=sys.stderr)
main()
