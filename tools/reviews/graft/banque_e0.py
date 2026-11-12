#!/usr/bin/env python3
"""banque_e0.py -- graft review (DECOR_E0, common sprite bank): in Upper's type-2 sprite frames copied by the graft,
list the entries (code, attr) of which a tile < $33F0 has a different common-bank entry in Hyper (f545) and Upper
(f351) ("class B"), and tell whether DECOR_E0 recoded them (stage zone) or not, and why.

Usage:  python3 -I banque_e0.py [frozen_build] > sorties/banque_e0.txt
Inputs: frozen graft build (argument or $HSFA_GRAFT_BUILD: banques_hx/f545.bin, banques_hx/f351.bin, zone_decors.bin,
        greffe.json), module ro5 ($HSFA_MODULES), file 390 ($HSFA_F390). See paths.py.
Output: counts, then the list of the class-B entries. Read only.
"""
import struct, json, bisect, collections, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
C = paths.construction(sys.argv[1] if len(sys.argv) > 1 else None); BASE = paths.BASE
b5 = paths.lit_module("ro5")
CE, HI = struct.unpack_from('<I', b5, 12)[0], struct.unpack_from('<I', b5, 24)[0]; LO = BASE + CE
F390 = 0xB04000; F390_1 = F390 + os.path.getsize(paths.f390())
h = open(os.path.join(C, "banques_hx", "f545.bin"), "rb").read(); u = open(os.path.join(C, "banques_hx", "f351.bin"), "rb").read()
H = struct.unpack('<%dI' % (len(h) // 4), h); U = struct.unpack('<%dI' % (len(u) // 4), u)
NH = 0x33F0
J = json.load(open(os.path.join(C, "greffe.json"), encoding="utf-8"))
R = sorted((int(a, 16), int(b, 16)) for a, b, o in J['regions']); RA = [a for a, b in R]
zl, zh = int(J['zone_decors'][0], 16), int(J['zone_decors'][1], 16)
zb = open(os.path.join(C, "zone_decors.bin"), "rb").read(); zpad = len(zb) - (zh - zl)
def copie(p):
    k = bisect.bisect_right(RA, p) - 1
    return k >= 0 and R[k][0] <= p < R[k][1]
def tuiles(c, at):
    W_, Hh = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
    return [((c & ~0xf) + (((c & 0xf) + i) & 0xf) + 0x10 * j) & 0xffff for j in range(Hh) for i in range(W_)]
st = collections.Counter(); out = []
for a in range(LO, HI - 12, 2):
    o = a - BASE
    w0, w1, w2, w3 = struct.unpack_from('<4H', b5, o)
    if w0 != 2 or w3 != 0 or w2 > 0x3FF: continue
    p = struct.unpack_from('<I', b5, o + 8)[0]
    if not (F390 <= p < F390_1) or not copie(a): continue
    dz = zl <= a < zh
    zp = struct.unpack_from('<H', zb, zpad + a - zl + 10)[0] if dz else None
    for k in range(w2 + 1):
        e = a + 12 + 4 * k
        if e + 4 > HI: break
        c, at = struct.unpack_from('<2H', b5, e - BASE)
        T = tuiles(c, at)
        B = [t for t in T if t < NH and H[t] != U[t]]
        horsU = [t for t in T if t >= 0x6C60]
        if not B: st[('zone' if dz else 'hors', 'ok')] += 1; continue
        if dz:
            cn = struct.unpack_from('<H', zb, zpad + e - zl)[0]
            if cn != c: st[('zone', 'B recodee')] += 1; continue
            why = 'pal<0F' if (at & 0x1f) < 0xF else 'n>=81' if w2 >= 0x80 else 'ptr390 non reloge en ED/EE (%04x)' % zp if zp not in (0xED, 0xEE) else '?'
            st[('zone', 'B NON recodee : ' + why)] += 1
            out.append("zone trame %x entree %x code %04x attr %04x tuiles B %s : %s" % (a, e, c, at, ','.join('%04x' % t for t in B[:4]), why))
        else:
            st[('hors', 'B pal %s' % ('>=0F' if (at & 0x1f) >= 0xF else '<0F'))] += 1
            if len(out) < 4000: out.append("hors trame %x entree %x code %04x attr %04x" % (a, e, c, at))
for k, n in sorted(st.items()): print(n, *k)
print(); print('\n'.join(out))
