# Préparation du proto cross-stage — tout ce qui est prêt HORS JEU (2026-08-31)

> Objectif de cette passe : ratisser tout le travail faisable sans PCSX2, pour que la reprise
> (avec pad) soit « charger et regarder ». Voir `CARTO-Cross-Stage-Tables.md` (RE complète) et
> `CARTO-Caves-Memoire.md` (carte des caves).

## 0. STATUT — la chaîne chemin A est VALIDÉE hors jeu ✅

Un **rendu offline** du stage Upper extrait (bank + palette + ring) prouve que l'extraction et
le format sont corrects, **sans émulateur** :
- **Bank** : la planche de tuiles montre « CAPCOM », « SFA3 », lettres nettes → **format tuile
  8×8 4bpp LSB correct**, bank bien extraite.
- **Palette** : couleurs présentes via la formule exacte de `FUN_1d1300`.
- **Ring** : rendu en pages (SCR2 = 4×4 pages de 16×16) → **structure de temple Chun-Li
  reconnaissable**. Géométrie du ring = pages, pas linéaire.
- ⟹ Tuiles ✓ palette ✓ bank ✓ ring ✓. **Les données à transplanter sont bonnes.** Reste
  uniquement la mécanique d'injection in-game à tester.

Previews : `<workspace>/stage_packs/*.png` (banksheet / scr2 / scr3, pour Chun-Li et Blanka).

## 1. Outils créés (Linux, dans `<workspace>/scripts/`)

| Script | Rôle | Lancement |
|---|---|---|
| `decomp.py` | décompile des fns R5900 d'un dump | `python decomp.py <dump> <va…>` |
| `z5_stage_extract.py` | extrait un stage Upper (ring+palette+bank) d'un dump combat z5 | `python z5_stage_extract.py <ee_z5xxx.bin> "<nom>" stage_packs` |
| `render_stage.py` | rend un stage extrait en PNG (validation offline) | `python render_stage.py stage_packs/<nom>` |

Tous après `source <workspace>/env.sh`. Dumps z5 dispos : `tmp_hdd/ee_z5chunli.bin`,
`ee_z5blanka.bin` (+ `z5_*`). Packs déjà produits dans `stage_packs/` (Chun-Li, Blanka).

## 2. Données extraites (par stage, dans `stage_packs/`)

| Fichier | Contenu | Taille |
|---|---|---|
| `<nom>.ring_scr2.bin` | ring SCR2 composé (z5 `0xa24000`), `{tile\|0x1000, attr}` | 0x4000 |
| `<nom>.ring_scr3.bin` | ring SCR3 (z5 `0xa28000`), `{tile, attr}` | 0x18000 |
| `<nom>.ring_scr1.bin` | ring SCR1 (ciel/uni) | 0x4000 |
| `<nom>.palette.bin` | palette source (z5 `0x6fa460`), 128×16 CPS2 4444 | 0x1000 |
| `<nom>.bank.bin` | bank de tuiles BG (z5 `0xd35800`) | 0x2d8000 (2.98 Mo) |
| `<nom>.manifest.json` | adresses source + amplitude n° tuiles | — |

## 3. Découvertes de cette passe

- **Bank BG z5 = `0xd35800`** (pointeur `0x1dc2e4` = struct BG `+0x34`). z9 = `0xdb4000`.
- **4 banks gfx séparées** : `+0x34` BG (décor), `+0x38`/`+0x3c`/`+0x44` = persos/sprites.
  ⟹ **repointer `+0x34` ne change QUE le décor** → persos/HUD a priori épargnés (à confirmer
  in-game). z9 : BG `0xdb4000`, sprites `0x108c000/0x112b800/0x11cb000`.
- **Pas de remap nécessaire pour le proto** : on transplante la bank ENTIÈRE (2.98 Mo, couvre
  tous les n° de tuiles jusqu'à ~0x16c00). Le remap compact (v7) ne sert qu'à réduire la taille
  pour le bake ISO.
- **Format tuile** : 8×8, 4bpp, 2 px/octet, nibble bas = pixel pair (PS2 INDEX4LSB).
- **Formule palette** (de `FUN_1d1300`) : `c = [bri:4][R:4][G:4][B:4]` ; `bri=(c>>12)+0x10` ;
  `canal = nibble * bri * 0x11 / 0x1f`.
- **Attribut de cellule** (validé sur le rendu) : rangée palette = **`base_couche + (attr & 0x1f)`**
  avec `base` = **`0x40` (SCR2)** / **`0x60` (SCR3)** (cf. doc rangées 0x40-0x5f / 0x60-0x7f) ;
  **`attr & 0x20` = flip H**, `attr & 0x40` = flip V ; `attr == 0xffff` = cellule vide.
  → avec ça le rendu offline de Chun-Li est net (temple, piliers rouges/or, ciel bleu).

## 4. Recette d'injection du proto (chemin A) — quoi écrire où en z9

Par-frame (cave sur `0x1d0750`, patron `asm_v7pg.py`), en combat :
1. **Bank** : copier `<nom>.bank.bin` en RAM libre (**`0x1690000+`**, PAS `0x1580000` = widescreen)
   puis **repointer** `0x1dc2e4` → cette adresse. (Ou écraser `0xdb4000` directement si libre.)
2. **Ring** : deux options —
   - (a) **écraser les pages de pool** SCR2 `0x640960+sel*0x300` (sels `0xd-0x10`) et SCR3
     `0x643c60+sel*0xc0` (sels `0x1c-0x1d`) avec les pages découpées du ring z5 → le builder dur
     z9 compose + scrolle ; OU
   - (b) **écraser le ring** `0xba4000`/`0xba8000` directement avec `ring_scr2/3.bin` (plus simple
     à tester, mais re-composé au re-layout → à réappliquer par-frame).
   → **Commencer par (b)** pour valider visuellement vite, puis passer à (a) pour le scroll propre.
3. **Palette** : écrire `palette.bin` → `0xbac000` (source), le convertisseur `FUN_1d1300` fait le
   reste. (Ou repointer `[[0x1dc070]+0x14]`.)
4. **Gating** : uniquement en combat (ne pas toucher menus/écrans).

⚠️ La bank (2.98 Mo) ne rentre pas dans un pnach texte → pour le proto, l'injecter via **savestate
patché** (méthode la plus simple sans loader) OU via le loader AFS (`FUN_154c9c`, cf. CARTO §6) OU
bake ISO. Le pnach ne convient que pour les petits blobs (ring, palette, pointeurs).

## 5. Checklist de test (jour du pad)

1. Activer les cheats : PCSX2 → `EnableCheats=true` (config `~/.config/PCSX2/PCSX2.ini`).
2. Générer un **savestate combat Hyper** (stage résident) → extraire eeMemory (`p2s_ee.py`).
3. Injecter (option b) : écrire `ring_scr2/3.bin`→`0xba4000/0xba8000`, `palette.bin`→`0xbac000`,
   `bank.bin`→`0xdb4000` (ou RAM libre + repoint), dans le eeMemory, **repacker le savestate**.
4. Charger → **regarder** : le décor Chun-Li apparaît-il ? persos/HUD intacts ? couleurs OK ?
5. Itérer : si couleurs fausses → affiner la rangée palette par cellule (attr bits) ; si persos
   cassés → la bank BG n'était pas isolée (revoir +0x34 vs +0x38) ; si géométrie fausse → passer
   à l'option (a) pages de pool.

## 6. Risques / à confirmer in-game (rien de bloquant identifié)

- **Isolation bank BG** (`+0x34` seul) : très probable mais non testé — le seul vrai inconnu.
- **Scroll** : validé en théorie (§3ter carto) ; l'option (a) pages de pool le rend natif.
- **Objets animés** (serpent, feu, taichi) : hors périmètre (bloc E) — resteront absents/figés.
- **Repacker de savestate** : à écrire (inverse de `p2s_ee.py` : re-zip zstd de eeMemory dans le
  `.p2s`) — faisable hors jeu, à préparer aussi.

## 7. Prochaines actions hors-jeu encore possibles (si on continue)

- Écrire le **repacker de savestate** (`.p2s` ← eeMemory modifié) → prépare un savestate de test
  prêt à charger.
- Écrire le **découpeur ring→pages** (option a) + le générateur de pnach pour ring+palette.
- Affiner l'assignation **palette par cellule** (mapping attr→rangée) sur le rendu offline.
- Décompiler le **repacker AFS** si on vise le loader `FUN_154c9c` plutôt que le savestate.
