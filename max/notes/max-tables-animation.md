# Tables d'animation PAR COUP des persos MAX ($2B0/$2B4/$2B8/$2BC) : trouvées et exportées

Note de la session MAX, 2026-10-04. Rien n'est poussé. Outils : `sfa3max-psp-widescreen/work/re/convert/tables_anim.py`
(+ `convert_max.py`, qui écrit maintenant `animations.json`).

## 1. Où elles sont côté PSP

- Entrée `[6]` du conteneur `plXX_e.pac` : **l'en-tête (67 u32) donne des décalages RELATIFS à `0x208`** (début des
  données). Le moteur PSP pointe `objet + 0x1A0` sur `&T[3]` :
  `T[3]` = `$2B0`, `T[4]` = `$2B4`, `T[5]` = `$2B8`, `T[6]` = `$2BC`, `T[7]` = table des jeux de boîtes (`$88`),
  `T[10]` = octets par coup normal et par ism (≈ ta `0x48D178`).
- Chaque table = **u32 = numéro de pas** dans un réservoir commun (script = `[6] + 0x208 + 10 × n`), fin `0xFFFFFFFF`.
- Pas PSP de 10 o `(durée, drapeau, frame, 1, index de boîtes)` → pas du module :
  - **contrôle = (drapeau << 16) | durée** (ex. `0xFF000004`, `0x01000004`) ; fin de script = bit 15 (reprise) **ou
    bit 14** (`0x4001`…`0x4004` : fin avec enchaînement) ;
  - **mots A, B, C = l'entrée de 12 o de la table des boîtes** (`T[7] + 0x208`).

## 2. Validation sur Ryu (module `0x48DA78`, ism 0)

| table | entrées module / PSP | contrôle identique | mots A/B/C identiques (pas) |
|---|---|---|---|
| `$2B0` | 75 / 64 | 63/64 | 229/229 |
| `$2B4` | 49 / 50 | 48/49 | 409/409 |
| `$2B8` | 48 / 48 | 48/48 | 174/174 |
| `$2BC` | 34 / 37 | 34/34 | 222/222 |

**Les numéros d'animation sont les mêmes des deux côtés** (index n PSP = index n module ; décalage testé : 0 seul).
Frames : 149 animations identiques (limite = la correspondance de frames PSP ↔ module, 360/417).
Une seule série côté PSP (pas 3 ism) : les 3 séries du module sont égales sauf `$2BC` en ism −1 chez Ryu.

## 3. Fichiers prêts : `~/.cache/sfa3max/converti/plXX/animations.json`

```
{"$2B0": [{"n": 0, "pas_psp": 0, "steps": [{"ctl": 0x…, "frame": <index frames.json>, "A": …, "B": …, "C": …}, …]}, …],
 "$2B4": […], "$2B8": […], "$2BC": […]}
```
| perso | `$2B0` | `$2B4` | `$2B8` | `$2BC` | lisibles |
|---|---|---|---|---|---|
| Eagle (pl26) | 48 | 50 | 48 | 30 | 176/176 |
| Maki (pl27) | 48 | 77 | 48 | 34 | 207/207 |
| Ingrid (pl29) | 53 | 68 | 48 | 34 | 203/203 (frames renumérotées après fusion haut + bas) |
| Yun (pl28) | 57 | 129 | 48 | 38 | 272/272 — tables et scripts dans l'EBOOT (ajout du même jour, cf. §5) |

- `$2B0` PSP est plus courte que celle du module (Ryu 64 contre 75, Eagle 48) : les numéros manquants sont à remplir
  (copie de Ryu ?) si le moteur les appelle.
- Pour l'injection : écrire chaque script en pas 5 × u32 `(ctl, ptr frame, A, B, C)` + la table de décalages u16, et
  pointer les 3 ism de `0x48DA78[$26]` sur la même série.

## 4. Corrections de mes sorties précédentes

- `sections/sNN.bin` étaient décalés de `0x208` (corrigé ; réexportés pour les 4 persos).
- Mots de collision : le 3e mot de l'entrée de boîtes = mot C (avant : seulement A/B). `scripts.json` /
  `scripts_eboot.json` ont maintenant `C`, mais gardent l'ancien `ctl` (sans drapeau ni bit 14) : **utiliser
  `animations.json`** pour l'injection. Table des boîtes = `T[7] + 0x208` pour tous (Yun : non, cf. ci-dessus).

## 5. Yun (ajout, même jour)

- L'init de chaque perso recopie un gabarit de 39 mots de l'EBOOT dans `objet + 0x1A0` (Ryu `0x23F8FC`, Yun `0x2AD6DC`).
  Chez Ryu les 12 premiers mots sont à 0 (remplis depuis `[6]`) ; **chez Yun les 4 premiers sont les tables**
  (`$2B0` `0x2A9EC4`, `$2B4` `0x2A9FA8`, `$2B8` `0x2AA244`, `$2BC` `0x2AA1AC`) : tables de pointeurs vers des scripts
  rangés dans l'EBOOT, même format de pas.
- Ses jeux de boîtes sont en tête de `[6]` (`+0x208`, 1 203 entrées, ce qui couvre ses index jusqu'à 1 202).
- `animations.json` de Yun : 272/272 lisibles ; 2 pas visent une frame hors bornes (à vérifier).

## 6. `$2B0` plus courte côté PSP : comment compléter (mesure sur les 32 ID du module)

- Entrées 48-63 du module : surtout des **copies des entrées 44 ou 45** (ex. n° 55 : 45 chez 17 persos, 44 chez 11,
  propre chez 3) ⟹ remplissage.
- Entrées 64 et au-delà : variables (64 = copie de 0 chez 22 persos ; les suivantes sont souvent propres au perso,
  et ma borne de longueur côté module peut déborder sur les données suivantes chez certains ID).
- Proposition : compléter `$2B0` des persos MAX jusqu'à la longueur de Ryu en recopiant l'entrée 45 (48-63) puis 0 (64)
  et, au-delà, les entrées de Ryu ; à affiner si ton banc montre quels n° de `$2B0` le moteur appelle vraiment.

## 7. Reprise des scripts (correction importante, même jour)

- Le champ en `+6` d'un pas PSP (que je prenais pour une constante « 1 ») est l'**écart signé vers le pas suivant**
  (0xCFDE0 : `pas + 10 × écart`). Pour un dernier pas à bit 15 (reprise), la cible est `dernier + écart`.
- Validé sur Ryu contre les pointeurs de reprise du module : **166/166**.
- **La plupart des reprises ne repartent PAS au début** (Eagle : 24 sur 112 seulement ; souvent écart 0 = le dernier
  pas se répète).
- `animations.json` (4 persos) a maintenant un champ **`reprise`** = index du pas cible dans le script (ou `null`).
  Pour écrire le pointeur de reprise après le dernier pas : adresse du script + 20 × `reprise` (en 68K natif) /
  équivalent module.
- Disposition d'un pas en 68K natif : note `max-pas-68k-natif.md`.
