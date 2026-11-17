#!/usr/bin/env python3
# (portraits, V1, 15/11) PORT_COULEUR=1 : « ZERO 3 suit le bouton » a la SELECTION et au VS d'Hyper (etude
# work/portraits_couleurs/ETUDE.md §1.3, §3 ; decision ATTENTES-ET-DECISIONS « Couleur choisie sur les portraits »).
# Hyper impose la couleur 2 a ses portraits (selection : MOVEQ #2,D2 va 0x33BE70 ; chargeur 0x31F854 : MOVE.B #$2,D1
# va 0x31FA24) ; Upper (0x18BFE0) passe la couleur au chargeur (MOVE.B D2,D1). Regle de couleur EFFECTIVE, la meme que
# PORT_VERSION (greffe3.py, talons port_carte / port_vict) : version de base ($103 == $117 du joueur, A4) -> $129 ;
# version (ZERO / ZERO 2 / ALPHA) -> 2, comme Hyper. Aucune donnee : vraies palettes de portrait d'Upper (T_7251a0).
# Sites (code d'Hyper, ecrans de selection et VS seulement ; aucun site en combat) :
#   S1 va 0x31FA24 chargeur      : MOVE.B #$2,D1 -> MOVE.B D2,D1 ; NOP (sur place ; le 3e appelant va 0x377210 passe
#                                  deja MOVEQ #2,D2 ; le LEA de L2-04 en va 0x31FA64 n'est pas touche)
#   S2 va 0x33BE70 selection     : MOVEQ #2,D2 -> NOP (D2 = $55(A6), couleur effective de l'image precedente)
#   S3 va 0x33BEC8 selection     : MOVE.B $129(A4),$55(A6) -> JSR talon_sel (range la couleur EFFECTIVE dans $55 :
#                                  l'objet recharge donc aussi quand la VERSION change ; D0 / D1 vivants, non touches)
#   S4 va 0x3313A4/0x3313B8 VS   : MOVE.B $129(A4),D2 ; MOVE.B $C(A6),D3 -> JSR talon_vs ; NOP
#   S5 va 0x339EB8 petit sprite  : MOVEQ #2,D2 -> EXT.W D2 (16/11, v1b) : le petit sprite de la selection (objet suiveur
#                                  va 0x339AEC, homologue d'Upper 0x18A0CC qui passe $55 = $129 au chargeur 0x191320)
#                                  recoit la couleur du bouton au lieu de la couleur 2. D2 = $55(A6) (MOVE.B juste avant) ;
#                                  EXT.W met l'octet haut a zero ($55 = 0..5), car le chargeur d'Hyper 0x3429F0 prend D2 en
#                                  MOT (MOVE.W D2,D1) et n'a plus le masque d'Upper (ANDI.W #7 ; >= 6 -> 0). Meme taille et
#                                  memes cycles que MOVEQ ; le rechargement reste declenche par les memes changements ($3D
#                                  = $117, $3F, $55) : seules les couleurs ecrites dans les palettes 08 / 09 changent. Le
#                                  sprite est celui de la version de BASE ($117) : visible a l'etat 0 seulement (comme le
#                                  grand portrait), quand $103 est encore l'id ZERO 3.
# S3 n'est pose qu'avec PORT_COULEUR_SEL_VERSION=1 (defaut 0). Vu en emulateur (15/11, work/portraits_v1/ETAT.md) : a
# la selection, le grand portrait n'est visible qu'a l'etat 0 (choix du perso) ; le bouton qui valide le perso pose $129
# alors que $103 est encore l'id ZERO 3 (= $117) ; la version se choisit APRES, portrait cache. S3 n'y change donc rien a l'ecran, mais son
# cout a chaque image (2 objets) decale d'une image l'entree d'une selection dans l'essai des boutons (B1 / BC contre
# B0), alors que sans S3 le journal est identique au temoin (BS). Sans S3 : S2 + S1 donnent $129 au chargeur (regle
# d'Upper), sans aucun cycle de plus (NOP a la place de MOVEQ ; MOVE.B D2,D1 + NOP a la place de MOVE.B #2,D1).
# PORT_COULEUR=0 (defaut) : rien n'est change (temoin a l'octet).
# (16/11, v1b) A la selection, le PETIT SPRITE du perso suit aussi le bouton (S5, comme Upper) : work/portraits_v1b/ETAT.md.
# Usage autonome (prototype sur une construction figee) : port_couleur.py CARTE_IMAGE DOSSIER_ROMS [TALON_HEXA]
#   (ROM programme CPS-2 decoupees en 8 x 512 Ko, mots echanges : sz3ud.03c, sz3ud.04c, sz3.05c ... sz3.10b)
import os, struct, sys

PORT_COULEUR = os.environ.get("PORT_COULEUR", "0") == "1"
SEL_VERSION = os.environ.get("PORT_COULEUR_SEL_VERSION", "0") == "1"
TALON_DEFAUT = 0x37FF80        # re/allocations.tsv : $37FF80-$37FFA7 (haut de la plage libre $35E400-$37FFFF, sous la reserve
                               # des decors $380000 ; le code traduit croit par le bas) ; talon_sel $37FF80, talon_vs $37FF94

SITES = {   # nom : (va fichier, octets attendus en hexa)
    'S1_chargeur': (0x31FA24, '123c0002'),
    'S2_sel_moveq': (0x33BE70, '7402'),
    'S3_sel_55': (0x33BEC8, '1d6c01290055'),
    'S4_vs': (0x3313A4, '142c0129162e000c'),
    'S5_sel_sprite': (0x339EB8, '7402'),
}

def talon_sel():
    return [0x1D6C, 0x0129, 0x0055,   # MOVE.B $129(A4),$55(A6)   (instruction remplacee)
            0xB22C, 0x0103,           # CMP.B $103(A4),D1         (D1 = $117(A4), pose juste avant par Hyper)
            0x6706,                   # BEQ.S +6                  version de base : couleur du bouton
            0x1D7C, 0x0002, 0x0055,   # MOVE.B #2,$55(A6)         version : couleur 2 (Hyper)
            0x4E75]                   # RTS

def talon_vs():
    return [0x142C, 0x0129,           # MOVE.B $129(A4),D2        (instruction remplacee)
            0xB02C, 0x0103,           # CMP.B $103(A4),D0         (D0 = $117(A4), pose juste avant par Hyper)
            0x6704,                   # BEQ.S +4
            0x143C, 0x0002,           # MOVE.B #2,D2              version : couleur 2
            0x162E, 0x000C,           # MOVE.B $C(A6),D3          (instruction remplacee)
            0x4E75]                   # RTS

def lit_carte(chemin):
    """va fichier -> premiere adresse d'image (carte_image.txt : 'image va instruction')"""
    d = {}
    for l in open(chemin, encoding='utf-8'):
        p = l.split()
        if len(p) < 3: continue
        try: a, v = int(p[0], 16), int(p[1], 16)
        except ValueError: continue
        if v not in d or a < d[v]: d[v] = a
    return d

def applique(img, va_img, talon=TALON_DEFAUT, journal=print):
    """img : bytearray 68K big-endian (adresse 0 = 0). Retourne la liste des retouches (adresse, avant, apres)."""
    if not PORT_COULEUR: return []
    a = {}
    for n, (va, att) in SITES.items():
        if n == 'S3_sel_55' and not SEL_VERSION: continue
        k = va_img.get(va); b = bytes.fromhex(att)
        assert k is not None, '%s : va %x absente de la carte' % (n, va)
        assert img[k:k + len(b)] == b, '%s : $%x vaut %s, attendu %s' % (n, k, img[k:k + len(b)].hex(), att)
        a[n] = k
    ts, tv = talon_sel(), talon_vs()
    t_sel, t_vs = talon, talon + 2 * len(ts)
    fin = t_vs + 2 * len(tv)
    assert not any(img[talon:fin]), 'talon : $%x-$%x non vide' % (talon, fin)
    R = []
    def pose(k, mots):
        avant = bytes(img[k:k + 2 * len(mots)])
        for i, w in enumerate(mots): struct.pack_into('>H', img, k + 2 * i, w)
        R.append((k, avant.hex(), bytes(img[k:k + 2 * len(mots)]).hex()))
    if SEL_VERSION: pose(t_sel, ts)
    pose(t_vs, tv)
    pose(a['S1_chargeur'], [0x1202, 0x4E71])                                     # MOVE.B D2,D1 ; NOP
    pose(a['S2_sel_moveq'], [0x4E71])                                            # NOP
    if SEL_VERSION: pose(a['S3_sel_55'], [0x4EB9, t_sel >> 16, t_sel & 0xFFFF])  # JSR talon_sel
    pose(a['S4_vs'], [0x4EB9, t_vs >> 16, t_vs & 0xFFFF, 0x4E71])                # JSR talon_vs ; NOP
    pose(a['S5_sel_sprite'], [0x4882])                                           # EXT.W D2
    for k, av, ap in R: journal('PORT_COULEUR : $%06x %s -> %s' % (k, av, ap))
    return R

ROMS = ['sz3ud.03c', 'sz3ud.04c', 'sz3.05c', 'sz3.06c', 'sz3.07c', 'sz3.08c', 'sz3.09c', 'sz3.10b']

def _swap(b):
    b = bytearray(b); b[0::2], b[1::2] = b[1::2], b[0::2]; return b

if __name__ == '__main__':
    carte, dossier = sys.argv[1], sys.argv[2]
    talon = int(sys.argv[3], 16) if len(sys.argv) > 3 else TALON_DEFAUT
    img = bytearray()
    for r in ROMS: img += _swap(open(os.path.join(dossier, r), 'rb').read())
    R = applique(img, lit_carte(carte), talon)
    if not R: print('PORT_COULEUR=0 : rien'); sys.exit(0)
    touches = sorted({k // 0x80000 for k, av, ap in R} | {(k + len(ap) // 2 - 1) // 0x80000 for k, av, ap in R})
    for i in touches:
        p = os.path.join(dossier, ROMS[i])
        assert not os.path.islink(p), '%s est un lien : copier d\'abord' % p
        open(p, 'wb').write(_swap(img[i * 0x80000:(i + 1) * 0x80000]))
        print('ecrit', ROMS[i])
