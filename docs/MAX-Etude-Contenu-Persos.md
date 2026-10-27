# SFA3 MAX (PSP) — rétro-ingénierie du jeu, des persos et de leur contenu

*Documentation de référence, tenue à jour au fil de l’étude. Dernière mise à jour : 2026-10-02 (correction §5, PSP ↔ Upper, identifiants, §10 tranché).*
*Aucune donnée de jeu n'est versionnée : chaque outil lit les fichiers de l'utilisateur (voir §12).*
*Outils : `tools/max/` (et `tools/max/nature/` pour le §1).*

---

## 0. Contexte et objectif

**But de l'utilisateur** : un « SFA3 complet » réunissant tout ce que la série a ajouté :
SFA3 arcade (CPS2, set `sfa3u`) + ajouts d'**Upper** + ajouts d'**Hyper** (Anthology PS2) + ajouts de **MAX** (PSP).
Cible de jeu : handheld Android (Retroid), et une diffusion communautaire.

**Répartition du travail**

| Chantier | Où | Qui |
|---|---|---|
| Traducteur MIPS → 68K, Upper et Hyper sur CPS2, fork FBNeo | ce dépôt, `src/hsfa/` + `docs/journal/HANDOFF.md` | en cours |
| **Côté MAX** : ce que contient le PSP, comment l'extraire, le convertir, le chiffrer | **ce document**, `tools/max/` | étude menée à part |

Documents liés : dépôt public `Rickow/SFA3max-PSP-widescreen` (patch 16:9 du même jeu) · `HANDOFF.md` (traducteur).

---

## 1. Nature du portage MAX — un port C natif

**Question** : SFA3 MAX émule-t-il le CPS2, ou est-il du 68K recompilé comme l'Anthology ?
**Réponse : ni l'un ni l'autre — c'est un portage en C compilé nativement**, avec des assets refaits.
Outils : `tools/max/nature/`.

### 1.1 Preuve décisive : le banc de registres 68K émulé

La recompilation de l'Anthology garde les registres 68K **en mémoire**, dans le scratchpad
(`0x70001114` = A5, `0x70001124`/`0x1128` = D0/D1…). Chaque instruction 68K devient
« lire le registre en mémoire → opérer → réécrire ». Mesure (`regfile.py`, `regfile_base.py`) :

| | Anthology (Hyper SFA) | SFA3 MAX PSP |
|---|---|---|
| Accès mémoire à adresse fixe (`lui` + load/store) | **201 465** | **1 113** |
| Part des 6 adresses les plus utilisées | **83,6 %** (`0x70001110`–`0x1158`) | globales ordinaires, rien de dominant |
| Banc caché derrière `$gp` / un registre dédié | — | non (pas de `$gp` ; aucun registre de base concentré sur ≤ 16 cases) |

Code PSP = ABI C standard, valeurs en registres, `s0` = pointeur « objet courant » (52 602 accès
sur 632 déplacements distincts).

### 1.2 Données

ROM programme arcade (`sfa3.zip` : `sz3e.03c`, `sz3e.04c`, `sz3.05c`…`sz3.10b` ; **fichiers stockés en mots
de 16 bits inversés** — le texte `NELGSI H` redevient `ENGLISH` une fois remis en ordre) découpée en
**75 242 sondes** de 16 octets (`nature/probe_scan.py`), cherchées telles quelles (BE) et mots inversés (LE16) :

| Cible | Sondes retrouvées | Blocs contigus ≥ 128 o |
|---|---|---|
| Anthology `ee_std` (SFA3 recompilé) | ~20 000 | 1 162 (jusqu'à 8 Ko) |
| EBOOT PSP | 460 | 27 (≤ 928 o) ; 34 au seuil de 96 o |
| 313 `.pac` PSP (151 Mo) | quelques Ko par fichier perso | — |

`USRDIR` = 313 `.pac` + 51 `.at3` (ATRAC3) + 7 `.prx` + `dummy.bin` (10 Mo d'un seul octet = remplissage).
Aucune chaîne d'émulateur (68000, Musashi, Cyclone, QSound, Z80) ; « Hiroaki "X68k" Kondo » = crédit son.

### 1.3 Ce qui reste « arcade »

Structure dérivée du CPS2 : tilemaps 64 colonnes, calques 16/32 px, aire logique 384×224, objets pilotés
par des octets de routine indexant des tables de sauts, virgule fixe 16.16. Hypothèse la plus plausible
(non prouvée) : Capcom a traduit ses sources 68K en C.

### 1.4 Fausses pistes écartées

Trois signatures « génériques » de recompilation (accès octet `adresse^1`, `wsbh`/`wsbw`, masque 24 bits)
donnent ~0 **aussi sur le témoin Anthology** : non discriminantes, ne pas les réutiliser.

---

## 2. Roster et fichiers de persos

Roster lu dans l'EBOOT (table de noms vers `0x1fa544`, **jamais une liste fournie à la main**) : **38 persos**.
Face à l'Upper de l'Anthology (34 uniques), il manque **Eagle, Maki, Yun, Ingrid**, plus les modes console
(World Tour, Dramatic/Reverse Dramatic, Variable, Survival, défis…).

Fichiers : `PSP_GAME/USRDIR/eur/data/plXX_e.pac`, **43 fichiers**, table de pointeurs vers leurs noms
indexée par ID perso à **`0x1ff680`** (42 entrées). Identification **visuelle** par le nom affiché dans
la liste de coups (entrée [8]) → `tools/max/pl_mapping.json` ; images reproduites par `movelists.py`.

| ID | Perso | ID | Perso | ID | Perso |
|---|---|---|---|---|---|
| 00 | Ryu | 0e | Rolento | 1c | Vega |
| 01 | Ken | 0f | Dhalsim | 1d | Karin |
| 02 | Akuma | 10 | Zangief | 1e | Juli |
| 03 | Charlie | 11 | Gen | 1f | Juni (code = clone de Juli) |
| 04 | Chun-Li | 12 | Chun-Li (variante) | **20** | **Guile** |
| 05 | Adon | 13 | Gen (variante) | **21** | **Fei-Long** |
| 06 | Sodom | 14 | Sodom (variante) | **22** | **Dee Jay** |
| 07 | Guy | 15 | Balrog | **23** | **T.Hawk** |
| 08 | Birdie | 16 | Cammy | **24** | **Shin Akuma** |
| 09 | Rose | 17 | Evil Ryu | 25 | Balrog (variante) |
| 0a | M.Bison | 18 | E.Honda | **26** | **Eagle** |
| 0b | Sagat | 19 | Blanka | **27** | **Maki** |
| 0c | Dan | 1a | R.Mika | **28** | **Yun** |
| 0d | Sakura | 1b | Cody | **29** | **Ingrid** (+ `pl29r`) |

En gras : ajouts d'Upper (20-24) et de MAX (26-29). **Ces identifiants sont ceux de l'Anthology** : la table
« perso → banque » d'Upper (HANDOFF §51) donne `$20` Guile, `$21` Fei-Long, `$22` Dee Jay, `$23` T.Hawk, `$24` Shin
Akuma, `$25` Balrog (variante) — exactement les fichiers `pl20`–`pl25`. Eagle, Maki, Yun et Ingrid prendraient
naturellement **`$26`–`$29`**, en prolongeant cette table de 4 entrées (une banque de sprites chacun). Les listes de coups de Sakura et des 4 persos MAX sont
en japonais même dans les fichiers `_e` européens.

Recoupement avec la ROM arcade : chacun des fichiers `pl00`–`pl1f` contient des tables d'une **zone arcade
propre au perso**, croissante dans l'ordre des ID (`0x100080` → `0x144xxx`) ; `pl20`–`pl23` et `pl26`–`pl29`
≈ 0 (persos absents de SFA3 arcade). Les données persos du PSP sont donc **héritées du format arcade**.

---

## 3. Conteneur `plXX_e.pac`

```
+0x00  u32 n = 9                  nombre d'entrées
+0x04  u32 total                  = taille du fichier − 0x800
+0x08  n × (u32 type, u32 taille)
+0x800 données : entrées successives, chacune alignée sur 0x800
```
(`tools/max/plpac.py`)

| # | Type | Taille (Ryu / Ingrid) | Contenu | État |
|---|---|---|---|---|
| 0 | `0x00100000` | 18 905 / 82 951 | **frames** : grilles de tuiles, palettes, miroirs, ancres (§4bis) | ✅ |
| 1 | `0x00200000` | 611 681 / 1 425 669 | **tuiles** (§4) | ✅ |
| 2 | `0x00400000` | 960 / 1 536 | **palettes** 16 couleurs ABGR1555 (§5) | ✅ |
| 3 | `0x40000002` | 384 / 688 | en-tête de banque son Sony **PPHD** | identifié |
| 4 | `0x40008002` | 160 256 / 384 944 | corps de la banque : échantillons **VAG** (ADPCM) | identifié |
| 5 | `0x0000000d` | 1 024 | table d'enregistrements | à décoder |
| 6 | `0x00000011` | 28 276 / 38 820 | table d'offsets puis données (scripts ?) | à décoder |
| 7 | `0x0000000a` | 1 165 / 1 244 | enregistrements (liste de commandes ?) | à décoder |
| 8 | `0x10000e00` | 131 104 | texture GBIX/PVRT 256×256 = **liste de coups** (§6) | ✅ |

---

## 4. Tuiles : format et décodeur

### 4.1 Organisation de l'entrée [1]

`u32 offsets[n]` (le premier offset = `4·n` = fin de la table), puis `n` flux compressés, chacun
produisant **une tuile 16×16 en 4 bits par pixel** (0x80 octets, quartet bas = pixel de gauche).

### 4.2 Décodeur (portage exact de `FUN_000ceb6c`, `tools/max/maxtile.py`)

Tables lues dans l'EBOOT : `DIST` à `0x23a600` (128 o), `STEP` à `0x23a680` (8 o : `1,1,1,1,1,1,1,25`).

```
écrits = 0 ; a = 0 (adresse de sortie) ; bits = 0
tant que écrits < 0x80 :
    c = octet suivant
    si bits == 0 : ctrl = c ; c = octet suivant ; bits = 8
    si ctrl & 1 == 0 :                     # littéral
        sortie[a] = c ; a += STEP[a & 7] ; écrits += 1
    sinon :
        haut, n = c >> 4, c & 0xF
        si haut == 0 :                     # remplissage
            v = octet suivant ; écrire v (n+1) fois ; écrits += n+1
        sinon :                            # copie arrière
            s = a − DIST[((a & 7) << 4) + haut] ; copier n octets de s (s avance aussi par STEP)
            écrits += n
    ctrl >>= 1 ; bits −= 1
```

- **Disposition** : `STEP` écrit 8 octets puis saute de 25 ⇒ lignes de 8 octets au **pas de 32 octets**
  (la tuile est posée dans une texture de 64 px de large). `DIST` traduit une distance logique (1-15,
  dans la tuile linéaire à 8 o/ligne) en distance dans cette disposition.
- **Débordement** : la dernière copie peut dépasser 0x80 octets (le jeu écrit alors plus loin dans sa
  texture, sans effet) ⇒ prévoir un tampon plus grand et tronquer.
- **Validation** : **698 180 / 698 180 tuiles** des 43 fichiers décodées avec consommation **exacte** de la
  longueur de chaque flux (même méthode d'auto-cohérence que HSFA pour ses tuiles).
- Ce n'est **pas** le LZ de l'Anthology (`lz148778`) : 0/400 flux décodés avec lui (`lzc.py`).

---

## 4bis. Frames et sprites (entrée [0])

Outils : `tools/max/frames.py` (lecture), `render.py` (assemblage), `sprites.py` (rendus et analyse d'Ingrid).

```
En-tête : N enregistrements de 12 o, N = (premier offset) / 12
   u32 offset de la grille (dans l'entrée [0])
   u8  largeur, u8 hauteur        en CASES de 32×32
   u8  a (ancre x), u8 b (= 0)    ; u32 c (ancre y)
Grille : largeur × hauteur cases, ligne par ligne ; chaque case :
   0xFF                              case vide
   u16 big-endian k, u8 attr         4 tuiles 16×16 : k·4 … k·4+3, rangées EN COLONNES (haut-gauche,
                                     bas-gauche, haut-droite, bas-droite)
attr : 0x20 toujours posé · 0x80 miroir horizontal · 0x40 miroir vertical · bits 0-1 = sous-palette (+0 à +3)
```

Validation : chaque grille se termine exactement là où commence la suivante (Ryu 470/470, Ingrid 1812/1812) ;
le plus grand numéro de case × 4 = nombre de tuiles (Ryu : 3 170 × 4 ≈ 12 684) ; rendu visuel juste
(Ryu en garde, coup de poing ; frames de chute : sans les miroirs, le sprite est en puzzle).

| Perso | Frames | Cases par sous-palette | Frames à plusieurs sous-palettes |
|---|---|---|---|
| Ryu | 471 | 0 : 3 760 · 1 : 394 | 0 |
| Guile | 511 | 0 : 5 216 · 1 : 387 · 2 : 34 | 0 |
| Eagle | 723 | 0 : 6 333 · 1 : 1 074 · 2 : 478 | 0 |
| Maki | 727 | 0 : 6 340 · 1 : 328 · 2 : 400 | 0 |
| Yun | 870 | 0 : 6 349 · 2 : 1 621 | 0 |
| **Ingrid** | **1 813** | 0 : 3 866 · 1 : 3 414 · 2 : 56 · 3 : 3 813 | 0 |

Eagle, Maki et Yun suivent le schéma des persos arcade : le corps en sous-palette 0, les effets en 1 ou 2.
**Ingrid est un sprite composite** : ses frames forment des blocs par sous-palette —
0 = **haut du corps** (687 frames), 1 = **bas du corps** (687), 2 = poses complètes spéciales (8),
3 = effets (431). **Chaque pose = haut `k` + bas `k`** (même ancre sur 687 paires / 687 ; recomposition
visuellement parfaite : garde, coup de pied sauté, accroupie, fente). Chaque moitié a sa palette ⟹ jusqu'à
**32 couleurs par pose**, d'où ses 48 palettes.

**Conséquence pour la CPS2** : aucun blocage matériel — un objet CPS2 choisit sa palette, et les frames
arcade utilisent déjà un décalage de palette par case (Ryu : 394 cases en +1). Il suffira de **fusionner les
deux moitiés de chaque pose en une seule liste d'objets** (palettes +0 / +1) ; à vérifier : que le format de
frame du moteur 68K accepte des objets qui se chevauchent (a priori oui : c'est une liste d'objets).

## 5. Palettes et conversion vers la CPS2

- Entrée [2] : `n × 16` couleurs u16 **ABGR1555** (format natif du GE PSP : R = bits 0-4, V = 5-9, B = 10-14,
  bit 15 = alpha). 30 palettes par perso ; **48 pour Ingrid**.
- **Validation contre la CPS2 d'origine** (`cps2_tiles.py` : graphismes `sz3.13m`…`20m` décodés à
  l'identique de FBNeo via `cps2gfx.py`, 262 144 tuiles) :

| Tuiles comparées | Identiques | Même forme, couleurs renumérotées |
|---|---|---|
| PSP Ryu (`pl00`) | 0,1 % | **85,8 %** |
| PSP Guile (`pl20`, absent de SFA3 arcade) | 0,2 % | 13,2 % |

- La renumérotation est **fixe** (`validate_cps2.py`, analyse des paires d'index) : **index PSP `i` → index FBNeo
  `16 − i`, 0 → 0**, confirmée à 99-100 % sur Ryu, Ken, Sagat (même forme : 85,8 / 84,5 / 85,3 %). (Le décodeur FBNeo inverse les bits :
  `Separate(255 − x)` ⇒ ses index sont `15 − brut`.)
- ⟹ **Conversion PSP → CPS2 prouvée** : permutation d'index puis encodage planaire CPS2. Le découpage des
  sprites en tuiles est celui de la CPS2.
- Les ~14 % de tuiles de Ryu sans équivalent CPS2 : frames ou retouches propres aux versions console (à caractériser).

Volume pour les 4 nouveaux persos (tuiles uniques non vides × 128 o ; `inventory.py`) :

| Eagle | Maki | Yun | Ingrid | Total | Réf. Ryu / Guile |
|---|---|---|---|---|---|
| 1,82 Mo | 1,66 Mo | 2,00 Mo | 2,25 Mo | **~7,7 Mo** | 0,86 / 1,08 Mo |

Couleurs : toutes les tuiles sont en 4 bpp ⇒ ≤ 16 couleurs, **compatible CPS2 par construction**.
Ingrid (48 palettes, 1 813 frames) : sprite composite en deux moitiés, chacune dans sa palette — voir §4bis.

### ✅ Constat initial « 12 % / 5 % » : faux négatif, corrigé (HANDOFF §45)

Une première mesure concluait que les tuiles de l'Anthology ne recoupaient la CPS2 qu'à 12 % (`ro3`) / 5 % (`ro5`).
**C'était faux**, pour deux raisons établies par HSFA (§45) : l'Anthology stocke les **valeurs brutes** de la ROM
(FBNeo affiche `15 − brute`), alors que la comparaison forçait `0 → 0` ; et `gfx.py` lisait les tuiles non
compressées comme des 8×8. `ro_tiles.py` utilise désormais `anthgfx.py` (unités CPS2 de 16 lignes, espace FBNeo,
tous les conteneurs). Mesure refaite (`validate_cps2.py`) : **100 % des unités de `ro3` sont des tuiles CPS2
exactes de SFA3** ; `ro5` en partage 81,6 % (le reste = ajouts d'Upper). La conversion PSP → CPS2 n'était pas
concernée : côté PSP comme côté FBNeo, le transparent vaut 0, et la permutation `i → 16 − i` en tient compte.

### PSP ↔ Upper : même art, au pixel près (`cmp_tiles.py`)

Tuiles PSP converties en espace FBNeo (`i → 16 − i`), cherchées telles quelles dans les conteneurs d'Upper (`ro5`) :

| Perso | Identiques dans Upper | | Perso | Identiques dans Upper |
|---|---|---|---|---|
| Guile | **74,0 %** | | Eagle | 2,2 % |
| Fei-Long | **89,2 %** | | Maki | 12,8 % |
| Dee Jay | **85,6 %** | | Yun | 7,2 % |
| T.Hawk | **84,1 %** | | Ingrid | 0,4 % |
| Balrog (variante) | 71,1 % | | | |

Les ajouts d'Upper ont **le même art et le même découpage** sur PSP et dans l'Anthology ; les 4 persos de MAX sont
de l'art nouveau. Ryu (1,4 %) et Shin Akuma (2,5 %) sont bas pour une raison de couverture : leurs banques
(`e355`, `e357`) ne sont pas dans les conteneurs extraits localement — Ryu PSP ↔ CPS2 complète = 85,8 % (§5).

---

## 6. Liste de coups (entrée [8])

Texture GBIX+PVRT 256×256 ARGB1555 (R = bits 10-14). Le champ « type » vaut 1 (carré twiddlé en norme
Dreamcast) mais **les pixels sont linéaires** ; l'ordre de Morton donne une mosaïque. Contenu : bandeau du
nom, onglets, noms de coups et commandes. Le format GBIX/PVRT trahit une **ascendance Dreamcast/NAOMI** des assets.
Outil : `tools/max/pvr.py`.

## 7. Son (entrées [3] et [4])

Banque Sony : en-tête **PPHD** (on retrouve aussi `PPHD`, `PPVA`, `PPTN`, `PPPG` dans l'EBOOT) + corps
d'échantillons **VAG** (ADPCM, trames de 16 o). À convertir en PCM puis en échantillons QSound pour une
cible CPS2. Non décodé à ce stade.

---

## 8. Code des persos

### 8.1 Outil clé : les relocations

L'EBOOT n'est **pas strippé** : en-têtes de sections et relocations présents (`.rel.data` = 25 536 entrées,
`.rel.text`…). `tools/max/relocs.py` en tire la liste **exacte** des mots-pointeurs des données.
Sections utiles : `.text` `0x0`–`0x1f835c` · `.rodata` `0x1f8ff0` · `.data` `0x1fede0`–`0x2d4f18` · `.bss` 10 Mo.

### 8.2 Tables par perso

23 tables de **42/43 pointeurs** contigus (une entrée par ID) : ~20 vers des structures de données par
perso, la table des noms de fichiers (`0x1ff680`) et **la table des routines racines `0x215040`**.

### 8.3 Un module contigu par perso (`tools/max/modules.py`, sortie de référence `modules_resultats.txt`)

Les 42 racines sont **rangées dans l'ordre des ID** à travers `.text` (`0xe9724` → `0x1caf0c`, 902 Ko) ⇒
un module (unité de compilation) par perso ; 80-88 % de ses fonctions sont des **gestionnaires d'états
pointés depuis des tables de données**.

| Perso | Module | Fonctions | Fonctions moteur appelées | dont aussi utilisées par l'arcade |
|---|---|---|---|---|
| Ryu (réf.) | 18,5 Ko | 162 | 70 | 70 |
| Guile (Upper) | 12,7 Ko | 118 | 64 | 64 |
| Shin Akuma (Upper) | 26,4 Ko | 220 | 88 | 88 |
| **Eagle** | **26,0 Ko** | **202** | 106 | 55 |
| **Maki** | **21,4 Ko** | **168** | 97 | 54 |
| **Yun** | **27,4 Ko** | **220** | 108 | 57 |
| **Ingrid** | **~19,4 Ko** (borne par les données) | **145** | 42 | 21 |

- **4 persos MAX ≈ 95 Ko de MIPS, ~735 petites fonctions**, + **88 utilitaires moteur (~6 Ko)** qu'aucun perso
  arcade n'utilise (44 partagés par au moins 2 des 4 ; aucun utilisé par les ajouts d'Upper).
- **Les ajouts d'Upper n'utilisent que l'API moteur de l'arcade** (64/64, 60/60…) ; ceux de MAX en utilisent
  la moitié plus un jeu d'utilitaires propre ⟹ ils ont été écrits contre un moteur étendu (lignée GBA probable).
- Les modules appellent surtout le moteur (84-92 % des appels), peu eux-mêmes, presque jamais les autres persos.

---

## 9. Pièges rencontrés (à ne pas rejouer)

1. **`jal` du PRX = adresses relatives à 0**, relogées au chargement : cible = `imm26 << 2`. Ne PAS soustraire
   `0x08804000` (règle des sauts *injectés* par le patch widescreen, pas celle du code d'origine). Cette erreur a
   faussé une première série de mesures (cohésion « 0 % », fonctions « hors arcade » aberrantes) — corrigée.
2. **Le segment « exécutable » contient aussi les données en lecture seule** : utiliser les sections, pas le
   program header, pour borner `.text`.
3. **Suites de pointeurs ≠ tables par perso** : les premières détections (suites de 41-43 « pointeurs », ou
   ≥ 42) attrapaient des structures entrelacées (alternance 245/0 selon la parité de l'ID). Les relocations
   règlent la question.
4. **Suivre les appels depuis un perso finit par tout atteindre** (moteur commun) : la fermeture par appels ne
   mesure pas le code d'un perso ; l'ordre des racines dans `.text` si.
5. **PVRT type 1 ≠ twiddlé ici**.
6. **Débordement de la dernière copie** du décodeur de tuiles (tampon trop court = faux échecs).
7. **ROM programme arcade en mots inversés** dans les fichiers du set.
8. **Nommer un perso** : toujours depuis les données du jeu (liste de coups), jamais par déduction de l'ordre.

---

## 10. Porter le contenu HSFA dans MAX, plutôt que l'inverse ?

Deux architectures pour « tout réunir » :

- **A — base CPS2 / FBNeo** (plan actuel) : Upper et Hyper par le traducteur ; MAX par portage des 4 persos.
- **B — base MAX / PSP** : MAX contient déjà tout le roster d'Upper ; il faudrait y ajouter Hyper.

**Ce qui distingue vraiment les deux** : quel contenu doit **changer de famille de moteur**.
SFA3 arcade → Upper → Hyper forment une seule famille (même machine émulée, variables A5 d'Hyper à 77 %
celles de l'arcade) ; MAX est une autre famille (C natif, lignée console, API moteur étendue).

| | A (base CPS2) | B (base MAX) |
|---|---|---|
| Contenu qui change de famille | **4 persos MAX** : modules contigus, ~95 Ko, bornés et réguliers | **Hyper** : modification profonde du moteur (composant de ~1 Mo recompilé, 374 fonctions, 68 points de branchement) + menus (182 Ko) |
| Upper | à traduire (même famille ; traducteur à 97,6 %, HANDOFF §43) | déjà présent (roster), mais équilibrage/moteur console, pas arcade |
| Plateforme | fork FBNeo **obligatoire** (Upper dépasse la ROM gfx CPS2 de ~9 %, HANDOFF §49) ; banques Anthology = tuiles CPS2 exactes (§5, HANDOFF §45) | facile : caves MIPS éprouvées, module C (PSPSDK) possible, insertion de fichiers dans l'ISO déjà écrite, pas de plafond |
| Graphismes | conversion PSP → CPS2 prouvée | encodeur PSP à écrire (trivial : flux tout-littéral valide) |
| Mécanisme d'accueil | slots/palettes/tables CPS2 à étendre | **existe déjà** : des variantes de persos ont leur propre ID, module et fichier `pl` (Chun-Li, Gen, Sodom, Balrog) |

**Avis** : la plateforme B est nettement plus facile, mais le contenu qu'elle obligerait à déplacer (Hyper)
est le plus difficile à déplacer, car il est entremêlé au moteur de l'autre famille. L'architecture A ne
fait traverser que ce qui se déplace le mieux (des modules de persos autonomes). **Globalement, A est la
plus faisable.** Les deux réserves émises à l'origine sont levées : la ROM graphique d'Upper se construit à
partir des banques de l'Anthology (§5 corrigé, HANDOFF §45/§49), et la nature d'Hyper est tranchée ci-dessous.

**L'inconnue qui pouvait renverser l'avis est levée (HANDOFF §46)** : les « versions » d'Hyper sont un octet de
drapeaux par joueur (`$117` → `$D3(A6)`, transmis aux objets enfants) testé par `BTST` dans **~1 300 sites** du moteur.
Elles sont donc pilotées par le **code**, pas par des données ⟹ elles ne se déplaceraient pas mieux vers MAX.
**Base A (CPS2 / fork FBNeo) confirmée.**

---

## 10bis. Capcom Fighting Collection 2 — évaluée, écartée pour la cible CPS2

*Recherche du 2026-09-27 (question : faut-il acheter CFC2 pour le projet ?).*

**Ce que c'est** : le SFA3 Upper de CFC2 est la version **NAOMI** (processeur SH-4). La mise à jour gratuite du
7 août 2025 y a ajouté **Eagle, Maki, Yun, Ingrid** (EX Settings > Additional Characters), les modes
**MAZI / SAIKYO / CLASSIC** et des corrections (latence, jauge de garde des Custom Combos V-ISM).

**Accessibilité** (fil arcade-projects, moddeur HDemon, mai → novembre 2025) :
- les ROM de la collection s'extraient ; celle de SFZ3U est une image NAOMI « fortement réorganisée » ; une partie
  des changements a pu être reportée dans la ROM NAOMI d'origine (jouable, avec le son) ;
- mais « le moteur SFZ3U est caché dans le .exe », protégé par **Enigma Protector** ⟹ projet abandonné
  (notes publiées en novembre 2025) ;
- précédent sur la collection Marvel, empaquetée de la même façon : le son est sorti de l'image ROM (WAV, Ogg).

**Verdict pour la cible CPS2** : inutile.
1. Troisième famille de moteur (SH-4) : ni le 68K de l'Anthology traduit par ce projet, ni le C du PSP.
2. Les 4 persos sont déjà disponibles par le PSP (graphismes décodés et convertibles, code et données localisés).
3. Le seul apport propre — l'intégration des 4 persos dans le moteur d'Upper — est justement dans l'exécutable
   protégé, qu'on ne contournera pas (mesure technique de protection).

Intérêt résiduel : y jouer, ou s'en servir comme **référence de comportement** des 4 persos dans Upper pour
valider le portage. Projet voisin : NEON.Bitchi (recompilation NAOMI/Dreamcast d'Upper avec les assets de CFC2).
Signal utile : des joueurs réclament explicitement un **Upper + Hyper en CPS2 jouable sur Fightcade**.

Sources : [arcade-projects p.1](https://www.arcade-projects.com/threads/capcom-fighting-collection-2-street-fighter-zero-3-upper-sega-naomi-p-o-r-t.34097/),
[p.2](https://www.arcade-projects.com/threads/capcom-fighting-collection-2-street-fighter-zero-3-upper-sega-naomi-p-o-r-t.34097/page-2),
[p.3](https://www.arcade-projects.com/threads/capcom-fighting-collection-2-street-fighter-zero-3-upper-sega-naomi-p-o-r-t.34097/page-3) ·
[Push Square](https://www.pushsquare.com/news/2025/08/bonus-characters-in-street-fighter-alpha-3-upper-now-available-with-free-capcom-fighting-collection-2-update) ·
[game-extraction-toolbox #81](https://github.com/shawngmc/game-extraction-toolbox/issues/81) ·
[NEON.Bitchi](https://x.com/NEONBitchi/status/2101778371499921505) ·
[Capcom](https://www.capcom-games.com/cfc2/en-us/title/sf-zero3-upper/)

---

## 11. Suite (côté MAX) — plan révisé le 2026-10-02

**Ce que la récupération du 68K (projet HSFA) apporte à ce côté :**
- **un banc d'essai réel** : SFA3 traduit tourne dans MAME jusqu'au combat (HANDOFF §80, outils `mame/*.lua`) —
  on peut y injecter du contenu converti et le voir ;
- **les formats cibles** : banques de sprites des persos = sous-ensembles de tuiles CPS2 (§45), table
  « perso → banque » (§51), schéma de banques du fork (§48) ; **frames** de sprites de tous les persos dans
  le **fichier 289** de `X_DATA.BIN` (adresse fixe `0xA04000`, format « converti, à retrouver », §45/§75) ;
  **animations natives** dans les fichiers 290-311, un par perso (§75, `assets_natifs.py`) ;
- **les identifiants** : `$20`-`$25` communs avec le PSP ⟹ MAX en `$26`-`$29` (§2) ;
- **une pierre de Rosette de données** : Guile, Fei-Long, Dee Jay, T.Hawk existent sur PSP **et** dans Upper,
  avec le même art au pixel près (§5) ⟹ on peut apprendre les conversions de frames et d'animations sur eux.

**Étapes, dans l'ordre :**
1. ~~Décoder l'entrée [0] et trancher Ingrid~~ — **fait** (§4bis).
2. **Frames** : retrouver le format du fichier de frames de l'Anthology (celui d'Upper) en partant des frames
   PSP de Guile (ses tuiles étant identiques, on sait quels codes chercher), puis convertir les frames PSP.
3. **Animations** : même méthode entre les entrées PSP [5]/[6]/[7] et le fichier d'animation natif de Guile.
4. **Prototype visuel** : banque + frames + animations d'**Eagle** (structure standard, §4bis), affiché dans le
   banc MAME à la place d'un perso existant.
5. **Code** : porter les gestionnaires d'Eagle en 68K ; correspondance API moteur et champs d'objet apprise sur
   Guile (C du PSP ↔ 68K traduit d'Upper). Puis Maki, Yun, et Ingrid (composite, §4bis). Inclure les 88 utilitaires MAX.
6. **Son** : PPHD/VAG → PCM → échantillons QSound, tables du pilote Z80 à étendre.

**Dépendances côté HSFA** : renumérotation des banques dans le fork (§48) ; Upper tournant dans le banc MAME.
**Accès** : les fichiers d'Upper sont dans `X_DATA.BIN` sur disque à plateaux — lectures ciblées uniquement.

---

## 12. Reproduire

Prérequis : Python 3 + Pillow ; capstone pour `nature/` (venv du projet). Les fichiers de l'utilisateur se
désignent par variables d'environnement (détail et exemple : `tools/max/README.md`) ; les caches, qui contiennent
des données dérivées du jeu, vont dans `$SFA3MAX_CACHE` (défaut `~/.cache/sfa3max`), **hors dépôt**.

```bash
cd tools/max
python3 plpac.py                     # extrait les 43 plXX_e.pac de l'ISO (lecture seule)
python3 movelists.py                 # listes de coups + planche des noms (§2)
python3 inventory.py                 # palettes, tuiles, volume CPS2 (§5)
python3 validate_cps2.py             # CPS2 : même forme, permutation, unités Anthology exactes (§5)
python3 cmp_tiles.py pl20 pl26       # tuiles PSP retrouvées dans Upper (§5)
python3 sprites.py pl00 0 317        # rendu de frames (§4bis)
python3 sprites.py --ingrid          # structure d'Ingrid + poses recomposées (§4bis)
python3 modules.py                   # modules de code par perso (§8.3) — identique à modules_resultats.txt
cd nature
python3 regfile.py && python3 regfile_base.py     # banc de registres émulé (§1.1)
python3 probe_scan.py scan "$EE_STD" ee_std "$SFA3MAX_EBOOT" eboot   # sondes arcade (§1.2)
python3 probe_scan.py blocks && python3 xref_arcade.py            # blocs arcade de l'EBOOT et leurs consommateurs
```

Tous ces résultats ont été reproduits depuis un cache vide avant publication.
