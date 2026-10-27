"""Champs PSP inconnus : essai de chaque écart de zone connu, sur les paires (vérité arcade) qui les contiennent ;
retenu si au moins une paire s'améliore et aucune ne se dégrade."""
import json, re, collections
import traduire as T
T.MODE_MAX = False
from evaluer import norm_arc, norm_tr, lcs
E = json.load(open("evaluation.json"))
ECARTS = sorted({d for o0, o1, p0, d in T.SEGS} | {0x49, 0x3C, 0x38, -0x20, -0x10})
def score(p, a):
    A, Tr = norm_arc(a), norm_tr(T.traduire(p)); return 2 * lcs(A, Tr) / (len(A) + len(Tr))
par_champ = collections.defaultdict(list)
for sc, c, a, p in E:
    for m in re.finditer(r"\?\?psp_0x([0-9a-f]+)\(a\d\)", " ".join(T.traduire(p))): par_champ[int(m.group(1), 16)].append((a, p))
res = {}
for x, paires in sorted(par_champ.items(), key=lambda kv: -len(kv[1])):
    paires = list(dict.fromkeys(paires))[:30]
    base = [score(p, a) for a, p in paires]
    meilleur = None
    for d in ECARTS:
        o = x - d
        if o < 0 or o >= 0x400: continue
        T.HORS[x] = o
        sc = [score(p, a) for a, p in paires]
        del T.HORS[x]
        up = sum(1 for u, v in zip(sc, base) if u > v + 1e-9); down = sum(1 for u, v in zip(sc, base) if u < v - 1e-9)
        if up and not down and (meilleur is None or up > meilleur[1]): meilleur = (o, up, d)
    print("0x%x (%d paires) -> %s" % (x, len(paires), ("$%x (écart %+#x, %d améliorées)" % meilleur) if meilleur else "rien"))
    if meilleur: res["%x" % x] = "%x" % meilleur[0]
json.dump(res, open("ecarts_retenus.json", "w"), indent=0)
