# Données de combat : Upper (ro5) ↔ Hyper (ro9) — première mesure (2026-10-11)

Demande HSFA (transfert des persos MAX vers Hyper). Mesure sur **Ryu** (SFA3), modules
`anthology_extract/decompressed/ro5_usa_prog68k.bin` et `ro9_usa_prog68k.bin` (fichier = adresse PS2 − 0x1F0000).
Méthode : pierre de Rosette (pixels des frames, banque e355 pour les deux), puis remontée frames -> pas -> tables -> bloc.

## Ce qui est IDENTIQUE
- **Frames** : 317 / 335 frames des animations de Ryu d'Upper se retrouvent OCTET POUR OCTET dans Hyper (zone PS2
  0x6BD5EA-0x6C1A68), type 2, mêmes codes locaux à la banque e355. Seul le fichier des positions change : **547**
  (banc ro9 `ext_c84000.bin`, $C84000) au lieu de **390** (`ext_b04000.bin`, $B04000).
- **Pas d'animation** : 20 o, même disposition (durée, drapeaux, …, pointeur de frame en +4, boîtes A/B/C). Ex. garde
  de Ryu : Upper pas -> frame $7A28A6 ; Hyper pas 0x6B40F8 -> frame 0x6BD5EA (même frame).
- **Tables d'animation** : mots relatifs au DÉBUT de la table, comme dans Upper (Hyper $2B0 de Ryu = 0x6B3CA0 ;
  0x6B3CA0 + $458 = 0x6B40F8). Sur les n° communs : 197 animations identiques (frames et durées), 16 différentes
  (ex. la garde, plus longue dans Hyper).

## Ce qui DIFFÈRE
- **Nombre d'entrées** : Ryu Upper $2B0/$2B8/$2B4/$2BC = 76/48/55/34 ; Hyper = 76/≥48/≥72/≥36 (tables prolongées ;
  bornes mesurées approximativement : à recompter avec les vraies tailles).
- **Bloc par perso** : mêmes lignes de 16 o ($2B0, $2B8, $2B4, $2BC), mais **nombre de lignes variable** : Ryu Hyper
  0x6B3C10 = 9 lignes (3 séries de 3 ismes : lignes 4-6 changent $2B4/$2BC, lignes 7-9 changent $2B0), Upper = 3 lignes
  (T_749838). Le choix de la ligne n'obéit donc pas au seul $132 (0x10 / 0x20) d'Upper.
- **Table des blocs** : Hyper **0x6A7A94** (128 places ; 0-37 persos SFA3 ; 38-41 = bloc de Ryu en remplissage = places
  libres pour $26-$29 ; 48-127 autres séries) ; Upper **T_749838** (40 places).
- ⚠ Piège rencontré : un motif de pas (durée 5, mêmes boîtes) est COMMUN à plusieurs persos ; en Hyper, la 1re
  « garde » trouvée par ce motif (0x5D45B0, table à triplets de mots par isme) n'était PAS celle de Ryu. Toujours
  identifier par les PIXELS des frames.

## Conséquence pour MAX (provisoire)
Frames (F%02X_n), pas de 20 o et tables ANIM_xx / FIN_ANIM_xx : **même format** dans Hyper. À adapter : le bloc par
perso (nombre de lignes / indexation propre à Hyper), la place dans 0x6A7A94 (38-41), et le fichier des positions si
on range les positions comme Hyper (nos frames portent leurs propres listes POS : sans objet). La cause du plantage du
K.O. 0x268AB0 n'est donc probablement PAS le format des frames ni des pas : plutôt l'indexation du bloc (ligne
d'isme) ou une table propre à Hyper -> à confirmer sur le cas précis.

## Extension à tous les persos SFA3 (`upper_hyper.py`, sortie ~/.cache/sfa3max/rosette/upper_hyper.json)
- **Animations identiques au même n° (1re ligne du bloc, 4 tables)** : **8 109 / 8 315 = 97,5 %** (frames comparées par
  leurs octets, positions exclues). Écarts les plus nets : Dhalsim $0F (164 / 216), Gen $11 / $13 (260 / 276),
  Guile $20 (181 / 188).
- **Lignes du bloc** : Upper toujours 3 ; Hyper 3, 6 ou 9 (6 : Ken, Chun-Li, Bison, Sagat, Dhalsim, Zangief, E.Honda,
  Blanka, Vega, Guile, Balrog alt… ; 9 : Ryu, Evil Ryu, Shin Akuma… ; à confirmer : le compte s'arrête au premier long
  hors module ou au début d'un autre bloc).
- **Tailles des tables** : $2B0 et $2BC identiques (sauf Blanka $2B0 78 -> 84) ; $2B4 souvent prolongée dans Hyper
  (+0 à +36).
- **$2B8 d'Hyper = 3 sous-tables de 48 entrées, VÉRIFIÉ** (mot 144 = 0, début des pas, comme le mot 48 d'Upper) :
  - la table $2B8 est la même sur toutes les lignes du bloc (sauf Chun-Li et Guy : 2 tables alternées, déjà dans Upper) ;
  - sous-table 0 = celle d'Upper : animations identiques 48 / 48 pour tous les persos, sauf Gen ($11 / $13 : 37 / 48) ;
  - sous-tables 1 et 2 : mêmes animations (durées, frames), mais certains pas sont des COPIES qui diffèrent
    surtout par l'octet +8 du pas (1re boîte : 1 419 octets différents sur tous les persos ; ex. Ryu e19 / e23 / e24 :
    +8 = $04 / $04 / $07 en sous-tables 0 et 1, $75 en sous-table 2). Entrées touchées : 19-34 environ ;
  - lecture probable : index = sous-table × 48 + n (sous-table choisie par un mode, à confirmer dans le code).
- Pour un bloc MAX « à la manière d'Hyper » : schéma 3 lignes (ou 6 / 9 si Hyper l'exige), et $2B8 de 144 entrées
  = nos 48 entrées + 2 copies (les pas modifiés des sous-tables 1-2 à reproduire selon la règle de l'octet +8, une
  fois le sélecteur connu), aux places 38-41 de 0x6A7A94.

## Mécanisme établi (BLOC-HYPER.md de l'agent HSFA, 2026-10-11) et règle des copies de pas $2B8
- **Ligne du bloc** (routine 0x2E7C40 = 68K $071C88) : table = 0x6A7D54 si $123 == 2, sinon 0x6A7C94 si $F0 < 0, sinon
  0x6A7A94 ; bloc = table[$102] ; ligne = isme ($132 : 0 = A, < 0 = X, > 0 = V). Les 6 / 9 lignes mesurées plus haut ne
  sont que des groupes de 3 visés par des entrées différentes des 3 tables (pas de compteur de lignes).
- **$2B8** : index = n + 48 × s (0x2B8E10, champs de la VICTIME) : s = 0 coup ZERO 3 ; s = 1 coup d'une version
  ancienne ($328 ≠ 0, $28D = 0) ; s = 2 enchaînement de custom combo ($28D ≠ 0).
- **Octet +8 du pas = jeu de boîtes** (table $88 du perso, 0x6A6DD4[$102]). Hyper ajoute DEUX jeux par perso en fin de
  table : A = aucune boîte de corps, B = une seule boîte de corps (Ryu $74 / $75, Ken $6F / $70, Chun-Li $78 / $7A…).
- **Règle des copies** (mesurée sur les 33 blocs distincts ; majorité) :

  | entrée | sous-table 1 (version ancienne) | sous-table 2 (custom combo) |
  |---|---|---|
  | 19, 23, 24, 28 | tous les pas sauf le 1er -> A | tous -> B (20 blocs ; 13 blocs inchangés) |
  | 29 | inchangée | tous -> B (28 / 33) |
  | 32 | tous sauf le 1er -> A | tous -> B (21 / 33) |
  | 33 | tous -> A | tous -> A |
  | 34 | dernier pas -> A | tous -> B (20) ou pas 0-1 -> B (10) |
  | 22 | tous sauf le 1er -> $06 (jeu existant) | idem |
  | 27 | tous -> $06 | idem |
  | autres | identiques (même pointeur) | identiques |

- **Places $26-$29** : Hyper ET Upper y pointent sur Ryu, SAUF **$27 = bloc du perso $1E** dans les 3 tables d'Hyper
  et dans T_749838 d'Upper (0x8D9730). À écraser pour Maki dans les deux jeux.
- **Recette MAX (Hyper)** : 3 lignes (A, X, V), les 3 tables 0x6A7A94 / 0x6A7C94 / 0x6A7D54 aux index $26-$29, $2B8 de
  144 entrées = nos 48 + 2 copies selon la règle ci-dessus, et 2 jeux de boîtes ajoutés à la table $88 du perso.
- **Généré (2026-10-11)** : `rosette_code/anims_hyper_max.py` -> `anims_hyper_{eagle,maki,yun,ingrid}.s` (REMPLAÇANTS de
  `anims_XX.s` pour Hyper : mêmes étiquettes, $2B8 = 144 entrées, copies H1_/H2_ après les pas d'origine) et
  `symboles_anims_hyper_max.s` (à inclure À LA PLACE de `symboles_anims_max.s`). 19 entrées copiées par perso (9 en s1,
  10 en s2), +1,4 à 1,5 Ko ; vérifié par vasm : sous-table 0 = $2B8 d'origine 48 / 48. Les jeux de réaction $04/$06/$07/$08
  des persos MAX ont la même numérotation que l'arcade. À définir à l'intégration : `BOITES_A_xx`, `BOITES_B_xx`.
