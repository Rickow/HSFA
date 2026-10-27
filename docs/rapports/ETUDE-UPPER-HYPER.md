# Étude : « SFA3 Upper avec les modes d'Hyper » — base Upper (voie A) ou base Hyper (voie B) ?

Agent « étude Upper/Hyper », 2026-10-10. **Lecture seule** : rien n'a été modifié en dehors de
`<workspace>/work/etude_upper_hyper/`. Ni MAME ni PCSX2 n'ont été lancés. Calculs en `nice -n 19`.

**Conventions**
- `ro5` = Upper, `ro9` = Hyper. Adresses MIPS en **fichier** (comme `show.py`) ; données en **exéc.** (fichier + `0x1F0000`).
- Champs de structure en **numérotation PS2** (= arcade), sauf mention « 68K » (XOR 1).
- « routine » = grain fin de `carto_ro9` (`GRAIN=routine`) : 12 716 routines dans Upper, 10 168 dans Hyper.
- Tailles en octets de code **MIPS** ; « instr. » = instructions 68K produites par le traducteur (`n68` des caches).
- `o` = octets, `Ko` = 1 024 o.

**Mesure de présence (nouvelle, plus fiable que les classes de `comparaison_ro9_routine`)**
- Les classes « identique / modifiée / nouvelle » de la carto comparent des routines entières par Jaccard. Elles
  surestiment l'absence quand Hyper a redécoupé une routine. Elles sous-estiment aussi la différence : un petit talon
  (`lui ; addiu ; jalr`) est « identique » à n'importe quel autre, car les constantes sont masquées.
- J'ai donc mesuré la **couverture instruction par instruction** : fenêtres de 12 instructions MIPS, adresses masquées,
  déplacements gardés (méthode de `carto_ro9/couverture.py`). Le calcul est fait dans les deux sens.
- Par routine : **absente** si < 50 % de ses instructions sont couvertes, **modifiée** entre 50 et 90 %, **présente** à
  90 % ou plus.
- Résultat global : **90,4 %** des instructions d'Upper se retrouvent dans Hyper, et **88,2 %** de celles d'Hyper dans
  Upper.

---

## 0. En bref

1. **La voie A (base Upper + greffe d'Hyper) revient à greffer presque tout le moteur et le code des persos d'Hyper.**
   - Code d'Hyper absent d'Upper : **149 routines nouvelles** (351 Ko, 11 600 instr.) et **870 modifiées** (605 Ko,
     22 500 instr.).
   - S'y ajoutent **180 routines** presque identiques mais qui contiennent 203 `BTST $D3`.
   - Au total : **≈ 1,1 Mo de MIPS, ≈ 34 000 instructions 68K, 1 445 tests de version**. Cela remplace **≈ 800
     routines d'Upper** et demande **≈ 300 accroches** dans des routines d'Upper restées inchangées.
   - Côté données : **2,4 Mo** de zone nouvelle, 45 tables par `$102` (128 entrées), et les attaques en
     **40 octets** pour toutes les versions, ZERO 3 compris. Toutes les données d'attaque d'Upper sont donc à
     convertir.
   - Il faut enfin repasser par `$116` les **130 comparaisons et lectures de `$102`** du code d'Upper, ou passer ses
     35 tables par perso de 40 à 128 entrées.
   - Une fois ce travail fait, on a reconstitué Hyper dans Upper.
2. **La voie B (base Hyper + greffe du mode Arcade d'Upper) est 5 à 10 fois plus petite.**
   - Code d'Upper absent d'Hyper sur les chemins du mode Arcade : **≈ 98 Ko de MIPS (≈ 3 350 instr.)**, en ~90
     routines. On les trouve dans les scènes `A5+4 = 6/8/A/C`, dans les états d'entre-combats de la scène 4 et dans
     la sélection.
   - S'y ajoutent des **retouches** dans 60 à 200 routines qu'Hyper a modifiées (branches arcade coupées).
   - Borne haute, si l'on compte des objets atteints par les grandes tables : **≈ 260 Ko** (tout le code d'Upper absent
     d'Hyper, attraction et intro comprises).
   - Données : **≈ 0,1-0,3 Mo**. Ce sont les scripts de fin, les listes d'adversaires, les tables de scènes et le
     chargeur de fin, plus les fichiers de fin du disque (gfx 391-418, anim 458-485).
   - Les routines d'Upper « mortes mais présentes » dans Hyper sont rares, mais deux sont précieuses : le **rival**
     `0x24EA30 → 0xA43F0` et `0x250EA0 → 0xA5CA0`, identiques, avec sa table `0x5B61F0`.
3. **Le risque principal de B est la RAM A5.**
   - **191 variables d'Upper n'existent plus dans Hyper.** 109 d'entre elles servent au mode Arcade, dont 82 dans
     `$FF0000-$FF00FF`.
   - **Le portage d'Hyper a réorganisé la zone `$C388-$C3BC`** :
     - le bloc d'Upper `$C392-$C39D` est passé en `$C3A2-$C3AD` ;
     - les réglages du portage `$C3A7-$C3A9` sont passés en `$C3BA-$C3BC` ;
     - la routine C `0x28C30` y écrit des longs.
   - Les variables d'Upper `$C38E`, `$C391`, `$C39E`, `$C39F`, `$C3A0`, `$C3A2`, `$C3A5` et `$C3A6` tomberaient donc
     sur des octets d'Hyper. Il faut une **table de relogement A5** pour le code greffé.
   - Second risque : **≈ 27 lectures de `$102`** dans le code arcade à greffer. Elles indexent des tables à 40 entrées,
     alors qu'Hyper a des ids jusqu'à `$7F`. Il faut les passer par `$116`.
4. **MAX** : la conversion actuelle vise l'image d'Upper par va MIPS. Viser Hyper est faisable.
   - Sur 120 adresses du moteur, **98 sont dans des routines identiques** dans Hyper. Elles se résolvent en chaîne
     arcade → va ro5 → va ro9 → image d'Hyper.
   - **22 tombent dans des routines qu'Hyper a modifiées** : seuil de super, coup n de `$A0` (40 octets),
     animation par perso et ism, saisie.
   - Pièges propres à Hyper :
     - attaques MAX à **passer à 40 octets** (`+$20..$27` = 0, comportement ZERO 3) et `×32 → ×40` dans
       `psp_66ae8` ;
     - octet « type PSP » `$FF` à déplacer : il tombe sur le champ d'Hyper `$FE` ;
     - cases `$26-$29` de la grille d'Hyper = cases « ? » ;
     - 47 tables par `$116` à passer à 42 entrées.
   - **Avantage** : dans Hyper, les ids `$26-$29` sont des **places libres** dans les 45 tables à 128 entrées.
5. **Recommandation : B, sous une forme hybride.**
   - La base est le module Hyper. Le mode Arcade d'Upper y est greffé **au niveau MIPS** (« ro9 augmenté », traduit
     par la même chaîne).
   - **Upper reste l'oracle** : même code à 60 %, 40/40 fins validées. On compare la RAM et les scènes sur les persos
     ZERO 3.
   - Cela contredit la décision du §143 (« base Upper »). Les chiffres ci-dessus montrent pourquoi. Plusieurs étapes
     peuvent commencer tout de suite (§6).

---

## 1. Le mode Arcade d'Upper : où il vit (et ce qu'Hyper en a gardé)

### 1.1 Scènes (`A5+4`, table `T_61C1E0` d'Upper / `T_5B5E80` d'Hyper)

Les tables ont été relevées dans le module. Le déroulé vient de la trace d'état d'une partie Arcade gagnée avec Ryu
(`work/balayages/ro5_20261010-1320/p00.txt`, colonnes `A5+0 / +4 / +8 / +C`).

| `A5+4` | Upper (talon → corps) | Hyper | rôle (trace) |
|---|---|---|---|
| 0 | `0x261210` | `0x96330` (identique) | init du mode |
| 2 | `0x261470 → 0x2524B0` | `0x96590 → 0x316418` (aiguilleur identique 68K, sous-états joueurs nouveaux) | sélection |
| 4 | `0x261560`, `A5+8` : `T_61C200` | `0x96620`, `T_5B5EA0` | VS, combat **et tous les écrans d'entre-combats de l'Arcade** : toute la partie reste en `A5+4 = 4`, `A5+8` passant par 0→2→4→6→8→A→C→E→0 entre deux combats |
| 6 | `0x2614A0 → 0x24A480` (`A5+8`, `T_61BC60`) | **`RTS`** | non vue dans une partie gagnée ⟹ **continue / fin de partie** (hypothèse, à confirmer par une partie perdue) |
| 8 | `0x2614D0 → 0x24B050` (`T_61BC80`) | **`RTS`** | après la fin : 134 images, puis C (score / classement ?) |
| A | `0x261500 → 0x2A300` (aiguillage sur `$148(A5)`, `T_60B380`) | **`RTS`** | **fin du perso + générique** (≈ 11 800 images) |
| C | `0x270920` (natives `0x407EC0`, `0x4077C0`) | `0xA0DD0` (vestige) | sortie (29 images), puis titre |
| E | `0x261530 → 0x40CF70` | `0x965F0 → 0x2D550` (identique) | RÉSULTAT VERSUS (code C du portage) |

### 1.2 Taille du code d'Upper absent d'Hyper, par sous-arbre (`bilan_absent.py`)

Méthode des sous-arbres :
- graphe d'appels approché (`graphe.py`) : `jal`, constantes de code, tables de pointeurs ;
- aiguilleurs de haut niveau bloqués ;
- **grandes tables (> 24 entrées : par perso, par type d'objet) non suivies**.

| sous-arbre | absent (< 50 %) | modifié par Hyper (50-90 %) | présent |
|---|---|---|---|
| scènes Arcade 6/8/A/C | **47,9 Ko**, 45 r., 1 809 instr. | 38,1 Ko, 61 r., 1 354 instr. | 213 Ko |
| — dont propre à la scène 6 / 8 / A / C | 3,3 / 2,7 / 22,2 / 0,2 Ko | 2,3 / 1,9 / 15,5 / 0 Ko | |
| scène 4 (entre-combats, VS, combat) | **44,4 Ko**, 43 r., 1 349 instr. (flux de jeu arcade 22,5 Ko, moteur 14 Ko, sélection 4,3 Ko, propre à Upper 3,4 Ko) | 131 Ko, 152 r. (surtout le moteur de combat, réécrit par Hyper : on garde celui d'Hyper) | 411 Ko |
| scène 2 (sélection) | 5,4 Ko, 2 r. | 7,3 Ko, 5 r. | 26 Ko |
| scène E / 0 | 0 | 0 | 14 Ko |
| autre (attraction, intro, objets atteints par les grandes tables) | 162 Ko, 262 r. (objets et écrans 58 Ko, intro et attraction 30 Ko, code de persos 29 Ko, propre à Upper 22 Ko, flux de jeu 12 Ko) | 475 Ko | 2,5 Mo |
| **total d'Upper** | **260 Ko, 352 r., 9 123 instr.** | 651 Ko | 3,16 Mo |

Lecture :
- Le **cœur à greffer** fait environ 98 Ko (≈ 3 350 instr.) : scènes 6/8/A/C, partie arcade de la scène 4, et
  sélection.
- La part des 58 Ko d'objets à ajouter dépend des écrans d'histoire, de carte et de fin. Ces objets sont atteints
  par la table des types d'objets `0x615100`, à 122 entrées. Dans Hyper (`0x5C5720`), **63 entrées sont remplacées
  par le défaut `0x511DE0`**.
- La « fermeture » exacte se mesure mieux **à l'exécution** (§6, étape 0b).

### 1.3 Routines d'Upper identifiées sur le chemin Arcade

Adresse arcade = médiane des instructions alignées, d'après `agent_upper_ecarts/realign.pkl`.

| routine Upper | arcade | état dans Hyper | rôle |
|---|---|---|---|
| `0x2615D0` (4,1 Ko) | `$8FF6-$916C` | absente (Hyper a sa propre init `0x96690`) | scène 4, `A5+8 = 0` : init de match, variante Arcade |
| `0x269340` (6,3 Ko) | `$9CA0-$9E92` | **absente** | après K.O. (appelée par `0x268AB0` = Hyper `0x9C940`, modifiée) : enchaînement Arcade, **mène au chargeur de fin** `0x272B90 → 0x4114A0` |
| `0x24F9D0` (3,4 Ko) | `$B8CC-$B94A` | **absente** | choix de l'adversaire CPU / init de l'étape (variables `$C39F`, `$C3A5`) |
| `0x250EF0`, `0x251320` | `$BA66-$BB28` | modifiées | recherche du prochain adversaire (liste `$C0C0(A5)`, masque `$140/$144`, §125-§126) |
| `0x2519A0`, `0x251AC0`, `0x251CC0` | | absente / modifiée / identique | masque des battus sur 48 bits (BSET, BTST) |
| `0x24EA30`, `0x250EA0` | | **identiques, vivantes** (`0xA43F0`, `0xA5CA0`) | rival (table `0x5B61F0` d'Hyper, 40 entrées lues par `$102` : déborde pour les ids ≥ `$28`) |
| `0x272B90` | | modifiée | appel du chargeur de fin |

La **liste complète** est dans `upper_absent.tsv` (352 routines : zone arcade, scène, variables A5 propres à Upper).

### 1.4 IA, victoires, classements

- **IA** : elle est présente dans Hyper.
  - Le mode VS COM (option persistante « VS MODE »), utilisé par le mode Arcade PS2 (`legacy/docs/ARCADE-Hyper-SFA.md`),
    joue J2 en CPU.
  - Les tables d'IA par `$102` d'Hyper (`0x6AD614` pour le code, `0x6AD814-0x6ADE14` pour les scripts, 128 entrées)
    ont 16 à 18 scripts propres aux versions anciennes ; les autres sont partagés.
  - Ce qui manque est **la progression Arcade de l'IA** : niveau ou ism du CPU par étape (`$FF8E4C`, ECARTS §8.2),
    `$114(A5)` (n° d'étape : 30 accès dans Upper contre 9 dans Hyper), `$14C` (limite 9). Ces lectures sont surtout
    dans les routines Arcade absentes.
- **Victoires** : `$C30C/$C30D` (VERSUS) existent dans les deux jeux.
- **Classements** : ils sont absents d'Hyper.
  - `$FF23BC` (records, 6 × 35 × 16 o) : 14 accès dans Upper, 0 dans Hyper.
  - Bloc `$FF3350-$FF3A12` : 27 variables propres à Upper.
  - Scènes 8 et C.

---

## 2. Voie B (base Hyper + mode Arcade d'Upper) : liste et chiffrage

### 2.1 Code

| lot | taille | remarques |
|---|---|---|
| Scènes 6 / 8 / A / C (continue, après-fin, fin + générique, sortie) | 48 Ko absents + 38 Ko modifiés (≈ 3 150 instr.) | Talons `A5+4 = 6/8/A` à rebrancher dans `T_5B5E80` (aujourd'hui `RTS`) |
| États d'entre-combats de la scène 4 (histoire, carte / NEXT STAGE, VS Arcade, adversaire, Bison, rival) | ≈ 22-45 Ko absents + retouches de 30 à 150 routines modifiées (branches Arcade coupées par Hyper dans `0x9C940`, `0x96690`…) | La part « moteur » des 131 Ko modifiés **reste celle d'Hyper** |
| Sélection en mode Arcade | 5 Ko absents + 7 Ko modifiés | 1 joueur, J2 CPU, « nouveau challenger » ; s'appuie sur la sélection d'Hyper (versions, écran de mode) |
| Entrée ARCADE au menu | lanceur d'Upper `0x4E1C0` (homologue de `0x5B4210[0]`), tables de navigation et libellé `0x69CF70` (déjà présent) | Hyper : entrées 0-3 → VERSUS |
| Objets des écrans Arcade (histoire, carte, fins) | 0-58 Ko | 63 types d'objets d'Upper remplacés par le défaut dans `0x5C5720` |
| Chargeur de fin natif `0x4114A0` | talon (comme `assets_natifs.py`) : table `0x6283C0`, index = octet bas de D8 (§122) | Hyper n'a qu'un chargeur natif `0x22B00` |
| **Total** | **≈ 100 Ko de MIPS (≈ 3 400 instr.) + 60-200 routines à retoucher ; borne haute 260 Ko (≈ 9 100 instr.)** | |

Points d'appel vers du code qu'Hyper a réécrit (à vérifier un par un) :
- `0x9C940` (fin de manche) ;
- `0x96690` (init de match ; pose `$C178` et `$100`) ;
- le chargeur, la musique, les décors.

### 2.2 Variables A5 (`a5_compare.py` → `a5_ro5_absentes_ro9.tsv`, `a5_communes_suspectes.tsv`)

Les accès relevés suivent la méthode de `vars_a5.a5_access`. Cela donne **613 déplacements dans Upper, 437 dans
Hyper** : 422 communs, **191 propres à Upper**, 15 propres à Hyper.

| zone CPS2 | propres à Upper | utilisées par le code Arcade | remarque |
|---|---|---|---|
| `$FF0000-$FF00FF` | 82 | **82** | travail des scènes Arcade. Hyper ne les adresse pas par A5, mais sa routine `0x34EA0` (identique à Upper) lit `$FF0000/28/29/2B/40/42` en absolu, comme Upper : zone partagée, à garder telle quelle |
| `$FF0100-$FF0FFF` | 48 | 2 | surtout attraction et intro (`$FF0C24-$FF0D16`) |
| `$FF1000-$FF2FFF` | 5 | 4 | `$FF1EA0-$FF1EA4`, `$FF23BC` (records) |
| `$FF3000-$FF3FFF` | 27 | 5 | `$FF3350-$FF3A12` (records et affichage ?). Hyper utilise `$B360/$B364` tout près (à vérifier) |
| `$FF4000-$FF43FF` | 21 | 10 | **zone réorganisée par Hyper** (ci-dessous) |
| `$FF8000+` | 8 | 6 | `$000D`, `$000F`, `$001A`, `$00DD`, `$0112/3`, `$0160`, `$017A` |

**Zone `$C388-$C3BC`.** Les trois colonnes de droite donnent l'origine du déplacement dans SFA3 (vote des
instructions homologues).

| déplacement | Upper | Hyper | origine SFA3 |
|---|---|---|---|
| `$C392-$C39D` | bloc ro3 `$C190-$C19B` | — | **déplacé dans Hyper en `$C3A2-$C3AD`** |
| `$C3A7/$C3A8/$C3A9` | lecture seule (réglages du portage, 6/6/5 accès) | `$C3A8/$C3A9` = ro3 `$C196/$C197` | **déplacés dans Hyper en `$C3BA/$C3BB/$C3BC`** (mêmes comptes) |
| `$C38E`, `$C391`, `$C39E`, `$C39F`, `$C3A0.W`, `$C3A2.W`, `$C3A5`, `$C3A6` | propres à Upper (Arcade, attraction) | `$C3A2.W`, `$C3A4.W`, `$C3A6.W` écrits par Hyper | **collision** : les reloger |
| `$C388-$C398` | | longs écrits par la routine C **`0x28C30`** d'Hyper (nouvelle) | ne rien y poser |

⟹ Il faut une **table de relogement A5 « Upper → Hyper »** pour le code greffé :
- les variables communes déplacées (`$C392…` → `$C3A2…`, `$C3A7…` → `$C3BA…`) ;
- les variables propres à Upper, vers une zone libre d'Hyper, à **prouver libre** : aucun accès A5, aucune constante
  RAM, aucun effacement par bloc ;
- la règle « +`$212` » du bloc `$C190` (INDEX-HYPER §5.1) est une conséquence de ce même remaniement.

Une collision « sémantique » inverse a aussi été cherchée : un même déplacement utilisé par Hyper pour autre chose,
via les votes ro3 → ro5 et ro3 → ro9. Il n'y en a pas en dehors de cette zone. Restent 4 suspects isolés : `$0106`,
`$0140`, `$0149`, `$0163`, utilisés par une routine d'Hyper dont le partenaire d'Upper ne les lit pas.

**Champs de structure** : les champs d'Upper absents d'Hyper (`$7A-$7F`, `$105-$110`, `$134-$17C`, objets de l'Arcade
et des fins) ont **0 accès dans Hyper** (`champs_a6.tsv`). Pas de collision.

### 2.3 Identifiant perso

- Le code Arcade d'Upper indexe des tables à 40 entrées par `$102` : fins, rival, musique, décor de l'adversaire,
  histoire.
- Dans Hyper, `$102` vaut jusqu'à `$7F` hors de la sélection. C'est `$116` qui porte le perso de base.
- Comptage (`lit102.py`) : **5 + 13 + 1 = 19 lectures de `$102` dans le code Arcade absent** (scènes, scène 4,
  sélection), plus 8 dans le code absent « autre ». Il faut y ajouter les routines identiques déjà présentes et
  vivantes dans Hyper qui lisent `$102` sur ce chemin. Exemple : le rival `0xA5CA0` déborde de `0x5B61F0`.
- **Correctif** : `MOVE.B $102 → $116`, comme Hyper l'a fait sur 82 sites. Les fins et les rivaux par version
  deviennent alors ceux du perso de base, en ZERO 3.

### 2.4 Données (`donnees_b.py` → `donnees_b.tsv`)

Données d'Upper : 3,76 Mo.
- 66,6 % se retrouvent dans Hyper (fenêtres de 32 o, pointeurs masqués) ;
- **0,82 Mo non nuls sont absents** ;
- rattachement par les constantes du code :
  - 57 Ko visés par les scènes Arcade ;
  - 26 Ko par la scène 4 ;
  - 150 Ko par le reste du code ;
  - 629 Ko non visés directement : données atteintes par des pointeurs, dont l'intro, l'attraction et les attaques
    d'Upper en 32 o, remplacées par celles d'Hyper.

Tables Arcade absentes d'Hyper (exemples, exéc. Upper) :
- bloc des **scripts de fin** autour de `0x60B860` ;
- **listes d'adversaires** autour de `0x61B7A0` ;
- tables de scènes `0x61BC60` ;
- **table du chargeur de fin `0x6283C0`** ;
- tables de décor `0x70E560`, `0x7147E2` et `0x71D422` : format d'Upper, alors qu'Hyper a deux tables A/B avec
  variantes (§4).

Fichiers du disque : banques des fins **391-418** et animations **458-485**. Ils sont déjà dans la ROM graphique
étendue d'Upper (§122). Il faut les ajouter à l'étape de construction d'Hyper (`hsfa_build.py`, blocs externes du
pilote `sfa3hhsfa`).

Estimation : **0,1 à 0,3 Mo** de données du module, plus les fichiers de fin.

### 2.5 Ce qu'Hyper garde « mort »

Hyper reprend **identiques et vivantes** une partie des routines d'Arcade d'Upper :
- rival : `0xA43F0`, `0xA5CA0` ;
- masque des battus : `0xA5D40` ;
- autour : `0xA3AE0-0xA4170`.

En revanche, aucune scène Arcade, aucun continue ni aucune fin n'existe sous forme de code mort : les entrées `6/8/A`
sont des `RTS`, et la mesure « présent mais non atteint depuis le reset d'Hyper » vaut **0 octet** (au sens du graphe approché, qui sur-relie). Il n'y a donc rien
à « réveiller » : il faut greffer.

---

## 3. Voie A (base Upper + spécificités d'Hyper) : liste et chiffrage

### 3.1 Code (`couv_k9.py`, `accroches_a.py` → `hyper_a_reporter.tsv`)

| état de la routine d'Hyper par rapport à Upper | moteur | code des persos | total | `BTST $D3` |
|---|---|---|---|---|
| **nouvelle** (< 50 % couverte) | 145 Ko, 98 r., 3 994 instr. | 209 Ko, 51 r., 7 627 instr. | **351 Ko, 149 r., 11 621 instr.** | 349 |
| **modifiée** (50-90 %) | 240 Ko, 292 r., 8 244 instr. | 366 Ko, 578 r., 14 232 instr. | **605 Ko, 870 r., 22 476 instr.** | 893 |
| présente (≥ 90 %) mais avec `BTST $D3` | | | 147 Ko, 180 r. (retouches ponctuelles) | 203 |
| **total à reporter** | | | **≈ 1,1 Mo, 1 199 r., ≈ 34 000 instr. + 180 retouches** | **1 445** |

Lecture :
- « Moteur » = propriétaire « moteur » de `btst_d3.tsv`, ou routine hors des bornes du code par perso.
- Routines d'Upper **à remplacer** (partenaires des modifiées) : **798**.
- **Accroches** (appels vers une routine nouvelle depuis une routine identique à Upper) : **281 routines d'Upper,
  297 sites**.
- Sélection et écran de mode (`0x316E50`, `0x319430`, `0x31AAA0`, `0x31B890`, `0x321BA0`, `0x98DA0`) : 29 Ko,
  ≈ 850 instr. C'est la seule partie « petite » de la voie A.
- Mécaniques par version, parmi les routines citées : custom combo `0x2D1F10` (modifiée), jauge `0x3B7320`
  (nouvelle), init de combat `0x2C6BE0` (modifiée), init de manche `0x2A1630` (nouvelle), projectiles `0x2EF040`…

### 3.2 Données

- **45 tables par `$102`** (128 entrées) : ≈ 24 Ko de tables, plus ce qu'elles visent.
- **Zone nouvelle** `0x8AF140-0xB0F140` : 2,4 Mo, dont ≈ 1,3 Mo non nuls. Plus ≈ 0,25 Mo de données neuves ailleurs.
- **Attaques en 40 octets** pour toutes les versions : 15 sites `×40` dans le moteur d'Hyper. Les attaques ZERO 3
  d'Hyper = les 32 o d'Upper + 8 zéros. ⟹ en voie A, **toutes les attaques d'Upper** sont à convertir, et **tous les
  lecteurs d'Upper** (`LSL #5`) sont à remplacer par ceux d'Hyper.
- Les données ZERO 3 d'Hyper ont aussi été **retouchées** : la géométrie de Ryu a plus de boîtes de corps qu'Upper
  (INDEX §3.2). On finit par prendre la section de données d'Hyper presque entière.
- Tables d'Upper par perso (40 entrées, indexées par `$102`) : à passer à 128 entrées ou à indexer par `$116`.
  Upper a **130 `CMPI.B #,$102`**, dont Hyper a déplacé 82 sur `$116`.
- Bonus : les 3 tables d'Upper à 40 entrées lues par `$102` (`0x6AF640`, `0x6AF668`, `0x6AF6B8`) débordent déjà dans
  Hyper (bogue probable). C'est à corriger dans les deux voies.

### 3.3 Points d'accroche et risques

- **Accroches** :
  - les 798 routines d'Upper remplacées ;
  - les 281 appelants ;
  - les tables de code par perso (13 tables par `$102`, contre 40 entrées dans Upper) ;
  - la sélection : Upper `0x2524B0` = Hyper `0x316070` à l'identique 68K, mais les sous-états joueurs d'Hyper sont
    neufs.
- **Champs** : les champs propres à Hyper (`$D3`, `$116/$117`, `$69`, `$B5-$B8`, `$C7`, `$F3-$FE`, `$260-$262`,
  `$292`, `$2A2/$2A3`, `$318`, `$32F`) sont **libres dans Upper**, sauf deux points :
  - `$D2/$D3` sont écrits en mot par 3 inits d'Upper (`0x228F10`, `0x229EF0`, `0x22A530`) ;
  - `$32F` a été retiré par Upper et rétabli par Hyper (garde automatique).

  Le risque est faible côté champs, mais **fort côté sémantique** : `$123` est étendu (130 accès dans Hyper contre 11),
  et `$128` (palettes) est commun.
- **Régression** : la voie A touche le moteur de combat validé d'Upper : 40/40 fins, retours console, correctifs de
  coups des §142-§143. Tout serait à revalider.

---

## 4. Conséquences pour MAX et pour le tirage des décors

### 4.1 MAX visant Hyper (`max_vers_hyper.py` → `max_vers_hyper.tsv`)

Adresses du moteur utilisées par MAX : 120 avec va (`correspondances.tsv` + complément). L'adresse arcade `$2E700`
est déjà absente d'Upper.

| homologue dans Hyper | nombre |
|---|---|
| routine identique (dont 2 « identique 68K », 4 « déplacements ») | **98** : résolution sûre par alignement d'instructions |
| quasi identique (≥ 90 %) | 4 (`$1C206`, `$2EDA0`, `$2F770`, `$2E646`) |
| modifiée par Hyper | 10, dont **`$2ECD8`** (seuil de super, dépend de la version et de `$123` : Hyper `0x2DA4F0`), **`$2E7F2`** (coup n de `$A0`, 40 o), `$2A710` (animation par perso et ism), `$2A98C`, `$2BB5A`, `$2EB06`, `$2EF6C`, `$2F5AC`, `$1C1C8`, `$97CD6` |
| apparentée / nouvelle | 8 : **`$80B70`** (objet fils lié à l'attaque n de `$A0`), `$80E8E`, `$2E4C2` (saisi), `$2EC28`, `$2F796` ; nouvelles : `$2F52C`, `$82F20`, `$AA630` |

Ce qu'il faudrait pour viser Hyper :
1. **`convertit_max.py --module ro9`**. Chaîne : arcade → va ro5 (existant) → va ro9 (homologue, alignement), puis
   `carte_image.txt` d'Hyper. Revoir à la main les 22 routines touchées par Hyper.
2. **Alignement Hyper ↔ arcade** (pendant de `realign.pkl`) :
   - pour retrouver le typage des champs dans Hyper, en relançant `realigne.py` sur l'image d'Hyper et sa
     `carte_image.txt` ;
   - les règles de disposition (octets XOR 1, longs SWAP, `CONV_An`) sont celles du même portage. Seuls les
     15 champs propres à Hyper sont à ajouter à la table de types.
3. **Formats** :
   - attaques MAX (`A_`, 32 o) → **40 o** (`+$20..+$27` = 0 ⟹ comportement ZERO 3) ;
   - `$A0 + 32·n` → `40·n` (`psp_66ae8` et ses 4 appelants).
4. **Champs** :
   - le « type PSP » de MAX en `$FF` (identité dans l'image = octet hôte `$FE`) **tombe sur le champ `$FE` d'Hyper**
     (8 accès, code des persos) : à déplacer, par exemple dans la zone `$332-$3F3` (libre dans Upper ; à vérifier dans
     Hyper, qui utilise `$318`) ;
   - ne pas écrire `$32F` (garde automatique d'Hyper) ;
   - aucune autre collision entre les 199 champs MAX et les champs propres à Hyper.
5. **Ids `$26-$29`**. Dans Hyper ce sont des **places de remplissage** (copies de Ryu ZERO 3) dans les 45 tables
   par `$102` : on les y écrit sans rien étendre (`$117 = $10`, banque `0x5AF1B0`, MOMO `0x5AF2B0`, chargement
   `0x5AF420`, et `0x5C5300 → $26-$29`). Restent :
   - les **47 tables par `$116`** (38-40 entrées) à passer à 42 ;
   - les grilles de versions `0x5C5380/0x5C5420` (+4 lignes `FF FF FF id`) ;
   - la **grille de sélection `0x5C5650`**, où **`$26-$29` codent les cases « ? »** : à renuméroter ;
   - les pseudo-ids d'Upper `$28-$2C` (musique) et `$28/$29` (Vega, Chun-Li ID×8), hérités tels quels par Hyper.
6. **Coût** : ≈ 3 à 5 jours si l'intégration MAX sur Upper est terminée. Le convertisseur est déjà « par va »,
   donc il change de cible sans réécriture.

### 4.2 Tirage SFA2 / SFA3 des décors

- **Fait sur SFA3** (ro3, `decors_sfa2/DECOR-SFA2.md`) :
  - crochet au choix du décor du mode Arcade (`$4A428` traduit ; arcade `$4A406` : `$4AAE4[perso]×2 → $174(A5)`) ;
  - tables par décor relogées et étendues à 58 entrées (`ext_c80000`) ;
  - 58 correctifs, 1 444 o de code ;
  - décors SFA2 en `$50-$72`.
- **Voie A** : à reporter sur l'image d'Upper. Même structure que SFA3 ; Upper occupe `$40-$4E`.
- **Voie B** :
  - le **choix du décor Arcade** arrive avec le code greffé d'Upper : le crochet se pose au même endroit qu'en A ;
  - mais le **constructeur de décor est celui d'Hyper** : deux tables A `0x660240` et B `0x661E60`, index
    **`$100 + $C178`** ;
  - `$C178` tourne à chaque match (`0x96690` : `ADDQ.W #8 ; ANDI.W #$18`), ce qui donne 4 variantes ;
  - un décor SFA2 demande donc 4 entrées par table (ou `$C178` forcé à 0 en Arcade), et les 58 correctifs sont à
    refaire sur les routines de décor d'Hyper (`0x605B0`, `0x611C0`, `0x61280` : modifiées) ;
  - effort comparable à A, plus les variantes.
- À vérifier en jeu (question ouverte d'ETATS-HYPER §6) : les variantes `$C178` sont-elles des couleurs ou des
  versions ?

---

## 5. Recommandation

**Voie B, sous forme hybride : module Hyper + couche Arcade d'Upper greffée au niveau MIPS, avec Upper comme
oracle.**

**Pourquoi**
1. **Taille**. B ≈ 100 Ko de MIPS (≈ 3 400 instr.) + 0,1-0,3 Mo de données. A ≈ 1,1 Mo de MIPS (≈ 34 000 instr.)
   + 2,7 Mo de données + la conversion de toutes les attaques. Le rapport est d'au moins 5 contre 1, et plutôt 10.
2. **Nature**. B greffe une **couche de scènes** : peu de points d'entrée (5 talons de scène, 1 lanceur, quelques
   appels dans la fin de manche), un aiguillage par `A5+4/A5+8`, et des données. A greffe un **moteur** dispersé :
   1 445 tests dans 1 200 routines, dont 1 004 dans le code des persos (≈ 2 Mo, plus de la moitié du code
   d'Hyper).
3. **Convergence**. Mener A au bout revient à reconstruire Hyper dans Upper. Pour B, le moteur des versions est
   **déjà traduit et validé en VERSUS** (0 exception, pilote FBNeo `sfa3hhsfa`).
4. **Chantiers en cours** (son d'Hyper, voix SFA1/SFA2 par version, flux ADX, banques SFA1/SFA2) : ils visent déjà
   Hyper.
5. **Validation**. Upper reste l'**oracle**. Pour un perso ZERO 3 et des entrées scriptées, « Hyper + Arcade » doit
   reproduire les scènes d'Upper : même ordre des adversaires, même rival, mêmes fins. Les outils existent :
   `tournee.lua`, `balayage_fins.sh`, comparaison de RAM de l'étape A.

**Ce que B coûte en plus**
- la table de relogement A5 (§2.2) ;
- le passage `$102 → $116` dans le code greffé ;
- un mécanisme de greffe à écrire ;
- l'intégration MAX à reviser (§4.1) ;
- les défauts propres à Hyper à corriger d'abord : TRAINING (saut à `$000001`), pertes du traducteur classées.

**Forme de la greffe conseillée : au niveau MIPS** (« ro9 augmenté »).
- Les routines d'Upper à greffer sont ajoutées au module Hyper, avec leurs données, puis traduites par la même chaîne.
- Relogements :
  - `jal` vers les homologues d'Hyper (identiques pour l'essentiel) ;
  - constantes de données vers le bloc ajouté ;
  - déplacements A5 par la table du §2.2.
- Une greffe en 68K (routines prises dans l'image d'Upper) serait plus fragile : bornes de conversion des pointeurs
  PS2 (`CONV_An`) propres à chaque module, adresses d'image qui changent à chaque reconstruction.

---

## 6. Plan par étapes

**Ce qui peut commencer tout de suite.** Ces étapes ne dépendent ni des défauts d'Hyper, ni du son d'Hyper, ni de
l'intégration MAX.

- **0a. Nommer les scènes et sous-états Arcade d'Upper** (MAME sur la ROM d'Upper validée, `tournee.lua`) :
  - une partie **perdue**, pour la scène 6 (continue) ;
  - une partie gagnée, déjà tracée (`p00.txt`) ;
  - journaliser `A5+4/+8/+C` et les PC des gestionnaires (carte d'image → va).
- **0b. Fermeture dynamique**, à partir de la même trace :
  - les routines d'Upper **exécutées en Arcade et jamais en VERSUS** ;
  - croisées avec `upper_absent.tsv` et la couverture : on obtient la **liste exacte à greffer**, qui remplace les
    bornes 100-260 Ko de ce rapport.
- **0c. Table de relogement A5 Upper → Hyper** :
  - partir de `a5_compare.py` et des votes ro3 ;
  - plus une **preuve de zone libre** dans la RAM d'Hyper : accès A5, constantes RAM, effacements par bloc
    (`0x28C30`) ;
  - livrable : un TSV.
- **0d. Inventaire des données Arcade et étape de construction** :
  - tables (scripts de fin, adversaires, scènes, chargeur de fin `0x6283C0`) ;
  - fichiers 391-418 / 458-485 ;
  - illustrations d'histoire ;
  - étape `hsfa_build.py` pour Hyper (blocs externes).
- **0e. Audit `$102 → $116`** du code à greffer, et des routines vivantes d'Hyper sur ce chemin (rival `0xA5CA0` /
  `0x5B61F0`, tables `0x6AF640…`).
- **0f. Prototype du mécanisme de greffe MIPS** (outil seul, sans MAME) :
  - ajout de routines d'Upper à ro9, relogement des `jal`, constantes et A5 ;
  - assemblage à blanc avec l'outillage existant (`essai_assemblage.py`).

**Ensuite (après correction des défauts d'Hyper qui touchent VERSUS et TRAINING)**

1. **Entrée ARCADE au menu** : lanceur `0x5B4210[0]`, navigation, libellé. Scène 6 (continue) greffée en premier,
   car c'est la plus petite (≈ 5 Ko).
2. **Entre-combats de la scène 4** : adversaire CPU, liste et masque des battus, rival, Bison final, histoire, carte.
   Retouches de `0x9C940` et `0x96690`.
3. **Fins** : scène A, talon du chargeur de fin, fichiers. Puis scènes 8 et C (classements).
4. **Validation contre l'oracle Upper** :
   - persos ZERO 3 : 40/40 fins, ordre des adversaires identique ;
   - puis versions ZERO / ZERO 2 / ALPHA / EX : fin du perso de base, au moins sans exception.
5. **Tirage des décors SFA2 / SFA3** sur le constructeur d'Hyper (tables A/B, `$C178`).
6. **MAX sur Hyper**, quand l'intégration sur Upper est stabilisée : `convertit_max.py --module ro9`, attaques en
   40 o, ids `$26-$29` dans les places libres, tables `$116` à 42 entrées, grille `0x5C5650`.

**Si la voie A était malgré tout retenue**, l'ordre serait :
1. tables `$102` → 128 et `$102 → $116` dans Upper (130 sites) ;
2. attaques en 40 o (lecteurs et données) ;
3. sélection et écran de mode (29 Ko) ;
4. puis moteur et persos, routine par routine (1 200 routines).

Seule l'étape 3 donne un résultat visible tôt. Les étapes 1 et 2 sont un préalable lourd.

---

## 7. Limites de l'étude

- **Graphe d'appels approché** :
  - les tables de pointeurs sont bornées au début de la table voisine ;
  - les aiguillages par registre et les tâches créées par des données échappent en partie ;
  - les sous-arbres « sans grandes tables » excluent volontairement les tables par perso et par objet ;
  - d'où la fourchette 100-260 Ko de la voie B.
- **Couverture K = 12** : une routine « modifiée » peut l'être par Hyper pour une tout autre raison que l'Arcade
  (versions). Le tri fin des 131 Ko modifiés de la scène 4 demande la trace de l'étape 0b.
- **Scènes 6 et 8** : leurs rôles sont des **hypothèses** (continue, après-fin), à confirmer par l'étape 0a.
- **Tailles en MIPS**. Le nombre d'instructions 68K vient des caches de traduction de `carto_ro9` (antérieurs aux
  corrections des §128-§143) : c'est un ordre de grandeur.
- **Jours de travail**. Je n'ai pas chiffré en jours, faute de base fiable. À titre indicatif, et en reprenant
  l'échelle de CARTE-ro9 §6 : B ≈ 3-6 semaines de sessions, A ≈ 2-3 mois.

---

## 8. Fichiers (`<workspace>/work/etude_upper_hyper/`)

**Interpréteurs** :
- `python3` système pour les scripts sans numpy ;
- `<workspace>/venv/bin/python3` pour `couv_k.py`, `couv_k9.py` et `donnees_b.py`.

Lancer tout en `nice -n 19`.

| script | rôle | sorties |
|---|---|---|
| `voir68.py VA [FIN\|+LONG]` (`MODULE=ro5\|ro9 MEMMODE=cps2`) | traduction 68K seule d'une plage | — |
| `table.py MOD EXEC N [l\|w\|b]` | vidage d'une table de données | — |
| `graphe.py` | graphe d'appels approché (`succ`, `petit` = sans grandes tables) | `graphe_ro5.pkl`, `graphe_ro9.pkl` |
| `atteint.py`, `chemin2.py MOD DE VERS [bloqués]` | atteignabilité, plus court chemin et nature des arêtes | — |
| `inverse_ro5.py` | correspondance Upper → Hyper par routine (classes de `comparaison.py`) | `inverse_ro5.pkl` |
| `couv_k.py` / `couv_k9.py` | couverture K = 12 d'Upper par Hyper / d'Hyper par Upper ; bilan de la voie A | `couv_k.pkl`, `couv_k9.pkl`, `bilan_a.pkl`, **`hyper_a_reporter.tsv`** |
| `arcade_upper.py`, `zones_upper.py` (`CLE=petit`) | scènes Arcade d'Upper, sous-arbres par scène | `arcade_upper.pkl/.tsv`, `zones_upper*.pkl` |
| `va_arcade.py` | routine Upper → adresses arcade (`realign.pkl`) | `va_arcade.pkl` |
| `bilan_absent.py` | code d'Upper absent d'Hyper, par zone arcade et par scène | **`upper_absent.tsv`**, `bilan_absent.pkl` |
| `supprimees.py`, `zones_arcade.py`, `compare_tables.py T5:T9` | première méthode (classes Jaccard, plus grossière) ; comparaison des tables de code entrée par entrée | `upper_supprimees.tsv` |
| `plage.py DEB FIN` | routines d'Upper d'une plage : état dans Hyper, scènes, variables A5 propres | — |
| `a5_compare.py` | variables A5 : présence, collisions | **`a5_ro5_absentes_ro9.tsv`**, **`a5_communes_suspectes.tsv`**, `a5.pkl` |
| `lit102.py`, `champ_sites.py MOD DEP…` | lectures de `$102` ; sites d'un champ | — |
| `donnees_b.py` | données d'Upper absentes d'Hyper, rattachées aux routines | **`donnees_b.tsv`** |
| `sous_arbres9.py`, `accroches_a.py` | sous-arbres d'Hyper ; accroches de la voie A | `sous_arbres9.pkl` |
| `max_vers_hyper.py` | adresses MAX → homologues dans Hyper | **`max_vers_hyper.tsv`** |

**Ordre de relance** :
1. `graphe.py`
2. `inverse_ro5.py`
3. `arcade_upper.py`
4. `CLE=petit zones_upper.py`
5. `a5_compare.py`
6. `va_arcade.py`
7. `couv_k.py`
8. `bilan_absent.py`
9. `couv_k9.py`
10. le reste
