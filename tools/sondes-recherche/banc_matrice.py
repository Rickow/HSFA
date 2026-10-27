#!/usr/bin/env python3
"""Matrice des coups : chaque coup special / super / lancer de SFA3 du tableau BradyGames, joue par J1 contre Ryu
(J2 passif), a deux distances, jauge pleine, dans deux jeux (par defaut Hyper Z3 et SFA3 d'arcade, meme ISM) ; on
compare les degats sur J2. Les essais tournent en parallele (--proc).

  banc_matrice.py --tableau coups.csv --jeux hyper,arcade [--persos "R. Mika,Ryu"] [--ism A] [--force H]
                  [--proc 4] [--sortie DOSSIER] [--coup "R. Mika:↓↘→↓↘→:Kick"] [--adv 00,26]

Variables : HSFA_JOUE, HSFA_COEUR, HSFA_SYS (comme banc_coups.py) et HSFA_ZIP_<JEU> (HSFA_ZIP_HYPER, HSFA_ZIP_ARCADE,
HSFA_ZIP_UPPER). Sortie : <sortie>/matrice.tsv (une ligne par coup, distance et jeu) et le resume sur la sortie standard.

Geste : J1 a gauche (avant = droite). Chaque direction d'une manipulation est tenue 3 images ; « (charge) » tient la
premiere 60 images ; 360° = → ↘ ↓ ↙ ← ↖ ↑, 720° = deux fois ; le bouton part sur la derniere direction. « Punch » /
« Kick » = la force --force (L / M / H), « 2 Punch » = LP + MP, « 3 Punch » = les trois. Jauge : mot +$21C = $1B0 (3 niveaux de +$11E = $90), avant le geste.
Distance : « loin » = depart de manche (J1 x $220, J2 $2E0) ; « pres » = J2 replace a 56 px de J1 (x poke a T0 - 20).
Coups ignores : suites (« ← ou → », « puis »), coups en l'air, notations libres ; voir la colonne « raison ».
"""
import argparse, csv, os, re, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import banc_coups as bc

IDS = {'Ryu': 0x00, 'Ken': 0x01, 'Akuma': 0x02, 'Charlie': 0x03, 'Chun-Li': 0x04, 'Adon': 0x05, 'Sodom': 0x06,
       'Guy': 0x07, 'Birdie': 0x08, 'Rose': 0x09, 'M. Bison': 0x0a, 'Sagat': 0x0b, 'Dan': 0x0c, 'Sakura': 0x0d,
       'Rolento': 0x0e, 'Dhalsim': 0x0f, 'Zangief': 0x10, 'Gen': 0x11, 'Balrog': 0x15, 'Cammy': 0x16, 'E. Honda': 0x18,
       'Blanka': 0x19, 'R. Mika': 0x1a, 'Cody': 0x1b, 'Vega': 0x1c, 'Karin': 0x1d, 'Juli': 0x1e, 'Juni': 0x1f}
FL = {'→': (bc.D,), '←': (bc.G,), '↓': (bc.B,), '↑': (bc.H,), '↘': (bc.B, bc.D), '↙': (bc.B, bc.G),
      '↗': (bc.H, bc.D), '↖': (bc.H, bc.G)}
TOUR = '→↘↓↙←↖↑'
FORCE = {'L': (bc.LP, bc.LK), 'M': (bc.MP, bc.MK), 'H': (bc.HP, bc.HK)}
NOMS_B = {'LP': bc.LP, 'MP': bc.MP, 'HP': bc.HP, 'LK': bc.LK, 'MK': bc.MK, 'HK': bc.HK}

def boutons(txt, force):
    t = txt.strip()
    p, k = FORCE[force]
    if t == 'Punch': return [p]
    if t == 'Kick': return [k]
    if t in ('2 Punch',): return [bc.LP, bc.MP]
    if t in ('2 Kick',): return [bc.LK, bc.MK]
    if t in ('3 Punch', 'LP + MP + HP'): return [bc.LP, bc.MP, bc.HP]
    if t in ('3 Kick', 'LK + MK + HK'): return [bc.LK, bc.MK, bc.HK]
    if t in NOMS_B: return [NOMS_B[t]]
    return None

def directions(m):
    """manipulation -> (liste de directions, charge) ; None si notation non geree"""
    m = m.strip().replace(' ', '')
    if m in ('360°',): return list(TOUR), False
    if m in ('720°',): return list(TOUR) * 2, False
    charge = '(charge)' in m
    m = m.replace('(charge)', '')
    if not m or any(c not in FL for c in m): return None
    return list(m), charge

def geste(dirs, charge, bts, t0):
    L, t, dern = [], t0, t0
    for i, d in enumerate(dirs):
        n = 60 if (charge and i == 0) else 3
        for b in FL[d]: L.append((t, t + n, 0, b))
        dern = t; t += n
    for b in bts: L.append((dern + 1, dern + 5, 0, b))   # bouton pendant la derniere direction
    return L

def suite(nom, t):
    """suites martelees apres le coup (--suite) : 'course' = avant tenu 80 images et poings repetes (R. Mika)"""
    if nom == 'course':
        return [(t + 5, t + 85, 0, bc.D)] + [(t + k, t + k + 3, 0, bc.HP) for k in range(25, 140, 12)]
    return []

def coups(tableau, persos, ism, force, unique):
    R = []
    if unique:
        p, m, b = unique.split(':')
        R.append(dict(personnage=p, nom_du_coup='(essai)', type='?', manipulation=m, boutons=b, version_style='', conditions=''))
    else:
        R = [r for r in csv.DictReader(open(tableau, encoding='utf-8'), delimiter=';') if r['jeu'] == 'Street Fighter Alpha 3'
             and r['type'] in ('special', 'super', 'lancer') and (not persos or r['personnage'] in persos)]
    out = []
    for r in R:
        raison = ''
        if r['personnage'] not in IDS: raison = 'perso'
        vs = r['version_style']
        if not raison and vs and f'{ism}-ISM' not in vs and 'tous' not in vs.lower(): raison = f'pas en {ism}-ISM'
        c = r['conditions'].lower()
        if not raison and re.search(r'saut|en l\'air|après|pendant|apres', c): raison = 'condition : ' + r['conditions']
        d = directions(r['manipulation']) if not raison else None
        if not raison and d is None: raison = 'manipulation non geree'
        bts = boutons(r['boutons'], force) if not raison else None
        if not raison and bts is None: raison = 'boutons non geres'
        out.append(dict(r, dirs=d, bts=bts, raison=raison))
    return out

def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--tableau'); p.add_argument('--jeux', default='hyper,arcade')
    p.add_argument('--persos', default=''); p.add_argument('--ism', default='A', choices='XAV')
    p.add_argument('--force', default='H', choices='LMH'); p.add_argument('--proc', type=int, default=4)
    p.add_argument('--sortie', default='banc_matrice'); p.add_argument('--coup', default='')
    p.add_argument('--adv', default='00'); p.add_argument('--suite', default=''); p.add_argument('--distances', default='loin,pres')
    a = p.parse_args()
    persos = [x.strip() for x in a.persos.split(',') if x.strip()]
    liste = coups(a.tableau, persos, a.ism, a.force, a.coup)
    jeux = a.jeux.split(','); dists = a.distances.split(',')
    taches = []
    for i, r in enumerate(liste):
        if r['raison']: continue
        for adv in a.adv.split(','):
            for dist in dists:
                for jeu in jeux: taches.append((i, r, int(adv, 16), dist, jeu))
    print(f'{len(liste)} coups, {sum(1 for r in liste if not r["raison"])} joues, {len(taches)} essais', flush=True)
    os.makedirs(a.sortie, exist_ok=True)

    def un(t):
        i, r, adv, dist, jeu = t
        j1 = IDS[r['personnage']]
        ns = argparse.Namespace(jeu=jeu, j1=(f'{j1:02x}.Z3.i{a.ism}' if jeu == 'hyper' else f'{j1:02x}'))
        sadv = f'{adv:02x}.Z3.i{a.ism}' if jeu == 'hyper' else f'{adv:02x}'
        t0 = bc.debut_manche(jeu, ns.j1, sadv) + bc.ECART
        dirs, charge = r['dirs']
        g = geste(dirs, charge, r['bts'], t0)
        if a.suite: g += suite(a.suite, max(e[1] for e in g))
        xo = 0x10 if jeu == 'arcade' else 0x12
        pk = [(t0 - 60, t0 - 1, 0xFF861C, 0x01), (t0 - 60, t0 - 1, 0xFF861D, 0xB0)]          # jauge de J1 : 3 niveaux
        if dist == 'pres':
            x1, x2 = 0x260, 0x298
            for base, x in ((0xFF8400, x1), (0xFF8800, x2)):
                pk += [(t0 - 20, t0 - 19, base + xo, x >> 8), (t0 - 20, t0 - 19, base + xo + 1, x & 0xff)]
        capt = [t0 - 1] + list(range(t0 + 30, t0 + 391, 30))
        d = f'{a.sortie}/{i:03d}_{dist}_{adv:02x}_{jeu}'
        try:
            _, rams = bc.essai(ns, '', sadv, capt, d, gestes=g, pokes=pk)
        except Exception as e:
            return t, None, str(e)
        v = [bc.u16(rr, 0xFF8850) for rr in rams]
        for c in capt[1:]: os.remove(f'{d}/ram_{c:06d}.bin')
        chutes = sum(1 for x, y in zip(v, v[1:]) if y < x)
        return t, (v[0] - min(v), chutes, v), ''

    res = {}
    with ThreadPoolExecutor(a.proc) as ex:
        for n, (t, m, err) in enumerate(ex.map(un, taches)):
            res[(t[0], t[2], t[3], t[4])] = (m, err)
            if n % 20 == 0: print(f'  {n}/{len(taches)}', flush=True)
    with open(f'{a.sortie}/matrice.tsv', 'w', encoding='utf-8') as f:
        f.write('n\tperso\tcoup\ttype\tmanip\tboutons\tadv\tdistance\t' + '\t'.join(f'degats_{j}' for j in jeux) + '\tecart\traison\n')
        for i, r in enumerate(liste):
            if r['raison']:
                f.write(f'{i}\t{r["personnage"]}\t{r["nom_du_coup"]}\t{r["type"]}\t{r["manipulation"]}\t{r["boutons"]}\t\t\t' + '\t' * len(jeux) + f'\t{r["raison"]}\n')
                continue
            for adv in a.adv.split(','):
                for dist in dists:
                    ds = []
                    for j in jeux:
                        m, err = res[(i, int(adv, 16), dist, j)]
                        ds.append('err' if m is None else str(m[0]))
                    ec = 'ECART' if len(set(ds)) > 1 else ''
                    if not ec:                                     # captures gardees pour les ecarts seulement
                        for j in jeux:
                            dd = f'{a.sortie}/{i:03d}_{dist}_{int(adv, 16):02x}_{j}'
                            for fn in os.listdir(dd) if os.path.isdir(dd) else []:
                                if fn.endswith('.bmp'): os.remove(f'{dd}/{fn}')
                    f.write(f'{i}\t{r["personnage"]}\t{r["nom_du_coup"]}\t{r["type"]}\t{r["manipulation"]}\t{r["boutons"]}\t{adv}\t{dist}\t' + '\t'.join(ds) + f'\t{ec}\t\n')
                    if ec or a.coup: print(f'{r["personnage"]:9s} {r["nom_du_coup"][:28]:28s} {r["manipulation"]} {r["boutons"]} adv {adv} {dist} : ' + ' / '.join(f'{j} {x}' for j, x in zip(jeux, ds)), flush=True)

if __name__ == '__main__':
    main()
