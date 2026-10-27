# Le hasard de SFA3 (arcade et traduction) — pourquoi FBNeo ne tire pas comme MAME

Agent `agent_hasard`, 2026-10-07. Analyse en lecture seule : aucun fichier existant modifié. Scripts, sondes et
mesures dans `work/agent_hasard/` (liste en fin de document).

## 0. Résumé

- SFA3 a **un seul générateur** : `$01BDA6` (arcade) = `$0114DC` (traduction, mêmes instructions). Graine : le mot
  `$FF80AE` (octet haut `$AE`, octet bas `$AF`). Mise à `$01C3` au démarrage.
- La graine n'avance **qu'à chaque appel**. Ni l'IRQ vblank, ni la boucle d'attente de l'ordonnanceur ne l'appellent,
  **ni dans l'arcade, ni dans la traduction**. Ce n'est donc pas « l'attente arcade appelle le hasard et la traduite
  non » (ni l'inverse) : les deux sont identiques sur ce point.
- Pourtant, le **nombre d'appels par image** dépend du temps réel, de trois façons. Ces trois mécanismes viennent du
  jeu d'origine et existent aussi dans l'arcade :
  1. la boucle principale (`$40A2-$40D4`) appelle le RNG **une fois par tour**. Un tour est perdu quand une passe de
     l'ordonnanceur déborde sur l'image suivante (chargements) ;
  2. des appels sont conditionnés par le compteur d'IRQ `$FF8080` (IA : `$4065A`, `move.b ($80,A5) ; andi #3 ; bne`) ;
  3. la cinématique d'intro avance au rythme du **compteur musical du Z80** (`$618021`, lu à chaque image en `$4CE8`
     arcade / `$755E` traduit). Une scène à particules tire **51 nombres par image** (48 en `$5DE6`, plus 3).
- **Mesure MAME ↔ FBNeo** (même traduction, attraction) : graines identiques jusqu'à l'IRQ n°1176. Ensuite, les deux
  scènes à particules de l'intro durent **une image de plus dans FBNeo**, soit +51 appels chacune et ≈ +100 au total.
  Dans MAME, ces scènes ne débordent jamais (marge ≥ 254 lignes). Elles se terminent pile quand `$618021` passe de
  `21` à `22`. **La cause principale est donc la phase entre le Z80 (musique) et le 68000**, et non la boucle
  d'attente. Ensuite, la démo diffère et l'écart grossit (+249 puis +471 appels).
- Dans FBNeo seul, changer l'horloge du 68K décale aussi le tirage, dès les chargements de l'attraction (IRQ ≈ 420-435 :
  2 à 4 tours de boucle principale gagnés ou perdus) : c'est le mécanisme 1.
- Piste la plus simple pour aligner MAME et FBNeo : empêcher l'effet **décoratif** de particules (`$5DDE-$5DFA`
  arcade, `$8622-$863E` traduit) de consommer la graine principale (sauvegarder et restaurer `$FF80AE`, ou utiliser
  une graine à part). Reproduire exactement l'arcade est impossible : l'arcade elle-même dépend du temps (voir §5).

## 1. Le générateur

### 1.1 Routine (arcade `$01BDA6`, traduction `$0114DC`, MIPS `0x27ED60` = fichier `0x8ED60`)

```
01BDA6  move.w ($ae,A5),D0      ; s = graine (A5 = $FF8000 → $FF80AE)
01BDAA  move.w D0,D1
01BDAC  add.w  D0,D0
01BDAE  add.w  D1,D0            ; 3*s (16 bits)
01BDB0  lsr.w  #8,D0            ; h' = (3*s >> 8) & $FF
01BDB2  add.b  D0,($af,A5)      ; l' = l + h'
01BDB6  move.b D0,($ae,A5)      ; octet haut = h'
01BDBA  move.b ($af,A5),D0      ; résultat D0.w = l' (0..255, octet haut de D0 nul)
01BDBE  rts
```

Formule : `h' = ((3·s) >> 8) & 0xFF`, `l' = (l + h') & 0xFF`, `s' = h'·256 + l'`. La routine renvoie `l'`.

Propriétés (`rng.py`) : depuis `$01C3`, l'orbite est un **cycle pur de 43 534 états**, ce qui permet de compter les
appels à partir de deux graines. L'application a 115 cycles et 86 points fixes, dont `$00xx` pour `xx < $56` : une
graine `0` resterait bloquée. C'est pourquoi la sauvegarde arcade (§1.2) réécrit `$1C3` si elle trouve 0.

### 1.2 Initialisation et sauvegarde

- Arcade `$3F10` : `tst.b ($86,A5) ; bne ; move.w #$1C3,($ae,A5)`. `($86,A5)` est mis à $FF en `$1060-$1074` si le
  bit 14 de `$804030` vaut 0, c'est-à-dire si la mémoire annexe `$660000-$663FFF` est présente. Avec cette mémoire, la
  graine est conservée en triple exemplaire en `$661200/$662200/$663200` (`movep`, vote et réparation en `$29B8`, `$1C3`
  si 0). Elle est sauvegardée toutes les 256 IRQ par le vblank : `$1244 tst.b ($80,A5) ; bne ; jsr $2C48`.
  Sur MAME (pas d'adaptateur), `$86 = 0` : graine `$01C3` au démarrage (mesuré : 1re valeur `$01C3`).
- Traduction `$021116` (MIPS `0xEFAB8`) : `move.w #$1C3,$00AE(A5)` **sans condition**. Le portage PS2 a supprimé la
  persistance, ce qui revient au même que l'arcade sur MAME. La sauvegarde `$2C48` n'existe pas dans le vblank traduit.
  Il n'y aurait d'ailleurs pas la place : `$660000-$6637FF` sert aux piles des tâches du noyau traduit.

### 1.3 Appelants

- Arcade : 217 `JSR $1BDA6.L` dans l'image (aucun BSR ni JMP). Traduction : 208 `JSR $0114DC.L` + 16 `BSR`, nombre
  comparable.
- Principaux appelants, mesurés sous MAME (adresse de retour sur la pile) et ramenés à l'arcade :

| Arcade (JSR) | Traduit (retour) | Rôle | Fréquence |
|---|---|---|---|
| `$0040C2` | `$006824` | **boucle principale** (`$40A2` : `addq.b #1,($81,A5)` … `jsr RNG` … dort 1 image) | 1 par tour |
| `$005DE6` | `$008630` | effet de particules de l'intro (`lea $90E640,A0 ; moveq #$2F,D6` : 48 × `RNG & $7F + $80`) | 48 par image pendant la scène |
| `$0A0B28` | `$038630` | effet / objet (attraction) | variable |
| `$0277F2` | `$043F08` | tirage d'une table (`andi #$3C`) | 1 par image en démo |
| `$030A66` | `$00F30E` | combat (`andi #$1F`, masque de bits par perso) | combat |
| `$0B059E`, `$0B0688` | `$01B8EA…$01B9D4` | objets du décor | variable |
| `$00672A` | `$0090C0` | conditionné par `($81,A5) & 7` (compteur de la boucle principale) | 1 / 8 tours |
| `$040664-$040694` | `$06F89A…` | **IA**, conditionnée par `($80,A5) & 3` (**compteur d'IRQ**) | 1 / 4 IRQ |
| `$01E8A2` | — | choix aléatoire de personnage (`$1E898`, `& $3F`, +`$40` si `$EE(A5) ≥ 1`) | sélection |
| `$085ACC` | `$02CB76` | combat | combat |

## 2. Ce qui fait avancer la graine

### 2.1 Pas l'IRQ, pas l'attente

- Vecteurs (lus dans `sfa3ud_prog.bin` : dans `sfa3_prog.bin`, la table `$0-$3FF` est déchiffrée à tort) :
  niveau 2 (`$68`) = **`$1198`** (vblank) ; niveaux 1, 3-7 = `$14E` (`RTE`).
- Vblank `$1198-$128A` : 43 fonctions atteintes par appels directs (`graphe.py`). Le RNG n'en fait pas partie. Les
  trois sauts indirects non suivis sont dans `$2640/$26D4/$29B8` (EEPROM et mémoire annexe), sans RNG.
- Ordonnanceur `$1110-$1140` : `clr.b -$7B9C(A5)` (= `$FF0464`), puis parcours des 16 emplacements (`-$7DA4(A5)` =
  `$FF025C`, $20 octets chacun) sous `SR=$2600`. Il recommence en `$1110` dès que le vblank a posé le drapeau.
  `JSR $1414` = `move.w #$20,D0 ; moveq #0,D1 ; rts` : pas de RNG.
- La seule tâche qui « cède » sans dormir (`TRAP #4` via `$13A2`, boucle `$16C12-$16C56`) tourne à chaque passe libre.
  Elle ne tire pas : elle avance les compteurs des tâches si `($AA,A5)` est mis (mode de mise au point).
- Traduction : IRQ2 `$0C08` → VBL traduit `$2F8E` (9 fonctions atteintes, sans RNG). Attente `$0BC0-$0C04` : relit
  `$663888` (compteur d'images posé par l'IRQ2 en `$0C34`), sans appel. Elle recommence la passe (`$0BCE` →
  `$0BC0`) si l'image change en cours de route, comme l'arcade.

### 2.2 Mais le nombre d'appels par image dépend du temps

1. **Tours perdus par débordement.** Une tâche endormie pour une image (état 1, compteur 1) est réveillée par le
   vblank (état 4). Si la passe n'atteint pas cette tâche avant le vblank suivant, celui-ci ne la décompte pas : elle
   est déjà prête. La tâche tourne donc **une fois pour deux vblanks**. La boucle principale tire une fois par tour :
   le nombre de tirages n'est plus égal au nombre d'images. Mesures MAME (`correl.py`, 6 000 images d'attraction) :
   - arcade : 124 images débordées, 146 tours de boucle principale manqués, **dont 134 sur ou juste après un
     débordement** ;
   - traduction : 79 images débordées, 153 tours manqués, dont 88 sur ou juste après un débordement. Les autres sont
     des attentes voulues du portage.
   L'arcade déborde donc aussi, surtout pendant les chargements de scène.
2. **Appels conditionnés par le compteur d'IRQ** `$FF8080` (vblank `$1250 addq.b #1,($80,A5)` ; traduit `$3056`).
   Exemple : `$4065A move.b ($80,A5),D0 ; andi.w #3 ; bne → jsr RNG` (traduit `$6F890`). Si la tâche tourne après le
   vblank au lieu d'avant, la condition change.
3. **Synchronisation sur la musique.** L'intro lit l'octet `$618021` (compteur de position musicale écrit par le Z80
   dans la RAM QSound) à chaque image : arcade `$4CE8 move.b $618021,($b,A5)`, traduit `$755E`. Elle change de scène
   quand ce compteur avance. Les scènes à particules tirent 51 nombres par image, pendant un nombre d'images fixé par
   la musique (Z80, IRQ 250 Hz) et non par le 68K.

## 3. Arcade et traduction

| Point | Arcade | Traduction |
|---|---|---|
| générateur | `$1BDA6` | `$0114DC`, mêmes instructions |
| graine initiale | `$1C3` (`$3F16`, si pas de mémoire annexe) | `$1C3` (`$21116`, sans condition) |
| persistance / sauvegarde vblank | `$2C48`, toutes les 256 IRQ, si `$86` | absente (sans effet sur MAME) |
| appel par tour de boucle principale | `$40C2` | `$681E` |
| boucle d'attente | `$1110-$1140`, pas de RNG | `$0BC0-$0C04`, pas de RNG |
| IRQ vblank | `$1198`, pas de RNG | `$0C08` → `$2F8E`, pas de RNG |
| préemption de la passe par le vblank | oui (drapeau `$FF0464`) | oui (`$663888`) |
| après une passe complète | rebouclage immédiat (tâches `TRAP #4`) | attente de l'image suivante |
| intro synchronisée sur `$618021` | oui (`$4CE8`) | oui (`$755E`) |

Seule différence de structure : après une passe complète, l'arcade reboucle aussitôt, alors que la traduction attend
l'image suivante. Cela ne concerne que les tâches qui cèdent par `TRAP #4` (`$16C12`), qui ne tirent pas. La logique
du hasard est donc reproduite fidèlement. Seul le **profil temporel** diffère : le code traduit et le banc ne
débordent pas sur les mêmes images. La traduction arrive aussi au titre environ 500 images plus tôt.

## 4. MAME ↔ FBNeo : mesures

Même traduction des deux côtés (`roms_tr` du 2026-10-07 12:55). FBNeo : zip reconstruit dans `fb/` par
`paquet_fbneo.py` (`HSFA_SORTIE`), lanceur `fb/hsfa_run_graine`, copie de `hsfa_run.c` qui journalise
`$FF80AE/$FF8080/$FF8081` à chaque image. MAME : `lance.sh tr trA` (sonde `sonde.lua`). Pour aligner les deux
émulateurs, on se cale sur le compteur d'IRQ `$FF8080` déroulé. Pour compter les appels, on prend l'indice de la graine
sur l'orbite de `$01C3`.

- Jusqu'à l'IRQ n°1175, **mêmes graines**, avec un décalage d'échantillonnage d'une IRQ : FBNeo relève l'état une IRQ
  plus tard. On y trouve la même chaîne `e4c6 → ae74 → 0b7f → 22a1`.
- Rafales de l'effet de particules (≥ 40 appels par image, `rafales.py`) :
  MAME `(986-1023 : 1940 appels)`, `(1179-1201 : 1173)`, `(1234-1242 : 459)`, `(1303-1353 : 2496)` ;
  FBNeo `(987-1024 : 1940)`, `(1180-1203 : 1224)`, `(1235-1244 : 510)`, `(1304-1354 : 2499)`.
  Les 2e et 3e scènes ont **une image (51 appels) de plus** dans FBNeo.
- Dans MAME, pendant la 2e scène, la marge reste entre 254 et 262 lignes, sans aucun débordement. La scène se termine à
  l'image 1216/1217, **exactement quand `$618020` passe de `0021` à `0022`** (`sonde_qs.lua`). La scène dure donc
  jusqu'au changement du compteur musical. FBNeo voit ce changement une image plus tard.
- Écart lissé (médiane ±15 IRQ, `compare_irq.py` / `ecart_lisse.py`) : FBNeo a **+1 à +2** appels d'avance
  jusqu'à l'IRQ 900 (bruit d'échantillonnage). L'écart passe à **+50** après la 2e scène, puis **+100** après la 3e. Il
  reste stable (+97) de l'IRQ 1300 à 2300 environ. Il grandit ensuite pendant la démo (+249 à l'IRQ 3500, +471 à
  6000) : les combattants et l'IA diffèrent déjà, et la divergence s'entretient.
- FBNeo seul, horloge 68K à 90/95/105/110 % (`compare_fb.py`, `zoom_fb.py`) : l'écart apparaît plus tôt, pendant les
  chargements de l'attraction. À 110 %, vers les IRQ 420-435, l'écart de tours de boucle principale passe à −2 puis
  +2, et le compte d'appels diverge (+19 à l'IRQ 600, +83 à l'IRQ 900). Le mécanisme 1 dépend donc bien du compte de
  cycles du 68K. À 100 %, MAME et FBNeo sont d'accord sur ces chargements : seule la phase musicale les sépare.

**Explication probable.** Le tirage dépend du nombre de tours de jeu par vblank et de l'image où le 68K voit avancer
le compteur musical du Z80. Ces deux quantités dépendent des cycles du 68K, de l'ordonnancement Z80/QSound et du moment
de l'IRQ dans l'image. Aucun portage ne peut les reproduire exactement entre deux émulateurs. Pour cette traduction, la
première divergence MAME/FBNeo vient de la **phase Z80 ↔ 68K dans l'intro** : une image de plus pour deux scènes à
particules, donc +102 tirages. Le reste découle de ce premier écart.

## 5. Pistes de correction

1. **Neutraliser les consommateurs décoratifs** (le plus rentable, peu risqué). L'effet `$5DDE-$5DFA` (traduit
   `$8622-$863E`) remplit 48 mots de `$90E640` (palette ou VRAM) avec `RNG & $7F + $80`. Une graine locale suffit :
   sauver `$FF80AE` avant la boucle et le restaurer après, ou appeler un clone du RNG sur une autre graine (par exemple
   un mot libre de la RAM du portage). Les scènes de l'intro n'influenceraient alors plus le tirage de la démo et de
   l'adversaire. À vérifier avec `ecart_lisse.py` sur une nouvelle traduction. Faire de même pour `$A0B28` (traduit
   `$3862A`) si la démo diverge encore.
2. **Rendre la boucle principale insensible aux débordements** : remplacer le tirage par tour (`$40C2` / `$681E`) par
   un tirage par vblank, fait par l'IRQ. Moins utile, car à 100 % les deux émulateurs perdent les mêmes tours. Cela
   écarte aussi la traduction de l'arcade.
3. **Côté FBNeo** : essayer de caler la phase du Z80 sur MAME (découpage de l'image, moment de l'IRQ Z80 à 250 Hz,
   QSound haut niveau). Si les rafales de l'intro retrouvent la même durée que dans MAME, la démo et l'adversaire
   devraient suivre. C'est fragile.
4. **Reproduire l'arcade** : la logique l'est déjà (§3). L'arcade elle-même déborde (124 images sur 5 495) et suit la
   musique : son tirage dépend aussi du temps. Le même écart MAME/FBNeo est probable sur la ROM d'origine (non testé
   ici). Il n'y a pas de « bon » tirage à copier, seulement un comportement à rendre identique entre les deux cœurs,
   ce qui passe par 1 (ou 3).

## 6. Outils (`work/agent_hasard/`)

| Fichier | Rôle |
|---|---|
| `cherche_rng.py` | candidats RNG dans l'arcade (fonctions courtes avec mélange et accès RAM) → `$1BDA6` |
| `atteint.py`, `graphe.py` | atteignabilité par appels directs (`dec68k`) : le RNG est-il atteint depuis l'IRQ ou l'ordonnanceur ? |
| `rng.py` | formule, orbite de `$01C3` (43 534), cycles et points fixes |
| `sonde.lua` + `lance.sh <tr|arc> <dossier> [NF]` | MAME : par image, graine, nombre d'appels, tour de boucle principale, marge avant vblank (−1 = débordement), `$80`, `$81` |
| `sonde2.lua` | histogrammes des appelants (adresse de retour) et des lectures de `$663888` |
| `sonde_qs.lua` | lectures et écritures 68K de la RAM QSound par image (compteur musical `$618020/1`) |
| `analyse.py`, `correl.py` | résumé par tranches, corrélation débordements / tours manqués |
| `compare_irq.py`, `ecart_lisse.py`, `rafales.py`, `zoom.py` | MAME ↔ FBNeo alignés sur le compteur d'IRQ |
| `compare_fb.py`, `zoom_fb.py` | FBNeo ↔ FBNeo (horloges 68K différentes) |
| `fb/hsfa_run_graine(.c)`, `fb/sfa3hsfa.zip` | lanceur FBNeo avec journal de graine (`GRAINE=`), zip de la traduction courante |
| `runs/` | mesures : `trA` (MAME traduit), `arcC` (MAME arcade, `arcA/arcB` : déterminisme vérifié), `fb90…fb110`, `qs` |
