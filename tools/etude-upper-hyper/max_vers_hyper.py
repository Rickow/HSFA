#!/usr/bin/env python3
"""Adresses du moteur utilisees par MAX (arcade -> va MIPS d'Upper, correspondances.tsv + complement) : homologue dans
Hyper (routine ro9 partenaire de la routine ro5 ; classe ; instruction alignee). Sortie max_vers_hyper.tsv."""
import os, sys, csv, pickle, collections, bisect
os.environ["GRAIN"] = "routine"
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
import homologue as H
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb"))
CMP9 = pickle.load(open("<workspace>/work/carto_ro9/comparaison_ro9_routine.pkl", "rb"))
BA9 = pickle.load(open(os.path.join(OUT, "bilan_a.pkl"), "rb"))
rows = list(csv.DictReader(open("<workspace>/work/agent_max_upper/correspondances.tsv"), delimiter='\t'))
for r in csv.DictReader(open("<workspace>/work/agent_conv_max/correspondances_complement.tsv"), delimiter='\t'):
    rows.append(r)
out = []; c = collections.Counter()
for r in rows:
    va = r.get('va_mips_instr') or r.get('va_mips') or ''
    try: va = int(va, 16)
    except ValueError: out.append((r['arcade'], r.get('nom', ''), '', '', 'sans va', '', '', '')); c['sans va'] += 1; continue
    f5 = AT.fstart('ro5', va); inv = INV[f5]
    h = H.homologue('ro5', va, 'ro9')
    va9 = h['va_dst'] if h else None
    p9 = inv['partenaire']
    cl = inv['classe']
    e9 = BA9['etat'].get(AT.fstart('ro9', va9)) if va9 else None
    k = cl if cl in ('identique', 'identique 68K', 'deplacements') else ('proche (%s)' % cl)
    c[k] += 1
    out.append((r['arcade'], r.get('nom', '')[:60], '0x%X' % va, '0x%X' % f5, cl, '0x%X' % p9 if p9 is not None else '',
                '0x%X' % va9 if va9 else '', e9 or ''))
with open(os.path.join(OUT, "max_vers_hyper.tsv"), "w") as fo:
    fo.write("arcade\tnom\tva_ro5\troutine_ro5\tclasse_ro5_vers_ro9\troutine_ro9\tva_ro9_alignee\tetat_ro9_vs_ro5\n")
    for o in out: fo.write('\t'.join(o) + '\n')
print(len(out), "adresses ;", dict(c))
