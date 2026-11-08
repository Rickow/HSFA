# Upper MAX depuis les disques du joueur (`hsfa_build.py --jeux uppermax --psp-iso …`)

Upper avec les quatre persos de *Street Fighter Alpha 3 MAX* (PSP) : Eagle, Maki, Yun et Ingrid. Le résultat est
l'archive FBNeo `sfa3umhsfa.zip`, à l'état du lot **2b31** (banc_max52). On part de deux disques seulement :
- l'ISO PS2 de *Street Fighter Alpha Anthology* (USA) ;
- l'ISO PSP de *SFA3 MAX* (Europe, ULES-00235 v1.01).

Il ne faut ni programme d'arcade, ni EBOOT déchiffré, ni dump. Seul outil en plus : `vasm` (`vasmm68k_mot`), qui
assemble le code MAX.

## Étapes (dans `hsfa_build.py`)

| Étape | Outil | Entrées | Sorties |
|---|---|---|---|
| `psp` | `hsfa_build.py` (`tools/max/iso_psp.py`) | ISO PSP | `cache/psp/BOOT.BIN` (EBOOT déjà en clair dans l'ISO), `pac/pl26-29_e.pac` ; identité et empreintes contrôlées |
| `max_donnees` | `regen_max.py` | ISO PSP (`DATA`), sorties d'Upper (anims, X_DATA, extraction, `mame_ro5`), ROM graphique de SFA3 (`cache/arcade`) | `cache/max_regen/` : cache MAX v2 (`converti/`, `fork/`, `s/`) et sources `.s` de `rosette_code`, avec les outils de `max/` |
| `son_uppermax` | `son/chaine_son.py` | ISO PSP (pac, `se_mid.pac`), ROM son hybride d'Upper, module ro9 | `travail/agent_son_max/roms_son_max_pas/` (hx3.*), `commandes_voix_max.s`, `commandes_son_max.s` |
| `prog_uppermax` | `um_prog.py` (+ `fige.py`, `integration_2b31/`) | Upper sans MAX (banc de référence), cache MAX, sources | `travail/mame_ro5um/banc/` (programme, `ext_*.bin`, banques) |
| `paquet_uppermax` | `tools/fbneo-hsfa/paquet_fbneo.py upper_max` | tout ce qui précède | `archives/sfa3umhsfa.zip` |

Sans `--psp-iso`, `uppermax` donne Upper sans les persos MAX, identique à `--jeux upper`.

## Contenu du dossier

- `regen_max.py` : pilote de régénération du cache MAX. Il suit l'ordre de l'atelier :
  - Yun sans l'onde d'efct pour `gfx_fork` ;
  - `portraits_fork` après l'habillage ;
  - `brouillons` → `projectiles_max` → `brouillons`.

  Il ajoute les compléments (scripts et palettes de fin, sauts, parcours). Sans programme d'arcade, il saute les
  étapes d'apprentissage de la Rosette et lit les tables apprises versionnées dans `max/`. L'option `--sfa3ud` sert
  au développement : elle refait cet apprentissage.
- `parcours_max.json` : table de décision, avec des ids seulement. C'est le tirage du parcours Arcade relevé sur PSP
  (R6 de l'intégration). Le rang 5, le rival et le boss sont relus dans l'EBOOT.
- `traduire_2b31.py` : copie du `max/outils/rosette_code/traduire.py` de **d98c4f1**. Il sert seulement à produire
  `s/acteurs_fins_max.s` à l'état du lot 2b31 ; la session MAX passera aux acteurs actuels après un lot d'essai.
- `um_prog.py`, `fige.py` et `integration_2b31/` : construction MAX=1 de l'intégration, figée à l'état 2b31
  (traducteur v154 + crochets MAX ; + `PRETE_TEST` / `MEMSWAPD` de la v159, §204, et `PRETE_CMP` de la v160, §207,
  pour que la carte d'Upper reste celle de la préparation). On n'y trouve que les fichiers que la construction lit, avec des marques de
  chemins `@UM_*@`, plus 2 relevés d'adresses.
- `son/` : chaîne de la ROM son. Elle contient :
  - `extrait_psp.py` et `rend_seq.py` (banque commune PSP) ;
  - `gen_voix_max.py` (agent voix) ;
  - `gen_son_max.py` (agent son : cris, voix d'Ingrid, `$2C`) ;
  - `numeros_max.json` : numéros de commandes libres et commandes vues. Ce ne sont que des contrôles.

  Elle utilise aussi `max/outils/sons/voix_max.py` et `banque_commune.py` (session MAX).

## Garanties (07/11, agent script_um)

- Toutes les sorties régénérées sont identiques au lot 2b31, avec la ROM graphique d'arcade : cache (121/126),
  sources `.s`, ROM son (6/6), commandes son. Les 5 écarts du cache sont sans effet sur le programme : lignes opA
  des scripts de fin (remises à 0 par `fins_integration.py`) et commentaires de `parcours_max.json`.
- Voir `docs/rapports/BUILD.md` §10 pour la construction depuis zéro et la voie « ISO seule ».
