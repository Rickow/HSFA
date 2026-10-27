"""Traducteur expérimental d'un gestionnaire de perso : MIPS du PSP (C compilé) -> assembleur 68K arcade.

Règles apprises sur les 26 persos de SFA3 (rosette, README) :
  - objet : a0 à l'entrée (et ses copies, ex. s0) = A6 ; champs : carte PSP -> 68K (zones + votes), taille 68K usuelle ;
    accès 32 bits dans la zone « +2 » ($10-$14 : positions) : même décalage (l'écart +2 ne vaut que pour les demi-mots,
    effet petit-boutiste) ;
  - appels : cible PSP -> cible arcade (api_arcade_psp.json + interpolées) ; arguments a1, a2, a3 -> D0, D1, D2 ;
    un appel suivi seulement de l'épilogue = JMP ;
  - numéros d'état (champs $4-$7) : PSP n <-> 68K 2n (tables de mots) ;
  - créneau de délai : exécuté avant le saut ; « likely » (beql, bnel, bltzl, bgezl) : seulement si le saut est pris
    (tremplin émis en fin de routine).
Méthode : exécution symbolique par bloc de base (valeurs = expressions), émission aux écritures, appels et sauts.
Ce qui n'est pas reconnu sort en « ?? » : le résultat est une ÉBAUCHE à relire, pas du code fini."""
import sys, os, json, re, struct, collections
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
from relocs import img
from mips import decode, REG
from charcode2 import fend
from champs import modele

API = {int(p, 16): int(a, 16) for a, p in json.load(open("api_arcade_psp.json")).items()}
API.update({0x5d75c: 0x2a770, 0x5d900: 0x2a7f0, 0x5da38: 0x2a83c, 0x5dbe8: 0x2a8ca, 0x5dedc: 0x2a98c, 0x5f2c4: 0x2af7a,
            0x5f748: 0x2b0c4, 0x66d10: 0x2e5f0, 0x66d68: 0x2e614, 0x69b94: 0x2f728, 0x69be8: 0x2f74c, 0x69c3c: 0x2f770,
            0x69c78: 0x2f796, 0x69d68: 0x2f980, 0x69fc4: 0x2faae, 0x6a17c: 0x2fb96})          # interpolées (ordre)
API.update({0x1D424: 0x1B4D0, 0x1D5C4: 0x1B4EC, 0x70C90: 0x251F0})
# (2026-10-07) annulation coup normal -> coup normal (rosette par $28E) : PSP 0x67B1C = arcade $2EB06 (pas à pas
# identique : $10D|$8A, $2AF7A, $132/$102, $5B, boutons, $2EB8C = 0x67CB8, $2B216 = 0x5FA9C, $3E, $28E, $2EC0A =
# 0x67E08, $2EBBE = 0x67D68, $82/$81/$80, $2070A = 0x331F8, $2F770) ; tables par ID ($DC9EA…) à étendre pour $26-$29
API.update({0x33058: 0x2065C, 0x33130: 0x206AE, 0x32E60: 0x2055C})   # points (mode $AC = 3 exclu, $125)
API.update({0x67E50: 0x2EC28})
# (2026-10-07) retour en garde : PSP 0x60740 = arcade $2BB26 (pas à pas : $2B828, état $02000004, $2C8 = 1, $2BB5A,
# $2F490, remises à zéro $B0/$5E/$5D/$23A, animation 1) -> sous-fonctions appariées par position
API.update({0x60740: 0x2BB26, 0x60494: 0x2B828, 0x6331C: 0x2BB5A, 0x6929C: 0x2F490})   # poing faible + pied faible (même structure pas à pas)
API.update({0x67B1C: 0x2EB06, 0x67CB8: 0x2EB8C, 0x5FA9C: 0x2B216, 0x67E08: 0x2EC0A, 0x67D68: 0x2EBBE, 0x331F8: 0x2070A})   # (2026-10-07) afficher si à l'écran / afficher (aiguillage par type $8)
API.update({0x1F19C: 0x1C28E, 0x1F1C8: 0x1C2DE, 0x1F1F4: 0x1C3C2, 0x1F220: 0x1C32E, 0x1F24C: 0x1C37E})  # libérations (objet = A6)
# (2026-10-07) 0x78408 (jouer le son de code ABSOLU a2, joueur a1) n'est PAS l'arcade $38E4 (index dans la table de
# voix du perso $E6(A6)) : appariement par votes juste pour les persos arcade, faux pour MAX (voix absentes de la ROM
# son d'Upper). -> appel « bsr psp_78408 » (D0 = joueur, D1 = code PSP), point d'entrée unique des sons MAX.
API.pop(0x78408, None)
# (2026-10-07) routines communes des PROJECTILES (objet = A6, sans argument) : renvoi 0x72744 = $33120 (gel, demi-tour,
# 2 images, vitesses inversées, accélération par table $72), 0x72678 = $330C4 (même chose sans table), disparition
# 0x725C0 = $33074 (0x18 images clignotantes puis état 3), avancer l'animation 0x728F0 = $33210. (0x7284C = $331D0
# seulement si la table par perso $3327A est étendue aux ID MAX : non apparié.)
API.update({0x72744: 0x33120, 0x72678: 0x330C4, 0x725C0: 0x33074, 0x728F0: 0x33210})
# (2026-10-07) contrôles avant coup (Ryu arcade : spéciaux -> $2ED00, supers -> $2ECD8 après $132 / $238 ; retours D0 = 1/0)
# et retour en garde : 0x686EC = $2ECD8 (jauge 0x30 / 0x90 / 0x48 selon $132), 0x67F84 = $2ED00, 0x682B4 = $2ED28
# (état $2000606), 0x6069C = $2BAF2 (= $2B828 puis animation 0), 0x606CC(objet, n) = $2BAF8 (D0 = n)
# 0x1F0F4 = $1C206 (libération d'un objet de type 8 / projectile) ; 0x72998 = $3323A (pointeurs $90-$A0 depuis l'en-tête
# $60 : ⚠ en-tête PSP = 5 longs absolus, arcade = 5 mots relatifs -> en-têtes des projectiles MAX à convertir)
API.update({0x1F0F4: 0x1C206, 0x72998: 0x3323A})
API.update({0x6808C: 0x2EDA0})
# 0x670AC (coup direct si l'adversaire n'est pas en l'air) = arcade $2E700, absente d'Upper -> psp_670ac à la main     # queue commune des contrôles avant coup ($5D/$5E, $2AF7A, globales ; D1 = 0 -> $114 = 2)
API.update({0x686EC: 0x2ECD8, 0x67F84: 0x2ED00, 0x682B4: 0x2ED28, 0x6069C: 0x2BAF2, 0x606CC: 0x2BAF8})
SEGS = modele(json.load(open("champs_votes.json"))["chaine"])
HORS = {int(p, 16): int(o, 16) for p, (o, w) in json.load(open("carte_champs.json")).items() if w != "zone"}
HORS.pop(0x10, None); HORS.pop(0x16a, None)
try: TABLES_EXPL = {int(k, 16) for k in json.load(open("tables_explicites.json"))}         # clés = tables
except FileNotFoundError: TABLES_EXPL = set()   # tables de scripts passées par adresse, converties (TAB_xxxxxx)
GLOB = {}                                   # globales PSP hors bloc A5 -> décalage A5 (appris : appris.json « globale »)
try:
    _AP = json.load(open("appris.json"))
    HORS.update({int(p, 16): int(o, 16) for p, o in _AP.get("champ", {}).items()})
    API.update({int(p, 16): int(o, 16) for p, o in _AP.get("fonction", {}).items()})
    GLOB.update({int(p, 16): int(o, 16) for p, o in _AP.get("globale", {}).items()})
except FileNotFoundError: pass
# (2026-10-07) rosette Ryu : 0x39CA67 (structure d'état PSP +0x87) = $10B(A5) « pose de victoire terminée », un bit par
# joueur ; arcade : 2 BSET Dn,$10B(A5) par perso (Ryu 0x3415C/0x341DC), lu une fois (0xA0F8) ; PSP : 0x24C04 seul
# écrivain, appelé 2 fois par Ryu.
# (2026-10-07) test « jeu figé » avant 0x5F2C4 (= $2AF7A) : PSP 0x818305 | 0x39CA06 ; arcade au même endroit
# $10D | $10E | $8A(A5) (ex. 0x3C83C, 0x607EA). 0x39CA06 : seul écrivain = init (0x1EA9C), réglage de partie.
GLOB.update({0x818305: 0x10D, 0x39CA06: 0x8A})    # rectifié : arcade $2EB06 teste $10D | $8A
GLOB.update({0x39CA19: 0xAC})
# (2026-10-07) caméra : PSP 0x80F970 (lui 0x81 + addiu 0xF970 signé) + 0x10 = X caméra 16.16 (partie entière = mot +0x12) = arcade long $290(A5)
# (partie entière = mot $290 ; bord gauche de l'écran, $180 de large) — avant : fenêtre A5 générale -> $7788 (faux)
GLOB.update({0x80F980: 0x290, 0x80F982: 0x290})                 # mode de jeu (PSP 1 en entraînement ; arcade cmpi #3,$AC(A5) au même endroit)
# (2026-10-07, PPSSPP + routine arcade $27AAC) ENTRÉES : PSP 0x2F0 courant, 0x2F2-0x2F6 images précédentes, 0x2F8 appuyés,
# 0x2FA relâchés (0x2FC/0x2FE : copies) = arcade $370, $372-$376, $378, $37A ($37C/$37E). Même codage des directions
# (bits 0-3, gauche/droite relatifs au sens $B) ; BOUTONS différents : PSP poings $10/$20/$40, pieds $80/$100/$200 ;
# arcade poings $1000/$2000/$4000, pieds $100/$200/$400 -> constantes converties (conv_boutons). Ancienne carte fausse
# (0x2F0 -> $38, 0x2F8 -> $34 : vote 3/5).
HORS.update({0x2F0 + 2 * _k: 0x370 + 2 * _k for _k in range(8)})
# (2026-10-07) fenêtre d'annulation : PSP 0x70C90 (0x27E = table 0x21E0D0[ID]) = arcade $251F0 ($28E = table $25204[$102],
# mêmes valeurs) ; mesurée sous PPSSPP (Ingrid : 6 au lancement du poing faible, décrémentée après l'arrêt sur coup)
HORS[0x27E] = 0x28E
# (2026-10-07) rosette $2EDC2 / PSP 0x68380 : « $3F = $254 ; clr $2C8 ; clr $D6 » <-> « … ; clr 0x10E » -> 0x10E = $D6
HORS[0x10E] = 0xD6
# (2026-10-07) zones +$10 (rosette $2E4C2 / 0x66BB4 et $251F0 / 0x70C90) : PSP 0x270-0x27F -> $280-$28F, 0x2B0-0x2BF -> $2C0-$2CF
for _p in range(0x270, 0x280): HORS.setdefault(_p, _p + 0x10)
for _p in range(0x2B0, 0x2C0): HORS.setdefault(_p, _p + 0x10)
BOUTONS = {0x370 + 2 * _k for _k in range(8)} | {0x371 + 2 * _k for _k in range(8)}
def conv_boutons(c):
    return (c & 0xF) | ((c & 0x70) << 8) | ((c & 0x380) << 1) | (c & ~0x3FF & 0xFFFF0000)
GLOB.update({0x39CA67: 0x10B, 0xA3E7C2: 0x6EB8, 0xA3E7C3: 0x6EB9, 0xA3E7C4: 0x6EBC, 0xA3E7C5: 0x6EBA, 0xA3E7C6: 0x6EBB})   # + compteurs des réservoirs (types)
SON = {0x6a3cc}                                  # son du PSP (table 0x217FD8 + pilote audio) : pas d'équivalent direct
# champs PROPRES À MAX : 0xAA -> $3F0, 0x1EA -> $3F2 (dans HORS_MAX) logés en fin de structure (HSFA : jamais écrits en combat ;
                                             # code arcade : aucun accès d(An) à $3F0-$3F3). ⚠ $380-$397 est pris (MOVEM 0x6EFD2)
# prolongements de zones (paire $2EF6C/0x68A2C : 0x88 <-> $68, 0x139 <-> $F0 ; vote différentiel : 0x24F <-> $26F)
for _p in range(0x88, 0xA0): HORS.setdefault(_p, _p - 0x20)
for _p in range(0x134, 0x140): HORS.setdefault(_p, _p - 0x49)
for _p in range(0x23E, 0x270): HORS.setdefault(_p, _p + 0x20)
HORS[0x53] = 0x3B; HORS[0x119] = 0xDD; HORS[0x26] = 0x26   # tester_ecarts.py : écarts de zone soutenus par la vérité arcade
HORS[0xEA] = 0xAA                            # arcade 0x346B4 / PSP 0xCF490 : $AA (×2) <-> 0xEA, $A9 <-> 0xEB
HORS[0xE4] = 0xA4; HORS[0x2BA] = 0x2CA       # prolongements de zones (vote différentiel : 4/4, 6/31)
# variables de travail PROPRES À CHAQUE PERSO (union C, rangement différent par perso) : pour les persos MAX, logées en
# fin de structure (libre en combat d'après HSFA ; à confirmer dans ro3/ro5 pour $3C0-$3E5)
HORS_MAX = {0x334 + 4 * _k: 0x3C0 + 4 * _k for _k in range(7)}       # allocations PROPRES AUX PERSOS MAX (union de travail)
HORS_MAX.update({0xAA: 0x3F0, 0x1EA: 0x3F2})   # (2026-10-07) 0x2FA/0x2FC retirés : champs d'ENTRÉE (PPSSPP)
# (2026-10-27, Q16.3) PSP 0x305 = compteur « en l'air depuis un saut » du MOTEUR (++ au départ du saut si +0xEE,
# remis à 0 à l'atterrissage) = arcade $32D (même code : $286CE tst.b $AC / addq.b #1,$32D / clr.b $270 ; image
# Upper $32C) ; avant : $3E4, que personne n'écrivait chez un adversaire natif
HORS[0x305] = 0x32D
# (2026-10-07) persos MAX : MIROIR des entrées au format PSP (psp_entrees, moteur_max_main.s, à appeler à chaque image) :
# PSP 0x2F0 -> $3E0, 0x2F8 -> $3E2, 0x2FA -> $3E6, 0x2FC -> $3E8 (mots, lus en 16 bits) ; constantes PSP inchangées
HORS_MAX.update({0x2F0: 0x3E0, 0x2F8: 0x3E2, 0x2FA: 0x3E6, 0x2FC: 0x3E8})
# (2026-10-07) PSP 0x318 = mot d'OPTIONS de console (rempli par 0x61540 depuis les réglages du mode ; 0 en jeu normal,
# vérifié sous PPSSPP) : long réservé, toujours nul côté arcade (à confirmer libre : $3EC-$3EF)
HORS_MAX.update({0x318: 0x3EC})
HORS_MAX.pop(0x10E, None)                    # champ moteur ($D6), pas une variable propre à MAX
# PSP 0x330 (long, écrit par les réactions aux coups 0x58A48/0x61DDC/0x607C4, lu par 0x68380 = contre-alpha) : sans
# équivalent arcade identifié -> lu comme nul ($3EC, toujours 0) ; à revoir au banc
HORS_MAX.update({0x330: 0x3EC})
# champs PSP sans équivalent arcade trouvé (C restructuré / propres à MAX) : logés en $332-$367 (HSFA : libre dans ro5 ;
# ro3 écrit MOVE.B D0,$330(A6) en 68K $44460 -> on commence à $332) — si le moteur arcade lit l'un d'eux sous un autre
# nom, le banc le montrera
_ALLOC = [(0x28, 4), (0x2C, 4), (0x30, 4), (0x34, 4), (0xA4, 4), (0x124, 4), (0x2C4, 4), (0x118, 4),
          (0x1A, 2), (0x54, 2), (0x56, 2), (0xE8, 2), (0x10C, 2), (0x11E, 2),
          (0xA0, 1), (0xAB, 1), (0xFF, 1), (0x10A, 1), (0x10E, 1), (0x147, 1), (0x1EB, 1), (0x1EC, 1), (0x1ED, 1), (0x27A, 1)]
_ad = 0x332
for _p, _t in _ALLOC:
    if _t > 1 and _ad % 2: _ad += 1
    HORS_MAX[_p] = _ad; _ad += _t
assert _ad <= 0x370, hex(_ad)
PRIORITE_MAX = {0x16A: 0x3E0}            # (2026-10-07) boutons TENUS au format PSP (0x16C = image précédente ; 0x63794 :
                                         # appuyés = 0x16A & ~0x16C) -> miroir des entrées $3E0 (mot) ; avant : octet $11A
HORS_MAX.update({0x1E2: 0x362, 0x1E3: 0x3F3})   # (2026-10-07) 0x77E00 (variante d'attaque MAX) : $362 libéré par 0x10E
HORS_MAX.pop(0x10E, None)                    # (2026-10-07) l'emplacement reste réservé, mais 0x10E = champ moteur $D6 (le retrait
                                             # fait plus haut était annulé par cette boucle)
MODE_MAX = True                                                      # False : évaluation sur les persos arcade (vérité)
HORS[0x5C] = 0x38; HORS[0x58] = 0x36        # pointeurs adversaire / propriétaire (mot côté 68K)
HORS[0x1C] = 0x1C; HORS[0x0] = 0x0       # pointeur du pas d'animation (lu dans 0x5D63C) ; état de l'objet
HORS[0x334] = 0x1FE                          # Ryu (paire 0x34F64) ; pour les persos MAX : HORS_MAX (union de travail)
                      # vu dans la paire Ryu 0x34F64 / 0xEBAE4 (compteur élargi en 32 bits)
TAILLE = {int(o, 16): s for o, s in json.load(open("tailles68.json")).items()}
ARITE = {int(t, 16): a for t, a in json.load(open("arite.json")).items()}
TAILLE[0x38] = TAILLE[0x36] = 2              # pointeurs (adresses RAM courtes)
TAILLE[0x3F0] = 1; TAILLE[0x3F2] = 2
for _k in range(7): TAILLE[0x3C0 + 4 * _k] = 4
TAILLE[0x2C] = TAILLE[0x2E] = TAILLE[0x20] = 2      # liens 16 bits / mot des objets fils (aucun champ joueur ici)
TAILLE[0x3E0] = TAILLE[0x3E2] = 2; TAILLE[0x3E4] = 1
TAILLE[0xA4] = 2       # (2026-10-07) $A4 = pointeur 16 bits vers le projectile du joueur (arcade : move.w a4,$a4(a6))
for _p, _t in _ALLOC:
    if _p in HORS_MAX: TAILLE[HORS_MAX[_p]] = _t      # arguments a1..a3 (arite.py)
for _o in (0x332, 0x336, 0x33A, 0x33E): TAILLE[_o] = 2       # liens 16 bits du joueur (LIENS_JOUEUR)
for _o in (0x3E0, 0x3E2, 0x3E6, 0x3E8): TAILLE[_o] = 2      # miroir des entrées (mots)
TAILLE[0x3EC] = 4                                            # options de console PSP (long, nul)
ETATS = {4, 5, 6, 7, 0x80, 0x82, 0xAA, 0x248, 0x2A0, 0x2C4}   # (2026-10-25, Q12 : $248 = PSP 0x228, niveau de super ; clés = décalages 68K) champs « ×2 » (PSP n = 68K 2n), mesurés sur les paires (≥ 3 votes)
# (2026-10-07) facteur d'échelle par champ ; $E (plan de caméra) ×4 : PSP indexe la table 0x20A05C par $E×4 (0x1D330),
# l'arcade lit la table $1BD96 par $E directement (valeurs 0/4/8/12) ; parallaxe PSP $E = 2 <-> arcade $E = 8 ($1BD68)
FACTEUR = {o: 2 for o in ETATS}; FACTEUR[0xE] = 4
FACTEUR[0xBD] = 2                   # classe de projectile (PSP 0xFF, contexte objet fils) ; aucun champ joueur ne vise $BD
DECAL = {2: 1, 4: 2}
ALLOC = {0x1EEAC: 0x1C2C8}                  # PSP alloc(type, sous-type) -> nouvel objet ; arcade JSR alloc -> A4 (Z si échec)
# (2026-10-07) réservoirs d'objets : appariés par le code de type écrit dans $8 à la libération (PSP × 4 = arcade) ;
# volumes d'appels cohérents (ex. effets : PSP 82 allocations / 62 libérations, arcade 50 / 34). Compteurs PSP
# 0xA3E7C2-C6 <-> arcade $6EB8-$6EBC(A5) (sauf C4/C5 croisés, cf. types).
ALLOC.update({0x1EE74: 0x1C278, 0x1EEE4: 0x1C3AC, 0x1EF1C: 0x1C318, 0x1EF54: 0x1C368})
# (2026-10-07) 0x1ED2C (projectile) = $1C1C8 : c'est aussi une ALLOCATION (-> A4, Z si échec ; réservoir du camp $59,
# objets de $100 libérés par $1C206), pas une fonction à valeur de retour. En-tête arcade d'un projectile : $0 = 1,
# $2 = n° du PERSO (aiguillage $32F46[$2] et animations $3327A[$2] ; Ryu $34D62 : move.w #$0,$2(a4)) ; $3 écrit par le
# créateur (PSP : a1 = code de type d'objet du module, a2 = ?).
ALLOC_PERSO = {0x1ED2C: 0x1C1C8}
ALLOC.update(ALLOC_PERSO)
LIBERE = {0x1F19C: 0x1C28E, 0x1F1C8: 0x1C2DE, 0x1F1F4: 0x1C3C2, 0x1F220: 0x1C32E, 0x1F24C: 0x1C37E}
                                            # puis MOVE.L #$0100ttss,(A4) (octets $0-$3 : actif, 0, type, sous-type)
PTR = {0x5C: 0x38, 0x58: 0x36, 0xE4: 0xA4}      # pointeurs d'objets (mots côté 68K) : adversaire, propriétaire, projectile
# octets d'un pas d'animation 68K (ROM arcade, vérifié sur les données : routine 0x2A770 et pas réels) :
# +0 durée, +1 drapeaux de fin (bit 7 reprise via +$14, bit 6 fin), +2/+3 mot « drapeau » ; +4 ptr frame (long BE) ;
# +8..+$13 = mots A, B, C dans l'ORDRE DES OCTETS DU PSP (entrée de boîtes recopiée telle quelle). Mêmes octets que le PSP.
PAS_OCTETS = {0: 0, 1: 1, 2: 2, 3: 3}              # champs pointeurs : PSP (long) -> 68K (mot, adresse RAM courte) ; 0x5C 79 votes
# (2026-10-07) globales PSP lues comme nulles : 0x39CA2A (mode spécial ; PPSSPP : 0 pendant tout le mode arcade, démos
# comprises) -> liste complète des coups d'Ingrid
GLOB_ZERO = {0x39CA2A}
JOUEURS_PSP, TAILLE_JOUEUR_PSP = 0x80AF70, 0x498   # 0x213F88[k] = 0x80AF70 + 0x498 k ; arcade $FF8400 + $400 k
GLOB_A5 = 0x8081F8                          # variables globales : $n(A5) = adresse PSP - 0x8081F8 (36 votes)
SUF = {1: ".b", 2: ".w", 4: ".l"}
MASQUE = {".b": 0xFF, ".w": 0xFFFF, ".l": 0xFFFFFFFF}
BR = {"beq": "beq", "beql": "beq", "bne": "bne", "bnel": "bne", "bgez": "bpl", "bgezl": "bpl", "bltz": "bmi",
      "bltzl": "bmi", "blez": "ble", "blezl": "ble", "bgtz": "bgt", "bgtzl": "bgt"}
LD = {"lb": 1, "lbu": 1, "lh": 2, "lhu": 2, "lw": 4}
ST = {"sb": 1, "sh": 2, "sw": 4}

_REFS = None
def refs_code():
    """adresses construites par lui/addiu dans tout .text (débuts de tables référencées par le code)"""
    global _REFS
    if _REFS is None:
        from relocs import TEXT_END
        import struct
        W = struct.unpack_from("<%dI" % (TEXT_END // 4), img, 0); _REFS = set()
        for k, w in enumerate(W):
            if w >> 26 != 0x0F: continue
            rt, hi = (w >> 16) & 31, w & 0xFFFF
            for x in W[k + 1:k + 8]:
                if (x >> 21) & 31 == rt and x >> 26 == 0x09:
                    lo = x & 0xFFFF; _REFS.add(((hi << 16) + (lo - 0x10000 if lo & 0x8000 else lo)) & 0xFFFFFFFF); break
    return _REFS

# (2026-10-07) OBJETS FILS / PROJECTILES (arcade : $1C1C8, objets de $100 octets, gérés par $32EFA via $32F46[perso]) :
# même carte que le joueur (en-tête, $60/$88 tables d'animation, $CC/$EE/$EF clignotement, $50 solidité) SAUF :
#   0xFF -> $BD (classe au choc de deux projectiles, $24E10 ; valeur ×2 : 3/5/6 <-> 6/10/12 chez tous les persos),
#   0x158/0x15A/0x15B -> $70/$72/$73 (0x72744 <-> $33120, création du Hadoken 0xEC148 <-> $34D62) ;
#   0xAA/0xAB : réglages d'affichage PSP (recopiés dans l'enregistrement de sprite, 0x8514) ; 0x164 : table des JEUX DE
#   BOÎTES du tir (lue par 0x72894 : octet 0 = index $88, octet 1 = attaque ; rectifié 2026-10-17) -> sans objet en 68K :
#   ses entrées sont recopiées dans les pas des scripts du tir (tables_explicites.py, BOITES_TIRS).
# Contexte : routines dont A6 est un objet fils (proj_fn), objet neuf (A4, allocations dont 0x1ED2C).
PROJ = {0xFF: 0xBD, 0x158: 0x70, 0x15A: 0x72, 0x15B: 0x73}
# champs propres aux objets d'Ingrid (sans équivalent arcade), logés dans des octets que le code des projectiles arcade
# n'emploie pas ($72BA0-$7C000, $32EF0-$33300, choc $24D70) et qu'aucun champ joueur ne vise — à valider au banc :
# 0x28/0x2C/0x30/0x34 = liens entre objets (effets attachés, listes : 0x1C6D58, 0x1C70D8, 0x1C8CE0…) -> POINTEURS 16 BITS
# (adresses d'objets arcade = mots) en $28/$2A/$2C/$2E (les effets $1C368 n'ont que $80 octets) ; 0x54 (mot) -> $20.
PROJ.update({0x28: 0x28, 0x2C: 0x2A, 0x30: 0x2C, 0x34: 0x2E, 0x54: 0x20})
LIENS16 = {0x28, 0x2A, 0x2C, 0x2E}
# liens du JOUEUR vers ses effets (Ingrid 0x1C8720 à l'init : 3 effets accrochés en 0x28/0x2C/0x30) : mêmes pointeurs
# 16 bits, dans les emplacements MAX $332/$336/$33A/$33E (premier mot de chaque long réservé)
PTR_TABLES = {0x2C4: 0x34A}    # (2026-10-07) pointeurs longs vers des tables au format PSP (données recopiées)
LIENS_JOUEUR = {0x28: 0x332, 0x2C: 0x336, 0x30: 0x33A, 0x34: 0x33E}
PROJ_SANS = {0xAA, 0xAB, 0x164, 0x56, 0xA4}
ALPHA_SITES = []   # (2026-10-18) sites d'écriture de PSP +0xAA traduits vers MAX_ALPHA (rapport)   # + 0x56 / 0xA4 : attributs d'affichage lus par le traceur PSP (0x8408)
PROJ_SANS.add(0x94)   # (2026-10-10) long lu par le traceur PSP 0x8408 (0x842C) : Ingrid type 0x37 écrit 3 -> omis (relevé HSFA)
PROJ_SANS.add(0x118)  # (2026-10-27) Ingrid 0x1C7750 : octet +0x118 de l'objet neuf de type 0x2D (n° d'ordre 0x296), jamais relu
                      # par le code MAX ; traduit avec la carte joueur, il visait $34E(a4) = HORS de l'objet projectile -> omis
SANS_OBJET = "<sans objet>"
# (2026-10-07) champs JOUEUR écrits par le code MAX, lus seulement par le moteur PSP (pas de lecteur apparié à l'arcade) :
# 0x38 = effet attaché à l'adversaire (Eagle, objet 0x33 : 0x1B3970 / 0x1B3BC0) -> écritures omises
JOUEUR_SANS = {0x38}
# (2026-10-11, agent_integration_max) 0x2CA-0x2D0 = position d'impact propre au PSP (recopiée de 0x2D8-0x2DE par
# psp_1b24a8 d'Eagle, jamais atteinte ; lue seulement par l'étincelle psp_cf858, neutralisée) -> écritures omises
JOUEUR_SANS |= {0x2CA, 0x2CC, 0x2CE, 0x2D0}
JOUEUR_SANS |= {0x252}
JOUEUR_SANS |= {0xEA}       # (2026-10-18) PSP 0xEA (effacé au début d'un spécial par 0xCF490 ; ↔ $AA de l'arcade, Rosette $346B4) :
                            # chez les MAX, $AA porte le n° de spécial PSP 0xEC. Effacer 0xEA en $AA au milieu d'un spécial
                            # (riposte du contre d'Ingrid : psp_1c3ec0 -> psp_cf490) renvoyait le dispatcher au spécial 0.
                            # Le code MAX ne lit jamais 0xEA (9 écritures, 0 lecture) : écritures omises.      # (2026-10-17) masque PSP des joueurs touchés (0x6CA58) : pas tenu par l'arcade ($272 = autre champ) ; psp_d014c écrite sans lui
CTX = {"proj": False, "acteur": False}
# (2026-10-10) ACTEURS DE FIN (objets du réservoir $1C2C8, classes $48-$50) : champs PSP -> arcade relevés sur le
# générateur PSP 0x1DBEDC (homologue de $27556 : recopie des enregistrements de 32 o dans l'objet)
ACTEUR = {0x0B: 0x0B, 0x0C: 0x0C, 0x0D: 0x0D, 0x09: 0x09, 0x18: 0x18, 0x74: 0x70, 0x75: 0x76, 0x76: 0x78, 0x77: 0x79,
          0x78: 0x7A, 0x50: 0x7B, 0x88: 0x7C, 0x89: 0x7D, 0x8A: 0x7E, 0x49: 0x7F, 0x70: 0x72, 0x72: 0x74,
          0x60: 0x40, 0x64: 0x44, 0x68: 0x48, 0x6C: 0x4C, 0x10: 0x10, 0x12: 0x10, 0x14: 0x14, 0x16: 0x14, 0x58: 0x36,
          0x00: 0x00, 0x01: 0x01, 0x02: 0x02, 0x03: 0x03, 0x04: 0x04, 0x05: 0x05, 0x06: 0x06, 0x07: 0x07,
          0x20: 0x20, 0x22: 0x22,      # 0x20/0x22 : sauvegarde X/Y (MAX) -> $20/$22, jamais employés par le code d'acteurs arcade
          # (2026-10-10, retour HSFA) position privée 16.16 des acteurs $4F/$19 (PSP 0x7C X, 0x80 Y ; partie entière en
          # +2) -> longs $5C / $60 : octets $5C-$67 jamais touchés par la classe $4F ($AAE04-$AC15E), le moteur
          # générique d'objets ($1A000-$1D000), le générateur $2750E ni la classe $48. ($28-$2F, essayés d'abord :
          # employés par le moteur générique et effacés par la libération $1C2DE -> exclus)
          0x7C: 0x5C, 0x7E: 0x5C, 0x80: 0x60, 0x82: 0x60}
# 2e argument des comportements d'acteurs PSP (a1) = structure d'état de la fin -> globales A5 arcade
FIN_GLOB = {0x02: 0x1C8, 0x04: 0x1CA,
            # scène demandée par un acteur (homologue de l'opcode x1 : $27288 puis $25FC6) : positions courantes et
            # nouvelles = -$50FA/-$50F8/-$50F6 (défilement scroll1/2/3), drapeau « scène à appliquer » = -$5107
            0x70: -0x50FA, 0x72: -0x50F8, 0x74: -0x50F6, 0x90: -0x50FA, 0x92: -0x50F8, 0x94: -0x50F6, 0x6B: -0x5107}
# (2026-10-10) plans, en contexte acteur : structures de couches PSP 0xA46A20 + 0x98·k (X 16.16 en +8, Y en +$C) =
# accumulateurs arcade $210/$214 (scroll1), $290/$294 (scroll2), $310/$314 (scroll3) ; registres de rendu PSP
# 0x80F8D0 / 0x80F970 / 0x80FA10 (+$10 X, +$14 Y, longs 16.16) = ombres arcade en MOTS $22/$24, $26/$28, $2A/$2C
# (pseudo-décalage $F000 + ombre, réécrit par acteurs_fins.post : partie entière <-> 16.16)
COUCHES_ACTEUR = {}
for _k, (_acc, _omb) in enumerate(((0x210, 0x22), (0x290, 0x26), (0x310, 0x2A))):
    _c = 0xA46A20 + 0x98 * _k; _r = (0x80F8D0, 0x80F970, 0x80FA10)[_k]
    COUCHES_ACTEUR.update({_c + 8: _acc, _c + 0xA: _acc, _c + 0xC: _acc + 4, _c + 0xE: _acc + 4,
                           _r + 0x10: 0xF000 + _omb, _r + 0x12: _omb, _r + 0x14: 0xF000 + _omb + 2, _r + 0x16: _omb + 2})
def api_acteurs():
    """(2026-10-10) fonctions du moteur d'acteurs PSP -> arcade : apprises (appris_acteurs.py) + relevées à la main"""
    d = {0x1D4C48: 0xAA630, 0x1D3810: 0xAA5D2}      # classe $4B, partie commune (1CB5B4 <-> $A7576)
    try: d.update({int(k, 16): int(v[1:], 16) for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_acteurs.json"))).items()})
    except FileNotFoundError: pass
    return d
# (2026-10-17) ACCÈS DE TAILLES MÊLÉES (demande HSFA : course de Maki) : un champ PSP écrit en demi-mot (sh +0x3A) et lu
# en octet (lb +0x3A) -> l'octet lu est l'octet BAS (petit-boutiste), soit la FIN du champ côté 68K (gros-boutiste) :
# $3A(a6) lisait l'octet haut (toujours 0). Tailles d'accès relevées sur le joueur (pas les objets fils ni les acteurs)
# pendant la génération (acces_psp.json, 2 passes : brouillons.py relance si le relevé change) ; un accès plus étroit que
# l'accès le plus large au même champ vise les octets de poids faible : o(q) + W - sz - k (q = début du champ, W = sa
# taille PSP, k = rang de l'octet PSP dans le champ). Zones « +2 » (positions 16.16) exclues.
ACCES_F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acces_psp.json")
try: ACCES = {int(k, 16): set(v) for k, v in json.load(open(ACCES_F)).items()}
except FileNotFoundError: ACCES = {}
ACCES_VUS = collections.defaultdict(set)
# écritures en demi-mot (sh) des champs du joueur : décalages 68K (le sh est rendu en MOVE.W) ; une lecture de ces champs
# n'est pas réduite à l'octet que l'arcade y range (TAILLE = 1), sinon elle lirait l'octet HAUT du mot écrit
try: ECRITS_MOT = set(json.load(open(ACCES_F + ".ecritures")))
except FileNotFoundError: ECRITS_MOT = set()
ECRITS_VUS = set()
def sauver_acces():
    """-> True si le relevé a changé (il faut alors relancer la génération)"""
    d = {k: set(v) for k, v in ACCES_VUS.items()}
    json.dump({"%x" % k: sorted(v) for k, v in sorted(d.items())}, open(ACCES_F, "w"), indent=0)
    json.dump(sorted(ECRITS_VUS), open(ACCES_F + ".ecritures", "w"))
    change = d != ACCES or ECRITS_VUS != ECRITS_MOT
    ACCES.clear(); ACCES.update(d); ACCES_VUS.clear(); ECRITS_MOT.clear(); ECRITS_MOT.update(ECRITS_VUS); ECRITS_VUS.clear()
    return change
def _zone_plus2(p):
    return any(d == 2 and o0 <= p <= o1 + 3 for o0, o1, p0, d in SEGS)
def champ(p, sz=None, proj=None):
    """décalage PSP -> (texte 68K, décalage 68K ou None) ; accès étroit d'un champ plus large -> octets de poids faible"""
    joueur = not CTX.get("acteur") and not (CTX["proj"] if proj is None else proj)
    if joueur and sz in (1, 2, 4): ACCES_VUS[p].add(sz)
    t, o = _champ(p, sz, proj)
    if not joueur or sz not in (1, 2) or o is None or _zone_plus2(p): return t, o
    for q in range(p, p - 4, -1):
        W = max(ACCES.get(q, {0}))
        if W in (2, 4) and W > sz and q % W == 0 and q <= p and p + sz <= q + W:
            if q != p and (q in ACCES and max(ACCES[q]) <= p - q): continue
            tq, oq = _champ(q, W, proj)
            if oq is None or "(a6)" not in tq: return t, o
            if q != p and o != oq + (p - q): return t, o     # octet logé ailleurs (HORS_MAX…) : champ distinct
            n = oq + W - sz - (p - q)
            return "$%x(a6)" % n, n
        if q != p and q in ACCES: break
    return t, o
def _champ(p, sz=None, proj=None):
    """décalage PSP -> (texte 68K, décalage 68K ou None)"""
    if CTX.get("acteur") and proj is not False:
        if p in ACTEUR: return "$%x(a6)" % ACTEUR[p], ACTEUR[p]
        proj = True                      # autres champs : objet fils générique (même famille d'objets de $80 o)
    if CTX["proj"] if proj is None else proj:
        if p in PROJ: return "$%x(a6)" % PROJ[p], PROJ[p]
        if p in PROJ_SANS: return SANS_OBJET, None
    elif MODE_MAX and p in JOUEUR_SANS: return SANS_OBJET, None
    if MODE_MAX and p in PRIORITE_MAX: return "$%x(a6)" % PRIORITE_MAX[p], PRIORITE_MAX[p]   # avant les segments
    if sz == 4:                                   # long dans la zone « +2 » : même décalage (petit-boutiste)
        for o0, o1, p0, d in SEGS:
            if d == 2 and o0 <= p <= o1: return "$%x(a6)" % p, p
    for o0, o1, p0, d in SEGS:
        if o0 + d <= p <= o1 + d:
            o = p - d
            return "$%x(a6)" % o, o
    if MODE_MAX and p in HORS_MAX: return "$%x(a6)" % HORS_MAX[p], HORS_MAX[p]
    if p in HORS: return "$%x(a6)" % HORS[p], HORS[p]
    return "??psp_%#x(a6)" % p, None

class V:
    def __init__(s, k, a=None, b=None, sz=None): s.k, s.a, s.b, s.sz = k, a, b, sz
    def __repr__(s):
        if s.k == "c": return "#$%x" % (s.a & 0xFFFFFFFF)
        if s.k == "f": return champ(s.a, s.sz)[0]
        if s.k == "obj": return "a6"
        if s.k == "ret": return "<retour d0>"
        if s.k == "arg": return "<arg d%d>" % s.a
        if s.k == "a4": return "<nouvel objet a4>"
        if s.k == "phi": return "<jonction %s>" % s.a
        if s.k == "reg": return "<%s>" % s.a
        return "(%s %s %s)" % (s.a, s.k, s.b)

# (2026-10-10) acteurs de fin : $78-$7F = octets NON SIGNÉS (repères, comparés en arcade par moveq #0 / move.b /
# cmp.w $1C8(A5)) ; $5C/$60 = position privée 16.16 des acteurs $4F/$19 (PSP 0x7C/0x80)
TAILLE_ACTEUR = {**{o: 1 for o in range(0x78, 0x80)}, 0x5C: 4, 0x60: 4}
ETAT_FIN = 0x87FCB0
def fin_off(v):
    """v = lecture d'un champ de l'état de fin PSP (constante 0x87FCB0 + n, ou 2e argument + n en contexte acteur) -> n"""
    if v.k != "mem": return None
    a = v.a
    if a.k == "c" and 0 <= a.a - ETAT_FIN < 0x200: return a.a - ETAT_FIN
    if a.k == "+" and a.b.k == "c":
        if a.a.k == "c" and a.a.a == ETAT_FIN: return a.b.a
        if a.a.k == "arg" and a.a.a == 0 and CTX.get("acteur"): return a.b.a
    return None
def decaler(t, k):
    """opérande mémoire 68K avancé de k octets ($n(aX), -$n(aX), ($n).l) ; inchangé sinon"""
    m = re.match(r"^(-?)\$([0-9a-f]+)\((a[0-7])\)$", t)
    if m:
        v = (-1 if m.group(1) else 1) * int(m.group(2), 16) + k
        return ("-$%x(%s)" if v < 0 else "$%x(%s)") % (abs(v), m.group(3))
    m = re.match(r"^\(\$([0-9a-f]+)\)\.l$", t)
    if m: return "($%x).l" % (int(m.group(1), 16) + k)
    return t
def taille_lecture(o, psz):
    """taille d'une lecture : la plus petite de la taille PSP et de la taille 68K usuelle (le C a élargi certains champs ;
    l'arcade accède parfois en long à un champ lu octet par octet) ; positions longues ($10-$14) : 4"""
    if o is not None and o % 2 and psz > 1: return 1     # (2026-10-07) champ à adresse impaire : jamais d'accès mot/long
    if psz == 2 and o in ECRITS_MOT and not CTX.get("acteur"): return 2   # (2026-10-17) champ écrit en mot par le code MAX
    t = TAILLE.get(o) if o is not None else None
    if CTX.get("acteur") and o in TAILLE_ACTEUR: t = TAILLE_ACTEUR[o]
    if CTX.get("acteur") and psz == 2 and t == 1 and o not in TAILLE_ACTEUR: return 2   # (2026-10-18) demi-mot PSP d'un
    # acteur que la table du JOUEUR réduisait à un octet ($3A : compteur décrémenté en mot puis testé sur son octet haut)
    if t is None: return psz
    if psz == 4 and t == 2 and o is not None and 0x10 <= o <= 0x17: return 4
    return min(t, psz)

def mnem(i):
    if i.m == "regimm": return {0: "bltz", 1: "bgez", 2: "bltzl", 3: "bgezl"}.get(i.rt, "regimm")
    if i.op == 0x16: return "blezl"
    if i.op == 0x17: return "bgtzl"
    return i.m

def _sig(c): return c - (1 << 32) if c & 0x80000000 else c
_TC = None
def _cas_de_table(c):
    """autres cibles de la (des) table(s) de données qui contiennent la valeur c"""
    global _TC
    if _TC is None:
        from charcode2 import P
        import collections
        adr = sorted(P); _TC = collections.defaultdict(set)
        bloc = []
        for a in adr:                                    # tables = mots consécutifs
            if bloc and a != bloc[-1] + 4:
                vs = {P[x] for x in bloc}
                for v in vs: _TC[v] |= vs
                bloc = []
            bloc.append(a)
        vs = {P[x] for x in bloc}
        for v in vs: _TC[v] |= vs
    return _TC.get(c, set())
_VP = None
def _valeurs_pointeurs():
    """valeurs des mots de données (charcode2.P) : cibles possibles de switch"""
    global _VP
    if _VP is None:
        from charcode2 import P
        _VP = set(P.values())
    return _VP
DONNEES = {}                # tables de données PSP lues par les persos MAX : début -> {(décalage, taille)}
def ecrire_donnees(f="donnees_max.s"):
    """recopie les tables de DONNEES en gros-boutiste (taille d'élément = taille d'accès si unique ; sinon octets)"""
    refs = sorted(refs_code()); out = ["; Tables de données PSP lues par les persos MAX (recopiées en gros-boutiste) — traduire.py\n"]
    for d in sorted(DONNEES):
        tailles = {t for _, t in DONNEES[d]}
        suiv = [r for r in refs if r > d]
        fin = max(min(suiv[0] if suiv else d + 0x40, d + 0x200), d + max(o + t for o, t in DONNEES[d]))
        t = tailles.pop() if len(tailles) == 1 else 1
        if len(DONNEES[d]) and len({x for _, x in DONNEES[d]}) > 1: out.append("; ⚠ tailles d'accès mêlées : octets")
        out.append("TABD_%x:   ; PSP %#x..%#x, accès %s" % (d, d, fin, sorted(DONNEES[d])))
        fmt = {1: "<B", 2: "<H", 4: "<I"}[t]; vals = []
        for a in range(d, fin - t + 1, t):
            v = struct.unpack_from(fmt, img, a)[0]
            vals.append(("$%x" % v) + (" ; ⚠ pointeur PSP ?" if t == 4 and 0x100000 <= v < len(img) else ""))
        for k in range(0, len(vals), 8):
            ligne = vals[k:k + 8]
            if any(";" in v for v in ligne): out += ["        dc.%s    %s" % ({1: "b", 2: "w", 4: "l"}[t], v) for v in ligne]
            else: out.append("        dc.%s    %s" % ({1: "b", 2: "w", 4: "l"}[t], ", ".join(ligne)))
    open(f, "w").write("\n".join(out) + "\n")
    return len(DONNEES)

class Trad:
    def __init__(s, f, end=None):
        e = end or fend(f)
        if end is None:                                      # (2026-10-07) cas de switch placés après le saut indirect
            from charcode2 import P
            vus = set()
            while True:
                L_ = list(decode(img, f, e)); cas = []
                for k_, x in enumerate(L_):
                    if x.m != "jr" or x.rs == 31 or x.va in vus: continue
                    vus.add(x.va)
                    for y in reversed(L_[max(0, k_ - 4):k_]):            # lw at,lo(at) ; lui at,hi juste avant
                        if y.m == "lw" and y.rt == x.rs:
                            for z in reversed(L_[max(0, k_ - 8):k_]):
                                if z.m == "lui" and z.rt == y.rs:
                                    t = ((z.imm << 16) + y.simm) & 0xFFFFFFFF; n_ = 0
                                    while t + 4 * n_ in P and f <= P[t + 4 * n_] < f + 0x2000: cas.append(P[t + 4 * n_]); n_ += 1
                                    break
                            break
                cas = [c for c in cas if c >= e]
                if not cas: break
                e = max(fend(c) for c in cas)
        s.f = f; s.ins = list(decode(img, f, e))
        s.out, s.R, s.obj, s.tramp = [], {5: V("arg", 0), 6: V("arg", 1), 7: V("arg", 2)}, {4}, []
        s.pile, s.tables_pile = {}, []
        # (2026-10-07) entrée au milieu d'une routine (cible de table de saut, sans prologue) : s0 = objet (prologue
        # parent « or s0,a0,zero », convention des modules MAX)
        if s.ins and not (s.ins[0].m == "addiu" and s.ins[0].rt == 29 and s.ins[0].rs == 29): s.obj.add(16)
        s.entrants = {}
        s.etats_label = {}                    # étiquette -> états entrants (fall-through compris)
        s.n_entrants = {}
        s.phi = {}                            # 2e passe : étiquette -> {registre MIPS: registre 68K de jonction}
        s.sous = set()
        s.tables = []                         # tables de saut d'états : (étiquette, [gestionnaires PSP])                        # fonctions PSP sans équivalent connu : traduites à part (sous-routines)                       # étiquette -> [états (R, obj)] des sauts qui y mènent
    def emit(s, x):
        if x.startswith("movea") and s.out and s.out[-1].strip() == x.strip(): return     # pointeur déjà chargé
        s.out.append("        " + x)
    def val(s, r):
        if r == 0: return V("c", 0)
        if r in s.obj: return V("obj")
        return s.R.get(r, V("reg", REG[r]))
    def setr(s, r, v): s.R[r] = v; s.obj.discard(r)
    # ---- écriture d'un champ
    def store(s, off, sz, v):
        s._store(off, sz, v)
        # (2026-10-17, projectile d'Ingrid L_1c7b94) écriture EN PLACE (champ ± c, -champ) : le champ contient maintenant v ;
        # les registres qui gardent l'expression v sont rebranchés sur le champ (sinon un test ultérieur relit le champ
        # déjà modifié et rejoue l'opération : décrément compté deux fois)
        en_place = (v.k in ("+", "-") and getattr(v.a, "k", None) == "f" and v.a.a == off and getattr(v.b, "k", None) == "c") \
            or (v.k == "-" and getattr(v.a, "k", None) == "c" and v.a.a == 0 and getattr(v.b, "k", None) == "f" and v.b.a == off)
        if en_place:
            src = v.a if v.a.k == "f" else v.b
            n = V("f", off, sz=sz); n.u = getattr(src, "u", False)
            def subst(x, vus):                       # v remplacé par le champ, y compris dans les sous-expressions
                if x is v: return n
                if not isinstance(x, V) or id(x) in vus or x.k in ("f", "c", "obj", "ret", "arg", "a4", "phi", "reg"): return x
                vus.add(id(x)); a, b = subst(x.a, vus), subst(x.b, vus)
                if a is x.a and b is x.b: return x
                y = V(x.k, a, b, x.sz); y.__dict__.update({k: w for k, w in x.__dict__.items() if k not in ("k", "a", "b", "sz")})
                return y
            for r, x in list(s.R.items()):
                y = subst(x, set())
                if y is not x: s.R[r] = y
    def alpha(s, base, v):
        """(2026-10-18, spécification HSFA) PSP +0xAA d'un objet -> MAX_ALPHA[(base.w − $9400) >> 7] (hors plage : rien)"""
        ALPHA_SITES.append(("%x" % s.f, base, str(v)))
        if v.k == "c": val = "#$%x" % (v.a & 0xFF)
        else:
            op = s.op68(v)
            if not op or op[0] in ("d0", "a0") or "(a0" in op[0]: s.emit("?? +0xAA (transparence) <- %s" % v); return
            val = op[0]
        n = "%x_%d" % (s.f, len(ALPHA_SITES))
        s.emit("movem.l d0/a0, -(sp)        ; PSP +0xAA (transparence) -> MAX_ALPHA[objet]")
        s.emit("move.w  %s, d0" % base); s.emit("subi.w  #$9400, d0"); s.emit("bcs.s   L_alpha_%s" % n)
        s.emit("cmpi.w  #$3C00, d0"); s.emit("bcc.s   L_alpha_%s" % n); s.emit("lsr.w   #7, d0")
        s.emit("lea     MAX_ALPHA.l, a0")
        s.emit(("clr.b   0(a0,d0.w)") if val == "#$0" else ("move.b  %s, 0(a0,d0.w)" % val))
        s.out.append("L_alpha_%s:" % n); s.emit("movem.l (sp)+, d0/a0")
    def _store(s, off, sz, v):
        if off == 0xAA and sz == 1 and (CTX["proj"] or CTX.get("acteur")): return s.alpha("a6", v)
        t, o = champ(off, sz); s68 = TAILLE.get(o, sz) if o is not None else sz
        if sz == 2 and o is not None and not CTX.get("acteur") and not CTX["proj"]: ECRITS_VUS.add(o)
        if t == SANS_OBJET: s.emit("; (champ PSP %#x : sans objet sur l'arcade)" % off); return
        if sz == 4 and s68 == 2 and not (CTX["proj"] and o in LIENS16): s68 = 4   # position/vitesse 32 bits (partie entière lue)
        if sz == 2: s68 = 2                          # écriture 16 bits côté PSP : mot côté 68K (les élargissements sont en 32 bits)
        if sz == 1: s68 = 1                          # écriture d'un octet : octet
        suf = SUF.get(s68, ".?"); mul = FACTEUR.get(o, 1) if s68 == 1 else 1
        if o in set(PTR.values()) | (LIENS16 if CTX["proj"] else set(LIENS_JOUEUR.values())) and v.k in ("a4", "obj", "ret", "arg", "phi"):
            if v.k == "arg": r = "ARG%dW" % v.a
            else: r = {"a4": "a4", "obj": "a6"}.get(v.k) or (s.op68(v)[0] if s.op68(v) else None)
            if r: s.emit("move.w  %s, %s          ; pointeur d'objet (mot)" % (r, t)); return
        if v.k == "c":
            c = (v.a * mul) & ((1 << (8 * s68)) - 1)
            s.emit(("clr%s     %s" % (suf, t)) if c == 0 else ("move%s    #$%x, %s" % (suf, c, t)))
        elif v.k == "+" and v.a.k == "f" and v.a.a == off and v.b.k == "c":
            c = v.b.a * mul
            if c & 0x80000000: c -= 1 << 32
            if -8 <= c < 0: s.emit("subq%s    #%d, %s" % (suf, -c, t))
            elif 0 < c <= 8: s.emit("addq%s    #%d, %s" % (suf, c, t))
            else: s.emit("addi%s    #$%x, %s" % (suf, c & 0xFFFFFFFF, t))
        elif v.k == "-" and v.a.k == "c" and v.a.a == 0 and v.b.k == "f" and v.b.a == off:
            s.emit("neg%s     %s" % (suf, t))
        elif v.k in ("mem", "ret") and s.op68(v) and {".b": 1, ".w": 2, ".l": 4}.get(s.op68(v)[1], 4) >= s68:
            ts, sfx = s.op68(v); k = {".b": 1, ".w": 2, ".l": 4}.get(sfx, 4) - s68
            p_ = getattr(s, "_p", None)
            if k > 0 and p_ is not None:
                # (2026-10-17) partie basse d'un champ PSP lu en long = demi-mot / octet PSP de MÊME décalage -> son propre
                # homologue arcade (champ(p, taille)), pas « décalage 68K + k » : faux quand chaque demi-mot PSP a son
                # champ arcade (étoiles d'Ingrid : PSP +0x18 attributs -> $18, et non $1A = emplacement de banque)
                t2, o2 = champ(p_, s68, getattr(s, "_proj", None))
                m_ = re.match(r"^-?\$[0-9a-f]+(\(a[0-7]\))$", ts)
                ts = ("$%x%s" % (o2, m_.group(1))) if (o2 is not None and m_) else decaler(ts, k)
            elif k > 0: ts = decaler(ts, k)
            s.emit("move%s    %s, %s" % (suf, ts, t))   # partie BASSE (gros-boutiste)
        elif v.k == "-" and v.a.k == "f" and v.a.a == off and v.b.k == "c":
            c = v.b.a * mul
            s.emit(("subq%s    #%d, %s" % (suf, c, t)) if 0 < c <= 8 else ("subi%s    #$%x, %s" % (suf, c & 0xFFFFFFFF, t)))
        elif v.k == "-" and v.a.k == "f" and v.b.k == "f" and v.a.a == off:
            s.charger_d0(v.b, suf); s.emit("sub%s     d0, %s" % (suf, t))
        elif v.k == "+" and v.a.k == "f" and v.b.k == "f" and off in (v.a.a, v.b.a):
            src = v.b if v.a.a == off else v.a
            s.charger_d0(src, suf); s.emit("add%s     d0, %s" % (suf, t))
        elif v.k == "f":
            # (2026-10-07) copie brute champ -> champ : tailles réelles (source plus petite : extension de signe ;
            # source plus grande : partie BASSE, gros-boutiste)
            ts_, os_ = champ(v.a, v.sz)
            n_src = {".b": 1, ".w": 2, ".l": 4}.get(SUF.get(taille_lecture(os_, v.sz), ".l"), 4)
            if os_ is not None and n_src < s68:
                s.emit("move%s  %s, d3" % (SUF[n_src], ts_))
                if n_src == 1: s.emit("ext.w   d3")
                if s68 == 4: s.emit("ext.l   d3")
                s.emit("move%s    d3, %s" % (suf, t))
            elif os_ is not None and n_src > s68:
                s.emit("move%s    $%x(a6), %s" % (suf, os_ + n_src - s68, t))
            else:
                s.emit("move%s    %s, %s" % (suf, ts_, t))
        elif s.calc(v):
            # (2026-10-17) valeur calculée (jonction de constantes, expression) rangée dans un champ ×n (numéros d'état) :
            # calc() rend la VALEUR PSP (lecture des champs ×n divisée) -> ×n avant l'écriture (Eagle, super $0A :
            # « +7 = 6 ou 4 » rangé tel quel -> sous-état $06 au lieu de $0C, bouclage sans fin)
            if mul > 1: s.emit("lsl%s   #%d, d3          ; valeur -> champ ×%d" % (suf, DECAL[mul], mul))
            s.emit("move%s    d3, %s" % (suf, t))
        else:
            s.emit("?? %s <- %s" % (t, v))
    # ---- une instruction « simple » (corps ou créneau) ; renvoie False si non reconnue
    def simple(s, i):
        m = mnem(i)
        # (2026-10-07) multiplications / divisions : HI/LO symboliques (68000 : MULS/DIVS 16 bits, cf. calc)
        if m in ("mult", "multu"):
            a_, b_ = s.val(i.rs), s.val(i.rt); s.LO = V("*", a_, b_); s.HI = V("*h", a_, b_); return True
        if m in ("div", "divu"):
            a_, b_ = s.val(i.rs), s.val(i.rt); s.LO = V("/", a_, b_); s.HI = V("%", a_, b_); return True
        if m == "mflo" and getattr(s, "LO", None) is not None: s.setr(i.rd, s.LO); return True
        if m == "mfhi" and getattr(s, "HI", None) is not None: s.setr(i.rd, s.HI); return True
        if m == "sw" and i.rs == 29:                          # (2026-10-07) constantes rangées sur la pile (tableaux locaux)
            v_ = s.val(i.rt)
            if v_.k == "c": s.pile[i.simm] = v_.a
            else: s.pile.pop(i.simm, None)
            return True
        if (m == "addiu" and i.rt == 29) or (m in ("sw", "lw") and i.rs == 29): return True
        if m == "sll" and i.w == 0: return True
        if m == "or" and i.fn == 0x25:
            if (i.rs in s.obj and i.rt == 0) or (i.rt in s.obj and i.rs == 0): s.obj.add(i.rd); s.R.pop(i.rd, None); return True
            src = i.rs if i.rt == 0 else (i.rt if i.rs == 0 else None)
            if src is not None: s.setr(i.rd, s.val(src)); return True
        if m in ("ori", "addiu") and i.rs == 0: s.setr(i.rt, V("c", i.simm & 0xFFFFFFFF if m == "addiu" else i.imm)); return True
        if m == "lui": s.setr(i.rt, V("c", i.imm << 16)); return True
        if m in ("ori", "addiu") and s.val(i.rs).k == "c":
            s.setr(i.rt, V("c", (s.val(i.rs).a + (i.simm if m == "addiu" else i.imm)) & 0xFFFFFFFF)); return True
        if m in LD and i.rs in s.obj:
            v = V("f", i.simm, sz=LD[m]); v.u = m in ("lbu", "lhu"); s.setr(i.rt, v); return True
        if m == "addiu": s.setr(i.rt, V("+", s.val(i.rs), V("c", i.simm & 0xFFFFFFFF))); return True
        if m == "addu": s.setr(i.rd, V("+", s.val(i.rs), s.val(i.rt))); return True
        if m == "subu": s.setr(i.rd, V("-", s.val(i.rs), s.val(i.rt))); return True
        if m == "andi": s.setr(i.rt, V("&", s.val(i.rs), V("c", i.imm))); return True
        if m in ("slti", "sltiu"): s.setr(i.rt, V("<s" if m == "slti" else "<u", s.val(i.rs), V("c", i.simm & 0xFFFFFFFF))); return True
        if m in ("slt", "sltu"): s.setr(i.rd, V("<s" if m == "slt" else "<u", s.val(i.rs), s.val(i.rt))); return True
        if m == "sll" and i.sa in (1, 2) and i.w != 0: s.setr(i.rd, V("<<", s.val(i.rt), V("c", i.sa))); return True
        if m == "lw" and i.simm == 0x124:                    # (2026-10-07) table des voix du perso (posée par le moteur
            s.setr(i.rt, V("c", 0)); return True              # 0x6099C) : sons PSP muets (psp_78408) -> lue nulle
        if m in LD and i.rs not in s.obj and i.rs != 29 and s.val(i.rs).k == "c" and \
                (s.val(i.rs).a + i.simm) & 0xFFFFFFFF in GLOB_ZERO:
            s.setr(i.rt, V("c", 0)); return True                # globale PSP toujours nulle en jeu normal
        if m in LD and i.rs not in s.obj and i.rs != 29 and s.val(i.rs).k == "c":
            from relocs import TEXT_END
            ad = (s.val(i.rs).a + i.simm) & 0xFFFFFFFF
            if TEXT_END <= ad < 0x2D4F30 and ad not in refs_code():    # donnée en lecture seule (segment 0) : constante
                f_ = {"lb": "<b", "lbu": "<B", "lh": "<h", "lhu": "<H", "lw": "<I"}[m]
                s.setr(i.rt, V("c", struct.unpack_from(f_, img, ad)[0] & 0xFFFFFFFF)); return True
        if m in LD and i.rs not in s.obj and i.rs != 29:
            s.setr(i.rt, V("mem", V("+", s.val(i.rs), V("c", i.simm & 0xFFFFFFFF)), sz=LD[m])); return True
        if m == "sll" and i.sa in (16, 24): s.setr(i.rd, V("<<%d" % i.sa, s.val(i.rt))); return True
        if m == "sra" and i.sa in (16, 24):                          # extension de signe (octet / mot)
            v = s.val(i.rt)
            if v.k == "<<%d" % i.sa:
                x = v.a
                deja = x.k == "f" and x.sz == (1 if i.sa == 24 else 2) and not getattr(x, "u", False)
                s.setr(i.rd, x if deja else V("sx%d" % (32 - i.sa), x)); return True
        if m == "sll" and i.w != 0: s.setr(i.rd, V("<<", s.val(i.rt), V("c", i.sa))); return True
        if m == "sra": s.setr(i.rd, V(">>s", s.val(i.rt), V("c", i.sa))); return True
        if m in ("sllv", "srlv", "srav"):                               # décalage par registre
            s.setr(i.rd, V({"sllv": "<<", "srlv": ">>u", "srav": ">>s"}[m], s.val(i.rt), s.val(i.rs))); return True
        if m == "srl": s.setr(i.rd, V(">>u", s.val(i.rt), V("c", i.sa))); return True
        if m == "or" and i.fn == 0x25: s.setr(i.rd, V("|", s.val(i.rs), s.val(i.rt))); return True
        if m == "xor": s.setr(i.rd, V("^", s.val(i.rs), s.val(i.rt))); return True
        if m == "and": s.setr(i.rd, V("&", s.val(i.rs), s.val(i.rt))); return True
        if m == "ori": s.setr(i.rt, V("|", s.val(i.rs), V("c", i.imm))); return True
        if m == "xori": s.setr(i.rt, V("^", s.val(i.rs), V("c", i.imm))); return True
        if m in ST and i.rs in s.obj: s.store(i.simm, ST[m], s.val(i.rt)); return True
        if m in ST and i.rs not in s.obj and i.rs != 29:
            v0 = s.val(i.rt); pre = None; k0 = len(s.out)
            if v0.k == "mem" and s.calc(v0): pre = "d3"     # (2026-10-07) source lue via un pointeur : D3 d'abord (A0 resservira)
            s._ecriture = True
            try: dst = s.adresse(V("+", s.val(i.rs), V("c", i.simm & 0xFFFFFFFF)), ST[m])
            finally: s._ecriture = False
            if dst and dst[0].startswith(SANS_OBJET):
                del s.out[k0:]                              # (2026-10-11) ni écriture NI lecture de la source
                if i.simm == 0xAA and ST[m] == 1:          # (2026-10-18) transparence d'un objet désigné par pointeur
                    bv = s.val(i.rs)
                    base = {"a4": "a4", "obj": "a6"}.get(bv.k) or (s.op68(bv)[0] if s.op68(bv) else None)
                    if base: s.alpha(base, s.val(i.rt)); return True
                s.emit("; (champ PSP %#x : sans objet sur l'arcade)" % i.simm); return True
            if dst:
                # taille d'ÉCRITURE = règle de store() : octet / mot PSP tels quels ; long PSP sur un mot 68K -> long
                ecr = {1: ".b", 2: ".w"}.get(ST[m]) or (".l" if dst[1] in (".w", "") else dst[1])
                if (s._o in LIENS16 and s._proj) or (s._o in LIENS_JOUEUR.values() and not s._proj): ecr = ".w"   # liens 16 bits
                dst = (dst[0], ecr)
                v = s.val(i.rt); src = ("d3", "") if pre else s.op68(v)
                if v.k == "obj": s.emit("move.w    a6, %s" % dst[0]); return True
                if v.k == "c" and v.a and ecr == ".b" and FACTEUR.get(s._o, 1) > 1:     # (2026-10-07) numéro ×n via pointeur
                    v = V("c", (v.a * FACTEUR[s._o]) & 0xFF); src = s.op68(v)
                if v.k == "c" and v.a == 0: s.emit("clr%s     %s" % (dst[1] or SUF[ST[m]], dst[0]))
                elif src and ({".b": 1, ".w": 2, ".l": 4}.get(src[1], 4) >= {".b": 1, ".w": 2, ".l": 4}.get(dst[1] or SUF[ST[m]], 4)
                              or src[0].startswith("#") or pre):
                    ns_ = {".b": 1, ".w": 2, ".l": 4}.get(src[1], 4); nd_ = {".b": 1, ".w": 2, ".l": 4}.get(dst[1] or SUF[ST[m]], 4)
                    so_ = decaler(src[0], ns_ - nd_) if ns_ > nd_ and "(" in src[0] and not pre else src[0]   # (2026-10-17) partie BASSE
                    if pre and ecr == ".b" and FACTEUR.get(s._o, 1) > 1:   # (2026-10-17) D3 = VALEUR (calc) -> champ ×n
                        s.emit("lsl.b   #%d, d3          ; valeur -> champ ×%d" % (DECAL[FACTEUR[s._o]], FACTEUR[s._o]))
                    s.emit("move%s    %s, %s" % (dst[1] or SUF[ST[m]], so_, dst[0]))
                elif s.calc(v):
                    if ecr == ".b" and FACTEUR.get(s._o, 1) > 1:      # (2026-10-17) idem via pointeur d'objet
                        s.emit("lsl.b   #%d, d3          ; valeur -> champ ×%d" % (DECAL[FACTEUR[s._o]], FACTEUR[s._o]))
                    s.emit("move%s    d3, %s" % (dst[1] or SUF[ST[m]], dst[0]))
                else: s.emit("?? %s <- %s" % (dst[0], v))
                return True
        return False
    def calc(s, v, n=3):
        """mode de repli : calcule v (32 bits) dans d<n> (registres de travail d3-d7) ; False si impossible"""
        if n > 7: return False
        d = "d%d" % n
        if v.k == "c":
            sv = v.a - (1 << 32) if v.a & 0x80000000 else v.a
            s.emit(("moveq   #%d, %s" % (sv, d)) if -128 <= sv < 128 else "move.l  #$%x, %s" % (v.a & 0xFFFFFFFF, d)); return True
        if v.k == "obj": s.emit("move.l  a6, %s" % d); return True
        if v.k == "a4": s.emit("move.l  a4, %s" % d); return True
        o = s.op68(v) if v.k in ("f", "mem", "ret", "arg", "phi") else None
        if o:
            t, suf = o
            nonsigne = getattr(v, "u", False)
            o68 = champ(v.a, v.sz)[1] if v.k == "f" else getattr(s, "_o", None)
            if CTX.get("acteur") and suf == ".b" and ((o68 is not None and 0x78 <= o68 <= 0x7F) or t in ("$1c9(a5)", "$1ca(a5)")):
                nonsigne = True
            if suf in (".b", ".w") and nonsigne:
                s.emit("moveq   #0, %s" % d); s.emit("move%s  %s, %s" % (suf, t, d))
            elif suf == ".b": s.emit("move.b  %s, %s" % (t, d)); s.emit("ext.w   %s" % d); s.emit("ext.l   %s" % d)
            elif suf == ".w": s.emit("move.w  %s, %s" % (t, d)); s.emit("ext.l   %s" % d)
            else: s.emit("move.l  %s, %s" % (t, d))
            if v.k == "f" and s.mul(v) > 1: s.emit("asr.l   #%d, %s          ; champ ×%d -> valeur" % (DECAL[s.mul(v)], d, s.mul(v)))
            elif v.k == "mem" and suf == ".b" and FACTEUR.get(o68, 1) > 1:     # (2026-10-17) idem via pointeur d'objet
                s.emit("asr.l   #%d, %s          ; champ ×%d -> valeur" % (DECAL[FACTEUR[o68]], d, FACTEUR[o68]))
            return True
        OPS = {"+": "add", "-": "sub", "&": "and", "|": "or", "^": "eor"}
        if v.k in OPS:
            if not s.calc(v.a, n): return False
            if v.b.k == "c":
                c = v.b.a & 0xFFFFFFFF
                if v.k in ("+", "-") and 0 < c <= 8: s.emit("%sq.l  #%d, %s" % (OPS[v.k], c, d))
                elif v.k == "+" and c >= 0xFFFFFFF8: s.emit("subq.l  #%d, %s" % ((1 << 32) - c, d))
                else: s.emit("%si.l  #$%x, %s" % (OPS[v.k], c, d))
                return True
            if not s.calc(v.b, n + 1): return False
            s.emit("%s.l   d%d, %s" % (OPS[v.k], n + 1, d)); return True
        if v.k in ("<<16", "<<24"):                          # sll 16/24 sans sra derrière : vrai décalage
            if not s.calc(v.a, n): return False
            if v.k == "<<16": s.emit("swap    %s" % d); s.emit("clr.w   %s" % d)
            else: s.emit("swap    %s" % d); s.emit("clr.w   %s" % d); s.emit("lsl.l   #8, %s" % d)
            return True
        if v.k in ("*", "/", "%"):
            # 68000 : MULS.W (16 x 16 -> 32) ; DIVS.W (32 / 16 -> quotient / reste 16 bits) : opérandes supposés tenir sur
            # 16 bits (cas des persos MAX : petits nombres) ; ⚠ à revoir si un opérande dépasse
            if not (s.calc(v.a, n) and s.calc(v.b, n + 1)): return False
            if v.k == "*": s.emit("muls.w  d%d, %s" % (n + 1, d))
            else:
                s.emit("divs.w  d%d, %s" % (n + 1, d))
                if v.k == "%": s.emit("swap    %s" % d)
                s.emit("ext.l   %s" % d)
            return True
        if v.k in ("sx8", "sx16"):
            if not s.calc(v.a, n): return False
            if v.k == "sx8": s.emit("ext.w   %s" % d)
            s.emit("ext.l   %s" % d); return True
        if v.k in ("<<", ">>s", ">>u") and v.b.k != "c":
            if not (s.calc(v.a, n) and s.calc(v.b, n + 1)): return False
            s.emit("%s.l   d%d, %s" % ({"<<": "lsl", ">>s": "asr", ">>u": "lsr"}[v.k], n + 1, d)); return True
        if v.k in ("<<", ">>s", ">>u") and v.b.k == "c":
            if not s.calc(v.a, n): return False
            ins_ = {"<<": "lsl", ">>s": "asr", ">>u": "lsr"}[v.k]; k = v.b.a
            while k > 0: s.emit("%s.l   #%d, %s" % (ins_, min(k, 8), d)); k -= 8
            return True
        if v.k in ("<s", "<u"):
            if not s.calc(v.a, n): return False
            if v.b.k == "c": s.emit("cmpi.l  #$%x, %s" % (v.b.a & 0xFFFFFFFF, d))
            else:
                if not s.calc(v.b, n + 1): return False
                s.emit("cmp.l   d%d, %s" % (n + 1, d))
            s.emit("%s     %s" % ("slt" if v.k == "<s" else "scs", d)); s.emit("andi.l  #1, %s" % d); return True
        return False
    def est_boutons(s, v):
        """v est un champ d'entrée (ou une combinaison | & de tels champs)"""
        if v.k == "f": return champ(v.a, v.sz)[1] in BOUTONS
        if v.k in ("|", "&"): return s.est_boutons(v.a) and (v.b.k == "c" or s.est_boutons(v.b))
        if v.k in ("sx8", "sx16", "zx8", "zx16"): return s.est_boutons(v.a)
        return False
    def cste(s, v, c):
        """constante c comparée à / masquant la valeur v (champ ×n, ou entrées : boutons convertis)"""
        if s.est_boutons(v): return conv_boutons(c)
        return c * s.mul(v)
    def mul(s, v):
        """facteur d'échelle du champ (×2 numéros d'état, ×4 plan de caméra $E), 1 sinon ; champ lu via un pointeur
        (v.k == "mem") : le dernier champ résolu par adresse() (s._o, posé par l'op68 qui précède)"""
        if v.k == "f": return FACTEUR.get(champ(v.a, v.sz)[1], 1)
        if v.k == "mem" and v.sz == 1: return FACTEUR.get(getattr(s, "_o", None), 1)
        return 1
    def charger_d0(s, v, suf):
        """(2026-10-11, rapport agent_integration_max : PSP lb 0x4D lu en « move.w $35 », adresse impaire) champ v chargé
        dans D0 à la taille suf de l'opération : lu à SA taille (taille_lecture), puis étendu (signe, ou zéro si lbu/lhu)"""
        t, o = champ(v.a, v.sz); n = {".b": 1, ".w": 2, ".l": 4}.get(suf, 4)
        tl = taille_lecture(o, v.sz); lu = min(tl, n)
        if lu < tl and tl == 2 and o in ECRITS_MOT: t = decaler(t, tl - lu)   # (2026-10-17) octet BAS d'un mot écrit par le code MAX
        if lu >= n: s.emit("move%s    %s, d0" % (suf, t)); return
        if getattr(v, "u", False):
            s.emit("moveq   #0, d0"); s.emit("move%s    %s, d0" % (SUF[lu], t)); return
        s.emit("move%s    %s, d0" % (SUF[lu], t))
        if lu == 1: s.emit("ext.w     d0")
        if n == 4: s.emit("ext.l     d0")
    def op68(s, v):
        """opérande 68K d'une valeur simple (champ, constante, champ d'un objet pointé, globale, retour), sinon None ;
        peut émettre le chargement du pointeur (MOVEA.W $ptr(A6),A1)"""
        if v.k == "f": t, o = champ(v.a, v.sz); return t, SUF.get(taille_lecture(o, v.sz), "")
        if v.k == "c": return "#$%x" % (v.a & 0xFFFFFFFF), ""
        if v.k == "ret": return "d0", ".w"
        if v.k == "arg": return "ARG%dW" % v.a, ".w"          # repère résolu par finaliser_args (registre ou pile)
        if v.k == "a4": return "a4", ".l"
        if v.k == "phi": return v.a, ".l"
        if v.k == "mem": return s.adresse(v.a, v.sz)
        return None
    def adresse(s, e, sz):
        """adresse mémoire e (base + décalage) -> opérande 68K (retient le décalage 68K du champ visé : s._o)"""
        s._o = None; s._proj = False; s._p = None
        r = s._adresse(e, sz)
        return r
    def table_fin(s, base, d, sz):
        """pointeur lu dans l'état de fin PSP (+$110/+$114/+$118/+$12C, constante 0x87FCB0 ou 2e argument) + index :
        +$12C = enregistrements de 32 o de la fin courante (fin_t12c -> A0) ; +$114 = jeu de boîtes du pas courant
        (en ligne dans le pas 68K, +8) ; +$110 / +$118 = pas de l'animation n (valeur = POINTEUR, rendu dans D7 par
        fin_pas110 / fin_pas118)"""
        for p, idx in ((base.a, base.b), (base.b, base.a)):
            off = fin_off(p)
            if off is None: continue
            if off == 0x12C and s.calc(idx, 7):
                s.emit("bsr     fin_t12c          ; A0 = enregistrements +$12C de la fin courante")
                s.emit("adda.l  d7, a0"); s._o = None
                return "$%x(a0)" % d, SUF.get(sz, "")
            if off == 0x114 and "$1c(a6) + #$8" in repr(idx):
                s.emit("movea.l $1c(a6), a0          ; jeu de boîtes du pas courant (en ligne dans le pas 68K)")
                s._o = None; return "$%x(a0)" % (8 + d), SUF.get(sz, "")
            if off in (0x110, 0x118) and d == 0 and idx.k == "<<" and idx.b.k == "c" and idx.b.a == 2 and s.calc(idx.a, 7):
                s.emit("bsr     fin_pas%x          ; D7 = n° d'animation -> D7 = pointeur du pas" % off)
                s._o = None; return "d7", ".l"
        return None
    def _adresse(s, e, sz):
        if e.k == "+" and e.b.k == "c":
            base, d = e.a, e.b.a
            if d & 0x80000000: d -= 1 << 32
        else: base, d = e, 0
        if base.k == "c":
            ad = (base.a + d) & 0xFFFFFFFF
            if CTX.get("acteur") and ad in COUCHES_ACTEUR: return "$%x(a5)" % COUCHES_ACTEUR[ad], SUF.get(sz, "")
            if ad in GLOB: return "$%x(a5)" % GLOB[ad], SUF.get(sz, "")
            if JOUEURS_PSP <= ad < JOUEURS_PSP + 4 * TAILLE_JOUEUR_PSP:      # (2026-10-10) structure joueur k nommée
                k, p = divmod(ad - JOUEURS_PSP, TAILLE_JOUEUR_PSP)              # en absolu (table PSP 0x213F88)
                t, o = champ(p, sz, False); s._o = o
                if o is not None: return "($%x).l" % (0xFF8400 + 0x400 * k + o), SUF.get(taille_lecture(o, sz), "")
                return "??joueur%d_%s" % (k, t), SUF.get(sz, "")
            if 0 <= ad - GLOB_A5 < 0x10000: return "$%x(a5)" % (ad - GLOB_A5), SUF.get(sz, "")
            if 0x300000 <= ad < 0xC00000: return "??glob_%#x" % ad, SUF.get(sz, "")      # globale PSP sans équivalent connu
            return None
        if CTX.get("acteur") and base.k == "+":                 # (2026-10-10) tables de l'état de fin PSP (0x87FCB0)
            r = s.table_fin(base, d, sz)
            if r: return r
        if base.k == "+" and base.a.k == "obj" and base.b.k == "c":   # (a6 + n) + d -> champ n + d de l'objet
            dd = base.b.a + d
            t, o = champ(dd, sz); return t, SUF.get(taille_lecture(o, sz), "")
        if base.k == "obj":
            t, o = champ(d, sz); return t, SUF.get(taille_lecture(o, sz), "")
        if base.k == "a4":
            t, o = champ(d, sz, True); s._o = o; s._proj = True; s._p = d; return t.replace("(a6)", "(a4)"), SUF.get(TAILLE.get(o, sz) if o is not None else sz, "")
        if CTX.get("acteur") and base.k == "arg" and base.a == 0:   # (2026-10-10) a1 = état de la fin -> globales A5
            if d == 2 and sz == 1: return "$1c9(a5)", ".b"           # octet faible du repère (mot $1C8)
            if d == 4: return "$1ca(a5)", ".b"                         # événement = OCTET en arcade
            if d in FIN_GLOB: return ("-$%x(a5)" % -FIN_GLOB[d]) if FIN_GLOB[d] < 0 else ("$%x(a5)" % FIN_GLOB[d]), SUF.get(sz, "")
            if 0 <= d < 0x10: return "$%x(a5)" % (0x1C6 + d), SUF.get(sz, "")    # même disposition que $1C6-$1D5 (n° de fin, repère, événement)
            return "??fin_%#x" % d, SUF.get(sz, "")
        if base.k in ("ret", "arg", "phi"):                    # pointeur d'objet reçu / renvoyé : mêmes champs
            src = ("ARG%dL" % base.a) if base.k == "arg" else s.op68(base)[0]
            s.emit("movea.l %s, a0          ; pointeur d'objet" % src)
            pj = CTX["proj"]          # (un pointeur renvoyé n'est pas forcément un objet fils : 0x67468 = fiche du camp)
            t, o = champ(d, sz, pj); s._o = o; s._proj = pj; s._p = d
            return t.replace("(a6)", "(a0)"), SUF.get(taille_lecture(o, sz), "")
        if base.k == "f" and base.a == 0x128 and 0 <= d < 12:        # entrée de boîtes courante (mots A, B, C, u32 LE)
            s.emit("movea.l $1c(a6), a0      ; mots A/B/C du pas courant (68K : +8..+$13, mêmes octets que le PSP)")
            if sz != 1: s.emit("; ⚠ lecture multi-octets d'un mot A/B/C : ordre des octets PSP (petit-boutiste) en mémoire 68K")
            return "%d(a0)" % (8 + d), {1: ".b", 2: ".w", 4: ".l"}.get(sz, ".b")
        if base.k == "f" and base.a == 0x1C and d in PAS_OCTETS:     # pas d'animation courant (PSP 10 o -> 68K 20 o)
            s.emit("movea.l $1c(a6), a0")
            return "%d(a0)" % PAS_OCTETS[d], ".b"
        if base.k == "f" and base.a in PTR:
            s.emit("movea.w $%x(a6), a1" % PTR[base.a])
            t, o = champ(d, sz, False); s._o = o; s._p = d; t = t.replace("(a6)", "(a1)")
            # (2026-10-25, Q3 : onde de choc de Yun tuée par psp_1c19e0) taille de l'ACCÈS PSP, pas celle du champ 68K
            # ($4 est un long en 68K, la PSP y lit un octet : « cmpi.l #2,$4(a1) » ne vaut jamais)
            return t, SUF.get(taille_lecture(o, sz) if o is not None else sz, "")
        # (2026-10-07) repli : additions de constantes aplaties, puis table de données PSP constante indexée, ou chaîne
        # de pointeurs d'objets (propriétaire / adversaire / liens 16 bits des objets fils)
        b2, d2 = base, d
        while b2.k == "+" and b2.b.k == "c": d2 += _sig(b2.b.a); b2 = b2.a
        if b2.k != "c" and 0x100000 <= d2 < len(img) and not getattr(s, "_ecriture", False):
            return s.table_donnees(b2, d2, sz)
        if b2.k == "+" and not getattr(s, "_ecriture", False):  # tableau local constant sur la pile : table en ROM
            for sp_, x_ in ((b2.a, b2.b), (b2.b, b2.a)):
                if sp_.k == "reg" and sp_.a == "sp":
                    vals, k = [], 0
                    while d2 + 4 * k in s.pile: vals.append(s.pile[d2 + 4 * k]); k += 1
                    if vals and sz == 4 and s.calc_index(x_):
                        lab = "P_%x_%d" % (s.f, len(s.tables_pile)); s.tables_pile.append((lab, vals))
                        s.emit("lea     %s(pc), a1          ; tableau local constant (pile PSP)" % lab)
                        return "0(a1,d7.l)", ".l"
        # (2026-10-07) champ « pointeur long vers une table de données au format PSP » + index calculé (Eagle :
        # 0x2C4 -> $34A, table de sauts posée à l'init, donnees_sauts_max.s)
        if b2.k == "+" and not getattr(s, "_ecriture", False):
            for f_, x_ in ((b2.a, b2.b), (b2.b, b2.a)):
                if f_.k == "f" and f_.a in PTR_TABLES and s.calc_index(x_):
                    s.emit("movea.l $%x(a6), a1          ; table PSP (champ %#x)" % (PTR_TABLES[f_.a], f_.a))
                    return "%d(a1,d7.l)" % d2, SUF.get(sz, ".w")
        if b2.k == "mem":                                     # (2026-10-07) pas courant (0x128 / 0x1C) d'un autre objet
            e, dd = b2.a, 0
            while e.k == "+" and e.b.k == "c": dd += _sig(e.b.a); e = e.a
            if dd in (0x128, 0x1C):
                rr = s.pointeur(e)
                if rr is not None:
                    s.emit("movea.l $1c(%s), a1" % rr[0])
                    if dd == 0x128 and 0 <= d2 < 12: return "%d(a1)" % (8 + d2), {1: ".b", 2: ".w", 4: ".l"}.get(sz, ".b")
                    if dd == 0x1C and d2 in PAS_OCTETS: return "%d(a1)" % PAS_OCTETS[d2], ".b"
                    if dd == 0x1C and d2 == 4 and sz == 2 and not getattr(s, "_ecriture", False):
                        # n° d'image PSP du pas courant : le pas 68K porte un POINTEUR d'image -> table de conversion
                        s.emit("movea.l a1, a0"); s.emit("jsr     num_image_psp      ; D7 = n° d'image PSP du pas (A0)")
                        return "d7", ".w"
                    return None
        r = s.pointeur(b2)
        if r is None: return None
        reg, pj = r
        t, o = champ(d2, sz, pj); s._o = o; s._proj = pj; s._p = d2
        return t.replace("(a6)", "(%s)" % reg), SUF.get(taille_lecture(o, sz), "")
    def pointeur(s, b):
        """b = valeur d'un pointeur d'objet -> (registre chargé, objet fils ?) ; chaînes chargées dans A1"""
        if b.k == "obj": return "a6", CTX["proj"]
        if b.k == "a4": return "a4", True                      # objet tout juste créé
        if b.k in ("arg", "phi", "ret"):                       # pointeur reçu / de jonction / renvoyé
            src = ("ARG%dL" % b.a) if b.k == "arg" else s.op68(b)[0]
            s.emit("movea.l %s, a1          ; pointeur d'objet" % src); return "a1", CTX["proj"]
        if b.k == "mem":                                       # (2026-10-07) joueur k de la table PSP 0x213F88
            e, dd = b.a, 0
            while e.k == "+" and e.b.k == "c": dd += _sig(e.b.a); e = e.a
            if dd == 0x213F88 and e.k != "c" and s.calc(e, 7):
                s.emit("lsl.l   #8, d7"); s.emit("addi.l  #$ff8400, d7      ; joueur k (PSP 0x213F88[k])")
                s.emit("movea.l d7, a1"); return "a1", False
            if e.k == "c" and (e.a + dd) & 0xFFFFFFFF in range(0x213F88, 0x213F98):
                k = ((e.a + dd) - 0x213F88) // 4
                s.emit("lea     $ff8400+$%x, a1     ; joueur %d (PSP 0x213F88[%d])" % (0x400 * k, k, k)); return "a1", False
        if b.k == "f" and b.a in PTR: s.emit("movea.w $%x(a6), a1" % PTR[b.a]); return "a1", False
        if b.k == "f" and CTX["proj"] and PROJ.get(b.a) in LIENS16:
            s.emit("movea.w $%x(a6), a1" % PROJ[b.a]); return "a1", True
        if b.k == "f" and not CTX["proj"] and b.a in LIENS_JOUEUR:
            s.emit("movea.w $%x(a6), a1" % LIENS_JOUEUR[b.a]); return "a1", True
        if b.k == "mem":
            e, dd = b.a, 0
            while e.k == "+" and e.b.k == "c": dd += _sig(e.b.a); e = e.a
            r = s.pointeur(e)
            if r is None: return None
            reg, pj = r
            if dd in PTR: s.emit("movea.w $%x(%s), a1" % (PTR[dd], reg)); return "a1", False
            if pj and PROJ.get(dd) in LIENS16: s.emit("movea.w $%x(%s), a1" % (PROJ[dd], reg)); return "a1", True
            if not pj and dd in LIENS_JOUEUR: s.emit("movea.w $%x(%s), a1" % (LIENS_JOUEUR[dd], reg)); return "a1", True
        return None
    def calc_index(s, idx):
        """index dans D7 ; si trop complexe pour D7 seul : calcul dans D3 avec D3/D4 sauvés"""
        k0 = len(s.out)
        if s.calc(idx, 7): return True
        del s.out[k0:]
        s.emit("movem.l d3-d4, -(sp)")
        if not s.calc(idx, 3): del s.out[k0:]; return False
        s.emit("move.l  d3, d7"); s.emit("movem.l (sp)+, d3-d4"); return True
    def table_donnees(s, idx, ad, sz):
        """lecture dans une table de données PSP constante (ad = adresse + décalage, idx = index en octets) : valeur
        chargée dans D7 (table recopiée en gros-boutiste dans donnees_max.s, étiquette TABD_<début>)"""
        k0 = len(s.out)
        if not s.calc(idx, 7):
            del s.out[k0:]                                   # index trop complexe pour D7 seul : D3/D4 sauvés
            s.emit("movem.l d3-d4, -(sp)")
            if not s.calc(idx, 3): del s.out[k0:]; return None
            s.emit("move.l  d3, d7"); s.emit("movem.l (sp)+, d3-d4")
        if ad == 0x213F88 and sz == 4:       # table PSP des joueurs (structures 0x498 o) = arcade $FF8400 + $400 k ($156/$158(A5))
            s.emit("lsl.l   #8, d7")
            s.emit("addi.l  #$ff8400, d7      ; joueur k (PSP 0x213F88[k]) = $FF8400 + $400 k")
            return "d7", ".l"
        refs = [r for r in refs_code() if r <= ad and ad - r < 0x400]
        debut = max(refs) if refs else ad
        DONNEES.setdefault(debut, set()).add((ad - debut, sz))
        suf = SUF.get(sz, ".l")
        s.emit("lea     TABD_%x+%d, a0       ; table de données PSP %#x (donnees_max.s)" % (debut, ad - debut, debut))
        s.emit("move%s  0(a0,d7.l), d7" % suf)
        return "d7", suf
    def cond(s, v, m):
        """saut conditionnel sur v (comparé à 0) : renvoie le mnémonique 68K à utiliser, après avoir émis le test"""
        base = BR[m]
        if v.k in ("sx8", "sx16") and v.a.k == "&": v = v.a                 # test à zéro : l'extension de signe ne change rien
        if v.k == "&" and v.b.k == "c" and v.a.k in ("f", "mem") and v.b.a and v.b.a & (v.b.a - 1) == 0 and s.op68(v.a):
            t, suf = s.op68(v.a); taille = {".b": 1, ".w": 2, ".l": 4}.get(suf, 1)
            b = (conv_boutons(v.b.a) if s.est_boutons(v.a) else v.b.a).bit_length() - 1
            if b < 8 * taille:
                dec = (taille - 1) - b // 8                               # octet gros-boutiste qui porte le bit
                mm = re.match(r"(\$?)(-?[0-9a-f]+)\((a\d)\)", t)
                if dec and mm:
                    base_ = int(mm.group(2), 16 if mm.group(1) else 10) + dec
                    t = ("$%x(%s)" if mm.group(1) else "%d(%s)") % (base_, mm.group(3))
                s.emit("btst      #%d, %s" % (b % 8, t)); return base
        if v.k == "&" and v.b.k == "c" and v.a.k == "f" and s.op68(v.a):
            c = conv_boutons(v.b.a) if s.est_boutons(v.a) else v.b.a; t, suf = s.op68(v.a)
            s.emit("move%s    %s, d0" % (suf, t)); s.emit("andi%s    #$%x, d0" % (suf, c))
            return base
        direct = v.k in ("<s", "<u") and s.op68(v.a) and s.op68(v.b) and (v.a.k == "c" or v.b.k == "c" or s.op68(v.a)[1] == s.op68(v.b)[1])
        if v.k in ("<s", "<u") and m in ("beq", "bne", "beql", "bnel") and not direct:
            if s.calc(v.a, 3) and s.calc(v.b, 4):
                s.emit("cmp.l     d4, d3")
                lt = "blt" if v.k == "<s" else "bcs"; ge = "bge" if v.k == "<s" else "bcc"
                return lt if m.startswith("bne") else ge
        if v.k in ("<s", "<u") and m in ("beq", "bne", "beql", "bnel") and direct:
            (ta, suf), (tb, sufb) = s.op68(v.a), s.op68(v.b)
            if v.a.k == "c": suf = sufb                         # constante : taille de l'autre opérande
            if v.b.k == "c": s.emit("cmpi%s    #$%x, %s" % (suf, s.cste(v.a, v.b.a) & MASQUE.get(suf, 0xFFFFFFFF), ta))
            else:                                               # a < b : d0 <- a ; CMP b,d0 (d0 - b)
                s.emit("move%s    %s, d0" % (suf, ta)); s.emit("cmp%s     %s, d0" % (suf, tb))
            lt = "blt" if v.k == "<s" else "bcs"; ge = "bge" if v.k == "<s" else "bcc"
            return lt if m.startswith("bne") else ge          # (a<b) != 0 -> saut si a < b
        s.tst(v); return base
    def tst(s, v):
        if v.k == "f":
            t, o = champ(v.a, v.sz); n_ = TAILLE.get(o, v.sz) if o is not None else v.sz
            if v.sz == 2 and o in ECRITS_MOT and not CTX.get("acteur"): n_ = 2     # (2026-10-17) mot écrit par le code MAX
            if CTX.get("acteur") and v.sz == 2 and n_ == 1 and o not in TAILLE_ACTEUR: n_ = 2   # (2026-10-18) idem
            s.emit("tst%s     %s" % (SUF.get(n_, ""), t))
        elif v.k == "+" and v.a.k == "f": pass                 # valeur que l'on vient d'écrire : drapeaux posés
        elif v.k == "a4": s.emit("tst.b     d7                ; objet créé ?")
        elif v.k in ("mem", "ret", "arg") and s.op68(v): t, suf = s.op68(v); s.emit("tst%s     %s" % (suf, t))
        elif s.calc(v): s.emit("tst.l     d3")
        else: s.emit("?? tst %s" % v)
    def copies_jonction(s, dest, R=None):
        """avant de rejoindre l'étiquette dest : recopier dans son registre de jonction chaque valeur qui diffère selon
        le chemin (2e passe)"""
        R = s.R if R is None else R
        for r, dr in sorted(s.phi.get(dest, {}).items()):
            v = R.get(r)
            if v is None or v.k == "reg": continue
            if v.k == "phi" and v.a == dr: continue
            if v.k == "c":
                sv = v.a - (1 << 32) if v.a & 0x80000000 else v.a
                s.emit(("moveq   #%d, %s" % (sv, dr)) if (-128 <= sv < 128 and dr[0] == "d") else "move.l  #$%x, %s" % (v.a & 0xFFFFFFFF, dr))
            elif s.calc(v, 3): s.emit("move.l  d3, %s          ; jonction" % dr)
            else: s.emit("?? %s <- %s (jonction)" % (dr, v))
    def table_saut(s, v):
        """v = mem(table + index << 2) -> (adresse de table, valeur d'index) ; sinon None"""
        if v.k != "mem" or v.sz != 4: return None
        e = v.a; dec = 0
        if e.k == "+" and e.b.k == "c":                     # déplacement final (ex. lw x,-8(r) : index décalé)
            dec = e.b.a - (1 << 32) if e.b.a & 0x80000000 else e.b.a; e = e.a
        if e.k != "+": return None
        a, b = e.a, e.b
        if a.k == "c": a, b = b, a
        if b.k != "c" or a.k != "<<" or a.b.a != 2: return None
        return (b.a + dec) & 0xFFFFFFFF, a.a
    def dispatch(s, v, terminal):
        ts = s.table_saut(v)
        if not ts: s.emit("?? saut indirect %s" % v); return
        tab, idx = ts
        from charcode2 import P
        cibles, k = [], 0
        R_ = refs_code()
        while (tab + 4 * k) in P and not (k and (tab + 4 * k) in R_): cibles.append(P[tab + 4 * k]); k += 1
        from relocs import TEXT_END
        lab = "J_%x" % tab
        n_ = sum(1 for l, _ in s.tables if l == lab or l.startswith(lab + "_"))
        if n_: lab = "%s_%d" % (lab, n_ + 1)                 # (2026-10-07) même table aiguillée deux fois dans la routine
        # (2026-10-07) tables d'ADRESSES LONGUES (dc.l) : cibles lointaines possibles ; lea tab(pc) : ±32 Ko
        if idx.k == "f":
            t, o = champ(idx.a, idx.sz)
            s.emit("moveq   #0, d0"); s.emit("move.b  %s, d0" % t)
            if FACTEUR.get(o) == 4: pass                     # champ ×4 = décalage 4n
            elif o in ETATS: s.emit("add.w   d0, d0          ; champ ×2 -> décalage 4n")
            else: s.emit("add.w   d0, d0"); s.emit("add.w   d0, d0          ; index PSP n -> décalage 4n")
        elif s.calc(idx, 3):                                 # (2026-10-07) index calculé (argument, registre…)
            s.emit("move.l  d3, d0"); s.emit("add.w   d0, d0"); s.emit("add.w   d0, d0          ; index PSP n -> décalage 4n")
        else: s.emit("?? d0 <- %s (index de la table)" % idx)
        s.emit("lea     %s(pc), a0" % lab)
        s.emit("movea.l 0(a0,d0.w), a0")
        s.emit("%s     (a0)" % ("jmp" if terminal else "jsr"))
        s.tables.append((lab, cibles))
        for c in cibles:
            if c in s.cases: s.entrants.setdefault(c, []).append((dict(s.R), set(s.obj)))   # cas local : état du saut
        s.sous.update(c for c in cibles if c < TEXT_END and c not in s.cases)
    def epilogue_apres(s, j):
        k = j + 2
        while k < len(s.ins):
            x = s.ins[k]
            if x.m == "jr" and x.rs == 31:
                sl = s.ins[k + 1] if k + 1 < len(s.ins) else None      # le créneau du retour ne doit rien faire d'utile
                return sl is None or (sl.m == "addiu" and sl.rt == 29) or (sl.m == "sll" and sl.w == 0) or (sl.m == "lw" and sl.rs == 29)
            if (x.m == "lw" and x.rs == 29) or (x.m == "addiu" and x.rt == 29): k += 1; continue
            if x.va in {y.va + 4 + 4 * y.simm for y in s.ins if mnem(y) in BR}: return False
            return False
        return False
    def run(s):
        ins = s.ins
        cibles = {x.va + 4 + 4 * x.simm for x in ins if mnem(x) in BR}
        # (2026-10-07) cas de switch internes (mots de données qui pointent dans la routine) : étiquettes locales
        s.cases = {c for c in _valeurs_pointeurs() if ins and ins[0].va < c <= ins[-1].va}
        cibles |= s.cases
        j = 0
        s.mort = False
        while j < len(ins):
            i = ins[j]; m = mnem(i)
            if s.mort and i.va not in cibles: j += 1; continue
            if i.va in cibles and s.mort and not s.entrants.get(i.va) and i.va not in s.phi:
                s.mort = False                                     # étiquette atteinte seulement depuis le code mort
            s.mort = False
            if i.va in cibles:
                prec = s.out[-1].strip().split()[0] if s.out and not s.out[-1].endswith(":") else ""
                if prec not in ("jmp", "bra", "rts"): s.copies_jonction(i.va)
                s.out.append("L_%x:" % i.va)
                etats = list(s.entrants.get(i.va, []))
                dernier = s.out[-2].strip().split()[0] if len(s.out) > 1 and not s.out[-2].endswith(":") else ""
                if dernier not in ("jmp", "bra", "rts"): etats.append((dict(s.R), set(s.obj)))
                s.etats_label[i.va] = etats
                s.n_entrants[i.va] = len(s.entrants.get(i.va, []))     # (2026-10-07) arrivées en arrière ajoutées ensuite
                if etats:
                    R0, o0 = etats[0]
                    # valeur commune aux chemins qui en ont une (chemin sans valeur ni objet = indéfini : ignoré)
                    s.R = {}
                    for r in set().union(*[set(e[0]) for e in etats]):
                        vs = {repr(e[0][r]) for e in etats if r in e[0]}
                        if len(vs) == 1 and not any(r in e[1] for e in etats):
                            s.R[r] = next(e[0][r] for e in etats if r in e[0])
                    s.obj = set.intersection(*[e[1] for e in etats])
                else: s.R = {}
                for r, dr in s.phi.get(i.va, {}).items(): s.R[r] = V("phi", dr)
            if m == "jal":
                if j + 1 < len(ins): s.simple(ins[j + 1])
                for r, d in ((5, 0), (6, 1), (7, 2))[:0 if i.tgt in ALLOC else ARITE.get(i.tgt, 3)]:
                    v = s.R.get(r)
                    if v is None: continue
                    if v.k == "c" and v.a in TABLES_EXPL:
                        s.emit("move.l  #TAB_%x, d%d     ; table de scripts convertie (tables_explicites_*.s)" % (v.a, d))
                    elif v.k == "c":
                        sv = v.a - (1 << 32) if v.a & 0x80000000 else (v.a - 0x10000 if 0x8000 <= v.a <= 0xFFFF else v.a)
                        s.emit(("moveq   #%d, d%d" % (sv, d)) if -128 <= sv < 128 else "move.w  #$%x, d%d" % (v.a & 0xFFFF, d))
                    elif v.k == "f":
                        t, o = champ(v.a, v.sz); suf = SUF.get(taille_lecture(o, v.sz), "")
                        s.emit("move%s  %s, d%d" % (suf, t, d))
                        if o in FACTEUR: s.emit("lsr%s   #%d, d%d          ; champ ×%d -> valeur" % (suf, DECAL[FACTEUR[o]], d, FACTEUR[o]))
                    elif v.k == "ret" and d == 0: pass          # déjà dans D0
                    elif v.k == "arg": s.emit("move.l  ARG%dL, d%d" % (v.a, d))   # supprimé si sans pile et même registre
                    elif s.op68(v): t, suf = s.op68(v); s.emit("move%s  %s, d%d" % (suf, t, d))
                    elif s.calc(v): s.emit("move.l  d3, d%d" % d)
                    else: s.emit("?? d%d <- %s" % (d, v))
                t68 = API.get(i.tgt)
                jx = "jmp" if s.epilogue_apres(j) else "jsr"
                # (2026-10-24, super 2× QCB + P d'Ingrid bloquée, banc_max12) a0 PSP = un AUTRE objet (victime +0x5C, objet
                # créé…) : l'appelée travaille sur A6 -> A6 basculé sur cet objet le temps de l'appel. Seulement si l'appelée
                # emploie a0 comme objet (a0_objet) : ailleurs a0 est un nombre (aléa 0x1D368, compteurs 0xCFB58…)
                autre = None
                if i.tgt not in ALLOC and i.tgt not in SON | A0_SANS_OBJET and s.val(4).k != "obj" and a0_objet(i.tgt):
                    k_ = len(s.out); r_ = s.pointeur(s.val(4))
                    if r_ and r_[0] != "a6": autre = r_[0]
                    else: del s.out[k_:]                 # chargements partiels d'un a0 qui n'est pas un objet connu
                if autre:
                    s.emit("move.l  a6, -(sp)")
                    s.emit("movea.l %s, a6          ; a0 PSP = autre objet (%s)" % (autre, s.val(4)))
                    queue, jx = jx == "jmp", "jsr"
                if i.tgt in ALLOC:
                    ty, so = s.R.get(4), s.R.get(5)
                    s.emit("jsr     $%x.l            ; création d'objet -> A4 (Z si échec)" % ALLOC[i.tgt])
                    s.emit("sne     d7")
                    s.emit("beq.s   L_alloc_%x" % i.va)
                    if i.tgt in ALLOC_PERSO:
                        s.emit("move.b  #1, (a4)")
                        if CTX.get("perso") is not None:
                            s.emit("move.b  #%s, $2(a4)       ; type d'objet projectile ($32F46)" %
                                   {0x26: "TYPE_PROJ_EAGLE", 0x27: "TYPE_PROJ_MAKI", 0x28: "TYPE_PROJ_YUN", 0x29: "TYPE_PROJ_INGRID"}[CTX["perso"]])
                        else: s.emit("move.b  $2(a6), $2(a4)        ; n° du perso (projectile)")
                        # a1 = code de type PSP (Eagle 0x2B, Ingrid 0x2D/0x2E -> table du module 0x2B1EA0) : remplacé par
                        # l'aiguillage arcade par perso ; le sous-type $3 est écrit ensuite par le créateur lui-même
                        if so is not None and so.k == "c": s.emit("move.b  #$%02x, $ff(a4)       ; type d'objet PSP (octet libre ; Upper lit $22 en mot)" % (so.a & 0xFF))
                        else: s.emit("; (type d'objet PSP %s : aiguillage arcade par perso $32F46[$2])" % so)
                    elif ty is not None and ty.k == "c" and so is not None and so.k == "c":
                        # (2026-10-07) types propres aux persos MAX (tables TYPES_OBJETS, routines traduites qui doublent
                        # elles-mêmes l'index de $3) : sous-type BRUT ; types du moteur (routines arcade) : sous-type ×2
                        brut = (ty.a & 0xFF) in TYPES_MAX or 0x48 <= (ty.a & 0xFF) <= 0x50   # (2026-10-10) acteurs de fin : $3 brut (doublé par l'aiguillage de classe)
                        s.emit("move.l  #$%08x, (a4)%s" % (0x01000000 | (ty.a & 0xFF) << 8 | ((so.a if brut else 2 * so.a) & 0xFF),
                                                           "        ; type MAX : sous-type brut" if brut else "        ; sous-type ×2"))
                    elif ty is not None and ty.k == "c":     # sous-type non fourni (arité 1 : registre a1 hérité) : type seul
                        s.emit("move.b  #1, (a4)")
                        s.emit("move.b  #$%02x, $2(a4)" % (ty.a & 0xFF))
                    else: s.emit("?? move.l #$0100<type><sous-type>, (a4)  ; type %s, sous-type %s" % (ty, so))
                    if i.tgt not in ALLOC_PERSO: s.emit("bsr     psp_raz_alloc       ; champs remis à zéro par l'allocateur PSP 0x1EFE4")
                    else: s.emit("bsr     psp_raz_alpha       ; transparence remise à 0 (allocateur PSP)")
                    s.out.append("L_alloc_%x:" % i.va)
                    for r in (2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25): s.R.pop(r, None)
                    s.R[2] = V("a4"); s.obj -= {2, 4}; s.R.pop(4, None)
                    j += 2; continue
                if i.tgt in SON:
                    s.emit("; SON : n° PSP en d0 (table des sons à faire correspondre ; psp %#x)" % i.tgt)
                    if jx == "jmp": s.emit("rts")
                elif t68 in RET_A3:                  # (2026-10-27, Q16.2) valeur rendue en A3, pas en D0
                    s.emit("jsr     $%x.l" % t68); s.emit("move.l  a3, d0          ; $%X rend sa valeur en A3" % t68)
                    if jx == "jmp": s.emit("rts")
                elif t68: s.emit("%s     $%x.l" % (jx, t68))
                else:
                    s.emit("%s     psp_%x" % ("bra" if jx == "jmp" else "bsr", i.tgt)); s.sous.add(i.tgt)
                if autre:
                    s.emit("movea.l (sp)+, a6")
                    if queue: s.emit("rts")
                for r in (2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25): s.R.pop(r, None)
                s.obj -= {2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
                s.R[2] = V("ret")                    # valeur de retour : D0 (convention arcade)
                j += 2; continue
            if m in BR:
                dest = i.va + 4 + 4 * i.simm; slot = ins[j + 1] if j + 1 < len(ins) else None
                likely = m.endswith("l") and m not in ("bltz",)
                a, b = s.val(i.rs), s.val(i.rt)
                pur = slot is not None and (mnem(slot) in LD or mnem(slot) in ("ori", "addiu", "lui", "or", "addu", "sll", "sra"))
                if slot is not None and not likely: s.simple(slot)
                pris = None
                if slot is not None and likely and pur:          # « likely » sans effet de bord : état du chemin PRIS seulement
                    sauve = (dict(s.R), set(s.obj)); s.simple(slot); pris = (dict(s.R), set(s.obj)); s.R, s.obj = sauve
                # (2026-10-07) condition constante (ex. pointeur lu nul) : saut toujours / jamais pris
                cst = None
                if a.k == "c" and b.k == "c" and m in ("beq", "beql", "bne", "bnel") and not (i.rs == 0 and i.rt == 0):
                    cst = (a.a == b.a) == (m in ("beq", "beql"))
                if cst is not None:
                    if cst:
                        if likely and slot is not None: s.simple(slot)
                        s.copies_jonction(dest)
                        s.emit("bra     L_%x          ; condition constante" % dest)
                        s.entrants.setdefault(dest, []).append((dict(s.R), set(s.obj)))
                        s.mort = True                              # code mort jusqu'à la prochaine étiquette
                    j += 2; continue
                if m in ("beq", "beql") and i.rs == 0 and i.rt == 0:
                    s.copies_jonction(dest, pris[0] if pris else None)
                    s.emit("bra     L_%x" % dest); s.entrants.setdefault(dest, []).append(pris or (dict(s.R), set(s.obj)))
                else:
                    k0 = len(s.out)
                    s.copies_jonction(dest, pris[0] if pris else None)     # AVANT le test (les MOVE changent les drapeaux)
                    copies = s.out[k0:]; del s.out[k0:]
                    bx = BR[m]
                    if m in ("beq", "bne", "beql", "bnel") and not (b.k == "c" and b.a == 0):
                        if s.op68(a) and s.op68(b) and b.k == "c":
                            ta, suf = s.op68(a); s.emit("cmpi%s    #$%x, %s" % (suf, s.cste(a, b.a) & MASQUE.get(suf, 0xFFFFFFFF), ta))
                        elif s.op68(a) and s.op68(b) and a.k == "c":
                            tb, suf = s.op68(b); s.emit("cmpi%s    #$%x, %s" % (suf, a.a & MASQUE.get(suf, 0xFFFFFFFF), tb))
                        elif s.calc(a, 3) and s.calc(b, 4): s.emit("cmp.l     d4, d3")
                        else: s.emit("?? cmp %s, %s" % (b, a))
                    else: bx = s.cond(a, m)
                    if copies and "<jonction" in repr(a) + repr(b):
                        # (2026-10-07) le test relit une valeur de jonction que les recopies vont écraser (boucles) :
                        # résultat du test dans D7 (Scc), recopies, puis saut sur D7
                        s.emit("s%s     d7" % bx[1:]); s.out += copies; s.emit("tst.b   d7"); bx = "bne"
                    else: s.out[k0:k0] = copies
                    if likely and slot is not None and not pur and not (slot.m == "sll" and slot.w == 0):
                        lab = "T_%x" % i.va; s.emit("%s     %s" % (bx, lab)); s.tramp.append((lab, slot, dest, dict(s.R), set(s.obj)))
                    else: s.emit("%s     L_%x" % (bx, dest))
                    s.entrants.setdefault(dest, []).append(pris or (dict(s.R), set(s.obj)))
                j += 2; continue
            if m == "jr" and i.rs == 31:
                if j + 1 < len(ins): s.simple(ins[j + 1])          # créneau de délai du retour (souvent une écriture)
                v0 = s.R.get(2)
                if v0 is not None and v0.k not in ("ret", "reg", "a4"):  # valeur de retour calculée ici -> D0
                    if v0.k == "c":
                        sv = v0.a - (1 << 32) if v0.a & 0x80000000 else v0.a
                        s.emit(("moveq   #%d, d0" % sv) if -128 <= sv < 128 else "move.l  #$%x, d0" % (v0.a & 0xFFFFFFFF))
                    elif s.calc(v0): s.emit("move.l  d3, d0          ; valeur de retour")
                    else: s.emit("?? d0 <- %s (valeur de retour)" % v0)
                s.emit("rts"); j += 2; continue
            if m in ("jalr", "jr"):
                v = s.val(i.rs)
                if j + 1 < len(ins): s.simple(ins[j + 1])
                s.dispatch(v, m == "jr" or s.epilogue_apres(j))
                for r in (2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25): s.R.pop(r, None)
                j += 2; continue
            if not s.simple(i): s.emit("?? " + repr(i))
            j += 1
        from relocs import TEXT_END
        for lab, cibles in s.tables:                         # tables de saut (décalages 16 bits, comme l'arcade)
            s.out.append(lab + ":")
            for c in cibles:
                if c in s.cases: s.emit("dc.l    L_%x" % c)
                elif c < TEXT_END: s.emit("dc.l    psp_%x" % c)
                else: s.emit("dc.l    0               ; entrée PSP %#x hors code (index jamais utilisé ?)" % c)
        for lab, vals in s.tables_pile:
            s.out.append(lab + ":"); s.emit("dc.l    " + ", ".join("$%x" % (v & 0xFFFFFFFF) for v in vals))
        for lab, slot, dest, R_, o_ in s.tramp:               # créneaux « likely » (état des registres au saut)
            s.out.append(lab + ":")
            s.R, s.obj = dict(R_), set(o_)
            if not s.simple(slot): s.emit("?? " + repr(slot))
            s.copies_jonction(dest)
            s.entrants.setdefault(dest, []).append((dict(s.R), set(s.obj)))
            s.emit("bra     L_%x" % dest)
        return nettoyer(s.out)

A0_SANS_OBJET = {0x1D368} # aléa (void, = arcade $1BDA6) : a0 résiduel, sans objet
RET_A3 = {0x1BD5C}                 # (2026-10-27, Q16.2) fonctions arcade qui rendent leur valeur en A3 (PSP 0x1D330 : en v0)
def a0_objet(f):
    """a0 est un objet si son PREMIER emploi (avant d'être écrasé) est une base d'accès ou une copie (or rX,a0,zero)
    (même règle que brouillons.py)"""
    for i in decode(img, f, fend(f)):
        if i.m in ("lb", "lbu", "lh", "lhu", "lw", "sb", "sh", "sw") and i.rs == 4: return True
        if i.m == "or" and i.fn == 0x25 and 4 in (i.rs, i.rt) and 0 in (i.rs, i.rt): return True
        if i.m == "jal": return True
        lit = (i.op == 0 and 4 in (i.rs, i.rt)) or (i.op != 0 and i.rs == 4 and i.m not in ("sw", "sh", "sb"))
        if lit: return False
        ecrit = (i.op == 0 and i.rd == 4) or (i.op != 0 and i.rt == 4 and i.m not in ("sw", "sh", "sb", "beq", "bne"))
        if ecrit: return True
    return True

def nettoyer(out):
    """JSR x ; BRA L ; ... L: RTS -> JMP x ; RTS mort après JMP/BRA/RTS"""
    labels = {}
    for k, l in enumerate(out):
        if l.endswith(":"): labels[l[:-1]] = k
    def suivant_reel(k):
        while k < len(out) and out[k].endswith(":"): k += 1
        return out[k].strip() if k < len(out) else ""
    res = []
    for k, l in enumerate(out):
        x = l.strip()
        if x.startswith("jsr") and k + 1 < len(out) and out[k + 1].strip().startswith("bra"):
            lab = out[k + 1].split()[-1]
            if lab in labels and suivant_reel(labels[lab] + 1) == "rts":
                res.append(l.replace("jsr", "jmp", 1)); out[k + 1] = "        ;"; continue
        if x == ";": continue
        if x == "rts" and res and res[-1].strip().split()[0] in ("jmp", "bra", "rts") and not res[-1].endswith(":"): continue
        res.append(l)
    return res

RESERVE_JONCTION = ["d5", "d6", "a2", "a3"]   # registres de jonction (D3/D4 = calcul, D7 = création d'objet, A0/A1 = pointeurs)
def _lit_ecrit(i):
    """registres lus / écrits par une instruction MIPS"""
    m = mnem(i); lit, ecrit = set(), set()
    if i.op == 0:
        if m in ("sll", "srl", "sra"): lit = {i.rt}; ecrit = {i.rd}
        elif m in ("jr", "jalr"): lit = {i.rs}
        else: lit = {i.rs, i.rt}; ecrit = {i.rd}
    elif m in ST: lit = {i.rs, i.rt}
    elif m in BR: lit = {i.rs, i.rt}
    elif m in ("jal",): lit = {4} | {5 + k for k in range(ARITE.get(i.tgt, 3))}
    elif m == "lui": ecrit = {i.rt}
    else: lit = {i.rs}; ecrit = {i.rt}
    return lit - {0}, ecrit - {0}
def _vivant(t, va, r):
    """r est-il lu après l'adresse va avant d'être réécrit (parcours linéaire jusqu'au retour) ?"""
    for x in t.ins:
        if x.va < va: continue
        lit, ecrit = _lit_ecrit(x)
        if r in lit: return True
        if r in ecrit: return False
        if x.m == "jr" and x.rs == 31: return r == 2           # v0 = valeur de retour
    return False
def conflits(t, avant=None):
    """par étiquette : registres MIPS vivants dont la valeur diffère selon le chemin d'arrivée -> registre 68K
    (affectation FIXE par registre MIPS dans toute la fonction, pour ne jamais écraser une valeur vivante)"""
    par_label, regs = {}, []
    avant = avant or {}
    for lab, d in avant.items():                          # (2026-10-07) passes successives : jonctions déjà connues gardées
        par_label[lab] = list(d)
        for r in sorted(d, key=lambda r: RESERVE_JONCTION.index(d[r]) if d[r] in RESERVE_JONCTION else 9):
            if r not in regs: regs.append(r)
    for lab, etats in t.etats_label.items():
        etats = etats + t.entrants.get(lab, [])[t.n_entrants.get(lab, 0):]     # boucles : arrivées par saut arrière
        if len(etats) < 2: continue
        # (2026-10-07) un chemin sans valeur pour r (registre indéfini, chemin impossible en pratique) ne bloque plus
        # la jonction des autres
        communs = {r for r in set().union(*[set(e[0]) for e in etats]) if sum(r in e[0] for e in etats) >= 2}
        diff = [r for r in sorted(communs) if r not in (0, 29, 31)
                and len({repr(e[0][r]) if r in e[0] else "obj" for e in etats if r in e[0] or r in e[1]}) > 1
                and all(e[0][r].k != "reg" for e in etats if r in e[0]) and _vivant(t, lab, r)]
        if diff:
            par_label[lab] = sorted(set(par_label.get(lab, [])) | set(diff))
            for r in diff:
                if r not in regs: regs.append(r)
    affect = {r: RESERVE_JONCTION[k] for k, r in enumerate(regs[:len(RESERVE_JONCTION)])}
    return {lab: {r: affect[r] for r in diff if r in affect} for lab, diff in par_label.items()}

def finaliser_args(L):
    """(2026-10-07) arguments reçus (D0-D2) : s'ils peuvent être écrasés (appel, écriture de D0-D2) avant d'être relus,
    ils sont sauvés sur la pile en entrée (MOVEM) et relus à 0/4/8(sp) ; la pile est rendue à chaque sortie."""
    import re as _re
    if not any("ARG" in l for l in L): return L
    def ecrit_d(l):
        t = l.strip()
        if t.startswith(("bsr", "jsr")): return True
        m = _re.match(r"\S+\s+(.*)$", t)
        mc = _re.match(r"move\.\w\s+ARG(\d)[LW], d(\d)$", t)
        if mc: return mc.group(1) != mc.group(2)                           # copie croisée : écrase un autre argument
        if not m or t.startswith(("cmp", "tst", "btst", ";")) or "ARG" in t: return False
        ops = m.group(1).split(";")[0]
        dst = ops.split(",")[-1].strip()
        return dst in ("d0", "d1", "d2")
    der = max(k for k, l in enumerate(L) if "ARG" in l)                    # dernière relecture d'un argument
    pile = any(ecrit_d(l) for l in L[:der])                                 # écrasement possible AVANT elle
    out = []
    if pile: out.append("        movem.l d0-d2, -(sp)         ; arguments sauvés (relus après des appels / écritures)")
    for l in L:
        if pile:
            l = _re.sub(r"ARG(\d)L", lambda m: "%d(sp)" % (4 * int(m.group(1))), l)
            l = _re.sub(r"ARG(\d)W", lambda m: "%d(sp)" % (4 * int(m.group(1)) + 2), l)
            t = l.strip(); w = t.split()
            sortie = t == "rts" or (w and w[0] == "jmp" and "(pc," not in t) or \
                     (w and w[0] == "bra" and len(w) > 1 and (w[1].startswith("psp_") or w[1].startswith("$")))
            if sortie: out.append("        lea     12(sp), sp")
            out.append(l)
        else:
            l = _re.sub(r"ARG(\d)[LW]", lambda m: "d%s" % m.group(1), l)
            m = _re.match(r"\s*move\.[wl]\s+(d\d), (d\d)$", l)
            if m and m.group(1) == m.group(2): continue
            out.append(l)
    return out

# racines des routines d'objets fils des persos MAX : table (type d'objet PSP -> routine) du module, ex. Ingrid 0x2B1EA0 :
# 0x2D/0x2E -> 0x1C7840 (projectiles, $1C1C8, 26 sous-types via 0x2B2020), 0x35 -> 0x1C7260, 0x36 -> 0x1C6E58,
# 0x37 -> 0x1C8874, 0x3A -> 0x1C8F10 (effets, $1C368, objets de $80 : aucun autre champ hors objet)
# tables (type d'objet PSP, routine) des modules MAX (groupes séparés par -1 ; 1er groupe = projectiles $1C1C8, puis
# effets) : Eagle 0x2A3174, Maki 0x2A6248, Yun 0x2AD6B0, Ingrid 0x2B1EA0
TYPES_OBJETS = {0x26: 0x2A3174, 0x27: 0x2A6248, 0x28: 0x2AD6B0, 0x29: 0x2B1EA0}
def types_objets(c):
    """-> [(groupe, type PSP, routine)]"""
    U = lambda a: struct.unpack_from("<I", img, a)[0]
    a, g, out = TYPES_OBJETS[c], 0, []
    while True:
        if U(a) == 0xFFFFFFFF:
            if U(a + 4) == 0xFFFFFFFF or not out: break
            g += 1; a += 4; continue
        if not 0x20 <= U(a) <= 0x40: break
        out.append((g, U(a), U(a + 4))); a += 8
    return out
RACINES_FILS = {c: tuple(sorted({r for _, _, r in types_objets(c)})) for c in TYPES_OBJETS}
TYPES_MAX = {t for c in TYPES_OBJETS for _, t, _ in types_objets(c)}
# (2026-10-07) famille d'objets « effets de décor » d'Ingrid (type 13 du réservoir PSP de 0x94 o, tables 0x2B2148 /
# 0x2B2158 / 0x2B2234, aiguillage 0x1C9250) : créés seulement par cette famille ou par du code hors module (scénarios),
# allocation neutralisée (psp_1f338) -> routines mortes, non traduites (ébauche : rts)
_MORTES = None
def mortes():
    global _MORTES, _PROJ_FN
    if _MORTES is None:
        U = lambda a: struct.unpack_from("<I", img, a)[0]
        r = {0x1C9250, 0x1C9024}             # + 0x1C9024 : cycle de palette du décor (gestionnaire inscrit dynamiquement)
        for tab in (0x2B2148, 0x2B2158):
            k = 0
            while 0x1C0000 <= U(tab + 4 * k) < 0x1CAF0C: r.add(U(tab + 4 * k)); k += 1
        sauve, sp = RACINES_FILS.copy(), _PROJ_FN
        RACINES_FILS.clear(); RACINES_FILS[0x29] = tuple(sorted(r)); _PROJ_FN = None
        _MORTES = set(proj_fn())
        RACINES_FILS.clear(); RACINES_FILS.update(sauve); _PROJ_FN = sp
    return _MORTES
_PROJ_FN = None
def proj_fn():
    """routines PSP dont A6 est un objet fils : racines, cibles des tables de saut qu'elles chargent (LUI/ADDIU),
    et appelées dont TOUS les appelants du module en font partie (point fixe)"""
    global _PROJ_FN
    if _PROJ_FN is not None: return _PROJ_FN
    U = lambda a: struct.unpack_from("<I", img, a)[0]
    import modules
    B = modules.module_bounds(); res = set()
    for c, racines in RACINES_FILS.items():
        a0, e0 = B[c]
        # routines = [début, fend(début)) (fend suit les branches : les cas de switch internes restent dans la routine)
        sites = collections.defaultdict(list)                  # appelée -> sites d'appel (JAL) dans le module
        for a in range(a0, e0, 4):
            if U(a) >> 26 == 3 and a0 <= (U(a) & 0x3FFFFFF) << 2 < e0: sites[(U(a) & 0x3FFFFFF) << 2].append(a)
        def tables(f):
            out = []
            for a in range(f, fend(f), 4):
                w = U(a)
                if w >> 26 != 0x0F: continue
                rt = (w >> 16) & 31
                for k in range(1, 8):
                    x = U(a + 4 * k)
                    if x >> 26 == 9 and ((x >> 21) & 31) == rt:
                        t = ((w & 0xFFFF) << 16) + ((x & 0xFFFF) ^ 0x8000) - 0x8000; n = 0
                        while 0 <= t + 4 * n < len(img) - 4 and a0 <= U(t + 4 * n) < e0: out.append(U(t + 4 * n)); n += 1
                        break
            return out
        fils = set(racines); pile = list(racines)
        while True:
            while pile:
                f = pile.pop()
                for g in tables(f):
                    if g not in fils: fils.add(g); pile.append(g)
            corps = [(f, fend(f)) for f in fils]
            dedans = lambda a: any(f <= a < e for f, e in corps)
            neuf = {t for t, sa in sites.items() if t not in fils and all(dedans(a) for a in sa)}
            if not neuf: break
            fils |= neuf; pile += list(neuf)
        res |= fils
    _PROJ_FN = res
    return res

def traduire_trad(f, end=None):
    """deux passes : la 1re relève les jonctions, la 2e y recopie les valeurs (D5/D6) -> (objet Trad, lignes)"""
    avant = CTX["proj"]; CTX["proj"] = f in proj_fn()
    import modules
    CTX["perso"] = next((c for c, (a, e) in modules.module_bounds().items() if a <= f < e and c >= 0x26), None)
    try:
        t1 = Trad(f, end); out1 = t1.run()
        ph = conflits(t1)
        if not ph: return t1, symboles_projectiles(finaliser_args(out1))
        for _ in range(4):                                # jusqu'à ce que les jonctions ne bougent plus
            t2 = Trad(f, end); t2.phi = ph; out2 = t2.run()
            ph2 = conflits(t2, ph)
            if ph2 == ph: break
            ph = ph2
        return t2, symboles_projectiles(finaliser_args(out2))
    finally:
        CTX["proj"] = avant

_PROJ_SYM = None
def symboles_projectiles(L):
    """(2026-10-07) adresses PSP d'en-têtes / tables $88 de projectiles -> étiquettes au format arcade
    (projectiles_max.py -> donnees_projectiles_max.s)"""
    global _PROJ_SYM
    if _PROJ_SYM is None:
        try: _PROJ_SYM = {int(k, 16): v for k, v in json.load(open("projectiles_max.json")).items()}
        except FileNotFoundError: _PROJ_SYM = {}
    def rep(m):
        v = int(m.group(1), 16)
        return ("#%s, %s" % (_PROJ_SYM[v], m.group(2))) if v in _PROJ_SYM else m.group(0)
    return [re.sub(r"#\$([0-9a-f]+), (\$(?:60|88)\(a[0-6]\))", rep, l) for l in L]
def traduire(f, end=None): return traduire_trad(f, end)[1]

def traduire_tout(f, profondeur=3):
    """routine + sous-routines PSP non appariées qu'elle appelle (récursif), en un seul listing"""
    faits, a_faire, out = set(), [(f, 0)], []
    while a_faire:
        g, d = a_faire.pop(0)
        if g in faits: continue
        faits.add(g); t, lignes = traduire_trad(g)
        out.append(("psp_%x:" % g) if g != f else "; ---- PSP %06x" % g); out += lignes
        if d < profondeur: a_faire += [(h, d + 1) for h in sorted(t.sous)]
    return out

if __name__ == "__main__":
    for x in sys.argv[1:]:
        print("\n".join(traduire_tout(int(x, 16))))
