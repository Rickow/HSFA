#!/usr/bin/env python3
"""Carte MIPS<->68K par TRADUCTION PUIS RECHERCHE (signal d'OPCODES).

Les cartes precedentes n'alignaient que les CONSTANTES : un signal rare
(0x100..0xfffe seulement) qui laisse muettes toutes les fonctions sans immediat
distinctif. Ici on exploite le traducteur : on TRADUIT le MIPS en 68000, puis on
aligne la suite des OPCODES produits avec la suite des opcodes reels de la ROM.

Le signal est beaucoup plus dense (un opcode par instruction traduite, contre une
constante de temps en temps) et beaucoup plus structurel (un opcode 68000 encode
l'operation, la taille ET le mode d'adressage).

Meme machinerie d'alignement que chain.py : k-mers -> couples rares -> extraction
iterative de sous-suites croissantes -> blocs colineaires. Couverture mesuree en
UNION (jamais en somme : les blocs se chevauchent).
"""
import sys, struct, collections, bisect, json, os
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import CODE0, CODE1
from chain import lis
import m68k

RO3="<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin"
K68=os.environ.get("K68","<workspace>/work/cps2/sfa3_prog.bin")
CODE_END=0x100000                      # seul le 1er Mo est du code (zone chiffree)

def opseq_68k(buf, end=CODE_END):
    """suite (offset, mot d'opcode) des instructions reelles de la ROM 68000."""
    n=min(len(buf),end)//2
    w=struct.unpack('>%dH'%n, buf[:n*2])
    out=[]; i=0; bad=0
    while i<n:
        r=m68k.decode_one(w,i,n)
        if r is None: bad+=1; i+=1; continue
        out.append((i*2, w[i])); i+=r[0]
    return out,bad

def opseq_mips(buf, a, b, chunk=0x8000):
    """suite (adresse MIPS, mot d'opcode 68000 emis) via le traducteur d'idiomes.

    On traduit par tranches : le traducteur suit l'etat des registres, une tranche
    trop grande n'apporte rien (l'etat est reinitialise a chaque fonction de fait)
    et une tranche trop petite perd les idiomes a cheval sur la frontiere."""
    import translate
    out=[]
    x=a
    while x<b:
        y=min(x+chunk,b)
        try: ins,_=translate.translate(buf,x,y)
        except Exception as e: print('!!! erreur de traduction @%x : %r'%(x,e)); ins=[]
        for va,mn,ws in ins:
            if ws: out.append((va,ws[0]))
        x=y
    return out

def kmers(seq,k):
    d=collections.defaultdict(list)
    for i in range(len(seq)-k+1):
        d[tuple(v for _,v in seq[i:i+k])].append(i)
    return d

def union_cov(blocks,key):
    iv=sorted((b[key][0],b[key][1]) for b in blocks if b[key][1]>b[key][0])
    u=[]
    for a,b in iv:
        if u and a<=u[-1][1]: u[-1]=(u[-1][0],max(u[-1][1],b))
        else: u.append((a,b))
    return sum(b-a for a,b in u), u

if __name__=="__main__":
    K=int(sys.argv[1]) if len(sys.argv)>1 else 6
    AMB=int(sys.argv[2]) if len(sys.argv)>2 else 4
    ro3=open(RO3,"rb").read(); k68=open(K68,"rb").read()
    ks,bad=opseq_68k(k68)
    print("opcodes 68K reels : %d  (%d mots indecodables)"%(len(ks),bad))
    ms=opseq_mips(ro3,CODE0,CODE1)
    print("opcodes 68000 emis par le traducteur : %d   (k=%d, AMB=%d)"%(len(ms),K,AMB))
    km=kmers(ms,K); kk=kmers(ks,K)
    pairs=[]; uniq=0
    for key,mi in km.items():
        ki=kk.get(key)
        if not ki: continue
        if len(mi)*len(ki)>AMB: continue
        uniq+=1
        for p in mi:
            for q in ki: pairs.append((ms[p][0], ks[q][0]))
    print("empreintes rares appariees : %d  ->  %d couples"%(uniq,len(pairs)))
    if not pairs: sys.exit("aucun couple : signal trop pauvre a ce k")
    remaining=set(pairs); blocks=[]
    for _ in range(80):
        if not remaining: break
        ch=lis(list(remaining))
        if len(ch)<4: break
        blocks.append(ch); remaining-=set(ch)
    print("blocs colineaires : %d"%len(blocks))
    out={"blocks":[]}
    for ch in blocks:
        out["blocks"].append({"mips":[ch[0][0],ch[-1][0]],
                              "m68k":[ch[0][1],ch[-1][1]],"n":len(ch)})
    cov,_=union_cov(out["blocks"],"m68k")
    raw=sum(b["m68k"][1]-b["m68k"][0] for b in out["blocks"])
    print("\nCOUVERTURE 68K (union) : %d o  (%.1f%% de la zone code)"%(cov,100*cov/CODE_END))
    print("  [somme brute : %.1f%% - surcomptage %.1fx]"%(100*raw/CODE_END,raw/max(1,cov)))
    for b in sorted(out["blocks"],key=lambda z:-z["n"])[:8]:
        r=(b["mips"][1]-b["mips"][0])/max(1,b["m68k"][1]-b["m68k"][0])
        print("   %4d pts  MIPS %07x..%07x <-> 68K %06x..%06x  ratio %.1fx"%(
            b["n"],b["mips"][0],b["mips"][1],b["m68k"][0],b["m68k"][1],r))
    json.dump(out,open(os.path.join(D,"map_opcodes.json"),"w"))
    print("carte exportee -> map_opcodes.json")
