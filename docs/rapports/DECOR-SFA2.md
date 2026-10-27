# DECOR-SFA2 — premier import d'un décor de SFA2 (Ryu) dans la traduction 68000 de SFA3 (fork `sfa3hx`)

Dossier : `<workspace>/work/decors_sfa2/`. Je n'ai écrit que dans ce dossier.
- Lus seulement : `src/hsfa`, `work/mame*`, `decors_ws/`, `carto_sfa2/`, `agent_flux/`.
- Le fork est une copie du binaire « flux » (`mame/cps2f`).
- MAME : `nice -n 19`, dossiers nvram/cfg/state/snap propres (`mame/run/<essai>/`), jamais `-state`, aucun `pkill -f`/`pgrep -f`.

ROM de départ : traduction ro3 du 2026-10-10 (`decors_ws/injection_fork/trav`, `prog_ro3.bin` md5 `2a3f68eb…`,
identique à `work/mame/roms_tr`), en mode « bases de plans » (`HSFA_PLANS=300,340,3a0`).

## 0. En bref

1. **Format** : le format des décors SFA2 est celui de SFA3 : mêmes listes, blocs 256 px, super-tuiles scroll1,
   gestionnaires de plans, CPS-B, longs `$40/$44`, objets de 16 o. Les différences sont mécaniques (§1).
2. **Export** (agent d'export, `export/EXPORT.md`) : contrôle **0 px** sur 497 images × 3 plans, sur le composite et
   sur les sprites. Parallaxe scroll1 3/4, scroll3 1/4. Pas d'animation de tuiles ni de palettes.
3. **Import** : le décor devient le nouveau **`$FF8100 = $50`**.
   - Numérotation retenue : décor SFA2 `$s` → `$50 + s`, donc `$50`–`$72` pour les 18. Upper occupe déjà `$40`–`$4E`.
   - Tuiles en codes locaux libres : 395 en scroll1 `$6000+`, 289 en scroll2 `$8A00+`, 226 en scroll3 `$1000+`.
   - Tables par décor relogées et étendues à 58 entrées dans `ext_c80000.bin`.
   - Bibliothèques recopiées + blocs neufs dans `ext_b00000.bin`.
   - 58 correctifs du programme, dont 1 444 o de code dans la zone libre `$93200`.
4. **Validation au fork** : le décor importé est **identique au pixel à sfa2u**.
   - Tilemaps entières scroll1/2/3 + palettes : 0 px.
   - Composite écran des 3 plans au même défilement : **0 / 86 016 px** sur 3 positions de caméra.
   - Défilements de parallaxe identiques à ceux de sfa2u.
   - Partie Arcade complète (Ryu, 8 combats sur le décor `$50`, boss, fin) : **aucune exception**.
   - Hors décor `$50`, rien ne change : écrans identiques à la ROM de base.
5. **Sélection** : crochet au point de choix du décor du mode Arcade (`$4A428`). Modes toujours SFA3 / toujours
   SFA2 / tirage, et table perso → décor SFA2. Il est appliqué à ma copie seulement (§4).
6. **Musique** : la musique SFA2 de Ryu (commande `$0051` → flux **Y70**) est jouée sur ce décor. Mesure dans le
   WAV : gain 0,261 = gain du lecteur (§5).
7. **Cœur FBNeo décors** (`injection_fork/fbneo-decors`, 448×224) : le décor s'affiche. La partie 4:3 est identique
   au fork, hors sprites et HUD.
8. **Restent** :
   - les **objets sprites du décor** (temple, nuages, corbeau), identifiés au §3.4 ;
   - la place en scroll2 pour les 17 autres décors (§6).

## 1. Format SFA2 comparé à SFA3

Vérification par désassemblage de sfa2u (`carto_sfa2/dump/sfa2u/prog_opcodes.bin`) et du programme traduit. Le
convertisseur `py/sfa2.py` + `py/construit.py` relit le décor ; le résultat est identique au pixel (§3).

| élément | SFA2 (sfa2u) | SFA3 traduit (ro3) | conversion |
|---|---|---|---|
| listes s1/s2/s3 | `$1CFF4`/`$1D0EC`/`$1D2A4`, mots de décalage + octets (4-8 / 16 / 64) ; types `$1CFC4`/`$1D0BC`/`$1D274` | `$18CA30`/`$18CB5C`/`$18CD8C` ; types `$18C9F0`/`$18CB1C`/`$18CD4C` ; octets lus à `k^1` ; la routine copie 128 o | numéros de blocs renumérotés, octets échangés, liste complétée à 128 o |
| blocs scroll1 + super-tuiles | `$2AD300` (128 o) + `$2B1A80` (64 o = 16 × (code, attr)) | même structure ; super-tuile = long PS2 (attr, code) | ordre des mots inversé dans la super-tuile, code local 8×8 |
| bloc scroll2 | 256 × (code mot, attr mot) = 1 Ko, code + (−`$5C00`) | 256 codes + 256 attr octets, code + `$1600` = local | attr ≤ `$FF` (vérifié), code local − `$1600` |
| bloc scroll3 | 64 × (code, attr), code + `$900` | 64 codes + 64 attr octets, code local sans ajout | idem |
| palettes de plans | denses, `$400` par décor (`$27C1C0`/`$2865C0`/`$2909C0`), 0RGB **luminosité 0**, copiées telles quelles | table de décalages signés, 0RGB, copie avec `or.l #$F000F000` ; scroll3 : 31 palettes, `$7F` forcée | copie directe (luminosité F au final = sfa2u, vérifié) ; **palette scroll3 31 → 4** (Ryu l'utilise) |
| palettes de sprites de décor | 7 × 32 o → `$90C000` (palettes 0-6) | 6 palettes → `$90C1E0` (`$0F`-`$14`) | à remapper avec les objets (§3.4) |
| gestionnaires de plans | 20 par plan (init X/Y + rapport X/Y) | même moteur, bibliothèques de rapports différentes (pas de 3/4 en scroll1, pas de 1/4 X en scroll3) | gestionnaires neufs écrits (§2.4) |
| caméra (scroll2) | gestionnaire de Ryu = init `$1C0,0` + caméra `$1B662`/`$1B6DA` | gestionnaire par défaut `$25BF4` : même code | alias (décor 0) |
| bornes caméra | longs `$40/$44` de scroll2 (`$00100000/$01000280`, toutes) | identiques | alias |
| CPS-B `$32/$3A(A5)` | `$1C34A` : Ryu `$2700/$2641` | même vocabulaire (`$9C940`) | entrée neuve |
| rowscroll | effet `$1D836` → `rts` pour Ryu ; table constante +`$C0` | effet `$19B9C` | alias « rts » (`$23134`) ; constante identique (vérifié) |
| objets de décor | `$1EB66`, 16 o : X `+0`, Y `+2`, groupe `+4`, `+5`, routine `+6`… | `$358BC0` : routine `+0`, X `+2`, Y `+4`… | champs réordonnés + routines 68K (§3.4) |
| musique | par décor, `$154EE` (Ryu `01`) | par perso (`$9AFD0`), par décor en VS (`$9AF40`) | crochet (§5) |
| choix du décor | `$7A7A[perso adverse]` | `$4A406` : `$4AAE4[perso]×2 → $174(A5)` puis `$4D150` : `$174 → $100` | crochet (§4) |

Le décor de Ryu ne demande ni animation de tuiles, ni animation de palettes, ni perspective (export).

## 2. Import : technique

`py/construit.py` produit `import/<essai>/`. Il contient `roms/sfa3hx/`, `ext/` (`ext_a04000` + `ext_b00000` +
`ext_c80000`), `hsfa_plans_sfa2.bin`, `tramp.s`/`.bin` et `rapport.json`. Il prend environ 5 s.

### 2.1 Tuiles (région en mode base)
Les octets MAME d'origine sont copiés depuis la région `:gfx` de sfa2u (même format que le fork), puis
dédoublonnés :
- scroll1 : 395 codes `$6000-$618A` (paires paire/impaire conservées) ;
- scroll2 : 289 codes `$8A00-$8B20` ;
- scroll3 : 226 codes `$1000-$10E1`.

Le résultat est `hsfa_plans_sfa2.bin`, chargé en `$3000000`.

### 2.2 Bibliothèques (copie relogée + blocs neufs), `ext_b00000.bin` (424 Ko)
Il y a 9 opérandes `LEA` :
- blocs scroll1 : 4 sites ;
- super-tuiles : 3 sites ;
- scroll2 et scroll3 : 1 site chacun.

Blocs neufs :
- scroll1 : `$5E-$61` ;
- super-tuiles : indices 2 377-2 428 ;
- scroll2 : `$92-$95` ;
- scroll3 : 15 numéros libres (`$8B, $8F, $91-$9D`).

Les numéros restent sur un octet. Les autres écrans (fins, VS) gardent leurs blocs d'origine.

### 2.3 Tables par décor relogées et étendues (`ext_c80000.bin`, 62 Ko)
Chaque table est copiée avec **58 entrées** (indice = `$100/2`) :
- 0-31 : SFA3 d'origine ;
- 32-39 : copies de l'entrée 0 (place d'Upper, inutilisée en ro3) ;
- 40-57 : décors SFA2, alias du décor SFA3 du même perso, sauf l'entrée 40 (Ryu SFA2) quand elle est neuve.

Les tables de décalages sont recopiées avec leurs données. **Liste complète des tables par décor** (= les « ≈ 17
tables » du §113, recensées sur les 68 accès à `$100(A5)` du programme traduit, `format/sites100_tr.txt`) :

| table (image ro3) | rôle (arcade SFA3) | entrée `$50` | technique |
|---|---|---|---|
| `$18C9F0` / `$18CB1C` / `$18CD4C` | types des plans | 2 / 0 / 0 (SFA2) | relogée |
| `$18CA30` / `$18CB5C` / `$18CD8C` | listes de blocs | neuves | relogée + données |
| `$1619D0` / `$165EB0` / `$16CD10` (2 sites chacune) | palettes des plans (`$1FC38`…) | neuves (1 Ko × 3) | relogée + données |
| `$15D910` (2 sites) | palettes des sprites de décor (`$1FE0A`) | alias | relogée + données |
| `$358BC0` (2 LEA) | objets de décor (`$1A644`) | **liste vide** | relogée + données |
| `$9C0D0/$9C0D4`, `$9C1F0/4`, `$9C2F0/4` | longs `$40/$44` (bornes, `$189E8`…) | alias (identiques) | relogée |
| `$9C940/$9C942` | contrôle CPS-B (`$18876`) | `$2700/$2641` | relogée |
| `$98FB0` (2 sites) | couleur de « ROUND » (`$7CBAC`) | alias | relogée |
| `$A3030`, `$A3070/2`, `$A30F0/2` | initialisation des joueurs (`$2BECA`, `$2BF16`, `$2BFE0` : `$E(A6)`, X/sol ; constantes) | alias | relogée |
| `$9E480/$9E482` | positions par décor (`$8DF3E`, aussi lu avec `$172` = décor précédent) | alias | relogée |
| `$02541A` (en ligne) | ordre de mise à jour des plans (`$1749A`) | `$2545A` (s2, s1, s3 = SFA2) | trampoline |
| `$02548A` / `$025BB4` / `$025EFE` | gestionnaires scroll1/2/3 (`$17532`/`$17C6C`/`$18000`) | neuf / défaut / neuf | trampoline |
| `$022562` (JMP) | effet par décor : rowscroll, etc. (`$19BA8`) | `rts` (`$23134`) | trampoline |
| `$001FB6` | ordre des plans, 2ᵉ moteur (fins, `$2643E`) | alias | trampoline |
| `$97DD0`+`D3` (`$10E68`, `$3C32A`) | animations de palettes par décor | alias (D3 − `$50`) | `jsr $C40.w` |
| `$C6664`+`D1·4` (`$2FA1A`, `$2FB66`) | animations par décor (`$8E18E`) | alias | trampoline |
| `$378A20` (`$193F8`), `$1868B0` (`$1A76E`) | animations des objets de décor, données par décor | alias | trampoline |
| masques `$C0A00400` (`$2F804`), `$3F60BDB3` (`$79880`) | tests de bits par décor | alias | trampoline |
| `$9AF40` / `$9AFD0` | musique par décor (VS) / par perso | `$0051` | crochet `$2219E` |
| `$A3A50` (`$4AAE4`), `$A33B0` | perso → décor, rivaux | inchangé | crochet `$4A428` |
| bibliothèques `$107670`, `$10A570`, `$12F7B0`, `$14ADB0` | blocs | neufs | copie relogée |

Les comparaisons `cmpi.w #$14/#$04/#$1E/#$38,$100(A5)` (cas de Bison, Chun-Li, Juli/Juni, Gen) donnent « faux »
pour `$50`, ce qui est correct. Les autres palettes (`$0128(A5)`, routines `$6402…`) ne dépendent pas de `$100`.

### 2.4 Code ajouté (zone libre `$93200-$937A4` après la fin du code traduit ; 16 o en `$C40`)
- **Tables de sauts en ligne** (6 sites). `move.w (d,PC,D0),D1 ; jsr/jmp (d,PC,D1)` devient `jsr/jmp TJ.l ; nop`.
  TJ reprend la table d'origine pour `D0 < $40`, sinon une table de longs (indices 32-57).
- **Alias de registre** (8 sites). La lecture de `$100(A5)` passe par un trampoline : si la valeur est ≥ `$50`,
  il retire `$50`, ce qui donne le décor SFA3 du même perso.
  - Deux sites (`$10E68`, `$3C32A`) ont l'instruction suivante comme cible de boucle. Seule la lecture (4 o) y est
    remplacée, par `jsr $0C40.w`.
  - Contrôle automatique : aucune cible de branchement à l'intérieur d'une zone corrigée.
- **Gestionnaires neufs** (parallaxe exacte de SFA2), écrits avec les routines traduites `$2594C`/`$25A84`/
  `$25B22`/`$25B68` (scroll1) et `$26330`/`$2646C`/`$26476`/`$264EA` (scroll3) :
  - scroll1 : init `$1C0,0` ; X = 3/4·(caméra), Y = 3/4 ;
  - scroll3 : init `$140,0` ; X = 1/4, Y = 1/4.
- **Garde** : les lecteurs de `$FF8100` hors des sites traités sont journalisés quand le décor vaut ≥ `$50`
  (`lua/partie.lua`). Les lectures faites par Lua en fin d'image sont exclues ; elles causaient le bruit du 1er
  essai.

## 3. Validation

### 3.1 Fork MAME, décor forcé `$50` (`lua/essai.lua`)
Caméra aux butées gauche et droite puis au centre (X des joueurs imposés) ; relevé FRM0 ; `py/compare_plans.py`.
Les mesures de sfa2u viennent du relevé de l'export (1 993 images).

| contrôle | résultat |
|---|---|
| défilements fork vs sfa2u au même scroll2 (3 positions) | identiques : s1 `00F0/0010/0180`, s3 `00D0/0130/0100` |
| tilemap scroll2 entière (1024²) / scroll3 (2048²), couleur + transparence | **0 px** (82 827 / 954 368 px opaques) |
| anneau scroll1 (512²) au même défilement | **0 px** sur les 3 positions |
| composite écran des 3 plans (ordre CPS-B `$270E`, rowscroll, vidéo `$000F`) | **0 / 86 016 px** sur les 3 positions |
| non-régression : ROM corrigée sans sélection, décor naturel `$08`, 3 captures plein écran | **0 px** contre la ROM de base, mêmes défilements |

### 3.2 Partie Arcade complète (`lua/partie.lua` = `tournee.lua` du banc + journaux)
Construction `--selection sfa2 --table-essai`, où tous les décors de persos SFA3 renvoient à `$50`, Ryu, 40 000
images :
- **20 manches, FIN, aucune exception** ;
- 8 combats sur le décor `$50`, choisi par le chemin naturel `$4D156` ;
- combat final contre Bison sur `$14` (cas spécial conservé) ;
- séquence de fin atteinte.

Captures : `captures/planche_partie1.png` (Chun-Li, Guy, Zangief, Dan, Rose, écrans de victoire et VS).

Partie en mode **tirage** (`--selection alea`) : §4.

### 3.3 Cœur FBNeo décors (448×224, `fbneo_hsfaws_libretro.so` de `injection_fork`)
- Archive `fbneo/sfa3hsfa.zip` (avec `injection_fork/py/paquet_decor.py`), lanceur `fb/hsfa_decor`, `DEC=50`.
- Combat stable sur `$50`, 4 200 images, sans exception.
- La partie 4:3 centrale est identique à la capture du fork à la même position. Les seuls écarts sont dans les
  sprites et le HUD (adversaire différent) : `captures/fbneo_vs_fork_gauche.png`.
- Bandes 448 : `captures/fbneo_448_gauche_droite.png`. Le décor SFA2 n'est pas élargi ; la bande gauche est noire
  au-delà de la course.

### 3.4 Objets du décor en sprites (non portés)
Ils ont été identifiés par l'export (`export/out/decor00/sprites/`, contrôle 0 px). Il y en a trois :
- **temple** : objet `$FFB180`, routine `$0000`, X `$26E` Y `$B1`, 14 entrées, palette 1, priorité 3, parallaxe
  9/16 ;
- **nuages** : objets `$4E00`/`$4E01`, 2 × 2 instances affichées une image sur deux, dérive −0,17 px/image,
  palette 4, parallaxe 1/4 ;
- **corbeau** sur la branche : animé, 71 poses, palette 5, priorité 7.

Il y a 123 tuiles 16×16 (`$14801-$1487B` de sfa2u). Pour les porter, il faut :
1. **Tuiles** : copie dans la région étendue du fork, dans la banque « décor » des sprites. Les codes sont étendus
   par les bits X 10-11, comme pour les persos d'Upper.
2. **Palettes** : les 7 palettes de sprites de SFA2 (0-6) vont dans les emplacements de décor de SFA3 (`$0F-$14`,
   table `$15D910`) ; il faut renuméroter le champ palette des entrées.
3. **Enregistrements** : conversion des 4 enregistrements au format SFA3 (champs réordonnés) dans la liste du
   décor `$50` (elle est vide aujourd'hui).
4. **Routines** :
   - `$0000` (objet fixe) a sans doute un homologue dans SFA3, à vérifier ;
   - les routines `$4E00/$4E01` (nuages) et l'animation du corbeau sont du 68K de SFA2 ; il faut les traduire
     vers la disposition RAM du programme traduit (champs `+$50/+$58`, A5).
   - Coût estimé : environ ½ jour pour ce décor.

## 4. Sélection du décor en mode Arcade

Point de choix (arcade SFA3 `$1EBFE-$1EC1E`, programme traduit) :
- `$4A406` : `D0` = perso adverse, puis `bsr $4AAE4` (table `$A3A50`, perso → décor), puis `add.w D0,D0`, puis
  `move.w D0,$174(A5)` en `$4A428`, puis les cas spéciaux (Bison final `$14`, rivaux `$A33B0`) ;
- `$4D150` : `move.w $174(A5),$100(A5)` au début de l'écran VS.

Le correctif (appliqué à ma copie seulement, `--selection`) remplace `move.w D0,$174(A5) ; clr.b $110(A5)` en
`$4A428` (8 o) par `jsr SEL.l ; nop` :
```
SEL:  move.l d1,-(sp)
      cmpi.w #$24,d0 ; bcc .garde          ; seuls les 18 décors de persos $00-$22 ont un homologue SFA2
      d1 = SEL_TAB[d0/2] ; $FF -> .garde   ; table perso (décor SFA3) -> décor SFA2 ($50 + 2k)
      SEL_MODE : 0 -> .garde (toujours SFA3) ; 1 -> .sfa2 (toujours SFA2) ;
                 2 -> jsr $11514 (hasard du jeu), bit 0 : .sfa2 ou .garde
.sfa2: d0 = SEL_TAB[d0/2]
.garde: move.w d0,$174(a5) ; clr.b $110(a5) ; move.l (sp)+,d1 ; rts
```
- La table compte 18 octets par perso, sans mélange : Ryu → `$50`, Ken → `$52`… Aujourd'hui, seul Ryu a son
  décor SFA2.
- Les combats spéciaux gardent leurs décors SFA3, puisque leurs cas passent après le crochet.
- **Option** : l'octet `SEL_MODE` est en ROM dans cet essai. En production, il serait lu dans un DIP du cœur ou du
  fork (comme « PS2 music ») ou dans une option du menu Anthology. Le reste ne change pas.
- Le hasard utilise la routine du jeu (`$11514`), ce qui avance la suite pseudo-aléatoire d'un tirage par combat
  (comme tout appel du jeu).

Validation : en mode « toujours SFA2 », §3.2. Le mode « tirage » (`import/essai_alea`) est donné au §8.

## 5. Musique

- Le choix de la musique de combat finit en `$2219E` (`moveq #0,d2 ; moveq #0,d3 ; bra $21F9C`, `D1` = code).
  Il est remplacé par `jmp TM_MUS.l ; nop`.
- TM_MUS : si `$100 ≥ $50`, `D1 = $0050 + code SFA2` du décor (table SFA2 `$154EE`, 18 codes ; Ryu `01` →
  `$0051`).
- Le lecteur de flux du fork (`HSFA_YDATA` = ISO, `HSFA_FLUX_TABLE` = `agent_flux/hsfa_flux_table.txt`, mode 1)
  joue `$0051` en flux Y70 ; le Z80 reçoit `FF05`.
- Essai (`mame/out/musique.flux`, `mame/out/musique.wav`) : `0051 -> flux Y70 vol 73`. La référence Y70 décodée
  par `test_flux` est retrouvée dans le WAV avec un départ constant (46,8 s, environ l'image 2 790) et un gain de
  **0,261** (= 0,26 du lecteur) ; corrélation 0,60-0,88 malgré les bruitages du combat.
- Extrait : `captures/musique_ryu_sfa2_Y70_decor50.wav`.
- Sans `Y_DATA`, `$0051` est inconnu du Z80 : la musique du perso précédent continue (comportement du §118).

## 6. Coût estimé pour les 17 autres décors

**Automatique** avec `construit.py` (à généraliser à N décors en une passe) : tuiles, blocs, listes, palettes,
CPS-B, musique, entrées des tables. Environ 1 h par décor, contrôle compris (`compare_plans.py` sur un relevé
d'export).

Capacités, mesurées sur l'union des 18 décors de persos :
- blocs distincts : s1 49, s2 86, s3 86 ; numéros libres après relogement : 161 / 109 / 90 ;
- tuiles : scroll1 9 138 (places 40 960, OK) ; scroll3 1 677 (OK) ;
- **scroll2 : 9 358 pour 5 632 places** (`$8A00-$BFFF`, avant la zone 32×32 de `hsfa_plans`). Il faut déplacer la
  base de scroll3 (`HSFA_PLANS` 3ᵉ valeur, par exemple `$3E0`) pour libérer les codes 16×16 `$C000-$FFFF`. Dans
  FBNeo, la région de 64 Mo devra passer à 96/128 Mo, ou il faudra regrouper les tuiles avec dédoublonnage par
  retournement ;
- palettes : 3 Ko par décor ; code : environ 80 o de gestionnaires par décor.

**Semi-manuel** : gestionnaires de plans.
- Il faut lire le gestionnaire SFA2 (init X/Y + rapport X/Y).
- Ce sont des formules simples (1/8, 1/4, 1/2, 3/4, 7/8, 15/16, 1, 5/4, tables) ; une génération automatique depuis
  la table des routines de SFA2 est possible.
- Environ ½ h par décor, plus si scroll2 n'est pas la caméra standard.
- Effets par décor : 9 décors SFA2 sur 18 ont un effet autre que `rts` (`$1D842`) ; ce sont des rowscroll ou des
  animations, à traduire : ½ à 1 j chacun.
- Animations de tuiles et de palettes : à mesurer par l'export.

**Manuel** : objets sprites. 4 à 15 objets par décor, routines de type `$xx00` propres à SFA2 (`aiguillages.txt`).
De ½ j (Ryu, Ken) à 2 j (Chun-Li et ses cyclistes, Zangief et son public).

**Total** : environ ½ à 1 j par décor plans compris, plus 0,5-2 j d'objets ; soit environ 3 à 5 semaines pour les
17 avec objets, ou environ 2 jours sans objets (décors « nus » comme cet essai).

## 7. Reproduire

```
cd <workspace>/work/decors_sfa2
../decors_ws/venv/bin/python py/construit.py --sortie import/essai                      # décor $50 seul
../decors_ws/venv/bin/python py/construit.py --sortie import/essai_sel --selection sfa2 --table-essai
E=$PWD/import/essai; NOM=essai1 ROMS=$E/roms EXT=$E/ext GFX=$E/hsfa_plans_sfa2.bin OUT=$PWD/mame/out/essai1 DEC=50 \
  mame/lance.sh lua/essai.lua                                                          # + HSFA_YDATA=... pour la musique
ECRAN=1 ../decors_ws/venv/bin/python py/compare_plans.py mame/out/essai1_frm.bin $E/hsfa_plans_sfa2.bin \
  export/rec/00/full.rec export/gfx/gfx_region.bin captures/cmp1                       # (sans ECRAN : tilemaps)
NOM=partie1 ROMS=... EXT=... GFX=... OUT=... PERSO=00 NF=40000 SNAPP=600 mame/lance.sh lua/partie.lua
```

| fichier | rôle |
|---|---|
| `py/sfa2.py` | lecture des données de décor de sfa2u |
| `py/construit.py` | import (tuiles, bibliothèques, tables, trampolines, gestionnaires, musique, sélection) |
| `py/compare_plans.py` | contrôle pixel fork vs sfa2u |
| `py/sites100.py` | recensement des accès à `$100(A5)` → `format/sites100_tr.txt` |
| `py/tables_saut.py` | lecture des tables de sauts en ligne |
| `lua/essai.lua` | essai de combat sur un décor forcé |
| `lua/partie.lua` | partie Arcade avec journaux |
| `lua/sonde*.lua` | sondes des lectures et écritures de `$FF8100` |
| `lua/trace.lua` | trace du débogueur |
| `mame/lance.sh` | lanceur du fork |
| `import/*/rapport.json` | tables relogées, symboles, 58 correctifs (avant/après) |
| `captures/` | captures et extraits |
| `export/` | export (`EXPORT.md`) |

## 8. Partie en mode tirage

Construction `import/essai_alea` (`--selection alea --table-essai`), Ryu, 40 000 images (`mame/out/partie2*`) :
- **20 manches, FIN, aucune exception** ;
- décors tirés : `$08`, `$0E`, **`$50`, `$50`, `$50`**, `$04`, `$1C`, **`$50`**, puis Bison `$14` (cas spécial
  conservé) ;
- 4 combats sur 8 sur le décor SFA2, chacun avec la commande `$0051` (musique SFA2) ; les combats SFA3 ont leur
  musique habituelle.

Garde des lecteurs de `$FF8100` ≥ `$50` :
- une seule alerte, PC `$11DB2` (file des commandes son). C'est un faux positif : c'est la lecture faite par la prise
  d'écriture son de `partie.lua` elle-même ;
- aucun lecteur non traité dans le programme.
