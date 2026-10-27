#!/usr/bin/env python3
"""compare_tables.py T5:T9[:N] ... : compare entree par entree une table de pointeurs de code d'Upper et son homologue
d'Hyper. Pour chaque entree : routine ro5, routine ro9, relation (meme routine par la correspondance, defaut / talon
dans Hyper, differente) ; somme des routines SUPPRIMEES dans Hyper atteintes (graphe sans grandes tables) depuis les
entrees retirees d'Hyper."""
import os, sys, pickle, struct, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb"))
CMP9 = pickle.load(open("<workspace>/work/carto_ro9/comparaison_ro9_routine.pkl", "rb"))
S = pickle.load(open(os.path.join(OUT, "supprimees.pkl"), "rb")); T5 = AT.taille('ro5')
VA = pickle.load(open(os.path.join(OUT, "va_arcade.pkl"), "rb"))
def lit(mod, ex, n):
    b = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, 'rb').read()
    return [struct.unpack_from('<I', b, ex - 0x1F0000 + 4 * k)[0] for k in range(n)]
for arg in sys.argv[1:]:
    p = arg.split(':'); t5, t9 = int(p[0], 16), int(p[1], 16)
    n5 = len(AT.G('ro5')['tables'].get(t5, [])) or 0
    n = int(p[2]) if len(p) > 2 else max(n5, len(AT.G('ro9')['tables'].get(t9, [])))
    e5, e9 = lit('ro5', t5, n), lit('ro9', t9, n)
    d9 = collections.Counter(e9).most_common(1)[0][0]
    rel = collections.Counter(); retires = []
    for k in range(n):
        a5 = e5[k] - 0x1F0000 if e5[k] else None; a9 = e9[k] - 0x1F0000 if e9[k] else None
        r5 = AT.fstart('ro5', a5) if a5 else None; r9 = AT.fstart('ro9', a9) if a9 else None
        if r5 is None: rel['vide ro5'] += 1; continue
        same = (r9 is not None) and (INV[r5]['partenaire'] == r9 or CMP9.get(r9, {}).get('ro5', {}).get('partenaire') == r5)
        if same: rel['meme'] += 1
        elif r9 is None or e9[k] == d9: rel['retire (defaut/vide dans Hyper)'] += 1; retires.append((k, r5))
        else: rel['different'] += 1; retires.append((k, r5))
    Rr = AT.reach('ro5', [r for k, r in retires], cle='petit') if retires else set()
    sup = Rr & S['supp']
    print("ro5 %x / ro9 %x (%d entrees, defaut ro9 %x) : %s" % (t5, t9, n, d9, dict(rel)))
    print("   supprimees atteintes depuis les entrees retirees/differentes : %d routines, %d o, %d instr. 68K" % (
        len(sup), sum(T5[a] for a in sup), sum(INV[a]['n68'] for a in sup)))
    print("   entrees : " + ' '.join("%x:%x(%s)" % (k, r, ('$%X' % VA[r][2]) if r in VA else '-') for k, r in retires[:60]))
