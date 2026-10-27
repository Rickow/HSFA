; Fonctions moteur PSP des persos MAX ÉCRITES À LA MAIN en 68K (celles que traduire.py ne sait pas traduire) — 2026-10-04
; Convention (la même que les ébauches) : objet en A6, arguments D0-D2, retour D0 (+ drapeaux), A0/D3-D7 libres.

; ---- psp_cfec8 (225 appels : Eagle 90, Maki 65, Yun 70)
; « avancer l'animation sauf fin avec enchaînement » : si le pas courant n'a pas le bit 14 (contrôle 0x4xxx), avance
; l'animation ($2A7EA) ; sinon $33 = $FF. Renvoie D0 = 0 ou -128 selon le bit 7 de $33 (= PSP : v0 = $33 & 0x80 signé),
; drapeaux posés (BMI = animation terminée). Octet +1 du pas = drapeaux de fin (bit 6 = fin), comme l'arcade (0x2A822).
psp_cfec8:
        movea.l $1c(a6), a0
        btst    #6, 1(a0)
        bne.s   .fin
        jsr     $2a7ea.l
        bra.s   .retour
.fin:   move.b  #$ff, $33(a6)
.retour:
        moveq   #0, d0
        tst.b   $33(a6)
        bpl.s   .x
        moveq   #-128, d0
.x:     rts

; ---- psp_cf5d8 (45 appels : Eagle 21, Maki 12, Yun 12) — « au-dessus du sol ? »
; D0 = 1 si (Y + décalage) < sol ($64), sinon 0. Décalage = octet 3 du mot A du pas courant (bits 24-31, « décalage
; vertical » de la note HSFA), lu NON signé comme le PSP ; nul dans l'état $4/$5/$6 = 2/0/10 (PSP 1/0/5).
; L'arcade fait ce test en ligne : « move.w $14(a6),d0 ; cmp.w $64(a6),d0 ; bcc » (27 sites).
psp_cf5d8:
        moveq   #0, d1
        cmpi.w  #$0200, $4(a6)
        bne.s   .lit
        cmpi.b  #10, $6(a6)
        beq.s   .cmp
.lit:   movea.l $1c(a6), a0
        move.b  11(a0), d1           ; mot A, octet 3 (bits 24-31) : octets du pas = ordre PSP
.cmp:   add.w   $14(a6), d1
        moveq   #0, d0
        cmp.w   $64(a6), d1
        bge.s   .x
        moveq   #1, d0
.x:     rts

; ---- psp_cfd9c (16 appels) — lancer l'animation n (D1) d'une table EXPLICITE (D0 = TAB_xxxxxx, tables_explicites_*.s :
; table de pointeurs longs vers des scripts déjà au format 68K). PSP : $1C <- table[n], chargement du pas (psp_cfce0 =
; équivalent du chargement arcade $2A770 : $1C, $32-$35, boîtes $88/$C8, table $C0), plus deux champs de suivi propres
; au PSP (0x160 = table courante -> $110 ; 0x98 = mode « table explicite », inconnu côté 68K : non reporté, la reprise
; étant portée par le pointeur après le dernier pas). À valider au banc.
psp_cfd9c:
        move.l  d0, $110(a6)            ; PSP 0x160 (zone +0x50) : table courante
        movea.l d0, a0
        add.w   d1, d1
        add.w   d1, d1
        movea.l 0(a0,d1.w), a0
        jmp     $2a770.l                ; chargement du pas courant (arcade)

; ---- Scripts convertis au format 68K (tables_explicites_*.s) : les variantes PSP de chargement / avance de pas ont un
; équivalent direct dans le moteur arcade ($2A770 charge le pas en A0, $2A7EA avance et gère la reprise via +$14).
; ÉQUIVALENCES À VALIDER AU BANC : les champs de suivi propres au PSP (0x98 = « la frame a changé », 0x160) ne sont pas
; reportés.

; ---- psp_cfb6c (15 appels) — charger le pas n (D1) d'une table de petits pas d'objet fils (D0 = TAB_xxxxxx, format
; « pas8 » converti en pas 68K de 20 o, boîtes A/B/C à zéro : ⚠ à vérifier pour les projectiles).
psp_cfb6c:
        movea.l d0, a0
        andi.w  #$ff, d1                ; index = octet NON signé (appelants PSP : lbu ou constantes 5..$1E ; relevé agent_integration_max, 2026-10-17)
        add.w   d1, d1
        add.w   d1, d1
        movea.l 0(a0,d1.w), a0
        jmp     $2a770.l

; ---- psp_1d9b0 (19 appels, Ingrid) / psp_cfde0 (18 appels) — avancer l'animation (variantes PSP des formats pas8 /
; table explicite ; reprise par écart signé) = avance arcade, la reprise étant portée par le pointeur après le dernier pas.
; ---- psp_1d96c / psp_1da64 (acteurs de fin) : poser le pas d'animation pointé par l'argument (D0) = queue de l'arcade
; $1B6E0 ($1B6EE : $1C <- pas, $32 <- 4 premiers octets du pas). Le drapeau PSP 0x98 (jamais lu par l'arcade) est omis :
; traduit en $78, il écrasait les repères des acteurs (relevé HSFA, 2026-10-10).
psp_1d96c:
psp_1da64:
        tst.l   d0                      ; pointeur nul (image fixe non convertie, fin_pas118) : rien
        beq.s   .rien
        movea.l d0, a0
        jmp     $1b6ee.l
.rien:  rts

psp_1d9b0:
psp_cfde0:
        jmp     $2a7ea.l

; ---- psp_cfb90 (20 appels) — comme psp_cfec8 mais pour les objets à petits pas (même corps une fois convertis).
psp_cfb90:
        bra     psp_cfec8

; ---- FICHES (pas encore portées : dépendent d'un point ouvert)
; psp_1ef54 (14) : allocation d'un objet dans le réservoir d'EFFETS (42 places, compteur global 0xA4E7C6) ; a0 = type,
;   a1 = sous-type (pas un objet) ; renvoie l'objet. Équivalent arcade à confirmer : allocateurs $1C2C8 / $1C1C8 (le premier
;   est déjà l'équivalent de 0x1EEAC, réservoir d'objets). L'init de Ryu l'appelle (0x1EF54(0,0) puis lien parent/enfant).
; psp_1f24c (19) : appelle 0x1F2B0(a0, 6) puis incrémente l'octet global 0xA3E7C6 — bloc de globales hors A5
;   (0xA3E000…), sans équivalent connu ; a0 n'est pas un objet.

; ---- Réservoirs d'objets (2026-10-07) : allocateurs et libérations PSP <-> arcade, appariés par le code de type de $8
; (PSP × 4 = arcade) : 0x1EE74/0x1F19C = $1C278/$1C28E (type $0C) ; 0x1EEAC/0x1F1C8 = $1C2C8/$1C2DE ($10, standard) ;
; 0x1EF1C/0x1F220 = $1C318/$1C32E ($14) ; 0x1EF54/0x1F24C = $1C368/$1C37E ($18, EFFETS) ; 0x1EEE4/0x1F1F4 =
; $1C3AC/$1C3C2 ($1C). Traduits par traduire.py (ALLOC / API) : JSR alloc -> A4, en-tête, puis psp_raz_alloc.
; ⚠ Objets d'effet arcade = $80 octets (PSP 0xC0) : un champ PSP qui tombe au-delà de $7F (ex. allocations HORS_MAX
; $332-$367, valables pour la structure JOUEUR seulement) ne doit pas être écrit sur un objet fils.
; ⚠ Le type d'effet ($2) est un numéro PSP (ex. Eagle $33) : à raccorder dans la table des gestionnaires d'effets.
; psp_raz_alloc : ce que l'allocateur PSP 0x1EFE4 remet à zéro et que la libération arcade ne touche pas, pour les
; champs qui existent dans un objet de $80 : positions $10/$14 (PSP 0x10/0x14), vitesses/accélérations $40-$4C
; (PSP 0x60-0x6C), $74 (PSP 0x94). (PSP 0xA0-0xA3 = $FF, 0xA4, 0xA8, 0xA9 : hors objet arcade, non reportés.)
psp_raz_alloc:
        bsr     psp_raz_alpha           ; (2026-10-18) +0xAA PSP remis à 0 par l'allocateur (table MAX_ALPHA)
        moveq   #0, d7
        move.l  d7, $10(a4)
        move.l  d7, $14(a4)
        move.l  d7, $40(a4)
        move.l  d7, $44(a4)
        move.l  d7, $48(a4)
        move.l  d7, $4c(a4)
        move.l  d7, $74(a4)
        moveq   #1, d7                  ; rend « sne d7 » (succès) au code appelant
        rts

; ---- (2026-10-18, spécification HSFA) TABLE DE TRANSPARENCE : PSP +0xAA d'un objet (0 = alpha normal, 1 = additif
; FIX/FIX blanc, choisi par FUN_001E10DC) -> un octet par emplacement de réservoir, MAX_ALPHA[(adresse.w − $9400) >> 7]
; (0-119 : tirs $FF9400 / $FFA000 au pas de $100, objets $FFB000 / $FFC000 et effets $FFC800 au pas de $80) ; lu par
; EFFET_W (intégration). Hors plage : rien n'est écrit. psp_raz_alpha : A4 = objet neuf, remis à 0 (allocateur PSP 0x1F0F4).
        ifnd    MAX_ALPHA
MAX_ALPHA equ $FF7F00
        endif
psp_raz_alpha:
        clr.l   $28(a4)                 ; (2026-10-24, boucle infinie d'Ingrid après 2× QCF + P, relevé HSFA b17) l'allocateur
        clr.l   $2c(a4)                 ; PSP FUN_0001EAEC remet à 0 0x28 / 0x2C / 0x30 / 0x34 (liste chaînée des effets :
                                        ; $28 suivant, $2A / $2C / $2E fils) : rien ne retire un objet libéré de la liste,
                                        ; c'est cette remise à 0 qui empêche psp_1c6d58 de la refermer sur elle-même
        movem.l d0/a0, -(sp)
        move.w  a4, d0
        subi.w  #$9400, d0
        bcs.s   .hors
        cmpi.w  #$3C00, d0
        bcc.s   .hors
        lsr.w   #7, d0
        lea     MAX_ALPHA.l, a0
        clr.b   0(a0,d0.w)
.hors:  movem.l (sp)+, d0/a0
        rts

; ---- psp_6a638 (17 appels, Yun : psp_1bf944) / psp_6ab48 (3 appels : Eagle, Maki, Ingrid) — CONSTRUCTION À L'INIT de
; l'espace de travail PSP du perso (pointeur en objet+0x1A0, mémoire allouée par le moteur PSP) : l'init recopie un
; gabarit de 39 mots (Yun : EBOOT 0x2AD6DC), puis ces fonctions remplissent d'autres mots (T[7] boîtes, T[9], T[11],
; T[13], T[14], T[35], T[36], mots 629-639…) avec des adresses de scripts calculées depuis les données [6] chargées
; (a1 = base des pas, a2 = sous-en-tête : décalages +8+4i, nombres +264+4i ; n = 0 : un pointeur, n = −1 : liste de
; numéros de pas terminée par −1 -> base + 10 n, n > 0 : renvois dans le sous-en-tête). Le même schéma existe chez les
; persos PSP de SFA3 (0x14A718, 0x1667AC, 0x183CD8…).
; En 68K, ces données sont STATIQUES (tables converties : animations.json, tables_explicites_*.s, boîtes) et
; l'espace de travail PSP n'est lu par AUCUN code des persos MAX en dehors de cette init (vérifié : tous les accès
; « ??psp_0x1a0 » des ébauches sont dans psp_1bf944) -> rien à faire.
psp_6a638:
psp_6ab48:
        rts

; ---- SONS (2026-10-07). PSP 0x78408(objet, joueur a1, code a2) joue le son de code ABSOLU ; l'arcade $38E4 prend un
; INDEX dans la table de voix du perso ($E6(A6)) : appariement des votes faux pour MAX (voix d'Eagle, Maki, Yun, Ingrid
; absentes de la ROM son d'Upper). Point d'entrée UNIQUE des sons MAX : psp_78408 (D0 = joueur $101, D1 = code PSP).
; (2026-10-07) PSP : code < $200 = banque commune (se_mid.pac), code $2xx = voix n du perso (banque PPHD/PPVA de son
; pack, sons/voix_max.py). Arcade : commande QSound D1 via $32A4 / $3938 (balance d'après A6, +$500 côté 2 par $59,
; file $3168). Tables : SONS_COMMUNS (code PSP -> commande arcade) et VOIX_26..29 (n -> commande des échantillons MAX à
; importer dans la ROM son) ; 0 = muet. Entrée : D0 = joueur (PSP a1), D1 = code PSP, A6 = objet (position).
psp_78408:                           ; (2026-10-10) préserve TOUS les registres (A2/A3 des appelants, relevé HSFA)
        movem.l d0-d7/a0-a5, -(sp)
        cmpi.w  #$200, d1
        bcs.s   .commun
        andi.w  #$ff, d1             ; voix n du perso du joueur D0 ($FF8400 + $400 k, n° de perso $102)
        andi.w  #3, d0
        lsl.w   #8, d0
        lsl.w   #2, d0
        movea.l #$ff8400, a0
        adda.w  d0, a0
        moveq   #0, d2
        move.b  $102(a0), d2
        subi.b  #$26, d2
        cmpi.b  #3, d2
        bhi.s   .muet
        lsl.w   #2, d2
        lea     VOIX_MAX, a1
        movea.l 0(a1,d2.w), a1
        cmp.w   (a1)+, d1            ; nombre de voix
        bcc.s   .muet
        add.w   d1, d1
        move.w  0(a1,d1.w), d1
        bra.s   .jouer
.commun:
        cmpi.w  #SONS_COMMUNS_N, d1
        bcc.s   .muet
        add.w   d1, d1
        lea     SONS_COMMUNS, a1
        move.w  0(a1,d1.w), d1
.jouer: tst.w   d1
        beq.s   .muet
        move.w  d1, d0
        jsr     $32a4.l
        move.w  d0, d1
        andi.l  #$ffff, d1
        moveq   #0, d2
        moveq   #0, d3
        jsr     $3938.l
.muet:  movem.l (sp)+, d0-d7/a0-a5
        rts

; ---- psp_cee0c (auto avant : faux, cf. ci-dessus) — voix n (D0) du joueur : code $200 | n
psp_cee0c:
        move.w  d0, d1
        andi.w  #$ff, d1
        ori.w   #$200, d1
        moveq   #0, d0
        move.b  $101(a6), d0
        bra     psp_78408

; ---- psp_cec94 (13 appels : Eagle 5, Maki 7, Yun 1) — réplique i (D0) du perso : table PSP 0x23A6D8[ID] (entrées
; u16 code de voix, u16 durée ; listes qui se chevauchent, seuls les ID MAX $26-$28 en ont). Joue la voix (code $2xx,
; octet bas $FF = sans voix, mot $FFFF = pas d'entrée) et renvoie D0 = durée (0 sans entrée).
psp_cec94:
        moveq   #0, d1
        move.b  $102(a6), d1
        subi.w  #$26, d1
        bcs.s   .rien
        cmpi.w  #3, d1
        bhi.s   .rien
        add.w   d1, d1
        add.w   d1, d1
        lea     TAB_VOIX_MAX(pc), a0
        move.l  0(a0,d1.w), d1
        beq.s   .rien
        movea.l d1, a0
        add.w   d0, d0
        add.w   d0, d0
        adda.w  d0, a0
        move.w  (a0), d1
        cmpi.w  #$ffff, d1
        beq.s   .rien
        cmpi.b  #$ff, d1
        beq.s   .duree
        move.l  a0, -(sp)
        moveq   #0, d0
        move.b  d1, d0
        bsr     psp_cee0c
        movea.l (sp)+, a0
.duree: moveq   #0, d0
        move.w  2(a0), d0
        rts
.rien:  moveq   #0, d0
        rts
TAB_VOIX_MAX:
        dc.l    TAB_VOIX_26, TAB_VOIX_27, TAB_VOIX_28, 0          ; Ingrid : pas de table (PSP)
TAB_VOIX_26:
        dc.w    $0218, 60
        dc.w    $0219, 96
        dc.w    $021a, 72
TAB_VOIX_27:
        dc.w    $021b, 78
        dc.w    $021c, 102
        dc.w    $021d, 96
        dc.w    $021e, 78
        dc.w    $021f, 78
        dc.w    $0220, 60
        dc.w    $0221, 78
TAB_VOIX_28:
        dc.w    $0216, 90
        dc.w    $0217, 102
        dc.w    $0218, 78
        dc.w    $0219, 156
        dc.w    $021a, 90
        dc.w    $021b, 72
        dc.w    $021c, 30
        dc.w    $021d, 54
        dc.w    $021e, 72
        dc.w    $021f, 60

; ---- psp_cee5c (10 appels : Eagle 7, Maki 1, Yun 2) — son associé à une clé (D0) : table PSP 0x23A798 de 15 couples
; (clé, code de son ; -1 = aucun), parcourue depuis la fin comme le PSP (copie sur la pile, recherche décroissante).
psp_cee5c:
        lea     TAB_SONS_CLES+15*8(pc), a0
        moveq   #14, d2
.cherche:
        subq.l  #8, a0
        cmp.l   (a0), d0
        bne.s   .suite
        move.l  4(a0), d1
        cmpi.l  #-1, d1
        beq.s   .fin
        moveq   #0, d0
        move.b  $101(a6), d0
        bra     psp_78408
.suite: dbra    d2, .cherche
.fin:   rts
TAB_SONS_CLES:
        dc.l    6, 6
        dc.l    32, 40
        dc.l    33, 41
        dc.l    34, 42
        dc.l    35, 40
        dc.l    36, 41
        dc.l    37, 42
        dc.l    42, -1
        dc.l    44, 32
        dc.l    50, 36
        dc.l    52, 38
        dc.l    60, -1
        dc.l    62, -1
        dc.l    63, -1
        dc.l    84, -1


; ---- psp_24c04 (3 appels : Eagle, Maki, Yun) — « pose de victoire terminée » : bit du joueur ($101) dans $10B(A5)
; (PSP : octet 0x39CA67 de la structure d'état). ROSETTE RYU : l'arcade fait BSET $101,$10B(A5) deux fois par perso
; (fin des deux poses de victoire, Ryu 0x3415C/0x341DC, Ken 0x35C68/0x35CE8…), le moteur l'attend en 0xA0F8 ; le PSP
; passe par 0x24C04, seul écrivain, appelé 2 fois par Ryu (0xEAD1C, 0xEB0E0).
psp_24c04:
        move.b  $101(a6), d0
        bset    d0, $10b(a5)
        rts

; ---- psp_cfbf4 (4 appels : Eagle 1, Yun 3) — « l'objet est-il à l'écran ? » : D0 = 1 si 0 <= X écran + $40 < $200.
; Même test que l'affichage arcade $1B4D0 (= PSP 0x1D424) ; la parallaxe (PSP : plan $E = 2, $26) est celle de l'arcade
; ($1BD68 : A3 = caméra du plan $E, D0 = décalage, plan ×4 : arcade $E = 8).
psp_cfbf4:
        jsr     $1bd68.l
        neg.w   d0
        add.w   $10(a6), d0
        sub.w   $10(a3), d0
        addi.w  #$40, d0
        cmpi.w  #$200, d0
        scs     d0
        andi.l  #1, d0
        rts

; ---- psp_79f88 (1 appel, Yun) — charger le petit pas n (D0) de la table d'objets fils PSP 0x220120 (désignée dans la
; fonction moteur elle-même), convertie dans tables_explicites_yun.s (TAB_220120).
psp_79f88:
        move.w  d0, d1
        move.l  #TAB_220120, d0
        bra     psp_cfb6c

; ---- psp_d014c (3 appels : Eagle 2, Maki 1) — choix de la CIBLE d'une saisie après un coup porté. PSP : parmi les joueurs
; du masque +0x252 (bit k = joueur k touché par le coup, posé par le moteur PSP en 0x6CA58 à chaque coup) en ignorant ceux
; dont 0x75 ($55) a le bit 7 ; l'adversaire courant de préférence. (2026-10-17) Le moteur arcade / Upper ne tient PAS ce
; masque (l'ancienne traduction le lisait en $272, champ arcade sans rapport, jamais posé : aucune cible, chope de la
; course de Maki absente). Tous les appelants testent d'abord « coup porté » ($5B = 1, posé par le moteur arcade) : en
; combat à deux, le joueur touché est l'adversaire $38. D0 = adversaire ($55 bit 7 clair), sinon 0.
psp_d014c:
        moveq   #0, d0
        move.w  $38(a6), d1
        beq.s   .fin
        movea.w d1, a0          ; pointeur d'objet
        btst    #7, $55(a0)
        bne.s   .fin
        move.l  a0, d0
.fin:   rts

; ---- psp_entrees — MIROIR DES ENTRÉES au format PSP pour le code MAX (À APPELER À CHAQUE IMAGE pour un joueur MAX, après
; la mise à jour arcade des entrées $27AAC, avant le gestionnaire du perso). Mesures : PPSSPP (Ingrid, entraînement) et
; routine arcade $27AAC. Arcade : $370 courant, $372-$376 images précédentes, $378 appuyés (courant ET NON précédent),
; $37A relâchés, $37C variante (sens selon $2C9). PSP : 0x2F0 courant, 0x2F8 appuyés, 0x2FA relâchés, 0x2FC variante.
; Directions identiques (bits 0-3 : gauche 1 / droite 2 relatifs au sens, bas 4, haut 8). Boutons : UPPER poings
; $0100/$0200/$0400, pieds $1000/$2000/$4000 (relevé au banc 2026-10-18 ; l'ancienne note disait l'inverse) ; PSP poings
; $10/$20/$40, pieds $80/$100/$200.
; Miroir : $3E0 (0x2F0), $3E2 (0x2F8), $3E6 (0x2FA), $3E8 (0x2FC) — ⚠ $3E6-$3E9 : à confirmer libres (HSFA).
psp_entrees:
        move.w  $370(a6), d0
        bsr.s   .conv
        move.w  d0, $3e0(a6)
        move.w  $378(a6), d0
        bsr.s   .conv
        move.w  d0, $3e2(a6)
        move.w  $37a(a6), d0
        bsr.s   .conv
        move.w  d0, $3e6(a6)
        move.w  $37c(a6), d0
        bsr.s   .conv
        move.w  d0, $3e8(a6)
        rts
.conv:  move.w  d0, d1
        move.w  d0, d2
        andi.w  #$000f, d0              ; directions
        andi.w  #$0700, d1              ; (2026-10-18, mesuré au banc par HSFA) Upper : POINGS bits 8-10 -> PSP 4-6
        lsr.w   #4, d1                  ; ($0100 petit poing -> $10)
        or.w    d1, d0
        andi.w  #$7000, d2              ; PIEDS bits 12-14 -> PSP 7-9 ($2000 moyen pied -> $100)
        lsr.w   #5, d2
        or.w    d2, d0
        rts

; ---- (2026-10-07) points : PSP 0x33058 / 0x331F8 / 0x33130 = arcade $2065C / $2070A / $206AE (pas à pas identiques ;
; mode PSP 0x39CA19 = $AC(A5), 0x32E60 = $2055C) -> traduits directement (API), plus de neutralisation.

; ---- psp_67468 (sous-fonction de 68380, contre-alpha) — objet du camp du joueur : arcade $2E8C0 (A0 = $156/$158(A5)
; selon $59) ; le PSP renvoie en D0 (et ajoute une inversion selon le mode $138/$AC, propre au versus console).
psp_67468:
        jsr     $2e8c0.l
        move.l  a0, d0
        rts

; ---- psp_66bb4 (sous-fonction de 66ae8 : saisie) — mettre la VICTIME (PSP a1 -> D0) en état « saisie » : arcade $2E4C2
; (victime en A1, attaquant en A6 ; pas à pas : état $02060000, $67, $2CA, $3A = 4, $263, $23B, $38, points $2065C,
; $3E selon $B9, remises à zéro). Renvoie D0 = 1.
psp_66bb4:
        movea.l d0, a1
        jmp     $2e4c2.l

; ---- psp_66ae8 (4 appels : Eagle 2, Maki 1, Yun 1) — SAISIE : attaquant A6, D0 = victime (PSP a1), D1 = entrée d'attaque
; (PSP a2). Rosette : arcade $2E4B6 « tst.b $F(a3) ; bmi ; jsr $3608 (son de saisie) ; $2E4C2 (état de la victime) ».
; Sons PSP : $2B (saisie), $2E (victime $2CF = PSP 0x2BF), $217 (réplique d'Eagle saisi : ID $26, union $3C0, $AA = 8
; c.-à-d. PSP 4, champ ×2), effets 0x6A3CC (0,1) et (9,8) : tous via psp_78408 / non reportés (sons MAX muets).
; ⚠ quand psp_78408 jouera vraiment, il devra préserver A2/A3.
psp_66ae8:                           ; D0 = victime (mot ou long : Eagle pose move.w $38(a6),d0 ; Maki : D0 = objet
        movea.w d0, a2                   ; trouvé par d014c, rangé aussi en $38 par T_1be710), D1 = fiche de coup ($A0 + n)
        movea.l d1, a3
        btst    #7, $f(a3)
        bne.s   .s1
        moveq   #0, d0
        move.b  $101(a2), d0
        moveq   #$2b, d1
        bsr     psp_78408
.s1:    tst.b   $2cf(a2)
        beq.s   .s2
        moveq   #0, d0
        move.b  $101(a2), d0
        moveq   #$2e, d1
        bsr     psp_78408
.s2:    cmpi.b  #$26, $102(a2)
        bne.s   .saisie
        tst.l   $3c0(a2)
        beq.s   .saisie
        cmpi.b  #8, $aa(a2)
        bne.s   .saisie
        moveq   #0, d0
        move.b  $101(a2), d0
        move.w  #$217, d1
        bsr     psp_78408
.saisie:
        move.l  a2, d0
        bra     psp_66bb4

; ---- psp_63708 / psp_64220 (reconnaissance des manipulations ; Yun 2 appels directs, Maki 1, + 13 enveloppes cef20…)
; PSP : 63708(objet, fiche, n°) et sa variante « pressions » 64220 ; fiche = objet + 0x350..0x3B8 (8 octets), déf. =
; table 0x2178C8[n°]. C'est la machine de l'arcade : entrées $2D5E2 + 8k (LEA déf.(pc),A3 ; tronc commun $2D7E6,
; $2D900 = variante pressions, $2DBBA = charges), fiche en A4 = objet + $180..$1E8 (= PSP − $1D0), D0 = −1 quand la
; manipulation est finie. Les déf. PSP sont celles de l'arcade réordonnées (mouvements.py : 46 / 48 identiques, dont
; toutes celles des persos MAX ; 0x2000 = tenue <-> $80, 0x400 = dernière direction <-> $10, 0x4070 / 0x8380 / 0xD3F0
; <-> $0F00 / $F000 / $FF40). Le test PSP 63c30 (« touches raccourcis » de la console quand 0x39CA52 = 2) n'a pas
; d'équivalent arcade : omis. Entrée D0 = adresse de la fiche PSP, D1 = n° ; sortie D0 = 1 (reconnue) ou 0, drapeaux.
psp_63708:
psp_64220:
psp_64a34:                           ; 3e variante PSP (table 0x217D4C, n° 39 = $2D722 / tronc $2DA84 : direction tenue + bouton)
        movem.l d1-d2/a1-a4, -(sp)
        movea.l d0, a4
        lea     -$1d0(a4), a4
        move.l  a4, d2                  ; (2026-10-10, relevé HSFA) Upper emploie $1D5/$1D7 : la fiche $1D0 (PSP 0x3A0,
        sub.l   a6, d2                  ; Yun) passe en $1E0 (PSP 0x3B0, libre chez Yun)
        cmpi.w  #$1d0, d2
        bne.s   .fiche
        lea     $10(a4), a4
.fiche: moveq   #0, d0
        cmpi.w  #47, d1
        bhi.s   .x
        lsl.w   #2, d1
        lea     TAB_MANIPS(pc), a0
        move.l  0(a0, d1.w), d2
        beq.s   .x
        movea.l d2, a0
        jsr     (a0)
        tst.l   d0
        sne     d0
        andi.l  #1, d0
.x:     movem.l (sp)+, d1-d2/a1-a4
        tst.l   d0
        rts
; ---- psp_1b9544 (Eagle) / psp_1beec0 (Maki) / psp_1c56cc (Yun) : remise à zéro des fiches de manipulation
; PSP : 72 longs à partir de objet + 0x350 (fiches PSP 0x350..0x46F). Traduite telle quelle, la boucle débordait de la
; structure joueur ($400) sur le joueur suivant (relevé HSFA, 2026-10-10). Les persos MAX n'utilisent que les fiches PSP
; 0x350..0x3B8 = arcade $180..$1EF (PSP − $1D0, cf. psp_63708) : on n'efface que cette zone, SAUF $1D0-$1D7 (champs
; propres à Upper en $1D5/$1D7, relevé HSFA 2026-10-10 ; la fiche PSP 0x3A0 de Yun est déplacée en $1E0 par psp_63708).
psp_1b2e54:                          ; Eagle (même effacement ; relevé agent_integration_max 2026-10-11)
psp_1b9544:
psp_1beec0:
psp_1c56cc:
        lea     $180(a6), a0
        moveq   #19, d3                 ; $180-$1CF
.raz:   clr.l   (a0)+
        dbra    d3, .raz
        lea     $1d8(a6), a0
        moveq   #5, d3                  ; $1D8-$1EF
.raz2:  clr.l   (a0)+
        dbra    d3, .raz2
        rts

TAB_MANIPS:      ; n° de manip PSP (table 0x2178C8) -> entrée arcade $2D5E2 + 8k (0 = sans équivalent)
        dc.l    0, $2d5ea, $2d5f2, $2d60a      ; n° 0 : entrée $2D5E2 supprimée par Upper (inutilisée par MAX)
        dc.l    $2d612, $2d61a, $2d622, $2d5fa
        dc.l    $2d602, $2d63a, $2d62a, $2d632
        dc.l    0, $2d642, $2d64a, $2d652
        dc.l    $2d65a, $2d662, $2d66a, $2d672
        dc.l    $2d67a, $2d682, $2d68a, $2d692
        dc.l    $2d69a, $2d6a2, $2d6aa, $2d6b2
        dc.l    $2d6ba, $2d6c2, $2d6ca, $2d6d2
        dc.l    $2d6da, 0, $2d6ea, $2d6f2
        dc.l    $2d6fa, $2d702, $2d70a, $2d722
        dc.l    $2d712, $2d71a, $2d73a, $2d742
        dc.l    $2d72a, $2d732, $2d74a, $2d752

; ---- psp_1c70d8 (Ingrid, objets fils : orbite) — PSP en FLOTTANTS (COP1) : angle = (40 − $3C) & 31 (PSP 0x4E),
; c = cos·1000, s = sin·1000 par les tables quart d'onde 0x2B1F98 / 0x2B1FAA (0x1C7514 / 0x1C75BC), puis
; X(16.16) ±= trunc(rx·256·c / 100000 · 256) (− si $B ≠ 0), Y += trunc(ry·256·s / 125000 · 256).
; 68K : coefficients par angle précalculés (K = c·65536/100000, s·65536/125000, arrondis : écart < rx/65536 px).
; Entrée : D0 = rx, D1 = ry (mots signés). D0/D1/D3/A0 modifiés.
psp_1c70d8:
        moveq   #40, d3
        sub.b   $3c(a6), d3
        andi.w  #31, d3
        add.w   d3, d3
        lea     TAB_ORBITE_X(pc), a0
        muls    0(a0,d3.w), d0
        tst.b   $b(a6)
        bne.s   .gauche
        add.l   d0, $10(a6)
        bra.s   .y
.gauche:
        sub.l   d0, $10(a6)
.y:     lea     TAB_ORBITE_Y(pc), a0
        muls    0(a0,d3.w), d1
        add.l   d1, $14(a6)
        rts
TAB_ORBITE_X:   ; cos(2πk/32)·1000 (table PSP) · 65536 / 100000
        dc.w    655, 643, 608, 549, 463, 357, 245, 125
        dc.w    0, -125, -245, -357, -463, -549, -608, -643
        dc.w    -655, -643, -608, -549, -463, -357, -245, -125
        dc.w    0, 125, 245, 357, 463, 549, 608, 643
TAB_ORBITE_Y:   ; sin(2πk/32)·1000 (table PSP) · 65536 / 125000
        dc.w    0, 100, 196, 285, 371, 439, 486, 514
        dc.w    524, 514, 486, 439, 371, 285, 196, 100
        dc.w    0, -100, -196, -285, -371, -439, -486, -514
        dc.w    -524, -514, -486, -439, -371, -285, -196, -100

; ---- psp_1dc32c / psp_1f338 / psp_1caf0c : EFFETS DE DÉCOR d'Ingrid (2026-10-07) — NEUTRALISÉS (visuels seulement).
; PSP : 0x1DC32C(n) = effet de fond n pendant ses supers (Ingrid : n = 1 ou 18) : libère l'effet courant (0xA4CED4),
; note n dans la structure du décor (0x87FCB0 + 0x6E) et crée un objet de 0x94 octets de type 13, sous-type n + 16
; (0x1F338 = allocation dans le réservoir de 32 objets 0x819C58, compteur 0xA3E7C9 ; gestionnaire par type 0x221AA0,
; type 13 inscrit dynamiquement) ; 0x1CAF0C(objet, n) = animation n de ces objets (table du décor 0x87FCB0 + 0x118).
; Aucun perso d'arcade ne s'en sert : pas d'équivalent arcade direct (à refaire plus tard avec les effets de fond
; arcade si on le souhaite). Ici : allocation refusée (D0 = 0 : les appelants testent le résultat, sauf 0x1CABC8
; qui écrit en $7C(0) = ROM, sans effet), fond inchangé.
psp_1dc32c:
psp_1caf0c:
        rts
psp_1f338:
        moveq   #0, d0
        rts

; ---- psp_cf3e8 (Eagle, 1 appel) — tentative de SAISIE avec l'entrée d'attaque n (D0) : conditions propres à MAX sur
; l'adversaire (PSP 0x2BE, 0x21F, 0x10E nuls -> $2CE, $23F, $D6) puis = arcade $2E3E0 (= PSP 0x6666C, même cœur que
; 0xCF2FC : drapeau du pas adverse $D, $25D, $10E(A5), $31, $67, boîte $A0[n] contre $9C[$CB], test $24936, saisie
; $2E4C2 ; D0 = 1 si saisi, 0 sinon).
psp_cf3e8:
        movea.w $38(a6), a1
        tst.b   $2ce(a1)
        bne.s   .non
        tst.b   $23f(a1)
        bne.s   .non
        tst.b   $d6(a1)
        bne.s   .non
        jmp     $2e3e0.l
.non:   moveq   #0, d0
        rts

; ---- psp_cf644 (Yun, 1 appel) — « au-dessus du sol ? » avec décalage : comme psp_cf5d8, plus D0 = dy (mot signé) :
; D0 = 1 si Y + décalage du pas + dy < sol ($64) ; décalage nul dans l'état 1/0/5 (68K $0200 / 10).
psp_cf644:
        moveq   #0, d1
        cmpi.w  #$0200, $4(a6)
        bne.s   .lit
        cmpi.b  #10, $6(a6)
        beq.s   .cmp
.lit:   movea.l $1c(a6), a0
        move.b  11(a0), d1           ; mot A, octet 3 (non signé, comme le PSP)
.cmp:   add.w   d0, d1
        add.w   $14(a6), d1
        moveq   #0, d0
        cmp.w   $64(a6), d1
        bge.s   .x
        moveq   #1, d0
.x:     rts

; ---- psp_5df68 (Maki, 1 appel ; fonction moteur PSP sans équivalent arcade) — début d'une attaque enchaînée :
; $361 (PSP 0x10A) = 0, $80 = 2 (PSP 0xC0 = 1, ×2), $2AEBC (= 0x5F114), puis selon $125 / $2C5 / $2C0 : rappel n° 17 de
; la table du perso (PSP *(0x1A0)+0x44 : table de 39 rappels recopiée à l'initialisation depuis 0x2A3198 / 0x2A6268 /
; 0x2AD6DC / 0x2B1EE0), ou 0x77E00 / 0x5FD4C (variantes MAX, traduites). Rappel choisi par le n° de perso $102 (PSP 0x152).
psp_5df68:
        clr.b   $361(a6)
        move.b  #2, $80(a6)
        jsr     $2aebc.l
        tst.b   $125(a6)
        beq.s   .rappel
        tst.b   $2c5(a6)
        beq.s   .c0
        bsr     psp_77e00
        bra.s   .fin
.c0:    tst.b   $2c0(a6)
        beq.s   .rappel
        bsr     psp_5fd4c
        bra.s   .fin
.rappel:
        moveq   #0, d0
        move.b  $102(a6), d0
        subi.b  #$26, d0
        cmpi.b  #3, d0
        bhi.s   .fin
        add.w   d0, d0
        add.w   d0, d0
        lea     .r17(pc), a0
        movea.l 0(a0,d0.w), a0
        jsr     (a0)
.fin:   move.b  #2, $80(a6)
        rts
.r17:   dc.l    psp_1b36f8, psp_1b9ef8, psp_1bf63c, psp_1c67a4      ; Eagle, Maki, Yun, Ingrid (rappel n° 17)

; ---- psp_77e00 / psp_5fd4c : appelées par psp_5df68 ; traduction automatique recopiée (traduire.py, 2026-10-07)
psp_77e00:
        move.b    #$5, $362(a6)
        move.b    #$1, $3f3(a6)
        move.b    #$2, $4(a6)
        move.b    #$10, $6(a6)
        clr.b     $7(a6)
        clr.b     $5(a6)
        move.b    $2c9(a6), $b(a6)
        clr.b     $2c5(a6)
        clr.b     $2c8(a6)
        clr.b     $5b(a6)
        move.b    $3f2(a6), $aa(a6)
        clr.b     $365(a6)
        tst.b     $364(a6)
        bgt     L_77e74
        tst.b     $364(a6)
        bmi     L_77ec8
        clr.b     $244(a6)
        move.w    #$f, $2a6(a6)
        move.w    #$5, $2a8(a6)
        move.b    #$1, $d6(a6)
        rts
L_77e74:
        cmpi.b    #$2, $364(a6)
        blt     L_77e90
        cmpi.b    #$3, $364(a6)
        blt     L_77eb0
        bra     L_77ec8
L_77e90:
        clr.b     $244(a6)
        move.w    #$30, $2a6(a6)
        move.w    #$10, $2a8(a6)
        move.b    #$1, $d6(a6)
        rts
L_77eb0:
        move.b    #$4, $244(a6)
        move.w    #$51, $2a6(a6)
        move.w    #$1b, $2a8(a6)
L_77ec8:
        move.b    #$1, $d6(a6)
        rts
psp_5fd4c:
        move.b    #$2, $4(a6)
        move.b    #$4, $5(a6)
        clr.b     $6(a6)
        clr.b     $7(a6)
        move.b    $2c9(a6), $b(a6)
        rts

; ---- psp_66890 (Yun, 1 appel) — saisie avec l'entrée d'attaque n (D0), essayée sur chaque adversaire du masque PSP
; 0x107 (jusqu'à 4 joueurs) ; si $3E ≠ 0 : échec. Conditions sur la victime (0x49, 0x21F, 0x23D nuls ; états 1/2,
; 1/0, ou 1/1 avec 0x74 = 6 ; 0x330 nul) puis 0x669FC (boîtes + saisie), adversaire retenu en 0x5C. Arcade (un seul
; adversaire $38) : chemin « joueur » de $2E3FE = $2E422 (mêmes conditions : $204 / $200 / $24E / $202 avec $54 = $C,
; $23F, $25D, puis $2E462 : $10E(A5), $31, $67, boîtes, $24936, saisie $2E4C2) ; D0 = 1 si saisi.
psp_66890:
        tst.b   $3e(a6)
        bne.s   .non
        jmp     $2e422.l             ; n° d'entrée dans D0 jusqu'à $2E462 (Upper : plus de $32F, cf. ADRESSES-MAX-UPPER.md)
.non:   moveq   #0, d0
        rts

; ---- psp_672dc (Yun, 1 appel) — coup appliqué directement à la victime D0 avec l'entrée d'attaque n (D1) : état
; victime 1/1/0/0, champs de l'entrée $A0[n] (+10 / +9 / +13 / +28…), dégâts et effets. PSP 0x67144 (= arcade $2E7F2)
; = 0x672DC(objet, adversaire 0x5C, n) : sur l'arcade (deux joueurs) la victime EST l'adversaire $38 -> $2E7F2 avec
; D0 = n. (Écarts PSP négligés : masque MAX 0x479 de la victime, appel 0x68A2C hors état 8, que $2E7F2 ne fait pas.)
psp_672dc:
        move.w  d0, $38(a6)          ; victime = adversaire (déjà le cas en combat à deux)
        move.l  d1, d0
        jmp     $2e7f2.l

; ---- psp_6f35c (Maki, 1 appel, après un coup direct $2E7F2) — compteur de combo PSP (0x7E, plafond 99) et record par
; camp (0x165 des joueurs, écrans console). L'arcade n'appelle rien de tel après $2E7F2 (119 sites) : son compte de
; coups est tenu par son propre moteur. -> neutralisée (à revoir au banc si l'affichage « HITS » manque sur ce coup).
psp_6f35c:
        rts

; Types d'objet des projectiles MAX ($2 de l'objet, index de $32F46 = TYPE d'objet) — valeurs fixées par l'intégration
; HSFA (2026-10-17) : Eagle $26, Yun $2D, Ingrid $2E (Maki : pas de projectile)
TYPE_PROJ_EAGLE equ $26
TYPE_PROJ_YUN   equ $2d
TYPE_PROJ_INGRID equ $2e
; ---- psp_fils_26..29 : entrées à placer dans $32F46[TYPE_PROJ_xxx] (routine des projectiles du perso, appelée par la boucle
; $32EFA, A6 = objet de $100). Le type d'objet PSP est noté en $FF à la création (Upper lit $22 en mot) (traduction de 0x1ED2C) ; tables PSP
; type -> routine : Eagle 0x2A3174, Maki 0x2A6248, Yun 0x2AD6B0, Ingrid 0x2B1EA0. Maki n'a pas de projectile ($1C1C8) :
; ses types 0x2F/0x30/0x31 sont des objets du réservoir $1C368, comme les effets des autres.
psp_fils_26:
        jmp     psp_1b3ee0           ; Eagle, type 0x2B
psp_fils_28:
        jmp     psp_1c0dd0           ; Yun, type 0x2C
psp_fils_29:
        jmp     psp_1c7840           ; Ingrid, types 0x2D / 0x2E (aiguillage interne par sous-type $3)

; ---- initialisations des 4 persos (PSP 0x1B3668 / 0x1B9E68 / 0x1BF3EC / 0x1C619C) sans la recopie de la table de
; rappels dans l'espace de travail PSP (objet+0x1A0, sans équivalent : voir psp_6a638) ; psp_1bf944 (Yun) ne fait que
; remplir cet espace -> vide. Le reste = traduction automatique.
pose_table_sauts:                    ; table de sauts au format PSP selon le style ($132), comme l'arcade $2BE6A
        lea     TAB_SAUT_PSP_A, a0   ; ($2D4 : $DD792 / $DDF92 / $DE792) ; lue via 0x2C4 -> $34A
        tst.b   $132(a6)
        beq.s   .t
        lea     TAB_SAUT_PSP_C, a0   ; $132 = $FF : $DE792 (PSP 0x21CE3E)
        cmpi.b  #$ff, $132(a6)
        beq.s   .t
        lea     TAB_SAUT_PSP_B, a0   ; autre : $DDF92 (PSP 0x21C8FE)
.t:     move.l  a0, $34a(a6)
        rts
psp_1b3668:                          ; Eagle
        bsr     pose_table_sauts
        move.b  #$1, $35f(a6)
        move.b  #$ff, $c(a6)
        move.b  $101(a6), d0         ; n° de joueur (octet, adresse impaire : pas d'accès mot)
        ext.w   d0
        move.w  d0, $356(a6)
        move.l  #$1, $342(a6)
        moveq   #1, d0
        bra     psp_1b38b8
psp_1b9e68:                          ; Maki
        bsr     pose_table_sauts     ; (2026-10-18) $34A manquait : course arrière + pied de Maki (psp_1b9070) lisait ses vitesses à une adresse quelconque
        move.b  #$1, $35f(a6)
        move.b  #$ff, $c(a6)
        move.b  $101(a6), d0         ; n° de joueur (octet, adresse impaire : pas d'accès mot)
        ext.w   d0
        move.w  d0, $356(a6)
        move.l  #$1, $342(a6)
        moveq   #1, d0
        bra     psp_1ba2b8
psp_1bf3ec:                          ; Yun
        bsr     pose_table_sauts
        move.b  #$1, $35f(a6)
        move.b  #$ff, $c(a6)
        move.b  $101(a6), d0         ; n° de joueur (octet, adresse impaire : pas d'accès mot)
        ext.w   d0
        move.w  d0, $356(a6)
        move.l  #$1, $342(a6)
        moveq   #4, d0
        moveq   #0, d1
        bra     psp_1bfb14
psp_1c619c:                          ; Ingrid
        bsr     pose_table_sauts
        move.b  #$1, $35f(a6)
        move.b  #$ff, $c(a6)
        move.b  $101(a6), d0         ; n° de joueur (octet, adresse impaire : pas d'accès mot)
        ext.w   d0
        move.w  d0, $356(a6)
        move.l  #$1, $342(a6)
        moveq   #1, d0
        bra     psp_1c1de0
psp_1bf944:
        rts

; ---- psp_1c7514 / psp_1c75bc (cos / sin tabulés d'Ingrid) : appelées seulement par 0x1C70D8, réécrite à la main
; (psp_1c70d8, tables TAB_ORBITE_X/Y) -> jamais appelées ici.
psp_1c7514:
psp_1c75bc:
        moveq   #0, d0
        rts

; ---- num_image_psp (2026-10-07) : A0 = pas d'animation 68K -> D7.w = n° d'image PSP. Seuls appelants : les CALQUES
; d'Ingrid (0x1C8C30 = type 0x37 sous-type 2, créé à l'init par 0x1C8818 ; 0x1C8F9C = type 0x3A) qui, sur PSP, dessinent
; l'autre moitié de son corps (images PSP : bas 0-690, haut 691-1381) par n° d'image direct (0x54 = $20). La conversion a
; FUSIONNÉ les moitiés (pose k = bas k + haut 691+k, convert_max.INGRID_LOWER/UPPER) et l'arcade n'affiche que par le
; pas $1C : ces calques restent invisibles (pas de double affichage) ; $20 est sans effet -> valeur neutre.
num_image_psp:
        move.w  #691, d7
        rts

; ---- psp_63c30 (2026-10-07) — « touche raccourci » de la console PSP (0x63BB0/0x63794/0x63A60, réglage 0x39CA52) :
; sans équivalent arcade, toujours 0 (comme dans le pont psp_63708).
psp_63c30:
        moveq   #0, d0
        rts

; ---- psp_cf72c (2026-10-07) — effet moteur (type 4 du réservoir $1C2C8, sous-type D2) placé par rapport à l'objet :
; PSP à 5 arguments (a1 = dx, a2 = dy, a3 = sous-type, t0 = octet $57, t1 = position absolue) -> D0, D1, D2, D3, D4.
; Référence ($36 du nouvel objet) : adversaire $38 pour un joueur ($8 = 0), propriétaire $36 sinon ; $6B = 2 si sa
; solidité $50 < 0 ; position relative (dx selon l'orientation $B & 1) ou absolue ; 0x56 (affichage PSP) omis.
psp_cf72c:
        movem.l d5/a1, -(sp)
        movea.w $38(a6), a1
        tst.b   $8(a6)
        beq.s   .ref
        movea.w $36(a6), a1
.ref:   jsr     $1c2c8.l             ; création d'objet -> A4 (Z si échec)
        beq.s   .x
        move.b  #1, (a4)
        move.b  #$04, $2(a4)
        move.b  d2, d5
        add.b   d5, d5               ; type du moteur : sous-type ×2
        move.b  d5, $3(a4)
        bsr     psp_raz_alloc
        move.w  a1, $36(a4)
        move.b  d3, $57(a4)
        move.b  $59(a6), $59(a4)
        move.b  #$ff, $67(a4)
        clr.w   $3a(a4)
        clr.b   $6b(a4)
        tst.w   $50(a1)
        bpl.s   .pos
        move.b  #2, $6b(a4)
.pos:   tst.w   d4
        bne.s   .abs
        move.b  $b(a6), d5
        andi.b  #1, d5
        move.b  d5, $b(a4)
        beq.s   .dx
        neg.w   d0
.dx:    add.w   $10(a6), d0
        add.w   $14(a6), d1
.abs:   move.w  d0, $10(a4)
        move.w  d1, $14(a4)
.x:     movem.l (sp)+, d5/a1
        rts
; enveloppes PSP (sous-type, $57, absolu) : 0xCF934 / 0xCF970 = ($B, $FF, non), 0xCFA38 = ($E, 0, non), 0xCF9D8 = ($6, $FF,
; oui) au bord de l'écran : X = caméra $290(A5) (+ $180 si $B), Y = Y de l'objet + dy (PSP 0x80F970 + 0x12 = $290(A5))
psp_cf934:
psp_cf970:
        moveq   #$b, d2
        move.l  #$ff, d3
        moveq   #0, d4
        bra     psp_cf72c
psp_cfa38:
        moveq   #$e, d2
        moveq   #0, d3
        moveq   #0, d4
        bra     psp_cf72c
psp_cf9d8:
        move.w  $290(a5), d0         ; caméra (disposition arcade ; image Upper : $292(A5), moitiés de long échangées)
        tst.b   $b(a6)
        beq.s   .g
        addi.w  #$180, d0
.g:     add.w   $14(a6), d1
        moveq   #6, d2
        move.l  #$ff, d3
        moveq   #1, d4
        bra     psp_cf72c

; ---- psp_670ac (2026-10-07) — coup direct n (D0) si l'adversaire n'est pas en l'air ($31) : arcade SFA3 $2E700, ABSENTE
; d'Upper (ADRESSES-MAX-UPPER.md §7) -> écrite ici sur la suite commune $2E646 (Upper : va 0x15eb70), sans $32F.
psp_670ac:
        movea.w $38(a6), a1
        tst.b   $31(a1)
        bne.s   .non
        jmp     $2e646.l
.non:   moveq   #0, d0
        rts

; ---- tables de sons MAX (2026-10-07) : commandes QSound arcade, 0 = muet (à remplir : sons/README.md)
SONS_COMMUNS_N equ $100
SONS_COMMUNS:   ; code PSP 0..$FF (banque commune se_mid.pac) -> commande arcade (2026-10-17 : Rosette des tables de
; sons par pas, gabarit +0x90 PSP ↔ T_74C538 d'Upper, + appariement acoustique d'agent_voix_max ; voir sons_pas_max.py)
        dcb.w   $D, 0
        dc.w    CMD_SEQ_0D         ; code $0D : forte (agent_son_max : séquence se_mid 10 / I_009 = bruitage arcade $020E)
        dcb.w   $12, 0
        dc.w    $0239              ; code $20 : forte (Rosette 2 + agent_voix_max (forte))
        dcb.w   $1, 0
        dc.w    $0230              ; code $22 : forte (Rosette 9 ; agent_voix_max : $0257, même échantillon que $0230)
        dc.w    $0231              ; code $23 : moyenne (Rosette 3)
        dcb.w   $3, 0
        dc.w    $0263              ; code $27 : moyenne (agent_voix_max (moyenne) ; Rosette : $0238 (3) / $0263 (2))
        dc.w    $0220              ; code $28 : forte (Rosette 38/43 (index 1))
        dc.w    $0221              ; code $29 : forte (Rosette 38/39 (index 2))
        dc.w    $0222              ; code $2A : forte (Rosette 33 ($0222, index 3 ; $0223 à l'index 4 chez les persos d'arcade))
        dc.w    $023e              ; code $2B : forte (agent_voix_max (forte))
        dc.w    CMD_SEQ_2C         ; code $2C : importée (agent_son_max : séquence se_mid 37 / I_016, sans équivalent arcade)
        dcb.w   $3, 0
        dc.w    $022e              ; code $30 : forte (Rosette 21 + agent_voix_max (forte))
        dcb.w   $5, 0
        dc.w    $023b              ; code $36 : moyenne (agent_voix_max (moyenne))
        dcb.w   $c9, 0
VOIX_MAX:
        dc.l    VOIX_26, VOIX_27, VOIX_28, VOIX_29
VOIX_26:   ; 64 n° de voix PSP ($200|n) -> commande (table de sons du pack pl26, lue par 0x60BC)
        dc.w    64
        dc.w    CMD_VOIX_26_E00    ; n° 0
        dc.w    CMD_VOIX_26_E01    ; n° 1
        dc.w    CMD_VOIX_26_E02    ; n° 2
        dc.w    CMD_VOIX_26_E03    ; n° 3
        dc.w    0                  ; n° 4 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_26_E09    ; n° 5
        dc.w    CMD_VOIX_26_E19    ; n° 6
        dc.w    CMD_VOIX_26_E08    ; n° 7
        dc.w    CMD_VOIX_26_E17    ; n° 8
        dc.w    CMD_VOIX_26_E18    ; n° 9
        dc.w    CMD_VOIX_26_E19    ; n° 10
        dc.w    CMD_VOIX_26_E20    ; n° 11
        dc.w    CMD_VOIX_26_E21    ; n° 12
        dc.w    CMD_VOIX_26_E22    ; n° 13
        dc.w    CMD_VOIX_26_E23    ; n° 14
        dc.w    CMD_VOIX_26_E24    ; n° 15
        dc.w    CMD_VOIX_26_E13    ; n° 16
        dc.w    CMD_VOIX_26_E14    ; n° 17
        dc.w    CMD_VOIX_26_E15    ; n° 18
        dc.w    CMD_VOIX_26_E27    ; n° 19 : bruit de bâton (v27, confirmé à l'écoute), pas une voix
        dc.w    CMD_VOIX_26_E27    ; n° 20 : bruit de bâton (v27, confirmé à l'écoute), pas une voix
        dc.w    CMD_VOIX_26_E27    ; n° 21 : bruit de bâton (v27, confirmé à l'écoute), pas une voix
        dc.w    CMD_VOIX_26_E28    ; n° 22 : échantillon 28 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    0                  ; n° 23 : autre banque (type 1026, n° 0) — à apparier
        dc.w    CMD_VOIX_26_E13    ; n° 24
        dc.w    CMD_VOIX_26_E14    ; n° 25
        dc.w    CMD_VOIX_26_E15    ; n° 26
        dc.w    CMD_VOIX_26_E10    ; n° 27
        dc.w    CMD_VOIX_26_E11    ; n° 28
        dc.w    CMD_VOIX_26_E07    ; n° 29
        dc.w    CMD_VOIX_26_E04    ; n° 30
        dc.w    CMD_VOIX_26_E05    ; n° 31
        dc.w    CMD_VOIX_26_E10    ; n° 32
        dc.w    CMD_VOIX_26_E12    ; n° 33
        dc.w    CMD_VOIX_26_E06    ; n° 34
        dc.w    CMD_VOIX_26_E06    ; n° 35
        dc.w    CMD_VOIX_26_E05    ; n° 36
        dc.w    CMD_VOIX_26_E16    ; n° 37
        dc.w    CMD_VOIX_26_E26    ; n° 38
        dc.w    0                  ; n° 39 : muet (aussi sur PSP)
        dc.w    0                  ; n° 40 : muet (aussi sur PSP)
        dc.w    0                  ; n° 41 : muet (aussi sur PSP)
        dc.w    0                  ; n° 42 : muet (aussi sur PSP)
        dc.w    0                  ; n° 43 : muet (aussi sur PSP)
        dc.w    0                  ; n° 44 : muet (aussi sur PSP)
        dc.w    0                  ; n° 45 : muet (aussi sur PSP)
        dc.w    0                  ; n° 46 : muet (aussi sur PSP)
        dc.w    0                  ; n° 47 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_26_E10    ; n° 48
        dc.w    CMD_VOIX_26_E10    ; n° 49
        dc.w    0                  ; n° 50 : muet (aussi sur PSP)
        dc.w    0                  ; n° 51 : muet (aussi sur PSP)
        dc.w    0                  ; n° 52 : muet (aussi sur PSP)
        dc.w    0                  ; n° 53 : muet (aussi sur PSP)
        dc.w    0                  ; n° 54 : muet (aussi sur PSP)
        dc.w    0                  ; n° 55 : muet (aussi sur PSP)
        dc.w    0                  ; n° 56 : muet (aussi sur PSP)
        dc.w    0                  ; n° 57 : muet (aussi sur PSP)
        dc.w    0                  ; n° 58 : muet (aussi sur PSP)
        dc.w    0                  ; n° 59 : muet (aussi sur PSP)
        dc.w    0                  ; n° 60 : muet (aussi sur PSP)
        dc.w    0                  ; n° 61 : muet (aussi sur PSP)
        dc.w    0                  ; n° 62 : muet (aussi sur PSP)
        dc.w    0                  ; n° 63 : muet (aussi sur PSP)
VOIX_27:   ; 64 n° de voix PSP ($200|n) -> commande (table de sons du pack pl27, lue par 0x60BC)
        dc.w    64
        dc.w    CMD_VOIX_27_E00    ; n° 0
        dc.w    CMD_VOIX_27_E01    ; n° 1
        dc.w    CMD_VOIX_27_E02    ; n° 2
        dc.w    CMD_VOIX_27_E03    ; n° 3
        dc.w    0                  ; n° 4 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_27_E09    ; n° 5
        dc.w    0                  ; n° 6 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_27_E08    ; n° 7
        dc.w    CMD_VOIX_27_E22    ; n° 8
        dc.w    CMD_VOIX_27_E23    ; n° 9
        dc.w    CMD_VOIX_27_E24    ; n° 10
        dc.w    CMD_VOIX_27_E25    ; n° 11
        dc.w    CMD_VOIX_27_E26    ; n° 12
        dc.w    CMD_VOIX_27_E27    ; n° 13
        dc.w    CMD_VOIX_27_E28    ; n° 14
        dc.w    CMD_VOIX_27_E29    ; n° 15
        dc.w    CMD_VOIX_27_E30    ; n° 16
        dc.w    CMD_VOIX_27_E31    ; n° 17
        dc.w    CMD_VOIX_27_E32    ; n° 18
        dc.w    CMD_VOIX_27_E33    ; n° 19
        dc.w    CMD_VOIX_27_E34    ; n° 20
        dc.w    CMD_VOIX_27_E35    ; n° 21
        dc.w    CMD_VOIX_27_E36    ; n° 22
        dc.w    CMD_VOIX_27_E37    ; n° 23
        dc.w    CMD_VOIX_27_E38    ; n° 24
        dc.w    CMD_VOIX_27_E38    ; n° 25
        dc.w    CMD_VOIX_27_E38    ; n° 26
        dc.w    CMD_VOIX_27_E13    ; n° 27
        dc.w    0                  ; n° 28 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_27_E15    ; n° 29
        dc.w    CMD_VOIX_27_E16    ; n° 30
        dc.w    CMD_VOIX_27_E17    ; n° 31
        dc.w    CMD_VOIX_27_E18    ; n° 32
        dc.w    CMD_VOIX_27_E19    ; n° 33
        dc.w    CMD_VOIX_27_E04    ; n° 34
        dc.w    CMD_VOIX_27_E05    ; n° 35
        dc.w    CMD_VOIX_27_E06    ; n° 36
        dc.w    CMD_VOIX_27_E07    ; n° 37
        dc.w    0                  ; n° 38 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_27_E12    ; n° 39
        dc.w    CMD_VOIX_27_E11    ; n° 40
        dc.w    CMD_VOIX_27_E08    ; n° 41
        dc.w    0                  ; n° 42 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_27_E06    ; n° 43
        dc.w    CMD_VOIX_27_E06    ; n° 44
        dc.w    CMD_VOIX_27_E21    ; n° 45
        dc.w    CMD_VOIX_27_E39    ; n° 46
        dc.w    CMD_VOIX_27_E40    ; n° 47
        dc.w    CMD_VOIX_27_E11    ; n° 48
        dc.w    CMD_VOIX_27_E11    ; n° 49
        dc.w    CMD_VOIX_27_E41    ; n° 50
        dc.w    0                  ; n° 51 : muet (aussi sur PSP)
        dc.w    0                  ; n° 52 : muet (aussi sur PSP)
        dc.w    0                  ; n° 53 : muet (aussi sur PSP)
        dc.w    0                  ; n° 54 : muet (aussi sur PSP)
        dc.w    0                  ; n° 55 : muet (aussi sur PSP)
        dc.w    0                  ; n° 56 : muet (aussi sur PSP)
        dc.w    0                  ; n° 57 : muet (aussi sur PSP)
        dc.w    0                  ; n° 58 : muet (aussi sur PSP)
        dc.w    0                  ; n° 59 : muet (aussi sur PSP)
        dc.w    0                  ; n° 60 : muet (aussi sur PSP)
        dc.w    0                  ; n° 61 : muet (aussi sur PSP)
        dc.w    0                  ; n° 62 : muet (aussi sur PSP)
        dc.w    0                  ; n° 63 : muet (aussi sur PSP)
VOIX_28:   ; 64 n° de voix PSP ($200|n) -> commande (table de sons du pack pl28, lue par 0x60BC)
        dc.w    64
        dc.w    CMD_VOIX_28_E00    ; n° 0
        dc.w    CMD_VOIX_28_E01    ; n° 1
        dc.w    CMD_VOIX_28_E02    ; n° 2
        dc.w    CMD_VOIX_28_E03    ; n° 3
        dc.w    0                  ; n° 4 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_28_E09    ; n° 5
        dc.w    0                  ; n° 6 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_28_E08    ; n° 7
        dc.w    CMD_VOIX_28_E21    ; n° 8
        dc.w    CMD_VOIX_28_E22    ; n° 9
        dc.w    CMD_VOIX_28_E18    ; n° 10
        dc.w    CMD_VOIX_28_E26    ; n° 11 : échantillon 26 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E29    ; n° 12 : échantillon 29 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E27    ; n° 13 : échantillon 27 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E30    ; n° 14 : échantillon 30 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E35    ; n° 15 : échantillon 35 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E33    ; n° 16 : échantillon 33 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E36    ; n° 17 : échantillon 36 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E28    ; n° 18 : échantillon 28 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E31    ; n° 19 : échantillon 31 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E37    ; n° 20
        dc.w    CMD_VOIX_28_E38    ; n° 21
        dc.w    CMD_VOIX_28_E12    ; n° 22
        dc.w    CMD_VOIX_28_E13    ; n° 23
        dc.w    CMD_VOIX_28_E14    ; n° 24
        dc.w    CMD_VOIX_28_E32    ; n° 25 : échantillon 32 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E34    ; n° 26 : échantillon 34 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E15    ; n° 27
        dc.w    CMD_VOIX_28_E16    ; n° 28
        dc.w    CMD_VOIX_28_E17    ; n° 29
        dc.w    CMD_VOIX_28_E31    ; n° 30 : échantillon 31 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E28    ; n° 31 : échantillon 28 du perso (entrée PSP de type $400, octet de banque 1 : sa propre banque, échantillon inutilisé par les entrées de type 0)
        dc.w    CMD_VOIX_28_E10    ; n° 32
        dc.w    CMD_VOIX_28_E08    ; n° 33
        dc.w    CMD_VOIX_28_E11    ; n° 34
        dc.w    CMD_VOIX_28_E04    ; n° 35
        dc.w    CMD_VOIX_28_E05    ; n° 36
        dc.w    CMD_VOIX_28_E06    ; n° 37
        dc.w    CMD_VOIX_28_E07    ; n° 38
        dc.w    0                  ; n° 39 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_28_E05    ; n° 40
        dc.w    CMD_VOIX_28_E07    ; n° 41
        dc.w    CMD_VOIX_28_E05    ; n° 42
        dc.w    CMD_VOIX_28_E19    ; n° 43
        dc.w    CMD_VOIX_28_E20    ; n° 44
        dc.w    0                  ; n° 45 : muet (aussi sur PSP)
        dc.w    0                  ; n° 46 : muet (aussi sur PSP)
        dc.w    0                  ; n° 47 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_28_E10    ; n° 48
        dc.w    CMD_VOIX_28_E10    ; n° 49
        dc.w    0                  ; n° 50 : muet (aussi sur PSP)
        dc.w    0                  ; n° 51 : muet (aussi sur PSP)
        dc.w    0                  ; n° 52 : muet (aussi sur PSP)
        dc.w    0                  ; n° 53 : muet (aussi sur PSP)
        dc.w    0                  ; n° 54 : muet (aussi sur PSP)
        dc.w    0                  ; n° 55 : muet (aussi sur PSP)
        dc.w    0                  ; n° 56 : muet (aussi sur PSP)
        dc.w    0                  ; n° 57 : muet (aussi sur PSP)
        dc.w    0                  ; n° 58 : muet (aussi sur PSP)
        dc.w    0                  ; n° 59 : muet (aussi sur PSP)
        dc.w    0                  ; n° 60 : muet (aussi sur PSP)
        dc.w    0                  ; n° 61 : muet (aussi sur PSP)
        dc.w    0                  ; n° 62 : muet (aussi sur PSP)
        dc.w    0                  ; n° 63 : muet (aussi sur PSP)
VOIX_29:   ; 64 n° de voix PSP ($200|n) -> commande (table de sons du pack pl29, lue par 0x60BC)
        dc.w    64
        dc.w    CMD_VOIX_29_E00    ; n° 0
        dc.w    CMD_VOIX_29_E04    ; n° 1
        dc.w    CMD_VOIX_29_E04    ; n° 2
        dc.w    CMD_VOIX_29_E05    ; n° 3
        dc.w    0                  ; n° 4 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_29_E05    ; n° 5
        dc.w    0                  ; n° 6 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_29_E04    ; n° 7
        dc.w    CMD_VOIX_29_E01    ; n° 8
        dc.w    CMD_VOIX_29_E02    ; n° 9
        dc.w    CMD_VOIX_29_E08    ; n° 10
        dc.w    0                  ; n° 11 : muet (aussi sur PSP)
        dc.w    0                  ; n° 12 : muet (aussi sur PSP)
        dc.w    0                  ; n° 13 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_29_E04    ; n° 14
        dc.w    0                  ; n° 15 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_29_E09    ; n° 16
        dc.w    CMD_VOIX_29_E20    ; n° 17
        dc.w    CMD_VOIX_29_E21    ; n° 18
        dc.w    CMD_VOIX_29_E22    ; n° 19
        dc.w    0                  ; n° 20 : muet (aussi sur PSP)
        dc.w    0                  ; n° 21 : muet (aussi sur PSP)
        dc.w    0                  ; n° 22 : muet (aussi sur PSP)
        dc.w    0                  ; n° 23 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_29_E07    ; n° 24
        dc.w    CMD_VOIX_29_E08    ; n° 25
        dc.w    CMD_VOIX_29_E09    ; n° 26
        dc.w    CMD_VOIX_29_E10    ; n° 27
        dc.w    CMD_VOIX_29_E11    ; n° 28
        dc.w    CMD_VOIX_29_E12    ; n° 29
        dc.w    CMD_VOIX_29_E13    ; n° 30
        dc.w    CMD_VOIX_29_E14    ; n° 31
        dc.w    CMD_VOIX_29_E15    ; n° 32
        dc.w    CMD_VOIX_29_E16    ; n° 33
        dc.w    CMD_VOIX_29_E17    ; n° 34
        dc.w    CMD_VOIX_29_E18    ; n° 35
        dc.w    CMD_VOIX_29_E23    ; n° 36
        dc.w    CMD_VOIX_29_E24    ; n° 37
        dc.w    CMD_VOIX_29_E25    ; n° 38
        dc.w    0                  ; n° 39 : muet (aussi sur PSP)
        dc.w    CMD_VOIX_29_A_095  ; n° 40 : voix propre d'Ingrid A_095 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_096  ; n° 41 : voix propre d'Ingrid A_096 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_097  ; n° 42 : voix propre d'Ingrid A_097 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_098  ; n° 43 : voix propre d'Ingrid A_098 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_099  ; n° 44 : voix propre d'Ingrid A_099 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_100  ; n° 45 : voix propre d'Ingrid A_100 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_101  ; n° 46 : voix propre d'Ingrid A_101 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_102  ; n° 47 : voix propre d'Ingrid A_102 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_E08    ; n° 48
        dc.w    CMD_VOIX_29_E08    ; n° 49
        dc.w    CMD_VOIX_29_A_103  ; n° 50 : voix propre d'Ingrid A_103 (se_mid banque A, agent_son_max)
        dc.w    CMD_VOIX_29_A_103  ; n° 51 : voix propre d'Ingrid A_103 (se_mid banque A, agent_son_max)
        dc.w    0                  ; n° 52 : autre banque (type 1026, n° 256) — à apparier
        dc.w    0                  ; n° 53 : autre banque (type 2, n° 0) — à apparier
        dc.w    0                  ; n° 54 : autre banque (type 1026, n° 256) — à apparier
        dc.w    0                  ; n° 55 : autre banque (type 2, n° 0) — à apparier
        dc.w    CMD_VOIX_29_E26    ; n° 56
        dc.w    CMD_VOIX_29_E27    ; n° 57
        dc.w    0                  ; n° 58 : muet (aussi sur PSP)
        dc.w    0                  ; n° 59 : muet (aussi sur PSP)
        dc.w    0                  ; n° 60 : muet (aussi sur PSP)
        dc.w    0                  ; n° 61 : muet (aussi sur PSP)
        dc.w    0                  ; n° 62 : muet (aussi sur PSP)
        dc.w    0                  ; n° 63 : muet (aussi sur PSP)

; ---- psp_1c622c / psp_1c3db4 / psp_1c3e60 (Ingrid, RIPOSTE des contres 13 / 14 : sous-états 2 et 3 de la garde 0x1C3CA0),
; écrites à la main (2026-10-17, défaut relevé au banc : drapeau CONTRE_DECLENCHE jamais remis, aucune riposte). La
; traduction automatique appelait psp_1c622c SANS son argument (n° du joueur saisi, PSP +0x348 = $3D4, posé par
; psp_1c3ec0) puis prenait D0, écrasé entre-temps par psp_cfec8 / psp_1c60a0, pour le pointeur de la victime : écritures
; en mémoire basse ($14(0)…). Ici la victime est cherchée puis gardée sur la pile.
; psp_1c622c(n) : joueur dont le n° ($101 ; PSP 0x151) vaut n, parmi les 4 de la table PSP 0x213F88 = arcade $FF8400 + $400 k.
psp_1c622c:
        movem.l d1/a0, -(sp)
        movea.l #$ff8400, a0          ; pointeur d'objet (structure joueur 0)
        moveq   #3, d1
.k:     cmp.b   $101(a0), d0
        beq.s   .ok
        lea     $400(a0), a0
        dbra    d1, .k
        moveq   #0, d0
        bra.s   .x
.ok:    move.l  a0, d0
.x:     movem.l (sp)+, d1/a0
        rts

; sous-état 2 (PSP 0x1C3DB4) : tient la victime (Y + 8 si $34), puis à $35 : sous-état suivant, saisie (fiche $A0 + $4C0,
; psp_66ae8) et coup direct n° 38 (psp_672dc) ; sinon victime $5F (PSP 0x7F) = $7F.
psp_1c3db4:
        move.l  $3d4(a6), d0
        andi.l  #$ff, d0
        bsr     psp_1c622c
        move.l  d0, -(sp)            ; victime
        bsr     psp_cfec8
        bsr     psp_1c60a0
        movea.l (sp), a0          ; pointeur d'objet
        tst.b   $34(a6)
        beq.s   .a
        addq.w  #8, $14(a0)
.a:     tst.b   $35(a6)
        beq.s   .b
        addq.b  #2, $7(a6)
        clr.b   $25d(a0)
        move.l  a0, d0
        move.l  $a0(a6), d1
        addi.l  #$4c0, d1
        bsr     psp_66ae8
        move.l  (sp), d0
        moveq   #38, d1
        bsr     psp_672dc
        movea.l (sp)+, a0          ; pointeur d'objet
        clr.b   $5f(a0)
        rts
.b:     movea.l (sp)+, a0          ; pointeur d'objet
        move.b  #$7f, $5f(a0)
        rts

; sous-état 3 (PSP 0x1C3E60) : fin d'animation -> victime $5D (PSP 0x7D) = 0, retour à la garde ($2BAF2 = PSP 0x6069C).
psp_1c3e60:
        move.l  $3d4(a6), d0
        andi.l  #$ff, d0
        bsr     psp_1c622c
        move.l  d0, -(sp)
        bsr     psp_cfec8
        bsr     psp_1c60a0
        movea.l (sp)+, a0          ; pointeur d'objet
        tst.b   $33(a6)
        bpl.s   .x
        clr.b   $5d(a0)
        jmp     $2baf2.l
.x:     rts
