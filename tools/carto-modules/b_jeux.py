#!/usr/bin/env python3
"""Decode la table des jeux du menu b (b_usa_prog68k.bin, base d'execution 0x1C8000) : par jeu, 45 mots :
nom, 1, son (2 = Z80/QSound charges, 0 = son natif PS2), entree X_DATA du programme MWo3, adresse libre
(= base RAM 68K + 0x64000), 12 emplacements de 12 octets (u16 type, u16 entree X_DATA, adr1, adr2), puis
entree TIM2, 0, adresse, point d'entree (exec)."""
import struct, csv
B = 0x1C8000
d = open('<workspace>/anthology_extract/decompressed/b_usa_prog68k.bin', 'rb').read()
man = {int(r['idx']): r for r in csv.DictReader(open('<workspace>/anthology_extract/manifest.csv'))}
def cstr(p):
    o = p - B; return d[o:d.index(b'\0', o)].decode()
o = 0x13690; recs = []
while True:
    w = struct.unpack_from('<45I', d, o)
    if not (B <= w[0] < B + len(d)): break
    nom = cstr(w[0])
    ent = []
    for k in range(12):
        t, a1, a2 = struct.unpack_from('<III', d, o + 20 + 12 * k)
        ent.append((t & 0xffff, t >> 16, a1, a2))
    tim, z, adr, pe = struct.unpack_from('<4I', d, o + 20 + 144)
    recs.append((o, nom, w[1], w[2], w[3], w[4], ent, tim, adr, pe))
    o += 180
for o, nom, un, son, prog, libre, ent, tim, adr, pe in recs:
    print('%05x  %-28s son=%d  programme e%d (%s, %s o)  adresse libre 0x%X (base RAM 68K 0x%X)  TIM2 e%d -> 0x%X  entree exec 0x%X' % (
        o, nom, son, prog, man[prog]['name'], man[prog]['size'], libre, libre - 0x64000, tim, adr, pe))
    for k, (ty, ix, a1, a2) in enumerate(ent):
        if ty or ix or a1:
            print('      emplacement %2d : type %d  %-6s %-5s %8s o  -> 0x%07X  0x%07X' % (
                k, ty, ('e%d' % ix) if ix else '(vide)', man[ix]['kind'] if ix else '', man[ix]['size'] if ix else '', a1, a2))
