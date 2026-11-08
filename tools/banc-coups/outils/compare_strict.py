#!/usr/bin/env python3
"""(banc_coups) NON-REGRESSION STRICTE : candidat contre reference (deux traductions), image par image.
Champs compares a chaque image : etats J1/J2, X1, Y1, X2, vie J2, $AA, empreinte du pas d'animation, jauge, sens,
vie J1, compteurs $32 ; objets actifs (adresse, mot $2, etat, X). Les pointeurs ($1C) et le compteur de tours ne sont pas
compares (les donnees MAX deplacent des blocs ; les tours different si la cadence differe, signale a part).
Usage : compare_strict.py --index i.tsv --ref ref/log.txt --cand cand/log.txt --sortie v.tsv [--etiquette x]
Verdicts : IDENTIQUE ; RALENTI (meme jeu tour par tour, mais des images sans tour de jeu en plus ou en moins :
ralentissement du 68K) ; DIFFÉRENT (1re image et champ, puis 1re difference par tour) ; KO (exception, essai non joue).
"""
import argparse, csv, collections

CH = {3: 'état J1', 4: 'état J2', 5: 'X1', 6: 'Y1', 7: 'X2', 8: 'vie J2', 9: '$AA', 11: 'pas anim', 12: 'jauge',
      13: 'sens', 15: 'vie J1', 16: '$32 J1', 17: '$32 J2'}


def lit(p):
    F = collections.defaultdict(dict)
    O = collections.defaultdict(lambda: collections.defaultdict(list))
    X, R, info = {}, {}, {}
    for l in open(p, errors='replace'):
        t = l.split()
        if not t:
            continue
        if t[0] == 'F':
            F[t[1]][int(t[2])] = t
        elif t[0] == 'O':
            O[t[1]][int(t[2])].append(tuple(t[3:7]))
        elif t[0] == 'X':
            X[t[1]] = (int(t[2]), t[3])
        elif t[0] == 'R':
            R[t[1]] = l.strip()
        elif t[0] == 'SAVE':
            info['save'] = l.strip()
    return F, O, X, R, info


def par_tour(F, O):
    """{tour relatif: champs de l'image qui l'a fini}, objets idem, nombre d'images sans tour"""
    T, OT, lag, prec = {}, {}, 0, None
    for r in sorted(F):
        t = int(F[r][14]) if len(F[r]) > 14 else r
        if prec is not None and t == prec:
            lag += 1
            continue
        k = len(T)
        T[k] = F[r]; OT[k] = O.get(r, [])
        prec = t
    return T, OT, lag


def compare(fa, fb, oa, ob):
    for r in sorted(set(fa) | set(fb)):
        a, b = fa.get(r), fb.get(r)
        if a is None or b is None:
            return 'longueur différente à l\'image %d (réf %s, cand %s)' % (r, 'fin' if a is None else 'suite', 'fin' if b is None else 'suite')
        for i, nom in CH.items():
            va = a[i] if i < len(a) else ''
            vb = b[i] if i < len(b) else ''
            if va != vb:
                return 'image %d : %s réf %s, cand %s' % (r, nom, va, vb)
        if sorted(oa.get(r, [])) != sorted(ob.get(r, [])):
            return 'image %d : objets réf %s, cand %s' % (r, ' '.join('/'.join(x) for x in oa.get(r, [])) or '-',
                                                        ' '.join('/'.join(x) for x in ob.get(r, [])) or '-')
    return None


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', required=True)
    ap.add_argument('--ref', required=True)
    ap.add_argument('--cand', required=True)
    ap.add_argument('--sortie', required=True)
    ap.add_argument('--etiquette', default='')
    a = ap.parse_args()
    FR, OR, XR, RR, IR = lit(a.ref)
    FC, OC, XC, RC, IC = lit(a.cand)
    n = collections.Counter()
    with open(a.sortie, 'w') as f:
        f.write('etiquette\tid\tligne\tperso\tism\ttype\tcoup\tvariante\tverdict\tdetail\n')
        for r in csv.DictReader(open(a.index), delimiter='\t'):
            base = [a.etiquette, r['id'], r['ligne'], r['perso'], r['ism'], r['type'], r['coup'], r['variante']]
            tid = r['id']
            if r['statut'] == 'NT':
                continue
            if tid in XC and tid not in XR:
                v, d = 'KO', 'exception au candidat image %d pc=%s' % XC[tid]
            elif tid not in FC:
                v, d = 'KO', 'essai non joué au candidat'
            elif tid not in FR:
                v, d = 'KO', 'essai absent de la référence'
            else:
                d = compare(FR[tid], FC[tid], OR[tid], OC[tid])
                v = 'IDENTIQUE' if d is None else 'DIFFÉRENT'
                if d is not None:
                    # alignement par TOUR DE JEU : une image sans tour (ralentissement : le 68K n'a pas fini son tour)
                    # decale tout d'une image sans changer le jeu
                    ta, oa, la = par_tour(FR[tid], OR[tid])
                    tb, ob, lb = par_tour(FC[tid], OC[tid])
                    n_ = min(len(ta), len(tb)) - 2
                    d2 = compare({k: ta[k] for k in range(n_)}, {k: tb[k] for k in range(n_)},
                                 {k: oa[k] for k in range(n_)}, {k: ob[k] for k in range(n_)})
                    if d2 is None:
                        v, d = 'RALENTI', 'même jeu tour par tour ; images sans tour : réf %d, cand %d (%s)' % (la, lb, d)
                    else:
                        d = '%s ; par tour : %s' % (d, d2)
                d = d or ''
            n[v] += 1
            f.write('\t'.join(base + [v, d]) + '\n')
    print(a.etiquette, ' '.join('%s=%d' % kv for kv in sorted(n.items())), '| réf', IR.get('save', '?'), '| cand', IC.get('save', '?'))
