"""Planche : ligne 1 = anim 0 (2E52D0), ligne 2 = anim 5 (2E565C), ligne 3 = efct.pac 300-305 (PSP).
Valeurs brutes CPS2 en fausses couleurs (pas la vraie palette : la palette $16 est réglée par l'acteur via $C/$D)."""
import sys, numpy as np, rendu_anim as r, rendu_efct as e
from PIL import Image, ImageDraw
def palette(mode):
    if mode == 'gris': return [(v * 17, v * 17, v * 17, 255) for v in range(16)]
    return [(min(255, v * 34), max(0, min(255, (v - 4) * 28)), max(0, min(255, (v - 10) * 50)), 255) for v in range(16)]
def cadre(im):
    im = im.copy(); im[..., 3] = 255
    im[0, :] = im[-1, :] = im[:, 0] = im[:, -1] = (90, 90, 90, 255); return im
for mode in ('gris', 'feu'):
    pal = palette(mode)
    L = [np.concatenate([cadre(r.rendu(fr, pal)[2]) for a, d, f, fr in r.pas(n)[:6]], 1) for n in (0, 5)]
    L.append(np.concatenate([cadre(e.rendu(k, pal)) for k in range(300, 306)], 1))
    im = Image.fromarray(np.concatenate(L, 0)).resize((960 * 2, 480 * 2), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    for i, t in enumerate(('anim 0 (pas 2E52D0) : frames 2E6894 ($12 vide), 2E6B72..2E6BB2 (type 6)',
                           'anim 5 (pas 2E565C) : frames 2E8ECA..2E8FA4 (type 6)',
                           'PSP efct.pac frames 300-305')):
        dr.text((8, 8 + 320 * i), t, fill=(255, 255, 0))
    for k in range(6):
        dr.text((8 + 320 * k, 300), f'pas {k}', fill=(200, 200, 200))
    im.save(f'<workspace>/work/agent_explosion/anim0_anim5_efct300_{mode}.png')
