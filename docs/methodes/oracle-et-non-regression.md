# Oracle et non-régression

Méthode de travail du traducteur, valable pour tout projet de retraduction d'un binaire recompilé (HSFA, et la
transcription PSP de SFA3 MAX). Les « §N » renvoient au [journal](../journal/HANDOFF.md).

## 1. Un oracle d'abord, jamais l'œil

1. **La référence est l'arcade sous MAME** (ROM `sfa3ud`, `REF=1`), pas l'émulateur de la console.
2. Une même partie **scriptée** (Lua, entrées à l'image près) tourne des deux côtés : `tournee.lua`, `commandes.lua`,
   `jeu.lua` ([banc-mame](../architecture/banc-mame.md)).
3. On compare des **grandeurs** : RAM, positions d'objets image par image, captures, nombre d'images jusqu'à un
   événement. Un défaut qui « se voit » se prouve par une grandeur : le texte du gros A qui défilait mal a été réduit
   à la position de 6 sous-objets, égale à l'arcade sur 346 images une fois corrigé.
4. Avant de toucher au traducteur, vérifier que l'écart vient du **jeu traduit** : le glitch du portrait d'Upper
   venait du banc et du cœur, qui changeaient de banque graphique trop tôt (§146). Comparer d'abord l'ordre des
   écritures du jeu à l'arcade.

## 2. La batterie de non-régression

Relancée après **chaque** règle ajoutée au traducteur ([`scripts/validation/`](../../scripts/validation/)) :

| Script | Contrôle | Attendu | Durée |
|---|---|---|---|
| `nonreg.sh` | SFA3 : attraction 20 000 images sans entrée, 20 000 avec pièce / Start / bouton, partie offensive de 60 000 images, puis test des 42 commandes | 3 × « aucune exception », « 42 actions, 0 différentes », 5 359 tours en 4 019 images (133,3 %) | ~2 h |
| `nonreg_ro5.sh` | Upper : attraction 20 000 images, puis trois parties Arcade (Ryu, Chun-Li, Akuma) sur le fork | « aucune exception », « fin=finie » ×3 | ~15 min |
| `balayage_fins.sh` | une partie Arcade par perso jusqu'à sa fin (32 SFA3, 40 Upper) | SFA3 : captures = arcade ± 1 ; Upper : « fin=finie » | long |
| `valide_tout.sh` | reconstruit ro3, ro5, ro9, puis tout ce qui précède + une partie VERSUS d'Hyper | aucune ligne « ECART » | ~3 h |

Beaucoup de régressions ne se voyaient **que dans les fins** (§137) : le balayage des fins n'est pas facultatif.

## 3. Un interrupteur par règle

- Chaque règle du traducteur a sa variable d'environnement ; `=0` rend l'ancien comportement.
- **`=0` doit redonner des ROM identiques à l'octet (md5).** On peut alors bissecter, isoler l'effet d'une règle et
  livrer un correctif sous forme de diff sans risque.
- Exemples : `TAILBR`, `LUIDN` (§143), `CMPMM` (§145), `FLUXEA` (flux d'octets `(An)+`, gros A), `EXT_MEM` (§128).
- Chaque construction affiche un **compteur par règle** (« CMP mémoire-mémoire : n sites ») : une variation
  inattendue est un signal.

## 4. « 0 non résolu » ne veut pas dire correct

Les pires défauts sont des **pertes silencieuses** : une instruction source qui ne produit rien, ou une forme fausse
mais qui assemble. Outils :

| Outil | Rôle | § |
|---|---|---|
| `census.py` | ce que le traducteur rate, sur tout le binaire | §17-§18 |
| `chutes.json` (audit des écritures de registre) | registres écrits sans aucune instruction émise | §107, §132, §137 |
| `AUDIT_MEM=1` → `mem_miss.json` | écritures mémoire sans trace | §107, §138 |
| `audit_exacts.txt` | comparaisons « drapeaux exacts » à opérande inconnu | §126 |
| `diverge.py` | **première** divergence face à l'arcade | §37 |
| `verify.py` | vérificateur indépendant (fiable là où le traducteur a émis quelque chose) | §3 |
| `e2e.py` | oracle **statique** : traduire, assembler, comparer à la ROM arcade fonction par fonction | §23 |
| `hooks.py` | carte des zones : code d'origine, code ajouté par le portage, données, veneers | §21 |

91 % du code de SFA3 s'aligne fonction par fonction sur la ROM arcade (`layout_pairs.json`) ; pour un binaire sans
corrigé, chercher l'homologue de chaque routine dans un jeu qui en a un (Upper pour MAX).

## 5. Oracle RAM et journal des conversions

L'étape A de la réorganisation des données ([ETAPE-A](../rapports/ETAPE-A.md), outils dans
[`tools/reorg/`](../../tools/reorg/)) ajoute deux oracles :
- **RAM traduction ↔ arcade** (`compare_ram.py`) : même partie, vidages au début des manches ; une zone typée doit être
  identique à l'arcade ;
- **journal des conversions** (`journal_conv.lua`) : chaque adresse PS2 brute vue par un talon de conversion ; le but
  est un journal vide.

## 6. Hygiène

- Ne jamais tracer sur une construction qu'un autre peut refaire : figer une copie des ROM, noter les md5.
- Un calcul lourd à la fois, `nice -n 19`.
- MAME : `-nvram_directory` et `-cfg_directory` temporaires, jamais `-state` en ligne de commande, jamais `pkill -f`.
- Après chaque reconstruction, relire `carte_image.txt` avant de poser un point d'arrêt.
