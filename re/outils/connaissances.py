"""Lecture commune des fichiers de l'index des connaissances (re/connaissances/*.tsv, re/allocations.tsv).

Utilisé par quoi.py, verifie.py et zones.py. Aucune dépendance hors bibliothèque standard.
"""
import os
import re
import unicodedata

RACINE_RE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # .../re
RACINE_DEPOT = os.path.dirname(RACINE_RE)
DOSSIER = os.path.join(RACINE_RE, 'connaissances')
ALLOCATIONS = os.path.join(RACINE_RE, 'allocations.tsv')

COLS_ADR = ['adresse', 'adresse_autres', 'genre', 'nom', 'role', 'taille_type', 'mises_en_garde',
            'source', 'confiance']
COLS_CHAMPS = ['structure', 'decalage_ps2', 'decalage_arcade', 'decalage_autres', 'espaces', 'nom',
               'role', 'taille_type', 'mises_en_garde', 'source', 'confiance']
COLS_FACULTATIVES = ['score', 'outil']      # en fin de ligne, dans cet ordre, facultatives
COLS_ALLOC = ['cible', 'debut', 'fin', 'occupant', 'etat', 'source', 'remarque']

# fichier -> nom de l'espace tel qu'il s'écrit dans adresse_autres
ESPACE_DU_FICHIER = {'sfa3_arcade': 'arcade', 'ro3': 'ro3', 'ro5': 'ro5', 'ro9': 'ro9', 'ro9a': 'ro9a',
                     'max_psp': 'psp', 'sfa1_arcade': 'sfa1_arcade', 'sfa2_arcade': 'sfa2_arcade',
                     'ssf2_arcade': 'ssf2_arcade', 'cps1_arcade': 'cps1_arcade', 'z80_son': 'z80_son'}
ESPACES = {'arcade', 'ro3', 'ro5', 'ro9', 'ro9a', 'psp', 'img_ro3', 'img_ro5', 'img_ro9', 'img_ro9a',
           'cps2', 'sfa1_arcade', 'sfa2_arcade', 'ssf2_arcade', 'cps1_arcade', 'z80_son',
           'cvs2_ps2', 'cfe_ps2', 'fichier_ro5', 'fichier_ro9'}  # fichier_roN : décalage dans le fichier du module PS2 ; exécutables PS2 de Capcom vs. SNK 2 et Capcom Fighting Evolution (noms de symboles)
# synonymes tolérés dans adresse_autres (nom canonique à droite)
ALIAS = {'upper': 'ro5', 'hyper': 'ro9', 'sfa3': 'arcade', 'max': 'psp', 'image68k_ro5': 'img_ro5',
         'image68k_ro9a': 'img_ro9a'}


def entete_valide(entete, base):
    """en-tête = colonnes obligatoires + un préfixe des colonnes facultatives."""
    n = len(base)
    return entete[:n] == base and entete[n:] == COLS_FACULTATIVES[:len(entete) - n]
GENRES = {'fonction', 'table', 'variable', 'champ', 'structure', 'format', 'constante'}
CONFIANCES = {'mesuré', 'déduit', 'supposé'}
ETATS = {'utilisé', 'réservé', 'libre prouvé'}

RE_HEX = r'(?:\$|0x)[0-9A-Fa-f]+'


def sans_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()


def hexv(s):
    """'$1A2B' / '0x1A2B' / '1A2B' -> entier (None si illisible)."""
    s = (s or '').strip()
    if s.startswith('+'):
        s = s[1:]
    if s.startswith('-'):
        return None
    if s.startswith('$'):
        s = s[1:]
    elif s.lower().startswith('0x'):
        s = s[2:]
    if not s or not re.fullmatch(r'[0-9A-Fa-f]+', s):
        return None
    return int(s, 16)


def plage(texte):
    """'$1000' -> (0x1000, 0x1000) ; '0x10-0x1F' -> (0x10, 0x1F) ; sinon None."""
    texte = (texte or '').strip().replace('+', '')
    m = re.fullmatch(r'(%s)\s*-\s*(%s)' % (RE_HEX, RE_HEX), texte)
    if m:
        return hexv(m.group(1)), hexv(m.group(2))
    v = hexv(texte)
    return (v, v) if v is not None else None


TAILLES = {'B': 1, 'W': 2, 'L': 4}


def etendue_taille(taille_type):
    """Étendue en octets lisible dans taille_type : « N × B|W|L … » en tête, ou « (N o) »."""
    t = (taille_type or '').strip()
    m = re.match(r'(\d+)\s*[×x\*]\s*([BWL])\b', t)
    if m:
        return int(m.group(1)) * TAILLES[m.group(2)]
    m = re.search(r'\((\d+)\s*o\)', t)
    if m:
        return int(m.group(1))
    return None


def autres(texte):
    """'img_ro5:$1DFB78; arcade:$0DD412' -> [('img_ro5', '$1DFB78'), ('arcade', '$0DD412')]."""
    res = []
    for morceau in (texte or '').split(';'):
        morceau = morceau.strip()
        if not morceau:
            continue
        if ':' in morceau:
            esp, adr = morceau.split(':', 1)
            esp = esp.strip()
            res.append((ALIAS.get(esp, esp), adr.strip()))
        else:
            res.append(('', morceau))
    return res


def lire_tsv(chemin):
    """Renvoie (en-tête, lignes) ; chaque ligne = dict avec '_ligne' (numéro) et '_fichier'."""
    with open(chemin, encoding='utf-8') as f:
        brut = f.read().split('\n')
    if brut and brut[-1] == '':
        brut.pop()
    if not brut:
        return [], []
    entete = brut[0].split('\t')
    lignes = []
    nom = os.path.splitext(os.path.basename(chemin))[0]
    for i, l in enumerate(brut[1:], start=2):
        if not l.strip() or l.startswith('#'):
            continue
        cellules = l.split('\t')
        d = dict(zip(entete, cellules))
        d['_ligne'] = i
        d['_fichier'] = nom
        d['_ncol'] = len(cellules)
        lignes.append(d)
    return entete, lignes


def fichiers_connaissances():
    if not os.path.isdir(DOSSIER):
        return []
    return sorted(os.path.join(DOSSIER, f) for f in os.listdir(DOSSIER) if f.endswith('.tsv'))


def charger_tout():
    """{'adresses': [...], 'champs': [...], 'allocations': [...]}"""
    adr, ch = [], []
    for chemin in fichiers_connaissances():
        _, lignes = lire_tsv(chemin)
        if os.path.basename(chemin) == 'champs.tsv':
            ch.extend(lignes)
        else:
            adr.extend(lignes)
    al = lire_tsv(ALLOCATIONS)[1] if os.path.exists(ALLOCATIONS) else []
    return {'adresses': adr, 'champs': ch, 'allocations': al}


def etendue_ligne(d):
    """(début, fin) de l'adresse principale d'une ligne d'adresses, taille comprise."""
    p = plage(d.get('adresse', ''))
    if p is None:
        return None
    a, b = p
    if a == b:
        n = etendue_taille(d.get('taille_type', ''))
        if n and n > 1:
            b = a + n - 1
    return a, b
