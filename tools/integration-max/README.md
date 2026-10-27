# Intégration des persos MAX (Eagle, Maki, Yun, Ingrid) dans Upper

| Dossier | Contenu |
|---|---|
| [`upper/`](upper/MAX1.md) | Construction `MAX=1` d'Upper (pilote FBNeo `sfa3umhsfa`, patch 0013) : crochets `integre_max.py` / `agrandit_max.py`, préparation (`outils/`), sondes MAME (`lua/`). |
| [`conversion/`](conversion/) | Traducteur des sources MAX vers l’image d’Upper (`convertit_max.py`) et des frames (`convertit_frames.py`), avec leurs tables. |
| [`voix/`](voix/) | Voix de victoire et sons des persos MAX. |

**État au 2026-10-25.** `upper/untranspile/` et `upper/mame_test_max.diff` sont un instantané de la copie de travail de l'agent : ils ne sont pas encore fondus dans `src/hsfa/` ni dans `src/hsfa/mame_test.py`. Deux blocs du diff sont à reporter à la main, et des chemins écrits en dur restent à paramétrer (§4 de [`upper/fichiers.txt`](upper/fichiers.txt)). La fusion se fera quand les défauts MAX seront stables.

Bancs : [`../banc-max-psp/`](../banc-max-psp/BANC-PSP.md) compare Upper MAX à SFA3 MAX PSP coup par coup (mode B, oracle PPSSPP), et [`../ppsspp-banc/`](../ppsspp-banc/PPSSPP-BANC.md) fournit l'oracle et le comparateur d'appels. Savoir de la session MAX : [`../../max/notes/SAVOIR-MAX.md`](../../max/notes/SAVOIR-MAX.md).
