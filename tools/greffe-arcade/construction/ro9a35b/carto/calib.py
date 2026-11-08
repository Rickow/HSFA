import sys, numpy as np, couverture as V, commun as C
for K in (32, 64, 128):
    V.K = K
    for m, refs in (('ro9',('ro5',)),('ro9',('ro3',)),('ro9',('ro5','ro3')),('ro1',('ro5',)),('ro2',('ro5',)),('ro5',('ro9',)),('ro3',('ro9',))):
        cov,_ = V.cover(m, refs, False)
        print("K=%3d  %s couvert par %-8s : %5.1f %%" % (K, m, '+'.join(refs), 100*cov.mean()), flush=True)
