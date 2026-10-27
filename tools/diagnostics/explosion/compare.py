"""Comparaison pixel à pixel (valeurs brutes CPS2) : anim 0 / anim 5 de 2E50A0 vs efct.pac 300-305."""
import numpy as np, rendu_anim as r, rendu_efct as e
pal = [(v, 0, 0, 255) for v in range(16)]          # canal R = valeur brute, A = couverture
def carte(im): return np.where(im[..., 3] > 0, im[..., 0].astype(int), -1)
for n in (0, 5):
    tot = []
    for k, (a, d, f, fr) in enumerate(r.pas(n)[:6]):
        A = carte(r.rendu(fr, pal, taille=256, ox=128, oy=128)[2])
        B = carte(e.rendu(300 + k, pal, taille=256, ox=128, oy=128))
        best = None
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                Bs = np.roll(np.roll(B, dy, 0), dx, 1)
                u = (A >= 0) | (Bs >= 0); eq = (A == Bs) & u
                s = eq.sum() / max(u.sum(), 1)
                if best is None or s > best[0]: best = (s, dx, dy, int(u.sum()), int((A >= 0).sum()), int((B >= 0).sum()))
        tot.append(best)
        print(f'anim {n} pas {k} frame {fr:#x} vs efct {300+k} : identité {best[0]*100:5.1f} % (décalage dx={best[1]} dy={best[2]}, px arcade={best[4]}, px PSP={best[5]})')
