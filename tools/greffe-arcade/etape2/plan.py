#!/usr/bin/env python3
"""PLAN DE GREFFE (etape 2) : fermeture du code d'Upper a greffer a partir de racines, avec une decision par routine
atteinte : GREFFE (copie d'Upper), HYPER (homologue d'Hyper), NATIF (talon / natif homologue d'Hyper).

Regles (dans l'ordre) pour une routine X d'Upper atteinte depuis du code greffe :
  a) decision imposee (FORCE) ;
  b) native (code C du portage) -> natif homologue d'Hyper s'il est natif aussi, sinon talon RTS ;
  c) absente d'Hyper (couverture < 50 %) ou sans homologue -> GREFFE ;
  d) modifiee du coeur : tri (tri_modifiees) HYPER -> HYPER, COPIE/MIXTE -> GREFFE ;
  e) equivalente a son homologue (memes instructions ; constantes de code -> meme decision ; donnees de meme contenu ;
     RAM/portage reloges a l'identique ; deplacements A5 non reloges) -> HYPER ;
  f) zone « code des persos » / « moteur de combat » -> HYPER (on garde le moteur d'Hyper) ;
  g) modifiee hors coeur (jamais vue en Arcade) -> HYPER (journal) ;
  h) presente mais non equivalente (lit d'autres donnees, appelle du code greffe...) -> GREFFE.
References suivies : jal/j, constantes de code (lui+addiu), pointeurs de code des tables de donnees visees
(longs alignes visant un debut de routine d'Upper, dans l'etendue de la table bornee par la constante suivante).
Usage : bibliotheque (ferme(racines, force) -> Plan)."""
import os, sys, struct, pickle, collections, bisect, functools
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import greffe as GR
import commun as C
from mips import Ins
G = GR.G; BASE = GR.BASE
b5, b9 = C.load('ro5'), C.load('ro9')
F5 = C.funcs('ro5'); F9 = C.funcs('ro9')
S5 = [a for a, _ in F5]; E5 = dict(F5); E9 = dict(F9)
HOM = pickle.load(open(os.path.join(G, 'donnees', 'homologues.pkl'), 'rb'))
HOMC, HOMD = HOM['code'], HOM['donnees']
HOMDT = HOM.get('donnees_tous', {})
TRI = pickle.load(open(os.path.join(G, 'donnees', 'tri_modifiees.pkl'), 'rb'))
LA = pickle.load(open(os.path.join(G, 'donnees', 'liste_arcade.pkl'), 'rb'))
BY = {l['r']: l for l in LA['lignes']}
COURTES = set(LA['courtesA'])          # routines courtes (relais...) vues en Arcade, indecidables par la couverture
CK = pickle.load(open(os.path.join(GR.EU, 'couv_k.pkl'), 'rb'))
BA = pickle.load(open(os.path.join(GR.EU, 'bilan_absent.pkl'), 'rb'))
RA5 = pickle.load(open(os.path.join(G, 'donnees', 'relogement_a5.pkl'), 'rb'))['table']
NAT9 = None

def natifs9():
    global NAT9
    if NAT9 is None:
        import json
        h = json.load(open(os.path.join(G, 'untranspile', 'hooks_fork_ro9.json')))
        NAT9 = {int(k, 16) for k, v in h.items() if v.get("type") == "natif du module"}
    return NAT9

def native_at(b, t, h):
    """critere de mame_test.native_at (fonction C du portage ?) sur [t, premier 'jr ra'] ; un relais court vers du
    code du module n'est PAS natif (traduit)"""
    L = []
    for o in range(t, t + 0x4000, 4):
        x = Ins(o, struct.unpack_from('<I', b, o)[0]); L.append(x)
        if x.m == 'jr' and x.rs == 31: break
    a = sum(1 for x in L if x.m == 'lui' and x.imm == 0x7000); n = len(L)
    s_ = sum(1 for x in L if x.m in ('sq', 'lq', 'mult', 'multu', 'div', 'divu', 'mfhi', 'mflo')
             or (x.m == 'addiu' and x.rs == 29 and x.rt == 29 and -0x400 < x.simm < -16 and x.simm % 16 == 0))
    lu = {}; relais = False; c0, c1 = BASE + 0x22B00, BASE + h['code_end']
    for x in L:
        if x.m == 'lui': lu[x.rt] = x.imm
        elif x.m == 'addiu' and x.rs in lu: lu[x.rt] = (lu[x.rs] << 16) + x.simm
        elif (x.m == 'jalr' and x.rs in lu and c0 <= lu[x.rs] < c1) or (x.m == 'jal' and c0 <= x.tgt < c1): relais = True
    if a == 0 and (n <= 8 or (n <= 24 and relais)): return False
    return a == 0 or (s_ > 0 and a * 20 < n)

@functools.lru_cache(None)
def est_natif5(x): return bool(GR.INV.get(x, {}).get('nat')) and native_at(b5, x, GR.H5)

def _ratio(a5, a9):
    import difflib
    e5, e9 = E5.get(a5), E9.get(a9)
    if e5 is None or e9 is None: return 0.0
    nw = lambda w: (w & 0xFC000000) if (w >> 26) in (2, 3) else ((w & 0xFFFF0000) if (w >> 26) in (0x0f, 0x09, 0x0d) else w)
    return difflib.SequenceMatcher(None, [nw(x.w) for x in ins(b5, a5, e5)], [nw(x.w) for x in ins(b9, a9, e9)], autojunk=False).ratio()

@functools.lru_cache(None)
def homologue(a5):
    """homologue d'Hyper : propage (positionnel) s'il est majoritaire et au moins aussi ressemblant que le partenaire
    d'inverse_ro5 ; sinon le partenaire d'inverse_ro5"""
    h = HOMC.get(a5); p = GR.INV.get(a5, {}).get('partenaire')
    if h and h[1] > h[2]:
        if p is None or p == h[0] or _ratio(a5, h[0]) >= _ratio(a5, p): return h[0]
    return p

def routine_de(f):
    k = bisect.bisect_right(S5, f) - 1
    return S5[k] if k >= 0 else None

def ins(b, a, e): return [Ins(o, struct.unpack_from('<I', b, o)[0]) for o in range(a, e, 4)]

@functools.lru_cache(None)
def refs_donnees5():
    out = set(); lu = {}
    for x in C.instrs('ro5'):
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if x.m in ('addiu', 'ori') and x.rs in lu:
            v = (lu[x.rs] | x.imm) if x.m == 'ori' else (lu[x.rs] + x.simm) & 0xffffffff
            if GR.classe_valeur(v, GR.H5) == 'data': out.add(v)
        d = GR.dest(x)
        if d is not None: lu.pop(d, None)
    return sorted(out)

def etendue(v, cap=0x2000):
    R = refs_donnees5(); k = bisect.bisect_right(R, v)
    fin = min(R[k] if k < len(R) else GR.H5['data_end'], v + cap, GR.H5['data_end'])
    return fin - v

def ptrs_code(v):
    """pointeurs de code PROUVES d'une table de donnees d'Upper (longs alignes visant un debut de routine). Comme
    translate.read_jump_table : la table continue au-dela de la constante suivante si elle finit par un trou (0)."""
    if v & 3: return []
    n = etendue(v); out = []; i = 0
    while i < 0x2000:
        if i >= n - 3:                 # au-dela de la table suivante : seulement apres un trou (entree nulle)
            if not (i >= 4 and out and struct.unpack_from('<I', b5, v - BASE + i - 4)[0] == 0): break
            q = struct.unpack_from('<I', b5, v - BASE + i)[0]
            if not (GR.classe_valeur(q, GR.H5) == 'code' or q == 0): break
        p = struct.unpack_from('<I', b5, v - BASE + i)[0]
        if GR.classe_valeur(p, GR.H5) == 'code' and (p - BASE) in E5: out.append((i, p - BASE))
        elif MILIEUX and GR.classe_valeur(p, GR.H5) == 'code' and not (p & 3) and routine_de(p - BASE) is not None:
            out.append((i, routine_de(p - BASE)))          # entree au milieu d'une routine (etats, aiguillages)
        i += 4
    return out
MILIEUX = os.environ.get("MILIEUX", "1") == "1"

def consts(L):
    lu = {}; out = []
    for k, x in enumerate(L):
        if x.m in ('jal', 'j'): out.append((k, 'jal', x.tgt))
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if (x.m in GR.MEM or x.m in ('addiu', 'ori')) and x.rs in lu:
            v = (lu[x.rs] | x.imm) if x.m == 'ori' else (lu[x.rs] + x.simm) & 0xffffffff
            out.append((k, 'c', v))
        d = GR.dest(x)
        if d is not None: lu.pop(d, None)
    return out

def refs_routine(r):
    """(type, cible fichier ou valeur) : code (jal, constantes), donnees (constantes)"""
    e = E5[r]; L = ins(b5, r, e); out = []
    for k, t, v in consts(L):
        cl = GR.classe_valeur(v, GR.H5) if t == 'c' else 'code'
        if t == 'jal':
            if GR.BASE + 0x22B00 <= v < GR.BASE + GR.H5['code_end']: out.append(('code', v - BASE, L[k].va))
        elif cl == 'code': out.append(('code', v - BASE, L[k].va))
        elif cl == 'data': out.append(('data', v, L[k].va))
    return out

class Plan:
    def __init__(self, force=None):
        self.force = dict(force or {})
        self.dec = {}                 # routine Upper -> ('GREFFE',) | ('HYPER', f9) | ('NATIF', f9 ou None)
        self.raison = {}
        self.donnees = set()          # constantes de donnees visees par le code greffe
        self.journal = collections.defaultdict(list)
        self._eq = {}
        self.refs = set()
        self.parent = {}

    def equivalent(self, x, p):
        key = (x, p)
        if key in self._eq: return self._eq[key]
        self._eq[key] = (True, '')    # optimiste sur les cycles
        why = ''
        e5, e9 = E5.get(x), E9.get(p)
        ok = e5 is not None and e9 is not None and (e5 - x) == (e9 - p)
        if ok:
            L5, L9 = ins(b5, x, e5), ins(b9, p, e9)
            nw = lambda w: (w & 0xFC000000) if (w >> 26) in (2, 3) else ((w & 0xFFFF0000) if (w >> 26) in (0x0f, 0x09, 0x0d) else w)
            ok = all(nw(a.w) == nw(b.w) for a, b in zip(L5, L9))
        if not ok: why = 'forme'
        if ok:
            c5 = {k: (t, v) for k, t, v in consts(L5)}; c9 = {k: (t, v) for k, t, v in consts(L9)}
            for k, (t, v) in c5.items():
                if k not in c9: ok = False; break
                w = c9[k][1]; cl = GR.classe_valeur(v, GR.H5) if t == 'c' else 'code'
                if t == 'jal' and not (GR.BASE + 0x22B00 <= v < GR.BASE + GR.H5['code_end']):
                    if v != w: ok = False; why = 'externe'; break
                    continue
                if cl == 'code':
                    f = v - BASE
                    if v in GR.AIDES: ok = GR.AIDES[v] == w
                    elif f in E5:
                        d = self.decide(f, peek=True)
                        ok = d is not None and d[0] in ('HYPER', 'NATIF') and isinstance(d[1], int) and d[1] + BASE == w
                    else: ok = False
                    if not ok: why = 'code'
                elif cl == 'data':
                    import verifie_reutil as VR
                    n_ = min(64, etendue(v))
                    ok = GR.classe_valeur(w, GR.H9) == 'data' and VR.masque(b5, v - BASE, n_) == VR.masque(b9, w - BASE, n_)
                    if not ok: why = 'donnee'
                    if ok:                     # pointeurs de code de la table : memes decisions (entree par entree)
                        for i_, q_ in ptrs_code(v):
                            if i_ >= 0x400: break
                            w_ = struct.unpack_from('<I', b9, w - BASE + i_)[0]
                            d_ = self.decide(q_, peek=True)
                            if not (d_[0] in ('HYPER', 'NATIF') and isinstance(d_[1], int) and d_[1] + BASE == w_): ok = False; why = 'table'; break
                elif cl in ('ram', 'port'):
                    g = GR.Greffe([], a5=lambda d: RA5.get(d, d)); nv = g.valeur(v, 0); ok = nv == w
                    if not ok: why = 'ram'
                if not ok: break
            # deplacements A5 reloges -> pas equivalent
            if ok:
                r7 = set(); a5r = set()
                for x_ in L5:
                    if x_.m == 'lui': (r7.add if x_.imm == 0x7000 else r7.discard)(x_.rt); a5r.discard(x_.rt); continue
                    if x_.m == 'lw' and x_.rs in r7 and x_.imm == 0x1114: a5r.add(x_.rt); continue
                    if (x_.m in GR.MEM or x_.m == 'addiu') and x_.rs in a5r and RA5.get(x_.imm, x_.imm) != x_.imm: ok = False; why = 'a5'; break
                    d = GR.dest(x_)
                    if d is not None: a5r.discard(d); r7.discard(d)
        self._eq[key] = (ok, why)
        return ok, why

    def decide(self, x, peek=False):
        if x in self.dec: return self.dec[x]
        if x in self.force:
            d = self.force[x]; r = 'impose'
        else:
            d, r = self._regle(x)
        if not peek or d[0] != 'GREFFE':
            pass
        self.dec[x] = d; self.raison[x] = r
        return d

    def _regle(self, x):
        i = GR.INV.get(x, {}); p = homologue(x)
        if est_natif5(x):
            if p is not None and p in natifs9() and native_at(b9, p, GR.H9): return ('NATIF', p), 'b) natif homologue'
            return ('NATIF', None), 'b) natif sans homologue natif (talon)'
        c = CK.get(x, 1.0)
        if c < 0.5 or p is None: return ('GREFFE',), 'c) absente d\'Hyper' if c < 0.5 else 'c) sans homologue'
        if x not in BY and x not in TRI and x not in COURTES: return ('HYPER', p), 'j) non vue en Arcade : homologue'
        if x in TRI:
            t = TRI[x]['dec']
            if t == 'HYPER': return ('HYPER', TRI[x]['p']), 'd) tri : HYPER'
            return ('GREFFE',), 'd) tri : ' + t
        ok, why = self.equivalent(x, p)
        if ok: return ('HYPER', p), 'e) equivalente'
        z = BA['zone'].get(x, '?')
        if _ratio(x, p) < 0.8: return ('GREFFE',), 'h) vue en Arcade, homologue douteux (%s)' % why
        if E5[x] - x < 256: return ('GREFFE',), 'h) vue en Arcade, petite routine non equivalente (%s)' % why
        if z.startswith(('code des persos', 'moteur de combat')): return ('HYPER', p), 'f) moteur/persos'
        l = BY.get(x)
        if l is not None and l['vs'] and why == 'code' and not z.startswith(('flux de jeu', 'selection', 'intro/attraction')):
            return ('HYPER', p), 'f) service partage avec VERSUS (%s)' % z.split(' ')[0]
        if c < 0.9: return ('HYPER', p), 'g) modifiee hors coeur'
        return ('GREFFE',), 'h) vue en Arcade, non equivalente (%s)' % why

def ferme(racines, force=None, max_n=5000):
    P = Plan(force)
    todo = []
    for r in racines:
        P.dec[r] = ('GREFFE',); P.raison[r] = 'racine'; todo.append(r)
    vus = set()
    while todo:
        r = todo.pop()
        if r in vus: continue
        vus.add(r)
        for t, v, va in refs_routine(r):
            if t == 'code':
                f = v if v in E5 else routine_de(v)
                P.refs.add(f)
                if f != v: P.journal['code_milieu'].append((va, v, f))
                d = P.decide(f)
                P.parent.setdefault(f, (r, 'appel'))
                if d[0] == 'GREFFE' and f not in vus: todo.append(f)
            else:
                P.donnees.add(v)
                for i, q in ptrs_code(v):
                    P.refs.add(q)
                    d = P.decide(q)
                    P.parent.setdefault(q, (r, 'table 0x%X' % v))
                    if d[0] == 'GREFFE' and q not in vus: todo.append(q)
        if len(vus) > max_n: break
    P.greffe = sorted(f for f in vus if P.dec[f][0] == 'GREFFE')
    P.atteint = vus
    return P

def resume(P):
    c = collections.Counter(P.raison[f] for f in P.dec if f in P.refs or f in P.atteint)
    t = sum(E5[f] - f for f in P.greffe)
    out = ["routines greffees : %d (%d o MIPS, %.1f Ko)" % (len(P.greffe), t, t / 1024)]
    for k, v in sorted(c.items()): out.append("  %-45s %d" % (k, v))
    out.append("constantes de donnees visees : %d" % len(P.donnees))
    return "\n".join(out)

if __name__ == "__main__":
    rs = [int(x, 16) for x in sys.argv[1:]] or [0x4E1C0, 0x24EA30, 0x261560]
    import force as FO
    P = ferme(rs, FO.FORCE)
    print(resume(P))

# ---------------------------------------------------------------------------------------------------------------
# TABLES DE CODE A COMPLETER (types d'objets...) : tables homologues Upper <-> Hyper (constantes de donnees appariees
# par l'alignement des routines) ; une entree NULLE chez Hyper face a un gestionnaire d'Upper execute en Arcade est un
# objet retire par Hyper (attraction, ecrans Arcade). Elle recoit la copie greffee du gestionnaire : le VERSUS
# d'Hyper ne cree jamais ce type (l'entree nulle l'aurait fait planter).
@functools.lru_cache(None)
def refs_donnees9():
    out = set(); lu = {}
    for x in C.instrs('ro9'):
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if x.m in ('addiu', 'ori') and x.rs in lu:
            v = (lu[x.rs] | x.imm) if x.m == 'ori' else (lu[x.rs] + x.simm) & 0xffffffff
            if GR.classe_valeur(v, GR.H9) == 'data': out.add(v)
        d = GR.dest(x)
        if d is not None: lu.pop(d, None)
    return sorted(out)

def table_longs(b, v, refs, n0):
    """longs d'une table [v, table suivante referencee), au plus n0 entrees"""
    k = bisect.bisect_right(refs, v); fin = refs[k] if k < len(refs) else v + 4 * n0
    n = min(n0, (fin - v) // 4)
    return [struct.unpack_from('<I', b, v - BASE + 4 * i)[0] for i in range(max(n, 0))]

def tables_a_completer(routines_arcade=None):
    """[(exec9 de l'entree, gestionnaire Upper, table Upper, table Hyper, indice)]"""
    out = []
    for d5, cand in HOMDT.items():
      for d9 in sorted(cand, key=lambda x: -cand[x]):
        if d5 & 3 or d9 & 3: continue
        t5 = table_longs(b5, d5, refs_donnees5(), 256); t9 = table_longs(b9, d9, refs_donnees9(), 256)
        if len(t5) < 2 or len(t5) != len(t9): continue
        # memes gestionnaires aux entrees non nulles des deux cotes (au moins la moitie homologues) : meme table
        com = [(u, h) for u, h in zip(t5, t9) if u and h]
        if not com or sum(1 for u, h in com if homologue(u - BASE) == h - BASE or _ratio(u - BASE, h - BASE) > 0.9) * 2 < len(com): continue
        if not all(x == 0 or GR.classe_valeur(x, GR.H5) == 'code' for x in t5): continue
        if not all(x == 0 or GR.classe_valeur(x, GR.H9) == 'code' for x in t9): continue
        for i, (u, h) in enumerate(zip(t5, t9)):
            if h == 0 and u != 0 and (u - BASE) in E5 and (u - BASE) in BY and \
               not all(sc.startswith('hors partie') for sc in BY[u - BASE]['scenes']):
                out.append((d9 + 4 * i, u - BASE, d5, d9, i))
        break
    return out
