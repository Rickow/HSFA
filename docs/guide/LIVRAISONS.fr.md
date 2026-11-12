# Registre des livraisons (archives de jeu et cœurs)

**English: [LIVRAISONS.md](LIVRAISONS.md)**

Ce registre dit **ce qui a été remis à l'utilisateur** : nom, md5, base, contenu. Il répond à la question « quel
cœur et quel zip sont en circulation ? » ([POINT-ETAPE-2026-10-21](../rapports/POINT-ETAPE-2026-10-21.md) §2.2).

- Les archives contiennent des données de jeu : elles ne sont **jamais** dans le dépôt. Seuls leurs noms et leurs md5
  sont ici. Chacun reconstruit les siennes depuis son ISO ([construction-iso.fr.md](construction-iso.fr.md)).
- Un md5 terminé par « … » est le seul connu (abrégé dans le registre d'origine).
- Le plus récent en haut. Une nouvelle livraison ajoute une ligne en tête du tableau concerné.
- **Registre détaillé (md5) arrêté au 2026-10-24.** Depuis la v0.1 (2026-10-27), les cœurs et le paquet de
  construction publiés sont sur la page des releases, avec leurs sommes (`SHA256SUMS.txt`) ; les journaux §177 et
  suivants disent ce que chaque release contient. Le §4 ci-dessous résume les cœurs de chaque release et les lots
  non publiés.
- « Patchs » renvoie à la chaîne de [`patches/fbneo/`](../../patches/fbneo/README.fr.md) ; « v149 », « v150 » aux
  versions validées du traducteur (journal §162, §163).

## 1. Cœurs FBNeo « HSFA »

| date | objet | md5 | base | contenu |
|---|---|---|---|---|
| 2026-11-12b | `hsfa-coeurs-2026-11-12b.zip` (62,8 Mo) | `6bf00dee23eb141462c6de9fdcf5f745` | patchs 0001-0027, 0029-0032 (+ 0007b, 0021b, 0021c) | 12 cœurs, 4:3 et 16:9 ; zone HSFA des états vérifiée avant d'être appliquée (0032 : état abîmé ou complété de zéros chargé sans son coupé ni image noire ni plantage) ; sans état chargé et avec un état valide : identiques au lot du 12/11 image par image, son et états à l'octet ; FinalBurn Neo autonome (essai, W01-W06 : rembobinage et run-ahead complets) à part, zip `e5ff151c…` |
| 2026-11-12b | ↳ `android/fbneo_hsfa_libretro_android.so` | `d33e61f90d268d4d4aa5260b3d513cdf` | idem | Android arm64, 4:3 |
| 2026-11-12b | ↳ `android/fbneo_hsfaws_libretro_android.so` | `ba33d6fc8f9fe65b5ffde454eb2033eb` | idem | Android arm64, 16:9 |
| 2026-11-12b | ↳ `linux/fbneo_hsfa_libretro.so` | `b9cb53e3f64331aaf87ad8a175dc14f8` | idem | Linux x86_64 (glibc ≤ 2.27), 4:3 |
| 2026-11-12b | ↳ `linux/fbneo_hsfaws_libretro.so` | `4ac1f5b35ae43a8317a5759af641715b` | idem | Linux x86_64 (glibc ≤ 2.27), 16:9 |
| 2026-11-12b | ↳ `rocknix/fbneo_hsfa_libretro.so` | `33e416a6cc09529e93ff85ad783aa33d` | idem | ROCKNIX aarch64, 4:3 |
| 2026-11-12b | ↳ `rocknix/fbneo_hsfaws_libretro.so` | `8fcf508165e07a8a3d6c21fa9fa8f4fb` | idem | ROCKNIX aarch64, 16:9 |
| 2026-11-12b | ↳ `windows/fbneo_hsfa_libretro.dll` | `681652a65106d235f48c3d44cb8d2294` | idem | Windows x64, 4:3 |
| 2026-11-12b | ↳ `windows/fbneo_hsfaws_libretro.dll` | `50704cff5fd8ebd69ac54f6d8332f78c` | idem | Windows x64, 16:9 |
| 2026-11-12b | ↳ `recalbox/armhf/fbneo_hsfa_libretro.so` | `54be38759d32e6c669e13a54601f5700` | idem | Recalbox armhf (Pi 3), 4:3 |
| 2026-11-12b | ↳ `recalbox/armhf/fbneo_hsfaws_libretro.so` | `1cac150aec4a9410a6275d3644c632fe` | idem | Recalbox armhf (Pi 3), 16:9 |
| 2026-11-12b | ↳ `recalbox/aarch64/fbneo_hsfa_libretro.so` | `1e35fcbab63261527479f0a73ad21a52` | idem | Recalbox / Batocera aarch64, 4:3 |
| 2026-11-12b | ↳ `recalbox/aarch64/fbneo_hsfaws_libretro.so` | `2bed050c056aac09c6079728972bec60` | idem | Recalbox / Batocera aarch64, 16:9 |
| 2026-11-12 | `hsfa-coeurs-2026-11-12.zip` (62,8 Mo) | `5c1adaacb7ef1f39d3e051238adc7cf4` | patchs 0001-0027, 0029-0031 (+ 0007b, 0021b, 0021c) | 12 cœurs, 4:3 et 16:9 ; 16:9 : « Widescreen edges » = Raw par défaut (0031 ; vue calée en option) ; 4:3 identiques au 11/11 (hors version) ; paquet Batocera `hsfa-batocera/` |
| 2026-11-12 | ↳ `android/fbneo_hsfa_libretro_android.so` | `0ac296a697020a3a0fe78c45f0f77c3a` | idem | Android arm64, 4:3 |
| 2026-11-12 | ↳ `android/fbneo_hsfaws_libretro_android.so` | `81b900033427b98fcea15a710218fb75` | idem | Android arm64, 16:9 |
| 2026-11-12 | ↳ `linux/fbneo_hsfa_libretro.so` | `deb35b0d862c38a4bc6e9a37040348b5` | idem | Linux x86_64 (glibc ≤ 2.27), 4:3 |
| 2026-11-12 | ↳ `linux/fbneo_hsfaws_libretro.so` | `f609e6e9fd985a59ae8ddb1cb9a541e4` | idem | Linux x86_64 (glibc ≤ 2.27), 16:9 |
| 2026-11-12 | ↳ `rocknix/fbneo_hsfa_libretro.so` | `552b3efbff8425a24490b02ec4a90467` | idem | ROCKNIX aarch64, 4:3 |
| 2026-11-12 | ↳ `rocknix/fbneo_hsfaws_libretro.so` | `f8841f3a0b879388806be4628dd07ad4` | idem | ROCKNIX aarch64, 16:9 |
| 2026-11-12 | ↳ `windows/fbneo_hsfa_libretro.dll` | `ec46f4a872a0941d6ed3a9e54f1958f3` | idem | Windows x64, 4:3 |
| 2026-11-12 | ↳ `windows/fbneo_hsfaws_libretro.dll` | `f2e6be23797f049cd48253e93718bc57` | idem | Windows x64, 16:9 |
| 2026-11-12 | ↳ `recalbox/armhf/fbneo_hsfa_libretro.so` | `da38bb0a96bf865bbf9ea58d3208e475` | idem | Recalbox armhf (Pi 3), 4:3 |
| 2026-11-12 | ↳ `recalbox/armhf/fbneo_hsfaws_libretro.so` | `e235f90aee049eefcdf99ed7598d43a2` | idem | Recalbox armhf (Pi 3), 16:9 |
| 2026-11-12 | ↳ `recalbox/aarch64/fbneo_hsfa_libretro.so` | `9f15a4a417fe2822ea171e94932a8f5e` | idem | Recalbox / Batocera aarch64, 4:3 |
| 2026-11-12 | ↳ `recalbox/aarch64/fbneo_hsfaws_libretro.so` | `238cba87fce6d25e00776dd96bbacc85` | idem | Recalbox / Batocera aarch64, 16:9 |
| 2026-11-11 | `hsfa-coeurs-2026-11-11.zip` (62,8 Mo) | `28dd52b24388ffaf85278555314ccfd6` | patchs 0001-0027, 0029 (+ 0007b, 0021b, 0021c) | 12 cœurs, 4:3 et 16:9 ; sauvegardes d'état complètes et déterministes (run-ahead, rembobinage, jeu en ligne) ; Linux x86_64 compatible glibc 2.27 (Batocera 43, distributions anciennes) ; paquet Batocera `hsfa-batocera/` (x86_64, aarch64) |
| 2026-11-11 | ↳ `android/fbneo_hsfa_libretro_android.so` | `4583b90e0bd2820c31e2423886868139` | idem | Android arm64, 4:3 |
| 2026-11-11 | ↳ `android/fbneo_hsfaws_libretro_android.so` | `25e9d2ebb6a5bfa089bf7082d94b04e2` | idem | Android arm64, 16:9 |
| 2026-11-11 | ↳ `linux/fbneo_hsfa_libretro.so` | `ad24a37b89eef8396072818c08450ac5` | idem | Linux x86_64 (glibc ≤ 2.27), 4:3 |
| 2026-11-11 | ↳ `linux/fbneo_hsfaws_libretro.so` | `57a445f52d8fbff2ec9742422c9282d0` | idem | Linux x86_64 (glibc ≤ 2.27), 16:9 |
| 2026-11-11 | ↳ `rocknix/fbneo_hsfa_libretro.so` | `02d4da35952b9a8a23e1348798f66668` | idem | ROCKNIX aarch64, 4:3 |
| 2026-11-11 | ↳ `rocknix/fbneo_hsfaws_libretro.so` | `c2c7ed5f3b1371c34b4d7dff3a0e88bf` | idem | ROCKNIX aarch64, 16:9 |
| 2026-11-11 | ↳ `windows/fbneo_hsfa_libretro.dll` | `0a7228eec3d33c45cb0960c38c0170ae` | idem | Windows x64, 4:3 |
| 2026-11-11 | ↳ `windows/fbneo_hsfaws_libretro.dll` | `5d76931147c396df6f0b22da912cbc19` | idem | Windows x64, 16:9 |
| 2026-11-11 | ↳ `recalbox/armhf/fbneo_hsfa_libretro.so` | `731df293c2f26913ad9a4db40c503700` | idem | Recalbox armhf (Pi 3), 4:3 |
| 2026-11-11 | ↳ `recalbox/armhf/fbneo_hsfaws_libretro.so` | `39ac370871289239e5fb2e2bbc2ec243` | idem | Recalbox armhf (Pi 3), 16:9 |
| 2026-11-11 | ↳ `recalbox/aarch64/fbneo_hsfa_libretro.so` | `4ca78f4711d45d1edd94ddf8a8114128` | idem | Recalbox / Batocera aarch64, 4:3 |
| 2026-11-11 | ↳ `recalbox/aarch64/fbneo_hsfaws_libretro.so` | `730c4436e72971019014645fdf47a135` | idem | Recalbox / Batocera aarch64, 16:9 |
| 2026-10-24 | `hsfa-coeurs-2026-10-24.zip` (33,2 Mo) | `25d14861477ee016024072e892017b34` | patchs 0001-0012 (16 + 11b) | Android, ROCKNIX, Windows, Linux ; 4:3 et 16:9 ; nouveau : option du cœur 16:9 « Screen format (fill height) » |
| 2026-10-24 | ↳ `android/fbneo_hsfa_libretro_android.so` | `5f808114a6f2a5310db2c427844f6d54` | idem | Android arm64, 4:3 |
| 2026-10-24 | ↳ `android/fbneo_hsfaws_libretro_android.so` | `63764e03a65c88a74daa0063b09f491f` | idem | Android arm64, 16:9 |
| 2026-10-24 | ↳ `linux/fbneo_hsfa_libretro.so` | `0f5051c94f42b70452c3b1e443012790` | idem | Linux x86_64, 4:3 |
| 2026-10-24 | ↳ `linux/fbneo_hsfaws_libretro.so` | `12da7fad833e9dad3042eb4bc115471d` | idem | Linux x86_64, 16:9 |
| 2026-10-24 | ↳ `rocknix/fbneo_hsfa_libretro.so` | `c295ae32b126c98d9859230d6d62bc35` | idem | ROCKNIX aarch64, 4:3 |
| 2026-10-24 | ↳ `rocknix/fbneo_hsfaws_libretro.so` | `a1f1fec2f0733a0fdb7e76509da8697e` | idem | ROCKNIX aarch64, 16:9 |
| 2026-10-24 | ↳ `windows/fbneo_hsfa_libretro.dll` | `446c4511ee9a9cd3ebdca67edf6b0fec` | idem | Windows x64, 4:3 |
| 2026-10-24 | ↳ `windows/fbneo_hsfaws_libretro.dll` | `143ade812c5567e7bb335c7a0bf8b3d1` | idem | Windows x64, 16:9 |
| 2026-10-18 | `hsfa-coeurs-2026-10-18.zip` (31,7 Mo) | `4a9ca08783be4e5a46e340aa84d1f093` | patchs 0001-0011 (0010 v3) | 4 plates-formes, 4:3 et 16:9 ; ombres transparentes PSP (par défaut) ; mélange des objets pour les MAX ; anciens états rechargeables |
| 2026-10-18 | ↳ `android/fbneo_hsfa_libretro_android.so` | `3bd1bf16c8a6e018ab8ce53dba23ff26` | idem | Android arm64, 4:3 |
| 2026-10-18 | ↳ `android/fbneo_hsfaws_libretro_android.so` | `57dd6dd6f0cfff1c19190437d94b52a0` | idem | Android arm64, 16:9 |
| 2026-10-18 | ↳ `linux/fbneo_hsfa_libretro.so` | `c493d2f6916fcfc357741b14ff6a1c34` | idem | Linux x86_64, 4:3 |
| 2026-10-18 | ↳ `linux/fbneo_hsfaws_libretro.so` | `dad31c659e563724342f58453cd661c3` | idem | Linux x86_64, 16:9 |
| 2026-10-18 | ↳ `rocknix/fbneo_hsfa_libretro.so` | `0f10ca3ef3407d717873386b60defe21` | idem | ROCKNIX aarch64, 4:3 |
| 2026-10-18 | ↳ `rocknix/fbneo_hsfaws_libretro.so` | `a0b4036b79bdb942b6955b142b88bffa` | idem | ROCKNIX aarch64, 16:9 |
| 2026-10-18 | ↳ `windows/fbneo_hsfa_libretro.dll` | `44918828826f6ae6209ca4d0d3f89604` | idem | Windows x64, 4:3 |
| 2026-10-18 | ↳ `windows/fbneo_hsfaws_libretro.dll` | `748f8573205a748d307998dbb109c8ff` | idem | Windows x64, 16:9 |
| 2026-10-16 | `hsfa-coeurs-2026-10-16b.zip` (24,1 Mo) | non relevé | patchs 1-11 (jusqu'à 0007) | session cloud : Android, ROCKNIX (+ kit `essai_son`), Windows ; Vorbis, carte musique, roulette sur Select (§157) |
| 2026-10-16 | ROCKNIX `fbneo_hsfa_libretro.so` / `fbneo_hsfaws_libretro.so` | `d17e80a8…` / `f5fce850…` | patchs 1-10, `GITbdc9ef132` | 1ʳᵉ exécution sous émulation ARM ([ROCKNIX](../rapports/ROCKNIX.md) §7) |
| 2026-10-11 | cœurs Android 4:3 / 16:9 | `d4d74a85…` / `57637fc8…` | patchs 1-3 de l'époque (rejeu, portrait, options) | livraison v148 |
| 2026-10-11 | cœurs ROCKNIX 4:3 / 16:9 | `e9d039a9…` / `d595b78b…` | idem | livraison v148 |

## 2. Archives de jeu

| date | objet | md5 | base | contenu |
|---|---|---|---|---|
| 2026-10-18 | `sfa3uhsfa.zip`, Upper + MAX, lot 2b15 | `e0a969d08b5e5576873e091da5971949` | Upper v150 + MAX | fins sans rectangles magenta ; noms verticaux de la carte du monde ; à jouer avec les cœurs du 18/10 ou plus récents |
| 2026-10-18 | idem, lot 2b14 | `d8b01e6e06ea3bbce5453ad32deb2e00` | Upper v150 + MAX | tirs MAX lumineux (bit 12) |
| 2026-10-18 | idem, lot 2b13 | `365a722ccd43a92fc0c1b264c2331436` | Upper v150 + MAX | effets MAX lumineux, 1ʳᵉ version |
| 2026-10-18 | idem, lot 2b13a | `bf432dc17e14f7fdbca82adbd067d062` | Upper v150 + MAX | bio de Yun et d'Ingrid |
| 2026-10-18 | idem, lot 2b12 | `916e83961a8ddb2f02a61ed629c56660` | Upper v150 + MAX | WINNER des MAX, aperçu étiré, fins à 30 palettes |
| 2026-10-18 | idem, lot 2b11 | `5d2cd2ea903a3cd3a8eb8bce339cdb1b` | Upper v150 + MAX | persos MAX étirés ×38/32 comme sur PSP |
| 2026-10-18 | idem, lot 2b10 | `b6babbf64d3d84a0dead8a4c2a96e96e` | Upper v150 + MAX | Maki (sauts, projections), yeux de victoire |
| 2026-10-18 | idem, lot 2b9 | `d2de0270f4cb8afcbd2922fd10f1a776` | Upper v150 + MAX | fins MAX, 1ʳᵉ version |
| 2026-10-18 | idem, lot 2b8 | `fbda23c628471485f9b2f83b37b5365b` | Upper v150 + MAX | course de Maki |
| 2026-10-18 | idem, lot 2b7 | `ea0ac9368e35e6bd3b69192c5bbd4126` | Upper v150 + MAX | contres d'Ingrid, fins jusqu'au bout |
| 2026-10-17 | idem, lot 2b6 | `cab8d235f691c14fac43b22d9eb11288` | Upper v150 + MAX | écran d'histoire des 4 MAX ; décor de Cammy complet |
| 2026-10-17 | idem, lot 2b5 | `f3f3ef8e7970934b022e71fa6c15ac2e` | Upper v149 + MAX | cris MAX, portraits de victoire |
| 2026-10-17 | idem, lot 2b4 | `f8ffbdfec88e290fc5cb5f9d3a62947d` | idem | sons et voix MAX |
| 2026-10-17 | idem, palier 2b | `855f8878cd858e7e1b93c197985aa0be` | Upper v149 (`7898814c`) + MAX | Eagle `$26`, Maki `$27`, Yun `$2D`, Ingrid `$2E` jouables ; sans flux |
| 2026-10-16 | `sfa3hhsfa.zip`, Hyper en Ogg (201 Mo) | non relevé | programme du zip v148 | session cloud : flux Ogg, cris et voix d'Hyper pris sur l'arcade |
| 2026-10-11 | `sfa3uhsfa_max.zip`, Upper + Eagle et Maki | `0b71207b…` | Upper v148 | premier essai MAX |
| 2026-10-11 | `sfa3hsfa.zip` (SFA3), v148 | `500f7ec22b7e50c7cbf5e59a317faf84` | ROM `7e22b1ec…` | options, gros A, étape B |
| 2026-10-11 | `sfa3uhsfa.zip` (Upper), v148 | `f6c848ffbeea9e8024e5fb1d36cbc91e` | ROM `1908ec9e…` | idem, portrait du face-à-face |
| 2026-10-11 | `sfa3hhsfa.zip` (Hyper, ADX, 743 Mo), v148 | `56024e1c31fe896eebcbfe1b1c670d3b` | ROM `964943b1…` | musique ADX, rejeu SFA1 / SFA2 |
| 2026-10-10 | `sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip`, v145 | `e193a2923c3c079b90f57dbc92dc8a61`, `7a5429a4026b1c6287ea6be4284b6cfb`, `e22f606035564f51d7a505f54a370c40` | v145 | Hyper corrigé, voix SFA1 / SFA2 |

Construits mais **pas enregistrés comme livrés** : lot MAX 2b16 (`75ef6bea5f2dd28dc4c9402fb630d7f9`, CRC `606e7af4`,
acteurs de fin v2) ; zip `ro9a` `sfa3hahsfa.zip` (construit sur `ro9a4_fige`, essai du cœur).

## 3. Ce qui manquait aux archives en circulation le 2026-10-24 (historique)

Depuis la v0.1, chacun reconstruit ses jeux depuis son ISO avec la release : ce tableau ne vaut plus que pour les
archives de cette époque.

| objet | base | correctifs manquants |
|---|---|---|
| Hyper (`sfa3hhsfa.zip`, 2026-10-11 et Ogg du 2026-10-16) | v148 | `PILE_LUI` (v149), `VRAM_TABLE` (v150), règles du §171 (v151) |
| Upper + MAX (2b15) | v150 (rebasé au lot 2b6 ; le point d'étape dit v149) | règles du §171 (v151) |
| SFA3, Upper (v148) | v148 | v149, v150, §171 |
| `ro9a` (`sfa3hahsfa.zip`) | `ro9a4_fige` | étapes 5 à 7 de la greffe ; voix d'Hyper non vérifiées |
| référence de `nonreg_coeur.sh` | `linux_hsfa_501aebd.so`, zips v148 | antérieure aux patchs 0010-0012 (comparer avec `HSFA_OMBRES=0`) |

## 4. Depuis le 2026-10-24 : cœurs des releases et lots non publiés

Cœurs publiés (base libretro/FBNeo `af5d3f3` ; patchs d'après les notes de chaque release, dates d'après le
[CHANGELOG](../../CHANGELOG.md)). Chaque release contient les archives de cœurs Android, ROCKNIX, Windows, Linux et,
depuis la v0.1.2, Recalbox ; leurs SHA-256 sont dans `SHA256SUMS.txt` de la release.

| release | date | patchs du cœur | remarque |
|---|---|---|---|
| v0.1.8 (pré-version) | 2026-11-08 | 0001-0027, 0007b | 0027 : objets au délai de l'arcade ; cœur Linux : glibc 2.43 exigée |
| v0.1.7 (stable) | 2026-11-08 | 0001-0026, 0007b | constructeur tout-en-un ; cœur Linux : glibc 2.43 exigée |
| v0.1.6 | 2026-11-07 | 0001-0025, 0007b | tuiles du portage dans SFA3 (0025) |
| v0.1.5 | 2026-11-07 | 0001-0024, 0007b | vrai 16:9 |
| v0.1.4 | 2026-11-04 | 0001-0021c, 0007b | cœurs plus rapides |
| v0.1.3 | 2026-11-03 | 0001-0018, 0007b | option « Blood » |
| v0.1.2 | 2026-11-02 | 0001-0017, 0007b | premiers cœurs Recalbox |
| v0.1.1 | 2026-10-28 | 0001-0014, 0007b | mêmes cœurs que la v0.1 |
| v0.1 | 2026-10-27 | 0001-0014, 0007b | première release publique |

Lots de cœurs construits à l'atelier et non publiés tels quels (12 cœurs chacun, construits par
[`tools/coeurs/`](../../tools/coeurs/README.md) ; dossiers `<workspace>/work/livraison_coeurs_<date>` quand le journal
les nomme) :

| lot | patchs | source |
|---|---|---|
| 2026-11-07 | 0001-0024 (arbre `590e367`) | journal §200 |
| 2026-11-08 | 0001-0025 | journal §201 |
| 2026-11-09 | 0001-0026, 0007b, 0021b, 0021c | [`patches/fbneo/README.md`](../../patches/fbneo/README.fr.md) (« Construire ») |
| 2026-11-10 | 0027 en plus | journal §210, §211 ; cœur Linux : [`tools/linux/README.md`](../../tools/linux/README.md) |
| 2026-11-11 | 0029 en plus (sauvegardes d'état) ; cœur Linux compatible glibc 2.27 ; paquet Batocera ; zip `28dd52b2…` (détail au tableau ci-dessus) | [CHANGELOG](../../CHANGELOG.md) « En cours », [`tools/linux/`](../../tools/linux/README.md) |
| 2026-11-12 | 0030 et 0031 en plus (16:9 : « Widescreen edges » = Raw par défaut, vue calée en option) ; zip `5c1adaac…` (détail au tableau ci-dessus) ; FinalBurn Neo autonome (essai, W01-W05) à part | [CHANGELOG](../../CHANGELOG.md) « En cours », [`patches/fbneo/README.md`](../../patches/fbneo/README.fr.md) (patch 34) |
| 2026-11-12b | 0032 en plus (zone HSFA des états vérifiée avant d'être appliquée, valeurs bornées) ; zip `6bf00dee…` (détail au tableau ci-dessus) ; FinalBurn Neo autonome (essai, W01-W06) à part | [CHANGELOG](../../CHANGELOG.md) « En cours », [`patches/fbneo/README.md`](../../patches/fbneo/README.fr.md) (patch 35) |

Archives de jeu : plus aucune n'est livrée depuis la v0.1 ; chacun les construit depuis son ISO, et les empreintes de
référence sont dans [construction-iso.fr.md](construction-iso.fr.md). Les zips d'essai de la greffe (Hyper + Arcade) et des
lots MAX ont leur CRC dans la section du journal qui les décrit.
