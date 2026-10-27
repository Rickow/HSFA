# Mélange par objet : choix (a) bit d'objet ou (b) bloc de palettes — mesures et recommandation

Agent `agent_alpha`, 2026-10-18, après la réponse de la session MAX : le mélange est décidé **par objet**, champ
`+0xAA` → sprite `+0x56`, mode 1 = additif. Rien n'est codé en dur avant la décision du coordinateur.

## 1. Mesures

**Outil** : cœur instrumenté hors patch (`fbneo_mesure/`, `coeurs/mesure_hsfa.so`). Variable `HSFA_OBJ_STATS`. Pour
chaque entrée **brute** de la liste d'objets écrite par le programme traduit (`HsfaEclater`), il relève :

- les bits candidats ;
- la palette utilisée, avec l'état du jeu `$FF8000/4/8`.

**Parties** (`tests/mesure.sh`, `outils/analyse_mesure.py`, sorties `tests/essais/mes_*/stats.txt`) :

| partie | images |
|---|---|
| nonreg SFA3 | 9 000 |
| nonreg Upper | 9 000 |
| nonreg Hyper | 12 000 |
| Upper MAX (zip 2b10 figé), Eagle : DP + P, ¼ cercle + pied, boutons au hasard | 14 000 |
| Upper MAX, Maki : mêmes entrées | 14 000 |

Total : **10,99 millions d'entrées brutes**.

### 1.1 Bits libres (choix a)

| bit (liste brute) | entrées où il est posé | sens pour le matériel et le cœur |
|---|---|---|
| X 10, X 11, X 12 | **0** | aucun : le convertisseur garde `x & $3FF` (position) et `x & $E000` (priorité) |
| Y 10, Y 11, Y 12 | **0** | aucun : le convertisseur garde `y & $3FF` ; `y >> 13` = emplacement de banque |
| attribut bit 7 | **0** | **utilisé par le matériel** : objet placé par rapport aux registres de décalage (MvC). Le cœur (`Cps2ObjDraw`, `a & $80`) et MAME (`colour & 0x80`) l'appliquent. Le convertisseur le recopie (`at & $00FF`). **À écarter** |

Le convertisseur (cœur `HsfaEclater` et banc `work/mame/banc_sprites.lua`, même code) produit des tuiles 16×16 :

- X de sortie : bits 0-9, 10-11 (bits 18-19 du code) et 13-15 (priorité). **Le bit 12 vaut toujours 0** ;
- Y de sortie : bits 0-9 et 13-14 ;
- attribut de sortie : bits 0-7.

Ni `Cps2ObjDraw` (FBNeo) ni `cps2_render_sprites` (MAME) ne lisent le bit 12 de X.

### 1.2 Palettes OBJ libres en combat (choix b)

État de combat `$FF8000/4/8 = 2/4/6` (le plus long de chaque partie). Palettes **jamais utilisées** par un objet :

| partie | palettes jamais utilisées en combat |
|---|---|
| SFA3 | 1-4, 8-14, 17, 24, 26 |
| Upper | 1-4, 6, 10-15, 24 |
| Hyper | 2-4, 6-19, 26, 31 |
| Eagle (MAX) | 2-4, 6, 8-15 |
| Maki (MAX) | 1-4, 8-14, 17 |
| **intersection** | **10, 11, 12, 13, 14** (5 palettes) |

Limites :

- 1-4 et 6-9 sont les emplacements des joueurs, qui n'ont simplement pas servi dans ces parties ;
- toutes les palettes 0-31 ont un contenu non nul dans toutes les parties : le contenu ne prouve rien ;
- la couverture est faible : peu de persos, la CPU joue peu. Rien ne prouve que 10-14 sont libres pour tous les persos
  (effets d'un natif, flashes de super, écrans spéciaux). Il faudrait une campagne VERSUS de tous les persos avec
  supers.

## 2. Comparaison

| critère | (a) bit X 12 de la liste brute | (b) bloc de palettes « additives » |
|---|---|---|
| granularité | par objet et par image : la règle PSP elle-même (calque `$33` additif seulement pour les animations 1-6) | par objet aussi (EFFET_W déplace la base de palette), mais seulement vers des emplacements libres |
| ressources | 1 bit jamais posé (0 / 11 M), sans sens matériel | 5 palettes jamais vues (10-14), non prouvées libres. Il en faut 2 par joueur et par sous-palette mélangée (Eagle +1/+2, Ingrid +3, Maki ?). Deux MAX à 2 sous-palettes : 4 palettes |
| couleurs | celles de l'emplacement du joueur : suivent les flashes, assombrissements de super et palettes de coup | **copies** : ne suivent pas les modifications en place des palettes 0-9 (flash d'impact, brûlure, électrocution, assombrissement) sans recopie à chaque image (≈ 1 000 cycles) ou alias dans le cœur |
| 68K | EFFET_W : après l'appel d'affichage (`$19D9A`), parcourir les entrées que l'objet vient d'ajouter (pointeur de liste avant et après) et faire `ORI.W #$1000` sur leur mot X si `+0xAA` = 1. Coût seulement pour les objets additifs ; moteur commun inchangé | EFFET_W : changer la base de palette de l'objet si `+0xAA` = 1, la remettre sinon ; plus la copie des sous-palettes au chargement (et à chaque modification) |
| cœur / banc | convertisseur : garder le bit (`x & $F000` au lieu de `x & $E000`, une ligne dans `HsfaEclater` et dans `banc_sprites.lua`). Rendu : `x & $1000` et registre de mode global ≠ 0 → mode du registre | aucun changement de conversion ; le registre par palette (0010 v2) suffit |
| non-régression | identique tant que le registre global vaut 0, et même s'il est posé (bit jamais posé par les natifs) | identique tant que les registres valent 0 |

## 3. Recommandation : (a), bit 12 du mot X brut

Raisons :

- C'est la règle PSP (par objet, par image) sans contrainte de palettes.
- Il n'y a pas de copie de palettes à garder synchronisée.
- Le bit est prouvé jamais posé (0 sur 10,99 M) et n'a de sens ni pour le matériel ni pour les deux convertisseurs.
- Le côté 68K reste local à EFFET_W.

Proposition :

1. **Liste brute** : bit 12 du mot X d'une entrée = « objet mélangé ». Posé par EFFET_W quand le `+0xAA` de l'objet
   (champ fourni par l'agent d'intégration) vaut 1.
2. **Convertisseurs** : cœur `HsfaEclater` et banc `banc_sprites.lua`, `x & $E000` → `x & $F000`. Le bit passe tel
   quel dans les tuiles. Ce sont deux lignes ; le Lua du banc est partagé, la modification serait décrite et non
   appliquée.
3. **Registre** : `$804220` = mode appliqué aux objets marqués. 0 = bit ignoré (défaut), 1 = additif, 2/3 = alpha,
   4 = soustractif.
   - Garder aussi les registres par palette de 0010 v2 ? Le PSP n'en a pas besoin. Je propose de les **retirer**
     pour ne garder qu'un octet, ce qui réduit la réservation à `$804220-$804221`, et de garder le mélange déjà écrit
     (cps_mix, cps_mix16, deux passes MAME).
   - À ta décision : l'autre option est de tout garder.
4. **États** : même méthode qu'en v2 (zone finale facultative), un octet au lieu de 32.

Si tu choisis (b), il faut d'abord une campagne VERSUS de tous les persos pour prouver que 10-14 sont libres. Il
faudrait aussi des registres d'**alias** (palette p affichée avec les couleurs de la palette s, en additif) pour
éviter les copies désynchronisées.
