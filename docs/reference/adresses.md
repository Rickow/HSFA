# Adresses utiles

Adresses **68K côté CPS2** (traduction), sauf mention. Les octets de la traduction sont à l'adresse XOR 1 de ceux de
l'arcade ([memoire-cps2](../architecture/memoire-cps2.md)). Carte complète des symboles de SFA3 (10 246 symboles,
trois espaces d'adresses) : [SYMBOLES.md](SYMBOLES.md) et `tools/symboles/symboles_ro3.csv`.

## 1. RAM de jeu (A5 = `$FF8000`)

| Adresse | Contenu | Source |
|---|---|---|
| `$FF8000` / `$FF8002` / `$FF8004` | modes de jeu (journal de `jeu.lua`) ; `A5+4` = scène | §80, [GREFFE-PREPARATION](../rapports/GREFFE-PREPARATION.md) §0 |
| `$FF8008` | sous-scène (`A5+8`) entre deux combats | GREFFE-PREPARATION §0 |
| `$FF8100` | décor courant (`$100(A5)`, mot = décor × 2) | §92, [REIMPORT](../rapports/REIMPORT.md) §5 |
| `$FF8400`, `$FF8800` | structures des joueurs 1 et 2 (`A5+$400`, `A5+$800`) ; vie = mot `+$50` | R§0, §110 |
| `$FF8C00`, `$FF9000` | joueurs 3 et 4 (DRAMATIC BATTLE) | §102 |
| `$FF8540` | masque des adversaires battus (forcé par `tournee.lua` pour aller droit aux fins) | §111 |
| `$FF4001` | curseur du menu des modes | §112 |
| `$FF3E48` (ro3) / `$FF40BC` (ro5, ro9) | pointeur d'animation de la scène (`$BE48(A5)` / `$C0BC(A5)`) | §106, §115 |
| `$FF0000-$FFFFFF` | RAM de travail (RAM PS2 `0x00000-0x0FFFF`) | [OUTILS](../architecture/OUTILS.md) §1.4 |

Déplacements A5 **signés** : `$BE48(A5)` = `$FF3E48`, `-$7178(A5)` = `$FF0E88`.

**Hyper** : champ perso `$102` = id étendu (perso × version, `0..$7F`) ; `$116` = id de base, `$117` = version
(`$D3`) ([INDEX-HYPER](../rapports/INDEX-HYPER.md)). Zone A5 libre utilisée par la greffe : `$FF43BE-$FF7FFF`.

## 2. Matériel CPS2 et portage

| Adresse | Contenu | Source |
|---|---|---|
| `$618000-$619FFF` | mémoire partagée QSound (boîte aux lettres du son) | §58 |
| `$61801F` | pose d'une commande son (crochet du lecteur de flux et du rejeu) | [REJEU-FBNEO](../rapports/REJEU-FBNEO.md) |
| `$700000`, `$708000` | mémoire d'objets (deux pages) | OUTILS §1.4, §103 |
| `$804000…` | entrées | §62 |
| `$804102-$804107` | bases des plans (CPS-A) | OUTILS §4.2 |
| `$804200-$804205` | **fork / cœur** : une base par plan (unités de 64 Ko de la région graphique) | §120 |
| `$900000-$92FFFF` | mémoire vidéo | OUTILS §1.4 |
| `$A00000-$EFFFFF` | blocs externes (`ext_<adresse>.bin`) ; Hyper à partir de `$940000` | OUTILS §1.4 |
| `$D40000 + $40000·k` | blocs des persos MAX convertis | §144, [CONV-MAX](../rapports/CONV-MAX.md) |
| `0xE70000` (adresse d'exécution PS2, pas 68K) | bloc de données de la redirection des voix d'Hyper (`HSFA_SON_DONNEES`) | §145 |
| `$F00000-` | variables propres au portage (`PORT_RAM`) | OUTILS §1.4 |

## 3. Image 68K produite

| Adresse | Contenu |
|---|---|
| `$000900` | amorçage (`LEA $FF8000,A5`, reset, init, ordonnanceur) |
| `$000A00-$000A7F` | une boucle `BRA.S *` par vecteur d'exception : signature d'une faute pour `diag.py` |
| `$000B00-$000FFF` | noyau de tâches |
| `$001000-` | code traduit |
| `$3C0000-$3DFFFF` | table de hachage adresse de code PS2 → 68K |
| `$3E0000-$3FEFFF` | débuts de fonction (adresse PS2, adresse 68K) |
| `$660000-$6637FF` | piles des 16 tâches |
| `$6638F0` | `EXCMARK` : PC d'un talon d'exception interrompu (lu par `diag.py`, `tournee.lua`) |

Les adresses du code traduit **bougent à chaque reconstruction** : relire `carte_image.txt` avant tout point d'arrêt.

## 4. MIPS (module PS2)

- Base d'exécution `0x1F0000` : va (adresse dans le fichier) = adresse d'exécution − `0x1F0000`.
- Banc de registres du recompilateur dans le scratchpad, `0x70001100-0x70001158` ([memoire-cps2](../architecture/memoire-cps2.md) §4).
- Liste d'objets PS2 dans le scratchpad (`0x70002000`), pas en RAM EE (§85).
