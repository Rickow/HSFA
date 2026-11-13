#!/usr/bin/env python3
"""ecrit donnees/greffe_v2.pkl : liste des routines greffees du plan (pour relogement_a5_v2.py)"""
import os, sys, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as PL, force as FO
rac = [int(x, 16) for x in os.environ.get("RACINES", "4E1C0,24EA30,261560,2614A0,2614D0,261500,1346A0").split(',')]
TC = PL.tables_a_completer()
P = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FO.FORCE)
pickle.dump(P.greffe, open(os.path.join(PL.G, 'donnees', 'greffe_v2.pkl'), 'wb'))
print(PL.resume(P))
