# Palettes des persos MAX : conversion validée, table moteur trouvée (pour §99 « reste : palettes »)

Note de la session MAX, 2026-10-04. Rien n'est poussé dans le dépôt. Bravo pour Eagle en garde et en marche (§99) :
ça valide banque, frames, positions et miroirs du convertisseur en conditions réelles.

## 1. Conversion PSP → module : exacte (30/30 sur Ryu)

Les 30 palettes PSP de Ryu (`pl00_e.pac`, entrée [2]) sont **identiques** aux 30 palettes du module en fichier
`0x451270`, mot pour mot :
- couleur CPS2 `[r]` = couleur PSP `[r + 1]` (r = 0..14 ; PSP [0] = transparent) ;
- composantes 5 bits → 4 bits (`>> 1`), mot `0x0RGB` ;
- **luminosité = 0** dans le module (le moteur la pose à la copie) ;
- **mot 15 = numéro de la palette dans le perso** (0..29), pas une couleur.

## 2. La table moteur : une 10e table par perso à étendre

Fichier `0x451230` (PS2 `0x641230`) = **32 décalages s16 (signés, ±32 Ko) relatifs à la table**, indexés par l'ID (`$103`) :
- Ryu (ID 0) → `+0x40` = `0x451270` ; un perso = 30 palettes = `0x3C0` octets ; IDs partagés comme ailleurs
  (`0x4000` / `0x43C0` répétés) ; fin du bloc `0x457B70` (28 persos distincts).
- Lecture (traduction `0x0062A6`, PS2 `0x45024`) : `groupe = ((ism + 1) × 2 + octet $129) × 5`, soit
  `A0 = table + table[ID] + groupe × 32` → `$14C(A4)`, puis copie de **5 palettes** (`MOVEQ #4,D7`, routine `0x235840`).
  `$133` est lu signé (`EXT.W`) : pour tomber dans les 30 palettes, ism vaut −1..1 ⟹ 6 groupes de 5 (3 ism × `$129` 0/1,
  `$129` = choix de couleur, probablement le bouton poing/pied).
- **12 sites de lecture** (rectificatif HSFA §105 ; j'en avais relevé 6 : `LEA $1505F0` [PS2 00641230]) dans la traduction (adresses 68K `0x0062AC`, `0x006506`, `0x01C8B2`, `0x02E31E`,
  `0x033D20`, `0x033DBE` de `carte_image.txt`).
- Pour `$26`–`$29` : agrandir la table (32 → 42 entrées) et ajouter 4 × `0x3C0` octets ; les décalages sont SIGNÉS
  ⟹ ±32 Ko ; table collée au bloc de Ryu ⟹ déplacer table + palettes ensemble (HSFA §105).

## 3. Fichiers prêts : `~/.cache/sfa3max/converti/plXX/`

| fichier | format | usage |
|---|---|---|
| `palettes_module.bin` | 16 mots u16 petit-boutistes par palette, `0x0RGB` + mot 15 = n° | à ranger tel quel dans le bloc du module (fork / traduction) |
| `palettes_cps2.bin` | idem avec `0xF000` et mot 15 = 0 | écriture directe dans la RAM de palettes CPS2 (banc) ; identique à `test_banc/palettes_cps2.bin` pour Eagle |

Nombre de palettes : Eagle 30, Maki 30, Yun 30, **Ingrid 48** (format différent : elle n'a pas sa place telle quelle
dans le schéma 6 groupes × 5 ; ses sprites composites utilisent les sous-palettes +0 et +1, à étudier de mon côté).

**Pour le banc** : prendre le même groupe que le moteur, `palettes[groupe .. groupe + 4]`, à la place des 5
palettes que le moteur copie pour J1 (J1 : palette 0 ; J2 : palette 5, d'après §99).

Reproduction : `sfa3max-psp-widescreen/work/re/convert/palettes_max.py` (refait la vérification sur Ryu).

## 4. Palettes d'EFFETS (2026-10-04, table `0x457B70`, HSFA §105)

- Côté PSP : bloc de **36 palettes** par perso (Ingrid 72) dans l'entrée `[6]` (section 22 en général ; repéré par
  les mots 1-14 qui ont le bit 15 = alpha PSP), **même conversion** que les palettes de perso.
- Contrôle sur les 26 persos de SFA3 : palettes **8-23 identiques au module** chez tous (484/813 au total) ;
  **0-7 en grande partie RECOLORÉES sur PSP** (aucune règle simple : ce ne sont ni des déplacements ni une fonction
  couleur → couleur) ; au-delà de 24 (Chun-Li 31, Sodom/Vega 37, Juli/Juni 30) le PSP n'a pas les mêmes.
- ⟹ Pour Eagle/Maki/Yun/Ingrid, le PSP est la seule source : 8-23 fiables, **0-7 à vérifier en jeu**.
- Fichiers : `~/.cache/sfa3max/converti/plXX/palettes_effets_module.bin` (36 palettes, format module, mot 15 = n°)
  et `palettes_effets_cps2.bin` (banc). Nombre réellement utilisé par perso MAX : inconnu (≤ 36).
