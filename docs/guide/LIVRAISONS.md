# Delivery register (game archives and cores)

**Français : [LIVRAISONS.fr.md](LIVRAISONS.fr.md)**

This register states **what was handed over to the user**: name, md5, base, contents. It answers the question "which
core and which zip are in circulation?" ([POINT-ETAPE-2026-10-21](../rapports/POINT-ETAPE-2026-10-21.md) §2.2).

- The archives contain game data: they are **never** in the repository. Only their names and their md5
  are here. Everyone rebuilds their own from their ISO ([construction-iso.md](construction-iso.md)).
- An md5 ending in "…" is the only one known (abbreviated in the original register).
- Most recent at the top. A new delivery adds a line at the top of the table concerned.
- **Detailed register (md5) stopped on 2026-10-24.** Since v0.1 (2026-10-27), the published cores and build
  package are on the releases page, with their checksums (`SHA256SUMS.txt`); journal §177 and
  following say what each release contains. §4 below sums up the cores of each release and the unpublished
  batches.
- "Patches" refers to the chain of [`patches/fbneo/`](../../patches/fbneo/README.md); "v149", "v150" to the
  validated versions of the translator (journal §162, §163).

## 1. FBNeo "HSFA" cores

| date | item | md5 | base | contents |
|---|---|---|---|---|
| 2026-11-12b | `hsfa-coeurs-2026-11-12b.zip` (62.8 MB) | `6bf00dee23eb141462c6de9fdcf5f745` | patches 0001-0027, 0029-0032 (+ 0007b, 0021b, 0021c) | 12 cores, 4:3 and 16:9; HSFA zone of the states checked before being applied (0032: damaged or zero-padded state loaded with no cut sound, no black frame and no crash); with no state loaded and with a valid state: identical to the batch of 12/11 frame by frame, sound and states byte for byte; standalone FinalBurn Neo (test, W01-W06: complete rewind and run-ahead) separately, zip `e5ff151c…` |
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
| 2026-11-12 | `hsfa-coeurs-2026-11-12.zip` (62.8 MB) | `5c1adaacb7ef1f39d3e051238adc7cf4` | patches 0001-0027, 0029-0031 (+ 0007b, 0021b, 0021c) | 12 cores, 4:3 and 16:9; 16:9: "Widescreen edges" = Raw by default (0031; stage-locked view as an option); 4:3 identical to 11/11 (except version); Batocera package `hsfa-batocera/` |
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
| 2026-11-11 | `hsfa-coeurs-2026-11-11.zip` (62.8 MB) | `28dd52b24388ffaf85278555314ccfd6` | patches 0001-0027, 0029 (+ 0007b, 0021b, 0021c) | 12 cores, 4:3 and 16:9; complete and deterministic savestates (run-ahead, rewind, netplay); Linux x86_64 compatible with glibc 2.27 (Batocera 43, older distributions); Batocera package `hsfa-batocera/` (x86_64, aarch64) |
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
| 2026-10-24 | `hsfa-coeurs-2026-10-24.zip` (33.2 MB) | `25d14861477ee016024072e892017b34` | patches 0001-0012 (16 + 11b) | Android, ROCKNIX, Windows, Linux; 4:3 and 16:9; new: 16:9 core option "Screen format (fill height)" |
| 2026-10-24 | ↳ `android/fbneo_hsfa_libretro_android.so` | `5f808114a6f2a5310db2c427844f6d54` | idem | Android arm64, 4:3 |
| 2026-10-24 | ↳ `android/fbneo_hsfaws_libretro_android.so` | `63764e03a65c88a74daa0063b09f491f` | idem | Android arm64, 16:9 |
| 2026-10-24 | ↳ `linux/fbneo_hsfa_libretro.so` | `0f5051c94f42b70452c3b1e443012790` | idem | Linux x86_64, 4:3 |
| 2026-10-24 | ↳ `linux/fbneo_hsfaws_libretro.so` | `12da7fad833e9dad3042eb4bc115471d` | idem | Linux x86_64, 16:9 |
| 2026-10-24 | ↳ `rocknix/fbneo_hsfa_libretro.so` | `c295ae32b126c98d9859230d6d62bc35` | idem | ROCKNIX aarch64, 4:3 |
| 2026-10-24 | ↳ `rocknix/fbneo_hsfaws_libretro.so` | `a1f1fec2f0733a0fdb7e76509da8697e` | idem | ROCKNIX aarch64, 16:9 |
| 2026-10-24 | ↳ `windows/fbneo_hsfa_libretro.dll` | `446c4511ee9a9cd3ebdca67edf6b0fec` | idem | Windows x64, 4:3 |
| 2026-10-24 | ↳ `windows/fbneo_hsfaws_libretro.dll` | `143ade812c5567e7bb335c7a0bf8b3d1` | idem | Windows x64, 16:9 |
| 2026-10-18 | `hsfa-coeurs-2026-10-18.zip` (31.7 MB) | `4a9ca08783be4e5a46e340aa84d1f093` | patches 0001-0011 (0010 v3) | 4 platforms, 4:3 and 16:9; PSP transparent shadows (default); object blending for the MAX characters; old states loadable |
| 2026-10-18 | ↳ `android/fbneo_hsfa_libretro_android.so` | `3bd1bf16c8a6e018ab8ce53dba23ff26` | idem | Android arm64, 4:3 |
| 2026-10-18 | ↳ `android/fbneo_hsfaws_libretro_android.so` | `57dd6dd6f0cfff1c19190437d94b52a0` | idem | Android arm64, 16:9 |
| 2026-10-18 | ↳ `linux/fbneo_hsfa_libretro.so` | `c493d2f6916fcfc357741b14ff6a1c34` | idem | Linux x86_64, 4:3 |
| 2026-10-18 | ↳ `linux/fbneo_hsfaws_libretro.so` | `dad31c659e563724342f58453cd661c3` | idem | Linux x86_64, 16:9 |
| 2026-10-18 | ↳ `rocknix/fbneo_hsfa_libretro.so` | `0f10ca3ef3407d717873386b60defe21` | idem | ROCKNIX aarch64, 4:3 |
| 2026-10-18 | ↳ `rocknix/fbneo_hsfaws_libretro.so` | `a0b4036b79bdb942b6955b142b88bffa` | idem | ROCKNIX aarch64, 16:9 |
| 2026-10-18 | ↳ `windows/fbneo_hsfa_libretro.dll` | `44918828826f6ae6209ca4d0d3f89604` | idem | Windows x64, 4:3 |
| 2026-10-18 | ↳ `windows/fbneo_hsfaws_libretro.dll` | `748f8573205a748d307998dbb109c8ff` | idem | Windows x64, 16:9 |
| 2026-10-16 | `hsfa-coeurs-2026-10-16b.zip` (24.1 MB) | not recorded | patches 1-11 (up to 0007) | cloud session: Android, ROCKNIX (+ `essai_son` kit), Windows; Vorbis, music map, roulette on Select (§157) |
| 2026-10-16 | ROCKNIX `fbneo_hsfa_libretro.so` / `fbneo_hsfaws_libretro.so` | `d17e80a8…` / `f5fce850…` | patches 1-10, `GITbdc9ef132` | 1st run under ARM emulation ([ROCKNIX](../rapports/ROCKNIX.md) §7) |
| 2026-10-11 | Android cores 4:3 / 16:9 | `d4d74a85…` / `57637fc8…` | patches 1-3 of the time (replay, portrait, options) | v148 delivery |
| 2026-10-11 | ROCKNIX cores 4:3 / 16:9 | `e9d039a9…` / `d595b78b…` | idem | v148 delivery |

## 2. Game archives

| date | item | md5 | base | contents |
|---|---|---|---|---|
| 2026-10-18 | `sfa3uhsfa.zip`, Upper + MAX, batch 2b15 | `e0a969d08b5e5576873e091da5971949` | Upper v150 + MAX | endings without magenta rectangles; vertical names on the world map; to be played with the cores of 18/10 or newer |
| 2026-10-18 | idem, batch 2b14 | `d8b01e6e06ea3bbce5453ad32deb2e00` | Upper v150 + MAX | bright MAX projectiles (bit 12) |
| 2026-10-18 | idem, batch 2b13 | `365a722ccd43a92fc0c1b264c2331436` | Upper v150 + MAX | bright MAX effects, 1st version |
| 2026-10-18 | idem, batch 2b13a | `bf432dc17e14f7fdbca82adbd067d062` | Upper v150 + MAX | Yun's and Ingrid's bios |
| 2026-10-18 | idem, batch 2b12 | `916e83961a8ddb2f02a61ed629c56660` | Upper v150 + MAX | WINNER of the MAX characters, stretched preview, endings with 30 palettes |
| 2026-10-18 | idem, batch 2b11 | `5d2cd2ea903a3cd3a8eb8bce339cdb1b` | Upper v150 + MAX | MAX characters stretched ×38/32 as on PSP |
| 2026-10-18 | idem, batch 2b10 | `b6babbf64d3d84a0dead8a4c2a96e96e` | Upper v150 + MAX | Maki (jumps, throws), victory eyes |
| 2026-10-18 | idem, batch 2b9 | `d2de0270f4cb8afcbd2922fd10f1a776` | Upper v150 + MAX | MAX endings, 1st version |
| 2026-10-18 | idem, batch 2b8 | `fbda23c628471485f9b2f83b37b5365b` | Upper v150 + MAX | Maki's run |
| 2026-10-18 | idem, batch 2b7 | `ea0ac9368e35e6bd3b69192c5bbd4126` | Upper v150 + MAX | Ingrid's counters, endings to the end |
| 2026-10-17 | idem, batch 2b6 | `cab8d235f691c14fac43b22d9eb11288` | Upper v150 + MAX | story screen of the 4 MAX characters; Cammy's stage complete |
| 2026-10-17 | idem, batch 2b5 | `f3f3ef8e7970934b022e71fa6c15ac2e` | Upper v149 + MAX | MAX shouts, victory portraits |
| 2026-10-17 | idem, batch 2b4 | `f8ffbdfec88e290fc5cb5f9d3a62947d` | idem | MAX sounds and voices |
| 2026-10-17 | idem, stage 2b | `855f8878cd858e7e1b93c197985aa0be` | Upper v149 (`7898814c`) + MAX | Eagle `$26`, Maki `$27`, Yun `$2D`, Ingrid `$2E` playable; without streams |
| 2026-10-16 | `sfa3hhsfa.zip`, Hyper in Ogg (201 MB) | not recorded | program of the v148 zip | cloud session: Ogg streams, Hyper's shouts and voices taken from the arcade |
| 2026-10-11 | `sfa3uhsfa_max.zip`, Upper + Eagle and Maki | `0b71207b…` | Upper v148 | first MAX trial |
| 2026-10-11 | `sfa3hsfa.zip` (SFA3), v148 | `500f7ec22b7e50c7cbf5e59a317faf84` | ROM `7e22b1ec…` | options, big A, step B |
| 2026-10-11 | `sfa3uhsfa.zip` (Upper), v148 | `f6c848ffbeea9e8024e5fb1d36cbc91e` | ROM `1908ec9e…` | idem, face-off portrait |
| 2026-10-11 | `sfa3hhsfa.zip` (Hyper, ADX, 743 MB), v148 | `56024e1c31fe896eebcbfe1b1c670d3b` | ROM `964943b1…` | ADX music, SFA1 / SFA2 replay |
| 2026-10-10 | `sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip`, v145 | `e193a2923c3c079b90f57dbc92dc8a61`, `7a5429a4026b1c6287ea6be4284b6cfb`, `e22f606035564f51d7a505f54a370c40` | v145 | Hyper fixed, SFA1 / SFA2 voices |

Built but **not recorded as delivered**: MAX batch 2b16 (`75ef6bea5f2dd28dc4c9402fb630d7f9`, CRC `606e7af4`,
ending actors v2); `ro9a` zip `sfa3hahsfa.zip` (built on `ro9a4_fige`, core trial).

## 3. What the archives in circulation on 2026-10-24 lacked (history)

Since v0.1, everyone rebuilds their games from their ISO with the release: this table only applies to the
archives of that time.

| item | base | missing fixes |
|---|---|---|
| Hyper (`sfa3hhsfa.zip`, 2026-10-11 and Ogg of 2026-10-16) | v148 | `PILE_LUI` (v149), `VRAM_TABLE` (v150), rules of §171 (v151) |
| Upper + MAX (2b15) | v150 (rebased at batch 2b6; the progress review says v149) | rules of §171 (v151) |
| SFA3, Upper (v148) | v148 | v149, v150, §171 |
| `ro9a` (`sfa3hahsfa.zip`) | `ro9a4_fige` | steps 5 to 7 of the graft; Hyper's voices not checked |
| reference of `nonreg_coeur.sh` | `linux_hsfa_501aebd.so`, v148 zips | earlier than patches 0010-0012 (compare with `HSFA_OMBRES=0`) |

## 4. Since 2026-10-24: release cores and unpublished batches

Published cores (base libretro/FBNeo `af5d3f3`; patches according to the notes of each release, dates according to the
[CHANGELOG](../../CHANGELOG.md)). Each release contains the core archives for Android, ROCKNIX, Windows, Linux and,
since v0.1.2, Recalbox; their SHA-256 sums are in the release's `SHA256SUMS.txt`.

| release | date | core patches | note |
|---|---|---|---|
| v0.1.10 (stable) | 2026-11-13 | 0001-0027, 0029-0032, 0007b | same cores as v0.1.9 (batch of 12/11b) |
| v0.1.9 (pre-release) | 2026-11-12 | 0001-0027, 0029-0032, 0007b | batch of 12/11b: complete savestates (0029, 0032), 16:9 Raw by default (0031); Linux core: glibc 2.27; Batocera |
| v0.1.8 (pre-release) | 2026-11-08 | 0001-0027, 0007b | 0027: objects with the arcade delay; Linux core: glibc 2.43 required |
| v0.1.7 (stable) | 2026-11-08 | 0001-0026, 0007b | all-in-one builder; Linux core: glibc 2.43 required |
| v0.1.6 | 2026-11-07 | 0001-0025, 0007b | tiles of the port in SFA3 (0025) |
| v0.1.5 | 2026-11-07 | 0001-0024, 0007b | true 16:9 |
| v0.1.4 | 2026-11-04 | 0001-0021c, 0007b | faster cores |
| v0.1.3 | 2026-11-03 | 0001-0018, 0007b | "Blood" option |
| v0.1.2 | 2026-11-02 | 0001-0017, 0007b | first Recalbox cores |
| v0.1.1 | 2026-10-28 | 0001-0014, 0007b | same cores as v0.1 |
| v0.1 | 2026-10-27 | 0001-0014, 0007b | first public release |

Core batches built in the workshop and not published as such (12 cores each, built by
[`tools/coeurs/`](../../tools/coeurs/README.md); folders `<workspace>/work/livraison_coeurs_<date>` when the journal
names them):

| batch | patches | source |
|---|---|---|
| 2026-11-07 | 0001-0024 (tree `590e367`) | journal §200 |
| 2026-11-08 | 0001-0025 | journal §201 |
| 2026-11-09 | 0001-0026, 0007b, 0021b, 0021c | [`patches/fbneo/README.md`](../../patches/fbneo/README.md) ("Construire") |
| 2026-11-10 | 0027 as well | journal §210, §211; Linux core: [`tools/linux/README.md`](../../tools/linux/README.md) |
| 2026-11-11 | 0029 as well (savestates); Linux core compatible with glibc 2.27; Batocera package; zip `28dd52b2…` (details in the table above) | [CHANGELOG](../../CHANGELOG.md) v0.1.9, [`tools/linux/`](../../tools/linux/README.md) |
| 2026-11-12 | 0030 and 0031 as well (16:9: "Widescreen edges" = Raw by default, stage-locked view as an option); zip `5c1adaac…` (details in the table above); standalone FinalBurn Neo (test, W01-W05) separately | [CHANGELOG](../../CHANGELOG.md) v0.1.9, [`patches/fbneo/README.md`](../../patches/fbneo/README.md) (patch 34) |
| 2026-11-12b | 0032 as well (HSFA zone of the states checked before being applied, bounded values); zip `6bf00dee…` (details in the table above); standalone FinalBurn Neo (test, W01-W06) separately | [CHANGELOG](../../CHANGELOG.md) v0.1.9, [`patches/fbneo/README.md`](../../patches/fbneo/README.md) (patch 35) |

Game archives: none has been delivered since v0.1; everyone builds them from their ISO, and the reference
fingerprints are in [construction-iso.md](construction-iso.md). The test zips of the graft (Hyper + Arcade) and of the
MAX batches have their CRC in the journal section that describes them.
