#!/usr/bin/env python3
"""preuve_traces.py (banc_unique, 16/11) : PREUVE À UNE LECTURE — compare les sorties du banc unique (runs/<nom>/cand ou
cache/<id>) aux traces DÉJÀ ÉTABLIES par les chantiers (autres harnais, autres noms de fichiers), octet par octet.

  preuve_traces.py FAMILLE DOSSIER_BANC DOSSIER_ETABLI [PREFIXE] [--sans MOTIF]
FAMILLE : versus (journal.txt+menu.txt+snap  <->  TRACE/vs.log + TRACE.menu + snap ; PREFIXE = chemin de la trace),
          fins (DOSSIER_BANC/<p_v>/{journal.txt,sf.txt,graine.txt,sent.txt,sent.txt.totaux,snap} <-> ETABLI/PREFIXE_<p_v>{/journal.txt,.sf,.graine,.sent,.sent.totaux,/snap}),
          arcade (journal.txt, sonde.txt, graine.txt, snap <-> ETABLI/{journal.txt,sonde.txt,graine.txt,snap}),
          decors (DOSSIER_BANC/<x>/{bd.txt,snap} <-> ETABLI/PREFIXE_<x>.txt + PREFIXE_<x>/snap),
          max (DOSSIER_BANC/<clé>/journal.txt <-> ETABLI/<clé ou pXX>/log.txt ; --sans MOTIF : lignes ignorées, ex. EPALE).
Sortie : une ligne par partie (IDENT ou ce qui diffère) puis le total."""
import sys, os, glob, hashlib, re


def md5(f):
    return hashlib.md5(open(f, 'rb').read()).hexdigest()


def snaps(d):
    return {os.path.relpath(f, d): md5(f) for f in glob.glob(d + '/**/*.png', recursive=True)} if os.path.isdir(d) else {}


def lit(f, sans):
    if not os.path.isfile(f):
        return None
    t = open(f, 'rb').read()
    if f.endswith('.totaux'):    # ordre d'un parcours de table Lua : comparé trié
        t = b'\n'.join(sorted(t.split(b'\n')))
    if sans:
        t = b'\n'.join(l for l in t.split(b'\n') if not re.search(sans.encode(), l))
    return t


def paire(nom, couples, sa, sb, sans=None):
    x = []
    for a, b in couples:
        ta, tb = lit(a, sans), lit(b, sans)
        if ta is None or tb is None:
            x.append('%s absent (%s)' % (os.path.basename(a), 'banc' if ta is None else 'établi'))
        elif ta != tb:
            x.append('%s DIFF' % os.path.basename(a))
    if sa is not None:
        A, B = snaps(sa), snaps(sb)
        d = [k for k in set(A) | set(B) if A.get(k) != B.get(k)]
        x.append('captures %d/%d identiques' % (len(A) - len([k for k in d if k in A]), len(B)) + (' (écarts %s)' % ' '.join(sorted(os.path.basename(k) for k in d)[:12]) if d else ''))
        ok = not d and len(A) == len(B)
    else:
        ok = True
    ok = ok and not [y for y in x if 'DIFF' in y or 'absent' in y]
    print('%s : %s%s' % (nom, 'IDENT' if ok else 'DIFFÉRENT', (' ; ' + ' ; '.join(x)) if x else ''))
    return ok


def main():
    a = sys.argv[1:]
    sans = None
    if '--sans' in a:
        i = a.index('--sans'); sans = a[i + 1]; del a[i:i + 2]
    fam, B, E = a[0], a[1], a[2]
    P = a[3] if len(a) > 3 else ''
    n = k = 0
    if fam == 'versus':
        n, k = 1, paire(os.path.basename(E), [(B + '/journal.txt', E + '/vs.log'), (B + '/menu.txt', E + '.menu')], B + '/snap', E + '/snap')
    elif fam == 'arcade':
        n, k = 1, paire(os.path.basename(E), [(B + '/' + f, E + '/' + f) for f in ('journal.txt', 'sonde.txt', 'graine.txt')], B + '/snap', E + '/snap')
    elif fam == 'fins':
        for d in sorted(glob.glob(B + '/*/')):
            c = os.path.basename(d.rstrip('/'))
            e = os.path.join(E, '%s_%s' % (P, c))
            n += 1
            k += paire(c, [(d + 'journal.txt', e + '/journal.txt'), (d + 'sf.txt', e + '.sf'), (d + 'graine.txt', e + '.graine'),
                           (d + 'sent.txt', e + '.sent'), (d + 'sent.txt.totaux', e + '.sent.totaux')], d + 'snap', e + '/snap')
    elif fam == 'decors':
        for d in sorted(glob.glob(B + '/*/')):
            c = os.path.basename(d.rstrip('/'))
            e = os.path.join(E, '%s_%s' % (P, c))
            n += 1
            k += paire(c, [(d + 'bd.txt', e + '.txt')], d + 'snap', e + '/snap')
    elif fam == 'max':
        for d in sorted(glob.glob(B + '/*/')):
            c = os.path.basename(d.rstrip('/'))
            e = os.path.join(E, c) if os.path.isdir(os.path.join(E, c)) else os.path.join(E, 'p' + c)
            n += 1
            k += paire(c, [(d + 'journal.txt', e + '/log.txt')], None, None, sans)
    print('TOTAL %s : %d/%d identiques aux traces établies (%s)' % (fam, k, n, E))


if __name__ == '__main__':
    main()
