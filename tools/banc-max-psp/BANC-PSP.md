# BANC-PSP : mode B du banc des coups (PSP = oracle, Upper MAX = candidat)

Agent `banc_max_psp`, 2026-10-25. Tout est dans `work/banc_max_psp/`. Aucun commit. Les dossiers `agent_ppsspp_banc/` et `banc_coups/` sont lus, jamais modifiés.
But : pour chaque coup d'un perso MAX (ou d'un natif contre un perso MAX), jouer la MÊME séquence d'entrées sur la PSP (SFA3 MAX EU, PPSSPP sans fenêtre,
images exactes) et dans Upper (MAME, module `max` du banc des coups), comparer, et trouver automatiquement les coups qui ne se comportent pas comme sur PSP.

## 1. Usage

```
./banc_psp.sh <candidat> --perso Eagle --ism A [--adv ryu] [--tests palette|tableau|<fichier.tsv>] [--filtre regex] [--x1 300]
              [--scanobj] [--recompare] [--detail ID --plage a-b] [--rejouer-psp] [--sans-upper]
```
- `<candidat>` : copie figée d'une construction MAX (même disposition que `banc_coups/max15`, avec `env_max_cache.txt`). Rien n'est écrit dedans.
- Sorties : `resultats/<candidat>/<nom>.tsv` (un verdict par coup), `<nom>_objets.txt` (pistes d'objets PSP / Upper appariées), journaux Upper dans
  `essais/<candidat>/<nom>/log.txt`, relevés PSP en cache dans `essais/psp/psp_<perso>_<adv>_<ism>[_x<n>].json` (ne dépendent pas du candidat :
  une nouvelle construction ne relance que MAME ; `--rejouer-psp` force la PSP).
- `--detail ID` : tableau image par image « PSP | Upper » (états, X, Y, vie) pour lire une divergence ; `--recompare` refait les verdicts sans MAME.
- `outils/matrice.py resultats/<cand> nom1 nom2 ...` : verdicts côte à côte (ex. même coup contre plusieurs victimes).
- Jeux d'essais : `palette` (normaux, lancers, quarts, dragons, demi-cercles, charges, 360°, doubles quarts : comme `banc_max.sh max`), `tableau` (lignes du tableau
  des coups pour un perso du jeu, pour les natifs ; `--perso Mika`), ou un fichier `scenarios/*.tsv` (`id<TAB>nom<TAB>script en tours<TAB>distance hexa<TAB>type<TAB>observation`).

Le 1er passage d'un couple (perso, adversaire, ISM) crée l'état PSP `etats/<perso>_<adv>_<ism>.ppst` (≈ 6 s : navigation par curseur jusqu'à l'ENTRAÎNEMENT).
Les tests suivants rechargent cet état (≈ 1 s chacun). Un MAME par lancement (≈ 30-60 s quel que soit le nombre d'essais d'un perso).

## 2. Correspondances PSP ↔ Upper (mesurées)

| grandeur | PSP (structure joueur 0x498 o, J1 0x092E3EA0, J2 +0x498) | Upper (structure $400, J1 $FF8400, J2 $FF8800) | règle |
|---|---|---|---|
| états | octets +4..+7 | octets $4..$7 | **chaque octet PSP × 2** (PSP `01000501` = Upper `02000a02`) ; neutre PSP `01000001` = `02000002` |
| position X | long 16.16 en +0x10 | mot $12 (entier) | mêmes pixels ; on compare le **déplacement** depuis la ligne de départ |
| position Y | long 16.16 en +0x14 | mot $16 | mêmes pixels, sol = 40 des deux côtés (Upper non signé : lire en 16 bits signés) |
| vie | mot +0x70 (0x90) | mot $50 (0x90) | identique ; dégâts = vie perdue (identiques sur les normaux d'Eagle) |
| ID perso | octet +0x152 | octet $102 | MAX : PSP Eagle 26, Maki 27, **Yun 28, Ingrid 29** ; Upper 26, 27, **2D, 2E** ; natifs : mêmes n° (Ryu 00, Mika 1A) |
| ISM | octet +0x182 (A 00, X FF, V 01) | octet $132 | identique |
| temps | **4 tours de jeu pour 3 images** (compteur 16 bits RAM 0x092E51C6 : +1, +1, +2) | 1 tour par image (SPEED NORMAL forcé), compteur `$FF851C` | on compare **tour par tour** |
| boutons | LP carré, MP triangle, **HP L**, LK croix, MK rond, **HK R** | B1..B6 | (la table de `trace_appels.py` avait HP / HK inversés) |

Le réglage SPEED de l'écran de sélection PSP (TURBO 2 / 1 / NORMAL, touche haut) **ne change pas** la cadence mesurée (4/3 dans les trois cas) : le banc le règle à NORMAL
mais ne s'y fie pas, il lit le compteur de tours.

### Comparaison tour par tour
Une image PSP contient 1 ou 2 tours (cycle 1, 1, 2, prévisible) et la sonde de fin d'image ne voit que l'état du dernier. On rééchantillonne donc Upper aux tours
visibles de la PSP : pour chaque image PSP (tour e = fin de l'image), on compare l'état Upper du tour e (journal Upper : tour = `compteur $FF851C` - valeur à la ligne 8).
Les entrées : le script est exprimé en tours ; la PSP lit le pad une fois par image, on lui applique les touches du **1er tour** de l'image, puis on **rejoue côté Upper
les touches effectives tour par tour** (chaque tour de l'image reçoit les touches de l'image). Même entrée des deux côtés, par construction.
Piège du banc des coups : son 1er jeton de séquence perd un tour ; le banc PSP préfixe `1:N`.

### Verdicts
- **IDENTIQUE** : mêmes états J1 et J2, mêmes X, Y, vies, à chaque image.
- **PROCHE** : écarts d'au plus 2 px, ou un état identique à celui d'Upper un tour avant / après (±1 tour), mêmes dégâts. (Tolérance justifiée : la PSP ne voit que 3 tours sur 4,
  un état d'un seul tour peut tomber du côté invisible ; 2 px = arrondi de la partie fractionnaire PSP.)
- **DÉCALÉ(n)** : même suite mais décalée de n tours à partir de la 1re divergence (ex. Flying Peach de Mika : la PSP passe 4 tours en `0a` avant le spécial).
- **MUR** : la 1re divergence est une position près d'un bord de scène (la scène PSP, 480 px, n'a pas les mêmes bornes que celle d'Upper) : non significatif.
- **DIFFÉRENT** : le coup ne sort pas d'un côté, dégâts différents, état différent (même avec ±1 tour), position différente de plus de 2 px, exception Upper. La 1re divergence est donnée (tour, champ, valeurs).
- **NC** : rien ne sort des deux côtés (manip à revoir).
- États d'initialisation (dernier octet 00) vus un tour d'un seul côté : ignorés (règle du banc des coups).
- La PSP en ENTRAÎNEMENT rend la vie après ~1 s sans coup : la comparaison s'arrête à la première hausse de vie PSP.

## 3. Objets (effets d'impact, projectiles, étincelles)
PSP : 5 réservoirs d'objets de 0xC0 o (`0x09512170` 8, `0x09512770` 32, `0x09513F70` 16, `0x09514B70` 16, `0x09515770` 16 ; allocateurs 0x1EE74 / 0x1EEAC / 0x1EEE4 / 0x1EF1C /
0x1EF54, `a0` = base du réservoir) ; octet +0 = actif, X / Y 16.16 en +0x10 / +0x14. On relève les objets nouveaux ou changés par rapport à la fin de l'attente.
Upper : zones d'objets `$FF8C00`-`$FFC000` par pas de `$100` (option `--scanobj` ; sans elle les deux réservoirs `$FF9400` / `$FFA000` du banc des coups).
Les pistes (création, fin, position relative à J1) sont appariées par instant de création (±3 tours) : `<nom>_objets.txt`. Information, sans verdict.

(La suite — limites, cas Mika / Maki, MAX — est complétée au fil des jalons.)

## 4. Découvertes (mesurées)
- Cadence PSP : 4 tours pour 3 images, réglage SPEED sans effet (compteur 0x092E51C6, cycle +1 +1 +2).
- Boutons PSP : HP = L, HK = R (et non l'inverse). Entrée de J2 : routine 0x55650 (a0 = joueur) lit +0x2F0 (bits : gauche 1, droite 2, bas 4, haut 8, LP 10, MP 20, HP 40, LK 80, MK 100, HK 200) ; le banc y pose un point d'arrêt conditionnel (a0 = J2) et écrit le mot voulu : J2 scripté sur PSP (script2 des fichiers de scénarios).
- Réservoirs d'objets PSP : 0x09510F28 (24, projectiles), 0x09512170 (8), 0x09512770 (32, effets : étincelles type 04, poussières 0f), 0x09513F70, 0x09514B70, 0x09515770 (16 chacun) ; objets de 0xC0 o, octet +0 actif, type en +2, X / Y 16.16 en +0x10 / +0x14.
- Entraînement PSP : vie de J1 rendue aussitôt, vie de J2 rendue environ 1 s après le dernier coup.
- Les spéciaux sortent sur PSP 2 à 4 tours plus tard que dans Upper (état normal `0a` d'abord) pour Mika (natif) et Yun : à vérifier sur les MAX (palette).
- Les murs de scène diffèrent de quelques pixels (écrans 480 / 384) : verdict MUR.

## 5. Limites
- Conditions G: / Y: du banc des coups et NT (combos, suites) non rejouées ; suites de super (Hashiru) : scénario scenarios/mika_hashiru.tsv à passer.
- Manips : 4 tours par direction, 360° avec diagonales (adaptation PSP, patch en mémoire de notation.py) ; 720° non reconnu des deux côtés.
- Un seul adversaire (Ryu) par défaut ; stage aléatoire figé par l'état PSP.
- Deux PPSSPP en parallèle : dossiers de travail séparés obligatoires (voir ETAT.md).
