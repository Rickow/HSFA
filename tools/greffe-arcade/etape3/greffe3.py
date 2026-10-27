#!/usr/bin/env python3
"""GREFFE, ETAPE 3 (copie de etape2/greffe2.py) : construction du module Hyper augmente (ro9a).

Etape 3 : COMBAT = HYPER (COMBAT_HYPER=1, defaut). La sous-table de combat d'Upper copiee (T_61C2A0, A5+C) renvoie
aux sous-etats d'Hyper (T_5B5F40 : init de manche, intro, combat, K.O., ...) ; seul l'etat 7 (fin de match :
enchainement Arcade) reste celui d'Upper, et seulement quand le match est decide ($0104/$014B/$015C), sinon
(match nul, a rejouer) celui d'Hyper. Au K.O. d'Hyper (0x9C940), deux crochets par le mode : comptage des
victoires d'Upper (0x269340 : masque des battus, dernier combat -> fin) et suites Arcade d'Upper (0x26B7C0,
0x26B0B0, 0x272EB0). Traducteur : copie fusionnee untranspile3/ (TRAD).

Etape 2 : construction du module Hyper augmente (ro9a) a partir d'un plan (plan.py).

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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etape2'))
# (etape 3) donnees : critere de pointeur de donnees2.py (preuves du journal des conversions, filtre des paires de
# mots signes et des longs impairs, plages chevauchantes) ; DONNEES3=0 : criteres de l'etape 2
if os.environ.get("DONNEES3", "1") == "1":
    os.environ.setdefault("PREUVES", "<workspace>/work/greffe_arcade/donnees/pointeurs_prouves.txt")
    os.environ.setdefault("FILTRE3", "1"); os.environ.setdefault("OU3", "1"); os.environ.setdefault("TABLES_PTR", "1")
    os.environ.setdefault("SEG_REFS", "0"); os.environ.setdefault("DECALAGES16", "1")   # SEG_REFS=1 : bloc trop grand pour le 68K
    os.environ.setdefault("PLAFOND_DEC", "d200")                                         # citations : $CF63 + marge
    os.environ.setdefault("ECART_REGION", "80")                                          # place (journaux de lecture des 40 persos)
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
GRF_Y2 = 0xC40000                                   # (etape 4) 2e fenetre 68K si le bloc depasse $F00000
# (etape 4) FENETRES=1 : DISPOSITION PAR FENETRES. Le bloc (40 journaux u_lu : 2,30 Mo) ne tient plus ni cote PS2
# ($DB0000-$FF0000 moins le trou du son) ni cote 68K ($D10000-$F00000 + $C40000-$C84000). Cote PS2 : $D60000-$D9FFFF en
# plus (aucun lui $D6-$D9 dans ro5/ro9 ; fichiers anim de VBASE $D20000 finis avant $D60000) ; $DA (lui d'Hyper) et le
# son ($E7) restent des trous. Cote 68K : tous les trous libres des blocs externes ($940000-$EFFFFF) : apres le son
# d'Hyper (fin d'ext_940000 $C30F00) jusqu'a ext_c84000, et apres ext_c84000 (fin $D0B188) jusqu'a $F00000. Le trou du
# son n'occupe plus de place cote 68K. Chaque morceau PS2 [lo, hi) est servi en 68K a y (HSFA_GREFFE_FEN) ; aucune
# region ne traverse un changement de fenetre (coupure). FENETRES=0 : disposition de l'etape 3/4 (e5g).
FENETRES = os.environ.get("FENETRES", "1") == "1"
CARTE_EFFACE = os.environ.get("CARTE_EFFACE", "1") == "1"   # (etape 5) effacements de la selection d'Upper avant le planisphere
CARTE_S1 = os.environ.get("CARTE_S1", "0") == "1"   # (etape 5) effacement de scroll1 (Hyper 0x38AE50) avant le planisphere
DECOR_CARTE = os.environ.get("DECOR_CARTE", "0") == "1"     # (etape 4) $100 = $10 pendant les ecrans d'Upper
COUCHES_UPPER = os.environ.get("COUCHES_UPPER", "0") == "1"   # (etape 4) ordre des couches d'Upper (0x15ACB0)
BASES_UPPER = os.environ.get("BASES_UPPER", "0") == "1"     # (etape 4) bases $C130-$C13C d'Upper a l'init du match
FEN_PS2 = [(0xD60000, 0xDA0000), (0xDB0000, 0xE70000), (0xE80000, 0xFF0000)]
FEN_68K = [(0xD0C000, 0xF00000), (0xC38000, 0xC84000)]   # fin d'ext_940000 (v149) : $C32000 ; marge 24 Ko
# (etape 7, decision D3) D3=1 : zone $3A0000-$3BFFFF de l'image laissee au code MAX (traducteur : RESERVE_MAX=20000) ;
# les donnees d'Hyper qui en descendent allongent ext_940000 de $20000 (fin $C52000, + v151) -> 2e fenetre en $C60000
D3 = os.environ.get("D3", "1") == "1"
EXT_FIN = 0xC32000
if D3:
    os.environ.setdefault("RESERVE_MAX", "20000"); EXT_FIN = 0xC32000 + int(os.environ["RESERVE_MAX"], 16)
    FEN_68K = [(0xD0C000, 0xF00000), (0xC60000, 0xC84000)]
# (etape 5) TROUS=1 : TROUS de la carte 68K CPS2 servis en ROM (agent_coeur_banques, COEUR-BANQUES.md §B : banc =
# banc_mem.lua / cps2f_trous HSFA_TROUS, coeur = patch 0009 hsfa_trous.bin) : fenetres 68K en plus ; cote PS2, morceaux
# sans lui de ro5/ro9 sous $D20000 (lui utilises entre $C0 et $FF : $C0 $C3 $CC $D3 $DA $E7 $F0 $FF ; VBASE des fichiers
# anim $D20000-$D5FC4F). Pointeurs vers les trous etiquetes $01xxxxxx (HW_TAG du traducteur, $400000-$EFFFFF)
TROUS = os.environ.get("TROUS", "1") == "1"
if FENETRES and TROUS:
    # fichier 547 d'Hyper a adresse fixe $C84000-$D0B187 (PS2 = 68K) : a eviter
    FEN_PS2 = [(0xC10000, 0xC30000), (0xC40000, 0xC80000), (0xD10000, 0xD20000)] + FEN_PS2
    FEN_68K = FEN_68K + [(0x410000, 0x618000), (0x710000, 0x800000), (0x810000, 0x900000), (0x668000, 0x700000),
                         (0x61A000, 0x660000), (0x930000, 0x940000)]
if FENETRES: GRF_X = FEN_PS2[0][0]
def fenetres():
    """morceaux (lo, hi, y) : PS2 [lo, hi) -> 68K y ; trous et coupures pour Fermeture.bloc"""
    fen = []; wi = 0; wy = FEN_68K[0][0]
    for lo, hi in FEN_PS2:
        v = lo
        while v < hi and wi < len(FEN_68K):
            n = min(hi - v, FEN_68K[wi][1] - wy); fen.append((v, v + n, wy)); v += n; wy += n
            if wy == FEN_68K[wi][1]:
                wi += 1; wy = FEN_68K[wi][0] if wi < len(FEN_68K) else None
    trous = [(a[1], b[0]) for a, b in zip(FEN_PS2, FEN_PS2[1:])]
    trous += [(a[1], a[1]) for a, b in zip(fen, fen[1:]) if a[1] == b[0] and a[2] + (a[1] - a[0]) != b[2]]
    return fen, trous
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
            ] + (_pose_flag(1) if MODE_FLAG else []) + [      # (etape 3) drapeau de partie Arcade
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
         0x3c037000, 0xac601158, 0x3c037000, 0x8c631114, 0x80630000 | (((FLAG ^ 1) if MODE_FLAG else 0xC200) & 0xffff),
         0x0003263c, 0x0004263f, 0x3c037000, 0xac641150, 0x3c037000, 0x8c631150,
         0x10600003 if MODE_FLAG else 0x14600003, 0x00000000,            # drapeau nul (C201 non nul) -> suite
         j_(3, natif_perso), 0x00000000,                                  # jal natif (chargeur par perso, J1)
         j_(3, prep), 0x00000000,                                         # suite : jal preparation
         0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    return w, 15


# (etape 3) DRAPEAU « PARTIE ARCADE EN COURS » : octet 68K $FF00(A5) = $FF7F00 (zone libre d'Hyper, hors relogements) ;
# pose par le depart ARCADE (talon depart_arcade), efface a la sortie (scene C apres le GAME OVER, talon plans_s8). Les
# aiguillages de la greffe le testent au lieu de $C201 (curseur du menu, qui vaut aussi 0 au demarrage : la demo
# d'amorcage d'Hyper passait par la scene 4 d'Upper). MODE_FLAG=0 : $C201 comme a l'etape 2.
MODE_FLAG = os.environ.get("MODE_FLAG", "1") == "1"
# (etape 7, decision D2) le drapeau passe en $FE00(A5) = $FF7E00 (MAX garde $FF7F00-$FF7FFF) ; D2=0 : $FF7F00
FLAG = 0xFE00 if os.environ.get("D2", "1") == "1" else 0xFF00
def _pose_flag(v): return [0x24030000 | v, 0x3c027000, 0x8c421114, 0xa0430000 | ((FLAG ^ 1) & 0xffff)]
def stub_arcade(si, sinon):
    """aiguillage par le mode : partie Arcade -> appels si, sinon -> appels sinon"""
    return stub_si(si, sinon, octets=[FLAG]) if MODE_FLAG else stub_si(si, sinon)

# (etape 3) routines synthetiques generiques, dans la forme des talons ci-dessus (verifiee a la traduction)
def _test_octet(d68):
    """TST.B d68(A5) -> RES (forme de stub_mode) ; d68 = deplacement 68K (octet : MIPS = d68 XOR 1)"""
    m = (d68 ^ 1) & 0xffff
    return [0x3c037000, 0xac601158, 0x3c037000, 0x8c631114, 0x80630000 | m,
            0x0003263c, 0x0004263f, 0x3c037000, 0xac641150, 0x3c037000, 0x8c631150]
def _appels(L): return [w for c in L for w in (j_(3, c), 0x00000000)]
def stub_si(si, sinon, octets=None, avant=()):
    """octets=None : si le mode $C201(A5) vaut 0 (ARCADE) -> appels si, sinon appels sinon ;
    octets=[d68...] : si l'un des octets d68(A5) est non nul -> si, sinon -> sinon. Cibles = adresses d'EXECUTION."""
    w = [0x27bdfff0, 0xffbf0000] + _appels(avant); br = []
    if octets is None:
        w += _test_octet(0xC201); br.append((len(w), 0x10600000)); w += [0, 0]      # beq v1,zero -> si
    else:
        for d in octets:
            w += _test_octet(d); br.append((len(w), 0x14600000)); w += [0, 0]       # bne v1,zero -> si
    w += _appels(sinon); jf = len(w); w += [0x10000000, 0]
    L_si = len(w); w += _appels(si); L_fin = len(w)
    w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    for i, op in br: w[i] = op | ((L_si - i - 1) & 0xffff)
    w[jf] = 0x10000000 | ((L_fin - jf - 1) & 0xffff)
    return w

def forme_cmpi_w(off, imm):
    """(etape 3) CMPI.W #imm,off(A5) dans la forme du recompilateur (copiee d'Upper 0x26EE0C-0x26EEC4, traduite
    CMPI.W #$6,$0138(A5)) : drapeaux C (0x1158) et resultat (0x1150) poses"""
    b5_ = C.load('ro5')
    f = [struct.unpack_from('<I', b5_, o)[0] for o in range(0x26EE0C, 0x26EEC8, 4)]
    assert f[0] == 0x24120006 and f[3] == 0x84420138
    f[0] = 0x24120000 | (imm & 0xffff); f[3] = 0x84420000 | (off & 0xffff)
    return f

def forme_cmpi_b(d68, imm):
    """(etape 3) CMPI.B #imm,d68(A5) dans la forme du recompilateur (Upper 0x26ED28-0x26EDF0, traduite CMPI.B
    #$7,$C201(A5)) : temporaire de pile 172(sp) -> cadre de pile >= $B0 ; d68 = deplacement 68K (MIPS = d68 XOR 1)"""
    b5_ = C.load('ro5')
    f = [struct.unpack_from('<I', b5_, o)[0] for o in range(0x26ED28, 0x26EDF4, 4)]
    assert f[0] == 0x24150007 and f[3] == 0x8042c200
    f[0] = 0x24150000 | (imm & 0xffff); f[3] = 0x80420000 | ((d68 ^ 1) & 0xffff)
    return f

def stub_remap_ids(fond=0, efface=()):
    """(etape 3) remplace Upper 0x272D80 (appelee par l'init de match 0x2615D0) : $x03 de J1-J4 passe par T_61C160
    (40 entrees : identite sauf $13 -> $11) ; les ids des versions d'Hyper ($30-$7F) y debordaient (-> 0 = Ryu).
    Ici : si $x03 == $13 alors $11, sinon inchange."""
    w = [0x27bdff40, 0xffbf00b8]
    for k in range(1, 5):
        d = 0x0103 + 0x400 * k
        f = forme_cmpi_b(d, 0x13) + [0x14400006, 0x00000000]          # bne -> suivant
        f += [0x24030011, 0x3c027000, 0x8c421114, 0xa0430000 | ((d ^ 1) & 0xffff), 0x00000000]   # MOVE.B #$11,d(A5)
        w += f
    # (suite) adversaires CPU (J2-J4) : ids d'Upper (< $28, versions ZERO 3) -> perso de base 68K $x17 (= PS2 $116)
    # et version 68K $x16 = $10 poses DES l'init du match : les ecrans Arcade (VS, carte) les lisent avant que l'init
    # du joueur d'Hyper ne les calcule (sinon : adversaire precedent / Ryu sur l'ecran VS)
    for k in range(2, 5):
        d = 0x0103 + 0x400 * k
        f = forme_cmpi_b(d, 0x28) + [0x3c037000, 0x8c631158, 0x04600002, 0x00000000,   # BCS -> copie
                                     0x10000007, 0x00000000]                            # sinon suivant
        f += [0x3c027000, 0x8c421114, 0x80430000 | ((d ^ 1) & 0xffff), 0xa0430000 | (((d + 0x14) ^ 1) & 0xffff),
              0x24030010, 0xa0430000 | (((d + 0x13) ^ 1) & 0xffff), 0x00000000]
        w += f
    # (etape 4) FOND DES ECRANS ARCADE (planisphere) : celui de la selection d'Upper (0x253A80 : plans s2 $86/$87 en
    # $904000/$904400, s3 $81/$82 en $908000/$908100), qu'Hyper n'execute jamais ; redessine a chaque init de match
    # (le decor de combat d'Hyper l'ecrase)
    # (etape 4) BASES_UPPER=1 : bases de pages des plans des ecrans d'Upper ($C130-$C13C, comme sa selection 0x51B40 :
    # $A30000/$A34000/$A38000/$A2F800 -> RAM d'Hyper +$180000, VRAM $910000-$91FFFF) ; sinon le moteur de plans greffe
    # dessinait le planisphere dans les pages du combat d'Hyper ($904000/$90C000), effacees ensuite
    if fond and BASES_UPPER:
        w += [0x3c027000, 0x8c421114]
        for off, v in ((0xC130, 0xBB0000), (0xC134, 0xBB4000), (0xC138, 0xBB8000), (0xC13C, 0xBAF800)):
            w += [0x3c030000 | (v >> 16), 0x34630000 | (v & 0xffff), 0xac430000 | off]
    # (etape 4) DECOR_CARTE=1 : $100 = $10 (« decor » du planisphere, Upper 0x4F70C : $100 = $C38C) pendant les ecrans
    # Arcade d'Upper : ordre des couches T_614CD0[$10] = $270E/$2641 et plans du planisphere ; vs_decor ramene ensuite le
    # combat a un decor d'Hyper ($10 >= 8 -> 4)
    if fond and DECOR_CARTE: w += [0x24030010, 0x3c027000, 0x8c421114, 0xa4430100]
    # (etape 5) CARTE_EFFACE=1 : comme la selection d'Upper (0xC58C0, image 1990 de l'oracle) avant 0x253A80 : page de
    # scroll1 $900000-$903FFF <- $20 (Hyper 0x38AE50 = Upper 0xC5BC0), scroll2 $904000-$907FFF <- $1C20 (0xC5C10) et
    # scroll3 $908000-$90BFFF <- 0 (0xC5C60) ; sinon les restes des
    # ecrans d'Hyper entourent le planisphere
    for e_ in efface: w += [j_(3, e_), 0x00000000]
    if fond: w += [j_(3, fond), 0x00000000]
    w += [0xdfbf00b8, 0x27bd00c0, 0x03e00008, 0x00000000]
    return w

# (etape 3) BASES DES PLANS (registre du fork $804200-$804205, via l'adresse PS2 RAM + $7FF00, cf. mame_test.py) : les
# ecrans de la couche Arcade d'Upper (presentation, carte, face-a-face, VS, continue, game over, fin) dessinent leurs
# plans avec les codes de tuiles d'Upper -> memoires de plans d'Upper (hsfa_plans.bin d'Upper charge en $4000000) ; le
# combat et les ecrans d'Hyper -> celles d'Hyper ($3000000). Unites de 64 Ko.
PLANS_HYPER = (0x300, 0x340, 0x3A0)
PLANS_UPPER = (0x400, 0x440, 0x4A0)
# (etape 6) PLANS_CONT=1 : CONTINUE et GAME OVER d'Upper montrent le DECOR DU COMBAT (grise) deja en VRAM ; le combat
# etant celui d'Hyper, scroll2/scroll3 gardent les bases d'Hyper, scroll1 (textes d'Upper) celle d'Upper
# (etape 6) DECOR_BOSS_FIN=1 : au lieu d'effacer, pose du decor d'Upper $100 (= $174, boss) comme l'ecran VS d'Upper 0x2651C0
# (copies de 0x4C1B0, 0x151B80, 0x4B270) a la 1re image de la fin
DECOR_BOSS_FIN = os.environ.get("DECOR_BOSS_FIN", "0") == "1"
EFFACE_FIN = os.environ.get("EFFACE_FIN", "0") == "1"   # (etape 6) effacer scroll2/3 a l'entree de la fin
PLANS_CONT = os.environ.get("PLANS_CONT", "1") == "1"
PLANS_S68 = (0x400, 0x340, 0x3A0) if PLANS_CONT else None
PLANS = os.environ.get("HSFA_GREFFE_PLANS", "1") != "0"
# (etape 4) DECOR_FIN=1 : pendant la fin (scene A), $100 = $174, decor choisi par Upper (0x24F020 greffee : $14 pour le
# boss ; vs_decor ne borne que $100) : la fin d'Upper fait tourner le moteur de decor d'Upper sur $100
DECOR_FIN = os.environ.get("DECOR_FIN", "1") == "1"
FOND_ARCADE = os.environ.get("FOND_ARCADE", "1") == "1"   # (etape 4) planisphere d'Upper a l'init du match
def _bases(b):
    w = []
    for k, v in enumerate(b): w += [0x24030000 | v, 0x3c0200c0, 0xa4430000 | ((-0x100 + 2 * k) & 0xffff)]   # sh v1,$BFFF00+2k
    return w
def stub_plans(bases, cible):
    """bases des plans puis JSR cible (adresse d'EXECUTION ; 0 = sans appel)"""
    w = [0x27bdfff0, 0xffbf0000] + (_bases(bases) if PLANS else []) + ([j_(3, cible), 0x00000000] if cible else [])
    return w + [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
DECOR_SAUVE = 0xFF02                                   # (etape 4) mot $FF02(A5) = $FF7F02 : decor demande par Upper
def _copie_mot(src, dst):
    """MOVE.W src(A5),dst(A5) (deplacements 68K de MOTS = PS2)"""
    return [0x3c027000, 0x8c421114, 0x84430000 | (src & 0xffff), 0xa4430000 | (dst & 0xffff)]
def stub_plans_scene(cible, restaure=False, bases=None, efface=()):
    """scenes 6/8/A d'Upper (CONTINUE, GAME OVER, fin) : plans d'Upper, JSR cible, puis si la scene est quittee vers
    A5+4 = 0 (continue accepte -> selection d'Hyper) ou $C (sortie -> titre d'Hyper) : plans d'Hyper. Aucun talon sur
    les scenes 0 et C d'Hyper : le VERSUS garde exactement son minutage."""
    w = [0x27bdfff0, 0xffbf0000] + _bases(bases or PLANS_UPPER) + (_copie_mot(0x174, 0x100) if restaure else [])
    # (etape 6) EFFACE_FIN=1 : 1re image de la fin (A5+8 = 0) : pages scroll2/scroll3 effacees comme a la selection
    # d'Upper (le decor du boss d'Upper n'est pas en VRAM : le dernier combat etait sur un decor d'Hyper)
    if efface:
        w += forme_cmpi_w(0x0008, 0) + [0x3c037000, 0x8c631150]; ie = len(w); w += [0x14600000, 0]   # bne RES -> suite
        for e_ in efface: w += [j_(3, e_), 0x00000000]
        w[ie] |= (len(w) - ie - 1) & 0xffff
    w += [j_(3, cible), 0x00000000]
    w += forme_cmpi_w(0x0004, 0) + [0x3c037000, 0x8c631150]; i1 = len(w); w += [0x10600000, 0]   # beq RES -> Lh
    w += forme_cmpi_w(0x0004, 0xC) + [0x3c037000, 0x8c631150]; i2 = len(w); w += [0x10600000, 0]   # beq RES -> Lc
    j1 = len(w); w += [0x10000000, 0]                                                              # -> fin
    Lc = len(w); w += (_pose_flag(0) if MODE_FLAG else [])                                         # sortie : fin de partie
    Lh = len(w); w += _bases(PLANS_HYPER)
    Lf = len(w); w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    for i, L in ((i1, Lh), (i2, Lc), (j1, Lf)): w[i] |= (L - i - 1) & 0xffff
    return w

def stub_plans_auto(couches=0):
    """scene 4 (Arcade), a chaque image : A5+8 >= 6 (combat, victoire) ou (A5+8 = 4 et A5+C >= 4 : entree dans le
    decor) -> plans d'Hyper ; sinon (init, presentation / carte, face-a-face, VS) -> plans d'Upper"""
    if not PLANS: return [0x03e00008, 0x00000000]
    w = [0x27bdfff0, 0xffbf0000]
    w += forme_cmpi_w(0x0008, 6) + [0x3c037000, 0x8c631158]; i1 = len(w); w += [0x04600000, 0]   # bltz C -> L1 (< 6)
    w += _bases(PLANS_HYPER); j1 = len(w); w += [0x10000000, 0]                                    # -> fin
    L1 = len(w)
    w += forme_cmpi_w(0x0008, 4) + [0x3c037000, 0x8c631150]; i2 = len(w); w += [0x14600000, 0]   # bne RES -> Lu (!= 4)
    w += forme_cmpi_w(0x000C, 4) + [0x3c037000, 0x8c631158]; i3 = len(w); w += [0x04600000, 0]   # bltz C -> Lu (< 4)
    w += _bases(PLANS_HYPER); j2 = len(w); w += [0x10000000, 0]
    Lu = len(w); w += _bases(PLANS_UPPER)
    # (etape 4) COUCHES_UPPER=1 : ordre des couches CPS-B des ecrans d'Upper ($32/$3A(A5) <- T_614CD0[$100], copie de
    # 0x15ACB0), qu'Upper calcule dans 0x2654B0 (remplacee par Hyper 0x9A6F0, combat = Hyper) : sans lui, $32 = $1B0E
    # d'Hyper (scroll1 devant) au lieu de $270E -> fond de la presentation recouvert de tuiles de scroll1
    if couches: w += [j_(3, couches), 0x00000000]
    Lf = len(w); w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    for i, L in ((i1, L1), (i2, Lu), (i3, Lu), (j1, Lf), (j2, Lf)): w[i] |= (L - i - 1) & 0xffff
    return w

def stub_decor(cible, decor=4):
    """(etape 3) decors d'Hyper en Arcade (alternative minimale de DECORS.md) : CMPI.W #8,$100(A5) ; BCS -> appel ;
    sinon (rival $14, Bison, decors d'Upper) MOVE.W #decor,$100(A5) ; puis JSR cible (adresse d'EXECUTION)"""
    w = [0x27bdfff0, 0xffbf0000] + forme_cmpi_w(0x100, 8)
    w += [0x3c037000, 0x8c631158, 0x04600006, 0x00000000]          # lw v1,C ; bltz v1 -> appel (BCS)
    w += [0x24030000 | decor, 0x3c027000, 0x8c421114, 0xa4430100, 0x00000000]   # MOVE.W #decor,$100(A5)
    # entree en combat : en-tetes ($0000-$0003) des 7 emplacements d'objets $5000-$5C00 (moteur 0x3A45F0 / Upper
    # 0x1196E0) remis a zero : les objets texte d'Upper des ecrans Arcade y laissaient leur type (1), et le combat
    # d'Hyper reutilise l'emplacement $5C00 (pointeur $0156) en n'ecrivant que $0000-$0001 -> objet texte fantome
    w += [0x3c027000, 0x8c421114] + [0xac400000 | (0x5000 + 0x200 * i) for i in range(7)]   # CLR.L $5x00(A5)
    w += [j_(3, cible), 0x00000000, 0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    return w

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

    PAR_APPELANT = {}                              # (etape 3) {routine d'Upper greffee: (homologue d'Hyper, appelants
                                                   # qui gardent la copie)} : les autres references vont a Hyper
    PAR_APPELANT_HYPER = {}                        # {routine d'Upper : (homologue d'Hyper, appelants envoyes a Hyper)}
    def code(self, v, ctx):
        f = v - BASE
        if f in self.PAR_APPELANT_HYPER and isinstance(ctx, int):
            h_, vers_ = self.PAR_APPELANT_HYPER[f]
            if PL.routine_de(ctx) in vers_: self.rap['par_appelant_vers_hyper'].append((ctx, v)); return h_ + BASE
        if f in self.PAR_APPELANT:
            h_, garde_ = self.PAR_APPELANT[f]
            r_ = PL.routine_de(ctx) if isinstance(ctx, int) else None
            if r_ not in garde_: self.rap['par_appelant_hyper'].append((ctx, v)); return h_ + BASE
            self.rap['par_appelant_copie'].append((ctx, v))
        n = self.neuf(f)
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

# (etape 3) TRI DES PETITES ROUTINES : la regle d) du plan (tri des modifiees : HYPER) passait outre la preuve
# d'equivalence ; pour les petites routines (< 256 o : relais, aiguilleurs), l'homologue par ressemblance est souvent
# faux (Upper 0x137170 : TST.B $BC(A5) -> 0x92D50 ; « homologue » 0x1DBFE0 : TST.B $2C9(A6) -> code de perso d'Hyper).
# TRI_PETITES=1 : une petite routine que le tri (d) renvoie a Hyper n'y va que si elle est EQUIVALENTE (regle e). (Etendre
# la regle aux relais j) « non vus en Arcade » fait passer le plan de 1 850 a 2 535 routines : cas traites un par un dans
# force3.py.)
# (etape 4) RELAIS_J=1 : aussi les RELAIS (<= 64 o) de la regle j) « non vue en Arcade » (courts, indecidables par la
# couverture) du moteur de fin et du flux Arcade : 0x310B0 (commande de script de fin -> 0x31CB0) et 0x2CC00 (defilement
# de decor) allaient a d'autres relais. (Sans borne d'adresse : 91 routines de plus, dont des objets et du code C.)
RELAIS_J = os.environ.get("RELAIS_J", "1") == "1"
if os.environ.get("TRI_PETITES", "1") == "1":
    _regle2 = PL.Plan._regle
    def _regle3(self, x):
        d, r = _regle2(self, x)
        if (r == 'd) tri : HYPER' and PL.E5[x] - x < 256) or \
           (RELAIS_J and r == 'j) non vue en Arcade : homologue' and PL.E5[x] - x <= 0x40 and
            (0x29000 <= x < 0x32000 or 0x240000 <= x < 0x276000)):     # moteur de fin, flux Arcade
            ok, why = self.equivalent(x, d[1])
            if not ok: return ('GREFFE',), 'd3) %s refuse, petite routine non equivalente (%s)' % (r[:2], why)
        return d, r
    PL.Plan._regle = _regle3

# (etape 3) MOTEUR DE PLANS D'UPPER pour la couche Arcade : les routines de plans/decor d'Upper (0x14E000-0x160000 :
# listes, bibliotheques, chargeurs s1/s2/s3) jugees « equivalentes » (regle e : instructions identiques, 64 premiers
# octets des tables egaux) ou « services partages » (f) lisent en fait les tables d'Hyper (0x1515C0 -> 0x315AB0 : codes
# s2 + $1000 au lieu de + $1C00 ; images de la fin noires). Appelees seulement par du code greffe (le combat appelle
# directement le moteur d'Hyper) -> copies d'Upper. MOTEUR_PLANS_UPPER=0 : regles de l'etape 2.
if os.environ.get("MOTEUR_PLANS_UPPER", "1") == "1":
    _regle_p = PL.Plan._regle
    def _regle_plans(self, x):
        d, r = _regle_p(self, x)
        if d[0] == 'HYPER' and 0x14E000 <= x < 0x160000 and r.startswith(('e)', 'f)')):
            return ('GREFFE',), 'p3) moteur de plans d\'Upper (%s)' % r[:2]
        return d, r
    PL.Plan._regle = _regle_plans

# (etape 5) FIN_J=1 : dans le MOTEUR DE FIN d'Upper (0x29000-0x32000), une routine de la regle j) « non vue en Arcade :
# homologue » (les fins ne sont pas dans la couverture) ne va a Hyper que si elle est EQUIVALENTE, quelle que soit sa
# taille : 0x2A3D0 (gestionnaire des acteurs de fin) -> Hyper 0x12EFC0 traitait l'objet $FFDE00 avec le moteur des
# joueurs d'Hyper (0x2B8F80, +$C0) -> plantage des la 1re image des fins 08, 0C, 0E, 19
J_EQUIV = os.environ.get("J_EQUIV", "0") == "1"   # (etape 5) la meme exigence pour TOUTE la regle j)
# 0x2C510 greffee par cette regle cassait la fin du perso $18 (Upper 0x2E49C, table de pointeurs) : laissee a Hyper
FIN_J_SAUF = {int(x, 16) for x in os.environ.get("FIN_J_SAUF", "").split(',') if x}
if os.environ.get("FIN_J", "1") == "1":
    _regle_f = PL.Plan._regle
    def _regle_fin(self, x):
        d, r = _regle_f(self, x)
        if d[0] == 'HYPER' and (J_EQUIV or 0x29000 <= x < 0x32000) and r.startswith('j)') and x not in FIN_J_SAUF:
            ok, why = self.equivalent(x, d[1])
            if not ok: return ('GREFFE',), 'f5) moteur de fin, homologue non equivalent (%s)' % why
        return d, r
    PL.Plan._regle = _regle_fin

# (etape 6) MOTEUR D'AFFICHAGE D'UPPER (0x13D820-0x14E000) entierement greffe quand DESSIN_UPPER=1 : toute routine de
# la plage envoyee a Hyper (regles e/f/j) -> copie (atteinte seulement par la copie de 0x13D820, appelants Arcade)
if os.environ.get("DESSIN_UPPER", "0") == "1":
    _regle_d = PL.Plan._regle
    def _regle_dessin(self, x):
        d, r = _regle_d(self, x)
        if d[0] == 'HYPER' and 0x13D820 <= x < 0x14E000:
            return ('GREFFE',), 'a6) moteur d\'affichage d\'Upper (%s)' % r[:2]
        return d, r
    PL.Plan._regle = _regle_dessin

# (etape 3) COMBAT = HYPER
COMBAT_HYPER = os.environ.get("COMBAT_HYPER", "1") == "1"
TRAD = os.environ.get("TRAD", os.path.join(G, 'untranspile3'))
U_T_COMBAT = 0x61C2A0                                   # sous-table de combat d'Upper (A5+C), 8 entrees
H_COMBAT = (0x9A980, 0x9B350, 0x9B7E0, 0x9C940, 0x9E920, 0x9F300, 0x9FD10)   # T_5B5F40[0..6] d'Hyper
U_T_VS, H_VS = 0x61C288, 0x9A430                       # sous-table 4/4 d'Upper ; entree 1 = ecran VS (d'Hyper si VS_UPPER=0)
H_ETAT7 = 0x9FDB0                                       # T_5B5F40[7] : fin de match d'Hyper (match nul)
ETAT7_OCTETS = (0x0104, 0x014B, 0x015C)                 # match decide / dernier combat gagne / cas Upper (68K)
KO_ARCADE = (0x26B7C0, 0x26B0B0, 0x272EB0)              # suites Arcade du K.O. d'Upper (apres 0x272410 = 0xA1980) :
                                                        # appelees au debut de l'etat 7 (talon etat7) et non au K.O. :
                                                        # 0x26B0B0 rend les joueurs inactifs ($0101 = 0) quand le CPU
                                                        # gagne, ce qui bloquait les etats 4-6 d'Hyper (pose de victoire)
H_SITE_KO_COMPTE, H_KO_COMPTE = 0x9D094, 0x9D240        # jal 0x9D240 dans 0x9C940 (homologue de 0x269340)
H_SITE_KO_SUITE, H_KO_SUITE = 0x9D09C, 0xA1980          # jal 0xA1980 (= Upper 0x272410)

# (etape 3) AFFICHAGE DES OBJETS (0x13D820 = Hyper 0x392270 : interpreteur d'animation, sprites) : celui d'Upper pour
# les ecrans de la couche Arcade qui montrent des acteurs d'Upper (fin : commandes d'animation absentes de
# l'interpreteur d'Hyper ; continue, game over, carte, presentation, face-a-face) ; celui d'Hyper ailleurs (fin de
# match 0x26E900 et pose de victoire 0x26F930 : combattants d'Hyper).
AFFICHAGE_UPPER = os.environ.get("AFFICHAGE_UPPER", "0") == "1"   # 1 : objets des ecrans Arcade invisibles (essai e3v)
COPIES_BASE = os.environ.get("COPIES_BASE", "1") == "1"
TOUT_116 = os.environ.get("TOUT_116", "1") == "1"
AFFICHAGE = {0x13D820: (0x392270, frozenset({0x2AF30, 0x24A480, 0x24B050, 0x259190, 0x25B0E0, 0x25CE40, 0x2651C0, 0x265310}))}
# (etape 3) VS d'Upper : sa preparation du decor passe par Hyper (memes paires que la fin de match nulle 0x26E900 /
# 0x9FDB0 et que le VS d'Hyper 0x9A430 : 0xCB470/0x38F2E0, 0x4B270/0x60A20, 0x151B80/0x30EC10, 0x4C1B0/0xAC050)
VS_UPPER = os.environ.get("VS_UPPER", "1") == "1"
_VS = frozenset({0x2651C0, 0x265310})
DECOR_VS = {0x4B270: (0x60A20, _VS), 0x151B80: (0x30EC10, _VS), 0x4C1B0: (0xAC050, _VS)}

def VS_CIBLE(g): return a_exec(g, 0x2651C0) if VS_UPPER else H_VS + BASE

def exec_donnee(g, v):
    """adresse d'execution de la donnee d'Upper v dans le bloc de la greffe (ou chez Hyper si reutilisee)"""
    for (a, b), x in g.data['_plages'].items():
        if a <= v < b: return x + (v - a)
    raise KeyError(hex(v))

def a_exec(g, f5):
    """adresse d'execution de la copie greffee de la routine d'Upper f5"""
    n = g.neuf(f5); assert n is not None, hex(f5); return n + BASE

def main():
    import force3 as FO
    nom = os.environ.get("NOM", "ro9a")
    P_ = os.path.join(G, 'constructions', nom); os.makedirs(P_, exist_ok=True)
    rac = [int(x, 16) for x in os.environ.get("RACINES", "4E1C0,24EA30,261560,2614A0,2614D0,261500,1346A0").split(',')]
    if COMBAT_HYPER: rac += [x for x in KO_ARCADE + (0x269340, 0x26E900) if x not in rac]
    if AFFICHAGE_UPPER:
        rac += [x for x in AFFICHAGE if x not in rac]; Greffe2.PAR_APPELANT = dict(AFFICHAGE)
    if COMBAT_HYPER and VS_UPPER: Greffe2.PAR_APPELANT_HYPER = dict(DECOR_VS)
    TC = PL.tables_a_completer() if os.environ.get("TABLES_OBJETS", "1") == "1" else []
    Pl = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FO.force())
    routines = Pl.greffe
    # table de relogement A5 (etape 3 ; recalculee pour l'ensemble greffe si relogement_a5_v2.pkl existe)
    pickle.dump(routines, open(os.path.join(G, 'donnees', 'greffe_v3.pkl'), 'wb'))   # (etape 3) pour relogement_a5_v3.py
    if os.environ.get("PLAN_SEUL") == "1": print("plan : %d routines" % len(routines)); return
    ra5f = os.path.join(G, 'donnees', os.environ.get("RA5", 'relogement_a5_v3.pkl'))
    if not os.path.exists(ra5f): ra5f = os.path.join(G, 'donnees', 'relogement_a5_v2.pkl')
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
    SYN = [('scene4_mode', stub_arcade([0, 0], [0])), ('depart_arcade', stub_depart_arcade(0, 0, 0)), ('fin_selection', stub_fin_selection(0, 0)[0])]
    if COMBAT_HYPER:
        SYN += [('ko_compte', stub_arcade([0], [0])),
                ('etat7', stub_si([0], [0], octets=ETAT7_OCTETS, avant=[0] * len(KO_ARCADE))), ('vs_decor', stub_decor(0)),
                ('remap_ids', stub_remap_ids(4 if FOND_ARCADE else 0, ((4,) if CARTE_S1 else ()) + (4, 4) if FOND_ARCADE and CARTE_EFFACE else ())), ('plans_auto', stub_plans_auto(4 if COUCHES_UPPER else 0))]
        if PLANS: SYN += [('plans_s%X' % k, stub_plans_scene(4, k == 0xA and DECOR_FIN, PLANS_S68 if k in (6, 8) else None, ((4, 4, 4) if DECOR_BOSS_FIN else (4, 4)) if k == 0xA and EFFACE_FIN else ())) for k in (6, 8, 0xA)]
    g = Greffe2(routines, Pl.dec, a5, synth=SYN)
    FEN, TROUS = fenetres() if FENETRES else (None, TROU_SON)
    if FENETRES:
        assert all(hi <= ASSET_VBASE or lo >= 0xD60000 for lo, hi, y in FEN), "morceau PS2 sur les fichiers anim"
        assert all((y >= EXT_FIN or y + hi - lo <= 0x940000) and y + hi - lo <= 0xF00000 for lo, hi, y in FEN)
        import donnees2 as D2_
        f547 = (D2_.F547, D2_.F547 + len(D2_.B547))
        assert all(y + hi - lo <= f547[0] or y >= f547[1] for lo, hi, y in FEN), "fenetre 68K sur ext_c84000"
    blob, ptr_code, plages = FD.bloc(g, GRF_X, trou=TROUS); blob = bytearray(blob)
    if FENETRES:
        assert GRF_X + len(blob) <= FEN[-1][1], "bloc de donnees trop grand pour les fenetres (%d o)" % len(blob)
        print("fenetres : %s ; bloc %d o, place PS2 %d o, 68K %d o" % (' '.join('%x-%x>%x' % f for f in FEN), len(blob),
              FEN[-1][1] - GRF_X, sum(hi - lo for lo, hi, y in FEN)))
    print("bloc de donnees : %d o (%d regions) ; place : %d o (PS2), %d o (68K, $%X-$F00000)" % (len(blob), len(FD.reg),
          min(Z2_0, 0xFF0000 - BASE) - (GRF_X - BASE), 0xF00000 - GRF_Y, GRF_Y))
    # (etape 3) cote 68K, le bloc externe propre ($D10000) doit finir avant la RAM du portage du fork ($F00000) : un
    # bloc de 2,29 Mo la recouvrait (demarrage d'Hyper modifie, VERSUS decale d'une image)
    # (etape 4) au-dela, 2e fenetre 68K $C30000-$C83FFF (libre entre ext_940000 et ext_c84000 ; blocs externes du coeur
    # FBNeo : $940000-$EFFFFF) : HSFA_GREFFE_Y2 pour la copie du traducteur
    N1 = 0xF00000 - GRF_Y
    Y2 = (GRF_Y2, N1) if len(blob) > N1 else None
    if os.environ.get("BLOC_SEUL") == "1":
        for a_, b_ in sorted(FD.reg, key=lambda r: r[0] - r[1])[:int(os.environ.get("BLOC_N", "15"))]: print("   region %x-%x %d" % (a_, b_, b_ - a_))
        return
    if FENETRES: Y2 = None
    else: assert len(blob) <= N1 + (0xC84000 - GRF_Y2), "bloc de donnees trop grand pour les deux fenetres 68K"
    copie = [(v, n, ()) for v, n in sorted(FD.segments.items())]; reutil = {v: h for v, (h, n) in FD.reutil.items()}
    rap_donnees = {k: len(v) for k, v in g.rap.items()}; g.rap.clear()
    g.synth = [('scene4_mode', stub_arcade([0, a_exec(g, 0x261560)], [0x96620 + BASE])),
               ('depart_arcade', stub_depart_arcade(a_exec(g, 0x1346A0), 0x63560 + BASE, 0x3F660 + BASE)),
               ('fin_selection', stub_fin_selection(a_exec(g, 0x24EA30), TALON_RTS + BASE)[0])]
    if COMBAT_HYPER:
        X = lambda f: a_exec(g, f)
        g.synth += [('ko_compte', stub_arcade([X(0x269340)], [H_KO_COMPTE + BASE])),
                    ('etat7', stub_si([X(0x26E900)], [H_ETAT7 + BASE], octets=ETAT7_OCTETS, avant=[X(f) for f in KO_ARCADE])),
                    ('vs_decor', stub_decor(VS_CIBLE(g))), ('remap_ids', stub_remap_ids(a_exec(g, 0x253A80) if FOND_ARCADE else 0, ((0x38AE50 + BASE,) if CARTE_S1 else ()) + (a_exec(g, 0xC5C10), a_exec(g, 0xC5C60)) if FOND_ARCADE and CARTE_EFFACE else ())), ('plans_auto', stub_plans_auto(a_exec(g, 0x15ACB0) if COUCHES_UPPER else 0))]
        SC = {6: a_exec(g, 0x2614A0), 8: a_exec(g, 0x2614D0), 0xA: a_exec(g, 0x261500)}
        if PLANS: g.synth += [('plans_s%X' % k, stub_plans_scene(SC[k], k == 0xA and DECOR_FIN, PLANS_S68 if k in (6, 8) else None, ((a_exec(g, 0x4C1B0), a_exec(g, 0x151B80), a_exec(g, 0x4B270)) if DECOR_BOSS_FIN else (a_exec(g, 0xC5C10), a_exec(g, 0xC5C60))) if k == 0xA and EFFACE_FIN else ())) for k in (6, 8, 0xA)]
        g.synth[0] = ('scene4_mode', stub_arcade([g.synth_place['plans_auto'] + BASE, a_exec(g, 0x261560)], [0x96620 + BASE]))
        for nom_, mots_ in g.synth: assert len(mots_) * 4 <= ((4 * len(dict(SYN)[nom_]) + 15) & ~15), nom_
        # sous-table de combat d'Upper copiee : entree 7 (fin de match) -> talon etat7
        e7 = exec_donnee(g, U_T_COMBAT + 4 * 7); o7 = e7 - GRF_X
        assert struct.unpack_from('<I', blob, o7)[0] == X(0x26E900), hex(struct.unpack_from('<I', blob, o7)[0])
        struct.pack_into('<I', blob, o7, g.synth_place['etat7'] + BASE)
        for i_, h_ in enumerate(H_COMBAT):
            v_ = struct.unpack_from('<I', blob, e7 - GRF_X - 28 + 4 * i_)[0]
            assert v_ == h_ + BASE, "T_61C2A0[%d] = %x (attendu Hyper %x)" % (i_, v_, h_ + BASE)
        # sous-table de la scene 4/4 d'Upper copiee : entree 1 (ecran VS + decor d'Hyper) -> talon vs_decor
        e1 = exec_donnee(g, U_T_VS + 4); o1 = e1 - GRF_X
        assert struct.unpack_from('<I', blob, o1)[0] == VS_CIBLE(g), hex(struct.unpack_from('<I', blob, o1)[0])
        struct.pack_into('<I', blob, o1, g.synth_place['vs_decor'] + BASE)
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
    # (etape 7) MENU_ARCADE=1 : le menu du titre d'Hyper ne propose pas l'entree 0 (curseur $C201 : tables « suivant »
    # 0x5B41F0 (Bas) et « precedent » 0x5B4200 (Haut) sans 0 : VERSUS 1, TRAINING 4, OPTION 5, EXIT 6) -> ARCADE (0)
    # insere avant VERSUS : Haut depuis VERSUS = ARCADE, Bas depuis EXIT = ARCADE
    if os.environ.get("MENU_ARCADE", "1") == "1":
        for ex_, t_ in ((0x5B41F0, bytes([1, 4, 5, 5, 5, 6, 0])), (0x5B4200, bytes([6, 0, 1, 1, 1, 4, 5]))):
            o_ = ex_ - BASE; av_ = bytes(mod[o_:o_ + 7]); mod[o_:o_ + 7] = t_
            patchs.append(dict(type='octets', exec=hex(ex_), avant=av_.hex(), apres=t_.hex(), quoi="menu du titre : entree ARCADE (0) accessible"))
    const_(0x318E30, g.synth_place['fin_selection'] + BASE, "fin de selection (0x318C40) : ARCADE -> animations du perso de J1 puis preparation du combat d'Upper 0x24EA30 (adversaire CPU)")
    long_(0x5B5E88, g.synth_place['scene4_mode'] + BASE, "scene A5+4=4 : aiguillage par le mode (ARCADE -> Upper 0x261560)")
    if COMBAT_HYPER:
        jal_(H_SITE_KO_COMPTE, g.synth_place['ko_compte'] + BASE, "K.O. d'Hyper 0x9C940 : comptage des victoires -> ARCADE : Upper 0x269340 (masque des battus, dernier combat), sinon 0x9D240")
    for k, f5, q in ((3, 0x2614A0, 'CONTINUE'), (4, 0x2614D0, 'GAME OVER'), (5, 0x261500, 'FIN + generique')):
        if g.neuf(f5) is not None:
            if COMBAT_HYPER and PLANS:
                long_(0x5B5E80 + 4 * k, g.synth_place['plans_s%X' % (2 * k)] + BASE, "scene A5+4=%X (%s) -> plans d'Upper, Upper 0x%X, plans d'Hyper en sortie vers 0/C" % (2 * k, q, f5))
            else: long_(0x5B5E80 + 4 * k, a_exec(g, f5), "scene A5+4=%X (%s) -> Upper 0x%X" % (2 * k, q, f5))
    # $102 -> $116 (etape2/patch_116.py) : lectures INDEX et CMP a un id de base dans le code greffe
    p116 = []
    if os.environ.get("PATCH_116", "1") == "1":
        import patch_116 as P116
        for a, va, lbva, c, det, t, pat in P116.sites(routines):
            # (etape 3) copies de $102 vers $0132/$0133 (perdant/gagnant : citations, chargeur de fin) et $0147 :
            # consommees par des tables a 40 persos -> perso de BASE (versions ZERO / ZERO 2 / ALPHA d'Hyper)
            # (toutes les COPIES en fait : le code d'Upper ignore les versions ; portraits, noms, palettes et citations
            # sont des tables a 40 persos -- Ryu ALPHA : palette du portrait lue a T[$60])
            if c == 'COPIE' and COPIES_BASE: pat = True
            # TOUT_116=1 (defaut) : toute LECTURE de $102 dans le code greffe (CMP registre/registre ou pseudo-id, AUTRE :
            # arguments passes aux routines d'affichage) lit le perso de base ; seules les ECRITURES gardent $102
            if c != 'ECRITURE' and TOUT_116: pat = True
            if not pat or lbva is None: continue
            n_ = g.neuf(lbva); w = struct.unpack_from('<I', mod, n_)[0]
            assert (w & 0xffff) == 0x102, hex(lbva)
            struct.pack_into('<I', mod, n_, (w & 0xffff0000) | 0x116)
            p116.append(dict(routine=hex(a), mips_upper=hex(lbva), copie=hex(n_ + BASE), classe=c, detail=det))
    for e9, u, d5, d9, i in TC:
        long_(e9, a_exec(g, u), "table 0x%X[%d] (homologue d'Upper 0x%X) : entree nulle -> gestionnaire d'Upper 0x%X" % (d9, i, d5, u))
    # (etape 3) 0x269340 (comptage des victoires d'Upper) : son 1er test, CMPI.W #6,$0138(A5) (combat a 3), est calcule
    # par des temporaires de PILE (fonction a prologue 'sq') et PERDU a la traduction : le BEQ suivant lit les drapeaux
    # de l'appelant (Upper : fin de 0x26ABF0, par chance ; talon ko_compte : TST.B $C201 = 0 -> branche du combat a 3,
    # masque des battus faux, pas d'adversaire suivant). On recopie a sa place la forme standard du meme test prise dans
    # 0x26E900 (0x26EE0C-0x26EEC4, traduite CMPI.W #$6,$0138(A5)) ; le BEQ d'origine (0x269488, sur a0) est garde.
    if COMBAT_HYPER and os.environ.get("CMP138", "1") == "1":
        b5_ = C.load('ro5'); a0_, a1_ = 0x26936C, 0x269488
        forme = [struct.unpack_from('<I', b5_, o)[0] for o in range(0x26EE0C, 0x26EEC8, 4)] + [0x3c037000, 0x8c641150]
        n_ = (a1_ - a0_) // 4; assert len(forme) <= n_
        mots = [0] * (n_ - len(forme)) + forme
        assert struct.unpack_from('<I', b5_, a1_)[0] == 0x1080031a and forme[0] == 0x24120006
        c_ = g.neuf(a0_); struct.pack_into('<%dI' % n_, mod, c_, *mots)
        patchs.append(dict(type='mips', site=hex(c_ + BASE), quoi="0x269340 : test CMPI.W #6,$0138(A5) perdu -> forme standard (0x26EE0C)"))
    # (etape 4) lectures du perso des joueurs PAR A5 ($0503/$0903/$0D03/$1103 en 68K = lb $x02 sur la base A5) dans le
    # code greffe : perso de base ($x17 68K = PS2 $x16), comme les lectures par An (patch_116). Ex. 0x260390 recopie
    # $0503 dans $8E39 (fin de Ken ZERO : id $31 hors des tables a 40 persos)
    if os.environ.get("A5_116", "1") == "1":
        b5_ = C.load('ro5'); E5_ = PL.E5; n116 = 0
        for r_ in routines:
            r7, a5r = set(), set()
            L_ = [Ins(o, struct.unpack_from('<I', b5_, o)[0]) for o in range(r_, E5_[r_], 4)]
            for k_, x_ in enumerate(L_):
                o = x_.va
                # forme « addiu rX,A5,$x02 ; lb rY,0(rX) » (rX ne sert a rien d'autre ensuite)
                if x_.m == 'addiu' and x_.rs in a5r and x_.imm in (0x502, 0x902, 0xD02, 0x1102) and k_ + 1 < len(L_):
                    y_ = L_[k_ + 1]
                    if y_.m in ('lb', 'lbu') and y_.rs == x_.rt and y_.imm == 0 and \
                       not any(z_.rs == x_.rt or (z_.m in GR.MEM and z_.rt == x_.rt and z_.m.startswith('s')) for z_ in L_[k_ + 2:k_ + 8] if GR.dest(z_) != x_.rt):
                        c_ = g.neuf(o); w_ = struct.unpack_from('<I', mod, c_)[0]
                        if (w_ & 0xffff) == x_.imm:
                            struct.pack_into('<I', mod, c_, (w_ & 0xffff0000) | (x_.imm + 0x14)); n116 += 1
                            patchs.append(dict(type='mips', site=hex(c_ + BASE), quoi="lecture A5 $%X -> $%X (perso de base, Upper 0x%X)" % (x_.imm ^ 1, (x_.imm + 0x14) ^ 1, o)))
                if x_.m == 'lui': (r7.add if x_.imm == 0x7000 else r7.discard)(x_.rt); a5r.discard(x_.rt); continue
                if x_.m == 'lw' and x_.rs in r7 and x_.imm == 0x1114: a5r.add(x_.rt); r7.discard(x_.rt); continue
                if x_.m in ('lb', 'lbu') and x_.rs in a5r and x_.imm in (0x502, 0x902, 0xD02, 0x1102):
                    c_ = g.neuf(o); w_ = struct.unpack_from('<I', mod, c_)[0]
                    assert (w_ & 0xffff) == x_.imm
                    struct.pack_into('<I', mod, c_, (w_ & 0xffff0000) | (x_.imm + 0x14)); n116 += 1
                    patchs.append(dict(type='mips', site=hex(c_ + BASE), quoi="lecture A5 $%X -> $%X (perso de base, Upper 0x%X)" % (x_.imm ^ 1, (x_.imm + 0x14) ^ 1, o)))
                d_ = GR.dest(x_)
                if d_ is not None: r7.discard(d_); a5r.discard(d_)
        print("lectures A5 du perso -> base : %d" % n116)
    # (etape 3) ADRESSES VIDEO/RAM FORMEES PAR DECALAGE (MOVE.W #$A3C0,Dn ; LSL.L #8,Dn -> $A3C000 : tampons de palettes de
    # la fin, $8000/$8004(A5)) : 'addiu rX,zero,$A0xx-$A7xx' suivi d'un 'sll 8' -> page de RAM d'Hyper (+$1800 :
    # $A00000 -> $B80000). Sans cela, la fin ecrivait ses palettes en $B04000 (ecran noir).
    if os.environ.get("PAGES_RAM", "1") == "1":
        b5_ = C.load('ro5'); E5_ = PL.E5
        for r_ in routines:
            L_ = [Ins(o, struct.unpack_from('<I', b5_, o)[0]) for o in range(r_, E5_[r_], 4)]
            for i_, x_ in enumerate(L_[:-6]):
                if x_.m == 'addiu' and x_.rs == 0 and 0xA000 <= x_.imm < 0xA800 and \
                   any(y_.m == 'sll' and y_.sa == 8 for y_ in L_[i_ + 1:i_ + 7]):
                    c_ = g.neuf(x_.va); w_ = struct.unpack_from('<I', mod, c_)[0]
                    struct.pack_into('<I', mod, c_, (w_ & 0xffff0000) | (x_.imm + 0x1800))
                    patchs.append(dict(type='mips', site=hex(c_ + BASE), quoi="page RAM formee par decalage $%X -> $%X (Upper 0x%X)" % (x_.imm, x_.imm + 0x1800, x_.va)))
    # (etape 7) ANIM24=1 : Upper 0x20EAD0 lit un pointeur d'animation 24 bits dans une table ([pointeur | parametre << 24])
    # et le masque (dsll32/dsrl32 de 8 = ANDI.L #$00FFFFFF) : chez ro9a le pointeur reloge est une adresse 68K etiquetee
    # $01xxxxxx, le masque efface l'etiquette -> +$1C faux -> plantage du dessin (fin de 02 : acteur de l'emplacement $18).
    # Les cases relogees ont un octet haut nul et une adresse 68K SANS etiquette : le masque est remplace par la pose de
    # l'etiquette (lui a0,$0100 ; or a0,a0,v1 -> $01xxxxxx) ; ANIM24_TAG=0 : simple copie (or a0,v1,zero ; nop).
    if os.environ.get("ANIM24", "1") == "1" and g.neuf(0x20EBCC) is not None:
        b5_ = C.load('ro5')
        assert struct.unpack_from('<2I', b5_, 0x20EBCC) == (0x0003223C, 0x0004223E), [hex(x) for x in struct.unpack_from('<2I', b5_, 0x20EBCC)]
        c_ = g.neuf(0x20EBCC); struct.pack_into('<2I', mod, c_, *((0x3C040100, 0x00832025) if os.environ.get('ANIM24_TAG', '1') == '1' else (0x00602025, 0)))
        patchs.append(dict(type='mips', site=hex(c_ + BASE), quoi="0x20EBCC : masque 24 bits du pointeur d'animation -> copie (etiquette 68K gardee)"))
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
    if Y2: env['HSFA_GREFFE_Y2'] = '%x:%x' % Y2
    if FENETRES: env['HSFA_GREFFE_FEN'] = ','.join('%x:%x:%x' % f for f in FEN); env['HSFA_GREFFE_Y'] = '%x' % FEN[0][2]
    open(os.path.join(P_, 'env.sh'), 'w').write(''.join('export %s=%s\n' % kv for kv in env.items()))
    print("greffe %s : %d routines, MIPS %d o ; zone Z80 [%#x, %#x) %d o ; zone 2 [%#x, %#x) %d o ; donnees : %d copiees (%d o), %d reutilisees, %d ptr code"
          % (nom, len(routines), info['mips'], g.g0, Z80_1, info['zone_z80'][2], Z2_0, g.z2_fin, info['zone2'][2], len(copie), len(blob), len(reutil), len(ptr_code)))
    for k, v in g.rap.items(): print("  %-24s %d" % (k, len(v)))
    print("  A5 hors table : %d %s" % (len(inconnus), ' '.join(sorted('$%04X' % d for d in inconnus))[:300]))
    if '--construire' in sys.argv:
        e = dict(os.environ, **env)
        with open(os.path.join(P_, 'construction.log'), 'w') as f:
            subprocess.run(['nice', '-n', '19', 'python3', 'mame_test.py'], cwd=TRAD, env=e, stdout=f, stderr=subprocess.STDOUT)
        print(open(os.path.join(P_, 'construction.log')).read().splitlines()[-1])

if __name__ == "__main__":
    main()
