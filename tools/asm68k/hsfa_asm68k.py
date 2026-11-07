#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 projet HSFA
"""hsfa_asm68k.py -- assembleur 68000 (syntaxe Motorola) pour la construction d'Upper MAX (projet HSFA).

Écrit de zéro (bibliothèque standard seulement, Python 3.8+), sans code de vasm. Il reproduit À L'OCTET la sortie de
« vasmm68k_mot -m68000 -spaces -Fbin » sur le sous-ensemble employé par la construction : mêmes optimisations par
défaut (tailles des branchements en plusieurs passes, absolu court / PC-relatif / absolu long, moveq, addq, lea,
tst...), même binaire plat (sections « org » triées, trous comblés de zéros), même table des symboles dans la liste.

Usage (options compatibles avec la ligne de commande de vasm employée par la construction) :
    python3 hsfa_asm68k.py -m68000 -spaces -Fbin -quiet [-maxerrors=N] [-L liste] -o sortie.bin source.s
Sortie : 0 si aucune erreur ; messages « error N in line L of "fichier": ... » / « warning N ... » (format de vasm).
Bibliothèque : assemble_fichier(chemin) -> Resultat (binaire, symboles, liste).
"""
import os
import re
import sys

VERSION = "hsfa_asm68k 1.0"

# ----------------------------------------------------------------------------------------------------------------
# Erreurs
# ----------------------------------------------------------------------------------------------------------------


class AsmError(Exception):
    def __init__(self, num, msg):
        Exception.__init__(self, msg)
        self.num = num
        self.msg = msg


class Unknown(Exception):
    """valeur pas encore connue (référence en avant pendant une passe de dimensionnement)"""


def s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


def u32(v):
    return v & 0xFFFFFFFF


# ----------------------------------------------------------------------------------------------------------------
# Expressions
# ----------------------------------------------------------------------------------------------------------------
# priorités (vasm, syntaxe mot) : unaires > << >> > & > ^ ~ > | ! > * / % // > + - > comparaisons > == != = > && > ||
BINOPS = {
    "||": 1, "&&": 2,
    "==": 3, "!=": 3, "=": 3, "<>": 3,
    "<": 4, ">": 4, "<=": 4, ">=": 4,
    "+": 5, "-": 5,
    "*": 6, "/": 6, "%": 6, "//": 6,
    "|": 7, "!": 7,
    "^": 8, "~": 8,
    "&": 9,
    "<<": 10, ">>": 10,
}
TOK_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<hex>\$[0-9A-Fa-f]+)
  | (?P<bin>%[01]+)
  | (?P<oct>@[0-7]+)
  | (?P<dec>[0-9]+)
  | (?P<chr>'(?:[^']|'')*'|"(?:[^"]|"")*")
  | (?P<id>\.?[A-Za-z_][A-Za-z0-9_]*\$?)
  | (?P<op><<|>>|<=|>=|==|!=|<>|&&|\|\||//|[-+*/%&|^~!<>=()])
""", re.X)


class Expr:
    """arbre : ('n', v) ('s', nom) ('pc',) ('u', op, e) ('b', op, a, b)"""
    __slots__ = ("t", "syms")

    def __init__(self, t, syms):
        self.t = t
        self.syms = syms        # noms référencés (pour la liste des equ référencés)


def tokenize(s):
    toks = []
    i = 0
    n = len(s)
    while i < n:
        m = TOK_RE.match(s, i)
        if not m:
            raise AsmError(5, "syntax error in expression: %s" % s[i:])
        i = m.end()
        k = m.lastgroup
        if k == "ws":
            continue
        toks.append((k, m.group(k)))
    return toks


NUM_SIMPLE = re.compile(r"^(?:\$([0-9A-Fa-f]+)|(-?[0-9]+))$")
ID_SIMPLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_expr(s, ctx):
    """chaîne -> Expr ; ctx.resolve(nom) donne le nom complet (étiquettes locales)"""
    m = NUM_SIMPLE.match(s)               # chemins rapides : constante, nom simple
    if m:
        return Expr(("n", int(m.group(1), 16) if m.group(1) is not None else int(m.group(2))), [])
    if ID_SIMPLE.match(s):
        return Expr(("s", s), [s])
    toks = tokenize(s)
    pos = [0]
    syms = []

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else (None, None)

    def take():
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def primary():
        k, v = peek()
        if k is None:
            raise AsmError(5, "missing operand in expression")
        take()
        if k == "hex":
            return ("n", int(v[1:], 16))
        if k == "bin":
            return ("n", int(v[1:], 2))
        if k == "oct":
            return ("n", int(v[1:], 8))
        if k == "dec":
            return ("n", int(v))
        if k == "chr":
            q = v[0]
            body = v[1:-1].replace(q + q, q)
            x = 0
            for c in body.encode("latin-1"):
                x = (x << 8) | c
            return ("n", x)
        if k == "id":
            nom = ctx.resolve(v)
            syms.append(nom)
            return ("s", nom)
        if v == "(":
            e = binary(0)
            k2, v2 = peek()
            if v2 != ")":
                raise AsmError(5, "missing ) in expression")
            take()
            return e
        if v == "*":
            return ("pc",)
        if v in ("-", "+", "~", "!"):
            return ("u", v, primary())
        raise AsmError(5, "syntax error in expression: %s" % s)

    def binary(minp):
        a = primary()
        while True:
            k, v = peek()
            if k != "op" or v not in BINOPS:
                break
            p = BINOPS[v]
            if p <= minp:
                break
            take()
            b = binary(p)
            a = ("b", v, a, b)
        return a

    t = binary(0)
    if pos[0] != len(toks):
        raise AsmError(5, "syntax error in expression: %s" % s)
    if t[0] == "n":
        t = ("n", t[1])
    return Expr(t, syms)


def ev(t, ctx, pc):
    """évalue un arbre ; Unknown si un symbole n'a pas encore de valeur ; arithmétique 32 bits signée"""
    k = t[0]
    if k == "n":
        return s32(t[1])
    if k == "s":
        return ctx.symval(t[1])
    if k == "pc":
        if pc is None:
            raise Unknown()
        return s32(pc)
    if k == "u":
        x = ev(t[2], ctx, pc)
        op = t[1]
        if op == "-":
            return s32(-x)
        if op == "+":
            return x
        if op == "~":
            return s32(~x)
        return 1 if x == 0 else 0           # !
    op = t[1]
    a = ev(t[2], ctx, pc)
    b = ev(t[3], ctx, pc)
    if op == "+":
        return s32(a + b)
    if op == "-":
        return s32(a - b)
    if op == "*":
        return s32(a * b)
    if op == "/":
        if b == 0:
            raise AsmError(5, "division by zero")
        q = abs(a) // abs(b)
        return s32(q if (a >= 0) == (b >= 0) else -q)
    if op in ("%", "//"):
        if b == 0:
            raise AsmError(5, "division by zero")
        r = abs(a) % abs(b)
        return s32(r if a >= 0 else -r)
    if op == "<<":
        return s32(a << (b & 63)) if 0 <= b < 64 else 0
    if op == ">>":
        return s32(a >> min(b & 0xFFFFFFFF, 63))
    if op == "&":
        return s32(a & b)
    if op in ("|", "!"):
        return s32(a | b)
    if op in ("^", "~"):
        return s32(a ^ b)
    if op in ("==", "="):
        return -1 if a == b else 0
    if op in ("!=", "<>"):
        return -1 if a != b else 0
    if op == "<":
        return -1 if a < b else 0
    if op == ">":
        return -1 if a > b else 0
    if op == "<=":
        return -1 if a <= b else 0
    if op == ">=":
        return -1 if a >= b else 0
    if op == "&&":
        return -1 if (a and b) else 0
    if op == "||":
        return -1 if (a or b) else 0
    raise AsmError(5, "unknown operator %s" % op)


# ----------------------------------------------------------------------------------------------------------------
# Opérandes (modes d'adressage)
# ----------------------------------------------------------------------------------------------------------------
DN, AN, IND, POSTINC, PREDEC, DISP, IDX, ABSW, ABSL, PCDISP, PCIDX, IMM = range(12)
ABS = 12          # absolu sans taille : court, PC-relatif ou long selon la valeur
SR, CCR, USP, REGLIST = 13, 14, 15, 16
MODE_NOM = {DN: "Dn", AN: "An", IND: "(An)", POSTINC: "(An)+", PREDEC: "-(An)", DISP: "d16(An)", IDX: "d8(An,Xn)",
            ABSW: "abs.w", ABSL: "abs.l", PCDISP: "d16(PC)", PCIDX: "d8(PC,Xn)", IMM: "#imm", ABS: "abs",
            SR: "SR", CCR: "CCR", USP: "USP", REGLIST: "reglist"}

ALL = frozenset([DN, AN, IND, POSTINC, PREDEC, DISP, IDX, ABSW, ABSL, PCDISP, PCIDX, IMM])
DATA = ALL - {AN}
MEM = DATA - {DN}
ALT = frozenset([DN, AN, IND, POSTINC, PREDEC, DISP, IDX, ABSW, ABSL])
DALT = ALT - {AN}
MALT = DALT - {DN}
CTRL = frozenset([IND, DISP, IDX, ABSW, ABSL, PCDISP, PCIDX])
CALT = frozenset([IND, DISP, IDX, ABSW, ABSL])

REG_RE = re.compile(r"^(?:([dD])([0-7])|([aA])([0-7])|([sS][pP]))$")


def reg_of(s):
    """'d3' -> (0,3) ; 'a7'/'sp' -> (1,7) ; sinon None"""
    m = REG_RE.match(s)
    if not m:
        return None
    if m.group(1):
        return (0, int(m.group(2)))
    if m.group(3):
        return (1, int(m.group(4)))
    return (1, 7)


class Op:
    __slots__ = ("mode", "reg", "expr", "xreg", "xlong", "dsize", "mask", "dyn", "texte")

    def __init__(self, mode, reg=0, expr=None, xreg=None, xlong=False, dsize=None, mask=0):
        self.mode = mode
        self.reg = reg
        self.expr = expr
        self.xreg = xreg          # registre d'index (type, n)
        self.xlong = xlong
        self.dsize = dsize        # taille imposée du déplacement / de l'absolu ('w', 'l') ou None
        self.mask = mask
        self.dyn = False


def split_top(s, sep=","):
    """découpe aux séparateurs hors parenthèses et hors chaînes"""
    out = []
    prof = 0
    cur = []
    q = None
    for c in s:
        if q:
            cur.append(c)
            if c == q:
                q = None
            continue
        if c in "'\"":
            q = c
            cur.append(c)
            continue
        if c == "(":
            prof += 1
        elif c == ")":
            prof -= 1
        if c == sep and prof == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    out.append("".join(cur))
    return out


def strip_spaces(s):
    """retire les blancs hors chaînes (-spaces)"""
    if "'" not in s and '"' not in s:
        return "".join(s.split())
    out = []
    q = None
    for c in s:
        if q:
            out.append(c)
            if c == q:
                q = None
        elif c in "'\"":
            q = c
            out.append(c)
        elif not c.isspace():
            out.append(c)
    return "".join(out)


def match_close(s, j):
    """indice de la '(' qui ferme la ')' en s[j]"""
    prof = 0
    for i in range(j, -1, -1):
        if s[i] == ")":
            prof += 1
        elif s[i] == "(":
            prof -= 1
            if prof == 0:
                return i
    return -1


def parse_index(s):
    """'d0.w' / 'a1.l' / 'd2' -> (reg, long)"""
    long_ = False
    sl = s.lower()
    if sl.endswith(".w"):
        s = s[:-2]
    elif sl.endswith(".l"):
        s = s[:-2]
        long_ = True
    if "*" in s:
        s, sc = s.split("*", 1)
        if sc.strip() != "1":
            raise AsmError(2, "scale factor not supported on 68000")
    r = reg_of(s)
    if r is None:
        raise AsmError(2, "invalid index register: %s" % s)
    return r, long_


def parse_reglist(s):
    mask = 0
    for part in s.split("/"):
        if "-" in part:
            a, b = part.split("-", 1)
            ra, rb = reg_of(a), reg_of(b)
            if ra is None or rb is None:
                return None
            ia, ib = ra[0] * 8 + ra[1], rb[0] * 8 + rb[1]
            if ia > ib:
                ia, ib = ib, ia
            for i in range(ia, ib + 1):
                mask |= 1 << i
        else:
            r = reg_of(part)
            if r is None:
                return None
            mask |= 1 << (r[0] * 8 + r[1])
    return mask


def size_suffix(s):
    sl = s.lower()
    if len(s) > 2 and sl[-2] == "." and sl[-1] in "wl":
        return s[:-2], sl[-1]
    return s, None


def parse_operand(s, ctx):
    """texte d'opérande (sans blancs) -> Op"""
    if not s:
        raise AsmError(2, "missing operand")
    sl = s.lower()
    if s[0] == "#":
        e = parse_expr(s[1:], ctx)
        o = Op(IMM, expr=e)
        o.dyn = bool(e.syms) or "*" in s[1:]
        return o
    r = reg_of(s)
    if r is not None:
        return Op(DN if r[0] == 0 else AN, r[1])
    if sl == "sr":
        return Op(SR)
    if sl == "ccr":
        return Op(CCR)
    if sl == "usp":
        return Op(USP)
    if "/" in s or ("-" in s and re.match(r"^[dDaA][0-7]-[dDaA][0-7]", s)):
        m = parse_reglist(s)
        if m is not None:
            return Op(REGLIST, mask=m)
    if s[0] == "-" and s[1:2] == "(" and s[-1] == ")":
        r = reg_of(s[2:-1])
        if r is not None and r[0] == 1:
            return Op(PREDEC, r[1])
    if s[0] == "(" and s.endswith(")+"):
        r = reg_of(s[1:-2])
        if r is not None and r[0] == 1:
            return Op(POSTINC, r[1])
    # forme avec base registre : d(An) d(An,Xn) (d,An) (d,An,Xn) (An,Xn) d(PC) ...
    if s[-1] == ")":
        i = match_close(s, len(s) - 1)
        if i >= 0:
            inner = split_top(s[i + 1:-1])
            pre = s[:i]
            # base registre ?
            parts = inner
            disp = None
            if pre == "" and len(parts) >= 2 and reg_of(parts[0]) is None and parts[0].lower() != "pc":
                disp = parts[0]
                parts = parts[1:]
            elif pre != "":
                disp = pre
            b = parts[0].lower()
            rb = reg_of(parts[0])
            if b == "pc" or (rb is not None and rb[0] == 1):
                ispc = b == "pc"
                dsize = None
                e = None
                if disp is not None:
                    disp, dsize = size_suffix(disp)
                    e = parse_expr(disp, ctx)
                if len(parts) == 1:
                    if ispc:
                        o = Op(PCDISP, 0, e if e else Expr(("n", 0), []), dsize=dsize)
                    elif e is None:
                        return Op(IND, rb[1])
                    else:
                        o = Op(DISP, rb[1], e, dsize=dsize)
                elif len(parts) == 2:
                    xr, xl = parse_index(parts[1])
                    o = Op(PCIDX if ispc else IDX, 0 if ispc else rb[1], e if e else Expr(("n", 0), []),
                           xreg=xr, xlong=xl, dsize=dsize)
                else:
                    raise AsmError(2, "invalid addressing mode: %s" % s)
                o.dyn = bool(o.expr.syms) or (disp is not None and "*" in disp) or ispc
                return o
            if rb is not None and rb[0] == 0 and len(parts) == 1:
                raise AsmError(2, "invalid addressing mode: %s" % s)
    # absolu
    base, sz = size_suffix(s)
    if sz and base.startswith("(") and base.endswith(")") and match_close(base, len(base) - 1) == 0:
        base = base[1:-1]
    elif sz is None and s.startswith("(") and s.endswith(")") and match_close(s, len(s) - 1) == 0:
        base = s[1:-1]
    e = parse_expr(base, ctx)
    o = Op(ABSW if sz == "w" else ABSL if sz == "l" else ABS, expr=e, dsize=sz)
    o.dyn = True
    return o


# ----------------------------------------------------------------------------------------------------------------
# Encodage 68000
# ----------------------------------------------------------------------------------------------------------------
CC = {"t": 0, "f": 1, "hi": 2, "ls": 3, "cc": 4, "hs": 4, "cs": 5, "lo": 5, "ne": 6, "eq": 7, "vc": 8, "vs": 9,
      "pl": 10, "mi": 11, "ge": 12, "lt": 13, "gt": 14, "le": 15}
BCC = dict((("b" + k), v) for k, v in CC.items() if k not in ("t", "f"))
BCC["bra"] = 0
BCC["bsr"] = 1
DBCC = dict((("db" + k), v) for k, v in CC.items())
DBCC["dbra"] = 1
SCC = dict((("s" + k), v) for k, v in CC.items())
SZ2 = {"b": 0, "w": 1, "l": 2}


class Enc:
    """construction d'une instruction : mots + avertissements ; ctx.pc = adresse de l'instruction"""
    __slots__ = ("w", "pc", "ctx", "final", "warn", "idx", "changes")

    def __init__(self, ctx, pc, final):
        self.w = bytearray()
        self.pc = pc
        self.ctx = ctx
        self.final = final
        self.warn = []
        self.idx = None

    def word(self, x):
        self.w += bytes(((x >> 8) & 0xFF, x & 0xFF))

    def long(self, x):
        x &= 0xFFFFFFFF
        self.w += bytes(((x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, x & 0xFF))

    def en_avant(self, e):
        """la cible est-elle une étiquette définie plus loin dans le source ?"""
        if e.t[0] != "s":
            return False
        sy = self.ctx.syms.get(e.t[1])
        return sy is not None and sy.idx is not None and self.idx is not None and sy.idx > self.idx

    def here(self):
        return self.pc + len(self.w)

    def val(self, e, defaut=0):
        """valeur d'une expression ; en passe de dimensionnement, None si inconnue"""
        try:
            return ev(e.t, self.ctx, self.pc)
        except Unknown:
            if self.final:
                raise AsmError(2, "undefined symbol")
            return None


def fits8(v):
    return -128 <= v <= 127


def fits16(v):
    return -32768 <= v <= 32767


def check_imm(v, size):
    if size == "b":
        if not (-128 <= v <= 255):
            raise AsmError(2040, "immediate operand out of range")
        return v & 0xFF
    if size == "w":
        if not (-32768 <= v <= 65535):
            raise AsmError(2040, "immediate operand out of range")
        return v & 0xFFFF
    return v & 0xFFFFFFFF


def resolve_abs(enc, o, allowed, extoff):
    """décide la forme d'un absolu sans taille : ABSW, PCDISP ou ABSL ; extoff = décalage du mot d'extension"""
    if o.mode != ABS:
        return o.mode
    v = enc.val(o.expr)
    if v is None:
        return ABSL
    if fits16(v) and ABSW in allowed:
        return ABSW
    if PCDISP in allowed and fits16(s32(v - (enc.pc + extoff))):
        return PCDISP
    return ABSL


def ea_len(enc, o, size, allowed, extoff):
    """(mode effectif, nombre d'octets d'extension)"""
    m = o.mode
    if m == ABS:
        m = resolve_abs(enc, o, allowed, extoff)
        return m, (2 if m in (ABSW, PCDISP) else 4)
    if m == DISP:
        if o.dsize is None:
            v = enc.val(o.expr)
            if v == 0:
                return IND, 0
        return DISP, 2
    if m in (PCDISP, IDX, PCIDX, ABSW):
        return m, 2
    if m == ABSL:
        return m, 4
    if m == IMM:
        return m, (4 if size == "l" else 2)
    return m, 0


def ea_bits(m, reg):
    if m == DN:
        return reg
    if m == AN:
        return 8 | reg
    if m == IND:
        return 0x10 | reg
    if m == POSTINC:
        return 0x18 | reg
    if m == PREDEC:
        return 0x20 | reg
    if m == DISP:
        return 0x28 | reg
    if m == IDX:
        return 0x30 | reg
    if m == ABSW:
        return 0x38
    if m == ABSL:
        return 0x39
    if m == PCDISP:
        return 0x3A
    if m == PCIDX:
        return 0x3B
    if m == IMM:
        return 0x3C
    raise AsmError(2, "invalid addressing mode")


def ea_check(o, allowed, what="operand"):
    m = o.mode
    if m == ABS:
        if ABSW in allowed or ABSL in allowed:
            return
    elif m == DISP and IND in allowed and DISP in allowed:
        return
    elif m in allowed:
        return
    raise AsmError(9, "instruction not supported on selected architecture")


def emit_ext(enc, o, m, size):
    """écrit les mots d'extension du mode m (déjà résolu) à la position courante"""
    if m == IND or m in (DN, AN, POSTINC, PREDEC):
        return
    if m == DISP:
        v = enc.val(o.expr)
        if v is None:
            enc.word(0)
            return
        if not fits16(v):
            raise AsmError(2030, "displacement out of range")
        enc.word(v & 0xFFFF)
        return
    if m == ABSW:
        v = enc.val(o.expr)
        if v is None:
            enc.word(0)
            return
        if not (-32768 <= v <= 65535):
            raise AsmError(2030, "absolute short address out of range")
        enc.word(v & 0xFFFF)
        return
    if m == ABSL:
        v = enc.val(o.expr)
        enc.long(0 if v is None else v)
        return
    if m == IMM:
        v = enc.val(o.expr)
        if v is None:
            v = 0
        if size == "l":
            enc.long(v)
        else:
            enc.word(check_imm(v, size))
        return
    raise AsmError(2, "invalid addressing mode")


def put_ea_ext(enc, o, m, size):
    # o.mode ABS résolu en PCDISP : déplacement par rapport au mot d'extension
    if m == PCDISP and o.mode == ABS:
        v = enc.val(o.expr)
        if v is None:
            enc.word(0)
            return
        enc.word(s32(v - enc.here()) & 0xFFFF)
        return
    if m == PCDISP and o.mode == PCDISP:
        v = enc.val(o.expr)
        if v is None:
            enc.word(0)
            return
        d = s32(v - enc.here())
        if not fits16(d):
            raise AsmError(2030, "displacement out of range")
        enc.word(d & 0xFFFF)
        return
    if m == PCIDX:
        v = enc.val(o.expr)
        ext = (o.xreg[0] << 15) | (o.xreg[1] << 12) | (0x800 if o.xlong else 0)
        if v is None:
            enc.word(ext)
            return
        d = s32(v - enc.here())
        if not fits8(d):
            raise AsmError(2030, "displacement out of range")
        enc.word(ext | (d & 0xFF))
        return
    if m == IDX:
        v = enc.val(o.expr)
        ext = (o.xreg[0] << 15) | (o.xreg[1] << 12) | (0x800 if o.xlong else 0)
        if v is None:
            enc.word(ext)
            return
        if not fits8(v):
            raise AsmError(2030, "displacement out of range")
        enc.word(ext | (v & 0xFF))
        return
    emit_ext(enc, o, m, size)


def mode_of(enc, o, size, allowed, extoff):
    ea_check(o, allowed)
    return ea_len(enc, o, size, allowed, extoff)[0]


# ----------------------------------------------------------------------------------------------------------------
# Instructions
# ----------------------------------------------------------------------------------------------------------------


def exige(o, mode):
    if o.mode != mode:
        raise AsmError(9, "instruction not supported on selected architecture")


def need(ops, n):
    if len(ops) != n:
        raise AsmError(2, "wrong number of operands")


def imm_val(enc, o):
    """valeur d'un immédiat ou None (inconnue)"""
    return enc.val(o.expr)


def i_simple(enc, opw, ea_o, size, allowed, extra=None):
    """mot d'opération | ea (+ extension) ; extra : mots placés avant l'extension de l'ea (ex. bit de btst)"""
    pre = 2 + (len(extra) * 2 if extra else 0)
    m = mode_of(enc, ea_o, size, allowed, pre)
    enc.word(opw | ea_bits(m, ea_o.reg))
    if extra:
        for x in extra:
            enc.word(x)
    put_ea_ext(enc, ea_o, m, size)


def i_move(enc, size, src, dst, alias=False):
    if size is None:
        size = "w"
    # registres spéciaux
    if dst.mode == CCR:
        i_simple(enc, 0x44C0, src, "w", DATA)
        return
    if dst.mode == SR:
        i_simple(enc, 0x46C0, src, "w", DATA)
        return
    if src.mode == SR:
        i_simple(enc, 0x40C0, dst, "w", DALT)
        return
    if src.mode == USP:
        if dst.mode != AN:
            raise AsmError(2, "invalid operand")
        enc.word(0x4E68 | dst.reg)
        return
    if dst.mode == USP:
        if src.mode != AN:
            raise AsmError(2, "invalid operand")
        enc.word(0x4E60 | src.reg)
        return
    if dst.mode == AN:
        i_movea(enc, size, src, dst)
        return
    if src.mode == IMM and dst.mode == DN and size == "l" and not alias:
        v = imm_val(enc, src)
        if v is not None and moveq_opt(enc, v, dst.reg):
            return
    szc = {"b": 0x1000, "w": 0x3000, "l": 0x2000}[size]
    if size == "b" and src.mode == AN:
        raise AsmError(9, "instruction not supported on selected architecture")
    ms = mode_of(enc, src, size, ALL, 2)
    nsrc = ea_len(enc, src, size, ALL, 2)[1]
    md = mode_of(enc, dst, size, DALT, 2 + nsrc)
    db = ea_bits(md, dst.reg)
    enc.word(szc | ((db & 7) << 9) | ((db >> 3) << 6) | ea_bits(ms, src.reg))
    put_ea_ext(enc, src, ms, size)
    put_ea_ext(enc, dst, md, size)


def moveq_opt(enc, v, r):
    """MOVE.L #v,Dn -> moveq / moveq+add.w / moveq+swap (optimisations par défaut de vasm) ; True si fait"""
    v = s32(v)
    if -128 <= v <= 127:
        enc.word(0x7000 | (r << 9) | (v & 0xFF))
        return True
    if -256 <= v <= 254 and not (v & 1):          # moveq #v/2 + add.w Dn,Dn
        enc.word(0x7000 | (r << 9) | ((v >> 1) & 0xFF))
        enc.word(0xD040 | (r << 9) | r)
        return True
    u = u32(v)
    if (u & 0xFFFF) == 0 and 0x10000 <= u <= 0x7F0000:
        enc.word(0x7000 | (r << 9) | ((u >> 16) & 0xFF))
        enc.word(0x4840 | r)
        return True
    if (u & 0xFFFF) == 0xFFFF and 0xFF80FFFF <= u <= 0xFFFEFFFF:
        enc.word(0x7000 | (r << 9) | ((u >> 16) & 0xFF))
        enc.word(0x4840 | r)
        return True
    return False


def i_movea(enc, size, src, dst):
    if size == "b":
        raise AsmError(9, "instruction not supported on selected architecture")
    if size is None:
        size = "w"
    if src.mode == IMM:
        v = imm_val(enc, src)
        if v is not None:
            if v == 0:
                enc.word(0x91C8 | (dst.reg << 9) | dst.reg)      # suba.l An,An
                return
            if size == "l" and fits16(v):
                size = "w"
    szc = 0x3040 if size == "w" else 0x2040
    m = mode_of(enc, src, size, ALL, 2)
    enc.word(szc | (dst.reg << 9) | ea_bits(m, src.reg))
    put_ea_ext(enc, src, m, size)


def i_addsub(enc, mn, size, src, dst):
    """add/sub/adda/suba/addi/subi/addq/subq"""
    sub = mn.startswith("sub")
    if size is None:
        size = "w"
    if dst.mode == AN:
        if size == "b":
            raise AsmError(9, "instruction not supported on selected architecture")
        if mn in ("addi", "subi"):
            raise AsmError(9, "instruction not supported on selected architecture")
        if mn in ("addq", "subq"):
            i_quick(enc, sub, size, src, dst)
            return
        if src.mode == IMM:
            v = imm_val(enc, src)
            if v is not None:
                if v == 0:
                    return                                   # adda #0 / suba #0 : supprimé
                if not sub:
                    if 1 <= v <= 8:
                        enc.word((0x5080 if size == "l" else 0x5040) | ((v & 7) << 9) | 8 | dst.reg)
                        return
                    if -8 <= v <= -1:
                        enc.word((0x5180 if size == "l" else 0x5140) | (((-v) & 7) << 9) | 8 | dst.reg)
                        return
                    if fits16(v):
                        enc.word(0x41E8 | (dst.reg << 9) | dst.reg)
                        enc.word(v & 0xFFFF)
                        return
                else:
                    if 1 <= v <= 8:
                        enc.word((0x5180 if size == "l" else 0x5140) | ((v & 7) << 9) | 8 | dst.reg)
                        return
                    if fits16(s32(-v)):
                        enc.word(0x41E8 | (dst.reg << 9) | dst.reg)
                        enc.word((-v) & 0xFFFF)
                        return
        base = 0x9000 if sub else 0xD000
        m = mode_of(enc, src, size, ALL, 2)
        enc.word(base | (dst.reg << 9) | (0x1C0 if size == "l" else 0xC0) | ea_bits(m, src.reg))
        put_ea_ext(enc, src, m, size)
        return
    if mn in ("adda", "suba"):
        raise AsmError(2, "address register required")
    if mn in ("addq", "subq"):
        i_quick(enc, sub, size, src, dst)
        return
    if src.mode == IMM:
        v = imm_val(enc, src)
        if v is not None and 1 <= v <= 8:
            i_quick(enc, sub, size, src, dst)
            return
        if dst.mode == DN and mn in ("add", "sub"):
            base = 0x9000 if sub else 0xD000
            enc.word(base | (dst.reg << 9) | (SZ2[size] << 6) | 0x3C)
            emit_ext(enc, src, IMM, size)
            return
        # addi / subi
        base = 0x0400 if sub else 0x0600
        i_simple_imm(enc, base | (SZ2[size] << 6), src, dst, size, DALT)
        return
    if mn in ("addi", "subi"):
        raise AsmError(2, "immediate operand required")
    base = 0x9000 if sub else 0xD000
    if dst.mode == DN:
        if size == "b" and src.mode == AN:
            raise AsmError(9, "instruction not supported on selected architecture")
        m = mode_of(enc, src, size, ALL, 2)
        enc.word(base | (dst.reg << 9) | (SZ2[size] << 6) | ea_bits(m, src.reg))
        put_ea_ext(enc, src, m, size)
        return
    if src.mode == DN:
        m = mode_of(enc, dst, size, MALT, 2)
        enc.word(base | (src.reg << 9) | 0x100 | (SZ2[size] << 6) | ea_bits(m, dst.reg))
        put_ea_ext(enc, dst, m, size)
        return
    raise AsmError(9, "instruction not supported on selected architecture")


def i_simple_imm(enc, opw, src, dst, size, allowed):
    """forme immédiate (ori/andi/subi/addi/eori/cmpi) : mot, immédiat, extension de l'ea"""
    nimm = 4 if size == "l" else 2
    m = mode_of(enc, dst, size, allowed, 2 + nimm)
    enc.word(opw | ea_bits(m, dst.reg))
    emit_ext(enc, src, IMM, size)
    put_ea_ext(enc, dst, m, size)


def i_quick(enc, sub, size, src, dst):
    if src.mode != IMM:
        raise AsmError(2, "immediate operand required")
    v = imm_val(enc, src)
    if v is None:
        v = 1
    if not (1 <= v <= 8):
        raise AsmError(2040, "immediate operand out of range")
    if dst.mode == AN and size == "b":
        raise AsmError(9, "instruction not supported on selected architecture")
    m = mode_of(enc, dst, size, ALT, 2)
    enc.word(0x5000 | (0x100 if sub else 0) | ((v & 7) << 9) | (SZ2[size] << 6) | ea_bits(m, dst.reg))
    put_ea_ext(enc, dst, m, size)


def i_logic(enc, mn, size, src, dst):
    """and/or/eor (+ formes i, ccr, sr)"""
    base_name = mn.rstrip("i") if mn != "ori" else "or"
    if mn in ("andi", "ori", "eori"):
        base_name = mn[:-1]
    if size is None:
        size = "w"
    if dst.mode in (CCR, SR):
        if src.mode != IMM:
            raise AsmError(2, "immediate operand required")
        code = {"and": 0x0200, "or": 0x0000, "eor": 0x0A00}[base_name]
        enc.word(code | (0x3C if dst.mode == CCR else 0x7C))
        v = imm_val(enc, src)
        enc.word(0 if v is None else check_imm(v, "b" if dst.mode == CCR else "w"))
        return
    if src.mode == IMM:
        v = imm_val(enc, src)
        mask = {"b": 0xFF, "w": 0xFFFF, "l": 0xFFFFFFFF}[size]
        if v is not None and dst.mode != AN:
            if base_name == "and" and u32(v) == mask:
                i_simple(enc, 0x4A00 | (SZ2[size] << 6), dst, size, DALT)          # tst
                return
            if base_name == "or" and v == 0:
                i_simple(enc, 0x4A00 | (SZ2[size] << 6), dst, size, DALT)
                return
            if base_name == "eor":
                if (u32(v) & mask) == mask:
                    i_simple(enc, 0x4600 | (SZ2[size] << 6), dst, size, DALT)      # not
                    return
                if v == 0:
                    i_simple(enc, 0x4A00 | (SZ2[size] << 6), dst, size, DALT)
                    return
        if dst.mode == DN and mn in ("and", "or"):
            base = 0xC000 if base_name == "and" else 0x8000
            enc.word(base | (dst.reg << 9) | (SZ2[size] << 6) | 0x3C)
            emit_ext(enc, src, IMM, size)
            return
        code = {"and": 0x0200, "or": 0x0000, "eor": 0x0A00}[base_name]
        i_simple_imm(enc, code | (SZ2[size] << 6), src, dst, size, DALT)
        return
    if mn in ("andi", "ori", "eori"):
        raise AsmError(2, "immediate operand required")
    if base_name == "eor":
        if src.mode != DN:
            raise AsmError(9, "instruction not supported on selected architecture")
        m = mode_of(enc, dst, size, DALT, 2)
        enc.word(0xB100 | (src.reg << 9) | (SZ2[size] << 6) | ea_bits(m, dst.reg))
        put_ea_ext(enc, dst, m, size)
        return
    base = 0xC000 if base_name == "and" else 0x8000
    if dst.mode == DN:
        m = mode_of(enc, src, size, DATA, 2)
        enc.word(base | (dst.reg << 9) | (SZ2[size] << 6) | ea_bits(m, src.reg))
        put_ea_ext(enc, src, m, size)
        return
    if src.mode == DN:
        m = mode_of(enc, dst, size, MALT, 2)
        enc.word(base | (src.reg << 9) | 0x100 | (SZ2[size] << 6) | ea_bits(m, dst.reg))
        put_ea_ext(enc, dst, m, size)
        return
    raise AsmError(9, "instruction not supported on selected architecture")


def i_cmp(enc, mn, size, src, dst):
    if size is None:
        size = "w"
    if mn == "cmpm":
        if src.mode != POSTINC or dst.mode != POSTINC:
            raise AsmError(2, "invalid operand")
        enc.word(0xB108 | (dst.reg << 9) | (SZ2[size] << 6) | src.reg)
        return
    if dst.mode == AN:
        if mn == "cmpi" or size == "b":
            raise AsmError(9, "instruction not supported on selected architecture")
        if src.mode == IMM and size == "l":
            v = imm_val(enc, src)
            if v is not None and fits16(v):
                size = "w"
        m = mode_of(enc, src, size, ALL, 2)
        enc.word(0xB000 | (dst.reg << 9) | (0x1C0 if size == "l" else 0xC0) | ea_bits(m, src.reg))
        put_ea_ext(enc, src, m, size)
        return
    if mn == "cmpa":
        raise AsmError(2, "address register required")
    if src.mode == IMM:
        v = imm_val(enc, src)
        if v == 0:
            i_simple(enc, 0x4A00 | (SZ2[size] << 6), dst, size, DALT)              # tst
            return
        if dst.mode == DN and mn == "cmp":
            enc.word(0xB000 | (dst.reg << 9) | (SZ2[size] << 6) | 0x3C)
            emit_ext(enc, src, IMM, size)
            return
        i_simple_imm(enc, 0x0C00 | (SZ2[size] << 6), src, dst, size, DALT)
        return
    if mn == "cmpi":
        raise AsmError(2, "immediate operand required")
    if dst.mode != DN:
        raise AsmError(9, "instruction not supported on selected architecture")
    if size == "b" and src.mode == AN:
        raise AsmError(9, "instruction not supported on selected architecture")
    m = mode_of(enc, src, size, ALL, 2)
    enc.word(0xB000 | (dst.reg << 9) | (SZ2[size] << 6) | ea_bits(m, src.reg))
    put_ea_ext(enc, src, m, size)


def i_shift(enc, mn, size, ops):
    kinds = {"as": 0, "ls": 1, "rox": 2, "ro": 3}
    d = 1 if mn.endswith("l") else 0
    k = kinds[mn[:-1]]
    seul = len(ops) == 1
    if len(ops) == 1:
        o = ops[0]
        if o.mode == DN:      # forme « asl d0 » = #1
            ops = [Op(IMM, expr=Expr(("n", 1), [])), o]
        else:
            if size not in (None, "w"):
                raise AsmError(9, "instruction not supported on selected architecture")
            i_simple(enc, 0xE0C0 | (k << 9) | (d << 8), o, "w", MALT)
            return
    need(ops, 2)
    src, dst = ops
    if size is None:
        size = "w"
    if dst.mode != DN:
        raise AsmError(9, "instruction not supported on selected architecture")
    if src.mode == DN:
        enc.word(0xE000 | (src.reg << 9) | (d << 8) | (SZ2[size] << 6) | 0x20 | (k << 3) | dst.reg)
        return
    if src.mode != IMM:
        raise AsmError(2, "invalid operand")
    v = imm_val(enc, src)
    if v is None:
        v = 1
    if not (1 <= v <= 8):
        raise AsmError(2040, "immediate operand out of range")
    if k == 0 and d == 1 and v == 1:        # asl #1,Dn -> add Dn,Dn (forme « asl Dn » : vasm prend D0 comme destination)
        enc.word(0xD000 | ((0 if seul else dst.reg) << 9) | (SZ2[size] << 6) | dst.reg)
        return
    enc.word(0xE000 | ((v & 7) << 9) | (d << 8) | (SZ2[size] << 6) | (k << 3) | dst.reg)


def i_bit(enc, mn, size, src, dst):
    t = {"btst": 0, "bchg": 1, "bclr": 2, "bset": 3}[mn]
    allowed = DATA if t == 0 else DALT
    if src.mode == DN:
        if t == 0:
            allowed = DATA
        m = mode_of(enc, dst, "b", allowed, 2)
        enc.word(0x0100 | (src.reg << 9) | (t << 6) | ea_bits(m, dst.reg))
        put_ea_ext(enc, dst, m, "b")
        return
    if src.mode != IMM:
        raise AsmError(2, "invalid operand")
    if dst.mode == IMM:
        raise AsmError(9, "instruction not supported on selected architecture")
    v = imm_val(enc, src)
    if v is None:
        v = 0
    allowed = (DATA - {IMM}) if t == 0 else DALT
    m = mode_of(enc, dst, "b", allowed, 4)
    enc.word(0x0800 | (t << 6) | ea_bits(m, dst.reg))
    enc.word(v & 0xFF)
    put_ea_ext(enc, dst, m, "b")


def i_movem(enc, size, src, dst):
    if size is None:
        size = "w"
    if size == "b":
        raise AsmError(9, "instruction not supported on selected architecture")
    szb = 0x40 if size == "l" else 0
    if src.mode in (REGLIST, DN, AN) and dst.mode not in (DN, AN, REGLIST):
        mask = src.mask if src.mode == REGLIST else (1 << ((8 if src.mode == AN else 0) + src.reg))
        if mask == 0:
            return
        if dst.mode == PREDEC:
            rev = 0
            for i in range(16):
                if mask & (1 << i):
                    rev |= 1 << (15 - i)
            enc.word(0x4880 | szb | ea_bits(PREDEC, dst.reg))
            enc.word(rev)
            return
        m = mode_of(enc, dst, size, CALT, 4)
        enc.word(0x4880 | szb | ea_bits(m, dst.reg))
        enc.word(mask)
        put_ea_ext(enc, dst, m, size)
        return
    if dst.mode in (REGLIST, DN, AN):
        mask = dst.mask if dst.mode == REGLIST else (1 << ((8 if dst.mode == AN else 0) + dst.reg))
        if mask == 0:
            return
        if dst.mode == AN or (dst.mode == REGLIST and mask & 0xFF == 0 and bin(mask).count("1") == 1):
            r = (mask.bit_length() - 1) - 8
            i_movea(enc, size, src, Op(AN, r))
            return
        allowed = CTRL | {POSTINC}
        m = mode_of(enc, src, size, allowed, 4)
        enc.word(0x4C80 | szb | ea_bits(m, src.reg))
        enc.word(mask)
        put_ea_ext(enc, src, m, size)
        return
    raise AsmError(2, "invalid operand")


def i_lea(enc, src, dst):
    if dst.mode != AN:
        raise AsmError(2, "address register required")
    r = dst.reg
    if src.mode == ABS or src.mode == ABSW or src.mode == ABSL:
        v = imm_val(enc, src)
        if src.mode == ABS and v == 0:
            enc.word(0x91C8 | (r << 9) | r)         # suba.l An,An
            return
    if src.mode == IND and src.reg == r:
        return
    if src.mode == DISP and src.dsize is None:
        v = imm_val(enc, src)
        if v is not None:
            if v == 0 and src.reg == r:
                return
            if v == 0:
                enc.word(0x41D0 | (r << 9) | src.reg)
                return
            if src.reg == r and 1 <= v <= 8:
                enc.word(0x5088 | ((v & 7) << 9) | r)
                return
            if src.reg == r and -8 <= v <= -1:
                enc.word(0x5188 | (((-v) & 7) << 9) | r)
                return
            if not fits16(v):
                enc.warn.append((2048, "lea-displacement out of range, changed into move/add"))
                if src.reg != r:
                    enc.word(0x2048 | (r << 9) | src.reg)      # movea.l Am,An
                enc.word(0xD1FC | (r << 9))                    # adda.l #d,An
                enc.long(v)
                return
    m = mode_of(enc, src, "l", CTRL, 2)
    enc.word(0x41C0 | (r << 9) | ea_bits(m, src.reg))
    put_ea_ext(enc, src, m, "l")


# Relâchement des branchements (calé sur vasm 2.0f par sondes, sans son code ; voir RAPPORT.md §3) :
# - passe 0 : aucune étiquette utilisable -> formes longues (bcc.w, jmp.l, absolu long) ;
# - passes suivantes : étiquettes mises à jour au fil de la passe (les cibles en avant gardent la valeur de la passe
#   précédente) ;
# - branchement « vers l'instruction suivante » (cible en avant = adresse + taille précédente, dans l'agencement
#   courant ET dans le précédent) : bra/bcc supprimé, bsr en forme mot ; un jmp devenu bra puis supprimé l'est
#   définitivement ;
# - court : |d| <= 127, d != 0 ; pour une cible en avant d'un bcc/bra déjà en forme mot, la portée est testée en
#   retranchant les 2 octets que gagnera l'instruction ; d = 0 (cible à pc+2) : forme transitoire de 2 octets ;
# - amortissement : une instruction qui a changé de taille plus de MAX_CHANGES fois garde sa suppression.
MAX_CHANGES = 200
RAPIDE = True                 # passes de dimensionnement accélérées (mêmes résultats ; False pour contrôle)
STICKY_APRES = 302            # après ce nombre de passes, toute suppression de branchement est définitive


def branch(enc, cond, o, explicit, prevsize, dejmp=False):
    """Bcc / BRA / BSR. explicit : 's' 'w' 'l' ou None. prevsize : (adresse, taille) à la passe précédente ou None.
    dejmp : instruction écrite jmp/jsr, transformée en bra/bsr."""
    if o.mode not in (ABS, ABSW, ABSL):
        raise AsmError(2, "invalid branch target")
    v = enc.val(o.expr)
    pc = enc.pc
    if explicit in ("s", "b"):
        if v is None:
            enc.word(0x6000 | (cond << 8))
            return
        d = s32(v - (pc + 2))
        if d == 0 and cond == 1:
            raise AsmError(2029, "branch destination out of range")
        if d == 0:
            enc.warn.append((2058, "short-branch to following instruction turned into a nop"))
            enc.word(0x4DD6)
            return
        if not fits8(d):
            raise AsmError(2029, "branch destination out of range")
        enc.word(0x6000 | (cond << 8) | (d & 0xFF))
        return
    if explicit == "w":
        enc.word(0x6000 | (cond << 8))
        if v is None:
            enc.word(0)
            return
        d = s32(v - (pc + 2))
        if not fits16(d):
            raise AsmError(2029, "branch destination out of range")
        enc.word(d & 0xFFFF)
        return
    if explicit == "l":
        raise AsmError(9, "instruction not supported on selected architecture")
    if v is None:                                       # passe 0 / cible inconnue : forme mot
        enc.word(0x6000 | (cond << 8))
        enc.word(0)
        return
    ps = prevsize[1] if prevsize is not None else None
    if ps == 0 and cond != 1 and (dejmp or enc.ctx.passes > STICKY_APRES or enc.changes > MAX_CHANGES):
        if enc.final and v != pc:
            if dejmp:                                   # défaut de vasm reproduit (même sortie), mais signalé
                enc.warn.append((9001, "jmp/jsr deleted although it does not target the next instruction "
                                       "(vasm behaviour reproduced: CHECK THIS CODE)"))
            else:                                       # garde : incohérence du modèle -> modèle de secours / erreur
                raise AsmError(3, "relâchement incohérent (branchement supprimé qui ne vise pas l'instruction "
                                  "suivante) : assembler avec vasm (HSFA_ASM=vasm) et signaler la source")
        return                                          # supprimé définitivement
    if ps is not None and enc.en_avant(o.expr) and v == pc + ps and (dejmp or v == prevsize[0] + ps) \
            and not (dejmp and ps == 6):
        if cond != 1:
            return                                      # vers l'instruction suivante : supprimé
        enc.word(0x6100)                                # bsr vers l'instruction suivante : forme mot
        enc.word(s32(v - (pc + 2)) & 0xFFFF)
        return
    d = s32(v - (pc + 2))
    ds = d - 2 if (ps == 4 and v > pc and not dejmp) else d
    if d == 0 and cond != 1:
        enc.warn.append((2058, "short-branch to following instruction turned into a nop"))
        enc.word(0x4DD6)                                # forme transitoire (cible à pc+2 pendant le relâchement)
        return
    if fits8(ds) and ds != 0 and d != 0:
        enc.word(0x6000 | (cond << 8) | (d & 0xFF))
        return
    if fits16(d):
        enc.word(0x6000 | (cond << 8))
        enc.word(d & 0xFFFF)
        return
    enc.warn.append((2047, "branch out of range changed to jmp"))
    if cond == 0:
        enc.word(0x4EF9)
        enc.long(v)
    elif cond == 1:
        enc.word(0x4EB9)
        enc.long(v)
    else:
        enc.word(0x6006 | ((cond ^ 1) << 8))            # b!cc *+8 ; jmp
        enc.word(0x4EF9)
        enc.long(v)


def i_jmp(enc, jsr, o, prevsize):
    """jmp/jsr : absolu court si la valeur tient sur 16 bits, sinon bra/bsr si la cible est à portée, sinon long"""
    if o.mode == ABS:
        v = enc.val(o.expr)
        if v is None:
            enc.word(0x4EB9 if jsr else 0x4EF9)
            enc.long(0)
            return
        if fits16(v):
            enc.word(0x4EB8 if jsr else 0x4EF8)
            enc.word(v & 0xFFFF)
            return
        d = s32(v - (enc.pc + 2))
        if fits16(d):
            branch(enc, 1 if jsr else 0, o, None, prevsize, True)
            return
        enc.word(0x4EB9 if jsr else 0x4EF9)
        enc.long(v)
        return
    i_simple(enc, 0x4E80 if jsr else 0x4EC0, o, "l", CTRL)


SANS_TAILLE = {"jmp", "jsr", "unlk", "trap", "stop", "nop", "rts", "rte", "rtr", "reset", "trapv", "illegal"}
BWL = {"b", "w", "l"}
TAILLES = {"move": BWL, "movea": {"w", "l"}, "adda": {"w", "l"}, "suba": {"w", "l"}, "cmpa": {"w", "l"},
           "nbcd": {"b"}, "tas": {"b"}, "abcd": {"b"}, "sbcd": {"b"}, "pea": {"l"}, "lea": {"l"}, "exg": {"l"},
           "swap": {"w"}, "ext": {"w", "l"}, "movep": {"w", "l"}, "movem": {"w", "l"}, "moveq": {"l"},
           "muls": {"w"}, "mulu": {"w"}, "divs": {"w"}, "divu": {"w"}, "chk": {"w"}, "link": {"w"}}
for _m in ("add", "sub", "and", "or", "eor", "cmp", "addi", "subi", "andi", "ori", "eori", "cmpi", "addq", "subq",
           "cmpm", "clr", "neg", "negx", "not", "tst", "addx", "subx", "asl", "asr", "lsl", "lsr", "rol", "ror", "roxl",
           "roxr", "btst", "bchg", "bclr", "bset"):
    TAILLES[_m] = BWL
for _m in SCC:
    TAILLES[_m] = {"b"}
for _m in DBCC:
    TAILLES[_m] = {"w"}


def controle_taille(enc, mn, size, ops):
    """tailles admises (comme vasm) ; renvoie la taille à employer"""
    if size is None:
        return None
    if mn in SANS_TAILLE:
        enc.warn.append((2036, "extension for unsized instruction ignored"))
        return None
    if mn in BCC:
        if size == "l":
            enc.warn.append((2076, "deprecated B<cc>.L on 68000 transformed into B<cc>.W"))
            return "w"
        return size
    if size == "l" and mn in ("muls", "mulu", "divs", "divu", "chk", "link") or (size == "l" and mn in DBCC):
        raise AsmError(2001, "instruction not supported on selected architecture")
    ok = TAILLES.get(mn)
    if ok is not None:
        if mn in ("btst", "bchg", "bclr", "bset") and len(ops) == 2:
            ok = {"l"} if ops[1].mode == DN else {"b"}
        elif mn in ("asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr") and len(ops) == 1 and ops[0].mode != DN:
            ok = {"w"}
        elif mn == "movea" and len(ops) == 2 and ops[1].mode != AN:
            ok = BWL                                       # alias de move (avertissement 2034)
        elif mn == "move" and len(ops) == 2 and (ops[0].mode in (SR, CCR) or ops[1].mode in (SR, CCR)):
            ok = {"w"}
        elif mn == "move" and len(ops) == 2 and (ops[0].mode == USP or ops[1].mode == USP):
            ok = {"l"}
        elif mn in ("andi", "ori", "eori", "and", "or", "eor") and len(ops) == 2 and ops[1].mode == CCR:
            ok = {"b"}
        elif mn in ("andi", "ori", "eori", "and", "or", "eor") and len(ops) == 2 and ops[1].mode == SR:
            ok = {"w"}
        if size not in ok:
            raise AsmError(2035, "illegal opcode extension")
    return size


def encode(enc, mn, size, ops, prevsize):
    """mn : mnémonique en minuscules sans taille ; size : 'b' 'w' 'l' 's' ou None"""
    n = len(ops)
    size = controle_taille(enc, mn, size, ops)
    if mn in BCC:
        need(ops, 1)
        branch(enc, BCC[mn], ops[0], size, prevsize)
        return
    if mn in ("move", "movea"):
        need(ops, 2)
        if mn == "movea" and ops[1].mode != AN:
            enc.warn.append((2034, "deprecated instruction alias"))
        i_move(enc, size, ops[0], ops[1], mn == "movea")
        return
    if mn == "moveq":
        need(ops, 2)
        if ops[0].mode != IMM or ops[1].mode != DN:
            raise AsmError(2, "invalid operand")
        v = imm_val(enc, ops[0])
        if v is None:
            v = 0
        if not (-128 <= v <= 255):
            raise AsmError(2040, "immediate operand out of range")
        if v > 127 and size is None:
            enc.warn.append((2028, "using signed operand as unsigned: %d (valid: -128..127), %d to fix" % (v, v - 256)))
        enc.word(0x7000 | (ops[1].reg << 9) | (v & 0xFF))
        return
    if mn in ("add", "sub", "adda", "suba", "addi", "subi", "addq", "subq"):
        need(ops, 2)
        i_addsub(enc, mn, size, ops[0], ops[1])
        return
    if mn in ("and", "or", "eor", "andi", "ori", "eori"):
        need(ops, 2)
        i_logic(enc, mn, size, ops[0], ops[1])
        return
    if mn in ("cmp", "cmpa", "cmpi", "cmpm"):
        need(ops, 2)
        i_cmp(enc, mn, size, ops[0], ops[1])
        return
    if mn in ("tst", "clr", "neg", "negx", "not"):
        need(ops, 1)
        if size is None:
            size = "w"
        if mn == "clr" and size == "l" and ops[0].mode == DN:
            enc.word(0x7000 | (ops[0].reg << 9))            # moveq #0,Dn
            return
        code = {"tst": 0x4A00, "clr": 0x4200, "neg": 0x4400, "negx": 0x4000, "not": 0x4600}[mn]
        i_simple(enc, code | (SZ2[size] << 6), ops[0], size, DALT)
        return
    if mn in ("asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr"):
        i_shift(enc, mn, size, ops)
        return
    if mn in ("btst", "bchg", "bclr", "bset"):
        need(ops, 2)
        i_bit(enc, mn, size, ops[0], ops[1])
        return
    if mn in DBCC:
        need(ops, 2)
        if ops[0].mode != DN:
            raise AsmError(2, "data register required")
        enc.word(0x50C8 | (DBCC[mn] << 8) | ops[0].reg)
        v = enc.val(ops[1].expr)
        if v is None:
            enc.word(0)
            return
        d = s32(v - (enc.pc + 2))
        if not fits16(d):
            raise AsmError(2029, "branch destination out of range")
        enc.word(d & 0xFFFF)
        return
    if mn in SCC:
        need(ops, 1)
        i_simple(enc, 0x50C0 | (SCC[mn] << 8), ops[0], "b", DALT)
        return
    if mn == "lea":
        need(ops, 2)
        i_lea(enc, ops[0], ops[1])
        return
    if mn == "pea":
        need(ops, 1)
        i_simple(enc, 0x4840, ops[0], "l", CTRL)
        return
    if mn in ("jmp", "jsr"):
        need(ops, 1)
        i_jmp(enc, mn == "jsr", ops[0], prevsize)
        return
    if mn == "movem":
        need(ops, 2)
        i_movem(enc, size, ops[0], ops[1])
        return
    if mn == "swap":
        need(ops, 1)
        exige(ops[0], DN)
        enc.word(0x4840 | ops[0].reg)
        return
    if mn == "ext":
        need(ops, 1)
        exige(ops[0], DN)
        enc.word((0x48C0 if size == "l" else 0x4880) | ops[0].reg)
        return
    if mn == "exg":
        need(ops, 2)
        a, b = ops
        if a.mode == DN and b.mode == DN:
            enc.word(0xC140 | (a.reg << 9) | b.reg)
        elif a.mode == AN and b.mode == AN:
            enc.word(0xC148 | (a.reg << 9) | b.reg)
        elif a.mode == DN and b.mode == AN:
            enc.word(0xC188 | (a.reg << 9) | b.reg)
        elif a.mode == AN and b.mode == DN:
            enc.word(0xC188 | (b.reg << 9) | a.reg)
        else:
            raise AsmError(2, "invalid operand")
        return
    if mn in ("muls", "mulu", "divs", "divu", "chk"):
        need(ops, 2)
        if size not in (None, "w"):
            raise AsmError(9, "instruction not supported on selected architecture")
        code = {"muls": 0xC1C0, "mulu": 0xC0C0, "divs": 0x81C0, "divu": 0x80C0, "chk": 0x4180}[mn]
        if ops[1].mode != DN:
            raise AsmError(2, "data register required")
        i_simple(enc, code | (ops[1].reg << 9), ops[0], "w", DATA)
        return
    if mn in ("abcd", "sbcd", "addx", "subx"):
        need(ops, 2)
        a, b = ops
        base = {"abcd": 0xC100, "sbcd": 0x8100, "addx": 0xD100, "subx": 0x9100}[mn]
        if mn in ("addx", "subx"):
            base |= SZ2[size or "w"] << 6
        if a.mode == DN and b.mode == DN:
            enc.word(base | (b.reg << 9) | a.reg)
        elif a.mode == PREDEC and b.mode == PREDEC:
            enc.word(base | (b.reg << 9) | 8 | a.reg)
        else:
            raise AsmError(2, "invalid operand")
        return
    if mn in ("nbcd", "tas"):
        need(ops, 1)
        i_simple(enc, 0x4800 if mn == "nbcd" else 0x4AC0, ops[0], "b", DALT)
        return
    if mn == "link":
        need(ops, 2)
        exige(ops[0], AN)
        exige(ops[1], IMM)
        enc.word(0x4E50 | ops[0].reg)
        v = imm_val(enc, ops[1])
        enc.word(0 if v is None else v & 0xFFFF)
        return
    if mn == "unlk":
        need(ops, 1)
        exige(ops[0], AN)
        enc.word(0x4E58 | ops[0].reg)
        return
    if mn == "trap":
        need(ops, 1)
        exige(ops[0], IMM)
        v = imm_val(enc, ops[0])
        enc.word(0x4E40 | ((v or 0) & 15))
        return
    if mn == "stop":
        need(ops, 1)
        exige(ops[0], IMM)
        v = imm_val(enc, ops[0])
        enc.word(0x4E72)
        enc.word((v or 0) & 0xFFFF)
        return
    if mn == "movep":
        need(ops, 2)
        a, b = ops
        sz = 0x40 if size == "l" else 0
        if a.mode == DN:
            mo = b
            enc.word(0x0188 | sz | (a.reg << 9) | (mo.reg))
        else:
            mo = a
            enc.word(0x0108 | sz | (b.reg << 9) | (mo.reg))
        if mo.mode == IND:
            enc.warn.append((2049, "translated (A%d) into (0,A%d) for movep" % (mo.reg, mo.reg)))
        v = 0 if mo.mode == IND else imm_val(enc, mo)
        enc.word((v or 0) & 0xFFFF)
        return
    simples = {"nop": 0x4E71, "rts": 0x4E75, "rte": 0x4E73, "rtr": 0x4E77, "reset": 0x4E70, "trapv": 0x4E76,
               "illegal": 0x4AFC}
    if mn in simples:
        if n:
            raise AsmError(2, "no operands expected")
        enc.word(simples[mn])
        return
    raise AsmError(1, "instruction not supported on selected architecture")


# ----------------------------------------------------------------------------------------------------------------
# Source : lignes, étiquettes, directives
# ----------------------------------------------------------------------------------------------------------------
LABEL_RE = re.compile(r"^(\.?[A-Za-z_][A-Za-z0-9_]*\$?)(::?)?")
IDENT_RE = re.compile(r"^\.?[A-Za-z_][A-Za-z0-9_]*\$?$")
WIDTH = {"b": 1, "w": 2, "l": 4}
COND_DIRS = ("ifd", "ifnd", "if", "ifeq", "ifne", "ifgt", "ifge", "iflt", "ifle", "else", "elseif", "endif", "endc")


class Sym:
    __slots__ = ("nom", "kind", "value", "expr", "pc", "line", "refd", "busy", "sect", "idx", "redef")

    def __init__(self, nom, kind, line):
        self.nom = nom
        self.kind = kind          # 'L' étiquette, 'E' expression (equ / = / set)
        self.value = None
        self.expr = None
        self.pc = None
        self.line = line
        self.refd = False
        self.busy = False
        self.sect = None
        self.idx = None
        self.redef = False


class Stmt:
    __slots__ = ("kind", "line", "labels", "mn", "size", "ops", "args", "nbytes", "fixed", "addr", "paddr", "sect", "out",
                 "warn", "pad", "texte", "src", "idx", "changes", "memo")

    def __init__(self, kind, line):
        self.kind = kind
        self.line = line          # (indice du fichier, numéro de ligne)
        self.labels = []
        self.mn = None
        self.size = None
        self.ops = None
        self.args = None
        self.nbytes = None        # taille à la passe précédente
        self.fixed = None         # octets figés (instruction sans dépendance)
        self.addr = 0
        self.sect = 0
        self.out = b""
        self.warn = ()
        self.pad = 0
        self.changes = 0
        self.memo = None


class Bloc:
    """suite d'énoncés de taille fixe ; agencement (taille, étiquettes, equ) calculé par parité de départ"""
    __slots__ = ("sts", "cache")

    def __init__(self, sts):
        self.sts = sts
        self.cache = {}

    def agencement(self, parite, asm):
        r = self.cache.get(parite)
        if r is None:
            pc = parite
            labs = []
            equs = []
            for st in self.sts:
                k = st.kind
                if k == "equ":
                    equs.append((st.args, pc - parite))
                    continue
                if k == "ins" and pc & 1:
                    pc += 1
                for nom in st.labels:
                    labs.append((nom, pc - parite))
                if k == "ins":
                    pc += st.fixed
                elif k == "dc":
                    pc += st.nbytes
                elif k == "dcb":
                    pc += ev(st.args[0].t, asm, None) * WIDTH[st.size]
            r = self.cache[parite] = (pc - parite, labs, equs)
        return r


class Section:
    __slots__ = ("org", "nom", "debut", "fin")

    def __init__(self, org, nom):
        self.org = org
        self.nom = nom
        self.debut = org
        self.fin = org


def strip_comment(l):
    """retire le commentaire (« ; » hors chaînes)"""
    if ";" not in l:
        return l
    q = None
    for i, c in enumerate(l):
        if q:
            if c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c == ";":
            return l[:i]
    return l


class Assembleur:
    def __init__(self, maxerrors=50):
        self.syms = {}
        self.stmts = []
        self.sections = []
        self.fichiers = []        # [(chemin, [lignes octets])]
        self.erreurs = []         # (fichier, ligne, num, msg)
        self.avert = []
        self.globale = None
        self.maxerrors = maxerrors
        self.final = False
        self.passes = 0
        self.passe0 = False

    # --- symboles -------------------------------------------------------------------------------------------
    def resolve(self, nom):
        if nom.startswith(".") or nom.endswith("$"):          # locale : portée = dernière étiquette globale
            return (self.globale or "") + ">" + nom
        return nom

    def symval(self, nom):
        if self.passe0:               # passe initiale (lecture) : aucune étiquette n'est encore utilisable
            s = self.syms.get(nom)
            if s is not None and s.kind == "L":
                raise Unknown()
        s = self.syms.get(nom)
        if s is None or s.kind is None:
            if self.final:
                raise AsmError(2, "undefined symbol <%s>" % self.affiche(nom))
            raise Unknown()
        if s.kind == "L":
            if s.value is None:
                if self.final:
                    raise AsmError(2, "undefined symbol <%s>" % self.affiche(nom))
                raise Unknown()
            return s.value
        if s.value is not None and s.expr is None:
            return s.value
        if s.busy:
            raise AsmError(5, "circular definition of symbol <%s>" % self.affiche(nom))
        s.busy = True
        try:
            return ev(s.expr.t, self, s.pc)
        finally:
            s.busy = False

    @staticmethod
    def affiche(nom):
        i = nom.find(">")
        return nom[i + 1:] if i >= 0 else nom

    def reference(self, e):
        for n in e.syms:
            s = self.syms.get(n)
            if s is None:
                s = self.syms[n] = Sym(n, None, None)
            s.refd = True

    def definit_label(self, nom, line):
        s = self.syms.get(nom)
        if s is not None and s.kind is not None:
            raise AsmError(2, "label <%s> redefined" % self.affiche(nom))
        if s is None:
            s = self.syms[nom] = Sym(nom, "L", line)
        s.kind = "L"
        s.line = line
        return s

    # --- erreurs ----------------------------------------------------------------------------------------------
    def erreur(self, line, num, msg, warn=False):
        (self.avert if warn else self.erreurs).append((line, num, msg))

    # --- lecture ----------------------------------------------------------------------------------------------
    def lit(self, chemin, data=None):
        if data is None:
            with open(chemin, "rb") as f:
                data = f.read()
        lignes = data.split(b"\n")      # (vasm liste aussi la ligne vide qui suit le dernier saut de ligne)
        idx = len(self.fichiers)
        self.fichiers.append((chemin, lignes))
        if not self.sections:
            self.sections.append(Section(0, None))
        cond = []                 # pile : (actif, deja_vrai)
        actif = True
        for n, brut in enumerate(lignes, 1):
            l = brut.decode("latin-1").rstrip("\r")
            line = (idx, n)
            try:
                st = self.analyse(l, line, cond)
            except AsmError as e:
                self.erreur(line, e.num, e.msg)
                continue
            if st == "end":
                break
        if cond:
            self.erreur((idx, len(lignes)), 2, "if without endif")

    def actif(self, cond):
        return all(c[0] for c in cond)

    def analyse(self, l, line, cond):
        if not l.strip() or l[0] == "*":
            return None
        l = strip_comment(l)
        if not l.strip():
            return None
        label = None
        reste = l
        if not l[0].isspace():
            m = LABEL_RE.match(l)
            if not m:
                raise AsmError(5, "syntax error")
            label = m.group(1)
            reste = l[m.end():]
        else:
            t = l.lstrip()
            m = LABEL_RE.match(t)
            if m and m.group(2):
                label = m.group(1)
                reste = t[m.end():]
        t = reste.strip()
        # mnémonique / directive
        if t.startswith("="):
            mn, ops = "=", t[1:].strip()
        else:
            p = t.split(None, 1)
            mn = p[0] if p else ""
            ops = p[1].strip() if len(p) > 1 else ""
        mnl = mn.lower()
        # assemblage conditionnel
        if mnl in COND_DIRS:
            return self.conditionnel(mnl, ops, cond)
        if not self.actif(cond):
            return None
        if mnl in ("equ", "=", "set"):
            if label is None:
                raise AsmError(5, "missing label for %s" % mn)
            nom = self.resolve(label)
            if not nom.startswith(".") and not label.startswith("."):
                pass
            e = parse_expr(strip_spaces(ops), self)
            self.reference(e)
            s = self.syms.get(nom)
            if s is not None and s.kind is not None and not (mnl == "set" and s.kind == "E"):
                raise AsmError(2, "symbol <%s> redefined" % self.affiche(nom))
            if s is None:
                s = self.syms[nom] = Sym(nom, "E", line)
            s.kind = "E"
            s.redef = mnl == "set"
            s.line = line
            try:                   # valeur immédiate si possible (set : obligatoire)
                v = ev(e.t, self, None)
                s.value = v
                s.expr = None
            except (Unknown, AsmError):
                if mnl == "set":
                    raise AsmError(2, "undefined symbol in set")
                s.expr = e
            st = Stmt("equ", line)
            st.args = s
            self.stmts.append(st)
            return None
        st = None
        if label is not None:
            nom = self.resolve(label)
            if not label.startswith(".") and not label.endswith("$"):
                self.globale = label
                nom = label
            self.definit_label(nom, line)
        if not mn:
            st = Stmt("lab", line)
            if label is not None:
                st.labels.append(nom)
            self.stmts.append(st)
            return None
        base, size = mn, None
        if "." in mn[1:]:
            base, sz = mn.rsplit(".", 1)
            size = sz.lower()
        b = base.lower()
        st = Stmt("ins", line)
        if label is not None:
            st.labels.append(nom)
        st.mn = b
        st.size = size
        if b == "org":
            v = ev(parse_expr(strip_spaces(ops), self).t, self, None)
            sec = Section(u32(v), "org%04d:%x" % (len(self.sections) if self.sections[0].nom is None else len(self.sections) + 1, u32(v)))
            if self.sections and self.sections[0].nom is None and not any(s.kind in ("ins", "dc", "dcb", "ds") for s in self.stmts):
                self.sections = []
                sec.nom = "org%04d:%x" % (1, u32(v))
            else:
                sec.nom = "org%04d:%x" % (len(self.sections) + (0 if self.sections[0].nom is None else 1), u32(v))
            self.sections.append(sec)
            st.kind = "org"
            st.args = len(self.sections) - 1
            self.stmts.append(st)
            return None
        if b == "end":
            return "end"
        if b in ("dc", "dcb", "blk", "ds", "even", "cnop", "align"):
            self.directive(st, b, size, ops)
            self.stmts.append(st)
            return None
        if b in ("include", "incbin", "macro", "rept", "section", "xdef", "xref", "public", "opt", "machine", "mc68000",
                 "list", "nolist", "ttl", "idnt", "printt", "printv", "fail", "endm", "endr", "incdir"):
            raise AsmError(2, "directive <%s> not supported by hsfa_asm68k" % b)
        # instruction
        if size is not None and size not in ("b", "w", "l", "s"):
            raise AsmError(2, "illegal size extension .%s" % size)
        texte = strip_spaces(ops)
        st.ops = [parse_operand(x, self) for x in split_top(texte)] if texte else []
        for o in st.ops:
            if o.expr is not None:
                self.reference(o.expr)
        st.texte = None
        self.stmts.append(st)
        return None

    def conditionnel(self, d, ops, cond):
        parent = self.actif(cond)
        if d in ("endif", "endc"):
            if not cond:
                raise AsmError(2, "endif without if")
            cond.pop()
            return None
        if d == "else" or d == "elseif":
            if not cond:
                raise AsmError(2, "else without if")
            a, deja = cond[-1]
            cond[-1] = (not deja, True)
            return None
        if not parent:
            cond.append((False, True))
            return None
        if d in ("ifd", "ifnd"):
            nom = self.resolve(ops.split()[0])
            s = self.syms.get(nom)
            defini = s is not None and s.kind is not None
            v = defini if d == "ifd" else not defini
        else:
            x = ev(parse_expr(strip_spaces(ops), self).t, self, None)
            v = {"if": x != 0, "ifne": x != 0, "ifeq": x == 0, "ifgt": x > 0, "ifge": x >= 0, "iflt": x < 0,
                 "ifle": x <= 0}[d]
        cond.append((v, v))
        return None

    def directive(self, st, b, size, ops):
        texte = strip_spaces(ops)
        if b == "dc":
            st.kind = "dc"
            size = size or "w"
            if size not in WIDTH:
                raise AsmError(2, "illegal size extension .%s" % size)
            st.size = size
            items = []
            for x in split_top(texte):
                if len(x) >= 2 and x[0] in "'\"" and x[-1] == x[0] and size == "b":
                    items.append(("str", x[1:-1].replace(x[0] * 2, x[0]).encode("latin-1")))
                else:
                    e = parse_expr(x, self)
                    self.reference(e)
                    items.append(("e", e))
            st.args = items
            n = 0
            for k, v in items:
                n += len(v) if k == "str" else WIDTH[size]
            st.nbytes = n
            st.fixed = True
        elif b in ("dcb", "blk"):
            st.kind = "dcb"
            size = size or "w"
            p = split_top(texte)
            cnt = parse_expr(p[0], self)
            val = parse_expr(p[1], self) if len(p) > 1 else Expr(("n", 0), [])
            self.reference(cnt)
            self.reference(val)
            st.size = size
            st.args = (cnt, val)
        elif b == "ds":
            st.kind = "dcb"
            size = size or "w"
            cnt = parse_expr(texte, self)
            self.reference(cnt)
            st.size = size
            st.args = (cnt, Expr(("n", 0), []))
            st.mn = "ds"
        elif b == "even":
            st.kind = "align"
            st.args = (0, 2, False)
        elif b in ("cnop", "align"):
            st.kind = "align"
            if b == "cnop":
                p = split_top(texte)
                off = ev(parse_expr(p[0], self).t, self, None)
                al = ev(parse_expr(p[1], self).t, self, None)
                st.args = (off, al, True)
            else:
                al = ev(parse_expr(texte, self).t, self, None)
                st.args = (0, 1 << al, False)        # align n : 2^n, bourrage de zéros (cnop : NOP)

    # --- passes -----------------------------------------------------------------------------------------------
    def taille(self, st, pc, final):
        """octets de l'énoncé à l'adresse pc ; met à jour st.out / st.warn si final"""
        k = st.kind
        if k == "ins":
            if st.fixed is not None:
                return st.fixed
            enc = Enc(self, pc, final)
            enc.idx = st.idx
            enc.changes = st.changes
            encode(enc, st.mn, st.size, st.ops, None if st.nbytes is None else (st.paddr, st.nbytes))
            if not any(o.dyn for o in st.ops):
                st.fixed = len(enc.w)
                st.out = bytes(enc.w)
                st.warn = enc.warn
            elif final:
                st.out = bytes(enc.w)
                st.warn = enc.warn
            return len(enc.w)
        if k == "dc":
            if final:
                st.out = self.donnees(st, pc)
            return st.nbytes
        if k == "dcb":
            cnt, val = st.args
            try:
                n = ev(cnt.t, self, pc)
            except Unknown:
                raise AsmError(2, "undefined symbol in repeat count")
            if n < 0:
                raise AsmError(2, "negative repeat count")
            w = WIDTH[st.size]
            if final:
                v = ev(val.t, self, pc)
                one = self.pack(v, st.size)
                st.out = one * n
            return n * w
        if k == "align":
            off, al, nop = st.args
            if al <= 0:
                return 0
            cible = ((pc + al - 1) // al) * al + off
            n = cible - pc
            if final:
                out = bytearray()
                if nop:
                    q = pc
                    if q & 1:
                        out.append(0)
                        q += 1
                    while q + 2 <= cible:
                        out += b"\x4e\x71"
                        q += 2
                    if q < cible:
                        out.append(0)
                else:
                    out = bytearray(n)
                st.out = bytes(out)
            return n
        return 0

    def pack(self, v, size):
        if size == "b":
            if not (-128 <= v <= 255):
                raise AsmError(2040, "data out of range")
            return bytes((v & 0xFF,))
        if size == "w":
            if not (-32768 <= v <= 65535):
                raise AsmError(2040, "data out of range")
            return bytes(((v >> 8) & 0xFF, v & 0xFF))
        v &= 0xFFFFFFFF
        return bytes(((v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF))

    def donnees(self, st, pc):
        out = bytearray()
        for k, v in st.args:
            if k == "str":
                out += v
            else:
                out += self.pack(ev(v.t, self, pc + len(out)), st.size)
        return bytes(out)

    def passe(self, final):
        if not getattr(self, "indexe_fait", False):
            self.indexe()
        self.final = final
        change = False
        sect = 0
        pc = self.sections[0].org
        for s in self.sections:
            s.fin = s.org
        for st in self.stmts:
            k = st.kind
            if k == "org":
                self.sections[sect].fin = pc
                sect = st.args
                pc = self.sections[sect].org
                st.addr = pc
                st.sect = sect
                continue
            if k == "equ":
                st.args.pc = pc
                st.addr = pc
                continue
            pad = 0
            if k == "ins" and pc & 1:
                pad = 1
                pc += 1
            st.pad = pad
            st.paddr = st.addr
            st.addr = pc
            st.sect = sect
            for nom in st.labels:
                sy = self.syms[nom]
                if sy.value != pc:
                    if sy.value is not None:
                        change = True
                    sy.value = pc
                sy.sect = sect
            try:
                n = self.taille(st, pc, final)
            except AsmError as e:
                if final:
                    self.erreur(st.line, e.num, e.msg)
                    st.out = b""
                n = st.nbytes or 0
            if final and k == "ins" and pad:
                self.erreur(st.line, 51, "instruction has been auto-aligned", warn=True)
            if final and k == "ins":
                for num, msg in st.warn:
                    self.erreur(st.line, num, msg, warn=True)
            if n != st.nbytes:
                change = True
                if st.nbytes is not None and not self.passe0:
                    st.changes += 1
                if final and st.nbytes is not None and k == "ins":
                    self.erreur(st.line, 3, "internal error: size changed in final pass (%d -> %d)" % (st.nbytes, n))
                st.nbytes = n
            pc += n
        self.sections[sect].fin = pc
        return change

    # --- passe rapide (dimensionnement) : les suites d'énoncés de taille fixe sont traitées en bloc -------------
    def plan(self):
        """[('org', st) | ('dyn', st) | ('run', Bloc)] ; bloc = énoncés de taille indépendante des symboles"""
        P = []
        cur = []

        def fin():
            if cur:
                P.append(("run", Bloc(list(cur))))
                del cur[:]
        for st in self.stmts:
            k = st.kind
            statique = (k in ("lab", "equ", "dc") or (k == "ins" and st.fixed is not None)
                        or (k == "dcb" and not st.args[0].syms and "*" not in repr(st.args[0].t)))
            if k == "org":
                fin()
                P.append(("org", st))
            elif statique:
                cur.append(st)
            else:
                fin()
                P.append(("dyn", st))
        fin()
        self._plan = P

    def passe_rapide(self):
        """même résultat qu'une passe de dimensionnement complète (passe()), sans parcourir les blocs fixes"""
        change = False
        sect = 0
        pc = self.sections[0].org
        syms = self.syms
        for kind, x in self._plan:
            if kind == "org":
                self.sections[sect].fin = pc
                sect = x.args
                pc = self.sections[sect].org
                continue
            if kind == "run":
                taille, labs, equs = x.agencement(pc & 1, self)
                for nom, off in labs:
                    sy = syms[nom]
                    v = pc + off
                    if sy.value != v:
                        change = True
                        sy.value = v
                    sy.sect = sect
                for sy, off in equs:
                    sy.pc = pc + off
                pc += taille
                continue
            st = x
            if st.kind == "ins" and pc & 1:
                pc += 1
            st.paddr = st.addr
            st.addr = pc
            for nom in st.labels:
                sy = syms[nom]
                if sy.value != pc:
                    change = True
                    sy.value = pc
                sy.sect = sect
            try:
                n = self.taille_memo(st, pc)
            except AsmError:
                n = st.nbytes or 0
            if n != st.nbytes:
                change = True
                st.changes += 1
                st.nbytes = n
            pc += n
        self.sections[sect].fin = pc
        return change

    def taille_memo(self, st, pc):
        """taille d'une instruction variable, mémorisée selon tout ce dont elle dépend"""
        if st.kind != "ins":
            return self.taille(st, pc, False)
        noms = st.texte
        if noms is None:
            noms = st.texte = [n for o in st.ops if o.expr is not None for n in o.expr.syms]
        try:
            vals = tuple([self.symval(n) for n in noms])
        except (Unknown, AsmError):
            return self.taille(st, pc, False)
        cle = (pc, st.paddr, st.nbytes, st.changes > MAX_CHANGES, self.passes > STICKY_APRES, vals)
        m = st.memo
        if m is None:
            m = st.memo = {}
        r = m.get(cle)
        if r is None:
            r = self.taille(st, pc, False)
            if len(m) > 16:
                m.clear()
            m[cle] = r
        return r

    def indexe(self):
        for i, st in enumerate(self.stmts):          # ordre du source (références en avant / en arrière)
            st.idx = i
            for nom in st.labels:
                self.syms[nom].idx = i
        self.indexe_fait = True

    def assemble(self):
        # passes de dimensionnement jusqu'à stabilité (références en avant inconnues à la 1re passe)
        for i in range(1000):
            self.passes = i + 1
            self.passe0 = i == 0
            if i >= 2 and RAPIDE:
                ch = self.passe_rapide()
            else:
                ch = self.passe(False)
                if i == 1 and RAPIDE:
                    self.plan()
            self.passe0 = False
            if not ch and i > 0:
                break
        else:
            self.erreur((0, 0), 3, "relâchement non résolu après 1000 passes (oscillation des tailles de "
                                   "branchements) : assembler avec vasm (HSFA_ASM=vasm) et signaler la source")
        self.passe(True)
        # contrôle : symboles non définis
        for s in self.syms.values():
            if s.kind is None and s.refd:
                self.erreur(s.line or (0, 0), 2, "undefined symbol <%s>" % self.affiche(s.nom))

    # --- sorties ----------------------------------------------------------------------------------------------
    def binaire(self):
        secs = [(i, s) for i, s in enumerate(self.sections) if s.fin > s.org]
        if not secs:
            return b""
        secs.sort(key=lambda x: x[1].org)
        base = secs[0][1].org
        fin = max(s.fin for i, s in secs)
        img = bytearray(fin - base)
        for st in self.stmts:
            if st.out:
                a = st.addr - base
                img[a:a + len(st.out)] = st.out
        prev = None
        for i, s in secs:
            if prev is not None and s.org < prev.fin:
                self.erreur((0, 0), 3006, "section <%s> overlaps with <%s>" % (s.nom, prev.nom))
            prev = s
        return bytes(img)

    def table_symboles(self):
        """[(nom, 'A'|'E', valeur)] : étiquettes globales et expressions référencées (comme la liste de vasm)"""
        out = []
        for s in self.syms.values():
            if s.kind is None or ">" in s.nom:
                continue
            if s.kind == "L":
                out.append((s.nom, "A", u32(s.value or 0)))
            elif s.refd:
                try:
                    v = self.symval(s.nom)
                except (AsmError, Unknown):
                    v = 0
                out.append((s.nom, "S" if s.redef else "E", u32(v)))
        return out

    def liste(self, nom_source):
        """liste au format de vasm (-L)"""
        L = ["Sections:"]
        for i, s in enumerate(self.sections):
            if s.nom is None:
                continue
            L.append('%02X: "%s" (%X-%X)' % (i, s.nom, s.org, s.fin))
        L += ["", "", 'Source: "%s"' % nom_source]
        lignes = self.fichiers[0][1]
        par_ligne = {}
        for st in self.stmts:
            if st.line[0] == 0:
                par_ligne.setdefault(st.line[1], []).append(st)
        out = [("\n".join(L) + "\n").encode("latin-1")]
        for n, brut in enumerate(lignes, 1):
            sts = par_ligne.get(n, ())
            premier = None
            suite = []
            for st in sts:
                for a, b in self.morceaux(st):
                    if premier is None:
                        premier = (st.sect, a, b)
                    else:
                        suite.append((st.sect, a, b))
            src = brut.rstrip(b"\r")[:119]
            if premier is None:
                out.append(b" " * 28 + b"\t" + (b"%6d: " % n) + src + b"\n")
            else:
                sect, a, b = premier
                tete = ("%02X:%08X %-16s" % (sect, a, b)).encode()
                out.append(tete + b"\t" + (b"%6d: " % n) + src + b"\n")
                for sect, a, b in suite:
                    out.append(("%02X:%08X %s\n" % (sect, a, b)).encode())
        out.append(b"\n\nSymbols by name:\n")
        tab = sorted(self.table_symboles())
        for nom, t, v in tab:
            out.append(("%-32s %s:%08X\n" % (nom, t, v)).encode("latin-1"))
        out.append(b"\nSymbols by value:\n")
        for nom, t, v in sorted(tab, key=lambda x: x[2]):
            out.append(("%08X %s\n" % (v, nom)).encode("latin-1"))
        return b"".join(out)

    def morceaux(self, st):
        """[(adresse, texte hexa)] pour la liste"""
        if not st.out:
            return []
        k = st.kind
        h = st.out.hex().upper()
        if k == "ins":            # 8 octets par ligne
            return [(st.addr + i, st.out[i:i + 8].hex().upper()) for i in range(0, len(st.out), 8)]
        if k == "dc":
            res = []
            a = st.addr
            i = 0
            for kk, v in st.args:
                n = len(v) if kk == "str" else WIDTH[st.size]
                if n:
                    res.append((a, st.out[i:i + n].hex().upper()))
                a += n
                i += n
            return res
        if k == "dcb":
            w = WIDTH[st.size]
            res = [(st.addr, st.out[:w].hex().upper())]
            if len(st.out) > w:
                res.append((st.addr + w, "*"))
            return res
        if k == "align":           # vasm : seul le décalage de cnop (après l'alignement) figure dans la liste
            off, al, nop = st.args
            if off > 0 and len(st.out) >= off:
                return [(st.addr + len(st.out) - off, st.out[len(st.out) - off:].hex().upper())]
            return []
        return []


# ----------------------------------------------------------------------------------------------------------------
# Interface
# ----------------------------------------------------------------------------------------------------------------


class Resultat:
    def __init__(self, asm, binaire, chemin):
        self.asm = asm
        self.binaire = binaire
        self.chemin = chemin
        self.erreurs = asm.erreurs
        self.avertissements = asm.avert

    def symboles(self):
        return dict((n, v) for n, t, v in self.asm.table_symboles())

    def liste(self):
        return self.asm.liste(self.chemin)

    def messages(self):
        """messages au format de vasm, triés par ligne"""
        tout = [(l, 0, num, msg) for l, num, msg in self.asm.erreurs] + [(l, 1, num, msg) for l, num, msg in self.asm.avert]
        tout.sort(key=lambda x: (x[0][0], x[0][1]))
        out = []
        for line, w, num, msg in tout:
            f, n = line
            chemin, lignes = self.asm.fichiers[f] if self.asm.fichiers else (self.chemin, [])
            src = lignes[n - 1].decode("latin-1").rstrip("\r") if 0 < n <= len(lignes) else ""
            out.append('\n%s %d in line %d of "%s": %s\n>%s\n' % ("warning" if w else "error", num, n, chemin, msg, src))
        return "".join(out)


# Amortissement des oscillations du relâchement (cas pathologiques : cascades de branchements vers l'instruction
# suivante). Modèle principal : une instruction qui a changé de taille plus de MAX_CHANGES fois garde sa
# suppression, et toutes les suppressions deviennent définitives après STICKY_APRES passes ; secours : la seconde
# règle seule. Le secours n'est employé que si le modèle principal aboutit à un état incohérent (contrôlé à la
# passe finale), jamais en silence ; s'il échoue aussi : erreur claire (employer alors HSFA_ASM=vasm).
MODELES = [None, {"MAX_CHANGES": 100000}]


def assemble_fichier(chemin, data=None):
    if data is None:
        with open(chemin, "rb") as f:
            data = f.read()
    g = globals()
    for i, m in enumerate(MODELES):
        sauve = {}
        if m:
            for k, v in m.items():
                sauve[k] = g[k]
                g[k] = v
        try:
            a = Assembleur()
            a.lit(chemin, data)
            if not a.erreurs:
                a.assemble()
        finally:
            g.update(sauve)
        a.modele = i
        if not any(num == 3 for l, num, msg in a.erreurs) or i == len(MODELES) - 1:
            break
    b = a.binaire() if not a.erreurs else b""
    return Resultat(a, b, chemin)


class Execution:
    """résultat compatible avec subprocess.CompletedProcess (returncode, stdout, stderr)"""

    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def lance(argv):
    """exécute l'assembleur dans le processus courant avec la ligne de commande de vasm (sans le nom du programme) ;
    -> Execution(returncode, stdout, stderr) ; les messages sont ceux de vasm (lignes source décodées en latin-1)"""
    import io
    out, err = io.StringIO(), io.BytesIO()

    class _E:
        buffer = err

        def write(self, x):
            err.write(x.encode("latin-1", "replace"))

        def flush(self):
            pass
    so, se = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, _E()
    try:
        code = main(list(argv))
    finally:
        sys.stdout, sys.stderr = so, se
    return Execution(code, out.getvalue(), err.getvalue().decode("utf-8", "replace"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    sortie = "a.out"
    liste = None
    source = None
    maxerr = 50
    quiet = False
    i = 0
    while i < len(argv):
        x = argv[i]
        if x == "-o":
            sortie = argv[i + 1]
            i += 2
            continue
        if x == "-L":
            liste = argv[i + 1]
            i += 2
            continue
        if x.startswith("-maxerrors="):
            maxerr = int(x.split("=", 1)[1])
        elif x == "-quiet":
            quiet = True
        elif x in ("-m68000", "-spaces", "-Fbin", "-mc68000"):
            pass
        elif x in ("-v", "--version"):
            print(VERSION)
            return 0
        elif x.startswith("-"):
            sys.stderr.write("hsfa_asm68k : option non prise en charge : %s\n" % x)
            return 2
        else:
            source = x
        i += 1
    if source is None:
        sys.stderr.write(__doc__)
        return 2
    if not quiet:
        sys.stdout.write(VERSION + " (assembleur 68000 du projet HSFA, MIT)\n")
    r = assemble_fichier(source)
    sys.stderr.flush()
    sys.stderr.buffer.write(r.messages().encode("latin-1"))      # lignes source telles quelles (octets)
    sys.stderr.flush()
    if r.erreurs:
        return 1
    with open(sortie, "wb") as f:
        f.write(r.binaire)
    if liste:
        with open(liste, "wb") as f:
            f.write(r.liste())
    return 0


if __name__ == "__main__":
    sys.exit(main())
