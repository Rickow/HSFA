# Loader multi-stage Hyper SFA — Spec d'implémentation (état au 2026-06-28)

But : perso → stage maison pour TOUS les persos. Charger le stage par match dans la RAM libre + repointer.
Résident jamais touché. Ce doc = tout ce qu'il faut pour coder + tester le loader.

## A. DONNÉES — package stage (FAIT ✅, vérifié hors-ligne)
- Builder : voir commande qui a produit `E:\tmp\stage_upper_pkg.bin` (147 Ko brut) / `.mwo3` (65 Ko compressé) /
  `stage_upper_remap.json`.
- Contenu package (`UPST` header) : `{u32 ntiles, u32 nused, u32 rsv}` + **buffer tuiles compact** (2683
  tuiles × 0x20 = 83 Ko, indices 0x1..N) + **tilemap composée remappée** (4 couches × 0x4000 = 64 Ko).
- **Remap** : les 2682 tuiles Upper distinctes (épars 0x1..0xfffe) → indices compacts 0x1..0x97f. La tilemap
  composée a ses valeurs de tuiles remappées. **Reconstruction vérifiée identique** (compact==original).
- ⇒ un stage = **65 Ko compressé** → 15-20 stages = ~1.2 Mo (large dans l'ISO), charge en **147 Ko RAM**.
- Pour les autres stages : rejouer le builder sur un savestate Upper de chaque stage (ou décoder la source
  zero5). Pipeline build-time identique.

## B. RAM — où charger
- **Zone libre confirmée : 0x1580000–0x19d0000 = 4.4 Mo** (vide dans TOUS les dumps : combat, s10, stage3…).
- Plan d'adressage proposé pour un stage chargé :
  - tuiles compact → `0x1580000` (83 Ko)
  - tilemap composée → `0x1600000` (64 Ko)  (ou la laisser dans le buffer 0xba0000 via composeur, cf. D)
  - palette → `0x1620000` (TODO localiser/format)
- ⚠️ La queue de load elle-même est à **0x19d7000** (hors de la zone libre, OK).

## C. RENDER — repoint (100% pointer-driven, CONFIRMÉ par RE)
Tout le rendu suit des pointeurs en DATA. Pour afficher le stage chargé :
- **Bank tuiles** : struct BG `0x1dc2b0+0x34` = `0x1dc2e4` (vaut 0xdb4000). → écrire `0x1580000`.
  (le drawer lit ce pointeur à chaque frame : aucun builder const de 0xdb4000, c'est bien un pointeur data.)
- **Source tilemap** : descripteur `0xbe2180` (+0=source 0xb90000, dims 64×16) câblé dans struct via
  `[0x1dc2b0]+0xd0..0xe8` (par `FUN_21fcfc`). `FUN_22daa4` pose ces valeurs. Repointer +0 → tilemap chargée.
- Table buffers couches : `0xb84130` (0xba0000/4000/8000/c000) — en data.
- **Palette** : TODO (GS-uploadée, pas trouvée dans la struct ; démarrer avec la palette zero9 = géométrie OK,
  couleurs à corriger après).
- Struct BG `0x1dc2b0` autres champs : +0x04=0x22da00, +0x38=0x108c000 (gfx2), +0x3c, +0x44.

## D. Deux variantes de rendu pour le prototype
1. **Variante composeur (scrolle, propre)** : fournir la tilemap au FORMAT SOURCE (strips+index, multi-niveau :
   descripteur 0xbe2180 → table de pointeurs colonnes 0xb90000 → strips type 0x644000/0xd1e1xx dans le prog).
   Repointer 0xbe2180 → source chargée. Le composeur (`FUN_2517e0`, copie |0xf000, 31-32 lignes×16 u16)
   construit 0xba0000/frame ⇒ scroll natif. → demande de produire la source au format strips (le + de travail).
2. **Variante directe (statique, plus simple pour 1er test)** : écrire la tilemap composée remappée (du package)
   directement dans 0xba0000-0xbac000 chaque frame (cave memcpy 64 Ko) + repoint bank. Pas de scroll mais
   prouve le cross-stage de bout en bout. **Recommandé pour le 1er proto.**

## E. LOAD — mécanisme (queue framework, partiellement reversé)
- `FUN_154db0` = machine à états poller (par frame). Queue base = **0x19d7000** (init `FUN_154bc0` :
  `uRam001a2440=0x19d7000`, zéro 0x2000 = 0x80 entrées × 0x40). Flag non-vide = `0x1a2450`. Index process = `0x1a2454`.
- **Format entrée (0x40 o)** : +0x00 u16 flags | +0x02 u16 id1 | +0x04 u16 id2 | +0x06 u16 arg3 |
  +0x08 u32 src | +0x0c u32 dst | +0x10.. filename.
  - `(flags&3)==1` → load par ID (`func_128bd0(id1,id2)`) ; sinon par filename (+0x10).
  - completion : `flags&0x40` → **`FUN_148698(src,dst)` = décompresse MWo3** ; `flags&0x80` → `FUN_155d40`+`152b0`.
- **✅ API D'ENQUEUE TROUVÉE** (3 fonctions, écrivent l'entrée + avancent la TAIL `0x1a2458` &0x7f) :
  - `FUN_154c1c(id1,id2,src)` = load simple (pas de flag).
  - **`FUN_154c9c(id1,id2,src,dst)` = load + DÉCOMPRESSE MWo3** (set flag 0x40) ← **CELLE À UTILISER** :
    charge le fichier (id1,id2) dans `src`, puis `FUN_148698(src,dst)` décompresse src→dst.
  - `FUN_154d2c(id1,id2,src,arg3)` = load + flag 0x80 (chemin 155d40).
  - ⚠️ Ces fns lisent `v0`/`v1` implicites : `v0`=0x1a0000 (base, *(v0+0x2440)=queue 0x19d7000), `v1`=tail
    (`uRam001a2458`). Donc un wrapper pose v0=0x1a0000, v1=[0x1a2458] avant l'appel. Le cave doit faire pareil.
  - Ouverture fichier : `func_128c18(id1,id2)` (par id, via wrapper `FUN_128bd0`) ou `func_1288b0` (par nom,
    via `FUN_128868`). **Convention id1/id2 = à découvrir au RUNTIME** : breakpoint PCSX2 sur `FUN_154c9c`
    (0x154c9c) pendant un chargement connu de zero9 → lire a0/a1/a2/a3 → en déduire id1/id2 + src buffer.
- ⇒ **Le cave PEUT charger mon package** : `FUN_154c9c(id_package, ?, src_temp, 0x1580000)`. Reste à
  connaître l'id du package (= l'ajouter à l'AFS et lire la convention au runtime).

### ✅✅ PIPELINE LOAD COMPLET REVERSÉ (2026-06-28, via breakpoint write 0xDB5000 de Rickow)
Chemin de chargement bank confirmé (zb `FUN_1c9290`) + **convention file_ref = INDEX AFS** (prouvé : struct
load @0x1dbc30 +0x0c = 0x220 = 544 = e544). API utilisables depuis le cave :
- **`FUN_154b00(0, index_AFS, buffer)`** = lit un fichier dans `buffer` (SYNCHRONE : boucle open→read→poll
  jusqu'à fini ; appelle `FUN_128bd0`/open, `FUN_1292e8`/read). Renvoie taille en secteurs (<<0xb).
- **`FUN_148698(src, dst)`** = décompresse MWo3 src→dst (CONFIRMÉ a0=src,a1=dst ; vu en action @0x148738
  écrivant a3=0xDB5000 depuis a0=src). Variante async : `FUN_154c9c(id1,id2,src,dst)` enqueue load+décompresse.
- poll async : `FUN_155070()` renvoie `uRam001a2450` (queue vide = 0 = fini).
- **CAVE LOADER (variante synchrone, la + simple)** :
  ```
  FUN_154b00(0, INDEX_PACKAGE, 0x1600000)   # lit mon package (compressé) → scratch 0x1600000
  FUN_148698(0x1600000, 0x1580000)          # décompresse → 0x1580000 (= header+tuiles+tilemap)
  # parse package: tuiles → repoint bank ; tilemap → 0xba0000 ; (palette TODO)
  *0x1dc2e4 = <addr tuiles dans 0x1580000>   # repoint bank
  memcpy(0xba0000, <tilemap>, 0x10000)       # variante statique D2
  ```
- ⇒ **plus aucune inconnue RE bloquante.** Reste : (1) ajouter le package à l'AFS/ISO (index connu),
  (2) coder le cave + trouver le hook par-frame, (3) palette, (4) TEST PCSX2.

## F. CAVE — pseudocode (à coder + TESTER avec Rickow, non testable en aveugle)
```
hook par-frame (technique data-redirect comme arcade mode, cave @0x1c0000) :
  si stage courant == stage maison du perso ET pas encore chargé :
     [option boot-preload : le package est déjà en RAM via la liste de load étendue]
     OU [enqueue : écrire entrée queue {flags=1|0x40, id=package, dst=0x1580000}, set 0x1a2450]
     attendre completion (poll), puis :
       *0x1dc2e4 = 0x1580000                      # repoint bank
       [variante D2] memcpy(0xba0000, tilemap_chargee, 0x10000) chaque frame
       [palette] set palette (TODO)
```

## G. PLAN D'EXÉCUTION (ordre recommandé, avec points de test)
1. **Trouver l'enqueueur / liste de load boot** (1 passe pyghidra : writers de 0x19d7000 / tail 0x1a2454).
   → débloque "mettre le package en RAM". C'EST LE BLOCANT PRINCIPAL.
2. **Proto variante D2 (statique)** : package en RAM (via 1) + cave repoint bank + memcpy tilemap → 0xba0000.
   TEST : le décor Upper apparaît en combat (statique), résident/menus intacts. Valide l'archi.
3. **Palette** : localiser (GS upload) + charger/repointer. TEST couleurs.
4. **Variante D1 (scroll)** : produire la source strips, repoint 0xbe2180. TEST scroll.
5. **Multi-stage** : package par stage + table perso→stage maison + enqueue dynamique par match.

## H. État des fichiers
- `E:\tmp\stage_upper_pkg.bin` / `.mwo3` / `stage_upper_remap.json` — package stage 0x8 (Upper), prêt.
- `E:\tmp\ee_upper_combat.bin` — savestate zero5 Upper (source des captures stage).
- `mwo3_codec.py` — codec. Repack X_DATA in-place (si fichier rentre dans son slot).
- Démo mono-stage (overwrite résident) : prouvée rendable (savestate 10) mais NON scalable (abandonnée).
```
