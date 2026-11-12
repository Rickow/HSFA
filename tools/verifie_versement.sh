#!/bin/bash
# verifie_versement.sh [jours] : contrôles à lancer AVANT de valider un versement (changements indexés, git add fait).
#   1. retours en arrière : lignes que le versement RETIRE alors qu'elles ont été ajoutées par un commit des N derniers
#      jours (défaut 7) -> un diff fait sur une base ancienne annule silencieusement un travail récent (11/11 : correctifs
#      Windows de paquet_fbneo.py retirés par le diff des sons PS2) ;
#   2. syntaxe des .py indexés ; 3. tools/verifie_portabilite.py ; 4. re/outils/verifie.py ;
#   5. scripts/qualite/verifier_liens.py (compte seulement) ; 6. anonymat des lignes ajoutées.
# Code de sortie 1 si un contrôle bloquant échoue (1, 2, 3, 4, 6). Ne modifie rien.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
J=${1:-7}; ECHEC=0
fichiers=$(git diff --cached --name-only --diff-filter=M)

echo "== 1. retours en arrière (lignes retirées, ajoutées depuis $J jours)"
for f in $fichiers; do
  git diff --cached -U0 -- "$f" | grep '^-[^-]' | sed 's/^-//' | grep -v '^[[:space:]]*$' | sort -u > /tmp/.vv_retirees.$$ || true
  [ -s /tmp/.vv_retirees.$$ ] || continue
  git log --since="$J days ago" -p --format='@@COMMIT %h %s' -- "$f" \
    | awk '/^@@COMMIT/{c=substr($0,10); next} /^\+[^+]/{print c "\t" substr($0,2)}' > /tmp/.vv_ajouts.$$
  while IFS= read -r l; do
    m=$(awk -F'\t' -v l="$l" '$2==l{print $1; exit}' /tmp/.vv_ajouts.$$)
    if [ -n "$m" ]; then echo "  !! $f : retire une ligne ajoutée par $m :"; echo "       $l"; ECHEC=1; fi
  done < /tmp/.vv_retirees.$$
done
rm -f /tmp/.vv_retirees.$$ /tmp/.vv_ajouts.$$
[ $ECHEC = 0 ] && echo "  ok"

echo "== 2. syntaxe Python"
for f in $(git diff --cached --name-only --diff-filter=AM | grep '\.py$'); do
  python3 -I -c "import ast,sys; ast.parse(open(sys.argv[1], encoding='utf-8').read())" "$f" 2>/dev/null \
    || { echo "  !! $f"; ECHEC=1; }
done

echo "== 3. portabilité"; python3 -I tools/verifie_portabilite.py | tail -2 || ECHEC=1
echo "== 4. index re/"; python3 -I re/outils/verifie.py 2>&1 | tail -1 | tee /tmp/.vv_re.$$
grep -q '^0 erreur' /tmp/.vv_re.$$ || ECHEC=1; rm -f /tmp/.vv_re.$$
echo "== 5. liens de la doc (introuvables)"; python3 -I scripts/qualite/verifier_liens.py 2>&1 | grep -c introuvable
echo "== 6. anonymat des lignes ajoutées"
if [ -n "${HSFA_MOTIFS_PERSO:-}" ]; then
  git diff --cached | grep '^+' | grep -n -i -E "$HSFA_MOTIFS_PERSO" && ECHEC=1 || echo "  ok"
else
  echo "  (HSFA_MOTIFS_PERSO non défini : contrôle sauté)"
fi
[ $ECHEC = 0 ] && echo "VERSEMENT OK" || echo "VERSEMENT À REVOIR"
exit $ECHEC
