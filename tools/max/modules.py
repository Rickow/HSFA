import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
#!/usr/bin/env python3
"""Modules de code des persos dans l'EBOOT de SFA3 MAX (méthode finale, reproductible).

1. Relocations (.rel.data) -> mots-pointeurs exacts (relocs.py).
2. Table des routines racines par ID perso : 0x215040 (42 entrées). Les racines sont rangées
   dans l'ordre des ID à travers .text => un module contigu par perso ; sa taille = écart à la
   racine suivante. Le dernier (Ingrid) est borné par les données : fin = plus haute cible
   des tables de pointeurs dont la première cible est dans son module.
3. Contrôle : part des fonctions du module pointées depuis les données (gestionnaires d'états).
4. API moteur : cibles `jal` hors modules persos ; recouvrement avec celles des persos arcade.
   ATTENTION : dans ce PRX les `jal` sont 0-based (relogés au chargement) -> cible = imm26 << 2.
"""
import json, collections, bisect, os
from charcode2 import P, PA, S, W, jal, fend, fstart, TEXT_END
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(HERE, "pl_mapping.json")))
ROOTS = 0x215040
root = lambda c: P[ROOTS + 4*c]
def module_bounds():
    order = sorted({(root(c), c) for c in range(42)})
    b = {c: (a, order[i+1][0]) for i, (a, c) in enumerate(order[:-1])}
    ing = root(0x29)
    runs, cur = [], [PA[0]]
    for x in PA[1:]:
        if x == cur[-1] + 4: cur.append(x)
        else: runs.append(cur); cur = [x]
    runs.append(cur)
    ends = [max(t) for r in runs for t in [[P[a] for a in r if P[a] < TEXT_END]]
            if t and ing <= min(t) < ing + 0x4000]
    b[0x29] = (ing, fend(fstart(max(ends))))
    b[0x13] = b[0x11] = (root(0x11), root(0x12))          # Gen et Gen (alt) partagent leur racine
    return b
def main():
    B = module_bounds(); LO, HI = min(a for a, _ in B.values()), max(e for _, e in B.values())
    pointed = collections.Counter(fstart(t) for t in P.values() if t < TEXT_END)
    calls = lambda a, e: collections.Counter(jal(W[k]) for k in range(a//4, e//4) if W[k] >> 26 == 3)
    eng = lambda c: {t for t in calls(*B[c]) if not (LO <= t < HI)}
    arcade = set().union(*(eng(c) for c in range(0x20)))
    upper = set().union(*(eng(c) for c in range(0x20, 0x25)))
    print(f"modules persos : {LO:#x}..{HI:#x}  ({(HI-LO)/1024:.0f} Ko)")
    print(f"{'ID':<5}{'perso':<14}{'module':>9}{'fonctions':>11}{'pointées':>10}{'API moteur':>12}{'dont arcade':>13}")
    for c in range(42):
        a, e = B[c]; fs = [f for f in S if a <= f < e]; E = eng(c)
        pt = 100 * sum(f in pointed for f in fs) / max(len(fs), 1)
        print(f"{c:#04x} {NAMES[f'{c:02x}']:<14}{(e-a)/1024:7.1f} Ko{len(fs):9}{pt:9.0f} %{len(E):10}{sum(t in arcade for t in E):11}")
    four = set().union(*(eng(c) - arcade for c in (0x26, 0x27, 0x28, 0x29)))
    use = collections.Counter(t for c in (0x26, 0x27, 0x28, 0x29) for t in eng(c) - arcade)
    print(f"\nutilitaires moteur appelés par Eagle/Maki/Yun/Ingrid mais par aucun perso arcade : {len(four)}"
          f" (~{sum(fend(t)-t for t in four)/1024:.0f} Ko), dont {sum(use[t] >= 2 for t in four)} partagés par >= 2 des 4,"
          f" {len(four & upper)} utilisés par les ajouts d'Upper")
if __name__ == "__main__":
    main()
