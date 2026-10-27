# Persos MAX (Eagle, Maki, Yun, Ingrid) : ce que l'injection dans le moteur traduit devra accueillir

Note de la session MAX, 2026-10-03. Rien n'est poussé dans le dépôt. Pas d'urgence : à lire quand le moment s'y prête.
Détail et outils : `sfa3max-psp-widescreen/work/re/convert/README.md` (convertisseur) et `…/frames289/README.md` (formats).

## 1. Ce qui est prêt côté MAX (sorties dans `~/.cache/sfa3max/converti/plXX/`)
| fichier | contenu | format cible |
|---|---|---|
| `bank.bin` | tuiles 16×16, 4 bpp linéaire, quartet bas à gauche, **valeurs brutes CPS2** | comme les conteneurs/banques Anthology (§45) |
| `frames.json` | frames de **type 2** : `T`, objets `(dx, dy, code local, attributs CPS2)` | ta note `frames-anthology-emetteur.md` |
| `scripts.json` + `scripts_eboot.json` | pas `(contrôle = durée \| 0x8000 si dernier, n° de frame, mot A, mot B)` | pas Anthology 5 × u32 |
| `sections/sNN.bin` | sections de l'entrée PSP `[6]` ; chez Ryu, 9-11 et 17-19 = tables du module à 100 % (géométrie des boîtes) | recopie telle quelle |

Validation : aller-retour sur Ryu (PSP → convertisseur → comparé à ro3/e258) = **87 % des frames identiques**
(pixels, positions, miroirs), **81 % des pas de script identiques** (mots de collision : 92 %).
Rendus depuis la sortie convertie : Eagle et Ingrid (fusion haut + bas) corrects.

## 2. Ce que le moteur devra fournir pour un nouvel ID (`$26` Eagle, `$27` Maki, `$28` Yun, `$29` Ingrid ; base Upper)
1. **Banque de sprites** : un emplacement dans la table « perso → banque » (§51) et une banque par perso dans le
   schéma de banques du fork (§48 / §82, emplacement en bits 13-15 de Y). Numérotation locale déjà faite : la case PSP `j`
   = bloc 2×2 aux codes `b, b+1, b+16, b+17` avec `b = 32·(j // 8) + 2·(j % 8)`.
2. **Positions des frames** : un bloc façon fichier 289 (n × (s16 dx, s16 dy)) chargé à une adresse connue ; les frames
   pointent dedans (pointeur 32 bits réaligné sur 4).
3. **Frames et scripts en mémoire** : les frames de type 2 rangées au mot près, les pas de script en 5 × u32 avec le
   **pointeur d'exécution** de leur frame ; puis un pointeur de reprise après le dernier pas (boucle).
4. **Tables par perso à étendre** (32 entrées dans SFA3, davantage dans Upper) : au minimum les 9 tables de collision
   (fichier ro3 `0x48D678`, `0x48D6F8`, `0x48D778`, `0x48D878`, `0x48FCF8`, `0x48FD78`, `0x48FDF8`, `0x48FE78`, `0x48FEF8`,
   chargées par adresse constante ⟹ à déplacer/agrandir et corriger dans la traduction) ; et les tables d'animation par
   coup, que je n'ai PAS encore localisées côté moteur.
5. **Palettes** : 30 palettes de 16 couleurs par perso (Ingrid : 48 ; sa fusion utilise les sous-palettes +0 et +1).
6. **Code des coups** : ~95 Ko de MIPS (Eagle 26 / Maki 21 / Yun 27 / Ingrid ~19 Ko) à porter en 68K — l'API moteur sera
   apprise sur Guile (C du PSP ↔ 68K d'Upper traduit). C'est le gros morceau ; il viendra après les données.

## 3. Ce qui reste ouvert côté MAX
- **Yun** : ses scripts sont dans l'EBOOT (table `0x2A9EC4`, 272 scripts) ; sa table des jeux de boîtes n'est pas
  trouvée (index jusqu'à 1 202 ; sa section 7 ressemble à de la géométrie brute).
- Tables de scripts de l'EBOOT d'Eagle/Maki/Ingrid : presque tous d'un seul pas, à vérifier.
- Sens des mots A/B (question de `reponse-max-frames-et-collisions.md`) : utile pour rattacher chaque section PSP à
  sa table moteur, pas indispensable pour une première injection (les mots se recopient tels quels).

## 4. Proposition de premier test, sans toucher au fork
Dans le banc MAME : remplacer, dans la ROM graphique chargée par MAME, les tuiles d'une banque existante (ex. Ryu)
par celles d'Eagle, et quelques frames/scripts de Ryu par leurs équivalents convertis ⟹ voir Eagle à l'écran avec les
coups de Ryu. Ça validerait banque, frames et positions en conditions réelles avant tout travail sur les tables.
