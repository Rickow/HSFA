# HSFA (SLUS-21317) — Analyse Scène / Résultat / Boot (session autonome 2026-06-24)

Décompilation depuis `eeMemory_versus.bin` (HSFA en combat, VA=offset). Objectifs :
(A) cartographier l'avant-jeu skippable ; (B) approfondir les fonctions clés pour l'arcade.

## 0. Couverture du dump (faisabilité boot-skip)
Régions résidentes non-nulles : `0x0-0x20000`, `0x70000-0x90000`, **`0x100000-0x1a0000` (main/EBOOT HSFA)**,
**`0x1c0000-0xb70000` (code+données jeu)**, `0x19d0000+` (options), etc.
- **Le code HSFA est résident** → décompilable (main, menu, combat, char-select, result).
- **Le shell Anthology (logos, sélection de jeu) est ABSENT** (programme séparé, pas chargé en RAM HSFA).
  ⇒ Les logos Anthology / la sélection de jeu **ne sont pas analysables ni patchables depuis ce dump**
  et tombent sous la contrainte shell-safe (même CRC). Un boot-skip de CE niveau exige un **dump de
  boot du shell** + serait risqué.
- **Skippable côté HSFA (résident)** : son intro/attract → mode-select, via le **code de scène** (cf §3).

## 1. Système de MODES (variable `0xb880a8`)
Confirmé par décompilation + savestates :
| Mode | Lanceur | Char-select | Combat |
|---|---|---|---|
| **3** | `0x252ff0` (VERSUS) | 2 pads | versus, **KO/vainqueur** |
| **1** | (TRAINING) | **1 pad (P1+P2)** | **infini, pas de KO** |
| **2** | — (code présent, non exposé) | 1 pad + gère P2 | inconnu (vestige 1P-vs-CPU ?) |
| 0 | `0x253280` | 1 pad | — |

Char-select racine `0x506070` branche sur `mode&1` (→ `0x506184` si pair) puis `mode&2`.
**Implication arcade** : training (mode 1) = sélection 1-pad des 2 persos MAIS combat infini.
⇒ Architecture retenue (Rickow) : **char-select en mode 1, basculer en mode 3 à la sortie**
(`0x5c55dc`) pour avoir un vrai KO. (Tentatives v20/v21 en cours de test.)

## 2. Flux RÉSULTAT (subphase `0x0e`) — pour enchaînement arcade propre
- `RESULT_h 0x2865f0` → `0x21d550` = **sous-séquenceur** : `struct+8`/2 indexe table **`0x5b2cd0`**
  (6 étapes : `0x21d5a0`,`0x21d620`,`0x21d710`,`0x21da40`,`0x21da60`,`0x21da90`).
- Étape finale **`0x21da90`** : lit `struct+0xc`, branche, et **écrit le code de scène `0x1144`**
  (`0x21df44`,`0x21e07c`) puis appelle **`0x21f6b0`** (interpréteur de transition).
- `0x21f6b0` : code scène `0x1144` → table **`0x5b2cf0`** → flux de commandes (`0x1100`) exécuté.
- Condition `0x1150` (dérivée de `struct+0xc`) choisit la branche (rematch/menu/…).
- **Piste arcade déterministe** : au lieu du skip-route fragile (v19), hooker l'étape finale du
  résultat / forcer le code de scène pour enchaîner sur un nouveau combat. À tracer en live (codes).

## 3. Système de SCÈNE (le mécanisme maître de transition)
- **Code de scène** = `0x70001144` (scratchpad), source persistante `0xb84214` (=struct-0x3dec).
- Écrit par les lanceurs (VERSUS `0x252ff0` pose le code), par le résultat (`0x21da90`).
- Lu/dispatché par `0x21f6b0` (interpréteur), `0x2222b0`, `0x229038`, `0x22ff00` (sérialise l'état).
- Le code est **apparié bit-à-bit** (codes vus : `0x5200`, `0x5700`) → PAS un simple index ;
  un dispatcher matche les bits. Table de flux `0x5b2cf0` (entrées code à partir de l'index 8 :
  `0x21ff30`, `0x220430`, `0x221f00`, `0x221f50`, `0x21ffb0`, `0x2201d0`, `0x220300`, `0x2206c0`…).
- **Pour boot-skip → mode-select** ET **arcade chaining** : il faut le **code de scène du mode-select**
  (et du combat). Identification exacte = traçage live (poser BP en écriture sur `0x70001144` /
  `0xb84214` aux transitions intro→titre→mode-select). Non déterminable proprement en statique (MMI).

## 4. Skip écran HANDICAP (entre combats, char-select)
- Sous-flux handicap = `0x5105d0` (pointeur table char-select `0x5c55d0[+0x14]` = **`0x5c55e4`**).
  C'est un sous-séquenceur (table `0x5c52e0`, 1er état `0x510690` écrit `+0x404`/`+0x804`).
- **Skip** : rediriger `0x5c55e4` → cave qui **avance le sous-flux** `0xb88008` au-delà du handicap
  (ou pose le flag candidat `0xb880c2`) puis retourne, sans afficher l'écran. Shell-safe (DATA).

## 5. Recommandations / prochaines étapes
1. **Finir l'archi training-select → versus-combat** (v21 en test) : si char-select 1-pad + KO OK,
   c'est la base saine.
2. **Enchaînement arcade DÉTERMINISTE** : remplacer le skip-route (`0xb84200=7`, source du "aléatoire")
   par une transition via le **code de scène** (forcer le combat suivant proprement). Nécessite
   d'identifier le code de scène "combat" en live.
3. **Nettoyer la nav menu** : VERSUS et ARCADE partagent le curseur 7 (`0xb84200`) → désync, à séparer.
4. **Handicap** : redirection `0x5c55e4` (si l'écran réapparaît dans la base training).
5. **Boot-skip** : côté HSFA seulement, via code de scène (mode-select au démarrage) — à tracer live.
   Côté shell Anthology = hors de portée sans dump de boot + risqué (shell-safe).

## Adresses clés (récap)
- Mode : `0xb880a8`. Scène : `0x70001144` / `0xb84214`. Curseur menu : `0xb84200`.
- RESULT : `0x2865f0`→`0x21d550`→table `0x5b2cd0`→`0x21da90`→`0x21f6b0`→table `0x5b2cf0`.
- Char-select : racine `0x506070`, sous-flux table `0x5c55d0` (init `0x506480`@+0, sortie `0x508b80`@+0xc,
  handicap `0x5105d0`@+0x14). Dérivation perso : `0x511ba0` (grilleA `0x5c5300`→`+0x116`).
- Lanceurs modes : VERSUS `0x252ff0`(m3), `0x253170`, `0x253280`(m0), `0x253430`. Menu render `0x252b30`.
