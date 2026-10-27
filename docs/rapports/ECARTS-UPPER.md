# Écarts Upper / arcade SFA3 : classement des 509 (et 629) écarts, champs déplacés, tables étendues

Session « écarts Upper », 2026-10-07. Lecture seule de l'existant ; tout ce qui est produit est dans
`<workspace>/work/agent_upper_ecarts/`. Pas de MAME lancé.

**Conventions**
- *arcade* = adresse 68K dans la ROM SFA3 (`sfa3ud_prog.bin`, celle de l'alignement) ;
- *va* = adresse MIPS d'Upper, **décalage fichier** dans `ro5_usa_prog68k.bin` (ce que prend `show.py`) ; exéc. = fichier + `0x1F0000` ;
- décalages d'octets de structure donnés **en numérotation arcade** (= celle du MIPS) ; l'image traduite et `carte_image.txt`
  affichent le XOR 1 (`$102` arcade = `$0103` dans la traduction) ;
- `$xxxx(A5)` avec A5 = `$FF8000` ; `-$5C42(A5)` = `$FF23BE`.
- Familles : **(a)** changement de jeu d'Upper ; **(b)** champ / variable déplacé ou supprimé ; **(c)** extension du
  roster et des tables (32 → 40 persos) ; **(d)** portage, recompilateur, artefact d'alignement (rien à voir avec Upper) ;
  **(e)** inexpliqué.

---

## 0. En bref

1. **Les adresses de `upper_ecarts_vs_arcade.json` ne sont plus valables** : l'image `sfa3ud` de `mame_ro5` a été reconstruite
   à 12 h 56 (après l'alignement de 10 h 52), avec un traducteur différent (image de 545 700 → 660 662 o). J'ai **réaligné** Upper
   sur l'arcade sur l'image actuelle (instantané + `carte_image.txt` du même build, qui donne la va MIPS de chaque instruction) :
   83 709 instructions alignées (46,3 %), même table de relocalisation A5. **503 des 509 écarts** se retrouvent tels quels ; les 6
   autres sont désormais alignés (bruit). Le réalignement ajoute 126 écarts. Total actuel : **629 écarts hors branchements, 434 sites**.
2. **Les « 509 » excluaient à tort `BTST/BSET/BCLR/BCHG`** (filtre sur la 1re lettre `b`). Ces 42 instructions sont parmi les plus
   intéressantes (masques par perso). L'exemple `$AC(A5)` du rapport de couverture n'est pas un décalage A5 : c'est un bloc déplacé
   par le recompilateur (`CMPI.B #3,$AC(A5)` existe deux instructions plus loin).
3. Répartition des 509 (503 retrouvés + 6) : **(a) 250, (b) 12, (c) 73, (d) 172, (e) 2**. Sur les 629 : (a) 309, (b) 15,
   (c) 109, (d) 194, (e) 2. Par site (434) : (a) 183, (b) 15, (c) 81, (d) 155, (e) 2.
4. **(a) n'est pas de l'équilibrage chiffré** : je n'ai trouvé aucune valeur de dégâts ou de durée changée dans le code commun. Ces
   valeurs sont dans les **données** par coup, que l'alignement de code ne voit pas. Les changements de code d'Upper portent sur :
   - les **palettes** (le champ `$128` porte l'index complet de palette, plus `(ism+1)×2+couleur`, 129 écarts avec les couleurs) ;
   - la **sélection** (couleur par bouton, Juli/Juni, codes secrets) et les **modes console** (`$C200(A5)`) ;
   - des **renumérotations d'animations** dans le code de 4 persos (Adon +3, Guy −3, R.Mika −1, Zangief −$E) ;
   - quelques suppressions (bonus d'IA par perso `$32DDC`, champ `$32F`) et un cas spécial nouveau (intro de Charlie contre Guile).
5. **(c) est le plus utile pour ajouter 4 persos.** Sont confirmés dans le code :
   - **masques 32 bits remplacés** (voix, rival, dialogues, boss, Gen, `$10004040`) ;
   - **masque « adversaires battus » `$140` élargi à 48 bits** (`$140.l` + `$144.w`) ;
   - **pas de table +$40 → +$50**, **+$20 → +$28** ;
   - **tableaux de records en RAM** de 29 à 35 entrées : c'est eux qui décalent les variables A5 de `$FF2Exx` à `$FF41A7` ;
   - **pseudo-ID placés juste après le roster**, passés de `$20…` à `$28…`.
6. **Piège majeur pour les ID `$28/$29`** : Upper utilise déjà `$28-$2C` comme **pseudo-ID** dans la table de musique, `$28/$29`
   pour les variantes de Vega (table `$832A6`) et de Chun-Li dans les tables ID×8. En plus, **les codes ≥ `$26` de la grille de
   sélection sont des codes spéciaux** (`CMPI.B #$26`). Ajouter des persos en `$26-$29` impose donc de déplacer ces pseudo-ID et
   de relever cette borne, en plus d'agrandir les tables à 42.

---

## 1. Méthode

| étape | script | sortie |
|---|---|---|
| contrôle : le traducteur actuel ne reproduit plus `ro5_traduit.bin` (660 662 o contre 545 700) | `carte_ro5.py` | — |
| réalignement Upper ↔ arcade sur l'image actuelle (même méthode que `upper_align.py`) | `realigne.py <dossier_instantané>` | `realign.pkl` |
| écarts : instruction arcade alignée dans SFA3, pas dans Upper, voisines alignées à ≤ 6 instructions, trou Upper ≤ `$80` o (règle de `upper_trous.py`) ; trou arcade, trou Upper avec va, forme SFA3 | `ecarts.py` | `ecarts.pkl` (2 312 écarts, 629 hors branchements) |
| appariement de l'instruction manquante avec une instruction Upper non alignée du trou, même gabarit ; nature de l'écart (immédiat, déplacement, A5) | `classe.py` | `classe.pkl` |
| familles : décisions manuelles par plage (`manuel.py`, 100 plages vérifiées à la main) puis règles (relocalisation A5 = SFA3, données en ligne, bloc déplacé, code de perso) | `famille.py` | **`familles.json`** (un enregistrement par écart : arcade, instruction, va Upper, homologue, forme SFA3, trou Upper, famille, étiquette), `familles.txt` |
| outils de lecture | `site.py ADR` (contexte arcade + Upper avec va), `ctx.py`, `s3ctx.py` (forme SFA3), `lea_upper.py VA1 VA2` (données référencées par Upper), `liste_sites.py` → `sites.txt`, `voir.py`, `persos_arcade.py` (bornes du code par perso, tables `$DCB12/$DD192/$DD292/$DF412`) | |

L'instantané des ROM et de `carte_image.txt` est dans le scratchpad de la session. `realign.pkl` contient l'image désassemblée et
la carte : les scripts suivants n'ont pas besoin des ROM.

**Attention aux données arcade** : `sfa3_prog.bin` a ses données brouillées par endroits (opcodes déchiffrés partout). Par
exemple, la table `$832A6` y est illisible. Pour lire une table arcade, utiliser **`sfa3ud_prog.bin`**.

---

## 2. Familles : effectifs

| famille | 509 | 629 | sites | étiquettes principales (écarts, sur 629) |
|---|---|---|---|---|
| (a) jeu d'Upper | 250 | 309 | 183 | palettes et couleurs 129 · renumérotations d'animations 62 · sélection 21 · modes console 3 · autres 94 (dont code de persos remanié, suppressions, ajouts) |
| (b) champs / variables | 12 | 15 | 15 | `$145→$121` 3 · `$32F` supprimé 6 · Balrog `$37F→$1FF` 2 · table RAM `$FF8FA2→$FF8E4C` 4 · R.Mika `$35→$33` 1 |
| (c) roster / tables | 73 | 109 | 81 | masques 32 bits 29 · pas de table et tables ID×8 23 · records 20 · masque `$140` 18 · pseudo-ID 10 · EX Balrog 4 · grille 3 · tableau RAM 2 |
| (d) portage / recompilateur | 172 | 194 | 155 | tables en ligne et désynchronisation 99 · blocs déplacés 75 · relocalisation A5 de SFA3 non apprise 17 · idiomes du traducteur 3 |
| (e) inexpliqué | 2 | 2 | 2 | `$841AC`, `$A14E2` |

Les 509 comptent 6 écarts désormais alignés (`$431C`, `$365A2/A8/AC`, `$64A58/6A`), tous en (d). Les 42 opérations de bit
exclues à tort se répartissent ainsi : 21 (c), 17 (a), 3 (d), plus 1 désormais alignée.

---

## 3. (a) Changements de jeu d'Upper

Upper = SFA3 + Guile `$20`, Fei-Long `$21`, Dee Jay `$22`, T.Hawk `$23`, Shin Akuma `$24`, (EX)Balrog `$25`, remplissage `$26/$27`
(confirmé par `CARTE-ro5.md` et les noms en ROM). Evil Ryu `$17`, Balrog `$15`, Juli `$1E` et Juni `$1F` existent déjà dans
l'arcade, mais Upper les rend jouables. Eagle, Maki, Yun et Ingrid sont dans MAX, pas dans Upper.

| sous-famille | exemple : arcade → Upper (va) | interprétation |
|---|---|---|
| **index de palette, couleurs** (129) | `$303FC` `MOVE.B $132(A6),D0 ; ADDQ.B #1 ; ADD.W D0,D0 ; ADD.B $128(A6),D0` → va `0x116FBC` `MOVE.B $128(A6),D0` ; idem `$1F95C`, `$5FB56`, `$96DEA`, `$872C0` (`ANDI #1 → #7`), objets `$947CE` (`$A`→`$3C`) | **`$128` ne contient plus la couleur 0/1 mais l'index complet**, calculé une fois : `$9250-$940E` → va `0x262C78`, `$128 := ($132+1)×2` (+ bouton). Changement de sémantique de champ. Du code de perso repris de l'arcade (ou de MAX) qui calcule `(ism+1)×2+couleur` donnera de mauvaises palettes. |
| **sélection** | `$1E7FE` `MOVEQ #1,D0` (couleur 0/1 selon l'adversaire) → va `0x25649C` `MOVEQ #4,D0 ; BTST #$A,D1…` (couleur 0-5 selon le bouton) ; `$1E9EA` `MOVEQ #$1F/#$1E` (Juli/Juni par boutons) → logique nouvelle (minuteur `$258`, `$378`, `$122`) ; `$802C-$80AE` combinaisons `$11A & $7700` → tests `$C200(A5)` | écran de sélection réécrit (couleurs par bouton, persos cachés) |
| **renumérotation d'animations** (62) | Adon `$3EC5C` `MOVEQ #$5B,D0` → va `0x310518` `#$5E` (+3) ; Guy `$42C14` `#$5E` → `#$5B` (−3) ; R.Mika `$6312A` `MOVEQ #$37,D0 ; JSR $80B70` → `#$36` (−1) ; Zangief `$58584` `ADDI.W #$C5` → `#$B7` (−$E) | les n° d'animation passés au moteur sont décalés d'une constante : les tables d'animation de ces 4 persos ont été réordonnées (entrées ajoutées ou retirées) |
| **modes console** | `$1F440 TST.B $168(A5)`, `$2B9A8 CMPI.W #6,$138(A5)` → `CMPI.B #1/#4/#7,$C200(A5)` (va `0x25C7E0`, `0x245448`) | tests du mode de jeu console (curseur `$FF4200`) |
| suppressions | `$32866` `MOVE.B $102(A6) … LEA $32DDC(PC) ; ADD.W …,$21A(A6)` (bonus d'IA par perso) : absent (va `0x84F0C`) ; `$2ABFC ADDI.W #$100 ; CMPI.W #$200` (seule la variante `±$A0/$140`, déjà présente dans l'Anthology SFA3, reste) ; `$2D838…` `BTST #4,D6` ×6 ; `$BA16` choix d'un perso caché | — |
| ajouts | `$3BBB0` (Charlie) : Upper insère `CMPI.B #$20,$102(A4)` (adversaire = **Guile**) → réplique `#$33` (va `0x2FCEC4`) ; `$9F9E` : nouvel octet joueur `$149` + appels au chargeur natif `0x4113A0` ; `$2A356…` `BSR 0x51BCC` inséré | **comparaisons d'ID en dur ajoutées pour les nouveaux persos** : à prévoir pour `$26-$29` si l'on veut des intros spéciales |
| divers | `$8DCA` `$15E(A5) := (aléa&3)×28` → `(aléa&7)×10` ; `$9FEE` `$14C(A5)` → constante 9 ; `$69C20` (Vega) tests de l'adversaire `$0D/$07` → masques par décor `#$3F60BDB3`/`#$8F` ; `$6BCD4` Juli `$AA := $0E → $22` ; `$B3924 #$2B60 → #$2B80` ; `$8BC8A` seuil `#7 → #4` sur `$FFEEB9` | — |

---

## 4. (b) Champs et variables déplacés : voir la liste du §8.

Exemples : arcade `$7DF4 MOVE.B D0,$145(A6)` ↔ va `0x134BAC` `sb v1,289(v0)` (= `$121`), traduit `MOVE.B D0,$0120(A6)`.
Balrog `$59FCE MOVE.B D1,$37F(A6)` ↔ va `0x3B0D18` `$1FF`. Table RAM `$B7E4 LEA -$705E(A5),A2` (`$FF8FA2`) ↔ va `0x24EFA0`
`LEA -$71B4(A5)` (`$FF8E4C`).

---

## 5. (c) Extension du roster et des tables

| sous-famille | exemple | interprétation |
|---|---|---|
| **masque 32 bits par perso → sous-programme ou table** (29) | `$363C MOVE.L #$03210D40,D0 ; MOVE.B $102(A6),D2 ; BTST D2,D0` → va `0x138C34` `JSR 0x138CD0` ; `$D324 #$2640F310` → `JSR 0x249740` ; `$80C82 #$10004040` → `MOVE.B T_615380(PC,D0.W)` (fichier `0x425380`) ; `$848AE #$C0200400` → table (+`$28` pour la 2e série) ; `$2B7B8 #$000A0000` → `CMPI.B #$11` / `#$13` | un long ne code que 32 ID |
| **masque « adversaires battus » `$140`** (18) | `$9D86 BSET D0,D2` → va `0x269F14` `JSR 0x251AC0` ; `$B7D8 BTST D1,D2` → `JSR 0x251CC0` ; `$8E764 MOVE.L $140(A0),D6` → va `0x19BF54` `MOVE.L $140(A0),D2 ; MOVE.W $144(A0),D3` | masque élargi à **48 bits** (`$140.l` + `$144.w`). Il couvre `$00-$2F`, donc `$28/$29` y tiennent. |
| **pas de table** (23 avec les tables ID×8) | M.Bison `$47B3E LEA $40(A0),A0` → va `0x3DDFD8` `LEA $50(A0)` (table `$48DC0` 3×32 mots → fichier `0x433E50` 3×40) ; `$8E790 ADDI.W #$40,D1` → `#$50` ; `$BC20` +`$40` → +`$50` ; `$8B7DE ADDI.W #$20` → `#$28` ; `$8EA18 #$B0 → #$D0`, `#$B8 → #$120` ; `$B9450…` `$40 → $50` | séries de 32 entrées → 40 : **à repasser à 42 (`$54`, `$2A`)** pour `$28/$29` |
| **records en RAM** (20) | `$8592 LEA $1D0(A3),A3` → va `0x93B30` `LEA $230(A3)` ; `$85A0 MOVEQ #$1B,D1` → `#$21` ; `$8536 LEA $570(A0)` → `$690` ; `$25A6C MOVEQ #$1C,D4` → `#$22` | 6 tableaux × 29 → 35 entrées × 16 o à `$FF23BE`. Upper passe l'ID par une table ID → rang (`T_60EBB0`, fichier `0x41EBB0`). C'est l'origine du décalage **+$240** des variables A5 suivantes. |
| **pseudo-ID après le roster** (10 + 4 dans les tables ID×8) | `$3A5A MOVEQ #$20,D0` → va `0x13A12C` `#$28` (… `$24 → $2C`) ; Vega `$68B76/$82CA8 #$20/#$21 → #$28/#$29` ; Chun-Li `$B95F6 MOVE.B #$20 → #$28`, `$B95B6 #$21 → #$29` | voir §9 : **collision avec les ID `$28/$29`** |
| **grille de sélection** (3) | `$1E6EE BTST #5,D0 ; ANDI.B #$23,D0` → va `0x255B68` `ANDI.B #$3F,D0 ; CMPI.B #$26,D0 ; BLT` | **codes de case ≥ `$26` = persos spéciaux** résolus par `JSR 0x2567F0` |
| tableau RAM 25 → 37 | `$85CE8 MOVEQ #$18,D2 ; LEA -$4A52(A5)` → va `0x186AD8` `MOVEQ #$24 ; LEA -$4C8C(A5)` | 25 → 37 couples (`$25CC`,`$1116`), déplacé de `$FFB5AE` à `$FFB374` |
| variante EX Balrog | `$59A20 MOVEQ #$40,D0` → va `0x3AE5C8` `MOVE.B $1FE(A6),D0 ; MOVE.B T_…(PC,D0.W)` | n° d'animation choisis par variante (`$1FE`) : le moyen d'Upper pour faire un perso `$25` avec le code de `$15` |
| masque d'ID | `$7830 ANDI.W #$1F,D0` (palettes, table `$34CDD4`) → va `0x5F648` `#$3F` | — |

---

## 6. (d) Portage, recompilateur, alignement

| sous-famille | exemple | interprétation |
|---|---|---|
| tables en ligne / désynchronisation (99) | `$3A432 ADDQ.B #2,$7(A6)` derrière un `JMP (PC,D1.W)` : dans Upper, la table de sauts (décalages relatifs) a d'autres valeurs, et le désassemblage du code qui suit se décale | bruit (sauf si la table a plus d'entrées : nombre donné par la carte, « [table de N entrees] ») |
| blocs déplacés (75) | `$20324 CMPI.B #3,$AC(A5)` à va `0x25124`, deux instructions plus loin ; `$A7C50 ADDQ.B #2,$5(A6)` : le recompilateur inverse le saut (`BGT` → `BLE` + `BSR`) | nouvelle version du recompilateur (style « drapeaux complets » d'Upper/Hyper) |
| relocalisation A5 de SFA3 non apprise (17) | `$669E MOVE.L D0,-$7148(A5)` → va `0x58A34` `-$739C` : `$8C64+$254 = $8EB8`, même intervalle que SFA3 (`$8C24-$8C70 +$254`) ; `$ACB0 -$6026 → -$615C` (`+$136`, comme SFA3 `$9EA4`) | trous dans la table A5 apprise pour Upper : à **ajouter** à la table d'Upper (`$8C61-$8C79 +$254`, `$9EA4 +$136`) |
| idiomes du traducteur (3, plus 6 lectures de tables PC classées avec les tables en ligne) | `$ADFF0 MOVE.L $30C(A5),D2 ; SUB.L…` → `SWAP/MOVEM` (« long échangé ») ; `$4D9C MOVE.B $60(PC,D0.W),D1` → `MOVEM/MOVE SR` | forme de la traduction, pas d'Upper |
| demi-mots de longs | `$1C8(A5) → $1CA(A5)`, `$10/$14(A6) → $12/$16` (déjà dans SFA3 traduit) | ordre des mots du portage |

---

## 7. (e) Inexpliqués (2)

`$841AC MOVE.W A6,$36(A4)` (va `0x180164`) et `$A14E2 LSL.W #2,D0` (va `0x1D1EFC`) : rien d'équivalent dans le trou Upper.
Probablement des blocs déplacés au-delà de la fenêtre. À lire avec `site.py`.

---

## 8. LISTE — DÉPLACEMENTS DE CHAMPS

### 8.1 Structure joueur / objet (`A6`, `A4` ; numérotation arcade)

| champ arcade | Upper | preuve | remarque |
|---|---|---|---|
| `$145` (octet) | **`$121`** | `$7DF4`, `$817C`, `$8EC0` (va `0x134BAC`, `0x136520`, `0x260E00`) ; `CARTE-ro5` §5 : 3/3 | `$145` n'existe plus dans Upper |
| `$32F` (octet) | **supprimé** | `$2E3E0`, `$2E5D4`, `$2E5F0`, `$2E614`, `$2E714` : l'écriture disparaît (va `0x15CD5C…0x15F52C`) | `CARTE-ro5` : `$32F`, `$331`, `$37F` disparus |
| `$37F` (Balrog) | **`$1FF`** | `$59FCE`, `$5A01A` (va `0x3B0D18`, `0x3B0E44`) | champ propre au code de Balrog, partagé avec EX Balrog `$25` |
| `$35` (R.Mika) | `$33` ? | `$64766 TST.B $35(A6)` ↔ va `0x3AB634 TST.B $33(A6)` | un seul site, à confirmer |
| `$128` couleur | **sémantique changée** | §3 | arcade : couleur 0/1 (palette = `(ism+1)×2+$128`) ; Upper : index complet de palette |
| `$140` (long) | **`$140.l` + `$144.w`** | `$8E764` → va `0x19BF54` | masque d'adversaires battus sur 48 bits ; `$144` ne doit pas servir à autre chose |
| nouveaux | `$149` (octet, va `0x26B60C`), `$1FE` (variante Balrog), `$15F` (`$80BC`), `$10B/$10F` (`$817C`) | | `CARTE-ro5` : nouveaux `$121`, `$144`, `$1D5`, `$1D7`, `$269` |
| `$10/$14` (mots) | `$12/$16` | `$1E704` | **portage, pas Upper** (demi-mot de long, idem SFA3) |

### 8.2 Variables globales A5 (RAM `$FFxxxx`)

| arcade | Upper | origine |
|---|---|---|
| `$FF23BE` records 6 × 29 × 16 o (`$AE0`) | `$FF23BE` 6 × 35 × 16 o (`$D20`, +`$240`) | §5 ; **cause du décalage +$240** de la zone `$FF2F84–$FF3124` |
| `$FF2F84–$FF3124` | +`$240` | `CARTE-ro5` §5 (vote ro3 → ro5) |
| `$FF31D8–$FF3BE8` | +`$270` par rapport à SFA3 | `CARTE-ro5` ; confirmé par la relocation apprise ici : déplacements Upper `$B466-$B4E6` = arcade − `$208`, `$B980-$BA12` = arcade − `$204`, contre − `$474`/− `$472` dans SFA3 (soit Upper = SFA3 + `$26C`/`$26E`) |
| `$FF3E48` (`$BE48`) | `$C0BC` (+`$274`) | `CARTE-ro5` |
| `$FF3F30–$FF418E` | +`$200` (`$C000→$C200`, `$C010→$C210`…) | `CARTE-ro5` |
| `$FF4190–$FF41A7` | +`$202` | `CARTE-ro5` |
| `$FF8F82` liste des adversaires du parcours (`LEA -$707E(A5)`) | **`$FFC0C0`** (`LEA -$3F40(A5)`, va `0x19BF90`) | relocation `$C0C0 −$313E` ; déplacée en fin de zone, probablement pour être agrandie |
| `$FF8FA2` ism des CPU par étape | **`$FF8E4C`** (`-$71B4`) | `$B7E4`, `$B9CC`, `$BAB8`, `$BB16`. Occupe l'ancienne place de `$FF8F82` dans le portage (`$8F82−$136`) |
| `$FFB5AE` 25 × 4 o, puis `$FFB612` 4 × 4 o | `$FFB374` 37 × 4 o, puis `$FFB408` | `$85CE8` |
| `$FF81C8` (`$1C8`) | `$1CA` | **portage** (demi-mot), pas Upper |
| `$FF8C64-$FF8C79`, `$FF9EA4` | relocation du portage identique à SFA3 | à **ajouter** à la table A5 d'Upper (`$8C61-$8C79 +$254`, `$9EA4 +$136`) |

---

## 9. LISTE — TABLES ÉTENDUES (pour les ID `$26-$29`)

Rappel des travaux précédents : `carto_persos/combat/PERSOS-COMBAT.md` (84 tables de combat) et
`carto_persos/hors_combat/PERSOS-HORS-COMBAT.md` (tables hors combat) recensent les **tables de données** passées de 32 à 40
entrées. Ce qui suit est ce que le **code** montre en plus ou confirme.

| table / structure | arcade (adresse, taille) | Upper (fichier ro5, taille) | à faire pour `$26-$29` |
|---|---|---|---|
| **musique par perso** (`MOVE.B $A(PC,D0.W),D1`, `$3AAE`) | `$3ABA`, 37 o = 32 ID + pseudo `$20-$24` (Sodom X-ism, `$15D`, étapes `$114=9/8`) | **`0x423350`, 45 o** = 40 ID + pseudo **`$28-$2C`** | 42 ID + 5 pseudo : **déplacer les pseudo en `$2A-$2E`** et changer les `MOVEQ #$28…#$2C` (va `0x13A12C`, `0x13A1A8`, `0x13A430`, `0x13A644`, `0x13A810`) |
| **variantes de Vega** (ID×4, `MOVEA.L #$832A6`) | `$832A6`, 34 × 4 o (`$20/$21` = Vega masqué / griffe) | **`0x425940`, 42 × 4 o** (`$28/$29` = Vega) | collision : `$28/$29` → `$2A/$2B` ; sites `$68B76`, `$68DAE`, `$695A2`, `$82CA8/$82CB4` (va `0x384A74`, `0x385AAC`, `0x388A08`, `0x175FCC`) |
| **tables ID×8** (`$B95FA LSL.W #3 ; LEA (A0,D0.W)`) | `$B996C`, `$B9A7C` (+`$B9B8C`) : 3 × 34 × 8 o (`$20` = Chun-Li X-ism, `$21` = autre) | **`0x76C8E0`, `0x76CA30`, `0x76CB80` : 3 × 42 × 8 o** (pas `$150`) | collision `$28/$29` ; sites `$B95B6`, `$B95C2`, `$B95F6`, `$B96C8` (va `0x12DB08`…`0x12E458`) |
| séries de mots par ID (`+$40 → +$50`) | `$B97EC` (2 × 32 mots), `$8E7A4` (`$8E794`, 2 × 32 mots), M.Bison `$48DC0` (3 × 32 mots) | `0x76C700`… (2 × 40), **`0x426D30`** (T_616D30, carte du monde), **`0x433E50`** (3 × 40) | 42 : pas `$54` (`LEA $54(A0)`, `ADDI.W #$54`) ; M.Bison : table **par adversaire** |
| séries d'octets par ID (`+$20 → +$28`) | `$8B812` (`MOVE.B $2E(PC,D0.W)`, 2 × 32) | **`0x426850`** (T_616850), 2 × 40 | `+$2A` |
| `$BC20` (ID + `$40`) | indice ID+`$40` | ID+`$50` | ID+`$54` |
| masques remplacés | `#$03210D40` voix, `#$2640F310`/`#$E76BFFFB`/`#$3F4AFB9B` rival et dialogues, `#$10004040`, `#$C0200400`, `#$000A0000` (Gen) | sous-programmes `0x138CD0`, `0x249740`/`0x249660`, tables `0x425380`, `0x426130`, `CMPI #$11/#$13` | ajouter 2 entrées aux tables d'octets ; vérifier les bornes des sous-programmes |
| masque `$140` adversaires battus | 32 bits | 48 bits (`$140.l`+`$144.w`), aides `0x251AC0` (BSET), `0x251CC0` (BTST), `0x2519A0` | rien (couvre `$00-$2F`) |
| **records** (RAM) | `$FF23BE` 6 × 29 × 16 o | 6 × 35 × 16 o ; ID → rang `0x41EBB0` | 35 + 4 rangs = 39 entrées : **+`$40`/bloc, +`$180` au total**, ce qui décale à nouveau toute la RAM A5 qui suit (`$FF2F84`…). Autre solution : donner aux nouveaux persos des rangs existants dans `0x41EBB0`. |
| tableau RAM `$FFB5AE` | 25 × 4 o | `$FFB374` 37 × 4 o | à mesurer selon son rôle (probablement les cases de l'écran de sélection) |
| **grille de sélection** | codes `$20-$23` (bit 5) = persos cachés | codes **`≥ $26`** = spéciaux (`CMPI.B #$26`, va `0x255C84`), `ANDI #$3F` | relever la borne à `$2A` et décaler les codes spéciaux (≤ `$3F`) |
| palettes par perso (`ANDI.W #$1F → #$3F`, `$34CDD4`) | 32 décalages | table `0x5351A0` (PS2 `0x7251A0`) | ajouter 2 décalages : les décalages relatifs existants augmentent (cf. `PERSOS-COMBAT` §7) |
| fin spéciale | entrée 32 | entrée 40 (`$28`) | déjà relevé par `PERSOS-HORS-COMBAT` |

À ajouter à la liste des pièges de `PERSOS-COMBAT` §7 : **Upper utilise les numéros `$28-$2C` comme pseudo-ID** dans au moins
trois familles de tables (musique, Vega, tables ID×8 de Chun-Li). Ces collisions ne se voient pas en comptant les entrées
des tables (« 40 entrées »), car les pseudo-ID sont **au-delà** de ces 40 entrées.

---

## 10. Corrections à `agent_couverture/COUVERTURE-ARCADE.md` §6

- Les adresses « Upper » (`upper_avant`, `upper_apres`, `upper_alignement.pkl`) renvoient à une image qui n'existe plus. Il faut
  utiliser `realign.pkl` et la va de `familles.json`. Les adresses arcade restent valables.
- « 509 hors branchements » : le filtre excluait `BTST/BSET/BCLR/BCHG`. Le compte exact est **551** (ancienne image) ou **629**
  (image actuelle).
- L'exemple `$AC(A5)` n'est pas une variable A5 non apprise : c'est un bloc réordonné.
- « 138 Ko de code de persos rééquilibrés » : dans les écarts courts, le code des persos montre surtout des **renumérotations
  d'animations** et des **tables par variante**, pas des constantes de dégâts.
- Table de relocalisation A5 d'Upper : il manque `$8C61-$8C79 +$254` et `$9EA4 +$136`, présents dans celle de SFA3.

## 11. Fichiers

`ECARTS-UPPER.md` (ce rapport) ; `familles.json` (629 écarts classés) ; `familles.txt` (comptes par étiquette) ; `sites.txt`
(434 sites, une ligne chacun) ; `manuel.py` (décisions par plage, modifiables) ; scripts : `carte_ro5.py`, `realigne.py`,
`ecarts.py`, `classe.py`, `famille.py`, `site.py`, `ctx.py`, `s3ctx.py`, `lea_upper.py`, `liste_sites.py`, `voir.py`,
`persos_arcade.py`. Caches : `realign.pkl`, `ecarts.pkl`, `classe.pkl`.
Ordre de relance : `realigne.py <instantané>` → `ecarts.py` → `classe.py` → `famille.py`.
