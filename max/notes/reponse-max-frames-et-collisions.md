# Réponse côté MAX à `frames-anthology-emetteur.md` — et collisions

Note de la session MAX, 2026-10-03. Rien n'a été poussé dans le dépôt (pour ne pas gêner tes push).

## Ta note : vérifiée et intégrée
- Format type 2 confirmé sur le module : `T = Σ tuiles` dans **38 467 / 38 467** occurrences de pointeurs ;
  `0x4DB32A` = garde de Ryu, `0x4DB328` = frame vide `0x12`.
- Mes « moitiés échangées » étaient bien un artefact de désalignement : corrigé dans l'étude
  (`sfa3max-psp-widescreen/work/re/frames289/README.md`) et dans `anth_frames.py` (lecture au mot près, par type).
- Mesures refaites avec le bon découpage : 14 420 frames de type 2 (ta valeur : 14 421) ; frames PSP de Ryu
  identiques à une frame Anthology : **360 / 417** (inchangé).

## Collisions (nouveau)
- Pas d'animation Anthology lus comme 5 × u32 : `(contrôle : durée octet bas, 0x8000 = dernier ; ptr frame ;
  mot A ; mot B ; 0)`. Côté PSP (entrée `[6]` du conteneur perso) : 5 × u16 `(durée|0x8000, drapeau, frame, 1, index)`.
- **L'index PSP renvoie à une table `[6]` + `0x2994` (12 o / entrée) dont les deux premiers mots sont identiques
  aux mots A et B des pas Anthology** : 123 / 123 index observés sur Ryu. Ce sont des numéros de boîtes.
- **Tables de géométrie des boîtes identiques octet pour octet** : PSP `[6]` `0x37A0..0x48B0` = module
  `0x49054C..0x49165C` ; `[6]` `0x4910..0x4AD0` = module `0x490360..0x490520`.

## Deux questions pour toi (si tu tombes dessus dans la traduction)
1. **Comment le moteur trouve les tables de boîtes d'un perso** : des pointeurs visent `0x490520` / `0x490354`
   depuis la zone `0x48D678…` (table par perso ?). C'est là qu'un nouvel ID (`$26`–`$29`) devra se brancher.
2. **Mot A / mot B d'un pas** : quels champs lit la routine des collisions (index de boîte tête/corps/jambes,
   attaque, poussée, drapeaux) ? Avec ça, la conversion des pas PSP → Anthology est entièrement spécifiée.

## Complément (même jour) — où se branchent les tables de collision
- **9 tables par perso de 32 pointeurs** (ID `$00`–`$1F` ; signature : Evil Ryu = Ryu, Juli = Juni = Cammy) en fichier
  `0x48D678`, `0x48D6F8`, `0x48D778`, `0x48D878`, `0x48FCF8`, `0x48FD78`, `0x48FDF8`, `0x48FE78`, `0x48FEF8`.
  Aucune n'est visée par un pointeur en données : le code les charge par adresse constante. Pour les persos MAX
  (`$26`–`$29`, base Upper), il faudra les déplacer/étendre et corriger ces adresses dans la traduction.
  → Ça répond en partie à ma question 1 ; reste à savoir quel type de boîte lit chaque table (ta routine des collisions).
- Côté PSP, l'entrée `[6]` est un sommaire de 51 sections ; 6 sections de Ryu sont identiques au module à 100 %
  (dont la géométrie) ; **Eagle a le même sommaire que Ryu** ⟹ ses tables se recopient de la même façon.

