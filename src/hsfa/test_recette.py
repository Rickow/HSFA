#!/usr/bin/env python3
"""PREUVE par simulation que la recette 'mode cps2' reproduit exactement ce que le code
PS2 voit en memoire.

Deux memoires cote a cote :
  - PS2 : petit-boutiste ; le code MIPS fait lb/lh/lw/sb/sh/sw a l'adresse h ;
  - 68K : gros-boutiste ; le code traduit fait, pour la meme operation :
        mot  : MOVE.W a l'adresse h
        octet: MOVE.B a l'adresse h XOR 1
        long : MOVE.L a l'adresse h, avec SWAP de la valeur au passage registre<->memoire
Des milliers d'ecritures/lectures aleatoires qui se CHEVAUCHENT (octets dans des mots,
mots dans des longs, longs a 2 mod 4). Toute lecture doit rendre la meme valeur."""
import random, struct
N=256
def ps2_w(m,h,sz,v):  m[h:h+sz]=v.to_bytes(sz,'little')
def ps2_r(m,h,sz):    return int.from_bytes(m[h:h+sz],'little')
def swap32(v): return ((v&0xffff)<<16)|((v>>16)&0xffff)
def k68_w(m,h,sz,v):
    if sz==1: m[h^1]=v
    elif sz==2: m[h:h+2]=v.to_bytes(2,'big')
    else: m[h:h+4]=swap32(v).to_bytes(4,'big')          # SWAP puis MOVE.L
def k68_r(m,h,sz):
    if sz==1: return m[h^1]
    if sz==2: return int.from_bytes(m[h:h+2],'big')
    return swap32(int.from_bytes(m[h:h+4],'big'))        # MOVE.L puis SWAP
random.seed(1)
P=bytearray(N); K=bytearray(N); ok=bad=0; kinds={1:0,2:0,4:0}
for t in range(200000):
    sz=random.choice((1,2,4)); h=random.randrange(0,N-4)
    if sz>1: h&=~1                                        # 68K : mots/longs a adresse paire
    if random.random()<0.5:
        v=random.getrandbits(8*sz); ps2_w(P,h,sz,v); k68_w(K,h,sz,v)
    else:
        a,b=ps2_r(P,h,sz),k68_r(K,h,sz); kinds[sz]+=1
        if a==b: ok+=1
        else:
            bad+=1
            if bad<5: print("ECART taille %d adresse %#x : PS2 %x / 68K %x"%(sz,h,a,b))
print("lectures comparees : %d (octets %d, mots %d, longs %d) -> identiques : %d, ecarts : %d"%(
    ok+bad,kinds[1],kinds[2],kinds[4],ok,bad))
# le cas reel observe en jeu : X ecrit en long a +$10, partie entiere relue en mot a +$12
P=bytearray(N); K=bytearray(N); x=0x02200000
ps2_w(P,0x10,4,x); k68_w(K,0x10,4,x)
print("cas reel (X = 0x%08x ecrit en long a +$10) : mot relu a +$12 -> PS2 %#x, 68K %#x"%(x,ps2_r(P,0x12,2),k68_r(K,0x12,2)))
