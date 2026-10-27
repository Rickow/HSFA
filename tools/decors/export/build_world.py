"""RECOLLAGE : image « monde » de chaque plan a partir du releve par image (recs/<ID>/full.rec).

Pour chaque image t rendue (registres t-1 + VRAM t, cf. controle) et chaque plan L :
  - coordonnee monde X d'un pixel ecran = scrollX deroule (continuite) + 64 + sx (+ rowscroll de la ligne pour scroll2)
  - coordonnee monde Y = scrollY deroule + 16 + sy
  - SEULE la partie VISIBLE (fenetre 384x224, composee a coup sur) est recollee : pour chaque case-monde
    touchee, on releve l'entree de tilemap (code, attributs) presente en VRAM a cette image.
Resultat : par plan, grille monde (code, attr) + variantes (tuiles animees) + masque « vu » au pixel
+ masque « visible en 16:9 » (fenetre elargie de 32 px (448) ou 64 px (512) de chaque cote, meme trajet).

ANIMATION PAR DEFILEMENT (export complet, decor $14) : certains decors animent un plan en faisant sauter son
registre de defilement entre plusieurs zones de la tilemap (ex. scroll3 Y +$100 toutes les 8 images, X +$400).
Le defilement est decompose en camera (continue) + decalage de phase (sauts >= 24 px hors changement de mode de
camera, arrondis a 64/16/8 px). Les coordonnees monde sont celles de la camera dans l'espace de la phase
PRINCIPALE (la plus frequente) ; une image de phase k lit la tilemap a (case + delta_k / ts). Les cases des
autres phases sont dans res[L]["phases"][k] (k >= 1 ; l'entree 0 = phase principale).
"""
import sys, json, pickle, collections
sys.path.insert(0, "<workspace>/work/decors_ws/py")
import numpy as np
from recio import read_rec
import cpsgfx as G

def unwrap(vals, mod):
    out, prev = [], None
    for v in vals:
        v %= mod
        if prev is None: u = v
        else:
            d = (v - prev) % mod
            if d >= mod // 2: d -= mod
            u = prev + d
        out.append(u); prev = u
    return out

def decompose(vals, mod, modes, seuil=24):
    """-> (camera deroulee, decalage de phase mod `mod`, nb de sauts, sauts non quantifiables)"""
    cam, off = [vals[0] % mod], [0]
    nj = bad = 0
    for i in range(1, len(vals)):
        d = (vals[i] - vals[i - 1]) % mod
        if d >= mod // 2: d -= mod
        q = 0
        trans = any(modes[j] != modes[j - 1] for j in range(max(1, i - 3), min(len(modes), i + 4)))
        if abs(d) >= seuil and not (trans and abs(d) <= 80):
            for qu, tol in ((64, 16), (16, 6), (8, 3)):
                qq = int(round(d / qu)) * qu
                if abs(d - qq) <= tol: q = qq; break
            else:
                bad += 1
            if q: nj += 1
        cam.append(cam[-1] + d - q); off.append((off[-1] + q) % mod)
    return cam, off, nj, bad

def build(rec_path, out_path, extra=(32, 64)):
    frs = read_rec(rec_path)
    res = {}
    for L in (1, 2, 3):
        Lg = G.LAYERS[L]; ts = Lg["ts"]; W = G.TM * ts
        regs = frs[:-1]; data = frs[1:]          # image rendue k : regs frs[k-1], donnees frs[k]
        modes = [getattr(dd, "mode", None) or "nat" for dd in regs]
        cx, ox, njx, bx = decompose([f.reg(Lg["rx"]) for f in regs], W, modes)
        cy, oy, njy, by = decompose([f.reg(Lg["ry"]) for f in regs], W, modes)
        ph_cnt = collections.Counter(zip(ox, oy))
        main = ph_cnt.most_common(1)[0][0]
        plist = [main] + [p for p, _ in ph_cnt.most_common() if p != main]
        pidx = {p: k for k, p in enumerate(plist)}
        phase = [pidx[(a, b)] for a, b in zip(ox, oy)]
        deltas = [((p[0] - main[0]) % W, (p[1] - main[1]) % W) for p in plist]
        sx_u = [c + main[0] for c in cx]; sy_u = [c + main[1] for c in cy]
        if len(plist) > 1:
            print("   plan %d : ANIMATION PAR DEFILEMENT : %d phases (sauts X %d, Y %d, non quantifies %d) : %s"
                  % (L, len(plist), njx, njy, bx + by,
                     ", ".join("+%X,+%X (%d img)" % (dx, dy, ph_cnt[p]) for (dx, dy), p in zip(deltas, plist))))
            for dx, dy in deltas:
                if dx % ts or dy % ts: print("   ATTENTION : decalage de phase non multiple de la tuile", dx, dy)
        # rowscroll (scroll2 seulement) : decalage signe par ligne ecran
        rsl = []
        for f, d in zip(regs, data):
            rs = np.zeros(224, np.int64)
            if L == 2 and (f.reg(0x22) & 1):
                ob = (f.reg(0x08) << 8) & 0xfff800; oo = (ob - 0x900000) // 2
                v = d.vram[oo + ((np.arange(224) + 16 + f.reg(0x20)) & 0x3ff)].astype(np.int64)
                rs = np.where(v >= 0x8000, v - 0x10000, v)
            rsl.append(rs)
        mx = max(extra)
        x0 = min(sx_u[i] + 64 + int(rsl[i].min()) for i in range(len(regs))) - mx
        x1 = max(sx_u[i] + 64 + int(rsl[i].max()) for i in range(len(regs))) + 384 + mx
        y0 = min(sy_u) + 16; y1 = max(sy_u) + 16 + 224
        X0 = (x0 // ts) * ts; X1 = -(-x1 // ts) * ts; Y0 = (y0 // ts) * ts; Y1 = -(-y1 // ts) * ts
        WW, HH = X1 - X0, Y1 - Y0
        if WW > 8192 or HH > 4096:
            raise SystemExit("plan %d : monde aberrant %dx%d (defilement non decompose ?)" % (L, WW, HH))
        seen = np.zeros((HH, WW), bool)
        vis = {e: np.zeros((HH, WW), bool) for e in extra}
        P = [dict(cells=collections.defaultdict(collections.Counter), cells_col=collections.defaultdict(collections.Counter),
                  first={}) for _ in plist]
        base = (regs[0].reg(Lg["base"]) << 8) & 0xffc000
        bases = set()
        sy = np.arange(224)
        for i, (f, d) in enumerate(zip(regs, data)):
            fb = ((f.reg(Lg["base"]) * 256) & ~0x3fff) & 0x3ffff     # cps1_base de MAME (decalage dans gfxram)
            bases.add(fb)
            o0 = fb // 2
            wy = sy_u[i] + 16 + sy - Y0                       # lignes monde (relatif)
            used = set()
            for y in range(224):
                wx0 = sx_u[i] + 64 + int(rsl[i][y]) - X0
                seen[wy[y], wx0:wx0 + 384] = True
                for e in extra: vis[e][wy[y], wx0 - e:wx0 + 384 + e] = True
                r = (wy[y] + Y0) // ts
                for cc in range((wx0 + X0) // ts, (wx0 + X0 + 383) // ts + 1):
                    used.add((cc, r))
            vcols = {cc for (cc, r) in used}
            # toutes les phases sont lues a chaque image : les zones de tilemap des autres phases sont en VRAM
            # (plans statiques ; anneau scroll1 compose sur toute sa hauteur pour les colonnes visibles)
            for k in range(len(plist)):
                dcx, dcy = deltas[k][0] // ts, deltas[k][1] // ts
                cells, cells_col, first = P[k]["cells"], P[k]["cells_col"], P[k]["first"]
                if len(plist) > 1 and dcx and k != phase[i] and L == 1:
                    continue                              # anneau : colonnes d'une autre phase X non garanties
                for cc in vcols:
                    for r in range(Y0 // ts, Y1 // ts):
                        o = o0 + 2 * G.scan(L, (cc + dcx) % G.TM, (r + dcy) % G.TM)
                        cells_col[(cc, r)][(int(d.vram[o]), int(d.vram[o + 1]))] += 1
                for (cc, r) in used:
                    o = o0 + 2 * G.scan(L, (cc + dcx) % G.TM, (r + dcy) % G.TM)
                    ent = (int(d.vram[o]), int(d.vram[o + 1]))
                    cells[(cc, r)][ent] += 1
                    first.setdefault((cc, r, ent), i)
        cells, cells_col, first = P[0]["cells"], P[0]["cells_col"], P[0]["first"]
        phases = [dict(delta=deltas[k], tilemap_off=plist[k], n=ph_cnt[plist[k]],
                       cells=None if k == 0 else {kk: dict(v) for kk, v in P[k]["cells"].items()},
                       cells_col=None if k == 0 else {kk: dict(v) for kk, v in P[k]["cells_col"].items()})
                  for k in range(len(plist))]
        res[L] = dict(ts=ts, X0=X0, Y0=Y0, WW=WW, HH=HH, seen=seen, vis=vis,
                      cells={k: dict(v) for k, v in cells.items()}, first=first,
                      cells_col={k: dict(v) for k, v in cells_col.items()},
                      scroll_x=sx_u, scroll_y=sy_u, rs=[r.tolist() for r in rsl], base=base,
                      bases=sorted(bases), modes=modes,
                      camy=[getattr(dd, "camy", 0) for dd in regs],
                      phase=phase, phases=phases)
        nconf = sum(1 for v in cells.values() if len(v) > 1)
        # coherence : pour les cases vues, l'entree « colonne composee » = l'entree vue ?
        bad = sum(1 for k, v in cells.items() if set(cells_col[k]) - set(v))
        extra_c = sum(1 for k in cells_col if k not in cells)
        print("   plan %d : cases colonne-composee hors vue %d ; incoherences colonne/vue %d" % (L, extra_c, bad))
        print("plan %d : monde X [%d,%d) Y [%d,%d) = %dx%d px ; cases vues %d ; cases a plusieurs entrees %d"
              % (L, X0, X1, Y0, Y1, WW, HH, len(cells), nconf))
    pickle.dump(res, open(out_path, "wb"))
    return res

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
