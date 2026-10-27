# Carte des symboles de SFA3 (module `ro3`)

État au 2026-10-04. L'image traduite de référence est celle du banc, générée à 15 h 21. Tout est dans `work/agent_symboles/`. Tout se reconstruit avec `./construire.sh` (environ 12 s).

## 1. Livrables

| fichier | contenu |
|---|---|
| `symboles_ro3.csv` | 10 246 symboles. UTF-8, séparateur `;`. Colonnes `type;nom;arcade;mips;trad;taille;rôle;source;confiance` |
| `carte_annotee_ro3.txt` | `carte_image.txt` annotée : 6 850 en-têtes de fonction et 36 602 lignes commentées sur 130 095 |
| `annoter.py` | CSV + `carte_image.txt` → carte annotée. Options `--csv`, `--carte`, `--sortie` |
| `construire.sh` | chaîne complète : copie de l'image et de la carte courantes, alignement, fusion, annotation |
| `outils/` | `desasm.py`, `aligne.py`, `fonctions.py`, `carte_fonctions.py`, `auto.py`, `paires_a5.py`, `fusion.py`, `trois.py`, `corrections.tsv`, `transporter_ro5.py` |
| `_extraits/part1-6.tsv` | relevé brut du journal et des notes, en 6 lots, avec la section source de chaque ligne |
| `symboles_ro5_esquisse.csv`, `carte_annotee_ro5_esquisse.txt` | essai de transport vers Upper (§7) |
| `_cache/` | désassemblages, alignement, paires de déplacements. Régénérable |

Conversions ponctuelles entre les trois espaces : `python3 outils/trois.py mips=1c9a84 arcade=27bae trad=440a0`.

## 2. Méthode

1. **Relevé du journal.** `HANDOFF.md` a été lu en entier, en cinq tranches. S'y ajoutent `CARTE-ro5.md`, `CARTE-ro9.md`, `homologues.txt`, `points_entree.json`, les notes MAX (rosette, portage, collisions, palettes), `ETAT-DES-LIEUX.md` et `FRAMES-Anthology.md`. Résultat : 1 212 lignes brutes, regroupées en 880 symboles.
2. **Alignement image traduite ↔ ROM arcade** (`aligne.py`). C'est la nouveauté : la correspondance ne passe plus par les constantes MIPS (`map_ro3_sfa3.json`, 4 % utilisable). On compare directement le 68K traduit et le 68K d'origine.
   - Les deux côtés sont désassemblés par `unidasm` (MAME) : notre image de `$1000` à la base des données, et `sfa3ud_prog.bin` de `$0` à `$FFFFF`.
   - Les instructions sont normalisées. On masque les adresses absolues, les adresses relatives au PC et les cibles de branchement. `JSR`/`BSR` deviennent CALL, `JMP`/`BRA` deviennent GOTO. On garde les immédiats et les déplacements sur An.
   - On ramène l'image à la numérotation arcade : octets XOR 1, plus une table de **relocalisation des variables A5 du portage** apprise par itérations (29 intervalles, §4).
   - L'idiome de lecture d'un octet de table indexée (8 instructions dans le portage) est replié pour correspondre au `MOVE.B T(PC,Dn)` de la ROM.
   - Ancres : 4-grammes de jetons uniques des deux côtés, confirmés par une voisine colinéaire. Les trous entre ancres sont comblés par LCS.
   - Résultat : **86 757 instructions traduites ont leur instruction arcade**, soit 53 % des lignes désassemblées, tables hébergées comprises.
3. **Fonctions** (`carte_fonctions.py`) :
   - les débuts MIPS sont les cibles de `jal` : 3 167 fonctions, comme `carto_ro5/commun.py` ;
   - on passe à l'image traduite par `carte_image.txt` ;
   - on passe à l'arcade par l'alignement de la 1re instruction alignée ;
   - si l'entrée est précédée d'un préfixe ajouté par le portage (par exemple un `JSR` vers une aide), on recale sur la cible d'appel ou sur ce qui suit une rupture ;
   - 2e passe : LCS bornée par les deux voisines.
   - **2 663 / 3 167 fonctions MIPS ont leur adresse arcade.** Les 43 natives n'en ont pas, par nature.
4. **Symboles automatiques** (`auto.py`, aucun nom inventé) :
   - fonctions arcade appelées par `JSR`/`BSR` depuis du code aligné ;
   - entrées de tâches (`JSR $1302` avec A0 = entrée et D0 = emplacement) ;
   - 1 313 aiguillages Capcom `MOVE.W T(PC,Dn),Dm ; JMP/JSR T(PC,Dm)` (§15) et leurs 4 409 gestionnaires ;
   - natives (`natifs_ro3.json`) et fonctions du moteur PS2 (`hooks_fork_ro3.json`) ;
   - variables A5 et champs appariés par vote sur les instructions alignées (`paires_a5.py`, par taille d'accès).
5. **Fusion** (`fusion.py`). Elle regroupe les relevés par adresse, choisit le nom le plus précis et le plus sûr (les autres deviennent des alias dans le rôle), puis complète les colonnes manquantes par l'alignement et la carte.
   - **Le code fait foi.** Quand l'arcade citée par le journal contredit l'instruction alignée, c'est l'adresse alignée qui est retenue, et le désaccord est écrit dans le rôle (7 cas, cherchez « non confirmée »).
   - Les cas tranchés à la main sont dans `outils/corrections.tsv`, commentés.
6. **Lecture du code ROM** pour quelques symboles clés : le noyau (`$1302`–`$13FC`) et la tâche principale (`$3EBA`). Voir le §6.

## 3. Colonnes et conventions

- **arcade** : adresse dans `sfa3ud` (ROM 68K déchiffrée). Selon le type :
  - variables : adresse RAM arcade `$FFxxxx` ;
  - champs : `+$xx` en numérotation 68K d'origine.
- **mips** : selon le type :
  - code : va **fichier** du module (exécution = + `0x1F0000`) ;
  - fonctions du moteur PS2 : `moteur 0x…`, adresse d'exécution hors module ;
  - variables : adresse PS2 `0x90xxxx` ;
  - champs : déplacement `+$xx` tel que le MIPS l'emploie.
- **trad** : adresse dans **notre** image (`roms_tr`, celle de `carte_image.txt`). Selon le type :
  - variables : `$FFxxxx` dans la numérotation de l'image ;
  - champs : `+$xx` tel qu'il apparaît dans `carte_image.txt`.
- **taille** : selon le type :
  - fonctions : octets arcade, ou `(t)` pour des octets de l'image traduite, ou `(m)` pour des octets MIPS ;
  - variables et champs : B, W ou L (tailles d'accès observées dans l'image).
- **confiance** :
  - « sûr » : vérifié dans le code. Pour un symbole du journal, l'affirmation est mesurée et ses adresses sont confirmées. Pour un symbole automatique, le rôle structurel est lu dans le code et l'instruction est alignée.
  - « probable » : l'adresse est interpolée ou l'alignement est faible (fonction alignée à moins de 50 %, gestionnaire sans instruction traduite alignée), ou le journal lui-même dit « probable ».
  - « hypothèse » : section dépassée du journal (avec un renvoi), ou alignement inférieur à 25 %.
- **Numérotation des octets, mesurée dans le code** :

| | octet | mot | moitiés d'un long |
|---|---|---|---|
| arcade | `$4` | `$10` | haut `+$10`, bas `+$12` |
| MIPS (PS2) | `$4` (= arcade) | `$10` | haut `+$12`, bas `+$10` |
| image traduite | `$5` (XOR 1) | `$10` | haut `+$12`, bas `+$10` |

  Exemple : `lb 4(A6)` (MIPS 0x5A650) = `MOVE.B $5(A6)` (traduit) = `MOVE.B $4(A6)` (arcade). Ce routine_no[0] est le sélecteur de 247 aiguillages ROM.

  Quelques octets échappent à la règle, par exemple `$12`, `$13`, `$80`, `$81`(A5) ; les votes par taille d'accès les traitent.

  ⚠ Dans le journal, « 68K » désigne souvent l'**image traduite** (le banc), et « PS2 » la numérotation MIPS. Pour les variables octet citées, la numérotation de chaque citation a été tranchée dans `corrections.tsv` (`num=a/t/p`).

- **Nommage** : snake_case, sans accent, préfixé par le domaine :

| préfixe | domaine |
|---|---|
| `joueur_` | structure joueur |
| `objet_` | structure objet |
| `tache_` | tâches |
| `noyau_`, `trapN_` | noyau Capcom |
| `intro_`, `menu_`, `combat_`, `anim_`, `collision_`, `palette_`, `son_`, `cps_`, `qsound_` | domaines du jeu et du matériel |
| `portage_` | ajouté par l'Anthology |
| `recomp_` | aides et registres du recompilateur |
| `natif_` | code C du portage |
| `moteur_` | exécutable PS2 |

  Noms génériques (style décompilation) :
  - `fonc_XXXXXX` : fonction arcade non nommée (XXXXXX = adresse arcade) ;
  - `port_XXXXXX` : fonction MIPS sans homologue arcade (XXXXXX = va MIPS) ;
  - `natif_XXXXXX` ;
  - `tache_EE_XXXXXX` : tâche, avec EE = emplacement ;
  - `<parent>__r4_06` : gestionnaire du cas `$06` de l'aiguillage sur `+$4(A6)` de `<parent>`. Les autres préfixes sont `r5_`, `r6_`, `r7_`, `r3_`, `mode_` (sur `$0(A5)`), `m138_` et `c_` (autre sélecteur) ;
  - `aig_<parent>` : la table d'aiguillage elle-même.

## 4. Variables A5 : le portage a relogé une partie de la RAM

L'image (comme le MIPS) emploie d'autres déplacements que la ROM dans la moitié basse `$FF0000-$FF3FFF`. Les intervalles ci-dessous ont été appris sur les instructions alignées (`_cache/reloc_a5.pkl`) :

| A5 traduit | → arcade | | A5 traduit | → arcade |
|---|---|---|---|---|
| `$8010-$80FE` | +`$2E9E` | | `$9EB0-$9EB4` | +`$43C` |
| `$8B90-$8BB4` | +`$179A` / +`$1798` | | `$A2E8-$A3AC` | +`$1140` |
| `$8C21-$8D15` | +`$254` (±2 : moitiés de longs) | | `$B134-$B198` | +`$47A` |
| `$8E40-$8E92`, `$9EA4` | +`$136` | | `$B330-$B792` | +`$474` / +`$472` |

Exemples :
- table des tâches : traduit `$8184(A5)` = arcade `-$7DA4(A5)` = `$FF025C` ;
- `portage_var_9eb0` : le §21 la donne pour « jamais utilisée par la ROM », mais c'est en réalité l'arcade `$FFA2EC`, relogée.

La zone `$FF4000-$FF4FFF` (`$C0xx`-`$C1xx`) appartient au portage seul. La moitié haute `$FF8000-$FFFFFF` n'est pas relogée (règle XOR des octets seulement).

## 5. Couverture

| | nombre |
|---|---|
| symboles | 10 246 |
| fonctions du module (MIPS + arcade + gestionnaires) | 8 223 |
| dont **nommées** (journal + lecture du code) | **194** (130 avec adresse arcade, 96 avec les trois adresses) |
| dont gestionnaires d'aiguillage (nom structurel) | 4 409 |
| dont génériques `fonc_`/`port_`/`natif_` | 3 620 |
| fonctions du moteur PS2 | 43 (24 nommées) |
| fonctions MIPS (cibles de `jal`) avec adresse arcade | 2 663 / 3 167 (84 %) ; 43 natives sans objet |
| fonctions avec les trois adresses | 6 302 |
| étiquettes (points internes cités) | 41 |
| tables | 1 432 (dont 1 313 aiguillages ; 119 tables de données nommées, dont 50 par perso) |
| variables A5 | 120 (68 avec leur adresse arcade ; 52 propres au portage) |
| champs joueur / objet (et bloc de tâche) | 78 / 65 |
| registres matériels, variables du portage, constantes | 68 / 78 / 98 |
| carte annotée | 36 602 lignes commentées sur 130 095 (A5 2 664, champs 28 596, appels 6 565, absolus 671) |

En clair : environ 2 % des fonctions ont un **nom sémantique**. Toutes les autres ont au moins leurs adresses reliées et un rôle structurel : appelée N fois, gestionnaire du cas k, tâche, native.

## 6. Ce que le code a appris en plus du journal

- **Noyau Capcom complet.** Les TRAP #4-#7, donnés « non décodés » au §60, le sont maintenant :
  - #4 `$13A6` : céder la main ;
  - #5 `$13CC` : suspendre la tâche D0 (état 2) ;
  - #6 `$13E8` : réveiller D0 (état 4, octet +1 = D1) ;
  - #7 `$13FC` : masquer ou démasquer les interruptions.

  Les enveloppes appelées par le jeu sont `$1302`, `$1324`, `$1346`, `$1370` (`noyau_attendre`, avec MOVEM), `$13A2`, `$13C0`, `$13DC` et `$13F8`.
- **Tâches de la ROM** :
  - `$3EBA` `tache_principale` (emplacement 0) : boucle sur le mode `$FF8000`, avec la table `$3EEC` ;
  - `$4036` (emplacement `$40`) = l'entrée de la tâche d'attraction, mips `0x468B0` ;
  - `$45EA` (`$60`), `$7B5E` (`$80`), `$8B3C` (`$A0`), `$16CEE` (`$100`).
- **Corrections du journal** :
  - les « ROM `$617C` » et « `$6328` » du §62 (repris par `CARTE-ro5`/`homologues.txt`) étaient des adresses de **l'image traduite de l'époque**. L'entrée arcade est `$4036` ;
  - `joueur_init` = mips `0x1C9A84` = arcade **`$27BAE`** (`MOVE.W #$90,$50(A6)`), et non `$27B98` ;
  - l'émetteur de frames type 08, « `$24484` » au §103, est une adresse traduite. L'arcade est `$21992` ;
  - les ancres R§5 `$91D8`, `$27804`, `$29766` sont recalées sur `$91F6`, `$27884`, `$297D4`.

## 7. Étendre à Upper (`ro5`)

Upper n'a pas de ROM arcade. La colonne « arcade » y devient donc « homologue SFA3 », et tout passe par `ro3`.

1. **Fonctions.** `work/carto_ro5/appariement_ro3_ro5.json` (début ro3 → `ro5`, score, type) donne le partenaire ; on ajoute le décalage interne quand les tailles sont égales.
2. **Image traduite d'Upper.** On passe par `work/mame_ro5/carte_image.txt`, avec la même logique « 1re ligne de va ≥ début ».
3. **Variables A5.** `carto_ro5/a5_ro3_ro5.json` donne les décalages de zone, en numérotation MIPS : +`$240`, +`$270`, +`$274` pour `$BE48`→`$C0BC`, +`$200`, +`$202`. La moitié haute et les structures joueur sont inchangées.
4. **Champs.** 432/433 sont inchangés. `$145` → `$121`.
5. **Nouveau code d'Upper.** Les 1 096 fonctions non appariées (Guile, Fei-Long, Dee Jay, T.Hawk, Shin Akuma, Balrog : `CARTE-ro5 §1.2`) restent à nommer, à partir des tables de code par perso (`tables_perso_ro3_ro5.json`).

**Esquisse faite** : `outils/transporter_ro5.py` → `symboles_ro5_esquisse.csv`. Il transporte :
- 3 972 fonctions (les gestionnaires internes ne passent que si les tailles concordent) ;
- 114 variables ;
- 143 champs.

On l'annote avec :

```
python3 annoter.py --csv symboles_ro5_esquisse.csv \
    --carte <workspace>/work/mame_ro5/carte_image.txt \
    --sortie carte_annotee_ro5_esquisse.txt
```

Résultat : 34 937 lignes annotées, 3 890 en-têtes. **À valider** : les gestionnaires et les points internes ne sont pas encore transportés quand la fonction a changé de taille. Il faut refaire l'alignement d'instructions à l'intérieur des paires (comme `aligne.py`, mais sur l'image traduite ro3 contre l'image traduite ro5).

## 8. Étendre à Hyper (`ro9`)

- **Correspondances.** `work/carto_ro9/points_entree.json` donne `ro9_direct` et `ro9_par_ro5` pour les points d'entrée ; `comparaison_ro9.json` et `comparaison_ro9_routine.json` donnent la correspondance par fonction.
- **Recompilateur plus récent.** Il travaille en drapeaux complets (§52) : comparer en sémantique (accès A5/A6, constantes), comme `carto_ro5/semantique.py`, plutôt qu'en n-grammes.
- **Versions.** Les champs de version d'Hyper (`$102/$116/$117/$D3(A6)`, §46/§50) sont à ajouter comme champs joueur propres à ro9.
- **Banques.** Hyper n'a aucune banque propre (§51) : les tables par perso se transportent depuis ro5.
- **Procédure** : `transporter_ro5.py` avec le fichier de paires de ro9 et `work/mame_ro9/carte_image.txt`.

## 9. Limites

- **Découpage MIPS.** Il suit les `jal`. Des entrées atteintes par pointeur (tâches, rappels `ctx`, tables) tombent à l'intérieur d'une fonction MIPS. Le journal les nomme alors comme fonctions, et le CSV garde le va exact.
- **Fonctions sans arcade.** 461 fonctions MIPS non natives n'ont pas d'arcade (`port_…`) : code ajouté, routines réécrites, ou alignement trop pauvre. 229 autres ont une entrée « décalée (incertain) ».
- **Fonctions d'un seul `RTS`.** Elles sont ambiguës : `rts_vide_aaa6` garde l'adresse du journal.
- **Noms des automatiques.** Les gestionnaires et les tables d'aiguillage portent un nom structurel, pas sémantique. Leur sélecteur est lu dans le code. La sémantique des cas (états d'un perso…) reste à faire.
- **Numérotation.** Celle des octets cités par le journal a été tranchée au cas par cas (`corrections.tsv`). Ailleurs, la règle XOR est appliquée, avec les votes de l'alignement quand il y en a (au moins 3 votes et 75 % d'accord).
- **Régénération de l'image.** L'image traduite change à chaque `mame_test.py` : les adresses `trad` bougent, pas les va MIPS. `annoter.py` le détecte (contrôle de cohérence trad ↔ va) et retombe alors sur les va MIPS. Pour remettre la colonne `trad` à jour, relancer `./construire.sh`.
- **Rien n'a été lancé au banc** (pas de MAME). Toutes les vérifications sont statiques.
