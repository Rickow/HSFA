#!/usr/bin/env python3
"""Décodage MIPS R5900 minimal par champs de bits (rapide, sans capstone).
Suffisant pour reconnaître les idiomes du recompilateur 68K->MIPS de l'Anthology."""
import struct

REG = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
       's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']

LOADSTORE = {0x20:'lb',0x21:'lh',0x22:'lwl',0x23:'lw',0x24:'lbu',0x25:'lhu',0x26:'lwr',
             0x28:'sb',0x29:'sh',0x2a:'swl',0x2b:'sw',0x2e:'swr',0x37:'ld',0x3f:'sd'}
IMM = {0x08:'addi',0x09:'addiu',0x0a:'slti',0x0b:'sltiu',0x0c:'andi',0x0d:'ori',
       0x0e:'xori',0x0f:'lui'}
BR  = {0x04:'beq',0x05:'bne',0x06:'blez',0x07:'bgtz',0x14:'beql',0x15:'bnel'}
SPECIAL = {0x00:'sll',0x02:'srl',0x03:'sra',0x04:'sllv',0x06:'srlv',0x07:'srav',
           0x08:'jr',0x09:'jalr',0x10:'mfhi',0x12:'mflo',0x18:'mult',0x19:'multu',
           0x1a:'div',0x1b:'divu',0x20:'add',0x21:'addu',0x22:'sub',0x23:'subu',
           0x24:'and',0x25:'or',0x26:'xor',0x27:'nor',0x2a:'slt',0x2b:'sltu',
           0x2d:'addu',   # (HANDOFF §122) DADDU : copie de registre du recompilateur (toujours avec zero) = addu sur 32 bits
           0x38:'dsll',0x3a:'dsrl',0x3b:'dsra',0x3c:'dsll32',0x3e:'dsrl32',0x3f:'dsra32'}

class Ins:
    __slots__=('va','w','op','rs','rt','rd','sa','fn','imm','simm','tgt','m')
    def __init__(s, va, w):
        s.va=va; s.w=w
        s.op=w>>26; s.rs=(w>>21)&0x1f; s.rt=(w>>16)&0x1f
        s.rd=(w>>11)&0x1f; s.sa=(w>>6)&0x1f; s.fn=w&0x3f
        s.imm=w&0xffff; s.simm=s.imm-0x10000 if s.imm&0x8000 else s.imm
        s.tgt=(w&0x3ffffff)<<2
        if s.op==0: s.m=SPECIAL.get(s.fn,'?sp%02x'%s.fn)
        elif s.op==2: s.m='j'
        elif s.op==3: s.m='jal'
        elif s.op in LOADSTORE: s.m=LOADSTORE[s.op]
        elif s.op in IMM: s.m=IMM[s.op]
        elif s.op in BR: s.m=BR[s.op]
        elif s.op==1: s.m={0:'bltz',1:'bgez',16:'bltzal',17:'bgezal'}.get(s.rt,'regimm')
        elif s.op==0x1e: s.m='lq'
        elif s.op==0x1f: s.m='sq'
        else: s.m='?op%02x'%s.op
    def __repr__(s):
        R=REG
        if s.m in LOADSTORE.values(): return "%s %s,%d(%s)"%(s.m,R[s.rt],s.simm,R[s.rs])
        if s.m=='lui': return "lui %s,%#x"%(R[s.rt],s.imm)
        if s.m in ('addiu','addi','ori','andi','xori','slti','sltiu'):
            return "%s %s,%s,%#x"%(s.m,R[s.rt],R[s.rs],s.imm)
        if s.m in ('j','jal'): return "%s %#x"%(s.m,s.tgt)
        if s.m in BR.values(): return "%s %s,%s,%+d"%(s.m,R[s.rs],R[s.rt],s.simm*4+4)
        if s.m in ('sll','srl','sra','dsll','dsrl','dsra','dsll32','dsrl32','dsra32'):
            return "%s %s,%s,%d"%(s.m,R[s.rd],R[s.rt],s.sa)
        if s.m in ('jr','jalr'): return "%s %s"%(s.m,R[s.rs])
        # famille REGIMM (op=1) : bltz/bgez rs,offset (rt code le type, pas un registre)
        if s.op==1: return "%s %s,%+d"%(s.m,R[s.rs],s.simm*4+4)
        if s.m in ('mult','multu','div','divu'): return "%s %s,%s"%(s.m,R[s.rs],R[s.rt])
        if s.m in ('mfhi','mflo'): return "%s %s"%(s.m,R[s.rd])
        return "%s %s,%s,%s"%(s.m,R[s.rd],R[s.rs],R[s.rt])

def decode(buf, start=0, end=None):
    end = len(buf) if end is None else end
    for a in range(start, end-3, 4):
        yield Ins(a, struct.unpack_from('<I', buf, a)[0])

# ---------------------------------------------------------------------------
# BORNES DE LA ZONE DE CODE RECOMPILE, lues dans l'EN-TETE du module ro3 :
#   mot 0 = magic 'MWo3'   mot 2 = 0x1f0000 (base de chargement)
#   mot 3 = 0x393c40 (TAILLE DU CODE)
# Verifie par la densite de la signature 'lui rX,0x7000' (acces aux registres 68K
# emules) : premiere a 0xac, derniere a 0x393c1c, dernier 'jr ra' a 0x393c4c.
# ATTENTION : jusqu'a la session du 2026-09-26 tous les outils scannaient
# 0xb000..0x30b000, soit 84 % seulement du code. Toujours utiliser ces constantes.
# ⚠️ La zone de code contient DEUX processeurs recompiles, sans entrelacement :
#   Z80 (son QSound)  : fichier 0x20..0x22b00, banc de registres en 0x7000_1000..0x103f
#                       (8 644 acces ; octets appaires, adressage (IX+d)). INUTILE a
#                       retraduire : la ROM Z80 d'origine est deja verbatim dans l'Anthology.
#   68000 (le jeu)    : fichier 0x22b00..0x393c40, banc de registres 0x7000_1100..0x1160
#                       (200 774 acces). Premier acces 68K 0x22b0c, dernier Z80 0x22ae8.
Z80_0, Z80_1 = 0x20, 0x22b00
CODE0 = 0x22b00       # debut du code 68K recompile
CODE1 = 0x393c40      # taille du code, d'apres l'en-tete
def code_bounds(buf):
    import struct
    if buf[:4]==b'MWo3':                     # fin du code d'apres l'en-tete ; debut = 68K
        return CODE0, struct.unpack_from('<I',buf,12)[0]
    return CODE0, CODE1
