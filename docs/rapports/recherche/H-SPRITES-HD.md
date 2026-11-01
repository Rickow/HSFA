# Sprites ×2 (paquet HD dans le cœur) : plan et faisabilité

Plan du 2026-10-29, à l'état d'étude : rien n'est lancé.

> **Abandonné le 2026-10-29** : les essais de l'utilisateur avec des outils d'IA générative n'ont rien donné
> d'intéressant. Le plan reste comme trace ; la partie sans IA (MMPX + contrainte de palette, paquet HD dans le
> cœur) resterait faisable si l'idée revenait.

## 1. Choix d'architecture

Le 68000 ne change pas : positions, vitesses, boîtes, caméra et HUD restent en pixels CPS-2 (384×224). Seul le rendu
du cœur FBNeo change. Il dessine en 768×448 (896×448 en 16:9) et, pour chaque tuile, cherche une version 32×32 dans
un **paquet HD**, repérée par l'empreinte du contenu de la tuile d'origine. C'est le principe des « HD packs » de
l'émulateur NES Mesen.

- **Ce qu'on garde** : tous les bancs (oracle arcade, PPSSPP, matrice des coups, fins) restent valables, car le
  programme est identique. MAX, Hyper et la greffe ne sont pas touchés.
- **Où se fait le travail** : une nouvelle série de patchs du cœur, comme 0010-0014.
- **Écarté** : doubler la résolution dans le moteur. Il faudrait doubler les constantes de physique, les boîtes
  (rayons sur un octet), les décalages des tuiles dans les images, la caméra, le HUD, et le format de la table des
  objets, trop court pour 768 px. Ce serait une réécriture de trois jeux plus MAX.

## 2. Règle de fidélité : la réduction exacte

Chaque sprite ×2 doit respecter deux règles :
- **indices seulement** : chaque pixel prend un indice de la palette d'origine, choisi parmi ceux du voisinage 3×3 du
  pixel source (15 = transparent) ;
- **réduction exacte** : réduire le résultat de moitié redonne exactement le sprite d'origine.

Conséquences :
- aucune couleur nouvelle, aucun flou ;
- les couleurs alternatives, les flashs, la transparence par palette (patch 0010) et les ombres restent justes ;
- la fidélité se vérifie par programme, sprite par sprite.

## 3. Chaîne par lot

1. **Extraction**, depuis l'ISO du joueur. Les images d'animation sont assemblées en entier, pas tuile par tuile
   (`tools/max/cps2gfx.py`, `frames.py`, `sprites.py` comme base). On garde les indices et la palette utilisée, on
   supprime les doublons par empreinte, et on note la correspondance tuile ↔ images.
2. **Préparation** : chaque image passe dans une palette neutre propre au perso, avec des couleurs bien distinctes
   par indice, pour que le modèle voie la structure du dessin.
3. **Agrandissement ×2** par le modèle retenu (§4).
4. **Retour aux indices et contrainte** :
   - chaque pixel prend l'indice le plus proche parmi ceux autorisés par son voisinage ;
   - nettoyage des pixels isolés ; contours contre le transparent intacts ;
   - rejet de tout ce qui viole la réduction exacte.
5. **Cohérence entre images** : pour une tuile utilisée dans plusieurs images, on garde le résultat majoritaire et on
   liste les conflits. C'est le garde-fou contre le scintillement.
6. **Découpage en tuiles 32×32** repérées par l'empreinte de la tuile d'origine, puis paquet HD compressé.
7. **Contrôle qualité** :
   - automatique : réduction exacte, palette, nombre de conflits ;
   - visuel : planches par perso et animations côte à côte, ×1 et ×2 ;
   - retouche dans Aseprite (mode indexé, Lua), avec un fichier de corrections réappliqué à chaque passage.
8. **Cœur** : chargement du paquet et rendu en ×2. Les décors suivent plus tard ; polices et HUD au plus proche
   voisin.

## 4. Méthodes comparées au pilote

| Méthode | Principe | Pour | Contre |
|---|---|---|---|
| A. Scale2x / EPX + contrainte | règle fixe de copie des voisins | net, fidèle, immédiat ; étalon | n'invente aucun détail |
| B. Petit modèle entraîné sur nos sprites (recommandé) | classification : quel voisin source copier pour chaque pixel HD | style Capcom appris ; pas de bouillie par construction ; stable entre images ; rapide | ingénierie à faire |
| C. Diffusion + LoRA (SDXL / Flux, ControlNet Tile ou lineart, img2img ×2) | génère du détail, guidé par un LoRA (sprites + artbooks) | vrais détails nouveaux | invente, scintille, viole la palette : seulement avec l'étape 4, et seulement pour les grandes images fixes (portraits, fins) |

**Entraînement de B, sans données HD de Capcom** : on réduit nos propres sprites de moitié (réduction adaptée au pixel
art) et on apprend au modèle à retrouver l'original. On l'applique ensuite aux sprites d'origine. Le risque est l'écart
d'échelle, d'où la comparaison avec A.

**Outils** :
- B : PyTorch, avec traiNNer-redux ou neosr, ou un petit réseau codé directement ;
- essais de modèles ×2 existants : chaiNNer et OpenModelDB, toujours suivis de l'étape 4 ;
- C : ComfyUI pour la génération, kohya_ss (sd-scripts) pour le LoRA ;
- retouche : Aseprite.

Matériel : environ 8 Go de mémoire graphique (NVIDIA) pour B, 12 à 16 Go pour un LoRA SDXL.

## 5. Artbooks, droits, contraintes

- **Artbooks** : presque inutiles pour B (pas d'alignement pixel à pixel). Utiles pour le LoRA de C et surtout comme
  référence de retouche. Les scans restent chez l'utilisateur.
- **Droits** : le paquet HD et tout modèle entraîné sur l'art de Capcom sont fabriqués et gardés chez le joueur, depuis
  son ISO, jamais dans le dépôt ; un LoRA ne se distribue pas. Le modèle B pourrait s'entraîner à la volée chez le
  joueur. C'est à trancher.
- **Mémoire et vitesse** : en ×2, une tuile pèse 4 fois plus, et la ROM graphique de 128 Mo du banc passerait vers
  512 Mo. Il y a aussi 4 fois plus de pixels à dessiner. C'est bon sur PC et Android, douteux sur la RGB10X : prévoir
  la compression, le chargement des seuls persos du combat, ou le ×1 sur ces consoles.

## 6. Pilote proposé

- **Contenu** : Ryu d'*Alpha 3* (garde, marche, Hadoken, K.O.) et un portrait, en A, B et C, comparés en animation.
- **Mesures** : conflits entre images, pixels à retoucher, rendu en jeu sur PC puis Android.
- **Décision** : si B ne bat pas nettement A, A plus la retouche reste l'issue.
- **Volume à prévoir** : des dizaines de milliers de tuiles (Upper en ajoute 58 000 à celles d'*Alpha 3*). Même 5 %
  de retouche, c'est beaucoup.

## 7. Projets et méthodes existants (recherche du 2026-10-29)

- **MMPX** (McGuire et Gagiu, *JCGT* 2021) : agrandissement ×2 « fidèle au style ». Il reconstruit courbes, diagonales
  et angles en gardant la palette exacte, la transparence et les détails d'un pixel, avec des sources libres (C++,
  JavaScript, GLSL). C'est la meilleure **base A**, à la place d'EPX ;
  [article](https://casual-effects.com/research/McGuire2021PixelArt/McGuire2021PixelArt.pdf).
- **Paquets HD de Mesen** (NES), hérités de HDNes : remplacement de tuiles par leur contenu, conditions selon l'état du
  jeu, outil de construction intégré. C'est le **modèle du format de paquet HD** côté cœur ; le format est décrit dans
  la documentation de Mesen (`mesen.ca/docs/hdpacks.html`). Un guide signale qu'en ×2 les décors doivent l'être aussi,
  sinon ils sautent. Voir aussi
  [texture packs](https://emulation.gametechwiki.com/index.php/Texture_Packs).
- **Article MDPI, *Applied Sciences* vol. 16 n° 5** : agrandissement de pixel art qui garde la palette et la grille,
  contre Real-ESRGAN et ITSRN qui lissent ou inventent des couleurs. C'est la piste la plus proche de la **méthode B**,
  à lire avant de coder ([lien](https://www.mdpi.com/2076-3417/16/5/2314)).
- **CopperScale** : agrandisseur déterministe qui analyse palette, tramage et contours. Une autre base à comparer
  ([lien](https://zff.dev/sbechet/copperscale)).
- **OpenModelDB** : modèles ×2 pour pixel art, en RGB et sous licence non commerciale, par exemple
  [2x-Faithful](https://openmodeldb.info/models/2x-Faithful). Ils se testent dans chaiNNer, toujours suivis de la
  contrainte de palette.
- **Méthode communautaire** (Doomworld) : ESRGAN sur les planches de sprites, puis retour à la palette. C'est notre
  étape 4, mais sans la règle de réduction exacte.
- **Diffusion** : Retro Diffusion (extension locale d'Aseprite, payante) génère du pixel art mais n'agrandit pas.
  Les remasters IA de *Mortal Kombat* sur MUGEN montrent surtout les défauts à éviter : bords et animations qui
  scintillent, détails inventés.
- **Aucun projet trouvé** pour Street Fighter ou KOF qui applique cette méthode à des sprites CPS-2.
