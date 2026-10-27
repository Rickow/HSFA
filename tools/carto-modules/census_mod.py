#!/usr/bin/env python3
"""Recensement du traducteur (census.census, lecture seule de l'outillage) sur les ZONES 68K du module
(zones.py : le Z80 est exclu ou qu'il soit). Usage : nice -n 19 python3 census_mod.py roN > census_roN.txt
mips.CODE0 est abaisse a 0x40 quand du 68K precede le Z80 (ro1, ro6, ro7) : sinon les tables de sauts visant
ce code sont rejetees par read_jump_table."""
import os, sys, collections, time
mod = sys.argv[1]
os.environ['MODULE'] = mod
sys.path.insert(0, '<workspace>/scripts/untranspile')
import zones as Zm
Z = Zm.zones(mod)
import mips
if Z['m68k'][0][0] < mips.CODE0: mips.CODE0 = 0x40
import census, translate
buf = open(census.RO3, 'rb').read()
BASES = {'ro1': 0x60, 'ro2': 0x80, 'ro4': 0x80, 'ro6': 0x80, 'ro7': 0x66, 'ro8': 0x80, 'ro3': 0x90, 'ro5': 0xa0, 'ro9': 0xb8}
if os.environ.get('RAMFIX') == '1': translate._RAM_CACHE[bytes(buf[:32])] = BASES[mod]   # base mesuree (lui+addu, table b)
H = collections.Counter(); M = collections.Counter(); t0 = time.time()
per = []
for a0, a1 in Z['m68k']:
    h1 = collections.Counter(); m1 = collections.Counter(); x = a0
    while x < a1:
        h, mi = census.census(buf, x, min(x + census.CHUNK, a1)); h1 += h; m1 += mi; x += census.CHUNK
    per.append((a0, a1, sum(h1.values()), sum(m1.values()))); H += h1; M += m1
th = sum(H.values()); tm = sum(M.values())
print("module %s ; zones 68K %s ; RAM_HI %#x (ram_hi_of) ; %.0f s" % (mod, ' '.join('%x-%x' % ab for ab in Z['m68k']),
      translate.ram_hi_of(buf), time.time() - t0))
if census.ERREURS: print("!!! %d TRANCHES EN ERREUR : %s" % (len(census.ERREURS), census.ERREURS[:5]))
for a0, a1, h, m in per: print("  zone %x-%x : %d points, %.1f %% traduits" % (a0, a1, h + m, 100 * h / max(1, h + m)))
print("points d'effet : %d   traduits : %d (%.1f%%)   MANQUES : %d (%.1f%%)\n" % (th + tm, th, 100 * th / max(1, th + tm), tm, 100 * tm / max(1, th + tm)))
for k, c in M.most_common(25):
    h = H.get(k, 0)
    print("%-18s %-26s %8d %8d %6.0f%% %6.1f%%" % (k[0], k[1], c, h, 100 * h / (c + h), 100 * c / tm))
