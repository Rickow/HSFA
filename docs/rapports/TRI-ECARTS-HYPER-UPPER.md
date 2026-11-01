# RAPPORT — tri des 50 écarts robustes Hyper ≠ Upper (ZERO 3), 01/11/2026

Entrée : `banc_greffe_upper/resultats/phases_ecarts.tsv` (50 écarts « robustes »). Constructions v153 (Upper ro5
`0b8ecca2`, Hyper ro9 `a5f7fae0`), banc `banc_coups.lua` inchangé. Outils et journaux : `outils/`, `lots/`, `sondes/`.

## 1. Bilan

| verdict | nombre |
|---|---|
| **défaut de traduction** | **0** |
| retouche Anthology (donnée du module PS2) | 2 |
| artefact du banc, distance de départ (prouvé dans les deux sens) | 21 |
| artefact du banc, cadence turbo (Upper en turbo redonne Hyper) | 18 |
| indéterminé | 9 |

Aucun correctif du traducteur n'est donc proposé ; `untranspile/` n'a pas été créé (rien à corriger). Le traducteur
principal et `github/` n'ont pas été touchés.

## 2. Défaut → règle du traducteur → sites

| défaut | règle / fonction du traducteur | idiome MIPS | sites ro3 / ro5 / ro9 | correctif |
|---|---|---|---|---|
| aucun établi | — | — | — | — |

Contrôles statiques faits en passant (traduction relue contre le désassemblage, Upper / Hyper) : test de recouvrement
des boîtes (Upper `$59A6`, Hyper `$8494` : ajouts d'Hyper — table de boîtes par version `$99B70` si `BTST #7,$D2`, portée
+4 si `BTST #1,$D2` et `$257` — traduits correctement), poussée des corps (Upper `$5B82`, Hyper `$86A2` : identiques),
lectures de la table des dégâts (Upper `$5312-$5390`, Hyper `$7D74-$7DC2` : même séquence `EORI.B #1,($3,A7)`).

## 3. Cause commune (supers en ISM A, et la plupart des écarts)

- **Distance de départ** : Hyper tourne en turbo (4 tours de jeu pour 3 images) et le banc ne peut pas le remettre
  en NORMAL. Pendant la manipulation, un appui « → » tenu 3 tours fait faire à Hyper **un pas de marche de plus**
  (ex. Birdie : J1 1F9 → 1FF dans Hyper, 203 → 207 dans Upper). Les charges « ← » reculent aussi d'une autre longueur.
  Au début du coup, J1 est donc 2 à 13 px plus près ou plus loin de J2 que dans Upper (`outils/dist_depart.py`).
- Les coups touchés sont ceux **sensibles à la distance au pixel près** : ruées et prises (Bull Revenger : Birdie passe
  à travers J2 quand l'écart des boîtes de poussée tombe sous 11 px ; Knee Press, Hissho Burai Ken, Shinku Tatsumaki,
  Shitenshu, Dash Straight, Sonic Break, Kikosho). En ISM A, le tableau teste les supers de ruée et de corps-à-corps à
  trois niveaux, d'où leur nombre. En ISM X, la seule super est le plus souvent un projectile, peu sensible à la distance.
- **Preuve** (`outils/lot_comp.py`, `resume_comp.py`) : Hyper rejoué à la distance de départ d'Upper donne exactement le
  résultat d'Upper, ET Upper rejoué à la distance d'Hyper donne exactement le résultat d'Hyper, pour les 21 lignes.
  Birdie a été vérifié à la main : la sonde voit la même boîte d'attaque et la même boîte de corps, avec J1 déjà
  passé derrière J2 dans Hyper.
- **Cadence** (`outils/lot_turbo.py`, `resume_turbo.py`) : 13 Alpha Counter et 5 coups de la palette redonnent dans Upper
  le résultat d'Hyper dès qu'Upper joue en turbo (VITESSE 1 ou 2, phases 0-2).
- **À corriger dans le banc**, pas dans le traducteur : imposer la distance au début du coup (après la manipulation),
  ou comparer à distance égale. On ne retiendrait alors que les 2 retouches et les 9 indéterminés.

## 4. Les 2 retouches

Chun-Li X, arrière + MK (N19), et le Hyakuretsu Kyaku martelé (L862.2), où c'est ce même normal qui sort : 13 → 6.
Les pas d'animation sont identiques, sauf **l'octet d'attaque** du pas actif. Il vaut `0x0A` dans Upper et `0x06` dans
Hyper : image `0x261EB8` / `0x1DC9A8`, module ro5 `0x5DBB7D` / module ro9 `0x506AED`. La différence est déjà dans les
modules PS2 d'origine, et le traducteur recopie la donnée telle quelle.

## 5. Les 9 indéterminés

- **Rolento A, Alpha Counter ×3** :
  - même animation à l'octet près (12 pas comparés), mêmes tables de boîtes, sauf l'entrée `0x2B` ajoutée par Hyper
    à la table `$90` ;
  - dans Hyper, le coup de J2 touche J1 au 1er pas `0x41` de l'Alpha Counter (boîte des jambes `$98`, image 32), avant
    son pas actif ; Upper échange les coups ;
  - c'est une course entre le coup de J2 et l'Alpha Counter, comme les 13 autres Alpha Counter, mais le turbo d'Upper
    ne la reproduit pas.
- **Commandes non canoniques de la palette** (Evil Ryu A N75 / N76, Fei-Long X N75 / N76, T. Hawk V N73 / N74) :
  - le reconnaisseur de commandes renvoie un autre coup (Evil Ryu : spécial `$AA=04` par Hyper `$01498A`, au lieu de la
    super `$AA=0A`, Upper `$09BA7C`) ;
  - avec des appuis allongés ou décalés (`outils/lot_lent.py`), Upper et Hyper tombent d'accord sur certaines variantes
    et pas sur d'autres ;
  - les commandes canoniques marchent dans Hyper : la super d'Evil Ryu sort avec N71 / N72 (2×QCB+K) ;
  - c'est probablement la cadence, sans preuve.
- Pour trancher ces 9 lignes : l'oracle PCSX2 (Hyper PS2 d'origine). Non lancé : la manip devrait y être rejouée au
  tour près, et l'enjeu est faible.

## 6. Tableau par écart

| perso isme | id | coup | Upper | Hyper | verdict | preuve |
|---|---|---|---|---|---|---|
| Akuma A | L692.2 | Alpha Counter | 2/1 J1-9/1 | 4/3 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 2/6 |
| Akuma A | L692.3 | Alpha Counter | 2/1 J1-9/1 | 4/3 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 2/6 |
| Balrog A | L755.3 | Dash Straight | 14/1 | 15/1 | ARTEFACT (distance) | départ H−U = -13 px ; Hyper compensé = 14/1 ; Upper à la distance d’Hyper = 15/1 |
| Birdie A | L783.1 | Bull Revenger | 32/2 | 0/0 | ARTEFACT (distance) | départ H−U = −2 px ; Hyper à dist+2 = Upper ; Upper à dist−2 = 0/0 (= Hyper) |
| Birdie A | L783.2 | Bull Revenger | 48/3 | 0/0 | ARTEFACT (distance) | départ H−U = −2 px ; Hyper à dist+2 = Upper ; Upper à dist−2 = 0/0 (= Hyper) |
| Birdie A | L783.3 | Bull Revenger | 64/4 | 0/0 | ARTEFACT (distance) | départ H−U = −2 px ; Hyper à dist+2 = Upper ; Upper à dist−2 = 0/0 (= Hyper) |
| Cammy A | L692.1 | Alpha Counter | 2/1 J1-9/1 | 2/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 6/6 |
| Cammy A | L692.2 | Alpha Counter | 2/1 J1-9/1 | 2/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 6/6 |
| Cammy A | L692.3 | Alpha Counter | 2/1 J1-9/1 | 2/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 6/6 |
| Charlie A | L845.2 | Sonic Break | 6/1 | 7/1 | ARTEFACT (distance) | départ H−U = -10 px ; Hyper compensé = 6/1 ; Upper à la distance d’Hyper = 7/1 |
| ChunLi A | L692.1 | Alpha Counter | 4/1 J1-9/1 | 0/0 J1-9/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 4/6 |
| ChunLi A | L692.2 | Alpha Counter | 4/1 J1-9/1 | 0/0 J1-9/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 4/6 |
| ChunLi A | L692.3 | Alpha Counter | 4/1 J1-9/1 | 0/0 J1-9/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 4/6 |
| ChunLi A | L868.1 | Kiko Sho | 6/1 | 12/2 | ARTEFACT (distance) | départ H−U = 8 px ; Hyper compensé = 6/1 ; Upper à la distance d’Hyper = 12/2 |
| ChunLi A | L868.2 | Kiko Sho | 23/4 | 18/3 | ARTEFACT (distance) | départ H−U = 8 px ; Hyper compensé = 23/4 ; Upper à la distance d’Hyper = 18/3 |
| ChunLi A | L868.3 | Kiko Sho | 39/7 | 34/6 | ARTEFACT (distance) | départ H−U = 8 px ; Hyper compensé = 39/7 ; Upper à la distance d’Hyper = 34/6 |
| ChunLi X | L862.2 | Hyakuretsu Kyaku | 13/1 | 6/1 | RETOUCHE (donnée) | même normal (arrière+MK) ; pas d’animation 0x261EB8 / 0x1DC9A8 : octet d’attaque 0x0A (ro5 0x5DBB7D) / 0x06 (ro9 0x506AED), lu tel quel dans les modules PS2 |
| ChunLi X | N19 | normal arrière + MK | 13/1 | 6/1 | RETOUCHE (donnée) | même normal (arrière+MK) ; pas d’animation 0x261EB8 / 0x1DC9A8 : octet d’attaque 0x0A (ro5 0x5DBB7D) / 0x06 (ro9 0x506AED), lu tel quel dans les modules PS2 |
| Dan A | L917.2 | Hissho Burai Ken | 38/5 | 30/4 | ARTEFACT (distance) | départ H−U = 2 px ; Hyper compensé = 38/5 ; Upper à la distance d’Hyper = 30/4 |
| EvilRyu A | N75 | double demi-cercle arrière + LK | 0/0 | 14/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| EvilRyu A | N76 | double demi-cercle arrière + HK | 58/12 | 15/3 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| EvilRyu V | N75 | double demi-cercle arrière + LK | 6/1 | 12/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 5/6 |
| EvilRyu V | N76 | double demi-cercle arrière + HK | 15/2 | 12/3 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 5/6 |
| FeiLong A | N75 | double demi-cercle arrière + LK | 28/8 | 0/0 | ARTEFACT (distance) | départ H−U = 4 px ; Hyper compensé = 28/8 ; Upper à la distance d’Hyper = 0/0 |
| FeiLong V | N72 | double quart arrière + HK | 4/1 | 0/0 | ARTEFACT (distance) | départ H−U = 3 px ; Hyper compensé = 4/1 ; Upper à la distance d’Hyper = 0/0 |
| FeiLong V | N75 | double demi-cercle arrière + LK | 14/1 | 0/0 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 4/6 |
| FeiLong V | N76 | double demi-cercle arrière + HK | 17/2 | 12/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 3/6 |
| FeiLong X | N72 | double quart arrière + HK | 4/1 | 0/0 | ARTEFACT (distance) | départ H−U = 3 px ; Hyper compensé = 4/1 ; Upper à la distance d’Hyper = 0/0 |
| FeiLong X | N75 | double demi-cercle arrière + LK | 19/1 | 6/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| FeiLong X | N76 | double demi-cercle arrière + HK | 22/2 | 18/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| Gen A | L975.2 | Shitenshu | 34/8 | 33/7 | ARTEFACT (distance) | départ H−U = 2 px ; Hyper compensé = 34/8 ; Upper à la distance d’Hyper = 33/7 |
| Gen A | L975.3 | Shitenshu | 44/10 | 43/9 | ARTEFACT (distance) | départ H−U = 2 px ; Hyper compensé = 44/10 ; Upper à la distance d’Hyper = 43/9 |
| MBison A | L1132.1 | Knee Press Nightmare | 7/1 | 14/2 | ARTEFACT (distance) | départ H−U = -10 px ; Hyper compensé = 7/1 ; Upper à la distance d’Hyper = 14/2 |
| MBison A | L1132.2 | Knee Press Nightmare | 17/2 | 25/3 | ARTEFACT (distance) | départ H−U = -10 px ; Hyper compensé = 17/2 ; Upper à la distance d’Hyper = 25/3 |
| MBison A | L1132.3 | Knee Press Nightmare | 37/4 | 45/5 | ARTEFACT (distance) | départ H−U = -10 px ; Hyper compensé = 37/4 ; Upper à la distance d’Hyper = 45/5 |
| RMika A | L692.1 | Alpha Counter | 4/1 J1-9/1 | 4/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 4/6 |
| RMika A | L692.2 | Alpha Counter | 4/1 J1-9/1 | 4/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 4/6 |
| RMika A | L692.3 | Alpha Counter | 4/1 J1-9/1 | 4/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 4/6 |
| Rolento A | L692.1 | Alpha Counter | 1/1 J1-9/1 | 0/0 J1-9/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| Rolento A | L692.2 | Alpha Counter | 1/1 J1-9/1 | 0/0 J1-9/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| Rolento A | L692.3 | Alpha Counter | 1/1 J1-9/1 | 0/0 J1-9/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| Ryu A | L692.2 | Alpha Counter | 4/1 | 4/1 J1-9/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 2/6 |
| Ryu A | L692.3 | Alpha Counter | 4/1 | 4/1 J1-9/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 2/6 |
| Ryu A | L1227.2 | Shinku Tatsumaki Senpu Kyaku | 42/8 | 0/0 | ARTEFACT (distance) | départ H−U = 2 px ; Hyper compensé = 42/8 ; Upper à la distance d’Hyper = 0/0 |
| THawk A | N67 | double quart avant + LK | 0/0 | 3/1 | ARTEFACT (distance) | départ H−U = -3 px ; Hyper compensé = 0/0 ; Upper à la distance d’Hyper = 3/1 |
| THawk A | N73 | double demi-cercle arrière + LP | 0/0 | 3/1 | ARTEFACT (cadence) | Upper rejoué en turbo (vitesses 1/2, phases 0-2) redonne le résultat d’Hyper 2/6 |
| THawk V | N67 | double quart avant + LK | 0/0 | 3/1 | ARTEFACT (distance) | départ H−U = -3 px ; Hyper compensé = 0/0 ; Upper à la distance d’Hyper = 3/1 |
| THawk V | N73 | double demi-cercle arrière + LP | 0/0 | 3/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| THawk V | N74 | double demi-cercle arrière + HP | 13/1 | 11/1 | INDÉTERMINÉ | ni la distance compensée ni le turbo d’Upper ne le reproduisent ; données d’animation identiques |
| THawk X | N67 | double quart avant + LK | 0/0 | 3/1 | ARTEFACT (distance) | départ H−U = -3 px ; Hyper compensé = 0/0 ; Upper à la distance d’Hyper = 3/1 |

## 7. Outils (dans ce dossier)

- `cmp.py` : états comparés d'un essai.
- `sonde.sh` + `lua/sonde.lua` : opcodes lus par image, prises en écriture / lecture avec PC, registres à une adresse
  (`PCH`) ; option `DIST`.
- `voir.py` (carte + couverture), `dis.sh` (unidasm sur `img/`).
- `lot_dist.py` / `resume_dist.py`, `dist_depart.py`, `lot_comp.py` / `resume_comp.py`, `lot_turbo.py` /
  `resume_turbo.py`, `lot_lent.py`.
