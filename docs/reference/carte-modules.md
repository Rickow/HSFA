# Carte des modules de l'Anthology

Synthèse de [rapports/CARTE-MODULES.md](../rapports/CARTE-MODULES.md) (tous les modules) et des profils de
`src/hsfa/profils.py` (modules traités). Les modules sont extraits de `X_DATA.BIN` sous le nom `roN_usa_prog68k.bin`
(répertoire `decompressed/`) ; malgré ce nom, ils contiennent du **MIPS**.

## 1. Modules traités par HSFA

| Module | Jeu | Code 68K recompilé | Fin du code / des données (en-tête) | RAM PS2 | Pilote du cœur |
|---|---|---|---|---|---|
| `ro3` | Street Fighter Alpha 3 | `0x22B00` | `0x393C40` / `0x88C700` | `0x900000` | `sfa3hsfa` |
| `ro5` | SFA3 Upper | `0x22B00` | `0x41ACC0` / `0x9A0180` | `0xA00000` | `sfa3uhsfa` |
| `ro9` | Hyper Street Fighter Alpha | `0x22DE0` | `0x3BF140` / `0xB67200` | `0xB80000` | `sfa3hhsfa` |

Upper et Hyper sont la même machine que SFA3, décalée (§30) : 72 % des variables A5 d'Upper et 77 % de celles
d'Hyper sont celles de l'arcade SFA3. Hyper a été produit par une version plus récente du recompilateur (§52) et
emprunte des banques de sprites à SFA1 (e208-e220) et SFA2 (e229-e248) ainsi que les musiques ALPHA.

## 2. Autres modules (étudiés, non traduits)

| Module | Jeu | RAM 68K émulée | Recensement du traducteur | Accessible au menu US |
|---|---|---|---|---|
| `ro1` | Street Fighter Alpha (Zero) | `0x600000` | 98,2 % | oui |
| `ro2` | Street Fighter Zero 2 | `0x800000` | 98,7 % | non |
| `ro4` | Street Fighter Zero 2 Alpha | `0x800000` | 98,8 % | non |
| `ro6` | Street Fighter Zero 2 Dash (SFA2 Gold console, avec Cammy) | `0x800000` | 98,8 % | oui |
| `ro7` | Pocket Fighter / Super Gem Fighter Mini Mix | `0x660000` | 98,4 % | oui |
| `ro8` | Street Fighter Alpha 2 | `0x800000` | 98,8 % | oui |
| `b` | menu de l'Anthology (C natif) | — | — | — |

Pièges relevés (CARTE-MODULES §0.2) : `translate.ram_hi_of` donne une base de RAM fausse pour 5 modules sur 6 ; le
Z80 recompilé n'est pas toujours en tête du fichier (`CODE0 = 0x22B00` est en dur dans `mips.py`) — voir
`tools/carto-modules/zones.py`. Une fois corrigés, l'assemblage à blanc de ces modules n'a aucun non-résolu.

## 3. Groupes de `X_DATA.BIN`

Les entrées sont groupées par jeu, délimitées par les modules MWo3 ; `hsfa_build.py` vérifie l'empreinte de chaque
groupe utile (table complète : [BUILD](../rapports/BUILD.md) §1.1).

| Groupe | Entrées | Requis pour |
|---|---|---|
| `b` | e203-e205 | — |
| `ro1` | e206-e223 | Hyper (banques SFA1, voix SFA1 pour le rejeu) |
| `ro2` | e224-e252 | Hyper (banques SFA2, voix SFA2 pour le rejeu) |
| `ro3` | e253-e347 | SFA3, Upper (son), Hyper |
| `ro5` | e350-e525 | Upper, SFA3 (banques 391-412, 456-457), Hyper |
| `ro9` | e544-e552 | Hyper |

## 4. Ressources par jeu (extraits)

| | SFA3 | Upper | Hyper |
|---|---|---|---|
| banque commune (emplacement 0) | e254 | e351 | e545 |
| plans 32×32 | e312 | e525 | e548 |
| fichier de frames à adresse fixe | 289 (`$A04000`) | 390 (`$B04000`) | 547 (`$C84000`) |
| pointeur d'animation (`BANC_PTR_ANIM`) | `FF3E48` | `FF40BC` | `FF40BC` |
