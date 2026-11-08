#!/usr/bin/env python3
"""(banc_coups) ANALYSEUR DE LA NOTATION du tableau des coups (work/guide_coups/coups_sfa_anthology.csv) ->
sequences d'appuis image par image pour lua/banc_coups.lua.

Notation (perso tourne vers la droite) : fleches (→ = avant), « X (charge) Y » = charge puis Y, « ou » = alternatives,
360° / 720°, Punch / Kick = n'importe lequel (on teste les 3 forces), 2 Punch / 3 Kick = simultanes, Select / Start =
bouton Start. Les directions sont RELATIVES (F = avant, B = arriere) : le banc les resout a l'execution selon la
position reelle de J1 (miroir automatique cote J2 / face a gauche).

Sortie de variantes(ligne) : liste de Variante(nom, seq1, seq2, dist, jauge, drapeaux) ou NonTestable(raison).
Sequence = jetons « n:TOUCHES » (TOUCHES = U D F B, 1-6 = LP MP HP LK MK HK, S = Start, N = rien, reunis par +),
« G:n » = attendre la garde de J1 (au plus n images).
"""
import re
from dataclasses import dataclass, field

CHARGE = 120          # images de charge (2 s a 60 Hz)
PAS = 3               # images par direction d'une manipulation
FL = {'↑': 'U', '↓': 'D', '←': 'B', '→': 'F', '↖': 'UB', '↗': 'UF', '↙': 'DB', '↘': 'DF'}
BOUT = {'LP': '1', 'MP': '2', 'HP': '3', 'LK': '4', 'MK': '5', 'HK': '6'}
NOMS_B = {v: k for k, v in BOUT.items()}
NOMS_B['S'] = 'Start'
GARDE_J2 = '6:N 4:6'   # J2 : HK debout, que J1 garde (arriere tenu) avant l'Alpha Counter
ROT8 = ['F', 'DF', 'D', 'DB', 'B', 'UB', 'U', 'UF']


@dataclass
class Variante:
    nom: str
    seq1: str
    seq2: str = ''
    dist: int = 0x60
    jauge: int = 0x90
    drap: list = field(default_factory=list)   # 'air', 'pres', 'garde', 'suite', 'mash', 'charge'...


@dataclass
class NonTestable:
    raison: str


def dirs(s):
    """suite de directions d'une chaine de fleches (ignore les espaces / virgules)"""
    out = []
    for c in s:
        if c in FL:
            out.append(FL[c])
    return out


def combos_boutons(b):
    """'Punch' -> [['1'], ['2'], ['3']] ; '2 Punch' -> [['1','2']] ; 'LP + LK / MP + MK ou HP + HK' -> 3 variantes.
    Renvoie (liste de variantes, suites) ; suites = boutons supplementaires a rappuyer ensuite (rekka)"""
    b = b.strip()
    b = re.sub(r'\(imprimé.*?\)', '', b).strip()
    mash = bool(re.search(r'répété|marteler|rapidement', b))
    b = re.sub(r'\((répété|répété rapidement|marteler|ou rien|maintenu)\)', '', b).strip()
    tenir = 'maintenir puis relâcher' in b
    b = re.sub(r'\(maintenir puis relâcher\)', '', b).strip()
    # suites : « X, puis Y », « X puis Y », « X, X », « X x 3 »
    parts = [p.strip() for p in re.split(r',\s*puis|\s+puis\s+|,', b) if p.strip()]
    nfois = 1
    m = re.match(r'^(.*?)\s*x\s*(\d)$', parts[0]) if parts else None
    if m:
        parts[0], nfois = m.group(1).strip(), int(m.group(2))

    def un(p):
        p = p.strip()
        if p in ('', 'aucun'):
            return [[]]
        if p in ('Select', 'Start'):
            return [['S']]
        alts = [a.strip() for a in re.split(r'\s+ou\s+|\s*/\s*', p) if a.strip()]
        res = []
        for a in alts:
            if a in BOUT:
                res.append([BOUT[a]])
            elif re.fullmatch(r'(LP|MP|HP|LK|MK|HK)(\s*\+\s*(LP|MP|HP|LK|MK|HK))+', a):
                res.append([BOUT[x.strip()] for x in a.split('+')])
            elif a in ('Punch', 'bouton d\'attaque'):
                res += [['1'], ['2'], ['3']]
            elif a == 'Kick':
                res += [['4'], ['5'], ['6']]
            elif a == '2 Punch':
                res.append(['1', '2'])
            elif a == '2 Kick':
                res.append(['4', '5'])
            elif a == '3 Punch':
                res.append(['1', '2', '3'])
            elif a == '3 Kick':
                res.append(['4', '5', '6'])
            elif a.startswith('Punch ou Kick') or a == 'Punch ou Kick (selon le personnage)':
                res += [['1'], ['2'], ['3'], ['4'], ['5'], ['6']]
            else:
                return None
        return res
    prem = un(parts[0]) if parts else [[]]
    if prem is None:
        return None, None, mash, tenir, nfois
    suites = []
    for p in parts[1:]:
        u = un(p)
        if u is None:
            return None, None, mash, tenir, nfois
        suites.append(u[0])
    return prem, suites, mash, tenir, nfois


def jt(n, touches):
    return '%d:%s' % (n, '+'.join(touches) if touches else 'N')


def motion(m, charge=CHARGE):
    """manipulation (sans alternatives) -> liste de (n, [directions]) ; None si inconnue"""
    m = m.strip()
    m = re.sub(r'\((facultatif)\)', '', m).strip()
    if m == '':
        return []
    if m in ('360°',):      # mesure a l'arcade : 4 directions cardinales, 3 tours chacune, bouton sur Haut
        return [(3, ['F']), (3, ['D']), (3, ['B']), (3, ['U'])]
    if m in ('720°',):      # 720 : commence pendant un LP (sinon le 1er Haut fait sauter), 8 directions x 2
        return [(3, ['1'])] + [(2, [d]) for d in ROT8 + ROT8[:-1]] + [(3, ['U'])]
    if '(charge)' in m:
        a, b = m.split('(charge)', 1)
        da, db = dirs(a), dirs(b)
        if len(da) != 1 or not db:
            return None
        return [(charge, [da[0]])] + [(PAS, [d]) for d in db]
    if re.search(r'[A-Za-z]', m):
        return None
    d = dirs(m)
    if not d:
        return None
    return [(PAS, [x]) for x in d]


def touches_dir(d):
    return [c for c in d]   # 'DF' -> ['D', 'F']


def seq_motion_bouton(mot, boutons, tenir_dir=False):
    """manip + appui : chaque direction PAS images, bouton sur la derniere direction (3 images)"""
    t = []
    for i, (n, d) in enumerate(mot):
        td = touches_dir(d[0])
        if i == len(mot) - 1 and boutons:
            if n > 1:
                t.append(jt(1, td))
            t.append(jt(3, td + boutons))
        else:
            t.append(jt(n, td))
    if not mot and boutons:
        t.append(jt(3, boutons))
    return t


SAUT = {'avant': '3:U+F 10:N', 'vertical': '3:U 10:N', 'arriere': '3:U+B 10:N', 'sommet': '3:U+F 16:N',
        'decollage': '3:U+F 4:N'}


def variantes(row, ism=None):
    """row = dict du CSV ; renvoie une liste de Variante ou un NonTestable"""
    typ, man, bou, cond = row['type'], row['manipulation'].strip(), row['boutons'].strip(), row['conditions']
    nom = row['nom_du_coup']
    if typ in ('autre', 'secret', 'custom combo') and not nom.startswith('Variable Combo VC') and 'activation' not in nom.lower():
        return NonTestable('combo / enchaînement / secret de menu : hors banc')
    if typ == 'systeme' and not (nom.startswith('Variable Combo VC') or nom.startswith('Throw')):
        return NonTestable('mécanique système (garde, chute, parade, menu) : non scriptée')
    if man.startswith('Any Attack') or re.search(r'LP, LP', man):
        if man.startswith('LP, LP'):   # Shun Goku Satsu : LP, LP, →, LK, HP
            return [Variante('LP LP → LK HP', ' '.join(['3:1', '2:N', '3:1', '2:N', '3:F', '2:N', '3:4', '2:N', '3:6']))]
        return NonTestable('manipulation libre (n\'importe quels boutons) : non scriptée')
    c = cond.lower()
    for motcle, raison in (('pendant ', 'suite d\'un autre coup (pendant …) : non scriptée'),
                           ('après ', 'suite d\'un autre coup (après …) : non scriptée'),
                           ('reversal', 'reversal : demande un relevé / une sortie de garde'),
                           ('contre un mur', 'saut contre un mur : demande un coin'),
                           ('stage de vega', 'uniquement sur le décor de Vega'),
                           ('chute', 'au sol après une chute'),
                           ('une attaque', 'contre-attaque : demande une attaque adverse précise'),
                           ('bord de l\'écran', 'demande un bord de l\'écran'),
                           ('placer le', 'condition de jeu non scriptable')):
        if motcle in c and not ('en garde' in c and motcle == 'pendant '):
            if motcle == 'pendant ' and ('pendant un saut' in c or 'pendant le blockstun' in c):
                continue
            return NonTestable(raison)
    if man == '' and bou == '':
        return NonTestable('manipulation non indiquée dans le guide')
    if 'commande non' in c and man == '':
        if typ != 'alpha counter':
            return NonTestable('commande non indiquée dans le guide')
    # alternatives de manipulation
    man = re.sub(r'^direction \((.*)\)$', r'\1', man)
    alts = [a.strip() for a in re.split(r'\s+ou\s+', man)] if man else ['']
    alts2 = []
    for a in alts:
        a = re.sub(r'\s*puis\s+.*$', '', a)          # « ↓↘→↗ puis ← ou → » : on ne garde que la 1re partie
        a = re.sub(r'\((maintenu|maintenir)\)', '', a).strip()
        a = a.replace('direction (', '').replace(')', '') if a.startswith('direction') else a
        if a and a not in alts2:
            alts2.append(a)
    if not alts2:
        alts2 = ['']
    # « ← ou → » : une direction chacune (lancers avant / arriere)
    prem, suites, mash, tenir, nfois = combos_boutons(bou)
    if prem is None:
        return NonTestable('boutons non reconnus : %s' % bou)
    air = None
    if re.search(r'en l\'air|pendant un saut|en saut|au sommet|dès le décollage|saut vertical', c):
        if re.search(r'au sol ou en l|aussi en l|faisable en l', c):
            air = 'les2'
        elif 'sommet' in c:
            air = 'sommet'
        elif 'décollage' in c:
            air = 'decollage'
        elif 'vertical' in c:
            air = 'vertical'
        else:
            air = 'avant'
    pres = 'près de' in c or typ == 'lancer' or 'très près' in c or 'portée de lancer' in c or nom.startswith('Throw')
    if '360' in man or '720' in man:    # rotations = saisies : au contact
        pres = True
    if 'loin de' in c:
        pres = False
    garde = 'en garde' in c or typ == 'alpha counter'
    res = []
    if air == 'les2':
        r2 = dict(row); r2['conditions'] = re.sub(r"(au sol ou |(possible |faisable |réalisable )?aussi |faisable )en l'air", '', cond)
        if r2['conditions'] == cond:
            r2['conditions'] = ''
        sol = variantes(r2, ism)
        r2['conditions'] = 'en l\'air'
        enl = variantes(r2, ism)
        if isinstance(sol, NonTestable):
            return sol
        return sol + (enl if isinstance(enl, list) else [])
    for a in alts2:
        mot = motion(a)
        if mot is None:
            return NonTestable('manipulation non reconnue : %s' % a)
        for b in prem:
            if garde:
                # J2 attaque (MK debout), J1 tient arriere, attend sa garde puis fait la manip
                pre = ['G:60']
                s1 = pre + seq_motion_bouton(mot, b) + ['2:N']
                s2 = GARDE_J2
                v = Variante('%s + %s' % (a or '-', '+'.join(NOMS_B[x] for x in b) or '-'), ' '.join(s1), s2, dist=0x38, drap=['garde'])
                res.append(v)
                continue
            s1 = []
            if air:
                s1.append(SAUT[air])
            if 'accroupi' in c:
                s1.append('6:D')
            if mash:
                corps = seq_motion_bouton(mot, b)
                for _ in range(8):
                    corps += ['2:N', jt(2, b)]
                s1 += corps
            elif tenir:
                s1 += ['60:' + '+'.join(b), '2:N'] + seq_motion_bouton(mot, [])
            else:
                s1 += seq_motion_bouton(mot, b)
                for _ in range(nfois - 1):
                    s1 += ['3:N', jt(3, b)]
                for sb in suites:
                    s1 += ['14:N', jt(3, sb)]
            s1.append('2:N')
            dr = []
            if air:
                dr.append('air')
            if pres:
                dr.append('pres')
            if suites:
                dr.append('suite')
            if mash:
                dr.append('mash')
            if 'charge' in a:
                dr.append('charge')
            s2 = ''
            if air and pres:          # lancer aerien : J2 saute aussi (vertical, au meme moment)
                s2 = '3:U'
                s1 = ['3:U 8:N'] + seq_motion_bouton(mot, b) + ['2:N']
            v = Variante('%s%s + %s' % ('(air) ' if air else '', a or '-', '+'.join(NOMS_B[x] for x in b) or '-'),
                         ' '.join(s1), s2, dist=0x20 if pres else 0x60, drap=dr)
            res.append(v)
    return res


if __name__ == '__main__':
    import csv, sys
    p = '<workspace>/work/guide_coups/coups_sfa_anthology.csv'
    rows = list(csv.DictReader(open(p, encoding='utf-8'), delimiter=';'))
    filtre = sys.argv[1] if len(sys.argv) > 1 else 'Ryu'
    for i, r in enumerate(rows, 2):
        if r['personnage'] == filtre and r['jeu'].startswith('Street Fighter Alpha'):
            v = variantes(r)
            print(i, r['jeu'][21:], r['nom_du_coup'], '|', r['manipulation'], '|', r['boutons'], '|', r['conditions'][:40])
            if isinstance(v, NonTestable):
                print('    NON TESTABLE :', v.raison)
            else:
                for x in v:
                    print('    %-28s %s  || %s  d=%02x %s' % (x.nom, x.seq1, x.seq2, x.dist, x.drap))
