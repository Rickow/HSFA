# Construire les jeux depuis l'ISO

`scripts/construction/hsfa_build.py` reconstruit SFA3, Upper et Hyper à partir de **votre** ISO de *Street Fighter
Alpha Anthology* : extraction, traduction des trois modules, ROM graphique, son, tables, et archives du cœur FBNeo.
Rapport complet : [rapports/BUILD.md](../rapports/BUILD.md) (§143-§144 du journal).

## 1. Prérequis

- Python 3.8+ et les modules de `requirements.txt` (`pip install -r requirements.txt`, de préférence dans un venv) ;
  numpy sert aux étapes graphiques (`gfx_*`). Ni MAME, ni assembleur externe : l'assembleur 68000 de la chaîne est en
  Python.
- Pour la musique des archives d'Upper et d'Hyper en Ogg Vorbis (par défaut) : `ffmpeg` avec libvorbis, `gcc` et
  `g++`. Sans eux : `--flux-format adx` (zip d'Hyper d'environ 740 Mo au lieu de 190) ou `--sans-flux`.
- L'ISO USA (`SLUS-21317`, 2 048 o/secteur). Les images `.chd`, `.bin` et `.cso` sont refusées : convertir d'abord en
  `.iso`. Un dossier qui contient `X_DATA.BIN` est aussi accepté.
- Facultatif : `--arcade sfa3.zip` (ROM graphique d'arcade de SFA3) au lieu de la reconstruire depuis l'ISO.

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
| `--jeux sfa3,upper,hyper` | jeux à construire (défaut : les trois) |
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
| `--outils-*` | emplacement de chaque groupe d'outils (sinon `HSFA_OUTILS_*`) |

Chaque étape est **idempotente** : elle est sautée si ses entrées, ses outils et ses paramètres n'ont pas changé
(`etat.json`). Une construction complète prend environ 6 min (dont 1 min 30 d'encodage Ogg) ; une relance sans changement, quelques secondes.

## 4. Sorties et vérification

- `hsfa_sortie/EMPREINTES.txt` : md5 de toutes les ROM produites et du contenu des archives.
- `hsfa_sortie/journal.txt` (marques `>>` étape, `ok`, `!!` anomalie) et `journaux/<étape>.log`.
- Archives du cœur : `archives/sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip`. Elles sont déterministes : deux
  constructions donnent les mêmes octets, Ogg compris (`ffmpeg -fflags +bitexact`, contrôle du 2026-10-27).

Ce qui est garanti (rapport BUILD §0, §3, §5 ; contrôle du 2026-10-27 contre les zips officiels v151, ISO « All
Unlocked », `--arcade`) :
- les ROM programme sont **identiques (md5)** à celles des zips officiels : SFA3 `e0f1cfdc…`, Upper `0b8ecca2…`, Hyper
  `39985037…` (avec la table du rejeu) ;
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
  le programme d'Hyper est celui de la v151 (`39985037…`) et le zip contient `hsfa_rejeu.bin` (8 Mo, copiés depuis le
  `X_DATA.BIN` de l'ISO, CRC contrôlés) et `hsfa_rejeu_table.txt`.
- Sans table, Hyper garde les voix de SFA3 pour toutes ses versions (programme `e21ebb89…`) et le zip n'a pas de
  rejeu : sans table, les codes de rejeu n'auraient pas de son.

Pas encore couvert : le contenu MAX.

## 5. Ensuite

- Copier les zips sur la console : [installation-android.md](installation-android.md),
  [installation-rocknix.md](installation-rocknix.md).
- Les cœurs se compilent à part : [patches/fbneo](../../patches/fbneo/README.md).
