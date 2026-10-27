"""(agent_integration_max) tables lues avec un index dérivé de l'ID d'un perso (carte de l'image) : remontée simple du
registre d'index (lignes précédentes) jusqu'à son chargement ; source « ID » = $102/$103 d'une structure, $503/$903/
$D03/$1103(A5) (joueurs), $132/$146(A5) (gagnant / ID)."""
import re, sys, json
sys.path.insert(0, '<workspace>/work/agent_integration_max/untranspile')
import agrandit_max as AG
L = open(sys.argv[1]).read().splitlines()
SRC = re.compile(r'MOVE\.B \$(0103|0102|0503|0502|0903|0902|0d03|0d02|1103|1102|0132|0146)\((A\d)\),(D\d)')
ARITH = re.compile(r'^(ADD\.W|ADD\.B|LSL\.W|LSL\.B|ASL\.W|EXT\.W|ANDI\.W|ANDI\.B|ADDI\.W|ADDI\.B|ADDQ\.W|ADDQ\.B|MULU|SUBQ\.W|SUBI\.W)')
known = {s['ps2'] for s in AG.specs()} | set(AG.IGNOREES) | set(AG.PAIRES) | set(AG.DEJA_48)
def source(n, r):
    for c in reversed(L[max(0, n - 14):n]):
        mn = ' '.join(c.split()[2:])
        m = SRC.search(mn)
        if m and m.group(3) == r: return m.group(1)
        dst = re.search(r',(D\d)$', mn.split('[')[0].strip())
        if dst and dst.group(1) == r:
            if ARITH.match(mn): continue
            if mn.startswith('MOVEQ #$0') or mn.startswith('MOVEQ #0'): continue
            return None
        if re.match(r'(RTS|JMP|BRA|JSR)', mn): return None
    return None
res = {}
for n, l in enumerate(L):
    mn = ' '.join(l.split()[2:])
    m = re.search(r'T_([0-9a-f]{6})\(PC,(D\d)\.W\)', mn)
    if m:
        s = source(n, m.group(2))
        if s: res.setdefault(int(m.group(1), 16), set()).add((l.split()[1], s))
        continue
    m = re.search(r'LEA \$[0-9a-f]+\.L,(A\d)\s+\[PS2 00([0-9a-f]{6})\]', mn)
    if m:
        a, t = m.group(1), m.group(2)
        for k in range(n + 1, min(n + 7, len(L))):
            mm = re.search(r'\(%s,(D\d)\.W\)' % a, L[k])
            if mm:
                s = source(k, mm.group(1))
                if s: res.setdefault(int(t, 16), set()).add((l.split()[1], s))
                break
for t, v in sorted(res.items()):
    print('%x %s %s' % (t, 'connue' if t in known else 'NOUVELLE', sorted(v)[:4]))
