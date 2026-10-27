# Frames de sprites de l'Anthology (SFA3, `ro3`) — format retrouvé via Ryu (2026-10-03)

Réponse au point ouvert d'HSFA (HANDOFF §45/§75 : « format converti, à retrouver »). Méthode : pierre de Rosette Ryu
(PSP `pl00` ↔ vidage PS2 `ee_std` ↔ module `ro3` ↔ ROM CPS2), sans toucher au banc MAME.

## Format (CORRIGÉ le 2026-10-03 par la note HSFA `hsfa/work/notes/frames-anthology-emetteur.md`)
Lu dans la routine d'affichage traduite, puis vérifié ici sur le module. Les frames sont rangées **au mot près**
(adresse paire, parfois ≡ 2 mod 4) et commencent par un **u16 TYPE** (saut par la table `0x58BC30`).

```
Frame de type 2 (14 420 frames ; format de tous les sprites de persos) :
  u16 type = 2
  u16 T    = nombre total de tuiles 16×16 = Σ largeur×hauteur  (budget de la liste d'objets ; 38 467/38 467 vérifiés)
  u16 n−1
  bourrage jusqu'au multiple de 4 suivant (la routine fait A0 ← (A0+3) & ~3)
  u32 pos  → fichier 289 (0xA04000) : n × (s16 dx, s16 dy), décalages en pixels depuis l'origine du perso
  n × (u16 code, u16 attributs CPS2)   code LOCAL à la banque du perso
           attributs : bits 8-11 largeur−1, 12-15 hauteur−1, 5 miroir H, 6 miroir V, 0-4 palette
Frames vides d'un seul mot : types 0x12, 0x18, 0x1A, 0x1C, 0x1E. Autres types (00, 04-10, 14, 16) : note HSFA.
Blocs : tuile (i, j) d'un objet = code + i + 16·j.
```
⚠️ Ma première lecture (u32 alignés) voyait un en-tête « aux moitiés parfois échangées » : **artefact de
désalignement**. Ex. : la garde de Ryu est en `0x4DB32A`, pas `0x4DB328` (frame vide de type `0x12`).

**Pour écrire les frames des persos MAX** : type 2, `T` à jour, pointeur 289 réaligné sur 4 ; frame vide `0x0012`
disponible pour les pas invisibles.

## Validation
- **Vidage `ee_std`** : liste d'objets du joueur 1 (Ryu en garde, `0x910000`) = frame `0x4DB32A`
  (codes 10, 1, 5, 9, 6 ; blocs 1×1, 4×3, 1×1, 1×2, 3×3) ; positions écran retrouvées pour les 5 objets
  avec origine (160, 216) et miroir horizontal.
- **PSP ↔ Anthology** : 417 frames PSP de Ryu comparées (tuiles → code CPS2 par contenu → numéro local e258) :
  **360 identiques (86 %)**, 393 ≥ 0,9. Les écarts = frames retouchées/ajoutées par les versions console.
- ⟹ les frames PSP sont un ré-encodage SANS PERTE des frames d'origine : convertir celles d'Eagle, Maki, Yun,
  Ingrid dans ce format est mécanique (1 case PSP de 32×32 = 1 objet bloc 2×2 si sa banque range ses 4 tuiles
  en `b, b+1, b+16, b+17`).

## Animations (2026-10-03, première passe)

**Anthology** — deux formats de scripts :
- **principal (3 865 scripts, tous persos)** : pas de **5 mots de 32 bits** =
  `(contrôle, pointeur d'enregistrement de frame, mot d'attributs/collision, 0xd0020000, 0)` ;
  contrôle = octet haut : numéro d'étape (parfois), **bit 15 = dernier pas**, **octet bas = durée** (`0xFF` = tenue).
  Après le dernier pas : un **pointeur de reprise** (boucle). Ex. `0x4d83fc` : frames PSP 172-175-174-173.
- **compact (paires)** : `(pointeur de frame, contrôle)` ou `(contrôle, pointeur)`, même mot de contrôle —
  ex. `0x4db2c0` (cycle frames PSP 0 / 453 / 454, durées 2-1-2-1…, fin `0x8001` + pointeur de reprise).

**PSP (entrée [6] du conteneur, bloc « données de perso »)** : en-tête de 4 mots de 16 bits puis pas de **5 mots de
16 bits** = `(durée | 0x8000 si dernier, drapeau, numéro de frame PSP, 1, index de collision)` ; fin `0x80FF` —
**même convention** que l'Anthology. La même entrée [6] contient aussi des tables recopiées de la ROM arcade de Ryu
(`0x100260` → offset 0x3796 en mots convertis : groupes de 4 mots = **boîtes de collision** probables ; `0x100080`
→ 0x4910 en octets).

**Correspondance (Ryu, refaite avec le format corrigé)** : 3 814 scripts Anthology ; 175 scripts PSP de Ryu entièrement
identifiés en frames ; **59 ont le même enchaînement** qu'un script Anthology ; durées identiques dans 64 des 115 paires
(plusieurs candidats Anthology par script PSP, dont ceux d'Evil Ryu qui partage les frames de Ryu). Écarts = retouches de
durée (16 vs 12…). Le format « compact en paires » est **à revérifier** à la lumière de la note HSFA.

## Collisions (2026-10-03)
- **Champ 5 d'un pas PSP = index dans une table de jeux de boîtes** : entrée `[6]` + `0x2994`, **12 octets par entrée**
  (u32, u32, u32 le plus souvent 0). Les deux premiers mots sont **identiques octet pour octet** aux mots 3 et 4 des pas
  de l'Anthology : pour les **123 index PSP observés, 123** valent une valeur de l'Anthology (103 la plus fréquente ; les
  autres = Evil Ryu, mêmes frames, autres boîtes). Ces mots sont des **numéros de boîtes**, pas des géométries.
- **Tables de géométrie** : identiques aussi. Entrée PSP `[6]` `0x37A0..0x48B0` = module `0x49054C..0x49165C`
  (mots 68K en petit-boutiste, = ROM arcade `0x100260…`, groupes de 4 mots) et `[6]` `0x4910..0x4AD0` = module
  `0x490360..0x490520` (octets, ROM `0x100080…`). Des pointeurs du module visent `0x490520` / `0x490354` depuis
  `0x48D678…` : table par perso probable, **à caractériser** (c'est là qu'un nouveau perso se branchera).
- ⟹ **Conversion d'un pas PSP → pas Anthology** : (durée | 0x8000 si dernier, pointeur de la frame convertie,
  table[col].mot0, table[col].mot1, 0) ; et les tables de géométrie du perso MAX se recopient **telles quelles**.

### Structure de l'entrée PSP [6] (bloc « données du perso »)
Début = **sommaire de sections** : u32 offsets aux index 1-50 (zéros = absentes). Ryu : 49 sections. Comparées au module
Anthology (morceaux de 16 o retrouvés tels quels) :
| sections | contenu probable | identique au module |
|---|---|---|
| 3-6 | scripts d'animation (pas de 5 × u16) | 0 % (propre PSP) |
| 7 (3 576 o) | contient la table des jeux de boîtes (`+0x208` = `0x2994` chez Ryu) | ~1 % |
| **9, 10, 11, 17, 18, 19** | tables arcade, dont la **géométrie des boîtes** | **100 %** |
| 12, 13, 14, 20, 22, 25 | tables arcade partiellement modifiées / pointeurs | 34-85 % |
| 1, 8, 15, 16, 21, 23-50 (28 × 264 o) | propres au PSP (IA ? commandes ?) | 0 % |

**Eagle a le même sommaire que Ryu** (49 sections, mêmes index) ⟹ même lecture, mêmes recopies. Ingrid et Guile : 53
sections (4 de plus), à traiter au cas par cas.

### Points de branchement côté moteur (module ro3)
**9 tables par perso de 32 pointeurs** (une entrée par ID `$00`–`$1F` ; signature : Evil Ryu = Ryu, Juli = Juni = Cammy)
en `0x48D678`, `0x48D6F8`, `0x48D778`, `0x48D878`, `0x48FCF8`, `0x48FD78`, `0x48FDF8`, `0x48FE78`, `0x48FEF8` →
tables de collision du perso (Ryu : `0x490520`, `0x490354`, `0x4902E0`, `0x491670`, `0x492E68`…). Aucune n'est visée par
un pointeur en données (le code les charge par adresse constante). Pour `$26`–`$29` (base Upper : tables plus longues),
il faudra les **déplacer et les étendre**, puis corriger leurs adresses dans le code traduit. D'autres tables par perso
(index 16 bits, animations, IA) échappent à cette signature : recensement à compléter.

**Reste** : relier chaque section PSP à sa table moteur (via les 9 tables ci-dessus) ; champs des mots A/B des pas
(question posée à HSFA) ; format « compact en paires » à revérifier.

## Outils
`rosetta_ryu.py` (tuile PSP → code CPS2 → local e258), `anth_frames.py` (lecture des enregistrements, dépliage des blocs),
`frame_map.py` (frame PSP ↔ enregistrement Anthology, cache `frame_map_ryu.pkl`).

## Upper (ro5) — `frame_map_ro5.py` (2026-10-04)
- Frames de type 2 du module ro5 (15 984), positions dans le bloc externe `$B04000` du banc ro5 d'HSFA
  (`ext_b04000.bin`, **mots gros-boutistes**), codes locaux → ROM via `banques/f355.bin` (banque de Ryu d'Upper).
- 391 frames PSP de Ryu appariées (ro3 : 360) → `~/.cache/sfa3max/frame_map_ro5_ryu.json`.
- Les 5 frames du test introuvables par la règle « ro3 + $D75EC » : garde 0x5B28A6/0x5B28D8/0x5B290C/0x5B2944,
  accroupi 0x5B5420.
