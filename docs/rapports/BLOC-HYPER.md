# Bloc par perso d'Hyper (`$2B0/$2B8/$2B4/$2BC`) : sélection de la ligne et sous-tables de `$2B8`

Agent `agent_bloc_hyper`, 2026-10-11. Réponse à la session MAX (places 38-41 de `0x6A7A94`).

**Numérotation.** Les champs sont donnés en numérotation PS2, qui est aussi celle de l'arcade : `$102`, `$132`, `$D3`, etc.
Dans `carte_image.txt` (traduction en « mode CPS2 »), les octets apparaissent XOR 1 : `$103`, `$133`, `$F1`, `$122`, `$329`, `$28C`.
Les longs gardent leur déplacement. Les adresses de code sont des adresses du **fichier** (= PS2 − `0x1F0000`), sauf mention contraire.

---

## 0. Réponse courte

1. **Il n'y a pas de « série » dans le code.** Le jeu ne compte pas les lignes et ne lit aucun champ de série.
   - La routine choisit **une table parmi trois** selon le **mode de jeu ZERO 3**, puis **une ligne parmi trois** selon l'**isme**.
   - Les « 6 ou 9 lignes » d'un perso sont seulement plusieurs groupes de 3 lignes, rangés à la suite. Des entrées *différentes* des trois tables pointent vers ces groupes :
     ```
     table = 0x6A7D54   si $123 == 2         (mode ZERO 3 « curseur 4 » : $122 = $80)          48 entrées
           = 0x6A7C94   sinon si $F0 < 0     ($F0 = copie de $15E ; mode « curseur 7 » : $15E = $81)  48 entrées
           = 0x6A7A94   sinon                                                                 128 entrées
     bloc  = table[$102]                    (u32, $102 = perso + version, 0..$7F)
     ligne = bloc + 16 × i,  i = 0 si $132 = 0 (A), 1 si $132 < 0 (X), 2 si $132 > 0 (V)
     $2B0 = ligne[0] ; $2B8 = ligne[1] ; $2B4 = ligne[2] ; $2BC = ligne[3]
     ```
     - `0x6A7D54` est prioritaire sur `0x6A7C94`.
     - Ni la version `$D3/$117` ni les bits de `$102` ne servent de « série » : la version est déjà dans l'index `$102`.
2. **`$2B8` est lue par `index = n + 48 × s`**, avec `s` lu dans des champs de la **victime** (`0x2B8E10`) :
   - `s = 0` si `$328 = 0`, c'est-à-dire si le dernier coup reçu est une attaque ZERO 3 ;
   - `s = 1` si `$328 ≠ 0` et `$28D = 0` : coup d'une version ancienne (ZERO, ZERO 2 ou ALPHA) ;
   - `s = 2` si `$328 ≠ 0` et `$28D ≠ 0` : coup d'une version ancienne, dans un enchaînement commencé en **custom combo**.

   Les jeux de boîtes `$74` et `$75` sont **nouveaux dans Hyper** :
   - `$74` = **aucune boîte de corps** : la victime ne peut pas être reprise en jonglage ;
   - `$75` = **une seule boîte de corps** (`$90` n° `$41`, boîte ajoutée par Hyper) : jonglage possible pendant un custom combo, comme dans ZERO 2.
3. **Upper** (`0x16BCB0`) : la même routine, **sans** les deux tables de mode. Elle n'utilise que `T_749838[$102] + 16 × isme` (40 entrées).
   Le lecteur `$2B8` d'Upper n'a pas de sous-table.
4. **Recette pour les places 38-41** (`$102 = $26..$29`, plage ZERO 3) :
   - **3 lignes suffisent** ;
   - il faut **écrire les 3 tables** : `0x6A7A94`, `0x6A7C94` et `0x6A7D54` aux index `$26..$29`. Aujourd'hui elles pointent toutes sur le bloc de Ryu `0x6B3C10` ;
   - la `$2B8` doit avoir **144 entrées**. Le minimum est de recopier les 48 décalages trois fois (§4).

---

## 1. Routine d'initialisation du bloc

### 1.1 Hyper

- MIPS : `0x2E7C40` (PS2 `0x4D7C40`, prologue). Corps de `0x2E7C5C` à `0x2E7F28`.
- 68K traduit : `$071C88-$071CE6` (vérifié dans la ROM copiée : `$071CB0 = 2070`, `$071CD4 = D0C0`).

```
0x2e7c68 lb  a0,258(A6)        ; $102
0x2e7c7c sll a0,v1,2           ; ×4
0x2e7c88 lui/addiu 0x6a7a94    ; table par défaut
0x2e7ca8 lb  v1,240(A6)        ; $F0
0x2e7cc4 bgez → sinon 0x6a7c94
0x2e7ce8 lb  v1,291(A6)        ; $123
0x2e7cf4 subu (cmp #2) ; bne → sinon 0x6a7d54
0x2e7dd4 lw  a0,0(table+4×$102)
0x2e7df8 lb  v1,306(A6)        ; $132 : 0 → +0 ; <0 → +16 ; >0 → +32
0x2e7eac sw  → 688 ($2B0) ; 0x2e7ed0 → 696 ($2B8) ; 0x2e7ef4 → 692 ($2B4) ; 0x2e7f0c → 700 ($2BC)
```

Traduction 68K (`carte_image.txt`, déplacements XOR 1) :

```
071C8A MOVE.B $103(A6),D0 ; LSL.W #2,D0 ; LEA $18C954 [0x6A7A94],A0
071C96 TST.B $F1(A6)       ; BPL ; LEA $18CB54 [0x6A7C94],A0
071CA2 CMPI.B #2,$122(A6)  ; BNE ; LEA $18CC14 [0x6A7D54],A0
071CB0 MOVEA.L 0(A0,D0.W),A0
071CC2 MOVEQ #0,D0 ; TST.B $133(A6) ; BEQ ; MOVEQ #16 ; BMI ; MOVEQ #32 ; ADDA.W D0,A0
071CD6 MOVE.L (A0)+,$2B0 ; (A0)+,$2B8 ; (A0)+,$2B4 ; (A0),$2BC
```

**C'est la seule routine qui écrit `$2B0..$2BC`** : un balayage de tout le MIPS ne trouve que ces 4 `sw`. Elle a 10 appelants :

| appelant (fichier) | 68K | rôle |
|---|---|---|
| `0x2A21E8` | `$068D88` | **init. du joueur en début de manche** (`0x2A1630`). Elle appelle d'abord `0x321BA0` (décodage `$102 → $116/$117/$D3`). Juste avant, `0x2A1EC0` recopie `$F0 ← $15E` |
| `0x2C51B4`, `0x2C5564` | `$06D940`, `$06D9AE` | Gen : `BCHG #1,$102` (changement de garde `$11 ↔ $13`), puis `0x321BA0` et la routine |
| `0x1C75B0`, `0x1C78DC`, `0x1C870C`, `0x1C95A0`, `0x1CA74C`, `0x1CAA20`, `0x1CDBCC` | `$043B18…$04491C` | code propre de Gen (mêmes changements de garde) |

**Les deux champs de mode** (ce sont les modes cachés de SFA3, réservés à ZERO 3 ; INDEX-HYPER §4.1) :
- **`$123`** (`0xA5F7C`, 68K `$012520`) :
  - d'abord `$123 ← $132`, l'isme (−1, 0 ou +1) ;
  - si la version est ZERO 3 (`BTST #4,$117`) et que `$122 ≠ 0` : `$123 = 2` si `$122 = $80`, `4` si `$122 = $82`, `3` si `$122 = 2` ;
  - `$122` vient de l'écran de mode : curseur 4 (Start+3) = `$80`. Seule la valeur **2** change de table.
- **`$F0`** :
  - c'est la copie de `$15E` faite à l'init. de manche ;
  - `$15E = $81` vient du curseur 7 (Start+2), qui impose aussi l'isme X ;
  - ce même mode pose les bits 3 et 7 de `$D3` (« EX forcé »).
- Les deux modes passent par l'écran de mode de ZERO 3. En pratique, `0x6A7C94` et `0x6A7D54` ne sont lues que pour `$102 < $30`, d'où leurs 48 entrées.

### 1.2 Pourquoi 3, 6, 9 (ou 12) lignes

Les trois tables pointent vers des groupes de 3 lignes contigus. Voici les entrées qui diffèrent de `0x6A7A94`, pour `$102 < $30` :

| `$102` | `0x6A7A94` (normal) | `0x6A7C94` (`$F0 < 0`) | `0x6A7D54` (`$123 = 2`) |
|---|---|---|---|
| `$00` Ryu | `0x6B3C10` (lignes 1-3) | **+48** (lignes 4-6) | +0 |
| `$17` Evil Ryu | `0x6B3C10` (= Ryu, lignes 1-3) | +0 | **+96** (lignes 7-9) |
| `$02` Akuma | `0x6D1880` (1-3) | +0 | **+96** (7-9) |
| `$24` Shin Akuma | `0x6D18B0` (= Akuma, lignes 4-6) | +0 | **+96** (= Akuma, lignes 10-12) |
| `$15` Balrog | `0x7E1920` (1-3) | **+96** (7-9) | +0 |
| `$25` EX Balrog | `0x7E1950` (= Balrog, lignes 4-6) | id. | id. |
| `$01 $04 $0A $0B $0F $10 $18 $19 $1C $20` | bloc (1-3) | **+48** (4-6) | +0 |
| `$12`, `$14` (hors grilles) | Ryu par défaut | blocs de Chun-Li / Sodom | id. |
| `$26..$2F` (**places 38-47**) | **Ryu `0x6B3C10`** | **Ryu** | **Ryu** |

Pour Ryu :
- lignes 4-6 (`$F0 < 0`) : `$2B4` et `$2BC` changent ;
- lignes 7-9 (Evil Ryu, `$123 = 2`) : `$2B0` change.

C'est bien le constat de la session MAX. Mais les lignes 7-9 de Ryu **ne servent qu'à Evil Ryu**. **Upper fait déjà la même chose** :
- `T_749838[$24] = 0x7B03E0` = Akuma + 48 ;
- `T_749838[$25] = 0x87E520` = Balrog + 48.

⟹ **Le nombre de lignes n'est géré nulle part.** Il n'y a ni compteur ni plafond : chaque table pointe directement sur le bon groupe de 3 lignes.

## 2. Lecture de `$2B8`

Lecteurs (balayage MIPS des `lw …,696(…)`) :

| fichier | 68K | lecture |
|---|---|---|
| **`0x2B8E10`** | `$06C088-$06C0AE` | **choix d'animation standard** : `n` (D0) **+48 si `$328 ≠ 0`, encore +48 si en plus `$28D ≠ 0`**, puis `ANDI.W #$FF` et `table[index]` (relatif au début de la table) |
| `0x2E7BB0` | `$071C6C` | projection (la victime est saisie) : `A0 = T + T[0] + D0`, où D0 vient de la table de projection `0x6A73D4` du lanceur, indexée par le `$116` de la victime. Pas de sous-table |
| `0x2E61BC` | `$071818` | entrée **3** en direct (sous-table 0) |

```
0x2b8e20 lw   v1,696(A6)      ; $2B8
0x2b8e3c lb   v0,808(A6)      ; $328
0x2b8e58 beq  → saut
0x2b8e68 addiu D0,+0x30
0x2b8e84 lb   v0,653(A6)      ; $28D
0x2b8ea0 beq  → saut
0x2b8eb0 addiu D0,+0x30
0x2b8ebc jal  0x4a8ee0        ; ANDI #$FF ; ADD D0,D0 ; MOVE.W 0(A0,D0),D0 ; ADDA ; pose $1C…
```

**Le sélecteur** (les deux champs appartiennent à la **victime**) :
- **`$328`** est écrit en `0x42FA4` (traitement du coup reçu) : c'est l'octet **`+$20` de l'attaque reçue** (format à 40 octets d'Hyper).
  - Il vaut 0 pour ZERO 3, 2 pour ZERO, `$82` pour ZERO 2 et `$C2` pour ALPHA (INDEX-HYPER §3.2).
  - C'est donc **la version de l'attaquant**, sauf pour les ZERO 3, qui laissent 0.
- **`$28D`** est écrit en `0x43668`, au premier coup de l'enchaînement seulement (`TST $28D ; BNE`) : `$28D ← $3E` de l'attaquant.
  - Le `$3E` de l'attaquant est remis à 0 au début de l'attaque, puis passe à 1 si `$B9` (custom combo actif) : `0x2E34E4`, `0x2D4C04`.
  - Les objets peuvent porter `$80`.
  - Cette logique vient de SFA3 : on la retrouve à l'identique dans Upper (`0x3665C/0x36694`).
- **Remise à 0** de `$328` et `$28D` : routine `0x2C5C3C`, appelée au retour à la routine 2 (`$020000`, `$020002`, `$020400`, `$020406`), c'est-à-dire en fin d'enchaînement.

⟹ La sous-table 2 ne sert que si les deux conditions sont réunies : coup d'une version ancienne **et** enchaînement commencé en custom combo, c'est-à-dire une jongle de CC à la ZERO 2 ou ALPHA.

**Le sens de l'octet `+8` du pas** : c'est l'index du **jeu de boîtes**.
- Chemin de lecture : `$06C0D4` `MOVE.B 9(A0)`, numérotation PS2 `+8`. Puis `×4`, dans la table `$88` du perso (`0x6A6DD4[$102]`), et `→ $C8`.
- Le long `$C8` contient 4 octets, en numérotation PS2 : `[0]` boîte de corps de la table `$90`, `[1]` table `$94`, `[2]` table `$98`, `[3]` boîte de poussée `$9C`.
  - Lecture en `0x41588-0x41C34` : `$C8 → $8B98(A5)` puis 3 tests, qui posent les bits 1/2/4 de `$EB` de l'attaquant.
  - Le masque d'arcade `ANDI.L #$FFFFFF00` (`0x2E5D8C`) écarte la boîte de poussée.
- Jeux de boîtes de Ryu (`0x6AF770`) comparés à Upper (`0x74CAB8`) :
  - entrées `$00-$73` identiques ;
  - Upper s'arrête à `$73`, Hyper ajoute `$74`, `$75`, `$76`…

| jeu | octets `[0..3]` | sens |
|---|---|---|
| `$04` / `$07` (sous-table 0) | `04 00 00 03` / `03 00 00 03` | boîte de corps `$90` n° 4 ou n° 3, poussée 3 |
| **`$74`** (sous-table 1) | `00 00 00 03` | **aucune boîte de corps** (poussée seule) : on ne peut pas reprendre la victime |
| **`$75`** (sous-table 2) | `41 00 00 03` | une boîte de corps `$90` n° **`$41`** = (−5, 45, 45, 30) ; Upper n'a que 65 boîtes `$90` (n° 0-`$40`) : **boîte ajoutée par Hyper** |

Comparaison des trois sous-tables de Ryu (`$2B8 = 0x6B3FD6`) :
- entrées 19, 23, 24, 28, 32, 34 : l'octet `+8` vaut `$04`/`$07` en sous-table 0, **`$74` en sous-table 1** et **`$75` en sous-table 2** ;
- entrée 29 : sous-table 2 seulement (`$06 → $75`) ;
- entrées 22, 27 : `$08 → $06` ;
- entrées 20, 33 : scripts différents ;
- mot 144 = 0, mot 145 = 5. Aucun lecteur ne dépasse l'index 143.

⚠ **Correction du message de la session MAX** : en sous-table 1, `+8` ne vaut pas `$04/$04/$07` (valeurs de la sous-table 0) mais **`$74`**.

## 3. Homologue Upper

- Routine : MIPS `0x16BCB0` (PS2 `0x35BCB0`), 68K `$031E44-$031E88`. Appelants :
  - init. de manche : `0x223634` (68K `$04E8DC`) ;
  - Gen : `0x24473C`, `0x244ADC`, comme `0x2C51B4/0x2C5564` d'Hyper ;
  - 8 sites `0x3B67A8…0x3BC694`, non identifiés.

```
031E46 MOVE.B $103(A6),D0 ; LSL.W #2 ; LEA $1DFB78 [0x749838],A0 ; MOVEA.L 0(A0,D0.W),A0
031E64 MOVEQ #0 ; TST.B $133 ; BEQ ; MOVEQ #16 ; BMI ; MOVEQ #32 ; ADDA.W D0,A0
031E78 MOVE.L (A0)+,$2B0 ; $2B8 ; $2B4 ; (A0),$2BC
```

- **Différences avec Hyper** : pas de test `$F0` ni `$123`, et une seule table de 40 entrées.
- **Lecteur `$2B8` d'Upper** (`0x239B60`, 68K `$051A84`) : `JMP` direct vers `ANDI #$FF / table[n]`, **sans `$328/$28D`** ⟹ 48 entrées.

## 4. Recette pour les places 38-41 (`$102 = $26..$29`)

1. **Bloc = 3 lignes de 16 octets** dans l'ordre `$2B0, $2B8, $2B4, $2BC` : ligne 1 isme A, ligne 2 isme X, ligne 3 isme V.
   - On reprend tel quel le bloc de 3 lignes d'Upper (ou de ZERO 3).
   - 6 ou 9 lignes ne servent que si l'on veut des animations différentes dans les modes `$F0 < 0` ou `$123 = 2`.
2. **Écrire les 3 tables** à l'index `$102` :
   - `0x6A7A94 + 4 × $26..$29` ;
   - `0x6A7C94 + 4 × $26..$29` ;
   - `0x6A7D54 + 4 × $26..$29`.

   Elles pointent toutes vers le même bloc, ou vers une variante. Ces index tiennent dans les 48 entrées des deux tables de mode.

   **Sinon**, dans les modes « curseur 7 » (`$15E = $81`) et « curseur 4 » (`$122 = $80`), le perso MAX prendrait les **animations de Ryu** : toutes ces entrées valent aujourd'hui `0x6B3C10`.
3. **Table `$2B8` à 144 entrées**, u16 relatives au début de la table.
   - Les sous-tables 1 et 2 sont lues chaque fois que le perso MAX reçoit un coup de ZERO, ZERO 2 ou ALPHA. C'est possible en VERSUS : il n'y a aucune garde.
   - Une table de 48 entrées lirait donc les pas comme des décalages ⟹ plantage ou animation absurde.
   - **Minimum** : entrées 48-95 et 96-143 = copie exacte des entrées 0-47. Les décalages sont relatifs au début de la table, donc les mêmes valeurs visent les mêmes scripts. On obtient le comportement d'un perso ZERO 3 d'Upper : il peut être repris en jonglage par tout le monde.
   - **Si les pas suivent la table** : les 96 entrées ajoutées décalent les pas de 192 octets ⟹ ajouter 192 à **tous** les décalages, y compris ceux de la sous-table 0. On garde le mot 144 = 0, comme le mot 48 d'Upper : il n'est pas lu, mais cela reste homogène.
   - **Projections** : la position relative des pas « projeté » par rapport au **script de l'animation 0** ne doit pas changer, car `0x2E7BB0` adresse `T + T[0] + décalage`. En recopiant la zone des pas d'Upper sans la réordonner, c'est automatique.
   - **Fidèle à Hyper** (facultatif), pour les réactions en l'air et au sol (entrées 19-34 de Ryu) :
     - sous-table 1 : copie des pas avec `+8 = jeu « sans boîte de corps »` (comme `$74`) ;
     - sous-table 2 : copie avec `+8 = jeu à une boîte` (comme `$75`).
     - Il faut alors ajouter ces jeux à la fin de la table `$88` du perso, l'index devant rester < 256, et, pour `$75`, une boîte dans sa table `$90`.
4. **Une seule version** :
   - **La version n'est pas un champ à part**, elle est codée dans `$102`. `$26..$29` se trouvent dans la plage ZERO 3 (`0x5C2490[$26..$2F] = $10`).
   - Si la ligne de grille du perso (`0x5C5380 + 4 × $116`) vaut `id, FF…`, l'écran des versions ne propose rien d'autre (ETATS-HYPER : « perso à version unique, `0x5C5381 < 0` »). Le perso ne peut donc pas être choisi « dans une autre version ».
   - Restent l'**isme**, qui demande 3 lignes, et les **deux modes ZERO 3**, qui demandent les points 2 et 3 ci-dessus.
   - Rien ne peut lire `0x6A7C94/0x6A7D54` au-delà de `$2F` pour lui.

**Points voisins à vérifier côté MAX** (hors question) :
- `0x5C5300[$26..$2F] = 0` : le perso de base serait Ryu.
- La grille des versions n'a que 38 lignes (`$116 ≤ $25`) ; la ligne `$26` déborde vers `0x5C5418`, puis vers la grille Start `0x5C5420`.
- Dans la grille de sélection `0x5C5650`, les codes `$26..$29` sont les cases « ? ».
- Les attaques d'Hyper font **40 octets**, avec `+$20..+$27 = 0` pour ZERO 3.

## 5. Preuves à l'exécution

Banc : fork `cps2f sfa3hx`, **copie** des ROM et données dans `work/agent_bloc_hyper/m9/`, nvram et cfg neufs à chaque lancement, sans `-state`.
- Lanceur : `lance.sh`.
- Script : `lua/bloc.lua`, qui enveloppe `agent_hyper_etats/lua/tournee_hyper.lua`, en VERSUS.
- Points d'arrêt du débogueur (avec `printf`) :
  - `$071CB0` : table et `$102×4` ;
  - `$071CD4` : décalage de ligne ;
  - `$06C0AE` : index final de `$2B8`.
- Journaux : `essais/v1.bloc`, `essais/v2.bloc` (et `.log`).

| sélection (J1 / J2) | table vue (68K) | D0 = `$102×4` | ligne (D0) | `$2B0 / $2B8 / $2B4 / $2BC` relevés | attendu |
|---|---|---|---|---|---|
| Ryu ZERO `$30` | `$18C954` (A94) | `$C0` | 0 (A) | `8ABA10 / 8ABB46 / 8ABA92 / 8ABB02` | A94[`$30`] |
| Ryu ZERO 3 isme V | A94 | 0 | `$20` | `6B3CA0 / 6B3FD6 / 6B3DD4 / 6B3EF8` | ligne 3 |
| Ryu ZERO 3 isme X | A94 | 0 | `$10` | `… / 6B3F8C` | ligne 2 |
| Ryu ZERO 2 `$40` / ALPHA `$60` | A94 | `$100` / `$180` | 0 | `8CA3D0…` / `8D3410…` | |
| Ryu ZERO 3 **mode 7** (`$15E = $F0 = $81`, `$D3 = $98`) | **`$18CB54` (C94)** | 0 | `$10` (X imposé) | `6B3CA0 / 6B3FD6 / 6B3E66 / 6B3F42` | **ligne 5** |
| Evil Ryu `$17` **mode 4** (`$122 = $80`, `$123 = 2`) | **`$18CC14` (D54)** | `$5C` | 0 | `6B3D3A / 6B3FD6 / 6B3DD4 / 6B3EF8` | **ligne 7** |
| Balrog `$15` mode 7 | C94 | `$54` | `$10` | `7E19B0 / 7E1C10 / 7E1B22 / 7E1BD2` | Balrog + 96 + 16 = ligne 8 |
| Ken `$01` mode 7 / isme V | C94 / A94 | 4 | `$10` / `$20` | `6C50C4…` / `6C5030…` | ligne 5 / ligne 3 |

Champ de ligne relevé : `$123` vaut l'isme (`$FF` en X, `01` en V), sauf en mode 4 où il vaut 2.

Index `$2B8` de la victime J2 (point d'arrêt `$06C0AE`) :

| attaquant | `$328` | `$28D` | D0 relevés | sous-table |
|---|---|---|---|---|
| Ryu ZERO 3 | 0 | 0 | `$14 $15 $16 $1B $26 $27` | 0 |
| Ryu ZERO `$30` | `02` | 0 | `$43 $44 $45 $46 $4B` (= n + 48) | 1 |
| Ryu ZERO 2 `$40` | `82` | 0 | `$43…$4B` | 1 |
| Ryu ZERO, **`$28D` forcé à 1 sur J2** (essai `FORCE28D`) | `02` | `01` | `$73 $74 $75 $76 $7B` (= n + 96) | 2 |

Le seul forçage est l'écriture de `$28D` sur J2 pendant la sélection 1 de v2. Il sert à montrer le sélecteur sans avoir à jouer un custom combo ; sa signification vient de l'analyse statique (§2).

Non obtenu : sélection 4 de v1 (Akuma en mode 4 / mode 7), où J2 n'a pas fini sa sélection avant la fin de l'essai. Ce n'est pas nécessaire au résultat.
