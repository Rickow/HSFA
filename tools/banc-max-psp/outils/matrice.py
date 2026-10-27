#!/usr/bin/env python3
"""matrice.py <resultats/cand> nom1 nom2 ... : verdicts côte à côte (une colonne par fichier TSV de resultats) pour comparer les victimes."""
import sys, csv, collections
d = sys.argv[1]; noms = sys.argv[2:]
T = collections.OrderedDict()
for n in noms:
    for r in csv.DictReader(open("%s/%s.tsv" % (d, n)), delimiter="\t"):
        T.setdefault(r["id"], dict(coup=r["coup"]))[n] = r
print("\t".join(["id", "coup"] + noms))
for k, v in T.items():
    print("\t".join([k, v["coup"][:38]] + [v[n]["verdict"] if n in v else "-" for n in noms]))
