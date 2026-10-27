#!/usr/bin/env python3
"""Classification des tables de donnees referencees par le code recompile.

Constat qui simplifie le probleme : pour TRADUIRE, on n'a pas besoin de retrouver
l'adresse d'origine d'une table cote 68K. Il suffit de :
  - copier VERBATIM les tables de valeurs,
  - REECRIRE les tables de pointeurs avec les adresses 68K traduites (via la carte).
La relocation porte donc sur NOTRE sortie, pas sur un appariement avec l'original.

Ce module repere les adresses de tables construites par le code (lui+addiu) et
classe chaque table : POINTEURS (a reecrire) ou VALEURS (a copier).
"""
import sys, struct, collections
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import decode

RUNTIME_BASE = 0x1f0000
CODE_LO, CODE_HI = 0x200000, 0x700000     # plage d'adresses d'execution du code

def find_table_refs(buf, start, end):
    """paires (lui rX,hi ; addiu rX,rX,lo) -> adresse construite."""
    hi={}; refs=collections.Counter()
    for ins in decode(buf,start,end):
        if ins.m=='lui': hi[ins.rt]=ins.imm
        elif ins.m=='addiu' and ins.rs in hi and ins.rs==ins.rt:
            addr=(hi[ins.rs]<<16)+ins.simm
            if addr>CODE_HI: refs[addr&0xffffffff]+=1
            hi.pop(ins.rs,None)
        elif ins.m in ('lui',): pass
        else:
            if ins.m not in ('sll',) and ins.rt in hi and ins.m!='addiu': hi.pop(ins.rt,None)
    return refs

def classify(buf, addr, n=32):
    off=addr-RUNTIME_BASE
    if off<0 or off+n*4>len(buf): return None
    vals=[struct.unpack_from('<I',buf,off+i*4)[0] for i in range(n)]
    ptr=sum(1 for v in vals if CODE_LO<=v<=CODE_HI)
    return ('POINTEURS' if ptr>=n//3 else 'VALEURS'), ptr, n, vals[:4]

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    import json
    mp=json.load(open("<workspace>/scripts/untranspile/map_ro3_sfa3.json"))["blocks"]
    refs=collections.Counter()
    for b in sorted(mp,key=lambda x:-x["pts"])[:8]:
        refs += find_table_refs(ro3, b["mips"][0], b["mips"][1])
    print("adresses de tables referencees : %d distinctes, %d references\n"%(
        len(refs), sum(refs.values())))
    np=nv=0
    rows=[]
    for a,c in refs.most_common():
        r=classify(ro3,a)
        if not r: continue
        kind,ptr,n,head=r
        if kind=='POINTEURS': np+=1
        else: nv+=1
        rows.append((c,a,kind,ptr,n,head))
    print("  tables de POINTEURS (a reecrire) : %d"%np)
    print("  tables de VALEURS   (a copier)   : %d\n"%nv)
    print("=== les 12 plus referencees ===")
    for c,a,kind,ptr,n,head in rows[:12]:
        print("  x%-4d %08x  %-10s %2d/%d ptr   %s"%(
            c,a,kind,ptr,n,' '.join('%08x'%v for v in head)))
