#!/usr/bin/env python3
"""DONNEES DE DECOR de SFA3 arcade (sfa3ud, programme 68000) : listes de blocs par decor et bibliotheques de blocs.

Etabli par desassemblage (reimport/re/dis.sh) — cf. REIMPORT.md §5 :
  decor d = $100(A5) (mot, = decor*2 = valeur de $FF8100)
  scroll1 : type      = octet [$19106 + d + 1] (0 = 4 blocs statiques ; 1/2 = anneau compose selon la camera)
            liste     = $19146 + mot[$19146 + d]  (4 ou 8 octets = numeros de blocs ; type 2 : grille 4 x 2 blocs,
                        indice = colonne + 4*rangee, colonne = (tx >> 8) & 3, rangee = (ty >> 8) & 1)
            bloc n    = $367494 + n*$80 : 64 mots = indices de SUPER-TUILES, colonne par colonne (8 x 8 super-tuiles)
            super-tuile i = $36A394 + i*$40 : 16 x (code, attr) mots, colonne par colonne (4 x 4 tuiles 8 px)
  scroll2 : liste     = $19272 + mot[$19272 + d] (16 octets, 4 x 4 blocs de 256 px, rangee par rangee)
            bloc n    = $391014 + n*$300 : 256 mots code (+$6C00) puis 256 octets attr ; entree k : col k>>4, rang k&15
  scroll3 : liste     = $194A2 + mot[$194A2 + d] (64 octets, 8 x 8 blocs de 256 px)
            bloc n    = $3AC614 + n*$C0 : 64 mots code (+$B00) puis 64 octets attr ; entree k : col k>>3, rang k&7
  Sites des bases (lea abs.L, operande a l'adresse indiquee) : voir SITES.
"""
import struct

PROG = "<workspace>/work/cps2/sfa3ud_prog.bin"
T1_TYPE, T1_LIST, T2_LIST, T3_LIST = 0x19106, 0x19146, 0x19272, 0x194A2
B1, ST1, B2, B3 = 0x367494, 0x36A394, 0x391014, 0x3AC614
TAILLE = {1: 0x80, 2: 0x300, 3: 0xC0}
ADD = {2: 0x6C00, 3: 0xB00}
# operandes (adresse du long) des « lea base.L » dans le code arcade
SITES = {"bloc1": [0x18B2A, 0x18C34, 0x18CCC, 0x18CE6], "st1": [0x18BE6, 0x18C74, 0x18CFA],
         "bloc2": [0x18F30], "bloc3": [0x190E2]}
# tables de decalages (camera -> colonne/ligne a composer) de l'anneau scroll1 : (D2, D3) par sens, $18BA6
ANNEAU_DECALAGES = 0x18BA6


def w(d, a): return struct.unpack_from(">H", d, a)[0]


def liste(d, L, dec):
    """numeros de blocs du decor (dec = $100(A5), ex. $0C)"""
    if L == 1:
        t = d[T1_TYPE + dec + 1]; a = T1_LIST + w(d, T1_LIST + dec)
        return t, list(d[a:a + (8 if t else 4)]), a
    tl = T2_LIST if L == 2 else T3_LIST
    a = tl + w(d, tl + dec)
    return 0, list(d[a:a + (16 if L == 2 else 64)]), a


def bloc(d, L, n, base=None):
    """-> {(col, rang) relatifs au bloc (en tuiles du plan): (code, attr)}"""
    out = {}
    if L == 1:
        a = (base or B1) + n * 0x80
        for k in range(64):
            st = w(d, a + 2 * k); scol, srow = k >> 3, k & 7
            s = ST1 + st * 0x40
            for j in range(16):
                out[(scol * 4 + (j >> 2), srow * 4 + (j & 3))] = (w(d, s + 4 * j), w(d, s + 4 * j + 2))
        return out
    a = (base or (B2 if L == 2 else B3)) + n * TAILLE[L]
    nb = 256 if L == 2 else 64; sh = 4 if L == 2 else 3
    for k in range(nb):
        out[(k >> sh, k & (nb // (1 << sh) * 0 + (15 if L == 2 else 7)))] = ((w(d, a + 2 * k) + ADD[L]) & 0xFFFF, d[a + 2 * nb + k])
    return out


def cases_tilemap(d, L, dec):
    """{(col, rang) tilemap (deroule pour scroll1 : 128 x 64 tuiles = monde 1024 x 512) : (code, attr)}"""
    t, lst, _ = liste(d, L, dec)
    out = {}
    if L == 1:
        nc = 4 if t == 2 else 2 if t == 1 else 2
        for p, n in enumerate(lst):
            bx, by = p % nc, p // nc
            for (c, r), v in bloc(d, 1, n).items():
                out[(bx * 32 + c, by * 32 + r)] = v
        return out
    nc = 4 if L == 2 else 8; nt = 16 if L == 2 else 8
    for p, n in enumerate(lst):
        bx, by = p % nc, p // nc
        for (c, r), v in bloc(d, L, n).items():
            out[(bx * nt + c, by * nt + r)] = v
    return out


# ---------------- palettes de decor (routines $1FC38/$1FC54/$1FC70, copie $1FD9C : 32 palettes, or.l #$F000F000) ----
PAL_TABLE = {1: 0x33C474, 2: 0x340954, 3: 0x3477B4}     # mot signe [table + decor*2] -> bloc 0RGB de 32 o / palette


def palettes_bloc(d, L, dec):
    """-> (adresse du bloc du decor, nombre de palettes PROPRES au bloc = distance au bloc suivant de la table / 32).
    La routine copie TOUJOURS 32 palettes : au-dela du bloc propre, ce sont les palettes d'un autre decor."""
    t = PAL_TABLE[L]
    cibles = sorted({t + struct.unpack_from(">h", d, t + 2 * i)[0] for i in range(32)})   # 32 decors
    a = t + struct.unpack_from(">h", d, t + dec)[0]
    suiv = [x for x in cibles if x > a]
    n = (min(suiv) - a) // 32 if suiv else 32
    return a, min(32, n)
