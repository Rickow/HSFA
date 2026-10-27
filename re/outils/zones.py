#!/usr/bin/env python3
"""zones.py — registre des zones occupées (re/allocations.tsv).

  zones.py                      liste toutes les zones, par cible puis par adresse
  zones.py image68k_ro5         liste une cible
  zones.py 0x3FEF00             zones (toutes cibles) qui contiennent cette adresse
  zones.py image68k_ro5 0x3A0000 0x3BFFFF
                                zones d'une cible qui recouvrent une plage (avant de réserver)
  zones.py --verifie            chevauchements seulement ; code 1 s'il y a un conflit

Règle : réserver une zone dans re/allocations.tsv AVANT de l'utiliser, puis lancer zones.py --verifie.
Un chevauchement est un CONFLIT quand deux occupants différents utilisent ou réservent la même plage.
N'est qu'une INFORMATION : une sous-zone du même occupant, une zone déclarée « englobante » dans la
remarque, ou une zone « libre prouvé » (en partie) occupée depuis — à rétrécir quand on la consomme.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import connaissances as K  # noqa: E402


def zones():
    if not os.path.exists(K.ALLOCATIONS):
        return []
    return K.lire_tsv(K.ALLOCATIONS)[1]


def bornes(z):
    a, b = K.hexv(z.get('debut')), K.hexv(z.get('fin'))
    return (a, b) if a is not None and b is not None else None


def englobante(z):
    r = K.sans_accents(z.get('remarque', ''))
    return 'englobante' in r or "s'excluent" in r


def chevauchements(lignes):
    """[(gravité, message)] ; gravité = 'conflit' ou 'info'."""
    par_cible = {}
    for z in lignes:
        if bornes(z):
            par_cible.setdefault(z['cible'], []).append(z)
    res = []
    for cible, zs in sorted(par_cible.items()):
        zs.sort(key=lambda z: bornes(z))
        for i, z1 in enumerate(zs):
            a1, b1 = bornes(z1)
            for z2 in zs[i + 1:]:
                a2, b2 = bornes(z2)
                if a2 > b1:
                    break
                lib = [z for z in (z1, z2) if z['etat'] == 'libre prouvé']
                meme = z1['occupant'] == z2['occupant']
                if len(lib) == 2:
                    continue
                contient = (a1 <= a2 and b2 <= b1) or (a2 <= a1 and b1 <= b2)
                if lib:
                    grav = 'info'          # zone prouvée libre, maintenant (en partie) occupée : à rétrécir
                elif meme or (contient and (englobante(z1) or englobante(z2))) or \
                        ("s'excluent" in K.sans_accents(z1.get('remarque', '') + z2.get('remarque', ''))):
                    grav = 'info'
                else:
                    grav = 'conflit'
                res.append((grav, '%s %s : %s-%s « %s » (%s, l.%d) recouvre %s-%s « %s » (%s, l.%d)' % (
                    grav.upper(), cible, z1['debut'], z1['fin'], z1['occupant'], z1['etat'], z1['_ligne'],
                    z2['debut'], z2['fin'], z2['occupant'], z2['etat'], z2['_ligne'])))
    return res


def affiche(z):
    a, b = bornes(z) or (0, -1)
    taille = b - a + 1
    t = ('%d o' % taille) if taille < 10240 else ('%.0f Ko' % (taille / 1024))
    return '%-14s %-10s %-10s %8s  %-12s %-28s %s | %s' % (
        z['cible'], z['debut'], z['fin'], t, z['etat'], z['occupant'][:28], z.get('remarque', '')[:90],
        z.get('source', '')[:60])


def main(argv):
    zs = zones()
    if not zs:
        print('re/allocations.tsv absent ou vide')
        return 1
    if '--verifie' in argv:
        ch = chevauchements(zs)
        for g, m in ch:
            print(m)
        n = sum(1 for g, _ in ch if g == 'conflit')
        print('%d conflit(s), %d information(s)' % (n, len(ch) - n))
        return 1 if n else 0
    cibles = {z['cible'] for z in zs}
    cible = argv[0] if argv and argv[0] in cibles else None
    reste = argv[1:] if cible else argv
    vals = [K.hexv(x) for x in reste]
    if any(v is None for v in vals):
        print('argument illisible : %s (cibles connues : %s)' % (' '.join(reste), ', '.join(sorted(cibles))))
        return 2
    sel = [z for z in zs if bornes(z) and (cible is None or z['cible'] == cible)]
    if vals:
        a = vals[0]
        b = vals[1] if len(vals) > 1 else a
        sel = [z for z in sel if bornes(z)[0] <= b and a <= bornes(z)[1]]
    sel.sort(key=lambda z: (z['cible'], bornes(z)))
    for z in sel:
        print(affiche(z))
    if not sel:
        print('aucune zone enregistrée' + (' sur cette plage' if vals else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
