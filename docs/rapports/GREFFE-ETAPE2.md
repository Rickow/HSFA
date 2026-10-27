# Greffe du mode Arcade d'Upper dans Hyper (voie B) — étape 2 : Hyper augmenté (ro9a) jouable en Arcade

Agent « greffe_arcade », 2026-10-11. Suite de `GREFFE-PREPARATION.md` (§8).

**Périmètre.** Écritures seulement dans `work/greffe_arcade/`. Le traducteur partagé, `work/mame*` et le fork n'ont pas
été modifiés ; `max/` n'a pas été lu. MAME toujours en `nice -n 19`, `-nvram_directory`/`-cfg_directory` propres à chaque
trace (dans `traces/<nom>/`), jamais `-state`, jamais `pkill -f` (arrêts par PID). Aucun commit.

**Conventions** : celles de la préparation (`ro5` Upper, `ro9` Hyper, va MIPS en fichier, données en exéc.,
champs en numérotation PS2 : `$102` = `$0103` 68K, `$116` = `$0117` 68K = perso de base).

---

## 0. En bref

1. **Objectif atteint.** Dans Hyper augmenté, une partie ARCADE démarre depuis le menu (entrée 0), passe la sélection
   d'Hyper (Ryu ZERO 3), puis enchaîne : présentation → écran VS → **combat 1** (2 manches) → pose de victoire et
   citation d'Upper → **carte / NEXT STAGE** → VS → **combat 2** → citation → carte → VS → **combat 3**.
   - **Oracle Upper** : avec la même variante de liste (`$120`, tirée au hasard au début de partie dans les deux jeux,
     imposée par `lua/graine_pc.lua`), la liste des adversaires construite par le code greffé est **identique octet
     pour octet** à celle d'Upper : `19 0C 0D 1B 09 1C 0B 1D 01 0A` (Blanka, Dan, Sakura… comme `traces/gagne00`).
     Les trois combats joués le sont contre `$19`, `$0C`, `$0D`, dans l'ordre, à l'étape (`$114`) 0, 1, 2.
   - Sans imposer `$120`, ro9a tire sa propre variante (`06 11 19 04 09 1B 18 02 01 0A`) et la suit aussi.
2. **Ce qui bloque** : un plantage au **K.O. de la 1re manche du 3e combat** (contre `$0D`, image 5 273), dans
   l'interpréteur d'animation d'Hyper, sur un pointeur vers des données de perso d'Upper copiées (§7.3). La fin n'est
   donc pas encore atteinte. Visuels : décor d'Hyper (choix minimal), fonds des écrans d'Upper (carte, présentation)
   et couleurs des portraits faux (plans et palettes d'Upper absents de la ROM graphique d'Hyper).
3. **Place (choisie et prouvée)** : code greffé dans la **zone Z80** (fichier `[0x750, 0x22B00)`, 140 Ko) **et dans une
   2ᵉ zone hors du module** (exéc. `$1000000`, fichier `0xE10000`, 488 Ko) ; données dans un **bloc ajouté** exéc.
   `$DB0000` (1,35 Mo, trou réservé au bloc son `$E70000`) servi en 68K comme bloc externe propre **`$D10000`**.
   Témoin sans greffe identique octet pour octet ; VERSUS d'Hyper inchangé (21 sélections, 40 manches, mêmes choix).
4. **Tri des 366 modifiées** : 32 gardées chez Hyper (11 Ko), 334 copiées (170 Ko) ; la « retouche en place » se
   réduit à des patchs de constantes et de tables (§3). Plan complet : **1 758 routines greffées (614 Ko MIPS)**,
   1 167 renvoyées à Hyper, 8 natives, 3 routines synthétiques.
5. **Appels** : 0 non résolu à l'assemblage ; les natifs d'Upper vont vers les talons (chargeurs d'animation
   par site, par joueur, de fin) ou vers un natif d'Hyper sans effet.
6. **`$102 → $116`** : 33 lectures patchées dans le code greffé (24 INDEX, 9 CMP < `$28`) ; les écritures de l'adversaire CPU
   ne posent que `$102`, Hyper recalcule `$116/$117` à l'init du joueur (vérifié : `J2 19/19/10`).
7. Le défaut **`LEA table(PC,Dn)`** est livré à part, avec interrupteur : `diffs/01-leatab-ajoute.patch`.

---

## 1. Constructions figées et md5

| objet | md5 / état |
|---|---|
| ROM programme d'Hyper actuelle (`work/mame_ro9`, = `fige/ro9`) | `a37df09c86826203cbb79bf61b8c5784` |
| ROM programme d'Upper actuelle (`work/mame_ro5`, = `fige/ro5`) | `a296538feff3d9a5317b1609bfb594c0` |
| témoin Hyper refait avec la copie du traducteur (`constructions/temoin3`, bloc son + voix) | `a37df09c…` (identique) |
| témoin Upper refait avec la copie (`constructions/u5_temoin`) | `a296538f…` (identique) |
| module source d'Hyper (redirection des voix, `work/modules_son/ro9_usa_prog68k.bin`) | `dcda2bbac9751efa89122cb2f1cd0457` |
| **Hyper augmenté figé** (`constructions/ro9a_fige`, ROM `sz3ud.03c`) | `35cb58e8e04df38216805124529a4bbf` |
| module augmenté / bloc de données / `ext_d10000.bin` | `ed187d97…` / `bbeb326b…` / `60b86dad…` (`ro9a_fige/md5.txt`) |

`fige/ro5` et `fige/ro9` étaient déjà à jour (mêmes md5 que `mame_ro5`/`mame_ro9`, cartes et blocs `ext` compris).

⚠ **Le traducteur partagé a changé pendant la session** (`translate.py` 12:46, `assemble.py`/`mame_test.py`/`profils.py`
14:45 le 2026-10-11, autres sessions). Ma copie part de l'état du 2026-10-10 18:58, identique au commit `184b606` du dépôt.
Les diffs (§9) sont faits contre cette base ; le correctif LEA s'applique tel quel à l'état actuel, le diff complet
avec 2 conflits mineurs (§9).

---

## 2. Place : zone Z80 + 2ᵉ zone hors du module (point 2)

### 2.1 Disposition

| contenu | exécution PS2 | fichier du module | 68K | taille |
|---|---|---|---|---|
| code greffé, partie 1 | `$1F0750-$212B00` | `[0x750, 0x22B00)` (Z80 recompilé, jamais traduit) | code, devant celui d'Hyper | 140 208 o |
| code greffé, partie 2 + 3 talons synthétiques | `$1000000-$1077200` | `[0xE10000, 0xE87200)` (**module prolongé**) | code, à la suite | 487 648 o |
| bloc de données de la greffe | `$DB0000-$EF9000` (trou `$E70000-$E80000` = bloc son) | posé aussi à `0xBC0000` du module prolongé | **bloc externe `$D10000`** | 1 347 793 o |
| tables d'animation natives d'Upper (67 fichiers) | `$D20000` (virtuel) | — | `$37DF00` dans l'image | 261 200 o |

- **En-tête intact** (mot 3 fin du code, mot 6 fin des données) : le module est seulement prolongé (zéros puis code).
  La copie du traducteur reçoit `GREFFE_Z2=debut:fin` (décalages fichier) et traduit la 2ᵉ zone **à la suite** du code.
- Contraintes trouvées en route :
  - le traducteur lit les adresses de tables sur **6 chiffres hexa** (`T_xxxxxx`) : le bloc de données doit rester
    sous `$1000000`, et aussi sous `$FF0000`, sinon la conversion à l'exécution prend les adresses 68K de la RAM
    (`$FFxxxx`) pour des adresses du bloc (plantage au démarrage, essai a14) ;
  - aucun `lui` `$DB-$FE` dans ro9 (balayage) ; le bloc son est testé **avant** celui de la greffe et retiré de sa plage
    de conversion ;
  - le bloc de données est **aussi posé dans le module prolongé** : le traducteur y lit les tables de sauts (reconstruites
    en 68K) et les tables de valeurs hébergées dans le code (sinon : table vide, saut au hasard, essai a1).

### 2.2 Copie du traducteur (`untranspile/`)

| fichier | changement (étape 2) |
|---|---|
| `mips.py` | `GREFFE_Z2`, `zones_ajoutees()` ; `plages_module` ajoute la 2ᵉ zone |
| `assemble.py` | `assemble(..., extra=[(debut, fin)])` : plages traduites à la suite, étiquettes « dedans » |
| `translate.py` | `data_refs`/`read_jump_table` voient la 2ᵉ zone ; `GRF_Y` (bloc externe propre) ; bloc son testé d'abord ; `LEATAB_AJOUTE` |
| `mame_test.py` | clés de conversion du code et borne haute étendues à la 2ᵉ zone ; données du module bornées par l'en-tête (`FIN_FICHIER`) ; `HSFA_GREFFE_Y` → `ext_<Y>.bin` + `ext_liste.txt` ; plage de conversion en deux morceaux autour du bloc son |
| `assets_natifs.py` | profil `HSFA_GREFFE_ASSETS` (ro9 augmenté) : tables site/perso/fin d'Upper, sites d'appel des copies |

### 2.3 Preuves

- **Neutralité** : sans les variables, la copie refait Hyper et Upper à l'identique (§1).
- **La 2ᵉ zone s'exécute** : les talons synthétiques et 488 Ko de routines y sont (`greffe.json` : `zone2`, `synth`) ; les
  traces d'appels (`traces/ta_9*`) montrent leur exécution ; la partie Arcade passe par eux à chaque image.
- **VERSUS d'Hyper** sur `ro9a_fige` contre `fige/ro9` (`outils/lance_vs.sh`, `tournee_hyper.lua`, `CONTOURNE_E=1`,
  40 000 images) : **21 sélections, 40 manches, mêmes choix et mêmes états, aucune exception**. Seul écart : la pose de
  victoire de deux manches dure une image de plus ou de moins (décalage d'une image qui se résorbe) — probablement une
  image de retard due au code déplacé (à confirmer). Sur 15 000 images, journaux identiques à l'image près.

---

## 3. Tri des 366 routines modifiées (point 1) et plan de greffe

### 3.1 Homologues fiables (`etape2/homologues.py`)

Le partenaire de l'étude (`inverse_ro5`) est faux pour les petites routines semblables (aiguilleurs : `0x265120` →
`0x9A2C0` au lieu de `0x9A390`). Nouvelle correspondance par **propagation** : alignement des paires sûres, appels et
constantes appariés, **tables de pointeurs appariées entrée par entrée**, point fixe. Choix final : homologue propagé
s'il est majoritaire et au moins aussi ressemblant, sinon `inverse_ro5` (`plan.homologue`).

### 3.2 Diff par branche (`etape2/tri_modifiees.py` → `donnees/tri_modifiees.tsv`)

Alignement MIPS (cibles masquées, **déplacements A5 d'Upper relogés** avant comparaison, appels alignés comparés via
l'homologue). Marqueurs des parties non alignées : ARCADE (variable A5 propre à Upper, `$C201`, appel d'une absente,
donnée à copier), VERSION (`$D2`, `$116/$117`, variable/routine propre à Hyper), `$102`.

| | gardées chez Hyper | copiées (greffe) | mixtes |
|---|---|---|---|
| 366 modifiées du cœur | **32** (10,9 Ko) | **334** (169,9 Ko) | 0 |
| + 34 « homologue proche » vues en Arcade | 24 | 9 | 1 (`0x268AB0`, K.O. : copiée) |

Règle : ressemblance < 0,8 → copie (homologue douteux) ; sinon pas de marqueur ARCADE → Hyper ; ARCADE sans VERSION →
copie ; les deux → mixte. **Retouche en place** : la place manque pour insérer du code dans les routines d'Hyper ; les
retouches nécessaires sont devenues des **patchs de constantes et de tables** (§5) et 3 **routines synthétiques** écrites
dans la forme du recompilateur (talons). `etape2/force.py` impose 4 décisions argumentées (départ de partie, choix du
décor, init de manche, moteur des objets).

### 3.3 Fermeture (`etape2/plan.py`)

À partir des racines (lanceur, préparation du combat, scène 4, scènes 6/8/A, tâche Arcade `0x1346A0`, gestionnaires des
tables d'objets complétées), chaque routine atteinte est **GREFFE**, **HYPER** (homologue) ou **NATIF**. Ordre des
règles : imposé ; natif ; absente/sans homologue → greffe ; non vue en Arcade → homologue ; tri ; **équivalente**
(mêmes instructions, appels → mêmes décisions, données de même contenu, tables entrée par entrée, A5 non relogés) →
Hyper ; moteur/persos → Hyper ; homologue douteux (< 0,8), petite routine (< 256 o) ou vue en Arcade non
équivalente → greffe ; service partagé avec VERSUS différant **seulement par ses appels** → Hyper.

| décision | routines |
|---|---|
| GREFFE | 1 758 (absentes 209, sans homologue 31, tri 279+1, vues en Arcade non équivalentes 1 217, racines 20, imposées) |
| HYPER | 1 167 (équivalentes 418, non vues en Arcade 611, moteur/persos 55, tri 42, services 39, imposées) |
| NATIF | 8 |

Le cœur de la préparation (530) est dépassé : les écrans d'Arcade d'Upper (présentation, carte, citation) reposent sur
des objets et des aiguilleurs dont Hyper a modifié la table ou le format ; les remplacer par les siens cassait l'écran.

---

## 4. Appels non résolus et natifs (point 3)

- **Assemblage : 0 non résolu.** Chaque référence (jal, constante de code, pointeur de code d'une table copiée, y compris
  vers le **milieu** d'une routine : 909 renvoyés au même décalage chez un homologue identique) a une décision.
- **Natifs d'Upper** :

| natif | rôle | traitement |
|---|---|---|
| `0x4115A0` | chargeur de banques par perso | natif homologue `0x22B00` (banc du fork) |
| `0x407680` | — | natif homologue `0x28950` |
| `0x4112D0` | chargeur d'animation par site | appels **repatchés vers les talons** du profil `HSFA_GREFFE_ASSETS` (sites `0x25D6C0`, `0x262574` des copies) |
| `0x4113A0` | chargeur par perso (joueur) | talons par joueur (sites `0x26B640/660` + talon de fin de sélection, J1) |
| `0x4114A0` | chargeur de fin | talon de fin (site `0x272D50`), table `0x6283C0` d'Upper |
| `0x407EC0`, `0x41AB90`, `0x247A0` | sortie, divers | `0x22B00` (appel externe → RTS) |

- Profil d'animation : 67 fichiers anim d'Upper (pointeurs relatifs à `$B83800`) à `$D20000` ; banques du fork
  `constructions/<nom>/banques_hx` = celles d'Hyper + les fichiers graphiques d'Upper (paires site/perso/fin) avec
  les lignes `anim` recalculées. ⚠ `0x238E0`, d'abord choisi comme talon, est **traduit** : un appel y exécutait du code
  d'Hyper.

---

## 5. Points d'entrée (point 5)

| site d'Hyper | avant → après | rôle |
|---|---|---|
| `T_5B4210[0]` (`0x5B4210`) | `0x62FF0` → copie de `0x4E1C0` | lanceur ARCADE d'Upper (ne force pas `$A9 = 3` : J1 seul) |
| `0x4EA30` (appelé par le lanceur) | → talon `depart_arcade` | crée la **tâche Arcade d'Upper `0x1346A0`** (priorité `$40`), puis départ d'Hyper `0x63560` |
| `0x318E30` (lui/addiu, fin de sélection `0x318C40`) | `0xA43F0` → talon `fin_selection` | en ARCADE : animations du perso de J1 (chargeur natif par joueur), puis préparation du combat d'Upper `0x24EA30` (adversaire CPU, liste) |
| `T_5B5E80[2]` (scène `A5+4 = 4`) | `0x96620` → talon `scene4_mode` | `$C201 = 0` (ARCADE) → copie de `0x261560` (sous-table `T_61C200` copiée), sinon `0x96620` |
| `T_5B5E80[3/4/5]` (scènes 6/8/A) | RTS → copies de `0x2614A0` / `0x2614D0` / `0x261500` | CONTINUE, GAME OVER, fin + générique (branchés, non atteints) |
| `0x9C940` (K.O.) | inchangé | la sous-table de combat Arcade utilise la copie de `0x268AB0`, qui appelle `0x269340` |
| tables d'objets d'Hyper : `T_5C5720[13,18,19,55,72-79]`, `T_5CABD0[1]`, `T_5B5510[11]`, `T_5C6340[3]` | entrées **nulles** → gestionnaires d'Upper | objets retirés par Hyper (écrans Arcade, fins) ; le VERSUS ne crée pas ces types |

Les talons sont des mots MIPS dans la forme exacte du recompilateur (`TST.B $C201(A5)` d'Upper `0x24541C`, création
de tâche de `0x4EE20`), traduits par la chaîne normale (`etape2/greffe2.py`, `stub_*`).

---

## 6. `$102 → $116` (point 6) et données (point 4)

### 6.1 `$102`

`etape2/patch_116.py` (classement d'`audit_102.py` sur la traduction 68K, lecture MIPS retrouvée) → `donnees/patch_116.tsv` :
130 accès dans 101 routines greffées ; **33 lectures patchées** (`lb 0x102` → `0x116` dans la copie : 24 INDEX, 9 CMP à un
id de base < `$28`) ; gardés : 34 COPIE (surtout vers les objets fils `$0002(A6)`), 43 CMP registre/registre ou
pseudo-id, 9 ÉCRITURE, 11 AUTRE. Les écritures de l'adversaire CPU ne posent que `$102` : Hyper recalcule
`$116/$117` à l'init du joueur (`0x2A1630` → `0x321BA0`) — vérifié en partie (`J2 19/19/10`, `0C/0C/10`, `0D/0D/10`).
Le **rival `0xA5CA0`** n'est pas sur le chemin (Upper `0x24EA30` greffée prend `0x250700` → homologue `0xA5590`) :
non patché, à revoir avec le rival.

### 6.2 Données copiées : fermeture et bornes (`etape2/donnees2.py`)

- Départ : constantes de données des routines greffées. **Fermeture par les pointeurs** (longs alignés visant les données
  d'Upper ou son fichier de frames 390, mot bas ≥ `$200` ou constante du code ; les paires de petits mots `$0058 $006A`
  ne sont pas des pointeurs), **réutilisation** des segments identiques chez Hyper (même alignement modulo 4).
- **Bornes par la preuve dynamique** (`lua/donnees_lues.lua`, journaux `traces/u_lu00-02` : 293 184 adresses lues par
  Upper hors des manches) : un segment atteint seulement par pointeur n'est copié que s'il a été lu (fermeture
  statique complète : 1,66 Mo, trop de faux pointeurs).
- **Régions contiguës** : les tables d'animation d'Upper sont des tables de **décalages 16 bits** relatifs à la table
  (`0xC8510`) : segments voisins et lectures proches (écart < 1 Ko) copiés d'un seul tenant, au même alignement
  modulo 16 ; tous les longs des régions sont relogés.
- Résultat : 245 régions, 1,35 Mo ; 14 732 pointeurs de données relogés, 4 085 de code (+ 909 vers un milieu de routine),
  236 pointeurs RAM ; 6 681 segments réutilisés chez Hyper ; 4 332 segments jamais lus non copiés (pointeurs laissés).

---

## 7. Résultats de partie (contre l'oracle Upper)

### 7.1 Scripts

- `lua/tournee_arcade.lua` : menu (curseur `$FF4201 = 0`), sélection J1 (spécification de `tournee_hyper`), combats
  (vie de J1 maintenue, adversaire à 1), Start/bouton hors combat ; journal des états, `MANCHE` (ids, étape, décor,
  liste `$FF4B2E`), captures (`SNAPETAT`, `SNAPS`), couverture, surveillance d'écritures (`SURV`), anneau de PC
  (`TRACEPC`), pile et registres à l'exception, `BLOQUE` après 4 000 images figées.
- `lua/tournee_greffe.lua` (oracle Upper, `fige/ro5`) : + `GRAINE`, liste `$FF40C0` et ids au journal `COMBAT`.
- `lua/graine_pc.lua` : impose graine / octets (`FORCE_ADR`) à l'entrée d'une routine (ici `0x24F9D0`).
- `outils/oracle_ro9a.sh CONSTRUCTION TRACE NF` : partie ro9a avec la variante de liste d'Upper (`$120 = $32`).

### 7.2 Partie de référence `traces/or_final` (construction `ro9a_fige`)

| images | état (`A5+4/+8`) | Upper (`traces/oracle_u`) | ro9a |
|---|---|---|---|
| 408-618 | sélection | Ryu | Ryu ZERO 3 (sélection d'Hyper) |
| 619-816 | 4/0 → 4/2 présentation | | ✓ (fond faux) |
| 816-892 | 4/4 VS | | ✓ |
| 892-2886 | **combat 1** | Blanka `$19`, étape 0 | **Blanka `$19`, étape 0**, 2 manches |
| 2886-2928 | 4/8 victoire + citation | | ✓ « citation » de Ryu |
| 2928-3111 | 4/2 **carte / NEXT STAGE** | | ✓ (bandeau « BLANKA » vaincu ; fond faux) |
| 3111-3187 | 4/4 VS | | ✓ |
| 3187-4621 | **combat 2** | Dan `$0C`, étape 1 | **Dan `$0C`, étape 1**, 2 manches (PERFECT) |
| 4668-4927 | carte, VS | | ✓ |
| 4927- | **combat 3** | Sakura `$0D`, étape 2 | **Sakura `$0D`**, plantage au K.O. de la manche 1 (5 273) |

Liste au journal des deux jeux : `190c0d1b091c0b1d010a` (identique). Captures : **`traces/planche_ro9a_arcade.png`**
(sélection, présentation, combat 1 contre Blanka, SPECIAL FINISH, citation, carte NEXT STAGE, combat 2 contre Dan,
PERFECT, citation, combat 3 contre Sakura) ; écrans d'Upper : `traces/planche_entre_combats.png`.

### 7.3 Ce qui bloque / reste faux

1. **Plantage au K.O. de la manche 5 (adversaire `$0D`)** : l'objet fils de J2 (`$FFCF00`) reçoit un pointeur
   d'animation vers des données de perso d'Upper copiées (`0x840688`, atteintes par les tables `0x6139A4/0x613BA0`) ;
   l'interpréteur d'Hyper y lit un format différent (adresse `$000277`). Piste : le K.O. d'Upper copié (`0x268AB0` →
   `0x26B0B0`/`0x26B7C0`, chargeurs par perso) mélange données d'Upper et moteur d'Hyper ; soit garder le K.O. d'Hyper
   `0x9C940` en appelant seulement `0x269340`, soit renvoyer ces tables vers les données d'Hyper.
2. **Visuels** : fonds des écrans d'Upper (présentation, carte) faux — plans scroll d'Upper absents de `hsfa_plans.bin`
   d'Hyper ; couleurs des grands portraits fausses ; écran VS blanc par moments. Relève de l'étape graphique (décors,
   §7 de la préparation).
3. **Décor** : décor d'Hyper (`$100 = 4`, ZERO 3) faute des décors d'Upper (alternative minimale de `DECORS.md`).
4. **Données non lues** : 4 332 segments jamais lus par Upper dans les 3 parties journalisées ne sont pas copiés ; d'autres
   persos ou adversaires peuvent en avoir besoin → multiplier les journaux (`outils/lance_upper_donnees.sh`, ~1 min par
   partie) ou affiner la reconnaissance des pointeurs pour rendre la fermeture statique sûre.
5. Fin, CONTINUE, GAME OVER : branchés (§5) mais non atteints.

---

## 8. Outils (`etape2/`, `outils/`, `lua/`)

| outil | rôle |
|---|---|
| `etape2/homologues.py` | homologues Upper → Hyper par propagation → `donnees/homologues.pkl` |
| `etape2/tri_modifiees.py` | diff par branche, décision HYPER / COPIE / MIXTE → `donnees/tri_modifiees.tsv` |
| `etape2/plan.py`, `force.py` | fermeture du plan de greffe, décisions imposées ; tables d'objets à compléter |
| `etape2/ecrit_greffe.py`, `relogement_a5_v2.py` | ensemble greffé → table A5 recalculée (`donnees/relogement_a5_v2.tsv`) |
| `etape2/donnees2.py` | fermeture, bornes, régions et relogement des données |
| `etape2/patch_116.py` | `$102 → $116` → `donnees/patch_116.tsv` |
| `etape2/greffe2.py` | **construction du module augmenté** (zones, talons, patchs, bloc, profil d'animation, banques) |
| `outils/construit_ro9a.sh [NOM]`, `outils/cycle.sh` | construction ro9a (+ partie) ; profil = `constructions/<nom>/env.sh` |
| `outils/lance_ro9a.sh`, `oracle_ro9a.sh`, `lance_vs.sh`, `lance_upper_lua.sh`, `lance_upper_donnees.sh` | lanceurs MAME |
| `etape2/analyse_exc.py`, `ou.py`, `dis68.py`, `ptr_anim.py` | exception → instruction, chaîne d'appels, adresse d'Upper |
| `etape2/couv_ro9a.py`, `couv_manque.py`, `diff_images.py`, `debuts68.py` + `lua/trace_appels.lua`, `diff_appels.py` | **différentiel d'exécution Upper / ro9a** (couverture par état, par image, séquence d'entrées de routines) |
| `lua/donnees_lues.lua`, `lua/lire.lua`, `lua/couv_images.lua`, `lua/graine_pc.lua` | journaux de lecture, lecture de RAM, couverture par image, graine |

## 9. Diffs (`diffs/`)

- **`01-leatab-ajoute.patch`** (contre `src/hsfa/translate.py`) : `LEA T(PC,Dk),An` vers une table d'un bloc
  ajouté (son `$E70000`, greffe) n'est plus perdue ; **`LEATAB_AJOUTE=0`** = ancien comportement. Neutre sur les
  constructions actuelles (témoin Hyper identique). Corrige aussi un `TypeError` latent quand la constante manque.
  S'applique au traducteur actuel (décalage 67 lignes).
- **`02-greffe-traducteur.patch`** : toute la copie (préparation + étape 2) contre la base `184b606`
  (`src/hsfa`, chemins rétablis). Sur le traducteur actuel : 2 morceaux à fusionner à la main (`assemble.py`
  n° 1, `mame_test.py` n° 2), le reste s'applique.

## 10. Prochaines étapes

1. K.O. du 3e combat (§7.3.1), puis partie complète jusqu'à la fin (scène A, talon de fin déjà câblé).
2. Journaux de lecture d'Upper sur tous les persos (balayage des 40 fins) pour borner les données, ou reconnaissance
   des pointeurs par type de table.
3. Graphismes des écrans Arcade (plans, palettes des portraits) et décors d'Upper (plan de `DECORS.md`).
4. Rival (`0xA5CA0`, `$116`), versions non ZERO 3 en Arcade, CONTINUE / GAME OVER.
5. Mesurer l'écart d'une image du VERSUS (pose de victoire).
