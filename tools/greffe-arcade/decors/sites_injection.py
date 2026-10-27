#!/usr/bin/env python3
"""sites_injection.py : sites « LEA abs.L » des donnees de decor dans l'image traduite de chaque module, retrouves par
l'ADRESSE PS2 de la constante dans carte_image.txt (methode de blocs_tr.depuis_carte) -> sites_injection.tsv.
Constantes par module = seule partie propre au module de l'etape « decors »."""
import os, re, collections
H = os.path.dirname(os.path.abspath(__file__))
CARTE = {"ro3": "<workspace>/work/mame/carte_image.txt", "ro5": "<workspace>/work/mame_ro5/carte_image.txt",
         "ro9": "<workspace>/work/mame_ro9/carte_image.txt"}
# adresses PS2 (exec.) des donnees de decor ; None = absent du module
K = collections.OrderedDict([
    ("type1",  {"ro3": 0x67C630, "ro5": 0x747EE0, "ro9": 0x695FF0}),
    ("liste1", {"ro3": 0x67C670, "ro5": 0x747F30, "ro9": 0x695FF8}),
    ("liste2", {"ro3": 0x67C79C, "ro5": 0x7480D4, "ro9": 0x696010}),
    ("liste3", {"ro3": 0x67C9CC, "ro5": 0x748344, "ro9": 0x696048}),
    ("bloc1",  {"ro3": 0x5F72B0, "ro5": 0x69B830, "ro9": 0x63DA20}),
    ("st1",    {"ro3": 0x5FA1B0, "ro5": 0x69F3B0, "ro9": 0x63DD20}),
    ("bloc2",  {"ro3": 0x61F3F0, "ro5": 0x6CF5F0, "ro9": 0x640960}),
    ("bloc3",  {"ro3": 0x63A9F0, "ro5": 0x6EF3F0, "ro9": 0x643C60}),
    ("pal1",   {"ro3": 0x651610, "ro5": 0x70E560, "ro9": 0x660240}),
    ("pal2",   {"ro3": 0x655AF0, "ro5": 0x7147E0, "ro9": 0x661E60}),
    ("pal3",   {"ro3": 0x65C950, "ro5": 0x71D420, "ro9": 0x664280}),
    ("palspr", {"ro3": None,     "ro5": 0x707D10, "ro9": None}),
])
out = open(os.path.join(H, "sites_injection.tsv"), "w"); out.write("donnee\tmodule\tps2\tsites_image(instr. LEA)\tva_mips\n")
for mod, f in CARTE.items():
    if not os.path.exists(f): print("absent :", f); continue
    idx = collections.defaultdict(list)
    for ln in open(f, errors="replace"):
        m = re.search(r"\[PS2 00([0-9a-f]{6})\]", ln)
        if m and " LEA " in ln:
            p = ln.split(); idx[int(m.group(1), 16)].append((p[0], p[1]))
    n = 0
    for nom, d in K.items():
        v = d.get(mod)
        s = idx.get(v, []) if v else []
        n += len(s) if nom != "type1" else 0
        out.write("%s\t%s\t%s\t%s\t%s\n" % (nom, mod, ("%x" % v) if v else "-", " ".join("$" + a.upper() for a, _ in s), " ".join(b for _, b in s)))
    print("%s : %d sites LEA relogeables (hors type1)" % (mod, n))
out.close()
