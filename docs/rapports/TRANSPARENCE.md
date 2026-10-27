# Transparence des effets MAX : comportement PSP, registres HSFA, cœur FBNeo (0010) et fork MAME

Agent `agent_alpha`, 2026-10-18. Dossier : `work/agent_alpha/` (tout ce qui suit y est, sauf mention).

## Résumé

- **PSP** : les effets des persos MAX sont dessinés en **additif saturé** (`dst + src`, GE `BLENDMODE = ADD`,
  `FIXA = FIXB = 0xFFFFFF`). Pas d'alpha par couleur : le bit 15 des palettes est le bit « opaque » du format 5551.
  Le mode suit l'**emplacement de palette** : Eagle 1 et 2, Ingrid 3 (dans chaque groupe). Maki, Yun et les persos
  natifs : rien d'additif observé.
- **Interface** : 32 registres d'un octet, **`$804220-$80423F`**, un par palette OBJ. 0 = opaque, 1 = additif.
- **Cœur FBNeo** : patch `0010-HSFA-melange-des-objets-par-palette-OBJ.patch`.
  - Non-régression IDENTIQUE sur SFA3, Upper et Hyper.
  - Le chemin 16 bits (RGB565 et 0RGB1555) est aussi identique au pixel.
  - Démonstration sur l'arc d'Eagle : aspect PSP retrouvé (`captures/demo/`).
- **Fork MAME** (copie) : même interface (`melange-sur-fork.patch`).
  - Effet seulement avec `HSFA_MELANGE=1`, qui passe l'écran en RGB.
  - Sans la variable, 201/201 captures et le journal sont identiques au binaire partagé.

## 1. Comportement PSP

### 1.1 Méthode

On ne lit pas le code PSP. On mesure l'**état du GE** image par image :

- PPSSPP headless lancé avec le fork local, sur une copie de la carte mémoire (`psp/memstick`), port 45691.
- Le débogueur WebSocket fournit le dump GE d'une image (`gpu.record.dump`, format `.ppdmp` v6 compressé en zstd).
- `outils/gedump.py` rejoue les registres GE et liste, pour chaque primitive : mélange (`0x21`, `0xDF`, `0xE0`,
  `0xE1`), fonction de texture (`0xC9`), CLUT chargée, sommets.
- `outils/bilan.py` croise chaque CLUT avec les palettes des `pac` (`outils/palidx.py`).
- `outils/planche_add.py` superpose les primitives sur la capture : rouge = additif, vert = alpha < FF.

Pilotage :

- `outils/pa.py` (temps émulé), `choix.sh` (sélection en entraînement), `seq.py` (manipulation image par image, puis
  un dump et une capture toutes les n images) ;
- `batterie.sh` : 11 manipulations (¼ cercle et DP poing / pied, supers ¼ cercle ×2, coups simples).

Dumps : `psp/dumps/{shot,sup1,eagle,maki,yun,ken}/` (`.ppdmp` + `.png`). Bilan : `psp/bilan_modes.txt`.

### 1.2 Résultats

| constat | détail |
|---|---|
| Bit 15 des palettes | posé sur **toutes** les couleurs non nulles, y compris les palettes de persos (pl00 [2] : 450/480 mots, les 30 autres = couleur 0). C'est le bit « opaque » de l'ABGR1555. Couleur 0 : bit 15 = 0, c'est la transparence (test alpha `> 0`) |
| Mélange par défaut | `SRC_ALPHA / 1−SRC_ALPHA`, texture CLUT4 en `MODULATE` avec l'alpha de la texture. Couleur de sommet `FFFFFFFF`, donc opaque en pratique |
| **Effets MAX** | `BLENDMODE ADD, FIXA, FIXB`, `FIXA = FIXB = FFFFFF`, soit **`dst + src` saturé**. Mêmes sommets `FFFFFFFF`, même test alpha |
| Eagle | palettes PSP 1 et 2 de chaque groupe de 5. Ce sont l'arc du bâton (DP + poing) et les traînées du super. Sur 120 primitives additives, aucune primitive normale n'utilise ces emplacements |
| Ingrid | palette PSP 3 de chaque groupe de 8 : lueurs solaires du Sun Upper et explosion du super. Sur 236 primitives additives, aucune exception. Le Sun Shot et les étincelles violettes restent **opaques** |
| Maki, Yun | rien d'additif sur 11 manipulations chacun. Les clones du Genei Jin de Yun sont opaques (palette bleue) |
| Natifs | Ken : 11 manipulations, dont Shoryureppa et Shinryuken. Deejay : passif. Étincelles d'impact communes : opaques. **Aucun additif** |
| Autres mélanges (tous persos, hors sujet) | ombres : noir, alpha de sommet `C0` (75 %). Jauges du HUD : alpha `80` (50 %) |

Captures annotées dans `captures/psp_mesures/` : `eagle_additif.png`, `ingrid_coups_additif.png`,
`ingrid_super_additif.png`.

Correspondance **emplacement → mode**, toujours 1:1 dans les mesures :

- CLUT VRAM `0x040CB000 + 32·n` ;
- J1 = 0-7, J2 = 8-15 ;
- additif : Ingrid n = 3, Eagle n = 1 et 2.

Le registre « par palette » est donc l'interface naturelle. Un drapeau par couleur ne servirait à rien : il n'y a
pas d'alpha par couleur.

Les mêmes palettes dans Upper (constructions MAX) :

- **Eagle** : `palettes_module.bin` = palettes PSP 1:1. Emplacements **+1, +2** des 5 palettes du joueur.
- **Ingrid** : `palettes_module_upper.bin` (6 × 5) range la palette PSP 3 dans l'emplacement **+3** de chaque
  groupe (vérifié sur les 30 palettes).
- La base est **0 pour J1 et 5 pour J2**, vérifiée dans le cœur : palette 05 = corps de Cammy en J2.

## 2. Interface jeu → cœur

| adresse | taille | contenu |
|---|---|---|
| `$804220 + p` (p = 0..31) | 1 octet par palette OBJ (attribut d'objet `& $1F`) | **0** opaque (valeur au reset) ; **1** additif saturé (PSP) ; **2** alpha 50 % ; **3** alpha 75 % ; **4** soustractif saturé ; 5-255 réservés (opaques) |

Accès :

- lecture et écriture par octet, ou par mot (octet fort = palette paire) ;
- un `MOVE.L` couvre 4 palettes.

Disponibilité :

- mode 2 du cœur seulement (Upper, Hyper) ;
- remis à 0 au reset ;
- sauvé dans les états (32 octets de plus dans les états d'Upper et d'Hyper : les anciens états ne se rechargent pas).

Place :

- hors de `$804200-$804205` (plans) et de `$804210` (banque commutée proposée par agent_coeur_banques) ;
- dans le cœur, `$800000-$807FFF` est un miroir des ports (`a & $1FF`) : `$804220` serait lu comme le port `$020`
  (EEPROM). Ces adresses sont donc prises par `HsfaPort*` avant le miroir, comme `$804200`.

Ligne à inscrire dans `re/allocations.tsv` (vérifiée sur une copie de `re/`) :

- `zones.py --verifie` : 23 conflits avant comme après (`re_ajouts/zones_{avant,apres}.txt`) ;
- `verifie.py` : 0 erreur avec les 4 lignes de `re_ajouts/`.

```
materiel_cps2	$804220	$80423F	transparence des objets par palette OBJ (agent_alpha)	utilisé	<workspace>/work/agent_alpha/ALPHA-PSP.md §2 ; patch FBNeo 0010	un octet par palette OBJ 0-31 (0 opaque, 1 additif, 2 alpha 50 %, 3 alpha 75 %, 4 soustractif) ; cœur FBNeo HSFA (mode 2) et copie du fork MAME ; hors $804200-$804205 (plans) et $804210 (banque commutée proposée)
```

Autres lignes pour l'index : `re_ajouts/sfa3_arcade.tsv` (registres) et `re_ajouts/max_psp.tsv` (CLUT VRAM PSP,
mélange des effets MAX).

## 3. Cœur FBNeo : patch 0010

`0010-HSFA-melange-des-objets-par-palette-OBJ.patch` (format `git format-patch`, `From: Rickow`, contre `rejeu`
5e0eda6 = 0008 + 0009 ; commit local `e6d3f4e` dans `fbneo/` ; vérifié par `git apply --check` sur un clone
neuf). 5 fichiers, +125 / −6.

Le rendu CPS de FBNeo n'utilise pas `pTransDraw` : `CpstOne` / `ctv_do.h` écrivent directement en RGB dans
`pBurnDraw`. Le peintre suit l'ordre des priorités : plans et niveaux d'objets entrelacés, plus le tampon Z du
masquage CPS2. Il existait déjà un mélange par tuile (`nCpsBlend` + `alpha_blend`, blendtable de quelques jeux, en
24/32 bits seulement). Le patch s'y greffe, sans passe à part.

- `cps_hsfa.cpp` :
  - `nHsfaObjMix[32]`, lecture et écriture `$804220-$80423F` (`HsfaPortReadByte` / `WriteByte` / `WriteWord`) ;
  - remise à 0 dans `HsfaReset`, `SCAN_VAR` en mode 2 ;
  - essais : `HSFA_OBJMIX=pp:m[,…]` impose des valeurs au reset, `HSFA_MIX_LOG=<fichier>` journalise
    « image : palette = mode ».
- `cps_obj.cpp` (`Cps2ObjDraw`) : `nCpsBlend = 0x100 | mode` pour les tuiles d'une palette OBJ non nulle.
- `ctv.cpp` / `ctv_do.h` : `cps_mix()` (24/32 bits) et `cps_mix16()` (16 bits).
  - `cps_mix()` : valeurs < `0x100` → `alpha_blend` d'origine ; ≥ `0x100` → `hsfa_mix` (additif saturé, alpha
    50/75 %, soustractif).
  - `cps_mix16()` : 565 ou 1555, détecté par `BurnHighCol(0, 255, 0)` dans `CtvReady`. Seulement pour les valeurs
    ≥ `0x100`, pour ne rien changer aux jeux CPS1 en 16 bits.
- Coût : le mélange par pixel ne s'exécute que pour les objets marqués. Ailleurs, un test entier de plus en 16 bits
  (`nCpsBlend & 0x100`) et rien de plus en 32 bits (le test `if (nCpsBlend)` existait déjà).

Compilation Linux : `cd fbneo/src/burner/libretro; nice -n 19 make -j6 SUBSET=hsfa` (`REGEN_HEADERS=1` pour la 1re
construction).

- Journaux : `build_linux_base.log`, `build_linux_0010.log`.
- Cœur : `coeurs/linux_hsfa_0010a.so`, md5 **`b456d2c7bdc3edb64a28049cf8306c25`**.
- Cœur de base (5e0eda6, même machine) : `coeurs/linux_hsfa_base.so`, md5 `13c0d7e6…`.

Non-régression :

- `tests/nonreg_coeur.sh` : copie de `scripts/untranspile/nonreg_coeur.sh`, avec les sorties dans `tests/essais/` et
  le lanceur `tests/hsfa_run` compilé depuis `fbneo/hsfa/hsfa_run.c`.
- `COEUR=coeurs/linux_hsfa_0010a.so` contre `references/coeurs/linux_hsfa_501aebd.so` : **sfa3 IDENTIQUE (30), upper
  IDENTIQUE (30), hyper IDENTIQUE (40)** (`tests/nonreg_0010a.txt`).
- 16 bits : lanceurs `tests/hsfa_run16` (refuse le 32 bits → 565) et `tests/hsfa_run15` (n'accepte que le 1555).
  - Upper MAX, images 5000/5320/5500 : base = 0010 au pixel, en 565 comme en 1555.
  - Additif en 16 bits contre 32 bits : écart ≤ 8 par composante (quantification).

## 4. Démonstration

Pour comparer au banc, j'ai figé une copie du zip `fbneo/2b10/sfa3uhsfa.zip` de l'agent d'intégration MAX dans
`zips/max2b10/` (md5 `b6babbf6…`).

`tests/demo_eagle.sh` :

- Eagle choisi au curseur (R, R, U, U, U), mode Arcade contre Cammy ;
- DP + poing en boucle.

Pour trouver la palette de l'arc, j'ai imposé tour à tour les 32 palettes en additif à l'image 5320 : **l'arc =
palette OBJ 01**. Corps d'Eagle = 00, Cammy = 05.

- `captures/demo/eagle_arc_avant_opaque.png` : sans registre, l'arc est opaque, avec son contour brun-noir.
- `captures/demo/eagle_arc_apres_additif.png` : `HSFA_OBJMIX=01:1`. L'arc est lumineux, le contour sombre disparaît
  (ses couleurs sombres n'ajoutent presque rien) et le décor et le corps se voient au travers. C'est l'aspect PSP.
- `captures/demo/eagle_arc_psp_avant_apres.png` : planche PSP | avant | après.

## 5. Fork MAME (copie `mame-fork/mame`, binaire `mame-fork/cps2f_melange`)

Patch : `mame-fork/melange-sur-fork.patch`.

- Contre le `cps2.cpp` du fork partagé : sa version modifiée non commitée, gardée dans `mame-fork/cps2.cpp.avant`.
- 242 lignes, seul `src/mame/capcom/cps2.cpp` change.
- Recompilation incrémentale (cps2.cpp seul) dans la copie, après réécriture des chemins absolus des projets et des
  `.d` vers la copie. Le fork partagé n'a pas été touché.

Contenu du patch :

- `hsfa_map` : `$804220-$80423F` en `lrw8` vers `m_hsfa_mix[32]` ; `save_item` ; `HSFA_OBJMIX` lu dans `init_hsfa`.
- **`HSFA_MELANGE=1`** : la machine `hsfa` prend un écran RGB (`screen_update_hsfa`). L'image est rendue en indexé
  comme avant dans `m_hsfa_ind`, puis :
  - si aucun registre n'est posé : conversion par la palette ;
  - sinon, rendu des objets en RGB, en 2 passes :
    1. objets opaques aux règles de `prio_transpen` (le premier objet dessiné garde le pixel, priorité 31), en notant
       le numéro de l'objet qui prend chaque pixel ;
    2. objets translucides **du bas vers le haut** de la pile, sur l'image RGB, là où le masque de priorité des plans
       le permet et où aucun objet opaque plus haut n'a pris le pixel.
  - Pourquoi 2 passes : dans MAME, le haut de la pile est dessiné d'abord et bloque la suite. Sans cela, un objet
    translucide ne verrait pas les objets placés sous lui.
- Formules de mélange identiques au cœur.
- `cps2_render_sprites` devient un parcours générique (`cps2_walk_sprites`). Sans mélange, il fait les mêmes appels
  dans le même ordre.

Pourquoi `HSFA_MELANGE` est facultatif :

- avec un écran indexé, MAME applique la palette **à l'affichage** ; en RGB, elle est appliquée **au rendu** ;
- une image où la palette change entre les deux diffère donc : 1 capture sur 201, un flash de super, 24 pixels ;
- le banc de validation reste donc indexé par défaut.

Essais (`tests/lance_max_alpha.sh`) :

- c'est une copie de `lance_max.sh` sur le banc figé `zips/banc_max5_fige`, avec Eagle, `ALEA=1`, 7000 images et une
  capture toutes les 10 images ;
- binaire partagé contre copie sans variable : **journal identique, 201/201 captures identiques** ;
- `HSFA_MELANGE=1` seul : journal identique, 1 capture différente (le flash ci-dessus) ;
- `HSFA_MELANGE=1 HSFA_OBJMIX=01:1` : mélange visible. Sur l'écran de citation de victoire, le portrait d'Eagle
  utilise aussi la palette 01, et l'additif le rend transparent
  (`captures/demo/mame_victoire_{avant,apres_01additif}.png`). C'est la preuve du piège décrit au §6 : il faut
  remettre les registres à 0 hors combat.

## 6. Côté 68K : ce que l'agent d'intégration MAX doit ajouter (rien n'est intégré ici)

**Règle** : un registre suit l'**emplacement** de palette OBJ, pas une couleur. Il doit valoir 1 exactement quand
l'emplacement contient une palette d'effet additive d'un perso MAX, et 0 sinon.

**Valeurs**, avec base = 0 pour J1 et 5 pour J2 :

| perso | octets `$804220 + base + 0..4` |
|---|---|
| Eagle `$26` | 0, 1, 1, 0, 0 (emplacements +1, +2) |
| Maki `$27` | 0, 0, 0, 0, 0 |
| Yun `$2D` | 0, 0, 0, 0, 0 |
| Ingrid `$2E` | 0, 0, 0, 1, 0 (emplacement +3 de `palettes_module_upper.bin`) |
| natifs | 0 partout |

1. **Pose au chargement** des 5 palettes d'un joueur (sites `T_6f72b0`, 13 LEA, `MAX_PAL_ZONE`).
   - Ce sont les copies de 5 palettes (`MOVEQ #4,D7`), qui remplissent les emplacements OBJ base..base+4.
   - Après la copie, écrire les 5 octets du perso.
   - Il suffit de traiter les sites de combat (copie au début de la manche, et recopies éventuelles : changement de
     couleur, etc.). Les retrouver par le LEA de `T_6f72b0` suivi de l'appel de copie.
   - L'emplacement de destination donne la base : (adresse de destination − base de la palette OBJ) / 32.
   - Talon type, 5 octets par ID de `$26` à `$2E` dans `MIX_TABLE`, plus 5 zéros pour les autres IDs : environ
     100 octets de code et de données en ROM programme :

   ```
   ; D0.W = ID du perso ($103 du joueur), D1.W = 1re palette OBJ de l'emplacement (0 = J1, 5 = J2)
   HSFA_MIX_POSE:
       movem.l d0-d1/a0-a1,-(sp)
       cmpi.w  #$26,d0
       blo.s   .natif
       cmpi.w  #$2E,d0
       bhi.s   .natif
       subi.w  #$26,d0
       mulu.w  #5,d0
       lea     MIX_TABLE(pc),a0
       adda.w  d0,a0
       bra.s   .copie
   .natif:
       lea     MIX_ZERO(pc),a0
   .copie:
       lea     $804220,a1
       adda.w  d1,a1
       move.b  (a0)+,(a1)+
       move.b  (a0)+,(a1)+
       move.b  (a0)+,(a1)+
       move.b  (a0)+,(a1)+
       move.b  (a0)+,(a1)+
       movem.l (sp)+,d0-d1/a0-a1
       rts
   MIX_ZERO:  dc.b 0,0,0,0,0
   MIX_TABLE: dc.b 0,1,1,0,0   ; $26 Eagle
              dc.b 0,0,0,0,0   ; $27 Maki
              dcb.b 5*5,0      ; $28-$2C (non MAX)
              dc.b 0,0,0,0,0   ; $2D Yun
              dc.b 0,0,0,1,0   ; $2E Ingrid
       even
   ```

   - Coût : environ 150 cycles par chargement, aucun par image.
   - Pour les natifs, écrire aussi les zéros. Indispensable : un natif peut reprendre l'emplacement d'un MAX à la
     manche ou à la partie suivante.
2. **Remise à 0 hors combat (obligatoire)**.
   - Les mêmes emplacements OBJ servent à d'autres écrans : le portrait de la citation de victoire utilise la palette
     01, ce que montre l'essai MAME du §5. La sélection, le VS et les fins aussi.
   - Écrire 0 dans les 32 octets (8 × `CLR.L`, ou `MOVE.L #0` sur `$804220`, `$804224` … `$80423C`) dès qu'on sort du
     combat.
   - Endroit le plus sûr : le changement d'écran (passage de `$FF8004` hors de l'état de combat), ou l'entrée des
     chargeurs de palettes des écrans de victoire, VS et fin.
   - Variante défensive, plus simple : dans la routine d'image, si l'état n'est pas « combat », faire `CLR.L` des 8
     mots longs. Elle coûte environ 8 × 28 cycles par image hors combat.
3. **Banc** : le fork n'applique les registres qu'avec `HSFA_MELANGE=1`.
   - Les écritures sont sans effet sur la validation, qui reste indexée.
   - Pour vérifier la pose : `HSFA_MIX_LOG=<fichier>` dans le cœur, ou une prise d'écriture Lua sur `$804220-$80423F`
     au banc.
4. **Hyper (ro9a)** : mêmes registres (mode 2). À faire seulement si les MAX y entrent un jour.
5. **Pour plus tard** (pas sur la PSP pour les MAX, ou hors sujet) :
   - les ombres des persos sont à 75 % sur PSP (noir, alpha `C0`), soit le mode 3 sur la palette d'ombre ;
   - les jauges du HUD sont à 50 %, soit le mode 2.
   - Ce serait un changement visible des natifs : à décider avec l'utilisateur.

## 7. Questions ouvertes

1. **Pour la session MAX (Ghidra)**, à transmettre :
   > Dans la routine d'affichage des objets de SFA3 MAX (EBOOT EU), quelle condition choisit
   > `sceGuBlendFunc(GU_ADD, GU_FIX, GU_FIX, 0xFFFFFF, 0xFFFFFF)` (commandes GE `0xDF` = `0x0000AA` puis `0xE0` /
   > `0xE1` = `0xFFFFFF`) au lieu de `SRC_ALPHA / ONE_MINUS_SRC_ALPHA` (`0xDF` = `0x000032`) ? Est-ce le numéro de
   > palette (table par perso), un champ de l'objet (lequel, à quel décalage), ou un drapeau de la frame ou de
   > l'animation ?
   >
   > Sur ma mesure (dumps GE), le mode suit l'emplacement CLUT : Eagle 1-2, Ingrid 3. Si c'est un champ d'objet, le
   > même effet pourrait un jour utiliser une autre palette. Et si des persos natifs ont aussi la condition dans
   > des coups non essayés, le registre par palette resterait suffisant, mais la table devrait changer.
2. **Maki et Yun** : rien d'additif sur 11 manipulations chacun.
   - Des coups non essayés (supers au pied, coups spéciaux de Yun en l'air, etc.) pourraient en avoir.
   - La réponse à la question 1 trancherait.
3. **Ombres et HUD** (§6, point 5) : faut-il les translucides ? Ce serait un choix visuel de l'utilisateur, hors MAX.
4. **États sauvegardés** : 32 octets de plus dans les états d'Upper et d'Hyper (cœur et fork). Les anciens états
   ne se rechargent pas.
5. **Cœur 16:9** (`-DHSFA_WS`) : non compilé ici. Le code est commun (`cps_obj.cpp`, `ctv*`), mais il faut le
   compiler et le tester.

## 8. Fichiers

| chemin | contenu |
|---|---|
| `0010-HSFA-melange-des-objets-par-palette-OBJ.patch` | patch FBNeo (contre `rejeu` 5e0eda6) |
| `coeurs/linux_hsfa_0010a.so`, `coeurs/linux_hsfa_base.so` | cœurs Linux |
| `tests/nonreg_0010a.txt`, `tests/nonreg_coeur.sh`, `tests/fb.sh`, `tests/hsfa_run{,16,15}` | non-régression (32 et 16 bits) |
| `tests/demo_eagle.sh`, `tests/essais/pal_*` | démonstration et recherche de la palette de l'arc |
| `captures/demo/`, `captures/psp_mesures/` | avant / après, mesures PSP annotées |
| `mame-fork/melange-sur-fork.patch`, `mame-fork/cps2f_melange`, `mame-fork/cps2.cpp.avant` | fork (copie) |
| `tests/lance_max_alpha.sh`, `tests/mame/` | essais au banc |
| `outils/` | `gedump.py`, `bilan.py`, `palidx.py`, `marque.py`, `planche_add.py`, `pa.py`, `seq.py`, `batterie.sh`, `choix.sh` |
| `psp/dumps/`, `psp/bilan_modes.txt` | dumps GE et bilan |
| `re_ajouts/` | lignes pour `re/` (allocations, `sfa3_arcade`, `max_psp`) |
| `zips/max2b10/`, `zips/banc_max5_fige/` | constructions MAX figées |

---

## 9. Révision : mélange PAR OBJET (0010 v3), états compatibles (v2), 16:9

Réponse de la session MAX :

- le PSP décide le mélange **par objet** : champ `+0xAA` → sprite `+0x56`, mode 1 = additif ;
- objets additifs : Eagle `$2B`, `$33` (animations 1-6), `$34` ; Maki `$2F-$31` ; Ingrid `$2D` / `$2E`, `$35` / `$36`,
  `$37` ; fin, sous-type 66 ; natifs, aucun.

Étude et mesures : `ETUDE-MELANGE-PAR-OBJET.md`. Choix retenu : (a), le bit 12 du mot X.

### 9.1 Interface finale

| adresse | contenu |
|---|---|
| `$804220-$80423F` | octet par palette OBJ : 0 opaque, 1 additif, 2 alpha 50 %, 3 alpha 75 %, 4 soustractif, 5 noir à 75 % (0011) |
| `$804240-$804241` | mot, **octet bas = mode des objets marqués** : bit 12 du mot X de la liste du jeu. 0 = bit ignoré |

Règle de priorité, la même dans le cœur et dans le fork :

1. objet marqué (bit 12) et `$804240` ≠ 0 : mode de `$804240` ;
2. sinon, registre de la palette ≠ 0 : mode de la palette ;
3. sinon, option « ombres » (0011) ;
4. sinon, opaque.

Le bit 12 de X n'est jamais posé par les programmes traduits (0 sur 10,99 M d'entrées). Les convertisseurs de liste
le gardent :

- cœur : `HsfaEclater`, `x & $F000` ;
- banc : `banc_sprites.lua`, même changement → **`mame-fork/banc_sprites-bit12.diff`** (fichier partagé, à intégrer
  par le coordinateur).

Ligne `allocations.tsv` (`re_ajouts/allocations.tsv`, zones 23 → 23 conflits, `verifie.py` 0 erreur) :

```
materiel_cps2	$804240	$804241	mode des objets marqués, bit 12 du mot X (agent_alpha)	utilisé	<workspace>/work/agent_alpha/ALPHA-PSP.md §9 ; patch FBNeo 0010 v3	mot, octet bas = mode (0 = bit ignoré, 1 additif…) des objets dont le mot X de la liste du jeu a le bit 12 (posé par EFFET_W) ; prioritaire sur $804220-$80423F ; cœur FBNeo HSFA (mode 2) et copie du fork MAME
```

### 9.2 États (v2, gardé en v3)

Le format libretro de FBNeo est une concaténation brute des zones, sans nom ni version. Les registres sont donc la
**dernière zone** de l'état (`LibretroAreaScan`, versions `HSFA_CORE`), lue seulement si l'état chargé la contient.
Chaque partie absente vaut 0 : les palettes (32 octets), puis `$804240` (1 octet).

Essais (`tests/hsfa_run_etat`, sauvegarde à l'image 5300, arc d'Eagle à 5320) :

| état chargé | cœur | résultat |
|---|---|---|
| ancien (base) | v3, avec tout forcé à 1 | registres à 0, opaque |
| v2 (palettes à 1) | v3 | palettes restaurées, `$804240` à 0 |
| v3 (`$804240` = 1) | v3 sans forçage | additif restauré |
| v3 | base | chargé, opaque |

### 9.3 Résultats

**Non-régression, registres jamais écrits** :

| cœur | 32 bits | 16 bits (565) |
|---|---|---|
| 4:3 | IDENTIQUE ×3 | IDENTIQUE ×3 |
| 16:9 (`hsfaws`, contre le 16:9 de base 5e0eda6) | IDENTIQUE ×3 | IDENTIQUE ×3 |

**Démonstration du bit 12**. Le cœur d'essai, hors patch, a un crochet `HSFA_ESSAI_BIT12=01` qui marque les objets
de la palette 01, comme le ferait EFFET_W :

| essai | résultat |
|---|---|
| bit posé, registre à 0 | identique à la base |
| registre posé, sans bit | identique à la base |
| bit + `$804240` = 1 | additif, égal **au pixel près** au mode par palette |
| priorité | bit (1) > palette (2) ; si `$804240` = 0, c'est le mode de la palette qui s'applique |

Captures : `captures/demo/eagle_arc_bit12_*.png` et `ws_eagle_arc_avant_apres.png` (16:9).

**Banc** (copie du fork, `melange-sur-fork-v3.patch`, Lua d'essai `mame-fork/lua/`) :

- défaut : journal et 201 captures identiques au binaire partagé ;
- bit + registre = mode par palette (201 captures identiques) ;
- bit sans registre : sans effet.

## 10. Patch 0011 : option « Ombres transparentes (PSP) »

Étude : `ETUDE-OMBRES-JAUGES.md`. **Jauges : non faites**, il ne s'agit pas d'une transparence (rectangles de teinte
PSP) ; décision laissée à l'utilisateur.

`0011-HSFA-option-ombres-transparentes-PSP.patch` (sur 0010 v3, commit 832b069) :

- **DIP** : bit 7 du Dip A, « Transparent shadows (PSP) », **activé par défaut**, pour tous les pilotes HSFA, modes 1
  et 2. Variable d'essai `HSFA_OMBRES=0/1`, prioritaire sur le DIP.
- **Règle par tuile** : palette OBJ 0x14 ET code global ∈ {`0284A`, `305DF-30613`, `50888-5088A`}.
- **Mode 5** = noir à 75 % (dst × 0x3F / 256). Les registres de 0010 peuvent aussi l'utiliser.
- **Priorité** : modes du jeu > option > opaque.

**Contrôle automatique** (`tests/controle_ombres.sh`, `outils/controle_ombres.py`) :

- 7 parties (SFA3, Upper, Hyper, Hyper 30 persos, Eagle, Maki, ro9a), 980 captures × 3 variantes : option coupée,
  option active, témoin (ombres peintes en magenta, cœur d'essai) ;
- **0 pixel modifié hors d'une tuile d'ombre** ; tous les pixels d'ombre visibles sont modifiés ;
- 316 189 pixels modifiés au total (`tests/controle_ombres.txt`).

**Fins** : 14 fins d'Upper atteintes sur ro9a (Ryu, persos 01-0F sauf 04 et 07, qui n'ont pas atteint la fin en
22 000 images). Les codes d'ombre n'apparaissent qu'en combat (`2/4/6`) et dans les combats de démo, jamais dans
une fin ni sur un autre écran.

**Non-régression** :

- option coupée : IDENTIQUE ×3 en 32 et en 16 bits, en 4:3 et en 16:9 ;
- option active : seules les captures changent ; journaux et son identiques.

Captures : `captures/demo/ombres_upper_poteaux_*.png` (ombres translucides, poteaux du décor intacts),
`ombres_hyper_zero_zoom.png`, `ombres_ws_avant_apres.png`.

**Banc** (`melange-sur-fork-v4.patch` = v3 + ombres, `HSFA_OMBRES=1` avec `HSFA_MELANGE=1`) :

- défaut : journal et 201 captures identiques au binaire partagé ;
- ombres actives : 109 captures, seulement des assombrissements sur les lignes 198-218 (le sol).

## 11. Cœurs construits (0010 v3 + 0011, `builds2/`, `MD5SUMS`)

| plate-forme | hsfa | hsfaws |
|---|---|---|
| Linux x86-64 | `c493d2f6916fcfc357741b14ff6a1c34` | `dad31c659e563724342f58453cd661c3` |
| Android arm64 (NDK r28c, `build_android.sh`) | `3bd1bf16c8a6e018ab8ce53dba23ff26` | `57dd6dd6f0cfff1c19190437d94b52a0` |
| ROCKNIX aarch64 (`build.sh`) | `0f10ca3ef3407d717873386b60defe21` | `a0b4036b79bdb942b6955b142b88bffa` |
| Windows x64 (`build_win.sh`, `LIBS=-static`) | `44918828826f6ae6209ca4d0d3f89604` | `748f8573205a748d307998dbb109c8ff` |

- Les DLL ne dépendent que de KERNEL32 et msvcrt.
- Les variantes 16:9 ont le nom « HSFA Widescreen ». Les 8 cœurs contiennent l'option 0011.
- Les en-têtes générés (`driverlist.h`, `gamelist.txt`) ont été recopiés de l'arbre régénéré : `ndk-build` ne les
  régénère pas.
- `<workspace>` dans les scripts : relevé dans `WORKSPACE-SCRIPTS.txt` (corrigé depuis dans le dépôt).

## 12. Talon EFFET_W pour l'agent d'intégration MAX

Données d'entrée :

- `OFF_ADD` = décalage de l'octet « additif » de l'objet arcade, la recopie de `+0xAA` faite par le traducteur ;
  fourni par l'agent d'intégration ;
- `LP` = registre qui contient la position d'écriture dans la liste d'objets (mémoire `$70xxxx`) à l'entrée et à la
  sortie de la routine d'affichage `$19D9A`. Dans l'arcade SFA3, la liste s'écrit par **A1**, avec **D7** = place
  restante (« budget D7 », `champs.tsv` frame +$2). **À confirmer dans l'image d'Upper** avant d'écrire le talon.
  Si ce n'est pas un registre, c'est une variable RAM : lire sa valeur avant et après.

```
; dans EFFET_W_xx, à la place de « jsr $19D9A » (après move.b #$10,$9(a6)) :
EFFET_W_AFF:
    tst.b   OFF_ADD(a6)            ; octet « additif » de l'objet (copie de +0xAA) : 1 = additif
    beq.s   .normal
    move.l  LP,-(sp)               ; début des entrées que l'objet va ajouter
    jsr     $19D9A                 ; affichage ordinaire (classe $10)
    movea.l (sp)+,a0               ; a0 = première entrée ajoutée
.boucle:
    cmpa.l  LP,a0                  ; jusqu'à la position d'écriture courante
    bhs.s   .fin
    ori.w   #$1000,(a0)            ; bit 12 du mot X (mot 0 de l'entrée de 8 octets)
    addq.l  #8,a0
    bra.s   .boucle
.normal:
    jsr     $19D9A
.fin:
    rts
```

- Préserver a0 si la routine appelante s'en sert (`movem`).
- Coût : environ 20 cycles par entrée, seulement pour les objets additifs.
- Ne pas marquer le marqueur de fin (X = Y = `$8000`) : il est écrit plus tard, par la fin de liste.
- **Registre de mode** :
  - au début de chaque combat (entrée de l'état de combat, ou chargement des palettes des joueurs) :
    `move.w #$0001,$804240` (additif) ;
  - remise à 0 hors combat : `clr.w $804240`.
  - Sans effet tant qu'aucun objet n'est marqué ; à garder quand même par prudence (écrans de fin, sous-type 66).
- **Fin, sous-type 66** : même marquage dans le gestionnaire de l'acteur de fin, avec le registre posé pendant la fin.
- **Banc** : le bit n'est visible qu'avec `HSFA_MELANGE=1` et `banc_sprites.lua` modifié (diff §9.1).

## 13. Patch 0012 : 16:9 « remplir la hauteur » (2026-10-24)

`0012-HSFA-16-9-format-remplir-la-hauteur.patch`, sur la référence `agent_fbneo_rejeu/fbneo` 35b617b
(= 0010 v3 + 0011) ; commit 1f8bc0b dans `fbneo3/`.

Le numéro 0012 avait été prévu pour les jauges, finalement abandonnées. La partie jauges de
`ETUDE-OMBRES-JAUGES.md` est corrigée : les rectangles sont rejetés par le GE, et ce qui se voit sur PSP est un
dégradé de remplissage.

**Option du cœur** `fbneo-hsfa-format`, « Screen format (fill height) » :

- présente seulement dans le cœur 16:9, et active seulement pour les pilotes HSFA ;
- valeurs : Off (par défaut), 4:3, 3:2, **14:9 (pixels arcade, pleine largeur)**, 16:10, 5:3, 16:9.

| format | largeur montrée | rognage | forme des pixels |
|---|---|---|---|
| 4:3 | 384 px | centré, 32 px de chaque côté | arcade (0,778) |
| 3:2 | 432 px | centré, 8 px de chaque côté | arcade (0,778) |
| 14:9 | 448 px | aucun | arcade (0,778) |
| 16:10, 5:3, 16:9 | 448 px (plafond) | aucun | aspect annoncé = le format |
| Off | 448 px | aucun | 16:9, soit des pixels environ 14 % plus larges que l'arcade |

- La largeur vaut format × 224 / forme du pixel arcade (384 px ↔ 4:3), soit format × 288, rendue paire.
- Le rognage se fait à la sortie vidéo : pointeur décalé, même pas de ligne.
- `base_width` et `aspect_ratio` suivent le format, avec `SET_GEOMETRY` quand l'option change.
- La valeur 14:9 est l'option « pixels arcade » proposée pour le mode Off : toute la largeur, sans étirement ;
  laisse des bandes étroites sur un écran 16:9. Elle reste un choix ; Off ne change pas.

**Vérifications** :

- l'image de chaque format est **exactement** la découpe centrée de l'image Off (3 images × 5 formats) ;
- la géométrie annoncée est correcte (`tests/hsfa_run_geo`) : 4:3 → 384 × 224 à 1,3333 ; 3:2 → 432 × 224 à 1,5 ;
  14:9 → 448 × 224 à 1,5556 ;
- HUD complet en 3:2 et en 4:3 (portraits, noms, jauges du bas) : le HUD tient dans les 384 px centraux ;
- captures : `captures/demo/format_remplir_hauteur_{5320,6000}.png` (Off, 3:2, 4:3, 14:9, chacune à son aspect).

**Non-régression** (`HSFA_OMBRES=0`, format Off) : IDENTIQUE ×3 en 4:3 et en 16:9, en 32 et en 16 bits
(`tests/nonreg3_*.txt`).

**Cœurs** (`builds3/MD5SUMS`) :

| plate-forme | hsfa | hsfaws |
|---|---|---|
| Linux | `0f5051c94f42b70452c3b1e443012790` | `12da7fad833e9dad3042eb4bc115471d` |
| Android | `5f808114a6f2a5310db2c427844f6d54` | `63764e03a65c88a74daa0063b09f491f` |
| ROCKNIX | `c295ae32b126c98d9859230d6d62bc35` | `a1f1fec2f0733a0fdb7e76509da8697e` |
| Windows | `446c4511ee9a9cd3ebdca67edf6b0fec` | `143ade812c5567e7bb335c7a0bf8b3d1` |

Les DLL ne dépendent que de KERNEL32 et msvcrt.
