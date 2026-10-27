#!/usr/bin/env python3
"""RECENSEMENT des idiomes non traduits, sur TOUT le binaire.

Le compteur 'unknown' du traducteur ne dit presque rien : il consomme en silence
beaucoup d'instructions pour suivre l'etat. Critere plus propre : toute instruction
68000 laisse un EFFET visible dans le MIPS recompile :
  - ecriture d'un registre 68K   -> store vers un slot 0x70001100..0x1140
  - ecriture memoire 68K         -> store via une autre base
  - branchement conditionnel     -> beq/bne/bltz/bgez/blez/bgtz
  - appel / retour / saut        -> jal / jalr / jr
Un EFFET sans instruction 68000 emise a cet endroit = une instruction 68K MANQUEE.
On classe les manques par (type d'effet, provenance de la base d'adressage) :
c'est la liste de travail du traducteur, du plus frequent au moins frequent.
"""
import sys, os, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, CODE0, CODE1
import translate

import os as _os
# module a recenser : ro3 (SFA3) par defaut ; MODULE=ro5 (Upper) ou ro9 (Hyper)
RO3="<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin"%_os.environ.get("MODULE","ro3")
CHUNK=0x4000
ERREURS=[]
BR=('beq','bne','bltz','bgez','blez','bgtz','beql','bnel')

def slot(off):
    n=translate.slot_name(off)
    if n: return "%s%d"%n
    return {0x1150:'RES',0x1158:'NFLG'}.get(off,'slot?%x'%off)

def census(buf,a,b):
    emitted=set()
    try:
        out,_=translate.translate(buf,a,b)
        emitted={va for va,_,ws in out}          # une entree sans mot = effet traite (ex. RTS absorbe)
    except Exception as e:
        # JAMAIS silencieux : une exception viderait la tranche sans prevenir
        ERREURS.append((a,repr(e)))
    prov={}          # registre MIPS -> provenance de sa valeur
    miss=collections.Counter(); hit=collections.Counter()
    for ins in decode(buf,a,b):
        m=ins.m; key=None
        if m=='lui': prov[ins.rt]=('lui',ins.imm)
        elif m in ('lw','lh','lb','lhu','lbu','ld') and prov.get(ins.rs)==('lui',0x7000):
            prov[ins.rt]=('val',slot(ins.imm))
        elif m in ('addiu','addu','daddu','or') and ins.rt!=0:
            p=prov.get(ins.rs)
            prov[ins.rt if m=='addiu' else ins.rd]=(('addr',p[1]) if p and p[0] in ('val','addr') else None)
        elif m in ('lw','lh','lb','lhu','lbu','ld'):
            prov[ins.rt]=None
        if m in ('sb','sh','sw','sd'):
            # les stores via sp sont TOUS des sauvegardes de registres MIPS (ra, s0-s7 :
            # 16 087, verifie) - aucun n'est une ecriture 68K. Les compter gonflait la
            # categorie 'base=?' de 9 933 faux manques (les 'sd ra,0(sp)' des prologues).
            if ins.rs==29: continue
            p=prov.get(ins.rs)
            if p==('lui',0x7000):
                s=slot(ins.imm)
                if s in ('RES','NFLG'): continue          # drapeaux : pas une instruction
                key=('ecrit-registre',s[0])
            elif p and p[0] in ('val','addr'):
                key=('ecrit-memoire','base=%s'%p[1])
            else:
                key=('ecrit-memoire','base=?')
        elif m in BR: key=('branchement',m)
        elif m=='jal': key=('appel','jal')
        elif m=='jalr': key=('appel','jalr (indirect)')
        elif m=='jr': key=('retour/saut','jr ra' if ins.rs==31 else 'jr (table de sauts)')
        if key is None: continue
        ok=any(v in emitted for v in (ins.va-8,ins.va-4,ins.va,ins.va+4))
        (hit if ok else miss)[key]+=1
    return hit,miss

if __name__=="__main__":
    import struct as _st
    _b=open(RO3,'rb').read(16)
    # bornes du 68K propres au module : fin d'apres l'en-tete, debut = apres le Z80
    a0=int(sys.argv[1],16) if len(sys.argv)>1 else int(_os.environ.get("CODE0","%x"%CODE0),16)
    a1=int(sys.argv[2],16) if len(sys.argv)>2 else _st.unpack_from('<I',_b,12)[0]
    buf=open(RO3,"rb").read()
    H=collections.Counter(); M=collections.Counter()
    x=a0
    while x<a1:
        h,mi=census(buf,x,min(x+CHUNK,a1)); H+=h; M+=mi; x+=CHUNK
    th=sum(H.values()); tm=sum(M.values())
    if ERREURS:
        print("!!! %d TRANCHES EN ERREUR (resultats faux) : %s"%(len(ERREURS),ERREURS[:3]))
    print("zone MIPS %07x..%07x"%(a0,a1))
    print("points d'effet : %d   traduits : %d (%.1f%%)   MANQUES : %d (%.1f%%)\n"%(
        th+tm,th,100*th/max(1,th+tm),tm,100*tm/max(1,th+tm)))
    print("%-18s %-26s %8s %8s %7s %7s"%("effet","detail","manques","traduits","%trad","%manq."))
    for k,c in M.most_common(30):
        h=H.get(k,0)
        print("%-18s %-26s %8d %8d %6.0f%% %6.1f%%"%(k[0],k[1],c,h,100*h/(c+h),100*c/tm))
