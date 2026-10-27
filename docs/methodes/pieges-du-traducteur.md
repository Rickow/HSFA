# Pièges du traducteur

Catalogue des pièges rencontrés en retraduisant le MIPS du recompilateur en 68000, classés par famille. Ils valent
pour tout binaire produit par un recompilateur statique (la session SFA3 MAX s'en sert pour la PSP). Les « §N »
renvoient au [journal](../journal/HANDOFF.md) ; méthode de détection : [oracle-et-non-regression.md](oracle-et-non-regression.md).

## 1. Adresses et bornes

- **Base d'exécution fausse de 8 octets** (§5) et **bornes de la zone de code fausses** (§4) : tout a l'air de marcher
  à 99 %. Les vérifier sur des références croisées sûres (vecteurs, tables de saut).
- La zone de code contenait **deux processeurs** : Z80 puis 68000 (§16). Dans d'autres modules, le Z80 n'est pas en
  tête ([carte des modules](../reference/carte-modules.md)).
- Les écritures d'An **convertissent** les adresses 68K en adresses hôte (§10). Un pointeur de données lu en mémoire
  est une adresse hôte, à reconvertir à l'usage (talons de conversion, §76).
- Les pointeurs de **code** sont des adresses hôte : il faut une table de correspondance, et un hachage pour la
  performance (§98).
- Une table d'aiguillage peut être indexée par un **index brut** au lieu d'un index ×2 / ×4 (§102, §112 : SURVIVAL
  plantait).
- Découper le MIPS en fonctions par les cibles de `jal`, jamais par `jr ra`.

## 2. Disposition mémoire (le plus traître)

- Le recompilateur type **par champ** (§44) : le même octet 68K n'est pas toujours au même endroit selon la lecture.
- Recette retenue ([memoire-cps2](../architecture/memoire-cps2.md)) : octet = adresse XOR 1, mot = même adresse,
  long = moitiés échangées. Pièges propres à cette recette :
  - mot à octets inversés lu dans une table **indexée** (§92, §100) ;
  - long rangé octet par octet (`bswap32`, §90) ;
  - octet lu via un registre d'adresse de **parité inconnue** (après `ADDA Dn,An`) : l'adresse exacte se calcule à
    l'exécution, l'XOR fixe est faux (§97) ;
  - **flux d'octets `(An)+`** (§65) : après `MOVE.B (A3)+,x ; MOVE.B (A3)+,y`, la forme `ADDQ #1,A3 ; MOVE.B -2(A3)`
    n'est juste que si A3 est impair ; sinon on lit l'octet voisin. Cause du texte du gros A qui défilait mal dans les
    trois jeux (16 sites, règle `FLUXEA`) ;
  - unions (`s16[2]` / `s32` selon la fonction, §44).
- Hyper a été produit par une version **plus récente** du recompilateur (§52), avec d'autres idiomes : ne jamais
  supposer qu'un binaire suit les règles d'un autre.

- **Temporaire de pile chargé depuis la mémoire pris pour la constante d'un `lui` périmé du même registre** (§162, `PILE_LUI`) : le CMP n'est pas émis et le branchement lit les drapeaux de l'appelant ; signe distinctif : fonctions à prologue `sq`.

## 3. Drapeaux et branchements

- Les cases d'état ne sont pas celles qu'on croit : `0x1158` est la **retenue**, pas N (§11).
- Les drapeaux de `CMP` / `SUB` doivent être exacts (§20) ; ceux de `SUBI` en place aussi (§90).
- **Drapeaux rendus à l'appelant** : une routine finit par un `BTST` / `CMP` et c'est l'appelant qui branche (§87, §93,
  §125). Un épilogue partagé peut les écraser (§126). Suivre les drapeaux à travers les retours.
- **`CMP` mémoire-mémoire** (pas de forme 68K directe) : il était perdu, et le branchement relisait des drapeaux
  périmés. Cause de la jauge sans plafond d'Hyper (`CMPMM`, §145).
- Le **DBRA** du recompilateur boucle tant que ≥ 0 (`SUBQ.W ; BPL`), pas tant que ≠ −1 (§74).
- Branchements lointains ; appels terminaux supprimés alors qu'ils étaient cibles de branchements (`TAILBR`, §143) ;
  fusion de branchements par l'assembleur (§91).

## 4. Pertes silencieuses vues

Toutes trouvées par un symptôme en jeu, puis prouvées contre l'arcade.

| Défaut | Symptôme | § |
|---|---|---|
| `ADDI.L` perdu | portraits faux | §85 |
| `MOVEA.W An,Am` perdu | blocs dans le décor au K.O. | §86 |
| extension de signe en trop | son | §79 |
| lecture signée étendue perdue | plantage du perso `$22` d'Upper | §128 |
| constante `lui` seule rangée dans un registre de données, prise pour une adresse | supers d'Akuma et de Dan, boules multi-coups de Sakura (`LUIDN`) | §143 |
| registre écrit sans aucune instruction émise | divers | §107, §132, §137 |
| `CMP` mémoire-mémoire | jauge d'Hyper, plantage TRAINING (`CMPMM`) | §145 |
| `EXG Dx,Dy` du recompilateur (cases de registres) rendu par deux `MOVE` : la case relue après son écrasement ; `BCLR` testé après l'effacement ; aide `roxr` inconnue traduite en talon vide | Killer Bee Assault de Cammy raté dans Hyper et Upper (angle 0) ; `paires_exg.py` trouve les autres `EXG` perdus | §171 |

## 5. Registres et pile

- Le recompilateur a des registres **supplémentaires** « A8 » et « D8 » (§53). HSFA les prête à des registres libres
  par zones, avec des domiciles en RAM (`$87E0` / `$87F0(A5)`).
- Les **sorties latérales** de ces zones coûtent cher : combat miroir (§130).
- Pile privée du recompilateur en `0x114C` (§72), ramenée sur la pile 68K.

## 6. Code ajouté par le portage

- Crochets dans les fonctions ancrées elles-mêmes (§7, §12).
- Ressources chargées par le code natif, `setjmp` / `longjmp` (§75).
- Noyau de tâches à reconstruire (§60-§61).
- Couche matérielle « mirroitée » en variables (§57-§58).
- Code **C** du portage : ses propres idiomes (aiguilleurs par table de longs, `lb ; bne r,zero`, §140). Ne pas le
  traduire comme du 68K recompilé.

## 7. Assembleur

- Entrées de table d'aiguillage hors de portée 16 bits (§94).
- Placement itératif nécessaire (§22).
- `assemble.py` relit des **marqueurs dans les mnémoniques** produits par `translate.py` (`(cible …)`, `[mips …]`,
  `T_…`, `CODE_…`, `_ECH`) : ne pas changer leur format.

## 8. Banc et données

- Une écriture relevée à « l'image N » a lieu pendant N+1 ; `-debug` décale le minutage ; les prises d'opcodes voient
  la prélecture (§67, §81, §82, §114).
- `sfa3_prog.bin` a des données fausses dans `$0-$BFFFF` : les tables se lisent dans `sfa3ud_prog.bin` (§96).
- Couverture : toujours en union, et distinguer « étendue » et « utilisable » (R§6bis, C2).
- Profil : les adaptateurs mémoire (conversions de pointeurs, longs échangés, octets XOR, registres prêtés) coûtent
  ~20 % du temps 68K en combat (§138) : c'est l'objet de la
  [réorganisation des données](../architecture/ARCHI-Reorganisation-Donnees.md).

## 9. Pièges propres à la PSP (traducteur MIPS PSP → 68K de la session MAX)

Traducteur : `max/outils/rosette_code/traduire.py` ; détails : [max-integration-upper](../../max/notes/max-integration-upper.md),
[max-portage-code](../../max/notes/max-portage-code.md).

- **Cibles de `jal` 0-based** : le PRX est relogé au chargement ; cible = `imm26 << 2` (`tools/max/modules.py`).
- **Créneau de délai pointé par une donnée** : un mot de données peut viser l'instruction qui suit un saut. Ce n'est
  pas un début de fonction, sinon la fonction est coupée (`0x1B3450`, `tools/max/charcode2.py`).
- **Découpage en modules** : les gestionnaires des persos MAX sont rangés AVANT la racine. Couper à la dernière
  fonction atteinte depuis la racine, pas à la racine suivante (114 fonctions d'Eagle oubliées).
- **Taille de lecture** : le C élargit des champs. Lire à la plus petite des tailles PSP et 68K ; une lecture d'octet
  (`lb`) utilisée dans un calcul sur mot se lit en octet puis s'étend, jamais `MOVE.W` à une adresse impaire
  (`lb 0x4D` → `$35`).
- **Champs PSP sans équivalent** (position d'impact `0x2CA-0x2DE`, effet attaché `0x38`) : omettre l'écriture ET la
  lecture de la source.
- **Champs privés** : ne pas loger les champs propres aux persos MAX dans `$28-$2F` (pris par le moteur générique) ;
  `$5C` / `$60` libres.
- **Structures de taille différente** : joueur PSP de `0x498` o contre `$400` ; une boucle d'effacement PSP (72 longs depuis
  `+0x350`) débordait sur le joueur suivant.
- **Tables de pointeurs de fonctions** lues à tort comme des scripts d'animation : trancher avec Ghidra (extension
  Allegrex, `max/outils/ghidra/ghidra_decomp.py`).
- **Repère des octets** : un même octet a deux numéros selon le repère. Dans l'image en mémoire CPS2, l'octet 0 d'un pas porte
  les drapeaux ; dans l'arcade et dans les octets bruts du fichier, l'octet 0 est la durée. Toujours dire dans quel
  repère on écrit.
- **Données recopiées** : tables lues par adresse recopiées en gros-boutiste ; attaques : octets `$12` / `$14` ×2.
- **vasm** : `cnop` bourre avec `$4E71` (NOP), pas avec des zéros : bourrer explicitement (`dcb.b`) quand un octet
  compte.

Liste des pièges du banc et de l'environnement : [journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md) §7.
