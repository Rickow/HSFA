#!/usr/bin/env python3
"""Decodeur de LONGUEUR 68000 + extraction des vrais operandes.

But : ne plus confondre opcodes et constantes. On parcourt le code instruction par
instruction, et on ne retient que les mots d'extension qui sont reellement des
IMMEDIATS ou des DEPLACEMENTS.

Ne desassemble pas : calcule la taille et classe les mots d'extension.
Renvoie None si l'opcode est inconnu (= on a desynchronise, il faut resynchroniser).
"""
import struct

# nb de mots d'extension d'un mode d'adressage effectif
def ea_words(mode, reg, size):
    if mode in (0,1,2,3,4): return 0          # Dn, An, (An), (An)+, -(An)
    if mode == 5: return 1                     # (d16,An)
    if mode == 6: return 1                     # (d8,An,Xn) - extension breve
    if mode == 7:
        if reg == 0: return 1                  # (xxx).W
        if reg == 1: return 2                  # (xxx).L
        if reg == 2: return 1                  # (d16,PC)
        if reg == 3: return 1                  # (d8,PC,Xn)
        if reg == 4: return 2 if size == 2 else 1   # #imm
    return None

# les mots d'extension d'un EA sont-ils des DEPLACEMENTS exploitables ?
def ea_kind(mode, reg):
    if mode == 5: return 'disp'                # (d16,An)  <- tres frequent (A5)
    if mode == 7 and reg in (0,1): return 'abs'
    if mode == 7 and reg == 4: return 'imm'
    return None

SIZE_FROM_MOVE = {1:0, 3:1, 2:2}               # champ taille de MOVE -> B/W/L

def decode_one(w, i, n):
    """w: tuple de mots, i: index. -> (nwords, [(index, kind)]) ou None si inconnu."""
    if i >= n: return None
    op = w[i]
    top = op >> 12
    ext = []                                   # (index_du_mot, 'imm'|'disp'|'abs')
    def add_ea(mode, reg, size, base):
        k = ea_words(mode, reg, size)
        if k is None: return None
        kind = ea_kind(mode, reg)
        if kind: ext.append((base, kind))
        return k

    # --- MOVE / MOVEA (00,01,02,03 sauf 0000) ---
    if top in (1,2,3):
        size = SIZE_FROM_MOVE[top]
        smode, sreg = (op>>3)&7, op&7
        dmode, dreg = (op>>6)&7, (op>>9)&7
        L = 1
        k = add_ea(smode, sreg, size, i+L)
        if k is None: return None
        L += k
        k = add_ea(dmode, dreg, size, i+L)
        if k is None: return None
        L += k
        return L, ext

    # --- groupe 0 : immediats, bit ops, MOVEP ---
    if top == 0:
        mode, reg = (op>>3)&7, op&7
        if (op & 0xff00) in (0x0000,0x0200,0x0400,0x0600,0x0a00,0x0c00):  # ORI ANDI SUBI ADDI EORI CMPI
            size = (op>>6)&3
            if size == 3: return None
            L = 1 + (2 if size == 2 else 1)
            ext.append((i+1, 'imm'))
            k = add_ea(mode, reg, size, i+L)
            if k is None: return None
            return L+k, ext
        if (op & 0xff00) == 0x0800:            # BTST/BCHG/BCLR/BSET statiques
            L = 2; ext.append((i+1,'imm'))
            k = add_ea(mode, reg, 0, i+L)
            if k is None: return None
            return L+k, ext
        if (op & 0x0138) == 0x0108: return 2, [(i+1,'disp')]   # MOVEP
        k = add_ea(mode, reg, 0, i+1)          # BTST/... dynamiques
        if k is None: return None
        return 1+k, ext

    # --- MOVEQ ---
    if top == 7: return 1, []

    # --- Bcc / BSR / BRA ---
    if top == 6:
        d = op & 0xff
        if d == 0x00: return 2, [(i+1,'disp')]
        if d == 0xff: return 3, []
        return 1, []

    # --- ADDQ/SUBQ (5xxx) et Scc/DBcc ---
    if top == 5:
        mode, reg = (op>>3)&7, op&7
        if ((op>>6)&3) == 3:                   # Scc / DBcc
            if mode == 1: return 2, [(i+1,'disp')]   # DBcc
            k = add_ea(mode, reg, 0, i+1)
            if k is None: return None
            return 1+k, ext
        size = (op>>6)&3
        k = add_ea(mode, reg, size, i+1)
        if k is None: return None
        return 1+k, ext

    # --- groupe 4 : divers (TST, CLR, JMP, JSR, LEA, MOVEM, ...) ---
    if top == 4:
        if op in (0x4e70,0x4e71,0x4e72,0x4e73,0x4e75,0x4e76,0x4e77): 
            return (2,[(i+1,'imm')]) if op==0x4e72 else (1,[])
        if (op & 0xfff8) == 0x4e50: return 2, [(i+1,'disp')]        # LINK
        if (op & 0xfff8) == 0x4e58: return 1, []                     # UNLK
        if (op & 0xfff0) == 0x4e40: return 1, []                     # TRAP
        mode, reg = (op>>3)&7, op&7
        if (op & 0xfb80) == 0x4880:            # MOVEM
            size = 2 if (op>>6)&1 else 1
            L = 2; ext.append((i+1,'imm'))     # masque de registres
            k = add_ea(mode, reg, size, i+L)
            if k is None: return None
            return L+k, ext
        if (op & 0xf1c0) == 0x41c0:            # LEA
            k = add_ea(mode, reg, 2, i+1)
            if k is None: return None
            return 1+k, ext
        if (op & 0xffc0) in (0x4ec0,0x4e80):   # JMP / JSR
            k = add_ea(mode, reg, 2, i+1)
            if k is None: return None
            return 1+k, ext
        size = (op>>6)&3
        if size == 3: size = 1
        k = add_ea(mode, reg, size, i+1)
        if k is None: return None
        return 1+k, ext

    # --- 8/9/B/C/D : OR SUB CMP AND ADD (+ DIV MUL) ---
    if top in (8,9,0xb,0xc,0xd):
        mode, reg = (op>>3)&7, op&7
        size = (op>>6)&3
        if size == 3: size = 2                 # formes .W/.L d'adresse ou DIV/MUL
        k = add_ea(mode, reg, size, i+1)
        if k is None: return None
        return 1+k, ext

    # --- E : decalages ---
    if top == 0xe:
        if ((op>>6)&3) == 3:
            mode, reg = (op>>3)&7, op&7
            k = add_ea(mode, reg, 1, i+1)
            if k is None: return None
            return 1+k, ext
        return 1, []

    return None                                 # A-line, F-line, inconnu

def walk(buf, start, end, resync=True):
    """Parcourt le code et rend [(offset_octet, valeur, kind)] des vrais operandes."""
    n = min(len(buf), end)//2
    w = struct.unpack('>%dH'%n, buf[:n*2])
    i = start//2
    out=[]; bad=0
    while i < n:
        r = decode_one(w, i, n)
        if r is None:
            bad += 1
            if not resync: break
            i += 1
            continue
        L, ext = r
        for (idx, kind) in ext:
            if idx < n: out.append((idx*2, w[idx], kind))
        i += L
    return out, bad
