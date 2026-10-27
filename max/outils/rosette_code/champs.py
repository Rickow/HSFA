"""Correspondance des CHAMPS de la structure objet/joueur : décalage PSP (C) <-> décalage 68K arcade ($xx(A6)).
Pour chaque paire de routines (API moteur appariée + gestionnaires de persos appariés), on relève dans l'ordre les
accès mémoire relatifs à l'objet (68K : d(A6) ; PSP : d(rX) avec rX = a0 à l'entrée ou ses copies), puis on les
aligne (LCS sur taille + lecture/écriture) et on vote les couples de décalages sur toutes les paires."""
import sys, re, collections, json
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
from arc68k import explore
from relocs import img
from mips import decode
from charcode2 import fend
WR = ("move", "clr", "st", "sf", "add", "sub", "addq", "subq", "or", "and", "eor", "neg", "not", "bset", "bclr", "bchg",
      "lsl", "lsr", "asl", "asr", "addi", "subi", "ori", "andi", "eori", "seq", "sne", "scs", "scc")
def acc68(start, hi):
    seen, _, _ = explore([start], start, hi)
    out = []
    for a in sorted(seen):
        i = seen[a]; m = i.mnemonic; base, _, sz = m.partition(".")
        sz = {"b": 1, "w": 2, "l": 4}.get(sz, 2 if base in ("lea",) else 0)
        ops = [o.strip() for o in re.split(r",\s*(?![^()]*\))", i.op_str)]
        for k, o in enumerate(ops):
            mm = re.fullmatch(r"(?:\$([0-9a-f]+)|(-?\d+))?\(a6\)", o)
            if not mm or base in ("lea", "pea"): continue
            off = int(mm.group(1), 16) if mm.group(1) else int(mm.group(2) or 0)
            w = (k == len(ops) - 1 and base in WR) or (base in ("clr", "st", "sf", "neg", "not") )
            if base in ("tst", "cmp", "cmpi", "btst"): w = False
            out.append((off, sz, "W" if w else "R"))
    return out
LD = {"lb": 1, "lbu": 1, "lh": 2, "lhu": 2, "lw": 4, "sb": 1, "sh": 2, "sw": 4}
def accpsp(start, end=None):
    end = end or fend(start)
    obj = {4}; out = []
    for i in decode(img, start, end):
        if i.m in LD and i.rs in obj:
            out.append((i.simm, LD[i.m], "W" if i.m[0] == "s" else "R"))
        if i.m == "or" and i.fn == 0x25 and i.rt == 0 and i.rs in obj: obj.add(i.rd); continue
        if i.m == "or" and i.fn == 0x25 and i.rs == 0 and i.rt in obj: obj.add(i.rd); continue
        # registre écrasé
        dst = i.rd if i.op == 0 else (i.rt if i.m in ("addiu", "ori", "andi", "lui", "slti", "sltiu", "xori") or i.m in LD and i.m[0] == "l" else None)
        if dst in obj and dst is not None: obj.discard(dst)
        if i.m in ("jal", "jalr"): obj -= {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25}
    return out
def lcs(x, y):
    n, m = len(x), len(y); D = [[0]*(m+1) for _ in range(n+1)]
    eq = lambda a, b: a[2] == b[2] and (a[1] == b[1] or 0 in (a[1], b[1]))
    for i in range(n):
        for j in range(m):
            D[i+1][j+1] = D[i][j] + 1 if eq(x[i], y[j]) else max(D[i][j+1], D[i+1][j])
    out, i, j = [], n, m
    while i and j:
        if eq(x[i-1], y[j-1]) and D[i][j] == D[i-1][j-1] + 1: out.append((x[i-1], y[j-1])); i -= 1; j -= 1
        elif D[i-1][j] >= D[i][j-1]: i -= 1
        else: j -= 1
    return out

def collect():
    import rosette
    C = {int(a, 16): int(p, 16) for a, p in json.load(open("api_arcade_psp.json")).items()}
    pairs = list(C.items())
    for c in sorted(rosette.ARC_ENTRIES):
        if c in (0x11, 0x13, 0x1f): continue
        M, RP, *_ = rosette.run(c, C)
        pairs += list(RP.items())
    votes = collections.defaultdict(collections.Counter)
    for a, p in pairs:
        for u, v in lcs(acc68(a, a + 0x400), accpsp(p)):
            votes[u[0]][v[0]] += 1
    return votes, len(pairs)

def chain(votes, minv=2):
    """chaîne croissante de poids maximal : décalage 68K croissant -> décalage PSP croissant"""
    cand = sorted((o, p, n) for o, v in votes.items() for p, n in v.items() if n >= minv and o >= 0 and p >= 0)
    best = []                                   # (score, prev index)
    for k, (o, p, n) in enumerate(cand):
        s, pr = n, -1
        for j in range(k):
            oj, pj, _ = cand[j]
            if oj < o and pj < p and best[j][0] + n > s: s, pr = best[j][0] + n, j
        best.append((s, pr))
    k = max(range(len(best)), key=lambda i: best[i][0]); out = []
    while k >= 0: out.append(cand[k]); k = best[k][1]
    return out[::-1]

def modele(ch):
    """segments [(o68_debut, o68_fin, psp_debut, ecart)] : points consécutifs de même écart = segment sûr"""
    segs = []
    for o, p, k in ch:
        d = p - o
        if segs and segs[-1][3] == d: segs[-1][1] = o
        else: segs.append([o, o, p, d])
    return segs
def psp_vers_68k(segs, off):
    """-> (décalage 68K, 'sûr' | 'zone' | None) ; 'sûr' = dans un segment, 'zone' = au bord (même écart que le segment voisin)"""
    for o0, o1, p0, d in segs:
        if o0 + d <= off <= o1 + d: return off - d, "sûr"
    return None, None
