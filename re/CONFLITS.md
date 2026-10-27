# Conflits de zones connus (2026-10-17, mis à jour le 2026-10-24)

Liste brute à jour : `python3 re/outils/zones.py --verifie` (lit `re/allocations.tsv`). Ce fichier donne, pour chaque
conflit, son **sens**, son **responsable** et la **décision**. Quand un conflit est réglé : corriger
`allocations.tsv`, relancer `zones.py --verifie`, puis mettre à jour ou retirer la ligne ici.

| # | cible | zones en conflit | gravité | responsable | décision / action |
|---|---|---|---|---|---|
| 1 | `ext_ro9a` | greffe, 2ᵉ fenêtre réservée `$C30000-$C83FFF` / bloc son d'Hyper `$C2C200-$C30EFF` (utilisé) | **réglé** (2026-10-17) | greffe (voie B) | fenêtre `$C30000` abandonnée : la 2ᵉ fenêtre est `$C38000-$C83FFF`, au-dessus de la fin réelle d'`ext_940000` + son ; une assertion de `mame_test.py` le vérifie (`GREFFE-ETAPE4.md` §8.1). Réservation `$C30000` retirée d'`allocations.tsv`, lignes de l'étape 4 versées (2026-10-24) |
| 2 | `exec_ro9a` | talon de la greffe `$BFFF00-$BFFF04` dans la plage d'exécution du module Hyper `$B80000-$BFFFFF` | **réglé** (2026-10-17) | greffe | voulu : adresses PS2 de la RAM d'Hyper (+`$7FF00`) que `HWREG` détourne vers le registre `$804200` ; jamais lues ni écrites en mémoire, aucune instruction de ro5 / ro9 n'accède à +`$7FF00..$7FF05` (`GREFFE-ETAPE4.md` §8.3). La ligne d'`allocations.tsv` le dit (« s'excluent ») |
| 3 | `ext_ro9a` | bloc de données de la greffe `$D10000-$EDF427` (+ réserve `$DD0000`) / plan des décors d'Upper dans Hyper `$D10000-$EFFFFF` et `$BD0000-$C83FFF` | plan à refaire | futur chantier « décors d'Upper dans Hyper » | replanifier les décors après la greffe (zone hors `$F00000` : RAM du portage) |
| 4 | `ext_ro5` | MAX dans Upper `$E00000-$EC5B3B` (utilisé) / plan des décors d'Upper `$E00000-$EFFFFF` (réservé) | plan à refaire | futur chantier décors | replanifier les décors ; les zones MAX restent |
| 5 | `ext_ro3` | décor SFA2 `$C80000-$C8F7CD` / décors 16:9 `$C80000-$CE961F` | deux essais incompatibles | futur chantier décors (fusion SFA2 + 16:9) | répartir les deux injections dans un plan commun avant de les combiner |
| 6 | `gfx_rom_ro3`, `plans_ro3_s1/s2/s3` | décor SFA2 / décors 16:9 : même zone `$3000000` de la ROM graphique et mêmes codes de tuiles libres des plans | idem | idem | idem |
| 7 | `ext_ro3` | décor SFA2 `$B00000-$B69F3F` / ancien banc MAX de SFA3 `$B00000-$BFFFFF` (réservé, en pause) | faible | décors | le banc MAX de SFA3 est abandonné (MAX va dans Upper) : libérer la réserve si confirmé |
| 8 | `image68k_ro3` | trampoline du décor SFA2 `$000C40-$000C4F` dans la disposition commune du traducteur `$000B00-$000FFF` | à vérifier | décors | vérifier que `$C40` est libre dans la disposition commune ; sinon déplacer |
| 9 | `sons` | voix MAX d'Ingrid en page `$05` (`$051A-$051F`, `$0533-$0536`, `$057E-$057F`, `$05B9-$05BF`, `$05F9-$05FD`) / plage `$0500-$06FF` d'Upper | à vérifier | intégration MAX | vérifier qu'aucune commande d'Upper ne vise ces numéros (voix MAX v2, `VOIX-MAX.md`) ; la plage d'Upper est peut-être déclarée trop large |
| 10 | `sons` | `$0540-$055F` d'Hyper dans `$0500-$06FF` d'Upper | information | — | jeux différents : pas un conflit réel (à préciser dans `allocations.tsv`) |

État au 2026-10-24, après le report des n° 1 et 2 : `zones.py --verifie` passe de 30 à 27 conflits ; `verifie.py` : 0
erreur. Les n° 1 et 2 restent dans le tableau pour mémoire ; ils sont à retirer à la prochaine remise à plat.

Pièges associés (mises en garde de `quoi.py`) : 11 zones dites « libres » de ro9a sont dans la table des tâches ;
`0xE70000` (bloc de données du son d'Hyper) est une adresse d'exécution PS2, pas 68K.

## Ajouts du 2026-10-18 (fusion des re_ajouts)

| zones | gravité | décision |
|---|---|---|
| ext_ro9a `$C38000-$C83FFF` et `$D0C000-$EFFFFF` (greffe, utilisé) contre décors d'Upper dans Hyper (réservé) | à replanifier | même cas que les décors futurs de ro9a : le plan GREFFE-DECORS sera recalé au chantier des décors |
| ram68k `$FF7F00-$FF7F77` (table de transparence MAX) dans `$FF0000-$FFFFFF` (disposition commune du traducteur) | aucune | trou de RAM mesuré libre (jamais non nul sur 2 VERSUS de 12 000 images et une partie Arcade ; aucun accès A5 entre `$C3AA` et `$FFFF` dans Upper) |

## Décisions du 2026-10-21 (D1 à D3, voir `docs/rapports/POINT-ETAPE-2026-10-21.md` §3)

Prises au nom de l'utilisateur, à appliquer par les sessions MAX et greffe. Ensuite : corriger `allocations.tsv`,
relancer `zones.py --verifie`, puis retirer ces lignes.

| # | zones | décision | à faire par |
|---|---|---|---|
| D1 | ids MAX dans Hyper : `$26-$29` réservés (`allocations.tsv:210-213`) contre numéros d'Upper `$26`, `$27`, `$2D`, `$2E` | **Hyper : Eagle `$26`, Maki `$27`, Yun `$28`, Ingrid `$29`. Upper garde `$26`, `$27`, `$2D`, `$2E`.** Pourquoi : seules les 4 cases « ? » de la grille d'Hyper (`0x5C5650`) visent `$26-$29`, et la recette `BLOC-HYPER` §4 est prouvée pour ces index. Dans Hyper, `$28` et `$29` ne sont pas des pseudo-ID. `$2D`/`$2E` y déborderaient encore plus loin de la grille des versions (38 lignes, débordement vers la grille Start `0x5C5420`). Dans Upper, `$28`/`$29` sont des pseudo-ID (table des musiques). `$2A-$2F` restent libres dans Hyper | session MAX : une table de correspondance unique « id Upper → id Hyper » dans la conversion vers Hyper, appliquée partout où un id apparaît (tables par id, constantes du code MAX, sons et voix, propriétaire de banque) ; écraser le bloc du perso `$1E` que les 3 tables d'Hyper ont en `$27` |
| D2 | ram68k_ro9a `$FF7F00` : drapeau « partie Arcade » de la greffe (`allocations.tsv:146`) contre table de transparence MAX `$FF7F00-$FF7F77` et variable `$FF7F84-$FF7F87` (`:347`, `:353`, Upper) | **La greffe déplace son drapeau en `$FF7E00` (`$FE00(A5)`). MAX garde `$FF7F00-$FF7FFF` dans les deux jeux.** Partage de la zone A5 libre d'Hyper `$FF43BE-$FF7FFF` : relogés de la greffe vers le haut depuis `$FF43BE` (fin actuelle `$FF4CA2`) jusqu'à `$FF7DFF` au plus ; variables fixes de la greffe `$FF7E00-$FF7EFF` ; MAX `$FF7F00-$FF7FFF`. Pourquoi : un octet seul à déplacer, contre une table que le code MAX lit dans les deux jeux | session greffe : `depart_arcade` et l'effacement en scène C ; mettre `allocations.tsv:146` à jour et y réserver `$FF7F00-$FF7FFF` pour MAX |
| D3 | image68k_ro9a `$3A0000-$3BFFFF` : tables d'animation natives d'Upper posées par la greffe (`$37DF00-$3BDB4F`, `allocations.tsv:42`) contre code MAX (`$3A0000-$3BFFFF` dans Upper, `:20-22`, `:354`) | **Le code MAX garde `$3A0000-$3BFFFF` dans ro9a comme dans Upper. Les tables natives (des données) descendent de `$20000`**, par le même moyen que `MAX=1` dans Upper (« le plafond des données est abaissé d'autant », `allocations.tsv:20`), le surplus partant dans le bloc externe `$940000`. Pourquoi : la ROM programme est la seule zone exécutable, alors que les données peuvent sortir | session greffe : vérifier qu'il reste `$20000` o dans le bloc externe de ro9a ; à défaut, données vers les trous de la carte (patch 0009), jamais le code MAX |
