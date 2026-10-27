# `src/hsfa/` — traducteur MIPS → 68000 et chaîne de construction

*Street Fighter Alpha Anthology* (PS2) contient SFA3, Upper et Hyper sous forme d'une **recompilation statique
68000 → MIPS** : chaque registre 68K vit dans une case du scratchpad, les drapeaux aussi. Ces scripts **reconnaissent
les idiomes du recompilateur et réémettent le 68000 d'origine** (ce n'est pas un décompilateur), assemblent le
résultat, l'entourent d'un petit noyau 68K et produisent une ROM programme CPS2. La ROM arcade de SFA3 sert de corrigé.

- Vue d'ensemble : [docs/architecture/traducteur.md](../../docs/architecture/traducteur.md).
- **Référence complète** (fiche de chaque script, banc Lua, formats, recettes, incohérences connues) :
  [docs/architecture/OUTILS.md](../../docs/architecture/OUTILS.md).
- Journal : [docs/journal/HANDOFF.md](../../docs/journal/HANDOFF.md) ; les « §N » des commentaires du code renvoient à
  ses sections.

Les scripts sont **à plat** dans ce dossier : ils s'importent par leur nom (`import translate`, `import profils`…).

## Les scripts qui comptent

| Étape | Script | Rôle |
|---|---|---|
| configuration | `profils.py` | constantes par module (`MODULE=ro3` SFA3, `ro5` Upper, `ro9` Hyper) |
| | `hsfa_config.py` | chemins locaux par variables d'environnement (`HSFA_WORKSPACE`…) ; utilisé par `scripts/localiser.py` |
| extraction | `extract_anthology.py`, `mwo3_codec.py`, `table_son.py` | archive AFS `X_DATA.BIN`, décompresseur MWo3, table native des commandes son |
| traduction | `translate.py` | idiomes MIPS → 68K, suivi symbolique, passes de la recette mémoire « cps2 » |
| | `extra_regs.py`, `dn_alu.py` | registres supplémentaires A8/D8 ; écritures perdues (audit) |
| assemblage | `assemble.py`, `m68k.py`, `mips.py` | placement itératif, branchements, tables ; longueurs 68K ; décodeur MIPS |
| construction | **`mame_test.py`** | point d'entrée : image complète (noyau `kernel68k.py`, ressources natives `assets_natifs.py`, talons) |
| diagnostic | `diag.py`, `watch.py` | première exception + trace avec l'adresse MIPS ; point d'observation |
| non-régression | `commandes.py` (+ [`scripts/validation/`](../../scripts/validation/)) | comparaison du test des 42 commandes |
| graphismes | `banques.py`, `anthgfx.py`, `cps2rom.py`, `gfx.py`, `lz148778.py` | banques et plans de l'Anthology → codes de la ROM CPS2 ; conteneurs ; décompresseur du moteur |
| fork | `hsfa_gfx.py`, `hsfa_plans.py`, `hooks_fork.py` | ROM graphique étendue et mémoires de décor pour `sfa3hx` ; points de raccordement natifs |
| son | `gen_son.py`, `gen_hybride.py`, `z80son.py` | ROM son au format MAME depuis X_DATA ; ROM hybride d'Upper |
| visualiseur | `visu_rom.py` | ROM du visualiseur d'état PS2 (§89) |
| MAX | `banques_max.py` | persos MAX dans le banc (en pause) |

Les autres scripts (`census.py`, `verify.py`, `e2e.py`, `diverge.py`, `chain*.py`, `rosetta*.py`, `prof_an.py`…) sont
des outils de mesure ou des étapes historiques (carte MIPS ↔ 68K) : liste commentée dans OUTILS.md §3. Les scripts Lua
du banc sont dans [`mame/`](mame/) (`banc_mem.lua`, `banc_plans.lua`, `banc_sprites.lua`, `jeu.lua`, `tournee.lua`,
`commandes.lua`…) ; le patch du fork dans [`patches/mame-fork/`](../../patches/mame-fork/README.md).

## Démarrage rapide

Les chemins de l'espace de travail sont écrits `<workspace>/…` : travailler dans une **copie localisée**
(`python3 scripts/localiser.py DOSSIER --lua`, voir [docs/guide/demarrage.md](../../docs/guide/demarrage.md)). Puis,
depuis `DOSSIER/src/hsfa` :

```bash
# 1. construire SFA3 (ro3) -> $HSFA_WORK/mame/roms_tr/sfa3ud/
XDATA=$HSFA_XDATA nice -n 19 python3 mame_test.py
#    surveiller « écritures de registre tombées » et « non résolus » dans le compte rendu

# 2. chercher la première faute (sans --nobuild : reconstruit d'abord)
MAXF=20000 nice -n 19 python3 diag.py 30 --nobuild

# 3. non-régression complète (SFA3, jusqu'à ~2 h)
bash ../../scripts/validation/nonreg.sh
#    attendu : « aucune exception » x3, « 42 actions, 0 différentes », 133,3 %

# Upper : même chose avec MODULE=ro5 ; tables graphiques :
MODULE=ro5 python3 banques.py tout
```

Prérequis : Python 3 avec `numpy` (et `capstone` pour `kernel68k.disasm`) ; MAME 0.285 pour le banc ; les modules
`roN_usa_prog68k.bin` extraits de l'ISO, `X_DATA.BIN`, et la ROM `sfa3ud` (Phoenix) pour le banc de référence.

## À savoir avant de modifier quoi que ce soit

- **Recette mémoire « cps2 »** : un octet PS2 à l'adresse `a` est à `a ^ 1` côté 68K ; un long est rangé moitiés
  échangées en mémoire. Tout script de comparaison arcade ↔ traduction doit normaliser.
- `assemble.py` relit des **marqueurs dans les mnémoniques** produits par `translate.py` (`(cible …)`, `[mips …]`,
  `T_…`, `CODE_…`, `_ECH`) : ne pas changer leur format.
- Chaque règle a un interrupteur (`=0` → ancien comportement, ROM identiques à l'octet).
- Après chaque correctif du traducteur : reconstruire, vérifier les compteurs, lancer la non-régression
  ([méthode](../../docs/methodes/oracle-et-non-regression.md)).
- `hooks_fork_<module>.json` est une entrée de la construction (`MODULE=… python3 hooks_fork.py` pour le régénérer).
