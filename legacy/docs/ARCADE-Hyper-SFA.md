# Mode ARCADE pour Hyper Street Fighter Alpha (PS2)

**Jeu** : Street Fighter Alpha Anthology (USA) — SLUS-21317, CRC `72CE7A78`
**Cible** : Hyper Street Fighter Alpha (zero9), qui ne propose nativement que Versus / Training / Option
**Méthode** : reverse engineering (moteur CPS2 68K recompilé en MIPS R5900) + injection runtime via pnach PCSX2
**État** : ✅ **v30 — FONCTIONNEL** (v28 livrée 2026-06-24 ; v29 2026-07-05 : VS MODE sauvé/restauré ; v30 2026-07-18 : **label « ARCADE » au menu**, validé in-game. Deux pnach : `_72CE7A78` = ISO vanilla, `_72CE7A38` = ISO widescreen.)
**BAKE ISO** : ✅ **LIVRÉ ET VALIDÉ IN-GAME (2026-07-19)** — `SFA Anthology [Widescreen] (USA) [Arcade].iso` (widescreen + arcade v30 **sans cheats**, seuls les octets de zero9/e544 modifiés → autres jeux et shell garantis intacts par construction ; re-générable via `hyper_arcade_iso_patcher.py SRC.iso`). Détails complets : §8. ⚠️ Même CRC que l'ISO widescreen : **décocher le cheat `[Hyper Arcade]`** pour jouer l'ISO bakée (sinon le pnach reprend le dessus — fonctionnel mais il ré-écrit les adresses zero9 dans TOUS les jeux, cf. §4.1bis).

---

## 1. Ce que fait le mode

- Entrée **ARCADE** dans le menu de Hyper (curseur 7, **label « ARCADE » affiché** — entrée d'origine Capcom jamais exposée, réactivée en v30 : table des labels `0x69cf54` [0]=ARCADE, copiée en cave `0x1c0360` + `table[7]`=`0x69cf70` pointée dessus par caves ; cf. `ANALYSE-Menu-Groove-Visuels.md` §1).
- Char-select 1 joueur → enchaînement de combats **KO** (pas infinis).
- **P1 fixe** (perso + groove conservés de combat en combat).
- **P2 en ladder** : adversaire différent à chaque victoire (cycle d'index).
- **P2 contrôlé par le CPU**.
- **Skip de l'écran handicap** entre les combats.
- **Défaite** → rematch contre le **même adversaire** (« continue » d'arcade) ; le retour menu reste un choix joueur.
- Le mode **VERSUS reste 100 % intact** (tout est gaté sur un flag arcade). ⚠️ En v28 une ligne de diag résiduelle (`019d2fa5,byte,1`) forçait VS MODE=COM en permanence, versus compris — corrigé en v29 (save/restore).

Seul accroc résiduel : la validation de P2 demande **1 appui sur le pad 2** au char-select (l'auto-P2 complet s'est révélé être un mur, cf. §5).

---

## 2. Architecture (comment ça marche)

### Principe général
Aucune instruction du code HSFA n'est patchée (contrainte critique, cf. §4). Tout passe par :
- une **code-cave** en `0x1C0000` (zone libre, jamais exécutée par le shell Anthology) ;
- des **redirections de pointeurs de DONNÉES** (tables de handlers en `0x5Bxxxx`).

### Chaîne d'exécution
1. **Menu** : navigation étendue au curseur 7 (tables nav `0x5B41F0/F4`, `0x5B4204`), lanceur du slot 7 (`0x5B422C`) → `arcade_launch` (cave `0x1C0200`) : pose le flag arcade (`0x1C0100=1`), reset latch groove (`0x1C0104`) + index ladder (`0x1C0118`), **sauve VS MODE** (`0x19D2FA5` → `0x1C010C`) puis le force à COM (P2 CPU), force `0xB84200=1` (route char-select), et saute au lanceur VERSUS (`0x252FF0`).
2. **Char-select** (mode versus, 1 joueur) : à la **sortie** du char-select (pointeur `0x5C55DC` → cave `0x1C0140` → `0x508B80`) : latch du **groove P1** (1× par run, dans `0x1C010A` ; restauré aux sorties suivantes) + écriture du **P2 ladder** : perso `0xB88916` = index et curseur `0xB88902` = index+0x30. P1 n'a pas besoin d'épinglage : son curseur n'est jamais réinitialisé entre les matchs.
3. **Init combat** : **aucun hook nécessaire** — le moteur ré-dérive les persos depuis les **curseurs** (`0x2905C0`), et comme on écrit curseur **et** perso à la sortie char-select, l'épinglage survit tout seul. (`0x5B5E88` reste un point de hook DATA disponible, utilisé par d'anciennes versions.)
4. **Fin de combat** : hook RESULT via le pointeur `0x5B5E9C` (subphase `0x0E`), cave `0x1C0000` (discriminant calculé **avant** l'appel au handler original `0x2865F0`) :
   - **Victoire** → index ladder +1 (modulo 13), re-route char-select (`0xB84200=1`, subphase `0xB88004=2`).
   - **Défaite** → même re-route **sans** incrémenter → rematch contre le **même adversaire** (« continue »).
   - Le retour menu (choix joueur) passe par la phase-2 menu (`0x5B4238` → cave `0x1C0240`) qui **restaure VS MODE** et efface le flag arcade.
5. **Skip handicap** : redirection `0x5C55E4` (sous-flux 5 → `0x5105D0`) → cave `0x1C0300` : reset handicaps (`0xB88404/804=0`) + avance le sous-flux `0xB88008` à `0xC`.

### Discriminant victoire/défaite
**Compteurs de rounds** : `0xB88526` (P1) vs `0xB88926` (P2) — celui qui a 2 a gagné.
⚠️ Ne PAS utiliser les flags `0xB88530/930` : ils ne reflètent que le **dernier** round (faux sur un 2-1) et sont collants.

---

## 3. Référence des adresses

| Adresse | Rôle |
|---|---|
| `0xB880A8` | Variable de MODE : 1=Training, 3=Versus (2 = vestige 1P non exposé) |
| `0xB88004` | Subphase (A5+4) — `2` = char-select (utilisée par la re-route du hook RESULT) |
| `0xB88008` | Sous-flux du char-select (sortie = 6) |
| `0xB88516` / `0xB88916` | Perso P1 / P2 (**dérivé** du curseur, recalculé par `0x511BA0`) |
| `0xB88502` / `0xB88902` | **Curseur** P1 / P2 (la vraie source ; perso = grille`0x5C5300`[curseur]) |
| `0xB8851A` / `0xB8891A` | Confirmation perso (bit 15) |
| `0xB88413` / `0xB88813` | Groove P1 / P2 |
| `0xB88526` / `0xB88926` | Compteurs de rounds P1 / P2 (discriminant V/D) |
| `0xB84200` | Dual : `1` = route char-select + COM, `7` = skip char-select (fragile, abandonné) |
| `0x19D2FA5` | **Option persistante VS MODE : 0=MAN, 1=COM** (P2 CPU propre ; sauvée/restaurée par v29) |
| `0x5B5E88` / `0x5B5E9C` | Pointeurs handler combat / RESULT (seul `0x5B5E9C` est redirigé en v29 ; `0x5B5E88` = point de hook dispo) |
| `0x5C55D0` / `0x5C55DC` / `0x5C55E4` | Table sous-flux char-select : init / sortie / handicap |
| `0x5B4210` / `0x5B422C` / `0x5B4238` | Table lanceurs menu / slot 7 / phase-2 menu |
| `0x5B4240` | Table de POLICE du renderer texte (caractère → tuile ; PAS des labels par curseur) |
| `0x69CF54` | Table des labels mode-select (7 ptrs par curseur ; [0]=`0x69CF70`=entrée ARCADE d'origine) |
| `0x69CF70` | = `table[7]` lu pour le curseur 7 → pointé sur la copie cave `0x1C0360` (v30) |
| Caves `0x1C0000` / `0x1C0140` / `0x1C0200` / `0x1C0240` / `0x1C0300` / `0x1C0360` / `0x1C0380` | hook RESULT / hook sortie char-select / arcade_launch / modesel_clear (+write label) / skip handicap / entrée ARCADE copiée / cave init-menu (write label, redir `0x5B4230`) |
| Vars `0x1C0100` / `0x1C0104` / `0x1C010A` / `0x1C010C` / `0x1C0118` | flag arcade / latch-groove-fait / groove sauvé / VS MODE sauvé / index ladder |
| Grille curseur→perso | `0x5C5300` (rangée `0x30` = identité : curseur `0x30+N` → char N) |

---

## 4. Contraintes critiques (à ne jamais oublier)

1. **Le pnach s'applique à tout le disque** : le shell Anthology et HSFA partagent le même CRC. **Patcher une instruction de code HSFA corrompt le shell** (écran noir vécu avec un patch à `0x286560`). → Uniquement : redirections de pointeurs DATA (`0x5Bxxxx`, `0x5Cxxxx`) + code-cave `0x1C0000`.
1bis. **⚠️ Le pnach corrompt aussi les AUTRES JEUX (vérifié 2026-07-18)** : les adresses des
   pointeurs zero9 (`0x5B5E9C`, `0x5C55DC`…) contiennent du **CODE MIPS dans Upper/SFA3**
   (vérifié dans les dumps z5) — les écritures per-vsync du pnach écrasent des instructions
   de ces jeux quand ils tournent. **Ne cocher `[Hyper Arcade]` que pour jouer à Hyper**, ou
   utiliser l'**ISO bakée** (`hyper_arcade_iso_patcher.py`) qui ne modifie que le fichier
   zero9 (e544) → zéro risque pour les autres jeux, zéro cheat.
2. **Ne jamais écrire perso/curseur chaque frame** — ça fige/décale les persos (bug v17). En v29 l'écriture se fait 1× à la sortie char-select et suffit (le moteur re-dérive le perso du curseur à l'init combat).
3. `0xB84200=7` (skip char-select) **casse le P2 CPU** et fait re-tirer les persos au spawn → la route char-select (`=1`) est la bonne.
4. Écrire le perso (`0xB88916`) seul est **ignoré** (recalculé depuis le curseur) → toujours écrire curseur **et** perso (+ confirm).

---

## 5. Le mur « auto-P2 » (7 approches tentées)

Objectif abandonné : valider P2 automatiquement sans toucher au pad 2.
Essais : forçage curseur (erratique), mode training (encodage perso incompatible — Ryu→Gen), flags CPU `0xB880A5`/`0xB88063` (transitoires), forçage `a8=3` (dérivé, casse le menu), skip `0xB84200=7` (voir §4)…
Conclusion : le coût dépasse le gain — 1 appui pad 2 est acceptable.

---

## 6. Fichiers

| Fichier | Contenu |
|---|---|
| `E:\CLAUDE CODE\hyper_re\PROJET-Hyper-Arcade.md` | Doc de travail détaillée (state-machine, historique tests A→v28) |
| `E:\CLAUDE CODE\hyper_re\ARCHIVE-pnach-tests.txt` | Sections pnach de test retirées du fichier live (2026-07-05) |
| `E:\CLAUDE CODE\hyper_re\hyper_arcade_iso_patcher.py` | **Bake ISO** : arcade v30 dans e544/zero9 (mapping fichier = EE−0x1F0000, caves relogées `0x5CEF00`, label = pur data) |
| `E:\CLAUDE CODE\anthology_extract\mwo3_splice.py` | Recompression MWo3 **chirurgicale par splice** (fenêtre LZSS 0x7FF mots → seules les zones modifiées ré-encodées ; compress_opt full-file = heures sur 9,9 Mo) |
| `E:\ROMS\PS2\…\SFA Anthology [Widescreen] (USA) [Arcade].iso` | ISO widescreen + arcade bakée (2026-07-19) |
| `E:\CLAUDE CODE\hyper_re\ANALYSE-Scene-Result-Boot.md` | Analyse scène/result/boot |
| `E:\CLAUDE CODE\hyper_re\ANALYSE-Menu-Groove-Visuels.md` | Label menu, groove, visuels |
| `E:\EMU\Emulateurs\pcsx2-…\cheats\SLUS-21317_72CE7A78.pnach` | Section **`[Hyper Arcade]`** (le mode complet) |
| `E:\CLAUDE CODE\hyper_re\eeMemory_versus.bin` | Dump RAM de référence (combat versus) |
| `E:\tmp\asm_testL.py`, `disf.py`, `p2s_ee.py`, `decode_log.py` | Outillage (assembleur MIPS à labels, désasm, extraction savestates, logs) |

---

## 7. Pistes futures

- **Auto-P2** : reprendre si un nouveau savestate char-select révèle le mode 1P vestige (`mode=2`) — désormais aussi envisageable en patch de CODE zero9 direct dans l'ISO (plus de contrainte shell/pnach avec le bake).
- **Skip logos / boot direct HSFA** : code boot = overlay absent des dumps combat ; besoin d'un savestate boot/titre. L'entrée directe depuis le shell = binaire distinct.
- ~~Baker le mode dans l'ISO~~ → ✅ FAIT, cf. §8.

---

## 8. BAKE ISO (✅ livré + validé in-game 2026-07-19)

### Livrable
- **`E:\ROMS\PS2\Street Fighter Alpha Anthology\SFA Anthology [Widescreen] (USA) [Arcade].iso`**
  = widescreen v10 + arcade v30, **zéro cheat**. Seul le fichier AFS **e544** (prog zero9) est
  modifié (+604 octets compressés) → tous les autres jeux, le shell et le SLUS sont
  bit-identiques. Le CRC (SLUS) reste `72CE7A38`.
- Patcher rejouable : `hyper_re\hyper_arcade_iso_patcher.py SRC.iso [DST.iso]`
  (localise l'AFS par magic `AFS\0`+553, vérifs vanilla, patch, splice, réécriture TOC,
  relecture byte-exacte). Sur l'ISO widescreen : AFS @`0x9F738000`, e544 off_rel
  `0xB749000`, slot 3 504 128 (marge d'origine 1484 → reste **880 octets** pour de futurs
  patches zero9).

### Mapping fichier ↔ RAM (la clé du bake)
- **offset fichier e544 (décompressé, 0x977200 o) = adresse EE − `0x1F0000`** (données déjà
  little-endian ; validé par échantillonnage 3000/3000 contre dump RAM). Le prog couvre
  EE `0x1F0000`–`0xB67200`.
- ⚠️ La zone pnach `0x1C0000` n'est **PAS file-backed** (< base du prog) → les caves du bake
  sont relogées dans une **zone de zéros file-backed** : base **`0x5CEF00`** (zone
  `0x5CEEF0`–`0x5CF300`, vierge dans tous les dumps runtime). 2ᵉ zone libre connue (encore
  disponible, ex. pour le cross-stage) : **`0x5D16F0`–`0x5D1B00`** (0x410 o).
- Layout caves bakées : result `+0x000`, sortie-char-select `+0x0A0`, arcade_launch
  `+0x120`, modesel_clear (forme v29) `+0x160`, skip-handicap `+0x190`, entrée ARCADE
  (data) `+0x1F0` — fin `+0x208`. Le code est **position-indépendant** (variables runtime
  inchangées en RAM `0x1C01xx`, branches relatives, `j/jal` absolus) → mots identiques au
  pnach, seuls les 9 pointeurs changent. Le label ARCADE = **pur data** (word `0x69CF70`
  baké → `0x5CF0E0`) : plus besoin des caves label du pnach v30 (phase-0 `0x5B4230` reste
  natif, modesel_clear = forme v29).

### Compression MWo3 — le savoir complet (⚠️ leçons de sang)
- **Format** (cf. `mwo3_codec.py`) : LZSS 16-bit à mot, fenêtre **0x7FF mots** ; ctrl 16-bit
  MSB→LSB ; token : `len5=token>>11` ; len5≠0 → L=len5, off=token&0x7ff ; len5=0 → off=token,
  L=mot suivant ; off=0 : L=0=**FIN**, sinon zero-run ; off>0 : backref. Le magic « MWo3 »
  en tête de e544 = littéraux du flux lui-même (aucun header à gérer).
- **⚠️ LE VRAI DÉCODEUR (`FUN_148698` @`0x148698`) COPIE EN DO/WHILE** (désassemblé) : un
  token à longueur étendue **0** copie 65536+ mots = runaway = crash `FQC=0 VIF FIFO` au
  chargement (vécu : splice v1 avec tokens « no-op » L=0). **Ne jamais émettre L=0** ; ne
  jamais valider un flux avec son propre codec : utiliser `decompress_strict`
  (émulation fidèle do/while) de `mwo3_splice.py`.
- **Encodeurs disponibles** : `compress_opt` (DP optimal — OK ≤ ~100 Ko ; **>20 min sur
  3 Mo = inutilisable sur e544** ; émet un token FIN en queue) ; `mwo3_codec.compress`
  (greedy, trop gros) ; `patch_reemit` (casse sur caves en zero-runs) ; `comp_test` (buggé).
- **`anthology_extract\mwo3_splice.py`** = LA solution gros fichiers (0,7 s sur e544) :
  recompression **chirurgicale** — la fenêtre 0x7FF mots rend la compression locale ;
  on parse les frontières de mots de contrôle du flux original (`parse_boundaries`),
  on ré-encode uniquement les clusters modifiés (+0x800 mots de marge AVAL pour les
  backrefs du flux conservé), et la tranche est re-sérialisée maison en **scindant des
  matchs/zero-runs** (L→L1+L2, même offset = sémantique identique) jusqu'à un multiple de
  16 entrées **pile** (frontière de contrôle exacte, sans FIN ni rembourrage). Couture avec
  l'original ; 99,6 % du flux reste bit-identique.

### Vérifications faites
- Relecture ISO → décompression `decompress_strict` → comparaison byte-exacte au prog
  patché + présence de chaque patch. Boot shell OK, boot zero3 OK, **Hyper + mode ARCADE
  validés in-game par Rickow** (label, run arcade). Jeux cachés du shell (Upper/Hyper) =
  débloqués par la SAVE memory card (un boot sans save ne montre que 5 jeux).
