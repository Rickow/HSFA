# Voie B : greffer le mode Arcade d'Upper sur Hyper

Décision de l'utilisateur du 2026-10-10 (§144, remplace la « base Upper » du §143) : le produit final part du module
**Hyper** (`ro9`). On lui greffe, **au niveau MIPS**, la couche du **mode Arcade d'Upper** (« ro9 augmenté »). Upper
sert d'oracle : ses 40 fins sont validées. Rapports : [ETUDE-UPPER-HYPER](../rapports/ETUDE-UPPER-HYPER.md) (le choix),
[GREFFE-PREPARATION](../rapports/GREFFE-PREPARATION.md) et [GREFFE-DECORS](../rapports/GREFFE-DECORS.md) (la
préparation). Outils : [`tools/greffe-arcade/`](../../tools/greffe-arcade/), [`tools/etude-upper-hyper/`](../../tools/etude-upper-hyper/).

## 1. Pourquoi B plutôt que A

| | Voie A : base Upper + Hyper | Voie B : base Hyper + Arcade d'Upper |
|---|---|---|
| code à greffer | ≈ 1,1 Mo de MIPS, ≈ 34 000 instructions 68K, 1 445 tests de version | ≈ 98 Ko absents (≈ 3 350 instr.), ≤ 260 Ko en borne haute |
| données | 2,4 Mo, toutes les données d'attaque à convertir | ≈ 0,1-0,3 Mo (scripts de fin, adversaires, scènes) |
| risque principal | reconstituer Hyper dans Upper | la RAM A5 (variables d'Upper retirées par Hyper) et les lectures de `$102` |

Hyper n'a pas de mode Arcade ; son patch Arcade PS2 ([legacy](../../legacy/README.md)) n'est pas porté.

## 2. Ce qui est établi (§145)

- **Scènes** : `A5+4 = 6` CONTINUE, `8` GAME OVER, `A` fin du perso et générique, `C` sortie ; entre deux combats,
  `A5+4 = 4` et `A5+8` vaut `0` (init), `2` (carte), `4` (face-à-face, VS), `6` (combat), `8` (victoire).
- **Cœur à greffer** : 530 routines, 287 Ko de MIPS, ≈ 9 950 instructions 68K, dont 164 routines (111 Ko) absentes
  d'Hyper ; le reste est modifié par Hyper.
- **Table de relogement A5** : 443 déplacements utilisés ; 36 relogés dans la zone libre `$FF43BE-$FF7FFF` d'Hyper.
- **Règle `$102` → `$116`** : une lecture qui indexe une table par perso passe par `$116` ; une écriture de l'id pose
  aussi `$116/$117` ; une copie garde `$102` (la version).
- **Zone d'accueil** : le Z80 recompilé d'Hyper (fichier `[0x20, 0x22B00)`, 142 Ko), jamais traduit ni appelé par le
  68K d'Hyper. Insuffisante pour tout : un bloc de données ajouté est servi par le traducteur.
- **Prototype** : prochain adversaire (`0x250EF0`) et ses deux appelés ; assemblage du module augmenté sans non-résolu ;
  la traduction 68K de la greffe est identique instruction pour instruction à celle d'Upper, hors A5 relogés.
- **Décors** : 39 décors d'Upper sur 40 sont absents d'Hyper ([GREFFE-DECORS](../rapports/GREFFE-DECORS.md)).

## 3. Chaîne prévue

1. `tools/greffe-arcade/outils/greffe.py` copie les routines du cœur dans la zone d'accueil, reloge les A5 et les `lui`,
   copie les tables.
2. Le traducteur (copie dédiée) traduit en plus la zone greffée ; `mame_test.py` construit Hyper augmenté.
3. Oracle : mêmes parties scriptées qu'Upper (`tournee.lua`, `tournee_greffe.lua`), comparaison des scènes et des fins.
4. MAX : intégré d'abord sur Upper, puis transposé (98 adresses moteur sur 120 identiques dans Hyper).

## 4. Étape en cours

Étape 2 de `greffe_arcade` : greffe complète du cœur, données de fin (gfx 391-418, anim 458-485), décors.
