# Le banc MAME et le fork `sfa3hx`

Décision du §109 : un **fork de MAME** sert de banc de développement et de validation, avant le cœur FBNeo final.
On y garde le débogueur, les scripts Lua et la comparaison avec la ROM arcade. Détail complet : [OUTILS.md](OUTILS.md)
§4 ; scripts : [`src/hsfa/mame/`](../../src/hsfa/mame/) ; patchs : [`patches/mame-fork/`](../../patches/mame-fork/README.md).

## 1. Deux bancs

| | Banc « stock » | Fork `sfa3hx` |
|---|---|---|
| binaire | MAME 0.285 officiel, jeu Phoenix `sfa3ud` (programme non chiffré) | `cps2f` (MAME 0.285 + patch), jeu `sfa3hx` (clone de `sfa3ud`) |
| sert à | SFA3 traduit et ROM arcade de référence (`REF=1`) : diagnostic, test des commandes, fins | Upper et Hyper (tuiles au-delà de la ROM de SFA3), non-régression d'Upper, VERSUS d'Hyper |
| blocs externes | `banc_mem.lua` (prises de lecture) | `HSFA_EXT` (ROM `$A00000-$CFFFFF`) |
| tuiles hors ROM SFA3 | impossible | `HSFA_GFX` : ROM graphique de 128 Mo, codes d'objet sur 20 bits |
| plans | `banc_plans.lua` (renumérotation) | registres `$804200-$804205` : une base par plan (`HSFA_PLANS`) |
| sprites | `banc_sprites.lua` + `banques/` | `banc_sprites.lua` + `banques_hx/` |
| horloge 68K | — | `HSFA_CLOCK` |
| son | ROM de `sfa3ud` | `HSFA_SON` : ROM hybride d'Upper ; lecteur de flux ADX ; rejeu SFA1/SFA2 (patchs suivants) |

## 2. Les trois couches Lua

Chargées dans cet ordre, avant le script de scénario :
1. **`banc_mem.lua`** : sert au 68K les fichiers `ext_<adresse>.bin` (mots gros-boutistes).
2. **`banc_plans.lua`** : convertit les codes de tuile de plan du portage en codes CPS2 (`plan1.bin`, `plan2.bin`,
   `f312.bin`) ; avec `HSFA_PLANS` (fork), écrit seulement les bases des plans.
3. **`banc_sprites.lua`** : détourne la liste d'objets, éclate chaque objet en tuiles 16×16 et convertit chaque code
   par la table de son **emplacement** (bits 13-15 de Y) : 0 banque commune, 1 décor, 2/3 persos de J1/J2, 4 fichier
   graphique de la scène, 6/7 joueurs 3/4. Écrit la liste convertie dans les deux banques d'objets.
   `BANC_LAT4` (§146) diffère le changement de fichier de l'emplacement 4 tant que ses objets sont affichés.

⚠ Une prise Lua posée avant `banc_sprites.lua` voit la liste convertie : lire `BANC_OMBRE` (§106). `banc_mem.lua` doit
être chargé dans tout script ponctuel, sinon l'exécution diverge (§75).

## 3. Scripts de scénario

| Script | Rôle |
|---|---|
| `jeu.lua` | partie avec entrées scriptées (`INPUTS`), journal des modes, captures (`SNAPS`) |
| `commandes.lua` | test des commandes : 42 actions comparées à l'arcade (`commandes.py`) |
| `tournee.lua` | partie Arcade complète d'un perso (`PERSO`, `MODE`, `FORCE`…), arrêt sur exception ; base des balayages de fins |
| `force_stage.lua` | décor imposé |
| `visu.lua` | visualiseur d'état PS2 : rend dans MAME un état PCSX2 (§89) |
| `_prof_adapt.lua` | profil des adaptateurs mémoire (§138) |

Variables : [journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md) §6 et [OUTILS.md](OUTILS.md) §4.3.

## 4. Lancements types

```bash
# Upper sur le fork (depuis $HSFA_WORK/mame ; W5=$HSFA_WORK/mame_ro5)
BANC_COMMUN=351 PERSO=00 NF=70000 HSFA_PLANS=300,340,3a0 \
HSFA_GFX=$W5/hsfa_gfx.bin,$W5/hsfa_plans.bin@3000000 BANC_BANQUES=$W5/banques_hx/ BANC_PTR_ANIM=FF40BC \
BANC_GFX_INTRO=456 BANC_DIR=$W5/ OUT=p00.txt nice -n 19 $HSFA_CPS2F sfa3hx -rompath $W5/roms_fork \
  -video none -sound none -nothrottle -skip_gameinfo -nvram_directory /tmp/nv -autoboot_script tournee.lua
```

Hyper : même forme avec `BANC_COMMUN=545` et le dossier `work/mame_ro9` (voir
[`valide_tout.sh`](../../scripts/validation/valide_tout.sh)). `roms_fork/sfa3hx` est un lien vers le dossier
`sfa3ud` de la traduction.

## 5. Règles d'hygiène

- Toujours `-video none -sound none -nothrottle -skip_gameinfo` et `nice -n 19` ; un calcul lourd à la fois.
- Jamais `-state` en ligne de commande (bloque sur l'écran des sommes de contrôle) : `SAVEAT`/`SAVENAME`, puis
  `manager.machine:load(nom)` depuis Lua (§110).
- EEPROM figée (`~/.mame/nvram/sfa3ud` en lecture seule) ou `-nvram_directory` temporaire : sinon les parties
  divergent (§81).
- Ne jamais tracer sur une construction qu'un autre peut refaire : figer une copie des ROM et noter les md5.
- Une écriture relevée à « l'image N » a lieu pendant N+1 ; `-debug` décale le minutage (§67, §81).

## 6. Ce qui reste à faire au fork

Verrou de la liste d'objets et emplacements de banques en natif (encore en Lua) ; `HSFA_EXT` ne sert que des bases
fixes (rien pour les blocs d'Hyper `$940000` / `$C84000`, servis par `banc_mem.lua`) ; intégrer le rejeu au fork de
référence (`rejeu-sur-fork-flux.patch`, §145).
