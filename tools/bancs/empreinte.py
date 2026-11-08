#!/usr/bin/env python3
"""empreinte.py — EMPREINTE de ce qu'un émulateur charge réellement (bancs qui prouvent ce qu'ils mesurent).

Incident du 01/11 : banc_coups/lance.sh ignorait MAXDIR, le banc des données d'images a mesuré max6 au lieu de max39
sans que rien ne le signale. D'où : l'empreinte est calculée sur la LIGNE DE COMMANDE effective (pas sur la variable
qu'on croit avoir passée), écrite en tête des résultats, et comparée à l'empreinte attendue.

Ce qui entre dans l'empreinte :
  MAME / cps2f : dossier du jeu trouvé par -rompath (ou ./roms) + nom du jeu (dossier ou .zip) -> ROM programme
                 (fichiers *.03* … *.10*, liens résolus) ; + blocs ext_*.bin de BANC_DIR et HSFA_EXT (lus par le fork
                 et le Lua des bancs) ;
  FBNeo        : hsfa_run <coeur.so> <jeu.zip> / retroarch -L <coeur.so> <jeu.zip> -> md5 du zip (+ coeur à part) ;
  PPSSPP/PCSX2 : fichier de contenu (.iso/.cso/.chd/.elf/.pbp) ; au-delà de 256 Mo, « md5r » = md5(taille + 64 premiers
                 Mo + 64 derniers Mo).
  E = md5 de la liste triée « md5  rôle/nom » -> 12 premiers chiffres = l'empreinte courte.

Attendu (variables d'environnement, ou options) :
  ATTENDU_MD5=<hexa, 8 chiffres au moins>  : préfixe de E, du md5 programme, du md5 de la ROM .03c ou du md5 du zip ;
  ATTENDU_REF=<nom|chemin>                 : référence nommée (references.tsv à côté de ce script, ex. v153/ro5, max45,
                                             ro9a21) ou dossier figé / zip : l'empreinte attendue y est CALCULÉE (et le
                                             dossier contrôlé contre son MD5SUMS / MD5_COPIE.txt s'il en a un).

Usage :
  empreinte.py commande [--sortie F] -- <commande de l'émulateur…>
  empreinte.py dossier <dossier figé | zip>       empreinte d'une référence (pour remplir ATTENDU_MD5)
  empreinte.py attendu                            résout ATTENDU_MD5 / ATTENDU_REF
  empreinte.py crc -- <commande>                  CRC32 de la ROM programme 0-0x400000 (pour empreinte.lua)
Code de sortie : 0 OK ; 86 = EMPREINTE DIFFÉRENTE (le banc doit s'arrêter ; 86 n'est utilisé ni par MAME ni par
  timeout) ; 2 = usage / rien de reconnu.
API Python : calcule_commande(argv, env, cwd), calcule_dossier(d), attendu(env), verifie(e, att), ligne(e).
"""
import glob
import hashlib
import os
import re
import sys
import zipfile
import zlib

ICI = os.path.dirname(os.path.abspath(__file__))
H = os.environ.get('HSFA_WORKSPACE') or os.path.expanduser('~/hsfa')   # racine de l'espace de travail
EMUS_MAME = re.compile(r'^(mame[\w.-]*|cps2f[\w.-]*)$', re.I)
EMUS_FB = re.compile(r'^(hsfa_run|retroarch[\w.-]*)$', re.I)
EMUS_PSP = re.compile(r'^(ppsspp[\w.-]*)$', re.I)
EMUS_PS2 = re.compile(r'^(pcsx2[\w.-]*)$', re.I)
PROG = re.compile(r'\.(0[3-9]|10)[a-z]?$', re.I)       # ROM programme CPS2 : sz3ud.03c … sz3.10b
GROS = 256 << 20


def type_emu(argv):
    """(indice, type) du 1er mot qui est un émulateur connu (après timeout, nice, env…), sinon (None, None)"""
    for i, a in enumerate(argv):
        b = os.path.basename(a)
        for t, rx in (('mame', EMUS_MAME), ('fbneo', EMUS_FB), ('ppsspp', EMUS_PSP), ('pcsx2', EMUS_PS2)):
            if rx.match(b):
                return i, t
    return None, None


def md5f(p):
    """md5 d'un fichier ; « md5r » (rapide) au-delà de 256 Mo"""
    h = hashlib.md5()
    t = os.path.getsize(p)
    with open(p, 'rb') as f:
        if t <= GROS:
            for b in iter(lambda: f.read(1 << 20), b''):
                h.update(b)
            return h.hexdigest()
        h.update(str(t).encode())
        h.update(f.read(64 << 20))
        f.seek(-(64 << 20), 2)
        h.update(f.read())
    return 'r' + h.hexdigest()[1:]


def _ext(dossiers):
    vus, r = set(), []
    for d in dossiers:
        if d and os.path.isdir(d):
            for p in sorted(glob.glob(os.path.join(d, 'ext_*.bin'))):
                rp = os.path.realpath(p)
                if os.path.basename(p) not in vus:
                    vus.add(os.path.basename(p))
                    r.append(('ext/' + os.path.basename(p), rp))
    return r


def _prog_dossier(d):
    return [('prog/' + n, os.path.realpath(os.path.join(d, n))) for n in sorted(os.listdir(d))
            if PROG.search(n) and os.path.isfile(os.path.join(d, n))]


def _prog_zip(z):
    """ROM programme dans un zip MAME : md5 du contenu de chaque membre"""
    r = []
    with zipfile.ZipFile(z) as zf:
        for n in sorted(zf.namelist()):
            if PROG.search(n):
                r.append(('prog/' + os.path.basename(n), hashlib.md5(zf.read(n)).hexdigest()))
    return r


def _assemble(parts, info):
    """parts = [(rôle/nom, chemin ou md5 déjà calculé)] -> dict empreinte"""
    lignes = []
    for nom, x in parts:
        m = x if re.fullmatch(r'r?[0-9a-f]{32}', x or '') else md5f(x)
        lignes.append((nom, m))
    lignes.sort()
    e = dict(info)
    e['fichiers'] = lignes
    e['E'] = hashlib.md5(''.join('%s  %s\n' % (m, n) for n, m in lignes).encode()).hexdigest()
    pr = [m for n, m in lignes if n.startswith('prog/')]
    ex = [m for n, m in lignes if n.startswith('ext/')]
    e['prog'] = hashlib.md5(''.join(pr).encode()).hexdigest() if pr else ''
    e['ext'] = (len(ex), hashlib.md5(''.join(ex).encode()).hexdigest()[:8]) if ex else (0, '')
    e['03c'] = next((m for n, m in lignes if re.search(r'\.03[a-z]?$', n)), '')
    e['04c'] = next((m for n, m in lignes if re.search(r'\.04[a-z]?$', n)), '')
    e['zip'] = next((m for n, m in lignes if n.startswith('zip/')), '')
    return e


def _rompaths(argv, cwd):
    rp = None
    for i, a in enumerate(argv):
        if a in ('-rompath', '-rp', '--rompath') and i + 1 < len(argv):
            rp = argv[i + 1]
    if rp is None:
        rp = 'roms'
    return [os.path.normpath(os.path.join(cwd, x)) for x in rp.split(';') if x]


def _jeu_mame(argv, i):
    """1er argument après l'exécutable qui n'est ni une option ni la valeur d'une option"""
    k = i + 1
    while k < len(argv):
        a = argv[k]
        if a.startswith('-'):
            k += 2 if k + 1 < len(argv) and not argv[k + 1].startswith('-') and a not in BOOL_MAME else 1
            continue
        return a
    return None


BOOL_MAME = {'-nothrottle', '-skip_gameinfo', '-window', '-nowindow', '-debug', '-verbose', '-log', '-oslog',
             '-nomax', '-noreadconfig', '-nofilter', '-cheat', '-console'}


def calcule_commande(argv, env=None, cwd=None):
    env = os.environ if env is None else env
    cwd = cwd or os.getcwd()
    i, t = type_emu(argv)
    if t is None:
        return None
    emu = os.path.basename(argv[i])
    if t == 'mame':
        jeu = _jeu_mame(argv, i)
        if not jeu:
            return None
        for rp in _rompaths(argv, cwd):
            d, z = os.path.join(rp, jeu), os.path.join(rp, jeu + '.zip')
            if os.path.isdir(d):
                parts = _prog_dossier(d)
                src = os.path.realpath(d)
                break
            if os.path.isfile(z):
                parts = _prog_zip(z) + [('zip/' + jeu + '.zip', os.path.realpath(z))]
                src = os.path.realpath(z)
                break
        else:
            return {'erreur': 'jeu %s introuvable dans -rompath %s' % (jeu, ';'.join(_rompaths(argv, cwd)))}
        bd = env.get('BANC_DIR')
        if not bd and env.get('REF') != '1' and '-autoboot_script' in argv:
            bd = H + '/work/mame/'   # PIÈGE : sans BANC_DIR, banc_mem.lua charge les ext de work/mame/ (reconstruit)
        parts += _ext([bd, env.get('HSFA_EXT')])
        return _assemble(parts, {'emu': emu, 'jeu': jeu, 'source': src})
    # autres : contenu = arguments qui sont des fichiers existants
    parts, coeur = [], ''
    for k, a in enumerate(argv[i + 1:], i + 1):
        p = os.path.join(cwd, a)
        if not os.path.isfile(p):
            continue
        if a.endswith('.so') or a.endswith('.dll'):
            coeur = md5f(p)
        elif re.search(r'\.(zip|iso|cso|chd|elf|pbp|bin|7z)$', a, re.I):
            parts.append(('zip/' + os.path.basename(a), os.path.realpath(p)))
    if not parts:
        return {'erreur': 'aucun fichier de contenu reconnu dans la commande'}
    e = _assemble(parts, {'emu': emu, 'jeu': os.path.basename(parts[0][1]), 'source': parts[0][1]})
    e['coeur'] = coeur
    return e


def _dossier_jeu(d):
    for s in ('roms_fork/sfa3hx', 'roms_tr/sfa3ud', 'roms_ro5/sfa3ud', 'roms_ro9/sfa3ud', 'b9/roms_ro9/sfa3ud',
              'roms_fork/sfa3ud', 'sfa3ud', 'sfa3hx', ''):
        p = os.path.join(d, s)
        if os.path.isdir(p) and any(PROG.search(n) for n in os.listdir(p)):
            return p
    return None


def references():
    r = {}
    f = os.path.join(ICI, 'references.tsv')
    if os.path.exists(f):
        for l in open(f, encoding='utf-8'):
            x = l.rstrip('\n').split('\t')
            if len(x) >= 2 and not l.startswith('#'):
                r[x[0]] = x[1]
    return r


def resout_ref(nom):
    """nom de référence -> chemin (dossier figé ou zip)"""
    if os.path.exists(nom):
        return os.path.abspath(nom)
    R = references()
    if nom in R:
        return R[nom]
    for c in (os.path.join(H, 'work/references', nom), os.path.join(H, 'work/banc_coups', nom),
              os.path.join(H, 'work/greffe_arcade/constructions', nom + '_fige'),
              os.path.join(H, 'work/greffe_arcade/constructions', nom)):
        if os.path.exists(c):
            return c
    return None


def controle_sommes(d):
    """compare les fichiers programme / ext du dossier à son MD5SUMS / MD5_COPIE.txt (ou à celui de la version) ;
    renvoie la liste des écarts (vide = conforme ou rien à contrôler)"""
    ecarts = []
    for base in (d, os.path.dirname(d)):
        for nom in ('MD5SUMS', 'MD5_COPIE.txt'):
            f = os.path.join(base, nom)
            if not os.path.isfile(f):
                continue
            for l in open(f, errors='replace'):
                x = l.split(None, 1)
                if len(x) != 2:
                    continue
                p = os.path.normpath(os.path.join(base, x[1].strip()))
                if not p.startswith(d.rstrip('/') + '/'):
                    continue
                b = os.path.basename(p)
                if (PROG.search(b) or re.match(r'ext_.*\.bin$', b)) and os.path.isfile(p) and md5f(p) != x[0]:
                    ecarts.append('%s : %s au lieu de %s (%s)' % (p, md5f(p)[:8], x[0][:8], nom))
            return ecarts
    return ecarts


def calcule_dossier(d):
    d = os.path.abspath(d)
    if os.path.isfile(d):
        # zip / iso de référence : seul le md5 du fichier compte (les zips FBNeo ne sont pas des jeux MAME)
        return _assemble([('zip/' + os.path.basename(d), d)], {'emu': '-', 'jeu': os.path.basename(d), 'source': d})
    j = _dossier_jeu(d)
    if not j:
        return {'erreur': 'pas de ROM programme sous %s' % d}
    ext_d = os.path.join(d, 'b9') if os.path.isdir(os.path.join(d, 'b9')) else d
    e = _assemble(_prog_dossier(j) + _ext([ext_d]), {'emu': '-', 'jeu': os.path.basename(j), 'source': os.path.realpath(j)})
    e['controle'] = controle_sommes(d)
    return e


def ligne(e):
    if 'erreur' in e:
        return '# empreinte: ERREUR %s' % e['erreur']
    s = '# empreinte: %s | %s %s | source=%s' % (e['E'][:12], e['emu'], e['jeu'], e['source'])
    if e.get('prog'):
        s += ' | prog=%s 03c=%s 04c=%s' % (e['prog'][:12], e['03c'][:8], e['04c'][:8])
    if e.get('ext') and e['ext'][0]:
        s += ' | ext=%d:%s' % e['ext']
    if e.get('zip'):
        s += ' | zip=%s' % e['zip'][:12]
    if e.get('coeur'):
        s += ' | coeur=%s' % e['coeur'][:12]
    return s


def attendu(env=None):
    """-> (description, ensemble de valeurs acceptées, empreinte complète de la référence ou None) ; (None, None, None)"""
    env = os.environ if env is None else env
    if env.get('ATTENDU_REF'):
        p = resout_ref(env['ATTENDU_REF'])
        if not p:
            raise SystemExit('empreinte : référence inconnue ATTENDU_REF=%s (voir %s/references.tsv)' % (env['ATTENDU_REF'], ICI))
        e = calcule_dossier(p)
        if 'erreur' in e:
            raise SystemExit('empreinte : référence %s : %s' % (p, e['erreur']))
        if e.get('controle'):
            raise SystemExit('empreinte : la référence %s ne correspond plus à ses sommes :\n  %s' % (p, '\n  '.join(e['controle'])))
        return 'ref %s (%s)' % (env['ATTENDU_REF'], e['E'][:12]), None, e
    if env.get('ATTENDU_MD5'):
        v = env['ATTENDU_MD5'].strip().lower()
        if not re.fullmatch(r'[0-9a-f]{8,32}', v):
            raise SystemExit('empreinte : ATTENDU_MD5 invalide (%s) : 8 à 32 chiffres hexadécimaux' % v)
        return 'md5 %s' % v, v, None
    return None, None, None


def verifie(e, env=None):
    """-> (ok, message). Sans attendu : ok."""
    desc, v, ref = attendu(env)
    if desc is None:
        return True, 'aucune empreinte attendue (ATTENDU_MD5 / ATTENDU_REF) : non vérifiée'
    if 'erreur' in e:
        return False, 'empreinte incalculable : %s' % e['erreur']
    if ref is not None:
        ok = (ref['prog'], ref['ext']) == (e['prog'], e['ext']) if ref.get('prog') else ref.get('zip') == e.get('zip')
        if ok:
            return True, 'conforme à %s' % desc
        diff = [n for n, m in dict(e['fichiers']).items() if dict(ref['fichiers']).get(n) != m]
        diff += [n for n in dict(ref['fichiers']) if n not in dict(e['fichiers'])]
        return False, ('EMPREINTE DIFFÉRENTE : chargé %s (source %s), attendu %s (source %s) ; fichiers différents : %s'
                       % (e['E'][:12], e['source'], desc, ref['source'], ', '.join(sorted(set(diff), key=lambda n: (not n.startswith('prog/'), n))[:8]) or '?'))
    cands = [e.get(k, '') for k in ('E', 'prog', '03c', 'zip')]
    if any(c.lstrip('r').startswith(v) or c.startswith(v) for c in cands if c):
        return True, 'conforme à %s' % desc
    return False, ('EMPREINTE DIFFÉRENTE : chargé E=%s prog=%s 03c=%s zip=%s (source %s), attendu %s'
                   % (e['E'][:12], e.get('prog', '')[:12], e.get('03c', '')[:12], e.get('zip', '')[:12], e['source'], desc))


def crc_prog(e):
    """CRC32 (zlib) de la ROM programme telle que le 68000 la voit de 0 à 0x400000 (03c en 0, 04c en 0x80000…)"""
    noms = sorted((n for n, m in e['fichiers'] if n.startswith('prog/')),
                  key=lambda n: int(re.search(r'\.(\d\d)[a-z]?$', n).group(1)))
    src = e['source']
    c = 0
    for n in noms:
        p = os.path.join(src, n[5:]) if os.path.isdir(src) else None
        b = open(p, 'rb').read() if p else zipfile.ZipFile(src).read([x for x in zipfile.ZipFile(src).namelist() if x.endswith(n[5:])][0])
        s = bytearray(len(b))      # fichiers CPS2 = mots échangés (ROM_LOAD16_WORD_SWAP) : le 68000 lit b[1], b[0]
        s[0::2], s[1::2] = b[1::2], b[0::2]
        c = zlib.crc32(bytes(s), c)
    return '%08x' % c


def principal(args):
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    cmd = args[0]
    if cmd == 'dossier':
        e = calcule_dossier(args[1])
        print(ligne(e))
        if e.get('controle'):
            print('ATTENTION, écarts avec les sommes du dossier :\n  ' + '\n  '.join(e['controle']))
            return 86
        return 0 if 'erreur' not in e else 2
    if cmd == 'attendu':
        print(attendu()[0] or 'aucune')
        return 0
    if cmd in ('commande', 'crc'):
        sortie = None
        k = 1
        while k < len(args) and args[k] != '--':
            if args[k] == '--sortie':
                sortie = args[k + 1]
                k += 1
            k += 1
        argv = args[k + 1:]
        e = calcule_commande(argv)
        if e is None:
            print('empreinte : aucun émulateur reconnu dans la commande', file=sys.stderr)
            return 2
        if cmd == 'crc':
            print(crc_prog(e))
            return 0
        l = ligne(e)
        ok, msg = verifie(e)   # toujours : sans ATTENDU_*, ok (« non vérifiée »)
        if sortie:
            with open(sortie, 'w') as f:
                f.write(l + '\n' + ('# attendu: %s\n' % msg if msg else ''))
        print(l)
        if not ok:
            print('ARRÊT DU BANC : ' + msg, file=sys.stderr)
            return 86
        if msg:
            print('# attendu: ' + msg)
        return 0
    print('commande inconnue : %s' % cmd, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(principal(sys.argv[1:]))
