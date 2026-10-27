# Cœur FBNeo : registre des plans pour ro9a (A), place 68K pour les données ajoutées (B)

Agent `agent_coeur_banques`, 2026-10-17. Dossier : `work/agent_coeur_banques/` (tout ce qui suit y est, sauf mention).

## Résumé

- **A** : le cœur sait jouer ro9a. Patch **0008** contre la branche `rejeu` (501aebd) et pilote d'essai `sfa3hahsfa`.
  - Non-régression : **IDENTIQUE** sur SFA3, Upper et Hyper.
  - Partie Arcade complète dans le cœur, jusqu'à la fin et une nouvelle partie.
  - Bascules de banque `$300 ↔ $400` aux mêmes images que le banc MAME.
  - Écrans identiques au banc, sauf l'adversaire tiré.
- **B** : voie recommandée, **les trous de la carte CPS2 68K servis en ROM**.
  - 7 plages, **5,08 Mo**, soit presque autant que les 5,75 Mo des blocs externes actuels. Aucun cycle de plus.
  - Le banc MAME actuel les sert déjà, sans recompilation, par `banc_mem.lua`.
  - Prototype dans le cœur (patch **0009**, membre facultatif `hsfa_trous.bin`) et dans une copie du fork
    (`HSFA_TROUS`), validé. Sans le membre ou la variable, tout est identique à l'octet.
  - La banque commutée (voie 2) est chiffrée et gardée pour plus tard : décors en masse, au-delà d'environ 5 Mo.

## A. Registre des plans `$804200-$804205` dans le cœur

### A.1 Constat de départ

Le patch 1 (`fbneo-hsfa.patch`, `cps_hsfa.cpp`) contenait déjà, en mode 2 (Upper, Hyper) :

- les 3 registres (`nPlaneReg`), en lecture et en écriture par octet ;
- `nCpsGfxScroll[k] = base << 16`, avec 0 qui redonne `0x800000`, le mappage d'origine du CPS2 dans FBNeo ;
- la remise à 0 au reset ;
- l'état sauvegardé (`SCAN_VAR`).

Le code de tuile local se calcule comme dans le fork : `(base << 16) / taille + code`, avec `t << 6/7/9` dans
`Cps2Scr1Draw`, `cpsrd.cpp` et `Cps2Scr3Draw`, sans mapper CPS-B pour CPS2. Scroll3 est masqué à 14 bits comme dans MAME.

**Ce qui manquait pour ro9a : la taille de la ROM graphique.**

- La région faisait 64 Mo, soit `$4000000` octets.
- Les bases `$400/$440/$4A0` des écrans d'Upper tombent donc à la fin de la région. Le masque d'adresse
  (`nCpsGfxMask = $3FFFFFF`) les ramène sur `$0`, ce qui affiche les tuiles de SFA3 à la place.
- Le pilote Hyper ne déclarait par ailleurs qu'un `hsfa_gfx.bin` de 32 Mo (`$2000000-$3FFFFFF`).

### A.2 Patch 0008 (`0008-HSFA-registres-des-plans-ro9a-pilote-sfa3hahsfa.patch`)

| point de la spécification (GREFFE-ETAPE4 §7) | réalisation |
|---|---|
| 3 mots R/W, écritures 16 bits avec masque | `HsfaPlaneWrite(k, d, masque)` ; l'écriture de mot est traitée en une fois (`HsfaPortWriteWord`, appelé par `CpsWriteWord`), et l'écriture d'octet garde son masque `$FF00/$00FF` ; la lecture renvoie la dernière valeur |
| 0 = mappage d'origine ; sinon base en unités de 64 Ko, code local | inchangé (A.1) |
| `mark_all_dirty` à chaque changement | FBNeo n'a **pas de cache de tuiles** : il redessine les plans à chaque image depuis `nCpsGfxScroll`. Seul un **changement** de valeur met `nCpsGfxScroll` à jour, ce qui est l'équivalent exact |
| remise à 0 au reset, état sauvegardé | inchangés. Essai `STATETEST=700` (sauvegarde pendant les écrans d'Upper, base `$400`) : image finale **IDENTIQUE** |
| ROM graphique ≥ `$4000000` + taille de `hsfa_plans.bin` d'Upper | `HsfaGfxLenMin()` = `$2000000` + taille **déclarée** de `hsfa_gfx.bin`, et 64 Mo au moins. Upper et Hyper restent à 64 Mo. ro9a : `hsfa_gfx.bin` de 48 Mo, région de **80 Mo** (`$4000000` + 12,8 Mo d'Upper = `$4C3C000` ≤ `$5000000`). Les bornes `nCpstTile < nCpsGfxLen` existaient déjà dans `cpst.cpp` |
| — | `hsfa_gfx.bin` est chargée et convertie **sur place** : plus de tampon temporaire de 32 ou 48 Mo au démarrage, utile pour Android |
| — | journal d'essai `HSFA_PLANS_LOG=<fichier>` : une ligne « image : s1 s2 s3 » à chaque changement |
| — | pilote **`sfa3hahsfa`**, « Hyper Street Fighter Alpha + Arcade (HSFA, essai ro9a) » : fichiers d'Hyper, `hsfa_gfx.bin` de `0x3000000`. Quand ro9a remplacera Hyper, il suffira de passer cette taille dans `Sfa3hhsfaRomDesc` |
| — | `hsfa_run` : `PILOTE=arcade`, portage de `greffe_arcade/lua/tournee_arcade.lua`. Variables `PERSO`, `GRAINE`, `SNAPETAT`, `SNAPSC`, `NOCONT`, `SCENEA_PASSIF`, `BLOCAGE`, `LISTE_ADV`, `FORCE_LISTE`, `GRAINE_SEL` ; journal au format du script, lignes `LISTE` en plus |

Le patch s'applique sur `rejeu` et par-dessus le `hsfa_run.c` non validé de `agent_fbneo_rejeu` (vérifié par
`git apply --check`). Les fichiers générés (`gamelist.txt`, `driverlist.h`) sont exclus : il faut `REGEN_HEADERS=1`,
comme pour les patchs 4 à 11. Le cœur 16:9 (`-DHSFA_WS`) partage `d_cps2.cpp`, mais n'a pas été compilé.

### A.3 Validation

- **Non-régression** (`tests/nonreg_coeur.sh`, copie de `scripts/validation/nonreg_coeur.sh` avec les sorties
  dans ce dossier, zips `livraison_v148`, référence `linux_hsfa_501aebd.so`) : `sfa3`, `upper` et `hyper` sont
  **IDENTIQUE** (30, 30 et 40 captures, journaux, son). Même résultat avec 0008 + 0009 (`tests/nonreg_0009a.txt`).
- **Zip ro9a** : `zips/sfa3hahsfa.zip`, 50,6 Mo, déterministe (`SOURCE_DATE_EPOCH=1792000000`).
  - Construit par `outils/fbneo-hsfa/paquet_fbneo.py ro9a`, qui ajoute l'entrée `ro9a` (diff
    `outils/fbneo-hsfa/paquet_fbneo-ro9a.diff`) :
    - construction `greffe_arcade/constructions/ro9a4_fige` (ROM, `b9/ext_*`, `banques_hx`) ;
    - réglages de `lance_ro9a.sh` ;
    - plans d'Hyper en `$3000000`, plans d'Upper en `$4000000`.
  - Options : `HSFA_SANS_FLUX=1` (pas d'ISO dans l'essai) ; `HSFA_VOIX_ARCADE=0` et `HSFA_CRIS_ARCADE=0`, pour comparer
    au banc, qui ne les applique pas. Les corrections de voix d'Hyper n'ont pas été vérifiées sur ro9a.
- **Partie Arcade dans le cœur** (`tests/fa.sh`, Ryu ZERO 3, 20 000 images, environ 21 s) :
  - 21 manches sur les 10 étapes, puis la fin (A5+4 = A), le GAME OVER / classement (8), la sortie (C) et une
    nouvelle partie ;
  - le banc MAME (`mame/ma.sh`, binaire partagé, même script) en fait 22.
- **Bascules de banque** (`HSFA_PLANS_LOG` dans le cœur, prise d'écriture Lua `mame/lua/plans_arcade.lua` au banc) :
  - même suite de valeurs : `300/340/3a0` → `400/440/4a0` → `300/…` ;
  - aux mêmes images au début : 619/620 et 864/865 ;
  - ensuite, l'écart suit la durée des combats.
- **Captures** :
  - `captures/vs_ro9a_mame_coeur.png` (images 640-863, MAME | cœur | différence) ;
  - `captures/c1/etat_*.png` (36 états appariés, 11 identiques au pixel).
  - Résultats :
    - écrans d'Upper (base `$400`) : **identiques** au banc, sauf les objets liés à l'adversaire (1 à 6 %) ;
    - écran VS : même décor et même portrait de J1, adversaire différent (Sodom au banc, Dan dans le cœur) ;
    - flash blanc de la transition décalé d'une image (image 855) ;
    - retour au décor de combat (`$300`) identique.
  - Le fond « en mosaïque rouge » des écrans d'Upper est **le même dans le banc et dans le cœur**. C'est le défaut
    connu de la greffe (planisphère, GREFFE-ETAPE4 §6), pas un défaut du cœur.
- **Adversaires différents** : la liste `$FF4B2E` est tirée à la même image (619) des deux côtés, mais elle diffère
  même avec la graine `$FF80AE` imposée à chaque image de la sélection (`GRAINE_SEL`, `mame/lua/graine_sel.lua`).
  - Le tirage dépend d'autre chose que de la graine (nombre d'appels au hasard dans l'image) ; seul `graine_pc.lua`
    (prise sur le PC) la fixe.
  - Imposer `$FF4B2E` (`FORCE_LISTE`) ne change pas les adversaires : la liste n'est pas relue à chaque étape.
  - Pour une comparaison au pixel, il faudrait une prise PC dans le cœur (option d'essai), non faite.
- Observation hors sujet : après restauration d'un état, le son diffère dans `STATETEST`. C'est **déjà le cas avec le
  cœur de référence sur Hyper** (même nombre d'échantillons différents), donc ce n'est pas une régression.

## B. Place 68K pour les données ajoutées

### B.0 Où en est la carte

- **ROM programme `$000000-$3FFFFF` : pleine.**
  - Fin occupée en `$3FF176` (CODECONV) dans ro3, ro5, ro9 et ro9a.
  - Aucun bloc nul de 64 Ko ; 26 Ko de zéros au total dans ro9a.
  - Le fork n'exécute du code que dans cette plage (opcodes) : le **code** ajouté (MAX) ne peut aller qu'ici.
- **Blocs externes `$940000-$EFFFFF`** (5,75 Mo, `hsfa_ext.bin`) : saturés dans ro9a. Marge d'environ 28 Ko
  (`$C31F00-$C37FFF`, `$C7D11C-$C83FFF`).
- **PORT_RAM `$F00000-…`**, la RAM propre au portage selon le traducteur, n'est **mappée ni dans le fork ni dans le
  cœur** : les écritures sont perdues et les lectures rendent 0.
  - Mesure (prise MAME, partie Arcade ro9a de 20 000 images) : seuls `$F00308-$F0030B` sont écrits (une fois par
    image, PC `$B290`) et `$F002F8-$F002FB` lus (2 fois, PC `$FB62`). Le portage s'accommode donc de 0.
  - Étendue calculée (mot 6 de l'en-tête, `ram_hi_of`) :
    - variables : ro3 `$F00000-$F738FF`, ro5 `$F00000-$F5FE7F`, ro9/ro9a `$F00000-$F18DFF` ;
    - images de la RAM PS2 (+`$50000` et +`$62000`) : `$F80000-$F8FFFF` et `$F92000-$FAFFFF`.
  - Tout ce qui suit **`$FB0000`** n'est la cible de rien.
  - La ligne `ram68k $F00000-$FEFFFF` de l'index (« fin non déterminée ») peut être raccourcie à `$FAFFFF`.

### B.1 Voie 1 : trous de la carte CPS2 servis en ROM (RECOMMANDÉE, prototypée)

Recensement sur `dead_cps2_map` + `hsfa_map` (fork MAME) et sur `cps_mem.cpp` / `cps_rw.cpp` (cœur). Une plage
n'est retenue que si elle est libre **des deux côtés**.

| trou | plage | taille | bornes gardées |
|---|---|---|---|
| T1 | `$410000-$617FFF` | 2 080 Ko | `$400000-$40000F` registres d'objets (le cœur prend `$400000-$40000F`) ; `$618000-$619FFF` RAM partagée QSound |
| T2 | `$61A000-$65FFFF` | 280 Ko | `$620000` n'existe que dans `cps2_comm_map` (pas dans le fork) |
| T3 | `$668000-$6FFFFF` | 608 Ko | `$660000-$663FFF` piles du portage, `$664001` ; le cœur traite `$660000-$667FFF` |
| T4 | `$710000-$7FFFFF` | 960 Ko | mémoire d'objets `$700000-$70FFFF` (miroirs compris) |
| T5 | `$810000-$8FFFFF` | 960 Ko | ports `$800000-$807FFF` (miroir du cœur), registres HSFA `$804200` ; `$808000-$80FFFF` gardé pour de futurs registres |
| T6 | `$930000-$93FFFF` | 64 Ko | vidéo `$900000-$92FFFF`, blocs externes à partir de `$940000` |
| T7 | `$FB0000-$FEFFFF` | 256 Ko | PORT_RAM et images CONV jusqu'à `$FAFFFF` ; RAM de travail `$FF0000` |
| **total** | | **5 208 Ko (5,08 Mo)** | ro9/ro9a seulement, en plus : `$F20000-$F7FFFF` (384 Ko, au-delà de leurs variables) |

Mesure : **aucune lecture ni écriture** dans T1 à T6, ni dans `$F00000-$FEFFFF` hors `$F002F8-$F0030B`, pendant une
partie Arcade complète de ro9a (`mame/trous_ro9a.txt`, `mame/trous_f_ro9a.txt`).

Le recensement statique des longs `$F1xxxx-$FExxxx` dans la ROM programme ne montre que du bruit, environ 100 par
64 Ko ; seule la page `$F00000` sort du lot (`outils/rom68k.py`).

**Coût en cycles : nul.** Ce sont des lectures ROM directes, comme les blocs externes : pages `MAP_READ|MAP_FETCH`
dans le cœur, `install_rom` dans le fork.

**Accès depuis le code traduit ou greffé** : le même mécanisme que les fenêtres de la greffe (`GRF_FEN`,
`HSFA_GREFFE_FEN`). Un morceau PS2 libre de `lui` est projeté sur un trou. La routine `CONV` (dichotomie,
`kernel68k.build_conv`) gagne une plage par trou utilisé : un niveau de comparaison, environ 24 cycles, par
doublement du nombre de plages, et environ 18 octets dans `$400-$7FF`.

Deux règles :

- **Les pointeurs 68K vers un trou doivent porter l'étiquette `$01xxxxxx`**, comme ceux des blocs externes
  (`HW_TAG`, `TG` de `mame_test.py`). Le 68000 l'ignore (bus de 24 bits), et `CONV` ne la confond pas avec une
  adresse PS2. Sans étiquette, `$4xxxxx-$8xxxxx` (module PS2 `$1F0000-$B67200`), `$930000` (RAM PS2) et `$FBxxxx`
  (morceau PS2 `$F74000-$FBFFFF` de la greffe) seraient reconvertis à tort.
- Les morceaux PS2 choisis pour ces données doivent éviter `$01000000-$01FFFFFF`, l'espace des étiquettes.

**Côté outils :**

- les blocs se livrent comme aujourd'hui : `ext_<adresse>.bin` plus une ligne dans `ext_liste.txt` ;
- banc MAME (binaire partagé, Lua) : `banc_mem.lua` / `banc_mem_liste.lua` les servent déjà par prise de lecture.
  Vérifié : les blocs témoins sont relus dans les 7 trous, et la partie est identique au banc ordinaire (journal,
  plans) ;
- cœur : `paquet_fbneo.py` (copie) range dans `hsfa_trous.bin` les blocs qui tombent dans un trou (`trous=True` dans
  `JEUX`). Il n'ajoute le membre que s'il sert : sans bloc dans un trou, le zip est identique à l'octet (md5).

**Prototypes, sans effet sur les jeux actuels :**

- **Cœur, patch 0009** (`0009-HSFA-prototype-trous-de-la-carte-68K-en-ROM.patch`, sur 0008) :
  - membre `hsfa_trous.bin` facultatif (`BRF_OPT`, `0x516000` octets, les 7 trous bout à bout, mots échangés),
    déclaré par `sfa3hahsfa` seul ;
  - projeté seulement s'il est présent ; sinon, rien n'est projeté.
  - Essai (`essai_trous/b9` = ro9a4_fige + 8 blocs témoins, `zips/trous/sfa3hahsfa.zip`) : le cœur relit `CA0n … BE07`
    en tête et en fin des trous.
  - Partie Arcade de 20 000 images avec et sans le membre : journal, plans et 102 captures **identiques**, et
    identiques au cœur 0008. Non-régression SFA3, Upper et Hyper : IDENTIQUE.
- **Fork MAME** (copie `mame-fork/mame`, recompilée en incrémental ; binaire `mame-fork/cps2f_trous` ; diff
  `mame-fork/trous-sur-fork.patch`, 51 lignes, contre le `cps2.cpp` du fork) :
  - `HSFA_TROUS=<dossier>` remplit les 7 trous depuis les `ext_<adresse>.bin` de `ext_liste.txt` (`install_rom`) ;
  - sans la variable, rien n'est installé.
  - Essai : sonde Lua à l'image 10 = signatures avec `HSFA_TROUS`, 0 sans. Journal, plans et captures identiques au
    binaire partagé dans les deux cas.

Limites :

- pas de code dans les trous (le fork n'exécute que `$0-$3FFFFF`) ;
- les trous sont morcelés : le plus grand fait 2 Mo, il faut couper les blocs ;
- `hsfa_trous.bin` ajoute 5,1 Mo de RAM sur la machine, seulement pour les jeux qui le contiennent.

### B.2 Voie 2 : banque de données commutée (chiffrée, non prototypée)

- **Principe** :
  - une fenêtre fixe, par exemple **`$710000-$7FFFFF`** (960 Ko, T4) ou `$500000-$5FFFFF` dans T1 ;
  - un registre **`$804210`** (mot, lecture/écriture) donne la page dans un fichier `hsfa_banque.bin` (cœur) ou une
    région (fork) ;
  - 0 = fenêtre vide ;
  - état sauvegardé, remise à 0 au reset.
- **Fork** : `memory_bank` (`bankr`) ; changer de page coûte un `set_entry`, en temps constant.
- **Cœur** : `SekMapMemory` de la fenêtre à chaque changement. Pour 960 pages de 1 Ko × 2 (lecture, exécution),
  environ 1-2 µs ; à rappeler après un chargement d'état.
- **Coût 68K** :

  | opération | cycles |
  |---|---|
  | `MOVE.W #page,$804210.L` | 20 |
  | sauvegarde imbriquée `MOVE.W $804210.L,-(SP)` | 20 |
  | restauration `MOVE.W (SP)+,$804210.L` | 20 |
  | accès encadré (sauvegarde, choix, restauration) | 60, soit 0,03 % d'une image de 11,8 MHz / 59,6 Hz (≈ 198 000 cycles) |

  - Une page fixée **par contexte** (chargement du décor, entrée d'un écran d'Upper, d'une fin) coûte 20 cycles par
    combat : négligeable.
  - Un encadrement **par accès** (100 par image) coûte environ 3 % d'une image.
- **Accès depuis le code traduit ou greffé** : un pointeur vers la banque est une adresse de la fenêtre. Il n'a de
  sens que si la bonne page est en place. `CONV` ne peut pas choisir la page (plusieurs morceaux PS2 sur la même
  fenêtre), et une page posée dans `CONV` serait un effet de bord dangereux. Donc :
  - ne mettre en banque que des données **lues dans un contexte délimité** : le décor d'un combat (tables, code de
    décor greffé, palettes de plan), les données d'un écran d'Upper ou d'une fin ;
  - **talons** greffés à l'entrée de ces contextes, par exemple le crochet `$174` du choix du décor
    (GREFFE-DECORS) ou l'entrée des écrans d'Upper : `MOVE.W #page,$804210.L` (8 octets), puis retour au code ;
  - l'IRQ ne doit lire que des données hors banque, ou de la page du contexte en cours ;
  - pointeurs étiquetés `$01xxxxxx` comme en B.1 ;
  - une table « contexte → page » produite par l'outil de placement.
- **À éviter** : les données de persos (MAX). J1 et J2 sont actifs en même temps et leurs pointeurs sont absolus,
  donc une fenêtre unique ne convient pas.
- **Capacité** : illimitée (taille du fichier), par pages de 960 Ko à 1 Mo.

### B.3 Autres voies

1. **Données mortes** (recensement de l'agent de la greffe) : fins, textes et carte d'Hyper dans `ext_940000`
   (3 Mo). Il faut les journaux de lecture VERSUS, TRAINING et attraction comme preuve.
2. **Régions communes Upper/Hyper** : environ 134 Ko, dont 108 Ko avec pointeurs masqués (GREFFE-ETAPE4 §3) ; peu
   de gain.
3. **Libérer la ROM programme pour le code** : seule zone exécutable, elle compte pour MAX.
   - Les données du module dans l'image (`DATA_BASE $B2000-$37DEFF` dans ro9a, environ 2,8 Mo) peuvent partir dans
     les trous (B.1) et laisser la place au code.
   - `CODECONV_DICHO=1` supprime la table de hachage `$3C0000-$3DFFFF` (128 Ko) ; coût : une recherche dichotomique
     à chaque conversion de pointeur de code.
4. **`$F20000-$F7FFFF`** (384 Ko), pour ro9/ro9a seulement : au-delà de leurs variables PORT_RAM (`$F18DFF`).
5. Au-delà de 16 Mo : impossible (bus de 24 bits ; les bits hauts servent d'étiquette).

### B.4 Recommandation

1. **Maintenant : voie 1.**
   - Elle donne +5,08 Mo de données à coût nul, presque le double de l'espace externe actuel. Le banc la sert déjà,
     et le cœur et le fork ont un prototype à interrupteur.
   - Pour l'intégrer : passer 0009 dans la chaîne et `HSFA_TROUS` dans le fork, les deux à faire valider ;
     ajouter les plages aux fenêtres de la greffe (`HSFA_GREFFE_FEN`) avec l'étiquette `$01`.
   - Ordre conseillé :
     - décors d'Upper (environ 200-400 Ko de tables et de code de décor) en T4/T5 ;
     - tables des décors SFA2 (424 Ko de bibliothèques et 62 Ko de tables pour les premiers) et SFA1 en T1 ;
     - données des persos MAX en T1, leur code dans la ROM programme libérée (B.3, point 3).
2. **Ensuite, au besoin, voie 2** pour les décors en masse : une page par décor, posée au chargement du combat. Elle
   ne devient utile qu'au-delà d'environ 5 Mo de données ajoutées.
3. **En parallèle, voie 3** : données mortes d'Hyper, et ROM programme réservée au code.

### B.5 Réservations proposées pour `re/allocations.tsv` (non écrites dans le dépôt)

Vérifiées sur une copie (`re_copie/`) : `zones.py --verifie` ne signale **aucun conflit nouveau** (23 avant, 23 après).
T7 recouvre volontairement la ligne `ram68k $F00000-$FEFFFF`, à raccourcir à `$FAFFFF` (B.0).

```
trous68k	$410000	$617FFF	trous de la carte 68K (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B ; patch 0009 (prototype)	trou T1 (2 080 Ko) servi en ROM par hsfa_trous.bin (cœur) / HSFA_TROUS ou ext_<adresse>.bin (fork, banc) ; jamais accédé (taps, partie Arcade ro9a) ; pointeurs étiquetés $01xxxxxx (plages PS2 de CONV)
trous68k	$61A000	$65FFFF	trous de la carte 68K (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B ; patch 0009 (prototype)	trou T2 (280 Ko), après la RAM partagée QSound
trous68k	$668000	$6FFFFF	trous de la carte 68K (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B ; patch 0009 (prototype)	trou T3 (608 Ko) ; $660000-$667FFF restent au matériel (piles, $664001)
trous68k	$710000	$7FFFFF	trous de la carte 68K (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B ; patch 0009 (prototype)	trou T4 (960 Ko), après la mémoire d'objets et ses miroirs
trous68k	$810000	$8FFFFF	trous de la carte 68K (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B ; patch 0009 (prototype)	trou T5 (960 Ko) ; $800000-$80FFFF restent aux ports et registres ($804200, futur $804210)
trous68k	$930000	$93FFFF	trous de la carte 68K (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B ; patch 0009 (prototype)	trou T6 (64 Ko), entre la mémoire vidéo et les blocs externes
trous68k	$FB0000	$FEFFFF	trous de la carte 68K (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B ; patch 0009 (prototype)	trou T7 (256 Ko) : au-delà de toutes les cibles de PORT_RAM et de CONV (ro3 $F738FF, images RAM PS2 $F80000-$F8FFFF / $F92000-$FAFFFF) ; DANS la ligne ram68k PORT_RAM $F00000-$FEFFFF, à raccourcir
materiel_cps2	$804210	$804211	banque de données commutée (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B.2	registre de page PROPOSÉ (voie 2, non prototypée)
materiel_cps2	$808000	$80FFFF	registres du fork / cœur (agent_coeur_banques)	réservé	work/agent_coeur_banques/COEUR-BANQUES.md §B.1	gardé hors trous pour de futurs registres (le cœur mire les ports jusqu'à $807FFF)
```

Mise à jour proposée de la ligne `ram68k $F00000-$FEFFFF` (PORT_RAM) : « fin réelle : ro3 `$F738FF`, ro5 `$F5FE7F`,
ro9/ro9a `$F18DFF` ; images RAM PS2 `$F80000-$F8FFFF`, `$F92000-$FAFFFF` ; non mappée dans le fork ni dans le
cœur ; ro9a Arcade n'y accède qu'en `$F002F8-$F0030B` ».

## Fichiers

| chemin | contenu |
|---|---|
| `0008-HSFA-registres-des-plans-ro9a-pilote-sfa3hahsfa.patch` | patch A (contre `rejeu` 501aebd, `git am`) |
| `0009-HSFA-prototype-trous-de-la-carte-68K-en-ROM.patch` | prototype B.1, cœur (sur 0008) |
| `mame-fork/trous-sur-fork.patch`, `mame-fork/cps2f_trous` | prototype B.1, fork (copie) |
| `coeurs/linux_hsfa_0008a.so`, `coeurs/linux_hsfa_0009a.so` | cœurs Linux de test |
| `zips/sfa3hahsfa.zip`, `zips/trous/sfa3hahsfa.zip` | zip ro9a, et zip d'essai avec blocs témoins |
| `outils/fbneo-hsfa/paquet_fbneo.py` (+ `paquet_fbneo-ro9a.diff`) | entrée `ro9a`, `gfx_len`, `trous` |
| `tests/fa.sh`, `tests/hsfa_run`, `tests/nonreg_coeur.sh`, `tests/fb.sh` | partie Arcade dans le cœur, non-régression |
| `mame/ma.sh`, `mame/lua/*.lua` | partie Arcade au banc, journaux des plans, sondes des trous |
| `outils/compare_etats.py`, `outils/compare_images.py`, `outils/rom68k.py` | comparaisons et recensement |
| `captures/` | planches MAME / cœur |
| `fbneo/` (clone, 2 commits locaux), `mame-fork/mame/` (copie) | arbres de travail |
