#!/usr/bin/env python3
"""verifie.py — contrôle de l'index des connaissances (re/connaissances/*.tsv, re/allocations.tsv).

Contrôles :
  - en-tête exacte et nombre de colonnes de chaque ligne ;
  - colonnes obligatoires remplies ; genre, confiance, état dans les listes admises ;
  - adresses bien formées selon l'espace ($ + 6 chiffres pour l'arcade, 0x… pour PS2 / PSP, plages
    début <= fin), homologues `espace:adr` avec un espace connu, déplacements `+$xx` ;
  - doublons (même fichier, même adresse, même genre, même nom = erreur ; même adresse et même genre
    sous deux noms = avertissement) ;
  - sources : chaque `§N` doit exister dans docs/journal/HANDOFF.md, chaque chemin du dépôt cité doit
    exister (les chemins `<workspace>/…` ne sont contrôlés que si HSFA_WORKSPACE est défini) ;
  - anonymat (chemins personnels) et absence de suites d'octets (données de jeu) ;
  - chevauchements de re/allocations.tsv (via zones.py).
Code de sortie : 0 si aucune erreur.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import connaissances as K  # noqa: E402

FORME = {
    'sfa3_arcade': r'\$[0-9A-F]{6}',
    'ro3': r'0x[0-9A-F]{1,8}', 'ro5': r'0x[0-9A-F]{1,8}', 'ro9': r'0x[0-9A-F]{1,8}',
    'ro9a': r'(?:0x[0-9A-F]{1,8}|\$[0-9A-F]{1,8})',
    'max_psp': r'0x[0-9A-F]{1,8}',
    'sfa1_arcade': r'\$[0-9A-F]{6}', 'sfa2_arcade': r'\$[0-9A-F]{6}', 'ssf2_arcade': r'\$[0-9A-F]{6}',
    'cps1_arcade': r'\$[0-9A-F]{6}', 'z80_son': r'\$[0-9A-F]{4}',
}
ANONYMAT = re.compile(r'/home/[A-Za-z]|/run/m[e]dia|/Users/[A-Za-z]|/tmp/claude-\d|@gmail\.|C:\\\\Users', re.I)
OCTETS = re.compile(r'\b(?:[0-9A-Fa-f]{2}[ ,]){12,}[0-9A-Fa-f]{2}\b|\b[0-9A-Fa-f]{32,}\b')
CHEMIN = re.compile(r'(?<![\w<>/.-])((?:docs|tools|max|src|scripts|patches|re|legacy)/[\w./-]*\w)')
CHEMIN_WS = re.compile(r'<workspace>/([\w./ -]*\w)')


def sections_journal():
    p = os.path.join(K.RACINE_DEPOT, 'docs', 'journal', 'HANDOFF.md')
    if not os.path.exists(p):
        return None
    s = set()
    for l in open(p, encoding='utf-8'):
        m = re.match(r'#{2,4}\s+(\d+)\s*[.:)]', l)
        if m:
            s.add(int(m.group(1)))
        for m in re.finditer(r'§\s?(\d+)', l) if l.startswith('#') else ():
            s.add(int(m.group(1)))
    return s


class Rapport:
    def __init__(self):
        self.err, self.av = [], []

    def e(self, ou, msg):
        self.err.append('%s : %s' % (ou, msg))

    def a(self, ou, msg):
        self.av.append('%s : %s' % (ou, msg))


def controle_adresse(R, ou, fichier, texte):
    forme = FORME.get(fichier)
    if forme is None:
        R.a(ou, "fichier %s inconnu : forme d'adresse non contrôlée" % fichier)
        return
    m = re.fullmatch(r'(%s)(?:-(%s))?' % (forme, forme), texte or '')
    if not m:
        R.e(ou, 'adresse mal formée « %s » (attendu %s, majuscules, plage a-b)' % (texte, forme))
        return
    if m.group(2) and K.hexv(m.group(2)) < K.hexv(m.group(1)):
        R.e(ou, 'plage inversée « %s »' % texte)


def controle_autres(R, ou, texte, champ=False):
    for esp, adr in K.autres(texte):
        if not esp:
            R.e(ou, 'homologue sans espace « %s » (forme espace:adr)' % adr)
            continue
        if champ and esp in ('img', 'psp', 'arcade', 'ro3', 'ro5', 'ro9', 'ro9a', 'cps2', 'img_ro5', 'img_ro9',
                             'img_ro9a', 'img_ro3'):
            pass
        elif esp not in K.ESPACES and esp not in K.ALIAS:
            R.e(ou, 'espace inconnu « %s »' % esp)
            continue
        if K.plage(adr) is None:
            R.e(ou, 'adresse homologue illisible « %s:%s »' % (esp, adr))


def controle_sources(R, ou, src, sections, ws):
    if not (src or '').strip():
        R.e(ou, 'source vide')
        return
    if sections is not None:
        for m in re.finditer(r'§\s?(\d+)', src):
            avant = src[:m.start()]
            if avant.endswith(('R', 'r')) and not avant.endswith(' R'):
                continue                       # « R§5 » : série du journal de la PS2
            jeton = re.search(r'(\S+)\s*$', avant)
            jeton = jeton.group(1) if jeton else ''
            if re.search(r'[./]|-|^[A-Z]{3,}$', jeton) and not re.match(r'^(HANDOFF(\.md)?|journal)$', jeton) \
                    and not jeton.startswith('§'):
                continue                       # « BLOC-HYPER.md §2 », « CARTE-ro5 §3 » : autre document
            if int(m.group(1)) not in sections:
                R.e(ou, 'section du journal inexistante : §%s' % m.group(1))
    for m in CHEMIN.finditer(src):
        c = m.group(1).rstrip('.')
        if not os.path.exists(os.path.join(K.RACINE_DEPOT, c)):
            R.e(ou, 'chemin cité inexistant dans le dépôt : %s' % c)
    if ws:
        for m in CHEMIN_WS.finditer(src):
            c = m.group(1).rstrip('.').strip()
            if not os.path.exists(os.path.join(ws, c)):
                R.a(ou, 'chemin <workspace> introuvable : %s' % c)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-v', '--avertissements', action='store_true', help='afficher tous les avertissements')
    a = ap.parse_args()
    R = Rapport()
    sections = sections_journal()
    ws = os.environ.get('HSFA_WORKSPACE')
    stats = {}
    for chemin in K.fichiers_connaissances():
        base = os.path.basename(chemin)
        fichier = os.path.splitext(base)[0]
        entete, lignes = K.lire_tsv(chemin)
        attendu = K.COLS_CHAMPS if base == 'champs.tsv' else K.COLS_ADR
        if not K.entete_valide(entete, attendu):
            R.e(base, 'en-tête inattendue : %s' % entete)
            continue
        attendu = entete
        vus, vus2 = {}, {}
        st = stats.setdefault(base, {})
        for d in lignes:
            ou = '%s:%d' % (base, d['_ligne'])
            st[d.get('confiance', '?')] = st.get(d.get('confiance', '?'), 0) + 1
            if d['_ncol'] != len(attendu):
                R.e(ou, '%d colonnes au lieu de %d' % (d['_ncol'], len(attendu)))
                continue
            o = d.get('outil', '').strip()
            if o and '/' in o and not o.startswith('<') and not os.path.exists(os.path.join(K.RACINE_DEPOT, o.split()[0])):
                R.a(ou, 'outil cité introuvable dans le dépôt : %s' % o)
            if d['confiance'] not in K.CONFIANCES:
                R.e(ou, 'confiance « %s » hors liste' % d['confiance'])
            if not d['nom'].strip():
                R.e(ou, 'nom vide')
            texte = '\t'.join(v for k, v in d.items() if not k.startswith('_'))
            if ANONYMAT.search(texte):
                R.e(ou, 'chemin ou identité personnelle')
            if OCTETS.search(re.sub(r'md5\s*:?\s*[0-9a-fA-F]{32}|\b[0-9a-f]{32}\b', '', texte)):
                R.e(ou, "suite d'octets : données de jeu ?")
            controle_sources(R, ou, d['source'], sections, ws)
            if base == 'champs.tsv':
                if not d['structure'].strip():
                    R.e(ou, 'structure vide')
                if not (d['decalage_ps2'] or d['decalage_arcade'] or d['decalage_autres']):
                    R.e(ou, 'aucun déplacement')
                for col in ('decalage_ps2', 'decalage_arcade'):
                    if d[col] and not re.fullmatch(r'\+\$[0-9A-F]+(-\+?\$[0-9A-F]+)?', d[col]):
                        R.e(ou, '%s mal formé « %s » (forme +$1A, majuscules)' % (col, d[col]))
                controle_autres(R, ou, d['decalage_autres'], champ=True)
                cle = (d['structure'], d['decalage_ps2'], d['decalage_arcade'], d['nom'])
            else:
                if d['genre'] not in K.GENRES:
                    R.e(ou, 'genre « %s » hors liste' % d['genre'])
                if d['adresse'] or (not d['adresse_autres'] and d['genre'] not in ('format', 'structure', 'constante')):
                    controle_adresse(R, ou, fichier, d['adresse'])
                controle_autres(R, ou, d['adresse_autres'])
                cle = (d['adresse'], d['genre'], d['nom'])
                cle2 = (d['adresse'] or '-' + d['nom'], d['genre'])
                if cle2 in vus2 and cle not in vus and fichier != 'z80_son':
                    R.a(ou, 'même adresse et même genre que la ligne %d (%s / %s)'
                        % (vus2[cle2][0], vus2[cle2][1], d['nom']))
                vus2.setdefault(cle2, (d['_ligne'], d['nom']))
            if cle in vus:
                R.e(ou, 'doublon de la ligne %d' % vus[cle])
            vus.setdefault(cle, d['_ligne'])
    # allocations
    if os.path.exists(K.ALLOCATIONS):
        entete, lignes = K.lire_tsv(K.ALLOCATIONS)
        if entete != K.COLS_ALLOC:
            R.e('allocations.tsv', 'en-tête inattendue : %s' % entete)
        else:
            stats['allocations.tsv'] = {}
            for d in lignes:
                ou = 'allocations.tsv:%d' % d['_ligne']
                st = stats['allocations.tsv']
                st[d.get('etat', '?')] = st.get(d.get('etat', '?'), 0) + 1
                if d['_ncol'] != len(K.COLS_ALLOC):
                    R.e(ou, '%d colonnes au lieu de %d' % (d['_ncol'], len(K.COLS_ALLOC)))
                    continue
                if d['etat'] not in K.ETATS:
                    R.e(ou, 'état « %s » hors liste' % d['etat'])
                a_, b_ = K.hexv(d['debut']), K.hexv(d['fin'])
                if a_ is None or b_ is None:
                    R.e(ou, 'début/fin illisibles « %s » « %s »' % (d['debut'], d['fin']))
                elif b_ < a_:
                    R.e(ou, 'fin avant début')
                texte = '\t'.join(v for k, v in d.items() if not k.startswith('_'))
                if ANONYMAT.search(texte):
                    R.e(ou, 'chemin ou identité personnelle')
                controle_sources(R, ou, d['source'], sections, ws)
            import zones
            ch = zones.chevauchements(lignes)
            nc = sum(1 for c in ch if c[0] == 'conflit')
            if nc:
                R.a('allocations.tsv', '%d chevauchement(s) en conflit entre occupants : voir zones.py --verifie' % nc)
    for base, st in sorted(stats.items()):
        print('%-22s %6d lignes  %s' % (base, sum(st.values()),
                                        '  '.join('%s %d' % kv for kv in sorted(st.items()))))
    if R.av:
        print('\n%d avertissement(s)' % len(R.av))
        for x in (R.av if a.avertissements else R.av[:15]):
            print('  avert. ' + x)
        if not a.avertissements and len(R.av) > 15:
            print('  … (-v pour tout)')
    print('\n%d erreur(s)' % len(R.err))
    for x in R.err[:200]:
        print('  ERREUR ' + x)
    return 1 if R.err else 0


if __name__ == '__main__':
    sys.exit(main())
