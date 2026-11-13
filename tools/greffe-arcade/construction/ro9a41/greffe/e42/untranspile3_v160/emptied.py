#!/usr/bin/env python3
"""ROUTINES VIDEES PAR LE PORTAGE -> routine d'origine dans la ROM (vote des sites d'appel).

Une routine videe (corps = 'jr ra') est appelee depuis des fonctions recompilees. On traduit et
assemble chaque fonction appelante A SA PLACE dans la ROM (localisation guidee par la carte, comme
e2e.py), on aligne ses mots avec ceux de la ROM (SequenceMatcher), puis on lit l'instruction d'appel
d'ORIGINE alignee sur l'appel : JSR abs.L / BSR.W / BSR.S / JSR d16(PC) (ou JMP/BRA pour un appel
terminal). Chaque site vote pour une adresse ; la majorite donne la routine d'origine.
Sortie : emptied_ro3.json {va_mips: {"rom": adresse, "votes": n, "total": n}}.
"""
import sys, os, struct, bisect, json, collections, difflib
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from mips import decode, CODE0
import translate as T, verify, e2e
from assemble import assemble

def emptied_routines(buf, starts):
    """debuts de fonction dont le corps se reduit a 'jr ra' (eventuellement cadre de pile seul)"""
    out = set()
    for s in starts:
        ins = [x for x in decode(buf, s, s + 0x20) if not (x.m == 'sll' and x.w == 0)]
        body = [x for x in ins[:6] if not (x.rs == 29 and x.m in ('addiu', 'sd', 'ld', 'sw', 'lw'))]
        if body and body[0].m == 'jr' and body[0].rs == 31: out.add(s)
    return out

def rom_call_target(kw, p):
    """cible de l'instruction d'appel/saut 68K au mot p de la ROM, ou None"""
    if p < 0 or p + 2 >= len(kw): return None
    w = kw[p]
    if w in (0x4eb9, 0x4ef9): return (kw[p+1] << 16) | kw[p+2]
    if w in (0x4eba, 0x4efa): d = kw[p+1]; return (p*2 + 2 + (d - 0x10000 if d & 0x8000 else d)) & 0xffffff
    if w in (0x6100, 0x6000): d = kw[p+1]; return (p*2 + 2 + (d - 0x10000 if d & 0x8000 else d)) & 0xffffff
    if (w & 0xff00) in (0x6100, 0x6000) and (w & 0xff) not in (0, 0xff):
        d = w & 0xff; return (p*2 + 2 + (d - 0x100 if d & 0x80 else d)) & 0xffffff
    if (w & 0xf000) == 0x6000:                             # Bcc vers un bloc partage (souvent un RTS)
        if (w & 0xff) == 0: d = kw[p+1]; return (p*2 + 2 + (d - 0x10000 if d & 0x8000 else d)) & 0xffffff
        if (w & 0xff) != 0xff: d = w & 0xff; return (p*2 + 2 + (d - 0x100 if d & 0x80 else d)) & 0xffffff
    return None

def near_target(kw, q):
    """instruction d'appel/branchement a q, q-1 ou q+1 (l'alignement peut tomber sur l'extension)"""
    for d in (0, -1, 1, -2):
        t = rom_call_target(kw, q + d)
        if t is not None: return t
    return None

def map_pos(blocks, p):
    """position p (mots emis) -> position ROM, par le bloc correspondant precedent"""
    prev = None
    for b in blocks:
        if b.size == 0: continue
        if b.a <= p < b.a + b.size: return b.b + (p - b.a)
        if b.a + b.size <= p: prev = b
    if prev is None: return None
    return prev.b + prev.size + (p - (prev.a + prev.size))

def main():
    buf = open(verify.RO3, "rb").read(); k68 = open(verify.K68, "rb").read()[:0x100000]
    kw = struct.unpack('>%dH' % (len(k68)//2), k68)
    end = struct.unpack_from('<I', buf, 12)[0]
    L = list(decode(buf, CODE0, end))
    starts = sorted({x.tgt - T.RUNTIME_BASE for x in L if x.m == 'jal'} | {CODE0})
    starts = [s for s in starts if CODE0 <= s < end]
    E = emptied_routines(buf, starts)
    callers = collections.defaultdict(set)                  # fonction appelante -> routines videes appelees
    for x in L:
        if x.m == 'jal' and (x.tgt - T.RUNTIME_BASE) in E:
            k = bisect.bisect_right(starts, x.va) - 1
            callers[starts[k]].add(x.tgt - T.RUNTIME_BASE)
    print("routines videes : %d ; fonctions appelantes : %d" % (len(E), len(callers)))
    votes = collections.defaultdict(collections.Counter); tried = ok = 0
    for a in sorted(callers):
        k = bisect.bisect_right(starts, a); b = starts[k] if k < len(starts) else end
        if b - a > 0x4000: continue
        k0 = T.mips_to_68k(a)
        if k0 is None: continue
        try:
            its, words, _ = assemble(buf, a, b, base=0, external=T.mips_to_68k)
            if len(words) < 6: continue
            sc, j = e2e.locate_mapped(kw, words, k0, span=256)
            if j is None or sc < 4: continue
            its, words, _ = assemble(buf, a, b, base=j*2, external=e2e.snapped_external(kw))
        except Exception:
            continue
        tried += 1
        ref = kw[j:j + len(words) + 64]
        sm = difflib.SequenceMatcher(None, words, ref, autojunk=False)
        if sm.ratio() < 0.5: continue
        ok += 1
        blocks = sm.get_matching_blocks()
        for it in its:
            if it.kind in ('call', 'jump') and it.tgt in E:
                p = map_pos(blocks, (it.off - j*2) // 2)
                t = near_target(kw, j + p) if p is not None else None
                if t is not None: votes[it.tgt][t] += 1
    res = {}
    for e, c in votes.items():
        t, n = c.most_common(1)[0]
        rts = kw[t//2] == 0x4e75 if t//2 < len(kw) else False
        res["%x" % e] = {"rom": "%06x" % t, "votes": n, "total": sum(c.values()), "rts_seul": rts,
                         "debut": " ".join("%04x" % x for x in kw[t//2:t//2+6])}
    print("fonctions appelantes traduites et localisees : %d / %d ; routines videes identifiees : %d / %d"
          % (ok, tried, len(res), len(E)))
    sure = {k: v for k, v in res.items() if v["votes"] >= 2 and v["votes"] * 3 >= v["total"] * 2}
    print("dont SURES (>= 2 votes et >= 2/3 d'accord) : %d" % len(sure))
    print("  cible = simple RTS (bloc de retour partage, PAS une routine videe) : %d"
          % sum(1 for v in res.values() if v["rts_seul"]))
    for k, v in sorted(res.items(), key=lambda t: -t[1]["votes"])[:25]:
        print("   mips %s -> ROM %s  %d/%d votes  %s  [%s]" % (k, v["rom"], v["votes"], v["total"],
              "RTS seul" if v["rts_seul"] else "", v["debut"]))
    json.dump(res, open(os.path.join(D, "emptied_%s.json" % os.environ.get("MODULE", "ro3")), "w"), indent=1)
    return res, E

if __name__ == "__main__":
    main()
