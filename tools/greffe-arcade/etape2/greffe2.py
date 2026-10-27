#!/usr/bin/env python3
"""GREFFE, ETAPE 2 : construction du module Hyper augmente (ro9a) a partir d'un plan (plan.py).

  - placement : zone Z80 d'Hyper (fichier [G0, 0x22B00), a la fin) puis 2e zone HORS du module (fichier Z2 = exec
    $EC0000 : le fichier du module est prolonge, l'en-tete n'est pas touche ; GREFFE_Z2 pour la copie du traducteur) ;
  - relogement (outils/greffe.py) : appels et constantes de code par les DECISIONS du plan (greffe -> copie,
    HYPER -> homologue, NATIF -> natif homologue ou talon RTS), A5 par la table de relogement, donnees par le bloc
    ajoute ($E80000) ou l'homologue d'Hyper ;
  - routines SYNTHETIQUES (mots MIPS ecrits ici, forme du recompilateur) : aiguillage par le mode ($C201) ;
  - points d'entree : longs de tables d'Hyper et cibles de jal reecrits (PATCHS) ;
  - $102 -> $116 : deplacement des lectures reperees (PATCH_116) dans le code greffe.
Ecrit constructions/<nom>/ : ro9a_module.bin, greffe_donnees.bin, greffe_ptrs.txt, greffe.json, env.sh ;
avec --construire : assemblage par la copie du traducteur (TRAVAIL=constructions/<nom>/b9)."""
import os, sys, struct, json, pickle, collections, bisect, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as PL
import greffe as GR
import commun as C
from mips import Ins
G = GR.G; BASE = GR.BASE
MODULE_SOURCE = "<workspace>/work/modules_son/ro9_usa_prog68k.bin"       # Hyper + redirection des voix (actuel)
SON_DONNEES = "<workspace>/work/modules_son/son_donnees_ro9.bin"
Z80_0, Z80_1 = 0x20, 0x22B00
Z2_EXEC = 0x1000000                                 # 2e zone de code (execution) ; fichier = exec - 0x1F0000
Z2_0 = Z2_EXEC - BASE
GRF_X = 0xDB0000                                    # bloc de donnees (exec, 6 chiffres hexa : le traducteur lit les
                                                    # adresses de tables sur 6 chiffres) ; doit finir avant $FF0000 ;
                                                    # aucun 'lui' $DB-$FE dans ro9 ; TROU reserve au bloc son ($E70000)
TROU_SON = (0xE70000, 0xE80000)
GRF_Y = 0xD10000                                    # bloc externe 68K propre au bloc de donnees de la greffe
TALON_RTS = 0x22B00                                 # natif d'Hyper (chargeur de banques, remplace par le banc du fork) :
                                                    # appel externe -> talon RTS au liage (0x238E0 est TRADUIT)

# ---------------------------------------------------------------------------------------------------------------
# routines synthetiques : mots MIPS (petit-boutiste) dans la forme du recompilateur, cibles a reloger
def j_(op, tgt): return (op << 26) | ((tgt >> 2) & 0x3ffffff)
def stub_mode(cible_arcade, cible_autre):
    """aiguillage : si l'octet $C201(A5) (curseur du menu = mode) vaut 0 (ARCADE) -> JSR cible_arcade, sinon
    JSR cible_autre (cibles = adresses d'EXECUTION). Forme reprise d'Upper 0x24541C (TST.B $C201(A5) ; BEQ)."""
    w = [0x27bdfff0, 0xffbf0000,                     # addiu sp,sp,-16 ; sd ra,0(sp)
         0x3c037000, 0xac601158,                     # lui v1,0x7000 ; sw zero,C(v1)
         0x3c037000, 0x8c631114,                     # lui v1,0x7000 ; lw v1,A5(v1)
         0x8063c200,                                 # lb v1,-0x3E00(v1)        ($C201 68K)
         0x0003263c, 0x0004263f,                     # dsll32 a0,v1,24 ; dsra32 a0,a0,24
         0x3c037000, 0xac641150,                     # lui v1,0x7000 ; sw a0,RES(v1)
         0x3c037000, 0x8c631150,                     # lui v1,0x7000 ; lw v1,RES(v1)
         0x10600005, 0x00000000,                     # beq v1,zero,+24 -> arcade ; nop
         j_(3, cible_autre), 0x00000000,             # jal autre ; nop
         0x10000003, 0x00000000,                     # beq zero,zero,+16 -> fin ; nop
         j_(3, cible_arcade), 0x00000000,            # jal arcade ; nop
         0xdfbf0000, 0x27bd0010,                     # ld ra,0(sp) ; addiu sp,sp,16
         0x03e00008, 0x00000000]                     # jr ra ; nop
    return w

def stub_depart_arcade(tache, depart_hyper, creer_tache):
    """depart de partie du mode ARCADE (remplace l'appel d'Upper 0x4EA30) : cree la tache Arcade d'Upper 0x1346A0
    (priorite $40, comme 0x4EA30 en $4EE20) avec la fonction de creation de tache d'Hyper, puis le depart commun
    d'Hyper (0x63560 : init, tache de jeu). Adresses d'EXECUTION."""
    return [0x27bdfff0, 0xffbf0000,                          # addiu sp,sp,-16 ; sd ra,0(sp)
            0x24030040, 0x3c027000, 0xa4431124,              # MOVE.W #$40,D0
            0x3c030000 | (((tache + 0x8000) >> 16) & 0xffff), 0x24630000 | (tache & 0xffff),
            0x3c027000, 0xac431100,                          # LEA tache,A0
            0x3c020000 | (((creer_tache + 0x8000) >> 16) & 0xffff), 0x24420000 | (creer_tache & 0xffff),
            0x0040f809, 0x00000000,                          # JSR creation de tache
            j_(3, depart_hyper), 0x00000000,                 # JSR depart commun d'Hyper
            0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]  # ld ra ; addiu sp ; jr ra ; nop

# chargeurs natifs d'animation d'Upper (assets_natifs, profil ro5) : sites d'appel et tables (exec Upper)
U_SITES = {0x25d6c0: 2, 0x262574: 2, 0x4cc04: 0}
U_PERSO_JOUEUR = {0x257678: 0, 0x25769c: 1, 0x257d38: 0, 0x257d5c: 1, 0x26b640: 0, 0x26b660: 1}
U_FIN_SITES = (0x272d50,)
U_T_SITE, U_T_PERSO, U_T_FIN, U_PERSO_TABLE = 0x628460, 0x628470, 0x6283c0, 0x60ad90
ASSET_VBASE = 0xD20000                              # base virtuelle PS2 des fichiers anim (libre : aucun lui $D2)

def assets_json(g, plages, chemin, sites_pj_plus=None):
    """profil des chargeurs natifs pour la copie du traducteur (HSFA_GREFFE_ASSETS)"""
    b5 = C.load('ro5')
    tab = lambda t, n: [list(struct.unpack_from('<hh', b5, t - BASE + 4 * i)) for i in range(n)]
    def ou(v):
        for (a, b), x in plages.items():
            if a <= v < b: return x + (v - a)
    A = dict(load_base=0xB83800, vbase=ASSET_VBASE, site=tab(U_T_SITE, 3), perso=tab(U_T_PERSO, 0x28), fin=tab(U_T_FIN, 0x28),
             sites={str(g.neuf(k)): v for k, v in U_SITES.items() if g.neuf(k) is not None},
             perso_joueur=dict({str(g.neuf(k)): v for k, v in U_PERSO_JOUEUR.items() if g.neuf(k) is not None},
                               **{str(k): v for k, v in (sites_pj_plus or {}).items()}),
             fin_sites=[g.neuf(k) for k in U_FIN_SITES if g.neuf(k) is not None], perso_table=ou(U_PERSO_TABLE))
    json.dump(A, open(chemin, 'w'), indent=1)
    return A

def banques(A, dossier):
    """banques du fork pour ro9a : celles d'Hyper (liens) + les fichiers graphiques des paires d'Upper ; lignes
    'anim' de carte.txt recalculees pour les adresses virtuelles des fichiers anim (comme banques.carte())"""
    W9, W5 = "<workspace>/work/mame_ro9/banques_hx", "<workspace>/work/mame_ro5/banques_hx"
    os.makedirs(dossier, exist_ok=True)
    for f in os.listdir(W9):
        if f != 'carte.txt' and not os.path.exists(os.path.join(dossier, f)): os.symlink(os.path.join(W9, f), os.path.join(dossier, f))
    va = {}; x = A['vbase']
    for n in sorted({a for g_, a in A['site'] + A['perso'] + A['fin'] if g_ and a}):
        d = open("<workspace>/work/cps2/anims/f%d.bin" % n, 'rb').read(); va[n] = x; x += (len(d) + 15) & ~15
    lignes = open(os.path.join(W9, 'carte.txt')).read().splitlines()
    sw = lambda v: ((v & 0xffff) << 16) | (v >> 16)
    for g_, a in A['site'] + A['perso'] + A['fin']:
        if g_ and a:
            lignes.append("anim %d %d" % (sw(va[a]), g_))
            src = os.path.join(W5, "f%d.bin" % g_); dst = os.path.join(dossier, "f%d.bin" % g_)
            if os.path.exists(src) and not os.path.exists(dst): os.symlink(src, dst)
    open(os.path.join(dossier, 'carte.txt'), 'w').write('\n'.join(lignes) + '\n')

def stub_fin_selection(prep, natif_perso):
    """fin de selection (remplace l'appel d'Hyper 0x318E38 -> 0xA43F0) : en ARCADE ($C201 = 0), chargement natif des
    animations du perso de J1 (comme la selection d'Upper, sites 0x257678...) : l'appel natif est repatche vers le
    talon par joueur ; puis preparation du combat d'Upper 0x24EA30 (greffee). Retourne l'indice du jal natif."""
    w = [0x27bdfff0, 0xffbf0000,
         0x3c037000, 0xac601158, 0x3c037000, 0x8c631114, 0x8063c200,      # $C201(A5)
         0x0003263c, 0x0004263f, 0x3c037000, 0xac641150, 0x3c037000, 0x8c631150,
         0x14600003, 0x00000000,                                          # bne v1,zero,+16 -> suite
         j_(3, natif_perso), 0x00000000,                                  # jal natif (chargeur par perso, J1)
         j_(3, prep), 0x00000000,                                         # suite : jal preparation
         0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    return w, 15

class Greffe2(GR.Greffe):
    """routines d'Upper + routines synthetiques, placees dans plusieurs zones ; appels par les decisions du plan"""
    def __init__(self, routines, decisions, a5, synth=(), zones=None, data=None):
        self.R = sorted(set(routines)); self.a5 = a5; self.data = data or {}; self.D = decisions
        self.b5 = C.load('ro5'); self.rap = collections.defaultdict(list)
        E5 = PL.E5
        blocs = []
        for a in self.R:
            b = E5[a]
            if blocs and blocs[-1][1] == a: blocs[-1][1] = b
            else: blocs.append([a, b])
        self.blocs = blocs
        self.synth = list(synth)                  # [(nom, mots)]
        tot_z80 = Z80_1 - Z80_0
        # premier remplissage : blocs dans l'ordre ; zone Z80 tant que ca tient (placee a la FIN de la zone), puis Z2
        taille = lambda a, b: (b - a + 15) & ~15
        z80, z2 = [], []; t = 0
        for a, b in blocs:
            if t + taille(a, b) <= tot_z80 - 0x400 and not z2: z80.append((a, b)); t += taille(a, b)
            else: z2.append((a, b))
        self.g0 = (Z80_1 - t) & ~15
        self.place = []; g = self.g0
        for a, b in z80: self.place.append((a, b, g)); g += taille(a, b)
        assert g <= Z80_1
        g = Z2_0
        for a, b in z2: self.place.append((a, b, g)); g += taille(a, b)
        self.synth_place = {}
        for nom, mots in self.synth:
            self.synth_place[nom] = g; g += (4 * len(mots) + 15) & ~15
        self.z2_fin = g
        self.place.sort(key=lambda x: x[0])
        self._pa = [a for a, _, _ in self.place]
        self.fin = Z80_1

    def code(self, v, ctx):
        f = v - BASE; n = self.neuf(f)
        if n is not None: return n + BASE
        if v in GR.AIDES: return GR.AIDES[v]
        a = f if f in PL.E5 else PL.routine_de(f)
        d = self.D.get(a)
        if d is None:
            self.rap['code_non_decide'].append((ctx, v)); return None
        if d[0] == 'GREFFE':
            self.rap['code_greffe_non_place'].append((ctx, v)); return None
        if d[0] == 'SYNTH':
            return self.synth_place[d[1]] + BASE
        if d[0] == 'NATIF':
            if a != f: self.rap['natif_milieu'].append((ctx, v))
            return (d[1] if d[1] is not None else TALON_RTS) + BASE
        if a != f:                                     # milieu d'une routine non greffee : pas d'adresse fiable (ex. la
            self.rap['code_milieu_laisse'].append((ctx, v))   # constante $400000 = base des objets CPS2) -> inchangee
            return None
        return d[1] + BASE

    def module(self, src, blob=b''):
        b = bytearray(src)
        assert len(b) <= GRF_X - BASE and GRF_X - BASE + len(blob) <= min(Z2_0, 0xFF0000 - BASE), "bloc de donnees trop grand"
        b += bytes(max(self.z2_fin, GRF_X - BASE + len(blob)) - len(b))
        # le bloc de donnees est AUSSI pose dans le module prolonge, a son adresse d'execution : le traducteur y lit
        # les tables de sauts (reconstruites en 68K) et les tables de valeurs hebergees dans le code
        b[GRF_X - BASE:GRF_X - BASE + len(blob)] = blob
        for g, code in self.reloge().items():
            b[g:g + len(code)] = code
            pad = (-len(code)) % 16
            b[g + len(code):g + len(code) + pad] = bytes(pad)
        # routines synthetiques : jal relogeables (cibles deja en adresses d'execution d'Hyper ou de la greffe)
        for nom, mots in self.synth:
            g = self.synth_place[nom]
            for k, w in enumerate(mots): struct.pack_into('<I', b, g + 4 * k, w)
        return bytes(b)

def a_exec(g, f5):
    """adresse d'execution de la copie greffee de la routine d'Upper f5"""
    n = g.neuf(f5); assert n is not None, hex(f5); return n + BASE

def main():
    import force as FO
    nom = os.environ.get("NOM", "ro9a")
    P_ = os.path.join(G, 'constructions', nom); os.makedirs(P_, exist_ok=True)
    rac = [int(x, 16) for x in os.environ.get("RACINES", "4E1C0,24EA30,261560,2614A0,2614D0,261500,1346A0").split(',')]
    TC = PL.tables_a_completer() if os.environ.get("TABLES_OBJETS", "1") == "1" else []
    Pl = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FO.FORCE)
    routines = Pl.greffe
    # table de relogement A5 (etape 3 ; recalculee pour l'ensemble greffe si relogement_a5_v2.pkl existe)
    ra5f = os.path.join(G, 'donnees', 'relogement_a5_v2.pkl')
    R = pickle.load(open(ra5f if os.path.exists(ra5f) else os.path.join(G, 'donnees', 'relogement_a5.pkl'), 'rb'))['table']
    inconnus = set()
    def a5(d):
        if d in R: return R[d]
        inconnus.add(d); return d
    # donnees : fermeture bornee par les lectures d'Upper (etape2/donnees2.py)
    import donnees2 as D2, glob
    lj = sorted(glob.glob(os.path.join(G, 'traces', 'u_lu*', 'lu.txt')))
    # BORNES : fermeture statique des pointeurs (segments identiques chez Hyper reutilises) ; regions prolongees jusqu'aux
    # lectures d'Upper voisines (tables de decalages) ; DONNEES_LUES=1 : seulement les segments lus par Upper
    Pl.donnees.add(U_PERSO_TABLE)                    # table perso -> index du chargeur par perso (talons d'animation)
    LU_ = D2.lu_ps2(lj) if lj else None
    if os.environ.get("DONNEES_LUES", "1") == "1": FD = D2.Fermeture(Pl.donnees, LU_)
    else:                                            # fermeture STATIQUE (tous les pointeurs prouves) ; les lectures
        FD = D2.Fermeture(Pl.donnees, None); FD.lu = LU_   # d'Upper ne servent qu'a prolonger les regions
    synth = []
    # aiguillage de la scene 4 par le mode : ARCADE -> 0x261560 greffee, sinon 0x96620 d'Hyper (VERSUS, TRAINING...)
    synth.append(('scene4_mode', None))
    SYN = [('scene4_mode', stub_mode(0, 0)), ('depart_arcade', stub_depart_arcade(0, 0, 0)), ('fin_selection', stub_fin_selection(0, 0)[0])]
    g = Greffe2(routines, Pl.dec, a5, synth=SYN)
    blob, ptr_code, plages = FD.bloc(g, GRF_X, trou=TROU_SON)
    copie = [(v, n, ()) for v, n in sorted(FD.segments.items())]; reutil = {v: h for v, (h, n) in FD.reutil.items()}
    rap_donnees = {k: len(v) for k, v in g.rap.items()}; g.rap.clear()
    g.synth = [('scene4_mode', stub_mode(a_exec(g, 0x261560), 0x96620 + BASE)),
               ('depart_arcade', stub_depart_arcade(a_exec(g, 0x1346A0), 0x63560 + BASE, 0x3F660 + BASE)),
               ('fin_selection', stub_fin_selection(a_exec(g, 0x24EA30), TALON_RTS + BASE)[0])]
    SITE_PERSO_J1 = g.synth_place['fin_selection'] + 4 * stub_fin_selection(0, 0)[1]
    src = open(MODULE_SOURCE, 'rb').read()
    mod = bytearray(g.module(src, blob))
    # ---------------- points d'entree (exec des tables d'Hyper -> fichier) ----------------
    patchs = []
    def long_(ex, val, quoi):
        o = ex - BASE; old = struct.unpack_from('<I', mod, o)[0]; struct.pack_into('<I', mod, o, val)
        patchs.append(dict(type='long', exec=hex(ex), avant=hex(old), apres=hex(val), quoi=quoi))
    def jal_(f9, cible, quoi):
        w = struct.unpack_from('<I', mod, f9)[0]; assert (w >> 26) == 3, hex(f9)
        struct.pack_into('<I', mod, f9, j_(3, cible))
        patchs.append(dict(type='jal', site=hex(f9), avant=hex((w & 0x3ffffff) << 2), apres=hex(cible), quoi=quoi))
    def const_(f9, cible, quoi):
        """constante de code lui (f9) + addiu (f9+4) d'Hyper -> cible"""
        w1, w2 = struct.unpack_from('<II', mod, f9)
        assert (w1 >> 26) == 0x0f and (w2 >> 26) == 0x09, hex(f9)
        old = (((w1 & 0xffff) << 16) + ((w2 & 0xffff) - (0x10000 if w2 & 0x8000 else 0))) & 0xffffffff
        struct.pack_into('<II', mod, f9, (w1 & 0xffff0000) | (((cible + 0x8000) >> 16) & 0xffff), (w2 & 0xffff0000) | (cible & 0xffff))
        patchs.append(dict(type='constante', site=hex(f9), avant=hex(old), apres=hex(cible), quoi=quoi))
    long_(0x5B4210, a_exec(g, 0x4E1C0), "lanceur ARCADE du menu (entree 0) -> lanceur d'Upper 0x4E1C0")
    const_(0x318E30, g.synth_place['fin_selection'] + BASE, "fin de selection (0x318C40) : ARCADE -> animations du perso de J1 puis preparation du combat d'Upper 0x24EA30 (adversaire CPU)")
    long_(0x5B5E88, g.synth_place['scene4_mode'] + BASE, "scene A5+4=4 : aiguillage par le mode (ARCADE -> Upper 0x261560)")
    for k, f5, q in ((3, 0x2614A0, 'CONTINUE'), (4, 0x2614D0, 'GAME OVER'), (5, 0x261500, 'FIN + generique')):
        if g.neuf(f5) is not None: long_(0x5B5E80 + 4 * k, a_exec(g, f5), "scene A5+4=%X (%s) -> Upper 0x%X" % (2 * k, q, f5))
    # $102 -> $116 (etape2/patch_116.py) : lectures INDEX et CMP a un id de base dans le code greffe
    p116 = []
    if os.environ.get("PATCH_116", "1") == "1":
        import patch_116 as P116
        for a, va, lbva, c, det, t, pat in P116.sites(routines):
            if not pat or lbva is None: continue
            n_ = g.neuf(lbva); w = struct.unpack_from('<I', mod, n_)[0]
            assert (w & 0xffff) == 0x102, hex(lbva)
            struct.pack_into('<I', mod, n_, (w & 0xffff0000) | 0x116)
            p116.append(dict(routine=hex(a), mips_upper=hex(lbva), copie=hex(n_ + BASE), classe=c, detail=det))
    for e9, u, d5, d9, i in TC:
        long_(e9, a_exec(g, u), "table 0x%X[%d] (homologue d'Upper 0x%X) : entree nulle -> gestionnaire d'Upper 0x%X" % (d9, i, d5, u))
    open(os.path.join(P_, 'ro9a_module.bin'), 'wb').write(bytes(mod))
    open(os.path.join(P_, 'greffe_donnees.bin'), 'wb').write(blob or b'\0\0\0\0')
    open(os.path.join(P_, 'greffe_ptrs.txt'), 'w').write(''.join('%x\n' % o for o in ptr_code))
    h = lambda x: hex(x) if isinstance(x, int) else x
    z80 = [(a, b, n) for a, b, n in g.place if n < Z80_1]; z2 = [(a, b, n) for a, b, n in g.place if n >= Z2_0]
    info = dict(routines=len(routines), mips=sum(b - a for a, b, _ in g.place),
                zone_z80=[hex(g.g0), hex(Z80_1), sum(b - a for a, b, _ in z80)], zone2=[hex(Z2_0), hex(g.z2_fin), sum(b - a for a, b, _ in z2)],
                blocs=[[hex(a), hex(b), hex(n)] for a, b, n in g.place], synth={k: hex(v + BASE) for k, v in g.synth_place.items()},
                donnees_copiees=[[hex(v), n] for v, n, _ in copie], donnees_reutilisees={hex(v): hex(w) for v, w in reutil.items()},
                taille_bloc=len(blob), pointeurs_code=len(ptr_code), patchs=patchs, stat_donnees=dict(FD.stat), patch_116=p116,
                regions=[[hex(a), hex(b), hex(FD.roff[a])] for a, b in FD.reg], grf_y=hex(GRF_Y),
                donnees_non_suivies=len(FD.non_suivis), journaux_lecture=[os.path.basename(os.path.dirname(x)) for x in lj],
                a5_inconnus=sorted(hex(d) for d in inconnus),
                rapport={k: [[h(z) for z in e] for e in v] for k, v in g.rap.items()}, rapport_donnees=rap_donnees,
                decisions={hex(f): [d[0]] + ([hex(d[1]) if isinstance(d[1], int) else d[1]] if len(d) > 1 and d[1] is not None else []) + [Pl.raison[f]] for f, d in Pl.dec.items() if f in Pl.refs or f in Pl.atteint})
    json.dump(info, open(os.path.join(P_, 'greffe.json'), 'w'), indent=1)
    A_ = assets_json(g, plages, os.path.join(P_, 'assets.json'), {SITE_PERSO_J1: 0}); banques(A_, os.path.join(P_, 'banques_hx'))
    env = dict(MODULE='ro9', TRAVAIL=os.path.join(P_, 'b9'), XDATA='<workspace>/work/xdata/X_DATA.BIN',
               HSFA_GREFFE_ASSETS=os.path.join(P_, 'assets.json'),
               MODULE_FICHIER=os.path.join(P_, 'ro9a_module.bin'), GREFFE_C0='%x' % g.g0, GREFFE_Z2='%x:%x' % (Z2_0, g.z2_fin),
               EXTRACT_MODULES=os.path.dirname(MODULE_SOURCE), HSFA_SON_DONNEES=SON_DONNEES,
               HSFA_GREFFE_DONNEES=os.path.join(P_, 'greffe_donnees.bin'), HSFA_GREFFE_X='%x' % GRF_X, HSFA_GREFFE_Y='%x' % GRF_Y,
               HSFA_GREFFE_PTRS=os.path.join(P_, 'greffe_ptrs.txt'))
    open(os.path.join(P_, 'env.sh'), 'w').write(''.join('export %s=%s\n' % kv for kv in env.items()))
    print("greffe %s : %d routines, MIPS %d o ; zone Z80 [%#x, %#x) %d o ; zone 2 [%#x, %#x) %d o ; donnees : %d copiees (%d o), %d reutilisees, %d ptr code"
          % (nom, len(routines), info['mips'], g.g0, Z80_1, info['zone_z80'][2], Z2_0, g.z2_fin, info['zone2'][2], len(copie), len(blob), len(reutil), len(ptr_code)))
    for k, v in g.rap.items(): print("  %-24s %d" % (k, len(v)))
    print("  A5 hors table : %d %s" % (len(inconnus), ' '.join(sorted('$%04X' % d for d in inconnus))[:300]))
    if '--construire' in sys.argv:
        e = dict(os.environ, **env)
        with open(os.path.join(P_, 'construction.log'), 'w') as f:
            subprocess.run(['nice', '-n', '19', 'python3', 'mame_test.py'], cwd=os.path.join(G, 'untranspile'), env=e, stdout=f, stderr=subprocess.STDOUT)
        print(open(os.path.join(P_, 'construction.log')).read().splitlines()[-1])

if __name__ == "__main__":
    main()
