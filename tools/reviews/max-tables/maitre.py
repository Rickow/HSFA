#!/usr/bin/env python3
"""maitre.py -- max-tables tracer, merge: fuse the nets into TABLES.tsv, one line per table of the graft build indexed
by a character id (side: copy of Upper / Hyper table read by copies / Hyper / stub; Upper address, Hyper homologue,
shape, coverage of the MAX ids $26 $27 $28 $29 $2D $2E, readers, index, value in Upper MAX, what to set, risk, ...).
Manual corrections and notes: notes.py (keys = table address in the build).

Usage:  nice -n 19 python3 -I maitre.py [frozen_build]     (about 15 s)
Inputs: frozen build (argument or $HSFA_GRAFT_BUILD), module ro5, $HSFA_UM_BANC/{max_agrandies.txt,ext_e80000.bin},
        tools/integration-max/upper/untranspile/agrandit_max.py of the repository (entry counts),
        $HSFA_HYPER_INDEX/{tables_homologues,scan_tables102,tables_102}.json. See paths.py.
Output: $HSFA_REVIEW_OUT/TABLES.tsv and maitre.pkl; counts on stdout.
Recipe of the review (12/11, ro9a37): croise_upper_max.py then maitre.py; result kept as TABLES.tsv in the reports.
"""
import sys, os, struct, bisect, collections, pickle, json, re
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import lib_idx as L
try: from notes import NOTES, RETIRER, AJOUTS
except ImportError: NOTES, RETIRER, AJOUTS = {}, set(), []
X = L.charge(sys.argv[1] if len(sys.argv) > 1 else None); A5, A9 = X.A5, X.A9; BASE = L.BASE
IDS = (0x26, 0x27, 0x28, 0x29, 0x2D, 0x2E)
AGENT = {0x74C358, 0x617290, 0x61BBC0, 0x699408, 0x6993E0, 0x97CA90, 0x6F72B0, 0x978D1C, 0x7251A0, 0x960090, 0x72BDF0, 0x616850,
         0x674C00, 0x967F2A, 0x648BC8}          # X2_LISTE de greffe3.py (e48, 12/11 11 h 50), en adresses d'Upper
# ---------------------------------------------------------------- Upper MAX
UM = {}
for l in open(paths.banc_um("max_agrandies.txt"), encoding="utf-8"):
    q = l.split(None, 7)
    if q[0] == 'ps2': continue
    UM[int(q[0], 16)] = dict(u=int(q[0], 16), genre=q[1], e=int(q[2]), cmax=int(q[3], 16), tcopie=int(q[4]), role=q[7].strip() if len(q) > 7 else '', n=40, rangs=1)
ext = open(paths.banc_um("ext_e80000.bin"), "rb").read()
src = open(os.path.join(paths.DEPOT, "tools", "integration-max", "upper", "untranspile", "agrandit_max.py"), encoding="utf-8").read()
for m in re.finditer(r"\(0x([0-9A-F]{6}), (\d+), (\d+), \"", src):
    u = int(m.group(1), 16)
    if u in UM: UM[u]['n'] = int(m.group(3))
for u, t in UM.items():
    if t['genre'] == 'simple': t['rangs'] = max(1, t['tcopie'] // (48 * t['e']))
PLUS = [(0x6F72B0, 'rel16', 2, "palettes par perso (Upper MAX : table deplacee a part, 40 blocs)"), (0x700540, 'rel16', 2, "palettes d'effets (Upper MAX : deplacee a part)"),
        (0x60D070, 'simple', 4, "classes d'effets, index = type d'objet (Upper MAX : deplacee, 64 entrees)"), (0x61B4A0, 'simple', 1, "reactions : table d'animation (Upper MAX : MAX_ANIM_REACTIONS)"),
        (0x628320, 'simple', 4, "natif : banque de sprites par perso"), (0x628370, 'simple', 4, "natif : portrait X_DATA"), (0x628470, 'simple', 4, "natif : fichiers de pose"),
        (0x61BFB0, 'simple', 1, "grille de selection d'Upper (64 cases -> id)"), (0x61BE70, 'simple', 1, "positions du curseur (deja 48 entrees)"),
        (0x97A20C, 'rel16', 2, "parcours Arcade alternatif (aucun lecteur dans Upper)"), (0x61B580, 'simple', 1, "scenarios de dialogue speciaux, 3 x 40"),
        (0x61B600, 'simple', 1, "scenarios de dialogue speciaux (2)"), (0x620630, 'simple', 2, "aiguillage EN LIGNE dans le code (40 mots apres un JMP ; Upper MAX : talon)")]
for u, g, e, r in PLUS:
    if u not in UM: UM[u] = dict(u=u, genre=g, e=e, cmax=0, tcopie=0, role=r, n=64 if u == 0x61BFB0 else 48 if u == 0x61BE70 else 40, rangs=3 if u == 0x61B580 else 1)
US = sorted(UM)
def lg_u(u):
    t = UM[u]
    f = u + (t['n'] * t['e'] * t['rangs'] if t['genre'] == 'simple' else 0x50 if t['genre'] in ('rel16', '967bf0') else 0x10)
    k = bisect.bisect_right(US, u)
    if k < len(US) and f > US[k]: f = US[k]
    return f - u
def lit5(a, n): return X.b5[a - BASE:a - BASE + n]
def lit9(a, n):
    u = X.vers_upper(a)
    if u is not None: return lit5(u, n)
    return X.b9[a - BASE:a - BASE + n]
# ---------------------------------------------------------------- homologues combat (agent_hyper_index)
HOMC = {}
for t in json.load(open(paths.index_hyper('tables_homologues.json'), encoding='utf-8')):
    if t.get('ro9') and t.get('ro5'): HOMC[int(t['ro5'], 16) + BASE] = int(t['ro9'], 16)
HI = {int(k, 16): v for k, v in json.load(open(paths.index_hyper('scan_tables102.json'), encoding='utf-8')).items()}
H102 = {int(t['table'], 16): t for t in json.load(open(paths.index_hyper('tables_102.json'), encoding='utf-8'))['tables']}
# ---------------------------------------------------------------- acces
acc9 = collections.defaultdict(list)
for a in A9.acc: acc9[a[1]].append(a)
C9 = sorted(set(acc9) | set(A9.csite))
def sites9(base, lg):
    """{site: [acces]} des sites de ro9a37 qui construisent une adresse de [base, base+lg) ou y accedent"""
    out = collections.defaultdict(list)
    i = bisect.bisect_left(C9, base)
    while i < len(C9) and C9[i] < base + lg:
        c = C9[i]; i += 1
        for o in A9.csite.get(c, ()): out[o]
        for a in acc9.get(c, ()): out[a[0]].append(a)
    return out
ID_F = {0x102: 'id etendu $102', 0x116: 'perso de base $116'}
DER = {(0x3b, 'S'): "proprietaire d'objet $3A (68K)", (0x7f, 'S'): "id d'objet $7E (68K)", (0x133, 'A5'): 'gagnant $132(A5)', (0x132, 'A5'): '$133(A5)',
       (0x146, 'A5'): '$147(A5) (id copie)', (0x145, 'A5'): '$144(A5)', (0x1c8, 'A5'): 'numero de fin $1C9(A5)', (0x160, 'S'): '$161 du joueur (id precedent)',
       (0xc30f, 'A5'): 'choix J1 $C30E(A5)', (0xc30e, 'A5'): 'choix J2 $C30F(A5)', (0x5f, 'S'): '$5E (id recopie)', (0x121, 'A5'): '$120(A5)'}
def type_idx(accs):
    ty = set(); sg = []
    for a in accs:
        d = L.signature(a[4])[0]; s = "%s+%x[%s]" % ('.bwl'[a[3]] if a[3] < 3 else 'l', a[2], d[:70])
        if s not in sg: sg.append(s)
        for f in L.feuilles(a[4]):
            if f[1] != 1: continue
            if f[0] in ID_F and f[2] != 'A5': ty.add(ID_F[f[0]])
            else:
                k = (f[0], 'A5' if f[2] == 'A5' else 'S')
                if k in DER: ty.add(DER[k])
        d2 = d.replace(' ', '')
        if '[A5+#$1c8]' in d2: ty.add(DER[(0x1c8, 'A5')])
    return ty, sg
def fmt_val(b, e):
    if e == 1: return '%02x' % b[0]
    if e == 2: return '%04x' % struct.unpack('<H', b[:2])[0]
    if e == 4: return '%08x' % struct.unpack('<I', b[:4])[0]
    return b[:8][::-1].hex() if e == 8 else b[:6].hex() + '..'
def val_um(o, e, i):
    """valeur de l'entree i d'une table agrandie d'Upper MAX. ext_e80000.bin = image 68K = donnees PS2 echangees par
    paires : octet PS2 i a la position i ^ 1, mot PS2 = mot big-endian du fichier, long PS2 = (mot 1 << 16) | mot 0 ;
    les tables de CODE relogees (etape B) portent une adresse 68K en long big-endian (marquee « 68K: »)"""
    if e == 1: return '%02x' % ext[o + (i ^ 1)]
    b = ext[o + e * i:o + e * i + e]
    w = struct.unpack('>%dH' % (min(e, 8) // 2), b[:min(e, 8)])
    if e == 2: return '%04x' % w[0]
    if e == 4:
        v = (w[1] << 16) | w[0]; c = (w[0] << 16) | w[1]
        return '%08x' % v if v < 0x2000000 or c >= 0x1000000 else '68K:%06x' % c
    return '.'.join('%04x' % x for x in w)
def est_ptr(v): return 0x200000 <= v < 0x1600000

def regles(r, k, e, n, cop, hyp):
    """a_mettre / risque / confiance par regles (corrigees a la main par notes.py)"""
    g = r['genre']; um = [UM[u] for u in sorted(r['upper']) if u in UM]
    simple = g.startswith('simple')
    hors26 = simple and n <= 0x26; hors2d = simple and n <= 0x2D
    ptr = False
    if simple and e == 4:
        vv = struct.unpack('<%dI' % min(n, 40), lit9(k, 4 * min(n, 40))); ptr = sum(1 for v in vv if v == 0 or 0x212b00 <= v < 0x1600000) >= 0.9 * len(vv) and sum(1 for v in vv if v) >= len(vv) // 2 and len({v >> 16 for v in vv}) < 30 and not any(v >> 24 for v in vv)
    # a mettre
    if r.get('vmax'):
        if 'bloc Upper MAX' in r['vmax']: m = "blocs MAX d'Upper MAX (integre_max.py : ajout / bloc_rel16) reloges ; a defaut l'entree $00"
        elif 'traitee a part' in r['vmax']: m = "comme Upper MAX (table refaite a part : voir max_journal.txt) ; a defaut l'entree $00"
        else:
            vals = r['vmax'].split(' | ')[0]; ryu = vals.split('[Ryu:')[1].rstrip(']'); q = [x.split(':')[1] for x in vals.split(' [')[0].split()]
            if all(x == ryu for x in q): m = "neutre : entree $00 (Upper MAX n'y pose rien de propre)"
            elif ptr: m = "valeurs d'Upper MAX = POINTEURS vers ses blocs MAX (code / donnees a greffer et a reloger) ; a defaut l'entree $00"
            else: m = "valeurs d'Upper MAX (colonne valeur_upper_max)"
    elif simple and n >= 128: m = "entrees $26 / $27 / $2D / $2E presentes (remplissage) : y poser la valeur du perso MAX ; a decider (pas d'equivalent direct dans Upper MAX)"
    else: m = "a decider (pas d'equivalent dans Upper MAX) ; neutre = entree $00"
    r['mettre'] = m
    # risque
    if g == 'rel16' and r['n'] >= 0x30: ri = "aucun debordement ; decalage de remplissage (bloc de Ryu ou bloc par defaut)"
    elif not simple:
        ri = "plantage ou blocage pour $28-$2F (decalage lu dans le corps de la table)" if g in ('rel16', 'struct', '967bf0') else "aucun par l'id (table non indexee par l'id) ; contenu MAX a ajouter"
    elif n >= 0x30: ri = "aucun debordement ; contenu de remplissage (le perso MAX se comporte comme Ryu ou lit 0)"
    elif hors2d or n <= 0x2E:
        z = lit9(k + e * n, e * (0x30 - n)); nul = not any(z)
        if ptr: ri = "PLANTAGE probable pour %s (pointeur lu hors table%s)" % ('$28-$2F' if n <= 0x28 else '$%02X-$2F' % n, ' : nul' if nul else '')
        elif nul: ri = "pas de plantage : 0 lu hors table (zeros) au lieu de la valeur du perso"
        else: ri = "valeur fausse hors table (visuel / comportement ; plantage possible si elle sert d'index ou de decalage)"
    else: ri = ''
    if r['rangs'] > 1 and simple and n < 0x30: ri = "rangee suivante lue pour $28-$2F (valeur d'un autre perso) ; constante de rangee $%X a passer a $%X" % (n * e, 0x30 * e)
    r['risque'] = ri
    s = r['src']; nb = len({x.split('-')[0] for x in s} & {'UM', 'HI', 'H102', 'scan'})
    r['confiance'] = 'sur' if ('UM' in s or 'UM-hom' in s) and (cop or hyp) else 'sur' if nb >= 2 else 'a confirmer' if s == {'scan-derive'} else 'probable'
rows = {}
def row(k):
    if k not in rows: rows[k] = dict(cle=k, cote='', upper=set(), hyper=None, genre='', e=0, n=0, rangs=1, role=[], src=set(), note='')
    return rows[k]
# 1. tables d'Upper MAX
for u in US:
    t = UM[u]; lg = lg_u(u)
    cp = X.vers_copie(u); hy = X.reut.get(u) or X.hom.get(u) or HOMC.get(u)
    if cp:
        S = sites9(cp, lg)
        if any(X.cote(o) in 'CT' for o in S):
            r = row(cp); r['cote'] = 'COPIE'; r['upper'].add(u); r['hyper'] = hy; r.update(genre=t['genre'], e=t['e'], n=t['n'], rangs=t['rangs']); r['role'].append(t['role']); r['src'].add('UM')
    if hy:
        r = row(hy); r['upper'].add(u); r['src'].add('UM-hom')
        if not r['genre']: r.update(genre=t['genre'], e=t['e'], n=t['n'], rangs=t['rangs'])
        if t['role'] not in r['role']: r['role'].append(t['role'])
        if not r['cote']: r['cote'] = 'HYPER'
    if not cp and not hy: r = row(-u); r['cote'] = 'ABSENTE'; r['upper'].add(u); r.update(genre=t['genre'], e=t['e'], n=t['n'], rangs=t['rangs']); r['role'].append(t['role']); r['src'].add('UM')
# 2. index d'Hyper
for a, t in H102.items():
    r = row(a); r['src'].add('H102'); r['cote'] = r['cote'] or 'HYPER'
    if r['genre'] in ('', 'simple'): r.update(genre='simple', e=t['element'], n=t['entrees'], rangs=1)
    r['n_h'] = t['entrees']; r['e_h'] = t['element']
    if t['role'] not in r['role']: r['role'].append(t['role'])
for a, t in HI.items():
    r = row(a); r['src'].add('HI'); r['cote'] = r['cote'] or 'HYPER'
    r['hi_index'] = ','.join(t['index']); r['ecart'] = t.get('ecart_suivante')
# 3. balayage symbolique : feuilles $102 / $116 (toute table), champs derives (table >= 40 entrees seulement)
Cs = sorted(A9.consts | set(X.reut.values()))
def ecart(c):
    k = bisect.bisect_right(Cs, c); return Cs[k] - c if k < len(Cs) else 0
for c, accs in acc9.items():
    ty, sg = type_idx(accs)
    direct = any(f[0] in ID_F and f[1] == 1 and f[2] != 'A5' for a in accs for f in L.feuilles(a[4]))
    if not ty: continue
    # deja couverte par une ligne (dans la plage d'une table connue) ?
    dans = None
    for k, r in rows.items():
        if k > 0 and k <= c < k + max(1, r['e'] * r['n'] * r['rangs'] if r['genre'] == 'simple' else 0x50): dans = k; break
    if dans: rows[dans]['src'].add('scan'); continue
    if not direct:
        pas = max(1, min(a[3] for a in accs))
        if ecart(c) < 0x28: continue                    # table de moins de 40 octets : pas une table par perso
    r = row(c); r['src'].add('scan' if direct else 'scan-derive'); u = X.vers_upper(c)
    r['cote'] = r['cote'] or ('COPIE' if u else 'HYPER')
    if u: r['upper'].add(u)
    r['ecart'] = ecart(c)
for k, v in AJOUTS: 
    r = row(k); r.update(v); r['src'].add('greffe3.py' if v['cote'] == 'TALON' else 'entetes')
# ---------------------------------------------------------------- lignes
out = []
for k in sorted(rows):
    if k in RETIRER: continue
    r = rows[k]
    if k < 0:
        out.append(r); r.update(lect_c='', lect_h='', index='', type_id='', couverture='pas de copie ni d\'homologue connu dans ro9a37', lu='', vmax='', mettre='', risque='', agent=''); continue
    lg = max(4, r['e'] * r['n'] * r['rangs']) if r['genre'] == 'simple' and r['e'] else (r.get('ecart') or 0x50)
    if r['genre'] in ('rel16', 'struct', 'rel16n', '967bf0'): lg = 0x50
    S = sites9(k, lg)
    lc = sorted(o for o in S if X.cote(o) == 'C'); lt = sorted(o for o in S if X.cote(o) == 'T'); lh = sorted(o for o in S if X.cote(o) == 'H')
    accs = [a for o in S for a in S[o]]
    ty, sg = type_idx(accs)
    if r.get('hi_index'): 
        for x in r['hi_index'].split(','):
            if x.startswith('0102'): ty.add(ID_F[0x102])
            if x.startswith('0116'): ty.add(ID_F[0x116])
    if 'H102' in r['src']: ty.add(ID_F[0x102])
    if lc and lh and r['cote'] == 'HYPER': r['cote'] = 'HYPER partagee'
    if lc and not lh and r['cote'] == 'HYPER': r['cote'] = 'HYPER lue par les copies'
    r['lect_c'] = ' '.join(sorted({'%x<-U%x' % (o, X.origine(o)) for o in lc if S[o]} or {'%x<-U%x' % (o, X.origine(o)) for o in lc})) + (' ; talons ' + ' '.join('%x' % o for o in lt) if lt else '')
    r['lect_h'] = ' '.join(sorted({'%x' % o for o in lh if S[o]} or {'%x' % o for o in lh}))
    r['index'] = ' ; '.join(sg[:4]); r['type_id'] = ' / '.join(sorted(ty))
    e = r['e'] or (min(a[3] for a in accs) if accs else 1); n = r['n'] or ((r.get('ecart') or 0) // e)
    if not r['e']: r['e'] = e; r['n'] = n; r['genre'] = r['genre'] or 'simple ?'
    # valeurs lues aujourd'hui aux ids MAX (rangee 0)
    lu = []; nb_hors = 0
    if r['genre'].startswith('simple') and e in (1, 2, 4, 6, 8):
        for i in IDS:
            v = fmt_val(lit9(k + e * i, e), e)
            hors = i >= n
            nb_hors += hors
            lu.append('$%02X:%s%s' % (i, v, '(HORS)' if hors else ''))
    elif r['genre'] in ('rel16', 'struct', '967bf0'):
        for i in IDS:
            v = struct.unpack('<H', lit9(k + 2 * i, 2))[0]
            lu.append('$%02X:%04x%s' % (i, v, '(HORS)' if i >= 40 and r['genre'] == 'rel16' else ''))
    r['lu'] = ' '.join(lu)
    if r['genre'].startswith('simple'):
        z = lit9(k + e * 40, e * 8) if n <= 40 else b''
        suite = 'zeros' if z and not any(z) else 'autres donnees' if z else ''
        r['couverture'] = "%d entree(s) x %d o%s ; $26-$27 %s ; $28-$2F %s" % (n, e, (' x %d rangees' % r['rangs']) if r['rangs'] > 1 else '', 'DANS' if n > 0x27 else 'HORS', 'DANS' if n >= 0x30 else ('HORS, suite = ' + suite) if n <= 40 else 'HORS a partir de $%02X' % n)
    elif r['genre'] == 'rel16':
        h0 = struct.unpack('<H', lit9(k, 2))[0] // 2; r['n'] = h0
        r['couverture'] = "en-tete de %d decalages u16 relatifs + corps ; $26-$27 %s ; $28-$2F %s" % (h0, 'DANS' if h0 > 0x27 else 'HORS', 'DANS' if h0 >= 0x30 else 'HORS (corps de la table)')
        r['lu'] = r['lu'].replace('(HORS)', '') if h0 >= 0x30 else r['lu']
    else: r['couverture'] = {'rel16': "en-tete de 40 decalages u16 relatifs + corps", 'struct': "structure a en-tete de decalages + listes de 40 x 8 o", 'rel16n': "en-tete de N decalages, index NON id (entrees MAX ajoutees a la suite dans Upper MAX)", '967bf0': "structure a rangees ($30 mots x2, $D0 octets x2)"}.get(r['genre'], r['genre'])
    # Upper MAX
    vm = []
    for u in sorted(r['upper']):
        t = UM.get(u)
        if t and t['cmax'] and t['genre'] == 'simple':
            o = t['cmax'] - 0xE80000
            vm.append(' '.join('$%02X:%s' % (i, val_um(o, t['e'], i)) for i in (0x26, 0x27, 0x2D, 0x2E)) + (' [Ryu:%s]' % val_um(o, t['e'], 0)))
        elif t and t['cmax']: vm.append("bloc Upper MAX $%X (%d o) : en-tete 48 + blocs MAX" % (t['cmax'], t['tcopie']))
        elif t: vm.append("traitee a part dans Upper MAX")
    r['vmax'] = ' | '.join(vm)
    r['agent'] = 'oui' if (r['upper'] & AGENT) and (lc or lt) else ''
    r['mettre'] = ''; r['risque'] = ''
    regles(r, k, e, n, lc or lt, lh)
    if r.get('fixe'): r.update(r['fixe'])
    out.append(r)
for r in out:
    nt = NOTES.get(r['cle'] if r['cle'] > 0 else -r['cle'])
    if nt: r.update(nt)
cols = ['table_ro9a37', 'cote', 'upper_ro5', 'hom_hyper', 'forme', 'couverture_ids_MAX', 'lecteurs_copies', 'lecteurs_hyper', 'index', 'type_id', 'lu_aujourdhui', 'valeur_upper_max', 'a_mettre', 'risque', 'agent_ro9a38', 'role', 'sources', 'confiance', 'note']
with open(paths.sorties('TABLES.tsv'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\t'.join(cols) + '\n')
    for r in out:
        k = r['cle']
        f.write('\t'.join([('T_%06x' % k) if k > 0 else '-', r['cote'], ' '.join('%06x' % u for u in sorted(r['upper'])), ('%06x' % r['hyper']) if r.get('hyper') else '',
                           r.get('forme') or "%s e=%d n=%s%d%s" % (r['genre'], r['e'], '<=' if r['genre'].endswith('?') else '', r['n'], (' x%d' % r['rangs']) if r['rangs'] > 1 else ''), r.get('couverture', ''), r.get('lect_c', ''), r.get('lect_h', ''), r.get('index', ''),
                           r.get('type_id', ''), r.get('lu', ''), r.get('vmax', ''), r.get('mettre', ''), r.get('risque', ''), r.get('agent', ''), ' // '.join(r['role'])[:160], ','.join(sorted(r['src'])), r.get('confiance', ''), r.get('note', '') if isinstance(r.get('note'), str) else '']) + '\n')
pickle.dump(out, open(paths.sorties('maitre.pkl'), 'wb'))
print(len(out), collections.Counter(r['cote'] for r in out))
