#!/usr/bin/env python3
"""quoi.py — que sait-on de cette adresse, de ce nom, de ce mot ?

Cherche dans tous les TSV de re/connaissances/ (et dans re/allocations.tsv) :
  - par adresse, dans n'importe quel espace : adresse principale (plages et tailles comprises),
    homologues (`adresse_autres`), champs de structure (A5, joueur $FF8400 + $400·k) ;
  - par nom (sous-chaîne, sans casse ni accents) ;
  - par mot-clé (rôle, mises en garde, type, source).

Exemples :
  quoi.py 0x6139A4          quoi.py T_749838          quoi.py "Juli"
  quoi.py ro5:0x749838      quoi.py '$FF8503'         quoi.py +$102 -s joueur
  quoi.py 0x20E500 --va     (va = décalage fichier du module : + 0x1F0000)

Sortie : une ligne par entrée, mises en garde en tête (« !! … »).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import connaissances as K  # noqa: E402

BASE_MODULE = 0x1F0000


def analyse_adresse(q):
    """'ro5:0x749838' -> ('ro5', 0x749838, '0x') ; 'T_749838' -> (None, 0x749838, 'T_') ; sinon None."""
    esp = None
    m = re.fullmatch(r'([a-z_0-9]+):(.+)', q.strip())
    if m and (m.group(1) in K.ESPACES or m.group(1) in K.ESPACE_DU_FICHIER or m.group(1) in K.ALIAS):
        esp = K.ALIAS.get(m.group(1), K.ESPACE_DU_FICHIER.get(m.group(1), m.group(1)))
        q = m.group(2)
    q = q.strip()
    m = re.fullmatch(r'\+?(\$|0x|0X|T_|t_)?([0-9A-Fa-f]+)', q)
    if not m:
        return None
    pre = (m.group(1) or '').lower()
    if not pre and not re.search(r'\d', m.group(2)):
        return None          # « Bad », « ace »… : un mot, pas une adresse
    if not pre and len(m.group(2)) < 3:
        return None
    return esp, int(m.group(2), 16), pre or 'nu', q.startswith('+')


def variantes(v, pre, va):
    """Valeurs à essayer, avec leur étiquette."""
    res = [(v, '')]
    if pre in ('0x', 'nu', 't_') and (va or v < BASE_MODULE) and v + BASE_MODULE < 0x2000000:
        res.append((v + BASE_MODULE, 'va fichier + 0x1F0000'))
    if 0xFF0000 <= v <= 0xFFFFFF:
        res.append((v ^ 1, 'octet XOR 1 (image traduite <-> arcade)'))
    if pre in ('0x', 'nu') and (0x900000 <= v <= 0x90FFFF or 0xA00000 <= v <= 0xA0FFFF):
        res.append((0xFF0000 | (v & 0xFFFF), 'RAM PS2 du jeu -> $FFxxxx (0x90xxxx ro3, 0xA0xxxx Upper)'))
    vus, out = set(), []
    for x, e in res:
        if x not in vus:
            vus.add(x)
            out.append((x, e))
    return out


def dans(p, v):
    return p is not None and p[0] <= v <= p[1]


def cherche_adresse(base, esp, v, pre, va, champ_seul):
    trouves = []   # (priorité, texte d'origine de la correspondance, ligne, genre)
    for x, etiq in variantes(v, pre, va):
        va_fichier = etiq.startswith('va fichier')
        if not champ_seul:
            for d in base['adresses']:
                esp_d = K.ESPACE_DU_FICHIER.get(d['_fichier'], d['_fichier'])
                if va_fichier and esp_d not in ('ro3', 'ro5', 'ro9', 'ro9a'):
                    continue       # +0x1F0000 ne vaut que pour les modules PS2 (pas la va PSP, ni l'arcade)
                if esp in (None, esp_d):
                    e = K.etendue_ligne(d)
                    if e and dans(e, x):
                        exact = e[0] == x
                        petit = x < 0x1000 and pre == '$'
                        trouves.append(((3 if petit else 0) if exact else 2, etiq or ('' if exact else 'dans la plage'), d, 'adr'))
                        continue
                for e2, a2 in K.autres(d.get('adresse_autres', '')):
                    if esp not in (None, e2) or (va_fichier and e2 not in ('ro3', 'ro5', 'ro9', 'ro9a')):
                        continue
                    p = K.plage(a2)
                    if dans(p, x):
                        trouves.append((1, ('homologue %s' % e2) + (' ; ' + etiq if etiq else ''), d, 'adr'))
                        break
            for z in base['allocations']:
                a, b = K.hexv(z.get('debut')), K.hexv(z.get('fin'))
                if a is not None and b is not None and a <= x <= b:
                    trouves.append((3, 'zone ' + z.get('cible', '') + (' ; ' + etiq if etiq else ''), z, 'zone'))
        # champs : déplacement direct (+$xx ou petite valeur), A5, joueur $FF8400 + $400·k
        cand = []                      # (déplacement, structure imposée, étiquette, priorité)
        if champ_seul:
            cand.append((x, None, 'déplacement', 0))
        elif x < 0x10000 and pre != 'nu':
            cand.append((x, None, 'déplacement', 1 if (x < 0x1000 and pre == '$') else 4))
        if 0xFF0000 <= x <= 0xFFFFFF:
            cand.append(((x + 0x8000) & 0xFFFF, 'A5', 'A5 = $FF8000', 1))
            if 0xFF8400 <= x <= 0xFF93FF:
                k, off = divmod(x - 0xFF8400, 0x400)
                cand.append((off, 'joueur', 'joueur %d +$%X' % (k + 1, off), 1))
        for d in base['champs']:
            for e2, a2 in K.autres(d.get('decalage_autres', '')):
                if e2 == 'cps2' and K.hexv(a2) == x:
                    trouves.append((1, 'cps2' + ((' ; ' + etiq) if etiq else ''), d, 'champ'))
            for off, struct, etq, pr in cand:
                if struct and d.get('structure') != struct:
                    continue
                cols = [c for c in ('decalage_ps2', 'decalage_arcade') if K.hexv(d.get(c)) == off]
                if not cols and not struct:
                    cols = [e2 for e2, a2 in K.autres(d.get('decalage_autres', ''))
                            if e2 != 'cps2' and K.hexv(a2) == off]
                if cols:
                    trouves.append((pr, '%s, %s%s' % (etq, '/'.join(cols), (' ; ' + etiq) if etiq else ''),
                                    d, 'champ'))
    return trouves


def cherche_texte(base, q):
    nq = K.sans_accents(q)
    res = []
    for genre, lignes in (('adr', base['adresses']), ('champ', base['champs']), ('zone', base['allocations'])):
        for d in lignes:
            nom = K.sans_accents(d.get('nom', '') or d.get('occupant', ''))
            if nq == nom:
                res.append((0, 'nom exact', d, genre))
            elif nq in nom:
                res.append((1, 'nom', d, genre))
            else:
                texte = ' '.join(d.get(c, '') for c in ('role', 'mises_en_garde', 'taille_type', 'remarque',
                                                         'adresse_autres', 'structure', 'cible'))
                if nq in K.sans_accents(texte):
                    res.append((5, 'mot-clé', d, genre))
    return res


def ligne_sortie(d, genre, pourquoi, long):
    def c(s, n=160):
        s = (s or '').strip()
        return s if long or len(s) <= n else s[:n - 1] + '…'
    garde = ('!! ' + c(d.get('mises_en_garde'), 220) + ' !! ') if d.get('mises_en_garde') else ''
    if genre == 'adr':
        tete = '%s:%s %s [%s]' % (d['_fichier'], d.get('adresse', ''), d.get('nom', ''), d.get('genre', ''))
        corps = c(d.get('role'))
        if d.get('taille_type'):
            corps += ' (%s)' % c(d['taille_type'], 60)
        if d.get('adresse_autres'):
            corps += ' | autres : ' + c(d['adresse_autres'], 120)
    elif genre == 'champ':
        dec = d.get('decalage_ps2') or '-'
        if d.get('decalage_arcade') and d.get('decalage_arcade') != d.get('decalage_ps2'):
            dec += ' (arcade %s)' % d['decalage_arcade']
        tete = 'champ %s%s %s [%s]' % (d.get('structure', ''), dec, d.get('nom', ''), d.get('espaces', ''))
        corps = c(d.get('role'))
        if d.get('taille_type'):
            corps += ' (%s)' % c(d['taille_type'], 60)
        if d.get('decalage_autres'):
            corps += ' | autres : ' + c(d['decalage_autres'], 120)
    else:
        tete = 'zone %s %s-%s %s [%s]' % (d.get('cible', ''), d.get('debut', ''), d.get('fin', ''),
                                          d.get('occupant', ''), d.get('etat', ''))
        corps = c(d.get('remarque'))
        garde = ''
    pied = ' | %s | %s' % (d.get('confiance', '') or '-', c(d.get('source'), 100))
    if d.get('score'):
        pied += ' | score ' + c(d['score'], 40)
    if d.get('outil'):
        pied += ' | outil ' + c(d['outil'], 60)
    why = (' «%s»' % pourquoi) if pourquoi else ''
    return garde + tete + why + ' — ' + corps + pied


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('requete', nargs='+', help='adresse ($…, 0x…, espace:adr, +$déplacement), nom ou mot-clé')
    ap.add_argument('-e', '--espace', help='restreindre à un espace (arcade, ro3, ro5, ro9, ro9a, psp, img_ro5, cps2…)')
    ap.add_argument('-s', '--structure', help='restreindre les champs à une structure (joueur, objet, A5…)')
    ap.add_argument('-n', '--max', type=int, default=60, help='nombre maximal de lignes (défaut 60, 0 = tout)')
    ap.add_argument('--va', action='store_true', help="essayer aussi l'adresse + 0x1F0000 (va fichier)")
    ap.add_argument('--long', action='store_true', help='ne pas tronquer les textes')
    ap.add_argument('--texte', action='store_true', help="ne chercher qu'en texte (pas d'interprétation d'adresse)")
    a = ap.parse_args()
    q = ' '.join(a.requete)
    base = K.charger_tout()
    res = []
    adr = None if a.texte else analyse_adresse(q)
    if adr:
        esp, v, pre, est_dep = adr
        res += cherche_adresse(base, a.espace or esp, v, pre, a.va, est_dep)
    res += cherche_texte(base, q)
    if a.structure:
        res = [r for r in res if r[3] != 'champ' or r[2].get('structure') == a.structure]
    if a.espace:
        esp = K.ESPACE_DU_FICHIER.get(a.espace, a.espace)
        res = [r for r in res if r[3] != 'adr' or K.ESPACE_DU_FICHIER.get(r[2]['_fichier']) == esp
               or esp in r[2].get('adresse_autres', '')]
    vus, sortie = set(), []
    for pr, why, d, g in sorted(res, key=lambda r: (r[0], 0 if r[2].get('mises_en_garde') else 1)):
        cle = (d['_fichier'], d['_ligne'])
        if cle in vus:
            continue
        vus.add(cle)
        sortie.append(ligne_sortie(d, g, why, a.long))
    if not sortie:
        print('rien sur « %s ». Pensez à ajouter ce que vous trouverez (re/README.md).' % q)
        return 1
    lim = sortie if a.max == 0 else sortie[:a.max]
    print('\n'.join(lim))
    if len(lim) < len(sortie):
        print('… %d autres (option -n 0 pour tout)' % (len(sortie) - len(lim)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
