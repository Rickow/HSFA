#!/usr/bin/env python3
"""Inventaire des TABLES INDEXEES PAR L'IDENTIFIANT DE PERSO ($102(An) en numerotation PS2 = $103 en 68K) :
dans chaque routine traduite (mode hote), une lecture MOVE.B $0102(An),Dk suivie (<= 10 instructions) d'un acces
table indexe par Dk (LEA $X.L ... 0(A0,Dk.W) ou T_X(PC,Dk.W)). ro3/ro5 : ID 0..$25 ; ro9 : ID etendu 0..$7F."""
import os, re, pickle, collections, struct, json
os.environ.setdefault("GRAIN", "routine")
import commun as C

def inv(mod):
    tr = pickle.load(open(os.path.join(C.OUT, "tr68k_%s_routine.pkl" % mod), "rb"))
    T = collections.defaultdict(list)
    for a, seq in tr.items():
        seq = seq or []
        for i, (va, w, mn) in enumerate(seq):
            m = re.match(r"MOVE\.B \$(0102|0116)\(A\d\),D(\d)", mn)
            if not m: continue
            champ = m.group(1)
            k = m.group(2); lea = None
            for va2, w2, mn2 in seq[i+1:i+12]:
                l = re.match(r"LEA \$([0-9a-f]+)\.L,A\d", mn2)
                if l: lea = int(l.group(1), 16)
                t = re.search(r"T_([0-9a-f]+)\(PC,D%s\.W\)" % k, mn2)
                if t: T[(champ, int(t.group(1), 16))].append(va2); continue
                if lea and re.search(r"\(A\d,D%s\.W\)" % k, mn2): T[(champ, lea)].append(va2); lea = None; continue
                if re.match(r"MOVE\.B .*,D%s$" % k, mn2) or mn2.startswith(("RTS", "JMP", "BRA")): break
    return T

if __name__ == "__main__":
    out = {}
    for mod in ('ro3', 'ro5', 'ro9'):
        T = inv(mod); out[mod] = {"%s %x" % k: ["%x" % s for s in v] for k, v in T.items()}
        de = C.BASE + C.header(mod)['code_end']
        for ch in ('0102', '0116'):
            Tc = {k: v for k, v in T.items() if k[0] == ch}
            print("%s : %d tables indexees par $%s (%d sites)" % (mod, len(Tc), ch, sum(len(v) for v in Tc.values())))
            if mod == 'ro9':
                print("   " + ' '.join("%s(%d)" % (C.h(k[1]), len(Tc[k])) for k in sorted(Tc)))
    json.dump(out, open(os.path.join(C.OUT, "tables_id.json"), "w"), indent=0)
