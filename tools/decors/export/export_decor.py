#!/usr/bin/env python3
"""EXPORT D'UN DECOR : images monde par plan -> PSD a calques (un groupe par decor) + PNG + ACT + JSON.

Entrees : work/monde.pkl (build_world.py), rec2/full.rec (releve par image), rec2/scr_{1,2,3}.bin
          (captures MAME des plans isoles, pour le controle), gfx/gfx_region.bin.
Sorties : out/decors_sfa3.psd, out/<decor>/... (PNG, ACT, JSON), out/<decor>/controle.json
"""
import sys, os, json, pickle, collections
sys.path.insert(0, "<workspace>/work/decors_ws/py")
import numpy as np
from PIL import Image, ImageDraw
from recio import read_rec, read_scr
import cpsgfx as G
import world_render as R
from psdwriter import Layer, Group, write_psd, composite
from PIL import ImageFont
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except Exception:
    FONT = None

D = "<workspace>/work/decors_ws"
DECOR = dict(id="0C", slug="decor0C_temple_cloche",
             titre="SFA3 — décor $0C (Sodom) — temple à cloche",
             rec=D + "/rec2/full.rec", scr=D + "/rec2/scr_%d.bin", monde=D + "/work/monde.pkl")
NOMS = {   # nom explicite par plan (profondeur d'apres le layer control CPS-B $1E0E : bas -> haut = 2, 3, 1)
    2: "fond (scroll2 16 px) — façades, ville, sol",
    3: "plan médian (scroll3 32 px) — cloche, arbre, balustrade, bannières",
    1: "avant-plan (scroll1 8 px) — lanternes, guirlandes, statues",
}
COURT = {1: "scroll1", 2: "scroll2", 3: "scroll3"}
EXTRA = (32, 64)     # 448 = 384 + 2x32 (core FBNeo-WS) ; 512 = 384 + 2x64 (option)


def cps_rgb(w):
    b = 0x0f + ((w >> 12) << 1)
    return tuple(min(255, ((w >> s) & 15) * 0x11 * b // 0x2d) for s in (8, 4, 0))


def main():
    G.load_gfx()
    W = pickle.load(open(DECOR["monde"], "rb"))
    frs = read_rec(DECOR["rec"])
    regs, data = frs[:-1], frs[1:]
    n = len(regs)
    out = os.path.join(D, "out", DECOR["slug"]); os.makedirs(out, exist_ok=True)

    # ---------------- image de reference (palette) et alignement ----------------
    s3 = W[3]["scroll_x"]
    sy_ref = W[3]["scroll_y"]
    nominal_y = collections.Counter(sy_ref).most_common(1)[0][0]
    ref = min(range(n), key=lambda i: (s3[i], sy_ref[i] != nominal_y))         # extremite gauche, Y nominal
    pal_ref_i = n - 1                                                            # palette : derniere image
    palette = data[pal_ref_i].pal
    MX = max(EXTRA)
    info = {}
    for L in (1, 2, 3):
        w = W[L]
        sx, sy = np.array(w["scroll_x"]), np.array(w["scroll_y"])
        # parallaxe : pente du defilement de ce plan vs scroll3
        k = np.polyfit(np.array(s3, float), sx.astype(float), 1)[0] if np.ptp(s3) else 1.0
        info[L] = dict(parallaxe=round(float(k), 4), sx_min=int(sx.min()), sx_max=int(sx.max()),
                       sy_min=int(sy.min()), sy_max=int(sy.max()))
    course_x = info[3]["sx_max"] - info[3]["sx_min"]
    course_y = info[3]["sy_max"] - info[3]["sy_min"]
    CW = MX + course_x + 384 + MX
    CH = course_y + 224
    print("canevas", CW, "x", CH, "course X", course_x, "course Y", course_y, "ref", ref)

    def to_canvas(L, arr, fill=0):
        """tableau monde du plan L -> canevas (meme ecran que l'image ref)"""
        w = W[L]
        rsr = int(np.median(w["rs"][ref]))            # rowscroll (scroll2) : valeur dominante de l'image ref
        ox = w["X0"] - (w["scroll_x"][ref] + 64 + rsr) + MX
        oy = w["Y0"] - (w["scroll_y"][ref] + 16) + (w["scroll_y"][ref] - min(w["scroll_y"]))
        shape = (CH, CW) + arr.shape[2:]
        c = np.full(shape, fill, arr.dtype)
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(CH, oy + arr.shape[0]), min(CW, ox + arr.shape[1])
        c[ys:ye, xs:xe] = arr[ys - oy:ye - oy, xs - ox:xe - ox]
        return c, ox, oy

    # ---------------- par plan : pens, connu, a combler, VRAM hors course, animations ----------------
    planes = {}
    pal_var = {}
    allpal = np.array([d.pal for d in data])                                    # (n, 0xC00, 3)
    for L in (1, 2, 3):
        w = W[L]; ts = w["ts"]
        pen, pl, known, srcm = R.world_pens(W, L, with_src=True)
        # zones geometriques : course camera = rectangle X x Y (toute combinaison possible en jeu)
        sxs, sys_ = w["scroll_x"], w["scroll_y"]
        req = {e: np.zeros((w["HH"], w["WW"]), bool) for e in (0,) + EXTRA}
        for y in range(224):
            xs_ = [sxs[i] + 64 + w["rs"][i][y] for i in range(n)]
            lo, hi = min(xs_) - w["X0"], max(xs_) + 384 - w["X0"]
            for syv in range(min(sys_), max(sys_) + 1):
                wy = syv + 16 + y - w["Y0"]
                for e in req: req[e][wy, max(0, lo - e):hi + e] = True
        trous = req[0] & ~known
        rgba = R.to_rgba(pen, pl, palette, known)
        # tuiles animees (plusieurs entrees pour une meme case monde)
        anim = {k: v for k, v in w["cells"].items() if len(v) > 1}
        # palettes animees du plan
        p0 = G.LAYERS[L]["pal0"]
        varies = []
        for p in range(p0, p0 + 32):
            blk = allpal[:, p * 16:(p + 1) * 16]
            nv = len({b.tobytes() for b in blk})
            if nv > 1:
                varies.append((p, nv))
        used_pals = sorted({p0 + (main[1] & 0x1f) for main in (R.main_entry(c) for c in w["cells"].values())})
        pal_var[L] = [(p, nv) for p, nv in varies if p in used_pals]
        # contenu VRAM hors course : ce qu'afficherait un rendu elargi naif (le core 448 actuel) a cet endroit
        hors = np.zeros((w["HH"], w["WW"], 4), np.uint8)
        hors_inco = np.zeros((w["HH"], w["WW"]), bool)
        hors_set = np.zeros((w["HH"], w["WW"]), bool)
        unk = ~known
        sxm, sxM = min(w["scroll_x"]), max(w["scroll_x"])
        for i in range(n):
            if not (w["scroll_x"][i] - sxm < MX or sxM - w["scroll_x"][i] < MX):
                continue
            f = G.mix(regs[i], data[i])
            pens_tm, pal_tm = G.tilemap_pens(f, L)
            Wt = G.TM * ts
            for y in range(224):
                wy = w["scroll_y"][i] + 16 + y - w["Y0"]
                rs = w["rs"][i][y]
                wx0 = w["scroll_x"][i] + 64 + rs - w["X0"]
                for xa, xb in ((wx0 - MX, wx0), (wx0 + 384, wx0 + 384 + MX)):
                    xs = np.arange(xa, xb)
                    ok = (xs >= 0) & (xs < w["WW"])
                    xs = xs[ok]
                    sel = unk[wy, xs]
                    xs = xs[sel]
                    if xs.size == 0: continue
                    tx = (xs + w["X0"]) % Wt; tyy = (wy + w["Y0"]) % Wt
                    pp = pens_tm[tyy, tx]; qq = pal_tm[tyy, tx].astype(np.int64)
                    col = np.concatenate([data[i].pal[qq * 16 + pp], np.where(pp != 15, 255, 0)[:, None]], 1).astype(np.uint8)
                    prev = hors[wy, xs]
                    diff = hors_set[wy, xs] & (prev != col).any(1)
                    hors_inco[wy, xs] |= diff
                    hors[wy, xs] = col
                    hors_set[wy, xs] = True
        planes[L] = dict(pen=pen, pl=pl, known=known, srcm=srcm, req=req, trous=trous, rgba=rgba, anim=anim, hors=hors,
                         hors_inco=hors_inco, used_pals=used_pals)
        print("plan", L, "palettes utilisees", [hex(p) for p in used_pals], "animees", pal_var[L],
              "tuiles animees", len(anim), "hors-course incoherent (px)", int(hors_inco.sum()),
              "TROUS dans la course 4:3 (px)", int(trous.sum()), "px completes colonne composee", int(((srcm == 2) & req[0]).sum()))

    # ---------------- CONTROLE : ecran recompose depuis l'image monde vs capture MAME du plan isole ----------------
    ctrl = {}
    for L in (1, 2, 3):
        w = W[L]; P = planes[L]
        scr = read_scr(DECOR["scr"] % L)
        animmask = np.zeros_like(P["known"])
        for (cc, r) in P["anim"]:
            animmask[r * w["ts"] - w["Y0"]:(r + 1) * w["ts"] - w["Y0"], cc * w["ts"] - w["X0"]:(cc + 1) * w["ts"] - w["X0"]] = True
        tot = tot_anim = nimg = 0; worst = []
        for t in sorted(scr):
            if t < 8: continue                       # 1res images apres chargement : liste de sprites de l'etat
            i = t - 1                                 # image rendue t = regs frs[t-1] + donnees frs[t] = indice i
            wy = (w["scroll_y"][i] + 16 + np.arange(224) - w["Y0"])[:, None]
            rs = np.array(w["rs"][i])[:, None]
            wx = w["scroll_x"][i] + 64 + rs + np.arange(384)[None, :] - w["X0"]
            pp = P["pen"][wy, wx]; qq = P["pl"][wy, wx]
            img = np.where((pp != 15)[:, :, None], data[i].pal[qq * 16 + pp], 0).astype(np.uint8)
            d = (img != scr[t]).any(2)
            da = d & animmask[wy, wx]
            tot += int(d.sum()); tot_anim += int(da.sum()); nimg += 1
            if d.sum(): worst.append((t, int(d.sum()), int(da.sum())))
        ctrl[L] = dict(images=nimg, px_differents=tot, dont_cases_animees=tot_anim,
                       hors_cases_animees=tot - tot_anim, pires=sorted(worst, key=lambda x: -x[1])[:5])
        print("CONTROLE plan", L, ctrl[L])

    # ---------------- calques ----------------
    def rgba_mask(mask, color):
        a = np.zeros(mask.shape + (4,), np.uint8); a[mask] = color; return a

    zones = {}
    plane_groups = []
    for L in (1, 3, 2):                               # haut -> bas (ordre de rendu inverse)
        w = W[L]; P = planes[L]
        img, ox, oy = to_canvas(L, P["rgba"])
        known_c, _, _ = to_canvas(L, P["known"], False)
        z = {}
        lays = []
        for e, col, hid in ((32, (255, 0, 0, 140), False), (64, (255, 140, 0, 110), True)):
            vis_c, _, _ = to_canvas(L, P["req"][e], False)
            zc = vis_c & ~known_c
            cols = np.nonzero(zc.any(0))[0]
            lft = cols[cols < CW // 2]; rgt = cols[cols >= CW // 2]
            z[e] = dict(px=int(zc.sum()),
                        gauche=[int(lft.min()), int(lft.max()) + 1] if lft.size else None,
                        droite=[int(rgt.min()), int(rgt.max()) + 1] if rgt.size else None,
                        lignes=[int(np.nonzero(zc.any(1))[0].min()), int(np.nonzero(zc.any(1))[0].max()) + 1] if zc.any() else None)
            lays.append(Layer("à combler %d×224 — %s (%s)" % (384 + 2 * e, COURT[L], "option" if hid else "cible core"),
                              rgba_mask(zc, col), hidden=hid))
        zones[L] = z
        # tuiles animees
        am = np.zeros((w["HH"], w["WW"], 4), np.uint8)
        for (cc, r) in P["anim"]:
            y0 = r * w["ts"] - w["Y0"]; x0 = cc * w["ts"] - w["X0"]
            am[y0:y0 + w["ts"], x0:x0 + w["ts"]] = (255, 255, 0, 70)
            am[y0, x0:x0 + w["ts"]] = am[y0 + w["ts"] - 1, x0:x0 + w["ts"]] = (255, 255, 0, 255)
            am[y0:y0 + w["ts"], x0] = am[y0:y0 + w["ts"], x0 + w["ts"] - 1] = (255, 255, 0, 255)
        # cases utilisant une palette animee
        animpals = {p for p, _ in pal_var[L]}
        if animpals:
            for (cc, r), cnt in w["cells"].items():
                code, attr = R.main_entry(cnt)
                if G.LAYERS[L]["pal0"] + (attr & 0x1f) in animpals:
                    y0 = r * w["ts"] - w["Y0"]; x0 = cc * w["ts"] - w["X0"]
                    sub = am[y0:y0 + w["ts"], x0:x0 + w["ts"]]
                    m = P["pen"][y0:y0 + w["ts"], x0:x0 + w["ts"]] != 15
                    sub[m & (sub[:, :, 3] == 0)] = (0, 200, 255, 90)
        amc, _, _ = to_canvas(L, am)
        lays.append(Layer("animations — %s : jaune = tuiles changées (%d cases), cyan = palettes cycliques %s"
                          % (COURT[L], len(P["anim"]), ",".join("$%02X" % p for p in sorted(animpals)) or "aucune"),
                          amc, hidden=True))
        nm = NOMS[L]
        if L == 2:
            nm += " — SOL EXPORTÉ À PLAT (rowscroll)"
        lays.append(Layer(nm, img))
        hc, _, _ = to_canvas(L, P["hors"])
        lays.append(Layer("VRAM hors course — %s : ce que montre un rendu élargi naïf (NON fiable, info)" % COURT[L],
                          hc, hidden=True))
        plane_groups.append(Group("%s" % nm, lays))
        planes[L]["canvas"] = img
        planes[L]["ox"], planes[L]["oy"] = ox, oy

    # repères
    gd = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(gd)
    ytop = info[3]["sy_max"] - info[3]["sy_min"] if False else (W[3]["scroll_y"][ref] - info[3]["sy_min"])
    for x0, lab in ((MX, "4:3 extrémité gauche"), (MX + course_x, "4:3 extrémité droite")):
        d.rectangle([x0, ytop, x0 + 383, ytop + 223], outline=(255, 255, 255, 255))
        d.text((x0 + 3, ytop + 3), lab, fill=(255, 255, 255, 255), font=FONT)
        d.rectangle([x0 - 32, ytop, x0 + 383 + 32, ytop + 223], outline=(0, 255, 255, 255))
        d.rectangle([x0 - 64, ytop, x0 + 383 + 64, ytop + 223], outline=(255, 0, 255, 200))
    d.text((MX + 3, ytop + 14), "cyan = 448x224 (core) ; magenta = 512x224 ; course Y : %d px" % course_y, fill=(0, 255, 255, 255), font=FONT)
    d.rectangle([MX, 0, MX + course_x + 383, CH - 1], outline=(255, 255, 0, 160))
    cadres = Layer("cadres 4:3 / 16:9 aux deux extrémités (blanc 384, cyan 448, magenta 512, jaune = course)", np.array(gd))
    grids = []
    for L in (1, 3, 2):
        g = np.zeros((CH, CW, 4), np.uint8); ts = W[L]["ts"]
        ox, oy = planes[L]["ox"], planes[L]["oy"]
        colr = {1: (255, 255, 255, 60), 2: (0, 255, 0, 90), 3: (255, 0, 255, 110)}[L]
        for x in range(ox % ts, CW, ts): g[:, x] = colr
        for y in range(oy % ts, CH, ts): g[y, :] = colr
        grids.append(Layer("grille %s (%d px)" % (COURT[L], ts), g, hidden=True))
    # notes (texte rendu en pixels)
    notes = [
        "DECOR $0C (Sodom) - releve MAME sfa3ud, balayage camera gauche->droite, %d images." % n,
        "Ordre CPS-B (layer control $%04X) bas->haut : scroll2, scroll3, scroll1 (+ sprites)." % frs[0].breg(0x26),
        "Parallaxe : scroll1/scroll2/scroll3 = %.2f/%.2f/%.2f x scroll3 (meme vitesse)." % (info[1]["parallaxe"], info[2]["parallaxe"], info[3]["parallaxe"]),
        "SOL : rowscroll scroll2 actif mais decalage CONSTANT (+$C0) sur toutes les lignes :",
        "  aucune perspective ; scroll2 exporte A PLAT, coordonnees tilemap.",
        "Pen 15 = transparent. Palette de reference : derniere image du releve.",
        "Animations : %d tuiles scroll2 changeantes ; palettes cycliques : %s." % (
            len(planes[2]["anim"]), "; ".join("%s %s" % (COURT[L], ",".join("$%02X(%d)" % pv for pv in pal_var[L])) for L in (1, 2, 3) if pal_var[L]) or "aucune"),
        "A COMBLER (rouge) = visible en 448x224 aux extremites, jamais vu en 4:3. Orange = 512.",
        "VRAM hors course (masque) = contenu de tilemap la ou le jeu ne compose rien : non fiable.",
    ]
    nimg = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); nd = ImageDraw.Draw(nimg)
    nd.rectangle([4, 4, CW - 5, 16 + 12 * len(notes)], fill=(0, 0, 0, 200))
    for k, t in enumerate(notes): nd.text((10, 8 + 12 * k), t, fill=(255, 255, 255, 255), font=FONT)
    note_layer = Layer("NOTES (lire) — sol à plat, animations, légende", np.array(nimg), hidden=True)
    # repere sprites : pixels ou la capture complete differe de la capture « plans seuls » (persos, HUD, objets-sprites)
    sfull = read_scr(D + "/rec2/scr_full.bin"); splans = read_scr(D + "/rec2/scr_0.bin")
    spr = np.zeros((CH, CW, 4), np.uint8)
    s3x, s3y = W[3]["scroll_x"], W[3]["scroll_y"]
    picks = []
    for target in (min(s3x), max(s3x)):
        cand = [t for t in sorted(sfull) if t >= 8 and s3x[t - 1] == target and s3y[t - 1] == nominal_y]
        if cand: picks.append(cand[len(cand) // 2])
    for t in picks:
        dm = (sfull[t] != splans[t]).any(2)
        ox_ = s3x[t - 1] - s3x[ref] + MX; oy_ = s3y[t - 1] - min(s3y)
        reg = spr[oy_:oy_ + 224, ox_:ox_ + 384]
        reg[dm] = np.concatenate([sfull[t], np.full((224, 384, 1), 255, np.uint8)], 2)[dm]
    sprite_layer = Layer("repère sprites (images %s : persos, HUD, objets de décor en sprites — hors export)"
                         % ",".join(map(str, picks)), spr, hidden=True)
    reperes = Group("repères (masqué)", [cadres, sprite_layer] + grids, hidden=True)
    decor_group = Group(DECOR["titre"], [note_layer, reperes] + plane_groups)
    items = [decor_group]
    psd = os.path.join(D, "out", "decors_sfa3.psd")
    write_psd(psd, CW, CH, items)

    # ---------------- apercus ----------------
    flat = np.zeros((CH, CW, 4), np.uint8); flat[:, :, 3] = 255
    def over(dst, src):
        a = src[:, :, 3:4].astype(np.float32) / 255
        dst[:, :, :3] = (src[:, :, :3] * a + dst[:, :, :3] * (1 - a)).astype(np.uint8)
    for L in (2, 3, 1): over(flat, planes[L]["canvas"])
    Image.fromarray(flat).save(os.path.join(out, "apercu_decor.png"))
    zon = flat.copy()
    for L in (2, 3, 1):
        for e, col in ((64, (255, 140, 0, 90)), (32, (255, 0, 0, 120))):
            vc, _, _ = to_canvas(L, planes[L]["req"][e], False); kc, _, _ = to_canvas(L, planes[L]["known"], False)
            over(zon, rgba_mask(vc & ~kc, col))
    over(zon, np.array(gd))
    Image.fromarray(zon).save(os.path.join(out, "apercu_zones.png"))
    Image.fromarray(composite(items, CW, CH)).save(os.path.join(out, "apercu_psd_fusion.png"))
    for L in (1, 2, 3):
        Image.fromarray(planes[L]["canvas"]).save(os.path.join(out, "plan_%s.png" % COURT[L]))

    # ---------------- palettes .act + JSON ----------------
    pbase = (data[pal_ref_i].reg(0x0a) << 8) & 0xfffc00 if False else (regs[pal_ref_i].reg(0x0a) << 8)
    po = (pbase - 0x900000) // 2
    raw = regs[pal_ref_i].vram[po:po + 0xC00]       # la palette MAME de l image t = RAM palette relevee a t-1 (copiee au vblank)
    conv_ok = sum(cps_rgb(int(raw[i])) == tuple(int(v) for v in palette[i]) for i in range(0x200, 0x800))
    paljson = {"palette_base_vram": "$%06X" % pbase, "conversion_rgb_ok": "%d/1536" % conv_ok, "plans": {}}
    for L in (1, 2, 3):
        p0 = G.LAYERS[L]["pal0"]
        for half in (0, 1):
            buf = bytearray()
            for p in range(p0 + 16 * half, p0 + 16 * half + 16):
                for c in range(16):
                    buf += bytes(int(v) for v in palette[p * 16 + c])
            buf += bytes([1, 0, 0x00, 0x0F])   # 256 couleurs ; index transparent = 15 (pen 15 du 1er bloc)
            open(os.path.join(out, "palettes_%s_%02X-%02X.act" % (COURT[L], p0 + 16 * half, p0 + 16 * half + 15)), "wb").write(bytes(buf))
        pj = {}
        for p in range(p0, p0 + 32):
            versions = []
            seen = {}
            for i in range(n):
                b = allpal[i, p * 16:(p + 1) * 16]
                key = b.tobytes()
                if key not in seen:
                    seen[key] = len(versions)
                    versions.append(["#%02X%02X%02X" % tuple(int(v) for v in c) for c in b])
            pj["$%02X" % p] = dict(utilisee=p in planes[L]["used_pals"],
                                   cps2_mots_ref=["%04X" % int(raw[p * 16 + c]) for c in range(16)],
                                   rgb_ref=["#%02X%02X%02X" % tuple(int(v) for v in palette[p * 16 + c]) for c in range(16)],
                                   nb_versions=len(versions), versions=versions if len(versions) > 1 else None)
        paljson["plans"][COURT[L]] = pj
    json.dump(paljson, open(os.path.join(out, "palettes.json"), "w"), indent=1, ensure_ascii=False, default=int)

    # ---------------- carte des tuiles JSON ----------------
    carte = {"decor": DECOR["titre"], "canevas_psd": [CW, CH],
             "format_case": "[code, palette(0-31 relative au plan), flipX, flipY, groupe_prio(attr>>7 &3), attr brut] ; null = jamais composee (a combler)",
             "plans": {}}
    for L in (1, 2, 3):
        w = W[L]; ts = w["ts"]
        cols = w["WW"] // ts; rows = w["HH"] // ts
        grid = []
        for r in range(rows):
            line = []
            for c in range(cols):
                cell = w["cells"].get((w["X0"] // ts + c, w["Y0"] // ts + r))
                if cell is None: line.append(None); continue
                code, attr = R.main_entry(cell)
                line.append([code, attr & 0x1f, (attr >> 5) & 1, (attr >> 6) & 1, (attr >> 7) & 3, attr])
            grid.append(line)
        anim = [{"case": [cc - w["X0"] // ts, r - w["Y0"] // ts],
                 "variantes": [{"code": k[0], "attr": k[1], "images": v} for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])]}
                for (cc, r), cnt in planes[L]["anim"].items()]
        carte["plans"][COURT[L]] = dict(
            nom=NOMS[L], taille_tuile=ts, base_vram="$%06X" % w["base"],
            monde_tilemap_px=dict(x0=w["X0"], y0=w["Y0"], largeur=w["WW"], hauteur=w["HH"]),
            colonnes=cols, lignes=rows, origine_dans_canevas_psd=[planes[L]["ox"], planes[L]["oy"]],
            code_physique="(0x20000 + (code << s) & 0x1FFFF) >> s, s = 0/1/3 (scroll1/2/3) ; scroll3 : code & 0x3FFF ; octets = code_phys * %d dans la region gfx MAME" % G.LAYERS[L]["tbytes"],
            parallaxe=info[L]["parallaxe"], defilement_x=[info[L]["sx_min"], info[L]["sx_max"]],
            defilement_y=[info[L]["sy_min"], info[L]["sy_max"]],
            tuiles_animees=anim, palettes_animees=[{"pal": "$%02X" % p, "versions": v} for p, v in pal_var[L]],
            zones_a_combler=zones[L], cases=grid)
    json.dump(carte, open(os.path.join(out, "carte_tuiles.json"), "w"), ensure_ascii=False, default=int)
    json.dump(dict(controle=ctrl, zones=zones, info=info, canevas=[CW, CH], course=[course_x, course_y], ref=ref,
                   pal_var={COURT[L]: pal_var[L] for L in (1, 2, 3)}),
              open(os.path.join(out, "controle.json"), "w"), indent=1, ensure_ascii=False, default=int)
    print("ZONES", json.dumps(zones))
    print("OK", psd)


if __name__ == "__main__":
    main()
