#!/usr/bin/env python3
"""Section de DONNEES de ro9 (fichier code_end..fin) : d'ou viennent ses octets ?
Fenetres de W octets (pas de 2 octets), mots u32 'pointeurs' (valeur dans [0x1F0000, 0xC00000)) masques a 0 des
deux cotes (les tables ont ete deplacees d'un module a l'autre : les pointeurs changent, pas le reste).
Une fenetre de ro9 presente dans un module de reference => ses octets sont 'repris'. Ordre d'attribution :
ro5 (Upper), ro3 (SFA3), ro1 (SFA), ro2 (SFA2), ro4 (SFA2 ALPHA). Les fenetres tout a zero sont ecartees."""
import os, sys, pickle, collections
import numpy as np
import commun as C
W = 32

def data(mod):
    b = C.load(mod); e = C.header(mod)['code_end']
    return np.frombuffer(b, dtype=np.uint8)[e:].copy(), e

def masked(arr, phase):
    a = arr.copy()
    n = (len(a) - phase) // 4
    u = a[phase:phase + 4*n].view(np.uint32)
    m = (u >= 0x1F0000) & (u < 0xC00000)
    u[m] = 0
    return a

def win_hashes(a, phase):
    """hachage des fenetres de W octets commencant a phase, phase+4, ... (sur le tableau masque pour cette phase)"""
    n = (len(a) - phase) // 4
    u = a[phase:phase + 4*n].view(np.uint32).astype(np.uint64)
    k = W // 4
    if n < k: return np.zeros(0, np.uint64), np.zeros(0, bool)
    h = np.zeros(n - k + 1, dtype=np.uint64); z = np.ones(n - k + 1, dtype=bool)
    P = np.uint64(0x100000001B3)
    for i in range(k):
        h = h * P + u[i:n - k + 1 + i] + np.uint64(i + 1)
        z &= (u[i:n - k + 1 + i] == 0)
    return h, ~z

def index(mod):
    a, _ = data(mod); S = set()
    for ph in (0, 2):
        h, nz = win_hashes(masked(a, ph), ph)
        S.update(h[nz].tolist())
    return S

def main():
    a9, e9 = data('ro9')
    refs = ['ro5', 'ro3', 'ro1', 'ro2', 'ro4']
    src = np.full(len(a9), -1, dtype=np.int8)       # -1 non attribue ; -2 zeros
    hits = {}
    for r in refs:
        S = index(r); cov = np.zeros(len(a9), bool)
        for ph in (0, 2):
            h, nz = win_hashes(masked(a9, ph), ph)
            hit = np.fromiter((x in S for x in h.tolist()), dtype=bool, count=len(h)) & nz
            for i in np.nonzero(hit)[0]:
                o = ph + 4*i; cov[o:o+W] = True
        hits[r] = cov
        print("%s : %.1f %% des octets de donnees de ro9 retrouves" % (r, 100*cov.mean()), flush=True)
    zero = (a9 == 0)
    for k, r in enumerate(refs):
        src[(src == -1) & hits[r]] = k
    src[(src == -1) & zero] = -2
    tot = len(a9)
    print("\nAttribution exclusive (ordre %s) sur %d octets (%.2f Mo) :" % (' > '.join(refs), tot, tot/2**20))
    for k, r in enumerate(refs): print("   %-4s %6.1f %%  %.2f Mo" % (r, 100*(src == k).mean(), (src == k).sum()/2**20))
    print("   zeros %5.1f %%  %.2f Mo" % (100*(src == -2).mean(), (src == -2).sum()/2**20))
    print("   NEUF  %5.1f %%  %.2f Mo" % (100*(src == -1).mean(), (src == -1).sum()/2**20))
    # carte par tranche de 64 Ko
    print("\nCarte (tranches de 0x10000, fichier / execution) : %% ro5 / ro3 / ro1 / ro2 / ro4 / zeros / neuf")
    rows = []
    for o in range(0, tot, 0x10000):
        s = src[o:o+0x10000]; n = len(s)
        fr = [(s == k).sum()/n for k in range(5)] + [(s == -2).sum()/n, (s == -1).sum()/n]
        rows.append((e9 + o, fr))
        print("   %s : %s" % (C.fe(e9 + o), ' '.join('%3.0f' % (100*x) for x in fr)))
    pickle.dump(dict(e9=e9, src=src, refs=refs), open(os.path.join(C.OUT, "donnees_ro9.pkl"), "wb"))

if __name__ == "__main__":
    main()
