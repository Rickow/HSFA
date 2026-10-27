"""Image audiocpu CPS2 au format de la region MAME, pour pilote.py et mesure_boucles.py.

.01 -> 0x0000 (32 Ko) puis 0x10000 (reste) ; .02 -> 0x28000.
Usage : image_z80.py jeu.01 [jeu.02] sortie.bin   (ex. sz2.01a sz2.02a sfa2.bin ; sfx.01 sfx.02 ssf2t.bin)
"""
import sys
r1 = open(sys.argv[1], 'rb').read(); r2 = open(sys.argv[2], 'rb').read() if len(sys.argv) > 3 else b''
out = sys.argv[-1]
img = bytearray(0x50000)
img[0:0x8000] = r1[:0x8000]; img[0x10000:0x10000 + len(r1) - 0x8000] = r1[0x8000:]
if r2: img[0x28000:0x28000 + len(r2)] = r2
open(out, 'wb').write(img)
