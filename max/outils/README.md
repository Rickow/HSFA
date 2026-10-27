# Outils MAX (PSP → CPS2)

Scripts Python de la session « MAX ». Aucun extrait de jeu ici : tout se régénère depuis vos propres copies.

## Variables d'environnement

| variable | contenu |
|---|---|
| `SFA3MAX_EBOOT`, `SFA3MAX_ISO`, `SFA3MAX_PAC_DIR`… | voir `tools/max/README.md` (`paths.py`) |
| `ANTHOLOGY_DIR` | conteneurs extraits de l'Anthology (`decompressed/ro3_usa_prog68k.bin`) |
| `HSFA_WORK` | dossier `work/` du banc HSFA (`cps2/sfa3_prog.bin` = programme arcade déchiffré, `mame/banques/`, `mame_ro5/` = banc d'Upper, `xdata/X_DATA.BIN`) |
| `HSFA_WORK_RO5` | banc MAME d'Upper (défaut `$HSFA_WORK/mame_ro5`) |
| `HSFA_TOOLS`, `GHIDRA_PROJET` | JDK et Ghidra (défaut `tools/`), dossier du projet Ghidra de l'EBOOT (`ghidra/`) |

Python : celui de l'environnement HSFA (capstone, numpy, pyghidra).

Les caches et sorties vont dans `~/.cache/sfa3max/` (hors dépôt).

## Dossiers et ordre de régénération

1. `frames289/` — format des frames de l'Anthology et appariement des frames PSP ↔ module (`frame_map.py`).
2. `convert/` — conversion PSP → formats CPS2 / Anthology : `convert_max.py` (banque, frames, scripts, sections ;
   écrit `animations.json` via `tables_anim.py`), `palettes_max.py`, `textes_max.py`, `test_banc.py`.
3. `rosette_code/` — correspondance du code C du PSP avec le 68K arcade et traducteur :
   - `python tout.py` (≈ 30 min) : API moteur (`api_arcade_psp.json`, votes), champs objet (`champs_votes.json`),
     rapport ;
   - `python tailles68.py`, `python arite.py` : tailles des champs 68K, arité des fonctions moteur ;
   - `python evaluer.py` puis `python apprendre.py` : évaluation sur les persos arcade, apprentissage cumulatif
     (`appris.json`, versionné : correspondances établies) ;
   - `python tables_explicites.py`, `python brouillons.py` : tables de scripts passées par adresse, ébauches 68K des
     4 persos et inventaire des fonctions moteur à fournir.
   - générateurs de données 68K des persos MAX (sorties `*.s`, non versionnées) : `frames_max.py` (frames),
     `anims_max.py` (tables d'animation `ANIM_xx`), `anims_fins_max.py` (`FIN_ANIM_xx`), `decor_fins_max.py`
     (décors des fins), `acteurs_fins.py` (acteurs des fins), `projectiles_max.py`, `mouvements.py`,
     `champs_projectiles.py`, `appris_acteurs.py` ;
   - écrits à la main (versionnés) : `moteur_max_main.s` (fonctions moteur PSP non traduisibles),
     `acteurs_fins_main.s`, `symboles_externes_max.s` (symboles fournis par l'intégration) ;
   - `gestionnaires_main.s` : fonctions écrites à la main par l'agent d'intégration HSFA (disposition arcade) ;
   - `anims_hyper_max.py` : variante Hyper des tables d'animations (`$2B8` à 3 × 48, voie B) ;
   - `./assembler.sh [dossier]` : assemble l'ensemble (vasm) et regroupe les erreurs.
   Les fichiers générés (`*.json` sauf `appris.json`, autres `*.s`) ne sont pas versionnés.
4. `convert/` (fins) — `fins_max.py`, `convertir_fin.py`, `script_fin.py`, `dictionnaire_fins.py`, `rosette_donnees.py`
   (acteurs des fins : animations Upper retrouvées par les images, invités, entrées de décor) ; portraits, noms,
   icônes, citations (`portraits_*.py`, `noms_max.py`, `icones_max.py`, `citations_max.py`) ; barre de vie : visages
   (`hud_max.py`) et noms (`hud_noms_max.py`) ; aperçu de l'écran de sélection (`apercu_selection_max.py`) ; palettes
   d'Ingrid au schéma d'Upper (`palettes_ingrid_upper.py`). Détails : `../notes/max-integration-upper.md`.
5. `rosette_construction/` — pierre de Rosette de CONSTRUCTION : frames et animations PSP ↔ Upper au pixel près,
   règles de construction, chaîne images -> code, comparaison Upper ↔ Hyper (`README.md`, `FORMAT-UPPER-HYPER.md`).
6. `ghidra/ghidra_decomp.py` — décompilation de l'EBOOT PSP (Ghidra + extension Allegrex) par adresse.

Notes associées : `../notes/`.
