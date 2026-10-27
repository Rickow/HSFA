"""Apprend les champs et fonctions PSP encore inconnus (« ??psp_0xN ») : alignement LCS entre la traduction et la
routine arcade, avec joker ; un « ?? » aligné sur une ligne arcade identique hormis l'opérande vote pour la paire."""
import json, re, collections
from evaluer import norm_arc, norm_tr
from traduire import traduire
J = re.compile(r"\?\?(?:psp|glob)_(0x[0-9a-f]+)(\(a6\))?")
def _n(x): return re.sub(r"\bd\d\b", "dX", x)
def egal(t, a):
    t, a = _n(t), _n(a)
    if t == a: return True, None
    m = J.search(t)
    if not m: return False, None
    glob = t[m.start():].startswith("??glob")
    cible = r"\$([0-9a-f]+)\(a5\)" if glob else (r"\$([0-9a-f]+)\(a6\)" if m.group(2) else r"\$([0-9a-f]+)\.l")
    pat = re.escape(t[:m.start()]) + cible + re.escape(t[m.end():])
    mm = re.fullmatch(pat, a)
    kind = "globale" if glob else ("champ" if m.group(2) else "fonction")
    return (True, (m.group(1), kind, mm.group(1))) if mm else (False, None)
def aligner(A, T):
    n, m = len(A), len(T); D = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n):
        for j in range(m):
            D[i+1][j+1] = D[i][j] + 1 if egal(T[j], A[i])[0] else max(D[i][j+1], D[i+1][j])
    out, i, j = [], n, m
    while i and j:
        ok, b = egal(T[j-1], A[i-1])
        if ok and D[i][j] == D[i-1][j-1] + 1:
            if b: out.append(b)
            i -= 1; j -= 1
        elif D[i-1][j] >= D[i][j-1]: i -= 1
        else: j -= 1
    return out
if __name__ == "__main__":
    E = json.load(open("evaluation.json"))
    votes = collections.defaultdict(collections.Counter)
    for sc, c, a, p in E:
        for psp, kind, arc in aligner(norm_arc(a), norm_tr(traduire(p))): votes[(kind, psp)][arc] += 1
    try: res = json.load(open("appris.json"))          # on FUSIONNE avec l'acquis (les champs connus ne votent plus)
    except FileNotFoundError: res = {}
    for (kind, psp), v in sorted(votes.items(), key=lambda x: -sum(x[1].values())):
        (arc, n), tot = v.most_common(1)[0], sum(v.values())
        ok = n >= 2 and n / tot >= 0.6
        print("%-8s PSP %-8s -> %s%s  %d/%d %s" % (kind, psp, "$" if kind == "champ" else "$", arc, n, tot, "" if ok else "(rejeté)"))
        if ok: res.setdefault(kind, {})[psp] = arc
    json.dump(res, open("appris.json", "w"), indent=1)
