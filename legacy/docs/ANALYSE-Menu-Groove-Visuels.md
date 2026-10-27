# HSFA — Logique des modifications : label menu / groove / visuels (autonome 2026-06-24, §1 RÉVISÉ 2026-07-18)

## 1. LABEL "ARCADE" AU MENU — ✅ RÉSOLU ET LIVRÉ (v30, 2026-07-18, validé in-game)

### Le mécanisme FINAL (trouvé par diff RAM titre/menu + patch live PINE)
Le mode-select de Hyper affiche **un seul label à la fois**, en petite police verte sous le
logo, comme **une chaîne de sprites 8×8** (un sprite par lettre) émise dans la liste
`0xb90000/0xb92000` (double buffer, entrées 8 o `{i16 x, i16 y, u16 tuile, u16 attr}` ;
police : tuile = `0x12c1 + (char - 'A')`). Redessiné à chaque **changement de curseur**.
- **Table des labels = `0x69cf54`** (data zero9) : 7 pointeurs indexés PAR CURSEUR :
  `[0]=0x69cf70 ARCADE, [1]=VERSUS, [2]=SURVIVAL, [3]=DRAMATIC BATTLE, [4]=TRAINING,
  [5]=OPTION, [6]=EXIT` — **la liste SFA3 complète a survécu dans Hyper**, ARCADE compris !
- Format d'une entrée : `{u16 0x0a, u16 nb_lettres, u16 ?, u16 palette(0x1f), u32 ptr_table_X
  (coords centrage par lettre, ex. ARCADE→0x69d070), lettres u16 = 0x0200|(char|0x80)}`.
- **Pourquoi le slot 7 était vide** : curseur 7 → `table[7]` = **hors table** (tombe sur le
  header de l'entrée ARCADE lu comme pointeur → invalide → rien dessiné). Et l'entrée ARCADE
  [0] n'était jamais affichée car le curseur 0 n'existe pas. Aucun art manquant : la police
  couvre tout l'alphabet (TRAINING etc. l'utilisent).

### Le fix (v30, dans les DEUX pnach) — AUCUN art à importer, pur data+cave
1. Copie de l'entrée ARCADE d'origine (24 o de `0x69cf70`) → cave **`0x1c0360`** (6 words).
2. `table[7]` (word `0x69cf70`) → `0x001c0360`, écrit PAR CAVE uniquement (jamais en patch
   statique : 0x69cf70 = data zero9, potentiellement code côté shell) :
   - à l'**init menu** : pointeur phase-0 **`0x5b4230`** → cave `0x1c0380` (write + `j 0x252a10`) ;
   - **chaque frame menu** : `modesel_clear` (`0x5b4238`→`0x1c0240`) étendu avec le même write.
3. (Écraser le header de l'entrée [0] par le pointeur est sans effet : jamais lue par curseur 0.)

### Fausses pistes documentées (pour mémoire)
- « table 0x5b4240 = un ID de sprite par curseur » (analyse 24/06) : FAUX — `0x5b4240` est une
  table de police du renderer texte générique `FUN_2544d0` (chaînes ASCII/Shift-JIS `0x82xx`,
  commandes `0x80 x y attr`, petits menus = items 12 o `{id,x,y,ptr}` ex. COLOR EDIT @`0x5b09d0`).
- Les blocs tilemap pré-bakés (table `0x640960`, 0x300/id, `FUN_2537e0`→`FUN_505ab0`, ids
  0xd-0x10 → SCR2 `0xba4000+`) existent mais ne sont PAS le label visible du mode-select
  (probablement d'anciens écrans). Leur art n'est résident ni en combat ni au titre.
- Équivalents z5 par signature (si un jour utile) : renderer blocs `0x3415c0`, table `0x6cf5f0`,
  wrapper liste `0x341450` (ids à `A5-0x4db0`, A5 z5 = `0xa08000`).

## 2. GROOVE entre combats (garder le choix joueur)
- Groove stocké à **`0xb88413`** (P1) / `0xb88813` (P2) = `struct+0x13`.
- **Reset à l'init combat** : sites zone `0x10xxxx` (ex. `0x108c20` `beql a2,0x400` → sinon
  `sb zero,0x413(s1)`) → le groove peut être remis à 0/défaut au setup du combat.
- Char-select **sous-flux 1** (`0x5069b0`, table `0x5c5600`) ré-init aussi le groove à chaque passage.
- **PARADE (déjà en place v17-v19, robuste)** : latcher le groove du joueur à la **sortie char-select**
  (`0x5c55dc`) puis le **restaurer au hook init-combat `0x5b5e88`** (1×/combat, APRÈS les resets,
  juste avant le spawn). Le même hook qui fixe le perso fixe le groove. ⇒ rien de neuf à coder ;
  à VALIDER au prochain test (v21 + rebrancher le latch/restore).
- Note : la route skip (victoire) saute le char-select → sous-flux 1 non rejoué → groove persiste
  déjà ; le restore CINIT est la ceinture+bretelles contre le reset `0x10xxxx`.

## 3. VISUEL "SÉLECTION DE JEU" (shell Anthology)
- L'écran de **sélection de jeu** appartient au **shell Anthology** = programme séparé, **ABSENT du
  dump HSFA** (cf. ANALYSE-Scene-Result-Boot §0). ⇒ **non décompilable ni patchable depuis ce dump**,
  et soumis à la contrainte shell-safe (même CRC → un patch code fige le shell).
- Pour le changer il faudrait : (a) un **dump RAM du shell** (savestate sur l'écran de sélection),
  puis RE de son rendu ; (b) ou des assets remplacés dans l'ISO (hors pnach). Risqué/lourd.
- **Alternative recommandée** (ce que Rickow évoquait) : plutôt que changer le visuel, **atteindre
  HSFA directement** (boot-skip) — lui aussi gated par le shell (cf. boot-skip), à tracer en live.
- ⇒ **À faire au retour** : savestate sur l'écran de sélection de jeu du shell → on pourra enfin
  regarder son code/rendu (aujourd'hui on n'a que HSFA en RAM).

## 4. Ce qui touche nos modifications (récap des hooks)
- **Menu** : nav `0x5b41f0/f4`+`0x5b4200/04` (curseurs), lanceurs `0x5b4210[c]`, labels `0x5b4240`,
  render `0x252b30`, label-drawer `0x2544d0`. Slot 7 (`0x5b422c` lanceur / `0x5b424e` label) = ARCADE.
  **NAV (re-vérifiée 2026-06-24)** : `0x5b41f0`=BAS, `0x5b4200`=HAUT, valeur=curseur cible, index=
  curseur courant. Original bas: 1→4→5→6→1 (VERSUS,TRAINING,OPTION,EXIT). Mon hack actuel
  (`0x5b41f0=05050701`,`0x5b41f4=04010605`,`0x5b4204=01050407`, `0x5b4200` inchangé) donne
  bas **1→7→4→5→6→1** = ARCADE(7) inséré après VERSUS, **curseurs distincts** ⇒ nav en fait
  CORRECTE. L'anomalie "VERSUS=7" vue dans les savestates = probablement un slot mal étiqueté
  (TRAINING/OPTION/EXIT=4/5/6 étaient corrects). À reconfirmer visuellement, mais pas de bug nav avéré.
- **Char-select** : racine `0x506070`, sous-flux `0x5c55d0` (init `0x506480`@+0, groove `0x5069b0`@+4,
  sortie `0x508b80`@+0xc, handicap `0x5105d0`@+0x14). Mode `0xb880a8` (1=training/1-pad, 3=versus).
- **Combat** : handler `0x286620` (hook `0x5b5e88` = épinglage perso+groove 1×/combat), RESULT
  `0x2865f0`→`0x21d550` (hook `0x5b5e9c`). Perso `0xb88516`/curseur `0xb88502` (=perso+0x30).
- **Widescreen** : viewport `0x14ac28/b070/b0a0`, drawers tiles colonnes `0x1d19b0/…` (cf. doc WS §7).
- **Scène** : code `0x1144`/`0xb84214`, interpréteur `0x21f6b0`, table `0x5b2cf0` (transitions).
