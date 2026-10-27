# Audit des tables indexées par l'id du perso — Upper (`ro5`), construction `MAX=1`

Agent `agent_audit_id`, 2026-10-25. Construction auditée : copie figée `fige/banc_max15` (sz3ud.03c `0a68ad4e…`,
04c `a8e77753…`, md5 complets : `fige/banc_max15.md5`) ; référence `fige/banc_ref` (MAX=0). Rien n'a été modifié dans
la construction MAX ; seul fichier écrit hors de ce dossier : `work/echanges/MAX.md` (Q6-Q9 + une note).

## 0. Résumé

177 lignes dans `audit.tsv` : **8 défauts visibles (V)**, **4 déjà traités (T)**, **58 latents (L)**, **18 sans objet (S)**,
**65 propres (OK)**, 24 faux positifs du balayage rejetés (R). Seule table nouvelle trouvée par la différence dynamique :
`0x616B30` (carte du monde) ; les autres V/L nouvelles viennent du balayage statique et des copies restées par défaut.

Les 10 plus graves :
1. `0x960090` prologue (listes de pages terminées par **0**) — cas témoin Yun → Ingrid (§2) ; **T** (corrigé depuis).
2. `0x61B580` / `0x61B600` scénarios de dialogue des combats spéciaux (3 rangées de 40) : **Yun joue les dialogues
   d'Adon, Ingrid ceux de Sodom** (rangée suivante) ; Eagle / Maki ceux de Ryu / Juli. Capture `captures/cap_2d_dlg.png`.
3. `0x616B30` carte du monde, position de départ (x, y) : Yun / Ingrid lisent des données voisines (963,−60 / 392,360),
   Maki (0,0) comme Juli, Eagle Ryu.
4. `0x97AF50` noms ASCII de l'écran RESULT du VERSUS : les 4 MAX s'affichent « RYU » (`captures/cap_vs27.png`).
5. `0x978D1C` parcours de l'Arcade : ceux de Ryu / Juli (vu : Yun et Ingrid = suite de Ryu 19 0C 0D 1B 09 1C 0B 1D 01 0A).
6. `0x61B680` combat secret, 7. `0x61B6D0` décor imposé aux combats 8/9 : ceux de Ryu / Juli.
8. `0x748CA8` demi-largeur → `$A6` (distance de poussée) : valeur de Ryu, lue dans toutes les parties.
9. `0x95CCD0` visage HUD, 4e variante (42 × 8) : seule des 4 variantes non agrandie (Yun / Ingrid hors table ; non vue).
10. `0x74C720` / `0x74C748` / `0x74C6D0` / `0x74C6F8` réglages de jauge / récupération d'étourdissement : Ryu (lus).

Piège générique (à ajouter à AGENTS.md) : **un bloc ajouté par `agrandit_max.bloc_rel16` ne reçoit pas la marque de
fin du format natif** (0 pour 0x960090) ; seul le bourrage d'une longueur impaire en crée une, par hasard. Tout bloc
de liste doit porter sa marque explicitement. `outils/marques.py` vérifie toutes les copies rel16 : seul 0x960090 / Yun
était en défaut dans banc_max15.

## 1. Méthode

- **Statique** (`outils/balaye.py`, sortie `essais/usages.tsv`, 429 usages) : propagation avant de la « teinte » id
  depuis `$102/$103(An)`, `$503/$903/$D03/$1103(A5)`, `$132/$133/$146/$147/$C30E/$C30F/$1C9(A5)`, `$3A/$7F` d'objet ;
  suivi des ADD/LSL/MULU/ADDI/ANDI, des branches (cibles approchées : le prologue MIPS n'émet pas de 68K), des appels
  (`JSR ???` résolus par l'offset « fichier ») et des sauts terminaux absorbés ; usages : `(An,Dn)`, `T_x(PC,Dn)`,
  `ADDA Dn,An` puis `d(An)`, motif rel16, comparaisons à un id ; bases multiples par chemin, remontée chez l'appelant.
  Couverture : 118 des 139 tables déjà connues retrouvées ; manquent celles lues par un pointeur stocké
  (`$2D0/$2D4`, marche / sauts) ou par un index composé (`ADD.B $103(A6),D0` : 0x61B580 / 0x61B600, ajoutées à la main).
- **État MAX** (`outils/classe.py`, `audit_brut.tsv`) : base effective de chaque site LUE DANS LA ROM MAX (opérande du
  LEA / MOVE.L # : copie `$E8xxxx`, table déplacée `$B8xxxx` ou native) ; entrée de chaque id MAX comparée aux 40
  entrées natives : PROPRE / DEFAUT (copie agrandie restée à la valeur par défaut : entrée 0 pour 45/46, ancienne
  38/39) / COPIE(j) / HORS (index au-delà de la table native). Structures à listes, rel16, rangées : traitées à part.
- **Dynamique** : 16 parties espionnées (lecture de toute la ROM et des blocs, `lua/espion.lua` de l'intégration) :
  Arcade 90 000 images de `$26 $27 $2D $2E $00 $1E` (34 à 40 combats, fins comprises), VERSUS J1 MAX / J2 Ryu et J1
  Ryu / J2 MAX pour les 4, plus deux VERSUS natifs. `outils/dyn_analyse.py` : (A) lecture de l'entrée d'un id MAX par
  un lecteur de la table (`essais/dyn_confirme.tsv`, 700 lectures) ; (B) différence Ryu / MAX (même pc, écart
  e·id) pour trouver des tables inconnues (`essais/dyn_decouverte.tsv`) : 616B30 seule nouveauté, le reste = tables
  connues ou bruit (animateur générique, `$2B8`, décor).
- **Captures** (`captures/`, planches) : prologue de Yun (`cap_2d_pro` : 4 pages de Yun puis celles d'Ingrid),
  même partie sur la copie d'essai `fige/banc_max15_t0` (un 0 posé en `$EA7D45` : Yun s'arrête à ses pages),
  Ryu (`cap_00_pro`), dialogue de Yun (`cap_2d_dlg`), RESULT du VERSUS avec Maki (`cap_vs27`).

## 2. Cas témoin : intro de Yun suivie de celle d'Ingrid

Table `0x960090` (bios_par_perso) : 40 décalages u16 relatifs → liste d'octets n° de page (dernier | $80) **puis 0**.
Le lecteur (image `$056F9C`, va 0x44D1D0) lit l'octet `$144(A5)` de la liste et s'arrête sur 0 (`$80` ne termine pas).
Dans la copie agrandie (`$EA7848`), `prologue()` ajoute `PROLOGUE_MAX_xx` par `bloc_rel16`, qui ne met un 0 qu'après une
longueur impaire : Eagle `01 02 83 00`, Maki `04 05 86 00` (bourrage), **Yun `07 08 09 8A` puis directement Ingrid
`0B 0C 0D 8E`**, puis le bourrage `00`. Espion (`arc_2d`) : pc `$056FAE` lit `$EA7D40…$EA7D48` (9 octets, 8 pages)
aux images 2305-2641 ; Ingrid lit `$EA7D44…$EA7D48`. Correctif : `bloc_rel16(T_PROLOGUE_LISTES, id, b + b"\x00")`.
Aucune donnée PSP en cause. Le coordinateur signale la correction faite depuis ; à vérifier sur le prochain banc
(`outils/marques.py` sur la nouvelle construction).

## 3. Tableau (trié par gravité)

Colonnes : `e × n` = octets par entrée × entrées natives (× rangées) ; `copie` = copie agrandie (bloc `$E80000`) ou
« non » ; états : propre / déf(j) = resté à la valeur par défaut, égale à l'entrée native j / copie(j) / HORS ;
« lue » = parties où un lecteur de la table a lu l'entrée de cet id (A = Arcade, V = VERSUS J1_J2).

### 3.1 Défauts visibles (8)

| table | rôle | e × n | copie | $26 | $27 | $2D | $2E | lue avec un id MAX | correctif | PSP / données |
|---|---|---|---|---|---|---|---|---|---|---|
| `616b30` | carte du monde : position (x, y) par perso au départ de l'Arcade (2 mots, 40 entrées) | 4 × 40 | non | copie(0,2,12) | copie(21,30,31) | HORS | HORS | 26:A26,27:A27,2D:A2d,2E:A2e | agrandir à 48 (LEA dans T_616b30/T_616b32, va 0x3889C0) ; Eagle / Maki / Yun / Ingrid : positions PSP | positions de la carte PSP (pays : Angleterre, Japon, Hong Kong, ?) à demander ; à défaut : Birdie/Cammy, Ryu, Fei-Long/Chun-Li |
| `61b580` | scénarios de dialogue des combats spéciaux (3 rangées x 40, rangée = ($13E-8)/2) | 1 × 40 × 3 r. | non | copie(0) | copie(30) | HORS (rangée suiv.) | HORS (rangée suiv.) | 26:A26,27:A27,2D:A2d,2E:A2e | agrandir à 3 x 48 (constante de rangée : LSL #4 + LSL #2 = x20 sur ($13E-8) -> x24) ou talon : ID >= $28 -> $FF ; puis scénarios MAX | scénarios PSP d'avant-combat (rival, boss) des 4 MAX à demander ; textes déjà dans textes.json « scenario_et_fin » |
| `61b600` | scénarios de dialogue (2) (3 rangées x 40 ; rangée 2 = 61b650) | 1 × 40 × 3 r. | non | copie(0) | copie(2,18,20) | HORS (rangée suiv.) | HORS (rangée suiv.) | 26:A26,27:A27,2D:A2d,2E:A2e | idem 61b580 (et garder 61b650 cohérente : c'est sa 3e rangée) | idem 61b580 |
| `61b680` | combat secret (Balrog / Juli+Juni) par perso | 1 × 40 | e81290 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26,27:A27,2D:A2d,2E:A2e | valeurs MAX (ou $FF = aucun) | à demander (PSP : combats secrets des MAX) |
| `61b6d0` | décor imposé aux combats 8 / 9 (2 rangées) | 1 × 40 × 2 r. | e812c0 | déf(0,3,4) | déf(1,2,5) | déf(0,3,4) | déf(0,3,4) | 26:A26,27:A27,2D:A2d,2E:A2e | valeurs MAX | à demander |
| `748ca8` | demi-largeur du perso -> $A6 (24 ou 32 : poussée / distance) | 2 × 40 | ea08ec | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:A2e+V00_2e+V2e_00 | valeurs MAX | largeurs PSP (champ équivalent de $A6) à demander |
| `978d1c` | parcours de l'Arcade : 16 parcours de 10 adversaires par perso (rel16) | 2 × 40 | eacf58 | déf(0) | déf(30) | déf(0,38) | déf(0,38) | 26:A26+V26_00,27:A27+V27_00,2D:A2d+V2d_00,2E:A2e+V2e_00 | blocs MAX propres (bloc_rel16) aux entrées 38/39/45/46 | parcours PSP (adversaires, rival, boss) des 4 MAX à demander |
| `97af50` | textes par perso (noms ASCII de l'écran des résultats VERSUS, 2 rangées $C30F / $C30E+$28) | 2 × 40 × 2 r. | eae458 | déf(0,23,37) | déf(0,23,37) | déf(0,23,37) | déf(0,23,37) | 26:V00_26+V26_00,27:V00_27+V27_00,2D:V00_2d+V2d_00,2E:V00_2e+V2e_00 | blocs MAX propres « EAGLE », « MAKI », « YUN », « INGRID » (format #x y + 10 car. + $7F) | aucune donnée PSP nécessaire (texte) |

### 3.2 Déjà traités (hors de cet audit, à vérifier dans le prochain lot) (4)

| table | rôle | e × n | copie | $26 | $27 | $2D | $2E | lue avec un id MAX | correctif | PSP / données |
|---|---|---|---|---|---|---|---|---|---|---|
| `61b4a0` | anim de réaction par type (arcade $2D5B2), 34 octets ; PSP 0x214F3C a 37 types | 1 × 34 | non | - | - | - | - | non vue | prolonger 34 -> 37 (34 -> 36, 35 -> 23, 36 -> 36) — déjà traité (R5) | R5 (work/echanges/MAX.md) |
| `960090` | prologue : listes de pages (rel16, fin = 0) | 2 × 40 | ea7848 | propre | propre | propre | propre | 26:A26,27:A27,2D:A2d,2E:A2e | integre_max.prologue() : bloc_rel16(..., b + b'\x00') (marque 0 ; aujourd'hui Yun 4 octets pairs -> déborde sur Ingrid ; Ingrid finie par le bourrage, par chance) | aucune donnée PSP : défaut d'intégration (prologue_max.s est juste) |
| `arc:023608` | coup au sol par type de réaction (arcade $23608 ; PSP 0x21DC4C / 0x21DD0C) | 1 × 34 | non | - | - | - | - | non vue | 34 / 36 comme 18, 35 comme 14 — déjà traité (R5) | R5 (work/echanges/MAX.md) |
| `arc:028bf6` | gestionnaire de réaction par type (arcade $28BF6 ; PSP 0x2157C4) | 1 × 34 | non | - | - | - | - | non vue | 34 = 18 ; 35 / 36 nouveaux (PSP 0x583E4 / 0x584B4) — déjà traité (R5) | R5 (work/echanges/MAX.md) |

### 3.3 Défauts latents (valeur de Ryu / Juli ou hors table, effet non vu) (58)

| table | rôle | e × n | copie | $26 | $27 | $2D | $2E | lue avec un id MAX | correctif | PSP / données |
|---|---|---|---|---|---|---|---|---|---|---|
| `60b4a0` | octet par n° de fin $1C9 (1 pour les fins 2, 17, 19, 36) -> $40(A4) = 2 | 1 × 40 | non | copie(0,1,3) | copie(0,1,3) | HORS | HORS | 26:A26,27:A27,2D:A2d,2E:A2e | agrandir à 48 ($2D/$2E lisent 0 = valeur courante, sans effet) | - |
| `60c680` | octet par perso -> $28F | 1 × 40 | e80750 | déf(34) | déf(35) | déf(0,1,4) | déf(0,1,4) | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:V00_2e+V2e_00 | valeurs MAX | à identifier |
| `6132e0` | masque #$03210D40 (voix) -> octet par perso | 1 × 40 | e80840 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:A2e+V00_2e | valeurs MAX | à identifier |
| `615380` | octet par perso, test (va 0x3625A8) | 1 × 40 | e80990 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:V00_26 | valeurs MAX | à identifier |
| `615570` | (dx, dy) d'un objet attaché créé par le perso | 4 × 40 | e809c0 | déf(0,1,2) | déf(22,30,31) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | positions PSP à demander |
| `615572` | demi-table (dy) de 615570 | 4 × 40 | non | déf() | déf() | déf(0,1) | propre | non vue | avec 615570 | - |
| `615790` | (dx, dy) d'un effet ($3D = $45/$46) | 4 × 40 | e80a80 | déf(2,3,4) | déf(22,26,30) | déf(0) | déf(0) | non vue | valeurs MAX | à demander |
| `615792` | demi-table de 615790 | 4 × 40 | non | déf(21,25,29) | déf() | propre | propre | non vue | avec 615790 | - |
| `615940` | pseudo-ID de Vega (42 longs) | 4 × 42 | e80b40 | propre | propre | déf(0,28) | déf(0,28) | non vue | valeurs MAX pour Yun / Ingrid (Eagle / Maki posés) | - |
| `615ac0` | (dx, dy) par propriétaire ($3A d'un objet) : apparition d'effets | 4 × 40 | e80c00 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26,27:A27,2E:A2e | valeurs MAX | à demander |
| `615ca0` | octet par propriétaire -> routine 0x1337F | 1 × 40 | e80cc0 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | à identifier |
| `616130` | octet par perso, 2 rangées ($169 / $15C(A5)) | 1 × 40 × 2 r. | e80cf0 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | à identifier |
| `616180` | ID -> ID de référence pour un objet | 1 × 40 | e80d50 | déf(18,20,23) | déf(0,10,21) | déf(0,10,21) | déf(0,10,21) | non vue | valeurs MAX (lui-même ?) | - |
| `617290` | hauteur Y des étoiles d'étourdissement posées sur le perso (visible si étourdi ; non vu dans les parties) | 2 × 40 | e80de0 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | à demander (PSP : hauteur des étoiles) |
| `617be0` | octet par perso adverse -> routine 0x8BF10 | 1 × 40 | e80e40 | déf(0,2,10) | déf(0,2,10) | déf(0,2,10) | déf(0,2,10) | non vue | valeurs MAX | à identifier |
| `6180f0` | décalage X d'un objet attaché (signé selon le sens) | 2 × 40 | e80e70 | déf(0,23,27) | déf(0,23,27) | déf(0,23,27) | déf(0,23,27) | non vue | valeurs MAX | à demander |
| `61a840` | long par perso signé selon le sens, début de manche | 4 × 40 | e80f90 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | à identifier |
| `61aa30` | octet par perso x (ism+1) -> $270 | 4 × 40 | e81050 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:A2e+V00_2e+V2e_00 | valeurs MAX | à identifier |
| `61aad0` | (dx, dy) par perso -> $12/$16 d'un objet | 4 × 40 | e81110 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26,27:A27,2D:A2d,2E:A2e | valeurs MAX | à demander |
| `61aad2` | demi-table de 61aad0 | 4 × 40 | non | déf(0,1,12) | déf() | déf(0,1,12) | déf(0,1,12) | non vue | avec 61aad0 | - |
| `61b4e0` | masque #$E76BFFFB -> octet par perso | 1 × 40 | e811d0 | déf(0,1,3) | déf(0,1,3) | déf(0,1,3) | déf(0,1,3) | 26:A26,27:A27,2D:A2d,2E:A2e | valeurs MAX | à identifier |
| `61b510` | masque #$3F4AFB9B -> octet par perso | 1 × 40 | e81200 | déf(0,1,3) | déf(0,1,3) | déf(0,1,3) | déf(0,1,3) | 26:A26,27:A27,2D:A2d,2E:A2e | valeurs MAX | à identifier |
| `61b540` | masque #$2640F310 -> octet par perso | 1 × 40 | e81230 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | à identifier |
| `61b650` | scénario de dialogue (3e rangée de 61b600) -> $147 | 1 × 40 | e81260 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX (aujourd'hui $FF = pas de dialogue) | comme 61b580 |
| `61ba10` | octet par perso, 3 rangées -> drapeaux | 1 × 40 × 3 r. | e81320 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:A2e+V00_2e+V2e_00 | valeurs MAX | à identifier |
| `61ba90` | masques 8 o par perso (38 entrées !) OR dans D2/D3 si $C3A4(A5) | 8 × 40 | non | copie(38) | copie(39) | HORS | HORS | non vue | agrandir à 48 (entrée 38 lit déjà 61bbc0) | - |
| `61ba94` | 2e long de 61ba90 | 8 × 40 | non | copie(38) | copie(39) | HORS | HORS | non vue | avec 61ba90 | - |
| `61bbc0` | enregistrements de 4 o par perso (mode Arcade) | 4 × 40 | e813b0 | déf(39) | déf(38) | déf(0) | déf(0) | non vue | valeurs MAX | à identifier |
| `61bd60` | ID -> $176(A5) (variante 0-4 de fin / illustration) | 1 × 40 | e81470 | déf(0,1,2) | déf(4,9,13) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | - |
| `61bdb0` | adversaire spécial imposé -> $103 de l'adversaire | 1 × 40 | e814a0 | déf(0) | déf(30) | déf(0,38) | déf(0,38) | non vue | valeurs MAX | à demander |
| `61be10` | décor du perso (home stage) : lu quand le perso est l'ADVERSAIRE (jamais un MAX en Arcade) | 1 × 40 | e814d0 | déf(0,18,20) | déf(10,30,31) | déf(0,18,20) | déf(0,18,20) | non vue | valeurs MAX (aujourd'hui décor de Ryu / pour Maki celui de l'entrée 39) | décors PSP des MAX à demander ; Upper n'a pas leurs décors : choisir un décor natif |
| `61be40` | décor du perso, variante ($C3A4(A5) ≠ 0) ; 40 entrées puis zéros | 1 × 40 | non | copie(0,18,20) | copie(30) | HORS | HORS | non vue | agrandir à 48 avec les mêmes valeurs que 61be10 | comme 61be10 |
| `61bed0` | liste d'ID du choix aléatoire (&$3F) : les MAX n'y sont pas | 1 × 40 | non | copie(6) | copie(7) | HORS | HORS | non vue | ajouter les 4 ids si le tirage doit les donner | - |
| `61d9f0` | mot par perso -> $6A | 2 × 40 | e81560 | déf(39) | déf(38) | déf(0,1,22) | déf(0,1,22) | 26:A26,27:A27 | valeurs MAX | à identifier |
| `620630` | aiguillage EN LIGNE (40 mots) : ID >= $28 -> entrée 0 (talon) | 2 × 40 | non | copie(34) | copie(1,3,5) | HORS | HORS | non vue | cases MAX si le chemin compte | - |
| `620e30` | mot par perso -> $6A, 2 rangées | 2 × 40 × 2 r. | e815c0 | déf(31,39) | déf(31,38) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | à identifier |
| `622d10` | (dx, dy) selon l'ID ADVERSE (code d'un perso natif) | 4 × 40 | e81680 | déf(6,20) | déf(7) | déf(0,23) | déf(0,23) | non vue | valeurs MAX pour Yun / Ingrid | positions PSP (prises des natifs sur un MAX) |
| `623e50` | mot selon l'ID ADVERSE, 3 rangées | 2 × 40 × 3 r. | e81800 | déf(0,23) | déf(3,22,30) | déf(0,23,38) | déf(0,23,38) | 26:A26,27:A27,2D:A2d | valeurs MAX | à demander |
| `648bc8` | listes d'animation par perso (3 listes de 40 x 8) | 8 × 40 | e81920 | déf(3 listes) | déf(3 listes) | déf(3 listes) | déf(3 listes) | non vue | listes MAX | à identifier |
| `697fe0` | moteur de coups : octet [ID défenseur x 32 + $126] | 32 × 40 | e9ced4 | déf(28,30,31) | déf(28,30,31) | déf(0,1,6) | déf(0,1,6) | non vue | valeurs MAX | à identifier |
| `6993e0` | seuil par perso comparé à la vitalité | 1 × 40 | e9e0d4 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:A2e+V00_2e | valeurs MAX | à identifier |
| `699408` | seuil (variante) | 1 × 40 | e9e104 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:V00_26,27:V00_27,2D:V00_2d,2E:V00_2e | valeurs MAX | - |
| `699430` | octet par perso (moteur de coups) | 1 × 40 | e9e134 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:V00_26 | valeurs MAX | - |
| `699458` | octet signé par perso -> table 0x5F6030 x 128 | 1 × 40 | e9e164 | déf(35) | déf(4,6,7) | déf(0,1,2) | déf(0,1,2) | 26:A26,27:A27,2D:A2d,2E:A2e | valeurs MAX | à identifier |
| `699480` | octet par perso x 32 -> table 0x5F4F30 | 1 × 40 | e9e194 | déf(0,1,11) | déf(9,13,15) | déf(0,1,11) | déf(0,1,11) | 26:A26,27:A27,2D:A2d,2E:A2e | valeurs MAX | à identifier |
| `722080` | palettes (3e table : décalages -> palette n°) | 2 × 40 | e9e1c4 | déf(0,1,2) | déf(27,28,29) | déf(0,1,2) | déf(0,1,2) | non vue | blocs MAX | palettes MAX (déjà converties : palettes_module.bin) |
| `749b58` | vitesses de marche ism +1 (Maki = Juli) | 8 × 40 | ea19cc | propre | déf(30,31) | propre | propre | non vue | valeurs MAX de Maki | physique_max_arcade.json |
| `74c3f8` | positions d'apparition d'effets par propriétaire | 4 × 40 | ea43cc | déf(0,1,2) | déf(22,30,31) | déf(0,1,2) | déf(0,1,2) | 26:A26,27:A27,2E:A2e | valeurs MAX | à demander |
| `74c498` | positions d'effets (variante) | 4 × 40 | ea448c | déf(0,1,2) | déf(22,30,31) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | à demander |
| `74c6d0` | index par perso -> T_592780 (réglage de jauge) | 1 × 40 | ea472c | déf(0,1,2) | déf(3,4,18) | déf(0,1,2) | déf(0,1,2) | non vue | valeurs MAX | PSP 0x21D3A0 (jauges par perso) |
| `74c6f8` | index par perso -> T_5927C0 (réglage de jauge) | 1 × 40 | ea475c | déf(0,1,2) | déf(4,5,6) | déf(0,1,2) | déf(0,1,2) | 26:V00_26 | valeurs MAX | PSP 0x21D3A0 |
| `74c720` | octet par perso -> $159 | 1 × 40 | ea478c | déf(0,1,3) | déf(4,9,13) | déf(0,1,3) | déf(0,1,3) | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:A2e+V00_2e+V2e_00 | valeurs MAX | PSP 0x21D3A0 |
| `74c748` | octet retiré de $2CA (récupération d'étourdissement) | 1 × 40 | ea47bc | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:A26,27:A27+V27_00,2D:A2d,2E:A2e | valeurs MAX | PSP 0x21D3A0 |
| `74c770` | listes d'ID adverses (cas particuliers) | 2 × 40 | ea47ec | propre | déf(30) | déf(0) | déf(0) | 26:A26,27:A27,2D:A2d,2E:A2e | listes MAX ; et ids MAX dans les listes natives | à identifier |
| `74c8e0` | listes d'ID adverses (variante) | 2 × 40 | ea496c | déf() | déf(30) | déf(0) | déf(0) | 26:A26,27:A27,2D:A2d,2E:A2e | idem | - |
| `76e9fe` | paires de mots par ID adverse (projections de Rolento) | 2 × 40 | ea4ec6 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | blocs MAX | à demander |
| `95ccd0` | visage HUD, 4e variante (42 x 8, après 95cb80) | 8 × 42 | non | copie(0) | copie(39) | HORS | HORS | non vue | agrandir comme 95c8e0 / 95ca30 / 95cb80 | visages MAX (hud.json) |
| `967bf0` | mots / octets par ID à rangées (VS / carte) | 2 × 40 | eab35c | déf(0,23) | déf() | déf(0,23,38) | déf(0,23,38) | non vue | valeurs MAX | à identifier |

### 3.4 Sans objet (18)

| table | rôle | e × n | copie | $26 | $27 | $2D | $2E | lue avec un id MAX | correctif | PSP / données |
|---|---|---|---|---|---|---|---|---|---|---|
| `60d070` | classes d'effets : index = classe, pas l'id | 4 × 40 | non | copie(23,24,26) | copie(23,24,26) | HORS | HORS | non vue | - | - |
| `6102b0` | type de projectile -> routine (Maki : aucun projectile) | 4 × 40 | e80780 | propre | déf(38) | propre | propre | 2D:A2d,2E:A2e | - | - |
| `61be71` | 2e octet de 61be70 (curseur, déjà 48) | 2 × 40 | non | copie(10,39) | copie(10,38) | HORS | HORS | 26:A26+V00_26+V26_00,27:A27+V00_27+V27_00,2D:A2d+V00_2d+V2d_00,2E:A2e+V00_2e+V2e_00 | - | - |
| `628320` | natif (banque de sprites) | ? × 40 | non | - | - | - | - | non vue | - | - |
| `628370` | natif (portrait X_DATA) | ? × 40 | non | - | - | - | - | non vue | - | - |
| `628470` | natif (fichiers de pose) ; bio par la table $36FB00 à 48 | ? × 40 | non | - | - | - | - | non vue | - | - |
| `661ef0` | IA : 128 o par perso (le CPU ne joue jamais un MAX) | 128 × 40 | e821b0 | déf(2,3,5) | déf(30,31) | déf(0,32) | déf(0,32) | non vue | - | - |
| `6989e0` | IA [ID x 32 + aléa] | 32 × 40 | e9d4d4 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | - | - |
| `698ee0` | IA (variante) | 32 × 40 | e9dad4 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | - | - |
| `748ba0` | octet par coup normal (non lu : coups des MAX dans leur code) | 2 × 40 | ea07c4 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | 26:V00_26,27:V00_27,2D:V00_2d,2E:V00_2e | - | tables nulles chez MAX (session MAX) |
| `748c38` | masque par coup normal (non lu) | 2 × 40 | ea086c | déf(0,2,36) | déf(6,8,10) | déf(0,2,36) | déf(0,2,36) | non vue | - | - |
| `74c0d8` | IA scripts | 4 × 40 | ea400c | déf(0,18,20) | déf(30) | déf(0,18,20) | déf(0,18,20) | non vue | - | - |
| `74c178` | IA scripts | 4 × 40 | ea40cc | propre | déf(30) | propre | propre | non vue | - | - |
| `74c218` | IA scripts | 4 × 40 | ea418c | déf(0,18,20) | déf(30) | déf(0,18,20) | déf(0,18,20) | non vue | - | - |
| `74c2b8` | IA scripts | 4 × 40 | ea424c | déf(0,18,20) | déf(30) | déf(0,18,20) | déf(0,18,20) | non vue | - | - |
| `951ba0` | IA tirage | 2 × 40 | ea6d28 | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | déf(0,1,2) | non vue | - | - |
| `970f40` | scénarios de dialogue : index = n° de scénario ($146/$147), pas l'id | 2 × 40 | non | copie(38) | copie(39) | HORS | HORS | non vue | à prolonger pour des scénarios MAX | - |
| `97a20c` | parcours alternatif : aucun lecteur | ? × 40 | non | - | - | - | - | non vue | - | - |

### 3.5 Propres (corrigées) (65)

`60ad90`, `60b220`, `60b2d0`, `60b5a0`, `60b650`, `60b700`, `60b7b0`, `60b860`, `60b910`, `60b9c0`, `613350`, `613440`, `613490`, `614e20`, `616850`, `619b50`, `61be70`, `61bfb0`, `61c0e0`, `61c160`, `622db0`, `674c00`, `67e2a0`, `6f72b0`, `700540`, `72bdf0`, `748cf8`, `748d98`, `748e38`, `748ed8`, `748f78`, `749018`, `7490b8`, `749158`, `7491f8`, `749298`, `749338`, `7493d8`, `749478`, `749518`, `7495b8`, `749658`, `7496f8`, `749798`, `749838`, `7498d8`, `749a18`, `749c98`, `74a698`, `74b098`, `74c038`, `74c358`, `74c538`, `74c5d8`, `74c680`, `74c6a8`, `95c700`, `95c7a0`, `95c840`, `95c8e0`, `95ca30`, `95cb80`, `961af0`, `967f2a`, `97ca90`


### 3.6 Rejetées (faux positifs du balayage) (24)

`60f570`, `60f574`, `60f578`, `60f57c`, `611220`, `615720`, `615721`, `6172e0`, `617300`, `617c40`, `617ca0`, `617cd0`, `618840`, `618d68`, `619100`, `619101`, `619c80`, `623c38`, `623c40`, `6249f8`, `6487a4`, `69b830`, `9580c0`, `969e60`


## 4. Équivalent PSP et données disponibles (racine `~/.cache/sfa3max_v2_etire`, lecture seule)

| besoin | déjà converti ? | à demander (MAX.md) |
|---|---|---|
| prologue (960090) | oui, `converti/prologue_max.s` juste | — (défaut d'intégration) |
| dialogues d'avant-combat (61B580 / 61B600 / 970F40 / 61B570) | textes seuls : `converti/plXX/textes.json` « scenario_et_fin » (Eagle 27 lignes, fins comprises) | **Q7** : structure des scénarios (combats, locuteurs, ordre) |
| parcours, combat secret, décors imposés / maison (978D1C, 61B680, 61BDB0, 61B6D0, 61BE10, 61BE40) | non | **Q6** |
| carte du monde (616B30) | non (`carte_noms/` = noms seulement) | **Q8** |
| noms RESULT (97AF50) | inutile (texte ASCII) | — : blocs « #x y + 10 car. + $7F » à écrire |
| demi-largeur, jauges, étoiles, positions d'effets (748CA8, 74C6D0-74C748, 617290, 615AC0, 61AAD0, 74C3F8…) | non ; la PSP a des tables de jauges par id (0x21D3A0, index `max_psp.tsv`) | **Q9** |
| visage HUD 4e variante (95CCD0) | oui (`hud.json` / visages déjà posés dans 95C8E0-95CB80) | — : agrandir comme les 3 autres |
| réactions 34-36 (61B4A0, $23608, $28BF6) | R5 de MAX.md | déjà traité (T) |

## 5. Correctifs proposés (intégration)

1. **Prolonger à 48** (agrandit_max, AJOUTEES / MULTI) : `0x616B30` (avec la demi-table +2), `0x95CCD0`, `0x61BE40`,
   `0x61BA90` (38 entrées seulement !), `0x60B4A0` ; **rangées** `0x61B580` et `0x61B600` (3 × 48 ; la constante de
   rangée est (`$13E`−8)·20 = LSL #4 + LSL #2 : passer à ·24, ou plus simple : talon qui rend `$FF` pour un id ≥ $28
   tant que les scénarios MAX n'existent pas) — garder `0x61B650` cohérente (3e rangée de 61B600).
2. **Remplir** les entrées restées par défaut, d'abord les lues en jeu : 97AF50 (noms), 978D1C / 61B680 / 61B6D0
   (après Q6), 748CA8, 74C6D0-74C748 (après Q9).
3. **Marques de fin** : bloc_rel16 doit recevoir le bloc complet AVEC sa marque (0x960090 : 0) ; contrôle
   `outils/marques.py` après chaque construction.
4. Sans objet (S) : IA du CPU (661EF0, 6989E0, 698EE0, 74C0D8…, 951BA0), tables de coups normaux non lues
   (748BA0 / 748C38), natives 628320 / 628370 / 628470 — rien à faire tant que le CPU ne joue pas un MAX.

## 6. Limites

- Le balayage ne voit pas les index passés par un pointeur stocké ni les routines C du portage « hors carte » sans
  entrée résolue ; la différence dynamique couvre les chemins des 16 parties seulement (pas de dizzy forcé, pas
  d'attraction, pas de combat secret atteint).
- Pose finale du générique (arcade `$301FA2`, listes `$E/$F`, rang = id, jusqu'à `$3D` pour Yun/Yang) : homologue
  d'Upper non trouvé par l'analyse statique (aucune structure à listes de 40 × 8 avec ≥ 16 en-têtes) ; les scripts de
  fin MAX (`prep/tout.s`) créent bien l'acteur `$4E` aux rangs `$26 $27 $2D $2E $3D` : à suivre par l'intégration.
- Les états « déf(j) » d'octets peuvent coïncider avec la bonne valeur (ex. jauge 40 = Ryu = Eagle) : classés OK à la
  main quand la valeur MAX est connue.

## 7. Fichiers

`audit.tsv` (machine), `audit_brut.tsv`, `essais/usages.tsv`, `essais/dyn_confirme.tsv`, `essais/dyn_decouverte.tsv`,
`essais/dyn/*.esp|*.txt` (parties), `captures/*.png`, `outils/{balaye,classe,marques,dyn_analyse,annote,tableau_md,image}.py`,
`outils/file_dyn.sh`, `lance.sh`, `lua/prologue.lua`, `re_ajouts/{ro5,champs}.tsv` (12 + 5 lignes).
