#!/usr/bin/env python3
"""ETAPE 2, point 6 : lectures de $102 (id perso avec version, PS2 ; $0103 en 68K) dans le CODE GREFFE.
Regle du rapport de preparation (§5), appliquee par patch MIPS du deplacement du 'lb/lbu 0x102(rA)' :
  INDEX (table par perso a 40 entrees)          -> $116 (perso de base 0-$27, PS2 ; $0117 en 68K)
  CMP a une constante < $28 (id de base)        -> $116
  CMP a une constante >= $28 (pseudo-ids)       -> garder
  COPIE / ECRITURE / TEST / AUTRE               -> garder (journal) ; les ecritures de l'adversaire CPU ne posent
     que $102 : Hyper recalcule $116/$117 depuis $102 a l'init du joueur (0x2A1630 -> 0x321BA0), verifie en partie.
Classement : outils/audit_102.classe() sur la traduction 68K d'Upper. Sortie : donnees/patch_116.tsv ;
bibliotheque : sites(routines) -> [(va_mips_upper, classe, detail, instruction 68K, patcher?)]"""
import os, sys, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils")
import plan as PL
from mips import Ins

def sites(routines):
    os.environ['MODULE'] = 'ro5'
    sys.path.insert(0, os.path.join(PL.G, 'untranspile'))
    for m_ in ('mips', 'translate'): sys.modules.pop(m_, None)
    import audit_102 as AU
    out = []
    for a in sorted(routines):
        Lg = AU.lignes68('ro5', a, PL.E5[a])
        for i, (va, t) in enumerate(Lg):
            if '$0103(A' not in t or '$0103(A5)' in t: continue        # $0103(A5) = variable globale, pas un joueur
            c, det = AU.classe(Lg, i)
            # instruction MIPS lb/lbu ...,0x102(r) a va ou juste avant
            lbva = None
            for o in range(va, max(a, va - 0x80) - 4, -4):
                x = Ins(o, struct.unpack_from('<I', PL.b5, o)[0])
                if x.m in ('lb', 'lbu') and x.imm == 0x102: lbva = o; break
            pat = False
            if lbva is not None:
                if c == 'INDEX': pat = True
                elif c == 'CMP':
                    m = re.match(r'#\$([0-9a-f]+)', det)
                    pat = bool(m) and int(m.group(1), 16) < 0x28
            out.append((a, va, lbva, c, det, t, pat))
    return out

if __name__ == "__main__":
    import pickle, collections
    R = pickle.load(open(os.path.join(PL.G, 'donnees', 'greffe_v2.pkl'), 'rb'))
    S = sites(R)
    with open(os.path.join(PL.G, 'donnees', 'patch_116.tsv'), 'w') as f:
        f.write("routine\tva_68k\tva_lb\tclasse\tdetail\tinstruction_68K\tpatch_$116\n")
        for a, va, lb, c, det, t, pat in S:
            f.write("0x%X\t0x%X\t%s\t%s\t%s\t%s\t%s\n" % (a, va, ('0x%X' % lb) if lb else '-', c, det, t, 'oui' if pat else 'non'))
    c = collections.Counter((x[3], x[6]) for x in S)
    print("acces a $102 dans le code greffe : %d (%d routines) ; %s" % (len(S), len({x[0] for x in S}), dict(c)))
