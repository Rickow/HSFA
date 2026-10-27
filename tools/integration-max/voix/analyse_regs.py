#!/usr/bin/env python3
"""Controle registre par registre des voix MAX injectees (journal de voix.lua) contre attribution.json :
voie 11 (registres $58-$5F, banque = registre $50), debut, fin, boucle, hauteur, volume, duree de la note.
Usage : analyse_regs.py journal.txt [attribution.json] [cote2]"""
import sys, json, os
ICI = os.path.dirname(os.path.abspath(__file__))
j = sys.argv[1]
att = json.load(open(sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].endswith(".json") else os.path.join(ICI, "roms_voix/attribution.json")))
cle = "cmd2" if "cote2" in sys.argv else "cmd"
par = {int(v[cle], 16): v for v in att}
blocs, cur = {}, None
for l in open(j):
    t = l.split()
    if t[0] == "C": cur = int(t[2], 16); blocs[cur] = []
    elif t[0] == "Q" and cur is not None: blocs[cur].append((float(t[1]), int(t[2], 16), int(t[3], 16)))
ok = 0
for c, v in par.items():
    w = blocs.get(c, [])
    e = bytes.fromhex(v["entree"].replace(" ", ""))
    bank, deb, bou, fin = e[0], e[1] | e[2] << 8, e[3] | e[4] << 8, e[5] | e[6] << 8
    r = {}
    for tt, reg, val in w: r.setdefault(reg, []).append((tt, val))
    err = []
    if (0x8000 | bank) not in [x for _, x in r.get(0x50, [])]: err.append("banque")
    if deb not in [x for _, x in r.get(0x59, [])]: err.append("debut")
    if fin not in [x for _, x in r.get(0x5D, [])]: err.append("fin")
    if (fin - bou) not in [x for _, x in r.get(0x5C, [])]: err.append("boucle")
    if v["hauteur"] not in [x for _, x in r.get(0x5A, [])]: err.append("hauteur %s" % sorted(set(x for _, x in r.get(0x5A, []))))
    vol = [(tt, x) for tt, x in r.get(0x5E, [])]
    on = [tt for tt, x in vol if x]
    off = [tt for tt, x in vol if x == 0 and on and tt > on[0]]
    dur = (off[0] - on[0]) if on and off else None
    if dur is None or abs(dur - v["duree_note"]) > 0.02: err.append("duree %s / %s" % (dur, v["duree_note"]))
    v["_vol"] = sorted(set(x for _, x in vol if x))
    if err: print("%04X %s v%02d : %s" % (c, v["perso"], v["n"], ", ".join(err)))
    else: ok += 1
print("%s : %d/%d commandes conformes (banque, debut, fin, boucle, hauteur, duree de la note) ; volumes voie 11 : %s"
      % (os.path.basename(j), ok, len(par), sorted(set(x for v in par.values() for x in v["_vol"]))))
