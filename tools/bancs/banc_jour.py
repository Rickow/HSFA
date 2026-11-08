#!/usr/bin/env python3
"""banc_jour.py — BANC DE JOUR : non-régression des jeux sur les dernières versions FIGÉES (lancé par banc_jour.sh).

La machine ne tourne jamais la nuit : l'utilisateur lance le banc le matin, il doit finir dans BUDGET_H (défaut 8 h).
Étapes (banc_jour.conf ; --etapes pour choisir) :
  sfa3_cmd     SFA3 (ro3) : test des commandes arcade <-> traduction (commandes.lua, 42 actions, 0 différente attendue)
  sfa3_fins    SFA3 (ro3) : Arcade des 32 persos jusqu'à la fin (tournee.lua) : fin finie, captures = arcade ±1
  upper_fins   Upper (ro5) : Arcade des 40 persos : fin finie, sans exception
  hyper_vs     Hyper (ro9) : parties VERSUS (tournee_hyper.lua du dépôt) : sans exception
  greffe_fins  greffe ro9a figée : 85 parties Arcade (81 + Guy ×4) : fin A aboutie (durée comparée au banc précédent)
  max_arcade   Upper MAX (dernier lot validé) : Arcade des 4 persos MAX : fin finie
  max_croises  Upper MAX : VERSUS MAX contre 8 natifs, deux sens, entrées aléatoires : ≥ 2 manches, sans exception
  max_fins     Upper MAX : Arcade des 35 natifs : fin finie (comme banc_max « fins »)
Chaque partie passe par banc_jour_lance.sh -> lance_emu (places globales, étiquette banc_jour, registre) avec
l'EMPREINTE attendue de la version figée : une seule différence ARRÊTE TOUT le banc (RESUME « ARRÊTÉ »).
Sorties : work/banc_jour/AAAA-MM-JJ/ : etapes/<étape>.tsv, parties/<étape>/<clé>/ (journaux), RESUME.md (une page),
journal.txt. Comparaison : au dernier banc de jour qui a les MÊMES empreintes (régression = OK devenu KO ; « changé » =
mesure différente : même ROM + même script devraient donner le même journal).

  banc_jour.sh --sec                     essai à blanc : ce qui serait lancé, empreintes attendues, durée estimée
  banc_jour.sh [--etapes a,b] [--cles 00,01] [--limite N] [--places P] [--budget H] [--sortie DIR]
"""
import argparse
import collections
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import empreinte as EM  # noqa: E402

H = os.environ.get('HSFA_WORKSPACE') or os.path.expanduser('~/hsfa')   # racine de l'espace de travail
W = H + '/work'
LANCE = os.path.join(ICI, 'banc_jour_lance.sh')
TOURNEE = W + '/mame/tournee.lua'
CMD_LUA = W + '/mame/commandes.lua'
HYPER_LUA = H + '/github/tools/hyper-etats/tournee_hyper.lua'
MAX_LUA = W + '/banc_coups/lua/tournee_max_copie.lua'
G = W + '/greffe_arcade'
ORDRE = ['sfa3_cmd', 'sfa3_fins', 'upper_fins', 'hyper_vs', 'greffe_fins', 'max_arcade', 'max_croises', 'max_fins']
# durées estimées par partie (s, une place), mesurées le 01/11 sur cette machine (12 cœurs, charge ~6) ; voir ETAT outillage
EST = {'sfa3_cmd': 20, 'sfa3_fins': 70, 'upper_fins': 270, 'hyper_vs': 40, 'greffe_fins': 90, 'max_arcade': 500,
       'max_croises': 120, 'max_fins': 360}
MAX_IDS = {'Eagle': 0x26, 'Maki': 0x27, 'Yun': 0x2D, 'Ingrid': 0x2E}
ECHANT = {'Ryu': 0x00, 'Zangief': 0x10, 'Chun-Li': 0x04, 'Dhalsim': 0x0F, 'Blanka': 0x19, 'Akuma': 0x02, 'Juli': 0x1E,
          'Juni': 0x1F}


# ------------------------------------------------------------------ configuration
def lit_conf(f):
    c = {'VERSION': 'v153', 'GREFFE': 'auto', 'GREFFE_TABLE': '', 'MAX_VALIDE': '', 'PLACES_BANC': '5', 'BUDGET_H': '8',
         'ETAPES': ' '.join(ORDRE)}
    if os.path.exists(f):
        for l in open(f, encoding='utf-8'):
            m = re.match(r'^\s*([A-Z_]+)=(.*?)\s*(#.*)?$', l)
            if m:
                c[m.group(1)] = m.group(2).strip('"\'')
    return c


def greffe_figee(nom):
    if nom and nom != 'auto':
        return os.path.join(G, 'constructions', nom if nom.endswith('_fige') else nom + '_fige')
    def num(p):
        m = re.search(r'ro9a(\d+)([a-z]?)_fige$', p)
        return (int(m.group(1)), m.group(2)) if m else (-1, '')
    c = [p for p in glob.glob(os.path.join(G, 'constructions', 'ro9a*_fige')) if os.path.isfile(os.path.join(p, 'MD5SUMS'))]
    return max(c, key=num) if c else None


def graine_pc(c):
    """= greffe_arcade/outils/oracle_ro9a.sh : adresse image de la copie de 0x24F9D0 (variante de liste d'Upper)"""
    J = json.load(open(os.path.join(c, 'greffe.json')))
    n = [int(nn, 16) + 0x24f9d0 - int(a, 16) for a, b, nn in J['blocs'] if int(a, 16) <= 0x24f9d0 < int(b, 16)][0]
    for l in open(os.path.join(c, 'b9', 'carte_image.txt')):
        p = l.split(None, 2)
        if n <= int(p[1], 16) < n + 0x200:
            return p[0]
    raise SystemExit('graine PC introuvable pour %s' % c)


# ------------------------------------------------------------------ plan
def plan(conf, etapes):
    R = os.path.join(W, 'references', conf['VERSION'])
    gf = greffe_figee(conf['GREFFE'])
    mx = os.path.join(W, 'banc_coups', conf['MAX_VALIDE']) if conf.get('MAX_VALIDE') else None
    refs = {'ro3': os.path.join(R, 'ro3'), 'ro5': os.path.join(R, 'ro5'), 'ro9': os.path.join(R, 'ro9'), 'greffe': gf, 'max': mx}
    J = []

    def job(et, cle, module, lua, env, est=None):
        base = {'REFS': R}
        if module == 'greffe':
            base['GREFFE_C'] = gf
        if module == 'max':
            base['MAXDIR'] = mx
        J.append({'etape': et, 'cle': cle, 'module': module, 'lua': lua, 'env': dict(base, **env),
                  'attendu': refs[module], 'est': est or EST[et]})
    for et in etapes:
        if et == 'sfa3_cmd':
            job(et, 'commandes', 'ro3', CMD_LUA, {'DELAI': '1200'})
        elif et == 'sfa3_fins':
            for p in range(32):
                job(et, '%02x' % p, 'ro3', TOURNEE, {'PERSO': '%02x' % p, 'FORCE': 'Lff8540=ffffffff', 'NF': '40000' if p == 7 else '24000',
                                                     'SNAPP': '150', 'SNAPFIN': '1', 'DELAI': '1500'}, EST[et] * (2 if p == 7 else 1))
        elif et == 'upper_fins':
            for p in range(40):
                job(et, '%02x' % p, 'ro5', TOURNEE, {'PERSO': '%02x' % p, 'NF': '180000' if p == 7 else '90000', 'DELAI': '3500'},
                    EST[et] * (2 if p == 7 else 1))
        elif et == 'hyper_vs':
            for i, li in enumerate(['00.A/01.Z,02.Z/03.Z', '00.Z/01.Z2,01.Z/00.Z2,00.Z2/01.A']):
                job(et, 'vs%d' % (i + 1), 'ro9', HYPER_LUA, {'LISTE': li, 'MODEJEU': '1', 'NF': '20000', 'HSFA_BANC_LUA': W + '/mame',
                                                             'DELAI': '2400'})
        elif et == 'greffe_fins':
            if not gf:
                continue
            pc = graine_pc(gf)
            for l in open(os.path.join(G, 'e23', 'liste_sans07.txt')).read().split('\n') + \
                    open(os.path.join(G, 'e23', 'liste_07.txt')).read().split('\n'):
                if not l.strip():
                    continue
                p, v = l.split()
                guy = p == '07'
                job(et, '%s_%s' % (p, v), 'greffe', os.path.join(G, 'lua', 'graine_pc.lua'),
                    {'PERSO': '%s.%s' % (p, v), 'SNAPETAT': '1', 'LUA_BASE': os.path.join(G, 'lua', 'tournee_arcade.lua'),
                     'GRAINE_PC': pc, 'FORCE_ADR': 'ff8120=32,ff8123=82', 'SCENEA_PASSIF': '1', 'BLOCAGE': '20000', 'ARRET_FIN': '1',
                     'NF': '120000' if guy else '45000', 'DELAI': '14000' if guy else '6000'}, EST[et] * (3 if guy else 1))
        elif et == 'max_arcade' and mx:
            for n, i in MAX_IDS.items():
                job(et, n, 'max', MAX_LUA, {'PERSO': '%02x' % i, 'NF': '120000', 'DELAI': '4000'})
        elif et == 'max_croises' and mx:
            for m, im in MAX_IDS.items():
                for n, i_n in ECHANT.items():
                    for sens in ('max-j1', 'max-j2'):
                        j1, j2 = (im, i_n) if sens == 'max-j1' else (i_n, im)
                        job(et, '%s_%s_%s' % (m, n.replace('-', ''), sens), 'max', MAX_LUA,
                            {'VS': '1', 'PERSO': '%02x' % j1, 'PERSO2': '%02x' % j2, 'ALEA': '1', 'GRAINE': '%d' % (j1 * 64 + j2),
                             'KO': '900', 'NF': '24000', 'DELAI': '1500'})
        elif et == 'max_fins' and mx:
            for p in [i for i in range(0x26) if i not in (0x12, 0x13, 0x14)]:
                job(et, '%02x' % p, 'max', TOURNEE, {'PERSO': '%02x' % p, 'NF': '180000' if p == 7 else '90000', 'DELAI': '3500'},
                    EST[et] * (2 if p == 7 else 1))
    return J, refs


# ------------------------------------------------------------------ verdicts
def resume_tournee(log):
    """= banc_coups/outils/banc_max.py : manches, fin (avant / dans / finie), images, exception"""
    m = {'manches': 0, 'fin': 'avant', 'debut_fin': None, 'sortie_fin': None, 'exc': None, 'nf': None, 'FIN': False}
    if not os.path.exists(log):
        return m
    for l in open(log, errors='replace'):
        t = l.split()
        if not t:
            continue
        if t[0] == 'COMBAT':
            m['manches'] += 1
        elif t[0] == 'EXCEPTION':
            m['exc'] = ' '.join(t[1:])[:80]
        elif t[0] == 'FIN':
            m['FIN'] = True
        elif len(t) > 5 and t[1] == ':':
            try:
                k = int(t[0])
            except ValueError:
                continue
            p4 = t[4]
            m['nf'] = k
            if p4 == '000a' and m['fin'] == 'avant':
                m['fin'], m['debut_fin'] = 'dans', k
            elif p4 != '000a' and m['fin'] == 'dans':
                m['fin'], m['sortie_fin'] = 'finie', k
    return m


REF_CAPT = {}


def verdict(j, d):
    """-> (OK|KO, mesure comparable, détail)"""
    log = os.path.join(d, 'log.txt')
    et = j['etape']
    if et == 'sfa3_cmd':
        U = H + '/github/src/hsfa'
        r = subprocess.run(['python3', '-B', os.path.join(U, 'commandes.py'), W + '/mame/cmd_ref.txt', log], capture_output=True, text=True)
        t = (r.stdout.strip().splitlines() or ['?'])[-1]
        m = re.search(r'(\d+) actions?, (\d+) diff', r.stdout)
        ok = bool(m) and m.group(2) == '0'
        return ('OK' if ok else 'KO'), (m.group(0) if m else '?'), t[:100]
    if et in ('sfa3_fins', 'upper_fins', 'max_fins', 'max_arcade'):
        r = resume_tournee(log)
        mes = 'manches=%d fin=%s sortie=%s' % (r['manches'], r['fin'], r['sortie_fin'])
        ok = r['fin'] == 'finie' and not r['exc']
        det = (' exception %s' % r['exc']) if r['exc'] else ''
        if et == 'sfa3_fins':
            if not REF_CAPT:
                for l in open(W + '/balayages/ref_sfa3_captures.txt'):
                    x = l.split()
                    if len(x) >= 2:
                        REF_CAPT[x[0]] = int(x[1])
            n = len(glob.glob(os.path.join(d, 'tmp', 'snap', '*', '*.png')))
            ref = REF_CAPT.get(j['cle'])
            mes += ' captures=%d' % n
            if ref is None or abs(n - ref) > 1:
                ok = False
                det += ' captures %d, arcade %s' % (n, ref)
        return ('OK' if ok else 'KO'), mes, det.strip()
    if et == 'hyper_vs':
        t = open(log, errors='replace').read() if os.path.exists(log) else ''
        n = len(re.findall(r'^MANCHE', t, re.M))
        exc = re.search(r'^EXC\S*\s+(.*)$', t, re.M)
        ok = not exc and re.search(r'^FIN', t, re.M) is not None
        return ('OK' if ok else 'KO'), 'manches=%d' % n, ('exception ' + exc.group(1)[:60]) if exc else ('' if ok else 'pas de FIN')
    if et == 'greffe_fins':
        t = open(log, errors='replace').read() if os.path.exists(log) else ''
        f = re.search(r'FIN_A (\d+) duree (\d+) scene (\w+)', t)
        e = re.search(r'EXCEPTION (\d+) pc=(\w+)', t)
        b = re.search(r'BLOQUE (\d+)', t)
        if f:
            return 'OK', 'duree=%s' % f.group(2), ''
        return 'KO', 'non aboutie', ('exception image %s pc=%s' % (e.group(1), e.group(2))) if e else \
            ('BLOQUE %s' % b.group(1)) if b else 'fin non atteinte'
    if et == 'max_croises':
        r = resume_tournee(log)
        if r['exc']:
            return 'KO', 'exception', r['exc']
        if not r['FIN']:
            return 'KO', 'interrompu', 'journal interrompu (blocage ou délai)'
        return ('OK' if r['manches'] >= 2 else 'KO'), 'manches=%d' % r['manches'], '' if r['manches'] >= 2 else 'blocage'
    return 'KO', '?', 'étape inconnue'


# ------------------------------------------------------------------ comparaison au banc précédent
def precedent(sortie, etape, emp):
    racine = os.path.dirname(sortie)
    for d in sorted(glob.glob(os.path.join(racine, '20??-??-??*')), reverse=True):
        if os.path.abspath(d) == os.path.abspath(sortie):
            continue
        f = os.path.join(d, 'etapes', etape + '.tsv')
        if not os.path.exists(f):
            continue
        L = open(f, encoding='utf-8').read().splitlines()
        if not L or not L[0].startswith('# empreinte: ') or L[0].split()[2] != emp:
            continue
        return os.path.basename(d), {x.split('\t')[0]: x.split('\t') for x in L[2:] if x.strip()}
    return None, {}


def table_greffe(conf):
    """durées de référence de la greffe (tableau du dernier balayage de l'agent, même construction) : cle -> 'duree=N'"""
    f = conf.get('GREFFE_TABLE')
    r = {}
    if f and os.path.exists(f):
        for l in open(f, encoding='utf-8'):
            x = [c.strip() for c in l.split('|')]
            if len(x) > 8 and re.fullmatch(r'[0-9a-f]{2}', x[1]) and x[8] == 'aboutie':
                r['%s_%s' % (x[1], x[2])] = 'duree=%s' % x[5]
    return r


# ------------------------------------------------------------------ exécution
def avec_d(j, d):
    """variables qui dépendent du dossier de la partie (graine de la greffe : jamais dans le dossier de l'agent)"""
    return dict(j['env'], **({'GRAINE_OUT': os.path.join(d, 'graine.txt')} if j['module'] == 'greffe' else {}))


def commande_texte(j, d):
    env = ' '.join('%s=%s' % kv for kv in sorted(avec_d(j, d).items()))
    return 'ATTENDU_REF=%s HSFA_AGENT=banc_jour %s %s %s %s %s' % (j['attendu'], LANCE, d, j['module'], j['lua'], env)


def simule(J, P):
    """durée totale estimée (ordonnancement « plus long d'abord » sur P places)"""
    t = [0] * P
    for j in sorted(J, key=lambda x: -x['est']):
        k = t.index(min(t))
        t[k] += j['est']
    return max(t) if J else 0


def principal():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sec', action='store_true', help='essai à blanc : affiche ce qui serait lancé')
    ap.add_argument('--etapes')
    ap.add_argument('--cles', help='clés à garder (ex. 00,01,Eagle)')
    ap.add_argument('--limite', type=int, help='au plus N parties par étape')
    ap.add_argument('--places', type=int)
    ap.add_argument('--budget', type=float, help='heures')
    ap.add_argument('--sortie')
    ap.add_argument('--conf', default=os.path.join(ICI, 'banc_jour.conf'))
    a = ap.parse_args()
    conf = lit_conf(a.conf)
    etapes = (a.etapes or conf['ETAPES']).replace(',', ' ').split()
    etapes = [e for e in ORDRE if e in etapes]
    P = a.places or int(conf['PLACES_BANC'])
    budget = 3600 * (a.budget or float(conf['BUDGET_H']))
    J, refs = plan(conf, etapes)
    if a.cles:
        k = set(a.cles.split(','))
        J = [j for j in J if j['cle'] in k]
    if a.limite:
        n = collections.Counter()
        J2 = []
        for j in J:
            n[j['etape']] += 1
            if n[j['etape']] <= a.limite:
                J2.append(j)
        J = J2
    jour = datetime.date.today().isoformat()
    sortie = os.path.abspath(a.sortie or os.path.join(W, 'banc_jour', jour))

    # empreintes attendues (et intégrité des références figées) AVANT tout lancement
    emp, probl = {}, []
    for m in sorted(set(j['module'] for j in J)):
        p = refs[m]
        if not p:
            probl.append('%s : version figée non définie (banc_jour.conf)' % m)
            continue
        e = EM.calcule_dossier(p)
        if 'erreur' in e:
            probl.append('%s : %s' % (m, e['erreur']))
            continue
        if e.get('controle'):
            probl.append('%s : la référence ne correspond plus à ses sommes : %s' % (m, '; '.join(e['controle'][:3])))
        emp[m] = e
    outils = {os.path.basename(f): hashlib.md5(open(f, 'rb').read()).hexdigest()[:8]
              for f in sorted(set(j['lua'] for j in J)) if os.path.exists(f)}

    par_et = collections.OrderedDict()
    for j in J:
        par_et.setdefault(j['etape'], []).append(j)
    if a.sec:
        print('BANC DE JOUR — ESSAI À BLANC (%s) ; sortie prévue : %s' % (jour, sortie))
        print('places du banc : %d (lance_emu : %s) ; budget %.1f h' % (P, subprocess.run([os.path.join(ICI, 'lance_emu'), '--places'],
                                                                         capture_output=True, text=True).stdout.strip(), budget / 3600))
        for m, e in emp.items():
            print('empreinte attendue %-6s %s' % (m, EM.ligne(e)[13:]))
        for x in probl:
            print('PROBLÈME : ' + x)
        print('scripts Lua : ' + ', '.join('%s %s' % kv for kv in outils.items()))
        for et, L in par_et.items():
            print('\n== %s : %d partie(s), ~%d s chacune, %.1f h-place ; ex. :' % (et, len(L), L[0]['est'], sum(j['est'] for j in L) / 3600))
            for j in L[:2]:
                print('   ' + commande_texte(j, os.path.join(sortie, 'parties', et, j['cle'])))
            if len(L) > 2:
                print('   … clés : ' + ' '.join(j['cle'] for j in L[2:])[:200])
        tot = simule(J, P)
        print('\nTOTAL : %d parties, durée estimée %.1f h sur %d places (budget %.1f h)%s' % (
            len(J), tot / 3600, P, budget / 3600, '' if tot <= budget else ' -> DÉPASSE : les dernières parties seront « NON FAITES »'))
        return 0 if not probl else 1
    if probl:
        print('banc_jour : ARRÊT avant lancement :\n  ' + '\n  '.join(probl), file=sys.stderr)
        return 86

    os.makedirs(os.path.join(sortie, 'etapes'), exist_ok=True)
    jl = open(os.path.join(sortie, 'journal.txt'), 'a')
    verrou = threading.Lock()

    def log(s):
        with verrou:
            jl.write('%s %s\n' % (time.strftime('%H:%M:%S'), s))
            jl.flush()
    t0 = time.time()
    log('début : %d parties, étapes %s, %d places, budget %.1f h' % (len(J), ','.join(par_et), P, budget / 3600))
    arret = threading.Event()
    res = {}

    def un(j):
        cle = (j['etape'], j['cle'])
        if arret.is_set():
            res[cle] = ('NON FAIT', '', 'banc arrêté', 0)
            return
        if time.time() - t0 + j['est'] > budget:
            res[cle] = ('NON FAIT', '', 'budget', 0)
            log('NON FAIT (budget) %s %s' % cle)
            return
        d = os.path.join(sortie, 'parties', j['etape'], j['cle'])
        s = time.time()
        env = dict(os.environ, ATTENDU_REF=j['attendu'], HSFA_AGENT='banc_jour')
        env.pop('ATTENDU_MD5', None)
        r = subprocess.run([LANCE, d, j['module'], j['lua']] + ['%s=%s' % kv for kv in avec_d(j, d).items()],
                           env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        du = time.time() - s
        if r.returncode == 86:
            arret.set()
            msg = open(os.path.join(d, 'empreinte.txt')).read().strip() if os.path.exists(os.path.join(d, 'empreinte.txt')) else '?'
            att = [l[10:].strip() for l in msg.splitlines() if l.startswith('# attendu:')]
            res[cle] = ('EMPREINTE', '', (att[0] if att else msg.replace('\n', ' '))[:400], du)
            log('ARRÊT : empreinte différente %s %s : %s' % (cle[0], cle[1], msg))
            subprocess.run([os.path.join(ICI, 'lance_emu'), '--arrete', 'banc_jour', '--delai', '5'], capture_output=True)
            return
        v, mes, det = verdict(j, d)
        if r.returncode != 0 and v == 'OK':
            det = (det + ' ; code de sortie %d' % r.returncode).strip(' ;')
        elif r.returncode != 0:
            det = (det + ' ; code de sortie %d (mame.txt)' % r.returncode).strip(' ;')
        res[cle] = (v, mes, det, du)
        log('%s %s %s %s %s (%.0f s)' % (v, cle[0], cle[1], mes, det, du))
    ordre = sorted(J, key=lambda x: (ORDRE.index(x['etape']), -x['est']))
    with ThreadPoolExecutor(P) as tp:
        list(tp.map(un, ordre))
    t1 = time.time()

    # ------------------------------------------------------------------ résultats
    lignes, regs, chg, nonf = [], [], [], []
    tab_g = table_greffe(conf)
    for et, L in par_et.items():
        m = L[0]['module']
        e = emp[m]
        dprec, prec = precedent(sortie, et, e['E'][:12])
        if not prec and et == 'greffe_fins' and tab_g:
            dprec, prec = 'tableau ' + os.path.basename(conf['GREFFE_TABLE']), {k: [k, 'OK', v] for k, v in tab_g.items()}
        with open(os.path.join(sortie, 'etapes', et + '.tsv'), 'w', encoding='utf-8') as f:
            f.write(EM.ligne(e) + '\n')
            f.write('cle\tverdict\tmesure\tdetail\tduree_s\n')
            n = collections.Counter()
            dur = 0
            for j in L:
                v, mes, det, du = res.get((et, j['cle']), ('NON FAIT', '', '', 0))
                f.write('%s\t%s\t%s\t%s\t%.0f\n' % (j['cle'], v, mes, det, du))
                n[v] += 1
                dur += du
                p = prec.get(j['cle'])
                if v == 'NON FAIT':
                    nonf.append('%s %s (%s)' % (et, j['cle'], det))
                elif v != 'OK' and (p is None or p[1] == 'OK'):
                    regs.append('%s %s : %s %s%s' % (et, j['cle'], v, det or mes, (' (OK le %s)' % dprec) if p else ''))
                elif v != 'OK':
                    regs.append('%s %s : %s %s (déjà KO le %s)' % (et, j['cle'], v, det or mes, dprec))
                elif p is not None and p[1] == 'OK' and len(p) > 2 and p[2] != mes:
                    chg.append('%s %s : %s -> %s' % (et, j['cle'], p[2], mes))
        lignes.append('| %s | %s %s | %d | %d | %d | %s | %.0f min |' % (
            et, m, e['E'][:12], len(L), n['OK'], len(L) - n['OK'] - n['NON FAIT'], dprec or '—', dur / 60))
    etat = 'ARRÊTÉ (empreinte)' if arret.is_set() else ('OK' if not regs else '%d RÉGRESSION(S) / KO' % len(regs))
    with open(os.path.join(sortie, 'RESUME.md'), 'w', encoding='utf-8') as f:
        f.write('# Banc de jour %s — %s\n\n' % (jour, etat))
        f.write('Début %s, fin %s, durée %.1f h (budget %.1f h), %d places. Versions : %s ; greffe %s ; Upper MAX %s.\n\n' % (
            time.strftime('%H:%M', time.localtime(t0)), time.strftime('%H:%M', time.localtime(t1)), (t1 - t0) / 3600, budget / 3600, P,
            conf['VERSION'], os.path.basename(refs['greffe'] or '—'), conf.get('MAX_VALIDE') or '—'))
        f.write('| étape | empreinte | parties | OK | KO | comparé à | durée cumulée |\n|---|---|---|---|---|---|---|\n')
        f.write('\n'.join(lignes) + '\n\n')
        if arret.is_set():
            f.write('## ARRÊT : empreinte différente\n\n' + '\n'.join('- %s %s : %s' % (k[0], k[1], r[2]) for k, r in res.items()
                                                                          if r[0] == 'EMPREINTE') + '\n\n')
        f.write('## Régressions / KO (%d)\n\n' % len(regs) + ('\n'.join('- ' + x for x in regs[:15]) or '- aucun') +
                ('\n- … %d de plus (etapes/*.tsv)' % (len(regs) - 15) if len(regs) > 15 else '') + '\n\n')
        f.write('## Changés depuis le banc précédent (%d)\n\n' % len(chg) + ('\n'.join('- ' + x for x in chg[:10]) or '- aucun') +
                ('\n- … %d de plus' % (len(chg) - 10) if len(chg) > 10 else '') + '\n\n')
        if nonf:
            f.write('## Non faits (%d)\n\n' % len(nonf) + ', '.join(nonf[:20]) + '\n\n')
        f.write('Empreintes complètes : `etapes/<étape>.tsv` (1re ligne) ; scripts Lua : %s ; journaux : `parties/`.\n' %
                ', '.join('%s %s' % kv for kv in outils.items()))
    log('fin : %s' % etat)
    print(open(os.path.join(sortie, 'RESUME.md'), encoding='utf-8').read())
    return 0 if etat == 'OK' else (86 if arret.is_set() else 1)


if __name__ == '__main__':
    sys.exit(principal())
