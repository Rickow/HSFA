# État des lieux — Hyper SFA / Anthology vers CPS2 (2026-10-04)

> **État au 2026-10-24 : ce document n'est plus tenu à jour.** L'état des chantiers est dans
> [`AGENTS.md`](../../AGENTS.md) §5 (tableau des chantiers et des décisions D1-D7), le point transverse dans
> [`POINT-ETAPE-2026-10-21`](../rapports/POINT-ETAPE-2026-10-21.md), la reprise dans
> [`TRANSMISSION-2026-10-21`](TRANSMISSION-2026-10-21.md), ce qui a été livré dans
> [`docs/guide/LIVRAISONS.md`](../guide/LIVRAISONS.md), et le journal va jusqu'au §172 (index :
> [`INDEX-HANDOFF.md`](INDEX-HANDOFF.md) §13). En bref : traducteur v150 validée et v151 en préparation (§171) ;
> greffe Arcade sur Hyper à `ro9a7_fige` (60/85 fins) ; persos MAX dans Upper au lot 2b16 ; cœur FBNeo à 16 patchs
> plus le 11b. Ce qui suit reste utile pour ses commandes, ses variables et ses pièges.

> **Instantané du 2026-10-04** (jusqu'au §115), gardé pour ses commandes, ses variables et ses pièges. L'état à jour
> est dans le [README](../../README.fr.md) et le [journal](HANDOFF.md) §141-§146. Les chemins `<workspace>/...` sont
> ceux de l'espace de travail ; dans le dépôt, les outils sont dans `src/hsfa/` et `scripts/` ([journal/README.md](README.md)).

> Synthèse pour reprendre vite. Source de vérité : `<workspace>/github/docs/journal/HANDOFF.md` (§1-§115) ;
> index par thème : `INDEX-HANDOFF.md` (même dossier). Les « § » suivent la série canonique (voir l'index, §0).

## 1. But et méthode, en cinq lignes

- Street Fighter Alpha Anthology (PS2, `SLUS-21317`, CRC `72CE7A78`) contient **SFA3 (`ro3`), Upper (`ro5`) et Hyper
  (`ro9`)** sous forme de **recompilation statique 68000 → MIPS** (banc de registres 68K dans le scratchpad).
- On **retraduit le MIPS en 68000** (`translate.py` + `assemble.py`), avec la ROM arcade de SFA3 comme corrigé, puis on fait
  tourner le résultat sur une **CPS2 émulée** (banc MAME aujourd'hui, fork MAME demain, cœur FBNeo à la fin : Android /
  RetroArch).
- Ordre décidé (§109) : **Upper → MAX (4 persos PSP) → Hyper**. Le reste de MAX est écarté pour l'instant.

## 2. Où en est chaque chose

| Chantier | État | Référence |
|---|---|---|
| **SFA3 (`ro3`) au banc MAME** | **complet** : attraction stable (40 000 images), partie Arcade jusqu'au générique, **32 fins conformes**, modes VERSUS / SURVIVAL / DRAMATIC / TRAINING, commandes **42/42** identiques à l'arcade, cadence turbo 133,3 % (= arcade), son validé à l'oreille | §77, §81, §93, §98, §110-§113 |
| SFA3 : restes connus | OPTION / EXIT = code natif de l'exécutable PS2 (écran noir au banc, à réécrire pour le fork) ; graphismes retouchés par l'Anthology (chrono ∞, quelques tuiles) ; 28 « écritures de registre tombées » restantes (zones du portage, D8/A8) | §102, §89, §107 |
| **Upper (`ro5`) au banc** | **jouable de bout en bout sur le fork `sfa3hx`** : attraction, titre, modes, parcours Arcade complet (écrans d'histoire, NEXT STAGE, Juli et Juni, Bison), **40/40 fins** atteintes, SURVIVAL / VERSUS / entraînement vérifiés (§128) ; son = **ROM son hybride** (musiques de SFA3 + voix propres d'Upper, `HSFA_SON=<dossier>`, §127) ; non-régression `nonreg_ro5.sh`. Restent : 5 blocs exacts (`audit_exacts.txt`), effets MAZI-SAIKYO-CLASSIC à vérifier | §108-§126 |
| **Fork MAME `sfa3hx`** | **en cours, pas encore dans le journal** (voir §3) | §109, §115 |
| MAX | Eagle affiché et palettes dans le banc SFA3 (en pause) ; fins = réutiliser des fins existantes ; octets libres `$3F0`/`$3F2` | §99, §105, §110, §111 |
| Hyper (`ro9`) | traduit et assemblé (97,6 %), pas encore au banc ; versions décodées (`$102/$116/$117/$D3`) | §46, §50, §54, §55 |
| SFA2 | étude faite : 20 décors ajoutables sur le fork (registre de base par plan) | §113 |
| Fil PS2 (cross-stage, pnach) | en sommeil depuis le 2026-09-26 | R§0-R§3 |

**Décisions en vigueur (§109)** : fork MAME = banc intermédiaire (jeu dérivé de `sfa3ud` dans `cps2.cpp` qui rend en natif ce
que font les scripts Lua : ROM programme et graphique étendues, banques, liste d'objets verrouillée, surcadençage), puis
report dans FBNeo ; MAX ⊃ Upper ; les 4 persos MAX vont en `$26`/`$27` + 2 places à créer (tables de 40 entrées) ;
sauvegarde CPS2 = EEPROM 93C46 (128 o) seulement.

## 3. Fork MAME : ce qui existe (constaté sur disque le 2026-10-04 vers 14 h 15)

- Source : `<workspace>/mame-fork/mame` (MAME 0.285, `git diff` : `src/mame/capcom/cps2.cpp` +96 lignes,
  `src/mame/mame.lst` +1). Construction en sous-cible **`cps2f`** → binaire `<workspace>/mame-fork/mame/cps2f` (86 Mo).
  `build.log` : 1re édition de liens en échec (`référence indéfinie vers driver_sfa3hx`) ; `build2.log` : relinké, et
  `./cps2f -listfull sfa3hx` répond → **le binaire contient le jeu**. Non encore lancé avec un vrai programme (à vérifier).
- Jeu **`sfa3hx`** (clone de `sfa3`, machine `hsfa`, init `init_hsfa`) :
  - région `gfx` de **128 Mo** ; tuiles supplémentaires lues dans le fichier `HSFA_GFX` à partir de `$2000000`
    (= code `$40000`, format interne MAME, 128 o / tuile) ;
  - **code de tuile étendu par les bits 10-11 de X** (`code += (x & 0x0c00) << 8`, bits 18-19) — ⚠ le §115 proposait
    « bit 15 de Y » ; choix réel différent, **à documenter dans le journal** ;
  - ROM `$A00000-$CFFFFF` remplie au démarrage depuis `HSFA_EXT/ext_<adresse>.bin` (remplace `banc_mem.lua`) ;
  - `HSFA_CLOCK` = facteur d'horloge du 68K (> 1 = surcadençage).
- Sorties préparées : `work/mame_ro5/hsfa_gfx.bin` (6,4 Mo), `work/mame_ro5/banques_hx/`, et
  `work/mame_ro5/roms_fork/sfa3hx → ../roms_ro5/sfa3ud` (lien).
- Pas encore fait (d'après §109) : emplacements de banques et plans en natif, verrou de la liste d'objets, intégration aux
  scripts (`diag.py`, `nonreg.sh` appellent `mame`, pas `cps2f`). ⚠ L'EEPROM de `sfa3hx` (`~/.mame/nvram/sfa3hx`) n'est pas
  protégée comme celle de `sfa3ud` (piège n° 8).

## 4. Dossiers

| Chemin | Contenu |
|---|---|
| `<workspace>/scripts/untranspile/` | **copie de travail** des outils Python (chemins absolus) : `translate.py`, `assemble.py`, `mame_test.py`, `diag.py`, `profils.py`, `kernel68k.py`, `banques.py`, `nonreg.sh`… |
| `<workspace>/work/mame/` | banc ro3 : scripts Lua **actifs** (`jeu.lua`, `tournee.lua`, `commandes.lua`, `banc_*.lua`, `visu.lua`…), `roms_tr/` (traduction), `roms/` (ROM arcade de référence, `REF=1`), `roms_vis/`, `carte_image.txt`, `chutes.json`, `cmd_ref.txt` |
| `<workspace>/work/mame_ro5/` | banc Upper : `roms_ro5/`, `banques/`, `ext_*.bin`, `carte_image.txt`, fork : `roms_fork/`, `banques_hx/`, `hsfa_gfx.bin` |
| `<workspace>/work/cps2/` | `sfa3_prog.bin`, **`sfa3ud_prog.bin`** (tables), `roN_traduit.bin`, `roN_programme.bin`, ROM CPS2 brutes |
| `<workspace>/work/xdata/X_DATA.BIN` | ressources de l'ISO (lecture seule) |
| `<workspace>/work/etats_ps2/` | **copies** des états PCSX2 fournis par l'utilisateur (`ee/` = RAM extraite) |
| `<workspace>/work/carto_ro5/`, `carto_ro9/`, `carto_persos/`, `carto_sfa2/` | cartes produites par des agents (`CARTE-ro5.md`…) |
| `<workspace>/anthology_extract/decompressed/` | modules MIPS `roN_usa_prog68k.bin` (mal nommés : c'est du MIPS) |
| `<workspace>/github/` | dépôt `Rickow/SFA-Anthology-PS2-mods` (privé) ; `src/hsfa/` = copie **anonymisée** des outils (+ `mame/` = scripts Lua) |
| `<workspace>/mame-fork/` | fork MAME (voir §3) |
| `~/.mame/nvram/sfa3ud` (lecture seule) / `~/.mame/nvram_sauvegarde/` | EEPROM figée du banc |

## 5. Commandes

Préalable : `source <workspace>/env.sh` (venv : numpy, capstone). Toujours `nice -n 19` pour ce qui est lourd ;
un seul calcul lourd à la fois.

**Construire SFA3 (ro3)** — reconstruit `work/mame/roms_tr/sfa3ud/` :
```
cd <workspace>/scripts/untranspile
XDATA=<workspace>/work/xdata/X_DATA.BIN nice -n 19 python3 mame_test.py
```
Surveiller dans la sortie le compteur « écritures de registre tombées » (toute hausse = régression, §107). **Jamais**
`MAX_DEMO` / `MAX_PAL` pour une construction de référence.

**Construire Upper (ro5)** — `work/mame_ro5/roms_ro5/`, `ext_c80000.bin`… :
```
cd <workspace>/scripts/untranspile
MODULE=ro5 XDATA=<workspace>/work/xdata/X_DATA.BIN nice -n 19 python3 mame_test.py
MODULE=ro5 nice -n 19 python3 banques.py tout        # tables des banques d'Upper (§115 ; usage : banques.py N [N...])
```

**Lancer le banc** (toujours `-video none`, la fenêtre bloque MAME ; captures par `SNAPS` + `-snapshot_directory`) :
```
cd <workspace>/work/mame
# SFA3 traduit, partie avec entrées
INPUTS="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;2000-2006::IN2:1 Player Start;3500-19900%200,6::IN0:P1 Button 1" \
NF=20000 OUT=<journal> SNAPS=3000,6000 nice -n 19 mame sfa3ud -rompath roms_tr -video none -sound none -nothrottle \
  -skip_gameinfo -snapshot_directory <dossier> -autoboot_script jeu.lua
# Upper (banc graphique, §115)
BANC_DIR=<workspace>/work/mame_ro5/ BANC_BANQUES=<workspace>/work/mame_ro5/banques/ BANC_PTR_ANIM=FF40BC \
BANC_GFX_INTRO=456 NF=12000 OUT=<journal> nice -n 19 mame sfa3ud -rompath <workspace>/work/mame_ro5/roms_ro5 \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_script jeu.lua
```
Fork (proposition non vérifiée, d'après le code de `init_hsfa`) :
`HSFA_GFX=<workspace>/work/mame_ro5/hsfa_gfx.bin HSFA_EXT=<workspace>/work/mame_ro5 HSFA_CLOCK=1.2
<workspace>/mame-fork/mame/cps2f sfa3hx -rompath <workspace>/work/mame_ro5/roms_fork …`

**Diagnostic (1 exécution = la 1re faute, avec la va MIPS)** :
```
cd <workspace>/scripts/untranspile
MAXF=20000 nice -n 19 python3 diag.py 30 --nobuild            # ro3 ; sans --nobuild : reconstruit d'abord
MODULE=ro5 MAXF=12000 nice -n 19 python3 diag.py 30 --nobuild # Upper (dossier et ROM pris dans profils.py)
INPUTS="…" MAXF=60000 … diag.py 30 --nobuild                   # même format d'entrées que jeu.lua
```
Fin attendue : « aucune exception ». Code 99 = PC hors du code.

**Non-régression ro3 (à lancer après chaque correctif du traducteur ; jusqu'à ~2 h)** :
```
bash <workspace>/scripts/untranspile/nonreg.sh
bash <workspace>/scripts/untranspile/nonreg_ro5.sh      # Upper (fork), après MODULE=ro5 mame_test.py
```
Attendu : 3 × « aucune exception », « 42 actions, 0 différentes », 5 359 tours en 4 019 images (133,3 %). Le script
n'a pas de `MODULE` : il ne teste que ro3.

**Test des commandes à la main (§93)** :
```
cd <workspace>/work/mame
OUT=<t.txt> nice -n 19 mame sfa3ud -rompath roms_tr -video none -sound none -nothrottle -skip_gameinfo -autoboot_script commandes.lua
python3 <workspace>/scripts/untranspile/commandes.py cmd_ref.txt <t.txt>
```
La référence `cmd_ref.txt` vient de `REF=1 … -rompath roms …` : **ne pas l'écraser**.

**Partie complète (§110-§112)** :
```
cd <workspace>/work/mame
REF=1 OUT=<ref.txt> NF=24000 PERSO=00 FORCE="Lff8540=ffffffff" SNAPFIN=1 nice -n 19 mame sfa3ud -rompath roms \
  -video none -sound none -nothrottle -skip_gameinfo -snapshot_directory <d_ref> -autoboot_script tournee.lua
OUT=<tr.txt> NF=24000 PERSO=00 FORCE="Lff8540=ffffffff" SNAPFIN=1 nice -n 19 mame sfa3ud -rompath roms_tr … tournee.lua
OUT=<tr.txt> MODE=2 NF=40000 … tournee.lua      # traduction seulement : 0 ARCADE, 1 VERSUS, 2 SURVIVAL, 3 DRAMATIC, 4 TRAINING
```
Charger un état MAME : `SAVEAT`/`SAVENAME` pour l'écrire, puis `manager.machine:load(nom)` depuis Lua — **jamais `-state`**.

**Visualiseur d'état PS2 (§89)** : `python3 <workspace>/scripts/untranspile/visu_rom.py` (construit `roms_vis`), puis, depuis `work/mame`,
`ETAT=<workspace>/work/etats_ps2/ee/<nom> mame sfa3ud -rompath roms_vis … -autoboot_script visu.lua`.

## 6. Variables d'environnement

| Variable | Où | Rôle (défaut) |
|---|---|---|
| `MODULE` | Python | `ro3` (défaut) / `ro5` : profil (`profils.py`) |
| `XDATA` | Python | chemin de `X_DATA.BIN` (ressources natives, banques) |
| `MEMMODE` | Python | `hote` (validation ROM) / `cps2` (forcé par `mame_test.py`, `build_rom.py`) / `type` |
| `EXTRA_REGS`, `A8_HOME`, `D8_HOME`, `MERGE_IFELSE` | `translate`, `extra_regs` | A8/D8 prêtés (1), domiciles `87e0` / `87f0` (`none` = ancien comportement), fusion si/sinon (1) |
| `LONG_POSTINC`, `DROP_SR`, `DN_ALU`, `MASQ_OK`, `TYPE_REGS` | `translate` | judas `MOVE.L (An)+` (1), SR mort retiré (1), module `dn_alu` (1), masques 32 bits, bases typées (`5,6`) |
| `AUDIT_MEM=1` | `translate` | écrit `mem_miss.json` |
| `CODECONV_DICHO=1`, `DPTR`, `PILE`, `MAINS`, `VA_INIT` | `mame_test` | dichotomie au lieu du hachage ; conversion des pointeurs (`runtime`) ; pile 68K (`664000`) ; nb de routines à la main ; init |
| `MAX_DEMO`, `MAX_PAL`, `MAX_PAL_ID` | `mame_test` | démonstrations MAX (⚠ reconstruire sans après) |
| `DBG_VA`, `DBG_RANGE` | `translate` | traces de débogage |
| `MAXF`, `INPUTS` | `diag.py`, `jeu.lua` | dernière image ; entrées `debut-fin:PORT:Champ` ou `debut-fin%periode,duree:PORT:Champ` |
| `BANC_DIR`, `BANC_BANQUES`, `BANC_PTR_ANIM`, `BANC_GFX_INTRO` | Lua | dossier du module (`<workspace>/work/mame/`), tables de banques, pointeur d'animation (`FF3E48` ro3 / `FF40BC` ro5), fichier de l'emplacement 4 |
| `SPRITES`, `BANC_MEM`, `BANC_SANS_AGE`, `BANC_UNE_BANQUE`, `BANQUE_J1/J2`, `SLOT1`, `SANS_PAL` | Lua | couper le banc de sprites / la mémoire externe, diagnostics |
| `NF`, `OUT`, `SNAPS`, `REF` | Lua | dernière image, journal, captures, `1` = ROM arcade |
| `PERSO`, `MODE`, `CURSEUR`, `FORCE`, `FORCEC`, `SNAPP`, `SNAP0`, `SNAPFIN`, `DUMPC`, `DOUT`, `SAVEAT`, `SAVENAME` | `tournee.lua` | voir §110-§112 |
| `FS0`, `FS1`, `STG`, `SUIVI` | `force_stage.lua` | décor imposé |
| `ETAT`, `IMG` | `visu.lua` | état PS2 à rendre |
| `HSFA_GFX`, `HSFA_EXT`, `HSFA_CLOCK` | fork `cps2f` | tuiles étendues, blocs `ext_*.bin`, horloge 68K |

## 7. Pièges à ne pas rejouer (encore vrais)

**Adresses et mémoire**
1. **Déplacements A5 signés** : `$BE48(A5)` = `$FF3E48`, `-$7178(A5)` = `$FF0E88`, `$BF30(A5)` = `$FF3F30` (§67, §86, §108).
2. **Octet = adresse XOR 1** en mode cps2 (le champ `$A8` de la ROM se lit `$A9` dans la traduction, `tournee.lua` fait `a ~ 1`).
   Exceptions : ports d'entrée et QSound en octet **exact** (§62, §78) ; flux `(An)+`, index impairs, octet après `ADDA` =
   séquences exactes à l'exécution (§65, §66, §97).
3. **Longs à moitiés échangées en mémoire** : X/Y d'un objet en `+$12/+$16` au lieu de `+$10/+$14` ; octets d'état `$4-$7`
   échangés par mot ; un long empilé tel quel reste échangé (§77). Tout script Lua de comparaison doit normaliser.
4. **Banc de registres** (version juste) : A0-A7 `0x1100-0x111C`, **A8 `0x1120`**, D0-D7 `0x1124-0x1140`, **D8 `0x1144`**,
   `0x114C` pile privée, RES `0x1150` (Z, N), X `0x1154`, **C `0x1158`**. Base d'exécution **`0x1f0000`** ; 68K dès `0x22b00`
   (ro3/ro5), `0x22de0` (ro9).
5. Le « DBRA » du recompilateur boucle tant que ≥ 0 (`SUBQ.W ; BPL`), pas tant que ≠ −1 (§74).
6. Une constante **impaire** n'est jamais une adresse de données (§101) ; les adresses de code restent PS2 en mémoire et sont
   converties à l'usage (§76).

**Banc MAME**
7. **`-state` en ligne de commande bloque** sur l'écran des sommes de contrôle → charger l'état depuis Lua (§110). Constaté le
   2026-10-04 : deux `mame … -state fin_tr` tournaient depuis 2 h 30.
8. **EEPROM partagée** : `~/.mame/nvram/sfa3ud` est réécrite à chaque sortie → dossier rendu non inscriptible, copie dans
   `~/.mame/nvram_sauvegarde/` (§81). À refaire pour `sfa3hx`.
9. **`pkill -f` / `pgrep -f`** avec un motif présent dans la ligne de commande du shell **tuent le shell** → `ps -C mame` (§110).
10. **Une prise Lua posée avant `banc_sprites.lua` voit la liste CONVERTIE** → lire `BANC_OMBRE` (§106).
11. `banc_mem.lua` doit être chargé dans **tout** script ponctuel, sinon l'exécution diverge (§75).
12. Une écriture relevée à « l'image N » a lieu pendant N+1 ; `-debug` décale le minutage ; les prises d'opcodes voient la
    prélecture (SP trompeur) ; `$700000` est en écriture seule (§67, §81, §82, §114).
13. Fusion d'entrées Lua par clé « port|champ » (un objet champ est recréé à chaque accès) (§81).
14. Start trop tôt = perdu par le menu de l'Anthology ; il faut un 2e Start pour valider un mode ; la ROM arcade demande
    2 pièces par crédit (§93, §101).
15. **`roms_tr` à reconstruire SANS `MAX_DEMO`** après une démonstration MAX (l'utilisateur a vu des défauts sur un build de démo).
16. Après chaque reconstruction, les adresses 68K bougent : relire `carte_image.txt` avant tout point d'arrêt.
17. Toujours relancer les **trois** diagnostics + les commandes (`nonreg.sh`) : un correctif peut passer l'un et casser l'autre (§98).
18. Garde-fou md5 de `sz3ud.03c` (`a851…`, §109) : **périmé** depuis les correctifs §110-§114 ; la référence est `nonreg.sh`.

**Données et méthode**
19. `sfa3_prog.bin` a des **données fausses** dans `$0-$BFFFF` (déchiffrées alors qu'elles sont lues brutes) → tables :
    `sfa3ud_prog.bin` (§96).
20. `anthology_extract/*_prog68k.*` contient du **MIPS**, pas du 68K (R§7).
21. Couverture : toujours en **union**, et distinguer « étendue » et « utilisable » (R§6bis, C2). Correspondances binaires :
    filtrer par entropie (R§7). Découpage MIPS par cibles de `jal`, jamais par `jr ra`.
22. Le scratchpad est vidé entre les sessions : rien d'important dedans (§25, §37).
23. Le disque `<disque externe>` est à plateaux : accès ciblés, jamais de `find` qui balaie.
24. Ne pas mettre de projet dans un chemin avec espace (« CLAUDE CODE » casse les Makefiles) → `<workspace>`.
25. États PCSX2 : les **copier** puis extraire (`eeMemory.bin`, `Scratchpad.bin`) ; la liste d'objets PS2 est dans le
    **scratchpad** (`0x70002000`), pas en RAM EE (§85, mémoire).

## 8. Ce qui est dépassé dans le journal (lire la correction)

| Ancien | Correction |
|---|---|
| R§1 : D0 = `0x1120`, `0x1158` = N | R§5 l.260 (D0 = `0x1124`), §11 (C), §53 (A8/D8) |
| R§5 : base `0x1f0008` ; couverture « 99 % », « 26,7 % » | §5 (`0x1f0000`) ; §1 (25,8 % réel), R§6bis (17,3 %), C2 (4,2 % utilisable) |
| R§5 : « MOVE #0 plutôt que CLR » | §37 : `CLR` émis (risque sur registres matériels non réévalué) |
| §24-§27 : disposition mémoire bloquante | §29 / §32 (recette cps2) ; §44 (typage) ; §69 (bus du fork) |
| §35 : routines « vidées » à restaurer | §47 : ce sont des RTS partagés |
| §38 : `DBRA` | §74 : `SUBQ.W ; BPL` |
| §45 / §48 : emplacement = X>>13 | §82 : bits 13-15 de Y |
| §82 → §83 : emplacements 6/7 | §102 : J3/J4 si la structure est active |
| §65 : décalages de plans `+$5600`/`+$B00` | §83 : tables `plan1`/`plan2`/`f312` |
| §84 : « zone dynamique » | §85 : `ADDI.L` perdu |
| §76 : dichotomie de conversion de code | §98 : hachage |
| §99 : `banc_palettes.lua` | §105 : inutile |
| §80 : le CPU ne combat pas ; §108 : fautes ro5 ; §112 : balayage vert | §81 ; §114 ; §113 (normal) |
| Mémoire : « Upper = NAOMI, pas CPS2 » | ro5 = 68K recompilé, lignée CPS2 (R§4, §28) |
