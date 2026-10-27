"""Rosette par la TRADUCTION (2026-10-07, idée utilisateur « regarder Ryu sur SFA3 ») : pour chaque routine PSP d'un perso
de SFA3 qui appelle une fonction moteur restant à écrire, on la traduit (traduire.py) puis on cherche la routine arcade
du même perso la plus ressemblante (LCS des lignes normalisées, comme evaluer.py). Sortie : paires (score, arcade, PSP,
fonction visée) dans rosette_ryu.json, à lire côte à côte (cote_a_cote.py)."""
import json, sys, collections
import rosette
from appels import arcade_calls
from traduire import traduire, img, decode
from charcode2 import fstart, fend
from evaluer import norm_arc, norm_tr, lcs
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import modules
J = json.load(open("api_a_fournir.json"))
CIBLES = {int(f["psp"], 16) for f in J if not f["auto"] and not f["main"]}
persos = [int(x, 16) for x in sys.argv[1:]] or [0x00]
out = []
for c in persos:
    ent, lo, hi = rosette.ARC_ENTRIES[c]
    A, seen, tables = arcade_calls(ent, lo, hi)
    debuts = sorted(set(ent) | {t for v in tables.values() for t in v} |
                    {int(i.op_str.split("$")[-1], 16) for i in seen.values() if i.mnemonic.startswith("bsr") and "$" in i.op_str})
    norm = {}
    for a in debuts:
        try: n = norm_arc(a)
        except Exception: continue
        if n and len(n) >= 4: norm[a] = n
    a0, e0 = modules.module_bounds()[c]
    appelants = collections.defaultdict(set)
    for i in decode(img, a0, e0):
        if i.m == "jal" and i.tgt in CIBLES: appelants[fstart(i.va)].add(i.tgt)
    for fp, xs in appelants.items():
        try: T = norm_tr(traduire(fp))
        except Exception: continue
        if not T: continue
        best = max(((2 * lcs(n, T) / (len(n) + len(T)), a) for a, n in norm.items()), default=(0, None))
        out.append({"perso": c, "psp": "%x" % fp, "arcade": "%x" % best[1] if best[1] else None, "score": round(best[0], 2),
                    "visees": ["%x" % x for x in sorted(xs)]})
        print("perso %02x  PSP %x -> arcade %s (%.2f)  appelle %s" % (c, fp, out[-1]["arcade"], best[0], out[-1]["visees"]))
json.dump(out, open("rosette_ryu.json", "w"), indent=1)
