# Mise en route d'Hyper SFA (`ro9`) dans le banc MAME

> Rapport versé dans le dépôt le 2026-10-24 depuis `work/agent_ro9/MISE-EN-ROUTE-ro9.md` (copie anonymisée ; texte
> d'origine inchangé). Les chemins `work/…` et `<workspace>/…` désignent des dossiers de travail, hors dépôt. Note du
> 2026-10-04 (premiers pas d'Hyper au banc, avant le fork) ; l'annexe donne les diffs de l'époque, contre les
> originaux d'alors. Suite : [BANQUES-ET-MODES-ro9](BANQUES-ET-MODES-ro9.md), [ETATS-HYPER](ETATS-HYPER.md).

Agent `agent_ro9`, 2026-10-04. Tout le travail est dans `<workspace>/work/agent_ro9/`. Rien n'a été modifié
dans `scripts/untranspile`, `work/mame`, `work/mame_ro5`, `github/`, `mame-fork/` ni `sfa3max-psp-widescreen`.
Les scripts Lua communs de `work/mame` ont seulement été chargés par `dofile`. Aucun commit.

## 0. En bref

- **Profil `ro9`** établi (§1), chaque valeur revérifiée dans le MIPS.
  - Les points d'entrée sont **identiques, MIPS masqué, à ceux d'Upper**. Le profil reprend donc la structure du
    profil `ro5`.
  - Hyper **n'a aucun chargeur natif de tables d'animation** : pas de `LOAD_BASE`, pas de talons, `$C0BC` jamais écrit.
  - Le seul fichier à adresse fixe est le **547** (frames de sprites) en **`$C84000`**.
- **Construction** : 0 non résolu.
  - Les données dépassent 4 Mo. Leur fin (`$8DA000-$B67200`, 2,68 Mo) part dans un bloc externe en **`$940000`**,
    et non en `$C80000`, qui est occupé par le fichier 547.
- **Première faute** : image 736, juste après le choix du perso dans VERSUS. Saut dans une table d'aiguillage
  (instruction illégale) dans l'émetteur de frames (mips `0x393D8C`).
  - **Cause** : la boucle de création des 4 objets « version » (mips `0x33C3FC-0x33C5A4`). Deux défauts du traducteur :
    1. la restauration du registre prêté à A8 est **rejouée à chaque tour de boucle** (pile déséquilibrée, domicile
       de A8 écrasé) ;
    2. la lecture d'octet décroissante `-(A8)` a une **parité fausse**.
  - **Les deux sont corrigés** dans la copie.
- **État atteint** : écran-titre, menu des modes, sélection perso × version, puis **combats TRAINING**.
  - **Aucune exception** sur 20 000 images au repos, 30 000 en TRAINING avec entrées, et 4 × 20 000 avec les
    4 versions (ZERO `$30`, ZERO 2 `$41`, ZERO 2 ALPHA `$63`, ZERO 3 `$06`).
  - Les graphismes sont illisibles : c'est la ROM graphique de SFA3, les banques d'Hyper n'existent pas encore.
  - **Pas de démonstration d'attraction** : l'écran-titre attend Start indéfiniment (§4.3). À confirmer sur PS2.
- **Prochain blocage** : les graphismes (banques SFA1 / SFA2 / Upper et plans d'Hyper, `banques.py` pour `ro9`),
  puis VERSUS à 2 joueurs (§5).

## 1. Profil `ro9` (dans `untranspile/profils.py` de la copie)

```python
'ro9': dict(
    fichier='ro9_usa_prog68k.bin',
    va_reset=0x3da00, va_frame=0x3ee30, va_init=0x3ec20,
    irq2=0x3f1b0,
    sauve_regs=(0x3fe50, 0x40080),
    hooks='hooks_fork_ro9.json',
    manette={0x38a958: (1, 0x58, 0x51a), 0x38a97c: (2, 0x5c, 0x91a)},
    aides={0x212dc0: 'movem_push', 0x213120: 'movem_pop', 0x213480: 'andi_ccr', 0x213610: 'abcd'},
    be48=0xc0bc,
    musique=None, objets_intro=None, palettes=None, mains=False,
    data_ext=0x940000,                       # nouvelle clé (§3, correctif 2)
    travail='<workspace>/work/agent_ro9/mame_ro9', sortie='roms_ro9',
),
```

Preuves. Outil `outils/compare.py` : comparaison instruction par instruction jusqu'au `jr ra`, avec les cibles de
`jal` et les `lui/addiu/ori` masqués.

| clé | valeur ro9 (fichier) | preuve |
|---|---|---|
| `va_reset` | `0x3DA00` | **identique** à ro5 `0xCED70` (330 instr.) ; 0,967 contre ro3 `0x926B0` |
| `va_init` | `0x3EC20` | **identique** à ro5 `0x322A0` (132 instr.) |
| `va_frame` | `0x3EE30` | 224 instr. contre 224 ; seuls diffèrent 5 déplacements des variables du portage (ro5 `0x9A0428` → ro9 `0xB67508` = fin des données + `0x308`) |
| `irq2` | `0x3F1B0` (fonction ; contient `0x3F224`) | 239 contre 239 instr. avec ro5 `0x32830` ; un seul déplacement de variable du portage diffère |
| `sauve_regs` | `0x3FE50`, `0x40080` | **identiques** à ro5 `0x334D0` / `0x33700` (137 instr. chacune) |
| `hooks` | `hooks_fork_ro9.json` | régénéré par `MODULE=ro9 hooks_fork.py` dans la copie : **identique octet pour octet** à l'existant (42 cibles, 66 sites ; 15 natifs du module). C'est ainsi qu'est produit `hooks_fork_ro5.json` : début `0x22DE0` pour ro9, au lieu de `0x22B00` |
| `manette` | `0x38A958` (J1), `0x38A97C` (J2) | `jalr` vers `0x213D20` (fichier `0x23D20`), avec `A8 = A5+$400` / `A5+$800` et D-slot `$1124 = lb $63(A5)` ; forme identique à ro5 `0xC5738` / `0xC575C`. Natif `0x23D20` **identique** à ro5 `0x23BB0` et à ro3 `0x381410` (22 instr.) ⇒ mêmes `$58/$5C → $51A/$91A` |
| `aides` | exéc. `0x212DC0` push, `0x213120` pop, `0x213480` andi_ccr, `0x213610` abcd | **identiques** à ro5 `0x212B00` / `0x212E60` / `0x2131C0` / `0x2134A0` (215 / 215 / 31 / 89 instr.). Appels depuis `0x22DE0` : push 5, pop 5, andi 3, abcd 16 |
| `be48` | `$C0BC` | homologue (règle +`0x274` de ro3, comme ro5). Dans ro9 il n'a que **4 lectures** (`0x3728A4`, `…8BC`, `…8D4`, `…8EC`, copies vers `$70-$7C(A6)`) et **aucune écriture** : aucun natif de ro9 n'appelle `0x154C90` (cf. `assets_natifs`). Valeur gardée pour les talons et les scripts Lua (`BANC_PTR_ANIM=FF40BC`), sans effet aujourd'hui |
| `musique` | `None` | pas de table de ticks d'intro dans ro9 (CARTE-ro9 §4.3 : table absente, variable `$C38E` absente) |
| `objets_intro` | `None` | table `0x585750` / `0x60CA50` absente ; 0 accès `lb 0x1129` (CARTE-ro9 §5). `mame_test.py` est rendu tolérant à `None` (§3) |
| `palettes` | `None` | homologue non établi |
| `mains` | `False` | REMPL, BCD, R1, R2 identiques à ro5/ro3 à d'autres adresses (CARTE-ro9 §4.2) ; DEF modifiée. Non activé pour cette mise en route |
| `travail` / `sortie` | `agent_ro9/mame_ro9` / `roms_ro9` | |

### 1.1 Valeurs ro9 de `assets_natifs.py` (bloc `if MODULE == "ro9"`)

| nom | ro9 | preuve |
|---|---|---|
| `NATIF_SITE`, `NATIF_PERSO` | `None` | ro9 n'a qu'**un** chargeur natif, `0x22B00` (sites `0x970BC`, `0x31AF78`, `0x31AFA4`). C'est l'homologue du chargeur **4 joueurs** de ro3 `0x3838D0` : `0x154D20` dans `0x1BC8000 + j×0x60000` (table `0x5AF2B0`), puis `0x155080` (banque graphique, table `0x5AF1B0`). Il **n'appelle pas `0x154C90`** et n'écrit pas `$C0BC`. Les homologues de ro3 `0x383700` (site) / `0x3837D0` (perso) et de ro5 `0x4112D0` / `0x4113A0` / `0x4114A0` n'existent pas (`outils/resume_nat.py ro9`) |
| `T_SITE`, `T_PERSO`, `N_PERSO`, `N_SITE` | `None`, `None`, `0`, `0` | idem : aucune table « (gfx, anim) » à décompresser |
| `SITES`, `SITES_DYN` | `{}`, `{}` | idem |
| `LOAD_BASE`, `LOAD_SITE` | `None` | la règle « RAM + `0x175000` / `0x183000` » donnerait `$CF5000` / `$D03000`, qui tombent **dans** le fichier 547 : aucun chargement d'animation à adresse fixe dans ro9 |
| `VBASE` | `0xD20000` | inutilisé (bloc vide) ; choisi hors RAM ro9 (`$B80000-$BFFFFF`) et hors fichier 547 |
| `FIXES` | `{547: 0xC84000}` | histogramme des longs alignés des données : densité continue de `$C84000` à `~$D0B000`. Le fichier X_DATA **547** (MWo3 299 056 o → **553 352 o** = `0x87188`) finit exactement en `$D0B188`. Même en-tête que 289 (ro3) et 390 (ro5), `d1ff f2ff e1ff a2ff…` (frames de sprites). **39 656** longs alignés pointent dedans (16 537 distincts) ; seulement 155 dans les 64 Ko voisins. Base = RAM + `0x104000`, comme ro3 (`$A04000`) et ro5 (`$B04000`) |

Le chargeur 4 joueurs met en place des **banques graphiques** (tables `0x5AF2B0` : fichiers 314–344 ; `0x5AF1B0` :
banques 355–386 / 208–220 / 229–248). Ce n'est pas du ressort de `assets_natifs` : cela relève du chantier
graphique (`banques.py`).

## 2. Construction

```
cd <workspace>/work/agent_ro9/untranspile
MODULE=ro9 XDATA=<workspace>/work/xdata/X_DATA.BIN ANIM_CACHE=<workspace>/work/agent_ro9/anims \
  nice -n 19 python3 mame_test.py          # ~40 s ; journal : ../build_ro9.log
```

Disposition obtenue :
- code de `$1000` à `$93000` ;
- données du module de `$93000` à `$3BDF00` (PS2 `$5AF140-$8DA000`) ;
- **fin des données** (PS2 `$8DA000-$B67200`, 2 675 200 o) → `ext_940000.bin` en **`$940000`** ;
- hachage des adresses de code en `$3C0000`, table en `$3E0000` (11 008 clés) ;
- fichier 547 → `ext_c84000.bin` (identité, `$C84000`) ;
- setjmp/longjmp : 6 sites, 3 tampons ; manette : 2 sites ; tremplins d'aiguillage : 42 ;
- **0 non résolu** ; 126 écritures de registre « tombées » (`chutes.json`, contre 56 pour ro3, à auditer).

Lancement :
- `MODULE=ro9 MAXF=… [INPUTS=…] python3 diag.py N --nobuild` ;
- ou MAME direct avec `-rompath mame_ro9/roms_ro9`, `BANC_DIR=…/mame_ro9/` et un script qui charge `banc_mem.lua`
  **puis `lua/banc_mem_liste.lua`** (§3, correctif 3).

## 3. Correctifs apportés à la copie

Les diffs complets sont en annexe et dans `correctifs/*.diff` (`diff -u` contre les originaux).

**Attention** : les originaux ont changé pendant la session (§118 dans `translate.py` à 14:30 ; §118/§119 dans
`mame_test.py` et `profils.py` à 14:38 ; `banques.py`, `hsfa_gfx.py` ; nouveaux `gen_son.py`, `hsfa_plans.py`).
- J'ai **reporté ces évolutions dans la copie**.
- Les diffs sont faits contre l'état des originaux à 14:38 (copie figée dans `orig_1438/`). Ils ne contiennent donc
  que mes correctifs.

| # | fichier | correctif | pourquoi |
|---|---|---|---|
| 1 | `profils.py` | entrée `ro9` (§1) ; `TRAVAIL=` surcharge le dossier de travail | profil ; essais (`garde_ro3`, `mame_ro9_avant`) sans toucher les dossiers partagés |
| 2 | `profils.py` + `mame_test.py` | clé `data_ext` → `T.DATA_EXT = 0x940000`. Dans la conversion à l'exécution, la plage de fin des données reçoit la marque `$01000000` | **débordement de taille** : 0,57 Mo de code + 5,72 Mo de données. Le bloc externe d'Upper (`$C80000`) chevaucherait le fichier 547 (`$C84000-$D0B188`), et après `$D10000` il n'y a pas 2,6 Mo libres avant `PORT_RAM` (`$F00000`). `$940000-$BCD000` est libre sur le bus CPS2, mais c'est une plage d'adresses PS2 (`$5AF140-$C00000`) : sans la marque, un pointeur déjà converti serait reconverti (`CMPA.L` 32 bits). Avec elle, la valeur concorde aussi avec `addr_to_68k`, qui marque déjà tout `$400000-$F00000` |
| 3 | `mame_test.py` + `lua/banc_mem_liste.lua` + `diag.py` | `mame_test` écrit `ext_liste.txt` (bases des blocs externes) ; `banc_mem_liste.lua` installe un tap par bloc absent de la liste figée de `banc_mem.lua` ; `diag.py` le charge après `banc_mem.lua` | `banc_mem.lua` ne connaît que `a04000…c80000` : `$940000` et `$C84000` n'étaient pas servis. `banc_mem.lua` n'est pas modifié |
| 4 | `mame_test.py` | `SYSC` des natifs d'animation seulement s'ils existent ; plage `VBASE` ajoutée seulement si le bloc n'est pas vide ; correctif `objets_intro` sauté si `None` | ro9 n'a ni chargeur d'animation ni table d'objets de l'intro (plantages `None + int` / `addr_to_68k(None)`) |
| 5 | `assets_natifs.py` | bloc `ro9` (§1.1) ; cache en écriture `ANIM_CACHE` (lecture : cache partagé d'abord) | valeurs ; ne pas écrire dans `work/cps2/anims` |
| 6 | `translate.py` | `sys.path` pointe vers le dossier du script | le chemin en dur vers `scripts/untranspile` faisait charger le `profils.py` **original** (KeyError `ro9`) |
| 7 | `extra_regs.py` (**traducteur**) | `BACK_AFTER` : un retour de boucle venu d'**après** une zone de registre prêté et qui vise `after` (l'instruction qui suit la zone) marque la zone « restauration atteinte de l'extérieur ». La zone A8, ou D8 dans ce cas précis, passe en **fermeture anticipée** (`EARLY_CLOSE`), et non sur `after` | **cause de la 1re faute** (§4.1). La restauration émise sur `after` était rejouée à chaque tour : `MOVEA.L (SP)+` en trop (pile déséquilibrée) et domicile de A8 écrasé. D8 est ajouté : refuser sa zone renvoyait au repli mémoire, qui perdait `LSL.W #2` et l'`ADDA` de `0x33C42C` |
| 8 | `translate.py` (**traducteur**) | passe `byte_streams_pre` : `SUBQ.W #1,An ; MOVE.B 1(An),<ea>` → adresse exacte à l'exécution (An XOR 1 par la pile, drapeaux du `MOVE.B` gardés). Interrupteur `BYTE_PRE=0` | flux d'octets **décroissant** (`A8 -= 1 ; lb 0(A8)`, mips `0x33C4F0`) : le déplacement `0 XOR 1 = +1` suppose An pair, alors que le premier octet est à adresse **impaire** → octet du perso suivant. 1 site dans ro9, **0 dans ro3 et ro5** |
| 9 | `mame_test.py` | deux lignes de compte rendu (correctifs 7 et 8) | suivi |

**Effet sur ro3** (garde-fou, `garde_ro3/`) :
- avec `BACK_AFTER=0`, la copie produit pour ro3 **exactement** la ROM actuelle de `work/mame/roms_tr` (`sz3ud.03c`
  md5 `9248db4e562fadc28e00bebba27dbfea`). Le profil ro9, les correctifs 2 à 6 et 8 sont donc neutres pour ro3 ;
- avec le correctif 7, la ROM ro3 change (md5 `239141f3…`) : 1 zone A8 de plus en fermeture anticipée (mips
  `0x1F1800`) et 1 zone D8 (`0x1F1ECC`). Il s'agit du **même défaut, latent dans SFA3** :
  - la zone `A8 = A5+$8E4C` (`0x1F1800`) se referme sur `0x1F1804` ;
  - `0x1F1860 BNE 0x1F1804` (tirage aléatoire recommencé tant que `BTST D0,D2`) rejoue `MOVEA.L (SP)+,A4` à chaque
    nouveau tirage ;
- ro3 avec le correctif : 20 000 images sans exception (`diag.py`). Les autres diagnostics de non-régression ro3
  (entrées, partie offensive 60 000, commandes 42/42) **n'ont pas été rejoués**, à faire avant un report dans les
  originaux. Upper est touché aux mêmes endroits (`0x24FE98`, `0x2505E8`).

## 4. État atteint

### 4.1 Première faute (avant les correctifs 7 et 8)

Construction sans les correctifs (`BACK_AFTER=0 BYTE_PRE=0`, dossier `mame_ro9_avant/`). Entrées : pièce 300,
Start 400, B1 520 (VERSUS), B1 700 (perso).
- `diag.py` : « EXCEPTION 5 à l'image 736 ».
- La trace s'arrête en fait sur `$A08` = **vecteur 4, instruction illégale** (`dc.w $064E`). `diag.py` affiche 5 car
  il lit en fin d'image `PC=$A0A` (prélecture).
- Image : `faute_736_exception.png` (écran de sélection, colonne des versions). Trace : `diag_premiere_faute.log`.

```
  08cd08  movea.l ($1c,A6), A0     mips 0393d04  MOVEA.L $001c(A6),A0 ; JSR CONV_A0   (A6 = objet $FFCD80)
  08cd1a  movea.l ($4,A0), A0      mips 0393d1c  MOVEA.L $0004(A0),A0 ; JSR CONV_A0
  08cd2c  move.w  (A0)+, D0        mips 0393d64  MOVE.W $fffe(A0),D0  [(A0)+]
  08cd2e  move.w  ($6,PC,D0.w), D0 mips 0393d8c  MOVE.W T_5caa60(PC,D0.W),D0
  08cd32  jmp     ($2,PC,D0.w)     mips 0393d8c  JMP T_5caa60(PC,D0.W)   [table de 21 entrees]
  08cd52  dc.w    $064e; ILLEGAL
  000a08  bra     $a08
```

Remontée de la faute (points d'arrêt et `wpset` du débogueur, outils `lua/bp.lua` et `outils/trace_fn.py`) :
1. Objet `$FFCD80` (type 7, l'un des 4 objets « version » de la sélection) :
   - `$1C(A6) = $0CB5F6`, frame **décalée de 2** (les autres objets ont `…F4`) ;
   - car son index d'animation `$B(A6) = $4D` déborde la table `0x5E76D8` (44 entrées).
2. `$B` est écrit par mips `0x33C50C`. La boucle (`D1 = 3..0`) lit `A8 -= 1 ; lb 0(A8)`, avec
   `A8 = 0x5C6960 + 4 × perso + 4`. La table contient les versions par perso (`1E 1F 29 21`…) ; `$4D` n'y figure pas.
3. 68K produit :
   - la zone A8 n° 1 (`0x33C408-0x33C46C`) se refermait **sur la tête de boucle** `0x33C470` ;
   - `0x33C5A4 BPL 0x33C470` rejouait donc à chaque tour « A3 → domicile A8 ; `MOVEA.L (SP)+,A3` » ;
   - au 2e tour, A8 = l'A3 restauré (pointeur sans rapport) et un long de trop dépilé ;
   - de plus, `SUBQ.W #1,A3 ; MOVE.B 1(A3),$B(A4)` lisait l'octet du perso suivant (parité).

Après correction (`outils/dasm68.py 7e3f0 7e4c0`) :
- les deux restaurations sont émises **avant** l'étiquette de la boucle (`BPL` vers `$7E44E`, le `JSR`) ;
- la lecture se fait à l'adresse exacte (`EORI.B #1,3(SP)` autour de `MOVE.B (A3),$B(A4)`).

### 4.2 Après correction : pas d'exception

| essai | entrées | résultat |
|---|---|---|
| repos (écran-titre) | aucune | `diag.py` MAXF=20000 : **aucune exception** |
| scénario de la 1re faute (VERSUS) | pièce, Start, B1 ×3 | MAXF=6000 : **aucune exception** ; sélection J1 complète (colonne des versions validée, `planche_selection.png`) |
| TRAINING | `seq_training.txt` (Start, **Bas** = TRAINING, B1 ×8, puis coups, sauts et marches périodiques) | `diag.py` MAXF=30000 : **aucune exception**. Combat à partir de l'image ~2090 (`A5+$0/4/8/C = 2/4/6/6`), `planche_combat_training.png` |
| 4 versions (TRAINING) | `essais/seq_v{0..3}.txt` | 4 × 20 000 images sans exception. J1 `$102` = `$30` (ZERO, `$D3=01`), `$41` (ZERO 2, `$22`), `$63` (ZERO 2 ALPHA, `$06`), `$06` (ZERO 3, `$10`) ; J2 `$31` (`$D3=01`) |
| ro3 avec le correctif 7 | aucune | 20 000 images sans exception |

Les champs `$102 / $116 / $117 / $D3` (CARTE-ro9 §2.2) prennent bien les valeurs attendues : versions décodées par
`0x321BA0`.

### 4.3 Déroulé observé et attraction

- Phases `A5+0` : `0→2→6→8→0` (amorçage), puis `0→2→4→6`.
  - **Phase 6 = écran-titre**, aiguillage `T_5B41C0[3] = 0x62390`.
  - Sous-état `A5+8` : `T_5B41E8 = {0x62430, 0x624F0}`. L'état 2 (`0x624F0`) ne fait que défiler le fond
    (`$28 -= $100` toutes les 6 images).
- `$E(A5) = 300` est posé (`0x62458`) mais n'est lu par **aucune** routine de cette phase (les décomptes de `$E` sont
  dans d'autres phases : `0x2E46C`, `0x321290`, `0x321AA4`…). Le titre attend donc Start sans limite.
- Start → menu des modes (phase 4). Le menu revient au titre seul après ~850 images (`planche_titre_menu.png`).
- **Il n'y a donc pas d'attraction avec démonstrations** comme dans SFA3 ou Upper. **À confirmer sur PS2** : je n'ai
  pas de référence d'Hyper au repos.
- Menu : `$C201(A5)` = curseur ; **Bas** = VERSUS (1) → TRAINING (4), **Haut** → EXIT (6). Les entrées viennent de
  `$C210/$C212/$C216/$C218` (bloc Anthology décalé de +`$200`).

## 5. Prochains blocages / points ouverts

1. **Graphismes** (bloquant pour juger quoi que ce soit à l'écran) :
   - `banques.py` / `banc_sprites.lua` / `banc_plans.lua` pour `MODULE=ro9`. Ils doivent couvrir :
     - la table perso → banque `0x5AF1B0` × 128, indexée par `$102` ;
     - les banques SFA1 208–220, SFA2 229–248 et Upper 355–386 ;
     - le chargeur 4 joueurs `0x22B00` (fichiers `0x5AF2B0` 314–344 vers `0x1BC8000 + j×0x60000`) ;
     - les plans et décors.
   - D'après §115, il faudra le **fork MAME** (ROM graphique étendue).
2. **VERSUS à 2 joueurs** non joué : J2 n'a pas réussi à rejoindre avec les entrées essayées. Le portage gère sans
   doute J2 via `$C212`.
3. **`$C0BC`** jamais écrit dans ro9 : ses 4 lecteurs (`0x3728A4`…) copient 0 dans `$70-$7C(A6)`. À vérifier si
   ce chemin est atteint (fins ? Hyper n'a pas d'ARCADE).
4. **126 écritures de registre tombées** (`mame_ro9/chutes.json`) contre 56 pour ro3 : audit §107 à faire sur ro9.
   Le code ajouté d'Hyper prête beaucoup D8/A8 (295 zones, 59 refus « plusieurs entrées/sorties »).
5. **Correctifs 7 et 8** à reporter dans les originaux, après la non-régression complète de ro3 et de ro5
   (le correctif 7 change aussi leurs ROM, §3).
6. **Réécritures à la main** (`mains`) : REMPL / BCD / R1 / R2 réutilisables aux adresses ro9 (CARTE-ro9 §4.2) ; DEF à
   refaire.
7. **Reproductibilité** : MAME sans `-nvram_directory` partage l'EEPROM `sfa3ud` de `~/.mame` (y compris avec les
   autres sessions). Quatre MAME lancés en parallèle ont donné un essai resté sur le titre. Avec un dossier NVRAM
   propre par essai (`-nvram_directory essais/nvK`), les résultats sont stables.

## 6. Fichiers

- `untranspile/` : copie des scripts, corrigée (avec les évolutions amont de 14:38) ;
- `orig/` : originaux au moment de la copie ; `orig_1438/` : originaux à 14:38, base des diffs ;
- `correctifs/*.diff` : diffs `-u` par fichier ;
- `lua/` :
  - `banc_mem_liste.lua` (complément de `banc_mem.lua`) ;
  - `avec_entrees.lua` (séquence `INPUTS`, y compris périodique) ;
  - `suivi2.lua` (phases + arrêt à l'exception), `bp.lua` (commandes du débogueur à une image donnée) ;
  - `taches.lua`, `phases.lua`, `ram.lua`, `diffram.lua`, `combat_ids.lua` ;
- `outils/` :
  - `compare.py` (fonctions ro5/ro9 masquées), `dismips.py`, `resume_nat.py` (natifs) ;
  - `dasm68.py` (68K de l'image, capstone du venv), `trace_fn.py` (trace → zones MIPS) ;
- `mame_ro9/` : construction ro9 (ROM `roms_ro9`, `ext_940000.bin`, `ext_c84000.bin`, `ext_liste.txt`,
  `carte_image.txt`, `chutes.json`, captures) ;
- `mame_ro9_avant/` : construction sans les correctifs 7 et 8 (reproduit la faute) ;
- `garde_ro3/` : ro3 avec et sans le correctif 7 ;
- `essais/` : séquences et journaux des 4 versions ;
- journaux : `build_ro9.log`, `diag_premiere_faute.log`, `diag_training.log`, `suivi_training.log` ;
- images : `faute_736_exception.png`, `planche_titre_menu.png`, `planche_selection.png`,
  `planche_combat_training.png`.

## Annexe — diffs contre les originaux (état 14:38)

```diff
--- scripts/untranspile/profils.py (original 14:38)
+++ agent_ro9/untranspile/profils.py
@@ -36,8 +36,27 @@
         mains=False,                             # homologues a verifier (CARTE-ro5 §6 point 7)
         travail='<workspace>/work/mame_ro5', sortie='roms_ro5',
     ),
+    # (agent_ro9, MISE-EN-ROUTE-ro9.md) Hyper : valeurs de CARTE-ro9 §4, reverifiees dans le MIPS (outils/compare.py)
+    'ro9': dict(
+        fichier='ro9_usa_prog68k.bin',
+        va_reset=0x3da00, va_frame=0x3ee30, va_init=0x3ec20,   # = ro5 0xCED70 / 0x324B0 / 0x322A0 (MIPS masque)
+        irq2=0x3f1b0,                            # fonction du balayage vertical (contient 0x3F224 ; = ro5 0x32830)
+        sauve_regs=(0x3fe50, 0x40080),           # identiques a ro5 0x334D0 / 0x33700
+        hooks='hooks_fork_ro9.json',             # MODULE=ro9 hooks_fork.py (regenere a l'identique)
+        manette={0x38a958: (1, 0x58, 0x51a), 0x38a97c: (2, 0x5c, 0x91a)},   # jalr natif 0x23D20 (= ro5 0x23BB0)
+        aides={0x212dc0: 'movem_push', 0x213120: 'movem_pop', 0x213480: 'andi_ccr', 0x213610: 'abcd'},
+        be48=0xc0bc,                             # homologue de $BE48 : LU seulement (0x3728A4..), aucun natif ne l'ecrit
+        musique=None,                            # pas de table de ticks d'intro dans ro9 (CARTE-ro9 §4.3)
+        objets_intro=None,                       # pas de table 0x585750 ni d'acces 'lb 0x1129' dans ro9
+        palettes=None,
+        mains=False,
+        data_ext=0x940000,                       # fin des donnees en $940000 (marquee $01 dans la conversion) :
+                                                 # $C80000 est occupe par le fichier fixe 547 ($C84000-$D0B188)
+        travail='<workspace>/work/agent_ro9/mame_ro9', sortie='roms_ro9',
+    ),
 }
 
 NOM = os.environ.get("MODULE", "ro3")
 P = PROFILS[NOM]
+if os.environ.get("TRAVAIL"): P = dict(P, travail=os.environ["TRAVAIL"])   # (agent_ro9) essais hors des dossiers partages
 def chemin(): return os.path.join(EXTRACT, P['fichier'])
--- scripts/untranspile/assets_natifs.py (original 14:38)
+++ agent_ro9/untranspile/assets_natifs.py
@@ -43,17 +43,34 @@
     SITES_DYN = {0x4cc04: (0x8c21, 2)}  # index a l'execution : (octet $8C21(A5) >> 2) & 1 (intro d'Upper : 2 fichiers)
     FIXES = {390: 0xB04000}
     N_SITE = 3
+if os.environ.get("MODULE", "ro3") == "ro9":   # (agent_ro9) Hyper : AUCUN chargeur natif de tables d'animation
+    # Le seul chargeur natif de ro9 (0x22B00, sites 0x970BC / 0x31AF78 / 0x31AFA4) est l'homologue du chargeur
+    # 4 joueurs de ro3 0x3838D0 (banques graphiques via 0x154D20 / 0x155080 ; tables 0x5AF2B0 / 0x5AF1B0) : il
+    # n'appelle pas 0x154C90 (decompression d'un fichier « anim » a ctx+0x9C) et n'ecrit pas $C0BC(A5).
+    # Les homologues de 0x383700 / 0x3837D0 n'existent pas -> pas de talons, bloc virtuel vide.
+    LOAD_BASE = LOAD_SITE = None
+    VBASE = 0xD20000                     # inutilise (bloc vide) ; hors RAM ro9 ($B80000-$BFFFFF) et du fichier 547
+    T_SITE = T_PERSO = None
+    N_PERSO = 0
+    NATIF_SITE = NATIF_PERSO = None
+    SITES = {}
+    SITES_DYN = {}
+    FIXES = {547: 0xC84000}              # frames de sprites (en-tete d1ff f2ff.. comme 289/390), 553 352 o :
+                                         # 39 656 longs alignes des donnees dans [$C84000, $D0B188)
+    N_SITE = 0
+CACHE_ECRIT = os.environ.get("ANIM_CACHE", CACHE)   # (agent_ro9) cache en ecriture (lecture : CACHE d'abord)
 
 def fichier(n):
-    p = os.path.join(CACHE, "f%d.bin" % n)
-    if os.path.exists(p): return open(p, "rb").read()
+    for c_ in (CACHE, CACHE_ECRIT):
+        p = os.path.join(c_, "f%d.bin" % n)
+        if os.path.exists(p): return open(p, "rb").read()
     sys.path.insert(0, EXTRACT)
     from mwo3_codec import decompress
     man = {int(r['idx']): (int(r['offset']), int(r['size'])) for r in csv.DictReader(open(os.path.join(EXTRACT, "manifest.csv")))}
     o, s = man[n]
     with open(os.environ["XDATA"], "rb") as f:
         f.seek(o); d = bytes(decompress(f.read(s)))
-    os.makedirs(CACHE, exist_ok=True); open(p, "wb").write(d)
+    os.makedirs(CACHE_ECRIT, exist_ok=True); open(os.path.join(CACHE_ECRIT, "f%d.bin" % n), "wb").write(d)
     return d
 
 def tables(buf, rtbase=0x1F0000):
--- scripts/untranspile/mame_test.py (original 14:38)
+++ agent_ro9/untranspile/mame_test.py
@@ -12,6 +12,7 @@
 from mips import CODE0
 from profils import P, NOM as MODULE, chemin as module_chemin     # (HANDOFF §108) profil par module (MODULE=ro3|ro5)
 T.AIDES_RECOMP = dict(P['aides'])
+if P.get('data_ext'): T.DATA_EXT = P['data_ext']      # (agent_ro9) bloc externe de fin des donnees par module
 W = P['travail']
 STUB_RTS, STUB_RTE = 0x800, 0x802
 STUB_ANIM = 0x810                                        # talons des chargements natifs de tables d'animation
@@ -88,8 +89,8 @@
     asite, aperso = AN.tables(buf)
     stub_site = [STUB_ANIM + 10*k for k in range(len(asite))]
     stub_perso = STUB_ANIM + 10*len(asite)
-    SYSC[AN.NATIF_SITE + T.RUNTIME_BASE] = stub_site[0]  # site 0 ; les autres sites : appel repatche
-    SYSC[AN.NATIF_PERSO + T.RUNTIME_BASE] = stub_perso
+    if AN.NATIF_SITE is not None: SYSC[AN.NATIF_SITE + T.RUNTIME_BASE] = stub_site[0]  # site 0 ; autres sites : appel repatche
+    if AN.NATIF_PERSO is not None: SYSC[AN.NATIF_PERSO + T.RUNTIME_BASE] = stub_perso   # (agent_ro9) ro9 : aucun
     def ext(t):                                          # appels natifs : noyau pour les appels systeme de fils, sinon RTS
         return SYSC.get(t + T.RUNTIME_BASE, STUB_RTS)
     import json                                          # fonctions NATIVES du module (dans ses bornes) : externes
@@ -148,7 +149,7 @@
     if T.HW_TAG:
         R = T.RAM_HI << 16; PR = T.PORT_RAM; TG = 0x01000000
         ranges = ([(T.CODE_END_RT, T.DATA_SPLIT, T.DATA_BASE - T.CODE_END_RT),
-                   (T.DATA_SPLIT, T.DATA_END_RT, T.DATA_EXT - T.DATA_SPLIT)] if T.DATA_SPLIT else
+                   (T.DATA_SPLIT, T.DATA_END_RT, T.DATA_EXT - T.DATA_SPLIT + (TG if P.get('data_ext') else 0))] if T.DATA_SPLIT else
                   [(T.CODE_END_RT, T.DATA_END_RT, T.DATA_BASE - T.CODE_END_RT)]) + [
                   (T.DATA_END_RT, R, PR - T.DATA_END_RT),
                   (R, R + 0x10000, 0xff0000 - R),
@@ -160,7 +161,7 @@
                   (R + 0x62000, R + 0x80000, PR + 0x80000 + 0x12000 - (R + 0x62000))]
         NDATA = (T.DATA_SPLIT - T.CODE_END_RT) if T.DATA_SPLIT else (len(buf) - end)   # donnees DANS l'image
         ASSET = (T.DATA_BASE + NDATA + 0xff) & ~0xff      # bloc des tables d'animation, apres les donnees
-        ranges.append((AN.VBASE, AN.VBASE + len(ablob), ASSET - AN.VBASE))
+        if ablob: ranges.append((AN.VBASE, AN.VBASE + len(ablob), ASSET - AN.VBASE))   # (agent_ro9) ro9 : bloc vide
         ccode, _ = K.build_conv(CONV, ranges)
         assert CONV + len(ccode) <= STUB_RTS
         img[CONV:CONV+len(ccode)] = ccode
@@ -305,11 +306,12 @@
     # du portage : table aux octets arcade). La traduction lit l'octet bas (MOVE.B D1) -> parametre 0 pour tous,
     # bits de scene 4/2/0 au lieu de 5..0 ($FF8017 = $15 au lieu de $3F), fondus des portraits jamais lances.
     # Seul lecteur de la table : on echange les octets du parametre dans l'image.
-    t_ = T.addr_to_68k(P['objets_intro'])
-    for k_ in range(12):
-        o_ = t_ + 4 * k_ + 2
-        img[o_], img[o_ + 1] = img[o_ + 1], img[o_]
-    print("table 0x585750 en $%x : parametres remis en octet bas" % t_)
+    if P['objets_intro']:                                # (agent_ro9) ro9 : table absente
+        t_ = T.addr_to_68k(P['objets_intro'])
+        for k_ in range(12):
+            o_ = t_ + 4 * k_ + 2
+            img[o_], img[o_ + 1] = img[o_ + 1], img[o_]
+        print("table 0x585750 en $%x : parametres remis en octet bas" % t_)
     if T.HW_TAG:
         assert T.DATA_BASE + len(be) <= ASSET
         tperso = ASSET + len(ablob)
@@ -394,6 +396,9 @@
             assert all(not (r0 <= base < r1) for r0, r1, _ in ranges), "fichier %d : sa plage serait convertie" % n
             open(os.path.join(W, "ext_%06x.bin" % base), "wb").write(bytes(b for i in range(0, len(d), 2) for b in (d[i+1], d[i])))
             print("fichier %d : %d octets a adresse fixe $%x (banc_mem.lua)" % (n, len(d), base))
+        # (agent_ro9) liste des blocs externes pour banc_mem_liste.lua (banc_mem.lua ne connait que des bases fixes)
+        exts = sorted(["%06x" % b_ for b_ in AN.FIXES.values()] + (["%06x" % T.DATA_EXT] if T.DATA_SPLIT else []))
+        open(os.path.join(W, "ext_liste.txt"), "w").write("\n".join(exts) + "\n")
     sw = bytes(b for i in range(0, len(img), 2) for b in (img[i+1], img[i]))
     out = os.path.join(W, P['sortie'], "sfa3ud"); os.makedirs(out, exist_ok=True)
     names = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
@@ -407,6 +412,9 @@
     import assemble as _A
     print("aiguillages : %d entrees hors de portee 16 bits -> tremplins (HANDOFF §93)" % sum(len(v) for v in _A.FAR_ENT.values()))
     print("octets via An apres ADDA Dk,An : %d acces a adresse exacte (HANDOFF §97)" % T.BYTE_ADDA[0])
+    print("flux d'octets decroissants -(An) a adresse exacte : %d (agent_ro9)" % T.BYTE_PRE[0])
+    import extra_regs as _X
+    print("zones A8/D8 : retours de boucle sur la restauration : %d (agent_ro9)" % _X.BACK_AFTER_N[0])
     print("longs par post-increment fusionnes : %d (HANDOFF §103)" % T.LONG_POSTINC[0])
     print("adresses video formees par decalage converties : %d (HANDOFF §110)" % T.VRAM_SHIFT[0])
     print("pointeurs de table a index brut (x4) : %d (HANDOFF §112)" % T.IDX_X4[0])
--- scripts/untranspile/diag.py (original 14:38)
+++ agent_ro9/untranspile/diag.py
@@ -12,6 +12,8 @@
 W = _PR.P['travail']; ROMS = os.path.join(W, _PR.P['sortie'])
 os.environ["BANC_DIR"] = W + "/"
 D = os.path.dirname(os.path.abspath(__file__))
+# (agent_ro9) blocs externes hors de la liste fixe de banc_mem.lua (ro9 : $940000, $C84000)
+LUA_LISTE = 'dofile("%s/lua/banc_mem_liste.lua")\n' % os.path.dirname(D)
 EXC = {2: "erreur de bus", 3: "erreur d'adresse", 4: "instruction illegale", 5: "division par zero",
        6: "CHK", 7: "TRAPV", 8: "privilege", 9: "trace", 10: "ligne A", 11: "ligne F",
        99: "PC hors du code (fin d'image)"}
@@ -69,7 +71,7 @@
 '''
 
 def mame(script, debug=False, timeout=400):
-    path = os.path.join(W, "_diag.lua"); open(path, "w").write('dofile("%s/banc_mem.lua")\n' % LUA + LUA_INPUTS + script)
+    path = os.path.join(W, "_diag.lua"); open(path, "w").write('dofile("%s/banc_mem.lua")\n' % LUA + LUA_LISTE + LUA_INPUTS + script)
     cmd = ["mame", "sfa3ud", "-rompath", ROMS, "-video", "none", "-sound", "none",
            "-nothrottle", "-skip_gameinfo", "-autoboot_script", path]
     if debug: cmd += ["-debug", "-debugger", "none"]
--- scripts/untranspile/translate.py (original 14:38)
+++ agent_ro9/untranspile/translate.py
@@ -10,8 +10,8 @@
   MOVE.B #imm,(d16,A5) = 1b7c   MOVE.W = 3b7c   MOVE.L = 2b7c
   MOVE.B Dn ,(d16,A5)  = 1b40|n MOVE.W = 3b40|n MOVE.L = 2b40|n
 """
-import sys, struct
-sys.path.insert(0, "<workspace>/scripts/untranspile")
+import sys, struct, os
+sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # (agent_ro9) la copie, pas les originaux
 from mips import decode, REG
 
 A5_SLOT = 0x1114                      # [0x70001114] = registre A5
@@ -749,6 +749,31 @@
         prev=k
     return res
 
+BYTE_PRE=[0]
+BYTE_PRE_ON=__import__('os').environ.get('BYTE_PRE','1')!='0'
+def byte_streams_pre(out):
+    """(agent_ro9) FLUX D'OCTETS DECROISSANT EN MODE cps2 : 'SUBQ.W #1,An ; MOVE.B 1(An),<ea>' (deplacement 0 XOR 1,
+    juste seulement si An est PAIR apres le decrement). Hyper mips 0x33C4F0 : A8 = table 0x5C6960 + 4*perso + 4,
+    puis 'A8 -= 1 ; lb 0(A8)' : premier octet lu a une adresse IMPAIRE -> octet du perso suivant. Adresse exacte
+    a l'execution (An XOR 1, bascule du bit 0 via la pile) ; la bascule de retour garde les drapeaux du MOVE.B."""
+    import m68k
+    res=list(out); prev=None
+    tog=lambda n: [0x2f08|n, 0x0a2f,0x0001,0x0003, 0x205f|(n<<9)]
+    for k,(va,mn,ws) in enumerate(res):
+        if not ws: continue
+        if prev is not None:
+            pva,pmn,pws=res[prev]
+            if len(pws)==1 and (pws[0]&0xfff8)==0x5348 and len(ws)>=2 and (ws[0]&0xf000)==0x1000 and ws[1]==0x0001:
+                n=pws[0]&7; w=ws[0]; dmode=(w>>6)&7; dreg=(w>>9)&7
+                r=m68k.decode_one(ws,0,len(ws))
+                if (w&0x3f)==(0x28|n) and r and r[0]==len(ws) and not (dmode in (2,3,4,5,6) and dreg==n) \
+                   and not (dmode==7 and dreg in (2,3)):
+                    new=tog(n)+[(w&~0x3f)|0x10|n]+ws[2:]+[0x40e7]+tog(n)+[0x44df]
+                    res[k]=(va,mn+"  [flux d'octets -(A%d) : adresse XOR 1 a l'execution]"%n,new)
+                    BYTE_PRE[0]+=1
+        prev=k
+    return res
+
 def byte_index_exact(out):
     """OCTET INDEXE EN MODE cps2 (HANDOFF §66) : 'd8(An,Xn)' portait d8 XOR 1 en supposant l'index PAIR ;
     faux pour un index impair (numero de joueur 0/1 : ecriture dans le mot voisin). Adresse exacte a
@@ -3123,7 +3148,7 @@
     if MEMMODE=='cps2' and _os.environ.get("LONG_POSTINC","1")!="0": out=merge_long_postinc(out, br_targets)
     if MEMMODE=='cps2': out=vram_shift_const(out, br_targets)
     if MEMMODE=='cps2' and _os.environ.get("DROP_SR","1")!="0": out=drop_dead_sr(out)
-    if MEMMODE=='cps2': out=byte_streams(out); out=byte_index_exact(out); out=byte_after_adda(out)
+    if MEMMODE=='cps2': out=byte_streams(out); out=byte_streams_pre(out) if BYTE_PRE_ON else out; out=byte_index_exact(out); out=byte_after_adda(out)   # (agent_ro9) flux decroissant
     if DPTR_FIX: out=[dptr_fix(e) for e in out]
     if AUDIT_MEM:                                         # (HANDOFF §107) ecritures memoire sans trace dans la sortie
         _vas={va for va,mn,ws in out}
--- scripts/untranspile/extra_regs.py (original 14:38)
+++ agent_ro9/untranspile/extra_regs.py
@@ -10,6 +10,8 @@
 A8_HOME_PLAN = os.environ.get("A8_HOME", "87e0") != "none"   # (HANDOFF §80) A8 a un domicile memoire
 MERGE_IFELSE = os.environ.get("MERGE_IFELSE", "1") != "0"   # (HANDOFF §114)
 MERGED = [0]
+BACK_AFTER = os.environ.get("BACK_AFTER", "1") != "0"   # (agent_ro9) retour de boucle sur la restauration
+BACK_AFTER_N = [0]
 EARLY_CLOSE = set()          # (case, debut) des zones refermees juste apres leur derniere instruction
 POOL = {'A': [4, 3, 2, 1, 0, 6], 'D': [7, 6, 5, 4, 3, 2, 1, 0]}     # A5 (globales) jamais preté
 
@@ -169,16 +171,22 @@
         if hi not in pos: hi = vas[bisect.bisect_right(vas, hi) - 1]
         k = bisect.bisect_right(vas, hi)
         after = vas[k] if k < len(vas) else hi + 4
-        bad = False; resto = False
+        bad = False; resto = False; back = False
         for b, t in brs[f]:
             inside_b = lo <= b <= hi; inside_t = lo <= t <= hi
             if not inside_b and inside_t and t != lo: bad = True; break      # entree laterale
             if inside_b and not inside_t and t != after: bad = True; break    # sortie laterale
             if not inside_b and t == after and not (b > hi): resto = True     # saut exterieur sur la restauration
+            # (agent_ro9) retour de boucle venu d'APRES la zone et visant 'after' : la restauration emise sur 'after'
+            # serait rejouee a chaque tour (pile desequilibree, domicile de A8 ecrase par le registre restaure).
+            # Hyper mips 0x33C408-0x33C46C (A8 = table 0x5C6960 + 4*perso, boucle 0x33C470 <- 0x33C5A4).
+            if BACK_AFTER and not inside_b and t == after and b > hi: resto = True; back = True; BACK_AFTER_N[0] += 1
         if resto and not bad:
             # (HANDOFF §80) restauration emise JUSTE APRES la derniere instruction de la zone (et non sur la
             # cible 'after', atteinte de l'exterieur) : possible si aucun branchement interne ne sort vers 'after'
-            if A8_HOME_PLAN and s == 0x1120 and not any(lo <= b <= hi and t == after for b, t in brs[f]):
+            # (agent_ro9) D8 aussi quand c'est un retour de boucle : sa restauration (domicile D8, sauvegarde fixe) ne
+            # touche pas la pile ; la refuser renvoyait la zone au repli memoire, qui perdait 'LSL.W #2' et l'ADDA (0x33C42C)
+            if A8_HOME_PLAN and (s == 0x1120 or back) and not any(lo <= b <= hi and t == after for b, t in brs[f]):
                 EARLY_CLOSE.add((s, lo))
             else: bad = True
         if not bad and any(x.m == 'jr' for x in L[pos[lo]:pos.get(hi, pos[lo]) + 1]): bad = True
```
