#!/usr/bin/env python3
"""Constantes d'adresse du code relatives a la base RAM de chaque module (ro3 0x900000, ro5 0xA00000, ro9 0xB80000) :
memes registres materiels emules (HWREG, +0x62xxx), memes variables du portage ? Compte par zone et ecarts."""
import collections, os
os.environ.setdefault("GRAIN", "routine")
import commun as C, tables_ref as R
ZONES = [(-0x80000, 0, "sous la RAM (variables du portage, $88xxxx chez ro3)"), (0, 0x10000, "RAM de travail ($FF0000)"),
         (0x10000, 0x14000, "memoire d'objets ($700000/$708000)"), (0x14000, 0x20000, "+0x14000..0x1FFFF (non resolu)"),
         (0x20000, 0x50000, "video CPS2 ($900000-$92FFFF)"), (0x50000, 0x60000, "+0x50000..0x5FFFF (portage)"),
         (0x60000, 0x62000, "QSound ($618000)"), (0x62000, 0x80000, "+0x62000.. registres emules / portage ($96xxxx)")]
def rel_consts(mod):
    rb = C.ram_base(mod); de = C.header(mod)['fin_exec']; c = collections.Counter()
    for v, sites in R.cmap(mod)[1].items():
        r = v - rb
        if -0x80000 <= r < 0x80000 and v >= de: c[r] += len(sites)
    return c
if __name__ == "__main__":
    S = {m: rel_consts(m) for m in ('ro3', 'ro5', 'ro9')}
    print("zone (relative a la base RAM)                         distinctes ro3/ro5/ro9   ; communes ro3&ro9 ; propres ro9")
    for lo, hi, nom in ZONES:
        z = {m: {r for r in S[m] if lo <= r < hi} for m in S}
        print("  %-52s %5d %5d %5d ; %5d ; %5d" % (nom, len(z['ro3']), len(z['ro5']), len(z['ro9']), len(z['ro3'] & z['ro9']), len(z['ro9'] - z['ro3'] - z['ro5'])))
        prop = sorted(z['ro9'] - z['ro3'] - z['ro5'])
        if prop and len(prop) < 40: print("      propres a ro9 : %s" % ' '.join('%+#x' % r for r in prop))
    hw = [0x62184,0x62186,0x62188,0x6218a,0x6218c,0x62198,0x6219a,0x621a0,0x62146,0x62150] + [0x62118+r for r in range(0,0x18,2)] + list(range(0x62190,0x62197)) + [0x62100+4*k for k in range(6)]
    print("HWREG/INPUT/WIDEREG de translate.py (%d adresses relatives) : presentes ro3 %d, ro5 %d, ro9 %d" % (
        len(hw), sum(1 for r in hw if r in S['ro3']), sum(1 for r in hw if r in S['ro5']), sum(1 for r in hw if r in S['ro9'])))
    print("drapeau de page d'objets +0x621A0 : ro3 %d sites, ro9 %d sites" % (S['ro3'][0x621a0], S['ro9'][0x621a0]))
