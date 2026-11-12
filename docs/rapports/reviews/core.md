# Critical review of the FBNeo HSFA core patches (2026-11-11 / 12)

**Summary (English).** Static review of the FBNeo HSFA core patches, workshop `<workspace>/work/revue_coeur/`. A first
review (11/11) was stopped at line 1860 of `cps_hsfa.cpp`; a targeted review of the new patches of v0.1.9 (0029, 0030,
0031, standalone W01-W05) followed on 12/11. No trial was run by the reviews.
- **D1 (first review, medium, upstream FBNeo)**: D0-D7 / A0-A6 / USP of the 68000 survive an unload and reload of the
  game (`SekInitCPUM68K` copies the live `m68ki_cpu` into the new context): a relaunch differs from the first launch
  (the `$FF3A44` divergence), which matters for determinism, netplay and input replay. Fix of principle: zero these
  registers at `SekInit` / `HsfaInit`. **Open** (no patch yet; trial `essais_demain/01_relance_registres.sh` not
  written).
- **v0.1.9 review: nothing blocking.** R1 (HSF9 zone applied before the header check, no bound on values) → **fixed by
  patch `0032`** (v0.1.9: a damaged or padded state is no longer applied blindly). R3 (standalone FBNeo: rewind and
  run-ahead without the HSFA zones) → **fixed by `W06`**. R6 (saved option) already in the notes.
- **Still open**: R2 (a 4:3 state loaded in the 16:9 core: zone ignored; one sentence in the notes), R4
  (`bCpsPalCharge` set by the counting pass), R5 (`WsS1Copie` not cleared by `WsS1Suivi`), R7
  (`%ls` conversion of the archive path follows the C locale, patch 0030), R9 (shearing reported,
  not reproduced: cause not established); files not read yet: `hsfa_flux.h`, `hsfa_rejeu.h`, `hsfa_qsound.h`,
  `hsfa_musique.h` and the diffs of `cps_obj`, `cps_pal`, `cps_draw`, `cps_scr`, `cpsrd`, `ctv`, `z80` outside 0029.
- The trial `essais_release/01_etat_ancien_complete_zeros.sh` (old state padded with zeros) was written, not run, by
  the review. The upstream triage of the patches (`RAPPORT_triage.md`) is a separate study and stays in the workshop.
- No tool kept (the review only read the sources).

---

## Original text (French, kept as is)

> Kept as written in the workshop. Only changes: personal paths written `<workspace>/...`, workshop folders written `<workspace>/work/...`. Paths such as `outils/…`, `sorties/…`, `essais_demain/…`, `constr/…` are relative to the review's workshop folder (above); the tools kept are in `tools/reviews/` (see the summary).

# Revue critique des patchs du cœur FBNeo HSFA

Arbre lu : `<workspace>/work/coeur_0031/fbneo` (HEAD 040851b, base af5d3f3 + chaîne jusqu’à 0031). Analyse statique, aucun essai lancé.
Références `fichier:ligne` relatives à `src/burn/drv/capcom/` sauf mention.

## 1. Défauts réels

### D1 — Relance ≠ 1er lancement : les registres du 68000 survivent au déchargement (cause de la piste $FF3A44) — gravité MOYENNE (déterminisme, netplay, rejeu d'entrées), FBNeo d'origine
- **Preuve** : `src/cpu/m68000_intf.cpp:1026-1027` (`SekInitCPUM68K`) : `memset(SekM68KContext, 0, ...)` puis aussitôt
  `m68k_get_context(SekM68KContext[nCount])`, qui recopie la structure globale vivante `m68ki_cpu` DANS le contexte neuf.
  `src/cpu/m68k/m68kcpu.c:1034-1040` (`m68k_init`) ne met `m68ki_cpu` à zéro qu'au 1er appel du processus
  (`emulation_initialized`). `m68k_pulse_reset` (`m68kcpu.c:1058-1091`) ne pose que SR, VBR, SP et PC.
- **Mécanisme** : D0-D7, A0-A6, USP gardent, au 2e chargement, les valeurs de la dernière instruction de la session
  précédente (la boucle d'attente d'image : registres de fin d'image, dont les mots de manette → dépendance « Pièce
  tenue ou non » relevée dans `<workspace>/work/etats_coeur/RAPPORT.md` §6). Toute la RAM (`cps_mem.cpp:79`, memset), l'EEPROM
  (`eeprom.cpp:88`, memset 0xFF), le Z80 et les tableaux HSFA sont, eux, bien remis à neuf : c'est la seule mémoire lue
  par le jeu qui survit. Le programme d'arcade initialise ses registres avant de les ranger ; le programme retraduit
  range un registre non initialisé (8 octets = 2 longs en $FF3A44-$FF3A4B à l'image 15, puis la valeur se propage à
  $FF80B4…). D'où « pas sur l'arcade d'origine ».
- **Essai** : `essais_demain/01_relance_registres.sh` (cœur avec D0-A6 remis à zéro, rejouer `zt_av2490` → doit
  devenir identique au 1er lancement). Vérification sans compilation : chercher dans la ROM l'instruction qui écrit
  $FF3A44 avant l'image 15 et son registre source (voir D1bis si fait).
- **Correctif de principe** : dans `HsfaInit` (aucune instruction n'a encore tourné) ou mieux dans `SekInitCPUM68K` :
  mettre D0-D7/A0-A6/USP à zéro (`m68k_set_reg`), ou `memset(&m68ki_cpu, 0, ...)` avant `m68k_init` à chaque
  `SekInit` du CPU 0. Correctif d'amont valable pour tout FBNeo (à proposer tel quel).
- **Aussi** : avec Cyclone (ARM, `USE_CYCLONE=1`) le contexte `PicoCpu`/`c68k` est à vérifier de la même façon.

- **D1bis (indice fort, déjà dans les essais)** : `<workspace>/work/etats_coeur/essais/zt_ram6/ref_ram_002490.bin`, octets $3A44-$3A4B
  = mots `F002 00FF 8400 FFFF` : le long en $FF3A46 vaut `$00FF8400` = adresse de la structure du joueur 1, valeur
  typique d'un registre d'adresse (A6) en combat. Une telle valeur à l'image 15 d'un démarrage à froid ne peut venir
  que du contexte du processeur, pas de la RAM (remise à zéro) ni de l'EEPROM.


---

# Revue ciblée v0.1.9 (12/11) — patchs NOUVEAUX : 0029, 0030, 0031, W01-W05

Lecture seule, aucun essai lancé. Arbres : libretro `<workspace>/work/coeur_0031/fbneo` (040851b) ; autonome
`<workspace>/work/coeur_0031/autonome/FBNeo` (patchs W appliqués). `capcom/` = `src/burn/drv/capcom/`.
**Verdict d'ensemble : RIEN DE BLOQUANT.** 3 points à mentionner (R3, R6, R9 ; R6 et R9 sont déjà dans les textes
livrés), le reste pour plus tard. Classement : BLOQUANT / NOTES / PLUS TARD.

## 0029 — états complets (zone « HSF9 »)

Vérifié sans défaut : tailles fixes et identiques en 32 et 64 bits (que des `INT32` / `UINT8` / `UINT16`, `INT16[2][4]`,
aucun pointeur ni `long` ni `size_t` sauvé ; `ObjFrame.Obj` n'est PAS sauvé et est posé par `CpsObjInit`,
`cps_obj.cpp:126-127`, donc valide dans une 2e instance) ; `ObjMem` alloué `(nMax<<3)*nFrameCount` = taille sauvée
(`cps_obj.cpp:120,173`, CPS2 : 2) ; taille de l'état constante (`WsS1Copie` alloué par le scan lui-même,
`cps_hsfa.cpp:2163`) ; état d'avant 0029 ou tronqué : la passe de comptage (`HsfaFinCompte`) compare `nRestant` à la
taille de la zone AVANT toute lecture (`cps_hsfa.cpp:2181-2190`), donc jamais de lecture au-delà du tampon ni de
`bScanOk = false` ; run-ahead 1 instance (drapeau palette `bCpsPalCharge` consommé au 1er dessin, palette et
`CpsPalBrut` écrits ensemble par `CpsPalUpdate`, `cps_pal.cpp:82`) ; 2e instance (tout ce qui est lu est soit dans
l'état, soit refait à l'init) ; rembobinage (même chemin que le chargement) ; Windows libretro (rien de propre).
En Raw (défaut 0031) `nWsBande = 0` : tout le suivi 16:9 sauvé est dormant (`cps_hsfa.cpp:1960-1967`), ce qui réduit
encore le risque du lot.

### R1 — la zone est appliquée AVANT la vérification de l'en-tête, sans borne sur les valeurs — PLUS TARD (durcissement ; 5 lignes)
- **Preuve** : `capcom/cps_hsfa.cpp:2201` (`HsfaFinZones` lit tout), puis seulement `:2208` compare `nEntete` et ne
  fait qu'un `bprintf`. Valeurs lues sans contrôle : `nGetNext` (`cps_obj.cpp:174`, indice de `of[3]`, `:190`),
  `of[i].nCount` (borne des boucles de dessin), `Cps2Volume` (indice de `Cps2VolumeStates[]`, `cps_rw.cpp:227,233`,
  borné seulement toutes les 5 images, `cps_run.cpp:457-462`).
- **Scénario** : état plus long que l'état « ancien » mais sans zone HSF9 valide : frontal qui complète le tampon
  jusqu'à `retro_serialize_size`, fichier abîmé, future version 2 de la zone chargée dans ce cœur.
- **Effet joueur** : avec un complément de zéros : `Cps2Volume = 0` → `QscSetRoute(…, 0)` (`:2204-2207`) : jeu MUET
  jusqu'à une touche de volume (et le 0 est repris dans les états suivants) ; palette noire jusqu'à la copie suivante
  du jeu ; objets absents une image. Avec des octets quelconques : écriture hors tableau possible (`nGetNext`).
- **Pourquoi non bloquant** : RetroArch passe à `retro_unserialize` la taille exacte du fichier (rien dans le code lu ne
  dit le contraire ; l'essai « états étrangers » du harnais passe la taille du fichier) ; run-ahead / rembobinage /
  netplay : tailles égales et en-tête bon. Aucun état v2 n'existe.
- **Correctif de principe** : lire l'en-tête d'abord et sortir (comme « zone absente ») s'il n'est pas `HSF9` ;
  après lecture : `nGetNext &= 1`, `nCount` borné à `nMax`, `Cps2Volume` borné à 0-39.
- **Essai prêt** : `essais_release/01_etat_ancien_complete_zeros.sh` (≈ 1 min, nice 19) : montre le mode de défaut
  (message « zone de fin d'état inconnue », son). Contrôle manuel utile avant publication (1 min, hors banc) : charger
  dans RetroArch un état fait avec un cœur v0.1.8.

### R2 — état du cœur 4:3 chargé dans le cœur 16:9 : zone ignorée en entier — PLUS TARD (une phrase dans les notes suffit)
- **Preuve** : la partie 16:9 est dans la même zone (`cps_hsfa.cpp:2162-2171`, `#ifdef HSFA_WS`) : 22 Ko en 4:3,
  39 Ko en 16:9 ; `nRestant < nFinTaille` → `return 0` (`:2185-2190`) : QSound, objets, palette, registres F non
  restaurés non plus. Sens inverse (16:9 → 4:3) : zone lue, surplus ignoré.
- **Effet** : chargement « approximatif comme avant 0029 », sans message. Le GUIDE de l'autonome dit déjà de ne pas
  mélanger ; le LISEZMOI des cœurs ne le dit pas. **Correctif** : sous-zone 16:9 à part (version 2).

### R3 — FBNeo autonome : rembobinage et run-ahead INTÉGRÉS sans les zones HSFA — NOTES (autonome en essai)
- **Preuve** : W03 n'ajoute `HsfaScanMelange` / `HsfaScanFin` qu'à `state.cpp` et `statec.cpp` (états en fichier).
  `src/burn/burn.cpp:1293,1311,1318` (`StateRunAhead*`) et `:1430,1579,1670` (`StateRewind*`) appellent
  `BurnAreaScan` seul ; les deux fonctions sont compilées (`burn.cpp:49,53`).
- **Effet joueur** (Game > rewind, Video > RunAhead de l'autonome) : comportement d'avant 0029 (son du QSound décalé,
  1re image) et, pour Upper / Hyper, registres de mélange des objets (patch 0010, `nHsfaObjMix`,
  `cps_hsfa.cpp:180-192`) NON rembobinés : transparence d'un objet possiblement fausse après un retour en arrière,
  jusqu'à ce que le jeu les réécrive.
- **Notes de version** : la phrase d'INSTALL-EN.md l. 46-49 (« after a load, picture and sound go on exactly… ») ne
  vaut que pour les états en fichier ; ajouter « rembobinage et run-ahead de l'autonome : non couverts (essai) ».
- **Correctif** (W06) : les deux appels après chaque `BurnAreaScan` de run-ahead / rembobinage.

### R4 — autonome : `bCpsPalCharge` posé par la passe de comptage et quand la zone manque — PLUS TARD
- **Preuve** : `nRestant = -1` partout dans l'autonome (W03) : pas de garde « zone absente » ; `CpsPalScanHsfa`
  (`cps_pal.cpp:46-50`) pose le drapeau dès que `ACB_WRITE`, y compris sous `LenAcb` (`statec.cpp:193`,
  `state.cpp:50` avec `bRead = 0`) et quand `LoadAcb` ne trouve pas le bloc (`statec.cpp:84-134`, bloc sauté).
- **Effet** : au dessin suivant, palette refaite depuis `CpsPalBrut` COURANT au lieu de la RAM de l'état : au pire
  couleurs fausses jusqu'à la copie de palette suivante du jeu, et seulement pour un état sans zone (aucun n'existe :
  l'autonome est publié pour la 1re fois avec W03). Format par blocs nommés + hachage : pas de débordement possible.
- **Correctif** : poser le drapeau seulement si le bloc a réellement été lu (comparer un témoin avant / après).

### R5 — `WsS1Copie` alloué sans remise à zéro par `WsS1Suivi` — PLUS TARD
- **Preuve** : `cps_hsfa.cpp:1873` (`BurnMalloc` sans `memset`, alors que `:2163` en fait un) ; `:1876` retour si
  `Base == NULL` → 16 Ko indéterminés sauvés dans l'état. Modes non bruts seulement (non par défaut).
- **Effet** : aucun en jeu (recopié avant usage) ; états non identiques à l'octet entre deux machines (somme de
  contrôle du netplay). **Correctif** : `memset` à l'allocation.

## 0030 — dossier système en chaîne large — rien de bloquant
- Cœurs libretro : identiques à l'octet (macro en fin de `cps.h`, `_UNICODE` absent). Autonome : `"%.*ls"` avec un
  `TCHAR*` large, correct ; précision = nombre maximal d'octets, tampon `MAX_PATH` : pas de débordement.
- **R7 — PLUS TARD** : la conversion de `%ls` suit la locale C (« C » par défaut) et le chemin de l'archive passe par
  `TCHARToANSI` (CP_ACP, W02 `bzip.cpp:615-617`) puis `fopen(char*)` (`cps_hsfa.cpp:1081,1275`). Un chemin de ROM ou de
  « hiscores » ABSOLU contenant des caractères hors de la page de codes de Windows → archive / dossier `hsfa/` non
  trouvés → musiques en flux et voix du rejeu absentes, sans message. Les chemins par défaut sont relatifs
  (`roms/`, `support/hiscores/`) : pas touché par défaut. Notes (facultatif) : « chemins sans caractères exotiques ».

## 0031 — 16:9 Raw par défaut — rien de bloquant
- Deux valeurs par défaut (`cps_hsfa.cpp:1834,1934`) + l'option (`retro_common.cpp:134`) ; aucune ligne déplacée ; le
  4:3 n'est pas touché. Effets de bord, TOUS déjà écrits dans `LISEZMOI.txt` de la livraison (l. 5-22) :
  **R6 — NOTES (déjà fait)** : RetroArch garde la valeur enregistrée (« Stage-locked view » reste chez qui a déjà
  lancé un cœur 16:9) ; hors combat les côtés ne sont plus noircis ; un `.ini` de l'autonome du 11/11 garde
  `nHsfaWsEdges 0`. La livraison ne contient pas de `.ini` (vérifié) : un nouvel utilisateur a bien Raw.
- Changer l'option en pleine partie : le suivi repart de zéro (`bWsS1Init = 0`, `cps_hsfa.cpp:1966`), sans risque.

## W01-W05 — FBNeo autonome Windows (essai)
- **W01** : objets et drapeaux seulement. **W05** : défauts et libellés ; valeur hors bornes du `.ini` → Raw.
- **W02** (`bzip.cpp:596-662`) : CRC ignoré pour tout pilote dont le NOM contient « hsfa », longueur toujours exigée ;
  les autres jeux gardent le contrôle. Archive = 1re archive trouvée de la liste (celle du jeu). Limite connue et
  voulue (comme libretro) : une archive d'une ancienne construction, de mêmes longueurs, est acceptée sans message.
  Tampon : `szHsfaZip[MAX_PATH*2]` + contrôle `strlen < MAX_PATH` avant `strcpy` : correct. → rien.
- **W03** : voir R3 et R4. **W04** : rognage du format fait en UN point (`vid_interface.cpp:451-467`,
  `VidFrameCallback`), avec le pas de ligne du blitter à la recopie (`:444`) et un tampon privé au pas plein
  (`:436`) : pas de débordement, pas de pas de ligne faux. Valeurs du `.ini` bornées (`hsfa_win32.cpp`). → rien.

### R9 — cisaillement signalé, non reproduit — NOTES (texte livré déjà honnête ; une précision à apporter)
Ce que le code permet de dire :
1. **Pas de ligne en 512 px : exclu à la lecture.** Le pilote dessine partout avec `nBurnPitch` (`cpst.cpp:51…`,
   `cps_hsfa.cpp:2015`) ; 512 × 4 = 2048 octets, multiple de tous les alignements usuels. Seule largeur « impaire »
   du menu : 16:10 = 460 px (1840 octets, non multiple de 32) ; elle passe par la recopie W04 qui prend le pas du
   blitter : correct aussi. Reste d'origine FBNeo : `CpsClearScreen` suppose des lignes contiguës
   (`cps_draw.cpp:450-497`), sans effet de cisaillement (simple effacement).
2. **Déchirure (VSync) : peu probable avec les réglages par défaut, contrairement à ce que laisse entendre le texte.**
   Blitter par défaut du x64 = 2, SoftFX (`vid_interface.cpp:64`). Plein écran : `Flip(NULL, DDFLIP_WAIT)` toujours
   (`vid_ddrawfx.cpp:500`), VSync cochée ou non. Fenêtre : synchronisation sur DWM active par défaut
   (`bVidDWMSync = true`, `d3dkmt_sync.cpp:40` ; `run.cpp:238`) et composition. Une vraie déchirure n'est écrite
   dans le code que pour les blitters DirectX 9 (3 et 4) en plein écran avec VSync coupée
   (`D3DPRESENT_INTERVAL_IMMEDIATE`, `vid_directx9.cpp:1178,2244`). Piège : cocher VSync décoche la synchro DWM
   (`scrn.cpp:2549-2551`).
3. **Saccade 59,6 Hz / 60 Hz** : en fenêtre synchronisée sur DWM, une image est doublée à intervalle régulier ; sur un
   défilement horizontal cela se lit comme un à-coup, pas comme une image penchée.
4. **Glissement des plans de la vue calée** (seul défaut visible dans les captures) : supprimé par Raw (W05).
5. **Jamais essayé** : un vrai Windows (DirectDraw y est émulé par-dessus DWM), le blitter 3 (DirectX 9
   Experimental, ne démarre pas sous Wine), un vrai pilote graphique, un écran à fréquence variable.
- **À dire dans les notes** (le texte `NOUVEAU-2026-11-12.txt` le dit déjà pour l'essentiel) : « signalé sur une
  machine avec la version du 11/11 en vue calée ; non reproduit (essais sous Wine seulement, pas sur un vrai
  Windows) ; cause non établie ; le défaut Raw supprime le seul effet de ce genre vu dans nos captures ; ce n'est PAS
  annoncé comme corrigé ». Demander : fenêtre ou plein écran, blitter, format choisi, fréquence de l'écran, photo.
  Précision à corriger : ne pas présenter « VSync coupée » comme la cause probable avec le blitter par défaut (point 2).
