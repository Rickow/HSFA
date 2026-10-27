# Session cloud du 2026-10-07 au 2026-10-16 : récapitulatif pour les sessions locales

Session Claude Code dans le cloud (claude.ai/code), **sans données de jeu** : pas d'ISO, pas de `work/`, pas de MAME.
Seules les ROM arcade fournies par l'utilisateur ont servi aux bancs (`sfa`, `sfa2`, `sfa3`, `ssf2t`, `sf2hf`,
`ffight`). Elles ne sont jamais allées dans le dépôt.

Tout est sur la branche **`claude/zealous-darwin-4wgvrd`**, partie de `main` au commit `38959a3` (2026-10-11).
`main` n'a pas été modifié.

## 1. Récupérer le travail

```bash
git fetch origin claude/zealous-darwin-4wgvrd
git log --oneline main..origin/claude/zealous-darwin-4wgvrd     # les commits de la session
git merge origin/claude/zealous-darwin-4wgvrd                   # dans une copie à jour de main
```

Fichiers touchés hors ajouts : `docs/journal/HANDOFF.md` (sections §149 et §150 ajoutées à la fin),
`docs/rapports/README.md`, `tools/README.md`, `tools/fbneo-hsfa/README.md`, `tools/fbneo-hsfa/paquet_fbneo.py`,
`tools/flux/hsfa_flux.h`, `patches/fbneo/README.md`. Si une session locale a ajouté ses propres §149 / §150 au
journal, renuméroter les miennes à la fusion.

## 2. Ce qui a été fait (dans l'ordre des commits)

| commit | contenu | où lire |
|---|---|---|
| `3babb2c` | origine des musiques d'Hyper : **jeu de flux A = *Super SF2* arcade** ; scripts de banc Z80 de la session « son » (hors dépôt jusque-là) ; plan mis à jour | `docs/rapports/PLAN-SON-HYPER.md`, journal §149 |
| `8bd47a8`, `0a5c334`, `0a8f5a8` | banc Z80 **reproduit** depuis les ROM : SFA1 et SFA2 identiques ligne pour ligne ; SSF2T = SSF2 sauf `02` ; `image_z80.py` | `tools/son-hyper/mesures_z80.tsv` |
| `adea6f1`, `a2bb74c` | **banc CPS-1** (Z80 + timers du YM2151) : *SF2'* et *Final Fight* mesurés ; ni le jeu B ni les flux longs n'en viennent | PLAN-SON-HYPER §3.4, `tools/son-hyper/mesures_cps1.tsv` |
| `2dfda8b`, `1830c1b` | **cœurs Windows x64** (MinGW-w64, liaison statique), notice, frontaux de test sous Wine | `tools/windows/` |
| `cbda030`, `46cf7c3` | **musique en Ogg Vorbis** : patchs FBNeo 8 et 9, encodeur branché dans `paquet_fbneo.py`, banc de 23 contrôles ; **phase 1** : flux ZERO 3 omis du zip d'Hyper | `docs/rapports/PLAN-VORBIS.md`, journal §150 |
| `46b2152` | plan de la **carte musique** (partitions SFA1 / SFA2 jouées par leurs pilotes d'origine) | `docs/rapports/PLAN-PARTITIONS-HYPER.md` |
| `3e4bbec` | carte musique, étape 1 : **rendu hors ligne** des 32 morceaux ZERO / ZERO 2 et contrôle automatique ; limite du banc de boucles documentée | PLAN-PARTITIONS-HYPER « État », `tools/son-hyper/rendu_partitions.tsv` |
| (suivants) | récapitulatif ; **carte musique dans le cœur** : `hsfa_musique.h`, patch FBNeo 10, `HSFA_PARTITIONS=1` dans `paquet_fbneo.py`, bancs avec le Z80 de test et celui de FBNeo | PLAN-PARTITIONS-HYPER « État », journal §151 |

Chaque nouveauté est datée et décrite dans son rapport. Le journal (§149, §150) en donne la synthèse.

## 3. À faire en local, dans l'ordre

1. **Vorbis, zip d'essai d'Hyper** (le plus gros gain, ≈ 710 → 155-180 Mo) :
   ```bash
   cd tools/fbneo-hsfa
   HSFA_YDATA=<Y_DATA.BIN ou ISO> HSFA_FLUX_FORMAT=ogg python3 paquet_fbneo.py hyper
   ```
   Demande ffmpeg (libvorbis), g++, gcc, numpy. Noter la taille réelle et les flux restés en ADX (affichés).
2. **Cœurs Android et ROCKNIX** avec les patchs 1 à 9 (`patches/fbneo/README.md`). Un ancien cœur ne lit pas un zip
   Vorbis. Les cœurs Windows sont déjà faits et ont été envoyés à l'utilisateur.
3. **Un match** avec le zip Vorbis : départs, boucles, fondus. Journal `HSFA_FLUX_LOG` à comparer avec celui de
   l'ADX. Puis mesure sur la RGB10X (étape 7 de PLAN-VORBIS).
4. Si tout va bien : `HSFA_FLUX_FORMAT=ogg` par défaut dans `paquet_fbneo.py`.
5. **Carte musique** : zip d'Hyper avec `HSFA_PARTITIONS=1` (et `HSFA_FLUX_FORMAT=ogg`), cœurs avec les patchs 1-10 ;
   matchs avec des persos en version ZERO et ZERO 2 : départs, boucles, fondus, pause, états ; journal du cœur
   (« HSFA musique : 2 pilotes, 32 codes »).
6. **Écouter les rendus des partitions** (32 fichiers Ogg envoyés à l'utilisateur, hors dépôt) et les comparer aux
   flux PS2 du même code. Les refaire depuis `X_DATA.BIN` :
   `python3 tools/son-hyper/rendu_partitions.py sfa --z80 <e221> --qs <e222>` (de même `sfa2` avec `e250` / `e251`).
7. Vérifier le **CRC de `e221` / `e250`** contre `sfz.01-02` / `sz2.01a-02a` (étape 0 de PLAN-PARTITIONS-HYPER).

## 4. Points à connaître

- **Phase 1 optionnelle** (décision finale de l'utilisateur, voir §6) : par défaut le zip d'Hyper garde tous ses flux,
  en Ogg (201 Mo). `HSFA_FLUX_SANS_Q=1` omet les thèmes de stage et jingles ZERO 3 (rejoués en QSound, 174 Mo).
- **`tools/flux/hsfa_flux.h`** du dépôt est maintenant la version des patchs FBNeo (avec Vorbis sous
  `#ifdef HSFA_FLUX_VORBIS`). Compilé sans cette définition, il garde le comportement ADX ; vérifié en C++98 pour le
  fork MAME.
- **Banc de boucles** (`mesure_boucles.py`) : la boucle mesurée est fausse pour 4 morceaux de SFA1 / SFA2 sur 32
  (`03`, `04`, `08`, SFA2 `11`), et SFA1 `07` n'a pas de période courte. Les comparaisons de durées restent valables
  en statistique, pas ligne par ligne.
- La règle d'association flux → code de `variantes_ssf2.tsv` (session « son ») n'est pas documentée et n'a pas pu être
  reproduite. La conclusion (jeu A = *Super SF2*) tient avec une méthode décrite (`compare_durees.py`).
- Une ancienne branche `claude/zealous-darwin-4wgvrd` (correctif Zangief, 2026-10-07) a été supprimée par
  l'utilisateur ; le même nom de branche porte maintenant ce travail.

## 5. Étapes suivantes possibles

- Option du cœur « ZERO / ZERO 2 music » (partitions / flux PS2), puis omission des flux ZERO / ZERO 2 du zip.
- Gains par morceau calés sur les flux PS2 (chez l'utilisateur, avec `Y_DATA.BIN`).
- *Super SF2* (jeu A) sur la même carte (ROM `ssf2t` de l'utilisateur).

## 6. Journal des essais sur Hyper (zip de l'utilisateur, 2026-10-16)

Le zip `sfa3hhsfa.zip` de l'utilisateur (743 Mo : flux ADX, rejeu) a été récupéré dans la session (kDrive, domaines
`kdrive.infomaniak.com` et `*.infomaniakusercontent.com` autorisés dans l'environnement). Il n'est pas dans le dépôt.
Frontal d'essai : `tools/fbneo-hsfa/essais/joue_linux.c` (charge le cœur, N images, journal du cœur, son en WAV,
captures BMP, entrées scriptées par `HSFA_ENTREES`).

- **Hyper tourne dans le cœur Linux construit avec les patchs 1 à 10** : flux (588 entrées, 558 codes) et rejeu
  (1 323 sons) lus dans le zip ; écran-titre correct après 3 600 images. Sans entrée, le jeu reste au titre : aucune
  musique de combat n'est demandée (journal des flux : `FF00`, `FF05`).
- **Pilotage** : `tools/fbneo-hsfa/essais/tournee.h`, portage C de `tournee_hyper.lua` (VERSUS, choix du perso et de
  la version par la RAM 68K exposée par le cœur, K.O. forcé). Lancer avec `HSFA_NOROUL=1 HSFA_TOURNEE="00.Z/01.Z"`.
  Ryu ZERO contre Ken ZERO : sélection (`$102` = `30` / `31`), 2 manches, écran de fin de match, en 20 000 images
  (19 s de calcul). Codes musique demandés : `0002` (sélection), **`0042`** (match, famille ZERO), `0004`.
- **Carte musique en jeu, essai réussi** (pilotes tirés de `sfa.zip` / `sfa2.zip` par `HSFA_MUSIQUE_DATA` /
  `HSFA_MUSIQUE_TABLE`) : le cœur annonce « HSFA musique : 2 pilotes, 32 codes » ; `0042` n'est plus joué en flux, la
  carte applique les fondus `FF07` ; déroulement du jeu identique à l'image près. Son : identique à la référence ADX
  hors du match ; pendant le match, spectrogrammes flux / carte 0,93 puis 0,86, **carte plus forte de +0,7 à
  +1,6 dB** (gain du morceau à ramener vers 85-90 %).
- **ZERO 2 en jeu** (Ryu Z2 / Ken Z2, `$102` = `40` / `41`) : `0052` joué par la carte (pilote SFA2) ; son identique hors
  du match ; même morceau que le flux (0,92 / 0,84), +0,9 à +1,6 dB.
- **Gains calés sur les vrais flux** (`tools/son-hyper/gains_partitions.tsv`, utilisés par `paquet_fbneo.py`) : niveau du
  flux PS2 tel que le cœur le joue divisé par celui de la partition, 45 à 71 % selon le morceau (`0063` : flux absent
  du zip, médiane). Match ZERO rejoué : écart flux / carte ramené à +0,2 / +0,5 dB.
- **Vorbis sur le vrai zip, 1ʳᵉ passe** : phase 1 active (43 flux ZERO 3 omis : 173 flux sur 216) ; mais le contrôle à
  corrélation ≥ 0,99 refusait 125 flux sur 173 (0,94 à 0,99 : normal pour un codec perceptif sur de la vraie musique ;
  les signaux de test synthétiques passaient à 0,9998). Zip : 743 → 503 Mo avec seulement 48 flux en Vorbis. Seuil
  ramené à 0,90 (les vraies erreurs donnent ≈ 0), durée, boucle et niveau toujours contrôlés ; 2ᵉ passe en cours.
- **Vorbis sur le vrai zip, 2ᵉ passe (seuil 0,90)** : les 173 flux passent en Vorbis (124 Mo au lieu de 695) ; **zip
  d'Hyper 743 → 172 Mo**. Avec les flux ZERO 3 gardés (`HSFA_FLUX_ZERO3=1`) : 216 flux, 215 en Vorbis et Y27 resté en
  ADX (corrélation 0,894), **zip 201 Mo**.
- **Vorbis en jeu** (même VERSUS, zip Vorbis + phase 1) : déroulement identique ; `0042` en Vorbis contre ADX :
  corrélation 0,954, niveau −0,01 dB. Phase 1 vérifiée en vrai : `0002` / `0004` (flux omis) échouent proprement
  (« entrée vide ») et le Z80 principal les joue en QSound.
- **Constat sur la phase 1** (corrigé après analyse) : à alignement égal, les versions QSound et PS2 ont le même niveau
  (`0002` : +0,1 dB ; `0004` : +0,6 dB). L'écart de −5,7 dB mesuré sur l'écran de fin de match vient de la **boucle** :
  le flux PS2 de `0004` reboucle toutes les 61,5 s, la version arcade joue le morceau puis retombe à un fond calme
  (vers 70-90 s). Spectrogrammes à niveau égal : 0,59 seulement (rendu ou mixage différents, à écouter). Un gain ne
  corrigerait donc rien. Avec Vorbis, la phase 1 ne
  fait plus gagner que 29 Mo (201 → 172). **Décision à prendre par l'utilisateur** : garder la phase 1 par défaut
  (musiques ZERO 3 arcade, −29 Mo), ou la rendre optionnelle (comportement PS2 « All tracks » inchangé).
- **États de sauvegarde en jeu** (`HSFA_ETAT_TEST` du frontal, état pris en plein match puis rechargé) : l'écart du son
  entre les deux passages est identique au bit près avec et sans la carte, alors que la musique diffère entre ces deux
  configurations : la carte (et le flux) se rejouent exactement. Un petit écart commun subsiste (corrélation
  0,996-0,999, écart max 1 490) : il ne vient ni de la carte ni du flux. Origine à chercher (Z80 / QSound principaux,
  rejeu, ou rechargement par le frontal) ; il existait avant les patchs 8-10.
- **Écoute de l'utilisateur** (extraits envoyés) : fin de match en version PS2 préférée ; sélection : pas de différence
  gênante. **Décision appliquée** : `paquet_fbneo.py` garde par défaut les 7 flux ZERO 3 d'écran (boucle, ≤ 25 s :
  `0002`, `0004`, `0005`, `0007`, `0008`, `002B`, `002C`) et omet les 36 thèmes de stage et jingles. Zip **174 Mo**.
  Vérifié en jeu : sélection, match et fin de match en Vorbis contre ADX : corrélation 0,955-0,998, niveau ≤ +0,2 dB.
- **Décision finale de l'utilisateur** (après les mesures) : le gain de la phase 1 étant faible en Vorbis, **tout reste
  en Ogg**, ZERO 3 compris. `paquet_fbneo.py` : la phase 1 ne s'applique plus que sur `HSFA_FLUX_SANS_Q=1`
  (l'ancienne variable `HSFA_FLUX_ZERO3=1` ne concerne plus qu'Upper et SFA3). Zip d'Hyper par défaut : **201 Mo**.
  La carte musique (`HSFA_PARTITIONS=1`) reste disponible mais n'est pas activée par défaut.
- **Pistes réellement utilisées en jeu** (question de l'utilisateur : le lecteur de musique des options embarque-t-il
  des pistes inutiles ?) : le zip ne contient que **216 entrées de `Y_DATA.BIN` sur 588**, celles que les tables
  musique du 68K peuvent demander (`SON-HYPER.md` §2.2) : 43 ZERO 3, 4 persos d'Upper, 13 ZERO, 18 ZERO 2, 19 ALPHA,
  119 variantes (A = X-ISM `$133` < 0, B, EX / CLASSIC `$15F`, et les 2ᵉ codes). Les 372 autres (sound test, modules
  SFA1 / SFA2 de l'Anthology, Y440-459 jamais envoyés) ne sont pas embarqués : vérifié sur le zip réel (aucune entrée
  non vide hors de la table, aucune de Y97-131 ni de Y440-459). Les différentes musiques d'un même perso selon le mode
  (ISM, version) sont bien des pistes de jeu.
- **2ᵉ code `$C3B6` confirmé en jeu** (frontal `joue_linux`, `HSFA_TOURNEE="00.Z3.iA/00.Z3.iX"`, Ryu X-ISM contre
  Ryu A-ISM, adversaire ramené à 1 PV) : la variante A démarre `0181 -> Y554`, puis passe à **`0192 -> Y571`** (vie
  basse) aux deux manches, avant `0004`. Les 51 flux des 2ᵉ codes servent donc bien. `tournee.h` sait maintenant
  choisir l'ISM (`.iX`, `.iA`, `.iV` : état 8 de l'écran de sélection, bas jusqu'à `$133` = ISM, puis bouton 1).
- **Cœurs ROCKNIX (aarch64) avec les patchs 1 à 10**, exécutés sous `qemu-aarch64` avec le zip Ogg : même match et
  mêmes musiques qu'au PC, son à ±1 près, 16:9 correct. Détail : `docs/rapports/ROCKNIX.md` §7. Kit d'essai console
  `tools/rocknix/essai_son/` (vitesse + musiques). Paquet `hsfa-rocknix-2026-10-16.zip` envoyé à l'utilisateur.
  **À faire sur la console** : `sh essai_son_hyper.sh` (> 60 images/s attendu), puis un match dans RetroArch.
- **Tournée complète d'Hyper dans le cœur FBNeo** (`tools/fbneo-hsfa/essais/tournee_complete.py`, zip tout en Ogg) :
  un VERSUS piloté par id jouable (J2 = perso essayé, J1 = Ryu), les 3 ISM en ZERO 3 : **151 matchs, 151 bons**
  (aucun plantage, perso et ISM choisis conformes, 2 manches, aucun flux en échec). Résultat :
  `tools/son-hyper/tournee_musiques.tsv`.
  - La musique de combat suit exactement les tables du 68K (`SON-HYPER.md` §2.2) pour ZERO 3, ZERO, ZERO 2 et ALPHA ;
    en X-ISM, les persos venus de SF2 passent sur leur variante A, avec la musique de vie basse (2ᵉ code).
  - 122 des 216 codes du zip entendus. Les 94 autres : variante B (`$122`, 34 codes avec leurs 2ᵉ codes), versions
    EX / `$15F` (48 codes), et 12 morceaux ZERO 3 hors VERSUS (jingles, continue, fins, menus : `0003`, `0005`-`0008`,
    `001B`, `0020`, `0029`, `002B`-`002D`, `002F`). Ils sont demandés par les tables, donc gardés ; la façon d'obtenir
    B et EX en jeu reste à trouver (sélection cachée, mode de jeu ?).
- **Cœurs Android avec les patchs 1 à 10** (NDK r28c, après autorisation de `dl.google.com` par l'utilisateur) :
  `tools/android/build_android.sh`, contrôles statiques bons (`tools/android/README.md`). Paquet
  `hsfa-android-2026-10-16.zip` envoyé (cœurs, notices, `A-LIRE-2026-10-16.md`). **À faire** : installer sur la
  console Android et jouer un match d'Hyper avec le zip Ogg.
- **Modes cachés** (indication de l'utilisateur : Start + droite ou gauche maintenus sur MAZI / SAIKYO / CLASSIC) :
  pilote étendu (`tournee.h` : `.m0`-`.m3`, `.e+1` / `.e-1`, `.v+` ; `joue_linux` : `HSFA_RAM_DUMP=1`) ; tournée
  des persos ZERO 3 en CLASSIC, MAZI + Start et SAIKYO + Start : 99 VERSUS bons. **194 codes sur 216 entendus**
  (CLASSIC → table « EX », MAZI + Start → variante B). Restent 10 codes `01E6`-`01F7` (versions EX de ZERO 2 /
  ALPHA ?) et 12 morceaux ZERO 3 hors VERSUS. Détail : `SON-HYPER.md` §2.3.
- **S-ISM et persos EX** (guide BradyGames fourni par l'utilisateur, « New ISM Choices ») : les modes cachés sont les
  S-ISM (curseur 6, 5, 7, 4 pour NORMAL, MAZI, SAIKYO, CLASSIC) ; Mazi S-ISM → variante B, CLASSIC et Saikyo S-ISM →
  table « EX ». Start tenu à la validation de la version → persos EX. Tournées : 231 VERSUS de modes, 52 de persos
  EX. Toujours 194 codes sur 216. Le pilote : `.m0`-`.m7`, `.vS`, `.g` (`tournee.h`), `--extra` (`tournee_complete.py`).
- **Patch 11, roulette sur Select** (remarque de l'utilisateur : pas de Select sur CPS2, il faut un autre raccourci ;
  choix de l'utilisateur : la touche Pièce, c.-à-d. Select de RetroPad). Le portage lançait la roulette avec Start
  (`$D3` recopié du bit de Start) ; le cœur écrit maintenant `$D3` d'après la touche Pièce, sur la grille seulement.
  Vérifié (x86 et ARM sous émulation) : Select tenu + bouton → perso au hasard ; Start tenu → EX Balrog (`$15` →
  `$25`), Cammy ALPHA `$7E`, EX de version, S-ISM ; tournée de 151 VERSUS sans `HSFA_NOROUL` identique. Patch
  `patches/fbneo/0007-HSFA-roulette-touche-piece.patch` ; cœurs Windows, ROCKNIX, Android, Linux reconstruits avec
  les patchs 1-11, paquet `hsfa-coeurs-2026-10-16b.zip` envoyé (remplace les paquets ROCKNIX et Android du jour).
  **À vérifier sur ROCKNIX** : Select y est aussi la touche de raccourci de RetroArch.
- **Compatibilité** : les cœurs 1-11 lisent tels quels l'ancien zip d'Hyper de l'utilisateur (ADX, 743 Mo, construit
  le 2026-10-11, md5 `56024e1c…`) : EX Balrog, roulette sur Select, Mazi S-ISM (variante B), EX ALPHA, X-ISM avec
  musique de vie basse, tous bons. Le patch 11 ne s'applique qu'à Hyper ; SFA3 et Upper sont inchangés.
- **Cris faux des versions ZERO / ZERO 2 / ALPHA** (signalé par l'utilisateur sur Anbernic RG Arc-D sous ROCKNIX : Ryu
  ALPHA 1 en J2, TRAINING). Pas un défaut ARM (même son qu'au PC) : les cris venaient d'un appariement par
  ressemblance. Mesurés sur les arcades SFA1 / SFA2 / SFA3 (`tools/son-hyper/mesure_cris_arcade.py`,
  `cris_arcade.tsv`), corrigés dans la table du rejeu (`corrige_cris.py`, 404 lignes, sans retraduction), appliqués
  par `paquet_fbneo.py`. Zip Ogg corrigé envoyé à l'utilisateur. Détail : `SON-HYPER-ROM.md` §4.3.
- **Voix « par pas » vérifiées sur l'arcade** (46 versions ALPHA / ALPHA 2 / ALPHA 2 Gold, 35 gestes chacune, état
  sauvé commun, marqueurs dans les tables) : 112 justes, 6 fausses, 12 SFA3 gardées à tort, 1 conflit. Corrigées dans
  le zip (`corrige_voix.py`, 36 mots, sans retraduction), appliquées par `paquet_fbneo.py`, et par
  `gen_redirection.py` pour une retraduction. Détail : `SON-HYPER-ROM.md` §4.3, `tools/son-hyper/mesures_voix/`.
- **Suite des voix** : rôle des cris (`n` 3 = projeté, 5 = garde brisée = son `$08C274`) ; super-coups (4 corrections) ;
  Akuma / Bison / Dan d'ALPHA 1 mesurés en forçant le perso dans SFA1 (Dan crie avec les voix de Ryu) ; versions EX
  sans référence arcade (inchangées). Zip final : 65 mots de tables + 408 lignes de cris ; envoyé à l'utilisateur.
- **SFZ2 Alpha** (`sfz2al.zip` de l'utilisateur, suite au projet SFZ2A-DASH-CPS2) : même son que SFA2 ; versions ALPHA et
  EX d'Hyper conformes, sauf la projection HK d'Akuma EX (retraduction). Voir HANDOFF §161.
- **Guide BradyGames → tableau des coups** (2026-10-18) : 291 pages transcrites, 1 652 lignes (une par coup, flèches
  Unicode), vérifiées contre SuperCombo (90 coquilles du guide corrigées). Outils : `tools/guide-coups/` ; données hors
  dépôt (texte protégé) ; envoyé à l'utilisateur et à la session « HSFA PS2 CPS2 ». Voir HANDOFF §167.
- **Recherche du livre → projet** (2026-10-20) : `docs/rapports/recherche/` (synthèse + 3 fiches : persos cachés et
  modes, révisions et bugs, méthode pour une 1.0). Voir HANDOFF §168.
- **Sondes de la recherche** (2026-10-20) : `docs/rapports/recherche/D-SONDES.md`, `tools/sondes-recherche/`. Test
  CFC2 sur Upper + MAX : Head Press juste, Skull Diver de Bison qui rate Sakura et Ingrid. Voir HANDOFF §169.
