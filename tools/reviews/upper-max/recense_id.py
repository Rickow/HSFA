#!/usr/bin/env python3
"""recense_id.py -- Upper MAX review (B): independent census of the tables read by the character ID ($103 of an object)
in the map of Upper WITHOUT MAX: for each "MOVE.B $0103(An),Dn", look in the next 10 lines for a LEA [PS2 x] or a
T_x(PC,...); report the addresses x absent from tables_par_id.json and from the constants of agrandit_max.py /
integre_max.py / mame_test.py of the repository's integration copy (tables perhaps not extended to 48). Heuristic:
false positives possible (index other than the ID).

Usage:  python3 -I recense_id.py CARTE_IMAGE
        CARTE_IMAGE = carte_image.txt of Upper's reference build without MAX (outils_max/ag/banc_ref/ of an Upper MAX build)
Inputs: that map, tools/integration-max/upper_max/integration_2b31/ag/ of the repository. Output: text. Read only.
"""
import sys, os, re, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
if len(sys.argv) < 2: sys.exit(__doc__)
C = sys.argv[1]
connues = {int(t["ps2"], 16) for t in json.loads(paths.lit_texte(os.path.join(paths.AG, "outils", "tables_par_id.json")))}
for f in (("untranspile", "agrandit_max.py"), ("untranspile", "integre_max.py"), ("untranspile", "mame_test.py")):
    connues |= {int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{6})\b", paths.lit_texte(os.path.join(paths.AG, *f)))}
L = paths.lit_texte(C).splitlines(); vus = {}
for n, l in enumerate(L):
    m = re.search(r"MOVE\.B \$0103\(A\d\),(D\d)", l)
    if not m: continue
    reg = m.group(1)
    for q in L[n + 1:n + 11]:
        if re.search(r"\b(RTS|JMP|BRA)\b", q): break
        if re.search(r"(MOVEQ|MOVE\.[BWL]) [^,]+,%s\b" % reg, q) and "$0103" not in q: break     # registre écrasé
        x = re.search(r"\[PS2 00([0-9a-f]{6})\]", q) or re.search(r"T_([0-9a-f]{6})\(PC,%s" % reg, q)
        if x:
            a = int(x.group(1), 16)
            if 0x60AC00 <= a < 0xA00000: vus.setdefault(a, []).append((l[:14].strip(), q[15:75]))
            break
inc = {a: v for a, v in vus.items() if a not in connues and not any(a - 4 <= c <= a for c in connues)}
print("tables lues après un $103 : %d ; inconnues de l'intégration : %d" % (len(vus), len(inc)))
for a, v in sorted(inc.items()): print("%X  %d site(s)  %s  %s" % (a, len(v), v[0][0], v[0][1]))
