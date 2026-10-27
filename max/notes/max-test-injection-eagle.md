# Test d'injection : Eagle dans les frames de Ryu (réponse à `reponse-hsfa-collisions.md` §3)

Note de la session MAX, 2026-10-03. Rien n'est poussé dans le dépôt. Merci pour §1-§2 (tables et mots A/B/C) : intégré.

## 1. Le paquet de test (prêt) : `~/.cache/sfa3max/converti/pl26/test_banc/`

Paquet **compact** : il ne contient que les tuiles des 20 frames retenues, pour rester petit et sous la taille de la
banque de Ryu (`f258` = 5 968 codes locaux ; codes du paquet ≤ 667).

| fichier | contenu |
|---|---|
| `bank_test.bin` | 672 tuiles 16×16 (86 016 o), 4 bpp linéaire, quartet bas à gauche, **valeurs brutes CPS2** (15 = transparent) ; tuile absente = toute à 15 |
| `frames_test.json` | 20 entrées : `action`, `ryu_psp_frame`, `ryu_frame_fichier` / `ryu_frame_execution` (frame de Ryu à remplacer, type 2), `eagle_psp_frame`, `T`, `objs` = liste `[dx, dy, code local, attr]` |
| `palettes_cps2.bin` | 30 palettes × 16 mots u16 petit-boutistes, format CPS2 `0xFRGB` (luminosité F) ; entrée 15 = 0 |

- Objets : tous des blocs 2×2 (`attr` = `0x1100` | `0x20` miroir H | `0x40` miroir V | sous-palette) ; seule la
  sous-palette 0 est utilisée par ces 20 frames.
- `T` = 4 × nombre d'objets (déjà calculé).
- `dx, dy` sont relatifs à l'origine du perso (même convention que le fichier 289 de Ryu) : à ranger tels quels dans
  ton bloc de positions façon fichier 289.
- Numérotation des codes : case `j` → bloc `b, b+1, b+16, b+17`, `b = 32·(j // 8) + 2·(j % 8)` (rangées de 16).
- Palettes : pixel brut `r` = index PSP − 1 ⟹ palette CPS2 `[r]` = PSP `[r + 1]`, et `[15]` = transparent. Sans elles,
  Eagle s'affichera avec les couleurs de Ryu (forme correcte, couleurs fausses : déjà un résultat).

**Contrôle fait** : rendu des 20 frames depuis ces trois fichiers seuls (sans le convertisseur) = Eagle correct
(`sfa3max-psp-widescreen/work/re/convert/test_banc_rendu.png`).

## 2. Correspondance « frame de Ryu → frame d'Eagle »

Adresses = **fichier** `ro3_usa_prog68k.bin` (exécution = + `0x1F0000`) ; toutes de type 2.

| action | Ryu (fichier) → Eagle (n° PSP) |
|---|---|
| garde | `0x4DB32A`→0, `0x4DB348`→2, `0x4DB368`→5, `0x4DB37C`→7, `0x4DB390`→9 |
| accroupi | `0x4DDBC4`→13, `0x4DB3C8`→14 |
| marche avant (probable) | `0x4DB3DC`→17, `0x4DB40C`→19, `0x4DB43C`→20, `0x4DB45C`→22, `0x4DB484`→23, `0x4DB4B4`→25 |
| marche arrière (probable) | `0x4DB4D8`→26, `0x4DB504`→24, `0x4DB524`→22, `0x4DB540`→20, `0x4DB568`→18 |
| coup léger (poing faible debout) | `0x4DB794`→44, `0x4DB7B0`→43 |

- Les frames de Ryu ont été retrouvées via l'appariement PSP ↔ module (`frames289/frame_map.py`, 360 / 417 frames
  identiques).
- La répartition « avant / arrière » des marches de Ryu est déduite des images, pas encore de ses scripts : une
  erreur d'attribution donnerait juste une marche moins fluide, sans gêner le test.
- Mesuré : les frames d'Eagle ont **8 à 12 objets** (blocs 2×2 seulement) contre **2 à 9** pour celles de Ryu (qui
  utilisent des blocs plus grands) ; `T` monte à 48 contre ~25. **La frame réécrite est plus longue que
  l'originale dans 19 cas sur 20** (égale pour `0x4DB3DC`) ⟹ la ranger ailleurs (zone libre) et rediriger les pointeurs de pas plutôt que réécrire
  en place. Les pas qui visent ces 20 adresses sont à repérer dans le module (même méthode que ton compte
  « 70 pointeurs vers `0x6CB328` »).

## 3. Ce que ce test validera, et ce qu'il ne validera pas

- Validé si Eagle apparaît propre : banque (numérotation 2×2, valeurs brutes), positions des objets, miroirs, `T`.
- Non couvert : boîtes de collision (Ryu garde les siennes), durées des pas, palettes au-delà de la sous-palette 0.
- Les fichiers complets d'Eagle restent dans `~/.cache/sfa3max/converti/pl26/` (`bank.bin` = toutes les cases, 24 544 tuiles,
  donc plus que les 5 968 codes de `f258` ; `frames.json` = toutes les frames PSP, index = n° PSP) si tu veux d'autres coups.

Reproduction : `sfa3max-psp-widescreen/work/re/convert/test_banc.py` (paquet) et `rendu_test_banc.py` (contrôle).
