#!/usr/bin/env python3
"""Construit symboles_ro3.csv : symboles du journal (extraits _extraits/part*.tsv, corrigés par
corrections.tsv) + symboles automatiques (fonctions, tâches, aiguillages, natifs, moteur), avec les
adresses complétées dans les trois espaces (arcade / mips / traduit).

Conventions de numérotation (vérifiées dans le code, voir SYMBOLES.md) :
  octets : arcade = MIPS (PS2) ; image traduite = XOR 1
  mots   : identiques, sauf moitiés de longs : arcade +$10 (haut) = MIPS/traduit +$12
  zone A5 du portage relogée (table reloc_a5) : variables A5 appariées par vote (paires_a5.json)
"""
import sys, os, re, csv, json, bisect, collections, pickle, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trois, desasm as D, fonctions as F
ICI = os.path.dirname(os.path.abspath(__file__))
RAC = os.path.join(ICI, '..')
CA = os.path.join(RAC, '_cache')
CODE0, CODE1 = 0x22b00, 0x393c40
DATA_TRAD = None                          # base des données dans l'image traduite (fonctions.bornes_trad)
CONF = {'sûr': 3, 'probable': 2, 'hypothèse': 1, '': 0}
GENERIQUE = re.compile(r'^(fonc|routine|var|var_a5|site|fonction|portage_routine|portage_var|natif_[0-9a-f]{4,}|'
                       r'moteur_[0-9a-f]{4,}|objet_champ|joueur_champ|joueur_octet|joueur_mot|objet_octet|objet_mot|'
                       r'objet_long|entrees_00|table_[0-9a-f]{4,}|t_[0-9a-f]{4,})')

def h(v, n=6, p='$'): return '' if v is None else '%s%0*X' % (p, n, v)
def hx(v): return '' if v is None else '0x%X' % v

def lit_int(s):
    s = (s or '').strip().split()[0] if (s or '').strip() else ''
    s = s.rstrip(',;')
    if not s: return None
    neg = s.startswith('-'); s = s.lstrip('-+')
    try:
        v = int(s[1:], 16) if s.startswith('$') else int(s, 16) if s.lower().startswith('0x') else int(s, 16)
    except ValueError: return None
    return -v if neg else v

# ---------------------------------------------------------------- extraits du journal
def lit_extraits():
    rows = []
    for p in sorted(glob.glob(os.path.join(RAC, '_extraits', 'part*.tsv'))):
        for k, l in enumerate(open(p, encoding='utf-8')):
            c = l.rstrip('\n').split('\t')
            if k == 0 or len(c) < 12: continue
            r = dict(zip(['type', 'nom', 'arcade', 'mips', 'trad', 'a5', 'champ', 'taille', 'role', 'source',
                          'confiance', 'note'], [x.strip() for x in c[:12]]))
            r['fichier'] = os.path.basename(p)
            rows.append(r)
    corr = os.path.join(RAC, 'outils', 'corrections.tsv')
    if os.path.exists(corr):
        C = {}
        for l in open(corr, encoding='utf-8'):
            if l.startswith('#') or not l.strip(): continue
            c = l.rstrip('\n').split('\t')
            C[c[0]] = c[1:]
        out = []
        for r in rows:
            act = C.get(r['nom'])
            if act is None: out.append(r); continue
            if act[0] == 'suppr': continue
            for kv in act:
                if '=' in kv:
                    k, v = kv.split('=', 1); r[k] = v
            out.append(r)
        rows = out
    return rows

def est_moteur(r, v):
    return 'moteur' in (r['note'] + r['nom']).lower() and not (CODE0 <= v < CODE1 and 'module' in r['note'])

def main():
    global DATA_TRAD
    DATA_TRAD = F.bornes_trad()[1]
    X = trois.Trois()
    FN = json.load(open(os.path.join(CA, 'fonctions.json')))
    AU = json.load(open(os.path.join(CA, 'auto.json')))
    PA = json.load(open(os.path.join(CA, 'paires_a5.json')))
    natifs = set(int(x, 16) for x in json.load(open('<workspace>/work/carto_ro5/natifs_ro3.json')))
    A = D.desasm('<workspace>/work/cps2/sfa3ud_prog.bin', 0, 0, 0x100000, 'arc')
    aidx = {a: k for k, (a, *_r) in enumerate(A)}
    T = D.desasm(os.path.join(RAC, '_trad.bin'), 0, 0x1000, F.bornes_trad()[0], 'trad')
    # déplacements A5 / A6 réellement employés par l'image traduite (taille comprise)
    usage = {'A5': collections.defaultdict(set), 'A6': collections.defaultdict(set)}
    for a, n, mn, ops in T:
        for s, hh, r in re.findall(r'\((-?)\$([0-9a-f]+),(A[56])\)', ops):
            v = ((-1 if s else 1) * int(hh, 16)) & 0xffff
            usage[r][v].add('B' if (mn.endswith('.b') or mn in D.OCTET) else mn[-1].upper() if '.' in mn else '?')
    # déplacements employés par la ROM arcade (instructions de code alignées seulement)
    usage_arc = {'A5': collections.defaultdict(set), 'A6': collections.defaultdict(set)}
    code_arc = set(X.a2t)
    for a, n, mn, ops in A:
        if a not in code_arc: continue
        for s_, hh, r in re.findall(r'\((-?)\$([0-9a-f]+),(A[56])\)', ops):
            v = ((-1 if s_ else 1) * int(hh, 16)) & 0xffff
            usage_arc[r][v].add('B' if (mn.endswith('.b') or mn in D.OCTET) else mn[-1].upper() if '.' in mn else '?')
    # paires traduit -> arcade (A5)
    t2a = {}; a2t = {}
    for k, v in PA['A5'].items():
        t = int(k, 16); best = v[0]
        if not isinstance(best, list) or best[1] < 2: continue
        t2a[t] = int(best[0], 16)
        a2t.setdefault(int(best[0], 16), t)
    def octet(t): return t == 'B'
    def conv_t2a(vt, tail):
        """déplacement A5 de l'image traduite -> arcade (vote des instructions alignées si >= 3, sinon règle)"""
        ex = PA['A5'].get('%04x' % vt)
        if ex:
            vs = [e for e in ex if isinstance(e, list)]
            tot = sum(e[1] for e in vs)
            if vs and vs[0][1] >= 3 and vs[0][1] >= 0.75 * tot: return int(vs[0][0], 16)
        if vt < 0x8000 and vt not in (0x400, 0x800, 0xC00, 0x1000):     # zone non relogée : règle XOR 1 des octets
            return vt ^ 1 if octet(tail) else vt
        return t2a.get(vt)
    def conv_a2t(va, tail):
        cands = [int(k, 16) for k, v in PA['A5'].items() if isinstance(v[0], list) and int(v[0][0], 16) == va and v[0][1] >= 3]
        if len(cands) == 1: return cands[0]
        if va < 0x8000: return va ^ 1 if octet(tail) else va
        return a2t.get(va)
    def champ_t2a(vt, tail):
        ex = PA['A6_taille'].get('%04x/%s' % (vt, tail)) if tail else None
        if ex:
            tot = sum(e[1] for e in ex)
            if ex[0][1] >= 3 and ex[0][1] >= 0.75 * tot: return int(ex[0][0], 16)
        return vt ^ 1 if tail == 'B' else vt
    def champ_a2t(va, tail):
        if tail:
            cands = [int(k[:4], 16) for k, e in PA['A6_taille'].items() if k.endswith('/' + tail)
                     and int(e[0][0], 16) == va and e[0][1] >= 3 and e[0][1] >= 0.75 * sum(x[1] for x in e)]
            if len(cands) == 1: return cands[0]
        return va ^ 1 if tail == 'B' else va
    # ------------------------------------------------ fonctions MIPS : index
    fstarts = [f['mips'] for f in FN]
    fby = {f['mips']: f for f in FN}
    arc_start = {}                                      # arcade -> fonction MIPS
    for f in FN:
        if 'arcade' in f: arc_start.setdefault(f['arcade'], f)
    auto_f = {int(k): v for k, v in AU['fonctions'].items()}
    taches = {int(k): v for k, v in AU['taches'].items()}
    S = set(arc_start) | set(auto_f) | set(taches)
    for x in AU['aiguillages']:
        for c in x['cas']:
            if c in aidx and A[aidx[c]][2] != 'rts': S.add(c)
    apres_rupture = set(A[k][0] for k in range(1, len(A)) if A[k-1][2] in ('rts', 'jmp', 'bra', 'rte'))

    def fonction_mips(v):
        k = bisect.bisect_right(fstarts, v) - 1
        return FN[k] if k >= 0 else None

    def complete_code(ar, mi):
        """remplit les espaces manquants d'une adresse de code ; renvoie (arcade, mips, trad, cohérent, interne)"""
        tr = None; coh = None; interne = False
        if mi is not None and CODE0 <= mi < CODE1:
            f = fonction_mips(mi)
            if f and (mi == f['mips'] or (mi - f['mips'] <= 0x20 and 'trad' in f)):
                tr = f.get('trad'); arc_f = f.get('arcade')
                if ar is None: ar = arc_f
                elif arc_f is not None: coh = abs(arc_f - ar) <= 8
                if mi != f['mips']: mi = f['mips']
            else:
                interne = True
                t, d = X.mips_vers_trad(mi)
                tr = t
                if t is not None:
                    a2, dd = X.trad_vers_arcade(t, 16)
                    if ar is None: ar = a2
                    elif a2 is not None: coh = abs(a2 - ar) <= 0x20
        elif ar is not None:
            f = arc_start.get(ar)
            if f: mi = f['mips']; tr = f.get('trad')
            else:
                t, d = X.arcade_vers_trad(ar, 8)
                if t is not None:
                    tr = t; va, dd = X.trad_vers_mips(t); mi = va
        return ar, mi, tr, coh, interne

    # ------------------------------------------------ symboles du journal
    rows = lit_extraits()
    groupes = collections.OrderedDict()
    def ajoute(key, r, champs):
        g = groupes.setdefault(key, {'rows': [], 'champs': {}})
        g['rows'].append(r)
        for k, v in champs.items():
            if v not in (None, '') and k not in g['champs']: g['champs'][k] = v
    arc_seuls = []; jarc = {}                          # arcade donnée par le journal -> clé de groupe mips
    for r in rows:
        ty = r['type']; note = r['note']
        ar = lit_int(r['arcade']); mi = lit_int(r['mips']); trv = lit_int(r['trad'])
        if ty in ('fonction', 'étiquette'):
            if ar is not None and not (0 <= ar < 0x100000): ar = None
            if mi is not None and (mi < CODE0 or re.search(r'moteur ps2 \(ex', note.lower())) and ar is None:
                ajoute(('moteur', mi), r, {'type': 'fonction', 'mips': 'moteur ' + hx(mi)}); continue
            if mi is not None and mi >= 0x70000000:
                ajoute(('reg', mi), r, {'type': 'registre matériel', 'mips': hx(mi)}); continue
            if ar is None and mi is None and trv is not None:          # aides de l'image traduite
                ajoute(('trad', trv), r, {'type': 'fonction', 'trad': h(trv)}); continue
            if ar is None and mi is None:
                ajoute(('libre', r['nom']), r, {'type': ty}); continue
            if mi is not None and CODE0 <= mi < CODE1:
                f = fonction_mips(mi)
                debut = f is not None and 0 <= mi - f['mips'] <= 0x10
                key = ('m', f['mips'] if debut else mi)
                ajoute(key, r, {'debut': debut, 'mips_v': key[1], 'jarc': ar})
                if ar is not None: jarc.setdefault(ar, key)
                continue
            if mi is not None:                                          # données / hors code
                ajoute(('libre', r['nom']), r, {'type': ty, 'mips': hx(mi)}); continue
            arc_seuls.append(r)
        elif ty == 'variable A5':
            v = lit_int(r['a5'])
            if v is None and ar is not None and ar >= 0xff0000: v = (ar - 0xff8000) & 0xffff; r['_rom'] = True
            if v is None and mi is not None and 0x900000 <= mi < 0x910000: v = (mi - 0x908000) & 0xffff
            if v is None: ajoute(('libre', r['nom']), r, {'type': 'variable A5'}); continue
            v &= 0xffff
            txt = (note + ' ' + r['role'] + ' ' + r['nom']).lower()
            rom = r.get('_rom') or re.search(r'disposition rom|\(rom\)|en rom|\brom \$|\$[0-9a-f]+ rom\b|\brom\b.*\bposé|_rom\b', txt)
            tail = r['taille'].upper()[:1] if r['taille'] else ''
            it, ia = v in usage['A5'], v in usage_arc['A5']
            if r.get('num'):
                num = r['num']
                if num == 'p': num = 'a' if v < 0x8000 else 'p'
            elif it and not ia: num = 't'
            elif ia and not it: num = 'a'
            elif it and ia: num = 'a' if rom else 't'
            elif tail == 'B' and (v ^ 1) in usage['A5'] and not rom: num = 'p'      # numérotation PS2 d'un octet
            else: num = 'a' if rom else 't'
            if num == 'a':
                vt = conv_a2t(v, tail)
                key = ('a5', vt) if vt is not None else ('a5a', v)
            else:
                vt = v ^ 1 if num == 'p' else v
                key = ('a5', vt)
            ajoute(key, r, {'type': 'variable A5', 'vt': vt, 'va_rom': v if num == 'a' else None, 'tail': tail, 'num': num})
        elif ty in ('champ joueur', 'champ objet'):
            v = lit_int(r['champ'].replace('+', '')) if r['champ'] else None
            if v is None: ajoute(('libre', r['nom']), r, {'type': ty}); continue
            txt = (note + ' ' + r['role'] + ' ' + r['nom']).lower()
            tail = r['taille'].upper()[:1] if r['taille'] and r['taille'][0] in 'BWLbwl' else ''
            struct = 'tache' if (r['nom'].startswith('tache_') or 'bloc de tâche' in txt) else \
                     'ctx' if r['nom'].startswith('moteur_ctx') else 'obj'
            if r.get('num') == 't' or (r.get('num') is None and
                                        re.search(r'num[ée]rotation (traduction|68k)|\(68k\)', txt)):
                va = champ_t2a(v, tail)
            else:
                va = v
            ajoute((ty, struct, va, tail if tail == 'B' else ''), r, {'type': ty, 'va': va, 'tail': tail, 'struct': struct})
        elif ty == 'table':
            if ar is not None and ar < 0x100000:
                t, d = X.arcade_vers_trad(ar, 0)
                ajoute(('table', 'a', ar), r, {'type': 'table', 'arcade': ar, 'trad_v': t}); continue
            if mi is not None:
                if 0x500000 <= mi < 0x88C700: mi -= 0x1F0000   # adresse d'exécution
                tr = DATA_TRAD + (mi - CODE1) if CODE1 <= mi < 0x69C700 else None
                ajoute(('table', 'm', mi), r, {'type': 'table', 'mips_v': mi, 'trad_v': tr}); continue
            ajoute(('libre', r['nom']), r, {'type': 'table'})
        else:
            key = (ty, r['arcade'] or r['mips'] or r['trad'] or r['a5'] or r['nom'])
            ajoute(key, r, {'type': ty})
    for r in arc_seuls:
        ar = lit_int(r['arcade'])
        key = jarc.get(ar, ('a', ar))
        ajoute(key, r, {'jarc': ar} if key[0] == 'm' else {})
    # complétion des adresses de code
    for key, g in groupes.items():
        c = g['champs']
        if key[0] == 'm':
            mi = key[1]; jar = c.get('jarc')
            if c.get('debut'):
                f = fby[mi]; tr = f.get('trad'); aa = f.get('arcade')
                c['type'] = 'fonction'; c['trad_v'] = tr
                if jar is not None:
                    c['arcade'] = jar
                    if aa is not None and abs(aa - jar) > 8 and f.get('methode') == 'aligné' and f.get('n', 0) >= 4:
                        c['arcade'] = aa                       # le code fait foi
                        for r in g['rows']: r['_incoherent'] = 'le journal cite $%X, le code aligne cette fonction sur $%X' % (jar, aa)
                    elif aa is not None and abs(aa - jar) > 8:
                        for r in g['rows']: r['_incoherent'] = 'alignement : $%X' % aa
                elif aa is not None and f.get('score', 0) >= 0.25:
                    c['arcade'] = aa; c['arc_auto'] = True
            else:
                f = fonction_mips(mi)
                t, d = X.mips_vers_trad(mi, 0x60)
                txt = ' '.join(r['nom'] + ' ' + r['role'] for r in g['rows']).lower()
                site = re.search(r'\bsite|point interne|instruction|\bsll\b|\bappel (du|de la|terminal)|zone|^appel|_appel|appel_', txt)
                c['type'] = 'étiquette' if site or all(r['type'] == 'étiquette' for r in g['rows']) else 'fonction'
                c['trad_v'] = t
                a2 = None; dd = None
                if t is not None and f is not None and f.get('score', 0) >= 0.3:
                    a2, dd = X.trad_vers_arcade(t, 4)
                if jar is not None:
                    c['arcade'] = jar
                    if a2 is not None and abs(a2 - jar) > 0x10:
                        if dd == 0:
                            c['arcade'] = a2
                            for r in g['rows']: r['_incoherent'] = 'le journal cite $%X, l\'instruction alignée est en $%X' % (jar, a2)
                        else:
                            for r in g['rows']: r['_incoherent'] = 'alignement : $%X' % a2
                elif a2 is not None: c['arcade'] = a2; c['arc_auto'] = True
        elif key[0] == 'a':
            ar = key[1]; c['arcade'] = ar
            f = arc_start.get(ar)
            if f is not None:
                c['mips_v'] = f['mips']; c['trad_v'] = f.get('trad'); c['arc_debut'] = True
            else:
                t, d = X.arcade_vers_trad(ar, 4)
                if t is not None:
                    c['trad_v'] = t; c['mips_v'] = X.trad_vers_mips(t)[0]
            txt = ' '.join(r['nom'] + ' ' + r['role'] for r in g['rows']).lower()
            site = re.search(r'\bsite|point interne|instruction|\bsll\b|\bappel (du|de la|terminal)|zone|^appel|_appel|appel_|passage|boucle', txt)
            c['type'] = 'fonction' if (ar in S or ar in apres_rupture or not site) else 'étiquette'

    par_arc = {}
    for key, g in groupes.items():
        if key[0] == 'm' and g['champs'].get('arcade') is not None and g['champs'].get('debut'):
            par_arc.setdefault(g['champs']['arcade'], key)
    for key in [k for k in groupes if k[0] == 'a']:
        cible = par_arc.get(key[1])
        if cible is not None:
            groupes[cible]['rows'].extend(groupes[key]['rows']); del groupes[key]
    # ------------------------------------------------ choix du nom, du rôle, de la confiance
    def choisit(g):
        rs = [r for r in g['rows'] if 'dépassé' not in r['note']] or g['rows']
        def sc(r):
            return (CONF.get(r['confiance'], 0) * 4 + (0 if GENERIQUE.match(r['nom']) else 3)
                    + (1 if r['role'] else 0))
        best = max(rs, key=sc)
        noms = [r['nom'] for r in rs]
        sources = []
        for r in g['rows']:
            for s in re.split(r'\s*;\s*', r['source']):
                if s and s not in sources: sources.append(s)
        conf = max((r['confiance'] for r in rs), key=lambda c: CONF.get(c, 0))
        if any(r.get('_incoherent') for r in rs) and conf == 'sûr': conf = 'probable'
        alias = sorted(set(n for n in noms if n != best['nom']))
        return best, sources, conf, alias

    sortie = []; pris_nom = {}
    def nom_unique(n):
        if n not in pris_nom: pris_nom[n] = 1; return n
        pris_nom[n] += 1; return '%s_%d' % (n, pris_nom[n])
    deja_code = set()
    for key, g in groupes.items():
        best, sources, conf, alias = choisit(g)
        c = g['champs']; ty = c.get('type', best['type'])
        role = best['role'].rstrip('.') + '.'
        if alias: role += ' (alias : %s)' % ', '.join(alias[:4])
        if best['note'] and 'dépassé' in best['note']: role += ' [%s]' % best['note']
        row = {'type': ty, 'nom': best['nom'], 'arcade': '', 'mips': '', 'trad': '', 'taille': best['taille'],
               'role': role, 'source': ' + '.join(sources), 'confiance': conf}
        if key[0] in ('m', 'a'):
            ar = c.get('arcade'); mi = c.get('mips_v'); tr = c.get('trad_v')
            row['arcade'] = h(ar); row['mips'] = hx(mi); row['trad'] = h(tr)
            f = fby.get(mi) if mi is not None else None
            if f is None and ar is not None: f = arc_start.get(ar)
            if f is not None and ty == 'fonction':
                if 'arcade' in f and 'arcade_fin' in f and f['arcade_fin'] > f['arcade'] and ar == f.get('arcade'):
                    row['taille'] = str(f['arcade_fin'] - f['arcade'])
                elif 'trad' in f: row['taille'] = '%d (t)' % (f['trad_fin'] - f['trad'])
            if ar is not None: deja_code.add(('a', ar))
            if mi is not None and ty == 'fonction': deja_code.add(('m', mi))
            if not best['mips'] and mi is not None: row['source'] += ' + mips par carte_image'
            inc = [r['_incoherent'] for r in g['rows'] if r.get('_incoherent')]
            if inc: row['role'] += ' [arcade du journal non confirmée par le code : %s]' % inc[0]
            if c.get('arc_auto'): row['source'] += ' + arcade par alignement'
        elif key[0] == 'moteur':
            row['mips'] = c['mips']
        elif key[0] == 'reg':
            row['mips'] = c['mips']
        elif key[0] == 'trad':
            row['trad'] = c['trad']
        elif key[0] == 'a5a':                          # variable de la ROM sans équivalent dans l'image
            va = key[1]
            row['arcade'] = h(0xff0000 + ((0x8000 + (va if va < 0x8000 else va - 0x10000)) & 0xffff))
            row['role'] += " [A5%+d arcade ; aucune instruction alignée ne la relie à l'image traduite]" % (va if va < 0x8000 else va - 0x10000)
        elif key[0] == 'a5':
            vt = c['vt']; tail = c.get('tail', '')
            va = conv_t2a(vt, tail or ''.join(sorted(usage['A5'].get(vt, set())))) if c.get('va_rom') is None else c['va_rom']
            row['trad'] = h(0xff0000 + ((0x8000 + (vt if vt < 0x8000 else vt - 0x10000)) & 0xffff))
            sz = ''.join(sorted(usage['A5'].get(vt, set())))
            psv = vt ^ 1 if (tail == 'B' or sz == 'B') else vt
            if va is not None and vt < 0x8000: psv = va          # zone non relogée : MIPS = arcade
            row['mips'] = hx(0x900000 + ((0x8000 + (psv if psv < 0x8000 else psv - 0x10000)) & 0xffff))
            if va is not None:
                row['arcade'] = h(0xff0000 + ((0x8000 + (va if va < 0x8000 else va - 0x10000)) & 0xffff))
            if va is not None and 'jamais utilisée par la rom' in row['role'].lower():
                row['role'] += " [l'alignement la relie pourtant à la variable arcade A5%+d : déplacement relogé par le portage]" % (va if va < 0x8000 else va - 0x10000)
            row['role'] += ' [A5%+d trad. ; accès %s]' % ((vt if vt < 0x8000 else vt - 0x10000), sz or 'aucun dans l\'image')
            if not row['taille']: row['taille'] = sz
        elif key[0] in ('champ joueur', 'champ objet'):
            va = c['va']; tail = c.get('tail', '')
            vt = champ_a2t(va, tail)
            row['arcade'] = '+$%X' % va; row['trad'] = '+$%X' % vt
            row['mips'] = '+$%X' % (va if tail == 'B' else vt)
            if c.get('struct') == 'tache': row['role'] = '[bloc de tâche] ' + row['role']
            if c.get('struct') == 'ctx': row['role'] = '[contexte de couche du moteur PS2, mesuré sur ro9] ' + row['role']
            ex = PA['A6_taille'].get('%04x/%s' % (vt, tail)) if tail else None
            if ex and int(ex[0][0], 16) == va: row['source'] += ' + correspondance vérifiée (%d accès alignés)' % ex[0][1]
        elif key[0] == 'table':
            if key[1] == 'a': row['arcade'] = h(key[2])
            else: row['mips'] = hx(key[2])
            if c.get('trad_v') is not None: row['trad'] = h(c['trad_v'])
        else:
            row['arcade'] = best['arcade']; row['mips'] = best['mips']; row['trad'] = best['trad'] or best['a5']
            if not (row['arcade'] or row['mips'] or row['trad']):
                mm = re.search(r'(?:\$|0x)((?:96|88)[0-9A-Fa-f]{4}|9[0-4][0-9A-Fa-f]{4}|A[0-9A-Fa-f]{5})\b', best['role'] + ' ' + best['nom'] + ' ' + best['note'])
                if mm and ty == 'variable portage': row['mips'] = '0x' + mm.group(1).upper(); row['source'] += ' + adresse lue dans le rôle'
        if re.match(r'^fonc_[0-9a-fA-F]{6}$', row['nom']) and row['arcade'] and row['nom'][5:].upper() != row['arcade'][1:]:
            row['role'] += ' (nom du journal : %s)' % row['nom']; row['nom'] = 'fonc_' + row['arcade'][1:]
        row['nom'] = nom_unique(row['nom'])
        sortie.append(row)

    # ------------------------------------------------ symboles automatiques
    # noms donnés ici après lecture du code arcade (enveloppes du noyau Capcom, tâche principale)
    MANUEL = {
        0x1302: ('noyau_creer_tache', 'Enveloppe TRAP #0 (créer la tâche D0 = emplacement ×$20, A0 = entrée, D1/D2 = paramètres) ; gestionnaire $1306.'),
        0x1324: ('noyau_finir_tache', 'TRAP #1 : termine la tâche courante (gestionnaire $1326, ne revient pas).'),
        0x1346: ('noyau_tuer_tache', 'Enveloppe TRAP #2 : tue la tâche D0 (gestionnaire $134A).'),
        0x1370: ('noyau_attendre', 'Enveloppe TRAP #3 avec sauvegarde de D0-D7/A0-A6 : attend D0 images (gestionnaire $137C) ; appelée à chaque fin de boucle de tâche.'),
        0x13A2: ('noyau_ceder', 'Enveloppe TRAP #4 : la tâche courante reste prête et rend la main à l\'ordonnanceur (gestionnaire $13A6).'),
        0x13C0: ('noyau_suspendre_tache', 'Enveloppe TRAP #5 (MOVEM autour) : met la tâche D0 à l\'état 2 (suspendue), efface son octet +1 (gestionnaire $13CC).'),
        0x13CC: ('trap5_tache_suspendre', 'TRAP #5 : bloc de la tâche D0 -> état 2, octet +1 effacé.'),
        0x13DC: ('noyau_reveiller_tache', 'Enveloppe TRAP #6 : remet la tâche D0 à l\'état 4 (prête) avec D1 dans son octet +1 (gestionnaire $13E8).'),
        0x13E8: ('trap6_tache_reveiller', 'TRAP #6 : bloc de la tâche D0 -> état 4, octet +1 = D1.'),
        0x13F8: ('noyau_interruptions', 'Enveloppe TRAP #7 : D0 = 0 démasque les interruptions (ANDI #$F8FF,SR), sinon les masque (ORI #$700) ; gestionnaire $13FC.'),
        0x13FC: ('trap7_masque_interruptions', 'TRAP #7 : masque (D0 ≠ 0) ou démasque (D0 = 0) les interruptions dans le SR empilé.'),
        0x3EBA: ('tache_principale', 'Tâche principale (emplacement 0, créée par $DFBE) : chaque image, aiguille sur le mode de jeu $FF8000 par la table $3EEC (JSR), appelle $182E puis attend une image (JSR $1370 avec D0 = 1).'),
    }

    noms_par_arc = {}
    for r in sortie:
        if r['type'] == 'fonction' and r['arcade'] and not re.search(r'appel|site', r['nom']):
            noms_par_arc[int(r['arcade'][1:], 16)] = r['nom']
    # tâches
    for e, v in sorted(taches.items()):
        nom = noms_par_arc.get(e)
        ar, mi, tr, coh, interne = complete_code(e, None)
        role = 'Point d\'entrée de tâche créée par le noyau ($1302 = TRAP #0, A0 = entrée), emplacement(s) %s ; %d site(s) : %s.' % (
            ', '.join('$%X' % s for s in v['emplacements']), len(v['sites']), ', '.join('$%X' % s for s in v['sites'][:4]))
        if nom:
            for r in sortie:
                if r['nom'] == nom: r['role'] += ' ' + role; r['source'] += ' ; auto : création de tâche'
            continue
        nm = nom_unique(MANUEL[e][0] if e in MANUEL else 'tache_%02X_%06X' % (v['emplacements'][0] if v['emplacements'] else 0, e))
        if e in MANUEL: role = MANUEL[e][1] + ' ' + role
        sortie.append({'type': 'fonction', 'nom': nm, 'arcade': h(e), 'mips': hx(mi), 'trad': h(tr), 'taille': '',
                       'role': role, 'source': 'auto : appels JSR $1302 (ROM)', 'confiance': 'sûr'})
        noms_par_arc[e] = nm; deja_code.add(('a', e)); deja_code.add(('m', mi))
    # fonctions MIPS
    for f in FN:
        mi = f['mips']
        if ('m', mi) in deja_code or ('arcade' in f and ('a', f['arcade']) in deja_code): continue
        ar = f.get('arcade'); tr = f.get('trad')
        if f['natif']:
            nm = nom_unique('natif_%06X' % mi)
            sortie.append({'type': 'fonction', 'nom': nm, 'arcade': '', 'mips': hx(mi), 'trad': h(tr) if tr else '',
                           'taille': str(f['mips_fin'] - mi) + ' (m)', 'role': 'Fonction native (code C du portage, sans équivalent 68K) ; appelée par le jeu recompilé.',
                           'source': 'natifs_ro3.json (critère natmiss, §55)', 'confiance': 'sûr'})
            continue
        if ar is None:
            nm = nom_unique('port_%06X' % mi)
            sortie.append({'type': 'fonction', 'nom': nm, 'arcade': '', 'mips': hx(mi), 'trad': h(tr),
                           'taille': '%d (t)' % (f['trad_fin'] - tr) if tr else '',
                           'role': 'Fonction recompilée sans homologue arcade retrouvé (code ajouté ou trop modifié par le portage, ou alignement insuffisant : %d %% des instructions).' % round(100 * f.get('score', 0)),
                           'source': 'auto : cibles de jal + carte_image', 'confiance': 'sûr' if tr else 'probable'})
            continue
        nm = nom_unique(MANUEL[ar][0] if ar in MANUEL else 'fonc_%06X' % ar)
        sc = f.get('score', 0); meth = f.get('methode')
        conf = 'sûr' if (meth == 'aligné' and sc >= 0.5) else 'probable' if sc >= 0.25 else 'hypothèse'
        taille = str(f['arcade_fin'] - ar) if f.get('arcade_fin', 0) > ar else '%d (t)' % (f['trad_fin'] - tr)
        ap = auto_f.get(ar)
        role = 'Fonction %s ; non nommée par le journal.' % (
            'appelée %d fois en ROM (JSR/BSR)' % ap['appels'] if ap else 'atteinte par saut ou table (pas d\'appel direct en ROM)'
            if f.get('entree_arcade') != 'interne' else 'commençant au milieu d\'une routine arcade (fragment découpé par le recompilateur)')
        if ar in MANUEL: role = MANUEL[ar][1]
        sortie.append({'type': 'fonction', 'nom': nm, 'arcade': h(ar), 'mips': hx(mi), 'trad': h(tr), 'taille': taille,
                       'role': role, 'source': ('lecture du code ROM + ' if ar in MANUEL else '') + 'auto : alignement %s (%d %% des instructions)' % (meth, round(100 * sc)),
                       'confiance': conf})
        noms_par_arc[ar] = nm; deja_code.add(('a', ar))
    # fonctions arcade appelées sans début MIPS propre (fusionnées / inlinées dans une fonction MIPS)
    for ar, v in sorted(auto_f.items()):
        if ('a', ar) in deja_code: continue
        t, d = X.arcade_vers_trad(ar, 0)
        mi = X.trad_vers_mips(t)[0] if t is not None else None
        nm = nom_unique(MANUEL[ar][0] if ar in MANUEL else 'fonc_%06X' % ar)
        sortie.append({'type': 'fonction', 'nom': nm, 'arcade': h(ar), 'mips': hx(mi), 'trad': h(t),
                       'taille': '', 'role': (MANUEL[ar][1] + ' ') if ar in MANUEL else '' + 'Fonction appelée %d fois en ROM (JSR/BSR), sans début de fonction MIPS propre (absorbée dans la fonction MIPS englobante) ; non nommée par le journal.' % v['appels'],
                       'source': 'auto : cibles d\'appel ROM' + (' + alignement' if t is not None else ''),
                       'confiance': 'sûr' if t is not None else 'probable'})
        noms_par_arc[ar] = nm; deja_code.add(('a', ar))
    # aiguillages et gestionnaires
    starts_arc = sorted(noms_par_arc)
    SEL = {'($4,A6)': 'r4_', '($5,A6)': 'r5_', '($6,A6)': 'r6_', '($7,A6)': 'r7_', '($3,A6)': 'r3_',
           '($0,A5)': 'mode_', '($138,A5)': 'm138_'}
    for x in AU['aiguillages']:
        site = x['site']
        k = bisect.bisect_right(starts_arc, site) - 1
        parent = noms_par_arc[starts_arc[k]] if k >= 0 else 'rom'
        sel = x['selecteur'][1] if x['selecteur'] else '?'
        tag = SEL.get(sel, 'c_')
        t, d = X.arcade_vers_trad(site, 0)
        mi = X.trad_vers_mips(t)[0] if t is not None else None
        tbn = nom_unique('aig_%s' % parent)
        selt = ('sélecteur %s' % sel) if x['selecteur'] else 'sélecteur non déterminé'
        sortie.append({'type': 'table', 'nom': tbn, 'arcade': h(x['table']), 'mips': hx(mi), 'trad': h(t),
                       'taille': '%d' % (2 * len(x['cas'])),
                       'role': 'Table d\'aiguillage Capcom (%s, %d cas, %s) de %s ; mips/trad = site du %s.' % (
                           'JSR' if x['appel'] else 'JMP', len(x['cas']), selt, parent, 'JSR' if x['appel'] else 'JMP'),
                       'source': 'auto : idiome MOVE.W T(PC,Dn),Dm ; %s T(PC,Dm) (§15)' % ('JSR' if x['appel'] else 'JMP'),
                       'confiance': 'sûr' if x['aligne'] else 'probable'})
        for i, c in enumerate(x['cas']):
            if c in noms_par_arc or c not in aidx or A[aidx[c]][2] == 'rts': continue
            t, d = X.arcade_vers_trad(c, 0)
            mi = X.trad_vers_mips(t)[0] if t is not None else None
            nm = nom_unique('%s__%s%02X' % (parent, tag, 2 * i))
            sortie.append({'type': 'fonction', 'nom': nm, 'arcade': h(c), 'mips': hx(mi), 'trad': h(t), 'taille': '',
                           'role': 'Gestionnaire du cas %d (valeur $%02X) de l\'aiguillage %s (%s).' % (i, 2 * i, tbn, selt),
                           'source': 'auto : table d\'aiguillage ROM $%X' % x['table'],
                           'confiance': 'sûr' if t is not None else 'probable'})
            noms_par_arc[c] = nm
    # noms manuels (lecture du code) : renomme les symboles génériques, complète les autres, ajoute les absents
    par_arc_rows = collections.defaultdict(list)
    for r in sortie:
        if r['type'] in ('fonction', 'étiquette') and r['arcade']: par_arc_rows[int(r['arcade'][1:], 16)].append(r)
    for ar, (nm, role) in sorted(MANUEL.items()):
        rs = par_arc_rows.get(ar)
        if rs:
            r = rs[0]
            if GENERIQUE.match(r['nom']) or r['nom'].startswith('tache_') and r['nom'][6:8].isupper():
                r['role'] = role + ' (ancien nom : %s)' % r['nom'] if not r['nom'].startswith('fonc_') else role
                r['nom'] = nom_unique(nm); r['type'] = 'fonction'
            elif r['nom'] != nm:
                r['role'] += ' [lecture du code : %s]' % role
            if 'lecture du code' not in r['source']: r['source'] = 'lecture du code ROM + ' + r['source']
            r['confiance'] = 'sûr'
        else:
            t, d = X.arcade_vers_trad(ar, 0)
            mi = X.trad_vers_mips(t)[0] if t is not None else None
            sortie.append({'type': 'fonction', 'nom': nom_unique(nm), 'arcade': h(ar), 'mips': hx(mi), 'trad': h(t),
                           'taille': '', 'role': role + ('' if t is not None else ' Sans équivalent dans l\'image traduite (noyau remplacé par les fils PS2 du portage).'),
                           'source': 'lecture du code ROM', 'confiance': 'sûr'})
    # moteur PS2 / natifs : sites d'appel (hooks_fork_ro3.json)
    hk = json.load(open('<workspace>/scripts/untranspile/hooks_fork_ro3.json'))
    connus = set(r['mips'] for r in sortie)
    for k, v in hk.items():
        neg = k.startswith('-'); val = int(k.lstrip('-'), 16)
        if v['type'] == 'moteur PS2':
            ex = 0x1F0000 - val if neg else val + 0x1F0000
            lab = 'moteur ' + hx(ex)
            if lab in connus: continue
            sortie.append({'type': 'fonction', 'nom': nom_unique('moteur_%06X' % ex), 'arcade': '', 'mips': lab, 'trad': '',
                           'taille': '', 'role': 'Fonction du moteur PS2 (hors module) appelée par le jeu : %d site(s) (%s).' % (
                               len(v['sites']), ', '.join(v['sites'][:4])),
                           'source': 'hooks_fork_ro3.json (§55)', 'confiance': 'sûr'})
    # tri
    ordre = {'fonction': 0, 'étiquette': 1, 'table': 2, 'variable A5': 3, 'champ joueur': 4, 'champ objet': 5,
             'variable portage': 6, 'registre matériel': 7, 'constante': 8}
    def cle(r):
        a = r['arcade'] or ''; m = r['mips'] or ''; t = r['trad'] or ''
        def num(s):
            s = s.replace('moteur ', '').replace('+', '')
            try: return int(s[1:], 16) if s.startswith('$') else int(s, 16)
            except ValueError: return 1 << 40
        return (ordre.get(r['type'], 9), num(a) if a else (1 << 39) + num(m or t))
    sortie.sort(key=cle)
    with open(os.path.join(RAC, 'symboles_ro3.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        w.writerow(['type', 'nom', 'arcade', 'mips', 'trad', 'taille', 'rôle', 'source', 'confiance'])
        for r in sortie:
            pv = lambda t: re.sub(r'\s*;\s*', ' | ', t.replace('\n', ' '))
            w.writerow([r['type'], r['nom'], r['arcade'], r['mips'], r['trad'], pv(r['taille']),
                        pv(r['role']), pv(r['source']), r['confiance']])
    c = collections.Counter(r['type'] for r in sortie)
    print(len(sortie), 'symboles', dict(c))
    nj = sum(1 for k in groupes)
    print('groupes issus du journal :', nj)

if __name__ == '__main__':
    main()
