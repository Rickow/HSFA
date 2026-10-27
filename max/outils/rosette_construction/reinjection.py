"""Réinjection des paires de routines établies par les IMAGES dans la Rosette du code (2026-10-11).
Paires retenues par perso : celles de chaine_code.py sans conflit + conflits gagnés par les images (conflits.py) ;
les conflits gagnés par la Rosette du code ou indécis sont laissés au vote d'origine.
Mesure : consensus des correspondances de fonctions moteur (rosette.consensus) avant / après.
Usage : python reinjection.py"""
import os, sys, json
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "rosette_code"))
os.chdir(os.path.join(ICI, "..", "rosette_code"))
import rosette as RS, chaine_code as CC, conflits as CF

if __name__ == "__main__":
    imp = {}
    for c in sorted(RS.ARC_ENTRIES):
        if c in (0x11, 0x13, 0x1f): continue
        try: r = CC.chaine(c)
        except Exception as e: print("pl%02x : %s" % (c, e)); continue
        verdict = {int(l[0], 16): l[-1] for l in CF.arbitrer(c)}
        imp[c] = {fa: fp for fa, fp in r["RP"].items() if verdict.get(fa, "IMAGES") == "IMAGES"}
    base, _ = RS.consensus(RS.all_chars())
    neuf, _ = RS.consensus(RS.all_chars(imposees=imp))
    ajout = {a: p for a, p in neuf.items() if a not in base}
    retrait = {a: p for a, p in base.items() if a not in neuf}
    change = {a: (base[a], neuf[a]) for a in base if a in neuf and base[a] != neuf[a]}
    print("fonctions moteur appariées (consensus) : avant %d, après %d ; ajouts %d, retraits %d, changements %d"
          % (len(base), len(neuf), len(ajout), len(retrait), len(change)))
    json.dump({"ajouts": {"%x" % a: "%x" % p for a, p in ajout.items()},
               "retraits": {"%x" % a: "%x" % p for a, p in retrait.items()},
               "changements": {"%x" % a: ["%x" % x, "%x" % y] for a, (x, y) in change.items()},
               "imposees": {"%02x" % c: {"%x" % a: "%x" % p for a, p in d.items()} for c, d in imp.items()}},
              open(os.path.expanduser("~/.cache/sfa3max/rosette/reinjection.json"), "w"), indent=1)
    for a, p in sorted(ajout.items()): print("  + arcade %06x <-> PSP %06x" % (a, p))
    for a, (x, y) in sorted(change.items()): print("  ~ arcade %06x : PSP %06x -> %06x" % (a, x, y))
