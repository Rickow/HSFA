# Plan — musique en Ogg Vorbis dans le cœur FBNeo HSFA

Version du 2026-10-16. Détaille la phase 5 de [PLAN-SON-HYPER](PLAN-SON-HYPER.md) : remplacer les flux ADX par des flux
Ogg Vorbis, environ 5 fois plus petits, sans rien changer au comportement du jeu.
Légende : **établi** = lu dans le code ou mesuré ; *à vérifier* = point à valider par l'étape indiquée.

## État au 2026-10-16

| étape | état |
|---|---|
| 1. encodeur | **fait** : `tools/flux/fluxtool.cpp` (décodage par `hsfa_flux.h`) et `tools/flux/flux_ogg.py` (ffmpeg, commentaires de boucle, contrôle, cache, encodage en parallèle) ; branché dans `paquet_fbneo.py` (`HSFA_FLUX_FORMAT=ogg`) |
| 2. stb_vorbis dans le cœur | **fait** : patch 8 `0004-HSFA-stb_vorbis.patch` ; cœurs Linux et Windows compilés |
| 3. lecture Vorbis | **fait** : patch 9 `0005-HSFA-flux-musique-Ogg-Vorbis.patch` |
| 4. états, run-ahead | **fait** : structure d'état inchangée (124 octets) |
| 5. zip d'essai d'Hyper | **fait dans la session cloud** sur le zip de l'utilisateur (flux ADX du zip reconvertis) : 743 → 174 Mo ; VERSUS piloté : mêmes décisions du lecteur, corrélation 0,955-0,998 contre l'ADX, niveau ≤ +0,2 dB. Seuil du contrôle ramené de 0,99 à 0,90 (la vraie musique va de 0,94 à 0,99) |
| 6. Vorbis par défaut | après l'étape 5 ; décision du 2026-10-16 : tous les flux d'Hyper en Ogg (201 Mo), la phase 1 (flux ZERO 3 omis) devient optionnelle (`HSFA_FLUX_SANS_Q=1`) |
| 7. RGB10X | à mesurer |

Banc `tools/flux/tests/lance_tests.sh` (flux synthétiques fabriqués par ffmpeg, aucune donnée de jeu) : **23
contrôles, tous bons** sur Linux x86_64, Windows (MinGW, sous Wine) et ARM64 Cortex-A35 (sous QEMU) :
- Ogg décodé : même nombre d'échantillons que la source, boucle lue, corrélation 0,9998, niveau +0,04 dB ;
- 40 s de lecture avec deux passages du point de boucle : sortie **identique à l'échantillon près** au décodage
  continu déplié ;
- état rechargé (run-ahead, depuis l'anneau), dans un lecteur neuf (seek) et 8 s en arrière (hors anneau) : sortie
  **identique à l'octet** ; le seek de stb_vorbis est donc déterministe ;
- Ogg sans boucle (arrêt en fin de fichier), entrée vide (repli QSound, flux en cours arrêté), ADX inchangé,
  enchaînement Ogg → ADX → Ogg, fondu `FF07`, sortie à 44,1 kHz ;
- coût : 120 s rendues en 0,20 s, soit 0,17 % d'un cœur Xeon.

Écarts avec le plan ci-dessous : l'état n'a **pas** reçu de nouveaux champs. La source Vorbis réutilise `pos_abs`
(échantillon suivant du fichier) et `boucle_ok` (boucles faites) : les états de sauvegarde gardent leur taille et leur
format. Un état écrit avec un zip ADX puis rechargé avec un zip Vorbis reprend au même endroit. Le tampon fait 2,7 s
(2¹⁷ échantillons).

## 0. En bref

- **Ce qui change** : le format des flux dans `hsfa_flux.bin`, et le décodeur dans `hsfa_flux.h`. **Ce qui ne change
  pas** : la table `hsfa_flux_table.txt`, le conteneur AFS, la logique des commandes (`FF05`, fondus, volume), la DIP
  « PS2 music », le rééchantillonnage, le repli sur le QSound.
- **Décodeur** : stb_vorbis (un seul fichier C, domaine public / MIT), lu en mémoire. **Il n'est pas dans FBNeo** au
  commit `af5d3f3` (établi : seuls dr_mp3 et dr_flac sont dans `src/dep/libs`). Il faut l'ajouter.
- **ADX et Vorbis cohabitent** : le format est reconnu entrée par entrée (`OggS` ou `0x80`). Le mode « `Y_DATA.BIN`
  de l'utilisateur dans `system/fbneo/hsfa/` » reste en ADX, sans changement.
- **Gain attendu pour Hyper** : flux du zip ≈ 580 Mo d'ADX → **≈ 110-130 Mo** de Vorbis (≈ 96 kbit/s). Zip ≈ 710 Mo →
  **≈ 155-180 Mo** ; ≈ 135-155 Mo une fois SFA1 et SFA2 en partitions.
- **Coût processeur** (mesuré, §6) : stb_vorbis décode 120 s de musique en 0,14 s sur un cœur Xeon à 2,1 GHz. Estimé à
  1-1,5 % d'un cœur sur la RGB10X (*à vérifier*, étape 7).

## 1. L'existant (établi)

- `src/burn/drv/capcom/hsfa_flux.h` (390 lignes, en-tête seul, partagé avec le fork MAME) :
  - `ouvre_y()` lit un AFS : `Y_DATA.BIN`, l'ISO, ou `fichier@décalage` (membre `hsfa_flux.bin` **stocké** dans le zip,
    lu sur place) ;
  - `commande()` décide flux ou Z80 pour chaque commande du 68K, applique `FF00/05/06/07/0C/0D` ;
  - `rend()` : rééchantillonnage linéaire du flux vers la fréquence de sortie, gain avec rampe, fondus à 60 Hz ;
  - spécifique à l'ADX : `charge_entete()` (en-tête, boucle), `decode_trame()`, `suivant()` (boucle), lecture
    paresseuse par blocs de 64 Ko (`charge_jusqu`), et la reprise d'état `apres_chargement()` en une trame (coût
    constant, compatible avec le run-ahead).
- `tools/fbneo-hsfa/paquet_fbneo.py` construit `hsfa_flux.bin` : un AFS réduit qui garde **les indices de
  `Y_DATA.BIN`**. Les flux absents ont une taille nulle, donc la table ne change pas.
- **Repli déjà en place** : si une entrée est vide ou illisible, `demarre()` échoue, `commande()` rend `PASSE`, et le
  Z80 joue la musique en QSound. C'est ce qui permettra de retirer les flux ZERO 3 du paquet (phase 1 du plan son).

## 2. Choix techniques

### 2.1 Décodeur : stb_vorbis

- Fichier `src/dep/libs/stb_vorbis/stb_vorbis.c` (version 1.22 ou plus récente : corrections de `seek`), compilé
  avec `STB_VORBIS_NO_STDIO` et `STB_VORBIS_NO_PUSHDATA_API`. Seule l'API mémoire est utilisée : pas de conflit avec le
  `FILE` = `RFILE` de libretro.
- Ajouté à `SOURCES_C` dans `Makefile.hsfa` et `Makefile.hsfaws`. Android (`jni/Android.mk` inclut
  `Makefile.$(SUBSET)`), Linux, ROCKNIX et Windows en profitent sans autre changement (établi).
- Dans `hsfa_flux.h`, le code Vorbis est sous `#ifdef HSFA_FLUX_VORBIS`, défini par les deux Makefiles. Le **fork MAME
  reste en ADX** : il sert de référence pour la validation.

### 2.2 Conteneur et table

- `hsfa_flux.bin` reste un AFS avec les indices de `Y_DATA.BIN`. Chaque entrée contient soit un ADX, soit un fichier
  Ogg Vorbis complet. `charge_entete()` regarde les 4 premiers octets.
- `hsfa_flux_table.txt` ne change pas.
- Le membre reste **stocké** (non compressé) dans le zip : Vorbis ne se compresse pas plus, et le cœur le lit sur
  place.

### 2.3 Boucles

- Points de boucle dans les **commentaires Vorbis** `LOOPSTART` et `LOOPEND`, en échantillons à 48 kHz. C'est la
  convention la plus répandue, et le fichier se suffit à lui-même.
- Valeurs recopiées **exactement** de l'en-tête ADX (`m_bdeb`, `m_bfin`) par l'outil d'encodage. Sans commentaire,
  le flux joue une fois puis s'arrête, comme un ADX sans boucle.
- Arrivé à `LOOPEND`, le lecteur appelle `stb_vorbis_seek(LOOPSTART)`, qui est exact à l'échantillon près. Il n'y a
  pas de trou : stb_vorbis redécode la trame précédente pour le recouvrement MDCT.

### 2.4 Lecture du fichier

- Le fichier Ogg d'un morceau est chargé en mémoire. Le plus long fait environ 2,3 Mo (187 s).
- Remplissage **progressif** : 64 Ko par appel, en avance sur la position du décodeur (`stb_vorbis_get_file_offset`),
  comme `charge_jusqu` aujourd'hui. Aucun à-coup au démarrage d'un morceau, même sur carte SD.
- Avant une boucle ou un `seek`, le fichier est complété (en pratique, il l'est depuis longtemps).

### 2.5 États de sauvegarde, run-ahead, retour arrière

- L'état du flux Vorbis tient en une position : `pos`, l'échantillon absolu suivant, plus le nombre de boucles
  faites. Les champs ADX restent dans `etat_t` et ne servent pas pour une entrée Vorbis.
- **Tampon circulaire des 2 dernières secondes décodées** (48 000 × 2 voies × 2 s × 2 octets = 384 Ko), indexé par
  position absolue. Après le chargement d'un état :
  - si `pos` est dans le tampon : reprise immédiate, sans décodage. C'est le cas du **run-ahead**, qui recharge un état
    à chaque image, et des petits pas du retour arrière ;
  - sinon : `stb_vorbis_seek(pos)`, quelques millisecondes, seulement pour un vrai chargement d'état.
- Nouveaux champs ajoutés **à la fin** de l'état, avec un numéro de version dans `HsfaScan`. Les anciens états
  restent lisibles, si possible (*à vérifier*, étape 4).

### 2.6 Ce qui ne bouge pas

Rééchantillonnage (48 kHz vers la fréquence de sortie), gain et rampe, fondus, pause à niveau nul, `FF05` envoyé au
Z80, DIP, journal `HSFA_FLUX_LOG`, variables `HSFA_*`.

## 3. Encodage : `paquet_fbneo.py`

1. **Décodage ADX exact** : petit outil hôte `tools/flux/adx2wav.cpp` qui inclut `hsfa_flux.h` et utilise **le même
   décodeur que le cœur**. On ajoute une méthode publique `decode_tout(fid, pcm, debut_boucle, fin_boucle)`. Le PCM de
   référence est ainsi identique à ce que le cœur joue aujourd'hui.
2. **Encodage** : `ffmpeg -c:a libvorbis -q:a 2` (≈ 96 kbit/s en stéréo 48 kHz), ou `oggenc -q 2`. Le réglage peut
   être changé : `HSFA_OGG_QUALITE`.
3. **Commentaires** : `LOOPSTART`, `LOOPEND`, `HSFA_ADX_MD5` (empreinte du flux d'origine), `HSFA_ENC`
   (encodeur et réglage).
4. **Cache** : `work/flux_ogg/Y<n>.ogg`, réutilisé si l'empreinte ADX et le réglage n'ont pas changé. Ensuite,
   reconstruire le zip prend quelques secondes.
5. **Contrôle automatique** de chaque fichier : nombre d'échantillons décodés par stb_vorbis = nombre d'échantillons
   ADX ; corrélation avec le PCM ADX supérieure à 0,99 ; niveau moyen à ±0,5 dB.
6. Nouvelle option : `HSFA_FLUX_FORMAT=adx|ogg`. Elle vaut `ogg` par défaut une fois l'étape 6 validée.

Dépendance : ffmpeg ou oggenc **sur le PC qui construit les zips** seulement. Les joueurs n'ont rien à installer.
Temps d'encodage estimé : 3 h 38 min de musique, soit quelques minutes avec libvorbis.

## 4. Étapes

Chaque étape se valide seule, et l'ADX reste fonctionnel tout du long.

| # | étape | livrable | validation |
|---|---|---|---|
| 1 | `adx2wav` et l'encodeur dans `paquet_fbneo.py` (cache, commentaires, contrôle) | `work/flux_ogg/`, journal | §3.5 sur les 217 flux ; durées et boucles identiques |
| 2 | stb_vorbis dans l'arbre FBNeo et les Makefiles | patch `0004-HSFA-stb_vorbis.patch` | les 4 plateformes compilent (Linux, Android, ROCKNIX, Windows) |
| 3 | source Vorbis dans `hsfa_flux.h` : détection, chargement progressif, `suivant()` Vorbis, boucle par `seek` | patch `0005-HSFA-flux-vorbis.patch` | WAV d'un morceau rendu par le cœur contre le PCM ADX : même durée, même boucle, raccord sans clic |
| 4 | états : `pos`, tampon circulaire, version de `HsfaScan` | dans le patch 5 | état pris au milieu d'un morceau puis rechargé : sortie identique à l'octet près ; run-ahead 2 images et retour arrière sans craquement |
| 5 | zip d'essai d'Hyper en Vorbis | `paquet_fbneo.py` | un match complet : départs, arrêts et fondus aux mêmes images qu'en ADX (journal `HSFA_FLUX_LOG` identique) ; enveloppes corrélées à plus de 0,99 |
| 6 | Vorbis par défaut ; phase 1 du plan son (flux ZERO 3 retirés) | notices `LISEZMOI-*` | repli QSound pour ZERO 3 vérifié avec « All tracks » |
| 7 | mesure sur la RGB10X (ROCKNIX) | rapport | temps par image avec et sans flux Vorbis ; pas de son haché |

Banc de test sans écran : le frontal `tools/windows/joue.c`, complété d'une sortie WAV, compilé pour Linux ou
Windows. Il charge un zip, fait tourner N images et écrit le son.

## 5. Risques et parades

| risque | parade |
|---|---|
| durée décodée ≠ durée ADX (granules Vorbis) | contrôle à l'encodage (§3.5) ; en cas d'écart, corriger la boucle depuis la durée réelle |
| `seek` de stb_vorbis inexact (bogue des anciennes versions) | version ≥ 1.22 ; test de chaque boucle à l'échantillon près (étape 3) |
| run-ahead : un `seek` par image | tampon circulaire de 2 s (§2.5) |
| états de sauvegarde plus anciens | champs ajoutés en fin, version dans `HsfaScan` |
| niveau différent après encodage | contrôle à ±0,5 dB ; sinon, correction dans le gain |
| fork MAME sans Vorbis | il garde l'ADX par choix, et sert de référence |
| licence | stb_vorbis est en domaine public / MIT : compatible avec FBNeo |

## 6. Mesure de décodage (2026-10-16)

Extrait de 120 s, stéréo 48 kHz, décodé sur un seul cœur (Xeon 2,1 GHz) :

| format | décodeur | temps CPU |
|---|---|---|
| ADX | ffmpeg | 0,07 s |
| Vorbis 96 kbit/s | **stb_vorbis** | **0,14 s** |
| Vorbis 96 kbit/s | libvorbis | 0,40 s |
| Opus 48 kbit/s | libopus | 0,92 s |

Passer plus tard à Opus ne changerait que la source du §2.1 et l'encodeur du §3.2. Le reste du plan reste valable.
