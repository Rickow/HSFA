"""(agent_integration_max) HUD et APERÇU DE SÉLECTION des persos MAX (fichiers de la session MAX, lecture seule) :
  * noms de la barre de vie (converti/noms/hud_noms.bin + hud_noms.json : 4 tuiles 64×16 par perso, codes locaux 0/4/8/12) ;
  * visages de la barre de vie (converti/plXX/hud.bin + hud.json : J1/J2, objets [code local, (w-1)<<8 | r, x, y]) ;
  * petit sprite d'aperçu de la sélection (converti/plXX/apercu/ : tuiles.bin, apercu.s = APERCU_xx, pas de 20 o +
    frames de type 2 AP_xx_n + positions APP_xx_n, disposition ARCADE).
Tuiles : un fichier graphique PROPRE (prep/max_plus_gfx.bin) chargé derrière max_portraits_gfx.bin
(HSFA_GFX ...@2E45000 : tuiles globales G_PLUS = $5C8A0 + k).
  - noms et visages : emplacement 1 (plan2 prolongé, comme les cartouches) : code = PB1 + (g - G0) - $1C00 ;
    un visage = UN objet w × h (code + x + 16·y) -> tuiles rangées par rangées de 16 ;
  - aperçu : emplacement 0 (banque commune e351 : $1A(A6) = 0 à va 0x18A740) : codes locaux L0 + j ajoutés à
    banques_hx/f351.bin par integre_max (local L0 + j -> global G + j).
Sorties : prep/max_plus_gfx.bin, prep/max_plus.json, et les lignes vasm (DONNÉES, disposition IMAGE) de l'aperçu."""
import os, re, json, sys

import sys as _sy; _sy.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "untranspile"))
import max_cache as MC
CV = MC.CV
G0, PB1 = MC.G0, MC.PB1
G_PLUS = MC.G_PLUS                         # = 0x2E45000 / 128 : juste derrière max_portraits_gfx.bin (2100 tuiles)
L0_APERCU = 0x7000                       # premiers codes locaux libres de la banque commune (f351 : $6C60 entrées)
def code_plan2(g): return PB1 + (g - G0) - 0x1C00

CONVERT_MAX = os.path.expanduser("~/CLAUDE CODE/sfa3max-psp-widescreen/work/re/convert")   # lecture seule
def tuiles(f):
    """tuiles brutes CPS2 (16 rangées x 8 octets, quartet bas = pixel de gauche) -> format interne de MAME (gfx_fork.encode
    de la session MAX, comme portraits_fork.py) : ce que le fork charge par HSFA_GFX"""
    import numpy as np
    sys.path.insert(0, CONVERT_MAX)
    from gfx_fork import encode
    b = np.fromfile(f, np.uint8).reshape(-1, 16, 8)
    px = np.empty((len(b), 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
    return [bytes(encode(t)) for t in px]
def tuile_vide():
    import numpy as np
    sys.path.insert(0, CONVERT_MAX)
    from gfx_fork import encode
    return bytes(encode(np.full((16, 16), 15, np.uint8)))

def prepare(out, persos, conv_dir):
    """persos : [(id, pl)] actifs ; conv_dir : dossier conv/ (convertit_frames importable)"""
    sys.path.insert(0, conv_dir)
    import convertit_frames as CF
    VIDE = tuile_vide()                  # tuile transparente (couleur 15)
    gfx = []                             # tuiles du fichier, index k -> global G_PLUS + k
    def pose(k, t):
        while len(gfx) <= k: gfx.append(VIDE)
        gfx[k] = t
    J = {"G_PLUS": G_PLUS, "noms": {}, "visages": {}, "apercu": {}}
    # 1. noms de la barre de vie : 4 tuiles consécutives par perso
    HN = json.load(open(CV + "noms/hud_noms.json")); TN = tuiles(CV + "noms/hud_noms.bin")
    for pid, pl in persos:
        n = HN[pl]; c = n["code_local"]; k = len(gfx)
        if k % 16 > 12: k = (k + 15) & ~15                  # 4 tuiles sans franchir une ligne de 16
        for j in range(4): pose(k + j, TN[c + j])
        J["noms"][pid] = dict(code=code_plan2(G_PLUS + k), attribut=n["attribut"], x_J1=n["x_J1"], x_J2=n["x_J2"], y=n["y"])
    # 2. visages : un objet w × h par joueur, rangées de 16
    for pid, pl in persos:
        H = json.load(open(CV + "%s/hud.json" % pl)); TH = tuiles(CV + "%s/hud.bin" % pl)
        J["visages"][pid] = {}
        for jx in ("J1", "J2"):
            w, h = H[jx]["taille"][0] // 16, H[jx]["taille"][1] // 16
            k = (len(gfx) + 15) & ~15
            for code, at, x, y in H[jx]["objs"]:
                ow = ((at >> 8) & 0xF) + 1
                for t in range(ow): pose(k + x // 16 + t + 16 * (y // 16), TH[code + t])
            pose(k + 16 * h - 1, gfx[k + 16 * h - 1] if k + 16 * h - 1 < len(gfx) else VIDE)
            J["visages"][pid][jx] = dict(code=code_plan2(G_PLUS + k), w=w, h=h, r=H[jx]["objs"][0][1] & 0x1F)
    # 3. aperçu : tuiles consécutives, codes locaux L0 + ...
    L = []; loc = L0_APERCU
    for pid, pl in persos:
        A = CV + "%s/apercu/" % pl
        TA = tuiles(A + "tuiles.bin"); k = (len(gfx) + 15) & ~15     # codes locaux alignés sur 16 (objets de largeur w)
        loc = (loc + 15) & ~15
        for j, t in enumerate(TA): pose(k + j, t)
        J["apercu"][pid] = dict(local=loc, g=G_PLUS + k, n=len(TA))
        L += source_apercu(out, pid, A + "apercu.s", loc, CF)
        loc += len(TA)
    assert len(gfx) < 0x2000 - 2100, "plan2 prolongé : %d tuiles" % len(gfx)
    # 4. BIO (écran d'histoire, session MAX : converti/plXX/bio/) : tuiles neuves rangées à la suite ; table du fichier
    #    (format banques_hx/f<N>.bin) : 0x40000000 | code local -> tuile globale G_PLUS + k
    import struct as _st
    J["bio"] = {}
    for pid, pl in persos:
        B = CV + "%s/bio/" % pl
        if not os.path.exists(B + "anim_bio.bin"): continue
        TB = tuiles(B + "tuiles.bin")
        tab = list(_st.unpack("<%dI" % (os.path.getsize(B + "table_tuiles.bin") // 4), open(B + "table_tuiles.bin", "rb").read()))
        k0 = len(gfx); place = {}
        for i, v in enumerate(tab):
            if v != 0xFFFFFFFF and v & 0x40000000:
                L_ = v & 0xFFFFFF
                if L_ not in place: place[L_] = len(gfx); pose(len(gfx), TB[L_])
                tab[i] = G_PLUS + place[L_]
        open(os.path.join(out, "bio_%s_hx.bin" % pid), "wb").write(_st.pack("<%dI" % len(tab), *tab))
        J["bio"][pid] = dict(anim=B + "anim_bio.bin", table="bio_%s_hx.bin" % pid, tuiles=len(place), g=G_PLUS + k0)
    # 5. DÉCORS DE FIN (palier 4, session MAX : converti/plXX/fin/decor/tuiles.bin, codes LOCAUX 0.. de la banque gfx de
    #    fin, emplacement 4) : tuiles à la suite ; table du fichier de fin MAX (banques_hx/f<N>.bin) : local k -> G_PLUS + …
    J["decor"] = {}
    for pid, pl in persos:
        f = CV + "%s/fin/decor/tuiles.bin" % pl
        if not os.path.exists(f): continue
        TD = tuiles(f); k0 = len(gfx)
        for j, t in enumerate(TD): pose(k0 + j, t)
        tab = [G_PLUS + k0 + j for j in range(len(TD))]
        open(os.path.join(out, "decor_%s_hx.bin" % pid), "wb").write(_st.pack("<%dI" % len(tab), *tab))
        J["decor"][pid] = dict(table="decor_%s_hx.bin" % pid, tuiles=len(TD), g=G_PLUS + k0)
    assert 128 * len(gfx) <= MC.PLUS_MAX, "max_plus_gfx déborde sur hsfa_plans"
    open(os.path.join(out, "max_plus_gfx.bin"), "wb").write(b"".join(gfx))
    J["tuiles"] = len(gfx); J["L_fin"] = loc
    json.dump(J, open(os.path.join(out, "max_plus.json"), "w"), indent=1)
    return L

def source_apercu(out, pid, f, loc, CF):
    """apercu.s (arcade) -> lignes vasm disposition IMAGE : pas (convertit_anims, genre « pas »), frames et positions
    (convertit_frames : longs à moitiés échangées), codes des frames + loc ; structure APS_<id> (3 décalages, ismes)"""
    s = open(f).read()
    xx = re.search(r"^APERCU_(\w\w):", s, re.M).group(1)
    s = re.sub(r"^APERCU_\w\w:\s*\n", "", s, flags=re.M)
    s = re.sub(r"\bAP_PAS_%s_(\d+)\b" % xx, lambda m: "P%s_AP%s" % (xx, m.group(1)), s)
    i = re.search(r"^AP_%s_\d+:" % xx, s, re.M).start()
    pas, fr = s[:i], s[i:]
    pas = re.sub(r"^\s*cnop\s.*\n", "", pas, flags=re.M)        # alignement remis par l'assemblage (pas de 20 / 24 o)
    # codes des frames : lignes « dc.w code, attr » qui suivent « dc.l APP_.. » dans un bloc AP_xx_n
    o = []; dans = False
    for l in fr.split("\n"):
        if re.match(r"^AP_%s_\d+:" % xx, l): dans = False
        if re.match(r"^\s*dc\.l\s+APP_", l): dans = True; o.append(l); continue
        if re.match(r"^APP_", l): dans = False
        m = re.match(r"^(\s*dc\.w\s+)\$([0-9A-Fa-f]+),\s*(\$[0-9A-Fa-f]+)(.*)$", l)
        if dans and m: l = "%s$%04X, %s%s" % (m.group(1), int(m.group(2), 16) + loc, m.group(3), m.group(4))
        o.append(l)
    fr = "\n".join(o)
    d = os.path.join(out, "apercu"); os.makedirs(d, exist_ok=True)
    pa, fa = os.path.join(d, "pas_%s.s" % pid), os.path.join(d, "frames_%s.s" % pid)
    open(pa + ".src", "w").write(pas); open(fa + ".src", "w").write(fr)
    j = []; st = CF.convertit_anims(pa + ".src", pa, j)
    assert st["NON RÉSOLU"] == 0 and st["pas"] > 0, "aperçu %s : %s %s" % (pid, st, j)
    CF.convertit_frames(fa + ".src", fa)
    return ["        cnop    0,4", "; ---- aperçu de sélection $%s (session MAX : apercu.s, %d pas)" % (pid, st["pas"]),
            "APS_%s:" % pid] + ["        dc.w    P%s_AP0-APS_%s" % (xx, pid)] * 3 + ["        cnop    0,4",
            open(pa).read(), "        cnop    0,4", open(fa).read()]
