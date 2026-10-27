#!/usr/bin/env python3
"""Apprend la CARTE DES ADRESSES PS2 -> CPS2 sur SFA3, ou l'on a la ROM d'origine.

Le traducteur emet 'LEA $adresse_PS2.L,An' pour chaque adresse constante chargee dans
un registre d'adresse. Dans les fonctions alignees sur la ROM, on apparie ces LEA avec
l'instruction de la ROM qui occupe la meme place (meme opcode, ou meme position dans un
trou encadre par des instructions identiques), si c'est un chargement d'adresse :
LEA abs.L / abs.W / d16(PC), MOVEA.L #, MOVEA.W #. On en tire des paires
(adresse PS2, adresse 68K) regroupees par zone -> decalage par zone."""
import sys, os, json, re, struct, random, bisect, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify, e2e, m68k
from assemble import assemble, size
from layout_probe import insts
from mips import decode, CODE0, CODE1

def rom_addr_load(ins, pos):
    """(registre, adresse) si l'instruction ROM charge une adresse constante dans An."""
    w=ins[0]; n=(w>>9)&7
    if (w&0xf1ff)==0x41f9 and len(ins)>=3: return n, (ins[1]<<16)|ins[2]           # LEA abs.L
    if (w&0xf1ff)==0x207c and len(ins)>=3: return n, (ins[1]<<16)|ins[2]           # MOVEA.L #
    if (w&0xf1ff)==0x41f8 and len(ins)>=2: return n, (ins[1]-0x10000 if ins[1]&0x8000 else ins[1])&0xffffff
    if (w&0xf1ff)==0x307c and len(ins)>=2: return n, (ins[1]-0x10000 if ins[1]&0x8000 else ins[1])&0xffffff
    if (w&0xf1ff)==0x41fa and len(ins)>=2: return n, (pos+2+(ins[1]-0x10000 if ins[1]&0x8000 else ins[1]))&0xffffff
    return None

if __name__=="__main__":
    buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
    kw=struct.unpack('>%dH'%(len(k68)//2),k68)
    bad={0x05,0x18,0x19,0x1a,0x1b,0x38,0x39}
    starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
    random.seed(5); cand=[s for s in starts if (s>>16) not in bad]; random.shuffle(cand)
    pairs=[]; nf=0; ram=T.ram_hi_of(buf)<<16
    for a in cand[:1500]:
        k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
        if b-a>0x3000 or b-a<0x40: continue
        k0=T.mips_to_68k(a)
        if k0 is None: continue
        its,words,u=assemble(buf,a,b,external=T.mips_to_68k)
        if len(words)<8 or not any((w&0xf1ff)==0x41f9 for w in words): continue
        sc,j=e2e.locate_mapped(kw,words,k0)
        if j is None or sc<4: continue
        nf+=1
        E=insts(list(words)); R=insts(list(kw[j:j+len(words)+60]))
        Rpos=[]; p=j*2
        for r in R: Rpos.append(p); p+=2*len(r)
        n1,n2=len(E),len(R); dp=[[0]*(n2+1) for _ in range(n1+1)]
        for x in range(n1-1,-1,-1):
            for y in range(n2-1,-1,-1):
                dp[x][y]=dp[x+1][y+1]+1 if E[x][0]==R[y][0] else max(dp[x+1][y],dp[x][y+1])
        x=y=0; match=[]
        while x<n1 and y<n2:
            if E[x][0]==R[y][0]: match.append((x,y)); x+=1; y+=1
            elif dp[x+1][y]>=dp[x][y+1]: x+=1
            else: y+=1
        mset=dict(match)
        for x0,e in enumerate(E):
            if (e[0]&0xf1ff)!=0x41f9 or len(e)<3: continue
            host=(e[1]<<16)|e[2]
            if x0 in mset: y0=mset[x0]
            else:
                prev=[(xx,yy) for xx,yy in match if xx<x0]; nxt=[(xx,yy) for xx,yy in match if xx>x0]
                if not prev or not nxt: continue
                (pp,qp),(pn,qn)=prev[-1],nxt[0]
                if pn-pp!=qn-qp: continue                    # trou de meme taille des deux cotes
                y0=qp+(x0-pp)
            r=rom_addr_load(R[y0],Rpos[y0])
            if r and r[0]==(e[0]>>9)&7: pairs.append((host,r[1]))
    print("fonctions alignees contenant un LEA : %d   paires (PS2 -> 68K) : %d"%(nf,len(pairs)))
    z=collections.defaultdict(collections.Counter)
    for h,r in pairs: z[(h-ram)>>16][(r-(h-ram))&0xffffff]+=1
    print("\nzone PS2 (relative a la base RAM)  ->  decalage 68K le plus frequent (occurrences)")
    for zz in sorted(z):
        (off,c),=z[zz].most_common(1); tot=sum(z[zz].values())
        ex=[(h,r) for h,r in pairs if (h-ram)>>16==zz][:3]
        print("   +%05x :  68K = PS2rel + %06x   (%d/%d)   ex. %s"%(zz<<16,off,c,tot,', '.join('%06x->%06x'%(h,r) for h,r in ex)))
    json.dump([list(p) for p in pairs],open(os.path.join(D,"addr_pairs.json"),"w"))
