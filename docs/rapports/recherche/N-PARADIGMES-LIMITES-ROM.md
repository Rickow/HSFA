# Faire tenir plus que la machine : comment d'autres l'ont fait (2026-11-10)

Question de l'utilisateur, après `M-REUTILISATION-TUILES.md` : quelles solutions ont été trouvées, sur d'autres projets ou
d'autres machines, au problème « le jeu dépasse la mémoire graphique adressable » ?

## Les grandes familles

1. **Commuter des banques (« mappers »)**. La machine ne voit qu'une fenêtre ; un circuit sur la cartouche change ce qu'il y
   a derrière. NES (MMC1, MMC3 : banques de motifs de 1 ou 2 Ko commutées en cours d'image), Mega Drive (*Super Street
   Fighter II*, 40 Mbit, seul jeu sous licence à commuter des banques : mapper Sega 315-5709/5779, huit fenêtres de 512 Ko,
   repris par les cartouches amateurs et les Everdrive sous l'en-tête « SEGA SSF »), Neo Geo (cartouches « Giga Power » :
   banques sur la carte, jusqu'à environ 716 Mbit au lieu d'environ 330). Les cartes CPS-2 « all-in-one » commutent aussi une
   page de ROM, mais entre deux jeux, pas pendant la partie.
2. **Décompresser vers une mémoire vidéo**. Possible seulement quand la machine affiche depuis de la RAM : *Alpha 2* sur
   Super Nintendo (puce S-DD1), Mega Drive (formats UFTC, LZ4W, ZX0), Neo Geo CD (sprites chargés du CD, temps de
   chargement), CPS-3 (jeux sur CD copiés en mémoire flash). La CPS-2 lit ses tuiles directement en ROM : non applicable
   sans matériel nouveau.
3. **Couper ou ré-auteurer**. Les portages de la série (PlayStation, Saturn, GBA) retirent des images ; Capcom fait tenir
   *Hyper Street Fighter II* (2004) sur CPS-2 en réutilisant des données existantes ; le projet de Zer0-NexuS rééchantillonne
   156 sons à 15/16 pour tenir dans les 4 Mo de son d'origine (avec perte).
4. **Changer de machine**. *Upper* lui-même passe sur NAOMI ; le patcheur `sfa3u-naomi-2026` y ajoute les personnages de MAX ;
   strygo déclare 8 Mo de QSound, au-delà de la carte d'origine ; HSFA et cps2recomp élargissent une CPS-2 émulée ou
   recompilée.
5. **Refaire le matériel**. Tendance récente : répliques FPGA (Multisystem 2 au format JAMMA ; remplacement d'un processeur
   graphique d'arcade Nintendo publié en mars 2026). Aucune carte B CPS-2 en FPGA trouvée.

## Ce que ça dit pour Upper et Hyper

- **La bonne idée est la famille 1, et Capcom l'a déjà eue.** Un combat n'a besoin que de deux personnages, d'un décor et des
  éléments communs. Le portage PS2 de l'*Anthology* range chaque personnage dans une banque qu'il charge dans un
  emplacement (HANDOFF §48), et notre fork reprend ce schéma : registre « emplacement → base de banque », code global =
  base + code local. C'est exactement un mapper.
- **Sur une vraie CPS-2**, il faudrait une carte B modifiée avec un petit circuit logique : un registre écrit par le 68000
  (au changement de combat ou de décor) qui choisit quelle partie d'une grande mémoire flash apparaît dans la fenêtre de
  32 Mo. Côté programme, c'est simple (nous écrivons déjà ce registre dans le fork). Côté matériel, c'est un projet de carte.
- **À mesurer** (outil `tuiles_cps2.py`, à étendre) : la taille du « jeu de travail » d'un combat (tuiles communes +
  deux personnages + un décor) dans Upper et Hyper. Si le pire combat tient dans 32 Mo avec de la marge, le schéma de banques
  est prouvé suffisant sans aucune perte.

Sources : [nesdev, mapper 208](https://nesdev.org/wiki/INES_Mapper_208) ; [Sega Retro, notes techniques de SSF2 Genesis](https://segaretro.org/SSFII_Genesis_Technical_Information_(2000-07-26)) ;
[TCRF, SSF2 Genesis](https://tcrf.net/Super_Street_Fighter_II_(Genesis)) ; [MAME, PR 14117](https://github.com/mamedev/mame/pull/14117) ;
[neogeodev, bankswitching](https://wiki.neogeodev.org/index.php/Bankswitching) et [cartouches MVS](https://wiki.neogeodev.org/index.php/MVS_cartridge) ;
[MvC à 148 Mo, 2026](https://morphus56k.com/blog/cps2-maximum-rom-expansion) ; [cartes all-in-one CPS-2](https://www.arcade-projects.com/threads/cps2-black-all-in-one-conversion-multi.4566/) ;
[Plutiedev, UFTC](https://plutiedev.com/format-uftc) ; [LZ4W](https://gendev.spritesmind.net/forum/viewtopic.php?t=2479) ;
[Adafruit, PPU d'arcade Nintendo en FPGA, 2026](https://blog.adafruit.com/2026/03/17/making-an-inexpensive-replacement-for-a-nintendo-arcade-picture-processing-unit/) ;
[Hackster, Multisystem 2](https://www.hackster.io/news/get-perfect-emulation-from-this-fpga-based-arcade-d9062827c078).
