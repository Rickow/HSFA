#!/usr/bin/env python3
"""releve_tables.py -- Upper MAX arbitrations (A3 / A4): PSP against Upper MAX for the per-id table 0x615940 (dx, dy of
the linked effect) and the Arcade masks 0x61B540 / 0x61B4E0 / 0x61B510: EU EBOOT (VA = offset - 0x74), Upper's original
ro5 (PS2) and the extended copy of a build (ext_e80000.bin + max_agrandies.txt). Shows whether the build's MAX entries
equal the PSP: run it on a build with MAX_615940_PSP=1 / MAX_MASQUES_PSP=1 to check the switches before benching them.

Usage:  python3 -I releve_tables.py BENCH [BOOT.BIN] [ro5_usa_prog68k.bin]
Inputs: bench folder of an Upper MAX build; EBOOT ($HSFA_PSP_BOOT / $HSFA_CACHE) and ro5 ($HSFA_MODULES / $HSFA_CACHE)
        unless given. Output: text (French labels). Read only.
"""
import sys, os, struct
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
BANC = paths.banc(sys.argv[1] if len(sys.argv) > 1 else None)
EB = paths.boot(sys.argv[2] if len(sys.argv) > 2 else None)
RO5 = paths.module(sys.argv[3] if len(sys.argv) > 3 else "ro5")
EXT_IMG = open(os.path.join(BANC, "ext_e80000.bin"), "rb").read()
EXT = bytes(EXT_IMG[k ^ 1] for k in range(len(EXT_IMG)))   # le bloc est en ordre IMAGE (octets échangés par mot) -> ordre PS2
COPIE = {}
for l in open(os.path.join(BANC, "max_agrandies.txt"), encoding="utf-8"):
    c = l.split()
    if len(c) > 3 and c[0] != "ps2": COPIE[int(c[0], 16)] = int(c[3], 16)
MAX = (("Eagle", 0x26, 0x26), ("Maki", 0x27, 0x27), ("Yun", 0x2D, 0x28), ("Ingrid", 0x2E, 0x29))
# (table Upper, table PSP, taille d'entrée, format, rôle) ; homologies : revue_B/REVUE.md B4 / B5, A3_table_615940.md
TABLES = ((0x615940, 0x2205E8, 4, "<hh", "effet lié (dx, dy) ; Vega Upper 40/41 = PSP 42/43"),
          (0x61B540, 0x20B676, 1, "<B", "masque de l'Arcade : combat secret ($13E = 2)"),
          (0x61B4E0, 0x20B6A0, 1, "<B", "masque de l'Arcade : $13E = 8"),
          (0x61B510, 0x20B6CA, 1, "<B", "masque de l'Arcade : $13E = $A"))

def ent(buf, a, e, f): return struct.unpack_from(f, buf, a)
for tu, tp, e, f, role in TABLES:
    o = lambda i: tu - 0x1F0000 + e * i
    nat = sum(ent(RO5, o(i), e, f) == ent(EB, tp + e * i, e, f) for i in range(0x26))
    dif = [i for i in range(0x26) if ent(RO5, o(i), e, f) != ent(EB, tp + e * i, e, f)]
    c = COPIE[tu] - 0xE80000
    # ordre des octets de la copie : comparé aux natifs d'origine (PS2) sur 40 entrées
    ps2 = all(EXT[c + e * i:c + e * i + e] == RO5[o(i):o(i) + e] for i in range(0x26))   # natifs seulement
    print("0x%X (copie $%X, %s) <-> PSP 0x%X : %s ; natifs égaux %d/38%s" % (
        tu, COPIE[tu], "ordre PS2" if ps2 else "ORDRE ≠ PS2", tp, role, nat,
        (" (différents : %s)" % ", ".join("$%02X" % i for i in dif)) if dif else ""))
    for nom, iu, ip in MAX:
        print("   %-6s Upper $%02X / PSP $%02X : PSP %-10s Upper d'origine[$%02X] %-10s Upper MAX (copie) %-10s %s" % (
            nom, iu, ip, ent(EB, tp + e * ip, e, f), iu, ent(RO5, o(iu), e, f) if iu < 40 else "-",
            ent(EXT, c + e * iu, e, f),
            "= PSP" if ent(EXT, c + e * iu, e, f) == ent(EB, tp + e * ip, e, f) else "ÉCART"))
    if tu == 0x615940:
        for iu, ip in ((40, 42), (41, 43)):
            print("   Vega   Upper %d / PSP %d : PSP %s Upper MAX %s" % (iu, ip, ent(EB, tp + e * ip, e, f), ent(EXT, c + e * iu, e, f)))
