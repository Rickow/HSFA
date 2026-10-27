#!/usr/bin/env python3
"""NUMEROS DE BLOCS LIBRES dans les bibliotheques de blocs de decor (scroll1/2/3) : SFA3 arcade, SFA3 traduit (ro3),
Upper traduit (ro5). Lecture seule.

Sources des numeros :
  - listes par decor (tables type/liste lues par les routines de composition) ;
  - appels directs des routines de bloc (« moveq/move.w #n,D0 » avant l'appel) ;
  - boucles sur une liste en ROM (« lea table ; move.b (A4)+,D0 ») : la table est lue (16/64/4 octets x entrees) ;
  - fins (arcade) : tables $26CC4/$26D48 (session MAX).
Capacite d'une bibliotheque = (debut de la structure suivante - base) / taille de bloc, plafonnee a 256 (octet).
Usage : venv/bin/python reimport/blocs_libres.py   (-> reimport/blocs_libres.json)
"""
import os, re, sys, json, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blocs as B

TB = {1: 0x80, 2: 0x300, 3: 0xC0}
# tables des plans des fins (normale, variante $90(A5)), nombre d'entrees, decalage adresse PS2 -> image
FINS = {"ro3": ((0x0948A0, 0x094930), 36, 0x5843C0 - 0x094780),
        "ro5": ((0x0A1A40, 0x0A1AF0), 44, 0x60B5A0 - 0x0A18E0)}
NLIST = {1: 4, 2: 16, 3: 64}


def image_roms(dossier):
    noms = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
    raw = b"".join(open(os.path.join(dossier, n), "rb").read() for n in noms)
    b = bytearray(raw); b[0::2], b[1::2] = raw[1::2], raw[0::2]
    return bytes(b)


def w(d, a): return struct.unpack_from(">H", d, a)[0]


def listes_table(d, tl, L, n_dec, ttype=None):
    """table de decalages (mots) -> listes ; l'acces traduit lit l'octet n a l'adresse n^1 (memoire PS2), on lit
    donc la liste telle qu'elle est rangee (le jeu de numeros est le meme)."""
    out = set(); par = {}
    for k in range(n_dec):
        o = w(d, tl + 2 * k)
        if not (0 < o < 0x4000): continue
        n = NLIST[L]
        if L == 1 and ttype is not None and w(d, ttype + 2 * k) != 0: n = 8   # type 1/2 : 8 blocs
        l = d[tl + o:tl + o + n]
        par[k] = l.hex(); out.update(l)
    return out, par


def depuis_carte(carte, entrees, d, base_img=0):
    """appels traduits : numeros immediats et tables (A4) parcourues avant l'appel"""
    lignes = open(carte).read().splitlines()
    res = {1: set(), 2: set(), 3: set()}; dyn = {1: [], 2: [], 3: []}
    for i, l in enumerate(lignes):
        for L, cib in entrees.items():
            if cib not in l: continue
            n = None; tab = None
            for j in range(i - 1, max(0, i - 8), -1):
                m = re.search(r"MOVEQ #(\$?[0-9a-f]+),D0|MOVE\.W #\$([0-9a-f]+),D0", lignes[j])
                if m and n is None:
                    n = int(m.group(1)[1:], 16) if m.group(1) and m.group(1).startswith("$") else \
                        (int(m.group(1)) if m.group(1) else int(m.group(2), 16))
                    break
                if "(A4)" in lignes[j] or "A4" in lignes[j]:
                    mt = None
                    for k in range(j, max(0, j - 12), -1):
                        mt = re.search(r"LEA \$([0-9a-f]+)\.L,A4", lignes[k])
                        if mt: break
                    tab = int(mt.group(1), 16) if mt else "dynamique"
                    break
            if n is not None: res[L].add(n & 0xFF)
            else: dyn[L].append((lignes[i].split()[0], tab))
    return res, dyn


def capacite(bases, L, fin_donnees):
    b = bases[L]
    suiv = [x for x in bases.values() if x > b] + [fin_donnees]
    return min(256, (min(suiv) - b) // TB[L])


def rapport(nom, utilises, cap, details):
    out = {}
    for L in (1, 2, 3):
        u = utilises[L]
        lib = [x for x in range(cap[L]) if x not in u]
        out["scroll%d" % L] = dict(capacite=cap[L], utilises=len([x for x in u if x < cap[L]]),
                                   max_utilise="$%02X" % max(u) if u else None,
                                   libres=["$%02X" % x for x in lib], nb_libres=len(lib),
                                   hors_capacite=["$%02X" % x for x in sorted(u) if x >= cap[L]])
        print("%s scroll%d : capacite %d, utilises %d (max $%02X), LIBRES %d : %s" % (
            nom, L, cap[L], out["scroll%d" % L]["utilises"], max(u), len(lib), " ".join("%02X" % x for x in lib)))
    out["details"] = details
    return out


def main():
    res = {}
    # ---------------- arcade ----------------
    d = open(B.PROG, "rb").read()
    u = {1: set(), 2: set(), 3: set()}
    for L in (1, 2, 3):
        for dec in range(0, 64, 2):
            u[L].update(B.liste(d, L, dec)[1])
    for t in (0x26CC4, 0x26D48):                                  # fins (session MAX)
        bases = sorted(set(struct.unpack_from(">I", d, t + 4 * i)[0] for i in range(33)))
        for b in bases:
            if not 0x300000 <= b < 0x400000: continue
            offs = sorted(set(w(d, b + 2 * i) for i in range(w(d, b) // 2)))
            for i, o in enumerate(offs):
                e = (offs[i + 1] - o) if i + 1 < len(offs) else 64
                L = {4: 1, 16: 2, 64: 3}.get(e)
                if L: u[L].update(d[b + o:b + o + e])
    imm = {1: [0x52, 0x53, 0x50, 0x51, 0x55], 2: [0x80, 0x81, 0x86, 0x87], 3: [0x4F, 0x50, 0x51, 0x52, 0x53, 0x81]}
    for L, l in imm.items(): u[L].update(l)
    for L, a, n in ((1, 0x7404, 16), (2, 0x7458, 30), (3, 0x74BC, 64)):     # ecran a tables PC-relatives ($73C0)
        u[L].update(d[a:a + n])
    fin = 0x3C8540
    cap = {1: (B.ST1 - B.B1) // 0x80, 2: (B.B3 - B.B2) // 0x300, 3: min(256, (fin - B.B3) // 0xC0)}
    res["sfa3_arcade"] = rapport("arcade", u, cap, dict(bases={"bloc1": "$367494", "supertuiles1": "$36A394",
                                                              "bloc2": "$391014", "bloc3": "$3AC614"}))
    # ---------------- traductions ----------------
    for nom, roms, carte, bases, tables, entrees, ndec in (
            ("ro3", "<workspace>/work/mame/roms_tr/sfa3ud", "<workspace>/work/mame/carte_image.txt",
             {1: 0x107670, 0: 0x10A570, 2: 0x12F7B0, 3: 0x14ADB0},
             {1: 0x18CA30, 2: 0x18CB5C, 3: 0x18CD8C, "type1": 0x18C9F0},
             {1: "cible 002fd0f0", 2: "cible 002fdd40", 3: "cible 002fe1f0"}, 32),
            ("ro5", "<workspace>/work/mame_ro5/roms_ro5/sfa3ud", "<workspace>/work/mame_ro5/carte_image.txt",
             {1: 0x131B70, 0: 0x1356F0, 2: 0x165930, 3: 0x185730},
             {1: 0x1DE270, 2: 0x1DE414, 3: 0x1DE684, "type1": 0x1DE220},
             {1: "mips 003409d0]", 2: "cible 003415c0", 3: "cible 00341a00"}, 40)):
        d = image_roms(roms)
        u = {1: set(), 2: set(), 3: set()}; par = {}
        for L in (1, 2, 3):
            s, p = listes_table(d, tables[L], L, ndec, tables["type1"]); u[L] |= s; par["scroll%d" % L] = p
        r, dyn = depuis_carte(carte, entrees, d)
        tabs = {}
        for L in (1, 2, 3):
            u[L] |= r[L]
            for site, tab in dyn[L]:
                if isinstance(tab, int):
                    # table en ROM (image) : ecran a tables PC-relatives (16 / 32 / 64 octets)
                    blob = d[tab:tab + {1: 16, 2: 32, 3: 64}[L]]; u[L].update(blob)   # = tables $7404/$7458/$74BC de l arcade; tabs[site] = "$%06X" % tab
                else:
                    tabs[site] = tab
        # fins : tables de pointeurs (adresses PS2, longs a moities echangees) -> listes de plans (4/16/64 octets)
        tfin, nfin, delta = FINS[nom]
        nf = 0
        for t in tfin:
            for i in range(nfin):
                a = struct.unpack_from(">I", d, t + 4 * i)[0]
                b = (((a & 0xFFFF) << 16) | (a >> 16)) - delta
                if not 0 < b < len(d) - 2: continue
                offs = sorted(set(w(d, b + 2 * k) for k in range(min(64, w(d, b) // 2))))
                for k, o in enumerate(offs):
                    e = (offs[k + 1] - o) if k + 1 < len(offs) else 64
                    L = {4: 1, 16: 2, 64: 3}.get(e)
                    if L: u[L].update(d[b + o:b + o + e]); nf += 1
        print("%s : %d listes de fins lues" % (nom, nf))
        fin = len(d.rstrip(b"\xff"))
        cap = {L: capacite({1: bases[1], 0: bases[0], 2: bases[2], 3: bases[3]}, L, fin) for L in (1, 2, 3)}
        res[nom] = rapport(nom, u, cap, dict(bases={k: "$%06X" % v for k, v in bases.items()},
                                             listes_decor=par, appels_sur_liste=tabs))
    json.dump(res, open(os.path.join(HERE, "blocs_libres.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
