# Plan — les partitions de SFA1 et SFA2 jouées dans Hyper (« carte musique » du cœur FBNeo)

Version du 2026-10-16. Détaille la phase 2 de [PLAN-SON-HYPER](PLAN-SON-HYPER.md) (et la phase 3, *Super SF2*, en
option), en tenant compte des chantiers prévus : Vorbis ([PLAN-VORBIS](PLAN-VORBIS.md)), greffe du mode Arcade d'Upper
(voie B, journal §144-§148), persos de MAX, décors de SFA2.
Légende : **établi** = lu dans le code ou mesuré ; *à vérifier* = point à valider par l'étape indiquée.

## État au 2026-10-16

**Étape 1 faite** (rendu hors ligne, depuis les ROM arcade `sfa.zip` et `sfa2.zip`) :
- `tools/son-hyper/rendu_partitions.py` : le pilote d'origine tourne au banc (`mesure_boucles.Banc`), ses écritures
  QSound sont enregistrées au cycle près, puis rejouées par `tools/son-hyper/rendu_qsound.cpp` avec `hsfa_qsound.h`
  (copie du QSound du cœur) → WAV 24 038 Hz. 240 s de musique en 4 à 6 s.
- **Les 32 morceaux** (13 ZERO, 19 ZERO 2) : aucune saturation, aucun silence, niveaux homogènes (crête 8 600 à
  18 500). Chaque morceau se répète avec une période nette : spectrogrammes de deux passages corrélés à 0,74-0,96,
  contre 0,23-0,68 pour un témoin décalé de 13 s (`tools/son-hyper/rendu_partitions.tsv`).
- **Exception** : SFA1 `07` (code Hyper `0047`) n'a pas de période courte nette, même sur 500 s. Ses pistes bouclent
  probablement chacune de leur côté. Le flux PS2 fait 53,5 s : la version PS2 a sa propre boucle. La carte jouera le
  comportement arcade.
- **Limite trouvée sur le banc** : la boucle de `mesures_z80.tsv` est fausse pour `03`, `04`, `08` (SFA1 et SFA2) et
  SFA2 `11`. `mesure_boucles.py` prend la plus longue des boucles de piste, et pour ces morceaux l'opcode `16` sert
  aussi à autre chose. Période réelle : `03` 55,31 s (banc 57,04), `04` 88,22 s (88,63), `08` 67,25 s (78,20), SFA2
  `11` 71,83 s (72,41). La carte n'en dépend pas : elle fait tourner le vrai pilote.
- **Écoute** : les 32 morceaux ont été envoyés à l'utilisateur (Ogg, usage personnel, hors dépôt). Reste : comparer à
  l'oreille et à l'empreinte avec les flux PS2, et caler les gains (`rendu_partitions.py --z80 e221 --qs e222` marche
  aussi sur les fichiers de `X_DATA.BIN`).

**Étapes 2 et 3 faites côté code** (2026-10-16, session cloud) :
- **Carte** : `tools/son-hyper/hsfa_musique.h` (C++98, en-tête seul, le Z80 derrière une interface), copiée dans le cœur
  par le patch 10 `0006-HSFA-carte-musique.patch`. Dans le cœur, le Z80 est Zet n° 1 (classe `HsfaMusZet` de
  `cps_hsfa.cpp`), toujours initialisé pour Hyper ; le rendu se fait en fin d'image (`qs.cpp`), l'aiguillage dans
  `HsfaFluxCommande` (carte → flux → Z80 principal). Cœurs Linux et Windows compilés.
- **Paquet** : `paquet_fbneo.py`, `HSFA_PARTITIONS=1` (membres `hsfa_musique.bin` et `hsfa_musique_table.txt`).
- **Bancs** (`tools/son-hyper/tests/lance_tests_carte.sh`, avec `sfa.zip` et `sfa2.zip`) :
  - `test_carte` (Z80 de `z80.h`) : 15 contrôles bons. Démarrage des 2 pilotes en 0,07 s ; un morceau rejoué après un
    autre est identique à l'octet au premier départ ; état rechargé (même carte, carte neuve) identique ; `FF05`
    silence ; fondu à 0 : pause et Z80 gelé, puis reprise au même endroit ; 44,1 kHz. Sortie contre le rendu hors
    ligne de l'étape 1 : spectrogrammes 0,98, niveau −0,2 dB.
  - `test_zet` (Z80 de FBNeo, classe du cœur extraite telle quelle) : 60 s rendues, état rechargé identique ; contre
    `z80.h` : spectrogrammes 0,998-0,9998, niveau 0,00 dB (les deux Z80 ne prennent pas l'IRQ au même cycle : la
    forme d'onde diverge après 1,3 s, pas la musique).
- **Écarts avec le plan** : pas encore d'option du cœur. La carte s'active quand le zip contient ses membres
  (`HSFA_MUSIQUE=0` la coupe sur PC). Gains de la table à 100 % en attendant la comparaison avec les flux. Les flux
  ZERO / ZERO 2 restent dans le zip.
- **Premier essai en jeu** (2026-10-16, zip d'Hyper de l'utilisateur, cœur Linux, VERSUS Ryu ZERO / Ken ZERO piloté par
  `tools/fbneo-hsfa/essais/`) : la carte joue `0042` à la place du flux, applique les fondus, ne change rien au
  déroulement ; même morceau que le flux PS2 (spectrogrammes 0,86-0,93), un peu plus fort (+0,7 à +1,6 dB).
- **Reste** : étape 0 (CRC de `e221` / `e250`) et **étape 4, en jeu, chez l'utilisateur** : un zip d'Hyper avec
  `HSFA_PARTITIONS=1`, des matchs avec des persos en version ZERO et ZERO 2, une écoute, le journal, la RGB10X.

## 0. En bref

- **But** : les musiques ZERO (SFA1, 13 morceaux) et ZERO 2 (SFA2, 19 morceaux) d'Hyper sont jouées par **leurs
  pilotes son d'origine**, sur une puce QSound émulée, comme en arcade. Il n'y a plus d'enregistrement pour elles
  (environ 112 Mo d'ADX, ou 22-25 Mo de Vorbis, en moins dans le zip).
- **Architecture** : une « carte musique » dans le cœur, faite d'un **2ᵉ Z80** qui exécute le pilote d'origine
  (`e221` pour SFA1, `e250` pour SFA2) et d'un **3ᵉ QSound** qui lit les échantillons dans la ROM **déjà présente**
  pour le rejeu des voix (`hsfa_rejeu.bin` = `e222` + `e251`).
- **Rien à convertir, rien à redistribuer** : programmes et échantillons viennent du `X_DATA.BIN` de l'utilisateur
  (établi, SON-HYPER-ROM §1). Ce qui s'ajoute au zip : environ 0,6 Mo (les deux programmes Z80) et une petite table.
- **Aiguillage unique** de la musique, au même endroit que le lecteur de flux (`$61801F = 0`) : partition si elle
  existe, sinon flux (ADX ou Vorbis), sinon QSound du Z80 principal. Les fondus et pauses d'Hyper suivent la logique
  PS2, déjà écrite dans le lecteur de flux.
- **Indépendant des autres chantiers** : la carte voit les commandes envoyées au son, pas le code 68K qui les choisit.
  La greffe d'Upper, MAX et les nouveaux décors n'ont rien à lui demander de spécial (§4).
- **Première étape faisable tout de suite, sans Hyper** : un rendu WAV hors ligne des 32 morceaux par les pilotes
  d'origine, à écouter et à comparer aux flux PS2 (§5, étape 1).

## 1. Ce qui existe (établi)

| élément | état | source |
|---|---|---|
| programmes son SFA1 / SFA2 | `e221` (v1.05A, 0x48000 o) et `e250` (v1.05C, = `sz2.01a/02a`) dans `X_DATA.BIN` | SON-HYPER-ROM §1-§2 |
| échantillons SFA1 / SFA2 | `e222` et `e251`, 4 Mo chacun, **déjà dans le zip d'Hyper** (`hsfa_rejeu.bin`, 8 Mo : SFA1 en banque 0, SFA2 en banque `$40`) | REJEU-FBNEO §1.4 |
| codes musique d'Hyper → codes des pilotes | ZERO `0x41+k` → SFA1 `0x01+k`, `0x4D` → `0x32` ; ZERO 2 `0x51+k` → SFA2 `0x01+k`, `0x63` → `0x35` | PLAN-SON-HYPER §1 |
| pilotes au banc | SFA1 et SFA2 tournent dans un émulateur Z80 : poignée de main (`CFFF`, `CFFD`), commande (`C000-C001`, `C00F`), 8 MHz, IRQ à 250 Hz ; mesures reproduites à l'identique | `tools/son-hyper/mesure_boucles.py`, `mesures_z80.tsv` |
| QSound supplémentaire | `hsfa_qsound.h` : HLE instanciable, ROM fournie par l'hôte (`fixe_rom(pointeur, taille)`, lecture en miroir), horloge 60 MHz, états sauvegardés | REJEU-FBNEO §1.2-§1.3 |
| plusieurs Z80 dans FBNeo | `ZetInit(n)` / `ZetOpen(n)` ; le Z80 principal est le n° 0, cadencé par `BurnTimer` à 250 Hz en mode HSFA | `qs_z.cpp`, `qs.cpp` |
| interception des commandes | `$61801F = 0` : lecteur de flux puis rejeu, avant le Z80 principal ; le Z80 reçoit `FF05` quand la musique est jouée ailleurs | `cps_mem.cpp`, `hsfa_flux.h` |
| fondus PS2 | `FF00/05` arrêt, `FF06/07` fondu en p images vers v/255, `FF0C/0D` fondu à 0 ; niveau 0 = pause | `hsfa_flux.h` |

## 2. Choix d'architecture

| option | pour | contre | décision |
|---|---|---|---|
| **A. carte musique : 2ᵉ Z80 (pilote d'origine) + 3ᵉ QSound** | son exact (tempo, enveloppes, échos, panoramiques) ; aucune conversion ; données déjà chez l'utilisateur | un Z80 et un QSound de plus à émuler | **retenue** |
| B. partitions converties en v1.71 dans le Z80 principal | un seul pilote | impossible en l'état : ni numéros de commande libres, ni entrées libres, ni bit de banque (SON-HYPER-ROM §12.1) ; tempo 16 → 8 bits | écartée |
| C. partager le 2ᵉ QSound (celui du rejeu) | une puce de moins | la musique utilise jusqu'à 16 voies, les voix rejouées les voies 12 et 14 : deux pilotes indépendants écriraient sur les mêmes voies | écartée |
| D. « rejeu » de la musique (écritures QSound enregistrées une fois, rejouées en boucle) | pas de Z80 dans le cœur | fichiers de quelques Mo par jeu ; raccord de boucle non garanti (notes tenues, enveloppes à cheval sur le point de boucle) | repli seulement |

Le 3ᵉ QSound ne coûte pas de mémoire : il lit la même ROM que le rejeu, à partir de `+0` (SFA1) ou de `+4 Mo` (SFA2),
avec une taille de 4 Mo. Le pilote voit ainsi sa propre ROM, sans conversion de banque.

## 3. Fonctionnement

### 3.1 Aiguillage de la musique

Une seule fonction reçoit les commandes musique posées par le 68K et choisit, dans l'ordre :
1. **partition** : le code est dans `hsfa_musique_table.txt`, la carte est active (option du cœur) et le pilote est
   chargé ;
2. **flux** : le code est dans la table des flux et son entrée existe (ADX ou Vorbis) ;
3. **Z80 principal** : la commande passe telle quelle (QSound de la ROM hybride).

Démarrer une partition arrête le flux en cours, et inversement. Dans les cas 1 et 2, le Z80 principal reçoit `FF05`.
Les bruitages et les voix ne passent pas par là : ils vont au rejeu ou au Z80 principal, comme aujourd'hui.

Table, au format texte des autres tables :

```
# code_hyper  pilote  code_pilote  gain_%  drapeaux
0041  sfa1  0001  100  -
...
004D  sfa1  0032  100  -
0051  sfa2  0001  100  -
...
0063  sfa2  0035  100  -
```

### 3.2 Pilotes

- Les images Z80 (`e221`, `e250`) sont lues dans le membre `hsfa_musique.bin` du zip, ou dans `X_DATA.BIN` / l'ISO du
  dossier système, avec contrôle de CRC, comme pour le rejeu.
- **Démarrage une fois pour toutes** au chargement du jeu : chaque pilote fait sa poignée de main et son
  initialisation (au banc, environ 1 s de temps Z80), puis son état est **photographié** (registres et RAM `C000-FFFF`).
- Changer de pilote (un morceau ZERO après un morceau ZERO 2) revient à **restaurer la photo** puis à poster la
  commande : c'est instantané, sans attendre la réinitialisation.
- La carte ne garde qu'un pilote actif à la fois. Un seul Z80 et un seul QSound suffisent donc pour SFA1 et SFA2.

### 3.3 Cadence

- Z80 à 8 MHz, IRQ à 250 Hz, comme le Z80 principal en mode HSFA (`qs.cpp`), en tranches de 32 000 cycles.
- Commandes datées sur l'horloge à 60 MHz du rejeu (cycles 68K de l'image en cours), pour la même précision.
- QSound à 24 038 Hz, rééchantillonné vers la fréquence de sortie et mixé comme le rejeu.

### 3.4 Fondus, arrêt, pause

- La carte reprend **la logique PS2 du lecteur de flux** (`FF00/05/06/07/0C/0D`, rampe à 60 Hz) comme **étage de gain
  en sortie**. On n'a pas besoin de connaître les commandes de fondu des pilotes v1.05.
- Niveau 0 = pause : le Z80 et le QSound de la carte sont **gelés**. La musique reprend exactement où elle était, comme
  le flux PS2.
- `FF00` / `FF05` : la carte envoie au pilote sa commande d'arrêt (*à vérifier*, étape 0), sinon elle coupe sa sortie
  et gèle son Z80.

### 3.5 Niveau sonore

- Gain de base `Cps2Volume / 39`, comme les deux autres QSound.
- Gain par morceau (`gain_%` de la table), calé à l'étape 1 pour que chaque morceau sonne au niveau du flux PS2 qu'il
  remplace : volume de `hsfa_flux_table.txt` et mesure RMS.

### 3.6 États de sauvegarde, run-ahead

- Nouveau bloc d'état `HsfaMusique` : état du 2ᵉ Z80 (`ZetScan`), sa RAM, l'état du 3ᵉ QSound, celui de la carte
  (pilote actif, gain et fondu, gel).
- Tout est déterministe (émulation pure). Le run-ahead et le retour arrière fonctionnent sans précaution particulière.
- *À vérifier* (étape 2) : un état écrit avant l'arrivée de la carte doit rester chargeable. Sinon, le bloc n'est
  enregistré que si la carte est active, et la notice le signale.

### 3.7 Option du cœur

« **ZERO / ZERO 2 music** » : `Arcade scores` (partitions) / `PS2 streams` (flux). Défaut : `PS2 streams` jusqu'à
la validation (étape 4), puis `Arcade scores`. Avec `Arcade scores`, un code sans partition utilisable retombe sur le
flux, puis sur le Z80 principal.

### 3.8 Paquet (`paquet_fbneo.py`)

- Nouveaux membres **stockés** : `hsfa_musique.bin` (`e221` + `e250`, environ 0,6 Mo, CRC contrôlés) et
  `hsfa_musique_table.txt`, extraits du `X_DATA.BIN` / de l'ISO, comme `hsfa_rejeu.bin`.
- Les flux ZERO et ZERO 2 restent dans le zip tant que l'option vaut `PS2 streams` par défaut. Une fois les partitions
  par défaut, ils sont omis comme les flux ZERO 3 (`HSFA_FLUX_ZERO12=1` pour les garder).

## 4. Interaction avec les prochains chantiers

| chantier | effet sur la carte musique | précaution |
|---|---|---|
| **Vorbis** (en cours) | aucun : même interception, même logique de fondus. Les deux gains s'additionnent | valider Vorbis d'abord (gain immédiat le plus gros) ; les flux ZERO / ZERO 2 en Vorbis servent de repli et de référence d'écoute |
| **greffe du mode Arcade d'Upper** (voie B) | aucun : la carte reçoit les codes au niveau du son, quel que soit le code 68K qui les choisit (Hyper ou couche Arcade greffée) | si la greffe déplace la RAM de travail, rien à faire : seule la boîte aux lettres QSound (`$618000`) compte. Si l'Arcade greffée choisit la musique selon la version du perso, les codes ZERO / ZERO 2 seront servis automatiquement |
| **persos de MAX** (Eagle, Maki, Yun, Ingrid) | leurs thèmes n'existent pas sur CPS-2 : pas de partition | ils passeront par le lecteur de flux (Vorbis, tirés de l'ISO PSP de l'utilisateur), avec de nouveaux codes dans la table des flux. La table de la carte n'a pas à les connaître |
| **décors de SFA2 importés** (`DECOR-SFA2.md`) | leur musique est un code ZERO 2 → servie par la carte, sans changement | aucune |
| **rejeu des voix** | inchangé ; QSound distinct, donc aucun conflit de voies | les deux puces lisent la même ROM : aucune copie |
| ***Super SF2*** (jeu A, SHADALOO-D) | même carte, 3ᵉ pilote : `sfx.01/02` (v1.04, table en `$9000`, mesuré) et ses échantillons `sfx.11m/12m` (4 Mo) | ROM **arcade** fournie par l'utilisateur (pas dans `X_DATA`) ; +4 Mo dans le zip pour environ −15 Mo de Vorbis : intérêt surtout pour la fidélité ; étape 5, en option |
| **RGB10X** | un Z80 à 8 MHz et un QSound de plus | mesure dès le prototype (étape 2), en même temps que celle du Vorbis |

## 5. Étapes

| # | étape | où | livrable | validation |
|---|---|---|---|---|
| 0 | relevés : CRC de `e221` / `e250` contre `sfz.01-02` / `sz2.01a-02a` ; commande d'arrêt des pilotes v1.05 ; durée réelle de l'initialisation ; commandes musique et `FFxx` réellement envoyées par Hyper (journal `HSFA_FLUX_LOG` d'un match) | session cloud + journal d'un match chez l'utilisateur | notes dans ce plan | — |
| 1 | **rendu hors ligne** des 32 morceaux : banc Z80 qui enregistre les écritures QSound, rendu par `hsfa_qsound.h` en WAV ; empreinte et niveau contre les flux PS2 (`empreintes.py`), table des gains | **session cloud** (`sfa.zip` et `sfa2.zip` déjà fournis) ; comparaison aux flux chez l'utilisateur | `tools/son-hyper/rendu_partitions.py`, WAV à écouter, `hsfa_musique_table.txt` | écoute ; corrélation d'empreinte comparable à celle de SON-HYPER-ROM (0,84-0,95) ; boucles = `mesures_z80.tsv` |
| 2 | **carte musique dans FBNeo** : 2ᵉ Z80, 3ᵉ QSound, photos des pilotes, aiguillage, étage de fondu, mixage, bloc d'état, option du cœur | session cloud (compilation Linux, Windows, ARM) | patch `0006-HSFA-carte-musique.patch` | compilation 4 plateformes ; non-régression SFA3 arcade (frontal `joue.c`) |
| 3 | paquet : `hsfa_musique.bin` et sa table | session cloud (code), utilisateur (exécution) | `paquet_fbneo.py` | membres présents, CRC |
| 4 | **validation en jeu** : matchs avec des persos en version ZERO et ZERO 2 ; départs, arrêts et fondus aux mêmes images qu'avec les flux ; boucles ; états et run-ahead ; RGB10X | **chez l'utilisateur** (zip d'Hyper) | rapport ; option par défaut à `Arcade scores` ; flux ZERO / ZERO 2 omis du zip | journal identique hors source, écoute, temps par image |
| 5 | *Super SF2* (jeu A), en option | session cloud + `ssf2t.zip` de l'utilisateur | 3ᵉ pilote, table | comme l'étape 4, en SHADALOO-D |

Les étapes 1 et 2 ne dépendent pas de la validation Vorbis. L'étape 4 vient après elle, pour ne tester qu'une
nouveauté à la fois.

## 6. Bilan attendu (zip d'Hyper)

| état | musique dans le zip | zip (estimé) |
|---|---|---|
| aujourd'hui (ADX) | 695 Mo | ≈ 710 Mo |
| Vorbis + flux ZERO 3 omis | ≈ 110-130 Mo | ≈ 155-180 Mo |
| + partitions SFA1 / SFA2 | ≈ 85-105 Mo + 0,6 Mo | ≈ 135-155 Mo |
| + *Super SF2* (option) | ≈ 70-90 Mo + 4,3 Mo | ≈ 125-140 Mo |

## 7. Risques et points ouverts

| risque | parade |
|---|---|
| charge sur la RGB10X (Z80 + QSound en plus) | mesure à l'étape 2 ; au besoin, la carte ne tourne que pendant qu'une partition joue |
| changement de pilote audible (craquement, retard) | photos des pilotes (§3.2) ; essai au banc à l'étape 1 |
| fondus d'Hyper ≠ comportement des pilotes arcade | fondus faits par la carte, avec la logique PS2 (§3.4), et non par le pilote |
| niveau des partitions ≠ flux PS2 | gains par morceau calés à l'étape 1 |
| états de sauvegarde antérieurs | bloc d'état conditionnel si besoin (§3.6) |
| `X_DATA.BIN` d'une autre version | CRC, comme pour le rejeu |
| la musique arcade diffère un peu des enregistrements PS2 (corrélation 0,84-0,95) | c'est l'original arcade ; l'option du cœur laisse le choix |
