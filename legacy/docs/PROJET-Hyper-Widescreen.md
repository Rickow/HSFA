# Projet — Hyper Street Fighter Alpha (PS2) : Widescreen 16:9

> Investigation widescreen pour **Hyper Street Fighter Alpha** (Anthology PS2,
> SLUS-21317). Démarrée en s'appuyant sur les 2 projets jumeaux :
> **SFA3 MAX (PSP)** et **SFA3 CPS2 (FBNeo/Android)**. Statut : **reconnaissance**.

---

## 1. L'insight stratégique (issu du projet CPS2/FBNeo) — DÉTERMINANT

Le widescreen CPS2 dans FBNeo (`d_cps2.cpp`) = **17 lignes**, en pratique **une
seule** : changer la largeur du driver `384 → 448` (et l'aspect 4:3 → 16:9) :
```c
&CpsRecalcPal, 0x1000, SFA3_SCRW /*448*/, 224, 16, 9   // au lieu de 384,224,4,3
```
Commentaire capital de ce patch :
> « Le décor existe déjà dans la tilemap au-delà de 384px → **aucun patch ROM** »

**Conséquence pour HSFA PS2** : HSFA = mêmes données graphiques CPS2 (Anthology
contient les ROMs CPS2). Donc **l'art de fond existe déjà au-delà de 384px**, à
l'inverse total du cas PSP. Le widescreen PS2 devrait donc être « gratuit » :
il « suffit » d'élargir la **largeur de rendu / fenêtre visible** du port, sans
ajouter de tiles ni patcher l'art.

### Contraste avec le projet PSP (à NE PAS rejouer)
Sur **SFA3 MAX PSP**, l'art des calques BG était **4:3 par construction** (mesuré :
~31 colonnes, pile la couverture 384px). Élargir révélait des **trous noirs** aux
bords (art inexistant) → il a fallu un long RE du pipeline (drawers tilemap,
streamer d'anim, cull des décors peints, scissor GE) + une voie ré-injection de
tiles. **Ce chantier-là ne devrait PAS se reproduire ici** SI l'hypothèse « art
CPS2 déjà large » tient. C'est la **première chose à vérifier**.

---

## 2. Cible & environnement

| Élément | Valeur |
|---|---|
| Jeu | Hyper Street Fighter Alpha (Anthology PS2) |
| Serial / CRC | SLUS-21317 / 72CE7A78 |
| Nature | logique + **rendu** CPS2 recompilés/portés en MIPS R5900, sortie **GS** |
| Émulateur | PCSX2 (a un **débogueur GS** + dump GS — clé pour ce projet) |
| Dump | `E:\CLAUDE CODE\hyper_re\eeMemory_versus.bin` (32 Mo EE) |
| Outils RE | capstone (r5900 via skipdata), pyghidra (cf. projet PSP) |

CPS2 natif = **384×224** (= `0x180 × 0xe0`). Scissor GS = taille−1 →
`SCAX1=383=0x17f`, `SCAY1=223=0xdf`.

---

## 3. Reconnaissance statique faite (2026-06-15)

Recherche d'immédiats dans le code `0x100000..0x700000` :

| valeur | sens probable | hits | verdict |
|---|---|---|---|
| `0x180`=384 | largeur playfield | 95 (addiu) | trop nombreux, à filtrer |
| `0x1c0`=448 | largeur 16:9 | 71 | — |
| `0x1e0`=480 | largeur alt | 14 | — |
| `0xc0`=192 | **demi-largeur** (centrage/cull) | 303 | analogue PSP (centrage+cull ±192) |
| `0x17f`=383 | clamp X max | **3** | 3 sites zone 0x577 = **clamp coordonnée [0,383]** (UI/caméra), PAS le scissor GS |
| `0xdf`=223 | clamp Y max | 1 | `if(v1==0xdf)` dans un switch d'IDs → **fausse piste** |
| float 384.0f (`lui 0x43c0`) | (PSP utilisait ça) | 0 | le PS2 est **entier**, pas float |

**Sites `0x17f`** (clamp à 383 via scratchpad 0x70001124/1128/1150, zone 0x577xxx
= cluster UI/init proche de `0x57f2e0`) :
- `0x57761c` : `s2=0x17f` puis `subu v1,s1,s2` + compare → clamp `s1` à 383.
- `0x5776f4` : `if (*0x70001150) *0x70001124 = 0x17f` (clamp haut).
- `0x57da64` : `*0x70001128 = 0x17f` (pose une borne max = 383) avant `jal 0x57db50`.
→ Ce sont des **clamps de coordonnée** (curseur/caméra dans l'espace 384), donc
candidats « visible width » MAIS pas le scissor GS lui-même.

**Scissor GS empaqueté** (`017f0000 / 00df0000`) : **introuvable en template
statique** → le scissor est construit dynamiquement (GIF packet monté à la volée),
pas un blob constant. Le mot `0x017f0000` apparaît 41× (probables valeurs de
registres GS éparses).

**Conclusion recon constantes** : insuffisant seul. MAIS la lecture des **paquets
GIF A+D** dans le dump (registres GS écrits en RAM) a payé :

### ⭐ Architecture GS révélée (paquets A+D dans `eeMemory_versus.bin`)
Recherche des entrées `[valeur64][adresse_registre64]` (script : balayage 8-octets) :

**SCISSOR_1** (valeurs les plus fréquentes) :
- `01bf0000 027f0000` → **640×448** = framebuffer d'**affichage** (sortie PS2 4:3).
- `00ff0000 03ff0000` → **1024×256** = **buffer de travail** (le BG composé).

**FRAME_1** (FBW = largeur/64) :
- FBW=10 → **640px** (display).
- FBW=16 → **1024px** (buffer de travail) — concorde avec le scissor 1024×256.

**XYOFFSET_1** : `00006c00`/`00007200` (= 1728/1824 px en .4 fixe) = offsets de
centrage GS.

### Implication majeure (feasibility)
Le BG est **composé dans un buffer 1024 de large**, PAS borné à 384 au rendu. Donc
la limite 4:3 n'est PAS le scissor de rendu (déjà 1024) mais **la fenêtre de ~384px
de ce buffer qui est présentée vers le display 640×448** (quad texturé : UV/XY du
blit de présentation). **→ Widescreen = élargir cette fenêtre de présentation**
(montrer ~448px du buffer 1024 au lieu de 384), exactement l'esprit FBNeo. Pas de
scissor de rendu à toucher, pas d'art à ajouter (le buffer 1024 contient déjà le décor).

**Lead TEX0** : un buffer texture **TBP=`0x2bc0` TBW=6 (=384px de large)** apparaît
dans les paquets TEX0 (512×256 / 1024×1024) → candidat = le playfield présenté en
**384px**. (Les tiles persos = TBP `0x3d80`, 8/16/32px.) `TBW=6` = la signature
exacte de la largeur 384 à élargir côté présentation. À confirmer par l'ordre des
draws (GS dump live).

**Cible RE n°1 = le code de PRÉSENTATION** (le sprite/quad qui blitte une région du
buffer 1024 vers le framebuffer 640, et la **caméra** qui fixe la largeur de monde
visible à 384). À trouver via : (a) GS dump PCSX2 (voir le TEX0 pointant le buffer
1024 + les UV du quad de présentation), (b) la chaîne caméra (demi-largeur `0xc0`=192,
clamps `0x17f`=383).

---

## 4. Modèle mental du rendu (à confirmer)

Le port PS2 doit, par frame :
1. Calculer la **caméra** (X/Y de scroll dans le monde du stage) — logique CPS2.
2. Dessiner les **calques BG tilemap** CPS2 (4 plans) + sprites → GS.
3. Borner le rendu au **playfield 384×224** (scissor GS) puis afficher en 4:3.

Pour le 16:9, 3 leviers (par ordre de propreté, transposés de FBNeo) :
- **(A) Largeur de fenêtre visible** : la valeur qui dit « on montre 384px du
  monde ». L'élargir à 448/480 → plus de monde visible (= ce que fait FBNeo).
  C'est le levier ROI. Probablement lié aux clamps `0x17f`/demi-largeur `0xc0`.
- **(B) Scissor GS** : élargir `SCAX1` 383→447 pour ne pas couper le rendu élargi.
- **(C) Cull de sprites/objets** : bornes `±192 (0xc0)` → `±224` pour ne pas
  faire disparaître les persos/objets près des bords élargis (cf. PSP : cull
  `−32≤x<416`, demi-largeur 192). 303 sites `0xc0` → audit nécessaire.
- **(D) Aspect / DISPLAY GS** : sortie en 16:9 (étirement écran). PCSX2 a aussi
  des « Widescreen patches » génériques (souvent juste un stretch — à éviter seul,
  il déforme ; on veut montrer PLUS, pas étirer).

---

## 4bis. ⭐ CANDIDATS CONCRETS (scans ciblés 2026-06-15) — shortlist à tester

Recherche des couples **384 (`0x180`) + 224 (`0xe0`)** proches dans le code : **3
paires uniquement, toutes dans `0x14axxx`** (zone setup rendu, distincte de l'UI).
Ce sont les **dimensions de rendu** du playfield. Fonctions confirmées :
- `FUN_14a550(w=384, h=224, psm)` : calcule **FBW = (w+63)/64 = 6** (= largeur
  framebuffer en unités de 64px) → écrit un descripteur de render-target dans la
  table `0x19e400`. **384/64=6 = exactement le `TBW=6` de la texture playfield
  `0x2bc0`** ⇒ le playfield CPS2 est rendu dans un **buffer 384px de large**.
- `FUN_14a740(w=384, h=224)` : calcule les **offsets de centrage** `(0x1000−dim)/2`
  (positionnement GS / XYOFFSET).
- Descripteur global pointé par `*(0x19e448)`, champ `+0x494` = **largeur (384)**,
  `+0x240/+0x244` = dimensions pour le centrage, `+0x4a4` = base buffer.

**Sites patch (immédiats `0x180`=384 → essayer `0x1c0`=448) :**
| VA | instr | rôle |
|---|---|---|
| `0x14ac28` | `addiu t0,zero,0x180` puis `sw t0,0x494(a1)` | **largeur dans descripteur global** |
| `0x14b070` | `addiu t0,zero,0x180` puis `jal 0x14a550` | **largeur du render-target** (→ FBW) |
| `0x14b0a0` | `addiu a3,zero,0x180` puis `jal 0x14a740` | **largeur pour centrage** |
*(les `0xe0`=224 adjacents = hauteur, à laisser)*

**Hypothèse à trancher en test** (= la question feasibility) : élargir ces 384→448
fait-il **dessiner plus de BG** (le moteur remplit le buffer selon la caméra → vrai
16:9) ou juste **un buffer plus large avec du noir au bord** (le dessin BG reste
clippé à 384 → « 4:3 croppé », ce que Rickow veut éviter) ? Si noir → il faut aussi
élargir le **clip/caméra** (clamps `0x17f`=383 zone 0x577, demi-largeur `0xc0`=192).

**Ordre de test recommandé** : patcher les 3 sites `0x180→0x1c0` ensemble + observer.
Puis ajuster le centrage si l'image est décalée. C'est rapide à tenter en pnach
(immédiats `addiu` = `2408_0180`→`2408_01c0`, etc.).

### ✅ VALIDATION (analyse callers + désasm complet `0x14afd0`, 2026-06-15)
- **`FUN_14afd0` = LE setup du render playfield**, confirmé par ses appelants :
  init de stage (cluster `0x1c9–0x1cd`) **+** setup de mode (`0x152704/152fb0/154180`).
  C'est l'écran de jeu, pas un buffer annexe.
- En interne : lit les dims **plein écran** `s1=*(g+0x240)`, `s0=*(g+0x244)` ; calcule
  le **centrage `(s1−largeur)/2`** (sites `0x14b07c/8c`) ; appelle `FUN_14a550(384,224)`
  (render-target, **FBW=(384)/64=6** = exactement la texture playfield `TBW=6` `0x2bc0`)
  puis `FUN_14a740(384,224)` (offsets). Une branche d'échelle (mult magique
  `0x51eb851f`) gère un éventuel zoom mais ne change pas la largeur logique.
- **Le 384 est bien la largeur logique du playfield** ; les buffers BG (init de stage,
  largeur **variable lue d'une struct** `lh a3,0(s0)`) sont déjà larges (1024). ⇒ le
  decor est là, la contrainte est ce 384 → **levier confirmé**.
- Comme le centrage = `(plein_écran − largeur)/2`, passer 384→448 **réduit
  automatiquement la marge** (le playfield occupe plus de l'écran), pas besoin de
  toucher le centrage à la main au 1er essai.
- **Discordance à garder en tête** : les paquets GS FRAME capturés montraient FBW=10
  (640) et FBW=16 (1024), jamais FBW=6 → le buffer 384 est surtout utilisé comme
  **texture** (`TBW=6` `0x2bc0`) échantillonnée vers l'affichage 640. Donc le playfield
  est rendu en 384 puis blitté/scalé. Reste LA question test : le rendu BG **remplit-il**
  le buffer élargi (caméra) ou s'arrête à 384 (→ bord noir). Inconnu sans test live.

## 5. Plan concret (nécessite PCSX2 live — pour le retour de Rickow)

**Étape 0 — quick wins à tenter d'abord :**
- Vérifier s'il existe déjà un **code widescreen communautaire** pour SLUS-21317
  (base pnach PCSX2 / forums). L'Anthology a pu être patché par d'autres.
- Activer les **Widescreen patches** PCSX2 intégrés pour ce CRC (s'ils existent)
  pour voir le comportement de référence.

**Étape 1 — localiser le render target & le scissor (débogueur GS PCSX2) :**
- PCSX2 → Debug → **GS dump** d'une frame en combat. Analyser le dump (outil
  `gsdumpview` / parser) pour relever : taille du **FRAME** (FBW), **SCISSOR**
  (confirmer 0x17f/0xdf), **XYOFFSET**, registre **DISPLAY** (largeur affichée).
- Ça donne les **adresses/valeurs exactes** sans chercher dans 32 Mo.

**Étape 2 — vérifier l'hypothèse « art déjà large » (LA question clé) :**
- Une fois le scissor élargi (test jetable : forcer SCAX1=447), regarder si du
  **vrai décor** apparaît dans les 64px ajoutés, ou des **trous**.
  - Décor visible → hypothèse CPS2 confirmée → widescreen quasi gratuit (leviers A/B/C).
  - Trous → l'art PS2 est pré-clippé à 384 → chantier type PSP (bien plus lourd).

**Étape 3 — selon résultat :**
- Si gratuit : élargir proprement largeur visible (A) + scissor (B) + cull (C),
  caler l'aspect (D). Itérer 448 puis 480/496 (FBNeo a retenu 448).
- Si trous : RE du pipeline tilemap CPS2→GS (réutiliser la méthodo PSP :
  SOLO/kill-tests, savestate-diff en bougeant la caméra, identifier le drawer
  fautif). Beaucoup plus long.

**Méthodo savestate** (déjà outillée pour l'arcade, réutilisable ici) :
`E:\tmp\p2s_ee.py` extrait le eeMemory d'un `.p2s` ; diff de 2 savestates
(caméra à gauche vs droite) pour voir ce qui bouge (comme le projet PSP).

---

## 6. Liens
- Projet jumeau **PSP** : `[[project-sfa3max-streamer]]` — RE complet du rendu BG
  PSP (drawers tilemap, streamer, cull peint, scissor GE). Méthodo SOLO/kill +
  savestate-diff directement réutilisable.
- Projet jumeau **CPS2/FBNeo** : `[[project-sfa3-widescreen-android]]` — la preuve
  que l'art CPS2 dépasse 384px (widescreen sans patch ROM). Patch de référence :
  `E:\CLAUDE CODE\sfa3-widescreen-android\patches\fbneo-sfa3-widescreen.patch`.
- Projet **arcade** (même binaire HSFA PS2) : `PROJET-Hyper-Arcade.md` (cartographie
  de la state-machine, outils savestate, code-cave 0x1c0000).

---

## 7. ⭐⭐ PIPELINE DE RENDU DÉCOMPILÉ (session autonome 2026-06-24)

Décompilation complète du chemin viewport + dessin des tiles (depuis `eeMemory_versus.bin`).

### 7.1 Viewport / render-target (largeur logique 384)
- **`FUN_14afd0`** (setup playfield) pose la largeur 384 (`0x180`) à 3 sites :
  `0x14ac28`→descripteur global `[0x1ae448]+0x494` ; `0x14b070`→`FUN_14a550` (render-target,
  **FBW=(w+63)/64**) ; `0x14b0a0`→`FUN_14a740` (centrage `(0x1000−[g+0x240])/2`).
- Le champ largeur `+0x494` est **relu** par les builders GS **`0x1d3e80`** et **`0x1d40b0`**
  (constructeurs de paquets FRAME/BITBLT : `sra w,6`=FBW à `0x1d4120/0x1d4148`, regs GS
  `0x50`=BITBLTBUF etc.). ⇒ **Élargir `+0x494` (0x14ac28) propage au render-target GS.** Confirmé.
- Centrage = `(plein_écran − largeur)/2` → élargir 384→448 réduit la marge, pas besoin de
  retoucher le centrage au 1er essai.

### 7.2 ⭐ Dessin des tiles (BG) — l'orchestrateur et les drawers
- **Orchestrateur `0x1d0854`** : boucle sur **4 couches** (`s4<4`), appelle les drawers
  `0x1d1810`/`0x1d1da0`/`0x1d23c0` selon des bits d'activation (s2/s1/s0), puis le
  render-target `0x1d40b0` + présentation.
- `0x1d1810` dispatche vers les **vrais drawers de tiles `0x1d18a0`/`0x1d1a00`** (boucle X×Y).
- **BORNE DE COLONNES = LA largeur de dessin** (bornée pile au 4:3, marge +1 tile) :

| Couche (tile) | site colonnes | 4:3 | 16:9 (448) | 16:9 (480) |
|---|---|---|---|---|
| 8px (A) | `0x1d19b0` | 49 `0x31` | 57 `0x39` | 61 `0x3d` |
| 8px (B) | `0x1d1b9c` | 49 `0x31` | 57 `0x39` | 61 `0x3d` |
| 16px (A) | `0x1d1f7c` | 25 `0x19` | 29 `0x1d` | 31 `0x1f` |
| 16px (B) | `0x1d2140` | 25 `0x19` | 29 `0x1d` | 31 `0x1f` |
| 16px (C) | `0x1d223c` | 25 `0x19` | 29 `0x1d` | 31 `0x1f` |
| 32px | `0x1d2360` | 13 `0xd` | 15 `0xf` | 16 `0x10` |

- Vérif : 49×8 = 25×16 = 13×32 ≈ 384+marge. Les compteurs de **lignes** (`0x1d`=29 / `0xf`=15 /
  `8`) = hauteur 224 → **NE PAS toucher** (16:9 = même hauteur, plus de largeur).
- ⚠️ Certaines boucles sont **déjà à `0x39`=57** (`0x1d1cf8`,`0x1d2034`,`0x1d2234`) = déjà larges
  (buffer 1024 ou couche déjà étendue) → laisser. N'élargir que les bornes 4:3 ci-dessus.

### 7.3 Patch widescreen COMPLET (prêt à tester) — `…pnach.WSTEST`
- **Section 1** (viewport, 3 sites) : `0x180`→`0x1c0`.
- **Section 2** (colonnes tiles, 6 sites) : `0x31`→`0x39`, `0x19`→`0x1d`, `0xd`→`0xf`.
- Ordre : tester S1 seule (voit-on plus de décor ?) ; si bord noir → ajouter S2 (dessine plus
  de tiles). Puis cull persos (`0xc0`=192) / clamps (`0x17f`=383) si objets coupés aux bords.
- ⚠️ **CODE patches HSFA** → risque shell-safe (figer le shell au boot). Section testable séparée.

### 7.4 Reste (test-gated / live)
- Le test tranche : S1 montre-t-il du vrai décor (art CPS2 large) ou du noir (→ besoin S2) ?
- Cull/clamps persos (`0xc0`=192 demi-largeur, 303 sites ; `0x17f`=383 zone 0x577) : à ajuster
  seulement si des persos/objets disparaissent près des bords élargis.
- Aspect final (DISPLAY GS / PCSX2 aspect) pour ne pas étirer.
