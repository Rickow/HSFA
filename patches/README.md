# Patchs des forks

Modifications appliquées aux sources de MAME et de FBNeo. Elles ne contiennent **que du code** : aucune donnée de jeu.

| Dossier | Fork | Sert à |
|---|---|---|
| [`mame-fork/`](mame-fork/README.md) | MAME 0.285, jeu `sfa3hx` (binaire `cps2f`) | banc de développement et de validation ([architecture](../docs/architecture/banc-mame.md)) |
| [`fbneo/`](fbneo/README.md) | libretro/FBNeo, pilotes `sfa3hsfa`, `sfa3uhsfa`, `sfa3hhsfa` | cœur « FinalBurn Neo HSFA » pour RetroArch ([architecture](../docs/architecture/coeur-fbneo.md)) |
| [`traducteur/`](traducteur/greffe-arcade-v153.patch) | traducteur `scripts/untranspile`, étiquette `v153` | variante de la greffe Arcade (`untranspile3`), voir [`tools/greffe-arcade/ETAPES-4-7.md`](../tools/greffe-arcade/ETAPES-4-7.md) |

Les patchs PCSX2 (`.pnach`) de l'époque PNACH sont dans [`legacy/pnach/`](../legacy/pnach/README.md).
