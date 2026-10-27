#!/usr/bin/env python3
"""FERMETURE ET BORNES DES DONNEES COPIEES (etape 2, point 4).

Sources d'Upper : donnees du module (exec [fin du code, fin des donnees)) et fichier 390 (frames, charge a $B04000).
  - segments de depart : constantes de donnees formees par le code greffe ;
  - segment = [debut, frontiere suivante), frontieres = constantes de donnees de tout le code d'Upper + debut du
    fichier 390 + cibles des pointeurs decouverts ; plafond PLAFOND_SEG (8 Ko) ;
  - pointeur candidat = long aligne visant une source d'Upper (moitie haute >= $60) ; sa cible devient un segment ;
  - REUTILISATION : segment identique (pointeurs masques) dans les donnees d'Hyper ou son fichier 547 ($C84000) ->
    adresse d'Hyper, non parcouru ;
  - PREUVE DYNAMIQUE (bornes) : avec un journal des donnees lues par Upper (lua/donnees_lues.lua), un segment
    atteint seulement par pointeur n'est copie que s'il a ete LU par Upper ; sinon le pointeur est laisse tel quel
    (journal « non suivi »).
Bibliotheque : Fermeture(depart, lu).segments / .pointeurs / .reutil / .non_suivis ; .bloc(g, x) -> (blob, ptr_code, plages)."""
import os, sys, struct, bisect, collections, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as PL
import greffe as GR
BASE = GR.BASE; H5 = GR.H5; H9 = GR.H9
LO, HI = BASE + H5['code_end'], H5['data_end']
F390 = 0xB04000
CACHE = "<workspace>/work/cps2/anims"
B390 = open(os.path.join(CACHE, 'f390.bin'), 'rb').read()
B547 = open(os.path.join(CACHE, 'f547.bin'), 'rb').read()
F390_1 = F390 + len(B390)
F547 = 0xC84000
PLAFOND = int(os.environ.get("PLAFOND_SEG", "8192"))
# disposition des donnees d'Upper dans l'image 68K (construction temoin u5 = fige/ro5, md5 a296538f...)
U_DATA_BASE, U_SPLIT, U_EXT = 0xA1000, 0x8E4AE0, 0xC80000

def source(v):
    if LO <= v < HI: return 'module'
    if F390 <= v < F390_1: return '390'
    return None

def octets(v, n):
    if LO <= v < HI: return PL.b5[v - BASE:v - BASE + n]
    return B390[v - F390:v - F390 + n]

def fin_source(v): return HI if LO <= v < HI else F390_1

def masque(b):
    seg = bytearray(b)
    for i in range(0, len(seg) - 3, 4):
        x = struct.unpack_from('<I', seg, i)[0]
        if 0x200000 <= x < 0x1000000: seg[i:i + 4] = b'PPPP'
    return bytes(seg)

@functools.lru_cache(None)
def index9():
    """donnees d'Hyper (module et fichier 547) : 16 octets masques -> adresses d'execution"""
    idx = collections.defaultdict(list)
    for base, b in ((BASE + H9['code_end'], PL.b9[H9['code_end']:H9['data_end'] - BASE]), (F547, B547)):
        m = masque(b)
        for i in range(0, len(m) - 16, 4):
            k = m[i:i + 16]
            if k == bytes(16) or k == b'PPPP' * 4: continue
            l = idx[k]
            if len(l) < 4: l.append((base, i))
    return idx

def octets9(a, n):
    if F547 <= a < F547 + len(B547): return B547[a - F547:a - F547 + n]
    return PL.b9[a - BASE:a - BASE + n]

def homologue_donnee(v, n):
    if n < 16: return None
    m = masque(octets(v, n))
    if m[:16] == bytes(16): return None
    # meme alignement (modulo 4) que chez Upper : sinon les pointeurs vers l'interieur du segment changent de parite
    ok = [base + i for base, i in index9().get(m[:16], []) if (base + i - v) % 4 == 0 and masque(octets9(base + i, n)) == m]
    return ok[0] if len(ok) == 1 else None

def lu_ps2(chemins):
    """journaux d'adresses 68K lues par Upper -> ensemble d'adresses d'execution PS2 (granularite 2 octets)"""
    out = set()
    for c in chemins:
        for l in open(c):
            a = int(l, 16)
            if U_DATA_BASE <= a < U_DATA_BASE + (U_SPLIT - LO): v = LO + (a - U_DATA_BASE)
            elif U_EXT <= a < U_EXT + (HI - U_SPLIT): v = U_SPLIT + (a - U_EXT)
            elif F390 <= a < F390_1: v = a
            else: continue
            out.add(v & ~1)
    return out

class Fermeture:
    def __init__(self, depart, lu=None, reutil=True):
        self.lu = lu; lus = sorted(lu) if lu else None
        def lu_dans(a, b):
            if lus is None: return True
            k = bisect.bisect_left(lus, a); return k < len(lus) and lus[k] < b
        REFS = set(PL.refs_donnees5())
        front = REFS | {HI, F390, F390_1}
        self.segments = {}; self.pointeurs = {}; self.reutil = {}; self.non_suivis = collections.Counter()
        depart = {v for v in depart if source(v)}
        todo = sorted(depart); vus = set()
        Fl = sorted(front)
        while todo:
            v = todo.pop()
            if v in vus: continue
            vus.add(v)
            k = bisect.bisect_right(Fl, v)
            fin = min(Fl[k] if k < len(Fl) else fin_source(v), v + PLAFOND, fin_source(v))
            if reutil:
                h = homologue_donnee(v, fin - v)
                if h is not None: self.reutil[v] = (h, fin - v); continue
            if v not in depart and not lu_dans(v, fin):
                self.non_suivis[v] += 1; continue
            self.segments[v] = fin - v
            if v & 3: continue
            b = octets(v, fin - v)
            # table de petits mots (decalages, coordonnees) : ses longs ne sont pas des pointeurs (paires de mots
            # $0058 $006A = $006A0058 tomberait dans les donnees d'Upper)
            nl = max(1, (fin - v) // 4)
            petits = sum(1 for i in range(0, fin - v - 3, 4) if (struct.unpack_from('<I', b, i)[0] & 0xF000F000) == 0) / nl
            for i in range(0, fin - v - 3, 4):
                p = struct.unpack_from('<I', b, i)[0]
                if source(p) and (p >> 16) >= 0x60 and (p in REFS or (p & 0xffff) >= 0x200):
                    self.pointeurs[(v, i)] = p
                    if p not in front: front.add(p); bisect.insort(Fl, p)
                    if p not in vus: todo.append(p)
        # bornes definitives (frontieres finales)
        for v in list(self.segments):
            k = bisect.bisect_right(Fl, v); fin = min(Fl[k] if k < len(Fl) else fin_source(v), v + PLAFOND, fin_source(v))
            self.segments[v] = fin - v
        self.pointeurs = {(v, i): p for (v, i), p in self.pointeurs.items() if v in self.segments and i + 4 <= self.segments[v]}

    def regions(self, ecart=None):
        """REGIONS CONTIGUES : segments voisins (ecart < ECART_REGION) et adresses lues par Upper a proximite, copies
        d'un seul tenant. Les tables d'animation d'Upper sont des tables de DECALAGES 16 bits relatifs a la table
        (0xC8510 : A0 += table[i]) : leurs cibles doivent garder la meme distance a la table."""
        ecart = ecart or int(os.environ.get("ECART_REGION", "400"), 16)
        pts = sorted((v, v + n) for v, n in self.segments.items())
        if self.lu:
            lus = sorted(self.lu)
        R = []
        for a, b in pts:
            if R and a - R[-1][1] < ecart and source(a) == source(R[-1][0]): R[-1][1] = max(R[-1][1], b)
            else: R.append([a, b])
        if self.lu:                                   # prolonge chaque region jusqu'aux lectures voisines
            for r in R:
                k = bisect.bisect_left(lus, r[1])
                while k < len(lus) and lus[k] - r[1] < ecart and source(lus[k]) == source(r[0]):
                    r[1] = max(r[1], lus[k] + 2); k += 1
            R2 = []
            for a, b in R:
                if R2 and a <= R2[-1][1]: R2[-1][1] = max(R2[-1][1], b)
                else: R2.append([a, b])
            R = R2
        return [(a, min(b, fin_source(a))) for a, b in R]

    def bloc(self, g, x, trou=None):
        """bloc ajoute (exec x) : regions copiees d'un seul tenant, pointeurs reloges ; renseigne g.data"""
        blob = bytearray(); off = {}; self.reg = self.regions()
        rv = [a for a, b in self.reg]; roff = {}
        for a, b in self.reg:
            o = ((len(blob) + 15) & ~15) + (a & 15)    # meme alignement (modulo 16) que chez Upper
            if trou and x + o < trou[1] and x + o + (b - a) > trou[0]:     # region qui chevaucherait le trou reserve
                o = (trou[1] - x) + (a & 15)
            blob += bytes(o - len(blob)); roff[a] = o
            blob += octets(a, b - a)
        self.roff = roff
        for v in self.segments:
            k = bisect.bisect_right(rv, v) - 1; a, b = self.reg[k]; assert a <= v < b
            off[v] = roff[a] + (v - a)
        plages = {(a, b): x + roff[a] for a, b in self.reg}
        for v, (h, n) in self.reutil.items(): plages[(v, v + n)] = h
        sv = sorted(plages); dv = [a for a, _ in sv]
        def ou(p):
            k = bisect.bisect_right(dv, p) - 1
            if k >= 0 and sv[k][0] <= p < sv[k][1]: return plages[sv[k]] + (p - sv[k][0])
            return None
        g.data = {v: x + off[v] for v in self.segments}
        g.data.update({v: h for v, (h, n) in self.reutil.items()})
        g.data['_plages'] = plages
        ptr_code = []; stat = collections.Counter()
        REFS = set(PL.refs_donnees5())
        # TOUTES les regions copiees sont parcourues (pas seulement les segments : les regions sont prolongees jusqu'aux
        # lectures voisines), longs alignes comme chez Upper
        for a_r, b_r in self.reg:
            b = octets(a_r, b_r - a_r)
            for i in range((-a_r) & 3, b_r - a_r - 3, 4):
                v, o = a_r, roff[a_r] + i
                p = struct.unpack_from('<I', b, i)[0]
                if source(p) and (p >> 16) >= 0x60 and (p in REFS or (p & 0xffff) >= 0x200):
                    q = ou(p)
                    if q is None: stat['donnee non suivie'] += 1; continue
                    struct.pack_into('<I', blob, o, q); stat['donnee relogee'] += 1
                    continue
                cl = GR.classe_valeur(p, GR.H5)
                if cl == 'code' and (p & 0xffff) < 0x100 and (p - BASE) not in PL.E5: continue   # paire de mots ($0008 $0060)
                if cl == 'code' and not ((p - BASE) in PL.E5 or g.neuf(p - BASE) is not None) and not (p & 3):
                    a_ = PL.routine_de(p - BASE); d_ = g.D.get(a_)
                    if d_ and d_[0] == 'HYPER' and isinstance(d_[1], int) and PL.E5[a_] - a_ == PL.E9.get(d_[1], 0) - d_[1]:
                        struct.pack_into('<I', blob, o, d_[1] + (p - BASE - a_) + BASE); ptr_code.append(o); stat['code milieu homologue'] += 1
                    else: stat['code milieu laisse'] += 1
                    continue
                if cl == 'code' and ((p - BASE) in PL.E5 or g.neuf(p - BASE) is not None):
                    q = g.valeur(p, ('donnee', v + i))
                    if q is not None: struct.pack_into('<I', blob, o, q); ptr_code.append(o); stat['code'] += 1
                elif cl == 'ram' and not (p & 1):
                    q = g.valeur(p, ('donnee', v + i))
                    if q is not None and q != p: struct.pack_into('<I', blob, o, q); stat['ram'] += 1
        self.stat = stat
        return bytes(blob), ptr_code, plages

if __name__ == "__main__":
    import glob, force as FO
    rac = [0x4E1C0, 0x24EA30, 0x261560, 0x2614A0, 0x2614D0, 0x261500]
    TC = PL.tables_a_completer()
    P = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FO.FORCE)
    lj = sorted(glob.glob(os.path.join(PL.G, 'traces', 'u_lu*', 'lu.txt')))
    lu = lu_ps2(lj) if lj else None
    F = Fermeture(P.donnees, lu)
    print("journaux de lecture : %s (%d adresses)" % ([os.path.basename(os.path.dirname(x)) for x in lj], len(lu or ())))
    print("segments copies %d, %d o (%.1f Ko) ; pointeurs %d ; reutilises %d ; non suivis (jamais lus) %d" % (
        len(F.segments), sum(F.segments.values()), sum(F.segments.values()) / 1024, len(F.pointeurs), len(F.reutil), len(F.non_suivis)))
