#!/usr/bin/env python3
"""octets68k.py DOSSIER_B9 ADRESSE68K [N_MOTS] : mots 68K servis a cette adresse par les blocs ext_<adr>.bin du dossier"""
import sys, os, glob, struct
d = sys.argv[1]; a = int(sys.argv[2], 16); n = int(sys.argv[3]) if len(sys.argv) > 3 else 16
for f in glob.glob(os.path.join(d, 'ext_*.bin')):
    base = int(os.path.basename(f)[4:-4], 16); b = open(f, 'rb').read()
    if base <= a < base + len(b):
        print(' '.join('%04x' % struct.unpack_from('>H', b, a - base + 2 * i)[0] for i in range(n))); break
else: print('hors des blocs')
