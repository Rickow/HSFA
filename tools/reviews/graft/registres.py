#!/usr/bin/env python3
"""registres.py -- graft review (axis 4, transitions): list, in the translated 68K image of the graft
(b9/carte_image.txt), the WRITES and READS of the hardware registers ($8040xx CPS2 / I-O, $8041xx CPS-A / CPS-B,
$8042xx registers of the fork: plane bases) and of the graft's variables or RAM copies of registers (A5 offsets: $A8
request to reset the page bases, $32/$34/$3A layers, $2A/$2C, $C130-$C157 page bases, $FE00-$FE3F HSFA bytes,
$FF00-$FF03, $12A), split by SIDE: Hyper (code of ro9), copy of Upper (blocks of greffe.json, with the original address
in ro5), synthetic stub (greffe.json synth, by name). Check: also counts, in the module's MIPS, the direct accesses
lui $BE / $C0 (registers) per side, to spot what the map does not render.
Useful before touching a transition (A2a / E2b of ro9a38 were found this way).

Usage:  nice -n 19 python3 -I registres.py [frozen_build] > sorties/registres.txt
        nice -n 19 python3 -I registres.py [frozen_build] --detail REG   (every line of one register, e.g. 804166, A5:fe00)
Input:  frozen graft build (argument or $HSFA_GRAFT_BUILD: greffe.json, b9/carte_image.txt, ro9a_module.bin).
Output: stdout (register x side x sites). Read only. See paths.py.
"""
import sys, os, re, json, bisect, struct, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
args = [a for a in sys.argv[1:] if not a.startswith('--')]
C = paths.construction(args[0] if args and os.path.isdir(args[0]) else None)
DETAIL = sys.argv[sys.argv.index('--detail') + 1].lower() if '--detail' in sys.argv else None
BASE = 0x1F0000
J = json.load(open(os.path.join(C, "greffe.json"), encoding="utf-8"))
BL = sorted((int(c, 16), int(c, 16) + int(b, 16) - int(a, 16), int(a, 16)) for a, b, c in J['blocs'])
BLA = [x[0] for x in BL]
SY = sorted((int(v, 16) - BASE, k) for k, v in J['synth'].items()); SYA = [x[0] for x in SY]
Z2 = (int(J['zone2'][0], 16), int(J['zone2'][1], 16))
def cote(off):
    """-> ('H'|'U'|'T', detail)"""
    if SYA and SYA[0] <= off < Z2[1]:
        k = bisect.bisect_right(SYA, off) - 1
        return 'T', SY[k][1]
    k = bisect.bisect_right(BLA, off) - 1
    if k >= 0 and BL[k][0] <= off < BL[k][1]: return 'U', 'u%x' % (BL[k][2] + off - BL[k][0])
    return 'H', ''
A5_INT = [(0xA8, 0xA8), (0x2A, 0x2D), (0x32, 0x35), (0x3A, 0x3B), (0x12A, 0x12A), (0xC130, 0xC157), (0xFE00, 0xFE3F), (0xFF00, 0xFF03)]
def a5_ok(d): return any(lo <= d <= hi for lo, hi in A5_INT)
LECT = ('TST', 'CMP', 'BTST', 'PEA', 'LEA', 'JSR', 'JMP')
RMW = ('ANDI', 'ORI', 'EORI', 'ADD', 'SUB', 'BSET', 'BCLR', 'BCHG', 'NOT', 'NEG', 'AND', 'OR', 'EOR', 'LS', 'AS', 'RO')
re_abs = re.compile(r'\$(80[4][0-9a-f]{3})\.L'); re_a5 = re.compile(r'\$([0-9a-f]{4})\(A5\)')
def operandes(s):
    out = []; d = 0; cur = ''
    for ch in s:
        if ch == '(': d += 1
        if ch == ')': d -= 1
        if ch == ',' and d == 0: out.append(cur); cur = ''
        else: cur += ch
    out.append(cur); return out
T = collections.defaultdict(lambda: collections.defaultdict(list))   # reg -> (cote, sens) -> [(a68, off, detail, txt)]
for l in open(os.path.join(C, "b9", "carte_image.txt"), encoding="utf-8", errors="replace"):
    p = l.rstrip('\n').split(' ', 2)
    if len(p) < 3: continue
    try: a68, off = int(p[0], 16), int(p[1], 16)
    except ValueError: continue
    txt = p[2].split('  [')[0]
    for ins in txt.split(' ; '):
        m = ins.strip().split(' ', 1)
        if len(m) < 2: continue
        mn = m[0].split('.')[0]; ops = operandes(m[1])
        for i, op in enumerate(ops):
            regs = ['%s' % x for x in re_abs.findall(op)] + ['a5:%s' % x for x in re_a5.findall(op) if a5_ok(int(x, 16))]
            if not regs: continue
            dern = i == len(ops) - 1
            if mn.startswith(LECT) or not dern: sens = 'L'
            elif mn.startswith(RMW) and len(ops) >= 1 and not mn.startswith('MOVE'): sens = 'M'
            else: sens = 'E'
            if mn in ('CLR', 'ST', 'SF') or (mn.startswith('S') and len(ops) == 1 and mn not in ('SUB', 'SUBQ', 'SUBI', 'SWAP')): sens = 'E'
            if mn.startswith(('ADDQ', 'SUBQ', 'ADDI', 'SUBI')) and dern: sens = 'M'
            c, det = cote(off)
            for r in regs: T[r][(c, sens)].append((a68, off, det, ins.strip()))
NOMS = {'804166': 'CPS-B couches (copie $32(A5))', '804170': 'CPS-B priorites/palette ctrl (copie $34(A5))', '804100': 'CPS-A objets', '804102': 'CPS-A scroll1',
        '804104': 'CPS-A scroll2', '804106': 'CPS-A scroll3', '804108': 'CPS-A rowscroll', '80410a': 'CPS-A palette', '804122': 'CPS-A videocontrol',
        '804200': 'FORK base scroll1', '804202': 'FORK base scroll2', '804204': 'FORK base scroll3', 'a5:fe00': 'drapeau ARCADE', 'a5:fe02': 'intermede vu',
        'a5:fe04': 'phase fin (copies)', 'a5:fe08': '$12A sauve', 'a5:fe10': 'decor d\'Upper', 'a5:fe11': 'VERSUS D4', 'a5:0032': 'copie RAM couches', 'a5:00a8': 'demande : bases de pages <- $90xxxx (Hyper 0x3F5E0)', 'a5:c130': 'base page scroll1 ($190 = $900000 ; $191 = $910000 Upper)', 'a5:c134': 'base page scroll2', 'a5:c138': 'base page scroll3', 'a5:c13c': 'base page lignes', 'a5:c140': 'base palette (demandee)', 'a5:c154': 'base palette (prise)',
        'a5:0034': 'copie RAM $804170', 'a5:003a': 'ordre couches 2', 'a5:012a': 'effet de fond (bit 7 Hyper)'}
SENS = {'E': 'ecrit', 'M': 'modifie', 'L': 'lit'}
if DETAIL:
    for k, L in sorted(T.get(DETAIL, {}).items()):
        for a68, off, det, ins in L: print("%s %s 68K %06x fichier %07x %s  %s" % (k[0], SENS[k[1]], a68, off, det, ins))
    sys.exit(0)
print("# registres.py sur %s ; cotes : H = Hyper, U = copie d'Upper (uXXXX = fichier ro5), T = talon de la greffe" % C)
print("# sites : adresse 68K de l'image (carte_image.txt) ; 6 premiers par case, total entre parentheses")
for r in sorted(T):
    print("\n## %s  %s" % (r, NOMS.get(r, '')))
    for c in 'HUT':
        for s in 'EML':
            L = T[r].get((c, s))
            if not L: continue
            if c == 'T':
                par = collections.Counter(d for _, _, d, _ in L)
                print("  T %-7s (%d) : %s" % (SENS[s], len(L), ', '.join('%s x%d' % kv for kv in sorted(par.items()))))
            else:
                print("  %s %-7s (%d) : %s" % (c, SENS[s], len(L), ' '.join(('%06x' % a + ('/' + d if d else '')) for a, _, d, _ in L[:6])))
# controle MIPS : acces directs aux registres (lui $BE + [$2000,$2200) = $8040E0.. ; lui $C0 - $100.. = $804200..)
b = open(os.path.join(C, "ro9a_module.bin"), "rb").read()
ce = Z2[1]; lui = {}; cm = collections.Counter()
for a in range(0x20, min(ce, len(b) - 4), 4):
    w = struct.unpack_from('<I', b, a)[0]; op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; imm = w & 0xffff
    simm = imm - 0x10000 if imm & 0x8000 else imm
    if op == 15: lui[rt] = (imm, a); continue
    if op in (32, 33, 35, 36, 37, 40, 41, 43) and rs in lui and a - lui[rs][1] <= 64:
        v = (lui[rs][0] << 16) + simm
        if 0xBE2000 <= v < 0xBE2200 or 0xBFFF00 <= v < 0xBFFF10:
            cm[('%06x' % v, cote(a)[0], 'E' if op >= 40 else 'L')] += 1
    if op in (9, 13) and rt != rs: lui.pop(rt, None)
print("\n## controle MIPS (adresse PS2 du registre, cote, sens : nombre)")
for k, n in sorted(cm.items()): print("  %s %s %s : %d" % (k + (n,)))
