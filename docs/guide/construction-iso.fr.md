# Construire les jeux depuis l'ISO

**English: [construction-iso.md](construction-iso.md)**

`scripts/construction/hsfa_build.py` reconstruit SFA3, Upper et Hyper à partir de **votre** ISO de *Street Fighter
Alpha Anthology* : extraction, traduction des trois modules, ROM graphique, son, tables, et archives du cœur FBNeo.
Rapport complet : [rapports/BUILD.md](../rapports/BUILD.md) (§143-§144 du journal).

## 1. Prérequis

- Python 3.8+ et les modules de `requirements.txt` (`pip install -r requirements.txt`, de préférence dans un venv) ;
  numpy sert aux étapes graphiques (`gfx_*`). Ni MAME, ni assembleur externe : l'assembleur 68000 de la chaîne est en
  Python.
- Pour la musique des archives d'Upper et d'Hyper en Ogg Vorbis (par défaut) : `gcc` et `g++`. L'encodeur
  `hsfa_oggenc` (`tools/flux/oggenc/`, README) est compilé une fois, depuis les sources officielles de libvorbis,
  libogg et musl (`construit_oggenc.py --sources DIR --telecharge`, puis `HSFA_OGGENC_SOURCES=DIR`, ou un binaire
  tout fait par `HSFA_OGGENC`). Plus de ffmpeg depuis le 08/11 (§206). Sans `gcc` / `g++` : `--flux-format adx` (zip
  d'Hyper d'environ 740 Mo au lieu de 190) ou `--sans-flux`. Sans rien installer : le constructeur tout-en-un
  (`tools/constructeur/`, un exécutable par système joint aux releases), qui lit aussi les `.chd`.
- L'ISO USA (`SLUS-21317`, 2 048 o/secteur). Les images `.chd`, `.bin` et `.cso` sont refusées : convertir d'abord en
  `.iso`. Un dossier qui contient `X_DATA.BIN` est aussi accepté.
- Facultatif : `--arcade sfa3.zip` (ROM graphique d'arcade de SFA3) au lieu de la reconstruire depuis l'ISO.
- Pour **Upper MAX** (Upper + Eagle, Maki, Yun, Ingrid ; §5) : l'ISO PSP de *Street Fighter Alpha 3 MAX*,
  **américaine** (ULUS-10062) ou **européenne** (ULES-00235 v1.01), `.iso`. Rien d'autre à installer : le code des MAX est assemblé par l'assembleur 68000 du
  projet (`tools/asm68k/`, Python). vasm reste utilisable pour comparer (`HSFA_ASM=vasm`, ou `HSFA_ASM=compare`).

## 2. Configurer

Rien à configurer : les outils sont pris dans le dépôt lui-même. `config.env` (copie de `config.example.env`) ne sert
que pour prendre d'autres outils (`HSFA_OUTILS_*`) ou pour le banc MAME.

Les scripts appelés gardent des chemins `<workspace>/...` : `hsfa_build.py` les remplace à l'exécution (table
`PARAMETRAGES` du script) et lance chaque outil dans un sous-processus à l'environnement propre.

## 3. Construire

```bash
python3 scripts/construction/hsfa_build.py \
    --anthology "Street Fighter Alpha Anthology (USA).iso" --sortie hsfa_sortie --jeux sfa3,upper,hyper
```

| Option | Effet |
|---|---|
| `--jeux sfa3,upper,hyper` | jeux à construire (défaut : les trois) ; `uppermax` en plus : Upper MAX (§5) ; `hyperarcade` : Hyper + Arcade (§6, expérimental) |
| `--psp-iso ISO` | (Upper MAX) ISO PSP de SFA3 MAX (USA ou Europe) ; sans elle, `uppermax` = Upper |
| `--vasm CHEMIN` | (Upper MAX, facultatif) chemin de `vasmm68k_mot` pour `HSFA_ASM=vasm` ou `compare` |
| `--arcade ZIP\|DOSSIER` | ROM graphique d'arcade (sinon voie « ISO seule », par défaut) |
| `--liste` | liste des étapes |
| `--etape NOM` / `--jusqua NOM` | refaire à partir de NOM / s'arrêter après NOM |
| `--force` | tout refaire (à utiliser après une modification de `hsfa_build.py` lui-même) |
| `--comparer DOSSIER` | comparer les sorties à un banc existant |
| `--date-source SECONDES` | date des membres des zips (défaut `$SOURCE_DATE_EPOCH`, sinon 1980-01-01) |
| `--plans-fenetre auto\|oui\|non` | tables de plans limitées aux codes honorés par le banc et le cœur |
| `--flux-format ogg\|adx` | format des flux musique d'Upper et d'Hyper dans les zips (défaut `ogg`) |
| `--sans-flux` | ni table de flux, ni flux dans les zips (musiques du disque absentes) |
| `--rejeu-table FICHIER` | (Hyper) table du rejeu des sons SFA1 / SFA2 (défaut : `tools/son-hyper/rejeu/hsfa_rejeu_table.txt` si elle est là) ; avec elle, redirection des voix par version et rejeu (§4) |
| `--sans-redirection` | (Hyper) ni redirection des voix ni rejeu, même avec la table |
| `--greffe-releves DOSSIER` | (Hyper + Arcade) autres relevés de la greffe que ceux du dépôt (§6) |
| `--outils-*` | emplacement de chaque groupe d'outils (sinon `HSFA_OUTILS_*`) |

Chaque étape est **idempotente** : elle est sautée si ses entrées, ses outils et ses paramètres n'ont pas changé
(`etat.json`). Une construction complète prend environ 6 min (dont 1 min 30 d'encodage Ogg) ; une relance sans changement, quelques secondes.

## 4. Sorties et vérification

- `hsfa_sortie/EMPREINTES.txt` : md5 de toutes les ROM produites et du contenu des archives.
- `hsfa_sortie/journal.txt` (marques `>>` étape, `ok`, `!!` anomalie) et `journaux/<étape>.log`.
- Archives du cœur : `archives/sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip`. Elles sont déterministes : deux
  constructions donnent les mêmes octets, Ogg compris. Depuis le 08/11 (§206, `hsfa_oggenc`), c'est vrai d'un
  système à l'autre (Linux, Windows, macOS, x86_64, ARM) : mêmes empreintes partout.

Ce qui est garanti (rapport BUILD §0, §3, §5 ; contrôle du 2026-10-27 contre les zips officiels v151, refait le 2026-10-28 en v153 et le 2026-11-03 en v154
(depuis l'ISO, sans table : Hyper `dda35430…`), ISO « All Unlocked », `--arcade`) :
- les ROM programme sont **identiques (md5)** à celles des zips officiels : SFA3 `e0f1cfdc…`, Upper `0b8ecca2…`, Hyper
  `b8e699cf…` (avec la table du rejeu) ; depuis le traducteur v161 (2026-11-11, §219) : SFA3 `a569c361…`, Upper
  `ac053140…`, Hyper `dbfd237d…` (avec la table ; sans : `ffc5eac1…`) ; v160 (§207) : SFA3 `9b06c7cf…`, Upper `3a9b7fd9…`,
  Hyper `0baed6af…` / `e3806660…` ; v159 (§203-§204) : Upper
  `45fd0244…`, Hyper `8e4f9ef2…` / `1f06234d…` ;
- avec `--arcade`, les archives aussi, membre à membre, hors `hsfa_info.txt` (journal de construction) et
  `hsfa_flux.bin` : ses flux Ogg ont le même audio, paquet Vorbis par paquet Vorbis, et seul leur en-tête de
  commentaires change (chaîne d'encodeur sans version depuis `+bitexact`) ;
- en voie « ISO seule », `sz3.14m`, `16m`, `18m`, `20m` sont identiques à l'arcade ; `13m`, `15m`, `17m`, `19m` ne
  peuvent pas l'être (9 tuiles de l'arcade n'existent pas dans l'ISO), sans effet sur les jeux HSFA ;
- l'ISO est vérifiée **par groupe de jeu** : la variante « All Unlocked » de `X_DATA.BIN` convient aussi.

**Hyper : voix par version et rejeu** (étape `son_hyper`, SON-HYPER-ROM §12-§13) :
- `gen_redirection.py` relit le module `ro9` extrait de **votre** ISO et produit le module corrigé (70 mots, md5
  `dcda2bb…`) et le bloc de données `$E70000` (`son_donnees_ro9.bin`, 19 712 o, `ebefd8b2…`). Les deux contiennent des
  octets du jeu : ils sont **régénérés à chaque construction** et jamais publiés. Le dépôt ne fournit que des tables :
  `ids_102.tsv` (versions), `correspondance.tsv` (code SFA3 → commande SFA1 / SFA2).
- La **table du rejeu** (traces QSound des pilotes SFA1 / SFA2, 3,2 Mo) est une entrée à part : `--rejeu-table` ou
  `tools/son-hyper/rejeu/hsfa_rejeu_table.txt`. La construction y ajoute la section des cris par version. Avec elle,
  le programme d'Hyper est celui de la v161 (`dbfd237d…` ; v160 : `0baed6af…` ; v159 : `8e4f9ef2…` ; v154-v158 : `b8e699cf…`) et le zip contient `hsfa_rejeu.bin` (8 Mo, copiés depuis le
  `X_DATA.BIN` de l'ISO, CRC contrôlés) et `hsfa_rejeu_table.txt`.
- Sans table, Hyper garde les voix de SFA3 pour toutes ses versions (programme `ffc5eac1…` en v161, `e3806660…` en v160, `1f06234d…` en v159, `dda35430…` en v154-v158) et le zip n'a pas de
  rejeu : sans table, les codes de rejeu n'auraient pas de son.

## 5. Upper MAX (persos de SFA3 MAX)

```bash
python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" \
    --psp-iso "Street Fighter Alpha 3 MAX (USA).iso" --sortie hsfa_sortie --jeux upper,uppermax
```

- Résultat : `archives/sfa3umhsfa.zip` (pilote `sfa3umhsfa` du cœur). C'est l'état du lot **2b31**, porté sur le traducteur courant (v161 : le
  programme suit celui d'Upper). La ROM son est identique à ce lot ; avec `--arcade`, les graphismes aussi, hors `hsfa_info.txt`.
- Il ne faut pas de dump PPSSPP ni d'EBOOT déchiffré : le `BOOT.BIN` de l'ISO est déjà en clair (une ISO « déchiffrée »
  est acceptée aussi : elle ne diffère que par `EBOOT.BIN`, qui n'est pas lu). L'ISO est contrôlée : édition
  (`PARAM.SFO`) et empreintes des fichiers lus. Une ISO patchée (16:9 par exemple) ou un EBOOT chiffré sont refusés
  avec un message.
- **Les éditions américaine (ULUS-10062) et européenne (ULES-00235) donnent le même jeu, à l'octet.** L'édition est
  reconnue sur le disque. Le `BOOT.BIN` américain a son code 8 octets plus bas (une fonction d'écran du moteur est plus
  courte) : la construction le remet aux adresses européennes. 6 lignes des textes des persos MAX écrivent
  « Shadowloo » sur le disque américain : elles sont réécrites « Shadaloo », comme sur le disque européen et partout
  dans l'Anthology (`tools/integration-max/upper_max/psp_region.py`).
- L'édition japonaise (*Street Fighter Zero 3 Double Upper*, ULJM) est refusée avec un message : autre disposition
  du code, textes japonais.
- Durée : environ 2 min 30 de plus qu'Upper seul ; place : environ 500 Mo de plus.
- Détail et preuves : [rapports/BUILD.md](../rapports/BUILD.md) §10 ;
  [tools/integration-max/upper_max](../../tools/integration-max/upper_max/README.md).

## 6. Hyper + Arcade (mode Arcade d'Upper greffé sur Hyper, expérimental)

```bash
python3 scripts/construction/hsfa_build.py --anthology "Street Fighter Alpha Anthology (USA).iso" \
    --sortie hsfa_sortie --jeux hyperarcade [--rejeu-table hsfa_rejeu_table.txt] [--arcade sfa3.zip]
```

- Traducteur : la greffe a sa copie figée du traducteur **v161** (`untranspile3_v161`, états ro9a37 à ro9a41, §221, §223, §224, §228, §230) : les
  correctifs de la v161 (§219) atteignent Hyper + Arcade.
- Résultat : `archives/sfa3hahsfa.zip` (pilote `sfa3hahsfa` du cœur), état **ro9a41** (13/11 ; ro9a40 + 10 paires de mots des données de la greffe qui ne sont plus relogées comme des pointeurs de code, §230 ; ro9a40 : couleurs et portraits des versions, bande verte de la transition « logo », §225-§228). `hyperarcade`
  ajoute `upper` et `hyper` : la greffe part de leurs sorties (modules, anims, banques, son). Étapes en plus :
  `greffe_hyperarcade` (code figé de `tools/greffe-arcade/construction/`, environ 3 min) et `paquet_hyperarcade`.
- **Avec la ROM d'arcade et la table du rejeu** : le zip est celui de ro9a41 (livré le 13/11, CRC `C9107FC2`), hors
  `hsfa_info.txt` (provenance) et la ROM son (`hx3.01`, `hx3.02`, `hx3.14m` : sons propres au portage PS2 ajoutés,
  §218 ; avec `HSFA_SONS_PS2=0`, identique).
- **Sans la table du rejeu** : la greffe part du module d'Hyper d'origine. Hyper garde les voix de SFA3 pour toutes
  les versions, et le zip n'a pas de rejeu (`hsfa_rejeu.bin`, `hsfa_rejeu_table.txt` absents), comme Hyper seul.
- **Sans la ROM d'arcade** (voie ISO seule) : ROM graphique reconstruite depuis l'ISO, comme pour Hyper ; seuls la
  ROM graphique, `hsfa_gfx.bin` et `hsfa_tab.bin` changent (codes de tuiles), le programme est le même. Au cœur, la
  partie et l'image sont les mêmes (l'ombre au sol des persos ZERO / ZERO 2 est transparente dans les deux voies depuis
  `HSFA_OMBRE_CODES`, BUILD §11.5).
- **Relevés** : la greffe relit des tableaux tirés de passes MAME et d'analyses de l'atelier (adresses et numéros
  seulement, 4,5 Mo de TSV dans `tools/greffe-arcade/construction/releves_ro9a41/`) ; `--greffe-releves` en donne
  d'autres. Détail : [tools/greffe-arcade/construction](../../tools/greffe-arcade/construction/LISEZMOI.md).
- Durée : environ 2 min 30 de plus qu'Upper + Hyper (greffe 130-160 s, paquet 8 s) ; place : environ 0,4 Go de plus.
- Détail et preuves : [rapports/BUILD.md](../rapports/BUILD.md) §11.

## 7. Ensuite

- Copier les zips sur la console : [installation-android.fr.md](installation-android.fr.md),
  [installation-rocknix.fr.md](installation-rocknix.fr.md).
- Les cœurs se compilent à part : [patches/fbneo](../../patches/fbneo/README.fr.md).
