#!/usr/bin/env python3
"""(copie adaptee pour carto_modules : starts/funcs par zones 68K) Outils communs de la cartographie ro9 (lecture seule des modules et de l'outillage existant).
Conventions : 'fichier' = decalage dans <mod>_usa_prog68k.bin ; 'execution' = fichier + 0x1F0000."""
import sys, os, struct, bisect, collections, functools
UT = "<workspace>/scripts/untranspile"
sys.path.insert(0, UT)
from mips import decode
DIR = "<workspace>/anthology_extract/decompressed"
BASE = 0x1F0000
OUT = os.path.dirname(os.path.abspath(__file__))
SUF = "" if os.environ.get("GRAIN", "jal") == "jal" else "_" + os.environ["GRAIN"]

@functools.lru_cache(None)
def load(mod):
    return open(os.path.join(DIR, "%s_usa_prog68k.bin" % mod), "rb").read()

def header(mod):
    b = load(mod)
    h = struct.unpack_from('<7I', b, 0)
    return dict(magic=b[:4].decode(), version=h[1], base=h[2], code_end=h[3], data_size=h[4], champ20=h[5], fin_exec=h[6],
                taille=len(b))

@functools.lru_cache(None)
def instrs(mod):
    b = load(mod); e = header(mod)['code_end']
    return list(decode(b, 0x20, e))

@functools.lru_cache(None)
def start68k(mod):
    """debut de la zone apres le Z80 recompile : premier prologue apres le DERNIER acces au banc Z80
    (0x7000_10xx). ro3/ro5 : 0x22B00 = premier code 68K ; ro9 : 0x22B00 = une fonction NATIVE (C du portage,
    appelle le chargeur 0x155080), puis les aides du recompilateur a 0x22DC0 (l'outillage existant part de 0x22DE0)."""
    L = instrs(mod); lz = None
    for i in range(1, len(L)):
        p, x = L[i-1], L[i]
        if p.m == 'lui' and p.imm == 0x7000 and x.rs == p.rt and 0x1000 <= x.imm < 0x1040: lz = x.va
    for x in L:
        if x.va > lz and x.m == 'addiu' and x.rs == 29 and x.rt == 29 and x.simm < 0: return x.va
    return None

@functools.lru_cache(None)
def vas(mod):
    return [x.va for x in instrs(mod)]

def seg(mod, a, b):
    V = vas(mod); L = instrs(mod)
    return L[bisect.bisect_left(V, a):bisect.bisect_left(V, b)]

GRAIN = os.environ.get("GRAIN", "jal")      # 'jal' : cibles de jal (decoupage de modcompare/transplant)
                                            # 'routine' : + cibles de jalr a constante + prologues (addiu sp,-N)
@functools.lru_cache(None)
def starts(mod):
    """(carto_modules) debuts de routine DANS LES ZONES 68K de zones.py (le Z80 n'est pas toujours en tete)"""
    import zones as Zm
    Z = Zm.zones(mod)['m68k']; L = instrs(mod)
    def dedans(a): return any(z0 <= a < z1 for z0, z1 in Z)
    S = {x.tgt - BASE for x in L if x.m == 'jal' and dedans(x.tgt - BASE)} | {z0 for z0, z1 in Z}
    if GRAIN == 'routine':
        lu = {}
        for x in L:
            if not dedans(x.va): continue
            if x.m == 'lui': lu[x.rt] = x.imm << 16
            elif x.m == 'addiu' and x.rs in lu: lu[x.rt] = (lu[x.rs] + x.simm) & 0xffffffff
            elif x.m == 'jalr' and x.rs in lu and dedans(lu[x.rs] - BASE): S.add(lu[x.rs] - BASE)
            if x.m == 'addiu' and x.rs == 29 and x.rt == 29 and x.simm < 0: S.add(x.va)
    return sorted(S)

@functools.lru_cache(None)
def funcs(mod):
    import zones as Zm
    Z = Zm.zones(mod)['m68k']; st = starts(mod); out = []
    for k, a in enumerate(st):
        b = st[k+1] if k+1 < len(st) else Z[-1][1]
        for z0, z1 in Z:
            if z0 <= a < z1: b = min(b, z1)
        out.append((a, b))
    return out

def fidx(mod, va):
    return bisect.bisect_right(starts(mod), va) - 1

def func_of(mod, va):
    k = fidx(mod, va); return funcs(mod)[k] if k >= 0 else None

def ram_base(mod):
    e = header(mod)['fin_exec']; return (e + 0x7ffff) & ~0x7ffff

def is_native(seg_):
    """critere natmiss / mame_test.native_at (fonction C du portage, sans banc de registres 68K)"""
    a = sum(1 for x in seg_ if x.m == 'lui' and x.imm == 0x7000); n = len(seg_)
    s = sum(1 for x in seg_ if x.m in ('sq', 'lq', 'mult', 'multu', 'div', 'divu', 'mfhi', 'mflo')
            or (x.m == 'addiu' and x.rs == 29 and x.rt == 29 and -0x400 < x.simm < -16 and x.simm % 16 == 0))
    return a == 0 or (s > 0 and a * 20 < n), a, n, s

def consts32(seg_):
    """constantes 32 bits construites par lui (+ addiu/ori) -> [(va, valeur)]"""
    lu = {}; out = []
    for x in seg_:
        if x.m == 'lui':
            lu[x.rt] = (x.imm << 16, x.va); out.append((x.va, x.imm << 16, 'lui'))
        elif x.m in ('addiu', 'ori') and x.rs in lu:
            v = (lu[x.rs][0] + (x.simm if x.m == 'addiu' else x.imm)) & 0xffffffff
            out.append((x.va, v, x.m)); lu.pop(x.rs, None)
            if x.rt != x.rs: pass
        elif x.m in ('lb','lbu','lh','lhu','lw','sb','sh','sw','ld','sd','lq','sq') and x.rs in lu:
            v = (lu[x.rs][0] + x.simm) & 0xffffffff; out.append((x.va, v, x.m))
        else:
            d = x.rt if x.op not in (0,) else x.rd
            if x.op != 0 and x.m not in ('sb','sh','sw','sd','sq','beq','bne','bltz','bgez','blez','bgtz','j','jal'):
                lu.pop(d, None)
            elif x.op == 0:
                lu.pop(x.rd, None)
    return out

def h(v): return "0x%X" % v
def fe(v): return "%s / %s" % (h(v), h(v + BASE))   # fichier / execution
