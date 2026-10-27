# Époque PNACH (PCSX2) — archives

Avant la retraduction en 68000 (fin septembre 2026), le projet modifiait directement la version PS2 de *Street
Fighter Alpha Anthology* avec des patchs PCSX2 (`.pnach`) : du MIPS injecté (« caves ») et des octets modifiés. Ce
dossier conserve ces travaux tels quels. Ils ne sont plus développés ; le fil « cross-stage » est en sommeil depuis le
2026-09-26 (journal, R§0-R§3).

| Dossier | Contenu |
|---|---|
| [`pnach/`](pnach/README.md) | patchs PCSX2 : mode Arcade d'Hyper, construction de référence du cross-stage et ses essais |
| `tools/` | anciens outils Python : patcheur « tout débloqué », empaqueteur de décors, rendus, émulateur R5900 partiel, accès PINE à PCSX2, décompilation par Ghidra |
| `docs/` | documents de l'époque (voir ci-dessous) |

## Ce que faisaient les mods

**Mode Arcade pour Hyper Street Fighter Alpha** (livré). Hyper n'a pas de vrai parcours arcade. Le mod en ajoute un :
suite d'adversaires CPU, victoire et défaite, continue, fin. Du MIPS injecté est accroché à la machine à états du jeu.
Documents : [ARCADE-Hyper-SFA](docs/ARCADE-Hyper-SFA.md), [PROJET-Hyper-Arcade](docs/PROJET-Hyper-Arcade.md).
Décision du 2026-10-10 : ce patch n'est pas porté vers HSFA ; le mode Arcade d'Upper sera greffé à la place
([voie B](../docs/architecture/voie-b-greffe.md)).

**Widescreen 16:9 natif** (livré, validé sur Hyper et Upper). La géométrie de rendu est élargie et l'« anneau » de
tuiles du décor est prolongé : on voit plus de décor au lieu d'une image étirée. Découverte centrale : le modèle en
anneau du compositeur de décor. Documents : [PROJET-Anthology-Widescreen-Tiles](docs/PROJET-Anthology-Widescreen-Tiles.md),
[PROJET-Hyper-Widescreen](docs/PROJET-Hyper-Widescreen.md), [ANALYSE-Widescreen-ISO](docs/ANALYSE-Widescreen-ISO.md)
(intégrer les patchs à l'ISO).

**Tout débloqué** (livré). Un patch d'octets qui rend disponibles tous les persos et tous les modes :
[`tools/unlock_patcher.py`](tools/unlock_patcher.py).

**Cross-stage** (inachevé). But : chaque perso combat dans son décor, avec des décors d'Upper importés dans Hyper et
chargés à la volée. Acquis :
- le décor est assemblé par un compositeur, à partir d'un réservoir de pages de tuiles et de listes de disposition ;
- les tuiles ne sont pas lues dans la banque partagée au moment du dessin : elles sont dans un **contexte par
  couche**, en tuiles 32×32 compressées, préparées au chargement. Modifier la banque après coup n'atteint jamais le GPU ;
- l'approche validée **repointe le contexte de couche** vers un paquet de tuiles déjà décompressées ;
- la compression du moteur est une variante de LZ, portée en Python : `lz148778.py`, aujourd'hui dans
  [`src/hsfa/`](../src/hsfa/lz148778.py) car le traducteur s'en sert pour lire les graphismes.

Documents : [PLAN-Cross-Stage-Actualise](docs/PLAN-Cross-Stage-Actualise.md),
[CARTO-Cross-Stage-Tables](docs/CARTO-Cross-Stage-Tables.md), [ANALYSE-Cross-Stage-Multi](docs/ANALYSE-Cross-Stage-Multi.md),
[PREP-Cross-Stage-Proto](docs/PREP-Cross-Stage-Proto.md), [PACKER-Recette](docs/PACKER-Recette.md),
[ANIMATION-et-Finitions](docs/ANIMATION-et-Finitions.md).

Autres documents du moteur PS2 : [CARTO-Caves-Memoire](docs/CARTO-Caves-Memoire.md) (régions de code injecté),
[CAVE-Loader-Design](docs/CAVE-Loader-Design.md) et [LOADER-Implementation-Spec](docs/LOADER-Implementation-Spec.md)
(chargeur), [ANALYSE-Menu-Groove-Visuels](docs/ANALYSE-Menu-Groove-Visuels.md),
[ANALYSE-Scene-Result-Boot](docs/ANALYSE-Scene-Result-Boot.md).

## Ce qui a mené à HSFA

En étudiant le portage, on a établi que l'Anthology est une **recompilation statique** du 68000 arcade en MIPS R5900 :
53 % des accès au scratchpad tombent dans 64 octets (`0x70001100-0x7000113f`) = les 16 registres `D0-D7` / `A0-A7`,
accédés en `.B` / `.W` / `.L` comme en 68000 ; les drapeaux sont émulés en mémoire. L'original arcade est donc la
véritable source de la version PS2, ce qui a conduit à la retraduire (journal, R§4-R§8 puis §1 et suivants).

## Outils de ce dossier

Ils gardent leurs chemins d'origine (`<workspace>/scripts`…) : voir [scripts/localiser.py](../scripts/localiser.py).
Dépendances propres : `zstandard` (`p2s_inject_stage.py`) ; `pyghidra` et Ghidra avec l'extension
ghidra-emotionengine-reloaded, langage `r5900:LE:32:default` (`decomp.py`) ; PCSX2 avec PINE (`pine_linux.py`).
`build_ctx.py` importe `lz148778` : il est dans `src/hsfa/`.
