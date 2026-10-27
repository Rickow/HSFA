# Écran de victoire : réplique du vainqueur et « PRESS START » (SFA3, Upper, Hyper)

Agent `agent_victoire`, 2026-10-11. Tout est dans `<workspace>/work/agent_victoire/`. Le traducteur partagé, les
dossiers de ROM partagés et `max/` n'ont pas été modifiés.

## 0. En bref

**Le constat ne se reproduit pas comme un défaut de traduction.**

- **La réplique du vainqueur est bien affichée** dans SFA3 et dans Upper traduits (traducteur actuel, FLUXEA compris).
  - Elle apparaît 1 image plus tôt que sur l'arcade : image 17 au lieu de 18, à compter du début de l'écran.
  - Elle s'écrit au même rythme : 1 caractère toutes les 2 images, 4 images sur une espace.
  - Elle disparaît 1 image plus tôt : image 364 au lieu de 365.
  - Ce décalage constant de −1 image est la latence des objets du banc (`banc_sprites.lua`), déjà relevée par
    l'agent du bandeau. La réplique et « PRESS START » sont des **objets** (sprites) : aucune écriture dans les plans
    pendant la frappe.
- **« PRESS START » clignote** dans la traduction : 64 images affiché, puis 64 images éteint. Sur l'arcade, il reste
  fixe.
  - Ce clignotement est **voulu par le portage PS2**. La routine du message du côté J2 a été réécrite par
    l'Anthology, et la traduction la suit fidèlement (§3).
  - Une capture prise pendant une phase éteinte ne montre donc pas « PRESS START ».
- **La capture de l'agent du bandeau** (`sfa3_apres_victoire.png`, 1re colonne) date du début du balayage vert.
  - À ce moment, les textes sont déjà effacés sur les deux machines. L'arcade les efface à l'image 365, la
    traduction à l'image 364.
  - Les colonnes de cette planche étaient calées sur la 1re transition (+48 images), pas sur la fin de l'écran de
    victoire.
- **Hyper** n'a pas d'écran de victoire avec réplique.
  - En VERSUS, comme en ARCADE (curseur forcé), la fin de match passe directement à l'écran RESULT (scène `$E`).
  - C'est le comportement du portage : `ETATS-HYPER.md` §2.1-2.2 et HANDOFF §144 (« Hyper n'a pas de mode Arcade »).
- **Aucun correctif du traducteur n'est proposé**, faute de défaut de traduction. Il n'y a donc ni diff ni
  revalidation. La ROM de ma copie est identique à la ROM partagée : SFA3 `b62d489e…`, Upper `efde8593…`,
  Hyper `6a1cdd44…`. Une option « PRESS START fixe comme l'arcade » reste possible (§5), à décider.

## 1. Banc

| | arcade | SFA3 traduit | Upper traduit | Hyper traduit |
|---|---|---|---|---|
| machine | MAME `sfa3ud` (ROM de `agent_bandeau_A/roms_ref`) | MAME `sfa3ud` + `banc_*.lua` | fork `cps2f sfa3hx` | fork `cps2f sfa3hx` |
| scénario | `tournee.lua`, J1 = Ryu (PERSO 00) | idem | idem | `tournee_hyper.lua` (VERSUS) ; `tournee.lua` + `MODE=0` (ARCADE) |
| écran de victoire (2e combat gagné) | images 4716 → 5077 | 4521 → 4882 | 5064 → 5425 | — |

- Les trois écrans durent 361 images. L'image 0 est le passage `$FF800C = 6` après la fin du combat.
- L'adversaire n'est pas le même : arcade `$10`, SFA3 `$07`, Upper `$0C` (le hasard diffère). La réplique n'est donc
  pas la même, mais la routine est commune.
- Toutes les commandes MAME passent par `nice -n 19`, avec `-nvram_directory` / `-cfg_directory` temporaires et jamais
  `-state`.
- Lanceurs :
  - `outils/lance3.sh` (SFA3, ref|tr), `lance5.sh` (Upper), `lance9.sh` (Hyper) ;
  - répertoire courant = dossier de l'essai.
- Journaux Lua (`lua/`) :
  - `octets.lua` : octets par image ;
  - `slots.lua` : emplacements d'objets ;
  - `scr1.lua` : prises d'écriture avec PC ;
  - `dbg.lua` : commandes du débogueur, ici `trace` avec registres ;
  - `force.lua` : octets forcés.
- Mesures (`outils/mesure.py`) : pixels « vert texte » dans la zone de « PRESS START » (haut droite) et dans la zone de
  la réplique (bas), image par image.
- Planches : `outils/bandes.py`.

## 2. Mesures (point 1)

Image 0 = début de l'écran de victoire. Les fichiers `essais/*_mes.txt` donnent les valeurs image par image.

| | arcade sfa3u | SFA3 traduit | Upper traduit | écart |
|---|---|---|---|---|
| 1er caractère de la réplique | 18 | 17 | 17 | −1 (latence objets du banc) |
| fin de la frappe | 134 | 131 | 115 | même cadence (2 images/caractère) ; répliques de longueurs différentes |
| réplique effacée (fin d'écran) | 365 | 364 | 364 | −1 |
| « PRESS START » | fixe de 58 à 364 | 103-166, 231-294, 359-363 | 72-135, 200-263, 328-363 | clignotement 64/64 dans la traduction |
| début du balayage vert | 375 | 374 | — | −1 |

- Captures, `preuves/` :
  - `sfa3_victoire.png` : arcade / traduction, images 0 à 365 ;
  - `upper_victoire.png` ;
  - `sfa3_fin_victoire.png` : images 363-390, effacement puis balayage ;
  - `chronologie_textes.png` : présence des deux textes image par image.
- **1re apparition de « PRESS START »** : 58 sur l'arcade, 103 dans SFA3, 72 dans Upper.
  - L'écart ne vient pas de l'écran. Le message est recalculé tous les 64 images, quand l'octet `$80(A5)` du compteur
    d'images vérifie `& $3F = 0`. Ce compteur tourne librement.
  - Arcade : `$80` vaut `$08` au début de l'écran. Le premier recalcul tombe à l'image 56 et devient visible à 58.
  - SFA3 traduit : le compteur vaut `$9A`. Recalcul à 38, avec le bit 6 à 1, donc message 0, donc rien. Recalcul
    suivant à 102 (bit 6 à 0, message `$0C`), visible à 103.
- Upper : même routine, même rythme (Ryu est rendu avec une autre couleur de tenue : sans rapport, non étudié).
- Remarque sans rapport avec la question (`sfa3_fin_victoire.png`) : après l'effacement des textes, l'arcade garde
  une bande noire en bas de l'écran, la traduction montre le décor. Cela rejoint les écarts de scroll3 Y / ordre des
  plans déjà notés dans `BANDEAU-A.md` §6.

## 3. Cause du clignotement : routine du message J2 réécrite par l'Anthology (point 2)

**Trouvée par trace.** Le débogueur MAME (`-debug -debugger none`, `trace` avec registres) a tracé l'image où
« PRESS START » apparaît sur l'arcade (4772→4773), puis l'image précédente. Les deux traces ont été comparées. Les
octets ont aussi été journalisés image par image.

- **Variable** : octet « message du côté libre » `$14A` de la structure joueur (J2 = `$FF8800`).
  - Arcade : `$FF894A` passe à `$0C` à l'image 4772 et y reste.
  - Traduction : `$FF894B` (octet XOR 1) vaut `$0C`, puis `$00`, puis `$0C`… avec une bascule toutes les 64 images,
    aux images 4623, 4687, 4751, 4815, 4879.
- **Arcade `$7E30`** (appel tous les 64 images) :
  ```
  move.b ($80,A5),D0 ; andi.w #$3f,D0 ; bne fin
  moveq #$c,D0 ; tst.b ($9c,A5) ; beq ecrit       ; $9C = FREE PLAY
  moveq #1,D0 ; btst #6,($80,A5) ; beq ecrit ; moveq #0,D0
  ecrit: jmp $1ffa0                               ; -> move.b D0,($14a,A6)
  ```
  - Hors FREE PLAY, le message est `$0C` (« PRESS START ») en permanence.
  - En FREE PLAY, il alterne entre 1 (« FREE PLAY ») et 0 (rien).
  - Vérifié en forçant `$FF809C = 1` sur l'arcade (`essais/ref9c`) : « FREE PLAY » clignote 64/64, et le message 0
    n'affiche rien. Voir `preuves/messages_j2.png` et la 2e ligne de `chronologie_textes.png`.
- **Portage PS2**, même routine modifiée. MIPS SFA3 `0xF04A4`, 68K traduit `$213F0` ; Upper `0x134D04`.
  ```
  MOVE.B $80,D0 ; ANDI.W #$3F ; BNE fin
  MOVEQ #12,D0
  TST.B $C001(A5) [mode Anthology, PS2 $FF4000 ; Upper $FF4200] ; BNE -> test du bit 6
  A0 = autre joueur ; CMPI.B #$18,$119(A0) ; BCS -> test du bit 6 ; MOVE.B $119(A0),D0
  test du bit 6 : BTST #6,$80(A5) ; BEQ ecrit ; MOVEQ #0,D0
  ecrit: JSR (homologue de $1FFA0)
  ```
  - Le test FREE PLAY (sans objet sur console) a été remplacé par le test du mode.
  - **Tous les chemins** passent par le test du bit 6. Sur PS2, le message alterne donc entre 12 et 0 : « PRESS
    START » clignote.
  - La traduction rend exactement ce MIPS : `show.py f04ac`, chaque branchement et chaque cible vérifiés.
  - Le compteur lu est cohérent : `lb 129` côté PS2 donne `$80` côté 68K.
- **Recoupement PCSX2** (`work/etats_ps2/*.p2s`, `eeMemory.bin`, lus sans modification). Les valeurs de l'octet
  `0x90894A` et du compteur `0x908081` sont compatibles avec cette alternance :
  - `ancien_presentation` : compteur `$C1`, 1 image après un recalcul avec le bit 6 à 1, et message 0. L'image PS2
    montre encore « PRESS START », celui de la liste d'objets précédente.
  - `ancien_score3300` et `dramatic_jeu` : bit 6 à 0, message `$0C`.

  Aucun état ne permet d'observer directement une phase éteinte, mais rien ne contredit le code.
- **Même routine en combat** : pendant les combats, le « PRESS START » du côté libre devrait clignoter lui aussi,
  conformément au portage. Ce n'est pas mesuré.
- **Écarté**
  - Texte en scroll1 : aucune écriture dans `$900000-$92FFFF` pendant 9 images de frappe. Ce sont des objets.
  - Tâche du texte ou table des répliques : la frappe démarre et avance comme sur l'arcade (cadence identique).
  - Condition de temps : écran de même durée (361 images), effacement à −1 image.

## 4. Hyper

- **VERSUS** (`tournee_hyper.lua`, 2 manches gagnées) : à la fin du match, `A5+4 = $E`. L'écran passe à **RESULT**
  (tableau victoires / défaites) sans écran de victoire. Voir `preuves/hyper_versus_resultat.png`.
- **ARCADE** (`tournee.lua`, curseur `$FF4201 = 0`) :
  - J2 est validé par les minuteries (`$80A9 = 3`). C'est le vestige décrit dans `ETATS-HYPER.md` §2.2.
  - Après le combat, on passe aussi à la scène `$E` / RESULT (`preuves/hyper_arcade_resultat.png`).
  - Code : MIPS `0x2E9B0` (`A5+4 ← $E`), appelé depuis `0xA0330` (test du mode `$FF4200 = 1`) et `0xA09D4`.
- Hyper n'a pas de mode Arcade (HANDOFF §144) : **il n'y a pas d'écran de réplique à comparer**. La routine du
  message J2 d'Hyper n'a pas été cherchée plus loin : elle n'a pas la même forme et ne sert pas en VERSUS, où les
  deux joueurs sont en jeu.

## 5. Option possible (non faite, à décider)

Si l'on veut le comportement **arcade** (« PRESS START » fixe) plutôt que celui du portage PS2 :
- il suffit de ne pas émettre le `MOVEQ #0,D0` après `BTST #6,$80(A5)` dans cette routine ;
- cela fait 1 site par module : SFA3 `0xF06A4`, Upper `0x134F04` ;
- en pratique, une règle par adresse MIPS dans `translate.py`, derrière un interrupteur.

Ce serait un écart volontaire au portage, pas une correction de traduction : je ne l'ai pas appliqué.

## 6. Fichiers

- `untranspile/` : copie du traducteur, inchangée.
- Constructions : `mame3/`, `mame_ro5/`, `mame_ro9/`, avec `build3.log`, `build_ro5.log`, `build_ro9.log`.
- `essais/` : journaux et captures.
  - `ref2`, `tr2`, `u2` : captures image par image de l'écran de victoire.
  - `oct_*.txt` : octets ;
  - `tr4772.txt` / `tr4773.txt` : traces arcade ;
  - `ref9c` : arcade en FREE PLAY ;
  - `h1`…`h7` : Hyper.
- `preuves/` :
  - `sfa3_victoire.png`, `upper_victoire.png`, `sfa3_fin_victoire.png` ;
  - `chronologie_textes.png`, `messages_j2.png` ;
  - `hyper_versus_resultat.png`, `hyper_arcade_resultat.png`.
- **Incident** : un premier essai du débogueur avec `-log` a créé `work/mame/error.log`, car le répertoire courant
  était `work/mame`. Le fichier a été supprimé aussitôt : il ne contenait que mes 3 lignes. Les lanceurs travaillent
  désormais dans le dossier de l'essai.
