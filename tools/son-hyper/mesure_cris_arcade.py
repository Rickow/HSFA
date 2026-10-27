#!/usr/bin/env python3
"""Mesure des cris de degats et de K.O. sur l'arcade (SFA1 / SFA2 / SFA3) : le perso de J1 se fait frapper, on compte
les commandes son de sa page (cote 1). Resultat : cris_arcade.tsv (corrige_cris.py).

Il faut un coeur FBNeo de diagnostic qui journalise les commandes son du 68K, quel que soit le jeu : dans
CPSQSoundC0WriteByte (src/burn/drv/capcom/cps_mem.cpp), apres « CpsZRamC0[sekAddress >> 1] = byteValue; » :
    if (sekAddress == 0x001F && byteValue == 0 && getenv("HSFA_QSLOG")) { extern UINT32 nCurrentFrame;
        bprintf(0, _T("QSCMD %d %02X%02X %02X %02X%02X\\n"), nCurrentFrame, CpsZRamC0[0], CpsZRamC0[1], CpsZRamC0[2],
                CpsZRamC0[3], CpsZRamC0[4]); }
(jamais dans les coeurs livres). Puis, par case de la grille de selection (x vers la droite, y vers le bas depuis le
curseur de J1) :
  mesure_cris_arcade.py entrees X Y > e.txt
  HSFA_QSLOG=1 HSFA_ENTREES=e.txt joue_linux coeur_diag.so sfa.zip <system> 7000 /dev/null 2> err.log
  mesure_cris_arcade.py compte err.log [image_debut image_fin]
SFA1 : 1 piece par joueur, J2 (Ken) avance et frappe J1. SFA2 / SFA3 : 2 pieces par joueur, J2 ne rejoint pas, l'ordinateur
frappe J1. On ne garde que le premier match (avant l'ecran de continue).
"""
import collections, sys


def entrees(dx, dy):
    ev = [(600, 605, 0, 2), (620, 625, 1, 2), (660, 665, 0, 3), (700, 705, 1, 3)]     # pieces, Start J1 / J2
    f = 760
    for _ in range(dx): ev.append((f, f + 3, 0, 7)); f += 12                              # J1 : droite
    for _ in range(dy): ev.append((f, f + 3, 0, 5)); f += 12                              # J1 : bas
    ev += [(900, 904, 0, 1), (930, 934, 1, 1), (960, 964, 0, 1), (990, 994, 1, 1)]       # validations
    ev.append((1400, 12000, 1, 6))                                                       # J2 avance
    k = 0
    for f in range(1400, 12000, 24):
        b = [1, 10, 11, 1, 10, 0][k % 6]; k += 1                                         # LP, HP, HK, LP, HP, LK
        if k % 6 == 3: ev.append((f, f + 10, 1, 5))                                       # balayage
        ev.append((f + 2, f + 5, 1, b))
    return ev


def compte(log, a=1300, b=7000):
    """voix du cote 1 entre les images a et b : SFA1 0160-01F3, SFA2 0180-01FC et 0300-037E, page 00 00C0-00D3"""
    c = collections.Counter()
    for l in open(log, errors="replace"):
        t = l.split()
        if len(t) < 3 or "QSCMD" not in t[0]: continue
        f, v = int(t[1]), int(t[2], 16)
        if a < f < b and (0x160 <= v < 0x200 or 0x300 <= v < 0x380 or 0xC0 <= v < 0xD4): c["%04X" % v] += 1
    return c


if __name__ == "__main__":
    if sys.argv[1] == "entrees":
        for e in entrees(int(sys.argv[2]), int(sys.argv[3])): print(*e)
    else:
        a, b = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1300, 7000)
        for cmd, n in compte(sys.argv[2], a, b).most_common(12): print(n, cmd)
