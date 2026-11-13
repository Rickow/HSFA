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

def _lien(src, dst):   # (hyperarcade, portabilite) src/hsfa/liens.py (@HA_UT@) : lien symbolique, sinon (Windows sans
    try:               # droit de lien) lien physique ou copie ; HSFA_SANS_LIENS=1 : essai de cette voie
        if "@HA_UT@" not in sys.path: sys.path.append("@HA_UT@")
        import liens
    except ImportError:
        liens = None
    if liens: liens.lien(src, dst); return
    try: os.symlink(src, dst)
    except (OSError, NotImplementedError):
        import shutil; shutil.copyfile(src, dst)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etape2'))
# (etape 3) donnees : critere de pointeur de donnees2.py (preuves du journal des conversions, filtre des paires de
# mots signes et des longs impairs, plages chevauchantes) ; DONNEES3=0 : criteres de l'etape 2
if os.environ.get("DONNEES3", "1") == "1":
    os.environ.setdefault("PREUVES", "@HA_G@/donnees/pointeurs_prouves.txt")
    os.environ.setdefault("FILTRE3", "1"); os.environ.setdefault("OU3", "1"); os.environ.setdefault("TABLES_PTR", "1")
    os.environ.setdefault("SEG_REFS", "0"); os.environ.setdefault("DECALAGES16", "1")   # SEG_REFS=1 : bloc trop grand pour le 68K
    os.environ.setdefault("PLAFOND_DEC", "d200")                                         # citations : $CF63 + marge
    os.environ.setdefault("ECART_REGION", "80")                                          # place (journaux de lecture des 40 persos)
import plan as PL
import greffe as GR
import commun as C
from mips import Ins
G = GR.G; BASE = GR.BASE
MODULE_SOURCE = "@HA_MODULES_SON@/ro9_usa_prog68k.bin"       # Hyper + redirection des voix (actuel)
SON_DONNEES = "@HA_MODULES_SON@/son_donnees_ro9.bin"
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
    FEN_68K = [(0xD0C000, 0xF00000), (int(os.environ.get('FEN2_DEBUT', 'C70000'), 16), 0xC84000)]   # (28/10) FEN2_DEBUT : ext_940000 plus long
# (31/10, ossature des decors etape 2, conflit C4) DONNEES_TROU=1 : la coupure d'ext_940000 reste en PS2 $850CF0
# (ext_940000 inchange), l'image de ro9a rend $3C000 octets au code, la tranche de donnees d'Hyper qui en sort va dans
# la fin de T1b ($5D4000, borne $618000 = RAM QSound) : traducteur HSFA_DONNEES_TROU=y:n:coupure:borne
if os.environ.get("DONNEES_TROU", "1") == "1":
    os.environ.setdefault("HSFA_DONNEES_TROU", "5d4000:3c000:850cf0:618000")
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
    # (28/10) TROUS_PLAN=1 : plan d'allocation commun (re/allocations.tsv, 0c47636) : la greffe n'a que T1a $410000-$4D7FFF
    # et T2 $61A000-$65FFFF (T1b, T3 : decors ; T4, T5 : MAX dans Hyper ; T6, T7 : decors / 16:9)
    if os.environ.get("TROUS_PLAN", "1") == "1":
        FEN_68K = FEN_68K[:2] + [(0x410000, 0x4D8000), (0x61A000, 0x660000)]
# (01/11, ro9a17, decors etape 1) D4_TABLE=1 : table perso -> decor de 128 octets (regle D4, id etendu $103) dans T1b.
# Le dernier morceau PS2 du bloc ($FE0000-$FF0000, jusqu'ici promis a T2 et jamais atteint : le bloc finit vers
# $FC2000) devient la FENETRE DES DECORS, servie en 68K a $4D8000 (debut de T1b, plan d'allocation) ; le bloc de donnees
# est complete de zeros jusqu'a $FE0000, puis la table y est posee. D4_TABLE=0 : ro9a16.
D4_TABLE = os.environ.get("D4_TABLE", "1") == "1"
FEN_DECORS = (0xFE0000, 0xFF0000, 0x4D8000)          # PS2 [lo, hi) -> 68K y (T1b $4D8000-$5D3FFF)
if FENETRES and TROUS and D4_TABLE and os.environ.get("TROUS_PLAN", "1") == "1":
    assert FEN_PS2[-1] == (0xE80000, 0xFF0000), FEN_PS2
    FEN_PS2 = FEN_PS2[:-1] + [(0xE80000, FEN_DECORS[0]), FEN_DECORS[:2]]
    FEN_68K = FEN_68K[:-1] + [(FEN_DECORS[2], FEN_DECORS[2] + FEN_DECORS[1] - FEN_DECORS[0])]
def table_d4():
    """128 octets : decor D4 (numerotation unique) par id etendu $00-$7F (decors/d4/regle_d4_decidee.tsv).
    (e25) D4_ORDRE=1 (defaut) : octet i du bloc = D4[i] : la lecture traduite MOVE.B T_fe0000(PC,D0.W) rend l'octet i du
    bloc (mesure e25a : avec l'ordre « i ^ 1 » de ro9a17, J2 $19 donnait $30 = D4[$18] et $00 donnait $02 = D4[$01]).
    D4_ORDRE=0 : ordre de ro9a17 (t[i ^ 1] = D4[i])."""
    t = bytearray(128); x = 0 if os.environ.get("D4_ORDRE", "1") == "1" else 1
    # (L1 des MAX) D4_REGLE = nom du fichier de regle dans decors/d4/ (defaut regle_d4_decidee.tsv) ; regle_d4_l1.tsv :
    # Yun / Ingrid en $2D / $2E (ids d'Upper MAX), $28 / $29 inutilises (base Ryu, decor $00)
    for l in open(os.path.join(G, 'decors', 'd4', os.environ.get("D4_REGLE", "regle_d4_decidee.tsv"))).read().splitlines()[1:]:
        c = l.split('\t'); t[int(c[0][1:], 16) ^ x] = int(c[5][1:], 16)
    return bytes(t)
if FENETRES: GRF_X = FEN_PS2[0][0]
# (01/11 soir, e25) D4_CHALLENGER=1 : regle D4 sur le VRAI trajet du nouveau challenger (et sur le choix du decor de
# l'adversaire suivant, meme code) : Upper 0x24EA30 (fin de selection) lit $103 de A1 (perso de l'adversaire ou du
# challenger) puis 0x24F020 : $174 = 2 x T_61BE10[id] (0x251950). Dans la copie : (a) la lecture 0x24EFD8 revient a $103
# (id ETENDU, ecrit juste avant en 0x24EF8C ; TOUT_116 la passait a $117, PERIME a ce moment : perso de l'adversaire
# PRECEDENT) ; (b) jal 0x251950 -> talon d4_choix (EXT.W D0 ; MOVE.B T_D4(D0.W),D0) et ADD.W D0,D0 (7 mots) -> nop
# (D4 est deja en numerotation unique = 2 x T_61BE10 pour les ids $00-$25) ; (c) Hyper 0x31D6A0 (arrivee du challenger,
# $100 = 2 x $103 de J2, garde dans $172) : ADD.W D0,D0 (0x31D880-0x31D894) -> MOVE.B T_D4(D0.W),D0. =0 : comme avant.
D4_CHALLENGER = os.environ.get("D4_CHALLENGER", "1") == "1"
D4_CHOIX = D4_CHALLENGER and D4_TABLE and FENETRES and TROUS     # talon d4_choix present
def stub_d4_choix(t_d4):
    """EXT.W D0 (copie de 0x251950) ; MOVE.B T_D4(D0.W),D0 (forme du recompilateur reconnue : lh/lui/addiu/addu/lb/sb) ; RTS"""
    w = [0x3c037000, 0x80631124, 0x0003263c, 0x0004263f, 0x3c037000, 0xa4641124]
    w += [0x3c027000, 0x84441124, 0x3c030000 | (((t_d4 + 0x8000) >> 16) & 0xffff), 0x24630000 | (t_d4 & 0xffff),
          0x00831821, 0x80640000, 0xa0441124]
    return w + [0x03e00008, 0x00000000]
# (e28) D4_VERSUS=1 (decision de l'utilisateur) : regle D4 en VERSUS : le decor suit le perso ET la version de J2 (table
# D4). Mesure (tapd_e28c) : en VERSUS, le decor du combat est $174 recopie par l'init de match d'Hyper 0x96C20
# (MOVE.W $174(A5),$100(A5)) ; $174 n'est ecrit que par le choix du decor du VERSUS 0x321220 (curseur $C314) et, hors
# VERSUS, par 0xA49E0 (non appele en VERSUS). Site 0x96C0C-0x96C20 (6 mots) -> jal talon d4_vs : si $C201(A5) = 1
# (VERSUS) : $174 = D4[$103 de J2] (MOVE.B $903(A5),D0), drapeau $FE11 = 1, decor d'Upper ($174 < $50) -> $FE10 = 1,
# sinon $FE10 = 0 et repli par famille (SFA2 $50-$9F -> 2, SFA1 >= $A0 -> 0, comme Hyper) ; autres modes : $FE11 = 0.
# Puis MOVE.W $174(A5),$100(A5) comme Hyper. Les talons moteur_* acceptent ($FE00 ou $FE11) et $FE10. =0 : comme ro9a20.
D4_VERSUS = os.environ.get("D4_VERSUS", "1") == "1"
FLAG_VS = 0xFE11
H_D4_SITE = 0x96C0C
def stub_d4_vs(t_d4):
    w = [0x27bdff40, 0xffbf00b8]
    w += forme_cmpi_b(0xC201, 1); bh = len(w); w += [0x14400000, 0x00000000]            # bne -> Lh (pas VERSUS)
    w += [0x3c037000, 0x8c631114, 0x80640902, 0x3c037000, 0xa0641124]                    # MOVE.B $903(A5),D0 (J2)
    w += stub_d4_choix(t_d4)[:-2]                                                        # D0 = D4[id] (deja double)
    w += [0x3c037000, 0x84641124, 0x3c037000, 0x8c631114, 0xa4640174]                    # MOVE.W D0,$174(A5)
    w += _pose_octet(FLAG_VS, 1)
    w += forme_cmpi_w(0x174, 0x50) + [0x3c037000, 0x8c631158]; bu = len(w); w += [0x04600000, 0x00000000]   # BCS -> Lu
    w += _pose_octet(FLAG_DECOR, 0)
    w += forme_cmpi_w(0x174, 0xA0) + [0x3c037000, 0x8c631158]; b2 = len(w); w += [0x04600000, 0x00000000]   # BCS -> L2
    w += [0x24030000, 0x3c027000, 0x8c421114, 0xa4430174]; j0 = len(w); w += [0x10000000, 0x00000000]      # SFA1 -> 0
    L2 = len(w); w += [0x24030002, 0x3c027000, 0x8c421114, 0xa4430174]; j2 = len(w); w += [0x10000000, 0x00000000]
    Lu = len(w); w += _pose_octet(FLAG_DECOR, 1); jf = len(w); w += [0x10000000, 0x00000000]
    Lh = len(w); w += _pose_octet(FLAG_VS, 0)
    Lr = len(w); w += [0x3c027000, 0x8c421114, 0x84430174, 0x3c027000, 0x8c421114, 0xa4430100]   # MOVE.W $174(A5),$100(A5)
    w += [0xdfbf00b8, 0x27bd00c0, 0x03e00008, 0x00000000]
    for i, L in ((bh, Lh), (bu, Lu), (b2, L2), (j0, Lr), (j2, Lr), (jf, Lr)): w[i] |= (L - i - 1) & 0xffff
    return w

# ---------------------------------------------------------------------------------------------------------------
# (e43, ro9a33, decision de l'utilisateur du 08/11) TIRAGE_CPU=1 : VERSION DES ADVERSAIRES CPU TIREE AU HASARD parmi
# celles qui existent pour le perso (grille normale d'Hyper 0x5C5380 : ZERO / ZERO 2 / ALPHA / ZERO 3 ; EX et S-ISM
# hors tirage). Sites : la lecture « MOVE.B $103(A1),D0 ; JSR 0x24F020 » (choix du decor) de 0x24EA30 (1er adversaire,
# 0x24EFD0) et de 0x250EF0 (adversaire suivant, 0x2512CC), juste APRES l'ecriture de l'id ($103) et de l'ISM ($133) de
# l'adversaire par Upper -> jal talon tirage_N. Le talon : (1) pas de tirage si $AD(A5) = 3 (site 1 : defi, deux humains),
# si le rang $114 (D0) = $14C (dernier combat : boss final, ZERO 3), si l'id >= $24 (Shin Akuma, EX Balrog...) ou si
# TIRAGE_COUPE ($FF7E20 non nul) ; (2) indice = id x 64 + (octet haut de la graine $AE(A5)) / 4 -> T_TIR (64 cases par
# id, versions de la grille reparties : tirage reproductible par la graine du jeu, sans appel au generateur) ; (3) $103 =
# version, $117 (perso de base) = T_5C5300[id], $116 (drapeaux) = T_5C2490[id] (copies T_BASE / T_VER) ; version non
# ZERO 3 -> $133 (ISM) = 0 comme la selection d'Hyper (0x50AAA0 : CLR) et drapeau $FF7E21 = 1 ; (4) choix du decor
# (copie de 0x24F020) avec D0 = perso de base si version non ZERO 3 (decors SFA1 / SFA2 pas encore integres -> decor
# d'Upper du perso), sinon $103 ; (5) version non ZERO 3 et decor IMPOSE par Upper ($110 = $FF, rival au rang 8) -> decor
# du perso (regle D4 : « decors imposes d'Upper seulement si J2 est en ZERO 3 ») : $174 = D4[base], $110 = 0.
TIRAGE_CPU = os.environ.get("TIRAGE_CPU", "0") == "1"
TIR_COUPE, TIR_NONZ3, TIR_ID = 0xFE20, 0xFE21, 0xFE22     # $FF7E20-$FF7E22 (re_ajouts/allocations.tsv)
TIR_OFF = 0x1000                                          # tables dans la fenetre des decors : PS2 $FE1000 = 68K $4D9000
TIR_IDS = 0x40                                            # lignes de T_TIR (ids $00-$3F ; >= $40 : pas de tirage)
GRILLE_H, TBASE_H, TVER_H = 0x5C5380, 0x5C5300, 0x5C2490  # tables d'Hyper (exec)
# (e44, ro9a34, decision du 08/11 apres ro9a33) TIRAGE_MODES=1 (avec TIRAGE_CPU=1 ; defaut 0 -> ro9a33 a l'octet) : le
# tirage couvre aussi (1) les versions de la grille « Start tenu » d'Hyper 0x5C5420 absentes de la grille normale
# (EX ALPHA / ZERO 2 et versions « classiques » : TIRAGE_EX, defaut 7b 7a 78 79 76 75 56 55 7c 52 72 5d 7d ; hors tirage :
# Shin Akuma $24/$54/$74 (boss), EX Bison / Sagat ZERO 2 $58/$59 (donnees PS2 pointant sur Ryu, ETATS-HYPER §1.3),
# EX Balrog $25) et (2) les modes de l'ecran de mode ZERO 3 (0x50B890, champs PS2 du joueur) : 1 MAZI ($15A = 1), 2 SAIKYO
# ($131 = 1), 3 CLASSIC ($15E = 1, $132 = $FF), 4 S-ISM rouge ($122 = $80, $132 = 0), 5 S-ISM bleu = Mazi S-ISM ($122 = 2,
# $132 = $FF), 6 S-ISM vert ($122 = $82, $132 = 0), 7 EX ZERO 3 = Saikyo S-ISM ($15E = $81, $132 = $FF ; 12 persos de SF2,
# 0x5C5510[id] = 1) : TIRAGE_MODES_LISTE (defaut 1..7). Tirage UNIFORME parmi les modes du perso (versions + EX + modes
# ZERO 3 ; ZERO 3 NORMAL = 1 mode ; a 1/64 pres). Codage de T_TIR : octet < $80 = id de version ; $80 + m = mode m de
# l'id d'Upper (ZERO 3). Le talon remet a 0 les 4 champs de mode du CPU ($15A, $131, $15E, $122) a chaque adversaire
# hors defi / tirage coupe (combat final, Shin Akuma : ZERO 3 NORMAL), puis pose ceux du mode tire (tables T_Mxxx).
# TIRAGE_SEUL=1 (essais) : seulement les EX et modes (versions normales hors tirage quand le perso en a).
TIRAGE_MODES = TIRAGE_CPU and os.environ.get("TIRAGE_MODES", "0") == "1"
TIR_V = 0xFE23                                            # $FF7E23 : valeur tiree (id ou $80 + mode) (re_ajouts)
TIR_EX = tuple(int(x, 16) for x in os.environ.get("TIRAGE_EX", "7b,7a,78,79,76,75,56,55,7c,52,72,5d,7d").split(',') if x)
TIR_MODES_L = tuple(int(x) for x in os.environ.get("TIRAGE_MODES_LISTE", "1,2,3,4,5,6,7").split(',') if x)
TIR_SEUL = os.environ.get("TIRAGE_SEUL", "0") == "1"
# (e44) TIRAGE_EXCLUS=3c : versions retirees du tirage (Dan ZERO $3C : CPU perdant AU TEMPS -> n'entre jamais dans son
# etat de defaite (02/0A), $10A(A5) reste a 1, attente sans fin en 68K $017D18 ; VERSUS (Dan humain) : normal)
TIR_EXCLUS = tuple(int(x, 16) for x in os.environ.get("TIRAGE_EXCLUS", "").split(',') if x) if TIRAGE_MODES else ()
GRILLE_EX_H, SF2_H = 0x5C5420, 0x5C5510
#                 m :   1     2     3     4     5     6     7          (index 0 = inutilise)
TIR_CHAMPS = ((0x15A, (0, 1, 0, 0, 0, 0, 0, 0)), (0x131, (0, 0, 1, 0, 0, 0, 0, 0)),
              (0x15E, (0, 0, 0, 1, 0, 0, 0, 0x81)), (0x122, (0, 0, 0, 0, 0x80, 2, 0x82, 0)))
# (e44) TIRAGE_COPIES=1 : aussi les copies que l'init de manche d'Hyper (fichier 0x2A1EAC) ne fait que pour un humain
# (68K $124 = 0) : $F0 <- $15E, $EC <- $15A, $EB <- $131 (numerotation PS2)
if TIRAGE_MODES and os.environ.get("TIRAGE_COPIES", "0") == "1":
    TIR_CHAMPS = TIR_CHAMPS + ((0xF0, TIR_CHAMPS[2][1]), (0xEC, TIR_CHAMPS[0][1]), (0xEB, TIR_CHAMPS[1][1]))
TIR_ISM = (0, 0, 0, 0xFF, 0, 0xFF, 0, 0xFF)               # $132 pose pour m >= 3 (m = 1, 2 : ism tire par Upper garde)
def modes_perso(i, h=None):
    """liste des valeurs tirables pour l'id d'Upper i (< $24)"""
    h = h or open(MODULE_SOURCE, 'rb').read()
    tb = h[TBASE_H - BASE:TBASE_H - BASE + 128]
    g4 = h[GRILLE_H - BASE + 4 * i:GRILLE_H - BASE + 4 * i + 4]
    vers = [v for v in g4 if v != 0xFF]
    assert i in vers and all(tb[v] == i for v in vers), (hex(i), g4.hex())
    if not TIRAGE_MODES: return vers
    e4 = h[GRILLE_EX_H - BASE + 4 * i:GRILLE_EX_H - BASE + 4 * i + 4]
    ex = [v for v in e4 if v != 0xFF and v not in vers and v in TIR_EX]
    assert all(tb[v] == i for v in ex), (hex(i), e4.hex())
    sf2 = h[SF2_H - BASE + i]
    md = [0x80 | m for m in TIR_MODES_L if m != 7 or sf2 == 1]
    if TIR_SEUL and (ex or md): vers = []
    vers = [v for v in vers if v not in TIR_EXCLUS or v == i]
    sv = os.environ.get("TIRAGE_SEULE_VER")              # (e44, essais) seulement les versions de drapeaux T_VER = sv
    if sv:
        tv = h[TVER_H - BASE:TVER_H - BASE + 128]
        k = [v for v in vers + ex if tv[v] == int(sv, 16)]
        return k or [i]
    return vers + ex + md
def tables_tirage():
    """T_TIR (TIR_IDS x 64 o), T_BASE (128 o), T_VER (128 o), T_D4A (128 o, decor Arcade : D4[id] si decor d'Upper
    ($00-$4F), sinon D4[perso de base]), ordre « octet i du bloc = valeur i » (comme table_d4) ; (e44, TIRAGE_MODES)
    puis T_M132 et les tables des champs de mode (8 o chacune, indice m)."""
    h = open(MODULE_SOURCE, 'rb').read()
    tb = h[TBASE_H - BASE:TBASE_H - BASE + 128]; tv = h[TVER_H - BASE:TVER_H - BASE + 128]
    d4 = table_d4() if os.environ.get("D4_ORDRE", "1") == "1" else None
    t = bytearray()
    exclus = {0x12, 0x13, 0x14}
    for i in range(TIR_IDS):
        if i < 0x24 and i not in exclus: vers = modes_perso(i, h)
        else: vers = [i]
        t += bytes(vers[r * len(vers) // 64] for r in range(64))
    d4a = bytes((d4[i] if d4[i] < 0x50 else d4[tb[i]]) for i in range(128)) if d4 else bytes(128)
    r = [bytes(t), tb, tv, d4a]
    if TIRAGE_MODES: r += [bytes(TIR_ISM)] + [bytes(v) for _, v in TIR_CHAMPS]
    return tuple(r)
def _adr_tm(k):
    """(e44) adresse PS2 de la table de mode k (0 = T_M132, 1.. = TIR_CHAMPS), indice m"""
    return _adr_tir(3) + 128 + 8 * k
def _d0_vers_a5(d68):
    """MOVE.B D0,d68(A5) (forme de _a1_d0 sur A5)"""
    return [0x3c027000, 0x80431124, 0x3c027000, 0x8c421114, 0xa0430000 | ((d68 ^ 1) & 0xffff)]
def _d0_de_a5(d68):
    """MOVEQ #0,D0 ; MOVE.B d68(A5),D0 (forme de MOVE.B $AE(A5),D1 du talon)"""
    return [0x3c037000, 0xac601124, 0x3c037000, 0x8c631114, 0x80640000 | ((d68 ^ 1) & 0xffff), 0x3c037000, 0xa0641124]
def _clr_a1(off):
    """CLR.B off(A1) (off = deplacement MIPS ; forme de CLR.B $133(A1))"""
    return [0x3c027000, 0x8c421104, 0xa0400000 | off]
def _adr_tir(k):
    """adresse PS2 des tables : 0 T_TIR, 1 T_BASE, 2 T_VER, 3 T_D4A"""
    return FEN_DECORS[0] + TIR_OFF + (0, TIR_IDS * 64, TIR_IDS * 64 + 128, TIR_IDS * 64 + 256)[k]
def _lit_table(t):
    """MOVE.B T(D0.W),D0 (forme de stub_d4_choix, D0.W >= 0)"""
    return [0x3c027000, 0x84441124, 0x3c030000 | (((t + 0x8000) >> 16) & 0xffff), 0x24630000 | (t & 0xffff),
            0x00831821, 0x80640000, 0xa0441124]
def _d0_a1(off):
    """MOVEQ #0,D0 ; MOVE.B off(A1),D0 (off = deplacement MIPS)"""
    return [0x3c037000, 0xac601124, 0x3c037000, 0x8c631104, 0x80640000 | off, 0x3c037000, 0xa0641124]
def _a1_d0(off):
    """MOVE.B D0,off(A1) (off = deplacement MIPS)"""
    return [0x3c027000, 0x80431124, 0x3c027000, 0x8c421104, 0xa0430000 | off]
def _btst4_a1():
    """BTST #4,$116(A1) (drapeau ZERO 3 ; forme d'Hyper 0x3893C8) -> RES (0x1150)"""
    return [0x3c037000, 0x8c631104, 0x80630117, 0x00031e3c, 0x00031e3f, 0x30640010, 0x3c037000, 0xac641150]
def _btst4_a5(d68):
    """BTST #4,d68(A5) -> RES"""
    return [0x3c037000, 0x8c631114, 0x80630000 | ((d68 ^ 1) & 0xffff), 0x00031e3c, 0x00031e3f, 0x30640010, 0x3c037000, 0xac641150]
_RES = [0x3c037000, 0x8c631150]                             # lw v1,RES
def forme_cmp_14c():
    """CMP.W $014C(A5),D0 (forme d'Upper 0x2510FC-0x2511C8) -> C (0x1158) et RES (0x1150)"""
    b5_ = C.load('ro5')
    f = [struct.unpack_from('<I', b5_, o)[0] for o in range(0x2510FC, 0x2511CC, 4)]
    assert f[2] == 0x8463014c and f[-1] == 0xac641150, [hex(x) for x in f[:3]]
    return f
def stub_tirage(cible, site1):
    """talon des sites 0x24EFD0 (site1) / 0x2512CC ; cible = copie de 0x24F020 (exec)"""
    w = [0x27bdff40, 0xffbf00b8]
    w += _pose_octet(TIR_NONZ3, 0)
    sauts = []                                                                    # -> Lread
    if site1:
        w += forme_cmpi_b(0xAD, 3) + _RES; sauts.append(len(w)); w += [0x10600000, 0]      # $AD = 3 -> Lread
    w += _test_octet(TIR_COUPE); sauts.append(len(w)); w += [0x14600000, 0]                  # coupe -> Lread
    if TIRAGE_MODES:                                                              # (e44) champs de mode du CPU a 0
        for off, _ in TIR_CHAMPS: w += _clr_a1(off)
    w += forme_cmp_14c() + _RES; sauts.append(len(w)); w += [0x10600000, 0]                  # rang = $14C -> Lread
    w += [0x3c027000, 0x8c421104, 0x80430102, 0x3c027000, 0x8c421114, 0xa0430000 | ((TIR_ID ^ 1) & 0xffff)]  # MOVE.B $103(A1),$FE22(A5)
    w += forme_cmpi_b(TIR_ID, TIR_IDS) + [0x3c037000, 0x8c631158]; i_hors = len(w); w += [0x04610000, 0]   # BCC (>= TIR_IDS) -> Lread
    sauts.append(i_hors)
    w += _d0_a1(0x102)                                                            # D0 = id
    w += [0x3c037000, 0x94631124, 0x00032180, 0x3c037000, 0xa4641124]             # LSL.W #6,D0
    w += [0x3c037000, 0xac601128, 0x3c037000, 0x8c631114, 0x806400AF, 0x3c037000, 0xa0641128]   # MOVEQ #0,D1 ; MOVE.B $AE(A5),D1
    w += [0x3c037000, 0x94631128, 0x00032082, 0x3c037000, 0xa4641128]             # LSR.W #2,D1
    w += [0x3c037000, 0x84641124, 0x3c037000, 0x84631128, 0x00832021, 0x3c037000, 0xa4641124]   # ADD.W D1,D0
    w += _lit_table(_adr_tir(0))                                                  # D0 = T_TIR[...]
    if TIRAGE_MODES:                                                              # (e44) $80 + m : mode ZERO 3
        w += _d0_vers_a5(TIR_V)
        w += forme_cmpi_b(TIR_V, 0x80) + [0x3c037000, 0x8c631158]; i_ver = len(w); w += [0x04600000, 0]   # BCS -> Lver
        for k_, (off, _) in enumerate(TIR_CHAMPS):
            w += _d0_de_a5(TIR_V) + _lit_table(_adr_tm(1 + k_) - 0x80) + _a1_d0(off)
        w += forme_cmpi_b(TIR_V, 0x83) + [0x3c037000, 0x8c631158]; sauts.append(len(w)); w += [0x04600000, 0]   # m < 3 -> Lread
        w += _d0_de_a5(TIR_V) + _lit_table(_adr_tm(0) - 0x80) + _a1_d0(0x132)    # $133 (68K) = ism du mode
        sauts.append(len(w)); w += [0x10000000, 0]                                 # -> Lread (ZERO 3 : id d'Upper)
        w[i_ver] |= (len(w) - i_ver - 1) & 0xffff
    w += _a1_d0(0x102)                                                            # $103 = T_TIR[...]
    w += _d0_a1(0x102) + _lit_table(_adr_tir(1)) + _a1_d0(0x116)                  # $117 = T_BASE[id]
    w += _d0_a1(0x102) + _lit_table(_adr_tir(2)) + _a1_d0(0x117)                  # $116 = T_VER[id]
    w += _btst4_a1() + _RES; i_z3 = len(w); w += [0x14600000, 0]                  # ZERO 3 -> Lread
    sauts.append(i_z3)
    w += _pose_octet(TIR_NONZ3, 1)
    w += [0x3c027000, 0x8c421104, 0xa0400132]                                     # CLR.B $133(A1)
    Lread = len(w)
    w += _test_octet(TIR_NONZ3); i_id = len(w); w += [0x10600000, 0]              # 0 -> Lid
    w += [0x3c027000, 0x8c421104, 0x80430116, 0x3c027000, 0xa0431124]             # MOVE.B $117(A1),D0 (perso de base)
    j_c = len(w); w += [0x10000000, 0]
    Lid = len(w); w += [0x3c027000, 0x8c421104, 0x80430102, 0x3c027000, 0xa0431124]   # MOVE.B $103(A1),D0 (original)
    Lc = len(w); w += [j_(3, cible), 0]
    w += _test_octet(TIR_NONZ3); i_f1 = len(w); w += [0x10600000, 0]               # Z3 -> Lfin
    w += _test_octet(0x110); i_f2 = len(w); w += [0x10600000, 0]                   # decor non impose -> Lfin
    w += _d0_a1(0x116) + _lit_table(FEN_DECORS[0])                                 # D0 = D4[base] (deja double)
    w += [0x3c037000, 0x84641124, 0x3c037000, 0x8c631114, 0xa4640174]              # MOVE.W D0,$174(A5)
    w += _pose_octet(0x110, 0)
    Lf = len(w); w += [0xdfbf00b8, 0x27bd00c0, 0x03e00008, 0x00000000]
    for i in sauts: w[i] |= (Lread - i - 1) & 0xffff
    w[i_id] |= (Lid - i_id - 1) & 0xffff; w[j_c] |= (Lc - j_c - 1) & 0xffff
    for i in (i_f1, i_f2): w[i] |= (Lf - i - 1) & 0xffff
    return w
TIR_SITES = (0x24EFD0, 0x2512CC)
TIR_AVANT = (0x3c027000, 0x8c421104, 0x80430102, 0x3c027000, 0xa0431124)     # (lb $102 : deja rendu par D4_CHOIX)

# (e43, ro9a33, decision du 08/11) MUSIQUE_RIVAL=1 : en ARCADE, si J1 ET J2 sont en ZERO 3, themes speciaux d'Upper
# (son choix 0x329C18 = img_ro5 $2B88A, table img_ro5 $A9690) : boss ($15C de J2 non nul, combat final) -> $0020 ; rang 9
# contre Ryu -> $0028 ; rang 8 sur decor $14 (rival, decor impose) -> $0029 ; rang 8 sur decor $04 -> $001B ; sauf
# $140(A5) ou $15C(A5) non nul (comme Upper). Sinon (une version non ZERO 3) : theme du J2 dans sa version (choix
# d'Hyper, MUSIQUE_J2). Site : fin du choix d'Hyper 0x3890D0, 4 mots 0x3896B4-0x3896C0 (TST du 2e code $C3B6, lu par
# l'appelant 0x388C18 : BEQ) -> jal talon musique_rival ; le talon refait ce TST en sortie.
MUSIQUE_RIVAL = os.environ.get("MUSIQUE_RIVAL", "0") == "1"
MUS_SITE = 0x3896B4
MUS_AVANT = (0x0004243c, 0x0004243f, 0x3c037000, 0xac641150)
def stub_musique_rival():
    w = [0x27bdff40, 0xffbf00b8]
    fins = []
    w += _test_octet(FLAG); fins.append(len(w)); w += [0x10600000, 0]                          # hors Arcade -> Lfin
    for d in (0x516, 0x916):                                                                     # J1, J2 en ZERO 3 ?
        w += _btst4_a5(d) + _RES; fins.append(len(w)); w += [0x10600000, 0]
    if TIRAGE_MODES:                    # (e44) J2 dans un mode a musique propre (CLASSIC / EX ZERO 3 : table EX ; Mazi S-ISM :
        w += _test_octet(0x95F); fins.append(len(w)); w += [0x14600000, 0]                       # variante B) -> Lfin
        w += forme_cmpi_b(0x923, 2) + _RES; fins.append(len(w)); w += [0x10600000, 0]
    w += _test_octet(0x140); fins.append(len(w)); w += [0x14600000, 0]
    w += _test_octet(0x95C); i_boss = len(w); w += [0x14600000, 0]                              # $15C(J2) -> L20
    w += _test_octet(0x15C); fins.append(len(w)); w += [0x14600000, 0]
    w += forme_cmpi_w(0x114, 9) + _RES; i_r9 = len(w); w += [0x14600000, 0]                    # rang <> 9 -> L8
    w += forme_cmpi_b(0x917, 0) + _RES; i_ryu = len(w); w += [0x14600000, 0]                   # J2 <> Ryu -> L8
    def _code(c): return [0x24030000 | c, 0x3c027000, 0x8c421114, 0xa443c3b8, 0x24030000, 0x3c027000, 0x8c421114, 0xa443c3b6]
    w += _code(0x28); fins.append(len(w)); w += [0x10000000, 0]                                  # $C3B8 = code, $C3B6 = 0
    L8 = len(w)
    w += forme_cmpi_w(0x114, 8) + _RES; fins.append(len(w)); w += [0x14600000, 0]
    w += forme_cmpi_w(0x100, 0x14) + _RES; i_14 = len(w); w += [0x14600000, 0]                 # decor <> $14 -> L04
    w += _code(0x29); fins.append(len(w)); w += [0x10000000, 0]
    L04 = len(w)
    w += forme_cmpi_w(0x100, 0x04) + _RES; fins.append(len(w)); w += [0x14600000, 0]
    w += _code(0x1b); fins.append(len(w)); w += [0x10000000, 0]
    L20 = len(w); w += _code(0x20)
    Lf = len(w)
    w += [0x3c037000, 0x8c631114, 0x8464c3b6] + list(MUS_AVANT) + [0x3c037000, 0xac601158]   # TST.W $C3B6(A5)
    w += [0xdfbf00b8, 0x27bd00c0, 0x03e00008, 0x00000000]
    for i in fins: w[i] |= (Lf - i - 1) & 0xffff
    for i, L in ((i_boss, L20), (i_r9, L8), (i_ryu, L8), (i_14, L04)): w[i] |= (L - i - 1) & 0xffff
    return w

# (e43, ro9a33, point 3 : fins 0d et 18) GARDE_ANIM0=1 : dessin d'un acteur par Hyper (0x393CD0 = img $95152, homologue
# d'Upper img_ro5 $2C70A, code identique) : un acteur mis dans la liste d'affichage avant que son animation ($1C) soit
# posee (acteurs de fin d'Upper crees par les routines « impose » 0x1FF950 / 0x1FFDA0 : $FFBE00 « 0001 0148 », anim 0)
# etait dessine avec l'image lue a l'adresse 0 (type $0066 -> saut hors table -> A2 = pointeur de sortie des sprites
# ecrase -> erreur d'adresse au dessin de l'acteur suivant, pc $A08). Site 0x393CF4-0x393D24 (MOVEA.L $1C(A6),A0 ;
# MOVEA.L 4(A0),A0 ; JSR 0x583D40, 13 mots) -> jal talon garde_anim0 : TST.L $1C(A6) ; BEQ fin ; puis ces 13 mots.
GARDE_ANIM0 = os.environ.get("GARDE_ANIM0", "0") == "1"
GA_SITE = 0x393CF4
# (e43, demande du coordinateur : VERSUS d'Hyper inchange) GARDE_LISTE=1 : meme garde, mais A L'ENTREE DANS LA LISTE
# D'AFFICHAGE et seulement depuis les routines de fin greffees GARDE_LISTE_R (defaut 1ff950,1ffda0 = fin 0d) : leurs
# JSR 0xC67B0 (Upper : ajout de l'acteur A6 a la liste d'affichage, copie greffee) -> talon garde_liste : TST.L $1C(A6) ;
# BEQ fin ; JSR copie de 0xC67B0. Mesure (sv_0d, SURV $FFEECA) : l'acteur $FFBE00 sans anim est ajoute a la liste $7136
# par 0x1FFF1C (dans 0x1FFDA0). Aucun code d'Hyper touche -> VERSUS = ro9a32.
GARDE_LISTE = os.environ.get("GARDE_LISTE", "0") == "1"
GARDE_LISTE_R = tuple(int(x, 16) for x in os.environ.get("GARDE_LISTE_R", "1ff950,1ffda0").split(',') if x)
def stub_garde_liste(cible):
    w = [0x27bdfff0, 0xffbf0000]
    w += [0x3c037000, 0xac601158, 0x3c037000, 0x8c631118, 0x8c64001c, 0x3c037000, 0xac641150] + _RES   # TST.L $1C(A6)
    i0 = len(w); w += [0x10600000, 0]
    w += [j_(3, cible), 0]
    w[i0] |= (len(w) - i0 - 1) & 0xffff
    return w + [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
# (e45, ro9a35b) DAN_SUPER=1 : super de Dan (etat +7 = $10, routine du perso fichier 0x174FC8) : le chemin ZERO est choisi
# (BTST #0,$D2 ; $6 = $10 ; TST.B $83 ; BNE ; $6 = $1E pour le niveau 0) AVANT l'ajustement du niveau a la jauge
# (JSR 0x4D1A60 : $83 ramene a 0 si $11E < $60) ; un CPU d'Arcade qui demande le niveau 4 avec une jauge de niveau 1
# part sur le chemin $10 avec l'anim $15 (niveau 0) qui ne repose jamais $34 -> sous-etat $14 sans fin (blocage du
# banc g67 07 A, Dan ZERO perdant au temps). Talon : apres le dernier JSR commun (0x514A70, site fichier 0x1750E8,
# lui/addiu/jalr), REFAIRE le test d'origine (memes mots que fichier 0x17503C-0x1750BC, sans le MOVE.B #$10) :
# ZERO et $83 = 0 -> $6 = $1E. Hors chemin ZERO ou niveau garde : rien.
DAN_SUPER = os.environ.get("DAN_SUPER", "0") == "1"
DS_SITE = 0x1750E8
DS_AVANT = (0x3c020051, 0x24424a70, 0x0040f809, 0x00000000)
def stub_dan_super():
    h = open(MODULE_SOURCE, 'rb').read()
    mots = lambda a, b: list(struct.unpack('<%dI' % ((b - a) // 4), h[a:b]))
    b1 = mots(0x17503C, 0x175064); b2 = mots(0x17507C, 0x1750A8); b3 = mots(0x1750B0, 0x1750C0)
    assert b1[2] == 0x804200d3 and b2[4] == 0x80420082 and b3[0] == 0x2403001e and b3[3] == 0xa0430007, (b1, b2, b3)
    w = [0x27bdfff0, 0xffbf0000, j_(3, 0x514A70), 0]
    w += b1; i1 = len(w); w += [0x10400000, 0]
    w += b2; i2 = len(w); w += [0x14400000, 0]
    w += b3
    fin = len(w)
    for i in (i1, i2): w[i] |= (fin - i - 1) & 0xffff
    return w + [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
def stub_garde_anim0(avant):
    w = [0x27bdfff0, 0xffbf0000]
    w += [0x3c037000, 0xac601158, 0x3c037000, 0x8c631118, 0x8c64001c, 0x3c037000, 0xac641150] + _RES   # TST.L $1C(A6)
    i0 = len(w); w += [0x10600000, 0]
    w += list(avant)
    w[i0] |= (len(w) - i0 - 1) & 0xffff
    return w + [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]

def stub_plans_vs():
    """(e28, D4_VERSUS) scene 4 hors Arcade, a chaque image (avant Hyper 0x96620) : VERSUS a decor D4 ($FE11) : combat
    (A5+8 >= 6, ou A5+8 = 4 et A5+C >= 4) -> bases du decor ($FE10 : Upper $4400/$440/$4A0, sinon Hyper) ; autres ecrans du
    VERSUS -> bases d'Hyper. Sans $FE11 (TRAINING...) : rien."""
    w = [0x27bdfff0, 0xffbf0000]
    w += _test_octet(FLAG_VS); i0 = len(w); w += [0x10600000, 0]                                  # beq -> Lf
    w += forme_cmpi_w(0x0008, 6) + [0x3c037000, 0x8c631158]; i1 = len(w); w += [0x04600000, 0]   # bltz C -> L1 (< 6)
    w += _bases_flag(PLANS_DECOR_U, PLANS_HYPER); j1 = len(w); w += [0x10000000, 0]
    L1 = len(w)
    w += forme_cmpi_w(0x0008, 4) + [0x3c037000, 0x8c631150]; i2 = len(w); w += [0x14600000, 0]   # bne -> Lh
    w += forme_cmpi_w(0x000C, 4) + [0x3c037000, 0x8c631158]; i3 = len(w); w += [0x04600000, 0]   # bltz C -> Lh
    w += _bases_flag(PLANS_DECOR_U, PLANS_HYPER); j2 = len(w); w += [0x10000000, 0]
    Lh = len(w); w += _bases(PLANS_HYPER)
    Lf = len(w); w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    for i, L in ((i0, Lf), (i1, L1), (j1, Lf), (i2, Lh), (i3, Lh), (j2, Lf)): w[i] |= (L - i - 1) & 0xffff
    return w
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
    W9, W5 = "@HA_MAME_RO9@/banques_hx", "@HA_MAME_RO5@/banques_hx"
    os.makedirs(dossier, exist_ok=True)
    for f in os.listdir(W9):
        if f != 'carte.txt' and not os.path.exists(os.path.join(dossier, f)): _lien(os.path.join(W9, f), os.path.join(dossier, f))
    va = {}; x = A['vbase']
    for n in sorted({a for g_, a in A['site'] + A['perso'] + A['fin'] if g_ and a}):
        d = open("@HA_ANIMS@/f%d.bin" % n, 'rb').read(); va[n] = x; x += (len(d) + 15) & ~15
    lignes = open(os.path.join(W9, 'carte.txt')).read().splitlines()
    sw = lambda v: ((v & 0xffff) << 16) | (v >> 16)
    for g_, a in A['site'] + A['perso'] + A['fin']:
        if g_ and a:
            lignes.append("anim %d %d" % (sw(va[a]), g_))
            src = os.path.join(W5, "f%d.bin" % g_); dst = os.path.join(dossier, "f%d.bin" % g_)
            if os.path.exists(src) and not os.path.exists(dst): _lien(src, dst)
    # (28/10) banque commune d'Upper (e351) : objets des ecrans d'Upper (CONTINUE, GAME OVER, fins), commutee par le banc
    # (BANC_COMMUN_UPPER=351) quand la base scroll1 du fork vaut 400
    src, dst = os.path.join(W5, "f351.bin"), os.path.join(dossier, "f351.bin")
    if os.path.exists(src) and not os.path.exists(dst): _lien(src, dst)
    # (e29) OBJETS_DECOR : les objets de decor d'Upper (reservoir $FFC000) sont dessines dans l'EMPLACEMENT 0 avec des codes
    # de la banque commune d'UPPER (e351 : $3Axx, $46xx, $5Bxx, $60xx-$61xx...), or le combat a la banque commune
    # d'Hyper (e545, $33F0 entrees : codes au-dela retires). OBJETS_E0=1 : f545.bin PROLONGEE par les entrees
    # $33F0-$6C5F de f351 (Hyper n'emet aucun code e0 dans cette plage : entrees jusqu'ici absentes) ; les $33F0
    # premieres entrees sont celles d'Hyper a l'octet. Donnee seulement, aucun changement du coeur.
    if OBJETS_DECOR and OBJETS_E0:
        h_ = open(os.path.join(W9, "f545.bin"), 'rb').read(); u_ = open(os.path.join(W5, "f351.bin"), 'rb').read()
        d_ = os.path.join(dossier, "f545.bin")
        if os.path.islink(d_): os.unlink(d_)
        open(d_, 'wb').write(_prolonge_e0(h_ + u_[len(h_):]))
        # (e46) DECOR_E0 : f351 de la construction prolongée de même (codes recodés valables aussi sous la banque d'Upper)
        if _DECOR_E0_TABLE:
            d_ = os.path.join(dossier, "f351.bin")
            if os.path.lexists(d_): os.unlink(d_)       # lien OU copie / lien dur (liens.lien sous Windows) : jamais écrire dedans
            open(d_, 'wb').write(_prolonge_e0(u_))
    # (e30) INDIC_UPPER : plan2.bin PROLONGEE jusqu'a $FFFF : codes $5B00 + c -> tuile $88000 + c (plans d'Upper, places
    # en $4000000 du banc / +$2000000 du zip) ; les $5B00 entrees d'Hyper inchangees (codes au-dela : absents jusqu'ici)
    if INDIC_UPPER:
        h_ = open(os.path.join(W9, "plan2.bin"), 'rb').read(); assert len(h_) == 4 * PLAN2_UPPER_DEBUT, len(h_)
        d_ = os.path.join(dossier, "plan2.bin")
        if os.path.islink(d_) or os.path.exists(d_): os.unlink(d_)
        open(d_, 'wb').write(h_ + struct.pack('<%dI' % (0x10000 - PLAN2_UPPER_DEBUT), *range(PLAN2_UPPER_BASE, PLAN2_UPPER_BASE + 0x10000 - PLAN2_UPPER_DEBUT)))
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
# (31/10, e23) CONT_S1_HYPER=1 (essai, defaut 0) : scene 6 avec la base scroll1 d'Hyper : fond propre, mais la base 0x400
# est aussi le signal de la banque commune d'Upper des objets (banc BANC_BASE_UPPER, coeur 0015 base_upper) -> barres
# « CONTINUE » illisibles. Remplace par CONT_S1_MASQUE.
CONT_S1_HYPER = os.environ.get("CONT_S1_HYPER", "0") == "1"
# (31/10, e23) CONT_S1_MASQUE=1 : scene 6 (citation du vaincu + CONTINUE) : scroll1 masque (bit 1 de $32(A5), registre de
# couches $804166 ; Hyper 0x313960 garde ces bits) a chaque image, retabli quand la scene est quittee. Les decors
# d'Hyper ont une partie de scroll1 (ciel du decor 4) en codes d'Hyper, dessinee avec la base d'Upper -> « taches » du
# fond grise. Les textes scroll1 d'Upper du CONTINUE etaient deja absents.
# (02/11, e26, coeur 0017 « bases marquees » : work/coeur_0017/POUR-LA-GREFFE.md) CONT_S1_MARQUE=1 : scenes 6 (citation +
# CONTINUE) et 8 (GAME OVER) avec scroll1 = $8300 : tuiles d'Hyper ($300 : ciel du decor 4) ET banque commune d'Upper
# (bit de marquage $8000, cle marque_upper=8000 du zip) ; remplace CONT_S1_MASQUE (plus de scroll1 masque). Exige les
# coeurs du 02/11 (patch 0017) ; avec un coeur plus ancien : barres CONTINUE cassees, sans plantage. Le banc MAME ne
# connait pas la marque (ciel faux en scene 6, logique inchangee).
CONT_S1_MARQUE = os.environ.get("CONT_S1_MARQUE", "1") == "1"
CONT_S1_MASQUE = os.environ.get("CONT_S1_MASQUE", "0" if CONT_S1_MARQUE else "1") == "1"
if CONT_S1_MARQUE and PLANS_S68: PLANS_S68 = (0x8300,) + PLANS_S68[1:]
PLANS_S6 = PLANS_HYPER if CONT_S1_HYPER else PLANS_S68
# (28/10) PLANS_GO=1 : GAME OVER (scene 8) avec les bases de plans d'Upper (lettres « GAME OVER » / « TRY AGAIN » de scroll2/3)
PLANS_GO = os.environ.get("PLANS_GO", "0") == "1"
PLANS = os.environ.get("HSFA_GREFFE_PLANS", "1") != "0"
# (etape 4) DECOR_FIN=1 : pendant la fin (scene A), $100 = $174, decor choisi par Upper (0x24F020 greffee : $14 pour le
# boss ; vs_decor ne borne que $100) : la fin d'Upper fait tourner le moteur de decor d'Upper sur $100
DECOR_FIN = os.environ.get("DECOR_FIN", "1") == "1"
DECOR_FIN_UNE = os.environ.get("DECOR_FIN_UNE", "1") == "1"   # (e33) voir stub_plans_scene ; =0 : comme e32
# (e34) FIN_ID_BASE=1 : a la 1re image de la fin (scene A, A5+8 = 0), $103 de J1 et J2 (id d'HYPER : $70 = Zangief ALPHA)
# <- $117 (perso de BASE = id d'Upper, $10). Les acteurs de fin au sous-type < $80 (ex. Zangief de la fin de Zangief,
# acteur $4B/$1C) prennent l'emplacement du joueur dont le perso est le leur (Hyper 0x2E81xx, homologue d'Upper 0x16C1xx :
# T_5B5BB0[$103 du joueur] compare a T_5B5BB0[$7F de l'acteur]) : en ALPHA / ZERO / ZERO 2, aucun joueur ne correspondait
# -> $1A = 0 (emplacement 0, banque commune : tuiles en vrac) ; et la banque de l'emplacement 2 (coeur et banc : perso de
# $FF8503) etait celle de la version d'Hyper. Avec l'id de base : emplacement 2 = banque ZERO 3 (= celle d'Upper, memes
# fichiers 355-386), comme dans Upper. Sans effet en ZERO 3 ($103 = $117). =0 : comme e33.
FIN_ID_BASE = os.environ.get("FIN_ID_BASE", "1") == "1" and DECOR_FIN_UNE
# (e35) FIN_ID_COPIES=1 (avec FIN_ID_BASE) : le changement de $103 n'est plus fait a la 1re image de la fin mais a la 1re
# image ou AUCUN acteur actif du reservoir $FFBC00-$FFBFFF (8 x $80) n'a $1A = $4000 ou $6000 (emplacements 2 / 3) : en
# scene 1 (gagnant au-dessus du boss), les acteurs $4B sous-type 0 en $FFBE80 / $FFBF00 sont des COPIES de J1 / J2
# (animations d'Hyper de la version) ; la banque de l'emplacement 2 suit $FF8503 = $103 de J1 -> avec $103 = $10 des la
# 1re image, banque ZERO 3 sous des images ALPHA (Zangief A/Z/Z2 en vrac au-dessus de Bison, e34e). L'acteur $1C du
# couloir n'apparait qu'apres (~+1200). =0 : comme e34 (1re image).
FIN_ID_COPIES = os.environ.get("FIN_ID_COPIES", "1") == "1"
FIN_RES = (0xFFBC00 - 0xFF8000, 8, 0x80)               # (e35) reservoir des acteurs de fin (deplacements A5)
FIN_PHASE = 0xFE04                                     # (e35) $FF7E04 : 0 = copies pas encore vues, 1 = vues (scene A)
def _pose_octet(d68, v): return [0x24030000 | v, 0x3c027000, 0x8c421114, 0xa0430000 | ((d68 ^ 1) & 0xffff)]
def _fin_id_copie():
    """(e35) a chaque image de la fin : 1re image (A5+8 = 0) -> phase $FE04 = 0 ; si un acteur actif du reservoir FIN_RES
    occupe l'emplacement 2 ou 3 ($1A = $4000 / $6000 : copies des joueurs, creees 3 images apres le debut) -> phase = 1 ;
    sinon, si la phase vaut 1 (copies disparues) -> $103 <- $117 (J1, J2)"""
    w = forme_cmpi_w(0x0008, 0) + [0x3c037000, 0x8c631150]; i_init = len(w); w += [0x14600000, 0]   # bne -> scan
    w += _pose_octet(FIN_PHASE, 0); j_init = len(w); w += [0x10000000, 0]                           # -> fin
    w[i_init] |= (len(w) - i_init - 1) & 0xffff
    vus = []
    d0, n, pas_ = FIN_RES
    for k in range(n):
        d = d0 + k * pas_
        w += _test_octet(d + 1); i0 = len(w); w += [0x10600000, 0]                   # inactif -> suivant
        for v in (0x4000, 0x6000):
            w += forme_cmpi_w(d + 0x1A, v) + [0x3c037000, 0x8c631150]; vus.append(len(w)); w += [0x10600000, 0]  # copie -> Lvu
        w[i0] |= (len(w) - i0 - 1) & 0xffff
    w += _test_octet(FIN_PHASE); i_ph = len(w); w += [0x10600000, 0]                 # phase 0 (pas encore vues) -> fin
    for k_ in (1, 2):
        d_ = 0x0103 + 0x400 * k_
        w += [0x3c027000, 0x8c421114, 0x80430000 | (((d_ + 0x14) ^ 1) & 0xffff), 0xa0430000 | ((d_ ^ 1) & 0xffff)]
    j_sw = len(w); w += [0x10000000, 0]                                               # -> fin
    Lvu = len(w); w += _pose_octet(FIN_PHASE, 1)
    Lf = len(w)
    for i_ in vus: w[i_] |= (Lvu - i_ - 1) & 0xffff
    for i_ in (j_init, i_ph, j_sw): w[i_] |= (Lf - i_ - 1) & 0xffff
    return w
FOND_ARCADE = os.environ.get("FOND_ARCADE", "1") == "1"   # (etape 4) planisphere d'Upper a l'init du match
def _bases(b):
    w = []
    for k, v in enumerate(b): w += [0x24030000 | v, 0x3c0200c0, 0xa4430000 | ((-0x100 + 2 * k) & 0xffff)]   # sh v1,$BFFF00+2k
    return w
def _bases_flag(bases_u, bases_h):
    """(e26) drapeau « decor d'Upper » ($FE10) -> bases bases_u, sinon bases_h (branchements relatifs internes)"""
    if not DECORS_UPPER: return _bases(bases_h)
    w = _test_octet(FLAG_DECOR); i = len(w); w += [0x10600000, 0]
    w += _bases(bases_u); j = len(w); w += [0x10000000, 0]
    L = len(w); w += _bases(bases_h)
    w[i] |= (L - i - 1) & 0xffff; w[j] |= (len(w) - j - 1) & 0xffff
    return w
def stub_plans_vict(cible):
    """(e30) ecran de victoire : bases PLANS_VICT_U (decor d'Upper, drapeau $FE10) ou PLANS_VICT_H, puis JSR cible"""
    w = [0x27bdfff0, 0xffbf0000] + _bases_flag(PLANS_VICT_U, PLANS_VICT_H) + [j_(3, cible), 0x00000000]
    return w + [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
# (e33) TUILES_E1=1 : dessin d'Hyper 0x395930 (commande d'image « emplacement 1 », homologue d'Upper 0x140EE0) : code
# de tuile + $1000 (banque commune d'Hyper) au lieu de + $1C00 (Upper) ; dans les ecrans d'Upper (Arcade $FE00, scenes
# 6/8/A : CONTINUE, GAME OVER, fins) -> + $7700 = code d'Upper + $5B00 (plan2.bin prolongee : tuiles d'Upper, comme
# INDIC_UPPER). GAME OVER apres le boss final : panneaux e1 $3488 (blocs blancs) au lieu de $4088 d'Upper.
TUILES_E1 = os.environ.get("TUILES_E1", "1") == "1"
H_E1_SITE = 0x395EE0
H_E1_AVANT = (0x3c037000, 0x8c641128, 0x3c031000, 0x00832021, 0x3c037000, 0xac641128)
# (e34) TUILES_E1_FORME=1 (defaut) : le talon d'e33 testait A5+4 par lh / addiu / beq, forme que le traducteur ne reconnait
# pas : traduit en « TST.B $FE00(A5) ; BEQ ; ... ; ADDI.L #$77000000,D1 » -> +$7700 PARTOUT (selection comprise : portraits
# d'Evil Ryu, Dee Jay, Guile, Fei-Long, Juni, Balrog, T. Hawk en vrac dans ro9a25, retour du 02/11). Ici : formes du
# recompilateur (TST.B $FE00 par _test_octet, CMPI.W #k,$4(A5) par forme_cmpi_w) et deux copies de la sequence d'origine
# (+$1000 / +$7700). =0 : talon d'e33.
TUILES_E1_FORME = os.environ.get("TUILES_E1_FORME", "1") == "1"
def stub_tuile_e1_forme():
    w = [0x27bdfff0, 0xffbf0000] + _test_octet(FLAG); br_h = len(w); w += [0x10600000, 0]   # $FE00 = 0 -> Lh
    br_u = []
    for k_ in (6, 8, 0xA):
        w += forme_cmpi_w(0x0004, k_) + [0x3c037000, 0x8c631150]; br_u.append(len(w)); w += [0x10600000, 0]   # egal -> Lu
    Lh = len(w); w += list(H_E1_AVANT); jf = len(w); w += [0x10000000, 0]
    Lu = len(w); w += [x if x != 0x3c031000 else 0x3c037700 for x in H_E1_AVANT]
    Lf = len(w); w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    w[br_h] |= (Lh - br_h - 1) & 0xffff
    for i_ in br_u: w[i_] |= (Lu - i_ - 1) & 0xffff
    w[jf] |= (Lf - jf - 1) & 0xffff
    return w
def stub_tuile_e1():
    """a0 = D(0x1128) + ($7700 << 16) si $FE00 et A5+4 dans {6, 8, A}, sinon + ($1000 << 16) ; laisse v1 = $70000000
    (comme le code remplace) ; n'utilise que v1 et a0"""
    if TUILES_E1_FORME: return stub_tuile_e1_forme()
    w = [0x27bdfff0, 0xffbf0000, 0x3c037000, 0x8c631114, 0x80640000 | ((FLAG ^ 1) & 0xffff)]
    i0 = len(w); w += [0x10800000, 0]                                  # beq a0,zero -> Lh
    w += [0x84640004]                                                  # lh a0,4(v1) : A5+4
    bu = []
    for k_ in (6, 2, 2):
        w += [0x2484ffff & (0xffff0000 | (-k_ & 0xffff))]              # addiu a0,a0,-k
        bu.append(len(w)); w += [0x10800000, 0]                        # beq a0,zero -> Lu
    Lh = len(w); w += [0x3c031000]; jc = len(w); w += [0x10000000, 0]  # lui v1,$1000 ; b Lc
    Lu = len(w); w += [0x3c037700]                                     # lui v1,$7700
    Lc = len(w); w += [0x3c047000, 0x8c841128, 0x00832021, 0x3c037000, 0xac641128]
    w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    w[i0] |= (Lh - i0 - 1) & 0xffff
    for i_ in bu: w[i_] |= (Lu - i_ - 1) & 0xffff
    w[jc] |= (Lc - jc - 1) & 0xffff
    return w
def stub_plans(bases, cible):
    """bases des plans puis JSR cible (adresse d'EXECUTION ; 0 = sans appel)"""
    w = [0x27bdfff0, 0xffbf0000] + (_bases(bases) if PLANS else []) + ([j_(3, cible), 0x00000000] if cible else [])
    return w + [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
DECOR_SAUVE = 0xFF02                                   # (etape 4) mot $FF02(A5) = $FF7F02 : decor demande par Upper
def _copie_mot(src, dst):
    """MOVE.W src(A5),dst(A5) (deplacements 68K de MOTS = PS2)"""
    return [0x3c027000, 0x8c421114, 0x84430000 | (src & 0xffff), 0xa4430000 | (dst & 0xffff)]
# (e46, ro9a36 : « glitch rapide » quand on accepte le CONTINUE avec Start) CONT_SORTIE=1 : a la sortie de la scene 6 vers
# A5+4 = 0 (continue accepte), le talon pose les bases d'HYPER alors que la VRAM garde le decor du combat (decor d'Upper,
# codes d'Upper) jusqu'a ce que la selection d'Hyper la redessine : 2 images de decor en tuiles fausses (coeur et MAME).
# Upper montre 3 images du decor grise (bases inchangees) puis du noir. Ici : scroll1-3 masques (ANDI.W #$FFF1,$32(A5)) a
# la sortie ; la selection d'Hyper reecrit $32 entier ($1B00 a l'init, $1B0E ensuite). =0 : comme ro9a35b.
CONT_SORTIE = os.environ.get("CONT_SORTIE", "0") == "1"
H_SCENE2 = 0x286590 - 0x1F0000                     # (e46) scene 2 d'Hyper (exec 0x286590, table 0x5B5E84)
# (ro9a38, revue de la greffe A2a) A2A_VS=1 : hors ARCADE (VERSUS), le talon scene2_bases pose AUSSI les bases d'Hyper :
# apres un VERSUS sur un decor d'Upper (talon plans_vs : $4400/$440/$4A0), les bases restaient celles du decor pendant
# l'ecran de resultat ET toute la selection suivante (fond en tuiles fausses, essais 06/06b) jusqu'au match suivant.
# Pose a chaque image de la scene 2 (valeurs d'Hyper : sans effet quand elles sont deja posees). =0 : comme ro9a37.
A2A_VS = os.environ.get("A2A_VS", "0") == "1"
# (ro9a38, revue de la greffe E2b) E2B_DEFI=1 : nouveau challenger accepte pendant la carte, le face-a-face ou un combat de
# l'Arcade : la copie d'Upper u1353A0 (sous-etat 2 de la tache u1346A0) passe a la selection d'Hyper sans masque ; le talon
# scene2_bases posait les bases d'Hyper sur la VRAM d'Upper -> 2 a 3 images de paves plein ecran (+ 2 aux couleurs du decor
# depuis un combat). Ici (forme masque_sortie d'e46) : talon defi_sortie a l'appel JSR u1354E0 du chemin de sortie (Upper
# 0x1353EC) : appel d'origine, puis scroll1-3 masques ($32(A5) et registre des couches $804166) et compteur DEFI_CPT =
# E2B_IMAGES ; scene2_bases : tant que le compteur n'est pas nul, bases du decor GARDEES et couches masquees (compteur - 1) ;
# a 0 : bases d'Hyper + ORI.W #$E,$32(A5) (et $804166). =0 : comme ro9a37.
E2B_DEFI = os.environ.get("E2B_DEFI", "0") == "1"
# (ro9a38, revue de la greffe X2, sorties/2e_passe_axe3.md ; decision de l'utilisateur du 12/11 : AGRANDIR, pas de
# renumerotation) X2_TABLES=1 : les tables par perso lues par les copies d'Upper (index $116 = perso de base, ou $7F(A6))
# ont 40 entrees ($00-$27) ; un id de base $28-$2F (MAX) lisait la table suivante (erreur d'adresse $A08 a la carte /
# au face-a-face : essai 05c). Chaque table est recopiee a la fin du bloc de donnees de la greffe (fenetre PS2
# $F18000-$FE0000 = 68K $410000-$4D8000, avant la table D4) avec X2_N entrees ; la constante lui/addiu de chaque lecteur
# copie est redirigee (les lecteurs d'Hyper gardent l'original). Pointeurs de code recopies : ajoutes a greffe_ptrs.
# (ro9a39, L1 des MAX, work/l1_max_greffe/CONCEPTION.md) X2 v2 : liste lue dans x2_tables.tsv (54 tables, lots A-D,
# colonnes de X2_L1.tsv) ; remplissage de chaque rangee par x2_entree (entrees 40-44 = octets qui suivent la table :
# pseudo-ids d'Upper inchanges ; 45 / 46 = entree 0 ou valeur MAX de X2_VALEURS ; 47 = entree 39) ; genres simple, dec
# (+ ':ptr' : pointeurs de DONNEES de T_614E00 rediriges), rangs (R rangees de 48), banque, 967bf0, lignes32 (lot D :
# lignes $20-$2F = lignes 0-15, masque ANDI #$1F -> #$3F) ; constantes de rangee (addiu / imm / dep / sll / andi, une
# seule instruction de la forme attendue a +-$10 du site) ; constantes interieures ]T, T + taille[ redirigees si
# d < e (ou debut de rangee), sinon arret. =0 : comme ro9a38.
X2_TABLES = os.environ.get("X2_TABLES", "0") == "1"
X2_N0, X2_N = 0x28, 0x30
X2_BUDGET = int(os.environ.get("X2_BUDGET", "1C000"), 16)   # (L1, decision D6 revue le 12/11 : lot A mesure 78 Ko) 112 Ko au plus pour X2, le reste aux decors
X2_SAUF = {int(x, 16) for x in os.environ.get("X2_SAUF", "").split(',') if x}   # (essais) tables laissees telles quelles
X2_VALEURS = [int(x, 16) for x in os.environ.get("X2_VALEURS", "").split(',') if x]   # (L1, D1 : vide) ids 26 27 2d 2e
assert X2_TABLES or not X2_VALEURS, "X2_VALEURS sans X2_TABLES"
assert all(v_ in (0x26, 0x27, 0x2D, 0x2E) for v_ in X2_VALEURS), X2_VALEURS

def x2_liste():
    """lignes de x2_tables.tsv (en-tete : lot upper table_ro9a37 cote genre e n0 rangs lecteurs_a_rediriger sites_temoins
    constantes valeurs v26 v27 v2D v2E ryu role note) -> dicts ; X2_SAUF (adresse d'Upper ou de la table) retire une
    table ; le lot D (lignes32) est indivisible"""
    L_ = open(os.path.join(G, 'etape3', 'x2_tables.tsv'), encoding='utf-8').read().splitlines()
    k_ = L_[0].split('\t'); out_ = []
    for l_ in L_[1:]:
        if not l_.strip(): continue
        d_ = dict(zip(k_, l_.split('\t') + [''] * (len(k_) - len(l_.split('\t')))))
        d_['u'] = int(d_['upper'], 16); d_['hyp'] = d_['cote'].startswith('HYPER')
        d_['adr'] = int(d_['table_ro9a37'][2:], 16) if d_['hyp'] else d_['u']
        d_['e'] = int(d_['e']); d_['n0'] = int(d_['n0']); d_['R'] = int(d_['rangs'])
        d_['sites'] = [int(s_, 16) for s_ in d_['sites_temoins'].split()]
        lr_ = d_['lecteurs_a_rediriger']; d_['tous'] = not lr_.startswith('listes:')
        if not d_['tous']: d_['sites'] = [int(s_, 16) for s_ in lr_[7:].split(',')]
        d_['consts'] = [tuple([c_.split(':')[0]] + [int(v_, 16) for v_ in c_.split(':')[1:]])
                        for c_ in d_['constantes'].split() if ':' in c_ and not c_.startswith('garde:')]
        # garde:ADR : constante interieure gardee (ses lecteurs lisent l'original, inchange : neutre en L1)
        d_['gardes'] = {int(c_[6:], 16) for c_ in d_['constantes'].split() if c_.startswith('garde:')}
        out_.append(d_)
    sauf_ = [d_ for d_ in out_ if d_['u'] in X2_SAUF or d_['adr'] in X2_SAUF]
    lotd_ = [d_ for d_ in out_ if d_['genre'] == 'lignes32']
    assert not any(d_ in sauf_ for d_ in lotd_) or all(d_ in sauf_ for d_ in lotd_), "X2_SAUF : lot D indivisible"
    return [d_ for d_ in out_ if d_ not in sauf_]

def x2_entree(lit, e, i, val=None):
    """entree i (0-47) d'une rangee prolongee ; lit(k, n) : octets a partir de la base de la rangee ; val : octets MAX"""
    if i < 45: b = lit(e * i, e)
    elif i < 47: b = val if val is not None else lit(0, e)
    else: b = lit(e * 39, e)
    assert len(b) == e, (e, i)
    return bytes(b)

def x2_src(e, i):
    """decalage source (dans la rangee) de l'entree i, sans valeur MAX"""
    return e * i if i < 45 else (0 if i < 47 else e * 39)
DEFI_CPT = 0xFE0A                                     # $FF7E0A : compteur de la sortie de defi (zone fixe de la greffe, D2)
DEFI_N = int(os.environ.get("E2B_IMAGES", "6"))
U_DEFI_JSR, U_DEFI_CIBLE = 0x1353EC, 0x1354E0         # Upper : JSR du chemin « challenger accepte » de u1353A0 et sa cible
_MASQUE_COUCHES = [0x3c027000, 0x8c421114, 0x94430032, 0x3063fff1, 0xa4430032,      # ANDI.W #$FFF1,$32(A5)
                   0x3c027000, 0x8c421114, 0x84440032, 0x3c0200be, 0xa4442146]      # MOVE.W $32(A5),$804166 (forme d'Hyper)
_DEMASQUE_COUCHES = [0x3c027000, 0x8c421114, 0x94430032, 0x3463000e, 0xa4430032,    # ORI.W #$E,$32(A5)
                     0x3c027000, 0x8c421114, 0x84440032, 0x3c0200be, 0xa4442146]
def stub_defi_sortie(cible):
    """(ro9a38, E2B_DEFI) a la place du JSR u1354E0 de la sortie « challenger accepte » : JSR cible, couches masquees,
    compteur DEFI_CPT = DEFI_N"""
    return [0x27bdfff0, 0xffbf0000, j_(3, cible), 0x00000000] + _MASQUE_COUCHES + _pose_octet(DEFI_CPT, DEFI_N) + \
           [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
def stub_scene2_bases(cible):
    """(e46, CONT_SORTIE) scene A5+4 = 2 (selection d'Hyper) : en partie ARCADE (drapeau FLAG), bases de plans d'Hyper
    puis JSR cible (scene 2 d'Hyper) ; hors ARCADE (VERSUS...) : JSR cible seul (A2A_VS=1 : bases d'Hyper aussi) ;
    E2B_DEFI=1 : sortie de defi en cours (DEFI_CPT) -> attente masquee, puis bases d'Hyper et couches demasquees"""
    w = [0x27bdfff0, 0xffbf0000]; br = []
    if E2B_DEFI:
        w += _test_octet(DEFI_CPT); i0 = len(w); w += [0x10600000, 0]                        # beq (pas de defi) -> Ln
        w += [0x3c027000, 0x8c421114, 0x80430000 | ((DEFI_CPT ^ 1) & 0xffff), 0x2463ffff,
              0xa0430000 | ((DEFI_CPT ^ 1) & 0xffff)]                                           # SUBQ.B #1,DEFI_CPT(A5)
        w += _test_octet(DEFI_CPT); i1 = len(w); w += [0x10600000, 0]                        # beq (fini) -> Ld
        w += _MASQUE_COUCHES; j0 = len(w); w += [0x10000000, 0]                                 # attente : -> L
        Ld = len(w); w += _bases(PLANS_HYPER) + _DEMASQUE_COUCHES; j1 = len(w); w += [0x10000000, 0]   # -> L
        Ln = len(w); br += [(i0, Ln), (i1, Ld)]
    if not A2A_VS: w += _test_octet(FLAG); i = len(w); w += [0x10600000, 0]                 # beq (pas ARCADE) -> L
    w += _bases(PLANS_HYPER)
    L = len(w); w += [j_(3, cible), 0x00000000, 0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    if not A2A_VS: w[i] |= (L - i - 1) & 0xffff
    if E2B_DEFI: br += [(j0, L), (j1, L)]
    for k_, L_ in br: w[k_] |= (L_ - k_ - 1) & 0xffff
    return w
# (couleur du CPU, 12/11) une version ZERO / ZERO 2 / ALPHA / EX (CPU tire ou J1) changeait de couleur au FIGHT. Deux
# defauts : D1 = au face-a-face (Hyper 0x9A4E0) et a chaque reprise de manche (0x9FFEC), le talon moteur_pal appelle sur un
# decor d'Upper la copie d'Upper 0x4B270 (chargeur 0x4B5A0 : palettes ZERO 3 par $117 = perso de BASE), puis au FIGHT
# Hyper appelle son dispatcher 0x60A90 (fichier 0x9C428 ; chargeur 0x60D50 : palettes par $103 = VERSION) ; D2 = sur la
# carte, la copie d'Upper 0x262930 pose la couleur du CPU par la regle d'Upper $129 = ($133 + 1) x 2 (= 2 apres le tirage,
# $133 = 0) : 3e couleur de la version chez Hyper.
# PAL_VERSION=1 (D1) : talon moteur_pal, chemin « decor d'Upper » (Arcade, VERSUS D4) = copie d'Upper 0x4B270 PUIS
# dispatcher d'Hyper 0x60A90 (l'appel d'Hyper au FIGHT, chargeur 0x60D50 par $103) : palette de la version du face-a-face
# a la fin, reprises comprises (sans effet en ZERO 3 : $103 = $117). Au 1er ecran du face-a-face le 2e chargement finit
# apres l'image (1 image de palette ZERO 3 dans les emplacements 5-9) : invisible, l'ecran VS n'affiche pas les sprites des
# joueurs (captures MAME identiques a celles d'une variante sans cette image). Variantes essayees : chargeur d'un joueur
# route vers Hyper (meme resultat, plus de code) ; entree 0 de la sous-table de combat (la reprise rechargeait apres).
# =0 : comme ro9a39.
PAL_VERSION = os.environ.get("PAL_VERSION", "0") == "1"
H_PAL_JOUEURS = 0x60A90                               # dispatcher des palettes des joueurs d'Hyper (par $138 ; chargeur 0x60D50)
# COUL_CPU_VERSION=1 (D2) : les deux JSR de la copie 0x262930 qui suivent la pose de la couleur du CPU ($129 ; J1 CPU :
# Upper 0x262D18, J2 CPU : 0x262E10 ; cible = homologue d'Hyper de 0x263820) -> talons coul_cpu_1 / coul_cpu_2 : appel
# d'origine, puis si le CPU n'est pas dans sa version de base ($103 != $117) : $129 = 0 (couleur par defaut de la version),
# sauf miroir exact (meme $103 que l'autre joueur, dont le $129 vaut 0) : $129 = COUL_CPU_MIROIR (1 ; decision de
# l'utilisateur du 12/11 : equivalent de la regle d'Upper). CPU en version de base (ZERO 3) : regle d'Upper gardee.
# =0 : comme ro9a39.
COUL_CPU_VERSION = os.environ.get("COUL_CPU_VERSION", "0") == "1"
COUL_MIROIR = int(os.environ.get("COUL_CPU_MIROIR", "1"), 16)
COUL_TMP = 0xFE24                                     # $FF7E24 (mot) : temporaire des comparaisons (re/allocations.tsv)
U_COUL_SITES = ((0x262D18, 0x400, 0x800), (0x262E10, 0x800, 0x400))   # (JSR de la copie, CPU, autre joueur : depl. de A5)
COUL_JAL = 2                                          # indice du JSR d'origine dans le talon (pose apres la construction du module)
def _cmp_octets_a5(a, b):
    """octets a(A5) et b(A5) compares (sans signe) : MOVEQ #0,D0 ; MOVE.B b(A5),D0 ; MOVE.W D0,COUL_TMP(A5) ; MOVEQ #0,D0 ;
    MOVE.B a(A5),D0 ; CMP.W COUL_TMP(A5),D0 (forme_cmp_14c, deplacement change) -> RES (0 = egaux) ; D0 change"""
    f = forme_cmp_14c(); f[2] = 0x84630000 | (COUL_TMP & 0xffff)
    return _d0_de_a5(b) + [0x3c037000, 0x84641124, 0x3c037000, 0x8c631114, 0xa4640000 | (COUL_TMP & 0xffff)] + \
           _d0_de_a5(a) + f + _RES
_EMPILE_D0 = [0x3c027000, 0x8c441124, 0x3c027000, 0x8c42114c, 0x2443fffc, 0x3c027000, 0xac43114c, 0xac640000]   # MOVE.L D0,-(SP)
_DEPILE_D0 = [0x3c037000, 0x8c65114c, 0x24a40004, 0x3c037000, 0xac64114c, 0x8ca40000, 0x3c037000, 0xac641124]   # MOVE.L (SP)+,D0
def stub_coul_cpu(cpu, autre):
    """(COUL_CPU_VERSION) a la place du JSR qui suit la pose de la couleur du CPU : JSR d'origine (mot COUL_JAL, pose apres
    la construction du module), puis couleur du CPU (structure cpu(A5)) selon sa version ; D0 garde"""
    w = [0x27bdff40, 0xffbf00b8, j_(3, 0), 0x00000000] + _EMPILE_D0
    w += _cmp_octets_a5(cpu + 0x103, cpu + 0x117); i_b = len(w); w += [0x10600000, 0]    # version de base -> Lf (Upper)
    w += _cmp_octets_a5(cpu + 0x103, autre + 0x103); i_d = len(w); w += [0x14600000, 0]  # autre perso / version -> L0
    w += _test_octet(autre + 0x129); i_c = len(w); w += [0x14600000, 0]                  # autre couleur -> L0
    w += _pose_octet(cpu + 0x129, COUL_MIROIR); j = len(w); w += [0x10000000, 0]         # miroir exact -> Lf
    L0 = len(w); w += _pose_octet(cpu + 0x129, 0)
    Lf = len(w); w += _DEPILE_D0 + [0xdfbf00b8, 0x27bd00c0, 0x03e00008, 0x00000000]
    for i_, L_ in ((i_b, Lf), (i_d, L0), (i_c, L0), (j, Lf)): w[i_] |= (L_ - i_ - 1) & 0xffff
    assert w[COUL_JAL] == j_(3, 0)
    return w
# (couleur des portraits, 13/11) PORT_VERSION=1 (F3) : les portraits de la carte, du face-a-face de la carte et de l'ecran de
# victoire sont colores par deux copies d'Upper : 0x25D730 (table T_7251a0, perso de base en D0, couleur en D2 = $129(A4))
# et 0x196A30 (T_72BDF0 + $129(A4) x $100) : palette ZERO 3 d'Upper a la couleur $129, alors que le sprite d'une version
# prend la couleur $129 de la table d'Hyper (Dan ZERO couleur 0 : portrait orange, sprite rose). Hyper colore ses portraits
# avec la MEME table (copie d'Hyper de T_7251a0, image $15D3A0) a la couleur 2 imposee (MOVE.B #$2,D1, Hyper 0x31FA24),
# quelle que soit la couleur choisie : la couleur 0 d'une version y est celle de la couleur 2 d'Upper (palette de corps
# identique a 14 mots sur 15 pour presque toutes les versions, outils carte_coul.py). Ici, pour un joueur dans une version
# ($103 != $117 de A4) : couleur 2, comme Hyper ; version de base (ZERO 3) : couleur $129 (regle d'Upper). Appels lui/addiu
# de 0x25D730 avec A4 = joueur (Upper 0x18001C carte / face-a-face, 0x184640, 0x19D548 carte) -> talon port_carte (D2 = 2) ;
# JSR 0x196A30 (Upper 0x1967CC, ecran de victoire) -> talon port_vict ($129(A4) = 2 pendant l'appel, puis remis). =0 :
# comme ro9a39.
PORT_VERSION = os.environ.get("PORT_VERSION", "0") == "1"
PORT_COUL = 2                                         # couleur des portraits d'une version (Hyper 0x31FA24 : MOVE.B #$2,D1)
U_PORT_CARTE, U_PORT_CARTE_SITES = 0x25D730, (0x18001C, 0x184640, 0x19D548)
U_PORT_VICT, U_PORT_VICT_SITE = 0x196A30, 0x1967CC
PORT_SAUVE = 0xFE26                                   # $FF7E26 : $129 du joueur sauve pendant le chargeur de victoire
def _version_a4():
    """MOVEQ #0,D7 ; MOVE.B $117(A4),D7 ; MOVE.W D7,COUL_TMP(A5) ; MOVEQ #0,D7 ; MOVE.B $103(A4),D7 ; CMP.W COUL_TMP(A5),D7
    (RES : 0 = version de base). D7 (domicile 0x1140) : les deux chargeurs le posent eux-memes (nombre de palettes) ; pas
    de pile entre la comparaison et le branchement (le traducteur emet la comparaison au branchement : essai x1)"""
    f = forme_cmp_14c(); f[2] = 0x84630000 | (COUL_TMP & 0xffff); f[6] = 0x84631140
    assert forme_cmp_14c()[6] == 0x84631124
    d7 = lambda off: [0x3c037000, 0xac601140, 0x3c037000, 0x8c631110, 0x80640000 | off, 0x3c037000, 0xa0641140]
    return d7(0x116) + [0x3c037000, 0x84641140, 0x3c037000, 0x8c631114, 0xa4640000 | (COUL_TMP & 0xffff)] + \
           d7(0x102) + f + _RES
def stub_port_carte(cible):
    """(PORT_VERSION) a la place de l'appel de la copie de 0x25D730 : version (A4) -> MOVEQ #2,D2 (forme d'Upper 0x1EF748) ;
    JSR cible"""
    w = [0x27bdff40, 0xffbf00b8] + _version_a4(); i_ = len(w); w += [0x10600000, 0]       # version de base -> L
    w += [0x24030000 | PORT_COUL, 0x3c027000, 0xac43112c]                                 # MOVEQ #2,D2
    L = len(w); w += [j_(3, cible), 0x00000000, 0xdfbf00b8, 0x27bd00c0, 0x03e00008, 0x00000000]
    w[i_] |= (L - i_ - 1) & 0xffff
    return w
def stub_port_vict(cible):
    """(PORT_VERSION) a la place du JSR de la copie de 0x196A30 : $129(A4) sauve ; version (A4) -> $129(A4) = 2 ; JSR cible ;
    $129(A4) remis"""
    w = [0x27bdff40, 0xffbf00b8, 0x3c027000, 0x8c421110, 0x80430128, 0x3c027000, 0x8c421114,
         0xa0430000 | ((PORT_SAUVE ^ 1) & 0xffff)]                                         # MOVE.B $129(A4),$FE26(A5)
    w += _version_a4(); i_ = len(w); w += [0x10600000, 0]                                  # version de base -> L
    w += [0x24030000 | PORT_COUL, 0x3c027000, 0x8c421110, 0xa0430128]                     # MOVE.B #2,$129(A4)
    L = len(w); w += [j_(3, cible), 0x00000000]
    w += [0x3c027000, 0x8c421114, 0x80430000 | ((PORT_SAUVE ^ 1) & 0xffff), 0x3c027000, 0x8c421110, 0xa0430128]   # remis
    w += [0xdfbf00b8, 0x27bd00c0, 0x03e00008, 0x00000000]
    w[i_] |= (L - i_ - 1) & 0xffff
    return w
def stub_plans_scene(cible, restaure=False, bases=None, efface=(), masque_s1=False, masque_sortie=False):
    """scenes 6/8/A d'Upper (CONTINUE, GAME OVER, fin) : plans d'Upper, JSR cible, puis si la scene est quittee vers
    A5+4 = 0 (continue accepte -> selection d'Hyper) ou $C (sortie -> titre d'Hyper) : plans d'Hyper. Aucun talon sur
    les scenes 0 et C d'Hyper : le VERSUS garde exactement son minutage."""
    w = [0x27bdfff0, 0xffbf0000] + (_bases_flag(PLANS_UPPER, bases) if bases else _bases(PLANS_UPPER)) + (_copie_mot(0x174, 0x100) if restaure and not DECOR_FIN_UNE else [])
    # (e33) DECOR_FIN_UNE=1 : $100 = $174 seulement a la 1re image de la scene (A5+8 = 0) : la fin d'Upper change elle-meme
    # $100 (fin de Zangief : $14 -> $20 au generique) ; recopie a chaque image -> $100 revenait a $14 8 images apres la
    # creation des objets du decor $20 -> classes de decor sur la table du decor $14 (plantages 10 x3 pc $95B24/$A1DA2, 15 Z3)
    if restaure and DECOR_FIN_UNE:
        w += forme_cmpi_w(0x0008, 0) + [0x3c037000, 0x8c631150]; ir = len(w); w += [0x14600000, 0]   # bne RES -> suite
        w += _copie_mot(0x174, 0x100)
        if FIN_ID_BASE and not FIN_ID_COPIES:             # (e34) voir FIN_ID_BASE
            for k_ in (1, 2):
                d_ = 0x0103 + 0x400 * k_
                w += [0x3c027000, 0x8c421114, 0x80430000 | (((d_ + 0x14) ^ 1) & 0xffff), 0xa0430000 | ((d_ ^ 1) & 0xffff)]
        w[ir] |= (len(w) - ir - 1) & 0xffff
        if FIN_ID_BASE and FIN_ID_COPIES: w += _fin_id_copie()   # (e35) a chaque image de la fin
    # (etape 6) EFFACE_FIN=1 : 1re image de la fin (A5+8 = 0) : pages scroll2/scroll3 effacees comme a la selection
    # d'Upper (le decor du boss d'Upper n'est pas en VRAM : le dernier combat etait sur un decor d'Hyper)
    if efface:
        w += forme_cmpi_w(0x0008, 0) + [0x3c037000, 0x8c631150]; ie = len(w); w += [0x14600000, 0]   # bne RES -> suite
        for e_ in efface: w += [j_(3, e_), 0x00000000]
        w[ie] |= (len(w) - ie - 1) & 0xffff
    if masque_s1: w += [0x3c027000, 0x8c421114, 0x94430032, 0x3063fffd, 0xa4430032]   # ANDI.W #$FFFD,$32(A5)
    w += [j_(3, cible), 0x00000000]
    if masque_s1:                                                                    # scene quittee : ORI.W #2,$32(A5)
        w += forme_cmpi_w(0x0004, 6) + [0x3c037000, 0x8c631150]; im = len(w); w += [0x10600000, 0]   # beq (encore 6) -> suite
        w += [0x3c027000, 0x8c421114, 0x94430032, 0x34630002, 0xa4430032]
        w[im] |= (len(w) - im - 1) & 0xffff
    w += forme_cmpi_w(0x0004, 0) + [0x3c037000, 0x8c631150]; i1 = len(w); w += [0x10600000, 0]   # beq RES -> Lh
    w += forme_cmpi_w(0x0004, 0xC) + [0x3c037000, 0x8c631150]; i2 = len(w); w += [0x10600000, 0]   # beq RES -> Lc
    j1 = len(w); w += [0x10000000, 0]                                                              # -> fin
    Lc = len(w); w += (_pose_flag(0) if MODE_FLAG else [])                                         # sortie : fin de partie
    jc = None
    if masque_sortie:
        # (e46) sortie vers $C : bases d'Hyper (comme avant) ; sortie vers 0 (continue accepte) : bases du DECOR GARDEES
        # (la VRAM garde le decor : l'image suivante le montre juste, comme Upper), scroll1-3 masques dans $32(A5) ET dans
        # le registre des couches $804166 (forme d'Hyper 0x0A6C9C-0x0A6CAC : le coeur FBNeo prend les registres CPS-B au
        # debut de l'image, les bases du fork a l'affichage) ; les bases d'Hyper sont posees par le talon scene2_bases a
        # la 1re image de la selection (A5+4 = 2), quand le masque est deja pris par le coeur
        w += _bases(PLANS_HYPER); jc = len(w); w += [0x10000000, 0]
        Lh = len(w)
        w += [0x3c027000, 0x8c421114, 0x94430032, 0x3063fff1, 0xa4430032,
              0x3c027000, 0x8c421114, 0x84440032, 0x3c0200be, 0xa4442146]
    else:
        Lh = len(w); w += _bases(PLANS_HYPER)
    Lf = len(w); w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    if jc is not None: w[jc] |= (Lf - jc - 1) & 0xffff
    for i, L in ((i1, Lh), (i2, Lc), (j1, Lf)): w[i] |= (L - i - 1) & 0xffff
    return w

# (31/10, retour 3 de l'utilisateur : portraits de l'intermede entiers, sur le decor, restes pendant la 1re manche)
TYPE14 = os.environ.get("TYPE14", "1") == "1"
RESULTAT_CPU = os.environ.get("RESULTAT_CPU", "1") == "1"   # (31/10) voir stub_plans_auto   # (31/10) voir le patch de T_5C5720[14]
INTERMEDE_PLANS = os.environ.get("INTERMEDE_PLANS", "0") == "1"   # essai du 31/10 : sans effet utile (portraits toujours entiers, decor du combat casse) -> 0
# (e40) FLASH_SEL=1 : voir stub_plans_auto (scroll1-3 masques a l'init de la scene 4) ; =0 : comme ro9a30
FLASH_SEL = os.environ.get("FLASH_SEL", "0") == "1"
# (e40) EFFET_12A=1 (retour 3 du 07/11 : fond du K.O. par super des versions ALPHA / ZERO 2 coupe a droite) : la copie
# d'Upper 0x157318 (moteur de plans, appelee par 0x151B80 sur un decor d'Upper) pose $2A/$2C(A5) depuis la table
# T_614aa0[$12A] (homologue partagee : T_5c5120 d'Hyper) SANS le ANDI.W #$7F d'Hyper (0x311638-0x31164C) ; Hyper pose le
# bit 7 de $12A (BSET #7, 68K $007384) -> indice $85 au lieu de 5 : ($504,$706) au lieu de ($480,$700), page de l'effet
# decalee de $84 pixels. Ici : autour de l'appel de la copie d'Upper (talons moteur_plans / moteur_plans_vs), bit 7 de
# $12A(A5) retire puis remis (octet sauve en $FE08(A5) = $FF7E08). =0 : comme ro9a30.
EFFET_12A = os.environ.get("EFFET_12A", "0") == "1"
EFFET_SAUVE = 0xFE08
def _masque_12a():
    return [0x3c027000, 0x8c421114, 0x80430000 | ((0x012A ^ 1) & 0xffff), 0xa0430000 | ((EFFET_SAUVE ^ 1) & 0xffff),
            0x3063007f, 0xa0430000 | ((0x012A ^ 1) & 0xffff)]
def _remet_12a():
    return [0x3c027000, 0x8c421114, 0x80430000 | ((EFFET_SAUVE ^ 1) & 0xffff), 0xa0430000 | ((0x012A ^ 1) & 0xffff)]
# (e42, retour du 07/11 22 h 15 : bande de tuiles vertes au milieu de l'ecran quand la transition « logo » verte disparait
# sur la carte, apres un combat) la transition est l'objet d'HYPER $FFDE00 ($5E00(A5) ; octet $5E01 = actif, de la fin de
# la victoire au debut de la carte) ; sa barre horizontale (Hyper 0x968A4, donnees 0xFA00C : codes $15DF-$15F1) est en
# EMPLACEMENT 0, donc en codes de la banque commune d'HYPER ; sur la carte (A5+8 = 0 / 2), scroll1 = $0400 donne a
# l'emplacement 0 la banque commune d'UPPER (coeur 0015) -> morceaux de lettres du logo au lieu de la barre amincie
# (Upper : 0x2DDFC, codes $3B29-$3B3B). Avant le combat (A5+8 = 4) la base est deja $4400. BARRE_LOGO=1 : scene 4,
# chemin « plans d'Upper », A5+8 < 4 et $5E01(A5) non nul -> scroll1 = $4400 (alias S1_ALIAS : memes tuiles d'Upper,
# banque commune d'Hyper) tant que l'objet vit. =0 : comme ro9a31.
BARRE_LOGO = os.environ.get("BARRE_LOGO", "0") == "1"
# (logo_final_ha, retour du 12/11 soir, HANDOFF §227 : meme bande verte a la transition « logo » qui precede l'ecran de
# dialogue d'Upper : rival tire en ZERO 3 a l'etape 8 (decor $14, ex. Sakura contre Ryu) et combat final) l'objet $FFDE00
# nait a la fin de la victoire (A5+8 = 8) et vit ~145 images ; la carte ne dure alors que 4 images (A5+8 = 2) et l'ecran
# de dialogue est en A5+8 = 4, A5+C = 0 (puis 2) : chemin « plans d'Upper » mais hors du test A5+8 < 4 -> scroll1 =
# $0400 quand la barre s'affiche (fin de l'objet). BARRE_LOGO_FACE=1 (avec BARRE_LOGO=1) : l'alias vaut aussi pour A5+8 = 4 et A5+C = 0
# (ecran du dialogue / face-a-face) tant que $5E01 est non nul. PAS pour A5+C = 2 (ecran VS, logo d'entree en combat) :
# la colonne « VERSUS / VS » d'Upper est en scroll1, emplacement 0 (banque commune d'Upper) -> cassee par l'alias
# (essai lfa, logo_final_ha/essais/cmp_lfa.png). =0 : comme ro9a39.
BARRE_LOGO_FACE = os.environ.get("BARRE_LOGO_FACE", "0") == "1"
BARRE_LOGO_OBJ = 0x5E01
PLANS_BARRE_LOGO = (0x4400, 0x440, 0x4A0)
def stub_plans_auto(couches=0):
    """scene 4 (Arcade), a chaque image : A5+8 >= 6 (combat, victoire) ou (A5+8 = 4 et A5+C >= 4 : entree dans le
    decor) -> plans d'Hyper ; sinon (init, presentation / carte, face-a-face, VS) -> plans d'Upper"""
    if not PLANS: return [0x03e00008, 0x00000000]
    w = [0x27bdfff0, 0xffbf0000]
    w += forme_cmpi_w(0x0008, 6) + [0x3c037000, 0x8c631158]; i1 = len(w); w += [0x04600000, 0]   # bltz C -> L1 (< 6)
    br_ = []
    if RESULTAT_CPU:
        # (31/10, retour 7) manche gagnee par l'ORDINATEUR (gagnant $13A(A5) = $8800 et octet $924(A5) = $124 de J2 non
        # nul) : phase de resultat A5+C = $A sautee (A5+C = $C, A5+$10 = 0) comme dans Upper (pas de « WIN » ni de bonus)
        w += forme_cmpi_w(0x000C, 0xA) + [0x3c037000, 0x8c631150]; ir1 = len(w); w += [0x14600000, 0]   # bne -> Lr
        w += forme_cmpi_w(0x013A, 0x8800) + [0x3c037000, 0x8c631150]; ir2 = len(w); w += [0x14600000, 0]   # bne -> Lr
        w += _test_octet(0x0924); ir3 = len(w); w += [0x10600000, 0]                                      # beq -> Lr
        w += [0x2403000c, 0x3c027000, 0x8c421114, 0xa443000c, 0xa4400010]
        Lr = len(w)
        br_ += [(ir1, Lr), (ir2, Lr), (ir3, Lr)]
    if INTERMEDE_PLANS:
        # (31/10, retour 3) A5+C = 4 et A5+$10 = 0 (1re image de l'entree de la manche) : objets de la reserve $FFD000
        # ($5000-$5C00(A5)) remis a zero comme a l'entree en combat (vs_decor) : les portraits de l'intermede y restaient
        # SEULEMENT apres un intermede (octet $FE02(A5) pose pendant l'intermede) : la reserve porte aussi les objets
        # de l'entree de manche d'Hyper (ROUND / FIGHT), qu'il ne faut pas effacer dans un combat ordinaire
        w += forme_cmpi_w(0x000C, 4) + [0x3c037000, 0x8c631150]; ia = len(w); w += [0x14600000, 0]   # bne -> Lb
        w += forme_cmpi_w(0x0010, 0) + [0x3c037000, 0x8c631150]; ib = len(w); w += [0x14600000, 0]   # bne -> Lb
        w += _test_octet(0xFE02); ie_ = len(w); w += [0x10600000, 0]                                   # beq (pas d'intermede) -> Lb
        w += [0x3c027000, 0x8c421114] + [0xac400000 | (0x5000 + 0x200 * i) for i in range(7)]
        w += [0x24030000, 0x3c027000, 0x8c421114, 0xa0430000 | ((0xFE02 ^ 1) & 0xffff)]              # MOVE.B #0,$FE02(A5)
        Lb = len(w)
        # intermede (A5+C = 2, A5+$10 != 0 : sous-etats de l'intermede d'Upper) : plans d'Upper (bandeaux du regard)
        w += forme_cmpi_w(0x000C, 2) + [0x3c037000, 0x8c631150]; ic = len(w); w += [0x14600000, 0]   # bne -> LH
        w += forme_cmpi_w(0x0010, 0) + [0x3c037000, 0x8c631150]; idd = len(w); w += [0x10600000, 0]  # beq -> LH
        w += [0x24030001, 0x3c027000, 0x8c421114, 0xa0430000 | ((0xFE02 ^ 1) & 0xffff)]              # MOVE.B #1,$FE02(A5)
        w += _bases(PLANS_UPPER); ju = len(w); w += [0x10000000, 0]                                    # -> fin
        LH = len(w)
        br_ += [(ia, Lb), (ib, Lb), (ie_, Lb), (ic, LH), (idd, LH)]
    w += _bases_flag(PLANS_DECOR_U, PLANS_HYPER); j1 = len(w); w += [0x10000000, 0]                # -> fin
    L1 = len(w)
    w += forme_cmpi_w(0x0008, 4) + [0x3c037000, 0x8c631150]; i2 = len(w); w += [0x14600000, 0]   # bne RES -> Lu (!= 4)
    w += forme_cmpi_w(0x000C, 4) + [0x3c037000, 0x8c631158]; i3 = len(w); w += [0x04600000, 0]   # bltz C -> Lu (< 4)
    w += _bases_flag(PLANS_DECOR_U, PLANS_HYPER); j2 = len(w); w += [0x10000000, 0]
    Lu = len(w)
    if FLASH_SEL:   # (e40) image de l'init (A5+8 = 0) : bases d'Hyper gardees (voir plus bas, scrolls masques)
        w += forme_cmpi_w(0x0008, 0) + [0x3c037000, 0x8c631150]; ib_ = len(w); w += [0x14600000, 0]   # bne -> Upper
        w += _bases(PLANS_HYPER); jb_ = len(w); w += [0x10000000, 0]
        w[ib_] |= (len(w) - ib_ - 1) & 0xffff
    if BARRE_LOGO:  # (e42) transition « logo » d'Hyper active ($5E01(A5)) sur la carte (A5+8 < 4) : scroll1 en alias
        if BARRE_LOGO_FACE:
            w += forme_cmpi_w(0x0008, 4) + [0x3c037000, 0x8c631158]; ilt = len(w); w += [0x04600000, 0]   # bltz C -> test (< 4)
            w += forme_cmpi_w(0x000C, 0) + [0x3c037000, 0x8c631150]; ibl = len(w); w += [0x14600000, 0]   # bne RES -> Upper (A5+C != 0)
            w[ilt] |= (len(w) - ilt - 1) & 0xffff
        else:
            w += forme_cmpi_w(0x0008, 4) + [0x3c037000, 0x8c631158]; ibl = len(w); w += [0x04610000, 0]   # bgez C -> Upper (>= 4)
        w += _test_octet(BARRE_LOGO_OBJ); ibo = len(w); w += [0x10600000, 0]                           # beq (inactive) -> Upper
        w += _bases(PLANS_BARRE_LOGO); jbl = len(w); w += [0x10000000, 0]
        w[ibl] |= (len(w) - ibl - 1) & 0xffff; w[ibo] |= (len(w) - ibo - 1) & 0xffff
    w += _bases(PLANS_UPPER)
    if FLASH_SEL: w[jb_] |= (len(w) - jb_ - 1) & 0xffff
    if BARRE_LOGO: w[jbl] |= (len(w) - jbl - 1) & 0xffff
    # (etape 4) COUCHES_UPPER=1 : ordre des couches CPS-B des ecrans d'Upper ($32/$3A(A5) <- T_614CD0[$100], copie de
    # 0x15ACB0), qu'Upper calcule dans 0x2654B0 (remplacee par Hyper 0x9A6F0, combat = Hyper) : sans lui, $32 = $1B0E
    # d'Hyper (scroll1 devant) au lieu de $270E -> fond de la presentation recouvert de tuiles de scroll1
    if couches: w += [j_(3, couches), 0x00000000]
    if FLASH_SEL:
        # (e40, retour 1 du 07/11 : flash rouge apres la selection) a l'init de la scene 4 (A5+8 = 0), les bases de plans
        # passent a Upper alors que la VRAM garde le fond de la selection d'Hyper jusqu'a l'image ou le planisphere est
        # dessine (2-3 images : la logique ne tourne pas a chaque image pendant ce chargement) -> fond de la selection en
        # tuiles d'Upper. Ici : scroll1-3 masques (ANDI.W #$FFF1,$32(A5), apres l'ordre des couches) a l'image de l'init ;
        # l'image logique suivante recopie $32 (couches) et les reaffiche. (Un report des bases d'Hyper ne suffit pas :
        # 1re version d'e40a, planisphere en tuiles d'Hyper ; le masque seul agit une image apres les bases : e40b.)
        # Donc aussi : bases d'Hyper a l'image de l'init, celles d'Upper a l'image logique suivante (e40c).
        w += forme_cmpi_w(0x0008, 0) + [0x3c037000, 0x8c631150]; if_ = len(w); w += [0x14600000, 0]   # bne -> suite
        w += [0x3c027000, 0x8c421114, 0x94430032, 0x3063fff1, 0xa4430032]                              # ANDI.W #$FFF1,$32(A5)
        w[if_] |= (len(w) - if_ - 1) & 0xffff
    Lf = len(w); w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    for i, L in ((i1, L1), (i2, Lu), (i3, Lu), (j1, Lf), (j2, Lf)): w[i] |= (L - i - 1) & 0xffff
    for i, L in br_: w[i] |= (L - i - 1) & 0xffff
    if INTERMEDE_PLANS: w[ju] |= (Lf - ju - 1) & 0xffff
    return w

# (28/10, ossature des decors, etape 1) D4_REPLI=1 : le decor demande en numerotation unique (regle D4 : Upper $00-$4E,
# SFA2 $50-$72, SFA1 $A0-$B8) n'existant pas encore dans ro9a, repli sur le decor d'Hyper de la MEME famille
# (ZERO 3 -> 4, ZERO 2 / ALPHA -> 2, ZERO -> 0) au lieu de « < 8 garde, sinon 4 » (Ryu $00, Ken $02, Charlie $06
# tombaient par coincidence sur les decors 0 / 2 / 6 d'Hyper). decors/d4/regle_d4_decidee.tsv
D4_REPLI = os.environ.get("D4_REPLI", "1") == "1"
def stub_decor(cible, decor=4):
    """(etape 3) decors d'Hyper en Arcade (alternative minimale de DECORS.md) : CMPI.W #8,$100(A5) ; BCS -> appel ;
    sinon (rival $14, Bison, decors d'Upper) MOVE.W #decor,$100(A5) ; puis JSR cible (adresse d'EXECUTION)"""
    w = [0x27bdfff0, 0xffbf0000]
    # (e26) decors d'Upper actives : $100 garde, drapeau $FE10 = 1 ; sinon drapeau 0 puis repli
    bu = []
    for v in DECORS_UPPER:
        if v == 'tous':                                                                      # CMPI.W #$50 ; BCS -> Lu
            w += forme_cmpi_w(0x100, 0x50) + [0x3c037000, 0x8c631158]; bu.append(len(w)); w += [0x04600000, 0x00000000]
            continue
        w += forme_cmpi_w(0x100, v) + [0x3c037000, 0x8c631150]; bu.append(len(w)); w += [0x10600000, 0x00000000]   # beq -> Lu
    w += _pose_octet(FLAG_DECOR, 0)
    if D4_REPLI:
        sets = []
        for borne, v in ((0x50, 4), (0xA0, 2)):
            w += forme_cmpi_w(0x100, borne) + [0x3c037000, 0x8c631158]; sets.append((len(w), v)); w += [0x04600000, 0x00000000]   # BCS -> pose v
        w += [0x24030000, 0x3c027000, 0x8c421114, 0xa4430100]; fins = [len(w)]; w += [0x10000000, 0x00000000]   # SFA1 -> 0
        poses = []
        for i, v in sets:
            poses.append((i, len(w))); w += [0x24030000 | v, 0x3c027000, 0x8c421114, 0xa4430100]; fins.append(len(w)); w += [0x10000000, 0x00000000]
        L = len(w)
        for i, l in poses: w[i] |= (l - i - 1) & 0xffff
        for i in fins: w[i] |= (L - i - 1) & 0xffff
        w += [0x00000000]
    else:
        w += forme_cmpi_w(0x100, 8)
        w += [0x3c037000, 0x8c631158, 0x04600006, 0x00000000]          # lw v1,C ; bltz v1 -> appel (BCS)
        w += [0x24030000 | decor, 0x3c027000, 0x8c421114, 0xa4430100, 0x00000000]   # MOVE.W #decor,$100(A5)
    if bu:
        jr = len(w); w += [0x10000000, 0x00000000]                                       # -> suite
        Lu = len(w); w += _pose_octet(FLAG_DECOR, 1)
        for i in bu: w[i] |= (Lu - i - 1) & 0xffff
        w[jr] |= (len(w) - jr - 1) & 0xffff
    # entree en combat : en-tetes ($0000-$0003) des 7 emplacements d'objets $5000-$5C00 (moteur 0x3A45F0 / Upper
    # 0x1196E0) remis a zero : les objets texte d'Upper des ecrans Arcade y laissaient leur type (1), et le combat
    # d'Hyper reutilise l'emplacement $5C00 (pointeur $0156) en n'ecrivant que $0000-$0001 -> objet texte fantome
    w += [0x3c027000, 0x8c421114] + [0xac400000 | (0x5000 + 0x200 * i) for i in range(7)]   # CLR.L $5x00(A5)
    w += [j_(3, cible), 0x00000000, 0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    return w

# (02/11, e26, etape 3 des decors) DECORS D'UPPER EN COMBAT. DECORS_UPPER = liste (hexa, numerotation unique = $100 d'Upper)
# des decors d'Upper actives ; vide -> comme ro9a18. vs_decor : $100 dans la liste -> garde $100 et pose le drapeau
# « decor d'Upper » (octet $FE10(A5) = $FF7E10, zone des decors C10), sinon drapeau 0 et repli D4_REPLI. Talons moteur_* :
# partie Arcade ($FE00) ET decor d'Upper ($FE10) -> copie d'Upper (0x151B80 plans, 0x4B270 palettes), sinon Hyper
# (0x30EC10, 0x60A20) : site Hyper 0x9A8F0 (combat, a chaque image) et appels de l'ecran VS (DECOR_VS).
# DECORS_UPPER=tous : tous les decors d'Upper ($00-$4E, test de plage : $100 < $50)
_DU = os.environ.get("DECORS_UPPER", "tous")
DECORS_UPPER = ['tous'] if _DU == 'tous' else [int(x, 16) for x in _DU.split(',') if x]
FLAG_DECOR = 0xFE10
# Bases du combat sur un decor d'Upper : scroll1 = $4400 (S1_ALIAS=1) : le coeur FBNeo masque l'adresse de tuile par
# nCpsGfxMask ($7FFFFFF pour 80 Mo) -> $44000000 adresse les plans d'Upper comme $0400, sans etre le signal de la banque
# commune d'Upper (0015 : egalite a $0400 ; 0017 : bit $8000) -> decor complet, objets d'Hyper. S1_ALIAS=0 : scroll1
# masque ($32 bit 1) et base d'Hyper $300 (ciel noir).
S1_ALIAS = os.environ.get("S1_ALIAS", "1") == "1"
S1_MASQUE = os.environ.get("S1_MASQUE", "0" if S1_ALIAS else "1") == "1"
PLANS_DECOR_U = tuple(int(x, 16) for x in os.environ.get("PLANS_DECOR_U", "4400,440,4a0" if S1_ALIAS else "300,440,4a0").split(','))
# (e28) OBJETS_DECOR=1 : OBJETS DE DECOR d'Upper (linge de la hutte de Blanka...) : l'entree en combat d'Upper (0x2651C0 /
# 0x265310) appelle 0x4C1B0 (objets de T_950CE0 par decor), envoyee jusqu'ici par DECOR_VS a Hyper 0xAC050 (HUD d'Hyper,
# qui ne cree plus rien : JAUGE_HYPER) -> talon moteur_objets : decor d'Upper ($FE00 et $FE10) -> copie d'Upper 0x4C1B0,
# sinon Hyper 0xAC050. =0 : comme ro9a20.
OBJETS_DECOR = os.environ.get("OBJETS_DECOR", "1") == "1"   # (e31, ro9a23) defaut 1 : donnees dans la zone des decors (ZONE_DECORS) ; =0 -> ro9a22 a l octet (avec AIG_D1=0)
# (e29) OBJETS_DECOR=1, partie programme : (a) l'allocateur d'Upper 0xCD860 (reservoir $FFC000 = $4000(A5), 16 x $80,
# compteur $6EBB, pile de pointeurs $6E8C ; Hyper l'initialise (0x390640 = Upper 0xCC7D0) mais ne l'alloue ni ne le
# parcourt) est GREFFE pour le seul appelant 0x4C1B0 (PAR_APPELANT) ; les autres appelants gardent Hyper 0x391190
# (reservoir $FFAC00) ; (b) le parcours d'Upper de ce reservoir, 0xFD620 (classes T_611E50, toutes greffees), est appele
# a chaque image de combat sur decor d'Upper par le talon moteur_plans (apres 0x151B80, comme Upper 0x2654B0).
# OBJETS_PARCOURS=0 : sans (b).
# (e31, decision de l'utilisateur du 01/11 : place des donnees de decor, « prevoir au plus large ») ZONE_DECORS=1 : ZONE DE
# DONNEES DE DECORS DEDIEE, hors de l'espace PS2 de la greffe (plein a 7,8 Ko pres). Tete (adressable en PS2) = fenetre des
# decors PS2 $FE0000-$FEFFFF -> 68K $4D8000-$4E7FFF : table D4 ($4D8000, 128 o) puis REPERTOIRE de la zone ($4D8080, voir
# e31/DECORS-ZONE.md). CORPS = T1b $4E8000-$5D3FFF (944 Ko), 68K seulement : les regions copiees y sont posees a des
# adresses 68K ETIQUETEES ($014E8000...) ; constantes de code et pointeurs de donnees qui les visent sont reloges vers ces
# adresses ; le traducteur les rend telles quelles (HSFA_ZONES_68K) et sert le corps en ext_<y>.bin (HSFA_GREFFE_ZONE).
# Lot 1 = donnees des objets de decor d'Upper, zone PS2 0x950CE0-0x99FF00 (ZONE_OBJETS) copiee EN ENTIER. Defaut : comme
# OBJETS_DECOR. =0 : regions dans le bloc PS2 comme avant.
ZONE_DECORS = os.environ.get("ZONE_DECORS", "1" if OBJETS_DECOR else "0") == "1"
ZONE_OBJETS = tuple(int(x, 16) for x in os.environ.get("ZONE_OBJETS", "950ce0-99ff00").split('-'))
ZONE_CORPS = (0x4E8000, 0x5D4000)                    # T1b apres la tete (fenetre $FE0000) ; $5D4000 = tranche d'Hyper
ZONE_TAG = 0x01000000
ZONE_REP = 0x80                                      # repertoire : decalage dans la fenetre des decors (apres D4)
ZONE_REP_LOTS, ZONE_REP_DECORS = 16, 128
def zone_repertoire(lots, fin_occupee):
    """(e31) repertoire de la zone des decors (ordre PS2, petit-boutiste ; voir e31/DECORS-ZONE.md) :
    +$00 'HSFADZ01' ; +$08 u16 version, u16 nombre de lots ; +$0C u32 fin occupee du corps ; +$10 u32 debut du corps,
    +$14 u32 fin du corps (adresses 68K etiquetees) ; +$18 2 x u32 reserves ; +$20 16 lots x 16 o (u8 famille, u8 reserve,
    u16 drapeaux, u32 base etiquetee, u32 taille, u32 origine) ; +$120 index par decor (128 x u32, $100 / 2 -> descripteur
    etiquete, 0 = aucun)"""
    b = bytearray(b'HSFADZ01') + struct.pack('<HHIII8x', 1, len(lots), fin_occupee, ZONE_TAG | ZONE_CORPS[0], ZONE_TAG | ZONE_CORPS[1])
    assert len(lots) <= ZONE_REP_LOTS
    for fam, drap, base, taille, orig in lots: b += struct.pack('<BBHIII', fam, 0, drap, base, taille, orig)
    b += bytes(0x20 + 16 * ZONE_REP_LOTS - len(b)) + bytes(4 * ZONE_REP_DECORS)
    return bytes(b)
OBJETS_PARCOURS = os.environ.get("OBJETS_PARCOURS", "1") == "1"
# (e33) OBJETS_CLASSES=1 : CLASSES DE DECOR ENTIERES. (1) T_611E50 a $2F entrees (pas $28) : classes $28-$2E dans la
# fermeture ; (2) routines de la fermeture (plages des classes) renvoyees a Hyper -> GREFFEES : la classe $26 (0xFFD80) et la
# $2E (0x419D80) allaient au gestionnaire d'Hyper 0x2FEC0 (« impose » / regle j), qui ecrit hors de l'objet (21 Z3 : $FFC680
# ecrase, octet 9 = $3D -> liste d'affichage 0xC67B0, saut impair $9BD29) ; 31 enveloppes de liberation (JMP 0xCD9A0)
# allaient a Hyper 0x31F50 (-> 0x391AD0 : pile $6E90 / compteur $6EBD des objets d'Hyper !) ; (3) LIBERATION d'Upper
# 0xCD9A0 (pile $6E8C, compteur $6EBB, octet 9 = $14) greffee pour les appelants de la fermeture (Hyper 0x3912D0 =
# pile $6E88 : autre reservoir) ; idem 0xC6370 (test d'ecran par D6 ; « homologue » 0x38B4C0 = 0xC65B0) ; l'allocateur
# 0xCD860 garde la copie pour toute la fermeture. =0 : comme e32.
OBJETS_CLASSES = os.environ.get("OBJETS_CLASSES", "1") == "1"
# (e33) CONST_OBJET=decor (defaut) : constantes d'en-tete d'objet $00TT0001 (lui/ori) laissees telles quelles dans le code
# des classes de decor (voir Greffe2.valeur) ; =1 : dans TOUT le code greffe ; =0 : comme e32
CONST_OBJET = os.environ.get("CONST_OBJET", "decor")
CONST_OBJET = None if CONST_OBJET == "0" else CONST_OBJET
# (e34) CONST_OBJET_PLUS : routines HORS DECOR dont l'en-tete d'objet $00TT0001 (lui $TT / ori 1 suivi de MOVE.L ...,(A4))
# etait reloge comme une adresse (copie : 0x4DC80 $780001 -> $E862C1 ; 0x50290 et 0x5ACE0 $760001 -> $E62FB1 ; 0x11F510
# $230001 -> $1F97E1 ; 0x1B3140 et 0x1B3F70 $220001 -> $1F74A1). Les 28 autres « cas » de e33/const_objet_37.txt ($2C0001,
# $3880FF) sont des LUI de cibles de JSR (lui $2C / addiu / jalr : $2BD5A0, $2BDDA0, $386A30) bien relogees : faux positifs.
# Vide : comme e33.
CONST_OBJET_PLUS = tuple(int(x, 16) for x in os.environ.get("CONST_OBJET_PLUS", "4dc80,50290,5ace0,11f510,1b3140,1b3f70").split(',') if x)
OBJETS_E0 = os.environ.get("OBJETS_E0", "1") == "1"
# (e46, ro9a36 : tour sombre dans le ciel de Ryu, lune de Sodom en double et non détourée, glitch devant la tour de Cammy)
# DECOR_E0=1 : les objets de décor d'Upper (trames copiées dans la zone des décors, emplacement 0) donnent des codes de la
# banque commune d'UPPER (f351). Au combat la banque e0 est f545 d'HYPER (prolongée par f351 seulement au-delà de $33F0,
# OBJETS_E0) : un code < $33F0 dont l'entrée d'Hyper diffère de celle d'Upper donne une autre tuile (Ryu $28DE, Sodom
# $1D8A, Cammy $100D/$16C6/$1BB1/$295D...). Ici : dans les trames de type 2 de la zone ([2, ?, n-1, 0, pointeur $00ED/$00EE
# ....] puis n paires (code, attr)), chaque entrée à palette >= DECOR_E0_PAL ($0F, palettes des objets de décor) dont une
# tuile est dans ce cas est RECODÉE vers un code libre >= $6C60 (au-delà de f351) ; f545 (et f351 de la construction)
# sont prolongées par les entrées d'Upper de ces tuiles. Données seules, aucun code ni cœur changé. =0 : comme ro9a35b.
DECOR_E0 = os.environ.get("DECOR_E0", "0") == "1"
DECOR_E0_PAL = int(os.environ.get("DECOR_E0_PAL", "f"), 16)
DECOR_E0_DEBUT = 0x6C60
_DECOR_E0_TABLE = {}                                   # nouveau code -> entrée de f351 d'Upper (rempli par recode_decor_e0)
def _banques_hu():
    W9, W5 = "@HA_MAME_RO9@/banques_hx", "@HA_MAME_RO5@/banques_hx"
    h_ = open(os.path.join(W9, "f545.bin"), 'rb').read(); u_ = open(os.path.join(W5, "f351.bin"), 'rb').read()
    return struct.unpack('<%dI' % (len(h_) // 4), h_), struct.unpack('<%dI' % (len(u_) // 4), u_)
def recode_decor_e0(zbuf):
    """(e46) DECOR_E0 : recode dans zbuf (bytearray, ordre PS2) les entrées des trames d'objets de décor dont une tuile
    a une entrée de banque commune différente chez Hyper (f545) et Upper (f351) ; remplit _DECOR_E0_TABLE"""
    H_, U_ = _banques_hu()
    w_ = lambda o: struct.unpack_from('<H', zbuf, o)[0]
    def tuiles(c, at):
        W_, Hh = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
        return [[((c & ~0xf) + (((c & 0xf) + i) & 0xf) + 0x10 * j) & 0xffff for i in range(W_)] for j in range(Hh)]
    nxt = DECOR_E0_DEBUT; deja = {}; n_ent = n_tr = 0
    for o in range(0, len(zbuf) - 12, 2):
        if not (w_(o) == 2 and w_(o + 6) == 0 and w_(o + 4) < 0x80 and w_(o + 10) in (0xED, 0xEE)): continue
        n_tr += 1
        for k in range(w_(o + 4) + 1):
            a = o + 12 + 4 * k
            if a + 4 > len(zbuf): break
            c, at = w_(a), w_(a + 2)
            if (at & 0x1f) < DECOR_E0_PAL: continue
            T = tuiles(c, at)
            if not any(t < len(H_) and H_[t] != U_[t] for r in T for t in r): continue
            cle = (c, at & 0xff00)
            if cle not in deja:
                if len(T) == 1 and len(T[0]) == 1: base = nxt; nxt += 1
                else: nxt = (nxt + 15) & ~15; base = nxt; nxt += 16 * len(T)
                for j, r in enumerate(T):
                    for i, t in enumerate(r): _DECOR_E0_TABLE[base + i + 16 * j] = U_[t]
                deja[cle] = base
            struct.pack_into('<H', zbuf, a, deja[cle]); n_ent += 1
    assert nxt <= 0x8000, "DECOR_E0 : codes au-delà de $7FFF"
    print("DECOR_E0 : %d trames, %d entrées recodées, %d codes (%d sprites) -> $%04X-$%04X" % (n_tr, n_ent, len(_DECOR_E0_TABLE), len(deja), DECOR_E0_DEBUT, nxt - 1))
    return zbuf
def _prolonge_e0(d):
    """(e46) table e0 (bytes) prolongée par _DECOR_E0_TABLE (trous = $FFFFFFFF)"""
    if not _DECOR_E0_TABLE: return d
    n = max(_DECOR_E0_TABLE) + 1; V = list(struct.unpack('<%dI' % (len(d) // 4), d))
    assert len(V) <= DECOR_E0_DEBUT, len(V)
    V += [0xFFFFFFFF] * (n - len(V))
    for c, v in _DECOR_E0_TABLE.items(): V[c] = v
    return struct.pack('<%dI' % len(V), *V)
OBJETS_MANCHE = os.environ.get("OBJETS_MANCHE", "1") == "1"
# (e29) OBJETS_ANIM=1 : POSE D'ANIMATION d'Upper pour les objets de decor. Les aides de dessin des classes de decor (0xFDC10,
# 0xFDCB0... : JMP 0xC84A0 / 0xC82D0) allaient aux homologues d'Hyper (0x38D3B0 « j) », 0x38D1E0...) : exceptions pc $A08
# en 0x38D4FC (MOVE.L (A0),$32(A6), A0 impair) et 0x38D7E8 (balayage f38 sur e29d, 85/85 plantees). Copies d'Upper de toute
# la pose (liste ANIM_GREFFE de force3 + 0xC84C0) pour ces appelants (et entre elles) ; les autres gardent Hyper (PAR_APPELANT).
OBJETS_ANIM = {0xC84A0: 0x38D3B0, 0xC84C0: 0x38D3D0, 0xC8510: 0x38D420, 0xC85A0: 0x38D4B0, 0xC8D50: 0x2B9E70, 0xC8EC0: 0x32A5D0,
               0xCE4F0: 0x386F30, 0x139750: 0x388910, 0xC8150: 0x38D060, 0xC82D0: 0x38D1E0, 0xC85C0: None, 0xC8890: 0x38D510,
               0xC8C00: 0x38D880, 0xC8C50: 0x38D8D0, 0xC8F10: None, 0xC8F80: None,
               0xC8450: 0x38D360, 0xC8480: 0x38D390, 0xC8490: 0x390B0, 0xC8C80: 0x38D900}   # (e29j) + reste de la pose if os.environ.get("OBJETS_ANIM", "1") == "1" else {}
OBJETS_ANIM_FERMETURE = os.environ.get("OBJETS_ANIM_FERMETURE", "1") == "1"
OBJETS_ANIM_GARDE = (0xFDC10, 0xFDCB0, 0x10AE70, 0x10BC80, 0x10BEC0, 0x414EA0, 0x105080, 0x109720, 0x1098F0, 0x10AF00, 0x10BE20,
                     0x415450, 0x1078E0, 0x107AC0, 0x1001F0)
# ... et les routines de la pose deja GREFFEES (0xC8600, 0xC8770, 0xC8830... : la classe $0C 0x1025E0 -> 0xC8770 -> 0xC8830 ->
# 0xC8890 allait a Hyper 0x38D510, exception en 0x38D7E8 sur l'objet $FFC780) : elles appellent desormais les copies d'Upper
# pour TOUS leurs appelants (objets des ecrans Arcade compris). OBJETS_ANIM_POSE=0 : sans.
OBJETS_ANIM_POSE = os.environ.get("OBJETS_ANIM_POSE", "1") == "1"
if OBJETS_ANIM_POSE:
    OBJETS_ANIM_GARDE += (0xC8600, 0xC8770, 0xC87C0, 0xC8830, 0xC8FE0, 0xC9180, 0xC92F0, 0xC9340, 0xC93B0, 0xC9410, 0xC95B0, 0xC9720,
                          0xC9770, 0xC97E0)
# (e29) autres appelants de 0xCD860 qui gardent la copie : sous-etats des classes de decor (T_611E50) qui creent des
# objets enfants (classe $11 : 0x103950 par T_612334 ; classes $22-$27 : 0x412120, 0x413A90 par T_628540/564 ; 0x418160).
# Restent a Hyper (statu quo) : 0x57A90, 0x58390 (table T_60CC54, autre systeme d'objets).
OBJETS_ALLOC_GARDE = tuple(int(x, 16) for x in os.environ.get("OBJETS_ALLOC_GARDE", "103950,412120,413a90,418160").split(',') if x)
def _pose_octet(d68, v): return [0x24030000 | (v & 0xffff), 0x3c027000, 0x8c421114, 0xa0430000 | ((d68 ^ 1) & 0xffff)]
MASQUE_S1 = [0x3c027000, 0x8c421114, 0x94430032, 0x3063fffd, 0xa4430032]   # ANDI.W #$FFFD,$32(A5)
def stub_moteur(si, sinon, masque=False, m12a=False):
    """partie Arcade ($FE00) ET decor d'Upper ($FE10) -> JSR si (copie d'Upper) [+ scroll1 masque], sinon JSR sinon
    (e28, D4_VERSUS) : ($FE00 OU $FE11) ET $FE10 ; le chemin de l'Arcade garde EXACTEMENT les instructions d'avant (la
    cadence du combat en depend : e28f/e28g, ou l'ordre des tests changeait, decalaient les combats de l'Arcade) : le bloc
    VERSUS ($FE00 = 0) est place entre « si » et « sinon »"""
    w = [0x27bdfff0, 0xffbf0000]; br = []
    w += _test_octet(FLAG); b0 = len(w); w += [0x10600000, 0]                        # beq -> Lv (D4_VERSUS) / sinon
    w += _test_octet(FLAG_DECOR); br.append(len(w)); w += [0x10600000, 0]           # beq -> sinon
    Lsi = len(w); w += (_masque_12a() if m12a else []) + _appels(si) + (_remet_12a() if m12a else []) + (MASQUE_S1 if masque else []); j = len(w); w += [0x10000000, 0]
    if D4_VERSUS:
        Lv = len(w); w[b0] |= (Lv - b0 - 1) & 0xffff
        w += _test_octet(FLAG_VS); br.append(len(w)); w += [0x10600000, 0]          # beq -> sinon
        w += _test_octet(FLAG_DECOR); br.append(len(w)); w += [0x10600000, 0]       # beq -> sinon
        jb = len(w); w += [0x10000000, 0]; w[jb] |= (Lsi - jb - 1) & 0xffff           # -> si
    else:
        br.append(b0)
    Ls = len(w); w += _appels(sinon)
    Lf = len(w); w += [0xdfbf0000, 0x27bd0010, 0x03e00008, 0x00000000]
    for i in br: w[i] |= (Ls - i - 1) & 0xffff
    w[j] |= (Lf - j - 1) & 0xffff
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
    PAR_APPELANT_SYNTH = {}                        # (e26) {routine d'Upper : (talon synthetique, appelants envoyes au talon)}
    CONST_OBJET_GARDE = None                       # (e33) None = tout le code greffe ; sinon garde (GardePlages)
    def valeur(self, v, ctx):
        # (e33) CONST_OBJET : constante d'EN-TETE D'OBJET formee par lui/ori ($00TT0001 : actif = 1, type TT ; ex. Upper
        # 0x414B50 lui $79 / ori 1 -> MOVE.L #$10079,(A4)) prise pour une adresse (donnee 0x790001 -> $E60001, code 0x2C0001
        # -> $580001) : le type de l'objet change ($E6 dans le reservoir $FFB000 d'Hyper -> 21 Z3 plante, pc $81CF2).
        # Une adresse impaire $xx0001 n'est jamais un pointeur de code ni de table : laissee telle quelle.
        if CONST_OBJET and isinstance(ctx, int) and (v & 0xffff) == 1 and (v >> 16) < 0x100 and (
                (CONST_OBJET == "1" if self.CONST_OBJET_GARDE is None else PL.routine_de(ctx) in self.CONST_OBJET_GARDE)):
            self.rap['const_objet'].append((ctx, v)); return v
        return super().valeur(v, ctx)

    def code(self, v, ctx):
        f = v - BASE
        if f in self.PAR_APPELANT_SYNTH and isinstance(ctx, int):
            nom_, vers_ = self.PAR_APPELANT_SYNTH[f]
            if PL.routine_de(ctx) in vers_: self.rap['par_appelant_vers_talon'].append((ctx, v)); return self.synth_place[nom_] + BASE
        if f in self.PAR_APPELANT_HYPER and isinstance(ctx, int):
            h_, vers_ = self.PAR_APPELANT_HYPER[f]
            if PL.routine_de(ctx) in vers_: self.rap['par_appelant_vers_hyper'].append((ctx, v)); return h_ + BASE
        if f in self.PAR_APPELANT:
            h_, garde_ = self.PAR_APPELANT[f]
            r_ = PL.routine_de(ctx) if isinstance(ctx, int) else None
            # (e33) case d'une table de donnees citee par la garde (ex. table de pointeurs d'une classe de decor -> 0xC8EC0)
            c_ = ctx[1] if isinstance(ctx, tuple) and len(ctx) == 2 and ctx[0] == 'donnee' else None
            if r_ not in garde_ and not (c_ is not None and c_ in getattr(garde_, 'cases', ())):
                self.rap['par_appelant_hyper'].append((ctx, v)); return h_ + BASE
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
# (e30, retour du 01/11 : citations de victoire glitchees) VICT_PLANS=1 : l'ecran de victoire (scene 4, A5+8 = 8, Upper
# 0x26F930 = T_61C200[4], citation du gagnant, joueur OU ordinateur) dessine ses bandes « STREET FIGHTER ALPHA 3 » et
# son cadre de texte avec des objets de la banque commune d'UPPER (emplacement 0 : $1D8A x 144, $226B x 60, $3B3C-$3B3E),
# or plans_auto y laisse les bases du combat (4400 decor d'Upper / 300 decor d'Hyper) : emplacement 0 = banque d'Hyper
# e545 -> damier rose / orange. Entree 4 de la copie de T_61C200 -> talon plans_vict : bases PLANS_VICT_U (decor
# d'Upper : scroll1 = $400, signal 0015 de la banque commune d'Upper, memes tuiles que l'alias $4400) ou PLANS_VICT_H
# (decor d'Hyper : $8300 marque, coeur 0017 : tuiles d'Hyper, objets d'Upper), puis la copie de 0x26F930. Aucun
# changement du chemin du combat (plans_auto intact : cadence des combats inchangee). =0 -> ro9a21.
VICT_PLANS = os.environ.get("VICT_PLANS", "1") == "1"
U_T_SCENE4 = 0x61C200                                   # table de la scene 4 d'Upper (A5+8, 9 entrees) ; [4] = 0x26F930
PLANS_VICT_U = tuple(int(x, 16) for x in os.environ.get("PLANS_VICT_U", "400,440,4a0").split(','))
PLANS_VICT_H = tuple(int(x, 16) for x in os.environ.get("PLANS_VICT_H", "8300,340,3a0").split(','))
# (e30, retour du 01/11 : « bandeau » blanc / vert en haut a droite, fragment vert en haut a gauche du CONTINUE)
# INDIC_UPPER=1 : indicateurs du cote libre (« PRESS START », « CONTINUE? »… : octet $14B du joueur, pose par la COPIE
# d'Upper 0x29874 (68K Upper $19BE, ro9a $10BC, zone d'accueil Z80), dessines par la copie de 0x29994 (Upper $19E6, ro9a
# $10E4 : tampon d'objets fixes $79C4(A5), $71B8/$71BC/$71C0) depuis la tache des joueurs (copie, ro9a $A10A6)) : objets
# de l'emplacement 1 (plan2), codes T_CED150 (Upper ; = T_ECFC90 de ro9a, 36 entrees) + $1C00 ($2715 pour J2, x = $E148).
# Upper les montre en codes de SES plans ; dans ro9a la table plan2 est celle d'Hyper : $2715 = morceau d'une image
# d'Hyper (bandeau blanc / vert : selection, histoire, carte, citations, combat ; fragment du CONTINUE de J1). Le +$1C00
# (Upper 0x29CA4, « addiu a0,v1,$1C00 », ro9a fichier 0x1404) devient +$7700 (= $1C00 + $5B00)
# et la table plan2 de la construction est PROLONGEE ($5B00-$FFFF -> plans d'Upper, $88000 + code - $5B00 ; les
# $5B00 entrees d'Hyper inchangees a l'octet). Donnee + 1 immediat, aucun changement du coeur. =0 -> ro9a21.
INDIC_UPPER = os.environ.get("INDIC_UPPER", "1") == "1"
RANG_E1 = os.environ.get("RANG_E1", "1") == "1"         # (e34) voir le patch RANG_E1 ; =0 : comme e33
RANG_E1_SITES = (0x95230, 0x95474, 0x95600, 0x95714)   # ADDI.W #$1C00 d'Upper (carte image : $111F2, $11238, $11252, $11272)
PLAN2_UPPER_DEBUT, PLAN2_UPPER_BASE = 0x5B00, 0x88000
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

class GardePlages(frozenset):
    """(e29) garde de PAR_APPELANT : routines listees OU dans des plages (toute la pose 0xC8000-0xC97FF : 0xC8530,
    appelee entre 0xC8510 et 0xC85A0, envoyait la copie vers la pose d'Hyper 0x38D4B0 -> exception en 0x38D4FC)"""
    def __new__(cls, ens, plages=()):
        o = super().__new__(cls, ens); o.plages = tuple(plages); o.cases = frozenset(); return o
    def __contains__(self, x):
        return frozenset.__contains__(self, x) or (x is not None and any(a <= x < b for a, b in self.plages))

def classes_decor_cases():
    """(e33) cases (exec PS2 d'Upper) des tables de pointeurs de code citees par les classes de decor"""
    return frozenset(v + i for v in classes_decor_fermeture()[1] for i, _ in PL.ptrs_code(v))

def classes_decor_fermeture():
    """(e29) routines (plages des classes de decor 0xFD600-0x10C000 / 0x411000-0x41A000, + 0x4C1B0) atteintes depuis
    T_611E50 par appels et tables de code ; donnees citees"""
    ind = lambda a: 0xFD600 <= a < 0x10D0F0 or 0x411000 <= a < 0x41A000
    T = 0x611E50 - BASE
    pile_ = [r for r in (struct.unpack_from('<I', PL.b5, T + 4 * i)[0] - BASE for i in range(0x2F if OBJETS_CLASSES else 0x28)) if ind(r)] + [0x4C1B0]
    if OBJETS_CLASSES: pile_.append(0xFD620)          # (e33) + le parcours du reservoir
    vus_, data_ = set(), set()
    while pile_:
        r = pile_.pop()
        if r in vus_ or r not in PL.E5: continue
        vus_.add(r)
        for t_, v_, _ in PL.refs_routine(r):
            if t_ == 'code' and ind(v_): pile_.append(v_)
            elif t_ == 'data':
                data_.add(v_)
                for _, c_ in PL.ptrs_code(v_):
                    if ind(c_): pile_.append(c_)
    return vus_, data_

def preuves_objets_decor(D2):
    """(e29) cases de pointeurs de la fermeture statique des donnees des classes de decor d'Upper"""
    _, data_ = classes_decor_fermeture()
    F_ = D2.Fermeture(data_, None, reutil=False)
    # la fermeture statique s'etend a tout le module (animations des persos 0x7B0000-0x86FFFF, fichier 390...) : seules les
    # cases ET cibles de la zone des donnees de decor d'Upper (OBJETS_ZONE, defaut 0x950000-0x9A0000) sont gardees
    lo_, hi_ = (int(x_, 16) for x_ in os.environ.get("OBJETS_ZONE", "950000-9a0000").split('-'))
    out_ = {v + i for (v, i), p_ in F_.pointeurs.items() if lo_ <= v + i < hi_ and lo_ <= p_ < hi_}
    # + les enregistrements d'animation (atteints par des tables de DECALAGES 16 bits, que la fermeture ne suit pas) :
    # toute case alignee de la zone dont le long est un pointeur (est_pointeur) vers la zone
    if os.environ.get("OBJETS_ZONE_TOUT", "0") == "1":   # (e29) essai : +54 Ko, bloc au-dela de $FE0000 -> 0
        REFS_ = set(PL.refs_donnees5())
        for c_ in range(lo_, hi_, 4):
            p_ = struct.unpack_from('<I', D2.octets(c_, 4))[0]
            if lo_ <= p_ < hi_ and D2.est_pointeur(c_, p_, REFS_): out_.add(c_)
    return out_

def a_exec(g, f5):
    """adresse d'execution de la copie greffee de la routine d'Upper f5"""
    n = g.neuf(f5); assert n is not None, hex(f5); return n + BASE

def main():
    import force3 as FO
    nom = os.environ.get("NOM", "ro9a")
    P_ = os.path.join(G, 'constructions', nom); os.makedirs(P_, exist_ok=True)
    rac = [int(x, 16) for x in os.environ.get("RACINES", "4E1C0,24EA30,261560,2614A0,2614D0,261500,1346A0").split(',')]
    if COMBAT_HYPER: rac += [x for x in KO_ARCADE + (0x269340, 0x26E900) if x not in rac]
    if COMBAT_HYPER and TYPE14 and 0x17FD50 not in rac: rac.append(0x17FD50)
    if AFFICHAGE_UPPER:
        rac += [x for x in AFFICHAGE if x not in rac]; Greffe2.PAR_APPELANT = dict(AFFICHAGE)
    if COMBAT_HYPER and VS_UPPER: Greffe2.PAR_APPELANT_HYPER = dict(DECOR_VS)
    # (31/10, e23) JAUGE_HYPER=1 : HUD de la 1re manche. L'entree en combat d'Upper (0x2651C0 / 0x265310) appelle 0x295F0
    # (objets $1C 6, 9, 2, 5 : copie d'Upper) puis 0x4C1B0, envoyee par DECOR_VS a Hyper 0xAC050 (HUD d'Hyper : 5 objets,
    # + sous-type 7 = jauge ISM / super de J1) qui exige 5 places libres ($6EBD) et n'en trouve plus que 3 -> jauge absente
    # en 1re manche (Hyper la cree lui-meme ensuite). 0x295F0 va aussi a Hyper 0xAC050 pour ces appelants (le 2e appel ne
    # trouve plus de place et ne cree rien).
    if COMBAT_HYPER and VS_UPPER and os.environ.get("JAUGE_HYPER", "1") == "1": Greffe2.PAR_APPELANT_HYPER[0x295F0] = (0xAC050, _VS)
    TC = PL.tables_a_completer() if os.environ.get("TABLES_OBJETS", "1") == "1" else []
    FF_ = FO.force()
    if OBJETS_DECOR and COMBAT_HYPER and VS_UPPER:   # (e29) allocateur d'Upper pour 0x4C1B0 seulement
        FF_[0xCD860] = ('GREFFE',); Greffe2.PAR_APPELANT[0xCD860] = (0x391190, frozenset({0x4C1B0} | set(OBJETS_ALLOC_GARDE)))
        if OBJETS_CLASSES:                           # (e33) classes de decor entieres, liberation et test d'ecran d'Upper
            fc_ = classes_decor_fermeture()[0]
            gc_ = GardePlages(fc_ | {0x4C1B0} | set(OBJETS_ALLOC_GARDE), ((0xFD600, 0x10D0F0), (0x411000, 0x41A000)))
            gc_.cases = classes_decor_cases()
            if CONST_OBJET == "decor":
                Greffe2.CONST_OBJET_GARDE = gc_
                if CONST_OBJET_PLUS:                 # (e34) voir CONST_OBJET_PLUS
                    Greffe2.CONST_OBJET_GARDE = GardePlages(set(gc_) | set(CONST_OBJET_PLUS), gc_.plages)
            n_ = 0
            for r_ in sorted(fc_):
                if FF_.get(r_) != ('GREFFE',): FF_[r_] = ('GREFFE',); n_ += 1
            for f_, h_ in ((0xCD860, 0x391190), (0xCD9A0, 0x3912D0), (0xC6370, 0x38B4C0)):
                FF_[f_] = ('GREFFE',); Greffe2.PAR_APPELANT[f_] = (h_, gc_)
            print("objets de decor : fermeture des classes = %d routines, %d imposees GREFFE" % (len(fc_), n_))
        if OBJETS_ANIM:
            # (e29h) + TOUTES les routines de la fermeture des classes de decor (aides indirectes : f39 plantait encore
            # dans la pose d'Hyper 0x38D4D0 et, par des pointeurs d'animation faux, dans le dessin 0x399E80)
            g_ = GardePlages(set(OBJETS_ANIM_GARDE) | set(OBJETS_ANIM) | (classes_decor_fermeture()[0] if OBJETS_ANIM_FERMETURE else set()),
                             ((0xC8000, 0xC9800),) if OBJETS_ANIM_POSE else ())
            if OBJETS_CLASSES: g_.cases = classes_decor_cases()   # (e33) tables de pointeurs des classes : copies d'Upper
            print("objets de decor : garde de la pose d'Upper = %d routines" % len(g_))
            for f_, h_ in OBJETS_ANIM.items():
                FF_[f_] = ('GREFFE',)
                if h_: Greffe2.PAR_APPELANT[f_] = (h_, g_)
    Pl = PL.ferme(rac + sorted({u for _, u, _, _, _ in TC}), FF_)
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
    # (01/11 soir, e25) JOURNAUX_DEFI=1 : + donnees lues par Upper pendant un NOUVEAU CHALLENGER (lua/donnees_lues3.lua :
    # selection du 2e joueur, victoire 4/8 du combat de defi, reprise) : l'objet $12 sous-type 4 de la victoire (Upper
    # 0x193950, animation 35 de T_D01C60) lisait des frames d'Upper jamais copiees (0x9672EC...) -> plantage du dessin
    if os.environ.get("JOURNAUX_DEFI", "1") == "1": lj += sorted(glob.glob(os.path.join(G, 'traces', 'defi_lu', '*', 'lu.txt')))
    # (e29) OBJETS_JOURNAUX=1 : + lectures d'Upper PENDANT LES MANCHES dans la zone des donnees de decor (PS2 0x950000-
    # 0x9A0000 : animations et images des objets de decor ; lua/donnees_lues_objets.lua, e29/lu_objets_tous.sh : 6 persos
    # couvrant les 30 decors de l'Arcade)
    if OBJETS_DECOR and os.environ.get("OBJETS_JOURNAUX", "1") == "1": lj += sorted(glob.glob(os.path.join(G, 'traces', 'objets_lu', 'lu_*', 'lu.txt')))
    # BORNES : fermeture statique des pointeurs (segments identiques chez Hyper reutilises) ; regions prolongees jusqu'aux
    # lectures d'Upper voisines (tables de decalages) ; DONNEES_LUES=1 : seulement les segments lus par Upper
    Pl.donnees.add(U_PERSO_TABLE)                    # table perso -> index du chargeur par perso (talons d'animation)
    LU_ = D2.lu_ps2(lj) if lj else None
    # (e29) OBJETS_DONNEES=1 : les journaux d'Upper sont pris HORS des manches : les animations des objets de decor
    # atteintes plus tard en combat n'etaient pas copiees (decor $4C, classe $23 : anim 0x96A3B0 -> images 0x96CD66 hors
    # copie, pointeur laisse brut -> dessin d'Hyper 0x399E80 sur des octets d'Hyper, pc $A08). Fermeture STATIQUE depuis les
    # donnees citees par le code des classes de decor (T_611E50, plages 0xFD600-0x10C000 / 0x411000-0x41A000, + 0x4C1B0) :
    # ses cases de pointeurs deviennent des PREUVES (cibles suivies meme non lues, quand leur segment est copie).
    if OBJETS_DECOR and os.environ.get("OBJETS_DONNEES", "1") == "1":
        n0_ = len(D2.PREUVES); D2.PREUVES.update(preuves_objets_decor(D2))
        print("objets de decor : %d cases de pointeurs prouvees en plus" % (len(D2.PREUVES) - n0_))
    if os.environ.get("DONNEES_LUES", "1") == "1":
        FD = D2.Fermeture(Pl.donnees, LU_)
        if D2.R3_CIBLES:                             # (revue_greffe R3) cibles prouvees manquantes : point fixe (4 tours au plus)
            plus_ = set()
            for _t in range(4):
                m_ = D2.cibles_prouvees_manquantes(FD, FD.regions()) - plus_
                if not m_: break
                plus_ |= m_; FD = D2.Fermeture(Pl.donnees, LU_, plus=plus_)
                print("R3_CIBLES tour %d : + %d cibles prouvees (%s)" % (_t + 1, len(m_), ' '.join('%x' % x for x in sorted(m_)[:16])))
            m_ = D2.cibles_prouvees_manquantes(FD, FD.regions())
            if m_: print("R3_CIBLES : %d cibles prouvees ENCORE manquantes (%s)" % (len(m_), ' '.join('%x' % x for x in sorted(m_)[:16])))
    else:                                            # fermeture STATIQUE (tous les pointeurs prouves) ; les lectures
        FD = D2.Fermeture(Pl.donnees, None); FD.lu = LU_   # d'Upper ne servent qu'a prolonger les regions
    synth = []
    # aiguillage de la scene 4 par le mode : ARCADE -> 0x261560 greffee, sinon 0x96620 d'Hyper (VERSUS, TRAINING...)
    synth.append(('scene4_mode', None))
    SYN = [('scene4_mode', stub_arcade([0, 0], [0, 0] if D4_VERSUS else [0])), ('depart_arcade', stub_depart_arcade(0, 0, 0)), ('fin_selection', stub_fin_selection(0, 0)[0])]
    if COMBAT_HYPER:
        SYN += [('ko_compte', stub_arcade([0], [0])),
                ('etat7', stub_si([0], [0], octets=ETAT7_OCTETS, avant=[0] * len(KO_ARCADE))), ('vs_decor', stub_decor(0)),
                ('type14', stub_arcade([0], [0])),
                ('remap_ids', stub_remap_ids(4 if FOND_ARCADE else 0, ((4,) if CARTE_S1 else ()) + (4, 4) if FOND_ARCADE and CARTE_EFFACE else ())), ('plans_auto', stub_plans_auto(4 if COUCHES_UPPER else 0))]
        if PLANS: SYN += [('plans_s%X' % k, stub_plans_scene(4, k == 0xA and DECOR_FIN, (PLANS_S6 if k == 6 else PLANS_S68) if (k == 6 or (k == 8 and not PLANS_GO)) else None, ((4, 4, 4) if DECOR_BOSS_FIN else (4, 4)) if k == 0xA and EFFACE_FIN else (), k == 6 and CONT_S1_MASQUE, k == 6 and CONT_SORTIE)) for k in (6, 8, 0xA)]
        if D4_CHOIX: SYN += [('d4_choix', stub_d4_choix(FEN_DECORS[0]))]
        if D4_CHOIX and D4_VERSUS: SYN += [('d4_vs', stub_d4_vs(FEN_DECORS[0]))]
        if D4_VERSUS and DECORS_UPPER: SYN += [('plans_vs', stub_plans_vs())]
        if DECORS_UPPER and VS_UPPER:
            SYN += [('moteur_plans', stub_moteur([0, 0] if OBJETS_DECOR and OBJETS_PARCOURS else [0], [0], S1_MASQUE, EFFET_12A)), ('moteur_plans_vs', stub_moteur([0], [0], m12a=EFFET_12A)), ('moteur_pal', stub_moteur([0, 0] if PAL_VERSION else [0], [0])),
                    ('moteur_effet', stub_moteur([0], [0]))]
            Greffe2.PAR_APPELANT_SYNTH = {0x151B80: ('moteur_plans_vs', _VS), 0x4B270: ('moteur_pal', _VS)}
            if OBJETS_DECOR:
                SYN += [('moteur_objets', stub_moteur([0], [0]))]; Greffe2.PAR_APPELANT_SYNTH[0x4C1B0] = ('moteur_objets', _VS)
                if OBJETS_MANCHE: SYN += [('objets_manche', stub_moteur([0, 0], [0]))]
        # (e30) talon en DERNIER : les autres talons gardent leurs adresses
        if VICT_PLANS and PLANS: SYN += [('plans_vict', stub_plans_vict(0))]
        if TUILES_E1: SYN += [('tuile_e1', stub_tuile_e1())]   # (e33) en DERNIER
        if TIRAGE_CPU and D4_CHOIX: SYN += [('tirage_1', stub_tirage(0, True)), ('tirage_2', stub_tirage(0, False))]   # (e43) en dernier
        if MUSIQUE_RIVAL: SYN += [('musique_rival', stub_musique_rival())]
        if GARDE_ANIM0: SYN += [('garde_anim0', stub_garde_anim0([0] * 13))]
        if GARDE_LISTE: SYN += [('garde_liste', stub_garde_liste(0))]
        if DAN_SUPER: SYN += [('dan_super', stub_dan_super())]
        if PLANS and CONT_SORTIE: SYN += [('scene2_bases', stub_scene2_bases(4))]   # (e46) en dernier
        if PLANS and CONT_SORTIE and E2B_DEFI: SYN += [('defi_sortie', stub_defi_sortie(4))]   # (ro9a38) en dernier
        if COUL_CPU_VERSION: SYN += [('coul_cpu_%d' % (k_ + 1), stub_coul_cpu(c_, o_)) for k_, (_, c_, o_) in enumerate(U_COUL_SITES)]   # (couleur du CPU) en dernier
        if PORT_VERSION: SYN += [('port_carte', stub_port_carte(0)), ('port_vict', stub_port_vict(0))]   # (portraits) en dernier
    g = Greffe2(routines, Pl.dec, a5, synth=SYN)
    FEN, TROUS = fenetres() if FENETRES else (None, TROU_SON)
    if FENETRES:
        assert all(hi <= ASSET_VBASE or lo >= 0xD60000 for lo, hi, y in FEN), "morceau PS2 sur les fichiers anim"
        assert all((y >= EXT_FIN or y + hi - lo <= 0x940000) and y + hi - lo <= 0xF00000 for lo, hi, y in FEN)
        import donnees2 as D2_
        f547 = (D2_.F547, D2_.F547 + len(D2_.B547))
        assert all(y + hi - lo <= f547[0] or y >= f547[1] for lo, hi, y in FEN), "fenetre 68K sur ext_c84000"
    # (02/11, e26, decision de l'utilisateur) TABLES_DECOR=1 : les tables de decor d'Upper sont COMPLETEES SUR PLACE dans
    # leurs regions du bloc (seules les fins coutent de la place PS2) : bibliotheques s1 (blocs 0x69B830, 119 x $80),
    # super-tuiles s1 (0x69F3B0, 3 081 x $40), blocs s2 / s3 (0x6CF5F0-0x707D10) ; palettes et listes : deja entieres.
    # DECOR_SANS_PTR=1 : ces tables (et les palettes 0x707D10-0x7220CA, les listes 0x747EE0-0x748B94) ne contiennent
    # AUCUN pointeur (indices, codes de tuiles, couleurs, decalages 16 bits) : jamais relogees (e26c : 236 mots « reloges »
    # a tort -> tuiles et couleurs fausses, scroll3 de Rose $12 et de Karin $4C)
    if os.environ.get("TABLES_DECOR", "1") == "1":
        for a_, b_ in ((0x69B830, 0x69F3B0), (0x69F3B0, 0x6CF5F0), (0x6CF5F0, 0x707D10)):
            FD.segments[a_] = max(FD.segments.get(a_, 0), b_ - a_)
    if os.environ.get("DECOR_SANS_PTR", "1") == "1":
        import donnees2 as D2x
        for a_, b_ in ((0x69B830, 0x707D10), (0x707D10, 0x7220CA), (0x747EE0, 0x748B94)):
            D2x.PTR_EXCLUS.update(range(a_, b_, 4))
        # (e27) DECOR_PTR_GARDES (defaut 7097a0-7098e0) : VRAIES tables de pointeurs logees dans ces plages, relogees comme
        # dans ro9a18 : 0x7097A0-0x7098DF = 80 pointeurs de palettes des scenes de FIN (lus par Upper 0x2463A0, 0x2463F4,
        # 0x246EBC, 0x2477A4, 0x308A54, 0x3DDCF4) vers 0x7098E0-0x70DC00 ; laisses bruts dans ro9a19 -> fins de Rose (09)
        # et de Bison (0a) : exception $A08 (lien d'animation 8(A0) faux). Vide -> comme ro9a19.
        for s_ in os.environ.get("DECOR_PTR_GARDES", "7097a0-7098e0").split(','):
            if s_:
                a_, b_ = (int(x_, 16) for x_ in s_.split('-'))
                D2x.PTR_EXCLUS.difference_update(range(a_, b_, 4))
    zone_ = (ZONE_OBJETS[0], ZONE_OBJETS[1], ZONE_TAG | ZONE_CORPS[0]) if ZONE_DECORS else None
    blob, ptr_code, plages = FD.bloc(g, GRF_X, trou=TROUS, zone=zone_); blob = bytearray(blob)
    if ZONE_DECORS:                                   # (e31) corps de la zone : lot 1 a $4E8000 (+ alignement mod 16)
        zl_, zh_, ze_ = FD.zone; zbuf = bytearray(bytes((zl_ & 15)) + bytes(FD.zone_buf))
        # (e31 reprise) OBJETS_SANS_ZONE=<decors hexa> (defaut 14) : comme OBJETS_SANS, dans la ZONE (liste de T_950CE0 du
        # decor videe : 1er mot = $FFFF). Decor $14 : un objet de classe 0 passe a l'animation $1A, hors de la table du
        # decor (9 entrees) -> adresse impaire, erreur d'adresse $9BF10 (rejeux 01 A / 02 A / 07 Z3, combat contre Bison)
        # (e33) defaut VIDE (decision de l utilisateur : objets sur TOUS les decors) ; causes de $12/$14 : OBJETS_CLASSES
        for d_ in [int(x_, 16) for x_ in os.environ.get("OBJETS_SANS_ZONE", "").split(',') if x_]:
            o_ = struct.unpack_from('<h', PL.b5, 0x950CE0 - BASE + d_)[0]; L_ = 0x950CE0 + o_
            k_ = (zl_ & 15) + L_ - zl_
            assert zl_ <= L_ < zh_ and struct.unpack_from('<h', zbuf, k_)[0] >= 0
            struct.pack_into('<H', zbuf, k_, 0xFFFF)
            print("objets de decor : decor %02X sans objets (zone, %x)" % (d_, L_))
        if DECOR_E0: zbuf = recode_decor_e0(zbuf)          # (e46) codes d'objets de décor -> banque e0 prolongée
        zbuf = bytes(zbuf)
        assert ZONE_CORPS[0] + len(zbuf) <= ZONE_CORPS[1], "zone des decors pleine"
        print("zone des decors : Upper %x-%x (%d o) -> 68K $%X-$%X, %d pointeurs de code ; reste %d o" % (zl_, zh_, zh_ - zl_,
              ze_ & 0xFFFFFF, (ze_ & 0xFFFFFF) + zh_ - zl_, len(FD.zone_ptr), ZONE_CORPS[1] - ZONE_CORPS[0] - len(zbuf)))
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
                    ('type14', stub_arcade([X(0x17FD50)], [0x3310F0 + BASE])),
                    ('vs_decor', stub_decor(VS_CIBLE(g))), ('remap_ids', stub_remap_ids(a_exec(g, 0x253A80) if FOND_ARCADE else 0, ((0x38AE50 + BASE,) if CARTE_S1 else ()) + (a_exec(g, 0xC5C10), a_exec(g, 0xC5C60)) if FOND_ARCADE and CARTE_EFFACE else ())), ('plans_auto', stub_plans_auto(a_exec(g, 0x15ACB0) if COUCHES_UPPER else 0))]
        SC = {6: a_exec(g, 0x2614A0), 8: a_exec(g, 0x2614D0), 0xA: a_exec(g, 0x261500)}
        if PLANS: g.synth += [('plans_s%X' % k, stub_plans_scene(SC[k], k == 0xA and DECOR_FIN, (PLANS_S6 if k == 6 else PLANS_S68) if (k == 6 or (k == 8 and not PLANS_GO)) else None, ((a_exec(g, 0x4C1B0), a_exec(g, 0x151B80), a_exec(g, 0x4B270)) if DECOR_BOSS_FIN else (a_exec(g, 0xC5C10), a_exec(g, 0xC5C60))) if k == 0xA and EFFACE_FIN else (), k == 6 and CONT_S1_MASQUE, k == 6 and CONT_SORTIE)) for k in (6, 8, 0xA)]
        if D4_CHOIX: g.synth += [('d4_choix', stub_d4_choix(FEN_DECORS[0]))]
        if D4_CHOIX and D4_VERSUS: g.synth += [('d4_vs', stub_d4_vs(FEN_DECORS[0]))]
        if D4_VERSUS and DECORS_UPPER: g.synth += [('plans_vs', stub_plans_vs())]
        if VICT_PLANS and PLANS: g.synth += [('plans_vict', stub_plans_vict(X(0x26F930)))]
        if TUILES_E1: g.synth += [('tuile_e1', stub_tuile_e1())]
        if TIRAGE_CPU and D4_CHOIX: g.synth += [('tirage_1', stub_tirage(X(0x24F020), True)), ('tirage_2', stub_tirage(X(0x24F020), False))]
        if MUSIQUE_RIVAL: g.synth += [('musique_rival', stub_musique_rival())]
        if GARDE_LISTE: g.synth += [('garde_liste', stub_garde_liste(X(0xC67B0)))]
        if DAN_SUPER: g.synth += [('dan_super', stub_dan_super())]
        if PLANS and CONT_SORTIE: g.synth += [('scene2_bases', stub_scene2_bases(H_SCENE2 + BASE))]   # (e46) en dernier
        if PLANS and CONT_SORTIE and E2B_DEFI: g.synth += [('defi_sortie', stub_defi_sortie(X(U_DEFI_CIBLE)))]   # (ro9a38)
        if COUL_CPU_VERSION: g.synth += [('coul_cpu_%d' % (k_ + 1), stub_coul_cpu(c_, o_)) for k_, (_, c_, o_) in enumerate(U_COUL_SITES)]   # (couleur du CPU)
        if PORT_VERSION: g.synth += [('port_carte', stub_port_carte(X(U_PORT_CARTE))), ('port_vict', stub_port_vict(X(U_PORT_VICT)))]   # (portraits)
        if GARDE_ANIM0: g.synth += [('garde_anim0', stub_garde_anim0(struct.unpack_from('<13I', open(MODULE_SOURCE, 'rb').read(), GA_SITE)))]
        if DECORS_UPPER and VS_UPPER:
            g.synth += [('moteur_plans', stub_moteur([X(0x151B80)] + ([X(0xFD620)] if OBJETS_DECOR and OBJETS_PARCOURS else []), [0x30EC10 + BASE], S1_MASQUE, EFFET_12A)),
                        ('moteur_plans_vs', stub_moteur([X(0x151B80)], [0x30EC10 + BASE], m12a=EFFET_12A)),
                        ('moteur_pal', stub_moteur([X(0x4B270)] + ([H_PAL_JOUEURS + BASE] if PAL_VERSION else []), [0x60A20 + BASE])),   # (PAL_VERSION) + palettes par version
                        ('moteur_effet', stub_moteur([X(0x13BB10)], [0x391E50 + BASE]))]
            if OBJETS_DECOR: g.synth += [('moteur_objets', stub_moteur([X(0x4C1B0)], [0xAC050 + BASE]))]
            if OBJETS_DECOR and OBJETS_MANCHE: g.synth += [('objets_manche', stub_moteur([0xAC050 + BASE, X(0x4C1B0)], [0xAC050 + BASE]))]
        g.synth[0] = ('scene4_mode', stub_arcade([g.synth_place['plans_auto'] + BASE, a_exec(g, 0x261560)], ([g.synth_place['plans_vs'] + BASE] if D4_VERSUS and DECORS_UPPER else []) + [0x96620 + BASE]))
        for nom_, mots_ in g.synth: assert len(mots_) * 4 <= ((4 * len(dict(SYN)[nom_]) + 15) & ~15), nom_
        # sous-table de combat d'Upper copiee : entree 7 (fin de match) -> talon etat7
        e7 = exec_donnee(g, U_T_COMBAT + 4 * 7); o7 = e7 - GRF_X
        assert struct.unpack_from('<I', blob, o7)[0] == X(0x26E900), hex(struct.unpack_from('<I', blob, o7)[0])
        struct.pack_into('<I', blob, o7, g.synth_place['etat7'] + BASE)
        for i_, h_ in enumerate(H_COMBAT):
            v_ = struct.unpack_from('<I', blob, e7 - GRF_X - 28 + 4 * i_)[0]
            if i_ == 1 and os.environ.get("INTERMEDES", "1") == "1": continue   # (28/10) sous-etat 2 = copie d'Upper (force3)
            assert v_ == h_ + BASE, "T_61C2A0[%d] = %x (attendu Hyper %x)" % (i_, v_, h_ + BASE)
        # sous-table de la scene 4/4 d'Upper copiee : entree 1 (ecran VS + decor d'Hyper) -> talon vs_decor
        # (e29) OBJETS_SANS=<decors hexa> : decors d'Upper SANS objets de decor (liste de T_950CE0 videe dans la copie :
        # 1er mot du 1er enregistrement = $FFFF, fin de liste) : decors dont des animations atteintes dans ro9a ne sont
        # jamais lues par Upper (images non copiees)
        if OBJETS_DECOR:
            assert not (ZONE_DECORS and os.environ.get("OBJETS_SANS")), "OBJETS_SANS : listes dans le bloc PS2 seulement (ZONE_DECORS=0)"
            for d_ in [int(x_, 16) for x_ in os.environ.get("OBJETS_SANS", "").split(',') if x_]:
                o_ = struct.unpack_from('<h', PL.b5, 0x950CE0 - BASE + d_)[0]
                e_ = exec_donnee(g, 0x950CE0 + o_) - GRF_X
                assert struct.unpack_from('<h', blob, e_)[0] >= 0
                struct.pack_into('<H', blob, e_, 0xFFFF)
                print("objets de decor : decor %02X sans objets (%x)" % (d_, 0x950CE0 + o_))
        e1 = exec_donnee(g, U_T_VS + 4); o1 = e1 - GRF_X
        assert struct.unpack_from('<I', blob, o1)[0] == VS_CIBLE(g), hex(struct.unpack_from('<I', blob, o1)[0])
        struct.pack_into('<I', blob, o1, g.synth_place['vs_decor'] + BASE)
        # (e30) VICT_PLANS : table de la scene 4 d'Upper copiee : entree 4 (ecran de victoire 0x26F930) -> talon plans_vict
        if VICT_PLANS and PLANS:
            e4 = exec_donnee(g, U_T_SCENE4 + 4 * 4); o4 = e4 - GRF_X
            assert struct.unpack_from('<I', blob, o4)[0] == X(0x26F930), hex(struct.unpack_from('<I', blob, o4)[0])
            struct.pack_into('<I', blob, o4, g.synth_place['plans_vict'] + BASE)
    SITE_PERSO_J1 = g.synth_place['fin_selection'] + 4 * stub_fin_selection(0, 0)[1]
    x2_sites = []
    if X2_TABLES:                                      # (ro9a38, L1 : X2 v2) tables par perso prolongees a X2_N entrees, a la fin du bloc
        assert ZONE_DECORS and FENETRES and TROUS and D4_TABLE, "X2_TABLES : zone des decors et fenetres attendues"
        assert D3, "X2_TABLES : zone $3A0000-$3BFFFF reservee au code MAX (D3=1) attendue"
        src_ = open(MODULE_SOURCE, 'rb').read(); ptr_s = set(ptr_code); zp_s = set(FD.zone_ptr); zl_ = FD.zone[0]
        blob += bytes(-len(blob) & 0xFF); x2_debut_ = len(blob)
        def x2_lieu_(xu_, xhyp_):
            """(adresse d'execution, lit(k, n), est_pointeur(k), (tampon, decalage)) de la table d'Upper xu_ / d'Hyper"""
            if xhyp_: return xu_, (lambda k, n: src_[xu_ - BASE + k:xu_ - BASE + k + n]), (lambda k: False), None
            if zl_ <= xu_ < FD.zone[1]:
                xz_ = (zl_ & 15) + xu_ - zl_
                return (FD.zone[2] + xu_ - zl_, (lambda k, n: zbuf[xz_ + k:xz_ + k + n]),
                        (lambda k: (xu_ - zl_ + k) in zp_s), (zbuf, xz_))
            xa_ = exec_donnee(g, xu_); xb_ = xa_ - GRF_X; assert 0 <= xb_ < len(blob), hex(xa_)
            return xa_, (lambda k, n: blob[xb_ + k:xb_ + k + n]), (lambda k: (xb_ + k) in ptr_s), (blob, xb_)
        def x2_valeurs_(xd_, xlit_):
            """X2_VALEURS -> {entree : octets} (tables 'directes') ; ordre des octets choisi par la colonne ryu = entree 0
            de la table d'Upper (module ro5) : dans le bloc, une entree peut avoir ete relogee
            comme un pointeur (T_615AC0 [0] et [6] : (dx, dy) = $005A0000 / $005EFFE0 pris pour des adresses)"""
            if xd_['valeurs'] != 'directes' or not X2_VALEURS: return {}
            xe_ = xd_['e']
            e0_ = bytes(PL.b5[xd_['u'] - BASE:xd_['u'] - BASE + xe_])   # colonne ryu = valeur d'Upper (meme pour une table d'Hyper partagee)
            f_ = [lambda b: b, lambda b: b''.join(b[i + 1:i + 2] + b[i:i + 1] for i in range(0, len(b), 2)),
                  lambda b: b''.join(b[i:i + 4][::-1] for i in range(0, len(b), 4))]
            ok_ = [f for f in f_ if len(bytes.fromhex(xd_['ryu'])) == xe_ and f(bytes.fromhex(xd_['ryu'])) == e0_]
            out_ = {}
            for id_ in X2_VALEURS:
                h_ = xd_[{0x26: 'v26', 0x27: 'v27', 0x2D: 'v2D', 0x2E: 'v2E'}[id_]]
                r_ = {f(bytes.fromhex(h_)) for f in ok_}
                assert len(r_) == 1 and len(bytes.fromhex(h_)) == xe_, "X2_VALEURS : ordre des octets de T_%x ambigu ou faux (ryu %s, entree 0 %s)" % (xd_['u'], xd_['ryu'], e0_.hex())
                out_[id_] = r_.pop()
            return out_
        def x2_rangee_(xlit_, b_, xe_, vals_):
            """48 entrees d'une rangee de base b_ -> (octets, decalage source de chaque entree ou None)"""
            o_ = bytearray(); s_ = []
            for i_ in range(X2_N):
                v_ = vals_.get(i_)
                o_ += v_ if (v_ is not None and i_ in (0x26, 0x27)) else x2_entree(lambda k, n: xlit_(b_ + k, n), xe_, i_, v_)
                s_.append(None if v_ is not None else b_ + x2_src(xe_, i_))
            return bytes(o_), s_
        for xd_ in x2_liste():
            xu_, xhyp_, xe_, xg_ = xd_['u'], xd_['hyp'], xd_['e'], xd_['genre']
            xa_, xlit_, xptr_, _ = x2_lieu_(xd_['adr'], xhyp_)
            while len(blob) % 16 != (xa_ & 15): blob += b'\0'
            vals_ = x2_valeurs_(xd_, xlit_); xpas_ = None
            if xg_ in ('simple', 'rangs'):             # R rangees de 40 entrees -> R rangees de 48
                xR_ = xd_['R'] if xg_ == 'rangs' else 1; assert xR_ == 1 or xd_['n0'] == X2_N0, hex(xu_)
                xlu_ = (X2_N0 * (xR_ - 1) + max(xd_['n0'], 45)) * xe_
                assert len(xlit_(0, xlu_)) == xlu_, "X2_TABLES : T_%x : %x o illisibles" % (xu_, xlu_)
                xnv_ = GRF_X + len(blob); xc_ = bytearray(); xs_ = []
                for r_ in range(xR_):
                    o_, s_ = x2_rangee_(xlit_, r_ * X2_N0 * xe_, xe_, vals_); xc_ += o_; xs_ += s_
                if xe_ % 4 == 0:
                    for i_, s_ in enumerate(xs_):
                        for k_ in range(0, xe_, 4):
                            if s_ is not None and xptr_(s_ + k_): ptr_code.append(xnv_ - GRF_X + i_ * xe_ + k_)
                blob += xc_; xtaille_ = xd_['n0'] * xe_ * xR_; xpas_ = (X2_N0 * xe_, X2_N * xe_, xR_)
                xtxt_ = "%d rangee(s) de %d x %d o%s" % (xR_, X2_N0, xe_, ', valeurs %s' % ' '.join('%x' % v_ for v_ in sorted(vals_)) if vals_ else '')
            elif xg_ == 'banque':                      # en-tete de decalages vers des groupes de 40 entrees
                xg8_ = X2_N0 * xe_; xd0_ = struct.unpack_from('<h', bytes(xlit_(0, 2)))[0]; xhn_ = xd0_ // 2
                xd_l = list(struct.unpack('<%dh' % xhn_, bytes(xlit_(0, xd0_)))); xs_ = sorted(set(v_ for v_ in xd_l if v_))
                xfin_ = xs_[-1] + xg8_                  # dernier segment : taille inconnue -> traite comme un groupe de 40
                xcorps0_ = bytes(xlit_(0, xfin_ + 5 * xe_)); assert len(xcorps0_) == xfin_ + 5 * xe_ and xs_[0] == xd0_, hex(xu_)
                xnouv_ = {0: 0}; xc_ = bytearray(); xpos_ = xd0_; xng_ = 0
                while xpos_ < xfin_:
                    xsuiv_ = min([v_ for v_ in xs_ if v_ > xpos_] + [xfin_])
                    xnouv_[xpos_] = xd0_ + len(xc_)
                    if xsuiv_ - xpos_ == xg8_:
                        xc_ += x2_rangee_(lambda k, n, p=xpos_: xcorps0_[p + k:p + k + n], 0, xe_, {})[0]; xng_ += 1
                    else: xc_ += xcorps0_[xpos_:xsuiv_]
                    xpos_ = xsuiv_
                xnv_ = GRF_X + len(blob)
                blob += struct.pack('<%dh' % xhn_, *[xnouv_[v_] for v_ in xd_l]) + bytes(xc_)
                assert max(xnouv_.values()) < 0x8000, hex(xu_); xtaille_ = xfin_
                xtxt_ = "banque : %d decalages, %d groupes de %d x %d o prolonges, %x o -> %x o" % (xhn_, xng_, X2_N0, xe_, xfin_, xd0_ + len(xc_))
            elif xg_.startswith('dec:'):              # en-tete de decalages (mots signes relatifs a la table)
                xav_, xap_ = (int(v_, 16) for v_ in xg_.split(':')[1:3]); xh_ = 2 * X2_N0; xp_ = 2 * (X2_N - X2_N0)
                xd_l = struct.unpack('<%dh' % X2_N0, bytes(xlit_(0, xh_)))
                assert xd_l[0] == xh_ and all(v_ >= xh_ or -xav_ <= v_ < 0 for v_ in xd_l) and max(xd_l) + xp_ < 0x8000, hex(xu_)
                xtr_ = lambda v_: v_ + xp_ if v_ >= xh_ else v_
                xmots_ = [struct.unpack('<h', x2_entree(lambda k, n: xlit_(k, n), 2, i_))[0] for i_ in range(X2_N)]
                xavant_ = bytes(xlit_(-xav_, xav_)) if xav_ else b''; xcorps_ = bytes(xlit_(xh_, xap_ - xh_))
                assert len(xavant_) == xav_ and len(xcorps_) == xap_ - xh_, hex(xu_)
                blob += xavant_; xnv_ = GRF_X + len(blob)
                blob += struct.pack('<%dh' % X2_N, *[xtr_(v_) for v_ in xmots_]) + xcorps_; xtaille_ = xap_
                xtxt_ = "en-tete de decalages, %x o avant, %x o de corps" % (xav_, xap_ - xh_)
                if xg_.endswith(':ptr'):               # (L1) table atteinte par des pointeurs de DONNEES (T_614E00[langue])
                    _, _, _, xbo_ = x2_lieu_(0x614E00, False); xb1_ = x2_lieu_(0x614E20, False)[3]
                    assert xbo_ and xb1_ and xbo_[0] is xb1_[0] and xbo_[1] < xb1_[1], "X2_TABLES : T_614E00 / T_614E20"
                    xn_ = 0
                    for o_ in range(xbo_[1], xb1_[1], 4):
                        if struct.unpack_from('<I', xbo_[0], o_)[0] == xa_:
                            struct.pack_into('<I', xbo_[0], o_, xnv_); xn_ += 1
                    assert xn_ >= 1, "X2_TABLES : aucun pointeur de donnees vers T_%x dans T_614E00" % xu_
                    xtxt_ += ", %d pointeur(s) de donnees de T_614E00 rediriges" % xn_
            elif xg_ == '967bf0':                      # en-tete $30, mots x 40 ($30, $80), octets x 40 ($D0, $F8), paires ($120, 16 o)
                assert len(xlit_(0, 0x130)) == 0x130, hex(xu_)
                xnv_ = GRF_X + len(blob); xc_ = bytearray(xlit_(0, 0x30))
                for b_, e_ in ((0x30, 2), (0x80, 2), (0xD0, 1), (0xF8, 1)): xc_ += x2_rangee_(xlit_, b_, e_, {})[0]
                xc_ += xlit_(0x120, 16); assert len(xc_) == 0x160, hex(len(xc_))
                blob += xc_; xtaille_ = 0x130; xtxt_ = "disposition d'agrandit_max ($30, $90, $F0, $120, $150)"
            elif xg_ == 'lignes32':                    # (lot D) 48 lignes de 32 o : lignes $20-$2F = lignes (h & $1F)
                assert len(xlit_(0, X2_N0 * 32)) == X2_N0 * 32, hex(xu_)
                xnv_ = GRF_X + len(blob)
                blob += b''.join(bytes(xlit_(32 * (h_ if h_ < 32 else h_ & 0x1F), 32)) for h_ in range(X2_N))
                xtaille_ = X2_N0 * 32; xtxt_ = "48 lignes de 32 o, lignes $20-$2F = lignes 0-15"
            else: raise AssertionError("X2_TABLES : genre inconnu %s (T_%x)" % (xg_, xu_))
            x2_sites.append(dict(d=xd_, a=xa_, nv=xnv_, taille=xtaille_, pas=xpas_))
            print("X2_TABLES : T_%x (lot %s, %s %x, %s) -> %x (%d entrees ; 40-44 = suite, 45-46 = entree 0, 47 = entree 39)" % (xu_, xd_['lot'], 'Hyper' if xhyp_ else 'copie', xa_, xtxt_, xnv_, X2_N))
        assert GRF_X + len(blob) <= FEN_DECORS[0], "X2_TABLES : bloc sur la fenetre des decors (%x)" % (GRF_X + len(blob))
        assert len(blob) - x2_debut_ <= X2_BUDGET, "X2_TABLES : %x o > budget %x (D6, 112 Ko)" % (len(blob) - x2_debut_, X2_BUDGET)
        assert 0xF18000 <= GRF_X + x2_debut_, "X2_TABLES : debut %x hors de la fenetre $F18000-$FE0000 (68K $410000-$4D7FFF)" % (GRF_X + x2_debut_)
        print("X2_TABLES : %d tables, bloc X2 %d o (budget %d), bloc de donnees %d o, fin %x (fenetre des decors : %x) ; reste %d o avant la fenetre des decors"
              % (len(x2_sites), len(blob) - x2_debut_, X2_BUDGET, len(blob), GRF_X + len(blob), FEN_DECORS[0], FEN_DECORS[0] - GRF_X - len(blob)))
    T_D4 = None
    if FENETRES and TROUS and D4_TABLE:                   # fenetre des decors (T1b) : table D4 en tete
        assert GRF_X + len(blob) <= FEN_DECORS[0], "bloc de donnees sur la fenetre des decors (%x)" % (GRF_X + len(blob))
        blob += bytes(FEN_DECORS[0] - GRF_X - len(blob)); T_D4 = GRF_X + len(blob); blob += table_d4()
        if ZONE_DECORS:                               # (e31) repertoire de la zone apres la table D4
            assert len(blob) == FEN_DECORS[0] - GRF_X + ZONE_REP
            blob += zone_repertoire([(1, 0, ZONE_TAG | ZONE_CORPS[0], len(zbuf), FD.zone[0] - (FD.zone[0] & 15))],
                                    ZONE_TAG | (ZONE_CORPS[0] + ((len(zbuf) + 0xFF) & ~0xFF)))
        if TIRAGE_CPU and D4_CHOIX:                    # (e43) tables du tirage : PS2 $FE1000 = 68K $4D9000
            assert len(blob) <= FEN_DECORS[0] - GRF_X + TIR_OFF, hex(len(blob))
            blob += bytes(FEN_DECORS[0] - GRF_X + TIR_OFF - len(blob))
            for t_ in tables_tirage(): blob += t_
            assert GRF_X + len(blob) == (_adr_tm(len(TIR_CHAMPS) + 1) if TIRAGE_MODES else _adr_tir(3) + 128) and GRF_X + len(blob) <= FEN_DECORS[1]
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
    if x2_sites:                                       # (ro9a38, L1 : X2 v2) constantes lui/addiu des tables -> copies prolongees
        xpl_ = sorted((n_, n_ + b_ - a_) for a_, b_, n_ in g.place)   # code d'Upper copie (fichier du module)
        xall_ = collections.defaultdict(list)         # toutes les constantes lui/addiu adjacentes (meme registre) des copies
        for xd0_, xd1_ in xpl_:
            for xc_ in range(xd0_, xd1_ - 4, 4):
                xw1_, xw2_ = struct.unpack_from('<II', mod, xc_)
                if (xw1_ >> 26) == 0x0f and (xw2_ >> 26) == 0x09 and ((xw1_ >> 16) & 31) == ((xw2_ >> 21) & 31) == ((xw2_ >> 16) & 31):
                    xval_ = (((xw1_ & 0xffff) << 16) + ((xw2_ & 0xffff) - (0x10000 if xw2_ & 0x8000 else 0))) & 0xffffffff
                    xall_[xval_].append(xc_)
        xdebuts_ = {s_['a'] for s_ in x2_sites}
        def x2_instr_(kind_, site_, old_, new_, xu_):
            """(L1) constante de rangee / masque / decalage : l'unique instruction de la forme attendue a +-$10 du site"""
            xn_ = g.neuf(site_); assert xn_ is not None, "X2_TABLES : site %x non copie (T_%x)" % (site_, xu_)
            xk_ = []
            for o_ in range(xn_ - 0x10, xn_ + 0x14, 4):
                w_ = struct.unpack_from('<I', mod, o_)[0]; op_ = w_ >> 26; rs_ = (w_ >> 21) & 31; im_ = w_ & 0xffff
                ok_ = {'addiu': op_ == 0x09 and rs_ != 0 and im_ == old_,
                       'imm': op_ in (0x09, 0x0d) and rs_ == 0 and im_ == old_,
                       'dep': (op_ == 0x09 and rs_ != 0 or op_ in (0x20, 0x21, 0x23, 0x24, 0x25)) and im_ == old_,
                       'andi': op_ == 0x0c and im_ == old_,
                       'sll': w_ != 0 and (w_ & 0xFC00003F) == 0 and ((w_ >> 6) & 31) == old_}[kind_]
                if ok_: xk_.append(o_)
            assert len(xk_) == 1, "X2_TABLES : T_%x : %s $%X en Upper %x : %d candidat(s) a +-$10" % (xu_, kind_, old_, site_, len(xk_))
            o_ = xk_[0]; w_ = struct.unpack_from('<I', mod, o_)[0]
            w2_ = (w_ & ~(31 << 6)) | (new_ << 6) if kind_ == 'sll' else (w_ & 0xffff0000) | new_
            struct.pack_into('<I', mod, o_, w2_)
            patchs.append(dict(type='mips', site=hex(o_ + BASE), quoi="X2_TABLES : Upper 0x%X (%x) %s $%X -> $%X (T_%x)" % (site_, o_ - xn_ + site_, kind_, old_, new_, xu_)))
            print("X2_TABLES : T_%x : %s $%X -> $%X en %x (Upper 0x%X)" % (xu_, kind_, old_, new_, o_, o_ - xn_ + site_))
        for s_ in x2_sites:
            xd_ = s_['d']; xu_, xa_, xnv_ = xd_['u'], s_['a'], s_['nv']; xvu_ = list(xall_.get(xa_, ())); xpris_ = []
            for xus_ in xd_['sites']:                  # les acces releves par l'inventaire / la sonde : constante trouvee avant eux
                xn_ = g.neuf(xus_); xc0_ = [c_ for c_ in xvu_ if xn_ - 0x600 < c_ < (xn_ or 0)]
                assert xn_ is not None and xc0_, "X2_TABLES : constante %x introuvable avant %x (Upper %x)" % (xa_, xn_ or 0, xus_)
                xpris_.append(max(xc0_))
            if not xd_['tous']: xvu_ = sorted(set(xpris_))   # lecteurs listes seulement
            for k_ in xd_['consts']: x2_instr_(*k_, xu_)
            for xc_ in xvu_:
                const_(xc_, xnv_, "X2_TABLES : T_%x (%x) -> copie prolongee %x (%d entrees), lecteur copie d'Upper" % (xu_, xa_, xnv_, X2_N))
            xint_ = []
            if xd_['tous']:                            # (L1) constantes interieures ]T, T + taille[
                for xv_, xcs_ in sorted(xall_.items()):
                    if not (xa_ < xv_ < xa_ + s_['taille']) or xv_ in xdebuts_: continue
                    if xv_ in xd_['gardes']:
                        print("X2_TABLES : ATTENTION T_%x : constante interieure %x (T + $%X) gardee en %s (x2_tables.tsv : garde)" % (xu_, xv_, xv_ - xa_, ' '.join('%x' % c_ for c_ in xcs_)))
                        continue
                    xdl_ = xv_ - xa_; xpas_ = s_['pas']
                    xhd_ = 2 * X2_N0 if xd_['genre'].startswith('dec:') else (struct.unpack('<h', bytes(x2_lieu_(xd_['adr'], xd_['hyp'])[1](0, 2)))[0] if xd_['genre'] == 'banque' else None)
                    if xhd_ is not None and xdl_ >= xhd_:   # pointeur dans le CORPS d'origine (reste en place, inchange) : garde
                        print("X2_TABLES : ATTENTION T_%x : constante interieure %x (T + $%X, corps) gardee en %s (lit le corps d'origine, inchange)" % (xu_, xv_, xdl_, ' '.join('%x' % c_ for c_ in xcs_)))
                        continue
                    if xdl_ < xd_['e'] and xd_['genre'] in ('simple', 'rangs'): xcib_ = xnv_ + xdl_
                    elif xpas_ and xdl_ % xpas_[0] == 0 and xdl_ // xpas_[0] < xpas_[2]: xcib_ = xnv_ + xdl_ // xpas_[0] * xpas_[1]
                    else: raise AssertionError("X2_TABLES : T_%x : constante interieure %x (T + $%X) en %s : non traitee" % (xu_, xv_, xdl_, ' '.join('%x' % c_ for c_ in xcs_)))
                    for xc_ in xcs_:
                        const_(xc_, xcib_, "X2_TABLES : T_%x + $%X -> %x (constante interieure)" % (xu_, xdl_, xcib_)); xint_.append(xc_)
                    print("X2_TABLES : ATTENTION T_%x : constante interieure %x (T + $%X) -> %x en %s" % (xu_, xv_, xdl_, xcib_, ' '.join('%x' % c_ for c_ in xcs_)))
            print("X2_TABLES : T_%x : %d constante(s) redirigee(s) (%s)%s" % (xu_, len(xvu_), ' '.join('%x' % c_ for c_ in xvu_), ', %d interieure(s)' % len(xint_) if xint_ else ''))
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
    if COMBAT_HYPER and PLANS and CONT_SORTIE:          # (e46) scene A5+4 = 2 : bases d'Hyper en ARCADE (apres CONTINUE)
        assert struct.unpack_from('<I', mod, 0x5B5E84 - BASE)[0] == H_SCENE2 + BASE
        long_(0x5B5E84, g.synth_place['scene2_bases'] + BASE, "scene A5+4=2 (selection d'Hyper) : ARCADE -> bases de plans d'Hyper puis Hyper 0x%X" % H_SCENE2)
        if E2B_DEFI:                                   # (ro9a38) sortie « challenger accepte » de la copie u1353A0
            n_ = g.neuf(U_DEFI_JSR); w_ = struct.unpack_from('<I', mod, n_)[0]
            assert (w_ >> 26) == 3 and ((w_ & 0x3ffffff) << 2) == a_exec(g, U_DEFI_CIBLE), (hex(n_), hex(w_))
            jal_(n_, g.synth_place['defi_sortie'] + BASE, "Upper 0x%X (u1353A0, defi accepte) : JSR 0x%X -> talon defi_sortie (couches masquees, bases d'Hyper retardees de %d images)" % (U_DEFI_JSR, U_DEFI_CIBLE, DEFI_N))
    if COMBAT_HYPER and COUL_CPU_VERSION:              # (couleur du CPU) JSR de la copie 0x262930 apres la pose de $129 du CPU
        for k_, (us_, c_, o_) in enumerate(U_COUL_SITES):
            n_ = g.neuf(us_); assert n_ is not None, hex(us_)
            w_ = struct.unpack_from('<I', mod, n_)[0]; p_ = g.synth_place['coul_cpu_%d' % (k_ + 1)] + 4 * COUL_JAL
            assert (w_ >> 26) == 3 and struct.unpack_from('<I', mod, p_)[0] == j_(3, 0), (hex(n_), hex(w_))
            struct.pack_into('<I', mod, p_, w_)       # JSR d'origine (homologue d'Hyper de 0x263820) dans le talon
            jal_(n_, g.synth_place['coul_cpu_%d' % (k_ + 1)] + BASE, "Upper 0x%X (copie de 0x262930, couleur du CPU J%d) : JSR 0x%X -> talon coul_cpu_%d (version non de base : $129 = 0, miroir exact : %d)" % (us_, c_ // 0x400, (w_ & 0x3ffffff) << 2, k_ + 1, COUL_MIROIR))
    if COMBAT_HYPER and PORT_VERSION:                  # (portraits) chargeurs de portraits d'Upper -> talons port_carte / port_vict
        np_ = 0
        for us_ in U_PORT_CARTE_SITES:
            n_ = g.neuf(us_)
            if n_ is None: continue                    # appelant non greffe
            const_(n_, g.synth_place['port_carte'] + BASE, "PORT_VERSION : Upper 0x%X : appel de 0x%X (portrait de carte, A4 = joueur) -> talon port_carte (version : couleur %d)" % (us_, U_PORT_CARTE, PORT_COUL))
            assert int(patchs[-1]['avant'], 16) == a_exec(g, U_PORT_CARTE), patchs[-1]['avant']
            np_ += 1
        assert np_ >= 2, np_
        n_ = g.neuf(U_PORT_VICT_SITE); w_ = struct.unpack_from('<I', mod, n_)[0]
        assert (w_ >> 26) == 3 and ((w_ & 0x3ffffff) << 2) == a_exec(g, U_PORT_VICT), (hex(n_), hex(w_))
        jal_(n_, g.synth_place['port_vict'] + BASE, "PORT_VERSION : Upper 0x%X : JSR 0x%X (portrait de victoire, A4 = joueur) -> talon port_vict (version : couleur %d)" % (U_PORT_VICT_SITE, U_PORT_VICT, PORT_COUL))
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
    # (31/10, retour 2 de l'utilisateur sur ro9a11 : picto « AUTO » sous la barre de J1) CHAMP_POSE=1 : l'octet 68K $119
    # du joueur est, dans Upper (et SFA3), le type d'entree en scene (2 ; $1A / $1C : Upper 0x24BCC0), mais dans Hyper le
    # choix MANUAL / AUTO de la selection (0x31B54C) : le code greffe ecrivait 2 -> garde AUTO affichee (et active). Les
    # acces JOUEUR d'Upper a $119 (ecritures 0x24BF1C, 0x1355B8, 0x260DA0 ; lectures 0x134DFC, 0x134EC4) passent a l'octet
    # $30D (decalage MIPS $30C, jamais adresse dans Upper ni Hyper) ; 0x13B8DC ($119(A5)) est garde.
    # (31/10, retour 8 : meme musique (theme de J1) a tous les combats) MUSIQUE_J2=1 : choix de la musique d'Hyper
    # 0x3890D0 (68K : LEA $400(A5),A4 ; CMPI.B #1 / #4,$C201 -> hasard ; sinon TST.B $C3B5 : 0 -> J1, > 0 -> J2). Notre
    # Arcade a $C201 = 0 et $C3B5 = 0 : toujours J1. Le BEQ de 0x3892F4 ($C3B5 = 0) va maintenant a A4 = J2 (0x389360),
    # l'adversaire CPU comme dans Upper. VERSUS ($C201 = 1) et TRAINING (4) ne passent pas par ce branchement.
    # (31/10, retours 3 et 4) TYPE14=1 : objets de type 14 (table des types T_5C5720, homologue d'Upper T_615100) : Upper
    # 0x17FD50 (portraits des intermedes, fenetre du regard) contre Hyper 0x3310F0 (autre objet au meme numero) ; en
    # ARCADE (drapeau $FE00) la copie d'Upper, sinon Hyper : les portraits etaient entiers et jamais liberes
    if COMBAT_HYPER and TYPE14:
        long_(0x5C5758, g.synth_place['type14'] + BASE, "table des types d'objets T_5C5720[14] : ARCADE -> Upper 0x17FD50 (portraits d'intermede), sinon Hyper 0x3310F0")
        assert int(patchs[-1]['avant'], 16) == 0x3310F0 + BASE, patchs[-1]['avant']
    if COMBAT_HYPER and DECORS_UPPER and VS_UPPER:
        const_(0x9A8E8, g.synth_place['moteur_plans'] + BASE, "combat d'Hyper 0x9A6F0 : JSR 0x30EC10 (plans) -> talon moteur_plans (decor d'Upper : copie de 0x151B80)")
        assert int(patchs[-1]['avant'], 16) == 0x30EC10 + BASE, patchs[-1]['avant']
        # (e26) autres appels d'Hyper au moteur de decor (constantes lui/addiu) : reprise de manche 0x9EB30 (0x9FFEC palettes,
        # 0x9FFFC plans : plantage pc $A08 a la fin de la 1re manche, table de palettes d'Hyper lue a $100 = $32), challenger
        # 0x9A570, VS d'Hyper 0x9A430, 0x3BCE50 ; le drapeau $FE00 laisse le VERSUS et l'attraction a Hyper
        # (e29) OBJETS_MANCHE : le reservoir $FFC000 est remis a zero entre les manches ; la reprise de manche d'Hyper
        # (0x9FFxx : JSR 0xAC050, HUD) et le VS d'Hyper 0x9A430 (VERSUS) -> talon objets_manche : 0xAC050, puis sur decor
        # d'Upper (Arcade ou VERSUS D4) la copie de 0x4C1B0 (objets de decor de T_950CE0)
        if OBJETS_DECOR and OBJETS_MANCHE:
            for f9_ in (0xA000C, 0x9A4C0):
                const_(f9_, g.synth_place['objets_manche'] + BASE, "appel d'Hyper 0xAC050 (HUD) -> talon objets_manche (+ objets de decor d'Upper)")
                assert int(patchs[-1]['avant'], 16) == 0xAC050 + BASE, patchs[-1]['avant']
        for f9_, h_, nom_ in ((0x9FFEC, 0x60A20, 'moteur_pal'), (0x9FFFC, 0x30EC10, 'moteur_plans_vs'), (0x9A650, 0x30EC10, 'moteur_plans_vs'),
                              (0x9A4D0, 0x30EC10, 'moteur_plans_vs'), (0x9A4E0, 0x60A20, 'moteur_pal'), (0x3BCF80, 0x60A20, 'moteur_pal')):
            const_(f9_, g.synth_place[nom_] + BASE, "appel d'Hyper 0x%X -> talon %s (decor d'Upper : copie d'Upper)" % (h_, nom_))
            assert int(patchs[-1]['avant'], 16) == h_ + BASE, patchs[-1]['avant']
        # (e26) EFFET PAR DECOR (objet d'Hyper : table d'etats 0x3D9E20, etat 2 = 0x391E50, aussi JMP depuis l'init 0x391E38) :
        # $C174 / $C176 et gestionnaire par T_5C9E00/08/30 (4 entrees) -> sur un decor d'Upper, copie d'Upper 0x13BB10
        # (T_6134E0 / T_613530 / T_6135A0, 40 entrees) ; e26e : palettes de Gen ($22) toutes blanches
        jal_(0x391E38, g.synth_place['moteur_effet'] + BASE, "objet d'effet de decor d'Hyper 0x391DD0 : JMP 0x391E50 -> talon moteur_effet")
        long_(0x3D9E24 + BASE, g.synth_place['moteur_effet'] + BASE, "table d'etats de l'objet d'effet de decor (etat 2 = 0x391E50) -> talon moteur_effet")
        assert int(patchs[-1]['avant'], 16) == 0x391E50 + BASE, patchs[-1]['avant']
    # (e30) INDIC_UPPER : indicateurs « PRESS START » (Hyper 0x10E4 -> 0x1134) en codes de la table plan2 prolongee
    if INDIC_UPPER:
        n_ = g.neuf(0x29CA4); assert n_ is not None
        w = struct.unpack_from('<I', mod, n_)[0]; assert w == 0x24641C00, hex(w)
        struct.pack_into('<I', mod, n_, (w & 0xffff0000) | (0x1C00 + PLAN2_UPPER_DEBUT))
        patchs.append(dict(type='immediat', site=hex(n_ + BASE), avant='0x1c00', apres=hex(0x1C00 + PLAN2_UPPER_DEBUT), quoi="indicateurs PRESS START (copie d'Upper 0x29CA4, 68K Upper $1A40) : codes +$5B00 -> plans d'Upper (plan2 prolongee)"))
    # (e46, ro9a36 : « petit carre » apres « CONTINUE? ») CONT_CHIFFRE=1 : le chiffre du decompte a cote de « CONTINUE? »
    # est pose dans le tampon d'objets fixes $71B8(A5) par la copie d'Upper 0x136F80 (ADDI.W #$26F5,D2 : code e1 = $26F5 +
    # $10C du joueur ; Upper 0x13708C « addiu a0,v1,$26F5 », 68K ro9a35b $0A1A3E) : code des plans d'UPPER, lu dans la
    # table plan2 d'Hyper -> morceau d'image d'Hyper. Comme INDIC_UPPER : +$26F5 -> +$81F5 (plan2 prolongee). =0 : ro9a35b.
    if INDIC_UPPER and os.environ.get("CONT_CHIFFRE", "0") == "1":
        n_ = g.neuf(0x13708C); assert n_ is not None
        w = struct.unpack_from('<I', mod, n_)[0]; assert w == 0x246426F5, hex(w)
        struct.pack_into('<I', mod, n_, (w & 0xffff0000) | (0x26F5 + PLAN2_UPPER_DEBUT))
        patchs.append(dict(type='immediat', site=hex(n_ + BASE), avant='0x26f5', apres=hex(0x26F5 + PLAN2_UPPER_DEBUT), quoi="chiffre du decompte du CONTINUE (copie d'Upper 0x13708C) : code e1 +$5B00 -> plans d'Upper (plan2 prolongee)"))
    # (e34) RANG_E1 : pictogrammes en haut a gauche du GAME OVER = libelle du CLASSEMENT d'Upper (« 1st A__ » : rang et
    # initiales, routine d'Upper 0x95010 et voisines, bloc 0x92D50-0x96A40, copies) pose dans le tampon d'objets fixes
    # $79C4(A5) en codes de l'emplacement 1 « T + $1C00 » (plans d'Upper) : dans ro9a la table plan2 est celle d'Hyper sous
    # $5B00 -> morceaux d'images d'Hyper. Comme INDIC_UPPER : +$1C00 -> +$7700 (plan2 prolongee : tuiles d'Upper).
    if INDIC_UPPER and RANG_E1:
        for va_ in RANG_E1_SITES:
            n0_ = g.neuf(va_); assert n0_ is not None, hex(va_)
            c_ = [n0_ + 4 * i for i in range(-4, 8) if (struct.unpack_from('<I', mod, n0_ + 4 * i)[0] >> 26) == 0x09
                  and (struct.unpack_from('<I', mod, n0_ + 4 * i)[0] & 0xffff) == 0x1C00]
            assert len(c_) == 1, (hex(va_), [hex(x) for x in c_])
            w = struct.unpack_from('<I', mod, c_[0])[0]
            struct.pack_into('<I', mod, c_[0], (w & 0xffff0000) | (0x1C00 + PLAN2_UPPER_DEBUT))
            patchs.append(dict(type='immediat', site=hex(c_[0] + BASE), avant='0x1c00', apres=hex(0x1C00 + PLAN2_UPPER_DEBUT), quoi="libelle du classement (copie d'Upper 0x%X) : codes e1 +$5B00 -> plans d'Upper (plan2 prolongee)" % va_))
    if os.environ.get("MUSIQUE_J2", "1") == "1":
        w = struct.unpack_from('<I', mod, 0x3892F4)[0]; assert w == 0x1060001F, hex(w)
        struct.pack_into('<I', mod, 0x3892F4, 0x10600000 | ((0x389360 - 0x3892F8) >> 2))
        patchs.append(dict(type='branchement', site=hex(0x3892F4 + BASE), avant=hex(w), apres='0x1060001a', quoi="musique du combat hors VERSUS / TRAINING : J2 (adversaire) au lieu de J1"))
    if GARDE_LISTE:                                     # (e43) pas d'ajout a la liste d'affichage d'un acteur de fin sans anim
        E5_ = PL.E5; cib_ = a_exec(g, 0xC67B0); ng_ = 0
        for r_ in GARDE_LISTE_R:
            assert r_ in E5_ and g.neuf(r_) is not None, hex(r_)
            for va_ in range(r_, E5_[r_], 4):
                n_ = g.neuf(va_)
                if n_ is None: continue
                w_, w2_ = struct.unpack_from('<II', mod, n_)
                if (w_ >> 26) == 3 and ((w_ & 0x3ffffff) << 2) == cib_:
                    struct.pack_into('<I', mod, n_, j_(3, g.synth_place['garde_liste'] + BASE)); ng_ += 1
                    patchs.append(dict(type='jal', site=hex(n_ + BASE), quoi="Upper 0x%X : JSR 0xC67B0 (liste d'affichage) -> talon garde_liste (rien si $1C(A6) = 0)" % va_))
                elif (w_ >> 26) == 0x0f and (w2_ >> 26) == 0x09 and (w_ & 0x001f0000) == (w2_ & 0x001f0000) and \
                        ((((w_ & 0xffff) << 16) + ((w2_ & 0xffff) - (0x10000 if w2_ & 0x8000 else 0))) & 0xffffffff) == cib_:
                    c_ = g.synth_place['garde_liste'] + BASE                           # (lui/addiu/jalr du recompilateur)
                    struct.pack_into('<II', mod, n_, (w_ & 0xffff0000) | (((c_ + 0x8000) >> 16) & 0xffff), (w2_ & 0xffff0000) | (c_ & 0xffff)); ng_ += 1
                    patchs.append(dict(type='constante', site=hex(n_ + BASE), quoi="Upper 0x%X : JSR 0xC67B0 (liste d'affichage, lui/addiu/jalr) -> talon garde_liste (rien si $1C(A6) = 0)" % va_))
        assert ng_ > 0
        print("garde_liste : %d appels" % ng_)
    if DAN_SUPER:                                       # (e45) super de Dan : chemin ZERO revu apres l'ajustement du niveau
        av4 = struct.unpack_from('<4I', mod, DS_SITE)
        assert av4 == DS_AVANT, [hex(x) for x in av4]
        struct.pack_into('<4I', mod, DS_SITE, j_(3, g.synth_place['dan_super'] + BASE), 0, 0, 0)
        patchs.append(dict(type='mips', site=hex(DS_SITE + BASE), quoi="Hyper (Dan, super) : JSR 0x514A70 -> talon dan_super (niveau ramene a 0 -> chemin $1E)"))
    if GARDE_ANIM0:                                     # (e43) pas de dessin d'un acteur sans animation
        av13 = struct.unpack_from('<13I', mod, GA_SITE)
        assert av13[1] == 0x8c421118 and av13[2] == 0x8c43001c and av13[11] == 0x0c160f50, [hex(x) for x in av13]
        struct.pack_into('<13I', mod, GA_SITE, j_(3, g.synth_place['garde_anim0'] + BASE), *([0] * 12))
        patchs.append(dict(type='mips', site=hex(GA_SITE + BASE), quoi="dessin d'un acteur (Hyper 0x393CD0) : MOVEA.L $1C(A6),A0 ... JSR 0x583D40 -> talon garde_anim0 (rien si $1C = 0)"))
    if MUSIQUE_RIVAL:                                   # (e43) themes speciaux d'Upper (rival, combat final) si J1 et J2 en ZERO 3
        assert struct.unpack_from('<4I', mod, MUS_SITE) == MUS_AVANT, [hex(x) for x in struct.unpack_from('<4I', mod, MUS_SITE)]
        struct.pack_into('<4I', mod, MUS_SITE, j_(3, g.synth_place['musique_rival'] + BASE), 0, 0, 0)
        patchs.append(dict(type='mips', site=hex(MUS_SITE + BASE), quoi="choix de musique d'Hyper 0x3890D0 : TST.W $C3B6 -> talon musique_rival (Arcade, J1 et J2 en ZERO 3 : themes speciaux d'Upper)"))
    if os.environ.get("CHAMP_POSE", "1") == "1":
        for va_ in (0x24BF1C, 0x1355B8, 0x260DA0, 0x134DFC, 0x134EC4):
            n_ = g.neuf(va_)
            if n_ is None: continue
            w = struct.unpack_from('<I', mod, n_)[0]; assert (w & 0xffff) == 0x118, hex(va_)
            struct.pack_into('<I', mod, n_, (w & 0xffff0000) | 0x30C)
            patchs.append(dict(type='champ', site=hex(n_ + BASE), avant='0x118', apres='0x30c', quoi="Upper 0x%X : $119 du joueur (entree en scene) -> $30D (Hyper : MANUAL/AUTO)" % va_))
    # (01/11, ro9a17) CHAMP_POSE_A5=1 : meme champ ecrit PAR LA BASE A5 a la reprise apres un CONTINUE accepte (Upper
    # 0x26B0B0, 68K MOVE.B #2,$0519(A5) / $0919(A5) = « addiu v1,v1,$518 / $918 ; sb a0,0(v1) » en 0x26B768 / 0x26B77C) :
    # picto « AUTO » sous la vie de J1 apres un CONTINUE (vu sur ro9a15/16 : ecriture PC $0B7730 a l'image 4245)
    if os.environ.get("CHAMP_POSE", "1") == "1" and os.environ.get("CHAMP_POSE_A5", "1") == "1":
        for va_, av_, ap_ in ((0x26B768, 0x518, 0x70C), (0x26B77C, 0x918, 0xB0C)):
            n_ = g.neuf(va_)
            if n_ is None: continue
            w = struct.unpack_from('<I', mod, n_)[0]; assert (w & 0xffff) == av_ and (w >> 26) == 9, hex(va_)
            struct.pack_into('<I', mod, n_, (w & 0xffff0000) | ap_)
            patchs.append(dict(type='champ', site=hex(n_ + BASE), avant=hex(av_), apres=hex(ap_), quoi="Upper 0x%X : $%X(A5) (entree en scene apres CONTINUE) -> $%X(A5)" % (va_, av_ + 1, ap_ + 1)))
    # (01/11, ro9a17, decors etape 1) D4_TABLE=1 : NOUVEAU CHALLENGER (copie d'Upper 0x258450) : $100 = 2 x $103 de J2
    # (MOVEQ #0,D0 ; MOVE.B $103(A6),D0 ; ADD.W D0,D0 ; MOVE.W D0,$100(A5)) -> $100 = D4[$103] (id ETENDU : la lecture
    # 0x258620, passee a $117 par TOUT_116, revient a $103) ; ADD.W D0,D0 (6 mots 0x258630-0x258644) remplace par
    # MOVE.B T_D4(D0.W),D0 dans la forme du recompilateur (Upper 0x251978 : lui/addiu/addu/lb 0) ; D0 = $000000xx.
    if T_D4 is not None:
        b5_ = C.load('ro5')
        av6 = struct.unpack_from('<6I', b5_, 0x258630)
        assert av6 == (0x84431124, 0x3c027000, 0x84421124, 0x00621821, 0x3c027000, 0xa4431124), [hex(x) for x in av6]
        n0 = g.neuf(0x258620); w0 = struct.unpack_from('<I', mod, n0)[0]
        assert (w0 >> 16) == 0x8043 and (w0 & 0xffff) in (0x102, 0x116), hex(w0)
        struct.pack_into('<I', mod, n0, 0x80430102)
        n_ = g.neuf(0x258630); assert struct.unpack_from('<6I', mod, n_) == av6
        struct.pack_into('<6I', mod, n_, 0x84441124, 0x3c030000 | (((T_D4 + 0x8000) >> 16) & 0xffff),
                         0x24630000 | (T_D4 & 0xffff), 0x00831821, 0x80640000, 0xa0441124)
        patchs.append(dict(type='mips', site=hex(n0 + BASE), quoi="nouveau challenger 0x258620 : MOVE.B $103(A6),D0 (id etendu, au lieu de $117)"))
        patchs.append(dict(type='mips', site=hex(n_ + BASE), quoi="nouveau challenger 0x258630 : ADD.W D0,D0 -> MOVE.B T_D4(D0.W),D0 (table D4 PS2 %#x, T1b $4D8000)" % T_D4))
    if T_D4 is not None and D4_CHOIX:
        assert T_D4 == FEN_DECORS[0], hex(T_D4)
        # lectures MOVE.B $0103(A1),D0 juste avant JSR 0x24F020 : 0x24EFD8 (0x24EA30 : 1er adversaire, defi) et 0x2512D4
        # (0x250EF0 : adversaire suivant apres une victoire ; avant : decor de l'adversaire PRECEDENT)
        for va_ in (0x24EFD8, 0x2512D4):
            n_ = g.neuf(va_); w = struct.unpack_from('<I', mod, n_)[0]; assert w == 0x80430116, (hex(va_), hex(w))
            struct.pack_into('<I', mod, n_, 0x80430102)
            patchs.append(dict(type='champ', site=hex(n_ + BASE), avant='0x116', apres='0x102', quoi="Upper 0x%X : $103 de A1 (id etendu, ecrit juste avant) au lieu de $117 (perime) avant 0x24F020" % va_))
        n_ = g.neuf(0x24F2BC); w = struct.unpack_from('<I', mod, n_)[0]; assert (w >> 26) == 3, hex(w)
        struct.pack_into('<I', mod, n_, j_(3, g.synth_place['d4_choix'] + BASE))
        patchs.append(dict(type='jal', site=hex(n_ + BASE), avant=hex((w & 0x3ffffff) << 2), apres=hex(g.synth_place['d4_choix'] + BASE), quoi="Upper 0x24F2BC : JSR 0x251950 (T_61BE10) -> talon d4_choix (table D4)"))
        n_ = g.neuf(0x24F2C8); av7 = struct.unpack_from('<7I', mod, n_)
        assert av7 == (0x3c037000, 0x84641124, 0x3c037000, 0x84631124, 0x00832021, 0x3c037000, 0xa4641124), [hex(x) for x in av7]
        struct.pack_into('<7I', mod, n_, *([0] * 7))
        patchs.append(dict(type='mips', site=hex(n_ + BASE), quoi="Upper 0x24F2C8 : ADD.W D0,D0 -> rien (D4 deja doublee)"))
        av7 = struct.unpack_from('<7I', mod, 0x31D87C)
        assert av7 == (0x3c027000, 0x84431124, 0x3c027000, 0x84421124, 0x00621821, 0x3c027000, 0xa4431124), [hex(x) for x in av7]
        struct.pack_into('<7I', mod, 0x31D87C, 0x3c027000, 0x84441124, 0x3c030000 | (((T_D4 + 0x8000) >> 16) & 0xffff),
                         0x24630000 | (T_D4 & 0xffff), 0x00831821, 0x80640000, 0xa0441124)
        patchs.append(dict(type='mips', site=hex(0x31D87C + BASE), quoi="Hyper 0x31D880 (arrivee du challenger) : ADD.W D0,D0 -> MOVE.B T_D4(D0.W),D0"))
        if TIRAGE_CPU:                                  # (e43) talons du tirage de la version des CPU
            for k_, va_ in enumerate(TIR_SITES):
                n_ = g.neuf(va_); av5 = struct.unpack_from('<7I', mod, n_)
                assert av5[:5] == TIR_AVANT and (av5[5] >> 26) == 3 and av5[6] == 0, (hex(va_), [hex(x) for x in av5])
                assert ((av5[5] & 0x3ffffff) << 2) == a_exec(g, 0x24F020), hex((av5[5] & 0x3ffffff) << 2)
                struct.pack_into('<7I', mod, n_, j_(3, g.synth_place['tirage_%d' % (k_ + 1)] + BASE), 0, 0, 0, 0, 0, 0)
                patchs.append(dict(type='mips', site=hex(n_ + BASE), quoi="Upper 0x%X : MOVE.B $103(A1),D0 ; JSR 0x24F020 -> talon tirage_%d (version du CPU tiree au hasard, decor)" % (va_, k_ + 1)))
        if D4_VERSUS:
            av6 = struct.unpack_from('<6I', mod, H_D4_SITE)
            assert av6 == (0x3c027000, 0x8c421114, 0x84430174, 0x3c027000, 0x8c421114, 0xa4430100), [hex(x) for x in av6]
            struct.pack_into('<6I', mod, H_D4_SITE, j_(3, g.synth_place['d4_vs'] + BASE), 0, 0, 0, 0, 0)
            patchs.append(dict(type='mips', site=hex(H_D4_SITE + BASE), quoi="Hyper 0x96C0C (init de match hors Arcade) : MOVE.W $174(A5),$100(A5) -> JSR talon d4_vs (VERSUS : table D4 de J2, drapeaux $FE10 / $FE11)"))
    if TUILES_E1 and 'tuile_e1' in g.synth_place:                 # (e33)
        assert struct.unpack_from('<6I', mod, H_E1_SITE) == H_E1_AVANT, [hex(x) for x in struct.unpack_from('<6I', mod, H_E1_SITE)]
        struct.pack_into('<6I', mod, H_E1_SITE, j_(3, g.synth_place['tuile_e1'] + BASE), 0, 0, 0, 0, 0)
        patchs.append(dict(type='mips', site=hex(H_E1_SITE + BASE), quoi="Hyper 0x395EE0 (image emplacement 1, code + $1000) -> talon tuile_e1 (ecrans d'Upper : + $7700)"))
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
    if ZONE_DECORS:                                   # (e31) corps de la zone (ordre PS2) et ses pointeurs de code
        open(os.path.join(P_, 'zone_decors.bin'), 'wb').write(zbuf + bytes(len(zbuf) & 1))
        open(os.path.join(P_, 'zone_decors_ptrs.txt'), 'w').write(''.join('%x\n' % (o + (FD.zone[0] & 15)) for o in FD.zone_ptr))
    h = lambda x: hex(x) if isinstance(x, int) else x
    z80 = [(a, b, n) for a, b, n in g.place if n < Z80_1]; z2 = [(a, b, n) for a, b, n in g.place if n >= Z2_0]
    info = dict(routines=len(routines), mips=sum(b - a for a, b, _ in g.place),
                zone_z80=[hex(g.g0), hex(Z80_1), sum(b - a for a, b, _ in z80)], zone2=[hex(Z2_0), hex(g.z2_fin), sum(b - a for a, b, _ in z2)],
                blocs=[[hex(a), hex(b), hex(n)] for a, b, n in g.place], synth={k: hex(v + BASE) for k, v in g.synth_place.items()},
                donnees_copiees=[[hex(v), n] for v, n, _ in copie], donnees_reutilisees={hex(v): hex(w) for v, w in reutil.items()},
                taille_bloc=len(blob), pointeurs_code=len(ptr_code),
                zone_decors=([hex(FD.zone[0]), hex(FD.zone[1]), hex(FD.zone[2]), len(FD.zone_ptr)] if ZONE_DECORS else None), patchs=patchs, stat_donnees=dict(FD.stat), patch_116=p116,
                regions=[[hex(a), hex(b), hex(FD.roff[a])] for a, b in FD.reg], grf_y=hex(GRF_Y),
                donnees_non_suivies=len(FD.non_suivis), journaux_lecture=[os.path.basename(os.path.dirname(x)) for x in lj],
                a5_inconnus=sorted(hex(d) for d in inconnus),
                rapport={k: [[h(z) for z in e] for e in v] for k, v in g.rap.items()}, rapport_donnees=rap_donnees,
                decisions={hex(f): [d[0]] + ([hex(d[1]) if isinstance(d[1], int) else d[1]] if len(d) > 1 and d[1] is not None else []) + [Pl.raison[f]] for f, d in Pl.dec.items() if f in Pl.refs or f in Pl.atteint})
    if x2_sites:                                       # (L1) releve des tables prolongees (preuve P2 : l1_max_greffe/essais/x2_neutre.py)
        info['x2'] = [dict(upper=hex(s_['d']['u']), table=hex(s_['a']), copie=hex(s_['nv']), genre=s_['d']['genre'], e=s_['d']['e'],
                           n0=s_['d']['n0'], rangs=s_['d']['R'], taille=hex(s_['taille']), lot=s_['d']['lot'], valeurs=s_['d']['valeurs'])
                      for s_ in x2_sites]
    json.dump(info, open(os.path.join(P_, 'greffe.json'), 'w'), indent=1)
    A_ = assets_json(g, plages, os.path.join(P_, 'assets.json'), {SITE_PERSO_J1: 0}); banques(A_, os.path.join(P_, 'banques_hx'))
    env = dict(MODULE='ro9', TRAVAIL=os.path.join(P_, 'b9'), XDATA='@HA_XDATA@',
               HSFA_GREFFE_ASSETS=os.path.join(P_, 'assets.json'),
               MODULE_FICHIER=os.path.join(P_, 'ro9a_module.bin'), GREFFE_C0='%x' % g.g0, GREFFE_Z2='%x:%x' % (Z2_0, g.z2_fin),
               EXTRACT_MODULES=os.path.dirname(MODULE_SOURCE), HSFA_SON_DONNEES=SON_DONNEES,
               HSFA_GREFFE_DONNEES=os.path.join(P_, 'greffe_donnees.bin'), HSFA_GREFFE_X='%x' % GRF_X, HSFA_GREFFE_Y='%x' % GRF_Y,
               HSFA_GREFFE_PTRS=os.path.join(P_, 'greffe_ptrs.txt'))
    if Y2: env['HSFA_GREFFE_Y2'] = '%x:%x' % Y2
    # (e31, ro9a23 = traducteur v154 = v153 + AIG_D1 cible, agent sakura_hadoken) aiguillages a index garde (semantique PS2)
    # aux 2 sites d'Hyper 0x181d20 (Hadoken de Sakura Z3 S-ISM rouge) et 0x2ef020 (palette des boules de type 0 hors X-ism) ;
    # AIG_D1=0 : v153 (ro9a22) a l'octet
    env['AIG_D1'] = os.environ.get('AIG_D1', '1')
    if env['AIG_D1'] != '0': env['AIG_D1_SEUL'] = os.environ.get('AIG_D1_SEUL', '181d20,2ef020')
    if FENETRES: env['HSFA_GREFFE_FEN'] = ','.join('%x:%x:%x' % f for f in FEN); env['HSFA_GREFFE_Y'] = '%x' % FEN[0][2]
    if ZONE_DECORS:
        env['HSFA_ZONES_68K'] = '%x-%x' % ZONE_CORPS
        env['HSFA_GREFFE_ZONE'] = '%x:%s:%s' % (ZONE_CORPS[0], os.path.join(P_, 'zone_decors.bin'), os.path.join(P_, 'zone_decors_ptrs.txt'))
    open(os.path.join(P_, 'env.sh'), 'w').write(''.join('export %s=%s\n' % kv for kv in env.items()))
    print("greffe %s : %d routines, MIPS %d o ; zone Z80 [%#x, %#x) %d o ; zone 2 [%#x, %#x) %d o ; donnees : %d copiees (%d o), %d reutilisees, %d ptr code"
          % (nom, len(routines), info['mips'], g.g0, Z80_1, info['zone_z80'][2], Z2_0, g.z2_fin, info['zone2'][2], len(copie), len(blob), len(reutil), len(ptr_code)))
    for k, v in g.rap.items(): print("  %-24s %d" % (k, len(v)))
    print("  A5 hors table : %d %s" % (len(inconnus), ' '.join(sorted('$%04X' % d for d in inconnus))[:300]))
    if '--construire' in sys.argv:
        e = dict(os.environ, **env)
        with open(os.path.join(P_, 'construction.log'), 'w') as f:
            subprocess.run((['nice', '-n', '19'] if os.name == 'posix' else []) + [sys.executable, 'mame_test.py'], cwd=TRAD, env=e, stdout=f, stderr=subprocess.STDOUT)
        print(open(os.path.join(P_, 'construction.log')).read().splitlines()[-1])

if __name__ == "__main__":
    main()
