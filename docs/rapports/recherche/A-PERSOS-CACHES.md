# Personnages cachés, versions et modes secrets : fiche de test (HSFA)

Version du 2026-10-20. Ce document rassemble, pour chaque jeu de la série et pour Hyper, les personnages cachés, les
versions de personnages et les modes secrets, avec leur **commande exacte**, la **source**, un **niveau de confiance**
et une **procédure de test** dans Hyper (`sfa3hhsfa`) et dans les arcades de référence.

Il s'appuie sur trois ensembles :
- les **rapports du dépôt** `SFA-Anthology-PS2-mods` : `docs/rapports/INDEX-HYPER.md`, `ETATS-HYPER.md`,
  `DEFAUTS-HYPER.md`, `COUPS.md`, `OPTIONS.md`, `CARTE-MODULES.md`, `BLOC-HYPER.md`, `ECARTS-UPPER.md`,
  `SON-HYPER.md`, `docs/journal/SESSION-CLOUD-2026-10-16.md`, `tools/fbneo-hsfa/essais/tournee.h`, `joue_linux.c` ;
- les **notes de recherche du livre** (`03_*`, `04_*`, `05_*`, `06_*`, `09_*`, les `_verif` priment ; `12_ja_wikipedia.md` ;
  `livre_complet.md`, chapitre « Hyper ») ;
- le **guide officiel BradyGames** de l'Anthology (transcription locale :
  transcription locale du guide BradyGames (hors dépôt : texte protégé)),
  et des pages relues pour cette fiche : SuperCombo (wikitexte brut) et `history.dat` (copie libretro).

---

## 0. Conventions

### 0.1 Sources (abréviations)

| abrév. | source | ouverte pour cette fiche ? |
|---|---|---|
| **GUIDE p. N** | *Street Fighter Alpha Anthology*, guide officiel BradyGames (A. Deats, J. Epstein, 2006), page imprimée N | oui (transcription) |
| **HDAT** | `history.dat` d'arcade-history, copie libretro : https://raw.githubusercontent.com/libretro/mame2003-plus-libretro/master/metadata/history.dat (entrées `sfa`, `sfa2`, `sfz2j`, `sfz2ah`, `sfa3`) | oui |
| **AH** | arcade-history, Zero 3 : https://www.arcade-history.com/game/2672/ | oui (dans `04_zero3_verif.md`) |
| **SC-xxx** | wiki SuperCombo : [SFA](https://wiki.supercombo.gg/w/Street_Fighter_Alpha), [SFA2](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_2), [SFA2/Evil Ryu](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_2/Evil_Ryu), [SFA2 Gold](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_2_Gold), [SFA3/FAQ](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/FAQ), [SFA3/Juni](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Juni/Introduction), [SFA3/Juli](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Juli/Introduction), [SFA3/Balrog](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Balrog/Introduction), [Hyper](https://wiki.supercombo.gg/w/Hyper_Street_Fighter_Alpha) | oui |
| **JAWIKI** | https://ja.wikipedia.org/wiki/ストリートファイターZERO (copie : `12_ja_wikipedia.md`) | oui |
| **JAWIKI-FG** | https://ja.wikipedia.org/wiki/ストリートファイターZERO_ファイターズ_ジェネレーション (extraits dans `09_anthology_hyper_verif.md`) | oui |
| **CAPCOM-FAQ** | FAQ du support Capcom Japon : https://www.capcom.co.jp/support/faq/platform_ps2_sfz_fg_036605.html | oui (dans `09_*_verif`) |
| **DÉPÔT §** | rapport ou journal du dépôt (vérifié au banc ou dans le code) | — |

### 0.2 Niveaux de confiance

- **A** : au moins deux sources indépendantes concordent, ou une source plus une vérification au banc / dans le code du
  dépôt.
- **B** : une seule source fiable ouverte (guide officiel, HDAT, SuperCombo), sans recoupement.
- **C** : source non ouverte, conflit non tranché, ou déduction.
- **⚠** : conflit entre sources, détaillé au §10.

### 0.3 Boutons : arcade, PS2, cœur HSFA

| rôle | CPS-2 | PS2 (réglage par défaut de l'Anthology, SC-Hyper) | RetroPad (cœur HSFA, `LISEZMOI-hyper.md`) | n° pour `HSFA_ENTREES` / `HSFA_GESTES` |
|---|---|---|---|---|
| LP | bouton 1 | □ Carré | Y | 1 |
| MP | bouton 2 | △ Triangle | X | 9 |
| HP | bouton 3 | R1 | L | 10 |
| LK | bouton 4 | × Croix | B | 0 |
| MK | bouton 5 | ○ Rond | A | 8 |
| HK | bouton 6 | R2 | R | 11 |
| Start | Start | START | Start | 3 |
| Pièce / Select | Coin | SELECT | Select | 2 |
| Haut / Bas / Gauche / Droite | | | | 4 / 5 / 6 / 7 |

Les commandes PS2 du guide (« ■ + ✖ + R2 ») se traduisent donc en boutons d'arcade : ■ + ✖ + R2 = **LP + LK + HK**,
■ + ● + R1 = **LP + MK + HP**, △ + × + R2 = **MP + LK + HK**. Hypothèse : le jeu teste des rôles (LP…), pas des
touches. Si le joueur a remappé ses boutons dans l'Anthology, le résultat peut différer.

### 0.4 Mémoire : quelle numérotation ?

- **Arcade et PS2** : les champs portent le même numéro (`$102` = identifiant étendu du perso). Joueur 1 en
  `$FF8400`, joueur 2 en `$FF8800` (SFA3, Upper, Hyper).
- **Traduction 68K** (fork MAME `sfa3hx`, cœur FBNeo HSFA) : un octet PS2 `d` se lit à l'adresse 68K `d XOR 1`.
  Correspondances utiles pour Hyper (ETATS-HYPER, conventions) :

| sens | champ PS2 / arcade | octet 68K (fork, cœur) |
|---|---|---|
| identifiant étendu perso × version | `$102` | `$103` |
| perso de base | `$116` | `$117` |
| drapeaux de version vrais | `$117` | `$116` |
| drapeaux de version de travail | `$D3` | `$D2` |
| curseur de version / de mode | `$5D` | `$5C` |
| ism (−1 X, 0 A, +1 V) | `$132` | `$133` |
| mode S-ISM (`$80` / `$02` / `$82`) | `$122` | `$123` |
| ism étendu calculé (2 / 3 / 4) | `$123` | `$122` |
| CLASSIC (`$01`) ou Saikyo S-ISM (`$81`) | `$15E` | `$15F` |
| MAZI | `$15A` | `$15B` |
| SAIKYO | `$131` | `$130` |
| témoin vu sur Bison en Classic S-ISM | `$15D` | `$15C` |
| EX / CLASSIC à l'init. | `$B5` | `$B4` |

⚠ **Piège de lecture des journaux.** La ligne `CHOIX` de `tournee.h` imprime `$102=`, `$116=`, `$122=`, `$123=`,
`$15F=`, mais lit les octets 68K `$103`, `$116`, `$122`, `$123`, `$15F`. Donc `$102=` est bien l'id étendu, `$116=`
contient les drapeaux de version, `$123=` est le mode S-ISM (`80`, `02`, `82`) et `$15F=` vaut `01` (CLASSIC) ou `81`
(Saikyo S-ISM). Les valeurs attendues ci-dessous sont données **telles que ce journal les affiche**.

---

## 1. Outils de test disponibles dans le dépôt

| outil | où | pour quoi faire |
|---|---|---|
| `joue_linux` (frontal libretro) | `tools/fbneo-hsfa/essais/joue_linux.c` | charge le cœur et un zip, N images, son WAV, captures BMP aux images listées : `joue_linux coeur.so jeu.zip system N sortie.wav [images…]` |
| `HSFA_TOURNEE="J1/J2,…"` | `tournee.h` (portage C de `tournee_hyper.lua`) | pilote la sélection et les combats d'Hyper par la RAM. Syntaxe par joueur : `perso(hex, id de base).famille(Z / Z2 / A / Z3)` + options `.iX / .iA / .iV` (ism), `.m0`–`.m7` (mode ZERO 3 : 0 NORMAL, 1 MAZI, 2 SAIKYO, 3 CLASSIC, **4-7 = leurs S-ISM dans le même ordre**), `.vS` (Start tenu à la validation de la version), `.v+` / `.v-` (Start + droite / gauche à la version), `.g` (Start tenu à la validation du perso), `.r` (Select tenu : roulette), `.e+N` / `.e-N` (ancienne forme, Start + direction au menu des modes). Journal : `HSFA_TOURNEE_LOG` |
| `HSFA_TOURNEE_PASSIF=1`, `HSFA_TOURNEE_PV=1` | `tournee.h` | combat laissé aux entrées scriptées ; adversaire qui garde sa vie |
| `HSFA_ENTREES=fichier` | `joue_linux.c` | lignes `image_début image_fin port bouton` (n° du §0.3) |
| `HSFA_GESTES=fichier`, `HSFA_GESTES_DEBUT`, `HSFA_GESTES_DUREE` | `joue_linux.c` | état sauvé à une image, puis chaque geste rejoué depuis cet état (idéal pour essayer une commande ou une parade) |
| `HSFA_POKE="a-b:adresse:valeur,…"` | `joue_linux.c` | écrit un octet **68K** à chaque image de `[a, b)` (forcer un perso, une jauge, un mode) |
| `HSFA_RAM_DUMP=1` | `joue_linux.c` | RAM 68K écrite en `ram_<image>.bin` aux images capturées (octet 68K `a` = fichier`[(a − $FF0000) XOR 1]`) |
| `HSFA_NOROUL=1` | cœur `cps_hsfa.cpp` | neutralise la roulette (comparaisons à entrées égales) |
| `HSFA_FLUX_LOG` | cœur | journal des codes musique (variantes A / B / EX : indice indirect du mode choisi, SON-HYPER §2.3) |
| `tournee_complete.py --extra A:vS --z3 …` | `tools/fbneo-hsfa/essais/` | tournée de tous les ids, avec variantes EX et modes |
| `tournee_hyper.lua` (`LISTE`, `MODEJEU`, `CONTOURNE_E`, `NOROUL`) | `tools/hyper-etats/` | même pilotage au banc MAME (fork `sfa3hx`). ⚠ Ici `.mN` = **valeur du curseur** N (4 = Classic S-ISM, 5 = Mazi S-ISM, 6 = Normal S-ISM, 7 = Saikyo S-ISM), alors que dans `tournee.h`, `.m4` = Normal S-ISM. Ne pas recopier une liste d'un outil à l'autre sans traduire |
| `tournee.lua` (`REF=1`, `PERSO`, `CURSEUR`, `MODE`, `FORCE`) | `src/hsfa/mame/` | SFA3 (arcade de référence avec `REF=1`, ou traduction), perso imposé par `$102` |
| `compare_voix_arcade.py --jeu sfa1/sfa2 --poke` | `tools/son-hyper/` | joue les arcades SFA1 / SFA2 **dans le même cœur** ; persos cachés de SFA1 forcés par l'octet 68K `$FF84A2` (`02` Akuma, `0A` Bison, `0C` Dan) |
| options du cœur `Extra option: …` / `HSFA_OPT_EXTRA` | patch FBNeo 0003, `lua/banc_options.lua` | les EXTRA OPTION de l'Anthology (§8.2) |

Pour lire un champ d'arcade (référence `REF=1` ou MAME standard), un script d'une dizaine de lignes suffit :

```lua
-- lecture des ids des joueurs (arcade : numérotation directe) ; lancer avec -autoboot_script
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n % 30 == 0 then
    print(string.format("%d J1 $102=%02x $132=%02x $15A=%02x $131=%02x $15E=%02x $122=%02x | J2 $102=%02x",
      n, mem:read_u8(0xFF8502), mem:read_u8(0xFF8532), mem:read_u8(0xFF855A), mem:read_u8(0xFF8531),
      mem:read_u8(0xFF855E), mem:read_u8(0xFF8522), mem:read_u8(0xFF8902)))
  end
end)
```

Sur la traduction, lire `adresse XOR 1`. Pour SFA1 / SFA2 d'arcade, la structure joueur n'a pas les mêmes champs :
seul `$FF84A2` (perso de J1 dans SFA1) est connu du dépôt.

---

## 2. Street Fighter Alpha / Zero (1995)

### 2.1 Arcade CPS-2 (`sfa`, `sfau`, `sfzj`…)

| id | élément | commande exacte | source | conf. | dans Hyper ? |
|---|---|---|---|---|---|
| Z1-1 | **Dan** | Pièce mise, **Start maintenu** ; sur la case aléatoire « ? », entrer en moins d'une seconde l'une des suites **LP, LK, MK, HK, HP, MP** / LK, LP, MP, HP, HK, MK / **HP, HK, MK, LK, LP, MP** / HK, HP, MP, LP, LK, HK (selon la couleur). Prendre la couleur opposée à celle de l'adversaire | GUIDE p. 20 ; HDAT `sfa` (2 suites) ; SC-SFA | A | oui, id `$3C` sur la grille normale (colonne ZERO), sans code |
| Z1-2 | **M. Bison** | Start maintenu sur « ? » : J1 **↓↓←←↓←← + LP + HP** (ou LK + HK, autre couleur) ; J2 **↓↓→→↓→→** + LP + HP | GUIDE p. 20 ; HDAT `sfa` | A | oui, `$3A` |
| Z1-3 | **Akuma** | Start maintenu sur « ? » : J1 **↓↓↓←←← + LP + HP** (ou LK + HK) ; J2 ↓↓↓→→→ | GUIDE p. 20 ; HDAT ; SC-SFA | A | oui, `$32` |
| Z1-4 | Akuma, adversaire secret | Choisir son perso, puis **Start + MP + MK maintenus** à la fin de l'écran de sélection : Akuma bat le 1er adversaire et prend sa place | GUIDE p. 20 ; HDAT | A | non (Hyper n'a pas de mode Arcade) |
| Z1-5 | Dan, adversaire secret | Après chaque manche, **Start + LP + MP + HP** maintenus jusqu'à la suivante ; il remplace Sagat ou Adon | HDAT | B | non |
| Z1-6 | **Dramatic Battle** (Ryu + Ken contre Bison) | À deux. J1 sur Ryu : Start maintenu, ↑↑, relâcher Start, ↑↑ + LP. J2 sur Ken : Start maintenu, ↑↑, relâcher Start, ↑↑ + HP | GUIDE p. 20 ; HDAT ; JAWIKI | A | non |
| Z1-7 | Couleurs | Couleur au choix par LK, MK ou HK ; les persos cachés se prennent avec LP + HP ou LK + HK | HDAT | B | Hyper a ses propres tables de couleurs (`0x5B5C30`) |

Les notes `03_zero1_zero2.md` (l. 123) donnent pour Bison « bas, bas, gauche, gauche, bas, gauche » : il manque un
dernier « gauche ». Le guide et HDAT donnent ↓↓←←↓←←.

**Procédures de test (arcade de référence, cœur FBNeo ou MAME).**
- Z1-1 à Z1-3 : jeu `sfa.zip`. Mettre une pièce, tenir Start dès l'écran de sélection, placer le curseur sur « ? »,
  entrer la suite. Observer : le portrait du perso caché, puis son nom à l'écran VS. Avec `HSFA_ENTREES`, prévoir
  6 appuis de 3 images espacés de 3 images, le tout en moins de 60 images. Repli : forcer l'octet `$FF84A2` pendant
  la sélection (`HSFA_POKE="800-960:FF84A2:02"`) donne la référence attendue (méthode de `compare_voix_arcade.py`).
- Z1-4 : une partie Arcade, Start + MP + MK tenus à la sortie de la sélection. Observer : Akuma entre et frappe
  l'adversaire de la 1re étape.
- Z1-6 : deux joueurs, chacun entre sa séquence. Observer : écran de combat à trois, Ryu et Ken contre Bison. En
  version japonaise, la musique est l'instrumental du film (JAWIKI) ; à l'export, c'est le thème de Bison.

### 2.2 Version CPS Changer (CPS-1, `sfzch`, `sfach`, `sfzbch`)

| id | élément | commande | source | conf. |
|---|---|---|---|---|
| Z1-8 | **Écran-titre rouge** et options cachées : choix du parcours CPU, persos libres en Dramatic Battle, **les 3 persos cachés présents en permanence** sur la grille, mode entraînement, test son | Au démarrage, sur le levier du **joueur 2**, tenir **bas + LK + HK** | JAWIKI (« 2P側のレバー下と弱キックと強キック ») | B ⚠ |
| Z1-9 | Menu service | tenir le **Select** d'un joueur + Start | commentaire du pilote MAME `cps1.cpp` (`sfzch`) | B |

⚠ `05_portages_alpha1_alpha2_verif.md` écrit « bas + **LP** + HK ». Le texte japonais dit 弱キック (LK) : la note
contient une coquille.

**Test** : MAME ou FBNeo, jeu `sfzch`. Tenir J2 bas + LK + HK pendant la mise sous tension. Observer : fond du titre
rouge, Akuma, Bison et Dan sur la grille, nouveaux choix de mode. Aucun lien avec Hyper : utile seulement comme
référence (le son CPS-1 de l'Anthology vient de cette version).

### 2.3 Module de l'Anthology (`ro1`) et Hyper

- Les codes Z1-1 à Z1-6 sont repris tels quels dans l'Anthology (GUIDE p. 20) ; le Dramatic Battle y devient aussi un
  mode de menu (SC-SFA2 Gold : « retroactively added to the original Alpha and Alpha 2 »).
- **Hyper** : Akuma, Bison et Dan de ZERO sont sur la grille normale (`$32`, `$3A`, `$3C`), sans code. Rien à tester
  côté entrées. On peut seulement vérifier leurs voix, déjà mesurées par `compare_voix_arcade.py` (§160 du journal).

---

## 3. Street Fighter Zero 2 / Alpha 2 (1996)

### 3.1 Arcade Japon (`sfz2j`) et toutes régions

| id | élément | commande | source | conf. | dans Hyper ? |
|---|---|---|---|---|---|
| Z2-1 | **Chun-Li tenue *SF2*** | Curseur sur Chun-Li, **Start maintenu 3 s ou plus**, puis valider. HDAT : Start maintenu, **après 5 s**, LP / MP / HP (tenue bleue sans pantalon) ou **LP + MP + HP** (tenue rose) | JAWIKI (« スタートボタンを3秒以上押したまま選択 ») ; GUIDE p. 52 (3 s) ; HDAT `sfa2`, `sfz2j` (5 s) | A (durée ⚠) | oui : `$52` (ZERO 2) et `$72` (ALPHA), Start tenu à la validation de la version |
| Z2-2 | **Shin Akuma** (boss CPU) | Avec la couleur d'origine (bouton poing), ne perdre aucune manche, au moins 3 *perfect* et 3 fins par super : il remplace le dernier boss | HDAT `sfa2`, `sfz2j` | B | jouable : `$54` (ZERO 2), Start tenu |
| Z2-3 | Décors cachés Grass (Sagat) et Waterfall (Bison) | À deux joueurs, Start maintenu sur la grille, rester 5 s sur Sagat (ou Bison), aller sur n'importe quel perso, relâcher Start, valider | HDAT `sfa2` | B | le décor ZERO 2 d'Hyper **est** la cascade de Guyane (JAWIKI-FG) |
| Z2-4 | Sari dans tous les décors | Dhalsim : **LP + HK** maintenus avant chaque manche | HDAT | B | Hyper n'a que 3 décors : sans objet |
| Z2-5 | Décor de Sodom alternatif | tous les 4 096 matchs | HDAT | B | sans objet |

### 3.2 Arcade USA / Europe (`sfa2`, `sfa2u`) : ajouts

| id | élément | commande | source | conf. | dans Hyper ? |
|---|---|---|---|---|---|
| Z2-6 | **Evil Ryu** | Curseur sur Ryu, **Start** (appui ou maintien 1 s), déplacer le curseur **→ (Adon), ↑ (Akuma), ↓ (Adon), ← (Ryu)**, puis Start **maintenu** + un poing ou un pied | SC-SFA2/Evil Ryu ; HDAT `sfa2` (« Ryu, Start 1 s, Adon, Akuma, Adon, Ryu, Start 1 s + bouton ») ; GUIDE p. 52 (« hold Start, input →↑↓← ») | A (Start tenu ou non : ⚠) | oui, `$57` (ZERO 2) **sur la grille normale**, sans code |
| Z2-7 | **Dhalsim *SF2'* (EX)** | Curseur sur Dhalsim, Start maintenu, **←↓→↑**, valider Dhalsim | GUIDE p. 52 | B | oui, `$56` (ZERO 2), Start tenu à la validation de la version |
| Z2-8 | **Zangief *SF2'* (EX)** | Curseur sur Zangief, Start maintenu, **↓←←←←↑↑→→→→↓**, valider Zangief | GUIDE p. 52 | B | oui, `$55` (ZERO 2), Start tenu |
| — | Comportement des deux EX | « play like their counterparts from Street Fighter II: Champion Edition, including the omission of… super moves and air blocking » | SC-SFA2 | B | à vérifier sur `$55` / `$56` (pas de super, pas de garde aérienne) |

Ces suites de directions sont des **trajets du curseur** sur la grille d'*Alpha 2* (Ryu → Adon → Akuma → Adon → Ryu).
Elles dépendent donc de la grille, pas d'une manipulation de levier.

Evil Ryu, EX Dhalsim et EX Zangief n'existent qu'en version US / Europe (SC-SFA2, JAWIKI : « 北米版『ALPHA2』では、さらに新たな隠しキャラクターとして »). HDAT `sfz2j` (Japon) reprend pourtant le code d'Evil Ryu, sans doute par copie
de l'entrée `sfa2` : à vérifier (§10).

### 3.3 Module de l'Anthology *Alpha 2* (`ro8`)

Le guide (p. 52) donne pour ce module : Chun-Li d'origine (Start 3 s), **Shin Akuma jouable** (curseur sur Akuma,
Start 3 s, puis valider : ajout de l'Anthology, JAWIKI-FG), Evil Ryu, EX Dhalsim, EX Zangief (codes ci-dessus).
Modes cachés, avec les touches PS2 et leur traduction en boutons :

| mode | commande PS2 (GUIDE p. 52) | en boutons (§0.3) |
|---|---|---|
| Last Boss Mode | choisir Arcade en tenant ■ + ● + R1 | LP + MK + HP |
| Dramatic Battle | choisir Dramatic Battle en tenant ■ + ✖ + R2 | LP + LK + HK |
| Parcours spécial en Survival | choisir Survival en tenant R1 ou R2 | HP ou HK |
| Random Battle | choisir Versus en tenant ■ + ✖ + R2 | LP + LK + HK |

### 3.4 Procédures de test

- **Référence arcade** : `sfa2u.zip` (USA 960306, conseillée par le GUIDE p. 3 sous le nom 96/03/06ver) dans le cœur
  ou dans MAME. Pour Z2-6 à Z2-8 : écrire les entrées avec `HSFA_ENTREES` (Start = 3, directions 4-7, valider = 1) et
  capturer l'écran VS. Observer : Evil Ryu (kimono foncé, aura), Dhalsim et Zangief dans leur sprite de *SF2* et sans
  barre de super pendant le combat.
- **Hyper** :
  ```sh
  HSFA_NOROUL=1 HSFA_TOURNEE="00.Z2/01.Z2,0f.Z2.vS/10.Z2.vS,04.Z2.vS/02.Z2.vS" HSFA_TOURNEE_LOG=z2.log \
    joue_linux fbneo_hsfa_libretro.so sfa3hhsfa.zip system 30000 z2.wav 4000 12000 20000
  ```
  Journal attendu (`CHOIX`) : `$102=40` / `41`, puis `56` / `55`, puis `52` / `54`. Ryu ZERO 2 donne `40`. Evil Ryu
  ZERO 2 est une ligne de la grille à part (base `$17`) : `17.Z2` doit donner `57` sans Start.
- **À observer en combat** : EX Zangief et EX Dhalsim sans super ni garde aérienne (rôle de SC-SFA2). C'est la
  vérification la plus utile, car le dépôt n'a jamais confronté ces versions à leur comportement d'origine.

---

## 4. Street Fighter Zero 2 Alpha (arcade, août 1996)

### 4.1 Arcade (`sfz2al`, `sfz2aj`, `sfz2ah`…)

| id | élément | commande | source | conf. | dans Hyper ? (grille Start `0x5C5420`) |
|---|---|---|---|---|---|
| ZA-1 | **Versions *SF2'* (EX)** de Ryu, Ken, Sagat, Vega (= M. Bison), Dhalsim, Zangief | Curseur sur le perso, **Start une fois**, valider | HDAT `sfz2ah` ; notes `03_*` ; SC-SFA2 Gold | A | EX ALPHA : Ryu `$7B`, Ken `$7A`, Bison `$78`, Sagat `$79`, Zangief `$75`, Dhalsim `$76` |
| ZA-2 | **Evil Ryu** | Ryu, **Start deux fois** | HDAT | B | `$77` (ALPHA), grille normale, sans code |
| ZA-3 | **Chun-Li tenue *SF2*** / **Chun-Li *SF2'*** | Chun-Li, Start ×1 (tenue *SF2*) / Start ×2 (*SF2'*) | HDAT | B | `$72` (tenue *SF2*, colonne ALPHA) ; `$7C` (EX, obtenu par la **colonne ZERO** avec Start) |
| ZA-4 | **Sakura, autres couleurs** | Sakura, **Start ×5** | HDAT ; JAWIKI (« 色違いのさくら ») | A | `$7D` (ALPHA) et `$5D` (ZERO 2), Start tenu |
| ZA-5 | **Dramatic Battle** (2 contre 1) | à l'écran-titre, tenir **LP + MP + HK** et appuyer sur Start | HDAT | B | non |
| ZA-6 | **Shin Gouki Mode** | à l'écran-titre, tenir **MP + MK** et Start | HDAT ; SC-SFA2 Gold (« Shin Gouki Mode ») | A | Shin Akuma jouable `$74` (ALPHA), Start tenu |
| ZA-7 | **Survival** | à l'écran-titre, tenir **LP + MP + HP** et Start | HDAT ; JAWIKI (*All About ZERO2 ALPHA* p. 86-87) | A | non |

JAWIKI compte **10 persos cachés** : les 5 EX ajoutés (Ryu, Ken, Chun-Li, Sagat, Vega), la Sakura aux autres couleurs,
plus les 3 d'*Alpha 2* US (Evil Ryu, EX Dhalsim, EX Zangief) et la Chun-Li en tenue *SF2*.

### 4.2 Procédures de test

- **Référence** : `sfz2al.zip` (le dépôt l'a déjà utilisée, journal §161). Pour ZA-1 : curseur sur Ryu, un appui
  sur Start (port 0, bouton 3, 4 images), puis LP. Observer : Ryu au kimono et aux coups de *SF2'*. Pour ZA-5 à ZA-7 :
  à l'écran-titre, tenir les trois boutons et appuyer sur Start. Observer l'écran qui suit (VS à 2 contre 1, Shin Gouki
  d'emblée, compteur de Survival).
- **Hyper**, EX ALPHA (tous vérifiés à l'image par le dépôt, ETATS-HYPER §1.3) :
  ```sh
  HSFA_NOROUL=1 HSFA_TOURNEE="00.A.vS/01.A.vS,0a.A.vS/0b.A.vS,10.A.vS/0f.A.vS,04.Z.vS/0d.A.vS,04.A.vS/02.A.vS" \
    HSFA_TOURNEE_LOG=exa.log joue_linux … 50000 exa.wav …
  ```
  Attendu : `7b`/`7a`, `78`/`79`, `75`/`76`, `7c`/`7d`, `72`/`74`. `$116=` (drapeaux) vaut `0e` pour un EX ALPHA.
  Plaque « ALPHA2G » sur l'écran VS. Pour Zangief, Dhalsim et Sakura, la 1re colonne est ZERO 2 : la tournée le gère
  par la famille `A`.
- **À observer** en combat, sources à l'appui : EX Ryu / Ken / Sagat / Bison jouent comme dans *SF2'* (pas de super ;
  SC-SFA2 Gold, « classic versions »). Le dépôt ne l'a pas vérifié coup par coup : comparer à `sfz2al` avec
  `HSFA_GESTES` (35 gestes de `compare_voix_arcade.py`), en relevant les animations et les dégâts.

---

## 5. Gold / Zero 2 Dash (console) et module `ro6` de l'Anthology

| id | élément | commande (Anthology, GUIDE p. 52) | conf. | dans Hyper ? |
|---|---|---|---|---|
| G-1 | EX Ryu | Ryu, Start ×1, valider | B | `$7B` |
| G-2 | Evil Ryu | Ryu, Start ×2 | B | `$77` (grille normale) |
| G-3 | Chun-Li d'origine / EX Chun-Li | Chun-Li, Start ×1 / ×2 | B | `$72` / `$7C` |
| G-4 | EX Ken, EX Dhalsim, EX Zangief, EX Sagat, EX M. Bison | le perso, Start ×1 | B | `$7A`, `$76`, `$75`, `$79`, `$78` |
| G-5 | Sakura, autres couleurs | Sakura, Start ×5 | B | `$7D` |
| G-6 | **Shin Akuma** | Akuma, **Start ×5** (≠ arcade, où c'est un mode de titre) | B | `$74` |
| G-7 | **Cammy** | **M. Bison, Start ×2** | B ; JAWIKI (*Zero 2'* Saturn : Cammy en Versus seulement) | `$7E`, **grille normale** (colonne ALPHA), sans code |
| G-8 | Last Boss / Survival (parcours) / Dramatic / Random Battle | comme *Alpha 2* (§3.3) | B | Random Battle : voir §9.8 |

Dans l'Anthology, Cammy est jouable dans tous les modes, avec histoire et fin (Wikipédia en, `09_*_verif`). Sur la
*Street Fighter Collection* PS1 et sur Saturn, elle n'était jouable qu'en Versus et en entraînement (JAWIKI).

**Test (Hyper)** : `HSFA_TOURNEE="16.A/16.Z3"` doit donner `7e` / `16`. Avec `.vS` sur la colonne ALPHA, la grille
Start donne aussi `7e` : Cammy n'a pas d'EX. `$5E` (Cammy ZERO 2) existe dans la table des ids, mais n'est atteignable
par aucun chemin (INDEX §1.1) : Cammy n'a jamais été dans *Alpha 2*.

---

## 6. Street Fighter Zero 3 / Alpha 3 (arcade, 1998) et module `ro3`

### 6.1 Arcade CPS-2 (`sfa3`, `sfa3u`, `sfz3j`… ; référence du dépôt : `sfa3ud`, USA 980904)

| id | élément | commande | source | conf. | dans Hyper ? |
|---|---|---|---|---|---|
| Z3-1 | **Déblocage par le temps d'exploitation** : la couleur de l'écran-titre change au fil des semaines. Crème (départ) → **vert** (mode Classical) → **rouge** (Balrog, Juni, Juli) → **bleu foncé** (Mazi) → **violet** (Saikyo) → **bleu clair** (Final Battle, Dramatic, Survival). « after a few weeks… in a few months » | — | HDAT `sfa3` ; AH (texte identique) ; JAWIKI (« 基板が一定期間以上稼働することで ») | A | sans objet : tout est disponible |
| Z3-2 | **Code de déblocage immédiat** | Menu de test (F2 sous MAME), écran des réglages, 1re option « Input » ; sur la manette de J1 : **LP, LP, →, LK, HP, LP + Start**. Message « HERE COME NEW CHALLENGERS » | SC-SFA3/Juni, /Juli, /Balrog (même texte) | B | sans objet |
| Z3-3 | **Balrog** | (titre rouge ou plus) Curseur **sur Karin**, attendre, aller sur une case aléatoire, **Start maintenu**, valider | HDAT ; SC (« hover over Karin for 2+ seconds… hold start ») ; SC-FAQ (5 s) ; GUIDE p. 140 (1 s) | A (durée ⚠) | `$15`, grille normale |
| Z3-4 | **Juli** | Karin, puis case aléatoire en tenant **↑ ou ↓** | SC-FAQ, SC-Juli ; GUIDE p. 140 | **⚠** (HDAT et AH disent ← / →) | `$1E`, grille normale |
| Z3-5 | **Juni** | Karin, puis case aléatoire en tenant **← ou →** | SC-FAQ, SC-Juni ; GUIDE p. 140 (imprimé « → or → ») | **⚠** (HDAT et AH disent ↑ / ↓) | `$1F`, grille normale |
| Z3-6 | **Classical** | pièce mise, tenir **HP + HK** et appuyer sur Start | HDAT ; AH ; GUIDE p. 140 (« while starting game ») | A (marpirc inverse, non ouvert) | mode CLASSIC (curseur 3) |
| Z3-7 | **Mazi** | **MP + MK** + Start | HDAT ; AH ; GUIDE p. 140 | A | MAZI (curseur 1) |
| Z3-8 | **Saikyo** | **LP + LK** + Start | HDAT ; AH ; GUIDE p. 140 | A (marpirc inverse, non ouvert) | SAIKYO (curseur 2) |
| Z3-9 | **Final Battle** | après le choix de l'ism, tenir **Start + LP + MK + HP** : un seul combat contre Final Bison ; victoire = fin, défaite = mauvaise fin | HDAT ; AH | A | non |
| Z3-10 | **Dramatic Battle** | **LK + MK + HK** + Start : 2 contre 1, six manches | HDAT ; AH | A ⚠ (§6.2) | non |
| Z3-11 | **Survival** | **LP + MP + HP** + Start : « all 27 characters », manches uniques | HDAT ; AH | A | non |
| Z3-12 | Messages entre les combats (version japonaise) | Start + un bouton maintenus après une victoire | HDAT | B | non |
| Z3-13 | Sari partout | Dhalsim : LP + HK avant la manche | HDAT | B | sans objet (3 décors) |

Effets décrits par les sources :
- **Classical** : pas de super, pas de jauge de garde, pas de garde aérienne, ni de Zero Counter, ni de relevé
  (GUIDE p. 140, JAWIKI) ; gros dégâts et chaînes « CPS-1 » de X-ISM (GUIDE).
- **Mazi** : dégâts plus forts ; on perd la partie à la **première manche perdue** (GUIDE ; JAWIKI : « K.O.される
  とゲームオーバー »). Bogue de la rév. 980629 : la projection de Karin y faisait 99 % (AH ; une source non ouverte
  parle du mode Saikyo, §10).
- **Saikyo** : jauge de garde réduite, étourdissement plus facile, normaux non annulables en spécial (GUIDE ; JAWIKI).
- **S-ISM (Shadaloo-ISM)** : en arcade, réservée à l'ordinateur (JAWIKI, note 7). En Dramatic Battle solo, les boss
  sont V-ISM Adon, X-ISM Akuma, **S-ISM Balrog (« バイソン »), Vega, Sagat**, puis Final Bison (JAWIKI).
- **Rév. 980629** : Karin pouvait faire sa 2e super en X-ISM (AH).

### 6.2 Module de l'Anthology (`ro3`, `sfa3hsfa`)

Le guide (p. 140) donne pour l'Anthology :

| mode ou perso | commande | remarque |
|---|---|---|
| Balrog / Juli / Juni | Karin 1 s, case aléatoire ; Start / ↑ ou ↓ / ← ou → | aucun délai d'exploitation mentionné |
| Classical / Mazi / Saikyo | tenir HP + HK / MP + MK / LP + LK « while starting game » | |
| **Shadaloo Mode** | tenir **LK + MK + HK** « while starting game » : « secondary version of X-ISM that charges Super Meter incredibly fast… you can perform *all* of your character's Super Combos » | **S-ISM jouable : ajout de l'Anthology**. En arcade, LK + MK + HK lance le Dramatic Battle (HDAT, AH) |
| Survival, parcours spécial | choisir Survival en tenant R1 ou R2 (HP ou HK) | |
| Dramatic Battle | choisir Dramatic Battle en tenant ■ + ✖ + R2 (LP + LK + HK) | |
| Random Battle | choisir Versus en tenant ■ + ✖ + R2 (LP + LK + HK) | JAWIKI-FG : △ + × + R2 (§10) |

Le dépôt dit que le code ajouté du portage `port_202B70` pose les mêmes champs que l'écran de mode d'Hyper :
`$131`, `$15E`, `$122` (INDEX §4.1, numérotation PS2). C'est cohérent avec un **Random Battle qui tire au sort perso
et mode**, Shadaloo compris (déduction, C).

### 6.3 Procédures de test (`ro3` et référence)

1. **Juni / Juli (tranche le conflit)**. Référence `sfa3ud` (`REF=1`, ROM `roms/`), titre déjà débloqué (EEPROM
   d'un banc qui a tourné, ou code Z3-2).
   - Curseur sur Karin 5 s, case aléatoire, tenir **↑** et valider ; puis recommencer avec **→**.
   - Lire `$FF8502` (J1, numérotation arcade) : `$1E` = Juli, `$1F` = Juni (`tools/max/pl_mapping.json`).
   - Contrôle statique : `ECARTS-UPPER.md` situe le choix dans l'arcade en `$1E9EA` (`MOVEQ #$1F` / `#$1E`, « Juli/Juni
     par boutons »). Lire le test de `$11A` juste avant (bits 0-1 = droite/gauche, 2-3 = bas/haut) pour savoir quelle
     direction donne quel perso. Sur 3 sources, 2 (SC, guide) disent Juli = ↑ / ↓.
   - Mesurer aussi la **durée** minimale sur Karin : 1 s, 2 s, 5 s (§10).
2. **Codes de titre**. Avec `jeu.lua` et `INPUTS`, tenir HP + HK pendant l'appui sur Start ; vérifier ensuite
   `$FF855E = 1` et `$FF8532 = $FF` (X-ism imposé) sur la référence ; même lecture en `adresse XOR 1` sur la
   traduction. Faire de même pour Mazi (`$FF855A`), Saikyo (`$FF8531`) et LK + MK + HK (Shadaloo dans l'Anthology :
   attendu `$FF8522 ≠ 0` ; Dramatic en arcade). Les adresses viennent des champs d'Hyper (INDEX §4.1) ; leur identité
   dans SFA3 reste **à confirmer**. Observer en combat : plaque CLASSIC, absence de jauge de garde.
3. **Final Bison**. En Final Battle (référence), lire le champ arcade `$15D` du boss (`$FF895D`). Hypothèse à vérifier :
   `$80`, la valeur que pose la Classic S-ISM d'Hyper sur Bison (§9.4).
4. **Déblocage (Z3-1, Z3-2)**. Sur la référence, partir d'une EEPROM vierge (dossier `-nvram_directory` neuf) : titre
   crème attendu. Faire le code Z3-2, puis comparer les deux EEPROM pour trouver l'octet de déblocage. Puis regarder
   ce que fait `sfa3hsfa` : il ne lit pas l'EEPROM et charge les valeurs par défaut du portage (OPTIONS §1.3). Les
   persos et modes cachés devraient donc être ouverts d'emblée, ce que le dépôt n'a jamais vérifié explicitement.
5. **Modes de menu de l'Anthology**. Tenir LP + LK + HK en validant VERSUS ou DRAMATIC dans `sfa3hsfa`. On sait que ces
   lanceurs sont du 68K traduit dans Hyper (ETATS §2.1) ; pour `ro3`, le test n'a pas été fait.

---

## 7. Upper (NAOMI 2001, module `ro5` de l'Anthology) et MAX (PSP 2006)

### 7.1 Upper

| id | élément | commande | source | conf. | test |
|---|---|---|---|---|---|
| U-1 | Upper arcade : Dramatic, Survival, Final Battle accessibles sans attente, combinables sauf Final Battle | menu | GW 2001 (`04_zero3_verif`) | A | référence NAOMI hors du dépôt |
| U-2 | Upper arcade : Shin Akuma et Final Bison jouables, « 基板設定で使用不可にもできる » | réglage de la borne | JAWIKI | B | — |
| U-3 | **Écran de mode après le choix du perso** (Normal, Mazi, Saikyo, Classic) **et S-ISM par commande** à cet écran (« モードセレクト中に特定のコマンド入力によりS-ISMの選択が可能 ») | commande non décrite (Hyper : Start + ← / →) | JAWIKI | B | `sfa3uhsfa` : à l'écran de mode, tenir Start + ← ou →, puis observer la plaque S-ISM et l'octet 68K `$123` du joueur. Indice favorable : la sélection réécrite d'Upper lit `$122` (ECARTS-UPPER §3) |
| U-4 | Anthology : *Upper* débloqué en finissant *Alpha 3* ; **Select maintenu** en choisissant *Alpha 3* | menu de l'Anthology | GUIDE p. 4 ; SC-Hyper ; CARTE-MODULES §9.3 | A | §8.1 |
| U-5 | Anthology : Upper = la *Zero 3* CPS-2 « arrangée » façon NAOMI, avec Guile, Fei Long, Dee Jay, T. Hawk, Shin Akuma `$24`, (EX) Balrog `$25` | — | JAWIKI-FG ; DÉPÔT (ECARTS-UPPER §3) | A | façon d'obtenir `$24` / `$25` dans Upper : **non documentée** |

### 7.2 MAX (PSP)

La recherche ne contient **aucune commande de déblocage** pour MAX. Sont établis seulement : Eagle, Maki, Yun (de
*CvS2*) et Ingrid ; fins propres pour Yun, Maki et Eagle ; ids du dépôt `$26` Eagle, `$27` Maki, `$28` Yun,
`$29` Ingrid (`tools/max/pl_mapping.json`). Sur GBA, Yun, Maki et Eagle se débloquent « 一定条件下で » (JAWIKI,
conditions non précisées). Sur PS1, Guile, Evil Ryu et Shin Akuma se débloquent au temps de jeu (≈ 96 ou 8 h, 120 h,
144 h) ou par des parcours secrets du World Tour (sources japonaises non ouvertes, `06_*`, C). **Lacune à combler
avant de tester MAX.**

---

## 8. L'Anthology (PS2) : menu des jeux, options cachées, versions

### 8.1 Jeux cachés (menu `b`)

| id | élément | commande / condition | source | conf. |
|---|---|---|---|---|
| A-1 | **Upper** (« Street Fighter Alpha 3 Arranged ») | finir *Alpha 3* avec n'importe qui ; **Select maintenu** en choisissant *Alpha 3* | GUIDE p. 4 ; SC-Hyper ; JAWIKI-FG | A |
| A-2 | **Hyper Street Fighter Alpha** | US : finir tous les jeux du disque, *Upper* compris (une fois chacun, dans n'importe quel ordre) ; **Select maintenu** en choisissant *Street Fighter Alpha*. Japon : finir les 8 jeux (*Pocket Fighter* et les 3 jeux secrets compris), puis Select + *Zero* | GUIDE p. 4 ; SC-Hyper ; JAWIKI-FG | A |
| A-3 | Japon : *Alpha 2* et *Zero 2 Dash* | Select + *Zero 2* / Select + *Zero 2 Alpha* | CARTE-MODULES §9.3 ; JAWIKI-FG | A |
| A-4 | Mécanisme | fonction SELECT de `b` (fichier `0xE10`) : Select (`0x100`) tenu et bit posé dans l'octet `[*(0x19E438) + 220]` = `0x19D10DC` à l'exécution. Bits : `0x4` *Alpha 3* → *Upper* ; `0x8` *Zero* → Hyper ; `0x2` *Zero 2 Alpha* → *Dash* ; `0x1` *Zero 2* → *Alpha 2*. Posé par `0x1CB320` en fin de jeu (code `0xF5` → bit `0x8`) | DÉPÔT (CARTE-MODULES §9.3 ; `legacy/docs/ANALYSE-Widescreen-ISO.md`, « CORRECTION ») | A |
| A-5 | Ce qui manque au menu US | *Zero 2* (`ro2`) et *Zero 2 Alpha* (`ro4`) sont sur le disque, mais aucune entrée ni aucun Select n'y mène | DÉPÔT (CARTE-MODULES §9.3) ; Wikipédia en (« non inclus ») | A |
| A-6 | Balayage progressif | au démarrage, tenir △ + × : le jeu propose le mode progressif | CAPCOM-FAQ | A |

**Test PS2 (référence)** : PCSX2 avec l'ISO US. Code pnach `patch=1,EE,019D10DC,byte,0000000F`, ou l'ISO « All Unlocked »
de `legacy/tools/unlock_patcher.py`. Au menu, tenir Select et choisir *Alpha 3*, puis *Alpha*. Observer : *Upper*, puis
Hyper. ⚠ L'ancien premier essai du journal legacy donnait `0x02` pour *Upper* ; la correction (savestate) donne `0x04`,
comme CARTE-MODULES.

### 8.2 Options cachées (dans chaque jeu)

| id | élément | commande | effet | dans HSFA |
|---|---|---|---|---|
| A-7 | **Color Edit** | menu Options, tenir **R1** en choisissant Display Options | édition des palettes de tous les persos | non (écran natif PS2) |
| A-8 | **Extra Options** | Options, tenir **R1** en choisissant Game Options | EXTRA OPTION (1)-(4) : vitalité, jauges, garde, projections, relevés, minuterie des commandes, alpha counter… | **oui** : options du cœur « Extra option: … » (patch 0003, 17 bits) et `HSFA_OPT_EXTRA` au banc (OPTIONS §3) |
| A-9 | **Secret Options** | Options, tenir **R2** en choisissant Game Options | révision du jeu (dates « ver »), CUSTOMIZE (ombres des supers, voix, bogues retirés) | **non** : la révision PS2 est rangée en `+7` de la sauvegarde, puis l'octet `$BB` est aussitôt écrasé par la fonction d'application (OPTIONS §1.2) |

Source : GUIDE p. 3-5 ; le menu SECRET OPTION et ses dates sont aussi relevés dans les modules par le dépôt
(CARTE-MODULES §0.1).

| module | révisions proposées (SECRET OPTION) | recommandation du guide |
|---|---|---|
| *Alpha* (`ro1`) | 95/06/05, 95/06/27, 95/07/27 | **95/06/27** (garde les re-dizzies et le HK imparable de Sodom) |
| *Alpha 2* (`ro8`) | 96/03/06, 96/04/30 | **96/03/06** |
| *Alpha 3* (`ro3`) | 98/06/29, 98/07/27 (défaut) | **98/07/27** |
| *Zero 2* (`ro2`) | 96/02/27, 96/03/06, 96/04/30 | — |
| *Zero 2 Alpha* (`ro4`) | 96/08/05 | — |
| *Zero 2 Dash* (`ro6`) | 97/10/23 | — |
| *Pocket Fighter* (`ro7`) | 97/09/01, 97/09/04 | — |

⚠ Pour *Alpha 3*, le guide donne 98/07/27 comme version par défaut. Le dépôt a montré que le code de `ro3` suit la
**USA 980904** (journal §96, `src/hsfa/revision.py`). Les dates du menu sont peut-être des dates japonaises (980727 =
rév. 2 japonaise, AH). C'est à éclaircir si l'on veut un jour proposer la révision 980629.

---

## 9. Hyper Street Fighter Alpha (`ro9`, `sfa3hhsfa`)

### 9.1 Déroulé de la sélection (rappel)

Perso (grille 8 × 8) → **version** (ZERO / ZERO 2 / ALPHA / ZERO 3 ; curseur `$5C`) → MANUAL / AUTO → pour ZERO 3 :
**mode** (curseur `$5C` 0-7), puis **ism**. L'id `$102` vient de `grille[$116 × 4 + $5D]`, avec la grille normale
`0x5C5380` ou, si **Start est maintenu** à la validation, la grille secrète `0x5C5420` (INDEX §1.2, ETATS §1.2).

### 9.2 Versions (« `$Vx` ») : identifiants et drapeaux

| famille (écran US) | ids `$102` | drapeaux vrais `$117` (68K `$116`) | bits de `$D3` (68K `$D2`) |
|---|---|---|---|
| ZERO 3 (ALPHA3) | `$00`-`$25` | `$10` | bit 4 |
| ZERO (ALPHA) | `$30`-`$3C` | `$01` | bit 0 |
| ZERO 2 (ALPHA2) | `$40`-`$5F` | `$22` ; **`$2A`** pour les EX `$55 $56 $58-$5C` | bits 1 + 5 (+ 3 si EX) |
| ZERO 2 ALPHA (ALPHA2G) | `$60`-`$7F` | `$06` ; **`$0E`** pour les EX `$75 $76 $78-$7C` | bits 1 + 2 (+ 3 si EX) |
| ZERO 3 en Saikyo S-ISM | ids < `$30` des 12 persos de *SF2*, et ≥ `$24` | `$10` | `$D3` = **`$98`** (bits 4, 3 et 7) |

Bit 6 : jamais posé, 16 tests morts (INDEX §2.2) ; ni la recherche ni le guide n'en disent rien.

**Test** : chaque ligne `CHOIX` donne `$102=` et `$116=` (drapeaux vrais). Pour `$D2`, ajouter `HSFA_RAM_DUMP=1` avec
une capture prise pendant le combat, puis lire l'octet 68K `$FF84D2` (J1) dans `ram_<image>.bin`.

### 9.3 Persos cachés et versions EX

| id | élément | commande dans Hyper | ids attendus | source | conf. |
|---|---|---|---|---|---|
| H-1 | **EX ALPHA** (Ryu, Ken, Bison, Sagat, Zangief, Dhalsim, Chun-Li) | perso choisi, sur l'écran de version : curseur sur ALPHA (ZERO pour l'EX Chun-Li), **Start maintenu** et valider par un bouton | `$7B $7A $78 $79 $75 $76 $7C` | DÉPÔT (ETATS §1.3, vérifié à l'image) ; livre ch. Hyper ; GUIDE p. 4 (Hyper, sans détail) | A |
| H-2 | **Shin Akuma** | Akuma, Start maintenu sur ZERO 2 / ALPHA / ZERO 3 | `$54` / `$74` / `$24` | DÉPÔT | A |
| H-3 | **Chun-Li tenue *SF2*** | Chun-Li, Start maintenu sur ZERO 2 / ALPHA | `$52` / `$72` | DÉPÔT | A |
| H-4 | **Sakura aux autres couleurs** | Sakura, Start maintenu sur ZERO 2 / ALPHA | `$5D` / `$7D` | DÉPÔT | A |
| H-5 | **EX ZERO 2** Zangief, Dhalsim | Start maintenu sur ZERO 2 (leur 1re colonne) | `$55` / `$56` | DÉPÔT | A |
| H-6 | EX ZERO 2 Bison, Sagat (**en morceaux**) | Start maintenu sur ZERO 2 | `$58` / `$59` | DÉPÔT (45 tables = Ryu) | A (défaut des données PS2) |
| H-7 | **EX Balrog** | **Start maintenu à la validation du perso** sur la grille (Balrog n'a qu'une version) | `$25` | DÉPÔT (ETATS §1.3 ; cœur patch 11) | A |
| H-8 | Evil Ryu, Cammy, Akuma / Bison / Dan de ZERO, Balrog, Juni, Juli | **grille normale**, sans code | `$57 $77 $17`, `$7E $16`, `$32 $3A $3C`, `$15 $1E $1F` | DÉPÔT | A |
| H-9 | Inatteignables | `$5A $5B $5C` (EX ZERO 2 attendus : Ken, Ryu, Chun-Li), `$5E` (Cammy ZERO 2), `$12 $13 $14` (index de chargement, pas des ids choisis) | — | DÉPÔT (ETATS §1.3) | A |

**Ce que la recherche apporte sur ces versions :**
- **EX Balrog = le Balrog de l'arcade *Zero 3***. JAWIKI (section des versions console) : « AC版『ZERO3』の性能の
  バイソンも、隠しキャラクターのEXバイソンとして選択できる ». Au Japon, « M.バイソン » est le boxeur, Balrog en
  Occident (même doubleur, Kōichi Yamadera). Sur PS1, Capcom avait étoffé ses coups normaux, et la version arcade est
  restée jouable sous le nom « EX ». Le dépôt appelait `$25` « (EX) Balrog » sans en connaître le sens.
- **`$58` / `$59` en morceaux** : *Alpha 2* (US) n'a jamais eu d'EX Bison ni d'EX Sagat, seulement EX Dhalsim, EX
  Zangief et Evil Ryu (SC-SFA2, JAWIKI). Hyper n'a donc aucune donnée source pour eux, ce qui explique leurs
  45 tables par défaut (Ryu). Le même raisonnement explique pourquoi `$5A`-`$5C` (EX Ken, Ryu, Chun-Li de ZERO 2) et
  `$5E` (Cammy de ZERO 2) ne sont sur aucune grille. Le défaut vient très probablement du jeu PS2, pas du traducteur ;
  reste à le voir sur PCSX2.
- Correspondance avec les arcades : le **nombre d'appuis sur Start** (×1 / ×2 / ×5) des arcades et de *Gold* devient
  dans Hyper un seul **Start maintenu**, et la version choisie fait le reste.

**Procédures de test :**
- Tournée EX complète (déjà jouée : 52 VERSUS bons, `tools/son-hyper/tournee_ex.tsv`) :
  ```sh
  tournee_complete.py joue_linux coeur.so sfa3hhsfa.zip system sortie --extra Z:vS,Z2:vS,A:vS
  ```
- EX Balrog, avec un cœur 1-11 (roulette sur Select) : `HSFA_TOURNEE="15.Z3.g/00.Z3"`. Attendu : `$102=25`. Avec un
  ancien cœur, ou au banc MAME sans `NOROUL=1`, Start sur la grille lance la roulette (§9.6).
- **À ajouter** (non fait par le dépôt) : en combat, comparer EX Balrog et Balrog (`$15`) avec `HSFA_GESTES`. Même
  geste depuis le même état ; relever animation, dégâts et nombre de normaux distincts. Puis comparer à la référence
  `sfa3ud` (`PERSO=15`).
- À la main (RetroArch) : sur l'écran de version, tenir **Start** puis appuyer sur LP. Observer la plaque VS
  (« ALPHA2G » ou « ALPHA2 ») et le sprite (kimono de *SF2* pour EX Ryu).

### 9.4 Modes de ZERO 3 et S-ISM « SHADALOO » A / B / C / D

**Commande.** Après avoir choisi la version ZERO 3 (et MANUAL / AUTO), l'écran de mode propose NORMAL, MAZI, SAIKYO
et CLASSIC (Haut / Bas, curseurs 0-3). **Sur un mode, tenir Start et appuyer sur ← ou →** : la flèche disparaît, on
a choisi la « 2e version » du mode. Valider ensuite par un bouton. Sources : GUIDE p. 4 (« New ISM Choices ») ; SC-Hyper
(« highlight Normal mode, hold Start and press left or right ; select with any button ») ; JAWIKI-FG ; DÉPÔT (table de
navigation `0x5C54C0`, mesuré). Conf. **A**. Les curseurs 3 à 7 sautent l'écran d'ism.

| mode (curseur) | nom JAWIKI-FG / guide / SC | champs (journal `CHOIX`) | plaque VS / HUD (DÉPÔT) | effets selon les sources | conf. des effets |
|---|---|---|---|---|---|
| NORMAL (0) | — | — | ism choisi | aucun | A |
| MAZI (1) | 本気 | 68K `$15B = 1` (PS2 `$15A`) | ism, témoin « ON » | dégâts plus forts ; une manche perdue = partie perdue (GUIDE p. 140, JAWIKI) | B (Hyper non vérifié) |
| SAIKYO (2) | サイキョー流 | 68K `$130 = 1` | ism | jauge de garde réduite (DÉPÔT : garde `$24C` **et** étourdissement `$2CD` divisés par 2) | A |
| CLASSIC (3) | クラシカル | `$15F=01`, ism X imposé | « CLASSIC » | pas de super, pas de jauge de garde ; musique « EX » des persos de *SF2* (DÉPÔT, SON-HYPER §2.3) | A |
| **Classic S-ISM (4)** | **SHADALOO-A**, rouge ; GUIDE « S-ISM 4 (Red) » ; SC « Red S-Ism » | `$123=80` (→ PS2 `$123 = 2`) | « S-ISM » rouge, jauge « SUPER / CHARGE OK » | la plus proche de la S-ISM de *Zero 3* ; **Bison devient Final (Shin) Bison** ; coups de la série *Vs.* (§9.5) | A (recoupements §9.5) |
| **Mazi S-ISM (5)** | **SHADALOO-B**, bleu ; GUIDE « S-ISM 2 (Blue) » | `$123=02`, ism X imposé | « S-ISM » bleu | coups de X-ISM, **parade** (→ contre un coup haut, ↓ contre un coup bas, à l'impact) et **super cancel** (spécial → super) ; musique « variante B » (DÉPÔT) | A |
| **Normal S-ISM (6)** | **SHADALOO-C**, vert ; GUIDE « S-ISM 1 (Green) » | `$123=82` | « S-ISM » vert | **chain combos** (au sol et en l'air, ordre LP, LK, MP, MK, HP, HK), **garde repoussante** (→ + LP + MP + HP pendant la garde), alpha counter par **↘ en arc de DP + PPP ou KKK** pendant la garde, **sans coût de jauge** (JAWIKI) ; coups d'A-ISM | A (chaînes, poussée) ; B (alpha counter gratuit) |
| **Saikyo S-ISM (7)** | **SHADALOO-D**, rose ; GUIDE « S-ISM 3 (Pink) » ; SC « Pink S-Ism » | `$15F=81`, ism X imposé ; `$D2 = $98` | **aucune plaque, aucune jauge** (DÉPÔT) | les 12 persos de *SF2* (Ryu, Ken, Chun-Li, Dhalsim, Zangief, Honda, Blanka, Guile, Vega, Balrog, Sagat, Bison) en version *Champion Edition* : gros dégâts, pas de super, chaînes CPS-1 ; **interdit en tournoi** (infinis) | A |

Réserves sur les sources :
- La **couleur** de SHADALOO-D : « Pink » pour le guide et SC ; le dépôt n'a vu ni plaque ni jauge en combat. Le rose
  est sans doute la couleur de l'écran de mode.
- Réservé aux persos de *SF2* : le dépôt l'a mesuré (ligne `+$30` de `0x5C54C0` si `0x5C5510[$117] = 0`), SC l'écrit
  (« No other characters can select this Ism »). Les ids ≥ `$24` (Shin Akuma, EX Balrog) y ont aussi droit.
- Les surnoms de 2006 (DS-ism, CE-ism, 3-ism, M-ism, IGN) ne viennent pas de Capcom.
- La musique : JAWIKI affirme que le mode bleu donne aux persos de *SSF2X* leur thème de la version 3DO, et que le rose
  passe aux thèmes de *SF2* d'arcade. Les mesures du dépôt ne l'ont ni confirmé ni infirmé (livre, ch. Hyper).

### 9.5 Ce que fait chaque S-ISM : listes de coups à essayer

D'après SC-Hyper (« currently found character changes »), confirmé en partie par le guide (p. 5 : « characters like
Ken gain access to the outrageous attacks they had available in the Capcom vs SNK games ») :

| S-ISM | perso | commande à essayer | effet attendu |
|---|---|---|---|
| A (rouge) | Bison (Vega au Japon) | — | **Shin Bison** (aura, coups du boss) |
| A | Ryu | ↓↘→ ↓↘→ + K | Shin Shoryuken |
| A | Ken | ↓↘→ + P **en l'air** | grosse boule aérienne ; Hadoken et Shoryuken animés façon *Vs.* |
| A | Akuma | super Hadoken au sol et en l'air | grosse boule, animations *Vs.* |
| A | Sakura | ↓↙← + P ; ↓↘→ + P en l'air ; arc de DP + PPP ou KKK ; **LP, LP, →, LK, HP** | Hadoken anti-aérien ; Hadoken aérien ; téléportation ; **Shun Goku Satsu** |
| A | Evil Ryu | ↓↘→ + P en l'air ; **↓ + MK au sommet du saut** | boule aérienne ; coup de pied plongeant |
| A | Guy | ↓ ↓ + bouton | téléportation |
| A | Charlie | ↓↘→ + K en l'air | Flash Kick aérien |
| A | Dhalsim | ↓↘→ + P en l'air | boule aérienne ; animations *Vs.* |
| A | Dan | — | animations *Vs.* du Gadoken et du super Gadoken |
| B (bleu) | tous | → à l'instant du coup (haut), ↓ (bas) ; spécial annulé en super | parade ; super cancel |
| C (vert) | tous | LP → LK → MP… ; → + LP + MP + HP en garde ; arc de DP + PPP / KKK en garde | chaînes ; bouclier et recul de l'adversaire ; alpha counter, jauge `$11E` inchangée |
| D (rose) | les 12 de *SF2* | coups de *SF2'* ; tenter une super | pas de super ; dégâts nettement plus forts |

**Recoupements avec le code (DÉPÔT) :**
- La Classic S-ISM (PS2 `$123 = 2`) est la seule valeur qui change la table d'animations (`0x6A7D54`, BLOC-HYPER §1.1).
  Les persos concernés : Evil Ryu `$17`, Akuma `$02`, Shin Akuma `$24`. Ce sont ceux dont SC décrit des **animations
  *Vs.*** : bonne concordance.
- La Saikyo S-ISM (`$F0 < 0`, PS2 `$15E = $81`) change les animations (`0x6A7C94`) de Ryu `$00`, Ken `$01`, Chun-Li
  `$04`, Bison `$0A`, Sagat `$0B`, Dhalsim `$0F`, Zangief `$10`, Balrog `$15`, Honda `$18`, Blanka `$19`, Vega `$1C`,
  Guile `$20`. Ce sont exactement les **12 persos de *SF2*** : versions *Champion Edition*.
- **Bison en Classic S-ISM** : le dépôt a vu l'octet 68K `$15C = $80` (`0x2A1FD4`), avec un « effet visible non
  identifié » (ETATS §1.4). La recherche dit que Bison y devient **Final Bison** (SC, JAWIKI-FG). Côté arcade, la table
  de musique de SFA3 a un pseudo-id conditionné par `$15D` (ECARTS-UPPER, musique) : sans doute la musique du boss.
  **Hypothèse forte : PS2 `$15D = $80` = drapeau « Final Bison »** (test §6.3, point 3).
- Seuil de jauge `$90` dès que `$123 ≥ 2` (`0x2DA6F4`) et jauge « SUPER » : cohérent avec JAWIKI (« ゲージ形状は
  X-ISM準拠 »).

**Procédures de test :**
1. **Sélection des 4 S-ISM** (déjà fait : 231 VERSUS de modes) :
   `HSFA_TOURNEE="00.Z3.m4/01.Z3.m5,0a.Z3.m7/0b.Z3.m6,04.Z3.m3/0f.Z3.m1"` (rappel : dans `tournee.h`, `.m4` = Normal
   S-ISM, `.m5` = Mazi, `.m6` = Saikyo, `.m7` = Classic). Attendu dans les lignes `CHOIX` : `$123=82`, `$123=02`,
   `$123=80`, `$15F=81`, `$15F=01`, puis `$5C=01` pour MAZI. Le journal n'imprime pas `$15B` : le lire dans
   `ram_<image>.bin` (`HSFA_RAM_DUMP=1`), octet 68K `$FF895B` pour J2.
2. **Final Bison** : `HSFA_RAM_DUMP=1 HSFA_TOURNEE="0a.Z3.m7/00.Z3"`, capture en combat. Lire l'octet 68K `$FF855C` :
   attendu `$80`. À l'écran, comparer le sprite et les coups (Psycho Crusher, téléportation) avec le Final Bison de
   `sfa3ud` en Final Battle.
3. **Parade (bleu)** : J1 Ken Mazi S-ISM, J2 Ryu. Avec `HSFA_GESTES` : J2 lance un Hadoken (↓↘→ + LP), J1 tape →
   pendant 2 images au contact, à différents décalages. Observer l'absence de dégâts (`$50` de J1 inchangé) et
   l'effet de parade. Même essai sans S-ISM pour contrôle.
4. **Garde repoussante (vert)** : J1 en garde contre une série de coups, puis → + LP + MP + HP. Observer le bouclier et
   le recul de J2 (`$12` de J2 qui augmente).
5. **Alpha counter gratuit (vert)** : mettre la jauge de J1 à `$30` pendant **une seule image**, sinon le poke
   masque la consommation (mot `$11E` : `HSFA_POKE="N-N+1:FF851E:00,N-N+1:FF851F:30"`) ; faire un alpha counter en
   garde ; relire le mot `$FF851E`. Attendu : inchangé (JAWIKI). Contrôle : même geste en A-ISM, où la jauge baisse.
6. **Rose** : Ryu Saikyo S-ISM, jauge forcée au maximum, ↓↘→↓↘→ + P. Attendu : rien (pas de super). Mesurer la baisse
   de vie de l'adversaire sur un HP debout, en Saikyo S-ISM puis en NORMAL.
7. **Mazi** : `HSFA_TOURNEE="00.Z3/01.Z3.m1"` (J2 en Mazi ; la tournée met J2 K.O.). Attendu si la règle de l'arcade
   s'applique au VERSUS : fin du match après **une** manche (une seule ligne `MANCHE` par sélection). Puis mesurer les
   dégâts d'un même coup en NORMAL et en MAZI (`HSFA_TOURNEE_PV=1`). Le dépôt ne connaît pas l'effet de `$15A` / `$EC`
   au-delà de l'init. du perso (INDEX §4.1).

### 9.6 Roulette (perso au hasard)

| | commande | source | conf. |
|---|---|---|---|
| cœur HSFA (patch 11, cœurs du 2026-10-16 et suivants) | sur la grille, **Select (Pièce) maintenu** + un bouton | DÉPÔT (ETATS §1.1, FBNEO-HYPER, patch `0007-HSFA-roulette-touche-piece.patch`) | A |
| ancien cœur, banc MAME | Start maintenu sur la grille (Start et drapeau de roulette viennent du même bouton) | DÉPÔT | A |
| PS2 | bit `$0100` du moteur (natif `0x23D20`), distinct de START : **touche non établie**, sans doute Select | DÉPÔT ; le guide n'en parle pas | C |

Le drapeau est recopié dans l'octet `$D3` du joueur (68K `$FF84D3` / `$FF88D3`). Il y a aussi des cases « ? »
(`$26`-`$29`) sur la grille `0x5C5650`.

**Test** : `HSFA_TOURNEE="00.Z3.r/01.Z3"` sans `HSFA_NOROUL`, 5 sélections ; attendu : des `$102` différents d'une
sélection à l'autre pour J1. Sur PS2 : tenir Select puis valider, et noter s'il y a roulette. À tester aussi : valider
sur une case « ? » sans rien tenir.

### 9.7 Écran OPTION : générique STAFF caché

Au menu d'Hyper, valider OPTION en tenant le bouton `$0400` des entrées du portage (`$C214`), c'est-à-dire **HP** (B3
au banc), lance la tâche `0x3BCCC0` : générique « STAFF », ~3 000 images, puis retour au menu (ETATS §2.1). Sur PS2,
HP correspond à **R1** par défaut : c'est vraisemblablement « R1 + OPTION », comme R1 / R2 + Game Options ailleurs dans
l'Anthology (déduction, C). La recherche n'a trouvé **aucune** mention publique de ce générique ; les noms de l'équipe
2006 (« N. Minomiya »…) restent à relever (`09_*_verif`).

**Test** : cœur ou banc. Menu des modes, curseur sur OPTION, tenir L (HP) et valider. Observer le défilement STAFF.
À refaire avec la ROM `OPTION_RETOUR=1` (défaut) : le correctif redirige la tâche OPTION native, mais la branche STAFF
est testée avant. À vérifier, puis faire des captures pour relever les noms.

### 9.8 Random Battle (combats aléatoires sans fin)

| | commande | source | conf. |
|---|---|---|---|
| Anthology, Hyper compris | choisir **Versus** en tenant **△ + × + R2** (JAWIKI-FG : « △、×、R2を押しながら決定 »), ou **■ + ✖ + R2** (GUIDE p. 52 et 140, pour *Alpha 2*, *Gold*, *Alpha 3*, *Pocket Fighter*) | JAWIKI-FG ; GUIDE | B ⚠ |
| effet | « 設定された中からキャラクター、モードをランダムで選出し延々と対戦を繰り返す » ; existe aussi pour Hyper, **avec des réglages d'ISM** | JAWIKI-FG | B |

Dans le code d'Hyper, `0x98DA0` (tirage 0..63 → `$102`, homologue de `port_202B70`) et `0x991A0` (pose `$132` et les
champs de mode) sont de bons candidats. La table aléatoire `0x5B5CD0` contient `$54`, `$55`, `$56`, `$78`-`$7C` : le
mode aléatoire tirerait donc **aussi des EX**. Déduction (C).

**Test** : cœur, menu des modes, curseur sur VERSUS. Tenir MP + LK + HK (△ × R2), valider ; puis recommencer avec
LP + LK + HK (■ ✖ R2). Observer : sélection sautée, persos et modes changeant à chaque combat. Au banc : point d'arrêt
sur `0x98DA0` (adresse 68K dans `carte_image.txt`).

### 9.9 Autres réglages utiles au test

- **VS MODE (2P) = COM** (option du cœur) : la console joue J2 (JAWIKI-FG ; DÉPÔT, OPTIONS §4).
- **Timer = Infinity** : `∞` affiché (DÉPÔT).
- Hyper n'a ni ARCADE, ni SURVIVAL, ni DRAMATIC : les entrées du menu mènent au VERSUS (DÉPÔT, ETATS §2.2) ; aucun code
  de titre des arcades (Z3-6 à Z3-11) ne s'y applique. Le choix des modes passe par l'écran de mode du §9.4.

---

## 10. Conflits entre sources

| # | sujet | version 1 | version 2 | comment trancher |
|---|---|---|---|---|
| 1 | **Juni / Juli** (Zero 3) | Juli = ↑ / ↓, Juni = ← / → (SC-FAQ, SC-Juni, SC-Juli, GUIDE p. 140) | Juli = ← / →, Juni = ↑ / ↓ (HDAT, AH) | référence `sfa3ud` : lire `$FF8502` (§6.3, point 1), et le test des bits de `$11A` avant `$1E9EA` |
| 2 | Durée sur Karin | 1 s (GUIDE) | 2 s et plus (SC, pages persos) ; 5 s (SC-FAQ, HDAT, AH) | chronométrer à la référence |
| 3 | Classic / Saikyo (titre de Zero 3) | Classic = HP + HK, Saikyo = LP + LK (HDAT, AH, GUIDE, GameFAQs) | l'inverse (marpirc, non ouvert) | 3 sources contre 1 : retenir HP + HK = Classic ; vérifier une fois |
| 4 | LK + MK + HK au titre de Zero 3 | Dramatic Battle (HDAT, AH, arcade) | **Shadaloo Mode** (GUIDE, Anthology) | les deux sont sans doute vrais, chacun dans son jeu : tester `sfa3ud` puis `sfa3hsfa` |
| 5 | Random Battle | △ + × + R2 (JAWIKI-FG) | ■ + ✖ + R2 (GUIDE) | tester les deux (§9.8) |
| 6 | Evil Ryu (*Alpha 2* US) | Start maintenu pendant tout le trajet (GUIDE) | Start 1 s, trajet, puis Start maintenu + bouton (HDAT, SC) | même trajet Ryu → Adon → Akuma → Adon → Ryu ; tester les deux façons |
| 7 | Evil Ryu dans *Zero 2* japonais | présent (HDAT `sfz2j`) | US seulement (SC, JAWIKI) | probable copie dans HDAT ; tester sur `sfz2j` |
| 8 | Chun-Li tenue *SF2* (*Zero 2*) | Start 3 s (JAWIKI, GUIDE) | 5 s, puis LP / MP / HP ou LP + MP + HP (HDAT) | 5 s satisfait les deux ; tester 3 s |
| 9 | Bogue de Karin à 99 % | mode Mazi (AH) | mode Saikyo, avec l'Izuna Drop de Vega (atwiki, non ouvert) | sur `sfa3` 980629 |
| 10 | Couleur de SHADALOO-D | rose (GUIDE, SC, JAWIKI-FG) | ni plaque ni jauge en combat (DÉPÔT) | regarder l'écran de mode au moment du choix |
| 11 | Code de la CPS Changer | bas + LK + HK, J2 (JAWIKI) | bas + LP + HK (`05_*_verif`) | coquille de la note : retenir LK |
| 12 | Révision d'*Alpha 3* dans l'Anthology | 98/07/27 par défaut (GUIDE) | code = USA 980904 (DÉPÔT §96) | dates du menu = dates japonaises ? |
| 13 | Bit de déblocage d'*Upper* | `0x02` (1er essai legacy) | `0x04` (correction legacy, CARTE-MODULES) | retenir `0x04` |

---

## 11. Ce que la recherche apporte au dépôt, et ce qui reste inconnu

### 11.1 Réponses ou pistes nouvelles pour les rapports

1. **Sens des S-ISM** (ETATS §6, question 2 ; INDEX §6, point 1) : curseur 4 = SHADALOO-A (rouge, Classic, Final
   Bison, coups *Vs.*), 5 = B (bleu, parade + super cancel), 6 = C (vert, chaînes + garde repoussante + alpha counter
   gratuit), 7 = D (rose, *SF2'* des 12 persos de *SF2*). Les tables d'animations du dépôt concordent (§9.5).
2. **`$15C = $80` (68K) sur Bison en curseur 4 = Final Bison** (SC, JAWIKI-FG). Hypothèse : drapeau « boss » repris de
   l'arcade (PS2 `$15D`).
3. **EX Balrog `$25` = le Balrog de l'arcade *Zero 3*** (« EXバイソン », JAWIKI).
4. **`$58` / `$59` et `$5A`-`$5C`, `$5E`** : ces versions n'ont jamais existé dans *Alpha 2*, d'où l'absence de données.
   Ce sont des défauts du jeu PS2, non du traducteur. Reste à voir `$58` / `$59` sur PCSX2.
5. **`$122` = la S-ISM (« Shadaloo-ISM »)** : en arcade, c'est l'ism des boss CPU de Dramatic Battle (JAWIKI) ; dans
   l'Anthology *Alpha 3*, le Shadaloo Mode (LK + MK + HK) la rend jouable (GUIDE). Cela éclaire SON-HYPER §2.3 (« le
   test `$122` n'a pas eu d'effet au banc ») : le test est à refaire **en S-ISM réelle**, et dans `sfa3hsfa`.
6. **Mazi** : règle « une manche perdue = défaite » et dégâts accrus, inconnues du dépôt (champ `$15A` / `$EC`).
7. **Random Battle** existe dans Hyper (JAWIKI-FG) : candidat `0x98DA0` / `0x991A0` / table `0x5B5CD0`.
8. **STAFF** : HP (R1 sur PS2) tenu en validant OPTION, par analogie avec R1 / R2 dans les autres jeux (déduction).
9. **Upper** a lui aussi un écran de mode avec S-ISM par commande (JAWIKI). À essayer dans `sfa3uhsfa` (U-3).
10. **SFA3 arcade** : déblocage par semaines, couleurs du titre, code « Input » du menu de test. Le dépôt ne sait pas
    dans quel état `ro3` met ces déblocages (sans doute tout ouvert, par les défauts du portage).
11. **Musique** : selon JAWIKI, le bleu donne les thèmes 3DO de *SSF2X* et le rose ceux de *SF2* arcade. Piste pour
    nommer les variantes B et « EX » de SON-HYPER (à vérifier à l'écoute).

### 11.2 Inconnues que la recherche ne résout pas

- **Touche PS2 de la roulette** (bit moteur `$0100`) : le guide n'en dit rien.
- **Bit 6 de `$D3`**, l'**état A** de la sélection (choix commun, `$A2(A5) ≥ 3`), les octets `+$20`-`+$27` des attaques,
  les nouveaux champs `$F3`-`$FE`, `$260`-`$262` (INDEX §6) : aucune source publique.
- **Codes musique jamais entendus** `01E6`-`01EB`, `01F4`-`01F7` (fin de la table « EX », index ≥ `$18`) : peut-être
  Honda, Blanka, Vega ou Guile en Classic ou en Saikyo S-ISM ; la tournée de 231 modes ne les a pourtant pas
  obtenus.
- **MAX** : aucune commande de déblocage dans la recherche.
- Comment *Upper* (Anthology) donne `$24` (Shin Akuma) et `$25` (EX Balrog) ; comment l'Anthology rend Final Bison
  jouable dans *Alpha 3* / *Upper* (JAWIKI-FG l'affirme, sans commande).
- Le sens exact des Extra Options (bit 4 « SP GAUGE », OPTIONS §5) : le guide ne le détaille pas.

---

## 12. Liste de contrôle des tests (par ordre d'utilité)

| prio | test | où | résultat attendu | sert à |
|---|---|---|---|---|
| 1 | Juni / Juli (§6.3, point 1) | `sfa3ud` (référence) | `$FF8502` = `$1E` pour la direction de Juli | trancher le conflit n° 1 |
| 2 | Final Bison par Classic S-ISM (§9.5, point 2) | cœur / fork, puis `sfa3ud` | `$15C` (68K) = `$80` ; sprite Shin Bison | §11.1, points 1-2 |
| 3 | Parade, garde repoussante, alpha counter gratuit, pas de super en rose (§9.5, points 3-6) | cœur, `HSFA_GESTES` | effets du §9.4 | valider les S-ISM au-delà de la sélection |
| 4 | Mazi : une manche perdue = fin (§9.5, point 7) | cœur | une seule ligne `MANCHE` par sélection | §11.1, point 6 |
| 5 | EX Balrog contre Balrog contre arcade (§9.3) | cœur + `sfa3ud` | normaux de l'arcade sur `$25` | §11.1, point 3 |
| 6 | EX Zangief / Dhalsim ZERO 2 et EX ALPHA sans super (§3.4, §4.2) | cœur + `sfa2u` / `sfz2al` | pas de super, pas de garde aérienne | fidélité des EX |
| 7 | Random Battle (§9.8) | cœur | combats aléatoires sans fin | §11.1, point 7 |
| 8 | STAFF (§9.7) | cœur | générique, noms à relever | crédits 2006 (livre) |
| 9 | Codes de titre et Shadaloo dans `sfa3hsfa` (§6.3, point 2) | traduction SFA3 | `$15E`, `$15A`, `$131`, `$122` posés | §11.1, point 5 |
| 10 | S-ISM dans Upper (U-3) | `sfa3uhsfa` | plaque S-ISM | §11.1, point 9 |
| 11 | `$58` / `$59` et roulette sur PCSX2 (§8.1) | PS2 réelle ou PCSX2 | en morceaux ? touche de la roulette ? | défauts PS2 contre traduction |
| 12 | Déblocage SFA3 (§6.3, point 4) | `sfa3ud`, EEPROM vierge | titre crème, puis message « HERE COME NEW CHALLENGERS » | savoir ce que fait `ro3` |
