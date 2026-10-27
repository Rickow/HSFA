#!/usr/bin/env python3
"""Coeur a greffer = routines GREFFER de donnees/liste_arcade.pkl, attraction exclue (scenes toutes « hors partie »).
Ecrit donnees/coeur_greffe.pkl / .tsv et donnees/liste_arcade_zones.txt (resume)."""
import pickle, collections, os
G = "<workspace>/work/greffe_arcade"
L = pickle.load(open(os.path.join(G, 'donnees/liste_arcade.pkl'), 'rb'))
c = collections.Counter(); n = collections.Counter(); i = collections.Counter(); core = []
for l in L['lignes']:
    if not l['decision'].startswith('GREFFER'): continue
    att = all(x.startswith('hors partie') for x in l['scenes'])
    k = ('attraction' if att else 'coeur', 'partagee VS' if l['vs'] else 'Arcade seule', l['etat'])
    c[k] += l['taille']; n[k] += 1; i[k] += l['n68']
    if not att: core.append(l)
out = []
for k in sorted(c): out.append("%-11s %-13s %-8s %4d routines %7d o (%5.1f Ko) %5d instr." % (k[0], k[1], k[2], n[k], c[k], c[k] / 1024, i[k]))
tc = sum(v for k, v in c.items() if k[0] == 'coeur')
out.append("coeur total : %d routines, %d o (%.1f Ko), %d instr." % (len(core), tc, tc / 1024, sum(v for k, v in i.items() if k[0] == 'coeur')))
open(os.path.join(G, 'donnees/liste_arcade_zones.txt'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
pickle.dump(sorted(l['r'] for l in core), open(os.path.join(G, 'donnees/coeur_greffe.pkl'), 'wb'))
with open(os.path.join(G, 'donnees/coeur_greffe.tsv'), 'w') as f:
    f.write("va_ro5\tetat_ro9\tclasse\tpartenaire_ro9\tvu_VERSUS_upper\ttaille_mips\tn68\tzone_arcade\tscenes\n")
    for l in sorted(core, key=lambda l: l['r']):
        f.write("0x%X\t%s\t%s\t%s\t%s\t%d\t%d\t%s\t%s\n" % (l['r'], l['etat'], l['classe'], ('0x%X' % l['part']) if l['part'] else '',
                'oui' if l['vs'] else 'non', l['taille'], l['n68'], l['zone'], ' | '.join(l['scenes'])))
