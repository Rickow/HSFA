#!/usr/bin/env python3
"""(banc_coups) recalcule les verdicts d'un module a partir des journaux deja produits (sans relancer MAME) :
recompare.py <module>"""
import subprocess, glob, os, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mod = sys.argv[1]
for d in sorted(glob.glob(B + '/essais/%s/*_*' % mod)):
    n = os.path.basename(d); p, v = n.rsplit('_', 1)
    tr = d + '/%s/log.txt' % mod
    if not os.path.exists(tr):
        continue
    refs = glob.glob(B + '/essais/cache_arcade/%s_%s_*/log.txt' % (p, v))
    cmd = ['python3', B + '/outils/compare.py', '--index', d + '/index.tsv', '--tr', tr, '--module', mod,
           '--sortie', B + '/resultats/%s/%s.tsv' % (mod, n)]
    if refs and not (mod == 'ro9' and not v.startswith('Z3')) and not (mod == 'ro5' and p in ('Juli', 'Juni')):
        cmd += ['--ref', refs[0]] + (['--famille'] if mod == 'ro9' else [])
    print(n, subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
subprocess.run(['python3', B + '/outils/tableau.py'])
