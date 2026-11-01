# Décors de *Super SF2 Turbo* dans Hyper, recolorés « façon *Alpha* » : idée de pilote

Étude du 2026-10-30, rien n'est lancé. À reprendre après la greffe Arcade.

## Idée

Importer des décors de *Super SF2 Turbo* (CPS-2, même matériel qu'*Alpha 3*) dans Hyper, par exemple pour SHADALOO-D
et les persos de *SF2'*. On garde leurs éléments et leur dessin, mais on les recolore pour qu'ils s'accordent au rendu
d'*Alpha*.

## Faisabilité

- **Import** : même chaîne que le décor d'*Alpha 2* (`docs/rapports/DECOR-SFA2.md`) : relevé des trois plans de
  tuiles, des défilements ligne par ligne et des objets animés. Les décors de *SF2* ont moins d'objets en sprites
  qu'*Alpha*, ils sont donc plus simples à importer.
- **Recoloration par règles** (sans IA) :
  - remapper chaque palette vers des rampes mesurées sur les décors d'*Alpha 3*, matière par matière (ciel, pierre,
    bois, végétation, foule) ;
  - remplacer le tramage en damier par une teinte intermédiaire ou par des bandes ;
  - rester dans les 16 couleurs par palette.
- **Hors de portée des règles** : le trait, les formes, la lumière peinte, les animations propres à *Alpha*.
- **Pièges** : une palette sert à plusieurs tuiles (on règle par palette, pas par zone) ; les palettes animées (eau,
  lumières) se convertissent étape par étape.

## À trancher avant

1. **Source** : ces décors ne sont pas sur l'ISO de l'*Anthology* ; il faudrait une ROM de *Super SF2 Turbo* fournie
   par le joueur, ce qui change la règle « l'ISO seule ».
2. **Place** : ROM graphique du fork (128 Mo), cœur, petites consoles.
3. **Placement dans Hyper** : quel décor pour quel mode.

## Pilote

Un décor (Ryu ou Guile, *Super SF2 Turbo*), une conversion de palette et une règle anti-tramage réglées à la main
contre un décor d'*Alpha 3*, puis une capture côte à côte. Critère : le décor doit garder ses éléments *SF2* tout en
paraissant cohérent à côté des persos d'*Alpha*.
