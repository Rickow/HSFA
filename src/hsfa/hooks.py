#!/usr/bin/env python3
"""Localise le code AJOUTE par le portage (Anthology), absent de la ROM arcade.

Deux criteres independants, par zone :
  1. densite d'ANCRES de la carte (le code d'origine s'aligne sur la ROM, pas le code ajoute)
  2. part des variables A5 'ETRANGERES' : deplacements (d16,A5) que le code de la ROM
     n'utilise JAMAIS (ex. $c19c, $c112, $9eb0 : variables d'options du portage).
"""
import sys, os, json, re, struct, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify, m68k
from mips import CODE0, CODE1

def rom_a5_disps(k68):
    """deplacements utilises avec (d16,A5) par le code de la ROM (1er Mo)."""
    n=0x100000//2; w=struct.unpack('>%dH'%n,k68[:0x100000]); out=set(); i=0
    while i<n:
        r=m68k.decode_one(w,i,n)
        if r is None: i+=1; continue
        L,ext=r
        op=w[i]
        # champs EA source (bits 5-0) et destination MOVE (bits 11-6 inverses)
        eas=[op&0x3f]
        if (op>>12) in (1,2,3): eas.append(((op>>6)&7)<<3 | ((op>>9)&7))
        disps=[w[idx] for idx,kind in ext if kind=='disp' and idx<n]
        if any(e==0x2d for e in eas):
            out.update(disps)
        i+=L
    return out

if __name__=="__main__":
    buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()
    rom=rom_a5_disps(k68)
    print("deplacements (d16,A5) utilises par la ROM : %d"%len(rom))
    pts=[]
    for b in json.load(open(os.path.join(D,"map_chain2.json")))["blocks"]: pts+=[p[0] for p in b.get("pts",[])]
    anc=collections.Counter(p>>16 for p in pts)
    a5=collections.Counter(); foreign=collections.Counter(); fvars=collections.Counter()
    x=CODE0
    while x<CODE1:
        out,_=T.translate(buf,x,min(x+0x8000,CODE1))
        for va,mn,ws in out:
            for d in re.findall(r'\$([0-9a-f]{4})\(A5\)',mn):
                v=int(d,16); a5[va>>16]+=1
                if v not in rom: foreign[va>>16]+=1; fvars[v]+=1
        x+=0x8000
    print("\n zone     ancres  refs A5  etrangeres")
    for z in range(CODE0>>16,(CODE1>>16)+1):
        t=a5[z]; f=foreign[z]
        flag=" <== code AJOUTE ?" if t>=20 and f/t>0.5 else ""
        print("  %02x0000  %5d  %6d   %5d (%3.0f%%)%s"%(z,anc[z],t,f,100*f/max(1,t),flag))
    print("\nvariables A5 etrangeres les plus utilisees :",', '.join('$%04x x%d'%kv for kv in fvars.most_common(12)))
    json.dump({"rom_a5":sorted(rom),"foreign":{"%04x"%k:v for k,v in fvars.items()}},open(os.path.join(D,"hooks_a5.json"),"w"))
