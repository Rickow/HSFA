"""Outils communs d'analyse du code (fonctions, débuts, relocations, tables de 42 entrées).
NB : reach() suit les appels ET les données et finit par tout atteindre (moteur commun) :
NE PAS l'utiliser pour mesurer le code d'un perso — voir modules.py (méthode finale)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

import struct, bisect, collections, json
from relocs import pointer_words, TEXT_END, img
P = pointer_words(); PA = sorted(P)
NW = TEXT_END // 4
W = struct.unpack_from(f"<{NW}I", img, 0)
def s16(x): return x - 0x10000 if x & 0x8000 else x
jal = lambda w: (w & 0x03FFFFFF) << 2          # PRX : cibles 0-based, relogées au chargement
def _saut(w):                                  # j/jal, jr/jalr, branches, bc1x : le mot suivant est un créneau de délai
    op = w >> 26
    return op in (1, 2, 3, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) or (op == 0 and w & 0x3F in (8, 9)) \
        or (op == 0x11 and (w >> 21) & 31 == 8)
_jals = {jal(w) for w in W if w >> 26 == 3}
_prologues = {i*4 for i in range(NW) if W[i] >> 16 == 0x27BD and W[i] & 0x8000}
# (2026-10-11, rapport agent_integration_max) une cible de données qui tombe dans le CRÉNEAU DE DÉLAI d'un saut n'est
# pas un début de fonction (0x1B3450, pointé par le mot 0x2C8ED0, coupait psp_1b33c8 ; aussi 0x150450)
_creneaux = {t for t in P.values() if 4 <= t < TEXT_END and t not in _jals and t not in _prologues and _saut(W[t//4 - 1])}
starts = _jals | ({t for t in P.values() if t < TEXT_END} - _creneaux) | _prologues
S = sorted(s for s in starts if 0 <= s < TEXT_END)
fstart = lambda a: S[bisect.bisect_right(S, a) - 1]
fend = lambda f: S[bisect.bisect_right(S, f)] if bisect.bisect_right(S, f) < len(S) else TEXT_END
targets_in_data = sorted({t for t in P.values() if t >= TEXT_END})
def data_span(a):
    k = bisect.bisect_right(targets_in_data, a)
    nxt = targets_in_data[k] if k < len(targets_in_data) else a + 0x800
    return min(nxt, a + 0x800)
def reach(roots):
    seen_f, seen_d, todo = set(), set(), list(roots)
    while todo:
        a = todo.pop()
        if a < TEXT_END:
            f = fstart(a)
            if f in seen_f: continue
            seen_f.add(f)
            e = fend(f)
            for k in range(f//4, e//4):
                w = W[k]
                if w >> 26 == 3: todo.append(jal(w))
                elif w >> 26 == 0x0F:
                    rt, hi = (w >> 16) & 31, w & 0xFFFF
                    for m in range(k+1, min(k+8, e//4)):
                        x = W[m]
                        if (x >> 21) & 31 == rt and x >> 26 in (0x09, 0x23, 0x21, 0x25, 0x20, 0x24):
                            va = ((hi << 16) + s16(x & 0xFFFF)) & 0xFFFFFFFF
                            if TEXT_END <= va < len(img): todo.append(va)
                            break
        else:
            if a in seen_d: continue
            seen_d.add(a)
            lo = bisect.bisect_left(PA, a); hi_ = data_span(a)
            while lo < len(PA) and PA[lo] < hi_:
                todo.append(P[PA[lo]]); lo += 1
    return seen_f
# tables par perso : suites contiguës de 42/43 mots-pointeurs
runs, cur = [], [PA[0]]
for x in PA[1:]:
    if x == cur[-1] + 4: cur.append(x)
    else: runs.append(cur); cur = [x]
runs.append(cur)
tables = [r for r in runs if len(r) in (42, 43)]
if __name__ == "__main__":
    names = json.load(open(paths.MAPPING))
    R = {c: reach([P[t[c]] for t in tables]) for c in range(42)}
    size = lambda fs: sum(fend(f) - f for f in fs)
    union_all = set().union(*R.values())
    print(f"tables par perso: {len(tables)} ; code atteignable depuis les persos : {len(union_all)} fonctions, {size(union_all)/1024:.0f} Ko")
    for c in range(42):
        others = set().union(*(R[d] for d in R if d != c))
        ex = R[c] - others
        tag = " <== MAX" if c >= 0x26 else (" <== Upper" if 0x20 <= c <= 0x24 else "")
        print(f"  {c:#04x} {names[f'{c:02x}']:<13} exclusif : {len(ex):4} fonctions ~{size(ex)/1024:6.1f} Ko{tag}")
