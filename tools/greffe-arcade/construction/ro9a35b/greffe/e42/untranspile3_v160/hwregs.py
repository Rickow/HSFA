#!/usr/bin/env python3
"""REGISTRES MATERIELS CPS2 <-> VARIABLES DU PORTAGE, sur tout le programme (HANDOFF §57) :
chaque fonction recompilee qui accede a une variable du portage ($96xxxx) est traduite (mode hote),
localisee dans la ROM, puis ses mots sont alignes avec ceux de la ROM : la ou nous avons l'adresse
absolue 0096:xxxx, la ROM a l'adresse du registre (0040:00xx, 0080:4xxx, 0061:8xxx...). Vote."""
import sys, os, struct, bisect, collections, difflib, json
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from mips import decode, CODE0
import translate as T, e2e, verify
from assemble import assemble

def main():
    buf = open(verify.RO3, 'rb').read(); k68 = open(verify.K68, 'rb').read()[:0x100000]
    kw = struct.unpack('>%dH' % (len(k68)//2), k68)
    end = struct.unpack_from('<I', buf, 12)[0]
    L = list(decode(buf, CODE0, end))
    starts = sorted({x.tgt - T.RUNTIME_BASE for x in L if x.m == 'jal'} | {CODE0})
    fs = set(); lu = {}
    for x in L:
        if x.m == 'lui': lu[x.rt] = x.imm; continue
        if x.m in ('lb','lbu','lh','lhu','lw','sb','sh','sw') and lu.get(x.rs) in (0x96,):
            fs.add(starts[bisect.bisect_right(starts, x.va) - 1])
    votes = collections.defaultdict(collections.Counter); ok = 0
    for a in sorted(fs):
        k = bisect.bisect_right(starts, a); b = starts[k] if k < len(starts) else end
        k0 = T.mips_to_68k(a)
        if k0 is None or b - a > 0x4000: continue
        try:
            its, words, _ = assemble(buf, a, b, base=0, external=T.mips_to_68k)
            sc, j = e2e.locate_mapped(kw, words, k0, span=512)
            if j is None or sc < 3: continue
        except Exception: continue
        ref = kw[j:j + len(words) + 32]
        sm = difflib.SequenceMatcher(None, words, ref, autojunk=False)
        if sm.ratio() < 0.4: continue
        ok += 1
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'replace': continue
            for p in range(i1, i2 - 1):
                if words[p] == 0x0096:
                    q = j1 + (p - i1)
                    if q + 1 < j2 + 1 and q + 1 < len(ref) and ref[q] in (0x0040, 0x0080, 0x0061, 0x0062, 0x0066, 0x0070):
                        votes[0x960000 | words[p+1]][(ref[q] << 16) | ref[q+1]] += 1
    res = {}
    for host, c in sorted(votes.items()):
        t, n = c.most_common(1)[0]
        res["%06x" % host] = {"cps2": "%06x" % t, "votes": n, "total": sum(c.values())}
    print("fonctions alignees : %d ; variables reliees : %d" % (ok, len(res)))
    for h, v in res.items(): print("   portage $%s -> CPS2 $%s  (%d/%d)" % (h, v["cps2"], v["votes"], v["total"]))
    json.dump(res, open(os.path.join(D, "hwregs_ro3.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
