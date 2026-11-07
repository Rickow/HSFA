psp_1b07bc:                          ; (agent_integration_max) écrite à la main
; PSP 0x1B07BC(objet, n) : 1 si le pas de l'ADVERSAIRE actif dans n images porte une attaque (octet d'attaque du jeu de
; boîtes = mot A bits 8-15 = octet 9 du pas arcade). On avance de pas en pas (durée octet 0) tant que le cumul < n,
; sans franchir un dernier pas (drapeaux octet 1 & $C0), comme le PSP. D0 = n (octet) ; renvoie D0 = 0/1.
; Avant la boucle : disposition ARCADE (convertie). À partir de .boucle, A0 n'a plus de genre connu pour la passe
; (lea 20(a0)) : les accès au pas sont écrits DIRECTEMENT en disposition IMAGE (octets échangés par mot : drapeaux
; arcade 1 -> 0, durée 0 -> 1, attaque 9 -> 8) et laissés tels quels par convertit_max.py (signalés « non résolus »).
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
        move.b  0(a0), d1
        andi.b  #$c0, d1
        bne.s   .test
        tst.w   d2
        ble.s   .test
        lea     20(a0), a0
        moveq   #0, d1
        move.b  1(a0), d1
        sub.w   d1, d2
        bra.s   .boucle
.test:  tst.b   8(a0)
        bne.s   .oui
        moveq   #0, d0
        bra.s   .fin
.oui:   moveq   #1, d0
.fin:   movem.l (sp)+, d1-d2/a0-a1
        rts
