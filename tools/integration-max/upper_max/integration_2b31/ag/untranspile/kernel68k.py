#!/usr/bin/env python3
"""NOYAU DE TACHES 68K pour le jeu traduit (HANDOFF §61) : remplace les FILS D'EXECUTION PS2 du portage
par un noyau cooperatif calque sur celui de Capcom (ROM $1110..$13FC, TRAP #0-#3), sur la table des taches
DU PORTAGE (A5+$8184, 16 x $20 ; etat = octet +1 dans la vue memoire cps2 ; tache courante A5+$8388).
Mode superviseur, une pile par tache hors de la RAM du jeu. Genere du code machine (mini-assembleur),
verifie par desassemblage capstone.

Transposition des appels systeme PS2 (cibles 'externes' du jeu traduit) :
  CreateThread  0x1033E0 -> CREER   (D0 = emplacement*$20, A0 = entree : l'API de TRAP #0)
  SleepThread   0x103500 -> CEDER   (depuis une tache : sauve registres + pile, retour a l'ordonnanceur)
  ExitThread    0x103410, ExitDeleteThread 0x103420 -> FINIR   (numeros d'appel lus dans SLUS_213.17, §80)
  TerminateThread 0x103430 (fil d'une AUTRE tache, deja marquee libre par le portage), WakeupThread 0x103510,
  StartThread 0x103400, DeleteThread 0x1033F0, 0x10D870, 0x104720 -> RTS
"""
import struct

class Asm:
    def __init__(s, org): s.org = org; s.w = []; s.labels = {}; s.fix = []
    def here(s): return s.org + 2 * len(s.w)
    def L(s, name): s.labels[name] = s.here()
    def emit(s, *ws): s.w += [x & 0xffff for x in ws]
    def abs_l(s, a): s.emit(a >> 16, a)
    def bra(s, cond, name):                    # Bcc.W vers une etiquette (cond : 0 BRA, 6 BNE, 7 BEQ, 5 BCS, 4 BCC)
        s.emit(0x6000 | (cond << 8)); s.fix.append((len(s.w), name)); s.emit(0)
    def jsr(s, a): s.emit(0x4eb9); s.abs_l(a)
    def jmp(s, a): s.emit(0x4ef9); s.abs_l(a)
    def done(s):
        for pos, name in s.fix:
            s.w[pos] = (s.labels[name] - (s.org + 2 * pos)) & 0xffff
        return struct.pack('>%dH' % len(s.w), *s.w)

# memoire du noyau (hors RAM du jeu ; essai MAME : RAM annexe CPS2 $660000-$663FFF)
STK0 = 0x660000; STKSZ = 0x380           # piles des taches : $660000 + (n+1)*$380 (jusqu'a $663800)
SIDE = 0x663800                            # 16 x 8 : +0 pile sauvee (0 = jamais lancee), +4 entree
SCHEDSP = 0x663880; CURSLOT = 0x663884; FLAG = 0x663888   # pile de l'ordonnanceur : $664000 vers le bas
EXCMARK = 0x6638F0          # (HANDOFF §80) PC d'un talon d'exception interrompu par l'IRQ2 (diag.py)
TCB = 0x8184; CURTCB = 0x8388               # deplacements A5 du portage (table des taches, tache courante)
MOVEM_ALL = 0x7fff                          # D0-D7/A0-A6 (masque pour -(SP) : inverse -> 0xfffe)

def build(org, vbl_addr, n_slots=16, code_conv=None):
    """code_conv : entree 'convertir A0' des adresses de code PS2 (§76) appliquee a l'entree des taches"""
    a = Asm(org)
    # --- CREER : D0 = emplacement*$20, A0 = entree ---------------------------------------------
    a.L('creer')
    a.emit(0x48e7, 0xc040)                  # MOVEM.L D0-D1/A1,-(SP)
    a.emit(0xe448)                          # LSR.W #2,D0          (-> emplacement*8)
    a.emit(0x43f9); a.abs_l(SIDE)           # LEA SIDE,A1
    a.emit(0x42b1, 0x0000)                  # CLR.L 0(A1,D0.W)     (jamais lancee)
    a.emit(0x2388, 0x0004)                  # MOVE.L A0,4(A1,D0.W) (entree)
    a.emit(0x4cdf, 0x0203)                  # MOVEM.L (SP)+,D0-D1/A1
    a.emit(0x4e75)                          # RTS
    # --- CEDER : depuis une tache ---------------------------------------------------------------
    a.L('ceder')
    a.emit(0x48e7, 0xfffe)                  # MOVEM.L D0-D7/A0-A6,-(SP)
    a.emit(0x3039); a.abs_l(CURSLOT)        # MOVE.W CURSLOT,D0
    a.emit(0xe748)                          # LSL.W #3,D0
    a.emit(0x41f9); a.abs_l(SIDE)           # LEA SIDE,A0
    a.emit(0x218f, 0x0000)                  # MOVE.L SP,0(A0,D0.W)
    a.L('retour_ordo')
    a.emit(0x2e79); a.abs_l(SCHEDSP)        # MOVEA.L SCHEDSP,SP
    a.emit(0x4cdf, MOVEM_ALL)               # MOVEM.L (SP)+,D0-D7/A0-A6
    a.emit(0x4e75)                          # RTS  (retour dans l'ordonnanceur, apres son JSR lancer)
    # --- FINIR : la tache se termine ------------------------------------------------------------
    a.L('finir')
    a.emit(0x3039); a.abs_l(CURSLOT)        # MOVE.W CURSLOT,D0
    a.emit(0xe748)                          # LSL.W #3,D0
    a.emit(0x41f9); a.abs_l(SIDE)           # LEA SIDE,A0
    a.emit(0x72ff)                          # MOVEQ #-1,D1
    a.emit(0x2181, 0x0000)                  # MOVE.L D1,0(A0,D0.W)  (-1 = fil TERMINE : comme sur PS2, il ne
    a.bra(0, 'retour_ordo')                 #  tourne plus tant qu'on ne le recree pas ; l'etat du jeu est intact)
    # --- LANCER : D0 = emplacement ; lance ou reprend la tache ----------------------------------
    a.L('lancer')
    a.emit(0x48e7, 0xfffe)                  # MOVEM.L D0-D7/A0-A6,-(SP)
    a.emit(0x23cf); a.abs_l(SCHEDSP)        # MOVE.L SP,SCHEDSP
    a.emit(0x33c0); a.abs_l(CURSLOT)        # MOVE.W D0,CURSLOT
    a.emit(0x41ed, TCB)                     # LEA $8184(A5),A0
    a.emit(0x3200)                          # MOVE.W D0,D1
    a.emit(0xeb49)                          # LSL.W #5,D1
    a.emit(0xd0c1)                          # ADDA.W D1,A0
    a.emit(0x2408)                          # MOVE.L A0,D2
    a.emit(0x4842)                          # SWAP D2               (long en memoire : moities echangees, recette cps2)
    a.emit(0x2b42, CURTCB)                  # MOVE.L D2,$8388(A5)   (tache courante)
    a.emit(0xe748)                          # LSL.W #3,D0
    a.emit(0x43f9); a.abs_l(SIDE)           # LEA SIDE,A1
    a.emit(0x2231, 0x0000)                  # MOVE.L 0(A1,D0.W),D1
    a.bra(7, 'premier')                     # BEQ premier lancement
    a.emit(0x5281)                          # ADDQ.L #1,D1
    a.bra(7, 'retour_ordo')                 # -1 : fil termine -> rien a faire
    a.emit(0x5381)                          # SUBQ.L #1,D1
    a.emit(0x2e41)                          # MOVEA.L D1,SP
    a.emit(0x4cdf, MOVEM_ALL)               # MOVEM.L (SP)+,D0-D7/A0-A6
    a.emit(0x4e75)                          # RTS  (reprise apres son JSR ceder)
    a.L('premier')
    a.emit(0x2471, 0x0004)                  # MOVEA.L 4(A1,D0.W),A2 (entree)
    if code_conv is not None:               # entree = adresse de code PS2 -> la notre
        a.emit(0xc14a); a.jsr(code_conv); a.emit(0xc14a)   # EXG A0,A2 ; JSR convertir A0 ; EXG A0,A2
    a.emit(0x3639); a.abs_l(CURSLOT)        # MOVE.W CURSLOT,D3
    a.emit(0x5243)                          # ADDQ.W #1,D3
    a.emit(0xc6fc, STKSZ)                   # MULU #STKSZ,D3
    a.emit(0x0683); a.abs_l(STK0)           # ADDI.L #$660000,D3
    a.emit(0x2e43)                          # MOVEA.L D3,SP
    a.emit(0x2f3c); a.abs_l(a.labels['finir'])   # MOVE.L #finir,-(SP) (si l'entree fait RTS : fin de tache)
    a.emit(0x4ed2)                          # JMP (A2)
    # --- ORDONNANCEUR (premier plan, calque sur ROM $1110) --------------------------------------
    a.L('ordo')
    a.L('boucle')
    a.emit(0x3c39); a.abs_l(FLAG)           # MOVE.W FLAG,D6   (image de reference)
    a.emit(0x7000)                          # MOVEQ #0,D0
    a.L('scan')
    a.emit(0xba79); a.abs_l(FLAG)           # CMP.W FLAG,D5 ... (remplace ci-dessous)
    a.w[-3:] = [0x3a39, FLAG >> 16, FLAG & 0xffff]   # MOVE.W FLAG,D5
    a.emit(0xba46)                          # CMP.W D6,D5
    a.bra(6, 'boucle')                      # BNE : image arrivee -> on recommence
    a.emit(0x41ed, TCB)                     # LEA $8184(A5),A0
    a.emit(0x3200)                          # MOVE.W D0,D1
    a.emit(0xeb49)                          # LSL.W #5,D1
    a.emit(0x1430, 0x1001)                  # MOVE.B 1(A0,D1.W),D2 (etat, octet +1 en vue cps2)
    a.emit(0x0c02, 0x0004)                  # CMPI.B #4,D2
    a.bra(5, 'suivant')                     # BCS : pas prete
    a.bra(0x1, 'x') if False else None
    a.emit(0x4eb9); a.fix.append((len(a.w), 'lancer_hi')); a.emit(0, 0)   # JSR lancer (abs, corrige plus bas)
    a.L('suivant')
    a.emit(0x5240)                          # ADDQ.W #1,D0
    a.emit(0x0c40, n_slots)                 # CMPI.W #16,D0
    a.bra(5, 'scan')                        # BCS scan
    a.L('attente')
    a.emit(0x3a39); a.abs_l(FLAG)           # MOVE.W FLAG,D5
    a.emit(0xba46)                          # CMP.W D6,D5
    a.bra(7, 'attente')                     # BEQ attente
    a.bra(0, 'boucle')
    # --- IRQ2 : balayage vertical porte + drapeau d'image ---------------------------------------
    a.L('irq2')
    # (HANDOFF §80) l'IRQ2 interrompt-elle un talon d'exception ($A00-$A80 : BRA.S *) ? -> marqueur pour diag.py
    # (l'IRQ continuant de tourner, le PC vu en fin d'image n'est plus dans le talon). RTE rend le SR.
    a.emit(0x0caf, 0x0000, 0x0a00, 0x0002, 0x6512)          # CMPI.L #$A00,2(SP) ; BCS.S +18
    a.emit(0x0caf, 0x0000, 0x0a80, 0x0002, 0x6408)          # CMPI.L #$A80,2(SP) ; BCC.S +8
    a.emit(0x23ef, 0x0002); a.abs_l(EXCMARK)                # MOVE.L 2(SP),EXCMARK
    a.emit(0x48e7, 0xfffe)                  # MOVEM.L D0-D7/A0-A6,-(SP)
    a.emit(0x4bf9, 0x00ff, 0x8000)          # LEA $FF8000,A5
    a.jsr(vbl_addr)
    a.emit(0x5279); a.abs_l(FLAG)           # ADDQ.W #1,FLAG
    a.emit(0x4cdf, MOVEM_ALL)               # MOVEM.L (SP)+,D0-D7/A0-A6
    a.emit(0x4e73)                          # RTE
    # JSR lancer : adresse absolue
    fixes = []
    for pos, name in a.fix:
        if name == 'lancer_hi':
            v = a.labels['lancer']; a.w[pos] = v >> 16; a.w[pos + 1] = v & 0xffff
        else: fixes.append((pos, name))
    a.fix = fixes
    code = a.done()
    return code, a.labels

def build_conv(org, ranges):
    """CONVERSION DES POINTEURS PS2 A L'EXECUTION (HANDOFF §63). ranges : [(debut, fin, ajout)] tries,
    CONTIGUS ou non (un trou = ajout 0). Rend (code, {n: adresse de la routine 'convertir An'}).
    Chaque routine preserve les drapeaux (MOVE SR/CCR) et tous les registres sauf An."""
    a = Asm(org); entry = {}
    lo = ranges[0][0]; hi = max(r1 for r0, r1, add in ranges)
    for n in range(7):                       # talons A0..A6 : An <-> A0 autour du coeur
        entry[n] = a.here()
        a.emit(0x40e7)                       # MOVE SR,-(SP)
        # (HANDOFF §104) cas « inchange » les plus frequents traites dans le talon, sans appel ni EXG
        a.emit(0xb1fc | (n << 9)); a.abs_l(lo); a.bra(5, 'sortie%d' % n)   # CMPA.L #debut,An ; BCS
        a.emit(0xb1fc | (n << 9)); a.abs_l(hi); a.bra(4, 'sortie%d' % n)   # CMPA.L #fin,An ; BCC
        if n: a.emit(0xc148 | n)             # EXG A0,An
        a.bra(1, 'arbre')                    # BSR.W arbre (cond 1 = BSR)
        if n: a.emit(0xc148 | n)
        a.L('sortie%d' % n)
        a.emit(0x44df, 0x4e75)               # MOVE (SP)+,CCR ; RTS
    a.L('coeur')
    # (HANDOFF §104) recherche DICHOTOMIQUE au lieu de la chaine de comparaisons (jusqu'a 13 CMPA.L) ; acces
    # directs pour les deux cas les plus frequents : sous la premiere plage, et au-dela de la derniere ($FFxxxx).
    a.emit(0xb1fc); a.abs_l(lo); a.bra(5, 'hors')        # CMPA.L #debut,A0 ; BCS hors
    a.emit(0xb1fc); a.abs_l(hi); a.bra(4, 'hors')        # CMPA.L #fin,A0 ; BCC hors
    a.L('arbre')
    iv = []                                              # intervalles contigus [lo, hi) -> ajout (0 = trou)
    prev = lo
    for r0, r1, add in sorted(ranges):
        if r0 > prev: iv.append((prev, r0, 0))
        iv.append((r0, r1, add)); prev = r1
    m = []                                               # fusion des voisins de meme ajout
    for x in iv:
        if m and m[-1][2] == x[2] and m[-1][1] == x[0]: m[-1] = (m[-1][0], x[1], x[2])
        else: m.append(x)
    cnt = [0]
    def arbre(lst):
        if len(lst) == 1:
            if lst[0][2]: a.emit(0xd1fc); a.abs_l(lst[0][2] & 0xffffffff)   # ADDA.L #ajout,A0
            a.emit(0x4e75); return
        k = len(lst) // 2; cnt[0] += 1; g = 'g%d' % cnt[0]
        a.emit(0xb1fc); a.abs_l(lst[k][0]); a.bra(5, g)  # CMPA.L #borne,A0 ; BCS gauche
        arbre(lst[k:])
        a.L(g); arbre(lst[:k])
    arbre(m)
    a.L('hors'); a.emit(0x4e75)
    return a.done(), entry

HASH_BITS = 14                              # (HANDOFF §98) table de hachage : 16 384 entrees de 8 octets (128 Ko)
def code_hash(k): return ((k >> 2) ^ (k >> 8)) & ((1 << HASH_BITS) - 1)
def build_hash(pairs):
    """table de hachage a sondage lineaire : (cle PS2, adresse 68K) ; cle 0 = vide"""
    M = 1 << HASH_BITS; t = [None] * M
    for k, v in pairs:
        i = code_hash(k)
        while t[i] is not None: i = (i + 1) & (M - 1)
        t[i] = (k, v)
    return b''.join(struct.pack('>II', *(e if e else (0, 0))) for e in t)

def build_code_conv(org, table, n, lo, hi, hash_addr=None):
    """CONVERSION DES ADRESSES DE CODE PS2 A L'USAGE (HANDOFF §76) : avant JSR/JMP (An), An = adresse
    PS2 d'un debut de fonction [lo, hi) -> notre adresse, par dichotomie dans 'table' (n paires triees
    (adresse PS2, adresse 68K), 8 octets). Hors plage (deja une adresse 68K) ou absente : inchange.
    Preserve drapeaux et registres sauf An. Rend (code, {n: entree 'convertir An'})."""
    a = Asm(org); entry = {}
    for r in range(7):
        entry[r] = a.here()
        a.emit(0x40e7)                       # MOVE SR,-(SP)
        # (HANDOFF §104) hors plage (deja une adresse 68K) : traite dans le talon, sans appel ni EXG
        a.emit(0xb1fc | (r << 9)); a.abs_l(lo); a.bra(5, 'sortie%d' % r)   # CMPA.L #lo,Ar ; BCS
        a.emit(0xb1fc | (r << 9)); a.abs_l(hi); a.bra(4, 'sortie%d' % r)   # CMPA.L #hi,Ar ; BCC
        if r: a.emit(0xc148 | r)             # EXG A0,Ar
        a.bra(1, 'coeur')                    # BSR.W coeur
        if r: a.emit(0xc148 | r)
        a.L('sortie%d' % r)
        a.emit(0x44df, 0x4e75)               # MOVE (SP)+,CCR ; RTS
    a.L('coeur')
    if hash_addr is not None:
        # (HANDOFF §98) HACHAGE au lieu de la dichotomie (~13 tours, 14 % du temps processeur en combat) :
        # indice = ((k >> 2) ^ (k >> 8)) & $3FFF, sondage lineaire, ~2,4 sondages en moyenne
        a.emit(0x48e7, 0x3040)               # MOVEM.L D2-D3/A1,-(SP)
        a.emit(0x2408, 0x2602)               # MOVE.L A0,D2 ; MOVE.L D2,D3
        a.emit(0xec8b, 0xb583, 0xe48b)       # LSR.L #6,D3 ; EOR.L D2,D3 ; LSR.L #2,D3
        a.emit(0x0283); a.abs_l((1 << HASH_BITS) - 1)     # ANDI.L #$3FFF,D3
        a.emit(0xe78b)                       # LSL.L #3,D3
        a.emit(0x43f9); a.abs_l(hash_addr)   # LEA table,A1
        a.L('h_boucle')
        a.emit(0xb4b1, 0x3800); a.bra(7, 'h_trouve')      # CMP.L 0(A1,D3.L),D2 ; BEQ trouve
        a.emit(0x4ab1, 0x3800); a.bra(7, 'h_absent')      # TST.L 0(A1,D3.L) ; BEQ absent
        a.emit(0x5083)                       # ADDQ.L #8,D3
        a.emit(0x0283); a.abs_l((8 << HASH_BITS) - 1)     # ANDI.L #$1FFFF,D3
        a.bra(0, 'h_boucle')
        a.L('h_trouve')
        a.emit(0x2071, 0x3804)               # MOVEA.L 4(A1,D3.L),A0
        a.L('h_absent')
        a.emit(0x4cdf, 0x020c)               # MOVEM.L (SP)+,D2-D3/A1  (A1 = bit 9)
        a.emit(0x4e75)                       # RTS
    a.emit(0x48e7, 0xf040)                   # MOVEM.L D0-D3/A1,-(SP)
    a.emit(0x43f9); a.abs_l(table)           # LEA table,A1
    a.emit(0x2408)                           # MOVE.L A0,D2          (cle)
    a.emit(0x7000)                           # MOVEQ #0,D0           (bas)
    a.emit(0x223c); a.abs_l(n)               # MOVE.L #n,D1          (haut, exclu)
    a.L('boucle')
    a.emit(0xb280); a.bra(3, 'absent')       # CMP.L D0,D1 ; BLS absent
    a.emit(0x2600, 0xd681, 0xe28b)           # MOVE.L D0,D3 ; ADD.L D1,D3 ; LSR.L #1,D3   (milieu)
    a.emit(0xe78b)                           # LSL.L #3,D3
    a.emit(0xb4b1, 0x3800)                   # CMP.L 0(A1,D3.L),D2
    a.bra(7, 'trouve'); a.bra(5, 'gauche')   # BEQ trouve ; BCS gauche (cle < entree)
    a.emit(0xe68b, 0x5283, 0x2003)           # LSR.L #3,D3 ; ADDQ.L #1,D3 ; MOVE.L D3,D0
    a.bra(0, 'boucle')
    a.L('gauche')
    a.emit(0xe68b, 0x2203)                   # LSR.L #3,D3 ; MOVE.L D3,D1
    a.bra(0, 'boucle')
    a.L('trouve')
    a.emit(0x2071, 0x3804)                   # MOVEA.L 4(A1,D3.L),A0
    a.L('absent')
    a.emit(0x4cdf, 0x020f)                   # MOVEM.L (SP)+,D0-D3/A1
    a.L('fin'); a.emit(0x4e75)
    return a.done(), entry

def disasm(code, org):
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_000)
    return ["%06x  %-9s %s" % (i.address, i.mnemonic, i.op_str) for i in md.disasm(code, org)]

if __name__ == "__main__":
    code, lab = build(0xB00, 0x2c16)
    print({k: hex(v) for k, v in lab.items()})
    print("\n".join(disasm(code, 0xB00)))
