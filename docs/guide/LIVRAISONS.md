# Registre des livraisons (archives de jeu et cœurs)

Ce registre dit **ce qui a été remis à l'utilisateur** : nom, md5, base, contenu. Il répond à la question « quel
cœur et quel zip sont en circulation ? » ([POINT-ETAPE-2026-10-21](../rapports/POINT-ETAPE-2026-10-21.md) §2.2).

- Les archives contiennent des données de jeu : elles ne sont **jamais** dans le dépôt. Seuls leurs noms et leurs md5
  sont ici. Chacun reconstruit les siennes depuis son ISO ([construction-iso.md](construction-iso.md)).
- Un md5 terminé par « … » est le seul connu (abrégé dans le registre d'origine).
- Le plus récent en haut. Une nouvelle livraison ajoute une ligne en tête du tableau concerné.
- « Patchs » renvoie à la chaîne de [`patches/fbneo/`](../../patches/fbneo/README.md) ; « v149 », « v150 » aux
  versions validées du traducteur (journal §162, §163).

## 1. Cœurs FBNeo « HSFA »

| date | objet | md5 | base | contenu |
|---|---|---|---|---|
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

## 3. Ce qui manque aux archives en circulation (2026-10-24)

| objet | base | correctifs manquants |
|---|---|---|
| Hyper (`sfa3hhsfa.zip`, 2026-10-11 et Ogg du 2026-10-16) | v148 | `PILE_LUI` (v149), `VRAM_TABLE` (v150), règles du §171 (v151) |
| Upper + MAX (2b15) | v150 (rebasé au lot 2b6 ; le point d'étape dit v149) | règles du §171 (v151) |
| SFA3, Upper (v148) | v148 | v149, v150, §171 |
| `ro9a` (`sfa3hahsfa.zip`) | `ro9a4_fige` | étapes 5 à 7 de la greffe ; voix d'Hyper non vérifiées |
| référence de `nonreg_coeur.sh` | `linux_hsfa_501aebd.so`, zips v148 | antérieure aux patchs 0010-0012 (comparer avec `HSFA_OMBRES=0`) |
