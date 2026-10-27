# Persos MAX dans Upper : données fournies par la session MAX (2026-10-11 → 2026-10-17)

Réponses aux questions de l'agent d'intégration HSFA (`MAX=1`, Eagle `$26`, Maki `$27`, Yun `$2D`, Ingrid `$2E` dans
Upper). Adresses PSP = adresses de nos outils (base 0 de l'EBOOT) ; adresses PS2 d'Upper : fichier ro5 = PS2 − 0x1F0000.
Outils dans `max/outils/` ; sorties dans `~/.cache/sfa3max/` (hors dépôt).

## Code des persos

- **Gestionnaires rangés AVANT la racine** : chez les persos MAX, le module `[racine(c), racine(c+1))` contient la
  racine de c, son code atteint, puis les gestionnaires de c+1. Coupure = fin de la dernière fonction atteinte depuis la
  racine sans sortir du module (Balrog (alt) `$25` → `0x1B0088`). `rosette_code/brouillons.py` (`bornes_max`).
- **Créneau de délai pointé par une donnée** (`0x1B3450`, mot `0x2C8ED0` ; aussi `0x150450`) : ce n'est pas un début
  de fonction (`tools/max/charcode2.py`).
- Fonctions écrites à la main par l'agent d'intégration, reprises en disposition arcade : `rosette_code/gestionnaires_main.s`.

## Données de combat

- **Attaques : octets `$12` et `$14` ×2 dans l'arcade** (sous-type de l'étincelle d'impact). Vaut aussi pour les attaques
  des projectiles (Hadoken de Ryu : PSP `0x2830AA` = `$72DE8` de `sfa3ud`, seuls écarts) : `rosette_code/projectiles_max.py`.
- **Yun, entrée [6]** : init `0x1BF944`, 17 appels directs à `0x6A638` au lieu de `0x6AB48(objet, id, liste)` ;
  élément Yun = élément standard − 5 pour tous les champs (`rosette_code/yun_entree6.md`).
- **Jauges** (routine PSP `0x6099C`, indice `+0x152`) : garde `0x21D3A0[ID]`, seuil d'étourdissement `0x21D3CA[ID]` ;
  tables identiques à celles d'Upper `0x74C680` / `0x74C6A8` lues dans l'ordre BRUT du fichier. MAX : garde 40 ;
  seuil Eagle 72, Maki 68, Yun 64, Ingrid 68.

## Graphismes

- **Palettes d'Ingrid** : 48 = 6 groupes de 8 (sprites : sous-palettes 0-3 ; 4-7 = teintes bleues inemployées par les
  frames) → 6 × 5 pour Upper (`convert/palettes_ingrid_upper.py`).
- **Visages de la barre de vie** : `pit_e.pac`, frames `0x17D` (J1) / `0x1AA` (J2) + octets `0x222D76[perso]`
  (routine `0x8B0EC`), palettes du perso (`convert/hud_max.py`). Upper : tables `0x95C8E0` / `0x95CA30` / `0x95CB80`.
- **Noms de la barre de vie** : texte de la police sur PSP ; pour Upper, 64×16 dans `hsfa_plans.bin` (code
  `T_95C700[ID]` + `$1C00` + `$8000`), petites capitales, lettres découpées dans les noms d'Upper ; positions : J1
  x = 3 − 1re colonne du texte, J2 x = 381 − dernière colonne (règle vérifiée sur tous les noms) (`convert/hud_noms_max.py`).
- **Aperçu de l'écran de sélection** : PSP `0x99074`, animation `0x2256C0[perso]` (pas de 8 o) dans `select_e.pac`
  jeu 0, palette `0x538 + perso × 6 + couleur` (Ingrid : 2 par couleur) ; Upper : `T_97CA90` (`convert/apercu_selection_max.py`).
- **Citations** : table PS2 `0x67E2A0` = 40 mots relatifs à la table ; bloc = 8 mots relatifs au bloc (1er = 18),
  2 octets nuls, 8 citations (`convert/citations_max.py`).

## Voie B (Hyper)

- Formats de combat Upper = Hyper ; `$2B8` d'Hyper = 3 × 48, copies de pas dont seul l'octet +8 (jeu de boîtes)
  change, avec deux jeux ajoutés par perso (A : sans boîte de corps, B : une seule). Règle des copies et variante des
  tables MAX : `rosette_construction/FORMAT-UPPER-HYPER.md`, `rosette_code/anims_hyper_max.py`.
