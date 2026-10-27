# SFA3 MAX → CPS2 : avancées

Portage des 4 persos propres à **Street Fighter Alpha 3 MAX** (PSP) — Eagle, Maki, Yun, Ingrid — sur le moteur
arcade CPS2 retraduit (base : SFA3 Upper, module `ro5`, places `$26`/`$27` + 2 à créer). Plan : `docs/journal/HANDOFF.md`
§109 (ordre Upper → MAX → Hyper ; fins existantes réutilisées d'abord, fins PSP converties en fin de projet).

Ce dossier est tenu par la session de travail « MAX » ; le reste du dépôt par la session « HSFA ».

| dossier | contenu |
|---|---|
| `notes/` | notes techniques (`max-*.md` : rosette du code PSP ↔ 68K, tables d'animation, palettes, textes, injection…) |
| `outils/` | scripts (extraction PSP, traducteur MIPS PSP → 68K, générateurs de frames / animations / fins, pierre de Rosette de construction PSP ↔ Upper ↔ Hyper, Ghidra) |

## Règles

- **Pas de données de jeu** : ni extraits PSP/PS2/arcade, ni tables ou graphismes générés (`animations.json`,
  frames, tuiles, palettes binaires…). Seulement le code et la documentation qui permettent de les régénérer.
- Chemins anonymisés (`<workspace>`, `~`) ; identité de commit `Rickow` ; messages terminés par la ligne
  `Co-Authored-By`.
- Deux sessions écrivent dans ce dépôt : chacune ne touche que ses dossiers, et fait `git pull --rebase` avant
  chaque `git push`.
- Les notes partagées de travail restent dans `work/notes/` (hors dépôt) ; on en recopie ici une version
  anonymisée quand elles ont avancé.
