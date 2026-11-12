# Upper MAX: arbitration files A1-A6 of the integration review (2026-11-11 / 12)

**Summary (English).** Arbitration files of agent `arbitrages_um` for the major findings of the Upper MAX integration
review ([upper-max.md](upper-max.md), part B), static analysis plus builds (no emulator). There is no A5 file.
Workshop: `<workspace>/work/arbitrages_um/` (bench batch `essais/lot_um_arbitrages.sh`, not run).
- **A1 (B2, Yun `$32D`)**: the PSP, the arcade, Upper and `re/connaissances/champs.tsv` agree on image `$32C`;
  recommendation: apply the one-byte typing fix (optional diff of the review), bench Yun. **Open**: not merged; the
  line `psp_1bc300` stays admitted in `ag/conv/non_resolus_admis.tsv` until it is.
- **A2 (B3, unresolved conversions)**: **merged** (commit `54d43f8`): unresolved conversions now fail the build;
  allow-list of 26 justified exceptions (15 admitted, 10 dead behind Eagle's cross-intro `bra`, 1 known defect);
  `CONV_NON_RESOLUS_LIBRES=1` for old batches; negative tests `tools/reviews/upper-max/essai_nr.py` (9/9).
- **A3 (B4, table `0x615940`) and A4 (B5, Arcade masks `0x61B540` / `0x61B4E0` / `0x61B510`)**: **prepared** behind
  `MAX_615940_PSP` / `MAX_MASQUES_PSP` (default 0, MAX entries read from the EBOOT, fingerprint of the native entries
  checked); at 1 the values equal the PSP (`releve_tables.py`). **Open**: bench trials E1 / E2.
- **A6 (B7, effect palettes cut at 30)**: the cut is now logged; `MAX_PALE_PLEINES` (default 0) keeps every palette;
  every PSP character has 36 or more effect palettes. **Open**: bench trial E3.
- With every switch at 0 the build equals max57 byte for byte (journal and CHANGELOG "En cours").
- **Tools kept**: `releve_tables.py`, `releve_palettes.py`, `essai_nr.py` in
  [`tools/reviews/upper-max/`](../../../tools/reviews/upper-max/).

---

## Original text (French, kept as is)

> Kept as written in the workshop. Only changes: personal paths written `<workspace>/...`, workshop folders written `<workspace>/work/...`. Paths such as `outils/…`, `sorties/…`, `essais_demain/…`, `constr/…` are relative to the review's workshop folder (above); the tools kept are in `tools/reviews/` (see the summary).


<!-- source: <workspace>/work/arbitrages_um/A1_yun_32d.md -->

## File `<workspace>/work/arbitrages_um/A1_yun_32d.md`

# A1 — Yun : `tst.b $32d(a1)` non converti (constat B2)

Défaut proposé : correctif d'un octet (`<workspace>/work/revue_upper_max/a_verser/optionnel_b2_yun_32d.diff`), testé dans un lot d'essai.
Analyse statique du 11/11 (aucun MAME, aucune construction). Outils : `outils/psp_dis.py`, `outils/cherche_off.py`,
`outils/sonde_yun_32d.lua`.

## 1. Ce que fait le code

**PSP** (EBOOT EU, routine `0x1BC300`, désassemblée par `outils/psp_dis.py 1bc300 40`) :
```
1bc340  lw   a1, 0x33c(s0)        ; drapeau MAX du lanceur (= $3C8 côté 68K) == 1 ?
1bc34c  lb   a1, 0x305(s1)        ; s1 = adversaire : compteur « en l'air depuis un saut »
1bc350  beql a1, 0, 1bc370 ; sb 0, 0x7d(s1)
1bc358  lb   a1, 0x250(s1)        ; arcade $270
1bc35c  beql a1, 0, 1bc370 ; sb 0, 0x7d(s1)
1bc364  sb   1, 0x10e(s1)         ; arcade $D6 := 1
1bc368  sb   0, 0x250(s1)         ; arcade $270 := 0
1bc36c  sb   0, 0x7d(s1)          ; arcade $5D := 0
```
PSP `+0x305` : 5 remises à 0 et 1 incrément (`0x57484`-`0x57494`) dans le moteur (`outils/cherche_off.py 0x305`),
comme l'arcade (`$283D8`… : 4 `clr.b $32d(a6)` + `addq.b #1,$32d(a6)` en `$286D4` après `tst.b $ac(a6)`).

**Upper MAX** (construction `<workspace>/work/revue_upper_max/constr/b1_v161` = copie de banc `max57`) : le code de Yun est en image
`$3AA482` (`psp_1bc300`) ; le site est en **`$3AA4B4`** : `4A29 032D` = `tst.b $32D(a1)`.
Dans l'image d'Upper (vérifié par recherche d'octets dans b1_v161) :
- image **`$32C`** = le compteur de saut : `$4F94E` `addq.b #1,$32C(a6)` (après `tst.b $AD(a6)`, puis `clr.b $271(a6)`),
  5 `clr.b $32C(a6)` (`$4F5D6`, `$4F750`, `$4F7C2`, `$4F8D4`, `$50950`) ; c'est ce que dit `re/connaissances/champs.tsv:651`
  (« img:+$32C », mesuré) ;
- image **`$32D`** = autre champ : arcade `$32C`, index 4…`$E` d'une pose spéciale posé par `$2BA1C`… (image `$535A6`
  `move.b #4,$32D(a6)`), seulement quand `$4 = $208` et selon le couple d'ids ; nul pendant le combat.

Le site lit donc un octet presque toujours nul : la branche « adversaire en l'air depuis un saut » n'est **jamais prise**.
C'est exactement le symptôme que la session MAX avait corrigé à la source (`max/notes/SAVOIR-MAX.md:159`, « branche
jamais prise … champ MOTEUR arcade `$32D` (image Upper `$32C`) ») : la source est juste, le convertisseur de
l'intégration ne connaît pas le type du champ et laisse le déplacement arcade (`⚠ CONV NON RÉSOLU`).

Le lot d'essai **existe déjà** : `<workspace>/work/revue_upper_max/constr/b2_v161` = b1_v161 + le diff ; seul `sz3.10b` change, d'un
octet (fichier `0x2A4B6`, image `$3AA4B7` : `$2D` -> `$2C`) ; `sz3.10b` md5 `295a44eb` (b1 : `8c255f0a`) ; tous les
`ext_*.bin` et `max_plus_gfx.bin` identiques ; journal : « 28 NON RÉSOLUES » (b1 : 29).

## 2. Où et quand (effet en jeu le plus probable)

- Chemin : rappel 16 (coups normaux, table `0x748D98`, enveloppe `MAXW_2d_748d98` -> `psp_1bb944`), branche image `$80` ≠ 0
  (`J_2ad4fc`), sous-état 6 = `psp_1bc300`. Condition supplémentaire : `$3C8(a6)` = 1, posé par `psp_1bc988` (appelé par
  `psp_1bc8bc`, la détection des manips) quand le tampon d'entrées `$3B8` reconnaît une suite : c'est une **suite de coup
  normal de Yun déclenchée par une manip**, `$2AD` comptant les relances (identification exacte du coup : non faite).
- La branche ne compte que si l'**adversaire** a sauté (compteur ≠ 0) et a `$270` arcade ≠ 0 (état aérien de réaction).
  Alors la PSP lui pose `$D6 = 1` (arcade `$24DA2` : objet exclu de la poussée entre joueurs), efface `$270` et `$5D`.
- Upper MAX actuel : l'adversaire garde `$270` et reste « poussable » ; `$5D` est effacé dans les deux cas.
- Visibilité : **rare et probablement discrète** (adversaire touché en l'air pendant cette suite de Yun : placement /
  poussée / retombée différents). Le banc de jour ne passe pas par là : le plan MAX de Yun n'a ni coup sur adversaire
  sauteur ni prise aérienne (`max_Yun_X.tsv` : 22 normaux, 39 spéciaux, 20 supers, 4 lancers au sol).

## 3. Options et risques

| option | risque |
|---|---|
| **appliquer le correctif** (1 octet) | la branche PSP devient vivante : `$D6 = 1` sur l'adversaire. Faible : c'est le code PSP, et l'arcade réécrit `$D6` à l'entrée de plusieurs états (`$29802`, `$29852`, `$29AFE` : `move.b d0,$D6(a6)`) ; aucun natif touché (code du module de Yun seul). Risque résiduel : interaction avec le moteur d'Upper modifié, non mesurée |
| ne rien faire | Yun diffère de la PSP dans ce cas ; la ligne reste parmi les « NON RÉSOLU » et empêche de rendre la liste bloquante sans exception (A2) |

## 4. Essai qui tranche (banc, à faire de jour)

```
cd <workspace>/work/revue_upper_max/banc_coups
cp -a max57 max58b2 && cp ../constr/b2_v161/banc/roms_ro5/sfa3ud/sz3.10b max58b2/roms_ro5/sfa3ud/
( cd max58b2 && find . -type f ! -name MD5_COPIE.txt | sort | xargs md5sum > MD5_COPIE.txt )
export HSFA_AGENT=<agent> REFS=<workspace>/work/v161/fige/a6 MAXMAME=2 \
       LUA_EN_PLUS=<workspace>/work/arbitrages_um/outils/sonde_yun_32d.lua PERSOS=Yun
./banc_max.sh max57 max ; ./banc_max.sh max58b2 max      # puis : croises arcade
grep -rh "^Y32D" essais/max_max57 essais/max_max58b2   # lignes de la sonde dans les log.txt (journal BANC_OUT)
```
Précaution : vérifier d'abord sur un seul essai que `outils/journal.py` ignore les lignes `Y32D` (sinon écrire la sonde
dans un fichier à part : remplacer `_G.BANC_OUT` par `io.open(os.getenv("OUT")..".y32d","a")`).
Valeurs attendues :
- non-régression : `max_Yun_{X,A,V}.tsv` de max58b2 = max57 à la ligne près (défauts MAX 0), croisés et Arcade de Yun idem ;
- sonde : chaque passage `TEST` montre `img32C` (vrai compteur) et `img32D` (champ lu à tort). Sur max57, aucune ligne
  `PRIS` quel que soit `img32C` ; sur max58b2, `PRIS` dès que `img32C ≠ 0` et `img271 ≠ 0`, suivi de `imgD7 = 01`.
- si aucune ligne `TEST` n'apparaît : le banc n'atteint pas le site ; ajouter un essai à la main (J2 = Ryu qui saute sur
  Yun, Yun le touche en l'air avec le normal de la branche `$80 ≠ 0` puis entre la manip) — scénario à écrire d'après le
  relevé du coup sur PSP (PPSSPP, point d'arrêt `0x08804000 + 0x1BC34C`, valeur de `0x305(s1)`).

## 5. Recommandation

**Appliquer le correctif** (référence = PSP ; la source MAX est déjà juste, seul le typage de l'intégration manque ;
1 octet dans le seul code de Yun, champ établi par l'arcade, Upper, la PSP et `champs.tsv`). Le passer dans le même lot
d'essai que B1 (`$1B6B6`) ; critère : banc MAX de Yun identique + sonde `PRIS` présente.


<!-- source: <workspace>/work/arbitrages_um/A2_non_resolus.md -->

## File `<workspace>/work/arbitrages_um/A2_non_resolus.md`

# A2 — Rendre bloquants les « NON RÉSOLU » de la conversion (constat B3)

Défaut proposé : les rendre bloquants (les adresses du moteur le sont déjà depuis la revue, `prepare_max.py` après la l. 763).
Analyse statique du 11/11 sur `<workspace>/work/revue_upper_max/constr/b1_v161` (candidat v161 = copie de banc `max57`).

## 1. Ce que fait le code

- `conv/convertit_max.py:953-954` : une instruction que le convertisseur ne sait pas typer est laissée **telle quelle**
  (disposition arcade) avec « `⚠ CONV NON RÉSOLU : <raison>` » ; `:1489-1493` écrit `prep/conv/non_resolus.tsv`.
- `outils/prepare_max.py:763` : simple `print` (« 9130 réécrites, 29 NON RÉSOLUES, 122/122 adresses du moteur ») ;
  rien ne s'arrête. Seules les adresses du moteur non résolues arrêtent la construction (`:767-769`, sauf
  `CONV_SANS_ADRESSES`).
- Côté PSP : sans objet (c'est une étape de l'intégration).
- Conséquence : un accès non typé lit l'octet voisin (k^1) sans bruit. B2 (Yun `$32D`, voir A1) en est l'exemple.

## 2. Les 29 « NON RÉSOLU » actuels (b1_v161, `prep/conv/non_resolus.tsv` ; n° de ligne = source `prep/src`)

| # | fichier : ligne | instruction | raison du convertisseur | verdict (raison réelle) |
|---|---|---|---|---|
| 1 | moteur_max_main.s:103 | `lea $14(a0),a0` | lea sur base « donnée » | **admis** : `a0` = pas d'animation ; +`$14` = pas suivant (taille du pas, identique arcade / image) |
| 2 | moteur_max_main.s:166 | `ifnd MAX_ALPHA` | taille d'accès inconnue | **faux positif** : directive d'assemblage |
| 3-4 | moteur_max_main.s:170-171 | `clr.l $28(a4)`, `clr.l $2c(a4)` | base `a4` inconnue | **admis** : remise à 0 de 2 longs alignés = mêmes octets `$28-$2F` dans les deux dispositions (zéro invariant) |
| 5 | moteur_max_main.s:218 | `move.b $103(a0),d2` | base `a0` inconnue | **admis** : écrit à la main en disposition image (`$102` arcade = `$103` image : id du perso) |
| 6 | moteur_max_main.s:287 | `move.w 2(a0),d0` | base `a0` inconnue | **admis** : `a0` = entrée de `TAB_VOIX_MAX` (données du bloc MAX, assemblées en 68K natif) |
| 7 | moteur_max_main.s:882 | `tst.w $50(a1)` | base `a1` inconnue | **admis** : accès MOT (les mots restent en place ; arcade `$235E8` `tst.w $50(a1)` : même champ) |
| 8-11 | moteur_max_main.s:1300-1305 | `$2a1(a6)` ×4 (`psp_cf560`, Ingrid) | champ `$2A1` non typé | **admis** : écrit à la main en disposition image ; vérifié : Upper `$328CC`, `$329CC`, `$32A98` = `move.b #8,$2A1(..)` |
| 12-13 | brouillon_eagle.s:79, 85 | `cmpi.b #$10,$102(a1)` ; `movea.l 0(a0,d0.w),a0` | base inconnue | **mort** : intro croisée (Sagat), derrière le `bra` posé par `prepare_max.py:606-620` |
| 14-15 | brouillon_eagle.s:89, 95 | `cmpi.b #$b,$102(a1)` ; `movea.l …` | idem | **mort** : intro croisée (Zangief) |
| 16-17 | brouillon_maki.s:109, 115 | `cmpi.b #$e,$102(a1)` ; `movea.l …` | idem | **mort** : intro croisée (`$0E`) |
| 18-19 | brouillon_yun.s:221, 227 | `cmpi.b #$21,$102(a1)` ; `movea.l …` | idem | **mort** : intro croisée (`$21`) |
| 20 | **brouillon_yun.s:1504** | **`tst.b $32d(a1)`** | champ `$32D` non typé | **DÉFAUT** (B2 / A1) : doit lire image `$32C` |
| 21-22 | brouillon_ingrid.s:173, 179 | `cmpi.b #$19,$102(a1)` ; `movea.l …` | idem | **mort** : intro croisée (`$19`) |
| 23-26 | gestionnaires_main.s:23, 28, 30, 33 | `move.b 0(a0)` ; `lea 20(a0)` ; `move.b 1(a0)` ; `tst.b 8(a0)` | base `a0` inconnue | **admis** : `psp_1b07bc` écrite à la main, boucle en disposition image (en-tête du fichier : drapeaux 1->0, durée 0->1, attaque 9->8) |
| 27-29 | contres_max.s:29, 51, 125 | `move.w #1,CONTRE_DECLENCHE(a5)` | déplacement symbolique | **admis** : symbole résolu ensuite et contrôlé par `assert` (`prepare_max.py:499-506`, `TST.W` de l'image native) ; accès mot |

Bilan : **1 défaut** (n° 20), **10 morts** (intros croisées, vivants seulement si le `bra` saute), **17 admis**
(écrits à la main en disposition image, accès mot, zéros invariants, symbole contrôlé), **1 faux positif** (`ifnd`).
L'ancien défaut `$1B6B6` (B1) n'apparaît plus (corrigé : « 122/122 adresses du moteur »). Avec le correctif A1 : 28 (b2_v161).

Remarque en passant : `re/connaissances/champs.tsv:388` donne « joueur `+$2A0` img:`+$2A0` » ; l'image d'Upper écrit
`$2A1` (n° 8-11 ci-dessus) : la ligne de la base est à revoir (hors de cet arbitrage).

## 3. Effet en jeu

Aucun aujourd'hui en dehors du n° 20 (voir A1). L'enjeu est la **prochaine** source de la session MAX : un nouvel accès
non typé passerait sans bruit et lirait l'octet voisin (même mécanisme que B2).

## 4. Options et risques

| option | risque |
|---|---|
| **liste blanche versionnée + échec sur tout le reste** (proposé) | maintenance : chaque ajout volontaire de la session MAX demande une ligne motivée ; les 10 lignes « mortes » doivent rester liées au `bra` des intros (si on rétablit les intros croisées, ces lignes deviennent des défauts : la liste doit alors cesser de les admettre) |
| échec sur tout « NON RÉSOLU » sans liste | impossible sans réécrire 28 lignes admises ou mortes |
| statu quo (print) | B2 se reproduira sans signal |
| typer davantage dans le convertisseur (base `a0`/`a1` suivie) | plus long ; ne dispense pas d'une liste pour les fonctions écrites à la main |

Forme conseillée de la liste (`ag/conv/non_resolus_admis.tsv`) : `fichier`, `instruction normalisée` (texte avant le
`;`, blancs réduits), `raison du convertisseur`, `nombre attendu`, `verdict` (admis / mort / faux positif), `motif`.
Clé = texte, pas le n° de ligne (les lignes bougent à chaque régénération). Contrôle : l'ensemble des
`non_resolus.tsv` doit être **égal** à la liste (un admis disparu = signal aussi, liste à tenir propre). Pour les 10
lignes mortes : ajouter le contrôle « l'étiquette du rappel 19 commence par `bra` » (déjà fait par `prepare_max.py:613`).

## 5. Essai qui tranche (statique, de jour, sans MAME)

1. Avec la liste et le contrôle : `outils/um.sh` sur la base v161 a6 -> mêmes ROM que `constr/b1_v161` (03c `5e1430ee`,
   04c `83de84d6`, 10b `8c255f0a`) si la ligne n° 20 est dans la liste ; sinon échec nommé « brouillon_yun.s `tst.b $32d(a1)` ».
2. Avec le correctif A1 et la ligne n° 20 retirée de la liste : 10b `295a44eb` (= `constr/b2_v161`), 28 entrées.
3. Essais négatifs (comme `outils/essai_controles.py`) : retirer la ligne `$83` de `types_complement.tsv` -> échec ;
   rendre une ligne admise différente (ajouter un espace) -> pas d'échec (normalisation) ; supprimer le `bra` d'une intro
   -> échec du contrôle des intros.
4. `CONV_SANS_ADRESSES=1B6B6` + interrupteurs v160 (`outils/zero.txt`) : la reconstruction de max55 doit rester possible
   -> prévoir un interrupteur symétrique (`CONV_NON_RESOLUS_LIBRES=1`) pour rejouer les lots anciens.

## 6. Recommandation

**Rendre bloquant, avec une liste blanche** de 28 lignes (17 admises, 10 mortes, 1 faux positif), la ligne de Yun
étant corrigée (A1) plutôt qu'admise. Conforme à « on n'invente rien » : chaque admis cite son motif vérifiable. Aucun
octet ne change (contrôle : ROM = b1_v161 / b2_v161 à l'octet) ; aucun banc nécessaire.


<!-- source: <workspace>/work/arbitrages_um/A3_table_615940.md -->

## File `<workspace>/work/arbitrages_um/A3_table_615940.md`

# A3 — Table `0x615940` : position de l'effet lié, entrées des 4 MAX (constat B4)

Défaut proposé : aligner sur la PSP, après mesure. Analyse statique du 11/11 (outils : `outils/psp_dis.py`,
`outils/refs_va.py`).

## 1. Ce que fait la donnée

Table de couples (dx, dy) en mots, indexée par l'id du perso ×4 ; le même lecteur dans les trois jeux :

| jeu | lecteur | table | index spéciaux |
|---|---|---|---|
| arcade `sfa3ud` | `$82C98-$82CDC` (classe d'objet 7, sous-type 6, état `$82C72`) | `$832A6`, 34 entrées | Vega `$1C` -> `$20` (masqué) / `$21` (griffe, `$10` de sa frame) |
| Upper (v161, `b1_v161`) | image `$33B94-$33BE6` (va `0x175E58-0x176110`), `LEA $ABC80` = PS2 `0x615940` | 42 entrées | Vega -> 40 / 41 |
| PSP EU | `0x7B91C-0x7B9E8` (`lui 0x22 ; addiu 0x5E8`) | `0x2205E8`, 44 entrées | Vega -> `$2A` / `$2B` ; MAX `$26-$29` insérés |

Calcul (identique dans les trois) : objet fils A6, joueur A4 = `$36(A6)` ; `dx, dy = T[id]` ; l'objet prend le côté du
joueur (`$B` arcade / `$A` image / `0xB` PSP) ; `X = X_joueur ± dx` (moins si tourné), `Y = Y_joueur + dy`.

L'objet : classe 7 du réservoir `$FFB000` (table des classes arcade `$3333C`, entrée 7 = `$82A60`), créé par `$82E36`
(1 à 3 objets selon la force `$82` du joueur ; sous-type = `$82`) ; Upper : `UP_82E36` = image `$33D84`. **Le code MAX
l'appelle** : `psp_cf560` (« rémanences + suite », `moteur_max_main.s:1398-1428`) finit par `jmp UP_82E36`, et
`psp_cf560` est appelée par les 4 MAX (Eagle 2 sites, Maki 4, Yun 4, Ingrid 3 ; ex. Yun `psp_1bdf3c` : `moveq #-20,d0 ;
moveq #68,d1 ; bsr psp_cf560`). La PSP fait de même (`0x79144 + 0x7BD2C`). Seul le sous-type 6 (champ `$82` = 6) passe
par l'état qui lit la table.

Valeurs (contrôle d'alignement : natifs 0-`$25` égaux partout ; Vega d'Upper 40/41 = PSP `$2A/$2B` = (36, 96), (-38, 113)) :

| perso (id Upper / PSP) | PSP `0x2205E8` | Upper MAX (`ext_e80000.bin`, copie `$E80B40`) | écart |
|---|---|---|---|
| Eagle `$26` / `$26` | **(-40, 96)** | (-37, 84) = bouche-trou d'origine d'Upper | 3 px en X, 12 px en Y |
| Maki `$27` / `$27` | **(32, 80)** | (-37, 84) | **69 px en X (autre côté du corps)**, 4 px en Y |
| Yun `$2D` / `$28` | **(-16, 72)** | (0, 0) (table agrandie, rien posé) | 16 / 72 px : aux pieds |
| Ingrid `$2E` / `$29` | **(-18, 77)** | (0, 0) | 18 / 77 px : aux pieds |

## 2. Effet en jeu le plus probable

- Qui / quand : les 4 MAX, sur les coups qui appellent `psp_cf560` avec la force / le niveau `$82` = 6 (3 objets créés,
  sous-type 6) ; en X-isme (`$132 < 0`) `$82E36` prend un autre chemin (`$830B6`), non lu ici.
- Quoi : l'effet fils (classe 7, animation `#$14` de la table `$2E50A0`) apparaît au mauvais endroit : **aux pieds** de
  Yun et d'Ingrid au lieu de ~75 px plus haut ; **de l'autre côté du corps** pour Maki ; à peine décalé pour Eagle.
- Visible : oui si l'effet est assez grand pour être vu (quelques images pendant le coup) ; non mesuré. Aucun effet sur
  les natifs.
- Identification exacte du coup et de l'image de l'effet : non faite (statique).

## 3. Options et risques

| option | risque |
|---|---|
| **poser les 4 couples PSP** (lecture directe de l'EBOOT `0x2205E8 + 4 × id PSP`, avec contrôle « entrées 0-`$25` = Upper » comme `0x2190C8`, `integre_max.py:282-295`) | quasi nul : 16 octets de la copie MAX ; homologie prouvée (même lecteur, 38/38 natifs, Vega décalé de 2 de façon cohérente) ; natifs inchangés |
| les ajouter à `tables_id_max.s` (session MAX) | même résultat, une étape de plus ; la session MAX doit les relever (même source) |
| ne rien faire | Yun / Ingrid : effet aux pieds ; Maki : effet de l'autre côté ; écart PSP permanent |

## 4. Essai qui tranche (banc, de jour)

Sonde (`LUA_EN_PLUS`, à écrire sur le modèle de `outils/sonde_yun_32d.lua`) : tap d'opcode sur image **`$33BEA`** (le
`JSR` qui suit l'écriture de `$12/$16`) ; y lire `A4` (joueur), `A6` (objet), `id = $103(A4)`, `mem:read_u16(A6+$12) -
mem:read_u16(A4+$12)`, `mem:read_u16(A6+$16) - mem:read_u16(A4+$16)`, `$A(A4)`.
```
cd <workspace>/work/revue_upper_max/banc_coups
export HSFA_AGENT=<agent> REFS=<workspace>/work/v161/fige/a6 MAXMAME=2 LUA_EN_PLUS=<sonde_615940.lua> PERSOS=Eagle,Maki,Yun,Ingrid
./banc_max.sh max57 max            # avant ;   puis le lot corrigé (copie maxNN)
```
Valeurs attendues (côté non tourné ; signe de dX inversé si `$A ≠ 0`) :
- avant : Eagle et Maki (dX, dY) = (-37, 84) ; Yun et Ingrid (0, 0) ;
- après : Eagle (-40, 96), Maki (32, 80), Yun (-16, 72), Ingrid (-18, 77) ;
- natifs et `max_*.tsv` : identiques à max57 (seule la position d'un objet change ; le banc ne compare pas les positions
  d'objets fils, donc rien d'autre ne doit bouger).
Si la sonde ne voit aucun passage pour un MAX : le plan du banc ne contient pas le coup ; relever sur PPSSPP le coup qui
passe en `0x7B97C` (point d'arrêt, `0x152(s1)` = id MAX) et l'ajouter en essai à la main ; capture comparée PSP / Upper
(`SNAPID`) pour dire si c'est visible.

## 5. Recommandation

**Aligner sur la PSP** : poser Eagle (-40, 96), Maki (32, 80), Yun (-16, 72), Ingrid (-18, 77), lus dans l'EBOOT avec le
contrôle d'alignement sur les natifs. La valeur actuelle est un bouche-trou (Eagle, Maki) ou un zéro non voulu (Yun,
Ingrid) : rien à garder. La mesure ci-dessus confirme la position, elle n'est pas un préalable au choix.


<!-- source: <workspace>/work/arbitrages_um/A4_masques_arcade.md -->

## File `<workspace>/work/arbitrages_um/A4_masques_arcade.md`

# A4 — Masques de l'Arcade 0x61B540 / 0x61B510 (constat B5) — et rappel de 0x615940 (B4)

Analyse statique du 12/11 sur la construction témoin `constr/t6_defaut` (= max57). Relevé exact : `outils/releve_tables.py`
-> `constr/releve_tables_max57.txt` (témoin) et `constr/releve_tables_t5.txt` (interrupteurs à 1).

## 1. Relevé PSP contre Upper MAX (EBOOT EU ULES00235, `cache/psp/BOOT.BIN`, VA = décalage − 0x74)

| table Upper (copie) | PSP | natifs 0-$25 égaux | Eagle | Maki | Yun | Ingrid |
|---|---|---|---|---|---|---|
| 0x615940 (`$E80B40`) | 0x2205E8 | 38/38 (+ Vega 40/41 = PSP 42/43) | PSP (-40, 96) / UM (-37, 84) | (32, 80) / (-37, 84) | (-16, 72) / (0, 0) | (-18, 77) / (0, 0) |
| 0x61B540 combat secret (`$E812F0`) | 0x20B676 | 29/38 (≠ $12 $15 $17 $1E-$23) | **1** / 0 | 0 / 0 | **1** / 0 | 0 / 0 |
| 0x61B4E0 `$13E` = 8 (`$E81290`) | 0x20B6A0 | 36/38 (≠ $12 $14) | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| 0x61B510 `$13E` = $A (`$E812C0`) | 0x20B6CA | 35/38 (≠ $12 $1B $1C) | **0** / 1 | 1 / 1 | 1 / 1 | 1 / 1 |

(UM = Upper MAX max57. Les copies `$E8xxxx` sont en ordre image : octets échangés par mot.) Les revues B4 / B5 sont
confirmées à l'octet ; 0x61B4E0 est déjà aligné.

## 2. Ce que fait le code (carte v161 de t6_defaut)

Préparation du combat d'Arcade, image `$53C80-$53E3E` (va 0x248A50-0x249658), selon `$114(A5)` (n° du combat) :
- `$114` = 4 -> `$13E` = 8, `$162` = 1, masque 0x61B4E0[id] (`$53BE2`) non nul -> `$162` = `$FF` ;
- `$114` = 8 -> `$13E` = $A, `$162` = 1, masque 0x61B510[id] non nul -> `$162` = `$FF` ;
- `$114` = 9 -> adversaire spécial `D1` = 0x61B680[id] (Upper MAX : Eagle `$15`, Yun `$1E` ; Maki, Ingrid `$FF`) ; si
  `D1` ≥ 0 et pas encore rencontré (va 0x251CC0 : bit `D1` de `$140/$144` du joueur) : `$13E` = 4, `$162` = 1 ; si
  `D1` = `$15` (Balrog d'après `max_agrandies.txt`) `$13E` reste 4 ; si `D1` = `$1E` (Juli + Juni : `$D03` = `$1E`,
  `$1103` = `$1F`) `$13E` = 2 ; dans les deux cas, masque 0x61B540[id] (`$53C26`) non nul -> `$162` = `$FF`.
- Lecteurs de `$162` : image `$58F82` et `$590A0` (après une victoire : chargement de la fin si `$162` = 0 et
  `$114` = `$14C` : 1 et `$FF` se comportent pareil) ; image `$59C58` : `TST.B $162 ; BPL` : si `$FF`, `$C(A5)` = 8,
  `$E` = 0, JSR va 0x24DEC0 (autre enchaînement de l'état de jeu) ; sinon `$C` += 2 (suite ordinaire).

Constat : dans Upper, TOUS les natifs qui ont un combat secret dans 0x61B680 (ids 4, 8, 9, $C, $E, $F, $16, $19, $1A,
$1D) ont 1 dans 0x61B540. Eagle et Yun (combat secret `$15` / `$1E`) sont les seuls à 0 : la PSP leur met 1.

## 3. Effet probable en jeu

- Eagle (contre `$15`) et Yun (contre Juli + Juni) : au combat secret, `$162` reste 1 au lieu de `$FF` ; l'Arcade prend
  la suite ordinaire (`$C` += 2) au lieu de la branche `$C` = 8 que prennent la PSP et tous les natifs. Visible : la
  transition autour du combat secret (scène, écran, ordre) ; la fin n'est pas en cause (lecteurs `$58F82` / `$590A0`
  insensibles). Nature exacte de la branche va 0x24DEC0 : non lue (statique), à voir aux captures (E2).
- Eagle au combat `$13E` = $A (9e combat) : `$FF` au lieu de 1 (PSP 0, comme 7 natifs) : il prend la branche `$C` = 8
  là où la PSP ne la prend pas.
- Les tournées Arcade du banc max57 finissent pour Eagle et Yun : pas de blocage ; l'écart est de mise en scène.
- 0x615940 (A3) : effet lié (classe 7, sous-type 6) aux pieds de Yun / Ingrid, de l'autre côté du corps pour Maki.

## 4. Correctif préparé (commit 61f2145 du clone)

`integre_max.donnees()` : `MAX_615940_PSP=1` et `MAX_MASQUES_PSP=1` posent les entrées MAX lues dans l'EBOOT (id PSP
$26-$29) ; empreinte d'alignement contrôlée (liste exacte des natifs qui diffèrent, + Vega pour 0x615940). **À 0 par
défaut** : construction = max57 à l'octet. À 1 : seuls 04c (tables en place, `$ABD18-$ABD1E`, `$B1876`, `$B18A6`) et
`ext_e80000.bin` (copies) changent. Essais : `essais/LISEZMOI.md` E1, E2.


<!-- source: <workspace>/work/arbitrages_um/A6_palettes_effets.md -->

## File `<workspace>/work/arbitrages_um/A6_palettes_effets.md`

# A6 — Palettes d'effets des MAX coupées à 30 (constat B7) : lesquelles, quand, ce qui se verrait

Analyse statique du 12/11 ; relevé : `outils/releve_palettes.py` -> `constr/releve_palettes_max57.txt`.

## 1. Lesquelles

| perso | fichier (`converti/plXX/palettes_effets_module.bin`) | coupées (non nulles) | dont copies de 0-29 |
|---|---|---|---|
| Eagle | 36 palettes | 30-35 (6) | 30, 32, 34 (= 24 / 26 / 28) |
| Maki | 36 | 30-35 (6) | 30, 32, 34 |
| Yun | 36 | 30-35 (6) | 30, 32, 34 |
| Ingrid | 72 | 30-71 (42) | 30, 38 |

Côté PSP, TOUS les natifs ont aussi un bloc d'effets de 36 palettes ou plus (pac `pl00-pl25`, entrée [6]) dont 30-35
sont non nulles et propres à chaque perso ; Upper a des blocs de 30 (quelques ids plus longs, cf. max-palettes.md §4) : les palettes 30+ de
la PSP ne viennent donc pas du jeu d'origine (avec des blocs de 30 qui se suivent, un natif d'Upper qui en lirait une
prendrait celle du perso suivant : le jeu d'origine ne le fait pas).

## 2. Quand le moteur en lit une

Lecteur du bloc par perso : fonction image `$2643C` (l'autre lecteur de 0x700540, image `$41F58`, lit l'entrée fixe
de l'id `$0C`) (va 0x116750 : `LEA 0x700540 ; MOVE.B $103(A6),D2 ; …
ANDI.W #$FF,D0 ; LSL.W #5,D0 ; ADD.W` décalage du perso) = adresse de la palette `D0` du perso, **sans borne**. Ses 18
appelants natifs (image `$260F0-$262EC`, va 0x1149F4-0x115D70, et `$261B0`) sont l'automate des effets de palette du
joueur (`$2A1` / `$2AF`, table T_612b40, 53 états) : n° constants (0, 1, 4, 14), `8 + $129`, ou `D5 + 0 / 1 / $D / 24 /
25` avec `D5` tiré de l'état. Le code MAX (sources de la session MAX) n'appelle pas ce lecteur (aucun `UP_` vers lui dans
`adresses_upper.s`, aucune référence à 0x700540) ; il passe par `$2A1` (ex. `psp_cf560` : `move.b #8,$2a1(a6)`).
Donc : une palette 30+ n'est demandée pour un MAX que si un état de l'automate donne `D5 + 24 / 25 / $D` ≥ 30 pour lui.
Les natifs, avec les mêmes états, ne dépassent pas 29 : c'est **peu probable**, mais non prouvé (états `$2AF` posés par
le code MAX, valeur de `D5`).

## 3. Ce qui se verrait

La zone déplacée met les blocs bout à bout : palette 30 + k d'Eagle = palette k des effets de Maki ; Maki -> Yun ;
Yun -> Ingrid ; Ingrid 30-71 -> fin de la zone : 38 palettes sur 42 nulles (couleurs noires). Un effet MAX qui en
demanderait une aurait les couleurs d'un autre perso MAX, ou serait noir pour Ingrid.

## 4. Préparé (commit 1dd1a18 du clone)

- Coupure gardée par défaut, désormais signalée au journal de construction (« palettes d'effets de X : 36 palettes …
  COUPÉES À 30 (6 non nulles au-delà de 30) ») ; contrôle de portée des décalages s16 de tous les blocs.
- `MAX_PALE_PLEINES=1` (défaut 0) : blocs d'effets MAX entiers (réservation de `MAX_PALE_ZONE` portée de `$A000` à
  `$A800`) ; vérifié : `constr/t7_pale`, palettes 30+ lues = celles du fichier (6/6, 6/6, 6/6, 42/42). Le code MAX après
  la zone bouge (03c, 04c, 06c, 10b, 3 blocs externes changent) : non-régression complète nécessaire avant d'en faire le
  défaut.
- Essai : `essais/LISEZMOI.md` E3 (sonde de `$2643C` : couples (id, n°) demandés, `AU-DELA_DE_30`).
- Pour la session MAX (rien écrit dans `max/`) : `max/notes/max-palettes.md` §4 dit « nombre réellement utilisé :
  inconnu (≤ 36) » ; le résultat d'E3 répond ; si des n° ≥ 30 sont vus, il faudrait que `palettes_effets_module.bin`
  garde le bloc entier (c'est déjà le cas) et que le relevé dise quels effets PSP les utilisent.
