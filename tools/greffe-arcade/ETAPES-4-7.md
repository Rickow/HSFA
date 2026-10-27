> **État au 2026-10-25 : greffe en pause.** Le balayage sur la base v151 régresse (fins 04 Z/Z2/Z3, 09 Z2, 03 Z). Pistes, dans cet ordre : e9s, puis `D2=0`, puis `TEXTES_LU` / `BLOC_RESTES`. La priorité du projet est aux défauts MAX.

# Greffe Arcade (voie B) — étapes 4 à 7 : fichiers à verser au dépôt

Ce dossier contient ce que la session greffe propose d'ajouter au dépôt. Aucun fichier de jeu n'y figure.

## Contenu

| chemin | contenu |
|---|---|
| `patches/traducteur/greffe-arcade-v151.patch` | Copie du traducteur de la greffe (`untranspile3`) sous forme de diff contre l'étiquette `v151` de `scripts/untranspile` (`b9e0271`). Sans les variables `HSFA_GREFFE_*` ni `RESERVE_MAX`, le traducteur patché redonne les références v151 (Hyper `39985037`, Upper `0b8ecca2`). |
| `tools/greffe-arcade/` | Outils modifiés ou ajoutés depuis la dernière publication (mêmes dossiers que dans le dépôt ; les fichiers identiques au dépôt sont omis). |
| `tools/fbneo-hsfa/paquet_fbneo-ro9a.diff` | Entrée `ro9a` (pilote `sfa3hahsfa`, patchs 0008/0009 du cœur) pour `paquet_fbneo.py` du dépôt (`7b44980`) : `hsfa_trous.bin`, région graphique de 48 Mo, chemins des outils par `HSFA_OUTILS`. |

## Ce que fait le traducteur patché

- Bloc de données de la greffe dans ses fenêtres 68K (`HSFA_GREFFE_X`, `HSFA_GREFFE_FEN`), avec ses plages dans `plages_conv()` et dans les blocs de RETAG24 (`RETAG_GREFFE=0` pour les retirer).
- Registres des plans `$804200-$804205` (`HSFA_GREFFE_PLANS`).
- `RESERVE_MAX=20000` (décision D3) : zone `$3A0000-$3BFFFF` laissée vide pour le code MAX ; la fin des données part dans le bloc externe `$940000`, les tables d'animation natives descendent d'autant.

## Interrupteurs de l'étape 7 (défaut entre parenthèses)

Dans `etape3/force3.py` :
- `CONT_GREFFE` (1) : sous-états de la barre « CONTINUE » greffés (0x17BD90, 0x17BFF0) ;
- `FIN05_GREFFE` (1) : acteur de la fin de 05 (0x2139C0, 0x21AB10, 0x20FFF0, 0x2100C0, 0x2101E0).

Dans `etape2/donnees2.py` :
- `DESC_FIN` (1) : champ +$18 des descripteurs d'acteurs de fin jamais relogé (`donnees/ptr_exclus_desc.txt`) ;
- `BANQUES_LU` (1) : banques d'animation T_619B50 copiées jusqu'à la dernière animation lue, avec des creux réutilisés ;
- `TEXTES_LU` (1) : banques de textes T_614E10 copiées jusqu'au dernier texte lu (fin de 17) ;
- `BLOC_RESTES` (1) : la place perdue avant chaque coupure du bloc est réutilisée ;
- `REUTIL_VOISIN` (0).

Dans `etape3/greffe3.py` :
- `ANIM24` (1) : pointeur d'animation 24 bits de 0x20EAD0 avec son étiquette 68K ;
- `MENU_ARCADE` (1) : entrée ARCADE accessible dans le menu du titre d'Hyper ;
- `D2` (1) : drapeau « partie Arcade » en `$FF7E00` ;
- `D3` (1) : `RESERVE_MAX=20000`, 2ᵉ fenêtre de la greffe en `$C60000`.

## Usage

`outils/construit_e3.sh NOM ["VARS"]` construit une ro9a. `outils/balayage_liste.sh NOM PREFIXE` balaie les 85 combinaisons perso × version sélectionnables (MAME, 3 parties en parallèle). `etape4/tableau_fins.py PREFIXE` dresse le tableau.

Le zip du cœur se construit avec `paquet_fbneo.py ro9a` ; la partie Arcade dans le cœur avec `outils/fa_coeur.sh`. État détaillé : `<workspace>/work/greffe_arcade/ETAT.md`.
