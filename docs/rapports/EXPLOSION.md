# Table d'animations de décor `$2E50A0` (SFA3 arcade) : laquelle est l'explosion ?

Session agent_explosion, 2026-10-10. ROM : `work/cps2/sfa3ud_prog.bin` (programme déchiffré ; la table `$2E50A0`
et les frames sont identiques dans `sfa3_prog.bin`, mais la table de positions `$229AE`, lue en relatif au PC,
n'est lisible que dans la version déchiffrée). Tuiles : `work/cps2/sfa3_tiles_raw.npy`.

## Réponse : c'est l'animation n° 5

**L'animation n° 5 (pas en `$2E565C`) est l'explosion.** Ses 6 frames sont **identiques au pixel près** aux frames
300-305 d'`efct.pac` (PSP), avec la même ancre (décalage 0, 0). L'animation n° 0 n'a rien à voir (0 à 3 % de
pixels communs).

| pas | anim 0 : adresse du pas → frame (type) | anim 5 : adresse du pas → frame (type) | efct.pac |
|---|---|---|---|
| 0 | `$2E52D0` → `$2E6894` (**$12**, vide) | `$2E565C` → `$2E8ECA` (6, 4 objets, T=16) | 300 |
| 1 | `$2E52D8` → `$2E6B72` (6, 1 objet, T=6) | `$2E5664` → `$2E8EEC` (6, 8 objets, T=24) | 301 |
| 2 | `$2E52E0` → `$2E6B82` (6) | `$2E566C` → `$2E8F26` (6, 5 objets, T=32) | 302 |
| 3 | `$2E52E8` → `$2E6B92` (6) | `$2E5674` → `$2E8F4E` (6, 7 objets, T=31) | 303 |
| 4 | `$2E52F0` → `$2E6BA2` (6) | `$2E567C` → `$2E8F82` (6, 4 objets, T=9) | 304 |
| 5 | `$2E52F8` → `$2E6BB2` (6, 3 objets) | `$2E5684` → `$2E8FA4` (6, 2 objets, T=5) | 305 |
| fin | `$2E5300` : `FF 80 0000 002E6BB2`, long en +8 = `$2E5300` | `$2E568C` : `FF 80 0000 002E8FA4`, long en +8 = `$2E568C` | — |

Décalages dans la table : mot n° 0 = `$0230`, mot n° 5 = `$05BC` (relatifs à `$2E50A0`). Durée 3 images à chaque pas.
Le pas de fin (`$FF80`) reboucle sur lui-même : la dernière frame reste affichée (255 images par tour) jusqu'à ce
que l'acteur se supprime ; il n'y a pas de bit 6 (fin `$33 = -1`) dans ces deux animations.

**Ce que montre l'anim 0** : rien pendant 3 images, puis une ellipse pleine (~48×32 px) qui se creuse en anneau et
s'éparpille en points : un éclair / une bouffée d'impact, pas une explosion à éclats.
**Anim 5** : boule de feu (~100 px) avec éclats projetés, qui grossit (pas 1-2) puis ne laisse que des débris (pas 4-5).

## Preuves

1. **Comparaison au pixel** (`comparaison.txt`, script `tools/diagnostics/explosion/compare.py`) : rendu en valeurs brutes CPS2 des deux
   animations et des frames PSP 300-305 (index PSP `i` → brut `i - 1`, convention de `convert_max.py`), recherche du
   meilleur décalage ±4 px :
   - anim 5, pas 0-5 vs 300-305 : **100,0 % chacun, décalage (0, 0)**, nombres de pixels égaux (1567, 2123, 2142, 834,
     182, 76) ;
   - anim 0 : 0,0 à 2,6 %.
2. **Planches** (3 lignes : anim 0, anim 5, efct 300-305 ; 160×160 px par case, agrandi ×2, origine de l'acteur au
   point (80, 100) de chaque case) :
   - `anim0_anim5_efct300_feu.png` (fausses couleurs) ;
   - `anim0_anim5_efct300_gris.png` (valeurs brutes en gris).
   Ce ne sont pas les vraies couleurs : la palette `$16` des objets est remplacée à l'exécution par `$D(acteur)` quand
   `$C(acteur)` ≠ 0 (voir le format type 6 plus bas).
3. **Code 68K arcade** (`work/carto_persos/hors_combat/outils/_cache/sfa3_lin.txt`) :
   - `$A0814` : `MOVEQ #5,D0 ; LEA $2E50A0,A0 ; JSR $1B6E0` : un acteur placé d'après une table de positions
     (`$A0826`, index `$16(A5)`), `$E = 8`, `$18 = $E000`, `$1A = $6000`, palette forcée par `$C/$D` ;
   - table sous-type → animation `$80842` (code `$8082A` : `$3(A6) / 2`) et sa copie `$AAAE6` (code `$AAACE` :
     `$70(A6) / 2`) : `01 02 03 05 05 05 0A 24 10 15 16 1E 41 00 04 09 43 06 07 08 1F` ⟹ sous-types `$06`, `$08`, `$0A`
     → anim 5 ; sous-type `$1A` → anim 0.
   - `$97F20` : `MOVEQ #0` puis `MOVE.B $31(A6),D0` (index variable, pas une référence fixe à l'anim 0).

## Formats décodés (routine d'affichage `$20F6A`, saut par la table `$20F84` indexée par le type)

### Pas d'animation (8 octets, routines `$1B6B6` / `$1B6E0`)
```
+0 u8  durée (images)            +1 u8 drapeaux : 0 = pas suivant (+8) ; bit 7 = saut au u32 situé en +8 ;
                                                  bit 6 = fin (st.b $33(acteur))
+2 u16 (0 ici ; copié avec les 2 octets précédents dans $32-$35 de l'acteur)
+4 u32 pointeur de frame
```
Sélection : `$1B6E0` : `A0 = table + table[2 × n]` (mots relatifs), `$1C(acteur) = A0`, `$32.L = (A0)`.

### Frame type `$12` (gestionnaire `$2150C` = `RTS`)
Un seul mot `$0012` : rien n'est affiché. `$2E6894` est une frame vide partagée (les octets qui suivent appartiennent
à d'autres frames, rangées au mot près).

### Frame type 6 (gestionnaire `$2113A`)
```
+0  u16 6
+2  u16 T     = nombre total de tuiles 16×16 (budget : CMP T,D7 ; BCS rien ; SUB T,D7)
+4  u16 n − 1
+6  s16 dx0   +8 s16 dy0      (niées selon les bits miroir de $B(acteur))
+10 n × { u16 idx, u16 code, u16 attr }
```
- Position de l'objet = `table[$229AE + idx]` (s16 dx, s16 dy) + (dx0, dy0) + origine de l'acteur. La table `$229AE`
  est une grille de 16 px : entrée `k = idx / 4` → `(16 × (k mod 16), 16 × (k div 16))`. Pas de fichier de positions
  séparé (contrairement au type 2).
- X = (… ) & `$3FF` | `$18(acteur)` ; Y = (… ) & `$3FF` | `$1A(acteur)` ; ces acteurs mettent `$1A = $6000`, donc
  code CPS2 effectif = `code + ((Y & $6000) << 3)` = **`$30000 + code`** (banque des effets).
- attr = attributs CPS2 : bits 0-4 palette (`$16` ici), bit 5 miroir H, bit 6 miroir V, bits 8-11 largeur − 1,
  bits 12-15 hauteur − 1 (en tuiles). Le miroir de l'acteur (`$B`) est appliqué par `EOR` sur les bits 5-6 et corrige
  la position (largeur/hauteur du bloc). Si `$C(acteur)` ≠ 0 : palette = `$D(acteur)` (ou `$D + palette` si `$C` < 0).
- Entrée de la liste d'objets écrite : X, Y, code, attr. Bloc nx × ny : tuile `(code & ~$F) + ((code + i) & $F) + $10 × j`.

Objets de l'anim 5 (x, y relatifs à l'origine, code effectif, attr) — pas 0 : `(-40,-24,$3068A,$0016)`,
`(-24,-24,$306C7,$2316)`, `(24,-40,$306D2,$0116)`, `(40,-24,$3068F,$0016)` ; les autres sont listés par
`tools/diagnostics/explosion/rendu_anim.py` (fonction `objets`).

## Fichiers
- `tools/diagnostics/explosion/rendu_anim.py` : lecture des pas et rendu des frames type 6 depuis la ROM arcade ;
- `tools/diagnostics/explosion/rendu_efct.py` : rendu des frames d'`efct.pac` (modules de `github/tools/max`, lecture seule ;
  `efct.pac` = 2 entrées : [0] frames (581), [1] tuiles (12 164)) ;
- `tools/diagnostics/explosion/compare.py` → `comparaison.txt` ; `tools/diagnostics/explosion/planche.py` → les deux PNG.
Lancement : `cd <workspace> && source env_max.sh && venv/bin/python work/agent_explosion/scripts/planche.py`.
Aucun MAME lancé, rien modifié hors de `work/agent_explosion/`.
