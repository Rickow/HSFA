# Le traducteur MIPS → 68000

Vue d'ensemble. Le détail de chaque script (entrées, sorties, variables, fonctions) est dans
[OUTILS.md](OUTILS.md) ; le code est dans [`src/hsfa/`](../../src/hsfa/README.md).

## 1. Pourquoi c'est possible

Les jeux de l'Anthology ne sont pas émulés : le 68000 d'origine a été **recompilé statiquement en MIPS R5900**. Le
recompilateur range chaque registre 68K dans une case du scratchpad (`0x70001100…`) et tient les drapeaux en mémoire.
Il produit des **idiomes stéréotypés** : une instruction 68000 donne toujours la même suite d'instructions MIPS.
Le traducteur **reconnaît ces idiomes et réémet l'instruction d'origine**. Ce n'est pas un décompilateur : il ne
comprend pas le programme, il défait une transformation mécanique (§1-§21 du journal).

La ROM arcade de SFA3 sert de **corrigé** : 91 % du code de SFA3 s'aligne fonction par fonction sur elle. Upper et
Hyper n'ont pas de corrigé, mais partagent la même machine (§30) : ce qui est validé sur SFA3 se transporte.

## 2. Modules

| Module | Jeu | Code 68K recompilé (fichier) | RAM PS2 émulée | Dossier de travail |
|---|---|---|---|---|
| `ro3` | SFA3 | `0x22B00-0x393C40` | `0x900000` | `work/mame` |
| `ro5` | Upper | `0x22B00-0x41ACC0` | `0xA00000` | `work/mame_ro5` |
| `ro9` | Hyper | `0x22DE0-0x3BF140` | `0xB80000` | `work/mame_ro9` |

Base de chargement `0x1F0000` pour les trois. Avant le 68K, le fichier contient du **Z80 recompilé** (le programme
son), jamais retraduit (§16). Les autres modules de l'Anthology (SFA, SFA2 et variantes, Pocket Fighter) passent aussi
le traducteur à 98-99 % : [carte des modules](../reference/carte-modules.md).

`profils.py` réunit les constantes de chaque module (`MODULE=ro3|ro5|ro9`) : points d'entrée, aides du recompilateur,
routines patchées, tables. Une valeur absente désactive la fonction correspondante.

## 3. La chaîne

```
module MIPS (roN_usa_prog68k.bin) ──► translate.py ──► assemble.py ──► mame_test.py ──► ROM programme CPS2 (4 Mo)
        X_DATA.BIN (ISO) ─────────────────────────────────────────────┘  (noyau 68K,      + blocs externes ext_*.bin
                                                                          ressources,     + carte_image.txt, chutes.json
                                                                          talons)
X_DATA.BIN ──► banques.py / hsfa_gfx.py / hsfa_plans.py ──► tables de banques, ROM graphique étendue, plans
X_DATA.BIN ──► gen_son.py / gen_hybride.py ──► ROM son (SFA3 ; hybride pour Upper)
```

| Étape | Script | Rôle |
|---|---|---|
| profil | `profils.py` | constantes du module |
| traduction | `translate.py` | suivi symbolique des registres MIPS ; quand un motif complet est reconnu, émission de l'instruction 68000 ; pré-passes (paires non alignées, pile privée, zones de registres prêtés) et post-passes (raccourcissements, flux d'octets, fusion des `(An)+`) |
| | `extra_regs.py` | registres supplémentaires du recompilateur, « A8 » et « D8 » (§53) : prêtés à un registre libre par zone, sinon rangés à un domicile en RAM |
| | `dn_alu.py` | écritures de registre perdues (audit, §107) |
| assemblage | `assemble.py` | placement itératif, branchements courts ou longs, tables d'aiguillage et de données PC-relatives |
| image | `mame_test.py` | point d'entrée : profil → traduction → assemblage, puis noyau de tâches (`kernel68k.py`), ressources chargées par le code natif (`assets_natifs.py`), talons du portage ; écrit la ROM et ses annexes |
| contrôle | `diag.py`, `watch.py` | première exception au banc et instruction MIPS fautive (par `carte_image.txt`) ; point d'observation |
| graphismes | `banques.py`, `anthgfx.py`, `cps2rom.py`, `hsfa_gfx.py`, `hsfa_plans.py` | banques et plans de l'Anthology → codes de la ROM CPS2 ; ROM graphique étendue du fork |
| son | `gen_son.py`, `gen_hybride.py`, `z80son.py` | ROM son au format MAME ; ROM hybride d'Upper |

Les autres scripts de `src/hsfa` (`census.py`, `verify.py`, `e2e.py`, `diverge.py`, `chain*.py`, `rosetta*.py`…)
sont des outils de mesure ou des étapes historiques : [OUTILS.md](OUTILS.md) §3.

## 4. Ce que le portage a ajouté, et comment on le remplace

Le code recompilé n'est pas seul dans le module. Le portage PS2 a ajouté une **couche matérielle** (registres CPS-A/B,
QSound, entrées « mirroités » en variables, §57-§58), des **crochets**, du **code C natif** (aiguilleurs par table de
longs, §140) et un **noyau de tâches**. HSFA remplace :
- le noyau par un noyau 68K reconstruit (`kernel68k.py`, §60-§61) ;
- les variables matérielles par les vrais registres CPS2 (`HWREG`, `ADDRMAP` de `translate.py`) ;
- les ressources lues par le code natif (animations, fichier de frames à adresse fixe) par des blocs préparés à la
  construction (`assets_natifs.py`, §75) ;
- `setjmp` / `longjmp`, la manette et quelques routines par des talons écrits à la main.

## 5. Mémoire

Le code PS2 voit une mémoire **petit-boutiste** ; la CPS2 est gros-boutiste. Plutôt que de retrouver la disposition
arcade champ par champ, le traducteur applique une **recette universelle** (§29) : mot à la même adresse, octet à
l'adresse XOR 1, long avec ses moitiés échangées. Les pointeurs restent des adresses PS2, convertis à l'usage. Détail
et pièges : [memoire-cps2.md](memoire-cps2.md). Le coût de ces adaptateurs (~20 % du temps 68K en combat, §138) est
l'objet de la [réorganisation des données](ARCHI-Reorganisation-Donnees.md).

## 6. Interrupteurs

Chaque règle ajoutée a une variable d'environnement ; `=0` rend l'ancien comportement et doit redonner des ROM
**identiques à l'octet**. Exemples : `TAILBR`, `LUIDN` (§143), `CMPMM` (§145), `EXT_MEM` (§128), `FTC_AVANT`,
`EXG_PILE` (§126), `EXTRA_REGS`, `A8_HOME`, `D8_HOME`. Liste : [journal/ETAT-DES-LIEUX.md](../journal/ETAT-DES-LIEUX.md)
§6 et [OUTILS.md](OUTILS.md) §2.4. Méthode : [methodes/oracle-et-non-regression.md](../methodes/oracle-et-non-regression.md).

## 7. Sorties à connaître

| Fichier | Contenu |
|---|---|
| `roms_tr/sfa3ud/sz3ud.03c…sz3.10b` (ro3 ; `roms_ro5`, `roms_ro9`) | ROM programme de 4 Mo, en 8 × 512 Ko |
| `ext_<adresse>.bin`, `ext_liste.txt` | blocs servis hors de la ROM programme (données coupées, fichiers à adresse fixe) |
| `carte_image.txt` | une ligne par instruction émise : adresse 68K, va MIPS, mnémonique |
| `chutes.json` | écritures de registre sans traduction (audit des pertes silencieuses) |

Formats : [OUTILS.md](OUTILS.md) §5 et [reference/formats.md](../reference/formats.md).
