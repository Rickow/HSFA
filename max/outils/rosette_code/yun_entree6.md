# Yun (pl28) : entrée [6] du pac -> champs du gabarit (vérifié dans le code PSP, 2026-10-11)

Persos standard : init du perso -> `0x6AB48(objet, id, liste)` ; liste de 21 n° d'éléments (Eagle `0x2A3234` :
1 2 3 4 6 7 8 9 10 11 12 14 21 5 13 17 18 19 20 20 20) ; chaque n° passe par `0x6A638` (élément n du sous-en-tête :
décalage `+8+4n`, nombre `+0x108+4n`). Yun : init `0x1BF944`, 17 appels DIRECTS à `0x6A638` (pas de liste).

| champ du gabarit (+o) | table (agent) | standard : élément (section = élément + 2) | Yun : élément (section) |
|---|---|---|---|
| +0xC8 / +0x308 / +0x548 / +0x788 | animations $2B0… | 1-4 (3-6) | — (animations dans l'EBOOT) |
| +0x10 | jeux de boîtes | 5 (7) | 0 (2) |
| +0x9D4 / 9D8 / 9DC / 9E0 | boîtes $90 / $94 / $98 / $9C | 6-9 (8-11) | 1-4 (3-6) |
| +0x9E4 | attaques $A0 | 10 (12) | 5 (7) |
| +0x9E8 | table $88 | 11 (13) | 6 (8) |
| +0x9EC | table $C0 | 12 (14) | 7 (9) |
| +0x18 | ? | 13 (15) | 8 (10) |
| +0x9F0 | ? | 14 (16) | 9 (11) |
| (hors gabarit) | octets des coups normaux (s17 / s18) | 15 / 16 (17 / 18) | 10 / 11 (12 / 13), par le même décalage |
| +0x20 | table $264 | 17 (19) | 12 (14) |
| +0x28 / +0x2C | ? | 18 / 19 (20 / 21) | 13 / 14 (15 / 16) |
| +0x80 / +0x84 / +0x88 | ? | 20 (22) | 15 (17) en +0x80 et +0x84 ; +0x88 non rempli |
| +0x9FC | ? | 21 (23) | 16 (18) |

**Règle : élément Yun = élément standard − 5, pour TOUS les champs remplis** (la table `SECTIONS["pl28"]` de
`donnees_joueur_max.py` est donc confirmée : b90=3, b94=4, b98=5, b9c=6, a0=7, t88=8, tc0=9, d17=12, d18=13, t264=14).
Seul écart : Yun appelle deux fois `+0x84` et jamais `+0x88` (élément 15 dans les deux, comme le standard 20/20/20).
