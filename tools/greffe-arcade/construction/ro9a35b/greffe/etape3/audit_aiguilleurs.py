#!/usr/bin/env python3
"""audit_aiguilleurs.py CONSTRUCTION : routines d'Upper renvoyees a HYPER (hors equivalence prouvee, regle e) dont une
table de pointeurs de code (constante de donnees) ne correspond pas, entree par entree, a la table homologue d'Hyper
(meme position de constante dans l'homologue) : aiguilleur apparie a tort (ex. 0x2A300 -> 0x5DA40)."""
import os, sys, json, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etape2'))
import plan as PL
G = PL.G; c = sys.argv[1]
J = json.load(open(os.path.join(G, 'constructions', c, 'greffe.json')))
D = {int(k, 16): v for k, v in J['decisions'].items()}
n = 0
for f, d in sorted(D.items()):
    if d[0] != 'HYPER' or d[-1].startswith('e)') or d[-1].startswith('j)'): continue
    h = int(d[1], 16)
    if f not in PL.E5 or h not in PL.E9: continue
    c5 = [v for k, t, v in PL.consts(PL.ins(PL.b5, f, PL.E5[f])) if t == 'c' and PL.GR.classe_valeur(v, PL.GR.H5) == 'data']
    c9 = [v for k, t, v in PL.consts(PL.ins(PL.b9, h, PL.E9[h])) if t == 'c' and PL.GR.classe_valeur(v, PL.GR.H9) == 'data']
    for i, v in enumerate(c5):
        P = PL.ptrs_code(v)
        if not P: continue
        w = c9[i] if i < len(c9) else None
        bad = []
        for o, q in P[:16]:
            dq = D.get(q)
            hq = struct.unpack_from('<I', PL.b9, w - PL.BASE + o)[0] - PL.BASE if w else None
            ok = dq is not None and dq[0] in ('HYPER', 'NATIF') and len(dq) > 1 and dq[1].startswith('0x') and int(dq[1], 16) == hq
            if not ok: bad.append('%x->%s/%s' % (q, dq[0] if dq else '-', hex(hq) if hq is not None else '-'))
        if bad:
            n += 1; print('0x%X -> 0x%X (%s) table 0x%X / %s : %d/%d entrees differentes : %s' % (f, h, d[-1], v, hex(w) if w else '-', len(bad), len(P[:16]), ' '.join(bad[:5])))
print(n, 'tables suspectes')
