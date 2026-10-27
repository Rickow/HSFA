"""Champs PSP inconnus : vote différentiel. Pour chaque paire (gestionnaire arcade, gestionnaire PSP) où la traduction
contient ??psp_X(aN), les champs $Y(aN) touchés par la routine arcade et ABSENTS de la traduction votent pour X -> $Y
(normalisé par la fréquence de $Y)."""
import json, re, collections
from evaluer import norm_arc
from traduire import traduire
E = json.load(open("evaluation.json"))
votes = collections.defaultdict(collections.Counter); freq = collections.Counter(); n_x = collections.Counter()
for sc, c, a, p in E:
    T = traduire(p); A = norm_arc(a)
    inc = set(re.findall(r"\?\?psp_(0x[0-9a-f]+)\((a\d)\)", " ".join(T)))
    fa = set(re.findall(r"\$([0-9a-f]+)\((a\d)\)", " ".join(A)))
    ft = set(re.findall(r"\$([0-9a-f]+)\((a\d)\)", " ".join(T)))
    for f in fa: freq[f] += 1
    if not inc: continue
    rest = fa - ft
    for x in inc:
        n_x[x] += 1
        for y in rest:
            if y[1] == x[1] or {y[1], x[1]} <= {"a6"}: votes[x][y] += 1
res = {}
for x, v in sorted(votes.items(), key=lambda kv: -n_x[kv[0]]):
    sc = sorted(((n / (1 + 0.02 * freq[y]), n, y) for y, n in v.items()), reverse=True)[:3]
    print("%-12s (%3d paires) -> %s" % ("%s(%s)" % x, n_x[x], ["$%s(%s) %d" % (y[0], y[1], n) for s_, n, y in sc]))
