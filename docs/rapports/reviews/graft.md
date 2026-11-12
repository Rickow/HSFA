# Critical review of the graft "Hyper + Arcade" (ro9a36 / ro9a37, 2026-11-11 / 12)

**Summary (English).** Review of the graft of Upper's Arcade mode onto Hyper (route B): two static passes (11/11 on
ro9a36, 12/11 on ro9a37: relocation of data R1-R5, graphics banks B1-B3, shared tables and ids T1-T3 / X1-X7, state
transitions E1-E4), bench trials (`RESULTATS_ESSAIS.md`) and the "blur zones" pass (`flou/`); the seven files are below.
Workshop: `<workspace>/work/revue_greffe/` (trial scripts `essais_demain/` not merged).
- **Findings**: R1 295 cells `(word, $00A0-$00A7)` relocated +$18 as RAM pointers without proof; R2 26 word pairs
  relocated as data pointers; R3 142 pointers PROVEN by Upper's conversion log left raw; R4 216 relocations in two
  regions without any proof; X2 a MAX base id ≥ `$28` overflows per-character tables; X6 non-injective homologues.
- **Confirmed on the bench**: A2a (wrong tiles in the select after a VERSUS on an Upper stage), E2b (2-3 frames of
  wrong tiles after a new challenger, benign), X6 (13 real entries in the endings 07 0F 19 1A 1C), X2 (`$28` / `$2D`
  crash in the map or face-off, `$26` passes); infirmed: E1, E2, E3, E4, R3 c (128 cells: 0 pointer); the 12 stages with
  "random" objects are not a data defect (draw, fight reaction, bench).
- **Fixed in ro9a38 (journal §223)**: R3 (`R3_CREUX=1 R3_CIBLES=1`, 142 → 0), X6 (`X6_FINS=1`), A2a (`A2A_VS=1`),
  E2b (`E2B_DEFI=1`); all at 0 = ro9a37 byte for byte; 85/85 endings, VERSUS and stages unchanged.
- **Still open**: X2 MAX ids (code behind `X2_TABLES=0`, not in ro9a38; full list in [max-tables.md](max-tables.md));
  R1 / R2 / R4 exclusion lists not applied (no visible effect on the stage bench, undecidable in play; cell `917350` is
  data, harmless); residual differences of stages 4A, 22 / 26, 40 and class `$11` with a fixed seed; B1 `DECOR_E0`
  chooses by palette (to check); T2 five PS2 engine calls without hook; about 2,700 "absent target, no proof" cells
  not sorted; the 29 stubs are not seen by `index_tables.py`.
- **Tools kept**: [`tools/reviews/graft/`](../../../tools/reviews/graft/); on ro9a38 `laisses.py` shows no "proof" family.

---

## Original text (French, kept as is)

> Kept as written in the workshop. Only changes: personal paths written `<workspace>/...`, workshop folders written `<workspace>/work/...`. Paths such as `outils/…`, `sorties/…`, `essais_demain/…`, `constr/…` are relative to the review's workshop folder (above); the tools kept are in `tools/reviews/` (see the summary).


<!-- source: <workspace>/work/revue_greffe/RAPPORT.md -->

## File `<workspace>/work/revue_greffe/RAPPORT.md`

# Revue critique de la greffe « Hyper + Arcade » (ro9a36)

> **12/11 : une 2e passe, sur ro9a37, est à la fin de ce fichier.** Elle corrige plusieurs points de la 1re (R3 c, R4,
> T1, E1-E4, piste « objets aléatoires » de R1) et périme ses adresses 68K et ses chemins `ro9a36/`.

Agent `revue_greffe` (sfa3ha), 2026-11-11. Lecture et analyse statique seulement : rien n'est modifié hors de ce dossier,
aucun émulateur, aucune construction. Chaque constat « prouvé » l'est par lecture des données d'Upper, du bloc produit
par la construction figée et du MIPS ; l'effet en jeu reste à confirmer au banc (essai décrit à chaque fois).

Matière :
- code figé : `<workspace>/github/tools/greffe-arcade/construction/ro9a36/greffe/` (`etape2/donnees2.py` = relogement des données,
  `etape3/greffe3.py` = talons et interrupteurs), recette `vars_ro9a36.txt`, relevés `releves_ro9a36/` ;
- construction figée : `<workspace>/work/greffe_arcade/constructions/ro9a36_fige/` (`greffe.json`, `greffe_donnees.bin`,
  `zone_decors.bin`, `b9/carte_image.txt`) ;
- Upper : `<workspace>/work/modules_son/ro5_usa_prog68k.bin` ; les adresses sont des **adresses d'exécution PS2 d'Upper** (fichier +
  `0x1F0000`), comme dans `ptr_exclus*.txt`, sauf mention.

Outils écrits (`outils/`, usage en tête de chacun) ; sorties dans `sorties/`.

## En bref : les constats les plus graves

1. **R1** : tout long de la forme `(mot, $00A0-$00A7)` est relogé comme « pointeur de RAM » (+`$18` sur le mot haut) sans
   aucune preuve : 295 cases, dont ≈ 230 sont des paires de mots (coordonnées, tables de mots, couleurs). 73 sont lues par
   Upper en Arcade ; 28 sont dans la zone des objets de décor ; deux tables sont lues par du code greffé (prouvé).
2. **R2** : 26 autres paires de mots relogées comme pointeurs de données, toutes LUES par Upper (enregistrements de
   sprites, tables de positions, scripts), hors des listes d'exclusion.
3. **R3** : 142 pointeurs PROUVÉS par le journal des conversions d'Upper sont laissés bruts (cible non copiée, ou case
   dans un creux de banque) : en jeu ils sont convertis comme des adresses d'Hyper.
4. **R4** : deux régions entières sans un seul pointeur prouvé reçoivent 216 « relogements » (scripts `0x939790`,
   listes de sprites `0x678066`).

---

## 1. Relogement des données

### Méthode : `outils/classe_relogements.py`

Pour chaque long aligné des 365 régions copiées (758 200 cases), l'outil compare les octets d'Upper au bloc produit
(`greffe_donnees.bin`, `zone_decors.bin`) : différent = RELOGÉ. Il classe la valeur d'origine (donnée, fichier 390, code,
RAM) et pose des marques de contexte : `preuve` (case du journal des conversions d'Upper, `pointeurs_prouves`), `T2`
(dans les paires code/attr d'une trame de type 2, toute taille), `voisin_reloge` (table), `case_lue` / `cible_lue`
(journaux de lecture d'Upper, union des 65), `zone` (zone des décors). Sortie : `sorties/classe.tsv` (95 134 lignes),
bilan `sorties/classe_bilan.txt`. Contrôle : 49 196 données + 5 186 code + 295 RAM relogés, pour 49 177 / 5 161 / 295
dans `greffe.json` (`stat_donnees`).

Lecture du bilan : sur 49 196 pointeurs de données relogés, 25 500 sont prouvés ; les non prouvés ont une moitié basse
uniformément répartie (7 % sous `$1000`), donc sont en grande majorité de vrais pointeurs. Les faux se concentrent dans
quatre familles.

### R1. Classe « RAM » : `(mot, $00A0..$00A7)` relogé en `$00B8..$00BF` sans preuve — GRAVE

- **Site** : `etape2/donnees2.py`, fin de `bloc()` : `elif cl == 'ram' and not (p & 1): q = g.valeur(p, …)`. Aucun
  critère de pointeur n'est appliqué (ni `est_pointeur`, ni preuve, ni voisinage) : tout long pair dont le mot haut vaut
  `$00A0`-`$00A7` (base RAM d'Upper `0xA00000` + `0x80000`) reçoit +`$18` (base d'Hyper `0xB80000`).
- **Mesure** : 295 cases (`sorties/faux_relogements.txt`). 48 sont dans des tables de vrais pointeurs de RAM (voisins
  relogés, moitié basse ≥ `$0E00` : `0x60BE50` = `$A08400/8800/8C00/9000`, `0x615360`…) ; 16 sont ambiguës (`0x6142D0`,
  16 × pas `$10`) ; **231 sont des paires de mots**. `$00A0` = 160 est une ordonnée courante.
- **Preuves** (contexte : `outils/ctx.py ADR`) :
  - `0x615D70` : table de 16 mots `00A0 00A1 009F 00A2 009E 00A3 … 0099 00A8` lue par mot indexé, MIPS d'Upper
    `0x17BFB8` (`lh v1,0(v0)` puis `sh v1,$12(objet)`), routine `0x17BEF0` GREFFÉE (bloc `17bb30-17c850`). Entrées
    1, 5, 9, 13 : `$A1/$A3/$A5/$A7` → `$B9/$BB/$BD/$BF` : la grandeur écrite en `$12` saute de +24 une fois sur quatre.
  - `0x612380` : table de mots `0080 00A0 00C0 00E0 0100 0120 0140 0160`, ajoutée à D2 en `0x104114`, routine des
    classes d'objets de décor GREFFÉE (bloc `fd620-10d0f0`). Entrée 1 : `$A0` → `$B8`.
  - `0x61A188`, `0x61A194`, `0x61A1A8`, `0x61A1B4` : table de paires (x, y) `T_61a180` (l'index `re/` la donne déjà
    comme « PAS des pointeurs », arcade `$0ACE60`) : y `$A0` → `$B8` pour 4 entrées sur 16. Lues par Upper.
  - `0x7469BC`-`0x746A5C` (6 cases) : couleurs des banques de palettes animées (`0x724570-0x749000`) : `$00A2..$00A7`
    → `$00BA..$00BF`. La liste `ptr_exclus_pal` (e39) ne couvre que la classe « donnée ». Lues par Upper.
  - zone des décors : 28 cases. `0x9703EC`-`0x9703FC` : positions `(FFD8,00A5) (FFE8,00A5) …` → y +24 ;
    `0x972C88` : table de décalages 16 bits `001C 0024 … 0098 00A0` (animations d'un objet) : `$A0` → `$B8`, lue par
    Upper ; `0x960D0C`, `0x97097C`, `0x970BD4` : mot d'une suite `0041 0061 0081 00A1 00C1` → `$B9`, lues par Upper.
    Même mécanisme que `0x951724` (corrigé en e43 par une exclusion à la main).
- **Effet en jeu** : objets, acteurs ou couleurs décalés de 24 (pixels ou pas), décalage d'animation faux. Candidat
  direct pour une partie des 12 décors « aux objets aléatoires » et pour les écarts de +24 / +30 images relevés
  (carte, Birdie) : à vérifier.
- **Essai** : construire avec les 231 cases en `PTR_EXCLUS` (`sorties/ptr_exclus_revue.txt`, familles `RAM_FAUX_*`) ;
  comparer le banc des décors (attendu : plus de 28/40 identiques à Upper) et les durées du banc des fins.
- **Correctif de principe** : ne reloger un long de classe RAM que s'il est prouvé (lecture `MOVEA.L` suivie d'un
  accès, à journaliser comme les conversions) ou dans une table de ≥ 3 pointeurs de RAM voisins ; sinon le laisser.
- **Gravité** : haute (231 cases, 73 lues par Upper, 2 tables lues par du code greffé).

### R2. Paires de mots relogées comme pointeurs de données, lues par Upper — GRAVE

- **Site** : `donnees2.py` `est_pointeur` : sans preuve, un long est pointeur si son mot haut ≥ `$60` et son mot bas
  ≥ `$200` (ou constante du code). `FILTRE3` n'écarte que les impairs et les mots bas `$FE00+`.
- **Mesure** : cases relogées, non prouvées, lues par Upper, dont la « cible » n'a jamais été lue : 38 ; 12 sont dans des
  tables de pointeurs (vraisemblables) ; **26 sont des paires de mots** (`sorties/faux_relogements.txt`,
  `DATA_FAUX_PROBABLE_LU`).
- **Preuves** :
  - `0x67929C`, `0x67938C`, `0x67B144`, `0x67B168`, `0x67B10C`, `0x679E00`, `0x67A390`, `0x67B480` : enregistrements de
    sprites de 8 o `(x, code, taille, y)` : `(FFD0,157D,0202,0080)` → taille et y remplacés par `$ADC2,$00C5`.
  - `0x64A5C8` : `(031E, 0080)` dans une liste `(24C8, 031E, x, FFF8)` : même motif que le « bloc blanc du GAME OVER »
    corrigé en e33 dans la seule zone des décors (`ZONE_CIBLES`).
  - `0x61F4E8`, `0x61F4F0` (+ `0x61F4E0` en classe RAM) : table `(0400,00A0,4,0) (0480,0070,8,0) (0500,006C,$20,0)`
    référencée par le code d'Upper `0x4F38E8` : les trois premières paires sont relogées.
  - `0x792B6C` `(8000,0064)`, `0x74EBC4` `(0208,0097)`, `0x76031C` : enregistrements `(dx, dy, 8001, n)`.
  - `0x93D0E0`, `0x93F560`, `0x940164` : fin d'une table d'octets `0E0E` + 1er mot `007E` d'une table de décalages.
  - `0x931688`, `0x931C10`, `0x93B070`, `0x93D054`, `0x93DB8C`, `0x93DC8C`, `0x9434E4`, `0x943C98`, `0x943CD4`,
    `0x91AC20` : mots de scripts (`020A 0080`, `0202 0080`…).
- **Effet** : tuiles, positions ou commandes de script fausses dans des données que la partie Arcade d'Upper lit.
- **Essai** : exclure les 26 cases ; relever les objets (banc `objw`) des écrans d'Upper avant / après.
- **Correctif de principe** : voir R5 (reloger par structure prouvée, pas par forme de la valeur).
- **Gravité** : haute (toutes dans le chemin joué par Upper).

### R3. Pointeurs PROUVÉS laissés bruts — GRAVE

- **Mesure** (`outils/laisses.py`, `sorties/laisses.txt`) : 142 cases du journal des conversions d'Upper gardent leur
  valeur d'Upper dans le bloc. À l'exécution, la valeur brute passe par CONV comme une adresse d'Hyper : données sans
  rapport (c'est le mécanisme des plantages `$A08` des fins 10 / 18).
- **Trois mécanismes** :
  a. **cible jamais copiée (12 cases)** : la fermeture ne suit que les pointeurs des SEGMENTS ; une case qui n'est dans
     le bloc que par le prolongement d'une région (lectures voisines, `LIB_SPANS`, fusions) est relogée « si la cible
     existe », jamais suivie. `0x613208` et `0x613230` : entrée `0x84CBC4` de la table `0x6131F8` (8 pointeurs vers les
     banques, 7 relogés, celui-ci brut ; case et cible lues par Upper). `0x7A0E44`, `0x7A0E6C`, `0x7A0E94`,
     `0x7A0EBC`, `0x7A0EE4` : pointeur `0x7A28A4` de 5 enregistrements d'animation de la banque commune `0x79B680` ;
     la région copiée voisine commence à `0x7A28A6`, **deux octets après la cible** (le premier mot de la structure
     n'a pas été lu par Upper). Cases et cible lues par Upper. + `0x81F4BC`, `0x81F524` (fichier 390), `0x8E5784…`.
  b. **case dans un creux de banque (≈ 130 cases)** : `BANQUES_LU` rend au placement les parties de banque ni lues ni
     segment ; leurs cases ne sont jamais relogées (`dans_creux`). Or le journal des conversions y a vu Upper convertir
     des pointeurs (`0x79C254`, `0x7E07C4`, `0x832E00`, `0x83A1CC`…, `0x89D12C`…, enregistrements de 20 o des
     animations) : ces animations SONT jouées par Upper.
  c. sans preuve mais case et cible lues par Upper, cible non copiée : 128 cases (`sorties/laisses.txt`), la plupart
     des paires de mots (`008C008E`) ; à trier.
- **Effet** : image d'animation lue dans les données d'Hyper → sprite faux ou erreur d'adresse.
- **Essai** : sonde de lecture sur les 12 cases de (a) pendant une Arcade (intermèdes et fins) ; ou construction avec
  `BANQUES_LU=0` pour ces banques et comparaison.
- **Correctif de principe** : toute case prouvée est un départ de la fermeture, où qu'elle soit ; une cible prouvée
  est toujours copiée ; un creux qui contient une case prouvée n'est pas un creux.
- **Gravité** : haute pour (a) (7 cases dans le chemin d'Upper), moyenne pour (b).

### R4. Régions sans aucun pointeur prouvé, relogées quand même — MOYEN

- `0x939790-0x946A12` (54 Ko, scripts : octets de commande `0C02 0600 4500…`) : 196 relogements (73 « code », 61
  « donnée », 62 « RAM »), 0 prouvé ; le seul pointeur du bloc qui la vise est `0x74E8AC` = `(0208, 0094)`, lui-même
  une paire de mots. L'atelier a exclu à la main 39 cases de la région voisine `0x91A8AC-0x92D9F4` ; celle-ci ne l'est pas.
- `0x678066-0x67B53E` (listes de sprites de 8 o) : 107 relogements, 0 prouvé.
- Listes : `sorties/faux_relogements.txt` (`REGION_SANS_PREUVE_*`).
- **Effet** : seulement si la greffe lit ces régions (13 cases lues par Upper). À confirmer par sonde de lecture.
- **Correctif de principe** : une région sans pointeur prouvé ni table de pointeurs → `PLAGES_BRUTES`.

### R5. Faiblesses de structure (pas de défaut restant trouvé, mais rien ne les garde)

- `etape2/paires_sprites.py` ne reconnaît une trame de type 2 que si `n-1 ≤ $80` : le portrait de Bison (146 entrées,
  `0x64B138`) n'était donc pas protégé (défaut de la fin de Ken, corrigé à la main par `64b380`). Avec toutes les
  tailles, l'outil ne trouve plus aucun relogement dans une trame (hors `DECOR_E0`) : rien d'autre à corriger, mais
  la borne est à lever.
- `PTR_EXCLUS` est testé avant `PREUVES` : une case prouvée peut être exclue par une liste à motif (aucun cas aujourd'hui).
- Les quatre listes d'exclusion (≈ 7 500 cases à la main + 145 933 par plages) sont liées aux adresses d'Upper : justes
  tant que le module ne change pas, mais chaque nouvelle région copiée (nouveaux journaux) ramène des faux.

---

## 2. Banques graphiques

Rappel du mécanisme (lu dans `greffe3.py`) : la banque de l'emplacement 0 dépend de la **base de scroll1** : `$0400`
= banque commune d'Upper (f351), `$4400` (alias, combat sur décor d'Upper) et bases d'Hyper = f545 d'Hyper, prolongée
par f351 au-delà de `$33F0` ; `$8300` (scènes 6 / 8) = tuiles d'Hyper + banque d'Upper. Tout objet en emplacement 0
est donc juste ou faux selon la base du moment, pas selon son origine.

### B1. `DECOR_E0` choisit par la palette, pas par l'emplacement réel — À CONTRÔLER

- **Mesure** (`outils/banque_e0.py`, `sorties/banque_e0.txt`) : dans la zone des décors, 7 197 entrées de trames de
  type 2 ; 1 098 ont une tuile < `$33F0` dont l'entrée diffère entre f545 et f351 (« classe B ») ; 140 sont recodées,
  **958 ne le sont pas, toutes parce que leur palette est < `$0F`** (177 trames, `0x97EC6C-0x982C98` surtout ; 149 de
  ces trames sont lues par Upper). Aucune trame n'échappe au recodage pour une autre raison (taille, pointeur).
- **Lecture** : ces trames ont des codes bas (`$03xx-$07xx`) et la palette 0 ou 1 : forme d'objets dessinés avec la
  banque du décor (emplacement 1), où le code est relatif au décor et où f545 / f351 n'interviennent pas. Si l'un de
  ces acteurs est en emplacement 0, ses tuiles sont fausses. Le banc des décors (0 code de classe B restant) ne voit
  que les objets présents aux trois positions relevées, pas ceux qui apparaissent par événement ou au hasard.
- **Essai** : sonde du champ `$1A` de chaque acteur du réservoir `$FFC000` + adresse de sa trame, sur les 12 décors
  ouverts, pendant une manche entière ; croiser avec `sorties/banque_e0.txt`.
- **Correctif de principe** : décider par `$1A` relevé (liste trame → emplacement), pas par la palette.
- **Gravité** : inconnue tant que l'essai n'est pas fait (0 à 958 entrées).

### B2. Objets d'Hyper en emplacement 0 pendant les écrans d'Upper — STRUCTUREL

- Sens inverse du précédent, déjà rencontré trois fois (barre du logo e42, flash de la sélection e40, sortie du
  CONTINUE e46) et corrigé chaque fois par une retouche de base. Tout objet d'Hyper encore vivant (transition, objets
  de manche, compteur) quand la base passe à `$0400` (carte, face-à-face, victoire `PLANS_VICT_U`, fin) est dessiné
  avec f351. Sur 0-`$33EF`, les deux banques diffèrent pour les tuiles de classe B.
- **Essai** : sur une Arcade complète, relever à chaque image (base scroll1, objets actifs d'emplacement 0, origine
  Hyper / copie d'Upper d'après l'adresse de la routine) et lister les couples (objet d'Hyper, base `$0400`) et
  (objet d'Upper, base ≠ `$0400` hors zone des décors).
- **Correctif de principe** : marquer l'origine de l'objet (bit libre de `$1A`, comme la marque `$8000` des bases)
  au lieu de la déduire de la base de scroll1.

### B3. Trames hors zone des décors

- 48 722 entrées de classe B dans les trames copiées hors zone (dont 1 902 à palette ≥ `$0F`) : justes tant qu'elles
  ne sont dessinées que sous la base `$0400` / `$8300`. Celles des intermèdes (sous-état 2 copié d'Upper, joué
  PENDANT la scène de combat, base `$4400`) sont à vérifier en premier : `INTERMEDE_PLANS` est à 0.

## 3. Tables partagées et ids

### T1. Ids MAX : la règle D4 et la base `$116` ne connaissent pas `$2D` / `$2E` — À TRAITER AVANT LES MAX

- `decors/d4/regle_d4_decidee.tsv` (table `T_D4`, 128 octets) : `$26` Eagle, `$27` Maki, **`$28` Yun, `$29` Ingrid**,
  `$2A-$2F` « inutilisé, base Ryu », décor `$00`. Si Yun et Ingrid portent `$2D` / `$2E` (ids annoncés), ils auront
  le décor de Ryu et les lignes `$28` / `$29` ne servent pas.
- Table d'Hyper `T_BASE` (`0x5C5300`) : octets `$26-$2F` = `$00`. Toute lecture relogée de `$102` vers `$116`
  (`patch_116` : 30 INDEX, 48 CMP dans `greffe.json`) donnera **Ryu** pour un perso MAX : citations, rival,
  portraits, fin. La grille `0x5C5380` a des lignes `$28-$2F` non vides (versions d'autres persos).
- Tables d'Upper à 40 entrées lues par les copies avec l'id (`T_61BE10`, tête de `T_72BDF0`) : `$2D` / `$2E` hors
  table. `T_619B50` (46 entrées) : les entrées 40-45 ne sont pas des bases de banque (`$003FF3A0…`).
- Tirage : `T_TIR` a `$40` lignes, pas de tirage pour un id ≥ `$24` : sans risque.
- **Correctif de principe** : fixer les ids MAX dans une seule table (D4, `T_BASE`, tables à 40 entrées prolongées)
  avant l'intégration ; test : chaque table lue par une copie d'Upper avec `$102` ou `$116` listée avec sa taille.

### T2. Appels du moteur PS2 depuis le code greffé : 5 sites sans crochet — FAIBLE, À CONFIRMER

- `greffe.json` `rapport.code_non_decide` : copies `0xE118` (cible `0x155360`), `0xED75F0` (`0x1CB320`), `0xED7620`
  (`0x1CB520`), `0xED7758` et `0xED777C` (`0x118A60`). Ce sont des fonctions de l'exécutable PS2 ; l'image contient
  `JSR $000800` (`carte_image.txt` : « JSR ??? … hors carte ») ; `hooks_fork_ro9.json` ne liste aucun de ces sites
  (ro5 a un crochet « moteur PS2 » pour `0x51208`). Les routines `0x4077C0` et `0x407990` sont du C du portage
  traduit (« résultat natif supposé nul »).
- **Essai** : point d'arrêt sur `$000800` avec l'adresse de retour ; vérifier ce que fait Upper à ces sites.

### T3. Non fait

- Recensement de toutes les tables d'homologues « partagées » (`HOM_PARTAGES_LISTE`, 50 routines) lues avec un index
  différent (cas `ROUND_BEHAVIOUR`, `T_5c5120[$12A]`) : demande, pour chaque routine d'Upper renvoyée à son homologue
  d'Hyper, la comparaison des masques d'index (`ANDI`) des deux côtés. Outil à écrire : pour chaque paire
  (copie d'Upper, homologue d'Hyper) qui lit la même table, comparer la chaîne de calcul de l'index.

## 4. Transitions d'état

Lecture des talons `stub_plans_auto`, `stub_plans_scene`, `stub_scene2_bases` (bases par scène) :

- **E1. Sortie vers `$C` (titre d'Hyper) depuis les scènes 6 / 8 / A** : bases d'Hyper posées tout de suite, VRAM
  encore celle de la scène d'Upper. C'est le défaut du CONTINUE (e46), corrigé seulement pour la sortie vers 0. Sans
  effet si l'écran est déjà noir à ce moment (fondu) : à vérifier sur GAME OVER et sur la fin du générique. Faible.
- **E2. Masque `ANDI #$FFF1,$32(A5)`** (`FLASH_SEL`, `CONT_SORTIE`) : la remise des couches est laissée à Hyper
  (`$32` réécrit à l'init de la sélection) ou à « l'image logique suivante » d'Upper. `COUCHES_UPPER` vaut 0 : aucune
  routine de la greffe ne remet `$32` elle-même. Tout chemin qui sort de la scène 4 à l'image de l'init (nouveau
  challenger pendant la carte) garderait scroll1-3 masqués. Essai : Start J2 à l'image de l'init de la scène 4.
- **E3. Octets de la greffe `$FF7E00` (drapeau ARCADE), `$FF7E02`, `$FF7E08` (`$12A` sauvé), `$FF7E20-23` (tirage)** :
  le drapeau n'est remis à 0 qu'à la sortie vers `$C` par les talons des scènes 6 / 8 / A. Une sortie de l'Arcade par
  un autre chemin (réinitialisation logicielle, mode test) le laisse posé ; `scene2_bases` et les talons « moteur »
  le testent en VERSUS. Essai : mode test pendant une Arcade, puis VERSUS ; comparer à `vsd`.
- **E4. `EFFET_12A`** : le bit 7 de `$12A` est retiré puis remis autour de la copie d'Upper ; si la copie sort par un
  `longjmp` (6 sites setjmp / longjmp dans la construction), la remise n'a pas lieu. Non vérifié.
- Non fait : registres posés par Hyper et non remis par Upper au retour de la carte (liste complète des écritures
  `$804100-$80417F` des deux côtés).

## 5. Traducteur : ce que le report v160 → v161 changera

Copie figée `ro9a36/greffe/e42/untranspile3_v160` : diffère de l'étiquette `v160` de 107 lignes (`translate.py`) et
162 lignes (`mame_test.py`) (crochets de la greffe). `git diff v160 v161` (4 fichiers, +300 / -32) **s'applique sans
rejet** sur la copie (essai à blanc `patch --dry-run`, décalages de 1 à 124 lignes).

1. **Onze règles actives par défaut** : `A8_ENTREE`, `TST_C`, `TST_ZX`, `CMP_MEMADD`, `CMP_IDX`, `CMP_D8`,
   `CMP_MEMDN`, `PARITE_FLOT`, `PARITE_SITES`, `BCD_REG`, `AIDE_SBCD`. Elles touchent le code d'Hyper de ro9a comme
   dans Hyper seul, et les copies d'Upper. Témoin à refaire : les onze à 0 + `GARDE_AIDES=0 GARDE_CMP=0` = ro9a36 à
   l'octet.
2. **Listes de sites par module** (`MODULE=ro9` dans la greffe) : `PARITE_SITES` et `A8_ENTREE_SITES` sont en
   « module:décalage ». Trois sites d'Upper sont dans des routines GREFFÉES et ne seront pas reconnus à leur place
   de copie : `ro5:96878` → copie `0xE13B28` (saisie des initiales), `ro5:106418` → `0xE221B8`, `ro5:106468` →
   `0xE22208` (classes d'objets de décor). Il faut les ajouter à la liste `ro9` ; ces adresses bougent dès que le
   code greffé change : à calculer depuis `greffe.json` (`blocs`), pas à écrire en dur. Les six autres sites `ro5`
   et `ro5:3f230` sont dans des routines non greffées (`outils/decision.py`).
3. **Garde-fous** `GARDE_AIDES` / `GARDE_CMP` : la construction s'arrête (`sys.exit(3)`) sur un appel d'aide non
   rendu ou une comparaison sans forme 68K. Les talons de la greffe sont du MIPS écrit à la main dans les formes du
   recompilateur (`forme_cmpi_w`, `_test_octet`) : première cause d'arrêt probable.
4. **Talons à relire après le report** : les 29 talons (`greffe.json` `synth`) dépendent du rendu exact (e46 : un
   `andi` + `sh` fusionnés, une écriture perdue). `TST_C` / `TST_ZX` / `CMP_*` peuvent changer leur traduction :
   comparer `carte_image.txt` avant / après sur les plages `0x10D0B90-0x10D6600`.
5. `extra_regs.py` (+25) et `profils.py` (+4) changent aussi : la copie figée a les siens.

---

## Limites de cette revue

- Aucune preuve au banc. « Lue par Upper » = présente dans l'union des 65 journaux de lecture ; « prouvée » = dans le
  journal des conversions. Une case non lue n'est pas jugée.
- R1 : le partage vrai / faux des 295 cases RAM repose sur le voisinage et la moitié basse ; 16 cases ambiguës.
  Trois cases de la zone des décors (`0x9703EC`, `0x9703F0`, `0x9703F4`) sont fausses mais classées « table » par ce
  critère : à ajouter à la main à `sorties/ptr_exclus_revue.txt` (473 cases : 231 RAM, 26 données lues, 216 des deux
  régions de R4).
- R3 (b) : le mécanisme « creux de banque » est déduit du code (seule branche qui saute une case avant tout critère)
  et du fait que tout le voisinage est resté brut ; non reconstitué case par case.
- Axes 3 et 4 : survol ; les points « non fait » sont listés.

---

# 2e passe (12/11) — sur ro9a37

Analyse statique seulement, comme la 1re passe. **Rien n'a été lancé** : ni émulateur, ni construction ; les scripts
d'`essais_demain/` sont écrits et vérifiés en syntaxe (`bash -n`), pas exécutés.

**Ce qui change avec ro9a37 / v161.** `ro9a_module.bin`, `greffe.json`, `greffe_donnees.bin`, `zone_decors.bin` et
`greffe_ptrs.txt` de `<workspace>/work/greffe_arcade/e47/ro9a37_fige` sont identiques à ro9a36 à l'octet ; seule l'image 68K
(`b9/carte_image.txt`) change. Donc : tous les constats R1-R5, B1-B3, T1-T3 de la 1re passe valent tels quels (adresses
PS2 d'Upper et du module inchangées) ; **toutes les adresses 68K citées en 1re passe sont périmées** (prendre la carte
de ro9a37). Le dépôt a renommé `construction/ro9a36/` en `ro9a37/` et `releves_ro9a36/` en `releves_ro9a37/` (HEAD
`bed8b2a`) : les chemins de la 1re passe sont à lire ainsi ; `classe_relogements.py` et `dis.py` sont corrigés.
§5 (report v161) est fait par l'atelier : les 3 sites `ro5` greffés sont en forme exacte, les 29 talons se traduisent
pareil, les garde-fous sont à 0.

**Corrections de la 1re passe** (détail plus bas) : R3 c n'est pas un défaut (0 vrai pointeur sur 128) ; R4 : 117 des
216 cases sont lues par Upper, pas 13 ; T1 : la grille `0x5C5380` a 40 lignes, pas 48 ; E1 infirmée pour les scènes
6 et 8 ; E2 et E4 infirmées ; E3 : `$FF7E02` n'existe pas dans l'image.

## 6. Tri des 128 pointeurs « sans preuve » (R3 c) — CLOS : aucun vrai pointeur

`outils/tri_128.py` → `sorties/tri_128.txt`. Critères : valeur impaire, texte ASCII, moitié basse < `$200` hors
constantes du code (la greffe elle-même ne les prend pas pour des pointeurs), ≥ 6 petits mots sur les 8 voisins, un
seul des deux mots lu par Upper, voisin pointeur, cible = constante du code.

- **121 DONNÉES certaines** : coordonnées et tables de mots (`008C 008E`, `0090 00C0`), 9 fins de textes (`"ing"`,
  `"big"`), couleurs, mots de scripts.
- **7 DONNÉES probables** (un seul critère, aucun indice de pointeur) : `0x64ACD0`, `0x6D33D8`, `0x8B6468`, `0x928B70`,
  `0x92D9E4`, `0x92E97C`, `0x99EDC0` : paires (x, y) d'enregistrements de scripts de même forme que les 121.
- **0 pointeur, 0 indécidable.** Trois cases ont un indice de pointeur et sont relues à la main (`outils/ctx.py`) :
  `0x6EF7F8` (`0000 0095`, cible citée par le code, mais au milieu d'une table de petits mots `0082 0089 … 0099`),
  `0x99E624` (`0000 008C`, juste après une table de pointeurs, suivie de `0000 0020`, `0000 0028` : nombres 16.16),
  `0x99ECA4` (`00B8 0090`, voisine de `FFC0 0090` : coordonnées). Données toutes les trois.
- Le critère « un seul mot lu » n'a servi pour aucune des 128 (les deux mots sont toujours lus).
- Conséquence : R3 c est retiré des défauts ; rien à corriger, rien à essayer. Les autres familles « cible absente
  sans preuve » (1 995 + 142 + 577 cases, non lues ou cible non lue) ne sont pas triées : même forme à l'œil, non mesuré.

## 7. R3 a / b : cause reconstituée case par case, et correctif précis

`outils/r3_creux.py` → `sorties/r3_creux.txt` (142 cases prouvées laissées brutes dans ro9a37).

- **130 cases « creux de banque » : CONFIRMÉ case par case** (la 1re passe le déduisait). Les 130 (39 à cible copiée,
  91 à cible réutilisée chez Hyper) sont hors de tout segment et à plus de `$18` de toute lecture d'Upper, dans une
  banque de `T_619B50` ; aucune n'est dans une liste d'exclusion. Le journal des CONVERSIONS prouve qu'Upper joue ces
  enregistrements ; les journaux de LECTURE ne les ont pas vus (autres parties). Les 85 fins passent : effet hors du
  chemin des bancs (autres persos / coups), non mesuré.
- **12 cases à cible non copiée** : `0x613208`, `0x613230` (→ `0x84CBC4`), `0x7A0E44` + 4 (→ `0x7A28A4`, 2 octets avant
  la région copiée), `0x8E5784`, `0x8E5798`, `0x8E57AC` (→ `0x8EAFDC`, `0x8EAFAC`, `0x8EAF80` : enregistrements de 20 o
  dont le voisin `0x8E5770` est relogé), `0x81F4BC`, `0x81F524` (→ fichier 390, et dans un creux). Cause commune : la
  case est dans une région copiée mais pas dans un segment parcouru par la fermeture (prolongement, ou queue d'un
  segment coupé par une frontière réutilisée) ; `bloc()` reloge « si la cible existe » et ne suit jamais.
- **Correctif : `essais_demain/r3_preuves.diff`** (84 lignes, `patch -p1` depuis `ro9a37/greffe/`, essai à blanc sans
  rejet, `py_compile` bon ; **non exécuté**). Deux interrupteurs, à 0 par défaut (= ro9a37 à l'octet, témoin essai 01) :
  - `R3_CREUX=1`, `etape2/donnees2.py`, `Fermeture.regions()`, calcul des creux (après la ligne
    `while i_ < len(lus_) … occ.append((lus_[i_] - 8, lus_[i_] + 10))`, l. 480) : `occ += [(c - 8, c + $18) pour c dans
    PREUVES de la banque]`. L'enregistrement d'une case prouvée n'est plus rendu au placement, donc plus sauté par
    `dans_creux` ; il est relogé comme les autres.
  - `R3_CIBLES=1` : `donnees2.py` reçoit `cibles_prouvees_manquantes(F, reg)` (cibles des cases prouvées situées dans
    une région, ni copiées ni réutilisées) et `Fermeture(..., plus=())` (cibles suivies comme `cibles_prouvees`, sans
    devenir des départs, pour ne pas déclencher `SEG_REFS`) ; `etape3/greffe3.py`, à la création de `FD` (l. 1578) :
    point fixe de 4 tours au plus, avec le compte imprimé (« ENCORE manquantes » s'il en reste).
  - Risques : le bloc grossit (segments ajoutés, dont une banque en `0x84CBC4`, plafond 8 Ko par segment) et **tout
    se déplace** : toute la non-régression est à refaire (essai 03). `R3_CREUX` réduit les creux : des régions logées
    changent de place. Variante plus large, non retenue : ajouter les cases prouvées aux lectures (`LU_`, l. 1569).

## 8. R1 / R2 / R4 : listes séparées pour un essai par étapes

`outils/ptr_exclus_etapes.py` → `essais_demain/ptr_exclus_<étape>.txt` (8 fichiers) et `sorties/ptr_exclus_etapes.txt`.
« Certaine » = au moins une preuve statique de paire de mots : voisinage de petits mots, un seul mot du long lu par
Upper, banque de palettes, case prouvée à la main en 1re passe, valeur non multiple de 4 pour une cible de données.

| famille | certaines | probables | lues par Upper |
|---|---|---|---|
| R1 (classe RAM) hors zone | 136 | 70 | 47 + 21 |
| R1 zone des décors | 20 | 5 | 5 + 0 |
| R2 (paires relogées en pointeurs de données) | 21 | 5 | 26 |
| R4 (deux régions sans preuve) | 112 | 104 | 65 + 52 |

- Les 3 cases `0x9703EC/F0/F4` oubliées en 1re passe sont dans « R1 certaines zone ». Les 48 cases de vraies tables de
  pointeurs de RAM, les 16 ambiguës de `0x6142D0` et les 12 « table » de R2 ne sont dans aucune liste.
- **L'essai R1 d'hier** (`c37xh`, 231 cases) a bien changé les données (25 octets dans la zone des décors, 206 dans
  le bloc, mesurés sur les deux constructions) et le banc des décors n'a pas bougé (40/40 = ro9a37, 28/40 = Upper).
  Donc **R1 n'explique pas les 12 décors « aux objets aléatoires »** : cette piste de la 1re passe est à retirer. R1
  reste prouvé dans les données (bloc de ro9a37, copie de `T_615D70` : `00A0 00B9 009F 00A2 009E 00BB…`), son effet
  en jeu reste à voir ailleurs que sur ce banc : sonde de lecture (essai 02b), durées du banc des fins (essai 03b).
- Ordre proposé (essai 02) : A = R1 certaines, B = + R2 certaines, C = + R4 certaines, D = + probables. Une étape qui
  fait baisser « = Upper » contient un vrai pointeur : la retirer.
- Correction de R4 : d'après les marques de `classe.tsv`, **117** des 216 cases des deux régions sont lues par Upper
  (la 1re passe écrivait 13) : R4 passe de « moyen » à « à essayer avec R2 ».

## 9. Axe 3 : index des tables partagées (détail : `sorties/2e_passe_axe3.md`)

`outils/index_tables.py` (≈ 10 s) → `sorties/index_tables.txt`. Exécution symbolique du MIPS, 3 644 accès à des tables
dans ro9a37. Limites : 215 des 1 347 accès des copies ont un index non suivi ; les 29 talons ne sont pas vus.

- **X1 (prouvé dans ce périmètre)** : 54 tables d'Hyper sont lues par des copies d'Upper ; un seul masque manque dans
  une copie, `T_5c5120[$12A]` (copie `0xE42B8C`, Hyper `0x311680` avec `ANDI #$7F`), déjà couvert par `EFFET_12A`.
  Aucun index masqué ne déborde d'une table partagée.
- **X2 (prouvé) — ids MAX** : toutes les lectures par perso des copies passent par `$116` (perso de base).
  `T_BASE[$26-$2F] = 0` : un MAX lit Ryu partout aujourd'hui. `$26` / `$27` comme perso de base : dans toutes les
  tables (40 entrées), contenu d'Upper à remplir. `$28`, `$29`, `$2D`, `$2E` : **hors table** dans `T_74c358`,
  `T_617290`, `T_61bbc0`, `T_699408`, la table d'Hyper `T_63b5a4`, `T_619B50`, `T_72BDF0` ; valeurs sans rapport
  dans `T_97ca90`, `T_6f72b0`, `T_978d1c`. Règle : garder `$116 ≤ $27` pour les MAX, ou prolonger ces tables avant.
- **X3 (prouvé) — D4** : les lignes Yun / Ingrid sont en `$28` / `$29` ; les lignes `$2D` / `$2E` valent `$00`. Avec
  les ids annoncés, Yun aurait le décor de Ryu au lieu de `$42` ; à déplacer. `T_61BE10` ne déborde pas jusqu'à `$2F`.
- **X4 (corrige T1)** : la grille `0x5C5380` a 40 lignes (`$26` / `$27` à zéro) ; `0x5C5420` est une autre table.
  Hyper lui-même y déborde avec un perso de base ≥ `$28`.
- **X5 (probable)** : sur 1 063 routines renvoyées à Hyper, 7 paires ont un index différent ; une seule est un écart
  réel côté moteur (`0x333F70` → `0x117CA0`), juste tant que l'appelant est le moteur d'Hyper.
- **X6 (statique prouvé, effet à confirmer)** : 14 routines d'Hyper sont l'homologue de plusieurs routines d'Upper qui
  lisent des tables différentes (`0x2FEC0` ← 25, `0xA0FD0` ← 35, `0x31F50` ← 28, `0x65180` ← 21). Une vingtaine de ces
  routines d'Upper ne sont pas classées « non vue en Arcade » : famille des plantages de fins corrigés un à un
  (`FIN_A0FD0`). Correctif de principe : étendre `HOM_PARTAGES` (`force3.py`) sous interrupteur. Essai 04.

## 10. Axe 4 : registres et variables des deux côtés (détail : `sorties/2e_passe_axe4_transitions.md`)

`outils/registres.py` → `sorties/registres.txt` ; `outils/atteint.py` (fermeture des appels directs).

- **A1 (sain)** : aucune copie d'Upper n'écrit un registre `$8040xx` / `$8041xx` ; tout passe par la prise d'image
  d'Hyper, sauf une écriture de `$804166` par le talon `plans_s6`. Les copies n'écrivent que les copies en RAM.
- **A2 (à essayer en premier)** : les bases du fork `$804200-04` ne sont écrites que par 7 talons. Deux chemins les
  laissent périmées à la lecture du code : (a) VERSUS sur décor d'Upper puis retour à la sélection (`plans_vs` laisse
  `$4400/$440/$4A0`, `scene2_bases` ne fait rien hors Arcade) — jamais signalé en jeu, à vérifier avant tout
  correctif (essai 06) ; (b) réinitialisation pendant un écran d'Upper (dépend du cœur).
- **A3 / A4 (sains)** : bases de pages `$C130-$C13C` remises par Hyper sur `$A8(A5)` ; `$32` / `$3A` réécrits en entier
  par chaque écran suivant.
- **A5** : `$FE10` reste à 1 en TRAINING ou en démo après une Arcade ; sans effet aujourd'hui (tous les lecteurs hors
  Arcade exigent aussi `$FE11`), fragile. Correctif de 4 mots dans `d4_vs`. `$FE11` reste à 1 pendant une Arcade qui
  suit un VERSUS : sans effet. `$FE08` est temporaire.

## 11. Hypothèses des transitions : verdicts

| hypothèse | verdict | preuve / reste |
|---|---|---|
| E1 sortie vers `$C` | INFIRMÉE pour 6 et 8 ; indécidable pour A | la scène 6 ne sort jamais vers `$C` ; le GAME OVER appelle le fondu bloquant d'Hyper `0x948C0` avant la pose des bases. Scène A : pas de fondu avant la pose (essai 07). |
| E2 masque `$32` | INFIRMÉE | l'init de la scène 4 (`u2615D0`) n'écrit jamais `A5+4` ; la présentation réécrit `$32` à l'image suivante (`u25B09C`). |
| E2b (nouveau) | PROBABLE | la copie `u135430` renvoie à la sélection sans masque : si elle est atteinte pendant la carte ou le face-à-face (challenger), défaut du CONTINUE d'avant e46 (essai 08). |
| E3 drapeau `$FF7E00` | remis dans les sorties ordinaires ; pas dans les retours directs d'Hyper | remis au GAME OVER, en fin de générique, à la réinitialisation (RAM effacée `0x3DF38`). Non remis par `0x29C60`, `0x29C08`, `0x28608` (menu de pause du portage) : atteignabilité indécidable. Garde proposée : remise à 0 à l'init du titre d'Hyper (`0x61ED4`). |
| E4 `EFFET_12A` / longjmp | INFIRMÉE (appels directs) | les 6 sites setjmp / longjmp sont dans le moteur des joueurs d'Hyper ; aucun cadre setjmp n'est ancêtre des talons. Réserve : classes d'objets de `0xFD620` par tables (`jalr` non suivis). |

## 12. Essais prêts (`essais_demain/`, aucun lancé)

Tous écrivent dans `essais_demain/` (`c/`, `traces/`, `cmp/`) ; fonctions dans `outils/commun.sh` (copies adaptées des
lanceurs de `greffe_v161`, agent `revue_greffe`). Une construction ≈ 2 min 20 s et 1,3 Go.

| script | durée | tranche |
|---|---|---|
| `01_r3_temoin.sh` | ≈ 3 min | code + diff R3, interrupteurs à 0 = ro9a37 à l'octet (à faire avant 03) |
| `02_ptr_exclus_etapes.sh [A B C D]` | ≈ 6 min par étape, ≈ 25 min les quatre (2 places) | R1 / R2 / R4 par étapes, banc des décors |
| `02b_sonde_lecture_r1.sh` | ≈ 4 min (2 places) | les copies de `T_615D70` / `T_612380` sont-elles lues en Arcade ? |
| `03_r3.sh` | ≈ 12 min | `R3_CREUX`, puis `+ R3_CIBLES` : cases prouvées brutes (142 → attendu 0), banc des décors |
| `03_r3.sh fins` | ≈ 35 à 50 min (4 à 6 places) | banc des 85 fins sur la construction R3 |
| `04_x6_homologues.sh` | ≈ 8 min (4 places) | entrées des 14 homologues non injectifs depuis une copie d'Upper |
| `05_x2_ids_max.sh` | ≈ 6 min (3 places) | POKE du perso de base `$26` / `$28` / `$2D` (adresse `FF8517` déduite, à vérifier) |
| `06_a2a_versus_bases.sh` | ≈ 3 min | bases du fork après un VERSUS sur décor d'Upper |
| `07_e1_e3_fin_et_gameover.sh` | ≈ 5 min (2 places) | scène A → `$C` (écran noir ?) et remise de `$FF7E00` |
| `08_e2b_challenger_carte.sh` | ≈ 3 min | challenger pendant la carte (réserve : `defi.lua` n'a pas fait entrer J2 hier) |

Non scriptés (au cœur, à la main) : A2b réinitialisation pendant la carte (≈ 2 min), E3 menu de pause (≈ 3 min).

## Limites de la 2e passe

- Rien n'est prouvé au banc. Les scripts et `outils/etat_bases.lua` ne sont pas essayés ; le correctif R3 n'a pas tourné.
- Axes 3 et 4, et verdicts E1-E4 : faits par deux sous-tâches ; j'ai relu leurs synthèses et recontrôlé X3 (tableau D4)
  et X4 (octets de `0x5C5380` / `0x5C5420`), pas le reste.
- Le tri R1 / R2 / R4 « certaines » repose sur des critères de forme ; seul l'essai par étapes dira si une liste
  contient un vrai pointeur.


<!-- source: <workspace>/work/revue_greffe/RESULTATS_ESSAIS.md -->

## File `<workspace>/work/revue_greffe/RESULTATS_ESSAIS.md`

# Résultats des essais au banc — revue de la greffe « Hyper + Arcade » (ro9a37)

Agent `essaisgreffe` (sfa3ha), 12/11/2026. Scripts : `<workspace>/work/revue_greffe/essais_demain/` (RAPPORT.md §12). Construction
essayée : `<workspace>/work/greffe_arcade/e47/ro9a37_fige` (sauf essais à construction : `essais_demain/c/`). Rien n'est corrigé dans
la greffe ; un correctif confirmé est décrit avec la livraison qui le porterait (ro9a38).

Légende du verdict : CONFIRMÉ (le défaut existe), INFIRMÉ (le défaut n'existe pas), INDÉCIDABLE (l'essai ne tranche pas).

| essai | constat visé | résultat | verdict |
|---|---|---|---|
| 06 + 06b `a2a_versus_bases` | A2a : bases du fork `$804200-04` périmées après un VERSUS sur décor d'Upper | VERSUS Ryu Z3 / Ryu Z3 (MAME fork, ro9a37_fige), 3 matchs, tous sur décor d'Upper. Bases `4400 0440 04a0` posées à l'entrée du combat (images 1022, 2990, 5126), GARDÉES pendant l'écran de résultat (`A5+4 = $E`) puis pendant TOUTE la sélection suivante (`A5+4 = 2`, images 2358-2650, 4486-4786, 6462-6754) ; remises à `0300 0340 03a0` seulement à l'entrée du match suivant (`A5+4 = 4`, `A5+8 = 2`). Captures (06b, `SNAPS`) : 1re sélection = fond normal (planisphère) ; les sélections qui suivent un VERSUS sur décor d'Upper ont le fond en tuiles fausses (bandes rouges, morceaux de décor) — planche `essais_demain/cmp/a2a_vs2_planche.png` (ligne 1 = sélection normale, lignes 2-4 = après VERSUS). Déterministe (06 et 06b identiques ligne à ligne). | **CONFIRMÉ** (au banc MAME ; à revoir au cœur avant correctif, le banc reproduit le mécanisme des bases du fork) |
| 08 `e2b_challenger_carte` (tel quel) | E2b | NON LANCÉ tel quel : `lua/defi.lua` ne déclenche le défi qu'EN COMBAT (`A5` = 2/4/6) ; il ne peut pas tester un défi pendant la carte. Remplacé par 08b. | — |
| 08b `e2b_defi_carte` (variante, `outils/defi_carte.lua`) | E2b : nouveau challenger pendant la carte d'Upper → retour à la sélection sans masque, tuiles fausses ? | 1er passage (Start J2 4 images une fois) : J2 n'entre pas. 2e passage (impulsions de Start tant que l'état dure, Coin 2 à 400) : J2 ENTRE pendant la carte (Start à 650, carte `2/4/2`) et en combat (témoin). Carte : bases `0400` → `4400 0440 04a0` à 651 (bandeau « HERE COMES A NEW CHALLENGER »), sélection à 737 avec bases d'Upper UNE image, `0300 0340 03a0` dès 738 ; `c32` reste `1b0e`. **CORRIGÉ après contestation de l'agent flou** : ma 1re planche sautait les captures 108-109. Relu en entier (`cmp/e2b_carte_98_115.png`) : captures 108-109 (images ≈ 739-740) = gros blocs de tuiles fausses (planisphère en pavés) ; 107 et 110-115 propres. Témoin en combat (`cmp/e2b_combat_104_115.png`) : 107 (décor en partie en pavés), 108-109 (pavés), puis 110-111 planisphère aux couleurs fausses (magenta / vert ; peut-être l'éclair du défi d'Hyper, non comparé à Hyper seul). J2 prend Ken ZERO (`$31`), 2 manches, retour à `$19`, 0 EXC. | **CONFIRMÉ, BÉNIN** : 2 images de tuiles fausses (carte), 3 (combat), au passage vers la sélection après un défi ; pas de plantage |
| 08b `e2b_defi_carte` VARIANTES=vs:244 | E2b pendant le face-à-face (`2/4/4`) | Coin 2 à 400, Start J2 en impulsions à 711, 741, 771 (tout le face-à-face, 711-786) : J2 n'entre PAS ; la partie continue à un joueur (6 manches, 0 EXC). Sur la carte, la 1re impulsion (620, image d'entrée) est aussi ignorée et la 2e (650) prise. Upper d'origine non essayé (le lanceur Upper écrit chez greffe_arcade). | ~~INFIRMÉ de fait~~ → **FAUX**, voir flou/01 : le défi au face-à-face est accepté avec des impulsions serrées et J1 passif |
| 01 `r3_temoin` | témoin du correctif R3 (interrupteurs à 0) | code figé + `r3_preuves.diff` appliqué (`patching file etape2/donnees2.py`, `etape3/greffe3.py`), construction r3z en 150 s : 5 IDENT (données, zone, module, pointeurs, `sz3ud.03c` md5 `627c98c4…`) contre `ro9a37_fige`. | **TÉMOIN BON** : le diff R3 à 0 redonne ro9a37 à l'octet ; 03 peut tourner |
| 07 `e1_e3` — partie `go` (GAME OVER) | E1 (bases d'Hyper posées sur la VRAM d'Upper à la sortie vers `$C`) et E3 (`$FF7E00` remis) | Ryu Z3 PERDRE=1 NOCONT=1 : scène `$C` à 5990 avec bases `0400` (écran « GAME OVER » d'Upper encore affiché, captures 130-137), bases d'Hyper `0300 0340 03a0` et `fe00 00` à 6012 : captures 138-150 NOIRES (`cmp/e3_go_planche.png`). 0 EXC. | E1 **INFIRMÉ** pour le GAME OVER (écran noir à la pose) ; E3 **SAIN** (`fe00` remis à la pose des bases, 22 images après l'entrée en `$C`) |
| 07 `e1_e3` — partie `fin` (telle quelle) | E1 scène A → `$C` | Script défectueux : sans `SCENEA_PASSIF=1` la tournée appuie sur Start pendant la fin et l'ABRÈGE (scène A 39 images au lieu de ≈ 11 800 ; f77_00_Z3 : 11 780). Chemin réellement suivi : A (19948) → 8 (19987, « TRY AGAIN » / GAME OVER) → `$C` (20177, bases `0400`) → bases d'Hyper + `fe00 00` à 20199 : captures 449-456 NOIRES (`cmp/e1_fin_abregee_planche.png`). 20 manches (Ryu bat M. Bison), 0 EXC. | E1 **INFIRMÉ** pour « fin abrégée → 8 → `$C` » ; scène A → `$C` directe : voir 07b ; E3 **SAIN** |
| 07b `e1_fin_passive` (copie de 07, `SCENEA_PASSIF=1`) | E1 scène A → `$C` | Fin de Ryu Z3 complète : scène A 19948-31727 (11 780 images = f77_00_Z3), puis **scène 8** (31728, GAME OVER / « TRY AGAIN ») → `$C` (31831, bases `0400`, écran GAME OVER d'Upper, captures 441-448) → bases d'Hyper + `fe00 00` à 31853 : captures 449-455 NOIRES (`cmp/e1_finp_planche.png`). Titre d'Hyper ensuite, 0 EXC. La sortie A → `$C` DIRECTE n'est pas prise par la fin (A passe par 8). | E1 **INFIRMÉ** pour la fin (le chemin A → `$C` direct n'est pas atteint ; A → 8 → `$C` est noir à la pose) ; E3 **SAIN** |
| 02b `sonde_lecture_r1` | R1 : les copies de `T_615D70` (16 mots) et `T_612380` (8 mots) sont-elles LUES en Arcade ? | Adresses 68K `df2040` / `dee650` VÉRIFIÉES par vidage (`00A0 00B9 009F 00A2 009E 00BB…` = copie du bloc citée au RAPPORT ; `0080 00B8 00C0 00E0 0100…`). Partie oracle Ryu Z3, 20 000 images (20 manches, jusqu'à M. Bison et l'entrée de la fin) : **0 lecture** sur chacune. Témoin de la sonde (`lect_temoin`, fenêtre `de0000-df8000`, 3000 images) : 300 lectures prises (`df1408`, `df141a`, `deef44`…) : la prise voit bien les lectures du bloc. | R1 sur ces deux tables : **SANS EFFET OBSERVÉ** dans une Arcade Ryu Z3 (non lues) ; autres persos, fins et TRAINING non couverts |
| 02 étape A (R1 certains 136 + zone 20) | une liste PTR_EXCLUS contient-elle un vrai pointeur ? | pxA (TIRAGE_CPU=0) vs c37h : données 136 octets, zone 20, module 136, `sz3ud.03c` IDENT. Banc des décors : 40/40 = bd47h ; 28/40 = Upper (même compte que ro9a37 ; écarts 14 16 22 26 2A 30 3C 3E 40 42 46 4A). 1er passage perdu : MAME « Required files are missing » (liens ROM absents des constructions neuves, corrigé par `lie_roms` dans commun.sh). | **aucun vrai pointeur VISIBLE** dans A (le banc des décors ne voit pas R1 : cf. 02b) |
| 05b `x2_ids_max` (copie de 05, 1 partie à la fois) | X2 : perso de base ≥ `$28` dans les écrans d'Upper | Adresse `FF8517` VÉRIFIÉE avant (journaux f77 : MANCHE « J1 61/01 » = `$103`/`$117` de Ken EX ; `$117` = perso de base). POKE permanent dès l'image 900 : `$26` 9 manches 0 EXC ; `$28` et `$2D` : EXCEPTION pc `$A08` (erreur d'adresse) vers l'image 1600, EN COMBAT (scène 4/6/6), retours dans le code d'Hyper (`0x955dc`, `0x9676a`). | le script 05 tel quel ne teste pas les écrans d'Upper (le combat d'Hyper plante d'abord sur l'id falsifié) → 05c |
| 05c `x2_ids_hors_combat` (`outils/poke_hors_combat.lua`) | X2, id falsifié SEULEMENT pendant carte / face-à-face / victoire, remis en combat | `$26` : 6 poses (carte, face-à-face, 5 victoires), 11 manches, 0 EXC. `$2D` : EXCEPTION `$A08` à l'image 668, PENDANT LA CARTE (4/2), adresse lue impaire `01E4B703` ; pile : copies d'Upper module `0xEC8E48`, `0xE69128` → routine d'Hyper module `0x38D92C` (`MOVE.L $FFFC(A0),D0`, lecture d'un pointeur de table). `$28` : EXCEPTION `$A08` à 760, PENDANT LE FACE-À-FACE (4/4), adresse `0146BB91` ; pile : copie module `0xADC8` → Hyper `0x6181C` (même lecture). | **CONFIRMÉ** : un perso de base `$28` ou `$2D` plante la greffe dès la carte / le face-à-face ; `$26` passe |
| 02 étapes B, C, D (cumulées : + R2 certains 21 ; + R4 certains 112 ; + tous les probables 184) | idem | vs c37h : B 200 octets (données / module), C 563, D 969 (zone 25) ; `sz3ud.03c` IDENT à chaque étape. Banc des décors : 40/40 = bd47h aux trois étapes ; « = Upper » 28/40 inchangé. | aucun vrai pointeur VISIBLE au banc des décors dans A-D ; **INDÉCIDABLE** pour R1 / R2 / R4 en jeu (le banc des décors ne lit pas ces cases ; juge = banc des fins ou sondes de lecture) |
| flou/01 `e2b_face_a_face` (copie `essais_demain/flou/`, `flou/essais/defi_faf.lua`) | E2b pendant le face-à-face | Start J2 en impulsions serrées (3/6) et J1 passif : défi ACCEPTÉ à 718 (face-à-face `2/4/4`, `$8B` → 01), bandeau 79 images, sélection à 797 avec bases d'Upper `0400` UNE image, `0300` dès 798. Captures (`essais_demain/flou/cmp/e2b_faf_95_109.png`) : 100-101 (≈ 799-800) = planisphère en gros pavés, comme sur la carte ; le reste propre. J2 joue Ken ZERO, 0 EXC. Mon 08b (VARIANTES=vs:244) avait conclu « non atteignable » à tort (impulsions trop espacées, face-à-face abrégé par J1). | **CONFIRMÉ, BÉNIN** (2 images de pavés) ; ma ligne « face-à-face INFIRMÉ de fait » est FAUSSE |
| flou/02 `graine_figee_decors` (copie `essais_demain/flou/`) | point 1 du flou : les 12 décors « aléatoires » ne diffèrent-ils d'Upper QUE par le tirage ? | Banc des décors Upper (fige/ro5) et greffe (c37h, sans tirage CPU), graine `$FF80AE` imposée à chaque image de combat ; 56 passages, tous FIN. Mode **fixe** (`$0040`, point fixe) : OK pour 30, 42, 46 et les témoins 00, 28 ; restent 14 / 2A / 3C / 3E : objet 11 classe `$11` (y) seul (la classe `$12` disparaît) ; 16 : classes `$03` (y, caméra Y, attendu) ; 22 / 26 : objet 15 classe `$1B` (x) ; 40 : `$2B` (attendu, caméra) + `$2D` (y) + `$2C` (anim, objet 7 absent / 9 en trop) ; 4A : **21 écarts** classe `$28` (x, y, anim, objet absent). Mode **image** : 30 et 16 OK, le reste en écart (14 groupe : `$12` + `$11` ; 22/26 `$1B` ; 40 13 ; 42 `$25` ; 46 `$24` ; 4A 20). Détail `essais_demain/flou/cmp/gf_{fixe,image}_*.txt`. | « tirage seul » **CONFIRMÉ** pour 30, 46, 42 (fixe) et la classe `$12` ; **NON CONFIRMÉ** pour 4A (`$28`), 22/26 (`$1B`), 40 (`$2C`, `$2D`) et la classe `$11` (14 2A 3C 3E) : écarts restants avec une graine fixe = autre cause (à chercher : réserve du flou, une boucle de tirage peut se comporter autrement avec un générateur constant) |
| 03 `r3` (r3c = R3_CREUX, r3d = + R3_CIBLES, TIRAGE_CPU=0, constructions réutilisées) | R3 : pointeurs PROUVÉS laissés bruts | Cases prouvées laissées brutes (`classe_relogements.py`, même filtre) : ro9a37 **142** → r3c **15** (attendu ≤ 12 : 3 de plus, liste `cmp/brutes_r3c.tsv`) → r3d **0**. `sz3ud.03c` change (r3c = r3d md5 `70e382ad…` ; c37h `80f22a18…`). Banc des décors r3d : **40/40 = bd47h**, 28/40 = Upper (inchangé). | correctif R3 **EFFICACE** (0 case prouvée brute) et **sans régression visible** au banc des décors ; reste le banc des fins (03 fins) |
| flou/03 `sonde_probables` (copie, une partie à la fois) | point 4 du flou : les 184 cases « probables » (R1 70 + 5 zone, R2 5, R4 104) sont-elles lues, en long ou en mots ? | 2 Arcades complètes avec fin (Ryu Z3 32 028 images ; perso `0b` Z3 27 128 images), 184 prises de lecture : **1 case lue sur 184**, R1 probable Upper `917350` (68K `eab840`, Upper `00A1 000C`, bloc `00B9 000C`) : lue en DEUX MOTS par `(A2)+`, pendant la FIN DE RYU seulement (dès l'image 29 093) ; le mot bas `00B9` (au lieu de `00A1`) sert d'index : pc `09c3e0`/`09c3e2` `MOVE.W -2(A2),D0 ; MOVEA.L T_de0240(PC,D0.W),A0`. Perso `0b` : aucune lecture. | case `917350` = **DONNÉE, relogement FAUX prouvé** (index décalé de `$18` dans la fin de Ryu) : à EXCLURE (liste R1 probables) ; 183 autres non lues dans ces 2 parties (indécidable) |
| 09 `r1_fin_ryu` (essaisgreffe) | effet visible de la case R1 `917350` lue dans la fin de Ryu | Vidage : c37h (= ro9a37 sans tirage) `eab840` = `000C 00B9`, pxD (case exclue) = `000C 00A1`. Fin Ryu Z3 complète sur les deux, 91 captures de 29 000 à 31 700 (toutes en scène A) : **0 capture différente**. Explication par le code (`carte_image`, pc `09c40a-09c426`) : le mot lu sert à `ANDI.L #$FFE0` (`00B9` et `00A1` → `00A0`, même adresse de tuiles) et `BTST #0,D6` (bit 0 = 1 des deux côtés) : les bits 3-4 changés par `+$18` ne sont jamais utilisés. | relogement faux **SANS EFFET** (prouvé par le code et par les captures) ; l'exclure reste juste (donnée), sans urgence |
| 04b `x6_homologues` (copie de 04, `outils/appels_uniques.lua` : une ligne par (cible, retour, scène), PC exact) | X6 : homologues non injectifs entrés depuis une copie d'Upper ? | 8 Arcades complètes avec fin (00.Z3, 0b.A, 18.Z3, 21.Z, 0a.Z2, 10.A, 1d.Z3, 24.Z3 ; 24.Z3 donne la même partie que Ryu Z3 : fin 31728 / 11780), 0 EXC. Sur les 14 cibles, 3 seulement sont entrées : `0x64d00` (68K `010828`), `0x65180` (`0108b4`), `0x688f0` (`010f8e`, partie 18 seulement) ; **0 entrée avec retour dans une copie d'Upper**. Script 04 d'origine : `AP_N=20000` (e33_appels) coupait le journal en début de partie, et sans contrôle du PC la lecture anticipée du 1er mot donne de faux appels (`008fa4` ×4825, `010828` ret `17628` ×9650 sur 6000 images, absents avec PC exact). | **INFIRMÉ** au critère « retour dans une copie » pour ces 8 parties ; critère incomplet (cibles atteintes par `JMP` de table : voir flou/04b) |
| flou/04b `x6_fins_manquantes` (copie ; prises sur PC + 2, `appels_uniques.lua` AP_PCEXACT=0 au lieu d'e33_appels plafonné) | X6 pendant les fins 07, 0f, 19, 1a, 1c | 5 fins complètes (Guy 07 : 88 203 + 5 540 images), 0 EXC, durées de fin = f77 / g77 (et = Upper quand connue : 0f 7006, 19 8370, 1c 6164). **13 entrées réelles, toutes pendant la fin (`A5+4 = $A`) et avec retour dans une copie d'Upper** : `0x31F50` depuis la copie module `0xE29D90` dans les 5 fins (07, 0f, 19, 1a, 1c) ; `0x84EA0` depuis `0xEB7140`, `0xEB7330`, `0xEB7E70`, `0xEB8060` (0f, 19, 1a) ; `0xA0FD0` depuis `0xEA4C4C`, `0xEA58AC` (07). (Le script imprime la cible au module de PC − 2 : `31f60`, `84ecc`, `a0ff4` = ces trois routines.) | **CONFIRMÉ** (les 3 cas annoncés par le flou : routines d'Hyper entrées depuis des copies d'Upper dans les fins) ; effet visible NON MESURÉ (durées de fin inchangées, aucune exception) |
| 03 `r3.sh fins` (r3f = R3_CREUX + R3_CIBLES, AVEC tirage, MIEN=2) | non-régression des fins avec le correctif R3 | Construction r3f (`sz3ud.03c` md5 `51a0dc41…`), 85 fins oracle (81 + 4 de Guy) : **85/85 abouties, 0 EXC** ; durées et états comparés à ro9a37 (`<workspace>/work/greffe_v161/tab_f77.txt`, `tab_g77.txt`, `e44/cmp_durees.py`) : **0 / 81 et 0 / 4 différents**. Tableaux `essais_demain/cmp/tab_fr3.txt`, `tab_gr3.txt`. | correctif R3 **SANS RÉGRESSION** (décors 40/40, fins 85/85 identiques en durée) : bon pour ro9a38 |

### Détail 06 — correctif proposé (non appliqué) pour ro9a38
Au retour à la sélection hors Arcade (`$FF7E00 = 0`), reposer les bases d'Hyper `0300 0340 03a0` : soit dans
`scene2_bases` (aujourd'hui sans effet hors Arcade : le rendre actif en VERSUS dès que la base courante est `$4400`),
soit à la sortie du combat VERSUS (`plans_vs`, passage `A5+4` 4 → `$E`). L'écran de résultat (`A5+4 = $E`, 2239-2358)
garde aussi les bases d'Upper : à vérifier sur capture avant de choisir le point de pose (si l'écran de résultat dessine
le décor du match, poser à l'entrée de la sélection seulement). Trace : `essais_demain/cmp/a2a_vs.txt`, `a2a_vs2.txt`,
`traces/a2a_vs2/snap/sfa3hx/0000-0010.png` (images 450, 550, 640, 2420, 2500, 2600, 2640, 4560, 4650, 6540, 6700).

### Détail 05c — conséquence pour les ids MAX (décision, pas de correctif ici)
Le plantage est certain (pas seulement « sprites faux ») dès qu'un perso de base ≥ `$28` passe par la carte ou le
face-à-face d'Upper. Deux voies (RAPPORT §9 X2, décision du coordinateur) : garder les MAX à `$116 ≤ $27`, ou prolonger
les 9 tables qui débordent (`sorties/2e_passe_axe3.md`). Un correctif de prolongation (ro9a38 ou plus tard, avant
l'intégration MAX) se vérifierait par `05c_x2_ids_hors_combat.sh` (IDS="28 2d 2e" : 0 EXC attendu).

### Note sur le critère « = Upper n/40 » (coordinateur, 12/11)
« = Upper 28/40 » n'est PAS un critère de non-régression des décors : les tirages diffèrent par construction entre Upper et
la greffe. Le critère est « = bd47h 40/40 » (même construction sans le changement essayé, TIRAGE_CPU=0).

### Détail E2b — correctif proposé (non appliqué) pour ro9a38
Défi accepté pendant la carte, le face-à-face ou le combat : la copie `u1353A0` renvoie à la sélection sans masque et
`scene2_bases` pose les bases d'Hyper sur la VRAM d'Upper : 2 à 3 images de pavés plein écran (+ 2 de couleurs fausses
depuis un combat). Correctif proposé par l'agent flou : masque des couches de la forme `masque_sortie` (e46) autour de
`u1353A0`, ou bases d'Hyper retardées dans `scene2_bases`. Vérification : `08b_e2b_defi_carte.sh` (VARIANTES="carte:242
combat:246") et `flou/01_e2b_face_a_face.sh` : captures 107-111 sans pavés.

### Synthèse pour ro9a38 (correctifs confirmés au banc, aucun appliqué ici)
1. **R3** (`essais_demain/r3_preuves.diff`, interrupteurs `R3_CREUX=1 R3_CIBLES=1`) : 142 → 0 case prouvée brute ;
   témoin à 0 = ro9a37 à l'octet ; décors 40/40 = bd47h ; 85/85 fins, durées identiques. Prêt.
2. **A2a** : reposer les bases d'Hyper `0300 0340 03a0` au retour à la sélection hors Arcade (VERSUS après décor d'Upper).
3. **E2b** (bénin) : masque des couches autour de `u1353A0` ou bases d'Hyper retardées dans `scene2_bases`.
4. **X2** (ids MAX) : décision du coordinateur ; `$28` / `$2D` plantent dès la carte / le face-à-face.
5. **X6** (fins 07, 0f, 19, 1a, 1c) : entrées réelles confirmées, effet visible non mesuré : à juger avant correctif.
6. Exclusion de la case R1 `917350` : juste mais sans effet (essai 09).


<!-- source: <workspace>/work/revue_greffe/flou/RAPPORT_FLOU.md -->

## File `<workspace>/work/revue_greffe/flou/RAPPORT_FLOU.md`

# Zones floues de la revue de la greffe « Hyper + Arcade » (ro9a37) — verdicts

Agent `flou` (sfa3ha), 12/11. **Analyse statique seule** (code, données, traces déjà faites) : aucun émulateur, aucune
construction. Écrit seulement dans `<workspace>/work/revue_greffe/flou/`. Détail des points 2 et 3 : `p2_homologues.md`,
`p3_transitions.md` (deux sous-tâches ; je n'ai pas refait leurs lectures, seulement recoupé avec `RESULTATS_ESSAIS.md`).
« Prouvé » = lu dans le code ou mesuré dans une trace existante ; « déduit » = raisonnement sans mesure.

| point | verdict |
|---|---|
| 1. Objets « aléatoires » des 12 décors | **Pas un défaut de données** : tirage + réaction au combat + banc. Essai de confirmation prêt (02). |
| 2. Les 14 homologues non injectifs | 3 confirmés (`0xA0FD0`, `0x84EA0`, `0x31F50` pour une routine), 1 indécidable (`0x24A90`), 10 infirmés. |
| 3. E1 scène A / E3 pause / E2b | E1 infirmé, E3 infirmé, **E2b confirmé** (carte et combat ; face-à-face à essayer). |
| 4. Les 7 « probables » du tri des 128 | Infirmés comme pointeurs : 7 données, preuve de structure. |
| 4. Probables R1 / R2 / R4 (184 cases) | 106 données par preuve forte, 22 par indice, 56 toujours indécidables : essai prêt (03). |

---

## 1. Les 12 décors « aux objets aléatoires » (14 16 22 26 2A 30 3C 3E 40 42 46 4A)

**Verdict : la cause n'est pas dans les données copiées ni dans les tables. Les écarts viennent de trois mécanismes,
tous hors de la zone des décors, et du comparateur.** Preuve statique forte, confirmation au banc prête (essai 02).

### Ce qui est prouvé

1. **Mêmes images, mêmes états des deux côtés.** Sur les traces du banc (Upper `<workspace>/work/greffe_arcade/traces/bdu_*`, greffe
   `<workspace>/work/greffe_v161/traces/bd47h_*`), par classe d'objet et tous emplacements réunis, l'ensemble des pointeurs d'image
   pris par la greffe est **exactement** celui d'Upper décalé du relogement constant de la zone (`$804200`), pour toutes
   les classes des 8 décors distincts (`$00 $01 $02 $03 $05 $12 $13 $1B $1C $1D $1F $24 $27 $28 $29 $2A $2B $2C`) ;
   `$25` et `$2D` : il manque à la greffe une image qu'Upper montre (événement non déclenché), aucune en trop. Les
   états (+4..+7) sont les mêmes. Seule la classe `$11` (décor `$14`, hors zone, relogement non constant) n'est pas
   jugée par ce test ; le comparateur la donne conforme. Outils : `outils/obj_supports.py`, `obj_div.py`, `obj_champ.py`.
2. **Le générateur est le même, la suite des tirages non.** Les classes d'objets (table `T_611E50`, octet +3) appellent
   le générateur d'Upper `0x2BB350` par appel lointain (`lui / ori / jalr`) ; dans la greffe ces sites vont au
   générateur d'Hyper `0x57E890` : **mêmes 52 mots MIPS**, même graine `$AE(A5)` (`$FF80AE`). Il n'y a pas de 2e
   générateur ni de copie. Mais la graine avance à chaque appel de tout le jeu (boucle principale, IA, moteur d'Hyper) :
   l'état de la graine à l'entrée du combat et le nombre d'appels par image ne peuvent pas être ceux d'Upper.
   `outils/classes_tirage.py` : 21 classes sur 47 tirent.
3. **Exemple suivi image par image** (décor `$30`, objet 13, classe `$1F`) : même état, même compte à rebours jusqu'à 0
   à la même image, puis durée tirée `$E5` chez Upper et `$F3` dans la greffe ; ensuite seulement les deux divergent.
4. **Plans** : à caméra égale, `s1x − s2x` est le même (décor `$14` : 255 positions de caméra sur 274, le reste à ±1 ou
   pendant un tremblement). L'écart « parallaxe 0,908 / 0,945 » de `$14 $2A $3C $3E` est une pente de régression faussée
   par les tremblements (70 images chez Upper, 15 dans la greffe), pas une parallaxe différente.
5. `$14`, `$2A`, `$3C`, `$3E` donnent quatre traces identiques à l'octet de chaque côté : c'est un seul décor compté
   quatre fois (de même `$22` = `$26`). Il y a donc **8 cas distincts**, pas 12.

### Cause par décor

| décor | objets en écart | classe | mécanisme | preuve |
|---|---|---|---|---|
| `$14 $2A $3C $3E` | 4, 5, 9 (+ anim 4, 6) ; s1x / s3x | `$12` | tirage (3 sites) ; plans : artefact du comparateur | sites `0x1046F0`, `0x10477C`, `0x1047C8` ; point 4 ci-dessus |
| `$22 $26` | 14, 15 | `$1B` | tirage (2 sites) | `0x108110`, `0x108180` ; positions tirées dès avant l'image −30 |
| `$30` | 13 | `$1F` | tirage (2 sites) | `0x10A168`, `0x10A1F8` ; exemple suivi |
| `$46` | 15 | `$24` | tirage (5 sites) | `0x4127AC`… |
| `$4A` | 0 à 7 | `$28` | tirage (2 sites) | `0x414390`, `0x4143E0` |
| `$40` | 7, 8, 9 | `$2C` | tirage (4 sites) | `0x4175A0`… |
| `$40` | 12, 13, 14 ; 11 | `$2B`, `$2A` | **pas de tirage** : lisent la position de scroll1 `$212(A5)` (seuils `$2A0`-`$A00`) ; la caméra est libérée ≈ 32 images plus tard par le moteur d'Hyper (86 → 118), d'où un cycle de l'objet 11 décalé de 32 images (84 → 116, même période de 71) | 68K de la copie `0xEDCB70` (`$0BD43A`…) ; plans identiques à l'image −30 |
| `$40` | 15 | `$2D` | tirage (1 site) + événement à l'image 466 des deux côtés | `0x418BA8` |
| `$42` | anim de 15 | `$25` | **pas de tirage** : réagit aux VIES des joueurs (`$450(A5)`, `$850(A5)` comparées à `$50/$52(A6)`) : le combat d'Hyper n'est pas celui d'Upper (réaction à 626 chez Upper ; à 209, 269, 398 dans la greffe) | 68K de la copie `0xED9B10` (`$0BCCAE`…) |
| `$16` | 9, 13 (Y) | `$03` | **pas de tirage** : lit la caméra Y `$292(A5)` (sauts des joueurs) ; écart de pente de 0,18 sur un mouvement de 1 à 3 px | 68K de la copie `0xE1B140` (`$09D49C`) |

Reste non expliqué en détail (sans effet visible, déduit) : décor `$40`, objets 12-14, placés à leur position de
réserve `(5312, 219)` jusqu'à l'image ≈ 222 dans la greffe alors qu'Upper les a déjà en `(1168, 144)` à l'image −30.
Les deux positions sont hors écran tant que scroll1 n'a pas atteint ≈ `$310`, et les deux côtés se rejoignent avant
(`$2D0`) ; puis mêmes changements aux mêmes images (510, 1064). Upper a donc vu `$212 ≥ $2D0` avant le combat, pas la
greffe : différence d'initialisation de scroll1 avant la manche, à regarder seulement si un objet manque à l'écran au
début d'une manche sur ce décor.

### Effet en jeu
Aucun défaut : les objets tirés (foule, oiseaux, éclairs, passants) n'ont pas la même suite que dans Upper, comme
entre deux parties d'Upper. Le compte « 28/40 = Upper » ne peut pas monter avec ce banc : il compare des tirages et des
combats différents. Ce n'est pas un critère de non-régression pour ces 8 décors ; le bon critère est « mêmes ensembles
d'images et d'états par classe » (`outils/obj_supports.py`).

### Limites
- Rien n'est mesuré avec une graine commune : c'est l'objet de l'essai 02.
- Le test des ensembles ne voit pas un objet qui apparaîtrait par un événement jamais joué dans le banc (≈ 1 800 images
  par décor, joueurs tenus) ; B1 de la revue (trames à palette < `$0F` non recodées) reste ouvert pour ces objets.
- Les classes sont délimitées par l'adresse du gestionnaire suivant : un tirage fait dans une aide commune n'est pas
  compté (c'est peut-être le cas de `$03` : durées 55 / 48 d'un cycle).

### Essai prêt : `essais/02_graine_figee_decors.sh` (≈ 8 à 10 min à 2 places, sans construction)
Banc des décors des deux côtés avec la graine imposée à chaque image (`essais/graine_figee.lua`) : mode « fixe »
(`$0040`, point fixe du générateur : tous les tirages rendent `$40`) et mode « image ». Attendu : les classes qui tirent
ne sont plus en écart ; peuvent rester `$42` (vies), `$16` (caméra Y), `$40` (classes `$2A` / `$2B`). Tout autre écart
restant serait un défaut déterministe. Réserve : un tirage constant peut bloquer une boucle d'IA (lire alors le mode
« image »). Jamais lancé.

---

## 2. Les 14 homologues non injectifs (X6) — détail `p2_homologues.md`

| cible d'Hyper | verdict | preuve | effet en jeu |
|---|---|---|---|
| `0xA0FD0` | **CONFIRMÉ** (8 routines d'Upper hors « j ») | entrées de tables d'états copiées, lues par des gestionnaires copiés ; exécutées dans les fins 07 (Guy), 0b (Sagat), `$18` (traces d'opcodes d'Upper) | déduit : acteurs de fin figés dans leur état ; `$10D(A5)` écrit à chaque image ; pas de plantage attendu |
| `0x84EA0` | **CONFIRMÉ** (4 routines) | `21D6C0 21DD90 21EA50 21EDC0` créent un acteur enfant toutes les 12 / 16 / 30 images ; l'homologue fait `SUBQ.B #1,$254(A6)` ; fins 0f, 10, 19, 1a | déduit : acteurs enfants jamais créés ; un octet hors de l'acteur décrémenté à chaque image |
| `0x31F50` | **CONFIRMÉ pour `20FCE0`** ; infirmé pour `11AD00`, `4CF30` | `20FCE0` libère dans le réservoir `$6E8A/$6EB8`, l'homologue dans `$6E90/$6EBD` ; fin `$1C` | un emplacement perdu et un pointeur étranger dans l'autre pile ; rien de visible connu |
| `0x65180` | écart réel **sans effet** | `21F670` : `ADDQ.B #4,$5(A6)` contre `#2` ; les états 4 et 6 mènent à la même libération | rien (déduit) |
| `0x64D00`, `0x71910`, `0x385E30` | **INFIRMÉ** | vrais homologues de position, tables de même contenu | rien |
| `0x24A90` | **INDÉCIDABLE** (`70C70`) | l'homologue est « type invalide → libération » ; les traces ne séparent pas le relais de son corps | si pris : objet supprimé au lieu de vivre ; l'essai 04 / 04b tranche |
| `0x2FEC0`, `0x688F0`, `0x77750`, `0x143930`, `0x18BC80`, `0x345580` | **INFIRMÉ en l'état** | aucune routine hors « j », aucune exécutée dans 38 traces | rien de connu ; armé pour les chemins hors traces |

- Correctif de principe : `FIN_A0FD0 += 204bb0,207530,207780,20b2a0,20b430,2094a0,20c6e0,21d6c0,21dd90,21ea50,21edc0,20fce0,21f670`
  (`2046C0` reste à part : sa greffe plante en Z3).
- L'essai 04 de la revue a deux faiblesses (préanticipation du 1er mot ; cibles atteintes par `JMP` de table) et ne
  joue pas les fins 07, 0f, 19, 1a, 1c : variante `essais/04b_x6_fins_manquantes.sh` (≈ 25-30 min à 2 places).
- Hors périmètre, à vérifier : la règle « e) équivalente » de `plan.py` ignore les immédiats des `addiu` / `ori` ;
  2 paires sur 411 touchées, dont `0x121150` → `0x3A4E90` (`ADDQ.W #2,$16(A6)` contre `SUBQ.W #2`, objet du 1er round).

## 3. Transitions — détail `p3_transitions.md`

- **E1 scène A → `$C` : INFIRMÉ.** La revue s'est trompée de routine (`u254CA4` = sortie de la sélection d'Upper, code
  mort). La fin sort par la scène 8 (GAME OVER), qui sort vers `$C` par le fondu bloquant d'Hyper : bases posées écran
  noir. 85 journaux sur 85 du banc des fins et l'essai 07b le montrent. Effet : aucun.
- **E3 menu de pause : INFIRMÉ.** Le menu `0x295A0` n'est armé que par le bit START de la manette native PS2, hors du
  module ; dans l'image 68K l'enveloppe est `LEA ; LEA ; BRA.S` vers `RTS` : code mort. `0x28608` est la sortie de
  l'écran OPTION, hors partie. Effet : aucun, rien à essayer.
- **E2b nouveau challenger : CONFIRMÉ** sur la carte et en combat. La tâche d'Upper copiée `u1346A0` prend le Start si
  `$8E = $8D = 0` ; la sortie `u1353A0` ne masque rien et `scene2_bases` pose les bases d'Hyper à l'image suivante sur
  la VRAM d'Upper. Captures de 08b : carte 0107-0109, combat 0107-0111 (`essais/preuves/`). **Désaccord avec
  `RESULTATS_ESSAIS.md`** (« infirmé, aucune tuile fausse ») : sa planche saute les captures 108-109. Effet : 3 images
  de tuiles fausses plein écran à chaque défi (+ 2 de couleurs fausses depuis un combat) ; bénin, sans plantage.
  Face-à-face : porte ouverte en statique, non tranché au banc → `essais/01_e2b_face_a_face.sh` (≈ 3 min).
  Correctif : masque de la forme `masque_sortie` (e46) autour de `u1353A0`, bases d'Hyper retardées dans `scene2_bases`.
- À côté : `<workspace>/work/revue_greffe/outils/atteint.py` ne suit pas les appels lointains `lui ; addiu|ori ; jalr` (forme de tous
  les appels entre copies) : le « non atteint » du verdict E4 (longjmp) est à refaire (`outils/atteint2.py`).

## 4. Les « probables »

### 4a. Les 7 du tri des 128 (cases laissées brutes) : INFIRMÉS comme pointeurs — 7 données
Preuve par la structure voisine (`<workspace>/work/revue_greffe/outils/ctx.py`) : rien à corriger, rien à essayer.
- `0x928B70`, `0x92D9E4` `(00C0, 0090)` : champ (x, y) d'enregistrements `1849 4x00 0xE0 000x` ; le frère `0x928B50`
  porte `(00C0, 00C0)`. `0x92E97C` `(00D0, 0090)` : frères `(00D0, 00D0)` et `(00D0, 00C0)`. `0x99EDC0`
  `(00B0, 0090)` : frère `(0140, 00B0)`. `(192, 144)` est le centre de l'écran.
- `0x8B6468` `(0000, 0085)` : compteur d'enregistrements de 20 o : `0083, 0084, 0085, 0086, 0087` à la même place.
- `0x64ACD0` `(0002, 00B2)` : en-tête d'une trame de type 2 `[2, $B2, n−1 = $1E, 0, pointeur 0xB05D78]` ; seul le
  pointeur qui suit est relogé, à raison.
- `0x6D33D8` `(0020, 008C)` : case d'une table de codes de tuiles sur 16 bits (la ligne précédente a `4669 4677` à la
  même place).

### 4b. Probables de R1 (75), R2 (5), R4 (104) : cases RELOGÉES sans preuve
Test des « frères » (`outils/freres.py` → `essais/freres.txt`) : la même place d'un enregistrement voisin contient une
valeur qui ne peut pas être un pointeur (A : même mot de commande, autre argument ; C : suite arithmétique) = preuve
forte ; B (enregistrement périodique de même forme) = indice.

| famille | cases | donnée, preuve forte | indice | rien |
|---|---|---|---|---|
| R1 probables | 70 | 9 | 17 | 44 |
| R1 probables, zone des décors | 5 | 3 | 1 | 1 |
| R2 probables | 5 | 2 (+ 3 relues à la main : données) | 0 | 0 |
| R4 probables | 104 | 92 | 1 | 11 |

- **R2 : les 5 sont des données (confirmé).** `0x67B10C` et `0x67B168` : enregistrements de sprites de 8 o, x en suite
  `0040, 0060, 0080` ; `0x9434E4` : commande `0204 xx` avec les arguments `00A0`, `00C0`, `0080` ; `0x943C98` et
  `0x943CD4` : même commande `020C xx 0010 0016 0800` avec `0090` et `0080`.
- **R4 : 92 sur 104 confirmées données** (régions de scripts et de listes de sprites, mots de commande répétés).
- **R1 : 44 + 1 toujours indécidables en statique** (longs `(0000, $00A0)` isolés, sans frère). Les journaux de lecture
  d'Upper sont au mot, sans taille d'accès ni PC : ils ne disent pas si la case est lue en long.
- Effet en jeu si la case est une donnée lue : mot haut + `$18` (R1 : +24 sur une ordonnée ou un argument) ou valeur
  sans rapport (R2 / R4). Aucun effet mesuré à ce jour (essai 02 étape A : banc des décors inchangé ; 02b : deux tables
  non lues en Arcade Ryu Z3).
- **Essai prêt : `essais/03_sonde_probables.sh`** (≈ 10-12 min à 2 places, sans construction) : prise de lecture sur
  les 184 copies (`essais/sonde_probables.tsv`, adresses 68K contrôlées sur `T_615D70` → `df2040`), par (case, PC),
  moitié basse / haute : lue en long au même PC = pointeur possible (à retirer des listes) ; lue par mots = donnée
  (à exclure) ; non lue = sans effet dans ces parties. Jamais lancé.

---

## Essais déposés dans `flou/essais/` (aucun lancé ; tous n'écrivent que là)

| script | durée | tranche |
|---|---|---|
| `02_graine_figee_decors.sh` | ≈ 8-10 min, 2 places | point 1 : tirage seul ? |
| `03_sonde_probables.sh` | ≈ 10-12 min, 2 places | point 4b : 184 cases lues en long ou en mots |
| `04b_x6_fins_manquantes.sh` | ≈ 25-30 min, 2 places | point 2 : fins 07, 0f, 19, 1a, 1c ; `0x24A90` |
| `01_e2b_face_a_face.sh` | ≈ 3 min, 1 place | point 3 : E2b pendant le face-à-face |


<!-- source: <workspace>/work/revue_greffe/flou/p2_homologues.md -->

## File `<workspace>/work/revue_greffe/flou/p2_homologues.md`

# P2 — X6 : les 14 homologues non injectifs encore renvoyés à Hyper (ro9a37) — verdict par cible

Agent `flou` / sous-tâche « homologues X6 », 12/11/2026. ANALYSE STATIQUE SEULE (aucun émulateur, aucune construction).
Matière : `<workspace>/work/greffe_arcade/e47/ro9a37_fige` (module, `greffe.json`, carte), `<workspace>/work/modules_son/ro5` (Upper), `ro9` (Hyper),
traces d'opcodes d'Upper déjà faites (`<workspace>/work/greffe_arcade/traces/gagneXX|perdu*/couv.txt`, 38 parties), couverture e39
(`<workspace>/work/greffe_arcade/e39/couv`). Essai 04 de la revue : **pas encore passé** au moment d'écrire (relu `RESULTATS_ESSAIS.md` et
`ETAT_essais.md` à la fin : 04 toujours « à faire »).

Légende : **lu** = prouvé par lecture du désassemblage / des octets ; **mesuré** = traces d'Upper existantes ; **déduit** = raisonnement.

## 0. Résumé

| cible Hyper | routines d'Upper (hors « j ») | verdict | effet en jeu |
|---|---|---|---|
| `0xA0FD0` | 35 (1 imposé + 7 « g ») | **CONFIRMÉ** (8/8 exécutées dans les fins d'Upper) | fins de Guy (07 : 5 états), Sagat (0b : 2), perso `$18` (1) : acteurs figés dans leur état (jamais d'avance d'état, pose / apparition manquante) ; `$10D(A5)` écrit à chaque image |
| `0x84EA0` | 6 (4 « g ») | **CONFIRMÉ** (4/4 exécutées) | fins `0f`, `10`, `19`, `1a` : émetteurs d'acteurs muets (aucun acteur enfant créé) + `SUBQ.B #1,$254(A6)` à chaque image hors de l'acteur (octet d'un autre emplacement décrémenté) |
| `0x31F50` | 28 (2 imposés + 1 « e ») | **CONFIRMÉ pour 1** (`0x20FCE0`, fin `1c`) ; INFIRMÉ pour `0x11AD00` (équivalente) et `0x4CF30` (pointeur mort) | fin du perso `$1C` : l'acteur est libéré dans l'AUTRE réservoir (`$6E90/$6EBD` au lieu de `$6E8A/$6EB8`) : fuite d'un emplacement + emplacement étranger dans l'autre liste ; pas d'effet visible connu |
| `0x65180` | 21 (3 « e ») | écart statique réel pour 1 (`0x21F670` : `ADDQ.B #4` contre `#2`), **SANS EFFET** (déduit) ; 2 autres identiques | rien : les états 4 et 6 de l'aiguilleur mènent à la même libération |
| `0x64D00` | 5 (1 « e ») | **INFIRMÉ** | rien (vrai homologue de position, code des persos d'Hyper) |
| `0x71910` | 2 (1 imposé) | **INFIRMÉ** | rien (vrai homologue de position) |
| `0x385E30` | 2 (1 « f ») | **INFIRMÉ** | rien (même code, mêmes tables, anim de même structure) |
| `0x24A90` | 5 (0) | **INDÉCIDABLE** pour `0x70C70` ; les autres non empruntés dans les traces | si pris : objet libéré avec message « type invalide » au lieu de son code ; essai 04 tranche |
| `0x2FEC0` `0x688F0` `0x77750` `0x143930` `0x18BC80` `0x345580` | 25 / 2 / 3 / 3 / 2 / 2 (0) | **INFIRMÉ en l'état** (aucune hors « j », aucune exécutée dans 38 traces) | rien de connu ; risque résiduel = chemins d'Arcade hors traces |

Trois constats annexes (hors des 14 cibles, trouvés en chemin) : §6.

## 1. Méthode et outils (tous dans `flou/outils/`)

- `p2_liste.py` : routines d'Upper par cible et classe (`greffe.json` `decisions`). 141 routines : 120 « j », 21 hors « j »
  (4 imposées, toutes « j » dans `decisions_anciennes_e12.json` : `0x4CF30`, `0x20FCE0`, `0x6C000`, `0x2046C0` ; 5 « e », 11 « g », 1 « f »).
- `p2_refs.py` → `p2_refs.txt` : toutes les références d'Upper à chaque routine (jal / j, mot de données, lui+addiu) et leur
  sort dans ro9a37 (site copié ? valeur à l'emplacement de la copie). **Lu : les 141 routines ont TOUTES au moins une référence
  dans une copie** (surtout des entrées de tables d'aiguillage copiées qui valent l'adresse de la cible d'Hyper). Le point 2 de
  la mission (« aucun site d'appel → infirmé ») n'élimine donc rien à lui seul ; il faut savoir si le lecteur de la table est
  copié (`p2_table.py`) et si l'entrée est empruntée.
- `p2_table.py` : pour une entrée de table d'Upper, la table, la routine qui la lit, sa décision et son site copié.
- `p2_cmp.py` : comparaison instruction par instruction du corps d'Upper et de l'homologue d'Hyper.
- `p2_vues.py` → `p2_vues_hors_j.txt`, `p2_vues_j.txt` : passages dans les 38 traces d'opcodes d'Upper. **Piège trouvé** :
  le 1er mot d'une routine est lu par la PRÉANTICIPATION du `RTS` de la routine précédente ; une routine dont SEUL le 1er
  mot est vu n'est pas exécutée (35 des 120 « j » sont dans ce cas, 85 jamais vues). C'est aussi pourquoi la sonde e39 était
  posée à PC + 6.
- `p2_equiv_imm.py` → `p2_equiv_imm.txt` : défaut de la règle « e » (§6.1).

Limite de `index_tables.py` confirmée : sa marque TABLES_DIFFERENTES ne dit pas si l'homologue est faux (`0x64D00`,
`0x71910`, `0x385E30` sont de vrais homologues de position) et elle ne voit pas les écarts sans table (`0x84EA0` ← 4 « g »
sans table, `0x65180` ← `ADDQ #4`). Elle classe « j = non vue en Arcade » alors que « j » veut dire « pas dans la liste
des routines vues en Arcade ET JAMAIS EN VERSUS » (`plan.py` : `x not in BY`) : à lire avec les traces.

## 2. `0xA0FD0` — CONFIRMÉ (8 routines hors « j », toutes exécutées dans une fin d'Upper)

Lu : Hyper `0xA0FD0` = routine de combat (`CMP.W $850(A5),$450(A5)` puis `MOVE.B #1/#2/#3,$10D(A5)` par `0xA16D0/0xA16F0`) ;
elle ne touche pas `A6`. Les 8 routines d'Upper sont des états / gestionnaires d'acteurs de fin du type `$4B` :
« attendre que la phase `$1CA(A5)` atteigne `$7B(A6)` (ou `$78`, `$7D`), puis `ADDQ.B #2,$4(A6)` + anim / vitesse /
`MOVE.B #1,(A6)` ». Chacune est une entrée d'une table d'états COPIÉE lue par un gestionnaire COPIÉ (`p2_table.py`) :

| Upper | table (entrée) | gestionnaire copié | exécutée (mesuré, `p2_vues`) | e39 |
|---|---|---|---|---|
| `0x2046C0` (imposé) | `T_619430` n° 55 | `0x1EFF50` → ro9a `0xE96240` | fin 0b (Sagat), 21/24 mots | vue (296) ; laissée à Hyper exprès (`FIN_SAGAT=foret`, sa greffe plante Z3) |
| `0x20C6E0` (g) | `T_619B18` n° 0 | `0x20C530` → `0xEA833C` | fin 0b (Sagat), 25/27 mots | compte brut **1** → écartée par le seuil « ≥ 3 » de `resume_couv.py` |
| `0x204BB0` (g) | `T_619960` n° 0 | `0x204A00` → `0xEA4C2C` | fin 07 (Guy) 14/14 | **07 jamais mesuré** (absent de `fins_upper.tsv`, noté à tort « sans fin ») |
| `0x207530` (g) | `T_6199F0` n° 0 | `0x207380` → `0xEA588C` | fin 07 (Guy) 19/19 | idem |
| `0x207780` (g) | `T_6199F0` n° 2 | `0x207380` | fin 07 (Guy) 11/16 | idem |
| `0x20B2A0` (g) | `T_619AD0` n° 1 | `0x20B090` → `0xEA772C` | fin 07 (Guy) 20/20 | idem |
| `0x20B430` (g) | `T_619AD0` n° 3 | `0x20B090` | fin 07 (Guy) 20/20 | idem |
| `0x2094A0` (g) | `T_619A60` n° 0 | `0x2092F0` → `0xEA5AFC` | fin `$18`, 15/15 | absente de la liste e39 (53 routines de ro9a29) |

Effet (déduit, conforme à ce qui a été observé pour les 17 déjà corrigées — ETAT e39 : « ces acteurs ne font rien ») :
l'acteur reste dans l'état en question pour toute la scène : pas d'anim suivante, pas d'apparition (`0x20B2A0/0x20B430`
posent `(A6) = 1` et lancent `0x20BC80`), pas de vitesse (`0x20C6E0` : `$54 = -$40`, anim 71). Aucun plantage attendu de
`0xA0FD0` elle-même (elle n'écrit que `$10D(A5)`). Les 27 « j » : 24 jamais vues, 3 préanticipation seule (`0x1E8DF0`,
`0x2031E0`, `0x218FF0`, cohérent avec e39 : compte 0).
Correctif de principe : ajouter `204bb0,207530,207780,20b2a0,20b430,2094a0,20c6e0` à `FIN_A0FD0` (l'interrupteur force
GREFFE, il n'est pas propre à `0xA0FD0`) ; `0x2046C0` reste le cas connu « à reprendre » (commande 10 non réentrante).
Essai : `flou/essais/04b_x6_fins_manquantes.sh` (Guy 07) ; l'essai 04 d'origine couvre 0b et 18.

## 3. `0x84EA0` — CONFIRMÉ (4 « g », exécutées)

Lu : Upper `0x21D6C0` / `0x21DD90` / `0x21EA50` / `0x21EDC0` = état 2 de quatre classes d'acteurs de fin (table des
classes `T_619D30` : gestionnaires copiés `0x21D4D0`, `0x21DBA0`, `0x21E860`, `0x21EBD0`) : `ADDQ.B #1,$3A(A6)` ; à
`$0C` (`$0C`, `$10`, `$1E` selon la routine) : `JSR 0x21F690` (resp. `0x21FAA0`, `0x21FCE0`, `0x21FF20` : crée un acteur
enfant type `$50` classe 7 à la position `T_61A180[$3B]` + hasard), `$3B = ($3B + 1) & 7`, `$3A = 0`. Ce sont des
ÉMETTEURS (un acteur toutes les 12 / 16 / 30 images). Hyper `0x84EA0` = code de combat : `SUBQ.B #1,$254(A6)` ;
`D5 = D6 - $254(A6)` ; si ≠ 1 : `JSR 0x8D480` (`MOVEQ #1,D7` sous sauvegarde : sans effet). Vrai homologue seulement de
`0x080850` (« j », 2 lignes d'écart). Sites dans ro9a37 (lu) : 4 `jal` dans les copies (`0xEB7180`, `0xEB7370`,
`0xEB7EB0`, `0xEB80A0`, depuis les états 0 qui tombent dans l'état 2) + 4 entrées de table copiées (`T_61A070/90/C0/D0` n° 1).
Mesuré : `0x21D6C0` fins 0f, 10, 19, 1a ; `0x21DD90` fin 0f ; `0x21EA50` et `0x21EDC0` fin 1a (18/18 mots chacune).
Effet (déduit) : dans ces fins, l'émetteur ne crée aucun acteur enfant (particules / éléments répétés absents) et, à
chaque image où il vit, l'octet `A6 + $254` (hors de l'acteur : champ `$54` d'un autre emplacement du réservoir, ou
au-delà) est décrémenté. Pas de plantage au banc (85/85) : effet visuel + corruption lente. Les 2 « j » : jamais vues.
Correctif : `FIN_A0FD0+=21d6c0,21dd90,21ea50,21edc0` (leurs sous-routines `0x21F690…` sont à greffer par fermeture).
Essai : 04b (fins 0f, 19, 1a) ; l'essai 04 couvre 10.

## 4. `0x31F50` — CONFIRMÉ pour `0x20FCE0` seulement

Lu : Hyper `0x31F50` = relais `JMP 0x391AD0` (libération d'objet : en-tête effacé, `$9(A6) = $1C`, empilé sur
`$6E90(A5)`, `$6EBD(A5) += 1`). Attention aux constantes signées (`lui 0x58 ; addiu 0x1ad0`… `lui 0x2c ; addiu 0xd6e0`
= `0x2BD6E0`) : l'outil de la revue et une lecture rapide se trompent de `0x10000`.
- `0x11AD00` (e) = `JMP` Upper `0xCDEE0`, identique à Hyper `0x391AD0` à la base RAM près (70 instr., 2 lignes) :
  **équivalente, sans effet**.
- `0x20FCE0` (imposé, ex-« j ») = `JMP` Upper `0xCD6E0` = libération dans le réservoir PRINCIPAL (`$9 = $10`, pile
  `$6E8A(A5)`, `$6EB8(A5) += 1`, + remise à zéro de `$26-$2F`, `$31`). Elle est aux entrées 2 et 3 (états 4 et 6) de
  `T_619BF0`, table copiée lue par le gestionnaire copié `0x20F2E0` (→ ro9a `0xEAA590`). Mesuré : exécutée dans la fin
  du perso `$1C` (mots `$4B9BA/$4B9BC` à l'image 45927 de `gagne1c`). **Défaut réel** : dans la greffe l'acteur est rendu
  à l'autre réservoir : un emplacement du réservoir principal est perdu (compteur `$6EB8` non remonté) et la pile
  `$6E90` reçoit un pointeur étranger (débordement d'un mot possible si ce réservoir est plein-libre). Effet visible :
  aucun connu (fin `1c` aboutie au banc) ; latent jusqu'à la remise à zéro des réservoirs. Correctif : `FIN_A0FD0+=20fce0`
  (la cible `0xCD6E0` est déjà « e » → Hyper `0x391590`, équivalente).
- `0x4CF30` (imposé, ex-« j ») = `JMP` Upper `0x15ADD0` (aiguillage de scène sur `$8(A5)`, rien à voir avec une
  libération) ; exécutée dans Upper (gagne1d, gagne21). MAIS sa seule référence est `T_60C758` n° 0, lue par Upper
  `0x4CEC0` qui n'est PAS copiée (décision HYPER `0x61C90`, qui lit sa propre table `T_5B41D8`) : la copie de l'entrée
  est un pointeur mort. **INFIRMÉ** pour la cible (le renvoi `0x4CEC0` → `0x61C90` lui-même relève de X5, non examiné).
- 25 « j » : 18 jamais vues, 7 préanticipation seule.

## 5. Les autres cibles

- **`0x65180`** (`ADDQ.B #2,$5(A6)` ; `RTS`). `0x17EFF0` et `0x1CDD70` : 7 instructions identiques (lu) → sans effet.
  `0x21F670` : **`ADDQ.B #4,$5(A6)`** (lu ; unique dans Upper, absente d'Hyper) classée « e » à tort (§6.1) ; 19 `jal`
  copiés depuis les classes d'acteurs de fin (`0x21B920`… : « si la phase a dépassé `$78(A6)` : `JSR 0x21F670` ») ;
  exécutée dans 14 fins (mesuré). Dans la greffe l'état `$5(A6)` passe de 2 à 4 au lieu de 6. Or l'aiguilleur de ce type
  (`T_619F30` copiée, ro9a `0xDEA200`) a les entrées 4 ET 6 égales (`0x10A87C0` = `JMP 0x391590`, libération qui remet
  `$4-$7` à zéro) : **sans effet** (déduit ; suppose que les 19 sites ne sont atteints qu'à l'état 2, ce que dit la
  lecture : seule référence à la table des classes en Upper `0x211B94`, entrée 2 de `T_619F30`). À greffer par propreté
  (`FIN_A0FD0+=21f670`). 18 « j » : clones identiques du code des persos (17 préanticipation seule, 1 jamais).
- **`0x64D00`** ← `0x6111B0` (e) : aiguilleur `$5(A6)` → `T_60D110` ; Hyper : même code, `T_5B43A0`. Lu : les 4 entrées
  se correspondent à décalage constant `+0x3B50` (`0x61270→0x64DC0`, `0x61310→0x64E60`, `0x61630→0x65180`,
  `0x61650→0x651A0`), corps de même taille (2 à 10 lignes d'écart = constantes) : c'est le même objet du code des persos,
  gardé chez Hyper par principe. **INFIRMÉ**. Les 4 « j » (`0x1A0620`…) sont des sosies : jamais vues.
- **`0x71910`** ← `0x6C000` (imposé) : aiguilleur `$2(A6)` → `T_60DB58` (7 entrées) ; Hyper `T_5B4E48`, entrées à
  décalage constant `+0x5910`, mêmes tailles. Vrai homologue. **INFIRMÉ** (exécutée dans gagne20 seulement). 1 « j » jamais vue.
- **`0x385E30`** ← `0xFCA10` (f) : init d'un objet d'effet (toutes les parties). Lu : 104 instr., 14 lignes d'écart = 4
  constantes : `T_611DE0` / `T_5C92E0` identiques sur `$40` octets ; table d'anim `0x958310` / `0x69D820` de même
  structure (13 entrées, pointeurs décalés d'une constante `0x2BAAF0`) ; `0xC84A0` ≡ `0x38D3B0` ; `jal` vers `0xFCBB0`
  → `0x385FD0` (décision f, voisine de position). **INFIRMÉ** (non comparé : les images pointées par l'anim).
- **`0x24A90`** (5 « j ») : Hyper = `jal 0x24A30` = gestionnaire « type d'objet invalide » (message `0x5AF4A0` avec
  `$2/$3(A6)`, puis libération `0x391590` ; c'est l'entrée `$1A` de `T_5C5720`). Les 5 routines d'Upper sont des relais
  `JSR suite ; RTS` vers 5 codes différents : l'appariement par forme est faux pour toutes. Empruntées ? `0x301FC0` :
  le `jal` copié (ro9a `0xED5970`, Upper `$71CB2`) n'est exécuté dans aucune trace ; sa table `T_748ED8` et celle de
  `0x3A03C0` sont lues par du code NON copié (`0x229D20` → Hyper) : pointeurs morts. `0x2EB560` : lecteur non copié.
  `0x919B0` : constante dans la copie ro9a `0x1658` (non examinée plus loin). **`0x70C70`** : entrée n° 5 de `T_60DC20`,
  lue par le gestionnaire COPIÉ `0x6F920` (ro9a `0x020EAC`, aiguillage sur `$2(A6)`), relais vers `0x70C90` dont le
  corps est exécuté dans TOUTES les traces (image 2145) ; le relais et le corps ont le même PC dans la carte, les traces
  ne les séparent pas (le corps est aussi l'entrée n° 6). **INDÉCIDABLE** : si le sous-type 5 existe en Arcade, l'objet
  est libéré avec le message au lieu de vivre. L'essai 04 (cible `0x24A90`, n'importe quelle partie, vers l'image ≈ 2100
  du 1er combat) tranche ; attention à la préanticipation (poser à PC + 2).
- **`0x2FEC0`** (25 « j ») : lu : chaque routine d'Upper est un aiguilleur de 26 instr. avec SA table (`0x5AFB0` :
  index `$8C31(A5)`, 2 entrées ; `0x708D0`… : `$5(A6)`), Hyper `0x2FEC0` = aiguilleur `$5(A6)` → `T_5B2D10` : aucune
  n'est équivalente. 21 jamais vues, 4 préanticipation seule (`0x708D0`, `0x731C0`, `0x1CF1C0`, `0x1BEB40`). Toutes ont
  une entrée dans une table copiée lue par une copie : le défaut est armé, pas emprunté dans les 38 traces. **INFIRMÉ en l'état.**
- **`0x688F0`** (2 « j »), **`0x77750`** (3), **`0x143930`** (3), **`0x18BC80`** (2), **`0x345580`** (2) : aucune
  hors « j », aucune vue dans les traces (jamais). Corps très différents pour `0x3B0DC0`/`0x688F0` (48 / 20 instr.),
  `0x2D0FC0`/`0x143930` (67 / 246), `0xE0610`/`0x18BC80` (12 / 90) : homologues faux, mais non empruntés. **INFIRMÉ en l'état.**

Risque résiduel commun aux 120 « j » : les 38 traces = 36 persos gagnants (un style chacun) + 2 parties perdues ; pas
d'autre style, pas de 2e joueur, pas de combats spéciaux hors tirage. L'essai 04 (retour dans une copie) le borne pour
les parties jouées ; son critère manque les cibles atteintes par `JMP` de table (retour = appelant de l'aiguilleur, qui
peut être du code d'Hyper) et le 1er mot subit la préanticipation : 04b corrige les deux.

## 6. Constats annexes (hors des 14 cibles)

1. **Règle « e) équivalente » fausse sur les immédiats** (`etape2/plan.py`, `equivalent()` : `nw()` masque les 16 bits
   bas de tout `addiu` / `ori`, pas seulement de ceux qui complètent un `lui`). `p2_equiv_imm.py` : 2 paires « e » sur 411
   ont un immédiat libre différent : `0x21F670` → `0x65180` (`#4` / `#2`, §5) et **`0x121150` → `0x3A4E90`**
   (`ADDQ.W #2,$16(A6)` contre `SUBQ.W #2,$16(A6)`, puis `CMPI.W #$100,$16(A6)`). `0x121150` est l'entrée n° 2 de
   `T_613020`, copiée (ro9a fichier `0xBF32F8` = `0x3A4E90`), lue par le gestionnaire copié `0x120DC0` (ro9a `0xE2ED20`) :
   objet posé à `Y = $D0` qui monte de 2 jusqu'à `$100` au 1er round (attend `$C(A5) = 4`) ; sa jumelle `0x11BE50`
   (`$130` → `$100`, SUBQ) est le vrai homologue. Exécutée dans les 38 traces d'Upper. Dans la greffe, SI ce gestionnaire
   copié sert (le combat est celui d'Hyper : à vérifier), l'objet part vers le bas et n'atteint jamais `$100`. Essai
   précis : point d'entrée 68K sur la copie `0xE2ED20` + sur Hyper `0x3A4E90` (PC + 2), partie Ryu Z3, 1er round ; on
   attend soit 0 entrée depuis la copie (gestionnaire inutilisé : sans effet), soit `$16(A6)` qui décroît depuis `$D0`.
2. **Couverture e39 incomplète** : Guy (07) et `1a` n'ont pas été mesurés (`fins_upper.tsv` : « - »), le seuil « ≥ 3 »
   écarte les états exécutés une seule fois (`0x20C6E0`), et la liste datait de ro9a29 (`0x2094A0` absente).
3. `0x4CEC0` → Hyper `0x61C90` (imposé, ex-« j ») : aiguilleur `$4(A5)` exécuté dans Upper (gagne1d, gagne21) et renvoyé
   à Hyper avec la table d'Hyper : à regarder avec X5.

## 7. Essai proposé

`flou/essais/04b_x6_fins_manquantes.sh` (NON ESSAYÉ ; ≈ 10 min à 2 places + ≈ 15-20 min pour Guy ; n'écrit que dans
`flou/essais/`) : fins 0f, 19, 1a, 1c, 07 ; points d'entrée à PC + 2 sur `0x31F50`, `0x84EA0`, `0xA0FD0` ; cas réel =
retour dans une copie OU entrée pendant la fin (`$FF8004 = $A`) dans une routine de combat d'Hyper. Attendu si les
verdicts ci-dessus sont justes : `0xA0FD0` pendant la fin 07 ; `0x84EA0` pendant 0f / 19 / 1a ; `0x31F50` avec retour en
copie pendant 1c. Pour l'effet à l'écran : captures de la fin de Guy (greffe contre Upper) aux images où Upper passe par
`0x20B2A0` / `0x207530` (≈ 96 100 – 99 000 de `gagne07`).


<!-- source: <workspace>/work/revue_greffe/flou/p3_transitions.md -->

## File `<workspace>/work/revue_greffe/flou/p3_transitions.md`

# Point 3 — transitions E1 (scène A), E3 (menu de pause), E2b (challenger sur un écran d'Upper)

Sous-tâche `sfa3ha: transitions` de l'agent `flou`, 12/11. Analyse statique seule sur **ro9a37**
(`<workspace>/work/greffe_arcade/e47/ro9a37_fige`), plus lecture des traces déjà produites (aucun émulateur lancé ici).
Écrit au fil de l'eau : un verdict par point dès qu'il est établi. Adresses : « fichier » = décalage dans
`ro9a_module.bin` ; `uXXXX` = décalage fichier d'Upper (ro5) ; 68K = `b9/carte_image.txt`.
Outils : `flou/outils/refs.py` (qui référence une adresse d'exécution), `flou/outils/orig.py` (copie ↔ Upper).

## E2b — challenger pendant un écran d'Upper : **CONFIRMÉ (carte ET combat, captures du banc) ; face-à-face : porte ouverte en statique, banc à refaire**

### Qui teste l'arrivée du challenger : la tâche d'Upper copiée, pas Hyper
- Tâche `u1346A0` (racine de la greffe, copie `0xE34830`, 68K `$0A17BA`) : à chaque image, pour J1 puis J2,
  `0xE34910` ; joueur inactif (`$101(A6) = 0`) → aiguillage `$105(A6)` (table `0x613190` d'Upper, 6 entrées).
  - état 2 (`u134940`, 68K `$0A182C`) : porte `$105(A5) | $14B(A5) | $107(A5) | $8E(A5) | $8D(A5) = 0` et
    `$A5(A5) = 0` ; puis `u136EF0` (68K `$0A1D14`) : FRONT de Start (`$62(A5) AND NOT $63(A5)`, bit du joueur).
    Un Start appuyé pendant que la porte est fermée est donc PERDU.
  - état 4 (`u134F60`) : sous-état 0 (`u135040`, 68K `$0A1930`) attend `$8E | $8D | $8B = 0`, `$B9 = 0`, `$AA = 0`,
    puis réserve l'objet de transition d'Hyper `JSR 0x3D6B0` avec `D0 = 1` (bandeau) ; pose `$8B = $8D = $8A = 1`.
    Sous-état 2 (`u1353A0`, 68K `$0A19D0`) : `TST.B $8A(A5) ; BMI` → `MOVE.W #2,(A5)` et `A5+2…$17 = 0`
    (`$0A19DA`), `$8B = 0`. **Ni masque de `$32(A5)`, ni fondu, ni effacement** (seuls appels : `0xE35660`,
    `0xE35630` = `JSR 0x229950`).
- `$8A = $FF` est posé par l'objet bandeau d'Hyper (fichier `0x3D68C`, 68K `$00AE74`) : glissement, attente `$20`
  images, puis `$8A = $FF`, `$10E(A5) = 1`. Aucun fondu : le bandeau « HERE COMES A NEW CHALLENGER » reste posé sur
  l'écran d'Upper intact jusqu'à la bascule.
- Bascule : image n = scène 0 d'Hyper (`A5+4` 0 → 2), bases encore celles d'Upper ; image n+1 = 1re image de la
  scène 2, talon `scene2_bases` (pose les bases d'Hyper à CHAQUE image de la scène 2 en Arcade, `greffe3.py` l. 837).
  La sélection « challenger » d'Hyper ne masque pas les couches et met 3 images à repeindre les plans.

### Quand la porte `$8E` / `$8D` est-elle ouverte
- `$8E = 1` à l'init de la scène 4 (copie `u2615D0`, `0xECA924`). Remis à 0 par l'init des écrans `A5+8 = 2`
  (`0xEC7FBC` = `u25CBBC`, `0xEC5390` = `u258E10`), l'init de l'écran `A5+8 = 4`, `A5+$C = 0` (face-à-face,
  `0xEC733C` = `u25AE7C`) et les intros de manche du combat (`u2665C0`, `u266A60`, `u26730C`, `u26786C`). Ces écrans
  gèlent leur minuterie tant que `$8B(A5)` ≠ 0 (`TST.B $8B(A5) ; BNE`, 68K `$0BA02C` / `$0BA052`, `$0B9CDA`) :
  **ils sont écrits pour recevoir un challenger.**
- `$8D = $FF` (rideau en cours) : posé à la fin d'un écran avec la réservation du rideau (`JSR 0x3D6B0`, `D0 = 0` ;
  face-à-face `0xEC7778-0xEC7798`, Hyper `0x31F4B8-0x31F4D8`), remis à 0 par la fin de l'objet rideau d'Hyper
  (`0x3BFC4`). Le face-à-face n'avance qu'une fois `$8D = 0` (Hyper `0x31E318`, sous-état 0 de `0xEC75A0`).
- Fenêtres : écrans `A5+8 = 2` (carte) = une fois le rideau fini ; face-à-face = du rideau fini à la fin de l'écran ;
  chargement du décor (`A5+8 = 4`, `A5+$C = 2 / 4`) : fermé (`$8E = 1`, `$8D = $FF`) ; combat : ouvert.

### Preuve au banc (essais 08b de l'agent `essaisgreffe`, 12/11, lus dans `essais_demain/` ; rien relancé ici)
- CARTE, `cmp/e2b_carte.txt` : Start J2 pris à 650 (état 2/4/2) → **737 : état 2/2, bases `$4400/$440/$4A0` ;
  738 : `A5+8 = 2`, bases `$300/$340/$3A0`, `$32(A5)` reste `$1B0E`**. Captures
  `traces/e2b_carte/snap/sfa3hx/0106.png` (737 : carte juste + bandeau), **`0107`-`0109` (738-740 : la carte d'Upper
  en pavés unis, bandeau sur un rectangle bleu)**, `0110` (741 : fond de la sélection). Planche :
  `flou/essais/preuves/e2b_carte_104_115.png`.
- COMBAT (témoin de 08b, `cmp/e2b_combat.txt`) : **902 : état 2/2, bases d'Upper ; 903 : bases d'Hyper, `$32` reste
  `$2D0E` jusqu'à 908.** Captures `traces/e2b_combat/snap/sfa3hx/0106.png` (902 : décor juste + bandeau),
  **`0107`-`0109` (903-905 : le décor d'Upper en tuiles fausses, vert quadrillé)**, `0110`-`0111` (906-907 : fond de
  la sélection avec les palettes du décor, magenta / vert), `0112` (908 : juste). Planche :
  `flou/essais/preuves/e2b_combat_105_116.png`. Le défaut ne se limite donc PAS aux écrans d'Upper cités par la
  revue : tout combat de l'Arcade (décor d'Upper, bases `$4400/$440/$4A0`) y passe.
- DÉSACCORD avec `RESULTATS_ESSAIS.md` (ligne 08b : « INFIRMÉ pour la carte, aucune tuile fausse visible ») : la
  planche `cmp/e2b_carte_planche.png` saute les captures 108-109 et sa case 107 montre déjà le rectangle bleu en
  pavés ; le témoin combat, plus lisible, n'a pas été regardé. À corriger dans ce tableau : **CONFIRMÉ**.
- FACE-À-FACE (`cmp/e2b_vs.txt`, impulsions à 711 / 741 / 771) : challenger non accepté. Non concluant : la tournée
  abrège le face-à-face par Start / bouton 1 de J1 (`A5+$C = 0` ≈ 25 images : 816-841 dans
  `<workspace>/work/greffe_arcade/traces/c18_defi_j1/journal.txt`), le rideau tient `$8D = $FF` au début, le test est un front, et les
  impulsions tombaient toutes les 30 images. « INFIRMÉ de fait » est trop fort → `flou/essais/01_e2b_face_a_face.sh`
  (impulsions de 3 images sur 6, J1 passif 240 images, journal de `$8A/$8B/$8D/$8E` image par image).
- Réserve : au banc MAME les tuiles d'Upper lues avec les bases d'Hyper sortent en pavés ; au cœur ce seront d'autres
  tuiles, mais le mécanisme (bases du fork prises à l'affichage, VRAM d'Upper) est celui du CONTINUE d'avant e46.

### Effet en jeu et correctif
- Start J2 (avec crédit) pendant un combat de l'Arcade ou pendant la carte : après le bandeau, 3 images (≈ 50 ms) de
  tuiles fausses plein écran, puis (depuis un combat) 2 images du fond de la sélection aux couleurs du décor. Bénin
  (aucun plantage, la partie continue : J2 choisit, 2 manches, retour à l'adversaire), mais visible à chaque défi.
- Correctif (ro9a38, à construire) : talon autour de la sortie de `u1353A0` (68K `$0A19DA`), forme `masque_sortie`
  d'e46 : `ANDI.W #$FFF1,$32(A5)` + même valeur dans `$804166`, bases d'Upper GARDÉES ; et dans `scene2_bases` ne
  poser les bases d'Hyper (et lever le masque, `ORI.W #$E,$32(A5)`) qu'à partir de la 4e image de la scène 2 quand
  on vient d'un défi, car la sélection « challenger » ne réécrit pas `$32` toute seule depuis la carte (elle le fait
  depuis un combat, à +6 images : `$2D0E` → `$1B0E`). À valider par 08b (captures 106-112 propres).

## E3 — menu de pause du portage PS2 (`0x29C08`, `0x29C60`, `0x28608`) : **INFIRMÉ (inatteignable dans le fork arcade)**

### Chaîne d'appel remontée (MIPS de `ro9a_module.bin`, code d'Hyper inchangé)
- `0x29C08` (reprise en scène 4, `A5+8 = $A`) et `0x29C60` (retour au titre) sont deux cas de l'automate du menu de
  pause `0x295A0` (C du portage, table de sauts `0xB67160`, 11 choix). Seul appelant : `0x2957C`, dans l'enveloppe
  `0x29470`, qui n'aiguille que si l'octet `[12]` de la structure de pause (`0xB67260`) vaut 1 (init `0x21BA70` /
  `0x21BDB0`) ou 2 (menu). Seul appelant de l'enveloppe : la boucle principale `0x3EFD0` (chaque image).
- `[12]` n'est mis à 1 que par `0x2C440` (`0x2C520` pour J1, `0x2C5C0` pour J2), appelé par l'état de K.O. du combat
  d'Hyper (`0x9C974`). Condition d'entrée : **bit `$800` (START) du mot de manette natif de la PS2, `0x19E6B0` (J1) /
  `0x19E70C` (J2)**, adresses de l'exécutable hôte, hors du module ; plus `$8B = $8A = 0` et le joueur actif (`$AD`).

### Ce que l'image 68K en a gardé (octets de `b9/roms_ro9/sfa3ud/sz3ud.03c`, lus à la main)
- Entrée de pause, 68K `$008802-$008836` : `TST.B $8B(A5) ; BNE ; TST.B $8A(A5) ; BNE ; BTST #0,$AD(A5) ; BEQ ;
  TST.B $C321(A5) ; BNE ; MOVE.B #1,$8E(A5) ; …; RTS`. **Aucune lecture de manette, aucune écriture de la structure
  de pause** : le traducteur a retiré le test du mot natif et les accès à `0xB67260` ; il ne reste que l'effet de bord
  `$8E(A5) = 1` (porte du challenger fermée pendant l'état de K.O., sans conséquence).
- Enveloppe, 68K `$0082DE` : `49ED 0400 4DED 0400 600C` = `LEA $400(A5),A4 ; LEA $400(A5),A6 ; BRA.S $82F4` (→ `RTS`).
  Les deux `beq` sur `[12]` ont disparu : les appels de l'init et du menu (`$0082E8`, `$0082F0`) sont du code mort.
  `hooks_fork_ro9.json` classe d'ailleurs `0x295A0` « natif du module » (site `0x2957C`).
- Double verrou donc : l'état de pause ne peut pas être armé (pas de bouton : le START de la manette PS2 n'existe pas
  en arcade, et son test n'est pas traduit) ET, serait-il armé, l'enveloppe ne l'aiguille pas.
- `0x28608` n'est pas le menu de pause : c'est la sortie de l'écran OPTION (`0x2185B0`, `option_sortie_ecran` dans
  `re/connaissances/ro9.tsv`), entrée de la table `0x5B1100`, atteinte seulement depuis la tâche OPTION du menu des
  modes (hors partie, drapeau `$FE00` déjà remis par les scènes 8 / A).

### Effet en jeu
- Aucun : pas de menu de pause dans le fork, donc pas de sortie d'une partie Arcade qui laisserait `$FF7E00` /
  `$FF7E10` posés par ce chemin. La garde proposée par la revue (remise de `$FE00` à l'init du titre) reste une
  ceinture bon marché mais n'a plus de cas connu à couvrir. Rien à essayer au banc.

## E1 — sortie de la fin (scène `$A` → `$C`) : **INFIRMÉ — la transition n'existe pas (la revue s'est trompée de routine)**

### La routine citée par la revue n'est pas la fin
- `u254CA4` (copie `0xEC1464`, 68K `$0B8D0C`, `ADDQ.W #2,$4(A5)`) est l'état 6 de la SÉLECTION d'Upper (scène 2 → 4) :
  routine `0xEC12F0`, entrée de la table `0xDEC200` (copie de la table des états de la scène 2 d'Upper, lue par
  `0xEC03B0` = `u2524B0`, lui-même appelé par la copie de `u261470`, gestionnaire `A5+4 = 2` d'Upper). Les appels
  relevés par la revue (`0xEBDEB0`, `0x97130`, `0x38F2E0`) sont bien ceux de cette routine.
- Et ce code est MORT dans ro9a37 : la table des scènes d'Upper copiée (`0xDEC4B0`) n'est lue que par `0xECA460`,
  entrée de `0xDEC4A0`, lue par `0xEC95F0`, appelée par la seule copie de la tâche de jeu d'Upper `0xEC9450`
  (`u25FEF0`), qui n'a AUCUNE référence (ni `jal`, ni `lui/addiu`, ni mot de données : `flou/outils/refs.py`). La scène
  2 de la greffe est celle d'Hyper (talon `scene2_bases`).

### La vraie machine de la fin
- Scène A = talon `plans_sA` → copie de `u261500` → aiguilleur `u2A300` (copie `0x15B0`, 68K `$00122C`) sur
  `$148(A5)`, table `T_60B380` (copie `0xDDB650`) : type 0 → `0x18F0`, type 2 (Final Battle) → `0x1680` → `0x18F0` ;
  types 4 / 6 / 8 → Hyper `0x24A90` / `0x3BCE50`.
- `0x18F0` : états `A5+8` (table `0xDDB670`) : 0 `0x1960` (init), 2 `0x21E0` (fin + générique), 4 `0x2540`, **6 `0x2580`
  (`u2B2D0`, 68K `$001482`) : `JSR 0xE13E80 ; JMP 0xEBCC00`** = `u24AF70`, qui appelle `0xEBCAD0` (`u24AE40` :
  **`MOVE.W #8,$4(A5)`**, 68K `$0B8036`) et prépare l'écran GAME OVER (`$32 = $270E`). La fin sort donc vers la
  **scène 8**, jamais vers `$C` : aucune écriture de `$C` dans `A5+4` par la scène A. La branche « sortie vers `$C` »
  de `plans_sA` est morte, comme celle de `plans_s6`.
- La scène 8 sort ensuite vers `$C` par `u24B588` (68K `$0B81B2`) : `MOVE.W #$C,$4(A5)` puis, dans la même routine,
  `0x948C0` d'Hyper, fondu BLOQUANT (crée la tâche `0x90630`, boucle `JSR $024938` tant que `$180(A5)` ≠ 0 : relu,
  68K `$0165F2-$01663C`) ; `plans_s8` ne pose les bases d'Hyper et `$FE00 = 0` qu'au retour, écran noir.
- Types 4 / 6 / 8 de `$148` (qui sortiraient par Hyper `0x3BDD90`, `(A5) = 0`, SANS remise de `$FE00`) : posés par
  l'entrée en scène A (`u2712E0`, 68K `$0BB880-$0BB8AE`) si `$15C(A5)`, `$169(A5)` ou `$CC97(A5)` ≠ 0. En Arcade
  (`$C201 = 0`) ils restent nuls : `$169 = 1` exige `$C201 = 3` (copie `0xECA394` ; l'autre site, Hyper `0x960B0`, est dans l'init de scène 4 d'Hyper, que `scene4_mode` n'appelle pas en Arcade) ; `$15C = $FF` exige
  `$14A` du joueur, posé seulement si `$C201 = 2` (`0xE35EEC`) ; `$CC97` n'est jamais posé (un seul `CLR.B`).

### Preuves au banc
- Banc des fins `<workspace>/work/greffe_v161/traces/[fg]77_*` : **85 journaux sur 85** passent `A/6` puis `FIN_A … scene 8` ; aucun ne
  passe de `$A` à `$C`. Ex. `f77_00_A` : A/2 17551-29324, A/4 29324, A/6 29325, scène 8 à 29330, `$C` à 29431 ;
  captures 32-39 : « GAME OVER / TRY AGAIN », gris à `$C`+4, noir ensuite (`flou/essais/preuves/fin_f77_00_A.png`).
- Essai 07b de `essaisgreffe` (`essais_demain/cmp/e1_finp.txt`) : scène 8 à 31728, `$C` à 31831 avec bases `$0400`,
  bases d'Hyper + `fe00 00` à 31853, captures 449-455 noires. Même conclusion, indépendante.

### Effet en jeu
- Aucun défaut : fin → GAME OVER d'Upper (bases d'Upper des deux côtés) → fondu au noir d'Hyper → pose des bases
  d'Hyper sur écran noir → titre. Le correctif envisagé par la revue (`masque_sortie` sur la scène A) est sans objet.

## Remarques pour la revue (hors des trois points)
- `<workspace>/work/revue_greffe/outils/atteint.py` ne suit pas les appels lointains `lui ; addiu ; jalr` (forme de presque tous les
  JSR entre copies d'Upper et code d'Hyper) : il les compte comme « jalr non suivis ». Exemple : depuis les états de la
  scène A il déclare `0xEBCAE4` (`MOVE.W #8,$4(A5)`) « non atteint » alors que `0x2580` y saute. Les « non atteint »
  du verdict E4 (longjmp) reposent sur cet outil : à refaire avec `flou/outils/atteint2.py` (qui suit ces appels ;
  attention, sa fermeture devient vite très large : 2 354 fonctions depuis la scène A).
- E1 scène 6 / 8 et E3 « sorties ordinaires » de la revue : relus, exacts (fondu `0x948C0` dans `u24B588`).


<!-- source: <workspace>/work/revue_greffe/sorties/2e_passe_axe3.md -->

## File `<workspace>/work/revue_greffe/sorties/2e_passe_axe3.md`

# 2e passe — Axe 3 : index des tables partagées Upper / Hyper (ro9a37)

Sous-tâche `sfa3ha` du 12/11. Analyse statique seule (MIPS des modules, aucun émulateur, aucune construction).

- Outil : `outils/index_tables.py` (usage en tête ; ≈ 10 s) → `sorties/index_tables.txt` (787 lignes, sections A, A2, B, B2, C, D).
- Entrées : `<workspace>/work/greffe_arcade/e47/ro9a37_fige` (`ro9a_module.bin`, `greffe.json`, `b9/carte_image.txt`), Upper
  `ro5_usa_prog68k.bin`, copie figée du dépôt **`construction/ro9a37/`** et `releves_ro9a37/` (le dépôt a été renommé ce
  matin, HEAD `bed8b2a` : les chemins `ro9a36/…` du RAPPORT et de l'ETAT n'existent plus ; l'outil prend `ro9a37`, sinon `ro9a36`).
- **v161** : `ro9a_module.bin` et `greffe.json` de ro9a37 = ro9a36 à l'octet ; la sortie de l'outil sur `ro9a36_fige` est
  identique (hors adresses 68K de la carte). Aucun constat T1-T3 ne change avec v161 ; seules les adresses 68K changent.

## Méthode et périmètre

Exécution symbolique linéaire de chaque routine (cases des registres 68K du recompilateur en `0x70001100`, temporaires,
pile). Lecture à « constante de données + reste » = accès à une table ; le reste = l'index (champs `$off(An)`, masques,
décalages). Champs en numérotation **PS2** : octet `$102` = 68K `$0103`, `$116` = `$0117`, `$12b(A5)` = `$012A(A5)`.
Taille d'une table = distance à la constante de données suivante du code (**borne haute**).
Mesure : 3 121 accès dans Upper, 3 644 dans ro9a37 (Hyper 2 297, copies 1 347, talons 0).
**Non vu** : tables atteintes par un pointeur lu en mémoire, registre A reçu en argument ; index qui traverse un appel,
une tête de boucle ou une jonction (215 des 1 347 accès des copies : index « sans feuille », non jugés) ; les 29 talons
(MIPS écrit à la main : 0 accès reconnu, à relire à la main) ; les aides C du portage. Un appelant est substitué sur un
seul niveau. Les « CMP vus » sont indicatifs (dominance non prouvée).
Contrôle à la main (désassemblage `outils/dis.py`) : copie `0xE42B50-8C` (pas de `andi`) contre Hyper `0x311630-80`
(`andi a0,v1,0x7f`) ; copie `0xE4A53C-64` (`sll 2` puis `lw`) ; copie `0x9530-60` (`lui 0x64 / addiu 0xb5a4`, `lb`) ;
Upper `0x33427C-A4` contre Hyper `0x117FB0-8014` (×6 + `$82(A6)`). Les quatre concordent avec la sortie.

## Constats

### X1. Tables d'Hyper lues par les copies : un seul écart de masque, déjà traité — PROUVÉ (dans le périmètre)
54 tables d'Hyper sont lues par une copie d'Upper (section A) ; 42 ont aussi un lecteur d'Hyper vu. Une seule a un masque
présent chez Hyper et absent de la copie : **`T_5c5120[$12A(A5)]`** (copie `0xE42B8C` / `0xE42BBC`, Upper `0x15741C` ;
Hyper `0x311680` avec `ANDI #$7F`). C'est le cas déjà couvert par `EFFET_12A`. L'outil le retrouve seul : il n'y en a pas
d'autre parmi les index suivis. Quatre marques « DIFF » (`T_5c50a0`, `T_5c5240`, `T_5c72a0`, `T_62eba0`) sont des écritures
différentes du même index (registre non suivi d'un côté) ou une table générique lue par plusieurs routines : rien à corriger.
Aucun index borné par un masque ne dépasse une table partagée (DEBORD 0).
- Reste à risque : `EFFET_12A` ne protège que les appels passant par les talons `moteur_plans*` (RAPPORT E4, longjmp).
- Essai (10 min, banc des décors) : sonde d'écriture de `$2A/$2C(A5)` pendant un K.O. par super en ZERO 2, comparer à Hyper seul.

### X2. Ids MAX et tables par perso : aujourd'hui tout lit « Ryu » ; avec un id de base ≥ `$28`, 9 tables débordent — PROUVÉ
Toutes les lectures d'une table par l'id de perso dans les copies passent par **`$116` (perso de base)**, aucune par `$102`
(section C : 21 couples table / index vus, tous « par base » ; cohérent avec les 30 sites INDEX de `patch_116`).
`T_BASE` d'Hyper (`0x5C5300`, 128 o) vaut `$00` pour `$26-$2F` : un perso MAX a donc `$116 = 0` et lit l'entrée de **Ryu**
partout (confirme T1). Si l'on donne aux MAX un id de base propre :
- **`$26` / `$27` : dans toutes les tables** (les tables d'Upper ont 40 entrées, `$00-$27`), mais le contenu est celui
  d'Upper pour ces rangs (souvent la valeur de Ryu ; `T_74c358[$27] = 0x7844FE`, `T_616180[$27] = $0A`, `T_6f72b0[$27] = $6D10`,
  `T_978d1c[$27] = $1450`, `T_97ca90[$27] = 0x97CBCC`) : à remplir, pas de débordement.
- **`$28`, `$29`, `$2D`, `$2E` : hors table** dans 6 tables par la taille, 3 de plus par le contenu :
  - copies d'Upper à 40 entrées : `T_74c358` (longs, site `0xE4A564`), `T_617290` (mots, `0xE6E0E4`), `T_61bbc0` (4 o,
    masque `$3F`, sites `0xEBF544` / `0xEBF56C`), `T_699408` (octets, copie basse `0x9780`) ;
  - table d'**Hyper** partagée `T_63b5a4` (40 octets `$30` puis une autre table ; copie basse `0x9560`, Upper `0x3FF80`) ;
  - `T_97ca90` (longs, `0xE5AB58`) : `$29` → `0x013600C0`, `$2D` → `0x029A029A`, `$2E` → `0x03100364` (pas des pointeurs :
    passage par CONV → lecture n'importe où) ; `T_6f72b0` et `T_978d1c` (mots, sans borne dans le code) : valeurs sans rapport ;
  - par `$7F(A6)` × 4 sans masque (id d'objet, non relié à `$116` par l'outil) : `T_619B50` (40 pointeurs puis
    `0x003FF3A0…`, site `0xEA9718`) et `T_72BDF0` (40 pointeurs puis des mots de données, site `0xEAC52C`).
  - sans risque jusqu'à `$2F` (48 entrées, zéros au-delà de 40) : `T_5c59a0` (Hyper), `T_6132e0`, `T_616180`, `T_61b4e0`,
    `T_61b510`, `T_61b540`, `T_61b650`, `T_61b680`, et `T_5c7bd0` d'Hyper (72 mots).
- Non évalués (index composé) : `T_61b580` (`($13F(A5)-8)×20 + $116`), `T_697fe0` (`(($116 & $1F) << 5) + $127` : **masque `$1F`**
  d'Upper lui-même, un id ≥ `$20` replie sur `$00-$07` comme dans Upper ; un id de base MAX `$26` y lirait la ligne `$06`),
  `T_967bf0` (`D0 + $116`).
- **Conséquence** : garder `$116 ≤ $27` pour les MAX dans la greffe (donc `$2D` / `$2E` ne peuvent pas être leur propre id
  de base), ou prolonger d'abord ces 9 tables. Essai (15 min) : POKE `$116` = `$28` sur J1 à la carte et au face-à-face
  sous MAME avec sonde d'exception d'adresse ; attendu : sprites faux ou `$A08`.

### X3. Règle D4 et ids annoncés `$2D` / `$2E` — PROUVÉ (lecture du tableau)
`regle_d4_decidee.tsv` : `$26` Eagle → `$10`, `$27` Maki → `$0E`, `$28` Yun → `$42`, `$29` Ingrid → `$00`, `$2A-$2F` → `$00`.
Avec Yun = `$2D` et Ingrid = `$2E` : **Yun aura le décor de Ryu au lieu de celui de Fei-Long** ; Ingrid garde `$00` par
coïncidence. Les lignes `$28` / `$29` sont à déplacer en `$2D` / `$2E` (et à remettre à `$00`).
`T_61BE10` d'Upper (copie `0xDEC0E0`, lue par la copie `0xEBFFE4`, index reçu en D0) : 40 octets + 8 zéros ; `$28-$2F`
lisent `$00` (dans la table, pas de débordement) ; `$26` → `$00`, `$27` → `$15` (valeurs d'Upper, différentes de D4).

### X4. Correction de T1 : la grille `0x5C5380` a 40 lignes, pas 48 — PROUVÉ
La constante suivante du code est `0x5C5420` : la grille fait `$A0` octets (40 lignes de 4 ; lignes `$26` / `$27` à zéro).
Les « lignes `$28-$2F` non vides » du RAPPORT (T1) sont le début d'une **autre table** (`30 40 7B 00 / 31 41 7A 01…`).
Hyper lui-même lit la grille par `$116 << 2` (`0x319F94`, `0x31ADA4`) : un id de base ≥ `$28` y déborde aussi.
`T_BASE` et `T_VER` (128 o) sont lus par `$102` chez Hyper (`0x321BD8`, `0x2C6C40`, `0x321C04`) : sans risque jusqu'à `$7F`.
Aucune copie d'Upper ne lit `T_BASE`, `T_VER` ni la grille (les talons ont leurs propres copies : non vus par l'outil).

### X5. Routines d'Upper renvoyées à Hyper : 7 paires à index différent, aucune dans le chemin Arcade relevé — PROBABLE
Section B : 1 063 paires (décision HYPER), 300 accès comparés sur une table appariée, 7 paires diffèrent :
- `0x333F70` → `0x117CA0` (f, moteur) : Hyper indexe `T_5b8940` par **6 × (résultat d'un appel natif `0x4B8900`) + `$82(A6)`**,
  Upper `T_6203c8` par `$82(A6)` seul : la table d'Hyper a six blocs. Juste tant que l'appelant est le moteur d'Hyper.
- `0x419D0` → `0x571B0` (f) : `$14(A3)` contre un registre non suivi ; à lire.
- `0x5AFB0`, `0x5BFB0` → `0x2FEC0` ; `0x60140` → `0x63C90` ; `0x60550` → `0x640A0` (j, non vues en Arcade).
- `0x241A0` → `0x242B0` : seule la base RAM diffère (`$A08400` / `$B88400`) : faux positif.
La liste `HOM_PARTAGES` (50) : les 50 sont en `GREFFE imposé`, rien à comparer (leurs tables `T_6196xx` sont copiées).

### X6. Homologues non injectifs encore renvoyés à Hyper : 14 cibles lisent une autre table — PROUVÉ (statique), effet À CONFIRMER
Section B2 : 58 routines d'Hyper sont l'homologue de plusieurs routines d'Upper ; pour 14, les routines d'Upper lisent des
tables **différentes** entre elles, donc l'homologue unique ne peut pas les valoir toutes. Les plus chargées :
`0x2FEC0` (25 routines d'Upper, chacune avec sa table d'aiguillage `T_60cce0`, `T_60cd18`, `T_60dc60`… ; index
`$8C30(A5)` chez Upper, `$4(A6)` chez Hyper), `0xA0FD0` (35 restantes), `0x31F50` (28), `0x65180` (21), `0x24A90` (5),
`0x64D00` (5). Presque toutes sont en « j) non vue en Arcade » ; **hors « j »** : `0x611B0` → `0x64D00` (e), 3 routines →
`0x65180` (e), 1 → `0x31F50` (e) + 2 imposées, 1 imposée → `0x71910`, 1 imposée + 7 « g » → `0xA0FD0`, 4 « g » → `0x84EA0`,
1 « f » → `0x385E30`. C'est la famille des plantages de fins déjà corrigés un à un (`FIN_A0FD0`, e33-e38).
- Essai (20 min, sans construction) : point d'arrêt sous MAME sur les 14 cibles pendant le banc des fins, avec l'adresse
  de retour ; toute entrée dont l'adresse de retour est dans une copie d'Upper (fichier ≥ `0xE10000` ou < `0x22B00`) est un cas réel.
- Correctif de principe : `force3.py`, étendre `HOM_PARTAGES` aux routines hors « j » de ces 14 cibles (liste dans
  `sorties/index_tables.txt`, section B2), sous interrupteur, puis banc des fins.

### X7. Tables copiées : masque plus large que la table (section A2) — FAIBLE
40 accès : surtout le masque `$7F` (retrait du bit 7) devant des tables de 12 à 40 entrées, comme dans Upper : pas une
borne. À retenir : `T_61bbc0` (`$116 & $3F`, 40 entrées : voir X2) et `T_970f10` (zone des décors, `D2 & $FF` × 16 pour
`$30` octets : taille sous-estimée probable).

## Essais proposés (scripts à écrire par le parent dans `essais_demain/`)

| Essai | Durée | Quoi |
|---|---|---|
| X2 | 15 min | POKE `$116(J1) = $28` (puis `$26`) à la carte, au face-à-face, en combat ; sonde d'exception ; 1 place |
| X3 | 5 min | lecture de `T_D4A` dans le bloc construit aux rangs `$28 $29 $2D $2E` (statique, `greffe_donnees.bin`) |
| X6 | 20 min | points d'arrêt sur les 14 cibles non injectives pendant le banc des fins (85 parties, 6 places) |
| X1 | 10 min | `$2A/$2C(A5)` au K.O. par super en ZERO 2, greffe contre Hyper seul |


<!-- source: <workspace>/work/revue_greffe/sorties/2e_passe_axe4_transitions.md -->

## File `<workspace>/work/revue_greffe/sorties/2e_passe_axe4_transitions.md`

# 2e passe — Axe 4 (registres et variables des deux côtés) et hypothèses des transitions E1-E4

Sous-tâche `sfa3ha` du 12/11, analyse statique seule, sur **ro9a37** (`<workspace>/work/greffe_arcade/e47/ro9a37_fige` : module MIPS,
données et `greffe.json` identiques à ro9a36 à l'octet ; seule l'image 68K change, traducteur v161). Les adresses 68K
sont celles de `b9/carte_image.txt` de ro9a37 ; « fichier » = décalage dans `ro9a_module.bin` ; `uXXXX` = décalage
fichier d'origine dans ro5 (Upper).

Outils (usage en tête de chacun) :
- `outils/registres.py` → `sorties/registres.txt` : table registre × côté (H = Hyper, U = copie d'Upper, T = talon) ×
  sens (écrit / modifie / lit), plus un contrôle sur le MIPS (accès directs `lui $BE` / `$C0`). Option `--detail REG`.
- `outils/atteint.py DEPARTS SITES` : fermeture des appels directs du MIPS (les `jalr` ne sont pas suivis : comptés).

## Axe 4 — constats

### A1. Aucune copie d'Upper n'écrit un registre matériel — STRUCTURE SAINE (prouvé)
- `$8040xx`, `$8041xx` (CPS-A / CPS-B) : 100 % des écritures sont dans le code d'Hyper (init vidéo fichier `0x3DA18-0x3DC4C`,
  prise de l'image `0x3F224-0x3F594`, `0xA6C9C-0xA6CAC`), sauf UNE : talon `plans_s6`, `MOVE.W $32(A5),$804166`
  (68K `$0BDE2C`, e46). Contrôle MIPS : même compte (`be2146` : H 3, T 1 ; rien côté copie).
- Les copies d'Upper n'écrivent que les COPIES EN RAM : `$32(A5)` (13 écritures, 6 modifications), `$3A(A5)` (14),
  `$2A/$2C(A5)` (18 / 16+3), bases de pages `$C130-$C13C(A5)` (8 / 5 / 4 / 3), palette `$C140/$C154(A5)`, demande `$A8(A5)` (2).
  Hyper les prend à chaque image. Rien d'Upper ne court-circuite donc la prise d'Hyper.
- `$34(A5)` (→ `$804170`) : Hyper seul (init `$3F`), jamais écrit par une copie ni un talon : rien de périmé possible.

### A2. Bases du fork `$804200/02/04` : écrites par les seuls talons, jamais remises hors de leurs chemins — À ESSAYER
- 23 écritures par registre, toutes dans 7 talons : `plans_auto` (scène 4 Arcade, chaque image), `plans_s6/s8/sA`,
  `plans_vict`, `plans_vs` (scène 4 hors Arcade, seulement si `$FE11`), `scene2_bases` (seulement si `$FE00`).
  **Ni le code d'Hyper ni une copie d'Upper ne les écrit ; aucune écriture au démarrage.** La valeur de repos dépend du cœur.
- Chemins où elles restent PÉRIMÉES (lecture du code ; aucun n'est prouvé au banc) :
  a. **VERSUS sur décor d'Upper → retour à la sélection** : `plans_vs` pose `$4400/$440/$4A0` tant que `A5+8 >= 6`
     (68K `$0BE08A`) ; la fin de match d'Hyper (`0xA0308` : `$C201 = 1` → `0x2E9B0`, scène `$E`) quitte la scène 4 sans
     repasser par `A5+8 < 4` ; la scène 2 passe par `scene2_bases`, qui ne fait RIEN hors Arcade (`TST.B $FE00 ; BEQ`,
     `$0BE738`). Statiquement, la sélection d'Hyper qui suit un VERSUS joué sur un décor d'Upper (J2 en ZERO 3) est
     dessinée avec les mémoires de plans d'Upper, jusqu'à la scène 4 suivante (où `plans_vs` remet `$300/$340/$3A0`).
     Jamais signalé en jeu : **à vérifier en premier** (soit le défaut existe, soit le menu de fin de VERSUS / la
     sélection n'utilise aucun plan avant la remise, soit le cœur remet les bases : dans les trois cas le noter).
     Essai (cœur ou MAME, ≈ 3 min) : VERSUS, J2 Ryu ZERO 3, finir le match, « CHARACTER SELECT » ; captures du menu de
     fin et des 30 premières images de la sélection ; relever `$804200`.
     Correctif s'il est confirmé : `scene2_bases` sans le test du drapeau (bases d'Hyper à toute entrée en scène 2), ou
     `plans_vs` : bases d'Hyper dès que `A5+8 >= 8`.
  b. **Réinitialisation (ou mode test) pendant un écran d'Upper** : la RAM est effacée par Hyper (`0x3DF38`,
     `$FF0000-$FFFFFF`), donc `$FE00 = 0`, mais rien ne réécrit `$804200` : titre et menus d'Hyper avec les bases
     `$400/$440/$4A0` si le cœur ne les remet pas lui-même. INDÉCIDABLE ici (dépend du cœur FBNeo). Essai (≈ 2 min) :
     réinitialiser pendant la carte du mode Arcade.
  c. Arcade → titre par la scène `$C` (GAME OVER, fin) : bases d'Hyper posées par le talon. Sain (voir E1).

### A3. Bases de pages `$C130-$C13C(A5)` : remises par Hyper sur demande `$A8(A5)` — SAIN (prouvé par lecture)
- `$190` = page `$900000` (Hyper), `$191` = `$910000` (écrans d'Upper : talon `remap_ids`, copies `u2B6B4`, `u51B4C`).
- Hyper `0x3F5E0` (appelée à chaque prise d'image, `$00B4D4`) : si `$A8(A5)` ≠ 0, remet les quatre bases à `$90xxxx`.
  `$A8` est posé par Hyper à l'entrée en combat (`0xA0ACC`), par le nettoyage `0x38FF0C` (appelé par `0x38F2E0`, donc
  par tout retour au titre `0xA0E00` et par les sorties des copies `u24B588`, `u254CA4`), par `0x24BAC`, `0x94FB0`,
  `0xA6780`, `0x3BCDD4` ; et par deux copies (`u260000`, `u2704A4`). Aucun chemin Arcade → menus ne garde `$91xxxx`.

### A4. Couches `$32(A5)` / `$3A(A5)` : toujours réécrites en entier par l'écran suivant — SAIN
- Hyper : titre `0x618F4` / `0x61ED4` (`$1B0E`), sélection `0x316688` (`$1B00`) puis `0x3168CC`, `0x316CFC` (`$1B0E`),
  `0x24BBC` (`$270E`, écran non identifié) ; copies : présentation `u25B09C`, `u259020`, `u25CDD4`, `u252D0C` (`$1B0E`),
  GAME OVER `u24AFD4` (`$270E`). Les deux masques de la greffe (`ANDI.W #$FFF1,$32(A5)` : `plans_auto` `$0BDDB0`,
  `plans_s6` `$0BDE26`) sont donc levés par l'écran qui suit (voir E2).

### A5. Octets de la greffe `$FE00-$FE23(A5)` (`$FF7E00-$FF7E23`) — table complète dans `sorties/registres.txt`
| octet | posé par | remis par | lu par | périmé ? |
|---|---|---|---|---|
| `$FE00` Arcade | `depart_arcade` (`$0BDB40`) | `plans_s6/s8/sA` à la sortie vers `$C` (`$0BDE06`, `$0BDE84`, + sA) ; effacement de RAM au démarrage | 13 talons | voir E3 |
| `$FE04` phase de fin | `plans_sA` | `plans_sA` (1re image de la fin) | `plans_sA` | non |
| `$FE08` `$12A` sauvé | `moteur_plans`, `moteur_plans_vs` | — (temporaire) | les mêmes | non (E4) |
| `$FE10` décor d'Upper | `vs_decor` (Arcade), `d4_vs` (seulement si `$C201 = 1`) | les mêmes | 19 lectures (moteur_*, plans_*) | OUI en TRAINING / démo après une Arcade ou un VERSUS D4 : reste à 1. Sans effet aujourd'hui : tous les lecteurs hors Arcade exigent aussi `$FE11`, et `plans_vict` / `plans_s6/s8` ne sont atteints qu'en Arcade. Fragile : tout nouveau lecteur de `$FE10` seul sera faux. |
| `$FE11` VERSUS D4 | `d4_vs` (chaque init de match hors Arcade : 1 ou 0) | `d4_vs` | 7 lectures | reste à 1 pendant une Arcade qui suit un VERSUS : sans effet (les talons testent `$FE00` d'abord). |
| `$FE20` coupe du tirage | personne (lu par `tirage_1/2`) | — | 2 | interrupteur de banc, toujours 0 en jeu |
| `$FE21-$FE23` tirage | `tirage_1/2` | `tirage_1/2` | `tirage_1/2` | non |
| `$FE02`, `$FF02` | absents de l'image (`INTERMEDE_PLANS=0`, `DECOR_FIN_UNE=1`) | | | la 1re passe (E3) citait `$FF7E02` : il n'existe pas dans ro9a36 / ro9a37 |
- Correctif de principe pour `$FE10` : `d4_vs` le remet à 0 dans sa branche « pas VERSUS » (à côté de `MOVE.B #0,$FE11`,
  68K `$0BE066`, `stub` `d4_vs` de `greffe3.py`) ; coût : 4 mots MIPS.

### A6. `$12A(A5)` : la copie d'Upper le LIT seulement (`u1573E8`) ; Hyper l'écrit à 8 sites — voir E4.

## Transitions — verdicts

### E1. Sortie vers `$C` depuis les scènes 6 / 8 / A — INFIRMÉE pour 6 et 8, INDÉCIDABLE pour A
- Scène 6 : aucune copie de la scène 6 n'écrit `$C` dans `A5+4` (seulement 0 : `u24A94C`, et 8 : `u24AE54`). La branche
  « vers `$C` » de `plans_s6` est morte.
- Scène 8 (GAME OVER, `u24B588`, 68K `$0B81B2`) : après `MOVE.W #$C,$4(A5)`, la copie appelle dans la même routine
  `0x38F2E0` puis **`0x948C0` d'Hyper, qui est un fondu au noir BLOQUANT** (crée la tâche `0x90630`, boucle
  `JSR $024938` tant que `$180(A5)` ≠ 0, puis palette `$C140 = $92A000`). Le talon ne reprend la main (bases d'Hyper,
  `$FE00 = 0`) qu'une fois l'écran noir. Pas de défaut.
- Scène A (fin, `u254CA4`, 68K `$0B8D0C` : `ADDQ.W #2,$4(A5)`) : PAS de fondu dans cette routine (appels `0xEBDEB0`,
  `0x97130`, `0x38F2E0`, retour) ; le talon pose les bases d'Hyper à cette image, et le fondu `0x948C0` n'est joué qu'à
  l'image suivante par la scène `$C` d'Hyper (`0xA0E00`), donc AVEC les bases d'Hyper sur la VRAM d'Upper. Visible
  seulement si le dernier écran de la fin n'est pas déjà noir (état précédent : attente `$20` images) : non décidable
  en statique. Essai (MAME, ≈ 4 min avec une graine du banc des fins) : captures des 40 images autour du passage
  `$FF8004` : `$A` → `$C`. Correctif s'il est visible : dans `stub_plans_scene`, à la sortie vers `$C`, garder les bases
  et masquer scroll1-3 (même forme que `masque_sortie` d'e46) au lieu de poser les bases d'Hyper tout de suite.

### E2. Masque `ANDI.W #$FFF1,$32(A5)` — INFIRMÉE pour l'init de la scène 4 ; un cas voisin reste (E2b)
- `plans_auto` masque à `A5+8 = 0` (68K `$0BDDB0`), puis la copie `u2615D0` (init) tourne dans la même image : elle ne
  fait que `ADDQ.W #2,$8(A5)` et n'écrit jamais `A5+4` (aucune écriture de `$4(A5)` dans les copies `0xECA860-0xECCBE0`).
  **Aucun chemin ne sort de la scène 4 à l'image de l'init.** À l'image logique suivante, l'entrée de la présentation
  (`u25B09C`, 68K `$0B9C90`) réécrit `$32 = $1B0E`. Le masque de `plans_s6` (sortie vers 0) est levé par la sélection
  d'Hyper (`0x316688`).
- **E2b (nouveau, probable)** : la copie `u135430` (routine `0x1353A0`, 68K `$0A19DA` : `MOVE.W #2,(A5)` puis
  `A5+4 = 0`) renvoie à la sélection SANS masque. Si elle est atteinte pendant un écran d'Upper (arrivée d'un
  challenger sur la carte, le face-à-face ou le VS), `scene2_bases` pose les bases d'Hyper deux images plus tard alors
  que la VRAM garde l'écran d'Upper : même défaut que le CONTINUE avant e46 (1 à 2 images en tuiles fausses).
  Essai (≈ 3 min) : Start J2 pendant la carte, captures image par image. Correctif : dans `scene2_bases`, à la 1re image
  (`A5+8 = 0`), masquer scroll1-3 comme `masque_sortie` ; ou poser le masque dans un talon autour de `0x1353A0`.

### E3. Drapeau `$FF7E00` — CONFIRMÉE dans son principe, INFIRMÉE pour les sorties ordinaires
- Posé : 1 site (`depart_arcade`). Remis : 3 sites (`plans_s6` branche morte, `plans_s8`, `plans_sA`, quand
  `A5+4 = $C` au retour de la scène). Lu : 13 talons.
- GAME OVER : remis (retour du fondu bloquant, puis `CMPI.W #$C,$4(A5)`). Fin du générique : remis par `plans_sA`.
  CONTINUE accepté, nouveau challenger : la partie Arcade continue, le drapeau doit rester. Réinitialisation / mode
  test : effacé avec la RAM (`0x3DF38`).
- NON remis : tout retour au titre qui ne passe pas par les scènes 6 / 8 / A, c'est-à-dire les retours du code d'Hyper
  qui écrivent `(A5)` et `A5+4` directement : menu du portage `0x29C08` (reprise en scène 4, `A5+8 = $A`) et `0x29C60`
  (retour au titre), `0x28608`, et les `JMP 0xA0E00` de `0x62D5C` / `0x634BC`. Les deux derniers sont le menu du titre
  (hors partie). `0x29xxx` est le menu de pause du portage PS2 (résultats natifs « supposés nuls » dans la carte) :
  s'il est atteignable dans le fork pendant un combat d'Arcade, le drapeau, `$FE10` et les bases restent posés, et le
  VERSUS suivant part dans la scène 4 d'Upper (`scene4_mode`). INDÉCIDABLE en statique (dépend des crochets natifs).
  Essai (≈ 3 min) : en combat d'Arcade, chercher un menu de pause ; s'il existe, quitter par lui puis lancer un VERSUS.
- Garde bon marché, quel que soit le résultat : remettre `$FE00` (et `$FE10`) à 0 dans le lanceur des modes non Arcade
  ou à l'init du titre d'Hyper (`0x61ED4`, là où `$32 = $1B0E`), au lieu de ne compter que sur la scène `$C`.
- Remarque : la scène `$C` d'Upper (`0x270920`, table `0x61C1E0`) est copiée (`0xED2100`) mais jamais appelée (la table
  des scènes est celle d'Hyper, `0x5B5E80`) ; elle créerait la tâche de titre d'Upper `0x4C3F0`. Code mort, à savoir.

### E4. `EFFET_12A` et setjmp / longjmp — INFIRMÉE (appels directs)
- Les 6 sites sont TOUS dans le code d'Hyper, moteur des joueurs : setjmp `0x78384`, `0x78D80`, `0x85970` ; longjmp
  `0x8592C`, `0x85C38`, `0x8A300`. Aucun dans une copie d'Upper ni dans un talon.
- `outils/atteint.py` : depuis les deux routines appelées entre le masque et la remise (`0xE3D560` copie de `0x151B80`,
  `0xE193C0` copie de `0xFD620`), aucun site longjmp n'est atteint par appel direct ; depuis les trois fonctions à
  setjmp, aucun appelant des talons (`0x9A6F0`, `0x9FDB0`, `0x9A570`, `0x9A430`) n'est atteint : un cadre setjmp ne peut
  pas être l'ancêtre du talon. La remise de `$12A` ne peut donc pas être sautée par un longjmp.
- Aucun site d'Hyper qui écrit `$12A` (`0x50048`, `0x50094`, `0xA3C84`, `0xA3E74`, `0xA42A8`, `0x2A4CDC-0x2A4E10`) n'est
  atteint depuis ces deux routines par appel direct : la remise n'écrase pas une écriture d'Hyper.
- Réserve : `moteur_plans_vs` (une seule routine, 66 fonctions atteintes, 78 `jalr`) est propre ; `moteur_plans` appelle
  aussi le parcours des objets de décor `0xFD620`, dont les classes passent par des tables (`jalr` non suivis, 1 854) :
  une classe qui cède la main (`JSR $024938`) laisserait `$12A` sans son bit 7 pendant une image. Non tranché ; sonde
  d'écriture de `$FF812A` au banc si le fond du K.O. par super redevient faux.

## Ce que v161 change pour ces constats
- Rien sur le fond : module MIPS, données et talons identiques (les 29 talons se traduisent pareil). Les adresses 68K
  citées par la 1re passe (ro9a36) ne valent plus : prendre celles de ce fichier (carte de ro9a37).
- Rendu : le `ANDI.B #$7F` de `_masque_12a` apparaît en `BCLR #7,$12A(A5)` dans la carte (même effet).
- Correction de la 1re passe : E3 citait `$FF7E02` et « les talons des scènes 6 / 8 / A » ; `$FE02` n'est pas dans
  l'image, et la scène 6 ne sort jamais vers `$C`. E2 : « aucune routine de la greffe ne remet `$32` » est vrai des
  talons, mais les copies d'Upper le réécrivent à chaque entrée d'écran.

## Essais au banc proposés (aucun lancé)
| n° | essai | durée | tranche |
|---|---|---|---|
| 1 | VERSUS J2 ZERO 3, fin de match, retour à la sélection, captures + `$804200` | ≈ 3 min | A2a |
| 2 | réinitialisation pendant la carte de l'Arcade, capture du titre | ≈ 2 min | A2b |
| 3 | Start J2 pendant la carte, captures image par image | ≈ 3 min | E2b |
| 4 | fin la plus courte du banc, 40 captures autour de `$FF8004` `$A` → `$C` | ≈ 4 min | E1 (scène A) |
| 5 | menu de pause en combat d'Arcade, sortie, puis VERSUS | ≈ 3 min | E3 |
