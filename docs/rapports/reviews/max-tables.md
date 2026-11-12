# Inventory of the tables indexed by a character id in Hyper + Arcade, for the MAX characters (2026-11-12)

**Summary (English).** Inventory, by static analysis of Hyper + Arcade ro9a37 (Hyper + Upper's copies + stubs), of
every table indexed by a character id, to prepare the arrival of the MAX characters in the graft (finding X2 of the
graft review). Agent `tables_max`; workshop `<workspace>/work/tables_max_greffe/`.
- **Deliverable**: [tables-max-ids.tsv](tables-max-ids.tsv) (210 tables, 19 columns: side, Upper address, Hyper
  homologue, shape, coverage of the MAX ids `$26 $27 $28 $29 $2D $2E`, readers, index, value in Upper MAX, what to set,
  risk). In the repository copy, the values longer than 4 bytes (table entries, 54 on 9 lines) are masked as `<N o>`
  (no game data); `tools/reviews/max-tables/maitre.py` rebuilds the full file from the user's data, byte for byte.
- **Findings**: the reference list is Upper MAX's (`agrandit_max.py`, 137 tables extended to 48 entries); 69 tables are
  read by an Upper copy with an id (the ro9a38 agent had 15), 41 of them read outside the table or the wrong row for a
  base id `$28-$2F`; on Hyper's side 136 tables (50 by `$102`, 47 by `$116`), 71 of 40 to 45 entries overflow; rule to
  take from Upper MAX: entries 40-44 keep the bytes that followed (Upper's pseudo-ids), the MAX characters go to 45 / 46
  (`$2D` / `$2E`); why id `$2E` blocked the map (`T_967F2A`).
- **Status**: X2 is not in ro9a38 (code behind `X2_TABLES=0`, journal §223). **Open**: decision on the ids and on the
  values of `T_BASE[$26,$27,$2D,$2E]`; add the 41 tables to `X2_LISTE`; 7 lines "to confirm" (§7); bench trial
  `essais/x2_complet.sh` not run; Hyper's 71 tables when the MAX characters enter the fights.
- **Tools kept**: [`tools/reviews/max-tables/`](../../../tools/reviews/max-tables/) (`croise_upper_max.py`, `maitre.py`,
  `lib_idx.py`, `notes.py`…; about 20 s).

---

## Original text (French, kept as is)

> Kept as written in the workshop. Only changes: personal paths written `<workspace>/...`, workshop folders written `<workspace>/work/...`. Paths such as `outils/…`, `sorties/…`, `essais_demain/…`, `constr/…` are relative to the review's workshop folder (above); the tools kept are in `tools/reviews/` (see the summary).

# Inventaire des tables indexées par un id de perso — Hyper + Arcade (ro9a37), pour l'arrivée des persos MAX

Agent `tables_max` (sfa3ha), 12/11. Analyse statique seule : aucun émulateur, aucune construction, rien écrit hors de ce
dossier. Livrable principal : **`TABLES.tsv`** (210 lignes, une par table ; 19 colonnes).

## 1. En bref

1. **La liste de référence existait déjà : c'est celle d'Upper MAX.** `agrandit_max.py` agrandit 137 tables par ID
   d'Upper à 48 entrées, et la construction est validée au banc (56 bancs). Je l'ai reportée dans ro9a37.
2. **69 tables sont lues par une copie d'Upper avec un id** (58 tables d'Upper copiées, 11 tables d'Hyper). L'agent
   ro9a38 en avait 15. Sur les 54 autres, 41 lisent hors table ou une mauvaise rangée pour un id de base `$28-$2F`.
3. **Côté Hyper : 136 tables** (50 par `$102`, 47 par `$116`, le reste par un id dérivé ou non suivi). 71 sont des
   tables de 40 à 45 entrées qui débordent pour `$28-$2F`, dont 4 lues par `$102` et la grille de sélection.
4. **Règle à reprendre d'Upper MAX** : les entrées 40-44 d'une table agrandie restent les octets qui la suivaient
   (pseudo-ids d'Upper), les MAX sont en 45 / 46 (`$2D` / `$2E`). Recopier l'entrée `$00` en `$28-$2F` casse les pseudo-ids.
5. **`$2E` et la carte** : dans `T_967F2A`, l'entrée `$2E` de la liste 3 tombe sur l'entrée unique de la liste 5 (§6).

## 2. Méthode : cinq filets croisés

| Filet | Source | Outil | Ce qu'il apporte |
|---|---|---|---|
| 1 | Liste d'Upper MAX : `<workspace>/work/agent_integration_max/banc_max55/max_agrandies.txt` (137 tables) + 13 tables traitées à part (`max_journal.txt`) | `outils/croise_upper_max.py` → `sorties/croise_upper_max.txt` | Chaque table d'Upper par ID, sa copie ou son homologue dans ro9a37 (`greffe.json` : `regions`, `donnees_reutilisees` ; `homologues.tsv` ; `<workspace>/work/agent_hyper_index/tables_homologues.json`), et tous ses lecteurs |
| 2 | Index d'Hyper : `agent_hyper_index` (`tables_102.json` 45 tables, `scan_tables102.json` 91 tables) | repris dans `outils/maitre.py` | Tables d'Hyper par `$102` et par `$116` |
| 3 | MIPS de ro9a37 (Hyper + copies + talons) | `outils/lib_idx.py` (moteur de `<workspace>/work/revue_greffe/outils/index_tables.py` + journal des écritures et des sites de constantes), `outils/scan2.py`, `outils/propage_id.py` | Tout accès « constante + index » dont l'index contient `$102`, `$116` ou un champ qui reçoit un id |
| 4 | Forme des tables lues par le code | `outils/forme40.py` → `sorties/forme40.txt` | Tables de 40 ou 48 entrées absentes des filets 1-3 (117 candidates, triées par index) |
| 5 | Données seules, sans le code | `outils/entetes40.py` → `sorties/entetes40.txt` | Tous les en-têtes de 40 décalages (1er mot `$50`) : trouve les tables atteintes par pointeur |

Fusion : `outils/maitre.py` (≈ 15 s) + corrections à la main `outils/notes.py` → `TABLES.tsv`.

Suivi des flux d'id (`sorties/propage_id.txt`) : champs qui reçoivent `$102` ou `$116` sans calcul. Retenus :
`$132` / `$133(A5)` (gagnant), `$146(A5)`, `$C330(A5)`, `$FE23(A5)` (talons), et dans les objets `$3A` (propriétaire),
`$03` (139 écritures par le code des persos), `$5E`, `$160` du joueur. La propagation au-delà du 1er rang n'est pas
fiable (le décalage `$00` d'une structure quelconque capte tout) : elle n'a pas servi à conclure.

### Contrôles de la méthode
- Les 15 tables de l'agent ro9a38, trouvées par essais, sont toutes dans l'inventaire. 14 viennent du filet 1 ;
  `T_7251a0` n'est pas dans `max_agrandies.txt` (Upper MAX la traite par un talon, `talon_selpal`) : c'est le filet 5
  qui la donne, et le filet 4.
- Décodage des valeurs d'Upper MAX contrôlé sur le journal : `T_61C0E0[$26,$27,$2D,$2E]` = `26 27 24 25`,
  `T_61BE10` = `08 07 21 00` (décors maison 8, 7, 33, 0), `T_61C160` = identité.
- Le filet 3 seul trouve 85 tables par `$102` / `$116` ; 79 étaient déjà dans les filets 1 et 2.

## 3. Chiffres

| Groupe | Tables | Débordent pour `$28-$2F` (en-têtes de 40 compris) | Structure à listes | Dans la table |
|---|---|---|---|---|
| Lues par une copie d'Upper | 69 | 54 | 8 | 7 |
| Hyper seul | 136 | 71 | 4 | 61 |
| Talons de la greffe | 5 | 0 | 0 | 5 |

Les ids `$26` / `$27` sont dans toutes les tables de 40 entrées : pas de débordement, mais un contenu de remplissage
(Ryu, Juli ou 0) à remplacer.

Tables lues par les copies et absentes de la liste de l'agent, par risque (liste nominative : colonne `risque`) :

| Risque pour un id de base `$28-$2F` | Tables |
|---|---|
| Plantage ou blocage probable (pointeur ou décalage hors table) | 14 |
| Rangée suivante lue (constante de rangée `$28` → `$30`) | 5 |
| Valeur fausse hors table | 11 |
| Zéros lus hors table (pas de plantage, valeur à poser) | 11 |
| Aucun débordement (48 entrées ou plus, ou index qui n'est pas un id) | 12 |
| À confirmer (famille des projections, lecteurs directs) | 1 |

Correction de mon premier message au coordinateur (il annonçait 43 tables, 17 en « plantage ») : `T_f7cd10` (U `0x700540`, palettes d'effets) a un en-tête de
136 décalages indexé par le n° de palette, pas par l'id : aucun débordement. `T_14fef10` (U `0x967BF0`) est une
structure à rangées (4 constantes). `T_5c5f90` porte des paires de mots, pas des pointeurs.

## 4. Les familles de tables

### 4.1 Tables d'Upper copiées, lues par les copies (58)
- **Fins** (9 tables, `0x60B220` … `0x60B9C0`) : 44 entrées (41 + 3 nulles), index `$1C9(A5)`. `$2D` / `$2E` lisent le
  début de la table suivante : pointeurs faux. `$28-$2B` lisent une entrée nulle ou celle d'un pseudo-id.
- **Acteurs de fin** : `0x619B50`, `0x72BDF0`, `0x749338`, `0x749838` lues par `$7E` de l'acteur (id d'objet). Les
  entrées 40-45 de `0x619B50` sont d'autres acteurs.
- **Carte, face-à-face, victoire** : `0x616B30` (départ sur la carte), `0x614E20` puis `0x67E2A0` (citations, par
  pointeur), `0x616850`, `0x966740`, `0x967BF0`, `0x967F2A`, `0x648BC8`, `0x7251A0`, `0x960090`, `0x978D1C` (parcours),
  `0x61BBC0`, `0x61BD60`, `0x61BE10` / `0x61BE40` (décor maison), `0x613350` (musique, 45 entrées).
- **Tables à rangées** : `0x616130` (2), `0x616850` (2), `0x61B580` (3), `0x61BA10` (3), `0x967BF0`. Un id `≥ $28` lit
  la rangée suivante. Les constantes de rangée et leur sort dans ro9a37 : `sorties/constantes_rangees.txt`.
- **Moteur de coups** : `0x697FE0`, `0x6989E0`, `0x698EE0` (32 o par perso). `0x697FE0` est lue avec `id & $1F` dans
  Upper lui-même ; Upper MAX passe le masque à `$3F` et ajoute les lignes `$20-$2F`.
- **Tables non indexées par l'id mais à compléter** (`rel16n`) : `0x960180`, `0x966740`, `0x970F40`, `0x9719C0`,
  `0x971CC0`, `0x683C28`, `0x68DC72`, et `0x60D070` (classes d'effets, index = type d'objet).

### 4.2 Tables d'Hyper lues aussi par des copies (11)
`T_62eba0` (poses des portraits, 11 lecteurs copiés), `T_63b5a4`, `T_697ed0` (noms / bandeaux), `T_5c5230` (base de
voix, 6 lecteurs copiés), `T_5c5f90`, `T_5c7bd0`, `T_5c59a0`, `T_5b6030` (décor imposé, 2 rangées), `T_5c5240` (48),
`T_5c5650` (grille d'Upper, 64 cases), `T_63b6ec`. Les prolonger demande de rediriger aussi les lecteurs d'Hyper, ou
de garder deux tables.

### 4.3 Tables d'Hyper par `$102` (id étendu, `$00-$7F`)
- 39 tables de 128 entrées : les ids MAX y ont déjà une entrée, remplie comme Ryu. 13 sont des tables de **code**
  (`0x6A59D4` … `0x6A7894`, `0x6AD614`) : il faut y poser les routines du perso.
- 4 tables de 40 octets lues par `$102` : `0x6AF640`, `0x6AF668`, `0x6AF6B8` (déjà signalées par l'index d'Hyper) et
  **`0x5C6480`, nouvelle** (Hyper `0x33412C`). `$2D` / `$2E` y lisent hors table.
- `0x5B61F0` (rival, 40 + 8 zéros), `0x6A7C94` / `0x6A7D54` (48 entrées), `0x6AEA14` / `0x6AEE14` (index `$102 − $40`,
  versions ZERO 2 : les MAX n'y passent pas).
- Tables natives : `0x5AF1B0` (banque de sprites), `0x5AF2B0` (MOMO), `0x5AF420` (id de chargement), 128 entrées.
- `T_BASE` `0x5C5300` et `T_VER` `0x5C2490` : c'est `T_BASE[$26,$27,$2D,$2E]` qui décide de tout le reste. Tant qu'il
  vaut `$00`, aucune table par `$116` ne déborde et le perso MAX est Ryu partout.

### 4.4 Tables d'Hyper par `$116` (perso de base) : 40 entrées, comme Upper
47 tables vues directement, plus les homologues des tables d'Upper MAX : géométrie et jauges (`0x6AF5F0`, `0x6AF618`,
`0x6AF690`, `0x6A5784`), marche et sauts ZERO 3 (`0x6A8214` … `0x6ABA14`), objets et effets (`0x6AE014`, `0x6AE214`,
`0x6AE414`, `0x5C5BA0`, `0x5C5DE0`, `0x5C6110`), moteur de coups (`0x63ACB4` … `0x63D7EC`), HUD (`0x6A1D40` …
`0x6A2310`).
- **Grille de sélection `0x5C5380`** : 40 lignes de 4 o, lignes `$26` / `$27` nulles. La grille « Start » `0x5C5420`
  la suit : `$28-$2F` y lisent les lignes `$00-$07`. Les deux sont à prolonger ensemble.
- **Famille atteinte par pointeur** : `T_6a73d4[$116 du lanceur]` vise 30 sous-tables (`0x6B1DEA` … `0x8A108E`), chacune
  avec un en-tête de 40 décalages par `$116` de l'adversaire. Aucun outil fondé sur le code ne les voyait.
- `0x5C5510` (1 = perso de SF2, mode EX), `0x5C9580` / `0x5C97D0` (index `$116 + D1`), nouvelles.

### 4.5 Tables des talons de la greffe (5)
`T_D4` (`$FE0000`), `T_TIR` (`$FE1000`), copies de `T_BASE` et de `T_VER`, `T_D4A`. 128 entrées, pas de débordement.
`T_D4` a encore Yun en `$28` et Ingrid en `$29`. Les copies de `T_BASE` / `T_VER` sont refaites à la construction.
Les adresses de `T_BASE`, `T_VER` et `T_D4A` sont déduites de `greffe3.py` (`_adr_tir`), non relues dans le bloc.

## 5. Que mettre pour les MAX

Colonne `valeur_upper_max` : entrées `$26`, `$27`, `$2D`, `$2E` et celle de Ryu, lues dans
`banc_max55/ext_e80000.bin`. Trois cas, colonne `a_mettre` :
- **valeur d'Upper MAX** directe (octets, mots, positions) : reprise telle quelle ;
- **pointeur vers un bloc MAX** (code du perso, animations, fins, palettes) : la valeur n'a de sens qu'avec le bloc ;
  à défaut, l'entrée `$00` ;
- **à décider** : tables propres à Hyper, sans équivalent dans Upper MAX (grilles, `T_BASE`, banques natives, tables
  par `$102` des versions).

Les valeurs des tables à en-tête et des structures ne sont pas extraites (« bloc Upper MAX ») : elles sont dans
`integre_max.py` (`ajout`, `bloc_rel16`).

## 6. Pourquoi l'id `$2E` bloquait la carte

`T_967F2A` (copie `T_14ff24a`) a un en-tête de 9 décalages : `$12`, `$E2`, `$292`, `$3D2`, `$512`, `$542`, `$54A`.
Les listes 2 et 3 (`$292`, `$3D2`) ont 40 entrées de 8 o, une par perso. L'objet du joueur sur la carte prend
`liste + id × 8` (copie `0xE64AAC` ← Upper `0x198EDC`, routine `0x19DD00` ; `D1 = $116 << 3`).

| id dans la liste 3 | Adresse lue | Contenu |
|---|---|---|
| `$28-$2D` | `$512-$541` : les 6 entrées de la liste 4 | `08 … → animation` valide (sprite faux) |
| **`$2E`** | `$542` : l'entrée unique de la liste 5 | **`FF 40 00 00 → 0x9692D4`** (durée `$FF` au lieu de `$08`) |
| `$2F` | `$54A` : liste 6 | `08 00 00 00 → 0x969354` valide |

Seul `$2E` tombe sur une entrée d'un autre genre. La suite (pas `$34(A6)` nul, boucle sans fin en Upper `0x1992E8`,
`ADD.W D0,$16(A6)` tant que négatif) est le relevé de l'agent ro9a38 par sonde d'écriture ; je ne l'ai pas refait.
Upper MAX note le même piège (`agrandit_max.py`, `STRUCTS` : « `$34` nul → boucle infinie »).

## 7. Cas douteux et limites

- **7 lignes « à confirmer »** : `T_5b6b08`, `T_5ba6d0` (index `$3A` d'un objet : propriétaire ou sous-type ?),
  `T_5c1a40` (`$5E`), `T_ddb770`, `T_ddee80`, `T_dea3d0` (48 entrées, sans débordement), `T_f105de` (famille des
  projections d'Upper : 4 copies prennent une sous-table par son adresse, index non suivi).
- **24 lignes « probable »** : vues par un seul filet. La taille des tables d'Hyper sans homologue est une borne haute
  (distance à la constante suivante).
- **36 tables lues par les copies ont un index non suivi** (registre reçu en argument). Elles sont retenues parce
  qu'Upper MAX les agrandit ; le champ d'origine de l'index n'est pas prouvé ici.
- **Non couvert** : le code natif du portage (lectures de `0x5AF1B0`, `0x5AF2B0`, `0x5AF420` reprises de l'index
  d'Hyper, pas relues) ; les comparaisons en dur avec un id (`CMPI #$28`, seuil des cases « ? » d'Upper MAX) ; les
  tables de son du pilote ; les 14 en-têtes de 128 décalages d'Hyper sans lecteur vu (`sorties/entetes40.txt`).
- **Tables indexées par le décor** `$100(A5)` (40 décors : `0x707D10`, `0x70E560`, `0x7147E0`, `0x71D420`, `0x740B70`,
  `0x747F30`…) : écartées, l'index n'est pas un id. Elles comptent si un MAX reçoit un décor nouveau.
- Les routines d'Upper renvoyées à leur homologue d'Hyper lisent la table d'Hyper : une table d'Upper copiée sans
  lecteur copié n'a pas de ligne. **Deux trous** : `0x613440` (n° de son par perso, cri de K.O.) et `0x61B600`
  (scénarios de dialogue, 2) ont leurs lecteurs renvoyés à Hyper, et je n'ai pas identifié la table homologue d'Hyper.
  `0x683C28` (répliques) et `0x97A20C` (parcours alternatif) n'ont aucun lecteur vu.

## 8. Essai proposé

`essais/x2_complet.sh` (non lancé, à relire) : 05c sur les quatre ids (≈ 4 min), banc des fins avec `X2_TABLES=1`
(≈ 25 min, 6 places), sonde de lecture différentielle `$00` / `$2E` (≈ 3 min).

## 9. Fichiers

| Fichier | Contenu |
|---|---|
| `TABLES.tsv` | l'inventaire |
| `outils/maitre.py`, `outils/notes.py` | fusion et corrections à la main |
| `outils/lib_idx.py` | moteur d'exécution symbolique (copie étendue de celui de la revue) |
| `sorties/croise_upper_max.txt` | chaque table d'Upper MAX et ses lecteurs dans Upper et dans ro9a37 |
| `sorties/scan_102_116.txt`, `sorties/scan_derives.txt` | accès par `$102` / `$116` et par champs dérivés |
| `sorties/propage_id.txt` | champs qui reçoivent un id |
| `sorties/forme40.txt`, `sorties/entetes40.txt` | filets par la forme |
| `sorties/constantes_rangees.txt` | constantes de rangée d'Upper MAX et leur sort dans ro9a37 |
