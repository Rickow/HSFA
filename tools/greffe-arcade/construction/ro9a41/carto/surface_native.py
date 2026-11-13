#!/usr/bin/env python3
"""Surface native selon les criteres EXACTS de l'outillage (natmiss.native, boucle de hooks_fork.main, recopiee ici
pour ne PAS ecrire hooks_fork_<mod>.json dans le dossier des scripts). Usage : MODULE=ro9 surface_native.py"""
import os, sys, json, struct, collections
sys.path.insert(0, "@HA_UT@")
mod = os.environ.get("MODULE", "ro9")
import natmiss
from mips import decode
buf = open("@HA_EXTRACT@/decompressed/%s_usa_prog68k.bin" % mod, "rb").read()
end = struct.unpack_from('<I', buf, 12)[0]
L = list(decode(buf, 0x22b00, end))
sites = collections.defaultdict(list)
for x in L:
    if x.m != 'jal': continue
    if natmiss.native(natmiss.fidx(x.va)): continue
    t = x.tgt - 0x1f0000
    if t < 0 or t >= end: kind = 'moteur PS2'
    elif natmiss.native(natmiss.fidx(t)): kind = 'natif du module'
    else: continue
    sites[(kind, t)].append(x.va)
nat = [natmiss.starts[f] for f in range(len(natmiss.starts)) if natmiss.native(f)]
per = collections.Counter(k for k, _ in sites); ns = collections.Counter()
for (k, t), v in sites.items(): ns[k] += len(v)
print("%s : fonctions natives %d ; cibles %s ; sites %s" % (mod, len(nat), dict(per), dict(ns)))
for (k, t), v in sorted(sites.items(), key=lambda kv: -len(kv[1]))[:30]:
    print("   %-16s cible fichier %#08x (exec %#08x) : %3d sites  ex. %s" % (k, t & 0xffffffff if t >= 0 else t, t + 0x1f0000, len(v), ' '.join('%x' % s for s in v[:4])))
json.dump({"%x" % t: {"type": k, "sites": ["%x" % s for s in v]} for (k, t), v in sites.items()},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooks_fork_%s_carto.json" % mod), "w"), indent=0)
json.dump(["%x" % a for a in nat], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "natives_%s.json" % mod), "w"))
