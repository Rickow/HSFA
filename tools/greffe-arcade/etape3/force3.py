#!/usr/bin/env python3
"""(etape 3) DECISIONS IMPOSEES : celles de l'etape 2 (etape2/force.py) + COMBAT = HYPER (COMBAT_HYPER=1) : les
sous-etats 1-6 de la sous-table de combat d'Upper (T_61C2A0) renvoient aux sous-etats d'Hyper (T_5B5F40), K.O. compris.
L'etat 0 (init de manche) l'etait deja ; l'etat 7 (fin de match) reste greffe (talon etat7 de greffe3.py)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etape2'))
import force as F2
COMBAT = {
    0x266280: ('HYPER', 0x9B350),    # A5+C = 2 : presentation de la manche (ROUND, FIGHT)
    0x2679D0: ('HYPER', 0x9B7E0),    # A5+C = 4 : combat
    0x268AB0: ('HYPER', 0x9C940),    # A5+C = 6 : K.O. (crochets ko_compte / ko_suite pour l'Arcade)
    0x26BD50: ('HYPER', 0x9E920),    # A5+C = 8
    0x26CB60: ('HYPER', 0x9F300),    # A5+C = A
    0x26DFB0: ('HYPER', 0x9FD10),    # A5+C = C
    0x2654B0: ('HYPER', 0x9A6F0),    # suite de 0x265440 a CHAQUE image de combat (objets, decor, temps, HUD : le moteur
                                     # des objets d'Upper 0x16CA80 faisait tourner les objets de combat d'Hyper)
}
# ecran VS (scene 4/4, A5+C = 2) et entree dans le decor (A5+C = 4) : VS_UPPER=1 (defaut) -> routines d'Upper (portraits
# et noms du VS d'Upper ; le VS d'Hyper 0x9A430 montrait l'adversaire precedent), mais la preparation du DECOR qu'elles
# appellent passe par Hyper (greffe3.py, PAR_APPELANT_HYPER) ; VS_UPPER=0 -> VS d'Hyper
VS_HYPER = {
    0x2651C0: ('HYPER', 0x9A430),
    0x265310: ('HYPER', 0x9A570),
}
# hors combat : aiguilleurs apparies a tort par le tri (audit_aiguilleurs.py)
ARCADE = {
    0x2A300: ('GREFFE',),            # scene A (fin du perso + generique) : aiguilleur par $148(A5) sur T_60B380 ; le tri
                                     # l'avait renvoye a 0x5DA40 (aiguilleur d'objets d'Hyper par $BC(A6), autre table)
}
# aiguilleurs (table de pointeurs de code) renvoyes a Hyper par la regle d) du tri : leur table ne correspond pas a
# celle de l'homologue (etape3/tri_tables.py) -> copies d'Upper
for _f in (0x2FB40,            # fin : sous-etats A5+C (T_60BAC0) ; Hyper 0x3219B0 = autre table (2 entrees)
           0x10D030, 0x17EEF0, 0x1E3C70, 0x1E5170, 0x1EFF50):   # gestionnaires d'objets des ecrans Arcade
    ARCADE[_f] = ('GREFFE',)
ARCADE[0x136D50] = ('GREFFE',)       # relais (JMP 0x136D70 : joueur battu ? -> continue) de la tache Arcade ; « homologue »
                                     # 0x24A90 d'Hyper par la regle j) : autre relais -> J1 passait au sous-etat 4 et
                                     # l'ecran CONTINUE etait saute
COMBAT_SYNTH = {0x272D80: ('SYNTH', 'remap_ids')}   # init de match : ids des joueurs par T_61C160 (40 persos)
# services d'affichage partages avec le VERSUS (regle f) mais dont la table differe (audit_aiguilleurs.py) : les ecrans
# Arcade d'Upper dessinent leurs plans avec les BIBLIOTHEQUES de blocs d'Upper (T_69B830 : 119 blocs s1 contre 6) ->
# copies d'Upper (le combat appelle directement ceux d'Hyper)
for _f in (0x14FBA0, 0x1707F0):
    ARCADE[_f] = ('GREFFE',)
# moteur des objets $5000-$5C00 (texte, acteurs) appele par les ecrans Arcade (pose de victoire 0x26F930, fin 0x2AF30) :
# celui d'Upper avec SA table des types T_612C70 (Hyper 0x3A45F0 lit T_5CABD0 : types d'Hyper ; fin de Sakura : saut
# hors du code). Le combat appelle directement 0x3A45F0.
ARCADE[0x1196E0] = ('GREFFE',)
# (etape 4) EFFACEMENT DES PLANS des ecrans d'Upper (0xC58C0, appele en fin de la scene $14 d'Upper : s2 $904000 rempli
# de $0020, s3 $908000 de $1C20, $90C000, $910000...) : « equivalente » par la forme a Hyper 0x38AB50, qui efface
# d'AUTRES pages avec ses propres codes de tuiles ($1020) -> planisphere sur un fond de tuiles d'Hyper. CLEAR_UPPER=0 : sans
if os.environ.get("CLEAR_UPPER", "0") == "1": ARCADE[0xC58C0] = ('GREFFE',)
# (etape 4) GESTIONNAIRES DES TYPES D'OBJETS d'Upper (T_615100, 122 types ; T_612C70, 24 ; moteurs 0x16CA80 / 0x1196E0
# greffes) que la regle j) « non vue en Arcade : homologue » envoyait sur une MEME routine d'Hyper (40 -> 0x31F50, 9 ->
# 0x2FEC0, 7 -> 0x64D00...) : fins de Sakura/Ryu, objet d'Upper traite par le gestionnaire d'Hyper 0x2FEC0 qui ecrit dans
# l'emplacement voisin ($FFBE80) -> type $B0 -> saut hors du code. Homologues NON INJECTIFS -> greffes (33 routines,
# 4 464 o MIPS ; liste tiree de greffe.json d'e6j). TYPES_GREFFE=0 : sans
TYPES_PARTAGES = (0x249e0, 0x24a00, 0x24a20, 0x24a40, 0x24a60, 0x96ad0, 0x11a060, 0x11f3f0, 0x12a340, 0x12eac0, 0x16cc20,
                  0x16cc50, 0x16dae0, 0x1738c0, 0x1926a0, 0x19ed80, 0x19f110, 0x1aef80, 0x1afb30, 0x1b22b0, 0x1b5580,
                  0x1b85f0, 0x1c67d0, 0x1c6ed0, 0x1cec90, 0x1dc3b0, 0x1dd2b0, 0x1defb0, 0x1df5f0, 0x20f2e0, 0x21add0,
                  0x2205b0, 0x414e30)
if os.environ.get("TYPES_GREFFE", "1") == "1":
    for _f in TYPES_PARTAGES: ARCADE[_f] = ('GREFFE',)
# (etape 4) DESSIN_UPPER=1 : Upper 0x148240 (dessin des objets, appele par l'affichage 0x13D820) « equivalente » a Hyper
# 0x39CC90 par son code, mais ses appels vont au moteur d'Hyper (0x3932F0 -> 0x393D40) qui lit les objets au format
# d'Hyper (+$1C = table d'animation) : fin de Ryu, objets $4B d'Upper -> A0 = $601 -> erreur d'adresse. A combiner
# avec AFFICHAGE_UPPER=1 (greffe3.py)
# (etape 5) ... et les SOUS-DESSINATEURS par liste d'objets de 0x13D820 (« equivalents » a ceux d'Hyper 0x392xxx/0x393xxx,
# mais qui sautent dans la boucle de liste et le dessin par objet d'Hyper 0x3932F0/0x393890/0x393D40) : copies d'Upper,
# atteintes seulement par la copie de 0x13D820 (appelants Arcade de AFFICHAGE, greffe3.py) ; le combat garde Hyper
SOUS_DESSIN = (0x13EA10, 0x14B670, 0x13E510, 0x13E800, 0x13E020, 0x13E760, 0x1483D0, 0x13DDF0, 0x13DF80, 0x13E6C0, 0x13E970,
               0x13E620, 0x148240, 0x13E490, 0x13E410, 0x13E390, 0x13E310, 0x13E290, 0x13E210, 0x13E190, 0x14A3A0, 0x14A5D0,
               0x13DB10, 0x13E8A0, 0x13EE40, 0x13F270, 0x13F280, 0x13F2F0, 0x13F360)   # + boucle de liste, dessin par objet, animation
# (etape 6) ... et tout le reste du moteur d'affichage d'Upper 0x13D820-0x14E000 encore envoye a Hyper (boucles de
# liste « equivalentes » comme 0x13EAB0 -> Hyper 0x393500, commandes d'animation T_614460 0x13F900...) : fin de 1C
DESSIN_RESTE = (0x13db40, 0x13e180, 0x13e590, 0x13e610, 0x13e960, 0x13eab0, 0x13eb70, 0x13f900, 0x13ff90, 0x1406b0, 0x140ee0,
                0x141590, 0x141c10, 0x1422a0, 0x142d60, 0x143b20, 0x143f70, 0x1443c0, 0x144660, 0x1449f0, 0x148560, 0x14a800,
                0x14b720, 0x14b790, 0x14b800, 0x14b860, 0x14d150)
if os.environ.get("DESSIN_UPPER", "0") == "1":
    for _f in SOUS_DESSIN: ARCADE[_f] = ('GREFFE',)
    for _f in DESSIN_RESTE: ARCADE[_f] = ('GREFFE',)
# (etape 6) J_NON_INJ=1 : toutes les routines de la regle j) dont l'homologue d'Hyper est PARTAGE avec une autre routine
# d'Upper (donnees/j_non_injectifs.txt, tire de greffe.json) -> greffees ; ex. 0x17EFC0 (sous-etats 2-3 du type $0D,
# continue) -> Hyper 0x31F50 effacait l'objet du grand chiffre de CONTINUE
if os.environ.get("J_NON_INJ", "0") == "1":
    _fj = '<workspace>/work/greffe_arcade/donnees/j_non_injectifs.txt'
    if os.path.exists(_fj):
        for _l in open(_fj):
            if _l.strip() and not _l.startswith('#'): ARCADE[int(_l, 16)] = ('GREFFE',)
# (etape 6) ANIM_GREFFE=1 : coeur d'animation d'Upper (pose d'animation 0xC84A0/0xC8510/0xC85A0, 0xC8D50, 0xC8EC0,
# 0xCE4F0) envoye a Hyper par la regle j) « non vue en Arcade » (fins des persos 19 : Upper 0x20E410 -> Hyper 0x38D3B0
# -> 0x38D4D0), et 0x139750 « equivalente » a Hyper 0x388910 (fin du perso 05 : -> Hyper 0x387560) -> greffes
ANIM_GREFFE = (0xC84A0, 0xC8510, 0xC85A0, 0xC8D50, 0xC8EC0, 0xCE4F0, 0x139750,
               0xC8150, 0xC82D0, 0xC85C0, 0xC8890, 0xC8C00, 0xC8C50, 0xC8F10, 0xC8F80)   # + toute la pose d'animation 0xC8000-0xC97FF
if os.environ.get("ANIM_GREFFE", "0") == "1":   # (etape 6) 1 casse le perso 02 sans rien reparer
    for _f in ANIM_GREFFE: ARCADE[_f] = ('GREFFE',)
# (etape 7) CONT_GREFFE=1 : sous-etats du type d'objet $0D (CONTINUE : barre verticale « CONTINUE », pas le chiffre) envoyes a Hyper par la
# regle d) « tri : HYPER » : 0x17BD90 (glissement, T_615D60[0]) -> Hyper 0x3BB7C0 (l'objet ne glissait pas et se
# liberait au bout de 74 images) et 0x17BFF0 (T_615D60[2], appele aussi par 0x17BF08) -> Hyper 0x30300 -> greffes
# CONT_GREFFE=1 : les deux ; CONT_GREFFE=a : 0x17BD90 seule ; CONT_GREFFE=b : 0x17BFF0 seule ; 0 : aucune
CONT_GREFFE = (0x17BD90, 0x17BFF0)
_cg = os.environ.get("CONT_GREFFE", "1")
for _i, _f in enumerate(CONT_GREFFE):
    if _cg == "1" or _cg == "ab"[_i]: ARCADE[_f] = ('GREFFE',)
# (etape 7) FIN05_GREFFE=1 : Upper 0x2139C0 (gestion d'un acteur de la fin de 05, « non vue en Arcade ») etait envoyee
# a l'homologue d'Hyper 0x1C7B90, qui cree un objet d'Hyper (0x327510) au lieu de l'objet $4D d'Upper -> 0x388910 avec
# $0F(A6) = 6 (index non aligne de T_5C9AE0) -> plantage
FIN05_GREFFE = (0x2139C0, 0x21AB10, 0x20FFF0, 0x2100C0, 0x2101E0)   # + 0x21AB10 (creation de l objet $4D) -> Hyper 0x327510 (j)
if os.environ.get("FIN05_GREFFE", "1") == "1":
    for _f in FIN05_GREFFE: ARCADE[_f] = ('GREFFE',)
# (2026-10-28) INTERMEDES=1 : scenes d'Upper AVANT le combat (sous-etat 2 du combat, 0x266280 : aiguillage
# T_61C2C0[$13E(A5)]) : rival, intrusion (perso 19 : BSET #5,$148(J1) + J2 = $15 en 0x266B9C, puis Final Battle). Hyper
# 0x9B350 a le MEME code mais sa table T_5B5F60 renvoie toutes les entrees sur 0x9B4F0 (rien) -> dans ro9a les bits de
# progression $148(joueur) ne sont jamais poses, l'adversaire special n'est jamais insere et la fin chargee est la
# mauvaise ($148 = 2 -> fichier de fin $0A). Copies d'Upper : l'aiguilleur, ses tetes d'automate (tables differentes de
# celles d'Hyper : 0x2664F0 et 0x266EB0 etaient appariees toutes deux a Hyper 0x9B5C0) et les scenes.
INTERMEDES = (0x266280, 0x2664F0, 0x266560, 0x266950, 0x266990, 0x266A00, 0x266EB0, 0x266F20, 0x267770, 0x2677B0, 0x267820)
def force():
    d = dict(F2.FORCE); d.update(ARCADE)
    # (etape 4) choix du decor d'Upper (0x24F020 : T_61BE10, boss $14, rival) au lieu de celui d'Hyper (etape 2) : $174/$100
    # en numerotation d'Upper ; le talon vs_decor ramene le combat a un decor d'Hyper et sauve la valeur pour la fin
    if os.environ.get("DECOR_UPPER_CHOIX", "1") == "1": d.pop(0x24F020, None)
    if os.environ.get("COMBAT_HYPER", "1") == "1":
        d.update(COMBAT); d.update(COMBAT_SYNTH)
        if os.environ.get("INTERMEDES", "0") == "1":
            for _f in INTERMEDES: d[_f] = ('GREFFE',)
        if os.environ.get("VS_UPPER", "1") != "1": d.update(VS_HYPER)
    return d
FORCE = force()
