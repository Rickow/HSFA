#!/usr/bin/env python3
"""(banc_coups) FRAME DATA PUBLIEE : wikitexte des pages SuperCombo « Street Fighter Alpha 3/<perso> » (recupere par
l'API MediaWiki publique, frame_data/brut/<perso>.json, revid et date notes) -> frame_data/supercombo_sfa3.csv.

Colonnes : perso;section;coup;degats;demarrage;actif;recuperation;avantage_garde;avantage_contact;page;revid;date;remarque
« Frame Count » s/a/r = demarrage / actif / recuperation ; « Block Stun » = avantage en garde ; « Hit Stun » = au contact
(normal/contre). Valeur absente -> vide ; valeur non numerique (plusieurs coups, « KD »...) recopiee telle quelle et
signalee « douteux » en remarque. Rien n'est invente.
Usage : frame_data_sc.py [date]   (date de releve, defaut : date du fichier json)
"""
import json, os, re, sys, glob, time
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(B, 'frame_data')


def cellules(bloc):
    """{libelle: valeur} d'un tableau STDiagram"""
    c = {}
    for l in bloc.split('\n'):
        m = re.match(r"\{\{STDiagramCell\|\s*([^}]*)\}\}\s*([^|]*)\|\{\{STDiagramCell\s*\|\s*([^}]*)\}\}", l)
        if m:
            lab = (m.group(1).strip() + ' ' + m.group(2).strip()).strip()
            val = re.sub(r'</?b>', '', m.group(3)).strip()
            c[lab] = val
    return c


def coups(w):
    sec = ''
    res = []
    # en-tetes de coup : « *<b>Nom:</b> » ou « '''Nom [[File...]]:''' »
    pos = []
    for m in re.finditer(r"^====\s*(.*?)\s*====\s*$|^\*\s*<b>(.*?):?</b>|^'''(.*?)'''\s*$", w, re.M):
        pos.append((m.start(), m))
    for i, (p, m) in enumerate(pos):
        if m.group(1):
            sec = m.group(1)
            continue
        nom = m.group(2) or m.group(3) or ''
        nom = re.sub(r'\[\[File:[^\]]*\]\]', '', nom).strip().rstrip(':').strip()
        isms = ','.join(re.findall(r'File:([XAV])-ISM', m.group(0)))
        fin = pos[i + 1][0] if i + 1 < len(pos) else len(w)
        bloc = w[p:fin]
        if 'STDiagram' not in bloc:
            continue
        res.append((sec, nom, isms, cellules(bloc)))
    return res


def num(v):
    return bool(re.fullmatch(r'[+-]?\d+', v or ''))


def main():
    lignes = ['perso;section;coup;ismes;degats;demarrage;actif;recuperation;avantage_garde;avantage_contact;page;revid;date;remarque']
    for f in sorted(glob.glob(os.path.join(D, 'brut', '*.json'))):
        d = json.load(open(f))['parse']
        page, rev = d['title'], d.get('revid', '')
        date = sys.argv[1] if len(sys.argv) > 1 else time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(f)))
        perso = page.split('/', 1)[1]
        for sec, nom, isms, c in coups(d['wikitext']['*']):
            fc = c.get('Frame Count', '')
            s = a = r = ''
            rem = []
            m = re.fullmatch(r'\s*([^/]*)/([^/]*)/([^/]*)\s*', fc)
            if m:
                s, a, r = (x.strip() for x in m.groups())
            elif fc:
                rem.append('frame count non découpable : %s' % fc)
            else:
                rem.append('pas de frame count')
            dg = c.get('Damage', c.get('Damage(Ender)', ''))
            bg = c.get('Block Stun', '')
            hc = c.get('Hit Stun/Counter Hit', c.get('Hit Stun', ''))
            hit = hc.split('/')[0].strip() if hc else ''
            for lab, v in (('démarrage', s), ('actif', a), ('récupération', r), ('garde', bg), ('contact', hit)):
                if v and not num(v):
                    rem.append('%s douteux (%s)' % (lab, v))
            lignes.append(';'.join(x.replace(';', ',') for x in [perso, sec, nom, isms, dg, s, a, r, bg, hit, page, str(rev), date,
                                                                  ' / '.join(rem)]))
    open(os.path.join(D, 'supercombo_sfa3.csv'), 'w').write('\n'.join(lignes) + '\n')
    print(len(lignes) - 1, 'coups')


if __name__ == '__main__':
    main()
