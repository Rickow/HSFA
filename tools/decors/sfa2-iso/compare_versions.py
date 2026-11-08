#!/usr/bin/env python3
"""compare_versions.py (local) — Q1 : les 4 modules SFA2 de l'Anthology (ro2 Zero 2, ro4 Zero 2 Alpha, ro6 Alpha 2
Gold + Cammy, ro8 SFA2 occidental) et les révisions arcade (sfa2u, sfa2 Europe, sfz2al) ont-ils les mêmes décors ?
Compare, décor par décor, ce que lit extrait_sfa2.lit_decors (types, listes, palettes, CPS-B, musique, objets) et les
bibliothèques. Pour ro4/6/8, les adresses viennent de la recherche du contenu des tables de ro2 (même rangement).
Usage : compare_versions.py DONNEES/ (ro2.bin, ro4.bin… décompressés) [DUMP_CARTO_SFA2/]"""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extrait_sfa2 as X2
DON = sys.argv[1]; DUMP = sys.argv[2] if len(sys.argv) > 2 else None
R2 = X2.Ro(open(os.path.join(DON, "ro2.bin"), "rb").read())
ref = X2.lit_decors(R2); refb = X2.bibs(R2, ref)
CH = ["type_s1", "liste_s1", "liste_s2", "liste_s3", "pal_s1", "pal_s2", "pal_s3", "pal_spr", "cpsb", "musique", "objets"]
def compare(nom, dec, bb):
    out = []
    for s in range(X2.N):
        diff = [k for k in CH if dec[s][k] != ref[s][k]]
        if diff: out.append("%s:%s" % (ref[s]["val"], ",".join(diff)))
    for i, k in ((1, "bib_s1"), (2, "cel_s1"), (3, "bib_s2"), (4, "bib_s3")):
        a, b = bb[i], refb[i]
        if a != b:
            n = min(len(a), len(b)); unit = 4 if k != "bib_s1" else 2
            nd = sum(1 for j in range(0, n, unit) if a[j:j + unit] != b[j:j + unit])
            out.append("%s:%d entrées différentes%s" % (k, nd, "" if len(a) == len(b) else " (tailles %d/%d)" % (len(a), len(b))))
    print("%-8s %s" % (nom, "IDENTIQUE à ro2" if not out else " ; ".join(out)))
    return out
res = {}
for m in ("ro4", "ro6", "ro8"):
    Q = open(os.path.join(DON, m + ".bin"), "rb").read()
    carte = {}
    for k, a in X2.CARTE.items():
        n = 40 if k not in ("bib_s1", "cel_s1", "bib_s2", "bib_s3", "pal_s1", "pal_s2", "pal_s3", "pal_spr") else 0x400
        dk = 0x400 if k in ("bib_s2",) else (0x100 if k == "bib_s3" else 0)   # bloc 0 = tuiles vides, ambigu
        o = Q.find(R2.octets(a + dk, n)); carte[k] = o - dk + X2.EXEC if o >= 0 else None
    # types s2/s3 (zéros) : même écart que dans ro2 par rapport aux décalages
    for p in (2, 3): carte["types_s%d" % p] = carte["ofs_s%d" % p] - (X2.CARTE["ofs_s%d" % p] - X2.CARTE["types_s%d" % p])
    manq = [k for k, v in carte.items() if v is None]
    if manq: print(m, "tables non retrouvées :", manq)
    sauve = dict(X2.CARTE); X2.CARTE.update({k: v for k, v in carte.items() if v})
    Rm = X2.Ro(Q); dec = X2.lit_decors(Rm); bb = X2.bibs(Rm, dec)
    X2.CARTE.clear(); X2.CARTE.update(sauve)
    res[m] = dict(carte={k: ("0x%06X" % v) if v else None for k, v in carte.items()}, ecarts=compare(m, dec, bb))
if DUMP:
    # révisions arcade : mêmes lectures en grand-boutiste (oracle), adresses de sfa2u
    for j in ("sfa2u",):   # (sfa2 Europe / sfz2al : autres adresses de programme, non relogées ici)
        D = open(os.path.join(DUMP, j, "prog_donnees.bin"), "rb").read(); C = open(os.path.join(DUMP, j, "prog_opcodes.bin"), "rb").read()
        w = lambda a, d=D: struct.unpack_from(">H", d, a)[0]; sw = lambda a: struct.unpack_from(">h", D, a)[0]
        dec = []
        for s in range(X2.N):
            d = {}
            t1 = w(0x1CFC4 + 2 * s); d["type_s1"] = t1
            for p, (li, n) in enumerate(((0x1CFF4, X2.LONG_S1.get(t1, 8)), (0x1D0EC, 16), (0x1D2A4, 64))):
                d["liste_s%d" % (p + 1)] = list(D[li + sw(li + 2 * s):][:n])
            for p, a in ((1, 0x27C1C0), (2, 0x2865C0), (3, 0x2909C0)): d["pal_s%d" % p] = D[a + 0x400 * s:a + 0x400 * s + 0x400].hex()
            d["pal_spr"] = D[0x275C40 + 0xE0 * s:0x275C40 + 0xE0 * s + 0xE0].hex()
            d["cpsb"] = ["$%04X" % w(0x1C34A + 4 * s, C), "$%04X" % w(0x1C34C + 4 * s, C)]
            d["musique"] = "$%02X" % w(0x154EE + 2 * s, C)
            a = 0x1EB66 + w(0x1EB66 + 2 * s, C); objs = []
            while D[a] < 0x80:
                r = D[a:a + 16]; x, y, g, g5, rout = struct.unpack_from(">HHBBH", r, 0)
                objs.append(dict(x=x, y=y, groupe=g, o5=g5, routine="$%04X" % rout, brut=r.hex())); a += 16
            d["objets"] = objs; dec.append(d)
        nb = [len(refb[i]) for i in range(1, 5)]
        bb = [None, D[0x2AD300:0x2AD300 + nb[0]], D[0x2B1A80:0x2B1A80 + nb[1]], D[0x2D1F00:0x2D1F00 + nb[2]], D[0x2F8700:0x2F8700 + nb[3]]]
        res[j] = dict(ecarts=compare(j, dec, bb))
json.dump(res, open(os.path.join(DON, "compare_versions.json"), "w"), indent=1)
