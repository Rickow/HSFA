; symboles vers des données ARCADE / UPPER et réglages d'intégration, définis par HSFA (outils de relogement) —
; valeurs pour Upper (rapport HSFA agent_banque_1a)
EXPLO_PAS equ $2E565C           ; 1er pas (8 o) de l'explosion $2E50A0 n° 5 — adresse ARCADE sfa3ud, à reloger (Upper)
EXPLO_1A equ $0000              ; $1A de l'explosion : banque commune (arcade $6000 -> Upper emplacement 0 ; Hyper : e545)
BANQUE_1A_DECOR_FIN equ $8000   ; $1A des frames FD.. : emplacement 4 (graphismes de fin, $C0BC), comme Upper sous-types >= $80
; drapeau « palette propre » des acteurs de fin (invités dessinés avec les frames du perso MAX) — rosette_donnees.py
ACTEUR_PALPROPRE_OCTET equ 4    ; octet de l'enregistrement de 32 o (bits 5-7 = $18 arcade ; bits 0-4 jamais posés)
ACTEUR_PALPROPRE_BIT equ 0      ; bit dans cet octet
ACTEUR_PALPROPRE_CHAMP equ $18  ; champ de l'objet où le générateur recopie l'octet (bit 0)
; contres MAX (contres_max.s, 2026-10-17) — valeurs de l'IMAGE Upper v149 relevées par agent_integration_max (à confirmer
; à chaque construction : l'image bouge) :
COUP_NORMAL equ $003FBE         ; gestionnaire « pas de contre » d'Upper, appelé par les gestionnaires 4-9 : v151 (relevé max23 de l'intégration, qui le relève désormais dans l'image native ; v149 : $23A3C, devenu un tirage aléatoire en v151)
CONTRE_DECLENCHE equ -$7454     ; = $8BAC non signé : mot A5 « contre déclenché » (MOVE.W #1,$8BAC(A5) des gestionnaires d'Upper ; PSP octet 0x87F50D)
