#!/bin/bash
# empreinte.sh — fonctions shell des bancs qui prouvent ce qu'ils mesurent (à SOURCER : . ${HSFA_WORKSPACE}/work/outils/empreinte.sh)
# Le calcul est fait par empreinte.py (même dossier) ; voir son en-tête pour ce qui entre dans l'empreinte.
#
#   empreinte_verifie FICHIER -- <commande de l'émulateur…>
#       calcule l'empreinte de ce que la commande charge (ROM programme du -rompath réel + ext de BANC_DIR / HSFA_EXT,
#       ou zip FBNeo), l'écrit dans FICHIER (« # empreinte: … » + « # attendu: … »), la compare à ATTENDU_MD5 /
#       ATTENDU_REF. Code 86 + message « ARRÊT DU BANC » si elle diffère : le banc doit s'arrêter (exit 86).
#   empreinte_entete RESULTAT FICHIER_EMPREINTE
#       recopie les lignes « # empreinte » / « # attendu » de FICHIER_EMPREINTE EN TÊTE de RESULTAT (s'il ne les a pas).
#   empreinte_crc -- <commande>      CRC32 programme attendu par empreinte.lua (preuve interne, facultative)
#   empreinte_ref NOM|DOSSIER        empreinte d'une référence figée (pour remplir ATTENDU_MD5)
#
# Exemple (lance.sh) :
#   . ${HSFA_WORKSPACE}/work/outils/empreinte.sh
#   empreinte_verifie "$D/empreinte.txt" -- "${JEU[@]}" || { echo "lance.sh : ARRÊT, empreinte" >&2; exit 86; }
EMPREINTE_PY=${EMPREINTE_PY:-$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/empreinte.py}; export EMPREINTE_PY

empreinte_verifie() {
  local f=$1; shift; [ "${1:-}" = "--" ] && shift
  python3 "$EMPREINTE_PY" commande --sortie "$f" -- "$@" > /dev/null
}

empreinte_entete() {
  local r=$1 e=$2 t
  [ -f "$r" ] && [ -f "$e" ] || return 0
  head -n 3 "$r" | grep -q '^# empreinte: ' && return 0
  t=$(mktemp "$r.XXXXXX") || return 1
  { grep -E '^# (empreinte|attendu|EMPREINTE_LUA)' "$e"; cat "$r"; } > "$t" && mv "$t" "$r"
}

empreinte_crc() { [ "${1:-}" = "--" ] && shift; python3 "$EMPREINTE_PY" crc -- "$@"; }

empreinte_ref() {
  python3 - "$1" <<'P'
import sys, os
sys.path.insert(0, os.path.dirname(os.environ.get('EMPREINTE_PY', '${HSFA_WORKSPACE}/work/outils/empreinte.py')))
import empreinte as E
p = E.resout_ref(sys.argv[1])
if not p: sys.exit('référence inconnue : ' + sys.argv[1])
e = E.calcule_dossier(p); print(E.ligne(e))
for c in e.get('controle', []): print('ATTENTION : ' + c)
P
}

# exécuté directement : petite aide
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  case "${1:-}" in
    ref) empreinte_ref "$2";;
    crc) shift; empreinte_crc "$@";;
    verifie) shift; empreinte_verifie "$@"; c=$?; cat "$1" 2>/dev/null; exit $c;;
    *) sed -n '2,18p' "$0";;
  esac
fi
