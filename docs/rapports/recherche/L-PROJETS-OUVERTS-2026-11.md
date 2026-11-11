# Projets ouverts autour de la CPS-2 et des *Alpha* : état au 2026-11-10

Mise à jour de `F-PROTOS-PROJETS.md` et `K-CPS2RECOMP-PISTES.md`. Ne reprend pas ce qui y est déjà (cps2recomp, projet
Dreamcast d'irnutsmurt, SFZ2A-DASH-CPS2 et `sfa3u-naomi-2026` de Zer0-NexuS, *backports* de strygo, `sfa3ce` d'originalgrego,
outils de 0xZERO3, scripts de Jesuszilla, crowded-street/3s-decomp). Recherche web et lecture des dépôts publics (clones
en lecture seule, hors dépôt).

**Rappel de licence** : presque tout ici est en GPL-3. Chez nous (MIT), on prend des faits cités et des idées réécrites,
jamais du code ; faire tourner un outil en local sur nos propres fichiers est permis, ses sorties restent hors dépôt.

## 1. À regarder en premier

| Projet | Ce que c'est | Pour HSFA |
|---|---|---|
| [theweathervane/sfa3max-decomp](https://github.com/theweathervane/sfa3max-decomp) (GPL-3 ; v0.52.2 le 6 nov. 2026, très actif, fait avec Claude) | Décompilation de *Alpha 3 MAX* PSP (US ULUS-10062) en C lisible, vérifiée fonction par fonction contre l'original ; extraction des ressources en PNG / WAV / OGG. Suit une recompilation statique du même auteur. **Utilise notre patch 16:9 PSP**, crédité (MIT). | **Session MAX** : sa carte du programme PSP (`docs/PSP_PROGRAM_MAP.md`, 451 lignes), le format des archives `.pac` (`docs/PAC_FORMAT.md`, en cours), les décors (`docs/STAGES.md`) et les écarts de versions. Les combattants ne sont pas encore décompilés (tâches, menus, chargeur, décors seulement), mais le projet avance vite. Attention : version US, notre banc MAX est sur l'européenne. |
| [ValleyBell/qsound-hle](https://github.com/ValleyBell/qsound-hle) | Émulation haut niveau de la puce QSound, avec un désassemblage du programme du DSP (`qsound_dl-1425.asm`) et son portage commenté en C. | Notre second QSound (rejeu) et la précision du son dans le cœur : référence pour comprendre ce que fait vraiment la puce. |
| [ran-j/PS2Recomp](https://github.com/ran-j/PS2Recomp) (GPL ; actif, oct. 2026) | Recompilateur statique PS2 : décodeur R5900 vers C++, environnement d'exécution, export de fonctions depuis Ghidra. | Le côté PS2 de notre chemin. Utile comme référence de décodage R5900 et, à terme, comme autre voie : un *Anthology* natif sur PC sans repasser par le 68000 (perdrait l'intérêt CPS-2, mais pourrait servir à comparer). Pas de priorité. |

## 2. Ports natifs nés de cps2recomp (même famille que nos jeux)

- [omegakatana92/Street-Fighter-Alpha-3-Recomp](https://github.com/omegakatana92/Street-Fighter-Alpha-3-Recomp) (`sfa3`,
  Europe 980904) et [omegakatana92/Street-Fighter-Alpha-Recomp-](https://github.com/omegakatana92/Street-Fighter-Alpha-Recomp-)
  (`sfa`) : ports natifs faits avec l'outil de tmcleroy. Pas de connaissance neuve a priori ; signe que l'écosystème
  grandit.
- [some-gamer-dude/sfa2gp](https://github.com/some-gamer-dude/sfa2gp) : *Alpha 2 Gold+*, mod d'*Alpha 2* bâti sur cps2recomp
  (`sfa2` et `sfa2u`), mécaniques et modes optionnels, guide en ligne. Intéressant pour le livre (chapitre 11, la scène
  des bidouilleurs continue) ; pas pour le code.

## 3. Autres jeux de la série, autres machines

- [TechnicallyComputers/Street-Fighter-Alpha-3-Recomp](https://github.com/TechnicallyComputers/Street-Fighter-Alpha-3-Recomp) :
  recompilation statique d'*Alpha 3* **PlayStation** (PSXrecomp). Peut éclairer le contenu propre à la version PS1
  (World Tour, personnages ajoutés) cité au chapitre 6.
- Projet Dreamcast d'irnutsmurt ([Street-Alpha-3-Dreamcast-Recomp](https://github.com/irnutsmurt/Street-Alpha-3-Dreamcast-Recomp)) :
  v0.2.4 traduit en anglais les listes de coups d'Eagle, Maki, Yun et Ingrid. Déjà suivi.
- Une recompilation de *Zero 3 Upper* **NAOMI** est annoncée sur X (NEON.Bitchi!), sans dépôt public trouvé. À surveiller.
- *Capcom Fighting Collection 2* : son exécutable est protégé (Enigma Protector, selon un fil d'arcade-projects) ; aucun
  outil public d'extraction des données d'Upper trouvé.
- [gufranco/snes-street-fighter-alpha-2-nochip](https://github.com/gufranco/snes-street-fighter-alpha-2-nochip) :
  reconstruit *Alpha 2* Super Nintendo sans la puce S-DD1. Pour le livre (chapitre 6, la cartouche de 32 Mbit).

## 4. Outils CPS-2 et CPS-1 utiles à nos chantiers

- [goosechooser/cps2-gfx-editor](https://github.com/goosechooser/cps2-gfx-editor) : extraction des tuiles 8×8 et 16×16 des
  ROM graphiques CPS-2 vers des images, et réinjection. Pour la piste des décors de *SF2* recolorés « façon *Alpha* »
  (`I-DECORS-SF2.md`) et le décor d'*Alpha 2* importé.
- Conversions CPS-1 vers CPS-2, avec traduction des identifiants QSound :
  [fox4u/cps1q-to-cps2](https://github.com/fox4u/cps1q-to-cps2) (correctifs 68000),
  [kuzearcade/CPS15_to_CPS2](https://github.com/kuzearcade/CPS15_to_CPS2) (les dix-huit jeux CPS-1 QSound sur CPS-2), et le
  portage *Hyper Fighting* de Mike Moffitt. Pour les mêmes pistes (décors et musiques de *SF2* dans Hyper) et pour
  comprendre le CPS Changer.
- [jotego/jtcps](https://github.com/jotego/jtcps) : cœur FPGA CPS-1, CPS-1.5 et CPS-2 (MiSTer, Analogue Pocket), en
  Verilog. Description du matériel au cycle près (minutage, QSound). HSFA sur FPGA est exclu (nos jeux dépassent une
  CPS-2), mais c'est une référence matérielle.
- Training et boîtes de collision : [0xZERO3/fbneo-training-mode_for_sfa3](https://github.com/0xZERO3/fbneo-training-mode_for_sfa3)
  (dérivé du mode entraînement FBNeo multi-jeux) et le script `cps2-hitboxes.lua` de mame-rr (ancien). Pour proposer un
  mode entraînement dans notre cœur.

## 5. Ce que je propose (rien n'est lancé)

1. **Signaler sfa3max-decomp à la session MAX** : carte PSP, format `.pac`, et un contact possible (son auteur crédite
   déjà notre patch ; échange de notes comme avec tmcleroy et irnutsmurt).
2. **qsound-hle** comme référence pour vérifier notre rejeu (session du cœur).
3. Garder pour le livre : *Alpha 2 Gold+*, la cartouche SNES sans S-DD1, la recompilation PS1, la NAOMI annoncée
   (chapitres 6, 11 et 12, « les voisins »).
4. Outils de tuiles et conversions CPS-1 → CPS-2 : seulement si la piste des décors de *SF2* est relancée.
