#!/usr/bin/env python3
"""(e25) image 68K (4 Mo, gros-boutiste) d'un dossier de ROM sfa3ud/sfa3hx : image(dossier) ; mots(img, adr, n)"""
import os, struct, glob
NOMS = ['03c', '04c', '05c', '06c', '07c', '08c', '09c', '10b']
def image(d):
    out = bytearray()
    for n in NOMS:
        f = [x for x in glob.glob(os.path.join(d, '*.' + n))]
        f = [x for x in f if 'ud.' in x] or f
        b = open(f[0], 'rb').read()
        sw = bytearray(len(b)); sw[0::2] = b[1::2]; sw[1::2] = b[0::2]
        out += sw
    return bytes(out)
def mots(img, a, n=16): return ' '.join('%04x' % struct.unpack_from('>H', img, a + 2 * i)[0] for i in range(n))
if __name__ == '__main__':
    import sys
    im = image(sys.argv[1]); print(mots(im, int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 16))
