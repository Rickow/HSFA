#!/usr/bin/env python3
"""Mesure EMPIRIQUE de la disposition memoire du recompilateur.

Dans les fonctions d'origine alignees sur la ROM, on apparie chaque instruction emise
a son homologue de la ROM (alignement LCS sur les OPCODES), puis on compare les
deplacements (d16,An) : XOR 0, 1, 2 ou 3 entre deplacement hote (MIPS) et 68K (ROM).
Tabule par largeur d'acces et par registre de base."""
import sys, os, re, struct, json, random, bisect, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify, e2e, m68k
from assemble import assemble, size
from mips import decode, CODE0, CODE1

def insts(words):
    """decoupe une suite de mots en instructions 68K (via le decodeur de longueur)."""
    out=[]; i=0; n=len(words)
    while i<n:
        r=m68k.decode_one(words,i,n)
        L=r[0] if r else 1
        out.append(tuple(words[i:i+L])); i+=L
    return out

def disp_of(ins):
    """(taille, reg, deplacement) pour une instruction a UN operande (d16,An) simple."""
    op=ins[0]; h=op>>12
    sz={1:'B',3:'W',2:'L'}.get(h)
    if sz and (op&0x38)==0x28 and len(ins)>=2:          # MOVE source (d16,An)
        return sz, op&7, ins[1]
    if sz and ((op>>6)&7)==5 and len(ins)>=2:           # MOVE destination (d16,An)
        return sz, (op>>9)&7, ins[-1]
    if (op&0xff00) in (0x4a00,0x4200) and (op&0x38)==0x28:   # TST/CLR
        return 'BWL'[(op>>6)&3], op&7, ins[1]
    return None

if __name__=="__main__":
    buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
    kw=struct.unpack('>%dH'%(len(k68)//2),k68)
    fz=json.load(open(os.path.join(D,"hooks_a5.json"))); foreign={int(k,16) for k in fz["foreign"]}
    bad={0x05,0x18,0x19,0x1a,0x1b,0x38,0x39,0x02,0x03,0x04}
    starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
    random.seed(9); cand=[s for s in starts if (s>>16) not in bad]; random.shuffle(cand)
    tab=collections.Counter(); ex={}; nf=0; pairs=[]
    for a in cand[:900]:
        k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
        if b-a>0x3000 or b-a<0x40: continue
        k0=T.mips_to_68k(a)
        if k0 is None: continue
        its,words,u=assemble(buf,a,b,external=T.mips_to_68k)
        if len(words)<8: continue
        if any(int(d,16) in foreign for it in its for d in re.findall(r'\$([0-9a-f]{4})\(A5\)',it.mn)): continue
        sc,j=e2e.locate_mapped(kw,words,k0)
        if j is None or sc<4: continue
        nf+=1
        E=insts(list(words)); R=insts(list(kw[j:j+len(words)+40]))
        # adresse MIPS de chaque instruction emise (pour relier une paire a sa ZONE)
        w2va=[]
        for it in its: w2va += [it.va]*(size(it)//2)
        Eva=[]; wpos=0
        for e in E:
            Eva.append(w2va[wpos] if wpos < len(w2va) else None); wpos+=len(e)
        # alignement LCS sur les opcodes seuls
        n1,n2=len(E),len(R); dp=[[0]*(n2+1) for _ in range(n1+1)]
        for p in range(n1-1,-1,-1):
            for q in range(n2-1,-1,-1):
                dp[p][q]=dp[p+1][q+1]+1 if E[p][0]==R[q][0] else max(dp[p+1][q],dp[p][q+1])
        p=q=0
        while p<n1 and q<n2:
            if E[p][0]==R[q][0]:
                de=disp_of(E[p]); dr=disp_of(R[q])
                if de and dr and de[0]==dr[0] and de[1]==dr[1] and len(E[p])==len(R[q]):
                    # DIFFERENCE SIGNEE (et non XOR) : un champ long qui commence a 2 mod 4
                    # donne +2/-2 qui, exprime en XOR, depasse 3 et etait ELIMINE a tort
                    dd=((dr[2]-de[2]+0x8000)&0xffff)-0x8000
                    if -3<=dd<=3:
                        sure = (p>0 and q>0 and E[p-1]==R[q-1]) and (p+1<n1 and q+1<n2 and E[p+1]==R[q+1])
                        pairs.append((de[0],de[1],de[2],dd,a,b,j*2,len(words)*2,sure,Eva[p]))
                        tab[(de[0],'A%d'%de[1],dd)]+=1
                        ex.setdefault((de[0],'A%d'%de[1],dd),(de[2],dr[2]))
                p+=1; q+=1
            elif dp[p+1][q]>=dp[p][q+1]: p+=1
            else: q+=1
    print("fonctions alignees : %d\n"%nf)
    print("taille  base     -3    -2    -1     0    +1    +2    +3   (68K - hote)")
    for sz in 'BWL':
        for r in ('A0','A1','A2','A3','A4','A5','A6'):
            row=[tab[(sz,r,x)] for x in range(-3,4)]
            if sum(row)>=5: print("  %s     %s  %5d %5d %5d %5d %5d %5d %5d"%(sz,r,*row))
    json.dump(pairs,open(os.path.join(D,"layout_pairs.json"),"w"))
    print("\nexemples :",{k:('%04x->%04x'%v) for k,v in list(ex.items())[:10]})
