# Voix d'Hyper comparées à l'arcade (2026-10-16)

Mesures qui ont produit `../voix_arcade.tsv` (voix « par pas ») ; les cris de dégâts / K.O. sont dans
`../cris_arcade.tsv`.

- `lot.txt` : les 46 comparaisons (jeu d'arcade, case de la grille, version d'Hyper, nom).
- `comparaisons/<nom>.tsv` (`compare_voix_arcade.py`) : 35 gestes joués à l'identique par J1 dans l'arcade (SFA1 ou
  SFA2) et dans Hyper, chacun depuis l'état sauvé au début du combat ; voix entendues de part et d'autre. État
  **avant** correction.
- `supers/<nom>.super.tsv`, `marqueurs_supers/` : même chose pour 11 super-coups (`--super` : jauge remplie par
  1 500 images de coups spéciaux avant la sauvegarde de l'état ; un geste ne compte que si les deux jeux y jouent le
  même nombre de voix).
- Akuma, Bison, Dan de SFA1 (cachés) : perso forcé par l'octet `$FF84A2` pendant la sélection
  (`--poke 800-960:FF84A2:02`, `0A`, `0C` ; frontal `HSFA_POKE`).
- `marqueurs/<nom>.tsv` (`marque_voix.py`) : chaque entrée de la table de voix de la version reçoit un code marqueur ;
  chaque voix entendue est ainsi rattachée à son code SFA3 d'origine, puis à la voix d'arcade du même geste.

Refaire (cœur de diagnostic `HSFA_QSLOG`, voir `../mesure_cris_arcade.py`) :

```sh
compare_voix_arcade.py joue_linux coeur_diag.so sfa2.zip sfa3hhsfa.zip <system> <sortie> --jeu sfa2 --grille 4,0 --hyper 01.Z2 --nom Ken_Z2
marque_voix.py joue_linux coeur_diag.so sfa3hhsfa.zip <system> <sortie> Ken_Z2 01.Z2 <marqueurs>
fusionne_voix_arcade.py <marqueurs + marqueurs_supers> lot.txt > ../voix_arcade.tsv
corrige_voix.py ancien.zip nouveau.zip          # ou paquet_fbneo.py, qui l'applique
```
