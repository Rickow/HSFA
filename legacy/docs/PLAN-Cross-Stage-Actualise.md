# Plan cross-stage ACTUALISÉ — fusion sessions précédentes (v7/SPK) + session 2026-09-02

> Réconcilie ce qui a MARCHÉ avant (cave v7 `asm_v7pg.py`, schéma SPK1 `pack_build.py` gelé
> 2026-08-14, modèle v2 `stage_pack_v2_schema.md`) avec les acquis de la session actuelle
> (décompilation composeur, rendu offline, repacker .p2s, ISO all-unlock). Remplace l'approche
> naïve « écrasement mid-combat » (invalidée in-game le 2026-09-02). Réfs : `CARTO-Cross-Stage-Tables.md`,
> `PREP-Cross-Stage-Proto.md`, `PROJET-Hyper-Arcade.md`.

## 0. LA leçon qui recadre tout

**Le combat = COMPOSEUR ; il n'y a PAS de recompose mid-match.** Donc :
- ❌ Écraser le **ring** en combat = recomposé/écrasé → bouillie (test 2026-09-02).
- ❌ Écraser **toute la bank** = casse le HUD (tuiles système partagées).
- ✅ **Injecter au LOAD-TIME** : écrire pool + listes + palette-blocs + **seulement la région
  décor de la bank**, puis laisser le layout naturel de fin de chargement composer. Scroll natif.

C'est ce que faisait v7 (copies pendant l'écran « NOW LOADING », magic réarmé par e527) et ce
que fige SPK1 (« memcpy chaque bloc à son home natif + stage_sel + `0xb674f8=1` »). `0xb674f8`
n'est efficace **qu'au load** (mid-match il vide le ring sans relancer le layout des pages).

## 1. Ce qui a MARCHÉ avant (à réutiliser tel quel)

### Cave v7 (`asm_v7pg.py`) — recette de référence, validée « rendable » (savestate 10)
Hook `0x1d0750` (par-frame, actif au load). En combat (flag), one-shot par cycle de load :
1. **Bank = région décor SEULEMENT** (préserve HUD/système/menus) :
   - trou remap `0x1074000` (= `0xdb4000+0x2c0000`), 0x3d60 mots (décor SCR2) ;
   - tuiles SCR1 jungle `0xddb9c0` (+0x279c0), grille objets `0xff4000`.
   - **JAMAIS toute la bank** (v7.13 : « le reste reste NATIF → UI propre »).
2. **Pool pages** dans les slots : SCR2 `0x640c60` (slots 1-4) + ciel `0x643960` (slot 0x10,
   **slot 0 partagé INTACT**) ; SCR3 `0x6446e0` (slots 0x0e-0x1d).
3. **Listes de layout** : SCR2 `0x696018` (+variantes rounds `0x696028/38`) ; SCR3 `0x696050`
   (`/90/d0`) ; + copies runtime `0xb83250`/`0xb832d0`.
4. **Palette** : blocs `0x660660`/`0x662680`/`0x6646a0` (SCR3 rows 0x60-0x7f → table `0x664280`) ;
   + **CAVE2** (hook `0x1d0818`, post-`FUN_1d1300`) copie work→twin chaque frame (rows 0x40-0x7f)
   pour tuer le « 1 frame/2 en couleurs versus » (fond sombre/bleu).
5. **Lock stage 8** partout (char-select, cycleur, writers) + **variante `[0xb88100]=4`** (config
   couches Blanka = [0,1,3,2] = variante 4). **CAVE3** (hook `0x1d0784`) = mapping caméra→fenêtres z5
   (scroll calibré : s1=0x152+cam·23/96, s2=cam, s3=0x124+cam·23/48).

### Artefacts prêts (dans `<workspace>/tmp_hdd/`)
- `stage_upper_pkg.bin/.mwo3` + `stage_upper_remap.json` (package Blanka + remap tuiles épars→compacts).
- `v7pg_lines.txt` (pnach v7 complet), `v7_section.bin` (section cave assemblée).
- `pack_build.py` (extracteur SPK1 depuis z9 via PINE), `pine_lab.py` (accès RAM live PCSX2).

### Limite connue de v7 (pourquoi le pivot v2)
Package Blanka **hand-tuné** (offsets, variante, calibrations spécifiques) → 43 itérations
in-game pour régler couleurs/flicker/scroll. **Ne se généralise pas** tel quel aux ~20 stages.

## 2. Ce que la session 2026-09-02 AJOUTE (à ne pas jeter)

| Acquis | Valeur pour la suite |
|---|---|
| **Composeur z9 entièrement décompilé** (tables `0x5b41c0/d8/e8`, builders `0x2537e0`, pools, listes SPR+0x1110, scroll=registre, palette `FUN_1d1300`) | **Confirme le modèle SPK1** indépendamment ; donne les adresses exactes pour un extracteur/injecteur générique |
| **Formule palette** (`c=[bri][R][G][B]`, canal=`nib·bri·0x11/0x1f`) + **format tuile** (8×8 4bpp LSB) + **base pal/couche** (SCR2 0x40 / SCR3 0x60) + flips (H=0x20, V=0x40) | **RENDU OFFLINE** → valider un package AVANT injection |
| **`render_stage.py`** (bank+palette+ring → PNG, temple Chun-Li net) | **Casse le cycle des 43 itérations** : itérer hors jeu |
| **`z5_stage_extract.py`** (ring composé + bank + palette de tout stage Upper) | Matière première pour bâtir un package générique |
| **`p2s_inject_stage.py`** (repacker .p2s ZIP+zstd, VALIDÉ sur vrai savestate) | Injection de test **au load-screen** sans recompiler de cave |
| **Isolation bank** : persos = banks `+0x38/3c/44` (intactes) ; HUD = bank BG `+0x34` (à préserver) | Explique le HUD cassé ; borne la région bank à toucher |
| **`unlock_patcher.py`** + ISO `SFA_Anthology_AllUnlocked_WORK.iso` | Base de test propre (vanilla+unlock, sans widescreen) |
| **Correctif** ring SCR3 = **0x4000** (pas 0x18000) | Les buffers se suivent tous les 0x4000 |

**La grande synergie** : v7 a prouvé la RECETTE mais itérait en aveugle ; ma session apporte le
**rendu offline** + les **outils d'extraction/injection** → on peut construire un package pour
N'IMPORTE quel stage et le **valider hors jeu** avant de toucher l'émulateur.

## 3. Modèle de données unifié (SPK)

Un stage_pack = ce que le composeur natif attend, aux homes z9 :
- **desc/listes** `0x695ff0` (0xC0) : listes d'index de pages SCR2 (+0x28) / SCR3 (+0x60) par round.
- **pool SCR2** `0x640960` (0x300/page) — pages dédupliquées, slots à partir de 1 (slot 0 partagé).
- **pool SCR3** `0x643c60` (0xc0/page) — idem.
- **palette** table `0x660240`/blocs (rows par couche).
- **bank décor** : tuiles référencées, **remappées en indices compacts**, écrites SEULEMENT dans
  la région décor de `0xdb4000` (pas le système).

**Pont z5→SPK** (z5 n'a pas de pool, il streame) : partir du **ring composé z5** (extrait) →
**dé-composer** en pages dédupliquées + liste (= pool+desc) → **collecter les tuiles** référencées
+ **remapper** → région bank compacte → palette. Chaque étape **validée par `render_stage.py`**.

## 4. Plan d'action ciblé (phases, avec preuves de sortie)

### Phase 0 — Rétablir une base qui MARCHE (avant de créer)
- Poser `v7pg_lines.txt` en pnach PCSX2 (CRC `72CE7A78` = ISO all-unlock), `EnableCheats=true`,
  booter Hyper → combat. **Sortie attendue** : décor Blanka z5 rendu (reproduit « savestate 10 »).
  → Confirme que la recette v7 marche sur le setup actuel = point de départ sain.
- ⚠️ si le pnach ne matche pas (adresses zero9 = risque multi-jeux §4.1bis), le cocher **seulement
  pour Hyper**.

### Phase 1 — Pipeline package OFFLINE générique (le cœur de l'apport session)
1. **Dé-composeur** `ring → (pool pages dédupliquées + listes SCR2/SCR3)` : reprendre la logique
   de `pack_build.py` (schéma SPK1) mais à partir du ring extrait, pas de PINE.
2. **Collecteur+remappeur tuiles** : tuiles référencées par les pages → indices compacts
   (comme `stage_upper_remap.json`) → région bank décor.
3. **Palette** : rows par couche → blocs table.
4. **VALIDATION OFFLINE** : `render_stage.py` compose pool+listes+bank-remappée+palette → PNG ;
   doit correspondre au ring d'origine. **Preuve sans émulateur.**
   → Sortie : un `stage_pack` Chun-Li (format SPK) validé à l'écran, prêt à injecter.

### Phase 2 — Injection au LOAD-TIME (pas en combat)
Deux véhicules, du plus simple au plus propre :
- **(2a) Savestate au LOAD-SCREEN** : refaire un savestate pendant « NOW LOADING » du stage ;
  `p2s_inject_stage.py` (étendu) écrit les blocs SPK aux homes + `0xb674f8=1` → au chargement,
  le layout naturel compose. Test **sans recompiler de cave**, sans pad.
- **(2b) Adapter le cave v7** : remplacer les données Blanka embarquées par le package Chun-Li
  (garder toute la logique v7 : région bank, pool, listes, palette, CAVE2/3, lock stage). Pnach.

### Phase 3 — Multi-stage (généralisation, plan v2/final)
- Boucler le pipeline Phase 1 sur tous les stages Upper (savestates Upper par stage).
- **Table perso→stage maison** + **hook char-select** (technique arcade) + **loader AFS**
  (`FUN_154c9c`) chargeant le package du match dans `0x1690000+` (RAM libre hors widescreen).
- Bake final unifié sur `[Widescreen][Arcade].iso` (adresses identiques, vérifié ; placer la RAM
  autour des buffers widescreen).

## 5. Prochaines actions concrètes (ordre)
1. **Phase 0** : préparer le pnach v7 + le poser dans `~/.config/PCSX2/cheats/` → tu confirmes le rendu Blanka.
2. **Phase 1** : coder le dé-composeur + remappeur, valider Chun-Li **offline** (mon rendu).
3. **Phase 2a** : tu fais un savestate au load-screen ; j'injecte le package SPK Chun-Li → tu regardes.
4. Itérer **offline** d'abord à chaque bug (plus jamais 43 essais in-game).

## 6. Inconnus restants (bornés)
- Reproductibilité du pnach v7 sur cette ISO (Phase 0 tranche).
- La dé-composition ring→pool (dédup) doit matcher ce que le builder attend (validable offline).
- Calibration scroll par stage (CAVE3 v7 était pour Blanka ; générique = à dériver).
- `0xb674f8=1` dans un savestate load-screen déclenche-t-il bien le layout ? (Phase 2a tranche.)
