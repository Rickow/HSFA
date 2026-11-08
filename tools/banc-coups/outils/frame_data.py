#!/usr/bin/env python3
"""(banc_coups) FRAME DATA : mesure des coups normaux au sol dans notre jeu et comparaison a SuperCombo.

  frame_data.py plan <perso> <rep>            plan des essais (lu par lua/banc_coups.lua) + index, d'apres
                                              frame_data/supercombo_sfa3.csv (coups normaux au sol du perso)
  frame_data.py mesure <rep> <log> <sortie>   mesures (demarrage, actif, recuperation, avantages) -> TSV
  frame_data.py ecarts <mesures.tsv>... -> frame_data/ecarts.tsv (+ etalonnage)

Convention de mesure (vitesse NORMAL, 1 tour par image ; etalonnee sur Ryu / Ken, arcade sfa3ud) :
  - images « qui avancent » : celles ou le compteur de duree du pas ($32) ou le pas d'animation ($1C) de J1 change
    (les images gelees de l'arret sur coup, hitstop, ne comptent pas) ;
  - demarrage = images qui avancent, de la 1re image du coup (sortie du neutre) a la 1re image active exclue ;
  - actif = images qui avancent ou le pas courant porte une boite d'attaque (octet 9 du pas de 20 o non nul) ;
  - recuperation = images qui avancent apres la derniere active, jusqu'au retour au neutre ($5 = 0, $6 = 0/2/4,
    $7 non nul) exclu ;
  - avantage = (retour au neutre de J2) - (retour au neutre de J1), au contact (essai h) et en garde (essai b, J2 tient
    arriere) ; images brutes (le gel touche les deux joueurs).
Essais : w = dans le vide (J2 loin), h = au contact, b = en garde. Les normaux « Close » se jouent pres (pas de w).
"""
import csv, os, re, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, 'outils'))
SC = os.path.join(B, 'frame_data', 'supercombo_sfa3.csv')
BOUTON = {'Jab': '1', 'Strong': '2', 'Fierce': '3', 'Short': '4', 'Forward': '5', 'Roundhouse': '6'}
SC_NOM = {'Juli': 'Juli', 'Juni': 'Juni', 'Ryu': 'Ryu', 'Ken': 'Ken', 'Akuma': 'Akuma', 'Balrog': 'Balrog'}


def normaux(perso):
    """coups normaux au sol de SuperCombo pour ce perso : (n, nom, ismes, ligne SC)"""
    res = []
    for r in csv.DictReader(open(SC), delimiter=';'):
        if r['perso'] != perso or r['section'] != 'Ground Normals':
            continue
        m = re.fullmatch(r'(Close |Far )?(Standing|Crouching) (Jab|Strong|Fierce|Short|Forward|Roundhouse)', r['coup'])
        if m:
            res.append((len(res) + 1, r['coup'], r['ismes'], r))
    return res


GENERIQUES = ['%s %s' % (p, b) for p in ('Standing', 'Crouching') for b in ('Jab', 'Strong', 'Fierce', 'Short', 'Forward', 'Roundhouse')]


def essais(nom):
    m = re.fullmatch(r'(Close |Far )?(Standing|Crouching) (\w+)', nom)
    pres, acc, b = m.group(1) == 'Close ', m.group(2) == 'Crouching', BOUTON[m.group(3)]
    corps = ('8:D 3:D+%s 40:D' % b) if acc else ('8:N 3:%s' % b)
    e = []
    if not pres:
        e.append(('w', 0xC0, corps, ''))
    d = 0x24 if pres else 0x40
    e.append(('h', d, corps, ''))
    # garde : J2 tient arriere des l'appui de J1 (garde de proximite, il ne recule pas) ; accroupi (bas + arriere)
    # contre les coups accroupis (coups bas)
    e.append(('b', d, corps, '8:N 200:D+B' if acc else '8:N 200:B'))
    return e


def plan(perso, rep):
    os.makedirs(rep, exist_ok=True)
    with open(os.path.join(rep, 'plan.txt'), 'w') as fp, open(os.path.join(rep, 'index.tsv'), 'w') as fi:
        fi.write('id\tperso\tcoup\tismes\tessai\n')
        liste = normaux(SC_NOM.get(perso, perso))
        if not liste:   # perso sans frame data publiee : 12 normaux generiques, mesures sans reference
            liste = [(k + 1, nom, '', None) for k, nom in enumerate(GENERIQUES)]
        for n, nom, isms, r in liste:
            for t, d, s1, s2 in essais(nom):
                tid = 'FD%d%s' % (n, t)
                fp.write('T|%s|%x|90|%s|%s|120|%s\n' % (tid, d, s1, s2, nom))
                fi.write('\t'.join([tid, perso, nom, isms, t]) + '\n')


def neutre(e):
    return e[0:4] == '0200' and e[4:6] in ('00', '02', '04') and e[6:8] != '00'


def mesure_essai(F):
    """F = lignes F d'un essai (listes de champs du journal) -> dict de mesures"""
    L = []
    for t in F:
        r = int(t[2])
        if r < 8:
            continue
        fp = t[11]
        L.append({'r': r, 'e1': t[3], 'e2': t[4], 'ptr': t[10], 'att': fp[10:12] != '00', 'c1': t[16] if len(t) > 16 else '',
                  'vie2': int(t[8], 16)})
    m = {}
    if not L:
        return m
    # debut du coup = 1re image hors des etats « libres » ($5 = 0 et $6 = 0 / 2 / 4, quel que soit $7) : l'accroupi
    # ou la marche qui precedent l'appui n'en font pas partie
    libre = lambda e: e[0:4] == '0200' and e[4:6] in ('00', '02', '04')
    i0 = next((i for i, x in enumerate(L) if not libre(x['e1'])), None)
    if i0 is None:
        return m
    # images qui avancent (compteur $32 ou pas change par rapport a l'image precedente)
    av = [i == i0 or L[i]['c1'] != L[i - 1]['c1'] or L[i]['ptr'] != L[i - 1]['ptr'] for i in range(len(L))]
    fin = next((i for i in range(i0 + 1, len(L)) if neutre(L[i]['e1'])), None)
    if fin is None:
        return m
    act = [i for i in range(i0, fin) if L[i]['att'] and av[i]]
    if not act:
        m['note'] = 'aucune boîte d\'attaque vue'
    else:
        m['demarrage'] = sum(1 for i in range(i0, act[0]) if av[i])
        m['actif'] = len(act)
        m['recuperation'] = sum(1 for i in range(act[-1] + 1, fin) if av[i])
        if len(act) != sum(1 for i in range(act[0], act[-1] + 1) if av[i]):
            m['note'] = 'actif en plusieurs morceaux'
    m['retour1'] = L[fin]['r']
    # J2 : quitte le neutre puis y revient
    j0 = next((i for i in range(i0, len(L)) if not neutre(L[i]['e2']) and L[i]['e2'][2:4] != '00'), None)
    if j0 is not None:
        j1 = next((i for i in range(j0, len(L)) if neutre(L[i]['e2'])), None)
        if j1 is not None:
            m['retour2'] = L[j1]['r']
            m['avantage'] = L[j1]['r'] - L[fin]['r']
            if any(x['e2'][2:6] in ('0202', '0204', '0206') for x in L[j0:j1]) and m['avantage'] > 30:
                m['chute'] = True
    m['degats'] = 0x90 - min(x['vie2'] for x in L)
    return m


def mesure(rep, log, sortie):
    idx = {r['id']: r for r in csv.DictReader(open(os.path.join(rep, 'index.tsv')), delimiter='\t')}
    F = {}
    for l in open(log, errors='replace'):
        t = l.split()
        if t and t[0] == 'F':
            F.setdefault(t[1], []).append(t)
    par = {}
    for tid, r in idx.items():
        m = mesure_essai(F.get(tid, []))
        k = (r['perso'], r['coup'], r['ismes'])
        d = par.setdefault(k, {})
        e = r['essai']
        if e == 'w' or (e == 'h' and 'demarrage' not in d):
            for c in ('demarrage', 'actif', 'recuperation'):
                if c in m:
                    d[c] = m[c]
            d['source_dar'] = e
        if e == 'h':
            d['avantage_contact'] = m.get('avantage', '') if not m.get('chute') else ''
            if m.get('chute'):
                d['note_h'] = 'J2 chute au contact (avantage sans objet)'
            d['degats'] = m.get('degats', '')
            if m.get('degats', 0) == 0:
                d['note_h'] = 'pas de contact'
        if e == 'b':
            d['avantage_garde'] = m.get('avantage', '')
        if m.get('note'):
            d['note'] = m['note']
    cols = ['perso', 'coup', 'ismes', 'demarrage', 'actif', 'recuperation', 'avantage_garde', 'avantage_contact', 'degats', 'source_dar', 'note']
    with open(sortie, 'w') as f:
        f.write('\t'.join(cols) + '\n')
        for (p, c, i), d in par.items():
            d.update({'perso': p, 'coup': c, 'ismes': i})
            if d.get('note_h'):
                d['note'] = (d.get('note', '') + ' ' + d['note_h']).strip()
            f.write('\t'.join(str(d.get(x, '')) for x in cols) + '\n')


def etalonnage(fichier_ecarts):
    """decalage median par grandeur (mesure - SuperCombo) sur les persos d'arcade connus : convention de mesure"""
    import statistics
    v = {}
    for r in csv.DictReader(open(fichier_ecarts), delimiter='\t'):
        if r['ecart'] not in ('', None) and r['verdict'] and not r['verdict'].startswith('non'):
            g = r['grandeur'] + ('_accroupi' if r['grandeur'] == 'recuperation' and r['coup'].startswith('Crouching') else '')
            v.setdefault(g, []).append(int(r['ecart']))
    return {g: -int(statistics.median(x)) for g, x in v.items()}, {g: len(x) for g, x in v.items()}


def ecarts(fichiers, sortie, etal=None):
    """compare les mesures (TSV de mesure()) a SuperCombo ; etal = decalages par grandeur (etalonnage) a appliquer"""
    sc = {}
    for r in csv.DictReader(open(SC), delimiter=';'):
        sc.setdefault((r['perso'], r['coup']), []).append(r)
        # noms combines (Balrog : « Standing Jab/Short ») -> une entree par bouton
        m = re.fullmatch(r'(Standing|Crouching) (\w+)/(\w+)', r['coup'])
        if m and r['section'] in ('', 'Ground Normals'):
            for b in m.group(2, 3):
                sc.setdefault((r['perso'], '%s %s' % (m.group(1), b)), []).append(r)
    etal = etal or {}
    out = ['module\tperso\tcoup\tismes_sc\tgrandeur\tsupercombo\tmesure\tmesure_etalonnee\tecart\tverdict\tarcade_sfa3ud\tpage\trevid\tdate_releve']
    arc = {}
    for fch in fichiers:
        if fch.endswith('_ref3.tsv'):
            for m in csv.DictReader(open(fch), delimiter='\t'):
                arc[(m['perso'], m['coup'])] = m
    for fch in fichiers:
        mod = os.path.basename(fch)[:-4].rsplit('_', 1)[1]
        for m in csv.DictReader(open(fch), delimiter='\t'):
            ma = arc.get((m['perso'], m['coup'])) if mod != 'ref3' else None
            refs = sc.get((m['perso'], m['coup']), [])
            # plusieurs lignes SuperCombo du meme nom (variantes d'isme non nommees) : la 1re seule est comparee
            ref = refs[0] if refs else None
            for g, gs in (('demarrage', 'demarrage'), ('actif', 'actif'), ('recuperation', 'recuperation'),
                          ('avantage_garde', 'avantage_garde'), ('avantage_contact', 'avantage_contact'), ('degats', 'degats')):
                vs = ref[gs] if ref else ''
                vm = m.get(g, '')
                if not ref:
                    v, e = 'non mesurable (pas de frame data publiée pour ce perso / ce coup)', ''
                elif vs == '':
                    v, e = 'non mesurable (pas de valeur publiée)', ''
                elif vm == '':
                    v, e = 'non mesurable (%s)' % (m.get('note') or 'pas de mesure'), ''
                elif not re.fullmatch(r'[+-]?\d+', vs):
                    v, e = 'non mesurable (valeur publiée douteuse : %s)' % vs, ''
                else:
                    ge = g + ('_accroupi' if g == 'recuperation' and m['coup'].startswith('Crouching') else '')
                    e = int(vm) + etal.get(ge, etal.get(g, 0)) - int(vs)
                    v = 'conforme' if e == 0 else 'écart %+d' % e
                ge = g + ('_accroupi' if g == 'recuperation' and m['coup'].startswith('Crouching') else '')
                vme = str(int(vm) + etal.get(ge, etal.get(g, 0))) if re.fullmatch(r'[+-]?\d+', str(vm)) else ''
                va = ''
                if ma is not None:
                    va = ('= arcade' if ma.get(g, '') == vm else 'arcade %s' % (ma.get(g, '') or '?'))
                out.append('\t'.join([mod, m['perso'], m['coup'], ref['ismes'] if ref else '', g, vs, str(vm), vme, str(e), v, va,
                                      ref['page'] if ref else '', ref['revid'] if ref else '', ref['date'] if ref else '']))
    open(sortie, 'w').write('\n'.join(out) + '\n')


def synthese(ecarts_tsv, sortie, etal_txt=None):
    """FRAME-DATA.md : tableau par perso et par coup (verdict par grandeur), compteurs"""
    import collections
    rows = list(csv.DictReader(open(ecarts_tsv), delimiter='\t'))
    G = ['demarrage', 'actif', 'recuperation', 'avantage_garde', 'avantage_contact', 'degats']
    L = ['# Frame data des persos ajoutés — écarts à SuperCombo', '',
         'Source : SuperCombo Wiki, pages « Street Fighter Alpha 3/<perso> » (API MediaWiki publique, révision `revid` '
         'et date de relevé dans `ecarts.tsv`). Mesure : `outils/frame_data.py` (convention en tête du fichier), '
         'étalonnée sur Ryu et Ken à l\'arcade sfa3ud (`etalonnage.txt`, `etalonnage_ecarts.tsv`).', '',
         'Cellule : `=` conforme, `±n` écart après étalonnage, `nm` non mesurable (cause dans `ecarts.tsv`), '
         '`(m)` valeur mesurée sans référence publiée ; « arcade » = même mesure que l\'arcade sfa3ud quand le perso y existe.', '']
    par = collections.OrderedDict()
    for r in rows:
        par.setdefault((r['module'], r['perso']), collections.OrderedDict()).setdefault(r['coup'], {})[r['grandeur']] = r
    tot = collections.Counter()
    pos_tot = len(L)
    for (mod, p), coups in par.items():
        if mod in ('ref3', 'ro3') and p not in ('Ryu', 'Ken'):
            continue
        if p in ('Ryu', 'Ken'):
            if mod != 'ref3':
                continue
            L += ['## Étalonnage : %s (arcade sfa3ud)' % p, '']
        else:
            L += ['## %s (%s)' % (p, mod), '']
        L += ['| coup | ' + ' | '.join(G) + ' | arcade |', '|---' * (len(G) + 2) + '|']
        for c, g in coups.items():
            cel, arc = [], set()
            for x in G:
                r = g.get(x)
                if not r:
                    cel.append(''); continue
                v = r['verdict']
                k = 'étalonnage' if p in ('Ryu', 'Ken') else 'ajoutés'
                if v == 'conforme':
                    cel.append('= %s' % r['mesure_etalonnee']); tot[(k, 'conforme')] += 1
                elif v.startswith('écart'):
                    cel.append('%s (%s/%s)' % (v.split()[1], r['mesure_etalonnee'], r['supercombo'])); tot[(k, 'écart')] += 1
                elif 'pas de frame data' in v:
                    cel.append('(m) %s' % r['mesure_etalonnee'] if r['mesure_etalonnee'] else 'nm'); tot[(k, 'sans référence')] += 1
                else:
                    cel.append('nm'); tot[(k, 'non mesurable')] += 1
                if r.get('arcade_sfa3ud'):
                    arc.add(r['arcade_sfa3ud'])
            L.append('| %s | %s | %s |' % (c, ' | '.join(cel), '= arcade' if arc == {'= arcade'} else ', '.join(sorted(arc - {'= arcade'}))))
        L.append('')
    for k in ('étalonnage', 'ajoutés'):
        L.insert(pos_tot, 'Totaux %s (grandeurs) : ' % k + ', '.join('%s %d' % (kv[0][1], kv[1]) for kv in tot.most_common() if kv[0][0] == k) + '\n')
    open(sortie, 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'plan':
        plan(a[1], a[2])
    elif a[0] == 'mesure':
        mesure(a[1], a[2], a[3])
    elif a[0] == 'ecarts':
        ecarts(a[2:], a[1])
    elif a[0] == 'etalonne':   # etalonne <ecarts_arcade.tsv> <sortie> <mesures...> : applique l'etalonnage
        e, n = etalonnage(a[1])
        print('étalonnage (à ajouter à la mesure) :', e, 'sur', n)
        ecarts(a[3:], a[2], e)
    elif a[0] == 'synthese':
        synthese(a[1], a[2])
