#!/usr/bin/env python3
"""lib_idx.py -- engine of the per-character-id table tracer (max-tables): the symbolic-execution engine of
tools/reviews/graft/index_tables.py as a library, extended with the log of memory writes (Analyse.sto) and the sites
that build each data constant (Analyse.csite). Imported by the other tools of this folder.

  X = lib_idx.charge(C=None, upper=True)
      context of the frozen graft build C (None -> $HSFA_GRAFT_BUILD): modules ro5 / ro9a, greffe.json, correspondences
      copy <-> Upper (vers_upper, vers_copie, copie, origine), analyses X.A5 (Upper, if upper) and X.A9 (ro9a: Hyper +
      copies + stubs), 68K text of the sites (t68, a68), homologues (hom), side of a site (cote: C copy, T stub, H Hyper).

Method: LINEAR symbolic execution of each routine (cells of the 68K registers at 0x70001100.., MIPS temporaries,
stack cells). A memory read whose address = data constant + rest is a TABLE ACCESS; the rest is the INDEX, described
by its leaves (fields "$off(An)" in PS2 numbering: 68K byte = PS2 XOR 1), its masks (andi), its shifts (sll, mult by a
constant) and its range. The "CMP" are the subtractions of a constant seen earlier in the routine on a leaf of the
index (indicative: dominance is NOT proven). Size of a table = distance to the next data constant built by the code of
the same module (upper bound).

What the engine does NOT see: tables reached through a pointer read from memory (table of tables, A register received as
argument), an index that crosses a call (JSR) or a loop head (shown "?"), joins of diverging paths ("@j"), accesses
through the port's C helpers. A "?" index is not judged. The (A5) offsets of Upper and Hyper are not comparable in
the comparisons (A5 relocation): they are shown "$..(A5)".

Inputs: module ro5 ($HSFA_MODULES), the frozen build (ro9a_module.bin, greffe.json, b9/carte_image.txt), releves
homologues.tsv of the repository copy ($HSFA_GRAFT_STATE), file 390 size ($HSFA_F390). See paths.py. Read only.
"""
import sys, os, json, struct, bisect, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))   # src/hsfa of the repository (= paths.SRC_HSFA)
from mips import Ins
BASE = 0x1F0000
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
        s.sto = []; s.csite = collections.defaultdict(list)
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
                if R[x.rt][0] == 'c' and s.est_donnee(R[x.rt][2]) and x.rs and base_lui: s.consts.add(R[x.rt][2]); s.csite[R[x.rt][2]].append(o)
            elif m == 'ori':
                v = R[x.rs]
                R[x.rt] = K(v[2] | x.imm) if v[0] == 'c' else (v if x.imm == 0 else U)
                if R[x.rt][0] == 'c' and s.est_donnee(R[x.rt][2]) and x.rs and base_lui: s.consts.add(R[x.rt][2]); s.csite[R[x.rt][2]].append(o)
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
                elif bs is not U and v is not U: s.sto.append((o, bs, x.simm, sz, v, rout))
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

class Ctx: pass
def charge(C=None, upper=True):
    """contexte de la construction figee : modules, correspondances, analyses A5 (Upper) et A9 (ro9a)"""
    X = Ctx(); C = paths.construction(C); X.C = C
    J = X.J = json.load(open(os.path.join(C, "greffe.json"), encoding="utf-8"))
    b5 = X.b5 = paths.lit_module("ro5")
    b9 = X.b9 = open(os.path.join(C, "ro9a_module.bin"), "rb").read()
    X.ce5, X.fin5 = ce5, fin5 = struct.unpack_from('<I', b5, 12)[0], struct.unpack_from('<I', b5, 24)[0]
    X.ce9, X.fin9 = ce9, fin9 = struct.unpack_from('<I', b9, 12)[0], struct.unpack_from('<I', b9, 24)[0]
    n390u = os.path.getsize(paths.f390())
    regs = X.regs = sorted((0xC10000 + int(o, 16), int(b, 16) - int(a, 16), int(a, 16)) for a, b, o in J['regions'])
    RO = [r[0] for r in regs]
    def vers_upper(p):
        k = bisect.bisect_right(RO, p) - 1
        if k >= 0 and regs[k][0] <= p < regs[k][0] + regs[k][1]: return regs[k][2] + p - regs[k][0]
        return None
    ru = sorted((r[2], r[1], r[0]) for r in regs); RU = [r[0] for r in ru]
    def vers_copie(u):
        k = bisect.bisect_right(RU, u) - 1
        if k >= 0 and ru[k][0] <= u < ru[k][0] + ru[k][1]: return ru[k][2] + u - ru[k][0]
        return None
    X.vers_upper, X.vers_copie = vers_upper, vers_copie
    def don5(v): return BASE + ce5 <= v < fin5 or 0xB04000 <= v < 0xB04000 + n390u
    def hyper9(v): return BASE + ce9 <= v < fin9 or 0xC84000 <= v < 0xD0C000
    def don9(v): return hyper9(v) or vers_upper(v) is not None
    X.don5, X.hyper9, X.don9 = don5, hyper9, don9
    blocs = X.blocs = sorted((int(a, 16), int(b, 16), int(c, 16)) for a, b, c in J['blocs'])
    dec = X.dec = {int(k, 16): v for k, v in J['decisions'].items()}
    B0 = [x[0] for x in blocs]
    def copie(a):
        k = bisect.bisect_right(B0, a) - 1
        if k >= 0 and blocs[k][0] <= a < blocs[k][1]: return blocs[k][2] + a - blocs[k][0]
        return None
    bc = sorted((cc, cc + b - a, a) for a, b, cc in blocs); BC = [x[0] for x in bc]
    def origine(c):
        k = bisect.bisect_right(BC, c) - 1
        if k >= 0 and bc[k][0] <= c < bc[k][1]: return bc[k][2] + c - bc[k][0]
        return None
    X.copie, X.origine = copie, origine
    talons = X.talons = sorted(int(v, 16) - BASE for v in J['synth'].values()); t0 = X.t0 = talons[0]
    X.noms_talons = {int(v, 16) - BASE: k for k, v in J['synth'].items()}
    z2 = (int(J['zone2'][0], 16), int(J['zone2'][1], 16))
    X.pl9 = pl9 = [(0x22de0, ce9)] + sorted((c, c + b - a) for a, b, c in blocs) + [(t0, z2[1])]
    dep9 = {copie(a) for a in dec if copie(a) is not None} | set(talons) | {int(v[1], 16) for v in dec.values() if v[0] == 'HYPER' and len(v) > 1}
    if upper: X.A5 = Analyse(b5, [(0x22b00, ce5)], don5, departs_plus=set(dec))
    X.A9 = Analyse(b9, pl9, don9, departs_plus=dep9)
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
    def a68(site):
        k = bisect.bisect_right(CK, site) - 1
        return carte[k][1] if k >= 0 and site - carte[k][0] < 0x200 else ''
    X.t68, X.a68, X.carte = t68, a68, carte
    X.reut = reut = {int(k, 16): int(v, 16) for k, v in J['donnees_reutilisees'].items()}
    hom = dict(reut)
    try:
        dans = False
        for l in open(os.path.join(paths.releves(), "greffe", "donnees", "homologues.tsv"), encoding="utf-8"):
            if l.startswith('1\t'): dans = l.startswith('1\tR\ts:donnees\t'); continue
            if dans and l.startswith('i:'):
                q = l.split('\t'); hom.setdefault(int(q[0][2:], 16), int(q[1], 16))
    except OSError: pass
    X.hom = hom
    def cote(site):
        if origine(site) is not None: return 'C'
        return 'T' if site >= t0 else 'H'
    X.cote = cote
    def lit9(a, n): return b9[a - BASE:a - BASE + n] if hyper9(a) and a < fin9 else None
    X.lit9 = lit9
    return X
