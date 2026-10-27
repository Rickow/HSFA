#!/bin/bash
# (agent_integration_max) préparation MAX (contre la construction de référence banc_ref) puis construction MAX=1 dans
# banc_max ; journal dans banc_max/construction.log. Option : REF=1 reconstruit aussi banc_ref (MAX=0).
set -e
I=${HSFA_WORKSPACE}/work/agent_integration_max
source ${HSFA_WORKSPACE}/env.sh >/dev/null; source ${HSFA_WORKSPACE}/env_max.sh
if [ "$REF" = 1 ]; then (cd $I/untranspile; MODULE=ro5 TRAVAIL=$I/banc_ref nice -n 19 python3 mame_test.py > $I/banc_ref/construction.log 2>&1); fi
[ "$PREP" = 0 ] || (cd $I/outils; set -o pipefail; nice -n 19 python3 prepare_max.py | tail -3) || { echo "ÉCHEC de la préparation MAX : construction arrêtée"; exit 1; }
# banques du banc / du coeur : copie fraîche de celles d'Upper + une banque par perso MAX actif (perso 38+k -> 3826+k)
python3 - <<'PY'
import json, os, shutil
I = "${HSFA_WORKSPACE}/work/agent_integration_max"; B = I + "/" + os.environ.get("BANC", "banc_max") + "/banques_hx"
if os.path.exists(B): shutil.rmtree(B)
shutil.copytree("${HSFA_WORKSPACE}/work/mame_ro5/banques_hx", B)
P = json.load(open(I + "/outils/persos_max.json")); act = os.environ.get("MAX_PERSOS")
act = act.split(",") if act else [k for k, v in P.items() if not k.startswith("_") and v.get("actif")]
L = open(B + "/carte.txt").read().splitlines()
for p in act:
    i = int(p, 16); n = 3800 + i
    L = [l for l in L if l.split()[:2] != ["perso", str(i)]] + ["perso %d %d" % (i, n)]
    shutil.copy(os.path.join(os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max")), "fork", "pl%s_hx.bin" % P[p]["suffixe"]), B + "/f%d.bin" % n)
open(B + "/carte.txt", "w").write("\n".join(L) + "\n")
print("banques : " + ", ".join("perso %d -> %d" % (int(p, 16), 3800 + int(p, 16)) for p in act))
PY
mkdir -p $I/${BANC:-banc_max}; echo "${SFA3MAX_CACHE:-}" > $I/${BANC:-banc_max}/sfa3max_cache.txt   # (2b11) cache MAX du banc
(cd $I/untranspile; MAX=1 MODULE=ro5 TRAVAIL=$I/${BANC:-banc_max} nice -n 19 python3 mame_test.py > $I/${BANC:-banc_max}/construction.log 2>&1)
grep -E "MAX :|Traceback|Error" $I/${BANC:-banc_max}/construction.log | tail -4
md5sum $I/banc_ref/roms_ro5/sfa3ud/sz3ud.03c $I/${BANC:-banc_max}/roms_ro5/sfa3ud/sz3ud.03c
# (2b22, audit des tables par id) marques de fin des blocs ajoutés aux copies rel16 (piège 0x960090) : échec si absente
python3 $I/outils/audit/marques.py $I/${BANC:-banc_max} > $I/${BANC:-banc_max}/marques.tsv || { echo "ÉCHEC : marque de fin absente (marques.tsv)"; exit 1; }
