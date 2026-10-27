# Transition du « gros A » : texte « STREET FIGHTER ALPHA 3 » qui défile mal (SFA3, Upper, Hyper)

Agent `agent_bandeau_A`, 2026-10-11. Tout est dans `<workspace>/work/agent_bandeau_A/`. Le traducteur partagé
et les dossiers de ROM partagés n'ont pas été modifiés.

- Copie du traducteur : `untranspile/`.
- ROM figées : `roms_ref/` (arcade sfa3ud), `roms_tr3/` (traduction SFA3 du 10 octobre).
- Constructions : `mame3*/`, `mame_ro5*/`, `mame_ro9*/` (suffixe `_old` = `FLUXEA=0`).
- MAME en `nice -n 19`, `-nvram_directory` / `-cfg_directory` temporaires à chaque lancement, jamais `-state`.

## 0. En bref

- **Symptôme.** Pendant le balayage vert du gros A (avant le combat, et entre l'écran de victoire et le combat
  suivant), les trois lignes « STREET / FIGHTER / ALPHA3 » traversent l'écran à toute vitesse, par-dessus l'écran
  VS : ligne 1 vers la droite à 72 px/image, ligne 2 vers la gauche à 112 px/image, ligne 3 vers la droite à
  152 px/image, avec retour au bord à chaque passage.
  - Sur l'arcade, ces lignes ne bougent pas. Elles restent hors de l'écran (X = $2D8, $1C0, $2D0) jusqu'à
    l'éclair blanc, puis apparaissent fixes au centre.
  - La suite, texte fixe puis sortie, était déjà juste.
  - Le défaut touche les **trois jeux** (même code, deux copies par module).
- **Ce n'est ni un plan ni la table de défilement par ligne.** Le texte est fait d'**objets** (sprites) : masquer
  scroll1, scroll2 ou scroll3 ne l'enlève pas. Les registres CPS-A et la table `$22540` / `0xF7328` sont hors de
  cause.
- **Cause.** C'est un flux d'octets `(A3)+` mal traduit à l'initialisation des 6 sous-objets de la tâche.
  - Arcade `$337EC` : `MOVE.B (A3)+,$E(A4) ; MOVE.B (A3)+,$F(A4)` (sens, puis vitesse).
  - Traduction : `ADDQ.W #1,A3 ; MOVE.B -2(A3),$E(A4)`. Le déplacement -2 n'est juste que si A3 est impair. Or le
    1er octet est à une adresse paire : la vitesse prend l'octet bas du Y précédent ($48, $70, $98) au lieu de 0.
  - `byte_streams` (HANDOFF §65) ne corrigeait que la forme `MOVE.B -2(An),Dm` / `MOVE.B Dm,-2(An)`. Les formes
    mémoire → mémoire et les autres opérations octet (CMP, ADD, TST, CMPI, copie `(A3)+ → (A2)+`) passaient.
- **Correctif du traducteur** : passe `byte_streams_ea` (interrupteur `FLUXEA`, `FLUXEA=0` = ancien comportement).
  - Elle calcule l'adresse exacte à l'exécution (bascule du bit 0 de An, comme `byte_streams`) et garde les
    drapeaux de l'instruction (sauvegarde de SR).
  - 16 sites dans SFA3, 16 dans Upper, 12 dans Hyper.
  - Diff : `fluxea.diff`.
- **Validation**
  - Les positions des 6 sous-objets sont **identiques à l'arcade image par image** sur les 3 transitions d'une
    partie SFA3 (66 + 140 + 140 images, 0 écart ; avant le correctif, tous les états différaient).
  - Captures conformes à l'arcade.
  - `nonreg` SFA3 : 3 × « aucune exception », **42 actions, 0 différentes**, 5 359 tours en 4 019 images (133,3 %).
  - Upper : non-régression verte (3 parties Arcade jusqu'à la fin).
  - Hyper : partie VERSUS sans exception.

## 1. Captures et écart (point 1)

Banc :
- SFA3 : MAME standard, `sfa3ud`, `tournee.lua` (J1 = Ryu) + `lua/trace_a.lua` (registres CPS-A/CPS-B par image)
  + `lua/tache.lua` (mots de la tâche `$FFDE00-$FFDE7F` par image) ;
- Upper et Hyper : fork `cps2f sfa3hx`.

Décalage arcade → traduction sur la 1re transition : +48 images (arcade 2426, traduction 2474).

| | arcade sfa3u | traduction avant | traduction après |
|---|---|---|---|
| balayage vert (≈ 23 images) | aucun texte | les 3 lignes défilent : X += $48, -$70, +$98 par image, modulo $400 | aucun texte |
| éclair blanc puis texte fixe (≈ 17 images) | X = $58 / $40 / $50 | idem | idem |
| sortie du texte | le texte disparaît 1 image après l'état $12 | 1 image plus tôt | 1 image plus tôt (voir §6) |

Preuves (PNG, `preuves/`) :
- `sfa3_avant_combat.png` : arcade / avant / après, images 28 à 75 de la transition ;
- `sfa3_apres_victoire.png` : transition écran de victoire → combat suivant ;
- `upper_avant_combat.png` : Upper avant / après ;
- `hyper_versus.png` : Hyper (VERSUS) avant / après.

Registres :
- Pendant le balayage, CPS-A est identique sur l'arcade et la traduction (`ffc0 0000 ff40 0000 0000 0000`).
- Contrôle des plans : `1b0e` sur les deux.
- Pendant le texte fixe, deux écarts sans rapport avec le défaut :
  - scroll1 X : `$0008` sur l'arcade, `$0180` dans la traduction ;
  - scroll3 Y et ordre des plans : `ff10 / 2d0e` sur l'arcade, `0700 / 390e` dans la traduction.

  Ils sont sans effet visible ici (captures identiques sur ces images), mais sont notés pour mémoire.
- Masquer chaque plan tour à tour (`lua/couches.lua`, prise d'écriture sur `$804166`) laisse le texte en place :
  ce sont des objets.

## 2. Routine arcade et équivalents (point 2)

**Tâche de transition**, arcade `$33780-$33FE8`. Une instance est en `A6 = $FFDE00`. Ses 6 sous-objets sont en
`$20(A6) + $10·i` :
- `(A4)` : actif ;
- `$1` : 1 = pas de bouclage ;
- `$2` / `$4` : X / Y ;
- `$E` : sens (signe) ;
- `$F` : vitesse.

- **Initialisation**, `$337D0-$33812`, table `$33F66` de 6 entrées (X.w, Y.w, sens.b, vitesse.b, anim.w) :
  - `40,300` `C0,100` `140,300` : pièces vertes du balayage ;
  - `2D8,48` `1C0,70` `2D0,98` : STREET / FIGHTER / ALPHA3, toutes à vitesse 0.
  - Variante à 5 sous-objets : `$33C14`, table `$33F96`.
- **Mouvement**, `$33916` (et `$33D10`) :
  - sous-objets 0-2 : Y += ±vitesse, bouclage sur $F0 si `$1 = 0` ;
  - sous-objets 3-5 : X += ±vitesse, bouclage sur $40-$1D0 si `$1 = 0` ;
  - puis `ANDI.W #$3FF`.
- **Placement final** du texte : `$33B6A`, table `$33FBE` : X = $58, $40, $50.

| | arcade | MIPS (fichier) | 68K traduit (ROM du 10/10 → corrigée) |
|---|---|---|---|
| SFA3, copie 1 | `$337EC` | `0x937FC-0x9383C` | `$123F2` → `$1243A` / `$12458` |
| SFA3, copie 2 | `$33C30` | `0x955A4` / `0x955C8` | `$1290A` → `$1297E` / `$1299C` |
| Upper | — | `0xCFF6C` / `0xCFF90`, `0xD1E54` / `0xD1E78` | `$1B64E` / `$1B66C`, `$1BB92` / `$1BBB0` |
| Hyper | — | `0x3A35C` / `0x3A380`, `0x3C244` / `0x3C268` | `$3ECE` / `$3EEC`, `$4410` / `$442E` |

MIPS (SFA3 `0x937FC`) : `addiu a3,a0,1 ; lb v1,0(a0) ; sb v1,15(A4)`, puis `addiu ; lb 0(a0) ; sb 14(A4)`.
- L'octet PS2 `p` est l'octet 68K `p^1`. Il faut donc lire 68K `T+1` puis `T`, où `T` (pair) est l'adresse du
  couple qui suit X et Y.
- La traduction lisait `T-1` puis `T` : `ADDQ.W #1,A3 ; MOVE.B -2(A3),…` deux fois.
- Effet dans le format de la traduction (vitesse en 68K `$E`, sens en 68K `$F`) :
  - le sens est juste ;
  - la vitesse prend l'octet bas de Y : `$48`, `$70`, `$98` au lieu de 0.

Pistes du sujet écartées :
- accumulateurs, longs échangés, table par ligne `$22540` / `0xF7328` / `0xF72D8` (réécrite à la main §104, active
  en combat seulement) ;
- arithmétique 16/32 bits ;
- CMP perdu.

C'est une variante « mémoire → mémoire » de l'**octet XOR 1** dans un flux `(An)+`.

## 3. Correctif (point 3)

`translate.py`, nouvelle passe `byte_streams_ea(out, br_targets)`, appliquée en mode `cps2` après `byte_streams` /
`byte_streams_pre` / `byte_index_exact` / `byte_after_adda`. `FLUXEA=0` rend l'ancien comportement.

Une instruction est traitée si les quatre conditions suivantes sont réunies :
- elle opère sur un octet ;
- un de ses EA vaut `-2(An)` ;
- elle est précédée de `ADDQ.W #1,An` (un ou deux, pour la copie `(A3)+ → (A2)+`) ;
- elle n'est pas cible de branchement.

Elle est alors réécrite ainsi :
```
(bascule bit 0 de An) ; <instr> avec (An) ; MOVE SR,-(SP) ; (bascule) ; MOVE (SP)+,CCR ; ADDQ.L #1,An
```
avec, pour la bascule : `MOVE.L An,-(SP) ; EORI.B #1,3(SP) ; MOVEA.L (SP)+,An`.

Formes reconnues :
- `MOVE.B` (source, destination ou les deux) ;
- `ORI`/`ANDI`/`SUBI`/`ADDI`/`EORI`/`CMPI.B #imm` ;
- `TST`/`CLR`/`NEG`/`NOT.B` ;
- `OR`/`SUB`/`CMP`/`EOR`/`AND`/`ADD.B`.

L'adresse est exacte quelle que soit la parité : les sites où An était impair gardent leur comportement.
`mame_test.py` affiche le compte : « flux d'octets (An)+ hors Dn a adresse exacte ».

Sites corrigés (adresses 68K de la nouvelle image ; MIPS entre parenthèses) :
- **SFA3** :
  - `ADD.B -2(A0),D0` ×2 (`0x59814`, `0x59BC4`) ;
  - `CMPI.B #$2E,-2(A0)` en boucle (`0x88F90`) ;
  - les 4 `MOVE.B` du gros A ;
  - `CMP.B -2(A0),D0` en boucle de recherche ×2 (`0xD74B8`, `0xD76C8`) ;
  - `TST.B -2(A0)` ×4 (`0x124F14`, `0x125328`, `0x125704`, `0x1B7894`) ;
  - `MOVE.B $A(A6),-2(A0)` (`0x1B8078`) et `MOVE.B -2(A1),$A(A6)` (`0x1B8AD8`) ;
  - copie `MOVE.B -2(A3),-2(A2)` (`0x1F1DC4`).
- **Upper** : les mêmes 16 sites (homologues).
- **Hyper** : 12 sites (gros A ×4, ADD ×2, copie, TST ×3, CMP ×2).

Les sites autres que le gros A lisaient eux aussi l'octet voisin quand An était pair. Ils sont corrigés par la même
règle, et la non-régression reste verte (§5). Leurs effets visibles n'ont pas été recherchés un par un.

Diffs livrés :
- `fluxea.diff` : `translate.py` + `mame_test.py`, s'applique sur `src/hsfa` (copie de travail scripts/untranspile) (vérifié par
  `patch --dry-run`) ;
- `diag_nvram.diff` (facultatif) : `diag.py` lance MAME avec `-nvram_directory` / `-cfg_directory` temporaires.
  Le `diag.py` partagé ne le fait pas.

## 4. Reproduction et empreintes

- `FLUXEA=0` reproduit exactement les ROM partagées :
  - SFA3 : `sz3ud.03c` md5 `568cef19…` ;
  - Upper ;
  - Hyper (avec `EXTRACT_MODULES` / `HSFA_SON_DONNEES` de `valide_tout.sh`).
- ROM corrigées : `mame3/roms_tr`, `mame_ro5/roms_ro5`, `mame_ro9/roms_ro9`.
- Comparaison des positions : `essais/tache_{ref6,old6,fix6}.txt` (SFA3), `tache5_*` (Upper), `tache9_*` (Hyper).

## 5. Validation

- **SFA3** (`outils/nonreg3.sh`, copie de `nonreg.sh` sur ma construction) :
  - « aucune exception sur 20000 images » ×2 ;
  - « aucune exception sur 60000 images » ;
  - **42 actions, 0 differentes** ;
  - 5 359 tours de jeu en 4 019 images (133,3 %), comme la référence.
- **Upper** (`outils/nonreg5.sh`, copie de `nonreg_ro5.sh`) : « aucune exception sur 20000 images » ; trois parties Arcade complètes au fork, chacune jusqu'à la fin (`fin=finie`) : Ryu (00) en 27 manches, Chun-Li (04) en 23, Akuma (02) en 33.
- **Hyper** (VERSUS, `tournee_hyper.lua`, 20 000 images) : « FIN 20000 », 1 sélection, 2 manches, aucune exception.
- **Positions**
  - SFA3 : 0 écart avec l'arcade sur les 3 transitions d'une partie.
  - Upper et Hyper : les textes restent immobiles pendant le balayage, comme sur l'arcade. Avant le correctif, ils
    avançaient de +$48, -$70 et +$98 par image.

## 6. Restes (hors de ce défaut)

- **Disparition du texte 1 image plus tôt** que sur l'arcade (déjà le cas avant le correctif). Probablement la
  latence des objets du banc : `banc_sprites.lua` écrit la liste dans les deux banques à la fois, alors que l'arcade
  affiche la liste de l'image précédente. Ce n'est pas un défaut du code traduit.
- **Pendant le texte fixe**, scroll1 X (`$80410C`), scroll3 Y et l'ordre des plans (CPS-B `$804166`) diffèrent de
  l'arcade, sans effet visible sur ces images. À regarder si un autre défaut d'affichage de la transition est
  signalé.
- **Écran de victoire de SFA3** (1re image de `sfa3_apres_victoire.png`) : la réplique et « PRESS START » sont
  absents de la capture de la traduction à cette image. Ce n'est pas étudié ici.
