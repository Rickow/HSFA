#!/usr/bin/env python3
"""banc_ref.py — BANC UNIQUE de non-régression (banc_unique, 16/11) : une construction contre une référence, toutes
les parties jouées par UN SEUL lanceur (environnement vide, nvram / cfg neufs, -noreadconfig, contexte md5 par partie).

  banc_ref.sh CONSTRUCTION --contre REFERENCE [--jeu greffe|greffe_max|upper_max] [--parties a,b] [--cles k1,k2]
              [--echantillon] [--jumelle C2 --jumelle-ref R2] [--attendus F] [--upper [SERIE]] [--nom N]
              [--places P] [--heure-max HHMM] [--rejoue] [--rejoue-ref] [--sec]
  banc_ref.sh CONSTRUCTION --diag-sauve IMAGE --parties P --cles K     (DIAGNOSTIC : état sauvegardé par le Lua)
  banc_ref.sh CONSTRUCTION --diag-charge NOM [--parties P --cles K]    (DIAGNOSTIC : partie rejouée depuis l'état)

CONSTRUCTION / REFERENCE : chemin, ou nom (ro9a44_fige, ro9a44 -> greffe_arcade/constructions/ro9a44_fige ; max58 ->
banc_coups/max58). Jeu deviné : b9/ + greffe.json -> greffe (greffe_max si hsfa_gfx_max.bin) ; roms_fork/ +
env_max_cache.txt -> upper_max.
Parties (défaut : toutes celles du jeu) :
  greffe     versus (VERSUS témoin, 60 000 images, 90 captures ; = work/vs_fiable/harnais/vs_fiable.sh + Lua menu),
             training (MODEJEU=4, 1 500 images), fins (85 fins du banc des fins : sonde, captures, graine imposée ;
             = fins_greffe fin_banc), arcade (Arcade lancée par Start, Start au menu, Ken ZERO 3, sonde d'après combat ;
             = ro9a44 a44_01q), continue (J1 perd un combat puis CONTINUE, jusqu'à la fin), gameover (J1 perd sans
             continuer : GAME OVER puis retour au titre), j2 (un 2e joueur défie J1 pendant la carte d'Arcade), decors
             (40 décors ; EXIGE la jumelle TIRAGE_CPU=0 : --jumelle / --jumelle-ref), japonais (NON DISPONIBLE, motif écrit).
  upper_max  arcade (4 persos MAX), croises (64 VERSUS MAX contre natifs, entrées aléatoires), fins (35 natifs)
             (= banc_coups/banc_max.py et banc_jour : mêmes paramètres).
Menu : l'interrupteur MENU_CURSEUR_ARCADE est lu dans greffe.json (patch « MENU_CURSEUR_ARCADE ») ; la navigation
s'adapte (Lua menu : curseur attendu 0 ou 1 ; Arcade par Start : MENU_DIR=Up sans l'interrupteur) et le curseur à
l'arrivée est vérifié dans le verdict.
Cache : chaque partie de RÉFÉRENCE est rangée dans cache/<construction>_<empreinte>/<partie>/<clé>/ avec son contexte ;
elle est rejouée si son contexte change (cps2f, Lua, tuiles partagées, recette…) ou avec --rejoue-ref. Le CANDIDAT est
toujours rejoué (runs/<nom>/cand/…, reprise si même contexte et partie finie ; --rejoue pour tout refaire), puis versé
au cache s'il y manque. Comparaison : journal, fichiers de sonde (.sf, graine, sentinelles, menu, défi…) et captures
(md5), durée de la fin ; deux parties ne se comparent que si leurs lignes de BANC du contexte sont égales (sinon « NON
COMPARABLE »). Verdict de chaque partie indépendant de la comparaison (exception, blocage, scène non atteinte = KO).
Attendus (--attendus F) : lignes « partie<TAB>clé (motif fnmatch)<TAB>quoi (journal.txt|captures|<fichier>|*)<TAB>valeurs
(noms de captures, images de .sent, *, ou ~motif : expression rationnelle sur le détail, « _ » = espace) » ; une différence couverte est « attendue », sinon « à qualifier ».
Sortie : runs/<nom>/RESUME.md (+ resultats.tsv). Règles : nice 19, lance_emu --agent banc_unique, DISPLAY de l'atelier
écrit en dur (BANC_REF_DISPLAY, défaut :97), MAME jamais avec -state (états de DIAGNOSTIC seulement, par le Lua).
"""
import argparse, datetime, fnmatch, glob, hashlib, json, os, re, shutil, subprocess, sys, threading, time, bisect
from concurrent.futures import ThreadPoolExecutor

ICI = os.path.dirname(os.path.abspath(__file__))
H = os.environ.get('HSFA_WORKSPACE') or os.path.expanduser('~/hsfa')
W = H + '/work'
FORK = H + '/mame-fork/mame/cps2f'
MAME_LUA = W + '/mame'                       # banc_mem / banc_plans / banc_sprites (dofile en dur dans les tournées)
G = W + '/greffe_arcade'
MH = W + '/mesures_homologues'
AC = W + '/apres_combat'
BC = W + '/banc_coups'
LANCE = W + '/outils/lance_emu'
SONDE_PREP = W + '/fins_greffe/outils/sonde_prep.py'
CMP_UPPER = next((f for f in (os.path.join(ICI, '..', 'greffe-arcade', 'etape4', 'cmp_fins_upper.py'),
                               H + '/github/tools/greffe-arcade/etape4/cmp_fins_upper.py') if os.path.isfile(f)), None)
DISPLAY = os.environ.get('BANC_REF_DISPLAY', ':97')
AGENT = os.environ.get('BANC_REF_AGENT', 'banc_unique')
RECETTE = 'r1'
ATELIER = os.environ.get('BANC_REF_ATELIER') or W + '/banc_unique'   # cache/, runs/, etats/ (jamais dans le dépôt)
CACHE = os.path.join(ATELIER, 'cache')
RUNS = os.path.join(ATELIER, 'runs')
ETATS = os.path.join(ATELIER, 'etats')
LUAD = os.path.join(ICI, 'lua') if os.path.isdir(os.path.join(ICI, 'lua')) else os.path.join(ICI, 'banc_ref_lua')   # dépôt : banc_ref_lua/
LUA_MENU_VS = os.path.join(LUAD, 'tournee_hyper_guy_menu.lua')
LUA_MENU_ARC = os.path.join(LUAD, 'tournee_arcade_menu.lua')
LUA_DEFI = os.path.join(LUAD, 'defi_j2.lua')
LUA_DIAG = os.path.join(LUAD, 'etat_diag.lua')
PARTIES = {'greffe': ['versus', 'training', 'arcade', 'continue', 'gameover', 'j2', 'fins', 'decors', 'japonais'],
           'upper_max': ['arcade', 'croises', 'fins']}
PARTIES['greffe_max'] = PARTIES['greffe']
ECH = {'fins': ['00_Z3', '0b_Z3', '1c_Z3', '04_Z3', '15_A'], 'decors': ['00', '0E', '1C', '2A'],
       'croises': ['Eagle_Ryu_max-j1', 'Maki_Zangief_max-j2', 'Yun_ChunLi_max-j1', 'Ingrid_Akuma_max-j2'],
       'max_fins': ['02', '07', '1a', '1d', '20', '21', '24'], 'arcade': None}
MAX_IDS = {'Eagle': 0x26, 'Maki': 0x27, 'Yun': 0x2D, 'Ingrid': 0x2E}
ECHANT = {'Ryu': 0x00, 'Zangief': 0x10, 'Chun-Li': 0x04, 'Dhalsim': 0x0F, 'Blanka': 0x19, 'Akuma': 0x02, 'Juli': 0x1E,
          'Juni': 0x1F}
DECORS = '00 02 04 06 08 0A 0C 0E 10 12 14 16 18 1A 1C 1E 20 22 24 26 28 2A 2C 2E 30 32 34 36 38 3A 3C 3E 40 42 44 46 48 4A 4C 4E'.split()
JAPONAIS = ("NON DISPONIBLE : le pilote sfa3hx du fork n'a pas de réglage de région (sur CPS-2 la région est dans le "
            "programme) ; dans nos constructions la région est une CONSTANTE du code 68K recompilé depuis le module US "
            "(work/anthology_jp/RAPPORT.md : 0 = Japon, 2 = US ; textes japonais absents du module US ; construction depuis "
            "le disque japonais SLPM-66409 refusée, à faire PLUS TARD, ATTENTES-ET-DECISIONS 12/11). Forcer la constante "
            "donnerait un jeu US mal réglé, pas la version japonaise.")


def lit_conf_version():
    f = W + '/outils/banc_jour.conf'
    v = 'v161_banc'
    if os.path.exists(f):
        for l in open(f, encoding='utf-8'):
            m = re.match(r'^\s*VERSION=(\S+)', l)
            if m:
                v = m.group(1)
    return v


REFS = os.path.join(W, 'references', os.environ.get('BANC_REF_VERSION') or lit_conf_version())
R9, R5 = REFS + '/ro9', REFS + '/ro5'

_md5 = {}


def md5f(f):
    f = os.path.realpath(f)
    if f not in _md5:
        h = hashlib.md5()
        with open(f, 'rb') as x:
            for b in iter(lambda: x.read(1 << 20), b''):
                h.update(b)
        _md5[f] = h.hexdigest()[:12]
    return _md5[f]


# ------------------------------------------------------------------ constructions
def resout(n):
    if not n:
        return None
    for p in (n, os.path.join(G, 'constructions', n), os.path.join(G, 'constructions', n + '_fige'), os.path.join(BC, n)):
        if os.path.isdir(p):
            return os.path.realpath(p)
    sys.exit('banc_ref : construction introuvable : %s' % n)


def jeu_de(C):
    if os.path.isdir(C + '/b9/roms_ro9/sfa3ud') and os.path.isfile(C + '/greffe.json'):
        return 'greffe_max' if os.path.isfile(C + '/hsfa_gfx_max.bin') else 'greffe'
    if os.path.isdir(C + '/roms_fork/sfa3hx') and os.path.isfile(C + '/env_max_cache.txt'):
        return 'upper_max'
    sys.exit('banc_ref : jeu inconnu pour %s (ni b9/ + greffe.json, ni roms_fork/ + env_max_cache.txt)' % C)


def fichiers_constr(C, jeu):
    """entrées de la construction (ce qui la distingue) : liste (étiquette, chemin)"""
    L = []
    if jeu.startswith('greffe'):
        R = C + '/b9/roms_ro9/sfa3ud'
        L += [('rom ' + f, os.path.join(R, f)) for f in sorted(os.listdir(R))]
        L += [('blocs ' + os.path.basename(f), f) for f in sorted(glob.glob(C + '/b9/ext_*.bin'))]
        L += [('banque ' + f, os.path.join(C, 'banques_hx', f)) for f in sorted(os.listdir(C + '/banques_hx'))]
        L += [('decors_gfx ' + os.path.basename(f), f) for f in sorted(glob.glob(C + '/decors_gfx/*'))]
        L += [('greffe.json', C + '/greffe.json')]
        if os.path.isfile(C + '/hsfa_gfx_max.bin'):
            L += [('hsfa_gfx_max', C + '/hsfa_gfx_max.bin')]
    else:
        R = C + '/roms_fork/sfa3hx'
        L += [('rom ' + f, os.path.join(R, f)) for f in sorted(os.listdir(R))]
        L += [('blocs ' + os.path.basename(f), f) for f in sorted(glob.glob(C + '/ext_*.bin'))]
        L += [('banque ' + f, os.path.join(C, 'banques_hx', f)) for f in sorted(os.listdir(C + '/banques_hx'))]
        for f in ('max_plus_gfx.bin', 'env_max_cache.txt', 'carte_image.txt'):
            if os.path.isfile(os.path.join(C, f)):
                L.append((f, os.path.join(C, f)))
    return L


def empreinte_constr(C, jeu):
    h = hashlib.md5()
    for e, f in fichiers_constr(C, jeu):
        h.update(('%s %s\n' % (e, md5f(f))).encode())
    return h.hexdigest()[:10]


class Constr:
    def __init__(self, chemin, jeu=None):
        self.C = chemin
        self.jeu = jeu or jeu_de(chemin)
        self.nom = os.path.basename(chemin.rstrip('/'))
        m = re.search(r'/c/([^/]+)/outils/greffe/constructions/', chemin)   # sortie de c.sh d'un atelier : nom = c/<NOM>
        if m:
            self.nom = '%s_%s' % (os.path.basename(os.path.dirname(chemin.split('/c/')[0] + '/x')), m.group(1))
        self.emp = empreinte_constr(chemin, self.jeu)
        self.id = '%s_%s' % (self.nom, self.emp)
        self.menu_ca = False
        if self.jeu.startswith('greffe'):
            J = json.load(open(chemin + '/greffe.json'))
            self.menu_ca = any(str(p.get('quoi', '')).startswith('MENU_CURSEUR_ARCADE') for p in J.get('patchs', []))
            self._J = J

    def graine_pc(self):
        """adresse image de la copie de 0x24F9D0 (= banc_jour.graine_pc, commun.sh pc68k/copie_de)"""
        n = [int(nn, 16) + 0x24f9d0 - int(a, 16) for a, b, nn in self._J['blocs'] if int(a, 16) <= 0x24f9d0 < int(b, 16)][0]
        L = []
        for l in open(os.path.join(self.C, 'b9', 'carte_image.txt')):
            p = l.split(None, 2)
            if len(p) > 1 and all(c in '0123456789abcdefABCDEF$' for c in p[0] + p[1]):
                L.append((int(p[1], 16), p[0]))
        L.sort()
        K = [a for a, _ in L]
        k = bisect.bisect_left(K, n)
        if k < len(L) and L[k][0] - n < 0x200:
            return L[k][1].lstrip('$')
        raise SystemExit('graine PC introuvable pour %s' % self.C)

    def sonde(self):
        """sonde des sentinelles (fins_greffe/outils/sonde_prep.py) calculée dans une VUE du cache (rien n'est écrit
        dans la construction) -> (cibles68k, copie)"""
        V = os.path.join(CACHE, self.id, 'sonde_vue')
        if not os.path.isfile(V + '/sonde/copie.txt'):
            os.makedirs(V, exist_ok=True)
            for n in ('b9', 'greffe.json'):
                if not os.path.lexists(os.path.join(V, n)):
                    os.symlink(os.path.join(self.C, n), os.path.join(V, n))
            subprocess.run(['python3', '-I', SONDE_PREP, V], check=True, stdout=subprocess.DEVNULL)
        return V + '/sonde/cibles68k.txt', open(V + '/sonde/copie.txt').read().strip()


# ------------------------------------------------------------------ recettes
def gfx_greffe(c, ro5plans, decors=True):
    L = [R9 + '/hsfa_gfx.bin', R9 + '/hsfa_plans.bin@3000000'] + ([R5 + '/hsfa_plans.bin@4000000'] if ro5plans else [])
    if decors and os.path.isfile(c.C + '/decors_gfx/plan.tsv'):
        for l in open(c.C + '/decors_gfx/plan.tsv'):
            x = l.rstrip('\n').split('\t')
            if x[0] and not x[0].startswith('#'):
                L.append('%s/decors_gfx/%s@%x' % (c.C, x[0], int(x[1], 16)))
    if os.path.isfile(c.C + '/hsfa_gfx_max.bin'):
        L.append(c.C + '/hsfa_gfx_max.bin@5400000')
    return ','.join(L)


def banc_greffe(c, ro5plans=True):
    return [('BANC_COMMUN', '545')] + ([('BANC_COMMUN_UPPER', '351')] if ro5plans else []) + [
        ('HSFA_PLANS', '300,340,3a0'), ('HSFA_GFX', gfx_greffe(c, ro5plans)), ('BANC_BANQUES', c.C + '/banques_hx/'),
        ('BANC_PTR_ANIM', 'FF40BC'), ('BANC_DIR', c.C + '/b9/')]


class Job:
    def __init__(self, c, partie, cle, lua, env, tmax, envc=(), rom=None, verdict=None):
        env = list(dict(env).items())  # une variable donnée deux fois : la dernière valeur l'emporte (comme env)
        self.c, self.partie, self.cle, self.lua, self.env, self.tmax = c, partie, cle, lua, env, tmax
        self.envc = set(envc)          # variables qui dépendent de la construction (légitimement différentes)
        self.rom = rom or (c.C + '/b9/roms_ro9/sfa3ud' if c.jeu.startswith('greffe') else c.C + '/roms_fork/sfa3hx')
        self.verdict = verdict or partie
        self.diag = None


def plan_greffe(c, parties, cles, ech, jum=None):
    J = []
    T = '@T@'   # dossier de la partie (remplacé au lancement)
    menu = '1' if c.menu_ca else '0'
    liste = open(G + '/e22/liste_vsd.txt').read().rstrip('\n')   # comme « $(cat …) » de vs_fiable.sh : un « \n » final fausse la 8e paire
    head = []
    for p in parties:
        if p in ('versus', 'training'):
            nf, mj = ('60000', '1') if p == 'versus' else ('1500', '4')
            env = [('LISTE', liste), ('MODEJEU', mj), ('NF', nf), ('SNAPM', '1'), ('OUT', T + '/journal.txt'), ('BANC_COMMUN', '545'),
                   ('HSFA_PLANS', '300,340,3a0'), ('CONTOURNE_E', '1'), ('HSFA_GFX', gfx_greffe(c, False)),
                   ('BANC_BANQUES', c.C + '/banques_hx/'), ('BANC_PTR_ANIM', 'FF40BC'), ('BANC_DIR', c.C + '/b9/'),
                   ('HSFA_BANC_LUA', MAME_LUA), ('MENU_CURSEUR_ARCADE', menu), ('MENU_LOG', T + '/menu.txt')]
            J.append(Job(c, p, p, LUA_MENU_VS, env, 3000, envc=['MENU_CURSEUR_ARCADE']))
            continue
        if p == 'japonais':
            j = Job(c, p, 'region_jp', None, [], 0)
            J.append(j)
            continue
        pc = c.graine_pc()
        commun = [('SNAPETAT', '0'), ('GRAINE_PC', pc), ('GRAINE_OUT', T + '/graine.txt'), ('FORCE_ADR', 'ff8120=32,ff8123=82'),
                  ('SCENEA_PASSIF', '1'), ('BLOCAGE', '20000')]
        nav = [('MENU_START', '1')] + ([] if c.menu_ca else [('MENU_DIR', 'Up')])
        if p == 'arcade':
            env = [('PERSO', '01.Z3')] + commun + [('ARRET_FIN', '1'), ('SAC_SUITE', G + '/lua/graine_pc.lua'), ('SAC_OUT', T + '/sonde.txt'),
                   ('SAC_PASSIF', '1'), ('SAC_PASSIF_A', '1'), ('SAC_D2N', '3'), ('SAC_PAS', '60'), ('LUA_BASE', LUA_MENU_ARC)] + nav + \
                  [('NF', '21000'), ('OUT', T + '/journal.txt')] + banc_greffe(c)
            J.append(Job(c, p, '01_Z3', AC + '/lua/sonde_ac.lua', env, 3000, envc=['GRAINE_PC', 'MENU_DIR']))
        elif p == 'continue':
            env = [('PERSO', '01.Z3')] + commun + [('SNAPETAT', '1'), ('ARRET_FIN', '1'), ('LUA_BASE', LUA_MENU_ARC)] + nav + \
                  [('PERDRE_ETAPE', '2'), ('PERDRE_N', '2'), ('SNAPSC', '60'), ('NF', '60000'), ('OUT', T + '/journal.txt')] + banc_greffe(c)
            J.append(Job(c, p, '01_Z3_etape2', G + '/lua/graine_pc.lua', env, 4500, envc=['GRAINE_PC', 'MENU_DIR']))
        elif p == 'gameover':
            env = [('PERSO', '01.Z3')] + commun + [('SNAPETAT', '1'), ('LUA_BASE', LUA_MENU_ARC)] + nav + \
                  [('PERDRE', '1'), ('NOCONT', '1'), ('SNAPSC', '60'), ('NF', '12000'), ('OUT', T + '/journal.txt')] + banc_greffe(c)
            J.append(Job(c, p, '01_Z3', G + '/lua/graine_pc.lua', env, 2500, envc=['GRAINE_PC', 'MENU_DIR']))
        elif p == 'j2':
            env = [('PERSO', '01.Z3')] + commun + [('SNAPETAT', '1'), ('LUA_BASE_D', G + '/lua/graine_pc.lua'), ('LUA_BASE', LUA_MENU_ARC)] + nav + \
                  [('DEFI_COIN', '400'), ('DEFI_IMG', '500'), ('DEFI_ETAT', '2 4 2'), ('DEFI_OUT', T + '/defi.txt'),
                   ('NF', '15000'), ('OUT', T + '/journal.txt')] + banc_greffe(c)
            J.append(Job(c, p, '01_Z3_carte', LUA_DEFI, env, 2500, envc=['GRAINE_PC', 'MENU_DIR']))
        elif p == 'fins':
            cib, cop = c.sonde()
            L = [l.split() for l in (open(G + '/e23/liste_sans07.txt').read() + open(G + '/e23/liste_07.txt').read()).splitlines() if l.strip()]
            for pp, v in L:
                k = '%s_%s' % (pp, v)
                if (cles and k not in cles) or (ech and k not in ECH['fins']):
                    continue
                guy = pp == '07'
                env = [('PERSO', '%s.%s' % (pp, v))] + commun + [('ARRET_FIN', '1'), ('SENT_CIBLES', cib),
                       ('SENT_DECORS', MH + '/vide.txt'), ('SENT_COPIE', cop), ('SENT_BASE', MH + '/lua/snaps_fin.lua'),
                       ('SENT_OUT', T + '/sent.txt'), ('SF_BASE', G + '/lua/graine_pc.lua'), ('LUA_BASE', G + '/lua/tournee_arcade.lua'),
                       ('SF_PAS', '60'), ('SF_LOG', T + '/sf.txt'), ('NF', '120000' if guy else '45000'), ('OUT', T + '/journal.txt')] + banc_greffe(c)
                J.append(Job(c, p, k, MH + '/lua/sentinelles.lua', env, 14000 if guy else 6000, envc=['GRAINE_PC', 'SENT_COPIE', 'SENT_CIBLES']))
            continue
        elif p == 'decors':
            if not jum:
                j = Job(c, p, 'sans_jumelle', None, [], 0)
                j.verdict = 'refus_decors'
                J.append(j)
                continue
            for x in DECORS:
                if (cles and x not in cles) or (ech and x not in ECH['decors']):
                    continue
                env = [('BD_BASE', G + '/lua/tournee_arcade.lua'), ('PERSO', '00.Z3'), ('BD_DECOR', x), ('BD_OUT', T + '/bd.txt'),
                       ('BD_SNAPS', '150,300,450,700'), ('BLOCAGE', '20000'), ('NF', '9000'), ('OUT', T + '/journal.txt')] + banc_greffe(jum)
                J.append(Job(jum, p, x, G + '/lua/banc_decor_cam.lua', env, 900))
            continue
        if cles:
            J = [j for j in J if j.partie != p or j.cle in cles]
    return J


def plan_max(c, parties, cles, ech):
    J = []
    T = '@T@'
    M = c.C
    cfg = dict(MAXG='26D5580', PORTG='2E03600', PLUSG='2E45000', PLANSG='3000000', PLANS='300,340,3a0',
               MAXFORK=os.path.expanduser('~/.cache/sfa3max/fork/'))
    for m in re.finditer(r'(\w+)=(\S+)', open(M + '/env_max_cache.txt').read()):
        cfg[m.group(1)] = m.group(2)
    Gf = cfg['MAXFORK'].rstrip('/')
    gp = ',%s/max_plus_gfx.bin@%s' % (M, cfg['PLUSG']) if os.path.isfile(M + '/max_plus_gfx.bin') else ''
    base = [('OUT', T + '/journal.txt'), ('MODULE', 'max'),
            ('HSFA_GFX', '%s/hsfa_gfx.bin,%s/max_gfx.bin@%s,%s/max_portraits_gfx.bin@%s%s,%s/hsfa_plans.bin@%s' % (
                R5, Gf, cfg['MAXG'], Gf, cfg['PORTG'], gp, R5, cfg['PLANSG'])),
            ('BANC_COMMUN', '351'), ('HSFA_PLANS', cfg['PLANS']), ('BANC_BANQUES', M + '/banques_hx/'), ('BANC_PTR_ANIM', 'FF40BC'),
            ('BANC_GFX_INTRO', '456'), ('BANC_DIR', M + '/'), ('HSFA_EXT', M), ('UPPER', '1'), ('MAXDIR', M)]
    envc = ['HSFA_GFX', 'HSFA_PLANS']
    for p in parties:
        if p == 'arcade':
            for n, i in MAX_IDS.items():
                if cles and n not in cles:
                    continue
                J.append(Job(c, p, n, BC + '/lua/tournee_max_copie.lua', base + [('PERSO', '%02x' % i), ('NF', '120000')], 4000, envc, verdict='max_fin'))
        elif p == 'croises':
            for m_, im in MAX_IDS.items():
                for n, i_n in ECHANT.items():
                    for sens in ('max-j1', 'max-j2'):
                        k = '%s_%s_%s' % (m_, n.replace('-', ''), sens)
                        if (cles and k not in cles) or (ech and k not in ECH['croises']):
                            continue
                        j1, j2 = (im, i_n) if sens == 'max-j1' else (i_n, im)
                        J.append(Job(c, p, k, BC + '/lua/tournee_max_copie.lua', base + [
                            ('VS', '1'), ('PERSO', '%02x' % j1), ('PERSO2', '%02x' % j2), ('ALEA', '1'), ('GRAINE', '%d' % (j1 * 64 + j2)),
                            ('KO', '900'), ('NF', '24000')], 1500, envc, verdict='max_croise'))
        elif p == 'fins':
            for i in [x for x in range(0x26) if x not in (0x12, 0x13, 0x14)]:
                k = '%02x' % i
                if (cles and k not in cles) or (ech and k not in ECH['max_fins']):
                    continue
                J.append(Job(c, p, k, MAME_LUA + '/tournee.lua', base + [('PERSO', k), ('NF', '180000' if i == 7 else '90000')],
                             3500, envc, verdict='max_fin'))
    return J


def plan(c, parties, cles, ech, jum=None):
    return plan_max(c, parties, cles, ech) if c.jeu == 'upper_max' else plan_greffe(c, parties, cles, ech, jum)


# ------------------------------------------------------------------ contexte et lancement
def chaine_lua(job):
    L = [job.lua] + [v for k, v in job.env if v.endswith('.lua')]
    if job.diag:
        L.append(LUA_DIAG)
    L += [MAME_LUA + '/banc_mem.lua', MAME_LUA + '/banc_plans.lua', MAME_LUA + '/banc_sprites.lua']
    vu, R = set(), []
    for l in L:
        if l not in vu and os.path.isfile(l):
            vu.add(l)
            R.append(l)
    return R


def norm(v, job, D):
    v = v.replace(D, 'TRACE').replace(job.c.C, 'CONSTR').replace(CACHE + '/' + job.c.id, 'CACHE')
    return v


def contexte(job, D):
    """lignes : 'banc …' (doivent être égales pour comparer), 'constr …' (la construction), 'envc …' (adaptées à elle)"""
    L = ['recette %s %s %s %s' % (RECETTE, job.c.jeu, job.partie, job.cle), 'banc md5 cps2f %s' % md5f(FORK)]
    for l in chaine_lua(job):
        L.append('banc md5 lua %s %s' % (os.path.basename(l), md5f(l)))
    for e, f in fichiers_constr(job.c.C, job.c.jeu):
        L.append('constr md5 %s %s' % (e, md5f(f)))
    for k, v in job.env:
        if k == 'HSFA_GFX':
            for g in v.split(','):
                f, a = (g.split('@') + ['2000000'])[:2]
                dc = f.startswith(job.c.C) or '/.cache/sfa3max' in f   # tuiles MAX du cache de max_cache.py : de la construction
                L.append('%s md5 tuiles $%s %s %s' % ('constr' if dc else 'banc', a, md5f(f), os.path.basename(f) if dc else os.path.relpath(f, H)))
        if k in ('SENT_CIBLES', 'SENT_DECORS') and os.path.isfile(v):
            L.append('%s md5 %s %s' % ('constr' if k == 'SENT_CIBLES' else 'banc', k, md5f(v)))
    for k, v in job.env:
        if k == 'LISTE':
            L.append('banc md5 LISTE %s' % hashlib.md5(v.encode()).hexdigest()[:12])
            continue
        L.append('%s %s=%s' % ('envc' if k in job.envc else 'env', k, norm(v, job, D)))
    if job.diag:
        L.append('DIAGNOSTIC %s' % ' '.join('%s=%s' % kv for kv in sorted(job.diag.items()) if kv[0] != 'chemin'))
    return L


def cle_banc(ctx):
    return [l for l in ctx if l.startswith(('recette', 'banc', 'env '))]


def fini(D):
    return os.path.isfile(D + '/fini.txt')


def emus_de(D):
    """PID (registre de lance_emu) des émulateurs qui tournent sur le dossier D (rompath D/roms)"""
    R = []
    for f in glob.glob(os.path.join(os.path.dirname(LANCE), 'registre_emu', 'actifs', '*.tsv')):
        try:
            t = open(f).read()
        except OSError:
            continue
        if (D + '/roms ') in t and os.path.exists('/proc/' + t.split('\t')[0]):   # entrée vivante seulement
            R.append(t.split('\t')[0])
    return R


EN_COURS = set()


def lance(job, D):
    # (16/11) jamais deux émulateurs sur le même dossier : un émulateur d'une partie arrêtée qui tournerait encore
    # écrirait ses captures dans la nouvelle (MAME numérote à la suite : 0093… au lieu de 0000…)
    while emus_de(D) and not ARRET.is_set():
        time.sleep(15)
    if os.path.isdir(D):
        shutil.rmtree(D)
    for s in ('roms', 'nv', 'cfg', 'snap'):
        os.makedirs(os.path.join(D, s))
    os.symlink(job.rom, D + '/roms/sfa3hx')
    ctx = contexte(job, D)
    with open(D + '/contexte.txt', 'w') as f:
        f.write('# contexte banc_ref : %s %s %s ; %s ; charge %s\n' % (job.c.nom, job.partie, job.cle, time.strftime('%F %T'),
                                                                   ' '.join(open('/proc/loadavg').read().split()[:3])))
        f.write('construction %s\n' % job.c.C)
        f.write('\n'.join(ctx) + '\n')
    env = {'HOME': os.path.expanduser('~'), 'PATH': '/usr/local/bin:/usr/bin:/bin', 'DISPLAY': DISPLAY, 'LANG': 'C.UTF-8',
           'HSFA_AGENT': AGENT}
    for k, v in job.env:
        env[k] = v.replace('@T@', D)
    lua = job.lua
    extra = []
    if job.diag:
        env.update({'DIAG_BASE': job.lua, 'DIAG_NOM': job.diag['nom'], 'DIAG_OUT': D + '/diag.txt'})
        if 'sauve' in job.diag:
            env['DIAG_SAUVE'] = str(job.diag['sauve'])
        else:
            env['DIAG_CHARGE'] = '1'
        lua = LUA_DIAG
        extra = ['-state_directory', job.diag['chemin']]
    cmd = [LANCE, '--agent', AGENT, '--empreinte', D + '/empreinte.txt', '--', 'timeout', str(job.tmax), 'nice', '-n', '19',
           FORK, 'sfa3hx', '-noreadconfig', '-rompath', D + '/roms', '-nvram_directory', D + '/nv', '-cfg_directory', D + '/cfg',
           '-snapshot_directory', D + '/snap'] + extra + ['-video', 'none', '-sound', 'none', '-nothrottle', '-skip_gameinfo',
                                                          '-autoboot_script', lua]
    t0 = time.time()
    if ARRET.is_set():
        return -15
    with open(D + '/mame.log', 'w') as lo:
        pr = subprocess.Popen(cmd, cwd=MAME_LUA, env=env, stdout=lo, stderr=subprocess.STDOUT)
        ENFANTS.add(pr)
        EN_COURS.add(D)
        rc = pr.wait()
        ENFANTS.discard(pr)
        if ARRET.is_set():          # arrêt : l'émulateur enregistré est arrêté par son PID (TERM puis KILL)
            for pid in emus_de(D):
                subprocess.run([LANCE, '--arrete', pid, '--delai', '3'], capture_output=True)
        EN_COURS.discard(D)
    if ARRET.is_set():
        return -15      # partie interrompue : pas de fini.txt (elle sera rejouée à la reprise)
    with open(D + '/fini.txt', 'w') as f:
        f.write('code %d duree %.0f s fin %s\n' % (rc, time.time() - t0, time.strftime('%F %T')))
    return rc


# arrêt propre (kill PID du script) : plus aucun lancement, et chaque lance_emu en cours (y compris celui qui ATTEND une
# place) reçoit TERM, qu'il transmet au groupe de l'émulateur. Sans cela, un lance_emu en attente survivait au script et
# écrivait plus tard dans le dossier d'une partie relancée (16/11 : captures en double dans fins/07_A).
ARRET = threading.Event()
ENFANTS = set()


def arrete(sig, frm):
    """TERM à chaque lance_emu (il le transmet au groupe de l'émulateur), puis KILL 8 s après à ceux qui vivent encore
    (un lance_emu qui attend une place ignore TERM et lancerait plus tard)"""
    ARRET.set()
    for pr in list(ENFANTS):
        try:
            pr.terminate()
        except OSError:
            pass

    def tue():
        for D in list(EN_COURS):
            for pid in emus_de(D):
                subprocess.run([LANCE, '--arrete', pid, '--delai', '3'], capture_output=True)
        time.sleep(8)
        for pr in list(ENFANTS):
            if pr.poll() is None:
                try:
                    pr.kill()
                except OSError:
                    pass
    threading.Thread(target=tue, daemon=True).start()


def ctx_de(D):
    f = D + '/contexte.txt'
    return [l.rstrip('\n') for l in open(f) if not l.startswith(('#', 'construction '))] if os.path.isfile(f) else None


# ------------------------------------------------------------------ verdicts (indépendants de la comparaison)
ETAT_RE = re.compile(r'^\s*(\d+) : ([0-9a-f]{4}) ([0-9a-f]{4}) ([0-9a-f]{4})')


def etats(t):
    return [(int(m.group(1)), int(m.group(2), 16), int(m.group(3), 16), int(m.group(4), 16)) for m in map(ETAT_RE.match, t.splitlines()) if m]


def resume_tournee(log):
    """= banc_jour.resume_tournee (journaux de tournee.lua / tournee_max_copie.lua)"""
    m = {'manches': 0, 'fin': 'avant', 'sortie_fin': None, 'exc': None, 'FIN': False}
    for l in open(log, errors='replace') if os.path.exists(log) else []:
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
            if t[4] == '000a' and m['fin'] == 'avant':
                m['fin'] = 'dans'
            elif t[4] != '000a' and m['fin'] == 'dans':
                m['fin'], m['sortie_fin'] = 'finie', k
    return m


def verdict(job, D):
    """-> (OK|KO|VIDE|NON DISPONIBLE|REFUS, mesure, détail)"""
    if job.verdict == 'refus_decors':
        return 'REFUS', '', "décors : jumelle TIRAGE_CPU=0 exigée (--jumelle / --jumelle-ref) ; le banc des décors impose le décor et ne vaut que sans tirage de la version du CPU"
    if job.partie == 'japonais':
        return 'NON DISPONIBLE', '', JAPONAIS
    sn = sorted(glob.glob(D + '/snap/*/*.png'))
    t0 = os.path.getmtime(D + '/empreinte.txt') if os.path.isfile(D + '/empreinte.txt') else 0
    vieux = [f for f in sn if os.path.getmtime(f) < t0 - 1]
    if os.path.isfile(D + '/sf.txt') and len(sn) != len([l for l in open(D + '/sf.txt') if l.strip()]):
        vieux = vieux or sn          # fins : une capture par ligne de sf.txt (snaps_fin.lua)
    if vieux or (sn and [os.path.basename(f) for f in sn] != ['%04d.png' % i for i in range(len(sn))]):
        return 'KO', 'captures', 'captures d un AUTRE émulateur dans le dossier (%d antérieures au lancement, %d en tout) : partie à rejouer' % (len(vieux), len(sn))
    j = D + '/journal.txt'
    t = open(j, errors='replace').read() if os.path.isfile(j) else ''
    if not t.strip():
        return 'VIDE', '', 'journal vide ou absent (Lua introuvable ? délai ?) : %s' % (open(D + '/fini.txt').read().strip() if fini(D) else 'pas fini')
    if job.verdict in ('max_fin', 'max_croise'):
        r = resume_tournee(j)
        if r['exc']:
            return 'KO', 'exception', r['exc']
        if job.verdict == 'max_fin':
            return ('OK' if r['fin'] == 'finie' else 'KO'), 'manches=%d fin=%s sortie=%s' % (r['manches'], r['fin'], r['sortie_fin']), ''
        if not r['FIN']:
            return 'KO', 'interrompu', 'journal interrompu (blocage ou délai)'
        return ('OK' if r['manches'] >= 2 else 'KO'), 'manches=%d' % r['manches'], ''
    exc = re.search(r'^EXC\S*\s+(.*)$', t, re.M)
    if exc:
        return 'KO', 'exception', exc.group(1)[:80]
    bl = re.search(r'^BLOQUE (\d+)', t, re.M)
    if bl and job.partie != 'decors':
        return 'KO', 'bloqué', 'BLOQUE image %s' % bl.group(1)
    man = len(re.findall(r'^MANCHE', t, re.M))
    ss = etats(t)
    p = job.partie
    if p in ('versus', 'training'):
        f = re.search(r'^FIN (\d+) selections (\d+) manches (\d+)', t, re.M)
        mt = open(D + '/menu.txt').read() if os.path.isfile(D + '/menu.txt') else ''
        m = re.search(r'curseur a l.arrivee (\d+) \(attendu (\d+)\)', mt)
        att = 0 if job.c.menu_ca else 1
        if not f:
            return 'KO', '', 'pas de FIN'
        if not m or int(m.group(1)) != att:
            return 'KO', '', 'menu : curseur à l arrivée %s, attendu %d' % (m.group(1) if m else '?', att)
        q = re.search(r'quitte image (\d+) : curseur (\d+)', mt)
        return 'OK', 'selections=%s manches=%s menu %s->%s' % (f.group(2), f.group(3), m.group(1), q.group(2) if q else '?'), ''
    if p == 'decors':
        b = open(D + '/bd.txt', errors='replace').read() if os.path.isfile(D + '/bd.txt') else ''
        n = len(re.findall(r'^I ', b, re.M))
        return ('OK' if n else 'KO'), 'releves=%d' % n, '' if n else 'aucun relevé (décor non atteint)'
    if p == 'fins':
        f = re.search(r'FIN_A (\d+) duree (\d+)', t)
        return ('OK', 'duree=%s' % f.group(2), '') if f else ('KO', 'non aboutie', 'fin non atteinte')
    menu = re.findall(r'^MENU (\d+) image (\d+) : curseur \$FF4201=(\d+)', t, re.M)
    att = 0 if job.c.menu_ca else 1
    if not menu or int(menu[0][2]) != att:
        return 'KO', '', 'menu : curseur à l arrivée %s, attendu %d' % (menu[0][2] if menu else '?', att)
    drap = re.search(r'^MENU 1 quitte image (\d+) : curseur \$FF4201=(\d+) drapeau \$FF7E00=(\w+)', t, re.M)
    if not drap or drap.group(3) != '01':
        return 'KO', '', 'sortie du menu sans le drapeau ARCADE ($FF7E00=01)'
    if p == 'arcade':
        return ('OK' if man else 'KO'), 'manches=%d menu %s sortie %s' % (man, menu[0][1], drap.group(1)), '' if man else 'aucune manche'
    if p == 'continue':
        i6 = next((k for k, a0, a4, a8 in ss if a0 == 2 and a4 == 6), None)
        if i6 is None:
            return 'KO', '', 'écran CONTINUE (2/6) non atteint'
        apres = [int(x) for x in re.findall(r'^MANCHE \d+ image (\d+)', t, re.M) if int(x) > i6]
        if not apres:
            return 'KO', '', 'CONTINUE à %d mais aucune manche après' % i6
        fa = re.search(r'FIN_A (\d+) duree (\d+)', t)
        return 'OK', 'continue=%d manches_apres=%d fin=%s' % (i6, len(apres), ('duree %s' % fa.group(2)) if fa else 'non'), ''
    if p == 'gameover':
        i8 = next((k for k, a0, a4, a8 in ss if a0 == 2 and a4 == 8), None)
        if i8 is None:
            return 'KO', '', 'GAME OVER (2/8) non atteint'
        ret = next((k for k, a0, a4, a8 in ss if k > i8 and a0 != 2), None)
        m2 = re.search(r'^MENU 2 image (\d+) : curseur \$FF4201=(\d+)', t, re.M)
        if ret is None:
            return 'KO', '', 'GAME OVER à %d sans retour au titre' % i8
        return 'OK', 'gameover=%d titre=%d menu2=%s' % (i8, ret, ('%s curseur %s' % m2.groups()) if m2 else 'non'), ''
    if p == 'j2':
        d = open(D + '/defi.txt').read() if os.path.isfile(D + '/defi.txt') else ''
        m = re.search(r'^DEFI (\d+)', d, re.M)
        if not m:
            return 'KO', '', 'défi non déclenché (état visé non atteint)'
        i = int(m.group(1))
        sel = next((k for k, a0, a4, a8 in ss if k > i and a0 == 2 and a4 == 2), None)
        if sel is None:
            return 'KO', 'defi=%d' % i, 'J2 n entre pas (pas de retour à la sélection après le défi)'
        apres = [x for x in re.findall(r'^MANCHE \d+ image (\d+) J1 (\w+)/\w+/\w+ J2 (\w+)', t, re.M) if int(x[0]) > sel]
        return ('OK' if apres else 'KO'), 'defi=%d selection=%d manches_apres=%d J2=%s' % (i, sel, len(apres), apres[0][2] if apres else '?'), \
            '' if apres else 'sélection de J2 sans combat'
    return 'KO', '', 'partie inconnue'


# ------------------------------------------------------------------ comparaison
IGNORE = {'contexte.txt', 'mame.log', 'empreinte.txt', 'fini.txt', 'diag.txt'}


def fichiers_trace(D):
    R = {}
    for f in sorted(os.listdir(D)) if os.path.isdir(D) else []:
        if f not in IGNORE and os.path.isfile(os.path.join(D, f)):
            R[f] = os.path.join(D, f)
    return R


def captures(D):
    S = os.path.join(D, 'snap')
    R = {}
    for f in glob.glob(S + '/**/*.png', recursive=True):
        R[os.path.relpath(f, S)] = md5f(f)
    return R


def compare(DR, DC):
    """-> liste de différences [(quoi, valeurs)] ; [] = identique"""
    diffs = []
    FR, FC = fichiers_trace(DR), fichiers_trace(DC)
    for f in sorted(set(FR) | set(FC)):
        if f not in FR or f not in FC:
            diffs.append((f, ['absent ' + ('réf' if f not in FR else 'cand')]))
            continue
        a, b = open(FR[f], 'rb').read(), open(FC[f], 'rb').read()
        if f.endswith('.totaux'):      # totaux des sentinelles : ordre d'un parcours de table Lua, comparés triés
            a, b = b'\n'.join(sorted(a.split(b'\n'))), b'\n'.join(sorted(b.split(b'\n')))
        if a == b:
            continue
        if f.startswith('sent'):
            la, lb = set(a.decode(errors='replace').splitlines()), set(b.decode(errors='replace').splitlines())
            def img(l):      # « E 337 … » / « X 374 … » : 2e champ = image (comme cmp_fins.sh de ro9a44)
                t = l.split()
                return (t[1] if len(t) > 1 and t[0].isalpha() else t[0]) if t else ''
            im = sorted({img(l) for l in la ^ lb} - {''}, key=lambda x: (len(x), x))
            diffs.append((f, im or ['ordre']))
        else:
            A, B = a.decode(errors='replace').splitlines(), b.decode(errors='replace').splitlines()
            n = next((i for i in range(min(len(A), len(B))) if A[i] != B[i]), min(len(A), len(B)))
            diffs.append((f, ['1re ligne différente %d : %s' % (n + 1, (B[n] if n < len(B) else '(fin)')[:70])]))
    CR, CC = captures(DR), captures(DC)
    dc = sorted([k for k in set(CR) | set(CC) if CR.get(k) != CC.get(k)], key=lambda x: (len(x), x))
    if dc:
        diffs.append(('captures', [os.path.basename(x).replace('.png', '') for x in dc]))
    return diffs, len(CC), len(CC) - len([k for k in dc if k in CC])


def lit_attendus(f):
    A = []
    if f:
        for l in open(f, encoding='utf-8'):
            if l.strip() and not l.startswith('#'):
                x = l.rstrip('\n').split('\t')
                A.append((x[0], x[1], x[2], set(x[3].split()) if len(x) > 3 else {'*'}))
    return A


def couvert(A, partie, cle, quoi, vals):
    for p, c, q, v in A:
        if fnmatch.fnmatch(partie, p) and fnmatch.fnmatch(cle, c) and fnmatch.fnmatch(quoi, q):
            if '*' in v or set(vals) <= v:
                return True
            if any(x.startswith('~') and re.search(x[1:].replace('_', ' '), ' '.join(vals)) for x in v):
                return True          # « ~motif » : expression rationnelle sur le détail (« _ » = espace), ex. 1re ligne différente dans la fin
    return False


# ------------------------------------------------------------------ principal
def principal():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('construction')
    ap.add_argument('--contre')
    ap.add_argument('--jeu')
    ap.add_argument('--parties')
    ap.add_argument('--cles')
    ap.add_argument('--echantillon', action='store_true')
    ap.add_argument('--jumelle')
    ap.add_argument('--jumelle-ref')
    ap.add_argument('--attendus')
    ap.add_argument('--upper', nargs='?', const=W + '/oracle_upper/traces')
    ap.add_argument('--nom')
    ap.add_argument('--places', type=int, default=int(os.environ.get('BANC_REF_PLACES', '4')))
    ap.add_argument('--heure-max', default='2100')
    ap.add_argument('--rejoue', action='store_true')
    ap.add_argument('--rejoue-ref', action='store_true')
    ap.add_argument('--sec', action='store_true')
    ap.add_argument('--diag-sauve', type=int)
    ap.add_argument('--diag-charge')
    a = ap.parse_args()
    import signal
    signal.signal(signal.SIGTERM, arrete)
    signal.signal(signal.SIGINT, arrete)
    c = Constr(resout(a.construction), a.jeu)
    jeu = c.jeu
    parties = [p for p in (a.parties.split(',') if a.parties else PARTIES[jeu])]
    for p in parties:
        if p not in PARTIES[jeu]:
            sys.exit('banc_ref : partie %s inconnue pour %s (%s)' % (p, jeu, ','.join(PARTIES[jeu])))
    cles = set(a.cles.split(',')) if a.cles else None
    diag = a.diag_sauve is not None or a.diag_charge
    r = Constr(resout(a.contre), jeu) if a.contre and not diag else None
    jc = Constr(resout(a.jumelle), jeu) if a.jumelle else None
    jr = Constr(resout(a.jumelle_ref), jeu) if a.jumelle_ref else (jc if r and r.C == c.C else None)
    nom = a.nom or '%s_contre_%s_%s' % (c.nom, r.nom if r else 'diag', time.strftime('%m%d_%H%M'))
    S = os.path.join(RUNS, nom)
    JC = plan(c, parties, cles, a.echantillon, jc)
    JR = plan(r, parties, cles, a.echantillon, jr) if r else []
    if diag:
        etd = os.path.join(ETATS, c.id)
        os.makedirs(etd, exist_ok=True)
        if len(JC) != 1:
            sys.exit('banc_ref : diagnostic = UNE partie (--parties P --cles K) ; ici %d' % len(JC))
        j = JC[0]
        if a.diag_sauve is not None:
            nm = '%s_%s_%s_i%d' % (c.id, j.partie, j.cle, a.diag_sauve)
            j.diag = {'nom': nm, 'sauve': a.diag_sauve, 'chemin': etd}
        else:
            nm = a.diag_charge
            e = os.path.join(etd, nm + '.empreinte')
            if not os.path.isfile(e) or open(e).read().split()[0] != c.id:
                sys.exit('banc_ref : REFUS : état %s absent ou d une autre construction (empreinte %s attendue)' % (nm, c.id))
            j.diag = {'nom': nm, 'charge': 1, 'chemin': etd}
    print('banc_ref : %s (%s, %s, menu ARCADE %s) contre %s ; %d + %d parties ; sortie %s' % (
        c.nom, jeu, c.id, 'oui' if c.menu_ca else 'non', (r.nom + ' (' + r.id + ', menu ARCADE ' + ('oui' if r.menu_ca else 'non') + ')') if r else '—',
        len(JC), len(JR), S))
    if a.sec:
        for j in (JC + JR)[:6]:
            print('  %s %s %s lua=%s tmax=%s\n    %s' % (j.c.nom, j.partie, j.cle, j.lua, j.tmax, ' '.join('%s=%s' % kv for kv in j.env if kv[0] != 'LISTE')[:600]))
        return 0
    if DISPLAY in (':0', ':0.0'):
        sys.exit('banc_ref : DISPLAY :0 interdit')
    if not os.path.exists('/tmp/.X11-unix/X' + DISPLAY.lstrip(':')):   # Xvfb de l'atelier, lancé ici (PID dans xvfb.pid)
        x = subprocess.Popen(['Xvfb', DISPLAY, '-screen', '0', '1024x768x24', '-nolisten', 'tcp'], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        open(os.path.join(ATELIER, 'xvfb.pid'), 'w').write('%d\n' % x.pid)
        time.sleep(2)
    os.makedirs(S, exist_ok=True)
    jl = open(S + '/journal.txt', 'a')
    vr = threading.Lock()

    def log(s):
        with vr:
            jl.write('%s %s\n' % (time.strftime('%H:%M:%S'), s))
            jl.flush()
    log('début : %s contre %s, %d + %d parties, %d places' % (c.nom, r.nom if r else '—', len(JC), len(JR), a.places))
    hm = int(a.heure_max)
    res = {}
    rejouees = []

    def dossier(j, cote):
        if j.lua is None:
            return None
        if cote == 'ref':
            return os.path.join(CACHE, j.c.id, j.partie, j.cle)
        return os.path.join(S, 'diag' if j.diag else 'cand', j.partie, j.cle)

    def un(arg):
        j, cote = arg
        D = dossier(j, cote)
        if D is None:
            res[(cote, j.partie, j.cle)] = (D, 'pas de partie')
            return
        ctx = contexte(j, D)
        ok_cache = fini(D) and ctx_de(D) == ctx
        if ok_cache and not ((cote == 'ref' and a.rejoue_ref) or (cote == 'cand' and a.rejoue)):
            res[(cote, j.partie, j.cle)] = (D, 'cache' if cote == 'ref' else 'reprise')
            return
        if ARRET.is_set():
            res[(cote, j.partie, j.cle)] = (D, 'NON FAIT (arrêt)')
            return
        if int(time.strftime('%H%M')) >= hm:
            res[(cote, j.partie, j.cle)] = (D, 'NON FAIT (heure)')
            log('NON FAIT (heure) %s %s %s' % (cote, j.partie, j.cle))
            return
        if cote == 'ref' and ctx_de(D) is not None and ctx_de(D) != ctx:
            d = sorted(set(ctx_de(D)) ^ set(ctx))
            rejouees.append('%s %s : %s' % (j.partie, j.cle, ' | '.join(d[:4])))
        rc = lance(j, D)
        log('%s %s %s %s code %d' % (cote, j.c.nom, j.partie, j.cle, rc))
        if cote == 'cand' and not j.diag and fini(D):
            dc = os.path.join(CACHE, j.c.id, j.partie, j.cle)
            if not os.path.lexists(dc):     # jamais écraser une entrée du cache (une référence peut y tourner)
                os.makedirs(os.path.dirname(dc), exist_ok=True)
                subprocess.run(['cp', '-al', D, dc])
                # le contexte normalise les chemins (TRACE) : il reste valable à cet endroit
        if j.diag and 'sauve' in j.diag:
            with open(os.path.join(j.diag['chemin'], j.diag['nom'] + '.empreinte'), 'w') as f:
                f.write('%s %s %s image %s (DIAGNOSTIC, jamais une preuve)\n' % (c.id, j.partie, j.cle, j.diag['sauve']))
        res[(cote, j.partie, j.cle)] = (D, 'joué')
    # référence d'abord pour chaque clé, en alternance (les paires finissent ensemble)
    R = {(j.partie, j.cle): j for j in JR}
    ordre = []
    for j in JC:
        if (j.partie, j.cle) in R:
            ordre.append((R[(j.partie, j.cle)], 'ref'))
        ordre.append((j, 'cand'))
    ordre.sort(key=lambda x: -x[0].tmax)
    with ThreadPoolExecutor(a.places) as tp:
        list(tp.map(un, ordre))
    # ------------------------------------------------------------------ résultats
    A = lit_attendus(a.attendus)
    lignes = []
    par = {}
    for j in JC:
        Dc = res.get(('cand', j.partie, j.cle), (None, ''))[0]
        vc = ('DIAG', 'non évalué', 'état chargé : les repères d images du Lua repartent du chargement') if j.diag else \
            verdict(j, Dc) if (Dc is None or fini(Dc)) else ('NON FAIT', '', res.get(('cand', j.partie, j.cle), ('', ''))[1])
        jr_ = R.get((j.partie, j.cle))
        if jr_ is None or Dc is None:
            vr_, cl, det, ncap = ('—', '', ''), 'sans référence' if r else ('diagnostic (état chargé)' if j.diag else 'seul'), [], ''
        else:
            Dr = res.get(('ref', j.partie, j.cle), (None, ''))[0]
            vr_ = verdict(jr_, Dr) if fini(Dr) else ('NON FAIT', '', '')
            if not (fini(Dr) and fini(Dc)):
                cl, det, ncap = 'NON FAIT', [], ''
            elif cle_banc(ctx_de(Dr)) != cle_banc(ctx_de(Dc)):
                d = sorted(set(cle_banc(ctx_de(Dr))) ^ set(cle_banc(ctx_de(Dc))))
                cl, det, ncap = 'NON COMPARABLE', [('contexte', d[:4])], ''
            else:
                det, n, k = compare(Dr, Dc)
                ncap = '%d/%d' % (k, n)
                if not det:
                    cl = 'IDENTIQUE'
                elif all(couvert(A, j.partie, j.cle, q, v) for q, v in det):
                    cl = 'ATTENDU'
                else:
                    cl = 'À QUALIFIER'
        if j.diag:
            cl = 'diagnostic (état chargé)' if 'charge' in j.diag else 'diagnostic (état sauvegardé)'
        reg = vc[0] in ('KO', 'VIDE') and vr_[0] == 'OK'
        lignes.append((j.partie, j.cle, vc, vr_, cl, det, ncap, reg))
        par.setdefault(j.partie, []).append(lignes[-1])
    with open(S + '/resultats.tsv', 'w', encoding='utf-8') as f:
        f.write('partie\tcle\tverdict_cand\tmesure_cand\tdetail_cand\tverdict_ref\tmesure_ref\tcomparaison\tcaptures_identiques\tdifferences\n')
        for p, k, vc, vr_, cl, det, ncap, reg in lignes:
            f.write('\t'.join([p, k, vc[0], vc[1], vc[2], vr_[0], vr_[1], cl, ncap, ' ; '.join('%s: %s' % (q, ' '.join(v)) for q, v in det)]) + '\n')
    nreg = sum(1 for x in lignes if x[7])
    nko = sum(1 for x in lignes if x[2][0] in ('KO', 'VIDE'))
    nq = sum(1 for x in lignes if x[4] in ('À QUALIFIER', 'NON COMPARABLE'))
    nat = sum(1 for x in lignes if x[4] == 'ATTENDU')
    nnf = sum(1 for x in lignes if x[4] == 'NON FAIT' or x[2][0] == 'NON FAIT')
    if diag:
        etat = 'DIAGNOSTIC (état chargé ou sauvegardé) — NE COMPTE PAS COMME PREUVE'
    elif nreg:
        etat = 'RÉGRESSION (%d partie(s) OK à la référence, KO au candidat)' % nreg
    elif nko:
        etat = 'KO (%d partie(s) en échec, aussi à la référence)' % nko
    elif nq:
        etat = 'DIFFÉRENCES À QUALIFIER (%d)' % nq
    elif nat:
        etat = 'DIFFÉRENCES ATTENDUES SEULEMENT (%d)' % nat
    else:
        etat = 'IDENTIQUE'
    if nnf and not diag:
        etat += ' ; %d NON FAIT(S)' % nnf
    with open(S + '/RESUME.md', 'w', encoding='utf-8') as f:
        f.write('# Banc unique : %s contre %s — %s\n\n' % (c.nom, r.nom if r else '—', etat))
        f.write('%s ; jeu %s ; construction `%s` (empreinte %s, menu sur ARCADE : %s) ; référence `%s`%s ; places %d ; '
                'références figées des tuiles : %s ; attendus : %s.\n\n' % (
                    time.strftime('%F %H:%M'), jeu, c.C, c.emp, 'oui' if c.menu_ca else 'non', r.C if r else '—',
                    (' (empreinte %s, menu sur ARCADE : %s)' % (r.emp, 'oui' if r.menu_ca else 'non')) if r else '', a.places,
                    os.path.relpath(REFS, W), a.attendus or 'aucun'))
        if diag:
            f.write('**DIAGNOSTIC (état chargé / sauvegardé par le Lua)** : partie de mise au point, JAMAIS une preuve.\n\n')
        f.write('| partie | parties | cand OK | cand KO | identiques | attendues | à qualifier | non comparables | non faites | captures identiques |\n|---|---|---|---|---|---|---|---|---|---|\n')
        for p, L in par.items():
            nc = [x[6] for x in L if x[6]]
            tc = (sum(int(x.split('/')[0]) for x in nc), sum(int(x.split('/')[1]) for x in nc)) if nc else None
            f.write('| %s | %d | %d | %d | %d | %d | %d | %d | %d | %s |\n' % (
                p, len(L), sum(1 for x in L if x[2][0] == 'OK'), sum(1 for x in L if x[2][0] in ('KO', 'VIDE')),
                sum(1 for x in L if x[4] == 'IDENTIQUE'), sum(1 for x in L if x[4] == 'ATTENDU'),
                sum(1 for x in L if x[4] == 'À QUALIFIER'), sum(1 for x in L if x[4] == 'NON COMPARABLE'),
                sum(1 for x in L if x[4] == 'NON FAIT' or x[2][0] == 'NON FAIT'), ('%d/%d' % tc) if tc else '—'))
        f.write('\n## Parties (verdict du candidat ; comparaison)\n\n')
        for p, k, vc, vr_, cl, det, ncap, reg in lignes:
            if cl in ('IDENTIQUE', 'ATTENDU') and vc[0] == 'OK' and len(par[p]) > 6:
                continue     # grandes parties : seules les lignes à lire sont détaillées (tout est dans resultats.tsv)
            f.write('- %s %s : %s %s%s ; réf %s %s ; **%s**%s%s\n' % (
                p, k, vc[0], vc[1], (' (' + vc[2] + ')') if vc[2] else '', vr_[0], vr_[1], cl, (' ; captures identiques ' + ncap) if ncap else '',
                ''.join('\n  - %s : %s%s' % (q, ' '.join(v[:16])[:220], ' …(%d)' % len(v) if len(v) > 16 else '') for q, v in det)))
        n_id = ['%s (%d identiques, %d attendues)' % (p, sum(1 for x in L if x[4] == 'IDENTIQUE'), sum(1 for x in L if x[4] == 'ATTENDU'))
                for p, L in par.items() if len(L) > 6]
        if n_id:
            f.write('- (grandes parties : lignes identiques ou attendues et OK non détaillées : %s)\n' % ', '.join(n_id))
        if rejouees:
            f.write('\n## Références REJOUÉES (leur contexte avait changé depuis le cache : à lire, c\'est une dérive du banc)\n\n' +
                    '\n'.join('- ' + x for x in rejouees[:20]) + '\n')
        if a.upper and 'fins' in par and not diag:
            f.write('\n## Fins contre Upper v161 (série %s)\n\n' % a.upper)
            f.write(compare_upper(S, JC, R, res, a.upper) + '\n')
        f.write('\nDétail : `resultats.tsv`, traces du candidat `cand/`, de la référence `%s` (cache), journal `journal.txt`.\n' %
                os.path.relpath(os.path.join(CACHE, r.id), ATELIER) if r else '\n')
    log('fin : %s' % etat)
    print(open(S + '/RESUME.md', encoding='utf-8').read())
    return 0 if etat.startswith(('IDENTIQUE', 'DIFFÉRENCES ATTENDUES', 'DIAGNOSTIC')) else 1


def compare_upper(S, JC, R, res, serie):
    """cmp_fins_upper.py sur une vue (liens) : c_<p>_<v> = candidat, r_<p>_<v> = référence (témoin), u_<p> = Upper"""
    V = os.path.join(S, 'vue_upper')
    if os.path.isdir(V):
        shutil.rmtree(V)
    os.makedirs(V)
    for j in JC:
        if j.partie != 'fins':
            continue
        p = j.cle.split('_')[0]
        for pref, cote in (('c', 'cand'), ('r', 'ref')):
            D = res.get((cote, 'fins', j.cle), (None,))[0]
            if D and fini(D):
                os.symlink(D, os.path.join(V, '%s_%s' % (pref, j.cle)))
                if os.path.isfile(D + '/sf.txt'):
                    os.symlink(D + '/sf.txt', os.path.join(V, '%s_%s.sf' % (pref, j.cle)))
        for x in ('u_%s' % p, 'u_%s.sf' % p):
            if os.path.exists(os.path.join(serie, x)) and not os.path.lexists(os.path.join(V, x)):
                os.symlink(os.path.join(serie, x), os.path.join(V, x))
    out = os.path.join(S, 'fins_contre_upper.md')
    rr = subprocess.run(['python3', '-I', CMP_UPPER, V, 'c', 'r', '--sortie', out, '--upper', 'u'], capture_output=True, text=True)
    if rr.returncode != 0 or not os.path.isfile(out):
        return 'cmp_fins_upper.py a échoué : %s' % (rr.stderr.strip()[-300:])
    t = open(out, encoding='utf-8').read().splitlines()
    return '\n'.join(t[:4]) + '\n\n(tableau complet : `fins_contre_upper.md` ; série d Upper : contexte de l oracle, greffe_arcade/fige/ro5_v161)'


if __name__ == '__main__':
    sys.exit(principal())
