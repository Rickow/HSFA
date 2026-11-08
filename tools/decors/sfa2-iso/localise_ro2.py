#!/usr/bin/env python3
"""localise_ro2.py (côté ORACLE, local) : retrouve dans les modules SFA2 de l'Anthology (ro2 = e224 « zero2_usa.bin »,
et pour comparaison ro4 e348, ro6 e526, ro8 e543, décompressés) les tables de décor de l'arcade sfa2u (programme
vidé par MAME, carto_sfa2/dump/sfa2u : espaces DONNÉES et OPCODES), par contenu, sous les trois rangements du
recompilateur (octets tels quels « b », mots échangés « w », longs échangés « l »). Écrit outils/carte_ro2.json :
adresses seulement (aucune donnée de jeu). C'est ce fichier que lit extrait_sfa2.py (côté ISO).
Méthode et code de lecture repris de decors_sfa1/outils/localise_ro1.py.
Usage : localise_ro2.py DONNEES/ (contenant ro2.bin, ro4.bin, ro6.bin, ro8.bin) DUMP_SFA2U/"""
import sys, json, struct, os
DON = sys.argv[1]; DUMP = sys.argv[2]
D = open(os.path.join(DUMP, "prog_donnees.bin"), "rb").read(); C = open(os.path.join(DUMP, "prog_opcodes.bin"), "rb").read()
EXEC = 0x1F0000
def sw16(b): return b"".join(b[i:i + 2][::-1] for i in range(0, len(b), 2))
def sw32(b): return b"".join(b[i:i + 4][::-1] for i in range(0, len(b), 4))
TR = {"w": sw16, "l": sw32, "b": lambda b: b}
w = lambda b, a: struct.unpack_from(">H", b, a)[0]
sw = lambda b, a: struct.unpack_from(">h", b, a)[0]
N = 20

def trouve(R, src, a, n, modes="wlb"):
    hits = []
    for m in modes:
        t = TR[m](src[a:a + n]); o = R.find(t)
        while o >= 0 and len(hits) < 50:
            if o % 2 == 0: hits.append((m, o + EXEC))
            o = R.find(t, o + 1)
    hs = sorted(set(hits), key=lambda h: (h[1], "wlb".index(h[0])))
    return hs

TABLES = []
def T(nom, src, a, n, modes="wlb", ref=None): TABLES.append((nom, src, a, n, modes, ref))
for k, (ty, li, ln) in enumerate(((0x1CFC4, 0x1CFF4, 8), (0x1D0BC, 0x1D0EC, 16), (0x1D274, 0x1D2A4, 64))):
    T("types_s%d" % (k + 1), D, ty, 2 * N, "w"); T("ofs_s%d" % (k + 1), D, li, 2 * N, "w")
    adr = [li + sw(D, li + 2 * s) for s in range(N)]
    lo, hi = min(adr), max(adr) + ln
    T("listes_s%d" % (k + 1), D, lo, hi - lo, "w", "zone des listes des 20 décors")
T("bib_s1", D, 0x2AD300, 0x60 * 128, "w", "blocs scroll1 : 64 mots (n° de cellule), colonne d'abord")
T("cel_s1", D, 0x2B1A80, 0x400 * 64, "l", "cellules scroll1 : 16 longs (code<<16|attr) ; contrôle partiel (codes)")
T("bib_s2", D, 0x2D1F00, 58 * 1024, "l", "blocs scroll2 0-57 identiques ; 58+ renumérotés par le portage")
T("bib_s3", D, 0x2F8700, 0xA0 * 256, "l", "blocs scroll3 : 64 longs")
T("pal_spr", D, 0x275C40, N * 0xE0, "w", "palettes des sprites de décor : 7 × 32 o par décor")
for k, a in enumerate((0x27C1C0, 0x2865C0, 0x2909C0)):
    T("pal_s%d" % (k + 1), D, a, N * 0x400, "w")
T("cpsb", C, 0x1C34A, 4 * N, "w", "contrôle CPS-B (2 mots / décor)")
T("musique", C, 0x154EE, 2 * N, "w")
T("perso_decor", C, 0x7A7A, 0x20, "b")
T("ofs_objets", C, 0x1EB66, 2 * N, "w")
adr = [0x1EB66 + w(C, 0x1EB66 + 2 * s) for s in range(N)]
recs = []
for a in adr:
    n = 0
    while D[a + 16 * n] < 0x80: n += 1
    recs.append((a, 16 * n + 2))
lo = min(a for a, n in recs); hi = max(a + n for a, n in recs)
T("objets", D, lo, hi - lo, "w", "enregistrements de 16 o des objets de décor (20 décors)")

out = {}
mods = {m: open(os.path.join(DON, m + ".bin"), "rb").read() for m in ("ro2", "ro4", "ro6", "ro8") if os.path.exists(os.path.join(DON, m + ".bin"))}
for nom, src, a, n, modes, ref in TABLES:
    e = dict(arcade="$%06X" % a, espace="opcodes" if src is C else "donnees", taille=n, ref=ref)
    for m, R in mods.items():
        hs = trouve(R, src, a, n, modes)
        e[m] = ["%s 0x%06X" % h for h in hs[:4]] + (["+%d" % (len(hs) - 4)] if len(hs) > 4 else [])
    out[nom] = e
    print("%-12s %s n=%6d  %s" % (nom, e["arcade"], n, "  ".join("%s:%s" % (m, (e[m] or ["ABSENT"])[0]) for m in mods)))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "carte_ro2.json"), "w"), indent=1)
