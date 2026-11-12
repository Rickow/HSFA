#!/usr/bin/env python3
"""FERMETURE DES DONNEES (etape 2, point 4) : segments de donnees d'Upper a copier pour le code greffe.
  - depart : constantes de donnees formees par le code greffe (plan) ;
  - segment = [debut, frontiere suivante) ; frontieres = constantes de donnees de tout le code d'Upper + cibles des
    pointeurs decouverts ; plafond PLAFOND octets par segment ;
  - pointeur candidat = long aligne d'un segment copie qui vise les donnees d'Upper (exec [fin du code, fin des
    donnees)), et n'est pas une paire de mots a moitie haute < $60 ; sa cible devient un segment (fermeture) ;
  - pointeurs de code (debut de routine) : decisions du plan ; pointeurs RAM : rebasees.
Bibliotheque : ferme_donnees(depart) -> (segments {debut: taille}, pointeurs {(debut, decalage): cible})."""
import os, sys, struct, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as PL
import greffe as GR
BASE = GR.BASE; H5 = GR.H5
LO, HI = BASE + H5['code_end'], H5['data_end']
PLAFOND = int(os.environ.get("PLAFOND_SEG", "8192"))

def masque(b, o, n):
    seg = bytearray(b[o:o + n])
    for i in range(0, len(seg) - 3, 4):
        v = struct.unpack_from('<I', seg, i)[0]
        if 0x200000 <= v < 0x1000000: seg[i:i + 4] = b'PPPP'
    return bytes(seg)

_IDX = None
def index9():
    """donnees d'Hyper : 16 octets masques (pointeurs) -> decalages fichier (4-alignes)"""
    global _IDX
    if _IDX is None:
        b9 = PL.b9; h = GR.H9; o0 = h['code_end']; o1 = h['data_end'] - BASE
        m = masque(b9, o0, o1 - o0); _IDX = collections.defaultdict(list)
        for i in range(0, len(m) - 16, 4):
            k = m[i:i + 16]
            if k == bytes(16) or k == b'PPPP' * 4: continue
            l = _IDX[k]
            if len(l) < 4: l.append(o0 + i)
    return _IDX

def homologue_donnee(v, n):
    """adresse d'execution d'Hyper ou le segment d'Upper [v, v+n) existe a l'identique (pointeurs masques), sinon None"""
    if n < 16: return None
    m = masque(PL.b5, v - BASE, n)
    if m[:16] == bytes(16): return None
    cands = index9().get(m[:16], [])
    ok = [o for o in cands if masque(PL.b9, o, n) == m]
    return ok[0] + BASE if len(ok) == 1 else None

def ferme_donnees(depart, max_total=3 << 20, reutil=True):
    b5 = PL.b5; REU = {}
    front = set(PL.refs_donnees5()); front.add(HI)
    seg = {}; ptrs = {}; todo = sorted(set(depart)); vus = set(); depart_set = set()
    while todo:
        v = todo.pop()
        if v in vus: continue
        # deja a l'interieur d'un segment ? (debut inferieur, pas de frontiere entre)
        vus.add(v)
        F = sorted(front); k = bisect.bisect_right(F, v)
        fin = min(F[k] if k < len(F) else HI, v + PLAFOND, HI)
        if reutil and v not in depart_set:
            h = homologue_donnee(v, fin - v)
            if h is not None: REU[v] = h; continue
        seg[v] = fin - v
        if v & 3: continue
        for i in range(0, fin - v - 3, 4):
            p = struct.unpack_from('<I', b5, v - BASE + i)[0]
            if LO <= p < HI and (p >> 16) >= 0x60:
                ptrs[(v, i)] = p
                if p not in front:
                    front.add(p)
                if p not in vus: todo.append(p)
        if sum(seg.values()) > max_total: break
    # re-borne les segments avec les frontieres finales, fusionne les inclus
    F = sorted(front); out = {}
    for v in sorted(seg):
        k = bisect.bisect_right(F, v); fin = min(F[k] if k < len(F) else HI, v + PLAFOND, HI)
        out[v] = fin - v
    return out, ptrs, REU

if __name__ == "__main__":
    import force as FO
    rac = [0x4E1C0, 0x24EA30, 0x261560, 0x2614A0, 0x2614D0, 0x261500]
    TC = PL.tables_a_completer()
    P = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FO.FORCE)
    S, Pt, RE = ferme_donnees(P.donnees)
    print("segments copies %d, %d o (%.1f Ko) ; pointeurs %d ; segments reutilises (identiques dans Hyper) %d" % (len(S), sum(S.values()), sum(S.values()) / 1024, len(Pt), len(RE)))
    c = collections.Counter(v >> 16 for v in S)
    print(sorted((hex(k << 16), n) for k, n in c.items()))
