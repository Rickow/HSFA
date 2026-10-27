#!/bin/bash
# (agent_integration_max) bissection : construit BANC avec AG_SEL (PREP=0) puis une partie Arcade (PERSO) de NF images,
# comparée à REF_LOG (journal de banc_ref) : bissecte.sh BANC AG_SEL PERSO REF_LOG
I=${HSFA_WORKSPACE}/work/agent_integration_max; b=$1; sel=$2; p=${3:-04}; R=${4:-$I/essais/p2b/a04_ref.txt}
mkdir -p $I/$b/roms_fork; ln -sfn ../roms_ro5/sfa3ud $I/$b/roms_fork/sfa3hx
cd $I; PREP=0 AG_SEL=$sel BANC=$b nice -n 19 ./construit_max.sh > $I/$b/construit.txt 2>&1
NR5_NF=${NF:-49000} untranspile/arcade_tournee.sh $b $p essais/p2b/bis_$b.txt > /dev/null
python3 - "$R" "$I/essais/p2b/bis_$b.txt" "$sel" <<'P'
import sys
a=open(sys.argv[1]).read().splitlines(); b=open(sys.argv[2]).read().splitlines()
n=min(len(a),len(b))-2
d=next((i for i,(x,y) in enumerate(zip(a[:n],b[:n])) if x!=y), None)
print("AG_SEL=%s : %s" % (sys.argv[3], "identique (%d lignes)" % n if d is None else "diverge ligne %d : %s | %s" % (d, a[d], b[d])))
P
