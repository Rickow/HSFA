# Partitions pour la musique d'Hyper : pilotes v1.0x, banc Z80, origine des variantes

Session du 2026-10-14. Plan d'ensemble : [PLAN-SON-HYPER](PLAN-SON-HYPER.md). Outils : `tools/son-hyper/partitions/`.
Données lues dans les zips MAME de l'utilisateur (`sfa`, `sfa2`, `ssf2`, `ssf2t`, `hsf2`, `ffight`, `sf2hf`),
**jamais publiées** :
le dépôt ne contient que les outils et les mesures (codes, durées).

## 0. En bref

- **SSF2, SSF2T, SFA1 et SFA2 ont des pilotes Z80 de la même génération** : v1.04, v1.04, v1.05A, v1.05C. Même
  routine de commande, même format de morceau ; seul l'en-tête change d'adresse chez SSF2.
- La grille d'opcodes de v1.71 (`src/hsfa/z80son.py`), avec **le seul opcode `05` (tempo) passé à 2 octets**,
  parcourt **100 % des pistes de musique** des quatre jeux. Un convertisseur v1.0x → v1.71 unique est donc possible.
- **Banc Z80** (`mesure_boucles.py`) : on fait tourner le pilote d'origine et on mesure intro et boucle de chaque
  morceau. Calibration sur 32 morceaux déjà appariés (ZERO, ZERO 2) : **durée du flux ADX = intro + une boucle**, à
  3 % près pour 24 d'entre eux (médiane 1,005).
- **Variantes, jeu A (Y553-586, ~81 Mo d'ADX) = Super SF2** : 18 flux sur 34 à ≤ 0,25 %, 25 à ≤ 1 %, 30 à ≤ 2 %.
  Le bloc du 2ᵉ code (index 17-30) suit **dans l'ordre** les codes SSF2 `0x11-0x1E` (14/14 à ≤ 1,1 %).
- **SSF2T a la même musique que SSF2** (61/62 morceaux identiques octet pour octet, le 62ᵉ à durée égale) et
  **_Hyper SF2_ (v1.06b) est identique à SSF2T octet pour octet** (62/62) : ni l'un ni l'autre n'apporte de musique.
- **Jeux B, C et flux longs** : ni SSF2 / SSF2T / *Hyper SF2*, ni *Final Fight* (CPS-1). *SF2 Hyper Fighting* (CPS-1)
  ne correspond pas non plus, mais sa mesure n'est pas fiable (§4).
- **Sources documentaires (§5)** : en mode Hyper, SHADALOO-D (rose) joue le thème de *SF2* arcade, SHADALOO-B
  (bleu) le thème de la **version 3DO** de *Super SF2X*, et un titre bleu (personnages *SF2'*) la musique de *SF2'*.
  Rapproché des tables d'Hyper : A = SHADALOO-D (cohérent avec la mesure), *hypothèses* C = 3DO, B = *SF2'*, flux
  longs = *Final Fight* d'une version console.

## 1. Pilotes Z80

| jeu | version (chaîne en `0x000E`) | en-tête / table | entrée de commande | N |
|---|---|---|---|---|
| `ssf2` | ` version 1.04 /CPS2  1993 / NOVEM. [SF2]` | `$7C10` / `$7C16` (zone fixe) | `[$10 \| banque, H, L, x]` | `$1FF` |
| `ssf2t` | `version 1.04 /CPS2  1993 / NOVEMBER` | `$9000` / `$9006` | `[b, H, L, x]` linéaire 24 bits | `$1FF` |
| `sfa` | `version 1.05A /CPS2  1993 / JUNE` | `$9000` / `$9006` | idem | `$300` |
| `sfa2` | `version 1.05C /CPS2  1996 / FEB.` | `$9000` / `$9006` | idem | `$400` |
| `hsf2` | `version 1.06b /CPS2  1996 / APR.` | `$9000` / `$9006` | idem | — |
| `ffight` (CPS-1) | `version 2.00` | — | autre pilote (YM2151 + OKI) | — |
| `sf2hf` (CPS-1) | `version 4.25` | — | autre pilote (YM2151 + OKI) | — |

Repérage de la table chez SSF2 : même suite d'instructions que v1.05 (`sbc hl,de ; jr nc ; add hl,de ; add hl,hl ;
add hl,hl ; ld de,TABLE ; add hl,de ; ld b,(hl) …`, `$01EF` chez SSF2, `$021B` chez SFA1), avec `ld hl,$7C10` et
`ld de,$7C16` au lieu de `$9000` / `$9006`.

Images : `image_z80.py` (disposition MAME ; SFA1 a **deux** ROM Z80, `sfz.01` + `sfz.02` en `0x28000`).

## 2. Parcours des pistes (`parcours_v10x.py`)

| jeu | morceaux de musique | pistes parcourues | en boucle (opcode `16`) | instruments distincts |
|---|---|---|---|---|
| sfa | 40 | 597 / 597 | 36 | 65 |
| sfa2 | 58 | 861 / 861 | 50 | 65 |
| ssf2 | 62 | 812 / 812 | 60 | 60 |
| ssf2t | 62 | 811 / 811 | 60 | 60 |
| hsf2 | 62 | 811 / 811 | 60 | 60 |

Musique = priorité `0`, au moins 4 voies. Tempos 16 bits distincts : 36 (sfa), 34 (sfa2), 43 (ssf2). Leur passage
en 8 bits (v1.71) est le premier point à étudier pour le convertisseur.

## 3. Banc Z80 (`mesure_boucles.py`)

Émulateur : paquet pip `z80` (cœur C++, appels Python seulement sur les adresses marquées). Carte mémoire de MAME
`cps2` ; IRQ à 250 Hz **maintenue jusqu'à sa prise en compte** (HOLD_LINE). Poignée de main du 68K, relevée dans le
pilote :
- au démarrage, le Z80 écrit `$77` en `$CFFF` et attend `$FF` (68K prêt) ;
- l'IRQ (`$0038`) ne lit la boîte aux lettres que si `$CFFD = $88` ;
- commande : `$C000-$C00F`, postée quand `$C00F ≠ $FF` ; le Z80 la recopie en `$F100 + $F007` et remet `$FF`.

Mesure : point de lecture sur l'opcode `16` de chaque piste. 1er passage = fin de la 1re boucle, écart entre deux
passages = boucle. Environ 3 s de calcul pour 300 s de musique.

**Calibration** (`resultats/mesures_sfa*.tsv` contre `tools/flux/hsfa_flux_table.txt`) :

| famille | morceaux | rapport flux / (intro + boucle) |
|---|---|---|
| ZERO (SFA1 `0x01-0x0C`, `0x32`) | 13 | médiane 1,005 ; 8 entre 0,97 et 1,03 |
| ZERO 2 (SFA2 `0x01-0x12`, `0x35`) | 19 | médiane 1,005 ; 16 entre 0,97 et 1,03 |

Écarts à revoir : Y56 / Y70 (0,90), Y58 (2,19 : deux boucles ?), Y62 / Y76 (0,79 : flux coupé ?) ; plus près de
la limite : Y61 (0,956), Y74 (0,958), Y66 (1,033).

## 4. Origine des variantes (`compare_variantes.py`)

Affectation un pour un des flux aux morceaux mesurés, sur la durée intro + boucle (`resultats/variantes_ssf2.tsv`) :

| jeu | flux | SSF2 / SSF2T ≤ 0,25 % | ≤ 1 % | ≤ 2 % | *Final Fight* ≤ 1 % |
|---|---|---|---|---|---|
| **A** (Y553-586) | 34 | **18** | **25** | **30** | 3 |
| B (Y494-527) | 34 | 2 | 7 | 14 | 2 |
| C (Y460-493) | 34 | 4 | 6 | 17 | 2 |
| longs | 19 | 0 | 0 | 0 | 1 |

Jeu A, appariement par position (index k → code SSF2 `0x01 + k` pour les thèmes, `0x11 + (k − 17)` pour le 2ᵉ code) :
- **index 17-30 → `0x11-0x1E`** : 14/14 à ≤ 1,06 %, dont 9 à ≤ 0,2 % ;
- **thèmes 0-15 → `0x01-0x10`** : 9/16 à ≤ 0,8 % ; 7 entre 2,3 et 6,2 % (index 2, 5, 7, 8, 11, 12, 13) : autre ordre,
  révision, ou écart de mesure ;
- index 16 (35,9 s) : pas d'équivalent dans SSF2 (Akuma ?) ; index 31-33 : sans correspondance (`0x1F`, `0x20`).

Ce qui reste une **hypothèse** :
- le 2ᵉ code = musique accélérée quand la vie est basse : on sait seulement qu'il correspond aux codes `0x11-0x1E` de
  SSF2 ;
- la preuve par la durée n'est pas une preuve par le son : à confirmer par empreinte MFCC + DTW (SON-HYPER-ROM) avec
  l'ISO.

**SSF2T** : 52 morceaux communs à durée identique (à 0,05 s près), aucun nouveau. Comparaison des octets de toutes
les pistes : 61/62 morceaux identiques à SSF2, seul `02` diffère (même durée). **_Hyper SF2_** : 62/62 morceaux
identiques octet pour octet à SSF2T. Ni l'un ni l'autre n'apporte de musique de plus que SSF2.

**Final Fight** (`mesure_cps1.py`, pilote CPS-1 « version 2.00 », musiques `0x40-0x5F`, alias en `0xA0+`) :
- 10 morceaux bouclent de façon mesurable (`40-44`, `46-49`, `55`) ; les autres sont des jingles ou ne se répètent
  pas assez pour la mesure ;
- au plus 3 rapprochements à ≤ 1 % par jeu de variantes, aucun à ≤ 0,25 % : **pas de correspondance**. Réserve : ce
  banc n'est pas calibré (aucun flux CPS-1 connu).

**SF2 Hyper Fighting** (pilote CPS-1 « version 4.25 », musiques `0x01-0x22`, `0x34-0x35`) : boucles mesurées de 70 à
157 s et intros de 40 à 50 s pour des thèmes de SF2, **invraisemblables** : cadence ou variantes du pilote mal
reproduites par le banc. Aucune correspondance, mais **pas de conclusion** tant que la mesure n'est pas fiable.

Détection CPS-1 : les key-on sont comparés par cases de 10 ms (± 1 case), sans tenir compte de leur ordre dans une
même case. Boucle = plus petit décalage (≥ 4 s) qui reproduit 98 % des événements de la 2ᵉ partie ; intro = 1re
fenêtre de 2 s retrouvée une boucle plus loin.

## 5. Sources documentaires : ce qui déclenche chaque musique

Recherche du 2026-10-14 (guide officiel BradyGames lu par OCR, wikis japonais et anglophones). Aucune source ne donne
de liste de pistes par mode ; ce qui suit relie des descriptions de modes aux tables de SON-HYPER §1.

**Les modes d'Hyper** (guide BradyGames p. 6-7, atwiki, Niconico). Une fois la version *Zero 3* choisie, quatre modes :
Normal, Mazi (本気), Saikyo, Classic. Start + ← / → sur un mode = sa version cachée, un S-ISM *SHADALOO* :

| couleur | nom | depuis | effet (atwiki) | musique (Wikipédia ja) |
|---|---|---|---|---|
| vert | SHADALOO-C | Normal | style *Darkstalkers* : chain combos, guard cancel gratuit | — |
| bleu | SHADALOO-B | Mazi | style *SF3* : parades, super cancels, une seule super | personnages de *Super SF2X* : thème de la **version 3DO** |
| rose | SHADALOO-D | Saikyo | style *SF2* : limité aux 12 personnages de *SF2'*, leurs systèmes et statistiques | thème de ***SF2* arcade** |
| rouge | SHADALOO-A | Classic | coups supplémentaires (Ken de *CvS*, Final Vega) | — |

Pour les versions *Zero*, *Zero 2*, *Zero 2 Alpha*, Start change la couleur du titre. **Titre bleu** (Niconico) : les
personnages venus de *SF2'* passent en version *SF2'* (« ZERO2' » à la place de la jauge, pas de super), **et la
musique devient celle de *SF2'***. Témoignage de 2006 (NeoGAF, non vérifié) : un Ryu EX « façon *SF2* » de
*Zero 2 Alpha* joue son thème de *SF2*.

**Rapprochement avec les tables** (SON-HYPER §1 : `T_5c9680` variante A si `$133` < 0, `T_5c96d0` variante B,
`T_5c9720` EX / `$15F`) :

| jeu de flux | table | mesure (§4) | source documentaire la plus proche |
|---|---|---|---|
| A (Y553-586) | variante A | **= SSF2 arcade** | SHADALOO-D : « *SF2* arcade » — cohérent |
| C (Y460-493) | variante B | ni SSF2 ni *Final Fight* ; ≈ 10 % plus long | *hypothèse* : SHADALOO-B, arrangement 3DO (audio CD, sans partition) |
| B (Y494-527) | EX / `$15F` | ni SSF2 ni *Final Fight* | *hypothèse* : titre bleu, musique de *SF2'* (CPS-1 ; banc `sf2hf` non fiable) |
| longs | EX, ids `$18+` | rien | *hypothèse* : *Final Fight* d'une version console (« FF », « FF3 » lisibles sur le wiki Seesaa) |

Indices : l'album 3DO de *Super SF2X* a **17 thèmes de personnages, dont Akuma**, absent de SSF2 arcade (l'index 16
du jeu A reste sans équivalent). Le wiki Seesaa du jeu, illisible pour nos outils (EUC-JP), laisse voir dans sa partie
BGM « EX / CPS1 / X / CPS2 », « FF3 », « FF » et « ZERO2ALPHA → PS / SS » (= famille ALPHA, établie).

**Sound test** (atwiki, Wikipédia ja, Niconico) : arcade des trois *Zero* et leurs arrangements console, dont *Zero 2*
**Super Famicom** ; série *SF2* ; *Final Fight* ; *Super Puzzle Fighter II X* (chanson de Sakura *Kono omoi wo
tsutaetai*, message d'avertissement du CD). La plupart de ces pistes ne s'entendent pas en combat. TCRF signale des
**ADX orphelins** dans les réglages son de certains jeux (*Pocket Fighter* Saturn/PS, *Super Puzzle Fighter II Turbo*,
*Marvel vs. Capcom*, *Red Earth*, *SF3*) : candidats parmi les 588 flux de `Y_DATA.BIN` non référencés par Hyper.

**Le guide BradyGames** ne dit rien de la musique ; il documente les modes et les révisions (Zero 95/06/05, 95/06/27,
95/07/27 ; Zero 2 96/03/06, 96/04/30 ; Zero 3 98/06/29, 98/07/27).

Sources : [Wikipédia (ja)](https://ja.wikipedia.org/wiki/ストリートファイターZERO_ファイターズ_ジェネレーション) ·
[atwiki](https://w.atwiki.jp/gcmatome/pages/3259.html) ·
[Niconico](https://dic.nicovideo.jp/a/ストリートファイターzero%20ファイターズ%20ジェネレーション) ·
[Seesaa sfh21](https://seesaawiki.jp/w/sfh21/d/%A5%CF%A5%A4%A5%D1%A1%BC%A5%B9%A5%C8%A5%EA%A1%BC%A5%C8%A5%D5%A5%A1%A5%A4%A5%BF%A1%BCZERO) ·
[TCRF](https://tcrf.net/Street_Fighter_Alpha_Anthology) ·
[NeoGAF](https://www.neogaf.com/threads/street-fighter-alpha-collection-hidden-modes-hyper-street-fighter-zero-revealed.102127/) ·
[3DO OST (titres)](https://audiomack.com/thatkid_frank/album/super-street-fighter-ii-turbo-ost-3do) ·
*Street Fighter Alpha Anthology Official Strategy Guide*, BradyGames (Adam Deats, Joe Epstein).

## 6. Conséquences pour le plan

- **Jeu A en partition** : sa source (SSF2) a le même format de pilote que SFA1/SFA2. Gain visé : ~81 Mo d'ADX.
- **Convertisseur v1.0x → v1.71** : commence par le tempo (16 → 8 bits) ; le reste de la grille est commun.
- **Jeux B, C, longs (~312 Mo)** : sources encore inconnues. Écartés : SSF2T, *Hyper SF2*, *Final Fight*. Restent :
  SF2 CPS-1 (`sf2`, `sf2ce`, et `sf2hf` une fois le banc CPS-1 fiabilisé), versions console arrangées (*Street
  Fighter Collection*, *Hyper SF2 Anniversary* PS2…). Sinon : compression (PLAN-SON-HYPER §6).
- **Jeu C** : si c'est bien l'arrangement 3DO (§5), il n'a **aucune partition** → compression d'office.
- **Jeu B** : si c'est *SF2'* (CPS-1), sa partition existe mais demande l'adaptation FM → QSound (PLAN §4.4) ou une
  carte son CPS-1 ; d'abord fiabiliser le banc CPS-1 sur `sf2hf`.
- **Test décisif au banc** : sélectionner chaque mode et sa version cachée (§5), et les titres bleus, puis relever
  `$133`, `$122`, `$15F` et le code musique envoyé : quelle table, donc quel jeu de flux, répond à quel mode.

## 7. Fichiers

| fichier | rôle |
|---|---|
| `image_z80.py` | image Z80 (disposition MAME) depuis le zip de l'utilisateur |
| `pilote_v10x.py` | table de commandes et en-têtes de morceaux v1.04 / v1.05 |
| `parcours_v10x.py` | parcours des pistes avec la grille de `src/hsfa/z80son.py` (`05` sur 2 octets) |
| `mesure_boucles.py` | banc Z80 QSound : intro et boucle par morceau |
| `mesure_cps1.py` | banc Z80 CPS-1 (YM2151 + OKI) : période des key-on (non calibré) |
| `compare_variantes.py` | appariement flux ↔ morceaux mesurés |
| `apparie_vgm.py` | appariement flux ↔ packs VGM par durée de boucle (en-têtes ADX / VGM) |
| `resultats/mesures_*.tsv` | intro et boucle mesurées (sfa, sfa2, ssf2, ssf2t, ffight, sf2hf — ce dernier non fiable) |
| `resultats/variantes_ssf2.tsv` | appariement des variantes avec SSF2 |
