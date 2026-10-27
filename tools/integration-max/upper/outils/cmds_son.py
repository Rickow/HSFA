"""(agent_integration_max) commandes son (journal lua/sons.lua) : code = octet bas de $618000 << 8 | octet bas de $618002"""
import sys, collections
ev = []; cur = {}
for l in open(sys.argv[1]):
    f, a, d, m, pc = l.split(); f = int(f); a = int(a, 16); d = int(d, 16)
    if a == 0x618000: cur = {"f": f, "hi": d & 0xFF}
    elif a == 0x618002 and "hi" in cur: ev.append((f, (cur["hi"] << 8) | (d & 0xFF), pc)); cur = {}
i0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
c = collections.Counter(code for f, code, pc in ev if f >= i0)
print(" ".join("%04x:%d" % kv for kv in sorted(c.items())))
