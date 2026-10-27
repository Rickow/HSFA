#!/usr/bin/env python3
"""Compare les modules MIPS entre eux (SFA3 ro3, Upper ro5, Hyper ro9), fonction par
fonction. Meme architecture => comparaison directe, sans traduction.

Normalisation : on masque ce qui change forcement d'un module a l'autre (cibles de jal,
adresses construites par lui+addiu/ori). Deux niveaux :
  - 'identique'         : tout le reste est egal (dont les deplacements memoire)
  - 'meme structure'    : egal si on masque AUSSI les deplacements des lectures/ecritures
L'ecart entre les deux = fonctions ou SEULS des deplacements ont change (champ deplace,
ou disposition memoire differente)."""
import sys, os, struct, hashlib, bisect, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode
DIR="<workspace>/anthology_extract/decompressed"
BASE=0x1f0000
LS={0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b,0x37,0x3f,0x1e,0x1f}

def module(name):
    buf=open(os.path.join(DIR,name+"_usa_prog68k.bin"),"rb").read()
    end=struct.unpack_from('<I',buf,12)[0]
    # debut du 68K : premier acces au banc 0x7000_11xx (avant : le Z80, banc 0x10xx)
    L=list(decode(buf,0x20,end)); start=None
    for i in range(1,len(L)):
        if L[i-1].m=='lui' and L[i-1].imm==0x7000 and L[i].rs==L[i-1].rt and 0x1100<=L[i].imm<=0x1160:
            start=L[i].va; break
    starts=sorted({x.tgt-BASE for x in L if x.m=='jal' and start<=x.tgt-BASE<end})
    return buf,start,end,starts,L

def sig(L0, a, b, mask_disp):
    h=hashlib.blake2b(digest_size=12); prev_lui=set(); n=0
    for x in L0:
        if x.va<a: continue
        if x.va>=b: break
        w=x.w; op=w>>26
        if op==3: w&=0xfc000000                                   # jal : cible masquee
        elif op==0x0f: w&=0xffff0000; prev_lui.add((w>>16)&0x1f)   # lui : adresse masquee
        elif op in (0x09,0x0d) and ((w>>21)&0x1f) in prev_lui: w&=0xffff0000
        elif mask_disp and op in LS: w&=0xffff0000                 # deplacement masque
        h.update(struct.pack('<I',w)); n+=1
    return h.digest(), n

def functions(mod, mask_disp):
    buf,start,end,starts,L=mod
    out=[]
    for k,a in enumerate(starts):
        b=starts[k+1] if k+1<len(starts) else end
        if b-a<16: continue
        i0=bisect.bisect_left([x.va for x in L[:0]],a)  # (placeholder)
        out.append((a,b))
    return out

def _main_exact():
    mods={n:module(n) for n in ('ro3','ro5','ro9')}
    for n,(buf,s,e,st,L) in mods.items():
        print("%s : 68K de %#x a %#x (%d Ko), %d fonctions (cibles de jal)"%(n,s,e,(e-s)//1024,len(st)))
    idx={}
    for n,(buf,s,e,st,L) in mods.items():
        vas=[x.va for x in L]; fs=[]
        for k,a in enumerate(st):
            b=st[k+1] if k+1<len(st) else e
            i=bisect.bisect_left(vas,a); j=bisect.bisect_left(vas,b)
            seg=L[i:j]
            fs.append((a,b,sig(seg,a,b,False)[0],sig(seg,a,b,True)[0]))
        idx[n]=fs
    ref_exact={f[2] for f in idx['ro3']}; ref_struct={f[3] for f in idx['ro3']}
    for n in ('ro5','ro9'):
        tot=sum(b-a for a,b,_,_ in idx[n])
        ex=sum(b-a for a,b,e,_ in idx[n] if e in ref_exact)
        stc=sum(b-a for a,b,e,s in idx[n] if s in ref_struct and e not in ref_exact)
        nb_ex=sum(1 for f in idx[n] if f[2] in ref_exact)
        nb_st=sum(1 for f in idx[n] if f[3] in ref_struct and f[2] not in ref_exact)
        print("\n%s vs SFA3 (ro3), en taille de code :"%n)
        print("   fonctions IDENTIQUES a SFA3               : %5.1f %%  (%d fonctions)"%(100*ex/tot,nb_ex))
        print("   identiques SAUF des deplacements memoire  : %5.1f %%  (%d fonctions)"%(100*stc/tot,nb_st))
        print("   NOUVELLES ou modifiees                    : %5.1f %%"%(100*(tot-ex-stc)/tot))
    # Hyper vs Upper
    r5e={f[2] for f in idx['ro5']}
    tot=sum(b-a for a,b,_,_ in idx['ro9'])
    print("\nro9 (Hyper) : code identique a Upper (ro5) : %.1f %% ; identique a SFA3 OU Upper : %.1f %%"%(
        100*sum(b-a for a,b,e,_ in idx['ro9'] if e in r5e)/tot,
        100*sum(b-a for a,b,e,_ in idx['ro9'] if e in r5e or e in ref_exact)/tot))

def grams(seg, k=4):
    """k-grammes d'instructions normalisees (adresses et immediats masques : on compare
    la FORME du code, une valeur retouchee ne doit pas tout faire echouer)."""
    ws=[]; lui=set()
    for x in seg:
        w=x.w; op=w>>26
        if op in (2,3): w&=0xfc000000
        elif op==0x0f: w&=0xffff0000; lui.add((w>>16)&0x1f)
        elif op in (0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e) or op in LS or op in (4,5,1,6,7): w&=0xffff0000
        ws.append(w)
    return {hash(tuple(ws[i:i+k])) for i in range(len(ws)-k+1)}

def fuzzy(mods):
    """pour chaque fonction de ro5/ro9 : meilleure ressemblance (Jaccard des k-grammes)
    avec une fonction de ro3, via un index inverse."""
    def funcs(n):
        buf,s,e,st,L=mods[n]; vas=[x.va for x in L]; out=[]
        for k,a in enumerate(st):
            b=st[k+1] if k+1<len(st) else e
            if b-a<32: continue
            seg=L[bisect.bisect_left(vas,a):bisect.bisect_left(vas,b)]
            g=grams(seg)
            if g: out.append((a,b,g))
        return out
    F3=funcs('ro3'); inv=collections.defaultdict(list)
    for k,(a,b,g) in enumerate(F3):
        for x in g: inv[x].append(k)
    res={}
    for n in ('ro5','ro9'):
        rows=[]
        for a,b,g in funcs(n):
            cnt=collections.Counter()
            for x in g:
                lst=inv.get(x)
                if lst and len(lst)<40: cnt.update(lst)       # k-grammes trop communs ignores
            # les k-grammes rares ne servent qu'a CHOISIR les candidats ; la ressemblance
            # se calcule ensuite sur les ensembles COMPLETS (intersection / union).
            # (version precedente : numerateur sur les seuls k-grammes rares => sous-estimation)
            best=0.0
            for k,c in cnt.most_common(8):
                G=F3[k][2]; best=max(best,len(g&G)/len(g|G))
            rows.append((b-a,best))
        res[n]=rows
    return res

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="flou":
        mods={n:module(n) for n in ('ro3','ro5','ro9')}
        res=fuzzy(mods)
        for n,rows in res.items():
            tot=sum(sz for sz,_ in rows)
            print("\n%s : part du code (en taille) selon la ressemblance avec la fonction la plus proche de SFA3"%n)
            for lo,hi,lab in ((0.9,1.01,'>= 90 %% (quasi identique)'),(0.7,0.9,'70-90 %% (proche)'),(0.4,0.7,'40-70 %% (apparente)'),(0.0,0.4,'< 40 %% (nouveau)')):
                part=sum(sz for sz,j in rows if lo<=j<hi)
                print("   %-28s : %5.1f %%"%(lab%(),100*part/tot))
    else:
        _main_exact()
