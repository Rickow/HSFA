# RAPPORT — dégâts de la greffe Arcade (ro9a18) contre Upper, persos en version ZERO 3

31/10/2026. Mesure seulement, aucun correctif. Dossier : `work/banc_greffe_upper/` (outils, journaux, `resultats/`).

## 1. Réponse

- **Greffe = Hyper, partout.** À phase égale de la cadence turbo, la greffe donne exactement les mêmes dégâts, le même
  nombre de touches, les mêmes dégâts reçus par J1 et les mêmes états de la victime qu'Hyper seul : **0 écart sur
  11 312 comparaisons** (5 656 essais × 2 phases). La greffe ne touche pas au moteur de combat.
- **Greffe / Hyper contre Upper** : 5 362 essais identiques sur 5 656 (94,8 %). Les écarts restants sont ceux d'**Hyper
  lui-même**. 50 sont **robustes** (vus dans les 3 phases de la cadence) ; 244 **dépendent de la cadence** (une phase au
  moins d'Hyper donne le résultat d'Upper : un appui tombe un tour plus tôt ou plus tard).
- **Mode Arcade (point 3)** : la vie de départ est `$90` des deux côtés. Les quatre DAMAGE LEVEL donnent les mêmes
  dégâts, essai par essai, dans la greffe et dans Upper. Les DIFFICULTY 0 et 4 aussi. DIFFICULTY 7 donne les mêmes
  dégâts sur les touches communes, environ −15 % sur les coups du joueur, des deux côtés.
- **Avis** : en ZERO 3, la greffe est cohérente avec Upper autant qu'Hyper l'est ; elle n'ajoute aucun écart. Les écarts
  restants (§4) sont à chercher dans Hyper (données de l'Anthology ou traduction), pas dans la greffe.

## 2. Méthode

- Constructions : Upper v153 `references/v153/ro5` (03c `0b8ecca2`) ; Hyper v153 `references/v153/ro9` (03c `a5f7fae0`) ;
  greffe `greffe_arcade/constructions/ro9a18_fige` (03c `0dc7eb69`). Fork MAME `cps2f` (pilote `sfa3hx`) ; variables de la
  greffe reprises de `greffe_arcade/outils/lance_ro9a.sh` (module `greffe` de `lance.sh`, copie de `banc_coups/lance.sh`).
- Banc : `banc_coups/lua/banc_coups.lua` tel quel (lecture seule). VERSUS à 2 joueurs, J1 = perso testé, J2 = Ryu
  A-ISM passif. Une sauvegarde d'état est prise au combat stable et rechargée avant chaque coup (jamais `-state`).
  Upper : `$102` / `$132` imposés. Hyper et greffe : sélection par les manettes (colonne ZERO 3 + isme).
- Persos : les 33 natifs (`$00-$11`, `$15-$23`), ismes X, A et V, soit 99 lancements par construction.
- Plan, identique pour les 3 constructions :
  - les lignes du tableau des coups (spéciaux, supers, lancers, Alpha Counter : `banc_coups/outils/plan.py`) ;
  - les 22 normaux de la palette générique ;
  - Evil Ryu, Guile, Fei-Long, Dee Jay et T. Hawk n'ont pas de lignes au tableau : palette entière (85 commandes).
- Mesure (`lua/degats.lua`) : chaque écriture de la vie `$50` de J1 / J2 est journalisée, ce qui ne dépend pas de la
  cadence. On en tire, par essai : dégâts J2, touches J2, dégâts J1, touches J1, coup de J1 à chaque touche (`$6 $7 $AA`).
  On relève aussi la suite des états `$5 $6` de J2.
- Vérifications :
  - 2e passage complet (`essais2`) : les 3 constructions sont **déterministes** (0 essai instable) ;
  - **3 phases de cadence** : Hyper décalé de 1 et 2 images (`essais_h1`, `essais_h2`), greffe décalée de 1
    (`essais_g1`) ;
  - Upper rejoué avec une fenêtre ×4/3 (`essais_u43`), voir §3.

## 3. Deux pièges du banc (à garder)

1. **Phase de la cadence turbo.**
   - Hyper (et la greffe) tournent en turbo : 4 tours de jeu pour 3 images, période 3. Le banc ne peut pas les forcer
     en NORMAL.
   - Un essai dépend de la phase de cette cadence au moment de la sauvegarde.
   - La greffe démarre parfois une image plus tôt qu'Hyper (Dee Jay X : SAVE 1567 contre 1568). Au 1er passage, cela
     donnait **9 faux écarts greffe ≠ Hyper** (Dee Jay X ×7, Juli X ×2, dont Cannon Spike de Juli 13 contre 19).
   - Rejeu avec sauvegarde décalée (`lua/banc_coups_decale.lua`, `DECALE=n`, `essais/decale/`) : greffe décalée de k =
     Hyper décalé de k + 2, plan entier identique.
   - `outils/phases.py` aligne chaque lancement : décalage 0 pour 97 lancements, 2 pour Dee Jay X et Juli X.
2. **Fenêtre d'observation en images.**
   - La fenêtre vaut 150 images, et 300 pour les supers et lancers. Hyper en turbo y joue 4/3 de tours de plus.
   - Des coups longs étaient donc **coupés dans Upper**. Exemple, Final Atomic Buster de Zangief : J1 est encore en
     super à l'image 346, et la touche finale de 31 n'est jamais vue. Même chose pour Murderer Chain de Birdie, les
     prises de R. Mika…
   - Upper est rejoué avec une fenêtre ×4/3 (`essais/plans_u43` : mêmes appuis, même durée en tours qu'Hyper). Les
     écarts robustes passent de 80 à 50.

## 4. Résultats VERSUS

Classes (`resultats/phases.tsv`, détail des écarts : `resultats/phases_ecarts.tsv`) :
- OK : greffe = Hyper (à phase égale) et Hyper = Upper dans les 3 phases ;
- Hyper ≠ Upper robuste : aucune des 3 phases d'Hyper ne donne le résultat d'Upper ;
- Hyper ≠ Upper selon la cadence : certaines phases seulement.

### 4.1 Par perso

| perso | essais (X+A+V) | qui touchent | OK | Hyper ≠ Upper robuste | Hyper ≠ Upper selon la cadence | greffe ≠ Hyper |
|---|---|---|---|---|---|---|
| Adon | 138 | 115 | 138 | 0 | 0 | 0 |
| Akuma | 203 | 129 | 201 | 2 | 0 | 0 |
| Balrog | 135 | 105 | 128 | 1 | 6 | 0 |
| Birdie | 144 | 126 | 141 | 3 | 0 | 0 |
| Blanka | 152 | 109 | 148 | 0 | 4 | 0 |
| Cammy | 150 | 127 | 141 | 3 | 6 | 0 |
| Charlie | 145 | 132 | 143 | 1 | 1 | 0 |
| ChunLi | 144 | 123 | 125 | 8 | 11 | 0 |
| Cody | 173 | 138 | 173 | 0 | 0 | 0 |
| Dan | 146 | 108 | 142 | 1 | 3 | 0 |
| DeeJay | 255 | 215 | 237 | 0 | 18 | 0 |
| Dhalsim | 169 | 102 | 163 | 0 | 6 | 0 |
| EHonda | 152 | 128 | 149 | 0 | 3 | 0 |
| EvilRyu | 255 | 167 | 229 | 4 | 22 | 0 |
| FeiLong | 255 | 175 | 231 | 7 | 17 | 0 |
| Gen | 146 | 125 | 130 | 2 | 14 | 0 |
| Guile | 255 | 206 | 232 | 0 | 23 | 0 |
| Guy | 159 | 114 | 153 | 0 | 6 | 0 |
| Juli | 138 | 123 | 126 | 0 | 12 | 0 |
| Juni | 174 | 135 | 165 | 0 | 9 | 0 |
| Karin | 159 | 144 | 150 | 0 | 9 | 0 |
| Ken | 155 | 118 | 152 | 0 | 3 | 0 |
| MBison | 149 | 104 | 138 | 3 | 8 | 0 |
| RMika | 172 | 136 | 163 | 3 | 6 | 0 |
| Rolento | 169 | 123 | 166 | 3 | 0 | 0 |
| Rose | 140 | 112 | 137 | 0 | 3 | 0 |
| Ryu | 165 | 135 | 156 | 3 | 6 | 0 |
| Sagat | 144 | 134 | 143 | 0 | 1 | 0 |
| Sakura | 156 | 132 | 151 | 0 | 5 | 0 |
| Sodom | 156 | 128 | 144 | 0 | 12 | 0 |
| THawk | 255 | 183 | 231 | 6 | 18 | 0 |
| Vega | 168 | 114 | 162 | 0 | 6 | 0 |
| Zangief | 180 | 159 | 174 | 0 | 6 | 0 |
| **total** | **5656** | **4424** | **5362** | **50** | **244** | **0** |


États de la victime : sur les 4 130 essais OK qui touchent, aucun état de J2 de 4 tours ou plus ne manque d'un côté
(greffe / Hyper / Upper). Greffe contre Hyper image par image : 31 essais montrent un état d'un seul tour de plus ou de
moins (`0200` / `0204`, transitions), avec les mêmes touches et les mêmes dégâts. C'est la visibilité d'un état bref dans
l'image, pas une différence de jeu.

### 4.2 Écarts Hyper ≠ Upper robustes (50 essais, greffe = Hyper partout)

Format : dégâts / touches sur J2 (« J1-n/t » = dégâts reçus par J1). d0 / d1 / d2 = phases de la cadence d'Hyper.

|---|---|---|---|---|---|---|---|---|
| Akuma | A | L692.2 | Alpha Counter (→ + MP+MK) | 2/1 J1-9/1 | 4/3 / 4/3 / 4/3 | 4/3 / 4/3 | touches | 2 → 2 1 1 |
| Akuma | A | L692.3 | Alpha Counter (→ + HP+HK) | 2/1 J1-9/1 | 4/3 / 4/3 / 4/3 | 4/3 / 4/3 | touches | 2 → 2 1 1 |
| Balrog | A | L755.3 | Dash Straight (← (charge) → + HP) | 14/1 | 15/1 / 15/1 / 15/1 | 15/1 / 15/1 | degats | 14 → 15 |
| Birdie | A | L783.1 | Bull Revenger (↓↘→↓↘→ + LP) | 32/2 | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 | touches | 16 16 → — |
| Birdie | A | L783.2 | Bull Revenger (↓↘→↓↘→ + MP) | 48/3 | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 | touches | 16 16 16 → — |
| Birdie | A | L783.3 | Bull Revenger (↓↘→↓↘→ + HP) | 64/4 | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 | touches | 16 16 16 16 → — |
| Cammy | A | L692.1 | Alpha Counter (→ + LP+LK) | 2/1 J1-9/1 | 2/1 / 2/1 / 2/1 | 2/1 / 2/1 | J1 | 2 → 2 |
| Cammy | A | L692.2 | Alpha Counter (→ + MP+MK) | 2/1 J1-9/1 | 2/1 / 2/1 / 2/1 | 2/1 / 2/1 | J1 | 2 → 2 |
| Cammy | A | L692.3 | Alpha Counter (→ + HP+HK) | 2/1 J1-9/1 | 2/1 / 2/1 / 2/1 | 2/1 / 2/1 | J1 | 2 → 2 |
| Charlie | A | L845.2 | Sonic Break (← (charge) → ← → + MP) | 6/1 | 7/1 / 7/1 / 7/1 | 7/1 / 7/1 | degats | 6 → 7 |
| ChunLi | A | L692.1 | Alpha Counter (→ + LP+LK) | 4/1 J1-9/1 | 0/0 J1-9/1 / 4/1 / 0/0 J1-9/1 | 0/0 J1-9/1 / 4/1 | touches | 4 → — |
| ChunLi | A | L692.2 | Alpha Counter (→ + MP+MK) | 4/1 J1-9/1 | 0/0 J1-9/1 / 4/1 / 0/0 J1-9/1 | 0/0 J1-9/1 / 4/1 | touches | 4 → — |
| ChunLi | A | L692.3 | Alpha Counter (→ + HP+HK) | 4/1 J1-9/1 | 0/0 J1-9/1 / 4/1 / 0/0 J1-9/1 | 0/0 J1-9/1 / 4/1 | touches | 4 → — |
| ChunLi | A | L868.1 | Kiko Sho (↓↘→↓↘→ + LP) | 6/1 | 12/2 / 22/4 / 22/4 | 12/2 / 22/4 | touches | 6 → 6 6 |
| ChunLi | A | L868.2 | Kiko Sho (↓↘→↓↘→ + MP) | 23/4 | 18/3 / 29/5 / 29/5 | 18/3 / 29/5 | touches | 7 6 5 5 → 7 6 5 |
| ChunLi | A | L868.3 | Kiko Sho (↓↘→↓↘→ + HP) | 39/7 | 34/6 / 41/7 / 41/7 | 34/6 / 41/7 | touches | 7 7 5 5 5 5 5 → 7 7 5 5 5 5 |
| ChunLi | X | L862.2 | Hyakuretsu Kyaku (- + MK) | 13/1 | 6/1 / 6/1 / 6/1 | 6/1 / 6/1 | degats | 13 → 6 |
| ChunLi | X | N19 | normal arrière + MK | 13/1 | 6/1 / 6/1 / 6/1 | 6/1 / 6/1 | degats | 13 → 6 |
| Dan | A | L917.2 | Hissho Burai Ken (↓↙←↓↙← + MK) | 38/5 | 30/4 / 30/4 / 30/4 | 30/4 / 30/4 | touches | 7 7 8 8 8 → 7 7 8 8 |
| EvilRyu | A | N75 | double demi-cercle arrière + LK | 0/0 | 14/1 / 14/1 / 14/1 | 14/1 / 14/1 | touches | — → 14 |
| EvilRyu | A | N76 | double demi-cercle arrière + HK | 58/12 | 15/3 / 15/3 / 15/3 | 15/3 / 15/3 | coup_different | 6 6 5 5 5 5 5 5 4 4 4 4 → 5 5 5 |
| EvilRyu | V | N75 | double demi-cercle arrière + LK | 6/1 | 12/1 / 12/1 / 12/1 | 12/1 / 12/1 | coup_different | 6 → 12 |
| EvilRyu | V | N76 | double demi-cercle arrière + HK | 15/2 | 12/3 / 12/3 / 12/3 | 12/3 / 12/3 | coup_different | 8 7 → 4 4 4 |
| FeiLong | A | N75 | double demi-cercle arrière + LK | 28/8 | 0/0 / 5/1 / 5/1 | 0/0 / 5/1 | touches | 4 4 4 4 3 3 3 3 → — |
| FeiLong | V | N72 | double quart arrière + HK | 4/1 | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 | touches | 4 → — |
| FeiLong | V | N75 | double demi-cercle arrière + LK | 14/1 | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 | touches | 14 → — |
| FeiLong | V | N76 | double demi-cercle arrière + HK | 17/2 | 12/1 / 12/1 / 12/1 | 12/1 / 12/1 | coup_different | 13 4 → 12 |
| FeiLong | X | N72 | double quart arrière + HK | 4/1 | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 | touches | 4 → — |
| FeiLong | X | N75 | double demi-cercle arrière + LK | 19/1 | 6/1 / 6/1 / 6/1 | 6/1 / 6/1 | coup_different | 19 → 6 |
| FeiLong | X | N76 | double demi-cercle arrière + HK | 22/2 | 18/1 / 18/1 / 18/1 | 18/1 / 18/1 | coup_different | 18 4 → 18 |
| Gen | A | L975.2 | Shitenshu (↓↙←↓↙← + MP) | 34/8 | 33/7 / 34/9 / 33/7 | 33/7 / 34/9 | touches | 1 1 1 11 5 5 5 5 → 1 1 11 5 5 5 5 |
| Gen | A | L975.3 | Shitenshu (↓↙←↓↙← + HP) | 44/10 | 43/9 / 44/11 / 43/9 | 43/9 / 44/11 | touches | 1 1 1 1 1 11 7 7 7 7 → 1 1 1 1 11 7 7 7 7 |
| MBison | A | L1132.1 | Knee Press Nightmare (← (charge) → ← → + LK) | 7/1 | 14/2 / 14/2 / 14/2 | 14/2 / 14/2 | touches | 7 → 7 7 |
| MBison | A | L1132.2 | Knee Press Nightmare (← (charge) → ← → + MK) | 17/2 | 25/3 / 25/3 / 25/3 | 25/3 / 25/3 | touches | 9 8 → 9 8 8 |
| MBison | A | L1132.3 | Knee Press Nightmare (← (charge) → ← → + HK) | 37/4 | 45/5 / 45/5 / 45/5 | 45/5 / 45/5 | touches | 10 9 9 9 → 10 9 9 9 8 |
| RMika | A | L692.1 | Alpha Counter (→ + LP+LK) | 4/1 J1-9/1 | 4/1 / 4/1 / 4/1 | 4/1 / 4/1 | J1 | 4 → 4 |
| RMika | A | L692.2 | Alpha Counter (→ + MP+MK) | 4/1 J1-9/1 | 4/1 / 4/1 / 4/1 | 4/1 / 4/1 | J1 | 4 → 4 |
| RMika | A | L692.3 | Alpha Counter (→ + HP+HK) | 4/1 J1-9/1 | 4/1 / 4/1 / 4/1 | 4/1 / 4/1 | J1 | 4 → 4 |
| Rolento | A | L692.1 | Alpha Counter (→ + LP+LK) | 1/1 J1-9/1 | 0/0 J1-9/1 / 0/0 J1-9/1 / 0/0 J1-9/1 | 0/0 J1-9/1 / 0/0 J1-9/1 | touches | 1 → — |
| Rolento | A | L692.2 | Alpha Counter (→ + MP+MK) | 1/1 J1-9/1 | 0/0 J1-9/1 / 0/0 J1-9/1 / 0/0 J1-9/1 | 0/0 J1-9/1 / 0/0 J1-9/1 | touches | 1 → — |
| Rolento | A | L692.3 | Alpha Counter (→ + HP+HK) | 1/1 J1-9/1 | 0/0 J1-9/1 / 0/0 J1-9/1 / 0/0 J1-9/1 | 0/0 J1-9/1 / 0/0 J1-9/1 | touches | 1 → — |
| Ryu | A | L692.2 | Alpha Counter (→ + MP+MK) | 4/1 | 4/1 J1-9/1 / 4/1 J1-9/1 / 4/1 J1-9/1 | 4/1 J1-9/1 / 4/1 J1-9/1 | J1 | 4 → 4 |
| Ryu | A | L692.3 | Alpha Counter (→ + HP+HK) | 4/1 | 4/1 J1-9/1 / 4/1 J1-9/1 / 4/1 J1-9/1 | 4/1 J1-9/1 / 4/1 J1-9/1 | J1 | 4 → 4 |
| Ryu | A | L1227.2 | Shinku Tatsumaki Senpu Kyaku (↓↙←↓↙← + MK) | 42/8 | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 | touches | 6 6 5 5 5 5 5 5 → — |
| THawk | A | N67 | double quart avant + LK | 0/0 | 3/1 / 3/1 / 3/1 | 3/1 / 3/1 | touches | — → 3 |
| THawk | A | N73 | double demi-cercle arrière + LP | 0/0 | 3/1 / 3/1 / 3/1 | 3/1 / 3/1 | touches | — → 3 |
| THawk | V | N67 | double quart avant + LK | 0/0 | 3/1 / 3/1 / 3/1 | 3/1 / 3/1 | touches | — → 3 |
| THawk | V | N73 | double demi-cercle arrière + LP | 0/0 | 3/1 / 3/1 / 3/1 | 3/1 / 3/1 | touches | — → 3 |
| THawk | V | N74 | double demi-cercle arrière + HP | 13/1 | 11/1 / 11/1 / 11/1 | 11/1 / 11/1 | coup_different | 13 → 11 |
| THawk | X | N67 | double quart avant + LK | 0/0 | 3/1 / 3/1 / 3/1 | 3/1 / 3/1 | touches | — → 3 |

Lecture :
- **Alpha Counter** (Akuma, Cammy, Chun-Li, R. Mika, Rolento, Ryu ; A-ISM surtout) : échange de coups. Le banc les sait
  instables (garde de proximité une image plus tard, BANC-COUPS §5). À ne pas compter comme dégâts.
- **Écarts de dégâts à touches égales** :
  - Dash Straight de Balrog (A, HK) : 14 contre 15 ;
  - Sonic Break de Charlie (A, 2e variante) : 6 contre 7 ;
  - Chun-Li X, arrière + MK et Hyakuretsu Kyaku martelé : 13 contre 6 (même classe d'état `0a02` : sans doute un autre
    normal qui sort) ;
  - Shitenshu de Gen : une petite touche de 1 en moins dans Hyper.
- **Supers qui touchent différemment** :
  - Bull Revenger de Birdie (A) : ne touche pas dans Hyper (Upper 2 à 4 touches de 16) ;
  - Kikosho de Chun-Li (A) : 1 / 4 / 7 touches dans Upper, 2-4 / 3-5 / 6-7 dans Hyper selon la phase ;
  - Hissho Burai Ken de Dan (A, MP) : 5 touches contre 4 (déjà vu au §170 : « la super ne part pas ») ;
  - Knee Press Nightmare de Bison (A) : une touche de plus dans Hyper ;
  - Shinku Tatsumaki Senpu Kyaku de Ryu (A, MK) : ne touche pas dans Hyper.
- **Palette des persos ajoutés par Upper** (doubles quarts et demi-cercles) : Evil Ryu, Fei-Long et T. Hawk. Le super
  qui sort n'est pas le même, ou ne sort pas. Leur version ZERO 3 d'Hyper n'est donc pas celle d'Upper (données ou
  reconnaissance des commandes).
- Les coups de la 1re liste (Murderer Chain, The Birdie, Final Atomic Buster, Daydream Headlock, Final Destruction,
  Daikyo Burning…) **ne sont plus des écarts** une fois la fenêtre allongée. Le banc des coups les classe d'ailleurs
  « Upper = arcade ».
- Les 244 écarts « selon la cadence » sont surtout des coups à manip serrée de la palette : charges bas-haut,
  demi-cercles, avant-arrière-avant. Ils viennent aussi de l'Alpha Counter et de l'Orochi Kudaki de Honda. Ils
  traduisent le turbo d'Hyper, pas les dégâts.

## 5. Mode Arcade : vie de départ, DAMAGE LEVEL, DIFFICULTY (point 3)

Outils :
- `lua/banc_arcade.lua` (copie de `banc_coups.lua`, `ARCADE=1`) : J1 = Ryu ZERO 3 A-ISM, 1er combat du mode Arcade ;
- graine du hasard `$FF80AE` imposée : même 1er adversaire des deux côtés (E. Honda, `$18`) ;
- DAMAGE (`$FF80A0`) et DIFFICULTY (`$FF80A1`) écrits avant le début du mode ;
- plan `Ryu_A` (60 essais) ; ordinateur coupé pendant les essais (`$124` de J2 = 0) ou actif.

Analyse : `outils/arcade_analyse.py` → `resultats/arcade.md`. Série `essais/arcade2`. La 1re série `essais/arcade` est
fausse : sauvegarde prise J1 en réaction ; à supprimer.

| mesure | Upper v153 | greffe ro9a18 |
|---|---|---|
| vie au 1er image du combat (J1 / J2, `$50` / `$52`) | `$90` / `$90` | `$90` / `$90` |
| difficulté courante `$FF80BF` | = DIFFICULTY (copie au début du mode) | = DIFFICULTY |
| DAMAGE 0 / 1 / 2 / 3 (DIFF 4, ordi. coupé), somme des 60 essais | 771 / 834 / 897 / 1 020 | 771 / 834 / 897 / 1 020 (essai par essai identique) |
| exemple Hadoken HP (L52.1) | 18 / 20 / 22 / 25 | 18 / 20 / 22 / 25 |
| DIFFICULTY 0 / 4 (DAMAGE 1) | 834 / 834 | 834 / 834 (identique) |
| DIFFICULTY 7 (DAMAGE 1) | 690 (91 touches) ; Hadoken 20 → 17, jab 6 → 5 | mêmes valeurs sur les touches communes ; 8 essais touchent d'un seul côté (position de l'ordinateur à la sauvegarde) |

Lecture du code (images 68K dans `re/`, unidasm) :
- la fonction de dégâts est la même dans les trois ROM : Upper `$5300-$5452`, Hyper `$7D60-$7E92`, greffe `$E3xx-$E4A6` ;
- DAMAGE LEVEL, lu seulement là (`move.b ($A0,A5)`) : 0 = −1/8, 1 = ×1, 2 = +1/8, 3 = +1/4, conforme aux mesures ;
- le handicap Arcade (Upper `$53EC`, Hyper `$7E24`, greffe `$E442`) :
  - table `$A2810` / `$99E40` / `$BEE40`, identique ;
  - Hyper et la greffe ajoutent le test `BTST #4,$D2(A1)` (bit ZERO 3) : sans effet pour les persos ZERO 3 ;
- la greffe porte bien la copie DIFFICULTY → difficulté courante d'Upper (`$B6758`, en plus de celle d'Hyper `$16666`).

L'ordinateur actif n'est pas comparable : l'IA et la cadence changent ce qui se passe dès la 1re image (60 / 60
essais différents). Aucune conclusion de dégâts n'en est tirée.

## 6. Fichiers

- `ETAT.md` : journal de la session.
- `lance.sh` : copie de `banc_coups/lance.sh`, plus le module `greffe`.
- `lua/` :
  - `degats.lua` : écritures de la vie ;
  - `banc_coups_decale.lua` : copie, `DECALE=n` ;
  - `banc_arcade.lua` : copie, mode Arcade ;
  - `dbg.lua`.
- `outils/` :
  - `banc_gu.py` : orchestrateur (variables `ESSAIS`, `PLANS`, `LUA_BANC`) ;
  - `analyse.py` : un passage ;
  - `combine.py` : deux passages ;
  - `phases.py` : classement final, alignement de phase ;
  - `arcade_gu.py`, `arcade_analyse.py` : série Arcade.
- `resultats/` :
  - `phases.tsv` et `phases_ecarts.tsv` : RÉFÉRENCE ;
  - `phases_alignement.tsv`, `phases_resume.txt` ;
  - `final*.tsv` : stabilité des 2 passages ;
  - `essais.tsv` / `ecarts.tsv` / `par_perso.tsv` : 1er passage brut ;
  - `arcade.md`.
- Rejouer :
  - `MAXMAME=5 python3 outils/banc_gu.py tous X,A,V` ;
  - `ESSAIS=essais_h1 DECALE=1 LUA_BANC=$PWD/lua/banc_coups_decale.lua python3 outils/banc_gu.py tous X,A,V hyper` (de même
    h2 / g1) ;
  - `PLANS=essais/plans_u43 ESSAIS=essais_u43 python3 outils/banc_gu.py tous X,A,V upper` ;
  - puis `python3 outils/phases.py`.
