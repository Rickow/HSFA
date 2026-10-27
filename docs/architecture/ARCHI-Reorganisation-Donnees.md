# Architecture de la réorganisation des données (projet, 2026-10-07)

But : supprimer les adaptateurs mesurés au §138 (conversions de pointeurs 13 %, longs échangés ~7 %, octets XOR 1,
registres prêtés : ~20-22 % du travail du 68000 en combat) ET rendre la mémoire identique à l'arcade (disposition
CPS2 réelle). Cible ultime : SFA3 traduit = arcade octet pour octet là où le code est aligné ; Upper/Hyper/MAX dans
la disposition arcade.

## 1. État de départ

| couche | aujourd'hui | coût mesuré (§138) | volume (SFA3 / Upper) |
|---|---|---|---|
| pointeurs de données | adresses PS2 brutes dans les tables et la RAM, `JSR CONV_An` après chaque `MOVEA` venu de la mémoire | 8,6 % + appels 0,8 % | ~630 sites d'appel |
| pointeurs de code | adresse PS2 → table de hachage `$3C0000` avant chaque `JSR/JMP (An)` | 3,7 % | quelques dizaines de sites, chauds |
| longs | « recette universelle » §29 : moitiés échangées en mémoire, `SWAP` (+ `MOVE SR/CCR`, pile) | ~6,7 % | 4 693 / 5 096 émissions |
| octets | adresse XOR 1 (indexés : bascule à l'exécution) | 0,3 % | 128 / 130 sites à l'exécution |
| registres A8/D8 | domiciles `$87E0`/`$87F0(A5)`, prêts par zones | 0,2 % | 371 / 435 |

## 2. Principe : une carte unique, des étapes réversibles, un oracle

1. **Une seule source de vérité : `carte_types`** (JSON + module Python, lu par le traducteur, l'assembleur des
   données, les outils Lua et le cœur FBNeo) :
   - zones de RAM : variables A5 par ADRESSE (sans ambiguïté) ; structures par TYPE (joueurs `$FF8400+$400·k`,
     réservoirs d'objets, projectiles `$100`, tampons de sprites…) avec leur PROVENANCE (d'où vient le pointeur) ;
   - pour chaque champ : décalage PS2, type (`u8`, `s16`, `s32`, `u8[4]`, `s16[2]`, `ptr_donnees`, `ptr_code`),
     décalage arcade ;
   - tables de données en ROM : plage, taille d'élément, champs (dont pointeurs), adresse arcade correspondante.
   Sources : `typed_rule.py` (tailles d'accès, 94 %), `const_evidence.json` (constantes ROM, 95 %), paires des
   fonctions alignées sur l'arcade (`layout_pairs.json`, alignement de l'agent couverture : 91 % du code SFA3),
   traces d'exécution (journal des conversions, `watch.py`).
2. **Chaque étape a son interrupteur** (comme tout le traducteur : variable `=0` → ancien comportement) et la
   recette actuelle reste le **filet de sécurité** pour tout ce qui n'est pas encore typé. On bascule zone par zone.
3. **Oracle** :
   - SFA3 : **RAM comparée à l'arcade** (même partie jouée par `tournee.lua`, `REF=1` contre traduction, vidages
     `DUMPC` au début des manches et pendant l'attraction) ; une fois typée, une zone doit être IDENTIQUE à l'arcade
     (hors variables propres au portage). Upper partage 72 % des variables A5 de SFA3, Hyper 77 % (§30) : ce qui est
     validé sur SFA3 se transporte.
   - Tous : non-régression, 42 commandes, balayage des 72 fins, captures ±1, **journal des conversions vide**
     (aucune adresse PS2 brute vue par les talons), profil `_prof_adapt.lua`.
4. **ROM auto-descriptive** : un petit en-tête à adresse fixe dans la ROM programme (version de disposition, adresses
   des variables lues par le banc : liste d'objets, pointeur d'animations `$FF40BC`, bases de plans…). Le fork MAME,
   les scripts Lua et le cœur FBNeo lisent cet en-tête au lieu d'adresses en dur → **une nouvelle disposition ne
   demande pas de recompiler le cœur**, seulement un nouveau zip (`paquet_fbneo.py`, format inchangé).

## 3. Étapes

| # | étape | gain | risque | validation |
|---|---|---|---|---|
| A | **Instrumentation** : talons `CONV` en mode journal (Lua : valeur, instruction source `MOVEA.L d(Ax),An` → case mémoire d'origine) ; outil de comparaison RAM traduction/arcade ; accesseur Lua `disposition.lua` (tous les outils lisent la RAM par la carte) | 0 | nul | — |
| B | **Pointeurs de code** relogés à l'assemblage (tables et cases identifiées par le journal → étiquettes 68K) ; suppression du hachage aux sites dont toutes les provenances sont relogées | ~3,7 % | faible (un oubli = saut faux, visible tout de suite) | journal vide sur les 72 fins + modes |
| C | **Pointeurs de données des tables ROM** relogés (journal + vérification contre la table arcade quand elle existe) | | moyen | idem |
| D | **Pointeurs en RAM** : quand toutes leurs sources sont relogées, suppression des `JSR CONV` après les `MOVEA` | ~9,4 % | moyen | journal vide, puis talons retirés |
| E | **RAM typée** : variables A5 (adresses fixes) → structures joueurs (A6 du code des persos) → objets/projectiles → A0-A4 par provenance. Longs natifs (plus de `SWAP`), octets/mots aux décalages arcade | ~7 % | ÉLEVÉ (champ mal typé = corruption silencieuse) | RAM identique à l'arcade zone par zone (SFA3), puis Upper/Hyper |
| F | **Tables de données typées** (gros-boutistes par élément, comme 3SX `section_element_sizes`) ; pour SFA3, copie/contrôle depuis la ROM arcade | fidélité | moyen | octets identiques aux tables arcade |
| G | **Registres prêtés** : allocation globale (A8/D8 dans de vrais registres libres par fonction) | ~0,2 % + taille | faible | non-régression |

Ordre proposé : A → B → C → D (gain de performance rapide, risque contenu), puis E par zones, F, G.
Points durs connus : unions (`s16[2]` / `s32` selon la fonction, §44), registres de base qui désignent des
structures différentes (A4 `$0/$2/$4/$8`), copies génériques (MOVEM, boucles de copie : indifférentes à la
disposition si les deux côtés sont de même type et alignés sur 4), le code C du portage (laissé en recette).

## 4. Ce que ça apporte au-delà de la vitesse

- **Disposition arcade** : les adresses et cartes RAM connues de SFA3 (codes de triche MAME, outils d'entraînement,
  documentation) valent pour Upper et Hyper ; les comparaisons avec l'arcade deviennent exactes.
- **MAX** : la session MAX raisonne déjà en adresses arcade (`$32F46`, `$1C1C8`, champs `$362`/`$3F3`) → intégration
  directe, sans transposition PS2.
- **Outils plus simples** : plus de longs écrits en deux mots inversés dans les scripts (`FORCE="L…"`).

## 5. Ce que ça n'apporte pas

Sur une petite console (RGB10X), l'émulateur simule le 68000 à cadence fixe, boucle d'attente comprise : la charge de
l'hôte ne baisse pas. Le gain est pour le jeu lui-même : plus de marge (turbo sans images répétées, §104, sans
surcadençage). La charge hôte se joue sur le rendu CPS2 et le QSound du cœur.
