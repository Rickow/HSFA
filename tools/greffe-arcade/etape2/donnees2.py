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
    # (etape 6) REUTIL_STRICT=1 : segment surtout fait de « pointeurs » masques (flux de palettes : $0042 $0140 =
    # $01400042) -> la ressemblance masquee ne prouve rien : reutilise seulement si les octets sont IDENTIQUES (fin du
    # perso $21 : flux lu dans des donnees d'Hyper sans rapport)
    if REUTIL_STRICT and m.count(b'PPPP') * 4 * 4 > len(m):
        ok = [base + i for base, i in index9().get(m[:16], []) if (base + i - v) % 4 == 0 and octets9(base + i, n) == octets(v, n)]
        return ok[0] if len(ok) == 1 else None
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

# (etape 3) CRITERE DE POINTEUR : PREUVES=<fichier> (cases exec dont le long est un pointeur PROUVE par le journal des
# conversions d'Upper, etape3/preuve_ptrs.py) ; FILTRE3=1 : un long non prouve et hors des constantes du code n'est
# plus pris pour un pointeur s'il est IMPAIR ou si sa moitie basse vaut $FE00-$FFFF (paire de mots signes :
# coordonnees $FF25,$0083 de T_6139A4...). Sans ces variables : comportement de l'etape 2.
LIB_SPANS = [int(x, 16) for x in os.environ.get("LIB_SPANS", "69b830,69f3b0,6cf5f0,6ef3f0,72bdf0,739690,7442d0,745540,747ee0,747f30,7480d4,748344,95fe60").split(',') if x]   # (etape 5) bibliotheques de blocs des plans
DEC_PETITES = os.environ.get("DEC_PETITES", "1") == "1"   # (etape 5) petites tables de decalages aussi
DEC_GRANDES = os.environ.get("DEC_GRANDES", "1") == "1"   # (etape 5) grandes tables de decalages 16 bits (animations)
PTR_VOISIN = os.environ.get("PTR_VOISIN", "0") == "1"   # (etape 4) cible hors entree : seulement dans une table
# (etape 4) PTR_INSTR=1 : une cible de pointeur de code qui n'est pas une entree de routine doit etre un DEBUT
# D'INSTRUCTION 68K dans la traduction d'Upper (carte du temoin v149 u5_temoin7) : $00304200 (paire $4200 $0030 du script
# de fin de Ken) visait 0x114200, au milieu d'une instruction -> laisse
PTR_INSTR = os.environ.get("PTR_INSTR", "0") == "1"   # 1 : casse le demarrage (e6m)
@functools.lru_cache(None)
def instr5():
    c = os.environ.get("CARTE5", "<workspace>/work/greffe_arcade/constructions/u5_temoin7/carte_image.txt")
    return frozenset(int(l.split()[1], 16) for l in open(c) if len(l.split()) > 1)
# (etape 4) PTR_EXCLUS=<fichier> : cases (exec PS2 d'Upper) dont le long n'est JAMAIS un pointeur de code (paires de mots
# de scripts de fin trouvees par etape4/compare_script.py) ; defaut donnees/ptr_exclus.txt s'il existe
_PX = os.environ.get("PTR_EXCLUS", "<workspace>/work/greffe_arcade/donnees/ptr_exclus.txt")
PTR_EXCLUS = set(int(l.split()[0], 16) for l in open(_PX) if l.strip() and not l.startswith('#')) if os.path.exists(_PX) else set()
# (etape 7) DESC_FIN=1 : + champ +$18 des descripteurs d'acteurs de fin (donnees/ptr_exclus_desc.txt) : 4 octets de plages
# de palettes ($00484F48...) pris pour des pointeurs ; l'octet +$79 de l'objet (delai d'apparition) dependait alors de
# l'adresse du code greffe (fin de Ken cassee des que le code grossit)
_PD = "<workspace>/work/greffe_arcade/donnees/ptr_exclus_desc.txt"
if os.environ.get("DESC_FIN", "1") == "1" and os.path.exists(_PD):
    PTR_EXCLUS |= set(int(l.split()[0], 16) for l in open(_PD) if l.strip() and not l.startswith('#'))
REUTIL_STRICT = os.environ.get("REUTIL_STRICT", "0") == "1"   # (etape 6) reutilisation d'Hyper sans masque si > 25 % de pointeurs
BANQUES_LU = os.environ.get("BANQUES_LU", "1") == "1"
TEXTES_LU = os.environ.get("TEXTES_LU", "1") == "1"
BLOC_RESTES = os.environ.get("BLOC_RESTES", "1") == "1"   # (etape 7) place laissee avant une coupure reutilisee   # (etape 7) banques de textes copiees jusqu'au dernier texte lu
REUTIL_VOISIN = os.environ.get("REUTIL_VOISIN", "0") == "1"   # (etape 7) cible non suivie reutilisee au decalage du voisin
FE_TABLE = os.environ.get("FE_TABLE", "1") == "1"   # (etape 6) pointeurs $xxxxFExx en table acceptes
PTR_BAS = os.environ.get("PTR_BAS", "1") == "1"   # (etape 6) pointeurs de code a moitie basse < $100 : seulement en table
PTR_ALIGNE = os.environ.get("PTR_ALIGNE", "1") == "1"   # (etape 4) pointeurs de code alignes seulement
PREUVES = set(int(l, 16) for l in open(os.environ["PREUVES"])) if os.environ.get("PREUVES") else set()
FILTRE3 = os.environ.get("FILTRE3") == "1"
OU3 = os.environ.get("OU3") == "1"
TABLES_PTR = os.environ.get("TABLES_PTR") == "1"
DECALAGES16 = os.environ.get("DECALAGES16") == "1"
SEG_REFS = os.environ.get("SEG_REFS") == "1"             # (etape 3) bases du code greffe copiees jusqu'a la constante
PLAFOND_REFS = int(os.environ.get("PLAFOND_REFS", "8000"), 16)     # de code suivante (plafond 32 Ko)
PLAFOND_DEC = int(os.environ.get("PLAFOND_DEC", "10000"), 16)      # tables de decalages 16 bits (plafond 64 Ko)
def est_pointeur(case, p, REFS):
    if not source(p): return False
    if case in PREUVES: return True
    if not ((p >> 16) >= 0x60 and (p in REFS or (p & 0xffff) >= 0x200)): return False
    if FILTRE3 and p not in REFS and ((p & 1) or (p & 0xffff) >= 0xFE00):
        # (etape 6) FE_TABLE=1 : moitie basse $FExx dans une TABLE de pointeurs (voisin aligne de meme moitie haute, pair,
        # dans la source) : vrai pointeur (table de scenes de la fin du perso $21 : $0099FE18... non reloges -> CONV les
        # envoyait dans les donnees d'Hyper)
        if FE_TABLE and not (p & 1) and source(case) == 'module':
            for d in (-4, 4):
                c2 = case + d
                if not source(c2): continue
                q = struct.unpack_from('<I', octets(c2, 4))[0]
                if (q >> 16) == (p >> 16) and not (q & 1) and source(q): return True
        return False
    return True

class Fermeture:
    def __init__(self, depart, lu=None, reutil=True):
        self.lu = lu; lus = sorted(lu) if lu else None
        def lu_dans(a, b):
            if lus is None: return True
            k = bisect.bisect_left(lus, a); return k < len(lus) and lus[k] < b
        REFS = set(PL.refs_donnees5())
        front = REFS | {HI, F390, F390_1}
        self.REFSL = sorted(REFS | {HI, F390, F390_1}); self.depart = depart
        self.segments = {}; self.pointeurs = {}; self.reutil = {}; self.non_suivis = collections.Counter()
        self.cibles_prouvees = set()                  # (etape 3) cibles de pointeurs prouves : suivies meme non lues
        depart = {v for v in depart if source(v)}
        # (etape 7) BANQUES_LU=1 : animations des banques par perso (T_619B50 : base + decalage 16 bits) lues par Upper :
        # departs de la fermeture (leurs pointeurs d'images sont suivis), jamais reutilisees chez Hyper (base + decalage
        # doit tomber dans la copie de la banque)
        self.bq_cibles = set(); self.bq_bases = []
        if BANQUES_LU and lu:
            TB = sorted(set(x for x in struct.unpack('<46I', octets(0x619B50, 184)) if source(x) == 'module'))
            self.bq_bases = TB
            for j, base in enumerate(TB):
                lim = TB[j + 1] if j + 1 < len(TB) else fin_source(base)
                w0 = struct.unpack('<H', octets(base, 2))[0]
                if w0 & 1 or not 0x10 <= w0 <= 0x1000: continue
                for x_ in struct.unpack('<%dH' % (w0 // 2), octets(base, w0)):
                    t_ = base + x_
                    if x_ and not x_ & 1 and base + w0 <= t_ < lim and any((t_ + d_) in lu for d_ in range(0, 8, 2)):
                        self.bq_cibles.add(t_)
            depart |= self.bq_cibles
        # (etape 7) TEXTES_LU=1 : banques de textes par langue (T_614E10 : base + decalage 16 bits, decalages impairs)
        # lues par Upper : chaque banque prolongee jusqu'a la fin du dernier texte lu (fin de 17 : texte 0x6950ED hors
        # copie, base + decalage tombait dans une autre region -> rendu de texte sans fin, RAM ecrasee)
        self.tx_ext = []
        if TEXTES_LU and lu:
            lus_ = sorted(lu)
            TX = sorted(set(x for x in struct.unpack('<4I', octets(0x614E10, 16)) if source(x) == 'module'))
            for j, base in enumerate(TX):
                lim = min(TX[j + 1] if j + 1 < len(TX) else fin_source(base), base + 0x10000)
                w0 = struct.unpack('<H', octets(base, 2))[0]
                if w0 & 1 or not 0x10 <= w0 <= 0x1000: continue
                fin = 0
                for x_ in struct.unpack('<%dH' % (w0 // 2), octets(base, w0)):
                    t_ = base + x_
                    if not (x_ and base + w0 <= t_ < lim): continue
                    k_ = bisect.bisect_left(lus_, t_ & ~1)
                    if k_ < len(lus_) and lus_[k_] <= (t_ & ~1) + 6:
                        e_ = lus_[k_]
                        while k_ + 1 < len(lus_) and lus_[k_ + 1] - e_ <= 8: k_ += 1; e_ = lus_[k_]
                        fin = max(fin, min(e_ + 0x10, lim))
                if fin: self.tx_ext.append((base, fin))
        todo = sorted(depart); vus = set()
        Fl = sorted(front)
        while todo:
            v = todo.pop()
            if v in vus: continue
            vus.add(v)
            k = bisect.bisect_right(Fl, v)
            fin = min(Fl[k] if k < len(Fl) else fin_source(v), v + PLAFOND, fin_source(v))
            if reutil and v not in self.bq_cibles:
                h = homologue_donnee(v, fin - v)
                if h is not None: self.reutil[v] = (h, fin - v); continue
            if v not in depart and not lu_dans(v, fin) and v not in self.cibles_prouvees:
                self.non_suivis[v] += 1; continue
            self.segments[v] = fin - v
            if v & 3: continue
            b = octets(v, fin - v)
            # table de petits mots (decalages, coordonnees) : ses longs ne sont pas des pointeurs (paires de mots
            # $0058 $006A = $006A0058 tomberait dans les donnees d'Upper)
            nl = max(1, (fin - v) // 4)
            petits = sum(1 for i in range(0, fin - v - 3, 4) if (struct.unpack_from('<I', b, i)[0] & 0xF000F000) == 0) / nl
            # (etape 3) TABLES_PTR=1 : segment qui est une TABLE DE POINTEURS (>= 4 longs, >= 75 % de pointeurs au
            # sens d'est_pointeur) : toutes ses cibles sont suivies, meme jamais lues par Upper (citations, textes,
            # scripts par perso : les parties journalisees ne les lisent pas toutes)
            if TABLES_PTR:
                nl_ = (fin - v) // 4
                np_ = sum(1 for i in range(0, fin - v - 3, 4) if est_pointeur(v + i, struct.unpack_from('<I', b, i)[0], REFS))
                table_ptr = nl_ >= 4 and np_ * 4 >= nl_ * 3
            else: table_ptr = False
            for i in range(0, fin - v - 3, 4):
                p = struct.unpack_from('<I', b, i)[0]
                if est_pointeur(v + i, p, REFS):
                    if v + i in PREUVES or table_ptr: self.cibles_prouvees.add(p)
                    self.pointeurs[(v, i)] = p
                    if p not in front: front.add(p); bisect.insort(Fl, p)
                    if p not in vus: todo.append(p)
        # (etape 7) REUTIL_VOISIN=1 : cible NON SUIVIE (jamais lue par Upper, homologue ambigu) dont le segment voisin le
        # plus proche (< $1000) est reutilise chez Hyper avec un decalage d : reutilisee a v + d si le contenu masque y est
        # identique (images d'animation de l'acteur de fin de Ken, 0x7B87C0/0x7B87DC : voisines de 0x7B8794 -> 0x6DAFCC,
        # restees en adresse brute d'Upper -> lecture impaire dans le dessin d'Hyper 0x393D40)
        if REUTIL_VOISIN and reutil and self.reutil:
            RK = sorted(self.reutil)
            for v in sorted(self.non_suivis):
                if v & 3: continue
                k = bisect.bisect_left(RK, v); cands = [RK[j] for j in (k - 1, k) if 0 <= j < len(RK)]
                cands = sorted((abs(c - v), c) for c in cands if abs(c - v) < 0x1000)
                if not cands: continue
                c = cands[0][1]; d = self.reutil[c][0] - c
                kf = bisect.bisect_right(Fl, v); fin = min(Fl[kf] if kf < len(Fl) else fin_source(v), v + PLAFOND, fin_source(v))
                n = fin - v
                if n < 16: continue
                m = masque(octets(v, n)); h = v + d
                if len(octets9(h, n)) == n and masque(octets9(h, n)) == m:
                    self.reutil[v] = (h, n); del self.non_suivis[v]; self.n_voisin = getattr(self, 'n_voisin', 0) + 1
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
        if SEG_REFS:                                  # (etape 3) base visee par le code greffe : copiee (sans suivre ses
            R_ = self.REFSL                           # pointeurs au-dela) jusqu'a la constante de code suivante, plafond
            def fin_refs(v, b):                       # PLAFOND_REFS : tables indexees par decalage (citations, textes)
                kr = bisect.bisect_right(R_, v)
                return max(b, min(R_[kr] if kr < len(R_) else fin_source(v), v + PLAFOND_REFS, fin_source(v)))
            pts = sorted((v, fin_refs(v, b) if v in self.depart else b) for v, b in pts)
        if DECALAGES16:                               # (etape 3) segment qui commence par une TABLE DE DECALAGES 16 bits
            def fin_dec(v, b):                        # relatifs (>= 8 mots pairs, non decroissants, au-dela de la table,
                if v & 1: return b                    # ex. citations : base 0x67E2A0, Blanka +$2A12) : copie jusqu'au
                w = [struct.unpack_from('<H', octets(v + 2 * i, 2))[0] for i in range(min(64, (fin_source(v) - v) // 2))]
                n = 0                                 # plus grand decalage + $800 (plafond PLAFOND_REFS)
                while n < len(w) and w[n] % 2 == 0 and w[n] >= 2 * len(w[:n + 1]) and (n == 0 or w[n] >= w[n - 1]): n += 1
                if w and w[0] % 2 == 0 and 16 <= w[0] <= 128 and len(w) >= w[0] // 2 and \
                   all(x % 2 == 0 and x >= w[0] for x in w[:w[0] // 2]):
                    n = max(n, w[0] // 2)             # le 1er decalage = taille de la table (40 persos : $50)
                if n < 8: return b
                fin = v + max(w[:n]) + 0x800
                for o in set(w[:n]):                  # 2e niveau (citations : perso -> table de decalages -> texte)
                    t = v + o
                    if t >= fin_source(v) - 32: continue
                    w2 = [struct.unpack_from('<H', octets(t + 2 * i, 2))[0] for i in range(16)]
                    m = 0
                    k2 = w2[0] // 2 if w2[0] % 2 == 0 and 4 <= w2[0] <= 32 else 16   # 1er decalage = taille ; textes :
                    while m < k2 and w2[m] >= 2 * (m + 1) and (m == 0 or w2[m] >= w2[m - 1]) and w2[m] < 0x2000: m += 1   # impairs
                    if m >= 4: fin = max(fin, t + max(w2[:m]) + 0x200)
                return max(b, min(fin, v + PLAFOND_DEC, fin_source(v)))
            pts = sorted((v, fin_dec(v, b)) for v, b in pts)
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
        # (etape 5) LIB_SPANS : BIBLIOTHEQUES INDEXEES du moteur de plans d'Upper (base + index x pas : blocs $300 de
        # 0x6CF5F0 lus par 0x1515C0, 0x69F3B0 par 0x150250, 0x72BDF0 par 0x15BE74) : copiees d'un seul tenant de la base a
        # la derniere lecture d'Upper (avant la constante de code suivante, plafond $40000) ; sinon base + $86 x $300
        # tombait dans une autre region (planisphere fait de tuiles fausses)
        if LIB_SPANS and self.lu:
            lus_ = sorted(self.lu); RE = self.REFSL
            for v in LIB_SPANS:
                kr = bisect.bisect_right(RE, v); lim = min(RE[kr] if kr < len(RE) else v + 0x40000, v + 0x40000, fin_source(v))
                j = bisect.bisect_left(lus_, lim) - 1
                if j >= 0 and lus_[j] > v: R.append([v, lus_[j] + 2])
            R.sort(); R2 = []
            for a, b in R:
                if R2 and a <= R2[-1][1] and source(a) == source(R2[-1][0]): R2[-1][1] = max(R2[-1][1], b)
                else: R2.append([a, b])
            R = R2
        # (etape 5) DEC_GRANDES=1 : une GRANDE table de decalages 16 bits (1er mot ~ sa taille, $80-$1000 ; mots pairs,
        # zeros = entrees vides) n'importe ou dans une region : si ses cibles tombent dans une AUTRE region copiee, les
        # regions entre les deux sont fusionnees (trous compris) pour garder les distances (animations d'Upper 0x816160 :
        # cible +$4C38 dans la region suivante, decalee de $340 -> fin de Ryu). 69 trous, 83 Ko (e7f)
        if DEC_GRANDES:
            R = sorted([list(r) for r in R]); RA = [a for a, b in R]
            def reg_(x):
                k = bisect.bisect_right(RA, x) - 1
                return k if k >= 0 and R[k][0] <= x < R[k][1] else None
            fus = set()
            for k, (a, b) in enumerate(R):
                bb = octets(a, min(b, fin_source(a)) - a)
                for i in range((-a) & 1, len(bb) - 0x80, 2):
                    w0 = struct.unpack_from('<H', bb, i)[0]
                    grande = 0x80 < w0 <= 0x1000
                    if not ((grande or (DEC_PETITES and 0x10 <= w0 <= 0x80)) and w0 % 2 == 0) or a + i + w0 > fin_source(a): continue
                    ws = struct.unpack_from('<%dH' % (w0 // 2), octets(a + i, w0)); nz = [x for x in ws if x]
                    # (etape 5) DEC_PETITES=1 : petites tables ($10-$80 : >= 8 decalages, TOUS pairs et >= w0) aussi
                    if (grande and len(nz) >= 16 and sum(1 for x in nz if x % 2 == 0 and x >= w0 // 2) * 10 >= len(nz) * 9) or \
                       (not grande and len(nz) >= 8 and all(x % 2 == 0 and x >= w0 for x in nz)):
                        for x in nz:
                            if x & 1: continue
                            kk = reg_(a + i + x)
                            if kk is not None and kk != k:
                                j0, j1 = min(k, kk), max(k, kk)
                                if sum(R[j + 1][0] - R[j][1] for j in range(j0, j1)) <= 0x2000: fus.update(range(j0, j1))   # trous <= 8 Ko
            R2 = []
            for k, (a, b) in enumerate(R):
                if R2 and (k - 1) in fus and source(a) == source(R2[-1][0]): R2[-1][1] = max(R2[-1][1], b)
                else: R2.append([a, b])
            R = R2
        # (etape 7) BANQUES_LU=1 : chaque banque (T_619B50) copiee d'un seul tenant de sa base jusqu'a la fin de la derniere
        # animation lue (segments des cibles) ; les CREUX de ce prolongement (ni segment ni lu, >= $100) sont rendus au
        # placement (bloc() y loge d'autres regions) : self.creux = {debut de region : [(a, b) Upper]}
        self.creux = {}
        if (BANQUES_LU and self.bq_cibles) or self.tx_ext:
            TB = self.bq_bases; ext = [(a, b) for a, b in self.tx_ext if any(a_ <= a < b_ for a_, b_ in R)]
            for j, base in enumerate(TB):
                lim = TB[j + 1] if j + 1 < len(TB) else fin_source(base)
                cs = [t for t in self.bq_cibles if base <= t < lim]
                if not cs or not any(a <= base < b for a, b in R): continue
                fin = max(min(t + self.segments.get(t, 0x40), lim) for t in cs)
                ext.append((base, fin))
            R = sorted([list(r) for r in R] + [[a, b] for a, b in ext]); R2 = []
            for a, b in R:
                if R2 and a <= R2[-1][1] and source(a) == source(R2[-1][0]): R2[-1][1] = max(R2[-1][1], b)
                else: R2.append([a, b])
            R = R2
            # creux : dans [base + table, fin) de chaque banque prolongee, hors segments et hors lectures d'Upper
            cov = sorted((v, v + n) for v, n in self.segments.items())
            lus_ = sorted(self.lu) if self.lu else []
            for base, fin in ext:
                k = next(i for i, (a, b) in enumerate(R) if a <= base < b); ra = R[k][0]
                w0 = struct.unpack('<H', octets(base, 2))[0]
                occ = [(a, b) for a, b in cov if b > base and a < fin]
                i_ = bisect.bisect_left(lus_, base)
                while i_ < len(lus_) and lus_[i_] < fin: occ.append((lus_[i_] - 8, lus_[i_] + 10)); i_ += 1
                occ.append((base, base + w0 + 0x10)); occ.sort()
                pos = base
                for a, b in occ:
                    if a - pos >= 0x100: self.creux.setdefault(ra, []).append(((pos + 0x1F) & ~15, (a - 0x10) & ~15))
                    pos = max(pos, b)
                if fin - pos >= 0x100: self.creux.setdefault(ra, []).append(((pos + 0x1F) & ~15, (fin - 0x10) & ~15))
        if self.creux:
            print("banques prolongees : %s ; creux %d o" % (', '.join('%x-%x' % (a, b) for a, b in ext),
                  sum(c1 - c0 for v in self.creux.values() for c0, c1 in v)), file=sys.stderr)
        return [(a, min(b, fin_source(a))) for a, b in R]

    def bloc(self, g, x, trou=None):
        """bloc ajoute (exec x) : regions copiees d'un seul tenant, pointeurs reloges ; renseigne g.data"""
        blob = bytearray(); off = {}; self.reg = self.regions()
        rv = [a for a, b in self.reg]; roff = {}
        creux = getattr(self, 'creux', {}); libres = []; self.loges = 0
        hotes = [r for r in self.reg if r[0] in creux]
        ordre = hotes + [r for r in self.reg if r[0] not in creux]
        for a, b in ordre:
            # (etape 7) region logee dans un creux d'une banque deja placee (premier qui convient, meme alignement mod 16)
            pl = None
            for j, (l0, l1) in enumerate(libres):
                o_ = ((l0 + 15) & ~15) + (a & 15)
                if o_ + (b - a) <= l1: pl = (j, o_); break
            if pl:
                j, o_ = pl; l0, l1 = libres.pop(j)
                if o_ + (b - a) + 0x40 <= l1: libres.append((o_ + (b - a) + 0x10, l1))
                if o_ - l0 >= 0x40: libres.append((l0, o_ - 0x10))
                libres.sort(key=lambda z: z[1] - z[0])
                blob[o_:o_ + (b - a)] = octets(a, b - a); roff[a] = o_; self.loges += b - a
                if os.environ.get("DEBUG_BLOC") and a == int(os.environ["DEBUG_BLOC"], 16): print("DBG libre %x-%x -> %x" % (l0, l1, o_), file=sys.stderr)
                continue
            o = ((len(blob) + 15) & ~15) + (a & 15)    # meme alignement (modulo 16) que chez Upper
            # (etape 4) trou = (debut, fin) ou LISTE de trous ; un trou de longueur nulle est une COUPURE (changement de
            # fenetre 68K) : aucune region ne la traverse
            cur = len(blob)
            for t0, t1 in (sorted(trou) if isinstance(trou, list) else [trou] if trou else []):
                if x + o < t1 and x + o + (b - a) > t0:
                    # (etape 7) BLOC_RESTES=1 : la place perdue avant la coupure (ou le trou) sert aux regions suivantes
                    if BLOC_RESTES and t0 - x - cur >= 0x40 and x + cur < t0:
                        libres.append((cur, t0 - x - 0x10)); libres.sort(key=lambda z: z[1] - z[0])
                    o = (t1 - x) + (a & 15); cur = t1 - x
            blob += bytes(o - len(blob)); roff[a] = o
            blob += octets(a, b - a)
            for c0, c1 in creux.get(a, []):
                if not (a <= c0 < c1 <= b): print("CREUX HORS REGION %x-%x : %x-%x" % (a, b, c0, c1), file=sys.stderr); continue
                if c1 - c0 >= 0x100: libres.append((o + c0 - a, o + c1 - a))
            libres.sort(key=lambda z: z[1] - z[0])
        self.roff = roff
        _tr = sorted(trou) if isinstance(trou, list) else [trou] if trou else []
        for a_, b_ in self.reg:
            for t0, t1 in _tr:
                if t0 < t1 and x + roff[a_] < t1 and x + roff[a_] + (b_ - a_) > t0 or t0 == t1 and x + roff[a_] < t0 < x + roff[a_] + (b_ - a_):
                    print("REGION DANS UN TROU : %x-%x en %x (trou %x-%x)" % (a_, b_, x + roff[a_], t0, t1), file=sys.stderr)
        if creux: print("bloc : regions %d o, logees dans les creux %d o, bloc %d o, creux libres restants %d o" % (
            sum(b - a for a, b in self.reg), self.loges, len(blob), sum(l1 - l0 for l0, l1 in libres)), file=sys.stderr)
        # cases des creux des banques : jamais relogees (d'autres regions y sont logees)
        en_creux = sorted((c0, c1) for v in creux.values() for c0, c1 in v); ec0 = [c0 for c0, c1 in en_creux]
        def dans_creux(u):
            k_ = bisect.bisect_right(ec0, u) - 1
            return k_ >= 0 and u < en_creux[k_][1]
        for v in self.segments:
            k = bisect.bisect_right(rv, v) - 1; a, b = self.reg[k]; assert a <= v < b
            off[v] = roff[a] + (v - a)
        plages = {(a, b): x + roff[a] for a, b in self.reg}
        for v, (h, n) in self.reutil.items(): plages[(v, v + n)] = h
        sv = sorted(plages); dv = [a for a, _ in sv]
        rgs = sorted(self.reg); rgv = [a for a, _ in rgs]
        def ou(p):
            if OU3:                                   # (etape 3) les plages reutilisees chevauchent les regions
                k = bisect.bisect_right(rgv, p) - 1   # copiees : la region copiee qui contient p d'abord
                if k >= 0 and rgs[k][0] <= p < rgs[k][1]: return x + roff[rgs[k][0]] + (p - rgs[k][0])
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
                if en_creux and dans_creux(a_r + i): continue
                p = struct.unpack_from('<I', b, i)[0]
                if (a_r + i) in PTR_EXCLUS: stat['exclu (script)'] += 1; continue   # (etape 5) aussi les pointeurs de donnees
                if est_pointeur(a_r + i, p, REFS):
                    q = ou(p)
                    if q is None: stat['donnee non suivie'] += 1; continue
                    struct.pack_into('<I', blob, o, q); stat['donnee relogee'] += 1
                    continue
                cl = GR.classe_valeur(p, GR.H5)
                if cl == 'code' and (a_r + i) in PTR_EXCLUS: stat['code exclu'] += 1; continue
                if cl == 'code' and (p & 0xffff) < 0x100 and (p - BASE) not in PL.E5: continue   # paire de mots ($0008 $0060)
                # (etape 6) PTR_BAS=1 : moitie basse < $100 = paire de mots meme si la cible est une entree de routine, sauf
                # dans une table de pointeurs de code (voisin aligne de classe code) : flux de palettes du perso $18
                # ($0020 $002A = $002A0020 -> entree 0xB0020 ; 0x2E2B0 lisait $E1D0)
                if cl == 'code' and PTR_BAS and (p & 0xffff) < 0x100:
                    def _cv2(j):
                        if j < 0 or j + 4 > len(b): return False
                        x = struct.unpack_from('<I', b, j)[0]
                        return not (x & 3) and (x & 0xffff) >= 0x100 and GR.classe_valeur(x, GR.H5) == 'code'
                    if not (_cv2(i - 4) or _cv2(i + 4)): stat['code bas isole laisse'] += 1; continue
                if cl == 'code' and PTR_INSTR and not (p & 3) and (p - BASE) not in PL.E5 and (p - BASE) not in instr5():
                    stat['code hors instruction laisse'] += 1; continue
                if cl == 'code' and not ((p - BASE) in PL.E5 or g.neuf(p - BASE) is not None) and not (p & 3):
                    a_ = PL.routine_de(p - BASE); d_ = g.D.get(a_)
                    if d_ and d_[0] == 'HYPER' and isinstance(d_[1], int) and PL.E5[a_] - a_ == PL.E9.get(d_[1], 0) - d_[1]:
                        struct.pack_into('<I', blob, o, d_[1] + (p - BASE - a_) + BASE); ptr_code.append(o); stat['code milieu homologue'] += 1
                    else: stat['code milieu laisse'] += 1
                    continue
                # (etape 4) PTR_ALIGNE=1 : un pointeur de code MIPS est multiple de 4 ; sinon paire de mots de script
                # (fin de Ken : $0301 $0028 = $00280301 « relogee » en code -> commande $7494, script decale, plantage)
                if cl == 'code' and PTR_ALIGNE and (p & 3): stat['code non aligne laisse'] += 1; continue
                # (etape 4) PTR_VOISIN=1 : une cible qui n'est PAS une entree de routine (seulement une instruction d'une
                # routine greffee, g.neuf ; les « milieux homologues » d'Hyper restent : les ecarter cassait les fins) n'est un pointeur de code que dans une TABLE (long voisin aussi pointeur de code
                # aligne) ; isolee, c'est une paire de mots (fin de Ken : $4200 $0030 = $00304200 -> 0x114200)
                if cl == 'code' and PTR_VOISIN and (p - BASE) not in PL.E5:
                    def _cv(j):
                        if j < 0 or j + 4 > len(b): return False
                        x = struct.unpack_from('<I', b, j)[0]
                        return not (x & 3) and GR.classe_valeur(x, GR.H5) == 'code'
                    if not (_cv(i - 4) or _cv(i + 4)): stat['code isole laisse'] += 1; continue
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
