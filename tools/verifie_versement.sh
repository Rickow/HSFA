#!/bin/bash
# verifie_versement.sh [--base <réf>] [jours] : contrôles à lancer AVANT de valider ou de livrer un versement. Ne modifie
# rien (ni l'index, ni l'arbre de travail).
#   --base <réf> (RECOMMANDÉ, ex. --base origin/main) : contrôle TOUT ce qui sépare <réf> du dépôt de travail :
#      commits <réf>...HEAD (depuis la base commune), changements indexés, non indexés et fichiers non suivis
#      (hors .gitignore). ÉCHOUE si HEAD n'est pas rebasé sur <réf>.
#   sans --base : changements INDEXÉS seulement (git add fait). Échoue (code 2) si rien n'est indexé ; prévient si HEAD a
#      des commits en avance sur sa base (amont, sinon origin/main), que ce mode ne voit pas.
#   jours : fenêtre du contrôle 1, entier (défaut 7) ; tout autre argument est refusé (code 2).
# Contrôles :
#   1. retours en arrière : lignes RETIRÉES (fichiers modifiés, supprimés, renommés) dont le dernier commit, selon
#      git blame sur la base, a moins de N jours (11/11 : un diff fait sur une base ancienne annule un travail récent) ;
#   2. syntaxe des .py ajoutés ou modifiés ; 3. tools/verifie_portabilite.py ; 4. re/outils/verifie.py ;
#   5. scripts/qualite/verifier_liens.py (compte seulement) ;
#   6. anonymat : lignes ajoutées et noms de fichiers (diff complet ET chaque commit de la plage), messages de commit ;
#      motifs = HSFA_MOTIFS_PERSO (grep -E, sans casse) + nom de session (id -un) et nom du dossier personnel en mot
#      entier, sans casse ; auteur et committeur de chaque commit de la plage et du prochain commit = identité du projet.
# Code de sortie : 0 = OK ; 1 = un contrôle bloquant (1, 2, 3, 4, 6) échoue ; 2 = usage, ou rien à contrôler.
# Tests : bash tools/test_verifie_versement.sh (dépôt git jetable).
set -u
IDENT='Rickow <30348240+Rickow@users.noreply.github.com>'

erreur() {
  echo "verifie_versement.sh : $*" >&2
  echo "usage : bash tools/verifie_versement.sh [--base <réf>] [jours]   (ex. --base origin/main)" >&2
  exit 2
}

BASE=; J=
while [ $# -gt 0 ]; do
  case $1 in
    --base) [ $# -ge 2 ] || erreur "--base demande une référence (ex. --base origin/main)"; BASE=$2; shift 2 ;;
    --base=*) BASE=${1#--base=}; shift ;;
    -h|--help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) erreur "option inconnue : $1" ;;
    *) [ -z "$J" ] || erreur "un seul argument « jours » attendu (reçu « $J » puis « $1 »)"; J=$1; shift ;;
  esac
done
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || erreur "à lancer dans un dépôt git"
J=${J:-7}
case $J in
  *[!0-9]*|'')
    if git rev-parse --verify -q "$J^{commit}" >/dev/null 2>&1; then
      erreur "« $J » n'est pas un nombre de jours ; pour contrôler une plage de commits : --base $J"
    fi
    erreur "« $J » n'est pas un nombre de jours (entier attendu)" ;;
esac
J=$((10#$J))

TMPD=$(mktemp -d) || exit 2
trap 'rm -rf "$TMPD"' EXIT
ECHEC=0; PARTIEL=0; IDX=

# ------------------------------------------------------------------ périmètre
if [ -n "$BASE" ]; then
  BC=$(git rev-parse --verify -q "$BASE^{commit}") || erreur "référence inconnue : « $BASE »"
  MB=$(git merge-base "$BC" HEAD) || erreur "aucune base commune entre « $BASE » et HEAD"
  COMMITS=$(git rev-list --reverse "$MB..HEAD")
  # index temporaire = copie de l'index + fichiers non suivis en « intention d'ajout » : git diff MB voit alors les
  # commits, l'indexé, le non-indexé et les nouveaux fichiers ; l'index réel n'est pas touché.
  IDX="$TMPD/index"
  cp "$(git rev-parse --git-path index)" "$IDX" 2>/dev/null || true
  git ls-files -z --others --exclude-standard > "$TMPD/nonsuivis"
  [ -s "$TMPD/nonsuivis" ] && GIT_INDEX_FILE="$IDX" xargs -0 git add -N -- < "$TMPD/nonsuivis"
  gd() { GIT_INDEX_FILE="$IDX" git -c core.quotePath=false diff --no-color --no-ext-diff "$MB" "$@"; }
  NC=$(printf '%s' "$COMMITS" | grep -c .)
  NU=$(tr -cd '\0' < "$TMPD/nonsuivis" | wc -c)
  echo "== périmètre : $BASE (base commune ${MB:0:9}) → arbre de travail : $NC commit(s) + indexé + non indexé + $NU fichier(s) non suivi(s)"
  if [ "$MB" != "$BC" ]; then
    # bloquant : un « git diff $BASE » fait depuis cette branche annulerait ce que la base a reçu depuis (11/11)
    echo "  !! HEAD n'est pas rebasé sur $BASE ($(git rev-list --count "$MB..$BC") commit(s) de retard) : git fetch && git rebase $BASE"
    ECHEC=1
  fi
  if [ "$NU" -gt 0 ]; then
    echo "  (non suivis inclus :"; tr '\0' '\n' < "$TMPD/nonsuivis" | head -10 | sed 's/^/     /'; echo "   )"
  fi
else
  MB=HEAD; COMMITS=
  gd() { git -c core.quotePath=false diff --no-color --no-ext-diff --cached HEAD "$@"; }
  AMONT=$(git rev-parse -q --verify '@{upstream}' 2>/dev/null) || AMONT=$(git rev-parse -q --verify origin/main 2>/dev/null) || AMONT=
  AV=0; [ -n "$AMONT" ] && AV=$(git rev-list --count "$AMONT..HEAD")
  if git diff --cached --quiet HEAD; then
    if [ "$AV" -gt 0 ]; then
      erreur "rien d'indexé, mais HEAD a $AV commit(s) en avance sur sa base, que ce mode ne contrôle PAS : relancer avec --base origin/main (ou --base <base de la livraison>)"
    fi
    erreur "rien à contrôler : aucun changement indexé (git add), et aucun commit en avance ; pour une plage : --base <réf>"
  fi
  echo "== périmètre : changements INDEXÉS contre HEAD"
  [ "$AV" -gt 0 ] && echo "  ?? HEAD a $AV commit(s) en avance sur sa base, NON contrôlés par ce mode : ajouter --base origin/main"
  git diff --quiet || echo "  ?? des changements NON indexés existent, non contrôlés par ce mode (git add, ou --base)"
fi

# liste des fichiers : statut, ancien chemin, nouveau chemin (séparés par des tabulations ; -z pour les noms exotiques)
gd --name-status -z -M | while IFS= read -r -d '' st; do
  case $st in
    R*|C*) IFS= read -r -d '' a; IFS= read -r -d '' n ;;
    *) IFS= read -r -d '' a; n=$a ;;
  esac
  printf '%s\t%s\t%s\n' "${st:0:1}" "$a" "$n"
done > "$TMPD/fichiers"
if [ ! -s "$TMPD/fichiers" ] && [ -z "$COMMITS" ]; then
  erreur "rien à contrôler : aucun commit après $BASE et aucun changement dans l'arbre de travail"
fi
echo "   $(wc -l < "$TMPD/fichiers") fichier(s) touché(s) au total"

# ------------------------------------------------------------------ 1. retours en arrière
echo "== 1. retours en arrière (lignes retirées dont le dernier commit a moins de $J jours, blame sur ${MB:0:9})"
MAINTENANT=$(date +%s); LIM=$(( MAINTENANT - J * 86400 )); N1=0
while IFS=$'\t' read -r st a n; do
  case $st in M|D|R) ;; *) continue ;; esac
  # plages retirées « -début,nombre » des en-têtes de blocs (-U0 : toute ligne « @@ » est un en-tête)
  gd -U0 -M -- "$a" "$n" | awk '/^@@ /{ split(substr($2, 2), x, ","); k = (x[2] == "") ? 1 : x[2] + 0;
                                         if (k > 0) print "-L" x[1] "," (x[1] + k - 1) }' > "$TMPD/plages"
  [ -s "$TMPD/plages" ] || continue
  mapfile -t PL < "$TMPD/plages"
  git blame --line-porcelain "${PL[@]}" "$MB" -- "$a" 2>/dev/null \
    | awk -v lim="$LIM" -v now="$MAINTENANT" '
        $1 ~ /^[0-9a-f]+$/ && length($1) >= 40 { c = substr($1, 1, 9); l = $3; next }
        /^committer-time / { t = $2 + 0; next }
        /^\t/ { if (t >= lim) printf "       l.%d (%s, il y a %d j) : %s\n", l, c, int((now - t) / 86400), substr($0, 2, 110) }' \
    > "$TMPD/retours"
  if [ -s "$TMPD/retours" ]; then
    echo "  !! $a : $(wc -l < "$TMPD/retours") ligne(s) récente(s) retirée(s) :"; head -20 "$TMPD/retours"
    N1=$((N1 + 1)); ECHEC=1
  fi
done < "$TMPD/fichiers"
[ $N1 = 0 ] && echo "  ok"

# ------------------------------------------------------------------ 2. syntaxe Python
echo "== 2. syntaxe Python"; N2=0
while IFS=$'\t' read -r st a n; do
  case $st in A|M|R|C) ;; *) continue ;; esac
  case $n in *.py) ;; *) continue ;; esac
  if [ -n "$BASE" ]; then cat -- "$n"; else git show ":$n"; fi 2>/dev/null \
    | python3 -I -c "import ast,sys; ast.parse(sys.stdin.buffer.read())" 2>"$TMPD/py" \
    || { echo "  !! $n : $(tail -1 "$TMPD/py")"; N2=1; ECHEC=1; }
done < "$TMPD/fichiers"
[ $N2 = 0 ] && echo "  ok"

# ------------------------------------------------------------------ 3-5. outils du dépôt (sur l'arbre de travail)
echo "== 3. portabilité"
python3 -I tools/verifie_portabilite.py > "$TMPD/port" 2>&1; r=$?
tail -2 "$TMPD/port"; [ $r = 0 ] || { echo "  !! verifie_portabilite.py : code $r"; ECHEC=1; }
echo "== 4. index re/"
python3 -I re/outils/verifie.py > "$TMPD/re" 2>&1; r=$?
tail -1 "$TMPD/re"
{ [ $r = 0 ] && tail -1 "$TMPD/re" | grep -q '^0 erreur'; } || { echo "  !! re/outils/verifie.py : code $r"; ECHEC=1; }
echo "== 5. liens de la doc (introuvables)"
python3 -I scripts/qualite/verifier_liens.py 2>&1 | grep -c introuvable

# ------------------------------------------------------------------ 6. anonymat
echo "== 6. anonymat (lignes ajoutées, noms de fichiers, messages, auteurs)"
MOTS=()
for m in "$(id -un 2>/dev/null)" "$(basename "${HOME:-/}")"; do
  [ ${#m} -ge 3 ] && [ "$m" != root ] && [[ " ${MOTS[*]-} " != *" $m "* ]] && MOTS+=("$m")
done
ARGS=(); for m in "${MOTS[@]+"${MOTS[@]}"}"; do ARGS+=(-e "$m"); done
if [ -z "${HSFA_MOTIFS_PERSO:-}" ]; then
  echo "  !! HSFA_MOTIFS_PERSO non défini : seuls le nom de session et le dossier personnel sont cherchés (contrôle PARTIEL)"
  PARTIEL=1
fi
if [ ${#MOTS[@]} = 0 ]; then
  echo "  !! nom de session et dossier personnel inutilisables (root ou moins de 3 lettres) : mot entier non cherché (contrôle PARTIEL)"
  PARTIEL=1
fi
N6=0
# cherche <fichier> <libellé> : lignes du fichier qui contiennent un motif personnel
cherche() {
  local g=1 h=1
  : > "$TMPD/t1"; : > "$TMPD/t2"
  if [ -n "${HSFA_MOTIFS_PERSO:-}" ]; then
    grep -a -i -E -e "$HSFA_MOTIFS_PERSO" -- "$1" > "$TMPD/t1" 2>"$TMPD/e1"; g=$?
    if [ $g -ge 2 ]; then echo "  !! HSFA_MOTIFS_PERSO : expression grep -E invalide ($(head -1 "$TMPD/e1"))"; N6=1; ECHEC=1; return; fi
  fi
  if [ ${#ARGS[@]} -gt 0 ]; then
    grep -a -i -w -F "${ARGS[@]}" -- "$1" > "$TMPD/t2" 2>/dev/null; h=$?
    if [ $h -ge 2 ]; then echo "  !! grep en erreur sur $2"; N6=1; ECHEC=1; return; fi
  fi
  if [ $g = 0 ] || [ $h = 0 ]; then
    echo "  !! motif personnel dans $2 :"; sort -u "$TMPD/t1" "$TMPD/t2" | head -15 | cut -c1-160 | sed 's/^/       /'
    N6=1; ECHEC=1
  fi
}
# lignes ajoutées d'un diff, préfixées « fichier : » (les en-têtes de fichier ne sont pas des ajouts)
ajouts() {
  awk '/^@@@COMMIT /{ c = $2 " "; h = 1; next }
       /^diff --git /{ h = 1; next }
       h && /^\+\+\+ /{ f = substr($0, 5); sub(/^b\//, "", f); next }
       /^@@ /{ h = 0; next }
       !h && /^\+/{ print c f " : " substr($0, 2) }'
}
cut -f2,3 "$TMPD/fichiers" | tr '\t' '\n' | sort -u > "$TMPD/noms"
cherche "$TMPD/noms" "les noms de fichiers"
gd --text -U0 | ajouts > "$TMPD/aj"
cherche "$TMPD/aj" "les lignes ajoutées (diff complet)"
if [ -n "$COMMITS" ]; then
  git -c core.quotePath=false log --no-color --text -p -U0 --diff-merges=first-parent --format='@@@COMMIT %h' "$MB..HEAD" \
    | ajouts > "$TMPD/ajc"
  cherche "$TMPD/ajc" "les lignes ajoutées par les commits (un par un)"
  git -c core.quotePath=false log --name-only --format= "$MB..HEAD" | sort -u > "$TMPD/nomsc"
  cherche "$TMPD/nomsc" "les noms de fichiers des commits"
  git log --format='@@@COMMIT %h%n%B' "$MB..HEAD" > "$TMPD/msg"
  cherche "$TMPD/msg" "les messages de commit"
  git log --format='%h%x09%an <%ae>%x09%cn <%ce>' "$MB..HEAD" \
    | awk -F'\t' -v id="$IDENT" '$2 != id { print "       " $1 " auteur : " $2 } $3 != id { print "       " $1 " committeur : " $3 }' \
    > "$TMPD/id"
  if [ -s "$TMPD/id" ]; then
    echo "  !! identité différente de « $IDENT » :"; head -15 "$TMPD/id"; N6=1; ECHEC=1
  fi
fi
# identité du prochain commit, s'il reste des changements non commités
if ! git diff --cached --quiet HEAD || ! GIT_INDEX_FILE="${IDX:-$(git rev-parse --git-path index)}" git diff --quiet HEAD; then
  for v in GIT_AUTHOR_IDENT GIT_COMMITTER_IDENT; do
    p=$(git var "$v" 2>/dev/null | sed 's/ [0-9]* [-+][0-9]*$//')
    [ "$p" = "$IDENT" ] || { echo "  !! prochain commit ($v) : « $p » au lieu de « $IDENT » (git config user.name / user.email)"; N6=1; ECHEC=1; }
  done
fi
[ $N6 = 0 ] && echo "  ok"

if [ $ECHEC = 0 ]; then
  if [ $PARTIEL = 1 ]; then echo "VERSEMENT OK (anonymat PARTIEL : définir HSFA_MOTIFS_PERSO)"; else echo "VERSEMENT OK"; fi
else
  echo "VERSEMENT À REVOIR"
fi
exit $ECHEC
