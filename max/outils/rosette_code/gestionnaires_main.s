; Gestionnaires et fonctions moteur des persos MAX ÉCRITS À LA MAIN par l'agent d'intégration HSFA (agent_integration_max,
; 2026-10-11), repris ici en DISPOSITION ARCADE pour que brouillons.py ne les retraduise pas (lus comme moteur_max_main.s).
; psp_1b07bc : boucle remise en disposition arcade (mot de durée en 0 : drapeaux $80/$40 = octet 0, compte = octet 1 ;
; octet d'attaque du jeu de boîtes = octet 9). La version de l'agent lisait ces octets dans l'ordre inverse.
psp_1b07bc:                          ; PSP 0x1B07BC(objet, n) : 1 si le pas de l'ADVERSAIRE actif dans n images porte une attaque
        movem.l d1-d2/a0-a1, -(sp)
        movea.w $38(a6), a1
        movea.l $1c(a1), a0
        tst.b   9(a0)
        bne.s   .oui
        move.b  d0, d2
        ext.w   d2
        moveq   #0, d1
        move.b  $32(a1), d1
        sub.w   d1, d2
.boucle:
        move.b  0(a0), d1            ; drapeaux (fin / reprise)
        andi.b  #$c0, d1
        bne.s   .test
        tst.w   d2
        ble.s   .test
        lea     20(a0), a0
        moveq   #0, d1
        move.b  1(a0), d1            ; durée
        sub.w   d1, d2
        bra.s   .boucle
.test:  tst.b   9(a0)
        bne.s   .oui
        moveq   #0, d0
        bra.s   .fin
.oui:   moveq   #1, d0
.fin:   movem.l (sp)+, d1-d2/a0-a1
        rts
psp_1b33c8:                          ; (agent_integration_max) écrite à la main, disposition ARCADE (convertie ensuite)
; PSP 0x1B33C8 relu dans le MIPS : traduite de travers par traduire.py, qui prend 0x1B3450 (créneau de délai d'un JAL,
; pointé par hasard par un mot de données 0x2C8ED0) pour un début de fonction. Compteur PSP 0x4D = $35 (octet signé).
        cmpi.b  #1, $35(a6)
        bne.s   .l414
        addq.b  #4, $7(a6)           ; PSP 0x7 += 2 (états ×2)
        move.l  #-1, $3d0(a6)        ; PSP 0x344
        moveq   #102, d0
        jsr     $2e7f2.l             ; PSP 0x67144(objet, 102)
        bra     .l508
.l414:  bsr     psp_cfec8
        move.b  $35(a6), d1
        btst    #4, d1
        beq     .l508
        cmpi.b  #18, d1
        bge.s   .l47c
        cmpi.b  #16, d1
        blt     .l504
        cmpi.b  #17, d1
        bge.s   .l498
        moveq   #50, d0              ; 16 : son par clé 50, effet (-32, 0) sous-type $B
        bsr     psp_cee5c
        moveq   #-32, d0
        moveq   #0, d1
        bsr     psp_cf934
        clr.b   $35(a6)
        bra     .l508
.l47c:  cmpi.b  #19, d1
        blt.s   .l4b4                ; 18
        cmpi.b  #20, d1
        blt.s   .l4f8                ; 19
        clr.b   $35(a6)
        bra.s   .l508
.l498:  moveq   #21, d0              ; 17 : voix 21 puis 30
        bsr     psp_cee0c
        moveq   #30, d0
        bsr     psp_cee0c
        clr.b   $35(a6)
        bra.s   .l508
.l4b4:  moveq   #6, d0               ; 18
        bsr     psp_cee5c
        moveq   #-32, d0
        moveq   #16, d1
        bsr     psp_cf8cc
        moveq   #82, d0
        jsr     $2e970.l             ; PSP 0x6768C(objet, 82)
        moveq   #-32, d0
        moveq   #0, d1
        bsr     psp_cf970
        clr.b   $35(a6)
        bra.s   .l508
.l4f8:  moveq   #-16, d0             ; 19
        moveq   #64, d1
        bsr     psp_cf8cc
.l504:  clr.b   $35(a6)
.l508:  tst.b   $31(a6)
        beq.s   .fin
        jsr     $2aa08.l             ; PSP 0x5E004 : au sol ?
        tst.w   d0
        beq.s   .fin
        clr.b   $31(a6)
        move.w  $64(a6), d3          ; PSP 0x84
        swap    d3
        clr.w   d3
        move.l  d3, $14(a6)          ; Y = sol (16.16)
.fin:   rts

; (agent_integration_max) fonctions moteur PSP appelées par les gestionnaires d'Eagle et absentes de moteur_max_*.s
; (disposition ARCADE, converties par convertit_max.py comme les autres sources)
psp_cee54:                           ; PSP : jr ra (vide)
psp_cfc88:                           ; PSP : jr ra (vide)
        rts
psp_cef74:                           ; PSP : 0x63708(objet, fiche, 18) (auto)
        moveq   #18, d1
        bra     psp_63708
; enveloppes de psp_cf72c (D0 = dx, D1 = dy, D2 = sous-type, D3 = octet $57, D4 = absolu), relues dans le MIPS :
psp_cf8cc:                           ; sous-type 2, $57 = $FF, relatif
        moveq   #2, d2
        move.l  #$ff, d3
        moveq   #0, d4
        bra     psp_cf72c
psp_cf900:                           ; sous-type 6, $57 = $FF, relatif
        moveq   #6, d2
        move.l  #$ff, d3
        moveq   #0, d4
        bra     psp_cf72c
psp_cf9a4:                           ; sous-type 6, $57 = 0, relatif
        moveq   #6, d2
        moveq   #0, d3
        moveq   #0, d4
        bra     psp_cf72c
psp_cf858:                           ; étincelle au milieu de PSP 0x2CA-0x2D0 (position d'impact propre au PSP, sans
        rts                          ; équivalent) ; seuls appelants : psp_1b2454 / psp_1b24a8, jamais atteintes
