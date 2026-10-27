"""Appels moteur d'un perso et leurs arguments constants, des deux côtés.
Arcade 68K : `MOVEQ #n,D0` / `MOVE.W #n,D0` (ou D1) dans les 3 instructions avant JSR/JMP/BSR externe.
PSP MIPS : `ori/addiu aK,zero,n` (K = 0..3) dans les 6 instructions avant JAL (et le délai) ; a0 = souvent l'objet."""
import sys, re, collections
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
from arc68k import explore
def arcade_calls(entries, lo, hi):
    seen, tables, ext = explore(entries, lo, hi)
    addrs = sorted(seen); out = collections.defaultdict(list)
    for k, a in enumerate(addrs):
        i = seen[a]
        if i.mnemonic in ("jsr", "jmp", "bsr", "bsr.w", "bsr.b"):
            mm = re.search(r"\$([0-9a-f]+)(\.l)?$", i.op_str)
            if not mm or "(" in i.op_str: continue
            x = int(mm.group(1), 16)
            if lo <= x < hi: continue
            args = {}
            for j in range(max(0, k - 4), k):
                p = seen[addrs[j]]
                mc = re.match(r"#\$?(-?[0-9a-f]+), d([0-3])$", p.op_str) if p.mnemonic in ("moveq", "move.w", "move.b", "move.l") else None
                if mc:
                    v = int(mc.group(1), 16) if "$" in p.op_str else int(mc.group(1))
                    args["d" + mc.group(2)] = v & 0xFFFF
            out[x].append((a, args))
    return out, seen, tables
def psp_calls(a0, e0):
    from relocs import img
    from mips import decode
    ins = list(decode(img, a0, e0)); out = collections.defaultdict(list)
    for k, i in enumerate(ins):
        if i.m != "jal": continue
        t = i.tgt
        if a0 <= t < e0: continue
        args = {}
        for p in ins[max(0, k - 6): k + 2]:
            if p.m in ("ori", "addiu") and p.rs == 0 and 4 <= p.rt <= 7:
                args["a%d" % (p.rt - 4)] = p.imm
        out[t].append((i.va, args))
    return out, ins
