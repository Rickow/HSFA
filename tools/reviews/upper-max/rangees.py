#!/usr/bin/env python3
"""rangees.py -- Upper MAX review (B): per-id tables of tables_par_id.json (+ AJOUTEES / MULTI of agrandit_max.py):
gap up to the next known table compared with n x e. Reports the tables declared with one row whose room is
k x (n x e), k >= 2 (possible rows not declared in MULTI).

Usage:  python3 -I rangees.py
Input:  tools/integration-max/upper_max/integration_2b31/ag/ of the repository (no game data). Output: text.
"""
import sys, os, json, re
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
J = json.loads(paths.lit_texte(os.path.join(paths.AG, "outils", "tables_par_id.json")))
src = paths.lit_texte(os.path.join(paths.AG, "untranspile", "agrandit_max.py"))
T = {int(t["ps2"], 16): (t.get("n", 40), t["e"], t["kind"], t["role"][:70]) for t in J}
multi = {int(m, 16) for m in re.findall(r"^\s+\((0x[0-9A-F]+), \d, \d, \[", src, re.M)}
for m in re.finditer(r"\((0x[0-9A-F]{6}), (\d), (\d+), \"", src): T.setdefault(int(m.group(1), 16), (int(m.group(3)), int(m.group(2)), "ajoutee", ""))
ks = sorted(T)
for a, b in zip(ks, ks[1:] + [None]):
    n, e, k, r = T[a]
    if k not in ("simple", "code", "ajoutee") or b is None: continue
    d = b - a; t = n * e
    if d >= 2 * t and d % t == 0 and d // t <= 8:
        print("%X  n=%d e=%d  place jusqu'à %X = %d × (n×e) %s %s" % (a, n, e, b, d // t, "[MULTI]" if a in multi else "[1 rangée déclarée]", r))
