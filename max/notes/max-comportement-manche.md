# Comportement de manche des persos MAX (11/11/2026)

Piste tirée de la décompilation PSP US theweathervane/sfa3max-decomp (`round_behaviour`, GPL-3 : idées et adresses
seulement, aucun code repris). Adresses EU (EBOOT ULES00235) et Upper (ro5) relevées ici.

## Le mécanisme
- **PSP** : table s8 en 0x20B434, 5 rangées de 42 (index = perso +0x152 + 42 × groupe), lue vers 0x2D708 ; valeur non nulle
  -> +0x173, sinon +0x173 = +0x182 (l'ism). Valeur 2 : Bison, Sagat, Balrog, Cammy, Vega, Juli, Juni, Balrog (2) selon le
  groupe. **Places MAX $26-$29 : 0 dans toutes les rangées.**
- **Upper** : homologue 0x61BA10 (PS2 ; arcade image $B1D50), 3 rangées de 40 (ID `$103`, +$28, +$50), routine $5535C ;
  `$122(A0)` = `$133(A0)` (l'ism), puis la valeur de la table si elle n'est pas nulle. Groupe 1 : adversaire CPU (`$124`) ;
  groupe 2 : modes `$169(A5)` / `$15C(A5)`. Rangées 0-2 d'Upper = rangées 0-2 de la PSP (accord 32/32 sur les ID 0-31).
- L'intégration recopie la table agrandie à 48 (`agrandit_max.py`) : Yun `$2D` / Ingrid `$2E` = copie de l'entrée 0 (Ryu = 0)
  dans les rangées 1-2 ; entrée 47 = ancienne entrée 39 (variante Juli / Juni).

## Écart corrigé
- La place `$27` d'Upper est la copie de Juli : Maki y lisait **2** dans les rangées 1 et 2 (PSP : 0).
- `tables_id_max.py` donne désormais les 3 rangées : Eagle / Maki 0 partout, Yun / Ingrid 0 en rangée 0 ; rangées 1-2 de
  Yun / Ingrid : copie de l'entrée 0 (integre_max ne pose qu'en rangée 0 de la copie agrandie).
- Contrôle : aucun code d'Upper ne pose ni ne teste `#$27` dans `$102/$103` ; la place 39 ne sert nativement qu'à la
  variante Juli / Juni des portraits et des noms (déplacée en 47 par l'intégration).

## Mesures (banc MAME, Upper MAX v160 : max54 = avant, max55 = après)
- Maki J2 (VS contre Ryu), `$124` forcé (groupe 1) : `$122` = 2 avant, 0 après (= ism `$133` = 0). `$124` + `$15C` forcés
  (groupe 2) : idem.
- Arcade de Maki (Maki humaine : groupe 0, jamais touchée) : journal max55 = journaux des bancs max52 / max53 / max54
  (a875fe06). Croisé Juli contre Maki (J2) : max55 = max54 (5f918d4c).
- En jeu normal, l'écart n'était pas atteint : l'Arcade ne fait jamais jouer un MAX par le CPU.

## Greffe (Hyper, ro9) : constat, rien de fait
Même table en $9C160 (PS2 0x5B62A0, routine $12618, index `$117`), suivie de pointeurs : avec des ids d'Upper, la rangée 2
donnerait $28 = 64, $29 = 102, $2D = 102, $2E = 41. À étendre ou remplacer quand les MAX entreront dans la greffe.
