# Greffe Arcade : construction depuis l'ISO (jeu `hyperarcade` de `hsfa_build.py`)

État figé : **ro9a35b** (08/11/2026 ; programme `sz3ud.03c` md5 `650b1bec…`, zip de référence CRC `4D6E1D2D`).
Expérimental.

## Contenu

| chemin | rôle |
|---|---|
| `greffe_ha.py` | étape « greffe » : matérialise le code et les relevés, puis enchaîne la greffe comme l'atelier (`construit_e3.sh`) : plan seul → table A5 → module, bloc, traduction. `--audit` : journal de tous les fichiers ouverts. |
| `fige35.py` | `materialiser` : recopie en remplaçant les marques `@HA_*@` par les chemins de la construction ; une marque non donnée devient un chemin absent (toute fuite vers l'atelier échoue). (`figer` ne sert qu'à l'atelier.) |
| `ro9a35b/greffe/` | code de la greffe à l'état ro9a35b (`etape2`, `etape3`, `outils`, traducteur de la greffe `e42/untranspile3_v160`) et décisions (adresses, interrupteurs) ; `vars_ro9a35b.txt` = recette (interrupteurs de ro9a35b). |
| `ro9a35b/carto/` | `commun.py` et analyses communes (code). |
| `ro9a35b/paquet/paquet_fbneo.py` | paquet de ro9a35b (entrée `ro9a`, pilote `sfa3hahsfa`). |

Aucune donnée de jeu. `releves_tsv.py` : tableaux des relevés (ci-dessous). Le traducteur de référence est celui du dépôt (`src/hsfa`, marque `@HA_UT@`).

## Relevés (`releves_ro9a35b/`, tableaux TSV)

La greffe lit aussi des **relevés** de l'atelier, tirés de passes MAME sur le jeu et d'analyses statiques. Ils ne
contiennent que des adresses, des numéros (images, tailles, compteurs), des drapeaux et des étiquettes : aucun octet
du jeu. Ils sont versionnés en TSV (accord du 08/11, comme les tables de la Rosette des MAX), 18 tableaux, 4,5 Mo :

- `greffe/traces/journaux_{u_lu,defi_lu,objets_lu}.tsv` : union des 65 journaux d'adresses lues par Upper sous MAME
  (la construction n'en lit que l'union et les noms), en plages « début-fin » ;
- `greffe/traces/*/ram.txt.tsv` : cartes RAM d'Hyper et d'Upper (adresse, 1re / dernière image lue et écrite), en plages ;
- `greffe/donnees/*.tsv`, `eu/*.tsv` : analyses (routines, décisions, homologues, variables A5, couverture).

Chaque tableau commence par un en-tête « # » : origine, mesure, format. `releves_tsv.py reconstituer` redonne les
fichiers lus par les outils (`greffe_ha.py` le fait seul) ; `releves_tsv.py verifier` compare à des relevés d'origine.
Preuve : greffe depuis ces tableaux = ro9a35b à l'octet. `--greffe-releves DOSSIER` permet d'en donner d'autres.

## Entrées venues de la construction

`HA_EXTRACT` (modules ro5 / ro9 décompressés), `HA_ANIMS` (cache des anims), `HA_XDATA`, `HA_MODULES_SON` (module ro9
corrigé + bloc `$E70000` si la table du rejeu est donnée, sinon module d'Hyper d'origine : voix de SFA3),
`HA_MAME_RO9` / `HA_MAME_RO5` (banques d'Hyper et d'Upper). Tout est produit par `hsfa_build.py` depuis l'ISO.

## Portabilité

Python + NumPy seulement (pas de MAME, pas de vasm). La greffe relance le traducteur par `sys.executable` (le
constructeur tout-en-un sert de « python ») ; liens symboliques remplacés par des copies si le système les refuse.
