#!/usr/bin/env python3
"""Zones du code d'un module : Z80 recompile (banc 0x7000_10xx) et 68K recompile (banc 0x7000_11xx).
Le Z80 n'est PAS toujours en tete (ro1 : au milieu, ro6 : a la fin, ro7 : apres 0x2200) ; les outils supposent
CODE0 = 0x22B00 (mips.py) -> zones calculees ici."""
import sys, functools
sys.path.insert(0, '<workspace>/work/carto_modules')
import commun as C

@functools.lru_cache(None)
def zones(mod):
    L = C.instrs(mod); e = C.header(mod)['code_end']
    z = []; k = []
    for i in range(1, len(L)):
        p, x = L[i-1], L[i]
        if p.m == 'lui' and p.imm == 0x7000 and x.rs == p.rt:
            if 0x1000 <= x.imm < 0x1040: z.append(x.va)
            elif 0x1100 <= x.imm < 0x1160: k.append(x.va)
    if not z: return dict(z80=None, m68k=[(0x40, e)], acces_z80=0, acces_68k=len(k))
    z0, z1 = z[0], z[-1]
    avant = [a for a in k if a < z0]; apres = [a for a in k if a > z1]
    pro = [x.va for x in L if x.m == 'addiu' and x.rs == 29 and x.rt == 29 and x.simm < 0]
    import bisect
    # debut du Z80 : dernier prologue <= z0 (et apres le dernier acces 68K qui precede)
    i = bisect.bisect_right(pro, z0) - 1
    zs = pro[i] if i >= 0 else 0x40
    if avant and zs <= avant[-1]: zs = avant[-1] + 4
    # fin du Z80 : premier prologue > z1
    j = bisect.bisect_right(pro, z1)
    ze = pro[j] if j < len(pro) else e
    m = []
    if avant: m.append((0x40, zs))
    if apres: m.append((ze, e))
    return dict(z80=(zs, ze), m68k=m, acces_z80=len(z), acces_68k=len(k))

if __name__ == '__main__':
    for mod in sys.argv[1:] or ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
        Z = zones(mod)
        print(mod, 'Z80 %x-%x' % Z['z80'], '68K', ' '.join('%x-%x' % ab for ab in Z['m68k']),
              'taille 68K %d o' % sum(b - a for a, b in Z['m68k']))
