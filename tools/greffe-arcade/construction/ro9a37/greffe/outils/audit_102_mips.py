#!/usr/bin/env python3
"""ETAPE 5 : lectures (et ecritures) du champ $102 (id perso, numerotation PS2) dans le code a greffer et dans les
routines d'Hyper REUTILISEES sur le chemin Arcade (partenaires identiques executees en Arcade seulement).
Classement de chaque lecture par les instructions qui suivent (meme registre) :
  INDEX  : sert d'index (sll/addu vers une base de table)  -> $116 si la table est par perso de base (40 entrees) ;
  CMP    : compare a une constante (slti/sltiu/xori/beq/bne avec constante) -> $116 si la constante est un id de base ;
  COPIE  : rangee dans un autre champ / une variable (sb)   -> garder $102 (version) ET recopier $116/$117 ;
  AUTRE  : a examiner.
Sortie : donnees/audit_102.tsv"""
import os, sys, pickle, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import greffe as GR
import commun as C
from mips import Ins
G = GR.G

def sites(mod, routines, ends):
    b = C.load(mod); out = []
    for a in routines:
        e = ends[a]; regs = set(); lu = {}
        L = [Ins(a + 4*k, struct.unpack_from('<I', b, a + 4*k)[0]) for k in range((e - a) // 4)]
        for i, x in enumerate(L):
            if x.m == 'lui': lu[x.rt] = x.imm << 16
            if x.m == 'lw' and 0x1100 <= x.imm <= 0x1118: regs.add(x.rt); continue
            if x.m in ('lb', 'lbu', 'sb') and x.rs in regs and x.imm == 0x102:
                if x.m == 'sb': out.append((a, x.va, 'ECRITURE', '')); continue
                r = x.rt; cl = 'AUTRE'; det = ''
                for y in L[i + 1:i + 14]:
                    if y.m in ('sll', 'dsll', 'dsll32', 'addu', 'daddu') and (y.rt == r or y.rs == r):
                        # suite : base de table formee par lui/addiu
                        cl = 'INDEX'; break
                    if y.m in ('slti', 'sltiu', 'xori', 'andi') and y.rs == r:
                        cl = 'CMP'; det = '#$%X' % y.imm; break
                    if y.m in ('beq', 'bne') and (y.rs == r or y.rt == r):
                        cl = 'CMP'; break
                    if y.m in ('sb', 'sh', 'sw') and y.rt == r:
                        cl = 'COPIE'; det = 'vers %d(%s)' % (y.simm, y.rs); break
                    if GR.dest(y) == r: break
                out.append((a, x.va, cl, det))
            d = GR.dest(x)
            if d is not None: regs.discard(d)
    return out

def main():
    L = pickle.load(open(os.path.join(G, 'donnees', 'liste_arcade.pkl'), 'rb'))
    greffer = pickle.load(open(os.path.join(G, 'donnees', 'coeur_greffe.pkl'), 'rb'))     # etape 2 : coeur a greffer
    reuse = sorted({l['part'] for l in L['lignes'] if l['decision'].startswith('REUTILISER') and not l['vs'] and l['part']
                    and not l['zone'].startswith(('code des persos', 'moteur de combat', 'intro'))
                    and not all(x.startswith('hors partie') for x in l['scenes'])})
    e5 = {a: GR.INV[a]['b'] for a in greffer}
    e9 = dict(C.funcs('ro9'))
    S5 = sites('ro5', greffer, e5); S9 = sites('ro9', reuse, e9)
    with open(os.path.join(G, 'donnees', 'audit_102.tsv'), 'w') as f:
        f.write("module\troutine\tsite\tclasse\tdetail\n")
        for m, S in (('ro5 (greffe)', S5), ('ro9 (reutilise)', S9)):
            for a, va, cl, det in S: f.write("%s\t0x%X\t0x%X\t%s\t%s\n" % (m, a, va, cl, det))
    for m, S in (('ro5 greffe', S5), ('ro9 reutilise', S9)):
        c = collections.Counter(cl for _, _, cl, _ in S)
        print("%s : %d sites dans %d routines : %s" % (m, len(S), len({a for a, *_ in S}), dict(c)))

if __name__ == "__main__":
    main()
