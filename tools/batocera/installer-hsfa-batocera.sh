#!/bin/bash
# Installe (ou retire) les coeurs FBNeo HSFA sur Batocera v43 ou plus. A lancer en SSH (ou dans le terminal), depuis
# le dossier livre copie sur le partage, par exemple :
#   bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh            -> installe ou reinstalle
#   bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh retirer    -> retire tout ce que l'installeur a pose
#
# Ce qu'il fait (rien d'autre) :
#   - choisit les coeurs x86_64 ou aarch64 selon la machine et verifie la glibc (2.27 au moins) ;
#   - range les coeurs et leurs .info dans /userdata/system/hsfa/ (partition des donnees, conservee) ;
#   - installe le service /userdata/system/services/hsfa et l'active : a chaque demarrage il recopie les coeurs dans
#     /usr/lib/libretro (le systeme de Batocera est en lecture seule et refait a chaque demarrage ; un service
#     survit aux redemarrages et aux mises a jour, contrairement a batocera-save-overlay) ;
#   - pose /userdata/system/configs/emulationstation/es_systems_hsfa.cfg (systeme « hsfa ») ;
#   - ecrit hsfa.emulator=libretro, hsfa.core=fbneo_hsfa et hsfa.bezel=none dans batocera.conf s'ils n'y sont pas
#     (sans « bezel=none », le decor 4:3 de Batocera ecrase l'image du coeur 16:9) ;
#   - cree /userdata/roms/hsfa/ et y met gamelist.xml s'il n'y en a pas.
# Il ne touche ni aux jeux, ni aux sauvegardes, ni aux autres systemes. Il ne remplace jamais un fichier a vous sans
# en garder une copie (*.avant-hsfa).
set -u
D=$(cd "$(dirname "$0")" && pwd)
H=/userdata/system/hsfa
SERV=/userdata/system/services/hsfa
ESCFG=/userdata/system/configs/emulationstation/es_systems_hsfa.cfg
ROMS=/userdata/roms/hsfa
NOTE=$H/installe-par-hsfa.txt
CORES="fbneo_hsfa fbneo_hsfaws"

reglage_get() { /usr/bin/batocera-settings-get "$1" 2>/dev/null; }
reglage_set() { /usr/bin/batocera-settings-set "$1" "$2"; }

if [ "${1:-}" = "retirer" ]; then
  if [ -f "$SERV" ]; then
    batocera-services stop hsfa >/dev/null 2>&1 || bash "$SERV" stop
    batocera-services disable hsfa >/dev/null 2>&1 || true
    rm -f "$SERV"; echo "retire : service $SERV (et coeurs de /usr/lib/libretro)"
  fi
  for c in $CORES; do rm -f "/usr/lib/libretro/${c}_libretro.so" "/usr/share/libretro/info/${c}_libretro.info"; done
  if [ -f "$ESCFG" ]; then
    rm -f "$ESCFG"; echo "retire : $ESCFG"
    [ -f "$ESCFG.avant-hsfa" ] && mv -f "$ESCFG.avant-hsfa" "$ESCFG" && echo "remis : votre ancien $ESCFG"
  fi
  # tous les reglages du systeme « hsfa » (hsfa.xxx et hsfa["jeu.zip"].xxx) : sans le systeme, ils ne servent plus
  if grep -qE '^hsfa(\.|\[)' /userdata/system/batocera.conf 2>/dev/null; then
    cp -f /userdata/system/batocera.conf /userdata/system/batocera.conf.avant-retrait-hsfa
    grep -E '^hsfa(\.|\[)' /userdata/system/batocera.conf | sed 's/^/retire de batocera.conf : /'
    sed -i -E '/^hsfa(\.|\[)/d' /userdata/system/batocera.conf
    echo "(copie de l'ancien fichier : /userdata/system/batocera.conf.avant-retrait-hsfa)"
  fi
  rm -rf "$H"
  rmdir /userdata/system/services 2>/dev/null || true
  echo "Fini. Les jeux de $ROMS et les sauvegardes sont gardes (supprimez $ROMS a la main si vous le voulez)."
  echo "Relancez l'interface : Menu > Quitter > Redemarrer (ou : batocera-es-swissknife --restart)."
  exit 0
fi

case $(uname -m) in
  x86_64)              A=x86_64;  GMIN=2.27 ;;
  aarch64|arm64)       A=aarch64; GMIN=2.27 ;;
  armv6l|armv7l|armv8l|armhf)
     echo "Batocera ARM 32 bits ($(uname -m) : Raspberry Pi 0/1/2, Odroid XU4...) : pas de coeur HSFA pour ces machines."
     echo "Le coeur armhf du lot Recalbox utilise des instructions ARMv8 (Pi 3) absentes de ces processeurs."; exit 1 ;;
  *) echo "Architecture $(uname -m) non prevue (x86_64 ou aarch64)."; exit 1 ;;
esac
V=$( (ldd --version 2>/dev/null || /lib/libc.so.6 2>/dev/null) | head -1 | grep -o '[0-9]\+\.[0-9]\+' | tail -1)
echo "Machine : $(uname -m) -> coeurs $A ; glibc : ${V:-inconnue} (il faut $GMIN ou plus)"
if [ -n "$V" ]; then
  if [ "$(printf '%s\n%s\n' "$V" "$GMIN" | sort -V | head -1)" != "$GMIN" ]; then
    echo "glibc $V trop ancienne ($GMIN au moins)."; exit 1
  fi
fi
for c in $CORES; do
  [ -f "$D/$A/${c}_libretro.so" ] || { echo "Fichier manquant : $D/$A/${c}_libretro.so"; exit 1; }
  [ -f "$D/${c}_libretro.info" ] || { echo "Fichier manquant : $D/${c}_libretro.info"; exit 1; }
done
for f in hsfa es_systems_hsfa.cfg gamelist.xml; do
  [ -f "$D/$f" ] || { echo "Fichier manquant : $D/$f"; exit 1; }
done

# 1. coeurs et .info gardes sur la partition des donnees
mkdir -p "$H/cores" "$H/info"
for c in $CORES; do
  install -m 644 "$D/$A/${c}_libretro.so" "$H/cores/${c}_libretro.so"
  install -m 644 "$D/${c}_libretro.info" "$H/info/${c}_libretro.info"
done
echo "installe : $H/cores (coeurs $A) et $H/info"
[ -f "$NOTE" ] || echo "# fichiers et reglages poses par installer-hsfa-batocera.sh (sert a « retirer »)" > "$NOTE"

# 2. service lance a chaque demarrage, active puis demarre tout de suite
mkdir -p "$(dirname "$SERV")"
install -m 755 "$D/hsfa" "$SERV"
batocera-services enable hsfa >/dev/null 2>&1 || echo "ATTENTION : « batocera-services enable hsfa » a echoue (Batocera v43 ou plus ?)"
bash "$SERV" start
for c in $CORES; do
  [ -f "/usr/lib/libretro/${c}_libretro.so" ] && echo "en place : /usr/lib/libretro/${c}_libretro.so"
done

# 3. systeme « hsfa » pour l'interface
mkdir -p "$(dirname "$ESCFG")"
if [ -f "$ESCFG" ] && ! cmp -s "$D/es_systems_hsfa.cfg" "$ESCFG" && [ ! -f "$ESCFG.avant-hsfa" ]; then
  cp -f "$ESCFG" "$ESCFG.avant-hsfa" && echo "copie de votre ancien fichier : $ESCFG.avant-hsfa"
fi
cp -f "$D/es_systems_hsfa.cfg" "$ESCFG" && echo "installe : $ESCFG"

# 4. coeur par defaut du systeme (Batocera ignore default="true" du fichier ci-dessus) ; pas de decor (bezel) :
#    le decor 4:3 ecraserait l'image 16:9 de fbneo_hsfaws
for kv in hsfa.emulator=libretro hsfa.core=fbneo_hsfa hsfa.bezel=none; do
  k=${kv%%=*}; v=${kv#*=}
  if [ -z "$(reglage_get "$k")" ]; then
    reglage_set "$k" "$v" && echo "reglage $k=$v" && echo "reglage $k" >> "$NOTE"
  else
    echo "deja regle : $k=$(reglage_get "$k")"
  fi
done

# 5. dossier des jeux
mkdir -p "$ROMS"
[ -f "$ROMS/gamelist.xml" ] || { cp "$D/gamelist.xml" "$ROMS/gamelist.xml" && echo "installe : $ROMS/gamelist.xml"; }

echo
echo "Fini. Mettez sfa3hsfa.zip, sfa3uhsfa.zip, sfa3umhsfa.zip, sfa3hhsfa.zip, sfa3hahsfa.zip dans $ROMS"
echo "(partage reseau : roms/hsfa), sans les renommer, puis relancez l'interface :"
echo "  Menu > Reglages des jeux > Mettre a jour la liste des jeux, ou : batocera-es-swissknife --restart"
echo "16:9 : voir le guide (reglage hsfa[\"<jeu>.zip\"].core=fbneo_hsfaws, ou hsfa.core=fbneo_hsfaws pour tous)."
