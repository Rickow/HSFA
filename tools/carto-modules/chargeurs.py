#!/usr/bin/env python3
"""Appels aux chargeurs X_DATA de l'executable (0x155080 fichier, 0x154D20 banque son, 0x154C90...) dans chaque
module : arguments immediats (addiu aN,zero,imm) et tables (lui/addiu vers les donnees, puis lhu/lh/lw) dans les 40
instructions qui precedent. Les tables sont videes (u16) pour retrouver les numeros d'entrees."""
import sys, struct, collections
sys.path.insert(0, '.')
import commun as C
CIBLES = {0x156ec0: 'ec0', 0x155c60: 'c60', 0x155080: 'charge', 0x154d20: 'banque_son', 0x154c90: 'c90', 0x155020: '020', 0x154db0: 'db0', 0x154960: '960', 0x154990: '990'}
REG = {4: 'a0', 5: 'a1', 6: 'a2', 7: 'a3'}
for m in sys.argv[1:] or ['ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
    L = C.instrs(m); d = C.load(m); e = C.header(m)['code_end']
    cnt = collections.Counter(); out = []
    for i, x in enumerate(L):
        if x.m != 'jal' or x.tgt not in CIBLES: continue
        cnt[CIBLES[x.tgt]] += 1
        imm = []; tabs = []; lu = {}
        for y in L[max(0, i-40):i+2]:
            if y.m == 'lui': lu[y.rt] = y.imm << 16
            elif y.m == 'addiu' and y.rs in lu:
                v = (lu[y.rs] + y.simm) & 0xffffffff
                if e <= v - 0x1F0000 < len(d): tabs.append(v)
            if y.m in ('addiu', 'ori') and y.rs == 0 and y.rt in REG and 200 <= y.imm <= 560: imm.append('%s=%d' % (REG[y.rt], y.imm))
        desc = []
        for t in tabs:
            o = t - 0x1F0000
            vs = struct.unpack_from('<24H', d, o)
            if sum(1 for v in vs if 200 <= v <= 560) >= 3: desc.append('table %#x : %s' % (t, ' '.join(str(v) for v in vs)))
        if imm or desc: out.append('  %s @%x : %s %s' % (CIBLES[x.tgt], x.va, ' '.join(imm), ' | '.join(desc)))
    print('=== %s : appels %s' % (m, dict(cnt)))
    print('\n'.join(out))
