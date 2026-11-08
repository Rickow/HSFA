#!/usr/bin/env python3
"""(banc_coups) recalcule l'etape « coups » de banc_max sans MAME : recompare_max.py <etiquette candidat>"""
import glob, os, subprocess, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
et = sys.argv[1]
for d in sorted(glob.glob(os.path.join(B, 'essais', 'max_' + et, 'coups', '*_?'))):
    pv = os.path.basename(d); p, v = pv.rsplit('_', 1)
    refs = glob.glob(os.path.join(B, 'essais', 'max_ref', 'coups_%s_%s_*' % (p, v), 'log.txt'))
    cand = os.path.join(d, 'cand', 'log.txt')
    if not refs or not os.path.exists(cand):
        continue
    perso = open(os.path.join(d, 'index.tsv')).readlines()[1].split('\t')[3]
    r = subprocess.run(['python3', os.path.join(B, 'outils', 'compare_strict.py'), '--index', os.path.join(d, 'index.tsv'),
                        '--ref', refs[0], '--cand', cand, '--sortie', os.path.join(B, 'resultats_max', et, 'coups_%s.tsv' % pv),
                        '--etiquette', '%s %s' % (perso, v)], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-200:])
subprocess.run(['python3', os.path.join(B, 'outils', 'resume_max.py'), os.path.join(B, 'resultats_max', et)])
