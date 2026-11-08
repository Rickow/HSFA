#!/usr/bin/env python3
"""(banc_coups) Lecture d'un journal de lua/banc_coups.lua -> resume par essai.

Resume d'un essai (dict) :
  etats   suite des etats distincts de J1 (octets $4-$7), etats d'UNE image ignores (cadence turbo, HANDOFF §93)
  brut    suite exacte (etat, nombre d'images)
  classes ensemble des sous-etats $6 vus ; special : $6 = $0E (special), $10 (super) ; n° = octet $AA a l'entree
  anim    suite des empreintes d'animation distinctes (4 mots au pointeur $1C), anim_ptr idem en pointeurs
  degats  vie perdue par J2 (vie remise a $90 avant l'essai) ; etats2 suite des etats de J2
  objets  suite des objets apparus (mot $2 = classe/type), dans l'ordre d'apparition
  exc     exception (pc) ; fin derniere image d'entree ; neutre = J1 revenu au neutre a la fin (rend le controle)
  retour  image de retour au neutre (apres avoir quitte le neutre)
"""
import collections, os
# vitesse NORMAL (defaut du banc) : chaque tour est vu, on garde tous les etats (MINI=1) ; en turbo, MINI=2
MINI = int(os.environ.get("MINI", "1"))

def neutre(s):
    """J1 « a la main » : routine 2, $5 = 0, $6 = 0 (debout), 2 (accroupi), 4 (marche)"""
    return s[0:4] == '0200' and s[4:6] in ('00', '02', '04')


def dedup(seq, mini=2, poids=None):
    """etats consecutifs regroupes ; on retire ceux qui durent moins de mini TOURS DE JEU (poids = tours de chaque
    image ; une image sans tour, saut de cadence de la traduction, ne compte pas), puis on refusionne"""
    g = []
    for i, s in enumerate(seq):
        w = 1 if poids is None else poids[i]
        if w == 0:
            continue
        if g and g[-1][0] == s:
            g[-1][1] += w
        else:
            g.append([s, w])
    brut = [tuple(x) for x in g]
    # etats d'initialisation (dernier octet $00) vus une seule image : transitoires, leur visibilite depend de l'ordre
    # de traitement des objets dans le tour (lancers : J2 vu en 02020000 dans une machine et pas dans l'autre)
    g = [s for s, n in g if n >= mini and not (n == 1 and isinstance(s, str) and len(s) == 8 and s.endswith('00'))]
    g = [s for i, s in enumerate(g) if i == 0 or s != g[i - 1]]
    return g, brut


def lit(p):
    E = collections.OrderedDict()
    cur = None
    info = {}
    for l in open(p, errors='replace'):
        t = l.split()
        if not t:
            continue
        if t[0] == 'SAVE':
            info['save'] = l.strip()
        elif t[0] == 'T':
            cur = {'id': t[1], 'nom': ' '.join(t[2:]), 'F': [], 'O': [], 'exc': None, 'fin': None}
            E[t[1]] = cur
        elif t[0] == 'F' and cur is not None:
            # F id r e1 e2 x1 y1 x2 vie2 aa ptr fp jauge sens
            cur['F'].append((int(t[2]), t[3], t[4], int(t[5], 16), int(t[6], 16), int(t[7], 16), int(t[8], 16),
                             int(t[9], 16), t[10], t[11], int(t[12], 16), int(t[13], 16),
                             int(t[14]) if len(t) > 14 else 0, int(t[15], 16) if len(t) > 15 else 0x90))
        elif t[0] == 'O' and cur is not None:
            cur['O'].append((int(t[2]), t[3], t[4], t[5]))
        elif t[0] == 'X' and cur is not None:
            cur['exc'] = t[3]
        elif t[0] == 'R' and cur is not None:
            cur['fin'] = int(t[2])
            cur['trop_long'] = len(t) > 3
        elif t[0] in ('FIN', 'PAS'):
            info['fin'] = l.strip()
    return E, info


def resume(e):
    F = [f for f in e['F'] if f[0] >= 8]
    r = {'id': e['id'], 'nom': e['nom'], 'exc': e['exc'], 'trop_long': e.get('trop_long', False)}
    st = [f[1] for f in F]
    tours = {f[0]: f[12] for f in e['F']}
    # poids d'une image : 1 si au moins un tour de jeu s'y est joue (on ne voit que l'etat du dernier tour), 0 sinon
    w = [min(1, max(0, f[12] - tours.get(f[0] - 1, f[12] - 1))) for f in F]
    r["etats"], r["brut"] = dedup(st, MINI, w)
    r['classes'] = sorted(set(s[4:6] for s in st))
    sp = [f for f in F if f[1][4:6] in ('0e', '10')]
    r['special'] = sp[0][1][4:6] if sp else None
    r['num'] = '%02x' % sp[0][7] if sp else None
    r['anim'], _ = dedup([f[9] for f in F], MINI, w)
    r['degats'] = 0x90 - min([f[6] for f in F] or [0x90])
    r['etats2'], _ = dedup([f[2] for f in F], MINI, w)
    r['degats1'] = 0x90 - min([f[13] for f in F] or [0x90])   # vie perdue par J1 (contre, echange)
    vus, objs = set(), []
    for (rr, adr, mot, et) in e['O']:
        if rr >= 8 and (adr, mot) not in vus:
            vus.add((adr, mot))
            objs.append(mot)
    # objets presents des l'image 1 (restes) ignores
    deja = set(mot for (rr, adr, mot, et) in e['O'] if rr < 8)
    r['objets'] = [o for o in objs if o not in deja] if deja else objs
    r['neutre'] = bool(F) and neutre(F[-1][1])
    quitte, retour = None, None
    for f in F:
        if not neutre(f[1]) and quitte is None:
            quitte = f[0]
        if quitte is not None and retour is None and neutre(f[1]) and f[0] > quitte + 2:
            retour = f[0]
    r['quitte'], r['retour'] = quitte, retour
    # animation comparee pendant le coup seulement (jusqu'au retour au neutre + 2) : l'attente qui suit n'a pas de sens
    # (et a partir de la sortie du neutre : la phase de l'animation d'attente au moment de la sauvegarde differe
    # entre les deux machines)
    if quitte is not None:
        k = [i for i, f in enumerate(F) if f[0] > quitte and not neutre(f[1]) and (retour is None or f[0] <= retour + 2)]
        r['anim'], _ = dedup([F[i][9] for i in k], MINI, [w[i] for i in k])
    r['nimages'] = len(F)
    # instants (image) d'entree dans chaque etat retenu, pour J1 et J2 : sert a reconnaitre un simple decalage
    def instants(col):
        res, prec = [], None
        for f, ww in zip(F, w):
            if ww and f[col] != prec:
                res.append((f[col], f[0]))
                prec = f[col]
        return res
    r['t1'], r['t2'] = instants(1), instants(2)
    r['jauge0'] = F[0][10] if F else None
    r['jauge1'] = F[-1][10] if F else None
    return r


if __name__ == '__main__':
    import sys
    E, info = lit(sys.argv[1])
    print(info)
    for k, e in E.items():
        r = resume(e)
        print('%-9s %-28s sp=%s n=%s deg=%3d obj=%s exc=%s neutre=%s retour=%s cl=%s' % (
            k, r['nom'][:28], r['special'], r['num'], r['degats'], ','.join(r['objets']), r['exc'], r['neutre'], r['retour'], ','.join(r['classes'])))
        if len(sys.argv) > 2:
            print('     ', ' '.join(r['etats']))
