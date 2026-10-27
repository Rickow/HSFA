# Pierre de Rosette de construction (PSP SFA3 MAX ← Upper / Anthology ro5) — 2026-10-11

But : mesurer, perso par perso, ce que chaque élément PSP est devenu par rapport à sa source Upper, en tirer les
**règles de construction**, puis les inverser pour les persos MAX (vérifiables par aller-retour sur les persos
d'arcade). Outil : `rosette_construction.py` (méthode et sources en tête du fichier).

```bash
python rosette_construction.py            # persos 00-1F : frames + animations -> ~/.cache/sfa3max/rosette/plXX.json
python rosette_construction.py invites    # frames sans source cherchées chez TOUS les persos (+ persos MAX 26-29)
```

Méthode : une frame = ensemble de tuiles 16×16 **affichées** (position, empreinte des pixels après miroirs, valeurs
brutes CPS2), ramené à son coin haut-gauche ; appariement par index inversé + Jaccard ≥ 0,9 (exacte = 1,0).
Côté Upper : table des blocs par perso **T_61A100** (fichier 0x42A100 ; bloc = 3 ismes × {$2B0, $2B8, $2B4, $2BC},
même disposition que $DD412 de l'arcade), pas de 20 o, frames de type 2 (positions : fichier 390 = banc
`ext_b04000.bin`), tuiles = conteneur gfx du perso (`carte.txt`, `X_DATA.BIN`, `anthgfx.py` d'HSFA) ; réservoir
étendu à **toutes** les frames de type 2 du module (12 935), pas seulement celles des 4 tables.

## Règles mesurées (35 persos 00-25, hors variantes « alt » 12/13/14 ; 2026-10-11, après rapport HSFA EFFETS-UPPER)

Réservoir Upper : blocs par perso **T_749838** (PS2 0x749838 ; T_61A100 n'est PAS une table de blocs), frames de
types 00/02/0A/0C/0E/10/16 et 04/06/08/14 du module (pointeurs à toute adresse paire), chaque frame lue aussi avec la
banque COMMUNE e351 (objets attachés, $1A = 0 ; code = index local e351, sans +$1600), fichiers anim par perso.

| | Nombre | Part |
|---|---|---|
| Frames PSP | 19 942 | |
| identiques AU PIXEL PRÈS à une frame Upper | 14 635 | 73 % |
| proches (Jaccard 0,9-1) | 216 | 1 % |
| retouchées (Jaccard 0,5-0,9) | 413 | 2 % |
| **invités** (frames d'un AUTRE perso) | 964 | 5 % |
| sans source trouvée | ≈ 3 260 | 16 % |
| Animations PSP ($2B0/$2B4/$2B8/$2BC) | 7 639 | |
| même n°, mêmes frames, mêmes durées | 5 626 | 74 % |
| même n°, durées retouchées | 6 | ≈ 0 |
| renumérotées | 64 | 1 % |
| sans équivalent Upper / frames non appariées | 1 943 | 25 % |

Persos propres à Upper : Guile 395 / 511 exactes, Fei-Long 385 / 482, Dee Jay 304 / 389, T.Hawk 309 / 389.
Vega : 1 163 / 1 443 (griffe et masque = objets attachés, lus en banque commune).
Invités des fins MAX tous retrouvés : Eagle 671-676 = Guile (Upper $8F54AC…), 677-714 = Charlie ; Yun 786, 801-851 =
Fei-Long (Upper $8FFA64, $902370…).

1. **Frames = celles d'Upper, dans le même ordre.** Le n° de frame PSP suit l'ordre des adresses Upper à 88-99 % :
   le pac est une copie des frames Upper du perso, avec quelques frames ajoutées ou retouchées.
2. **Les invités d'une fin sont ajoutés À LA FIN du pac du perso qui la possède**, recopiés de la banque Upper de
   l'invité (pixels identiques). Ex. : Ryu 460-470 = Ken ; Charlie 360-383 = Rolento ; Bison 947-970 = Rolento ;
   Maki 633-726 = Guy ; **Eagle 677-714 = Charlie** (681-683 = Upper $7C42A0, $7C42D4, $7C4304 : l'animation
   « invitée » de la fin d'Eagle existe donc en images dans la banque de Charlie, palette comprise).
3. **Les animations ne sont pas re-minutées** : quand elles existent dans Upper, durées identiques (4 retouches sur
   4 755). Les écarts sont des animations ajoutées ou modifiées, et 56 renumérotations (surtout en $2BC).
4. **Variantes « alt » (12, 13, 14)** : dans Upper, leur bloc T_61A100 est celui de Ryu (remplissage) ; sur PSP,
   leurs frames sont faites avec les tuiles du perso de base (pl14 : 1 496 tuiles sur 1 552 identiques à celles de
   Sodom) mais ne correspondent à aucune frame Upper -> contenu PROPRE À LA PSP.
5. **Effets** (ex. Vega frames 0-752 : masque, griffes, éclats) : tuiles présentes dans la banque COMMUNE d'Upper
   (e351, index 15 396-16 482 = code + $1600) mais dans AUCUNE frame Upper lisible -> probablement dessinés par le
   code (tuiles posées directement) dans Upper, et mis en frames par la PSP. **Mécanisme PSP trouvé (Ghidra,
   2026-10-11)** : griffe et masque = OBJETS ATTACHÉS au corps (FUN_00183A38 / 0x183AB8 / 0x183E10…) ; l'octet +10/+11
   (mot C des boîtes) du pas courant du corps (pointeur +0x128 du joueur) donne un indice -> table 0x28FD8C (×4) ->
   indice de calque -> table 0x28EE30 (masque : frames 365…) / 0x28F0E2 (griffe : frames 0-303), $8000 = rien ;
   frame posée en +0x54 de l'objet attaché. Même principe que l'« objet attaché » de l'arcade (animation choisie par un
   octet du mot C du pas) -> dans Upper : objets attachés dessinés avec la banque commune (à confirmer par HSFA).

## Cas encore ouverts
- Gros blocs sans source : Vega (1C : frames 0-752), Rolento (0E : 522), « Sodom alt » (14 : 759, la banque gfx
  361 de `carte.txt` ne lui correspond sans doute pas), Bison (0A : 321) ; invités venant des persos propres à Upper
  (Guile, Fei-Long, Dee Jay, T.Hawk…), dont les blocs ne sont pas dans le module (T_61A100 [$20-$27] = $C00050,
  $900100… : données chargées ailleurs) -> à lire (ex. Guile de la fin d'Eagle, frames 667-676).
- Palettes, boîtes de collision, scripts de fin : pas encore dans l'outil.
- **Aller-retour** (convertir un perso d'arcade PSP -> format Upper/CPS2 avec les outils MAX et comparer à Upper) :
  la règle 1 montre déjà que les frames reviennent identiques ; reste à le mesurer sur les pas et les tables.

## Usage immédiat pour MAX
- Règle 2 = mécanisme de chargement (HSFA, 2026-10-11) : pendant une fin, seules sont en mémoire les banques de J1 / J2
  (emplacements 2/3), la commune (0) et le fichier de fin (4). Un invité ne peut donc PAS garder sa banque (sauf s'il
  est J2) : ses frames doivent venir de la banque du perso qui possède la fin. Solution retenue pour Charlie (fin
  d'Eagle) : banque d'Eagle + drapeau « palette propre » ; la Rosette sert à PROUVER que les frames sont les bonnes
  (pl26 681-683 = Upper $7C42A0 / $7C42D4 / $7C4304, au pixel près).
- Persos propres à Upper : T_61A100 [$20-$27] pointe en RAM PS2 ($900100 = RAM de jeu $FF0100, remplie à l'exécution)
  ou dans les fichiers chargés ($C00050). Pour les lire : vidage de la RAM sous le banc MAME d'Upper pendant un combat
  avec Guile / Fei-Long (work/mame_ro5, banc_mem.lua, ext_*.bin ; consignes : ROM copiées, nice -n 19, nvram/cfg
  temporaires, jamais -state).

## Chaîne images -> animations -> sites d'appel -> fonctions (`chaine_code.py`, 2026-10-11)
Un site PSP qui lance l'animation (table, n) et un site arcade qui lance (table, m), m vérifié par les IMAGES
(anims_map de plXX.json), sont dans des routines homologues. Lanceurs : arcade $2A708 / $2A710 / $2A758 / $2A75E ↔
PSP 0x5D63C / 0x5D674 / 0x5D6EC / 0x5D724 (+ relais d'appris.json, 0xCFA6C).
- 28 persos : **433 paires de routines** par les images ; **303 confirment** la Rosette du code (842 paires connues),
  **71 nouvelles**, **41 conflits** (à trancher par l'oracle : homologue arcade/Upper de chaque routine PSP).
- Couverture limitée par les sites à n° constant ; les n° lus dans des données (tables de coups) ne sont pas encore
  suivis.
- Méthodes et pièges du traducteur HSFA à appliquer : `hsfa/work/notes/METHODES-TRADUCTEUR-POUR-PSP.md`.
- **Arbitrage des 41 conflits** (`conflits.py`, méthode HSFA : oracle statique + TÉMOIN aléatoire) : chaque routine
  PSP candidate est traduite (traduire.py) et alignée sur la routine arcade (evaluer.py) ; le témoin = routines PSP du
  même perso tirées au hasard. Verdict : **images 20, Rosette du code 8, indécis 13** -> les deux méthodes se complètent.
- **Réinjection** (`reinjection.py`, option `imposees` de rosette.run, inactive par défaut) : paires sûres des images
  imposées au vote -> consensus des fonctions moteur **42 -> 43** (ajout $2AA08 ↔ 0x5E004, déjà connu par
  interpolation), aucun retrait ni changement : la carte de l'API moteur est **confirmée** ; pas de gain direct pour la
  traduction des persos MAX (qui repose sur l'API, pas sur les paires de routines).
