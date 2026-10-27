#!/usr/bin/env python3
"""EXPORT COMPLET : tous les decors de SFA3 dans UN SEUL PSD (un groupe par jeu de donnees de decor).

Pour chaque decor <ID> (recs/<ID>/ = releve lua/rec_all.lua + captures des plans isoles ; work/monde_<ID>.pkl =
build_world.py) : images monde par plan, zones a combler (course REELLE + marge Y forcee), controles d'exactitude,
PNG / ACT / JSON dans out/decors/decor<ID>/, puis le groupe du decor dans out/decors_sfa3.psd.

Usage : export_tous.py [--decors 00,02,...] [--sans-psd]
"""
import sys, os, json, pickle, collections, argparse, gc
sys.path.insert(0, "<workspace>/work/decors_ws/py")
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from recio import read_rec, read_scr
import cpsgfx as G
import world_render as R
from psdwriter import Layer, Group, write_psd, compress_layer

D = "<workspace>/work/decors_ws"
OUT = D + "/out"
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    FONTB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
except Exception:
    FONT = FONTB = None

PERSO = ["Ryu", "Ken", "Akuma", "Charlie", "Chun-Li", "Adon", "Sodom", "Guy", "Birdie", "Rose", "M.Bison", "Sagat",
         "Dan", "Sakura", "Rolento", "Dhalsim", "Zangief", "Gen", "Chun-Li (variante)", "Gen (variante)",
         "Sodom (variante)", "Balrog", "Cammy", "Evil Ryu", "E.Honda", "Blanka", "R.Mika", "Cody", "Vega", "Karin",
         "Juli", "Juni"]
# decors qui PARTAGENT leurs donnees (listes + palettes ; INJECTION-FORK §5) : un seul groupe par jeu de donnees
LIES = [["00", "2E"], ["08", "24"], ["0C", "28"], ["22", "26"], ["2A", "3C", "3E"]]
NOTE_14 = "$14 partage aussi scroll1/scroll3 avec le groupe $2A/$3C/$3E (INJECTION-FORK §5)"
DESCR = {"0C": {"titre": "temple à cloche",
                1: "lanternes, guirlandes, statues", 2: "façades, ville, sol", 3: "cloche, arbre, balustrade, bannières"}}
COURT = {1: "scroll1", 2: "scroll2", 3: "scroll3"}
RANG = {0: "fond", 1: "plan médian", 2: "avant-plan"}
EXTRA = (32, 64)
MX = 64
PAL_LIBRES = json.load(open(D + "/injection_fork/palettes_libres_ro3.json"))


def nom_decor(i):
    return "$%s (%s)" % (i, PERSO[int(i, 16) // 2])


def groupes_decors():
    """-> liste de jeux de donnees : [id principal, ids lies...] pour les 32 decors"""
    vus, out = set(), []
    for k in range(0, 0x40, 2):
        i = "%02X" % k
        if i in vus: continue
        g = next((l for l in LIES if i in l), [i])
        vus.update(g); out.append(g)
    return out


def cps_rgb(w):
    b = 0x0f + ((w >> 12) << 1)
    return tuple(min(255, ((w >> s) & 15) * 0x11 * b // 0x2d) for s in (8, 4, 0))


def rgba_mask(mask, color):
    a = np.zeros(mask.shape + (4,), np.uint8); a[mask] = color; return a


def over(dst, src):
    a = src[:, :, 3:4].astype(np.float32) / 255
    dst[:, :, :3] = (src[:, :, :3] * a + dst[:, :, :3] * (1 - a)).astype(np.uint8)


def periode(w):
    """plus petite periode X (en cases) du monde d'un plan (cases connues identiques), ou None"""
    cells, _ = R.merged_cells(w)
    ent = {k: R.main_entry(v) for k, v in cells.items()}
    for p in range(8, w["WW"] // w["ts"] // 2):
        tot = bad = 0
        for (c, r), e in ent.items():
            o = ent.get((c + p, r))
            if o is not None:
                tot += 1; bad += o != e
                if bad: break
        if tot > 200 and not bad: return p
    return None


def replier(w, n):
    """plan a DEFILEMENT AUTOMATIQUE (le defilement change camera fixe, ex. nuages) : le monde deroule est une
    bande periodique ; on le replie sur UNE periode P (+ fenetre 512) et on ramene les defilements dans [X0, X0+P)."""
    ts = w["ts"]; p = periode(w)
    if not p: return None
    P = p * ts; A = w["X0"]; WWn = P + 576; ncol = WWn // ts
    def fold(cells):
        f = {}
        for (c, r), v in cells.items(): f.setdefault(((c - A // ts) % p, r), v)
        out = {}
        for cc in range(ncol):
            for (c0, r), v in f.items():
                if c0 == cc % p: out[(A // ts + cc, r)] = v
        return out
    seen = np.zeros((w["HH"], WWn), bool)
    xs = (np.arange(w["WW"]) + w["X0"] - A) % P
    for x in range(WWn):
        seen[:, x] = w["seen"][:, xs == (x % P)].any(1)
    nw = dict(w)
    nw.update(WW=WWn, cells=fold(w["cells"]), cells_col=fold(w.get("cells_col", {})), seen=seen,
              scroll_x=[A + ((sx - A) % P) for sx in w["scroll_x"]], periode_auto=P, phases=None, phase=None)
    return nw


def fmtp(v):
    return v if isinstance(v, str) else "%.3f" % v


def process(ids):
    ID = ids[0]
    out = os.path.join(OUT, "decors", "decor%s" % ID); os.makedirs(out, exist_ok=True)
    W = pickle.load(open(D + "/work/monde_%s.pkl" % ID, "rb"))
    frs = read_rec(D + "/recs/%s/full.rec" % ID)
    regs, data = frs[:-1], frs[1:]
    n = len(regs)
    modes = W[3]["modes"]
    auto = {}
    for L in (1, 2, 3):
        if W[L]["WW"] > 2000:                    # bande deroulee trop longue : defilement automatique ?
            nw = replier(W[L], None)
            if nw: auto[L] = nw["periode_auto"]; W[L] = nw; print("   %s : defilement automatique replie sur %d px" % (ID, auto[L]), flush=True)
    ff = next((i for i in range(n) if modes[i] in ("cup", "cdn")), n)
    real = [i for i in range(n) if modes[i] in ("nat", "haut") and i < ff]
    allv = list(range(n))
    order = collections.Counter(tuple(G.layer_order(f)) for f in regs).most_common()
    lorder = list(order[0][0])                                   # bas -> haut
    rang = {L: RANG[min(2, lorder.index(L))] if L in lorder else "plan inactif" for L in (1, 2, 3)}
    info = {}
    for L in (1, 2, 3):
        w = W[L]; sx = np.array(w["scroll_x"]); sy = np.array(w["scroll_y"])
        info[L] = dict(sx=(int(sx[real].min()), int(sx[real].max())), sy_reel=(int(sy[real].min()), int(sy[real].max())),
                       sy_tout=(int(sy.min()), int(sy.max())))
    # plan de reference = plus grande course X
    Lr = max([L for L in (1, 2, 3) if L not in auto], key=lambda L: info[L]["sx"][1] - info[L]["sx"][0])
    sxr = W[Lr]["scroll_x"]; syr = W[Lr]["scroll_y"]
    # Y nominal = camera au repos ($FF82A4 = 0) ; sinon (decors ou les images camera haute dominent) le sens s'inverse
    repos = [i for i in real if W[Lr]["camy"][i] == 0] or real
    nominal = collections.Counter(syr[i] for i in repos).most_common(1)[0][0]
    for L in (1, 2, 3):
        a = np.array([W[Lr]["scroll_x"][i] for i in real], float); b = np.array([W[L]["scroll_x"][i] for i in real], float)
        info[L]["parallaxe"] = round(float(np.polyfit(a, b, 1)[0]), 3) if np.ptp(a) else 1.0
        if L in auto: info[L]["parallaxe"] = "auto (cyclique %d px)" % auto[L]
        rsv = sorted({v for i in real for v in W[L]["rs"][i]})
        info[L]["rowscroll"] = "inactif" if rsv == [0] else ("constant %+d" % rsv[0] if len(rsv) == 1 else "variable (%d valeurs, %+d..%+d)" % (len(rsv), rsv[0], rsv[-1]))
    ref = min(real, key=lambda i: (sxr[i], syr[i] != nominal))
    palref_i = max(i for i in real if syr[i] == nominal)
    palette = data[palref_i].pal
    course_x = max(info[L]["sx"][1] - info[L]["sx"][0] for L in (1, 2, 3) if L not in auto)
    up_reel = nominal - info[Lr]["sy_reel"][0]; dn_reel = info[Lr]["sy_reel"][1] - nominal
    up_tout = nominal - info[Lr]["sy_tout"][0]; dn_tout = info[Lr]["sy_tout"][1] - nominal
    # placement : chaque plan est cale sur l'ecran de l'image ref (butee gauche, Y nominal) ; le canevas couvre
    # l'union des images monde de tous les plans (parallaxe, rowscroll, camera forcee compris)
    raw = {}
    for L in (1, 2, 3):
        w = W[L]
        rsr = int(np.median(w["rs"][ref]))
        raw[L] = (w["X0"] - (w["scroll_x"][ref] + 64 + rsr), w["Y0"] - (w["scroll_y"][ref] + 16))
    minx = min(raw[L][0] for L in raw); miny = min(raw[L][1] for L in raw)
    SX0, SY0 = -minx, -miny                       # ecran de l'image ref dans le canevas
    CW = max(raw[L][0] - minx + W[L]["WW"] for L in raw)
    CH = max(raw[L][1] - miny + W[L]["HH"] for L in raw)
    camtop = max(W[3]["camy"][i] for i in real) if real else 0

    def place(L):
        return raw[L][0] - minx, raw[L][1] - miny

    def to_canvas(L, arr, fill=0):
        ox, oy = place(L)
        c = np.full((CH, CW) + arr.shape[2:], fill, arr.dtype)
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(CH, oy + arr.shape[0]), min(CW, ox + arr.shape[1])
        if ye > ys and xe > xs:
            c[ys:ye, xs:xe] = arr[ys - oy:ye - oy, xs - ox:xe - ox]
        return c

    allpal = np.array([d.pal for d in data])
    # images a « flash global » (super, eclair : la plupart des palettes de decor changent) : exclues du
    # reperage des palettes cycliques
    ref_blk = allpal[palref_i, 0x200:0x800].reshape(96, 16, 3)
    diffr = (allpal[:, 0x200:0x800].reshape(n, 96, 16, 3) != ref_blk[None]).any((2, 3)).mean(1)
    calme = [i for i in range(n) if diffr[i] < 0.5]
    flashes = n - len(calme)
    P = {}
    pal_var = {}
    for L in (1, 2, 3):
        w = W[L]; ts = w["ts"]
        pen, pl, known, srcm = R.world_pens(W, L, with_src=True)
        phs = w.get("phases") or [dict(delta=(0, 0), tilemap_off=(0, 0), n=n, cells=None, cells_col=None)]
        phase = w.get("phase") or [0] * n
        phpen = [(pen, pl, known)]
        for k in range(1, len(phs)):
            wk = dict(w); wk["cells"] = phs[k]["cells"]; wk["cells_col"] = phs[k]["cells_col"]
            phpen.append(R.world_pens({L: wk}, L))
        anim = {k: v for k, v in w["cells"].items() if len(v) > 1}
        p0 = G.LAYERS[L]["pal0"]
        cells, _ = R.merged_cells(w)
        used = sorted({p0 + (R.main_entry(c)[1] & 0x1f) for c in cells.values()})
        pal_var[L] = []
        for p in used:
            nv = len({allpal[i, p * 16:(p + 1) * 16].tobytes() for i in calme})
            if nv > 1: pal_var[L].append((p, nv))
        # zones geometriques : course reelle / course avec camera forcee
        req = {}
        for nom, idx in (("reel", real), ("tout", allv)):
            for e in (0,) + EXTRA:
                m = np.zeros((w["HH"], w["WW"]), bool)
                sxs = [w["scroll_x"][i] for i in idx]; sys_ = [w["scroll_y"][i] for i in idx]
                for y in range(224):
                    xs_ = [w["scroll_x"][i] + 64 + w["rs"][i][y] for i in idx]
                    lo, hi = min(xs_) - w["X0"] - e, max(xs_) + 384 - w["X0"] + e
                    r0 = min(sys_) + 16 + y - w["Y0"]; r1 = max(sys_) + 16 + y - w["Y0"]
                    m[max(0, r0):r1 + 1, max(0, lo):max(0, hi)] = True
                req[(nom, e)] = m
        # decoupe : on ne garde que ce qui peut s'afficher (course + camera forcee + 512, ou deja vu) ;
        # au-dela (ex. colonnes completees loin du sol en perspective) = contenu de tilemap jamais montre
        clip = req[("tout", 64)] | w["seen"]
        for a, b, kn in phpen:
            a[~clip] = 15; kn &= clip
        known = phpen[0][2]
        rgba = R.to_rgba(pen, pl, palette, known)
        phrgba = [None] + [R.to_rgba(a, b, palette, kn) for a, b, kn in phpen[1:]]
        trous = req[("reel", 0)] & ~known
        # VRAM hors course (images reelles pres des butees)
        hors = np.zeros((w["HH"], w["WW"], 4), np.uint8); hset = np.zeros((w["HH"], w["WW"]), bool)
        inco = np.zeros((w["HH"], w["WW"]), bool)
        unk = ~known
        sxm, sxM = info[L]["sx"]
        Wt = G.TM * ts
        for i in real:
            if phase[i] != 0 or L in auto: continue
            if not (w["scroll_x"][i] - sxm < MX or sxM - w["scroll_x"][i] < MX): continue
            f = G.mix(regs[i], data[i])
            pens_tm, pal_tm = G.tilemap_pens(f, L)
            for y in range(224):
                wy = w["scroll_y"][i] + 16 + y - w["Y0"]
                wx0 = w["scroll_x"][i] + 64 + w["rs"][i][y] - w["X0"]
                for xa, xb in ((wx0 - MX, wx0), (wx0 + 384, wx0 + 384 + MX)):
                    xs = np.arange(max(0, xa), min(w["WW"], xb))
                    xs = xs[unk[wy, xs]] if xs.size else xs
                    if xs.size == 0: continue
                    tx = (xs + w["X0"]) % Wt; ty = (wy + w["Y0"]) % Wt
                    pp = pens_tm[ty, tx]; qq = pal_tm[ty, tx].astype(np.int64)
                    col = np.concatenate([data[i].pal[qq * 16 + pp], np.where(pp != 15, 255, 0)[:, None]], 1).astype(np.uint8)
                    inco[wy, xs] |= hset[wy, xs] & (hors[wy, xs] != col).any(1)
                    hors[wy, xs] = col; hset[wy, xs] = True
        P[L] = dict(pen=pen, pl=pl, known=known, srcm=srcm, rgba=rgba, anim=anim, used=used, req=req, trous=trous,
                    hors=hors, inco=int(inco.sum()), phpen=phpen, phrgba=phrgba, phs=phs, phase=phase)

    # ---------------- controles ----------------
    ctrl = {}
    scr = {L: read_scr(D + "/recs/%s/scr_%d.bin" % (ID, L)) for L in (0, 1, 2, 3)}
    for L in (1, 2, 3):
        w = W[L]; Q = P[L]
        ams = []
        for k in range(len(Q["phs"])):
            am = np.zeros_like(Q["known"])
            an = Q["anim"] if k == 0 else [kk for kk, v in Q["phs"][k]["cells"].items() if len(v) > 1]
            for (cc, r) in an:
                am[r * w["ts"] - w["Y0"]:(r + 1) * w["ts"] - w["Y0"], cc * w["ts"] - w["X0"]:(cc + 1) * w["ts"] - w["X0"]] = True
            ams.append(am)
        Q["ams"] = ams
        tot = ta = ni = 0; pires = []; parmode = collections.Counter()
        for t in sorted(scr[L]):
            if t < 8: continue
            i = t - 1
            wy = (w["scroll_y"][i] + 16 + np.arange(224) - w["Y0"])[:, None]
            wx = w["scroll_x"][i] + 64 + np.array(w["rs"][i])[:, None] + np.arange(384)[None, :] - w["X0"]
            ph = Q["phpen"][Q["phase"][i]]
            pp = ph[0][wy, wx]; qq = ph[1][wy, wx]
            img = np.where((pp != 15)[:, :, None], data[i].pal[qq * 16 + pp], 0).astype(np.uint8)
            dm = (img != scr[L][t]).any(2); da = dm & Q["ams"][Q["phase"][i]][wy, wx]
            tot += int(dm.sum()); ta += int(da.sum()); ni += 1; parmode[modes[i]] += 1
            if dm.sum() - da.sum(): pires.append((t, modes[i], int(dm.sum()), int(da.sum())))
        ctrl[COURT[L]] = dict(images=ni, px_differents=tot, dont_cases_animees=ta, hors_cases_animees=tot - ta,
                              images_par_mode=dict(parmode), pires_hors_anim=sorted(pires, key=lambda x: -x[2])[:5])
    # composite des 3 plans (ordre CPS-B de chaque image) depuis les images monde vs capture « plans seuls »
    tot = 0; ni = 0; tot_anim = 0; nph = 0
    for t in sorted(scr[0]):
        if t < 8: continue
        i = t - 1
        img = np.zeros((224, 384, 3), np.uint8); anim_px = np.zeros((224, 384), bool)
        for L in G.layer_order(regs[i]):
            w = W[L]; Q = P[L]
            wy = (w["scroll_y"][i] + 16 + np.arange(224) - w["Y0"])[:, None]
            wx = w["scroll_x"][i] + 64 + np.array(w["rs"][i])[:, None] + np.arange(384)[None, :] - w["X0"]
            ph = Q["phpen"][Q["phase"][i]]
            pp = ph[0][wy, wx]; qq = ph[1][wy, wx]
            m = pp != 15
            img[m] = data[i].pal[qq * 16 + pp][m]
            col = (wx + w["X0"]) // w["ts"]; row = (wy + w["Y0"]) // w["ts"]
            anim_px |= Q["ams"][Q["phase"][i]][wy, wx]
        dm = (img != scr[0][t]).any(2)
        if any(P[L]["phase"][i] for L in (1, 2, 3)): nph += 1
        tot += int(dm.sum()); tot_anim += int((dm & anim_px).sum()); ni += 1
    ctrl["composite_3_plans"] = dict(images_hors_phase_principale=nph, images=ni, px_differents=tot, dont_cases_animees=tot_anim, hors_cases_animees=tot - tot_anim)
    coh = {COURT[L]: sum(1 for k, v in W[L]["cells"].items() if set(W[L]["cells_col"].get(k, {})) - set(v)) for L in (1, 2, 3)}
    ctrl["incoherences_colonne_vue"] = coh
    ctrl["trous_course_reelle_px"] = {COURT[L]: int(P[L]["trous"].sum()) for L in (1, 2, 3)}

    # ---------------- zones ----------------
    zones = {}
    for L in (1, 2, 3):
        Q = P[L]; kc = to_canvas(L, Q["known"], False); z = {}
        for e in EXTRA:
            zr = to_canvas(L, Q["req"][("reel", e)], False) & ~kc
            zt = to_canvas(L, Q["req"][("tout", e)], False) & ~kc & ~zr
            cols = np.nonzero(zr.any(0))[0]; rows = np.nonzero(zr.any(1))[0]
            z[e] = dict(px_course_reelle=int(zr.sum()), px_marge_y=int(zt.sum()),
                        gauche=[int(cols[cols < CW // 2].min()), int(cols[cols < CW // 2].max()) + 1] if (cols < CW // 2).any() else None,
                        droite=[int(cols[cols >= CW // 2].min()), int(cols[cols >= CW // 2].max()) + 1] if (cols >= CW // 2).any() else None,
                        lignes=[int(rows.min()), int(rows.max()) + 1] if rows.size else None,
                        largeur_gauche=int(((zr.any(0)) & (np.arange(CW) < CW // 2)).sum()),
                        largeur_droite=int(((zr.any(0)) & (np.arange(CW) >= CW // 2)).sum()))
            Q["zr%d" % e] = zr; Q["zt%d" % e] = zt
        zones[COURT[L]] = z

    # ---------------- calques ----------------
    desc = DESCR.get(ID, {})
    plane_groups = []
    canv = {}
    for L in reversed(lorder + [x for x in (1, 2, 3) if x not in lorder]):    # haut -> bas
        w = W[L]; Q = P[L]
        nm = "%s (%s %d px)" % (rang[L], COURT[L], w["ts"])
        if desc.get(L): nm += " — " + desc[L]
        if L == 2 and info[2]["rowscroll"] != "inactif": nm += " — SOL À PLAT (rowscroll %s)" % info[2]["rowscroll"]
        img = to_canvas(L, Q["rgba"]); canv[L] = img
        lays = [
            Layer("à combler 448×224 — %s (cible core, course réelle)" % COURT[L], rgba_mask(Q["zr32"], (255, 0, 0, 140))),
            Layer("à combler 448×224 — %s — marge Y hors course réelle (facultatif)" % COURT[L], rgba_mask(Q["zt32"], (255, 0, 160, 90))),
            Layer("à combler 512×224 — %s (option)" % COURT[L], rgba_mask(Q["zr64"] | Q["zt64"], (255, 140, 0, 110)), hidden=True),
        ]
        am = np.zeros((w["HH"], w["WW"], 4), np.uint8)
        for (cc, r) in Q["anim"]:
            y0 = r * w["ts"] - w["Y0"]; x0 = cc * w["ts"] - w["X0"]; ts = w["ts"]
            am[y0:y0 + ts, x0:x0 + ts] = (255, 255, 0, 70)
            am[y0, x0:x0 + ts] = am[y0 + ts - 1, x0:x0 + ts] = (255, 255, 0, 255)
            am[y0:y0 + ts, x0] = am[y0:y0 + ts, x0 + ts - 1] = (255, 255, 0, 255)
        animpals = {p for p, _ in pal_var[L]}
        if animpals:
            cells, _ = R.merged_cells(w)
            for (cc, r), cnt in cells.items():
                if G.LAYERS[L]["pal0"] + (R.main_entry(cnt)[1] & 0x1f) in animpals:
                    y0 = r * w["ts"] - w["Y0"]; x0 = cc * w["ts"] - w["X0"]; ts = w["ts"]
                    sub = am[y0:y0 + ts, x0:x0 + ts]
                    mm = Q["pen"][y0:y0 + ts, x0:x0 + ts] != 15
                    sub[mm & (sub[:, :, 3] == 0)] = (0, 200, 255, 90)
        lays.append(Layer("animations — %s : jaune = tuiles changées (%d cases), cyan = palettes cycliques %s"
                          % (COURT[L], len(Q["anim"]), ",".join("$%02X" % p for p in sorted(animpals)) or "aucune"),
                          to_canvas(L, am), hidden=True))
        lays.append(Layer(nm, img))
        for k in range(1, len(Q["phs"])):
            ph = Q["phs"][k]
            lays.append(Layer("animation par défilement — %s phase %d/%d : tilemap +$%X,+$%X (%d images) — à étendre comme le calque principal"
                              % (COURT[L], k + 1, len(Q["phs"]), ph["delta"][0], ph["delta"][1], ph["n"]),
                              to_canvas(L, Q["phrgba"][k]), hidden=True))
        lays.append(Layer("VRAM hors course — %s : ce que montre un rendu élargi naïf (NON fiable, info)" % COURT[L],
                          to_canvas(L, Q["hors"]), hidden=True))
        plane_groups.append(Group(nm, lays))
        Q["nom"] = nm; Q["origine"] = list(place(L))

    # reperes
    gd = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(gd)
    ynom = SY0
    xr = SX0 + info[Lr]["sx"][1] - sxr[ref]
    for x0, lab in ((SX0, "4:3 butée gauche"), (xr, "4:3 butée droite")):
        for yy, col in ((ynom, (255, 255, 255, 255)), (ynom - up_reel, (255, 255, 255, 120))):
            d.rectangle([x0, yy, x0 + 383, yy + 223], outline=col)
        d.text((x0 + 3, ynom + 3), lab, fill=(255, 255, 255, 255), font=FONT)
        d.rectangle([x0 - 32, ynom, x0 + 383 + 32, ynom + 223], outline=(0, 255, 255, 255))
        d.rectangle([x0 - 64, ynom, x0 + 383 + 64, ynom + 223], outline=(255, 0, 255, 200))
    yr0 = ynom - up_reel; yr1 = ynom + dn_reel + 223
    d.rectangle([SX0, yr0, xr + 383, yr1], outline=(255, 255, 0, 200))
    d.rectangle([SX0, ynom - up_tout, xr + 383, ynom + dn_tout + 223], outline=(255, 150, 0, 150))
    d.text((MX + 3, ynom + 14), "cyan 448 ; magenta 512 ; jaune = course réelle (Y -%d/+%d) ; orange = caméra forcée (-%d/+%d)"
           % (up_reel, dn_reel, up_tout, dn_tout), fill=(0, 255, 255, 255), font=FONT)
    cadres = Layer("cadres 4:3 / 16:9 aux deux butées (blanc 384 nominal / pâle caméra haute, cyan 448, magenta 512, jaune = course réelle, orange = caméra forcée)", np.array(gd))
    grids = []
    for L in (1, 3, 2):
        g = np.zeros((CH, CW, 4), np.uint8); ts = W[L]["ts"]; ox, oy = place(L)
        colr = {1: (255, 255, 255, 60), 2: (0, 255, 0, 90), 3: (255, 0, 255, 110)}[L]
        g[:, np.arange(ox % ts, CW, ts)] = colr; g[np.arange(oy % ts, CH, ts), :] = colr
        grids.append(Layer("grille %s (%d px)" % (COURT[L], ts), g, hidden=True))
    # repere sprites
    sfull = read_scr(D + "/recs/%s/scr_full.bin" % ID)
    spr = np.zeros((CH, CW, 4), np.uint8); picks = []
    for target in (info[Lr]["sx"][0], info[Lr]["sx"][1]):
        cand = [t for t in sorted(sfull) if t >= 8 and t - 1 in real and sxr[t - 1] == target and syr[t - 1] == nominal]
        if cand: picks.append(cand[len(cand) // 2])
    for t in picks:
        dm = (sfull[t] != scr[0][t]).any(2)
        ox_ = sxr[t - 1] - sxr[ref] + SX0; oy_ = syr[t - 1] - syr[ref] + SY0
        if ox_ < 0 or oy_ < 0 or ox_ + 384 > CW or oy_ + 224 > CH: continue
        reg = spr[oy_:oy_ + 224, ox_:ox_ + 384]
        reg[dm] = np.concatenate([sfull[t], np.full((224, 384, 1), 255, np.uint8)], 2)[dm]
    sprite_layer = Layer("repère sprites (images %s : persos, HUD, objets de décor en sprites — hors export)"
                         % ",".join(map(str, picks)), spr, hidden=True)
    # trous : aucun plan opaque
    opq = np.zeros((CH, CW), bool)
    for L in (1, 2, 3): opq |= canv[L][:, :, 3] > 0
    kall = np.zeros((CH, CW), bool)
    for L in (1, 2, 3): kall |= to_canvas(L, P[L]["known"], False)
    noir = kall & ~opq
    # decor qui s'arrete : dans la fenetre 448/512 (camera forcee comprise), hors course 4:3 reelle, aucun plan opaque
    back = lorder[0]
    deja = np.zeros((CH, CW), bool)
    for L in (1, 2, 3): deja |= P[L]["zr64"] | P[L]["zt64"]
    arret = {}
    for e in EXTRA:
        arret[e] = (to_canvas(back, P[back]["req"][("tout", e)], False) & ~to_canvas(back, P[back]["req"][("reel", 0)], False)
                    & ~opq & ~deja)
    rows_a = np.nonzero(arret[32].any(1))[0]
    arret_info = {str(e): dict(px=int(arret[e].sum()),
                               lignes=[int(np.nonzero(arret[e].any(1))[0].min()), int(np.nonzero(arret[e].any(1))[0].max()) + 1] if arret[e].any() else None)
                  for e in EXTRA}
    arret_layers = [
        Layer("à combler 448×224 — DÉCOR QUI S'ARRÊTE : aucun plan opaque hors course 4:3 réelle (caméra forcée, à peindre sur %s)" % COURT[back],
              rgba_mask(arret[32], (0, 140, 255, 130))),
        Layer("à combler 512×224 — décor qui s'arrête (option)", rgba_mask(arret[64] & ~arret[32], (0, 220, 255, 100)), hidden=True)]
    trous_layer = Layer("noir à l'écran : aucun plan opaque (souvent sprites de décor ; au-dessus de la course = décor qui s'arrête)",
                        rgba_mask(noir, (0, 255, 0, 110)), hidden=True)
    # notes
    pl = PAL_LIBRES.get(ID, {})
    def plst(k, s): return ",".join("$" + x for x in pl.get(k, {}).get(s, [])) or "aucune"
    lies = [nom_decor(i) for i in ids]
    notes = [
        "DÉCOR %s — %d images relevées (MAME sfa3ud), dont %d « course réelle » et %d caméra forcée." % (
            " = ".join(lies), n, len(real), n - len(real)),
        ("Données PARTAGÉES par : %s (un seul groupe ; modifier l'un modifie les autres sans relogement)." % ", ".join(lies)) if len(ids) > 1 else "Données propres à ce décor.",
        (NOTE_14 if ID in ("14", "2A") else ""),
        "Ordre CPS-B (layer control $%04X) bas→haut : %s." % (regs[ref].breg(0x26), ", ".join(COURT[L] for L in lorder)),
        "Parallaxe (vs %s) : scroll1 %s, scroll2 %s, scroll3 %s. Rowscroll scroll2 : %s." % (
            COURT[Lr], fmtp(info[1]["parallaxe"]), fmtp(info[2]["parallaxe"]), fmtp(info[3]["parallaxe"]), info[2]["rowscroll"]),
        ("DÉFILEMENT AUTOMATIQUE : %s — bande cyclique (période = tilemap entière) exportée sur une période + 576 px : rien à combler en X, seulement en Y." % (
            ", ".join("%s %d px" % (COURT[L], auto[L]) for L in auto))) if auto else "",
        "Course caméra : X %d px ; Y réelle maximale -%d / +%d px (butée haute mesurée $FF82A4 = %d : joueurs forcés très haut, le jeu plafonne la caméra ; vers le bas 0 hors secousses de quelques px) ; exportée -%d / +%d (caméra forcée au-delà)." % (
            course_x, up_reel, dn_reel, camtop, up_tout, dn_tout),
        "PALETTES UTILISABLES par l'utilisateur (avec relogement fork/FBNeo, tilemaps complètes, décors liés compris) :",
        "    scroll1 : %s" % plst("reloge", "scroll1"),
        "    scroll2 : %s" % plst("reloge", "scroll2"),
        "    scroll3 : %s   ($7F jamais utilisable en scroll3)" % plst("reloge", "scroll3"),
        "  en place (arcade, sans relogement) : s1 %s ; s2 %s ; s3 %s." % (
            plst("en_place", "scroll1"), plst("en_place", "scroll2"), plst("en_place", "scroll3")),
        "Animations : tuiles changeantes s1/s2/s3 = %d/%d/%d cases ; palettes cycliques : %s." % (
            len(P[1]["anim"]), len(P[2]["anim"]), len(P[3]["anim"]),
            "; ".join("%s %s" % (COURT[L], ",".join("$%02X(%d)" % pv for pv in pal_var[L])) for L in (1, 2, 3) if pal_var[L]) or "aucune"),
        "Pen 15 = transparent. Palette de référence : image %d (course réelle, Y nominal). Images à flash global (exclues des cycles) : %d." % (palref_i, flashes),
        "À COMBLER rouge = visible en 448×224 dans la course réelle ; rose = marge Y (caméra forcée) ; orange (masqué) = 512 ; bleu = décor qui s'arrête (%d px en 448, à peindre sur %s)." % (arret_info["32"]["px"], COURT[back]),
        ("Animation PAR DÉFILEMENT (le jeu fait sauter le registre de défilement entre des zones de la tilemap) : %s ; calques masqués « phase k » : étendre chaque phase comme le calque principal." % "; ".join(
            "%s %d phases" % (COURT[L], len(P[L]["phs"])) for L in (1, 2, 3) if len(P[L]["phs"]) > 1)) if any(len(P[L]["phs"]) > 1 for L in (1, 2, 3)) else "",
        "VRAM hors course (masqué) = contenu de tilemap là où le jeu ne compose rien : non fiable.",
    ]
    notes = [x for x in notes if x]
    nimg = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); nd = ImageDraw.Draw(nimg)
    lignes = []
    for t in notes:                                   # retour a la ligne a la largeur du canevas
        ind = "      " if t.startswith("    ") else "    "
        cur = ""
        for mot in t.split(" "):
            essai = (cur + " " + mot) if cur else mot
            if cur and nd.textlength(essai, font=FONT) > CW - 24:
                lignes.append(cur); cur = ind + mot
            else:
                cur = essai
        lignes.append(cur)
    pas = 12 if 16 + 12 * len(lignes) <= CH - 4 else max(9, (CH - 20) // len(lignes))
    nd.rectangle([4, 4, CW - 5, min(CH - 1, 16 + pas * len(lignes))], fill=(0, 0, 0, 215))
    for k, t in enumerate(lignes): nd.text((10, 8 + pas * k), t, fill=(255, 255, 255, 255), font=FONT)
    note_layer = Layer("NOTES (lire) — palettes utilisables, décors liés, course, animations", np.array(nimg), hidden=True)
    reperes = Group("repères (masqué)", [cadres, sprite_layer] + grids, hidden=True)
    titre = "SFA3 — décor " + " + ".join(lies) + (" — " + desc["titre"] if desc.get("titre") else "")
    grp = Group(titre, [note_layer] + arret_layers + [trous_layer, reperes] + plane_groups)

    # ---------------- apercus ----------------
    flat = np.zeros((CH, CW, 4), np.uint8); flat[:, :, 3] = 255
    for L in lorder: over(flat, canv[L])
    Image.fromarray(flat).save(os.path.join(out, "apercu_decor.png"))
    zon = flat.copy()
    for L in lorder:
        over(zon, rgba_mask(P[L]["zt64"] | P[L]["zr64"], (255, 140, 0, 70)))
        over(zon, rgba_mask(P[L]["zt32"], (255, 0, 160, 110)))
        over(zon, rgba_mask(P[L]["zr32"], (255, 0, 0, 130)))
    over(zon, rgba_mask(arret[64] & ~arret[32], (0, 220, 255, 70)))
    over(zon, rgba_mask(arret[32], (0, 140, 255, 130)))
    over(zon, np.array(gd))
    Image.fromarray(zon).save(os.path.join(out, "apercu_zones.png"))
    for L in (1, 2, 3): Image.fromarray(canv[L]).save(os.path.join(out, "plan_%s.png" % COURT[L]))

    # ---------------- palettes ----------------
    po = (((regs[palref_i].reg(0x0a) * 256) & ~0x3ff) & 0x3ffff) // 2
    raw = regs[palref_i].vram[po:po + 0xC00]
    conv_ok = sum(cps_rgb(int(raw[i])) == tuple(int(v) for v in palette[i]) for i in range(0x200, 0x800))
    paljson = {"decor": titre, "image_ref": palref_i, "conversion_rgb_ok": "%d/1536" % conv_ok,
               "palettes_utilisables": pl, "plans": {}}
    for L in (1, 2, 3):
        p0 = G.LAYERS[L]["pal0"]
        for half in (0, 1):
            buf = bytearray()
            for p in range(p0 + 16 * half, p0 + 16 * half + 16):
                for c in range(16): buf += bytes(int(v) for v in palette[p * 16 + c])
            buf += bytes([1, 0, 0x00, 0x0F])
            open(os.path.join(out, "palettes_%s_%02X-%02X.act" % (COURT[L], p0 + 16 * half, p0 + 16 * half + 15)), "wb").write(bytes(buf))
        pj = {}
        for p in range(p0, p0 + 32):
            vers = []; seen = set()
            for i in range(n):
                b = allpal[i, p * 16:(p + 1) * 16]; key = b.tobytes()
                if key not in seen:
                    seen.add(key); vers.append(["#%02X%02X%02X" % tuple(int(v) for v in cc) for cc in b])
            pj["$%02X" % p] = dict(utilisee=p in P[L]["used"], cps2_mots_ref=["%04X" % int(raw[p * 16 + c]) for c in range(16)],
                                   rgb_ref=["#%02X%02X%02X" % tuple(int(v) for v in palette[p * 16 + c]) for c in range(16)],
                                   nb_versions=len(vers), versions=vers if len(vers) > 1 else None)
        paljson["plans"][COURT[L]] = pj
    json.dump(paljson, open(os.path.join(out, "palettes.json"), "w"), indent=1, ensure_ascii=False, default=int)

    # ---------------- carte des tuiles ----------------
    carte = {"decor": titre, "decors_lies": ids, "canevas_psd": None, "canevas_decor": [CW, CH],
             "ecran_ref_dans_canevas": [SX0, SY0], "plan_reference": COURT[Lr],
             "note_canevas": "ecran 4:3 de l'image ref (butee gauche, Y nominal) en ecran_ref_dans_canevas ; butee droite = +course_x",
             "course_x": course_x, "course_y_reelle": [up_reel, dn_reel], "course_y_exportee": [up_tout, dn_tout],
             "format_case": "[code, palette(0-31 relative au plan), flipX, flipY, groupe_prio(attr>>7 &3), attr brut] ; null = jamais composee",
             "plans": {}}
    def grille(w, cells_):
        ts = w["ts"]; cols = w["WW"] // ts; rows = w["HH"] // ts
        grid = []
        for r in range(rows):
            line = []
            for c in range(cols):
                cell = cells_.get((w["X0"] // ts + c, w["Y0"] // ts + r))
                if cell is None: line.append(None); continue
                code, attr = R.main_entry(cell)
                line.append([code, attr & 0x1f, (attr >> 5) & 1, (attr >> 6) & 1, (attr >> 7) & 3, attr])
            grid.append(line)
        return grid
    for L in (1, 2, 3):
        w = W[L]; ts = w["ts"]; cols = w["WW"] // ts; rows = w["HH"] // ts
        grid = grille(w, w["cells"])
        colc = []
        for (cc, r), v in w["cells_col"].items():
            if (cc, r) not in w["cells"] and len(v) == 1:
                code, attr = next(iter(v))
                colc.append([cc - w["X0"] // ts, r - w["Y0"] // ts, code, attr])
        anim = [{"case": [int(cc - w["X0"] // ts), int(r - w["Y0"] // ts)],
                 "variantes": [{"code": k[0], "attr": k[1], "images": v} for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])]}
                for (cc, r), cnt in P[L]["anim"].items()]
        carte["plans"][COURT[L]] = dict(
            nom=P[L]["nom"], taille_tuile=ts, bases_vram=["$%06X" % (0x900000 + b) for b in w["bases"]],
            monde_tilemap_px=dict(x0=w["X0"], y0=w["Y0"], largeur=w["WW"], hauteur=w["HH"]),
            colonnes=cols, lignes=rows, origine_dans_canevas_psd=P[L]["origine"],
            code_physique="(0x20000 + (code << s) & 0x1FFFF) >> s, s = 0/1/3 (scroll1/2/3) ; scroll3 : code & 0x3FFF ; octets = code_phys * %d dans la region gfx MAME" % G.LAYERS[L]["tbytes"],
            parallaxe=info[L]["parallaxe"], rowscroll=info[L]["rowscroll"], defilement_x=list(info[L]["sx"]),
            defilement_y_reel=list(info[L]["sy_reel"]), defilement_y_exporte=list(info[L]["sy_tout"]),
            tuiles_animees=anim, palettes_animees=[{"pal": "$%02X" % p, "versions": v} for p, v in pal_var[L]],
            zones_a_combler=zones[COURT[L]], cases=grid,
            phases_defilement=[dict(phase=k + 1, decalage_tilemap_px=list(P[L]["phs"][k]["delta"]), images=P[L]["phs"][k]["n"],
                                    cases=grille(w, P[L]["phs"][k]["cells"])) for k in range(1, len(P[L]["phs"]))],
            cases_colonne_composee=colc)
    resume = dict(id=ID, lies=ids, titre=titre, persos=[PERSO[int(i, 16) // 2] for i in ids], canevas=[CW, CH],
                  ecran_ref=[SX0, SY0], ref=ref,
                  course_x=course_x, course_y_reelle=[up_reel, dn_reel], course_y_exportee=[up_tout, dn_tout], camtop=camtop,
                  ordre=[COURT[L] for L in lorder], parallaxe={COURT[L]: info[L]["parallaxe"] for L in (1, 2, 3)},
                  rowscroll=info[2]["rowscroll"],
                  monde={COURT[L]: [W[L]["WW"], W[L]["HH"]] for L in (1, 2, 3)},
                  zones=zones, decor_arrete=arret_info, plan_du_fond=COURT[back],
                  anim_defilement={COURT[L]: len(P[L]["phs"]) for L in (1, 2, 3)}, controle=ctrl, palettes_libres=pl,
                  anim_tuiles={COURT[L]: len(P[L]["anim"]) for L in (1, 2, 3)},
                  anim_palettes={COURT[L]: ["$%02X" % p for p, _ in pal_var[L]] for L in (1, 2, 3)},
                  hors_course_incoherent={COURT[L]: P[L]["inco"] for L in (1, 2, 3)}, conv_palette=conv_ok, images_flash=flashes)
    json.dump(carte, open(os.path.join(out, "carte_tuiles.json"), "w"), ensure_ascii=False, default=int)
    json.dump(resume, open(os.path.join(out, "controle.json"), "w"), indent=1, ensure_ascii=False, default=int)
    # compresser les calques tout de suite (memoire)
    def comp(items):
        for it in items:
            if isinstance(it, Group): comp(it.children)
            else: compress_layer(it, drop=True)
    comp(grp.children)
    return grp, resume, flat


def _work(g):
    os.nice(19) if hasattr(os, "nice") else None
    r = process(g)
    gc.collect()
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decors", default=None, help="ids principaux (defaut : tous ceux qui ont un releve)")
    ap.add_argument("--psd", default=OUT + "/decors_sfa3.psd")
    a = ap.parse_args()
    G.load_gfx()
    gs = groupes_decors()
    if a.decors: gs = [g for g in gs if g[0] in a.decors.split(",")]
    gs = [g for g in gs if os.path.exists(D + "/work/monde_%s.pkl" % g[0])]
    groups, resumes, flats = [], [], []
    import multiprocessing as mp
    with mp.get_context("fork").Pool(int(os.environ.get("NPROC", "4"))) as pool:
        results = pool.map(_work, gs, chunksize=1)
    for g, (grp, res, flat) in zip(gs, results):
        print("== decor", g, flush=True)
        groups.append(grp); resumes.append(res); flats.append(flat)
        c = res["controle"]
        print("   canevas %s course X %d Y reel -%d/+%d exporte -%d/+%d ; controle s1/s2/s3/composite hors anim : %s"
              % (res["canevas"], res["course_x"], *res["course_y_reelle"], *res["course_y_exportee"],
                 [c[k]["hors_cases_animees"] for k in ("scroll1", "scroll2", "scroll3", "composite_3_plans")]), flush=True)
        gc.collect()
    CW = max(r["canevas"][0] for r in resumes); CH = max(r["canevas"][1] for r in resumes)
    for k, (g, r) in enumerate(zip(groups, resumes)):
        g.hidden = k > 0                       # seul le 1er decor visible ; les autres : cocher l'oeil du groupe
        p = os.path.join(OUT, "decors", "decor%s" % r["id"], "carte_tuiles.json")
        cj = json.load(open(p)); cj["canevas_psd"] = [CW, CH]; json.dump(cj, open(p, "w"), ensure_ascii=False)
    merged = np.zeros((CH, CW, 4), np.uint8)
    f0 = flats[0]; merged[:f0.shape[0], :f0.shape[1]] = f0
    write_psd(a.psd, CW, CH, groups, merged=merged)
    json.dump(resumes, open(os.path.join(OUT, "decors", "recap.json"), "w"), indent=1, ensure_ascii=False, default=int)
    # planche contact
    th = []
    for r, f in zip(resumes, flats):
        im = Image.fromarray(f).convert("RGB")
        z = Image.open(os.path.join(OUT, "decors", "decor%s" % r["id"], "apercu_zones.png")).convert("RGB")
        th.append((r, im, z))
    TW = 448
    rows = []
    for r, im, z in th:
        sc = TW / im.width
        a1 = im.resize((TW, max(1, int(im.height * sc)))); a2 = z.resize((TW, max(1, int(z.height * sc))))
        h = max(a1.height, a2.height) + 18
        row = Image.new("RGB", (2 * TW + 8, h), (20, 20, 20)); row.paste(a1, (0, 18)); row.paste(a2, (TW + 8, 18))
        ImageDraw.Draw(row).text((4, 2), r["titre"] + "  —  %dx%d, course X %d, Y -%d/+%d" % (
            r["canevas"][0], r["canevas"][1], r["course_x"], *r["course_y_reelle"]), fill=(255, 255, 0), font=FONT)
        rows.append(row)
    Hh = sum(x.height for x in rows)
    sheet = Image.new("RGB", (2 * TW + 8, Hh), (0, 0, 0)); y = 0
    for x in rows: sheet.paste(x, (0, y)); y += x.height
    sheet.save(os.path.join(OUT, "decors", "planche_decors.png"))
    print("OK", a.psd, CW, CH, len(groups), "groupes")


if __name__ == "__main__":
    main()
