#!/usr/bin/env python3
"""Mode Arcade d'Upper : code atteint depuis les scenes propres a l'arcade (A5+4 = 6, 8, A, C ; table T_61C1E0),
moins le code atteint depuis le reste du programme (reset, taches, scenes 0/2/4/E) ; classement de chaque routine
par rapport a Hyper (correspondance inverse ro5 -> ro9) et vivacite de l'homologue dans Hyper."""
import os, sys, pickle, collections, json
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb"))
ORDRE = ['identique', 'identique 68K', 'deplacements', 'quasi identique (>=90 %)', 'modifiee (70-90 %)',
         'apparentee (40-70 %)', 'nouvelle (<40 %)']
SCENES5 = {6: 0x2614a0, 8: 0x2614d0, 0xA: 0x261500, 0xC: 0x270920}
PARTAGE5 = {0: 0x261210, 2: 0x261470, 4: 0x261560, 0xE: 0x261530}
RACINES5 = [0xCED70, 0x322A0, 0x324B0, 0x32830]           # reset, init, tache par image, balayage
RACINES9 = [0x3DA00, 0x3EC20, 0x3EE30, 0x3F1B0]

def bilan(mod, S, titre):
    T = AT.taille(mod); return "%s : %d routines, %d o MIPS" % (titre, len(S), sum(T[a] for a in S))

def main():
    T5 = AT.taille('ro5')
    tout5 = AT.reach('ro5', RACINES5)
    reste5 = AT.reach('ro5', RACINES5, bloque=SCENES5.values())
    print(bilan('ro5', tout5, "ro5 atteint depuis le reset"))
    print(bilan('ro5', reste5, "ro5 atteint sans les scenes 6/8/A/C"))
    vivant9 = AT.reach('ro9', RACINES9)
    print(bilan('ro9', vivant9, "ro9 atteint depuis le reset"))
    par_scene = {}
    excl = set()
    for k, r in SCENES5.items():
        R = AT.reach('ro5', [r]); E = R - reste5
        par_scene[k] = (R, E); excl |= E
        print(bilan('ro5', R, "scene %X : atteint" % k), "|", bilan('ro5', E, "exclusif"))
    print(bilan('ro5', excl, "ARCADE exclusif (union)"))
    # classement / Hyper
    cl = collections.Counter(); cln = collections.Counter(); vivant = collections.Counter(); mort = collections.Counter()
    lignes = []
    for a in sorted(excl):
        r = INV[a]; c = r['classe']; cl[c] += T5[a]; cln[c] += 1
        p = r['partenaire']; v = p in vivant9 if p is not None else None
        if c in ORDRE[:4]:
            (vivant if v else mort)[c] += T5[a]
        sc = ''.join('%X' % k for k, (R, E) in par_scene.items() if a in E)
        lignes.append((a, T5[a], r['n68'], c, p, r['score'], v, sc))
    print("\nClassement des routines ARCADE exclusives d'Upper par rapport a Hyper (taille MIPS) :")
    tot = sum(T5[a] for a in excl)
    for c in ORDRE:
        print("  %-26s %7d o  %4d routines  %5.1f %%   (homologue vivant dans ro9 : %d o, mort : %d o)" % (
            c, cl[c], cln[c], 100 * cl[c] / tot, vivant[c], mort[c]))
    n68 = sum(INV[a]['n68'] for a in excl)
    print("  instructions 68K traduites : %d" % n68)
    with open(os.path.join(OUT, "arcade_upper.tsv"), "w") as f:
        f.write("routine_ro5\ttaille\tn68\tclasse_vs_ro9\tpartenaire_ro9\tscore\thomologue_vivant_ro9\tscenes\n")
        for a, t, n, c, p, s, v, sc in lignes:
            f.write("0x%X\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n" % (a, t, n, c, '0x%X' % p if p is not None else '', s, v, sc))
    pickle.dump(dict(excl=excl, par_scene={k: (sorted(R), sorted(E)) for k, (R, E) in par_scene.items()},
                     reste5=reste5, tout5=tout5, vivant9=vivant9), open(os.path.join(OUT, "arcade_upper.pkl"), "wb"))

if __name__ == "__main__":
    main()
