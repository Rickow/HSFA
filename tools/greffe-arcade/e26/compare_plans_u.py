#!/usr/bin/env python3
"""(e26) CONTROLE PIXEL A PIXEL d'un decor d'Upper en combat dans ro9a contre Upper (oracle), d'apres
github/tools/decors/sfa2/compare_plans.py (meme rendu : decors_sfa2/export/py/cpsgfx.py, releves FRM2 de lua/rec_plans.lua).

Les deux bancs servent les plans d'Upper (work/mame_ro5/hsfa_plans.bin) : Upper a l'adresse $3000000 (bases 300/340/3A0),
ro9a a $4000000 (bases 400/440/4A0). Le code de tuile d'un plan L se lit donc dans ce fichier au decalage
(base_L - base0) x 64 Ko + code x taille (base0 = 300 ou 400 ; bases relevees par image dans REC.txt).
  - scroll2 / scroll3 : tilemaps ENTIERES (VRAM + palette MAME) comparees au pixel ;
  - scroll1 : contenu de la VRAM (codes + attributs) compare ; rendu avec les bases d'Upper ;
  - ecran : composite des 3 plans (ordre CPS-B, rowscroll) quand les defilements sont egaux.
Usage : compare_plans_u.py <upper.rec> <ro9a.rec> [dossier images]"""
import sys, os, numpy as np
sys.path.insert(0, "<workspace>/work/decors_sfa2/export/py")
import recio, cpsgfx as G
from PIL import Image
PLANS = "<workspace>/work/mame_ro5/hsfa_plans.bin"

def bases(rec):
    d = {}
    for l in open(rec + ".txt"):
        p = l.split(); d[int(p[0])] = dict(b=[int(x, 16) for x in p[2:5]], decor=int(p[6], 16), drapeau=int(p[8], 16), couches=int(p[10], 16))
    return d

def regle(base0, b, s1_upper=False):
    def phys(layer, code):
        bl = b[layer - 1] & 0x7FF                      # adresse de tuile masquee par le coeur ($7FFFFFF : $4400 = $0400, $8300 = $0300)
        if layer == 1 and s1_upper: bl = base0          # scroll1 rendu comme dans Upper (base des plans d'Upper)
        if layer == 3: code &= 0x3fff
        return ((bl - base0) << 16) // G.LAYERS[layer]["tbytes"] + code
    return phys

def tilemap(f, L, phys):
    G.phys_code = phys; G.tile.cache_clear()
    pen, pal = G.tilemap_pens(f, L)
    return f.pal[pal.astype(np.int64) * 16 + pen], pen != 15, (pen, pal)

def entrees(f, L):
    base = (f.reg(G.LAYERS[L]["base"]) << 8) & 0xffc000; o0 = (base - 0x900000) // 2
    return f.vram[o0:o0 + 2 * 64 * 64]

def main():
    ru, rh = sys.argv[1:3]; dimg = sys.argv[3] if len(sys.argv) > 3 else None
    G.GFX = np.fromfile(PLANS, np.uint8)
    LU, LH = recio.read_rec(ru), recio.read_rec(rh)       # releves apparies dans l'ordre (REC_DECOR : meme rang en combat)
    BU, BH = bases(ru), bases(rh)
    tot = 0
    paires = list(zip(LU, LH))
    if os.environ.get("PAR_DECOR") == "1":                 # releves REC_TOUS : un par decor, apparies par decor
        du = {BU[f.t]['decor']: f for f in LU}
        paires = [(du[BH[f.t]['decor']], f) for f in LH if BH[f.t]['decor'] in du]
        print("decors ro9a sans releve Upper : %s" % ' '.join('%02X' % BH[f.t]['decor'] for f in LH if BH[f.t]['decor'] not in du))
    for fu, fh in paires:
        tu, t = fu.t, fh.t
        print("images %d (Upper) / %d (ro9a) : Upper bases %s decor %04X | ro9a bases %s decor %04X drapeau %d couches %04X/%04X" % (
            tu, t, ' '.join('%03X' % x for x in BU[tu]['b']), BU[tu]['decor'], ' '.join('%03X' % x for x in BH[t]['b']),
            BH[t]['decor'], BH[t]['drapeau'], BU[tu]['couches'], BH[t]['couches']))
        pu, ph = regle(0x300, BU[tu]['b']), regle(0x400, BH[t]['b'])
        for L in (2, 3):
            a, ma, _ = tilemap(fu, L, pu); b, mb, _ = tilemap(fh, L, ph)
            dm = ma != mb; dc = (ma & mb) & (a != b).any(2); n = int(dm.sum() + dc.sum()); tot += n
            print("  scroll%d tilemap entiere %dx%d : %d px differents (transparence %d, couleur %d) sur %d opaques ; VRAM identique : %s" % (
                L, a.shape[1], a.shape[0], n, int(dm.sum()), int(dc.sum()), int(ma.sum()), bool((entrees(fu, L) == entrees(fh, L)).all())))
            if dimg:
                os.makedirs(dimg, exist_ok=True)
                Image.fromarray(np.where(ma[..., None], a, 0).astype(np.uint8)).save(os.path.join(dimg, "s%d_upper_%d.png" % (L, t)))
                Image.fromarray(np.where(mb[..., None], b, 0).astype(np.uint8)).save(os.path.join(dimg, "s%d_ro9a_%d.png" % (L, t)))
        eu, eh = entrees(fu, 1), entrees(fh, 1)
        print("  scroll1 VRAM (codes + attributs, 4096 cases) : %d cases differentes ; palettes s1 (pens $200-$3FF) identiques : %s" % (
            int(((eu[0::2] != eh[0::2]) | (eu[1::2] != eh[1::2])).sum()), bool((fu.pal[0x200:0x400] == fh.pal[0x200:0x400]).all())))
        a, ma, _ = tilemap(fu, 1, pu); b, mb, _ = tilemap(fh, 1, regle(0x400, BH[t]['b'], s1_upper=True))
        print("  scroll1 rendu aux bases d'Upper (ce que donnerait le futur patch 0017) : %d px differents" % int((ma != mb).sum() + ((ma & mb) & (a != b).any(2)).sum()))
        # ecran : 3 plans composes (sans sprites), ordre et defilements de chaque cote
        for nom, f, ph_ in (("upper", fu, pu), ("ro9a", fh, ph)):
            G.phys_code = ph_; G.tile.cache_clear()
            img = np.zeros((224, 384, 3), np.uint8)
            for L in G.layer_order(f):
                if not (f.breg(0x26) & (1 << L)): continue          # plan masque (bits 1-3 du layer control)
                rgb, m = G.render_screen_layer(f, L); img[m] = rgb[m]
            if nom == "upper": iu = img
            else: ih = img
        d = (iu != ih).any(2)
        same = all(fu.reg(G.LAYERS[L]["rx"]) == fh.reg(G.LAYERS[L]["rx"]) and fu.reg(G.LAYERS[L]["ry"]) == fh.reg(G.LAYERS[L]["ry"]) for L in (2, 3))
        print("  ecran (plans seuls) : defilements s2/s3 egaux : %s ; %d px differents sur %d (layer control %04X / %04X)" % (
            same, int(d.sum()), d.size, fu.breg(0x26), fh.breg(0x26)))
        if dimg:
            Image.fromarray(np.concatenate([iu, ih, np.where(d[..., None], 255, ih // 3).astype(np.uint8)], 1)).save(os.path.join(dimg, "ecran_%d_upper_ro9a_ecarts.png" % t))
    print("TOTAL scroll2+scroll3 : %d px differents" % tot)

if __name__ == "__main__":
    main()
