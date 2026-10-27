"""DONNEES DE DECOR du programme TRADUIT (fork sfa3hx / coeur FBNeo HSFA) : listes, bibliotheques de blocs, palettes.

Meme format que l'arcade (reimport/blocs.py, REIMPORT.md §5) avec deux differences :
  - les OCTETS (listes, attributs des blocs scroll2/3, type scroll1) sont ranges par paires echangees (memoire PS2
    petit-boutiste vue en mots gros-boutistes ; le code traduit lit l'octet k a l'adresse k^1) ; les MOTS sont en
    ordre naturel (codes, indices de super-tuiles, palettes 0RGB) ;
  - super-tuiles scroll1 : chaque entree est un LONG du portage, moities echangees : mot +0 = attribut, +2 = code ;
  - codes de tuiles LOCAUX a la memoire de decor du module (e256 pour SFA3 : scroll1 = indice 8x8, scroll2 = indice
    16x16 = mot du bloc + $1600 ; scroll3 = indice du conteneur 32x32 e312, sans ajout).
Adresses : image ro3 (carte_image.txt du 2026-10-10, md5 sz3ud.03c f2f46b7e...) ; ro5 d'apres REIMPORT.md §5.5.
Sites = adresse de l'INSTRUCTION « LEA abs.L,An » (carte_image.txt) ; l'operande long est a +2.
"""
import struct

MOD = {
    "ro3": dict(type1=0x18C9F0, list1=0x18CA30, list2=0x18CB5C, list3=0x18CD8C,
                b1=0x107670, st1=0x10A570, b2=0x12F7B0, b3=0x14ADB0, add2=0x1600, add3=0,
                pal={1: 0x1619D0, 2: 0x165EB0, 3: 0x16CD10},
                sites={"bloc1": [0x024EDA, 0x025012, 0x0250C4, 0x0250DC], "st1": [0x024FB0, 0x025058, 0x0250F0],
                       "bloc2": [0x025296], "bloc3": [0x02538A],
                       "liste1": [0x024DA2], "liste2": [0x0251EC], "liste3": [0x0252F2],
                       "pal1": [0x006366, 0x0065DA], "pal2": [0x006380, 0x0065F4], "pal3": [0x00639A, 0x00660E]},
                ndec=32),
    "ro5": dict(type1=0x1DE220, list1=0x1DE270, list2=0x1DE414, list3=0x1DE684,
                b1=0x131B70, st1=0x1356F0, b2=0x165930, b3=0x185730, add2=0x1C00, add3=0,
                pal=None, sites=None, ndec=40),       # palettes et sites de listes/palettes d'Upper : a relever
}
TAILLE = {1: 0x80, 2: 0x300, 3: 0xC0}
NLIST = {1: 8, 2: 16, 3: 64}


def w(d, a): return struct.unpack_from(">H", d, a)[0]
def b(d, a): return d[a ^ 1]                       # octet tel que le lit le code traduit


def liste(d, M, L, dec):
    """-> (type scroll1, numeros de blocs, adresse de la liste)"""
    if L == 1:
        t = d[M["type1"] + dec + 1]                # mot de la table, lu par « adresse ^ 1 » = octet faible
        a = M["list1"] + w(d, M["list1"] + dec)
        return t, [b(d, a + k) for k in range(8 if t else 4)], a
    tl = M["list2"] if L == 2 else M["list3"]
    a = tl + w(d, tl + dec)
    return 0, [b(d, a + k) for k in range(NLIST[L])], a


def bloc(d, M, L, n, base=None, base_st=None):
    """-> {(col, rang) dans le bloc : (code LOCAL, attr)}"""
    out = {}
    if L == 1:
        a = (base or M["b1"]) + n * 0x80
        for k in range(64):
            st = w(d, a + 2 * k); scol, srow = k >> 3, k & 7
            s = (base_st or M["st1"]) + st * 0x40
            for j in range(16):
                out[(scol * 4 + (j >> 2), srow * 4 + (j & 3))] = (w(d, s + 4 * j + 2), w(d, s + 4 * j))   # long PS2 : (attr, code)
        return out
    a = (base or (M["b2"] if L == 2 else M["b3"])) + n * TAILLE[L]
    nb = 256 if L == 2 else 64; sh = 4 if L == 2 else 3; msk = (1 << sh) - 1
    add = M["add2"] if L == 2 else M["add3"]
    for k in range(nb):
        out[(k >> sh, k & msk)] = ((w(d, a + 2 * k) + add) & 0xFFFF, b(d, a + 2 * nb + k))
    return out


def cases_tilemap(d, M, L, dec, **kw):
    t, lst, _ = liste(d, M, L, dec)
    out = {}
    if L == 1:
        nc = 4 if t == 2 else 2
        for p, n in enumerate(lst):
            bx, by = p % nc, p // nc
            for (c, r), v in bloc(d, M, 1, n, **kw).items():
                out[(bx * 32 + c, by * 32 + r)] = v
        return out
    nc = 4 if L == 2 else 8; nt = 16 if L == 2 else 8
    for p, n in enumerate(lst):
        bx, by = p % nc, p // nc
        for (c, r), v in bloc(d, M, L, n, **kw).items():
            out[(bx * nt + c, by * nt + r)] = v
    return out


def palettes_bloc(d, M, L, dec):
    """-> (adresse du bloc de palettes du decor, nombre de palettes PROPRES) — cf. reimport/blocs.palettes_bloc"""
    t = M["pal"][L]
    cibles = sorted({t + struct.unpack_from(">h", d, t + 2 * i)[0] for i in range(M["ndec"])})
    a = t + struct.unpack_from(">h", d, t + dec)[0]
    suiv = [x for x in cibles if x > a]
    return a, min(32, (min(suiv) - a) // 32 if suiv else 32)


# ---------------- reperage automatique dans carte_image.txt (robuste aux reconstructions) ----------------
# adresses PS2 des donnees de decor = constantes du module (les adresses image et les sites changent a chaque
# traduction) ; chaque « LEA $image.L,An  [PS2 adresse] » de la carte donne l'adresse image et un site.
PS2 = {
    "ro3": dict(type1=0x67C630, list1=0x67C670, list2=0x67C79C, list3=0x67C9CC, b1=0x5F72B0, st1=0x5FA1B0,
                b2=0x61F3F0, b3=0x63A9F0, pal1=0x651610, pal2=0x655AF0, pal3=0x65C950),
    "ro5": dict(type1=0x747EE0, list1=0x747F30, list2=0x7480D4, list3=0x748344, b1=0x69B830, st1=0x69F3B0,
                b2=0x6CF5F0, b3=0x6EF3F0, pal1=0x70E560, pal2=0x7147E0, pal3=0x71D420),
}
SITE_NOM = {"b1": "bloc1", "st1": "st1", "b2": "bloc2", "b3": "bloc3", "list1": "liste1", "list2": "liste2",
            "list3": "liste3", "pal1": "pal1", "pal2": "pal2", "pal3": "pal3"}


def depuis_carte(carte, module):
    """-> profil M (adresses image + sites) d'apres carte_image.txt"""
    import re
    inv = {v: k for k, v in PS2[module].items()}
    trouve = {}; sites = {}
    rx = re.compile(r"^([0-9a-f]{6}) \S+ LEA \$([0-9a-f]+)\.L,A\d\s+\[PS2 ([0-9a-f]{8})\]")
    for l in open(carte):
        m = rx.match(l)
        if not m: continue
        p = int(m.group(3), 16)
        if p in inv:
            k = inv[p]; a = int(m.group(2), 16)
            assert trouve.setdefault(k, a) == a, "%s : deux adresses image" % k
            if k in SITE_NOM: sites.setdefault(SITE_NOM[k], []).append(int(m.group(1), 16))
    manque = set(PS2[module]) - set(trouve)
    assert not manque, "carte %s : donnees de decor introuvables %s" % (carte, manque)
    M = dict(MOD[module])
    M.update({k: trouve[k] for k in ("type1", "list1", "list2", "list3", "b1", "st1", "b2", "b3")})
    M["pal"] = {1: trouve["pal1"], 2: trouve["pal2"], 3: trouve["pal3"]}
    M["sites"] = {k: sorted(v) for k, v in sites.items()}
    return M
