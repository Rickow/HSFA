# RESUME-PSP : mode B du banc des coups (PSP oracle / Upper MAX)

Généré le 2026-10-25 par `outils/resume_psp.py` sur `resultats/max15` (221 essais, 6 fichiers). Méthode, correspondances et limites : `BANC-PSP.md`.

## 1. Vue d'ensemble

| série (fichier) | perso | adv | ISM | IDENTIQUE | PROCHE | DÉCALÉ | MUR | DIFFÉRENT | NC |
|---|---|---|---|---|---|---|---|---|---|
| ingrid_ryu_A_contres | ingrid | ryu | A | 8 | 0 | 0 | 0 | 40 | 0 |
| mika_eagle_A_x150 | mika | eagle | A | 12 | 7 | 0 | 3 | 13 | 2 |
| mika_eagle_A_x300 | mika | eagle | A | 6 | 4 | 1 | 10 | 14 | 2 |
| mika_ryu_A_x150 | mika | ryu | A | 18 | 6 | 0 | 3 | 8 | 2 |
| mika_ryu_A_x300 | mika | ryu | A | 6 | 5 | 0 | 12 | 12 | 2 |
| yun_ryu_A_prio | yun | ryu | A | 6 | 0 | 0 | 0 | 19 | 0 |

Total : DIFFÉRENT 106, DÉCALÉ 1, IDENTIQUE 56, MUR 28, NC 8, PROCHE 22

## 2. Écarts classés (du plus grave au moins grave)

### B coup absent dans Upper (0)

le coup sort sur PSP, rien (ou autre chose) dans Upper : à corriger en priorité.


### A exception Upper (0)

plantage / adresse illégale dans Upper pendant le coup.


### C2 dégâts différents (20)

les deux jouent le coup mais la vie perdue diffère.

- `mika_eagle_A_x150` **mika A** Flying Peach : ↓↙← + MP : dégâts J2 PSP 17 / Upper 16 (J1 : 0 / 0) ; 1re divergence tour 44 vie J2 : PSP 127 / Upper 128 [vie rendue par l'entraînement PSP au tour 164 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Flying Peach : ↓↙← + HP : dégâts J2 PSP 18 / Upper 17 (J1 : 0 / 0) ; 1re divergence tour 46 vie J2 : PSP 126 / Upper 127 [vie rendue par l'entraînement PSP au tour 166 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Shooting Peach : ↓↙← + MK : dégâts J2 PSP 17 / Upper 16 (J1 : 0 / 0) ; 1re divergence tour 26 vie J2 : PSP 127 / Upper 128 [vie rendue par l'entraînement PSP au tour 146 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Shooting Peach : ↓↙← + HK : dégâts J2 PSP 18 / Upper 17 (J1 : 0 / 0) ; 1re divergence tour 24 vie J2 : PSP 126 / Upper 127 [vie rendue par l'entraînement PSP au tour 144 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + LP : dégâts J2 PSP 32 / Upper 30 (J1 : 0 / 0) ; 1re divergence tour 114 vie J2 : PSP 126 / Upper 127 [vie rendue par l'entraînement PSP au tour 276 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + MP : dégâts J2 PSP 42 / Upper 41 (J1 : 0 / 0) ; 1re divergence tour 138 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 316 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + HP : dégâts J2 PSP 60 / Upper 58 (J1 : 0 / 0) ; 1re divergence tour 114 vie J2 : PSP 126 / Upper 127
- `mika_eagle_A_x300` **mika A** Flying Peach : ↓↙← + MP : dégâts J2 PSP 17 / Upper 16 (J1 : 0 / 0) ; 1re divergence tour 44 vie J2 : PSP 127 / Upper 128 [vie rendue par l'entraînement PSP au tour 164 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Flying Peach : ↓↙← + HP : dégâts J2 PSP 18 / Upper 17 (J1 : 0 / 0) ; 1re divergence tour 46 vie J2 : PSP 126 / Upper 127 [vie rendue par l'entraînement PSP au tour 166 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Shooting Peach : ↓↙← + MK : dégâts J2 PSP 17 / Upper 16 (J1 : 0 / 0) ; 1re divergence tour 26 vie J2 : PSP 127 / Upper 128 [vie rendue par l'entraînement PSP au tour 146 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Shooting Peach : ↓↙← + HK : dégâts J2 PSP 18 / Upper 17 (J1 : 0 / 0) ; 1re divergence tour 24 vie J2 : PSP 126 / Upper 127 [vie rendue par l'entraînement PSP au tour 144 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + LP : dégâts J2 PSP 32 / Upper 30 (J1 : 0 / 0) ; 1re divergence tour 114 vie J2 : PSP 126 / Upper 127 [vie rendue par l'entraînement PSP au tour 276 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + MP : dégâts J2 PSP 42 / Upper 41 (J1 : 0 / 0) ; 1re divergence tour 138 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 316 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + HP : dégâts J2 PSP 60 / Upper 58 (J1 : 0 / 0) ; 1re divergence tour 114 vie J2 : PSP 126 / Upper 127
- `yun_ryu_A_prio` **yun A** Yun pied debout HK dist 10 : dégâts J2 PSP 15 / Upper 6 (J1 : 0 / 0) ; 1re divergence tour 15 dX J2 : PSP 1 / Upper 6
- `yun_ryu_A_prio` **yun A** Yun pied debout HK dist 18 : dégâts J2 PSP 15 / Upper 6 (J1 : 0 / 0) ; 1re divergence tour 15 dX J2 : PSP 1 / Upper 6
- `yun_ryu_A_prio` **yun A** Yun pied debout HK dist 20 : dégâts J2 PSP 15 / Upper 6 (J1 : 0 / 0) ; 1re divergence tour 15 dX J2 : PSP 1 / Upper 6
- `yun_ryu_A_prio` **yun A** Yun pied debout HK dist 28 : dégâts J2 PSP 15 / Upper 6 (J1 : 0 / 0) ; 1re divergence tour 15 dX J2 : PSP 1 / Upper 6
- `yun_ryu_A_prio` **yun A** Yun pied debout HK dist 30 : dégâts J2 PSP 15 / Upper 6 (J1 : 0 / 0) ; 1re divergence tour 15 dX J2 : PSP 1 / Upper 6
- `yun_ryu_A_prio` **yun A** Yun pied debout HK dist 40 : dégâts J2 PSP 15 / Upper 6 (J1 : 0 / 0) ; 1re divergence tour 15 dX J2 : PSP 1 / Upper 6

### D état / animation différent (60)

suite d'états de J1 ou de J2 différente (1re divergence indiquée).

- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu LP au tour 10 : 243 images divergentes ; 1re : tour 54 etat J2 : PSP 02020000 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 174 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu LP au tour 22 : 243 images divergentes ; 1re : tour 66 etat J2 : PSP 02020000 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 186 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu LP au tour 34 : 240 images divergentes ; 1re : tour 79 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 198 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu HK au tour 10 : 241 images divergentes ; 1re : tour 58 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 176 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu HK au tour 16 : 241 images divergentes ; 1re : tour 64 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 183 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu HK au tour 22 : 242 images divergentes ; 1re : tour 70 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 188 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu HK au tour 28 : 242 images divergentes ; 1re : tour 75 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 195 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu LP au tour 10 : 243 images divergentes ; 1re : tour 54 etat J2 : PSP 02020000 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 174 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu LP au tour 22 : 243 images divergentes ; 1re : tour 66 etat J2 : PSP 02020000 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 186 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu LP au tour 34 : 240 images divergentes ; 1re : tour 79 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 198 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu HK au tour 10 : 241 images divergentes ; 1re : tour 58 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 176 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu HK au tour 16 : 241 images divergentes ; 1re : tour 64 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 183 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu HK au tour 22 : 242 images divergentes ; 1re : tour 70 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 188 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu HK au tour 28 : 242 images divergentes ; 1re : tour 75 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 195 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu LP au tour 10 : 200 images divergentes ; 1re : tour 14 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu LP au tour 16 : 190 images divergentes ; 1re : tour 20 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu LP au tour 22 : 182 images divergentes ; 1re : tour 26 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu LP au tour 28 : 172 images divergentes ; 1re : tour 32 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu LP au tour 34 : 164 images divergentes ; 1re : tour 38 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu HK au tour 10 : 204 images divergentes ; 1re : tour 18 etat J1 : PSP 02020002 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu HK au tour 16 : 195 images divergentes ; 1re : tour 23 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu HK au tour 22 : 186 images divergentes ; 1re : tour 30 etat J1 : PSP 02020002 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu HK au tour 28 : 177 images divergentes ; 1re : tour 35 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LK (contre) ; Ryu HK au tour 34 : 129 images divergentes ; 1re : tour 42 etat J1 : PSP 02020002 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu LP au tour 10 : 200 images divergentes ; 1re : tour 14 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu LP au tour 16 : 190 images divergentes ; 1re : tour 20 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu LP au tour 22 : 182 images divergentes ; 1re : tour 26 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu LP au tour 28 : 172 images divergentes ; 1re : tour 32 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu LP au tour 34 : 164 images divergentes ; 1re : tour 38 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu HK au tour 10 : 204 images divergentes ; 1re : tour 18 etat J1 : PSP 02020002 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu HK au tour 16 : 195 images divergentes ; 1re : tour 23 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu HK au tour 22 : 186 images divergentes ; 1re : tour 30 etat J1 : PSP 02020002 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu HK au tour 28 : 177 images divergentes ; 1re : tour 35 etat J1 : PSP 02020000 / Upper 02000e02
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HK (contre) ; Ryu HK au tour 34 : 129 images divergentes ; 1re : tour 42 etat J1 : PSP 02020002 / Upper 02000e02
- `mika_ryu_A_x150` **mika A** Heavenly Dyanamite : 720° + LP : 22 images divergentes ; 1re : tour 52 etat J2 : PSP 02000c00 / Upper 02000002 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_ryu_A_x150` **mika A** Heavenly Dyanamite : 720° + MP : 22 images divergentes ; 1re : tour 52 etat J2 : PSP 02000c00 / Upper 02000002 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_ryu_A_x150` **mika A** Heavenly Dyanamite : 720° + HP : 23 images divergentes ; 1re : tour 52 etat J2 : PSP 02000c00 / Upper 02000002 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_ryu_A_x150` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + MP : 484 images divergentes ; 1re : tour 138 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 316 : comparaison arrêtée]
- `mika_ryu_A_x150` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + HP : 468 images divergentes ; 1re : tour 162 etat J2 : PSP 02020000 / Upper 02020202
- `mika_ryu_A_x300` **mika A** Heavenly Dyanamite : 720° + LP : 22 images divergentes ; 1re : tour 52 etat J2 : PSP 02000c00 / Upper 02000002 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_ryu_A_x300` **mika A** Heavenly Dyanamite : 720° + MP : 22 images divergentes ; 1re : tour 52 etat J2 : PSP 02000c00 / Upper 02000002 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_ryu_A_x300` **mika A** Heavenly Dyanamite : 720° + HP : 23 images divergentes ; 1re : tour 52 etat J2 : PSP 02000c00 / Upper 02000002 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_ryu_A_x300` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + MP : 487 images divergentes ; 1re : tour 138 etat J2 : PSP 02020002 / Upper 02020202 [vie rendue par l'entraînement PSP au tour 316 : comparaison arrêtée]
- `mika_ryu_A_x300` **mika A** Rainbow Hip Rush : ↓↘→↓↘→ + HP : 471 images divergentes ; 1re : tour 162 etat J2 : PSP 02020000 / Upper 02020202
- `mika_ryu_A_x300` **mika A** Sardine's Beach Special : ↓↘→↓↘→ + LK : 247 images divergentes ; 1re : tour 170 etat J1 : PSP 02001006 / Upper 02001008
- `mika_ryu_A_x300` **mika A** Sardine's Beach Special : ↓↘→↓↘→ + MK : 224 images divergentes ; 1re : tour 170 etat J1 : PSP 02001006 / Upper 02001008
- `mika_ryu_A_x300` **mika A** Sardine's Beach Special : ↓↘→↓↘→ + HK : 224 images divergentes ; 1re : tour 170 etat J1 : PSP 02001006 / Upper 02001008
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + LK dist 20 : 175 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a02 / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + MK dist 20 : 175 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a0c / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + HK dist 20 : 175 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a08 / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + LK dist 40 : 175 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a02 / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + MK dist 40 : 175 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a0c / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + HK dist 40 : 175 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a08 / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + LK dist 60 : 5 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a02 / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + MK dist 60 : 5 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a0c / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun demi-tour arriere + HK dist 60 : 5 images divergentes ; 1re : tour 13 etat J1 : PSP 02000a06 / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun QCB + LP dist 40 : 64 images divergentes ; 1re : tour 8 etat J1 : PSP 02000a0a / Upper 02000e02 [vie rendue par l'entraînement PSP au tour 148 : comparaison arrêtée]
- `yun_ryu_A_prio` **yun A** Yun QCB + HP dist 40 : 63 images divergentes ; 1re : tour 8 etat J1 : PSP 02000a02 / Upper 02000e02 [vie rendue par l'entraînement PSP au tour 149 : comparaison arrêtée]
- `yun_ryu_A_prio` **yun A** Yun QCB + LP dist 80 : 2 images divergentes ; 1re : tour 8 etat J1 : PSP 02000a0a / Upper 02000e02
- `yun_ryu_A_prio` **yun A** Yun QCB + HP dist 80 : 3 images divergentes ; 1re : tour 8 etat J1 : PSP 02000a02 / Upper 02000e02

### D position / vie différente (14)

mêmes états mais position X / Y ou vie différente de plus de 2 px.

- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu LP au tour 16 : 241 images divergentes ; 1re : tour 62 dX J2 : PSP 0 / Upper 11 [vie rendue par l'entraînement PSP au tour 180 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu LP au tour 28 : 241 images divergentes ; 1re : tour 74 dX J2 : PSP 0 / Upper 11 [vie rendue par l'entraînement PSP au tour 192 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+LP (contre) ; Ryu HK au tour 34 : 241 images divergentes ; 1re : tour 82 Y J2 : PSP 178 / Upper 168 [vie rendue par l'entraînement PSP au tour 200 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu LP au tour 16 : 241 images divergentes ; 1re : tour 62 dX J2 : PSP 0 / Upper 11 [vie rendue par l'entraînement PSP au tour 180 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu LP au tour 28 : 241 images divergentes ; 1re : tour 74 dX J2 : PSP 0 / Upper 11 [vie rendue par l'entraînement PSP au tour 192 : comparaison arrêtée]
- `ingrid_ryu_A_contres` **ingrid A** Ingrid QCB+HP (contre) ; Ryu HK au tour 34 : 241 images divergentes ; 1re : tour 82 Y J2 : PSP 178 / Upper 168 [vie rendue par l'entraînement PSP au tour 200 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Heavenly Dyanamite : 720° + LP : 50 images divergentes ; 1re : tour 40 dX J1 : PSP 29 / Upper 34 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Heavenly Dyanamite : 720° + MP : 50 images divergentes ; 1re : tour 40 dX J1 : PSP 29 / Upper 34 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_eagle_A_x150` **mika A** Heavenly Dyanamite : 720° + HP : 51 images divergentes ; 1re : tour 40 dX J1 : PSP 29 / Upper 34 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Daydream Headlock : 360° + MK : 110 images divergentes ; 1re : tour 258 dX J1 : PSP -106 / Upper -112
- `mika_eagle_A_x300` **mika A** Heavenly Dyanamite : 720° + LP : 50 images divergentes ; 1re : tour 40 dX J1 : PSP 29 / Upper 34 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Heavenly Dyanamite : 720° + MP : 50 images divergentes ; 1re : tour 40 dX J1 : PSP 29 / Upper 34 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_eagle_A_x300` **mika A** Heavenly Dyanamite : 720° + HP : 51 images divergentes ; 1re : tour 40 dX J1 : PSP 29 / Upper 34 [vie rendue par l'entraînement PSP au tour 127 : comparaison arrêtée]
- `mika_ryu_A_x300` **mika A** Daydream Headlock : 360° + HK : 54 images divergentes ; 1re : tour 295 dX J1 : PSP -160 / Upper -166

### D autre (0)

divergence autre.


### C1 décalé (1)

même suite d'états, décalée de n tours (délai d'un spécial, durée d'une phase).

- `mika_eagle_A_x300` **mika A** Brain Buster : → + LK+MK : même suite mais PSP(tour e) = Upper(tour e-1) à partir du tour 50 (tour 50 dX J2 : PSP -135 / Upper -141) [vie rendue par l'entraînement PSP au tour 168 : comparaison arrêtée]

### E manip non reconnue sur PSP (à adapter) (12)

Upper sort le coup, la PSP non : très probablement la manip scriptée (timing, diagonales, distance) ; à rejouer avec une autre manip avant de conclure.

- `mika_eagle_A_x150` **mika A** Wingless Airplane : (air) →↘↓↙← + LK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_eagle_A_x150` **mika A** Wingless Airplane : (air) →↘↓↙← + MK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_eagle_A_x150` **mika A** Wingless Airplane : (air) →↘↓↙← + HK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_eagle_A_x300` **mika A** Wingless Airplane : (air) →↘↓↙← + LK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_eagle_A_x300` **mika A** Wingless Airplane : (air) →↘↓↙← + MK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_eagle_A_x300` **mika A** Wingless Airplane : (air) →↘↓↙← + HK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_ryu_A_x150` **mika A** Wingless Airplane : (air) →↘↓↙← + LK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_ryu_A_x150` **mika A** Wingless Airplane : (air) →↘↓↙← + MK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_ryu_A_x150` **mika A** Wingless Airplane : (air) →↘↓↙← + HK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_ryu_A_x300` **mika A** Wingless Airplane : (air) →↘↓↙← + LK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_ryu_A_x300` **mika A** Wingless Airplane : (air) →↘↓↙← + MK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)
- `mika_ryu_A_x300` **mika A** Wingless Airplane : (air) →↘↓↙← + HK : le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)

### Écarts non significatifs

- MUR : 28 (divergence de position près d'un bord de scène ; la scène PSP est plus large).
- PROCHE : 22 (±2 px / ±1 tour).
- NC : 8 (rien ne sort des deux côtés : manip ou condition à revoir).
