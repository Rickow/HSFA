#!/usr/bin/env python3
"""Assemblage COMPLET a blanc (rien n'est ecrit hors de ce dossier) d'un module en mode cps2, zone 68K par zone 68K
(zones.py), comme essai_assemblage.py de carto_ro9 : externes et cibles hors zone -> talon, natives (critere
natmiss + native_at de mame_test, recopie ici car mame_test n'a pas de profil pour ro1/2/4/6/7/8).
Base RAM : celle mesuree (RAMFIX=0 pour garder ram_hi_of). Usage : nice -n 19 python3 essai_mod.py roN"""
import os, sys, time, struct, collections
os.environ["MEMMODE"] = "cps2"
mod = sys.argv[1]
sys.path.insert(0, "<workspace>/scripts/untranspile")
import zones as Zm
Z = Zm.zones(mod)
import mips
if Z['m68k'][0][0] < mips.CODE0 and os.environ.get('CODE0BAS', '1') == '1': mips.CODE0 = 0x40
import translate as T
import assemble as A
from assemble import assemble
from mips import decode
buf = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, "rb").read()
BASES = {'ro1': 0x60, 'ro2': 0x80, 'ro4': 0x80, 'ro6': 0x80, 'ro7': 0x66, 'ro8': 0x80, 'ro3': 0x90, 'ro5': 0xa0, 'ro9': 0xb8}
if os.environ.get('RAMFIX', '1') == '1': T._RAM_CACHE[bytes(buf[:32])] = BASES[mod]
T.set_module_bounds(buf); T.DATA_BASE = 0x200000
end = struct.unpack_from('<I', buf, 12)[0]

def native_at(t):
    L = []
    for x in decode(buf, t, t + 0x4000):
        L.append(x)
        if x.m == 'jr' and x.rs == 31: break
    a = sum(1 for x in L if x.m == 'lui' and x.imm == 0x7000); n = len(L)
    s = sum(1 for x in L if x.m in ('sq', 'lq', 'mult', 'multu', 'div', 'divu', 'mfhi', 'mflo')
            or (x.m == 'addiu' and x.rs == 29 and x.rt == 29 and -0x400 < x.simm < -16 and x.simm % 16 == 0))
    lu = {}; relais = False
    for x in L:
        if x.m == 'lui': lu[x.rt] = x.imm
        elif x.m == 'addiu' and x.rs in lu: lu[x.rt] = (lu[x.rs] << 16) + x.simm
        elif (x.m == 'jalr' and x.rs in lu and 0x1F0000 + 0x40 <= lu[x.rs] < 0x1F0000 + end) or \
             (x.m == 'jal' and 0x1F0000 + 0x40 <= x.tgt < 0x1F0000 + end): relais = True
    if a == 0 and n <= 24 and relais: return False
    if a == 0 and n <= 8: return False
    return a == 0 or (s > 0 and a * 20 < n)

tg = sorted({x.tgt - 0x1F0000 for a0, a1 in Z['m68k'] for x in decode(buf, a0, a1) if x.m == 'jal'})
NAT = [t for t in tg if any(a0 <= t < a1 for a0, a1 in Z['m68k']) and native_at(t)]
t0 = time.time(); tot = collections.Counter()
for a0, a1 in Z['m68k']:
    if a1 - a0 < 0x1000: continue
    e1 = T.code_end_translate(buf) if a1 == end else a1
    its, words, unres = assemble(buf, a0, e1, base=0x1000, external=lambda t: 0x800, native=NAT)
    far = sum(len(v) for v in A.FAR_ENT.values())
    print("%s zone %x-%x : %d elements, code 68K %d o (%.2f Mo), non resolus %d, tremplins %d" % (
        mod, a0, e1, len(its), 2 * len(words), 2 * len(words) / 2**20, unres, far), flush=True)
    tot['el'] += len(its); tot['o'] += 2 * len(words); tot['nr'] += unres; tot['far'] += far
print("%s TOTAL : %d elements, %.2f Mo de 68K, non resolus %d, tremplins %d, natives %d, octets ADDA %d, longs post-incr. %d, longs sans SR %d, %.0f s" % (
    mod, tot['el'], tot['o'] / 2**20, tot['nr'], tot['far'], len(NAT), T.BYTE_ADDA[0], T.LONG_POSTINC[0], T.LONG_SR[0], time.time() - t0))
print("natives :", ' '.join('%x' % t for t in NAT))
