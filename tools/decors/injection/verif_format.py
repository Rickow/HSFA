"""Controle du format traduit : tilemaps du decor reconstruites depuis l'image ro3 (codes locaux) -> codes arcade par
les tables du banc (plan1 / plan2 / f312 : local -> indice ROM) = tilemaps reconstruites depuis le programme arcade."""
import sys, os, struct, collections
sys.path[:0] = [os.path.dirname(__file__), "<workspace>/work/decors_ws/reimport"]
import image, blocs_tr as BT, blocs as BA
d = image.lit(sys.argv[1] if len(sys.argv) > 1 else "trav/roms_tr/sfa3ud"); M = BT.MOD["ro3"]
a = open(BA.PROG, "rb").read()
BAN = "<workspace>/work/mame/banques/"
tab = {1: (open(BAN + "plan1.bin", "rb").read(), 0x20000), 2: (open(BAN + "plan2.bin", "rb").read(), 0x10000),
       3: (open(BAN + "f312.bin", "rb").read(), 0x4000)}
def glob(L, c):
    t, sub = tab[L]
    if 4 * c + 4 > len(t): return None
    g = struct.unpack_from("<I", t, 4 * c)[0]
    return None if g == 0xFFFFFFFF else g - sub
for dec in [int(x, 16) for x in (sys.argv[2:] or ["0C"])]:
    for L in (1, 2, 3):
        Tt = BT.cases_tilemap(d, M, L, dec); Ta = BA.cases_tilemap(a, L, dec)
        st = collections.Counter()
        for k, (ca, aa) in Ta.items():
            v = Tt.get(k)
            if v is None: st["absente"] += 1; continue
            g = glob(L, v[0])
            if (v[1] & 0xFF) != (aa & 0xFF): st["attr"] += 1
            if g is None: st["hors_table"] += 1
            elif (g & 0xFFFF) == ca or (L == 3 and (g & 0x3FFF) == (ca & 0x3FFF)): st["ok"] += 1
            else: st["code"] += 1
        print("decor %02X scroll%d : listes tr %s arc %s ; %s" % (dec, L, BT.liste(d, M, L, dec)[1][:8], BA.liste(a, L, dec)[1][:8], dict(st)))
