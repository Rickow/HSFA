#!/usr/bin/env python3
"""build_cave.py — CAVE DATA-DRIVEN cross-stage, TIMING v7 (2026-09-06).

Leçon de la décomp de v7 (qui RENDAIT) : il ne faut PAS appeler le loader au hook par-frame ni
forcer 0xb674f8. Il faut :
  1. POSER le descripteur slot-11 (le loader NATIF charge le package à 0x1580000 pendant l'écran
     de chargement — AVANT le staging bank->VRAM et la composition de fin de load).
  2. GATER la copie sur le MAGIC présent ([0x1580000]=='CSTG') = on copie pendant le load.
  3. EFFACER le magic après copie (one-shot par cycle de load ; le slot-11 le recharge au load
     suivant -> re-copie automatique à chaque nouveau stage).
  4. NE PAS toucher 0xb674f8 : la composition naturelle de fin de load compose depuis nos données.

Le cave lit la table de copies CSTG {dst,size,src} et applique chaque copie (générique, tout stage).
Hook 0x1d0750 (rendu BG, tourne aussi pendant l'écran de chargement). Sortie : pnach + binaire emu.
"""
import struct

R = {'zero':0,'v0':2,'a0':4,'a1':5,'a2':6,'a3':7,
     't0':8,'t1':9,'t2':10,'t3':11,'t4':12,'t5':13,'t6':14,'t7':15,'t9':25,
     's0':16,'sp':29,'ra':31}
BASE = 0x1c0400
code = []; lblpos = {}; fixes = []

# slot-11 descripteur (desc v8 = 0x1dbc30 ; slot 11 = +0x98 = 0x1dbcc8)
SLOT11   = 0x1dbcc8
FILE_ID  = 527            # AFS index du package CSTG dans l'ISO
PKG_DST  = 0x01580000
CSTG_MAGIC = 0x47545343   # 'CSTG'

def emit(*ws): code.extend(ws)
def L(n): lblpos[n] = len(code)
def lui(rt,i): return 0x3c000000|(R[rt]<<16)|(i&0xffff)
def ori(rt,rs,i): return 0x34000000|(R[rs]<<21)|(R[rt]<<16)|(i&0xffff)
def addiu(rt,rs,i): return 0x24000000|(R[rs]<<21)|(R[rt]<<16)|(i&0xffff)
def addu(rd,rs,rt): return (R[rs]<<21)|(R[rt]<<16)|(R[rd]<<11)|0x21
def lw(rt,o,rs): return 0x8c000000|(R[rs]<<21)|(R[rt]<<16)|(o&0xffff)
def sw(rt,o,rs): return 0xac000000|(R[rs]<<21)|(R[rt]<<16)|(o&0xffff)
NOP = 0
def li(rt,val):
    emit(lui(rt,(val>>16)&0xffff)); emit(ori(rt,rt,val&0xffff))
def B(op,rs,rt,name):
    fixes.append((len(code),op,rs,rt,name)); emit(0,NOP)

# ---- prologue : instr déplacée + sauvegarde ----
emit(addiu('sp','sp',-0x70))                          # 0x1d0750 déplacée
emit(addiu('sp','sp',-0x20))
emit(sw('ra',0,'sp'), sw('a0',4,'sp'), sw('a1',8,'sp'),
     sw('a2',0xc,'sp'), sw('a3',0x10,'sp'), sw('s0',0x14,'sp'))

# ---- GATE CONTEXTE : n'agir QUE quand un stage se build (0xb84178==8). Sinon EXIT.
#      (évite tout au boot/memcard/menus : pas de pose slot-11 -> pas de load prématuré -> pas de hang) ----
li('t0', 0x00b84178)
emit(0x94000000|(R['t0']<<21)|(R['t4']<<16)|0)        # lhu t4, 0(t0)
li('t5', 8)
B('bne','t4','t5','EXIT')

# ---- POSE slot-11 (idempotent) : {u16 type=3, u16 file, u32 dst, u32 stg=0} ----
li('t0', SLOT11)
li('t4', (FILE_ID << 16) | 3)          # word0 = file<<16 | type(3=load brut)
emit(sw('t4', 0, 't0'))
li('t4', PKG_DST)
emit(sw('t4', 4, 't0'))                # word1 = dst
emit(sw('zero', 8, 't0'))              # word2 = stg = 0

# ---- GATE : magic 'CSTG' présent à 0x1580000 ? sinon EXIT (package pas encore chargé) ----
li('s0', PKG_DST); emit(lw('t4',0,'s0')); li('t5', CSTG_MAGIC)
B('bne','t4','t5','EXIT')

# ---- boucle de copies (table CSTG) ----
emit(lw('t2',8,'s0'), addu('t2','t2','s0'))           # t2 = table = PKG + [PKG+8]
emit(lw('t3',0xc,'s0'), addu('t3','t3','s0'))         # t3 = data  = PKG + [PKG+0xc]
emit(lw('t1',4,'s0'))                                  # t1 = n_copies
L('CP')
B('blez','t1','zero','CPEND')
emit(lw('a2',0,'t2'))                                  # dst_ee
emit(lw('a3',4,'t2'))                                  # size
emit(lw('t6',8,'t2'), addu('a1','t3','t6'))            # src = data + src_off
L('MC')
emit(lw('t9',0,'a1'), sw('t9',0,'a2'),
     addiu('a1','a1',4), addiu('a2','a2',4), addiu('a3','a3',-4))
B('bgtz','a3','zero','MC')
emit(addiu('t2','t2',12), addiu('t1','t1',-1))
B('b','zero','zero','CP')
L('CPEND')
# ---- EFFACER le magic = one-shot par cycle de load (le slot-11 le recharge au load suivant) ----
emit(sw('zero',0,'s0'))
# NB : PAS de 0xb674f8 — la composition naturelle de fin de load compose depuis nos données.
L('EXIT')
emit(lw('ra',0,'sp'), lw('a0',4,'sp'), lw('a1',8,'sp'),
     lw('a2',0xc,'sp'), lw('a3',0x10,'sp'), lw('s0',0x14,'sp'))
emit(addiu('sp','sp',0x20))
emit(0x08000000|((0x1d0758>>2)&0x3ffffff), NOP)        # j 0x1d0758 ; nop

# ---- résolution des branches ----
OPC = {'beq':0x04,'bne':0x05,'blez':0x06,'bgtz':0x07}
for pos,op,rs,rt,name in fixes:
    off = (lblpos[name]-pos-1) & 0xffff
    if op == 'b':
        code[pos] = (0x04<<26)|off
    else:
        code[pos] = (OPC[op]<<26)|(R[rs]<<21)|(R[rt]<<16)|off

assert (here_end := BASE+len(code)*4) <= 0x1c1000, hex(here_end)

if __name__ == "__main__":
    binout = bytes(b for w in code for b in struct.pack("<I", w))
    open("<workspace>/tmp_hdd/cave_cstg.bin","wb").write(binout)
    lines = [f"patch=1,EE,{BASE+i*4:08x},word,{w:08x}" for i,w in enumerate(code)]
    lines.append(f"patch=1,EE,001d0750,word,{0x08000000|((BASE>>2)&0x3ffffff):08x}")  # hook
    open("<workspace>/tmp_hdd/cave_cstg_lines.txt","w").write("\n".join(lines)+"\n")
    print(f"cave TIMING-v7 : {len(code)} instr, fin @{hex(BASE+len(code)*4)}")
    print("slot-11 posé + gate magic CSTG + clear magic + PAS de b674f8")
    print("bin -> tmp_hdd/cave_cstg.bin ; pnach -> tmp_hdd/cave_cstg_lines.txt")
