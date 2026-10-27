#!<workspace>/venv/bin/python
"""Tables « sons par pas » d'Hyper (champ $E6 du joueur ; table exec 0x6AE614, 128 pointeurs LE indexes par $102,
68K $06DF92 : LEA $1934d4 = PS2 0x6AE614 ; MOVE.L 0(A0,D0.W),$E6(A6)). Entree = 8 o (mots LE dans le module) [code, code_alt, 0, 0] ; la routine
68K $08BCCE (= arcade $38E4 sans le test $BC(A5)) lit le mot 0 : code = table[index]. Les ZERO/ZERO 2/ALPHA pointent sur
la table ZERO 3 de leur perso de base, sauf $78 et $7E (cf. agent_hyper_index/tables_102.tsv).
Sortie : tables_hyper.json {id: {"ptr":..., "codes": [...]}}"""
import struct, json, csv
M = "<workspace>/anthology_extract/decompressed/ro9_usa_prog68k.bin"
d = open(M, "rb").read()
B = 0x1F0000
ids = {int(r["id"][1:], 16): r for r in csv.DictReader(open("<workspace>/work/agent_hyper_index/ids_102.tsv"), delimiter="\t")}
out = {}
for i in range(128):
    p = struct.unpack_from("<I", d, 0x6AE614 - B + 4 * i)[0]
    o = p - B
    codes = []
    for k in range(80):
        c, a, z1, z2 = struct.unpack_from("<4H", d, o + 8 * k)
        if z1 or z2 or not (c == 0 or 0x200 <= c <= 0x6ff) or not (a == 0 or 0x200 <= a <= 0x6ff): break
        codes.append(c)
    r = ids.get(i, {})
    out["%02x" % i] = dict(ptr="%06x" % p, version=r.get("version", ""), base=r.get("base", ""), nom=r.get("nom", ""), codes=["%04x" % c for c in codes])
json.dump(out, open("<workspace>/work/agent_son_hyper_rom/catalogue/tables_hyper.json", "w"), indent=0)
for i in (0x00, 0x01, 0x30, 0x41, 0x78, 0x7e):
    v = out["%02x" % i]; print("%02x %s %s %s : %s" % (i, v["ptr"], v["version"], v["nom"], " ".join(v["codes"])))
