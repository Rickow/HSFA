#!/usr/bin/env python3
"""PARCOURS DU CODE de la ROM 68K (desassemblage recursif) : ne garde que le VRAI code.

Decoder lineairement le 1er Mo melange code et donnees (ex. les mots 0000 se decodent en
'ORI.B #0,D0'). Ici on part du point d'entree (vecteur reset) et des vecteurs d'interruption,
et on suit : Bcc/BRA/BSR, DBcc, JSR/JMP (xxx).L et d16(PC), et les tables d'aiguillage
'MOVE.W tbl(PC,Dn),D1 ; JMP/JSR tbl(PC,D1)' (entrees = dc.w cible-table).
Rend l'ensemble des adresses d'instructions atteintes."""
import sys, os, struct, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import m68k, verify

def reach(kw, limit=0x100000):
    n=min(len(kw),limit//2)
    vec=[(kw[2*v]<<16)|kw[2*v+1] for v in range(64)]
    todo=[a for a in vec[1:64] if 0x400<=a<limit and a%2==0]
    seen=set(); starts=set(todo); tables=0
    def s16(x): return x-0x10000 if x&0x8000 else x
    while todo:
        a=todo.pop()
        i=a//2
        while 0<=i<n and i*2 not in seen:
            r=m68k.decode_one(kw,i,n)
            if r is None: break
            L=r[0]; w=kw[i]; seen.add(i*2); pc=i*2
            nxt=True
            if (w&0xf000)==0x6000:                         # Bcc / BRA / BSR
                d8=w&0xff
                t=pc+2+(s16(kw[i+1]) if d8==0 else (d8-0x100 if d8&0x80 else d8))
                if 0<=t<limit: todo.append(t); starts.add(t) if (w&0x0f00)==0x0100 else None
                if (w&0x0f00)==0x0000: nxt=False           # BRA
            elif (w&0xf0f8)==0x50c8:                       # DBcc
                t=pc+2+s16(kw[i+1]); todo.append(t)
            elif w in (0x4eb9,0x4ef9):                     # JSR/JMP (xxx).L
                t=(kw[i+1]<<16)|kw[i+2]
                if 0<=t<limit and t%2==0: todo.append(t); starts.add(t)
                if w==0x4ef9: nxt=False
            elif w in (0x4eba,0x4efa):                     # JSR/JMP d16(PC)
                t=pc+2+s16(kw[i+1])
                if 0<=t<limit: todo.append(t); starts.add(t)
                if w==0x4efa: nxt=False
            elif w in (0x4efb,0x4ebb):                     # JMP/JSR d8(PC,Xn) : table
                tb=pc+2+((kw[i+1]&0xff)-0x100 if kw[i+1]&0x80 else kw[i+1]&0xff)
                j=tb//2; cnt=0; lim=0x4000
                while j<n and cnt<256:
                    off=s16(kw[j])
                    if off<=0 or off%2 or off>=lim: break
                    lim=min(lim,off)                        # la table ne peut pas depasser sa 1re cible
                    if (j*2-tb)>=lim: break
                    t=tb+off; todo.append(t); starts.add(t); cnt+=1; j+=1
                tables+=1
                if w==0x4efb: nxt=False
            elif w in (0x4e75,0x4e73,0x4e77) or (w&0xffc0)==0x4ec0: nxt=False   # RTS/RTE/RTR/JMP (An)...
            if not nxt: break
            i+=L
    return seen, starts, tables

if __name__=="__main__":
    k68=open(verify.K68,"rb").read(); kw=struct.unpack('>%dH'%(len(k68)//2),k68)
    seen,starts,tables=reach(kw)
    print("instructions atteintes : %d   points d'entree : %d   tables d'aiguillage suivies : %d"%(len(seen),len(starts),tables))
    print("etendue : %06x .. %06x"%(min(seen),max(seen)))
    import json; json.dump(sorted(seen),open(os.path.join(D,"rom_code.json"),"w"))
