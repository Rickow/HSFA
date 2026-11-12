#!/usr/bin/env python3
"""VERS QUOI POINTE CHAQUE REGISTRE D'ADRESSE, a chaque acces (analyse de provenance).

Pourquoi : la disposition memoire du recompilateur depend de la ZONE pointee (RAM de
travail : champs 16.16 en long natif ; memoire video : mots seulement ; donnees ROM...).
Un meme (registre, deplacement) change de sens selon la zone.

Zones (adresses hote) : 0x90xxxx = RAM 68K $FFxxxx ; 0x91..0x94xxxx = memoire video CPS2
emulee ; 0x40..0x8fxxxx = donnees ROM relogees dans le module ; le reste : inconnu.

1. Intra-fonction : pour chaque An, sa provenance courante : constante (-> zone), copie
   d'un autre An, pointeur lu en memoire ('charge'), ou PARAMETRE (valeur a l'entree).
2. Inter-fonctions : la zone d'un parametre = union des zones fournies par les appelants
   (point fixe).
Approximation assumee : parcours LINEAIRE de chaque fonction (pas de flot de controle).
"""
import sys, os, json, bisect, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify
from mips import decode, CODE0, CODE1

def zone_of(v):
    z=v>>16
    if z==0x90: return 'RAM'
    if 0x91<=z<=0x94: return 'VIDEO'
    if 0x40<=z<=0x8f: return 'ROMDATA'
    return 'AUTRE'

def analyse(buf, starts):
    """rend : acces[va] = (n, provenance) ; appels = [(f_appelant, cible, {n: prov})]"""
    access={}; calls=[]
    for k,f in enumerate(starts):
        g=starts[k+1] if k+1<len(starts) else CODE1
        A={n:('param',f,n) for n in range(7)}          # provenance des slots An
        A[5]=('zone','RAM')        # A5 est fixe pour tout le jeu (= $FF8000, vu en direct)
        reg={}                                          # registre MIPS -> provenance
        lu={}
        for x in decode(buf,f,g):
            m=x.m
            if m=='lui': lu[x.rt]=x.imm; reg.pop(x.rt,None); continue
            if m in ('addiu','ori') and x.rs in lu and x.rs!=0:
                v=((lu[x.rs]<<16)+(x.simm if m=='addiu' else x.imm))&0xffffffff
                reg[x.rt]=('zone',zone_of(v),v); lu.pop(x.rt,None); continue
            # conversion d'adresse du MOVEA : '+ 0x900000' (lui 0x90 ; addu) = RAM 68K
            if m in ('addu','daddu') and 0x90 in (lu.get(x.rs), lu.get(x.rt)):
                reg[x.rd]=('zone','RAM',0x900000); continue
            # table d'aiguillage : const + index -> lw -> jalr
            if m in ('addu','daddu') and (reg.get(x.rs,('',))[0]=='zone' or reg.get(x.rt,('',))[0]=='zone'):
                c=reg.get(x.rs) if reg.get(x.rs,('',))[0]=='zone' else reg.get(x.rt)
                reg[x.rd]=('tbladdr',c[2]); continue
            if m=='lw' and reg.get(x.rs,('',))[0]=='tbladdr' and x.simm==0:
                reg[x.rt]=('tblent',reg[x.rs][1]); continue
            if m=='jalr':
                p=reg.get(x.rs,('',))
                if p[0]=='zone':                         # veneer : saut vers une constante
                    calls.append((f, p[2]-T.RUNTIME_BASE, dict(A)))
                elif p[0]=='tblent':                     # aiguillage : toutes les cibles
                    for e in T.read_jump_table(buf,p[1]): calls.append((f, e-T.RUNTIME_BASE, dict(A)))
                reg.pop(2,None); reg.pop(3,None); continue
            if m=='lw' and lu.get(x.rs)==0x7000 and 0x1100<=x.imm<0x111c:
                reg[x.rt]=('slot',(x.imm-0x1100)//4); lu.pop(x.rt,None); continue
            if m=='addiu' and reg.get(x.rs) and reg[x.rs][0]=='slot':
                reg[x.rt]=reg[x.rs]; continue                       # An + deplacement
            if m=='sw' and lu.get(x.rs)==0x7000 and 0x1100<=x.imm<0x111c:
                n=(x.imm-0x1100)//4; p=reg.get(x.rt)
                if p and p[0]=='zone': A[n]=('zone',p[1])
                elif p and p[0]=='slot': A[n]=A[p[1]]
                elif p and p[0]=='charge': A[n]=('zone','CHARGE')
                else: A[n]=('zone','INCONNU')
                continue
            if m in ('lb','lbu','lh','lhu','lw','sb','sh','sw') and reg.get(x.rs) and reg[x.rs][0]=='slot':
                n=reg[x.rs][1]; access[x.va]=(n,A[n])
                if m=='lw': reg[x.rt]=('charge',)            # pointeur lu en memoire
                continue
            if m=='jal':
                calls.append((f, x.tgt-T.RUNTIME_BASE, dict(A)))
                reg.pop(2,None); reg.pop(3,None); continue
            d=x.rt if m in ('lb','lbu','lh','lhu','lw','andi','slti','sltiu','addiu') else (x.rd if x.op==0 else None)
            if d is not None: reg.pop(d,None); lu.pop(d,None)
    return access, calls

def resolve(access, calls, starts, rounds=8):
    """zones des parametres par point fixe inter-fonctions"""
    entry=collections.defaultdict(set)                  # (f,n) -> {zones}
    for _ in range(rounds):
        changed=False
        for f,tgt,A in calls:
            for n,p in A.items():
                zs = {p[1]} if p[0]=='zone' else set(entry.get((p[1],p[2]),()))
                new=zs-entry[(tgt,n)]
                if new: entry[(tgt,n)]|=new; changed=True
        if not changed: break
    out={}
    for va,(n,p) in access.items():
        if p[0]=='zone': out[va]=(n,frozenset([p[1]]))
        else: out[va]=(n,frozenset(entry.get((p[1],p[2]),()) or {'PARAM?'}))
    return out

if __name__=="__main__":
    buf=open(verify.RO3,"rb").read()
    F=json.load(open(os.path.join(D,"families.json"))); starts=F["starts"]
    access,calls=analyse(buf,starts)
    res=resolve(access,calls,starts)
    c=collections.Counter()
    for va,(n,zs) in res.items():
        c[('A%d'%n, '/'.join(sorted(zs)) if len(zs)<=2 else 'MULTIPLE')]+=1
    print("acces memoire via An : %d"%len(res))
    for r in ('A0','A1','A2','A3','A4','A5','A6'):
        row=[(z,v) for (rr,z),v in c.items() if rr==r]
        row.sort(key=lambda t:-t[1])
        print("  %s : %s"%(r,', '.join('%s %d'%t for t in row[:6])))
    json.dump({"%x"%va:[n,sorted(zs)] for va,(n,zs) in res.items()},open(os.path.join(D,"regions.json"),"w"))
    print("-> regions.json")
