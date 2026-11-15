#!/usr/bin/env python3
"""cmp_fins_upper.py : banc des fins, comparaison des IMAGES a Upper (l'oracle des fins de la greffe).

usage : cmp_fins_upper.py TRACES PREFIXE [TEMOIN] [--sortie F.md] [--seuil 3.0] [--upper U]

TRACES contient, pour chaque fin jouee, le dossier PREFIXE_<perso>_<version>/ (captures MAME, snap/**.png) et le
journal PREFIXE_<perso>_<version>.sf (« n image_absolue image_relative » : une capture toutes les 60 images depuis
l'entree en fin, $FF8004 = $A ; lua snaps_fin.lua) ; la reference d'Upper du perso est U_<perso>/ + U_<perso>.sf (U = u
par defaut, --upper pour une autre serie ; meme graine imposee, meme recette).
ORACLE (15/11) : les references doivent venir de l'Upper traduit par le traducteur courant, greffe_arcade/fige/ro5_v161
(programme = celui de l'Upper publie, v161). L'ancien fige/ro5 (traducteur v153) a 19 echanges EXG Dx,Dy casses
(MOVE.L Dx,Dy ; MOVE.L Dy,Dx), dont 12 dans des acteurs de fin : il teleporte les acteurs qui marchent vers une cible
avec une vitesse negative (§233, §234). Les images sont comparees a la MEME image relative (pixel different = ecart > 24 sur
un canal, comme cmp_snaps.py des mesures).

Par fin : images comparees, ecart moyen a Upper (% de pixels), images « proches » d'Upper (ecart < seuil), 1re image
relative ecartee (hors image 0, la transition, toujours differente). Avec TEMOIN (prefixe d'une autre construction, meme banc) : images IDENTIQUES au temoin (au pixel),
images plus proches d'Upper (gain > 1 point) et plus loin (perte > 1 point), avec leurs plages : une fin que le
correctif ne touche pas doit rester identique au temoin ; une fin corrigee doit se rapprocher d'Upper.
Duree de la fin lue dans PREFIXE_<p>_<v>/journal.txt (« FIN_A n duree d »), « - » si absente."""
import sys, os, glob, re
from PIL import Image, ImageChops

def args():
    a = [x for x in sys.argv[1:]]
    opt = {'--sortie': None, '--seuil': '3.0', '--upper': 'u'}
    for k in list(opt):
        if k in a: i = a.index(k); opt[k] = a[i + 1]; del a[i:i + 2]
    if len(a) < 2: sys.exit(__doc__)
    return a[0], a[1], (a[2] if len(a) > 2 else None), opt['--sortie'], float(opt['--seuil']), opt['--upper']

def serie(d, sf):
    if not (os.path.isdir(d) and os.path.exists(sf)): return {}
    fs = sorted(glob.glob(os.path.join(d, '**', '*.png'), recursive=True), key=lambda f: (len(f), f))
    rel = [int(l.split()[2]) for l in open(sf, encoding='utf-8') if len(l.split()) > 2]
    return dict(zip(rel, fs))

_cache = {}
def img(f):
    if f not in _cache:
        if len(_cache) > 600: _cache.clear()
        _cache[f] = Image.open(f).convert('RGB')
    return _cache[f]

def ecart(fa, fb):
    a, b = img(fa), img(fb)
    if a.size != b.size: return 100.0
    d = ImageChops.difference(a, b).convert('L').point(lambda v: 255 if v > 24 else 0)
    return 100.0 * d.histogram()[255] / (a.size[0] * a.size[1])

def plages(xs):
    out = []
    for x in sorted(xs):
        if out and x - out[-1][1] <= 60: out[-1][1] = x
        else: out.append([x, x])
    return ' '.join('%d' % a if a == b else '%d-%d' % (a, b) for a, b in out) or '-'

def duree(d):
    try: m = re.search(r'FIN_A (\d+) duree (\d+)', open(os.path.join(d, 'journal.txt'), encoding='utf-8', errors='replace').read())
    except OSError: return '-'
    return m.group(2) if m else '-'

def main():
    T, P, TM, sortie, seuil, UP = args()
    fins = sorted(os.path.basename(d)[len(P) + 1:] for d in glob.glob(os.path.join(T, P + '_*_*')) if os.path.isdir(d))
    lignes = ['| fin | durée | durée témoin | images | écart moyen à Upper | proches (< %.1f %%) | 1re écartée | témoin : écart moyen | '
              'identiques au témoin | plus proches d\'Upper | plus loin d\'Upper |' % seuil, '|' + '---|' * 11]
    tot = dict(n=0, ident=0, mieux=0, pire=0)
    for f in fins:
        p, v = f.split('_', 1)
        U = serie(os.path.join(T, UP + '_' + p), os.path.join(T, '%s_%s.sf' % (UP, p)))
        A = serie(os.path.join(T, '%s_%s' % (P, f)), os.path.join(T, '%s_%s.sf' % (P, f)))
        B = serie(os.path.join(T, '%s_%s' % (TM, f)), os.path.join(T, '%s_%s.sf' % (TM, f))) if TM else {}
        rs = sorted(set(A) & set(U))
        ea = {r: ecart(A[r], U[r]) for r in rs}
        prem = next((r for r in rs if r > 0 and ea[r] >= seuil), None)   # l'image 0 (transition) differe toujours
        moy = sum(ea.values()) / len(ea) if ea else 0.0
        cols = [f, duree(os.path.join(T, '%s_%s' % (P, f))), duree(os.path.join(T, '%s_%s' % (TM, f))) if TM else '-',
                str(len(rs)), '%.1f %%' % moy if rs else '(pas de référence)', str(sum(1 for r in rs if ea[r] < seuil)),
                str(prem) if prem is not None else '-']
        if TM and B:
            rb = [r for r in rs if r in B]
            eb = {r: ecart(B[r], U[r]) for r in rb}
            ident = [r for r in sorted(set(A) & set(B)) if ecart(A[r], B[r]) == 0.0]
            mieux = [r for r in rb if ea[r] < eb[r] - 1.0]; pire = [r for r in rb if ea[r] > eb[r] + 1.0]
            nab = len(set(A) & set(B))
            cols += ['%.1f %%' % (sum(eb.values()) / len(eb)) if eb else '-', '%d / %d' % (len(ident), nab),
                     '%d : %s' % (len(mieux), plages(mieux)) if mieux else '0', '%d : %s' % (len(pire), plages(pire)) if pire else '0']
            tot['n'] += nab; tot['ident'] += len(ident); tot['mieux'] += len(mieux); tot['pire'] += len(pire)
        else:
            cols += ['-'] * 4
        lignes.append('| ' + ' | '.join(cols) + ' |')
        print(lignes[-1], flush=True)
    resume = '%d fins (%s, references %s_) ; ' % (len(fins), P, UP) + ('contre %s : %d images, %d identiques, %d plus proches d\'Upper, %d plus loin'
                                                  % (TM, tot['n'], tot['ident'], tot['mieux'], tot['pire']) if TM else 'sans témoin')
    print(resume)
    if sortie:
        open(sortie, 'w', encoding='utf-8').write('# Banc des fins : images contre Upper (%s)\n\n%s\n\n%s\n' % (P, resume, '\n'.join(lignes)))

if __name__ == '__main__':
    main()
