# Greffe de la couche Arcade d'Upper dans Hyper (voie B) — étape 4

État au 2026-10-17 (soir). Reprise : lire `ETAT.md` (journal détaillé, commandes exactes), puis ce fichier.

## 1. Résultats

| point | état |
|---|---|
| rebase sur **v149** (PILE_LUI intégré) | **fait**. Sans variables de greffe, la copie `untranspile3/` redonne Hyper **`cb9b37b9`** (`constructions/temoin7`, `temoin8`, toutes ROM programme identiques) et Upper **`7898814c`** (`u5_temoin7`) |
| diff de la greffe contre v149 | `diffs/05-greffe-traducteur-v149.patch` (433 lignes, 7 fichiers). v149 + diff 05 = `untranspile3/`, vérifié fichier par fichier. Le diff 03 oubliait `assets_natifs.py` et `profils.py` |
| bloc de données avec les 40 journaux | 2,30 Mo de régions (1,19 Mo réellement lus par Upper) : ne tenait plus. **Disposition par fenêtres** (§3), marge ≈ 28 Ko |
| partie complète | e6a (v149, fenêtres) : Ryu ZERO 3, 60 manches en 60 000 images, fin, nouvelle partie |
| VERSUS d'Hyper | e6a contre le témoin v149 : mêmes choix sur 40 manches ; −1/−2 images (poses de victoire, déjà connu) ; ±48 images par endroits, **écart qui existe déjà entre les témoins v148 et v149** |
| base scroll1 des écrans d'Upper | **corrigée** (§4.1, §4.2) : elle bascule `$190/$191` comme dans Upper |
| planisphère | **non résolu** (§6). Cause localisée en partie ; mesures d'Upper à refaire en partie Arcade (piège §6.3) |
| fins de Ken ZERO et Sakura | **résolues** (construction figée `ro9a4_fige` = e6o) : Ken ZERO, fin de 4 930 images (Upper 4 976) ; Sakura ZERO 3, 6 398 (Upper 6 289) ; perso `$02` ZERO 2, 2 952 (Upper 2 965) ; Chun-Li ZERO 2 aboutit ; textes, générique et image finale corrects, fonds faux (§5) |
| fin de Ryu (ZERO 3, ALPHA) | **régression** : avec le script désormais conforme (`RELAIS_J=1`), ses objets `$4B` sont dessinés par le moteur d'Hyper et plantent (§5.3). À l'étape 3, sa fin « aboutissait » sur un script faux |
| défauts du traducteur | PILE_LUI : livré, validé, intégré en v149. « Tampons vidéo LSL #8 » : pas un défaut du traducteur (constante d'Upper, corrigée dans la greffe par `PAGES_RAM`) |

Constructions (non figées, `constructions/<nom>/b9/roms_ro9/sfa3ud/`) :

| nom | variables | `sz3ud.03c` | autres ROM programme (md5 concaténé) |
|---|---|---|---|
| temoin7 / temoin8 | aucune (Hyper seul) | `cb9b37b9` | `23f2015c` |
| e6a | RELAIS_J=0 (avant LUI_NEG) | `ced1e5c8` | `c3220342` |
| e6b | RELAIS_J=1, LUI_NEG | `fb0e9cd1` | `437800dd` |
| e6d | RELAIS_J=0, LUI_NEG, LUI_A5ST | `a8cdfbe9` | `9c62ac62` |
| e6e | RELAIS_J=1, LUI_NEG, LUI_A5ST | `22f353ef` | `b11334b9` |
| e6n | + PTR_ALIGNE, PTR_EXCLUS | `22f353ef` | `7b6fcce1` (bloc `f557d7f9`) |
| **e6o = `ro9a4_fige`** | + TYPES_GREFFE (`VARIABLES.txt`, `md5.txt` dans le dossier) | `89f483c1` | `7a9257cb` (bloc `bb6babf1`) |

`ro9a3_fige` (étape 3, `217fc51c…`) et `ro9a4_fige` (étape 4) sont figées. VERSUS de `ro9a4_fige` : mêmes choix que le témoin v149 sur 40 manches.

## 2. Rebase v149

- `diffs/v148-v149.patch` (`git diff v148 v149` du dépôt partagé : PILE_LUI et `nonreg_coeur.sh`) appliqué à
  `untranspile3/` ; sauvegarde `etape4/translate_u3_avant_v149.py`.
- Le témoin d'Hyper se construit **avec la redirection des voix** :
  `EXTRACT_MODULES=work/modules_son HSFA_SON_DONNEES=work/modules_son/son_donnees_ro9.bin`. Sans elles, on obtient
  `bb3dcf28`, ce qui n'est pas une régression.
- La greffe utilise déjà ce module (`MODULE_SOURCE` de `greffe3.py`).
- Avec PILE_LUI dans le traducteur, le contournement `CMP138` de la greffe est redondant mais sans effet ; il est gardé.

## 3. Disposition du bloc de données par fenêtres (`FENETRES=1`, défaut)

Contraintes :

- côté PS2, aucune valeur de `lui` de ro5/ro9 ne doit tomber dans le bloc. Valeurs présentes entre `$C0` et `$FF` :
  `$C0 $C3 $CC $D3 $DA $E7 $F0 $FF` ;
- côté 68K, les blocs externes de FBNeo vont de `$940000` à `$EFFFFF`. `$F00000` est la RAM du portage dans le fork.

| | morceaux |
|---|---|
| PS2 (exécution) | `$D60000-$D9FFFF`, `$DB0000-$E6FFFF`, `$E80000-$FBFFFF` (trous : `lui $DA` d'Hyper, son `$E7`) |
| 68K | `$D0C000-$EFFFFF` (après ext_c84000, qui finit en `$D0B188`) et `$C38000-$C83FFF` (après ext_940000 + son, qui finit en `$C32000` en v149 ; 24 Ko de marge) |
| correspondance | `d60000-da0000>d0c000`, `db0000-e70000>d4c000`, `e80000-f74000>e0c000`, `f74000-fc0000>c38000` |

Points de la disposition :

- Le trou du son ne coûte plus 64 Ko côté 68K.
- Aucune région ne traverse un changement de fenêtre (coupure dans `donnees2.bloc`).
- Assertions : fichiers anim (VBASE `$D20000`, 261 200 o) finis avant `$D60000` ; fenêtres hors ext_c84000 et au-dessus
  de la fin d'ext_940000 ; tout sous `$F00000`.

Code :

- `greffe3.py` : `FEN_PS2`, `FEN_68K`, `fenetres()` ;
- `donnees2.bloc` : liste de trous et coupures ;
- `translate.py` : `GRF_FEN`. Une adresse hors des morceaux, par exemple `$DAxxxx` d'Hyper, garde la conversion
  ordinaire, ce qui vaut aussi pour LEATAB ;
- `mame_test.py` : `HSFA_GREFFE_FEN="lo:hi:y,..."`, une plage de CONV et un `ext_<y>.bin` par suite contiguë en 68K.

**Marge : ≈ 28 Ko, la disposition est saturée.** Les décors d'Upper (plan GREFFE-DECORS : `$D10000-$EFFFFF`) n'y
tiendront pas. Propositions, de la moins à la plus coûteuse :

1. Récupérer les données d'Arcade **propres à Hyper**, devenues mortes dans ro9a (fins, textes, carte d'Hyper) dans
   ext_940000 (3 Mo). Il faut prouver qu'elles ne sont lues ni en VERSUS, ni en TRAINING, ni en attraction (journaux
   de lecture d'Hyper).
2. Mettre en commun les régions identiques à Hyper. Mesure : 134 Ko de régions entières retrouvées dans Hyper, dont
   108 Ko avec pointeurs masqués, donc peu de gain.
3. Banque de données dans le cœur : une fenêtre 68K commutée par un registre, comme `$804200` (§7). C'est la seule
   option qui passe à l'échelle (décors d'Upper, SFA1/SFA2).

## 4. Correctifs de la greffe

### 4.1 `LUI_NEG=1` (`outils/greffe.py`)

Upper 0x259190 fait `$C130 = (($C130 − $A20000) ^ $10000) + $A20000`. C'est la bascule de la page de scroll1.

- Le `lui $A2` était relogé (`$BA`), mais pas le `lui $FF5E` (= −`$A20000`).
- Conséquence : la base dérivait de `$18` pages à chaque bascule. On voyait des `o` bleus en fond et `$804102` valait
  `7e50/9750/ae50`.
- Correctif : un `lui` négatif additionné (`addu`) dont l'opposé est une adresse d'Upper est relogé comme
  −(adresse relogée). 1 site.

### 4.2 `LUI_A5ST=1` (`outils/greffe.py`)

`lui v1,$A2 ; … ; sw v1,$C130(A5)` : la valeur rangée en A5 venait d'un `lui`, mais la branche « accès A5 » masquait
son usage, et le `lui` n'était pas relogé.

- Effet : `$C130 = $A20000`, soit `$01AE6000` côté 68K.
- 9 sites (Upper 0x259000, 0x25CDC4, …).

### 4.3 `RELAIS_J`

Inchangé depuis l'étape 3 : relais ≤ 64 o greffés dans le moteur de fin et le flux Arcade. Défaut 1 dans
`greffe3.py`. Les constructions `RELAIS_J=0` servent aux vues.

### 4.4 Interrupteurs d'essai, tous à 0 par défaut

Ils étaient fondés sur des mesures de l'**attraction** d'Upper (§6.3) :

- `BASES_UPPER` ;
- `DECOR_CARTE` (`$100 = $10` : casse le décor de combat) ;
- `COUCHES_UPPER` (copie de 0x15ACB0 dans `plans_auto`) ;
- `CLEAR_UPPER` (0xC58C0 greffée, `force3.py`).

## 5. Fins

### 5.1 Méthode

`etape4/compare_script.py UPPER.txt RO9A.txt` compare le script de fin des deux jeux. Il lit les journaux `surv.lua`
de `$FF0034-$FF003B` : `$8034` est le pointeur, `$8038` la commande, `$803A` le paramètre (interpréteur Upper
0x2FBE8). Il affiche la première divergence. `etape4/octets68k.py` montre les mots 68K servis à une adresse.

Références d'Upper (oracle `tournee_greffe.lua`, mêmes images que les journaux `u_lu_*`) :

| perso | scène A | scène 8 | durée |
|---|---|---|---|
| Ken | 45 794 | 50 770 | 4 976 |
| Sakura | 41 411 | 47 700 | 6 289 |
| Ryu | 41 607 | — | — |

### 5.2 Causes trouvées et correctifs (défauts 1 à 3 cumulés dans e6o)

1. **Paires de mots de script relogées en pointeurs de code** (`etape2/donnees2.py`, `bloc`).
   - Exemple : `$0301 $0028`, soit le long PS2 `$00280301` (impair), était relogé comme code. Résultat :
     commande `$7494`, script décalé, `JSR T(PC,D1)` hors d'une table de 4 entrées, saut au milieu de la copie de
     0x53BD0, fin de Ken plantée à 18 037.
   - **`PTR_ALIGNE=1`** : un pointeur de code est un multiple de 4. 1 100 faux pointeurs en moins.
2. **Paire alignée** `$4200 $0030` (`$00304200` → 0x114200), script +550 de Ken.
   - **`PTR_EXCLUS`** : fichier `donnees/ptr_exclus.txt`, cases jamais pointeurs de code, alimenté par
     `compare_script.py`. 1 case pour l'instant.
   - Deux règles générales ont été essayées puis **écartées** (laissées à 0) :
     - `PTR_VOISIN` (cible hors entrée seulement en table) : des pointeurs isolés sont légitimes, Ken casse à 18 601 ;
     - `PTR_INSTR` (cible = début d'instruction 68K) : casse le démarrage.
3. **Gestionnaires de types d'objets** (T_615100, 122 types ; T_612C70) que la règle j) « non vue en Arcade :
   homologue » envoyait sur une **même** routine d'Hyper (40 → 0x31F50, 9 → 0x2FEC0, 7 → 0x64D00…).
   - Exemple dans la fin de Sakura : Hyper 0x2FEC0 écrit dans l'emplacement voisin `$FFBE80`, ce qui donne un type
     `$B0` et un saut hors du code.
   - **`TYPES_GREFFE=1`** (`force3.py`) : les 33 gestionnaires à homologue non injectif sont greffés (4 464 o MIPS).

Résultats sur e6o (34 000 images, SCENEA_PASSIF) :

| perso | scène A → 8 | durée (Upper) |
|---|---|---|
| Ken ZERO | 17 017 → 21 947 | 4 930 (4 976) |
| Sakura ZERO 3 | 19 072 → 25 470 | 6 398 (6 289) |
| `$02` ZERO 2 | 19 102 → 22 054 | 2 952 (2 965) |
| Chun-Li ZERO 2 | 21 052 → 31 022 | 9 970 (non mesurée : le journal u_lu_04 s'arrête au début de la fin) |

Ensuite viennent la scène 8, la scène C et une nouvelle partie. Planche : `traces/planche_e6o_ken_fin.png`. Les fonds
sont faux : c'est le point 2.

### 5.3 Ryu : objets d'Upper dessinés par le moteur d'Hyper

Ryu ZERO 3 plante à 18 915 et Ryu ALPHA à 17 810 (`$00000601`, interpréteur d'animations d'Hyper 0x393D40).

- Chaîne d'appel : fin greffée 0x2B050 → affichage Upper 0x13D820 (≡ Hyper 0x392270, règle f) « service partagé
  avec le VERSUS ») → Upper 0x148240 (« équivalente » à Hyper 0x39CC90, mais ses appels vont au moteur d'Hyper).
- Les objets `$4B` (gestionnaire Upper 0x1EFCA0, greffé) ont en +$1C une valeur au format d'Upper. Le moteur d'Hyper la
  lit comme pointeur de table d'animation.
- Essai `AFFICHAGE_UPPER=1` + `DESSIN_UPPER=1` (e6q) : Ryu plante plus tôt, et tous les objets des écrans d'Upper
  deviennent invisibles (portraits, échelle). La fin de Ken garde les sprites du combat. **Écarté.**
- Piste : l'aiguillage du dessin par type d'affichage (octet +2 = `$36`) diffère entre Upper et Hyper. Il faut soit
  greffer la seule branche concernée, soit savoir pourquoi l'affichage d'Upper ne sort rien : liste `$71B8` et vidage
  d'Upper 0xCC240 ≡ Hyper 0x3900B0.

### 5.4 Balayage des 40 fins × 4 versions

**Pas encore fait** : il faut d'abord régler Ryu (§5.3), qui touche probablement d'autres persos. Commande prévue :
`oracle_ro9a.sh ro9a4_fige <trace> 34000 "PERSO=XX.V SCENEA_PASSIF=1 BLOCAGE=20000 SNAPSC=600"`, 3 en parallèle.
Pour chaque fin qui plante, comparer avec `compare_script.py` (§5.1).

## 6. Planisphère (entrée de l'Arcade)

### 6.1 Constats dans ro9a (e6c-e6i, image 700)

- À l'image 619, `remap_ids` appelle bien la copie de 0x253A80. Elle dessine `$86/$87` en `$904000` et `$81/$82` en
  `$908000` (512 et 128 mots).
- Hyper efface ensuite `$900000-$903FFF` et `$90E000-$90FFFF` aux images 620 et 660 : copies d'Upper 0x25CD48 et
  0x258F6C → Hyper 0x38AE50/0x38AEF0, équivalentes à Upper 0xC5BC0/0xC5DA0, avec écriture en pré-décrément.
- `$C130-$C13C` sont remis aux pages `$190` par l'IRQ d'Hyper (0x3F5C0) quand `$A8(A5)` est posé. Upper fait de même.
- Tilemaps (dumps VRAM) : scroll2 n'a aucune cellule commune avec la référence. Mais cette référence a été prise en
  attraction (§6.3), donc la conclusion est à revoir.

### 6.2 Dans Upper

Il existe un répartiteur d'écrans 0x50B80 (`T_60C820[$8C28]`, 9 entrées). L'entrée 8 est 0x59D20 (`T_60CCA8[$8C2A]`,
`T_60CCB8[$8C31]`) et mène à 0x59EC0. Celle-ci efface les plans (0x5D630, 0x5D7F0, 0x5D9D0), dessine la carte (0x5DAC0)
et charge les palettes (0xC8C50 → `$90C0xx`).

Toutes ces routines sont greffées, mais aucune de leurs copies n'écrit en VRAM dans ro9a. À vérifier en partie Arcade
d'Upper (§6.3) : est-ce bien ce chemin, et qui l'appelle ?

### 6.3 Piège de méthode

`lua/tournee_arcade.lua` est fait pour Hyper/ro9a. Dans Upper, il ne lance pas de partie : le jeu reste en attraction
(A5+0 = `$14`).

Les mesures d'Upper faites avec lui (`u_c130`, `u_vram2480`, `u_lire*`, `u_32`, `u_100`, `u_8c28`, `u_s2w`, `u_s2b`)
sont donc celles de l'attraction. L'oracle Upper reste `outils/oracle_upper.sh` (tournee_greffe.lua). À refaire
avec lui : `$32/$3A/$100/$C130-$C13C` et la VRAM à la présentation Arcade.

## 7. FBNeo : registre des plans `$804200-$804205` (exigences pour le cœur)

Modèle : le fork MAME, `src/mame/capcom/cps2.cpp` (`hsfa_map`) et `cps1_v.cpp` (`hsfa_plane_code`).

Écritures :

- 3 mots en lecture/écriture : `$804200` = scroll1, `$804202` = scroll2, `$804204` = scroll3.
- Accepter les écritures 16 bits avec masque d'octets (`COMBINE_DATA`) et les relire telles quelles (lecture CPU =
  dernière valeur).
- Le code traduit écrit par `MOVE.W #imm,$80420x.L`. Les écritures viennent des adresses PS2 RAM + `$7FF00/2/4`,
  détournées par `HWREG` dans `mame_test.py`.
- Valeurs : 0 = mappage d'origine du jeu (`gfxrom_bank_mapper`). Sinon, base en **unités de 64 Ko** de la ROM
  graphique. Hyper : `$300/$340/$3A0` (plans d'Hyper chargés en `$3000000`). Écrans d'Upper : `$400/$440/$4A0`
  (`hsfa_plans.bin` d'Upper chargé en `$4000000`).

Sémantique :

- Si la base ≠ 0, le code de tuile brut de la tilemap est un indice **local** à partir de la base :
  `code_effectif = (base << 16) / taille_element + code`, avec une taille d'élément de 64 o (scroll1 8×8), 128 o
  (scroll2 16×16) ou 512 o (scroll3 32×32). Pas de renumérotation, pas de table de banques CPS-B pour ce plan.
- Toute **modification** marque le plan entier comme à redessiner (`mark_all_dirty`). La base peut changer d'une image
  à l'autre (combat ↔ écrans d'Upper, plusieurs fois par partie).
- Remise à 0 au reset. L'état doit être sauvegardé dans les états de sauvegarde.
- La ROM graphique doit couvrir au moins `$4000000 + taille(hsfa_plans.bin d'Upper)`.

## 8. Index `re/` : réponses aux conflits relevés

1. **2ᵉ fenêtre `$C30000`** : abandonnée. Désormais `$C38000-$C83FFF`, au-dessus de la fin réelle d'ext_940000 + son
   (`$C2D200-$C31FFF` en v149 ; l'index indique `$C2C200-$C30EFF`, valeur v148). Une assertion dans `mame_test.py`
   le vérifie.
2. **`$D10000-$EFFFFF`** (décors GREFFE-DECORS) : recouvert par le bloc (désormais `$D0C000-$EFFFFF`). À replanifier
   avec les décors (§3).
3. **`$BFFF00-$BFFF04`** : voulu. Ce sont des adresses PS2 de la RAM d'Hyper (+`$7FF00`) que `HWREG` détourne vers le
   registre `$804200`. Elles ne sont jamais lues ni écrites en mémoire : aucune instruction de ro5/ro9 n'accède à
   +`$7FF00..$7FF05`.
4. **Table des tâches** `$FF0184-$FF0383` : aucune variable A5 relogée n'y tombe (toutes sont en
   `$FF43BA-$FF4CA2`). `$C3A7/$C3A8` sont des variables communes déplacées par le portage d'Hyper. Par prudence, la
   zone est exclue des zones libres dans `relogement_a5_v3.py` (34 zones libres → 23).

Lignes proposées pour `re/allocations.tsv`, non écrites dans le dépôt :

```
ext_ro9a	$C38000	$C83FFF	greffe voie B (greffe_arcade)	utilisé	work/greffe_arcade/GREFFE-ETAPE4.md §3	2e fenêtre du bloc de la greffe (FENETRES=1) : PS2 $F74000-$FBFFFF ; remplace la réservation $C30000
ext_ro9a	$D0C000	$EFFFFF	greffe voie B (greffe_arcade)	utilisé	work/greffe_arcade/GREFFE-ETAPE4.md §3	1re fenêtre du bloc de la greffe : PS2 $D60000-$D9FFFF, $DB0000-$E6FFFF, $E80000-$F73FFF ; plus de bourrage du trou son ; recouvre la réserve GREFFE-DECORS
exec_ro9a	$D60000	$D9FFFF	greffe voie B (greffe_arcade)	utilisé	work/greffe_arcade/GREFFE-ETAPE4.md §3	1er morceau PS2 du bloc (aucun lui $D6-$D9 dans ro5/ro9)
exec_ro9a	$DA0000	$DAFFFF	Hyper (ro9)	réservé	work/greffe_arcade/GREFFE-ETAPE4.md §3	lui $DA d'Hyper (4 sites) : trou du bloc
exec_ro9a	$DB0000	$FBFFFF	greffe voie B (greffe_arcade)	utilisé	work/greffe_arcade/GREFFE-ETAPE4.md §3	morceaux PS2 2-3 du bloc (trou son $E70000-$E7FFFF)
```

## 9. Décors (point 5, pour plus tard)

Précision de l'utilisateur : le décor suit le **joueur 2**, son perso **et** sa version.

| version de J2 | décor |
|---|---|
| ZERO (Alpha 1) | décor SFA1 du perso |
| ZERO 2 ou ALPHA (Alpha 2) | décor SFA2 |
| ZERO 3 (Alpha 3) | décor SFA3 / Upper |

- Plus de tirage au hasard.
- La table de choix lit l'id étendu `$102` de J2 (structure `$FF8800`), avec un crochet sur l'écriture de `$174`.
- Numéros de décor : Upper `$00-$4E`, SFA2 `$50-$72`, Hyper `$78-$7C`, une plage SFA1 à réserver.
- Place : voir §3. La disposition actuelle n'a plus de marge.

## 10. Outils ajoutés

- `outils/oracle_ro9a.sh` : `SCRIPT_LUA=` permet d'envelopper (`surv.lua`, `lire.lua`, `vram.lua`) avec
  `LUA_BASE=lua/graine_pc.lua LUA_BASE_G=lua/tournee_arcade.lua`.
- `etape3/greffe3.py` : `BLOC_SEUL=1 BLOC_N=n` liste les n plus grosses régions avant l'assertion de taille.
- `lua/donnees_lues2.lua`, `outils/lance_upper_donnees2.sh`, `outils/journaux_lu2.sh` : **inutiles** (fausse alerte
  du §5 ; tournee_arcade ne joue pas Upper).

## 11. Découvertes durables

- PILE_LUI : un temporaire de pile chargé depuis la mémoire était pris pour la constante d'un `lui` périmé, ce qui
  perdait des CMP (Upper 7 sites, Hyper 26) ; corrigé en v149.
- « Tampons vidéo `MOVE.W #$A3C0 ; LSL #8` » : constante d'adresse d'Upper construite par décalage, à reloger dans la
  greffe (`PAGES_RAM`) ; ce n'est pas un défaut du traducteur.
- Greffe : un `lui` peut être relogé de trois façons : paire lui/lo, `lui` négatif additionné (`LUI_NEG`), valeur
  rangée en A5 (`LUI_A5ST`).
- `$C130-$C13C(A5)` contiennent les pages des plans au format adresse PS2 (68K « `#$190` » = `$900000`), recopiées
  par l'IRQ dans `$C144…` puis `>> 8` vers `$804102…`. `$A8(A5)` demande leur remise à `$190`.
- La « 2ᵉ fenêtre » 68K doit suivre la fin réelle d'ext_940000, qui bouge avec le traducteur (`$C30F00` en v148,
  `$C32000` en v149).
- `tournee_arcade.lua` ne joue pas Upper : oracle Upper = `oracle_upper.sh`.
- Données de la greffe : une paire de mots (scripts) peut ressembler à un pointeur de code. Un pointeur de code est
  aligné sur 4 ; les cas restants se trouvent en comparant les scripts (compare_script.py).
- Règle j) « homologue » : un homologue doit être injectif. Des gestionnaires d'objets d'Upper distincts envoyés sur une
  même routine d'Hyper sont faux.
