#!/bin/bash
# test_verifie_versement.sh : prouve chaque cas de tools/verifie_versement.sh dans un dépôt git JETABLE (dossier
# temporaire, effacé à la fin) : témoin propre, motif dans un fichier commité / un message / un commit intermédiaire /
# un fichier non suivi, nom de session en mot entier, mauvais auteur / committeur, retours en arrière (TSV, ancien,
# indexé, antislashs), arguments invalides, rien à contrôler, syntaxe Python, échec de la portabilité.
# Usage : bash tools/test_verifie_versement.sh [script à tester]   (défaut : le verifie_versement.sh voisin)
# Code de sortie : 0 si tous les cas donnent le code ET le message attendus.
set -u
SCRIPT=$(readlink -f "${1:-$(dirname "$0")/verifie_versement.sh}")
[ -f "$SCRIPT" ] || { echo "script introuvable : $SCRIPT" >&2; exit 2; }
T=$(mktemp -d) || exit 2
trap 'rm -rf "$T"' EXIT
export GIT_AUTHOR_NAME=Rickow GIT_AUTHOR_EMAIL=30348240+Rickow@users.noreply.github.com
export GIT_COMMITTER_NAME=Rickow GIT_COMMITTER_EMAIL=30348240+Rickow@users.noreply.github.com
export GIT_CONFIG_NOSYSTEM=1
MOTIF='motif-secret-zq'                       # motif personnel FICTIF passé par HSFA_MOTIFS_PERSO
MOT=$(id -un)                                 # nom de session : cherché en mot entier par le script
ILYA() { echo "@$(( $(date +%s) - $1 * 86400 )) +0000"; }

# ---- dépôt « amont » (base) et clone de travail
git init -q --bare -b main "$T/amont.git"
git clone -q "$T/amont.git" "$T/c" 2>/dev/null
cd "$T/c" || exit 2
git config core.hooksPath "$T/sans_hooks"; git config commit.gpgsign false
mkdir -p tools re/outils scripts/qualite
cp "$SCRIPT" tools/verifie_versement.sh
cat > tools/verifie_portabilite.py <<'EOF'
import os, sys
print("portabilite (bouchon)")
sys.exit(1 if os.path.exists("ECHEC_PORTABILITE") else 0)
EOF
echo 'print("0 erreur(s)")' > re/outils/verifie.py
echo 'print("0 lien")' > scripts/qualite/verifier_liens.py
printf 'ligne ancienne 1\nligne ancienne 2\nligne ancienne 3\n' > ancien.txt
git add -A; GIT_AUTHOR_DATE=$(ILYA 40) GIT_COMMITTER_DATE=$(ILYA 40) git commit -q -m "old base"
printf 'adresse\tnom\tvaleur\n0x10\tA\t1\n0x20\tB\t2\n0x30\tC\t3\n' > donnees.tsv
printf 'normal\nmotif \\d+\\.\\t et \\x41 fin\nautre\n' > echap.txt
git add -A; git commit -q -m "recent base"
git push -q origin HEAD:main 2>/dev/null
git fetch -q origin

ok=0; ko=0
remet() { git reset -q --hard origin/main; git clean -qfdx; git config user.name Rickow; git config user.email 30348240+Rickow@users.noreply.github.com; }
# cas <libellé> <code attendu> <texte attendu dans la sortie> -- <arguments du script>
# (CAS_MOTIFS=<valeur> cas … : HSFA_MOTIFS_PERSO pour ce cas ; vide = non défini)
cas() {
  local lib=$1 attendu=$2 texte=$3; shift 4
  HSFA_MOTIFS_PERSO=${CAS_MOTIFS-$MOTIF} bash tools/verifie_versement.sh "$@" > "$T/sortie" 2>&1; local r=$?
  if [ $r = "$attendu" ] && grep -q -F -- "$texte" "$T/sortie" && ! grep -q 'awk:' "$T/sortie"; then
    echo "OK    $lib (code $r)"; ok=$((ok + 1))
  else
    echo "ÉCHEC $lib : code $r (attendu $attendu), texte attendu « $texte »"; sed 's/^/      | /' "$T/sortie"; ko=$((ko + 1))
  fi
  remet
}

remet
# 1. témoin propre : un mot qui CONTIENT le nom de session sans être ce mot, un .py valide
printf 'note propre %schet\n' "$MOT" > propre.txt; echo 'x = 1' > ok.py; git add -A; git commit -q -m "clean change"
cas "témoin propre (--base)" 0 "VERSEMENT OK" -- --base origin/main
# 2. motif dans un fichier commité
echo "chemin /x/$MOTIF/y" > f.txt; git add -A; git commit -q -m "add f"
cas "motif dans un fichier commité" 1 "motif personnel dans les lignes ajoutées (diff complet)" -- --base origin/main
# 3. motif dans un message de commit
echo a > g.txt; git add -A; git commit -q -m "fix for $MOTIF"
cas "motif dans un message" 1 "motif personnel dans les messages de commit" -- --base origin/main
# 4. nom de session en mot entier, en capitales
echo "voir ${MOT^^} ici" > h.txt; git add -A; git commit -q -m "add h"
cas "nom de session (mot entier, sans casse)" 1 "motif personnel dans les lignes ajoutées" -- --base origin/main
# 5. mauvais auteur, mauvais committeur
echo a > i.txt; git add -A; GIT_AUTHOR_NAME=Autre GIT_AUTHOR_EMAIL=autre@exemple.org git commit -q -m "add i"
cas "mauvais auteur" 1 "auteur : Autre <autre@exemple.org>" -- --base origin/main
echo a > i.txt; git add -A; GIT_COMMITTER_EMAIL=autre@exemple.org git commit -q -m "add i"
cas "mauvais committeur" 1 "committeur : Rickow <autre@exemple.org>" -- --base origin/main
# 6. retours en arrière
sed -i '/^0x20/d' donnees.tsv; git commit -q -am "drop a tsv row"
cas "TSV : ligne récente retirée (commitée)" 1 "donnees.tsv : 1 ligne(s) récente(s) retirée(s)" -- --base origin/main 3
sed -i 's/^0x30\tC\t3$/0x30\tC\t4/' donnees.tsv; git add -A
cas "TSV : ligne récente remplacée (indexée, sans --base)" 1 "donnees.tsv : 1 ligne(s) récente(s) retirée(s)" -- 3
sed -i '/ancienne 2/d' ancien.txt; git commit -q -am "drop an old line"
cas "ligne ancienne retirée (40 j > 7 j) : permis" 0 "VERSEMENT OK" -- --base origin/main
sed -i '/ancienne 2/d' ancien.txt; git commit -q -am "drop an old line"
cas "ligne ancienne retirée, fenêtre de 60 j" 1 "ancien.txt : 1 ligne(s) récente(s) retirée(s)" -- --base origin/main 60
sed -i '/motif/d' echap.txt; git commit -q -am "drop escaped line"
cas "ligne à antislashs retirée (sans avertissement awk)" 1 'motif \d+\.\t et \x41 fin' -- --base origin/main
git rm -q donnees.tsv; git commit -q -m "remove tsv"
cas "fichier récent supprimé" 1 "donnees.tsv : 4 ligne(s) récente(s) retirée(s)" -- --base origin/main
# 7. arguments invalides, base inconnue
cas "argument « origin/main » pris pour des jours" 2 "pour contrôler une plage de commits : --base origin/main" -- origin/main
cas "argument « abc »" 2 "« abc » n'est pas un nombre de jours" -- abc
cas "base inconnue" 2 "référence inconnue" -- --base origine/rien
# 8. rien à contrôler
echo a > j.txt; git add -A; git commit -q -m "add j"
cas "commits en avance, rien d'indexé, sans --base" 2 "relancer avec --base origin/main" -- 3
cas "rien du tout (--base)" 2 "rien à contrôler" -- --base origin/main
# 9. motif ajouté puis retiré dans la plage : invisible dans le diff net, vu commit par commit
echo "$MOTIF" > k.txt; git add -A; git commit -q -m "add k"; git rm -q k.txt; git commit -q -m "remove k"
cas "motif dans un commit intermédiaire" 1 "motif personnel dans les lignes ajoutées par les commits (un par un)" -- --base origin/main
# 10. fichier non suivi, non indexé
echo "$MOTIF" > nonsuivi.txt
cas "motif dans un fichier non suivi (--base)" 1 "motif personnel dans les lignes ajoutées (diff complet)" -- --base origin/main
echo "propre" >> ancien.txt; echo "$MOTIF" >> ancien.txt
cas "motif dans un changement non indexé (--base)" 1 "motif personnel dans les lignes ajoutées (diff complet)" -- --base origin/main
# 11. syntaxe Python, identité du prochain commit, portabilité
echo 'def f(:' > casse.py; git add -A
cas "syntaxe Python (indexé)" 1 "!! casse.py" -- 7
echo a > l.txt; git add -A
GIT_COMMITTER_NAME=Autre cas "identité du prochain commit" 1 "prochain commit (GIT_COMMITTER_IDENT)" -- --base origin/main
echo a > l.txt; git add -A; touch ECHEC_PORTABILITE
cas "échec de la portabilité remonté" 1 "verifie_portabilite.py : code 1" -- --base origin/main

# 12. sans HSFA_MOTIFS_PERSO (cas réel du coordinateur), expression invalide
echo a > m.txt; git add -A; git commit -q -m "add m"
CAS_MOTIFS= cas "propre, HSFA_MOTIFS_PERSO non défini : OK mais PARTIEL" 0 "VERSEMENT OK (anonymat PARTIEL" -- --base origin/main
echo "voir $MOT ici" > m.txt; git add -A; git commit -q -m "add m"
CAS_MOTIFS= cas "nom de session attrapé sans HSFA_MOTIFS_PERSO" 1 "motif personnel dans les lignes ajoutées" -- --base origin/main
echo a > m.txt; git add -A; git commit -q -m "add m"
CAS_MOTIFS='(' cas "HSFA_MOTIFS_PERSO invalide" 1 "expression grep -E invalide" -- --base origin/main
# 13. branche non rebasée : la base a reçu un commit après la bifurcation
echo "travail d'un autre" > autre.txt; git add -A; git commit -q -m "other work"; git push -q origin HEAD:main 2>/dev/null
git fetch -q origin; git reset -q --hard HEAD~1; echo a > n.txt; git add -A; git commit -q -m "add n"
cas "branche non rebasée sur la base" 1 "n'est pas rebasé sur origin/main (1 commit(s) de retard)" -- --base origin/main

echo "== $ok cas OK, $ko en échec"
[ $ko = 0 ]
