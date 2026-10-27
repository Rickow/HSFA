; Gestionnaires de CONTRE des persos MAX (octet $0D du pas = type de contre), ÉCRITS À LA MAIN — 2026-10-17.
; PSP : 0x71594 (le défenseur est touché) -> octet 5 du jeu de boîtes courant (+0x128) ; > 3 : 0x6CAF8 -> PTR 0x21DC10[n].
; Upper (v149, relevé agent_integration_max) : MOVE.B $C(A0),D0 (image) puis, pour D0 >= 4, aiguillage en ligne image $40D4
; (6 mots, valeurs 4-9) ; l'agrandissement (10-14) se fait par un talon qui saute ici : CONTRE_MAX_11 … CONTRE_MAX_14.
; Contexte d'ENTRÉE (celui des gestionnaires 4-9 d'Upper, ex. image $40EC = PSP 0x6CB30) : A6 = attaquant (joueur OU
; objet lancé), A1 = défenseur, A3 = attaque reçue (enregistrement de 32 o) ; D0 libre. SORTIE : RTS ; échec = le coup
; normal (JSR COUP_NORMAL puis RTS, comme Upper) ; contre = drapeau « contre déclenché » (MOVE.W #1,CONTRE_DECLENCHE(A5),
; PSP octet 0x87F50D) puis la routine de contre du perso. Tous les registres sont rendus intacts.
; Champs (pierre de Rosette = gestionnaire 4, PSP 0x6CB30 / Upper $40EC) : PSP +0x8 -> $8, +0xB -> $B, +0xC3 -> $EA
; (image $EB), attaque +0x13 / +0x15 -> $13 / $15 (mêmes décalages qu'en PSP) ; défenseur +0x2B9 -> $2C9 (champs votés) ;
; +0x151 (n° de joueur) -> $101.
; Approximations (champs PSP sans homologue établi, tests omis) :
;  - 11 : attaquant +0xFF ∈ {0, 1} (type de l'objet lancé : 3 = super chez Ryu) -> Eagle contre aussi ces objets-là ;
;  - 13 / 14 : attaquant +0x47A == 0 (drapeau posé seulement par Chun-Li et Dhalsim) -> Ingrid les contre toujours.
; Routines de contre appelées (brouillons, convention objet = A6, argument D0) :
;  - Eagle 11 : psp_1b2174(défenseur, attaquant) ; Eagle 12 : psp_1b24a8(attaquant, défenseur) ;
;  - Ingrid 13 / 14 : rappel +0x8C du gabarit d'Ingrid = psp_1c3ec0(défenseur, attaquant) (table 0x2B1EDC).

CONTRE_MAX_11:                          ; PSP 0x6CFA4 (Eagle)
        move.b  $b(a1), d0
        cmp.b   $2c9(a1), d0
        bne.s   .non
        tst.b   $8(a6)
        beq.s   .non
        tst.b   $ea(a6)
        beq.s   .non
        cmpi.b  #2, $13(a3)
        beq.s   .non
        move.w  #1, CONTRE_DECLENCHE(a5)
        movem.l d0-d7/a0-a6, -(sp)
        move.l  a6, d0                  ; attaquant
        movea.l a1, a6                  ; défenseur (Eagle)
        jsr     psp_1b2174
        movem.l (sp)+, d0-d7/a0-a6
        rts
.non:   jsr     COUP_NORMAL
        rts

CONTRE_MAX_12:                          ; PSP 0x6D040 (Eagle)
        move.b  $b(a1), d0
        cmp.b   $2c9(a1), d0
        bne.s   .non
        btst    #0, $ea(a6)
        beq.s   .non
        cmpi.b  #2, $13(a3)
        beq.s   .non
        movem.l d0-d7/a0-a6, -(sp)
        move.l  a1, d0                  ; défenseur (Eagle) ; objet = attaquant (A6)
        jsr     psp_1b24a8
        movem.l (sp)+, d0-d7/a0-a6
        move.w  #1, CONTRE_DECLENCHE(a5)
        rts
.non:   movem.l d0-d7/a0-a6, -(sp)      ; échec : voix PSP $217 du défenseur, puis le coup normal
        moveq   #0, d0
        move.b  $101(a1), d0            ; n° du joueur défenseur
        move.w  #$217, d1
        movea.l a1, a6                  ; objet (position du son) = défenseur
        jsr     psp_78408
        movem.l (sp)+, d0-d7/a0-a6
        jsr     COUP_NORMAL
        rts

CONTRE_MAX_13:                          ; PSP 0x6D0C8 (Ingrid) : attaque SANS le bit 0 de +$15
        move.b  $b(a1), d0
        cmp.b   $2c9(a1), d0
        bne.s   .non
        tst.b   $ea(a6)
        beq.s   .non
        tst.b   $8(a6)
        bne.s   .non
        btst    #0, $15(a3)
        bne.s   .non
        bra.s   contre_ingrid
.non:   jsr     COUP_NORMAL
        rts

CONTRE_MAX_14:                          ; PSP 0x6D15C (Ingrid) : attaque AVEC le bit 0 de +$15
        move.b  $b(a1), d0
        cmp.b   $2c9(a1), d0
        bne.s   .non
        tst.b   $ea(a6)
        beq.s   .non
        tst.b   $8(a6)
        bne.s   .non
        btst    #0, $15(a3)
        beq.s   .non
        bra.s   contre_ingrid
.non:   jsr     COUP_NORMAL
        rts

contre_ingrid:                          ; rappel +0x8C du gabarit d'Ingrid (défenseur, attaquant)
        move.w  #1, CONTRE_DECLENCHE(a5)
        movem.l d0-d7/a0-a6, -(sp)
        move.l  a6, d0                  ; attaquant
        movea.l a1, a6                  ; défenseur (Ingrid)
        jsr     psp_1c3ec0
        movem.l (sp)+, d0-d7/a0-a6
        rts
