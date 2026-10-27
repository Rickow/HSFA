# Carte des modules non étudiés de l'Anthology : `ro1`, `ro2`, `ro4`, `ro6`, `ro7`, `ro8` et le menu `b`

Cartographie statique rapide, 2026-10-10. Rien n'a été modifié hors de `<workspace>/hsfa/work/carto_modules/` ;
ni MAME ni PCSX2 n'ont été lancés ; `mame_test.py` n'a été ni lancé ni importé (pas de profil pour ces modules).
Les ROM arcade et l'ISO de travail ont seulement été LUS (comparaisons ponctuelles, §8).

**Conventions** (celles de CARTE-ro9) :
- `fichier` = décalage dans `roN_usa_prog68k.bin` ; `exéc.` = fichier + `0x1F0000` (pour `b` : + **`0x1C8000`**) ;
- « routine » = découpage fin (`GRAIN=routine`), restreint aux **zones 68K** de `zones.py` (§0.2) ;
- `eN` = entrée N de `X_DATA.BIN` (manifeste), `YN` = flux N de `Y_DATA.BIN` ;
- pourcentages de code = part de la **taille MIPS du code recompilé** (natives exclues), sauf mention.

---

## 0. Synthèse

### 0.1 Tableau

| | **ro1** | **ro2** | **ro4** | **ro6** | **ro7** | **ro8** | **b** |
|---|---|---|---|---|---|---|---|
| nom interne (+0x20) / nom dans `b` | `zero1_usa.bin` / Street Fighter Zero | `zero2_usa.bin` / SF Zero 2 | `zero4_usa.bin` / SF Zero 2 Alpha | `zero6_usa.bin` / **SF Zero 2 Dash** | `zero7_usa.bin` / **Pocket Fighter** | `zero8_usa.bin` / SF Alpha 2 | `sub_usa.bin` (menu, système) |
| jeu | SFA / Zero (1995), noms occidentaux | Zero 2 (1996), noms japonais | Zero 2 Alpha (arcade, 1996) | Alpha 2 Gold console **+ Cammy** | Super Gem Fighter Mini Mix / Pocket Fighter (1997) | SFA2 occidental (1996) | — |
| versions de SECRET OPTION | 95/06/05, 95/06/27, 95/07/27 | 96/02/27, 96/03/06, 96/04/30 | 96/08/05 | 97/10/23 | 97/09/01, 97/09/04 | 96/03/06, 96/04/30 | — |
| roster (table de noms) | 13 | 18 (+SHIN-GOUKI) | 22 (+5 EX) | 22 (+5 EX) **+CAMMY** | 12 | 18 + 4 | — |
| entrée X_DATA du programme | e206 | e224 | e348 | e526 | e536 | e543 | e203 |
| RAM 68K émulée (base) | **`0x600000`** | **`0x800000`** | **`0x800000`** | `0x800000` | **`0x660000`** | **`0x800000`** | (natif) |
| `ram_hi_of` (outillage) | `0x58` faux | `0x78` faux | `0x78` faux | `0x80` juste | `0x68` faux | `0x78` faux | — |
| code / données (en-tête) | 1,94 / 1,17 Mo | 2,86 / 2,42 Mo | 3,03 / 2,52 Mo | 2,96 / 2,62 Mo | 2,23 / 2,13 Mo | 2,92 / 2,60 Mo | 50 / 29 Ko |
| Z80 recompilé (fichier) | `0x41A00–0x61550` (**au milieu**) | `0x80–0x235A0` | `0x80–0x235A0` | `0x2D1750–0x2F4C70` (**à la fin**) | `0x21E0–0x2C980` | `0x80–0x235A0` | aucun |
| recompilateur (formes de CMP) | récent | récent | récent | **mixte** (17 % ancien) | récent | récent | C natif |
| natives (cibles de `jal`) | 31 | 32 | 30 | 32 | 32 | 30 | tout |
| recensement, base fausse → juste | 96,4 → **98,2 %** | 97,0 → **98,7 %** | 97,1 → **98,8 %** | **98,8 %** | 97,0 → **98,4 %** | 97,0 → **98,8 %** | — |
| assemblage à blanc : 68K, non résolus | 0,28 Mo, 9 (artefact §1.3) | 0,43 Mo, **0** | 0,46 Mo, **0** | 0,47 Mo, **0** | 0,35 Mo, **0** | 0,45 Mo, **0** | — |
| programme 68K + données | 1,45 Mo | 2,85 Mo | 2,98 Mo | 3,09 Mo | 2,48 Mo | 3,05 Mo | — |
| graphismes (X_DATA) | e207 + banques **e208–e220** | e225–e228, e249 + banques **e229–e248** | ceux de ro2 | e527, e529–e531, e535 (+e528, e534 ?) | e537–e539 | ceux de ro2 | e204/e205 |
| son | Z80 e221 + QSound e222 **+ ADX Y97–131** | Z80 e250 + QSound e251 | ceux de ro2 | Z80/QSound **de ro2** (e250/e251) **+ ADX Y170–228** | Z80 e540 + QSound e541 + ADX Y530–542, Y90–95, Y281–432 | ceux de ro2 | — |
| parenté de code (identique MIPS) | 9,7 % avec SFA2 ; 5 % avec ro3/ro5/ro9 | 93 % ro8, 91 % ro4 | 88 % ro2 | 71 % ro4 | ≤ 7,7 % avec tous | 92 % ro2 | — |
| repris par Hyper (ro9) | banques e208–e220 (version ZERO) | banques e229–e248, dont **e248 = Cammy** | (rien de mesurable) | **musiques ALPHA** (Y170–187) | rien | (rien de mesurable) | — |
| accessible au menu US ? | oui | **non** (§9.3) | **non** | oui (SFA2 Gold) | oui | oui | — |

### 0.2 Ce qu'il faut retenir

1. **Identités confirmées** par les tables de noms (trouvées en cherchant `ZANGIEF`, ou `SODOM` pour ro1 qui n'a pas
   Zangief), les chaînes de version de SECRET OPTION et la table des jeux de `b` (§9).
   - **ro6 = « Street Fighter Zero 2 Dash »** (nom japonais de l'Alpha 2 Gold console avec Cammy). En US, c'est le
     « SFA2 Gold » du menu.
   - **ro7 = Pocket Fighter / Super Gem Fighter Mini Mix** : roster de **12** (avec MORRIGAN, HSIEN-KO, FELICIA,
     TESSA, IBUKI, DAN, AKUMA). La note « CHUN-LI/SAKURA/ZANGIEF seuls » de CARTE-sfa2 §1.1 est fausse.
2. **La RAM 68K n'est pas où l'outillage la croit** pour 5 modules sur 6 : `translate.ram_hi_of` (fin d'exécution
   arrondie à `0x80000`) donne une base fausse. La base est prouvée de **trois façons** (§1.1). La corriger fait
   gagner 1,4 à 1,8 point de recensement : ce sont les `MOVEA` (`bgez`, écritures d'An).
3. **Le Z80 recompilé n'est pas toujours en tête**. Or l'outillage suppose `CODE0 = 0x22B00` (en dur dans `mips.py`,
   et `c0` dans `translate.empty_funcs` / `_CODE_STARTS`). D'où `zones.py` (§1.2).
4. Une fois ces deux points corrigés, **le traducteur passe sur tous les modules** : 98,2 à 98,8 % de recensement
   (ro3 : 98,8 %) et un assemblage à blanc **sans non-résolu**, sauf l'artefact de découpage de ro1.
5. **Familles** :
   - SFA2 = ro2 ≈ ro8 ≈ ro4 (88–93 % de code identique), puis ro6 (71 % ; 82 % au niveau 68K) ;
   - ro1 et ro7 sont isolés ;
   - aucun module ancien ne partage avec SFA3/Upper/Hyper plus que la couche Anthology commune (≈ 4–10 %).
6. **Hyper ne reprend pas de code** de ces modules. Il en reprend :
   - les **banques de sprites** des groupes ro1 et ro2 ;
   - les **flux musicaux ADX** de ro6 (ses musiques ALPHA).
7. **Contenus propres à l'Anthology** dans chaque module :
   - SECRET OPTION (choix de la révision arcade) ;
   - CUSTOMIZE / EXTRA OPTION (1)–(4) : réglages du système de jeu ;
   - TRAINING MENU avec enregistrement ;
   - COLOR EDIT, DISPLAY ADJUST, SAVE/LOAD ;
   - Cammy dans ro6, CPS1/CPS2 dans ro1.

   Ils sont décrits par module. Aucun ne concerne directement Hyper ou Upper, sauf la musique ALPHA (ro6) et les
   banques (ro1, ro2).

---

## 1. Machine (commun aux six modules)

### 1.1 RAM 68K émulée : trois preuves concordantes

| module | `MOVEA` converti : `bgez … lui X ; addu` (motif `translate.movea_fixup`) | table des jeux de `b` : « adresse libre » − `0x64000` (§9.1) | `lui` (base + k·`0x10000`) : k = 0 / +2 / +6 | base retenue |
|---|---|---|---|---|
| ro1 | `0x60` × 696 | `0x664000` | 708 / 282 / 224 | **`0x600000`** |
| ro2 | `0x80` × 1 000 | `0x864000` | 1 022 / 711 / 188 | **`0x800000`** |
| ro4 | `0x80` × 1 053 | `0x864000` | 1 075 / 755 / 188 | **`0x800000`** |
| ro6 | `0x80` × 1 079 | `0x864000` | 1 101 / 767 / 219 | **`0x800000`** |
| ro7 | `0x66` × 622 | `0x6C4000` | 632 / 462 / 216 | **`0x660000`** |
| ro8 | `0x80` × 1 026 | `0x864000` | 1 048 / 711 / 188 | **`0x800000`** |
| (contrôle) ro3, ro5, ro9 | `0x90`, `0xA0`, `0xB8` | `0x964000`, `0xA64000`, `0xBE4000` | | `0x900000`, `0xA00000`, `0xB80000` |

- **Zones** : même disposition que SFA3 (§30 du HANDOFF), relative à la base :
  - RAM de travail : base + 0 ;
  - vidéo CPS2 : base + `0x10000`–`0x4FFFF` ;
  - registres et boîte QSound : base + `0x6xxxx`.
- Les adresses A5 sont identiques partout (constante `0x70008000` posée 6 fois dans chaque module).
- `ram_hi_of` est donc **faux pour ro1, ro2, ro4, ro7, ro8**. L'erreur est silencieuse : les conversions `MOVEA`
  échouent, les `bgez` et les écritures d'An ne sont pas traduites.
- Correctif d'essai dans mes scripts : `T._RAM_CACHE[bytes(buf[:32])] = base >> 16`. Il est à porter dans
  `translate.ram_hi_of`, par exemple sous forme de table par module ou par le motif `bgez`/`lui`.

### 1.2 Bornes : Z80, 68K, aides du recompilateur

`zones.py` :
- **Z80** = de la fonction du premier accès au banc `0x7000_10xx` jusqu'au premier prologue après le dernier accès ;
- **68K** = le reste du code (banc `0x7000_11xx`) ;
- dans les six modules, il n'y a **aucun accès 68K à l'intérieur de la zone Z80** (zones contiguës).

| module | zones 68K (fichier) | aides du recompilateur : `movem_push` / `movem_pop` / `andi_ccr` / `abcd` (+ une aide non répertoriée à push + `0x740`) |
|---|---|---|
| ro1 | `0x40–0x41A00` **et** `0x61550–0x1F1BC0` | `0x80` / `0x3E0` / `0x740` / `0x910` (+ `0x7C0`) |
| ro2, ro4, ro8 | `0x235A0–fin` | `0x235A0` / `0x23900` / `0x23C60` / `0x23E30` (+ `0x23CE0`) |
| ro6 | `0x40–0x2D1750` (+ `0x2F4C70–0x2F5340`, 2 natives) | `0x2B30E0` / `0x2B3440` / `0x2B37A0` / `0x2B3970` (+ `0x2B3820`) |
| ro7 | `0x40–0x21E0` (aides et natives) **et** `0x2C980–fin` | `0x80` / `0x3E0` / `0x740` / `0x910` (+ `0x7C0`) |

Preuves pour les aides :
- empreinte MIPS (adresses masquées) des aides de ro5 / ro3 (`aides.py`) ;
- `andi_ccr` de ro1 `0x740` comparée mot à mot à celle de ro9 `0x23480` : identiques ;
- nombre d'appels : ro1 = 5 / 5 / 11 / 27 (+16 vers `0x7C0`).

L'aide non répertoriée (push + `0x740`) existe aussi dans ro3 (`0x380AA0`, 4 appels), ro5 (`0x23240`) et ro9
(`0x23500`). Elle **manque à `AIDES_RECOMP`**, à vérifier.

### 1.3 Ce qui est codé en dur pour ro3 et casse ici (cf. CARTE-ro9 §6)

| # | constante / hypothèse | effet sur ces modules | correctif |
|---|---|---|---|
| 1 | `ram_hi_of` (fin d'exécution arrondie) | base fausse pour ro1/2/4/7/8 (§1.1) : −1,4 à −1,8 point | table par module, ou motif `bgez`/`lui` |
| 2 | `mips.CODE0 = 0x22B00`, `c0 = 0x22de0 if ro9 else 0x22b00` (`translate.empty_funcs`, `_CODE_STARTS`), `census.py`, `natmiss.py`, `hooks_fork.py`, `surface_native.py` (`decode(buf, 0x22b00, …)`) | **ro1** : 0,27 Mo de 68K avant `0x22B00` ignorés, et Z80 `0x41A00–0x61550` pris pour du 68K ; **ro6** : le 68K `0x40–0x22B00` est hors des listes de débuts de fonction, et le Z80 final `0x2D1750–0x2F4C70` est pris pour du 68K ; **ro7** : Z80 `0x22B00–0x2C980` pris pour du 68K ; **ro2/4/8** : 0xAA0 octets de queue Z80 inclus | bornes par module (`zones.py`) |
| 3 | `read_jump_table` borne les tables par `CODE0 ≤ v < CODE1` | si l'on abaisse `CODE0` à `0x40` pour ro7, 4 tables débordent sur des valeurs `0x200000` (= 4 non résolus) ; avec `CODE0` par défaut : 0 | borne = zones 68K, pas `CODE0` |
| 4 | `AIDES_RECOMP` (exéc. ro3 `0x570360…`) | adresses propres à chaque module (§1.2) | profil par module |
| 5 | un seul segment de code 68K | **ro1** : le 68K entoure le Z80 ⟹ assemblage en deux unités. Il en résulte 9 non résolus : 5 entrées de tables et ~20 `Bcc` de la 2ᵉ zone vers la 1ʳᵉ (`nonresolus.py`) | une seule unité qui saute le trou Z80 |
| 6 | profil `mame_test` (`va_reset`, VBL, hooks, `$BE48`, fichier fixe 289, palettes, intro, routines réécrites à la main…) | **sans objet** : les moteurs SFA1/SFA2/SGF diffèrent de celui de SFA3. Points d'entrée à rechercher. **Pas** de fichier de frames à adresse fixe : emplacements 10/11 vides dans `b` (§9.1) | profil à créer de zéro |

Ce qui ne casse pas :
- même banc de registres (`0x1100–0x115F`, A8/D8, pile `0x114C`) ;
- mêmes 159 cibles de l'exécutable, de mêmes familles ;
- même couche Anthology (natives identiques à celles de ro3 : manette `0x381770`, remappage `0x381900`, etc.,
  `natives_mod.txt`).

**Taille** : programme 68K + données **< 4 Mo** pour les six modules (1,45 à 3,09 Mo). Ils tiennent dans un
programme CPS2 standard, contrairement à Upper et Hyper. Pour ro6 et ro8 (> 3 Mo), la marge est faible à cause des
tables de `mame_test` en `0x3C0000` / `0x3E0000`.

### 1.4 Recensement détaillé (base corrigée, `census_<mod>_base.txt`)

| module | points | traduits | manques | `base=?` | `beq` | `bne` | cases `s` | `bgez` | An |
|---|---|---|---|---|---|---|---|---|---|
| ro1 | 73 910 | 98,2 % | 1 305 | 453 | 355 | 207 | 69 | 47 | 29 |
| ro2 | 112 212 | 98,7 % | 1 407 | 520 | 388 | 218 | 59 | 49 | 42 |
| ro4 | 119 279 | 98,8 % | 1 389 | 495 | 402 | 217 | 61 | 48 | 34 |
| ro6 | 118 930 | 98,8 % | 1 387 | 491 | 379 | 219 | 74 | 50 | 35 |
| ro7 | 86 518 | 98,4 % | 1 378 | 509 | 356 | 217 | 65 | 48 | 34 |
| ro8 | 114 752 | 98,8 % | 1 389 | 513 | 389 | 214 | 59 | 53 | 33 |
| *ro3 / ro5 / ro9 (même script)* | | *98,8 / 99,0 / 98,9 %* | | | | | | | |

Pour ro7, la zone `0x40–0x21E0` (aides et 2 natives) n'est traduite qu'à 39,6 %. C'est attendu : c'est du C.

**Assemblage à blanc** (`essai_mod.py`, mode `cps2`, base corrigée, natives par le critère `natmiss`/`native_at`) :

| module | éléments | 68K | non résolus | tremplins (§94) | octets ADDA | longs sans SR |
|---|---|---|---|---|---|---|
| ro1 | 65 782 | 0,28 Mo | 9 (découpage) | 1 | 49 | 384 |
| ro2 | 100 994 | 0,43 Mo | 0 | 148 | 36 | 671 |
| ro4 | 107 532 | 0,46 Mo | 0 | 158 | 36 | 731 |
| ro6 | 107 812 | 0,47 Mo | 0 | 191 | 36 | 745 |
| ro7 | 77 613 | 0,35 Mo | 0 (4 si `CODE0` abaissé) | 2 | 21 | 642 |
| ro8 | 103 415 | 0,45 Mo | 0 | 150 | 36 | 695 |

Les 148 à 191 tremplins de la famille SFA2 (contre 29 à 42 pour ro3 et ro9) signalent beaucoup d'aiguillages
lointains : à surveiller en exécution.

---

## 2. Parenté de code (`comparaison_mod.py`, `couverture_mod.py`, `id68k.py`)

**Identité exacte des routines** : part du code recompilé de LIGNE identique (MIPS, adresses masquées) à une routine
de COLONNE (`comparaison_mod.txt`).

|  | ro1 | ro2 | ro3 | ro4 | ro5 | ro6 | ro7 | ro8 | ro9 |
|---|---|---|---|---|---|---|---|---|---|
| ro1 | – | 9,7 | 5,3 | 9,6 | 5,9 | 8,6 | 5,2 | 9,7 | 5,3 |
| ro2 | 8,6 | – | 10,3 | **91,3** | 12,5 | 65,6 | 5,7 | **93,4** | 11,5 |
| ro4 | 8,6 | **87,9** | 10,3 | – | 12,5 | 68,6 | 5,7 | **86,2** | 11,5 |
| ro6 | 7,7 | 65,6 | 11,5 | **70,8** | 11,1 | – | 5,7 | 64,6 | 10,9 |
| ro7 | 6,8 | 7,7 | 6,7 | 7,6 | 6,9 | 7,3 | – | 7,7 | 6,7 |
| ro8 | 8,6 | **92,4** | 10,3 | 88,7 | 12,4 | 64,1 | 5,6 | – | 11,5 |
| ro9 | 3,9 | 8,6 | 38,5 | 8,7 | **58,6** | 8,0 | 3,8 | 8,7 | – |

**Couverture par fenêtres de K = 64 instructions** (insensible au découpage ; `couverture_mod.txt`) :
- ro2/ro4/ro8 entre eux : 92–97 % ;
- ro6 par ro4 : 77,5 % ;
- ro1 par la famille SFA2 : 19 % ;
- ro7 par n'importe quel module : ≤ 6,7 % ;
- ro9 par ro2 : 17,8 %, contre ro5 par ro2 : 18,1 % et ro3 par ro2 : 13,6 % ⟹ c'est le **fond commun**, pas un
  emprunt d'Hyper.

**Classes complètes** (meilleur des références, part du code recompilé) :

| module | identique | déplacements seuls | ≥ 90 % | 70–90 % | 40–70 % | < 40 % |
|---|---|---|---|---|---|---|
| ro1 (contre ro3/5/9/2/7) | 9,9 | 15,3 | 7,9 | 12,5 | 30,9 | 23,4 |
| ro2 (contre ro8/4/6/3/1) | 97,1 | 0,9 | 1,0 | 0,3 | 0,4 | 0,3 |
| ro4 (contre ro2/8/6/3) | 93,6 | 0,8 | 1,1 | 1,5 | 1,8 | 1,1 |
| ro6 (contre ro4/2/8/3) | 71,7 | 2,1 | 1,2 | 3,5 | 10,9 | 10,6 |
| ro7 (contre ro3/2/6/1/5) | 8,0 | 8,5 | 3,5 | 10,4 | 34,8 | 34,8 |
| ro8 (contre ro2/4/6/3) | 94,4 | 4,0 | 0,8 | 0,2 | 0,1 | 0,6 |
| ro9 (contre ro1/2/4/6/8) | 8,9 | 9,0 | 4,5 | 11,2 | 30,9 | 35,5 |

**Niveau 68K** (opcodes émis par le traducteur, insensibles à la forme des CMP) :
- ro6 contre ro4 + ro2 + ro8 : identique MIPS 70,9 %, **identique 68K seulement 11,2 %**, autre 18,0 % (506 Ko).
  Le recompilateur mixte de ro6 explique donc une part de l'écart. Parmi les ~600 Ko non identiques en MIPS :
  301 Ko de forme « ancienne », 284 Ko de forme « récente » (`style_cmp.txt`).
- Autres modules (identique MIPS + identique 68K seulement) :
  - **ro9** contre ro1/2/4/6/8 : 8,9 + 6,4 = **15,3 %** ;
  - **témoin ro3** contre les mêmes : 9,4 + 5,9 = **15,3 %** ⟹ Hyper n'emprunte rien de plus que SFA3 aux anciens
    modules ;
  - ro1 contre ro2/3/5/9/7 : 9,9 + 13,2 = 23,1 % ;
  - ro7 contre ro1/2/3/6 : 8,0 + 3,6 = 11,6 %.

**Génération du recompilateur** (`style_cmp.txt`, part du code majoritairement « récente » / « ancienne ») :
- ro1 51 / 1,5 ; ro2 47 / 1,6 ; ro4 47 / 1,7 ; ro6 **31 / 17** ; ro7 40 / 2,0 ; ro8 47 / 1,7 ;
- pour mémoire, ro3 25 / 26 (mixte), ro5 et ro9 récents.

**Données** (`donnees_mod.txt`, fenêtres de 32 o, pointeurs masqués) :

| module | données | retrouvées ailleurs | zéros | **neuf** | remarque |
|---|---|---|---|---|---|
| ro1 | 1,17 Mo | 41,1 % (37,5 % dans la famille SFA2) | 18,5 % | **40,4 %** | |
| ro2 | 2,42 Mo | 92,7 % | 3,1 % | 4,2 % | |
| ro4 | 2,52 Mo | 95,9 % | 2,5 % | 1,7 % | 95 % dans ro6 |
| ro6 | 2,62 Mo | 92,4 % | 3,8 % | 3,8 % | 92 % dans ro4 |
| ro7 | 2,13 Mo | 13,0 % | 31,4 % | **55,6 %** | |
| ro8 | 2,60 Mo | 92,2 % | 5,1 % | 2,6 % | |
| ro9 | 5,72 Mo | 50,8 % | 22,2 % | 26,9 % | dans ro1 / ro2 / ro4 / ro6 : 5,1 / 7,7 / 7,9 / 8,1 % (non exclusif ; exclusif ≤ 0,6 %, CARTE-ro9 §2.3) |

---

## 3. ro1 — Street Fighter Alpha / Zero (1995)

**Identité**
- En-tête : version 2, `zero1_usa.bin`, code `0x1F1BC0`, données `0x12BE00`, fin d'exécution `0x50DA00`.
- Copyright : fichier `0x2C9A85` « @1995,2006 CAPCOM USA, INC. ».
- Chaînes de titre à `0x2BB3F4` : « ZEROZERO », « ALPHA! », « STREET », « CLASSIC! ».
- **Roster** : il n'y a pas de Zangief ; la table a été trouvée par `SODOM`. Il y en a deux, ajoutées par l'Anthology
  (ASCII natif) :
  - `0x1FF260` (pas de `0x18`, après « PLAYER : / PALETTE: / SAMPLE : / EXIT » en `0x1FF1F8`) ;
  - `0x2008F0` (pas de 8, entraînement).
  - Contenu : RYU, KEN, AKUMA, CHARLIE, CHUN-LI, ADON, SODOM, GUY, BIRDIE, ROSE, M.BISON, SAGAT, DAN. Ce sont
    **13 noms occidentaux**, le même nombre que les banques e208–e220.

**Menus de l'Anthology** (Shift-JIS, `sjis_ro1.txt`, `0x1FDB80–0x200958`) :
- OPTION MODE : GAME OPTION / CONTROLLER SETTINGS / SOUND OPTION / DISPLAY ADJUST / SAVE/LOAD ;
- **SECRET OPTION** : 95/06/05ver, 95/06/27ver, 95/07/27ver ;
- **CUSTOMIZE** et EXTRA OPTION (1)–(4) : VITALITY, SP GAUGE, GUARD DAMAGE, GROUND/MID-AIR/ADV/AUTO GUARD,
  THROW (ESCAPE), DEFENSIVE ROLL, DF ROLL COMMAND, SUPER LEVEL, COMMAND TIMER, FRIENDSHIP, ALPHA COUNTER,
  JUMP ATTACK, ALPHA COMBO, CANCEL TIMER, SUPER CANCEL, avec les valeurs **ALPHA / ALPHA2 / ALPHA3 / ARCADE / LONG /
  ADVANCED** (réglages façon « autre épisode ») ;
- SOUND : MONAURAL/STEREO et **CPS2 / CPS1** (`0x1FF0A8` / `0x1FF0C8`), sans doute la version CPS Changer ;
- DISPLAY : OFFSET, RATIO, SHARPNESS, FILTER ;
- COLOR EDIT ;
- **TRAINING MENU** (`0x1FFB90`) : DUMMY SETTINGS, CHARACTER CHANGE, ATTACK DATA, KEY INPUT, REC/PLAY, RANDOM
  PLAYER… ;
- pauses 1P/2P, VS MODE(1P/2P), MAX ROUND, TURBO0–2.

Les libellés des modes eux-mêmes (ARCADE / VERSUS…) ne sont ni en ASCII, ni en SJIS, ni en frames `$0A` : ce sont
probablement des images.

**Machine**
- RAM `0x600000` ; Z80 au milieu (`0x41A00–0x61550`) ; deux zones 68K (§1.2).
- 31 natives (couche Anthology identique à ro3 : `0xBE0`, `0xC10`, `0x1380` manette, `0x14B0` remappage,
  `0x1E8A10`…).
- **Pilote de musique ADX** natif : `0x1F17D0` / `0x1F1980` (appelle `0x1552D0`, `0x155510`… ; homologue de ro3
  `0x393190` / `0x3935F0`).
- Appels à `b` : `0x1CB320` (déblocage, site `0x1E8E70`) et `0x1CB520`.

**Traducteur** : 98,2 % avec la base corrigée (96,4 % sans) ; assemblage en 2 unités, 9 non résolus (§1.3, n° 5).

**Ressources**
- `b` charge (§9.1) :
  - emplacement 1 : e207 (« mémoire de tuiles » brute, type 2, vers `0x704000` / `0xF04000`) ;
  - emplacement 5 : vide (type 2) ;
  - Z80 e221 ;
  - QSound e222.
- Banques de persos **e208–e220** : conteneurs 16×16 seuls, 2 992 à 4 896 tuiles (`conteneurs.txt`). Je n'ai trouvé
  dans ro1 **ni table perso → banque ni appel à `0x155080`** : leur chargement passe probablement par l'exécutable
  (emplacement 5), à confirmer.
- e223 (TIM2) n'est pas cité par `b`.
- **e222 = `sfz.11m` + `sfz.12m` (arcade `sfa.zip`) octets échangés : identique sur 4 Mo.**
- **e221 = région audio MAME de `sfz.01`/`sfz.02`, exacte** : `0x0–0x8000`, `0x10000`, `0x28000`.
- Musique : table ADX native exéc. `0x3F0EB8` (63 enregistrements) → **Y97–Y131** (≈ 60 min, 184 Mo). Ce sont les
  codes `0x0141–0x0161` de la table son commune.

**Liens**
- Avec ro3/ro5/ro9 : 5 % identique, soit le fond commun. Avec la famille SFA2 : 9,7 % identique et 19 % de
  couverture (moteur CPS2 de 1995/96 en partie partagé).
- **Hyper** :
  - reprend les **banques e208–e220** (ids `$30–$3C`, version ZERO ; table ro9 `0x5AF1B0`) ;
  - ne reprend **pas** les musiques : ZERO d'Hyper = Y56–68, contre Y97–131 pour ro1 (SON-HYPER) ;
  - ne reprend **pas** le code : 3,9 % identique, au niveau du fond.

**Intérêt**
- Contenu propre : CUSTOMIZE/EXTRA (style ALPHA2/ALPHA3), choix des 3 révisions, son CPS1, entraînement. Rien qui
  manque à Hyper.
- Construction depuis l'ISO :
  - `X_DATA` e206 (programme), e207–e222 ;
  - `Y_DATA` 97–131 pour la musique PS2 ;
  - l'arcade `sfa`/`sfau` sert de référence (son identique, à vérifier pour les graphismes).

---

## 4. ro2 — Street Fighter Zero 2 (1996)

**Identité**
- En-tête : version 3, `zero2_usa.bin`. Copyright `0x3729B1` « @1996,2006 CAPCOM U.S.A., INC. ».
- Chaînes `0x3BDBE6` : « STREET », « ZERO 2 », « ALPHA 2 ».
- **Roster** :
  - `0x2EF4C0` (pas de `0x18`) : RYU, KEN, GOUKI, NASH, CHUN-LI, ADON, SODOM, GUY, BIRDIE, ROSE, VEGA, SAGAT, DAN,
    SAKURA, ROLENTO, DHALSIM, ZANGIEF, GEN, puis CHUN-LI2, GOUKI2 ;
  - `0x2F0D90` (pas de 8) : les 18, plus SHIN-GOUKI.
  - Ce sont des **noms japonais**.
- **SECRET OPTION** : 96/02/27, 96/03/06, 96/04/30.
- Valeurs EXTRA : ZERO2 / ZERO2A / ZERO3 / ARCADE / LONG. Le reste comme ro1, sans CPS1 ; il y a en plus ORIGINAL
  COMBO, ORICOM GAUGE, COMMAND LIST.
- **Propre à ro2** : en tête des données (`0x2DB210–0x2DB660`), une **liste de 18 différences de version** en
  japonais. Exemples : « 00:(ザンギ)垂直ジャンプ中Kが 削れない/削れる », « 13:(癲癇)タイトル画面のフラッシング ON/OFF »,
  « 17:(ALL)タイトル画面 ダッシュ/アレンジ ». Elle sert sans doute à paramétrer les révisions ; usage non vérifié.

**Machine** : RAM `0x800000` ; Z80 `0x80–0x235A0` ; 32 natives (couche commune) ; **pas de pilote ADX** : aucun appel
à `0x155510` / `0x1552D0`, son tout QSound.

**Traducteur** : 98,7 % (97,0 % sans correction) ; 0 non résolu ; 148 tremplins.

**Ressources** : il porte le **groupe commun SFA2**, e224–e252.
- `b` charge e225 (emplacement 0), e227 (1), e228 (2), e249 (3), Z80 e250, QSound e251.
- Banques **e229–e248** (dynamiques). e226 (fenêtre des plans) n'est pas cité par `b`.
- Pour le reste, voir CARTE-sfa2 §1.3 (e251 = `sz2.11m/12m`, ROM graphique complète).

**Liens**
- 93 % identique à ro8, 91 % à ro4 ; avec SFA3, seulement le fond commun.
- **Hyper** : banques e229–e248 pour ZERO 2 et ALPHA (ids `$40–$7F`), dont **e248 = Cammy** (ids `$5E` / `$7E`,
  table ro9 `0x5AF1B0`). Pas de code ni de données repris ; musique ZERO 2 d'Hyper = Y70–88 (ADX), pas le QSound de
  ro2.

**Intérêt** : décors SFA2 (CARTE-sfa2) ; ressources communes de toute la famille. **Absent du menu US** (§9.3).

## 5. ro4 — Street Fighter Zero 2 Alpha (arcade, 1996)

- En-tête : version 5. Chaînes « ZERO2ALP / ZR2ALPHA… » en `0x5765B6`, copyright `0x57D1D1`.
- Chaînes ASCII du menu de test arcade en `0x588967…` : « 3 SOUND & VOICE », « 6 GAME DATA », « QSOUND RAM »,
  « HIT TBL PTR », TURBO.
- **Roster** :
  - `0x31D540` : les 18, CHUN-LI2, SHIN AKUMA, ZANGIEF2, DHALSIM2, EVIL RYU, M.BISON2, SAGAT2, KEN2, RYU2,
    CHUN-LI3, SAKURA2 ;
  - `0x31EE90` : les 18, SHIN-AKUMA, (EX)ZANGIEF, (EX)DHALSIM, EVIL RYU, (EX)M.BISON, (EX)SAGAT, (EX)KEN, (EX)RYU,
    (EX)CHUN-LI.
  - Noms occidentaux.
- SECRET OPTION : **96/08/05** seulement. EXTRA : ALPHA2 / ALPHA3 / ARCADE / LONG.
- Machine : RAM `0x800000`, Z80 en tête, 30 natives, son QSound seul (pas d'ADX).
- Traducteur : 98,8 % ; 0 non résolu ; 158 tremplins.
- Ressources : **aucune propre**. `b` charge exactement les fichiers de ro2 (e225, e227, e228, e249, e250, e251).
  e349 (TIM2) n'est pas cité.
- Liens : 88 % identique à ro2 ; données à 95 % dans ro6. Les ids EX d'Hyper reprennent ses persos, mais pas ses
  données.
- **Absent du menu US** (§9.3).

## 6. ro6 — Street Fighter Zero 2 Dash = Alpha 2 Gold console avec Cammy

**Identité**
- En-tête : version 7, champ `+20` = `0xB00` (`0xA80` ailleurs). Chaînes « ZERO2ALP… » en `0x56D516`.
- Copyright `0x574131` « @1996,2006 CAPCOM U.S.A., INC. ALL RIGHTS RESERVED. ».
- **Roster** :
  - `0x30B470` : celui de ro4, **+ CAMMY** (30) ;
  - `0x30CDE0` : 27, **+ CAMMY**.
- SECRET OPTION : **97/10/23** (date console). Menus comme ro4.

**Machine**
- RAM `0x800000`, **Z80 à la fin** (`0x2D1750–0x2F4C70`).
- **Recompilateur mixte** (17 % de CMP « anciennes », comme ro3).
- 32 natives, dont le **pilote ADX** (`0x2F4ED0`, homologue de ro3 `0x393190`) et `0x2F5090`.
- Appelle aussi les banques SPU2 (`0x155C60`, `0x155E60`, `0x155EF0`).

**Traducteur** : 98,8 % (base juste par hasard) ; 0 non résolu ; 191 tremplins.

**Ressources** (`b`)
- Chargés :
  - e527 (emplacement 0, format **`CSTG`** inconnu, 4 Mo) ;
  - e529 (1, mémoire de tuiles brute) ;
  - e530 et e531 (2-3 : conteneurs 16×16 de 28 720 et 26 432 tuiles, les sprites) ;
  - e535 (5 : conteneur 32×32, 2 304 tuiles) ;
  - **Z80 e250 et QSound e251 de ro2** (pas les siens).
- Non cités : e528 (conteneur, fenêtre des plans, comme e226), e532 (Z80 propre, différent de e250), e533 (QSound
  propre, différent de e251 à 99 %), e534 (32×32, jumeau de e535). Probablement morts, ou chargés autrement.
- Musique : table ADX exéc. `0x4FD328` → **Y170–188, Y190–228** (≈ 46 min, 144 Mo ; codes `0x02C1–0x02FC`).

**Liens**
- 71 % identique à ro4 (MIPS) et 82 % au niveau 68K. Il reste 506 Ko « autres », pour moitié dus au recompilateur
  ancien. Cammy et les changements console sont à chercher dans le reste.
- **Hyper** :
  - ses **musiques ALPHA** (codes `0x02C1–0x02D2`, `0x02FC` → Y170–187, Y229) sont les flux de ro6 ;
  - Cammy ALPHA d'Hyper (`$7E`, grille `0x5C5380` : `7E 16 FF FF`) utilise la banque **e248 du groupe ro2**, pas les
    fichiers de ro6 ;
  - aucun code repris.

**Intérêt** : seule source de la **musique ALPHA** d'Hyper (déjà utilisée telle quelle) ; Cammy version Alpha 2
Gold (Hyper l'a déjà). Rien d'autre à porter.

## 7. ro7 — Pocket Fighter / Super Gem Fighter Mini Mix (1997)

**Identité**
- En-tête : version 8. Chaînes « POCKET », « pocket » en `0x372F18`.
- Copyrights `0x383391` / `0x3833B1` « @CAPCOM CO., LTD. 1997,2006 » / « @CAPCOM U.S.A., INC. 1997,2006 ».
- **URL `http://www.capcom.co.jp/` et `mailto:pocket@ capcom.co.jp`** (`0x38356C`).
- **Roster** :
  - `0x24B480` (pas de `0x18`) : RYU, KEN, CHUN-LI, SAKURA, MORRIGAN, HSIEN-KO, FELICIA, TESSA, IBUKI, ZANGIEF,
    DAN, AKUMA ;
  - même liste en `0x24CE80` (pas de 8).
- SECRET OPTION : **97/09/01, 97/09/04**. Options propres : MT GAUGE, GUARD CRUSH, BREAK FALL, COUNTER ATTACK, ITEM
  ATTACK / CARRIER / HIT ITEM, MEGA CRUSH, COUNTER CRUSH, PURSUIT ATTACK, gemmes RED/YELLOW/BLUE, boutons
  PUNCH/KICK/SPECIAL, JOIN IN.
- **Jeu caché ? Non.** Il est en position 4 de la table du menu US (`b` `0xC900`), sans condition de SELECT (§9.3).
  « Pocket Fighter » est son nom dans `b`.

**Machine**
- RAM **`0x660000`** (seule base non multiple de `0x80000`).
- Z80 `0x21E0–0x2C980`, précédé des aides et de 2 natives (`0x40–0x21E0`).
- 32 natives, dont le pilote ADX (`0x239980` / `0x239B30`, et `0x239D90` → `0x1555C0`).

**Traducteur** : 98,4 % (97,0 % sans correction) ; 0 non résolu avec `CODE0` par défaut ; 2 tremplins.

**Ressources**
- `b` charge e537 (conteneur 16×16 de 65 536 tuiles = quart 0), e538 (fenêtre des plans), e539 (16×16, 32 768),
  Z80 e540, QSound e541. L'image TIM2 est e542, au lieu de e549.
- **Aucune banque dynamique.**
- **e541 = `pcf.11m` + `pcf.12m` (`sgemf.zip`) échangés : identique sur 8 Mo ; e540 = région audio MAME de
  `pcf.01`/`pcf.02`, exacte.**
- Y_DATA propres :
  - table exéc. `0x43D548` → **Y530–542** (13 musiques en boucle) ;
  - exéc. `0x43F3B0` → Y90–91, Y93–95 (en boucle) ;
  - exéc. `0x4413B0` → **Y281–432** (152 clips courts de 3 à 4 s, voix et jingles).
  - ⚠️ **Correction de SON-HYPER §2.3** : Y530–542 ne sont pas des « variantes » d'Hyper. Ce sont les musiques de
    Pocket Fighter, absentes de la table commune de ro3/ro5/ro9.

**Liens** : isolé. ≤ 7,7 % identique à n'importe quel module, 55,6 % de données neuves. Hyper n'en reprend rien.

**Intérêt** : aucun pour Hyper ou Upper. Un « Pocket Fighter depuis l'ISO » se ferait avec `sgemf` :
- son identique ;
- graphismes en conteneurs `anthgfx` ;
- programme : soit l'arcade, soit le module traduit.

## 8. ro8 — Street Fighter Alpha 2 (occidental, 1996)

- En-tête : version 9. Copyright `0x49F5A1`.
- **Roster** :
  - `0x2FFB80` : les 18 (noms occidentaux), CHUN-LI2, SHIN AKUMA, ZANGIEF2, DHALSIM2, EVIL RYU ;
  - `0x301400` : les 18, SHIN-AKUMA, (EX)ZANGIEF, (EX)DHALSIM, EVIL RYU.
- SECRET OPTION : 96/03/06, 96/04/30. EXTRA : ALPHA2 / **ALPHA2G** / ALPHA3 / ARCADE / LONG ; CUSTOM COMBO.
- Machine : RAM `0x800000`, Z80 en tête, 30 natives, QSound seul.
- Traducteur : 98,8 % ; 0 non résolu ; 150 tremplins.
- Ressources : **aucune propre**. Le groupe e543 ne contient que le programme ; `b` charge les fichiers de ro2.
- Liens : 92 % identique à ro2 ; pour CARTE-sfa2 §1.2, ses données sont proches de l'Europe 960229.

---

## 9. b — menu des jeux et couche système (`sub_usa.bin`)

### 9.1 Rôle et table des jeux

- **C natif** (aucun banc 68K ni Z80), base d'exécution **`0x1C8000`** (en-tête `+8`). Taille : code `0xC8C0`,
  données `0x7580`.
- Contenu :
  - écran titre (« PRESS START BUTTON », « NOW LOADING ») ;
  - carte mémoire, installation sur disque dur, balayage progressif, DualShock (anglais et japonais SJIS) ;
  - messages de jeux secrets.
- Il **reste résident** pendant les jeux : ro1 à ro8 appellent `0x1CB320` (déblocage) et `0x1CB520`. ro9 ne les
  appelle pas.
- **Table des jeux** : fichier `0x13690` (exéc. `0x1DB690`), 9 × 180 octets (`b_jeux.py` → `b_jeux.txt`). Chaque
  enregistrement contient :
  - nom (`0x1DB580…`) ;
  - le mot 1 ;
  - **son** : 2 = Z80/QSound chargés, 0 = pilote natif ;
  - entrée X_DATA du programme ;
  - **adresse libre = base RAM 68K + `0x64000`** ;
  - **12 emplacements** (u16 type, u16 entrée, adr1, adr2) : 0–7 graphismes, 8–9 son, 10–11 fichiers à adresse
    fixe ;
  - le TIM2 (e549, ou e542 pour ro7) et le **point d'entrée**.

| index | nom (`b`) | module | son | points d'entrée (exéc.) | fichiers chargés |
|---|---|---|---|---|---|
| 0 | Street Fighter Zero | ro1 (e206) | 2 | `0x1F1FE0` | e207 ; Z80 e221, QSound e222 |
| 1 | Street Fighter Zero 2 | ro2 (e224) | 2 | `0x215520` | e225, e227, e228, e249 ; e250, e251 |
| 2 | Street Fighter Zero 3 | ro3 (e253) | 0 | `0x572EC0` | e254, e256, e312, e313 (annonceur) ; **e289 → `0xA04000`**, emplacement fixe `0xA75000` |
| 3 | Street Fighter Zero 2 Alpha | ro4 (e348) | 2 | `0x2152C0` | = ro2 |
| 4 | Street Fighter Zero 3 Upper | ro5 (e350) | 0 | `0x214A80` | e351, e353, e525, e313 ; **e390 → `0xB04000`**, `0xB83800` |
| 5 | Street Fighter Zero 2 Dash | ro6 (e526) | 2 | `0x4A4DE0` | e527, e529, e530, e531, e535 ; e250, e251 (de ro2) |
| 6 | Pocket Fighter | ro7 (e536) | 2 | `0x1F1D60` | e537, e538, e539 ; e540, e541 |
| 7 | Street Fighter Alpha 2 | ro8 (e543) | 2 | `0x2154B0` | = ro2 |
| 8 | Hyper Street Fighter Zero | ro9 (e544) | 0 | `0x21FA40` | e545, e546, e548, e313 ; **e547 → `0xC84000`** |

Recoupements avec le travail déjà fait :
- e289 en `0xA04000` (ro3, HANDOFF §75) et e547 en `0xC84000` (profil ro9 `data_ext`) ;
- e313 en EE `0x1341800` pour Hyper (SON-HYPER §1.3) ;
- les adresses de chargement des emplacements dynamiques (`0x112A000`, `0x11C9800` : persos J1/J2 de ro3) ;
- **e390** = fichier de frames fixe d'Upper (`0xB04000`, comme le `0xB00000` de CARTE-ro9 §4.4).

e204 (TIM2) = e549, à l'octet près.

### 9.2 Lancement d'un module

- `b` fichier `0x83E0` (exéc. `0x1D03E0`) :
  1. `memset(0x1DC050, 0, 0x20)` ;
  2. pointeur = `0x1DB690 + index × 180`, rangé dans `[0x1DC050]` ;
  3. **`jal 0x156EE0`**, fonction de l’exécutable, que seul `b` appelle parmi les 10 modules. C'est elle
     qui décompresse et charge le MWo3 et les emplacements, puis saute au point d'entrée.
- L'appelant est en `0x11DC` (machine d'état du menu). L'index vient de :
  - **la table menu → jeu** au fichier `0xC900` : **`00 07 05 02 06 08`** (puis `07 05 04`), soit SFA, SFA2 (ro8),
    SFA2 Gold (ro6), SFA3, Pocket Fighter, Hyper ;
  - puis de la fonction SELECT au fichier `0xE10` (§9.3).
- Nombre d'entrées : `ctx+4` vaut 5, plus 1 si la fonction de l'exécutable `0x14EC20` rend 0, −4 ou −6
  (fichier `0xC80–0xD8C`). Son rôle n'est pas identifié.

### 9.3 Jeux secrets (SELECT)

- **Fonction SELECT** (fichier `0xE10`) : si SELECT (`0x100`) est tenu et que le bit de déblocage
  `[*(0x19E438)+220]` est posé :

| choisi | bit | lancé |
|---|---|---|
| 2 (Zero 3) | `0x4` | **4 (Upper)** |
| 3 (Zero 2 Alpha) | `0x2` | 5 (Zero 2 Dash) |
| 1 (Zero 2) | `0x1` | 7 (Alpha 2) |
| 0 (Zero) | `0x8` | 8 (Hyper) |

- **Pose des bits** (fichier `0x3320` = exéc. `0x1CB320`, appelé par les modules) :
  - code `0xF5` → bit `0x8` ;
  - sinon table fichier `0xCF00` (jeu courant, code) : (1, `0xC8`) → `0x1`, (3, `0xC9`) → `0x2`, (2, `0xCA`) → `0x4`,
    (6, `0xCB`) → rien.
- **Messages** :
  - en anglais : « Secret Game 1 … Choose STREET FIGHTER ALPHA 3 while holding SELECT » et « Secret Game 2 …
    Choose STREET FIGHTER ALPHA » ;
  - en japonais : Secret Game 1–4 = ZERO 2 / ZERO 2 ALPHA / ZERO 3 / ZERO.
- **Conséquences statiques pour le menu US** :
  - Upper = SFA3 + SELECT ✔ ;
  - **ro2 (Zero 2) et ro4 (Zero 2 Alpha) ne figurent pas dans la table US et ne sont la cible d'aucun SELECT
    atteignable** ⟹ probablement inaccessibles en US, alors que leurs ressources servent à ro4, ro6, ro8 et Hyper ;
  - SFA + SELECT mène à l'index 8, Hyper, qui est aussi en 6ᵉ position de la table.
  - **À vérifier en jeu** : quelles entrées sont visibles et ce que vaut `0x14EC20`.

---

## 10. Intérêt pour le projet et construction depuis l'ISO

1. **Contenus de l'Anthology absents de l'arcade**, par module :
   - SECRET OPTION (choix de révision : 2 à 3 révisions arcade par jeu) ;
   - CUSTOMIZE / EXTRA OPTION (règles façon autre épisode : ALPHA2G, ZERO3, ADVANCED…) ;
   - TRAINING MENU avec enregistrement ;
   - COLOR EDIT, DISPLAY ADJUST ;
   - son CPS1 (ro1) ;
   - Cammy dans Alpha 2 Gold (ro6) ;
   - musiques ADX réarrangées (ro1 : Y97–131 ; ro6 : Y170–228 ; ro7 : Y530–542) ;
   - liste des différences de version (ro2).

   **Pour HSFA**, seuls comptent la musique ALPHA (ro6, déjà jouée par Hyper via ses flux) et les banques des
   groupes ro1 et ro2 (déjà utilisées par Hyper). Rien d'autre n'est à porter vers Hyper ou Upper.
2. **Script de construction depuis l'ISO**. Fichiers d'entrée, lus dans `X_DATA.BIN` (ISO `0x9F738000`) et
   `Y_DATA.BIN` (`0xAB628800`) avec `iso.py` :

| module | MWo3 | graphismes | son | Y_DATA |
|---|---|---|---|---|
| ro1 | e206 | e207, e208–e220 | e221, e222 | 97–131 |
| ro2, ro4, ro8 | e224 / e348 / e543 | e225–e228, e249, e229–e248 | e250, e251 | — |
| ro6 | e526 | e527–e531, e534, e535 (format `CSTG` de e527 à étudier) | e250, e251 (e532, e533 ?) | 170–228 |
| ro7 | e536 | e537–e539 | e540, e541 | 90–95, 281–432, 530–542 |
| b | e203 | e204, e205 | — | — |

   Une option simple pour ro1, ro7 et la famille SFA2 : le son de l'ISO est **identique à l'arcade** (Z80 en
   disposition MAME, QSound échangé). Le programme 68K peut venir du traducteur (98,2 à 98,8 %, après les correctifs
   du §1.3) ou de l'arcade. Les graphismes sont à reconvertir avec `anthgfx` / `cps2rom` (à vérifier tuile à tuile
   pour ro1 et ro7, comme CARTE-sfa2 l'a fait pour SFA2).
3. **Ordre conseillé** si l'on veut traduire l'un de ces modules :
   1. base RAM ;
   2. bornes par zones et `read_jump_table` ;
   3. `AIDES_RECOMP` par module ;
   4. profil de `mame_test` : points d'entrée à trouver (le point d'entrée de `b` donne le premier) ;
   5. pilote CPS2 d'origine (`sfa`, `sfa2`, `sgemf`) comme banc : **la ROM arcade sert de référence**, ce qui manque
      pour Hyper.


---

## Annexe — scripts et sorties (`<workspace>/hsfa/work/carto_modules/`)

| script | rôle | sortie |
|---|---|---|
| `commun.py` | copie de carto_ro9, avec `starts`/`funcs` par zones 68K | |
| `zones.py` | zones Z80 / 68K | |
| `chaines.py`, `chaines_ech.py`, `sjis.py`, `table_noms.py`, `autour.py`, `cherche_texte.py`, `libelles.py` | chaînes ASCII, mots échangés, SJIS, tables de noms | `chaines_*.txt`, `sjis_*.txt` |
| `b_jeux.py`, `desas.py` | table des jeux de `b`, désassemblage | `b_jeux.txt`, `dis_b.txt` |
| `census_mod.py` (`RAMFIX=1`) | recensement par zones | `census_<mod>[_base].txt` |
| `essai_mod.py`, `nonresolus.py` | assemblage à blanc | `essai_<mod>.txt` |
| `aides.py`, `natives_mod.py` | aides du recompilateur, natives et homologues ro3 | `natives_mod.txt` |
| `style_cmp.py` | formes de CMP | `style_cmp.txt` |
| `comparaison_mod.py`, `couverture_mod.py`, `id68k.py` | parenté du code | `comparaison_mod.txt`, `couverture_mod.txt`, `id68k_*.txt` |
| `donnees_mod.py` | parenté des données | `donnees_mod.txt` |
| `ou_y.py` (copie d'agent_hyper_son) | tables ADX → Y_DATA | `ou_y.txt` |
| `chargeurs.py`, `banques.py`, `xdata_refs.py`, `conteneurs.py`, `iso.py` | ressources X_DATA | `chargeurs.txt`, `banques.txt`, `conteneurs.txt` |

Exécution : `nice -n 19` ; numpy via `<workspace>/venv/bin/python3` ; `PYTHONPATH=…/scripts/untranspile` pour
`modcompare`.

**Non vérifié** (exécution exclue) :
- visibilité réelle des entrées du menu US et rôle de `0x14EC20` ;
- mécanisme de chargement des banques e208–e220 et e229–e248 par ro1 et ro2 ;
- usage de e528, e532–e534 (ro6) ;
- format `CSTG` (e527) ;
- complétude des graphismes de ro1 et ro7 par rapport à l'arcade.
