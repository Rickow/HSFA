# Ticket public n° 1 : « No Parry sound effect in B-ISM » (Hyper, Mazi S-ISM)

Agent `hyper_parade`, 11/11/2026. J'ai écrit uniquement dans `work/hyper_parade/`. Rien n'a été commité, poussé ni publié.
- PCSX2 : ma propre instance (Xvfb :86, copie de configuration `ps2/cfg`, PINE sur ma socket). Écritures PINE limitées à
  la vie de l'adversaire (pour finir un match). Instance et Xvfb arrêtés par PID.
- Cœur : celui du 10/11 (`livraison_coeurs_2026-11-10`, Linux, md5 ef13c96a). Lancé par `lance_emu`
  (`HSFA_AGENT=parade`, 2 places au plus), en `nice -n 19`. MAME n'a pas servi.

## 0. En bref

1. **Le défaut est reproduit** (cœur du 10/11, `sfa3hhsfa.zip` du script du 08/11, e2c8f6fd).
   - Ken en ZERO 3, Mazi S-ISM (`$123=02`), contre Ryu. Ryu lance un Hadoken, Ken tape → au bon moment.
   - Résultat : parade, sans aucun dégât.
   - Le 68K envoie **0327** (voix de Ken) et **077C**. 077C ne produit **aucun son**.
   - Sans la table du rejeu comme avec elle, le résultat est le même : le rejeu ne touche pas les codes < $2000.
2. **L'oracle PS2 confirme les mêmes commandes.**
   - PCSX2, Ryu en Mazi S-ISM contre Ken : 2 parades réussies, qui envoient **0307 + 077C**. Les commandes sont donc
     identiques : la traduction n'est pas en cause.
   - J'ai sauvé un état 40 ms après 077C. Une nouvelle voix SPU2 y joue **e345 VAG 92** (l'échantillon du Sset 123),
     avec un pitch de `$03E3`, soit **11 660 Hz au lieu de 23 329 Hz : une octave plus bas**.
   - L'enregistrement le confirme : une fois la musique (Y10) retirée, ce VAG à l'octave basse corrèle à 0,69 aux deux
     parades. À la vitesse d'origine, la corrélation tombe à 0,06.
   - C'est le « son à la 3rd Strike » du ticket. À l'écoute : `donnees/e345_vag92_octave_basse_ps2.wav`.
3. **Cause : un son propre au portage PS2, absent du QSound.**
   - 027C et 077C sont vides dans tous les Z80 : SFA3, Upper et l'hybride. Le Z80 n'a des commandes que jusqu'à 077B, qui
     ne joue d'ailleurs qu'un silence.
   - Ce n'est ni un flux ADX ni un flux Ogg.
   - Côté PS2, le pilote natif lit la table 0x5CB300 (type 3, o4 = 124). o4 est l'indice de la table SE du conteneur
     MOMO (§8.1). L'indice 124 mène au Sset 123, donc au VAG 92, que la SPU2 joue une octave plus bas (mesuré).
4. **Correctif (outil de construction ; ni le traducteur ni le cœur ne changent)** : `outils/sons_ps2.py`, qui a pris la
   suite de `son_parade.py` (§8).
   - Il ajoute à une COPIE de la ROM son hybride **21 sons propres au portage PS2**, chacun sur ses deux côtés, soit 42
     commandes. Les échantillons viennent du X_DATA de l'utilisateur :
     - la parade ;
     - l'activation du custom combo (ZERO 2 / ALPHA) ;
     - 0245 ;
     - Birdie ×2 ;
     - Sagat en Saikyo S-ISM ;
     - Cammy ALPHA ×14 ;
     - Dee Jay.
   - Hauteur mesurée sur PS2 ; niveau calibré à ±0,4 dB (027D à −1 dB, au plafond du volume).
   - Interrupteur `HSFA_SONS_PS2=0` : la ROM est recopiée identique à l'octet.
   - Versement : `a_verser/` (Hyper et Hyper + Arcade).
5. **Non-régression** (§9) :
   - vérification statique : les 3 030 autres commandes du Z80 donnent un contenu identique ;
   - balayage d'Hyper (418 essais) : journaux identiques, WAV identiques sauf après une commande ajoutée ;
   - mêmes constats pour Hyper + Arcade, en VERSUS comme en ARCADE.

## 1. Reproduction au cœur

- Outils :
  - `outils/joue_hp` : copie de `tools/fbneo-hsfa/essais/joue_linux.c` + `tournee.h`, avec deux ajouts.
    - `HP_MJ` journalise la file des commandes son du 68K. C'est un anneau de 256 entrées de 16 o en `$FFDE80`, indice
      d'écriture en `$FFEE80`. **Attention** : le journal `MJ` de `musique_ha` ne lisait que 16 entrées et rate tout
      après la 16e.
    - `HP_VIE_LIBRE` : la tournée ne force plus la vie de J1.
  - `outils/lance.sh` lance les essais.
- Gestes : `essais/gestes_hado.txt`, à partir de l'image 1500, état sauvé. Ryu lance ↓↘→ + LP ; Ken tape → pendant
  2 images, à t = 8, 10, …, 70.
- Résultat (`essais/hado1/mj.txt`) :
  - à t = 30-34 : **parade**, `0327` + `077C`, vie de Ken 144 ;
  - ailleurs : coup reçu, `0241` + `0321/0322` + `0703`, vie 135.
- Parade de J2 (Ken Mazi S-ISM contre Ryu, `essais/hado_j2_pv2`) : `0827` + **027C**. Le côté de la commande suit
  donc le joueur.
- **Rendu isolé** : je pose une commande dans la file (`HSFA_POKE`, image 1600) et je soustrais une exécution témoin,
  déterministe. Résultat (`donnees/coeur_*.wav`) :
  - 0327 / 0307 : voix d'arcade de 0,2 s ;
  - 077C : **rien**, son identique au témoin.
- Contrôle de la ROM avec `outils/z80cmd.py` : 077C, 077D et 027C sont vides dans l'hybride (`hx3.01` 3ddd95ab). Avec
  `z80son.charge`, ils sont vides aussi dans les Z80 de SFA3 (ro3) et d'Upper (ro5). 077B ne contient que `05 FA 40 17`.

## 2. Oracle PS2

- Mise en place : `ps2/` (copie des outils de `musique_ha/ps2`, Xvfb :86), avec :
  - `nav.py` : titre → VERSUS ;
  - `sel.py` : `3:5:X` donne la Mazi S-ISM ;
  - `parade.py` : J2 lance des Hadokens et J1 tape →. L'espion de la file tourne dans le même client PINE, car le
    serveur PINE ne sert qu'un client à la fois.
- Journal `ps2/parade1_q.txt` : les deux parades donnent `03 07 …` + `07 7c …`, les coups donnent `02 41` / `03 0x` /
  `07 03`, comme au cœur.
- Audio : capture PCSX2 `ps2/audio/ps2_parade_ryu_mazi_s_ism.{mkv,wav}`. La musique Y10 est retirée par
  `outils/residu.py` → `tmp/residu.wav`. Parades à 54,58 s et 61,64 s de la capture.
- État `ps2/etats/hyper_parade_077C.p2s`, pris par F1 dès que l'espion voit 7C (`parade2.py`). Dans `SPU2.bin` :
  - la RAM SPU est au décalage 0x10004 du fichier ;
  - les voix sont à partir de 0x210004 + 0x00, par pas de 0xA0, avec StartA en +0x44 et pitch en +0x3C (mots de
    16 bits).
- Nouvelles voix de l'état :
  - e345 VAG 47 (Hadoken, 0750, pitch `$0759` = natif 22 050 Hz) ;
  - e314 VAG 15 (0307, la voix de Ryu) ;
  - **e345 VAG 92, pitch `$03E3`**.
- Niveaux, en gain par moindres carrés contre le PCM décodé (`outils/gain2.py`) :
  - parade : 0,231 ;
  - coup (VAG 2 de 0703) : 0,22 ;
  - rapport ≈ 1,05.
- Parade de J2 (027C), faite ensuite (`ps2/parade3.py`, état `ps2/etats/hyper_parade_027C.p2s`) :
  - six parades, chacune `0827` + `027C` ;
  - voix SPU2 neuve : e345 VAG 92, pitch `$03E3` (`outils/voix_spu2.py`) ;
  - audio (`ps2/audio/ps2_parade_j2_027C.wav`) : VAG 92 à 11 660 Hz détecté six fois (0,51-0,61), aucune fois à
    23 329 Hz.
  - 027C = 077C : le correctif vaut pour les deux côtés.

## 3. Mécanisme PS2 (lecture du code)

- Module ro9, pilote 0x5AA0E0 :
  - pour les types 3/4, il appelle 0x5A9FA0 (vide), puis l'ELF 0x155C60(0xB67BD0, banque, o4, o5, o6) ;
  - 0x155C60 calcule le volume, puis appelle 0x152120.
- 0x152120 lit la table SE en EE 0x1A1400 + banque × 0x208, entrée 8 + 4 × o4 : [actif, volume ou $80, note, suivant].
  Il envoie ensuite à l'IOP (0x147570) le mot banque << 16 | o4 << 8 | note.
- Dans `tmp/eeMemory.bin`, l'entrée 124 de la banque 0 est active (`01000000`).
- L'IOP résout ensuite l'indice par la table SE du conteneur MOMO (§8.1) : pour e345, 124 → Sset 123 → VAG 92.
  L'octave basse est mesurée ; son origine (code IOP) n'a pas été lue.

## 4. Premier correctif : `outils/son_parade.py` (parade seule ; remplacé par `sons_ps2.py`, §8)

- Source : e345 du X_DATA de l'utilisateur. Le script vérifie la taille (928 000), la présence de 93 VAG et le taux de
  23 329 Hz.
  - Décodage PS-ADPCM du VAG 92 : 7 952 échantillons, md5 du PCM 735879f6.
  - Lecture à 11 660 Hz, comme la SPU2.
- Conversion, selon les règles des voix MAX (`gen_voix_max.py`) :
  - rééchantillonnage sinc Kaiser vers 12 019 Hz (hauteur QSound `$0800`, paramètre 72) ;
  - 8 bits signés, crête 124, fondus de 2 ms, 16 o nuls à la fin ;
  - au total 8 212 o, 0,682 s.
- Placement :
  - QSound : banque `$FF`, octets `$FF0000-$FF2013`. Cette banque n'est référencée ni par l'hybride, selon la règle
    prudente de `gen_voix_max`, ni par les voix MAX, qui occupent 7D-D5.
    - **Note** : les banques D6, E0, E5 et E9, notées « libres » dans `re/allocations.tsv`, SONT référencées selon
      cette règle. J'ai d'abord pris E9 et l'assertion l'a refusée.
  - Z80 :
    - entrée d'échantillon 1535 (`$796D`) ;
    - table de programmes d'un mot en `$7FF8`, référencée par NEWPT[23] (`$6B3E`) ;
    - deux morceaux en région 0x4FF80-0x4FFDD : priorité $10, pistes 13 (027C) et 15 (077C), comme 027B / 077B ;
      piste `05 54 06 FF 07 75 1F 17 08 00 09 03 B9 17` ;
    - entrées 027C et 077C de la table des commandes.
- Volume `07 75`, calibré au cœur : le rapport parade / coup (0703) vaut 1,05, comme sur PS2.
  - Gain mesuré : 0,1218 pour une cible de 0,1223.
  - Spectres cœur / PS2 (tiers d'octave) : corrélation 0,82 contre la source ; enveloppes identiques.
- Vérifications intégrées :
  - les 3 070 commandes anciennes donnent le même contenu ;
  - les zones QSound référencées sont intactes ;
  - le code du pilote (< $3800) n'est pas modifié ;
  - le résultat est déterministe (deux exécutions donnent les mêmes md5) ;
  - `HSFA_PARADE=0` donne une ROM identique à l'octet.
- Empreintes (base = hybride 3ddd95ab / c7e3d5a6, comme le zip du 08/11 et la construction v160) :
  - `hx3.01` 77125fd4
  - `hx3.02` bde554e7
  - `hx3.14m` 55358b43
  - `hx3.11m`, `hx3.12m`, `hx3.13m` inchangées
  - ROM : `roms/parade_v2/` ; zip d'essai : `zips/parade_v2/sfa3hhsfa.zip` (zip du 08/11 + 3 membres).
- Au cœur, avec ce zip :
  - parade de Ken → 0,682 s de son (`donnees/coeur_pv2_077C.wav`) ;
  - même son pour 027C.
- Mes ajouts à l'index (`re_ajouts/`) : 7 lignes d'allocation, 3 lignes `ro9`.

## 5. Versement (`a_verser/`, rien d'appliqué)

- `depot.diff` (523 lignes) : il s'applique sur le HEAD actuel (57c2e41), vérifié sur un clone du scratchpad. Les trois
  fichiers modifiés sont identiques depuis c53d7a2.
  - `tools/son-hyper/sons_ps2.py` (nouveau) ;
  - `scripts/construction/hsfa_build.py` :
    - étape `sons_ps2` (après `son_upper`), qui écrit `agent_son_ro5/hybride/roms_hyper` ;
    - `paquet_hyper` et `paquet_hyperarcade` en dépendent ;
    - `env_paquet` passe `HSFA_SON_HYPER` ;
  - `tools/fbneo-hsfa/paquet_fbneo.py` et `tools/greffe-arcade/construction/ro9a41/paquet/paquet_fbneo.py` : pour
    `hyper` (et `ro9a`), le dossier son vient de `HSFA_SON_HYPER`.
- Simulation de l'étape (même appel, X_DATA de l'ISO et manifeste du cache de la construction v160) : mêmes md5 que
  `roms/sons_v4` (`hx3.01` 349593e9, `hx3.02` d3affb3c, `hx3.14m` 3aaf2675). Avec `HSFA_SONS_PS2=0`, la ROM sort
  identique à l'hybride.
- Upper ne change pas. Il garde la ROM hybride ; or Dee Jay y envoie aussi 057D, muet : à voir à part.
- Aucune version v161 du traducteur n'est nécessaire, et le cœur ne change pas.

## 6. (voir §8 : inventaire complet)

## 8. Reprise : tous les sons propres au portage PS2 (`outils/sons_ps2.py`)

### 8.1 Comment le pilote PS2 choisit l'échantillon (découverte)
- Le conteneur MOMO d'une banque e3xx a **4 parties** : HD, BD, un bloc « RDSTqesT » (0x490) et une **table SE**
  (0x300 ou 0x800 octets, 16 octets par indice : [0] actif, [5] volume, [8] programme, [9] touche − 12).
- L'octet o4 de la table native (0x5CB300) est un **indice de cette table SE**, pas un n° de Sset. Le programme et la
  touche donnent la zone, donc le Sset, le Smpl et le VAG (`outils/se_table.py`).
  - e345 : presque l'identité. L'indice 124 (parade) mène au Sset 123 (VAG 92). L'indice 123 (077B) a un volume nul :
    077B est muet aussi sur PS2, ce qui explique le silence de 077B dans le Z80.
  - e314 : l'indice 7 (0307) mène au Sset 15. C'est la voix entendue à la parade de Ryu (VAG 15, mesurée).
  - e344 (Cammy ALPHA) : l'indice i mène au Sset i − 5. Mesuré sur PS2 : 0549 → VAG 4, 054A → VAG 5, 0553 → VAG 14
    (état `ps2/etats/hyper_cammy_054A.p2s`, capture `ps2/audio/ps2_cammy_alpha.wav`).
- Mon premier inventaire supposait o4 = Sset. Il est refait avec cette table (`inventaire_ps2_se.json`) : 104
  commandes sont vides dans le Z80 et jouent un vrai son sur PS2.

### 8.2 Ce que le jeu envoie réellement
- Émission statique par immédiat (`outils/codes_emis.py`) : seulement 0245 (`$8C0FA`) et 027D (`$8C26A`). La routine
  `$8C38A` ajoute $500 pour le côté 2.
- Balayage en jeu (`outils/balayage.sh`, `HP_VARIE`), 418 essais (`tmp/bilan_bal.txt`) :
  - jeu varié : normaux, sauts, quarts de cercle, DP, doubles, charge, PPP/KKK, provocation, LP+LK, HP+HK ;
  - jauge pleine ;
  - 38 persos × (Z3, X, V, Z, Z2, A, CLASSIC, 4 S-ISM).
- Résultat, croisé avec l'inventaire corrigé :

| commande | quand | banque, indice → échantillon | indice d'émission |
|---|---|---|---|
| 027C / 077C | parade, Mazi S-ISM | e345, 124 → VAG 92 (octave basse) | jeu (§1), PS2 mesuré (§2) |
| 027D / 077D | activation du custom combo, ZERO 2 / ALPHA (2P+1K ou 2K+1P, après 024F) | e345, 77 → VAG 89 | jeu, immédiat, PS2 mesuré |
| 0245 / 0745 | après une poussée de l'adversaire (`$7C038`) | e345, 69 → VAG 87 | immédiat (entrée non trouvée en jeu) |
| 041F / 091F | Birdie, versions ZERO / ZERO 2 / ALPHA | e322, 31 → Sset 26 | jeu, table |
| 040F / 090F | Birdie | e322, 15 → Sset 27 | table « par pas » seulement |
| 047A / 097A | Sagat, Saikyo S-ISM | e325, 26 → Sset 26 (44,1 kHz, ramené à 24 kHz : limite du QSound) | jeu, table |
| 0549-054C, 0553 / 0A4x | Cammy ALPHA (`$7E`) | e344, i → Sset i − 5 | jeu, table, PS2 mesuré |
| 054D, 054F-0551, 0554-0556, 055D, 055E / 0A4x-0A5x | Cammy ALPHA | e344 | table « par pas » |
| 057D / 0A7D | Dee Jay, toutes versions | e342, 29 → Sset 28 | jeu, table |

- Exclus :
  - 0410-0413 (Birdie) : indices SE inactifs, muets aussi sur PS2 ;
  - 0557 et les autres codes de la table : pas d'indice d'émission.

### 8.3 Hauteur et niveau
- Hauteur : le taux natif, mesuré pour e345 VAG 2, 47, 89, 90 et 91, e314 / e315, et e344 VAG 4, 5 et 14 (pitch
  `$0800` = 24 kHz). Seule exception : le VAG 92 de la parade, lu une octave plus bas (pitch `$03E3`).
- 027D sur PS2 (état `ps2/etats/hyper_027D.p2s`, Ryu ZERO 2) : `024F` puis `027D`, voix neuve **VAG 89, pitch
  `$0759`**. Niveau PS2 VAG 89 / VAG 91 = 1,106 ; rapport des o5 de la table : 127 / 112 = 1,13.
- Règle : sur PS2, le niveau rapporté au PCM est proportionnel à o5, l'octet 5 de la table native.
- Au cœur, j'ai fait un rendu isolé de chaque commande (pose dans la file + soustraction d'un témoin, `outils/rendus.sh`) :
  - référence K = niveau / o5 des sons d'arcade 024F et 0703 (0,00108 et 0,00132 ; moyenne 0,0012) ;
  - `outils/calibre.py` choisit l'op 07 qui donne K × o5 pour chaque son (`VOLUMES`) ;
  - tous les sons sont à ±0,4 dB de la cible, sauf 027D (−1 dB, au plafond `$7F`) ;
  - la parade garde l'étalonnage du §4.

### 8.4 Vérification sur PS2 de chaque son (états SPU2 pris à la commande, `outils/voix_spu2.py`)

| commande | situation | voix SPU2 neuve | état |
|---|---|---|---|
| 077C / 027C | parade de J1 / de J2 | e345 VAG 92, `$03E3` (octave basse) | `hyper_parade_077C`, `hyper_parade_027C` |
| 027D | custom combo, Ryu ZERO 2 | e345 VAG 89, natif | `hyper_027D` |
| 054A (0549, 0553 dans l'audio) | Cammy ALPHA | e344 VAG 5 (4, 14), natif 24 kHz | `hyper_cammy_054A` |
| 057D | Dee Jay, provocation (Select) | e342 VAG 28, natif | `hyper_deejay_057D` |
| 041F | Birdie ZERO, début de match (banque déjà chargée : emplacements 08 / 01) | e322 VAG 26, natif | `hyper_birdie_041F` |
| 047A | Sagat Saikyo S-ISM, ↓↘→↓↘→ + poing | e325 VAG 26, 44,1 kHz natif | `hyper_sagat_047A` |

- Non vérifiés sur PS2 :
  - 0245 : entrée de jeu inconnue ;
  - 040F, et 054D, 054F-0551, 0554-0556, 055D, 055E de Cammy : présents dans la table « par pas » seulement, non vus
    dans mes essais. Ils passent par la même banque et le même mécanisme que les sons mesurés.
- Piège de la mesure : quand on enchaîne les écrans trop vite, la banque du perso peut ne pas être encore chargée. Un
  premier essai de Birdie avait l'emplacement de Dee Jay et rien n'a sonné. Il faut relire les emplacements
  (`[0x19E440]+0x38`) au moment de la commande.

## 9. Non-régression et Hyper + Arcade

- Hyper, ROM `roms/sons_v4`, balayage complet (418 essais) contre le zip d'origine (`tmp/compare_bal_sv4.txt`) :
  - journaux de pilote et journaux son identiques ;
  - WAV identiques à l'octet dans 361 essais ;
  - dans les 57 autres, la première différence suit la première commande ajoutée (custom combo en ZERO 2 / ALPHA,
    Birdie Z, Sagat Saikyo, Cammy ALPHA, Dee Jay) ;
  - 0 anomalie.
- Hyper + Arcade, sur une COPIE du zip du script (greffe ro9a35b, `zips/ha_orig` 31659547 → `zips/ha_v4` 7e27c305) :
  - VERSUS, 10 sélections (dont Cammy ALPHA, ZERO 2, Dee Jay, Sagat Saikyo, Mazi S-ISM) et gestes de parade : identiques,
    ou différents seulement après une commande ajoutée ;
  - mode ARCADE, 9 000 images (`outils/ha_arcade.sh`, avec ma copie de `hsfa_run`, journal son à 256 entrées) :
    - Ryu ZERO 3 et Ryu ZERO 2 : pilote, journal son et WAV identiques ;
    - Cammy ALPHA : pilote et journal identiques ; WAV différent à partir de l'image 800, qui est celle de la première
      commande ajoutée.
  - Aucun fichier de `work/greffe_arcade` n'a été touché. Le branchement passe par le paquet de la greffe du dépôt
    (`tools/greffe-arcade/construction/ro9a41/paquet/paquet_fbneo.py`, variable `HSFA_SON_HYPER`).
- Note pour `musique_ha` : son `hsfa_run` (journal `MJ`) ne lit que 16 des 256 entrées de la file : des commandes
  manquent dans ses journaux.

## 10. Fichiers

| chemin | rôle |
|---|---|
| `outils/sons_ps2.py` | correctif : ROM son d'Hyper = hybride + 21 sons PS2 seuls (`son_parade.py` = 1re version) |
| `outils/se_table.py`, `outils/inventaire_ps2.py`, `inventaire_ps2_se.json`, `outils/codes_emis.py` | résolution commande → échantillon par la table SE ; inventaire ; codes émis par immédiat |
| `outils/balayage.sh`, `outils/bilan_balayage.py`, `outils/compare_nr.py`, `outils/rendus.sh`, `outils/calibre.py`, `outils/voix_spu2.py`, `outils/ha_arcade.sh`, `outils/hsfa_run/` | balayage en jeu, non-régression, rendus isolés, calibrage, voix SPU2 d'un état, Arcade d'Hyper + Arcade |
| `outils/scei.py`, `outils/desmips.py` | lecture des banques SCEI HD/BD (e3xx) et décodage VAG ; désassembleur MIPS (ELF ou module) |
| `outils/cherche_vag.py`, `pics.py`, `fenetre.py`, `tous_vag.py`, `gain*.py`, `residu.py` | recherche d'un VAG dans une capture, niveau, retrait de la musique |
| `outils/joue_hp`, `outils/lance.sh`, `outils/z80cmd.py` | cœur sans écran avec journal de la file son ; table des commandes Z80 |
| `ps2/` | outils PCSX2 (`nav.py`, `sel.py`, `parade*.py`, `fin_match.py`), états, capture audio |
| `essais/` | journaux, WAV des essais au cœur |
| `donnees/` | extraits : `e345_vag92_octave_basse_ps2.wav` (référence PS2), `coeur_pv2_077C.wav` (correctif au cœur), `coeur_0307/0327/077C.wav` (avant) |
| `roms/sons_v4/`, `zips/sons_v4/`, `zips/ha_v4/` | ROM son finale et zips d'essai (Hyper ; Hyper + Arcade) ; `roms/parade_v2/`, `zips/parade_v2/` : parade seule |
| `a_verser/` | versement (diff, fichiers, LISEZMOI) |
| `re_ajouts/` | `allocations.tsv` (7 lignes), `ro9.tsv` (3 lignes) |
| `brouillon_ticket_1.md` | réponse au ticket (anglais, non postée) |
