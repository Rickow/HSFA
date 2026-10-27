# Journal du projet

| Document | Rôle |
|---|---|
| [HANDOFF.md](HANDOFF.md) | journal complet, §1-§146 (et chapitres « racine » R§0-R§8, C1-C5) : chaque découverte, décision et correctif, dans l'ordre. **Source de vérité.** Les « §N » cités dans le code et la documentation renvoient ici. |
| [INDEX-HANDOFF.md](INDEX-HANDOFF.md) | index thématique ; §0 explique les trois séries de numéros (R§, C, §) ; signale les sections dépassées (⛔) |
| [ETAT-DES-LIEUX.md](ETAT-DES-LIEUX.md) | synthèse du 2026-10-04 (jusqu'à §115) : commandes, variables d'environnement, 25 pièges. L'état à jour est dans le [README](../../README.fr.md) et les §141-§146. |

Le contenu de `HANDOFF.md` n'est **pas modifié** par la réorganisation du dépôt du 2026-10-11 : il cite donc des
chemins d'avant. Correspondance :

| Chemin cité dans le journal | Emplacement actuel |
|---|---|
| `docs/HANDOFF.md`, `docs/INDEX-HANDOFF.md`, `docs/ETAT-DES-LIEUX.md` | `docs/journal/` |
| `docs/OUTILS.md`, `docs/ARCHI-Reorganisation-Donnees.md` | `docs/architecture/` |
| `docs/SYMBOLES.md`, `docs/FRAMES-Anthology.md` | `docs/reference/` |
| `docs/MAX-Etude-Contenu-Persos.md` | inchangé (document de la session MAX, laissé en place) |
| autres `docs/*.md` (cross-stage, widescreen PS2, mode Arcade PS2, caves, chargeur) | `legacy/docs/` |
| `tools/untranspile/*.py`, `*.json` (copie publiée du traducteur) | `src/hsfa/` (lien de compatibilité `tools/untranspile` → `src/hsfa`) |
| `tools/untranspile/mame/` (scripts Lua du banc) | `src/hsfa/mame/` |
| `tools/untranspile/nonreg.sh`, `nonreg_ro5.sh`, `balayage_fins.sh`, `valide_tout.sh` | `scripts/validation/` |
| `tools/build/hsfa_build.py`, `rom_iso.py` | `scripts/construction/` |
| `tools/extraction/` | `src/hsfa/` (`extract_anthology.py`, `mwo3_codec.py`, `table_son.py`) |
| `tools/lz148778.py` | `src/hsfa/lz148778.py` |
| `tools/mame-fork/` | `patches/mame-fork/` |
| `tools/fbneo-hsfa/*.patch` (dont `0001-…`, `0002-…`, `hyper-*.patch`) | `patches/fbneo/` |
| `tools/flux/*.patch` | `patches/mame-fork/` (fork), `patches/fbneo/` (cœur) |
| `tools/son-hyper/rejeu-sur-fork-flux.patch` | `patches/mame-fork/` |
| autres `tools/*.py` à la racine de `tools/` (époque PNACH) | `legacy/tools/` |
| `patches/*.pnach` | `legacy/pnach/` |

Les chemins `<workspace>/scripts/untranspile`, `work/...`, `agent_*` désignent l'espace de travail du développeur
(données de jeu, jamais publiées) ; leur équivalent publié est donné par [scripts/correspondances.tsv](../../scripts/correspondances.tsv).

Table complète ancien → nouveau chemin de la réorganisation : historique Git (`git log --follow`, `git log -M
--name-status`) ou commit « Réorganisation : déplacements purs ».
