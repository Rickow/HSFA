#!/usr/bin/env python3
"""ETAPE 3 : table de relogement des variables A5 d'Upper pour le code greffe (ro9 augmente).
Entrees : donnees/liste_arcade.pkl (etape 2 -> routines a greffer), acces A5 statiques (etude a5.pkl + balayage des
routines greffees, LEA compris), cartes RAM DYNAMIQUES (traces/h_*/ram.txt : Hyper ; traces/u_*/ram.txt : Upper),
acces statiques de toute la RAM d'Hyper (donnees/ram_statique_ro9.pkl).
Regles :
  - deplacement commun (Upper et Hyper l'utilisent) : identite, sauf les deux blocs deplaces par le portage d'Hyper
    ($C392-$C39D -> +$10, $C3A7-$C3A9 -> +$13) et les collisions de la zone $C388-$C3BC ;
  - deplacement propre a Upper : garde tel quel s'il est LIBRE dans Hyper (aucun acces A5/absolu statique, aucune
    lecture dynamique, aucune ecriture dynamique apres le demarrage), sinon RELOGE dans une zone prouvee libre ;
  - etendue d'une variable = taille d'acces, ou, pour un tableau (LEA d(A5) / acces indexe), jusqu'a la variable
    d'Upper suivante, bornee par la plage effectivement touchee par Upper en Arcade (carte dynamique).
Sorties : donnees/relogement_a5.tsv, donnees/relogement_a5.pkl {dep_upper: dep_hyper}, donnees/zones_libres_hyper.tsv."""
import os, sys, pickle, collections, struct, bisect
sys.path.insert(0, '<workspace>/work/greffe_arcade/outils')
import greffe as GR
import commun as C
from mips import Ins
G = GR.G; EU = GR.EU
DEMARRAGE = 120                      # images : effacements du demarrage (RAM entiere) toleres
TAILLE = {'lb':1,'lbu':1,'sb':1,'lh':2,'lhu':2,'sh':2,'lw':4,'sw':4,'lwu':4,'ld':8,'sd':8}

def s16(d): return d - 0x10000 if d >= 0x8000 else d
def cps2(d): return (0xFF8000 + s16(d)) & 0xFFFFFF
def dep(a): return (a - 0xFF8000) & 0xFFFF

def carte_dyn(traces):
    """adresse (octet, CPS2) -> [lu, ecrit_apres_demarrage, premiere_image]"""
    M = {}
    for t in traces:
        f = os.path.join(G, 'traces', t, 'ram.txt')
        if not os.path.exists(f): continue
        for l in open(f):
            a, r0, r1, w0, w1 = l.split(); a = int(a, 16); r0, w1 = int(r0), int(w1)
            for b in (a, a + 1):
                e = M.setdefault(b, [False, False])
                e[0] |= r0 >= 0; e[1] |= w1 > DEMARRAGE
    return M

def acces_routines(routines, mod='ro5', fins=None):
    """acces A5 des routines (balayage comme greffe.reloge, LEA = addiu compris) : dep -> {'tailles', 'lea', 'routines'}"""
    b5 = C.load(mod); A = collections.defaultdict(lambda: dict(tailles=set(), lea=False, routines=set(), n=0))
    for a in routines:
        b = fins[a] if fins else dict(C.funcs('ro5'))[a]; r7 = set(); a5r = set()
        for k in range((b - a) // 4):
            x = Ins(a + 4*k, struct.unpack_from('<I', b5, a + 4*k)[0])
            if x.m == 'lui': (r7.add if x.imm == 0x7000 else r7.discard)(x.rt); a5r.discard(x.rt); continue
            if x.m == 'lw' and x.rs in r7 and x.imm == 0x1114: a5r.add(x.rt); r7.discard(x.rt); continue
            if (x.m in GR.MEM or x.m == 'addiu') and x.rs in a5r:
                e = A[x.imm]; e['routines'].add(a); e['n'] += 1
                if x.m == 'addiu': e['lea'] = True
                else: e['tailles'].add(TAILLE.get(x.m, 1))
            d = GR.dest(x)
            if d is not None: a5r.discard(d); r7.discard(d)
    return A

def main():
    greffer = pickle.load(open(os.environ.get('GREFFER_PKL', os.path.join(G, 'donnees', 'greffe_v2.pkl')), 'rb'))   # (etape 2) ensemble greffe du plan
    A = acces_routines(greffer)
    a5 = pickle.load(open(os.path.join(EU, 'a5.pkl'), 'rb')); D5 = a5['D5']
    F9 = dict(C.funcs('ro9')); D9 = acces_routines(list(F9), 'ro9', F9)          # Hyper : acces ET LEA
    F5 = dict(C.funcs('ro5')); D5 = dict(acces_routines(list(F5), 'ro5', F5))
    S9 = pickle.load(open(os.path.join(G, 'donnees', 'ram_statique_ro9.pkl'), 'rb'))
    stat9 = set(S9['a5']) | set(S9['abs'])
    H_TR = ('h_versus', 'h_training'); U_TR = ('u_gagne00', 'u_perdu00', 'u_versus')
    dyn9 = carte_dyn(H_TR); dyn5 = carte_dyn(U_TR)
    deps5 = sorted(D5, key=s16); deps5s = [s16(x) for x in deps5]
    connus = sorted({s16(x) for x in D9})          # borne des tableaux : variable d'Hyper suivante
    DEPL = {}
    for d in range(0xC392, 0xC39E): DEPL[d] = d + 0x10
    for d in range(0xC3A7, 0xC3AA): DEPL[d] = d + 0x13
    COLL = (0xC38E, 0xC391, 0xC39E, 0xC39F, 0xC3A0, 0xC3A2, 0xC3A5, 0xC3A6)
    # 1) etendue de chaque deplacement utilise par le code greffe
    V = {}
    for d in sorted(A, key=s16):
        e = A[d]; base = cps2(d); tl = max(e['tailles']) if e['tailles'] else 1; ext = tl
        if e['lea']:                                    # tableau : plage CONTIGUE touchee par Upper (carte dynamique,
            k = bisect.bisect_right(connus, s16(d))     # trous <= 8 o) a partir de la base, bornee a la variable connue
            nxt = connus[k] if k < len(connus) else s16(d) + 0x1000      # suivante (Upper ou Hyper) et a 4 Ko
            lim = min(nxt - s16(d), 0x1000); ext = tl; trou = 0
            for o in range(tl, lim):
                if base + o in dyn5: ext = o + 1; trou = 0
                else:
                    trou += 1
                    if trou > 8: break
            ext = max(tl, ext)
        V[d] = (base, ext)
    # 2) blocs = reunion des etendues qui se chevauchent (deplaces d'un seul tenant)
    blocs = []
    for d in sorted(V, key=lambda x: V[x][0]):
        b0, ext = V[d]
        if d in DEPL or (d in D9 and d not in COLL) or 0x0400 <= d < 0x2000: continue   # structures J1/J2/objets : champs
        if blocs and b0 < blocs[-1][1]: blocs[-1][1] = max(blocs[-1][1], b0 + ext); blocs[-1][2].append(d)
        else: blocs.append([b0, b0 + ext, [d]])
    def preuve(a, b):
        st = sum(1 for x in range(a, b) if x in stat9)
        lu = sum(1 for x in range(a, b) if x in dyn9 and dyn9[x][0])
        ec = sum(1 for x in range(a, b) if x in dyn9 and dyn9[x][1])
        return st, lu, ec
    # 3) zones libres d'Hyper : ni acces statique, ni lecture, ni ecriture apres le demarrage ; et pas dans un bloc
    #    d'Upper garde tel quel
    libres = []; cur = None
    garde = set()
    for b0, b1, ds in blocs:
        st, lu, ec = preuve(b0, b1)
        if not (st or lu or ec) and not (0xFF4388 <= b0 < 0xFF43BD): garde |= set(range(b0, b1))
    for b in range(0xFF0000, 0x1000001):
        ok = b < 0x1000000 and b not in stat9 and not (b in dyn9 and (dyn9[b][0] or dyn9[b][1])) and b not in garde \
             and not (b in dyn5 and (dyn5[b][0] or dyn5[b][1])) \
             and not (0xFF8000 <= b < 0xFFA000)          # structures joueurs/objets : exclues par prudence
        if ok and cur is None: cur = b
        if not ok and cur is not None:
            if b - cur >= 16: libres.append([cur, b])
            cur = None
    with open(os.path.join(G, 'donnees', 'zones_libres_hyper_v2.tsv'), 'w') as f:
        f.write("debut\tfin\ttaille\n")
        for a, b in libres: f.write("$%06X\t$%06X\t%d\n" % (a, b, b - a))
    # 4) decision par bloc et allocation (premier ajustement, alignement 2 ; blocs les plus grands d'abord)
    dec_bloc = {}
    for b0, b1, ds in blocs:
        st, lu, ec = preuve(b0, b1)
        coll = any(d in COLL for d in ds) or (0xFF4388 <= b0 < 0xFF43BD)
        if not (st or lu or ec) and not coll: dec_bloc[b0] = ('identite (libre dans Hyper)', b0)
        elif st and not coll and b1 - b0 <= 4: dec_bloc[b0] = ('identite (meme mot qu\'une variable d\'Hyper : a verifier)', b0)
        else: dec_bloc[b0] = (('RELOGE : lu/ecrit par Hyper' if (st or lu) else 'RELOGE : efface par Hyper') if not coll else 'RELOGE : collision $C388-$C3BC', None)
    pool = sorted([list(z) for z in libres], key=lambda z: (not (0xFF43BE <= z[0] < 0xFF8000), z[0]))   # d'abord $FF43BE-$FF7FFF
    for b0, b1, ds in sorted(blocs, key=lambda x: -(x[1] - x[0])):
        if dec_bloc[b0][1] is not None: continue
        n = (b1 - b0 + 1) & ~1
        for z in pool:
            a = ((z[0] + 1) & ~1) + (b0 & 1)              # parite conservee (octet pair/impair, mots alignes)
            if z[1] - a >= n: dec_bloc[b0] = (dec_bloc[b0][0], a); z[0] = (a + n + 1) & ~1; break
    # 5) table par deplacement
    table = {}; lignes = []
    for d in sorted(V, key=s16):
        b0, ext = V[d]; st, lu, ec = preuve(b0, b0 + ext)
        if d in DEPL: nat, dec, nd = 'commun, deplace par le portage d\'Hyper', 'decalage', DEPL[d]
        elif d in D9 and d not in COLL: nat, dec, nd = 'commun', 'identite', d
        elif 0x0400 <= d < 0x2000:
            nat, dec, nd = 'champ de structure (J1 $FF8400 / J2 $FF8800 / objets)', 'identite (champ : voir table des champs A6)', d
        else:
            blk = next(b for b in blocs if b[0] <= b0 < b[1])
            dd, nb = dec_bloc[blk[0]]
            nat = 'collision $C388-$C3BC' if d in COLL else 'propre a Upper'
            dec = dd; nd = None if nb is None else dep(nb + (b0 - blk[0]))
        table[d] = nd
        lignes.append((d, b0, ext, A[d]['n'], len(A[d]['routines']), 'oui' if A[d]['lea'] else '', nat,
                       'A5/abs:%d lu:%d ecrit:%d' % (st, lu, ec), dec, nd))
    with open(os.path.join(G, 'donnees', 'relogement_a5_v2.tsv'), 'w') as f:
        f.write("dep_upper\tcps2_upper\tetendue\tacces\troutines\ttableau\tnature\tpreuves_hyper(octets)\tdecision\tdep_hyper\tcps2_hyper\n")
        for d, base, ext, n, nr, lea, nat, pr, dec, nd in lignes:
            f.write("$%04X\t$%06X\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s\n" % (d, base, ext, n, nr, lea, nat, pr, dec,
                    ('$%04X' % nd) if nd is not None else '?', ('$%06X' % cps2(nd)) if nd is not None else '?'))
    pickle.dump(dict(table=table, lignes=lignes, blocs=blocs, dec_bloc=dec_bloc, libres=libres, greffer=greffer),
                open(os.path.join(G, 'donnees', 'relogement_a5_v2.pkl'), 'wb'))
    c = collections.Counter(l[8] for l in lignes)
    print("routines a greffer : %d ; deplacements A5 utilises : %d" % (len(greffer), len(lignes)))
    for k, v in c.most_common(): print("   %-40s %d" % (k, v))
    nr = [(b0, b1) for b0, b1, _ in blocs if dec_bloc[b0][0].startswith('RELOGE')]
    print("blocs propres a Upper : %d ; a reloger : %d (%d octets), non places : %d" % (len(blocs), len(nr), sum(b - a for a, b in nr),
          sum(1 for b0, _, _ in blocs if dec_bloc[b0][1] is None)))
    print("zones libres d'Hyper (>= 16 o, hors $FF8000-$FF9FFF) : %d, %d octets" % (len(libres), sum(b - a for a, b in libres)))

if __name__ == "__main__":
    main()
