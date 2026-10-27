#!/usr/bin/env python3
"""POINTS DE RACCORDEMENT DU FORK (HANDOFF §55) : appels du jeu RECOMPILE vers du code NATIF
(fonctions natives du module, cf. natmiss.py, ou moteur PS2 hors du module). Ce sont les seuls
endroits ou le jeu traduit sort de lui-meme : le fork FBNeo doit les remplacer (materiel CPS2).
Usage : MODULE=ro3 hooks_fork.py"""
import sys, os, struct, bisect, collections, json
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from mips import decode
import natmiss

SETJMP, LONGJMP = 0x119f48, 0x119fa0      # moteur PS2 (hote) : setjmp(buf) / longjmp(buf, val)

def setjmp_sites(buf, L=None):
    """BRANCHEMENTS ENTRE FONCTIONS DU RECOMPILATEUR (HANDOFF §75) : l'entree d'une routine cible fait
    setjmp(tampon) ; un 'Bcc/BRA' 68K vers elle depuis une AUTRE fonction (appels MIPS en trop sur la
    pile) devient longjmp(tampon, 1), qui revient au point du setjmp avec la pile de ce moment.
    -> {va du jal: ('setjmp'|'longjmp', adresse du tampon)} (a0 = lui/addiu constants au site)."""
    if L is None:
        end = struct.unpack_from('<I', buf, 12)[0]; L = list(decode(buf, 0x22b00, end))
    out = {}
    for i, x in enumerate(L):
        if x.m == 'jal' and x.tgt in (SETJMP, LONGJMP):
            hi = lo = None
            for y in L[max(0, i-6):i+2]:
                if y.m == 'lui' and y.rt == 4: hi = y.imm
                if y.m == 'addiu' and y.rt == 4 and y.rs == 4: lo = y.simm
            assert hi is not None and lo is not None, "tampon de %s non constant en %x" % (x.tgt, x.va)
            out[x.va] = ('setjmp' if x.tgt == SETJMP else 'longjmp', ((hi << 16) + lo) & 0xffffffff)
    return out

def main():
    mod = os.environ.get("MODULE", "ro3")
    buf = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, "rb").read()
    end = struct.unpack_from('<I', buf, 12)[0]; c0 = 0x22de0 if mod == 'ro9' else 0x22b00
    L = list(decode(buf, c0, end))
    starts = natmiss.starts
    sites = collections.defaultdict(list)
    for x in L:
        if x.m != 'jal': continue
        if natmiss.native(natmiss.fidx(x.va)): continue          # appel DEPUIS du natif : sans objet
        t = x.tgt - 0x1f0000
        if t < 0 or t >= end: kind = 'moteur PS2'
        elif natmiss.native(natmiss.fidx(t)): kind = 'natif du module'
        else: continue
        sites[(kind, t)].append(x.va)
    per = collections.Counter(k for k, _ in sites)
    print("%s : %d cibles natives appelees par le jeu (%s), %d sites d'appel" % (
        mod, len(sites), dict(per), sum(len(v) for v in sites.values())))
    for (kind, t), v in sorted(sites.items(), key=lambda kv: -len(kv[1]))[:25]:
        print("   %-16s cible %#08x (hote %#08x) : %3d sites" % (kind, t, t + 0x1f0000, len(v)))
    json.dump({"%x" % t: {"type": k, "sites": ["%x" % s for s in v]} for (k, t), v in sites.items()},
              open(os.path.join(D, "hooks_fork_%s.json" % mod), "w"), indent=0)

if __name__ == "__main__":
    main()
