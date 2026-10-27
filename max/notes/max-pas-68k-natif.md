# Disposition d'un pas d'animation en 68K NATIF (ROM arcade) — à retenir pour l'injection dans le fork

Note de la session MAX, 2026-10-04. Vérifié sur la ROM `sfa3ud` (code et données). Concerne le fork natif (FBNeo/MAME),
pas la représentation dans le module PS2 (que tu gères déjà avec ta recette octets/mots/longs).

Un pas = 20 octets, lus par la routine arcade `0x2A770` (chargement) et `0x2A7EA` (avance) :

| décalage | contenu | lu par l'arcade |
|---|---|---|
| `+0` | durée (octet) | `move.l (a0),$32(a6)` → `$32` = durée, décomptée par `subq.b #1,$32` |
| `+1` | drapeaux de fin : bit 7 = reprise, bit 6 = fin avec enchaînement | `move.b 1(a0),d0 ; bmi … ; btst #6,d0` |
| `+2`, `+3` | mot « drapeau » PSP (octet bas, octet haut) | → `$34`, `$35` |
| `+4` | pointeur de frame (long, gros-boutiste) | |
| `+8` … `+$13` | mots A, B, C : **les 12 octets de l'entrée de boîtes PSP, dans le même ordre** | `move.b 8(a0)` = jeu de boîtes (×4 dans `$88`), `move.b $A(a0)` → table `$C0` |
| après un pas « reprise » | pointeur long du pas de reprise | `movea.l $14(a0),a0` (`0x2A80A`) |

Preuve sur les données : les 12 octets A/B/C de pas de Ryu (entrées de boîtes PSP) se retrouvent **tels quels** dans la
ROM arcade (ex. `0x14640A`), précédés de `05 00 00 00` (durée 5) et `00 14 CB D0` (pointeur de frame).

⟹ Pour écrire les scripts MAX en 68K natif depuis `animations.json` : octets `durée, drapeaux, drapeau bas, drapeau haut`
(= les 4 premiers octets du pas PSP), pointeur de frame en gros-boutiste, puis les 12 octets A/B/C bruts de l'entrée de
boîtes ; ajouter le pointeur de reprise après un dernier pas à bit 7 (le PSP reprend au début du script).
Exemple généré : `sfa3max-psp-widescreen/work/re/rosette_code/tables_explicites_*.s` (tables passées par adresse).
