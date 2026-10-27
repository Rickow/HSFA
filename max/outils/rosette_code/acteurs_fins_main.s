; routines ÉCRITES À LA MAIN pour les acteurs de fin MAX (2026-10-10) — appelées par acteurs_fins_max.s (traduire.py,
; contexte acteur : table_fin) ; données +$12C : donnees_fins_t12c.s (acteurs_fins.py). N° de fin = $1C6(A5).

; ---- fin_t12c : A0 = enregistrements de 32 o de la petite table d'acteurs [4] de la fin courante (PSP état +$12C ;
; Maki 1, Yun 8 ; Eagle / Ingrid : aucun -> table nulle). Seul A0 change.
fin_t12c:
        move.l  d0, -(sp)
        moveq   #0, d0
        move.b  $1c6(a5), d0
        subi.b  #$26, d0
        cmpi.b  #3, d0
        bls.s   .ok
        moveq   #0, d0
.ok:    add.w   d0, d0
        add.w   d0, d0
        lea     FIN_T12C(pc), a0
        movea.l 0(a0, d0.w), a0
        move.l  (sp)+, d0
        rts
FIN_T12C:
        dc.l    FIN_T12C_VIDE, FIN_T12C_27, FIN_T12C_28, FIN_T12C_VIDE

; ---- fin_pas110 : D7 = n -> D7 = pointeur du 1er pas de l'animation n de la fin courante (PSP état +$110[n] ;
; 68K : FIN_ANIM_xx, mots relatifs, anims_fins_max.py). Hors fin MAX : D7 = 0. Seul D7 change.
fin_pas110:
        movem.l d0/a0, -(sp)
        moveq   #0, d0
        move.b  $1c6(a5), d0
        subi.b  #$26, d0
        cmpi.b  #3, d0
        bhi.s   .rien
        add.w   d0, d0
        add.w   d0, d0
        lea     FIN_ANIMS(pc), a0
        movea.l 0(a0, d0.w), a0
        add.w   d7, d7
        adda.w  0(a0, d7.w), a0
        move.l  a0, d7
        movem.l (sp)+, d0/a0
        rts
.rien:  moveq   #0, d7
        movem.l (sp)+, d0/a0
        rts
FIN_ANIMS:
        dc.l    FIN_ANIM_26, FIN_ANIM_27, FIN_ANIM_28, FIN_ANIM_29

; ---- fin_pas118 : D7 = n -> D7 = pointeur du 1er pas (8 o) de l'image / animation de décor n de la fin courante
; (PSP état +$118[n] : pas8 0x20002 indexés par 0x20004 ; 68K : FIN118_xx, decor_fins_max.py, frames FD%02X_n à codes
; locaux de la banque gfx de fin). Hors fin MAX : D7 = 0 (la pose du pas, psp_1d96c, ignore un pointeur nul).
fin_pas118:
        movem.l d0/a0, -(sp)
        moveq   #0, d0
        move.b  $1c6(a5), d0
        lea     FIN118X(pc), a0         ; d'abord les images remplacées par des pas ARCADE (symboles relogés)
.ext:   cmpi.w  #-1, (a0)
        beq.s   .table
        cmp.b   (a0), d0
        bne.s   .suiv
        cmp.w   2(a0), d7
        bne.s   .suiv
        move.w  8(a0), $1a(a6)          ; banque des codes de tuiles des frames visées (arcade : $6000 décors globaux)
        move.l  4(a0), d7
        movem.l (sp)+, d0/a0
        rts
.suiv:  lea     10(a0), a0
        bra.s   .ext
.table: subi.b  #$26, d0
        cmpi.b  #3, d0
        bhi.s   .rien
        add.w   d0, d0
        add.w   d0, d0
        lea     FIN118S(pc), a0
        movea.l 0(a0, d0.w), a0
        move.w  #BANQUE_1A_DECOR_FIN, $1a(a6)   ; frames FD.. : banque gfx de fin (emplacement 4 = $8000)
; ⚠ un acteur qui repasse ensuite aux frames du perso (FIN_ANIM_xx) doit rétablir $1A (la partie commune $4B ne le pose
; qu'à l'état 0, selon le propriétaire T_61c0e0[$7F])
        add.w   d7, d7
        adda.w  0(a0, d7.w), a0
        move.l  a0, d7
        movem.l (sp)+, d0/a0
        rts
.rien:  moveq   #0, d7
        movem.l (sp)+, d0/a0
        rts
FIN118S:
        dc.l    FIN118_26, FIN118_27, FIN118_28, FIN118_29
; images de +$118 dont les frames ne sont pas dans le pac de la fin (efct.pac commun) -> pas arcade équivalents :
; dc.b fin, 0 ; dc.w n° PSP ; dc.l 1er pas (symbole défini à l'intégration, symboles_externes_max.s) ; dc.w valeur de $1A
FIN118X:
        dc.b    $27, 0
        dc.w    119
        dc.l    EXPLO_PAS               ; explosion (frames efct 300-305) = $2E50A0 n° 5 (HSFA : identique au pixel près)
        dc.w    EXPLO_1A                ; banque commune (arcade $6000 -> Upper emplacement 0 = $0000) ; palette $16 ($C = 0)
        dc.b    $28, 0
        dc.w    119
        dc.l    EXPLO_PAS
        dc.w    EXPLO_1A
        dc.w    -1

; ---- psp_1d75c4 (sous-type MAX) : PSP = libère l'effet de décor courant (0xA4CED0/0xA4CED4), crée un effet de type 26
; dans le réservoir des effets de décor (0x1F338, neutralisé comme pour Ingrid : moteur_max_main.s), lève 0x39CA3E,
; puis état 4. Effets de décor sans équivalent arcade : on ne garde que le changement d'état.
psp_1d75c4:
        move.b  #$4, $4(a6)
        rts

; ---- fin_pos_4f05 : D7 = index PSP (0, 2, … 10 : paires de mots du tableau global 0x2B3EC écrit par l'acteur $4F/05,
; PSP 0x1D5CB0) -> D7 = position (mot) recomposée (haut << 4 | bas). Arcade : $4F/05 ($AAFAC) garde ces 12 mots dans
; SON objet, $40-$57 (octet << 4, même ordre) -> on cherche l'objet $4F/05 actif dans le réservoir des acteurs
; ($3000(A5), 32 objets de $80 o ; +0 actif, +2 classe, +3 sous-type). Absent : position courante -$50F8(A5).
fin_pos_4f05:
        movem.l d0/a0, -(sp)
        lea     $3000(a5), a0
        moveq   #31, d0
.cherche:
        tst.b   (a0)
        beq.s   .suivant
        cmpi.w  #$4f05, 2(a0)
        beq.s   .trouve
.suivant:
        lea     $80(a0), a0
        dbra    d0, .cherche
        move.w  -$50f8(a5), d7
        bra.s   .fin
.trouve:
        add.w   d7, d7
        move.w  $40(a0, d7.w), d0
        lsl.w   #4, d0
        move.w  $42(a0, d7.w), d7
        lsr.w   #4, d7
        or.w    d0, d7
.fin:   movem.l (sp)+, d0/a0
        rts
