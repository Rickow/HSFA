#!/usr/bin/env python3
"""ptr_anim.py CONSTRUCTION MOT_HAUT MOT_BAS : suit un pointeur d'animation (champ $1C d'un objet, 68K, moities
echangees) dans le bloc de la greffe : adresse d'Upper d'origine, contenu copie et contenu d'Upper."""
import json, struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import donnees2 as D2
G = "<workspace>/work/greffe_arcade"
cons = sys.argv[1]; w1, w2 = int(sys.argv[2], 16), int(sys.argv[3], 16)
J = json.load(open(os.path.join(G, 'constructions', cons, 'greffe.json')))
blob = open(os.path.join(G, 'constructions', cons, 'greffe_donnees.bin'), 'rb').read()
GY = int(J['grf_y'], 16); GX = 0xDB0000
def up(o):
    for a, b, off in J['regions']:
        a, b, off = int(a, 16), int(b, 16), int(off, 16)
        if off <= o < off + (b - a): return a + o - off
v = ((w2 << 16) | w1) & 0xffffff
print("68K $%06x" % v)
# (etape 7) disposition par fenetres (env.sh : HSFA_GREFFE_FEN = ps2_lo:ps2_hi:68k_base,...) : 68K -> PS2 -> bloc
FEN = []
for l in open(os.path.join(G, 'constructions', cons, 'env.sh')):
    m = __import__('re').search(r'HSFA_GREFFE_FEN=([0-9a-f:,]+)', l)
    if m: FEN = [tuple(int(x, 16) for x in f.split(':')) for f in m.group(1).split(',')]
    m = __import__('re').search(r'HSFA_GREFFE_X=([0-9a-f]+)', l)
    if m: GX = int(m.group(1), 16)
o = None
for lo, hi, y in FEN:
    if y <= v < y + (hi - lo): o = lo + v - y - GX; print(" PS2 0x%X" % (lo + v - y))
if o is None and not FEN and GY <= v < GY + len(blob): o = v - GY
if o is not None and 0 <= o < len(blob):
    u = up(o)
    print(" bloc +%x = Upper 0x%X" % (o, u or 0))
    print("  copie : %s" % [hex(x) for x in struct.unpack_from('<4I', blob, o)])
    if u: print("  Upper : %s" % [hex(x) for x in struct.unpack_from('<4I', D2.octets(u, 16), 0)])
