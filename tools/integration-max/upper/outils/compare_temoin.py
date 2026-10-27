#!/usr/bin/env python3
"""(agent_integration_max) TÉMOIN RYU : comparaison au pixel près, hors émulateur, des frames natives d'Upper (module ro5,
positions dans le fichier 390, banque native f355) et des frames du témoin MAX (frames.json, pl00_hx.bin), avec la
résolution TUILE PAR TUILE (local c + bx + 16·by -> table -> global) du banc des sprites.
Usage : compare_temoin.py [nb de frames]"""
import struct, json, sys
R = open('<workspace>/work/cps2/sfa3_gfx_region.bin', 'rb').read()
H = open('<workspace>/work/mame_ro5/hsfa_gfx.bin', 'rb').read()
TEM = '~/.cache/sfa3max/converti/pl00_temoin/'
G = open(TEM + 'max_gfx_temoin.bin', 'rb').read()
def tile(g):
    if g < 0x40000: return R[128*g:128*g+128]
    if g < 0x4DAAB: return H[128*(g-0x40000):128*(g-0x40000)+128]
    if g >= 0x5C8A0: return G[128*(g-0x5C8A0):128*(g-0x5C8A0)+128]
    return None
def tab(f):
    t = open(f, 'rb').read(); return struct.unpack('<%dI' % (len(t)//4), t)
def glob(T, l):
    v = T[l] if l < len(T) else 0xFFFFFFFF
    return None if v == 0xFFFFFFFF else v & 0x3FFFFFFF
def grid(objs, T):
    D = {}
    for x, y, c, a in objs:
        nx = ((a >> 8) & 15) + 1; ny = ((a >> 12) & 15) + 1
        for by in range(ny):
            for bx in range(nx):
                g = glob(T, c + bx + 16*by)
                t = tile(g) if g is not None else None
                if t and g: D[(x + 16*bx, y + 16*by)] = (g, t)      # code 0 = tuile transparente (convention MAX)
    return D
M = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", 'rb').read()
F390 = open('<workspace>/work/cps2/anims/f390.bin', 'rb').read()
def native(exe):
    o = exe - 0x1F0000; h = struct.unpack_from('<3H', M, o); q = (o + 6 + 3) & ~3      # pointeur des positions : aligné
    pos = struct.unpack_from('<I', M, q)[0]; n = h[2] + 1
    E = [struct.unpack_from('<2H', M, q + 4 + 4*k) for k in range(n)]
    if 0xB04000 <= pos < 0xB04000 + len(F390): P = [struct.unpack_from('<2h', F390, pos - 0xB04000 + 4*k) for k in range(n)]
    else: P = [struct.unpack_from('<2h', M, pos - 0x1F0000 + 4*k) for k in range(n)]
    return [(x, y, c, a) for (c, a), (x, y) in zip(E, P)]
if __name__ == "__main__":
    TN = tab('<workspace>/work/agent_integration_max/banc_temoin/banques_hx/f355.bin'); TM = tab(TEM + 'pl00_hx.bin')
    FR = json.load(open(TEM + 'frames.json'))
    C = json.load(open(TEM + 'correspondance.json'))['psp_vers_upper']
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 10**6
    ok = bad = 0
    for k in sorted(C, key=int)[:N]:
        k = int(k)
        if k >= len(FR): break
        A = grid(native(int(C[str(k)]['exec'], 16)), TN); B = grid([tuple(o) for o in FR[k]['objs']], TM)
        if set(A) == set(B) and all(A[p][1] == B[p][1] for p in A): ok += 1; continue
        bad += 1
        if bad <= 4:
            print('frame', k, 'natif', len(A), 'MAX', len(B))
            print('  seulement natif', sorted(set(A) - set(B))[:10]); print('  seulement MAX', sorted(set(B) - set(A))[:10])
            print('  tuiles différentes', [(p, hex(A[p][0]), hex(B[p][0])) for p in A if p in B and A[p][1] != B[p][1]][:8])
    print('identiques', ok, 'différentes', bad)

def bilan():
    """classement des écarts : translation pure (dx, dy), tuiles différentes, autres"""
    import collections
    TN = tab('<workspace>/work/agent_integration_max/banc_temoin/banques_hx/f355.bin'); TM = tab(TEM + 'pl00_hx.bin')
    FR = json.load(open(TEM + 'frames.json')); C = json.load(open(TEM + 'correspondance.json'))['psp_vers_upper']
    cl = collections.Counter(); ex = collections.defaultdict(list)
    for k in sorted(C, key=int):
        k = int(k)
        if k >= len(FR): break
        A = grid(native(int(C[str(k)]['exec'], 16)), TN); B = grid([tuple(o) for o in FR[k]['objs']], TM)
        if set(A) == set(B) and all(A[p][1] == B[p][1] for p in A): cl['identique'] += 1; continue
        a0 = min(A) if A else None; b0 = min(B) if B else None
        if A and B and len(A) == len(B):
            dx, dy = b0[0] - a0[0], b0[1] - a0[1]
            if all((p[0] + dx, p[1] + dy) in B and B[(p[0] + dx, p[1] + dy)][1] == A[p][1] for p in A):
                cl['translation %+d,%+d' % (dx, dy)] += 1; ex['translation %+d,%+d' % (dx, dy)].append(k); continue
        if set(A) == set(B):
            nd = sum(A[p][1] != B[p][1] for p in A)
            cl['tuiles différentes'] += 1; ex['tuiles différentes'].append((k, nd)); continue
        cl['autre'] += 1; ex['autre'].append((k, len(A), len(B)))
    for c, n in cl.most_common(): print('%-24s %4d  %s' % (c, n, ex[c][:12]))
