#!/usr/bin/env python3
"""Test de BOUT EN BOUT sur une fonction : traduire -> assembler -> comparer a la ROM.

La fonction MIPS est delimitee par les cibles de 'jal' (vrais debuts de fonction).
On localise la fonction 68K correspondante dans la ROM par ses premiers mots, puis on
compare mot a mot et on liste les ecarts (avec leur nature)."""
import sys, os, struct, bisect
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify
from assemble import assemble
from mips import decode, CODE0, CODE1

def func_bounds(buf, va):
    starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
    k=bisect.bisect_right(starts,va)-1
    return starts[k], (starts[k+1] if k+1<len(starts) else CODE1)

def locate(kw, words, n=4):
    """position dans la ROM de la meilleure correspondance des premiers mots (en
    ignorant les mots de deplacement, qui peuvent differer)."""
    head=words[:n]; best=(0,None)
    for j in range(len(kw)-len(head)):
        if kw[j]!=head[0]: continue
        sc=sum(1 for t in range(len(head)) if kw[j+t]==head[t])
        if sc>best[0]: best=(sc,j)
    return best[1]

def _main_one():
    va=int(sys.argv[1],16) if len(sys.argv)>1 else 0x23090
    buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
    kw=struct.unpack('>%dH'%(len(k68)//2),k68)
    a,b=func_bounds(buf,va)
    rloc=None
    its,words,unres=assemble(buf,a,b,base=0,external=T.mips_to_68k)
    j=locate(kw,words)
    if j is None: sys.exit("fonction introuvable dans la ROM")
    # re-assembler a la VRAIE adresse (les BSR/BRA sont relatifs, mais les tables et les
    # JSR.L absolus dependent de l'adresse de base)
    its,words,unres=assemble(buf,a,b,base=j*2,external=snapped_external(kw))
    ref=kw[j:j+len(words)]
    same=sum(1 for x,y in zip(words,ref) if x==y)
    print("fonction MIPS %07x..%07x -> %d mots 68K ; localisee dans la ROM a %06x"%(a,b,len(words),j*2))
    print("non resolus : %d   IDENTITE : %d/%d mots (%.1f%%)"%(unres,same,len(words),100*same/len(words)))
    # premiers ecarts, avec l'element qui les produit
    pos=0; shown=0
    for it in its:
        from assemble import size
        n=size(it)//2
        for t in range(n):
            p=pos+t
            if p<len(words) and words[p]!=ref[p] and shown<14:
                print("   +%04x  emis %04x  ROM %04x   <- %s"%(p*2,words[p],ref[p],it.mn[:60])); shown+=1
        pos+=n

_ENTRIES=None
def rom_entries(kw):
    """debuts de routine CONNUS de la ROM : cibles de JSR/JMP (xxx).L et de BSR/BRA"""
    global _ENTRIES
    if _ENTRIES is None:
        e=set()
        for j in range(len(kw)-3):
            w=kw[j]
            if w in (0x4eb9,0x4ef9): e.add((kw[j+1]<<16)|kw[j+2])
            elif (w&0xfe00)==0x6000 and (w&0xff)==0:
                d=kw[j+1]-(0x10000 if kw[j+1]&0x8000 else 0); e.add(j*2+2+d)
        _ENTRIES=sorted(x for x in e if 0<=x<0x100000 and x%2==0)
    return _ENTRIES

def snapped_external(kw):
    """VALIDATION SEULEMENT : la carte place une cible d'appel a quelques octets pres ;
    on la cale sur le vrai debut de routine le plus proche (+-16 o). Aucun effet sur la
    traduction elle-meme (dans une vraie sortie, les cibles sont nos propres libelles)."""
    ent=rom_entries(kw)
    def ext(t):
        k=T.mips_to_68k(t)
        if k is None: return None
        i=bisect.bisect_left(ent,k); best=None
        for c in ent[max(0,i-2):i+2]:
            if abs(c-k)<=16 and (best is None or abs(c-k)<abs(best-k)): best=c
        return best if best is not None else k
    return ext

def locate_mapped(kw, words, k0, span=64, n=12):
    """localisation guidee par la carte : meilleure correspondance des n premiers mots
    dans [k0-span, k0+span]."""
    best=(0,None)
    for j in range(max(0,(k0-span)//2), min(len(kw)-n,(k0+span)//2)):
        sc=sum(1 for t in range(min(n,len(words))) if kw[j+t]==words[t])
        if sc>best[0]: best=(sc,j)
    return best

def batch(buf, kw, nmax=300):
    import json, re, random
    from assemble import assemble
    fz=json.load(open(os.path.join(D,"hooks_a5.json")))
    foreign={int(k,16) for k in fz["foreign"]}
    bad_zones={0x05,0x18,0x19,0x1a,0x1b,0x38,0x39,0x02,0x03,0x04}
    starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
    random.seed(9); cand=[s for s in starts if (s>>16) not in bad_zones]
    random.shuffle(cand)
    res=[]; skipped=0
    for a in cand:
        if len(res)>=nmax: break
        k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
        if b-a>0x3000 or b-a<0x40: continue
        k0=T.mips_to_68k(a)
        if k0 is None: continue
        try: its,words,unres=assemble(buf,a,b,base=0,external=T.mips_to_68k)
        except Exception as e: print("!!! %x %r"%(a,e)); continue
        if len(words)<8: continue
        if any(int(d,16) in foreign for it in its for d in re.findall(r'\$([0-9a-f]{4})\(A5\)',it.mn)):
            skipped+=1; continue
        sc,j=locate_mapped(kw,words,k0)
        if j is None or sc<4: continue
        its,words,unres=assemble(buf,a,b,base=j*2,external=snapped_external(kw))
        ref=kw[j:j+len(words)]
        same=sum(1 for x,y in zip(words,ref) if x==y)
        # identite par ALIGNEMENT (LCS) : insensible aux decalages
        n1,n2=len(words),len(ref); dp=[0]*(n2+1)
        for x in words:
            prev=0
            for t in range(n2):
                cur=dp[t+1]
                dp[t+1]=prev+1 if x==ref[t] else max(dp[t+1],dp[t])
                prev=cur
        lcs=dp[n2]
        # premiere divergence : element emis et mots ROM a cet endroit
        pos=0; first=None
        from assemble import size
        for it in its:
            n=size(it)//2
            if any(pos+t<len(words) and words[pos+t]!=ref[pos+t] for t in range(n)):
                first=(it.mn.split()[0] if it.mn else '?', ref[pos] if pos<len(ref) else 0, it.mn); break
            pos+=n
        res.append((same/len(words),len(words),a,j*2,unres,lcs/len(words),first))
    return res, skipped

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="batch":
        buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
        kw=struct.unpack('>%dH'%(len(k68)//2),k68)
        res,sk=batch(buf,kw,int(sys.argv[2]) if len(sys.argv)>2 else 200)
        res.sort()
        ids=[r[0] for r in res]
        print("fonctions d'origine testees : %d (ecartees car crochet : %d)"%(len(res),sk))
        if ids:
            q=lambda f: ids[min(len(ids)-1,int(f*len(ids)))]
            print("IDENTITE binaire par fonction : mediane %.0f%%   quartiles %.0f%% / %.0f%%   min %.0f%%   max %.0f%%"%(
                100*q(.5),100*q(.25),100*q(.75),100*ids[0],100*ids[-1]))
            tot=sum(r[1] for r in res); same=sum(r[0]*r[1] for r in res)
            print("identite ponderee (tous les mots) : %.1f%%"%(100*same/tot))
            print("fonctions a 100 %%        : %d"%sum(1 for x in ids if x>=0.999))
            print("fonctions >= 90 %%        : %d"%sum(1 for x in ids if x>=0.9))
            al=sorted(r[5] for r in res)
            print("IDENTITE PAR ALIGNEMENT (LCS) : mediane %.0f%%   quartiles %.0f%% / %.0f%%"%(
                100*al[len(al)//2],100*al[len(al)//4],100*al[3*len(al)//4]))
            import collections
            def fam(w):
                h=w>>12
                return {0:'imm/bit',1:'MOVE.B',2:'MOVE.L',3:'MOVE.W',4:'misc(4)',5:'ADDQ/Scc/DBcc',6:'Bcc/BSR/BRA',
                        7:'MOVEQ',8:'OR/DIV',9:'SUB',0xb:'CMP/EOR',0xc:'AND/MUL',0xd:'ADD',0xe:'decalage'}.get(h,'?')
            fd=collections.Counter()
            for r in res:
                if r[6]: fd[(r[6][0], fam(r[6][1]))]+=1
            print("\nPREMIERE DIVERGENCE (emis -> famille ROM a cet endroit) :")
            for (e,f),c in fd.most_common(14): print("   %-10s -> %-14s %3d"%(e,f,c))
            for r in res[-5:]: print("   %.0f%%  %4d mots  MIPS %07x  ROM %06x  non resolus %d"%(100*r[0],r[1],r[2],r[3],r[4]))
    else:
        _main_one()
