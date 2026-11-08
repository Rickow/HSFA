import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as PL
rs = [int(x, 16) for x in os.environ.get("RACINES", "4E1C0,24EA30,261560").split(',')]
import force as FO
P = PL.ferme(rs, FO.FORCE)
atteint = set(P.atteint) | P.refs
for f in sorted(atteint):
    d = P.dec[f]; l = PL.BY.get(f)
    print("0x%06X %-8s %-9s %-42s %5d %s" % (f, d[0], ('0x%X' % d[1]) if len(d) > 1 and d[1] is not None else '', P.raison[f], PL.E5[f] - f,
          (l['zone'][:25] + ' ' + str(l['k0'])) if l else '-'))
