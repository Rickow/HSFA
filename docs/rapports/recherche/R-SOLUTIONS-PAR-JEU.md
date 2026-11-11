# Quelle solution pour quel jeu (2026-11-10)

Besoins (mesurés ou relevés dans le dépôt) :

| | Upper | Upper MAX | Hyper | Hyper Arcade (greffe) |
|---|---|---|---|---|
| graphismes | ≥ 34,9 Mo (> 32 Mo, HANDOFF §49) | ≈ 42,6 Mo (+ ≈ 7,7 Mo pour Eagle, Maki, Yun, Ingrid) | banques de *Zero*, *Zero 2* et Upper : région de 64 Mo dans le cœur | idem Hyper, + décors d'Upper |
| programme 68000 | > 4 Mo (données au-delà, `$C80000`) | idem | > 4 Mo (`$940000`) | idem |
| son | QSound hybride (taille à mesurer face aux 8 Mo câblés) ; musique des nouveaux personnages en flux, inexistante sur CPS-2 | idem | 2e QSound (sons d'*Alpha* et *Alpha 2*) + ≈ 200 Mo de musique en flux | idem |

Solutions, par méthode :

| méthode | Upper | Upper MAX | Hyper | Hyper Arcade |
|---|---|---|---|---|
| **Aucune modification** (carte d'origine) | seulement avec sacrifices (tuiles, programme dans 4 Mo, sans musiques en flux) | non | non | non |
| **Méthode officielle de Capcom : carte fille sur CN5/CN6** (comme 93661G-2, 93646C-3, 00716C-3), ici avec banques, et accès au 68000 par CN7 (registre, programme > 4 Mo ; lignes d'adresse à vérifier) | oui, sans les musiques en flux (thèmes existants à la place) | idem | oui **avec le son d'Upper** (thèmes et voix d'*Alpha 3*, comme sur PS2), voir plus bas ; sinon non | idem |
| **Carte SD** : la même carte fille, mais chargée depuis une carte SD (principe du multi Darksoft), plus un lecteur audio | oui, complet | oui | en théorie, très lourd (2e puce son) | idem |
| **FPGA** : cœur CPS-2 de Jotego étendu, MiSTer (SDRAM jusqu'à 128 Mo, flux audio depuis la SD) | oui | oui | oui | oui |
| FPGA, Analogue Pocket (moins de mémoire) | oui | probable | douteux (musique) | douteux |
| **Émulation** : cœur FBNeo HSFA | **fait** | **fait** (lots d'essai) | **fait** | en cours (greffe) |
| **Recompilation native** (à la cps2recomp) | possible | possible | possible | possible |

Hors de notre retraduction : sur NAOMI, Upper d'origine existe, et le patcheur `sfa3u-naomi-2026` de Zer0-NexuS y ajoute
les personnages de MAX.

Lecture : sur vraie CPS-2, Upper et Upper MAX deviennent jouables avec une carte fille à banques (sans les musiques
propres aux nouveaux personnages) ; Hyper et Hyper Arcade demandent du son qu'aucune CPS-2 ne sait produire. Pour
tout faire sur du vrai matériel, la cible réaliste est un cœur MiSTer étendu. Voir `O-` (connecteurs, bus) et `P-`
(synthèse).

## Cartes filles : pas d'espace en plus, une fenêtre de 32 Mo (2026-11-10)
- Les adresses de tuiles viennent de la CGA, qui ne compte que jusqu'à 32 Mo ; CN5/CN6 sont des copies de CN3/CN4. Une
  carte fille **déplace** des ROM dans la même fenêtre (la PAL 9J choisit qui répond selon la zone) ; carte B + carte fille
  se cumulent, mais le total reste ≤ 32 Mo (*Zero 2* + 93661G-2 : ROM sur les deux, total sous 32 Mo ; cartes de location :
  tout sur la fille).
- Avec des banques, la fenêtre visible reste de 32 Mo mais la carte fille peut cacher 64, 128 Mo… derrière. Cumul utile :
  zone fixe (ROM de la carte B ou de la fille) pour les éléments communs, zones commutées pour personnage 1, personnage 2 et
  décor ; la PAL 9J, reprogrammée, décide quelle zone vient d'où.

## Le « pire combat » tient-il dans 32 Mo ? (estimation, mesure exacte à faire)
Mesure exacte impossible dans cette session : il faut les banques d'Upper et d'Hyper construites depuis l'ISO (outils de
la session du projet). Estimation à partir des chiffres connus :
- un personnage pèse de 0,9 à 2,3 Mo (Ryu 0,86, Guile 1,08, Maki 1,66, Eagle 1,82, Yun 2,00, Ingrid 2,25 :
  `docs/MAX-Etude-Contenu-Persos.md`) ; tous les décors d'Upper réunis font 5,4 Mo, un décor seul bien moins ;
- *Alpha 3* entier (28 personnages, tous les décors, l'interface) tient déjà dans 32 Mo, soit moins de 1 Mo par personnage
  en moyenne.
⇒ un combat demande les éléments communs + au plus ≈ 4,5 Mo de personnages + un décor. Sauf si les éléments communs
dépassaient 25 Mo, ce qui est exclu puisque 28 personnages et tous les décors tiennent avec eux dans 32 Mo, **le pire
combat tient largement**, pour Upper, Upper MAX et Hyper. Points à vérifier par la mesure : images de victoire et de fin
(grandes illustrations propres à chaque personnage), écran de sélection d'Hyper (toutes les versions).

## Hyper avec le son d'Upper
Sur PS2, Hyper faisait déjà parler toutes les versions avec les voix d'*Alpha 3* (`SON-HYPER-ROM.md`). Si Hyper reprend la
musique QSound d'Upper (thèmes d'*Alpha 3*) au lieu de ses flux enregistrés, et garde ces voix, il n'a plus besoin ni du
2e QSound ni d'un lecteur audio : son besoin en son devient celui d'Upper. Avec la carte fille à banques, **Hyper et Hyper
Arcade deviennent possibles sur vraie CPS-2**, au prix de : la musique propre à chaque version (arrangements *SF2*,
*Alpha*, *Alpha 2*), les voix par version (ajout d'HSFA, pas du jeu PS2), et les thèmes des personnages console d'Upper,
qui n'ont jamais existé en QSound (thèmes existants à la place). Reste à vérifier, comme pour Upper : le programme de plus
de 4 Mo par CN7, et la taille du son QSound face aux 8 Mo câblés.

## Les deux points vérifiés (2026-11-10)

### 1. CN7 et le 68000 (relevé de WydD, onglet `Wiring`)
- CN7 reçoit, par les tampons LS245 10D et 10E, **16 lignes d'adresse** du bus local de la puce DL-1727 (MIF), celles qui
  adressent aussi les ROM programme (A0-A15 des supports 3-10) ; par le LS245 10B, **8 lignes de données** (Q0-Q7 du
  programme) ; plus des signaux de contrôle des puces MIF et CIF, et neuf lignes partagées avec CN1 (C17-C25), sans doute des
  adresses hautes ou des sélections, puisque la carte de communication de Capcom décode son adresse `620000` à partir de CN7.
- ⇒ **Registre de banques : oui.** Un octet écrit par le 68000 suffit, c'est exactement ce que fait la carte de communication
  (UART 8 bits).
- ⇒ **Programme de plus de 4 Mo par CN7 : non, en l'état.** Seules 8 lignes de données y arrivent ; le 68000 lit son
  programme et ses données en 16 bits. Solution de rechange : une petite carte sur les supports de ROM programme (3-10), comme
  le fait le multi Darksoft, qui commute elle aussi une banque, commandée par le même registre ; le traducteur range les
  données qui débordent (aujourd'hui `$C80000` pour Upper, `$940000` pour Hyper) dans cette fenêtre commutée.
- Rappel : pour faire tourner un programme modifié sur une vraie carte, il faut soit le chiffrer avec la clé de la carte,
  soit une carte à clé neutre (cartes « Phoenix », ou clé reprogrammée avec un programmateur comme openkey-cps2 de
  jwestfall69, par le connecteur CN9 des cartes récentes).

### 2. Le son QSound face aux 8 Mo câblés
- Mesure sur la ROM `sfa3` de l'utilisateur : les 8 Mo d'échantillons d'*Alpha 3* (`sz3.11m`, `sz3.12m`) sont **pleins**
  (aucun bloc de 4 Ko vide).
- Upper (HANDOFF §118, §127) : sa propre ROM QSound fait aussi 8 Mo et n'a **aucun instrument de musique** (≈ 1,8 Mo
  manquent : sur PS2, sa musique vient d'ailleurs). La ROM « hybride » d'HSFA met donc Upper (0-8 Mo) et *Alpha 3* (8-16 Mo)
  côte à côte : 16 Mo.
- ⇒ **Le son d'Upper ne tient pas dans 8 Mo** : sons propres d'Upper + instruments d'*Alpha 3* ≈ 8 + 1,8 Mo, si sa ROM est
  pleine comme celle d'*Alpha 3* (taille réellement occupée à mesurer sur l'ISO).
- Solution : **la même méthode de banques pour le son**. Les lignes d'adresse de la ROM QSound passent aussi par CN3, donc
  par CN5 ; la carte fille peut commuter une banque de sons par combat (éléments communs, instruments, voix des deux
  personnages). Même conclusion pour Hyper avec le son d'Upper.

Bilan : la méthode officielle (carte fille sur CN5/CN6) + un registre sur CN7 + une petite carte sur les supports du
programme couvrent graphismes, son et programme, pour les quatre jeux (Hyper et Hyper Arcade avec le son d'Upper).

## Jeux hors des listes officielles : où ils tournent (2026-11-10)
MAME et FBNeo identifient un jeu par sa fiche (noms, tailles et empreintes des fichiers, machine à simuler).

| où | jeu absent des listes officielles |
|---|---|
| vraie carte CPS-2 | tourne si le matériel correspond et avec la bonne clé (ou une clé neutre) : la carte n'a pas de liste |
| MAME officiel | seulement en remplaçant un jeu existant (mêmes noms et tailles, même matériel) ; MAME signale les empreintes fausses et lance |
| FBNeo officiel | même principe ; empreinte fausse signalée ou refusée selon la version et l'interface |
| Fightcade | non : jeux exacts de sa liste uniquement |
| HBMAME | oui avec une fiche ajoutée (hacks et homebrew ; les « PS2 Backport » de strygo y sont) |
| cœur FBNeo et fork MAME d'HSFA | oui, déjà (fiches propres, fichiers cherchés par nom, sans contrôle d'empreinte) |
| MiSTer | oui : un fichier MRA décrit l'assemblage des ROM ; facile à écrire si le cœur gère le matériel |

Pour HSFA : Upper, Upper MAX et Hyper demandent du matériel étendu, que seul un émulateur modifié (ou un cœur FPGA étendu)
fournit ; une fiche ne suffit pas. La construction depuis l'ISO étant déterministe (empreintes stables, contrôle du
27 octobre), des fiches avec de vraies empreintes sont possibles pour HBMAME ou une proposition à FBNeo, et des MRA pour le
MiSTer. *Alpha 3* retraduit, conforme à la CPS-2 standard, pourrait remplacer un *Alpha 3* existant dans MAME (curiosité).
