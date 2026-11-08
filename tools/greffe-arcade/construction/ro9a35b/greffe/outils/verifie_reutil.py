#!/usr/bin/env python3
"""Verification des routines « REUTILISER » de l'etape 2 (homologue ro9 identique, constantes MASQUEES) :
les instructions sont alignees une a une et chaque constante 32 bits (lui + addiu/ori/acces) d'Upper est comparee a
celle d'Hyper apres relogement :
  - code : cible Upper -> homologue (inverse_ro5) == cible Hyper ?
  - donnees : memes octets aux deux adresses (64 o, pointeurs masques) ?
  - RAM : rebasee (+$180000) et table A5 ; port : table des variables du portage ;
  - jal : cible Upper -> homologue == cible Hyper ?
Une routine dont une constante differe est « douteuse » : on la greffe (copie d'Upper) au lieu de la reutiliser.
Sorties : donnees/verifie_reutil.tsv, donnees/coeur_greffe_v2.pkl (coeur de l'etape 2 + douteuses)."""
import os, sys, pickle, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import greffe as GR
import commun as C
from mips import Ins
G = GR.G
R5 = pickle.load(open(os.path.join(G, 'donnees', 'relogement_a5.pkl'), 'rb'))['table']

def consts(L):
    lu = {}; out = {}
    for k, x in enumerate(L):
        if x.m in ('jal', 'j'): out[k] = ('jal', x.tgt)
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if (x.m in GR.MEM or x.m in ('addiu', 'ori')) and x.rs in lu:
            v = (lu[x.rs] | x.imm) if x.m == 'ori' else (lu[x.rs] + x.simm) & 0xffffffff
            out[k] = ('c', v)
        d = GR.dest(x)
        if d is not None: lu.pop(d, None)
    return out

def _norm(b, a, n):
    out = []
    for k in range(n):
        w = struct.unpack_from('<I', b, a + 4*k)[0]; op = w >> 26
        if op in (2, 3): w &= 0xFC000000
        elif op in (0x0f, 0x09, 0x0d): w &= 0xFFFF0000
        out.append(w)
    return out
def meme_routine(f5, f9):
    """la routine d'Upper f5 et le code d'Hyper en f9 : memes instructions (constantes et cibles masquees) ?"""
    n = GR.INV[f5]['taille'] // 4
    if not (0 <= f9 < GR.H9['code_end'] - 4 * n): return False
    return _norm(C.load('ro5'), f5, n) == _norm(C.load('ro9'), f9, n)
def masque(b, o, n=32):
    seg = bytearray(b[o:o + n])
    for i in range(0, len(seg) - 3, 4):
        v = struct.unpack_from('<I', seg, i)[0]
        if 0x200000 <= v < 0x1000000: seg[i:i + 4] = b'PPPP'
    return bytes(seg)

def compare(a):
    r = GR.INV[a]; p = r['partenaire']; n = r['taille'] // 4
    b5, b9 = C.load('ro5'), C.load('ro9')
    L5 = [Ins(a + 4*k, struct.unpack_from('<I', b5, a + 4*k)[0]) for k in range(n)]
    L9 = [Ins(p + 4*k, struct.unpack_from('<I', b9, p + 4*k)[0]) for k in range(n)]
    if [x.op for x in L5] != [y.op for y in L9]: return 'longueur/forme differente', []
    c5, c9 = consts(L5), consts(L9); diff = []
    g = GR.Greffe([], a5=lambda d: R5.get(d, d))
    for k, (t, v) in c5.items():
        if k not in c9: diff.append((L5[k].va, 'sans contrepartie')); continue
        w = c9[k][1]; cl = GR.classe_valeur(v, GR.H5)
        if (t == 'jal' or cl == 'code') and not (GR.BASE + 0x22B00 <= v < GR.BASE + GR.H5['code_end']):
            if v != w: diff.append((L5[k].va, 'externe %x -> %x' % (v, w)))      # fonction de l'executable PS2
            continue
        if t == 'jal' or cl == 'code':
            f = v - GR.BASE; q = GR.INV.get(f)
            if v in GR.AIDES: ok = GR.AIDES[v] == w
            elif f in GR.INV and meme_routine(f, w - GR.BASE): ok = True
            elif q and q['partenaire'] is not None: ok = q['partenaire'] + GR.BASE == w        # homologue (toute classe)
            else:                                        # cible au milieu d'une routine : meme decalage chez l'homologue
                st = C.starts('ro5'); import bisect as _b; s0 = st[_b.bisect_right(st, f) - 1]; q0 = GR.INV.get(s0)
                ok = bool(q0 and q0['partenaire'] is not None and q0['partenaire'] + (f - s0) + GR.BASE == w)
            if not ok: diff.append((L5[k].va, 'code %x -> %x' % (v, w)))
        elif cl == 'data':
            if GR.classe_valeur(w, GR.H9) != 'data' or masque(b5, v - GR.BASE) != masque(b9, w - GR.BASE):
                diff.append((L5[k].va, 'donnees %x / %x' % (v, w)))
        elif cl in ('ram', 'port'):
            nv = g.valeur(v, L5[k].va)
            if nv is not None and nv != w: diff.append((L5[k].va, '%s %x -> %x (ro9 %x)' % (cl, v, nv, w)))
    return ('identique apres relogement' if not diff else 'DOUTEUSE'), diff

def main():
    L = pickle.load(open(os.path.join(G, 'donnees', 'liste_arcade.pkl'), 'rb'))
    coeur = set(pickle.load(open(os.path.join(G, 'donnees', 'coeur_greffe.pkl'), 'rb')))
    cand = [l for l in L['lignes'] if l['decision'].startswith('REUTILISER') and l['part']
            and not all(x.startswith('hors partie') for x in l['scenes'])
            and not l['zone'].startswith(('code des persos', 'moteur de combat'))]
    res = collections.Counter(); dout = []
    with open(os.path.join(G, 'donnees', 'verifie_reutil.tsv'), 'w') as f:
        f.write("va_ro5\tpartenaire_ro9\tvu_VERSUS\tverdict\tdifferences\n")
        for l in cand:
            v, d = compare(l['r']); res[v] += 1
            if v != 'identique apres relogement': dout.append(l['r'])
            f.write("0x%X\t0x%X\t%s\t%s\t%s\n" % (l['r'], l['part'], 'oui' if l['vs'] else 'non', v, '; '.join('%x:%s' % e for e in d[:6])))
    pickle.dump(sorted(coeur | set(dout)), open(os.path.join(G, 'donnees', 'coeur_greffe_v2.pkl'), 'wb'))
    t = sum(GR.INV[a]['taille'] for a in dout)
    print("routines REUTILISER verifiees (chemin Arcade, hors attraction/moteur/persos) : %d -> %s" % (len(cand), dict(res)))
    print("douteuses ajoutees au coeur : %d (%d o, %.1f Ko) ; coeur v2 : %d routines, %.1f Ko" % (
        len(dout), t, t / 1024, len(coeur | set(dout)), sum(GR.INV[a]['taille'] for a in coeur | set(dout)) / 1024))

if __name__ == "__main__":
    main()
