# Le cœur libretro FBNeo « HSFA »

Ce document explique comment le cœur fait tourner les jeux retraduits, pourquoi chaque mécanisme existe et où le
trouver dans le code. Il vaut pour l'arbre `libretro/FBNeo` au commit `af5d3f3` plus la chaîne de
[`patches/fbneo/`](../../patches/fbneo/README.md) (vérifiée le 2026-10-18). Une fiche par patch :
[coeur-fbneo-patchs.md](coeur-fbneo-patchs.md). Banc de développement équivalent : [banc-mame.md](banc-mame.md).
Les mots techniques sont définis dans le [glossaire](#glossaire), en fin de document.

## 1. Le principe

L'Anthology PS2 ne contient pas d'émulateur : chaque jeu est une **recompilation statique** du 68000 d'origine vers le
MIPS de la PS2. HSFA fait le chemin inverse et produit une **ROM programme 68000** pour la CPS2.

Le programme retraduit garde des habitudes de la PS2 qu'une vraie CPS2 ne sait pas servir :

| habitude du portage PS2 | sur une CPS2 réelle |
|---|---|
| données du module à des adresses fixes, bien au-delà de 4 Mo | la ROM programme fait 4 Mo |
| fichiers graphiques chargés par « emplacement », codes de tuiles **locaux** à chaque fichier | codes de tuiles **globaux** |
| tuiles d'Upper et d'Hyper absentes de la ROM graphique de SFA3 | 32 Mo de ROM graphique |
| musiques lues sur le disque (flux ADX) | musique jouée par le Z80 sur le QSound |
| sons de SFA1 / SFA2 pour les versions ZERO / ZERO 2 d'Hyper | une seule ROM QSound de 16 Mo, pleine |
| écran d'options en C natif, non traduisible | menu de test et EEPROM, que le jeu ne lit plus |

Deux réponses sont possibles : changer le programme (le traducteur), ou **augmenter la machine**. Le cœur choisit la
seconde chaque fois que le programme aurait dû être réécrit en profondeur. C'est une CPS2 de FBNeo avec des
extensions, que ce document appelle le **« matériel virtuel HSFA »** (§5).

Trois règles tiennent l'ensemble :
- **Rien ne change pour les autres jeux.** Chaque crochet teste `HsfaMode` (0 = jeu ordinaire).
- **Le cœur imite le banc MAME** (fork `sfa3hx` + scripts Lua). Le même zip doit donner la même partie des deux
  côtés, au hasard près (§11).
- **Aucune donnée de jeu dans le code.** Tout vient de l'archive du jeu, construite chez l'utilisateur par
  `tools/fbneo-hsfa/paquet_fbneo.py`, ou de ses fichiers PS2. Une nouvelle traduction demande un nouveau zip, pas un
  nouveau cœur.

## 2. Où est le code

Tout est dans l'arbre FBNeo patché. Chemins relatifs à `src/burn/drv/capcom/` sauf mention.

| fichier | rôle |
|---|---|
| `cps_hsfa.cpp` | le cœur d'HSFA : tables, liste d'objets, plans, options, roulette, flux, rejeu, carte musique, états, chargement |
| `d_cps2.cpp` | les 4 pilotes, leurs listes de ROM, entrées et DIP ; `HsfaSfa3Init`, `HsfaUpperInit`, `HsfaHyperInit` |
| `hsfa_flux.h` | lecteur de flux musique ADX et Ogg Vorbis (en-tête seul, partagé avec le fork MAME) |
| `hsfa_rejeu.h`, `hsfa_qsound.h` | rejeu des sons SFA1 / SFA2 ; 2ᵉ QSound instanciable (HLE de `qs_c.cpp`) |
| `hsfa_musique.h` | carte musique : pilote Z80 d'origine + QSound dédié |
| `cps.cpp`, `cps_mem.cpp`, `cps_obj.cpp`, `cps_run.cpp`, `cps_rw.cpp`, `cps_scr.cpp`, `qs.cpp` | crochets (quelques lignes chacun) |
| `src/burner/libretro/libretro.cpp` | ROM sans CRC cherchées par nom ; chemin de l'archive (`szBurnHsfaArchive`) ; nom du cœur |
| `src/burner/libretro/Makefile.hsfa`, `Makefile.hsfaws` | sous-ensemble CPS1/CPS2 + `cps_hsfa.cpp` + stb_vorbis ; variante 16:9 |
| `src/dep/libs/stb_vorbis/` | décodeur Ogg Vorbis (stb_vorbis 1.22, domaine public / MIT) |
| `hsfa/hsfa_run.c` | lanceur d'essai sans fenêtre (§10) |

`hsfa/paquet_fbneo.py`, dans l'arbre FBNeo, est une vieille copie : l'outil de référence est
`tools/fbneo-hsfa/paquet_fbneo.py` du dépôt.

## 3. Parcours d'une image

`Cps2Frame()` (`cps_run.cpp`) reste celui de FBNeo. Les extensions s'y glissent ainsi :

1. **Le 68000 exécute le programme traduit**, en tranches, avec les IRQ de la CPS2.
   - Il lit ses données dans les **blocs externes** (`$940000-$EFFFFF` pour Hyper) comme dans une ROM.
   - Il écrit sa liste d'objets dans `$700000-$70FFFF`. Chaque écriture passe par `HsfaObjWrite`, qui en garde une
     copie brute (`Ombre`). Quand le **marqueur de fin** arrive (X = Y = `$8000`), `HsfaEclater` convertit toute la
     liste (§5.1) et l'écrit dans les deux banques d'objets.
   - Pour un son, il remplit la boîte aux lettres QSound (`$618001-$618019`) puis écrit `$61801F = 0`. Le crochet de
     `CPSQSoundC0WriteByte` (`cps_mem.cpp`) décide alors qui joue la commande (§6) et peut la réécrire pour le Z80.
   - Upper et Hyper : une écriture dans `$804200-$804205` change la base d'un plan (§5.2).
2. **En même temps, le Z80 principal** joue la ROM son (SFA3, ou ROM hybride `hx3.*`), avec une IRQ à 250 Hz
   comme MAME.
3. **`CpsDraw()`** dessine les plans depuis `nCpsGfxScroll` et les objets avec leurs codes sur 20 bits.
4. **`HsfaFrameDone()`** (`cps_hsfa.cpp`), l'équivalent du `frame_done` du banc :
   - à la 1ʳᵉ image, écrit les bases de plans de la configuration (`plans=` de `hsfa_tab.bin`) ;
   - suit le pointeur d'animation de l'emplacement 4 et termine un chargement différé (§5.1) ;
   - au menu des modes (`$FF8000 = 4`), écrit les réglages des options du cœur dans la RAM (§7) ;
   - incrémente le compteur d'images `nImage`.
5. **`QsndEndFrame()`** (`qs.cpp`) mixe, dans l'ordre : QSound principal, flux musique, 2ᵉ QSound (rejeu), puis la
   carte musique (2ᵉ Z80 + 3ᵉ QSound).

Exemple : un combat d'Hyper contre Ken en version ZERO. Le jeu pose le code musique `0042`
([FLUX](../rapports/FLUX.md) §0). Si le zip contient la carte musique, elle démarre le pilote SFA1 sur son QSound ;
sinon le flux `Y57` est lu. Dans les deux cas, le Z80 principal reçoit `FF05` : sa musique s'arrête, les voix
continuent. Les voix et bruitages de version ZERO (codes du rejeu, `$2000` et plus) partent sur le 2ᵉ QSound, et le
Z80 reçoit un code vide.

## 4. Pilotes et archives

### 4.1 Pilotes

| pilote | jeu | `HsfaMode` | blocs externes | ROM graphique | son | DIP |
|---|---|---|---|---|---|---|
| `sfa3hsfa` | SFA3 (`ro3`) | 1 : plans renumérotés | `$A00000-$EFFFFF` | 32 Mo de SFA3 | ROM de SFA3 | `HsfaDIPList` (musique PS2 : « Missing tracks only ») |
| `sfa3uhsfa` | Upper (`ro5`) | 2 : bases de plans | `$A00000-$EFFFFF` | 64 Mo (`hsfa_gfx.bin` en `$2000000`) | hybride `hx3.*` + flux | `HsfaDIPList` |
| `sfa3hhsfa` | Hyper (`ro9`) | 2, `HsfaHyper = 1` | `$940000-$EFFFFF` | 64 Mo | hybride + flux + rejeu + carte | `HhsfaDIPList` (« All tracks ») |
| `sfa3hahsfa` | essai `ro9a` (Hyper + Arcade d'Upper) | 2, `HsfaHyper = 1` | `$940000-$EFFFFF` (+ trous, §5.3) | 80 Mo (`hsfa_gfx.bin` de 48 Mo) | comme Hyper | `HhsfaDIPList` |

Le programme reste un CPS2 « Phoenix » (non chiffré). Les mêmes noms de pilotes servent au cœur 16:9 : seul le
cœur change (§9).

### 4.2 Membres du zip

« Déclaré » : membre de la liste de ROM du pilote, chargé par FBNeo. « Sur place » : lu par le cœur dans le zip, à
son décalage, sans passer par la liste de ROM ; il doit être **stocké** (non compressé).

| membre | pilotes | mode | contenu | lu par |
|---|---|---|---|---|
| `sz3ud.03c`, `sz3ud.04c`, `sz3.05c` … `sz3.10b` | tous | déclaré, CRC 0 | programme 68000 traduit, 8 × 512 Ko, mots échangés | FBNeo (cherché **par nom** : `libretro.cpp`) |
| `sz3.13m` … `sz3.20m` | tous | déclaré | ROM graphique de SFA3 (arcade, ou reconstruite depuis l'ISO) | FBNeo |
| `phoenix.key` | tous | déclaré | clé Phoenix | FBNeo |
| `sz3.01`, `sz3.02`, `sz3.11m`, `sz3.12m` | `sfa3hsfa` | déclaré | Z80 et QSound de SFA3 | FBNeo |
| `hx3.01`, `hx3.02`, `hx3.11m` … `hx3.14m` | Upper, Hyper, `ro9a` | déclaré, CRC 0 | son hybride d'Upper : Z80 + QSound de 16 Mo | FBNeo |
| `hsfa_ext.bin` | tous | déclaré | image des blocs externes jusqu'à `$EFFFFF` ; sa **taille donne la base** | `HsfaExtTaille`, `HsfaLoadData` |
| `hsfa_tab.bin` | tous | déclaré | tables des banques et des plans, carte, configuration (§4.4) | `HsfaParseTab` |
| `hsfa_gfx.bin` | Upper, Hyper, `ro9a` | déclaré | région graphique étendue, au format interne de MAME, convertie au chargement | `HsfaConvertGfx` |
| `hsfa_trous.bin` | `sfa3hahsfa` | déclaré **facultatif** (`BRF_OPT`) | les 7 trous de la carte 68K bout à bout, 5,08 Mo (prototype) | `HsfaInit` |
| `hsfa_flux.bin` | Upper, Hyper | sur place | AFS réduit : mêmes indices que `Y_DATA.BIN`, flux ADX ou Ogg, entrées inutiles vides | `HsfaFluxInit` |
| `hsfa_flux_table.txt` | Upper, Hyper | sur place | table code musique → flux | `hsfa_flux::lecteur` |
| `hsfa_rejeu.bin` | Hyper | sur place | ROM du 2ᵉ QSound, 8 Mo (SFA1 en +0, SFA2 en +4 Mo), CRC contrôlés | `HsfaRejeuCharge` |
| `hsfa_rejeu_table.txt` | Hyper | sur place | écritures QSound de chaque son de SFA1 / SFA2 | `hsfa_rejeu::rejeu` |
| `hsfa_musique.bin`, `hsfa_musique_table.txt` | Hyper (`HSFA_PARTITIONS=1`) | sur place | programmes Z80 son de SFA1 et SFA2 ; table code Hyper → pilote | `HsfaMusiqueInit` |
| `hsfa_info.txt` | tous | ignoré | date et sources de la construction | — |

Ordre de recherche des données de son : **membre du zip**, puis `<système RetroArch>/fbneo/hsfa/` (`Y_DATA.BIN`,
`X_DATA.BIN`, `anthology.iso`, ou `ydata.txt` / `xdata.txt` contenant un chemin), sinon la fonction reste inactive
et le jeu tourne quand même. Un zip en 7z ne donne aucun membre « sur place ».

### 4.3 Comment le cœur retrouve l'archive

- Les ROM au CRC nul d'un pilote dont le nom contient `hsfa` sont cherchées **par nom** (`open_archive`,
  `libretro.cpp`) : le programme change à chaque traduction.
- Le frontal note le chemin de l'archive dans `szBurnHsfaArchive` (`burn.cpp`). `HsfaResoutArchive` essaie le nom
  sans extension, `.zip` puis `.ZIP`, et vérifie la signature zip.
- `HsfaZipMembre` lit le répertoire central et rend le décalage des données. Le zip64 n'est pas géré (le zip d'Hyper
  en ADX fait environ 710 Mo).

### 4.4 `hsfa_tab.bin`

En-tête `HSFATAB1`, nombre d'entrées, puis `{ nom[24], décalage, longueur }` par entrée (petit-boutiste).

| entrée | contenu |
|---|---|
| `f<N>` | fichier graphique PS2 n° N : pour chaque code local, le code global (u32, `$FFFFFFFF` = vide) |
| `plan1`, `plan2`, `f312` | tables de renumérotation des plans de SFA3 (scroll1, scroll2, scroll3) ; `plan2` sert aussi d'emplacement 1 |
| `carte` | texte : `perso <id> <fichier>` et `anim <pointeur> <fichier>` |
| `config` | texte `clé=valeur` : `commun` (banque commune : SFA3 254, Upper 351, Hyper 545), `ptr_anim` (`FF3E48` SFA3, `FF40BC` Upper / Hyper), `gfx_intro` (456), `plans` (Upper / Hyper `300,340,3a0`), `lat4`, `lat4_max` |

## 5. Le matériel virtuel HSFA

Chaque ligne est une chose qu'une CPS2 réelle n'a pas, ou fait autrement. « Programme » = le programme 68000
traduit ; « cœur » = le code C++ d'HSFA.

| extension | adresse ou interface | qui l'écrit | pourquoi (PS2 → CPS2) | code | patch |
|---|---|---|---|---|---|
| programme sans CRC | ROM `$000000-$3FFFFF` | — | il change à chaque traduction | `libretro.cpp` (`find_rom_by_name`) | 1 |
| blocs externes | ROM `$A00000-$EFFFFF` (Hyper `$940000-`) ; base = `$F00000` − taille de `hsfa_ext.bin` | lus par le programme | les données du module PS2 sont à des adresses fixes et ne tiennent pas dans 4 Mo | `HsfaExtTaille`, `SekMapMemory` dans `HsfaInit` | 1, 4 |
| trous de la carte 68K | 7 plages, dont `$410000-$617FFF` et `$FB0000-$FEFFFF` (§5.3) | lus par le programme | blocs externes saturés dans `ro9a` ; +5,08 Mo de données sans cycle de plus | `HsfaTrous`, `HsfaInit` | 13 (prototype) |
| liste d'objets convertie | écritures dans `$700000-$70FFFF` ; marqueur de fin X = Y = `$8000` | programme (liste brute) → cœur (liste convertie) | codes de tuiles **locaux** à un emplacement de banque (bits 13-15 de Y) | `HsfaObjWrite`, `HsfaEclater`, `HsfaEmplacements` | 1 |
| codes d'objet sur 20 bits | bits 16-17 → bits 13-14 de Y (comme la CPS2) ; bits 18-19 → **bits 10-11 de X** (ajout HSFA) | cœur | tuiles d'Upper / Hyper au-delà de `$40000` | `HsfaEclater` ; `Cps2ObjDraw` (`cps_obj.cpp`) | 1 |
| ROM graphique étendue | région ≥ 64 Mo, `hsfa_gfx.bin` en `$2000000` ; `ro9a` : 80 Mo | cœur, au chargement | les persos et décors d'Upper / Hyper ne sont pas dans les 32 Mo de SFA3 | `HsfaGfxLenMin`, `HsfaConvertGfx` ; `nCpsGfxLenMin` (`cps.cpp`) | 1, 12 |
| registres des bases de plans | mots `$804200`, `$804202`, `$804204` (scroll1-3), unités de 64 Ko ; 0 = mappage d'origine | cœur à la 1ʳᵉ image (`plans=`) ; programme dans `ro9a` | décors PS2 rangés dans `hsfa_plans.bin` : une base par plan | `HsfaPlaneWrite`, `HsfaPortWriteWord`, `HsfaUpdateScroll` | 1, 12 |
| renumérotation des plans (SFA3) | écritures dans la vidéo `$900000-$92FFFF` et dans `$804102-$804107` (CPS-A) | programme → cœur | les codes de tuiles de plan de SFA3 PS2 ne sont pas ceux de l'arcade | `HsfaVramWrite`, `HsfaBaseWrite`, `HsfaReconvertit` | 1 |
| scroll3 sur 14 bits | `Cps2Scr3Draw` | cœur | comme MAME | `cps_scr.cpp` | 1 |
| emplacement 4 différé (LAT4) | pointeur d'animation `$FF3E48` / `$FF40BC` ; `lat4=`, `HSFA_LAT4` | cœur | sur PS2 la lecture du fichier est mise en file : l'ancien portrait reste quelques images | `HsfaSuivre4`, fin de `HsfaFrameDone` | 6 |
| boîte aux lettres QSound interceptée | écriture `$61801F = 0` (commande en `$618001/3`, volume `$618005`, paramètre `$618007/9`) | programme → cœur | aiguiller chaque commande vers la carte, le flux, le rejeu ou le Z80 | `CPSQSoundC0WriteByte` (`cps_mem.cpp`), `HsfaFluxCommande`, `HsfaRejeuCommande` | 3, 5, 10 |
| IRQ du Z80 à 250 Hz | `QsndReset` | cœur | FBNeo met 252 Hz ; MAME 8 MHz / 32 000 = 250 Hz : musique synchronisée comme au banc | `qs.cpp` | 1 |
| flux musique ADX / Ogg | `hsfa_flux.bin` ou `Y_DATA.BIN` ; DIP A | cœur | sur PS2, beaucoup de musiques ne sont **que** des flux du disque | `hsfa_flux.h`, `HsfaFluxInit`, `HsfaFluxRendu` | 3, 8, 9 |
| 2ᵉ QSound (rejeu) | codes `$2000+`, `$3000+`, `$4000+` ; ROM `hsfa_rejeu.bin` 8 Mo | cœur | voix et bruitages SFA1 / SFA2 d'Hyper : la ROM QSound de 16 Mo est pleine | `hsfa_rejeu.h`, `hsfa_qsound.h`, `HsfaRejeuRendu` | 5 |
| 2ᵉ Z80 + 3ᵉ QSound (carte musique) | Zet n° 1 ; ROM du rejeu ; `hsfa_musique.bin` | cœur | jouer les musiques ZERO / ZERO 2 par leurs pilotes Z80 d'origine au lieu d'enregistrements | `hsfa_musique.h`, `HsfaMusZet`, `HsfaMusiqueRendu` | 10 |
| options du cœur → RAM | DIP B-H ; octets `$FF80A0-$FF80A5`, `$FF80DE-$FF80DF`, VS MODE, EXTRA OPTION | cœur, au menu des modes | l'écran OPTION PS2 est du C natif, non traduit : sa recopie des réglages était perdue | `HsfaOptions` | 7 |
| roulette sur Select | `$FF84D3` / `$FF88D3`, prise d'écriture `$FF8400-$FF8BFF` | cœur (remplace la valeur du programme) | sur PS2 la roulette vient de Select ; la traduction la recopiait depuis Start | `HsfaRoulette`, `HsfaRouletteWrite*` | 11 |
| membres lus sur place | `szBurnHsfaArchive`, `HsfaZipMembre` | cœur | un zip complet par jeu, sans charger 700 Mo en mémoire | `cps_hsfa.cpp`, `libretro.cpp`, `burn.cpp` | 5 |
| image 16:9 | 448 × 224, `-DHSFA_WS` | — | le décor existe au-delà des 384 px | `d_cps2.cpp` (`HSFA_SCRW`), `Makefile.hsfaws` | 2 |
| mélange des objets | `$804220-$80423F` (mode par palette OBJ), `$804240` (mode des objets dont le mot X brut a le bit 12) ; modes 0-5 | programme (EFFET_W des persos MAX, table RAM `$FF7F00`) | la PSP dessine des effets en additif, décidé par objet ; le CPS2 n'a pas de transparence | `Cps2ObjDraw` (`cps_obj.cpp`), `nCpsBlend` | 14 |
| ombres transparentes | option DIP A bit 7 (par défaut), `HSFA_OMBRES` | cœur | ombres à 75 % comme sur PSP ; règle par code de tuile car la palette 0x14 sert aussi au décor | `Cps2ObjDraw` | 15 |
| format d'écran du cœur 16:9 | option `fbneo-hsfa-format` (« Screen format (fill height) ») : **option de sortie vidéo, pas un registre** | cœur (réglage du joueur) | remplir la hauteur d'un écran moins large que 16:9 en rognant les côtés du décor élargi | `libretro.cpp`, `retro_common.cpp` | 16 |

Les numéros de patch sont ceux du tableau de [`patches/fbneo/README.md`](../../patches/fbneo/README.md).

### 5.1 La liste d'objets et les emplacements

Sur PS2, un objet porte un code **local** au fichier graphique chargé dans un **emplacement**. L'emplacement est
donné par les bits 13-15 de Y. `HsfaEmplacements` choisit la table de chaque emplacement à chaque conversion :

| emplacement | table | d'après |
|---|---|---|
| 0 | banque commune | `commun=` |
| 1 | décor | entrée `plan2` |
| 2, 3 | persos de J1, J2 | id du perso `$FF8503`, `$FF8903` → ligne `perso` de la carte |
| 4 | fichier graphique de la scène | pointeur d'animation (`ptr_anim=`) → ligne `anim` ; nul → `gfx_intro=` |
| 6, 7 | joueurs 3, 4 | seulement si `$FF8C01` / `$FF9001` ≠ 0 |

`HsfaEclater` découpe chaque objet en tuiles 16 × 16, traduit chaque code, et range au plus 1 023 tuiles. Une entrée
écrite plus de 3 images avant est ignorée (reste d'un écran précédent). La liste convertie est écrite **dans les deux
banques d'objets** (§103 du journal).

**Chargement différé (LAT4)** : quand le fichier de l'emplacement 4 change, le nouveau fichier attend qu'aucune
liste de l'image n'ait plus d'objet de l'emplacement 4, 10 images au plus (`lat4_max=`). Sans cela, le grand
portrait du face-à-face d'Upper montrait 5 images de tuiles de l'écran VS ([PORTRAITS](../rapports/PORTRAITS.md)).

### 5.2 Les plans : deux modes

- **SFA3 (mode 1)** : le programme écrit des codes de tuiles PS2 en mémoire vidéo. Le cœur garde la valeur brute
  (`Raw90`) et écrit le code arcade, lu dans `plan1` / `plan2` / `f312`. Si le jeu change la base d'un plan
  (`$804102-$804107`), tout le plan est reconverti. C'est `banc_plans.lua` porté en C++.
- **Upper, Hyper (mode 2)** : les décors PS2 sont des tuiles à part (`hsfa_plans.bin`, dans `hsfa_gfx.bin`). Chaque
  plan reçoit une base (`$804200-$804205`) ; le code de la tilemap devient un indice local à cette base. Le cœur
  écrit `300,340,3a0` à la 1ʳᵉ image. Dans `ro9a`, le programme bascule lui-même vers `400,440,4a0` pour les écrans
  d'Upper. FBNeo redessine les plans à chaque image : il suffit de mettre `nCpsGfxScroll` à jour quand la valeur
  change (l'équivalent du `mark_all_dirty` du fork). `HSFA_PLANS_LOG=<fichier>` journalise chaque changement.

### 5.3 La carte 68K vue par le programme traduit

| plage | contenu |
|---|---|
| `$000000-$3FFFFF` | ROM programme (pleine ; seule zone où du code s'exécute) |
| `$400000-$40000F` | registres d'objets CPS2 |
| `$410000-$617FFF` | trou T1 (2 080 Ko) |
| `$618000-$619FFF` | RAM partagée QSound (boîte aux lettres) |
| `$61A000-$65FFFF` | trou T2 (280 Ko) |
| `$660000-$667FFF` | RAM en plus (piles du portage) |
| `$668000-$6FFFFF` | trou T3 (608 Ko) |
| `$700000-$70FFFF` | mémoire d'objets (écriture convertie) |
| `$710000-$7FFFFF` | trou T4 (960 Ko) |
| `$800000-$80FFFF` | ports, registres CPS-A / CPS-B, registres HSFA `$804200` ; `$808000-$80FFFF` gardés pour l'avenir |
| `$810000-$8FFFFF` | trou T5 (960 Ko) |
| `$900000-$92FFFF` | mémoire vidéo |
| `$930000-$93FFFF` | trou T6 (64 Ko) |
| `$940000-$EFFFFF` | blocs externes (`$A00000-` pour SFA3 et Upper) |
| `$F00000-$FAFFFF` | variables du portage (PORT_RAM) : **non mappées** ; le portage s'accommode de lectures à 0 (mesuré sur `ro9a`) |
| `$FB0000-$FEFFFF` | trou T7 (256 Ko) |
| `$FF0000-$FFFFFF` | RAM de travail ; A5 = `$FF8000` |

Les trous ne sont servis que si le zip contient `hsfa_trous.bin` (seul `sfa3hahsfa` le déclare). Un pointeur 68K vers
un trou ou un bloc externe doit porter l'étiquette `$01xxxxxx`, que le bus de 24 bits ignore
([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §B.1).

## 6. Son

Une commande posée par le programme (`$61801F = 0`) suit cet aiguillage :

1. **carte musique** (Hyper, si le zip contient ses membres) : code ZERO ou ZERO 2 connu → le pilote d'origine le
   joue, le Z80 principal reçoit `FF05` ;
2. **flux** (selon le DIP A) : musique de la table → flux ADX ou Ogg, le Z80 reçoit `FF05` ; `FFxx` (arrêt, fondus)
   s'applique au flux et passe au Z80 ;
3. **rejeu** (Hyper) : son de SFA1 / SFA2 → 2ᵉ QSound, le Z80 reçoit un code vide ou un `ALIAS` ;
4. **Z80 principal** : tout le reste, sans changement.

Pourquoi `FF05` : un code inconnu du Z80 laisserait sa musique continuer, et `FF00` couperait aussi les voix
([FLUX](../rapports/FLUX.md) §1.2).

| source | cadence | gain | état sauvegardé |
|---|---|---|---|
| QSound principal (FBNeo) | celle de FBNeo | `Cps2Volume / 39` | oui (FBNeo) |
| flux | fréquence du fichier, rééchantillonnée vers la sortie | 0,26 × `HSFA_FLUX_VOL` % | bloc `HsfaFlux` (si le lecteur est actif) |
| 2ᵉ QSound (rejeu) | 24 038 Hz, horloge de 60 MHz datée par les cycles 68K | `Cps2Volume / 39` | blocs `HsfaRejeu`, `HsfaQs2` (toujours présents pour Hyper) |
| carte musique | Z80 8 MHz, IRQ 250 Hz ; QSound 24 038 Hz | `Cps2Volume / 39` × gain de la table | bloc `HsfaMusique` + « Z80 #2 » |

Les flux Ogg sont décodés par stb_vorbis en mémoire ; un anneau de 2,7 s évite tout `seek` au run-ahead. La boucle vient
des commentaires `LOOPSTART` / `LOOPEND` ([PLAN-VORBIS](../rapports/PLAN-VORBIS.md)).

## 7. Options

**Options du cœur** (RetroArch : Options du cœur → commutateurs DIP) :

| DIP | réglage | valeurs |
|---|---|---|
| A | `PS2 music (ADX streams, Y_DATA.BIN)` | `Off` / `Missing tracks only` (défaut SFA3, Upper) / `All tracks` (défaut Hyper) |
| A, bit 7 | `Transparent shadows (PSP)` (patch 15) | activé par défaut ; ombres en noir à 75 % |
| B-E | `Option: Difficulty`, `Damage level`, `Timer speed` (dont `Infinity`), `Speed select`, `Max round`, `VS mode (1P/2P)`, `Join in` (SFA3, Upper) | `Game default` = rien n'est écrit |
| F-H | 17 `Extra option: …` (une page d'EXTRA OPTION par DIP, un bit par réglage) | 1ʳᵉ valeur = bit à 0 |

Les réglages sont écrits à chaque fin d'image passée au menu des modes : ils prennent effet au prochain passage par ce
menu. Clé RetroArch, par exemple : `fbneo-dipswitch-sfa3hhsfa-Option__Timer_speed`. Détail des octets :
[OPTIONS](../rapports/OPTIONS.md) §1.2.

**Cœur 16:9 seulement** : option `fbneo-hsfa-format`, « Screen format (fill height) » (Off par défaut, 4:3, 3:2,
14:9, 16:10, 5:3, 16:9). Elle rogne les côtés à la sortie vidéo pour remplir la hauteur de l'écran (patch 16).

**Variables d'environnement** (PC, essais seulement ; jamais lues sur console) :

| variable | effet |
|---|---|
| `HSFA_LAT4=0`, `HSFA_LAT4_MAX=<n>` | ancien changement immédiat de l'emplacement 4 ; délai maximal |
| `HSFA_OPTIONS=0` | aucune écriture des options |
| `HSFA_NOROUL=1` | `$FF84D3` / `$FF88D3` toujours à 0 (= `NOROUL` du banc) |
| `HSFA_PLANS_LOG=<f>`, `HSFA_STATS=1` | journal des bases de plans ; statistiques des listes d'objets |
| `HSFA_FLUX=<0-2>`, `HSFA_YDATA`, `HSFA_FLUX_TABLE`, `HSFA_FLUX_VOL`, `HSFA_FLUX_LOG` | mode imposé, sources, volume, journal du flux |
| `HSFA_REJEU=0`, `HSFA_XDATA`, `HSFA_REJEU_TABLE`, `HSFA_REJEU_LOG`, `HSFA_REJEU_SEUL=1` | rejeu coupé, sources, journal, sortie du 2ᵉ QSound seul |
| `HSFA_MUSIQUE=0`, `HSFA_MUSIQUE_DATA`, `HSFA_MUSIQUE_TABLE` | carte musique coupée, sources |
| `HSFA_OMBRES=0/1` | ombres transparentes forcées (prioritaire sur le DIP) ; `0` pour comparer à une référence antérieure |
| `HSFA_OBJMIX=oo:m[,…]`, `HSFA_MIX_LOG=<f>` | registres de mélange imposés au reset ; journal de leurs changements |

## 8. États de sauvegarde

`HsfaScan` ajoute l'état d'HSFA à celui de FBNeo : copies de la liste d'objets (`HsfaOmbre`, `HsfaAge`, `HsfaConv`,
`HsfaConvOk`), mémoire vidéo brute (SFA3), compteur d'images, emplacement 4, bases de plans, flux, rejeu et carte
musique. Pour Hyper, les blocs du rejeu et de la carte sont **toujours présents** (vides si inactifs) : un état se
recharge avec ou sans les données de son. Les patchs qui ajoutent des variables d'état (LAT4, rejeu, carte musique)
rendent les états des cœurs plus anciens probablement illisibles.

## 9. Plates-formes

| cible | construction | remarque |
|---|---|---|
| Linux x86_64 | `make -j4 SUBSET=hsfa REGEN_HEADERS=1` dans `src/burner/libretro` | `SUBSET=hsfaws` : cœur « FinalBurn Neo HSFA Widescreen » |
| Android arm64-v8a | `NDK=<ndk r28c> FBNEO=<arbre> tools/android/build_android.sh` | `ndk-build` ne régénère pas les en-têtes : lancer d'abord `make SUBSET=hsfa generate-files` |
| ROCKNIX (RK3326) | `FBNEO=<arbre> tools/rocknix/build.sh hsfa\|hsfaws` | glibc ≤ 2.38, `rocknix_compat.h` |
| Windows x64 | `tools/windows/build_win.sh <arbre> [hsfa\|hsfaws\|tous]` | MinGW-w64, `LIBS=-static` |

Chaîne complète et commandes vérifiées : [`patches/fbneo/README.md`](../../patches/fbneo/README.md#construire). Le
16:9 garde les mêmes pilotes et les mêmes zips ; FBNeo recentre plans et objets (`nCpsGlobalXOffset = 32`).

## 10. Validation et outils d'essai

**`hsfa/hsfa_run.c`** : lanceur libretro sans fenêtre. Il rejoue les mêmes entrées que `jeu.lua` du banc, écrit
journal, captures et WAV.

```bash
gcc -O2 -I<fbneo>/src/burner/libretro/libretro-common/include -o hsfa_run <fbneo>/hsfa/hsfa_run.c -ldl -lm
NF=9000 SNAPS=300,600 OUTDIR=snap OUT=journal.txt WAV=son.wav SYSDIR=sys \
  INPUTS="100-106::IN0:Coin 1;200-206::IN0:1 Player Start" ./hsfa_run fbneo_hsfa_libretro.so sfa3hsfa.zip
```

Autres variables : `PILOTE=hyper` (tournée VERSUS d'Hyper : `LISTE`, `MODEJEU`, `CONTOURNE_E`…), `PILOTE=arcade`
(partie Arcade de `ro9a`), `STATETEST=<image>` (sauvegarde, restauration, comparaison image et son), `CPUSPEED`,
`HSFA_VARS="clé=valeur;…"` / `HSFA_VARS2` + `HSFA_VARS2_IMAGE` (options du cœur, changées en cours de partie).

**`scripts/validation/nonreg_coeur.sh`** (§162) : mêmes parties scriptées (SFA3, Upper, Hyper) jouées par un cœur de
référence et par le cœur à tester, sur les mêmes zips. Captures, journal du jeu, journaux du rejeu et des flux, WAV
comparés ; attendu : `IDENTIQUE` pour chaque jeu, en 20 à 30 s sur PC.

```bash
HSFA_WORKSPACE=<workspace> COEUR=<nouveau.so> REF=<reference.so> ZIPS=<dossier des 3 zips> \
  scripts/validation/nonreg_coeur.sh
```

Il dépend encore de `fb.sh` et `hsfa_run` d'un dossier de travail (`work/agent_fbneo_rejeu/tests/`), hors dépôt.

**Ce qui a été validé** (détail dans les rapports) : SFA3, journal d'attraction identique à MAME image par image sur
8 000 images (§136) ;
Upper identique au pixel après l'image 1656 ; Hyper : même déroulement que le fork sur une tournée VERSUS de
13 000 images ([FBNEO-HYPER](../rapports/FBNEO-HYPER.md)) et 151 VERSUS sur 151 (§154) ; rejeu : mêmes décisions que
le fork, au ms près ([REJEU-FBNEO](../rapports/REJEU-FBNEO.md)) ; `ro9a` : partie Arcade complète, bascules de banque
aux mêmes images que le banc ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md)). Le 2026-10-18, un cœur reconstruit
depuis `af5d3f3` et les patchs publiés donne `IDENTIQUE` contre le cœur de l'arbre de référence sur les trois jeux.

## 11. Écarts connus

- **Hasard** : le tirage du programme dépend du nombre de cycles 68000 par image et de la phase du Z80. Adversaires,
  démonstrations, phrases d'annonce et roulette peuvent différer de MAME, avec des décalages de 1-2 images
  ([HASARD](../rapports/HASARD.md)). À entrées égales, `HSFA_NOROUL=1` est nécessaire pour comparer Hyper au banc.
- **QSound principal** : celui de FBNeo. Après restauration d'un état, son rendu diffère légèrement (phase du
  rééchantillonnage non sauvegardée par `QscScan`, déjà vrai sans HSFA ; [REJEU-FBNEO](../rapports/REJEU-FBNEO.md)
  §3.7). Cette émulation est celle de superctr (haut niveau, déduite du code du DSP) ; MAME émule le DSP lui-même
  depuis la 0.196 : comparer le son au bit près dans une même implémentation, par tolérance entre le fork et le cœur
  ([recherche C §1.2](../rapports/recherche/C-TECHNIQUE-METHODE.md)).
- **Flux** : une commande prend effet au début du tampon son de l'image (≤ 17 ms d'avance) ; fondus à 60 Hz en temps
  de son ; le volume numérique CPS2 (`$804030`) ne s'applique pas au flux ([FLUX](../rapports/FLUX.md) §5).
- **Carte musique** : elle s'active dès que le zip contient ses membres, quel que soit le DIP A ; l'option du cœur
  « ZERO / ZERO 2 music » prévue par le plan n'existe pas encore. Le libellé du DIP A dit « ADX » mais vaut aussi
  pour l'Ogg.
- **Emplacements 2 et 3** : ils changent de table tout de suite (aucun défaut vu, [PORTRAITS](../rapports/PORTRAITS.md)
  §5).
- **16:9** : bande de 32 px aux butées de caméra de certains décors, objets coupés à la limite 4:3, écrans hors combat
  incomplets (§139). Les décors widescreen injectés sont un patch à part, hors chaîne.
- **`Cps2Turbo`** (surcadençage de FBNeo) n'est pas repris : format différent du fork (§136).
- **En-têtes générés** : `REGEN_HEADERS=1` écrit littéralement `" HSFA_SUFFIXE "` dans les commentaires de
  `gamelist.txt` et `driverlist.h` (cosmétique ; [FBNEO-HYPER](../rapports/FBNEO-HYPER.md) §5).
- **Prototypes** : `sfa3hahsfa` et `hsfa_trous.bin` servent aux essais de `ro9a` ; la banque de données commutée
  (`$804210`) est seulement chiffrée ([COEUR-BANQUES](../rapports/COEUR-BANQUES.md) §B.2).

## Glossaire

| terme | sens |
|---|---|
| **CPS2** | carte arcade Capcom : 68000 à 11,8 MHz, Z80 pour le son, puce QSound, ROM graphique (32 Mo pour SFA3) |
| **CPS-A / CPS-B** | les deux puces vidéo de la CPS ; leurs registres sont en `$804100` / `$804140` (bases de plans, défilements, priorités) |
| **Phoenix** | version d'une ROM CPS2 au programme déchiffré (`sfa3ud`) ; HSFA en part |
| **QSound** | puce son des CPS2 (échantillons, 16 voix + 3 ADPCM, écho) ; ici émulée en HLE (sans ROM de DSP) |
| **Z80** | processeur son : il exécute le « pilote son » qui transforme une commande en écritures QSound |
| **boîte aux lettres** | RAM partagée `$618000` : le 68000 y pose un code de son, le Z80 le lit |
| **scroll1-3, plan** | les trois couches de décor en tuiles (8 × 8, 16 × 16, 32 × 32), décrites par des tilemaps en `$900000` |
| **objet** | sprite : élément mobile (persos, effets, textes) décrit dans la liste d'objets `$700000` |
| **tuile** | carré de pixels de la ROM graphique ; son **code global** est son rang dans la ROM |
| **banque** | ici : un fichier graphique PS2 (`f<N>`) et sa table code local → code global |
| **emplacement** | case de chargement d'une banque sur PS2 (0 commune, 1 décor, 2-3 persos…), notée par les bits 13-15 de Y |
| **A5** | registre de base des variables du jeu : `$FF8000` ; « `$A0(A5)` » = octet `$FF80A0` |
| **bloc externe** | données du module PS2 servies en ROM au-delà de 4 Mo (`ext_<adresse>.bin` → `hsfa_ext.bin`) |
| **PORT_RAM** | variables propres au portage, en `$F00000` ; non mappées dans le cœur |
| **flux** | musique enregistrée (ADX de CRI sur PS2, Ogg Vorbis pour les zips allégés), lue par blocs |
| **rejeu** | sons de SFA1 / SFA2 rejoués à partir des écritures QSound que leurs pilotes faisaient |
| **carte musique** | 2ᵉ Z80 + 3ᵉ QSound qui exécutent les pilotes son d'origine de SFA1 / SFA2 |
| **`X_DATA.BIN`, `Y_DATA.BIN`** | archives de l'Anthology PS2 : données (dont son SFA1 / SFA2), musique (AFS de flux ADX) |
| **AFS** | format d'archive de CRI : un index d'entrées, ici repris tel quel par `hsfa_flux.bin` |
| **DIP** | commutateur de réglage d'un jeu arcade ; RetroArch les montre dans les options du cœur |
| **état de sauvegarde, run-ahead** | photo complète de la machine ; le run-ahead en recharge une à chaque image pour réduire la latence |
| **mots échangés** | octets de chaque mot 16 bits inversés, format de rangement des ROM 68000 dans les zips |
| **banc** | le fork MAME `sfa3hx` et ses scripts Lua, outil de développement et oracle du cœur |
| **`ro3`, `ro5`, `ro9`, `ro9a`** | modules PS2 retraduits : SFA3, Upper, Hyper, Hyper + Arcade d'Upper greffée |
