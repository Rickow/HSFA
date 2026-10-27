# DECOR-CAMMY — plans manquants dans le décor de Cammy (Upper, ro5)

Dossier : `<workspace>/work/agent_decor_cammy/` (rien n'a été écrit ailleurs ; aucun commit). Base : constructions figées
`references/v149` (copiées dans `v149/`), traducteur `scripts/untranspile` à l'étiquette `v149` (worktree `untranspile/`).

## 1. Conclusion

- Le décor de Cammy est **`$100 = $2C`**. C'est un décor de SFA3, commun à SFA3 et à Upper : le moulin grec.
- Le plan manquant est **scroll2**, le plan du DESSUS (ordre CPS-B `$2D0E`). Il porte le moulin, la maison, les murets et
  le **sol pavé**. Scroll1 (ciel, mer) et scroll3 (chapelle, coupole) sont justes.
- Le défaut apparaît dès que le gestionnaire d'animation du moulin prend la main, vers l'image 20 de chaque manche. Il
  dure toute la manche.
- **Cause : une perte de traduction.** Le gestionnaire scroll2 du décor `$2C` (MIPS ro5 `0x155CE0`, image v149 `$02F060`)
  fait ceci :
  `MOVE.W T_614a60(PC,D0.W),D7 ; LSL.L #8,D7 ; ANDI.L #$00FFFFFF,D7 ; MOVE.L D7,$C134(A5)`.
  - `$C134(A5)` est la base scroll2, élargie par le portage (§58).
  - La table `T_614A60` contient des **adresses vidéo HÔTE PS2 décalées de 8** : `$A240` / `$A340` (Upper : RAM PS2 en
    `0xA00000`, vidéo en `+$20000`). Ce sont des données du module, que la traduction ne convertit pas.
  - La règle `VRAM_SHIFT` (§110) ne convertit que la forme à immédiat `MOVE.W #imm ; LSL.L #8`.
  - La base CPS-A valait donc `$A240` / `$A340` au lieu de `$9040` / `$9140` (arcade). `$A240` donne `$924000`, une zone
    sans le décor. `$A340` donne `$934000`, hors de la mémoire vidéo : au fork, MAME lit hors de son tableau et affiche
    un motif bruité (déjà noté par ZANGIEF.md). Dans FBNeo, on voit ce que l'utilisateur décrit : moulin, maison et
    sol absents.
- **SFA3 traduit a le même défaut** : même site (MIPS ro3 `0x111698`, table `T_58C2E0` = `$9240` / `$9340`). Hyper n'a pas
  de décor `$2C`. Ce site est le seul de cette forme dans ro3, ro5 et ro9 (recensement des `LSL.L #8` dans les trois
  `carte_image.txt`).
- Causes écartées :
  - **tuiles** : les tilemaps scroll2 sont bien écrites en `$904000` / `$914000`. `hsfa_plans.bin` et la ROM étendue sont
    justes, puisqu'une fois la base corrigée le rendu est identique à l'arcade.
  - **base de plan `$804200`** : `300,340,3a0`, inchangée.
  - **fichier non servi**, **table de décor incomplète** : non, le décor est entièrement présent avant l'image 20.

## 2. Reproduction (banc, copie v149)

- `lance.sh` lance le fork `sfa3hx` sur la copie `v149/ro5` (ou `W5=`), avec nvram et cfg propres et `nice -n 19`.
- `lua/decor.lua` force le décor par une prise sur `$FF8100`, posée à l'image 200 (sinon le test de RAM de l'arcade
  échoue). Il fait aussi :
  - les vidages et captures aux images listées dans `DUMPAT` ;
  - `ISO=1/2/3` (un plan seul), `ISO=9` (objets supprimés) ;
  - `REGS=n` : journal CPS-A/B toutes les n images ;
  - `LOCKCAM=1` : défilements figés, pour comparer au pixel.
- `lance_arcade.sh` lance l'arcade SFA3 d'origine (MAME 0.285, `sfa3.zip` en lecture seule, `REF=1`). C'est l'oracle :
  le décor `$2C` est commun.
- `lance_ro3.sh` lance SFA3 traduit (MAME standard).
- `py/regs.py` lit les registres vidés. Exemple de bases scroll2 relevées :
  - arcade : `9140 9140 … 9040 9040 … 9140` (Y = 0/100/200/300 : huit images d'animation du moulin) ;
  - v149 : `a340 … a240 … a340` ;
  - corrigé : `9140 … 9040 … 9140`, comme l'arcade.
- Captures :
  - `cap/avant_seq_2c.png` et `cap/apres_seq_2c.png` : une image sur huit, du début de la manche jusqu'à l'image 340 ;
  - `cap/comparaison_2c.png` : arcade, v149, corrigé ;
  - `cap/scroll2_2c_arcade_avant_apres.png` : scroll2 seul, arcade, v149, corrigé ;
  - `cap/iso_2c.png` : plans isolés ;
  - `cap/sfa3_2c_avant_apres.png` : SFA3 traduit.
- **PS2** : les sauvegardes PCSX2 ont été copiées dans `ps2/` (zip zstd, extraites par `py/p2s.py`). Aucune n'est dans le
  décor `$2C` d'Upper. L'état `etats_ps2/ancien_perfect_cammy` est SFA3 (module ro3, `$FF8100 = $2C`) et montre le même
  moulin que l'arcade. Le décor est le même dans les deux jeux (GREFFE-DECORS §1.3 : décors SFA3 d'Upper à 99,8-100 %
  dans e256 ; listes et gestionnaires homologues). L'export `decors_sfa3.psd` vaut donc pour `$2C`.

## 3. Correctif

### 3.1 Traducteur : règle `VRAM_TABLE`

Diff contre v149 : `diffs/traducteur_VRAM_TABLE.diff` (`translate.py` + une ligne de compteur dans `mame_test.py`).

- `vram_table_shift` reconnaît la forme `MOVE.W T(PC,Dx.W),Dn ; LSL.L #8,Dn ; ANDI.L #$00FFFFFF,Dn`.
- Gardes :
  - le 1er mot de la table, lu dans le module, décalé de 8, tombe dans la vidéo hôte `[base+$20000, base+$50000)` ;
  - l'instruction suivante ne lit pas X (MOVE ou SWAP) ;
  - aucune cible de branchement au milieu de la forme.
- Code ajouté après l'ANDI (22 octets), qui convertit à l'exécution et reste borné :
  `CMPI.L #lo,Dn ; BCS.S fin ; CMPI.L #hi,Dn ; BCC.S fin ; ADDI.L #(cps2 marqué − hôte),Dn ; fin: TST.L Dn`.
  - La constante vient de `addr_to_68k` : Upper `$00EE0000` (`$A24000` → `$01904000`), SFA3 `$00FE0000`.
  - Les valeurs hors de la vidéo restent inchangées.
  - `TST.L` rend N, Z, V et C comme l'ANDI. X est modifié seulement dans le cas converti, et l'instruction suivante ne le
    lit pas.
- Interrupteur : **`VRAM_TABLE=0` donne des constructions identiques à v149 à l'octet**. Contrôlé sur `sz3ud.03c` :
  ro3 `7e22b1ec…`, ro5 `7898814c…`, ro9 `cb9b37b9…` ; pour ro5, carte, chutes et blocs externes aussi.
- Avec `VRAM_TABLE=1` :
  - Upper `36fc4f37…` (`b_vt1/`) ; seuls changent `sz3ud.03c`, `04c`, `06c` et `10b`, les blocs externes ne bougent pas ;
  - SFA3 `6230bba0…` (`b_ro3_vt1/`) ;
  - **Hyper inchangé** (`cb9b37b9…`).
- Compteur : « adresses video formees par decalage d'un mot de table converties : 2 ». C'est un seul site, traduit deux
  fois, comme pour `VRAM_SHIFT`.

### 3.2 Chaîne graphique, banc, cœur

Rien à changer : `hsfa_gfx.py`, `hsfa_plans.py` et `banques.py` ne sont pas en cause. Le correctif est dans la ROM
programme. Pour FBNeo, il suffit de refaire `sfa3uhsfa.zip` (et `sfa3hsfa.zip` pour SFA3) avec les ROM corrigées ; le
cœur n'est pas à recompiler.

## 4. Vérifications

- **Banc Upper** :
  - les bases scroll2 suivent la même suite que l'arcade ;
  - scroll2 seul (moulin animé) est identique à l'arcade à l'œil ;
  - en balayage caméra figée, plans seuls, la corrélation de structure avec l'arcade est de 1,00 à l'image 60 et de 0,92
    à l'image 100. En v149, elle est de 0,21 et 0,20.
- **SFA3 traduit** : bases `9240/9340` avant, `9040/9140` après ; décor complet.
- **FBNeo** (cœur de référence `linux_hsfa_501aebd.so`, copié) :
  - les zips sont des copies de `livraison_v148/sfa3uhsfa.zip` où seules les 8 ROM programme sont remplacées (v149 /
    corrigé) ;
  - `fbneo/fb.sh` est une copie du `fb.sh` de l'agent rejeu, avec ses sorties dans mon dossier ;
  - `fbneo/hsfa_run` est recompilé avec `FORCE_DECOR` (diff `diffs/hsfa_run_force_decor.diff`) ;
  - la partie Arcade scriptée fait Ryu contre Cammy, en Grèce. En v149 : moulin, maison et sol absents, c'est le défaut
    signalé. Corrigé : décor complet (`cap/fbneo_2c_avant_apres.png`).
- **Non-régression du cœur** (scénario Upper de `nonreg_coeur.sh`, 9 000 images, même cœur, zip v149 puis zip corrigé) :
  - la RAM du jeu est identique jusqu'à l'image 3000, sauf `$FF4136` / `$FF414A` (la base scroll2 corrigée) ;
  - le flux est identique ;
  - le combat diverge à partir de l'image ≈ 3 600 (son, journal). La cause probable est la durée d'exécution du code
    ajouté, qui modifie un tirage au hasard (même effet que tout changement de ROM). Ce n'est pas un défaut du cœur.
- **Non fait** : la validation complète `valide_tout.sh` (≈ 1 h 15, qui écrit dans les dossiers partagés). Elle est à
  lancer avant intégration, à cause de l'effet du correctif sur le hasard.

## 5. Balayage des 40 décors (`$00-$4E`)

- Scripts :
  - `balayage.sh` : Zangief, décor forcé, objets supprimés, registres toutes les 2 images ; versions corrigé, v149 et
    arcade (`$00-$3E`) ;
  - `balayage_cam2.sh` : plans seuls, caméra figée, corrigé contre arcade.
- Planches, une capture par décor à l'image de combat 100 (`$20`, `$30`, `$32` : manche finie avant, case vide) :
  `cap/balayage_decors_fix.png`, `_v149.png`, `_arc.png`.
- Résultats : `tableau_decors.md` (produit par `py/tableau.py`). En résumé :
  - **Seul `$2C` avait un plan manquant de ce genre.** Pour les 32 décors SFA3, les bases s1/s2/s3, le contrôle des
    couches et les défilements à l'image 1 sont égaux à l'arcade (à l'exception de `$24`, ci-dessous).
  - Les décors propres à Upper (`$40-$4E`) ont des bases normales (`9000/9040/9080`) et des captures complètes. Il n'y a
    pas d'oracle arcade pour eux.
  - La corrélation de structure reste entre 0,76 et 1,00 hors `$2C` (v149) et `$24` / `$2E`. Les écarts viennent des
    animations (foules, éclairs, eau) et de la caméra (tuiles chargées selon la vraie caméra).
- Écarts relevés, qui ne sont pas des pertes de traduction :
  - **`$24`** (variante de Chun-Li, aucun perso n'y mène dans Upper) : scroll1 est décalé de `$80` en X. La valeur
    initiale vient de la table d'Upper `T_614600[$24] = $0040`, alors que `$08` vaut `$01C0` et que SFA3 traduit comme
    l'arcade partent de `$0180`. La lecture de la table est fidèle : c'est une donnée d'Upper, à confirmer sur PS2 si
    ce décor est atteint.
  - **`$2E`** (Evil Ryu, propre à Upper : grotte d'Akuma en bleu) : l'arcade force ici un autre décor. La comparaison ne
    s'applique pas.
  - La base du défilement de lignes (`$804108`) tourne sur quatre tampons avec un déphasage d'une image par rapport à
    l'arcade, dans tous les décors. Les images sont identiques : ce n'est pas un défaut.

## 6. Découvertes durables (pour AGENTS.md / l'index)

- Les données du module peuvent contenir des **adresses vidéo hôte décalées de 8** (mots), lues par `LSL.L #8`. Cette
  forme échappe à `VRAM_SHIFT` (§110) ; la règle `VRAM_TABLE` la corrige. Un seul site, dans ro3 et ro5 : le
  gestionnaire scroll2 du moulin de Cammy.
- `T_614A60` (ro5) / `T_58C2E0` (ro3) : animation scroll2 du décor `$2C`, entrées de 8 octets (base hôte >> 8, durée
  `$0C`, 0, Y). `$C134(A5)` (ro5) / `$BF34(A5)` (ro3) : base scroll2 élargie.
- `T_614600` (ro5) : X et Y initiaux de scroll1 par décor (4 octets par décor, indice `$100 × 2`). Upper diffère de SFA3
  pour `$24` (`$0040`).
- Méthode : forcer un décor sur l'arcade demande une prise sur `$FF8100` posée APRÈS le test de RAM du démarrage. Les
  images 1 à 20 d'une manche sont noires (fondu) : comparer à partir de l'image 25.
