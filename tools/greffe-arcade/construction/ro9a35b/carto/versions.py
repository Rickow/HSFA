#!/usr/bin/env python3
"""Mecanisme des VERSIONS d'Hyper, compte sur la traduction 68K (mode hote = deplacements PS2) de chaque routine :
tests de bits de $D3(An), comparaisons de l'identifiant etendu $102(An), lectures de $116/$117, et LEA vers la
zone de donnees nouvelle d'Hyper. Repartition selon la classe de la routine (identique a Upper / modifiee / nouvelle)."""
import os, re, pickle, collections
os.environ.setdefault("GRAIN", "routine")
import commun as C
F = pickle.load(open(os.path.join(C.OUT, "comparaison_ro9_routine.pkl"), "rb"))

def scan(mod):
    tr = pickle.load(open(os.path.join(C.OUT, "tr68k_%s_routine.pkl" % mod), "rb"))
    bits = collections.Counter(); cmp102 = collections.Counter(); f116 = collections.Counter()
    sites = collections.defaultdict(list); lea = collections.Counter(); per_class = collections.Counter()
    for a, seq in tr.items():
        if not seq: continue
        for va, w, mn in seq:
            m = re.match(r"BTST #\$?([0-9a-f]+),\$00d3\(A(\d)\)", mn)
            if m:
                bits[int(m.group(1), 16)] += 1; sites['btst_d3'].append(va)
                if mod == 'ro9': per_class[F[a]['meilleur']] += 1
            m = re.match(r"CMPI\.B #\$?([0-9a-f]+),\$0102\(A(\d)\)", mn)
            if m: cmp102[int(m.group(1), 16)] += 1; sites['cmp102'].append(va)
            if re.search(r"\$011[67]\(A\d\)", mn): f116[mn.split()[0]] += 1
            m = re.match(r"LEA \$([0-9a-f]+)\.L", mn)
            if m:
                v = int(m.group(1), 16)
                if 0x8AF140 <= v < 0xB0F140: lea['zone_nouvelle'] += 1
    return bits, cmp102, f116, sites, lea, per_class

if __name__ == "__main__":
    for mod in ('ro3', 'ro5', 'ro9'):
        bits, cmp102, f116, sites, lea, pc = scan(mod)
        print("%s : BTST #n,$D3(An) = %d  par bit %s" % (mod, sum(bits.values()), dict(sorted(bits.items()))))
        print("     CMPI.B #x,$102(An) = %d (valeurs les plus testees : %s)" % (sum(cmp102.values()),
              ', '.join('$%02x×%d' % kv for kv in cmp102.most_common(12))))
        print("     acces $116/$117 : %s ; LEA vers la zone nouvelle 0x8AF140-0xB0F140 : %d" % (dict(f116), lea['zone_nouvelle']))
        if mod == 'ro9':
            print("     BTST $D3 par classe de routine : %s" % dict(pc))
