#!/usr/bin/env python3
"""croise_upper_max.py -- max-tables tracer, net 1: start from the list of the tables by character ID of Upper MAX
(max_agrandies.txt of an Upper MAX bench, plus the tables moved apart) and find, for each, where it lives in the
frozen graft build (copy of the graft, reused Hyper table, homologue) and who reads it (sites that build its address +
indexed accesses), on the side of Upper's copies (C), stubs (T) and Hyper (H).

Usage:  nice -n 19 python3 -I croise_upper_max.py [frozen_build] > sorties/croise_upper_max.txt
Inputs: frozen build (argument or $HSFA_GRAFT_BUILD), $HSFA_UM_BANC/max_agrandies.txt, module ro5. See paths.py.
Output: stdout, and $HSFA_REVIEW_OUT/croise.pkl (read by feuilles_id.py and scan2.py). Read only otherwise.
"""
import sys, os, struct, bisect, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
X = L.charge(sys.argv[1] if len(sys.argv) > 1 else None)
A5, A9 = X.A5, X.A9
BASE = L.BASE
T = []
for l in open(paths.banc_um("max_agrandies.txt"), encoding="utf-8"):
    q = l.split(None, 7)
    if q[0] == 'ps2': continue
    T.append(dict(u=int(q[0], 16), genre=q[1], e=int(q[2]), tcopie=int(q[4]), role=q[7].strip() if len(q) > 7 else ''))
PLUS = [(0x6F72B0, 'rel16', 2, "palettes par perso (Upper MAX : deplacee a part)"), (0x700540, 'rel16', 2, "palettes d'effets (Upper MAX : deplacee a part)"),
        (0x60D070, 'simple', 4, "classes d'effets (Upper MAX : deplacee, 64 entrees)"), (0x61B4A0, 'simple', 1, "reactions : table d'animation (Upper MAX : MAX_ANIM_REACTIONS)"),
        (0x628320, 'simple', 4, "natif : banque de sprites par perso"), (0x628370, 'simple', 4, "natif : portrait X_DATA"), (0x628470, 'simple', 4, "natif : fichiers de pose"),
        (0x61BFB0, 'simple', 1, "grille de selection (64 cases)"), (0x61BE70, 'simple', 1, "positions du curseur (deja 48)"),
        (0x97A20C, 'rel16', 2, "parcours Arcade alternatif (aucun lecteur dans Upper)"), (0x61B580, 'simple', 1, "scenarios de dialogue speciaux 3 x 40"),
        (0x61B600, 'simple', 1, "idem (2)")]
connu = {t['u'] for t in T}
for u, g, e, r in PLUS:
    if u not in connu: T.append(dict(u=u, genre=g, e=e, tcopie=0, role=r))
T.sort(key=lambda t: t['u'])
US = [t['u'] for t in T]
def fin_u(k):
    t = T[k]; n = t['tcopie'] * 40 // 48 if t['genre'] == 'simple' and t['tcopie'] else 0
    f = t['u'] + (n or 0x28 * t['e'])
    if t['genre'] != 'simple' and t['tcopie']: f = t['u'] + t['tcopie']
    if k + 1 < len(T): f = min(f, T[k + 1]['u']) if f > T[k + 1]['u'] else f
    return f
def routine5(o):
    ks = sorted(X.dec); k = bisect.bisect_right(ks, o) - 1
    return ks[k]
KS = sorted(X.dec)
def dec5(o):
    k = bisect.bisect_right(KS, o) - 1; r = KS[k]; return r, X.dec[r]
acc5 = collections.defaultdict(list); acc9 = collections.defaultdict(list)
for a in A5.acc: acc5[a[1]].append(a)
for a in A9.acc: acc9[a[1]].append(a)
res = []
for k, t in enumerate(T):
    u, f = t['u'], fin_u(k)
    cp = X.vers_copie(u); re = X.reut.get(u); ho = X.hom.get(u)
    print("\n## T_%06x %s e=%d %s | copie %s | reutilisee %s | homologue %s" % (u, t['genre'], t['e'], t['role'][:70], '%x' % cp if cp else '-', '%x' % re if re else '-', '%x' % ho if ho else '-'))
    # Upper : sites de construction de l'adresse et acces
    su = sorted({o for c in A5.csite if u <= c < f for o in A5.csite[c]} | {a[0] for c in acc5 if u <= c < f for a in acc5[c]})
    gre = hyp = 0
    for o in su:
        r, d = dec5(o); c = X.copie(o)
        ac = [a for cc in acc5 if u <= cc < f for a in acc5[cc] if a[0] == o]
        sig = ' ; '.join("%s+%x[%s]" % ('.bwl'[a[3]] if a[3] < 3 else 'l', a[2] + a[1] - u, L.signature(a[4])[0]) for a in ac)
        print("  U %06x rout %06x %-6s %s %s  %s" % (o, r, d[0], ('copie %06x' % c) if c is not None else (d[1] if len(d) > 1 and d[0] == 'HYPER' else ''), d[-1][:30], sig))
        if c is not None: gre += 1
        else: hyp += 1
    # ro9a : sites sur la copie et sur l'homologue
    n9 = collections.Counter()
    for nom, base in (('copie', cp), ('hyper', re or ho)):
        if not base: continue
        lg = f - u
        s9 = sorted({o for c in A9.csite if base <= c < base + lg for o in A9.csite[c]} | {a[0] for c in acc9 if base <= c < base + lg for a in acc9[c]})
        for o in s9:
            ac = [a for cc in acc9 if base <= cc < base + lg for a in acc9[cc] if a[0] == o]
            sig = ' ; '.join("%s+%x[%s]" % ('.bwl'[a[3]] if a[3] < 3 else 'l', a[2] + a[1] - base, L.signature(a[4])[0]) for a in ac)
            og = X.origine(o); n9[(nom, X.cote(o))] += 1
            print("  9 %-5s %s %06x %s %s | %s" % (nom, X.cote(o), o, ('<- U %06x' % og) if og is not None else '', sig, X.t68(o)[:50]))
    res.append(dict(t, fin=f, copie=cp, reut=re, hom=ho, u_gre=gre, u_hyp=hyp, n9=dict(n9)))
    print("  => Upper : %d site(s) greffe(s), %d renvoye(s)/non greffe(s) ; ro9a : %s" % (gre, hyp, dict(n9)))
pickle.dump(res, open(paths.sorties('croise.pkl'), 'wb'))
