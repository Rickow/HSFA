#!/usr/bin/env python3
"""(banc_coups) VERDICTS d'un passage du banc : traduction (journal --tr) contre l'oracle arcade (--ref), ou seule
(critere « le coup sort, se termine, rend le controle »), ou contre une arcade d'une autre generation (--famille :
meme famille d'effet).

Usage : compare.py --index i.tsv --tr tr/log.txt [--ref ref/log.txt [--famille]] --module ro3 --sortie v.tsv
Sortie : une ligne par variante (id, ligne, jeu, perso, ism/version, type, coup, variante, verdict, cause, detail).
Verdicts : OK ; KO (cause) ; NC = non concluant (le coup ne sort pas a l'arcade non plus avec cette manip : manip,
condition ou isme a revoir) ; NT = non testable (raison de l'index).
"""
import argparse, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from journal import lit, resume


def sort(r):
    """le coup a-t-il produit un effet ? special / super, lancer ($5 = 4), objet, degats"""
    lancer = any(s[2:4] == '04' for s in r['etats'])
    return bool(r['special'] or lancer or r['objets'] or r['degats'] > 0), lancer


def effet(r):
    s, lancer = sort(r)
    e = []
    if r['special'] == '0e':
        e.append('spécial')
    if r['special'] == '10':
        e.append('super')
    if lancer:
        e.append('lancer')
    if r['objets']:
        e.append('objet')
    if r['degats']:
        e.append('dégâts')
    return e


def court(r):
    return 'sp=%s n=%s deg=%d/%d obj=%s retour=%s' % (r['special'] or '-', r['num'] or '-', r['degats'], r['degats1'],
                                                     ','.join(r['objets']) or '-', r['retour'])


def prefixe(a, b):
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def decalage(R, T):
    """memes suites d'etats (a la coupure de la fenetre pres) mais instants differents : renvoie la description du
    premier decalage (joueur, etat, images), sinon None"""
    if not (prefixe(R['etats'], T['etats']) and prefixe(R['etats2'], T['etats2'])):
        return None
    for j, (a, b) in (('J1', (R['t1'], T['t1'])), ('J2', (R['t2'], T['t2']))):
        ia = [(s, t) for s, t in a]
        ib = [(s, t) for s, t in b]
        # alignement sur la suite des etats (les transitoires d'une image peuvent manquer d'un cote)
        db = {}
        for s, t in ib:
            db.setdefault(s, []).append(t)
        for s, t in ia:
            if s in db and db[s]:
                t2 = db[s].pop(0)
                if t2 != t:
                    return 'même suite d\'états, %s décalé de %+d image(s) à l\'état %s (image %d arcade)' % (j, t2 - t, s, t)
    return None


def verdict_oracle(R, T):
    so_r, _ = sort(R)
    if T['exc']:
        return 'KO', 'exception pc=%s' % T['exc']
    if T['trop_long']:
        return 'KO', 'essai sans fin (blocage)'
    egal = (R['etats'] == T['etats'] and R['etats2'] == T['etats2'] and R['anim'] == T['anim'] and R['degats'] == T['degats'] and R['degats1'] == T['degats1']
            and R['objets'] == T['objets'] and R['num'] == T['num'])
    if egal:
        return ('OK', '') if so_r else ('NC', 'ne sort pas à l\'arcade non plus (manip / condition / isme)')
    d = decalage(R, T)
    if d and R['degats'] == T['degats'] and R['objets'] == T['objets'] and R['num'] == T['num'] and R['degats1'] == T['degats1']:
        return 'DÉCALÉ', d
    if R['special'] and not T['special']:
        return 'KO', 'le coup ne sort pas (arcade : %s n°%s)' % ('super' if R['special'] == '10' else 'spécial', R['num'])
    if not R['special'] and T['special']:
        return 'KO', 'coup spécial inattendu (n°%s) : l\'arcade ne le fait pas' % T['num']
    if R['num'] != T['num']:
        return 'KO', 'mauvais coup : n° $AA arcade %s, traduit %s' % (R['num'], T['num'])
    if R['etats'] != T['etats'] or R['etats2'] != T['etats2']:
        if R['etats'] == T['etats']:
            a, b = R['etats2'], T['etats2']
            i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
            return 'KO', 'réaction de J2 différente (rang %d : arcade %s, traduit %s)' % (
                i, ' '.join(a[i:i + 3]) or 'fin', ' '.join(b[i:i + 3]) or 'fin')
        # premiere divergence
        i = next((k for k in range(min(len(R['etats']), len(T['etats']))) if R['etats'][k] != T['etats'][k]),
                 min(len(R['etats']), len(T['etats'])))
        return 'KO', 'suite d\'états différente (rang %d : arcade %s, traduit %s)' % (
            i, R['etats'][i] if i < len(R['etats']) else 'fin', T['etats'][i] if i < len(T['etats']) else 'fin')
    if R['degats'] != T['degats']:
        return 'KO', 'dégâts différents (arcade %d, traduit %d)' % (R['degats'], T['degats'])
    if R['degats1'] != T['degats1']:
        return 'KO', 'dégâts subis par J1 différents (arcade %d, traduit %d)' % (R['degats1'], T['degats1'])
    if R['objets'] != T['objets']:
        return 'KO', 'objets différents (arcade %s, traduit %s)' % (','.join(R['objets']) or '-', ','.join(T['objets']) or '-')
    a, b = R['anim'], T['anim']
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    return 'KO', 'animation différente, même suite d\'états (pas %d/%d : arcade %s, traduit %s)' % (
        i, len(a), a[i] if i < len(a) else 'fin', b[i] if i < len(b) else 'fin')


def verdict_seul(T):
    so, _ = sort(T)
    if T['exc']:
        return 'KO', 'exception pc=%s' % T['exc']
    if T['trop_long']:
        return 'KO', 'essai sans fin (blocage)'
    if not so:
        return 'NC', 'aucun effet (pas de spécial, d\'objet ni de dégâts) : coup absent ou manip à revoir'
    if not T['neutre'] or T['retour'] is None:
        return 'KO', 'ne rend pas le contrôle (état final %s)' % (T['etats'][-1] if T['etats'] else '?')
    return 'OK', ''


def verdict_famille(R, T):
    """arcade d'une autre generation (SFA1 / SFA2) : meme famille d'effet"""
    v, c = verdict_seul(T)
    if v == 'KO' and c.startswith('ne rend pas') and (not R['neutre'] or R['retour'] is None):
        v, c = 'OK', ''   # l'arcade non plus n'a pas rendu la main dans la fenetre : coup long, pas un defaut
    if v == 'KO':
        return v, c
    er, et = effet(R), effet(T)
    if not er:
        return ('NC', 'ne sort pas à l\'arcade (%s) non plus' % c) if v == 'NC' else ('OK*', 'sort ; l\'arcade ne le fait pas avec cette manip')
    if v == 'NC':
        return 'KO', 'le coup ne sort pas (arcade : %s)' % '+'.join(er)
    fam = lambda e: set(x for x in e if x in ('spécial', 'super', 'lancer', 'objet'))
    if fam(er) - fam(et):
        return 'KO', 'famille d\'effet différente (arcade %s, traduit %s)' % ('+'.join(er), '+'.join(et))
    return 'OK', ''


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', required=True)
    ap.add_argument('--tr', required=True)
    ap.add_argument('--ref')
    ap.add_argument('--famille', action='store_true')
    ap.add_argument('--module', default='')
    ap.add_argument('--sortie', required=True)
    a = ap.parse_args()
    ET, infot = lit(a.tr)
    ER, infor = lit(a.ref) if a.ref else ({}, {})
    rows = list(csv.DictReader(open(a.index), delimiter='\t'))
    n = {}
    with open(a.sortie, 'w') as f:
        f.write('module\tid\tligne\tjeu\tperso\tism\ttype\tcoup\tvariante\tverdict\tcause\tdetail\n')
        for r in rows:
            base = [a.module, r['id'], r['ligne'], r['jeu'], r['perso'], r['ism'], r['type'], r['coup'], r['variante']]
            if r['statut'] == 'NT':
                v, c, d = 'NT', r['raison'], ''
            elif r['id'] not in ET:
                v, c, d = 'KO', 'essai non joué (%s)' % (infot.get('fin') or 'journal interrompu'), ''
            else:
                T = resume(ET[r['id']])
                if a.ref and r['id'] in ER:
                    R = resume(ER[r['id']])
                    v, c = verdict_famille(R, T) if a.famille else verdict_oracle(R, T)
                    d = 'arcade[%s] trad[%s]' % (court(R), court(T))
                else:
                    v, c = verdict_seul(T)
                    if 'palette' in r.get('drapeaux', '') and r['type'] in ('special', 'super') and not T['special'] and v != 'KO':
                        v, c = 'NC', 'pas de spécial sur cette commande (coup normal ou rien)'
                    d = 'trad[%s] effet=%s' % (court(T), '+'.join(effet(T)) or '-')
            n[v] = n.get(v, 0) + 1
            f.write('\t'.join(base + [v, c, d]) + '\n')
    print(a.module, ' '.join('%s=%d' % kv for kv in sorted(n.items())), infot.get('save', ''))
