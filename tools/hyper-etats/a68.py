#!/usr/bin/env python3
"""a68.py va_mips... : adresse 68K (premiere ligne de carte_image.txt dans [va, va+0x40)) de chaque routine MIPS"""
import sys, bisect, collections
par_va = collections.defaultdict(list)
for l in open("<workspace>/work/mame_ro9/carte_image.txt"):
    a, va, _ = l.split(" ", 2); par_va[int(va, 16)].append(int(a, 16))
vas = sorted(par_va)
for x in sys.argv[1:]:
    t = int(x, 16); i = bisect.bisect_left(vas, t)
    r = "$%06x" % min(par_va[vas[i]]) if i < len(vas) and vas[i] < t + 0x40 else "(absent)"
    print("%s %s%s" % (x, r, "" if i >= len(vas) or vas[i] == t else "  (ligne en %06x)" % vas[i]))
