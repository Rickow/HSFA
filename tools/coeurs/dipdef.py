#!/usr/bin/env python3
# dipdef.py <ancien> <nouveau> : compte les listes DIP qui commencent par DIP_OFFSET(0x1d) puis l'octet par defaut
# {0x00, 0xff, 0xff, XX, NULL} (BurnDIPInfo = INT32, 3 x UINT8, pointeur : 12 octets en 32 bits, 16 en 64 bits ;
# pointeurs nuls dans le fichier) pour XX = c1 c2 c9 ca.
# Attendu entre le lot du 05/11 et celui du 06/11 : aucun changement (0023 ne touche pas aux DIP) ; c9/ca = Blood rouge
# (bit 2 a 0) et Skip idle loops On (bit 3 a 1).
import sys
def compte(f):
    b = open(f, 'rb').read()
    ptr = 8 if b[4] == 2 or b[:2] == b'MZ' else 4         # ELF64 / PE32+ : 8 ; ELF32 : 4
    t = 16 if ptr == 8 else 12
    r = {}
    for x in (0xc1, 0xc2, 0xc9, 0xca):
        n = 0; i = b.find(b'\x1d\0\0\0\xf0\xff\xff')
        while i >= 0:
            e = b[i + t:i + t + 7]
            if i % ptr == 0 and b[i + 8:i + t] == bytes(t - 8) and e == bytes([0, 0, 0, 0, 0xff, 0xff, x]) and b[i + t + 8:i + 2 * t] == bytes(t - 8): n += 1
            i = b.find(b'\x1d\0\0\0\xf0\xff\xff', i + 1)
        r['%02x' % x] = n
    return r
a, n = compte(sys.argv[1]), compte(sys.argv[2])
d = {k: n[k] - a[k] for k in a}
ok = d == {'c1': 0, 'c2': 0, 'c9': 0, 'ca': 0} and n['c9'] + n['ca'] > 0 and n['c1'] + n['c2'] == 0
print('defauts DIP ref %s -> lot %s : %s' % (a, n, 'OK (inchanges : Blood Red, Skip idle loops On)' if ok else 'ECART %s' % d))
