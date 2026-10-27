# HSFA — Widescreen & patch ISO : état (2026-06-24)

## Résumé exécutif
- **Arcade** = livré et fonctionnel en **runtime (pnach v28)** : P1 fixe + P2 ladder + P2 CPU + KO +
  skip handicap. (Seul accroc : valider P2 au pad 2.) Voir `PROJET-Hyper-Arcade.md`.
- **Widescreen** = **prouvé** (fond en vrai 16:9 vu une fois) mais **non déployable stablement** par
  les 3 voies runtime (voir murs ci-dessous). Voie propre = **patch ISO**, qui exige de craquer la
  compression **MWo3** (gros chantier, démarré).

## Widescreen — mécanisme & murs
Le rendu CPS2 384px (0x180) est élargissable à 448 (0x1c0) :
- **Viewport** (largeur render-target) : descripteur `[0x19e448]+0x494`, posé par le code à
  **`0x14ac28`** / `0x14b070` / `0x14b0a0` (immédiats `0x180`→`0x1c0`). **Dans `SLUS_213.17`** (à plat,
  patchable ISO : fileoff = VA − 0x100000 + 0x200 ; ex. `0x14ac28` → ISO `0x188e28`).
- **Tiles BG** (nb colonnes par calque) : `0x1d19b0`/`0x1d1b9c` (8px 0x31→0x39),
  `0x1d1f7c`/`0x2140`/`0x223c` (16px 0x19→0x1d), `0x1d2360` (32px 0xd→0xf). **PAS dans SLUS** (VA
  `0x1c0000`+ = overlay émulateur séparé, sous le load de zero9 `0x1f0000`).

**3 murs runtime :**
| Voie | Mur |
|---|---|
| pnach statique (code) | crash shell au boot (RAM partagée même CRC : assertion VIF1 FQC=0) |
| runtime SMC gated | course/instable : fond 16:9 OK une fois, calque sol manquant + crash autre stage |
| ISO direct | overlay tiles **compressé MWo3** (non décompressé) |

**Constat art** : l'art CPS2 dépasse 384 pour CERTAINS calques/stages seulement (le fond oui, le
sol non sur certains stages) → un 16:9 robuste demande un audit calque-par-calque + clamp.

## Patch ISO — structure (vérifiée)
ISO `Hyper Street Fighter Alpha (USA).iso` (4,7 Go, déjà patchée xdelta pour déverrouiller HSFA).
Fichiers ISO9660 : `SLUS_213.17` (572 Ko = ELF EE, 1 segment code VA `0x100000` fileoff `0x200`
taille `0x8b680`), `X_DATA.BIN` / `Y_DATA.BIN` (archives **AFS** CRI : conteneurs MWo3 + gfx + audio).
- **Viewport = patchable ISO directement** (dans SLUS, à plat). Mais seul = bord noir/doublon
  (il faut aussi les tiles).
- **Tiles + char-select + tables arcade = dans des overlays MWo3 compressés** (X_DATA.BIN).

## ⭐ MWo3 — DÉCOMPRESSION (percée 2026-06-24, à finir)
- Format documenté par la **communauté GTA** : GTAMods Wiki « PS2 Code Overlay ». Header (depuis
  le magic) : `MWo3`(4) + nb_seg?(4) + load_addr(4) + text_size(4) + data_size(4) + bss_size(4) +
  cb_start(4) + cb_end(4) + filename(32). **HSFA = conteneur `zero9`** (`ro9_usa_prog68k.mwo3`,
  3,5 Mo → décompressé **~10 Mo** : text `0x3bf140` + data `0x5b8080`, **load VA `0x1f0000`**).
- **Le décompressé EST dans le dump** à `0x1f0000` (header `MWo3` + `zero9_usa.bin` propre + code).
  ⇒ le contenu cible est connu ; reste à reproduire la (dé)compression.
- **Algo = LZ77 type kid23/SRWZ** (`github.com/kid23/PS2_Projects`, `SRWZ/src/MWo3uncompress.cpp`) :
  octet de contrôle = nibble bas (nb littéraux) / nibble haut (nb matchs) ; 0 → varint `getnum`
  (lit des octets `num=(num<<7)|b` jusqu'à `num&1`, renvoie `num>>1`). Match : nibble bas = offset,
  nibble haut = longueur ; copie depuis `dst-pos-1`, `num+1` octets.
- **⚠️ Ma réimpl ne matche pas exactement** (variante Anthology vs SRWZ ; meilleur 19/64 sur le
  header). Le `02 00` initial + l'offset de départ du flux ne sont pas résolus. **Le codec exact est
  dans `SLUS_213.17`** (mais pas de comparaison au magic `MWo3` trouvée → appelé par le loader AFS).

## Prochaines actions (projet ISO, par ordre)
1. **(A) RE du codec MWo3 dans SLUS** : suivre le loader AFS / les `lui 0x1f` du buffer `0x1f0000`
   jusqu'à la routine de décompression ; en extraire l'algo exact (decomp). Puis le compresseur
   (kid23 `MWo3compress.cpp` comme base, à adapter).
2. Localiser l'**overlay des tiles** (`0x1c0000`, ≠ zero9) dans X_DATA et le craquer pareil.
3. Patcher décompressé → recompresser → réinjecter dans l'AFS (offsets alignés 0x800) → régénérer
   l'ISO. (Pas de checksum côté jeu — krat0s : ROM éditable en place.)
4. Arcade en ISO : le code-cave (`0x1c0000`) + redirections (tables char-select `0x5c55d0` etc.,
   dans zero9) → tout dans le binaire patché. Unifie arcade + widescreen sans contrainte shell-safe.

## Fichiers
- Décompressé de référence : dump `eeMemory_versus.bin` @ `0x1f0000` (zero9 chargé).
- Conteneur MWo3 HSFA : `E:\CLAUDE CODE\anthology_extract\ro9_usa_prog68k.mwo3`.
- Extracteur AFS : `E:\CLAUDE CODE\extract_anthology.py`. Carto : `project_sfa_anthology` (mémoire).

## A — RE codec MWo3 : progrès session 2026-06-24
- **Routine de traitement overlay = `0x151fc0`** (SLUS) : opère sur l'en-tête MWo3 **DÉCOMPRESSÉ**
  (pointé par s3). Lit **3 paires (offset, taille)** de segments (s3+8/+0xc, s3+0x10/+0x14,
  s3+0x18/+0x1c) ; calcule des pointeurs `s3+offset` ; appelle l'**allocateur `0x1478f0`** (appelé
  uniquement depuis `0x15205c`). L'allocateur valide contre `0x1ffff1` (haut du buffer `0x1f0000`)
  et enregistre les segments dans une **table à `0x19e030`** (tag `0x4d......`='M').
- ⇒ **La décompression est EN AMONT** (chemin de lecture AFS : lire zero9 compressé de X_DATA →
  décompresser vers `0x1f0000` → `0x151fc0` traite l'en-tête). Le décompresseur = au-dessus de
  `0x151fc0` dans la chaîne (loader AFS). **Prochain pas : remonter les appelants de la fonction
  contenant `0x151fc0`, trouver la lecture AFS + l'appel decompress(src_compresse, dst=0x1f0000).**
- **Format** : ne matche pas kid23 exactement. Tokens observés (alignement compressé↔décompressé) :
  literal-run de 28o "MWo3..72 b6 00" précédé de `02 00` ; token `02 10`→backref(off=4,len=4) ;
  puis "ze" + token `00 03`→"ro" (backref énigmatique, pas de "ro" antérieur) → l'encodage exact
  reste à tirer du décompresseur SLUS (autoritaire). Atout : paire (compressé `ro9...mwo3` ↔
  décompressé dump@`0x1f0000`) pour valider toute hypothèse octet à octet.

### Tokens MWo3 exacts (alignement validé, 2026-06-24)
Paire C=`ro9...mwo3` / D=dump@`0x1f0000` :
- `C[0:2]=02 00` → **28 littéraux** (D[0:0x1c] = "MWo3…72 b6 00", copiés de C[2:0x1e]).
- `C[0x1e:0x20]=02 10` → **backref offset=4 longueur=4** (D[0x1c:0x20]="00 72 b6 00").
- `C[0x22:0x24]=00 03` → **12 littéraux** (D[0x22:0x2e]="ro9_usa.bin\0", copiés de C[0x24:0x30]).
  (entre les deux : `C[0x20:0x22]=7a 65` = 2 littéraux "ze".)
**Encodage des comptes/offsets NON résolu** : ni kid23 (getnum/nibbles), ni LZSS, ni varint simple.
⇒ **Lire la boucle de décompression dans SLUS** (voisinage `0x147xxx`, chemin AFS au-dessus de
`0x151f40`) pour l'algo exact. Atout : tout se valide sur la paire. Décompresseur écrit vers `0x1f0000`.

### Passe décompresseur (2026-06-24) — non localisé en statique
- Recherche signature varint `sll reg,reg,7` dans SLUS : candidats `0x14aa6c`/`0x14aa94` = code
  d'AFFICHAGE (`0x14aa30`, lit le descripteur `[0x19e448]`+0x4a0/4a4/4c5 ; `sll,7` = `(x*128)/div`
  mise à l'échelle, PAS un varint). Cluster `0x155xxx` non vérifié.
- La variante Anthology ne matche ni kid23 (getnum `<<7`/nibbles), ni LZSS/varint simple.
- **CONCLUSION** : isoler le décompresseur MWo3 dépasse le RE statique Python ici. Voies adaptées :
  (1) **Ghidra** sur `SLUS_213.17` @0x100000 (suivre loader AFS → `decompress(src,dst=0x1f0000)`);
  (2) **trace runtime PCSX2** : BP write/exec autour de `0x1f0000` pour capter l'algo en action.
- Prêt pour ces voies : paire de validation, tokens de référence, chaîne loader (`0x147xxx`→`0x151fc0`).

### Passe pyghidra (2026-06-24) — chaîne loader mappée, décompresseur PAS sur l'EE
**pyghidra opérationnel sur SLUS** : projet `E:\CLAUDE CODE\ghidra_sfa3\` (project "slus"), lang
`r5900:LE:32` (ext ee-reloaded), scripts `gh_slus*.py`. SLUS extrait : `E:\tmp\SLUS_213.17`.
Chaîne de chargement overlay (décompilée, lisible) :
- `FUN_154db0` = state-machine de chargement async (ouvre fichier `FUN_128868/128bd0`, lit
  `FUN_1292e8`→`129340`→`129148`→**`128e98` = read streamé par secteurs** `<<11`, poll `129bb0`).
  Quand fini + flag overlay (`*puVar4 & 0x80`) → `FUN_155d40` (register callbacks) + `FUN_1520b0`.
- `FUN_1520b0`→`FUN_151f40` : lit l'en-tête (DÉCOMPRESSÉ) du buffer `param_2` : 3 paires
  (offset `+8/+0x10/+0x18`, taille `+0xc/+0x14/+0x1c`) + callbacks `+0x20/+0x24` → `FUN_1478f0`
  (valide <`0x1ffff1`, table `0x19e030`) → `FUN_1477e0` = **enregistre les 3 segments** (ptr|taille,
  tag `0x4f`). **AUCUNE copie/décompression sur l'EE** — les segments pointent DANS le buffer reçu.
- ⇒ Comme buffer décompressé (~10 Mo) > fichier (3,5 Mo), **la décompression se fait PENDANT le
  transfert, probablement côté IOP** (modules `MODULE.BIZ`/`IOPRP.IMG` de l'ISO ; pattern PS2 std).
- Fausses pistes écartées : `sll,7` @`0x155xxx`/`0x14aa` = code AUDIO (pan/volume `*0x7f`) et
  AFFICHAGE (échelle), pas le varint. `FUN_1561c0` = nettoyage callbacks.
- **Voie la + efficace pour la suite = TRACE RUNTIME PCSX2** : breakpoint d'écriture sur le buffer
  décompressé (premier `0x1f0000`... ou trouver le buffer réel via `FUN_1298d0`) pendant un chargement
  Hyper → capter l'algo en action (que ce soit EE ou IOP). Sinon : RE des IRX IOP (toolchain IOP).

### ⭐⭐ MWo3 — BACKREF DÉCODÉ (autonome 2026-06-24, data-driven sur la paire)
Aligneur (70 tokens extraits, `E:\tmp\` script) → encodage backref :
- Token = 2 octets `[o0][o1]`. **Discriminant : `o1 >= 0x10` → BACKREF**, sinon littéraux.
- **BACKREF : `offset = o0 << 1`, `length = o1 >> 2`** (copie depuis `dst-offset`). Validé ~12 tokens :
  `02 10`→off4/len4, `08 10`→off16/len4, `06 18`→off12/len6, `40 28`→off128/len10, `1c 30`→off56/len12,
  `38 10`→off112/len4, `40 18`→off128/len6, `12 18`→off36/len6.
- (Les bits bas : `o0` bit0 et `o1` bits0-1 = extension offset/flags probable, à confirmer sur grands offsets.)
**RESTE : encodage du COMPTE DE LITTÉRAUX** (tokens `o1<0x10`). Data points :
  `02 00`→28, `00 03`→12, `00 00`→32, `42 02`→12, `1a 09`→8 ; + littéraux "sans contrôle" après backrefs
  (2,4,2,6,4,8…) → soit le backref encode aussi un litcount (bits bas), soit token litéral séparé.
  Une fois ça trouvé → décodeur complet validable sur la paire, puis recompresseur.
Aligneur : décompo C(`ro9...mwo3`)↔D(dump@0x1f0000), lit≥1/resync, backref=plus long match.

### B (stages) — mécanisme (autonome 2026-06-24)
- **3 stages** confirmés : table cycle `0x5b5cb0` (compteur `0xb84314` step2 wrap 0xc → 6 positions
  mappées sur **3 IDs distincts 0/2/4**). Param stage → `0xb88100` (via `0x5b5cb0`) + `0xb84178` (`0x5b5cc0`).
- **Stages = FICHIERS AFS** chargés par ID via le **loader générique `0x5aa5c0`** (appelé de partout :
  `0x2864f0`/`0x28fdcc` combat, `0x5088b0`/`0x508cbc` char-select…). `0x2864f0` POMPE le load async
  (`while 0x5aa5c0()!=0`) puis init-stage `0x2905c0`. ⇒ l'ID fichier du stage est posé dans la
  **requête de chargement async EN AMONT** (state-machine `0x154db0`), pas au combat.
- **Faisabilité cross-jeu = VIABLE** : le stage étant un fichier chargé par ID, le rediriger vers le
  fichier de stage d'un autre jeu (zero2…) dans X_DATA est l'angle. Reste : (1) localiser la pose de
  l'ID fichier stage (requête async) ; (2) vérifier format compatible (probable, même moteur CPS2).
  Tout au RUNTIME (pnach), comme l'arcade — ni MWo3 ni recompression nécessaires pour CE point.

### ⭐⭐⭐ MWo3 — DÉCODEUR VALIDÉ 4048 octets + format 2-FLUX (autonome 2026-06-24)
- **BACKREF CRACKÉ & VALIDÉ** : décodeur reproduit **0xfd0 octets EXACTEMENT (100%)** avant de caler.
  Unité = token 2 octets `[o0][o1]` : si `o1>=0x10` → backref `off=o0<<1, len=o1>>2` (copie `dst-off`).
- **Littéraux = format À DEUX FLUX** (preuve) : le token `02 00` produit **28 octets (header)** au début
  MAIS devrait produire des **zéros** à out=0x32 (après le nom de fichier). Même token, sortie ≠ ⇒ les
  littéraux ne sont PAS inline ; il y a un **pool de littéraux séparé avec son propre pointeur**.
  ⇒ colle à l'indice GTA « conteneur de 2 fichiers ». Le décodeur greedy (lit tant que C==D) marche
  jusqu'au 1er run de zéros puis cale (`02 00` @0x32, is_br=None, C[ci]=27 ≠ D=00).
- **RESTE** : trouver la structure/pointeur du flux littéraux (compte par token `o1<0x10` + d'où viennent
  les octets). Piste : code décompresseur **IOP** (`MODULE.BIZ`/`IOPRP.IMG`, R3000) — l'EE ne fait que
  registrer les segments. Décodeur partiel sauvé : `anthology_extract\mwo3_decode.py`.

### B (stages) — VERDICT DÉFINITIF (autonome 2026-06-24, suite)
**Le dump entier ne référence que 2 noms de fichiers** : `zero9_usa.bin` (@0x1f0000, le jeu) et
`sub_usa.bin` (@0x1c0000, sub/BIOS). ⇒ **AUCUN load par stage ni par perso** : tout (persos, 3 stages,
GFX) est dans `zero9_usa.bin`, **résident**. Le loader par nom (state-machine `0x154db0`, table requêtes
`0x1a2440`, by-index `128bd0`/by-name `128868`) ne charge que ces 2 blobs au boot. Le « load » pompé par
`0x2864f0` au combat = décompression/copie depuis la data résidente, pas un fichier de stage.
- **Conséquence** : « rediriger l'ID fichier du stage » = IMPOSSIBLE (pas de tel fichier). `init-stage
  0x2905c0` ne charge rien (confirme résident).
- **Vrai cross-jeu = gros projet** : soit (1) charger `zero2_usa.bin` en + de zero9 (loader by-name le
  permet) PUIS rediriger les pointeurs tilemap/GFX du moteur stage HSFA vers la data zero2 (2 layouts
  MIPS-recompilés différents, ~+10 Mo RAM, multi-semaines) ; soit (2) cuire le stage dans zero9 (ISO+MWo3,
  besoin du crack flux littéraux).
- **Atteignable (esprit de l'idée Rickow)** : contrôler lequel des **3 stages résidents** via la table
  `0x5b5cb0` (DATA, shell-safe). Test ajouté au pnach : section **[Stage Test]** force ID=4 partout.
  Hook groove→stage = nécessite un point de redirection (function-ptr) près de l'init-stage, à trouver.

### ⭐ ARTICULATION SLUS ↔ JEUX (autonome 2026-06-24, choix 2)
**SLUS_213.17 = LOADER + FRAMEWORK uniquement** (`0x100000`–`0x18b680`, ~570 Ko). Le JEU est dans le blob.
Carte du chargement (tout dans SLUS) :
- **AFS read** `0x1520e0` (→`147c90`/`147e10`) ; **sector read** `0x128xxx` (`<<11`=×2048).
- **State-machine de chargement** `0x154db0` : table de requêtes `0x1a2440` (entrées 0x40 o), charge
  **by-index** (`128bd0`) ou **by-name** (`128868`, chaîne à entry+0x10, `/`→`\`). Globals : `0x1a2450`
  (flag), `0x1a2451` (état 0/1/2), `0x1a2454` (idx courant), `0x1a245c` (handle).
- **Registration segments** `0x151f40(slot,hdr)` : table modules `0x1a1400` (8 slots ×0x208). Lit le
  header MWo3 : sous-table @hdr+0x20 (count hdr+0x24, entrées 0x10 o), puis 3 paires (ptr,size) à
  hdr+8/+0xc, +0x10/+0x14, +0x18/+0x1c → `0x1478f0`/`0x1477e0` qui enregistrent dans la **ring table
  `0x19e030`** (0x20 entrées ×8 o) avec **tags 'M'=0x4d / 'O'=0x4f** (= MWo3). Bornes seg < 0x1ffff1.
- **PAS DE DÉCOMPRESSION dans le chemin EE** : les segments pointent dans de la data **déjà
  décompressée**. (`0x155d40`/`0x1561c0` = nettoyage slots ; `0x150f10` = dé-planar GFX ; `0x128400` =
  parse table segments — aucun = LZ.) ⇒ **décompression MWo3 = IOP** (fichier arrive décompressé via DMA).
- **Logique jeu (combat/stage/char)** = dans le blob `0x1f0000`+ (zero9), PAS dans SLUS.
**Implication choix 2** : pour étudier zero1-8, le plus rapide = **dumps RAM PCSX2** (l'IOP décompresse
pour nous, comme zero9/zero3 déjà dumpés). Le codec MWo3 offline (RE IOP) n'est requis qu'à la FIN pour
**re-cuire** le zero9 modifié dans l'ISO. Modules IOP à RE : `IOPRP.IMG`/`MODULE.BIZ` (R3000).

### ⭐⭐⭐ B (cross-stage) — DATA DE STAGE LOCALISÉE + FORMAT IDENTIQUE PROUVÉ (autonome 2026-06-24)
Renderer BG (du travail widescreen) : orchestrateur `0x1d0854` (4 couches) → drawer `0x1d18a0`.
Le drawer lit la data de stage via la **struct état-couches `[0x1dc078] = 0x1dc2b0`** :
- **`+0x04` = pointeur TILEMAP** (entrée = [0]=index tuile, [1]=attr : palette `(attr&0x1f)+0x20`, flip `attr&0x60`).
- **`+0x34` = pointeur TILE GFX base** (tuiles CPS2 4bpp, 0x20 o/tuile ; indexé `base + tile_idx*0x20`).
- **`+0x38` = GFX2 bank**, `+0xd4`/`+0xe4` = scroll, `+0x100` = compteur tuiles dessinées (0x58d=0x31*0x1d).
**FORMAT IDENTIQUE zero9 ↔ zero3 PROUVÉ** : même `[0x1dc078]=0x1dc2b0`, même layout struct ; seules les
valeurs (adresses data) diffèrent :
- zero9/HSFA : tilemap=0x22da00, tileGFX=0xdb4000, GFX2=0x108c000, scroll=0xbe2184
- zero3/SFA3 : tilemap=0x2826b0, tileGFX=0xc02800, GFX2=0x112a000, scroll=0x962184
Tailles : tileGFX bank ~2 Mo (partagée stage+persos), tilemap ~128 Ko, GFX2 ~302 Ko → **trop gros pour
pnach** ⇒ méthode = **REPOINT** de la struct `0x1dc2b0` (pas copie). 
**Conclusion : cross-stage PROUVÉ faisable** (moteur/format identiques). ISO = data stage zero3 en fichier
AFS non compressé + patch SLUS (load + repoint) → **sans MWo3**. Reste = ingénierie définie :
(1) cerner l'extent EXACT d'une stage zero3 (sous-ensemble tuiles référencé par sa tilemap + palette) ;
(2) charger en RAM ; (3) repointer `0x1dc2b0`. Dumps : ee_std.bin (zero3), eeMemory_versus.bin (zero9).

### Option 2 — extent stage (autonome 2026-06-24, CORRECTION adresses)
Le drawer `0x1d18a0` : tilemap via `[0x1d0e90(col)+4]` où `0x1d0e90` retourne `[0x1dc070]`(=0x1dc080) ou
`[0x1dc074]`(=0x1dc198) selon seuil — **PAS** `[0x1dc078]`. Adresses RÉELLES (zero9) :
- **Descripteurs couches** : `[0x1dc070]`→0x1dc080, `[0x1dc074]`→0x1dc198, `[0x1dc078]`→0x1dc2b0.
- **TILEMAP = `0xba0000`** (les deux couches L070/L074 pointent dessus ; +4). ~36 Ko (0x8cfe), **organisée
  en BLOCS** (adressage `(y&0xf8)>>1 + (x&0xf8)*0x10 + bank*0x2000/0x1000`, pas linéaire). Tuiles dominantes
  0x20/0x1020/0xc0. Palettes (attr&0x1f) = 0..23 → indices palette 0x20-0x37.
- **TILE GFX = `0xdb4000`** = `[0x1dc078]+0x34` (bank PARTAGÉE ~2 Mo : tuiles stage + persos).
- Descripteur +0x34 (L070/L074) = 0xf (count/flag), pas un ptr GFX.
**Extent précis d'une stage = TODO** : répliquer l'adressage par blocs de la tilemap pour (a) isoler les
tuiles de la STAGE des tuiles persos dans la bank partagée 0xdb4000, (b) borner proprement. = prochaine
tâche focalisée avant extraction. Palette RAM (drawer `0x1d3d80`, idx (attr&0x1f)+0x20) : adresse à trouver.

### Carte buffers BG + architecture rendu stage (autonome 2026-06-24, FIN phase recon)
`FUN_21d688` assigne les bases buffers BG dans la struct (base 0xb88000) :
- `0xba0000`/`0xba4000`/`0xba8000`/`0xbac000` = **tilemaps des 4 couches BG** (struct-0x3ed0/-0x3ecc/-0x3ec8/-0x3ec0)
- `0xbc8000` = buffer extra (struct-0x3eac) ; struct+0xe0 = 0xbac000.
**Pipeline complet** : logique jeu → données scroll CPS2 → compositeur `0x21dxxx` → tilemaps 0xba0000+ →
drawers `0x1d18a0…` (tilemap + tile GFX `0xdb4000` décodé ROM CPS2 + palette 0x20-0x37) → framebuffer GS.
`0xdb4000` (tile GFX) = **alloué dynamiquement** (pas de lui ; rempli par décodage GFX ROM CPS2). `0xba*`
(tilemaps) = **recomposées chaque frame** depuis les données scroll CPS2.
**Stage = (scroll CPS2 4 couches) + (sous-ensemble tuiles ROM GFX) + (palettes).**
=== FIN PHASE RECON cross-stage : faisabilité PROUVÉE, structures TOUTES localisées. ===
PHASE SUIVANTE (build, multi-session) : extraire la data réelle d'une stage zero3 (scroll+tuiles+palette)
via les internals émulation CPS2, charger en RAM, repointer/composer dans zero9. Sans MWo3 (fichier AFS +
patch SLUS). Dumps : ee_std.bin (zero3), eeMemory_versus.bin (zero9).

### Savestate 1 (crash) + chasse décompresseur MWo3 (autonome 2026-06-24)
**CRASH** "jump to unaligned 0x10605" : mémoire EE du dump **PROPRE** — `0x5b41f4=0x10605` est la valeur
NORMALE (identique clean vs crash, c'est une donnée de table nav, pas un ptr). `[Stage Test]` (0x5b5cb0)
ET arcade (cave 0x1c0000 vide, 0x5b422c=0) sont **OFF** dans le dump. ⇒ crash = faute de flux de contrôle
**transitoire** (mauvais jr/return), invisible en mémoire statique. Cause à corréler avec le pnach actif.
**Routage STAGE** : `0xb88100`/`0x5b5cb0` n'est **PAS** le sélecteur du BG rendu (sinon [Stage Test]
aurait tenu). Mes 2 dumps HSFA = **même stage** (tilemap/tileGFX/0xb88100 identiques) → impossible de
diff pour trouver le vrai sélecteur. **Besoin : un dump sur une AUTRE stage** → diff = la variable qui
change = le sélecteur.
**Décompresseur MWo3 INTROUVABLE** par signature backref (sll<<1~srl>>2, addu-double~>>2) dans : SLUS EE
(0x100000-0x18c000 → seulement GFX-deplanar 0x150f10 + parse-segments 0x128400 + bornes), IOP dump
(2 Mo, 1 hit = dispatch srl>>2;jalr), sub_usa (bad data), **MODULE.BIZ** (= conteneur MOMO de modules IOP
IRX : sio2man/mcserv/SPU2/MIDI/CRI-ADX = périph+audio, PAS de décompresseur), IOPRP.IMG (Sony standard).
⇒ Hypothèses : (a) dans SLUS avec pattern d'instr. non-signaturé (scan manuel du flux load requis), ou
(b) IRX résident seulement PENDANT le load → **besoin d'un savestate sur l'écran "NOW LOADING"**.
Littéraux MWo3 = 2-flux non résolu sans le code décompresseur (pair seule insuffisante : token 02 00
ambigu, "ze" littéraux sans token clair).

### Savestates CHARGEMENT HSFA (autonome 2026-06-24) — décompression EE confirmée, fonction non pinnée
2 savestates pendant "NOW LOADING" HSFA : **slot01 = 0x1f0000 COMPRESSÉ** (`02 00 MWo3 … 72 b6 00 02 10`,
backref intact) ; **slot02 = 0x1f0000 DÉCOMPRESSÉ** (`MWo3 0a 00 …`). ⇒ **décompression = EE, transforme
0x1f0000** entre les deux. Le compressé n'existe qu'à 0x1f0000 (pas de buffer temp trouvé).
**Le décompresseur n'est PAS dans la chaîne load-completion** `0x154db0` : celle-ci ne fait QUE registrer
les segments (tags M=0x4d / O=0x4f / J=0x4a dans ring `0x19e030` via `0x151f40`/`0x1478f0`/`0x1477e0`/
`0x147a30`). `0x155d40`→`0x1524b0`→`0x147a30`(tag J), `0x1561c0`(cleanup) = aucune décompression.
Introuvable aussi par : signature backref (FPs : date-calc 0x14e24c, GFX-deplanar 0x150f10, dispatch),
check magic 'MWo3' (seule occurrence 0x1c8000 = header propre de sub_usa), parse PC EE/IOP des structures
internes PCSX2 (layout non trivial, échec). **Littéraux MWo3 = 2-flux/run non dérivable de la paire seule.**
**UNBLOCK FIABLE** : breakpoint mémoire PCSX2 **sur écriture à 0x1f0030** (ou 0x1f0100) PENDANT le load
→ casse DANS le décompresseur → relever le PC EE = adresse du décompresseur → décompiler → flux littéraux.
(MWo3 N'EST PAS requis pour le cross-stage : voie sans-MWo3 = AFS séparé + patch SLUS.)

### 🎉🎉🎉 MWo3 CRACKÉ — décompresseur = SLUS `FUN_148698` (autonome 2026-06-24, via breakpoint PCSX2)
Breakpoint mémoire PCSX2 sur write 0x1F0030 pendant load → pile d'appels → décompresseur localisé.
La pile montrait l'écran de chargement (`0x1c8xxx`) → `0x1c9290` qui, après le load du compressé à 0x1f0000,
appelle **`FUN_148698(0x1f0000, dst)` = LE DÉCOMPRESSEUR**.
**FORMAT = LZSS 16-bit À MOT (LE)** — le fichier .mwo3 EST le flux direct (l'en-tête 'MWo3' = littéraux) :
- Mot de CONTRÔLE 16-bit, MSB→LSB. bit=0 → littéral (1 mot copié). bit=1 → match.
- Token match 16-bit : `len5=token>>11` ; si len5≠0 → length=len5, offset=token&0x7ff (1 mot) ;
  si len5==0 → offset=token, length=mot suivant (2 mots).
- offset==0 : length==0 → FIN ; sinon → RUN DE ZÉROS. offset>0 → backref dst-offset (en MOTS).
(Ma déduction byte-level antérieure off=o0<<1/len=o1>>2 était l'approximation de offset×2/len word-based.)
**VALIDÉ** : décompresseur reproduit zero9 à **9 925 118 / 9 925 120 octets (100%)** (2 octets = état runtime).
**Re-compresseur** écrit (greedy, offset≤0x7ff mots) : round-trip EXACT, ratio ~36% (≈ original 35%).
Codec : `anthology_extract\mwo3_codec.py` (decompress + compress). **LES 10 JEUX décompressés** dans
`anthology_extract\decompressed\` (b, zero1-9). ⇒ **Baking ISO débloqué** : décompresser zero9 → modifier
(routage stage / injection) → recompresser → remettre dans X_DATA.BIN (AFS).

### 🎉 ISO DE TEST CONSTRUITE (autonome 2026-06-24) — pipeline complet bout-en-bout
Routage stage RÉSOLU : **`0xb84178` = sélecteur causal** (index des tables BG `0x660240`/`0x664280` via
lecteurs `0x2511ac`/`0x25126c`/`0x25132c`). Le force runtime échoue (writer `0x290840` écrit juste avant
le reader, même frame). **Fix = patcher zero9** : instruction `0x290834: lh v1,0(v0)` (charge la valeur
stage depuis `0x5b5cc0[idx]`) → remplacée par **`ori v1,zero,0x18`** (`0x34030018`) → 0xb84178 toujours 0x18.
- Mapping fichier↔runtime confirmé (file 0xa0834 = runtime 0x290834, identique).
- **patch_reemit** (`anthology_extract\patch_reemit.py`) : re-émet le flux MWo3 original en rejouant ses
  tokens, ne remplaçant que les 2 mots cibles (backref→littéraux). Résultat **+6 octets** (3 502 650 vs
  3 502 644), round-trip exact, **rentre dans le slot AFS** (3 504 128, marge 1478). → `zero9_patched.mwo3`.
- **ISO** : X_DATA @ ISO 0x9f738000, zero9 @ 0xaae81000. Copie OS (60s) + patch in-place (zero9 + taille TOC
  e544→3502650). → **`E:\ROMS\PS2\...\SFA Anthology - Stage Test (USA).iso`** (4.70 Go).
TEST : lancer cette ISO, jouer plusieurs versus HSFA → si TOUS montrent le MÊME stage = lock OK = pipeline
RE+MWo3+ISO prouvé. Caveat : autres writers (`0x288758` char-select, `0x286c34` combat) pourraient
réécrire 0xb84178 sur certains chemins ; init-stage `0x290840` est le dernier avant la compo BG donc devrait
suffire. Si lock partiel → patcher aussi ces writers.

### Cross-jeu : structure d'un stage CPS2 dans le moteur (autonome 2026-06-24)
Sélecteur `0xb84178` → table `0x660240` (4 ptrs de couches/stage, offsets stage=0/8/0x10/0x18).
L0/L1/L3 partagées, **L2 unique par stage** (`0x660660`/a60/e60/`0x661260`). Les blocs (`0x660260`…) =
**tables d'indices de tuiles** (hiérarchie d'offsets). Consommateur `0x2511ac`→`0x2517b0`→**`0x2517e0`** =
remplit le buffer tilemap (`0xbac400`/`0xbacc00`) avec les indices OR 0xf000 (palette). Drawer `0x1d18a0`
lit tilemap + **tile GFX `0xdb4000`** (bank PARTAGÉE entre stages, confirmé : identique cur vs stage3) + palette.
**⇒ Un stage = (1) données d'indices de tuiles `0x660240`+ (petit) + (2) tuiles BG dans la bank GFX
partagée `0xdb4000` (le gros) + (3) palette.**
**PLAN INJECTION cross-jeu (remplacer stage 0x18 par un stage zero3, format IDENTIQUE même moteur SFA3) :**
1. Copier les blocs d'indices du stage zero3 → région `0x660240` de zero9 (petit, facile).
2. Copier les tuiles BG du stage zero3 → bank tuiles BG de zero9 (le gros : localiser la région + fit/place).
3. Copier la palette du stage zero3.
4. Recompresser zero9 (MWo3) + cuisson ISO (socle prouvé).
**PROCHAIN PAS** : localiser la bank de tuiles BG (où sont les pixels des tuiles de décor, taille/stage) dans
zero9 ET zero3 (`ee_std.bin`/`decompressed\ro3...bin`) → évaluer fit. C'est le point dur restant.

### Cross-jeu — état au cœur du morceau GFX (autonome 2026-06-24)
ACQUIS : compo BG = `0x250a20` → `0x251180`/`240`/`300` (contiennent lecteurs `0x2511ac`/`26c`/`32c`) =
remplit la TILEMAP (indices) depuis `0x660240`. Tile-index data = PETIT, localisé, copiable.
RESTE (morceau dur) : **localiser le chargement des PIXELS de tuiles BG** (la bank GFX par-stage). Tentatives
infructueuses : callers 0x150f10 (aucun dans zero9), lui 0x108 (=0x1080001 GIF, pas la bank), 0x5ad988 (idem),
0x29c050 (objets), 0x250a20 (tilemap pas GFX). La bank GFX est allouée dynamiquement → décode pas trouvé par
adresse. NEXT : tracer via struct+0x38 (ptr bank GFX2 = [0x1dc078]+0x38) le writer/décode, OU comparer
zero9↔zero3 décompressés pour isoler les régions de GFX de décor (planar CPS2). = focus prochaine session.
PLAN injection inchangé (3 composants : tile-index OK + GFX-tuiles TODO + palette). Socle ISO+MWo3 prêt.

### Cross-jeu — CORRECTION bank de tuiles (autonome 2026-06-24)
0x108c000 (GFX2, struct+0x38) = table de POINTEURS, PAS des pixels (mon erreur). Le vrai drawer BG
`0x1d1810`→`0x1d18a0` lit les pixels depuis **`0xdb4000`** (struct+0x34). **`0xdb4000` = bank de pixels
4bpp ~4 Mo (0xdb4000→0x11b3000), PARTAGÉE** (tuiles persos+décors décodées UNE fois au chargement ; identique
entre stages → le stage = tilemap qui sélectionne un sous-ensemble). Breakpoint corrigé = **write 0xDB5000
PENDANT le NOW LOADING** (décodage GFX, comme MWo3) → pile = fonction décode + SOURCE CPS2 dans zero9.
Injection cross-jeu : ajouter les tuiles de décor zero3 dans la source GFX de zero9 + tilemap (0x660240) +
palette → recompresse → ISO (socle prouvé).

### 🎉 CROSS-JEU ENTIÈREMENT CARTOGRAPHIÉ (autonome 2026-06-24, via breakpoint 0xdb5000)
Breakpoint write 0xdb5000 pendant NOW LOADING → pile : **`0x148698` (= LE DÉCOMPRESSEUR MWo3) écrit la
bank GFX**. Donc les tuiles de décor sont **MWo3-compressées**, décodées dans `0xdb4000` (bank ~4 Mo).
- **GFX décor zero9 = AFS e546** (MWo3, 1212638 o → 2981888 o) : décompresse à **100% sur 0xdb4000** (codec OK).
  (Le `20 00` au début = 1er mot de contrôle MWo3, PAS un magic — MWo3 n'a pas de magic, le 'MWo3' du prog
  était du contenu décompressé.)
- **GFX décor zero3 = AFS e256** (MWo3, 2080896 o → 4521984 o), MÊME format (`3f 33 33 f0…`).
- e256 (2.08 Mo) > slot e546 (1.21 Mo) de 866 Ko → rebuild AFS (ou extraire 1 stage subset).
**3 composants d'un stage = (1) GFX tuiles e546/e256 [MWo3] + (2) tilemap prog 0x660240 + (3) palette.**
TOUS accessibles avec les outils. Injection cross-jeu = MÉCANIQUE désormais (plus d'inconnue) :
remplacer les 3 composants du stage 0x18 par ceux d'un stage zero3 → recompresser (prog MWo3 + e256 GFX) →
AFS (rebuild si plus gros) → ISO (socle prouvé). Reste : localiser palette + tilemap zero3 + gérer la taille.

### Cross-jeu — MAPPING FINI (autonome 2026-06-24)
Les 3 composants d'un stage, localisés pour zero9 ET zero3 :
1. **GFX tuiles** : zero9 AFS **e546** (MWo3) / zero3 AFS **e256** (MWo3). Décompresse sur bank 0xdb4000.
   (Autres blobs : e545=sprites persos 10.4Mo, e547=coords sprite, e548=table ptrs — tous MWo3.)
2. **Tilemap** (table BG 4ptr/stage) : zero9 = **prog 0x470240** (runtime 0x660240) ; zero3 = **prog 0x393ea0**
   (cluster `2000 2000`, plus d'entrées car plus de stages).
3. **Palette** : région candidate **runtime 0x952800** (RGB555, prog ~0x762800) — à confirmer au build
   (vérifier quelle palette les tuiles du stage 0x18 utilisent, indices attr 0x20-0x37).
⇒ **MAPPING TERMINÉ. Tout est localisé.** Reste = LE BUILD : extraire 1 stage zero3 (tilemap 0x393ea0 +
sous-ensemble tuiles e256 + palette) → injecter dans zero9 (tilemap 0x470240 + GFX e546 + palette) →
recompresser (prog MWo3 + GFX MWo3) → AFS (rebuild si plus gros) → ISO. Outils prêts (mwo3_codec, patch_reemit).

### ⭐ DÉCRYPTAGE COMPLET 1/2/3 (autonome 2026-06-24) — via drawer 0x1d18a0
**1. GFX (format tuiles)** : bank `0xdb4000` = **tableau linéaire de tuiles 8×8 4bpp, 0x20 octets/tuile**.
   `adresse_pixel = 0xdb4000 + index_tuile × 0x20` (instr drawer `iVar2 + *puVar6 * 0x20`). e546 (MWo3) =
   décompresse exactement la bank. Les tuiles de DÉCOR sont OR'd 0xf000 → haut de la bank (~0x1e0000+).
**2. Table BG** (`prog 0x470240` / runtime 0x660240) : indexée par (stage + couche), **4 couches/stage**.
   Entrées = **offsets 16-bit AUTO-RELATIFS** → blocs tilemap (`offset + 0x660240`). zero9 : L0=L1=0x20,
   L2 varie +0x400/stage (0x420/820/c20/1020), L3=0x420.
**3. Tilemap** : chaque bloc = grille d'entrées **(tuile u16, attr u16)**. `0x2517e0` le copie vers le buffer
   tilemap (`0xbac400`) en OR 0xf000f000. Drawer : tuile = entrée|0xf000 ; **palette = (attr&0x1f)+0x20** ;
   flip = attr&0x60. Stage 0x18 L2 = 41 tuiles distinctes, région bank 0x1e0e80-0x200000 (~124 Ko), pal 0x34.
   Un stage = pour chaque couche (4) : 1 bloc tilemap + son sous-ensemble de tuiles.
**COMPLICATION cross-jeu** : la table BG de zero3 n'est PAS au même motif (HSFA a re-layouté son BG).
→ Il faut **localiser la table/blocs BG de zero3 via SON code** (décompiler zero3 dans pyghidra, trouver
son reader équivalent à 0x2511ac + sa constante de table). C'est le dernier maillon avant le build.

### RE BG zero3 (autonome 2026-06-24, projet pyghidra "dump3" = ee_std.bin) — système DIFFÉRENT de zero9
zero3 N'utilise PAS 0xb84178. Son BG (drawer partagé 0x1d18a0, mais compo propre) :
- **Fill** : `FUN_247bd4` (4 couches, source 0x93c400+ → dest 0x94c400+, OR 0xf000f000 = format tuile/attr
  IDENTIQUE). Autres fills : `0x21c410` (dest 0x944000), `0x21bf2c`/`0x21c04c`.
- **Sélecteur** = **struct-0x7f82 / -0x7f80** (par couche), PAS 0xb84178.
- **Table** = pointeur en scratchpad **[0x70001110]** (`pbRam70001110 += *(pbRam70001110 + sel*2)` =
  offsets auto-relatifs, même principe que zero9 mais base dynamique + sélecteur différent).
- **Tilemap BYTE-encodée** : `FUN_21bf2c` lit des OCTETS et appelle `0x2fd0f0` par octet (décodeur) →
  ≠ blocs (tuile,attr) directs de zero9. Donc le FORMAT de tilemap diffère (encodé vs direct).
- ee_std.bin = écran MENU (0x93c400 = zéros) → pas de stage chargé, pas de capture runtime possible ici.
- [0x70001110]/[0x70001114] en scratchpad (0x70000000) → pas lisibles dans le dump eeMemory.
**CONCLUSION** : zero9 et zero3 ont des systèmes BG SUBSTANTIELLEMENT différents (sélecteur, table dynamique,
tilemap encodée vs directe). GFX tuiles compatibles (e546/e256), mais cross-jeu = **TRADUCTION** (décoder
tilemap zero3 → ré-encoder format zero9 + tuiles + palette), pas un calque. Voie pratique = **savestate
zero3 EN COMBAT** : capture la forme runtime DÉCODÉE (work tilemap + bank) = bien plus simple à traduire
que décoder la source byte-encodée. (Décodeur zero3 = 0x2fd0f0 si on veut la voie source pure.)

### ⭐ DÉVERROUILLAGE Upper + Hyper (Select+bouton) — autonome 2026-06-24
Diff base ISO vs ISO Hyper (xdelta) = **1 SEUL octet** : ISO 0xa00771c4 (X_DATA e203=zb, MWo3, décompressé
offset 0xc900 = runtime **0x1d4900**), `0x00→0x08`. C'est un **bitfield** lu par **`FUN_1c8e10`** (gating
Select+bouton de l'écran de sélection) :
```
if (pad & 0x100 SELECT) {
  if (jeu==3 && unlock&0x02) version=5;  // 0x02 = SFA3 UPPER (zero5)
  if (jeu==0 && unlock&0x08) version=8;  // 0x08 = HYPER (zero9) -- ce que fait le xdelta
  if (jeu==1 && unlock&0x01) version=7;  // jeu1 alt
  if (jeu==2 && unlock&0x04) version=4;  // jeu2 alt
}
```
Octet à 0x1d4900 (= [0x19e438]+0xdc). **Upper+Hyper = 0x0a ; TOUT = 0x0f.** L'octet est un LITTÉRAL du flux
MWo3 → patch direct de l'octet compressé (e203 file offset 0x79c4, = ISO 0xa00771c4), même taille, pas de
recompression. ISO livrée : `SFA Anthology - All Unlocked (USA).iso` (base + octet 0xa00771c4 = 0x0f).

### CORRECTION déverrouillage (autonome 2026-06-24) — le bon mécanisme
Mes 2 1ers essais faux : (1) 0xc900=0x0f = la TABLE de select (valeur invalide → crash), (2) zb 0x90dc ≠
le bitfield (0x19d1000 est AVANT zb). **Savestate écran-select débloqué = vérité** : bitfield runtime
**`0x19d10dc` = 0x04** (bit 0x04 = Upper débloqué), table[0]=0. Donc l'unlock EST le bitfield de
`FUN_1c8e10` (mis depuis la SAVE de complétion). Mapping confirmé par titres dans zb (0x13580+) :
**v4="Zero 3 Upper", v8="Hyper Street Fighter Zero"**. Gating : SFA3(a0==2)+Select+bit0x04→v4 Upper ;
SFA1(a0==0)+Select+bit0x08→v8 Hyper. **FIX = patcher `FUN_1c8e10` (zb runtime 0x1c8e58/74/90/ac) : les 4
`lbu v0,0xdc(v0)` (0x904200dc) → `ori v0,zero,0xff` (0x340200ff)** = unlock toujours actif, sans save.
zb recompressé (patch_reemit, +12 o, rentre slot e203). ISO : `SFA Anthology - All Unlocked (USA).iso`
(base + zb patché, table 0xc900 intacte). Savestate Upper combat = `E:\tmp\ee_upper_combat.bin` (zero5,
pour cross-stage).

### SÉPARABILITÉ décor/persos CONFIRMÉE (2026-06-27) — feu vert cross-stage
Diff bank 0xdb4000 sur 3 combats zero9 differents : VARIABLE (persos charges/match) = 2 fenetres
**tuiles 0x16c00-0x19200 + 0x1bbc0-0x1e300** ; INVARIANT (decor resident 3 stages + systeme) = 3478 Ko,
tuiles **0x0-0x16c00**. Stage zero9 0x18 (0xf074-0xffff) = dans l'invariant = decor. **Stage Upper utilise
tuiles 0x1-0xffff, TOUTES < 0x16c00 => zero chevauchement avec les persos.** => Remplacer le decor resident
par les tuiles Upper ne touche jamais les combattants, ET pas de remap d'indices (indices Upper tombent
dans la zone decor de zero9). BUILD = (1) overlay tuiles Upper (zero5 bank 0xd35800) sur e546, recompress
MWo3 ; (2) tilemap 4 couches Upper (0xa20000/24/28/2c) -> blocs prog zero9 (table 0x660240) ; (3) palette.
