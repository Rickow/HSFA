#!/usr/bin/env python3
"""anims_observees.py (oracle, local) : animations de sprites vues dans les chronologies MAME (mame/out_chrono), rangées
par racine de table -> outils/anims_observees.json {racine: [animations]} (adresses et numéros seulement).
La racine de chaque classe est celle que lit son gestionnaire (code 68K de sfa2u, RAPPORT §5) : les sous-tables
$21B7BE…$21B992 sont des tables distinctes (décalages relatifs à leur propre racine) qui se chevauchent.
Les objets hors décor (combattants, effets : classes $03-$07, $0E, $0F, $27, $3B du pool A ; $00, $0E du pool C)
sont ignorés."""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arcade_anims as AA, analyse_chrono as AC
HORS = {"03", "04", "05", "07", "0e", "0f", "27", "3b"}
RACINE_A = {0x23: 0x21B8A6, 0x38: 0x21B864, 0x3C: 0x21B864, 0x3E: 0x21B864, 0x40: 0x21B930, 0x41: 0x21B930,
            0x42: 0x21B954, 0x43: 0x21B8B4, 0x45: 0x21B82A, 0x47: 0x21B846, 0x48: 0x21B7F4, 0x4A: 0x21B7F4,
            0x4B: 0x21B982, 0x4E: 0x21B7B6, 0x4F: 0x21B7BE, 0x50: 0x21B878, 0x51: 0x21B982, 0x52: 0x21B930,
            0x54: 0x21B82A, 0x57: 0x21B930, 0x58: 0x21B954, 0x59: 0x21B954, 0x5A: 0x21B954, 0x5B: 0x21B7BE,
            0x5C: 0x21B7BE, 0x60: 0x21B954, 0x62: 0x21B8E8, 0x64: 0x21B878, 0x68: 0x21B942, 0x69: 0x21B846,
            0x6A: 0x21B914, 0x6B: 0x21B8E8, 0x6C: 0x21B914, 0x6E: 0x21B954, 0x39: 0x06A55C, 0x67: 0x21B878, 0x3D: 0x21B8E8}
RACINE_B = {0: 0x21B7B6, 1: 0x21B8E8, 2: 0x21B7EA, 3: 0x21B8B4, 4: 0x21B992, 5: 0x21B8A6}
RACINE_C = {0x15: 0x21B930, 0x16: 0x21B930, 0x17: 0x21B878, 0x18: 0x21B82A, 0x19: 0x21B914}

def racine(pool, cls, sub):
    if pool == "A" and cls == 0:
        v = AA.l(0x5B3EE + 4 * sub, AA.O); return v & 0xFFFFFF
    if pool == "A" and cls == 0x4D:                      # table $6E308 : 8 o par sous-type (racine, animation)
        return AA.l(0x6E308 + 8 * sub, AA.O) & 0xFFFFFF
    return {"A": RACINE_A, "B": RACINE_B, "C": RACINE_C}[pool].get(cls)

_cache = {}
def anim_de(T, f):
    if T not in _cache:
        m = {}
        for i in AA.anims_valides(T, 16):
            for fr in AA.walk(T, i, 16)[0]: m.setdefault(fr[0], i)
        _cache[T] = m
    return _cache[T].get(f)

if __name__ == "__main__":
    obs = collections.defaultdict(set); par = collections.defaultdict(lambda: collections.defaultdict(set)); inc = collections.Counter()
    for s in range(0, 0x24, 2):
        stg = "%02X" % s; E = AC.lit(stg)
        for k, pool, slot, act, cls, sub, fr, dur, x, y in E["o"]:
            f = int(fr, 16) & 0xFFFFFF
            if f == 0 or (pool == "A" and cls in HORS) or (pool == "C" and cls in ("00", "0e")): continue
            T = racine(pool, int(cls, 16), int(sub, 16))
            i = anim_de(T, f) if T else None
            if i is None: inc["%s %s%s.%s %06X" % (stg, pool, cls, sub, f)] += 1; continue
            obs["$%06X" % T].add(i); par[stg]["%s%s.%s" % (pool, cls, sub)].add("$%06X/%d" % (T, i))
    json.dump({k: sorted(v) for k, v in obs.items()}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "anims_observees.json"), "w"), indent=0)
    for k, v in sorted(obs.items()): print(k, len(v), sorted(v))
    for stg, d in sorted(par.items()): print(stg, {c: sorted(v) for c, v in d.items()})
    print("cadres sans racine connue :", len(inc))
    for x in sorted({" ".join(k.split()[:2]) for k in inc}): print("  ", x)
