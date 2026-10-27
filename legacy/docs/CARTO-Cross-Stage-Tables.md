# Cartographie des tables & du composeur de stage — Hyper SFA (z9)

> Carte unique de référence pour le **cross-stage** (perso → stage maison).
> Consolide `ANALYSE-Cross-Stage-Multi.md` (§6 v7), `LOADER-Implementation-Spec.md`,
> `CAVE-Loader-Design.md`, `stage_pack_v2_schema.md`, et une **passe de décompilation
> fraîche du 2026-08-31** (toolchain Ghidra 12.1.3 + EE reloaded réinstallée sous Linux ;
> sorties brutes : `<workspace>/tmp_hdd/out_composer_z9/`).
> Adresses = RAM EE ; dump de travail = `hyper_re/eeMemory_versus.bin` (z9 versus, base 0).

---

## 0. TL;DR — le point d'arrêt et la bifurcation

- Le décor de combat est **composé chaque frame** par une hiérarchie de machines à états
  (coroutine `FUN_296750` → composer `FUN_2518c0`). Le rendu final suit des **pointeurs data**
  (bank, source tilemap, buffers) posés par `FUN_22daa4`.
- **DEUX chemins de layout coexistent :**
  1. **CODÉ EN DUR** — `FUN_2537e0` compose le stage versus avec des **sels de page
     constants** (`0xd,0xe,0xf,0x10` SCR2 ; `0x1c,0x1d` SCR3). C'est le stage résident.
  2. **DATA-DRIVEN** — `FUN_5059f0`/`FUN_505e4c` composent depuis une **liste d'octets de
     sels de page** (ptr `SPR 0x70001110`, count `SPR 0x70001140`).
- **⟹ Décision d'archi cross-stage — TRANCHÉE (xref scan 2026-08-31) :**
  - **Chemin A = OBLIGATOIRE en combat. Écraser les pages de pool** ciblées par les sels
    durs (le composeur dur produit alors le décor Upper) — approche « staging-fix » déjà
    éprouvée (asm_v7pg v7.41).
  - **(B) rerouter vers data-driven `5059f0/505e4c` = ÉCARTÉ pour le combat** : preuve —
    ces deux fns ont **0 référence** dans le build combat (ni `jal`, ni pointeur de table,
    scan `0x100000–0x6c0000`), alors que le codé-en-dur `2537e0` est bien `jal`'d (depuis
    `0x252a34`) et `252430` est un pointeur de la table `0x5b41e8[0]`. Le chemin data-driven
    appartient à un autre sous-système (loader/preview du menu), pas au composeur de combat.
- Reste non couvert par un pack DATA : **objets/sprites animés** (serpent, taichi, feu) =
  sous-système d'émission séparé (hors pack, cf. `stage_pack_v2_schema.md` bloc E).

---

## 1. Hiérarchie d'exécution du composeur (décompilé)

```
FUN_296750  coroutine maître BG (spawnée par FUN_22ec20, entry en SPR+0x1100)
  └─ dispatch u16[0xb88000] via table 0x5b6320 (états 0-8)
       └─ état 8 = FUN_296980 → spawne la tâche composer :
            FUN_2518c0  BOUCLE COMPOSER (par frame)
              ├─ si [0xb674f8]!=0 → force état 6 (FULL RE-LAYOUT) + pose 2 octets dirty
              ├─ dispatch u16[0xb88000] via TABLE 0x5b41c0  (voir §2)
              ├─ func 0x252150  (re-clear+respawn upload si octets dirty ctx+0x62/0x63)
              └─ yield 0x22fab0
```

`SPR 0x70001114` = **pointeur base contexte** (= `0xb88000` en combat ; posé par
`FUN_22daa4` : `uRam70001114 = 0xb88000`). Les `psRam70001114[k]` du décompilé = `u16[0xb88000 + 2k]`.

---

## 2. Tables de dispatch (dumpées du binaire)

### `0x5b41c0` — composer, index `u16[0xb88000]` (9 états)
| idx | handler | rôle |
|----|---------|------|
| 0 | `0x251bf0` | init couche (pose scroll defaults, appelle 0x250630/578600/57f330) |
| 1 | `0x251c90` | → dispatch sous-table `0x5b41d8` sur `u16[0xb88004]` |
| 2 | `0x251f20` | avance + logique dirty-bit |
| 3 | `0x252390` | → dispatch sous-table `0x5b41e8` sur `u16[0xb88008]` (+ appels 511c40/5945f0/582270) |
| 4 | `0x251c90` | (idem 1) |
| 5 | `0x251f20` | (idem 2) |
| 6 | `0x251d00` | **FULL RE-LAYOUT** : avance +4, appelle **`0x284a10`** |
| 7 | `0x251d40` | check `[ctx+0x182]`, pose buffers `0xbca000` |
| 8 | `0x251dc0` | reset champs contexte, appelle 57f330 + `0x57ab50` (clear/schedule) |

### `0x5b41d8` — sous-couche, index `u16[0xb88004]` (~6 états)
`[0]=0x251d00  [1]=0x251d40  [2]=0x251dc0  [3]=0  [4]=0x252430  [5]=0x2524f0`
(au-delà = octets de la table nav suivante, pas des pointeurs.)

### `0x5b41e8` — sous-couche, index `u16[0xb88008]` (~2 états)
`[0]=0x252430  [1]=0x2524f0` (le reste = data).
- `FUN_252430` (état 0) = **builder de couches** : appelle `0x2514b0` (SCR1), `0x2537e0`
  (SCR2), `0x2525b0`, `0x252310`, puis 578600/57f330 + scroll (2525b0/252310).
- `FUN_2524f0` = **scroll par frame** (anime `ctx+0x28 -=0x100 &0x3ff` toutes les 6 frames
  via `ctx+0x16`) — PAS de recompose.

### `0x5b41b0` — SOL/rowscroll, index `u16[0xb88138]` (6 états)
`[0]=0x250b00 [1]=0x250b70 [2]=0x250c10 [3]=0x250cb0 [4]=0x251bf0 [5]=0x251c90`
→ tous mènent à `FUN_250d50` (page SOL via table `0x6452e0`, page `= [ctx+0x128]*0xa0`).

---

## 3. Composition d'une page (décompilé, format PROUVÉ)

### SCR2 — `FUN_505ab0`
- Entrée : sel de page dans `SPR 0x1124` (octet). Index pool = `(sel & 0xff) * 3 * 0x100`.
- Pool **`0x640960`** = tiles `u16[256]` (+0) ; **`0x640b60`** = attrs `u8[256]`.
  → **page SCR2 = 0x300 octets** à `0x640960 + sel*0x300`.
- Émet dans le ring des paires `{tile|0x1000, attr}` (0x400/page).

### SCR3 — `FUN_505ef0`
- Index pool = `(sel & 0xff) * 3 * 0x40 = sel*0xc0`.
- Pool **`0x643c60`** = tiles `u16[64]` ; **`0x643ce0`** = attrs `u8[64]`.
  → **page SCR3 = 0xc0 octets**. Émet `{tile, attr}` (0x100/page), sans offset +0x1000.

### Wrappers data-driven — `FUN_5059f0` (SCR2) / `FUN_505e4c` (SCR3)
```
liste = (byte*) SPR 0x70001110 ; count = SPR 0x70001140
do { compose_page(sel = *liste++) ; } while(--count >= 0)
puis *(u8*)([0x70001118]+1) = 0xff   (terminateur)
```
→ **le layout d'un stage = une simple liste d'octets de sels de page.** C'EST le levier
d'injection propre (chemin B du §0).

### Copie ring — `FUN_2517e0`
Copie 8 mots `src | 0xf000` (OR de priorité) par itération, count `SPR 0x1140`. Utilisé
par le SOL (`FUN_250d50`) et le composeur.

### ⚠️ Composeur CODÉ EN DUR — `FUN_2537e0` (SCR2 du stage versus)
N'utilise PAS la liste : appelle `FUN_505ab0` avec des **sels constants** →
`0xd,0xd,0xe,0xe,0xf,0xf,0x10,0x10` vers ring `0xba4000..0xba7400`, puis `FUN_505ef0`
sels `0x1c,0x1d` vers `0xba8000/0xba8100`, puis remplit `0xbae400` (SOL) de `0xc000c0`.
⟹ **le stage résident est baké en code** : pour un autre stage il faut écraser les pages
de pool `0xd,0xe,0xf,0x10 / 0x1c,0x1d` (chemin A) ou rerouter (chemin B).

### `FUN_284a10` (appelé par l'état 6 FULL-RELAYOUT via 251d00)
Gate `[ctx+0x181]==0` → pose `[ctx+0x182]=0xff` + **spawne la coroutine `0x280630`**
(`FUN_22f660(prio=0x100, ...)`). = (re)lancement du builder de décor.

---

## 3bis. ⭐ Énumération COMPLÈTE `{source, sels}` d'un stage (= ce qu'un pack chemin-A remplace)

Décompilé le 2026-08-31 (builder maître `FUN_252430`, état `0xb88008=0`, + sous-builders).
Pour changer le décor de combat, il faut réécrire **ces sources** (les pointeurs rendu, eux,
restent ceux de `FUN_22daa4`) :

| Couche | Builder | Source à écraser | Sels / index |
|---|---|---|---|
| **SCR2** (ring `0xba4000`) | `FUN_2537e0` → `FUN_505ab0` | **pool `0x640960`** (tiles u16[256]) + `0x640b60` (attrs) | pages **`0xd,0xe,0xf,0x10`** (0x300 o/page) |
| **SCR3** (ring `0xba8000`) | `FUN_2537e0` → `FUN_505ef0` | **pool `0x643c60`** (tiles u16[64]) + `0x643ce0` (attrs) | pages **`0x1c,0x1d`** (0xc0 o/page) |
| **SOL rowscroll L0** | `FUN_2514b0`→`2514f0` | strips **`0x65f980`** (+ `0x65f820`) → dst `0xbac000` | idx = `[ctx+0x128]>>7` |
| **SOL rowscroll L1** | `→2515a0` | strips **`0x661660`** → dst `0xbac400` | idem |
| **SOL rowscroll L2** | `→251650` | strips **`0x663a80`** → dst `0xbac800` | idem |
| **SOL rowscroll L3** | `→251700` | strips **`0x665ea0`** → dst `0xbacc00` | idem |
| **SOL pages** | `FUN_250d50` | table **`0x6452e0`** | page = `[ctx+0x128]*0xa0` |
| **SOL tables (stage-idx)** | (rowscroll) | **`0x660240`** / **`0x661e60`** | idx = `stage_sel(0xb84178) + [0xb88100]` |
| **bank tuiles** | drawer | ptr **`0x1dc2e4`** (=`0xdb4000`) | repoint (1 write) |
| **palette** | source ptr `[[0x1dc070]+0x14]` = **`0xbac000`** | 128 rangées×16 (CPS2 4444) — cf. §4bis |

Le 2ᵉ appelant `FUN_252a34` réutilise `FUN_2537e0` (mêmes sels) + setup sprites — **pas de
pages supplémentaires**. `FUN_250630` = init des 4 couches rowscroll (250670/720/7d0/880).
⟹ **La liste ci-dessus est exhaustive pour l'état de composition versus.** Un pack chemin-A
= {pages SCR2 0xd-0x10, pages SCR3 0x1c-0x1d, 4 tables de strips, tuiles bank, palette}
remplacées par celles du stage Upper (déjà extraites dans les dumps `z5_*` / `ee_z5chunli.bin`).

## 3ter. ⭐ Scroll = registre, PAS de treadmill (décompilé 2026-08-31) → chemin A scrolle

`FUN_2524f0` (handler scroll) : toutes les 6 frames (`ctx+0x16`), `ctx+0x28 -= 0x100` puis
`&= 0x3ff`. **C'est tout.** Le scroll = **offset de registre bouclant** à `0x3ff = 1024 =
largeur ring (64 tuiles × 16px)`. Le composer compose le ring **une fois au layout**
(état-machine), **aucune re-composition par frame, aucune lecture de liste pendant le scroll**.
`FUN_252150` (helper par-frame) ne re-layoute que sur **dirty-bits** (`~[ctx+0x62]&[ctx+0x63]&3`)
ou `0xb674f8` — pas un treadmill.
- ⟹ **Écraser les pools (chemin A) produit un stage qui SCROLLE** (bouclage toroïdal du ring).
- ⟹ **La prémisse d'août « un snapshot de pool figé ne scrolle pas » ne tient pas** pour le
  composer de combat : elle ne vaudrait que pour un stage **plus large que le ring** (scroll
  non-répétitif) → là il faudrait un re-layout à la frontière (mécanisme dirty-bit / état 6).
  La plupart des fonds CPS2 sont des **pavages 64×64** qui bouclent → chemin A OK. **À
  confirmer live** sur un stage à long défilement.
- ⟹ **Le pack v2 (source par-couche) n'est PAS nécessaire** pour un stage qui tient dans le
  ring : chemin A (plus simple) suffit. Garder v2 en réserve pour les stages à long scroll.

## 4. Pointeurs de rendu — `FUN_22daa4` (LA référence d'injection)

Initialiseur de stage : pose tous les pointeurs (tous en DATA, donc repointables).
| Adresse | Valeur (versus) | Rôle |
|---|---|---|
| `0xbe2100/04` | `0xba0000` | base SCR1 |
| `0xbe2108` | `0xba4000` | base SCR2 (ring) |
| `0xbe210c` | `0xba8000` | base SCR3 (ring) |
| `0xbe2110` | `0xbae000` | — |
| `0xbe2114` | `0xbac000` | SOL / staging |
| **`0xbe2180`** | **`0xb90000`** | **source tilemap** (ptr colonnes) |
| `0xbe2184/86` | `0x807d/0x2461` | params source |
| `0xbe218a/8c` | `0x40/0x10` | dims 64×16 |
| **`0xb84130..40`** | `ba0000/ba4000/ba8000/bae000/bac000` | **table buffers couches** |
| `0xb84144..54` | idem | table buffers twin |
| `0xb84158` | `0xb90000` | source tilemap (miroir contexte) |
| `0xb88030/32/34` | `0xf/0x1b02/0x3f` | dims/params contexte |
| `0xb88088` | `8` | (id build ? à confirmer vs gate `0xb84178==8`) |

Bank tuiles : struct BG **`[0x1dc078]+0x34 = 0x1dc2e4`** (vaut `0xdb4000`) — repoint = 1 write.
Descripteur source câblé par `FUN_21fcfc` : `[0x1dc078]+0xd0..0xe8 = 0xbe2180..0xbe21a0`
(+ centrage widescreen `+0x10 += [0x80000]+[0xc0000]`).

---

## 4bis. Palette — chemin complet (décompilé 2026-08-31, `FUN_1d1300`)

Convertisseur palette **par frame**, appelé par `FUN_1d0750` (master rendu BG) :
- **SOURCE = pointeur** `[[0x1dc070]+0x14]` (via `FUN_1d0e90(0)`) = **`0xbac000`** dans le dump
  versus. Data-driven ⟹ **repointable** (ou écraser en place). Format d'entrée = **CPS2
  16 bits `0x?RGB`** : nibble haut = luminosité (le conv. fait `bri=(c>>12)+0x10`), puis
  R=`(c>>8)&0xf`, G=`(c>>4)&0xf`, B=`c&0xf`.
- **CONVERSION** (`FUN_1d1300`) : par canal `out = (nibble * bri * 0x11) / 0x1f` → 0-255 ;
  assemble un `u32` GS `0x80000000 | (B<<16)|(G<<8)|R`. Boucle **0x80 = 128 rangées × 16
  couleurs**.
- **DESTINATION (work)** = `0x1dc3e0 + [0x1dc078+0x114]*0x4000` → **double-buffer** work
  `0x1dc3e0` / twin `0x1e03e0` (parité `[0x1dc078+0x114]`).
- **UPLOAD GS** = `FUN_1d36a0([0x1dc078+0x114]*4 + 0x1dbce8)` (DMA CLUT).
- ⟹ **Pour le cross-stage** : la palette Upper (même moteur CPS2, même format 4444 ; extraite
  = `chunli_pack_v2` champ `pal:0x6fa460` côté z5) se pose **telle quelle** — soit en écrasant
  `0xbac000` (par rangées, comme le staging-fix v7), soit en repointant `[[0x1dc070]+0x14]`.
- ⚠️ à confirmer live : `0xbac000` sert aussi de zone staging SOL dans `FUN_22daa4`/`2514f0`
  (rôle multiple du buffer selon sous-système) — vérifier qu'écraser la palette ne perturbe
  pas le SOL (ou cibler la source amont / repointer plutôt qu'écraser).

## 5. Sélecteur de stage & descripteur de layout

- **Sélecteur de stage = `0xb84178`** (octet ; isolé par `find_selector.py` : diff de
  savestates invariant sur 6 matchs même stage vs 3 autres). Tables indexées par lui :
  **`0x660240`** / **`0x661e60`** = `[stage_sel*? + [0xb88100]]` (strips SOL/rowscroll).
- **Descripteur de layout versus** (blob e544, data pure) `0x695ff4–0x6960a0` :
  - header u16 `0002 0002 0008 000c 0010 0010`
  - listes SCR2 (16B) : `0x696018=[0×12,4,1,2,3]`, variantes `0x696004/28/38`
  - quads scroll : `08 00 18 00 28 00 28 00`, `08 00 48 00 88 00 88 00`
  - **liste SCR3 (64B)** `0x696050 = 0e 0f 10 11 12 13 19 19 14 15 16 17 18 00…`
    (+ copie `0x696090`)
- Table catalogue preview (NON combat) : z9 `0x695ff8` (pool `0x63da20`) ;
  z5 `0x747f30` (32 stages, pool `0x69b830`).

---

## 6. Chargement (LOAD) — file framework réutilisable

- Queue `0x1a2440` (0x80 entrées × 0x40 o ; index `0x1a2454` ; flag non-vide `0x1a2450` ;
  tail `0x1a2458 &0x7f`). Entrée = `{+0:flags, +2:id1, +4:id2, +8:src, +0xc:dst, +0x10:nom}`.
- API (le cave peut les appeler ; `v0=0x1a0000`, `v1=[0x1a2458]` à poser avant) :
  - **`FUN_154b00(0, index_AFS, buf)`** = lecture SYNCHRONE d'un fichier → buf (renvoie secteurs).
  - **`FUN_154c9c(id1,id2,src,dst)`** = enqueue load + **décompresse MWo3** (flag 0x40).
  - **`FUN_148698(src,dst)`** = décompresse MWo3 (a0=src,a1=dst). poll async `FUN_155070()`.
- **Convention `file_ref = index AFS`** (prouvé : struct load `0x1dbc30+0x0c = 0x220 = e544`).
- Cave loader synchrone type :
  ```
  FUN_154b00(0, INDEX_PACKAGE, 0x1600000)   # lit le package compressé
  FUN_148698(0x1600000, 0x1580000)          # décompresse
  # parse : pools/listes → homes ; tuiles → bank ; palette → staging
  ```

> **API confirmée décompilée 2026-08-31** : `FUN_154b00` (sync read : open `128bd0` → read
> `1292e8` → poll `129bb0`==2 → close `128d28` ; renvoie `size<<0xb`). `FUN_154c9c` (enqueue :
> `[0x1a2440]+tail*0x40`, flags=1|0x40, +2:id1 +4:id2 +8:src +0xc:dst ; `0x1a2450=1` ; tail
> `0x1a2458=(tail+1)&0x7f` ; `v0=0x1a0000 v1=[0x1a2458]`). `FUN_154c1c` idem sans flag 0x40.

## 7. RAM libre & zones réservées (ne pas écraser)

- **Libre : `0x1580000–0x19d0000` = 4.4 Mo** (vide dans tous les dumps). Queue à `0x19d7000` (hors zone).
- Réservé widescreen : buffers relogés `0x1580000+`, caves zb `0x1d7e90–0x1d7f6x`.
- Réservé arcade (bake) : zone file-backed zero9 `0x5CEF00`.
- **Libre pour cross-stage (bake) : file-backed zero9 `0x5D16F0`** (+ marge slot e544 ≈ 880 o)
  ou insérer un fichier AFS dédié (comme le package 553).

## 8. Carte source z5 (Upper) ↔ cible z9 (Hyper) — pour un pack v2

| élément | z5 (SFA3 Upper) | z9 (Hyper) |
|---|---|---|
| ring SCR1/2/3 | `0xa20000/a24000/a28000` | `0xba0000/ba4000/ba8000` |
| contexte couche | `0xa08000 + L*0x400` | `0xb88000 + L*0x400` |
| descripteur scroll | `0xa62100` | `0xbe2100` |
| staging palette | `0xa2c000` | `0xbac000` |
| pool pages SCR3 | `~0x6f2xxx` | `0x643c60` |
| pool pages SCR2 | (à localiser) | `0x640960` |
| données colonnes couche | `0x76bxxx` (ctx +0x88/+0xc0) | (ctx +0x88/+0xc0) |

Champs contexte couche (v2 schema) : `+0x88..0xa0`=6 ptrs données colonnes ;
`+0xc0`=liste index (term `ff00`) ; `+0x128`=page courante ; `+0x14c/+0x150`=source/dest
courants (réutilisés par SOL, cf. `FUN_250d50`) ; `+0x14c` palette RGB source /
`+0x150` staging (selon le sous-système).

## 8bis. ⭐ z5 (Upper/SOURCE) — carto réelle & DÉSALIGNEMENT DE MODÈLE (décompilé 2026-08-31)

**z5 est un binaire distinct** (le composeur n'est PAS aux adresses z9 ; le framework compose
n'est pas partagé). Décompilé sur `ee_z5blanka.bin` :

**⚠️ z5 et z9 n'utilisent PAS le même modèle de composition :**
- **z9 (Hyper)** = 3 stages RÉSIDENTS, composés depuis des **pools de pages** fixes
  (`0x640960` SCR2 / `0x643c60` SCR3) + sels codés en dur. Pas de streaming.
- **z5 (Upper)** = beaucoup de stages, **STREAMÉS** depuis une **source par-couche**
  (colonnes `0x76bxxx`, strips, listes d'index). **z5 n'a PAS de pool de pages** équivalent.
- ⟹ **On ne peut pas copier un « pool de pages z5 » (il n'existe pas)** → le pont pour le
  chemin A = passer par le **RING COMPOSÉ** de z5 (cf. plan d'extraction ci-dessous).

**Adresses z5 confirmées cette session :**
| élément | z5 | note |
|---|---|---|
| **ring SCR2 composé** | **`0xa24000`** | `{tile\|0x1000, attr}` — format z9 (= `0xba4000` +0x180000) |
| **ring SCR3 composé** | **`0xa28000`** | `{tile, attr}` — format z9 (= `0xba8000`) |
| **palette source** | **`0x6fa460`** | CPS2 4444, format z9 identique |
| tables strips rowscroll | **`0x649030` / `0x655f48` / `0x656ce8`** | builders `FUN_25918c/25a0a0/25aca0` (= z9 `0x2514f0`…) |
| table strips SOL | **`0x6f72b0`** | builders `FUN_23a98c/23b85c` (= z9 `0x6452e0`/`FUN_250d50`) |
| contexte couche | `0xa08000 + L*0x400` | (= z9 `0xb88000`, +0x180000) |
| source colonnes / index | `0x76bxxx` / `0x76bdb0` | la vraie source décor streamé |
| pool preview/catalogue | `~0x69b830`, table `0x747f30` | **NON combat** (menu select) |

**Note** : l'offset RAM runtime **z9 = z5 + 0x180000** vaut pour les buffers (ctx, rings,
`0xa2xxxx↔0xb8/baxxxx`) mais **PAS pour les données prog** (`0x6xxxxx`, propres à chaque jeu).

### Plan d'extraction chemin A (le pont z5→z9)
1. Savestate PCSX2 d'un **stage Upper en combat** → `ee_z5<stage>.bin` (`p2s_ee.py`).
2. Grab **ring SCR2 `0xa24000`** (composé) + **ring SCR3 `0xa28000`** + **palette `0x6fa460`**.
3. **Découper** les rings en pages au format z9 : SCR2 en blocs `0x300`, SCR3 en `0xc0`.
4. **Écrire** ces pages dans les slots pool z9 utilisés par le builder dur : SCR2 `0xd-0x10`
   (`0x640960 + sel*0x300`), SCR3 `0x1c-0x1d` (`0x643c60 + sel*0xc0`) ; + palette → `0xbac000` ;
   + tuiles Upper → bank (repoint `0x1dc2e4`).
5. Le builder dur z9 (`FUN_2537e0`) compose ces pages → ring → **scrolle** (§3ter). Objets
   animés (serpent…) = hors périmètre (bloc E).

> Avantage : on part du **ring déjà composé** de z5 → pas besoin de rejouer le stream z5 ni de
> localiser un pool z5 (inexistant). Limite : le ring = fenêtre visible (OK pour stage pavé/ring-fit).

## 9. État des packages

- **v1 (package v7)** : `stage_upper_pkg.mwo3` + `stage_upper_remap.json` (tuiles+remap+tilemap
  composée) — prouvé rendable en mono-stage (savestate 10), non scalable en résident.
- **v2 (composer, par-couche)** : `chunli_pack_v2.json/.bin` (SPK2, temple Chun-Li z5,
  bloc B des 3 couches **extrait** depuis `ee_z5chunli.bin`). **NON injecté / NON testé côté z9.**

---

## 10. Prochaines étapes (méthodiques, minimisent les allers-retours)

1. ~~Trancher A vs B~~ → **FAIT : chemin A** (cf. §0, xref scan). Cross-stage combat = écraser
   les pages de pool.
2. ~~Cartographier les pages de pool exactes d'un stage~~ → **FAIT (§3bis)** : liste exhaustive
   {source, sels} = pages SCR2 `0xd-0x10`, SCR3 `0x1c-0x1d`, 4 tables de strips SOL, bank, palette.
3. ~~Palette~~ → **FAIT (§4bis)** : source `0xbac000` (ptr repointable, CPS2 4444, 128 rangées),
   conv. `FUN_1d1300`, upload `FUN_1d36a0`. **⟹ TOUT le chemin A rendu est cartographié.**
4. ~~Hook char-select → load~~ / ~~API de chargement~~ → **API confirmée (§6)**. Pour un PROTO,
   pas besoin de load AFS : embarquer les données Upper dans la section du cave (pnach `patch`
   → RAM libre) + petit cave par-frame (patron v7 = `asm_v7pg.py`, hook BG `0x1d0750`/`0x1d1848`).
5. **➡️ PROCHAINE ACTION = ASSEMBLER LE PROTO 1 stage (chemin A)** — la RE est FINIE :
   écraser pages pool SCR2 `0xd-0x10` / SCR3 `0x1c-0x1d` (+ strips SOL + bank `0x1dc2e4` +
   palette `0xbac000`) par celles d'Upper (extraites dans `ee_z5chunli.bin`/`z5_*`) → le builder
   dur compose Upper, ça scrolle (§3ter). TEST PCSX2 (`EnableCheats=true`, pnach dans
   `~/.config/PCSX2/cheats/`).

> **Cartographie RE = COMPLÈTE** (rendu §3/§3bis/§3ter/§4/§4bis + sélecteur §5 + load §6).
> Il ne reste que de l'**assemblage** (bâtir le pack Upper + le cave) et le **test live**.

> Sorties de décompilation de cette passe : `<workspace>/tmp_hdd/out_composer_z9/`
> (`composer.txt`, `handlers.txt`, `layers.txt`). Re-décompiler : `source <workspace>/env.sh`
> puis `python scripts/decomp.py <dump.bin> <va...>`.
```
