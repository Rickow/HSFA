#!/usr/bin/env python3
"""genere.py DOSSIER : génère le corpus synthétique (toutes les instructions 68000 × tailles × modes d'adressage,
valeurs limites des optimisations, branchements à toutes les distances limites) en plusieurs fichiers .s"""
import os
import sys

D = sys.argv[1] if len(sys.argv) > 1 else "synth"
os.makedirs(D, exist_ok=True)

IMMS = ["0", "1", "2", "7", "8", "9", "-1", "-2", "-8", "-9", "127", "128", "-128", "-129", "200", "254", "255",
        "256", "$7fff", "$8000", "-$8000", "-$8001", "$ffff", "$10000", "$12345", "$7f0000", "$800000", "$ff0000",
        "$fffeffff", "$ff80ffff", "$ff7fffff", "$ffff0000", "$ffffff00", "$fffffff0", "$ffffffff", "$80000000",
        "LOIN", "PRES", "ZERO", "UN", "LOIN-PRES", "*-*+3"]
EAS_SRC = ["d3", "a2", "(a1)", "(a4)+", "-(a5)", "4(a3)", "-2(a6)", "0(a2)", "(0,a2)", "ZERO(a2)", "$7ffe(a0)",
           "-$8000(a1)", "(6,a0)", "6(a0,d1.w)", "-4(a2,a3.l)", "0(a1,d2)", "(a1,d2.l)", "127(a0,a1)", "-128(a6,d7.w)",
           "$1234.w", "$12345678.l", "$1234", "$8000", "$ffff8000", "$ffff7fff", "-2", "$7fff", "$3A2000", "PRES",
           "LOIN", "PRES.l", "PRES.w", "(PRES).l", "(PRES)", "PRES(pc)", "(PRES,pc)", "PRES(pc,d0.w)", "*+20(pc)",
           "PRES+$9000", "ARRIERE", "ARRIERE(pc)", "AVANT_LOIN", "#5", "#$1234", "#-1", "#LOIN"]
EAS_DST = ["d3", "a2", "(a1)", "(a4)+", "-(a5)", "4(a3)", "0(a2)", "$7ffe(a0)", "6(a0,d1.w)", "0(a1,d2)", "$1234.w",
           "$12345678.l", "$1234", "$8000", "PRES", "LOIN", "PRES(pc)", "#5", "sp", "-(sp)"]
SIZES = ["", ".b", ".w", ".l"]


def entete(org):
    return ["        org     $%X" % org, "ZERO    equ 0", "UN      equ 1", "LOIN    equ $D00000",
            "ARRIERE: nop", "        dcb.w 8,$4e71"]


def queue():
    return ["        dcb.b   $40,0", "PRES:   dc.w $1234", "        dcb.b   $40,0", "        dcb.b   $9000,0",
            "AVANT_LOIN: nop"]


def fichier(nom, org, corps):
    with open(os.path.join(D, nom), "w") as f:
        f.write("\n".join(entete(org) + corps + queue()) + "\n")


# 1. instructions à deux opérandes : source quelconque -> Dn/An, Dn/imm -> destination quelconque
DEUX = ["move", "movea", "add", "adda", "addi", "addq", "sub", "suba", "subi", "subq", "and", "andi", "or", "ori",
        "eor", "eori", "cmp", "cmpa", "cmpi"]
corps = []
for mn in DEUX:
    for sz in SIZES:
        for s in EAS_SRC:
            for d in ("d0", "a1"):
                corps.append("        %s%s %s,%s" % (mn, sz, s, d))
        for s in ("d4", "a3", "#5"):
            for d in EAS_DST:
                corps.append("        %s%s %s,%s" % (mn, sz, s, d))
fichier("s01_deux.s", 0x3A0000, corps)

# 2. immédiats (valeurs limites des optimisations) vers Dn, An et mémoire
corps = []
for mn in DEUX + ["moveq"]:
    for sz in SIZES:
        for v in IMMS:
            for d in ("d2", "a3", "(a0)", "6(a1)", "PRES"):
                corps.append("        %s%s #%s,%s" % (mn, sz, v, d))
fichier("s02_imm.s", 0x3A0000, corps)

# 3. instructions à un opérande
UN = ["clr", "neg", "negx", "not", "tst", "nbcd", "tas", "pea", "jmp", "jsr", "swap", "ext", "st", "sf", "shi", "sls",
      "scc", "shs", "scs", "slo", "sne", "seq", "svc", "svs", "spl", "smi", "sge", "slt", "sgt", "sle", "asl", "asr",
      "lsl", "lsr", "rol", "ror", "roxl", "roxr", "unlk", "move"]
corps = []
for mn in UN:
    for sz in SIZES:
        for e in EAS_SRC + ["sr", "ccr", "usp", "a6", "d0"]:
            corps.append("        %s%s %s" % (mn, sz, e))
fichier("s03_un.s", 0x3A0000, corps)

# 4. décalages, bits, mult/div, divers
corps = []
for mn in ["asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr"]:
    for sz in SIZES:
        for c in ["#1", "#2", "#8", "#0", "#9", "d1"]:
            corps.append("        %s%s %s,d5" % (mn, sz, c))
for mn in ["btst", "bchg", "bclr", "bset"]:
    for sz in SIZES:
        for c in ["#0", "#7", "#9", "#31", "#33", "d2"]:
            for e in EAS_DST + ["PRES(pc,d1.w)", "#3"]:
                corps.append("        %s%s %s,%s" % (mn, sz, c, e))
for mn in ["muls", "mulu", "divs", "divu", "chk"]:
    for sz in SIZES:
        for e in EAS_SRC:
            corps.append("        %s%s %s,d6" % (mn, sz, e))
for mn in ["lea"]:
    for e in EAS_SRC + ["4(a5)", "-4(a5)", "8(a5)", "9(a5)", "-8(a5)", "-9(a5)", "0(a5)", "(a5)", "$8000(a5)",
                        "-$8001(a5)", "$8000(a1)", "0", "ZERO", "$10"]:
        corps.append("        lea %s,a5" % e)
for e in EAS_SRC:
    corps.append("        move %s,sr" % e)
    corps.append("        move %s,ccr" % e)
    corps.append("        move sr,%s" % e)
for x in ["d0,d1", "a0,a1", "d2,a3", "a3,d2", "d0,d0"]:
    corps += ["        exg %s" % x, "        exg.l %s" % x]
for x in ["abcd", "sbcd", "addx", "subx"]:
    for sz in SIZES:
        corps += ["        %s%s d1,d2" % (x, sz), "        %s%s -(a1),-(a2)" % (x, sz)]
for sz in SIZES:
    corps += ["        cmpm%s (a0)+,(a1)+" % sz, "        movep%s 4(a0),d1" % sz, "        movep%s d1,4(a0)" % sz,
              "        movep%s d1,(a0)" % sz]
corps += ["        link a6,#-8", "        link a5,#$7fff", "        unlk a6", "        trap #0", "        trap #15",
          "        stop #$2700", "        nop", "        rts", "        rte", "        rtr", "        reset",
          "        trapv", "        illegal", "        moveq #$ff,d0", "        moveq #-128,d7", "        moveq.l #5,d1",
          "        move.l a0,usp", "        move usp,a1", "        andi #$fe,ccr", "        ori #$700,sr",
          "        eori.b #1,ccr", "        andi.w #$f8ff,sr", "        ori.b #4,ccr", "        eori #$2000,sr"]
for sz in SIZES:
    for regs in ["d0", "a0", "d0/a0", "d0-d7/a0-a6", "a3-a5", "d1/d3/d5", "d0-d1", "a6"]:
        for e in ["-(sp)", "(a0)", "4(a1)", "6(a2,d0.w)", "$1234", "PRES", "LOIN"]:
            corps.append("        movem%s %s,%s" % (sz, regs, e))
        for e in ["(sp)+", "(a0)", "4(a1)", "6(a2,d0.w)", "$1234", "PRES", "PRES(pc)", "LOIN"]:
            corps.append("        movem%s %s,%s" % (sz, e, regs))
fichier("s04_divers.s", 0x3A0000, corps)

# 5. mêmes familles à une adresse basse (étiquettes en absolu court)
corps = []
for mn in ["move", "lea", "jmp", "jsr", "pea", "add", "cmp", "tst", "btst", "movem"]:
    for e in ["PRES", "ARRIERE", "LOIN", "$1234", "$8000", "$7ff0", "AVANT_LOIN", "PRES+$7000"]:
        if mn in ("jmp", "jsr", "pea", "tst"):
            corps.append("        %s %s" % (mn, e))
        elif mn == "lea":
            corps.append("        lea %s,a0" % e)
        elif mn == "btst":
            corps.append("        btst #1,%s" % e)
        elif mn == "movem":
            corps.append("        movem.l %s,d0/d1" % e)
        else:
            corps.append("        %s.w %s,d0" % (mn, e))
fichier("s05_bas.s", 0x1000, corps)

# 6. branchements : distances limites en avant / en arrière, explicites et libres, vers l'instruction suivante
corps = []
k = 0
for mn in ["bra", "bsr", "beq", "bne", "bhi", "bls", "bcc", "bcs", "bvc", "bvs", "bpl", "bmi", "bge", "blt", "bgt",
           "ble", "bhs", "blo", "jmp", "jsr", "dbra", "dbf", "dbne", "dbt"]:
    for sz in (["", ".s", ".w", ".b"] if mn[0] == "b" else [""]):
        for dist in [0, 2, 4, 120, 124, 126, 128, 130, 132, 32760, 32762, 32764, 32766, 32768, 32770]:
            k += 1
            pre = "d0," if mn.startswith("db") else ""
            corps += ["V%d:     %s%s %sW%d" % (k, mn, sz, pre, k), "        dcb.b %d,0" % dist, "W%d:     nop" % k]
            k += 1
            corps += ["W%d:     nop" % k, "        dcb.b %d,0" % dist, "V%d:     %s%s %sW%d" % (k, mn, sz, pre, k)]
fichier("s06_branches.s", 0x3A0000, corps)

# 7. chaînes de branchements interdépendants (relâchement en plusieurs passes, points fixes ambigus)
corps = []
for n in range(1, 40):
    corps += ["C%d_0:  bra C%d_F" % (n, n)]
    for j in range(n):
        corps += ["C%d_%d:  beq C%d_%d" % (n, j + 1, n, j),
                  "        dcb.b %d,0" % ((120 // max(1, n // 4) - 2 * (j % 3)) & ~1)]
    corps += ["C%d_M:  bra C%d_0" % (n, n), "        bne C%d_F" % n, "C%d_F:  nop" % n,
              "        bsr C%d_0" % n, "        bra C%d_N" % n, "C%d_N:" % n, "        jmp C%d_M" % n]
fichier("s07_chaines.s", 0x3A0000, corps)

# 8. données et directives
corps = ["        dc.b 1,2,$ff,-128,255,'A','xy'", "        dc.w 1,-1,$ffff,-32768,$ffff8000,PRES", "        even",
         "        dc.l 1,-1,PRES,PRES-ARRIERE,$ffffffff", "        dc.b 3", "        dc.w 4", "        dc.l 5",
         "        dcb.b 3,$aa", "        dcb.w 2,$1234", "        dcb.l 2,PRES", "        dc.b 1", "        ds.w 2",
         "        ds.l 1", "        ds.b 5", "        cnop 0,4", "        dc.b 9", "        cnop 0,8",
         "        dc.b 9,9", "        cnop 2,4", "        dc.b 9", "        even", "        dc.b 1", "        nop",
         "        dc.w (PRES)&$ffff,((PRES)>>16)&$ffff", "        dc.w 1+2*3, 2*3<<1, 1!2, 5~1, 7-2-1, 100/10/2, -7/2",
         "        dc.w -7%2, 2<3, 3=3, ~1, !0, !5, 1-2*3, (1-2)*3, 1+2<<3, 2*3&1, $10>>2, -16>>2, 5//3",
         "        dc.l ((PRES>>16)&$ffff)|((PRES&$ffff)<<16)", "X1      equ PRES+4", "        dc.l X1, X2",
         "X2      equ X1*2", "        dc.l 'ABCD'", "        dc.w 'AB'", "        dc.b \"q\"",
         "        ifnd NON_DEFINI", "        dc.b $11", "        endif", "        ifd PRES", "        dc.b $22",
         "        endif", "        ifnd ZERO", "        dc.b $33", "        endif", "        even"]
fichier("s08_donnees.s", 0x3A0000, corps)
print("corpus synthétique :", D)

# 6b. branchements isolés : chaque essai dans sa propre section (org), sans interaction entre essais
corps = []
k = 0
org = 0x400000
for mn in ["bra", "bsr", "beq", "bgt", "jmp", "jsr", "dbra"]:
    for sz in (["", ".s", ".w"] if mn[0] == "b" else [""]):
        for dist in [0, 2, 4, 120, 124, 126, 128, 130, 32760, 32762, 32764, 32766, 32768]:
            for sens in (0, 1):
                k += 1
                pre = "d0," if mn.startswith("db") else ""
                corps.append("        org     $%X" % org)
                org += 0x10000
                if sens == 0:
                    corps += ["V%d:     %s%s %sW%d" % (k, mn, sz, pre, k), "        dcb.b %d,0" % dist, "W%d:     nop" % k]
                else:
                    corps += ["W%d:     nop" % k, "        dcb.b %d,0" % dist, "V%d:     %s%s %sW%d" % (k, mn, sz, pre, k)]
with open(os.path.join(D, "s06b_branches_isoles.s"), "w") as f:
    f.write("\n".join(corps) + "\n")

# 9. autres directives (=, set, align, blk, if/else, ifeq/ifne/ifgt/iflt, chaînes)
with open(os.path.join(D, "s09_directives.s"), "w") as f:
    f.write("""        org $1000
X       = 5
Y       set 3
Y       set Y+1
        dc.b X,Y
        dc.b 1
        align 2
        dc.b 2
        blk.w 2,$abcd
        if X>4
        dc.b $11
        else
        dc.b $22
        endif
        ifeq X-5
        dc.b $33
        endif
        ifne X-5
        dc.b $44
        endif
        ifgt X
        dc.b $55
        endif
        iflt X
        dc.b $66
        endif
Z:      dc.w *-Z, Z
        dc.l "AB"
        dc.b 'it''s'
        dc.b 1
        align 3
        dc.b 2
        even
        nop
        align 4
        nop
loc:    nop
.a:     bra.s .b
.b:     bra.s .a
loc2:   bra.s .a
.a:     nop
fin$:   nop
        bra fin$
""")
