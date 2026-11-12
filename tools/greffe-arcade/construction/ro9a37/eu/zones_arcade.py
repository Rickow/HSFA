#!/usr/bin/env python3
"""Routines d'Upper supprimees dans Hyper, classees par zone de la ROM arcade (mediane des instructions alignees) :
  systeme / scenes < $1C000 ; moteur $1C000-$34000 ; persos $34000-$74000 ; $74000-$80000 ; objets / effets >= $80000 ;
  sans alignement (code propre a Upper : nouveaux persos, portage)."""
import os, pickle, collections
import atteint as AT
OUT = os.path.dirname(os.path.abspath(__file__))
S = pickle.load(open(os.path.join(OUT, "supprimees.pkl"), "rb")); VA = pickle.load(open(os.path.join(OUT, "va_arcade.pkl"), "rb"))
INV = pickle.load(open(os.path.join(OUT, "inverse_ro5.pkl"), "rb")); T5 = AT.taille('ro5')
def zone(a):
    v = VA.get(a)
    if not v: return 'sans alignement'
    m = v[2]
    if m < 0x1C000: return 'systeme/scenes <$1C000'
    if m < 0x34000: return 'moteur $1C000-$34000'
    if m < 0x74000: return 'persos $34000-$74000'
    if m < 0x80000: return '$74000-$80000'
    if m < 0xC0000: return 'objets/effets $80000-$C0000'
    return '>= $C0000'
Zs = ['systeme/scenes <$1C000', 'moteur $1C000-$34000', 'persos $34000-$74000', '$74000-$80000', 'objets/effets $80000-$C0000', '>= $C0000', 'sans alignement']
print("%-58s" % "groupe \\ zone arcade (o MIPS, routines supprimees)" + ''.join("%16s" % z[:15] for z in Zs))
for g, Sg in S['groupes'].items():
    c = collections.Counter(); n = collections.Counter()
    for a in Sg & S['supp']: z = zone(a); c[z] += T5[a]; n[z] += 1
    print("%-58s" % g[:58] + ''.join("%9d (%4d)" % (c[z], n[z]) for z in Zs))
pickle.dump({a: zone(a) for a in S['supp']}, open(os.path.join(OUT, "zones_arcade.pkl"), "wb"))
