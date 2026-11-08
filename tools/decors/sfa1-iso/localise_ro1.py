#!/usr/bin/env python3
"""localise_ro1.py (cote ORACLE, local) : retrouve dans le module ro1 de l'Anthology (Street Fighter Zero, e206
decompresse) les tables de decor de l'arcade sfa (programme dechiffre de etude_decors), par contenu, sous les trois
rangements du recompilateur (brut, mots echanges « w », longs echanges « l »). Ecrit outils/carte_ro1.json : pour
chaque table, adresse arcade, adresse EXEC ro1 (= fichier + 0x1F0000), taille, rangement. Ce fichier ne contient
que des adresses (aucune donnee de jeu) : c'est lui que lit extrait_sfa1.py (cote ISO).
Usage : python3 localise_ro1.py RO1_DEC.bin DONNEES.bin CODE.bin"""
import sys, json, struct, os
R = open(sys.argv[1], 'rb').read(); D = open(sys.argv[2], 'rb').read(); C = open(sys.argv[3], 'rb').read()
EXEC = 0x1F0000
def sw16(b): return b''.join(b[i:i+2][::-1] for i in range(0, len(b), 2))
def sw32(b): return b''.join(b[i:i+4][::-1] for i in range(0, len(b), 4))
TR = {'w': sw16, 'l': sw32, 'b': lambda b: b}
w = lambda b, a: struct.unpack_from('>H', b, a)[0]
sw = lambda b, a: struct.unpack_from('>h', b, a)[0]

def trouve(src, a, n, modes='wlb', prefere=None):
    """toutes les positions exec de la table src[a:a+n] dans ro1 ; rend (mode, exec) unique ou leve"""
    hits = []
    for m in modes:
        t = TR[m](src[a:a+n]); o = R.find(t)
        while o >= 0:
            if o % 2 == 0: hits.append((m, o + EXEC))
            o = R.find(t, o + 1)
    if prefere is not None:
        h2 = [h for h in hits if h[1] - a == prefere]
        if h2: return h2[0], len(hits)
    hs = sorted(set(hits))
    if not hs: return None, 0
    return hs[0], len(hs)

N = 13; out = {}
def note(nom, src, a, n, modes='wlb', prefere=None, ref=None):
    h, k = trouve(src, a, n, modes, prefere)
    out[nom] = dict(arcade='$%06X' % a, source='code' if src is C else 'donnees', taille=n,
                    exec=('0x%06X' % h[1]) if h else None, rangement=h[0] if h else None, occurrences=k, ref=ref)
    print('%-22s arc $%06X n=%5d -> %s (%d occ.)' % (nom, a, n, ('%s exec 0x%06X delta %+X' % (h[0], h[1], h[1]-a)) if h else 'ABSENT', k))
    return h

# 1. tables par decor indexees ($FFAE00) : types, decalages des listes
note('types_s2', D, 0x1B2AE, 2*N); note('types_s3', D, 0x1B37A, 2*N)
note('ofs_listes_s2', D, 0x1B2CE, 2*N); note('ofs_listes_s3', D, 0x1B39A, 2*N)
# zone des listes (decalages signes depuis la table)
for nom, tab, n in (('listes_s2', 0x1B2CE, 16), ('listes_s3', 0x1B39A, 64)):
    adr = [tab + sw(D, tab + 2*s) for s in range(N)]
    lo, hi = min(adr), max(adr) + n
    note(nom, D, lo, hi - lo, ref='zone [%X,%X) : listes des 13 decors' % (lo, hi))
# 2. bibliotheques (blocs 0..44 de scroll2 = 1 Ko ; scroll3 0..22, 76, 77 = 256 o)
note('bib_s2', D, 0x1CDB60, 45*1024)
note('bib_s3_a', D, 0x1E2B60, 23*256); note('bib_s3_b', D, 0x1E2B60 + 76*256, 2*256)
# 3. palettes
note('pal_s2', D, 0x1F20A0, N*0x400); note('pal_s3', D, 0x1F94A0, N*0x400)
note('pal_obj24', D, 0x1E97A0, N*0x100)
for s in range(N): note('pal_obj0_%02d' % s, D, 0x1E7960 + 0x200*s, 0x200)
note('pal_s1_hud', D, 0x1EE0A0, 0x20)
# 4. objets : decalages (relatifs PC -> code.bin) puis enregistrements (donnees.bin)
note('ofs_objets', C, 0x1BCF8, 2*N)
adr = []
for s in range(N):
    a = 0x1BCF8 + w(C, 0x1BCF8 + 2*s); n = 0
    while D[a + 16*n] < 0x80: n += 1
    adr.append((a, 16*n + 2))
lo = min(a for a, n in adr); hi = max(a + n for a, n in adr)
note('objets', D, lo, hi - lo, ref='zone des enregistrements de 16 o des 13 decors')
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'carte_ro1.json'), 'w'), indent=1)
