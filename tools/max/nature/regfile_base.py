"""Même idée, mais via un registre de base (gp, s0-s7, fp, k0/k1) : un banc de registres
émulé = un registre de base dont les accès se concentrent sur <= 16 petits déplacements."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import struct, collections
LS = {0x20,0x24,0x21,0x25,0x23,0x28,0x29,0x2B}
NAMES = {28:"gp",16:"s0",17:"s1",18:"s2",19:"s3",20:"s4",21:"s5",22:"s6",23:"s7",30:"fp",26:"k0",27:"k1"}
def profile(path, lo, hi):
    b = open(path, "rb").read()[lo:hi]
    W = struct.unpack(f"<{len(b)//4}I", b[:len(b)//4*4])
    per = collections.defaultdict(collections.Counter)
    for w in W:
        if (w >> 26) in LS:
            rs = (w >> 21) & 31
            if rs in NAMES:
                imm = w & 0xFFFF; imm -= 0x10000 if imm & 0x8000 else 0
                per[rs][imm] += 1
    return per, len(W)
for path, label, lo, hi in [(paths.eboot(),"PSP SFA3 MAX",0x74,0x74+0x2d4f30),
                            (paths.ee_hyper(),"Anthology (Hyper SFA)",0x100000,0x800000)]:
    per, nw = profile(path, lo, hi)
    print(f"--- {label}  ({nw} mots)")
    for rs, c in sorted(per.items(), key=lambda kv: -sum(kv[1].values()))[:5]:
        tot = sum(c.values()); top16 = sum(v for _, v in c.most_common(16))
        print(f"   base ${NAMES[rs]:<3} accès={tot:7}  déplacements distincts={len(c):5}  part des 16 plus fréquents={100*top16/tot:5.1f} %")
