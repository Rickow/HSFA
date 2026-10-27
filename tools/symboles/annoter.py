#!/usr/bin/env python3
"""Carte annotée de ro3 (SFA3) : symboles_ro3.csv + carte_image.txt -> carte_annotee_ro3.txt

Pour chaque ligne de carte_image.txt (« adresse68K_traduite va_mips mnémonique ») :
  - en-tête de fonction (nom, rôle, adresses arcade / mips / traduit) quand l'adresse traduite ou le va
    MIPS est le début d'un symbole « fonction » ou « étiquette » ;
  - commentaire en fin de ligne : noms des variables A5, des champs de structure (+$xx(A6), et des
    autres An avec « ? »), des cibles d'appel/saut, des tables et des registres matériels reconnus.

Les déplacements sont comparés dans la numérotation de l'IMAGE TRADUITE (colonne « trad » du CSV) :
c'est celle de carte_image.txt (octets XOR 1 et moitiés de longs échangées par rapport à l'arcade).

Usage : python3 annoter.py [--csv symboles_ro3.csv] [--carte .../carte_image.txt] [--sortie carte_annotee_ro3.txt]
"""
import argparse, csv, os, re, collections

ICI = os.path.dirname(os.path.abspath(__file__))
R_OP = re.compile(r'(-?)\$([0-9a-fA-F]+)\((A[0-7])(?:,[^)]*)?\)|(?<![$\w])\((A5)\)')
R_ABS = re.compile(r'\$([0-9a-fA-F]{4,8})(\.L|\.W)?')
R_MIPS = re.compile(r'\[mips ([0-9a-fA-F]+)')
OCTET = ('BTST', 'BSET', 'BCLR', 'BCHG', 'TAS', 'NBCD', 'ST', 'SF', 'SEQ', 'SNE', 'SCC', 'SCS', 'SMI', 'SPL')

def num(s):
    s = (s or '').strip()
    if not s: return None
    s = s.replace('moteur ', '')
    try:
        if s.startswith('+$'): return int(s[2:], 16)
        if s.startswith('$'): return int(s[1:], 16)
        if s.lower().startswith('0x'): return int(s, 16)
    except ValueError: return None
    return None

def taille_de(mn):
    m = mn.split()[0].upper() if mn.strip() else ''
    if m.endswith('.B') or m in OCTET: return 'B'
    if m.endswith('.W'): return 'W'
    if m.endswith('.L'): return 'L'
    return ''

def charge_csv(path):
    S = list(csv.DictReader(open(path, encoding='utf-8'), delimiter=';'))
    code_t = {}; code_m = {}; a5 = collections.defaultdict(list); champs = collections.defaultdict(list)
    absolu = {}
    for r in S:
        ty = r['type']; t = num(r['trad']); m = num(r['mips'])
        if ty in ('fonction', 'étiquette'):
            if r['mips'].startswith('moteur'): continue
            if t is not None and t < 0x400000:
                if t not in code_t or (code_t[t]['type'] == 'étiquette' and ty == 'fonction') or \
                        (code_t[t]['nom'].startswith(('fonc_', 'port_')) and not r['nom'].startswith(('fonc_', 'port_'))):
                    code_t[t] = r
            elif m is not None:
                code_m.setdefault(m, r)
        elif ty == 'variable A5' and t is not None and 0xFF0000 <= t <= 0xFFFFFF:
            d = (t - 0xFF8000) & 0xffff
            a5[d].append(r)
        elif ty in ('champ joueur', 'champ objet') and t is not None:
            champs[t].append(r)
        elif ty == 'table' and t is not None:
            absolu.setdefault(t, r)
        elif ty == 'registre matériel':
            a = num(r['arcade'])
            if a is not None: absolu.setdefault(a, r)
        elif ty == 'variable portage':
            for col in ('trad', 'arcade'):
                a = num(r[col])
                if a is not None and a >= 0x400: absolu.setdefault(a, r)
    return S, code_t, code_m, a5, champs, absolu

def choisit(lst, tl):
    """symbole de même taille d'accès de préférence ; une taille vide accepte tout"""
    if not lst: return None, ''
    exact = [r for r in lst if (r['taille'] or '')[:1] == tl]
    if exact: return exact[0], ''
    libres = [r for r in lst if not (r['taille'] or '')[:1] in ('B', 'W', 'L')]
    if libres: return libres[0], ''
    if tl == 'W' and any((r['taille'] or '')[:1] == 'L' for r in lst):
        return [r for r in lst if (r['taille'] or '')[:1] == 'L'][0], ' (moitié)'
    if tl in ('', 'L'): return lst[0], ''
    return None, ''

def entete(r):
    a = r['arcade'] or '—'; m = r['mips'] or '—'; t = r['trad'] or '—'
    mex = ''
    mm = num(r['mips'])
    if mm is not None and not r['mips'].startswith('moteur'): mex = ' (exéc 0x%X)' % (mm + 0x1F0000)
    l = ['', '; ' + '=' * 98,
         '; %s %s   [%s, confiance : %s]' % ('FONCTION' if r['type'] == 'fonction' else 'ÉTIQUETTE', r['nom'], r['type'], r['confiance'] or '—'),
         ';   arcade %s | mips %s%s | traduit %s | taille %s' % (a, m, mex, t, r['taille'] or '—')]
    role = r['rôle']
    while role:
        l.append(';   ' + role[:110]); role = role[110:]
    l.append(';   source : ' + (r['source'] or '—'))
    l.append('; ' + '=' * 98)
    return l

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default=os.path.join(ICI, 'symboles_ro3.csv'))
    ap.add_argument('--carte', default='<workspace>/work/mame/carte_image.txt')
    ap.add_argument('--sortie', default=os.path.join(ICI, 'carte_annotee_ro3.txt'))
    a = ap.parse_args()
    S, code_t, code_m, a5, champs, absolu = charge_csv(a.csv)
    stats = collections.Counter()
    # La carte peut venir d'une autre génération de l'image que celle qui a servi au CSV : les adresses
    # traduites bougent alors, pas les va MIPS. On vérifie la cohérence trad <-> va sur la carte lue ;
    # si elle est mauvaise, on ne se fie qu'aux va MIPS.
    lignes = []
    for l in open(a.carte, encoding='utf-8', errors='replace'):
        p = l.rstrip('\n').split(' ', 2)
        try: lignes.append((int(p[0], 16), int(p[1], 16), p[2] if len(p) > 2 else '', l.rstrip('\n')))
        except (ValueError, IndexError): lignes.append((None, None, '', l.rstrip('\n')))
    va_de = {}
    for t, va, _, _ in lignes:
        if t is not None: va_de.setdefault(t, va)
    ok = tot = 0
    for t, r in code_t.items():
        m = num(r['mips'])
        if m is None or r['mips'].startswith('moteur'): continue
        tot += 1
        if t in va_de and 0 <= va_de[t] - m <= 0x80: ok += 1
    fiable = tot and ok >= 0.9 * tot
    print('cohérence adresses traduites du CSV / carte lue : %d/%d -> %s' % (ok, tot, 'adresses traduites utilisées' if fiable else 'va MIPS seulement'))
    vas = sorted({va for t, va, _, _ in lignes if va is not None})
    import bisect
    code_v = {}
    for r in S:
        if r['type'] not in ('fonction', 'étiquette') or r['mips'].startswith('moteur'): continue
        m = num(r['mips'])
        if m is None: continue
        i = bisect.bisect_left(vas, m)
        if i < len(vas) and vas[i] - m <= 0x80:
            v = vas[i]
            if v not in code_v or (code_v[v]['nom'].startswith(('fonc_', 'port_')) and not r['nom'].startswith(('fonc_', 'port_'))) \
                    or (code_v[v]['type'] == 'étiquette' and r['type'] == 'fonction'):
                code_v[v] = r
    if not fiable:
        code_t = {}
    cible_m = {}                                        # va exéc des cibles d'appel -> symbole
    for r in S:
        if r['type'] in ('fonction', 'étiquette') and not r['mips'].startswith('moteur'):
            m = num(r['mips'])
            if m is not None: cible_m.setdefault(m, r)
    vus_m = set()
    out = open(a.sortie, 'w', encoding='utf-8')
    out.write('; Carte annotée du module ro3 (SFA3) — généré par annoter.py\n')
    out.write('; colonnes : adresse 68K traduite, va MIPS (fichier), instruction traduite ; commentaires = symboles\n')
    out.write('; source des symboles : %s (%d symboles) ; carte : %s\n' % (os.path.basename(a.csv), len(S), a.carte))
    out.write('; « ? » = champ de structure supposé sur un An autre que A6 (base non vérifiée)\n')
    for t, va, mn, l in lignes:
        if t is None: out.write(l + '\n'); continue
        r = code_t.get(t)
        if r is None and va not in vus_m: r = code_v.get(va)
        if r is not None and not (r.get('_fait')):
            r['_fait'] = True
            for x in entete(r): out.write(x + '\n')
            stats['entetes'] += 1
        vus_m.add(va)
        notes = []
        tl = taille_de(mn)
        corps = mn.split('  [')[0]
        for mo in R_OP.finditer(corps):
            if mo.group(4):
                reg = 'A5'; d = 0
            else:
                reg = mo.group(3); d = int(mo.group(2), 16) * (-1 if mo.group(1) else 1)
            if reg == 'A5':
                s, suf = choisit(a5.get(d & 0xffff, []), tl)
                if s: notes.append(s['nom'] + suf); stats['A5'] += 1
                else:
                    # dans une structure joueur ($400..$13FF) : champ joueur
                    if 0x400 <= d < 0x1400:
                        f, suf = choisit(champs.get(d & 0x3ff, []), tl)
                        if f: notes.append('J%d.%s%s' % (d // 0x400, f['nom'], suf)); stats['A5j'] += 1
            elif reg in ('A6', 'A0', 'A1', 'A2', 'A3', 'A4'):
                f, suf = choisit(champs.get(d, []), tl)
                if f:
                    notes.append(f['nom'] + suf + ('' if reg == 'A6' else '?')); stats['champ'] += 1
        for mo in R_ABS.finditer(corps):
            v = int(mo.group(1), 16)
            if mo.group(2) == '.W' and v >= 0x8000: v |= 0xFF0000
            v &= 0xFFFFFF
            s = absolu.get(v)
            if s is None and v in code_t and corps.split()[0].upper() in ('JSR', 'JMP', 'BSR', 'BRA', 'LEA', 'PEA'):
                s = code_t[v]
            if s is not None: notes.append(('→ ' if s['type'] in ('fonction', 'étiquette') else '') + s['nom']); stats['absolu'] += 1
        mm = R_MIPS.search(mn)
        if mm and not any(n.startswith('→') for n in notes):
            v = int(mm.group(1), 16) - 0x1F0000
            s = cible_m.get(v)
            if s is not None: notes.append('→ ' + s['nom']); stats['appel_mips'] += 1
        if notes:
            l = '%-60s ; %s' % (l, ', '.join(dict.fromkeys(notes)))
            stats['lignes_annotees'] += 1
        stats['lignes'] += 1
        out.write(l + '\n')
    out.close()
    print('%(lignes)d lignes, %(lignes_annotees)d annotées, %(entetes)d en-têtes de fonction' % stats)
    print('références : A5 %d, champs joueur via A5 %d, champs (An) %d, absolues %d, appels via mips %d'
          % (stats['A5'], stats['A5j'], stats['champ'], stats['absolu'], stats['appel_mips']))

if __name__ == '__main__':
    main()
