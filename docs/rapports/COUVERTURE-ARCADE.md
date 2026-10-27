# Couverture ROM arcade SFA3 ↔ traduction (ro3) — et pistes pour compléter

> Rapport versé dans le dépôt le 2026-10-24 depuis `work/agent_couverture/COUVERTURE-ARCADE.md` (copie anonymisée ;
> texte d'origine inchangé). Les chemins `work/…` et `<workspace>/…` désignent des dossiers de travail, hors dépôt.
> Analyse statique du 2026-10-07 (avant les §132-§171) ; les chiffres de couverture datent de cette version du
> traducteur.

État au 2026-10-07. Tout est statique : aucun MAME lancé, aucun fichier partagé modifié. Les scripts et données sont dans `work/agent_couverture/`.

## 0. Réponse courte

**Non, tout n'est pas retranscrit, mais presque tout le jeu l'est.** Le code 68K d'arcade fait **515 Ko** (128 300 instructions). Il est découpé en 12 857 unités : fonctions, gestionnaires d'aiguillage, entrées de tables et blocs.

| statut final | octets | part | sens |
|---|---|---|---|
| présente | 469 748 | **91,1 %** | homologue trouvé : alignement, site d'appel, vote ou sac d'atomes (§2) |
| partielle | 4 198 | 0,8 % | présente, mais réécrite par le portage (champs d'objet relogés, en-têtes changés) |
| probable | 18 874 | 3,7 % | ressemblance entre 0,6 et 0,8. Surtout du code de persos aux champs relogés (`$6C000`–`$72FFF`) |
| indécidable | 7 178 | 1,4 % | unités de 1 à 3 instructions (`JMP`, `RTS`, amorces) |
| **absente** | **15 370** | **3,0 %** | aucun homologue |

- **Ce qui manque est du code « système » d'arcade.** Les 15 zones identifiées au §3 totalisent 19,7 Ko de code arcade. **11,3 Ko** y sont absents, et seulement 2,5 Ko sûrement présents. On y trouve :
  - le **mode test** (8 Ko) ;
  - l'**EEPROM** (la config d'arcade) ;
  - la **RAM tenue** `$66xxxx` (statistiques et records) ;
  - le **monnayeur**, la comptabilité et l'affichage des crédits ;
  - les **tests mémoire et l'attente du Z80** au reset ;
  - les **écrans de démarrage** ;
  - un afficheur de **débogage** ;
  - le **noyau** de tâches (déjà reconstruit au §61).
- Hors de ces zones, il reste 7,8 Ko d'« absentes ou partielles », éparpillées. Ce résidu est une borne haute : il contient des faux négatifs de la mise en correspondance et quelques données décodées à tort (ex. `$B8B22`).
- **Fonctions appelées ou pointées** (2 202 unités) :
  - 1 871 présentes, 7 partielles, 118 probables, 83 indécidables ;
  - **123 absentes** (7,6 Ko), presque toutes dans les zones système.
- **Contrôles** :
  - les **45/45** fonctions de la rosette MAX (`api_arcade_psp.json`) sont « présentes » ;
  - **100/124** fonctions nommées de la table des symboles le sont. Les 24 autres sont le noyau, l'IRQ2, la tâche principale, et 1 erreur de la table (§7).
- **Sens inverse** : ro3 compte 3 167 fonctions MIPS (cibles de `jal`) :
  - **2 892** ont un homologue arcade ;
  - **43** sont natives (44 Ko MIPS) ;
  - **232** n'ont pas d'homologue (65 Ko MIPS). Le sac inverse les sépare en 20 homologues probables, 14 incertaines et **197 propres au portage** (46 Ko MIPS). Ces 197 se répartissent ainsi : 53 dans la zone `0x38xxxx`–`0x39xxxx` (menus et options, 22 Ko), 120 éparpillées (23 Ko), 11 dans `0x05xxxx`.

## 1. Méthode (et ce qu'elle vaut)

### 1.1 Inventaire du code arcade (`arcade_reach.py`, `dec68k.py`)

C'est un parcours récursif de `sfa3ud_prog.bin`. Il part de deux sources :
- les vecteurs ;
- en option, les adresses arcade de l'alignement de `agent_symboles`.

Il suit :
- `Bcc`, `BRA`, `BSR`, `DBcc`, `JMP` et `JSR` absolus ou relatifs au PC ;
- les aiguillages Capcom `MOVE.W T(PC,Dn) ; JMP/JSR T(PC,Dm)` ;
- les pointeurs de code : `LEA`/`PEA`/`MOVE.L #` vers du code plausible, et tables de longs indexées au PC ;
- les tables de longs ≥ 3 dans les données.

Trois variantes ont été calculées :

| variante | instructions |
|---|---|
| sans les graines d'alignement (« pur ») | 126 029 |
| sans les tables de données (« sûr ») | 121 583 |
| union | 128 300 |

**Code non atteint** (`trous.py`) : les trous de `$400`–`$C0000` qui ressemblent à du code ne font que **1,8 Ko**. L'inventaire est donc quasi complet. Au-delà de `$BDBD6`, la ROM ne contient que des données.

### 1.2 Mise en correspondance, de la plus sûre à la plus floue

1. **Alignement** instruction par instruction (`agent_symboles/_cache/alignement.pkl`) : 86 757 paires. Une unité est « présente » si au moins 50 % de ses instructions sont alignées.
2. **Sites d'appel** : un `JSR`/`BSR` arcade aligné sur un `JSR` traduit relie leurs deux cibles. Cela donne **2 563 cibles** reliées (`cibles_appel.pkl`). C'est ce qui rattrape les amorces de 2 à 5 instructions (ex. `$2A758`).
3. **Vote par 3-grammes**, normalisé pour la recette cps2 (`vote_robuste.py`) :
   - les `SWAP` et empilements temporaires sont ignorés ;
   - les longs immédiats pré-échangés sont remis à l'endroit ;
   - `MOVE #0` est traité comme `CLR` ;
   - la relocalisation A5 et l'inversion XOR 1 des octets sont appliquées.
4. **Sac d'atomes** (`sac.py`) : multi-ensemble des déplacements `d(An)`, des immédiats, des cibles d'appel reliées et des opérations rares, cherché dans une fenêtre de l'image traduite. **Calibrage** sur 400 unités alignées :

| seuil | rappel | faux positifs (unités mutées, déplacements +2) |
|---|---|---|
| 0,6 | 96 % | 33 % |
| 0,8 | 75 % | 6 % |

   « Présente » est attribué à partir de 0,8 (ou de 0,6 avec un vote positif), « probable » à partir de 0,6.

⚠ **Limites**
- « probable » dans les zones système (2,7 Ko) relève surtout du faux positif : ce sont de petites unités qui retombent par hasard sur un sac voisin.
- « absente » hors des zones système peut être un faux négatif. Exemple : le code d'objet dont le portage a changé l'en-tête (`MOVE.L #$01002610,(A4)` arcade devient `#$00011026`) et relogé des champs (`+$48` → `+$4A`, `+$4C` → `+$4E`). C'est ce que recouvre « partielle ».

## 2. Fichiers produits

| fichier | contenu |
|---|---|
| `unites_arcade.json` | une entrée par unité arcade : `debut`, `fin`, `sortes`, `n`, `octets`, `alignees`, `statut` (passe 1), `statut2` (vote), `sac`, `final`, adresses `trad`/`mips` de l'homologue, appelants, accès matériels, `upper_alignees` |
| `absentes_arcade.tsv` | toutes les unités absentes, partielles, probables et indécidables, avec la zone et son rôle |
| `zones_systeme.json` | les 15 zones système, leur bilan en octets, leurs appels sortants et leurs variables A5 |
| `composantes_absentes.json` | les absentes regroupées par graphe d'appel et contiguïté, avec les accès matériels |
| `sites_vers_absentes.json` | les sites présents qui appellent une absente |
| `fonctions_mips_sans_arcade.json` | les 275 fonctions MIPS natives ou sans arcade, leur zone, le sac inverse et leur classement |
| `raccords_arcade.json`, `raccords.txt` | les 83 sites natifs (`hooks_fork_ro3.json`) et les fonctions C du §132, avec l'instruction arcade au même endroit |
| `trous_arcade.json` | les zones non atteintes, avec leur score « ressemble à du code » |
| `upper_alignement.pkl`, `upper_ecarts_vs_arcade.json` | l'alignement de l'image d'**Upper** sur la ROM arcade de SFA3 (§6) |
| scripts | `dec68k.py`, `arcade_reach.py`, `arc_texte.py`, `couverture.py`, `vote_robuste.py`, `sac.py`, `absentes.py`, `zones.py`, `inverse.py`, `sac_inverse.py`, `site_arcade.py` (va MIPS → instruction arcade), `raccords.py`, `upper_align.py`, `upper_trous.py`, `montre.py` (désassemblage arcade annoté : `=` pour une instruction alignée), `chaines.py` |

Ordre de reconstruction : `arcade_reach.py` → `arc_texte.py` → `couverture.py` → `vote_robuste.py` → `sac.py 0.8` → `absentes.py` → `zones.py` → `inverse.py` → `sac_inverse.py`. Le tout prend environ 2 minutes.

## 3. Ce qui manque : les zones système de l'arcade

| zone arcade | taille | absente | présente | rôle (lu dans le code) |
|---|---|---|---|---|
| `$0400`–`$062A` | 496 | 260 | 70 | **Débogage** : affichage hexadécimal de pointeurs ou variables en vidéo (`$92Dxxx`) |
| `$091E`–`$0F7A` | 1 260 | 222 (+202 part.) | 274 | **Reset** : attente du Z80 (`CMPI.B #$77,$619FFF`), tests de la RAM QSound et de la RAM de travail sans pile (retours par `LEA x(PC),A4/A5/A6`), init EEPROM `$804040` |
| `$0F7A`–`$1110` | 496 | 78 (+126) | 228 | Démarrage à chaud ou à froid (signature `$1C62F5A8` de RAM tenue, lecture `$804030`) |
| `$1110`–`$1198` | 114 | 44 | 20 | Ordonnanceur. Remplacé par des fils PS2, déjà reconstruit (§61) |
| `$1198`–`$12CE` | 346 | 30 | 88 | IRQ2 (portée en `0x2F2B0`) |
| `$12CE`–`$1414` | 340 | 68 | 90 | TRAP #0–#7 du noyau |
| `$1414`–`$15A2` | 456 | 0 | 376 | Lecture des entrées : présente |
| `$15A2`–`$1B8E` | 1 648 | **1 108** | 256 | **Monnayeur et comptabilité** : compteurs de pièces et de service (`$534`/`$934(A5)`), temps de jeu (`$1F6(A5)`, seuil `$4F1A00`), verrouillage des monnayeurs, décodage des réglages (`$61`–`$67(A5)`) |
| `$1B8E`–`$2578` | 2 394 | **1 458** | 220 | **EEPROM série** `$804040` : lecture et écriture de la config d'arcade, « EEPROM ERROR » |
| `$2578`–`$2F66` | 2 528 | **1 548** | 16 | **RAM tenue** `$661000`–`$663FFF` : copies triples, vérification et réparation (statistiques et records) |
| `$3EF6`–`$4036` | 264 | 98 | 116 | Tâche principale, modes 2 à 6 : **écrans de démarrage** (`$B4` images chacun, région `$90(A5)`, passage par Start) |
| `$7BDA`–`$7D9E` | 452 | 356 (+96) | 0 | **Crédits par joueur** : « INSERT COIN » et continuer (structure `$70(A5)`, gratuit `$9C`/`$9D`/`$9E`) |
| `$D800`–`$11000` | 8 186 | **5 426** | 700 | **MODE TEST**, entrée `$DD7E` (`$82(A5)=1`, boucle de modes propre). On y trouve CONFIGURATION (« MODIFY SETTING » `$F1FC`), les tests de son QSound (`$619E81`…), d'entrées et d'écran, palettes `$10CC2` |
| `$16C12`–`$16CEE` | 220 | 220 | 0 | Tâche qui surveille l'interrupteur TEST : tue les 16 tâches et passe en mode test |
| `$B4BE4`–`$B4DE0` | 508 | 418 | 78 | **HUD des crédits** (« CREDITS: n ») |

Lecture : le portage a remplacé, par le menu console et les fils PS2, tout ce qui touche au matériel d'arcade sans équivalent sur PS2 (pièces, EEPROM, RAM tenue, interrupteur TEST, attente du Z80) et au mode test. **Le gameplay, l'attraction, les fins, le son en jeu et les entrées sont entiers.**

**Où le menu console s'est greffé** (`raccords.txt`) :
- l'aiguillage des modes du portage (`0x485A4`) et la tâche OPTION (`0x383E20`) prennent la place de la logique Start/crédits de l'attraction (arcade `$4462`–`$44A0` et `$47A4`–`$47FA`, toutes deux « partielles ») ;
- l'appel EXIT (`-25380` = `0x1CAC80`) est au site arcade `$47CE`.

## 4. Raccordements natifs et fonctions C du §132 : l'équivalent arcade, site par site

| natif ou C | sites | à cet endroit dans l'arcade | piste | faisabilité |
|---|---|---|---|---|
| `0x381900` remappage des boutons | `$2773A`, `$2774A` | `MOVE.W $51A(A5),D0 ; ANDI.W #$F70F,D0`, **consécutifs** : rien entre les deux | supprimer l'appel (identité) | triviale, déjà sans effet (§132) |
| `0x393B20` (5 sites : attente ou test du portage) | `$4332` (`BNE ; ADDQ.W #2,$0(A5)`), `$1E496`, `$1F38A`, `$8FBE`, `$A8E0` | rien : l'arcade enchaîne directement. Le natif est un test du portage dont le résultat est « supposé nul » | rendre le chemin arcade (supprimer l'appel) | triviale |
| `0x383700`/`0x3837D0` chargeurs X_DATA | `$42A0`–`$42CC`, `$8B7C` ; perso via `$132(A5)` | aucun chargement : les tables sont en ROM. Exemples : `MOVEA.L #$DCB12,A0` (`$2A722`), `#$C955A` (`$30A44`). Le bloc `$CC900`–`$DC900` est copié tel quel dans ro3 | à vérifier : remplacer `assets_natifs` par les tables de la ROM arcade | moyenne (hypothèse à confirmer) |
| `-25380` EXIT, `-d75a0`, `-9aca0` | `$47CE`, `$484E`, `$4DEC` | logique Start, crédits et démo de l'attraction | sur CPS2, rendre la logique arcade d'attraction et de crédits (§3, zones `$15A2`/`$7BDA`) | moyenne |
| `-d60b8`/`-d6060` (setjmp/longjmp, 6 sites) | `$30A80`, `$30BBE`, `$321C0`, `$32212`, `$329A2` | un simple `BRA`/`BNE` vers une autre fonction (`$30BC8`, `$321C8`…) | déjà traité par des talons (§75). Le paradigme arcade serait un vrai `BRA` | déjà fait |
| `-24650` (`0x1CB9B0`) | `$1745E` → `$17462` | `MOVEQ #0,D0 ; RTS` puis la boucle de tâches | supprimer | triviale |
| moteur PS2 du noyau (`-e2790`, `-ecaf0`, `-ecb00`, `-eb8e0`, `-a4a60`…) | `$113A`–`$116E`, `$138C` | ordonnanceur et TRAP de Capcom `$1110`–`$1414` | **paradigme déjà appliqué** : `kernel68k.py` est calqué sur l'arcade (§60-61). On pourrait aller jusqu'au code arcade lui-même (840 o), adapté à la table des tâches du portage | faite / facultative |
| `0x2ED20` (chute `0x2F114`) | appelée par `0x2E7E0` (arcade `$1016`) | init portée et répartiteur : arcade `$F7A`–`$1184` | sans objet : remplacée par le noyau 68K | — |
| **§132** `0x388770` (chutes `0x3887B8`, `0x388800`), `0x389990` (`0x38A0CC`), `0x3925A0` (`0x3927E0`, `0x392A10`) | appelants `0x387940`, `0x388AB0`, `0x391A20` : tous dans la zone du portage | **aucun équivalent arcade.** Ce sont les écrans console (modes, OPTION) sur les variables `$886990`… L'analogue le plus proche est l'écran **CONFIGURATION du mode test** (`$F1FC`) | réécrire ces C en 68K, **ou** remplacer OPTION par le CONFIGURATION d'arcade (§5, P2) | moyenne à difficile ; impact faible (jamais atteintes par les sondes) |
| Upper `0x32694`, `0x4069E8`, `0x406A30`, `0x406D70`, `0x407E18`, `0x410C00`, `0x410E30` | — | **jumelles exactes** des précédentes : `0x4069A0` = ro3 `0x388770` (identique), `0x406CC0` = `0x388AB0` (0,89), `0x4109C0` = `0x3925A0` (structure), `0x322A0` = `0x2ED20`. `0x407990` n'a pas d'homologue | une seule réécriture sert aux deux modules (et sans doute à Hyper) | — |

Les **sites `0x38xxxx`–`0x39xxxx`** (menus du portage, 52 sites vers le moteur PS2) n'ont, par construction, aucun équivalent arcade.

## 5. Pistes classées (impact en jeu × facilité)

**P1 — Outil de « greffe 68K d'arcade »** (préalable à P2-P5). Le code qui manque est **déjà du 68000** : on peut le reprendre de la ROM et le réécrire en 68K « mode cps2 ».
- Ce que la réécriture doit faire :
  - octets en `d(An)` : XOR 1 ;
  - accès longs à la mémoire : `SWAP`, et longs immédiats pré-échangés ;
  - variables A5 : relocalisation par les 29 intervalles appris (`agent_symboles/_cache/reloc_a5.pkl`) ;
  - appels vers du code présent : adresses traduites (`cibles_appel.pkl` : 2 563 cibles, ou la colonne `trad` des unités alignées) ;
  - tables relatives au PC : hébergées comme dans `assemble.py`.
- **Vérité terrain massive** : les 86 757 paires de l'alignement permettent de valider la réécriture instruction par instruction. On réécrit l'instruction arcade, on la compare à l'instruction traduite alignée, et l'on doit obtenir l'identité.
- C'est la recette du traducteur, appliquée à une autre source. Le cas difficile est connu (octets via un registre d'adresse de parité inconnue, §97).
- Impact : rend possibles toutes les restitutions ci-dessous, sans écrire de 68K à la main.

**P2 — Démarrage arcade fidèle : attente du Z80 et tests au reset** (`$AF2`–`$B18`, `$C1E`–`$E16`, ~0,6 Ko).
- Le §102 note que l'intro part 2 images après le fondu, contre 37 sur l'arcade, et que le portage démarre « sans test de la RAM son ni commande `01 03` ».
- La boucle `CMPI.B #$77,$619FFF ; BNE` et les tests de la RAM QSound sont absents : c'est exactement ce morceau.
- Petit, autonome (sans pile, retours par registre) et à fort effet sur le calage son/intro. **Facile.**

**P3 — Mode test et CONFIGURATION d'arcade** (`$D800`–`$11000`, 8 Ko) avec l'**EEPROM** (`$1B8E`–`$2578`, 2,4 Ko).
- Sur le fork CPS2, l'EEPROM 93C46 existe (MAME l'émule). Restituer ces routines donne les vrais réglages d'arcade (difficulté, temps, sons, langue) au lieu du menu OPTION natif (§102).
- Cela supprime aussi le besoin de réécrire les C du §132 pour OPTION.
- Liens : 64 appels sortants, dont 23 déjà reliés à la traduction (les autres visent d'autres absentes système). 129 variables A5, dont la moitié haute n'est pas relogée.
- Impact moyen, facilité moyenne (avec P1).

**P4 — Monnayeur, crédits, HUD, comptabilité, RAM tenue** (`$15A2`–`$1B8E`, `$7BDA`–`$7D9E`, `$B4BE4`–`$B4DE0`, `$2578`–`$2F66`, `$16C12` ; ~5,4 Ko).
- Nécessaire pour une ROM qui se comporte comme une borne : pièces, « INSERT COIN », free play, bouton TEST.
- Le HUD des crédits (`$B4BE4`) et la tâche TEST (`$16C12`) ont tous leurs appels reliés : ce sont les greffes les plus simples.
- Impact élevé si l'objectif est une ROM « borne » (y compris un Upper ou un Hyper en borne). Moyen sinon.

**P5 — Écrans de démarrage** (tâche principale, modes 2 à 6, `$3F28`–`$3F80`, 264 o). Avertissement et région avant l'attraction. Petit, appels reliés. **Facile**, impact cosmétique.

**P6 — Supprimer les raccords sans fonction** : remappage `0x381900` (2 sites), `0x393B20` (5 sites), `-24650` (1 site). L'arcade montre qu'il n'y avait rien à cet endroit. **Triviale.** Gain : propreté et cadence, moins de talons.

**P7 — Tables d'animation depuis la ROM arcade plutôt que depuis X_DATA.BIN.** Hypothèse à vérifier : les fichiers 290–311 seraient les tables que l'arcade lit en ROM (`MOVEA.L #$DCB12`/`#$C955A`…). Si c'est le cas, le fork n'a plus besoin de `assets_natifs.py` pour SFA3. Facilité moyenne, impact technique.

**P8 — Fonctions C du §132** : pas d'équivalent arcade (écrans console). Les réécrire en 68K ne vaut la peine que si l'on garde les menus console. Elles sont communes à SFA3 et Upper : une réécriture sert aux deux.

## 6. Upper et Hyper : code commun et paradigmes réutilisables

**Alignement direct d'Upper sur la ROM arcade de SFA3** (`upper_align.py`, même méthode, relocalisation A5 apprise sur Upper) :
- **69 594 instructions traduites d'Upper sur 152 307 (45,7 %)** s'alignent sur l'arcade de SFA3. Pour SFA3 lui-même, c'est 53 %.
- Côté arcade, **355 Ko** d'unités (69 % du code) ont une trace directe dans Upper. 138 Ko sont présents dans SFA3 sans trace directe dans Upper : surtout le code des persos (`$40000`–`$6FFFF`), rééquilibré dans Upper.
- Relocalisation A5 d'Upper : mêmes intervalles que SFA3, plus `$B466`–`$B4E6` (+`$208`), `$B980`–`$BA12` (+`$204`) et `$C0C0` (−`$313E`).

⟹ **La ROM arcade de SFA3 est un « corrigé » partiel pour Upper**, pas seulement pour SFA3 (le §28 disait le contraire). Les outils de validation par alignement (`verify.py`, audits) peuvent tourner sur Upper pour sa moitié commune.

**Écarts Upper/arcade** (`upper_ecarts_vs_arcade.json`) :
- **1 999** instructions arcade sont traduites dans SFA3 mais absentes d'Upper, entre deux voisines alignées.
- 1 490 sont des formes de branchement (relaxation de l'assembleur) : du bruit.
- **509** ne sont pas des branchements. C'est à trier : décalages A5 propres à Upper non appris (ex. `$AC(A5)`), ou vraies pertes de traduction propres à Upper.
- La comparaison avec la traduction SFA3 au même point arcade (`trad_sfa3`) montre la forme attendue.

**Mêmes absences, mêmes greffes.** Le code système d'arcade (P2-P5) manque aussi dans Upper et Hyper (même portage), et les C du §132 y ont leurs jumelles. La moitié haute de A5 n'est pas relogée et les tables de tâches sont communes. Une greffe validée sur SFA3 se transpose donc à Upper avec la table de relocalisation ci-dessus.

**Hyper, mode ARCADE** (`PROJET-Hyper-Arcade.md`). L'enchaînement arcade (adversaire suivant, carte, fins) existe dans SFA3 et Upper, traduit et vérifié (32 et 40 fins). La filiation SFA3 → Upper → Hyper (§28 : Hyper partage 28,6 % de code identique avec Upper) fait des routines d'enchaînement d'Upper les candidates naturelles. Elles sont à apparier avec `carto_ro9` (non mesuré ici).

## 7. Corrections et remarques sur l'existant

1. **La zone ro3 `0x190000`–`0x1BFFFF` n'est pas « absente de la ROM »** (contrairement au §21) :
   - 127 de ses 177 fonctions s'alignent sur l'arcade `$A4FB0`–`$ABBFE` ;
   - le §21 s'appuyait probablement sur `sfa3_prog.bin`, dont `$0`–`$BFFFF` est faux ;
   - **c'est du code d'origine.**
2. **`scripts/untranspile/reach.py`** :
   - la lecture des tables d'aiguillage s'arrête après la 1re entrée (`off >= lim` avec `lim` = plus petite cible) ;
   - `rom_code.json` n'a donc que 46 instructions ;
   - le parcours corrigé atteint 126 029 instructions.
3. **`scripts/untranspile/m68k.decode_one`** se trompe de taille sur quatre cas :
   - `EXT.W`/`EXT.L` (pris pour `MOVEM` : 2 mots au lieu de 1) ;
   - `ADDA.W`/`SUBA.W`/`CMPA.W #imm` (immédiat compté en long) ;
   - `MOVE USP` (+1 mot) ;
   - `CHK.W #imm`.
   
   `translate.py` l'utilise dans des passes postérieures, sur des éléments à plusieurs instructions (`zero_disp_short`, `byte_index_exact`). Les 3 éléments `EXT.W D1 ; MOVE.W D1,d(An) ; MOVEM.L (SP)+,D1` de SFA3 (`$4B50A`, `$4B530`, `$4D1C0`) sont émis juste : le risque est latent, il n'y a pas de dégât constaté. Le décodeur corrigé est `agent_couverture/dec68k.py`.
4. **La table des symboles** donne `table_ptr_par_perso_index` en `$0F3DA0`, mais l'arcade n'y contient que `$FFFF`. C'est sans doute une adresse de l'image traduite de l'époque (§68).
5. Le code de persos `$6C000`–`$72FFF` (« probable » ou « partielle ») est bien présent. Le portage y a :
   - changé le format de l'en-tête d'objet (`#$01002610` → `#$00011026`) ;
   - relogé des champs (`+$48` → `+$4A`).
   
   Les audits qui comparent l'arcade et la traduction doivent connaître ces deux transformations.
