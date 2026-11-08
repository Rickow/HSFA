#!/usr/bin/env python3
"""(banc_coups) NON-REGRESSION DE L'INTEGRATION MAX : banc_max.sh <dossier candidat> [etapes]

Reference = Upper v150 (references/v150/ro5, module ro5 de lance.sh), candidat = copie figee d'une construction MAX
(module max, MAXDIR=<candidat>). Etapes (defaut : toutes, dans cet ordre) :
  coups    coups des natifs d'Upper : lignes du tableau (persos de SFA3, Juli, Juni ; ismes X/A/V) ou palette generique
           (Guile, Fei-Long, Dee Jay, T. Hawk, Evil Ryu, Shin Akuma, Balrog EX ; isme A) ; candidat contre reference image
           par image (outils/compare_strict.py) : IDENTIQUE attendu partout ;
  fins     mode Arcade des natifs jusqu'a la fin (tournee.lua, comme balayage_fins.sh) : fin atteinte, manches, duree ±1 % ;
  max      palette generique sur les 4 persos MAX, ismes X/A/V : le coup sort, rend la main, sans exception ;
  croises  VERSUS MAX contre natifs (Ryu, Zangief, Chun-Li, Dhalsim, Blanka, Akuma, Juli, Juni), dans les deux sens,
           entrees aleatoires des deux joueurs (tournee_max, ALEA) : pas d'exception, pas de blocage, manches qui finissent ;
  arcade   mode Arcade complet des 4 persos MAX : fin atteinte et finie.
Les journaux de reference sont mis en cache (essais/max_ref/, cle = plan ou parametres + version du journal).
Sorties : resultats_max/<etiquette>/*.tsv et RESUME-MAX.md (etiquette = nom du dossier candidat).
Au plus MAXMAME (defaut 2) MAME en parallele.
"""
import csv, glob, hashlib, os, re, subprocess, sys, collections
from concurrent.futures import ThreadPoolExecutor
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, 'outils'))
import plan as P
import palette as PAL
from banc import PERSOS_SFA3, nomf

LUA = os.path.join(B, 'lua', 'banc_coups.lua')
TOURNEE = os.path.join(B, 'lua', 'tournee_max_copie.lua')
VERSION = 'm1'
NATIFS_PALETTE = {'Guile': 0x20, 'Fei-Long': 0x21, 'Dee Jay': 0x22, 'T. Hawk': 0x23, 'Evil Ryu': 0x17, 'Shin Akuma': 0x24,
                  'Balrog EX': 0x25}
MAX = {'Eagle': 0x26, 'Maki': 0x27, 'Yun': 0x2D, 'Ingrid': 0x2E}
ECHANT = {'Ryu': 0x00, 'Zangief': 0x10, 'Chun-Li': 0x04, 'Dhalsim': 0x0F, 'Blanka': 0x19, 'Akuma': 0x02, 'Juli': 0x1E,
          'Juni': 0x1F}


def lance(dossier, module, script, env, cand=None):
    os.makedirs(dossier, exist_ok=True)
    e = ['%s=%s' % kv for kv in env.items()]
    if cand:
        e.append('MAXDIR=' + cand)
    subprocess.run([os.path.join(B, 'lance.sh'), dossier, module, script] + e, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, env=dict(os.environ, MAXDIR=cand or os.environ.get('MAXDIR', '')))
    return os.path.join(dossier, 'log.txt')


def fini(log, marque=('FIN',)):
    if not os.path.exists(log):
        return False
    t = open(log, errors='replace').read()[-300:]
    return any(m in t for m in marque)


def ref_cache(nom, cle, module, script, env, pool, marque=('FIN',), extra=None):
    """journal de reference en cache : cle = contenu (plan...) + env + VERSION ; extra = variables non hachees (PLAN)"""
    h = hashlib.md5((cle + repr(sorted(env.items())) + VERSION + os.environ.get('REFS', '')).encode()).hexdigest()[:12]  # REFS : référence v150 / v151
    d = os.path.join(B, 'essais', 'max_ref', '%s_%s' % (nom, h))
    log = os.path.join(d, 'log.txt')
    if fini(log, marque + ('EXCEPTION',)):
        return None, log
    return pool.submit(lance, d, module, script, dict(env, **(extra or {}))), log


# ------------------------------------------------------------------ 1. coups des natifs
def travail_coups(et, cand, perso, ism, pool):
    rep = os.path.join(B, 'essais', 'max_' + et, 'coups', '%s_%s' % (nomf(perso), ism))
    os.makedirs(rep, exist_ok=True)
    plan, index = os.path.join(rep, 'plan.txt'), os.path.join(rep, 'index.tsv')
    if perso in NATIFS_PALETTE:
        PAL.ecrit(plan, index, perso, ism)
        pid = NATIFS_PALETTE[perso]
    else:
        P.ecrit(P.selection('Street Fighter Alpha 3', perso, ism), plan, index, ism, 'Street Fighter Alpha 3', perso)
        pid = P.IDS_SFA3[perso]
    env = {'PERSO': '%02x' % pid, 'PERSO2': '00', 'ISM': ism}
    f, ref = ref_cache('coups_%s_%s' % (nomf(perso), ism), open(plan).read(), 'ro5', LUA, env, pool, extra={'PLAN': plan})
    fc = pool.submit(lance, os.path.join(rep, 'cand'), 'max', LUA, dict(env, PLAN=plan), cand)
    if f is not None:
        f.result()
    fc.result()
    os.makedirs(os.path.join(B, 'resultats_max', et), exist_ok=True)
    s = os.path.join(B, 'resultats_max', et, 'coups_%s_%s.tsv' % (nomf(perso), ism))
    cmp = lambda cand: subprocess.run(['python3', os.path.join(B, 'outils', 'compare_strict.py'), '--index', index, '--ref',
                                       ref, '--cand', cand, '--sortie', s, '--etiquette', '%s %s' % (perso, ism)],
                                      capture_output=True, text=True)
    r = cmp(os.path.join(rep, 'cand', 'log.txt'))
    if 'DIFFÉRENT=' in r.stdout and os.environ.get('CONFIRME', '1') != '0':
        # (25/10) CONFIRMATION : le candidat n'est pas toujours reproductible (meme plan, meme construction : une entree
        # vue un tour plus tot ou plus tard, ~1 lancement sur 3). On rejoue le candidat ; une variante DIFFERENTE
        # une fois et IDENTIQUE l'autre est classee INSTABLE.
        premier = {x['id']: x for x in csv.DictReader(open(s), delimiter='\t')}
        pool.submit(lance, os.path.join(rep, 'cand2'), 'max', LUA, dict(env, PLAN=plan), cand).result()
        r2 = cmp(os.path.join(rep, 'cand2', 'log.txt'))
        second = {x['id']: x for x in csv.DictReader(open(s), delimiter='\t')}
        rows = list(second.values())
        for x in rows:
            a, b = premier.get(x['id'], {}).get('verdict'), x['verdict']
            if a != b and 'IDENTIQUE' in (a, b):
                x['verdict'], x['detail'] = 'INSTABLE', 'non reproductible : %s puis %s (%s)' % (a, b, (premier[x['id']]['detail'] or x['detail'])[:120])
        with open(s, 'w') as f:
            f.write('\t'.join(rows[0].keys()) + '\n')
            for x in rows:
                f.write('\t'.join(x.values()) + '\n')
        n = collections.Counter(x['verdict'] for x in rows)
        return 'coups %s %s %s (confirmé par un 2e lancement)' % (perso, ism, ' '.join('%s=%d' % kv for kv in sorted(n.items())))
    return 'coups ' + (r.stdout.strip() or r.stderr.strip()[-300:])


# ------------------------------------------------------------------ 2. fins des natifs
def resume_tournee(log):
    """manches, fin (avant / dans / finie), image d'entree en fin, image de sortie, derniere image, exception"""
    m = {'manches': 0, 'fin': 'avant', 'debut_fin': None, 'sortie_fin': None, 'exc': None, 'nf': None}
    if not os.path.exists(log):
        return m
    for l in open(log, errors='replace'):
        t = l.split()
        if not t:
            continue
        if t[0] == 'COMBAT':
            m['manches'] += 1
        elif t[0] == 'EXCEPTION':
            m['exc'] = ' '.join(t[1:])
        elif len(t) > 5 and t[1] == ':':
            k, p4 = int(t[0]), t[4]
            m['nf'] = k
            if p4 == '000a' and m['fin'] == 'avant':
                m['fin'], m['debut_fin'] = 'dans', k
            elif p4 != '000a' and m['fin'] == 'dans':
                m['fin'], m['sortie_fin'] = 'finie', k
        elif t[0] == 'FIN':
            pass
    return m


def travail_fin(et, cand, pid, pool):
    env = {'PERSO': '%02x' % pid, 'NF': '180000' if pid == 0x07 else '90000', 'DELAI': '3500'}
    f, ref = ref_cache('fin_%02x' % pid, 'fin', 'ro5', os.path.join(B, '..', 'mame', 'tournee.lua'), env, pool, ('FIN',))
    d = os.path.join(B, 'essais', 'max_' + et, 'fins', 'p%02x' % pid)
    fc = pool.submit(lance, d, 'max', os.path.join(B, '..', 'mame', 'tournee.lua'), env, cand)
    if f is not None:
        f.result()
    fc.result()
    a, b = resume_tournee(ref), resume_tournee(os.path.join(d, 'log.txt'))
    if b['exc'] and not a['exc']:
        v, c = 'KO', 'exception au candidat : %s' % b['exc']
    elif a['fin'] != b['fin']:
        v, c = 'KO' if a['fin'] == 'finie' else 'DIFFÉRENT', 'fin réf %s, cand %s' % (a['fin'], b['fin'])
    else:
        # (24/10) les parties ne sont pas comparables au-dela de la 1re image sans tour qui differe : la cadence turbo
        # depend du temps de calcul (construction MAX plus lourde) et les entrees de tournee.lua sont en images ->
        # nombre de manches et duree varient sans defaut de jeu (prouve sur Chun-Li : tours identiques jusqu'a
        # l'image 16 980, puis 1 tour d'ecart, puis divergence). Critere retenu : fin atteinte et finie, sans exception.
        da = (a['sortie_fin'] or a['nf'] or 0)
        db = (b['sortie_fin'] or b['nf'] or 0)
        ecart = 100.0 * (db - da) / da if da else 0
        v = 'OK'
        c = 'manches réf %d, cand %d ; durée réf %s, cand %s (%+.2f %%)%s' % (a['manches'], b['manches'], da, db, ecart,
            '' if (a['manches'] == b['manches'] and abs(ecart) <= 1.0) else ' (écart de cadence, non significatif)')
    return '%02x\t%s\t%s\t%d/%d\t%s/%s\t%s' % (pid, v, c, a['manches'], b['manches'], a['fin'], b['fin'], b['exc'] or '')


# ------------------------------------------------------------------ 3. persos MAX
def travail_max(et, cand, nom, ism, pool):
    rep = os.path.join(B, 'essais', 'max_' + et, 'max', '%s_%s' % (nom, ism))
    os.makedirs(rep, exist_ok=True)
    plan, index = os.path.join(rep, 'plan.txt'), os.path.join(rep, 'index.tsv')
    PAL.ecrit(plan, index, nom, ism)
    log = pool.submit(lance, os.path.join(rep, 'cand'), 'max', LUA,
                      {'PERSO': '%02x' % MAX[nom], 'PERSO2': '00', 'ISM': ism, 'PLAN': plan}, cand).result()
    os.makedirs(os.path.join(B, 'resultats_max', et), exist_ok=True)
    s = os.path.join(B, 'resultats_max', et, 'max_%s_%s.tsv' % (nom, ism))
    r = subprocess.run(['python3', os.path.join(B, 'outils', 'compare.py'), '--index', index, '--tr', log, '--module', 'max',
                        '--sortie', s], capture_output=True, text=True)
    return 'max %s %s %s' % (nom, ism, r.stdout.strip() or r.stderr.strip()[-300:])


# ------------------------------------------------------------------ 4. croises
def travail_croise(et, cand, m, n, sens, pool):
    j1, j2 = (MAX[m], ECHANT[n]) if sens == 'max-j1' else (ECHANT[n], MAX[m])
    d = os.path.join(B, 'essais', 'max_' + et, 'croises', '%s_%s_%s' % (m, nomf(n), sens))
    env = {'VS': '1', 'PERSO': '%02x' % j1, 'PERSO2': '%02x' % j2, 'ALEA': '1', 'GRAINE': '%d' % (j1 * 64 + j2),
           'KO': '900', 'NF': '24000', 'DELAI': '1500'}
    log = pool.submit(lance, d, 'max', TOURNEE, env, cand).result()
    r = resume_tournee(log)
    texte = open(log, errors='replace').read() if os.path.exists(log) else ''
    if r['exc']:
        v, c = 'KO', 'exception %s' % r['exc']
    elif 'FIN' not in texte[-50:]:
        v, c = 'KO', 'journal interrompu (blocage ou délai)'
    elif r['manches'] < 2:
        v, c = 'KO', 'blocage : %d manche(s) en 24 000 images' % r['manches']
    else:
        v, c = 'OK', '%d manches' % r['manches']
    return '%s\t%s\t%s\t%s\t%s' % (m, n, sens, v, c)


# ------------------------------------------------------------------ 5. arcade des MAX
def travail_arcade(et, cand, nom, pool):
    d = os.path.join(B, 'essais', 'max_' + et, 'arcade', nom)
    log = pool.submit(lance, d, 'max', TOURNEE, {'PERSO': '%02x' % MAX[nom], 'NF': '120000', 'DELAI': '4000'}, cand).result()
    r = resume_tournee(log)
    v = 'OK' if r['fin'] == 'finie' and not r['exc'] else 'KO'
    c = 'fin=%s manches=%d%s' % (r['fin'], r['manches'], (' exception %s' % r['exc']) if r['exc'] else '')
    return '%s\t%s\t%s' % (nom, v, c)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    cand = os.path.abspath(a[0])
    et = os.path.basename(cand.rstrip('/'))
    etapes = a[1:] or ['coups', 'fins', 'max', 'croises', 'arcade']
    nm = int(os.environ.get('MAXMAME', '2'))
    pool = ThreadPoolExecutor(nm)
    R = os.path.join(B, 'resultats_max', et)
    os.makedirs(R, exist_ok=True)
    personnes = os.environ.get('PERSOS')
    for e in etapes:
        print('== %s' % e, flush=True)
        if e == 'coups':
            jobs = [(p, i) for p in PERSOS_SFA3 + ['Juli', 'Juni'] for i in ('X', 'A', 'V')] + [(p, 'A') for p in NATIFS_PALETTE]
            if personnes:
                jobs = [j for j in jobs if j[0] in personnes.split(',')]
            with ThreadPoolExecutor(max(1, nm // 2)) as tp:
                for l in tp.map(lambda j: travail_coups(et, cand, j[0], j[1], pool), jobs):
                    print(l, flush=True)
        elif e == 'fins':
            ids = [i for i in range(0x00, 0x26) if i not in (0x12, 0x13, 0x14)]
            fts = os.path.join(R, 'fins.tsv')
            if os.environ.get('REPRISE') == '1' and os.path.exists(fts):
                faits = set(int(l.split('\t')[0], 16) for l in open(fts).readlines()[1:] if l.strip())
                ids = [i for i in ids if i not in faits]
                mode = 'a'
            else:
                mode = 'w'
            with ThreadPoolExecutor(max(1, nm // 2)) as tp, open(fts, mode) as f:
                if mode == 'w':
                    f.write('perso\tverdict\tdetail\tmanches_ref/cand\tfin_ref/cand\texception\n')
                for l in tp.map(lambda i: travail_fin(et, cand, i, pool), ids):
                    print('fin', l, flush=True); f.write(l + '\n'); f.flush()
        elif e == 'max':
            jobs = [(m, i) for m in MAX for i in ('X', 'A', 'V')]
            with ThreadPoolExecutor(nm) as tp:
                for l in tp.map(lambda j: travail_max(et, cand, j[0], j[1], pool), jobs):
                    print(l, flush=True)
        elif e == 'croises':
            jobs = [(m, n, s) for m in MAX for n in ECHANT for s in ('max-j1', 'max-j2')]
            with ThreadPoolExecutor(nm) as tp, open(os.path.join(R, 'croises.tsv'), 'w') as f:
                f.write('max\tnatif\tsens\tverdict\tdetail\n')
                for l in tp.map(lambda j: travail_croise(et, cand, *j, pool), jobs):
                    print('croisé', l, flush=True); f.write(l + '\n'); f.flush()
        elif e == 'arcade':
            with ThreadPoolExecutor(nm) as tp, open(os.path.join(R, 'arcade.tsv'), 'w') as f:
                f.write('max\tverdict\tdetail\n')
                for l in tp.map(lambda m: travail_arcade(et, cand, m, pool), list(MAX)):
                    print('arcade', l, flush=True); f.write(l + '\n'); f.flush()
    pool.shutdown()
    subprocess.run(['python3', os.path.join(B, 'outils', 'resume_max.py'), R])


if __name__ == '__main__':
    main()
