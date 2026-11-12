#!/usr/bin/env python3
"""exact_groupes.py : pour chaque routine de code_decor.tsv, copie EXACTE (masquee) dans Hyper ? -> code_decor_exact.tsv
et bilan par groupe (octets avec / sans copie exacte)."""
import os, sys, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import routines_exactes as RE
H = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(H, "code_decor.tsv")), delimiter='\t'))
out = open(os.path.join(H, "code_decor_exact.tsv"), "w"); out.write("groupe\troutine_ro5\ttaille\tcouv_k\tcopie_hyper\n")
tot = collections.defaultdict(collections.Counter)
for r in rows:
    a, b, h = RE.cherche(int(r['routine_ro5'], 16))
    out.write("%s\t%s\t%s\t%s\t%s\n" % (r['groupe'], r['routine_ro5'], r['taille'], r['couv_k'], ' '.join('%x' % x for x in h)))
    tot[r['groupe']]['avec' if h else 'sans'] += int(r['taille'])
out.close()
for g, c in tot.items(): print("%-95s copie exacte %5.1f Ko ; sans %5.1f Ko" % (g[:95], c['avec']/1024, c['sans']/1024))
