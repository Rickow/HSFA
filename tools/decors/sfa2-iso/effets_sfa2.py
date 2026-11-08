#!/usr/bin/env python3
"""effets_sfa2.py (côté ORACLE, local) — rowscroll de scroll2 (« effet par décor », arcade sfa2u $1D836, table $1D842) :
lit les 15 gestionnaires dans le désassemblage de sfa2u (carto_sfa2/dump/sfa2u/dasm.txt) et en tire les CONSTANTES du
modèle (pas de données de jeu) : diviseur k, nombre de lignes des segments ; vérifie le modèle contre la table rowscroll
de la VRAM des vidages de la sonde. Écrit donnees/effets.json (constantes reprises dans le rapport).
Modèle « sol en perspective » (même famille que SFA1, extrait_sfa1 EFFETS) : d = (X2 − X2init) / k (16.16) ;
  base = $3D8 (= $7B0 / 2, comme SFA1) ; lignes base + i, i = 0..n1-1 : $C0 + ⌊i·d⌋ ; lignes base − 1 − i, i = 0..n2-1 : $C0 + ⌊−(i+1)·d⌋ ;
  puis n3 lignes constantes ; [variante Birdie : puis n4 lignes qui remontent : $C0 + ⌊−(n2 − i)·d⌋…]."""
import re, sys, os, json, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_mame as M
DASM = "<workspace>/work/carto_sfa2/dump/sfa2u/dasm.txt"
GEST = {0: None, 1: 0x1d86a, 2: 0x1d8c4, 3: None, 4: 0x1d928, 5: None, 6: 0x1d988, 7: 0x1d9e8, 8: 0x1da48, 9: 0x1dac0,
        10: None, 11: 0x1db20, 12: 0x1db80, 13: 0x1dbe0, 14: 0x1dc3a, 15: 0x1dc9a, 16: None, 17: 0x1dd48}
import subprocess, tempfile
OPC = "<workspace>/work/carto_sfa2/dump/sfa2u/prog_opcodes.bin"
def code(a):
    """désassemble à partir de a (unidasm, espace opcodes) jusqu'au premier rts"""
    with tempfile.NamedTemporaryFile(suffix=".bin") as t:
        t.write(open(OPC, "rb").read()[a:a + 0x200]); t.flush()
        out = subprocess.run(["unidasm", t.name, "-arch", "m68000", "-basepc", "%x" % a], capture_output=True, text=True).stdout
    res = []
    for l in out.splitlines():
        m = re.match(r"^[0-9a-f]+: (?:[0-9a-f]{4} )+\s*(.*)$", l)
        if not m: continue
        res.append(m.group(1).strip())
        if res[-1].startswith("rts"): break
    return res
def params(a):
    c = code(a); p = dict(adresse="$%05X" % a)
    for x in c:
        m = re.match(r"asr\.l\s+#(\d+), D3", x)
        if m: p["k"] = 1 << int(m.group(1)); p["division"] = "asr"
        m = re.match(r"(?:moveq|move\.l)\s+#\$([0-9a-f]+), D2", x)
        if m and "k" not in p: p["k"] = int(m.group(1), 16); p["division"] = "signée ($190AA)"
    n = [int(m.group(1), 16) + 1 for x in c for m in [re.match(r"(?:moveq|move\.w)\s+#\$([0-9a-f]+), D1", x)] if m]
    p["segments"] = n
    p["remontee"] = any("($8,A4)" in x for x in c)
    if "k" not in p: p["type"] = "autre (vague, table de sinus ; " + " ; ".join(c[:4]) + "…)"
    return p
def modele(p, x2, x0, base):
    r = np.full(1024, -1, np.int64)
    x = x2 - x0
    if p["division"] == "asr": d = x >> 7 if p["k"] == 128 else x // p["k"]
    else:
        d = abs(x) // p["k"]; d = -d if x < 0 else d
    n = p["segments"]; acc = 0
    for i in range(n[0]):
        r[(base + i) & 0x3FF] = (0xC0 + (acc >> 16)) & 0xFFFF; acc += d
    acc = 0; v = 0xC0; j = base
    for i in range(n[1]):
        acc -= d; v = (0xC0 + (acc >> 16)) & 0xFFFF; j -= 1; r[j & 0x3FF] = v
    for i in range(n[2]): j -= 1; r[j & 0x3FF] = v
    if p["remontee"] and len(n) > 3:
        acc8 = acc
        for i in range(n[3]): j -= 1; r[j & 0x3FF] = (0xC0 + (acc8 >> 16)) & 0xFFFF; acc8 += d
    return r
res = {}
for s, a in GEST.items():
    if a is None: res["$%02X" % (2 * s)] = dict(type="aucun (rts : rowscroll constant +$C0)"); continue
    p = params(a); res["$%02X" % (2 * s)] = p
    f = "mame/out/stg%02X_dmp.bin" % (2 * s)
    if "k" in p and os.path.exists(f):
        ver = []
        for d in M.lit(f):
            A = d["A"]; ram = d["ram"]
            rows = M.mots(d["gfx"], A[4], 1024).astype(np.int64)
            x2 = struct.unpack_from(">i", ram, 0x290)[0]; x0 = struct.unpack_from(">i", ram, 0x288)[0]
            base = 0x3D8                          # mot ($20,A4) = $7B0 (comme SFA1 : ligne de base $7B0 / 2)
            m = modele(p, x2, x0, base); k = m >= 0
            ver.append("%s:%d/%d" % (d["tag"].strip(), int((rows[k] == m[k]).sum()), int(k.sum())))
        p["controle_vram"] = ver
    print("$%02X" % (2 * s), json.dumps(p, ensure_ascii=False))
json.dump(res, open("donnees/effets.json", "w"), indent=1, ensure_ascii=False)
