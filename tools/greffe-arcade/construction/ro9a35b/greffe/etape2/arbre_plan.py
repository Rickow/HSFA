import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as PL
rs = [int(x, 16) for x in os.environ.get("RACINES", "4E1C0,24EA30,261560").split(',')]
import force as FO
P = PL.ferme(rs, FO.FORCE)
# taille du sous-arbre greffe attribue a chaque routine (par premier parent)
enf = collections.defaultdict(list)
for f in P.greffe:
    if f in P.parent: enf[P.parent[f][0]].append(f)
def tot(f, vu=set()):
    if f in vu: return 0
    vu.add(f); return (PL.E5[f] - f) + sum(tot(c, vu) for c in enf[f])
def montre(f, prof, maxp):
    t = tot(f, set())
    if t < int(os.environ.get("MIN", "3000")) or prof > maxp: return
    l = PL.BY.get(f)
    print("%s0x%06X %6d o (soi %5d) %-40s %s %s" % ('  ' * prof, f, t, PL.E5[f] - f, P.raison[f][:40], P.parent.get(f, ('', ''))[1], (l['zone'][:22]) if l else '-'))
    for c in sorted(enf[f], key=lambda c: -tot(c, set())): montre(c, prof + 1, maxp)
for r in rs: montre(r, 0, int(os.environ.get("PROF", "8")))
