"""Données de décor de SFA2 arcade (sfa2u, vidage MAME carto_sfa2/dump/sfa2u/prog_donnees.bin) — format arcade natif.
Adresses : CARTE-sfa2.md §2.2 (vérifiées par désassemblage, voir format/FORMAT.md)."""
import struct
PROG = "<workspace>/work/carto_sfa2/dump/sfa2u/prog_donnees.bin"
OPC = "<workspace>/work/carto_sfa2/dump/sfa2u/prog_opcodes.bin"
D = open(PROG, "rb").read()
O = open(OPC, "rb").read()          # espace opcodes (tables lues en (d,PC) sous $100000)
T = dict(type1=0x1CFC4, list1=0x1CFF4, type2=0x1D0BC, list2=0x1D0EC, type3=0x1D274, list3=0x1D2A4,
         b1=0x2AD300, st1=0x2B1A80, b2=0x2D1F00, b3=0x2F8700, add2=-0x5C00, add3=0x900,
         pal1=0x27C1C0, pal2=0x2865C0, pal3=0x2909C0, palspr=0x275C40,
         cpsb=0x1C34A, longs1=0x1C4D4, ordre=0x1A81C, h1=0x1A8AA, h2=0x1B1FC, h3=0x1B842, effet=0x1D842,
         objets=0x1EB66, musique=0x154EE)
NLIST = {1: 8, 2: 16, 3: 64}
def w(a, d=D): return struct.unpack_from(">H", d, a)[0]
def ws(a, d=D): return struct.unpack_from(">h", d, a)[0]

def liste(L, dec):
    """-> (type, numéros de blocs) ; dec = valeur de $100 (décor x 2)"""
    t = D[T["type%d" % L] + dec + 1]
    tl = T["list%d" % L]
    a = tl + w(tl + dec)
    n = (8 if t else 4) if L == 1 else NLIST[L]
    return t, list(D[a:a + n]), a

def bloc(L, n):
    """-> {(col, rang): (code VRAM (constante ajoutée), attr)} ; scroll1 : cellules 4x4 de tuiles 8x8"""
    out = {}
    if L == 1:
        a = T["b1"] + n * 0x80
        for k in range(64):
            st = w(a + 2 * k); scol, srow = k >> 3, k & 7
            s = T["st1"] + st * 0x40
            for j in range(16):
                out[(scol * 4 + (j >> 2), srow * 4 + (j & 3))] = (w(s + 4 * j), w(s + 4 * j + 2), st)
        return out
    nb = 256 if L == 2 else 64; sh = 4 if L == 2 else 3; msk = (1 << sh) - 1
    a = T["b%d" % L] + n * nb * 4
    add = T["add%d" % L]
    for k in range(nb):
        out[(k >> sh, k & msk)] = ((w(a + 4 * k) + add) & 0xFFFF, w(a + 4 * k + 2))
    return out

def cases(L, dec):
    t, lst, _ = liste(L, dec)
    out = {}
    if L == 1:
        nc = 4 if t == 2 else 2
        for p, n in enumerate(lst):
            bx, by = p % nc, p // nc
            for (c, r), v in bloc(1, n).items(): out[(bx * 32 + c, by * 32 + r)] = v
        return out
    nc = 4 if L == 2 else 8; nt = 16 if L == 2 else 8
    for p, n in enumerate(lst):
        bx, by = p % nc, p // nc
        for (c, r), v in bloc(L, n).items(): out[(bx * nt + c, by * nt + r)] = v
    return out

def palettes(L, dec):
    """32 palettes x 16 mots (0RGB, luminosité 0 : copiées telles quelles par SFA2)"""
    a = T["pal%d" % L] + (dec >> 1) * 0x400
    return [[w(a + 32 * p + 2 * c) for c in range(16)] for p in range(32)]
