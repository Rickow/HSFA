#!/usr/bin/env python3
"""Resolution des STUBS d'appel (trampolines vers le moteur).

Constat (2026-09-26) : 106 fonctions 'natives' de ro3 ne sont que des trampolines
  addiu sp ; sd ra ; lui/addiu v0,<moteur> ; jalr v0 ; ld ra ; jr ra
vers une routine du moteur PS2 (0x3de600, parfois 0x28bbc0). Elles ne passent aucun
argument : la routine identifie la cible par l'adresse de retour. Au meme endroit la
ROM 68K a un BSR/JSR/JMP. Chaque stub represente donc UN appel 68K dont la cible est
resolue a l'execution. 1 282 sites d'appel passent par ces stubs.

Methode : aux sites que la carte place avec precision, on decode l'instruction
d'appel presente dans la ROM et sa cible ; on vote par stub. Un vrai trampoline
vers une routine donnee doit faire emerger UNE cible majoritaire.
"""
import sys, os, json, struct, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, CODE0, CODE1
import translate as T, verify
B=T.RUNTIME_BASE

def rom_calls(kw, k, span=12):
    """instructions d'appel/saut 68K dans [k-span, k+span] : (offset, type, cible)."""
    out=[]
    for j in range(max(0,(k-span)//2), (k+span)//2+1):
        w=kw[j]; o=j*2
        if w==0x4eb9 or w==0x4ef9:                                  # JSR/JMP (xxx).L
            out.append((o,'JSR' if w==0x4eb9 else 'JMP',(kw[j+1]<<16)|kw[j+2]))
        elif w==0x4eba or w==0x4efa:                                # JSR/JMP (d16,PC)
            d=kw[j+1]-(0x10000 if kw[j+1]&0x8000 else 0)
            out.append((o,'JSR' if w==0x4eba else 'JMP',o+2+d))
        elif (w&0xff00) in (0x6100,0x6000):                         # BSR/BRA
            t='BSR' if w&0x0100 else 'BRA'
            d8=w&0xff
            if d8==0:
                d=kw[j+1]-(0x10000 if kw[j+1]&0x8000 else 0); out.append((o,t,o+2+d))
            elif d8!=0xff:
                d=d8-(0x100 if d8&0x80 else 0); out.append((o,t,o+2+d))
    return out

if __name__=="__main__":
    buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()
    kw=struct.unpack('>%dH'%(len(k68)//2),k68[:len(k68)//2*2])
    nat=set(json.load(open(os.path.join(D,"native_funcs.json")))["native"])
    stubs={}
    for o in nat:
        b=list(decode(buf,o,o+0x24))
        if len(b)>4 and b[4].m=='jalr' and b[2].m=='lui' and b[3].m=='addiu':
            stubs[o]=(b[2].imm<<16)+b[3].simm
    print("stubs : %d  (cibles moteur : %s)"%(len(stubs),
          ', '.join('%x x%d'%kv for kv in collections.Counter(stubs.values()).items())))
    votes=collections.defaultdict(collections.Counter); nsites=collections.Counter(); placed=0
    for ins in decode(buf,CODE0,CODE1):
        if ins.m!='jal': continue
        s=ins.tgt-B
        if s not in stubs: continue
        nsites[s]+=1
        k=T.mips_to_68k(ins.va)
        if k is None: continue
        placed+=1
        for o,t,tgt in rom_calls(kw,k):
            if t in ('JSR','BSR','JMP') and 0<=tgt<0x100000: votes[s][tgt]+=1
    print("sites d'appel de stubs : %d, dont places par la carte : %d"%(sum(nsites.values()),placed))
    res={}; clean=0; amb=0
    for s,c in votes.items():
        (t,n),=c.most_common(1); tot=sum(c.values())
        if n>=2 and n/tot>=0.6: res[s]=t; clean+=1
        else: amb+=1
    print("stubs resolus (cible majoritaire >=60 %% et >=2 votes) : %d | ambigus : %d | sans vote : %d"%(
        clean,amb,len(stubs)-len(votes)))
    cov=sum(nsites[s] for s in res)
    print("=> sites d'appel resolus : %d / %d (%.0f%%)"%(cov,sum(nsites.values()),100*cov/max(1,sum(nsites.values()))))
    for s,t in sorted(res.items(),key=lambda z:-nsites[z[0]])[:8]:
        print("   stub %07x (%3d sites) -> 68K %06x   votes %s"%(s,nsites[s],t,dict(votes[s].most_common(3))))
    json.dump({"%x"%s:t for s,t in res.items()},open(os.path.join(D,"stubs_resolved.json"),"w"))
