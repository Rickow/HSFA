#!/usr/bin/env python3
"""routines d'Upper executees dans un etat (trace Upper) dont NI la copie greffee NI l'homologue d'Hyper n'ont ete
executes par ro9a dans le meme etat (sans tenir compte des decisions). Usage : couv_manque.py CONS T9 T5 "etat" """
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import couv_ro9a as CR, plan as PL
cons, t9, t5, etat = sys.argv[1:5]
R9, J = CR.charge_ro9a(cons, t9)
vu = {r for r, e in R9.items() if etat in e}
R5, _, _ = CR.CV.charge('ro5', t5)
dec = {int(f, 16): d for f, d in J['decisions'].items()}
P = PL.ferme([0x4E1C0], {})  # pour homologue()
out = []
for r, e in R5.items():
    if etat not in e['etats']: continue
    h = PL.homologue(r)
    ok = ('U', r) in vu or (h is not None and ('H', h) in vu)
    if not ok: out.append((e['etats'][etat], r, h, dec.get(r)))
for fr, r, h, d in sorted(out):
    l = PL.BY.get(r)
    print("%6d 0x%06X hom %-9s %-30s %s" % (fr, r, ('0x%X' % h) if h else '-', ' '.join(d) if d else '', (l['zone'][:30]) if l else ''))
