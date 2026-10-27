"""Rosette du code : API moteur PSP (C) <-> arcade 68K, apprise sur un perso présent des deux côtés.
Phase 1 : appariement des cibles par les arguments constants (Jaccard pondéré par la rareté des valeurs).
Phase 2 : routines appariées via les sites d'appel ancrés (même cible appariée + même argument),
          puis alignement des suites d'appels moteur dans chaque paire de routines -> nouvelles paires de cibles.
Itéré jusqu'à stabilité."""
import sys, math, collections, bisect, re
from appels import arcade_calls, psp_calls
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import modules
from charcode2 import fstart as psp_fstart
from arc68k import L as _L
# tables arcade de 32 longs indexées par l'ID ($102(A6)) ; régions de code par perso = rangées dans l'ordre des ID
ARC_TABLES = [0xdcb12,0xdcb92,0xdcc12,0xdcc92,0xdcd12,0xdcd92,0xdce12,0xdce92,0xdcf12,0xdcf92,0xdd092,0xdd112,0xdd192,
              0xdd212,0xdd292,0xdd312,0xdd412,0xdf412,0xdf812,0xdf892]
def _regions():
    cnt = collections.Counter(_L(t + 4*c) for t in ARC_TABLES for c in range(32))
    E = {c: sorted({_L(t + 4*c) for t in ARC_TABLES}) for c in range(32)}
    low = {c: [x for x in E[c] if x < 0xe0000 and cnt[x] < 3] for c in range(32)}
    low[0] = [x for x in E[0] if 0x33f00 <= x < 0x35a74]          # Ryu : entrées partagées avec Evil Ryu ($17)
    st = sorted({min(v) for v in low.values() if v})
    out = {}
    for c, v in low.items():
        if not v: continue
        lo = min(v); nx = [x for x in st if x > lo]
        hi = nx[0] if nx else max(v) + 0x200
        out[c] = ([x for x in E[c] if lo <= x < hi], lo, hi)
    return out
ARC_ENTRIES = _regions()

def arcade_routines(seen, tables, entries, A):
    starts = set(entries) | {t for v in tables.values() for t in v}
    for i in seen.values():
        if i.mnemonic.startswith("bsr"):
            m = re.search(r"\$([0-9a-f]+)$", i.op_str)
            if m: starts.add(int(m.group(1), 16))
    S = sorted(starts)
    return lambda a: S[max(0, bisect.bisect_right(S, a) - 1)]

def sequences(calls, fstart):
    seq = collections.defaultdict(list)
    for t, L in calls.items():
        for site, args in L: seq[fstart(site)].append((site, t, tuple(sorted(args.values()))))
    return {f: sorted(v) for f, v in seq.items()}

def phase1(A, P):
    df = collections.Counter(v for L in list(A.values()) + list(P.values()) for v in {x for _, a in L for x in a.values()})
    w = lambda v: 1.0 / math.log(2 + df[v]) if v not in (0, 1) else 0.05
    va = {t: collections.Counter(x for _, a in L for x in a.values()) for t, L in A.items()}
    vp = {t: collections.Counter(x for _, a in L for x in a.values()) for t, L in P.items()}
    sc = []
    for ta, ca in va.items():
        for tp, cp in vp.items():
            inter = sum(w(v) * min(ca[v], cp[v]) for v in ca if v in cp)
            uni = sum(w(v) * max(ca[v], cp.get(v, 0)) for v in set(ca) | set(cp))
            if inter > 0.3: sc.append((inter / uni * min(1, inter), ta, tp))
    pairs, ua, up = {}, set(), set()
    for s, ta, tp in sorted(sc, reverse=True):
        if ta in ua or tp in up or s < 0.25: continue
        pairs[ta] = (tp, round(s, 2), "args"); ua.add(ta); up.add(tp)
    return pairs

def align(sa, sp, M):
    """LCS des suites de cibles (arcade traduites par M quand connues ; inconnues = joker de même rang)"""
    n, m = len(sa), len(sp)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    eq = lambda x, y: M.get(x[1], (None,))[0] == y[1] or (x[1] not in M and y[1] not in Minv(M))
    for i in range(n):
        for j in range(m):
            D[i+1][j+1] = D[i][j] + 1 if eq(sa[i], sp[j]) else max(D[i][j+1], D[i+1][j])
    out, i, j = [], n, m
    while i and j:
        if eq(sa[i-1], sp[j-1]) and D[i][j] == D[i-1][j-1] + 1: out.append((sa[i-1], sp[j-1])); i -= 1; j -= 1
        elif D[i-1][j] >= D[i][j-1]: i -= 1
        else: j -= 1
    return out[::-1]
def Minv(M): return {v[0] for v in M.values()}

def run(cid=0x00, seed=None, imposees=None):
    """imposees (2026-10-11) : {routine arcade: routine PSP} établies par les IMAGES (rosette_construction/chaine_code.py)
    et arbitrées (conflits.py) ; elles remplacent les paires votées en conflit avec elles. None = comportement d'origine."""
    ent, lo, hi = ARC_ENTRIES[cid]
    A, seen, tables = arcade_calls(ent, lo, hi)
    a0, e0 = modules.module_bounds()[cid]
    P, ins = psp_calls(a0, e0)
    afs = arcade_routines(seen, tables, ent, A)
    SA, SP = sequences(A, afs), sequences(P, psp_fstart)
    M = phase1(A, P)
    if seed:
        M = {ta: v for ta, v in M.items() if ta not in seed and v[0] not in set(seed.values())}
        M.update({ta: (tp, 0, 'graine') for ta, tp in seed.items()})
    for it in range(6):
        # routines appariées : sites ancrés (cible appariée + mêmes arguments non triviaux)
        votes = collections.Counter()
        for fa, sa in SA.items():
            for _, ta, va in sa:
                if ta not in M or not [v for v in va if v not in (0, 1)]: continue
                for fp, sp in SP.items():
                    if any(tp == M[ta][0] and vp == va for _, tp, vp in sp): votes[(fa, fp)] += 1
        RP, ua, up = {}, set(), set()
        if imposees:
            for fa, fp in imposees.items(): RP[fa] = fp; ua.add(fa); up.add(fp)
        for (fa, fp), n in votes.most_common():
            if fa in ua or fp in up: continue
            RP[fa] = fp; ua.add(fa); up.add(fp)
        # alignement des suites d'appels dans les routines appariées
        cand = collections.Counter()
        for fa, fp in RP.items():
            for (x, y) in align(SA[fa], SP[fp], M):
                if x[1] not in M and y[1] not in Minv(M): cand[(x[1], y[1])] += 1
        new = 0
        for (ta, tp), n in cand.most_common():
            if ta in M or tp in Minv(M): continue
            M[ta] = (tp, n, "alignement"); new += 1
        if not new: break
    return M, RP, A, P, SA, SP

if __name__ == "__main__":
    M, RP, A, P, SA, SP = run()
    print("cibles appariées : %d / %d arcade, %d PSP ; routines appariées : %d / %d arcade, %d PSP"
          % (len(M), len(A), len(P), len(RP), len(SA), len(SP)))
    for ta, (tp, s, how) in sorted(M.items(), key=lambda x: -len(A[x[0]])):
        print("  arcade %06x (%2d appels)  <->  PSP %06x (%2d appels)   %s %s" % (ta, len(A[ta]), tp, len(P[tp]), how, s))

def consensus(res, min_votes=2, share=0.66):
    votes = collections.defaultdict(collections.Counter)
    for m in res.values():
        for ta, tp in m.items(): votes[ta][tp] += 1
    cand = sorted(((v.most_common(1)[0][1], v.most_common(1)[0][1] / sum(v.values()), ta, v.most_common(1)[0][0])
                   for ta, v in votes.items()), reverse=True)
    out, used = {}, set()
    for n, sh, ta, tp in cand:
        if n >= min_votes and sh >= share and tp not in used: out[ta] = tp; used.add(tp)
    return out, votes

def all_chars(seed=None, imposees=None):
    res = {}
    for c in sorted(ARC_ENTRIES):
        if c in (0x11, 0x13, 0x1f): continue            # Gen (double entrée), Juni : à part
        M = run(c, seed, (imposees or {}).get(c))[0]
        res[c] = {ta: tp for ta, (tp, s, how) in M.items()}
    return res
