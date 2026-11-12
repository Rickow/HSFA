#!/usr/bin/env python3
"""essai_controles.py -- Upper MAX review: negative tests of the site checks of integre_max.py (_site_unique, _cible,
_recoupe: the integration finds its sites by unique pattern and decoded jumps, cross-checked with the MIPS va of the
build map, journal section 220) on a synthetic image: pattern absent, pattern twice, unexpected jump, different MIPS va,
address outside the map -> each must raise AssertionError. No game data.

Usage:  python3 -I essai_controles.py [integre_max.py]
        default: tools/integration-max/upper_max/integration_2b31/ag/untranspile/integre_max.py of the repository
Output: one verdict per test; exit code 1 if a check failed to fail.
"""
import sys, os, struct, re
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(paths.AG, "untranspile", "integre_max.py")
src = paths.lit_texte(f)
i = src.index("def _va_image():"); j = src.index("def talon_cond40(")
ns = {"struct": struct}; exec(src[i:j], ns)
img = bytearray(0x4000); m = bytes.fromhex("30183d40020a323b00064efb1002")
def doit_echouer(nom, f):
    try: f()
    except AssertionError as e: print("ok   %-28s -> %s" % (nom, str(e)[:110])); return 0
    print("RATÉ %s : aucun échec" % nom); return 1
n = doit_echouer("motif absent", lambda: ns["_site_unique"](img, m, "essai"))
img[0x1200:0x1200 + len(m)] = m
assert ns["_site_unique"](img, m, "essai") == 0x1200
img[0x1301:0x1301 + len(m)] = m                       # adresse impaire : ignorée
assert ns["_site_unique"](img, m, "essai") == 0x1200
img[0x1400:0x1400 + len(m)] = m
n += doit_echouer("motif en double", lambda: ns["_site_unique"](img, m, "essai"))
n += doit_echouer("saut attendu", lambda: ns["_cible"](img, 0x1000))
struct.pack_into(">HH", img, 0x1000, 0x6100, 0x0100); assert ns["_cible"](img, 0x1000) == (0x1102, 4)
n += doit_echouer("va MIPS différente", lambda: ns["_recoupe"]({0x1200: 0x111}, "essai", 0x1200, 0x78A58))
n += doit_echouer("adresse hors carte", lambda: ns["_recoupe"]({}, "essai", 0x1200, 0x78A58))
print("%d raté(s)" % n); sys.exit(1 if n else 0)
