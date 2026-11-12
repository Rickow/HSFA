#!/usr/bin/env python3
"""releve_palettes.py -- Upper MAX arbitrations (A6, finding B7: EFFECT palettes cut at 30): for each MAX character,
palettes of the converted file beyond 30, duplicates within 0-29, and what the engine reads in their place in a build
(table moved into the ext_b80000 block); PSP side, palettes 30-35 of the native characters (pac pl00-pl25) compared
with Upper's block of the same id. Run it on a build with MAX_PALE_PLEINES=1 to check the switch before benching it.

Usage:  python3 -I releve_palettes.py BENCH CONVERTED PSP_PAC [ro5_usa_prog68k.bin]
        BENCH     bench folder of an Upper MAX build (max_journal.txt, ext_b80000.bin)
        CONVERTED folder of the converted MAX characters (<cache>/max_regen/converti)
        PSP_PAC   folder of the PSP character pacs (<cache>/max_regen/psp/pac)
        ro5 from $HSFA_MODULES / $HSFA_CACHE unless given. Output: text (French labels). Read only.
bloc_effets / convert: copied from max/outils/convert/palettes_max.py (MAX session, read only); plpac.split is imported
from tools/max/ (read only).
"""
import sys, os, struct, re
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
if len(sys.argv) < 4: sys.exit(__doc__)
BANC = paths.banc(sys.argv[1])
CV = sys.argv[2]
PAC = sys.argv[3]
RO5 = paths.module(sys.argv[4] if len(sys.argv) > 4 else "ro5")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "max"))   # tools/max (= paths.MAX_OUTILS)
from plpac import split                                    # lecture seule (tools/max)

def bloc_effets(b6):
    ispal = lambda a: a + 32 <= len(b6) and all(x & 0x8000 for x in struct.unpack_from("<16H", b6, a)[1:15])
    a = 0
    while a < len(b6) - 32:
        if ispal(a):
            n = 0
            while ispal(a + 32 * n): n += 1
            if n >= 4: return a, n
            a += 32
        else: a += 2
    return None, 0
def convert(pal):
    mod = []
    for k in range(len(pal) // 32):
        cols = []
        for r in range(15):
            v = struct.unpack_from("<H", pal, 32 * k + 2 * (r + 1))[0]
            cols.append(((v & 31) >> 1) << 8 | (((v >> 5) & 31) >> 1) << 4 | ((v >> 10) & 31) >> 1)
        mod += cols + [k]
    return mod

MAX = (("Eagle", 0x26, "pl26"), ("Maki", 0x27, "pl27"), ("Yun", 0x2D, "pl28"), ("Ingrid", 0x2E, "pl29"))
cols = lambda d, k: tuple(struct.unpack_from("<15H", d, 32 * k))      # 15 couleurs (mot 15 = n°, ignoré)
# --- construction : table déplacée (journal « palettes d'effets : table déplacée en $xxxxxx »)
jr = open(os.path.join(BANC, "max_journal.txt"), encoding="utf-8").read()
tab_img = int(re.search(r"palettes d'effets : table déplacée en \$([0-9a-f]+)", jr).group(1), 16)
ext = open(os.path.join(BANC, "ext_b80000.bin"), "rb").read()
le = bytes(ext[k ^ 1] for k in range(len(ext)))                       # image -> ordre PS2 (petit-boutiste)
t0 = tab_img - 0xB80000
tab = struct.unpack_from("<64h", le, t0)
debut = {}                                                              # début de bloc -> ids qui le partagent
for i, v in enumerate(tab[:0x30]): debut.setdefault(v, []).append(i)
blocs = sorted(debut)
# --- Upper d'origine : table 0x700540 (40 décalages s16 relatifs à la table), taille des blocs = écart au suivant
T = 0x700540 - 0x1F0000
up = struct.unpack_from("<40h", RO5, T)
ub = sorted(set(up))
utaille = {b: (ub[k + 1] - b) // 32 if k + 1 < len(ub) else None for k, b in enumerate(ub)}
print("== MAX : fichier converti, bloc posé (30), ce qui est lu au-delà")
for nom, i, pl in MAX:
    f = os.path.join(CV, pl, "palettes_effets_module.bin"); fu = f.replace(".bin", "_upper.bin")
    d = open(fu if os.path.exists(fu) else f, "rb").read(); n = len(d) // 32
    nz = [k for k in range(30, n) if any(cols(d, k))]
    dup = [k for k in range(30, n) if cols(d, k) in {cols(d, j) for j in range(30)}]
    b = tab[i]; k_ = blocs.index(b); suiv = blocs[k_ + 1] if k_ + 1 < len(blocs) else None
    ids = debut.get(suiv, [])
    egal = [k for k in range(30, n) if t0 + b + 32 * k + 32 <= len(le) and cols(le[t0 + b:], k) == cols(d, k)]
    print("%-6s $%02X : %d palettes dans le fichier%s ; > 29 non nulles : %d (%s) ; déjà dans 0-29 : %d (%s)" % (
        nom, i, n, " (_upper)" if os.path.exists(fu) else "", len(nz), ",".join(map(str, nz)), len(dup), ",".join(map(str, dup))))
    if suiv is not None:
        quoi = "palette k du bloc suivant (table%+d : ids %s)" % (suiv, ",".join("$%02X" % x for x in ids) or "?")
    else:
        z = le[t0 + b + 32 * 30:t0 + b + 32 * n]
        quoi = "fin de la zone : %d palettes nulles (noires) sur %d" % (sum(1 for k in range(0, len(z), 32) if not any(z[k:k + 30])), n - 30)
    print("        bloc posé en table%+d ; palette 30+k lue = %s ; palettes 30+ du fichier = ce qui est lu : %d/%d" % (
          b, quoi, len(egal), n - 30))
print("== Natifs : PSP (pac pl00-pl25, bloc d'effets) contre Upper (0x700540)")
for j in range(0x26):
    p = os.path.join(PAC, "pl%02x_e.pac" % j)          # n° de pac = id en hexadécimal (pl26 = Eagle $26)
    if not os.path.exists(p) or j >= 40: continue
    try: b6 = split(open(p, "rb").read())[6][1]
    except Exception as e: print("pl%02x : %s" % (j, e)); continue
    a, n = bloc_effets(b6)
    if a is None: print("pl%02x : pas de bloc d effets" % j); continue
    m = convert(b6[a:a + 32 * n]); mb = struct.pack("<%dH" % len(m), *m)
    ut = utaille[up[j]]
    ue = RO5[T + up[j]:T + up[j] + 32 * (ut or 30)]
    eg = sum(cols(mb, k) == cols(ue, k) for k in range(min(n, ut or 30)))
    nz = [k for k in range(30, n) if any(cols(mb, k))]
    print("pl%02x id $%02X : PSP %d palettes, Upper %s ; égales %d ; PSP > 29 non nulles : %s" % (
        j, j, n, ut, eg, ",".join(map(str, nz)) or "-"))
