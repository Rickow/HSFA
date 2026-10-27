#!/usr/bin/env python3
"""OUTIL DE GREFFE MIPS (prototype, agent greffe_arcade) : recopie des routines d'Upper (ro5) dans une zone libre du
module d'Hyper (ro9) et relogement, pour un « ro9 augmente » traduit par la chaine habituelle.

Zone d'accueil : le Z80 recompile d'Hyper, fichier [0x20, 0x22B00). Il n'est jamais traduit (le Z80 d'origine
tourne sur la CPS2) et rien dans le 68K d'Hyper ne le vise (verifie par verifie_zone()). La greffe est posee a la FIN
de cette zone, [G0, 0x22B00) ; la copie du traducteur (greffe_arcade/untranspile) traduit alors [G0, 0x22B00) en plus
(GREFFE_C0=G0). L'en-tete du module n'est PAS modifie (mot 3 = fin du code, mot 6 = fin des donnees : piege du
mot 6, SON-HYPER-ROM §13).

Relogements (par routine, balayage lineaire avec suivi des 'lui' comme le traducteur) :
  - jal / j / constantes de code (lui+addiu) : routine greffee -> sa copie ; sinon homologue ro9 (inverse_ro5,
    classes 'identique', 'identique 68K', 'deplacements') ; aides du recompilateur (movem...) -> aides ro9 ;
    sinon NON RESOLU (rapport) ;
  - A5 (lw 0x1114 puis acces/LEA d(base)) : table de relogement A5 (etape 3, TSV) ;
  - constantes RAM : base RAM Upper 0xA00000 -> Hyper 0xB80000 (+ table A5 pour la RAM de travail $FF0000-$FFFFFF) ;
  - variables du portage (fin des donnees .. base RAM) : table apprise sur les routines identiques (port_map) ;
  - constantes de donnees : table de donnees fournie (Upper exec -> ro9 exec, homologue ou bloc ajoute).
Un 'lui' partage par plusieurs utilisations doit recevoir la meme nouvelle moitie haute, sinon CONFLIT (rapport).
Branchements : tous internes au bloc recopie (sinon rapport)."""
import os, sys, struct, bisect, pickle, collections, functools
LUI_NEG = os.environ.get("LUI_NEG", "1") == "1"; LUI_A5ST = os.environ.get("LUI_A5ST", "1") == "1"; LUI_ST = os.environ.get("LUI_ST", "1") == "1"   # (etape 4) lui negatifs (-adresse d'Upper) reloges
os.environ.setdefault("GRAIN", "routine")
sys.path.insert(0, "<workspace>/work/carto_ro9")
import commun as C
from mips import decode, Ins
BASE = 0x1F0000
EU = "<workspace>/work/etude_upper_hyper"
G = "<workspace>/work/greffe_arcade"
INV = pickle.load(open(os.path.join(EU, "inverse_ro5.pkl"), "rb"))
OK_CLASSES = ('identique', 'identique 68K', 'deplacements')
AIDES = {0x212b00: 0x212dc0, 0x212e60: 0x213120, 0x2131c0: 0x213480, 0x2134a0: 0x213610}   # profils ro5 -> ro9 (exec)
Z80_FIN = 0x22B00

def H(mod):
    h = C.header(mod); return dict(code_end=h['code_end'], data_end=h['fin_exec'], ram=C.ram_base(mod))
H5, H9 = H('ro5'), H('ro9')

def classe_valeur(v, h):
    """nature d'une valeur 32 bits (adresse d'execution PS2) dans le module h"""
    if h['ram'] <= v < h['ram'] + 0x80000: return 'ram'
    if h['data_end'] <= v < h['ram']: return 'port'
    if BASE + 0x22B00 <= v < BASE + h['code_end']: return 'code'
    if BASE + h['code_end'] <= v < h['data_end']: return 'data'
    return None

DEST_RT = {'lb','lh','lw','lbu','lhu','ld','lwu','addiu','daddiu','andi','ori','xori','lui','slti','sltiu','lwl','lwr','addi'}
DEST_RD = {'addu','subu','daddu','dsubu','and','or','xor','nor','slt','sltu','sll','srl','sra','sllv','srlv','srav',
           'dsll','dsrl','dsra','dsll32','dsrl32','dsra32','movz','movn','mfhi','mflo','add','sub'}
def dest(x):
    if x.m in DEST_RT: return x.rt
    if x.m in DEST_RD or (x.op == 0 and x.m == 'jalr'): return x.rd
    if x.m == 'jal': return 31
    return None
MEM = {'lb','lbu','lh','lhu','lw','lwu','ld','sb','sh','sw','sd','lwl','lwr','swl','swr'}

@functools.lru_cache(None)
def port_map():
    """variables du portage (adresses entre la fin des donnees et la base RAM) : Upper -> Hyper, apprises sur les
    routines IDENTIQUES (memes instructions une a une, constantes lui/addiu appariees)"""
    b5, b9 = C.load('ro5'), C.load('ro9'); votes = collections.defaultdict(collections.Counter)
    for a, r in INV.items():
        if r['classe'] not in ('identique', 'identique 68K', 'deplacements') or r['nat'] or not r['partenaire']: continue
        n = r['taille'] // 4; p = r['partenaire']
        L5 = [Ins(a + 4*k, struct.unpack_from('<I', b5, a + 4*k)[0]) for k in range(n)]
        L9 = [Ins(p + 4*k, struct.unpack_from('<I', b9, p + 4*k)[0]) for k in range(n)]
        if [x.op for x in L5] != [x.op for x in L9]: continue
        l5, l9 = {}, {}
        for x, y in zip(L5, L9):
            if x.m == 'lui': l5[x.rt] = x.imm << 16; l9[y.rt] = y.imm << 16; continue
            if (x.m in MEM or x.m == 'addiu') and x.rs in l5 and y.rs in l9:
                v5 = (l5[x.rs] + x.simm) & 0xffffffff; v9 = (l9[y.rs] + y.simm) & 0xffffffff
                if classe_valeur(v5, H5) == 'port' and classe_valeur(v9, H9) == 'port': votes[v5][v9] += 1
            d = dest(x)
            if d is not None: l5.pop(d, None); l9.pop(d, None)
    return {v: c.most_common(1)[0][0] for v, c in votes.items()}

def verifie_zone(z0=0x20, z1=Z80_FIN):
    """aucune reference du 68K d'Hyper (jal, j, constantes lui/addiu, longs des donnees) vers [z0, z1) (fichier)"""
    b9 = C.load('ro9'); s0 = C.start68k('ro9'); e = H9['code_end']; refs = collections.Counter(); lu = {}
    for x in decode(b9, s0, e):
        if x.m in ('jal', 'j') and z0 <= x.tgt - BASE < z1: refs['jal/j'] += 1
        if x.m == 'lui': lu[x.rt] = x.imm << 16; continue
        if x.m in ('addiu', 'ori') and x.rs in lu:
            v = (lu[x.rs] + (x.simm if x.m == 'addiu' else x.imm)) & 0xffffffff
            if z0 <= v - BASE < z1: refs['constante'] += 1
        d = dest(x)
        if d is not None: lu.pop(d, None)
    for o in range(e, len(b9) - 3, 4):
        v = struct.unpack_from('<I', b9, o)[0]
        if z0 + BASE <= v < z1 + BASE and v % 4 == 0: refs['long des donnees (aligne)'] += 1
    return refs

class Greffe:
    def __init__(self, routines, a5=None, data=None, fin=Z80_FIN, debut_min=0x20):
        self.R = sorted(set(routines)); self.a5 = a5 or (lambda d: d); self.data = data or {}
        self.b5 = C.load('ro5'); self.rap = collections.defaultdict(list)
        # blocs contigus d'Upper
        blocs = []
        for a in self.R:
            b = INV[a]['b']
            if blocs and blocs[-1][1] == a: blocs[-1][1] = b
            else: blocs.append([a, b])
        self.blocs = blocs
        tot = sum((b - a + 15) & ~15 for a, b in blocs)
        self.g0 = (fin - tot) & ~15
        assert self.g0 >= debut_min, "greffe trop grande (%d o) pour la zone [%#x, %#x)" % (tot, debut_min, fin)
        self.place = []; g = self.g0
        for a, b in blocs: self.place.append((a, b, g)); g += (b - a + 15) & ~15
        self.fin = g
        self._pa = [a for a, _, _ in self.place]

    def neuf(self, f):
        """adresse fichier Upper -> adresse fichier dans la greffe (ou None)"""
        k = bisect.bisect_right(self._pa, f) - 1
        if k >= 0:
            a, b, g = self.place[k]
            if a <= f < b: return g + (f - a)
        return None

    def code(self, v, ctx):
        f = v - BASE; n = self.neuf(f)
        if n is not None: return n + BASE
        if v in AIDES: return AIDES[v]
        r = INV.get(f)
        if r is None:
            st = C.starts('ro5'); a = st[bisect.bisect_right(st, f) - 1]; r = INV.get(a)
            self.rap['code_milieu'].append((ctx, v, a)); return None
        if r['nat']: self.rap['natif'].append((ctx, v)); return None
        if r['classe'] in OK_CLASSES and r['partenaire'] is not None:
            if r['classe'] != 'identique': self.rap['homologue_a_verifier'].append((ctx, v, r['classe'], r['partenaire'] + BASE))
            return r['partenaire'] + BASE
        self.rap['code_non_resolu'].append((ctx, v, r['classe'], (r['partenaire'] or 0) + BASE)); return None

    def valeur(self, v, ctx):
        """nouvelle valeur d'une constante 32 bits (adresse PS2) ; None = non resolue ; v si inchangee"""
        k = classe_valeur(v, H5)
        if k is None: return v
        if k == 'ram':
            rel = v - H5['ram']
            if rel < 0x10000:                                   # RAM de travail : table A5 (adresses CPS2)
                d = (rel - 0x8000) & 0xffff; nd = self.a5(d)
                if nd is None: self.rap['ram_non_relogee'].append((ctx, v)); return None
                rel = (0x8000 + (nd - 0x10000 if nd >= 0x8000 else nd)) & 0xffff
            return H9['ram'] + rel
        if k == 'port':
            m = port_map().get(v)
            if m is None: self.rap['port_non_resolu'].append((ctx, v))
            return m
        if k == 'code': return self.code(v, ctx)
        if k == 'data':
            m = self.data.get(v)
            if m is None:
                # table : la constante peut viser l'interieur d'une plage donnee (debut <= v < fin)
                for (d0, d1), n0 in self.data.get('_plages', {}).items():
                    if d0 <= v < d1: return n0 + (v - d0)
                self.rap['donnee_non_resolue'].append((ctx, v))
            return m

    def reloge(self):
        out = {}
        for a, b, g in self.place:
            words = list(struct.unpack_from('<%dI' % ((b - a) // 4), self.b5, a))
            L = [Ins(a + 4*k, w) for k, w in enumerate(words)]
            lu = {}; a5r = set(); r7 = set(); uses = collections.defaultdict(list)
            for k, x in enumerate(L):
                ctx = x.va
                # branchements relatifs : internes au bloc
                if x.m in ('beq','bne','blez','bgtz','beql','bnel','bltz','bgez','bltzal','bgezal'):
                    t = x.va + 4 + 4 * x.simm
                    if not (a <= t < b): self.rap['branche_externe'].append((ctx, t))
                if x.m in ('jal', 'j'):
                    nv = self.code(x.tgt, ctx)
                    if nv is not None: words[k] = (words[k] & 0xfc000000) | ((nv >> 2) & 0x3ffffff)
                if x.m == 'lui':
                    lu[x.rt] = k; (r7.add if x.imm == 0x7000 else r7.discard)(x.rt); a5r.discard(x.rt); continue
                # base A5 : lw rt,0x1114(r7000)
                if x.m == 'lw' and x.rs in r7 and x.imm == 0x1114:
                    a5r.add(x.rt); lu.pop(x.rt, None); r7.discard(x.rt); continue
                # (etape 5) LUI_ST=1 : valeur d'un lui RANGEE en memoire quelle que soit la base (registres 68K du
                # portage : 'lui v1,$A1 ; lui v0,$7000 ; sw v1,$1108(v0)' = LEA $700000,A2 de l'affichage 0x13D820, que la
                # branche « base lui » masquait -> OBJ ecrits en $AD6000) ; les rangements en A5 sont traites plus bas
                if LUI_ST and x.m in ('sw', 'sh', 'sd') and x.rt in lu and x.rt != 0 and x.rs not in a5r:
                    uses[lu[x.rt]].append((k, 'nu')); self.rap['lui_stocke'].append((ctx, L[lu[x.rt]].imm))
                if (x.m in MEM or x.m == 'addiu') and x.rs in a5r:
                    d = x.imm; nd = self.a5(d)
                    if nd is None: self.rap['a5_non_relogee'].append((ctx, d))
                    elif nd != d: words[k] = (words[k] & 0xffff0000) | (nd & 0xffff); self.rap['a5_reloge'].append((ctx, d, nd))
                    # (etape 4) LUI_A5ST=1 : la VALEUR rangee en A5 vient d'un lui ('lui v1,$A2 ; sw v1,$C130(A5)', Upper
                    # 0x259000 : base scroll1) : constante a reloger aussi ; sinon $A20000 restait (68K $01AE6000)
                    if LUI_A5ST and x.m in ('sw', 'sh', 'sd', 'sb') and x.rt in lu and x.rt != 0:
                        uses[lu[x.rt]].append((k, 'nu')); self.rap['lui_stocke_a5'].append((ctx, L[lu[x.rt]].imm))
                elif x.rs in lu and (x.m in MEM or x.m in ('addiu', 'ori')):
                    uses[lu[x.rs]].append((k, 'lo'))
                elif x.m in ('addu', 'subu', 'daddu', 'or') and x.op == 0:
                    for r in (x.rs, x.rt):
                        if r in lu and r != 0: uses[lu[r]].append((k, 'nu'))
                elif x.m in ('sw', 'sh', 'sd', 'sb') and x.rt in lu:
                    uses[lu[x.rt]].append((k, 'nu'))
                dd = dest(x)
                if dd is not None: lu.pop(dd, None); a5r.discard(dd); r7.discard(dd)
            # relogement des paires lui / lo
            for kl, us in uses.items():
                hi = L[kl].imm; nhs = set(); lo_new = {}
                for k, kind in us:
                    x = L[k]
                    if kind == 'nu': v = hi << 16
                    elif x.m == 'ori': v = (hi << 16) | x.imm
                    else: v = ((hi << 16) + x.simm) & 0xffffffff
                    nv = self.valeur(v, L[k].va)
                    # (etape 4) LUI_NEG=1 : lui NEGATIF additionne (addu) = -(adresse d'Upper) : Upper 0x259190
                    # $C130 = (($C130 - $A20000) ^ $10000) + $A20000 ; seul le lui $A2 etait reloge ($BA), pas $FF5E ->
                    # la base scroll1 derivait de $18 pages a chaque bascule (fonds en « o » bleus)
                    if nv == v and LUI_NEG and kind == 'nu' and v & 0x80000000 and classe_valeur((-v) & 0xffffffff, H5):
                        nv_ = self.valeur((-v) & 0xffffffff, L[k].va)
                        if nv_ is not None and nv_ != (-v) & 0xffffffff and not (nv_ & 0xffff):
                            nv = (-nv_) & 0xffffffff; self.rap['lui_negatif'].append((L[kl].va, hi, nv >> 16))
                    if nv is None: continue
                    if kind == 'nu':
                        if nv & 0xffff: self.rap['conflit_lui'].append((L[kl].va, v, nv)); continue
                        nhs.add(nv >> 16)
                    elif x.m == 'ori': nhs.add(nv >> 16); lo_new[k] = nv & 0xffff
                    else: nhs.add(((nv + 0x8000) >> 16) & 0xffff); lo_new[k] = nv & 0xffff
                if len(nhs) > 1: self.rap['conflit_lui'].append((L[kl].va, sorted(nhs))); continue
                if nhs:
                    nh = nhs.pop()
                    if nh != hi: words[kl] = (words[kl] & 0xffff0000) | nh; self.rap['lui_reloge'].append((L[kl].va, hi, nh))
                    for k, lo in lo_new.items(): words[k] = (words[k] & 0xffff0000) | lo
            out[g] = struct.pack('<%dI' % len(words), *words)
        return out

    def module(self, src=None):
        b = bytearray(src if src is not None else C.load('ro9'))
        for g, code in self.reloge().items():
            b[g:g + len(code)] = code
            pad = (-len(code)) % 16
            b[g + len(code):g + len(code) + pad] = bytes(pad)
        return bytes(b)

if __name__ == "__main__":
    print("zone Z80 d'Hyper [0x20, 0x22B00) : references depuis le 68K :", dict(verifie_zone()) or "aucune")
    print("variables du portage apprises : %d" % len(port_map()))

# ---------------------------------------------------------------------------------------------------------------
# BLOC DE DONNEES DE LA GREFFE (etape 4) : segments d'Upper a copier, servis en [GRF_X, GRF_X + taille) par la copie du
# traducteur (HSFA_GREFFE_DONNEES / HSFA_GREFFE_X / HSFA_GREFFE_PTRS). Les longs du segment qui sont des pointeurs
# d'Upper sont reloges : donnees -> ro9 ou bloc ; code -> homologue ro9 ou copie greffee (puis adresse 68K a la
# construction : liste des decalages HSFA_GREFFE_PTRS).
GRF_X = 0xE80000
def bloc_donnees(g, reutil, copie, x=GRF_X, segments_ptr=True):
    """g : Greffe (pour code()/valeur()) ; reutil {v5: v9} ; copie [(v5, taille, ptrs)] -> (blob, ptr_code, carte)"""
    plages = {}; blob = bytearray(); off = {}
    for v, n, ptrs in sorted(copie):
        a = (len(blob) + 3) & ~3; blob += bytes(a - len(blob)); off[v] = a
        blob += C.load('ro5')[v - BASE:v - BASE + n]; plages[(v, v + n)] = x + a
    g.data = dict(reutil); g.data['_plages'] = plages
    for v, a in off.items(): g.data[v] = x + a
    ptr_code = []
    if segments_ptr:
        for v, n, ptrs in copie:
            for i, p in ptrs:
                o = off[v] + i; k = classe_valeur(p, H5)
                nv = g.valeur(p, ('donnee', v + i))
                if nv is None: continue
                struct.pack_into('<I', blob, o, nv)
                if k == 'code': ptr_code.append(o)
    return bytes(blob), ptr_code, plages
