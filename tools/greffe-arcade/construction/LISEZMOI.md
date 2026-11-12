# Greffe Arcade : construction depuis l'ISO (jeu `hyperarcade` de `hsfa_build.py`)

État figé : **ro9a38** (12/11/2026 ; programme `sz3ud.03c` md5 `2dfdb15c…`, zip de référence CRC `AC7D9F00`) :
ro9a37 + quatre correctifs de la revue de la greffe, chacun sous son interrupteur (R3 : `R3_CREUX`, `R3_CIBLES` ;
X6 : `X6_FINS` ; A2a : `A2A_VS` ; E2b : `E2B_DEFI` ; tous à 0 = ro9a37 à l'octet) dans `etape2/donnees2.py`,
`etape3/force3.py`, `etape3/greffe3.py` ; `X2_TABLES` (tables par perso prolongées pour les ids MAX) est présent mais
reste à 0 (hors ro9a38). Recette `ro9a38/greffe/vars_ro9a38.txt` = celle de ro9a37 + ces cinq interrupteurs (§223).
Précédents : ro9a37 (12/11, `627c98c4…`, CRC `51882820`, recette `ro9a38/greffe/vars_ro9a37.txt`) : ro9a36 traduite par
le traducteur de la greffe v161 (`e47/untranspile3_v161`) ; ro9a36 (11/11, `93e88fee…`, CRC `31F7E170`, recette
`vars_ro9a36.txt`) ; ro9a35b (08/11, `650b1bec…`, CRC `4D6E1D2D`, recette `vars_ro9a35b.txt`) (`HA_VARS`).
Expérimental.

## Contenu

| chemin | rôle |
|---|---|
| `greffe_ha.py` | étape « greffe » : matérialise le code et les relevés, puis enchaîne la greffe comme l'atelier (`construit_e3.sh`) : plan seul → table A5 → module, bloc, traduction. `--audit` : journal de tous les fichiers ouverts. |
| `fige35.py` | `materialiser` : recopie en remplaçant les marques `@HA_*@` par les chemins de la construction ; une marque non donnée devient un chemin absent (toute fuite vers l'atelier échoue). (`figer` ne sert qu'à l'atelier.) |
| `ro9a38/greffe/` | code de la greffe à l'état ro9a38 (`etape2`, `etape3`, `outils`, traducteurs de la greffe `e47/untranspile3_v161` et, pour les recettes précédentes, `e42/untranspile3_v160`) et décisions (adresses, interrupteurs) ; `vars_ro9a37.txt` = recette (celle de ro9a36 avec `TRAD=@HA_G@/e47/untranspile3_v161` ; ro9a36 = ro9a35b + `DECOR_E0=1 CONT_SORTIE=1 CONT_CHIFFRE=1`, exclusion `64b380`). |
| `ro9a38/carto/` | `commun.py` et analyses communes (code). |
| `ro9a38/paquet/paquet_fbneo.py` | paquet de la greffe (entrée `ro9a`, pilote `sfa3hahsfa`), inchangé depuis ro9a36. |

Aucune donnée de jeu. `releves_tsv.py` : tableaux des relevés (ci-dessous). Le traducteur de référence est celui du dépôt (`src/hsfa`, marque `@HA_UT@`).

## Relevés (`releves_ro9a38/`, tableaux TSV)

La greffe lit aussi des **relevés** de l'atelier, tirés de passes MAME sur le jeu et d'analyses statiques. Ils ne
contiennent que des adresses, des numéros (images, tailles, compteurs), des drapeaux et des étiquettes : aucun octet
du jeu. Ils sont versionnés en TSV (accord du 08/11, comme les tables de la Rosette des MAX), 18 tableaux, 4,5 Mo :

- `greffe/traces/journaux_{u_lu,defi_lu,objets_lu}.tsv` : union des 65 journaux d'adresses lues par Upper sous MAME
  (la construction n'en lit que l'union et les noms), en plages « début-fin » ;
- `greffe/traces/*/ram.txt.tsv` : cartes RAM d'Hyper et d'Upper (adresse, 1re / dernière image lue et écrite), en plages ;
- `greffe/donnees/*.tsv`, `eu/*.tsv` : analyses (routines, décisions, homologues, variables A5, couverture).

Chaque tableau commence par un en-tête « # » : origine, mesure, format. `releves_tsv.py reconstituer` redonne les
fichiers lus par les outils (`greffe_ha.py` le fait seul) ; `releves_tsv.py verifier` compare à des relevés d'origine.
Les relevés n'ont pas changé depuis ro9a35b (79 fichiers identiques à l'octet ; ro9a37, ro9a38 : simple renommage). Preuve :
greffe depuis ces tableaux = ro9a38 à l'octet. `--greffe-releves DOSSIER` permet d'en donner d'autres.

## Entrées venues de la construction

`HA_EXTRACT` (modules ro5 / ro9 décompressés), `HA_ANIMS` (cache des anims), `HA_XDATA`, `HA_MODULES_SON` (module ro9
corrigé + bloc `$E70000` si la table du rejeu est donnée, sinon module d'Hyper d'origine : voix de SFA3),
`HA_MAME_RO9` / `HA_MAME_RO5` (banques d'Hyper et d'Upper). Tout est produit par `hsfa_build.py` depuis l'ISO.

## Portabilité

Python + NumPy seulement (pas de MAME, pas de vasm). La greffe relance le traducteur par `sys.executable` (le
constructeur tout-en-un sert de « python ») ; liens symboliques remplacés par des copies si le système les refuse.

## Nouvelle livraison de la greffe

`hsfa_build.py` lit l'état dans une seule constante, `HA_ETAT` : code `<HA_ETAT>/`, recette
`<HA_ETAT>/greffe/vars_<HA_ETAT>.txt`, relevés `releves_<HA_ETAT>/`. Pour une nouvelle livraison, reporter le diff du
code de l'atelier (pas une nouvelle copie : elle perdrait les correctifs de portabilité), écrire la recette, vérifier
que les relevés lus n'ont pas changé (sinon `releves_tsv.py exporter`), renommer les deux dossiers, changer `HA_ETAT`,
puis prouver : greffe seule = construction figée de l'atelier à l'octet, et zip complet = zip livré hors
`hsfa_info.txt` (BUILD §11).
