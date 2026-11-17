# Greffe Arcade : construction depuis l'ISO (jeu `hyperarcade` de `hsfa_build.py`)

**ro9a45** (16/11/2026 ; construit par défaut depuis le 16/11 au soir : `HA_RECETTE = "vars_ro9a45.txt"`, code et relevés
de ro9a41, construction `ro9a45_fige`) : recette `ro9a41/greffe/vars_ro9a45.txt` = `vars_ro9a44.txt` + `DONNEES_BRUTES=1`
(détail et mesures : paragraphe « ro9a45 » ci-dessous, §243). Programme `sz3ud.03c` `37799f69…` (= ro9a44) ; seules les
données changent (235 octets dans `ext_4e8000.bin`, `ext_c70000.bin`, `ext_d0c000.bin` et le module).

**ro9a44** (16/11/2026 ; construit par défaut du 16/11 après-midi au 16/11 soir : `HA_RECETTE = "vars_ro9a44.txt"`, code
et relevés de ro9a41, construction `ro9a44_fige`) :
recette `ro9a41/greffe/vars_ro9a44.txt` = `vars_ro9a44_generique.txt` + `MENU_CURSEUR_ARCADE=1 PORT_COULEUR=1`
(`PORT_COULEUR_SEL_VERSION` reste à 0), soit ro9a43 + les fins (étape ro9a44_fins ci-dessous), le budget du générique
(variante ro9a44_generique), le menu sur ARCADE (candidat ro9a43_menu) et les portraits V1b (candidat ro9a43_portraits).
Programme `sz3ud.03c` `37799f69…`, `sz3ud.04c` `f818fa11…`. Contre `vars_ro9a44_generique.txt` (même code) : 1 octet du
module (menu), 1 octet de `sz3ud.03c` (`$010126`), les 4 retouches des portraits dans `sz3ud.04c` et le talon de 20 o en
`$37FF94` (`sz3.09c`), rien d'autre (blocs, banques, bloc de données identiques) ; les trois interrupteurs trouvent leurs
sites par va (assertions d'octets), les sites des portraits tombent aux mêmes adresses d'image que sur ro9a43 (sous la
plage décalée par `GENERIQUE_BUDGET`). Mesures (`<workspace>/work/ro9a44/ETAT.md`) : VERSUS (Lua du menu) : `vs.log`
identique à ro9a43, 90 / 90 captures = portraits seuls, 70 / 90 contre ro9a43 (les 20 VS des paires ZERO 3) ; TRAINING :
`vs.log` identique ; partie Arcade par Start, Start : dialogue au 5e combat et primes ; 40 décors : journaux et 160
captures = ro9a44_generique ; 85 fins : journaux, sondes et 9 547 / 9 547 captures = ro9a44_generique (seule la ligne
de sentinelle de l'image 337, le menu, change) ; contre ro9a43 : 7 940 identiques, 1 002 plus proches d'Upper, 259 plus
loin (générique d'un tic, explosions au hasard de 04).

**ro9a45** (16/11/2026, candidat retenu le 16/11 au soir : `HA_RECETTE = "vars_ro9a45.txt"`) : recette
`ro9a41/greffe/vars_ro9a45.txt` = `vars_ro9a44.txt` + `DONNEES_BRUTES=1` (`ro9a41/greffe/etape2/donnees2.py`). La classe
« ram » du relogement des données copiées d'Upper prenait pour un pointeur de la RAM d'Upper tout long pair compris entre
`$A00000` et `$A7FFFF` (relogé de +`$180000`) ; dans ro9a44, 283 longs, dont 235 sont des DONNÉES (un mot `$00A0`-`$00A7`
à côté d'un autre mot, lu en mots / octets / couleurs par le code d'Upper : X / Y d'objets, tables de mots, couleurs des
banques de palettes T_619110, décalages de palette, scripts d'IA, enregistrements d'anims, images des fins). À 1 : les
235 cases de `donnees/ram_donnees.txt` restent comme chez Upper, les 48 pointeurs RAM / vidéo de
`donnees/ram_pointeurs.txt` (45 prouvés par le journal des conversions ou par le lecteur, 3 déduits) restent relogés, et toute autre
case « ram » est relogée comme avant mais comptée (`ram non classee` dans `stat_donnees`, adresse affichée) pour être
classée. À 0 = ro9a44 à l'octet (témoin : 34/35, `env.sh`). À 1 : 235 octets changent (un par case, l'octet bas du mot
haut `$B8`.. -> `$A0`..), dans `ext_4e8000.bin` (24), `ext_c70000.bin` (21), `ext_d0c000.bin` (190) et le module ;
aucune taille ni adresse ne bouge, `sz3ud.03c` inchangé (`37799f69…`) ; `a5_inconnus` passe de 30 à 12 (les 18 retirés
venaient de ces données). Mesures (`<workspace>/work/reloges_293/ETAT.md`, banc unique contre ro9a44_fige) : VERSUS,
training, Arcade, continue, game over, 2e joueur et 40 décors (jumelle `TIRAGE_CPU=0`) identiques ; 85 fins : 85 / 85
abouties, journaux, sondes et durées identiques, 77 fins identiques, 8 avec des captures différentes (0F ×3, 10 ×3, 19,
1A : 56 captures) ; effets visibles trouvés : (1) la séquence de la base (fins 0F, 10, 19, 1A) place ses explosions avec les Y de
T_61A180 (`$A0`, et non `$B8` = 24 px plus bas) ; dans la boîte qui change, 47 de ces captures sont plus près d'Upper,
8 plus loin, 1 égale (part de hasard des explosions, relevée par fins_restes) ; capture 0046 de la fin 0F identique au
pixel à Upper ; (2) en combat sur le décor de Zangief (route 0D), le décalage de palette de T_917BE0 (`0x917C02` :
`$A0`, et non `$B8` = palette mal alignée) : la machine derrière les tuyaux n'a plus de couleurs fausses (captures
denses ro9a44 contre ro9a45 ; le banc des décors, 4 images par décor, ne le voyait pas).

Candidat **ro9a43_portraits** (16/11/2026, non basculé) : recette `ro9a41/greffe/vars_ro9a43_portraits.txt` =
`vars_ro9a43.txt` + `PORT_COULEUR=1` (`ro9a41/greffe/etape3/port_couleur.py`) : à la sélection et au VS d'Hyper, le
portrait d'un perso en version ZERO 3 prend la couleur du bouton (règle d'Upper ; ZERO / ZERO 2 / ALPHA restent en
couleur 2, comme Hyper) ; 3 retouches dans le code d'Hyper (chargeur va `0x31FA24`, objet de sélection `0x33BE70`, objet
du VS `0x3313A4`) et un talon de 20 o en `$37FF94` (`re/allocations.tsv`). `PORT_COULEUR_SEL_VERSION=1` ajoute le talon
par image de la sélection (`0x33BEC8`, `$37FF80`), sans effet visible : laissé à 0. À 0 = ro9a43 à l'octet ; à 1, seuls
`sz3ud.04c` et `sz3.09c` changent. Mesures (`<workspace>/work/portraits_v1/ETAT.md`) : VS de 7 paires identiques au
pixel à Upper v161 joué avec les mêmes persos et boutons, portraits de sélection identiques ; VERSUS : `vs.log`
identique à ro9a43 ; banc des 85 fins identique à ro9a43 (journaux, sondes, sentinelles et 9 569 / 9 569 captures). Avec les MAX (recette `vars_ro9a41_max.txt` + `PORT_COULEUR=1`) :
le portrait d'Eagle suit aussi le bouton (accroche L2-04, bloc de 6 couleurs), identique au pixel à Upper MAX aux 6
boutons.

Depuis le 16/11 (même interrupteur, site S5) : à la sélection, le **petit sprite** du perso prend aussi la couleur du
bouton, comme dans Upper (objet suiveur d'Hyper va `0x339AEC` : `MOVEQ #2,D2` en va `0x339EB8` -> `EXT.W D2`, sur place,
mêmes cycles ; 4e retouche, toujours dans `sz3ud.04c`). Mesures (`<workspace>/work/portraits_v1b/ETAT.md`) : palettes
08 / 09 chargées à la sélection identiques à Upper v161 pour 18 / 18 (9 paires Ryu / Sagat / Chun-Li / Ken / Rose, 6
boutons, J1 et J2) ; essai des boutons et VERSUS : `vs.log` identique à ro9a43 et à la V1 précédente ; 4 fins
identiques à ro9a43 ; Eagle (MAX) : les 15 premiers mots de chaque palette identiques à Upper MAX ; le 16e (un numéro,
pas une couleur) vaut couleur × 5 chez les natifs (Upper et greffe) et dans la table d'Eagle de la greffe, la couleur
seule dans Upper MAX. `$129` reste dans 0..5 (bouton 0..5 ; miroir : +1 puis 6 -> 0 en va `0x31FB70`, vu sur Ryu HK /
Ryu HK, mêmes palettes que dans Upper).

Candidat **ro9a43_menu** (16/11/2026, non basculé) : recette `ro9a41/greffe/vars_ro9a43_menu.txt` = `vars_ro9a43.txt` +
`MENU_CURSEUR_ARCADE=1` : le curseur du menu des modes est posé sur ARCADE (et non plus VERSUS) à chaque arrivée depuis
l'écran titre ; titre, Start, Start lance donc une partie Arcade, BAS une fois redonne VERSUS. Un seul mot du module :
l'immédiat de `addiu v1,zero,1` (fichier `0x6296C`, tâche du menu `0x2526E0` : `CMPI.B #5,$C201(A5) ; BEQ ;
MOVE.B #1,$C201(A5)`) passe à 0 ; en 68K, un octet de `sz3ud.03c` (image `$010126`, `MOVE.B #$1` → `#$0`). Le retour
d'OPTION / EXIT (curseur 5) est inchangé. Interrupteur à 0 (défaut) = ro9a43 à l'octet. Le nom `MENU_ARCADE` était déjà
pris (entrée ARCADE du menu, défaut 1).

Étape **ro9a44_fins** (16/11/2026 ; recette renommée `ro9a41/greffe/vars_ro9a44_fins.txt`, elle s'appelait `vars_ro9a44.txt` au §241) =
`vars_ro9a43.txt` + `FINS_IMAGES=1 SCRIPTS_FIN_BRUTS=1 CARTES_FIN_BRUTES=1 FIN_SECOUSSE=1` (§241) : les trois lecteurs de
T_674C00 du module des fins lisent une copie de la table X2 aux images d'Upper là où celles d'Hyper diffèrent (41 images,
codes d'emplacement 1 décalés de $200 chez Hyper : portraits des fins $20, $21, $22…) ; aucun long des 42 scripts de fin
ni des structures T_60B700 / T_60B7B0 n'est relogé (attentes $00A0-$00A6 prises pour des pointeurs de RAM : +24 images,
palette décalée ; fondu de la fin 1A ; carte de blocs du plan 2 de la fin 03) ; 0x214630 (secousse de la fin 03) greffée
(exige `CARTES_FIN_BRUTES=1`, la construction échoue sinon). Programme `sz3ud.03c` `68d0cf87…` ; les quatre à 0 =
ro9a43 à l'octet. Mesures : 85 / 85 fins abouties, durées de 04, 08, 0E, 1A = Upper (± 1), 8 455 / 9 547 images
identiques à ro9a43, 956 plus proches d'Upper, 12 plus loin (colonne du générique, explosions placées au hasard) ;
VERSUS 90/90 et `vs.log` identiques ; 40 décors : journaux et 160 captures identiques à ro9a43.
Variante **ro9a44_generique** (`vars_ro9a44_generique.txt` = ro9a44_fins + `GENERIQUE_BUDGET=1`, retenue le 16/11 dans ro9a44) : les lignes
du générique décomptent le budget de sprites comme Upper (un par lettre) au lieu de réserver $C0 par objet : texte de
dialogue rendu pendant le générique (fins 21, 22) ; coûts : code d'Hyper décalé de $A octets au plus entre 0x39DCB8 et
0x3BF110 dans l'image 68K, une image de ralentissement de plus çà et là (générique d'un tic en retard : 06, 0A, 09, 15,
1D). Programme `sz3ud.03c` `571acf08…` ; VERSUS, décors identiques ; détail §241.

Candidat **ro9a43_pointeurs** (15/11/2026, non basculé : `HA_ETAT` reste `ro9a41`) : recette
`ro9a41/greffe/vars_ro9a43_pointeurs.txt` = `vars_ro9a42.txt` + `PREUVES=@HA_G@/donnees/pointeurs_prouves_union.txt
DECOR_E0_MIN=700` : les cases de pointeurs prouvées sont l'UNION des journaux de conversions mesurés sur l'ancien oracle
d'Upper (`fige/ro5`, traducteur v153, 30 580 cases = `pointeurs_prouves.txt`) et sur le nouveau (`fige/ro5_v161` = Upper
publié, mêmes 44 parties, 30 670 cases) : 33 299 cases (relevé `releves_ro9a41/greffe/donnees/pointeurs_prouves_union.txt.tsv`) ;
`DECOR_E0_MIN=700` fait échouer la construction si le recodage des objets de décor perd des trames (correctif DECOR_E0, 5e4e6b0). Les autres
relevés restent ceux mesurés sur l'ancien oracle (les re-mesurer change l'échantillon des combats, pas la justesse).
Programme `sz3ud.03c` `195d29d2…` ; contre ro9a42 : 03c 24 octets, 04c 133, 05c-10b identiques, bloc de données +3 104 o.
Mesures (15/11, contre la copie figée de ro9a42) : VERSUS 90/90 captures et `vs.log` identiques ; décors 39/40 identiques
(mêmes journaux aux pointeurs du bloc près, mêmes captures), décor 40 corrigé (objets $12 / $14 comme chez Upper, plus de
soldat parasite près du score) ; 85 / 85 fins abouties aux mêmes durées, 9 565 / 9 569 images identiques, les 4 autres
(20 Z3, 13740-13920) sans l'objet parasite du haut, comme Upper. Les nouvelles cases seules (sans l'union) plantent la fin
1b Z3 : la partie de conversions de 1b, plus longue sur le nouvel oracle, est coupée par NF avant la fin de la fin.

Candidat **ro9a42** (14/11/2026, non basculé : `HA_ETAT` reste `ro9a41`) : recette `ro9a41/greffe/vars_ro9a42.txt` =
`vars_ro9a41.txt` + `FINS_A=1 GENERIQUE_TITRES=1` : 26 routines d'acteurs de fin d'Upper greffées au lieu d'homologues
d'Hyper sans rapport (`etape3/force3.py`, groupes `a1`, `sagat`, `1c`, `a2`) et les deux pointeurs impairs des titres du
générique (`T_9590C0`) relogés (`etape2/donnees2.py`) ; programme `sz3ud.03c` `ca3d87d2…` ; les deux à 0 = ro9a41 à
l'octet (§233).

État figé : **ro9a41** (13/11/2026 ; programme `sz3ud.03c` md5 `be88f3f9…` (inchangé), `sz3ud.04c` `ae411424…`, zip de
référence CRC `C9107FC2`) : ro9a40 + `PAIRES_CODE=1` : 10 longs du bloc de données de la greffe, paires de mots signés
(dx, dy) de tables décrites dans `re/` (T_615AC0 [0] [6], T_60DAE0, T_6139A4, T_613BA0, T_615940), n'y sont plus relogés comme des
pointeurs de code (liste `ro9a41/greffe/donnees/ptr_exclus_paires.txt`) ; 14 longs changent (avec la copie X2 de
T_615AC0), aucun n'est lu dans les parties d'essai (§230). Recette `ro9a41/greffe/vars_ro9a41.txt` = `vars_ro9a40.txt`
+ `PAIRES_CODE=1` ; à 0 = ro9a40 à l'octet.
Précédent : ro9a40 (13/11, `be88f3f9…`, CRC `68B5EE56`, recette `vars_ro9a40.txt`) : ro9a39 + quatre correctifs,
interrupteurs à 0 dans le code et à 1 dans la recette : `PAL_VERSION` et `COUL_CPU_VERSION`
(un CPU ou un joueur en ZERO / ZERO 2 / ALPHA garde la couleur de sa version du face-à-face à la fin, §225),
`PORT_VERSION` (portraits de la carte, du face-à-face et de la victoire d'une version en couleur 2, comme dans Hyper,
§226), `BARRE_LOGO_FACE` (plus de bande de morceaux de lettres quand la transition « logo » finit sur l'écran de dialogue
d'un rival ZERO 3 ou du combat final, §227) ; tous à 0 = ro9a39 à l'octet (§228).
Précédents : ro9a39 (12/11, `2459b5a5…`, CRC `D31889B0`, recette `vars_ro9a39.txt`) : ro9a38 + étape L1 de l'intégration
des persos MAX, **invisible pour le joueur** (§224) : `X2_TABLES=1` (54 tables par perso, liste
`ro9a41/greffe/etape3/x2_tables.tsv`, recopiées à 48 entrées dans la fenêtre des données de la greffe, ≤ 112 Ko ; entrées
40-44 = octets qui suivent la table, 45 / 46 = entrée 0, 47 = entrée 39 ; lecteurs copiés redirigés) et
`D4_REGLE=regle_d4_l1.tsv` (Yun / Ingrid en `$2D` / `$2E` dans la table D4). `X2_VALEURS` (valeurs des MAX) reste vide.
Rien n'est encore posé pour les MAX : ROM graphique `$5400000-$5FFFFFF` (5 segments, emplacement 5 « commun MAX »), code
`$3A0000-$3BFFFF`, T4 / T5 et RAM `$FF7F00-$FF7FFF` sont seulement réservés ; le format prévu de la liste des segments
est `greffe/max/segments.tsv` (règles M2, M4, M6 : sans objet en L1).
Précédents : ro9a38 (12/11, `2dfdb15c…`, CRC `AC7D9F00`, recette `vars_ro9a38.txt`) : ro9a37 + quatre correctifs de la
revue (R3 `R3_CREUX`, `R3_CIBLES` ; X6 `X6_FINS` ; A2a `A2A_VS` ; E2b `E2B_DEFI`), §223.
Précédents : ro9a37 (12/11, `627c98c4…`, CRC `51882820`, recette `ro9a41/greffe/vars_ro9a37.txt`) : ro9a36 traduite par
le traducteur de la greffe v161 (`e47/untranspile3_v161`) ; ro9a36 (11/11, `93e88fee…`, CRC `31F7E170`, recette
`vars_ro9a36.txt`) ; ro9a35b (08/11, `650b1bec…`, CRC `4D6E1D2D`, recette `vars_ro9a35b.txt`) (`HA_VARS`).
Expérimental.

## Contenu

| chemin | rôle |
|---|---|
| `greffe_ha.py` | étape « greffe » : matérialise le code et les relevés, puis enchaîne la greffe comme l'atelier (`construit_e3.sh`) : plan seul → table A5 → module, bloc, traduction. `--audit` : journal de tous les fichiers ouverts. |
| `fige35.py` | `materialiser` : recopie en remplaçant les marques `@HA_*@` par les chemins de la construction ; une marque non donnée devient un chemin absent (toute fuite vers l'atelier échoue). (`figer` ne sert qu'à l'atelier.) |
| `ro9a41/greffe/` | code de la greffe à l'état ro9a41 (`etape2`, `etape3`, `outils`, traducteurs de la greffe `e47/untranspile3_v161` et, pour les recettes précédentes, `e42/untranspile3_v160`) et décisions (adresses, interrupteurs) ; `vars_ro9a37.txt` = recette (celle de ro9a36 avec `TRAD=@HA_G@/e47/untranspile3_v161` ; ro9a36 = ro9a35b + `DECOR_E0=1 CONT_SORTIE=1 CONT_CHIFFRE=1`, exclusion `64b380`). |
| `ro9a41/carto/` | `commun.py` et analyses communes (code). |
| `ro9a41/paquet/paquet_fbneo.py` | paquet de la greffe (entrée `ro9a`, pilote `sfa3hahsfa`), inchangé depuis ro9a36. |

Aucune donnée de jeu. `releves_tsv.py` : tableaux des relevés (ci-dessous). Le traducteur de référence est celui du dépôt (`src/hsfa`, marque `@HA_UT@`).

## Relevés (`releves_ro9a41/`, tableaux TSV)

La greffe lit aussi des **relevés** de l'atelier, tirés de passes MAME sur le jeu et d'analyses statiques. Ils ne
contiennent que des adresses, des numéros (images, tailles, compteurs), des drapeaux et des étiquettes : aucun octet
du jeu. Ils sont versionnés en TSV (accord du 08/11, comme les tables de la Rosette des MAX), 19 tableaux, 4,7 Mo (dont
`greffe/donnees/pointeurs_prouves_union.txt.tsv`, 15/11, lu seulement par la recette `vars_ro9a43_pointeurs.txt`) :

- `greffe/traces/journaux_{u_lu,defi_lu,objets_lu}.tsv` : union des 65 journaux d'adresses lues par Upper sous MAME
  (la construction n'en lit que l'union et les noms), en plages « début-fin » ;
- `greffe/traces/*/ram.txt.tsv` : cartes RAM d'Hyper et d'Upper (adresse, 1re / dernière image lue et écrite), en plages ;
- `greffe/donnees/*.tsv`, `eu/*.tsv` : analyses (routines, décisions, homologues, variables A5, couverture).

Chaque tableau commence par un en-tête « # » : origine, mesure, format. `releves_tsv.py reconstituer` redonne les
fichiers lus par les outils (`greffe_ha.py` le fait seul) ; `releves_tsv.py verifier` compare à des relevés d'origine.
Les relevés n'ont pas changé depuis ro9a35b (79 fichiers identiques à l'octet ; ro9a37 à ro9a41 : simple renommage). Preuve :
greffe depuis ces tableaux = ro9a41 à l'octet. `--greffe-releves DOSSIER` permet d'en donner d'autres.

## Entrées venues de la construction

`HA_EXTRACT` (modules ro5 / ro9 décompressés), `HA_ANIMS` (cache des anims), `HA_XDATA`, `HA_MODULES_SON` (module ro9
corrigé + bloc `$E70000` si la table du rejeu est donnée, sinon module d'Hyper d'origine : voix de SFA3),
`HA_MAME_RO9` / `HA_MAME_RO5` (banques d'Hyper et d'Upper). Tout est produit par `hsfa_build.py` depuis l'ISO.

## Portabilité

Python + NumPy seulement (pas de MAME, pas de vasm). La greffe relance le traducteur par `sys.executable` (le
constructeur tout-en-un sert de « python ») ; liens symboliques remplacés par des copies si le système les refuse.

## Nouvelle livraison de la greffe

`hsfa_build.py` lit l'état dans deux constantes : `HA_ETAT` (code `<HA_ETAT>/`, relevés `releves_<HA_ETAT>/`) et
`HA_RECETTE` (recette `<HA_ETAT>/greffe/<HA_RECETTE>` ; le nom de la construction, `HA_NOM`, en dérive :
`vars_ro9a44.txt` -> `ro9a44_fige`, celui de la copie figée de l'atelier, écrit dans `hsfa_info.txt`). La greffe avec
les persos MAX (`hyperarcademax`) a ses propres recettes, `HA_RECETTE_MAX_BASE` et `HA_RECETTE_MAX` (ro9a41).
Une livraison qui ne change que la recette (même code, mêmes relevés, comme ro9a44) ne change que `HA_RECETTE`.
Sinon, reporter le diff du code de l'atelier (pas une nouvelle copie : elle perdrait les correctifs de portabilité),
écrire la recette, vérifier que les relevés lus n'ont pas changé (sinon `releves_tsv.py exporter`), renommer les deux
dossiers, changer `HA_ETAT` et `HA_RECETTE`, puis prouver : greffe seule = construction figée de l'atelier à l'octet, et zip complet = zip livré hors
`hsfa_info.txt` (BUILD §11).
