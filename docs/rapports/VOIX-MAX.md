# Voix des persos MAX dans la ROM son QSound d'Upper (fork `sfa3hx`) ; bruitages communs

Agent `agent_voix_max`, 2026-10-07. J'ai écrit seulement dans `<workspace>/work/agent_voix_max/`.
- La ROM hybride (`agent_son_ro5/hybride/roms_hybride/hx3.*`) est **intacte** : md5 vérifiés à la fin.
- Le dépôt MAX (`sfa3max-psp-widescreen/`) est resté en lecture seule, `rosette_code/commandes_voix_max.s` compris : le
  README de la session MAX ne demande pas explicitement de le remplir. Mon fichier en est le remplaçant direct (mêmes
  134 symboles).
- MAME : `nice -n 19`, NVRAM et config dans ce dossier, jamais `-state`, au plus 2 instances.
- **Mise à jour du 2026-10-10 : renumérotation de toutes les voix (§9).** Cammy ALPHA (Hyper) envoyait des numéros
  donnés à Maki. Seule `hx3.01` (table des commandes) change ; les données Z80 et QSound sont aux mêmes adresses.

## 0. En bref

1. **ROM son avec voix** : `roms_voix/` (format `hx3.*` de l'hybride, 16 Mo), pour `HSFA_SON=<workspace>/work/agent_voix_max/roms_voix`.
   - Elle contient les **134 voix MAX** : Eagle 29, Maki 39, Yun 37, Ingrid 29.
   - Chaque voix a **une commande Z80 côté 1 et la même + `$500` côté 2**, car `$3938` ajoute `$500` côté 2.
   - Les numéros (§2, §9) sont libres dans **SFA3, Upper et Hyper** : Z80, table native PS2 (contenu réel), tables
     de voix 68K de chaque perso et version, cris et K.O., journaux en jeu, prototype `roms_hyper`.
   - Elle utilise **2,48 Mo** de QSound, répartis dans 41 banques de 64 Ko que l'hybride n'utilisait pas.
   - Elle ajoute **8,8 Ko** de données Z80 (entrées, programmes, morceaux, table des commandes). Le code du pilote n'est pas modifié.
2. **`commandes_voix_max.s`** contient un `equ` par échantillon (`CMD_VOIX_xx_Ekk equ $nnnn`). Ce sont les mêmes symboles
   que `rosette_code/commandes_voix_max.s`.
3. **Validation au fork** (injection des commandes au Z80, enregistrement, comparaison avec les WAV PSP) :
   - **134/134** commandes conformes registre par registre, côté 1 et côté 2 ;
   - corrélation de la forme d'onde : médiane **0,979** (min 0,854) ;
   - corrélation de l'enveloppe : médiane **0,999** (min 0,939) ;
   - vitesse exacte : dérive ≤ 0,02 % sur 89 voix mesurables ;
   - niveau égal à celui des voix SFA3/Upper : −30,3 dB contre −30,5 et −29,5.
4. **Non-régression** :
   - les **1 840 commandes** existantes donnent des écritures QSound identiques à celles de la ROM hybride ;
   - sur 255 commandes, le WAV est **identique à l'octet près** ;
   - un tap de lecture sur la ROM QSound n'a vu **aucune lecture** dans les banques des voix MAX.
5. **Bruitages communs** (`appariement_bruitages.tsv`, `sons_communs_max.s`) : 5 sur 8 ont un équivalent arcade
   **sûr**, 2 un équivalent **probable**, et **$06 est douteux**. **$2E n'est pas résolu** : son type de table PSP est
   inconnu.
6. **WAV d'écoute** dans `ecoute/` (§5).

## 1. Comment le Z80 de SFA3/Upper joue une voix

J'ai vérifié chaque point par désassemblage (`agent_son_ro5/hybride/dis/z5.asm`) et par journal des registres QSound.

- **Commande** : entrée `c mod $C00` de la table des commandes (linéaire `$8C06`, 4 octets : pointeur 24 bits BE + 1 octet).
  Le pilote fait le modulo par soustractions (`$050D`). Il n'existe donc que `$C00` numéros.
- **Morceau d'une voix** (SFA3 `0301`, Upper `0A61`) :
  - priorité **`$0A`** (52 voix sur 82 ; `$0B` pour les autres) ;
  - **voie 11** seule ;
  - piste `05 TT 06 FF 07 VV 1F NN 08 II 09 03 B9 17`.
  - Côté 2 (`+$500`) : même piste, même voie.
- **`05 TT` = tempo** (table `$3492`, mot ≈ 3,27·(TT+1)).
  - La note `B9` (0x30 tics) dure **196,6 / tempo(TT) s**. Mesuré : `$14` → 2,88 s, `$CC` → 0,30 s.
  - Capcom règle la durée de la note sur celle de l'échantillon (écart médian 2 ms). La coupure est nette à la fin de la
    note.
- **`07 VV` = volume** (table `$2E92`). Exemple : `$76` → registre `$08E4`.
- **`1F NN`** : table de programmes `NEWPT[NN]` (`$6B10`).
- **`08 II`** : programme (4 octets : n° d'échantillon LE, `$00`, enveloppe `$40`).
- **`09 03 B9`** : octave 3, note 72.
- **Échantillon** : entrée `$4975 + 8n` = banque, début LE, boucle LE, fin LE, paramètre.
  - La **hauteur** vaut `TABLE[48 + 72 − paramètre]` (Z80 `$21BA`, demi-tons ; `$48` → `$0800`).
  - Fréquence de lecture = 24 038,46 Hz × hauteur / `$1000` (QSound : 60 MHz / 2 / 1248). Les voix de SFA3 sont à
    **12 019 Hz** (`$0800`).
- **QSound** :
  - PCM 8 bits signé ;
  - registres de la voie 11 : `$59` début, `$5A` hauteur, `$5B` phase, `$5C` longueur de boucle (= fin − boucle),
    `$5D` fin, `$5E` volume ;
  - la banque de la voie 11 est dans le registre **`$50`** (`$8000 | banque`).
- **Découverte 1 : adresses signées.**
  - Le DSP (LLE MAME, et `qs_c.cpp` de FBNeo, même logique) compare adresse et fin en **16 bits signés**.
  - Un échantillon qui traverse `$7FFF→$8000` est **muet**. C'était le cas de mes premiers essais : 30 voix muettes.
  - Un échantillon peut en revanche passer `$FFFF→$0000` dans la même banque, jusqu'à 64 Ko.
  - Aucun échantillon d'origine ne traverse `$8000`. Le générateur range donc les données en « ordre signé » : `$8000..$FFFF`
    puis `$0000..`. 29 voix utilisent ce passage, vérifié au fork.
- **Découverte 2 : lecture transitoire dans l'ancienne banque.**
  - Le Z80 écrit le début **avant** la banque. Le DSP lit donc quelques octets à (ancienne banque, nouveau début).
  - Exemple vu par tap de lecture : la musique `0006` lit `A7DEFB` alors que l'entrée vise la banque `A5`.
  - Écrire dans les « trous » d'une banque déjà utilisée modifiait donc 5 musiques, d'environ 1 % de RMS. D'où la règle :
    **les voix MAX ne vont que dans des banques entières qu'aucune entrée n'utilise**.

## 2. Numéros attribués (version du 2026-10-10, cf. §9)

**Critères** (`numeros.py` → `numeros_libres.json`) : une paire (`c`, `c + $500`), avec `c < $700`, est libre si `c`
et `c + $500` remplissent **tous** ces points.
1. **Z80 hybride** : l'entrée est vide.
2. **Table native PS2 d'Hyper** (0x1200 entrées, identique ro3/ro5/ro9) : il n'y a rien, ou une entrée **sans contenu
   réel**.
   - Entrée de perso (type ≥ 5) : banque = fichier `T_5af2b0[PERSO[type−5]]`.
   - L'indice `o4` n'a aucun son dans cette banque SCEI (X_DATA e314-e344) : pas de jeu d'échantillons `o4`, et aucune
     zone de programme sur la touche `o4 + 12`.
   - Les codes ADX et ceux des banques communes sont exclus d'office.
3. **Aucun code 68K de SFA3, Upper ou Hyper ne peut l'envoyer.**
   - **Tables « sons par pas »** (`$E6`, entrées `[code, code_alt, 0, 0]`) :
     - balayage de tous les programmes : arcade `sfa3ud` (BE), modules `ro3`/`ro5`/`ro9` (LE) ;
     - plus les 128 tables de version d'Hyper (`0x6AE614`, `catalogue/tables_hyper.json` de l'agent son_hyper_rom),
       dont celles de `$78` et `$7E`.
   - **Cris et K.O.** : `base + 0..6` pour les 40 bases de `0x3D9A90` (dont Cammy ALPHA `$0540`) et pour tout début
     de bloc `$300 + $20k`.
   - **Codes envoyés en jeu** dans les journaux 68K des agents ro5, hybride, hyper_son, flux et son_hyper_rom. Les
     balayages par injection, qui contiennent tous les codes, sont exclus.
   - Chaque code envoyable l'est aussi à ±`$500`.
4. **Pas une commande du prototype `roms_hyper`** (`agent_son_hyper_rom/redirection.txt`), à ±`$500` près.

Il reste **157 paires libres**. J'en garde **144**, sans les pages 00-01, sans le bloc de Cammy ALPHA (`$0540-$055F`)
et sans les entrées PS2 de banque commune. J'attribue les 134 premières dans l'ordre des adresses et dans l'ordre des
persos.

| perso | côté 1 (côté 2 = +`$500`) |
|---|---|
| Eagle (29) | `$0246-$024B`, `$027E-$027F`, `$02A4-$02A9`, `$02B4-$02C0`, `$02FD-$02FE` |
| Maki (39) | `$02FF`, `$0314-$031F`, `$033B-$033F`, `$0354-$035F`, `$0376-$037E` |
| Yun (37) | `$037F`, `$039B-$039F`, `$03B7-$03BF`, `$03D9-$03DF`, `$03F7-$03FF`, `$041E`, `$045B-$045F` |
| Ingrid (29) | `$047B-$047F`, `$051A-$051F`, `$0533-$0536`, `$057E-$057F`, `$05B9-$05BF`, `$05F9-$05FD` |

Restent libres pour la suite : `$05FE`, `$05FF`, `$063C`, `$063F`, `$069F`, `$06DD-$06DF`, `$06F6`, `$06FF`.

Les voix suivent l'ordre des échantillons de `voix.json` (n° croissants). Le détail par voix (commande, échantillon,
adresse, hauteur, tempo, gain) est dans `roms_voix/attribution.json`. La correspondance entre ancien et nouveau numéro
est dans `renumerotation.tsv`.

## 3. Construction (`gen_voix_max.py`, ≈ 4 s, déterministe)

**Z80** :
- entrées d'échantillons 1283-1416 en `$718D-$75BC` (zone fixe libre, à la suite de l'hybride) ;
- 4 tables de programmes en `NEWPT[19-22]` (une par perso, `$75BD-$77D4`) ;
- 134 morceaux de 47 octets (en-tête + piste) en banque 15, région `0x4C600-0x4DE99`, sans chevauchement de banque ;
- 268 entrées de la table des commandes ;
- le script vérifie que toutes ces zones étaient nulles.

**Reste libre dans le Z80** : `$77D5-$7974` et `$797D-$7FFF` (zone fixe), et `0x4DE9A-0x4FFFF` (8,5 Ko en banque 15).

**Piste** : `05 TT 06 FF 07 6A 1F 13+k 08 i 09 03 B9 17`.
- TT : note la plus courte qui dure au moins la voix + 30 ms.
- Volume `$6A` : j'ai pris le niveau médian (échantillon × table de volume) des 82 voix SFA3/Upper. Les voix MAX sont
  normalisées plus fort (RMS 8 bits ≈ 38 contre ≈ 24).

**Échantillons** :
- **Fréquence** : la plus petite fréquence QSound au moins égale à l'original.
  - 22 050 → **22 724 Hz** (`$0F20`, paramètre `$3D`) : 124 voix ;
  - 20 182 → 20 189 Hz ;
  - 16 000 → 15 963 Hz ;
  - 11 025 → 11 362 Hz.
  - Deux voix trop longues pour 64 Ko sont plus basses : Eagle v00 (3,11 s → 20 189 Hz) et Ingrid v21 (3,79 s → 16 996 Hz).
- **Rééchantillonnage** : sinc fenêtré de Kaiser.
- **Normalisation de crête** à 124/127, avec un gain ≤ 4. Le gain réel va de 0,71 à 1,03 : les sources sont déjà fortes.
- Fondu de 2 ms aux deux bouts, puis 16 octets nuls (boucle d'un octet nul, comme les voix d'Upper).

**Place QSound** : 61 banques entières ne sont référencées par aucune entrée de l'hybride. J'ai calculé les entrées
utilisées à partir des programmes résolus des 3 072 commandes, des plages complètes de la table et des deux sentinelles :
- `$7D-$7F` = fin nulle de e389 ;
- 58 banques de e288 (SFA3) que l'hybride n'utilise plus.

Les voix en occupent **41 (2 603 381 o)**. Il reste **20 banques entières (1,3 Mo)**, utilisables avec la même règle.

**Vérification statique** (dans le script) :
- les 2 804 commandes existantes ont un contenu résolu identique ;
- les 268 nouvelles commandes résolvent vers leur échantillon ;
- les octets QSound référencés sont intacts ;
- le code du pilote (`0-$37FF`) est inchangé.

**ROM produite** (`roms_voix/md5.txt`) :

| fichier | md5 | CRC32 |
|---|---|---|
| `hx3.01` | `922642bfeb080212803d2242fb865c49` (v1 : `10bb7de1…`) | `20be6020` |
| `hx3.02` | `10cfead0d45b015098d2a13f75ab0a9f` | `eb0eff93` |
| `hx3.11m` | `8da6a5e4272125bc0a7accada5e249e8` (= hybride) | `806b8a4d` |
| `hx3.12m` | `2920bde5bea33dbca952d49edeb06329` | `7a033ef8` |
| `hx3.13m` | `65c573eb71d7963c7fbe7f22f86b114c` | `64792716` |
| `hx3.14m` | `a29885802c1afe5f61783c56ef65a07a` | `f654a747` |

## 4. Validation au fork (`cps2f sfa3hx`, `HSFA_SON=roms_voix`)

Banc : le programme Upper muet de l'agent ro5 (sans boîte aux lettres) ; `voix.lua` dépose les commandes à
`$618001/3` puis `$61801F=0`, comme le 68K. Il journalise toutes les écritures de registres QSound (temps émulé) et
enregistre la sortie (`start_recording`, 48 kHz).

| contrôle | résultat |
|---|---|
| `analyse_regs.py` : banque, début, fin, boucle, hauteur, durée de la note | **134/134** côté 1 et **134/134** côté 2 ; journaux des deux côtés identiques |
| `compare_voix.py` : forme d'onde, canal gauche, source passée par le même rééchantillonnage | médiane **0,979**, min 0,854 (Maki v08). Le canal droit sort en opposition de phase (traitement QSound, aussi pour Ryu) : min 0,694 |
| enveloppe RMS 10 ms | médiane **0,999**, min 0,939 |
| dérive de vitesse (décalage début/fin) | ≤ 0,02 % pour 89 des 93 voix assez longues. Pour les 4 autres, la mesure s'est accrochée à un faux pic ; leur corrélation globale reste ≥ 0,90 |
| niveau RMS actif | MAX −30,3 dB (−34,9 à −27,4) ; voix d'Upper `0A60-0A7F` −30,5 ; Ryu `0801-080F` −29,5 |
| `nonreg.sh` : 255 commandes (`codes.txt` de l'agent ro5 sans `057E/057F/0A7E/0A7F`, devenues des voix d'Ingrid) | journaux **identiques**, WAV **identiques à l'octet près** |
| `nonreg_tout.sh` : les 1 840 commandes non vides, ROM d'origine contre `roms_voix` | journaux de registres **identiques** ; **0 lecture** dans les banques des voix MAX (témoin positif : 2 103 lectures avec deux voix MAX) |

Commandes :
- `./valide.sh` : injection, contrôles et WAV d'écoute ;
- `./nonreg.sh`, `./nonreg_tout.sh` (≈ 21 min) ;
- `<workspace>/venv/bin/python gen_voix_max.py` (numpy du venv HSFA).

## 5. WAV d'écoute (`ecoute/`, 48 kHz stéréo)

| fichier | contenu |
|---|---|
| `Eagle_qsound.wav`, `Maki_…`, `Yun_…`, `Ingrid_…` | toutes les voix du perso, dans l'ordre des commandes, telles que jouées par le QSound du fork |
| `<perso>_psp_puis_qsound.wav` | pour chaque voix : original PSP, 0,3 s, version QSound (pour comparer) |
| `bruitages_psp_puis_arcade.wav` | pour chaque code commun : son PSP, puis la commande arcade proposée et ses variantes |

`validation_voix.tsv` donne les mesures voix par voix, dans le même ordre.

## 6. Bruitages communs (`communs/`, `appariement_bruitages.tsv`, `sons_communs_max.s`)

**Contenu réel de `se_mid.pac`.** `banque_commune.py` ne lit que les sections 0-40. Le fichier en a 47 :
- 0-1 : 18 instruments ;
- 2-40 : 39 séquences MIDI ;
- 41-42 : **banque A** (104 entrées, dont 28 échantillons) ;
- **43 : table de sons des codes `$00-$3F`** (64 × 16 octets, même format que la table des persos) :
  - mot 0 = `$100` : séquence MIDI n° mot 2 ;
  - mot 0 = 0 : échantillon, mot 2 = banque<<8 | n ;
  - mot 0 = −1 : muet ;
  - mot 0 = 2 : type inconnu ;
- 44-46 : banque B (21 échantillons) et table système (80 entrées ; `$200+n` y désigne les instruments).

`communs/extrait_psp.py` sort les échantillons (`communs/psp/`) et `table43.json`.

**Méthode d'appariement** (`communs/apparie.py`) :
- enregistrement des 172 commandes `$0100-$02FF` non vides du Z80 hybride ;
- pour chaque son PSP :
  - corrélation de la forme d'onde, avec recherche de vitesse 0,8-1,25 ; c'est la preuve qu'il s'agit du même
    échantillon ;
  - bandes spectrales log 24 bandes, avec décalage ;
  - enveloppe.

| code PSP | source PSP | commande arcade | forme d'onde | spectre + env. | variante (même échantillon) | confiance |
|---|---|---|---|---|---|---|
| `$06` | séquence MIDI 5 (programme 5, note 60 ; rendue avec l'instrument I_005) | `$0206` | 0,36 | 0,83 | `$0207` (même piste à 2 voies, autre volume) | **faible** (rendu MIDI approché) |
| `$20` | A_000 | `$0239` | 0,73 | 0,62 | (`$023A` 0,62 : autre échantillon) | forte |
| `$22` | A_002 | `$0257` | **0,98** | 0,92 | `$0230` (priorité `$04` au lieu de `$10`) | forte |
| `$27` | A_006 | `$0263` | 0,54 | 0,45 | `$0238` (autre tempo, volume `$7F`) | moyenne |
| `$2B` | A_008 | `$023E` | 0,74 | 0,74 | `$023D` (voie 13 seule, sans le petit retard) | forte |
| `$2E` | type 2, mot 2 = 0 | — | | | | **sans équivalent** : type inconnu, à éclaircir côté PSP (`0x60BC`) |
| `$30` | A_011 | `$022E` | 0,79 | 0,81 | (`$020C` : même échantillon, autre enveloppe, 0,46) | forte |
| `$36` | A_016 | `$023B` | 0,52 | **0,93** | `$023C` (+ une 2e voie) | moyenne (spectre sûr). ⚠ `$023B` joue sur la **voie 11** : il coupe une voix en cours, comme en arcade |

Toutes ces commandes existent aussi côté 2 (`$07xx`), car `$3938` ajoute `$500`.

## 7. Limites, points ouverts

**Côté MAX, rien de fait** :
- recopier `commandes_voix_max.s` dans `rosette_code/` ;
- remplir `SONS_COMMUNS` (valeurs dans `sons_communs_max.s`, à confirmer à l'écoute) ;
- les entrées « autre banque » des tables de voix (ex. Eagle n° 22 : type `$400`, n° 284 ; n° 23 : type `$402`) restent
  à apparier.

**Branchement** :
- les voix ne sonnent qu'avec `HSFA_SON=…/agent_voix_max/roms_voix`. Avec la ROM hybride, les 268 commandes sont vides,
  donc muettes et sans risque ;
- `fbneo/paquet_fbneo.py` pointe toujours vers `agent_son_ro5/hybride/roms_hybride`, et je n'y ai pas touché. Pour
  embarquer les voix, il faut changer `son=` vers `agent_voix_max/roms_voix`.
- Le QSound de FBNeo (`qs_c.cpp`) a la même arithmétique signée que le DSP, donc le passage `$FFFF→$0000` y vaut aussi.
  Ce n'est pas testé sous FBNeo.

**Numéros** :
- les critères du §2 ne garantissent rien pour un futur code 68K qui enverrait un numéro sans son aujourd'hui ;
- un nouvel ajout aux tables de voix (MAX, Hyper) doit repasser par `numeros.py` ;
- le balayage des tables est prudent : il exclut aussi des données qui leur ressemblent seulement (§9).

**Lecture transitoire** (§1, découverte 2) : quand une voix MAX succède à un autre son sur la voie 11, ou l'inverse,
le DSP lit quelques octets à (ancienne banque, nouveau début). C'est le comportement d'origine du pilote, inchangé et
inaudible en pratique.

**Qualité** :
- 8 bits à ≈ 22,7 kHz, bien au-dessus des 12 kHz des voix de SFA3 ;
- la durée de note se règle par pas de tempo, avec une marge d'au moins 30 ms après la fin de la voix ;
- la priorité `$0A` est celle des voix de SFA3 : une voix de priorité ≥ `$0A` remplace la voix en cours ;
- l'écoute de l'utilisateur reste à faire, en particulier sur Maki, dont les corrélations sont les plus basses (≈ 0,86).

**Bruitages** :
- `$06` est mal rendu (séquence MIDI approchée par un seul instrument) ;
- `$2E` est inconnu ;
- pour `$27`, `$36`, `$22` et `$2B`, choisir entre la commande et sa variante à l'écoute.

## 8. Fichiers

| fichier | rôle |
|---|---|
| `gen_voix_max.py` | générateur (ROM hybride → `roms_voix/` + `commandes_voix_max.s` + `attribution.json`) avec vérification statique |
| `roms_voix/` | `hx3.*`, `z80_voix.bin` (image `audiocpu`), `md5.txt`, `attribution.json` |
| `commandes_voix_max.s` | 134 `equ` (remplaçant de `rosette_code/commandes_voix_max.s`) |
| `numeros.py`, `numeros_libres.json` | recherche des paires de commandes libres dans les trois jeux, avec le motif de chaque exclusion |
| `renumerotation.tsv`, `archive_v1/` | ancien → nouveau numéro ; ROM, `.s` et mesures de la version du 2026-10-07 |
| `sons_communs_max.s`, `appariement_bruitages.tsv` | bruitages communs : proposition et détail (6 meilleurs candidats par code) |
| `voix.lua`, `lectures.lua`, `lance.sh` | injection de commandes (journal QSound, WAV) ; tap de lecture sur la ROM QSound |
| `valide.sh`, `analyse_regs.py`, `compare_voix.py`, `validation_voix.tsv` | validation des voix |
| `nonreg.sh`, `nonreg_tout.sh` | non-régression contre la ROM hybride |
| `communs/extrait_psp.py`, `communs/apparie.py`, `communs/ecoute.py` | extraction de se_mid.pac (banques A/B, table 43), appariement, écoute |
| `communs/arcade_0100_02ff.wav/.txt` | enregistrement des 172 commandes arcade (base de l'appariement) |
| `journaux/` | journaux d'injection (`cote1/2`, `regr_*`, `tout_*`), `cote1.wav` |
| `rp/`, `nvram/`, `cfg/` | rompath (liens vers le programme muet de l'agent ro5), NVRAM et config de MAME |

`journaux/cote1.wav` (34 Mo) et `communs/arcade_0100_02ff.wav` (53 Mo) sont supprimables : `valide.sh` et un nouvel
enregistrement les recréent.

## 9. Renumérotation (2026-10-10)

**Cause.** L'agent son_hyper_rom a trouvé le conflit (`SON-HYPER-ROM.md` §4.3).
- Dans Hyper, **Cammy ALPHA (`$7E`)** a sa propre table de voix. Elle envoie `0546`, `0548-054D`, `054F-0551`,
  `0553-0556`, `055D`, `055E`, plus les cris `0540-0546`.
- Avec la v1, ces numéros jouaient les voix de Maki (`0549-055F`).
- Mes journaux de jeu ne passaient jamais par Cammy ALPHA. Le critère « remplissage PS2 » de la v1 ne testait pas le
  contenu réel des banques SCEI.

**Revérification de toutes les voix v1** avec les critères du §2 : **69 voix sur 134** étaient en conflit.

| perso | voix en conflit | motif |
|---|---|---|
| Eagle | 10 (`02AA-02B3`) | motif de table dans ro3/ro5 (sans doute d'autres données ; exclu par prudence) |
| Maki | 22 | table de Cammy ALPHA (`0x6AE614` / ro9), cris `0540+`, journaux d'Hyper (flux), `roms_hyper` (`054E`) ; `0312-0313` : la banque de Ryu (e314) a un son pour ces indices |
| Yun | 12 | `0537-053F` = commandes de `roms_hyper` ; `0352-0353` : contenu PS2 |
| Ingrid | 25 | `05E0-05E6` : cris (base `05E0`) et contenu PS2 (copie de Ryu) ; `05E6-05F6` : `roms_hyper` (`00E6-00F6` + `$500`) ; `05EF-05F8` : motif de table ro3/ro5 |

Par motif (une voix peut en cumuler plusieurs) : contenu PS2 43, `roms_hyper` 28, motif de table ro3/ro5 16, tables
d'Hyper 14, cris 7, journaux 3.

**Choix.** Toutes les voix sont renumérotées d'un seul tenant, dans l'ordre des adresses (§2). Les symboles ne changent
pas, donc la session MAX n'a qu'à remplacer le fichier `.s`.

**Ce qui change dans la ROM** : seule la **table des commandes** du Z80, en `hx3.01`.
- Entrées d'échantillons, programmes, morceaux et données QSound restent aux **mêmes adresses** ; `hx3.02` et
  `hx3.11m`-`hx3.14m` sont identiques à la v1.
- 1 090 octets diffèrent dans `z80_voix.bin`, tous dans la table `0x10C06-0x13C06`.
- Le prototype `roms_hyper`, construit sur la v1, peut donc garder ses ajouts. Il doit cependant repartir de la
  nouvelle `hx3.01` : il faut vider les anciennes entrées de voix MAX et ajouter les nouvelles.

**Anciennes commandes** : toutes redeviennent vides, comme dans la ROM hybride. La vérification statique compare les
2 804 commandes hors voix MAX à l'hybride. Cammy ALPHA retombe donc dans le cas de la ROM hybride : muette au QSound
tant que ses voix e344 ne sont pas importées.

**Validation de la v2** (même banc) :
- `analyse_regs.py` : 134/134 commandes conformes côté 1 et côté 2 ;
- `compare_voix.py` : forme d'onde médiane 0,979 (min 0,854), enveloppe médiane 0,999 (min 0,939). Ce sont les mêmes
  mesures qu'en v1, puisque les données n'ont pas bougé ; les WAV de `ecoute/` sont régénérés ;
- `nonreg.sh` : 255 commandes, journaux **identiques**, WAV **identiques à l'octet près**, 0 lecture dans les banques
  des voix MAX.
  - Le premier passage, sur les 259 codes de `codes.txt`, différait seulement sur `057E/057F/0A7E/0A7F`. Ces codes
    étaient vides dans l'hybride et sont devenus des voix d'Ingrid : c'est attendu.
- `nonreg_tout.sh` : 1 840 commandes, journaux de registres **identiques** à l'hybride, **0 lecture** dans les
  banques des voix MAX.

**md5 v2** (`roms_voix/md5.txt`) : `hx3.01` `922642bfeb080212803d2242fb865c49`, `z80_voix.bin`
`9a87545a77c46ed9b23e35353548909a`. Les autres fichiers sont inchangés (§3).
