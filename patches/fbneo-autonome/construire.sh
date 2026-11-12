#!/bin/bash
# construire.sh <depot_hsfa> <dossier_de_travail> [essai]
#
# FinalBurn Neo HSFA autonome pour Windows x64 (sans RetroArch), en compilation croisee MinGW-w64 depuis Linux.
#   1. FBNeo officiel (github.com/finalburnneo/FBNeo) au commit 84faab7 (2026-06-02) : c'est la base commune exacte
#      (merge-base) du libretro/FBNeo af5d3f3 sur lequel les patchs du depot sont faits ; src/burn y est identique.
#   2. Patchs du depot (patches/fbneo/, ordre du README : chaine 0001-0027 avec 0007b, 0021b, 0021c, puis 0029, 0030, 0031 et 0032),
#      parties src/burner/libretro et fichiers generes exclus.
#   3. Patchs Windows de ce dossier (W01-W06 de ce dossier ; E01, construction d essai, non versée, 3e argument « essai »).
#   4. Deux executables : fbneo64.exe (4:3, 384 x 224) et fbneo64ws.exe (16:9, 512 x 224, -DHSFA_WS) : le 16:9 est un
#      choix de compilation du coeur commun (comme les deux coeurs libretro fbneo_hsfa / fbneo_hsfaws).
# Besoins : git, perl, make, x86_64-w64-mingw32-gcc/g++/windres (posix), gcc hote ; environ 15 min par -j4 pour le
# premier executable (tous les pilotes de FBNeo), 1 min pour le second.
set -euo pipefail
DEP=$(readlink -f "${1:?usage : construire.sh <depot_hsfa> <dossier_de_travail> [essai]}")
T=$(readlink -f "${2:?dossier de travail}")
ESSAI=${3:-}
ICI=${HSFA_AUTONOME:-$(dirname "$(readlink -f "$0")")}   # dossier des patchs W01-W06 / E01 (par defaut : celui du script)
BASE=84faab702d785701d68b0fe22f90432c29916ff2
JOBS=${JOBS:-4}
P=$DEP/patches/fbneo

mkdir -p "$T"
if [ ! -d "$T/FBNeo/.git" ]; then
  git clone --filter=blob:none "${FBNEO_GIT:-https://github.com/finalburnneo/FBNeo.git}" "$T/FBNeo"
fi
cd "$T/FBNeo"
git checkout -q -f "$BASE"
git clean -q -fdx -e obj

# 2. chaine du depot (README de patches/fbneo), sans l'interface libretro
X=(--exclude='src/burner/libretro/*' --exclude='hsfa/*' --exclude=gamelist.txt --exclude='src/dep/generated/*')
for p in fbneo-hsfa.patch fbneo-hsfa-widescreen.patch fbneo-hsfa-ws-flux.patch \
         hyper-HSFA-pilote-sfa3hhsfa-Hyper-Street-Fighter-Alpha-mod.patch \
         0001-HSFA-rejeu-QSound-des-sons-SFA1-SFA2-d-Hyper-donnees.patch 0002-HSFA-chargement-differe-emplacement-4.patch \
         0003-HSFA-options-du-coeur.patch 0004-HSFA-stb_vorbis.patch 0005-HSFA-flux-musique-Ogg-Vorbis.patch \
         0006-HSFA-carte-musique.patch 0007-HSFA-roulette-touche-piece.patch \
         0007b-HSFA-hsfa_run-options-du-coeur-HSFA_VARS.patch 0008-HSFA-registres-des-plans-ro9a.patch \
         0009-HSFA-prototype-trous-carte-68K.patch 0010-HSFA-melange-des-objets-transparence.patch \
         0011-HSFA-option-ombres-transparentes-PSP.patch 0012-HSFA-16-9-format-remplir-la-hauteur.patch \
         0013-HSFA-pilote-sfa3umhsfa-Upper-MAX.patch 0014-HSFA-provocation-sur-Select-en-combat.patch \
         0015-HSFA-banque-commune-Upper-greffe-ro9a.patch 0016-HSFA-roulette-sur-piece-Upper.patch \
         0017-HSFA-bases-marquees-ciel-du-CONTINUE-ro9a.patch 0018-HSFA-option-sang-rouge-par-defaut.patch \
         0019-HSFA-option-saut-des-boucles-d-attente-68000.patch 0020-HSFA-saut-de-la-boucle-d-attente-du-Z80-QSound.patch \
         0021-HSFA-crochets-Z80-Musashi-et-FIR-QSound-plus-rapides.patch \
         0021b-HSFA-option-saut-des-boucles-d-attente-active-par-defaut.patch \
         0021c-libretro-Makefile-interrupteur-HSFA_NO_FLOAT_STORE.patch \
         0022-HSFA-16-9-512-px-bords-en-miroir.patch 0023-HSFA-16-9-vue-calee-sur-le-decor-HUD-fixe.patch \
         0024-HSFA-SFA3-tuiles-d-objets-en-miroir.patch 0025-HSFA-SFA3-tuiles-du-portage-hsfa_gfx-facultatif.patch \
         0026-HSFA-SFA3-tuiles-scroll3-du-portage.patch 0027-HSFA-publication-differee-des-objets.patch \
         0029-HSFA-etats-complets-et-deterministes.patch 0030-HSFA-dossier-systeme-chaine-large-Windows.patch \
         0031-HSFA-16-9-bords-raw-par-defaut.patch 0032-HSFA-zone-de-fin-d-etat-verifiee-avant-application.patch; do
  git apply "${X[@]}" "$P/$p"
done

# 3. interface Windows
for p in "$ICI"/W0*.patch; do git apply "$p"; done
MK=(RELEASEBUILD=1)
if [ "$ESSAI" = essai ]; then git apply "$ICI"/E01-*.patch; MK+=(HSFA_ESSAI=1); fi

# 4. constructions (nice 19)
nice -n 19 make -j"$JOBS" mingwcc64 "${MK[@]}"
rm -rf obj/51/6ws && cp -a obj/51/6 obj/51/6ws
rm -f obj/51/6ws/burn/drv/capcom/*.o obj/51/6ws/burner/win32/{hsfa_win32,menu,scrn,cona,main,wave}.o \
      obj/51/6ws/intf/video/vid_interface.o
nice -n 19 make -j"$JOBS" mingwcc64 "${MK[@]}" HSFA_WS=1 COMPILENAME=6ws NAME=fbneo64ws
ls -la fbneo64.exe fbneo64ws.exe
sha256sum fbneo64.exe fbneo64ws.exe
