#!/usr/bin/env python3
"""Verification INDEPENDANTE d'une carte, avec temoin aleatoire.

Le signal qui a servi a CONSTRUIRE la carte (les constantes) ne peut pas servir a
la valider. On valide donc avec un signal different : on TRADUIT le MIPS en 68000
et on compare les OPCODES produits aux opcodes reels de la ROM a l'endroit predit.

Indispensable : un TEMOIN. On refait la meme mesure a des offsets 68K tires au
hasard. Sans temoin on ne sait pas si 30 % d'identite est bon ou si c'est le bruit
de fond (deux flux 68000 quelconques partagent beaucoup d'opcodes courants).
"""
import sys, os, json, struct, random
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate, m68k

RO3="<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin"
K68="<workspace>/work/cps2/sfa3_prog.bin"

def ops_at(k68, off, count):
    n=len(k68)//2; w=struct.unpack('>%dH'%n,k68[:n*2])
    out=[]; i=off//2
    while i<n and len(out)<count:
        r=m68k.decode_one(w,i,n)
        if r is None: i+=1; continue
        out.append(w[i]); i+=r[0]
    return out

# JSR (4eb9) et RTS (4e75) sont presents partout dans n'importe quel flux 68000 :
# les compter gonfle le temoin et rend le verificateur aveugle. Mesure montrant le
# probleme : sur l'ensemble de la carte ils representent 46 % des opcodes emis, et
# le temoin monte alors a 11 % au lieu de 0 %. On ne score que l'INFORMATIF.
BANAL = {0x4eb9, 0x4e75, 0x0000}
def informative(seq): return [x for x in seq if x not in BANAL]

def score(emitted, real):
    """alignement gloutonne tolerant : combien d'opcodes emis se retrouvent dans
    l'ordre dans le flux reel (une insertion/suppression ne casse pas tout)."""
    j=0; hit=0
    for e in emitted:
        k=j
        while k<min(len(real),j+4):
            if real[k]==e: hit+=1; j=k+1; break
            k+=1
    return hit/max(1,len(emitted))

if __name__=="__main__":
    mapf=sys.argv[1] if len(sys.argv)>1 else "map_chain2.json"
    N=int(sys.argv[2]) if len(sys.argv)>2 else 40
    ro3=open(RO3,"rb").read(); k68=open(K68,"rb").read()
    blocks=json.load(open(os.path.join(D,mapf)))["blocks"]
    blocks=[b for b in blocks if b["m68k"][1]>b["m68k"][0]]
    random.seed(1)
    good=0; tot=0; gs=[]; rs=[]
    for b in sorted(blocks,key=lambda z:-z["n"])[:N]:
        m0,m1=b["mips"]; k0,k1=b["m68k"]
        # 3 sondes par bloc : debut, milieu, fin
        for f in (0.05,0.5,0.9):
            mv=int(m0+(m1-m0)*f) & ~3
            kv=(k0+round((mv-m0)*(k1-k0)/(m1-m0))) & ~1
            try: ins,_=translate.translate(ro3,mv,mv+0x600)
            except Exception as e: print('!!! erreur de traduction @%x : %r'%(mv,e)); continue
            em=informative([w[0] for _,_,w in ins if w])[:24]
            if len(em)<6: continue
            # on autorise un petit recalage (+-24 mots) : l'interpolation lineaire
            # n'est pas exacte a l'instruction pres
            best=0
            for d in range(-24,26,2):
                best=max(best,score(em,informative(ops_at(k68,max(0,kv+d),3*len(em)))))
            ctrl=max(score(em,informative(ops_at(k68,random.randrange(0,0xf0000)&~1,3*len(em))))
                     for _ in range(6))
            gs.append(best); rs.append(ctrl); tot+=1
            if best>ctrl+0.15: good+=1
    gs.sort(); rs.sort()
    print("sondes exploitables : %d"%tot)
    if tot:
        print("  identite d'opcodes a l'endroit PREDIT  : median %.0f%%  moyenne %.0f%%"%(
            100*gs[len(gs)//2],100*sum(gs)/len(gs)))
        print("  identite au TEMOIN (offsets au hasard) : median %.0f%%  moyenne %.0f%%"%(
            100*rs[len(rs)//2],100*sum(rs)/len(rs)))
        print("  sondes nettement au-dessus du temoin   : %d/%d (%.0f%%)"%(
            good,tot,100*good/tot))
