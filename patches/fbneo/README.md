# Cœur libretro FBNeo « HSFA »

Patchs contre [libretro/FBNeo](https://github.com/libretro/FBNeo), commit `af5d3f3`.

- Fonctionnement du cœur : [docs/architecture/coeur-fbneo.md](../../docs/architecture/coeur-fbneo.md).
- Une fiche par patch (problème, solution, alternatives écartées, fichiers, comment le couper) :
  [docs/architecture/coeur-fbneo-patchs.md](../../docs/architecture/coeur-fbneo-patchs.md). La fiche porte le numéro
  de la colonne « # ».
- Archives de jeu et notices : [tools/fbneo-hsfa](../../tools/fbneo-hsfa/README.md).
- **Licence** : les cœurs construits avec ces patchs sont FinalBurn Neo et en suivent la licence, recopiée mot pour mot
  dans [LICENSE-FBNeo.txt](LICENSE-FBNeo.txt) (ni vente, ni dons ; sources des modifications = ces patchs). Notices
  de stb_vorbis (patch `0004`) et du QSound HLE BSD-3 (patch `0001`) : [NOTICE.md](../../NOTICE.md). À joindre à toute
  archive de cœur.

## Patchs, dans l'ordre d'application

| # | patch | contenu | pourquoi | sources |
|---|---|---|---|---|
| 1 | `fbneo-hsfa.patch` | pilotes `sfa3hsfa` / `sfa3uhsfa` ; `cps_hsfa.cpp` (blocs externes, plans, liste d'objets convertie, ROM graphique étendue, codes d'objet sur 20 bits, son hybride) ; `Makefile.hsfa` ; lanceur `hsfa/hsfa_run.c` | jouer les programmes retraduits sans MAME ni scripts Lua | §136 |
| 2 | `fbneo-hsfa-widescreen.patch` | variante 448 × 224 16:9 (`-DHSFA_WS`, `Makefile.hsfaws`, cœur « FinalBurn Neo HSFA Widescreen ») | le décor existe au-delà des 384 px | §139 |
| 3 | `fbneo-hsfa-ws-flux.patch` | lecteur de flux musique ADX (`hsfa_flux.h`, `Y_DATA.BIN`), DIP « PS2 music » | des musiques n'existent qu'en flux sur le disque PS2 | §142, [FLUX](../../docs/rapports/FLUX.md) |
| 4 | `hyper-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch` | pilote `sfa3hhsfa` (Hyper) ; base des blocs externes déduite de `hsfa_ext.bin` ; `hsfa_run` `PILOTE=hyper` | Hyper a ses blocs en `$940000` et sa musique en flux | §143, [FBNEO-HYPER](../../docs/rapports/FBNEO-HYPER.md) |
| 5 | `0001-HSFA-rejeu-QSound-des-sons-SFA1-SFA2-d-Hyper-donnees.patch` | 2ᵉ QSound qui rejoue les sons SFA1 / SFA2 ; flux et rejeu lus dans le zip du jeu | la ROM QSound de 16 Mo est pleine | §145, [REJEU-FBNEO](../../docs/rapports/REJEU-FBNEO.md) |
| 6 | `0002-HSFA-chargement-differe-emplacement-4.patch` | chargement différé de l'emplacement 4 (`HSFA_LAT4`) | sur PS2 l'ancien fichier reste affiché quelques images (portrait d'Upper) | §146, [PORTRAITS](../../docs/rapports/PORTRAITS.md) |
| 7 | `0003-HSFA-options-du-coeur.patch` | réglages de l'écran OPTION en DIP B-H, écrits au menu des modes | l'écran OPTION PS2 est du C natif, non traduit | §147, [OPTIONS](../../docs/rapports/OPTIONS.md) |
| 8 | `0004-HSFA-stb_vorbis.patch` | décodeur stb_vorbis 1.22 (domaine public / MIT), API mémoire ; `-DHSFA_FLUX_VORBIS` | zip d'Hyper environ 5 fois plus léger | §150, [PLAN-VORBIS](../../docs/rapports/PLAN-VORBIS.md) |
| 9 | `0005-HSFA-flux-musique-Ogg-Vorbis.patch` | flux Ogg Vorbis dans `hsfa_flux.h` (ADX et Ogg cohabitent, boucles, états inchangés) | idem, sans changer le jeu | §150, [PLAN-VORBIS](../../docs/rapports/PLAN-VORBIS.md) |
| 10 | `0006-HSFA-carte-musique.patch` | carte musique d'Hyper : 2ᵉ Z80 (pilotes SFA1 / SFA2 d'origine) et 3ᵉ QSound ; aiguillage carte → flux → Z80 principal | musiques ZERO / ZERO 2 par leurs pilotes d'origine plutôt qu'enregistrées | §151, [PLAN-PARTITIONS-HYPER](../../docs/rapports/PLAN-PARTITIONS-HYPER.md) |
| 11 | `0007-HSFA-roulette-touche-piece.patch` | roulette de la sélection d'Hyper sur la touche Pièce (Select) ; Start reste au jeu | sur PS2 la roulette vient de Select ; Start gênait les EX | §157, [ETATS-HYPER](../../docs/rapports/ETATS-HYPER.md) §1.1 |
| 11b | `0007b-HSFA-hsfa_run-options-du-coeur-HSFA_VARS.patch` | lanceur d'essai seulement : `HSFA_VARS`, `HSFA_VARS2` / `HSFA_VARS2_IMAGE` servent les options du cœur | essayer les options sans RetroArch ; morceau absent du patch 7 | [OPTIONS](../../docs/rapports/OPTIONS.md) §3.2 |
| 12 | `0008-HSFA-registres-des-plans-ro9a.patch` | registres `$804200-$804205` complétés (mot en une fois, mise à jour au changement), région graphique déduite de `hsfa_gfx.bin` (80 Mo pour `ro9a`), pilote d'essai `sfa3hahsfa`, `hsfa_run` `PILOTE=arcade` | `ro9a` change de banque de plans en jeu, au-delà de 64 Mo | [COEUR-BANQUES](../../docs/rapports/COEUR-BANQUES.md) §A |
| 13 | `0009-HSFA-prototype-trous-carte-68K.patch` | prototype : les 7 trous libres de la carte 68K (5,08 Mo) servis en ROM depuis le membre facultatif `hsfa_trous.bin` ; sans ce membre, rien ne change | ROM programme et blocs externes pleins | [COEUR-BANQUES](../../docs/rapports/COEUR-BANQUES.md) §B |
| 14 | `0010-HSFA-melange-des-objets-transparence.patch` | mélange des objets : registres `$804220-$80423F` (un mode par palette OBJ) et `$804240` (mode des objets marqués par le bit 12 du mot X de la liste brute) ; modes 0 opaque, 1 additif, 2 alpha 50 %, 3 alpha 75 %, 4 soustractif, 5 noir 75 % ; priorité bit 12 > palette > option > opaque ; états compatibles dans les deux sens | les effets MAX sont dessinés en additif sur PSP (décidé par objet, champ +0xAA), le CPS2 n'a pas de transparence | [TRANSPARENCE](../../docs/rapports/TRANSPARENCE.md), [par objet](../../docs/rapports/TRANSPARENCE-PAR-OBJET.md) |
| 15 | `0011-HSFA-option-ombres-transparentes-PSP.patch` | option « Transparent shadows (PSP) » (DIP A bit 7, activée par défaut ; `HSFA_OMBRES=0/1` pour les essais) : tuiles d'ombre (palette 0x14, codes `0284A`, `305DF-30613`, `50888-5088A`) en noir à 75 % | ombres translucides comme sur PSP ; la palette 0x14 sert aussi au décor, d'où la règle par code de tuile | [OMBRES](../../docs/rapports/TRANSPARENCE-OMBRES-JAUGES.md) |
| 16 | `0012-HSFA-16-9-format-remplir-la-hauteur.patch` | cœur 16:9 : option « Screen format (fill height) » (Off, 4:3, 3:2, 14:9, 16:10, 5:3, 16:9) ; largeur = format × 288 (pixels arcade : 384 px ↔ 4:3), paire, plafonnée à 448 ; rognage centré, géométrie libretro suivie | montrer sur un écran moins large que 16:9 la part du décor élargi qui y tient (forks « remplir la hauteur ») | [TRANSPARENCE](../../docs/rapports/TRANSPARENCE.md) §13 |
| 17 | `0013-HSFA-pilote-sfa3umhsfa-Upper-MAX.patch` | pilote `sfa3umhsfa` « Street Fighter Alpha 3 Upper MAX (HSFA) » : mêmes ROM, init et options que `sfa3uhsfa`, `hsfa_trous.bin` facultatif, sans parent ; paquet : entrée `upper_max` → `sfa3umhsfa.zip` | Upper et Upper + MAX côte à côte (zips, états, réglages séparés), comparaison à l'œil des régressions | décision du 2026-10-24 |
| 18 | `0014-HSFA-provocation-sur-Select-en-combat.patch` | option « Taunt on Select (in fight) » (DIP A bit 6, par défaut ; `HSFA_PROVOC`) : en combat (`$FF8000` = 2, `$FF8004` = 4), Pièce du joueur N ajoute le bit 15 aux écritures de `$378` (sans crédit) ; gestionnaire `$FF8400-$FF8BFF` installé pour tous les pilotes HSFA | le portage pose Start dans `$370` ET `$372` à la même image : le front `$378` n'existe jamais, la provocation par Start est impossible | décision du 2026-10-24 |

**Numérotation.** « # » est le rang dans la chaîne ; les rapports disent « patch 8 » pour la ligne 8. Le patch 11b
a été extrait du commit `bca36de` de l'arbre de référence. Il garde le préfixe `0007b` pour ne pas renuméroter 0008
et 0009, déjà cités par les rapports. Les patchs 12 et 13 s'appliquent avec ou sans lui.

**Hors chaîne :**
- `fbneo-hsfa-decors.patch` : décors widescreen injectés (mode « bases de plans » pour SFA3), posé sur les patchs
  1-2 ; ne s'applique pas après le patch 6 sans adaptation de `cps_hsfa.cpp`
  ([INJECTION-FORK](../../docs/rapports/INJECTION-FORK.md)).
- `hsfa_run-sysdir.diff` : correctif du lanceur (dossier système copié dans un tampon), relevé pour ROCKNIX
  ([ROCKNIX](../../docs/rapports/ROCKNIX.md) §3). Sur la chaîne actuelle : `patch -p1 < hsfa_run-sysdir.diff`
  (décalage de 143 lignes) ; `git apply` le refuse.

## Construire

Chaîne vérifiée le 2026-10-24 depuis un arbre neuf au commit `af5d3f3` : les 17 patchs (16 plus le 11b)
s'appliquent sans erreur (un avertissement d'espace pour le patch 4), et l'arbre obtenu est identique, hors fichiers
générés, à l'arbre de référence `94c666a` (`git diff` vide). Les cœurs 4:3 et 16:9 se construisent.

```bash
git clone https://github.com/libretro/FBNeo.git && cd FBNeo && git checkout af5d3f3
P=<depot>/patches/fbneo
git apply $P/fbneo-hsfa.patch $P/fbneo-hsfa-widescreen.patch
for p in fbneo-hsfa-ws-flux.patch hyper-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch \
         0001-HSFA-rejeu-QSound-des-sons-SFA1-SFA2-d-Hyper-donnees.patch 0002-HSFA-chargement-differe-emplacement-4.patch \
         0003-HSFA-options-du-coeur.patch 0004-HSFA-stb_vorbis.patch 0005-HSFA-flux-musique-Ogg-Vorbis.patch \
         0006-HSFA-carte-musique.patch 0007-HSFA-roulette-touche-piece.patch \
         0007b-HSFA-hsfa_run-options-du-coeur-HSFA_VARS.patch 0008-HSFA-registres-des-plans-ro9a.patch \
         0009-HSFA-prototype-trous-carte-68K.patch 0010-HSFA-melange-des-objets-transparence.patch \
         0011-HSFA-option-ombres-transparentes-PSP.patch 0012-HSFA-16-9-format-remplir-la-hauteur.patch \
         0013-HSFA-pilote-sfa3umhsfa-Upper-MAX.patch \
         0014-HSFA-provocation-sur-Select-en-combat.patch; do
  git apply --exclude=gamelist.txt --exclude='src/dep/generated/*' $P/$p
done
cd src/burner/libretro
nice -n 19 make -j4 SUBSET=hsfa REGEN_HEADERS=1       # Linux x86_64 -> fbneo_hsfa_libretro.so (≈ 40 s)
nice -n 19 make SUBSET=hsfa clean
nice -n 19 make -j4 SUBSET=hsfaws REGEN_HEADERS=1     # 16:9 -> fbneo_hsfaws_libretro.so
```

- **Fichiers générés** (`gamelist.txt`, `src/dep/generated/*`) : seul le patch 4 en contient, faits sur un arbre
  déjà régénéré ; il faut les exclure. `REGEN_HEADERS=1` les refait, et c'est **obligatoire** : sans lui, la table
  des pilotes du `.so` ne connaît pas les pilotes ajoutés (`sfa3hahsfa` en dernier).
- **Avec `git am`** (historique propre) : `git apply` des patchs 1 à 3, `git apply --exclude=…` du patch 4, un
  commit, puis `git am` des patchs suivants (11b compris) sans exclusion. Vérifié le 2026-10-18 jusqu'au patch 13.
- **Android** (arm64-v8a, NDK r28c) : `ndk-build` ne régénère pas les en-têtes. Lancer d'abord
  `make SUBSET=hsfa generate-files` dans `src/burner/libretro`, puis
  `NDK=<ndk> FBNEO=<arbre> tools/android/build_android.sh <sortie>` (les deux cœurs).
- **ROCKNIX** (aarch64, glibc ≤ 2.38) : `FBNEO=<arbre> tools/rocknix/build.sh hsfa` (puis `hsfaws`).
- **Windows x64** (MinGW-w64, depuis Linux) : `tools/windows/build_win.sh <arbre> tous`.
- **Lanceur d'essai** : `gcc -O2 -Isrc/burner/libretro/libretro-common/include -o hsfa_run hsfa/hsfa_run.c -ldl -lm`.

### Contrôler le résultat

- Le md5 d'un cœur change d'une construction à l'autre : `libretro.o` contient le hash court du commit Git de l'arbre
  (`GITaf5d3f3` pour un arbre patché sans commit). Comparer donc les objets, ou le comportement.
- Comportement : `scripts/validation/nonreg_coeur.sh` (§162) avec `COEUR=<nouveau .so>` et `REF=<cœur de
  référence>` ; attendu `IDENTIQUE` pour SFA3, Upper et Hyper.
- **Depuis le patch 15**, les ombres sont transparentes par défaut : contre une référence plus ancienne, lancer avec
  `HSFA_OMBRES=0` (option coupée) ; sinon les captures diffèrent, et c'est voulu. Le patch 16 ne touche que le cœur
  16:9 (format Off par défaut) : le cœur 4:3 est identique à l'octet avec ou sans lui.
- Le 2026-10-24 (chaîne à 17 patchs, zips `livraison_v148`, cœur 4:3) :
  - `HSFA_OMBRES=0`, contre la référence `linux_hsfa_501aebd.so` (antérieure à 0010) : `IDENTIQUE` sur les trois jeux
    (30, 30 et 40 captures, journaux, rejeu, flux, WAV) ;
  - options par défaut, contre le cœur Linux de l'arbre de référence (construit le 2026-10-18 avec 0010-0011) :
    `IDENTIQUE` sur les trois jeux ;
  - options par défaut, contre `linux_hsfa_501aebd.so` : seules les captures diffèrent (journaux, rejeu, flux, WAV
    identiques).
  - le cœur 16:9 a été construit, mais pas passé en non-régression (vérifications du patch 16 :
    [TRANSPARENCE](../../docs/rapports/TRANSPARENCE.md) §13).
- Le 2026-10-18 (14 patchs) : 124 objets sur 126 identiques à l'octet à ceux de l'arbre de référence (les deux
  autres, `burn.o` et `libretro.o`, ne diffèrent que par la table des pilotes générée et le hash Git).
