#!/usr/bin/env python3
"""(banc_coups) ORCHESTRATEUR : banc_coups.sh <module> [perso] [version]

  module : ro3 (SFA3 traduit, oracle arcade sfa3ud), ro5 (Upper : persos de SFA3 contre l'arcade, persos propres a
           Upper au critere « sort, se termine, rend le controle »), ro9 (Hyper : versions Z, Z2, A, Z3)
  perso  : nom du tableau (« Ryu », « M. Bison »...) ou « tous » (defaut)
  version: ro3 / ro5 : isme X, A ou V (defaut : les trois) ; ro9 : Z, Z2, A, Z3 (defaut : les quatre)

Chaque travail (perso, isme / version) : plan (outils/plan.py) -> MAME de la traduction (+ arcade si oracle, journal
arcade mis en cache par empreinte du plan) -> verdicts (outils/compare.py) dans resultats/<module>/<perso>_<v>.tsv.
Au plus MAXMAME (defaut 4) MAME en parallele. Puis tableau.py refait les tableaux et le resume.
"""
import hashlib, os, subprocess, sys, csv
from concurrent.futures import ThreadPoolExecutor
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, 'outils'))
import plan as P

LUA = os.path.join(B, 'lua', 'banc_coups.lua')
VERSION_JOURNAL = 'j1'
JEUX9 = {'Z': ['Street Fighter Alpha'], 'Z2': ['Street Fighter Alpha 2'],
         'A': ['Street Fighter Alpha 2', 'Street Fighter Alpha 2 Gold'], 'Z3': ['Street Fighter Alpha 3']}
# grille des versions d'Hyper (tournee_hyper.lua, INDEX-HYPER §1.2) : 4 colonnes par perso de base, id $102 ou $FF
VERS = [0x30,0x40,0x60,0x00,0x31,0x41,0x61,0x01,0x32,0x42,0x62,0x02,0x33,0x43,0x63,0x03,0x34,0x44,0x64,0x04,0x35,0x45,0x65,0x05,0x36,0x46,0x66,0x06,0x37,0x47,0x67,0x07,0x38,0x48,0x68,0x08,0x39,0x49,0x69,0x09,0x3a,0x4a,0x6a,0x0a,0x3b,0x4b,0x6b,0x0b,0x3c,0x4c,0x6c,0x0c,0x4d,0x6d,0x0d,0xff,0x4e,0x6e,0x0e,0xff,0x4f,0x6f,0x0f,0xff,0x50,0x70,0x10,0xff,0x51,0x71,0x11,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x15,0xff,0xff,0xff,0x7e,0x16,0xff,0xff,0x57,0x77,0x17,0xff,0x18,0xff,0xff,0xff,0x19,0xff,0xff,0xff,0x1a,0xff,0xff,0xff,0x1b,0xff,0xff,0xff,0x1c,0xff,0xff,0xff,0x1d,0xff,0xff,0xff,0x1e,0xff,0xff,0xff,0x1f,0xff,0xff,0xff,0x20,0xff,0xff,0xff,0x21,0xff,0xff,0xff,0x22,0xff,0xff,0xff,0x23,0xff,0xff,0xff]


def famille9(i):
    return 'Z3' if i < 0x30 else 'Z' if i < 0x40 else 'Z2' if i < 0x60 else 'A'


def versions_hyper(base, ver):
    """id $102 d'Hyper du perso de base dans la famille ver (Z, Z2, A, Z3x), ou None"""
    if base is None or base < 0 or base * 4 + 3 >= len(VERS):
        return None
    for c in range(4):
        i = VERS[base * 4 + c]
        if i != 0xff and famille9(i) == (ver if ver in ('Z', 'Z2', 'A') else 'Z3'):
            return i
    return None


PERSOS_SFA3 = ['Ryu', 'Ken', 'Akuma', 'Charlie', 'Chun-Li', 'Adon', 'Sodom', 'Guy', 'Birdie', 'Rose', 'M. Bison', 'Sagat',
               'Dan', 'Sakura', 'Rolento', 'Dhalsim', 'Zangief', 'Gen', 'Balrog', 'Cammy', 'E. Honda', 'Blanka',
               'R. Mika', 'Cody', 'Vega', 'Karin']
PROPRES_UPPER = ['Juli', 'Juni']   # persos du tableau absents de l'arcade SFA3 (Guile, Fei-Long, Dee Jay... n'y sont pas)


def nomf(s):
    return s.replace('. ', '').replace(' ', '').replace('-', '')


def lance(dossier, module, plan, env):
    os.makedirs(dossier, exist_ok=True)
    cmd = [os.path.join(B, 'lance.sh'), dossier, module, LUA, 'PLAN=' + plan] + ['%s=%s' % kv for kv in env.items()]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.join(dossier, 'log.txt')


def travail(module, perso, ver, pool):
    """renvoie la ligne de resume du travail"""
    pid = P.IDS_SFA3.get(perso)
    rep = os.path.join(B, 'essais', module, '%s_%s' % (nomf(perso), ver))
    os.makedirs(rep, exist_ok=True)
    plan, index = os.path.join(rep, 'plan.txt'), os.path.join(rep, 'index.tsv')
    env = {}
    oracle = None
    if module in ('ro3', 'ro5'):
        rows = P.selection('Street Fighter Alpha 3', perso, ver)
        P.ecrit(rows, plan, index, ver, 'Street Fighter Alpha 3', perso)
        env = {'PERSO': '%02x' % pid, 'PERSO2': '00', 'ISM': ver}
        # Juli / Juni : leur code est dans l'arcade (poupees de Bison) et ils y jouent forces par $102 -> oracle pour
        # ro3 ; dans Upper ce sont des persos propres (animations refaites : 25 pas differents) -> critere sans oracle
        if not (module == 'ro5' and perso in PROPRES_UPPER):
            oracle = ('ref3', env, False)
    else:   # ro9 : versions Z, Z2, A, Z3X / Z3A / Z3V (ZERO 3 et son isme)
        jeux = JEUX9[ver[:2] if ver.startswith('Z3') else ver]
        ism = ver[2] if ver.startswith('Z3') else None
        rows = []
        for j in jeux:
            rows += P.selection(j, perso, ism)
        if ver == 'A':   # ALPHA = Alpha 2 Gold : lignes de Gold, et celles d'Alpha 2 que Gold ne redefinit pas
            gold = set(r['nom_du_coup'] for r in rows if r['jeu'].endswith('Gold'))
            rows = [r for r in rows if r['jeu'].endswith('Gold') or r['nom_du_coup'] not in gold]
        P.ecrit(rows, plan, index, ism, '/'.join(jeux), perso)
        base = pid if pid is not None else 0
        env = {'LISTE': '%02x.%s%s/00.Z3' % (base, ver[:2] if ism else ver, ('.i' + ism) if ism else '')}
        if ism:
            oracle = ('ref3', {'PERSO': '%02x' % base, 'PERSO2': '00', 'ISM': ism}, True)
    ntest = sum(1 for l in open(plan))
    if ntest == 0:
        return '%s %s %s : aucun essai' % (module, perso, ver)
    # ORACLE=refjp : oracle japonais 980727 au lieu de sfa3ud (resultats/<module>-jp) ; le journal de la traduction est
    # repris s'il a ete fait avec le meme plan (empreinte gardee a cote), sinon rejoue
    ORA = os.environ.get('ORACLE', 'ref3')
    if oracle and ORA != 'ref3':
        oracle = (ORA,) + oracle[1:]
    trlog = os.path.join(rep, module, 'log.txt'); emp = os.path.join(rep, module, 'plan.md5')
    hp = hashlib.md5(open(plan).read().encode()).hexdigest()
    if os.path.exists(trlog) and os.path.exists(emp) and open(emp).read() == hp and 'FIN' in open(trlog).read()[-30:]:
        futs = [pool.submit(lambda: trlog)]
    else:
        futs = [pool.submit(lambda: (lance(os.path.join(rep, module), module, plan, env), open(emp, 'w').write(hp))[0])]
    ref = None
    if oracle:
        # cle du cache arcade : plan + selection + VERSION_JOURNAL (a changer si le journal Lua change de sens ;
        # les champs ajoutes en fin de ligne F ne l'invalident pas)
        h = hashlib.md5((open(plan).read() + repr(sorted(oracle[1].items())) + VERSION_JOURNAL).encode()).hexdigest()[:12]
        cache = os.path.join(B, 'essais', 'cache_arcade' + ('' if oracle[0] == 'ref3' else '_' + oracle[0]),
                             '%s_%s_%s' % (nomf(perso), ver, h))
        if os.path.exists(os.path.join(cache, 'log.txt')) and 'FIN' in open(os.path.join(cache, 'log.txt')).read()[-20:]:
            ref = os.path.join(cache, 'log.txt')
        else:
            futs.append(pool.submit(lance, cache, oracle[0], plan, oracle[1]))
    logs = [f.result() for f in futs]
    tr = logs[0]
    if oracle and ref is None:
        ref = logs[1]
    modres = module + ('' if not oracle or oracle[0] == 'ref3' else '-' + oracle[0][3:])
    os.makedirs(os.path.join(B, 'resultats', modres), exist_ok=True)
    sortie = os.path.join(B, 'resultats', modres, '%s_%s.tsv' % (nomf(perso), ver))
    cmd = ['python3', os.path.join(B, 'outils', 'compare.py'), '--index', index, '--tr', tr, '--module', modres,
           '--sortie', sortie]
    if oracle:
        cmd += ['--ref', ref] + (['--famille'] if oracle[2] else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    return '%s %-10s %-3s %s' % (module, perso, ver, r.stdout.strip() or r.stderr.strip()[-300:])


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    module = a[0]
    perso = a[1] if len(a) > 1 else 'tous'
    vers = [a[2]] if len(a) > 2 else (['X', 'A', 'V'] if module in ('ro3', 'ro5') else ['Z', 'Z2', 'A', 'Z3'])
    if module == 'ro9':
        vers = sum([['Z3X', 'Z3A', 'Z3V'] if v == 'Z3' else [v] for v in vers], [])
    if perso == 'tous':
        persos = PERSOS_SFA3 + (PROPRES_UPPER if module in ('ro3', 'ro5') else [])
        if module == 'ro9':
            persos = sorted(set(persos) | {'Evil Ryu'})
    else:
        persos = [perso]
    jobs = []
    reprise = os.environ.get('REPRISE') == '1'   # REPRISE=1 : saute les travaux dont le resultat existe deja
    for p in persos:
        for v in vers:
            if reprise and os.path.exists(os.path.join(B, 'resultats', module + ('-' + os.environ['ORACLE'][3:] if os.environ.get('ORACLE', 'ref3') != 'ref3' else ''), '%s_%s.tsv' % (nomf(p), v))):
                continue
            if module == "ro9" and versions_hyper(P.IDS_SFA3.get(p, -1), v) is None:
                continue
            jobs.append((p, v))
    nm = int(os.environ.get('MAXMAME', '4'))
    mame = ThreadPoolExecutor(nm)
    with ThreadPoolExecutor(max(1, nm // 2)) as tp:
        for ligne in tp.map(lambda j: travail(module, j[0], j[1], mame), jobs):
            print(ligne, flush=True)
    mame.shutdown()
    subprocess.run(['python3', os.path.join(B, 'outils', 'tableau.py')])


if __name__ == '__main__':
    main()
