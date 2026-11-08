# Données d'images des persos MAX (banc interne)

Banc INTERNE passé à chaque lot MAX (`docs/ATTENTES-ET-DECISIONS.md`). Il rejoue dans Upper MAX (MAME, module `max`
de `tools/banc-coups/lance.sh`) les entrées **effectives** des relevés faits sur la PSP (oracle SFA3 MAX, PPSSPP).
Les deux côtés sont mesurés **en tours de jeu** : démarrage, actif, récupération, avantages. Les écarts de plus d'un
tour doivent être expliqués avant livraison.

```sh
./frame_data.sh <copie figée Upper MAX> [--ref <copie précédente>] [--jobs 3]   # ≈ 4 min, PSP en cache
./frame_data.sh <copie> --mesure-seule                                          # remesure sans relancer MAME
run/lot.sh eagle A maki X ...                                                   # (re)faire les relevés PSP (cache psp_cache/)
```

- `outils/fd.py` : relevés (`psp`), rejeu (`upper`) et mesures (`mesure`). `psp_fd.py` : relevé PSP tour par tour
  (point d'arrêt). `coups.py` : coups et entrées ; noms et commandes repris de `docs/rapports/recherche/E-COUPS-MAX.md`.
  `tableaux.py`, `modes.py`, `bouge.py` : tableaux, tours contre images, valeurs qui bougent. `annexe.py` : annexe
  indicative SuperCombo CvS2. `psp_cadence.py` : contrôle des ralentissements PSP.
- `lua/tours.lua` : relevé par tour (`$FF851C`). `lua/exc.lua` : talons d'exception.
- Chaque lot vérifie l'empreinte de ce que MAME charge (`tools/bancs/empreinte.*`) ; en cas d'écart, arrêt.

Chemins : forme `<workspace>/…` (voir `scripts/localiser.py`). Il faut l'interpréteur du venv (numpy), le fork
MAME, `tools/banc-max-psp/psp` (pilote PPSSPP) et l'ISO PSP de l'utilisateur. Résultats, caches et traces restent dans
l'espace de travail.
