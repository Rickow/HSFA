#!/usr/bin/env python3
"""Compare la traduction 68K des routines greffees (carte de constructions/proto/b9) a celle des memes routines dans
Upper (fige/ro5/carte_image.txt). Cibles de branchement, adresses de tables et d'appels normalisees : ne doivent
rester que les relogements voulus (A5, tables). Sortie : constructions/proto/comparaison_68k.txt"""
import json, re, difflib, os
G = "<workspace>/work/greffe_arcade"; P = os.path.join(G, 'constructions', 'proto')
J = json.load(open(os.path.join(P, 'greffe.json')))
pl = [(int(a, 16), int(b, 16), int(g, 16)) for a, b, g in J['blocs']]
def lire(f, filt):
    out = []
    for l in open(f):
        p = l.split(None, 2); va = int(p[1], 16); t = p[2].strip() if len(p) > 2 else ''
        k = filt(va)
        if k is not None: out.append((k, t))
    return out
up = lambda va: next((va for a, b, g in pl if a <= va < b), None)
gr = lambda va: next((a + (va - g) for a, b, g in pl if g <= va < g + (b - a)), None)
def norm(t):
    t = re.sub(r'\[mips [0-9a-f]+\]', '', t); t = re.sub(r'\(cible [0-9a-f]+\)', '(cible X)', t)
    t = re.sub(r'cible [0-9a-f]+ -> fichier [0-9a-f-]+', 'cible X', t); t = re.sub(r'\$[0-9a-f]{6}\.L', '$ADR.L', t)
    t = re.sub(r'T_[0-9a-f]{6}', 'T_X', t); t = re.sub(r'\[PS2 [0-9a-f]+\]', '', t)
    return t.strip()
U = lire(os.path.join(G, 'fige/ro5/carte_image.txt'), up); Gf = lire(os.path.join(P, 'b9/carte_image.txt'), gr)
a = ["%x %s" % (k, norm(t)) for k, t in U]; b = ["%x %s" % (k, norm(t)) for k, t in Gf]
d = [l for l in difflib.unified_diff(a, b, lineterm='', n=0) if l[:1] in '+-' and not l.startswith(('+++', '---'))]
with open(os.path.join(P, 'comparaison_68k.txt'), 'w') as f:
    f.write("instructions 68K : Upper %d, greffe %d ; lignes differentes (normalisees) : %d\n" % (len(U), len(Gf), len(d)))
    for l in d: f.write(l + "\n")
print("instructions 68K : Upper %d, greffe %d ; lignes differentes : %d (dont A5 : %d)" % (len(U), len(Gf), len(d), sum(1 for l in d if '(A5)' in l)))
