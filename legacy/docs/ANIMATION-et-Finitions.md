# Cross-stage — consolidation « ce qui manque » + système d'ANIMATION (2026-09-06)

> Écrit après la réussite de la **Phase 0** (baseline v7 Blanka reproduite au load-time sur le
> setup neuf). Répond à : (1) ce qu'il manque pour du propre/ciblé, (2) cartographie du
> sous-système d'animation (le « bloc E » laissé de côté). Réfs : `PLAN-Cross-Stage-Actualise.md`,
> `CARTO-Cross-Stage-Tables.md`.

## 1. État réel (ce qui marche / ce qui manque)

| Élément | État | Ce qui manque pour « propre » |
|---|---|---|
| **Décor statique** (tuiles+ring+scroll) | ✅ marche (v7, injection load-time) | rien de bloquant |
| **Persos / HUD** | ✅ intacts | — (méthode « région décor seule » validée) |
| **Palette** | ⚠️ résidus (teinte 1 frame/2) | fix twin work→twin (CAVE2 v7) à confirmer / affiner |
| **Généralisation (tout stage)** | ❌ v7 = hand-tuné Blanka | **pipeline package offline** (Phase 1) |
| **Objets ANIMÉS** (serpent, feu…) | ❌ figés (entrées statiques) | **port des scripts d'émission** (ce doc §3) |
| **Résidus divers** | ⚠️ rectangle bleu (objet versus non tué), feuilles | WALK/KILL à généraliser |

**Priorité pour « ciblé »** : les résidus (palette, objets versus) se retrouvent sur CHAQUE
stage → les régler une fois. L'animation est le gros morceau restant.

## 2. Le grand levier : itérer HORS JEU
v7 a pris 43 versions car chaque réglage se testait en jeu. On a maintenant :
- **Rendu offline** (`render_stage.py`) : valider décor+palette avant injection.
- **Injection load-time par savestate** (repacker `p2s_inject_stage.py` VALIDÉ) : tester un
  package sans recompiler de cave (template = savestate load-screen, cf. slot 6).
- **Composeur + palette entièrement décompilés** (adresses exactes).
⟹ On peut diagnostiquer/corriger résidus ET animation en grande partie hors jeu.

## 3. ⭐ SYSTÈME D'ANIMATION — cartographie complète (NOUVEAU, 2026-09-06)

Les objets animés du décor (serpent, feu, taichi…) NE sont PAS des tuiles : ce sont des
**sprites émis par frame** par un sous-système de scripts. Chaîne complète décompilée :

```
DRIVER par-frame (~0x28a044 / 0x29fdd0)
  └─ INTERPRÉTEUR d'objets  FUN_29c050
       ├─ lit l'état d'émission dans le contexte : curseur [ctx+0x6e90], compteur [ctx+0x6ebc]
       ├─ ALLOCATEUR  FUN_581990 : pull le token u16 suivant du script
       │    (résout offsets relatifs → absolus via bases +0x5c0000 / +0xb80000)
       └─ pose chaque objet : type dans [handle+2] (vus : 6,9,2,5,7), handle rangé en ctx
  → émet les sprites courants dans la LISTE SPRITES  0x70002000
  → DRAWERS  0x1d2840 / 0x1d2dc0 lisent 0x70002000 et blittent au GS
```

**Format d'entrée sprite (8 o, décodé sur `FUN_1d2dc0`) :**
- `[0]` = x, `[1]` = y, `[2]` = tile, `[3]` = attr.
- attr : bits bas = palette ; **`(attr>>8)&0xf` = largeur-1 en tuiles** ; **`(attr>>0xc)` = hauteur-1**
  (⟹ un objet = un sprite multi-tuiles W×H). Priorité = `>>0xd`. Terminateur liste = `{0x8000,0x8000}`.
- Bank tuiles + palette du sprite via `FUN_1d0e90` (descripteur, palette à `+0xac`).
- ⟹ **animer un objet = changer son champ `tile` (frame) et sa position par frame** ; c'est ce
  que fait l'interpréteur en ré-émettant l'entrée. Une entrée statique (v7) = 1 frame figée.

**Données (dans le blob descripteur e544, région 0x695ff0–0x697xxx) :**
- **RECORDS** `0x696148` = table `{u32 count, u32 ptr_script}` (auto-réf à `0x696228`).
  Ex. record[0] = `{2, 0x696fd4}`.
- **SCRIPTS** `0x696fd4+` = suites de tokens u16 par groupes (observé : `03c0 0010 <idx>` /
  `0fe0 0014 <idx>` …) = {paramètre, paramètre, index}. Sémantique exacte des tokens =
  **à finir de décoder** (frame d'anim ? position ? mouvement ?).

**Ce que fait v7 (raccourci, = pourquoi ça ne s'anime pas) :**
- Il **APPEND des entrées sprites STATIQUES** (table `0x18bb460` du package, 8o/entrée
  `{x,y,tile,attr}`) directement dans `0x70002000`, + un WALK/KILL des objets versus.
- ⟹ les objets Blanka **apparaissent figés** (aucun script d'émission ne tourne). C'est le
  résidu « serpent » documenté.

## 3bis. ⭐⭐ RÉSULTAT DÉCISIF (2026-09-06) : l'anim = CODE par jeu, pas des données

Comparaison octet-à-octet z5 (`ee_z5blanka`) vs z9 (`eeMemory_versus`) :
| Fonction | z5 vs z9 | Nature |
|---|---|---|
| **`0x1d2dc0`** drawer objets (0x70002000→GS) | ✅ **IDENTIQUE** | **framework PARTAGÉ** (rendu commun) |
| `0x29fdd0` update objet (physique/rebond) | ❌ diffère (228/256) | **code SPÉCIFIQUE au jeu** |
| `0x29c050` spawner objets | ❌ diffère (229/256) | idem |
| `0x581990` allocateur | ❌ diffère (224/256) | idem |

**Conséquences :**
- Le **rendu** est commun : si on émet les bonnes entrées dans `0x70002000`, le drawer z9 les blitte.
- Mais **la logique d'animation (update/spawn) est du CODE propre à zero9 vs zero5** — les objets du
  stage z5 utilisent les fonctions `0x29xxxx` de z5, **absentes quand z9 tourne**. C'est LA raison du
  « non portable simplement » des sessions d'août.
- `FUN_29fdd0` = objet type-dispatché, params **codés en dur** (vélocité `0xfff40000`, gravité `0x9000`,
  timer `0x23`) + struct objet (pos `+0x10`, vel `+0x40`, grav `+0x48`, timer `+0x3b`, frame `+0x6`).

⟹ **3 stratégies d'animation** (par ordre de faisabilité) :
1. **Réimplémenter l'anim dans le cave** (voie DATA→code custom) : pour les quelques objets clés
   d'un stage (serpent, feu), le cave émet les sprites animés dans `0x70002000` chaque frame
   (avancer frame+position selon une table décodée). Le drawer partagé les rend. **Le plus tractable.**
2. **Injecter le code objet de z5** dans z9 (relocaliser les fonctions `0x29xxxx` de z5) — lourd
   (conventions d'appel, dépendances).
3. **Statique** (v7 actuel) : objets figés. Acceptable en attendant.

## 3ter. ⭐⭐⭐ PERCÉE (2026-09-06, PINE live) : le décor animé = TILEMAP, pas sprites

Test sur le **stage Chun-Li (taï-chi)** via PINE (save 8/9 + capture live). Découverte qui
**renverse** le §3bis pour le DÉCOR :

- Les **fighters** animent via la **liste sprites** (`0x70002000` scratchpad, tuiles cyclant).
- Mais **le décor animé (taï-chi) n'est PAS dans la liste sprites** — il est dans les **cellules
  de la tilemap SCR3** (le ring `0xa28000`/z5, `0xba8000`/z9) : le **numéro de tuile de chaque
  cellule cycle** dans le temps.
- ⚠️ **Piège méthodo** : `0x70002000` est le **SCRATCHPAD** (`Scratchpad.bin` dans le .p2s),
  PAS `eeMemory.bin`. Lire eeMemory offset 0x2000 = faux. (Live PINE lit bien le scratchpad.)

**Spec animation taï-chi (complète, reproductible) :**
- Région : **48 cellules SCR3** `0xe64..0xede` (grille ; 4 figurants synchro, bloc 3×4 tuiles chacun).
- **~18 poses**, pas de **`0xC` tuiles/pose**, jouées en **ping-pong** (0→17→0) sur un timer.
- Cellule : `tuile = base_pose + offset_bloc` ; `base_pose = 0x1071 + pose×0xC`.
- Toutes les tuiles de pose sont **déjà dans la bank** (statiques, portées par le package).

**⟹ Reproduction = mini-animateur dans le cave** : chaque frame, calculer `pose` (compteur
ping-pong) et écrire `base+pose×0xC` dans les 48 cellules du ring SCR3. **Data-driven, portable,
trivial** — pas de code objet par jeu. C'est LA bonne méthode pour le décor animé.

**Bilan animation révisé :**
- **Décor animé (taï-chi, eau, feu, torches…) = tilemap cell-cycling** → DATA, portable, mini-cave.
- **Objets sprites animés (serpent qui se déplace, persos de fond mobiles) = liste sprites** →
  plus rare, code par jeu (§3bis), à traiter au cas par cas. (Le serpent Blanka est quasi-statique.)
- ⟹ **La majorité de l'animation de décor est faisable proprement** (tilemap). Le §3bis ne vaut
  que pour les rares objets à trajectoire.

## 4. Ce qu'il faut pour ANIMER (plan ciblé)

Vu §3bis (anim = code par jeu), la voie réaliste = **réimplémenter l'anim des objets clés dans le
cave** (stratégie 1), pas porter du code z5. Étapes :

1. **Décoder les DONNÉES d'animation par objet** (pas du code) : pour chaque objet d'un stage z5
   (serpent, feu…), capturer sur savestates z5 la **séquence de tuiles (frames)** + la **trajectoire**
   (positions/vélocité par frame) depuis la struct objet (pos `+0x10`, vel `+0x40`, timer `+0x3b`,
   frame `+0x6`) et sa table de frames. → observation multi-frames (outils prêts).
2. **Émettre l'anim depuis le cave** : un mini-émetteur dans la code-cave qui, chaque frame,
   avance un compteur et écrit l'entrée sprite courante `{x,y,tile,attr}` de chaque objet dans
   `0x70002000` (le drawer partagé `0x1d2dc0` la rend). Réutiliser la grille objets `0xff4000`
   (tuiles déjà mises par le package v7).
3. **Positionner/scroller** les objets avec la caméra (réutiliser le mapping CAVE3 v7).
4. **Valider** : décor statique porté d'abord (Phase 1), PUIS les objets animés un par un (le
   serpent en premier = le plus visible).

> Réalité : c'est un **sous-système à part, par objet**. Un stage « BG complet + scroll + palette »
> (Phases 0-1-2) est atteignable proprement ; les objets animés sont un **bonus incrémental** ajouté
> objet par objet ensuite. Ne pas bloquer le cross-stage décor sur l'animation.

**Ordre imposé** : décor statique porté et propre (Phase 1) AVANT l'animation — l'émission
s'appuie sur le contexte du stage composé. Attaquer l'anim sur un décor non porté = prématuré.

## 5. Prochaines actions concrètes (ciblées)
1. **Résidus palette** (rapide, offline) : comparer le rendu in-game Blanka (capture) à mon
   rendu offline → isoler le token/rangée fautif → corriger le CAVE2 (work→twin).
2. **Phase 1** : pipeline offline pour bâtir un package UPST générique (dé-composer ring→pool+
   listes+remap), valider Chun-Li au rendu offline.
3. **Décodage script d'objets** : décompiler `0x29c050`/`0x581990`/`0x1d2840`/`0x1d2dc0` +
   drawer, mapper les tokens → sémantique. (RE, hors jeu.)
4. **Port animation** : records+scripts z5 → z9 (voie a ou b), tester au load-time.

## 6. Inconnus restants (bornés, plus de blocage majeur)
- Sémantique fine des tokens de script d'objet (§4.1) — à décompiler.
- Voie de port records/scripts (écrasement vs package) — à trancher après §4.1.
- Résidus palette/objets versus — diagnosticables offline.
- Calibration scroll/objets par stage (v7 CAVE3 était Blanka-spécifique).
