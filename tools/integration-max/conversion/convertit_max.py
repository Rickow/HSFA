#!/usr/bin/env python3
"""convertit_max.py — passe de conversion du code 68K des persos MAX : disposition mémoire ARCADE SFA3 -> disposition de
l'image traduite d'UPPER (portage PS2, mame_ro5).

Usage : python3 convertit_max.py [--sources DIR] [--sortie DIR] [--carte FICHIER] [--roms DIR] [--sans-image]

Entrées (lecture seule) :
  sources .s (vasm) ........ SFA3 MAX : work/re/rosette_code/ (code + données lues par le moteur)
  typage des champs ........ agent_typage_max/champs_types_upper.tsv (+ décisions de bases_forcees.tsv / ce fichier)
  adresses du moteur ....... agent_max_upper/correspondances.tsv + correspondances_complement.tsv (arcade -> va MIPS)
  carte de l'image ......... mame_ro5/carte_image.txt du moment (va MIPS -> adresse image) : RÉSOLUTION À CHAQUE LANCEMENT
  image ................... mame_ro5/roms_ro5/sfa3ud (adresses des routines CONV_An, contrôle carte <-> image)
Sorties (dans --sortie) :
  <fichier>.s convertis, adresses_upper.s (equ UP_xxxxx = adresse image résolue), tout_max_upper.s (assemblage),
  journal.tsv (une ligne par réécriture / cas non résolu), non_resolus.tsv, stats.json.

Invariant de la conversion : LES REGISTRES PORTENT TOUJOURS LA VALEUR LOGIQUE (arcade) ; seule la mémoire typée suit la
disposition de l'image. Chaque lecture d'un champ dont la disposition diffère est remise en ordre dans le registre ;
chaque écriture est remise en disposition image. Les copies mémoire -> mémoire entre champs de même disposition sont
recopiées telles quelles. Rien n'est deviné : un accès dont la base ou le champ n'est pas typé est laissé tel quel et
signalé « NON RÉSOLU ».
"""
import os, re, sys, csv, json, argparse, struct, datetime, subprocess
from collections import Counter, defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
SRC_DEF = '<workspace>/work/agent_integration_max/max_trad/rosette_code'   # (agent_integration_max) copie + gestionnaires d'Eagle
TYPES = '<workspace>/work/agent_typage_max/champs_types_upper.tsv'
CORR = '<workspace>/work/agent_max_upper/correspondances.tsv'
COMPL = os.path.join(ICI, 'correspondances_complement.tsv')
FORCEES = os.path.join(ICI, 'bases_forcees.tsv')
CARTE_DEF = '<workspace>/work/agent_integration_max/banc_ref/carte_image.txt'
ROMS_DEF = '<workspace>/work/agent_integration_max/banc_ref/roms_ro5/sfa3ud'
ROM_FICHIERS = ['sz3ud.03c', 'sz3ud.04c', 'sz3.05c', 'sz3.06c', 'sz3.07c', 'sz3.08c', 'sz3.09c', 'sz3.10b']

FICHIERS_ACTEURS = {'acteurs_fins_max.s', 'acteurs_fins_main.s'}       # objets = acteurs de fin (carte « acteur », voir OCT['acteur'])
FICHIERS_CODE = ['commandes_voix_max.s', 'commandes_son_max.s', 'moteur_max_main.s', 'moteur_max_auto.s', 'brouillon_eagle.s',
                 'brouillon_maki.s', 'brouillon_yun.s', 'brouillon_ingrid.s', 'acteurs_fins_max.s', 'acteurs_fins_main.s',
                 'gestionnaires_main.s', 'contres_max.s']   # (agent_integration_max) fonctions à la main de la session MAX (2026-10-11 soir) ; contres (17/10)
# données lues par le MOTEUR d'Upper (format PS2 de l'image) : converties par convertit_donnees()
FICHIERS_DONNEES_MOTEUR = ['tables_explicites_eagle.s', 'tables_explicites_maki.s', 'tables_explicites_yun.s',
                           'tables_explicites_ingrid.s', 'donnees_projectiles_max.s']
# données lues UNIQUEMENT par le code MAX (gros-boutiste, recopiées telles quelles)
FICHIERS_DONNEES_MAX = ['donnees_max.s', 'donnees_sauts_max.s', 'donnees_acteurs_fins.s', 'donnees_fins_t12c.s',
                        'sons_pas_max.s']   # (agent_integration_max) sons par pas ($E6) des 4 persos (2026-10-17)
ORDRE_ASSEMBLAGE = (['adresses_upper.s'] + FICHIERS_CODE + FICHIERS_DONNEES_MOTEUR[:4] + FICHIERS_DONNEES_MAX
                    + FICHIERS_DONNEES_MOTEUR[4:])

# ============================================================================================ outils numériques / texte
def num(t):
    """valeur d'une expression numérique simple ($hex, %bin, décimal, + -) ; None si symbolique"""
    t = t.strip().replace(' ', '')
    if not t: return None
    toks = re.findall(r'[+-]|[^+-]+', t)
    v, sg, att = 0, 1, True
    for k in toks:
        if k in '+-':
            sg = sg * (-1 if k == '-' else 1); continue
        if k.startswith('$'): x = int(k[1:], 16) if re.fullmatch(r'\$[0-9a-fA-F]+', k) else None
        elif k.startswith('%'): x = int(k[1:], 2) if re.fullmatch(r'%[01]+', k) else None
        elif re.fullmatch(r'\d+', k): x = int(k)
        else: x = None
        if x is None: return None
        v += sg * x; sg = 1
    return v

def hx(v):
    return ('-$%x' % -v) if v < 0 else ('$%x' % v)

def split_ops(s):
    out, cur, prof = [], '', 0
    for c in s:
        if c == '(': prof += 1
        elif c == ')': prof -= 1
        if c == ',' and prof == 0: out.append(cur.strip()); cur = ''
        else: cur += c
    if cur.strip(): out.append(cur.strip())
    return out

TAILLE = {'b': 1, 'w': 2, 'l': 4, 's': None}
SUF = {1: 'b', 2: 'w', 4: 'l'}

# ============================================================================================ modèle des champs
class NonResolu(Exception):
    pass

# classes d'octet : ('u8',) ; ('s16',) ; ('s32', F) ; ('ptr', F) ; ('libre',)
def charge_types():
    rows = list(csv.DictReader(open(TYPES), delimiter='\t'))
    OCT = {}                      # base -> {octet: classe}
    NOTE = {}                     # (base, d, taille) -> note
    LIGNE = {}                    # (base, d, taille) -> ligne du TSV
    A5 = {}
    conflits = []
    def pose(base, b, c, src):
        o = OCT.setdefault(base, {})
        if b in o and o[b] != c:
            conflits.append((base, b, o[b], c, src)); return
        o[b] = c
    for r in rows:
        if r['base'] == 'objet' and r['depl_arcade'] in ('$3D4',): continue   # remplacé par la décision $3D4 ci-dessous
        base = r['base']; d = int(r['depl_arcade'][1:], 16); sz = int(r['taille']); ty = r['type']
        LIGNE[(base, d, sz)] = r
        if base == 'A5':
            A5[(d, sz)] = r; continue
        key = {'objet': 'objet', "pas d'animation": 'pas'}.get(base)
        if key is None:                      # bases « pointeur a0/a3 » : décisions locales (voir plus bas)
            continue
        src = '%s $%X.%d' % (base, d, sz)
        if ty.startswith('ERREUR') or ty.startswith('inconnu') or ty.startswith('ambigu'):
            NOTE[(key, d, sz)] = ty; continue
        if ty.startswith('jamais accédé') or ty.startswith('MAX seul'):
            for k in range(sz): pose(key, d + k, ('libre',), src)
            continue
        if ty.startswith('u8[4]') or ty.startswith('u8[2]'):
            for k in range(sz): pose(key, d + k, ('u8',), src)
            if 'union' in ty: NOTE[(key, d, sz)] = ty
            continue
        if ty.startswith('u8'):
            pose(key, d, ('u8',), src); continue
        if ty.startswith('s16[2]'):
            for k in range(4): pose(key, d + k, ('s16',), src)
            continue
        if ty.startswith('s16 (octet faible'):
            pose(key, d - 1, ('s16',), src); pose(key, d, ('s16',), src); continue
        if ty.startswith('s16'):
            pose(key, d, ('s16',), src); pose(key, d + 1, ('s16',), src); continue
        if ty.startswith('s32 (partie haute)'):
            for k in range(4): pose(key, d + k, ('s32', d), src)
            continue
        if ty.startswith('s32 (partie basse)'):
            for k in range(4): pose(key, d - 2 + k, ('s32', d - 2), src)
            continue
        if ty.startswith('s32') or ty.startswith('s32 ou pointeur'):
            for k in range(4): pose(key, d + k, ('s32', d), src)
            NOTE[(key, d, sz)] = ty if 'ou' in ty else NOTE.get((key, d, sz))
            continue
        if ty.startswith('pointeur 32 bits'):
            for k in range(4): pose(key, d + k, ('ptr', d), src)
            continue
        if ty.startswith('mixte'):           # $AC : u8 $AC, u8 $AD, s16 $AE
            pose(key, d, ('u8',), src); pose(key, d + 1, ('u8',), src)
            pose(key, d + 2, ('s16',), src); pose(key, d + 3, ('s16',), src); continue
        NOTE[(key, d, sz)] = 'type non interprété : ' + ty
    # complément local (mesures de cette passe), même format de type que le TSV
    cp = os.path.join(ICI, 'types_complement.tsv')
    if os.path.exists(cp):
        for r in csv.DictReader(open(cp), delimiter='\t'):
            d = depl(r['depl_arcade']); sz = int(r['taille']); ty = r['type']
            if r['base'] == 'A5':                       # variables A5 mesurées ici (voir type_acces)
                A5C[(d, sz)] = r; continue
            if r['base'] == 'acteur' or r['base'].startswith('acteur_'):   # ACTEURS DE FIN : après la carte objet
                ACTEUR_C.append((r['base'], d, sz, ty)); continue
            key = {'objet': 'objet', "pas d'animation": 'pas'}.get(r['base'])
            if ty.startswith('jamais'):
                for k in range(sz): pose(key, d + k, ('libre',), 'complément')
            elif ty == 'u8':
                pose(key, d, ('u8',), 'complément')
            elif ty == 's16':                          # mot natif (identité), mesuré dans cette passe
                for k in range(sz): pose(key, d + k, ('s16',), 'complément')
    return OCT, A5, NOTE, LIGNE, conflits

def depl(t):
    """'$1C8' -> 0x1C8 ; '-$50FA' -> -0x50FA"""
    t = t.strip()
    return -int(t[2:], 16) if t.startswith('-$') else int(t.lstrip('$'), 16)

A5C = {}            # (d, taille) -> ligne de types_complement.tsv (base A5)
ACTEUR_C = []       # (d, taille, type) : champs des objets acteurs de fin (base acteur)
OCT, A5T, NOTE_T, LIGNE_T, CONFLITS_T = charge_types()

# Décisions propres à cette passe (justifiées dans CONV-MAX.md) -------------------------------------------------------
# $3D4 : les sources actuelles (Yun) n'y font plus de copie brute de $82.L : écriture longue d'un n° de joueur, puis
# relecture de l'octet $3D7 -> champ MAX seul, identité (TYPAGE §2 « champ MAX seul »). La ligne u8[4] du TSV visait
# l'ancien « move.l $82(a6),$3d4(a6) ».
for k in range(4): OCT['objet'][0x3D4 + k] = ('libre',)
# zone libre des structures joueur (TYPAGE §4 : aucun accès Upper en $330-$36F ni $398-$3FF)
ZONE_LIBRE = [(0x330, 0x370), (0x398, 0x400)]
# pas d'animation : format PS2 mesuré dans l'image (Ryu, pas arcade $146402 <-> image, cette session) :
# octets $0-$3 et $8-$13 = u8 (XOR 1), long $4 (image) et long $14 (reprise) = pointeurs (SWAP). Le TSV en confirme 6.
for b in list(range(0, 4)) + list(range(8, 0x14)): OCT['pas'].setdefault(b, ('u8',))
for b in range(4, 8): OCT['pas'][b] = ('ptr', 4)
for b in range(0x14, 0x18): OCT['pas'][b] = ('ptr', 0x14)
# entrée d'attaque (table $A0, 32 octets) : mesuré (Ryu, arcade $10082E <-> image) : mots $0-$7 natifs, octets $8-$1F
# échangés dans chaque mot (u8 XOR 1). Cohérent avec l'image (arcade move.b $e(a3) -> (A3+$E) XOR 1).
OCT['attaque'] = {}
for b in range(0, 8): OCT['attaque'][b] = ('s16',)
for b in range(8, 0x20): OCT['attaque'][b] = ('u8',)
# caméra de plan (A3 rendu par $1BD68) : $10.W -> image $12 (TSV « pointeur a3 », s32)
OCT['camera'] = {0x10 + k: ('s32', 0x10) for k in range(4)}
# en-tête de projectile ($60) : 5 mots relatifs lus tels quels (ADRESSES §7, $3323A)
OCT['entete'] = {b: ('s16',) for b in range(10)}

# OBJETS ACTEURS DE FIN (acteurs_fins_max.s : A6 = acteur du réservoir $1C2C8, A4 = acteur créé, A1 = acteur lié $36).
# Carte = celle des objets (TSV), dont chaque champ employé par les acteurs MAX a été recontrôlé sur le code d'acteurs
# d'Upper (arcade $A5000-$AD000 aligné : même déplacement image partout, voir CONV-MAX.md « Acteurs de fin »), plus
# les champs propres aux acteurs mesurés ici (types_complement.tsv, base « acteur »). Ces champs n'entrent PAS dans la
# carte « objet » des joueurs/projectiles ($74 y reste une union ambiguë, $78-$7F n'y sont pas typés).
OCT['acteur'] = dict(OCT['objet'])
# variantes par classe d'acteur (base « acteur_4F » : modèle « acteur » + ses lignes), employées pour le code atteint
# depuis les seules entrées de cette classe (en-tête « classe $4F sous-type … -> étiquette » d'acteurs_fins_max.s)
for _b in sorted({b for b, *_ in ACTEUR_C if b != 'acteur'}): OCT[_b] = None
for _b0, _d, _sz, _ty in sorted(ACTEUR_C, key=lambda x: x[0] != 'acteur'):
    if _b0 != 'acteur' and OCT[_b0] is None: OCT[_b0] = dict(OCT['acteur'])
    _M = OCT[_b0]
    if _ty.startswith('jamais') or _ty.startswith('libre') or _ty.startswith('MAX seul'): _c = [('libre',)] * _sz
    elif _ty.startswith('u8'): _c = [('u8',)] * _sz
    elif _ty.startswith('s16'): _c = [('s16',)] * _sz
    elif _ty.startswith('s32'): _c = [('s32', _d)] * 4
    elif _ty.startswith('pointeur'): _c = [('ptr', _d)] * 4
    elif _ty.startswith('union') or _ty.startswith('inconnu'):
        for _k in range(_sz): _M.pop(_d + _k, None)                   # non typé : NON RÉSOLU voulu
        continue
    else: raise SystemExit('types_complement.tsv : type acteur non interprété : %s' % _ty)
    for _k, _x in enumerate(_c): _M[_d + _k] = _x

NOTES_CHAMPS = {     # (base, déplacement, taille ou None = toutes)
    ('objet', 0x6C, 4): "union $6C.L (TYPAGE §3.1) : lu en u8[4] (disposition joueur ; MAX lit $6C.L du parent $36) — à confirmer",
    ('objet', 0x74, None): "union $74 (TYPAGE §3.1, ambigu) : type selon l'objet",
    ('objet', 0x22, None): "$22 : collision possible (Upper lit $22.W dans ses routines d'objets)",
    ('objet', 0x110, 4): "$110 : s32/pointeur (TYPAGE §3.2), SWAP",
    ('objet', 0xAC, 4): "$AC.L mixte : seul un test de nullité est sans risque",
}

def classe(base, b):
    o = OCT.get(base, {})
    if b in o: return o[b]
    if base == 'objet':
        for x0, x1 in ZONE_LIBRE:
            if x0 <= b < x1: return ('libre',)
    return None

class Acces:
    """accès typé : déplacement image + permutation de la valeur (registre logique <-> mémoire image)"""
    def __init__(s, d, perm, regle, ptr=None, note=None):
        s.d, s.perm, s.regle, s.ptr, s.note = d, perm, regle, ptr, note

# permutations : 'id' ; 'bsw' (mot : octets échangés) ; 'swap' (long : moitiés échangées) ;
# ('bl', b0, b1) (long : octets échangés dans le mot haut b0 / bas b1)
def type_acces(base, d, sz, mnem=''):
    """-> Acces ; lève NonResolu"""
    if base in ('tab', 'pile', 'entier'):
        return Acces(d, 'id', 'données MAX / pile : identité')
    if base == 'a5':
        c = A5C.get((d, sz))
        if c is not None:                       # mesuré dans cette passe (types_complement.tsv, base A5)
            if c['type'].startswith('inconnu'):
                raise NonResolu('variable A5 %s.%s : %s' % (hx(d), SUF[sz], c['type']))
            di = depl(c['depl_image_upper'])
            perm = 'swap' if (c['type'].startswith('s32') and sz == 4) else ('bsw' if c['type'].startswith('u8[2]') else 'id')
            return Acces(di, perm, 'A5 %s.%s -> %s (%s, complément%s)' % (hx(d), SUF[sz], hx(di), c['type'],
                         ', moitiés échangées' if perm == 'swap' else (', octets inversés' if perm == 'bsw' else '')))
        r = A5T.get((d, sz))
        if d == 0x290 and sz == 4:
            return Acces(0x290, 'swap', 'A5 $290.L caméra = s32 (moitiés échangées ; partie entière en $292)')
        if r is None:
            raise NonResolu('variable A5 %s.%s absente du typage' % (hx(d), SUF[sz]))
        if r['type'].startswith('inconnu'):
            raise NonResolu('variable A5 $%X : %s' % (d, r['type']))
        di = int(r['depl_image_upper'][1:], 16)
        return Acces(di, 'id', 'A5 $%X.%s -> $%X (%s, %s)' % (d, SUF[sz], di, r['type'], r['confiance']))
    if base not in OCT:
        raise NonResolu('base « %s » sans modèle de champs' % base)
    st = base
    if base == 'attaque_table':            # table d'attaques : entrée = d // 32
        st = 'attaque'; off = d % 32; e = d - off
    else:
        off, e = d, 0
    cl = [classe(st, off + k) for k in range(sz)]
    if any(c is None for c in cl):
        manq = [off + k for k, c in enumerate(cl) if c is None]
        nt = NOTE_T.get((st, d, sz))
        raise NonResolu('champ %s $%X.%s non typé (octets %s)%s' % (base, d, SUF[sz], ','.join('$%X' % x for x in manq),
                                                                   (' — TSV : ' + nt) if nt else ''))
    note = NOTES_CHAMPS.get((st, off, sz)) or NOTES_CHAMPS.get((st, off, None))
    if sz == 1:
        c = cl[0]
        if c[0] == 'u8': return Acces(e + (off ^ 1), 'id', '%s $%X.b u8 -> $%X' % (base, d, e + (off ^ 1)), note=note)
        if c[0] in ('s16', 'libre'): return Acces(d, 'id', '%s $%X.b %s -> inchangé' % (base, d, c[0]), note=note)
        F = c[1]; di = e + F + ((off - F) ^ 2)
        return Acces(di, 'id', '%s $%X.b octet de %s $%X -> $%X' % (base, d, c[0], F, di), note=note)
    if off & 1:
        raise NonResolu('accès %s à adresse impaire $%X (erreur d\'adresse 68000)' % (SUF[sz], d))
    def mot(c0, c1, w):
        if c0[0] == 'u8' and c1[0] == 'u8': return 'bsw'
        if c0[0] in ('s16', 'libre') and c1[0] in ('s16', 'libre') and c0[0] == c1[0]: return 'id'
        return None
    if sz == 2:
        c0, c1 = cl
        if c0[0] in ('s32', 'ptr') and c1 == c0:
            F = c0[1]
            if off == F: return Acces(e + F + 2, 'id', '%s $%X.w partie haute de %s $%X -> $%X' % (base, d, c0[0], F, e + F + 2), note=note)
            if off == F + 2: return Acces(e + F, 'id', '%s $%X.w partie basse de %s $%X -> $%X' % (base, d, c0[0], F, e + F), note=note)
        p = mot(c0, c1, off)
        if p is None: raise NonResolu('mot %s $%X à cheval sur des champs de types différents %s' % (base, d, cl))
        return Acces(d, p, '%s $%X.w %s' % (base, d, 'u8[2] : octets inversés' if p == 'bsw' else c0[0] + ' inchangé'), note=note)
    # sz == 4
    if cl[0][0] in ('s32', 'ptr') and all(c == cl[0] for c in cl):
        F = cl[0][1]
        if off != F: raise NonResolu('long %s $%X non aligné sur le champ %s $%X' % (base, d, cl[0][0], F))
        ptr = (base, F) if cl[0][0] == 'ptr' else None
        return Acces(d, 'swap', '%s $%X.l %s : moitiés échangées%s' % (base, d, cl[0][0], ' (+ CONV si adresse)' if ptr else ''), ptr=ptr, note=note)
    p0, p1 = mot(cl[0], cl[1], off), mot(cl[2], cl[3], off + 2)
    if p0 is None or p1 is None: raise NonResolu('long %s $%X à cheval sur des champs de types différents %s' % (base, d, cl))
    if p0 == 'id' and p1 == 'id': return Acces(d, 'id', '%s $%X.l %s inchangé' % (base, d, cl[0][0]), note=note)
    perm = ('bl', p0 == 'bsw', p1 == 'bsw')
    return Acces(d, perm, '%s $%X.l octets échangés dans %s' % (base, d, 'chaque mot' if perm[1] and perm[2] else ('le mot haut' if perm[1] else 'le mot bas')), note=note)

# ---- permutation d'une valeur immédiate / d'un registre
def perm_val(v, perm, sz):
    m = (1 << (8 * sz)) - 1; v &= m
    if perm == 'id': return v
    if perm == 'bsw': return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)
    if perm == 'swap': return ((v & 0xFFFF) << 16) | (v >> 16)
    _, b0, b1 = perm
    h, l = v >> 16, v & 0xFFFF
    if b0: h = ((h & 0xFF) << 8) | (h >> 8)
    if b1: l = ((l & 0xFF) << 8) | (l >> 8)
    return (h << 16) | l

def perm_expr(t, perm):
    """immédiat symbolique : expression vasm"""
    x = '(%s)' % t
    if perm == 'bsw': return '((%s&$ff)<<8)|((%s>>8)&$ff)' % (x, x)
    if perm == 'swap': return '((%s>>16)&$ffff)|((%s&$ffff)<<16)' % (x, x)
    _, b0, b1 = perm
    hi = '(((%s>>16)&$ff)<<24)|(((%s>>24)&$ff)<<16)' % (x, x) if b0 else '(%s&$ffff0000)' % x
    lo = '((%s&$ff)<<8)|((%s>>8)&$ff)' % (x, x) if b1 else '(%s&$ffff)' % x
    return '%s|%s' % (hi, lo)

def perm_code(perm, dk):
    """instructions qui appliquent la permutation (involutive) à Dk ; -> (liste, exact) ; exact = drapeaux N/Z/V/C
    finaux = ceux d'un move de la valeur logique"""
    if perm == 'id': return [], True
    if perm == 'bsw': return ['ror.w   #8, %s' % dk], False
    if perm == 'swap': return ['swap    %s' % dk], True
    _, b0, b1 = perm
    if b0 and b1: return ['ror.w   #8, %s' % dk, 'swap    %s' % dk, 'ror.w   #8, %s' % dk, 'swap    %s' % dk], True
    if b0: return ['swap    %s' % dk, 'ror.w   #8, %s' % dk, 'swap    %s' % dk], True
    return ['ror.w   #8, %s' % dk], False

# ============================================================================================ adresses du moteur
def charge_carte(carte):
    va2img = {}
    n = 0
    for l in open(carte, errors='replace'):
        p = l.split(None, 2)
        if len(p) < 2: continue
        try: a = int(p[0], 16); v = int(p[1], 16)
        except ValueError: continue
        n += 1
        va2img.setdefault(v, (a, p[2].strip() if len(p) > 2 else ''))
    return va2img, n

def charge_corr():
    C = {}
    for r in csv.DictReader(open(CORR), delimiter='\t'):
        a = int(r['arcade'][1:], 16)
        C[a] = dict(nom=r['nom'], va=r['va_mips_instr'], statut=r['statut'], remarque=r['remarque'],
                    ancien=r['upper_68k'], source='correspondances.tsv')
    for r in csv.DictReader(open(COMPL), delimiter='\t'):
        a = int(r['arcade'][1:], 16)
        if a not in C:
            C[a] = dict(nom=r['nom'], va=r['va_mips_instr'], statut=r['statut'], remarque=r.get('remarque') or r['source'], ancien='-',
                        source='complément : ' + r['source'][:80])
    return C

def charge_image(roms):
    try:
        img = bytearray()
        for f in ROM_FICHIERS:
            d = open(os.path.join(roms, f), 'rb').read()
            img += bytes(x for i in range(0, len(d), 2) for x in (d[i + 1], d[i]))
        return bytes(img)
    except OSError:
        return None

def trouve_conv(img):
    """adresses des routines CONV_An (A0..A6) : « MOVE SR,-(A7) ; CMPA.L #$60ACC0,An » au début de l'image"""
    R = {}
    if img is None: return R
    for n in range(7):
        motif = bytes([0x40, 0xE7, 0xB1 | (n << 1), 0xFC, 0x00, 0x60, 0xAC, 0xC0])
        p = img.find(motif, 0, 0x10000)
        if p >= 0: R['a%d' % n] = p
    return R

# ============================================================================================ analyse syntaxique
class Ins:
    def __init__(s, fichier, num, texte):
        s.fichier, s.num, s.texte = fichier, num, texte
        s.labels = []; s.mn = None; s.sz = None; s.ops = []; s.com = ''; s.directive = False
        s.equ = False

RX_LAB = re.compile(r'^([A-Za-z_.][\w.]*)(:?)')
def analyse_ligne(fichier, num, texte, glob):
    ins = Ins(fichier, num, texte)
    t = texte.rstrip('\n')
    i = t.find(';')
    corps, ins.com = (t[:i], t[i:]) if i >= 0 else (t, '')
    if corps.startswith('*'): return ins, glob
    if corps and not corps[0].isspace():
        m = RX_LAB.match(corps)
        if m:
            nom = m.group(1); reste = corps[m.end():]
            if re.match(r'\s+equ\b', reste, re.I) or re.match(r'\s*=', reste):
                ins.equ = True; ins.labels = [nom]; return ins, glob
            if nom.startswith('.'): nom = glob + nom
            else: glob = nom
            ins.labels.append(nom); corps = ' ' + reste
    corps = corps.strip()
    if not corps: return ins, glob
    p = corps.split(None, 1)
    mn = p[0].lower(); ops = p[1] if len(p) > 1 else ''
    if '.' in mn and not mn.startswith('.'):
        mn, s = mn.rsplit('.', 1)
        ins.sz = TAILLE.get(s, None) if s != 's' else 's'
    ins.mn = mn
    ins.ops = split_ops(ops) if mn not in ('dc', 'dcb', 'ds') else [ops.strip()]
    ins.directive = mn in ('dc', 'dcb', 'ds', 'even', 'align', 'org', 'cnop', 'section', 'include', 'incbin')
    ins.glob = glob
    return ins, glob

class EA:
    def __init__(s, t):
        s.t = t.strip(); tl = s.t.lower(); s.mode = 'autre'; s.reg = None; s.disp = None; s.dtxt = ''; s.idx = None
        s.imm = None
        if re.fullmatch(r'd[0-7]', tl): s.mode, s.reg = 'dn', tl; return
        if re.fullmatch(r'a[0-7]|sp', tl): s.mode, s.reg = 'an', ('a7' if tl == 'sp' else tl); return
        if tl in ('sr', 'ccr', 'usp'): s.mode = tl; return
        if tl.startswith('#'): s.mode = 'imm'; s.imm = s.t[1:].strip(); return
        m = re.fullmatch(r'-\((a[0-7]|sp)\)', tl)
        if m: s.mode, s.reg = 'predec', ('a7' if m.group(1) == 'sp' else m.group(1)); return
        m = re.fullmatch(r'\((a[0-7]|sp)\)\+', tl)
        if m: s.mode, s.reg = 'postinc', ('a7' if m.group(1) == 'sp' else m.group(1)); return
        m = re.fullmatch(r'(.*?)\(\s*(a[0-7]|sp|pc)\s*(?:,\s*([ad][0-7]|sp)(?:\.([wl]))?\s*)?\)', s.t, re.I)
        if m:
            r = m.group(2).lower(); r = 'a7' if r == 'sp' else r
            s.dtxt = m.group(1).strip(); s.disp = num(s.dtxt) if s.dtxt else 0
            s.reg = r
            if m.group(3):
                s.idx = (m.group(3).lower(), (m.group(4) or 'w').lower())
                s.mode = 'pcidx' if r == 'pc' else 'idx'
            else:
                s.mode = 'pcdisp' if r == 'pc' else ('ind' if not s.dtxt else 'disp')
            return
        if re.fullmatch(r'([ad][0-7]|sp)(-([ad][0-7]))?(/([ad][0-7]|sp)(-([ad][0-7]))?)*', tl):
            s.mode = 'liste'; return
        s.mode = 'abs'
    @property
    def mem(s):
        return s.mode in ('ind', 'disp', 'idx', 'predec', 'postinc', 'abs')
    def regs(s):
        r = set()
        if s.reg: r.add(s.reg)
        if s.idx: r.add('a7' if s.idx[0] == 'sp' else s.idx[0])
        return r

def ea_txt(base_reg, d):
    return '%s(%s)' % (hx(d), 'sp' if base_reg == 'a7' else base_reg)

# ============================================================================================ drapeaux
COND = {'eq': 'Z', 'ne': 'Z', 'mi': 'N', 'pl': 'N', 'vs': 'V', 'vc': 'V', 'cs': 'C', 'cc': 'C', 'lo': 'C', 'hs': 'C',
        'hi': 'CZ', 'ls': 'CZ', 'ge': 'NV', 'lt': 'NV', 'gt': 'NVZ', 'le': 'NVZ', 't': '', 'f': '', 'ra': ''}
POSE_DRAPEAUX = {'move', 'moveq', 'add', 'addi', 'addq', 'sub', 'subi', 'subq', 'and', 'andi', 'or', 'ori', 'eor',
                 'eori', 'cmp', 'cmpi', 'cmpa', 'cmpm', 'tst', 'clr', 'neg', 'not', 'ext', 'swap', 'muls', 'mulu',
                 'divs', 'divu', 'asl', 'asr', 'lsl', 'lsr', 'rol', 'ror', 'tas', 'chk'}

def drapeaux_utilises(code, i, labels_idx, prof=0, vus=None):
    """drapeaux lus après l'instruction i (avant d'être reposés) : chaîne de 'NZVCX' ; parcours linéaire + sauts
    inconditionnels locaux ; un RTS = tous (convention « retour D0 + drapeaux »)"""
    if vus is None: vus = set()
    used = set(); vivant = set('NZVCX')
    j = i + 1
    while j < len(code) and prof < 6:
        if j in vus: return used
        vus.add(j)
        ins = code[j]; mn = ins.mn
        if mn is None or ins.directive and mn != 'dc':
            j += 1; continue
        if mn == 'dc': return used | vivant          # données en ligne : on ne sait pas
        if mn in ('rts', 'rte', 'rtr'): return used | vivant
        if mn in ('bsr', 'jsr'): return used
        if mn.startswith('b') and mn[1:] in COND and mn not in ('bset', 'bclr', 'bchg', 'btst'):
            c = mn[1:]
            used |= set(COND[c]) & vivant
            if c == 'ra':
                cible = ins.ops[0] if ins.ops else ''
                k = labels_idx.get(_scope(cible, ins))
                if k is None: return used | vivant
                j = k; prof += 1; continue
            # conditionnel : les deux chemins
            cible = ins.ops[0] if ins.ops else ''
            k = labels_idx.get(_scope(cible, ins))
            if k is None: used |= vivant
            else: used |= drapeaux_utilises(code, k - 1, labels_idx, prof + 1, vus) & vivant
            j += 1; continue
        if mn == 'jmp': return used | (vivant if not ins.ops[0].startswith('$') else set())
        if mn.startswith('db'):
            used |= set(COND.get(mn[2:], 'NZVC')) & vivant; j += 1; continue
        if mn.startswith('s') and mn[1:] in COND:
            used |= set(COND[mn[1:]]) & vivant; j += 1; continue
        if mn in ('addx', 'subx', 'negx', 'roxl', 'roxr', 'abcd', 'sbcd', 'nbcd'):
            used |= {'X'} & vivant
        if mn == 'move' and ins.ops and ins.ops[0].lower() == 'sr': return used | vivant
        if mn in ('btst', 'bset', 'bclr', 'bchg'):
            vivant.discard('Z')
        elif mn in POSE_DRAPEAUX:
            if mn in ('cmp', 'cmpi', 'cmpa', 'cmpm', 'tst', 'move', 'moveq', 'clr', 'and', 'andi', 'or', 'ori', 'eor',
                      'eori', 'not', 'ext', 'swap', 'muls', 'mulu', 'divs', 'divu'):
                vivant -= set('NZVC')
            else:
                vivant -= set('NZVCX')
            if mn == 'move' and ins.ops and len(ins.ops) == 2 and ins.ops[1].lower() in ('ccr', 'sr'):
                vivant -= set('NZVCX')
        if not vivant: return used
        j += 1
    return used

def _scope(nom, ins):
    nom = nom.strip()
    if nom.startswith('.'): return getattr(ins, 'glob', '') + nom
    return nom

# ============================================================================================ genres des registres
REGS = ['d%d' % i for i in range(8)] + ['a%d' % i for i in range(8)]
INCONNU = ('inconnu',)
def etat_entree():
    e = {r: INCONNU for r in REGS}
    e['a5'] = ('a5',); e['a6'] = ('objet',); e['a7'] = ('pile',)
    return e

def meet1(x, y):
    if x == y: return x
    if x[0] == y[0] and x[0] in ('objet_plus', 'ps2', 'donnee') and x[:-1] == y[:-1]:
        return x[:-1] + (None,)                     # même genre, décalage différent -> décalage inconnu
    return INCONNU

def meet(a, b):
    if a is None: return dict(b)
    if b is None: return dict(a)
    return {r: meet1(a[r], b[r]) for r in REGS}

LOCALES = ('L_', 'T_', 'AL_', 'AT_')       # étiquettes locales (cibles de branchement) : pas des entrées de fonction
ALLOC = {0x1C1C8, 0x1C2C8, 0x1C2DE, 0x1C368, 0x1C37E, 0x1C278, 0x1C28E, 0x1C318, 0x1C32E, 0x1C3AC, 0x1C3C2}
CAMERA = {0x1BD68, 0x1BD5C}
# fonctions MAX écrites à la main (acteurs_fins_main.s) : registres modifiés et genre rendu, d'après leur en-tête
# (« Seul A0 change », « Seul D7 change ») ; vérifié à la lecture du code (2026-10-10)
APPELS_MAX = {'fin_t12c': ({'a0'}, {'a0': ('tab',)}),          # A0 = enregistrements FIN_T12C_xx (données MAX)
              'fin_pas110': ({'d7'}, {}), 'fin_pas118': ({'d7'}, {}), 'fin_pos_4f05': ({'d7'}, {})}
# zones de la structure joueur effacées en bloc (clr.l (An)+) : invariant si aucun champ de l'image ne franchit leurs
# bornes — vérifié (paires_recs.pkl : aucun accès aligné à cheval ni déplacé hors de sa zone ; MIPS ro5 : aucun accès
# hôte à cheval) pour $180-$1CF et $1D8-$1EF (fiches de manipulation, psp_1b9544 ; $1D0-$1D7 : champs d'Upper exclus)
ZONES_RAZ = [(0x180, 0x1D0), (0x1D8, 0x1F0)]
RETOUR_A0_OBJET = {0x2E8C0}
CHAMP_PTR_STRUCT = {0x1C: 'pas', 0x60: 'entete', 0x88: 'boites', 0xA0: 'attaque_table'}
CHAMPS_TABLES_MAX = {0x34A: 'table de sauts PSP (TAB_SAUT_PSP_*, posée par psp_1b3668)'}

def charge_forcees():
    F = defaultdict(dict)
    if os.path.exists(FORCEES):
        for r in csv.DictReader(open(FORCEES), delimiter='\t'):
            g = tuple(x for x in r['genre'].split(':'))
            if g[0] in ('ps2', 'donnee'): g = (g[0], g[1], int(g[2]) if len(g) > 2 and g[2] not in ('', '?') else None)
            elif len(g) == 1: g = (g[0],)
            F[r['etiquette']][r['registre']] = (g, r['justification'])
    return F

# ============================================================================================ conversion d'un fichier
class Convertisseur:
    def __init__(s, args):
        s.args = args
        s.journal = []; s.stats = Counter(); s.adresses = {}     # arcade -> info résolue
        s.va2img, s.n_carte = charge_carte(args.carte)
        s.corr = charge_corr()
        s.img = None if args.sans_image else charge_image(args.roms)
        s.conv = trouve_conv(s.img)
        s.forcees = charge_forcees()
        s.feuilles = {}
        s.modele_objet = 'objet'; s.modele_ins = 'objet'
        for n in range(7):
            s.conv.setdefault('a%d' % n, None)

    # ---------------------------------------------------------------- journal
    def log(s, ins, statut, regle, orig, nouv=''):
        s.journal.append((ins.fichier, ins.num, statut, regle, orig.strip(), nouv))
        s.stats[statut] += 1

    # ---------------------------------------------------------------- résolution d'une adresse du moteur
    def resout(s, a):
        if a in s.adresses: return s.adresses[a]
        c = s.corr.get(a)
        r = dict(arcade=a, ok=False)
        if c is None:
            r['raison'] = 'adresse arcade $%X absente des correspondances' % a
        elif c['va'] in ('-', ''):
            r['raison'] = 'absente d\'Upper (%s) : %s' % (c['statut'], c['remarque'][:120])
        else:
            va = int(c['va'], 16)
            t = s.va2img.get(va)
            if t is None:
                r['raison'] = 'va 0x%x introuvable dans la carte actuelle' % va
            else:
                r.update(ok=True, va=va, img=t[0], texte=t[1], statut=c['statut'], nom=c['nom'], source=c['source'],
                         remarque=c['remarque'], ancien=c['ancien'])
        s.adresses[a] = r
        return r

    def sym(s, a):
        return 'UP_%05X' % a

    # ---------------------------------------------------------------- flux des genres de registres
    def flux(s, code, labels_idx, entrees):
        n = len(code)
        etat = [None] * n
        travail = list(range(n))
        preds_br = defaultdict(list)            # cible -> [(i)]
        for i, ins in enumerate(code):
            if ins.mn and (ins.mn.startswith('b') and ins.mn[1:] in COND or ins.mn.startswith('db')) \
                    and ins.mn not in ('bsr',) and ins.ops:
                k = labels_idx.get(_scope(ins.ops[-1], ins))
                if k is not None: preds_br[k].append(i)
        sortie = [None] * n
        def entree(i):
            ins = code[i]
            st = None
            if i > 0 and not s.terminal(code[i - 1]) and sortie[i - 1] is not None: st = meet(st, sortie[i - 1])
            for p in preds_br.get(i, []):
                if sortie[p] is not None: st = meet(st, sortie[p])
            if any(l in entrees for l in ins.labels) or i == 0:
                st = meet(st, etat_entree()) if st is not None else etat_entree()
            if st is not None:
                for l in ins.labels + ['%s:%d' % (ins.fichier, ins.num)]:
                    for r, (g, j) in s.forcees.get(l, {}).items(): st[r] = g
            return st
        for _ in range(30):
            change = False
            for i in range(n):
                st = entree(i)
                if st is None: continue
                if etat[i] != st:
                    etat[i] = st; change = True
                sortie[i] = s.transfert(code[i], dict(st))
            if not change: break
        return etat

    @staticmethod
    def terminal(ins):
        return ins.mn in ('bra', 'jmp', 'rts', 'rte', 'rtr')

    def genre_ea_lu(s, ins, ea, st, taille):
        """genre de la valeur lue (pour movea/move.l vers un registre)"""
        if ea.mode in ('dn', 'an') and st[ea.reg][0] == 'objet_plus':
            return st[ea.reg]                       # adresse calculée objet + k : l'annotation ne suffit pas
        if 'pointeur d\'objet' in ins.com: return ('objet',)
        if ea.mode == 'an' or ea.mode == 'dn': return st[ea.reg]
        if ea.mode == 'imm':
            v = num(ea.imm)
            if v is None: return ('tab',)
            if 0xFF8000 <= v < 0xFFA000: return ('objet',)
            return ('const', v)
        if ea.mode == 'abs':
            return ('tab',) if num(ea.t.split('.')[0]) is None else INCONNU
        if ea.mode in ('disp', 'ind') :
            b = st.get(ea.reg, INCONNU)[0]
            d = ea.disp or 0
            if b == 'objet' and taille == 2: return ('objet',)            # pointeur mot vers un objet
            if b == 'objet' and taille == 4:
                if d in CHAMP_PTR_STRUCT: return ('ps2', CHAMP_PTR_STRUCT[d], 0)
                if d in CHAMPS_TABLES_MAX: return ('tab',)
            if b == 'tab': return ('tab',)
            return INCONNU
        if ea.mode in ('idx', 'pcidx', 'pcdisp'):
            b = 'tab' if ea.mode != 'idx' else st.get(ea.reg, INCONNU)[0]
            return ('tab',) if b == 'tab' else INCONNU
        return INCONNU

    def transfert(s, ins, st):
        mn = ins.mn
        if mn is None or ins.directive: return st
        ops = [EA(o) for o in ins.ops] if mn not in ('dc', 'dcb') else []
        sz = ins.sz if isinstance(ins.sz, int) else None
        dst = ops[-1] if ops else None
        def ecrit(r, g): st[r] = g
        if mn in ('bsr', 'jsr'):
            cible = ins.ops[0] if ins.ops else ''
            a = num(cible.split('.')[0]) if cible.startswith('$') else None
            if a in ALLOC:                      # arcade $1C1C8… : seuls A0 et A4 changent (désassemblage)
                for r in ['d%d' % i for i in range(8)] + ['a0']: st[r] = INCONNU
                st['a4'] = ('objet',); return st
            if cible.strip() in APPELS_MAX:
                ecr, rend = APPELS_MAX[cible.strip()]
                for r in ecr: st[r] = rend.get(r, INCONNU)
                return st
            feuille = s.feuilles.get(cible.strip())
            if feuille is not None:             # fonction MAX feuille : seuls ses registres écrits changent
                for r in feuille: st[r] = INCONNU
                return st
            for r in ['d%d' % i for i in range(8)] + ['a0', 'a1', 'a2', 'a3']: st[r] = INCONNU
            if a in CAMERA: st['a3'] = ('camera',)
            if a in RETOUR_A0_OBJET: st['a0'] = ('objet',)
            return st
        if mn in ('movea', 'move') and dst is not None and dst.mode == 'an' and dst.reg == 'a6' \
                and ops[0].mode == 'postinc' and ops[0].reg == 'a7':
            # (2b20) traduire.py (64f79e3) : appel sur un AUTRE objet = move.l a6,-(sp) / movea.l <objet>,a6 / jsr / movea.l
            # (sp)+,a6 -> A6 restauré = l'objet courant
            ecrit('a6', ('objet',)); return st
        if mn in ('movea', 'move') and dst is not None and dst.mode == 'an':
            g = s.genre_ea_lu(ins, ops[0], st, sz or 2)
            if g[0] == 'ps2': g = ('donnee', g[1], g[2])           # CONV inséré par la réécriture
            ecrit(dst.reg, g); return st
        if mn == 'lea' and dst is not None:
            src = ops[0]
            if 'pointeur d\'objet' in ins.com: g = ('objet',)
            elif src.mode in ('pcdisp', 'abs'):
                v = num(src.t)
                g = ('objet',) if v is not None and 0xFF8000 <= v < 0xFFA000 else ('tab',)
                if src.mode == 'abs' and v is not None and not (0xFF8000 <= v < 0xFFA000): g = INCONNU
            elif src.mode == 'disp':
                b = st[src.reg]
                if b[0] in ('a5', 'objet') and src.disp is not None and src.disp % 0x400 == 0 and src.disp != 0:
                    g = ('objet',)
                elif b[0] in ('objet', 'fiche_psp') and src.disp == -0x1d0: g = ('fiche',)
                elif b[0] == 'fiche' and src.disp is not None and src.disp % 0x10 == 0: g = ('fiche',)
                elif b[0] == 'objet' and s.modele_objet == 'acteur' and src.disp is not None and src.disp % 0x80 == 0 \
                        and src.disp != 0: g = ('objet',)                    # acteur suivant (objets de $80 o)
                elif b[0] == 'objet' and src.disp is not None and any(a <= src.disp < z for a, z in ZONES_RAZ):
                    g = ('raz', src.disp)
                elif b[0] in ('tab', 'pile'): g = b
                else: g = INCONNU
            elif src.mode == 'pcidx': g = ('tab',)
            elif src.mode == 'idx': g = ('tab',) if st[src.reg][0] == 'tab' else INCONNU
            else: g = INCONNU
            ecrit(dst.reg, g); return st
        if mn in ('adda', 'suba') and dst is not None and dst.mode == 'an':
            b = st[dst.reg]
            if b[0] == 'tab': return st
            if b[0] == 'donnee' and ops[0].mode == 'imm' and num(ops[0].imm) is not None and b[2] is not None:
                k = num(ops[0].imm) * (1 if mn == 'adda' else -1)
                ecrit(dst.reg, ('donnee', b[1], b[2] + k)); return st
            ecrit(dst.reg, INCONNU if b[0] != 'pile' else b); return st
        if mn == 'exg':
            a, b = ops[0].reg, ops[1].reg
            st[a], st[b] = st[b], st[a]; return st
        if mn == 'movem':
            if ops and ops[-1].mode == 'liste':
                for r in s.liste_regs(ops[-1].t): st[r] = INCONNU
            return st
        if dst is not None and dst.mode == 'dn' and mn not in ('cmp', 'cmpi', 'cmpa', 'tst', 'btst', 'chk'):
            r = dst.reg
            if mn == 'move' and sz == 4:
                g = s.genre_ea_lu(ins, ops[0], st, 4)
                ecrit(r, g if g[0] in ('objet', 'tab', 'ps2', 'donnee', 'objet_plus', 'const') else INCONNU); return st
            if mn == 'moveq' or (mn == 'move' and ops[0].mode == 'imm' and sz == 4):
                v = num(ops[0].imm)
                ecrit(r, ('const', v) if v is not None else ('tab',)); return st
            if mn in ('addi', 'addq', 'subi', 'subq', 'add', 'sub') and sz == 4 and ops[0].mode == 'imm':
                v = num(ops[0].imm)
                if v is not None and st[r][0] == 'ps2' and st[r][2] is not None:
                    k = v if mn.startswith('add') else -v
                    ecrit(r, ('ps2', st[r][1], st[r][2] + k)); return st
                if v == 0xFF8400 and mn in ('addi', 'add'):
                    ecrit(r, ('objet',)); return st
                if v is not None and st[r][0] in ('objet', 'objet_plus'):
                    k0 = 0 if st[r][0] == 'objet' else st[r][1]
                    k = None if k0 is None else k0 + (v if mn.startswith('add') else -v)
                    ecrit(r, ('objet',) if k is not None and k % 0x400 == 0 else ('objet_plus', k)); return st
            ecrit(r, INCONNU); return st
        if mn in ('swap', 'ext') and ops and ops[0].mode == 'dn':
            st[ops[0].reg] = INCONNU
        return st

    def classes_acteurs(s, code, labels_idx):
        """instructions atteintes UNIQUEMENT depuis les entrées d'une classe qui a un modèle propre (OCT['acteur_4F']…) ->
        nom du modèle. Entrées lues dans l'en-tête « ; classe $4F sous-type $19 -> acteur_1d6588 ». Graphe : suite,
        branchements, bsr/jsr/bra/jmp vers une étiquette, tables dc.l citées par lea."""
        racines = defaultdict(set)
        for ins in code[:60]:
            m = re.match(r';\s*classe \$([0-9A-Fa-f]+) sous-type \$[0-9A-Fa-f]+ -> (\w+)', ins.texte.strip())
            if m: racines['acteur_%s' % m.group(1).upper()].add(m.group(2))
        def succ(i):
            ins = code[i]; out = []
            if ins.mn is None or ins.directive and ins.mn != 'dc':
                return [i + 1] if i + 1 < len(code) else []
            if i + 1 < len(code) and ((not s.terminal(ins) and ins.mn != 'dc') or (ins.mn == 'dc' and code[i + 1].mn == 'dc')):
                out.append(i + 1)                                   # une table dc.l continue sur la ligne suivante
            for o in ins.ops if ins.mn != 'dc' else split_ops(ins.ops[0]):
                for mm in re.finditer(r'[A-Za-z_][\w.]*', o):
                    k = labels_idx.get(mm.group(0)) or labels_idx.get(_scope(mm.group(0), ins))
                    if k is not None: out.append(k)
            return out
        def atteint(rs):
            vu = set(); pile = [labels_idx[r] for r in rs if r in labels_idx]
            while pile:
                i = pile.pop()
                if i in vu: continue
                vu.add(i); pile.extend(succ(i))
            return vu
        par = {c: atteint(rs) for c, rs in racines.items()}
        res = {}
        for c, vu in par.items():
            if c not in OCT: continue
            autres = set().union(*[v for c2, v in par.items() if c2 != c]) if len(par) > 1 else set()
            for i in vu - autres: res[i] = c
        return res

    def verifie_raz(s, code, i, d):
        """lea d(objet),An ; moveq #n,Dk ; .x: clr.l (An)+ ; dbra Dk,.x  : la boucle doit rester dans sa zone"""
        z = [(a, b) for a, b in ZONES_RAZ if a <= d < b][0]
        suite = [x for x in code[i + 1:i + 6] if x.mn][:3]
        if len(suite) == 3 and suite[0].mn == 'moveq' and suite[1].mn == 'clr' and suite[1].sz == 4 \
                and suite[2].mn == 'dbra':
            n = num(suite[0].ops[0].lstrip('#'))
            if n is not None and d + 4 * (n + 1) <= z[1]: return
            raise NonResolu('effacement $%X + %s longs : sort de la zone $%X-$%X' % (d, n + 1 if n is not None else '?', z[0], z[1]))
        raise NonResolu('lea dans une zone d\'effacement sans boucle « moveq ; clr.l (An)+ ; dbra » reconnue')

    @staticmethod
    def liste_regs(t):
        out = []
        for p in t.lower().replace('sp', 'a7').split('/'):
            if '-' in p:
                a, b = p.split('-')
                for i in range(int(a[1]), int(b[1]) + 1): out.append(a[0] + str(i))
            else: out.append(p)
        return out

    # ---------------------------------------------------------------- base d'un opérande mémoire
    def base_de(s, ea, st):
        g = st.get(ea.reg, INCONNU) if ea.reg else INCONNU
        if ea.mode in ('pcdisp', 'pcidx'): return ('tab',)
        return g

    def acces_de(s, ea, st, taille, mn):
        """-> (Acces) pour un opérande mémoire ; lève NonResolu"""
        if ea.mode == 'abs':
            v = num(re.sub(r'\.[wl]$', '', ea.t, flags=re.I))
            if v is None: return Acces(None, 'id', 'adresse absolue symbolique (données MAX) : identité')
            if 0xFF8000 <= v <= 0xFFFFFF or 0xFFFF8000 <= v:
                raise NonResolu('accès absolu à la RAM $%X : non typé' % v)
            return Acces(None, 'id', 'adresse absolue $%X : identité' % v)
        g = s.base_de(ea, st)
        b = g[0]
        if b in ('tab', 'pile', 'entier', 'const'):
            return Acces(None, 'id', 'base %s : identité' % b)
        if b == 'raz':
            if mn != 'clr': raise NonResolu('zone d\'effacement : seule l\'écriture de zéros est invariante (%s)' % mn)
            return Acces(None, 'id', 'effacement à zéro d\'une zone fermée de la structure joueur (invariant)')
        if ea.mode in ('predec', 'postinc'):
            raise NonResolu('(An)+ / -(An) sur une base %s typée' % b)
        if ea.mode == 'idx':
            raise NonResolu('accès indexé sur une base %s (déplacement variable)' % b)
        if ea.disp is None:
            raise NonResolu('déplacement symbolique « %s » sur une base %s' % (ea.dtxt, b))
        d = ea.disp
        if b == 'objet':
            m = s.modele_ins if (s.modele_ins == s.modele_objet or ea.reg == 'a6') else s.modele_objet
            return type_acces(m, d, taille, mn)
        if b == 'a5': return type_acces('a5', d, taille, mn)
        if b == 'camera': return type_acces('camera', d, taille, mn)
        if b == 'donnee':
            struct_, off = g[1], g[2]
            if off is None: raise NonResolu('pointeur de données %s à décalage inconnu' % struct_)
            if struct_ == 'pas': return type_acces('pas', off + d, taille, mn)
            if struct_ == 'attaque_table': return type_acces('attaque_table', off + d, taille, mn)
            if struct_ == 'attaque': return type_acces('attaque', off + d, taille, mn)
            if struct_ == 'entete': return type_acces('entete', off + d, taille, mn)
            raise NonResolu('données « %s » (format PS2 non mesuré)' % struct_)
        if b == 'fiche': raise NonResolu('fiche de manipulation (A4 = objet + $180) : format non typé')
        if b == 'objet_plus':
            raise NonResolu('base = adresse calculée objet + %s (annotée « pointeur d\'objet » par traduire.py, mais ce '
                            'n\'est pas le début d\'un objet)' % (hx(g[1]) if g[1] is not None else '?'))
        raise NonResolu('registre %s de genre inconnu (base non déterminée)' % ea.reg)

    # ---------------------------------------------------------------- réécriture
    def choisit_dk(s, *eas, evite=()):
        occupes = set(evite)
        for e in eas:
            if e is not None: occupes |= e.regs()
        for k in ('d7', 'd6', 'd5', 'd4', 'd3', 'd2', 'd1', 'd0'):
            if k not in occupes: return k
        raise NonResolu('aucun registre de travail libre')

    @staticmethod
    def txt_mem(ea, acc, decal_pile=0):
        """texte de l'opérande mémoire converti (décalage de pile si des registres ont été empilés)"""
        if acc is not None and acc.d is not None:
            return ea_txt(ea.reg, acc.d)
        if decal_pile and ea.reg == 'a7' and ea.mode in ('disp', 'ind', 'idx'):
            if ea.mode == 'idx': raise NonResolu('opérande indexé sur la pile dans une séquence qui empile')
            return ea_txt('a7', (ea.disp or 0) + decal_pile)
        if decal_pile and ea.mode in ('predec', 'postinc') and ea.reg == 'a7':
            raise NonResolu('opérande -(sp)/(sp)+ dans une séquence qui empile')
        return ea.t

    def calcule_feuilles(s, sources, fichiers):
        """fonctions MAX « feuilles » (ligne droite jusqu'au RTS, sans appel ni saut) -> registres qu'elles écrivent"""
        for f in fichiers:
            glob = ''; cour = None; ecr = set()
            for k, l in enumerate(open(os.path.join(sources, f), errors='replace'), 1):
                ins, glob = analyse_ligne(f, k, l, glob)
                if ins.labels and not ins.equ and not ins.labels[0].startswith(('L_', 'T_')) and '.' not in ins.labels[0]:
                    if cour is None or ins.mn is not None or True:
                        cour = [x for x in ins.labels]; ecr = set()
                if cour is None or ins.mn is None: continue
                mn = ins.mn
                if mn == 'rts':
                    for x in cour: s.feuilles[x] = set(ecr)
                    cour = None; continue
                if ins.directive or mn in ('bsr', 'jsr', 'jmp', 'bra', 'rte') or (mn.startswith('b') and mn[1:] in COND) \
                        or mn.startswith('db'):
                    cour = None; continue
                ops = [EA(o) for o in ins.ops]
                if mn in ('cmp', 'cmpi', 'cmpa', 'tst', 'btst'): pass
                elif mn == 'exg': ecr |= {ops[0].reg, ops[1].reg}
                elif mn == 'movem' and ops[-1].mode == 'liste': ecr |= set(s.liste_regs(ops[-1].t))
                elif ops and ops[-1].mode in ('dn', 'an'): ecr.add(ops[-1].reg)
                elif mn in ('swap', 'ext') and ops: ecr.add(ops[0].reg)
                for o in ops:
                    if o.mode in ('predec', 'postinc') and o.reg != 'a7': ecr.add(o.reg)
        s.feuilles = {k: {r for r in v if r != 'a7'} for k, v in s.feuilles.items()}

    def convertit_fichier(s, nom, lignes):
        s.modele_objet = 'acteur' if nom in FICHIERS_ACTEURS else 'objet'
        code = []; glob = ''
        for k, l in enumerate(lignes, 1):
            ins, glob = analyse_ligne(nom, k, l, glob)
            ins.glob = glob
            code.append(ins)
        labels_idx = {}
        for i, ins in enumerate(code):
            for lb in ins.labels: labels_idx[lb] = i
        # étiquettes d'entrée : globales (non L_ et non locales) + toute étiquette citée hors branchement
        cites = set()
        for ins in code:
            if ins.mn in ('dc',) or ins.mn in ('bsr', 'jsr', 'lea', 'pea', 'jmp', 'move', 'movea'):
                for o in ins.ops:
                    for m in re.finditer(r'[A-Za-z_][\w]*', o): cites.add(m.group(0))
        # AL_/AT_ (acteurs_fins_max.s) = étiquettes locales de branchement de traduire.py (comme L_/T_) : pas des entrées
        entrees = set(l for l in labels_idx if not l.startswith(LOCALES) and '.' not in l) | (cites & set(labels_idx))
        etat = s.flux(code, labels_idx, entrees)
        classe_ins = s.classes_acteurs(code, labels_idx) if nom in FICHIERS_ACTEURS else {}
        sortie = []
        for i, ins in enumerate(code):
            st = etat[i] or etat_entree()
            s.modele_ins = classe_ins.get(i, s.modele_objet)
            try:
                nouv = s.reecrit(ins, st, code, i, labels_idx)
            except NonResolu as e:
                s.log(ins, 'NON RÉSOLU', str(e), ins.texte); nouv = None
                sortie.append(ins.texte.rstrip('\n') + ('  ' if ins.com else '  ; ') + '⚠ CONV NON RÉSOLU : ' + str(e))
                continue
            if nouv is None:
                sortie.append(ins.texte.rstrip('\n'))
            else:
                sortie.extend(nouv)
        return s.peephole(sortie)

    def peephole(s, L):
        """« swap Dn » (fin d'une lecture) immédiatement suivi de « swap Dn » (début d'une écriture) puis d'un MOVE vers
        la mémoire : les deux SWAP s'annulent et le MOVE repose N/Z/V/C -> supprimés (forme compacte de l'image)."""
        out = []; i = 0
        rx = re.compile(r'^\s+swap\s+(d[0-7])\s*(;.*)?$')
        while i < len(L):
            m1 = rx.match(L[i]); m2 = rx.match(L[i + 1]) if i + 1 < len(L) else None
            if m1 and m2 and m1.group(1) == m2.group(1) and i + 2 < len(L) and \
                    re.match(r'^\s+move\.[bwl]\s+%s,' % m1.group(1), L[i + 2]):
                com = ' '.join(x for x in (m1.group(2), m2.group(2)) if x)
                out.append(L[i + 2] + ('   ' + com + ' [2 SWAP annulés]' if com else '')); i += 3
                s.stats['swap_annules'] += 1
                continue
            out.append(L[i]); i += 1
        return out

    def prefixe(s, ins):
        """étiquette(s) de la ligne d'origine, à remettre sur la 1re ligne émise"""
        t = ins.texte
        if t and not t[0].isspace() and not t.startswith(';') and ins.labels:
            m = RX_LAB.match(t)
            return m.group(0)
        return ''

    def emet(s, ins, lignes, regle, statut='réécrit'):
        """remplace l'instruction par `lignes` (sans indentation) ; l'original est gardé en commentaire"""
        pre = s.prefixe(ins)
        out = []
        orig = ins.texte.strip()
        if pre: orig = orig[len(pre):].strip()
        com = ins.com.strip()
        for k, l in enumerate(lignes):
            lab = (pre if k == 0 else '')
            if k == 0 and lab:
                out.append(lab)
            c = ''
            if k == 0: c = '   ; conv : %s | arcade : %s%s' % (regle, orig.split(';')[0].strip(), ('   ' + com) if com else '')
            out.append(('        %-40s%s' % (l, c)).rstrip())
        s.log(ins, statut, regle, ins.texte, ' ; '.join(lignes))
        return out

    def reecrit(s, ins, st, code, i, labels_idx):
        mn = ins.mn
        if mn is None or ins.equ: return None
        if mn == 'dc':
            return s.reecrit_dc(ins)
        if ins.directive: return None
        ops = [EA(o) for o in ins.ops]
        # ---- appels / sauts vers le moteur arcade
        if mn in ('jsr', 'jmp', 'bsr', 'bra') and ops and ops[0].mode == 'abs':
            v = num(re.sub(r'\.[wl]$', '', ops[0].t, flags=re.I))
            if v is not None:
                return s.reecrit_adresse(ins, mn, v, '%s     %s' % (mn, '%s'))
            return None
        if mn in ('jsr', 'jmp') and ops and ops[0].mode in ('ind', 'disp', 'idx', 'pcidx', 'pcdisp'):
            return None
        if (mn.startswith('b') and mn[1:] in COND and mn not in ('bset', 'bclr', 'bchg', 'btst')) or mn == 'bsr' \
                or (mn.startswith('db') and mn != 'dbcc' or mn == 'dbcc') or mn in ('jsr', 'jmp'):
            return None                     # branchement vers une étiquette MAX
        if mn in ('rts', 'rte', 'rtr', 'nop', 'illegal', 'trap', 'reset', 'stop'):
            return None
        if mn in ('lea', 'pea', 'movea') and ops and ops[0].mode in ('abs', 'imm'):
            t = ops[0].imm if ops[0].mode == 'imm' else re.sub(r'\.[wl]$', '', ops[0].t, flags=re.I)
            v = num(t)
            if v is not None and v in s.corr:
                return s.reecrit_adresse(ins, mn, v, mn + ('.' + SUF[ins.sz] if isinstance(ins.sz, int) else '') +
                                         ' ' + ('#' if ops[0].mode == 'imm' else '') + '%s, ' + ins.ops[1])
        # ---- instructions sans mémoire
        mems = [o for o in ops if o.mem]
        if mn in ('lea', 'pea'):
            src = ops[0]
            if src.mode == 'disp':
                g = s.base_de(src, st)
                ok = (g[0] in ('tab', 'pile')) or (g[0] in ('a5', 'objet') and src.disp is not None and src.disp % 0x400 == 0) \
                    or (g[0] in ('objet', 'fiche_psp') and src.disp == -0x1d0) \
                    or (g[0] == 'fiche' and src.disp is not None and src.disp % 0x10 == 0) \
                    or (g[0] == 'objet' and s.modele_objet == 'acteur' and src.disp is not None and src.disp % 0x80 == 0)
                if not ok and g[0] == 'objet' and src.disp is not None and any(a <= src.disp < z for a, z in ZONES_RAZ):
                    s.verifie_raz(code, i, src.disp)                       # lève NonResolu si la boucle sort de la zone
                    ok = True
                if not ok:
                    raise NonResolu('%s d\'une adresse de champ sur une base %s : non converti' % (mn, g[0]))
            return None
        if not mems:
            # movea Dn -> An avec un pointeur PS2 brut : CONV
            if mn in ('movea', 'move') and len(ops) == 2 and ops[1].mode == 'an' and ops[0].mode == 'dn' \
                    and st[ops[0].reg][0] == 'ps2':
                g = st[ops[0].reg]
                return s.emet(ins, [ins.texte.split(';')[0].strip()[len(s.prefixe(ins)):].strip(),
                                    'jsr     %s.w' % s.conv_txt(ops[1].reg)],
                              'pointeur PS2 (%s) -> adresse image : JSR CONV_%s' % (g[1], ops[1].reg.upper()))
            return None
        sz = ins.sz if isinstance(ins.sz, int) else None
        if sz is None:
            if mn in ('btst', 'bset', 'bclr', 'bchg', 'tas', 'nbcd') or (mn.startswith('s') and mn[1:] in COND): sz = 1
            elif mn in ('muls', 'mulu', 'divs', 'divu', 'chk'): sz = 2
            elif mn in ('movea', 'move', 'cmpa', 'adda', 'suba', 'add', 'sub', 'cmp', 'tst', 'clr', 'neg', 'not',
                        'and', 'or', 'eor', 'addi', 'subi', 'andi', 'ori', 'eori', 'cmpi', 'addq', 'subq',
                        'asl', 'asr', 'lsl', 'lsr', 'rol', 'ror'): sz = 2
            elif mn == 'movem':
                sz = 2
            else:
                raise NonResolu('taille d\'accès inconnue pour « %s »' % mn)
        if mn in ('muls', 'mulu', 'divs', 'divu', 'chk'): sz_acc = 2
        else: sz_acc = sz
        if mn == 'movem':
            # sauvegardes / restaurations sur la pile seulement
            for o in mems:
                g = s.base_de(o, st)
                if g[0] not in ('pile', 'tab'): raise NonResolu('movem sur une base %s' % g[0])
            return None
        accs = []
        zero = (mn == 'clr') or (mn == 'move' and len(ops) == 2 and (
            (ops[0].mode == 'imm' and num(ops[0].imm) == 0) or (ops[0].mode == 'dn' and st[ops[0].reg] == ('const', 0))))
        for k, o in enumerate(ops):
            if o.mem:
                try:
                    accs.append(s.acces_de(o, st, sz_acc, mn))
                except NonResolu as e:
                    if zero and sz_acc == 4 and k == len(ops) - 1 and o.mode == 'disp' and 'non typé' in str(e):
                        s.log(ins, 'AVERTISSEMENT', 'écriture de zéro dans un champ non typé (%s) : invariant, laissée telle quelle' % e, ins.texte)
                        accs.append(Acces(o.disp, 'id', 'zéro : invariant de disposition (champ non typé)'))
                    else:
                        raise
            else: accs.append(None)
        # notes de champs délicats -> avertissement
        notes = [a.note for a in accs if a is not None and a.note]
        rr = s.applique(ins, mn, sz_acc, ops, accs, st, code, i, labels_idx)
        if notes and rr is not None:
            s.log(ins, 'AVERTISSEMENT', ' ; '.join(sorted(set(notes))), ins.texte)
        return rr

    def conv_txt(s, reg):
        a = s.conv.get(reg)
        return '$%x' % a if a is not None else 'CONV_%s' % reg.upper()

    def reecrit_adresse(s, ins, mn, v, gabarit):
        r = s.resout(v)
        if not r['ok']:
            raise NonResolu('appel moteur $%X : %s' % (v, r['raison']))
        regle = 'moteur $%X -> image $%X (va 0x%x, %s)' % (v, r['img'], r['va'], r['statut'])
        if r['statut'].startswith('modifi'):
            s.log(ins, 'AVERTISSEMENT', 'routine modifiée par Upper $%X : %s' % (v, r['remarque'][:160]), ins.texte)
        if '%s, ' in gabarit: ligne = gabarit % s.sym(v)
        elif mn in ('jsr', 'jmp'): ligne = '%s     (%s).l' % (mn, s.sym(v))
        else: ligne = gabarit % s.sym(v)
        return s.emet(ins, [ligne], regle)

    def reecrit_dc(s, ins):
        """dc.l de valeurs numériques = adresses du moteur (TAB_MANIPS…) -> symboles résolus"""
        if ins.sz != 4: return None
        vals = split_ops(ins.ops[0]) if ins.ops else []
        out, chg, regles = [], False, []
        for t in vals:
            v = num(t)
            if v is not None and v >= 0x1000 and v in s.corr:
                r = s.resout(v)
                if not r['ok']:
                    raise NonResolu('dc.l $%X (adresse moteur) : %s' % (v, r['raison']))
                out.append(s.sym(v)); chg = True; regles.append('$%X->$%X' % (v, r['img']))
                if r['statut'].startswith('modifi'):
                    s.log(ins, 'AVERTISSEMENT', 'routine modifiée par Upper $%X : %s' % (v, r['remarque'][:160]), ins.texte)
            else:
                out.append(t)
        if not chg: return None
        return s.emet(ins, ['dc.l    ' + ', '.join(out)], 'adresses moteur ' + ' '.join(regles))

    # ---------------------------------------------------------------- cœur : une instruction avec mémoire typée
    def applique(s, ins, mn, sz, ops, accs, st, code, i, labels_idx):
        suf = SUF[sz]
        perms = [a.perm if a is not None else 'id' for a in accs]
        regles = [a.regle for a in accs if a is not None]
        regle = ' ; '.join(regles)
        ptr_lu = None
        orig = ins.texte.split(';')[0].strip()
        pre = s.prefixe(ins)
        if pre: orig = orig[len(pre):].strip()
        def mtxt(k, decal=0):
            return s.txt_mem(ops[k], accs[k], decal)
        def remplace_ops(decal=0):
            parts = []
            for k, o in enumerate(ops):
                parts.append(mtxt(k, decal) if o.mem else o.t)
            m = orig.split(None, 1)[0]
            return '%-7s %s' % (m, ', '.join(parts))
        tout_id = all(p == 'id' for p in perms)
        # pointeur lu vers un registre d'adresse : CONV
        if mn in ('movea', 'move') and len(ops) == 2 and ops[1].mode == 'an' and accs[0] is not None:
            a = accs[0]
            if sz == 4 and a.perm != 'id':
                an = ops[1].reg
                if an == 'a7': raise NonResolu('lecture permutée vers SP')
                dk = 'd0'
                if ops[0].reg == 'd0' or (ops[0].idx and ops[0].idx[0] == 'd0'): dk = 'd1'
                pc, _ = perm_code(a.perm, dk)
                L = ['movea.l %s, %s' % (mtxt(0), an), 'exg     %s, %s' % (dk, an), 'move    sr, -(sp)'] + pc + \
                    ['move    (sp)+, ccr', 'exg     %s, %s' % (dk, an)]
                g = st.get(ops[0].reg, INCONNU) if ops[0].reg else INCONNU
                if a.ptr is not None:
                    L.append('jsr     %s.w' % s.conv_txt(an)); regle += ' ; CONV_%s' % an.upper()
                return s.emet(ins, L, regle)
            if sz == 2 and a.perm != 'id':
                an = ops[1].reg
                dk = s.choisit_dk(ops[0])
                pc, _ = perm_code(a.perm, dk)
                L = ['move    sr, -(sp)', 'move.l  %s, -(sp)' % dk, 'move.w  %s, %s' % (mtxt(0, 6), dk)] + pc + \
                    ['movea.w %s, %s' % (dk, an), 'movem.l (sp)+, %s' % dk, 'move    (sp)+, ccr']
                return s.emet(ins, L, regle)
            if tout_id:
                if accs[0] is not None and (accs[0].d is None or accs[0].d == ops[0].disp and ops[0].mode == 'disp'):
                    if accs[0].d is not None: s.log(ins, 'inchangé', regle, ins.texte)
                    return None
                return s.emet(ins, [remplace_ops()], regle)
        if tout_id:
            if all(a is None or a.d is None for a in accs): return None
            if all(a is None or a.d is None or (ops[k].disp == a.d and ops[k].mode == 'disp') for k, a in enumerate(accs)):
                s.log(ins, 'inchangé', regle, ins.texte)
                return None
            if any(ops[k].mode == 'ind' and a is not None and a.d is not None for k, a in enumerate(accs)):
                pass
            return s.emet(ins, [remplace_ops()], regle)
        # ---------------- au moins un opérande à valeur permutée
        utilises = drapeaux_utilises(code, i, labels_idx)
        src, dst = (ops[0], ops[1]) if len(ops) == 2 else (None, ops[0])
        asrc, adst = (accs[0], accs[1]) if len(ops) == 2 else (None, accs[0])
        psrc = asrc.perm if asrc is not None else 'id'
        pdst = adst.perm if adst is not None else 'id'

        def via_registre(lecture, op_ligne, ecriture, garde_sr=False, perm_l='id', perm_e='id', fin_tst=False):
            dk = s.choisit_dk(*ops)
            L = ['move.l  %s, -(sp)' % dk]
            if lecture:
                L.append(lecture.replace('@', dk))
                L += perm_code(perm_l, dk)[0]
            if op_ligne: L.append(op_ligne.replace('@', dk))
            if ecriture:
                if garde_sr: L.append('move    sr, -(sp)')
                pc, ex = perm_code(perm_e, dk)
                L += pc + [ecriture.replace('@', dk)] + pc
                if garde_sr: L.append('move    (sp)+, ccr')
                elif not ex and utilises & set('NZVC'): L.append('tst.%s   %s' % (suf, dk))
            if fin_tst: L.append('tst.%s   %s' % (suf, dk))
            L.append('movem.l (sp)+, %s' % dk)
            return L

        if mn == 'move':
            if dst.mem and adst is not None and src.mem and asrc is not None:
                if psrc == pdst:
                    return s.emet(ins, [remplace_ops()], regle + ' ; copie brute (même disposition)')
                dk = s.choisit_dk(*ops)
                L = ['move.l  %s, -(sp)' % dk, 'move.%s  %s, %s' % (suf, mtxt(0, 4), dk)] + perm_code(psrc, dk)[0] + \
                    perm_code(pdst, dk)[0] + ['move.%s  %s, %s' % (suf, mtxt(1, 4), dk)] + perm_code(pdst, dk)[0]
                if not perm_code(pdst, dk)[1] or pdst == 'id': L.append('tst.%s   %s' % (suf, dk))
                L.append('movem.l (sp)+, %s' % dk)
                return s.emet(ins, L, regle + ' ; via registre')
            if dst.mem and pdst != 'id':
                if src.mode == 'imm':
                    v = num(src.imm)
                    if v is not None:
                        pv = perm_val(v, pdst, sz)
                        mauvais = set() if ((pv >> (8 * sz - 1)) & 1) == ((v >> (8 * sz - 1)) & 1) else {'N'}
                        if not (mauvais & utilises):
                            return s.emet(ins, ['move.%s  #$%x, %s' % (suf, pv, mtxt(1))], regle + ' ; immédiat #$%x -> #$%x' % (v & ((1 << 8 * sz) - 1), pv))
                    else:
                        if not ({'N'} & utilises):
                            return s.emet(ins, ['move.%s  #%s, %s' % (suf, perm_expr(src.imm, pdst), mtxt(1))], regle + ' ; immédiat symbolique permuté')
                    L = via_registre('move.%s  #%s, @' % (suf, src.imm), None, 'move.%s  @, %s' % (suf, mtxt(1, 4)), perm_e=pdst)
                    return s.emet(ins, L, regle + ' ; via registre (drapeaux)')
                if src.mode == 'dn':
                    pc, ex = perm_code(pdst, src.reg)
                    L = pc + ['move.%s  %s, %s' % (suf, src.reg, mtxt(1))] + pc
                    if not ex and utilises & set('NZVC'): L.append('tst.%s   %s' % (suf, src.reg))
                    return s.emet(ins, L, regle)
                if src.mode == 'an' or not src.mem:
                    L = via_registre('move.%s  %s, @' % (suf, src.t), None, 'move.%s  @, %s' % (suf, mtxt(1, 4)), perm_e=pdst)
                    return s.emet(ins, L, regle + ' ; via registre')
                # source mémoire non typée (table MAX, pile) -> champ permuté
                L = via_registre('move.%s  %s, @' % (suf, mtxt(0, 4)), None, 'move.%s  @, %s' % (suf, mtxt(1, 4)), perm_e=pdst)
                return s.emet(ins, L, regle + ' ; via registre')
            if src.mem and psrc != 'id':
                if dst.mode == 'dn':
                    pc, ex = perm_code(psrc, dst.reg)
                    L = ['move.%s  %s, %s' % (suf, mtxt(0), dst.reg)] + pc
                    if not ex and utilises & set('NZVC'): L.append('tst.%s   %s' % (suf, dst.reg))
                    return s.emet(ins, L, regle)
                # vers mémoire non typée (pile, table MAX)
                if dst.mode in ('predec',) and dst.reg == 'a7':
                    # empiler la valeur logique : la lire, la permuter sur place dans la pile
                    dk = s.choisit_dk(*ops)
                    L = ['move.%s  %s, -(sp)' % (suf, mtxt(0))]
                    raise NonResolu('empilement d\'un champ permuté (à écrire à la main)')
                L = via_registre('move.%s  %s, @' % (suf, mtxt(0, 4)), None, None, perm_l=psrc, fin_tst=not perm_code(psrc, 'd7')[1])
                L.insert(-1, 'move.%s  @, %s'.replace('@', L[0].split()[1].rstrip(',')) % (suf, mtxt(1, 4)))
                return s.emet(ins, L, regle + ' ; via registre')
        if mn == 'clr':
            return s.emet(ins, [remplace_ops()], regle + ' ; zéro invariant')
        if mn in ('andi', 'ori', 'eori') and src.mode == 'imm' and dst.mem:
            v = num(src.imm)
            mauvais = {'N'}
            if v is not None:
                pv = perm_val(v, pdst, sz)
                if not (mauvais & utilises):
                    return s.emet(ins, ['%s.%s  #$%x, %s' % (mn, suf, pv, mtxt(1))], regle + ' ; masque permuté')
            elif not (mauvais & utilises):
                return s.emet(ins, ['%s.%s  #%s, %s' % (mn, suf, perm_expr(src.imm, pdst), mtxt(1))], regle + ' ; masque permuté')
            op = mn
            L = via_registre('move.%s  %s, @' % (suf, mtxt(1, 4)), '%s.%s  #%s, @' % (op, suf, src.imm),
                             'move.%s  @, %s' % (suf, mtxt(1, 4)), garde_sr=True, perm_l=pdst, perm_e=pdst)
            return s.emet(ins, L, regle + ' ; via registre (drapeaux)')
        if mn == 'not' and not ({'N'} & utilises):      # NOT : Z exact, V=C=0, X intact
            return s.emet(ins, [remplace_ops()], regle + ' ; NOT invariant')
        if mn == 'tst':
            if not (utilises & {'N'}):            # tst : Z exact, V=C=0 exacts, X intact ; seul N dépend de l'ordre
                return s.emet(ins, [remplace_ops()], regle + ' ; test de nullité (Z seul)')
            L = via_registre('move.%s  %s, @' % (suf, mtxt(0, 4)), None, None, perm_l=pdst, fin_tst=True)
            return s.emet(ins, L, regle + ' ; via registre (drapeaux %s)' % ''.join(sorted(utilises)))
        if mn == 'cmpi' and dst.mem:
            v = num(src.imm)
            if not (utilises & set('NVC')):       # cmpi : Z exact (égalité), X intact
                if v is not None:
                    pv = perm_val(v, pdst, sz)
                    return s.emet(ins, ['cmpi.%s  #$%x, %s' % (suf, pv, mtxt(1))], regle + ' ; égalité : immédiat #$%x -> #$%x' % (v & ((1 << 8 * sz) - 1), pv))
                return s.emet(ins, ['cmpi.%s  #%s, %s' % (suf, perm_expr(src.imm, pdst), mtxt(1))], regle + ' ; égalité : immédiat permuté')
            L = via_registre('move.%s  %s, @' % (suf, mtxt(1, 4)), 'cmpi.%s  #%s, @' % (suf, src.imm), None, perm_l=pdst)
            return s.emet(ins, L, regle + ' ; comparaison ordonnée via registre')
        # source mémoire permutée, destination registre (add/sub/and/or/cmp/cmpa/muls/divs…)
        if src is not None and src.mem and psrc != 'id' and not dst.mem:
            dk = s.choisit_dk(*ops)
            L = ['move.l  %s, -(sp)' % dk, 'move.%s  %s, %s' % (suf, mtxt(0, 4), dk)] + perm_code(psrc, dk)[0] + \
                ['%s %s, %s' % (orig.split(None, 1)[0], dk, dst.t), 'movem.l (sp)+, %s' % dk]
            return s.emet(ins, L, regle + ' ; lecture via registre')
        # lecture-modification-écriture d'un champ permuté
        if dst.mem and pdst != 'id' and mn in ('add', 'sub', 'addi', 'subi', 'addq', 'subq', 'and', 'or', 'eor',
                                               'neg', 'negx', 'not', 'asl', 'asr', 'lsl', 'lsr', 'rol', 'ror',
                                               'andi', 'ori', 'eori'):
            if src is not None and src.mem and psrc != pdst and psrc != 'id':
                raise NonResolu('opération entre deux champs permutés différemment')
            m = orig.split(None, 1)[0]
            if src is None:
                opl = ('%s #1, @' % m) if mn in ('asl', 'asr', 'lsl', 'lsr', 'rol', 'ror') else ('%s @' % m)
            else:
                opl = '%s %s, @' % (m, s.txt_mem(src, asrc, 4) if src.mem else src.t)
            L = via_registre('move.%s  %s, @' % (suf, mtxt(len(ops) - 1, 4)), opl, 'move.%s  @, %s' % (suf, mtxt(len(ops) - 1, 4)),
                             garde_sr=bool(utilises), perm_l=pdst, perm_e=pdst)
            return s.emet(ins, L, regle + ' ; lecture-modification-écriture via registre')
        raise NonResolu('combinaison non gérée (%s, perms %s)' % (mn, perms))

    # ============================================================================ données lues par le moteur
    def convertit_donnees(s, nom, lignes):
        """tables_explicites_*.s (pas d'animation) et donnees_projectiles_max.s (en-têtes / boîtes / attaques /
        index de boîtes) -> format PS2 de l'image. Les octets sont regroupés par structure puis permutés."""
        out = []; i = 0; n = len(lignes)
        bloc = None          # (genre, étiquette)
        def flush_struct(acc, genre, lab_lignes):
            pass
        # on travaille enregistrement par enregistrement : chaque étiquette ouvre un bloc ; le bloc est lu comme une
        # suite d'éléments (octet, mot, long symbolique)
        blocs = []           # [(étiquette ou None, [lignes])]
        cur = [None, []]
        for l in lignes:
            ins, _ = analyse_ligne(nom, 0, l, '')
            if ins.labels and not ins.equ:
                blocs.append(cur); cur = [ins.labels[0], [l]]
            else:
                cur[1].append(l)
        blocs.append(cur)
        num_ligne = 0
        for lab, L in blocs:
            genre = s.genre_donnee(nom, lab)
            if genre is None or lab is None:
                out.extend(x.rstrip('\n') for x in L); num_ligne += len(L); continue
            elems = []      # (taille, valeur|expr, commentaire, n° de ligne)
            tete = []
            for k, l in enumerate(L):
                ins, _ = analyse_ligne(nom, num_ligne + k + 1, l, '')
                if ins.mn == 'dc' and isinstance(ins.sz, int):
                    for t in split_ops(ins.ops[0]):
                        elems.append((ins.sz, t, ins.com, num_ligne + k + 1))
                elif ins.mn is None:
                    tete.append(l.rstrip('\n'))
                else:
                    out.extend(x.rstrip('\n') for x in L); elems = None; break
            if elems is None: num_ligne += len(L); continue
            pseudo = Ins(nom, num_ligne + 1, L[0])
            try:
                nouv = s.permute_bloc(genre, elems)
            except NonResolu as e:
                s.log(pseudo, 'NON RÉSOLU', 'données %s : %s' % (lab, e), L[0])
                out.extend(x.rstrip('\n') + '  ; ⚠ CONV NON RÉSOLU' if j == 0 else x.rstrip('\n') for j, x in enumerate(L))
                num_ligne += len(L); continue
            out.append(L[0].rstrip('\n') + '   ; conv : format PS2 (%s)' % genre)
            out.extend(nouv)
            s.log(pseudo, 'réécrit', 'données %s (%s) : %d éléments' % (lab, genre, len(elems)), L[0].strip(), '')
            s.stats['blocs_donnees'] += 1
            num_ligne += len(L)
        return out

    @staticmethod
    def genre_donnee(nom, lab):
        if lab is None: return None
        if nom.startswith('tables_explicites'):
            if lab.startswith('P_'): return 'pas'
            if lab.startswith('TAB_'): return None          # table de pointeurs lue par le code MAX (psp_cfd9c)
            return '?'
        if nom == 'donnees_projectiles_max.s':
            if lab.startswith('TABP_'): return 'entete'
            if lab.startswith('B_'): return 'boites'
            if lab.startswith('A_'): return 'attaques'
            if lab.startswith('TABS_'): return 'index_boites'
            return '?'
        return None

    def permute_bloc(s, genre, elems):
        """éléments -> lignes dc au format image"""
        if genre == '?': raise NonResolu('bloc de genre inconnu')
        if genre in ('entete', 'boites'):
            # mots lus tels quels (ADRESSES §7 ; boîtes : mesuré, Ryu $100256 brut dans l'image $1E2FDE)
            if any(t != 2 for t, *_ in elems): raise NonResolu('élément non mot dans un bloc de mots')
            return ['        dc.w    ' + ', '.join(e[1] for e in elems)]
        # flux d'octets avec positions dans la structure courante. Pas : 20 o ; si l'octet +1 (drapeaux) a le bit 7
        # (pas de reprise, arcade $2A80A : movea.l $14(a0)), un long « reprise » suit en +$14 (pointeur, SWAP).
        # Attaques : 32 o.
        # index de boîtes ($88, entrées de 4 o copiées brutes en $C8 par $2A770) : 4 u8, échangés dans chaque mot
        # (mesuré : Ryu/Ken/Akuma/Sagat, arcade $DD092[id] <-> image, 64 o identiques une fois les octets échangés)
        per = {'pas': 20, 'attaques': 32, 'index_boites': 4}[genre]
        cls = {'pas': lambda o: OCT['pas'].get(o), 'attaques': lambda o: OCT['attaque'].get(o),
               'index_boites': lambda o: ('u8',)}[genre]
        def octets_de(v, sz):
            return [(v >> (8 * (sz - 1 - k))) & 0xFF for k in range(sz)]
        flux = []      # (décalage dans la structure, ('o', valeur) | ('L', expr))
        o = 0; reprise_due = False; drap = None
        for sz, t, com, ln in elems:
            v = num(t)
            if o == per and genre == 'pas' and reprise_due and sz == 4:
                flux.append((0x14, ('L', t))); o = 0; reprise_due = False; continue
            if o >= per:
                o -= per; reprise_due = False
            if sz == 4:
                c = cls(o)
                if c is not None and c[0] == 'ptr' and c[1] == o:
                    flux.append((o, ('L', t))); o += 4; continue
                if v is None: raise NonResolu('long symbolique « %s » hors champ pointeur (+$%X)' % (t, o))
                for b in octets_de(v, 4): flux.append((o, ('o', b))); o += 1
                continue
            if v is None: raise NonResolu('valeur symbolique « %s » (+$%X)' % (t, o))
            for b in octets_de(v & ((1 << 8 * sz) - 1), sz):
                if genre == 'pas' and o == 1: reprise_due = bool(b & 0x80)
                flux.append((o, ('o', b))); o += 1
        if o != per and not (o == 0 and flux and flux[-1][0] == 0x14 and flux[-1][1][0] == 'L'): raise NonResolu('bloc incomplet (%d octets dans la dernière structure de %d)' % (o, per))
        # permutation des octets u8 par paires (position paire)
        res = []; k = 0
        while k < len(flux):
            o, e = flux[k]
            if e[0] == 'L':
                res.append('        dc.l    %s' % perm_expr(e[1], 'swap')); k += 1; continue
            c0, c1 = cls(o), cls(o + 1)
            if o & 1 or k + 1 >= len(flux) or flux[k + 1][1][0] != 'o':
                raise NonResolu('octet isolé à +$%X' % o)
            b0, b1 = e[1], flux[k + 1][1][1]
            if c0 is None or c1 is None: raise NonResolu('octet +$%X non typé' % o)
            if c0[0] == 'u8' and c1[0] == 'u8': b0, b1 = b1, b0
            elif c0[0] == 's16' and c1[0] == 's16': pass
            else: raise NonResolu('octets +$%X/%X de types %s/%s' % (o, o + 1, c0, c1))
            res.append((b0, b1)); k += 2
        # regroupe les paires d'octets en lignes dc.b
        out = []; cour = []
        for r in res:
            if isinstance(r, tuple):
                cour += ['$%02x' % r[0], '$%02x' % r[1]]
                if len(cour) >= 16: out.append('        dc.b    ' + ', '.join(cour)); cour = []
            else:
                if cour: out.append('        dc.b    ' + ', '.join(cour)); cour = []
                out.append(r)
        if cour: out.append('        dc.b    ' + ', '.join(cour))
        return out

# ============================================================================================ programme principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sources', default=SRC_DEF)
    ap.add_argument('--sortie', default=os.path.join(ICI, 'sortie'))
    ap.add_argument('--carte', default=CARTE_DEF)
    ap.add_argument('--roms', default=ROMS_DEF)
    ap.add_argument('--sans-image', action='store_true')
    args = ap.parse_args()
    os.makedirs(args.sortie, exist_ok=True)
    C = Convertisseur(args)
    try:
        t_carte = os.path.getmtime(args.carte)
        t_rom = max(os.path.getmtime(os.path.join(args.roms, f)) for f in ROM_FICHIERS)
        if abs(t_rom - t_carte) > 120:
            print('⚠ carte_image.txt et les ROM de l\'image diffèrent de %d s : reconstruction en cours ou carte périmée ?'
                  % (t_rom - t_carte))
    except OSError:
        pass
    C.calcule_feuilles(args.sources, FICHIERS_CODE)
    if CONFLITS_T:
        for c in CONFLITS_T: print('conflit de typage :', c)
    for f in FICHIERS_CODE:
        L = open(os.path.join(args.sources, f), errors='replace').readlines()
        out = C.convertit_fichier(f, L)
        open(os.path.join(args.sortie, f), 'w').write(
            '; CONVERTI POUR L\'IMAGE D\'UPPER par convertit_max.py le %s — NE PAS ÉDITER (relancer la passe)\n'
            % datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + '\n'.join(out) + '\n')
    for f in FICHIERS_DONNEES_MOTEUR:
        L = open(os.path.join(args.sources, f), errors='replace').readlines()
        out = C.convertit_donnees(f, L)
        open(os.path.join(args.sortie, f), 'w').write(
            '; CONVERTI (données au format PS2 de l\'image) par convertit_max.py — NE PAS ÉDITER\n' + '\n'.join(out) + '\n')
    for f in FICHIERS_DONNEES_MAX:
        open(os.path.join(args.sortie, f), 'w').write(open(os.path.join(args.sources, f)).read())
    # adresses résolues
    with open(os.path.join(args.sortie, 'adresses_upper.s'), 'w') as o:
        o.write('; Adresses du moteur d\'Upper résolues par va MIPS (carte : %s, %d lignes, %s)\n' % (
            args.carte, C.n_carte, datetime.datetime.fromtimestamp(os.path.getmtime(args.carte)).strftime('%Y-%m-%d %H:%M:%S')))
        o.write('; CONV_An (image) : %s\n' % ', '.join('%s=$%X' % (k.upper(), v) for k, v in sorted(C.conv.items()) if v is not None))
        for a in sorted(C.adresses):
            r = C.adresses[a]
            if r['ok']:
                o.write('UP_%05X equ $%06X    ; arcade $%X -> va 0x%x (%s ; %s) [image du %s : %s]\n' % (
                    a, r['img'], a, r['va'], r['statut'], r['nom'][:50], 'TSV', r['ancien']))
            else:
                o.write('; UP_%05X NON RÉSOLU : %s\n' % (a, r['raison']))
        for k, v in sorted(C.conv.items()):
            if v is None: o.write('CONV_%s equ $0    ; ⚠ NON TROUVÉE dans l\'image\n' % k.upper())
    with open(os.path.join(args.sortie, 'journal.tsv'), 'w') as o:
        o.write('fichier\tligne\tstatut\tregle\toriginal\tconverti\n')
        for j in C.journal: o.write('\t'.join(str(x).replace('\t', ' ') for x in j) + '\n')
    with open(os.path.join(args.sortie, 'non_resolus.tsv'), 'w') as o:
        o.write('fichier\tligne\traison\toriginal\n')
        for j in C.journal:
            if j[2] == 'NON RÉSOLU': o.write('%s\t%s\t%s\t%s\n' % (j[0], j[1], j[3], j[4]))
    # assemblage d'essai
    with open(os.path.join(args.sortie, 'tout_max_upper.s'), 'w') as o:
        o.write('        org     $200000\n')
        for f in ORDRE_ASSEMBLAGE:
            o.write('; ==== %s\n' % f); o.write(open(os.path.join(args.sortie, f)).read()); o.write('\n')
    # contrôle carte <-> image : 1re instruction de chaque adresse résolue décodée dans l'image actuelle (unidasm)
    ctl = Counter(); ecarts = []
    if C.img is not None:
        import tempfile, shutil
        if shutil.which('unidasm'):
            tmp = os.path.join(args.sortie, '_ctl.bin')
            for a, r in sorted(C.adresses.items()):
                if not r['ok']: continue
                open(tmp, 'wb').write(C.img[r['img']:r['img'] + 16])
                out = subprocess.run(['unidasm', '-arch', 'm68000', '-basepc', hex(r['img']), tmp], capture_output=True, text=True).stdout
                l = out.splitlines()[0] if out else ''
                m = re.match(r'^[0-9a-f]+: (?:[0-9a-f]{4} )+\s*(\S+)', l)
                mn_img = (m.group(1) if m else '?').split('.')[0].lower()
                mn_carte = r['texte'].split()[0].split('.')[0].lower() if r['texte'] else '?'
                ok = mn_img == mn_carte or (mn_img.startswith('b') and mn_carte.startswith('b')) or mn_carte in ('jsr', 'jmp') and mn_img in ('jsr', 'jmp', 'bsr', 'bra')
                ctl['accord' if ok else 'écart'] += 1
                if not ok: ecarts.append('$%X -> $%X : carte « %s » / image « %s »' % (a, r['img'], r['texte'][:40], l[:60]))
            os.remove(tmp)
    open(os.path.join(args.sortie, 'controle_image.txt'), 'w').write(
        'contrôle carte <-> image (1re instruction de chaque adresse résolue) : %s\n' % dict(ctl) + '\n'.join(ecarts) + '\n')
    st = dict(C.stats)
    st['controle_image'] = dict(ctl)
    st['adresses_resolues'] = sum(1 for r in C.adresses.values() if r['ok'])
    st['adresses_non_resolues'] = sum(1 for r in C.adresses.values() if not r['ok'])
    st['conv'] = {k: v for k, v in C.conv.items()}
    st['carte'] = args.carte; st['lignes_carte'] = C.n_carte
    json.dump(st, open(os.path.join(args.sortie, 'stats.json'), 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(st, indent=1, ensure_ascii=False))

if __name__ == '__main__':
    main()
