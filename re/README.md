# `re/` — index des connaissances (rétro-ingénierie)

Index **léger** de ce que le projet sait des adresses, tables, champs et routines de SFA3 (arcade), des modules
PS2 `ro3` / `ro5` / `ro9`, du jeu final `ro9a` et de SFA3 MAX (PSP). But : **ne pas redécouvrir** ce qui est déjà
établi (le champ `$1A` des banques, les places `$27`-`$29` d'Upper réutilisées, `T_6139A4` faite de paires de
coordonnées et non de pointeurs…) et **ne pas répéter les erreurs**. Ce n'est pas encore le kit de décompilation
(voir la fin).

Aucune donnée de jeu ici : seulement des adresses, des noms, des tailles, des types et des descriptions.

## Fichiers

| fichier | contenu |
|---|---|
| `connaissances/sfa3_arcade.tsv` | SFA3 arcade : ROM 68K `sfa3ud` déchiffrée et RAM arcade (`$…`) |
| `connaissances/ro3.tsv`, `ro5.tsv`, `ro9.tsv` | SFA3, Upper, Hyper : adresses d'**exécution** PS2 (MIPS) |
| `connaissances/ro9a.tsv` | jeu final : Hyper + mode Arcade d'Upper (greffe, voie B) + persos MAX |
| `connaissances/max_psp.tsv` | SFA3 MAX PSP (EU `ULES-00235`) |
| `connaissances/sfa1_arcade.tsv`, `sfa2_arcade.tsv`, `ssf2_arcade.tsv`, `cps1_arcade.tsv` | autres jeux arcade mesurés (sfa/sfz ; sfa2/sfz2al ; ssf2/ssf2t ; sf2hf/ffight) : adresses 68K |
| `connaissances/z80_son.tsv` | pilotes son Z80 (v1.04 / v1.05 / v1.71…) : adresses dans la ROM son de chaque jeu (pilote et jeu rappelés en tête du rôle) |
| `connaissances/champs.tsv` | champs de structures : joueur (`$FF8400 + $400·k`), objets, tâches, A5, structures PSP… |
| `allocations.tsv` | registre des zones occupées (images 68K, blocs externes, RAM, ids de perso, ROM graphique…) |
| `outils/quoi.py` | recherche par adresse (tout espace, homologues et plages compris), nom ou mot-clé |
| `outils/verifie.py` | contrôle : colonnes, formes d'adresse, doublons, sources, anonymat, chevauchements |
| `outils/zones.py` | liste des zones par cible, recherche d'une plage, contrôle des chevauchements |

Colonnes des fichiers d'adresses : `adresse`, `adresse_autres` (homologues `espace:adr; …`), `genre` (fonction |
table | variable | champ | structure | format | constante), `nom`, `role`, `taille_type`, `mises_en_garde`,
`source`, `confiance`, puis deux colonnes **facultatives** en fin de ligne : `score` (rapprochement, par ex.
« 0,82 (12 votes) » pour la Rosette) et `outil` (script qui produit ou utilise l'entrée). `champs.tsv` : `structure`, `decalage_ps2`, `decalage_arcade`, `decalage_autres`, `espaces`,
puis les mêmes colonnes. `allocations.tsv` : `cible`, `debut`, `fin` (inclusive), `occupant`, `etat` (utilisé |
réservé | libre prouvé), `source`, `remarque`.

```
python3 re/outils/quoi.py 0x6139A4        # adresse d'exécution PS2
python3 re/outils/quoi.py T_749838        # nom (et l'adresse qu'il contient)
python3 re/outils/quoi.py Juli            # mot-clé
python3 re/outils/quoi.py '$FF8503'       # RAM CPS2 : trouve aussi joueur 1 +$103 (= $102 en octet XOR 1) et A5
python3 re/outils/quoi.py +$1A -s joueur  # champ
python3 re/outils/quoi.py 0x20E500 --va   # va = décalage dans le fichier du module (+ 0x1F0000)
python3 re/outils/zones.py image68k_ro5 0x3A0000 0x3BFFFF   # qui occupe cette plage ?
python3 re/outils/verifie.py
```

## Conventions d'adresses

| espace (`adresse_autres`) | forme | sens |
|---|---|---|
| `arcade` | `$0DD412` (6 chiffres) | ROM 68K `sfa3ud` déchiffrée, ou RAM arcade `$FFxxxx` |
| `ro3`, `ro5`, `ro9` | `0x749838` | adresse d'**exécution** PS2 = décalage dans le fichier du module **+ `0x1F0000`**. Beaucoup de rapports écrivent « va » pour le décalage fichier : `quoi.py` essaie les deux |
| `ro9a` | voir l'en-tête de `ro9a.tsv` | module augmenté et image de la construction figée citée |
| `psp` | `0x00183A38` (8 chiffres) | SFA3 MAX PSP : **VA à base 0** de l'EBOOT EU déchiffré (outils MAX, Ghidra base 0 `FUN_…`) = **décalage dans le fichier − `0x74`** (les outils prennent `EBOOT[0x74:]`) ; segment 0 (code puis données en lecture seule) : va `0`-`0x2D4F2F` ; segment 1 (`.data` puis `.bss`) : dès va `0x2D4F30`. Mémoire réelle sous PPSSPP = `0x08804000 +` va. Ce n'est **pas** un décalage de fichier, et `+ 0x1F0000` ne s'y applique jamais. Les décalages dans les entrées d'un `.pac` ne sont pas des VA : lignes sans adresse (`format`) |
| `sfa1_arcade`, `sfa2_arcade`, `ssf2_arcade`, `cps1_arcade` | `$0012AB` | ROM programme / RAM 68K du jeu arcade nommé |
| `z80_son` | `$F000` (4 chiffres) | adresse Z80 dans la ROM son ; le pilote et le jeu sont précisés dans le rôle |
| `img_ro3`, `img_ro5`, `img_ro9`, `img_ro9a` | `$1DFB78` | adresse dans **l'image 68K traduite** : propre à **une construction**, elle bouge à chaque reconstruction (relire `carte_image.txt`) |
| `cps2` | `$FF40BC` | adresse fixe de la carte CPS2 du programme traduit (RAM, blocs externes, registres) : ne bouge pas |

- Programme arcade : `sfa3_prog.bin` est la vue **opcodes** (code lisible, données brouillées) ; les **données**
  se lisent dans la ROM `sfa3ud` (fichiers concaténés, octets échangés par paire). Une table lue dans
  `sfa3_prog.bin` est fausse (`max/outils/convert/README.md`).
- Noms d'espaces **exacts** dans `adresse_autres` : `arcade` (SFA3), `ro3`, `ro5`, `ro9`, `ro9a`, `psp`, `img_ro3`,
  `img_ro5`, `img_ro9`, `img_ro9a`, `cps2`, `sfa1_arcade`, `sfa2_arcade`, `ssf2_arcade`, `cps1_arcade`, `z80_son`.
  Synonymes tolérés (à éviter) : `upper` = `ro5`, `hyper` = `ro9`, `sfa3` = `arcade`, `max` = `psp`.
- **Recette « mode CPS2 »** : octet = adresse **XOR 1**, mot = même adresse, long = moitiés échangées. Ainsi
  `MOVE.B $5(A6)` (image) = `MOVE.B $4(A6)` (arcade) = `lb 4(A6)` (MIPS). `quoi.py` essaie l'adresse XOR 1 pour la RAM.
- RAM du jeu côté PS2 : `0x900000-0x90FFFF` (ro3) et `0xA00000-…` (Upper) = `$FF0000-$FFFFFF`. `A5 = $FF8000`.
- Champs A5 : déplacement 16 bits **non signé** (`$C0BC(A5)` = `$FF40BC` ; `-$7178(A5)` s'écrit `+$8E88`).
  `quoi.py` passe de `$FFxxxx` au déplacement A5 et au champ joueur (`$FF8400 + $400·k + décalage`).
- `decalage_ps2` = déplacement employé par le MIPS (et par l'image, octets XOR 1 à part) ; `decalage_arcade` =
  numérotation 68K d'origine. Le portage a relogé une partie des variables A5 de la moitié basse (voir
  `docs/reference/SYMBOLES.md` §4).
- Constructions de référence des adresses `img_*` :

| espace | construction | md5 |
|---|---|---|
| `img_ro3`, `img_ro5`, `img_ro9` quand la `source` cite `references/v149` (ajoutées automatiquement aux fonctions) | **références v149** (`<workspace>/work/references/v149/roN`, traducteur à l'étiquette git `v149`) : 1re instruction produite pour le va de la fonction (écart < `0x40`) dans `carte_image.txt` | `sz3ud.03c` ro3 `7e22b1ec7d7a20ff05f401ddaa36c2da`, ro5 `7898814ceb4335d6cba06f58d3496ddf`, ro9 `cb9b37b90c2adc848abd6dad72c536e5` (rappelés dans `source`) |
| `img_ro9a` | `ro9a3_fige` (greffe, étape 3) | `sz3ud.03c` `217fc51c03d1c0a581d95a1c00029700`, module `ro9a_module.bin` `4440a95de9ee61a19622c4f4dec4d2bc` |
| `img_*` des autres lignes | celle du rapport cité en `source` | souvent antérieure à v149 et non notée : revérifier dans `carte_image.txt` |

## Niveaux de confiance

- **mesuré** : observé au banc ou dans le code et vérifié (trace, comparaison à l'arcade, lecture d'instruction).
- **déduit** : inféré par lecture statique ou raisonnement (alignement automatique, homologie de code), sans
  vérification au banc.
- **supposé** : hypothèse, « probable », transport automatique non validé, section dépassée. À vérifier avant
  de s'en servir.

Reprise de `tools/symboles/symboles_ro3.csv` : « sûr » issu du journal → mesuré ; « sûr » automatique → déduit ;
« probable » et « hypothèse » → supposé (le niveau d'origine est rappelé dans `source`). Les fonctions d'Upper
reprises de l'esquisse de transport (`symboles_ro5_esquisse.csv`, appariement « identique » ou « structure »,
score ≥ 0,9) sont « supposé », sauf celles que confirme une source indépendante : adresse citée par un rapport
d'Upper (la ligne du rapport fait foi), ou concordance des premières instructions 68K produites pour ro3 et ro5
dans les cartes v149 (≥ 6 instructions identiques, adresses absolues masquées) → « déduit ».

## Ajouter une ligne

1. **Avant d'analyser une adresse**, `quoi.py <adresse>` : ce qui est déjà su, et surtout les mises en garde.
2. Après une découverte : une ligne dans le TSV de l'espace **principal** (une seule ligne par chose ; les
   autres espaces vont dans `adresse_autres`) ; un champ va dans `champs.tsv`.
3. Toujours une `source` (`§N` du journal, ou chemin du rapport + section ; hors dépôt : `<workspace>/…`) et une
   `confiance`. **Rien d'inventé** : en cas de doute, « supposé ». Les pièges vont dans `mises_en_garde`.
4. Une zone de code ou de données qu'on va occuper : la **réserver d'abord** dans `allocations.tsv`, puis
   `zones.py --verifie`.
5. `python3 re/outils/verifie.py` doit finir sur « 0 erreur(s) ».

Adresse vide permise seulement pour un `format`, une `structure` ou une `constante` sans adresse (format de
fichier, règle). Pas de tabulation ni de saut de ligne dans une cellule ; hexadécimal en majuscules ; une plage s'écrit `a-b`
(inclusive) dans `adresse`, ou la taille `N × B|W|L` en tête de `taille_type`, ou `(N o)`.

## Plus tard : le kit de décompilation

À la fin du projet, cet index servira de base au **kit complet** : exports vers Ghidra / IDA / MAME (étiquettes,
types, commentaires), en-têtes C des structures (joueur, objets, A5, formats), cartes annotées par construction.
Rien de cela n'est encore fait : ici, seulement les connaissances, sourcées.

Conflits connus et décisions : [CONFLITS.md](CONFLITS.md).
