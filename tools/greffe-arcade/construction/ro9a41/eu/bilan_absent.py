#!/usr/bin/env python3
"""Code d'Upper absent d'Hyper (couverture K=12 < 50 %), modifie (50-90 %), present (>= 90 %) :
par zone de la ROM arcade (alignement Upper <-> arcade) et par sous-arbre de scene (graphe sans grandes tables).
Ecrit upper_absent.tsv (routines < 50 %) et bilan_absent.pkl."""
import os, pickle, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
CV = pickle.load(open(os.path.join(OUT, "couv_k.pkl"), "rb")); V = pickle.load(open(os.path.join(OUT, "va_arcade.pkl"), "rb"))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb")); Z = pickle.load(open(os.path.join(OUT, "zones_upper_petit.pkl"), "rb"))
A = pickle.load(open(os.path.join(OUT, "a5.pkl"), "rb")); D5, D9 = A['D5'], A['D9']
T5 = AT.taille('ro5')
par_r = collections.defaultdict(set)
for d in set(D5) - set(D9):
    for r in D5[d]['routines']: par_r[r].add(d)
BINS = [(0, 0x4000, 'noyau'), (0x4000, 0x8000, 'intro/attraction $4000-$7FFF'), (0x8000, 0xE000, 'flux de jeu $8000-$DFFF'),
        (0xE000, 0x1C000, 'systeme/affichage $E000-$1BFFF'), (0x1C000, 0x1E000, 'objets (moteur) $1C000-$1DFFF'),
        (0x1E000, 0x20000, 'selection $1E000-$1FFFF'), (0x20000, 0x34000, 'moteur de combat $20000-$33FFF'),
        (0x34000, 0x80000, 'code des persos $34000-$7FFFF'), (0x80000, 0xC0000, 'objets/effets/ecrans $80000-$BFFFF')]
def zone(a):
    v = V.get(a)
    if not v: return 'sans alignement (propre a Upper ou au portage)'
    for lo, hi, l in BINS:
        if lo <= v[2] < hi: return l
    return '?'
def etat(a):
    c = CV.get(a, 1.0)
    return 'absent' if c < 0.5 else ('modifie' if c < 0.9 else 'present')
arc = set().union(*(Z['res'][k] for k in ('scene 6', 'scene 8', 'scene A', 'scene C')))
def scene(a):
    if a in arc: return 'arcade 6/8/A/C'
    if a in Z['res']['scene 4 VS/combat']: return 'scene 4'
    if a in Z['res']['scene 2 selection']: return 'scene 2'
    if a in Z['res']['scene E resultat (C)'] or a in Z['res']['scene 0 init']: return 'scene E/0'
    return 'autre'
tab = collections.defaultdict(lambda: collections.Counter())
for a in T5:
    if INV[a]['nat']: continue
    e = etat(a); tab[zone(a)][e] += T5[a]; tab[zone(a)][e + '_n'] += 1; tab[zone(a)][e + '_i'] += INV[a]['n68']
print("%-48s %22s %22s %12s" % ("zone arcade", "ABSENT <50 % (o / rout. / instr.)", "modifie 50-90 % (o)", "present (o)"))
tot = collections.Counter()
for z in [b[2] for b in BINS] + ['sans alignement (propre a Upper ou au portage)']:
    t = tab[z]; tot.update(t)
    print("%-48s %8d / %4d / %5d %12d %14d" % (z, t['absent'], t['absent_n'], t['absent_i'], t['modifie'], t['present']))
print("%-48s %8d / %4d / %5d %12d %14d" % ("TOTAL", tot['absent'], tot['absent_n'], tot['absent_i'], tot['modifie'], tot['present']))
sc = collections.defaultdict(collections.Counter)
for a in T5:
    if INV[a]['nat'] or etat(a) != 'absent': continue
    s = scene(a); sc[s][zone(a)] += T5[a]; sc[s]['_tot'] += T5[a]
print("\nabsent par sous-arbre de scene :")
for s, c in sc.items(): print("  %-16s %7d o : %s" % (s, c['_tot'], ', '.join('%s %d' % (k.split(' $')[0], v) for k, v in c.most_common() if k != '_tot')))
with open(os.path.join(OUT, "upper_absent.tsv"), "w") as f:
    f.write("routine_ro5\ttaille\tn68\tcouverture\tzone_arcade\tarcade_med\tscene\tvar_A5_upper_seul\n")
    for a in sorted(T5):
        if INV[a]['nat'] or etat(a) != 'absent': continue
        f.write("0x%X\t%d\t%d\t%.2f\t%s\t%s\t%s\t%s\n" % (a, T5[a], INV[a]['n68'], CV[a], zone(a), ('$%X' % V[a][2]) if a in V else '', scene(a),
                ' '.join('$%04X' % d for d in sorted(par_r[a]))))
pickle.dump(dict(etat={a: etat(a) for a in T5}, zone={a: zone(a) for a in T5}, scene={a: scene(a) for a in T5}), open(os.path.join(OUT, "bilan_absent.pkl"), "wb"))
