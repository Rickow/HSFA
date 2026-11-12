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
# (e33) CLEAR_UPPER=1 PAR DEFAUT : les ecrans d'Upper de la greffe ont desormais les bases d'Upper (400/440/4A0) ; le GAME OVER
# apres defaite contre le boss final (copie de 0x2B2D0 -> 0xC58C0 -> Hyper 0x38AB50) remplissait s2 de $1020 (code d'Hyper)
# au lieu de $1C20 -> damier vert ; idem 0xCA490 (+$1C10, Hyper 0x38DA90 : +$1010, bande de 96 cases). =0 : comme e32.
if os.environ.get("CLEAR_UPPER", "1") == "1":
    ARCADE[0xC58C0] = ('GREFFE',); ARCADE[0xCA490] = ('GREFFE',)
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
    _fj = '@HA_G@/donnees/j_non_injectifs.txt'
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
# (28/10) CONT_JOUEUR=1 : Upper 0x24AA40 (rend en A0 le joueur qui continue : LEA $0400(A5),A0...) etait envoyee par le tri
# (regle d) a Hyper 0x2D90D0, une routine de joueur sans rapport : $9EA4 recevait $FC78 au lieu de $8400 -> l'objet du
# grand chiffre de CONTINUE lisait $10C d'un faux joueur (chiffre fige sur 0). Copie d'Upper.
if os.environ.get("CONT_JOUEUR", "1") == "1":
    ARCADE[0x24AA40] = ('GREFFE',)
# (01/11, essai) CHALLENGER=1 : Upper 0x1353A0 (arrivee d'un 2e joueur en cours de partie : (A5) = 2, $2-$F(A5) = 0 ->
# scene de selection) etait envoyee par la regle j) (non vue en Arcade) a Hyper 0x9A570 (ADDQ.W #2,$8(A5) a chaque appel)
# -> A5+8 = 8, A, ..., $14 hors de la table de la scene 4 d'Upper -> plantage (pc $A08) des le « nouveau challenger ».
if os.environ.get("CHALLENGER", "1") == "1":   # (e25) defaut 1
    ARCADE[0x1353A0] = ('GREFFE',)
# (28/10) FIN0D_GREFFE=1 : Upper 0x21AE40 (appelee par le gestionnaire du type d'objet $50, 0x21ADD0, acteur de la fin de
# Sakura) et 0x20F3A0 etaient envoyees toutes deux a Hyper 0x4CF60 par la regle j) (homologue NON injectif) : code de
# joueur d'Hyper ($67 / $26A de A1) sur un pointeur faux -> octets $01 semes dans la reserve d'objets ($FFDA00) -> le dessin
# d'Hyper plante ($2B8). Copies d'Upper.
FIN0D_GREFFE = (0x21AE40, 0x1B8B20)
if os.environ.get("FIN0D_GREFFE", "0") == "1":   # (28/10) essai : cascade (type $26, puis table des types) -> 0
    for _f in FIN0D_GREFFE: ARCADE[_f] = ('GREFFE',)
# (2026-10-28) INTERMEDES=1 : scenes d'Upper AVANT le combat (sous-etat 2 du combat, 0x266280 : aiguillage
# T_61C2C0[$13E(A5)]) : rival, intrusion (perso 19 : BSET #5,$148(J1) + J2 = $15 en 0x266B9C, puis Final Battle). Hyper
# 0x9B350 a le MEME code mais sa table T_5B5F60 renvoie toutes les entrees sur 0x9B4F0 (rien) -> dans ro9a les bits de
# progression $148(joueur) ne sont jamais poses, l'adversaire special n'est jamais insere et la fin chargee est la
# mauvaise ($148 = 2 -> fichier de fin $0A). Copies d'Upper : l'aiguilleur, ses tetes d'automate (tables differentes de
# celles d'Hyper : 0x2664F0 et 0x266EB0 etaient appariees toutes deux a Hyper 0x9B5C0) et les scenes.
INTERMEDES = (0x266280, 0x2664F0, 0x266560, 0x266950, 0x266990, 0x266A00, 0x266EB0, 0x266F20, 0x267770, 0x2677B0, 0x267820)
# (e33) HOM_PARTAGES=1 : routines renvoyees aux homologues NON INJECTIFS 0xA0FD0 (82 : gestionnaires d'acteurs de fin, table
# T_619430 du type $4B ; E. Honda de la fin de Zangief = entree $1C, 0x1F9B60 -> Hyper 0xA0FD0 : l'acteur restait a l'etat 0,
# jamais affiche) et 0x2FEC0 (25) -> greffees. Liste : e33/hom_partages.txt. =0 : comme e32. Applique APRES
# DECISIONS_ANCIENNES (41 de ces decisions y etaient « imposees »).
HOM_PARTAGES = []
if os.environ.get("HOM_PARTAGES", "1") == "1":
    _fh = os.environ.get("HOM_PARTAGES_LISTE", '@HA_G@/e33/hom_partages.txt')
    HOM_PARTAGES = [int(_l, 16) for _l in open(_fh) if _l.strip() and not _l.startswith('#')]
# (e38) CARTE_GREFFE=1 : etapes de la CARTE DU MONDE d'Upper (scene 4/2, sous-etats $14 de T_61C050 : 0x259DB0,
# 0x259F20, 0x25A090, 0x25A200, 0x25A370 = « bouton ? -> saut (0x25A690 : $14 = $E) ; sinon attendre $13 = 3/$F/$20/$40 »)
# envoyees TOUTES a Hyper 0x31F210 par « d) tri : HYPER » (homologue non injectif : attend $13 = $7F, le bouton ne pose que
# $15E) -> sans bouton la carte ne finissait jamais, avec bouton ~260-290 images (Upper : 343-413 sans bouton, 79-109 avec).
CARTE_GREFFE = (0x259DB0, 0x259F20, 0x25A090, 0x25A200, 0x25A370)
if os.environ.get("CARTE_GREFFE", "0") == "1":
    for _f in CARTE_GREFFE: ARCADE[_f] = ('GREFFE',)
# (e38) PARALLAXE_TABLE=1 : variante « par table » de la parallaxe X des plans d'Upper (0x158F40 : X = camera - $28A +
# $380(A5)[$3A0] - $C0 + $A(A6), queue 0x159040) envoyee a Hyper 0x30F5B0 (k = 1/8) par « d) tri : HYPER » : scroll3 du
# decor de Chun-Li ($08/$24) presque fixe (0x16F-0x190 contre 0xEB-0x214 dans Upper).
# + sa jumelle de scroll1 0x154CB0 (-14(A0,D1), queue 0x154DB0 ; meme renvoi a 0x30F5B0) : scroll1 du decor de Vega ($38)
# quasi fixe (s1X 0x170-0x190 contre 0xDC-0x224 dans Upper) = GRILLAGE qui glisse sur le sol.
if os.environ.get("PARALLAXE_TABLE", "0") == "1":
    ARCADE[0x158F40] = ('GREFFE',); ARCADE[0x154CB0] = ('GREFFE',)
# (e38) EFFET_08=1 : effet par decor d'Upper du decor de Chun-Li ($08/$24, 0x13C6C0 : defilement par ligne du sol,
# sorties $C174/$C176) envoye a Hyper 0x391F80 (« apparentee 40-70 % ») par « d) tri : HYPER » -> copie d'Upper.
if os.environ.get("EFFET_08", "0") == "1":
    ARCADE[0x13C6C0] = ('GREFFE',)
FIN_ETATS_G = (0x1F5810, 0x1F5A30, 0x1F6130, 0x1F7B60, 0x1F7F80, 0x1FC6F0, 0x1FCEE0, 0x1FD4F0, 0x202510, 0x202870, 0x203BE0,
               0x204BB0, 0x207530, 0x207780, 0x20B2A0, 0x20B430, 0x20C6E0, 0x216310)   # (e39) voir FIN_ETATS_G dans force()
def force():
    d = dict(F2.FORCE); d.update(ARCADE)
    # (28/10) DECISIONS_ANCIENNES=<json {routine: decision}> : bissection (decisions de ro9a9 remises sur une liste)
    _da = os.environ.get("DECISIONS_ANCIENNES", "@HA_G@/donnees/decisions_anciennes_e12.json")   # (ro9a10) defaut : 182 decisions de ro9a9 gardees ; "" : aucune
    if _da:
        import json as _js
        for _k, _v in _js.load(open(_da)).items():
            d[int(_k, 16)] = ('HYPER', int(_v[1], 16)) if _v[0] == 'HYPER' else ('GREFFE',)
    # (etape 4) choix du decor d'Upper (0x24F020 : T_61BE10, boss $14, rival) au lieu de celui d'Hyper (etape 2) : $174/$100
    # en numerotation d'Upper ; le talon vs_decor ramene le combat a un decor d'Hyper et sauve la valeur pour la fin
    if os.environ.get("DECOR_UPPER_CHOIX", "1") == "1": d.pop(0x24F020, None)
    if os.environ.get("COMBAT_HYPER", "1") == "1":
        d.update(COMBAT); d.update(COMBAT_SYNTH)
        if os.environ.get("INTERMEDES", "1") == "1":
            for _f in INTERMEDES: d[_f] = ('GREFFE',)
        if os.environ.get("VS_UPPER", "1") != "1": d.update(VS_HYPER)
    # (e27) FIN_ACTEURS_GREFFE (defaut 213110,2138b0) : gestionnaires d'ACTEURS DE FIN d'Upper (table des classes T_619D30,
    # 25 entrees, aiguillage 0x2119B8) gardes par DECISIONS_ANCIENNES (regle j, « non vue en Arcade ») sur des homologues
    # d'Hyper SANS RAPPORT : classe $10 (0x213110 -> 0x393CD0, interpreteur de script d'Hyper : lit $1C = 0, puis les
    # vecteurs de la ROM) et classe $18 (0x2138B0 -> 0x2B7A60, routine de joueur d'Hyper) : fins de Bison (0a) et de
    # Rose (09) ; aboutissaient par hasard dans ro9a18, exception $A08 dans ro9a19 (code et donnees decales). Copies d'Upper.
    # Vide -> comme ro9a19.
    # (e28) defaut etendu aux classes 6, 7, 10, 14 (0x2125A0 et 0x212630 -> 0x3351F0, 0x2127C0 -> 0x322FA0, 0x212FC0 ->
    # 0x327E00 : meme defaut d'homologue) : 85/85, seule duree changee : fin de Charlie (03) 9508 -> 9509 (Upper 9599).
    # Liste de ro9a20 : FIN_ACTEURS_GREFFE=213110,2138b0.
    for _x in os.environ.get("FIN_ACTEURS_GREFFE", "213110,2138b0,2125a0,212630,2127c0,212fc0").split(','):
        if _x: d[int(_x, 16)] = ('GREFFE',)
    for _x in HOM_PARTAGES: d[_x] = ('GREFFE',)        # (e33)
    # (e38) FONDU_901E0=1 : Upper 0x901E0 (lance la tache de fondu « vers les palettes $184-$190 », code 0x8BB40, D1 = $2001)
    # etait renvoyee par DECISIONS_ANCIENNES (regle j) a Hyper 0x94AD0, qui lance la tache d'HYPER 0x90640 (autre table de
    # fondus : $180 passe a $0F en une image, aucun fondu) -> fin de Ken, scene du bateau : palettes $90C000 restees
    # BLANCHES. Ses 4 jumelles (0x90060, 0x90120, 0x902A0, 0x90360, 0x90420) etaient deja greffees. Applique APRES les
    # decisions anciennes. =0 : comme e37.
    if os.environ.get("FONDU_901E0", "0") == "1": d[0x901E0] = ('GREFFE',)
    # (e45, ro9a35) FONDU_8FF20=1 : Upper 0x8FF20 (entree en fondu de la palette de scene : $C140/$C154(A5) = $0190C000,
    # puis la tache de fondu) renvoyee par « g) modifiee hors coeur » a Hyper 0x948C0, homologue PARTAGE avec 0x8FDD0
    # (fondu au NOIR, base $0192A000) -> fin d'E. Honda, 3e scene (foret violette, generique) : base de palette CPS-A
    # $92A0 (page vide) au lieu de $90C0 -> ecran noir ~1800 images (sondes e44 sv_u4140 / sv_g4140). =0 : comme ro9a34.
    if os.environ.get("FONDU_8FF20", "0") == "1": d[0x8FF20] = ('GREFFE',)
    # (e39) DECOR_4E=1 : routine scroll1 du decor $4E d'Upper (0x1540A0, entree $4E de T_614850, appelee par la copie du
    # moteur de plans 0x151B80) renvoyee par « j) non vue en Arcade » a Hyper 0x30EFC0, qui lit les tables d'HYPER par
    # $100 (Hyper 0x313A90 : T a $1A4EB0) -> a l'ecran VS sur le decor $4E, erreur d'adresse ($A08). Les 39 autres
    # entrees sont des copies. =0 : comme e38.
    if os.environ.get("DECOR_4E", "0") == "1": d[0x1540A0] = ('GREFFE',)
    # (e39) FIN_SAGAT=1 : gestionnaire d'acteurs de fin d'Upper 0x2046C0 (fin de Sagat, scene de Bison : acteur $37 qui cree
    # les acteurs $35 = boules psycho, anim $4C de la banque de Bison) GREFFE au lieu de l'homologue d'Hyper 0xA0FD0 (liste
    # hom_partages_51 = 50 + 0x2046C0). Le plantage d'e35g (a08 en 0x9515A) ne se produit plus avec les correctifs e38
    # (e39a : fin aboutie, 8049 images). =0 : comme e38.
    # + son etat 0x203BE0 (acteur $34 = Bison de la scene de la foret : anims $4F/$50 et tir des boules sur Ryu a terre ;
    # « g) modifiee hors coeur » -> Hyper 0xA0FD0, homologue partage par ~50 gestionnaires d'acteurs de fin : rien ne se passe)
    # + 0x202510 (etat de l'acteur Ryu de la foret : attente $7B puis anim $7F = Ryu souleve par les boules ; meme defaut)
    # FIN_SAGAT=foret : 0x203BE0 + 0x202510 seulement (scene de la foret). 0x2046C0 (scene Bison contre Ryu) fait planter
    # Sagat Z3 sous MAME (e39c : a08 a +2241, boucle de dessin d'Hyper 0x393890 : A3 ecrase pendant le dessin de l'acteur $37,
    # liste $7136 lue hors bornes) et fige la scene au coeur (Bison absent, boule immobile) : a reprendre.
    _fs = os.environ.get("FIN_SAGAT", "0")
    if _fs in ("1", "foret"): d[0x203BE0] = ('GREFFE',); d[0x202510] = ('GREFFE',)
    if _fs == "1": d[0x2046C0] = ('GREFFE',)
    # (e39) FIN_ETATS_G=1 : les 18 etats d'acteurs de fin d'Upper « g) modifiee hors coeur » renvoyes a Hyper 0xA0FD0 (routine
    # de COMBAT d'Hyper qui compare les vies $450/$850 : homologue absurde) -> GREFFE. Ce sont surtout des etats « attendre
    # $7B(A6) images puis poser l'anim $7F(A6) » : sans eux un acteur reste sur sa 1re pose. =0 : comme FIN_SAGAT seul.
    if os.environ.get("FIN_ETATS_G", "0") == "1":
        for _f in FIN_ETATS_G: d[_f] = ('GREFFE',)
    # (e39, ro9a31) FIN_A0FD0=hex,hex : gestionnaires / etats d'acteurs de fin d'Upper renvoyes a Hyper 0xA0FD0 et EXECUTES dans
    # les fins d'Upper (couverture e39/couv, e39/resume_couv.py) -> GREFFE. Vide : comme ro9a30.
    for _x in os.environ.get("FIN_A0FD0", "").split(','):
        if _x.strip(): d[int(_x, 16)] = ('GREFFE',)
    return d
FORCE = force()
