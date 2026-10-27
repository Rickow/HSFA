# Projet — Hyper Street Fighter Alpha : mode Arcade (RE PS2)

> Ajouter un **mode arcade** à *Hyper Street Fighter Alpha* (présent dans
> *Street Fighter Alpha Anthology*, PS2), qui n'a d'origine que Versus / Training /
> Option. Le tout par **reverse engineering + injection de code** (pas de source).

---

## 1. Cahier des charges (mode arcade visé)

1. Enchaînement de combats : victoire → adversaire suivant.
2. Adversaire **et** groove **aléatoires** — **seul P2 change**, P1 garde son perso
   et son groove choisis.
3. « Turbo » (vitesse) identique pour les deux joueurs.
4. **Laisser** le message « YOU WIN ».
5. Victoire → combat suivant / Défaite → retour menu (même adversaire tant que P1
   n'a pas gagné).
6. Idéalement : une entrée **ARCADE** dans le menu principal, à côté de VERSUS /
   TRAINING / OPTION, sans casser le VS existant.

---

## 2. Cible & environnement

| Élément | Valeur |
|---|---|
| Jeu | Hyper Street Fighter Alpha |
| Serial / CRC | **SLUS-21317 / 72CE7A78** |
| ISO | `E:\ROMS\PS2\Street Fighter Alpha Anthology\Hyper Street Fighter Alpha (USA).iso` |
| CPU | PS2 EE = MIPS **R5900** little-endian |
| Nature du code | logique CPS2 **68K recompilée en MIPS** (coroutines/tâches), pas du 68K |
| Émulateur | PCSX2 (cheats au format **`SLUS-21317_72CE7A78.pnach`**) |

### Outils de RE
- **pyghidra** (Ghidra 12.0) + extension **ghidra-emotionengine-reloaded** (langage
  `r5900:LE:32`) — indispensable car les instructions MMI (DPA.W.PH…) cassent le
  désassemblage MIPS générique.
- **capstone** (MIPS32 LE, `skipdata=True`) pour le désassemblage rapide / xrefs.
- Dump RAM EE : `eeMemory_versus.bin` (32 Mo), extrait des savestates `.p2s`
  (ZIP + Zstandard). Savestates de référence : `ss09`=RESULT P1 gagne,
  `ss01`=RESULT P1 perd, `ss07`=menu, `ss08`=char-select, `ss04/05/06`=combats.

---

## 3. Cartographie du moteur

### Adressage global
- Base globale **A5 = 0xb88000** (= valeur lue au scratchpad EE `0x70000000 + 0x1114`).
- Correspondance 68K → EE : `addr_EE = addr_68K − 0x470000` (A5 ≙ 68K `0xFF8000`).

### Hiérarchie d'état (machines à états imbriquées, chaque niveau = `*(u16*)(A5+off)` → table de handlers)
```
boucle principale 0x284b90
   └─ frame 0x22fc20/0x22fc40
        └─ task runner 0x22fe50 / 0x230080  (save/restore coroutines via scratchpad 0x70000000)
             └─ tâche versus (slot 5) 0x284ea0
                  └─ vs_d : phase = *(u16*)(A5+0)  -> table 0x5b5e70
                        phase 0x02 = "MATCH" -> match_flow 0x2862c0
                             └─ match_flow : subphase = *(u16*)(A5+4) -> table 0x5b5e80
                                   0x00 init      -> sub00_h   0x286330
                                   0x02 char-sel  -> 0x286590
                                   0x04 COMBAT    -> 0x286620
                                   0x0e RESULT    -> 0x2865f0 (-> 0x21d550)
                             └─ niveau +8 : *(u16*)(A5+8) -> sous-flux :
                                   combat   0x5b5ea0 | result 0x5b2cd0 | charsel 0x5c55d0
```

**Transition = écrire `*(u16*)(A5+4)`** (ex. `sub00_h` fait `A5+4 = 4` pour lancer le combat).

**Table subphase `0x5b5e80`** : entrées de **4 octets** (pointeurs), byte offset = `subphase×2`.
- subphase `0x04` COMBAT → ptr **`0x5b5e88`** = `0x286620`  ← *cible de hook pour épingler le perso au démarrage du combat (cf. fix perso à venir)*
- subphase `0x0e` RESULT → ptr **`0x5b5e9c`** = `0x2865f0` (déjà redirigé vers la code-cave `0x1c0000`)

**⭐ DISCRIMINANT VICTOIRE/DÉFAITE — CONFIRMÉ PAR LOG LIVE (build `Hyper Arcade DEV`) :**
Le bon discriminant est le **compteur de rounds**, PAS les flags de dernier round.
| | victoire (slot1 live) | défaite (slot2 live) |
|---|---|---|
| **`0xb88526`** rounds P1 | **2** | 0 |
| **`0xb88926`** rounds P2 | 0 | **2** |
| `0xb88530` flag P1 (dernier round) | 1 | 0 |
| `0xb88930` flag P2 (dernier round) | 0 | 1 |
→ **P1 gagne le match ⟺ `0xb88526 > 0xb88926`.** Les flags `0xb88530/930` ne valent que pour le **dernier round** : sur un **2-1**, P1 a `0xb88530=1` tout en **perdant** le match → c'est ce qui a fait échouer I/J/K (tes défaites « 1-2 » étaient des 2-1).
- ✅ **Compteurs de rounds remis à 0** au combat suivant (slot2 live = 0-0) → fiables, à lire au RESULT.
- ❌ **Flags `0xb88530/930` collants** (leftovers non remis à 0 entre matchs) → inutilisables seuls.
- ✅ **Le hook RESULT (subphase 0x0e) se déclenche bien sur victoire ET défaite** (slot2 a loggé une défaite). Le « refight en défaite » venait du flag skip `0xb84200=7` collant + mauvais discriminant, pas d'un hook absent.
- **Outils** : `E:\tmp\p2s_ee.py` (extrait eeMemory d'un .p2s zstd), `E:\tmp\decode_log.py` (décode le ring buffer du build DEV).

**Char/groove = octets** : `0xb88516`/`0xb88916` = char canonique P1/P2 (P2 n'a *que* cet emplacement) ; `0xb88413`/`0xb88813` = groove. Le moteur **ré-écrit ces persos pendant l'arbre d'init de `sub00_h`** (`jal 0x57f2e0`, exécuté avant le test du flag) → un pin posé au hook RESULT est écrasé. Le pin doit se faire **plus tard** (hook combat `0x5b5e88`, écriture une seule fois au 1er frame de combat pour éviter la corruption de spawn du Test A).

### Variables clés (RAM EE)
| Adresse | Sens |
|---|---|
| `0xb88004` | subphase (A5+4) |
| `0xb88008` | sous-phase niveau +8 |
| `0xb88516` | P1 char |
| `0xb88916` | P2 char |
| `0xb88413` | P1 groove |
| `0xb88813` | P2 groove |
| `0xb88530` | **flag « P1 a gagné »** (=1 côté gagnant ; posé dès le KO) |
| `0xb88930` | flag « P2/CPU a gagné » |
| `0xb84200` | flag **skip-char-select** (testé par `sub00_h`) ET curseur de mode au menu (A5−0x3e00) |
| `0xb88080` | compteur de frames → **source de RNG** |

### `sub00_h` (0x286330) — décompilé
Fait `A5+4 += 2` (→ char-select), **puis** lit le flag `0xb84200`, le compare à 7,
et selon le résultat (calcul via scratchpad `0x1150`) :
- flag **== 7** → chemin **combat** : `A5+4 = 4`, attend le chargement du stage
  (boucle `jal 0x5aa5c0` / yield `0x2305b0`) puis `jal 0x2905c0` (init stage).
- flag **≠ 7** → reste en **char-select** (`A5+4 = 2`).

→ C'est **lui** qui décide « skip char-select (combat) » vs « char-select », via
`0xb84200 == 7`. C'est la clé de l'enchaînement propre.

### `RESULT_h` (0x2865f0 → 0x21d550) — décompilé
Simple **dispatcher** : `index = *(u16*)(A5+8) >> 1` → `table_0x5b2cd0[index]()`
(le sous-flux résultat : YOU WIN, score…). Indispensable pour le **handoff de
ressources / stage** — le sauter provoque un freeze.

### Menu principal (entièrement mappé)
Tâche `0x2526e0`, phase → table `0x5b4230` ; `phase 4` = `mode_select 0x252b30`
(écran VERSUS/TRAINING/OPTION).
- Curseur de mode = octet **`0xb84200`** (&7).
- Navigation : tables `0x5b41f0` (haut) / `0x5b4200` (bas) ; cycle réel **1→6→5→4→1**.
- Confirmation → `(*table 0x5b4210[curseur])()` = **lanceur du mode**.
- **Slot 7 libre** → emplacement candidat pour ARCADE (`0x5b4210[7] = arcade_launch`).

---

## 4. Méthode d'injection

**Redirection de pointeur** (pas de trampoline) : l'entrée RESULT de la table de
subphase est à `0x5b5e9c` (= `0x5b5e80 + 0x0e*2`) et contenait `0x2865f0`. On y écrit
`0x001c0000` → `match_flow` appelle **notre routine** quand subphase == 0x0E.

- **Code-cave = `0x1c0000`** (vérifié à zéro dans tous les savestates).
- Index persistant d'adversaire à `0x1c0100` (non réécrit par le pnach).
- Table d'adversaires à `0x1c0110` = `00,01,02,04` (Ryu, Ken, Akuma, Evil Ryu).

### Format pnach (PCSX2 moderne, important)
- Fichier **`SLUS-21317_72CE7A78.pnach`** (SERIAL_CRC).
- Sections **`[Nom du cheat]`** obligatoires, type **`word`** (pas `extended`).
- À activer : **`Enable Cheats` global** + cocher le cheat dans *Properties → Cheats*.
- **PCSX2 ne CHAÎNE PAS les conditions D** (un D ne conditionne que la ligne
  suivante) → logique conditionnelle = **impossible proprement en pnach** → injection.

---

## 5. Historique des tests

| Test | Idée | Résultat |
|---|---|---|
| A / A′ | Forcer char P2 en continu | Corruption des spawns (« Akuma à gauche ») |
| B | subphase = 4 sur RESULT | Enchaîne mais **fond buggé** (stage pas réinit) |
| C | subphase = 0 sur RESULT | Re-montre le char-select |
| **D** | **flag 0xb84200=7 + subphase=0** | ✅ **Rematch propre** (skip char-sel, fond OK, mêmes persos) — mais « trop vite » (pas de YOU WIN). **Validé.** |
| E v1 | pnach conditionnel sur `0xb88530==1` | Trop tôt (flag posé dès le KO, pas à l'écran result) |
| E v2 | conditions D **chaînées** | **CRASH** (PCSX2 ne chaîne pas les D-codes) |
| F | routine injectée : win→adv. suivant / lose→RESULT_h | « Aucun effet » = prenait toujours `do_lose` (branche win cassée) |
| G | injecté inconditionnel, **sans** appeler RESULT_h | **Freeze** (musique tourne) — handoff stage manquant |
| G2 | + `jal RESULT_h` puis override (avec écriture P2) | Plus de freeze ✅ mais : passe par écran de score, char-select réapparaît, **les 2 persos changent** (skip pas honoré) |
| **G3** | Test D injecté : `jal RESULT_h` + flag=7 + subphase=0, **sans** écrire P2 | ❌ **Invalide** — bug : `sh subphase` utilisait l'offset `0x8004` (sign-extended → écrivait à `0xB78004`, pas `0xB88004`). subphase jamais remise à 0 → hook RESULT rappelé en boucle. Test jamais concluant. |
| **G3b** | Idem G3, **fix** : `ori t1,t0,0x8004` puis `sh zero,(t1)` → écrit bien `0xb88004=0`. Tail décalé d'un mot. | ✅ **Skip injecté OK** : victoire → combat suivant **sans écran de score ni char-select**. Restent 2 défauts : (a) **les 2 persos changent**, (b) refight **même en défaite** (pas de retour menu). |
| **H** | Base `t0=0xb88000` (offsets propres, fini le sign-ext). Sur RESULT : `jal RESULT_h` ; lit **flag victoire P1 `0xb88530`** → **défaite** = `beqz` → RET (flux normal) ; **victoire** = latch+réécrit P1 char(`0xb88516`)+groove(`0xb88413`) + flag skip=7 + subphase=0. char & groove = **octets** (confirmé dump). | ❌ **Identique à G3b** sur les 2 points. Diagnostic : (a) le pin P1 au RESULT **arrive trop tôt** — le perso est ré-écrit *après* notre hook, dans l'arbre d'init de `sub00_h` (appel `0x57f2e0`, avant le test du flag) ; (b) le refight en défaite venait du **flag skip `0xb84200=7` collant** (jamais remis à 0). |
| **I** | RESULT hook : **victoire** = `0xb84200=7` + subphase=0 ; **défaite** = `0xb84200=0` (efface le flag collant) + pas d'override → flux normal. Pin perso retiré (isolé). | ❌ **Défaite refight quand même** → le flag collant n'était PAS (la seule) cause. Reste 2 hypothèses : (a) `0xb88530` lit non-zéro en défaite à notre point de hook (on le lit *après* `RESULT_h`) ; (b) branche défaite prise mais flux normal mène au combat. |
| **J** | **Diagnostic** : lit `0xb88530` **AVANT** `jal RESULT_h` (sauve sur pile). **Victoire** = skip=7 + subphase=0 ; **défaite** = flag=0 + subphase=0 → **char-select**. | ❌ **Défaite → combat** (pas char-select) ⇒ `0xb88530` lit **non-zéro en défaite** même lu avant RESULT_h. **Cause racine** : les flags victoire ne sont **jamais remis à 0** dans la chaîne (on skippe l'init de match qui le ferait) → `0xb88530` reste à 1 après la 1ère victoire → tout refight. |
| **K** | Lit `0xb88530` avant RESULT_h, **puis efface `0xb88530` ET `0xb88930`**. **Victoire** = skip=7 + subphase=0 ; **défaite** = flag=0 + subphase=0 → char-select. | ❌ **Identique** (défaite refight, pas de char-select). Idem H/I/J → la branche défaite n'est jamais prise. |
| **VÉRIF** | Audit demandé par Rickow. (a) Injection OK : pnach correct, `EnableCheats=true`, cheat coché. (b) **Vrai discriminant trouvé** = compteurs de rounds **`0xb88526` (P1) / `0xb88926` (P2)** : le joueur à **2** a gagné le match. `0xb88530`/`0xb88930` ne sont que des flags de *dernier round* (fiables seulement sur 2-0) → discriminant fragile, source probable des échecs I/J/K. (c) Nom de section désormais **stable** = `Hyper Arcade DEV` (était renommé à chaque test). | — |
| **LOG** | Build de **logging** (`Hyper Arcade DEV`) : ring buffer `0x1c0100` (16×8o, idx `0x1c0180`) ; refight inconditionnel. | ✅ **Vérité terrain obtenue** : défaite loggée (hook OK en défaite), discriminant = compteurs de rounds. |
| **L** | `Hyper Arcade DEV` (nom stable). Log + **décision par compteurs de rounds** : `slt t6,t2,t1` (P1 gagne si `0xb88526>0xb88926`). VICTOIRE → flag=7 + subphase=0 ; DÉFAITE → flag=0 + subphase=0 (char-select). Assemblé via mini-assembleur à labels (`E:\tmp\asm_testL.py`), vérifié au désasm. | **PRÊT À TESTER** (Rickow absent). Attendu : victoire enchaîne, **défaite (même 2-1) → char-select**. Le ring buffer loggera la session pour vérif. |

**Handler COMBAT `0x286620` (subphase 4) = dispatcher** : lit `A5+8` (sous-flux), indexe
table `0x5b5ea0`, `jalr`. Le spawn fighters est dans l'entrée sous-flux 0 (appelée DANS
`0x286620` au 1er frame). ⇒ rediriger `0x5b5e88`→cave→`jal 0x286620` permet d'écrire le
perso **avant** le spawn (hook viable pour le pin). `0x2905c0` (appelé par `sub00_h`) =
init/reset des structs joueur (zéroïse champs via scratchpad 0x1124), à confirmer s'il
touche le char.

### Plan perso (« seul P2 change ») — conçu, à tester au retour
**NB** : le build **Test L logge déjà `P1char`/`P2char` à chaque RESULT** → la prochaine
session révélera *comment* les persos changent (aléatoire ? cycle ? copie d'un curseur ?)
avant de figer le design du pin.

**Approfondissement char (2026-06-15, statique)** : le char n'est PAS accédé en
`A5+0x516` ni via `addiu base,A5,0x500/0x900` + `0x16` (0 hit des deux). Il passe par
un **pointeur d'objet joueur dynamique** (`lbu char,0x16(player_ptr)`, player_ptr en
variable/argument) → **hunt statique du write impraticable**. Instrument correct = le
**log Test L** (ou un write-BP live sur `0xb88916`). Ne pas re-tenter le hunt statique.

### Validations statiques (2026-06-15) — confirmé sur dump propre
- Table subphase `0x5b5e80` : `[0x00]`=`0x286330` sub00_h, `[0x02]`=`0x286590` char-sel,
  `[0x04]`=`0x286620` combat, `[0x0e]`=`0x2865f0` RESULT_h. ✓ (entrées de 4 octets,
  byte offset = subphase×2.)
- `0x5b5e9c`=`0x2865f0` → notre redirection vers la cave `0x1c0000` est sur la bonne
  entrée ; le `jal 0x2865f0` (`0c0a197c`) de Test L appelle bien RESULT_h (prologue
  `27bdfff0` vérifié). ✓
- `0x5b5e88`=`0x286620` (combat) = point de hook validé pour le futur pin perso. ✓
- **Discriminant V/D** re-confirmé : compteurs rounds `0xb88526/926` (log live slot1/2).
Le perso P1/P2 (`0xb88516`/`0xb88916`, octets) est réécrit par l'init combat `0x2905c0` (appelée par `sub00_h`, via base `A5+0x500/0x900`+offset → invisible en recherche d'offset direct). Pin trop tôt (hook RESULT) = écrasé. **Solution** : 2ᵉ hook sur le handler COMBAT `0x5b5e88` (=`0x286620`) → écrire le char P1 latché **avant** le spawn. Latch délicat (timing du choix joueur vs leftovers) → à régler **avec** test live, pas en aveugle. Idée : latcher le char P1 à la **confirmation char-select**, pas au RESULT.

### Diagnostic en cours
- Le **hook se déclenche bien** (G/G2 changent radicalement le comportement).
- Le **freeze** sans RESULT_h = `sub00_h` attend un stage jamais chargé car le
  handoff de ressources de RESULT_h a été sauté → **il FAUT appeler RESULT_h**.
- G2 montre encore le char-select ⇒ le **flag skip `0xb84200=7` n'est pas honoré**
  au moment où `sub00_h` le lit. G3 tranche : si skip OK sans écriture P2 → le
  problème vient de l'écriture P2 ; sinon → timing injecté vs pnach (alors forcer
  directement `subphase=4` + init stage au lieu de repasser par `sub00_h`).

---

## 6. Reste à faire

1. **Valider G3b** (skip en injecté — version corrigée du store subphase).
2. Réintroduire « seul P2 change » (écrire `0xb88916` au bon moment, P1 inchangé).
3. **Vrai RNG** : `0xb88080 % N` pour l'adversaire et le groove (au lieu du cycle).
4. Laisser le **YOU WIN** : laisser tourner `RESULT_h` quelques frames avant de bouncer.
5. **Défaite → menu** (pas char-select).
6. Entrée **ARCADE** dans le menu (`0x5b4210[7]`, intégrer le slot 7 au cycle nav,
   label cosmétique à trouver) + flag ARCADE en octet libre (VS intact).
7. **Gravure ISO** : injecter le patch définitif dans le conteneur **MWo3** de `ro9`
   (le code tourne en RAM, patché depuis MWo3) puis xdelta sur `X_DATA.BIN`.

---

## 7. Fichiers de travail

| Chemin | Rôle |
|---|---|
| `E:\CLAUDE CODE\hyper_re\eeMemory_versus.bin` | Dump RAM EE servant à toute l'analyse |
| `E:\EMU\…\cheats\SLUS-21317_72CE7A78.pnach` | Cheat de test courant (Test G3) |
| `E:\EMU\…\cheats\*.testF.bak` | Sauvegardes des versions précédentes |
| `E:\tmp\ss01/04/05/06/07/08/09/10\` | Savestates extraits (eeMemory/Scratchpad/Screenshot) |
| `E:\tmp\funcs.pkl` | 4645 starts de fonctions (cibles de `jal`) |

## 8. Pistes fonctionnalités arcade étendues (recon statique 2026-06-15)

**⭐ Clé unificatrice : `A5+0xa8` = `0xb880a8` = VARIABLE DE MODE DE JEU.** En versus
elle vaut **3**. Les lanceurs de mode l'écrivent (VERSUS→3, le lanceur `0x253280`→0…),
et le **char-select `0x506070` branche dessus** dès l'entrée (`lb v0,0xa8(A5)`). Donc le
mode pilote à la fois le lancement ET le comportement du char-select. C'est le pivot des
4 features.

### #1 — Auto-sélection P2 (curseur P2 caché)
- Char-select réel = **`0x506070`** (résident ; `0x286590` ne fait que l'appeler). Il
  **branche sur le mode `A5+0xa8`** au début → le moteur CPS2 a déjà une logique
  char-select **dépendante du mode**. Un mode « 1 joueur » (P2=CPU auto-sélectionné,
  sans curseur P2) existe très probablement dans le code partagé (les jeux individuels
  de l'Anthology ont un mode arcade 1P).
- **Piste** : trouver la valeur de `A5+0xa8` qui met le char-select en 1P, et l'utiliser
  pour ARCADE (résout #1 « gratuitement »). Sinon : hooker `0x506070` pour, après
  confirmation P1, écrire char P2 (aléatoire) + poser le flag « P2 confirmé » + inhiber
  le rendu du curseur P2.
- **À approfondir** sur un **savestate char-select** (lire les flags confirm P1/P2 et le
  curseur P2 ; comparer mode 1P vs 2P).

### #2 — Entrée ARCADE dans le menu de modes (PISTE LA PLUS SOLIDE)
- Menu = tâche `0x2526e0`, écran = `mode_select 0x252b30`. Curseur = `0xb84200 & 7`.
- **Table lanceurs `0x5b4210`** (confirm) : slot0-3=`0x252ff0` (=**VERSUS**, écrit a8=3
  a5=1 → valeurs exactes du dump versus), slot4=`0x253170`, slot5=`0x253280` (a8=0),
  slot6=`0x253430`, **slot7=`0x00000000` = LIBRE** ✓.
- **Tables nav** : up `0x5b41f0`, down `0x5b4200` (octets, index = curseur). Cycle réel
  {1,4,5,6} : down 1→6→5→4→1 ; up inverse. (curseur 1 = VERSUS.)
- **Design ARCADE (VS intact)** :
  1. `0x5b422c` (slot 7) = `arcade_launch` (code-cave) qui pose un **flag arcade** (octet
     libre) + un **mode** donnant char-select 1P, puis `jal 0x252ff0` (lanceur VERSUS).
  2. Insérer curseur 7 dans le cycle nav (ex. `down[1]=7, down[7]=6, up[6]=7, up[7]=1`).
  3. **Label « ARCADE »** : cosmétique, à dériver du rendu des labels VERSUS/TRAINING
     (le `mode_select 0x252b30` dessine les libellés ; à mapper).
  4. Notre **hook RESULT ne chaîne que si flag arcade posé** → VERSUS normal (curseur 1)
     reste intact.

**✅ IMPLÉMENTÉ (plomberie, 2026-06-15)** — pnach `SLUS-21317_72CE7A78.pnach.MENUTEST`
(testable en isolation, sans label) :
- `arcade_launch` @ code-cave **`0x1c0200`** : `flag 0x1c0300=1` puis `j 0x252ff0`
  (tail-call lanceur VERSUS) → ARCADE = VERSUS + flag.
- Lanceur **slot 7** `0x5b422c` = `0x001c0200`.
- Nav curseur 7 inséré en bas (mots : `0x5b41f0=05050701`, `0x5b41f4=04010605`,
  `0x5b4204=01050407`) → cycle down `1→6→5→4→7→1`, up `1→7→4→5→6→1`.
- Désasm confirmé : curseur=`0xb84200&7`, `curseur=nav[curseur]`, lanceur=`0x5b4210[curseur]()`.
- **Test** : au menu, BAS depuis le dernier item → 5ᵉ position (curseur 7) ; confirmer →
  combat versus démarre.

**✅ INTÉGRATION CHAÎNAGE FAITE (2026-06-15)** — cheat unique `[Hyper Arcade]` :
- Hook RESULT `0x1c0000` **gaté sur flag arcade `0x1c0300`** (`beqz`→flux normal si pas
  arcade) → **VERSUS reste non-chaîné**, seul ARCADE chaîne. Discriminant = compteurs
  rounds. + logging conservé.
- `arcade_launch` `0x1c0200` **remet `0xb84200=0`** (montre le char-select ; sinon le
  curseur menu=7 valait skip-flag=7 → sautait le char-select) + flag `0x1c0300=1` + j VERSUS.
- `modesel_clear` `0x1c0240` (redir phase-2 `0x5b4238`) **efface le flag au menu** →
  VERSUS propre même après une session ARCADE.
- **Validé par test Rickow** : la 5ᵉ entrée se sélectionne et lance un combat ; bug
  « ARCADE sautait char-select » = curseur 7 ≡ skip-flag 7 (corrigé). Bug « VERSUS
  chaînait » = hook non gaté (corrigé).

**RESTE pour #2 complet :**
1. **Label « ARCADE »** — investigué (2026-06-15). Les libellés du mode-select
   (VERSUS/TRAINING/OPTION) sont de **GROS SPRITES** (aucune chaîne ASCII, pas de police),
   et **il n'existe aucun asset « ARCADE »**. La 5ᵉ position est donc **vide**. 
   Le jeu A une **police texte** (chaînes ASCII : menu OPTION `0x5b0980` « PLAYER:/PALETTE:/
   SAMPLE:/EXIT » ; UI `0x69e800` « SELECT/CONTINUE/QUIT » + noms persos, format =
   préfixe position+texte). **Voie réaliste** : rendre « ARCADE » via cette police à la
   position du 5ᵉ item (incohérent visuellement vs sprites, mais vrai texte) → nécessite
   RE **live** de la routine font + positionnement. OU injecter un sprite ARCADE (art).
   → **chantier graphique, pas faisable en aveugle**.
2. **Défaite → menu** (au lieu de char-select) : conforme cahier des charges point 5 ;
   nécessite la transition match→menu (task `0x2526e0`), pas encore câblée.

**✅ PIN PERSO IMPLÉMENTÉ (2026-06-15)** — `combat_hook` @ `0x1c0280`, redir handler
COMBAT `0x5b5e88` :
- En arcade (flag `0x1c0300`) : **latch** perso(`0x516`)+groove(`0x413`) de P1 au **1ᵉʳ
  combat** (= choix joueur via char-select, avant toute re-randomisation), stockés à
  `0x1c0308`/`0x1c0309` (latch-done `0x1c0304`, reset par `arcade_launch`). Puis à chaque
  combat suivant, **réécrit P1** depuis le latch **avant le spawn** (le hook tail-call
  `0x286620` après l'écriture) → **P1 garde son perso, seul P2 (adversaire) change**.
- Hors arcade → tail-call direct `0x286620`, **VERSUS intact**.
- Résout « les 2 persos changent » : P1 épinglé, P2 = adversaire variable (= arcade).
  P2 n'est pas encore un vrai RNG contrôlé (le moteur le re-tire) mais varie → OK pour
  l'instant. **À tester.**

### #3 — Skip des logos / #4 — Entrée directe HSFA — = LE SHELL ANTHOLOGY (sous-projet)
**Savestates fournis (2026-06-15)** : slot1/2=logos, slot3=accueil, slot4=sélection-jeu,
slot5=menu-modes HSFA. Décodés via `p2s_ee.py`. **Constat structurel net** :
- **Slots 1-4 = le SHELL Anthology** (binaire **distinct** de HSFA) : la tâche menu HSFA
  `0x2526e0` y est **non résidente** (zéro), les vars `0xb88xxx`/`0xb84200`=0. Code shell
  actif (≠ HSFA) ; sa logique de scène est vers **`0x154c00–0x154e00`** (lit `0x1a2458`).
- **Slot 5 = HSFA** : menu `0x2526e0` résident, curseur=1 → dump idéal pour **#2**.
- **#4 (direct HSFA)** : il faut reverser la **fonction de lancement de jeu du shell** +
  l'ID/index HSFA. C'est un **sous-projet** (binaire non mappé, lié au projet
  `[[project-sfa-anthology-cps2-extraction]]` / conteneurs MWo3).
- **#3 (skip logos)** : trouver l'état de scène autoritaire du shell + le forcer.

**⚠️ LEÇON MÉTHODO (importante)** : le **diff de savestates sur le binaire shell non
mappé donne des candidats AMBIGUS**. Ex. `0x1a2458` semblait un compteur de scène
(5→6→7→8 sur logo1/logo2/accueil/select) mais le désasm montre que c'est un **index de
tableau** (`sll ,6` stride 64, slot allocator) qui croît avec le boot, pas l'état de
scène. ⇒ Pour #3/#4, **ne pas se fier au diff** : il faut des **breakpoints live** (BP
sur la boucle principale du shell / la fonction de lancement) — méthode du projet PSP.
Ces deux features sont réalistes mais = **chantier de RE du shell Anthology à part**.

### #3 — P2 = CPU (LE cœur d'un vrai arcade) — recon 2026-06-15
HSFA a bien un réglage **P2 humain/CPU** (Rickow l'a togglé → savestates HUMAN/CPU).
Diff des 2 savestates (en plein combat) :
- CPU ajoute un **objet IA** → ~390 octets diffèrent, dont des **pointeurs heap +0x13a**
  (décalage d'allocation) et les **buffers d'input** `0x1b17xxx` (P1) / `0x1b35xxx` (P2)
  remplis d'**entrées générées par l'IA** au lieu de la manette. ⇒ le CPU marche par
  **injection d'inputs IA**, pas un simple flag passif.
- `0x19e020` (5→6) = **compteur d'objets de RENDU** (lu massivement depuis `0x147xxx`,
  zone rendu) → side-effect (le CPU ajoute un objet/indicateur), PAS le flag.
- Le vrai flag = **champ de struct de contrôle par joueur** (candidats `0x19e6b6` 4→6,
  `0x19e712` 3→5, `0x19d2fa5` 0→1) — **aucune xref absolue** (accès par pointeur runtime)
  → impossible à trancher depuis un diff en plein combat.
- **DÉBLOQUE-LE** : paire de savestates **AU CHAR-SELECT** (P2 humain vs P2 CPU, même
  instant) → le flag y est posé proprement, peu de bruit. OU tracer la routine d'input
  qui choisit manette-vs-IA pour P2.

**✅ FLAG P2-CPU TROUVÉ (2026-06-15, savestates slots 4-7 = char-sel/stage × COM/HUM)** :
filtre "stable" (même valeur COM dans les 2 contextes, idem HUM, COM≠HUM) →
| addr | P2 CPU | P2 humain | (P1 toujours) |
|---|---|---|---|
| `0xb880a8` (mode) | **3** | 1 | — |
| `0xb880a5` | **1** | 0 | — |
| `0xb88900` (P2 struct +0) | **2** | 0 | P1=2 |
| `0xb88904` (P2 struct +4) | **6** | 0 | P1=6 |
- `0x2905c0` (init combat) écrit **2** dans P1(`A5+0x500`) ET P2(`A5+0x900`) — donc 2 =
  « slot combattant actif » (par défaut). Pour P2 **humain**, l'assignation manette le
  **remet à 0** ; pour CPU il reste 2 + l'IA tourne. **Maître = `0xb880a8`** (bit1=2 → P2 CPU).
- `0x252ff0` (lanceur curseur 1) met **a8=3/a5=1** = la config CPU ! Donc mon arcade
  (qui l'appelle) devrait donner P2 CPU, MAIS un truc (char-select / P2 idle) **remet
  a8=1**. → forcer a8=3 (+a5=1, P2 struct) à travers le flux = la voie.
- ⚠️ le flag `0xb88900` est lu via **pointeur d'objet joueur** (offset 0), pas d'xref
  absolue ; forcer le byte mid-combat ≠ garanti (l'IA doit être initialisée). Forcer
  **a8=3 avant l'init combat** est plus sûr (l'IA se spawn).
- ❌ **Test « force a8=3 » → échec** : casse le menu (auto-select versus) ET P2 immobile.
  a8 est un dérivé, pas la source ; le jeu re-dérive depuis l'OPTION persistante.

**🎯 MAÎTRE TROUVÉ = OPTION « VS MODE (2P) » @ `0x19d2fa5` (0=MAN, 1=COM).**
Rickow règle P2 CPU via **OPTION→GAME OPTION→VS MODE (2P)→COM**. Diff savestates
char-sel/stage COM/MAN **croisé avec la navigation d'option** (slots 8→9→10→1) →
**un seul** octet : `0x19d2fa5`, qui bascule 0→1 pile à la sélection COM, stable
partout (COM=1/MAN=0). Bloc d'options à `0x19d2f98` (`04 01 01 02 01 01 01...`).
- C'est l'**option persistante** : la mettre à 1 = le jeu configure P2=CPU **proprement**
  (IA spawnée au setup combat), **sans toucher au menu** (≠ a8). 
- **Intégration arcade prévue** : `arcade_launch` sauvegarde la valeur courante de
  `0x19d2fa5` puis la met à 1 ; `modesel_clear` la restaure → **VERSUS garde le choix
  du joueur**. (à coder après confirmation du test diag.)
- Diag de confirmation : cheat `[Arcade DIAG force P2 CPU]` = `patch ...,019d2fa5,byte,01`.
- ✅ **Diag CONFIRMÉ par Rickow** : `0x19d2fa5=1` → P2 = CPU (l'option reste sur COM tant
  que forcé). 
- ✅ **INTÉGRÉ** : `arcade_launch` met maintenant `0x19d2fa5=1` (COM) au lancement arcade
  (lui t5,0x019d ; sb 1,0x2fa5(t5)). VERSUS garde le choix joueur (arcade ne force qu'au
  lancement ; restore au menu = TODO « passons » pour l'instant). Désactiver le diag,
  utiliser `[Hyper Arcade]`.

### ⭐ MÉCANISME CHAR-SELECT (confirmé savestate + désasm `0x506070`, 2026-06-15)
- **COM ne sélectionne PAS P2** : le joueur choisit P1 ET P2 ; P2 est juste piloté CPU
  ensuite. Donc « auto-P2 » = travail explicite (poser char P2 + confirmer à la place).
- **Flag de confirmation par joueur = bit `0x8000` du halfword `struct+0x1a`** :
  P1 `0xb8851a`, P2 `0xb8891a` (handler fait `lh ...0x51a ; or 0x8000`). Char en `+0x16`
  (`0xb88516`/`0xb88916`). Quand **les deux bits 15 sont posés → le combat démarre**.
  (Aussi : `+0x1b` bit7 = input « valider » consommé ; `0xb884d2` ; `0xb88063` bit0.)
- **ARCHITECTURE PROPRE pour la chaîne (remplace le `subphase=0` qui re-tire tout)** :
  router la chaîne **via le char-select** (`subphase=2`) en **pré-confirmant** :
  - **Victoire** : P1 char=gardé + `0xb8851a|=0x8000` ; P2 char=**nouveau (RNG)** +
    `0xb8891a|=0x8000` → les 2 confirmés → démarre direct (P1 conservé, P2 nouveau),
    sans écran visible.
  - **Défaite** : P1 **non** confirmé (le joueur re-choisit) ; P2 char=**même** +
    `0xb8891a|=0x8000` → l'écran attend P1, adversaire inchangé.
  → pilote la chaîne par le mécanisme natif, **plus de re-roll ni corruption de spawn**.
  À VALIDER : un test minimal « forcer P2 confirmé au char-select » confirme que poser
  le bit déclenche bien l'auto-sélection.

**RÉSULTAT TEST v2 (2026-06-15)** : ✅ routage char-select marche (flash + démarre),
✅ **P1 reste fixe**, ✅ adversaire change (cycle[0]=Ryu coïncidait avec P1 → paraissait
identique). ❌ **P2 plus CPU**. Findings :
- **`a8` = masque d'input HUMAIN par joueur** : char-select gate P1 sur `a8&1`, P2 sur
  `a8&2` (sites `0x506098`/`0x50618c`). Confirm input = `+0x1b` bit7 ; pose `+0x1a` bit15.
- **P2 CPU ⟺ `0x19d2fa5=1` MAINTENU** : le DIAG (force constante) marchait ; `arcade_launch`
  ne le pose qu'une fois → réinitialisé avant le combat → P2 humain. **FIX appliqué** :
  force constante `patch ...,019d2fa5,byte,01` dans `[Hyper Arcade]` (approche prouvée ;
  versus aussi COM tant que le cheat est actif = « passons » accepté).
- Cycle adversaires décalé pour commencer à **Ken** (visible vs P1=Ryu) : table `0x1c0320`
  = `04030201`/`00070605` (Ken,Akuma,Charlie,ChunLi,Adon,Sodom,Guy,Ryu).

**✅ CONSTRUIT — `[Hyper Arcade]` v2 (2026-06-15)** : hook RESULT redessiné (`0x1c0000`,
51 instr). Après `RESULT_h`, si arcade : **VICTOIRE** → `0xb8851a|=0x8000` (P1 gardé) +
P2 char = cycle adversaires (table `0x1c0320`=Ryu..Guy IDs 0-7, index `0x1c0318`) +
`0xb8891a|=0x8000` + `subphase=2` → char-select tout-confirmé démarre direct (P1 gardé,
P2 neuf). **DÉFAITE** → `0xb8851a&=~0x8000` (P1 re-choisit) + `0xb8891a|=0x8000` (P2 même)
+ `subphase=2`. Discriminant rounds. arcade_launch met aussi VS MODE COM. **EN TEST** —
valide l'hypothèse centrale (pré-confirmation pilote le char-select sans re-roll/corruption).

### ⭐ CHAR-SELECT = machine à sous-phases (`0xb88008`, table `0x5c55d0`)
Le char-select n'est pas une étape : c'est un sous-flux `0xb88008` (perso, groove, handicap…).
Pré-confirmer le perso (`0x51a/0x91a` bit15) ne couvre QUE le perso → groove se re-tire +
écran handicap apparaît (constaté). **Seuls perso P1/P2 utilisent le confirm bit15** (les
autres phases = logique séparée, non mappée).
- **PHASE DE SORTIE = `0xb88008=6`** (handler `0x508b80`) : appelle `0x5aa5c0` (charge
  stage) puis `subphase += 2` (2→4=combat). Site : `0x508cf4`.
- **v4 (build actuel)** : **VICTOIRE** → `0xb88008=6` (saute toutes les phases de sélection
  → P1 char+groove GARDÉS, pas d'écran groove/handicap) + P2 char=cycle adversaire ;
  **DÉFAITE** → `0xb88008=4` (phase choix perso → char-select s'affiche). Commun : `0xb84200=1`
  (versus→COM) + subphase=2. **EN TEST** — valide si jumper à `0xb88008=6` sort proprement
  (sinon `0xb88008` est resetté à l'entrée char-select → adapter).
- ✅ Acquis : P2 CPU (`0x19d2fa5=1` + `0xb84200=1`), P1 char gardé, opponent cycle.
- ❌ **v4 (saut `0xb88008=6/4`) CASSE** (test) : fond noir (setup stage sauté), char P2 pas
  propagé au spawn (chargement OK mais combat garde l'ancien), **défaite freeze** (savestate
  slot9 = bloqué `subphase=2 sub+8=4` sans l'init char-select). ⇒ **on ne peut PAS sauter
  dans le sous-flux** : le char-select DOIT tourner depuis la phase 0 (l'init prépare
  affichage + propagation).
- ⚠️ **CONFLIT `0xb84200`** : skip-char-select veut `==7`, mais **COM veut `==1`**. Donc le
  skip (flag=7) **casse le CPU P2**. ⇒ il FAUT la route char-select (`0xb84200=1`), pas le skip.
- **→ REVENU à v3** (route char-select, stable) comme baseline. Combat-init `0x2905c0` appelé
  depuis `0x286560` (sub00_h) et `0x2905a4`.
- **RESTE (dur)** : figer groove/handicap = pré-confirmer leurs phases (confirm inconnus,
  ≠ char `0x51a` bit15) OU épingler les valeurs au combat-init `0x2905c0` (hook avant spawn,
  garde valeurs mais écrans peuvent flasher). Mapping multi-phase du char-select = chantier.

### ⚠️ v3 BOUCLE LES MÊMES PERSOS (test Rickow) — le char-select copie CURSEUR→perso
Écrire `0xb88916` (char) est **écrasé** par la copie curseur→char du char-select. P1 et P2
suivent leur curseur (inchangé) → mêmes persos en boucle. Pour changer l'adversaire il faut
soit le **curseur P2** (non localisé), soit **ne pas re-passer par la sélection** (skip).

### ⭐ v5 (build actuel) — SKIP-path + épinglage au combat-init
- Fight 1 : char-select normal (`0xb84200=1` → COM, P2 CPU). `arcade_launch` pose flag/COM.
- **HOOK RESULT** `0x1c0000` : latch P1 perso+groove au 1er combat ; **VICTOIRE** → `0xb84200=7`
  (SKIP char-select : **pas de re-copie curseur** → on peut imposer les persos) + subphase=0 +
  adversaire = cycle (`0x1c0320`) stocké en `0x1c030a` ; **DÉFAITE** → `0xb84200=1` (char-select+COM).
- **CINIT hook** `0x1c0280` (redir `jal@0x286560` du skip-path, vérifié = `jal 0x2905c0`, delay
  nop) : juste avant le spawn, force P1 char(`0x516`)+groove(`0x413`) (latch) + P2 char(`0x916`)
  = adversaire → P1 gardé, **adversaire DIFFÉRENT**, setup combat propre (pas d'écran noir).
- **PARI central** : le contrôle CPU (COM) **persiste** après l'avoir posé au combat 1 (le skip
  met `0xb84200=7` ≠ 1 ; si COM est re-évalué chaque combat → P2 redevient humain). **À TESTER.**

### ✅✅ v6 VALIDÉ (test Rickow) — ARCADE FONCTIONNEL
Le jeu boote (shell-safe confirmé), **P2 bouge (CPU persiste !)**, adversaires changent, **pas de
corruption**. SEUL défaut : **P1 change aussi** (devrait rester). Cause : l'épinglage v6 était
gardé sur `A5+8==0` (sous-flux jamais matché à l'entrée handler combat) → pin jamais déclenché →
les 2 persos = re-tirage moteur (aléatoire).

### Spawn des combattants (angle skip, 2026-06-15) — pin trop tard confirmé
Combat sous-flux table `0x5b5ea0` : sous-flux 0 = **`0x286690`** (handler spawn) → appelle
**`0x2148b0`** → plusieurs sous-fonctions (`0x214790/7c0/820/850/880`...) où le perso est lu
**en profondeur**. `0x2905c0` (init stage) écrit les structs (A5+0x500/0x900=2) mais ne lit
PAS le perso. ⇒ sur le **skip path**, le spawn est trop profond/tôt pour un hook DATA shell-safe
→ **impossible de garder P1 via le skip**. La route **char-select** (sans re-roll) est la voie ;
un **agent** cherche la source persistante du perso confirmé (à écrire pour changer P2/garder P1).

### ⭐⭐ CHAR-SELECT — SOLVE COMPLET (agent 2, 2026-06-15)
- **2 structs** : scratchpad `0x70001114` = struct courant (repointée sur le joueur en phase
  per-player) ; `0x70001118` = struct joueur (P1 `0xb88400`, P2 `0xb88800`).
- Champs : curseur `+0x102`, perso `+0x116` (=grille[curseur]), groove `+0x13`, confirm perso
  bit15 `+0x11a`, **confirm groove `+0x12`**, handicap `+0x404`/`+0x804`.
- **POURQUOI P2 ne changeait pas = P2 EST CPU** (`0xb88080` bit0=0). Gate `0x5095b4` : si P2 CPU
  ET non confirmé → **chemin RANDOM** (reset `+0x3f`/`+0x15c`, RNG `0x58e890`, index&0x3f →
  table seed `0x5c52a0` → curseur `+0x102` → perso via `0x511ba0`). ⇒ **mon ancien confirm P2
  figeait ce random**. NE PAS toucher P2 = adversaire tiré au hasard à chaque combat (= ladder).
  (Pour CONTRÔLER l'adversaire : écrire `+0x15c≠0` pour court-circuiter le random AVANT le reset,
  puis imposer `+0x102`/`+0x116` = char voulu. Option avancée.)
- **Groove** : sous-flux 1 (`0x506a20`, table `0x5c5600`) ré-init le groove à 0/défaut à chaque
  passage (pas de source persistante) → reset Alpha-3. Confirm `+0x12=1` peut le figer (sinon
  sauter le sous-flux 1).
- **Handicap** : sous-flux 5 (`0x5105d0`, table `0x5c52e0`, 1er état `0x510690` écrit `+0x404`/
  `+0x804`). Skip = avancer le sous-flux (`0xb88008`) au-delà, OU flag skip `0xb880c2` (candidat).
- Progression : `0xb88008` = sous-flux (table `0x5c55d0`), `0xb8800c` = état interne (+2/confirm).
  Sortie = sous-flux 6 (`0x5119b0`→`0x508b80`→`0x5aa5c0` charge stage + subphase=4).

### ⭐⭐⭐⭐⭐ v20 (build actuel) — ARCHITECTURE training-select → versus-combat (idée Rickow)
**Décompilation menu/modes (variable `0xb880a8`)** : VERSUS=mode **3** (`0x252ff0`), TRAINING=mode
**1** (lanceur `0x253170`, char-select **pad 1 choisit P1 ET P2** — confirmé savestates), OPTION/EXIT
autres. Char-select root `0x506070` branche sur les bits du mode (bit0 2P/1P-ish, bit1 gère P2).
**Training = combat INFINI (pas de KO/vainqueur)** → inutilisable seul pour un ladder.
**SOLUTION (Rickow)** : utiliser le **char-select training** (sélection 1-pad des 2 persos) PUIS
**basculer en combat versus** (mode 3 = vrai KO) à la transition.
- arcade_launch `0x1c0200` : `0xb880a8=1` (mode training) + P2 CPU (`0x19d2fa5=1`) + `j 0x253170`
  (lanceur training ; en posant mode=1 d'abord, `0x253170` garde mode 1, pas 2).
- transition `0x1c0140` (redir DATA `0x5c55dc` = sortie char-select `0x508b80`) : `0xb880a8=3`
  (combat versus) puis `jal 0x508b80`. Training pour choisir, versus pour se battre.
- v20 = validation SANS ladder (pas de RESULT/CINIT). À TESTER : char-select 1-pad + combat KO + P2 CPU ?
- Si OK → rebrancher le ladder (latch P1 / cycle P2 / win→next) par-dessus cette base saine.
- Bug connu à nettoyer : nav VERSUS/ARCADE partagent le curseur 7 (`0xb84200`), source du "aléatoire" v19.

### v19 (étape) — versus+skip, P1 fixe + P2 ladder mais aléatoire (nav desync + timing skip)
Avancées clés validées par savestate + tests :
- **Écrire perso(0x516)+curseur(=perso+0x30) FIGE le perso** (diag v16 : P1 forcé=Ryu). +0x116 = char.
- **Latch à la sortie char-select `0x508b80` (redir `0x5c55dc`)** capture le VRAI choix (savestate
  v17 : latch=Akuma=0x02, P1 réel=Akuma ✓). Lire 0x516 au combat-init = trop tôt (décalé).
- **v18 fix injouabilité** : n'épingler qu'**1×/combat** (flag write-done `0x1c011c`, reset au
  RESULT). v17 écrivait 60×/s → le moteur réutilise les champs en combat → décalage = injouable.
- **v19 fix P1-change** : le latch se re-déclenchait à chaque sortie char-select (donc chaque
  défaite). ⇒ **latch gardé UNE fois** (gate `latched==0`, jamais reset hors arcade_launch) →
  P1 = choix initial, fixe toute la run. **Défaite = route skip** (rematch direct, même
  adversaire) au lieu du char-select. Victoire = index++ → adversaire suivant.
- Vars `0x1c0100` : flag/latched/P1char/P1groove/index/write-done. Caves : RESULT 0x1c0000,
  LATCH 0x1c0140, LAUNCH 0x1c0200, CLEAR 0x1c0240, CINIT 0x1c0280. P2 CPU `0x19d2fa5=1`.
- **À VALIDER** : P1 fixe même en perdant ? P2 change sur victoire ? (P2 ne bouge QUE sur victoire.)
- RESTE ensuite : option re-pick P1 sur défaite (si voulu), skip écran handicap s'il réapparaît,
  label ARCADE, quitter vers menu.

### v17 (étape) — latch P1 à la sortie du char-select (correct mais écrivait chaque frame)
**Percée (décompilation `0x511ba0` + diags) :** `perso = grilleA[curseur]` (table `0x5c5300`,
rangée 0x30 = identité) écrit en `struct+0x116` ; il y a une grilleB `0x5c2490`→`+0x117` (=1,
flag version, PAS le perso). Dump versus : en combat **curseur(+0x102)=perso(+0x116)+0x30**.
**Diag v16 a prouvé** : écrire `perso(0x516)+curseur(=perso+0x30)` au hook init-combat **FIGE
le perso à 100 %** (P1 forcé = Ryu quel que soit le choix). Donc l'écriture marche ; le bug
v14/v15 = le **latch** (lire `0x516` au combat-init = trop tôt, valeur décalée).
- **LATCH cave** `0x1c0140` (redir DATA `0x5c55dc` = sortie char-select `0x508b80`) : capture
  perso(`0x516`)+groove(`0x413`) **confirmés**, pose latched=1, puis `jal 0x508b80`. Ne se
  déclenche qu'au combat 1 (route skip saute le char-select ensuite) + re-latch sur défaite.
- **CINIT** `0x1c0280` (redir `0x5b5e88`) : restaure P1 perso+curseur(=perso+0x30)+groove depuis
  le latch ; écrit P2 = `cycle[index]` (perso=index, curseur=index+0x30). `jal 0x286620`.
- **HOOK RESULT** `0x1c0000` : victoire → index++ (wrap 0xd) + route skip (`0xb84200=7`,
  subphase=0) ; défaite → reset latch + char-select (`0xb84200=1`, subphase=2), **même index**.
- Vars en `0x1c0100` (flag/latched/P1char/P1groove/index). P2 CPU via `0x19d2fa5=1`. Shell-safe.
- **À TESTER** : P1 = perso exact (sans décalage) + groove gardé + adversaire change + défaite→même.

### v14/v15 (échecs) — LADDER au hook init-combat (latch au mauvais moment → décalage)
Le diag v13 a tranché : forcer P1=char 7 (**curseur `0x502` + perso `0x516`**) au hook init-combat
`0x5b5e88` (redir DATA → cave → `jal 0x286620`) **épingle bien le perso, à chaque combat**
(« P1 ne change pas » = char 7 figé). ⇒ le hook init-combat est **LE** point d'écriture qui tient.
Donc on n'y combat plus le char-select/random : on **impose les deux** persos là.
- **CINIT** `0x1c0280` (redir `0x5b5e88`) : si arcade — P1 : 1ᵉʳ combat latch curseur+perso+groove du
  choix joueur (`0x1c0108/9/a`, flag `0x1c0104`), sinon **restaure** P1 ; P2 : **toujours** =
  `cycle[index]` (perso=index 0..0xc, curseur=index+0x30) → adversaire change. Puis `jal 0x286620`.
- **HOOK RESULT** `0x1c0000` (redir `0x5b5e9c`) : victoire → **index++ (wrap 0xd)** + route skip
  (`0xb84200=7`, subphase=0) pour enchaîner ; défaite → reset latch P1 + char-select (`0xb84200=1`,
  subphase=2), **index inchangé = même adversaire**.
- arcade_launch : flag/COM(`0x19d2fa5=1`)/reset latch+index/`0xb84200=1`. Variables en **`0x1c0100`**
  (le code CINIT va jusqu'à `0x1c0310` → ne JAMAIS remettre les vars en `0x1c03xx`). Shell-safe.
- **À TESTER** : P1 fixe + groove gardé + adversaire qui change (ladder) + défaite→même adversaire ?
- v12/v13 (échecs) : v12 dé-confirmait P2 → **P2 miroir de P1** (pas random). v13 route skip + pin P1
  conditionnel → **les 2 changeaient** (pin pas pris faute de curseur). v14 écrit curseur+perso pour
  LES DEUX au point prouvé.

### v12 (ancien, échec) — DÉ-CONFIRMER P2 → P2 miroir de P1 (le gate random ne s'arme pas ainsi)
Insight Rickow : « ton skip va trop vite, c'est ton code qui sélectionne le même perso et tu
essaies de le re-changer après coup ». Diagnostic confirmé : le bit **confirm P2** (`0xb8891a`
bit15) restait **collé** depuis le combat 1 → le gate random `0x5095b4` (P2 CPU + non-confirmé
⇒ adversaire tiré au hasard) **ne se déclenchait jamais** → même adversaire + char-select
auto-terminé (« trop vite »). Tous les builds v8→v11 ratent là (forçaient/laissaient P2 confirmé).
- **HOOK RESULT** `0x1c0000` : latch P1 perso(`0x516`)+groove(`0x413`) au 1ᵉʳ combat ; **VICTOIRE**
  → P1 confirme (`0x51a` bit15=1, fixe) + **EFFACE confirm P2** (`0x91a` bit15=0 ⇒ random) ;
  **DÉFAITE** → P1 dé-confirme. subphase=2, `0xb84200=1` (COM). **Ne force/écrit JAMAIS P2.**
- **EXIT cave** `0x1c0280` (redir DATA `0x5c55dc` = sous-flux 6 = `0x508b80`) : restaure
  **uniquement P1** perso+groove depuis le latch (corrige le reset Alpha-3), **ne touche pas P2**
  (l'adversaire random tient), puis `jal 0x508b80`. Comme le char-select tourne maintenant à fond
  chaque combat (P2 dé-confirmé), le sous-flux 6 se redéclenche → groove restauré à chaque combat.
- Diag v11 avait prouvé que l'override P2 au sous-flux 6 marche **au combat 1 seulement** (les
  combats enchaînés ne repassaient pas par là car P2 restait confirmé → char-select court-circuité).
  v12 supprime ce court-circuit. Shell-safe (DATA-redirect + cave). **À TESTER : P1 fixe + groove
  gardé + adversaire DIFFÉRENT chaque combat ? handicap encore présent ?**

### v9 (ancien) — P2 random (CPU) + P1/groove figés (a échoué : P2 jamais dé-confirmé)
Ne touche PAS P2 (→ random adversaire). P1 confirmé (gardé). Groove confirmé `+0x12=1` (figé).
subphase=2, `0xb84200=1`. **À TESTER** : adversaire varie ? P1+groove gardés ? handicap encore là ?

### v8 (ancien) — route char-select + écriture curseur P2
Résultat : ✅ **P1 garde son perso** (curseur P1 `0xb88502` non touché). ❌ **P2 ne change pas**
(écriture curseur `0xb88902`+perso `0xb88916` **écrasée par le re-seed d'entrée** depuis
`struct+0xc` = `0xb8880c` ⇒ c'est LUI la vraie sélection persistante). ❌ **groove reset**
(défaut Alpha-3 ; groove = `0xb88413`/`0xb88813`). ❌ **écran handicap** entre combats.
⇒ Agent relancé pour le solve complet : (1) écrire `0xb8880c` (seed P2, mapping via tables
`0x5c52a0`→`0x5c5300`) pour changer l'adversaire ; (2) source persistante du groove pour le
figer ; (3) phase handicap + son confirm pour la sauter.

### v7 (ancien) — fix du déclencheur d'épinglage
Garde **« pin-pending »** (`0x1c030c`, posé par le hook RESULT sur victoire, effacé par le pin)
au lieu du sous-flux → le pin se déclenche **une fois** au 1er frame du handler combat
(`0x5b5e88`), **avant le spawn** → **P1 gardé (perso+groove) + P2 = adversaire du cycle**. Reste
shell-safe (DATA only). **À TESTER : P1 reste-t-il fixe maintenant ?**

### (ancien) Reste — à régler selon le comportement COM-chain observé
- **P1 reste fixe** : en mode COM le char-select est 1P (P1 choisit) ; sur le skip-chain
  (victoire) le char-select est sauté → P1 devrait rester. À confirmer en test (≠ l'ancien
  bug 2P où les 2 changeaient).
- **Défaite → char-select avec MÊME P2** (cahier des charges pt 5 : même adversaire tant
  que P1 n'a pas gagné). Sur défaite : retour char-select, mais épingler P2 (l'adversaire
  qui a gagné) au lieu de laisser le CPU re-tirer. → besoin de pin P2 sur la branche défaite.
- **Victoire → NOUVEL adversaire** (P2 change) : si le skip-chain garde P2, forcer un
  nouveau P2 (RNG) sur la branche victoire.
- Ces 3 dépendent de comment le COM-chain gère P1/P2 sur skip vs char-select → **tester
  d'abord**, puis cibler.

### #5bis — Défaite → menu (au lieu de char-select) — lead 2026-06-15
Le lanceur VERSUS `0x252ff0` bascule de scène via des **codes `0x5200`/`0x5700`** (lus de
`0xb84214` → scratchpad `0x1144`, compare bit-à-bit). C'est le mécanisme de switch de
scène ; la transition inverse (match→menu) passerait par un code analogue. À reverser
(intriqué, MMI) ou à capter en live. Le menu reste la tâche `0x2526e0`.

### Ce qu'il faut de Rickow
- **#1 (auto-P2)** : un savestate à l'**écran char-select** (pas le mode-select fourni).
- **#3/#4** : se feront **live** (BP sur le shell), pas en statique. Slots 1-4 utiles
  comme points de départ mais insuffisants seuls.
- **#2** : rien de plus — le dump versus + slot5 suffisent, **implémentable maintenant**.

---

> Voir aussi le projet jumeau **SFA3 Widescreen (Android)** — même série, autre
> approche (FBNeo/CPS2 côté émulation, ici code natif PS2 reverse-engineeré), et
> `[[project-hyper-widescreen]]` (16:9 du même binaire HSFA PS2).
```

### ⭐ PIÈGE CRITIQUE 0xb84200 (savestate v22, 2026-06-24)
`0xb84200` est **DOUBLE-USAGE** : (a) curseur du menu mode-select (ARCADE = curseur **7**), (b) flag
de route combat (**=7 → SKIP char-select = re-roll aléatoire des persos** ; =1 → char-select).
⇒ Sélectionner ARCADE laisse `0xb84200=7` → le combat **saute le char-select et re-tire les persos**
(= "combat direct aléatoire, pas de char-select"). **arcade_launch DOIT forcer `0xb84200=1`** pour
basculer en route char-select. (v22 l'avait oublié → bug ; v22b corrige.)
Savestate v22 (fight1) : `0xb84200=0x07`, persos aléatoires (P1=0x01/cur0x31, P2=0x0b/cur0x4b),
index=0, latched=0 → confirme : fight 1 partait en skip à cause du curseur 7 résiduel.

### ⭐ ROUTE = SKIP re-roll, CHAR-SELECT respecte (savestate v19, 2026-06-24)
Savestate combat enchaîné v19 (route skip 0xb84200=7) : mes flags TOUS corrects (latch=Akuma,
index=1, write-done=1) MAIS persos réels aléatoires (P1=0x0a/cur0x6a, P2=0x03/cur0x03) ≠ mes
écritures. ⇒ **le skip re-tire les persos DANS LE SPAWN, après mon hook init-combat** → tout pin
est écrasé. C'est LA cause du "aléatoire". La route **char-select (subphase=2, 0xb84200=1) respecte
les curseurs** (pas de re-roll) = la seule voie pour P1 fixe. v22b = route char-select + override P2
à la sortie char-select (`0x5c55dc`, fire chaque combat) + groove restore. P1 non touché (gardé).


## 📡 IMPACT DU WIDESCREEN v10 SUR L'ARCADE (2026-07-12 — voir PROJET-Anthology-Widescreen-Tiles.md)
- **Le widescreen est LIVRÉ en ISO bakée** (`SFA Anthology [Widescreen] (USA).iso`, patcher
  `hyper_re\sfa_anthology_ws_patcher.py`). **CRC de l'ISO patchée = 72CE7A38** (le SLUS est modifié)
  → **le pnach arcade `SLUS-21317_72CE7A78.pnach` NE S'APPLIQUE PLUS sur cette ISO.**
  Court terme : dupliquer le pnach en `SLUS-21317_72CE7A38.pnach` pour jouer arcade+widescreen.
- **Le bake arcade en ISO est DÉBLOQUÉ** : `anthology_extract\compress_opt.py` (recompresseur MWo3
  à parse optimal DP, 2026-07-12) recompresse zb/zero9 patchés AVEC caves de code de façon fiable
  (round-trip vérifié ; patch_reemit casse sur les caves, mwo3_codec.compress dépasse le slot).
  ⇒ le mode arcade peut devenir une ISO autonome (cave + redirections dans zero9 recompressé),
  idéalement en AJOUTANT les patches arcade au patcher widescreen (squelette tout prêt : table
  {va: (vanilla, patché)} + caves + vérifs).
- ⚠️ Espaces occupés par le widescreen (ne plus les utiliser pour l'arcade) : caves zb
  0x1d7e90–0x1d7f6x ; RAM libre 0x1580000–~0x1690000 (buffers templates relogés). Le padding de
  FIN du SLUS (0x18b60c) n'est PAS file-backed (cave impossible) ; les trous zéros du MILIEU du
  SLUS sont file-backed et utilisables.


## 🏁 CLÔTURE DU CHANTIER ARCADE (2026-07-19) — v30 pnach + BAKE ISO VALIDÉS

Le mode arcade est TERMINÉ sous ses deux formes. Ce doc reste l'historique de travail ;
**la référence à jour est `ARCADE-Hyper-SFA.md`** (architecture §2-3, contraintes §4 dont
le risque multi-jeux §4.1bis, bake §8).

### Chronologie finale
- **v28** (2026-06-24) : mode fonctionnel complet (pnach).
- **v29** (2026-07-05, revue de code) : retrait de la ligne diag `019d2fa5=1` qui forçait
  P2=CPU même en VERSUS ; VS MODE save/restore par arcade_launch/modesel_clear (`0x1c010c`).
- **v30** (2026-07-18) : label « ARCADE » au menu. RE complet du mode-select : table de
  **7 pointeurs de labels à `0x69cf54`** (un par curseur, 0=ARCADE 1=VERSUS 2=SURVIVAL
  3=DRAMATIC 4=TRAINING 5=OPTION 6=EXIT — entrées Capcom d'ORIGINE toutes présentes dans
  zero9 !), entrée = {header 0xa, nb lettres, ptr table-X centrage `0x69d070`, lettres u16
  `0x02xx`}. Le curseur 7 lisait table[7] hors table → label vide. Fix pnach : copie de
  l'entrée ARCADE en cave + write table[7] à l'init menu (`0x5b4230`) et par frame menu.
  Sprites 8×8 du menu : listes `0xb90000/0xb92000` {x,y,tuile,attr}, police tuile =
  `0x12c1 + char - 'A'` (art résident) — validé in-game.
- **BAKE ISO** (2026-07-19) : `SFA Anthology [Widescreen] (USA) [Arcade].iso` **validée
  in-game**. Découvertes clés : mapping e544 décompressé = **EE − 0x1F0000** (0x1c0000 pas
  file-backed → caves relogées `0x5CEF00`, zone zéros file-backed) ; label = pur data baké
  (table[7] → `0x5CF0E0`) ; recompression par **SPLICE chirurgical** (`mwo3_splice.py`) car
  compress_opt inutilisable à 10 Mo. **CRASH INSTRUCTIF splice v1** : le décompresseur réel
  `FUN_148698` copie en do/while → token longueur 0 = runaway (FQC=0 VIF) ; v2 scinde des
  matchs pour tomber sur 16 entrées pile + validation `decompress_strict`.
- **Risque multi-jeux du pnach PROUVÉ** : les adresses zero9 (0x5b5e9c…) = code MIPS dans
  Upper → un pnach coché pendant un autre jeu écrase ses instructions. L'ISO bakée élimine
  le problème (e544 seul modifié). Cheat à ne cocher que pour Hyper (ou jamais, avec l'ISO).

### Restes ouverts (hors périmètre arcade)
- Auto-P2 (1 appui pad 2) — rouvrable en patch de code zero9 direct via le bake.
- Boot-skip logos.
- **Prochaine étape du projet global : CROSS-STAGE (AXE B)** — voir
  `PROJET-Anthology-Widescreen-Tiles.md` §4 (conflits, dont zones file-backed zero9 :
  `0x5CEF00` occupée par l'arcade, `0x5D16F0` libre) et `ANALYSE-Cross-Stage-Multi.md`.
