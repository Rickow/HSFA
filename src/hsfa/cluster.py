#!/usr/bin/env python3
"""Regroupe les effets MANQUES par signature abstraite des instructions qui les
precedent : la liste des idiomes a ajouter, avec un exemple pour chacun."""
import sys,collections; sys.path.insert(0,'<workspace>/scripts/untranspile')
from mips import decode
import translate as T, census
buf=open(census.RO3,"rb").read()
def slotname(v):
    if v==0x1150: return 'RES'
    if v==0x1158: return 'C'
    if 0x1100<=v<0x1120: return 'A%d'%((v-0x1100)//4)
    if 0x1124<=v<=0x1140: return 'D%d'%((v-0x1124)//4)
    return 's%x'%v
def abst(x,keepreg=False):
    if x.m=='lui': return None if x.imm==0x7000 else 'lui'
    if x.m=='sll' and x.w==0: return None
    if x.m in ('dsll32','dsra32'): return None
    if x.m in ('lw','lh','lb','lhu','lbu','sw','sh','sb','ld','sd'):
        if 0x1000<=x.imm<=0x1160 and x.rs in (1,2,3,4,5): return x.m+' '+slotname(x.imm)[0]
        return x.m+' mem'
    if x.m in ('addiu','andi','ori','xori'): return x.m+('#' if x.rs==0 else '')
    return x.m
def cluster(kind, a, b, n=8, depth=6):
    out,_=T.translate(buf,a,b); em={va for va,_,ws in out}
    L=list(decode(buf,a,b)); sig=collections.Counter(); ex={}
    for i,x in enumerate(L):
        if x.m not in ('sb','sh','sw'): continue
        if any(v in em for v in (x.va-8,x.va-4,x.va,x.va+4)): continue
        slot = i>0 and L[i-1].m=='lui' and L[i-1].imm==0x7000
        if slot:
            nm=slotname(x.imm)
            if nm in ('RES','C'): continue
            k0='ecrit '+nm[0]
        else:
            k0='store mem'
        if kind and k0!=kind: continue
        pre=[s for s in (abst(y) for y in L[max(0,i-14):i]) if s][-depth:]
        k=tuple(pre)+(x.m,)
        sig[k]+=1; ex.setdefault(k,x.va)
    tot=sum(sig.values())
    print("\n=== %s : %d manques (%x..%x)"%(kind,tot,a,b))
    for k,c in sig.most_common(n): print("  %4d (%2.0f%%) @%07x  %s"%(c,100*c/max(1,tot),ex[k],' ; '.join(k)))
if __name__=="__main__":
    a=int(sys.argv[2],16) if len(sys.argv)>2 else 0x1c0000; b=int(sys.argv[3],16) if len(sys.argv)>3 else 0x220000
    for k in sys.argv[1].split(','): cluster(k,a,b)
