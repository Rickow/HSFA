#!/usr/bin/env python3
"""TRI DES ROUTINES MODIFIEES DU COEUR (etape 2, point 1) : diff par branche entre la routine d'Upper et son homologue
d'Hyper, puis decision : garder l'homologue d'Hyper, copier la routine d'Upper (greffe), ou retoucher.

Methode :
  - homologue = paire propagee (etape2/homologues.py, majoritaire) sinon partenaire d'inverse_ro5 ;
  - alignement des instructions MIPS (difflib ; cibles et moities hautes masquees, deplacements gardes) ;
  - marqueurs des instructions NON alignees, de chaque cote :
      ARCADE (cote Upper)  : variable A5 propre a Upper (table de relogement : pas « commun »), appel d'une routine
                             absente d'Hyper, constante de donnees propre a Upper (a copier) ;
      VERSION (cote Hyper) : champ $D2/$D3 (versions), $116/$117 (perso de base), variable A5 propre a Hyper, appel
                             d'une routine propre a Hyper ;
      $102 (cote Upper)    : lecture du champ $102 (a passer par $116 en cas de copie).
  - decision : pas de marqueur ARCADE -> HYPER ; ARCADE sans VERSION -> COPIE ; les deux -> MIXTE (copie + $116, ou
    retouche a la main de la routine d'Hyper).
Sortie : donnees/tri_modifiees.tsv, donnees/tri_modifiees.pkl {va5: dict(...)}, resume a l'ecran."""
import os, sys, struct, pickle, collections, difflib
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/greffe_arcade/outils"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import greffe as GR
import commun as C
from mips import Ins
G = GR.G; BASE = GR.BASE
b5, b9 = C.load('ro5'), C.load('ro9')
E5 = dict(C.funcs('ro5')); E9 = dict(C.funcs('ro9'))
HOM = pickle.load(open(os.path.join(G, 'donnees', 'homologues.pkl'), 'rb'))['code']
RA5 = pickle.load(open(os.path.join(G, 'donnees', 'relogement_a5.pkl'), 'rb'))
NAT_A5 = {l[0]: l[6] for l in RA5['lignes']}
A5P = pickle.load(open(os.path.join(GR.EU, 'a5.pkl'), 'rb'))
D5, D9 = set(A5P['D5']), set(A5P['D9'])
CK = pickle.load(open(os.path.join(GR.EU, 'couv_k.pkl'), 'rb'))          # couverture d'Upper par Hyper
CK9 = pickle.load(open(os.path.join(GR.EU, 'couv_k9.pkl'), 'rb'))        # couverture d'Hyper par Upper
if isinstance(CK9, dict) and 'couv' in CK9: CK9 = CK9['couv']

def homologue(a5):
    import plan as _PL
    p = _PL.homologue(a5); h = HOM.get(a5)
    return p, ('propage' if h and h[0] == p else 'inverse_ro5')

def norm(w):
    op = w >> 26
    if op in (2, 3): return w & 0xFC000000
    if op in (0x0f, 0x09, 0x0d): return w & 0xFFFF0000
    return w

def ins(b, a, e): return [Ins(o, struct.unpack_from('<I', b, o)[0]) for o in range(a, e, 4)]

def analyse(L):
    """par indice : liste de marqueurs ('a5', d) / ('champ', d) / ('jal', cible) / ('c', valeur)"""
    out = collections.defaultdict(list); lu = {}; r7 = set(); a5r = set(); slot = {}
    for k, x in enumerate(L):
        if x.m in ('jal', 'j'): out[k].append(('jal', x.tgt - BASE))
        if x.m == 'lui':
            lu[x.rt] = x.imm << 16; (r7.add if x.imm == 0x7000 else r7.discard)(x.rt); a5r.discard(x.rt); slot.pop(x.rt, None); continue
        if x.m == 'lw' and x.rs in r7 and x.imm == 0x1114:
            a5r.add(x.rt); r7.discard(x.rt); lu.pop(x.rt, None); continue
        if x.m == 'lw' and x.rs in r7 and 0x1100 <= x.imm < 0x1120:   # registre An du banc (A0..A7)
            slot[x.rt] = x.imm; r7.discard(x.rt); lu.pop(x.rt, None); continue
        if (x.m in GR.MEM or x.m == 'addiu') and x.rs in a5r:
            out[k].append(('a5', x.imm))
        elif (x.m in GR.MEM) and x.rs in slot:
            out[k].append(('champ', x.imm))
        elif (x.m in GR.MEM or x.m in ('addiu', 'ori')) and x.rs in lu and x.rs not in r7:
            v = (lu[x.rs] | x.imm) if x.m == 'ori' else (lu[x.rs] + x.simm) & 0xffffffff
            out[k].append(('c', v))
        d = GR.dest(x)
        if d is not None: lu.pop(d, None); a5r.discard(d); r7.discard(d); slot.pop(d, None)
    return out

CORE_ABS = None
def marqueurs(L, idx, cote, absent5):
    m = collections.Counter()
    A = analyse(L)
    for k in idx:
        for t, v in A.get(k, ()):
            if t == 'a5':
                if cote == 'u':
                    nat = NAT_A5.get(v)
                    if v == 0xC200: m['mode $C201'] += 1
                    elif nat and nat != 'commun' and not nat.startswith('champ'): m['A5 propre Upper $%04X' % v] += 1
                    elif nat is None and v not in D9: m['A5 propre Upper $%04X' % v] += 1
                else:
                    if v == 0xC200: m['mode $C201'] += 1
                    elif v not in D5: m['A5 propre Hyper $%04X' % v] += 1
            elif t == 'champ':
                if v in (0x102,) and cote == 'u': m['$102'] += 1
                if cote == 'h' and v in (0xD2, 0x116, 0x117): m['version $%X' % v] += 1
                if cote == 'h' and v == 0x102: m['$102 (Hyper)'] += 1
            elif t == 'jal':
                if cote == 'u' and v in absent5: m['appel absent 0x%X' % v] += 1
                if cote == "h" and CK9.get(v, 1.0) < 0.5: m['appel propre Hyper 0x%X' % v] += 1
            elif t == 'c':
                if cote == 'u' and GR.classe_valeur(v, GR.H5) == 'data' and v in DCOPIE: m['donnee Upper 0x%X' % v] += 1
    return m

SEUIL = 0.8          # ressemblance minimale avec l'homologue pour le garder (en dessous : homologue douteux, copie)
_ABS5 = None
def decide_paire(r, p, detail=False):
    """decision HYPER / COPIE / MIXTE pour la routine d'Upper r et la routine d'Hyper p (marqueurs du diff)"""
    global _ABS5, DCOPIE
    if _ABS5 is None:
        _ABS5 = {x for x, c in CK.items() if c < 0.5}
        Dg = pickle.load(open(os.path.join(G, 'donnees', 'donnees_greffe.pkl'), 'rb')); DCOPIE = {v for v, n, q in Dg['copie']}
    e5 = E5.get(r)
    if p is None or e5 is None or p not in E9: return ('COPIE', 0.0, {}, {}, 0) if detail else 'COPIE'
    L5, L9 = ins(b5, r, e5), ins(b9, p, E9[p])
    sm = difflib.SequenceMatcher(None, [norm(x.w) for x in a5_reloge(L5)], [norm(x.w) for x in L9], autojunk=False)
    iu, ih = [], []; hunks = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                x, y = L5[i1 + k], L9[j1 + k]
                if x.m in ('jal', 'j') and y.m == x.m and homologue(x.tgt - BASE)[0] != y.tgt - BASE:
                    hunks += 1; iu.append(i1 + k); ih.append(j1 + k)
            continue
        hunks += 1; iu += range(i1, i2); ih += range(j1, j2)
    mu = marqueurs(L5, iu, 'u', _ABS5); mh = marqueurs(L9, ih, 'h', _ABS5)
    arc = {k: v for k, v in mu.items() if not k.startswith('$102') and k != 'mode $C201'}
    ver = {k: v for k, v in mh.items() if not k.startswith('$102')}
    if sm.ratio() < SEUIL: dec = 'COPIE'
    elif not arc and not mu.get('mode $C201'): dec = 'HYPER'
    elif not ver: dec = 'COPIE'
    else: dec = 'MIXTE'
    return (dec, sm.ratio(), dict(mu), dict(mh), hunks) if detail else dec

def a5_reloge(L):
    """instructions d'Upper avec les deplacements A5 reloges (table de l'etape 3) : un deplacement deplace par le
    portage d'Hyper ($C392 -> $C3A2...) n'est pas une difference"""
    out = []; r7 = set(); a5r = set()
    RT = RA5['table']
    for x in L:
        w = x.w
        if x.m == 'lui': (r7.add if x.imm == 0x7000 else r7.discard)(x.rt); a5r.discard(x.rt)
        elif x.m == 'lw' and x.rs in r7 and x.imm == 0x1114: a5r.add(x.rt); r7.discard(x.rt)
        elif (x.m in GR.MEM or x.m == 'addiu') and x.rs in a5r:
            nd = RT.get(x.imm)
            if nd is not None and nd != x.imm: w = (w & 0xffff0000) | (nd & 0xffff)
        if x.m not in ('lui',) and not (x.m == 'lw' and x.imm == 0x1114):
            d = GR.dest(x)
            if d is not None: a5r.discard(d); r7.discard(d)
        out.append(Ins(x.va, w))
    return out

def main():
    L = pickle.load(open(os.path.join(G, 'donnees', 'liste_arcade.pkl'), 'rb'))
    core = set(pickle.load(open(os.path.join(G, 'donnees', 'coeur_greffe.pkl'), 'rb')))
    by = {l['r']: l for l in L['lignes']}
    absent5 = {r for r, c in CK.items() if c < 0.5} if isinstance(CK, dict) else set()
    global DCOPIE
    Dg = pickle.load(open(os.path.join(G, 'donnees', 'donnees_greffe.pkl'), 'rb'))
    DCOPIE = {v for v, n, p in Dg['copie']}
    res = {}; cnt = collections.Counter(); tail = collections.Counter()
    proches = {l['r'] for l in L['lignes'] if l['decision'].startswith('garder Hyper (homologue proche') and l['etat'] == 'modifie'}
    for r in sorted(core | proches):
        l = by[r]
        if l['etat'] != 'modifie': continue
        p, src = homologue(r)
        e5 = E5.get(r)
        if p is None or e5 is None or p not in E9:
            res[r] = dict(p=p, src=src, ratio=0, dec='COPIE', raison='pas d\'homologue', mu={}, mh={}, n=0); cnt['COPIE'] += 1; continue
        dec, ratio, mu, mh, hunks = decide_paire(r, p, detail=True)
        res[r] = dict(p=p, src=src, ratio=ratio, dec=dec, mu=mu, mh=mh, n=hunks, taille=l['taille'], vs=l['vs'])
        cnt[dec] += 1; tail[dec] += l['taille']
        continue
        L5, L9 = ins(b5, r, e5), ins(b9, p, E9[p])
        sm = difflib.SequenceMatcher(None, [norm(x.w) for x in L5], [norm(x.w) for x in L9], autojunk=False)
        iu, ih = [], []; hunks = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                # appels alignes mais vers des routines non homologues (cibles masquees par l'alignement)
                for k in range(i2 - i1):
                    x, y = L5[i1 + k], L9[j1 + k]
                    if x.m in ('jal', 'j') and y.m == x.m and homologue(x.tgt - BASE) != y.tgt - BASE:
                        hunks += 1; iu.append(i1 + k); ih.append(j1 + k)
                continue
            hunks += 1; iu += range(i1, i2); ih += range(j1, j2)
        mu = marqueurs(L5, iu, 'u', absent5); mh = marqueurs(L9, ih, 'h', absent5)
        arc = {k: v for k, v in mu.items() if not k.startswith('$102') and k != 'mode $C201'}
        ver = {k: v for k, v in mh.items() if not k.startswith('$102')}
        if sm.ratio() < SEUIL: dec = 'COPIE'                      # homologue peu fiable : pas de « meme routine » chez Hyper
        elif not arc and not mu.get('mode $C201'): dec = 'HYPER'
        elif not ver: dec = 'COPIE'
        else: dec = 'MIXTE'
        res[r] = dict(p=p, src=src, ratio=sm.ratio(), dec=dec, mu=dict(mu), mh=dict(mh), n=hunks, taille=l['taille'], vs=l['vs'])
        cnt[dec] += 1; tail[dec] += l['taille']
    pickle.dump(res, open(os.path.join(G, 'donnees', 'tri_modifiees.pkl'), 'wb'))
    with open(os.path.join(G, 'donnees', 'tri_modifiees.tsv'), 'w') as f:
        f.write("va_ro5\thomologue_ro9\tsource\tratio\tsegments_diff\tdecision\ttaille\tVS\tmarqueurs_Upper\tmarqueurs_Hyper\n")
        for r, d in sorted(res.items()):
            f.write("0x%X\t%s\t%s\t%.2f\t%d\t%s\t%d\t%s\t%s\t%s\n" % (r, ('0x%X' % d['p']) if d['p'] else '', d['src'], d['ratio'], d['n'],
                    d['dec'], by[r]['taille'], 'oui' if by[r]['vs'] else 'non',
                    ' '.join('%s×%d' % kv for kv in sorted(d['mu'].items())), ' '.join('%s×%d' % kv for kv in sorted(d['mh'].items()))))
    print("routines modifiees du coeur (+ %d « homologue proche » vues en Arcade) : %d" % (len(proches), sum(cnt.values())))
    for k in ('HYPER', 'COPIE', 'MIXTE'): print("  %-6s %4d routines %7d o (%.1f Ko)" % (k, cnt[k], tail[k], tail[k] / 1024))

if __name__ == "__main__":
    main()
