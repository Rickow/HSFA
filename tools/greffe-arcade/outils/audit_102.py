#!/usr/bin/env python3
"""ETAPE 5 : acces au champ $102 (id perso, numerotation PS2 ; $0103 en 68K, octet XOR 1) dans le code a greffer
(coeur de l'etape 2) et dans les routines d'Hyper reutilisees sur le chemin Arcade. Classement sur la TRADUCTION 68K
(mode cps2) : instruction qui lit $0103(An), puis usage du registre D lu dans les 8 instructions suivantes :
  CMP    : CMPI/CMP sur $0103(An) ou sur le Dn lu       -> $116 si la constante est un id de base (< $28)
  INDEX  : ADD Dn,Dn / LSL / (An,Dn) / MULU             -> $116 (table par perso de base : 40 entrees)
  COPIE  : MOVE.B Dn,<ailleurs>                         -> garder $102 (version) ET recopier $116/$117
  ECRITURE : MOVE.x ...,$0103(An)                       -> poser aussi $116/$117 (perso de base)
  TEST   : TST.B $0103(An) ; AUTRE : a examiner
(l'ancienne version, par motifs MIPS, est audit_102_mips.py). Sortie : donnees/audit_102.tsv + resume."""
import os, sys, pickle, re, collections, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["MEMMODE"] = "cps2"
G = "<workspace>/work/greffe_arcade"
sys.path.insert(0, os.path.join(G, 'untranspile'))
import translate as T
import greffe as GR
import commun as C

def lignes68(mod, a, b):
    buf = C.load(mod)
    with contextlib.redirect_stdout(io.StringIO()):
        out, _ = T.translate(buf, max(a - 0x200, 0x22b00), b + 0x100)
    return [(va, t) for va, t, ws in out if a <= va < b and not t.startswith('(')]

RD = re.compile(r'^MOVE\.[BW] \$0103\(A(\d)\),D(\d)')
def classe(L, i):
    va, t = L[i]
    if re.search(r',\$0103\(A\d\)', t) and (t.startswith('MOVE') or t.startswith('CLR')): return 'ECRITURE', t
    if t.startswith('CLR.B $0103'): return 'ECRITURE', t
    m = re.search(r'^CMPI?\.B (#\$[0-9a-f]+),\$0103\(A\d\)', t)
    if m: return 'CMP', m.group(1)
    if t.startswith('TST.B $0103'): return 'TEST', ''
    if re.search(r'^MOVE\.B \$0103\(A\d\),[-$]', t): return 'COPIE', t.split(',')[-1]   # memoire -> memoire
    if re.search(r'^CMP\.B \$0103\(A\d\),D\d', t): return 'CMP', 'registre'
    if re.search(r'^ADD\.B \$0103\(A\d\),D\d', t): return 'INDEX', 'ADD.B (calcul d\'index)'
    m = RD.search(t)
    if not m: return 'AUTRE', t
    dn = 'D' + m.group(2)
    for va2, t2 in L[i + 1:i + 9]:
        m2 = re.search(r'CMPI?\.[BW] (#\$[0-9a-f]+),%s\b' % dn, t2)
        if m2: return 'CMP', m2.group(1)
        if re.search(r'^CMP\.[BW] .*,%s\b' % dn, t2): return 'CMP', t2
        if re.search(r'(\(PC,%s\.W\)|ADDI\.W #\$[0-9a-f]+,%s|ADD\.[WL] %s,%s|LS[LR]\.[WL] #\$?\d+,%s|\(A\d,%s\.[WL]\)|MULU.*%s|ASL.*%s)' % (dn, dn, dn, dn, dn, dn, dn, dn), t2): return 'INDEX', t2
        if re.search(r'^MOVE\.B %s,' % dn, t2): return 'COPIE', t2
        if re.search(r',%s\b' % dn, t2) and not t2.startswith(('ANDI', 'EXT')): return 'AUTRE', t2
    return 'AUTRE', ''

def main():
    L = pickle.load(open(os.path.join(G, 'donnees', 'liste_arcade.pkl'), 'rb'))
    greffer = pickle.load(open(os.path.join(G, 'donnees', 'coeur_greffe.pkl'), 'rb'))
    reuse = sorted({l['part'] for l in L['lignes'] if l['decision'].startswith('REUTILISER') and not l['vs'] and l['part']
                    and not l['zone'].startswith(('code des persos', 'moteur de combat', 'intro'))
                    and not all(x.startswith('hors partie') for x in l['scenes'])})
    F9 = dict(C.funcs('ro9')); res = []
    for mod, rs, fin in (('ro5', greffer, lambda a: GR.INV[a]['b']), ('ro9', reuse, lambda a: F9[a])):
        os.environ['MODULE'] = mod
        for a in rs:
            Lg = lignes68(mod, a, fin(a))
            for i, (va, t) in enumerate(Lg):
                if '$0103(A' in t:
                    c, det = classe(Lg, i); res.append((mod, a, va, c, det, t))
    with open(os.path.join(G, 'donnees', 'audit_102.tsv'), 'w') as f:
        f.write("module\troutine\tva\tclasse\tdetail\tinstruction_68K\n")
        for r in res: f.write("%s\t0x%X\t0x%X\t%s\t%s\t%s\n" % r)
    for mod in ('ro5', 'ro9'):
        c = collections.Counter(r[3] for r in res if r[0] == mod)
        print("%s : %d acces a $102 dans %d routines : %s" % ('ro5 (code greffe)' if mod == 'ro5' else 'ro9 (homologues reutilises)',
              sum(c.values()), len({r[1] for r in res if r[0] == mod}), dict(c)))

if __name__ == "__main__":
    main()
