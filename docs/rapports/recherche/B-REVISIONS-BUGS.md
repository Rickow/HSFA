# B — Révisions, bugs et différences de versions : oracles et liste de contrôle pour HSFA

Synthèse du 2026-10-20, pour le projet HSFA (`<workspace>/SFA-Anthology-PS2-mods/`). Elle croise :
- le dépôt : `README.fr.md`, `docs/journal/ETAT-DES-LIEUX.md`, `docs/rapports/INDEX-HYPER.md`, `DEFAUTS-HYPER.md`,
  `ECARTS-UPPER.md`, `OPTIONS.md`, `CARTE-MODULES.md`, `ADRESSES-MAX-UPPER.md`, `docs/methodes/oracle-et-non-regression.md`,
  `src/hsfa/revision.py`, HANDOFF §96 ;
- la recherche documentaire : notes `03` à `12` (les `_verif` priment), `chapitres_v2/03`, `04`, `05`, `06`, `10`, et le
  guide BradyGames transcrit (`scratchpad/guide/transcript_guide_sfa_anthology.md`, p. 3 à 5) ;
- trois lectures faites pour cette synthèse : le pilote MAME `cps2.cpp` actuel (révisions et CRC des ROM programme), le
  wikitexte de SuperCombo (pages *Alpha*, *Alpha 2/FAQ*, *Alpha 3/FAQ*), et `strygo/arcade-patches/data/patches.json`
  (notices des restaurations, octobre 2026).

Rien n'a été modifié dans le dépôt.

**Confiance**
- **A** : source primaire ouverte. ROM et pilote MAME, Capcom, interview, guide officiel BradyGames.
- **B** : source secondaire ouverte et fiable : SuperCombo, arcade-history, Wikipédia.
- **C** : source unique non revérifiée : wiki de fans, ancien texte, extrait de moteur, notice de patch amateur.
- **D** : inférence de ma part.

**Colonne « Dépôt »**
- **connu** : déjà établi dans le dépôt ;
- **partiel** : le dépôt a le fait, mais pas son interprétation ou sa vérification ;
- **nouveau** : absent du dépôt.

**Conventions de RAM** (celles du dépôt) : A5 = `$FF8000` ; structure J1 = `$FF8400`, J2 = `$FF8800` (A5 + `$400` /
`$800`) ; champs en numérotation arcade/PS2 ; dans la traduction, un octet est à l'adresse XOR 1. Exemple :
`$FF891E` = jauge de J2.

---

## 0. En bref

1. **L'Anthology ne propose pas la révision qui sert d'oracle à SFA3.** Selon le guide officiel, le SECRET OPTION
   de *Alpha 3* n'offre que **98/06/29** et **98/07/27**, cette dernière par défaut. Or le banc compare à **USA 980904**
   (`sfa3ud`). [A, nouveau]
2. **Le test du §96 (« ro3 suit 980904 ») ne prouve pas ce qu'il dit.** `revision.py` ne cherche que dans le premier
   Mo du programme (`U[:0x100000]`, ROM 03 et 04). Ce sont précisément les ROM **régionales** de SFA3 : leur CRC change
   à chaque région.
   - Le test oppose donc l'USA au Japon, pas 980629 à 980904.
   - Il n'a jamais vu la **980727**.
   - Or les ROM 05-09 changent **à chaque révision** (CRC MAME, §2.4).
   - À refaire : protocole au §3. [A + D, nouveau]
3. **Chaque jeu a des révisions documentées par MAME**, avec ce que chacune change quand on le sait (§2). Elles
   fournissent des **sondes de version**, des comportements qui ne valent que pour une révision :
   - Sodom imparable et Kubikari de Guy (*Zero*) ;
   - Soul Illusion de Rose et Alpha Counter d'Adon (*Zero 2*) ;
   - les « Gold Changes » (*Zero 2 Alpha*) ;
   - les deux bugs de Karin (*Zero 3* 980629).

   Elles permettent de dire quelle révision, ou quel « arrangement », suivent les versions ZERO / ZERO 2 / ALPHA
   d'Hyper (§8). [A/B, nouveau]
4. **Le roster EX d'Hyper ZERO 2 est celui de la branche américaine d'*Alpha 2*** : EX Zangief, EX Dhalsim et Evil
   Ryu.
   - L'*Alpha 2* d'arcade n'a **jamais** eu d'EX Bison ni d'EX Sagat ; ils naissent avec *Zero 2 Alpha*.
   - Les cases `$58/$59` de la grille Start en colonne ZERO 2 désignent donc des versions qui n'ont jamais existé, et
     leurs tables pointent sur Ryu.
   - L'histoire soutient l'hypothèse d'un **défaut de données de Capcom** dans Hyper. Une vérification sur PCSX2 reste
     nécessaire. [A/B + D, partiel]
5. **CFC2 (septembre 2025) a eu le défaut que HSFA risque pour MAX.** Le Head Press et le Somersault Skull Diver de
   Bison ne touchaient pas Eagle, Maki, Yun et Ingrid, ni la Sardine Beach Special de R. Mika.
   - Or `ECARTS-UPPER` §5 et §9 relève une **table de M. Bison par adversaire**, 3 × 32 mots dans l'arcade, 3 × 40 dans
     Upper (`0x433E50`).
   - C'est le cas d'école à étendre pour `$26-$29`, et la séquence de test est toute trouvée (§5.3). [A + D, nouveau]
6. **Les différences régionales sont aussi de jeu, pas seulement de texte.**
   - Les restaurations de strygo rétablissent, pour *Zero*, *Zero 2* et *Zero 2 Alpha*, les « computer opponents,
     two-player damage and factory settings » japonais.
   - Les 825 répliques, le sang (Regulation), les lieux, la musique de la Dramatic Battle et les noms comptent pour la
     voie B (greffe du mode Arcade d'Upper). [A/C, nouveau]
7. **Upper (NAOMI) a retiré le crouch cancel** et réduit l'étourdissement du Tatsumaki de Ryu.
   - On ne sait pas si l'**Upper de l'Anthology** (`ro5`, CPS-2 « arrangé ») le fait aussi.
   - Les 629 écarts du dépôt ne regardent que le code, et la routine d'atterrissage `$2AF7A` y est **identique**.
   - À mesurer (§5.1). [A/B + D, nouveau]
8. **Les bugs connus d'Hyper** se rangent en trois familles (§7) :
   - **défauts du jeu PS2** probables : `$58/$59`, tables de 40 entrées lues par `$102`, bit 6 de `$D3` ;
   - **défauts de traduction** corrigés : plafond de jauge (`CMPMM`), exception du TRAINING ; la famille `CMPX` reste
     ouverte ;
   - **écarts voulus par HSFA** : voix SFA1/SFA2.

   Aucune source publique ne parle des premiers. La recherche ne confirme que deux points : le **mode rose banni en
   tournoi** (infinis) et des **zones de coup du mode rose décalées** pour Vega et Zangief.
9. **Deux inventaires manquent au dépôt** :
   - la liste complète des **18 différences de *Zero 2*** et ses lecteurs ;
   - les **interrupteurs CUSTOMIZE** (rangées d'étoiles) de SFA3, d'Upper et d'Hyper, avec l'octet de version
     `$BB` / `$FF80BA`, que `OPTIONS.md` voit « aussitôt écrasé ».

   Ce sont eux qui disent quelle révision le programme traduit applique par défaut (§3, §7). [A + D, nouveau]

---

## 1. Les oracles et ce que chacun prouve

| oracle | jeu MAME / source | ce qu'il prouve | limites | dépôt |
|---|---|---|---|---|
| **Hyper PS2 sous PCSX2** | ISO `SLUS-21317` | ce que Capcom a livré : seul oracle de la **fidélité de la traduction** d'Hyper | pas de mode Arcade ; aucune donnée publique ; versions mélangées par construction | connu (états PCSX2, PINE) |
| arcade *Zero* | `sfzjr2` 950605, `sfzjr1` 950627, `sfzj` 950727 (Japon) ; `sfau` 950627 (seul USA) ; `sfzb` 951109 | ce que doit être une version **ZERO** « arcade » ; sondes de révision | carte RAM différente de SFA3 : adresses à établir | nouveau |
| arcade *Zero 2* / *Alpha 2* | `sfz2jr1` 960227, `sfz2j` 960430 ; `sfa2ur1` 960306, `sfa2u` 960430 (USA) ; `sfa2` 960229 (Europe) | versions **ZERO 2** ; branche USA (EX Zangief, EX Dhalsim, Evil Ryu) | idem | nouveau |
| arcade *Zero 2 Alpha* | `sfz2alj` 960805 ; `sfz2alr1` 960805, `sfz2al` 960826 (Asie) ; `sfz2alh` / `sfz2alb` 960813 | versions **ALPHA** hors Cammy ; « Gold Changes » | pas de Cammy ; Hyper ALPHA vient de *Gold* console | nouveau |
| arcade *Zero 3* | `sfz3jr2` 980629, `sfz3jr1` 980727, `sfz3j` 980904 ; `sfa3ud` (Phoenix USA 980904) | **SFA3 (`ro3`)**, et base des ZERO 3 d'Upper et d'Hyper | l'Anthology n'offre pas 980904 (§3) | partiel (`sfa3ud` seul) |
| Anthology `ro1` / `ro8` / `ro6` / `ro4` / `ro2` | modules de l'ISO | ce que l'Anthology appelle ZERO, ALPHA 2, Gold ; leurs SECRET OPTION | non traduits, non lancés ; arrangés par défaut | partiel (`CARTE-MODULES`) |
| **Upper Anthology (`ro5`)** | traduit | oracle de la **voie B** et de la couche Upper d'Hyper | « Upper façon NAOMI » sur base CPS-2, pas l'Upper NAOMI | connu |
| Upper NAOMI | `sfz3ugd` (GDL-0002), et CFC2 (2025) | ce qu'était vraiment *Upper* (crouch cancel, Tatsumaki, boss jouables) | émulé ; code inaccessible (Enigma, selon l'ancien texte) | nouveau |
| *Alpha 3 MAX* (PSP) | transcription du dépôt | les 4 persos MAX et leurs interactions (Head Press, Sardine Beach) | — | connu (`max/`, `CONV-MAX`) |
| restaurations de strygo | `patches.json` (octobre 2026) | inventaire des écarts régionaux ; *Gold* de l'Anthology **reconstruit sur CPS-2** (`sfa2-gold`, rc7) | travail de fans, à vérifier dans MAME ; pas de code publié | nouveau |

Règle à ajouter à `oracle-et-non-regression.md` §1 : pour Hyper, une différence avec l'arcade n'est un défaut **de
traduction** que si PCSX2 ne la montre pas. Sinon, c'est un choix ou un défaut **de Capcom (2006)**, que l'on documente
et qu'un interrupteur pourra éventuellement corriger.

---

## 2. Révisions arcade datées : ce que change chacune

### 2.1 *Street Fighter Zero / Alpha* (1995)

Généalogie par les CRC des ROM programme de MAME (03 et 04 régionales et corrigées ; 05 change une fois ; 06 jamais).

| build | jeux MAME | ROM 04 / 05 | ce qui change (source, confiance) | Anthology `ro1` | dépôt |
|---|---|---|---|---|---|
| tests en salle (printemps 1995) | non conservé | — | roulade au relevé, remplacée par la roulade de récupération (Funamizu, *All About* vol. 11) — A | — | nouveau |
| juste avant la sortie | non conservé | — | mode Auto sans limites ; ensuite : 8 gardes auto par manche, jauge plafonnée au niveau 1, pas d'annulation normal → super (GAME Watch d'après *Gamest* n° 147) — A/B | — | nouveau |
| **950605** | `sfar3`, `sfzar1`, `sfzjr2` | `0c436d30` / `1f363612` | combos qui re-étourdissent ; **HK de Sodom imparable** (guide BradyGames p. 3) — A | 95/06/05ver | partiel (dates seules) |
| **950627** | `sfar2`, **`sfau`** (seul USA), `sfza`, `sfzjr1`, `sfzhr1` | `5f99e9a5` / `0810544d` | mêmes bugs ; retouches cosmétiques, dont le **cri de Dan quand il projette** ; version **recommandée** par le guide — A | 95/06/27ver | partiel |
| 950718 | `sfar1`, `sfzh` | `bb90acd5` / idem | non documenté — | absent | nouveau |
| **950727** | `sfa`, `sfzj`, `sfzbr1` | `8b73b0e5` / idem | **étourdissement du Kubikari de Guy presque divisé par deux** ; imparable de Sodom retiré ; retouches (guide) — A | **95/07/27ver, défaut** (« most recent ») | partiel |
| 951109 | `sfzb` | `8d9b2480` (= CPS Changer) | « Capcom's November fixes for **guard behavior** and **Rose's crouching heavy kick** » (notice de la restauration strygo) — C | absent | nouveau |

Constantes de *Zero* utiles comme oracle (guide p. 24, SuperCombo, Itsuno) :
- **40 points d'étourdissement pour tous**, +5 à chaque nouvel étourdissement dans la manche — A ;
- supers presque toutes imparables si l'adversaire ne garde pas avant le flash, avec des exceptions (720 de Sodom,
  super de pied d'Adon, supers de Birdie, Tatsu de Ryu, Aura Soul Throw et Soul Illusion de Rose) — B ;
- le **LK debout de Sagat** reste imparable du bout de sa portée « even in the final version » ; l'Anthology le corrige
  par défaut (« arranged version ») — B ;
- **bug de l'Alpha Counter de Rose** : roulé vers l'arrière, il laisse Rose dans un état aérien buggé. Une fois par
  partie, au 1er round ou après un round perdu. Révision non précisée — B ;
- Tiger Cannon de niveau 1-2 de Sagat suivi d'un Tiger Knee qui fait tomber — B ;
- Dan, dans *Zero* arcade, **recycle les voix d'autres persos**. Sur PS et Saturn, il a une voix propre, et l'Anthology
  propose de passer à la « nouvelle voix » par un réglage en étoiles — A/B.

### 2.2 *Street Fighter Zero 2 / Alpha 2* (1996)

| build | jeux MAME | ROM 05-08 | ce qui change | Anthology | dépôt |
|---|---|---|---|---|---|
| **960227** | `sfz2jr1` (Japon), `sfz2a` (Asie) | 05 `98e8e992`, 06 `5b1d49c0`, 08 `0fe8585d` | **invincibilité de la Soul Illusion de Rose** : ses ombres font des coups aériens interdits (boule de feu aérienne qui ne touche pas, Soul Throw aérien, Alpha Counter aérien invincible) — B | `ro2` 96/02/27ver | partiel |
| 960229 | `sfa2` (Europe), `sfz2n` (Océanie) | 05 `4b442a7c` | même bug — B | absent (les données de `ro8` en sont proches, `CARTE-sfa2` §1.2) | partiel |
| 960304 | `sfz2br1`, `sfz2h` | 07 et 08 propres | bug de Rose corrigé — B | absent | nouveau |
| **960306 USA** | `sfa2ur1` | jeu « sz2u » propre jusqu'en 06-08 | **branche américaine** : Evil Ryu, EX Zangief, EX Dhalsim (choisis par Capcom USA, *SSM* n° 12) ; bug de Rose corrigé ; carte en **Turbo 2** et chrono **Slow** par défaut — A/B | `ro8` **96/03/06ver, recommandée** par le guide (« very close to the original Arcade » ; mais Evil Ryu y perd le CC « blowout » à toute distance) ; `ro2` aussi 96/03/06ver | partiel |
| **960430 USA** | `sfa2u` | 03-05 changées | Soul Illusion encore bridée : Rose « perd beaucoup de ses coups normaux en saut » (guide) ; **AC poing d'Adon qui touche très facilement** (léger renfort, SuperCombo, découverte de « Raf ») ; **version de référence des données d'images de SuperCombo** — A/B | `ro8` **96/04/30ver, défaut** ; `ro2` 96/04/30ver | partiel |
| 960430 Japon | `sfz2j` | 05/06/08 = Brésil 960531 | non documenté ; Free Select 2 par défaut — B | `ro2` | nouveau |
| 960531 | `sfz2b` | — | Soul Illusion réduite à MP et MK en saut — B | absent | nouveau |

Bugs d'*Alpha 2*, toutes révisions (SuperCombo FAQ) — B :
- « Valle CC » (CC bas imparable) ;
- inversion de garde après un CC ;
- High Knockdown juggle après CC ;
- Tengu Walk glitch de Sodom ;
- environ 9 % des spéciaux qui ne sortent pas si l'on tient la 1re direction (« Variable Input Window ») ;
- coups moyens accroupis qui frappent bas ;
- auto-roll et juggle glitches de Dhalsim ;
- **showboating** : on bouge sans fin après le K.O. ;
- **Shiraha Catch de Sodom** qui laisse l'adversaire en mode CC indéfiniment ;
- Bull Horn de Birdie dans un CC qui finit une manche.

L'AC poing de Bison est « invincible and unblockable (version-specific) », sans dire laquelle.

### 2.3 *Street Fighter Zero 2 Alpha* (1996) et *Alpha 2 Gold*

MAME : Japon `sfz2alj` 960805 (six ROM programme « szaj » propres) ; Asie `sfz2alr1` 960805 et `sfz2al` 960826 (seules
03-04 diffèrent) ; `sfz2alh` / `sfz2alb` 960813. **ROM graphiques, Z80 et QSound identiques à *Zero 2*** (mêmes CRC).
Pas de version USA ni Europe. — A

Changements (SuperCombo « Gold Changes », valables pour *Z2A* et *Gold*) — B, sauf mention :

| domaine | *Zero 2* | *Z2A* / *Gold* | dépôt |
|---|---|---|---|
| Custom Combo | 3 boutons (PPK / PKK) | **HP+HK** ; plus d'invincibilité pendant le gel | connu (`INDEX-HYPER` §4.2 : ALPHA = `$4400`, ZERO 2 = `$379 & $77`) |
| Alpha Counter | 1 niveau | **1,5 niveau**, sauf en Auto (guide p. 58, ja.wikipedia) — A/B | nouveau |
| gain de jauge | — | réduit au démarrage de certains spéciaux (Kikoken 4 → 2, Sonic Boom 5 → 2) ; touché 3 → 2 | nouveau |
| supers à projectile | — | invincibilité selon le niveau ; 1-2 coups de moins contre un adversaire en l'air | nouveau |
| provocations | — | celles d'Akuma et de Rolento frappent (2 pts) ; K.O. sur provocation → **icône « 1-Up » de *Side Arms*** | nouveau |
| annulation | — | normaux de ≥ 11 images de démarrage : fenêtre de 8 images vers un spécial | nouveau |
| showboating | possible | **corrigé** (déjà corrigé sur les PS et Saturn de *Zero 2*) | nouveau |
| étourdissement | 0,5-3 s | **1,5-5 s** (corrige aussi la sortie de stun pendant « The Birdie ») | nouveau |
| Rose | Soul Spiral des clones 12-14 pts | 1 pt ; Soul Piede (→ + HK) ; bonus après absorption réduit et absent en CC (guide p. 58) ; bugs de mise à l'échelle corrigés | nouveau |
| Sodom | Shiraha → CC infini ; Tengu Walk après une super | corrigés ; Tengu Walking en reversal | nouveau |
| Sagat | — | Angry Scar ; Tiger Genocide plus dur en combo (*All About* vol. 16, selon SuperCombo — C) ; Fake Roundhouse 5 → 8 images | nouveau |
| autres | — | Guy : Bushin Musou Renge ; Ken : Knee Strike, Target Combo, Shoryu Reppa niv. 3 + 16 images d'invincibilité ; Birdie : Bull Horn en plusieurs coups ; Charlie : Somersault Shell parable en l'air ; Chun-Li : Yosokyaku orientable ; Adon : normaux ralentis, zones vulnérables agrandies ; Akuma : Shakunetsu en CC bien moins fort, provocation qui frappe (guide) | nouveau |
| après un CC | roulade possible | plus de roulade (High Knockdown supprimé) | nouveau |

Ajouts de *Z2A* :
- EX Ryu, Ken, Chun-Li, Sagat et Bison, en plus d'EX Zangief, EX Dhalsim et Evil Ryu ;
- une Sakura de couleur alternative ;
- les modes Survival, Dramatic Battle et Shin Gouki ;
- le camion de Sodom façon *Alpha 2* et les couleurs des persos du CPU sur les boutons de pied ;
- le jeu est bâti sur **le programme nord-américain** (ja.wikipedia). — A/B

*Gold* console (*Street Fighter Collection*, 1997) : *Z2A* plus Cammy (venue de *X-Men vs. SF*), sans Dramatic
Battle. L'Anthology mélange les deux : Dramatic Battle de *Z2A*, Cammy dans tous les modes avec histoire et fin. Le
module `ro6` est daté **97/10/23** (date console). — A/B, partiel

### 2.4 *Street Fighter Zero 3 / Alpha 3* (1998)

Généalogie des ROM programme (pilote MAME actuel, lu pour cette synthèse) — **A, nouveau** :

| build | jeux MAME | ROM 03-04 | ROM 05-09 | ROM 10 |
|---|---|---|---|---|
| 980616 « SAMPLE » | `sfa3us` | propres | propres (`sz3-usam_*`) | propre |
| **980629** | `sfz3jr2` (Japon), `sfa3ur1` (USA), `sfa3hr1`, `sfa3b` ; `sfz3ar1` (Asie 980701) | régionales | `9b21518a e7a6c3a7 ec4c0cfd 5c7e7240 c5589553` | `a9717252` |
| **980727** | `sfz3jr1` (Japon seul) | régionales | **toutes différentes** (`05964b7d 78ce2179 398bf52f 866d0588 2180892c`) | **= 980629** |
| **980904** | `sfa3`, `sfa3u`, `sfz3j`, `sfz3a`, `sfa3h` ; Phoenix `sfa3ud` | régionales | **toutes différentes** (`57fd0a40 f6305f8b 6eab0f6f 910c4a3b b29e5199`) | `deb2ff52` |

Ce qui change :
- **980629 → suite** : en X-ISM, **Karin** pouvait faire sa super *Kanzuki-ryū Kōō Ken* (sa 2e super, interdite en
  X-ISM), et sa **projection normale en mode Mazi** pouvait faire **99 %**. Corrigé ensuite (arcade-history) — B.
  Une autre source situe le second bug en Saikyō et lui ajoute l'Izuna Drop de Vega (la griffe), environ 90 % « sur
  les premières cartes » (atwiki, non ouvert) — C.
- **980629** : selon le guide, proche de la version par défaut, avec quelques bugs curieux, pour la plupart
  visuels (guide BradyGames p. 3) — A.
- **980727** : selon le guide, d'autres petits bugs corrigés ; c'est le réglage par défaut et celui qu'il conseille
  (guide BradyGames) — A. C'est la **version par défaut de l'Anthology**.
- **980904** : version finale, seule européenne ; base des hacks *Challenger's Edition* (USA) et de la restauration de
  strygo (Japon) ; aucun changement documenté — A/C.
- **Toutes révisions** : **couleurs de Sodom en X-ISM fautives**, corrigées par le hack *Challenger's Edition*
  (« Sodom Palette Fixes For Xism »). Les autres bugs ne sont pas datés : reset invincibility glitch, infinis de
  Cody, de Rolento et de Blanka V-ISM, infini de Balrog V-ISM **seulement côté J1** — B/C.
- **Test en salle** : le **Jaguar Kick fort d'Adon** (coup de pied normal en X-ISM) était un coup moyen impossible à
  garder accroupi (ja.wikipedia) — B. On ne sait pas si `sfa3us` (SAMPLE 980616) le garde.
- Le hack *Training Edition* de 0xZERO3 est bâti sur **980629 JAPAN** et ajoute un analyseur qui se lance « quand le
  jeu se réinitialise » : indice de resets sur cette révision — C/D.

Anthology `ro3` : **98/06/29ver** et **98/07/27ver (défaut)**, selon le guide, p. 3. Le dépôt n'a pas relevé ces dates
dans `ro3` (`CARTE-MODULES` ne couvre pas `ro3/ro5/ro9`). À lire dans `decomp/ro3_textes.txt`, ainsi que les dates
d'Upper et d'Hyper, si elles existent. — **nouveau**

### 2.5 *Zero 3 Upper* (NAOMI, février 2001) — voir §5

### 2.6 Les interrupteurs de révision de l'Anthology : récapitulatif

| module | jeu | dates (SECRET OPTION, R2 sur GAME OPTION) | défaut | recommandé (guide) | dépôt |
|---|---|---|---|---|---|
| `ro1` | *Alpha* | 95/06/05, 95/06/27, 95/07/27 | la plus récente (95/07/27) | **95/06/27** ; Turbo 2, dégâts 2 | connu (dates) ; défaut nouveau |
| `ro2` | *Zero 2* (Japon, inaccessible en US) | 96/02/27, 96/03/06, 96/04/30 | ? | — | connu |
| `ro8` | *Alpha 2* (export) | 96/03/06, 96/04/30 | 96/04/30 | **96/03/06** ; 5 étoiles, Turbo, dégâts 2 | connu (dates) ; défaut nouveau |
| `ro4` | *Zero 2 Alpha* (arcade, inaccessible en US) | 96/08/05 | — | — | connu |
| `ro6` | *Zero 2 Dash / Alpha 2 Gold* | 97/10/23 (date console) | — | — | connu |
| `ro3` | *Alpha 3* | **98/06/29, 98/07/27** | **98/07/27** | 98/07/27 ; 2 étoiles, Turbo, dégâts 2 | **nouveau** |
| `ro5` / `ro9` | Upper / Hyper | ? | ? | — | **nouveau** (à lire) |
| `ro7` | *Pocket Fighter* | 97/09/01, 97/09/04 | — | — | connu |

À noter :
- `ro2` (Japon) propose **96/03/06**, qui n'existe dans MAME qu'en **USA**. Les dates de l'Anthology ne reproduisent
  donc pas une ROM régionale précise ; ce sont des étiquettes de jeux de réglages (§3) — D.
- Le guide distingue deux menus cachés. `OPTIONS.md` §1.1 les confond (« SECRET OPTION donne accès aux EXTRA
  OPTION ») :
  - **R2** sur GAME OPTION = **SECRET OPTION** : dates, plus CUSTOMIZE (rangées d'étoiles) ;
  - **R1** sur GAME OPTION = **EXTRA OPTION**.

  Le CUSTOMIZE couvre, selon le guide : « Super Combo shadow colors, character voices, properties on certain actions,
  or bugs that were removed in previous versions ». — A, nouveau

---

## 3. Quelle révision suit le SFA3 traduit, et comment le savoir

**Constat sur `src/hsfa/revision.py` (§96)** :
- il construit `imgs = {'USA': U[:0x100000], 'JPN': J[:0x100000]}`, soit les **ROM 03 et 04 seules** ;
- il ne garde une fonction que si elle ressemble à plus de 50 % à l'une des deux images (`if max(sc.values()) < 0.5:
  continue`) : les fonctions des ROM 05 à 10 sont donc écartées sans bruit ;
- les 13 fonctions « plus proches de l'USA » peuvent être du **code régional** ; elles ne prouvent rien sur la
  révision ;
- la 980727 n'est pas testée.

**Ce qui est acquis quand même** : la non-régression (42/42 commandes, 32/32 fins) passe contre `sfa3ud`. Sur tout ce
que ces scénarios exercent, ro3 se conduit comme 980904. Les écarts de révision peuvent se cacher ailleurs : Karin,
modes Mazi et Saikyo, cas cosmétiques.

**Protocole proposé** (aucun calcul lancé ici) :

| étape | quoi | jeu de référence | mesure |
|---|---|---|---|
| 1 | Programmes déchiffrés de `sfz3jr2` (980629), `sfz3jr1` (980727) et `sfz3j` (980904), même méthode que `sfa3ud_prog.bin` ; Phoenix `sfz3jr2d` pour 980629 | MAME | 3 images de 4 Mo |
| 2 | **Diff Japon ↔ Japon** par fonction, sur `$100000-$3FFFFF` (ROM 05-10) et sur 03-04 : la région ne change pas, donc tout écart est une révision | — | liste « fonctions changées 0629 → 0727 → 0904 » |
| 3 | Pour chaque fonction changée, chercher l'homologue dans `ro3` (`layout_pairs.json`, alignement de `ECARTS-UPPER`) et classer : = 0629, = 0727, = 0904, ou **deux variantes sous un test** (interrupteur de révision) | `ro3_usa_prog68k.bin` | tableau par fonction |
| 4 | Chercher les lecteurs de **`$BB(A5)`** (`$FF80BA` en 68K), l'octet de version d'`OPTIONS.md`, et des octets CUSTOMIZE, dans `ro3`, `ro5` et `ro9` | traduction | sites `BTST/CMP` |
| 5 | Lire la valeur par défaut que la traduction pose au démarrage (table de défauts : `$A6xx` dans SFA3 ; `$9EBC`, table `$14B560` dans Hyper) | banc | octet `$FF80BA` à l'image 1 000 |
| 6 | Sondes de jeu (ci-dessous) sur `sfz3jr2`, `sfz3jr1` et `sfa3ud`, puis sur la traduction | MAME, `commandes.lua` | issue de chaque sonde |

**Sondes de révision SFA3** :

| sonde | séquence | attendu 980629 | attendu 980727 et 980904 | confiance |
|---|---|---|---|---|
| Karin, X-ISM, Kanzuki-ryū Kōō Ken | Karin X-ISM, jauge pleine, commande de la 2e super | sort | ne sort pas | B |
| Karin, mode Mazi, projection normale | Mazi (MP+MK + Start), projection sur un mannequin à pleine vie ; lire `$50` de J2 | environ −99 % | normal | B (C pour Saikyo et Izuna Drop) |
| Sodom X-ISM, palette | Sodom X-ISM, capture de la palette du perso (`sz3.09c`, palettes dès `0x2C0D2`) | fautive | fautive (fix CE) | B/C |
| Adon X-ISM, HK sauté | mannequin accroupi en garde | gardé (le moyen n'existait qu'en test ; à voir sur `sfa3us`) | gardé | B |

Les mêmes sondes, passées sur **Upper (`ro5`)** et **Hyper ZERO 3**, disent quelle base ZERO 3 Capcom a prise pour
eux.

---

## 4. Différences régionales Japon / export

| point | Japon | export (USA/Europe) | source, confiance | effet pour HSFA | à vérifier, et comment | dépôt |
|---|---|---|---|---|---|---|
| répliques de victoire *Zero 3* | **825**, dont **625 propres à l'adversaire** ; choix d'une autre réplique en tenant Start + bouton | **8 génériques** par perso | strygo (C), tcrf (C), arcade-history (B) | voie B : quelles répliques porte la couche Arcade d'Upper US (`ro5`) ? | compter les entrées des tables de répliques de `ro3` et `ro5` (statique), comparer à `sfa3u` (8) et `sfz3j` (825) | nouveau |
| répliques *Zero 2 Alpha* / *Gold* | 452, selon l'adversaire et la vie restante | 4 au hasard (*Z2A* Asie) | strygo (C) | Hyper n'a pas d'écran de réplique (`VICTOIRE.md`) | — | partiel |
| sang / « Regulation » (*Zero 3*) | Regulation **OFF** par défaut : sang rouge, effets complets de défaite et de fin | réglage absent ou forcé | strygo (C), tcrf (C) | interrupteur CUSTOMIZE « 自主規制 » relevé par *beep-on* (C) | trouver le drapeau dans `ro3`, `ro5` et `ro9` ; capture d'un coup (couleur du sang) sur `sfz3j` et `sfa3ud`, puis sur la traduction | nouveau |
| sang *Zero 2* / *Alpha 2* | rouge | **blanc** | strygo (C) | Hyper ZERO 2 et ALPHA | capture au coup, Hyper PCSX2 contre `sfz2j` et `sfa2u` | nouveau |
| musique de la Dramatic Battle (*Zero*) | instrumental de 『恋しさと せつなさと 心強さと』 (droits JASRAC, 30 yens par carte, morceau de 2 min 03) | **thème de Bison** ; idem sur CPS Changer, PS et Saturn | Funamizu, *All About* vol. 11 (A), ja.wikipedia (B) | l'Anthology JP l'a en piste cachée du Sound Test ; le disque US ? | chercher le flux dans le `Y_DATA` US (table ADX de `ro1` : Y97-131) | nouveau |
| noms des lieux | 24 lieux détaillés (*Zero 3*) ; noms précis (*Zero 2*) | pays seul ; « Secret Point 48106 » laissé vide | arcade-history (B), history.dat (B) | Hyper : « Secret Point 31580 » (ja.wikipedia) | — | nouveau |
| noms des persos | Vega = dictateur, Balrog = griffe, M. Bison = boxeur ; Gouki ; Nash ; Z-ISM ; ZERO Counter | M. Bison, Vega, Balrog ; Akuma ; Charlie ; A-ISM ; Alpha Counter | MAME, ja.wikipedia (A/B) | **piège de lecture** des sources japonaises (§9) | — | connu (`ro1` occidental, `ro2` japonais) |
| CPU, dégâts à deux joueurs, réglages d'usine | propres au Japon | autres | strygo pour *Zero*, *Zero 2* et *Z2A* (« Computer opponents, two-player damage and factory settings as in the Japanese version ») — C | Hyper n'est qu'un VERSUS : **les dégâts à 2 joueurs** des versions anciennes comptent | même coup, même perso, en VERSUS : `$50` perdu sur `sfz2alj` contre `sfz2al`, puis Hyper PCSX2 | nouveau |
| garde Auto (*Zero*) | Auto **par défaut** | Manuel | strygo (C) | Hyper : `$118` (AUTO) | — | partiel |
| vitesse et chrono par défaut (*Alpha 2*) | Free Select 2 ; chrono Normal (≈ 1 min) | USA 960306 : **Turbo 2**, chrono **Slow** (≈ 1 min 15) | SuperCombo FAQ (B) | défauts PS2 de `OPTIONS.md` (vitesse 2 = TURBO2) | — | partiel |
| *Zero 3* (strygo) | « original difficulty and **Turbo 1** defaults » | autres | C | idem | lire les défauts EEPROM des deux jeux dans MAME (menu de test) | nouveau |
| écran d'ouverture (*Alpha*) | — | « Recycle It, Don't Trash It! » | history.dat (B) | — | — | nouveau |
| pose de victoire de Birdie (*Zero 2*, *Z2A*) | 3e pose | remplacée | strygo (C) | — | — | nouveau |
| persos secrets (*Zero 2*) | Chun-Li tenue SF2, Shin Gouki (CPU) | + **Evil Ryu, EX Zangief, EX Dhalsim** (USA seulement : branche « sz2u ») | MAME CRC (A), SuperCombo (B), *SSM* n° 12 (A) | **Hyper ZERO 2 = branche USA** (`$55`, `$56`, `$57`) | §7 | partiel |
| écran-titre et titres affichés (Anthology JP) | les jeux arrangés gardent le titre de base | — | ja.wikipedia (B) | interrupteur « 17:(ALL) タイトル画面 ダッシュ/アレンジ » de `ro2` | — | connu |

---

## 5. *Zero 3* arcade → Upper → MAX → CFC2

### 5.1 Upper NAOMI (février 2001) contre *Zero 3* CPS-2

| changement | source, confiance | dans l'Upper de l'Anthology (`ro5`) ? | vérification | dépôt |
|---|---|---|---|---|
| **crouch cancel** (着地キャンセル) retiré, et avec lui les infinis du V-ISM | ENWIKI (B, sans note), Famitsu 2025 (A) | **inconnu**. Indice contraire : la routine sol/atterrissage `$2AF7A` est **identique** à l'arcade (`ADRESSES-MAX-UPPER`) — D | séquence V-ISM classique : saut en contre, atterrissage annulé en accroupi, puis enchaînement. `sfa3ud` contre `ro5` ; mesurer l'image où l'on peut agir après l'atterrissage | nouveau |
| Tatsumaki de Ryu : étourdissement réduit | ja.wikipedia (B) | inconnu ; les 629 écarts ne voient que le code | **diff des données d'attaque** (32 o par coup, octet `+$0C` = étourdissement) entre `ro3` et `ro5`, pour tous les persos communs ; le Tatsumaki de Ryu sert de **vérité de terrain** du diff | nouveau (le dépôt dit : valeurs non vues, §0.4) |
| V-ISM affaibli | namu.wiki (C, non ouvert) | inconnu | même diff de données, plus la durée et le coût du VC | nouveau |
| Fei Long, Dee Jay, T. Hawk, Guile, Evil Ryu (case propre), Shin Akuma ; Final Bison jouable (désactivable par réglage) ; Juni, Juli et Balrog jouables avec leur histoire | ja.wikipedia, GAME Watch 2001 (A/B) | oui (36 persos ; EX Balrog `$25`) | — | connu |
| EX Balrog = le Balrog (boxeur) **de l'arcade *Zero 3*** ; le Balrog normal a les normaux ajoutés sur PS | ja.wikipedia (« AC版『ZERO3』性能のM.バイソンは…EXバイソン ») — B | `$25` utilise le code de `$15` avec des animations par variante (`$1FE`) | `commandes.lua` sur Balrog de `sfa3ud` contre EX Balrog `$25` de `ro5` : suites d'états identiques attendues | **nouveau** (le dépôt a le mécanisme, pas la sémantique) |
| décors : Karin sur le *Queen of Victory* ; décors propres aux ajouts | arcade-history (B) | oui (décors d'Upper) | — | connu |
| mode choisi après le perso (Normal, Mazi, Saikyō, Classical) ; Dramatic, Survival et Final Battle sans attente | GAME Watch 2001 (A) | oui | — | connu |
| défaite contre le boss = mauvaise fin, sans continue (seuls *Zero 3* et Upper arcade) | ja.wikipedia (B) | ? | partie Arcade d'Upper perdue contre Final Bison : continue ou mauvaise fin ? (balayage des fins) | nouveau |
| 1/60 s de retard, attribué à une émulation de la CPS-2 | ja.wikipedia (C, sans source) | sans objet (CPS-2 traduit) | — | nouveau |
| ce que l'Anthology appelle Upper : « la *Zero 3* CPS-2 arrangée façon NAOMI » ; titre « Zero 3 » par défaut | ja.wikipedia (B) | confirmé de l'intérieur (programme 68000 de SFA3 étendu) | — | connu |
| 1re entrée de la table des manipulations supprimée (`$2D5E2`) ; `$32F` supprimé ; palettes `$128` ; renumérotation d'animations (Adon, Guy, R. Mika, Zangief) ; intro de Charlie contre Guile | dépôt | — | identifier le coup de l'entrée supprimée (comparer aux changements publics) | connu |

### 5.2 MAX (PSP, 2006) et GBA

- GBA (*Zero 3↑*, 27/09/2002) :
  - Eagle, Maki et Yun, sans fins propres (sauf Bison et Evil Ryu) ;
  - **EX Bison supprimé** ;
  - voix partagées, transposées en hauteur ;
  - les persos de *CvS2* n'ont pas de ZERO Counter différencié selon l'ISM.

  — A/B
- PSP (*Zero 3↑↑* / *MAX*) :
  - Ingrid (de *Capcom Fighting Jam*) ;
  - fins propres pour Yun, Maki et Eagle ;
  - décors empruntés : Yun → Fei Long, Maki → Guy, Eagle → Birdie ;
  - bug de sauvegarde sur Memory Stick ≥ 4 Go, non corrigé.

  — A/B

  Pour HSFA (`$26-$29`), les décors empruntés donnent l'oracle de la table perso → décor.

### 5.3 CFC2 (2025) : options EX et bugs, ce qu'il faut en tirer

| fait | source, confiance | leçon pour HSFA | vérification | dépôt |
|---|---|---|---|---|
| Upper NAOMI ; version anglaise « built using the Japanese version's data » ; Shin Akuma et Final Bison jouables | Capcom via Nintendo Life (A) | CFC2 est l'oracle du comportement de l'Upper **NAOMI** (crouch cancel, Tatsumaki) | jouer les séquences du §5.1 sur CFC2 (enregistrement vidéo à 60 i/s) | nouveau |
| option EX « 着地キャンセル » (réactive le crouch cancel), apparemment | Famitsu (A, « 模様 ») | le bug corrigé devient un réglage : modèle pour un interrupteur HSFA | — | nouveau |
| 12/06/2025 : « Reduced instances where some moves would not hit the opponent » | EventHubs (B) | — | — | nouveau |
| 07/08/2025 : Eagle, Maki, Yun et Ingrid en option (désactivés en ligne) ; Mode Select On / Off / **Original** | notes Capcom via EventHubs (A) | — | — | nouveau |
| **09-10/09/2025 : « Fixed an issue where M. Bison's Head Press and Somersault Skull Diver attacks would not hit Eagle, Maki, Yun, or Ingrid » ; idem pour la Sardine Beach Special de R. Mika ; répliques de Juni corrigées** | notes Capcom via EventHubs (A) | **même famille de défaut que les tables de 32 → 40 entrées**. Le dépôt connaît déjà la **table de M. Bison « par adversaire »** (`ECARTS-UPPER` §5 et §9 : arcade `$48DC0` 3 × 32 mots, Upper `0x433E50` 3 × 40, sites `$47B3E LEA $40(A0)` → `LEA $50`). Elle est à étendre à 42 ou 44 entrées pour `$26-$29`. Chercher la même chose dans le code de R. Mika | après intégration MAX : Bison Head Press (charge bas, haut + K), puis suite Skull Diver (P), contre chacun des 4 MAX, à 3 distances ; R. Mika Sardine Beach Special contre les 4. **Attendu : touche** comme contre Ryu. Oracle : MAX PSP (transcription), à défaut CFC2 ≥ septembre 2025 | **nouveau** (la table est connue, le lien non) |

---

## 6. Portages qui ont pu contaminer l'Anthology ou Hyper

| portage | différence | source, confiance | risque pour l'Anthology / Hyper | à vérifier | dépôt |
|---|---|---|---|---|---|
| *Alpha* PS / Saturn (1995-1996) | Dan : **nouvelle voix** (l'arcade recyclait) ; **ombres des supers** de couleur différente ; jauge de super **inversée**, « MAX » réduit ; Saturn : projection de victoire au « baseball », **imparable de Sodom réintroduit**, nom décalé sous le portrait | ja.wikipedia, *CVG* n° 173, SuperCombo (A/B) | le CUSTOMIZE de `ro1` couvre voix et ombres (guide) : les deux variantes sont **dans** l'Anthology | Hyper ZERO : Dan (voix), ombres des supers, sens de la jauge (`0xB66A30`) contre `sfa` arcade (captures) | nouveau |
| *Alpha* Anthology (`ro1`) par défaut | « arranged version that fixes things like Sagat ST.LK unblockable » ; « getting moves out is harder and **charging takes too long** » | SuperCombo (B) | Hyper ZERO hérite-t-il de l'arrangement ? Temps de charge plus long = EXTRA « COMMAND TIMER ARCADE/LONG » ? | Charlie ZERO : nombre d'images de charge minimal pour un Sonic Boom, arcade `sfa` contre Hyper PCSX2 contre traduction ; Sagat ZERO LK debout au bout de sa portée | nouveau |
| *Alpha 2* PS / Saturn (1996) | **showboating corrigé** ; musique arrangée (XA, ADPCM) ; Saturn : Evil Ryu, EX, Survival, Sakura de *Z2A* ; PS : images coupées (« on coupe sans couper ») | SuperCombo, ja.wikipedia, Funamizu (A/B) | Hyper ZERO 2 : showboating ou non ? | après un K.O., durée pendant laquelle le vainqueur garde la main (images), `sfa2u` contre Hyper | nouveau |
| *Gold* / *Zero 2'* (Collection 1997) | Cammy ; vraie intro au lieu de la FMV ; Survival ; pas de Dramatic | A/B | Hyper ALPHA = famille *Gold* : Cammy `$7E` ; **musique ALPHA = flux ADX de `ro6`**, arrangement Saturn, sans partition d'origine ; sans le thème de Cammy de la version PS | décision : garder les flux console, ou proposer la musique QSound de *Z2A* (= *Zero 2*, même QSound) | connu (musique) ; nouveau (choix arcade) |
| *Alpha 3* PS (1998) | moins d'images d'animation : combos et infinis impossibles en arcade ; Balrog enrichi (EX Balrog = arcade) ; étincelles en polygones | ENWIKI (B, sans source), ja.wikipedia (B) | Upper (Anthology) et Hyper ZERO 3 descendent du CPS-2, pas de la PS : risque faible ; mais les **thèmes des persos ajoutés** n'existent qu'en pistes console | — | connu (flux) |
| Dreamcast / Matching Service (1999-2001) | Saikyō Dojo, World Tour, I-ISM, Final Bison ; partenaire libre en Dramatic | A/B | Upper NAOMI en dérive, pas l'Anthology | — | — |
| PS2 Anthology (tous les modules) | **PRESS START clignotant** (routine J2 réécrite) ; **TIMER INFINITY** ; manches 1/3/5 (l'arcade va à 7) ; EVENT retiré ; intro calée sur des ticks ; OPTION / EXIT natifs | dépôt (A) | — | — | connu |
| PS2 Hyper | **toutes les versions parlent avec les voix de SFA3** ; HSFA rejoue les voix SFA1/SFA2 (e222 = `sfz.11m/12m`, e251 = `sz2`) | dépôt (A) | **écart voulu**, à documenter comme tel. Pour Dan ZERO, l'arcade recycle des voix : quelle voix rejoue HSFA ? | rejeu : liste des voix de Dan ZERO contre `sfa` | partiel |

---

## 7. Bugs connus d'Hyper et de l'Anthology, et ce que la recherche en dit

| bug | origine | dépôt | ce que dit la recherche | à vérifier, et comment |
|---|---|---|---|---|
| **EX Bison et EX Sagat ZERO 2** (`$58/$59`) atteignables (Start + colonne ZERO 2), données « défaut » (Ryu), affichés en morceaux | probablement Capcom (données PS2) | connu (`INDEX-HYPER` §1.2, `ETATS-HYPER`) | **aucune mention publique**. Mais l'*Alpha 2* d'arcade n'a jamais eu ces EX : ils naissent avec *Z2A* (ja.wikipedia, SuperCombo). La grille Start de ZERO 2 devrait donner `$4A/$4B`, ou rien. Les autres cases ZERO 2 de la grille suivent l'histoire : EX Zangief `$55`, EX Dhalsim `$56`, Evil Ryu `$57`, pas d'EX Ryu / Ken / Chun-Li — B + D | PCSX2, Hyper, curseur Bison puis Sagat, colonne ZERO 2, Start tenu à la validation : lire `$102` (`$58` ?) et faire une capture. Si l'affichage est cassé sur PS2, c'est un **défaut d'Hyper** : interrupteur HSFA « grille Start corrigée » (`$58` → `$4A`, `$59` → `$4B`), à 0 par défaut |
| tables d'Upper de **40 entrées** lues par `$102` (`0x6AF640`, `0x6AF668`, `0x6AF6B8` : récupération après garde brisée et après étourdissement) : débordement pour les ids ≥ `$28` | Capcom (code identique à Upper) | connu (`INDEX-HYPER` §3.1, §6.5) | même famille que le défaut CFC2 de 2025 (§5.3). Repères : durée d'étourdissement *Zero 2* 0,5-3 s, *Z2A* 1,5-5 s (SuperCombo, B) ; *Zero* et *Zero 2* n'ont **pas de jauge de garde** | (a) PCSX2 : Ryu ZERO étourdi, mesurer `$2CB` et la durée de l'étourdissement (images) contre Ryu ZERO 3 et contre `sfa` arcade. (b) La jauge de garde existe-t-elle pour les versions anciennes (`$24C` ≠ 0) ? Peut-on briser leur garde ? |
| **étourdissement maximal `$2CD`** pris dans `0x6AF5F0[$116]`, par perso de base | Capcom (choix) | connu (§4.3), pas confronté | *Zero* : **40 pour tous**, +5 par nouvel étourdissement (guide p. 24, A) | PCSX2 : `$2CD` de Ryu ZERO, de Birdie ZERO et de Ryu ZERO 3 ; arcade `sfa` : combien de coups pour étourdir |
| garde automatique `$32F` = `$0A` en ZERO | Capcom | connu | *Zero* : **8 gardes auto par manche** (GAME Watch, A) | Hyper ZERO en AUTO : compter les gardes auto jusqu'au 1er coup encaissé, contre `sfa` (Auto) |
| bit 6 de `$D3` jamais posé (16 tests : supers, CC, provocation) | Capcom (vestige ?) | connu | rien dans la recherche ; *Z2A* change justement les provocations (1-Up, frappes) et les supers à projectile — D | chercher un écrivain natif ou une écriture par l'application des options (`$BB` ?) |
| Ryu ZERO 3 d'Hyper : plus de boîtes de corps qu'Upper | Capcom ? | connu (§6.9) | — | diff des en-têtes de géométrie Hyper `$00` / Upper `$00` |
| **jauge qui déborde** (S-ISM « disparue ») ; **exception du TRAINING** à l'image 2945 | traduction (`CMP` mémoire-mémoire perdu) | connu, corrigé (`CMPMM`) | — | — |
| 23 `CMP` perdus ou faux `CMPI #0` dans Hyper (famille `CMPX`, désactivée) : seuils de vie et de jauge `#$90/#$30/#$48` | traduction | connu, ouvert | les seuils `$30` (niveau 1, ZERO 2 / ALPHA / AUTO), `$48` (Alpha Counter à 1,5 niveau en *Z2A* ; V-ISM) et `$90` sont des **valeurs d'oracle** : AC = −`$30` en ZERO 2, −`$48` en ALPHA — D | Hyper ALPHA : faire un Alpha Counter, lire `$11E` avant et après (−`$48` attendu ; −`$30` en ZERO 2), traduction avec `CMPX=0` puis `CMPX=1` contre PCSX2 |
| mode rose (SHADALOO-D) : zones de coup qui ne collent pas aux graphismes (Vega, Zangief) ; **banni en tournoi** pour ses infinis | Capcom | partiel (le banc a les correspondances) | ancien texte (C) ; SuperCombo (B) | capture des boîtes (affichage du banc) en mode rose, Vega et Zangief, contre PCSX2 |
| entrées ARCADE / SURVIVAL / DRAMATIC renvoyées au VERSUS ; pas d'écran de réplique ; générique « STAFF » caché | Capcom | connu | — | lire le générique (crédits non confirmés publiquement) |
| SFA3 traduit : « ∞ » invisible ; Upper : décor SURVIVAL et couleur du boss DRAMATIC (corrigés par `CMPMM`) | traduction | connu | — | — |
| **18 différences de version de *Zero 2*** (`ro2` `0x2DB210–0x2DB660`) : 3 citées sur 18 | Capcom (table de paramétrage) | partiel | *beep-on* : une commande cachée affiche les noms des interrupteurs (*Pocket Fighter*, son en mono, volume 0, sound test 019, 074, 007, 028, puis L2 sur la manette 2) ; exemples : CC infini de Sodom (Shiraha), Zangief saut vertical K, jauge de garde après 32 gardes, dégâts max du Saikyo, provocation de Dan en X-ISM parable, « 自主規制 », double K.O. du Shun Goku Satsu de Dan (*Pocket Fighter*), clignotement du titre (*Z2A*) — C | (1) publier les 18 lignes (déjà extraites dans `sjis_ro2.txt`) ; (2) chercher la même forme `NN:(…)` dans **tous** les modules, `ro3`, `ro5` et `ro9` compris, et dans `b` ; (3) trouver le tableau d'octets lu par ces interrupteurs et son lien avec les étoiles du CUSTOMIZE ; (4) en déduire la valeur par défaut de chaque interrupteur dans la traduction |
| octet de version `$BB` (`$FF80BA`) « aussitôt écrasé par la fonction d'application » | portage | partiel (`OPTIONS.md` §1.2) | c'est sans doute **le sélecteur de révision** du SECRET OPTION — D | voir §3, étapes 4-5 ; dans Hyper : que vaut `$BB` après le démarrage traduit, et qui le lit ? |

---

## 8. Sondes de version pour Hyper : liste de contrôle opérationnelle

Elles servent à deux choses : dire quelle révision, ou quel arrangement, Capcom a pris pour chaque version d'Hyper, et
vérifier que la traduction ne l'a pas changé.

Ordre des oracles :
1. PCSX2 (Hyper PS2) ;
2. l'arcade de la version ;
3. le module Anthology correspondant (`ro1`, `ro8`, `ro6`), si on le traduit un jour.

Les adresses arcade de *Zero* et *Zero 2* restent à établir (fichiers de triches de MAME, ou recherche RAM). Dans
Hyper : J1 `$FF8400`, J2 `$FF8800`, vie `$50`, jauge `$11E`, id `$102`, version `$D3/$117`, étourdissement `$2CB/$2CD`
(octets : XOR 1 dans la traduction).

**ZERO** (`$30-$3C`, `$D3` bit 0)

| sonde | séquence | si arcade 950605/950627 | si 950727 | si « arrangé » Anthology | confiance |
|---|---|---|---|---|---|
| HK de Sodom imparable | Sodom ZERO, HK contre un mannequin en garde (debout, puis accroupi), 3 distances | touche malgré la garde | gardé | gardé | A (guide), sans précision sur le coup |
| Kubikari de Guy | Guy ZERO, Kubikari sur le mannequin ; lire l'incrément de `$2CB` | ≈ 2× la 950727 | réf. | ? | A |
| LK debout de Sagat, au bout de sa portée | Sagat ZERO, LK debout à portée maximale contre une garde | imparable (toutes révisions) | imparable | **gardé** | B |
| cri de Dan à la projection | Dan ZERO, projection ; n° de son | 950605 : ancien | nouveau | ? | A (cosmétique) |
| AC roulé de Rose | Rose ZERO, Alpha Counter vers l'arrière au 1er round | état aérien buggé | ? | ? | B |
| Auto | AUTO, compter les gardes auto ; jauge ≤ `$30` | 8 par manche ; niveau 1 | idem | ? | A |
| supers imparables | super sur un adversaire qui n'est pas en garde avant le flash | imparable | idem | ? | B |
| charge de Charlie | images de charge minimales pour un Sonic Boom | arcade | arcade | plus long (SuperCombo) | B |

**ZERO 2** (`$40-$5F`, bits 1 et 5) : la base attendue est la **branche USA** (Evil Ryu, EX Zangief, EX Dhalsim).

| sonde | séquence | 960227 / 960229 | 960306 USA | 960430 USA | Brésil 960531 | confiance |
|---|---|---|---|---|---|---|
| coups aériens de Rose en Soul Illusion | Rose ZERO 2, Soul Illusion niv. 1, saut avant, puis chaque bouton ; saut vertical idem ; tenter une boule de feu aérienne et un AC aérien | coups interdits possibles, AC aérien invincible | corrigé | « beaucoup » de normaux perdus en saut (guide) | MP et MK seuls | A/B |
| AC poing d'Adon | Adon ZERO 2, AC poing sur une chaîne gardée | normal | normal | **touche très facilement** | ? | B |
| CC d'Evil Ryu, « blowout » à toute distance | Evil Ryu ZERO 2, activation de CC loin de l'adversaire : est-il repoussé ? | — | oui (arcade) ; **non** dans le 96/03/06 de l'Anthology (guide) | ? | — | A/B |
| showboating | après un K.O., le vainqueur bouge-t-il ou provoque-t-il sans fin ? | oui | oui | oui | oui (corrigé seulement en *Z2A* et sur PS/SS) | B |
| Shiraha de Sodom | Sodom ZERO 2, Shiraha Catch sur un adversaire en CC | CC infini | idem | idem | idem | B |
| coût de l'Alpha Counter | `$11E` avant et après | −1 niveau (`$30`) | idem | idem | idem | A/B |
| durée d'étourdissement | images d'étourdissement (mini, maxi) | 0,5-3 s | idem | idem | idem | B |

**ALPHA** (`$60-$7F`, bit 2) : la base attendue est *Z2A* / *Gold*.

| sonde | attendu (*Z2A*/*Gold*) | confiance |
|---|---|---|
| activation du CC | HP+HK ; pas d'invincibilité pendant le gel | B (code confirmé : `$4400`) |
| Alpha Counter | −1,5 niveau (`$48`) ; dégâts réduits pour certains AC | A/B |
| étourdissement | 1,5-5 s | B |
| showboating | impossible | B |
| K.O. sur provocation | icône 1-Up de *Side Arms* | B |
| provocations d'Akuma et de Rolento | frappent pour 2 pts | B |
| Soul Spiral des clones de Rose | 1 pt par coup ; Soul Piede (→ + HK) présent | B |
| Shiraha de Sodom | ne laisse plus en CC | B |
| Bull Horn de Birdie | en plusieurs coups | B |
| Yosokyaku de Chun-Li | rebond orientable | B |
| Somersault Shell de Charlie | parable en l'air | B |
| Kikoken et Sonic Boom | gain de jauge au démarrage 4 → 2 et 5 → 2 | B |
| roulade après un CC | impossible | B |
| Cammy (`$7E`) | version *Gold* (`ro6`) ; oracle CPS-2 externe : `sfa2-gold` de strygo, bâti sur l'Anthology | C |

**ZERO 3** (`$00-$25`, bit 4) : données d'Upper (`INDEX-HYPER` §1.3). Elle hérite donc des choix d'Upper (§5.1) :
crouch cancel, Tatsumaki de Ryu, Karin (§3).

---

## 9. Pièges de lecture (dates, noms, termes)

- **Date de ROM ≠ date de sortie.**
  - *Zero* : sortie le 22/06/1995, ROM 950605/950627.
  - *Zero 2* : sortie le 25/03/1996, ROM 960227.
  - *Z2A* : sortie fin août 1996 (22/08 probable), ROM 960805.
  - *Zero 3* : sortie le 15/07/1998, ROM 980629.
  - Les infobox occidentales recopient souvent la ROM. — A
- **Noms japonais.** ベガ (Vega) = M. Bison (US) ; バルログ (Balrog) = Vega (US, la griffe) ; M.バイソン = Balrog (US,
  le boxeur). « Final Vega » = Final Bison ; « EXバイソン » = EX Balrog (boxeur).
  - ⚠ Les notes `04_zero3_verif` (« Izuna Drop de Vega (Balrog en Occident) ») inversent le sens : l'Izuna Drop est à
    la griffe, Vega en Occident, バルログ au Japon. — A
- **ISM.** Z-ISM (Japon) = A-ISM (export). S-ISM (Shadaloo) est réservé au CPU en arcade. Les quatre S-ISM d'Hyper
  s'appellent SHADALOO-A à D (wikis japonais), S-ISM 1 à 4 (guide BradyGames, numérotation différente : 1 vert,
  2 bleu, 3 rose, 4 rouge) et DS / CE / 3 / M-ISM (presse, 2006). — A/B
- **« Crouch cancel »** (anglais) et « 着地キャンセル » (japonais, Famitsu 2025) désignent la même technique supprimée par
  Upper, selon les deux sources. namu.wiki parle aussi d'un « 着地キャンセル » corrigé. Mesurer plutôt que traduire. — B/D
- **Dates de l'Anthology.**
  - `ro2` (Japon) propose une date USA (96/03/06).
  - `ro3` propose une date japonaise seule (98/07/27).
  - Le guide écrit « By default … the most recent version ».

  Une date du menu nomme un jeu de réglages, pas forcément une ROM. — A/D

---

## 10. Priorités conseillées

| # | action | pourquoi | coût |
|---|---|---|---|
| 1 | Refaire `revision.py` : Japon contre Japon (980629, 980727, 980904), sur les ROM 05-10, en classant chaque fonction (§3) | l'oracle SFA3 repose sur une conclusion non prouvée | faible (statique) |
| 2 | Inventorier le CUSTOMIZE et `$BB` dans `ro3`, `ro5` et `ro9`, plus les listes « NN:(…) » de tous les modules ; publier les 18 lignes de `ro2` | c'est le mécanisme de révision de l'Anthology : il dit ce que la traduction applique par défaut | moyen |
| 3 | PCSX2 : `$58/$59`, `$2CD` / `$2CB` des versions anciennes, garde auto ZERO, Alpha Counter ALPHA (`$11E`) | sépare les défauts de Capcom des défauts de traduction (§7) | faible |
| 4 | Diff des données d'attaque `ro3` / `ro5` (et Hyper ZERO 3), avec le Tatsumaki de Ryu comme témoin | liste des changements d'équilibrage d'Upper, jamais publiée | moyen |
| 5 | Avant MAX dans `$26-$29` : étendre la table de Bison par adversaire (`0x433E50`) ; chercher l'équivalent pour R. Mika ; ajouter la séquence Head Press / Skull Diver / Sardine Beach contre les 4 MAX à `nonreg_ro5.sh` | défaut réel de Capcom en 2025 (CFC2) | faible |
| 6 | Sondes de version d'Hyper (§8) dans un `sondes_hyper.lua` (dérivé de `partie.lua`), sur PCSX2 et sur la traduction | qualifie ZERO / ZERO 2 / ALPHA ; non-régression de comportements fins | moyen |
| 7 | Régions pour la voie B : répliques, Regulation, musique de la Dramatic Battle, dégâts à deux joueurs | choix de présentation de la couche Arcade greffée | faible |

---

## Sources principales

- MAME `cps2.cpp` (lu le 2026-10-20) : https://raw.githubusercontent.com/mamedev/mame/master/src/mame/capcom/cps2.cpp ;
  NAOMI : `sega/naomi.cpp` (`sfz3ugd`, GDL-0002).
- Guide officiel BradyGames, *Street Fighter Alpha Anthology* (2006), p. 3-5, 24, 58 ; transcription :
  transcription locale du guide BradyGames (hors dépôt : texte protégé).
- SuperCombo (wikitexte lu le 2026-10-20) :
  - https://wiki.supercombo.gg/w/Street_Fighter_Alpha ;
  - https://wiki.supercombo.gg/w/Street_Fighter_Alpha_2/FAQ ;
  - https://wiki.supercombo.gg/w/Street_Fighter_Alpha_2/System ;
  - https://wiki.supercombo.gg/w/Street_Fighter_Alpha_2/Rose ;
  - https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/FAQ.
- arcade-history : https://www.arcade-history.com/game/2672/ et /2651/ (révisions 980629, 980727 et 980904 ; bugs de
  Karin).
- ja.wikipedia :
  - ストリートファイターZERO (copie dans `12_ja_wikipedia.md`) ;
  - ストリートファイターZERO ファイターズ ジェネレーション.
- Funamizu, *All About* vol. 11 (trad. It's Fantastic!) : https://itsfantastic.moe/all-about-street-fighter-alpha-developer-interview/
- GAME Watch : 2001 (https://game.watch.impress.co.jp/docs/20010131/zero3.htm) et 2025 (`/docs/kikaku/2024059.html`).
- Famitsu (CFC2, 07/02/2025 et 16/04/2025) ; EventHubs, notes de patch de CFC2 (06/08/2025, 10/09/2025, 12/06/2025).
- strygo, `data/patches.json` (lu le 2026-10-20) : https://github.com/strygo/arcade-patches
- *Challenger's Edition* : https://raw.githubusercontent.com/originalgrego/sfa3ce/master/README.md
- *Sega Saturn Magazine* n° 12 (1996), *CVG* n° 173 (1996) : OCR archive.org (notes `03_verif` et `05_verif`).
- Notes du dossier : `03_zero1_zero2(_verif).md`, `04_zero3(_verif).md`, `05_…_verif.md`, `06_…_verif.md`,
  `09_anthology_hyper(_verif).md`, `10_bidouilleurs_verif.md`, `00_ancien_texte_coulisses.md`, `chapitres_v2/03-06, 10`.
