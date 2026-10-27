# Packer de stage cross-stage — recette validée (2026-09-06)

> Comment construire un package portant N'IMPORTE quel stage z5 (Upper) dans z9 (Hyper).
> Recette dérivée + validée contre le vrai e527 (Blanka) et généralisée (Chun-Li). Outils :
> `legacy/tools/stage_packer.py` (dé-composeur), `legacy/tools/z5_stage_extract.py` (extraction).

## Principe (plus simple que le remap-dans-le-trou de v7)

v7 remappait les tuiles décor dans un « trou » bank (0x2c0000) pour économiser la place au bake,
MAIS ne copiait qu'une partie → **résidus** (tuiles décor manquantes rendues avec le contenu z9).
**Notre approche : copier les VRAIES tuiles décor** (celles qui diffèrent entre z5 et z9), aux
indices natifs. Plus simple, et **corrige les résidus de v7**.

## Recette (4 étapes, toutes validées)

### 1. Dé-composer le ring → pool + liste  ✅ (brique faite, `stage_packer.decompose`)
- Ring composé (SCR2 `0xa24000` / SCR3 `0xa28000`, z5) → pages de pool dédupliquées + liste de sels.
- z5 streame (pas de pool natif) ; le composeur z9 veut un pool → on dé-compose. Re-compose exact.
- **Placement** : pages dans les slots pool LIBRES de z9 (SCR2 → slots 1-4 + ciel 0x10 ;
  SCR3 → slots 0xe+). La **liste est décalée** en conséquence (ex. SCR3 : `sel += 0xe`).
- Chun-Li : SCR2 16→5 pages, SCR3 64→16 pages.

### 2. Tuiles décor à copier  ✅ (validé, généralise)
- Collecter les tuiles référencées par les pages (SCR2+SCR3).
- Diff **bank z5 (0xd35800) vs bank z9 (0xdb4000)** à ces indices → les tuiles qui **diffèrent**
  = à porter (les identiques sont partagées, rien à faire).
- Ces tuiles forment **quelques plages contiguës** (Blanka : 4 plages/31Ko ; Chun-Li : 6/27Ko).
- **Copier ces plages** de la bank z5 → bank z9 (mêmes indices).
  - Blanka : `0x63d-0x833`, `0xc1d-0xc20`, `0xe99`, `0x4fcc-0x51b2`.
  - Chun-Li : `0x3ba-0x3e4`, `0x63d-0x833`, `0xc10-0xc20`, `0xc80`, **`0x1071-0x107c`** (taï-chi!), `0x5382-0x54aa`.
- ⚠️ à confirmer au test : ces plages = tuiles de STAGE de z9 (remplacées, OK), pas le HUD
  (indices dédiés distincts). Très probable, à valider in-game.

### 3. Palettes  (straightforward)
- Copier les rangées palette du stage (source `0x6fa460` z5) vers les blocs z9
  (`0x660660`/`0x662680`/`0x6646a0`, cf. blueprint) + rows par couche (SCR2 0x40-0x5f, SCR3 0x60-0x7f).

### 4. Assemblage + cave data-driven  (à BUILDER — reste)
- Package = {pool pages, liste, table de plages-tuiles {dst_bank, taille, data}, palettes}.
- **Cave data-driven** : lit la table de plages → copie chaque plage dans la bank ; copie le pool
  aux slots ; écrit la liste ; copie les palettes ; puis re-layout. (≈ cave v7 mais générique :
  au lieu d'offsets Blanka codés en dur, lit la table du package.)
- Injecté au **load-time** (slot-11 AFS, cf. Phase 0) ou savestate load-screen.

## Bonus intégrés « gratuitement »
- **Anim taï-chi** : les tuiles de pose (`0x1071-0x107c`) sont dans la plage 5 → **portées d'office**.
  Reste juste le mini-animateur cave (écrire `base+pose×0xC` dans les 48 cellules ring, cf.
  `ANIMATION-et-Finitions.md` §3ter).
- **Auto-P2** : lire `0xb88916` (perso P2) → table `{perso→stage}` → charger le bon package.

## État
- Étapes 1-2 : **conçues et validées** (dé-composeur vérifié, plages tuiles généralisées).
- Étape 3 : mécanique.
- Étape 4 : **le build restant** (assembleur + cave générique + inject + test). La partie
  analytique/RE dure est FAITE ; reste de l'ingénierie itérative.
