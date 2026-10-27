#!/usr/bin/env python3
"""(agent_integration_max) PRÉPARATION DU CODE ET DES DONNÉES MAX pour une construction d'Upper avec MAX=1.

Le code MAX converti appelle le moteur d'Upper par adresses d'image (UP_xxxxx) : il dépend de la carte de l'image.
MAX=1 ne change pas la traduction (seulement des données, des tables et des blocs externes) : la carte d'une
construction d'Upper SANS MAX (option à 0) vaut donc pour la construction AVEC MAX ; mame_test.py le vérifie (md5 de
la carte).

Usage : prepare_max.py [--ref DOSSIER_DE_CONSTRUCTION] [--sortie DOSSIER]
  1. convertit_max.py (copie de conv/) : sources MAX (max_trad/rosette_code, + gestionnaires d'Eagle) -> image d'Upper ;
  2. integration_max.s (enveloppes des rappels, données de combat par perso, zones remplies à la construction) ;
  3. vasm : tout à l'adresse MAX_ORG ($B80000, hors des plages converties par CONV) -> ext_b80000.bin + symboles.json ;
  4. blocs externes des frames / animations (conv/sortie/ext_d40000.bin ... ext_e00000.bin, convertit_frames.py)."""
import os, sys, re, json, hashlib, shutil, subprocess, argparse
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(RACINE, "untranspile"))
import donnees_joueur_max as DJ
VASM = os.path.expanduser("~/outils/vasm/vasmm68k_mot")
SRC = os.path.join(RACINE, "max_trad", "rosette_code")
MAX_ORG = 0xB80000                    # DONNÉES MAX (lues par le moteur via CONV : hors des plages converties)
CODE_ORG = 0x3A0000                   # CODE MAX : DANS l'image de 4 Mo (le fork n'exécute que $0-$3FFFFF : carte des
CODE_RESERVE = 0x3C0000 - CODE_ORG    # opcodes déchiffrés) ; mame_test.py (MAX=1) abaisse d'autant le plafond des données
BLOC_EAGLE = 0xE40000                 # bloc des frames / animations d'Eagle DÉPLACÉ ($D40000 -> $E40000) : la fin des
                                      # données d'Upper ($C80000) grandit (code MAX dans l'image) et chevaucherait $D40000
PERSOS = json.load(open(os.path.join(ICI, "persos_max.json")))

CALQUES_MAX = {0x33, 0x34, 0x2F, 0x30, 0x31} if os.environ.get("MAX_CALQUES_SENS", "0") == "1" else set()   # inversion NON retenue : calque déjà du bon côté des deux sens (essais/b12/calque_g.png)
# (2b19) flammes sur une victime MAX : index du pas jusqu'à 21 (PSP, octet +$11 sans masque) alors qu'Upper masque par
# $F (image $32D5C, chemin des NATIFS laissé STRICTEMENT intact : tout ajout sur ce chemin décalait la nonreg, coût en
# cycles). A chaque passe d'un perso MAX (enveloppes MAX_ENTREES*), ses flammes (objets classe 4 / sous-type $26, parent
# $36 = lui) reçoivent $40 = FLAMMES_xx (index < 16) ou FLAMMES_xx + 32 (index >= 16) : (index & $F)·2 + base = index·2.
FLAMMES_AJ = os.environ.get("MAX_FLAMMES_IDX", "aj") == "aj"
FL_AJ = "        jsr     MAX_FLAMMES_AJ" if FLAMMES_AJ else ""
def flammes_aj():
    if not FLAMMES_AJ: return []
    L = ["MAX_FLAMMES_AJ:", "        movem.l d0-d1/a0-a1, -(sp)",
         "        move.l  $1c(a6), d0", "        swap    d0", "        movea.l d0, a0", "        jsr     $400.w",
         "        moveq   #0, d1", "        move.b  $10(a0), d1"]
    for k, pid in enumerate(("26", "27", "2d", "2e")):
        L += ["        lea     FLAMMES_%s, a1" % pid.upper(), "        cmpi.b  #$%s, $103(a6)" % pid, "        beq.s   .base"]
    L += ["        bra.s   .fin", ".base:  cmpi.w  #16, d1", "        bcs.s   .b0", "        lea     32(a1), a1",
          ".b0:    move.l  a1, d0", "        swap    d0", "        move.w  a6, d1", "        lea     $ffb000, a0",
          ".obj:   tst.b   1(a0)", "        beq.s   .suiv", "        cmpi.b  #4, 3(a0)", "        bne.s   .suiv",
          "        cmpi.b  #$26, 2(a0)", "        bne.s   .suiv", "        cmp.w   $36(a0), d1", "        bne.s   .suiv",
          "        move.l  d0, $40(a0)",
          ".suiv:  lea     $80(a0), a0", "        cmpa.l  #$ffd000, a0", "        bcs.s   .obj",
          ".fin:   movem.l (sp)+, d0-d1/a0-a1", "        rts"]
    return L

# (2b21) « PALETTE PROPRE » des acteurs de fin (session MAX : record +4 bit 0 -> $18) : un acteur dessiné avec les frames du
# perso MAX du JOUEUR lui-même ($7E = n° de banque = ID du joueur de la fin, $13C(A5)) prend la palette de COMBAT du joueur
# (couleur choisie : pointeur $14C du joueur, 1re palette du jeu de la couleur) recopiée dans la palette OBJ 31 (libre :
# les x9 des fins en chargent 30) ; les invités gardent les palettes de la fin. Appelé à la fin du générateur ($1B1C).
def palpropre():
    # joueur de la fin = J1 ou J2 dont l'ID (MAX) correspond à la banque de l'acteur ($7E = n° PSP : $26, $27, $28, $29) ;
    # palette recopiée dans l'emplacement OBJ 31 des TROIS tampons de palettes ($90C000 et ceux des fins $91C000 / $920000,
    # échangés à chaque scène : base = long $C140(A5))
    return ["MAX_PALPROPRE:", "        move.b  #$ff, $d(a4)", "        btst    #0, $18(a4)", "        beq.s   .x",
            "        movem.l d0/a0-a1, -(sp)", "        lea     $ff8400, a0", "        bsr.s   .t", "        beq.s   .ok",
            "        lea     $ff8800, a0", "        bsr.s   .t", "        bne.s   .f",
            ".ok:    move.b  #30, $c(a4)", "        move.l  $14c(a0), d0", "        swap    d0", "        movea.l d0, a0",
            "        lea     $90c3c0, a1", "        bsr.s   .cp", "        lea     $91c3c0, a1", "        bsr.s   .cp",
            "        lea     $9203c0, a1", "        bsr.s   .cp",
            ".f:     movem.l (sp)+, d0/a0-a1", ".x:     rts",
            ".cp:    move.l  a0, -(sp)", "        moveq   #7, d0", ".c:     move.l  (a0)+, (a1)+", "        dbra    d0, .c",
            "        movea.l (sp)+, a0", "        rts",
            ".t:     move.b  $103(a0), d0", "        cmpi.b  #$26, d0", "        bcs.s   .n", "        cmpi.b  #$2d, d0",
            "        bcs.s   .b", "        subq.b  #5, d0", ".b:     cmp.b   $7e(a4), d0", "        rts",
            ".n:     moveq   #1, d0", "        rts"]

def integration():
    """source vasm (disposition IMAGE, non convertie) des points d'entrée et des données propres à l'intégration"""
    D = ["; ==== integration_max.s, DONNÉES (agent_integration_max, prepare_max.py) — disposition IMAGE, NON convertie"]
    L = ["; ==== integration_max.s, CODE (agent_integration_max, prepare_max.py) — disposition IMAGE, NON convertie",
         "        even",
         "; miroir des entrées au format PSP (psp_entrees) avant chaque rappel d'un perso MAX : registres et CCR gardés",
         # (18/10 nuit, 2) MAX_ENTREES_TICK : enveloppe du rappel des MANIPS (749658), appelé une fois par passe de la
         # logique (parfois 2 passes pour un même compteur d'images) : front recalculé à chaque passe ; les autres rappels
         # (MAX_ENTREES) reprennent ce front, et ne le recalculent que si le compteur d'images a changé sans passe de manips
         "MAX_ENTREES_TICK:",
         "        move.w  sr, -(sp)",
         "        movem.l d0-d2, -(sp)",
         "        jsr     psp_entrees",
         FL_AJ,
         "        move.w  $ff80b4.l, d1",
         "        bra.s   MAXE_NEUF",
         "MAX_ENTREES:",
         "        move.w  sr, -(sp)",
         "        movem.l d0-d2, -(sp)",
         "        jsr     psp_entrees",
         FL_AJ,
         # (18/10) Upper ne tient pas $378 (« appuyé à l'instant ») pendant un coup spécial (ex. course de Maki : suites
         # au pied jamais vues) : $3E2 recalculé depuis $370 (tenu) et $374 (tenu à l'image précédente) si $378 = 0
         # (18/10 nuit) TOUJOURS depuis $370 & ~$374 : le $378 d'Upper garde un appui plusieurs images (tolérance des
         # manips) ; le $3E2 du PSP est l'appui de l'image. Sinon le pied qui lance la course de Maki est revu par l'état 1
         # deux images plus tard (petit pied -> arrêt de la course, moyen pied -> glissade aussitôt…)
         # $374 d'Upper n'est pas tenu pendant certains coups spéciaux (vu au banc : 2 images sans mise à jour) -> front
         # calculé ici, une fois par image (compteur d'images $FF80B4) : $3FA = tenu à l'image précédente, $3F8 = front,
         # $3F6 = image du calcul (champs $3F6-$3FA libres dans Upper et dans le code MAX)
         "        move.w  $ff80b4.l, d1",
         "        cmp.w   $3f6(a6), d1",
         "        beq.s   MAXE_MEME",
         "MAXE_NEUF:",
         "        move.w  d1, $3f6(a6)",
         "        move.w  $3fa(a6), d0",
         "        not.w   d0",
         "        and.w   $370(a6), d0",
         "        move.w  d0, $3f8(a6)",
         "        move.w  $370(a6), $3fa(a6)",
         "MAXE_MEME:",
         "        move.w  $3f8(a6), d0",
         "        move.w  d0, d1",
         "        move.w  d0, d2",
         # (18/10 soir) même conversion que psp_entrees .conv (session MAX) : POINGS bits 8-10 -> PSP $10/$20/$40,
         # PIEDS bits 12-14 -> PSP $80/$100/$200
         "        andi.w  #$000f, d0",
         "        andi.w  #$0700, d1",
         "        lsr.w   #4, d1",
         "        or.w    d1, d0",
         "        andi.w  #$7000, d2",
         "        lsr.w   #5, d2",
         "        or.w    d2, d0",
         "        move.w  d0, $3e2(a6)",
         ".e1:",
         "        movem.l (sp)+, d0-d2",
         "        move.w  (sp)+, ccr",
         "        rts"]
    # (18/10) objets d'EFFET MAX (réservoir $1C368) : les gestionnaires traduits n'inscrivent pas l'objet à l'affichage
    # (arcade $1B4D0 = UP_1B4D0, que les effets d'Upper appellent eux-mêmes) -> enveloppe : drapeau d'inscription
    # (octet image 0) remis à 0, gestionnaire, puis inscription si l'objet vit encore et ne s'est pas inscrit lui-même
    import sys as _s; _s.path.insert(0, os.path.join(RACINE, "untranspile"))
    import integre_max as _IM
    L += flammes_aj()
    if os.environ.get("MAX_PALPROPRE", "1") == "1": L += palpropre()
    L.append("; enveloppes des classes d'effets MAX (table MAX_T_EFFETS)")
    for pid_, cl_ in _IM.CLASSES.items():
        for c_, r_ in sorted(cl_.items()):
            # (pas de remise à 0 de l'octet image 0 : à 0, $1B4D0 réinitialise l'animation par la table des TYPES d'Upper
            # $A9510, hors bornes pour les types MAX -> erreur d'adresse, VERSUS Eagle-Ryu image 2340)
            # (18/10 soir, session MAX) classe d'affichage ($9 image, table $19DDC indexée par ($9 - 8)/2) mise à $10
            # ($19ED0 : simple inscription dans les listes) au lieu de $18 (EFFETS -> $1DFF2, qui refait l'animation par
            # TYPE, hors bornes pour les types MAX : pas $1C écrasé, plantage VERSUS image 2340) ; comme les projectiles MAX
            # (18/10, session MAX) inscription seulement si l'objet est VISIBLE : octet $1 arcade = octet 0 de l'image
            # (calques permanents d'Eagle / Maki, montrés par FUN_001B3B1C selon l'octet $12 du pas)
            # (2b12) CALQUES permanents (Eagle $33/$34, Maki $2F-$31 : recopient X/Y/sens du joueur) : la classe $10 les
            # retourne à l'inverse des joueurs -> sens = celui du parent ($36) INVERSÉ (octet $B arcade = $A image)
            sens = ["        movem.l d0/a0, -(sp)", "        movea.w $36(a6), a0", "        move.b  $a(a0), d0",
                    "        eori.b  #1, d0", "        move.b  d0, $a(a6)", "        movem.l (sp)+, d0/a0"] if c_ in CALQUES_MAX else []
            # (2b13) effets additifs : bit 12 du masque X $18(A6) (les écrivains de la passe de dessin font OR.W $18(A6),D0)
            # selon MAX_ALPHA[(A6.w - $9400) >> 7] (table écrite par le code MAX, session MAX) ; $804240 = 1 (mode additif)
            alpha = ["        movem.l d0/a0, -(sp)", "        move.w  a6, d0", "        subi.w  #$9400, d0", "        lsr.w   #7, d0",
                     "        lea     $ff7f00, a0", "        tst.b   0(a0, d0.w)", "        beq.s   .z",
                     "        ori.w   #$1000, $18(a6)", "        move.w  #1, $804240", "        bra.s   .x",
                     ".z:     andi.w  #$efff, $18(a6)", ".x:     movem.l (sp)+, d0/a0"] if os.environ.get("MAX_ALPHA_EFFETS", "1") == "1" else []
            # (2b18) bit 12 posé AVANT le test de l'octet 0 : les rémanences d'Ingrid (classe $35, 2xQCB+K) ont
            # l'octet 0 à 0 mais s'inscrivent elles-mêmes (visibles, dessinées opaques sans le bit) ; le bit n'est
            # retiré que si l'objet est LIBÉRÉ (octet 1 à 0 : le slot peut être repris par un objet natif)
            if alpha and os.environ.get("MAX_ALPHA_REMANENCES", "1") == "1":
                L += ["EFFET_W_%02X:" % c_, "        jsr     %s" % r_, "        tst.b   1(a6)", "        beq.s   .f"] + alpha + [
                      "        tst.b   (a6)", "        beq.s   .r", "        move.b  #$10, $9(a6)"] + sens + ["        jmp     UP_1B4D0",
                      ".f:     andi.w  #$efff, $18(a6)", ".r:     rts"]
                continue
            L += ["EFFET_W_%02X:" % c_, "        jsr     %s" % r_, "        tst.b   (a6)",
                  "        beq.s   .f", "        move.b  #$10, $9(a6)"] + sens + alpha + ["        jmp     UP_1B4D0",
                  # (2b14) objet invisible / libéré : bit 12 retiré (le slot peut être repris par un objet natif)
                  ".f:     andi.w  #$efff, $18(a6)" if alpha else ".f:", "        rts"]
    # (2b14) TIRS MAX (réservoirs des projectiles, gestionnaire posé dans T_PROJ par integre_max) : même marquage
    if os.environ.get("MAX_ALPHA_EFFETS", "1") == "1":
        for pid_, fils_ in (("26", "psp_fils_26"), ("2d", "psp_fils_28"), ("2e", "psp_fils_29")):
            L += ["TIR_W_%s:" % pid_, "        jsr     %s" % fils_, "        tst.b   (a6)", "        beq.s   .z",
                  "        movem.l d0/a0, -(sp)", "        move.w  a6, d0", "        subi.w  #$9400, d0", "        lsr.w   #7, d0",
                  "        lea     $ff7f00, a0", "        tst.b   0(a0, d0.w)", "        movem.l (sp)+, d0/a0", "        beq.s   .z",
                  "        ori.w   #$1000, $18(a6)", "        move.w  #1, $804240", "        rts",
                  ".z:     andi.w  #$efff, $18(a6)", "        rts"]
    for pid, P in PERSOS.items():
        if pid.startswith("_"): continue
        if not P.get("actif"): continue
        L.append("; ---- %s ($%s) : enveloppes des rappels (tables par perso d'Upper)" % (P["nom"], pid))
        for tab, rappel in P["rappels"].items():
            L += ["MAXW_%s_%s:" % (pid, tab), "        jsr     %s" % ("MAX_ENTREES_TICK" if tab == "749658" else "MAX_ENTREES")]
            if tab == "74c038" and os.environ.get("MAX_IA_A0", "1") == "1":
                # (2b23) IA du CPU : l'appelant natif ($DCD4 -> $F5DC -> table, puis BSR $ED48) garde en A0 le pointeur
                # de script IA à travers le rappel ; les rappels natifs ne touchent que D0/D1, ceux du PSP prennent A0
                # pour leur table de sauts (lea J_xxx(pc),a0 ; jmp (a0)) -> A0 sauvé ici (MOVEA ne touche pas le CCR :
                # le résultat Z de MOVEQ #0/#1 est rendu intact). Plantage $A0A, Yun CPU, image 3052 (essais/b27)
                L += ["        move.l  a0, -(sp)", "        jsr     %s" % rappel, "        movea.l (sp)+, a0", "        rts"]
            else:
                L += ["        jmp     %s" % rappel]
        D.append(DJ.asm(P["pl"], "MAXD_%s" % pid))
        D += ["        even", "MAXPAL_%s:" % pid] + DJ_pal(P["pl"])
        D += habillage(pid, P["pl"])
    D += ["        even",
          "; table des classes du réservoir d'effets $4800(A5) (T_60d070, 40 entrées) DÉPLACÉE et agrandie à 64 :",
          "; remplie à la construction (mame_test.py, MAX=1) : 40 entrées d'Upper relogées + classes MAX $2F-$3A",
          "MAX_T_EFFETS:", "        ds.l    64",
          "; table des palettes par perso (T_6f72b0) DÉPLACÉE : 64 entrées + blocs recopiés + blocs MAX (remplie à la construction)",
          "MAX_PAL_ZONE:", "        ds.b    $A000",
          "; table des palettes d'EFFETS par perso (T_700540) DÉPLACÉE, même schéma",
          "MAX_PALE_ZONE:", "        ds.b    $A000",

          "MAX_FIN:"]
    # (18/10 nuit, session MAX) positions de projection (table 7495b8) : lignes MAX (PROJ_POS_xx) et lignes natives
    # étendues à 48 colonnes (PROJ_NAT_00-25) ; mots seulement (disposition image = source) ; posées par integre_max
    # (2b12) bandeau « WINNER : nom » (session MAX : converti/bandeau_noms/bandeau_noms_max.s, disposition image)
    for fb in (MC.CV + "bandeau_noms/bandeau_noms_max.s", MC.CV + "winner_noms/winner_noms_max.s",
               MC.CV + "carte_noms/carte_noms_max.s", MC.CV + "flammes/flammes_max.s", MC.CV + "recul/recul_max.s",
               MC.CV + "bandeau_noms/frises_verticales_max.s"):
        # frames $0C : le lecteur du portage prend le pointeur des positions à l'adresse ALIGNÉE (frame + 6 arrondi à 4)
        # -> chaque frame doit commencer sur 4 (MAXWIN_26 en ≡ 2 mod 4 : entrées lues décalées d'un mot, relevé 2b12)
        if not os.path.exists(fb): continue
        t_ = re.sub(r"^((?:MAXWIN_|MAXBN_|MAXCARTE_|MAXBV_)\w+:)", r"        cnop    0,4\n\1", open(fb).read(), flags=re.M)
        D += ["        cnop    0,4", "; ---- %s (session MAX)" % os.path.basename(fb), t_, "        even"]
    # (2b19) flammes : index du pas masqué par & $1F (au lieu de $F) pour TOUS (même instruction, même coût : la nonreg
    # bougeait avec un JSR de test) ; les natifs reçoivent une copie DOUBLÉE de leurs 16 couples (entrée k+16 = entrée k)
    # -> résultat identique à & $F ; MAX : 22 couples (FLAMMES_xx). Données natives lues dans le fichier ro5 d'origine.
    D += recul_types() + anim_reactions()
    if os.environ.get("MAX_FLAMMES_IDX", "aj") == "dup":
        D += ["        even", "; ---- flammes natives doublées (0x74C358, ordre image)"] + flammes_natives()
    for f in ("projections_max.s", "projections_natifs_max.s"):
        fp = os.path.join(SRC, f)
        if os.path.exists(fp): D += ["        even", "; ---- %s (session MAX)" % f, open(fp).read(), "        even"]
    return "\n".join(L) + "\n", "\n".join(D) + "\n"

import max_cache as MC
G0, PB1 = MC.G0, MC.PB1               # tuiles des portraits / noms / icônes MAX : plan2 prolongé (MAX_PORTRAITS, §130)
def code_plan2(g): return PB1 + (g - G0) - 0x1C00   # code de frame (u16) d'une tuile globale g (rendu : + $1C00 -> plan2)

def habillage(pid, pl):
    """nom (frame de type $0C, cartouche de la sélection) et bandeaux défilants (4 enregistrements) — session MAX :
    converti/noms/noms.json, bandeau.json ; tuiles dans max_portraits_gfx.bin ; disposition IMAGE"""
    C = MC.CV + "noms/"
    N = json.load(open(C + "noms.json"))[pl]; B = json.load(open(C + "bandeau.json"))[pl]
    sw = lambda v: "$%08X" % (((v & 0xFFFF) << 16) | (v >> 16))
    w = N["largeur_tuiles"]; pos = int(N["frame_type_0C"]["positions"].split()[0], 16)
    g = MC.code_nom(N)
    L = ["        cnop    0,4", "MAXNOM_%s:" % pid,
         "        dc.w    $000C, %d, 0, 0" % w, "        dc.l    %s" % sw(pos),
         "        dc.w    $%04X, $%04X" % (code_plan2(g), N["attribut"]), "        dc.w    0, 0"]
    for k in ("J1_JP", "J1_US", "J2_JP", "J2_US"):
        m = B[k]["mots_u16"]; L += ["        even", "MAXBAND_%s_%s:" % (pid, k)]
        for x in m:
            if x.startswith("<u32"): L.append("        dc.l    %s" % sw(int(x.split()[1].rstrip(">"), 16)))
            else: L.append("        dc.w    $%s" % x)
    return L

def DJ_pal(pl):
    im = DJ.swapw(DJ.palettes_corps(pl))
    return ["        dc.b    " + ",".join("$%02x" % x for x in im[i:i + 16]) for i in range(0, len(im), 16)]

def symboles_listing(lst):
    """table des symboles de la liste vasm (-L) : « NOM  ... $ADRESSE » / format 'Symbols by name'"""
    S = {}; dans = False
    for l in open(lst, errors="replace"):
        if l.startswith("Symbols by name"): dans = True; continue
        if dans:
            m = re.match(r"^(\S+)\s+(?:[A-Z]:)?([0-9A-Fa-f]{6,8})\b", l)
            if m: S[m.group(1)] = int(m.group(2), 16)
    return S

# psp_cfb6c (PSP 0xCFB6C) : l'index D1 est un OCTET (lbu côté PSP) ; tous les appelants le chargent par move.b (bits
# 8-15 de D1 non nuls : 0x108 relevé, Ingrid contre Yun/Maki -> erreur d'adresse en $51AB2) -> extension à 16 bits
# SONS_COMMUNS (moteur_max_main.s) livrée à zéro (bruitages communs MAX muets) : appariement de l'agent voix MAX
# (work/agent_voix_max/sons_communs_max.s ; confiance forte/moyenne seulement ; $06 faible et $2E sans équivalent : muets)
SONS_COMMUNS_IMAGE = "SONS_COMMUNS:   ; (agent_integration_max) appariement agent_voix_max/sons_communs_max.s\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0239, $0000, $0257, $0000, $0000, $0000, $0000, $0263, $0000, $0000, $0000, $023E, $0000, $0000, $0000, $0000\n        dc.w    $022E, $0000, $0000, $0000, $0000, $0000, $023B, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n        dc.w    $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000, $0000\n"
CORRECTIFS = [("moteur_max_main.s", "psp_cfb6c:\n        movea.l d0, a0\n",
               "psp_cfb6c:\n        andi.w  #$ff, d1                ; (agent_integration_max) index octet (lbu)\n        movea.l d0, a0\n"),
              # (SONS_COMMUNS : la source de la session MAX est remplie depuis le 2026-10-17 -> plus de correctif)
              # psp_78408 : n° de perso du joueur (structure $FF8400 + $400 k) : la passe ne connaît pas A0 (movea.l #) ->
              # écrit directement en disposition IMAGE ($102 arcade = $103 image)
              ("moteur_max_main.s", "        move.b  $102(a0), d2\n", "        move.b  $103(a0), d2          ; (agent_integration_max) image : $102 arcade\n"),
              # explosion des fins ($4F/$19) : 1er pas arcade $2E565C ($2E50A0 n° 5) relogé sur Upper = PS2 0x65AD80 n° 5
              # (mêmes décalages d'en-tête qu'en arcade) -> sinon pas lu en adresse arcade : erreur d'adresse $2C736
              ("symboles_externes_max.s", "EXPLO_PAS equ $2E565C ", "EXPLO_PAS equ $65B33C "),
              # (2b17) Ingrid, liste chaînée des effets de super (psp_1c6d58, champs $28/$2A/$2C/$2E, racine $28 du joueur) :
              # un objet libéré puis réalloué restait chaîné ; réinséré, il bouclait la liste -> boucle infinie (jeu figé
              # après 3 supers 2xQCF+P, banc image 3392). Garde : objet déjà présent comme nœud ou dans un emplacement -> fin
              ("brouillon_ingrid.s", "L_1c6d78:\n        move.l  d6, d3\n        tst.l     d3\n        beq     T_1c6d78\n",
               "L_1c6d78:\n        move.l  d6, d3\n        tst.l     d3\n        beq     T_1c6d78\n"
               "        cmp.w   d0, d6                ; (agent_integration_max) nœud = objet à insérer : déjà chaîné\n"
               "        beq     L_1c6da8\n"
               "        cmp.w   d0, d5                ; (agent_integration_max) nœud courant = objet à insérer\n"
               "        beq     L_1c6da8\n"
               "        cmp.w   d5, d6                ; (agent_integration_max) nœud qui se désigne lui-même : fin\n"
               "        beq     L_1c6da8\n")]
              # (18/10 soir) saisie d'Ingrid / chope de Maki : correctifs provisoires $5F->$5E… RETIRÉS (A0 annoté par la
              # session MAX le 18/10 nuit ; bases_forcees.tsv si la passe ne le prend pas)
              # (TYPE_PROJ_YUN / _INGRID = $2D / $2E : repris dans la source MAX le 17/10 -> plus de correctif)

def sources(out):
    """copie des sources MAX (max_trad/rosette_code : copie de la session MAX + gestionnaires d'Eagle) -> out/src ;
    bloc d'Eagle déplacé en BLOC_EAGLE (org des 4 fichiers + valeurs des symboles $D40000-$D7FFFF)"""
    src = os.path.join(out, "src")
    if os.path.exists(src): shutil.rmtree(src)
    shutil.copytree(SRC, src, ignore=shutil.ignore_patterns("__pycache__", "sauvegardes", "*.py", "*.json", "*.md"))
    for f in ("physique_max_arcade.json",): shutil.copy(os.path.join(SRC, f), src)
    # (2b11) cache MAX choisi (SFA3MAX_CACHE, ex. version ÉTIRÉE) : ses frames_*.s / symboles_frames_max.s remplacent
    # ceux de rosette_code (seuls fichiers .s qui changent)
    if os.path.isdir(MC.S_DIR) and os.environ.get("SFA3MAX_CACHE"):
        for f in sorted(os.listdir(MC.S_DIR)):
            if f.endswith(".s"): shutil.copy(os.path.join(MC.S_DIR, f), os.path.join(src, f))
        print("frames du cache %s : %s" % (MC.RACINE, ", ".join(f for f in sorted(os.listdir(MC.S_DIR)) if f.endswith(".s"))))
    # psp_1b07bc (gestionnaires_main.s de la session MAX) : notre version, dont la boucle (après « lea 20(a0) », sans
    # genre connu pour la passe) est écrite en disposition IMAGE et vérifiée sur les données : octet 0 = drapeaux
    # ($80/$40), octet 1 = durée, octet 8 = attaque (pas de fin d'Eagle « 80 16 … », de Ryu dans Upper « 00 05 … »)
    f = os.path.join(src, "gestionnaires_main.s"); t = open(f).read()
    a = t.index("psp_1b07bc:"); b = t.index("\npsp_", a + 10)
    t = t[:a] + open(os.path.join(RACINE, "max_trad", "mes_fichiers", "psp_1b07bc_main.s")).read().rstrip("\n") + t[b:]
    open(f, "w").write(t)
    # CORRECTIFS LOCAUX des sources MAX (signalés à la session MAX) : (fichier, avant, après)
    # fils (projectiles...) : la création recopie $18 du parent mais PAS l'emplacement de banque $1A -> le fils dessinait
    # ses frames dans l'emplacement 0 (banque commune) : projectile d'Ingrid invisible / en charpie (relevé au banc)
    for f in sorted(os.listdir(src)):
        if f.startswith("brouillon_") and f.endswith(".s"):
            t = open(os.path.join(src, f)).read()
            t2 = t.replace("        move.w    $18(a6), $18(a4)\n",
                           "        move.w    $18(a6), $18(a4)\n        move.w    $1a(a6), $1a(a4)   ; (agent_integration_max) banque du fils = celle du parent\n")
            # (17/10) idem pour les objets créés par l'allocateur d'EFFETS ($1C368 : étoiles d'Ingrid $35…) : $1A restait 0
            # (banque commune) alors que leurs frames sont dans la banque du perso -> invisibles
            t2 = t2.replace("        bsr     psp_raz_alloc       ; champs remis à zéro par l'allocateur PSP 0x1EFE4\n",
                            "        bsr     psp_raz_alloc       ; champs remis à zéro par l'allocateur PSP 0x1EFE4\n"
                            "        move.w  $1a(a6), $1a(a4)    ; (agent_integration_max) banque de l'objet créé = celle du créateur\n")
            if t2 != t: open(os.path.join(src, f), "w").write(t2)
    # PROVISOIRE (palier 3, en attente de la session MAX) : acteurs de fin, « move.b #n,$9(a4) » avec n impair (1, 3) ->
    # Upper/arcade lit $9 comme index de table de saut ($19EDC) : erreur d'adresse (fin d'Eagle, image 45065). Valeur
    # PSP probablement un rang (arcade = 2 × rang, cf. « champ ×2 ») : n -> 2n
    f = os.path.join(src, "acteurs_fins_max.s"); t = open(f).read()
    import re as _re0
    t2, k_ = _re0.subn(r"(        move\.b    #\$)([13])(, \$9\(a4\))", lambda m: m.group(1) + str(2 * int(m.group(2))) + m.group(3) + "   ; (agent_integration_max) PROVISOIRE : $9 pair (×2)", t)
    assert k_ == 3, "acteurs_fins_max.s : %d « move.b #impair,$9(a4) » (3 attendus)" % k_
    open(f, "w").write(t2)
    # (2b23) COUP_NORMAL (« pas de contre », PS2 0x2262C0) : valeur de l'image v149 ($23A3C) figée dans
    # symboles_externes_max.s, PÉRIMÉE depuis le rebase v151 (en v151, $23A3C = tirage $3A(A6) : le coup n'était pas
    # appliqué -> Ingrid / Eagle restaient en pose de contre sous un coup non contré). Relevée ici dans l'image native
    # d'Upper (banc_ref) : dispatcher des contres « MOVE.B $C(A0),D0 ; BGT.S ; BSR.S coup_normal » (image $3FA4)
    fcn = os.path.join(src, "symboles_externes_max.s"); tcn = open(fcn).read()
    imr = bytearray(open(os.path.join(RACINE, "banc_ref", "roms_ro5", "sfa3ud", "sz3ud.03c"), "rb").read())
    imr[0::2], imr[1::2] = imr[1::2], imr[0::2]
    k_cn = imr.find(bytes.fromhex("1028000c6e046112600e0c0000046506"))
    assert k_cn > 0 and imr.find(bytes.fromhex("1028000c6e046112600e0c0000046506"), k_cn + 2) < 0, "COUP_NORMAL : motif du dispatcher"
    cn_ = k_cn + 6 + 2 + 0x12
    assert imr[cn_:cn_ + 2] == bytes.fromhex("6100"), "COUP_NORMAL : $%x inattendu" % cn_
    tcn, kcn = _re0.subn(r"^COUP_NORMAL equ \$[0-9A-Fa-f]+", "COUP_NORMAL equ $%06X" % cn_, tcn, flags=_re0.M)
    assert kcn == 1; open(fcn, "w").write(tcn)
    print("COUP_NORMAL = $%X (dispatcher des contres en $%X, image native)" % (cn_, k_cn))
    # CONTRE_DECLENCHE (mot A5 « contre déclenché », -$7454 = $8BAC) : vérifié dans la même image -- l'appelant du
    # dispatcher le teste (« TST.W $8BAC(A5) ; BNE », image $3F3E = $3FA4 - $66) avant d'appliquer les dégâts
    m_cd = _re0.search(r"^CONTRE_DECLENCHE equ -\$([0-9A-Fa-f]+)", tcn, flags=_re0.M)
    assert m_cd, "CONTRE_DECLENCHE absent de symboles_externes_max.s"
    cd_ = (0x10000 - int(m_cd.group(1), 16)) & 0xFFFF
    assert imr[k_cn - 0x66:k_cn - 0x62] == bytes([0x4A, 0x6D, cd_ >> 8, cd_ & 0xFF]), \
        "CONTRE_DECLENCHE : $%04X(A5) n'est plus le drapeau testé en $%X (image native)" % (cd_, k_cn - 0x66)
    print("CONTRE_DECLENCHE = $%04X(A5) vérifié (TST.W en $%X, image native)" % (cd_, k_cn - 0x66))
    # (2b23) PROVISOIRE (à signaler à la session MAX) : $248 (PSP, -> $249 image) = niveau de super, BRUT sur PSP mais ×2
    # dans l'arcade / Upper ($316D6 : $83 = 4 et $249 = 4 ; $316C6 = arcade $2F53C : MOVE.W $AB210(A0,D0.W) avec D0 = $249).
    # La traduction le laisse brut (absent des champs « ×2 », alors que $82 y est) : super d'Ingrid 2xQCF+MP (niveau 1)
    # -> $249 = 1 -> erreur d'adresse en $316F2 (exception pc=$A08, banc PSP mode B max17 / essais/b29). Écritures ×2,
    # lectures ÷2 (le code MAX calcule en brut : 2 × $248 = décalage de mot), copie $82 -> $248 inchangée (×2 des deux côtés)
    # (R12, 25/10) fait à la source par la session MAX (traduire.py 7374f60, brouillons régénérés) -> 0 par défaut
    if os.environ.get("MAX_CHAMP_248", "0") == "1":
        n248 = 0
        for f in sorted(os.listdir(src)):
            if not f.endswith(".s"): continue
            t = open(os.path.join(src, f)).read()
            t2, a_ = _re0.subn(r"^(\s+move\.b\s+#\$)([0-9a-fA-F]+)(, \$248\(a6\))", lambda m: "%s%X%s   ; (agent_integration_max) $248 ×2" % (m.group(1), 2 * int(m.group(2), 16), m.group(3)), t, flags=_re0.M)
            t2, b_ = _re0.subn(r"^(\s+move\.b\s+\$248\(a6\), (d\d))\s*$", r"\1\n        lsr.b   #1, \2          ; (agent_integration_max) $248 ×2 -> brut", t2, flags=_re0.M)
            t2, c_ = _re0.subn(r"^(\s+move\.b\s+(d\d), \$248\(a6\))\s*$", r"\1\n        add.b   \2, $248(a6)    ; (agent_integration_max) brut -> $248 ×2 (registre intact)", t2, flags=_re0.M)
            if t2 != t: open(os.path.join(src, f), "w").write(t2); n248 += a_ + b_ + c_
        print("champ $248 (niveau de super) : %d accès MAX passés en ×2" % n248)
        assert n248 == 13, "champ $248 : %d accès corrigés (13 attendus)" % n248
    # (course de Maki : correctif provisoire $3A -> $3B retiré le 17/10 : traducteur MAX corrigé, lectures en mot)
    # (2b22) test « parent dans son coup » cmpi.l -> cmpi.b : corrigé à la source (traduire.py 17b3221, R3) -> retiré
    # (2b22) fiches d'attaque des PROJECTILES MAX (dc.b = octets +$08..+$1F) : type de recul +9 28-32 -> 40-44 (RECUL_MAX)
    f_ = os.path.join(src, "donnees_projectiles_max.s"); t_ = open(f_).read(); k_ = [0]
    def _rec(m):
        b_ = [x.strip() for x in m.group(2).split(",")]
        if len(b_) == 24 and 28 <= int(b_[1].lstrip("$"), 16) <= 32:
            b_[1] = "$%02x" % RECUL_MAX[int(b_[1].lstrip("$"), 16)]; k_[0] += 1
        return m.group(1) + ", ".join(b_)
    t_ = re.sub(r"^(\s+dc\.b\s+)([^\n;]+)", _rec, t_, flags=re.M)
    open(f_, "w").write(t_); print("projectiles : %d fiche(s) de recul 28-32 -> 40-44" % k_[0])
    for fc, av, ap in CORRECTIFS:
        # (2b18) MAX_GARDE_INGRID=0 : garde de la liste d'Ingrid retirée (contrôle du correctif psp_raz_alpha de la session MAX)
        if fc == "brouillon_ingrid.s" and "L_1c6d78" in av and os.environ.get("MAX_GARDE_INGRID", "1") == "0": continue
        f = os.path.join(src, fc); t = open(f).read()
        assert t.count(av) == 1, "correctif introuvable dans %s : %r" % (fc, av)
        open(f, "w").write(t.replace(av, ap))
    # octet $0D des pas d'animation (arcade : type de réaction quand le perso est touché) : Upper n'accepte que 0-9 et
    # $FF (aiguillage EN LIGNE de 6 entrées pour 4-9, image $40D4) ; Eagle a des pas à $0B/$0C, Ingrid à $0D/$0E
    # (valeurs PSP propres) -> saut hors table, exception (Arcade Eagle, image 73305). Ramenés à 0 (réaction normale)
    # en attendant leur sens (question à la session MAX).
    import re as _re
    for pf in ("anims_eagle.s", "anims_maki.s", "anims_yun.s", "anims_ingrid.s"):
        f = os.path.join(src, pf); t = open(f).read(); n = [0]
        def _pas(m):
            b = [x.strip() for x in m.group(3).split(",")]
            if len(b) == 12 and int(b[5].lstrip("$"), 16) in (0x0B, 0x0C, 0x0D, 0x0E) and os.environ.get("MAX_CONTRES") != "1":
                b[5] = "$00"; n[0] += 1
            return m.group(1) + m.group(2) + ", ".join(b) + m.group(4)
        t = _re.sub(r"(^P\w\w_\w+:\s*\n\s*dc\.b[^\n]+\n\s*dc\.l[^\n]+\n)(\s*dc\.b\s+)([^\n;]+)(.*)$", _pas, t, flags=_re.M)
        open(f, "w").write(t)
        if n[0]: print("%s : %d pas à octet $0D hors 0-9 ramenés à 0" % (pf, n[0]))
    # sons par pas (sons_pas_max.s) : chaque table complétée à 256 index muets (un octet son hors table ne doit plus lire
    # la table suivante ni des commandes de musique)
    f = os.path.join(src, "sons_pas_max.s")
    if os.path.exists(f):
        t = open(f).read(); out = []; n = None
        for l in t.split("\n"):
            m = re.match(r"^SONS_PAS_(\w\w):.*?(\d+) index", l)
            if (m or l.startswith("SONS_COMMUNS") ) and n is not None:
                out.append("        dcb.w   4*%d, 0          ; (agent_integration_max) bourrage à 256 index" % (256 - n)); n = None
            if m: n = int(m.group(2))
            out.append(l)
        if n is not None: out.append("        dcb.w   4*%d, 0          ; (agent_integration_max) bourrage à 256 index" % (256 - n))
        open(f, "w").write("\n".join(out) + "\n")
    d = BLOC_EAGLE - 0xD40000
    for f in ("frames_eagle.s", "anims_eagle.s", "fin_anims_eagle.s", "decor_fin_eagle.s"):
        t = open(os.path.join(src, f)).read()
        t2 = re.sub(r"(\borg\s+\$)(D[4-7][0-9A-Fa-f]{4})", lambda m: m.group(1) + "%X" % (int(m.group(2), 16) + d), t, count=1, flags=re.I)
        assert t2 != t, f
        open(os.path.join(src, f), "w").write(t2)
    # intros CROISÉES du PSP (rappel 19) : le perso MAX attend des étapes de l'intro de certains adversaires (Eagle :
    # Sagat, Zangief ; Maki : $0E ; Yun : $21 ; Ingrid : $19) qu'Upper ne joue pas -> blocage avant le combat (vu au banc).
    # Intro ordinaire pour tous : saut direct au cas général (cible du dernier « bne » des tests d'ID adverse).
    for pid, P in PERSOS.items():
        if pid.startswith("_"): continue
        lab = P["rappels"]["7491f8"]
        for f in sorted(os.listdir(src)):
            if not f.startswith("brouillon_") or not f.endswith(".s"): continue
            t = open(os.path.join(src, f)).read()
            m = re.search(r"^%s:[^\n]*\n" % lab, t, re.M)
            if not m: continue
            corps = t[m.end():m.end() + 2000]
            if corps.lstrip().startswith("bra "): break                  # déjà fait (gestionnaires d'Eagle)
            cibles = re.findall(r"cmpi\.b\s+#\$[0-9a-f]+, \$102\(a1\)\s*\n\s+bne\s+(L_[0-9a-f]+)", corps)
            assert cibles, "intro de %s : forme inattendue" % P["nom"]
            t = t[:m.end()] + "        bra     %s           ; (agent_integration_max) intros croisées retirées\n" % cibles[-1] + t[m.end():]
            open(os.path.join(src, f), "w").write(t)
            print("intro de %s (%s, %s) : intros croisées retirées (-> %s)" % (P["nom"], lab, f, cibles[-1]))
            break
    for f in ("symboles_frames_max.s", "symboles_anims_max.s"):
        t = open(os.path.join(src, f)).read()
        t = re.sub(r"^(\w+\s+equ\s+\$)([0-9A-Fa-f]+)", lambda m: m.group(1) + ("%X" % (int(m.group(2), 16) + d)
                   if 0xD40000 <= int(m.group(2), 16) < 0xD80000 else m.group(2)), t, flags=re.M)
        open(os.path.join(src, f), "w").write(t)
    return src

def renumerote(d):
    """(appliqué aux sources CONVERTIES : les clés « fichier:ligne » de bases_forcees.tsv visent les sources d'origine)"""
    # NUMÉROTATION D'UPPER : Yun et Ingrid en $2D / $2E (au-delà des pseudo-ID $28-$2C d'Upper ; la session MAX les
    # numérote $28 / $29). Le code MAX indexe ses tables par « ID - $26 » (0-3) : on y insère le passage $2D/$2E -> 2/3.
    n_remap = 0
    for f in ("moteur_max_main.s", "acteurs_fins_main.s"):
        t = open(os.path.join(d, f)).read()
        def rb(m):
            nonlocal_k[0] += 1
            r, ind, lab = m.group(2), m.group(1), "maxid%d" % nonlocal_k[0]
            sp = "        "
            return ("%ssubi.b  #$26, %s\n%scmpi.b  #1, %s            ; (agent_integration_max) $26/$27 -> 0/1\n"
                    "%sbls.s   .%s\n%ssubq.b  #5, %s            ; $2D/$2E -> 2/3 (Yun, Ingrid)\n.%s:\n%scmpi.b  #3, %s"
                    % (ind, r, sp, r, sp, lab, sp, r, lab, sp, r))
        nonlocal_k = [n_remap]
        t, k1 = re.subn(r"^(\s*|\.\w+:\s*)subi\.b\s+#\$26, (d\d)\s*\n\s*cmpi\.b\s+#3, \2", rb, t, flags=re.M)
        def rw(m):
            nonlocal_k[0] += 1; lab = "maxidw%d" % nonlocal_k[0]
            return ("        subi.w  #$26, d1\n        bcs.s   .rien\n        cmpi.w  #1, d1            ; (agent_integration_max) $26/$27 -> 0/1\n"
                    "        bls.s   .%s\n        subq.w  #5, d1            ; $2D/$2E -> 2/3\n.%s:\n        cmpi.w  #3, d1" % (lab, lab))
        t, k2 = re.subn(r"^\s*subi\.w\s+#\$26, d1\s*\n\s*bcs\.s\s+\.rien\s*\n\s*cmpi\.w\s+#3, d1", rw, t, flags=re.M)
        n_remap = nonlocal_k[0]
        if f == "acteurs_fins_main.s":
            t, k3 = re.subn(r"(FIN118X:(?:.|\n)*?)dc\.b    \$28, 0", r"\1dc.b    $2D, 0          ; (agent_integration_max) Yun = $2D", t)
            t, k4 = re.subn(r"(FIN118X:(?:.|\n)*?)dc\.b    \$29, 0", r"\1dc.b    $2E, 0          ; (agent_integration_max) Ingrid = $2E", t)
            print("FIN118X : %d entrée(s) Yun renumérotée(s), %d Ingrid" % (k3, k4))
        open(os.path.join(d, f), "w").write(t)
        print("%s : %d index « ID - $26 » octet, %d mot, passés à $2D/$2E" % (f, k1, k2))
    f = "acteurs_fins_max.s"; t = open(os.path.join(d, f)).read()
    t, k = re.subn(r"cmpi\.b\s+#\$29, \(\$ff8[59]02\)\.l", lambda m: m.group(0).replace("#$29", "#$2E"), t)
    open(os.path.join(d, f), "w").write(t); print("%s : %d test(s) « perso = Ingrid » $29 -> $2E" % (f, k))

RECUL_MAX = {28: 40, 29: 41, 30: 42, 31: 43, 32: 44}   # (2b22) types de recul MAX (fiche +9) -> rangs libres de la table
def recul_types():
    """(2b22) table des types de recul (T_61B460 d'Upper) prolongée SANS toucher ce que lisent les natifs. Lecteur (image
    $52DC8) : octet PS2 2·type + D6 (LEA 0(A0,D0.W) puis EORI #1 : pas de +1), D6 = 0 à 2 -> un natif de type t lit les
    octets 2t à 2t+2, jusqu'à 56 pour le type 27 (la table de la session MAX y mettait $19 : régression Blanka / Sodom du
    banc max20). Octets 0-63 = Upper ; les types MAX 28-32 sont REMAPPÉS sur 40-44 dans les fiches (RECUL_MAX) et posés aux
    octets 2t, 2t+1, 2t+2 (séquences 25-29)."""
    b = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read()
    o = 0x61B460 - 0x1F0000
    ps2 = bytearray(b[o:o + 64]) + bytearray(96 - 64)
    for typ, sq in zip(range(28, 33), range(25, 30)):
        r = RECUL_MAX[typ]
        for k in range(3): ps2[2 * r + k] = sq
    im = bytes(ps2[k ^ 1] for k in range(len(ps2)))
    return ["        even", "MAX_RECUL_TYPES:            ; (agent_integration_max) octets PS2 0-63 = T_61B460 d'Upper ; types MAX 40-44",
            ] + ["        dc.b    " + ", ".join("$%02x" % x for x in im[k:k + 16]) for k in range(0, len(im), 16)]

def anim_reactions():
    """(2b22, R5) table d'animation des réactions (Upper 0x61B4A0, 34 octets, lue en octet PS2 r par $4FD12 / $50292) :
    réactions PSP 34 -> 36, 35 -> 23, 36 -> 36 ajoutées ; natives 0-33 = Upper"""
    b = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read()
    o = 0x61B4A0 - 0x1F0000
    ps2 = bytearray(b[o:o + 34]) + bytes([36, 23, 36, 0])
    im = bytes(ps2[k ^ 1] for k in range(len(ps2)))
    return ["        even", "MAX_ANIM_REACTIONS:         ; (agent_integration_max) octets PS2 0-33 = Upper 0x61B4A0 ; 34-36 = PSP",
            "        dc.b    " + ", ".join("$%02x" % x for x in im)]

def flammes_natives():
    """(2b19) FLAMMES_N_<ptr> : 16 couples natifs (pointeur de 0x74C358[ID], IDs 0-$25) recopiés DEUX fois, ordre image"""
    import struct as st
    b = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read()
    L = []; vus = set()
    for i in range(0x26):
        p = st.unpack_from("<I", b, 0x74C358 - 0x1F0000 + 4 * i)[0]
        if p in vus: continue
        vus.add(p); d = b[p - 0x1F0000:p - 0x1F0000 + 32]
        im = bytes(d[k ^ 1] for k in range(32)) * 2
        L += ["        even", "FLAMMES_N_%06X:" % p] + ["        dc.b    " + ", ".join("$%02x" % x for x in im[k:k + 16]) for k in range(0, 64, 16)]
    return L

def decor_base():
    """(palier 4) N = entrées de la table de banque du fichier de fin du MODÈLE (gfx de T_FIN 0x6283C0, banques_hx d'Upper)
    par perso -> base des codes des frames FD (fichier d'emplacement 4 = table du modèle puis tuiles des FD)"""
    import struct as st
    sys.path.insert(0, os.path.join(RACINE, "untranspile"))
    import integre_max as IM_
    b = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read()
    noms = {"26": "eagle", "27": "maki", "2d": "yun", "2e": "ingrid"}; r = {}
    for p, m in IM_.FIN_MODELE.items():
        g = st.unpack_from("<h", b, 0x6283C0 - 0x1F0000 + 4 * m)[0]
        f = "<workspace>/work/mame_ro5/banques_hx/f%d.bin" % g
        r[noms[p]] = os.path.getsize(f) // 4 if g and os.path.exists(f) else 0
    return r

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=os.path.join(RACINE, "banc_ref"))
    ap.add_argument("--sortie", default=os.path.join(RACINE, "prep"))
    a = ap.parse_args()
    out = a.sortie; os.makedirs(os.path.join(out, "conv"), exist_ok=True); os.makedirs(os.path.join(out, "blocs"), exist_ok=True)
    carte = os.path.join(a.ref, "carte_image.txt"); roms = os.path.join(a.ref, "roms_ro5", "sfa3ud")
    src = sources(out)
    # 1. conversion du code
    r = subprocess.run([sys.executable, os.path.join(RACINE, "conv", "convertit_max.py"), "--carte", carte, "--roms", roms,
                        "--sortie", os.path.join(out, "conv"), "--sources", src], capture_output=True, text=True)
    open(os.path.join(out, "conversion.txt"), "w").write(r.stdout + r.stderr)
    if r.returncode: sys.exit("convertit_max.py : échec (%s/conversion.txt)" % out)
    renumerote(os.path.join(out, "conv"))
    st = json.load(open(os.path.join(out, "conv", "stats.json")))
    print("conversion : %s réécrites, %s NON RÉSOLUES, %s/%s adresses du moteur" % (st.get("réécrit"), st.get("NON RÉSOLU"),
          st.get("adresses_resolues"), st.get("adresses_resolues", 0) + st.get("adresses_non_resolues", 0)))
    # 2. blocs externes (frames, animations de combat et de fin)
    env = dict(os.environ, CONV_SORTIE=os.path.join(out, "blocs"), BLOC_EAGLE="%X" % BLOC_EAGLE)
    env["DECOR_BASE"] = ",".join("%s:%d" % kv for kv in decor_base().items())
    r = subprocess.run([sys.executable, os.path.join(RACINE, "conv", "convertit_frames.py"), src], capture_output=True, text=True, env=env)
    open(os.path.join(out, "blocs.txt"), "w").write(r.stdout + r.stderr)
    if r.returncode: sys.exit("convertit_frames.py : échec (%s/blocs.txt)" % out)
    blocs = sorted(f[4:10] for f in os.listdir(os.path.join(out, "blocs")) if re.fullmatch(r"ext_[0-9a-f]{6}\.bin", f))
    print("blocs externes :", ", ".join(blocs))
    # 3. assemblage : CODE à CODE_ORG (dans l'image), DONNÉES à MAX_ORG
    sys.path.insert(0, os.path.join(RACINE, "conv"))
    import convertit_max as CM
    code_f = ["adresses_upper.s"] + CM.FICHIERS_CODE
    donn_f = [f for f in CM.ORDRE_ASSEMBLAGE if f not in code_f]
    ic, idn = integration()
    import hud_apercu_max as HA            # HUD (noms, visages) et aperçu de sélection : tuiles + données
    act = [(pid, P["pl"]) for pid, P in PERSOS.items() if not pid.startswith("_") and P.get("actif")]
    idn = idn.replace("MAX_FIN:", "\n".join(HA.prepare(out, act, os.path.join(RACINE, "conv"))) + "\nMAX_FIN:")
    import fins_integration as FM          # palier 3 : scripts, acteurs et textes des fins MAX
    actf = [(pid, P["pl"], P["suffixe"]) for pid, P in PERSOS.items() if not pid.startswith("_") and P.get("actif")]
    idn = idn.replace("MAX_FIN:", "\n".join(FM.prepare(out, actf)) + "\nMAX_FIN:")
    lit = lambda f: open(os.path.join(out, "conv", f)).read()
    tout = ["        org     $%X" % CODE_ORG]
    for f in ("symboles_frames_max.s", "symboles_anims_max.s", "symboles_externes_max.s"):
        tout += ["; ==== %s" % f, open(os.path.join(src, f)).read()]
    for f in code_f: tout += ["; ==== %s" % f, lit(f)]
    tout += [ic, "MAX_CODE_FIN:", "        org     $%X" % MAX_ORG]
    for f in donn_f: tout += ["; ==== %s" % f, lit(f)]
    tout += [idn]
    open(os.path.join(out, "tout.s"), "w").write("\n".join(tout))
    bin_, lst = os.path.join(out, "tout.bin"), os.path.join(out, "tout.lst")
    r = subprocess.run([VASM, "-m68000", "-spaces", "-Fbin", "-quiet", "-maxerrors=500", "-L", lst,
                        "-o", bin_, os.path.join(out, "tout.s")], capture_output=True, text=True)
    open(os.path.join(out, "asm.log"), "w").write(r.stdout + r.stderr)
    err = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("error")]
    if r.returncode or err: sys.exit("vasm : %d erreurs (%s/asm.log)" % (len(err), out))
    S = symboles_listing(lst)
    for f in ("symboles_frames_max.s", "symboles_anims_max.s", "symboles_externes_max.s"):   # equ non référencés : absents de la liste
        for m in re.finditer(r"^(\w+)\s+equ\s+\$([0-9A-Fa-f]+)", open(os.path.join(src, f)).read(), re.M):
            S.setdefault(m.group(1), int(m.group(2), 16))
    B = open(bin_, "rb").read()
    fin_code = S["MAX_CODE_FIN"]; assert fin_code <= 0x3C0000, "code MAX trop grand : fin $%X > $3C0000" % fin_code
    code = B[:fin_code - CODE_ORG]; donnees = B[MAX_ORG - CODE_ORG:]
    open(os.path.join(out, "code_%06x.bin" % CODE_ORG), "wb").write(code)
    open(os.path.join(out, "blocs", "ext_%06x.bin" % MAX_ORG), "wb").write(donnees)
    assert MAX_ORG + len(donnees) <= 0xC00000, "les données MAX débordent sur le bloc des animations natives ($C00000)"
    print("vasm : 0 erreur ; code %d octets en $%X-$%X (réserve $%X), données %d octets en $%X ; %d symboles" % (
          len(code), CODE_ORG, fin_code, CODE_RESERVE, len(donnees), MAX_ORG, len(S)))
    json.dump({"org": MAX_ORG, "taille": len(donnees), "code_org": CODE_ORG, "code_taille": len(code), "reserve": CODE_RESERVE,
               "blocs": sorted(set(blocs) | {"%06x" % MAX_ORG}), "symboles": S,
               "carte_md5": hashlib.md5("".join(" ".join(l.split()[:2]) + "\n" for l in open(carte)).encode()).hexdigest(), "ref": os.path.abspath(a.ref)},
              open(os.path.join(out, "symboles.json"), "w"), indent=0)
    print("préparation MAX : %s" % out)

if __name__ == "__main__":
    main()
