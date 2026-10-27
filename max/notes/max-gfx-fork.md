# Graphismes des persos MAX pour le fork MAME (sfa3hx) : prêts

Note de la session MAX, 2026-10-04. Rien n'est poussé. Outil : `sfa3max-psp-widescreen/work/re/convert/gfx_fork.py`.

## Sorties : `~/.cache/sfa3max/fork/`

| fichier | contenu |
|---|---|
| `max_gfx.bin` | **58 866 tuiles neuves** (7,2 Mo) au format interne de MAME (même `encode()` que ton `hsfa_gfx.py`), à **concaténer juste après `hsfa_gfx.bin`** : codes **`$4C340`-`$5A931`** |
| `pl26_hx.bin` … `pl29_hx.bin` | table locale → code global (u32 LE), comme tes `banques/f<N>.bin` ; une tuile transparente (brut 15 partout) pointe vers le code **`$0`** (tuile vide de la ROM SFA3) |
| `rapport.txt` | décomptes |

- Ordre de réutilisation : tuile identique de la ROM SFA3, puis d'Upper (relue depuis `work/mame_ro5/hsfa_gfx.bin`,
  49 984 tuiles), puis d'un autre perso MAX ; sinon tuile neuve.
- Contrôle : pour les 4 persos, **108 960 / 108 960** tuiles locales redonnent exactement les mêmes pixels via leur
  code global (ROM SFA3, Upper ou `max_gfx.bin`).
- Place : 13,3 Mo occupés sur 96 dans la région étendue (Upper + MAX).

| perso | tuiles locales | réutilisées ROM / Upper / autre MAX | neuves |
|---|---|---|---|
| Eagle (pl26) | 24 544 | 787 / 425 / 680 | 13 976 |
| Maki (pl27) | 23 360 | 2 048 / 109 / 860 | 11 798 |
| Yun (pl28) | 27 360 | 366 / 1 266 / 888 | 15 046 |
| Ingrid (pl29) | 33 696 | 561 / 198 / 977 | 18 046 |

⚠ Les codes dépendent du nombre de tuiles d'Upper (49 984 aujourd'hui) : si tu relances `hsfa_gfx.py` et que ce nombre
change, relancer `gfx_fork.py` (variable `HSFA_GFX` = chemin de ton `hsfa_gfx.bin`).
Les frames (`frames.json`) gardent leurs codes LOCAUX : la table `plXX_hx.bin` fait la traduction, comme pour les
banques des persos de SFA3 / Upper dans `banc_sprites.lua`.
