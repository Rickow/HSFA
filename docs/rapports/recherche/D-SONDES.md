# D — Sondes lancées dans le cœur (2026-10-20)

Premières mesures des protocoles des fiches [A](A-PERSOS-CACHES.md) et [B](B-REVISIONS-BUGS.md). Toutes ont été faites dans le
cœur FBNeo HSFA (patchs 1-11, frontal `tools/fbneo-hsfa/essais/joue_linux.c`). Outil du test CFC2 :
[`tools/sondes-recherche/`](../../../tools/sondes-recherche/README.md).

Constructions figées (règle 8 d'AGENTS.md ; md5) :

| Archive | Contenu | md5 |
|---|---|---|
| `sfa3uhsfa.zip` du 2026-10-18 20:26 | Upper + 4 persos MAX (`banc_max11`, son `agent_son_max`), `sz3ud.04c` `30c1473d…`, `hsfa_ext.bin` `8646fc3f…` | `e0a969d08b5e5576873e091da5971949` |
| `sfa3hhsfa.zip` du 2026-10-11 | Hyper | `514e42cb4ebfe583b530c5c880aade7a` |
| `sfa3.zip` | SFA3 d'arcade, Euro 980904 (FBNeo) | `68234a52029f4d823c91f8fdd5fa48d7` |
| `fbneo_hsfa_libretro.so` (Linux) | patchs 1-11 | `4551cd0c020307aa6cf9746e6a177c0e` |

Touches : depuis le patch 11 (`0007-HSFA-roulette-touche-piece`, §157), Select fait office de pièce et, sur la grille,
de roulette. Start sert aux EX et aux S-ISM. Les entrées des bancs n'appuient donc sur Start J2 qu'une fois, pour entrer
en jeu, **avant** la grille. Un Start tenu pendant la validation choisirait une version EX.

## 1. Hyper : modes et S-ISM (relecture de `tools/son-hyper/tournee_modes.tsv`)

- **Mazi = une manche.** Les 33 parties `.m1` (MAZI) s'arrêtent après une manche. Une manche perdue vaut défaite :
  c'est la règle du mode Mazi, pas un défaut (test 7 de la [synthèse](README.md)).
- **S-ISM rose (`.m6`, curseur 7)** : seuls 12 persos peuvent la prendre, les ID 00 01 04 0a 0b 0f 10 15 18 19 1c 20,
  c'est-à-dire la distribution de *SF2'*. Les 21 « pas_de_choix » du tableau sont donc attendus (A §9.4).
- **Bison en S-ISM rouge (`.m7`) contre NORMAL (`.m0`)** : sur `+$100-$1FF` de la structure de J2, seuls changent
  `$122` (00/02), `$123` (00/80) et `$15C` (00/80). Le super (charge, ←→← + PPP) montre la même image dans les deux
  cas. Côté son, un seul code diffère : `0302` en NORMAL, `0301` en S-ISM rouge. **Final Bison n'est pas confirmé** :
  il faut une comparaison avec le Final Bison d'arcade (test 3).

## 2. Test CFC2 sur Upper + MAX (fiche B §5.3, action 5)

La CFC2 (septembre 2025) a corrigé le Head Press et le Somersault Skull Diver de Bison, ainsi que la Sardine's Beach
Special de R. Mika, qui « ne touchaient pas » Eagle, Maki, Yun et Ingrid. Dans HSFA, les ID MAX sont `$26` Eagle,
`$27` Maki, `$2D` Yun et `$2E` Ingrid (§164).

**Protocole.** VERSUS, Bison (J1) contre l'adversaire (J2), persos forcés pendant la sélection, ISM par défaut du
jeu. Le geste part au début de la manche + 303 images, à la distance de départ (Bison en x `$220`, J2 en `$2E0`). On
lit la vie de J2 (`$FF8850`, 144 au départ) à 11 instants. Les manipulations viennent du guide (p. 228) :

- Head Press : bas chargé, haut + K ;
- Skull Diver : bas chargé, haut + P, puis P (avec ou sans direction).

### 2.1 Résultats

Dégâts sur J2 (0 = raté) :

| Jeu (ISM) | Ryu | Sakura `$0D` | Chun-Li | Juli | Eagle `$26` | Maki `$27` | Yun `$2D` | Ingrid `$2E` |
|---|---|---|---|---|---|---|---|---|
| Upper+MAX, Head Press (X) | 14 | 14 | — | — | 14 | 14 | 14 | 14 |
| Upper+MAX, Skull Diver (X) | 13 | **0** | 13 | 14 | 13 | 13 | 13 | **0** |
| Hyper Z3, Skull Diver (X) | 13 | 13 | 13 | 14 | — | — | — | — |
| Hyper Z3, Skull Diver (A) | 10 | 10 | 10 | 10 | — | — | — | — |
| Arcade SFA3, Skull Diver (A) | 10 | 10 | 10 | 10 | — | — | — | — |
| Arcade SFA3, Head Press (A) | 11 | 11 | 11 | 11 | — | — | — | — |

- **Roster complet d'Upper+MAX** (39 ID, Skull Diver) : il touche partout (12 à 14 points), sauf **Sakura et Ingrid**.
- **Variantes** : toutes les variantes du Skull Diver qui partent (second P à +30 images, avec →, ← ou sans
  direction, en LP, MP ou HP) donnent le même résultat. À +20 et +40, le second P ne part pas. Le Head Press suivi de ←/→ + P n'ajoute rien : la reprise ne part pas dans ce geste.
- **ISM** : sur Upper, les deux persos sont en X-ISM (octet `$133 = $FF`), sur l'arcade en A-ISM. En X-ISM, Hyper
  donne exactement les dégâts d'Upper. L'écart 13 contre 10 vient donc de l'ISM, pas d'un défaut.
- **R. Mika** : la Sardine's Beach Special est une super (↓↘→↓↘→ + K), il faut une jauge. Pas encore testée.

### 2.2 Ce qu'on en tire

1. **Le défaut de la CFC2 n'est pas reproduit pour le Head Press.** La table « mot selon l'ID adverse, 3 variantes »
   (PS2 `0x623E50`, arcade `$48DC0` 3 × 32, Upper 3 × 40) existe en deux copies :
   - une à 3 × 40 dans `sz3ud.04c`, vers `$BA190` ;
   - une étendue à **3 × 48** dans `hsfa_ext.bin` (à l'offset `0x481800`). Elle garde, pour `$28-$2C`, les valeurs
     qu'une lecture hors table rendait, et prend celles de Ryu pour `$2D-$2F`.

   C'est la copie étendue que lit le Head Press : y fausser l'entrée de Ryu le fait rater contre Ryu. Fausser la copie
   3 × 40 ne change rien. `tables_par_id.json` la range pourtant en `simple` (une rangée), alors qu'elle en a 3 : à
   corriger dans la liste, même si la construction est juste.
2. **Le Skull Diver rate Ingrid, mais aussi Sakura**, qui est d'origine. Hyper (même moteur, famille Z3) et l'arcade
   touchent Sakura. La trajectoire le montre :
   - dans Hyper, l'arc de Bison dépend de l'adversaire : contre Sakura, il est plus court et plus bas (x `$238` à
     +68, touche à +124) ;
   - dans Upper+MAX, l'arc contre Sakura est presque celui de Ryu (x `$23E` à +68). Bison passe trop haut et atterrit
     sans contact. Sur les captures contre Ingrid, la flamme du saut est rose au lieu de sa couleur normale.

   Ce n'est ni la table `0x623E50` ni la table « (dx, dy) selon l'ID adverse » (`0x622D10`) : fausser l'une ou l'autre
   copie de chacune ne change pas l'arc. La donnée par adversaire qui règle l'arc reste à trouver.
3. **Sakura est ratée aussi sans MAX.** Upper sans MAX (`sfa3uhsfa.zip` du 2026-10-07, `mame_ro5`, md5
   `043469a3c36eef58d031d35f95c72e1d`) donne le même résultat : Ryu 13, Sakura 0. Ce zip est **antérieur** à trois
   correctifs du traducteur :
   - `TAILBR` et `LUIDN` (§143, 2026-10-10) : boules de Sakura à « 42 coups », super boule d'Akuma ;
   - `PILE_LUI` (§162, v149).

   Le build Upper+MAX du 2026-10-18 (base v149) les contient tous, et rate pourtant Sakura de la même façon. Le raté ne
   vient donc pas de l'intégration MAX, et ces correctifs ne l'ont pas réglé : le correctif de Sakura portait sur
   **ses** projectiles, pas sur le plongeon de Bison contre elle. Reste une perte de traduction d'Upper, ou une vraie
   différence d'Upper sur PS2, à trancher par PCSX2 (Upper, Bison X-ISM contre Sakura). Ingrid a probablement la même
   cause. Piste : une constante ou une comparaison perdue de la même famille (`lui` seul, temporaire de pile) dans le
   calcul de l'arc.
   Pour un témoin sans MAX à jour, il faudrait le zip de `banc_ref` (v149).

### 2.3 Suite proposée

- PCSX2 : Upper, Bison X-ISM contre Sakura, même geste (oracle PS2) ; à défaut, le banc sur `banc_ref` (v149 sans MAX) ;
- au banc MAME, poser un point d'arrêt en lecture sur les tables par ID (`wp_*.lua` de `tools/integration-max/upper/lua`)
  pendant le Skull Diver contre Sakura et contre Ryu : la table qui rend des valeurs différentes est celle de l'arc ;
- R. Mika : remplir la jauge, puis Sardine's Beach Special contre les 4 MAX et Ryu ;
- ajouter Head Press / Skull Diver contre `$0D`, `$26`, `$27`, `$2D`, `$2E` à la non-régression (`nonreg_ro5_max.sh`).

## 3. Matrice des coups : Hyper Z3 contre SFA3 d'arcade

Outil : `tools/sondes-recherche/banc_matrice.py`. Chaque coup spécial, super ou lancer de SFA3 du tableau BradyGames
est joué par J1 contre Ryu immobile. Conditions : A-ISM des deux côtés, force H, jauge pleine (`+$21C = $1B0`), deux
distances (départ de manche, et 56 px). On compare les dégâts. Hyper : zip du 2026-10-11 ; arcade : `sfa3`, Euro
980904.

**Calage.** Le geste part au début de manche + 450 images. À + 303, l'intro de Karin dans Hyper n'avait pas fini : tous
ses coups tombaient pendant le « FIGHT » et comptaient faux. Le début de manche d'Hyper dépend aussi de la paire de
persos (trajet du curseur), donc il est mesuré par paire.

**Réserve.** L'Anthology propose SFA3 en 980629 et 980727, jamais en 980904 (fiche B §3). Une partie des écarts peut
donc venir de la révision, et non de la traduction. Pour trancher, il faut les ROM japonaises (980629, 980727).

### 3.1 Bilan

436 lignes SFA3 dans le tableau. 203 sont jouées (les autres sont des suites, des coups aériens ou des notations
libres), soit 406 essais par jeu :

- 226 donnent les mêmes dégâts ;
- 156 font 0 dans les deux jeux (geste trop simple, ou coup hors de portée) ;
- **24 diffèrent**. Les écarts sont **reproduits à l'identique** avec les calages + 303 et + 450, sauf deux (Rolento,
  Sagat Tiger Cannon).

### 3.2 Les écarts

| Classe | Coup (distance) | Hyper | Arcade | Ce qu'on voit |
|---|---|---|---|---|
| **plongeon raté** | Cammy, Killer Bee Assault (les deux) | 0 | 60 | la super part, Cammy plonge et manque Ryu ; à l'arcade, 4 coups. **Cause trouvée** : calcul d'angle mal traduit (§4) |
| **super qui ne part pas** | Dan, Hissho Burai Ken (près) | 17 | 64 | pas de flash dans Hyper ; les 17 viennent d'un coup normal. Rappelle `TAILBR` (§143) |
| **enchaînement coupé** | E. Honda, Fuji Oroshi (près) | 23 | 65 | la super part, le premier coup touche, la suite ne s'enchaîne pas (arcade : 5 coups) |
| | Sagat, Tiger Genocide (loin) | 17 | 33 | « 2 HIT » puis rien ; arcade : 6 coups |
| | Balrog, Crazy Buffalo (près) | 39 | 50 | à voir |
| | Balrog, Gigaton Blow (près) | 62 | 68 | à voir |
| **coups multiples, petit écart** | Cammy et Juli Spin Drive Smasher (loin), Guy Bushin Gorai Kyaku (loin), Ryu Shinku Hado Ken (loin), Sakura Midare Zakura (loin) | 28-45 | 37-51 | moins de coups dans Hyper, à distance |
| | Sakura Haru Ichiban (loin), Gen Shitenshu (près), Ryu Shinku Tatsumaki (près), Cammy et Juli Reverse Shaft Breaker (près) | 33-62 | 25-58 | **plus** de dégâts dans Hyper |
| **petit écart de dégâts** | Balrog Buffalo Head 16/15, Charlie Sonic Boom 4/5, Dhalsim Yoga Shock 3/6, Zangief Final Atomic Buster 17/18 | | | révision probable |
| **douteux (banc)** | Guy, Kubi Kudaki (près) | 0 | 12 | après le replacement, Guy et Ryu se chevauchent dans Hyper : position, pas coup |
| | Rolento, Fake Rod (près) ; Sagat, Tiger Cannon (loin) | | | change avec le calage |

### 3.3 Suite proposée

1. **ROM japonaises de SFA3** (980629, 980727) : relancer la matrice contre elles. Ce qui reste est de la traduction.
2. **Plongeons** : fait pour Cammy (§4 : aide `roxr`, `EXG` et `BCLR` perdus) ; Bison dans Upper a une autre cause
   (§4.5).
3. **Enchaînements coupés** (Honda, Sagat, Balrog) : compter les coups image par image (compteur de combo) et comparer
   la suite d'états de J1. Ce sont des candidats sérieux de perte de traduction.
4. **Dan** : vérifier sur PCSX2 que le Hissho Burai Ken part dans Hyper Z3, puis chercher un saut terminal perdu
   (même famille que `TAILBR`).
5. Banc : rendre le replacement « près » sûr (Guy). Ajouter les forces L et M, les suites, et Upper en A-ISM (il faut
   passer par le menu d'ISM d'Upper, l'octet seul ne suffit pas).

## 4. Killer Bee Assault de Cammy : la cause (Hyper, Upper)

Outils : `tools/sondes-recherche/` (sonde de PC du cœur, déchiffreur CPS2, désassembleur, recherche des paires, rustine
d'essai ; voir le README). Archives : Hyper du 2026-10-11 (image programme md5 `366f4ba1ea66f0093ef4c29ab049460c`),
Upper + MAX du 2026-10-18 (`07716def832278060a7219f5822f2924`), arcade `sfa3` 980904.

### 4.1 Ce qu'on voit

Cammy (A-ISM, jauge pleine) contre Ryu, trace image par image du bloc de J1 :

- les deux Cammy montent pareil, puis attendent en l'air (état `$10`, sous-état `$0A`) ;
- **arcade** : au départ du plongeon, l'angle vers Ryu (`+$3C`) vaut `$1D`, la vitesse `+$40` / `+$44` vaut
  (+4,6, −15,3) px par image. Cammy plonge et touche quatre fois (60) ;
- **Hyper** : l'angle vaut **0**, la vitesse (0, +16). Cammy remonte, retombe à la verticale et passe dans le sous-état
  `$16` (raté), que l'arcade n'atteint pas.

### 4.2 La fonction fautive

L'angle est calculé par la fonction arcade `$05DAEE` (Hyper `$4BA8E`, Upper `$67792`), appelée par `$05D24C` avec la
position de l'adversaire (pointeur `+$38`). Le résultat lit la table de vitesses `$05DBB4`. Dans les deux traductions,
la fonction a trois pertes :

| Arcade | Hyper (Upper identique) | Effet |
|---|---|---|
| `ROXR.B #1,D6` après chaque `SUB` (4 sites) : le bit X (signe de l'écart) entre dans D6 et choisit l'octant | `JSR $104E` (Upper `$1042`) : l'aide `roxr` du recompilateur, traduite comme une fonction ordinaire, dont il ne reste que des branchements | D6 reste à 0 : octant faux |
| `EXG D2,D3` (pente > 45°) | `MOVE.L D3,D2 ; MOVE.L D2,D3` : le temporaire est perdu, les deux registres valent \|dy\| | rapport 1, la fraction déborde (`ANDI #$1F` de `$20`) |
| `BCLR #0,D6 ; BNE` | `ANDI.L #-2,D6 ; BTST #0,D6` : le bit est testé après son effacement | le branchement n'est jamais pris |

**Preuve.** `rustine_angle.py` réécrit les trois pertes dans une copie de l'archive d'Hyper :

- Killer Bee Assault : 60 de dégâts aux deux distances (arcade 60) ;
- suite des angles **identique à l'arcade** : loin `$16`, `$33`, `$11` ; près `$1D`, `$02`, `$20`, `$38`. Les vitesses
  sont les mêmes, moitiés du long échangées ;
- les correctifs partiels donnent des angles faux qui touchent parfois par hasard. Exemple : `roxr` seul fait 60, mais
  avec les angles `$20`, `$13`, `$14`, 0 près de Ryu. Il faut les trois.

**Matrice complète refaite** (Hyper corrigé, 406 essais) : seules les deux lignes du Killer Bee Assault changent
(0 → 60). Aucune régression, il reste 22 écarts.

### 4.3 Déjà vu, mais pas dans le dépôt

L'index (`re/connaissances/sfa3_arcade.tsv`, `$05DAEE` ; `ro3.tsv`, `aide_recomp_roxr` 0x570AA0, `aide_recomp_sbcd`
0x570BB0 ; `ro9.tsv` 0x213500) note ces trois pertes sur SFA3. Il les dit réglées « à partir de v150 » par les règles
`EXG_PILE_D`, `AIDE_ROXR` et `BITOP_DN` (rapport `work/agent_defauts_banc/DEFAUTS-BANC.md` §4, hors dépôt). Pourtant :

- ces règles **ne sont pas dans `src/hsfa/`** (aucune occurrence dans `main`) ;
- `profils.py` ne connaît que 4 aides : `movem_push`, `movem_pop`, `andi_ccr`, `abcd` ;
- les archives d'Hyper et d'Upper en circulation ont le défaut.

Il faut verser ces règles dans le dépôt, puis reconstruire SFA3, Upper et Hyper, validation complète comprise.

### 4.4 Autres sites de la même famille

`paires_exg.py` cherche les paires `MOVE Dy,Dx ; MOVE Dx,Dy` (signature d'un `EXG` perdu ; 0 sur l'arcade) :

- **Hyper : 6 paires.**
  - `$4BAE2` : la fonction d'angle ;
  - `$45AC4` = arcade `$5850C` (`EXG D1,D0`, poussée de l'adversaire d'un pixel) ;
  - `$78546` et `$7854E` = arcade `$187DC` (deux `EXG`, valeur médiane de trois hauteurs `+$14`, moteur commun) ;
  - `$78588` = arcade `$18822` (`EXG D0,D1`) ;
  - `$80320` (`.W`) : pas d'homologue trouvé.

  Corrigées dans la rustine, ces quatre paires ne changent rien dans la matrice. Elles sont à revoir en 3-4 joueurs
  et sur les fins.
- **Upper : 20 paires**, dont 7 dans `$4C800`-`$4DCC0`.
- **Aide `roxr`** : seule la fonction d'angle l'appelle (4 appels dans chaque jeu).
- **Aide `sbcd`** (Upper `$104E`, 4 appels en `$592DC`) : l'arcade `$0A26C` y fait `SBCD -(A0),-(A1)` ×4 sur
  `$140` / `$13C(A6)`. Elle est notée réglée dans l'index, mais pas dans le dépôt.
- **Corps de l'aide `abcd`** (Upper `$1056` à `$226C8`, Hyper `$105A` à `$8B374`, 4 appels chacun, après
  `ANDI #$EF,CCR`) : quatre `ABCD` dont l'aide n'a pas été reconnue (arguments non suivis). Ce serait un ajout BCD qui
  ne fait rien. Non mesurable en VERSUS (le score ne bouge pas, arcade comprise) ; à vérifier en mode Arcade.

### 4.5 Bison contre Sakura dans Upper : autre cause

Dans Upper + MAX, le Skull Diver part avec les **mêmes vitesses** contre Ryu et contre Sakura, écrites par la même
routine (`$9849A`). Remplacer les 19 paires `.L` d'Upper par des `EXG` ne change rien (Ryu 13, Sakura 0, Ingrid 0). Le
raté vient d'ailleurs, peut-être du test de contact ou des boîtes de Sakura. Ce n'est ni un calcul de cible, ni cette
famille de pertes.

