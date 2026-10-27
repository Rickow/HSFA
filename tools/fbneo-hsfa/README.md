# Cœur libretro FBNeo « HSFA » : archives de jeu et notices

Pilotes `sfa3hsfa` (SFA3), `sfa3uhsfa` (SFA3 Upper) et `sfa3hhsfa` (Hyper), qui font tourner sans MAME ni scripts les
programmes 68000 retraduits depuis l'Anthology PS2 (journal §136, §139, §143-§146). Les **patchs** du cœur sont dans
[`patches/fbneo/`](../../patches/fbneo/README.md) ; l'architecture dans
[docs/architecture/coeur-fbneo.md](../../docs/architecture/coeur-fbneo.md). Ce dossier ne contient aucune donnée de jeu :

| Fichier | Contenu |
|---|---|
| `paquet_fbneo.py` | construit les archives `sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3hhsfa.zip` depuis le dossier de travail (données de l'utilisateur, jamais publiées) ; `HSFA_STRICT`, `SOURCE_DATE_EPOCH` |
| `paquet_fbneo.diff` | modification proposée par l'agent Hyper (historique, [FBNEO-HYPER](../../docs/rapports/FBNEO-HYPER.md)) |
| `LISEZMOI-coeur.md`, `LISEZMOI-hyper.md`, `LISEZMOI-widescreen.md` | notices d'installation livrées avec les cœurs (RetroArch Android) |

## Musique en Ogg Vorbis (zip d'Hyper ≈ 5 fois plus léger)

Les cœurs construits avec les patchs 8 et 9 lisent les flux ADX **et** Ogg Vorbis
([PLAN-VORBIS](../../docs/rapports/PLAN-VORBIS.md)). Pour construire le zip d'Hyper avec des flux Vorbis :

```bash
HSFA_YDATA=<Y_DATA.BIN ou ISO> HSFA_FLUX_FORMAT=ogg python3 paquet_fbneo.py hyper
```

- Demande ffmpeg (avec libvorbis), g++, gcc et numpy sur le PC qui construit les zips (pas sur la console).
- Le premier passage encode les 200 flux environ (quelques minutes, en parallèle) ; ils sont gardés dans
  `<work>/flux_ogg/` (`HSFA_OGG_CACHE`) et réutilisés tant que l'ADX et le réglage `HSFA_OGG_QUALITE` (défaut 2,
  ≈ 96 kbit/s) ne changent pas.
- Chaque flux est contrôlé (durée, boucle, corrélation, niveau) ; un flux qui échoue reste en ADX.
- **Hyper garde tous ses flux par défaut** (décision de l'utilisateur, 2026-10-16) : en Vorbis, retirer les flux
  ZERO 3 doublés par le QSound ne fait gagner que 27 Mo. `HSFA_FLUX_SANS_Q=1` réactive la phase 1 : omet les 36
  thèmes de stage et jingles ZERO 3 marqués `q` (rejoués en QSound), garde les 7 morceaux d'écran (flux `q` qui
  bouclent et durent au plus 25 s : `0002`, `0004`, `0005`, `0007`, `0008`, `002B`, `002C`, la version arcade ne
  rebouclant pas toujours comme la PS2) ; `HSFA_FLUX_ZERO3_GARDE="0004,..."` donne la liste à garder.
- Mesuré sur le zip réel (2026-10-16) : ADX 743 Mo ; **Vorbis par défaut (tous les flux) 201 Mo** ; avec
  `HSFA_FLUX_SANS_Q=1` 174 Mo ; sans aucun flux ZERO 3 172 Mo.
- Le zip ne contient que les flux qu'Hyper peut demander en jeu : 216 entrées de `Y_DATA.BIN` sur 588, celles des
  tables musique du 68K (`docs/rapports/SON-HYPER.md` §2.2). Les morceaux du seul lecteur de musique (sound test) et
  des autres modules de l'Anthology n'y sont pas.
- Un ancien cœur (sans les patchs 8 et 9) ne lit pas un zip Vorbis : les musiques concernées retombent sur le QSound
  ou se taisent. Mettre à jour le cœur avec le zip.

## Partitions ZERO / ZERO 2 (carte musique, Hyper)

Les cœurs construits avec le patch 10 jouent les musiques ZERO (SFA1) et ZERO 2 (SFA2) d'Hyper par leurs pilotes
son d'origine ([PLAN-PARTITIONS-HYPER](../../docs/rapports/PLAN-PARTITIONS-HYPER.md)) quand le zip contient la carte :

```bash
HSFA_YDATA=<ISO> HSFA_PARTITIONS=1 HSFA_FLUX_FORMAT=ogg python3 paquet_fbneo.py hyper
```

- Ajoute `hsfa_musique.bin` (programmes Z80 `e221` / `e250` de `X_DATA.BIN`, ≈ 0,6 Mo) et `hsfa_musique_table.txt`.
  Sources possibles : `HSFA_XDATA` / l'ISO, ou `HSFA_PILOTE_SFA1` / `HSFA_PILOTE_SFA2` (image Z80, ou zip arcade
  `sfa.zip` / `sfa2.zip`). Le programme est vérifié par sa chaîne de version (`1.05A`, `1.05C`).
- Les échantillons sont ceux du rejeu (`hsfa_rejeu.bin`) : rien d'autre à ajouter.
- Les flux ZERO / ZERO 2 restent dans le zip pour l'instant (repli, comparaison). Sur PC, `HSFA_MUSIQUE=0` coupe la
  carte (retour aux flux).
- Un état sauvegardé d'Hyper avec un cœur sans le patch 10 ne se rechargera probablement pas dans un cœur avec : l'état
  contient désormais un 2ᵉ Z80 et un bloc `HsfaMusique` (non vérifié, faute de zip d'Hyper dans la session cloud).

Installation résumée : [docs/guide/installation-android.md](../../docs/guide/installation-android.md) ;
ROCKNIX : [tools/rocknix](../rocknix/LISEZMOI-rocknix.md).
