"""Champs des objets PROJECTILES (2026-10-07) : décalage PSP <-> arcade, par vote sur des routines appariées.
Paires : (1) moteur commun 0x725C0/0x72678/0x72744/0x7284C/0x728F0 <-> $33074/$330C4/$33120/$331D0/$33210 ;
(2) pour chaque perso d'arcade ayant un projectile renvoyable (appelant de 0x72744), table d'états PSP du projectile
(contient la routine qui appelle 0x72744) <-> table d'états arcade de $32F46[perso] (move.b $4(a6),d0 ; table PC),
entrée k <-> entrée k. Alignement des accès (champs.lcs) et vote. Sortie : champs_projectiles.json"""
import struct, json, collections, sys
from champs import acc68, accpsp, lcs
from relocs import img
D = open(__import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "cps2", "sfa3ud_prog.bin"), "rb").read()
U = lambda i: struct.unpack_from("<I", img, i)[0]
MOTEUR = [(0x33074, 0x725C0), (0x330C4, 0x72678), (0x33120, 0x72744), (0x331D0, 0x7284C), (0x33210, 0x728F0)]
def jal(t): return struct.pack("<I", 0x0C000000 | (t >> 2))
def debut_fn(o):
    """début de la routine PSP contenant o (prologue addiu sp,sp,-x ou après jr ra précédent)"""
    a = o
    while a > 0:
        a -= 4
        if U(a) == 0x03E00008: return a + 8
    return o
def table_psp(f):
    for i in range(0x200000, len(img) - 4, 4):
        if U(i) == f:
            s = i
            while U(s - 4) and abs(U(s - 4) - f) < 0x8000: s -= 4
            e = i
            while U(e + 4) and abs(U(e + 4) - f) < 0x8000: e += 4
            return [U(k) for k in range(s, e + 4, 4)]
def table_arcade(r):
    """r : routine arcade du perso ; motif move.b $4(a6),d0 ; move.w t(pc,d0.w),d1 ; jmp/jsr t(pc,d1.w)"""
    if D[r:r + 4] != b"\x10\x2e\x00\x04": return None
    t = r + 6 + struct.unpack_from(">h", D, r + 6)[0]
    out = []
    for k in range(16):
        x = t + struct.unpack_from(">h", D, t + 2 * k)[0]
        if not r <= x < r + 0x2000: break
        out.append(x)
    return out
def paires():
    P = list(MOTEUR)
    appelants = [o for o in range(0, len(img) - 4, 4) if img[o:o + 4] == jal(0x72744)]
    import modules
    B = modules.module_bounds()
    for o in appelants:
        c = next((c for c, (a, e) in B.items() if a <= o < e), None)
        if c is None or c >= 0x26: continue
        tp = table_psp(debut_fn(o)); ta = table_arcade(struct.unpack_from(">I", D, 0x32F46 + 4 * c)[0])
        if not tp or not ta: print("perso %#x : tables %s %s" % (c, tp and len(tp), ta and len(ta))); continue
        print("perso %#x : %d états PSP, %d arcade" % (c, len(tp), len(ta)))
        P += list(zip(ta, tp))
    return P
if __name__ == "__main__":
    votes = collections.defaultdict(collections.Counter)
    P = paires()
    for a, p in P:
        for u, v in lcs(acc68(a, a + 0x400), accpsp(p)): votes[v[0]][u[0]] += 1
    res = {}
    for p in sorted(votes):
        (a, n), tot = votes[p].most_common(1)[0], sum(votes[p].values())
        res["%#x" % p] = {"arcade": "$%X" % a, "votes": n, "total": tot}
    json.dump(res, open("champs_projectiles.json", "w"), indent=1)
    print(len(P), "paires")
    for p, v in res.items():
        if v["votes"] >= 2: print(p, v)
