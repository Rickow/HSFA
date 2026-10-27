# Plan — la musique d'Hyper (`ro9`) : partitions d'abord, flux compressés pour le reste

Version du 2026-10-16. Elle remplace le plan du 2026-10-14, écrit **avant** les mesures au banc Z80. Elle intègre :
- les mesures des pilotes son d'origine (`tools/son-hyper/mesures_z80.tsv`, `variantes_ssf2.tsv`) ;
- les recherches de la session « coulisses de Street Fighter Alpha » (wikis japonais, TCRF, Wikipédia) sur les modes
  d'Hyper et l'origine de chaque bande-son ;
- `tools/flux/hsfa_flux_table.txt` (drapeau `q`).

Sources internes : [SON-HYPER](SON-HYPER.md), [SON-HYPER-ROM](SON-HYPER-ROM.md), [FLUX](FLUX.md),
[REJEU-FBNEO](REJEU-FBNEO.md). La session « coulisses » cite un rapport `PARTITIONS-HYPER` qui n'est pas dans le
dépôt (à ajouter s'il existe).
Légende : **établi** = mesuré ou vérifié ; *hypothèse* = à confirmer par l'étape indiquée.

## 0. En bref

- Hyper joue sa musique en **flux ADX** enregistrés : **217 flux, 696 Mo, 3 h 38 min** (établi). L'arcade joue des
  **partitions** : séquences Z80 de quelques Ko, plus une ROM d'échantillons QSound.
- **But** : jouer en partitions tout ce qui en a une (pilote Z80 + QSound, comme en arcade), et **compresser** le reste
  (Vorbis, environ 4,5 fois plus petit que l'ADX).
- **Qui a une partition** (après identification) :

  | famille | partition | décision |
  |---|---|---|
  | ZERO 3 (SFA3) | oui, déjà jouée en QSound par le cœur | **retirer les flux** du paquet (phase 1) |
  | ZERO 3, persos d'Upper (`0x30-0x36`) | **non** : cette musique n'a jamais existé sur CPS-2 | flux compressé |
  | ZERO (SFA1), ZERO 2 (SFA2) | oui (pilotes v1.05A et v1.05C) | **partitions** (phase 2) |
  | variantes, jeu A | oui : **= *Super SF2* arcade** (établi) | **partitions** (phase 3) |
  | variantes, jeu C | *hypothèse* : arrangement **3DO** = audio CD, donc pas de partition | flux compressé |
  | variantes, jeu B | **pas *SF2'* arcade** (mesuré) ; origine inconnue, à identifier à l'oreille | flux compressé |
  | variantes, 19 flux longs | **pas *Final Fight* arcade** (mesuré) ; *hypothèse* : une version console | flux compressé |
  | ALPHA | **non** : arrangement PlayStation (audio XA) / Saturn (flux ADPCM) | flux compressé |

- Ordre de grandeur (estimé à 53 Ko/s d'ADX) : après les phases 1 à 3, il reste environ **400 Mo d'ADX**. Compressés
  en Vorbis, ils font environ **90 Mo**, contre 696 Mo aujourd'hui.

## 1. Ce qui a changé depuis le plan du 2026-10-14

| point | plan du 14 | état au 16 |
|---|---|---|
| origine du jeu A | *hypothèse* SSF2 / SSF2T | **établi** : *Super SF2* arcade ; 25 flux sur 34 à ≤ 1 %, 32 à ≤ 2,5 % ; ordre de la table de commandes respecté |
| SSF2 et SSF2T | deux révisions possibles (A et B) | **même musique** : *Hyper SF2* = SSF2T octet pour octet, un seul morceau diffère entre SSF2 et Turbo (même durée). B ne peut donc pas être SSF2T |
| jeu C | SF2 CPS-1, à adapter (FM) | *hypothèse* : arrangement 3DO (thèmes des persos de *Super SF2X* en SHADALOO-B), donc **sans partition** |
| jeu B | SSF2T | **pas *SF2'* arcade** : mesuré au banc CPS-1 (§3.4), aucune concordance, même à un autre tempo. Les wikis disent pourtant « musique de *SF2'* » pour les titres bleus : sans doute un autre enregistrement ou arrangement |
| ALPHA | « chercher si une version console a des séquences » | **réglé** : PlayStation en audio XA, Saturn en flux ADPCM ; pas de séquences |
| ZERO 3 | `0x01-0x33` déjà en QSound | **corrigé** : seuls les codes marqués `q` dans `hsfa_flux_table.txt` le sont (44 flux). `0x30-0x36` = persos d'Upper, sans QSound |
| conversion v1.05 → v1.71 | « opcodes à vérifier un par un » | grille d'opcodes **identique de v1.04 à v1.71**, sauf le tempo (2 octets → 1). Vérifié par le parcours statique (`parcours.py`) |
| méthode d'identification | packs VGM (`apparie_vgm.py`) | **banc Z80** sur les pilotes d'origine (`mesure_boucles.py`), plus précis et sans téléchargement. `apparie_vgm.py` reste utile pour le CPS-1 |

## 2. Qui appelle quoi : modes d'Hyper et jeux de flux

D'après les wikis japonais, recoupés par les mesures :

| mode / réglage | musique jouée | jeu de flux | codes | Y_DATA |
|---|---|---|---|---|
| SHADALOO-D (rose, Saikyo) | thèmes de *SF2* arcade | **A** (variante A) | `0180-01A1` | Y553-586 |
| SHADALOO-B (bleu, Mazi), persos de *Super SF2X* | arrangement **3DO** (qualité CD) | **C** (variante B) | `01C4-01E5` | Y460-493 |
| titre bleu, persos de *SF2'* | musique de *SF2'* | **B** (variante EX) | `01A2-01C3` | Y494-527 |
| EX et autres identifiants | ? | longs | `01E6-01F7`, `01FE-01FF` | Y433-439, Y528-529, Y543-552 |

Attention aux noms : le **jeu de flux C** est appelé par la **variante B** du programme, et le **jeu de flux B** par la
**variante EX**.

Dans chaque jeu de 34 flux, les index 0-16 sont les 17 thèmes du roster de *Super SF2 Turbo*. Les index 17-33 sont un
2ᵉ code (`T_5c97d0`) : *hypothèse* « musique accélérée quand la vie est basse », toujours à vérifier au banc (`$C3B6`).

## 3. Mesures (établi)

### 3.1 Méthode (`tools/son-hyper/mesure_boucles.py`)

- Le pilote Z80 d'origine tourne dans un émulateur Z80 (paquet Python `z80`). Le banc joue le rôle du 68K : poignée de
  main au démarrage (`CFFD = 0x88`, `CFFF = 0xFF`), puis commande postée dans la boîte aux lettres (`C000-C001`,
  `C00F`).
- Un point de lecture sur l'opcode `16` (saut de boucle) de chaque piste donne la fin de l'intro et la durée de boucle.
- **Calibrage** sur SFA1 et SFA2, déjà identifiés : un flux de l'Anthology dure « intro + une boucle », à 3 % près pour
  24 morceaux sur 32.
- **Limite (2026-10-16)** : la boucle mesurée est la plus longue des boucles de piste. Le rendu audio
  (`rendu_partitions.tsv`) montre qu'elle est fausse pour 4 morceaux de SFA1 / SFA2 sur 32 (`03`, `04`, `08`, SFA2
  `11`), et qu'un morceau (SFA1 `07`) n'a pas de période courte. Les comparaisons de durées gardent leur valeur
  statistique, mais une ligne isolée peut être fausse.
- Pilotes lus (`pilote.py`) : SFA1 v1.05A et SFA2 v1.05C (en-tête `0x9000`), SSF2 v1.04 (en-tête `0x7C10`), SSF2T
  v1.04 (en-tête `0x9000`). *Hyper SF2* (v1.06b) n'est pas encore décrit dans `pilote.py`, et les pilotes CPS-1 ne
  sont pas pris en charge.
- Image Z80 : `image_z80.py` reconstruit la région `audiocpu` de MAME depuis les fichiers `.01` / `.02` du zip.
- **Reproduction (2026-10-16)** : SFA2 refait depuis `sfa2.zip`, **identique ligne pour ligne**. SSF2T mesuré depuis
  `ssf2t.zip` : identique à SSF2 pour 62 morceaux sur 63 ; seul `02` diffère (15 voies au lieu de 16, 55,69 s au lieu
  de 55,72 s), c'est le morceau qui distingue les deux jeux. SFA1 refait depuis `sfa.zip` : **identique ligne pour
  ligne**.
- **Limite de `variantes_ssf2.tsv`** : la règle d'association flux → code n'est pas décrite. Une affectation un pour
  un sur les seules durées ne la retrouve pas (54 à 81 lignes sur 121 selon la méthode), mais redonne la même image : A
  32/34 à ≤ 2,5 % ; B 20, C 19, longs 1. Une durée seule est un indice faible (une soixantaine de durées candidates
  entre 10 et 90 s) : ce qui fait la force du jeu A, c'est que presque tous ses flux concordent et que l'ordre de la
  table de commandes est respecté.

### 3.2 Résultats contre *Super SF2* (`variantes_ssf2.tsv`)

| jeu de flux | flux | ≤ 0,4 % | ≤ 1 % | ≤ 2,5 % | > 5 % | conclusion |
|---|---|---|---|---|---|---|
| A | 34 | 19 | 25 | 32 | 0 | *Super SF2* |
| B | 34 | 4 | 7 | 15 | 8 | pas SSF2 |
| C | 34 | 4 | 6 | 17 | 11 | pas SSF2 |
| longs | 19 | 0 | 0 | 0 | 19 | pas SSF2 |

Cas à vérifier dans le jeu A :
- **index 16** (Akuma, `2F` à 1,95 %) : *Super SF2* arcade n'a pas de thème d'Akuma, l'association est sans doute
  fausse. L'album 3DO, lui, en a un. Ce flux reste en flux compressé ;
- **index 5 et 11** (`05` à 4,5 %, `03` à 4,7 %) : écart nettement plus grand que les autres ; écoute nécessaire. L'un
  d'eux est peut-être le morceau qui diffère entre SSF2 et Turbo.

### 3.3 SFA1 et SFA2 (`mesures_z80.tsv`)

Les codes `01` à `0C` de SFA1 et de SFA2 ont **les mêmes durées** au centième près (sauf `09`). C'est cohérent avec
l'histoire : Alpha 2 refait une grande partie des morceaux d'Alpha 1. Mêmes partitions et même tempo, mais
**instruments différents** : il faut garder les deux familles.

### 3.4 Banc CPS-1 : *SF2'* et *Final Fight* (`banc_cps1.py`, `mesures_cps1.tsv`)

- Le pilote CPS-1 n'a pas d'opcode de boucle commun avec le CPS2. Le banc émule le Z80, les **timers du YM2151** (qui
  cadencent le pilote) et relève les notes de chaque voie FM. La boucle est la plus petite période qui se répète
  dans l'ordre des notes, voie par voie. Les voies d'un morceau sont décalées entre elles mais donnent toutes la
  même boucle (par exemple *SF2'* `01` : 8 voies sur 8 à 46,72 s, à quelques ms près).
- *SF2'* (pilote « version 4.25 », timer A à 4,0 ms) : 26 codes de musique, 21 avec une boucle de 5 s ou plus.
- *Final Fight* (pilote « version 2.00 », timer A à 8,0 ms pour le tempo, timer B à 3,15 ms pour lire les commandes) :
  musique en `40-58`, 14 boucles de 5 s ou plus.
- **Résultat (`compare_durees.py`)** :

  | mesures | jeu A | jeu B | jeu C | longs |
  |---|---|---|---|---|
  | SSF2T | **24** / 34 | 12 | 8 | 0 / 19 |
  | *SF2'* | 7 | **5** | 7 | 0 |
  | *Final Fight* | 4 | 4 | 4 | **0** |
  | SFA2 (témoin sans rapport) | 4 | — | — | — |

  (flux à ≤ 1 % de leur morceau associé). *SF2'* et *Final Fight* restent au niveau du hasard. Même en laissant
  libre un facteur de tempo (×0,7 à ×2,5), aucun ne dépasse le témoin SFA2 (10 à 12 flux par hasard) : **le jeu B
  n'est pas *SF2'* arcade, et les flux longs ne sont pas *Final Fight* arcade**.
- Limite : le banc CPS-1 est neuf et n'a pas de référence externe. Contrôle simple : dans MAME, `sf2hf` code `01`
  doit boucler à 46,7 s après 3,5 s d'intro. Les packs VGM de VGMRips donnent aussi les boucles
  (`apparie_vgm.py`).
- Conséquence : B et les flux longs n'ont **pas de partition connue**. Ils restent en flux compressé, sauf si
  l'écoute leur trouve une autre origine.

## 4. Architecture : la « carte musique »

Rappel (SON-HYPER-ROM §12) : le Z80 principal ne peut pas accueillir cette musique. Il n'a **ni numéros de commande
libres, ni entrées libres, ni bit de banque**. La musique passe donc par une carte dédiée dans le pilote HSFA :
- le fork intercepte les codes musique d'Hyper à `$61801F = 0`, comme le lecteur de flux aujourd'hui ;
- le Z80 principal reçoit `FF05` : sa musique s'arrête, les voix et les bruitages continuent ;
- les fondus `FF07` et l'arrêt `FF00` sont transmis aux deux.

### 4.1 Décision à prendre : pilotes d'origine ou conversion en v1.71

| option | principe | pour | contre |
|---|---|---|---|
| **A. pilotes d'origine** | la carte charge le Z80 de SFA1, de SFA2 ou de SSF2 selon la famille du morceau, avec sa ROM d'échantillons | **aucune conversion** : tempo et timbres exacts. Le rejeu des voix lit déjà les échantillons de SFA1 et SFA2 (`e222`, `e251` de `X_DATA.BIN`) | trois images Z80 et trois ROM d'échantillons à gérer ; changement d'image entre deux morceaux |
| **B. conversion en v1.71** | un seul pilote (SFA3) et une ROM musique neuve qui rassemble les séquences converties et les instruments | un seul pilote ; table de commandes propre | tempo 16 bits → 8 bits : **dérive des boucles** ; fréquences d'échantillons à corriger (SFA1 20-24 kHz, SFA2 12 kHz) ; ROM musique à construire |

**Recommandation : commencer par l'option A.** Elle donne un résultat exact sans convertisseur, et l'essentiel existe
déjà : les pilotes tournent au banc, et les échantillons de SFA1 et SFA2 sont déjà lus pour le rejeu. L'option B reste
le recours si la place, la charge processeur ou le nombre d'instances QSound posent problème.

### 4.2 Quel QSound

Le 2ᵉ QSound sert déjà au rejeu des voix SFA1 et SFA2. Deux choix :
1. un **3ᵉ QSound** dédié à la musique ; il faut une 3ᵉ instance du code QSound de FBNeo ;
2. **partager le 2ᵉ** : voies 0-11 pour la musique, 12-15 pour le rejeu (les voix utilisent les voies 12 et 14).

Avec l'option A, la musique et les voix d'une même famille partagent déjà la même ROM d'échantillons, ce qui favorise
le partage. Décision après mesure des voies réellement utilisées (phase 2, étape 4).

## 5. Plan d'action

### Phase 1 — retirer les flux ZERO 3 doublés par le QSound (gain immédiat)

> **2026-10-16 : rendue optionnelle** (`HSFA_FLUX_SANS_Q=1`). En Ogg Vorbis elle ne fait gagner que 27 Mo
> (201 → 174 Mo) ; l'utilisateur garde tous les flux en Ogg. Étapes 1-4 faites et vérifiées en jeu.

1. `tools/fbneo-hsfa/paquet_fbneo.py` : ne plus embarquer les flux marqués `q` dans `hsfa_flux_table.txt` (44 flux).
   **Garder** `0x30-0x36` (persos d'Upper, sans QSound).
2. Vérifier ce que fait le cœur si l'option « PS2 music » vaut `All tracks` et qu'un flux manque : il doit retomber sur
   le QSound, sans silence.
3. Non-régression : `tools/hyper-etats/tournee_hyper.lua` en mode 1 ; WAV et journal comparés au cœur actuel.
4. Recalculer le gain réel (attendu : un peu plus de 100 Mo).

### Phase 2 — ZERO et ZERO 2 en partitions (≈ 112 Mo d'ADX en moins)

Détail, architecture et étapes : [PLAN-PARTITIONS-HYPER](PLAN-PARTITIONS-HYPER.md) (carte musique : 2ᵉ Z80 avec
le pilote d'origine, 3ᵉ QSound sur la ROM du rejeu).

1. Prototype au banc MAME, option A : la carte musique fait tourner le Z80 SFA1 ou SFA2 et reçoit les codes interceptés.
   Correspondances établies : ZERO `0x41+k` → SFA1 `0x01+k`, `0x4D` → `0x32` ; ZERO 2 `0x51+k` → SFA2 `0x01+k`,
   `0x63` → `0x35`.
2. Validation par morceau : intro et boucle mesurées (`mesure_boucles.py`), empreinte contre le flux (SON-HYPER-ROM),
   écoute.
3. Niveau sonore recalé sur le flux (le volume de la table varie de 45 à 134 selon le morceau).
4. Mesure des voies utilisées, puis décision 3ᵉ QSound ou partage (§4.2).
5. Port FBNeo (`cps_hsfa.cpp`), états de sauvegarde, non-régression.

### Phase 3 — jeu A (*Super SF2*) en partitions (≈ 80 Mo d'ADX en moins)

1. ROM `ssf2` ou `ssf2t` fournie par l'utilisateur, contrôlée par les sommes MAME. La musique est la même ; préférer
   celle qui donne les meilleurs écarts sur les index 5 et 11.
2. Ajouter SSF2 à la carte musique (option A : 3ᵉ image Z80 et ses échantillons).
3. Table de correspondance flux → code SSF2 depuis `variantes_ssf2.tsv`. Exclure l'index 16 (Akuma), qui reste en flux.
4. Validation comme en phase 2.

### Phase 4 — identifier B et les flux longs (sans engagement de conversion)

1. **Jeu C = 3DO ?** Comparer les durées des flux Y460-493 aux durées des pistes de l'album 3DO de *Super SF2 Turbo*.
   Si ça concorde, C reste en flux compressé : il n'existe pas de partition.
2. ~~Jeu B = *SF2'* ?~~ **Fait** (§3.4) : non, pas *SF2'* arcade. Reste à l'identifier **à l'oreille** : écouter
   Y494 (index 0) à côté du thème de Ryu de *SF2'*. Pistes : une version console de *SF2'* (Super Famicom, PC
   Engine, Mega Drive…) ou un enregistrement retravaillé.
3. **Flux longs** : pas *Final Fight* arcade (§3.4). Écoute, puis comparaison avec les versions console (*Final
   Fight CD* sur Mega-CD, en audio CD : pas de partition).
4. **2ᵉ code** : au banc, baisser la vie d'un joueur et relever `$C3B6` et la commande envoyée.
5. Livrable : mise à jour de ce plan et de `variantes_ssf2.tsv` (ou un `variantes.tsv` général).

L'adaptation FM → QSound du CPS-1 (rendu des instruments YM2151 en échantillons) n'est **pas prévue** : beaucoup de
travail, fidélité incertaine. On ne la reconsidère que si B est confirmé *SF2'* et que le résultat compressé ne convient
pas à l'écoute.

### Phase 5 — compresser tout ce qui reste (≈ 400 Mo d'ADX → ≈ 90 Mo)

Concerne : persos d'Upper, ALPHA, jeux B et C, flux longs, index 16 du jeu A, et tout morceau qui échoue aux phases 2-3.

Détail : [PLAN-VORBIS](PLAN-VORBIS.md).

1. Ajouter `stb_vorbis` : **il n'est pas dans FBNeo** au commit `af5d3f3` (vérifié le 2026-10-16 ; seuls dr_mp3 et
   dr_flac y sont). Opus est absent aussi.
   Le système de samples de FBNeo décode tout au chargement : il est inutilisable ici.
2. Garder `tools/flux/hsfa_flux.h` (lecture par blocs, boucles, fondus, états) et remplacer seulement le décodeur ADX.
3. Boucles exprimées en échantillons dans `hsfa_flux_table.txt` ; état sauvegardé par position.
4. Encodage Vorbis à 80-96 kbit/s ; WAV de contrôle avant / après ; niveau recalé.

| format | débit | ratio contre l'ADX | remarque |
|---|---|---|---|
| **Vorbis** | 80-96 kbit/s | ÷ 4,5 à 5,4 | premier choix : seek exact, boucles sans trou |
| Opus | 32-48 kbit/s | ÷ 9 à 13 | meilleur, mais absent de FBNeo |
| MP3 | 160 kbit/s | ÷ 2,7 | délai d'encodeur à compenser aux boucles |

La compression ne dépend pas des phases 2 à 4 : elle peut avancer en parallèle.

## 6. Bilan attendu

| étape | ADX restant (estimé) |
|---|---|
| aujourd'hui | 696 Mo |
| après la phase 1 | ≈ 590 Mo |
| après la phase 2 | ≈ 480 Mo |
| après la phase 3 | ≈ 400 Mo |
| après la phase 5 (Vorbis) | ≈ 90 Mo, plus quelques Ko de tables |

## 7. Risques et points ouverts

- **Index 5, 11 et 16 du jeu A** : à écouter avant de les basculer en partition.
- **Hypothèses C, B et longs** : C vient des wikis ; B et longs sont écartés de *SF2'* / *Final Fight* arcade par la
  mesure. Elles décident seulement de ce qui reste en flux, pas du gain des phases 1 à 3.
- **Option A** : charge processeur d'un Z80 et d'un QSound de plus sur les consoles portables (probablement faible, à
  mesurer) ; changement d'image Z80 entre deux morceaux sans craquement.
- **Option B** : dérive du tempo 8 bits ; fréquences d'échantillons.
- **Données** : tout est construit chez l'utilisateur depuis ses fichiers (ISO, `X_DATA.BIN`, ROM SSF2). Le dépôt ne
  contient que les outils et les tables.

## 8. Outils (`tools/son-hyper/`)

| fichier | rôle |
|---|---|
| `pilote.py` | lecture des pilotes Z80 v1.04 / v1.05 : table de commandes, morceaux, pistes |
| `parcours.py` | parcours statique des pistes avec la grille d'opcodes de `src/hsfa/z80son.py` (tempo sur 2 octets) |
| `mesure_boucles.py` | banc Z80 : intro et boucle de chaque morceau. Dépendance : `pip install z80` |
| `apparie_vgm.py` | rapprochement flux ADX ↔ packs VGM par durée de boucle (testé sur fichiers synthétiques seulement) |
| `image_z80.py` | image `audiocpu` (format MAME) depuis les fichiers `.01` / `.02` d'un zip CPS2 |
| `mesures_z80.tsv` | mesures de SFA1, SFA2, SSF2 et SSF2T |
| `banc_cps1.py` | banc des pilotes son CPS-1 (Z80 + timers du YM2151) : boucle voie par voie, sans connaître le format |
| `mesures_cps1.tsv` | mesures de *SF2'* (`sf2hf`) et de *Final Fight* |
| `compare_durees.py` | flux d'Hyper (jeux A, B, C, longs) contre un fichier de mesures : association un pour un, statistiques |
| `rendu_partitions.py`, `rendu_qsound.cpp`, `hsfa_qsound.h` | rendu WAV d'un morceau par son pilote d'origine (banc Z80 + QSound du cœur) ; contrôle de boucle par spectrogrammes |
| `rendu_partitions.tsv` | contrôle des 32 morceaux ZERO / ZERO 2 |
| `variantes_ssf2.tsv` | flux des jeux A, B, C et longs contre SSF2 |

```bash
python3 -I tools/son-hyper/image_z80.py sfx.01 sfx.02 ssf2t.bin
python3 -I tools/son-hyper/mesure_boucles.py ssf2t ssf2t.bin 01-3f,c1 --secondes 400
python3 -I tools/son-hyper/apparie_vgm.py Y_DATA.BIN packs/ --tol 0.4 --top 3
```

## 9. Sources externes

- [Wikipédia (ja) — Street Fighter ZERO Fighters' Generation](https://ja.wikipedia.org/wiki/ストリートファイターZERO_ファイターズ_ジェネレーション)
- [ゲームカタログ@Wiki — Fighters' Generation](https://w.atwiki.jp/gcmatome/pages/3259.html)
- [ニコニコ大百科 — Fighters' Generation](https://dic.nicovideo.jp/a/ストリートファイターzero%20ファイターズ%20ジェネレーション)
- [Wikipedia — Street Fighter Alpha Anthology](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_Anthology)
- [TCRF — Street Fighter Alpha Anthology](https://tcrf.net/Street_Fighter_Alpha_Anthology)
- [VGMRips — CP System II](https://vgmrips.net/packs/system/capcom/cp-system-ii)
- [libretro/FBNeo `samples.cpp` au commit `af5d3f3`](https://github.com/libretro/FBNeo/blob/af5d3f3/src/burn/snd/samples.cpp)
