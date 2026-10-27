#!/usr/bin/env python3
"""Désassemblage (unidasm de MAME) et normalisation des instructions 68000 pour l'alignement
image traduite <-> ROM arcade. Lecture seule hors de work/agent_symboles/."""
import re, os, subprocess, pickle
ICI = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(ICI, '..', '_cache')
os.makedirs(TMP, exist_ok=True)
RX = re.compile(r'^([0-9a-f]+): ((?:[0-9a-f]{4} )+)\s*(\S+)\s*(.*)$')

def desasm(binfile, base, deb, fin, cle):
    """renvoie [(adresse, taille, mnémonique, opérandes)]"""
    pk = os.path.join(TMP, cle + '.pkl')
    if os.path.exists(pk): return pickle.load(open(pk, 'rb'))
    d = open(binfile, 'rb').read()[deb - base:fin - base]
    tmp = os.path.join(TMP, cle + '.bin'); open(tmp, 'wb').write(d)
    out = subprocess.run(['nice', '-n', '19', 'unidasm', '-arch', 'm68000', '-basepc', hex(deb), tmp],
                         capture_output=True, text=True).stdout
    L = []
    for l in out.splitlines():
        m = RX.match(l)
        if not m: continue
        a = int(m.group(1), 16); n = len(m.group(2).split()) * 2
        L.append((a, n, m.group(3), m.group(4).strip()))
    pickle.dump(L, open(pk, 'wb'))
    return L

R_ABSL = re.compile(r'\$[0-9a-f]+\.l')
R_ABSW = re.compile(r'\$[0-9a-f]+\.w')
R_PCIX = re.compile(r'\(-?\$[0-9a-f]+,PC,(\w+\.\w)\)')
R_PC = re.compile(r'\(-?\$[0-9a-f]+,PC\)')
R_IMM = re.compile(r'#\$([0-9a-f]+)')
BR = re.compile(r'^(b(ra|sr|hi|ls|cc|cs|ne|eq|vc|vs|pl|mi|ge|lt|gt|le)|db\w+)(\.[sw])?$')

OCTET = {'tas', 'nbcd', 'btst', 'bset', 'bclr', 'bchg', 'st', 'sf', 'shi', 'sls', 'scc', 'scs', 'sne',
         'seq', 'svc', 'svs', 'spl', 'smi', 'sge', 'slt', 'sgt', 'sle'}
R_DISP = re.compile(r'\((-?)\$([0-9a-f]+),(A[0-7])\)')

def xor_octets(mn, ops):
    """image traduite : déplacements des accès OCTET en numérotation PS2 (XOR 1) -> numérotation 68K"""
    if not (mn.endswith('.b') or mn in OCTET): return ops
    def f(m):
        v = -int(m.group(2), 16) if m.group(1) else int(m.group(2), 16)
        v ^= 1
        return '(%s$%x,%s)' % ('-' if v < 0 else '', abs(v), m.group(3))
    return R_DISP.sub(f, ops)

def norm(mn, ops):
    """jeton normalisé : adresses absolues / relatives au PC / cibles de branchement masquées,
    déplacements sur An et immédiats conservés."""
    if mn == 'dc.w': return None
    m = BR.match(mn)
    if m:
        b = m.group(1)
        if b == 'bsr': return 'CALL'
        if b == 'bra': return 'GOTO'
        if b.startswith('db'): return b + ' ' + ops.split(',')[0]
        return b
    if mn in ('jsr', 'jmp'):
        if 'PC,' in ops: return mn + ' TBL'
        if ops.startswith('(A'): return mn + ' ' + ops
        return 'CALL' if mn == 'jsr' else 'GOTO'
    o = R_ABSL.sub('ADDR', ops)
    o = R_ABSW.sub('ADDRW', o)
    o = R_PCIX.sub(r'(TBL,\1)', o)
    o = R_PC.sub('ADDR', o)
    def imm(mm):
        v = int(mm.group(1), 16)
        return '#ADR' if 0x1000 <= v < 0x400000 and mn.endswith('.l') else mm.group(0)
    o = R_IMM.sub(imm, o)
    return mn + ' ' + o
