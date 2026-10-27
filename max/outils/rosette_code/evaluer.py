"""Évaluation du traducteur : gestionnaires PSP des persos arcade traduits vs routines 68K réelles (vérité de terrain).
Score = 2 x LCS / (n68K + ntraduit) sur les instructions normalisées (mnémonique + opérandes, étiquettes ignorées)."""
import json, re, collections, sys
import rosette
from arc68k import explore
import traduire as _T
_T.MODE_MAX = False                    # vérité arcade : pas d'allocation propre aux persos MAX
from traduire import traduire
C = {int(a, 16): int(p, 16) for a, p in json.load(open("api_arcade_psp.json")).items()}
def norm68(l):
    l = l.strip()
    if not l or l.endswith(":") or l.startswith(";"): return None
    m, _, op = l.partition(" "); op = op.replace(" ", "")
    op = re.sub(r"(\$[0-9a-f]+|J_[0-9a-f]+)\(pc,(d\d\.w)\)", r"T(pc,\2)", op)
    if m == "dc.w": return None
    m = m.replace(".s", ".b") if m.startswith("b") else m
    if m[:1] == "b" and m not in ("btst", "bset", "bclr", "bchg") or m.startswith("db"): return m[:3]   # sauts : sans cible
    def imm(x):
        v = int(x.group(1), 16) if x.group(0).startswith("#$") else int(x.group(1))
        return "#%d" % (v & 0xFFFFFFFF)
    op = re.sub(r"#\$([0-9a-f]+)|#(-?\d+)", lambda x: "#%d" % ((int(x.group(1), 16) if x.group(1) else int(x.group(2))) & (0xFF if m.startswith("moveq") else 0xFFFFFFFF)), op)
    return m + " " + op
def norm_arc(a):
    seen, _, _ = explore([a], a, a + 0x300)
    out = []
    for k in sorted(seen):
        i = seen[k]; x = norm68("%s %s" % (i.mnemonic, i.op_str))
        if x: out.append(x)
    return out
def norm_tr(lines):
    out = []
    for l in lines:
        x = l.strip()
        y = norm68(x)
        if y: out.append(y)
    return out
def lcs(a, b):
    D = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a)):
        for j in range(len(b)):
            D[i+1][j+1] = D[i][j] + 1 if a[i] == b[j] else max(D[i][j+1], D[i+1][j])
    return D[-1][-1]
if __name__ == "__main__":
    scores, inc, tot_lines = [], 0, 0
    exemples = []
    for c in sorted(rosette.ARC_ENTRIES):
        if c in (0x11, 0x13, 0x1f): continue
        M, RP, *_ = rosette.run(c, C)
        for a, p in RP.items():
            try: tr = traduire(p)
            except Exception as ex: continue
            A, T = norm_arc(a), norm_tr(tr)
            if not A or not T: continue
            sc = 2 * lcs(A, T) / (len(A) + len(T)); scores.append(sc)
            q = sum(1 for l in tr if "??" in l); inc += q; tot_lines += len(tr)
            exemples.append((sc, c, a, p))
    scores.sort()
    n = len(scores)
    print("paires évaluées :", n)
    print("score médian %.2f ; >= 0.9 : %d ; = 1.0 : %d ; < 0.5 : %d" % (scores[n // 2], sum(s >= 0.9 for s in scores), sum(s == 1.0 for s in scores), sum(s < 0.5 for s in scores)))
    print("lignes non traduites (??) : %d / %d (%.0f %%)" % (inc, tot_lines, 100 * inc / tot_lines))
    json.dump(sorted(exemples), open("evaluation.json", "w"))
