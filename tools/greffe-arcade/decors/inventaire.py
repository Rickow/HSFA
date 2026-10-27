#!/usr/bin/env python3
"""inventaire.py : tableau decor par decor (Upper $00-$4E) : persos qui y menent (T_61BE10), donnees du module
(donnees_decor.tsv), graphismes (tuiles_decor.tsv), adresses Upper / Hyper -> inventaire_decors.tsv + inventaire_decors.md"""
import os, csv, json, struct, collections
H = os.path.dirname(os.path.abspath(__file__)); BASE = 0x1F0000
B5 = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read()
B3 = open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin", "rb").read()
# ids -> noms : table de noms d'Upper 0x626120 pour $00-$11 ; decalee d'un rang a partir de $15 (recoupements : Evil Ryu
# $17 -> $2E lie a $00, Juli/Juni $1E/$1F -> $2A lie a $3C/$3E, ROUND R.Mika +$2A0 = $34 / Cody +$2C0 = $36 (HANDOFF),
# Shin Akuma $24 -> $48 = donnees d'Akuma $04, EX Balrog $25 -> $4A comme Balrog $15) ; $12-$14 non tranches.
_L = ("Ryu Ken Akuma Charlie Chun-Li Adon Sodom Guy Birdie Rose M.Bison Sagat Dan Sakura Rolento Dhalsim Zangief Gen").split()
NOMS = _L + ["id12", "id13", "id14"] + ("Balrog Cammy EvilRyu E.Honda Blanka R.Mika Cody Vega Karin Juli Juni Guile Fei-Long "
        "DeeJay T.Hawk ShinAkuma EX-Balrog id26 id27").split()
T5 = B5[0x61BE10 - BASE:0x61BE10 - BASE + 40]; T3 = B3[0x593690 - BASE:0x593690 - BASE + 32]
par = collections.defaultdict(list); par3 = collections.defaultdict(list)
for i, v in enumerate(T5): par[2 * v].append(NOMS[i])
for i, v in enumerate(T3): par3[2 * v].append("%02X" % i)
grp = {}
try:
    for g in json.load(open("<workspace>/work/decors_ws/out/decors/recap.json")):
        for d in g['lies']: grp[int(d, 16)] = "/".join(g['persos'])
except Exception: pass
D = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(H, "donnees_decor.tsv")), delimiter='\t'):
    D[int(r['decor'][1:], 16)][r['table']] = r
G = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(H, "tuiles_decor.tsv")), delimiter='\t'):
    if r['module'] == 'ro5': G[int(r['decor'][1:], 16)][int(r['plan'])] = r
cols = ["decor", "groupe_export", "persos_arcade_Upper", "pal_s1_Upper", "liste_s1_Upper", "liste_s2_Upper", "liste_s3_Upper",
        "alias", "donnees_dans_Hyper", "gfx_s1_%Hyper", "gfx_s2_%Hyper", "gfx_s3_%Hyper", "gfx_SFA3", "decor_Hyper"]
out = open(os.path.join(H, "inventaire_decors.tsv"), "w"); out.write("\t".join(cols) + "\n")
md = ["| décor | export DECORS-WS | persos qui y mènent (Upper) | pal. s1 / listes s1-s2-s3 (Upper, exéc.) | données dans Hyper | gfx s1/s2/s3 dans Hyper | gfx dans SFA3 |",
      "|---|---|---|---|---|---|---|"]
for d in range(0, 0x50, 2):
    t = D[d]; g = G[d]
    p1 = t["palettes scroll1 (32 x 32 o)"]; l1 = t["listes scroll1"]; l2 = t["listes scroll2"]; l3 = t["listes scroll3"]
    cle = lambda e: tuple(D[e][k]['adr_upper'] for k in ("palettes scroll1 (32 x 32 o)", "listes scroll1", "listes scroll2", "listes scroll3"))
    al = ["$%02X" % e for e in range(0, d, 2) if cle(e) == cle(d)]
    lst = ["$%02X" % e for e in range(0, d, 2) if all(D[e][k]['adr_upper'] == D[d][k]['adr_upper'] for k in ("listes scroll1", "listes scroll2", "listes scroll3"))]
    if not al and lst: al = ["listes=" + lst[0]]
    dh = [k for k, x in t.items() if x['dans_hyper'] != '-' and not x['alias_de']]
    hy = "4 / 6 (ZERO 3)" if d == 0x4E else ""
    pct = [g[L]['pct_hyper'] for L in (1, 2, 3)]
    sf = "oui" if all(float(g[L]['pct_sfa3']) > 99 or int(g[L]['contenus_distincts']) == 0 for L in (1, 2, 3)) else "non"
    donnees = "palettes = Hyper %s" % ("décor 4 var. 0" ) if d == 0x4E else ("non" if not dh else ",".join(dh))
    pers = ", ".join(par.get(d, [])) or ("(attraction / VERSUS)" if d == 0x4E else "—")
    row = ["$%02X" % d, grp.get(d, "Upper (neuf)" if d >= 0x40 else ""), pers, p1['adr_upper'], l1['adr_upper'], l2['adr_upper'],
           l3['adr_upper'], " ".join(al), donnees, *pct, sf, hy]
    out.write("\t".join(row) + "\n")
    md.append("| `$%02X` | %s | %s | `%s` / `%s` `%s` `%s` | %s | %s / %s / %s %% | %s |" % (d, row[1] or "—", pers, row[3], row[4], row[5], row[6],
              ("oui (= Hyper 4/6)" if d == 0x4E else "non") + ((" ; alias " + " ".join(al)) if al else ""), *[x.split('.')[0] for x in pct], sf))
out.close()
open(os.path.join(H, "inventaire_decors.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md))
print("SFA3 (ro3) T_593690 : changements d'Upper :", [(NOMS[i], "%02X->%02X" % (2*T3[i], 2*T5[i])) for i in range(32) if T3[i] != T5[i]])
