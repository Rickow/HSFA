# cps2recomp : ce qui peut servir à HSFA (tour d'ensemble, 2026-11-10)

Dépôt public `tmcleroy/cps2recomp` (GPL-3), lu le 10 novembre 2026 (commit `b9064a5`). Portages natifs de jeux CPS-2 :
le programme 68000 de chaque jeu est traduit à l'avance en C++ et tourne sur une machine CPS-2 réécrite. Une trentaine
de jeux, dont `sfa` (Europe 950727), `sfa2u` (USA 960430), `sfz2al` (Asie 960826), `sfa3u` (USA 980904), `hsf2`.

**Règle de licence.** Notre dépôt public est sous MIT : on n'y verse **aucun code** de cps2recomp. Ce qu'on peut prendre :
des faits (adresses, rôles, mesures), cités, et des idées de méthode, réécrites chez nous. Faire tourner ses outils
**en local** pour analyser nos propres fichiers est permis (c'est de l'usage, pas de la redistribution) ; leurs
sorties restent hors dépôt, comme chez lui.

Le croisement détaillé pour *Alpha 3* est dans `J-CROISEMENT-CPS2RECOMP-SFA3.md`.

## 1. Le plus utile tout de suite : ses notes sur *Alpha*, *Alpha 2* et *Zero 2 Alpha*

Hyper joue chaque personnage dans ses versions ZERO, ZERO 2, ALPHA et ZERO 3. Notre banc compare surtout la version ZERO 3
à l'arcade (matrice des coups : 22 écarts restants), et les versions anciennes seulement pour les voix. Ses
`games/sfa/PROGRESS.md` (331 lignes), `games/sfa2/PROGRESS.md` (603) et `games/sfz2al/PROGRESS.md` (110) donnent, pour
les trois bornes d'origine, ce qu'il faut pour en faire des oracles au banc :

- structure des joueurs (`$FF8400` / `$FF8800`, vie en +40 dans *Alpha*), routine des dégâts (`$00FA06` pour un coup,
  `$021148` pour une projection dans *Alpha*), test de coup et de boîtes (`$00F4C0`, `$0104B8`), étourdissement, jauge ;
- horloge, résultat de manche (`$FFAE0C` dans *Alpha*), décor (`$FFAE00`), file de sons, caméra ;
- ce qui distingue *Zero 2 Alpha* d'*Alpha 2* dans le code (règles « façon *SSF2* » du mode EX : pas de garde en l'air,
  pas de relevé rapide ; portée de garde ; durée d'étourdissement ; gain de jauge).

**Piste** : étendre la matrice des coups aux versions ZERO, ZERO 2 et ALPHA d'Hyper, contre `sfa`, `sfa2` et
`sfz2al`, avec ces adresses comme points de mesure (après vérification de chacune au banc). Attention aux révisions : son
`sfa` est l'européenne 950727, le nôtre à vérifier.

## 2. Méthodes à reprendre (en idée)

- **`portmap.py` — relier deux programmes de la même famille.** Il trouve, entre deux jeux faits du même programme
  (*Vampire Savior* et sa suite, *Alpha 2* et *Zero 2 Alpha*), où chaque instruction et chaque table du premier se
  trouve dans le second : ancres sur des suites d'octets identiques aux adresses près, puis appariement des instructions
  par ce qu'elles font. **Pour nous** : propager automatiquement les ≈ 9 200 noms de l'index d'*Alpha 3* vers nos ROM
  retraduites d'Upper et d'Hyper (aujourd'hui, `CARTE-ro5` et `CARTE-ro9` à la main et par la rosette). Le faire
  tourner en local sur nos ROM serait le test le plus rapide.
- **`graft.py` — greffer les personnages d'un autre jeu.** Le code de l'autre jeu est posé tel quel à une adresse libre ;
  ses adresses absolues et ses variables sont déplacées vers celles du jeu hôte, ses branchements courts vers le moteur
  commun passent par des crochets. C'est le même problème que notre **greffe du mode Arcade d'Upper sur Hyper** (voie B)
  et qu'une éventuelle greffe d'un jeu de la famille *Alpha 2*. Sa liste des cas (code propre, adresses nommées,
  variables, pointeurs chargés depuis des tables, entrées de tables) est une bonne grille de contrôle pour notre greffe.
- **`aiscripts.py` — lire l'intelligence artificielle.** L'ordinateur d'*Alpha*, d'*Alpha 2* et d'*Alpha 3* est un
  interpréteur de scripts (quatre banques par personnage : plans, tactiques…) ; l'outil les imprime en texte et vérifie
  une partie enregistrée contre eux. **Pour nous** : contrôler les scripts convertis des personnages de MAX, et regarder
  quels scripts Hyper donne aux versions anciennes (ceux d'*Alpha 3* ou ceux de leur jeu d'origine ?). Question neuve,
  utile aussi au livre.
- **Décors invités (`fight/guest_stages.h`).** Pour montrer le décor d'un autre jeu, il fait tourner la carte de ce
  jeu à côté, dans un combat figé, caméra calée sur celle de l'hôte, avec sa musique, et dessine les combattants
  par-dessus. **Pour la piste des décors de *SF2* dans Hyper** (`I-DECORS-SF2.md`) : une alternative sans retouche de
  tuiles (décor d'origine, non « façon *Alpha* »), au prix d'une deuxième carte émulée, lourde sur console portable.
- **Écran large** : déjà relevé (README §7) : butées de caméra par décor, contrôle automatique des colonnes dessinées
  (`stage_ends.py`).

## 3. Exactitude et déterminisme

- **Le minutage de la carte** (`docs/TIMING.md`, `docs/ARCADE_ACCURACY.md`) : une CPS-2 ne donne pas tous ses cycles au
  68000 ; il a modélisé ce que la carte en prend, pour retrouver les ralentissements de la borne. Notre chapitre note
  que FBNeo et MAME tirent des adversaires différents parce que le hasard dépend des cycles : ses mesures peuvent dire
  lequel des deux est le plus proche de la borne.
- **Rollback et retour arrière** (`docs/VERIFYING.md`, `check_rollback.sh`) : il vérifie qu'une image rejouée après un
  chargement d'état donne exactement le même résultat. **À vérifier chez nous** : notre cœur FBNeo ajoute un second
  QSound (rejeu) et un lecteur de flux musicaux ; sont-ils bien dans les sauvegardes d'état ? Sinon, le *run-ahead* de
  RetroArch et un éventuel jeu en ligne désynchronisent le son. Test simple : sauver, charger, comparer l'audio.

## 4. Pour le livre

- ***Hyper Street Fighter II*** (CPS-2, 2004 ; `games/hsf2/PROGRESS.md`) : ses versions passent par des **tables par
  version** (couleurs, animations : une table par version, puis un long par personnage). *Hyper Street Fighter Alpha*
  (2006), lui, teste la version **bit par bit dans tout le moteur** (1 445 tests de l'octet `$D3`). Deux façons de faire
  le même produit, à deux ans d'écart : bon contraste pour les chapitres 10 et 12, à citer comme observation de
  cps2recomp, avec prudence (ses notes ne disent pas que *HSF2* n'a aucun test dans le code).
- cps2recomp est lui-même un « voisin » au sens du chapitre 12 (recompilation statique du 68000 vers du code natif,
  l'inverse de notre chemin) ; l'échange du ticket n° 244 peut y figurer.

## 5. Plus tard

- Portage natif d'HSFA sur ses outils, en collaboration (voir la discussion du 9 novembre) : ses `recompz80.py` (le pilote
  son Z80 en code) et sa bande-son personnalisée couvrent aussi notre musique.

## Ordre proposé (rien n'est lancé)

1. Vérifier au banc les contradictions de `J-CROISEMENT-CPS2RECOMP-SFA3.md` §2 (court).
2. Sauvegardes d'état du cœur avec rejeu et flux (§3) : un test, risque réel pour les utilisateurs.
3. `portmap.py` en local sur `sfa3ud` → Upper / Hyper retraduits (§2) : si ça marche, gros gain pour l'index.
4. Matrice des coups étendue aux versions anciennes (§1).
5. Scripts de l'ordinateur des versions d'Hyper (§2) : pour MAX et pour le livre.
