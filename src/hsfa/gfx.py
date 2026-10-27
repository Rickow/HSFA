#!/usr/bin/env python3
"""Extraction des graphismes des conteneurs de l'Anthology.

STRUCTURE DU CONTENEUR (etablie sur ro5_usa_gfx_e352.bin) :
  +0x00  petit en-tete (12 mots)
  +0x30  TABLE DE TUILES : un mot de 32 bits par tuile
           valeur 0            -> tuile absente
           bit31 = 0           -> offset d'une tuile BRUTE de 0x20 o (8x8, 4bpp packe)
           bit31 = 1           -> offset d'une tuile COMPRESSEE, masquer le bit 31
                                  taille decompressee = 0x80 o (16x16, 4bpp packe)
  suit    la zone de donnees

La compression est celle du moteur (portage `lz148778.py`, validee octet pour octet).

VALIDATION : pour 12 entrees testees, decompresser vers 0x80 consomme EXACTEMENT
la longueur compressee reelle (ecart jusqu'a l'entree suivante). 12/12.

Format des pixels : **4bpp PACKE** (2 pixels par octet, nibble bas = pixel gauche),
et non le planaire de la CPS2 -> une conversion est necessaire pour produire une
ROM CPS2 (cf. `packed_to_planar` ci-dessous).
"""
import struct, sys, os
sys.path.insert(0, "<workspace>/scripts")
from lz148778 import decompress

TBL_START = 12          # 1er mot de la table
RAW_SIZE  = 0x20        # tuile brute : 8x8
CMP_SIZE  = 0x80        # tuile compressee : 16x16

def read_table(buf, max_entries=200000):
    """-> [(index, offset, compressee?)] ; s'arrete a la fin de la table."""
    N=len(buf); out=[]; bad=0
    for i in range(TBL_START, max_entries):
        o=i*4
        if o+4>N: break
        v=struct.unpack_from('<I', buf, o)[0]
        if v==0:
            out.append((i-TBL_START, None, None)); continue
        comp = bool(v & 0x80000000)
        a = v & 0x7fffffff
        if not (0 < a < N):
            bad+=1
            if bad>64: break
            continue
        out.append((i-TBL_START, a, comp))
    return out

def get_tile(buf, off, comp):
    """-> octets de la tuile (0x20 si brute, 0x80 si compressee)."""
    if off is None: return None
    if comp: return decompress(buf, off, CMP_SIZE)
    return buf[off:off+RAW_SIZE]

def to_pixels(data):
    """4bpp packe -> grille d'index. 0x20 -> 8x8 ; 0x80 -> 16x16."""
    w = 8 if len(data)==RAW_SIZE else 16
    h = w
    rows=[]
    for y in range(h):
        r=[]
        for xb in range(w//2):
            b=data[y*(w//2)+xb]
            r.append(b & 0xf); r.append(b >> 4)
        rows.append(r)
    return rows

def packed_to_planar(data):
    """4bpp packe -> planaire CPS2 (4 bitplans, 1 octet par plan et par ligne).
    Necessaire pour produire une ROM CPS2 a partir des donnees PS2."""
    px=to_pixels(data); h=len(px); w=len(px[0])
    out=bytearray()
    for y in range(h):
        for x0 in range(0, w, 8):
            for p in range(4):
                b=0
                for k in range(8):
                    if (px[y][x0+k] >> p) & 1: b |= 1 << (7-k)
                out.append(b)
    return bytes(out)

if __name__=="__main__":
    path=sys.argv[1] if len(sys.argv)>1 else \
        "<workspace>/anthology_extract/ro5_usa_gfx_e352.bin"
    buf=open(path,'rb').read()
    tbl=read_table(buf)
    raw=sum(1 for _,o,c in tbl if o is not None and not c)
    cmp_=sum(1 for _,o,c in tbl if o is not None and c)
    holes=sum(1 for _,o,_ in tbl if o is None)
    print("%s"%os.path.basename(path))
    print("  entrees de table : %d"%len(tbl))
    print("    brutes (8x8)      : %d"%raw)
    print("    compressees(16x16): %d"%cmp_)
    print("    trous             : %d"%holes)
    ok=0; fail=0
    for _,o,c in tbl:
        if o is None: continue
        try:
            t=get_tile(buf,o,c)
            if t and len(t)==(CMP_SIZE if c else RAW_SIZE): ok+=1
            else: fail+=1
        except Exception: fail+=1
    print("  extraction : %d reussies, %d echecs"%(ok,fail))
