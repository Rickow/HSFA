#!/usr/bin/env python3
"""Alignement instruction par instruction de l'image 68K TRADUITE (roms_tr) sur la ROM ARCADE
(sfa3ud_prog.bin, déchiffrée).

1. jetons normalisés (desasm.norm) ; octets de l'image ramenés en numérotation 68K (XOR 1) ;
2. ancres = 4-grammes de jetons UNIQUES des deux côtés ;
3. on ne garde que les ancres confirmées par une voisine de même décalage (colinéarité locale) ;
4. entre deux ancres consécutives compatibles, alignement LCS des jetons (trous <= 600 x 600).
Sortie : _cache/alignement.pkl = {adresse traduite: (adresse arcade, 'ancre'|'lcs')}"""
import sys, os, collections, pickle, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desasm as D, fonctions as F
ICI = os.path.dirname(os.path.abspath(__file__))
ARC = '<workspace>/work/cps2/sfa3ud_prog.bin'
TRAD = os.path.join(ICI, '..', '_trad.bin')
K = 4

R_A5 = re.compile(r'\((-?)\$([0-9a-f]+),A5\)')

def a5_vals(ops):
    return [((-1 if s else 1) * int(h, 16)) & 0xffff for s, h in R_A5.findall(ops)]

def remap_ops(ops, table):
    """applique la table de relocalisation des variables A5 (traduit -> arcade)"""
    if not table: return ops
    def f(m):
        v = ((-1 if m.group(1) else 1) * int(m.group(2), 16)) & 0xffff
        for lo, hi, d in table:
            if lo <= v <= hi:
                v = (v + d) & 0xffff; break
        s = v - 0x10000 if v >= 0x8000 else v
        return '(%s$%x,A5)' % ('-' if s < 0 else '', abs(s))
    return R_A5.sub(f, ops)

def charge(table=None):
    T = D.desasm(TRAD, 0, 0x1000, F.bornes_trad()[0], "trad")
    A = D.desasm(ARC, 0, 0, 0x100000, 'arc')
    tt = [D.norm(x[2], remap_ops(D.xor_octets(x[2], x[3]), table)) for x in T]
    replie_tables(T, tt)
    ta = [D.norm(x[2], x[3]) for x in A]
    return T, A, tt, ta

R_PUSH = re.compile(r'^(A[0-7]), -\(A7\)$')
def replie_tables(T, tt):
    """idiome du portage pour un octet de table indexée (HANDOFF §65-§66) :
    MOVE.L An,-(A7) ; LEA T,An ; LEA (An,Dk.w),An ; MOVE.L An,-(A7) ; EORI.B #1,3(A7) ;
    MOVEA.L (A7)+,An ; OP (An),x ; MOVEA.L (A7)+,An   ==  OP T(PC,Dk.w),x  de la ROM"""
    n = len(T)
    for i in range(n - 8):
        if T[i][2] != 'move.l' or not R_PUSH.match(T[i][3]): continue
        an = T[i][3][:2]
        if T[i+1][2] != 'lea' or T[i+2][2] != 'lea' or T[i+4][2] != 'eori.b' or T[i+5][2] != 'movea.l': continue
        m = re.match(r'\(%s,(D[0-7]\.w)\), %s' % (an, an), T[i+2][3])
        if not m or T[i+4][3] != '#$1, ($3,A7)' or T[i+7][2] != 'movea.l': continue
        op = T[i+6]
        if '(%s)' % an not in op[3]: continue
        tok = D.norm(op[2], op[3].replace('(%s)' % an, '(TBL,%s)' % m.group(1)))
        tt[i] = tok
        for k in range(i+1, i+8): tt[k] = None

def lcs(a, b):
    n, m = len(a), len(b)
    if n == 0 or m == 0: return []
    prev = [0] * (m + 1); tab = [prev]
    for i in range(n):
        cur = [0] * (m + 1); ai = a[i]
        for j in range(m):
            cur[j+1] = prev[j] + 1 if (ai is not None and ai == b[j]) else (prev[j+1] if prev[j+1] >= cur[j] else cur[j])
        tab.append(cur); prev = cur
    i, j, out = n, m, []
    while i and j:
        if a[i-1] is not None and a[i-1] == b[j-1] and tab[i][j] == tab[i-1][j-1] + 1: out.append((i-1, j-1)); i -= 1; j -= 1
        elif tab[i-1][j] >= tab[i][j-1]: i -= 1
        else: j -= 1
    return out[::-1]

def aligne(T, A, tt, ta):
    ia = collections.defaultdict(list)
    for j in range(len(ta) - K + 1):
        g = tuple(ta[j:j+K])
        if None not in g: ia[g].append(j)
    it = collections.Counter(tuple(tt[i:i+K]) for i in range(len(tt) - K + 1))
    anc = []
    for i in range(len(tt) - K + 1):
        g = tuple(tt[i:i+K])
        if None in g or it[g] != 1: continue
        l = ia.get(g)
        if l and len(l) == 1: anc.append((i, l[0]))
    # confirmation par une voisine
    ok = []
    for k, (i, j) in enumerate(anc):
        d = j - i; good = False
        for q in range(max(0, k-4), min(len(anc), k+5)):
            if q == k: continue
            i2, j2 = anc[q]
            if abs(i2 - i) <= 200 and abs((j2 - i2) - d) <= max(12, abs(i2 - i) // 3) and i2 != i: good = True; break
        if good: ok.append((i, j))
    # garde une suite strictement croissante localement : retire les ancres qui croisent leurs voisines
    m = {}
    for i, j in ok:
        for t in range(K): m.setdefault(i + t, (j + t, 'ancre'))
    keys = sorted(m)
    # remplissage des trous
    nlcs = 0
    for a, b in zip(keys, keys[1:]):
        if b - a <= 1: continue
        ja, jb = m[a][0], m[b][0]
        di, dj = b - a, jb - ja
        if dj <= 1 or di > 600 or dj > 600 or abs(di - dj) > max(40, di // 2): continue
        for x, y in lcs(tt[a+1:b], ta[ja+1:jb]):
            m[a+1+x] = (ja+1+y, 'lcs'); nlcs += 1
    print("  ancres %d, confirmées %d, instructions alignées %d (dont lcs %d) sur %d"
          % (len(anc), len(ok), len(m), nlcs, len(T)))
    return m

def apprend(T, A, m, table):
    """paires de déplacements A5 (traduit, arcade) dans les trous de même longueur entre
    instructions alignées, même mnémonique -> intervalles de décalage constant"""
    pairs = collections.Counter()
    ks = sorted(m)
    for a, b in zip(ks, ks[1:]):
        di = b - a; dj = m[b][0] - m[a][0]
        if di != dj or not (2 <= di <= 12): continue
        for t in range(1, di):
            x = T[a+t]; y = A[m[a][0]+t]
            if x[2] != y[2]: continue
            va = a5_vals(D.xor_octets(x[2], x[3])); vb = a5_vals(y[3])
            if len(va) != len(vb): continue
            for p, q in zip(va, vb):
                if p != q: pairs[(p, q)] += 1
    # aussi les paires déjà égales confirment l'identité : non utile ici
    best = {}
    for (p, q), c in pairs.items():
        if p not in best or c > best[p][1]: best[p] = (q, c)
    pts = sorted((p, (q - p) & 0xffff, c) for p, (q, c) in best.items())
    # intervalles : suites de points de même décalage, >= 2 votes au total
    iv = []
    for p, d, c in pts:
        if iv and iv[-1][2] == d and p - iv[-1][1] <= 0x400: iv[-1][1] = p; iv[-1][3] += c
        else: iv.append([p, p, d, c])
    iv = [(lo, hi, d) for lo, hi, d, c in iv if c >= 3 and 0x10 <= d <= 0xfff0]
    return iv

def main():
    table = []
    for tour in range(4):
        T, A, tt, ta = charge(table)
        m = aligne(T, A, tt, ta)
        nt = apprend(T, A, m, table)
        # fusion : les nouveaux intervalles s'ajoutent à ceux qui ne se chevauchent pas
        for lo, hi, d in nt:
            if not any(not (hi < a or lo > b) for a, b, _ in table): table.append((lo, hi, d))
        table.sort()
        print("tour %d : %d intervalles de relocalisation A5" % (tour, len(table)))
    res = {T[i][0]: (A[j][0], k) for i, (j, k) in m.items()}
    pickle.dump(res, open(os.path.join(ICI, '..', '_cache', 'alignement.pkl'), 'wb'))
    pickle.dump(table, open(os.path.join(ICI, '..', '_cache', 'reloc_a5.pkl'), 'wb'))
    for lo, hi, d in table: print("  A5 traduit $%04x-$%04x -> arcade %+#x" % (lo, hi, d if d < 0x8000 else d - 0x10000))

if __name__ == '__main__':
    main()
