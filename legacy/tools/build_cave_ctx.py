#!/usr/bin/env python3
"""build_cave_ctx.py — CAVE « méthode v7 » pour Chun-Li (2026-09-26).

Mécanisme capturé sur le v7 qui rend :
  - le package est chargé par l'ISO (mécanisme baké) à 0x1580000 ;
  - on copie pool+liste SCR3 UNE FOIS par cycle de load (gate = magic CSTG, puis on l'efface) ;
  - on REPOINTE [0x1dc2f4]/+4/+8 (= contexte de couche) vers NOTRE ctx CHAQUE frame
    (le build du jeu les réécrit sans arrêt) -> le drawer lit nos graphismes de tuiles.

Aucun slot-11 posé (donc aucun risque de hang au boot) : c'est l'ISO qui charge.
Hook 0x1d0750. Repoint gaté sur ring SCR3 [0xba8000]==0x63d (= notre stage composé).
"""
import struct

R = {'zero':0,'v0':2,'a0':4,'a1':5,'a2':6,'a3':7,
     't0':8,'t1':9,'t2':10,'t3':11,'t4':12,'t5':13,'t6':14,'t9':25,
     's0':16,'sp':29,'ra':31}
BASE = 0x1c0400
CTX_RAM  = 0x01590000
PKG_RAM  = 0x01580000
CSTG     = 0x47545343
CTXPTR   = 0x001dc2f4        # = [0x1dc078]+0x44 ; +4/+8 = classes suivantes
RING3    = 0x00ba8000
RING3_T0 = 0x063d            # 1re tuile de notre ring SCR3 Chun-Li

code = []; lblpos = {}; fixes = []
def emit(*ws): code.extend(ws)
def L(n): lblpos[n] = len(code)
def lui(rt,i): return 0x3c000000|(R[rt]<<16)|(i&0xffff)
def ori(rt,rs,i): return 0x34000000|(R[rs]<<21)|(R[rt]<<16)|(i&0xffff)
def addiu(rt,rs,i): return 0x24000000|(R[rs]<<21)|(R[rt]<<16)|(i&0xffff)
def addu(rd,rs,rt): return (R[rs]<<21)|(R[rt]<<16)|(R[rd]<<11)|0x21
def lw(rt,o,rs): return 0x8c000000|(R[rs]<<21)|(R[rt]<<16)|(o&0xffff)
def lhu(rt,o,rs): return 0x94000000|(R[rs]<<21)|(R[rt]<<16)|(o&0xffff)
def sw(rt,o,rs): return 0xac000000|(R[rs]<<21)|(R[rt]<<16)|(o&0xffff)
NOP = 0
def li(rt,val):
    emit(lui(rt,(val>>16)&0xffff)); emit(ori(rt,rt,val&0xffff))
def B(op,rs,rt,name):
    fixes.append((len(code),op,rs,rt,name)); emit(0,NOP)

# ---- prologue ----
emit(addiu('sp','sp',-0x70))                          # instruction déplacée de 0x1d0750
emit(addiu('sp','sp',-0x20))
emit(sw('ra',0,'sp'), sw('a0',4,'sp'), sw('a1',8,'sp'),
     sw('a2',0xc,'sp'), sw('a3',0x10,'sp'), sw('s0',0x14,'sp'))

# ---- REPOINT du contexte de couche, CHAQUE frame, gaté sur notre ring SCR3 ----
li('t0', RING3); emit(lhu('t4',0,'t0'))
li('t5', RING3_T0)
B('bne','t4','t5','NOREPOINT')
li('t0', CTXPTR); li('t4', CTX_RAM)
emit(sw('t4',0,'t0'), sw('t4',4,'t0'), sw('t4',8,'t0'))
L('NOREPOINT')

# ---- COPIES one-shot : gate sur le magic CSTG du package chargé par l'ISO ----
li('s0', PKG_RAM); emit(lw('t4',0,'s0')); li('t5', CSTG)
B('bne','t4','t5','EXIT')
emit(lw('t2',8,'s0'), addu('t2','t2','s0'))           # table = PKG + [PKG+8]
emit(lw('t3',0xc,'s0'), addu('t3','t3','s0'))         # data  = PKG + [PKG+0xc]
emit(lw('t1',4,'s0'))                                  # n_copies
L('CP')
B('blez','t1','zero','CPEND')
emit(lw('a2',0,'t2'))                                  # dst
emit(lw('a3',4,'t2'))                                  # size
emit(lw('t6',8,'t2'), addu('a1','t3','t6'))            # src
L('MC')
emit(lw('t9',0,'a1'), sw('t9',0,'a2'),
     addiu('a1','a1',4), addiu('a2','a2',4), addiu('a3','a3',-4))
B('bgtz','a3','zero','MC')
emit(addiu('t2','t2',12), addiu('t1','t1',-1))
B('b','zero','zero','CP')
L('CPEND')
emit(sw('zero',0,'s0'))                                # efface le magic = one-shot par load
L('EXIT')
emit(lw('ra',0,'sp'), lw('a0',4,'sp'), lw('a1',8,'sp'),
     lw('a2',0xc,'sp'), lw('a3',0x10,'sp'), lw('s0',0x14,'sp'))
emit(addiu('sp','sp',0x20))
emit(0x08000000|((0x1d0758>>2)&0x3ffffff), NOP)        # j 0x1d0758

OPC = {'beq':0x04,'bne':0x05,'blez':0x06,'bgtz':0x07}
for pos,op,rs,rt,name in fixes:
    off = (lblpos[name]-pos-1) & 0xffff
    code[pos] = (0x04<<26)|off if op=='b' else (OPC[op]<<26)|(R[rs]<<21)|(R[rt]<<16)|off

assert (end := BASE+len(code)*4) <= 0x1c1000, hex(end)

if __name__ == "__main__":
    open("<workspace>/tmp_hdd/cave_ctx.bin","wb").write(
        bytes(b for w in code for b in struct.pack("<I", w)))
    lines = [f"patch=1,EE,{BASE+i*4:08x},word,{w:08x}" for i,w in enumerate(code)]
    lines.append(f"patch=1,EE,001d0750,word,{0x08000000|((BASE>>2)&0x3ffffff):08x}")
    open("<workspace>/tmp_hdd/cave_ctx_lines.txt","w").write("\n".join(lines)+"\n")
    print(f"cave CTX : {len(code)} instr, fin @{hex(end)} ; repoint {hex(CTXPTR)} -> {hex(CTX_RAM)}")
