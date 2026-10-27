# Carte mémoire unifiée des caves — Hyper SFA (z9)

> Plan directeur pour faire coexister/regrouper les injections (arcade · widescreen ·
> all-unlock · cross-stage) dans une seule ISO. Consolide le tableau des caves + la carte RAM
> + les points de hook + l'ordre par-frame. Adresses = RAM EE. Voir aussi
> `CARTO-Cross-Stage-Tables.md` (rendu), `ARCADE-Hyper-SFA.md` (arcade §8 bake),
> `PROJET-Anthology-Widescreen-Tiles.md` §4 (conflits).

## 0. Principe — 2 modules, pas 4 caves indépendantes

| Module | Features | Nature du hook | Cadence |
|---|---|---|---|
| **LOGIQUE** | arcade | redirection de **pointeurs de handlers** (flux de jeu/menu) | à chaque **transition de match** |
| **RENDU** | widescreen ⊕ cross-stage | interception dans le **pipeline BG** | **chaque frame** |
| (donnée) | all-unlock | **1 octet** (pas de code) | — |

- Le module RENDU **doit** être coordonné (widescreen et cross-stage touchent le même pipeline
  ET la même RAM `0x1580000` → conflit réel aujourd'hui). Les fusionner = résoudre le conflit.
- Le module LOGIQUE est **orthogonal** (gaté flag arcade, autre cadence) : même région = OK,
  mais aucun couplage fonctionnel avec le rendu.

---

## 1. Carte RAM runtime (EE) — occupation

```
0x001c0000 ┬ ARCADE  code+vars   (0x1c0000 RESULT hook … 0x1c0360 label ; vars 0x1c0100–0x1c0320)
0x001c0400 ┼ CROSS-STAGE v7 cave (asm_v7pg : 0x1c0400 → fin 0x1c0d54, 597 instr)
0x001c0d54 ┘   … marge libre jusqu'où ? (à borner ; région 0x1c0000 = PAS file-backed → bake reloge)
   …
0x001d7e90 ┬ WIDESCREEN 7 caves zb (0x1d7e90/eb0/ed0/ef0/f10/f30/f50, pas 0x20)
0x001d7f70 ┘   zéros après = marge cave restante (à re-vérifier)
   …
0x00b90000   source tilemap (ptr 0xbe2180)          ─┐
0x00ba0000   rings SCR1/2/3 (ba0000/ba4000/ba8000)   │  STRUCTURES STAGE
0x00bac000   palette source (128×16 CPS2 4444)       │  (cibles chemin A,
0x00db4000   bank tuiles (ptr repoint 0x1dc2e4)      │   PAS des caves)
0x00640960   pool SCR2 · 0x643c60 SCR3 · 0x6452e0 SOL ┘
   …
0x01580000 ┬ WIDESCREEN buffers relogés 8px ×2 (0x67500 @0x1580000 + 0x67500 @0x15F0000)
0x01660000 ┤   → occupé jusqu'ici ~0x1660000
0x01690000 ┼ ZONE LIBRE cross-stage recommandée (post-widescreen)
0x01700000 ┤   v7 staging (asm_v7pg) — au-dessus de 0x1660000, OK
0x019d0000 ┤ fin de la fenêtre libre (0x1580000–0x19d0000 = 4,4 Mo au total)
0x019d7000 ┘ FILE DE CHARGEMENT (queue framework, 0x80×0x40)
```

⚠️ **COLLISION connue** : le cave v7 met le package en **`0x1580000`** (check `UPST`) — **pile sur
les buffers widescreen**. En unifié : cross-stage doit charger dans **`0x1690000+`** (ou plus haut),
pas 0x1580000.

---

## 2. Sites de hook & patchs (par feature)

### LOGIQUE — Arcade (redirection de pointeurs data + 1 flag)
| Site (table handler) | → cave | Rôle |
|---|---|---|
| `0x5b5e9c` (subphase 0x0e RESULT) | `0x1c0000` | fin de combat : ladder/skip |
| `0x5c55dc` (sortie char-select) | `0x1c0140` | latch groove + P2 ladder |
| `0x5b5e88` (combat) | `0x1c0280` | (CINIT, versions antérieures) |
| `0x5b422c` (menu slot 7) | `0x1c0200` | `arcade_launch` |
| `0x5b4238` (menu phase-2) | `0x1c0240` | `modesel_clear` (restaure VS MODE) |
| `0x5b41f0/f4`, `0x5b4204` | (data nav) | curseur 7 dans le cycle |
| `0x69cf54` → `0x69cf70` | `0x1c0360` | label « ARCADE » |
| `0x19d2fa5` (octet) | — | VS MODE = COM (P2 CPU) |

### RENDU — Widescreen (interceptions d'instructions → caves zb)
| Site | Effet | → cave |
|---|---|---|
| `0x1d2360`, `0x1d2774` | Xstart tilemap −32px | `0x1d7e90+` |
| `0x1d38d4` | blit sol `0x180→0x1c0` | idem |
| `0x1d292c`, `0x1d2ef8` | sprites/HUD X +32px | idem |
| `0x1dbcf0`→`0x1580000`, `0x1dbcf4`→`0x15F0000` | reloc buffers 8px | (data) |

### RENDU — Cross-stage v7 (hook BG par-frame)
| Site | → cave | Rôle |
|---|---|---|
| `0x1d0750` (rendu BG, avant boucle couches) | `j 0x1c0400` | écrase pools/strips/palette + repoint bank |

### DONNÉE — All-unlock (aucun code)
- ISO : octet `0xa00771c4 = 0x0f` (e203=zb décompressé). Runtime : bitfield `0x19d10dc`.

---

## 3. Ordre par-frame du module RENDU (pourquoi ça marche fusionné)

```
[frame BG]
  0x1d0750  ── CROSS-STAGE : écrase pools SCR2/3 + strips + palette, repoint bank   (AMONT)
     │
     ▼  le composer natif compose le ring depuis les pools (maintenant = Upper)
     │
  0x1d2360/2774/38d4/292c/2ef8 ── WIDESCREEN : décale la géométrie (−32 / +32 / blit) (AVAL)
     │
     ▼  blit → écran
```
Le hook cross-stage est **en amont** des drawers que patche le widescreen ⟹ l'ordre tombe juste
tout seul : on remplace le *contenu* du décor, puis on en corrige la *géométrie*. **Zéro couplage
à gérer** tant que cet ordre amont→aval est respecté.

---

## 4. Zones cave FILE-BACKED (bake ISO ; mapping e544 = EE − 0x1F0000)

| Zone EE | Usage | État |
|---|---|---|
| `0x5CEF00–0x5CF108` | **ARCADE** code baké | occupé |
| `0x5CF0E0` | label « ARCADE » (data) | occupé |
| `0x5CF108–0x5CF300` | reste du slot arcade | ~libre |
| **`0x5D16F0`** | **CROSS-STAGE** (proposé) | libre |
| (zb après `0x1d7f70`) | reste widescreen | à re-vérifier |

Rappel : `0x1c0000` (runtime) **n'est pas file-backed** → au bake, les caves runtime sont
**relogées** dans ces zones file-backed (l'arcade l'a déjà fait : 0x1c0000→0x5CEF00).

---

## 5. Règles pour l'assemblage unifié

1. **Région de code unique** : regrouper le code des caves runtime en un blob contigu à
   `0x1c0000+` (arcade 0x1c0000–0x1c03xx, cross-stage 0x1c0400–0x1c0dxx) + **bloc de variables
   commun** → plus de collision d'adresses, flags partagés. Aucun impact fonctionnel.
2. **RAM cross-stage ≠ RAM widescreen** : charger les données stage en **`0x1690000+`**, jamais
   `0x1580000` (widescreen). Staging `0x1700000` OK.
3. **Caves zb `0x1d7e90+` = widescreen** : ne pas y toucher pour le cross-stage.
4. **Ordre par-frame** : hook cross-stage `0x1d0750` (amont) AVANT les drawers widescreen (aval).
   Respecter = pas de conflit de rendu.
5. **Bake** : reloger toute cave runtime en zone file-backed (arcade `0x5CEF00`, cross-stage
   `0x5D16F0`) ; all-unlock = octet ; widescreen = patchs SLUS+zb recompressés.
6. **Gating** : arcade gaté sur flag arcade (VERSUS intact) ; widescreen/cross-stage gatés sur
   « en combat » (menus/écrans intacts).

## 6. Verdict sur « regrouper »

- **Placement + variables + helpers partagés** : possible, recommandé, **sans effet fonctionnel**.
- **Fusion du module RENDU (widescreen⊕cross-stage)** : possible et **bénéfique** — résout le
  conflit RAM/pipeline existant (une seule carte mémoire + ordre amont→aval maîtrisé).
- **Arcade** : reste un module logique séparé (hooks + cadence propres) ; cohabite dans la même
  région sans couplage.
- **All-unlock** : trivial (octet), se pose n'importe où.
- La contrainte n'est **pas la place** (les caves sont petites, 4,4 Mo de RAM libre) : c'est
  **la coordination** (carte RAM partagée, ordre par-frame, placement file-backed).
