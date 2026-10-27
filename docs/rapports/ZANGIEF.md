# ZANGIEF — blocs blancs dans l'usine de Zangief (Upper, ro5)

Dossier : `<workspace>/work/agent_zangief/` (rien n'a été modifié ailleurs).

## Conclusion

**Ce n'est ni le programme traduit, ni une palette, ni une donnée de décor d'Upper non portée.** Les blocs sont des
**tuiles 32×32 de scroll3 de code 0**. Dans le conteneur 32×32 d'Upper `e525`, l'entrée 0 de la table vaut 0 = « tuile
vide, toute à 15, transparente » (`anthgfx.py`). `hsfa_plans.py` ne range pas ces tuiles vides (`HSFA_PLANS_VIDE15`
vaut 1 par défaut pour ro9 seulement). La zone reste donc à **zéros = pen 0 OPAQUE** dans `hsfa_plans.bin` (`$3A00000`,
base `$3A0`). Chaque case de code 0 se dessine alors comme un aplat de la **couleur 0 de sa palette** (attribut de
la case) : blanc, crème, rouge sombre, vert pâle, orange… Ce sont les « blocs blancs ».

- Usine : couches (CPS-B `$2D0E`) de bas en haut = scroll1 (plafond sombre, lampes), scroll3, scroll2. Le haut de
  l'écran est fait de cases scroll3 de code 0 qui doivent laisser voir scroll1. Opaques, elles le cachent.
- SFA3 (ro3) n'a pas ce défaut : avec les tables (`f312.bin[0]` = `FFFFFFFF`), le repli `c + $B00` vise la tuile
  arcade `$4B00`, entièrement à 15. **Régression du §120** (passage aux bases `$804200`), cachée jusqu'ici par le
  rendu identique des démos.
- Seul le code 0 est en cause dans la plage utile (0-4533) ; les 42 autres entrées vides (4534-4575) ne sont pas
  rangées non plus. Le code 1 est une vraie tuile entièrement à 0 : rien à changer.

## Reproduction (fork `sfa3hx`)

- `lance.sh` reprend le lancement de `nonreg_ro5.sh` avec des dossiers nvram, cfg et snap propres, `nice -n 19`,
  sans `-state`. Variables : `PERSO`, `STG`, `NF`, `DUMPAT`, `TAG`, `ISO`, `PLANS`.
- `lua/usine.lua` force le décor par une prise sur `$FF8100` (`STG`, 20 = usine) puis lance `tournee.lua`
  (J1 = Zangief `10`). Aux images de combat listées dans `DUMPAT`, il vide la VRAM `$900000-$93FFFF`, les registres
  CPS-A/B et `$804200`, la RAM et la palette MAME, et prend une capture. Avec `ISO=n`, le plan n est affiché seul,
  sans les objets.
- `py/vis.py <tag> 3` liste les cases scroll3 visibles (code, attribut). Usine (`iso3_c700`) : 40 % des cases
  visibles sont de **code `0000`** avec des palettes `00/02/04/06/09/0A/0C/0D/0F/10/1D`, ce qui correspond exactement
  aux aplats.
- Captures : `cap/iso_planche.png` (lignes : tous les plans, scroll1, scroll2, scroll3 ; la 4e colonne est la seule
  où l'isolement a pris), `cap/avant_apres.png`.

## Correctif (essayé sur copie)

Pour les fichiers partagés (je ne les ai pas modifiés), deux possibilités :
1. régénérer avec `HSFA_PLANS_VIDE15=1 MODULE=ro5 hsfa_plans.py` ;
2. ou, mieux, changer le défaut dans `src/hsfa/hsfa_plans.py` (et `github/src/hsfa/…`) :
   `VIDE15 = os.environ.get("HSFA_PLANS_VIDE15", "1" if profils.NOM in ("ro5", "ro9") else "0") == "1"`.

Ensuite, reconstruire l'archive FBNeo `sfa3uhsfa.zip` (`work/fbneo/paquet_fbneo.py`, qui lit
`mame_ro5/hsfa_plans.bin`). Le cœur n'a pas besoin d'être recompilé. `banques_hx/plan2.bin` ne change pas.

Copies dans mon dossier :
- `hsfa_plans_vide15.bin` (12 828 672 o), produit par `py/plans_vide15.py` à partir du fichier partagé. Il est
  **identique octet pour octet** à la sortie du générateur officiel lancé avec `HSFA_PLANS_VIDE15=1` dans
  `gen/hsfa_plans.bin`, sorties redirigées vers mon dossier.
- Fichier partagé actuel : md5 `37bf75d768552397bfcb647d42af21ab`.

## Vérification à l'image

- Usine : à entrées identiques, la VRAM est identique avant et après (le programme n'est pas en cause). Les blocs
  disparaissent et le plafond sombre de scroll1 réapparaît (`cap/avant_apres.png` : ligne 1 avant, ligne 2 après ;
  lignes 3 et 4 = scroll3 seul).
- **Balayage des 38 décors** (`balayage.sh`, Zangief contre Cody, capture à l'image 100 du combat) : 35 capturés
  (`10`, `1A`, `4A` ont fini la manche avant l'image 100). **16 décors avaient des aplats**, tous corrigés :
  `00 02 04 06 08 0C 16 1E 20 24 28 2E 32 44 48` (+ `2C`, voir plus bas). On y voit des ciels et fonds en aplat
  orange, rouge, bleu, crème, et même magenta (décors `06`, `32`). Seul `3A` a 4 pixels de différence. Aucun décor
  n'est dégradé par le correctif. Planches : `cap/balayage_0.png`, `cap/balayage_1.png`, `cap/balayage_2.png`
  (avant à gauche, après à droite).
- Le défaut est donc **général à Upper** sur scroll3, pas propre à l'usine. Les captures FBNeo 4:3 et widescreen
  ont la même cause, puisque l'archive embarque le même `hsfa_plans.bin`.

## Hors sujet relevé

- Le décor forcé `$2C` est illisible (motif bruité plein écran) avant **et** après le correctif. C'est un autre
  problème, peut-être un décor non prévu pour cet adversaire ou ce mode quand on le force ; non étudié.
