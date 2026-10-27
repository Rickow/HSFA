#!/usr/bin/env python3
"""Decodage des objets attaches de Vega dans Upper (agent_effets_upper).
Lit la COPIE locale : prog.bin (programme traduit remis bout a bout, fait_prog.py), ro5/ext_c80000.bin, ro5/ext_b04000.bin,
ro5/banques_hx/f351.bin. Vue « image » = ce que lit le 68K (mots natifs, longs a moities echangees, octets XOR 1).

  T_60D480 (image $A37C0)   : index (octet +$12 du pas du corps) -> (n° anim masque, n° anim griffe), 4 octets
  ANIM_MASQUE (image $EC288 = PS2 0x655F48), ANIM_GRIFFE (image $ED028 = PS2 0x656CE8) : tables de mots relatifs
  pas de 8 octets : duree, drapeaux, mot, long frame (PS2, converti par CONV_A0 = routine $4FE)
  frames type 0 / 2 (gestionnaires $2C86C / $2C900), positions dans le fichier 390 ($B04000).
Usage : decode_attaches.py [--tout]  (sortie texte sur stdout)
"""
import struct, sys, os
D = os.path.dirname(os.path.abspath(__file__))
IMG = open(os.path.join(D, 'prog.bin'), 'rb').read()
EXT = {0xC80000: open(os.path.join(D, 'ro5/ext_c80000.bin'), 'rb').read(),
       0xB04000: open(os.path.join(D, 'ro5/ext_b04000.bin'), 'rb').read()}
F351 = open(os.path.join(D, 'ro5/banques_hx/f351.bin'), 'rb').read()

def conv(a):
    """CONV_A0 d'Upper (image $400 -> $4FE) : adresse PS2 -> adresse 68K"""
    if a < 0x60ACC0 or a >= 0xC3FC50: return a
    if a >= 0xA14000:
        if a >= 0xA60000:
            if a >= 0xA80000:
                return (a - 0x885100) & 0xFFFFFFFF if a >= 0xC00000 else a
            return a + (0x530000 if a >= 0xA62000 else 0xBB8000)
        if a >= 0xA20000: return a + (0x530000 if a >= 0xA50000 else 0xEE0000)
        return a
    if a >= 0xA00000:
        if a >= 0xA10000: return a + (0xCF6000 if a >= 0xA12000 else 0xCF0000)
        return a + 0x5F0000
    if a >= 0x8E4AE0: return a + (0x55FE80 if a >= 0x9A0180 else 0x39B520)
    return (a - 0x569CC0) & 0xFFFFFFFF

def w(a):
    """mot lu par le 68K a l'adresse a"""
    if a < len(IMG): return struct.unpack_from('>H', IMG, a)[0]
    for b, s in EXT.items():
        if b <= a < b + len(s): return struct.unpack_from('>H', s, a - b)[0]
    raise ValueError('adresse %X hors image' % a)
def ws(a): v = w(a); return v - 0x10000 if v & 0x8000 else v
def l_ech(a): return (w(a + 2) << 16) | w(a)      # long a moities echangees (§29) = valeur PS2
def ps2_de_image(a): return a + 0x569CC0          # zone principale des donnees (image < $37F508)

def e351(c):
    return struct.unpack_from('<I', F351, 4 * c)[0] if 4 * c + 4 <= len(F351) else None

def frame(fa):
    """frame a l'adresse 68K fa -> dict"""
    t = w(fa)
    r = {'adr': fa, 'type': t}
    if t == 0:
        n = w(fa + 2); attr = w(fa + 4); p = (fa + 6 + 3) & ~3
        pos = l_ech(p); q = p + 4
        codes = [w(q + 2 * i) for i in range(n)]
        r.update(T=n, n=n, attr=attr, pos_ps2=pos, objets=[(c, attr) for c in codes])
        r['fin'] = q + 2 * n
    elif t == 2:
        T = w(fa + 2); n = w(fa + 4) + 1; p = (fa + 6 + 3) & ~3
        pos = l_ech(p); q = p + 4
        objs = [(w(q + 4 * i), w(q + 4 * i + 2)) for i in range(n)]
        r.update(T=T, n=n, pos_ps2=pos, objets=objs, fin=q + 4 * n)
    elif t in (0x12, 0x16, 0x18, 0x1A, 0x1C, 0x28):
        r['note'] = 'frame vide'; return r
    else:
        r['note'] = 'type non decode'
        return r
    pa = conv(r['pos_ps2'])
    r['pos'] = [(ws(pa + 4 * i), ws(pa + 4 * i + 2)) for i in range(r['n'])]
    return r

def anims(table_img, n=None):
    if n is None: n = w(table_img) // 2
    out = []
    for i in range(n):
        s = table_img + ws(table_img + 2 * i)
        pas = []
        for _ in range(64):
            fl, du = w(s) >> 8, w(s) & 0xFF
            fp = l_ech(s + 4)
            pas.append((s, du, fl, fp))
            if fl & 0x80 or fl & 0x40: break
            if du == 0xFF: break                    # pas tenu : l'objet attache change d'animation lui-meme
            s += 8
        out.append(pas)
    return out

def resume_frame(f):
    if 'objets' not in f: return 'type $%X (%s)' % (f['type'], f.get('note'))
    cs = [c for c, a in f['objets']]
    return 'type %d T=%d n=%d codes e351 %d-%d pos=%08X' % (f['type'], f['T'], f['n'], min(cs), max(cs), f['pos_ps2'])

if __name__ == '__main__':
    tout = '--tout' in sys.argv
    print('# T_60D480 (image $A37C0, PS2 0x60D480) : index -> (anim masque, anim griffe)')
    idx = [(w(0xA37C0 + 4 * i), w(0xA37C0 + 4 * i + 2)) for i in range(0x180)]
    print('entrees 0..%d ; max masque %d, max griffe %d' % (len(idx) - 1, max(a for a, b in idx), max(b for a, b in idx)))
    for i in range(0, len(idx), 8):
        print('  %03X : ' % i + ' '.join('%03X/%03X' % e for e in idx[i:i + 8]))
    tous = []
    nm, ng = max(a for a, b in idx) + 1, max(b for a, b in idx) + 1
    for nom, tab, nb in (('MASQUE (classe $13)', 0xEC288, nm), ('GRIFFE (classe $14)', 0xED028, ng), ('MORCEAUX (classe 0 = masque : anims 2-4 ; classe 1 = griffe : anims 0-1)', 0xEC1D0, 5)):
        A = anims(tab, nb)
        print('\n# %s : table image $%06X = PS2 0x%06X, %d animations' % (nom, tab, ps2_de_image(tab), len(A)))
        for i, pas in enumerate(A):
            for (s, du, fl, fp) in pas:
                fa = conv(fp)
                try: f = frame(fa); txt = resume_frame(f); tous += [c for c, a in f.get('objets', [])]
                except Exception as e: txt = 'erreur %s' % e
                if tout or i < 4 or len(A) - i <= 1:
                    print('  anim %3d pas $%06X duree %3d drap %02X frame PS2 %08X -> $%06X %s' % (i, s, du, fl, fp, fa, txt))
    print('\n# codes e351 de toutes ces frames : %d..%d' % (min(tous), max(tous)))
