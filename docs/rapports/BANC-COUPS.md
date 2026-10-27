# Banc MAME de test des coups (SFA3, Upper, Hyper)

Version publiée le 2026-10-24, résumée du rapport de l'agent `banc_coups` (2026-10-18, `work/banc_coups/BANC-COUPS.md`,
hors dépôt). On n'y donne que la méthode, les outils et les résultats chiffrés.

> ⚠ **Données protégées.** La liste des coups à jouer vient d'un tableau tiré d'un guide imprimé de l'utilisateur
> (journal §167). Ce tableau, ses textes et ses noms de coups ne sont **pas** dans le dépôt, et ce rapport n'en
> reprend rien. Les sorties du banc (verdicts par coup) restent elles aussi hors dépôt. Les outils qui lisent le
> tableau sont dans `tools/guide-coups/` ; le tableau se demande à l'utilisateur.

Le banc décrit ici tourne sous MAME (fork et banc Lua). Un banc équivalent, sans MAME, existe dans le cœur FBNeo :
`tools/sondes-recherche/banc_coups.py` et `banc_matrice.py` (journal §169-§170,
[recherche/D-SONDES](recherche/D-SONDES.md)). Les scripts du banc MAME (`banc_coups.sh`, `lua/banc_coups.lua`,
`outils/*.py`, `frame_data.py`, `banc_max.sh`) ne sont pas encore versés dans `tools/`.

## 1. Résultats (constructions v150, 2026-10-18)

Un « coup » = une ligne du tableau pour un perso et un isme (ou une version d'Hyper), toutes variantes de boutons et
de directions regroupées.

| module | oracle | OK | décalé | KO | NC | NT | OK / (OK + décalé + KO) |
|---|---|---|---|---|---|---|---|
| SFA3 (`ro3`, 28 persos × X/A/V) | arcade `sfa3ud`, comparaison exacte | 963 | 11 | 29 | 35 | 605 | **96,0 %** |
| Upper (`ro5`, 28 persos × X/A/V) | arcade `sfa3ud` (Juli, Juni sans oracle) | 852 | 43 | 119 | 24 | 605 | 84,0 % |
| Hyper (`ro9`, 27 persos, 6 versions) | ZERO / ZERO 2 / ALPHA : le coup sort et rend la main ; ZERO 3 : même famille d'effet que `sfa3ud` | 1 420 | — | 119 | 91 | 947 | 92,3 % |

- Variantes jouées et justes : 2 382 (SFA3), 2 105 (Upper), 3 842 (Hyper).
- Hyper par version : ZERO 79 %, ZERO 2 82 %, ALPHA 84 %, ZERO 3 X / A / V 97 / 97 / 98 %.
- Upper : 94 des 119 KO ne diffèrent que par l'animation (même suite d'états, mêmes dégâts). Ce sont des données
  d'Upper différentes de l'arcade, attendues pour une version arrangée. Les autres KO d'Upper sont ceux de SFA3, plus
  4 écarts de dégâts.
- NC : rien ne sort non plus à l'arcade (manipulation ou condition à revoir). NT : non testable par ce banc (combos,
  enchaînements, conditions de décor ou de menu).

## 2. Défauts trouvés et suite donnée

| # | défaut | cause établie ensuite | état |
|---|---|---|---|
| 1 | Hyper, supers des versions ZERO / ZERO 2 / ALPHA : exception (talon `$A08`) dans 98 des 133 lignes de super testées, 16 persos ; les mêmes supers en ZERO 3 passent | traducteur : un `ANDI.L #$00FFFFFF` effaçait l'étiquette `$01` du bloc `$940000` | règle `RETAG24` (v151, en préparation) |
| 2 | lancers aériens (Chun-Li, Gen, Charlie) : l'atterrissage de 4 images (`$6 = 06`, `$7 = 04`) disparaît ; J1 reprend la main plus tôt | portage PS2 | non corrigé |
| 3 | Alpha Counter : la garde de proximité de J1 arrive une image plus tard qu'à l'arcade | banc (ordre de J1 et J2 tiré au hasard) | sans objet |
| 4 | super de Cammy en ISM A : il s'arrête trop tôt (sous-état `$16` au lieu de reboucler) | traducteur : aide `roxr`, `EXG` et `BCLR` perdus (journal §171) | règles `EXG_PILE_D`, `AIDE_ROXR`, `BITOP_DN` (v151) : même résultat que l'arcade au banc |
| 5 | octets 3, 8 ou 10 du pas d'animation différents de l'arcade (5 persos) | donnée du module PS2 | non corrigé |
| 6 | Upper : pieds de Balrog et quelques dégâts différents de l'arcade | version arrangée | attendu |

Causes 1 à 5 : rapport `DEFAUTS-BANC.md`, publié avec la v151.

## 3. Méthode

1. **Notation → appuis** (`outils/notation.py`). Directions relatives (avant / arrière résolus à chaque image d'après
   la position réelle des joueurs, miroir automatique côté J2), quarts, demi-cercles, 360° (trois tours mesurés à
   l'arcade), 720°, charges (120 tours), boutons simultanés, suites, martèlement, maintien et relâche, coups en l'air
   (saut avant, vertical, au sommet, au décollage), lancers au contact, lancers aériens, Alpha Counter (J2 attaque,
   J1 tient arrière jusqu'au blocage puis fait la manipulation).
2. **Plan** (`outils/plan.py`) : les lignes du perso et de l'isme, plus les lignes communes (Alpha Counter, lancer
   générique, activation du Variable Combo).
3. **Banc** (`lua/banc_coups.lua`, MAME sans image ni son, nvram et cfg propres, jamais `-state`) : VERSUS à deux
   joueurs, J1 = perso testé, J2 = Ryu passif. SFA3 et Upper : `$102` et `$132` imposés pendant la sélection ; Hyper :
   sélection par les manettes (copie de `tournee_hyper.lua`), version et isme compris. Au combat stable, une
   **sauvegarde d'état par `manager.machine:save`** est rechargée avant chaque coup : essais reproductibles à l'octet.
   Positions, vies et jauge sont remises.
4. **Mesures** (`outils/journal.py`), par image : sous-états `$4-$7` de J1 et J2, positions, vies, numéro de spécial
   `$AA`, pas d'animation `$1C` et son empreinte (octets 0-3 et 8-19 du pas de 20 octets ; 4-7 = pointeur de frame,
   relogé par la traduction), objets des réservoirs `$FF9400` / `$FFA000`, tours de jeu (`$FF851C`), compteur `$32`,
   exceptions (PC ≥ `$400000` ou talons `$A00-$A80`).
5. **Verdicts** (`outils/compare.py`) :
   - avec oracle (SFA3, Upper) : même suite d'états des deux joueurs, même animation, mêmes dégâts, mêmes objets,
     même `$AA` → OK ; même suite décalée d'une image → décalé ; sinon KO, avec la première divergence ;
   - sans oracle (Hyper ZERO / ZERO 2 / ALPHA) : le coup sort, se termine et rend la main, sans exception ;
   - famille d'effet (Hyper ZERO 3 contre `sfa3ud`) : idem, plus la même famille (spécial, super, lancer, objet).
6. Le journal de l'arcade est mis en cache : après une correction du traducteur, seule la traduction est rejouée.
   Phase SFA3 : environ 40 minutes avec 4 MAME.

**Pièges de mesure (à garder)** :
- **Cadence turbo** : en turbo, la traduction saute des tours de jeu, et une image de deux tours n'en montre qu'un.
  Le banc force SPEED SELECT = NORMAL (`$FF80A2`, octet arcade `$A3`) et compte les durées **en tours de jeu**.
  Hyper remet la vitesse au début du combat (adresse non trouvée) : d'où le critère sans oracle.
- Les états d'initialisation (`$7 = 00`) vus une seule image sont ignorés (leur visibilité dépend de l'ordre des
  objets).
- La phase de l'animation d'attente au moment de la sauvegarde diffère d'une machine à l'autre : l'animation n'est
  comparée qu'à partir de la sortie du neutre.
- Hyper ne rend la main qu'après « FIGHT » : sauvegarde à 400 images de combat stable (150 ailleurs).

## 4. Frame data des persos ajoutés

- **Référence** : SuperCombo Wiki, pages « Street Fighter Alpha 3 », lues par l'API MediaWiki publique le 2026-10-18
  (la page HTML est protégée par un contrôle anti-robot, qui n'a pas été contourné). 268 coups ; frame data publiée
  seulement pour quelques persos, surtout les normaux au sol.
- **Mesure** (`outils/frame_data.py`, vitesse NORMAL) : on compte les images où le jeu avance (compteur `$32` ou pas
  qui change ; l'arrêt sur coup ne compte pas). Démarrage, actif (pas dont l'**octet 9** est non nul : boîte
  d'attaque), récupération, avantage au contact et en garde.
- **Étalonnage** sur Ryu et Ken de l'arcade : démarrage 27/27 et actif 25/25 exacts ; récupération exacte debout,
  +1 accroupi ; avantages à −1 (convention de la référence). Après étalonnage : 122 grandeurs conformes, 19 écarts
  (surtout des avantages à ±1-2), 9 non mesurables : le bruit de la référence elle-même.
- **Résultats** : Ryu et Ken traduits = arcade à l'image près ; Juli et Juni d'Upper = arcade à l'image près ; Balrog
  d'Upper diffère sur les coups de pied (version arrangée). Persos sans référence publiée (persos d'Upper et de MAX) :
  normaux mesurés quand même, pour servir de référence aux versions suivantes.

## 5. Non-régression de l'intégration MAX (`banc_max.sh`)

Question : l'ajout des 4 persos MAX dans Upper casse-t-il quelque chose ? Candidat = copie figée d'une construction
MAX (lot 2b14), référence = Upper v150. Cinq étapes :

1. **Coups des natifs** : mêmes plans qu'au §1, plus une palette générique de commandes pour les persos sans ligne ;
   comparaison image par image (`outils/compare_strict.py`). Si une image diffère, on réaligne par tour de jeu : même
   jeu avec une image sans tour en plus = **ralenti** (coût processeur ajouté), sinon **différent**.
2. **Fins** des natifs `$00-$25` en Arcade : fin atteinte, nombre de manches, durée à ±1 %.
3. **Persos MAX** : palette générique de commandes × X/A/V (aucune liste de coups MAX n'existe) ; le coup sort, rend
   la main, sans exception.
4. **Croisés** : VERSUS MAX contre 8 natifs, en J1 puis en J2, entrées aléatoires à graine fixe, K.O. forcé après
   900 images : pas d'exception, au moins 2 manches en 24 000 images.
5. **Arcade des MAX**, jusqu'à la fin.

Résultats sur le lot 2b14 (copie figée, 2026-10-18) :

| étape | résultat |
|---|---|
| 1. coups des natifs | 3 061 variantes identiques, 62 ralenties (une image sans tour de plus), **5 différentes** (Rolento, ISM X) |
| 2. fins des natifs | 3 identiques sur 17 persos ; 14 diffèrent par le nombre de manches jouées (une fin par la durée, −4,1 %) |
| 3. persos MAX | 530 commandes OK, 486 sans effet (NC), 4 KO |
| 4. croisés | 64 VERSUS sur 64 sans exception |
| 5. Arcade des MAX | Eagle, Maki, Yun et Ingrid : fin atteinte et finie |

Les écarts des étapes 1 et 2 sont classés « régressions » par l'outil ; leur analyse est en cours (session de
non-régression MAX) : le nombre de manches d'une partie dépend aussi du hasard, sensible au temps processeur.

## 6. Limites

- Hyper tourne en turbo pendant le combat (la vitesse est remise par le jeu).
- Les arcades SFA1, SFA2 et Gold ne servent pas encore d'oracle pour Hyper ZERO / ZERO 2 / ALPHA.
- Frame data limitée aux normaux au sol (spéciaux de la référence non structurés).
- NC : surtout des coups aériens sans état spécial et des coups conditionnels, à scripter au cas par cas.
