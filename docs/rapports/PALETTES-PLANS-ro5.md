# Upper (`ro5`) : palettes et plans dans le banc

> Rapport versé dans le dépôt le 2026-10-24 depuis `work/agent_pal_ro5/PALETTES-PLANS-ro5.md` (copie anonymisée ;
> texte d'origine inchangé). Les chemins `work/…` et `<workspace>/…` désignent des dossiers de travail, hors dépôt.
> Note du 2026-10-04 ; suite donnée dans le journal §119-§120 (fork : une base par plan, `hsfa_plans.py`).

Note d'agent, 2026-10-04. Travail fait uniquement dans `work/agent_pal_ro5/`. Les dépôts, `scripts/untranspile`,
`work/mame`, `work/mame_ro5` et `mame-fork` n'ont été que lus. Rien n'a été commité.

Conventions : `fichier` = décalage dans `ro5_usa_prog68k.bin` ; `exéc.` = fichier + `0x1F0000` ; « 68K $xxxxxx » =
adresse dans le programme traduit (`carte_image.txt` de `work/mame_ro5`) ; « mips 0x… » = décalage fichier du code MIPS.

---

## En bref

| sujet | conclusion |
|---|---|
| Table des palettes par perso (homologue de `0x451230`) | **fichier `0x5072B0`** (exéc. `0x6F72B0`) : 40 décalages **signés** de 16 bits, 30 palettes par perso |
| Perso « terne » de la 1re démo | **Dhalsim (ID `$0F`) en couleur n° 4.** Ses couleurs sont **fidèles** : il porte la 5e couleur, celle à peau grise, identique octet pour octet à la ROM arcade (`$32FB94`). Ce n'est **pas un défaut du traducteur**. |
| Contrôle global des palettes | sur 12 000 images d'attraction, toutes les palettes de la mémoire sont retrouvées dans les données du module, avec les mêmes exceptions que SFA3 (palettes calculées) |
| Conteneur 32×32 d'Upper (homologue de `e312`) | **`e525`** (985 290 o, 4 576 tuiles) : 4 015 retrouvées dans la ROM SFA3, **518 absentes (0,25 Mo)** |
| Effet dans le banc | blocs magenta de scroll3 supprimés (titre, décors de Rose, Blanka…). Les codes manquants passent de 561-1 658 à 1-2 par décor. |
| Tuiles de plan absentes de la ROM SFA3 | 8×8 : 6 254 ; 16×16 : 5 401 (dont 2 358 objets de l'emplacement 1) ; 32×32 : 518 → **1,29 Mo** dans une ROM CPS2 (8×8 dupliquées). Elles sont surtout dans les **5 nouveaux décors** (`$40` `$42` `$44` `$46` `$4A`), plus les noms et les grands portraits des nouveaux persos. |
| Besoin du fork | la fenêtre des plans CPS2 fait 8 Mo, fixe (quart 1) ; il n'y reste que 0,25 Mo de tuiles vides. Il faut donc un **registre de base par plan** (ou des bits de banque dans le mot d'attributs). |

---

## 1. Palettes

### 1.1 Faits vérifiés

**Table moteur par perso.** `carte_donnees_ro3_ro5.json` (carto_ro5) apparie exéc. `0x641230` → `0x6F72B0` (8 votes
sur 8). Le contenu le confirme (`scripts/cherche_pal.py`, lecture directe) :

- 40 mots signés en fichier `0x5072B0` (SFA3 : 32 mots non signés en `0x451230`). L'écart entre deux blocs est de
  `0x3C0`, soit 30 palettes de 32 octets.
- IDs `$00-$1F` : mêmes blocs que SFA3. Les palettes 0-2 de chaque groupe de 5 sont identiques. Les palettes 3 et 4
  diffèrent pour la plupart des persos ; `$04`, `$06`, `$07`, `$12`, `$14` et `$17` ont plus de différences.
- `$20` Guile `+0x7490`, `$21` Fei-Long `+0x7850`, `$22` Dee Jay `+0x7C10`.
- **`$23` T.Hawk `-0x780` (`0xF880`) et `$24` Shin Akuma `-0x3C0` (`0xFC40`)** : leurs blocs sont placés **avant**
  la table, car `+0x7FD0` dépasserait la portée signée.
- `$25` = bloc de `$15` (Balrog), `$26` = bloc de `$00` (Ryu), `$27` = bloc de `$1E` (Juli).

**Table des palettes d'effets** (homologue de `0x457B70`) : fichier **`0x510540`** (exéc. `0x700540`). Elle a 40
entrées signées avec un écart de `0x3C0`, donc 30 palettes par perso (SFA3 : 24). Les IDs `$20-$24` ont des
décalages négatifs (`-0x1200` … `-0x300`). Elle est lue par 2 sites : mips `0x11677C` et `0x1CC0E8`.

**Sites qui lisent la table** (`scripts/sites_const.py ro5 6f72b0 50`). Il y en a 13 dans ro5, contre 19 dans ro3 :

- mips `0x4A98C`, `0x4B85C`, `0x116AAC`, `0x1916C4`, `0x1B4A90`, `0x1B4F40`, `0x1BD41C`, `0x1BD4BC`, `0x1CBB84`,
  `0x1CBFCC`, `0x2132C4` : tous traduits (68K `$006666`, `$0068DA`, `$02613E`, `$037D34`, `$03D818`, `$03D8B4`,
  `$03F126`, `$03F140`, `$041934`, `$041A28`, `$04C026`).
- Ces sites calculent avec `ADD.W` / `ADDA.W 0(A0,Dn.W)`, et le MIPS fait l'extension de signe par
  `dsll32/dsra32 16`. Les décalages négatifs de T.Hawk et de Shin Akuma passent donc.
- `0x406D14` (fonction `0x406CC0`) et `0x407DCC` (fonction `0x407990`) sont du **code C natif du portage** :
  pile `sq`, argument `a0`, appel du moteur `0x1CD640`. Ils prévisualisent une palette (palette 2, `0xA2C040`) à
  partir des tables `0x624B10` / `0x624B68`. Ils sont traduits à tort en 68K (68K `$09D8B6`, `$09DA72` : `LEA` puis
  restitution immédiate du registre prêté). ro3 a le même cas en `0x389990` (68K `$0915EC`). Voir l'hypothèse H3.

**Choix du groupe de palettes : Upper a changé la règle.**

- SFA3 : groupe = `((ism + 1) × 2 + couleur) × 5`.
- Upper (68K `$037D1C`, mips `0x19155C`) : `ANDI.W #7,D2 ; CMPI.W #6,D2 ; BLT ; MOVEQ #0,D2`, puis
  `D1 = D2 × 5 × 32` : **groupe = couleur (0-5)**. Upper a donc 6 couleurs, une par bouton, indépendantes de l'ism.
  Ailleurs on trouve aussi `CMPI.B #$6,$0129(A6)` (68K `$056CEA`) et `couleur × 5` (68K `$02637E`).
- L'octet de couleur est l'octet PS2 `$128` du joueur, rangé en 68K `$129(A6)` dans la traduction.

**Démo d'attraction.**

- Les persos, l'ism et la couleur viennent du tirage de 68K `$0076E8-$00775E` (mips `0x4FC5C-0x50038`) :
  couleur = `(ism + 1) × 2` (`ADDQ.B #1 ; EXT.W ; LSL.W #1`, puis `MOVE.B D7,$0129(A6)`), +1 en cas de miroir
  (`ADDQ.B #1,$0129(A6)` en `$007700`). Elle est recopiée en `$C0B8/$C0B9(A5)`, puis relue en `$007596`/`$00759C`.
- Relevé `prise_ism.lua` (écritures, avec le PC) : J1 = `$0F` (Dhalsim), ism `1`, couleur `4` ; J2 = `$22` (Dee Jay),
  ism `$FF`, couleur `0`.
- Palettes réellement chargées (`prise_pal.lua` + `cherche_pal.py`, images 2 600-3 700) : objets 0-4 = palettes
  **20-24** du bloc de Dhalsim, objets 5-9 = palettes 0-4 du bloc de Dee Jay. Le groupe 4 est donc bien appliqué.
- La palette 20 de Dhalsim (gris, rouge, orange : `captures/dhalsim_palettes_ro5.png`) est **identique** dans ro3
  et dans la **ROM programme arcade** (`sz3ud.03c…sz3.10b` concaténées, octets bruts, adresse `$32FB94` ; sa palette
  0 est en `$32F914`).
- L'arcade elle-même charge le groupe 4 pour ism 1 / couleur 0 : démo d'Akuma à l'image 2 800
  (`captures/arcade_pal.txt`).

**Contrôle de tout le circuit des palettes** (`prise_palall.lua` + `palall.py`).

- La mémoire de palettes complète (`$1800` octets à la base suivie sur `$80410A`) a été vidée toutes les 300 images
  sur 12 000. Chaque palette non vide a été cherchée dans les données du module (15 couleurs, luminosité masquée).
- Upper : tout est retrouvé, sauf objets 25 (en combat) et 19 (classement), scroll3 30 (écran CAPCOM) et les fondus
  de scroll2 de l'intro (base `$91E000`).
- **Le banc SFA3 (`roms_tr`) donne exactement les mêmes exceptions** (`captures/palall_ro3.txt`). Ce sont des
  palettes calculées, pas un défaut d'Upper.
- Les démos 2 et 3 (IDs `$05` contre `$03`, `$1D` contre `$09`) chargent elles aussi le bon bloc avec groupe = couleur.

### 1.2 Cause des « couleurs ternes »

Ce n'est pas une erreur. Le tirage de la démo d'Upper donne à Dhalsim la couleur 4, et la couleur 4 de Dhalsim est la
palette à peau grise de SFA3. Les données, le code de choix et la traduction concordent. Les palettes des décors
sont toutes retrouvées telles quelles. Pour la juger « fausse », il faudrait une capture PCSX2 de la même démo,
qu'on n'a pas.

### 1.3 Correctifs proposés (non appliqués)

1. **`scripts/untranspile/profils.py` ligne 35** :
   `palettes=0x5072B0,  # table moteur des palettes par perso (exéc. 0x6F72B0) : 40 décalages SIGNÉS, 30 palettes/perso`.
   Cette valeur ne sert qu'à l'injection des palettes MAX (`mame_test.py`), pas à l'attraction.
2. **`mame_test.py` lignes 279-280** : `struct.unpack_from('<32H', …)` doit devenir `'<%dh' % NID`, avec
   `NID = 0x28` pour ro5 (`assets_natifs.N_PERSO`) et `range(NID)` dans l'assertion.
   - Les décalages doivent être signés : sinon T.Hawk et Shin Akuma visent `+0xF880`.
   - **Piège** : sous ro5, le bloc de Ryu (ID 0, défaut de `MAX_PAL_ID`) est partagé avec `$26`, donc l'assertion
     échouera. Il faut tolérer les copies `$26`/`$27` (et `$25` ↔ `$15`) ou choisir un autre ID.
3. **`work/mame/compare_palettes.py` lignes 8-9 et 24** : pour ro5, table `0x5072B0`, 40 entrées signées, et
   **groupe = couleur × 5**. La couleur est l'octet traduction `+$129`, que `verif_palettes.lua` lit déjà par
   `0x128 ~ 1`.
4. Pour les persos MAX sur Upper : les 30 palettes du module (6 groupes de 5) correspondent directement aux couleurs
   0-5. Une seconde table par perso est à étendre : effets en `0x510540`, 30 palettes.

### 1.4 Hypothèses (non vérifiées)

- **H1.** Upper a 6 couleurs par perso, choisies au bouton. On l'infère du code (`CMPI #6`, groupe = couleur) ; la
  sélection n'a pas été vérifiée en jeu.
- **H2.** Le tirage des démos varie d'un lancement à l'autre. Dhalsim / Dee Jay sortait dans 6 lancements, puis
  Zangief / Sodom et Adon / Charlie sont apparus (`captures/pal3.txt`). La cause n'a pas été cherchée : graine,
  ordre des prises ?
- **H3.** Les fonctions natives `0x406CC0` / `0x407990` (ro5) et `0x388AB0` / `0x389990` (ro3) sont des écrans
  console (prévisualisation de couleur). Elles ne servent pas en attraction. Leur traduction parasite est sans
  effet tant qu'on n'y passe pas. Pour les classer natives, `natmiss` peut s'appuyer sur `sq …,sp` ou
  `jal 0x1CD640`. Défaut de classement **à confirmer** avant de toucher le traducteur.

---

## 2. Plans

### 2.1 Conteneur 32×32 d'Upper = `e525`

**Identification.** Dans le groupe d'Upper, les tailles suivent celles du groupe SFA3 avec un décalage :

| SFA3 | taille (o) | Upper | taille (o) |
|---|---|---|---|
| `e310` | 8 696 | `e523` | 8 696 |
| `e311` | 3 158 | `e524` | 3 158 |
| `e312` | 882 246 | `e525` | 985 290 |

`anthgfx.records` donne `[(2, 0, 4576, 48)]`, c'est-à-dire un seul enregistrement de tuiles 32×32 (`e312` :
4 096 tuiles).

**Table produite** : `banques/f525.bin`, par `banques_ro5.py 525` (copie de `banques.py` ; sortie dans ce dossier).

**Structure** (`scripts/analyse32.py`) :

- 4 576 indices : 43 vides, 4 015 retrouvés dans la ROM SFA3, **518 absents (0,25 Mo)**.
- Les indices `0-$D58` sont identiques à `e312` (3 416 indices au même rang). Ensuite viennent **504 tuiles
  insérées en `$D59-$F50`**, puis la suite de `e312` décalée de `+$1F8`.
- Autres absents : `$858`, `$D4E` (la variante de Karin connue, §89) et 12 indices en `$1157-$1195`.
- Rendu : `captures/scroll3_absents_e525.png` (enseignes « LAS VEGAS / PARK », ciels et montagnes, ville, palmiers,
  nuages, canyon).

**Banc** : `banc_plans.lua` (copie) lit `BANC_F32=f525.bin` dans `BANC_PLANS_DIR`, avec la même conversion
(`- $4000`, repli `+$B00`).

- Statistiques (`PLANS_STATS`) : `captures/stats_avant.txt` / `stats_apres.txt`. Codes scroll3 manquants par valeur
  de `$FF8100` : 561-1 658 avant, **1-2** après. Seules les scènes `$40-$4A` de l'intro gardent 65-119 manquants :
  ce sont les 518 absents.
- Captures : `captures/planche_demos_avant_apres.png` montre la disparition des blocs magenta de scroll3 sur l'écran
  titre et dans les décors de Rose (`$12`) et de Blanka / jungle (`$32`). `captures/planche_intro_avant_apres.png`
  montre la scène `$2E` aux rayons bleus, désormais correcte.
- Le logo du titre reste un aplat blanc : ce n'est pas scroll3 (hypothèse : objets d'Upper absents de la ROM SFA3).

**Correctif proposé** : `scripts/untranspile/banques.py`, ligne 26 (`MOD`) et ligne 149 (`if n == 312:`).

- Ajouter au profil `f32=312` (ro3) / `f32=525` (ro5).
- Remplacer le test par `if n == MOD['f32']:`, en écrivant toujours `f312.bin`, le nom attendu par
  `banc_plans.lua` (ligne 13).
- Puis lancer `MODULE=ro5 banques.py 525`. Autre solution : copier `agent_pal_ro5/banques/f525.bin` en
  `work/mame_ro5/banques/f312.bin`.

### 2.2 Tuiles de plan absentes de la ROM SFA3

Les compteurs `plan1 47 283 / 169 984` et `plan2 30 055 / 42 496` sont trompeurs. La mémoire de décor (`e353`
décompressé, 5,19 Mo) y est mesurée deux fois, en 8×8 **et** en 16×16. Or elle contient une **zone 8×8 (unités
`0-$1BFF`)** suivie d'une **zone 16×16** (`scripts/besoins_rom.py`). Mesure par unité de `0x80` o
(`couverture_decor.py`) :

| mémoire | unités | vides | retrouvées (16×16 ou 4×8×8) | introuvables |
|---|---|---|---|---|
| SFA3 `e256` | 35 328 | 613 | 35 209 | 119 (retouches connues, §89) |
| Upper `e353` | 42 496 | 888 | 35 470 | **7 026 (0,86 Mo)** |

**Structure de `e353` par rapport à `e256`** (`analyse_decor.py`) : `e353` = `e256` plus **7 182 unités nouvelles**
insérées en blocs. 275 d'entre elles existent ailleurs dans la ROM ; **6 907 sont introuvables**.

**De quels décors.** `$FF8100` vaut 2 × l'ID du perso dans les démos : Dhalsim `$0F` → `$1E`, Blanka → `$32`.
Pendant l'intro, chaque scène de nouveau perso pose `$40`, `$42`, `$44`, `$46` ou `$4A`, et ce sont exactement les
scènes qui citent les blocs nouveaux (`par_scene.py`). Chacune utilise un bloc contigu, sans recoupement :

| `$FF8100` (ID probable) | scroll1 (unités 8×8) | scroll2 (unités 16×16) | scroll3 (indices 32×32) | aspect (rendus) |
|---|---|---|---|---|
| `$40` (`$20` Guile) | `15FC-15FD` | `9635-96D4` (160) | `DE2-E31` (80) | ciel, montagnes, mur, base |
| `$42` (`$21` Fei-Long) | `15FE-165E` (85) | `96D5-98F6` (546) | `E32-EA7` (118) | ville, immeubles |
| `$44` (`$22` Dee Jay) | `165F-1766` (264) | `98F7-9AB9` (451) | `EA8-EF1` (74) | palmiers, plage, graffitis |
| `$46` (`$23` T.Hawk) | `1766-17B7` (82) | `9ABA-9CEF` (566) | `EF2-F31` (64) | canyon, cactus |
| `$4A` (`$25` (EX)Balrog ?) | — | `9274-942E` (443) | `D59-DC5` (109) | Las Vegas : enseignes, néons |

Unités nouvelles vues dans l'attraction : 2 601 (0,32 Mo). **Jamais vues : 4 581 (0,56 Mo)**, en rendus gris
`captures/decor_nouveau_non_vu_{1,2,3}.png` :

| plage | contenu |
|---|---|
| `117D-12F7`, `17B8-1B80` (8×8) | ciel nuageux, avions de chasse, foule (base aérienne de Guile ?) |
| `942F-9634` (16×16) | gros plans d'avions et de voiture |
| `9CF0-9DF2` | rochers et nuages |
| `9E18-9E62` | petits personnages de foule (décor en sprites ?) |
| `4740-475B` | police minuscule |
| `4F1E-4F71` | kanji |
| `4FD0-50F6` | plaques de noms GUILE / FEI-LONG / DEE JAY / T.HAWK / EVIL RYU / SHIN AKUMA |
| `5100-58C8` (1 992) | grands portraits des nouveaux persos |

Les plages `4740-58FF` (2 358 unités, 0,29 Mo) relèvent plutôt des **objets de l'emplacement 1** (HUD, noms,
portraits ; mémoire `e256`/`e353`, §83-84) que des plans.

**Volume à ajouter dans une ROM CPS2** (`besoins_rom.py`) :

| type | tuiles absentes | volume |
|---|---|---|
| 8×8 | 6 254 (6 239 distinctes) | 0,38 Mo à 64 o (dupliquées dans les deux moitiés, comme le rangement CPS) ; 0,19 Mo si appariées |
| 16×16 | 5 401 (dont 2 358 objets de l'emplacement 1) | 0,66 Mo |
| 32×32 | 518 | 0,25 Mo |
| **total** | | **1,29 Mo**, soit ≈ 10 600 tuiles 16×16 |

### 2.3 Ce qu'il faut au pilote MAME du fork

**Fait (lecture de `mame-fork/mame/src/mame/capcom/cps1_v.cpp`).**

- `gfxrom_bank_mapper` décale le code de `0` (scroll1), `1` (scroll2) ou `3` (scroll3) pour l'exprimer en unités de
  64 o.
- `mapper_cps2_table` n'accepte pour les **trois plans** que `0x00000-0x1FFFF` et les envoie sur la banque 1
  (physique `0x20000-0x3FFFF`). C'est **une fenêtre unique de 8 Mo, le quart 1** (octets 8-16 Mo). Hors fenêtre, le
  code vaut −1 et la tuile est transparente.
- `get_tile2_info` masque le code de scroll3 par `& 0x3FFF`.
- Portées : scroll1 = 65 536 × 64 o = 4 Mo ; scroll2 = 8 Mo ; scroll3 = 16 384 × 512 o = 8 Mo.
- Le mot d'attributs n'utilise que `0x1F` (palette), `0x60` (retournements) et `0x180` (groupe) : **les bits 9-15
  sont libres**.
- `quart1.py` : la fenêtre SFA3 ne contient que 2 076 tuiles 16×16 vides (0,25 Mo) et 5 084 doublons (0,62 Mo). Les
  1,29 Mo d'Upper n'y tiennent pas sans réorganiser la ROM.

**Proposition.**

1. **Registre de base par plan** (choix conseillé). Le fork ajoute trois registres de 16 bits, un par plan : scroll1,
   scroll2, scroll3. Leur adresse est à choisir hors de la plage CPS-A / CPS-B : `$804100-$80413F` et
   `$804140-$80417F` sont occupées, d'où par exemple `$804200-$804205`.
   - Calcul dans le pilote : `unité64 = (BASE_k << 16) + (code << shift_k)`, à la place de `mapper_cps2`.
   - Valeur par défaut `BASE = 2` (8 Mo), ce qui donne exactement le comportement d'origine.
   - Le code reste sur 16 bits (14 pour scroll3) ; seule la fenêtre bouge, par pas de 4 Mo ou plus fin.
   - Comme pour le registre de base des objets, le pilote invalide la tilemap (`mark_all_dirty`) quand la base change.
2. **Variante « fenêtres Anthology ».** Avec ces registres, le fork peut ranger **telles quelles** les mémoires
   d'Upper, dans l'ordre LOCAL, dans la ROM étendue :
   - scroll1 = zone 8×8 de `e353` (28 672 tuiles × 64 o = 1,75 Mo) ;
   - scroll2 = `e353` en 16×16 (42 496 × 128 o = 5,2 Mo) ;
   - scroll3 = `e525` (4 576 × 512 o = 2,2 Mo).

   Les codes locaux tiennent dans la portée : max 8×8 `$6FFF`, 16×16 `$A5FF`, 32×32 `$11DF < $3FFF`. Les bases
   deviennent constantes : **plus aucune table de renumérotation** ni prise d'écriture sur les tilemaps. Les bases
   `+$5600` / `+$B00` du portage disparaissent aussi. Coût : 9,2 Mo, contre 1,29 Mo pour les seules tuiles neuves.
   La même logique vaut pour SFA3 (`e256` / `e312`) et pour Hyper.
3. **Variante par tuile** (analogue des bits 13-15 du mot Y des objets). On prend 1 à 3 bits libres de l'attribut
   (ex. bits 13-15) comme bits hauts du code (`code | (attr >> 13) << 16`). C'est souple : les tuiles neuves et
   anciennes se mélangent dans un même plan. Mais la couche de conversion doit écrire aussi le mot d'attributs, et il
   faut vérifier que le portage n'y laisse rien (non vérifié).
4. Dans tous les cas : la **zone dynamique** (`$0000-$157F`, remplie à l'exécution pour les portraits, §84) suppose
   une région graphique **inscriptible** (tuiles marquées sales), ou des tables comme dans le banc.

---

## 3. Fichiers

### Scripts de banc

| fichier | rôle |
|---|---|
| `lance.sh <dossier> VAR=…` | banc d'Upper (MAME stock, `nice -n 19`), avec la copie `jeu.lua` |
| `jeu.lua` | copie : `BANC_PLANS` (défaut : copie locale de `banc_plans.lua`), `PRISE` / `PRISE_AVANT` |
| `banc_plans.lua` | copie : `BANC_F32`, `BANC_PLANS_DIR`, statistiques en lecture seule `PLANS_STATS` |
| `banques_ro5.py` | copie de `banques.py` : ro5 par défaut, sortie `banques/`, gère `525` |
| `prise_pal.lua`, `prise_palall.lua`, `prise_ism.lua`, `prise_decor.lua` | prises en **lecture seule** : palettes, écritures ID / couleur / ism avec PC, décor |
| `planche.py` | planches de captures |

### Scripts d'analyse (`scripts/`)

| fichier | rôle |
|---|---|
| `sites_const.py` | sites MIPS qui construisent une adresse |
| `cherche_pal.py`, `palall.py` | origine des palettes relevées |
| `analyse32.py`, `rendu32.py` | conteneur 32×32 |
| `analyse_decor.py`, `couverture_decor.py`, `attribue.py`, `par_scene.py`, `rendu_unites.py` | mémoire de décor, attribution aux scènes |
| `besoins_rom.py`, `quart1.py` | volumes et place libre dans la ROM |

### Tables (`banques/`)

| fichier | contenu |
|---|---|
| `f525.bin` | 32×32 d'Upper vers indice ROM |
| `plan1.bin`, `plan2.bin` | régénérées, identiques à celles de `mame_ro5` |
| `decor_e256.bin`, `decor_e353.bin` | mémoires de décor décompressées |
| `nouv353.npy`, `dec353.npy` | unités nouvelles et décalages |
| `absents525.bin` | indices 32×32 absents |

### Planches et captures (`captures/`)

| fichier | contenu |
|---|---|
| `planche_base.png`, `planche_attraction_base.png` | état initial (démo de Dhalsim, attraction complète) |
| `planche_demos_avant_apres.png`, `planche_intro_avant_apres.png` | avant / après `f525` |
| `dhalsim_palettes_ro5.png` | les 30 palettes de Dhalsim |
| `scroll3_absents_e525.png`, `decor_nouveau_*.png` | rendus des tuiles absentes |
| `palall_ro5.txt`, `palall_ro3.txt`, `pal1.txt`, `ism.txt`, `ism_arcade.txt`, `arcade_pal.txt`, `stats_avant.txt`, `stats_apres.txt` | relevés |
