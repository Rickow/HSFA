#!/usr/bin/env python3
"""index_tables.py -- graft review, axis 3: INDEX of the data tables read by Upper's grafted code, by the Upper routines
sent back to their Hyper homologue, and by Hyper's code (static analysis of the recompiler's MIPS, no emulator).

Method: LINEAR symbolic execution of each routine (68K register slots at 0x70001100.., MIPS temporaries, stack slots).
A memory read whose address = data constant + rest is a TABLE ACCESS; the rest is the INDEX, described by its leaves
(fields "$off(An)" in PS2 numbering: 68K byte = PS2 XOR 1), its masks (andi), its shifts (sll, mult by a constant) and
its range. The "CMP" are the subtractions of a constant seen earlier in the routine on a leaf of the index
(indicative: dominance is NOT proven). Size of a table = distance to the next data constant built by the code of the
same module (upper bound).

Output (stdout):
  A. SHARED Hyper tables: read by a copy of Upper (graft block, or stub) AND by Hyper's code; index signature on both
     sides; DIFF if a signature of the copy exists in no Hyper reader, DEBORD if the index range exceeds the size;
  B. Upper routines sent back to the Hyper homologue (decision HYPER; P = in the HOM_PARTAGES list): paired tables
     (donnees_reutilisees + homologues.tsv) whose index signature differs between Upper and the homologue;
  C. tables indexed by the character id ($102 id with version, $116 base character; PS2) read by the grafted code:
     size in entries, and what is read at the MAX ids $26 $27 $28 $29 $2D $2E (inside / OUTSIDE the table);
  D. tables named by the review report (T_BASE, grid, T_61BE10, T_72BDF0, T_619B50, T_614aa0 / T_5c5120): readers.
What the tool does NOT see: tables reached through a pointer read from memory (table of tables, A register received
as argument), an index that crosses a call (JSR) or a loop head (rendered "?"), joins of diverging paths ("@j"),
accesses by the port's C helpers. A "?" index is not judged. Upper's and Hyper's (A5) offsets are not comparable in
section B (A5 relocation): they are rendered "$..(A5)". The 29 synthetic stubs are not seen.
For the full per-id inventory of the MAX characters, see ../max-tables/ (maitre.py, TABLES.tsv).

Usage:  nice -n 19 python3 -I index_tables.py [frozen_build] > sorties/index_tables.txt   (about 1 to 2 min)
Inputs: module ro5 ($HSFA_MODULES), frozen graft build (argument or $HSFA_GRAFT_BUILD: ro9a_module.bin, greffe.json,
        b9/carte_image.txt), file 390 ($HSFA_F390), repository's frozen copy (<state>/greffe/e35/hom_partages_50.txt,
        releves_<state>/greffe/donnees/homologues.tsv; $HSFA_GRAFT_STATE, default ro9a38). Read only. See paths.py.
"""
import sys, os, json, struct, bisect, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))   # src/hsfa of the repository (= paths.SRC_HSFA)
from mips import Ins
C = paths.construction(sys.argv[1] if len(sys.argv) > 1 else None)
BASE = paths.BASE
IDS_MAX = (0x26, 0x27, 0x28, 0x29, 0x2D, 0x2E)
CHAMPS_ID = {0x102: "id", 0x116: "base"}

# ---------------------------------------------------------------- expressions : (etiquette, profondeur, ...)
U = ('?', 0)
def K(v): return ('c', 0, v & 0xffffffff)
def Rg(n): return ('r', 0, n)
PMAX = 14
def mk(tag, *a):
    d = 1 + max([x[1] for x in a if isinstance(x, tuple)] or [0])
    return U if d > PMAX else (tag, d) + a
def sgn(v): return v - (1 << 32) if v & 0x80000000 else v
def add(a, b):
    if a[0] == 'c' and b[0] == 'c': return K(a[2] + b[2])
    if a[0] == 'c' and a[2] == 0: return b
    if b[0] == 'c' and b[2] == 0: return a
    if a is U or b is U:
        o = b if a is U else a                      # garde la constante de donnees : la table reste connue, index « ? »
        return mk('add', o, U) if o[0] == 'c' else U
    return mk('add', a, b)
def low(v, bits, signed):
    if v[0] == 'c':
        x = v[2] & ((1 << bits) - 1)
        if signed and x >> (bits - 1): x -= 1 << bits
        return K(x)
    if v[0] == 'ins':
        b = v[2]
        if b >= bits: return low(v[3], bits, signed)
        return mk('ins', b, v[3], low(v[4], bits, signed))
    if v[0] == 'ext' and v[3] <= bits: return v
    if v[0] == 'f' and v[4] * 8 <= bits: return v
    if v is U: return U
    return mk('ext', v, bits, signed)
def rng(e):
    """plage (min, max) de la valeur, ou None ; octets et mots pris non signes (ids, compteurs)"""
    t = e[0]
    if t == 'c': v = sgn(e[2]); return (v, v)
    if t == 'f' or t == 'tv':
        sz = e[4] if t == 'f' else e[3]
        return (0, (1 << (8 * sz)) - 1) if sz <= 2 else None
    if t == 'ext':
        r = rng(e[2]); m = (1 << e[3]) - 1
        return r if r and 0 <= r[0] and r[1] <= m else (0, m)
    if t == 'and':
        r = rng(e[2]); m = e[3]
        return (0, min(m, r[1]) if r and r[0] >= 0 else m)
    if t == 'shl':
        r = rng(e[2]); return (r[0] << e[3], r[1] << e[3]) if r else None
    if t == 'mul':
        r = rng(e[2]); return (r[0] * e[3], r[1] * e[3]) if r else None
    if t == 'shr':
        r = rng(e[2]); return (r[0] >> e[3], r[1] >> e[3]) if r and r[0] >= 0 else None
    if t == 'add':
        a, b = rng(e[2]), rng(e[3]); return (a[0] + b[0], a[1] + b[1]) if a and b else None
    if t == 'ins':
        b = e[2]; m = (1 << b) - 1; r = rng(e[3]); lo = (0, min(m, r[1])) if r and r[0] >= 0 else (0, m)
        o = e[4]
        if o[0] == 'c': h = o[2] & ~m & 0xffff; return (lo[0] + h, lo[1] + h)
        ro = rng(o)
        return lo if (ro and 0 <= ro[0] and ro[1] <= m) else (lo[0], lo[1], 'haut?')
    return None
def masque(e):
    """plus grande valeur permise par les MASQUES et constantes du code (None : rien ne borne l'index que sa largeur)"""
    t = e[0]
    if t == 'c': return max(sgn(e[2]), 0)
    if t == 'and':
        m = masque(e[2]); return e[3] if m is None else min(m, e[3])
    if t == 'ext': return masque(e[2])
    if t in ('shl', 'mul', 'shr'):
        m = masque(e[2])
        return None if m is None else (m << e[3] if t == 'shl' else m * e[3] if t == 'mul' else m >> e[3])
    if t == 'add':
        a, b = masque(e[2]), masque(e[3]); return None if a is None or b is None else a + b
    if t == 'ins':
        a = masque(e[3]); m = (1 << e[2]) - 1
        if a is None: return None
        o = e[4]
        if o[0] == 'c': return min(a, m) + (o[2] & ~m & 0xffff)
        return min(a, m)                            # octet haut suppose nul (signale par « haut de »)
    return None
import re
def norme(d): return re.sub(r'\{haut de [^}]*\}', '', re.sub(r'[~@][a-z]?', '', d))
def desc(e, a5=False):
    t = e[0]
    if t == 'c': return '#$%x' % e[2] if e[2] < 0x80000000 else '#-$%x' % ((-e[2]) & 0xffffffff)
    if t == 'r': return e[2]
    if t == '?': return '?'
    if t == 'f':
        b = e[2]; bn = b[2] if b[0] == 'r' else '[' + desc(b, a5) + ']'
        if a5 and bn.startswith('A5'): return '$..(A5).' + 'bwl'[e[4] >> 1]
        return '$%x(%s).%s' % (e[3] & 0xffff, bn, 'bwl'[e[4] >> 1])
    if t == 'tv': return 'T_%x[]' % e[2]
    if t == 'm': return '[$%x]' % e[2]
    if t == 'ext': return desc(e[2], a5)
    if t == 'and': return '(%s & $%x)' % (desc(e[2], a5), e[3])
    if t == 'shl': return '(%s << %d)' % (desc(e[2], a5), e[3])
    if t == 'shr': return '(%s >> %d)' % (desc(e[2], a5), e[3])
    if t == 'mul': return '(%s * $%x)' % (desc(e[2], a5), e[3])
    if t == 'add': return '%s + %s' % (desc(e[2], a5), desc(e[3], a5))
    if t == 'ins':
        ro = rng(e[4]); m = (1 << e[2]) - 1
        if e[4][0] == 'c' and not (e[4][2] & ~m & 0xffff): return desc(e[3], a5)
        if ro and len(ro) == 2 and 0 <= ro[0] and ro[1] <= m: return desc(e[3], a5)
        return '%s{haut de %s}' % (desc(e[3], a5), desc(e[4], a5))
    return t
def feuilles(e, out=None):
    if out is None: out = set()
    t = e[0]
    if t == 'f':
        b = e[2]
        out.add((e[3] & 0xffff, e[4], b[2].split('~')[0].split('@')[0] if b[0] == 'r' else '*'))
        if b[0] != 'r': feuilles(b, out)
    else:
        for x in e[2:]:
            if isinstance(x, tuple): feuilles(x, out)
    return out
def evalue(e, ident):
    """valeur de l'index quand la feuille id (champ $102 / $116 d'un joueur) vaut ident, les autres feuilles a 0"""
    t = e[0]
    if t == 'c': return sgn(e[2])
    if t == 'f': return ident if (e[3] & 0xffff) in CHAMPS_ID and e[4] == 1 else 0
    if t in ('?', 'r', 'tv', 'm'): return 0
    if t == 'ext': return evalue(e[2], ident)
    if t == 'and': return evalue(e[2], ident) & e[3]
    if t == 'shl': return evalue(e[2], ident) << e[3]
    if t == 'shr': return evalue(e[2], ident) >> e[3]
    if t == 'mul': return evalue(e[2], ident) * e[3]
    if t == 'add': return evalue(e[2], ident) + evalue(e[3], ident)
    if t == 'ins':
        m = (1 << e[2]) - 1; return (evalue(e[3], ident) & m) | (evalue(e[4], ident) & ~m & 0xffff)
    return 0
ENTREE = {'D%d' % i for i in range(8)}
def reg_entree(e, out=None):
    """registres D lus tels qu'a l'ENTREE de la routine (arguments)"""
    if out is None: out = set()
    if e[0] == 'r':
        if e[2] in ENTREE: out.add(e[2])
    else:
        for x in e[2:]:
            if isinstance(x, tuple): reg_entree(x, out)
    return out
def subst(e, env):
    if e[0] == 'r': return env.get(e[2], e) if e[2] in ENTREE else e
    if e[0] in ('c', '?', 'tv', 'm'): return e
    return (e[0], e[1]) + tuple(subst(x, env) if isinstance(x, tuple) else x for x in e[2:])
def decompose(e):
    """(constante ou None, [termes]) d'une somme"""
    if e[0] == 'c': return e[2], []
    if e[0] == 'add':
        c1, t1 = decompose(e[2]); c2, t2 = decompose(e[3])
        if c1 is not None and c2 is not None: return (c1 + c2) & 0xffffffff, t1 + t2
        return (c1 if c1 is not None else c2), t1 + t2
    return None, [e]

def nom_case(off):
    if 0x1100 <= off <= 0x111c: return 'A%d' % ((off - 0x1100) >> 2)
    if off == 0x1120: return 'A8'
    if 0x1124 <= off <= 0x1140: return 'D%d' % ((off - 0x1124) >> 2)
    if off == 0x1144: return 'D8'
    return 'S%x' % off
TEMPS = list(range(1, 16)) + [24, 25, 31]
LD = {'lb': (1, True), 'lbu': (1, False), 'lh': (2, True), 'lhu': (2, False), 'lw': (4, True)}
ST = {'sb': 1, 'sh': 2, 'sw': 4}
BRANCH = ('beq', 'bne', 'blez', 'bgtz', 'beql', 'bnel', 'bltz', 'bgez')

class Analyse:
    """acces aux tables d'un module : self.acc = [(site, table, disp, taille, index, routine, cmps)]"""
    def __init__(s, buf, plages, est_donnee, departs_plus=()):
        s.buf, s.plages, s.est_donnee = buf, plages, est_donnee
        s.acc = []; s.consts = set(); s.directs = collections.Counter(); s.appels = collections.defaultdict(list)
        L = {}
        for a, b in plages:
            for o in range(a, b, 4): L[o] = Ins(o, struct.unpack_from('<I', buf, o)[0])
        s.L = L
        dep = set(departs_plus) | {a for a, b in plages}; boucles = set()
        for o, x in L.items():
            if x.m == 'jal':
                t = x.tgt - BASE
                if t in L: dep.add(t)
            elif x.m == 'j':
                t = x.tgt - BASE
                if t in L and t <= o: boucles.add(t)
            elif x.m in BRANCH:
                t = o + 4 + x.simm * 4
                if t <= o: boucles.add(t)
        s.dep, s.boucles = dep, boucles
        for a, b in plages: s.passe(a, b)
        # table = constante de BASE (lui + addiu) la plus proche en dessous ; l'ecart passe dans le deplacement
        Cs = sorted(s.consts); out = []
        for (o, c, disp, sz, idx, rout, cm) in s.acc:
            if c not in s.consts:
                k = bisect.bisect_right(Cs, c) - 1
                if k >= 0 and c - Cs[k] < 0x1000: disp += c - Cs[k]; c = Cs[k]
                else: s.consts.add(c); Cs = sorted(s.consts)
            out.append((o, c, disp, sz, idx, rout, cm))
        s.acc = out
    def raz(s):
        s.R = [U] * 32; s.R[0] = K(0); s.R[29] = Rg('sp')
        s.S = {}; s.SP = {}; s.pend = {}; s.cmps = []; s.LO = U
    def case(s, off):
        v = s.S.get(off)
        return v if v is not None else Rg(nom_case(off))
    def opaque(s, tag, adr=False):
        R = s.R
        for i in TEMPS: R[i] = U
        for off in list(s.S):
            n = nom_case(off)
            if n[0] == 'D' or n[0] == 'S' or (adr and s.S[off][0] != 'r'): s.S[off] = Rg(n + tag)
        for off in range(0x1124, 0x1148, 4): s.S[off] = Rg(nom_case(off) + tag)
    def passe(s, a, b):
        L = s.L; R = None; s.raz(); R = s.R
        mort = False; apres = None; rout = a
        for o in range(a, b, 4):
            x = L[o]
            if o in s.dep: s.raz(); R = s.R; mort = False; rout = o
            else:
                p = s.pend.pop(o, None)
                if o in s.boucles: s.opaque('@b')
                elif p is not None:
                    if mort: s.R, s.S, s.SP = p[0][:], dict(p[1]), dict(p[2]); R = s.R
                    else:
                        pr, ps, pp = p
                        for i in range(1, 32):
                            if R[i] is not pr[i] and R[i] != pr[i]: R[i] = U
                        for off in set(ps) | set(s.S):
                            va, vb = s.S.get(off), ps.get(off)
                            if va is not vb and va != vb: s.S[off] = Rg(nom_case(off) + '@j')
                        s.SP = {k: v for k, v in s.SP.items() if pp.get(k) == v}
                elif mort: s.opaque('@x')
                if p is not None or o in s.boucles: mort = False
            fait = apres; apres = None
            m = x.m
            base_lui = R[x.rs][0] == 'c' and not (R[x.rs][2] & 0xffff)      # registre = « lui » pur : constante de BASE
            if x.w == 0: pass
            elif m == 'lui': R[x.rt] = K(x.imm << 16)
            elif m in ('addiu', 'addi'):
                if x.rt: R[x.rt] = add(R[x.rs], K(x.simm))
                if R[x.rt][0] == 'c' and s.est_donnee(R[x.rt][2]) and x.rs and base_lui: s.consts.add(R[x.rt][2])
            elif m == 'ori':
                v = R[x.rs]
                R[x.rt] = K(v[2] | x.imm) if v[0] == 'c' else (v if x.imm == 0 else U)
                if R[x.rt][0] == 'c' and s.est_donnee(R[x.rt][2]) and x.rs and base_lui: s.consts.add(R[x.rt][2])
            elif m == 'andi':
                v = R[x.rs]; R[x.rt] = K(v[2] & x.imm) if v[0] == 'c' else (U if v is U else mk('and', v, x.imm))
            elif m in ('slti', 'sltiu'):
                f = feuilles(R[x.rs])
                if f: s.cmps.append((o, f, x.simm & 0xffff))
                R[x.rt] = U
            elif m in LD:
                sz, sg = LD[m]; bs = R[x.rs]; v = U
                if bs[0] == 'c':
                    ad = (bs[2] + x.simm) & 0xffffffff
                    if 0x70001100 <= ad < 0x70001200:
                        off = ad - 0x70000000
                        if off & 3: v = U
                        else:
                            c = s.case(off); v = c if sz == 4 else low(c, sz * 8, sg)
                    elif s.est_donnee(ad):
                        if base_lui: s.consts.add(ad)
                        s.directs[ad] += 1; v = ('m', 0, ad, sz)
                elif bs[0] == 'r' and bs[2] == 'sp':
                    w = s.SP.get(x.simm)
                    if w is not None: v = w[0] if w[1] == sz else low(w[0], min(sz, w[1]) * 8, sg)
                else:
                    c, T = decompose(bs)
                    if c is not None and s.est_donnee(c):
                        idx = None
                        for t in T: idx = t if idx is None else add(idx, t)
                        f = feuilles(idx) if idx is not None else set()
                        cm = sorted({k for (so, ff, k) in s.cmps if ff & f})[:4] if f else []
                        s.acc.append((o, c, x.simm, sz, idx if idx is not None else K(0), rout, tuple(cm)))
                        v = ('tv', 0, c, sz)
                    elif bs is not U: v = mk('f', bs, x.simm, sz)
                if x.rt: R[x.rt] = v
            elif m in ST:
                sz = ST[m]; bs = R[x.rs]; v = R[x.rt]
                if bs[0] == 'c':
                    ad = (bs[2] + x.simm) & 0xffffffff
                    if 0x70001100 <= ad < 0x70001200:
                        off = ad - 0x70000000
                        if off & 3: s.S[off & ~3] = Rg(nom_case(off & ~3) + '@p')
                        elif sz == 4: s.S[off] = v
                        else:
                            old = s.case(off)
                            while old[0] == 'ins' and old[2] <= sz * 8: old = old[4]
                            s.S[off] = mk('ins', sz * 8, v, old)
                elif bs[0] == 'r' and bs[2] == 'sp': s.SP[x.simm] = (v, sz)
            elif m in ('ld', 'lq', 'lwl', 'lwr'):
                if x.rt: R[x.rt] = U
            elif m in ('sd', 'sq', 'swl', 'swr'): pass
            elif m == 'jal' or m == 'jalr':
                apres = 'appel'
                if m == 'jal': s.appels[x.tgt - BASE].append((o, {nom_case(k): v for k, v in s.S.items() if 0x1124 <= k <= 0x1140}))
            elif m == 'j' or m == 'jr':
                if m == 'j':
                    t = x.tgt - BASE
                    if t > o and t in L: s.pend.setdefault(t, (R[:], dict(s.S), dict(s.SP)))
                apres = 'mort'
            elif m in BRANCH:
                t = o + 4 + x.simm * 4
                if t > o: s.pend.setdefault(t, (R[:], dict(s.S), dict(s.SP)))
                if m == 'beq' and x.rs == 0 and x.rt == 0: apres = 'mort'
            elif x.op == 0:
                rd = x.rd; a_, b_ = R[x.rs], R[x.rt]; v = U
                if m in ('addu', 'add'): v = add(a_, b_)
                elif m in ('subu', 'sub'):
                    if b_[0] == 'c':
                        f = feuilles(a_)
                        if f: s.cmps.append((o, f, b_[2] & 0xffff))
                        v = add(a_, K(-b_[2]))
                    elif a_[0] == 'c':
                        f = feuilles(b_)
                        if f: s.cmps.append((o, f, a_[2] & 0xffff))
                elif m == 'or': v = b_ if x.rs == 0 else a_ if x.rt == 0 else (K(a_[2] | b_[2]) if a_[0] == b_[0] == 'c' else U)
                elif m == 'and':
                    if a_[0] == 'c' and b_[0] == 'c': v = K(a_[2] & b_[2])
                    elif b_[0] == 'c' and a_ is not U: v = mk('and', a_, b_[2])
                    elif a_[0] == 'c' and b_ is not U: v = mk('and', b_, a_[2])
                elif m == 'sll': v = K(b_[2] << x.sa) if b_[0] == 'c' else (U if b_ is U else mk('shl', b_, x.sa))
                elif m in ('srl', 'sra'): v = K(b_[2] >> x.sa) if b_[0] == 'c' else (U if b_ is U else mk('shr', b_, x.sa))
                elif m in ('dsll32', 'dsll'): v = U if b_ is U else mk('dsl', b_, x.sa + (32 if m == 'dsll32' else 0))
                elif m in ('dsra32', 'dsrl32', 'dsra', 'dsrl'):
                    n = x.sa + (32 if m.endswith('32') else 0)
                    if b_[0] == 'dsl' and b_[3] == n: v = b_[2] if n == 32 else low(b_[2], 64 - n, m.startswith('dsra'))
                elif m in ('mult', 'multu'):
                    s.LO = mk('mul', b_, a_[2]) if a_[0] == 'c' and b_ is not U else mk('mul', a_, b_[2]) if b_[0] == 'c' and a_ is not U else U
                    rd = 0
                elif m == 'mflo': v = s.LO
                elif m in ('slt', 'sltu'):
                    for p_, q_ in ((a_, b_), (b_, a_)):
                        if q_[0] == 'c':
                            f = feuilles(p_)
                            if f: s.cmps.append((o, f, q_[2] & 0xffff))
                elif m in ('div', 'divu'): s.LO = U; rd = 0
                if rd and m not in ('jr', 'jalr', 'mult', 'multu', 'div', 'divu'): R[rd] = v
            elif m == 'xori':
                if x.rt: R[x.rt] = U
            else:
                pass                                    # coprocesseur, etc. : rien de suivi
            if fait == 'appel': s.opaque('~', adr=True)
            elif fait == 'mort': mort = True

def signature(idx, a5=False):
    r = rng(idx)
    return norme(desc(idx, a5)), r

def main():
    J = json.load(open(os.path.join(C, "greffe.json"), encoding="utf-8"))
    b5 = paths.module("ro5")
    b9 = open(os.path.join(C, "ro9a_module.bin"), "rb").read()
    ce5, fin5 = struct.unpack_from('<I', b5, 12)[0], struct.unpack_from('<I', b5, 24)[0]
    ce9, fin9 = struct.unpack_from('<I', b9, 12)[0], struct.unpack_from('<I', b9, 24)[0]
    n390u = os.path.getsize(paths.chemin_f390())
    regs = sorted((0xC10000 + int(o, 16), int(b, 16) - int(a, 16), int(a, 16)) for a, b, o in J['regions'])
    RO = [r[0] for r in regs]
    def vers_upper(p):
        """adresse PS2 d'une donnee copiee par la greffe -> adresse d'Upper, ou None"""
        k = bisect.bisect_right(RO, p) - 1
        if k >= 0 and regs[k][0] <= p < regs[k][0] + regs[k][1]: return regs[k][2] + p - regs[k][0]
        return None
    fin_bloc = 0xC10000 + max(o - 0xC10000 + l for o, l, a in regs)
    def don5(v): return BASE + ce5 <= v < fin5 or 0xB04000 <= v < 0xB04000 + n390u
    def hyper9(v): return BASE + ce9 <= v < fin9 or 0xC84000 <= v < 0xD0C000
    def don9(v): return hyper9(v) or vers_upper(v) is not None
    blocs = sorted((int(a, 16), int(b, 16), int(c, 16)) for a, b, c in J['blocs'])
    dec = {int(k, 16): v for k, v in J['decisions'].items()}
    def copie(a):
        k = bisect.bisect_right([x[0] for x in blocs], a) - 1
        if k >= 0 and blocs[k][0] <= a < blocs[k][1]: return blocs[k][2] + a - blocs[k][0]
        return None
    def origine(c):
        for a, b, cc in blocs:
            if cc <= c < cc + b - a: return a + c - cc
        return None
    talons = sorted(int(v, 16) - BASE for v in J['synth'].values()); t0 = talons[0]
    z2 = (int(J['zone2'][0], 16), int(J['zone2'][1], 16))
    pl9 = [(0x22de0, ce9)] + sorted((c, c + b - a) for a, b, c in blocs) + [(t0, z2[1])]
    dep9 = {copie(a) for a in dec if copie(a) is not None} | set(talons) | {int(v[1], 16) for v in dec.values() if v[0] == 'HYPER' and len(v) > 1}
    print("# analyse d'Upper (ro5)...", file=sys.stderr)
    A5 = Analyse(b5, [(0x22b00, ce5)], don5, departs_plus=set(dec))
    print("# analyse de ro9a (Hyper + copies + talons)...", file=sys.stderr)
    A9 = Analyse(b9, pl9, don9, departs_plus=dep9)
    # texte 68K des sites de ro9a
    carte = []
    p = os.path.join(C, "b9", "carte_image.txt")
    if os.path.exists(p):
        for l in open(p, encoding='utf-8', errors='replace'):
            q = l.split(None, 2)
            if len(q) == 3 and len(q[0]) == 6:
                try: carte.append((int(q[1], 16), q[0], q[2].strip()))
                except ValueError: pass
        carte.sort()
    CK = [c[0] for c in carte]
    def t68(site):
        k = bisect.bisect_right(CK, site) - 1
        return "$%s %s" % (carte[k][1], carte[k][2][:60]) if k >= 0 and site - carte[k][0] < 0x200 else ''
    # tailles : constante de donnees suivante
    C5 = sorted(A5.consts); C9 = sorted(A9.consts | {int(v, 16) for v in J['donnees_reutilisees'].values()})
    def taille(t, Cs):
        k = bisect.bisect_right(Cs, t)
        return Cs[k] - t if k < len(Cs) else None
    reut = {int(k, 16): int(v, 16) for k, v in J['donnees_reutilisees'].items()}
    hom = dict(reut)
    try:
        dans = False
        for l in open(os.path.join(paths.REL, "greffe", "donnees", "homologues.tsv"), encoding="utf-8"):
            if l.startswith('1\t'): dans = l.startswith('1\tR\ts:donnees\t'); continue
            if dans and l.startswith('i:'):
                q = l.split('\t'); hom.setdefault(int(q[0][2:], 16), int(q[1], 16))
    except OSError: pass
    try: partages = {int(l, 16) for l in open(os.path.join(paths.GREFFE, "e35", "hom_partages_50.txt"), encoding="utf-8") if l.strip() and not l.startswith('#')}
    except OSError: partages = set()
    def cote(site):
        if origine(site) is not None: return 'C'
        return 'T' if site >= t0 else 'H'
    def variantes(a, A):
        """[(site appelant ou None, index)] : un index fait de registres d'ENTREE est remplace par l'etat des appelants (1 niveau)"""
        if not reg_entree(a[4]) or a[5] not in A.appels: return [(None, a[4])]
        return [(so, subst(a[4], env)) for so, env in A.appels[a[5]]]
    par_table = collections.defaultdict(lambda: collections.defaultdict(list))
    for a in A9.acc: par_table[a[1]][cote(a[0])].append(a)
    acc5_site = {a[0]: a for a in A5.acc}
    def plage_txt(r):
        if r is None: return 'plage ?'
        return 'plage %s$%x..$%x%s' % ('', r[0], r[1], ' (octet haut non suivi)' if len(r) > 2 else '') if r[0] >= 0 else 'plage %d..$%x' % (r[0], r[1])
    def ligne(a, avec68=True):
        site, t, disp, sz, idx, rout, cm = a
        d, r = signature(idx)
        s = "    %06x %s%s  [%s] %s%s" % (site, '.bwl'[sz] if sz < 3 else '.l', (' +$%x' % disp) if disp else '', d, plage_txt(r),
                                         (' ; CMP vus : ' + ','.join('#$%x' % k for k in cm)) if cm else '')
        if avec68:
            o = origine(site)
            if o is not None: s += "  <- Upper %06x" % o
            s += "  | " + t68(site)
        A = A9 if avec68 else A5
        V = variantes(a, A)
        if V[0][0] is not None:
            for so, e in V[:8]:
                s += "\n        appelant %06x%s : [%s] %s" % (so, (' (Upper %06x)' % origine(so)) if avec68 and origine(so) is not None else '',
                                                           norme(desc(e)), plage_txt(rng(e)) + (' masque $%x' % masque(e) if masque(e) is not None else ''))
            if len(V) > 8: s += "\n        ... %d appelants" % len(V)
        return s
    def deborde(a, tl):
        m = masque(a[4])                              # seulement un index BORNE par le code (masque, constante)
        return tl is not None and m is not None and m + a[2] + a[3] > tl

    print("# index_tables.py : construction %s" % C)
    print("# acces a une table (constante + index) : Upper %d, ro9a %d (Hyper %d, copies %d, talons %d)" % (
        len(A5.acc), len(A9.acc), sum(1 for a in A9.acc if cote(a[0]) == 'H'), sum(1 for a in A9.acc if cote(a[0]) == 'C'),
        sum(1 for a in A9.acc if cote(a[0]) == 'T')))
    cop = [a for a in A9.acc if cote(a[0]) != 'H']
    print("# copies : index sans feuille reconnue (registre apres appel / boucle / jonction, ou « ? ») : %d sur %d ; index bornes par un masque : %d" % (
        sum(1 for a in cop if not feuilles(a[4]) and a[4][0] != 'c'), len(cop), sum(1 for a in cop if masque(a[4]) is not None)))
    print("# champs en numerotation PS2 : octet $102 = 68K $0103, $116 = $0117, $12b(A5) = $012A(A5) ; mots et longs inchanges")
    print("# marques : MASQUE (la copie n'a pas le masque de tous les lecteurs d'Hyper, ou un masque plus large) ; DIFF (autre")
    print("#   ecriture de l'index, a lire) ; DEBORD (index borne par un masque mais plus grand que la table)")

    # ------------------------------------------------------------------ A
    print("\n## A. Tables d'Hyper partagees (lues par une copie d'Upper ou un talon ET par le code d'Hyper)")
    nA = nD = nB = 0; resume = []
    for t in sorted(par_table):
        d = par_table[t]
        if not hyper9(t) or not (d.get('C') or d.get('T')): continue
        tl = taille(t, C9); nA += 1
        sigH = {(signature(a[4])[0], a[3]) for a in d.get('H', [])}
        mH = [masque(a[4]) for a in d.get('H', [])]
        maxH = max(mH) if mH and None not in mH else None      # tous les lecteurs d'Hyper sont bornes
        marques = []
        diffs = [a for a in d.get('C', []) + d.get('T', []) if (signature(a[4])[0], a[3]) not in sigH]
        # difference de PLAGE : la copie depasse le plus grand index borne d'Hyper
        dplage = [a for a in diffs if maxH is not None and a[4][0] != 'c' and (masque(a[4]) is None or masque(a[4]) > maxH)]
        deb = [a for a in d.get('C', []) + d.get('T', []) if deborde(a, tl)]
        if not d.get('H'): marques.append('SANS_LECTEUR_HYPER_VU')
        elif dplage: marques.append('MASQUE')
        elif diffs: marques.append('DIFF')
        if deb: marques.append('DEBORD')
        if 'MASQUE' in marques: nD += 1
        if deb: nB += 1
        print("\nT_%x (Hyper) taille <= %s ; lecteurs : copies %d, talons %d, Hyper %d  %s" % (
            t, ('$%x' % tl) if tl else '?', len(d.get('C', [])), len(d.get('T', [])), len(d.get('H', [])), ' '.join(marques)))
        if marques and marques != ['SANS_LECTEUR_HYPER_VU']: resume.append((t, tl, marques))
        for a in d.get('C', []) + d.get('T', []):
            print(("  C" if cote(a[0]) == 'C' else "  T") + ligne(a)[3:] + ('  !DEBORD' if a in deb else '') + ('  !MASQUE' if a in dplage else '  !DIFF' if a in diffs and d.get('H') else ''))
        vus = set()
        for a in d.get('H', []):
            k = (signature(a[4])[0], a[3], a[2])
            if k in vus: continue
            vus.add(k)
            if len(vus) > 6: print("  H   ... (%d lecteurs d'Hyper en tout)" % len(d['H'])); break
            print("  H" + ligne(a)[3:])
    print("\n# A : %d tables partagees ; MASQUE %d ; DEBORD %d" % (nA, nD, nB))
    for t, tl, mq in resume: print("#   T_%x taille<=%s %s" % (t, ('$%x' % tl) if tl else '?', ' '.join(mq)))

    print("\n## A2. Tables d'Upper COPIEES par la greffe (privees) : index borne par un masque qui depasse la table")
    n2 = 0
    for t in sorted(par_table):
        u = vers_upper(t)
        if u is None: continue
        tl = taille(u, C5)
        for a in par_table[t].get('C', []) + par_table[t].get('T', []):
            if deborde(a, tl):
                n2 += 1; print("T_%x (copie de T_%x d'Upper, taille <= $%x)" % (t, u, tl)); print("  C" + ligne(a)[3:])
    print("# A2 : %d acces (borne haute de taille = constante suivante du code d'Upper : un depassement peut etre une table"
          " double lue par un seul LEA)" % n2)

    # ------------------------------------------------------------------ B
    print("\n## B. Routines d'Upper renvoyees a l'homologue d'Hyper : index differents sur une table appariee")
    S5 = sorted(set(dec) | A5.dep); S9 = sorted(A9.dep)
    def fin(a, S):
        k = bisect.bisect_right(S, a); return S[k] if k < len(S) else a + 0x4000
    r5 = collections.defaultdict(list); r9 = collections.defaultdict(list)
    for a in A5.acc: r5[a[5]].append(a)
    for a in A9.acc: r9[a[5]].append(a)
    def acces_routine(R, S, a0):
        out = []; e = fin(a0, sorted(dec) if S is S5 else S)
        k = bisect.bisect_left(S, a0)
        while k < len(S) and S[k] < e: out += R.get(S[k], []); k += 1
        return out
    nb = 0; npaires = 0; ncmp = [0]; npart = 0
    for u in sorted(dec):
        v = dec[u]
        if v[0] != 'HYPER' or len(v) < 2: continue
        h = int(v[1], 16); npaires += 1
        au = acces_routine(r5, S5, u); ah = acces_routine(r9, S9, h)
        if u in partages: npart += 1
        if not au: continue
        th = collections.defaultdict(list)
        for a in ah: th[a[1]].append(a)
        lignes = []
        for a in au:
            t9 = hom.get(a[1])
            if t9 is None or t9 not in th: continue
            su = (signature(a[4], True)[0], a[3]); ru = rng(a[4]); ncmp[0] += 1
            sh = {(signature(x[4], True)[0], x[3]) for x in th[t9]}
            if su in sh: continue
            mh = [masque(x[4]) for x in th[t9]]
            grave = bool(mh) and None not in mh and a[4][0] != 'c' and (masque(a[4]) is None or masque(a[4]) > max(mh))
            lignes.append((a, t9, th[t9], grave))
        if not lignes: continue
        nb += 1
        print("\nUpper %06x -> Hyper %06x  (%s)%s" % (u, h, v[2] if len(v) > 2 else '', '  P' if u in partages else ''))
        for a, t9, lh, grave in lignes:
            print("  U T_%x -> T_%x%s" % (a[1], t9, '  !MASQUE (Upper sans le masque d\'Hyper)' if grave else ''))
            print("  U" + ligne(a, False)[3:])
            vus = set()
            for x in lh:
                k = (signature(x[4], True)[0], x[3])
                if k in vus or len(vus) >= 3: continue
                vus.add(k); print("  H" + ligne(x)[3:])
    print("\n# B : %d paires (decision HYPER, dont %d de la liste HOM_PARTAGES), %d acces d'Upper compares sur une table appariee et"
          " lue des deux cotes, %d paires avec une signature d'index differente" % (npaires, npart, ncmp[0], nb))
    print("# liste HOM_PARTAGES : %d routines, %d avec la decision HYPER dans greffe.json" % (len(partages), sum(1 for u in partages if dec.get(u, [''])[0] == 'HYPER')))
    for u in sorted(partages):
        v = dec.get(u)
        au = acces_routine(r5, S5, u)
        print("#   P %06x %s : %d acces a une table vus dans Upper%s" % (u, ' '.join(v[:2]) if v else 'absente des decisions', len(au),
              (' ; tables : ' + ' '.join(sorted({'T_%x%s' % (a[1], ('->T_%x' % hom[a[1]]) if a[1] in hom else '(non appariee)') for a in au}))) if au else ''))

    print("\n## B2. Homologues NON INJECTIFS encore renvoyes a Hyper (plusieurs routines d'Upper -> une routine d'Hyper)")
    print("# TABLES_DIFFERENTES : les routines d'Upper lisent des tables differentes (constantes d'Upper), l'homologue unique")
    print("# ne peut donc pas les remplacer toutes ; seules les tables a index (acces vus par l'outil) sont comparees")
    cib = collections.defaultdict(list)
    for u, v in dec.items():
        if v[0] == 'HYPER' and len(v) > 1: cib[int(v[1], 16)].append(u)
    nni = ntd = 0
    for h in sorted(cib):
        us = sorted(cib[h])
        if len(us) < 2: continue
        nni += 1
        tabs = {u: tuple(sorted({a[1] for a in acces_routine(r5, S5, u)})) for u in us}
        th = sorted({a[1] for a in acces_routine(r9, S9, h)})
        diff = len(set(tabs.values())) > 1
        if diff: ntd += 1
        cats = collections.Counter(dec[u][2] if len(dec[u]) > 2 else '' for u in us)
        print("Hyper %06x <- %d routines d'Upper (%s)%s ; tables d'Hyper : %s" % (h, len(us), ', '.join('%s x%d' % kv for kv in cats.items()),
              '  TABLES_DIFFERENTES' if diff else '', ' '.join('T_%x' % t for t in th) or '-'))
        if diff:
            for u in us[:12]:
                print("    U %06x : %s" % (u, ' '.join('T_%x%s' % (t, ('->T_%x' % hom[t]) if t in hom else '') for t in tabs[u]) or '-'))
            if len(us) > 12: print("    ... (%d routines)" % len(us))
    print("# B2 : %d routines d'Hyper homologues de plusieurs routines d'Upper ; %d avec des tables differentes cote Upper" % (nni, ntd))

    # ------------------------------------------------------------------ C
    print("\n## C. Tables indexees par l'id de perso ($102 id, $116 perso de base ; PS2) lues par le code greffe")
    print("# valeur lue a chaque id MAX ; HORS = au-dela de la taille (borne haute) de la table")
    def octets9(ad, n):
        o = ad - BASE
        if 0 <= o <= len(b9) - n: return b9[o:o + n]
        u = vers_upper(ad)
        return None
    vus = collections.OrderedDict()
    for a0 in A9.acc:
        if cote(a0[0]) == 'H': continue
        for so, e in variantes(a0, A9):
            f = feuilles(e); ch = sorted({CHAMPS_ID[o] for (o, sz, bn) in f if o in CHAMPS_ID and sz == 1 and not bn.startswith('A5')})
            if not ch: continue
            a = a0[:4] + (e,) + a0[5:]
            vus.setdefault((a[1], signature(e)[0], a[3], a[2], tuple(ch)), []).append(a)
    ntc = 0; hors = collections.Counter(); horsp = collections.Counter()
    for (t, sg, sz, disp, ch), la in sorted(vus.items()):
        ntc += 1
        u = vers_upper(t); tl = taille(t, C9) if hyper9(t) else (taille(u, C5) if u else None)
        a = la[0]; pas = evalue(a[4], 1) - evalue(a[4], 0)
        ne = (tl // pas) if tl and pas > 0 else None
        ou = 'Hyper (partagee)' if hyper9(t) else 'copie de T_%x d\'Upper' % u if u else '?'
        print("\nT_%x %s ; index [%s] par %s ; pas $%x ; taille <= %s (%s entrees) ; %d site(s) : %s" % (
            t, ou, sg, '+'.join(ch), pas, ('$%x' % tl) if tl else '?', ('$%x' % ne) if ne else '?', len(la),
            ' '.join('%06x' % x[0] for x in la[:6])))
        print("    " + t68(a[0]))
        autres = [x for x in feuilles(a[4]) if not (x[0] in CHAMPS_ID and x[1] == 1)] or '?' in sg or any(r_ in sg for r_ in ENTREE) or 'T_' in sg
        if pas <= 0 or autres: print("    (index COMPOSE avec d'autres termes, ou non lineaire en l'id : non evalue, a lire a la main)"); continue
        src = b9 if hyper9(t) else b5
        ad0 = t if hyper9(t) else u
        cells = []
        o0 = (ad0 - BASE + evalue(a[4], 0) + disp) if ad0 else None
        v0 = int.from_bytes(src[o0:o0 + sz], 'little') if o0 is not None and 0 <= o0 <= len(src) - sz else None
        for i in IDS_MAX:
            off = evalue(a[4], i) + disp
            dehors = tl is not None and off + sz > tl
            if dehors: hors[i] += 1
            o = (ad0 - BASE + off) if ad0 else None
            val = int.from_bytes(src[o:o + sz], 'little') if o is not None and 0 <= o <= len(src) - sz and (ad0 < 0xB04000 or hyper9(t)) else None
            pasptr = sz == 4 and v0 is not None and v0 >= 0x200000 and val is not None and not (0x200000 <= val < 0x1000000)
            if pasptr and not dehors: horsp[i] += 1
            cells.append("$%02x:%s%s" % (i, ('%0*x' % (2 * sz, val)) if val is not None else '?', '(HORS)' if dehors else '(PAS UN POINTEUR : hors table probable)' if pasptr else ''))
        print("    id $00:%s   %s" % (('%0*x' % (2 * sz, v0)) if v0 is not None else '?', '  '.join(cells)))
    print("\n# C : %d (table, index) ; lectures HORS table par id : %s ; en plus, long qui n'est pas un pointeur : %s" % (
        ntc, ' '.join('$%02x:%d' % (i, hors[i]) for i in IDS_MAX), ' '.join('$%02x:%d' % (i, horsp[i]) for i in IDS_MAX)))
    print("# (la taille est une BORNE HAUTE : une table sans constante voisine dans le code parait plus grande qu'elle n'est)")

    # ------------------------------------------------------------------ D
    print("\n## D. Tables citees par le rapport : tous les lecteurs vus")
    cites = [('T_BASE', 0x5C5300, None), ('grille', 0x5C5380, None), ('T_VER', 0x5C2490, None), ('T_5c5120 (homologue de T_614aa0)', 0x5C5120, 0x614AA0),
             ('T_61BE10', None, 0x61BE10), ('T_72BDF0', None, 0x72BDF0), ('T_619B50', None, 0x619B50)]
    inv = {}
    for o, l, a in regs: inv[a] = o
    def vers_ps2(u):
        k = bisect.bisect_right([r[2] for r in sorted(regs, key=lambda r: r[2])], u) - 1
        rr = sorted(regs, key=lambda r: r[2])
        if k >= 0 and rr[k][2] <= u < rr[k][2] + rr[k][1]: return rr[k][0] + u - rr[k][2]
        return None
    for nom, t9, t5 in cites:
        cibles9 = set()
        if t9: cibles9.add(t9)
        if t5:
            if t5 in reut: cibles9.add(reut[t5])
            p = vers_ps2(t5)
            if p: cibles9.add(p)
        print("\n%s : Hyper/ro9a %s ; Upper %s%s" % (nom, ' '.join('T_%x' % x for x in sorted(cibles9)) or '-', ('T_%x' % t5) if t5 else '-',
              (' ; reutilisee -> T_%x' % reut[t5]) if t5 in reut else (' ; copiee en %x' % vers_ps2(t5)) if t5 and vers_ps2(t5) else ''))
        for t in sorted(cibles9):
            tl = taille(t, C9) if hyper9(t) else None
            print("  T_%x taille <= %s" % (t, ('$%x' % tl) if tl else '?'))
            for a in A9.acc:
                if t <= a[1] < t + (tl or 4) and (a[1] == t or not hyper9(t)): print("  " + cote(a[0]) + ligne(a)[3:])
            if A9.directs.get(t): print("  (+ %d lecture(s) directe(s) sans index)" % A9.directs[t])
        if t5:
            tl = taille(t5, C5)
            print("  Upper T_%x taille <= %s ; lecteurs d'Upper :" % (t5, ('$%x' % tl) if tl else '?'))
            for a in A5.acc:
                if a[1] == t5:
                    c = copie(a[0]); k = bisect.bisect_right(sorted(dec), a[0]) - 1; r = sorted(dec)[k]
                    print("  U" + ligne(a, False)[3:] + "  routine %06x %s%s" % (r, dec[r][0], (' copie %06x' % c) if c else ''))
main()
