#!/usr/bin/env python3
"""localise_anims_ro1.py (côté ORACLE, local) : retrouve dans ro1 (e206 décompressé) les tables d'ANIMATION des objets
de décor de SFA1 repérées dans le programme arcade sfa déchiffré (etude_decors), et le prouve par un parcours parallèle.

Rangement constaté dans ro1 (recompilateur) : chaque champ selon son type — mots petit-boutistes, pointeurs = longs
petit-boutistes en adresses EXEC de ro1 ; les cadres contenant un long sont REALIGNÉS sur 4 octets (décalages de la
table de tête décalés de 0 à 6 octets par rapport à l'arcade : pas de translation constante possible).
Cadre (arcade : 16 o pour tuiles / sprites, 8 o pour palettes) : +0 durée (mot), +2 drapeaux (octet fort ; bit 7 =
fin de boucle : le long qui suit est l'adresse de reprise), +4 pointeur (long) vers le bloc de tuiles / l'entrée de
palette / le descripteur de sprite.
Validation d'une racine candidate : pour chaque animation utilisée, mêmes durées, drapeaux, structure de boucle et
contenu pointé identique (mots) à l'arcade. Écrit outils/carte_anims_ro1.json (adresses seulement, aucune donnée).
Usage : python3 localise_anims_ro1.py RO1_DEC.bin DONNEES.bin"""
import sys, json, struct, os
R = open(sys.argv[1], 'rb').read(); D = open(sys.argv[2], 'rb').read()
EX = 0x1F0000
wa = lambda a: struct.unpack_from('>H', D, a)[0]; la = lambda a: struct.unpack_from('>I', D, a)[0]
wr = lambda a: struct.unpack_from('<H', R, a - EX)[0]; lr = lambda a: struct.unpack_from('<I', R, a - EX)[0]
def mots_a(a, n): return [wa(a + 2 * i) for i in range(n)]
def mots_r(a, n): return [wr(a + 2 * i) for i in range(n)]

# (racine arcade, genre, animations utilisées par les décors, rôle) — lu dans le code 68K (RAPPORT §5)
TABLES = [
    (0x11BCBA, 'tuiles_s2', [0, 1, 2, 3, 4, 5, 6], 'classes $14 ($9=8 : Sodom 0-3, Ken 4) et $2E (Guy 5, ou 6 si $190(A5)≠0)'),
    (0x444D4, 'palette', [0, 1], 'classe $33 (Ryu 0, Guy 1)'),
    (0x10F060, 'sprite', [0, 1], 'classe $06 s0 (Ryu, anim 0), $24 (Ryu, anim 1)'),
    (0x10F526, 'sprite', [0], 'classe $06 s1 (Ken)'),
    (0x10F69E, 'sprite', [0, 1, 2, 3, 4, 5, 6, 7], 'classe $06 s2 (Charlie 0), $11 (Charlie 1-4), $1F (Charlie, créés par $1E)'),
    (0x10FC44, 'sprite', [0, 1, 2, 3], 'classe $06 s3 (Guy 0), $16 (Guy 1-3)'),
    (0x110292, 'sprite', [0, 1, 2, 3], 'classe $15 (Birdie / Rose 0-2), $06 s4 (Rose 3)'),
    (0x10FBDA, 'sprite', [0, 1], 'classe $06 s5 / s6 (Adon, Sagat, Dan)'),
    (0x10FC20, 'sprite', [0], 'classe $06 s7 (Sodom, M.Bison)'),
]
TAILLE_CADRE = {'tuiles_s2': 16, 'palette': 8, 'sprite': 16}

def cible_a(genre, p):
    """mots du contenu pointé (arcade)"""
    if genre == 'tuiles_s2':
        r, c = wa(p + 2), wa(p + 4); return mots_a(p, 3 + 2 * (r + 1) * (c + 1))
    if genre == 'palette':
        return mots_a(p, 3)
    t, n = wa(p), wa(p + 2)        # descripteur de sprite : type 0 = 3 + 2n mots ; autres types : en-tête de 3 mots
    return mots_a(p, 3 + 2 * n) if t == 0 else mots_a(p, 3)

def cible_r(genre, p, n):
    if genre == 'tuiles_s2':       # ro1 : en-tête de 3 mots, 2 o de bourrage, puis paires en LONGS (code << 16 | attr)
        m = mots_r(p, 3)
        for k in range((n - 3) // 2):
            v = lr(p + 8 + 4 * k); m += [v >> 16, v & 0xFFFF]
        return m
    return mots_r(p, n)

def parcours_a(T, fs, i):
    a = T + wa(T + 2 * i); seq = []; vus = {}
    while a not in vus:
        vus[a] = len(seq); f = D[a + 2]; seq.append((a, wa(a), f, la(a + 4))); a += fs
        if f & 0x80: a = la(a); return seq, vus[a] if a in vus else None
    return seq, vus[a]

def valide(T, Tr, genre, anims):
    fs = TAILLE_CADRE[genre]; fsr = fs          # 16 / 8 dans ro1 aussi (constaté)
    for i in anims:
        sa, ba = parcours_a(T, fs, i)
        if ba is None: return False
        o = wr(Tr + 2 * i); a = Tr + o; vus = {}
        for k, (_, d, f, p) in enumerate(sa):
            if a - EX < 0 or a - EX + fsr > len(R): return False
            vus[a] = k
            if wr(a) != d or (wr(a + 2) >> 8) != f: return False
            pr = lr(a + 4)
            if not (EX <= pr < EX + len(R)): return False
            ca = cible_a(genre, p)
            if cible_r(genre, pr, len(ca)) != ca: return False
            a += fsr
            if f & 0x80:
                a = lr(a)
                if vus.get(a) != ba: return False
    return True

out = {}
for T, genre, anims, role in TABLES:
    n = max(anims) + 1
    offs = [wa(T + 2 * i) for i in range(n)]
    cands = set()
    for dl in range(0, 8, 2):
        t = b''.join(struct.pack('<H', x + dl) for x in offs[:2])
        o = R.find(t)
        while o >= 0:
            if o % 2 == 0: cands.add(o + EX)
            o = R.find(t, o + 1)
    bons = sorted(c for c in cands if valide(T, c, genre, anims))
    out['$%06X' % T] = dict(genre=genre, anims=anims, role=role, ro1=['0x%06X' % c for c in bons],
                            decalage_tete=[wr(bons[0] + 2 * i) - offs[i] for i in range(n)] if bons else None)
    print('%-8s $%06X anims %s -> ro1 %s (candidats %d)' % (genre, T, anims, ['0x%06X' % c for c in bons], len(cands)))

# sources des cycles de palettes : 4 banques (table $15D3A du moteur, sélecteur 0/4/8/12) ; banque 8 = $1FF1C0
BANQUES = [0x1FCA00, 0x1FEC60, 0x1FF1C0, 0x1FF340]
ent = set()
for T, genre, anims, _ in TABLES:
    if genre != 'palette': continue
    for i in anims:
        for (_, _, _, p) in parcours_a(T, 8, i)[0]:
            ent.add((wa(p + 2), wa(p + 4) & 0xFFE0))
for sel in sorted({s for s, _ in ent}):
    base = BANQUES[sel // 4]; ofs = sorted(o for s, o in ent if s == sel); hi = max(ofs) + 32
    t = b''.join(struct.pack('<H', x) for x in mots_a(base, hi // 2))
    o = R.find(t); hits = []
    while o >= 0: hits.append('0x%06X' % (o + EX)); o = R.find(t, o + 1)
    out['banque_%d' % sel] = dict(arcade='$%06X' % base, taille=hi, ro1=hits)
    print('banque %d ($%06X, %d o utiles) -> ro1 %s' % (sel, base, hi, hits))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'carte_anims_ro1.json'), 'w'), indent=1)
