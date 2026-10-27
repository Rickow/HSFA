# La mémoire en « mode CPS2 » (§29)

## 1. Le problème

Le code PS2 lit et écrit la mémoire en **petit-boutiste**, à des adresses PS2. Le 68000 de la CPS2 est
**gros-boutiste**, avec sa propre carte (RAM `$FF0000`, vidéo `$900000`, objets `$700000`…). Le recompilateur a en
plus typé la mémoire **champ par champ** (§44) : le même octet 68K n'est pas toujours au même endroit selon la façon
dont le champ est lu. Retrouver la disposition arcade exacte demande de typer chaque champ ; c'est le but, à terme, de
la [réorganisation des données](ARCHI-Reorganisation-Donnees.md).

## 2. La recette universelle

Décision du §29 : pour un jeu **qui fonctionne**, il suffit que le 68K voie la mémoire **comme le code PS2 la voit**.

| Accès PS2 (adresse hôte h) | Traduction 68K |
|---|---|
| mot | même adresse h |
| octet | h XOR 1 |
| long | même adresse, moitiés échangées (`SWAP`) |

La recette ne demande aucune connaissance des champs. Elle vaut pour les longs à 2 mod 4 et pour les trois jeux. Coût :
un `SWAP` par accès long, sauf les copies mémoire → mémoire et les immédiats, pré-échangés à la traduction.

## 3. Conversion des adresses

`translate.addr_to_68k` convertit les constantes d'adresse, dans cet ordre :
1. variables du portage qui « mirroitent » le matériel → vrais registres CPS-A/B, entrées `$804000…` (§57, §62) ;
2. RAM PS2 → `$FF0000`, QSound → `$618000`, objets → `$700000/$708000`, vidéo → `$900000` (`ADDRMAP`) ;
3. données du module → `DATA_BASE` en ROM, ou `DATA_EXT` quand le programme dépasse 4 Mo (`$C80000` Upper,
   `$940000` Hyper) ;
4. variables propres au portage → `PORT_RAM` (`$F00000`).

Les adresses matérielles reçoivent l'octet haut `$01` (`HW_TAG`), ignoré par le bus 24 bits, pour ne pas être
reconverties (§63).

**Pointeurs lus en mémoire** : ce sont des adresses PS2. Un pointeur de données est converti après chaque `MOVEA` qui
le charge (talons « convertir An » en `$000400`, §63, §104). Un pointeur de code passe par une **table de hachage**
adresse PS2 → 68K (`$3C0000`, 16 384 entrées, §98) avant chaque `JSR/JMP (An)`.

## 4. Banc de registres du recompilateur (version juste)

| Case `0x7000xxxx` | Registre 68K |
|---|---|
| `0x1100-0x111C` | A0-A7 (A7 = pile MIPS du portage) |
| `0x1120` | **A8** (supplémentaire) |
| `0x1124-0x1140` | D0-D7 |
| `0x1144` | **D8** (supplémentaire) |
| `0x114C` | pile privée |
| `0x1150` | RES (Z, N) |
| `0x1154` | X |
| `0x1158` | **C (retenue)** |

Base d'exécution `0x1F0000` ; le 68K commence à `0x22B00` (ro3, ro5) ou `0x22DE0` (ro9). Voir aussi
[OUTILS.md](OUTILS.md) §2.4.1.

## 5. Exceptions et pièges

1. **Déplacements A5 signés** : `$BE48(A5)` = `$FF3E48`, `-$7178(A5)` = `$FF0E88` (§67, §86, §108).
2. **Octets exacts** (pas de XOR) : ports d'entrée et QSound (§62, §78) ; flux `(An)+`, index impairs, octet après
   `ADDA Dk,An` : l'adresse exacte est calculée à l'exécution (§65, §66, §97).
3. **Longs à moitiés échangées en mémoire** : X/Y d'un objet en `+$12/+$16` au lieu de `+$10/+$14` ; octets d'état
   `$4-$7` échangés par mot ; un long empilé tel quel reste échangé (§77).
4. Mot à octets inversés lu dans une table **indexée** (§92, §100) ; long rangé octet par octet (`bswap32`, §90).
5. Une constante **impaire** n'est jamais une adresse de données (§101).

**Conséquence pour les outils** : tout script qui compare la traduction à l'arcade doit normaliser (octet `a` de la
ROM = octet `a ^ 1` de la traduction, X/Y décalés, octets d'état échangés). L'accesseur `disposition.lua`
([tools/reorg](../../tools/reorg/)) lit la RAM traduite par adresse arcade.

## 6. Carte de l'image produite

La ROM programme de 4 Mo contient les vecteurs, les talons de conversion, le noyau de tâches (`$000B00`), le code
traduit (`$001000…`), les données du module, les ressources, la table de hachage (`$3C0000`) et la table des débuts de
fonction (`$3E0000`). Hors ROM : piles des tâches (`$660000`), mémoire d'objets, vidéo, blocs externes (`$A00000-$EFFFFF`),
RAM de travail (`$FF0000`). Table complète : [OUTILS.md](OUTILS.md) §1.4 ; adresses utiles :
[reference/adresses.md](../reference/adresses.md).
