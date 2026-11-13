#!/usr/bin/env python3
"""(ciel_ryu, S1_MIROIR) TUILES SCROLL1 RANGEES EN MIROIR PAR LE PORTAGE (SFA3 seulement).

SFA3 traduit garde la ROM graphique d'arcade : les codes de tuiles des plans sont des indices LOCAUX de la memoire de
decor du portage (e256), renumerotes a l'ecriture en VRAM par la table plan1 (banques.py plans256 ; banc_plans.lua /
cps_hsfa.cpp HsfaConvertit). plans256 n'apparie que le contenu EXACT (moitie gauche). Or le portage a range certaines
tuiles de decor RETOURNEES et les emploie avec le bit de retournement : local $4CA8 = miroir X de l'arcade $4D98, pose
avec attr $20 (decor $00 / $2E, ciel de Ryu). Sans entree exacte, plan1 = VIDE (ou indice hors de la fenetre scroll1)
-> le pilote garde le code brut $4CA8 = AUTRE tuile de la ROM d'arcade, toujours retournee -> trainees du ciel.

Correction (donnees, deux volets coherents) :
  1. image : dans la table des super-tuiles scroll1 (16 x (attr, code), mots), l'attribut de chaque case dont le code
     est un local L de la liste est XORe avec T(L) (bits $20 X / $40 Y) ;
  2. table plan1 : plan1[L] = $20000 + code arcade C(L), avec T(ROM(C)) == tuile du portage, sur les DEUX moities
     (la moitie affichee depend de la parite de colonne). (v157) Ecrit par banques.py plans256 (MODULE=ro3) : la
     correction suit donc toute chaine qui produit plan1.bin (atelier work/mame/banques, hsfa_build.py depuis l'ISO),
     avec controle du contenu dans la ROM employee.
Le portage affiche T_a(PS2(L)) = T_a(T(ROM(C))) ; la traduction affiche alors ROM(C) avec attr a ^ T : identique.
Quand plusieurs (C, T) donnent les memes pixels (tuile symetrique), on garde celui que l'arcade emploie a ces cases
($2805 : $09E1 en XY ; $084A : $02D6 en Y) : la tilemap est alors identique a l'arcade au mot pres.
Les locaux viennent de l'examen site par site (work/ciel_ryu : statique_s1.py, solutions.py) : 21 tuiles, 156 cellules
sur 18 decors (blocs des listes de decor), dont 59 sur $00 / $2E. Variables :
  S1_MIROIR=0       : v154 a l'octet (rien n'est touche) ;
  S1_MIROIR_SEUL=L,L,... (hexa) : sous-ensemble de la liste (defaut : toute la liste examinee).
Seule la table des super-tuiles est touchee : aucun autre emploi des 21 locaux en scroll1 (recherche dans l'image)."""
import os, struct

# local : (T, code arcade)  — T = bits a XORer dans l'attribut ($20 X, $40 Y)
LISTE = {
    0x02C6: (0x60, 0x08F3), 0x084A: (0x40, 0x02D6), 0x2805: (0x60, 0x09E1), 0x2806: (0x60, 0x09E4),
    0x426F: (0x40, 0x0A53), 0x4BE6: (0x20, 0x4CD6), 0x4C05: (0x20, 0x4CF5), 0x4C24: (0x20, 0x4D14),
    0x4C3A: (0x20, 0x4D2A), 0x4C59: (0x20, 0x4D49), 0x4C71: (0x20, 0x4D61), 0x4C85: (0x20, 0x4D75),
    0x4C97: (0x20, 0x4D87), 0x4CA8: (0x20, 0x4D98), 0x4CAB: (0x20, 0x4D9B), 0x4CB4: (0x20, 0x4DA4),
    0x4CCB: (0x20, 0x4DBB), 0x4CE9: (0x20, 0x4DD9), 0x4D06: (0x20, 0x4DF6), 0x4D21: (0x20, 0x4E11),
    0x4D34: (0x20, 0x4E24),
}
# table des super-tuiles scroll1 du portage (adresses d'execution ro3) : $5FA1B0 .. blocs scroll2 $61F3F0
ST_VA, ST_FIN_VA = 0x5FA1B0, 0x61F3F0

ACTIF = os.environ.get("S1_MIROIR", "1") != "0"

def choisis():
    s = os.environ.get("S1_MIROIR_SEUL", "")
    if not s: return dict(LISTE)
    keep = {int(x, 16) for x in s.split(",") if x}
    return {k: v for k, v in LISTE.items() if k in keep}

def corrige_image(img, va2img):
    """XOR des attributs dans la table des super-tuiles ; rend [(adresse image de la case, local, attr avant, apres)]."""
    L = choisis(); faits = []
    a0, a1 = va2img(ST_VA), va2img(ST_FIN_VA)
    assert a0 is not None and a1 is not None and (a1 - a0) % 0x40 == 0, "table des super-tuiles introuvable"
    for o in range(a0, a1, 4):
        at, c = struct.unpack_from(">HH", img, o)
        if c in L and L[c][0]:
            n = at ^ L[c][0]
            struct.pack_into(">H", img, o, n); faits.append((o, c, at, n))
    return faits

def flip(a, T):
    """retournement d'une tuile (tableau lignes x colonnes) : $20 = X, $40 = Y"""
    if T & 0x20: a = a[:, ::-1]
    if T & 0x40: a = a[::-1, :]
    return a

def corrige_plan1(t, px, S, idx=None, fenetre=(0x20000, 0x2FFFF)):
    """table plan1 (banques.py plans256 ; t = indices ROM en unites de 8 lignes, px = pixels de la memoire de decor
    du portage, S = ROM decodee en lignes de 16 px) : t[L] = k tel que T(ROM(k)) == tuile du portage sur les DEUX
    moities (la moitie affichee depend de la colonne). k = $20000 + C(L) de la liste si la ROM le confirme (ROM
    d'arcade ET ROM reconstruite depuis l'ISO), sinon recherche par contenu (idx : moitie gauche -> indices), fenetre
    du plan d'abord. Rend [(L, T, k ou None, origine)] ; None = rien trouve (entree laissee telle quelle)."""
    import numpy as np                       # (mame_test n'importe que corrige_image : pas de numpy pour l'etape prog)
    res = []
    for L, (T, C) in sorted(choisis().items()):
        if not T: continue
        voulu = np.ascontiguousarray(flip(px[L*64:(L+1)*64].reshape(8, 8), T))
        ok = lambda k: 0 <= 8*k and 8*k+8 <= len(S) and (S[8*k:8*k+8, :8] == voulu).all() and (S[8*k:8*k+8, 8:] == voulu).all()
        k, d = 0x20000 + C, "liste"
        if not ok(k):
            cands = [y for y in (idx.get(voulu.astype(np.uint8).tobytes(), []) if idx else []) if ok(y)]
            cands.sort(key=lambda y: (not (fenetre[0] <= y <= fenetre[1]), y))
            k, d = (cands[0], "recherche") if cands else (None, "absente")
        if k is not None: t[L] = k
        res.append((L, T, k, d))
    return res
