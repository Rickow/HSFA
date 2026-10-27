# Démarrer avec HSFA

Ce guide va de l'ISO à un jeu traduit qui tourne au banc MAME, puis à la non-régression. Pour seulement construire
les jeux et les installer sur une console, [construction-iso.md](construction-iso.md) suffit.

## 1. Ce qu'il faut

| Élément | Rôle | Obligatoire |
|---|---|---|
| ISO de *Street Fighter Alpha Anthology* (USA, `SLUS-21317`) | toutes les données de jeu | oui |
| Python 3.8+ et `pip install -r requirements.txt` | traducteur, construction | oui |
| MAME 0.285 (`mame`) | banc de référence (`sfa3ud`) : diagnostic, test des commandes | pour le banc |
| fork MAME `sfa3hx` (`cps2f`, [patches/mame-fork](../../patches/mame-fork/README.md)) | Upper et Hyper au banc, non-régression d'Upper | pour le banc |
| ROM arcade `sfa3ud` (Phoenix) | oracle : comparaisons avec l'arcade, test des commandes | pour la validation |

Le dépôt ne contient aucune donnée de jeu. Les fichiers produits (ROM traduites, archives) restent sur votre poste.

## 2. L'espace de travail

Les scripts ont été écrits pour un espace de travail fixe, dont les chemins sont publiés sous la forme
`<workspace>/...`. Disposition attendue :

```
$HSFA_WORKSPACE/
  anthology_extract/        manifest.csv, decompressed/roN_usa_prog68k.bin (modules MIPS)   = $HSFA_EXTRACT
  work/                                                                                     = $HSFA_WORK
    xdata/X_DATA.BIN        extrait de l'ISO (lecture seule)
    mame/                   banc SFA3 : scripts Lua, roms/ (arcade de référence), roms_tr/ (traduction)
    mame_ro5/, mame_ro9/    bancs d'Upper et d'Hyper (roms_ro5/, roms_ro9/, roms_fork/, banques_hx/...)
    cps2/                   ROM CPS2 intermédiaires (sfa3ud_prog.bin...)
  mame-fork/mame/cps2f      binaire du fork                                                  = $HSFA_CPS2F
```

1. Copier `config.example.env` en `config.env`, adapter les chemins, puis `source config.env`.
2. Fabriquer une copie exécutable du dépôt, où `<workspace>` est remplacé par vos chemins :
   ```bash
   python3 scripts/localiser.py ~/hsfa-local --lua
   ```
   `--lua` copie aussi les scripts du banc (`src/hsfa/mame/*.lua`) dans `$HSFA_WORK/mame`, d'où MAME les lance.
   Le dépôt n'est pas modifié. Détail des variables : [`hsfa_config.py`](../../src/hsfa/hsfa_config.py).
3. Extraire les modules et `X_DATA.BIN` : le plus simple est de lancer une fois la construction depuis l'ISO
   ([construction-iso.md](construction-iso.md)), qui fait l'extraction et vérifie les empreintes.

## 3. Traduire un module

Depuis `~/hsfa-local/src/hsfa` (copie localisée) :

```bash
MODULE=ro3 XDATA=$HSFA_XDATA nice -n 19 python3 mame_test.py      # SFA3   -> work/mame/roms_tr/sfa3ud/
MODULE=ro5 XDATA=$HSFA_XDATA nice -n 19 python3 mame_test.py      # Upper  -> work/mame_ro5/roms_ro5/
MODULE=ro5 nice -n 19 python3 banques.py tout                      # tables des banques d'Upper
```

Surveiller dans le compte rendu les compteurs « écritures de registre tombées » et « non résolus » : toute hausse est
une régression. Ne jamais construire une référence avec `MAX_DEMO` ou `MAX_PAL`. Le rôle de chaque script est décrit
dans [architecture/traducteur.md](../architecture/traducteur.md) et, en détail, dans
[OUTILS.md](../architecture/OUTILS.md).

## 4. Lancer le banc

Toujours `-video none` (la fenêtre bloque MAME), `nice -n 19`, et jamais `-state` en ligne de commande. Depuis
`$HSFA_WORK/mame` :

```bash
# SFA3 traduit : pièce, Start, bouton 1 en continu ; captures aux images 3000 et 6000
INPUTS="1500-1508::IN2:Coin 1;1600-1608::IN2:Coin 2;2000-2006::IN2:1 Player Start;3500-19900%200,6::IN0:P1 Button 1" \
NF=20000 OUT=journal.txt SNAPS=3000,6000 nice -n 19 mame sfa3ud -rompath roms_tr -video none -sound none \
  -nothrottle -skip_gameinfo -snapshot_directory captures -autoboot_script jeu.lua
```

Upper et Hyper tournent sur le fork (`cps2f sfa3hx`) : voir [architecture/banc-mame.md](../architecture/banc-mame.md)
pour les variables (`HSFA_GFX`, `HSFA_PLANS`, `BANC_BANQUES`…) et les scripts de scénario (`tournee.lua`,
`commandes.lua`…).

## 5. Chercher une faute

```bash
MAXF=20000 nice -n 19 python3 diag.py 30 --nobuild              # ro3 ; sans --nobuild : reconstruit d'abord
MODULE=ro5 MAXF=12000 nice -n 19 python3 diag.py 30 --nobuild   # Upper
```

`diag.py` s'arrête à la première exception et remonte à l'instruction MIPS fautive grâce à `carte_image.txt`. Fin
attendue : « aucune exception ». Méthode complète : [methodes/oracle-et-non-regression.md](../methodes/oracle-et-non-regression.md).

## 6. Valider

Après **chaque** correctif du traducteur, depuis la copie localisée (`~/hsfa-local`) :

```bash
bash scripts/validation/nonreg.sh        # SFA3 : 3 diagnostics + 42 commandes (jusqu'à ~2 h)
bash scripts/validation/nonreg_ro5.sh    # Upper, sur le fork
bash scripts/validation/valide_tout.sh   # tout : reconstruit ro3/ro5/ro9, non-régressions, VERSUS d'Hyper, fins (~3 h)
```

Ces scripts lisent `HSFA_WORKSPACE` et prennent les outils dans le `src/hsfa` voisin (ou dans `HSFA_SRC`) : lancés
depuis le dépôt lui-même, ils trouveraient des scripts aux chemins `<workspace>` non remplacés. Résultats
attendus : 3 × « aucune exception », « 42 actions, 0 différentes », 133,3 % ; Upper « fin=finie » pour chaque perso.

## 7. Pièges à connaître dès le début

- Un octet PS2 à l'adresse `a` est à `a ^ 1` côté 68K ; un long est rangé moitiés échangées : tout script de
  comparaison avec l'arcade doit normaliser ([architecture/memoire-cps2.md](../architecture/memoire-cps2.md)).
- L'EEPROM du banc (`~/.mame/nvram/sfa3ud`) est réécrite à chaque sortie : la figer, sinon les parties divergent.
- `pkill -f` ou `pgrep -f` avec un motif présent dans la ligne de commande tue le shell : utiliser `ps -C mame`.
- Après chaque reconstruction, les adresses 68K bougent : relire `carte_image.txt` avant de poser un point d'arrêt.

Liste complète : [methodes/pieges-du-traducteur.md](../methodes/pieges-du-traducteur.md) et
[journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md) §7.
