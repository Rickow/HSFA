#!/usr/bin/env python3
"""valide_contre_upper.py — contrôle des règles de convertit_max.py contre la traduction réelle d'Upper.

Principe : pour chaque instruction du code MAX qui existe À L'IDENTIQUE dans la ROM arcade SFA3 (même mnémonique,
mêmes opérandes : ex. « move.b #$ff, $33(a6) »), on cherche ses sites arcade appariés à l'image Upper
(agent_upper_ecarts/realign.pkl : 83 709 instructions alignées) et on compare la forme qu'Upper a réellement produite
avec la forme produite par convertit_max.py (1re instruction de la réécriture). Sortie : sortie/validation.tsv +
résumé à l'écran. Lecture seule.
"""
import os, re, sys, pickle, csv
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convertit_max as C

REALIGN = '<workspace>/work/agent_upper_ecarts/realign.pkl'
ARC = '<workspace>/work/agent_symboles/_cache/arc.pkl'
SORTIE = os.path.join(C.ICI, 'sortie')
ALIAS = {'addi': 'add', 'subi': 'sub', 'cmpi': 'cmp', 'andi': 'and', 'ori': 'or', 'eori': 'eor', 'movea': 'move',
         'adda': 'add', 'suba': 'sub', 'cmpa': 'cmp'}

def unidasm_vers_vasm(ops):
    # ($33,A6) -> $33(a6) ; ($1c,A6,D0.w) -> $1c(a6,d0.w) ; (A6) -> (a6)
    ops = re.sub(r'\((-?\$[0-9a-fA-F]+),\s*(A\d|PC)\s*(?:,\s*([AD]\d)\.([wl]))?\)',
                 lambda m: '%s(%s%s)' % (m.group(1), m.group(2), (',' + m.group(3) + '.' + m.group(4)) if m.group(3) else ''), ops)
    return ops

def canon(mn, ops):
    """forme canonique (mnémonique sans alias, opérandes normalisés)"""
    mn = mn.lower()
    base, _, sz = mn.partition('.')
    base = ALIAS.get(base, base)
    t = C.TAILLE.get(sz) if sz else None
    out = []
    for o in C.split_ops(ops):
        e = C.EA(o)
        if e.mode == 'imm':
            v = C.num(e.imm)
            if v is None: return None
            if t: v &= (1 << (8 * t)) - 1
            out.append(('#', v))
        elif e.mode in ('disp', 'ind'):
            out.append(('d', e.reg, e.disp or 0))
        elif e.mode == 'idx':
            out.append(('x', e.reg, e.disp or 0, e.idx))
        elif e.mode in ('dn', 'an', 'predec', 'postinc'):
            out.append((e.mode, e.reg))
        else:
            return None
    return (base + ('.' + sz if sz else ''), tuple(out))

def main(plage=None, fichiers=None, nom='validation.tsv'):
    """plage = (lo, hi) : ne garder que les sites arcade de cette plage ; fichiers : lignes MAX de ces fichiers seulement"""
    res, table, T, carte = pickle.load(open(REALIGN, 'rb'))
    timg = {x[0]: (x[2], x[3]) for x in T}
    arc = {x[0]: (x[2], x[3]) for x in pickle.load(open(ARC, 'rb'))}
    # arcade canonique -> Counter(image canonique)
    paires = defaultdict(Counter)
    for ia, (aa, kind) in res.items():
        a = arc.get(aa); i = timg.get(ia)
        if not a or not i: continue
        if plage and not (plage[0] <= aa < plage[1]): continue
        ka = canon(a[0], unidasm_vers_vasm(a[1]))
        if ka is None or not any(o[0] in ('d', 'x') for o in ka[1]): continue
        ki = canon(i[0], unidasm_vers_vasm(i[1]))
        if ki is None: continue
        paires[ka][ki] += 1
    # lignes MAX converties (journal)
    J = list(csv.DictReader(open(os.path.join(SORTIE, 'journal.tsv')), delimiter='\t'))
    acc = Counter(); lignes = []
    vus = set()
    for r in J:
        if r['statut'] not in ('réécrit', 'inchangé'): continue
        if fichiers and r['fichier'] not in fichiers: continue
        o = r['original'].split(';')[0].strip()
        m = re.match(r'^(?:[A-Za-z_.][\w.]*:?\s+)?([a-z]+(?:\.[bwl])?)\s+(.*)$', o)
        if not m: continue
        ko = canon(m.group(1), m.group(2))
        if ko is None or ko not in paires: continue
        if r['statut'] == 'inchangé':
            kc = ko
        else:
            prem = r['converti'].split(' ; ')[0].strip()
            m2 = re.match(r'^([a-z]+(?:\.[bwl])?)\s+(.*)$', prem)
            if not m2: continue
            kc = canon(m2.group(1), m2.group(2))
            multi = ' ; ' in r['converti']
        cible, n = paires[ko].most_common(1)[0]
        tot = sum(paires[ko].values())
        if r['statut'] == 'réécrit' and ' ; ' in r['converti']:
            verdict = 'séquence (1re instr. non comparable)'
            # séquence : comparer l'accès mémoire de la 1re lecture/écriture
            mems_c = [x for x in (kc[1] if kc else ()) if x[0] in ('d', 'x')]
            mems_i = [x for x in cible[1] if x[0] in ('d', 'x')]
            if kc and mems_c and mems_i and mems_c[0] == mems_i[0]: verdict = 'séquence : même déplacement'
            elif kc and mems_c and mems_i: verdict = 'séquence : DÉPLACEMENT DIFFÉRENT'
        else:
            verdict = 'identique' if kc == cible else 'DIFFÉRENT'
        acc[verdict] += 1
        cle = (o, verdict)
        if cle in vus: continue
        vus.add(cle)
        lignes.append((verdict, r['fichier'], r['ligne'], o, r['converti'] or '(inchangé)',
                       '%s %s' % cible, '%d/%d' % (n, tot)))
    with open(os.path.join(SORTIE, nom), 'w') as f:
        f.write('verdict\tfichier\tligne\tarcade (MAX)\tconverti\tforme Upper majoritaire\taccord sites\n')
        for l in sorted(lignes): f.write('\t'.join(str(x) for x in l) + '\n')
    print('instructions MAX comparables (présentes telles quelles dans l\'arcade et alignées) :', sum(acc.values()))
    for k, v in acc.most_common(): print('  %-40s %d' % (k, v))
    print('formes distinctes :', len(lignes))

if __name__ == '__main__':
    if '--acteurs' in sys.argv:
        # acteurs de fin MAX contre le code d'ACTEURS d'Upper uniquement (classes $48-$50 : arcade $A5000-$AD000)
        main((0xA5000, 0xAD000), {'acteurs_fins_max.s'}, 'validation_acteurs.tsv')
    else:
        main()
