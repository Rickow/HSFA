#!/usr/bin/env python3
"""Banc des coups : un geste de J1 contre une liste d'adversaires, sur Upper (+MAX), Hyper ou SFA3 d'arcade, dans le
coeur FBNeo HSFA (frontal tools/fbneo-hsfa/essais/joue_linux.c). Pour chaque essai : partie VERSUS depuis la mise
sous tension, geste a debut de manche + 303 images, vie de J2 ($FF8850) lue dans la RAM a 11 instants.

  banc_coups.py --jeu upper|hyper|arcade --j1 0a --gestes sd_30_n_mp,hp --adv 00,0d,2e [--trace] [--sortie DOSSIER]

Variables : HSFA_JOUE (frontal joue_linux), HSFA_COEUR (fbneo_hsfa_libretro.so), HSFA_SYS (dossier system),
HSFA_ZIP (archive du jeu : sfa3uhsfa.zip, sfa3hhsfa.zip ou sfa3.zip ; nom attendu par le coeur).

Selection des persos :
  upper  : pieces et Start par HSFA_ENTREES (Start J2 une seule fois, AVANT la grille : depuis le patch 11, Start sur
           la grille sert aux EX et Select a la roulette), puis HSFA_TOURNEE="00/00" pour valider et HSFA_POKE de
           l'octet perso (68K +$103 en ordre de la traduction) pendant la selection. ISM : celle par defaut d'Upper
           (X-ISM, octet $133 = $FF).
  hyper  : HSFA_TOURNEE="<j1>/<adv>" (ex. 0a.Z3.iX/0d.Z3.iX) ; ISM dans la specification.
  arcade : pieces sur l'ecran titre, poing faible repete, HSFA_POKE de +$102 (ordre 68K) ; A-ISM par defaut.
Les temps (debut de manche 2627 Upper, 3466 arcade ; Hyper : mesure par paire) valent pour les archives et le coeur notes dans
docs/rapports/recherche/D-SONDES.md ; a remesurer (journal de HSFA_TOURNEE, ou --trace) sur une autre construction.

Gestes (J1 a gauche, temps relatifs au debut du geste T0 ; boutons RETRO_DEVICE_ID_JOYPAD : Y = LP, X = MP, L = HP,
B = LK, A = MK, R = HK) :
  hp            Head Press : bas charge 60, haut + MK
  hpsd_<t>_<d>  Head Press puis <d> (av / ar) + MP a +60+t
  sd_<t>_<d>_<p> Somersault Skull Diver : bas charge 60, haut + <p> (lp / mp / hp), puis <p> (+ <d> : av / ar / n) a +60+t
"""
import argparse, os, struct, subprocess, sys

H, B, G, D = 4, 5, 6, 7
LP, MP, HP, LK, MK, HK = 1, 9, 10, 0, 8, 11
JEUX = {'upper': 2627, 'hyper': 1108, 'arcade': 3466}     # image du debut de manche (MANCHE du journal de tournee.h)
_DEBUTS = {}

def debut_manche(jeu, j1, adv):
    """image MANCHE : fixe pour upper et arcade (persos imposes) ; pour hyper, elle depend du trajet du curseur sur la
    grille, donc mesuree une fois par paire (partie courte, journal de tournee.h)"""
    if jeu != 'hyper': return JEUX[jeu]
    k = (j1, adv)
    if k not in _DEBUTS:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, HSFA_NOROUL='1', HSFA_TOURNEE=f'{j1}/{adv}', HSFA_TOURNEE_PASSIF='1',
                       HSFA_TOURNEE_PV='1', HSFA_TOURNEE_LOG='t.log')
            subprocess.run([os.environ['HSFA_JOUE'], os.environ['HSFA_COEUR'],
                            os.environ.get('HSFA_ZIP_HYPER', os.environ.get('HSFA_ZIP')), os.environ['HSFA_SYS'], '2500', 'o.wav'],
                           cwd=d, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
            m = [l.split() for l in open(f'{d}/t.log') if l.startswith('MANCHE')]
            _DEBUTS[k] = int(m[0][3]) if m else JEUX['hyper']
    return _DEBUTS[k]
ECART = int(os.environ.get('HSFA_ECART', '303'))   # images entre le debut de manche et le geste (intros longues : 450)

def u16(r, a): o = a - 0xFF0000; return r[o] | r[o + 1] << 8   # mot 68K (RAM du coeur : mots dans l'ordre de l'hote)
def u8(r, a): return r[(a - 0xFF0000) ^ 1]

def geste(nom, t0):
    L = []
    if nom.startswith('sd_'):
        _, t, dr, bt = nom.split('_'); t = int(t); p = {'lp': LP, 'mp': MP, 'hp': HP}[bt]
        L += [(t0, t0 + 60, 0, B), (t0 + 60, t0 + 66, 0, H), (t0 + 61, t0 + 65, 0, p), (t0 + 60 + t, t0 + 64 + t, 0, p)]
        if dr != 'n': L += [(t0 + 58 + t, t0 + 66 + t, 0, D if dr == 'av' else G)]
    elif nom.startswith('hpsd_'):
        _, t, dr = nom.split('_'); t = int(t)
        L += [(t0, t0 + 60, 0, B), (t0 + 60, t0 + 66, 0, H), (t0 + 61, t0 + 65, 0, MK),
              (t0 + 58 + t, t0 + 66 + t, 0, D if dr == 'av' else G), (t0 + 60 + t, t0 + 64 + t, 0, MP)]
    elif nom == 'hp':
        L += [(t0, t0 + 60, 0, B), (t0 + 60, t0 + 66, 0, H), (t0 + 61, t0 + 65, 0, MK)]
    else:
        sys.exit('geste inconnu : ' + nom)
    return L

def amorce(jeu):
    L = []
    if jeu == 'upper':
        for k in range(1500, 1860, 60): L += [(k, k + 8, 0, 2), (k, k + 8, 1, 2)]
        L += [(1900, 1906, 0, 3), (1920, 1926, 1, 3)]
    elif jeu == 'arcade':
        for k in range(2700, 3000, 30): L += [(k, k + 4, 0, 2), (k + 10, k + 14, 1, 2)]
        L += [(3100, 3106, 0, 3), (3130, 3136, 1, 3)]
        for k in range(3240, 3460, 16): L += [(k, k + 4, 0, LP), (k + 8, k + 12, 1, LP)]
    return L

def essai(a, nom, adv, capt, dossier, gestes=None, pokes=()):
    """gestes : entrees du geste (sinon geste(nom)) ; pokes : (debut, fin, adresse, octet) en plus du choix des persos"""
    dossier = os.path.abspath(dossier); os.makedirs(dossier, exist_ok=True)   # le frontal tourne dans ce dossier
    t0 = debut_manche(a.jeu, a.j1, adv) + ECART
    with open(f'{dossier}/entrees.txt', 'w') as f:
        for e in amorce(a.jeu) + (gestes if gestes is not None else geste(nom, t0)): f.write('%d %d %d %d\n' % e)
    pk = ','.join('%d-%d:%x:%02x' % q for q in pokes)
    env = dict(os.environ, HSFA_ENTREES=f'{dossier}/entrees.txt', HSFA_RAM_DUMP='1')
    if a.jeu == 'upper':
        env.update(HSFA_NOROUL='1', HSFA_TOURNEE='00/00', HSFA_TOURNEE_PASSIF='1', HSFA_TOURNEE_PV='1',
                   HSFA_TOURNEE_LOG='tournee.log', HSFA_POKE=','.join(x for x in (f'1944-2060:ff8503:{a.j1},1944-2060:ff8903:{adv}', pk) if x))
    elif a.jeu == 'hyper':
        env.update(HSFA_NOROUL='1', HSFA_TOURNEE=f'{a.j1}/{adv}', HSFA_TOURNEE_PASSIF='1', HSFA_TOURNEE_PV='1',
                   HSFA_TOURNEE_LOG='tournee.log')
        if pk: env.update(HSFA_POKE=pk)
    else:
        env.update(HSFA_POKE=','.join(x for x in (f'3200-3400:ff8502:{a.j1},3200-3400:ff8902:{adv}', pk) if x))
    subprocess.run([os.environ['HSFA_JOUE'], os.environ['HSFA_COEUR'], os.environ.get('HSFA_ZIP_' + a.jeu.upper(), os.environ.get('HSFA_ZIP')), os.environ['HSFA_SYS'],
                    str(max(capt) + 2), os.environ.get('HSFA_SON', os.devnull)] + [str(c) for c in capt],
                   cwd=dossier, env=env, stdout=subprocess.DEVNULL, stderr=open(f'{dossier}/coeur.txt', 'w'), timeout=900)
    rams = [open(f'{dossier}/ram_{c:06d}.bin', 'rb').read() for c in capt]
    return t0, rams

def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--jeu', choices=JEUX, required=True); p.add_argument('--j1', required=True)
    p.add_argument('--gestes', required=True); p.add_argument('--adv', required=True)
    p.add_argument('--sortie', default='banc_coups'); p.add_argument('--trace', action='store_true',
                   help='positions de J1 de +60 a +184 (pas de 4) au lieu des vies')
    a = p.parse_args()
    xo = 0x10 if a.jeu == 'arcade' else 0x12                    # X : +$10 sur l'arcade, +$12 dans les traductions
    for nom in a.gestes.split(','):
        for adv in a.adv.split(','):
            d = f'{a.sortie}/{a.jeu}_{nom}_{a.j1}_{adv}'
            t0 = debut_manche(a.jeu, a.j1, adv) + ECART
            if a.trace:
                pts = []
                for t in (60, 124):
                    capt = [t0 + t + 4 * k for k in range(16)]
                    _, rams = essai(a, nom, adv, capt, f'{d}_{t}')
                    pts += [(c - t0, u16(r, 0xFF8400 + xo), u16(r, 0xFF8416)) for c, r in zip(capt, rams)]
                print(f'{a.jeu} {nom} {a.j1}/{adv} : ' + ' '.join(f'+{t}:{x:03x},{y:02x}' for t, x, y in pts), flush=True)
            else:
                capt = [t0 - 1] + list(range(t0 + 60, t0 + 241, 20))
                _, rams = essai(a, nom, adv, capt, d)
                v = [u16(r, 0xFF8850) for r in rams]
                pid = 0xFF8502 if a.jeu == 'arcade' else 0xFF8503
                ism = u8(rams[0], 0xFF8532 if a.jeu == 'arcade' else 0xFF8533)
                print(f'{a.jeu:6s} {nom:14s} J1 {u8(rams[0], pid):02x} J2 {u8(rams[0], pid + 0x400):02x} ISM {ism:02x} | '
                      f'vie J2 {v[0]} -> {min(v)} (degats {v[0] - min(v)}) ; ' + ' '.join(map(str, v)), flush=True)
                for c in capt[1:]: os.remove(f'{d}/ram_{c:06d}.bin')

if __name__ == '__main__':
    main()
