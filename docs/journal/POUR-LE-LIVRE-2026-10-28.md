# Pour le livre (session cloud) : ce qui manque au chapitre 12, au 2026-10-28

Le chapitre 12 de « Street Fighter Alpha — Histoire d'une renaissance » (version du 19 octobre) s'arrête au tableau
des coups du 18 octobre. Voici ce qui s'est passé depuis, ce qui est devenu faux et ce qui ferait de bons passages.
Sources : journal `docs/journal/HANDOFF.md` (§ cités), rapports `docs/rapports/`, `max/notes/`. À reprendre au rythme
voulu ; rien d'urgent.

## 1. Passages devenus faux

- **Encadré « Ce que le dépôt ne contient pas »** : « Le dépôt est privé » n'est plus vrai. Le 27 octobre, la v0.1 est
  publiée sur un dépôt **neuf**, à historique propre (github.com/Rickow/HSFA), sous licence MIT ; le dépôt de travail
  reste privé (§177). Les cœurs ont leur licence FinalBurn Neo jointe (ni vente, ni dons).
- **« Soixante-quatre octets »** : le patch PCSX2 du mode Arcade d'Hyper n'avait **pas de fins**, et le porteur du projet
  le juge « pas complet et un peu bancal ». Il n'est pas publié ; le vrai mode Arcade avec fins est celui de la greffe
  CPS2 (voie B). « Une suite d'adversaires, le continue, une fin » est donc à corriger.
- **« Les quatre personnages de MAX… attendent leur place »** : ils sont jouables dans Upper depuis le 18 octobre et
  livrés en zips d'essai successifs, du lot 2b4 au lot 2b24 (§164, §166, §174-§177).
- **« Une seule commande reconstruit les trois jeux depuis l'ISO »** : vrai, mais le 27 octobre la preuve a été refaite
  depuis un clone neuf du dépôt public : SFA3 et Upper identiques à la v151, Hyper identique sauf ses voix par version
  (§177, BUILD).

## 2. Ce qui manque, par thème

1. **MAX dans Upper, de la PSP au 68000** (§164, §166, §174-§177 ; `max/notes/SAVOIR-MAX.md`). Les quatre persos ne sont
   pas du code d'arcade : sur PSP, c'est un portage en C. La session MAX a construit une « Rosette du code » (fonctions
   PSP appariées aux routines arcade par vote) et un traducteur MIPS PSP → 68000. Anecdotes :
   - Ingrid était « écrasée » à l'écran : étirement ×38/32, mal mesuré deux fois (décor compris dans la mesure) avant
     d'être prouvé au pixel ;
   - des adresses d'Upper figées dans une version antérieure (v149) : un contre raté n'appliquait plus le coup reçu ;
   - l'onde de choc de Yun ne doit pas blesser (elle annule les projectiles) : les boîtes des tirs étaient échangées.
2. **La PSP comme témoin** (§174-§175). PPSSPP sans écran, avec débogueur, pilote un combat image par image ; un banc
   compare chaque coup sur PSP et dans Upper (« 4 tours pour 3 images », états PSP = moitié des octets d'Upper). Le
   même principe que l'arcade témoin du chapitre, transposé à la PSP.
3. **Le voisin du Dreamcast** (F-PROTOS-PROJETS, §175) : irnutsmurt recompile les mêmes quatre persos de la PSP vers le
   SFA3 Dreamcast. Une trentaine d'adresses concordent au chiffre près sur deux régions différentes ; le 27 octobre,
   HSFA lui ouvre un échange public (ticket n° 1 de son dépôt) avec deux corrections et la version européenne.
   Zer0-NexuS publie le 26 octobre un patcheur qui ajoute les quatre persos à l'Upper NAOMI.
4. **Les noms de Capcom** (`docs/rapports/recherche/G-METHODE-CAPCOM-MAX.md`). Les exécutables PS2 de *Capcom vs. SNK 2* et
   de *Capcom Fighting Evolution* gardent les noms de fonctions de Capcom (et un DWARF complet pour CFE). Eagle = pl23,
   Maki = pl24, Yun = pl2c (CvS2), Ingrid = pl22 (CFE) ; un gestionnaire par rôle, des spéciaux découpés en phases ;
   409 fonctions PSP renommées. Et une découverte : l'IA de la PSP est **l'interpréteur de l'arcade, version Upper**
   (max/notes/ia-psp-arcade.md) — les scripts des quatre persos se convertissent tels quels.
5. **Les bugs officiels comme banc de test** (§169, D-SONDES) : la mise à jour CFC2 d'août 2025 a dû corriger des coups
   de Bison et de R. Mika qui ne touchaient pas les quatre nouveaux. HSFA a rejoué ces cas : le Skull Diver ratait
   Ingrid (corrigé) mais aussi Sakura, et ce second raté existe déjà dans Upper sans MAX — un défaut hérité, pas une
   faute de la greffe.
6. **v151 et la matrice des coups** (§170-§173) : Hyper comparé coup par coup à l'arcade ; le Killer Bee Assault de Cammy
   (aide `roxr`, `EXG`, `BCLR` perdus) ; exceptions des supers d'Hyper de 316 à 0.
7. **Le cœur grandit** (patchs 0010-0014) : registres de transparence par palette pour les effets des persos MAX, ombres
   transparentes, 16:9 « remplir la hauteur », pilote `sfa3umhsfa` « Upper MAX (HSFA) », provocation sur Select (la PS2
   écrit Start dans deux registres à la même image : le front montant n'existe jamais).
8. **La greffe Arcade** (§165, §175) : entrée ARCADE dans le menu d'Hyper, 64 fins sur 85 combinaisons, régression au
   passage v151, reprise le 28 octobre.
9. **Les ROM japonaises** : l'oracle 980727 (révision de l'Anthology) construit à côté de sfa3ud ; index des pages du
   mook « ALL ABOUT ZERO3 » (référence privée).
10. **L'organisation** : une session MAX, une session cloud, des agents à mission unique ; un fichier d'échange (questions,
    réponses, notes), un index de rétro-ingénierie vérifié par script (`re/`), un banc de non-régression obligatoire
    avant toute livraison. La règle « aucune donnée de jeu » a tranché un cas limite le 27 octobre : la table du rejeu
    d'Hyper (écritures QSound relevées sous MAME, « un VGM sans échantillons ») n'est pas publiée ; la v0.2 la recréera
    depuis l'ISO du joueur.

## 3. Chronologie à ajouter

| date (2026) | étape |
|---|---|
| 18 oct. | premiers zips « Upper MAX » (Eagle, Maki, Yun, Ingrid) |
| 21 oct. | point d'étape transverse ; recherche du livre versée au projet |
| 24 oct. | ROM japonaises (oracle 980727) ; patchs 0010-0013 du cœur (transparence, 16:9 hauteur, pilote Upper MAX) |
| 25 oct. | traducteur v151 ; oracle PPSSPP ; banc PSP coup par coup ; lot 2b23 (persos MAX en CPU) |
| 26-27 oct. | noms Capcom (CvS2 / CFE) ; échange avec le projet Dreamcast ; IA de la PSP = interpréteur d'arcade |
| 27 oct. | **release publique v0.1** (github.com/Rickow/HSFA) |
| 28 oct. | lot 2b24 (Yun, Ingrid, IA et dialogues des MAX) ; reprise de la greffe Arcade |
