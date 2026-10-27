#!/usr/bin/env python3
"""MODELE TYPE (HANDOFF §44) : chaque champ est range comme un compilateur C petit-boutiste le
ferait selon son type (convention Capcom PS2, cf. structs.h de SF III) :
  u8    : octet a la meme adresse
  s16   : mot meme adresse ; octet interne XOR 1
  s32   : long meme adresse ; mot interne XOR 2 (partie entiere hote = F+2) ; octet XOR 3
  u8[4] lu en long : octets a leur place (valeur longue inversee)
  s16[2] lu en long : mots a leur place (valeur longue a moities echangees)
Le type d'un champ long en F se deduit des acces : octets dominants -> u8[4] ; mots en F+2
dominants -> s32 ; mots en F et F+2 comparables -> s16[2]. Evalue contre layout_pairs.json."""
import sys,os,json,collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import verify
from layout_rule import access_stats

try: CONST=json.load(open(os.path.join(D,"const_evidence.json")))
except Exception: CONST={}
def long_type(acc, reg, F):
    g=lambda d,w: acc.get((reg,d&0xffff),{}).get(w,0)
    ev=CONST.get("%d,%d"%(reg,F))                  # preuve par les constantes (ROM) : prioritaire
    if ev:
        best=max(ev,key=ev.get)
        return {'natif':'s32','octets':'u8x4','moities':'s16x2'}[best]
    l=g(F,4)
    if not l: return None
    b=sum(g(F+k,1) for k in range(4)); w0=g(F,2); w2=g(F+2,2)
    if b > w0+w2: return 'u8x4'
    if w2 > 1.5*w0: return 's32'
    if w0 or w2: return 's16x2'
    return 's32'                                   # long seul : natif

def predict_typed(acc, reg, sz, h):
    """difference (68K - hote) predite"""
    g=lambda d,w: acc.get((reg,d&0xffff),{}).get(w,0)
    if sz=='L': return 0
    if sz=='W':
        for F,dd in ((h-2,-2),(h,+2)):             # h = partie entiere (F+2) ou fraction (F)
            if long_type(acc,reg,F)=='s32': return dd
        return 0
    # octet : conteneur s32 (XOR 3) > conteneur u8[4] (0) > mot s16 (XOR 1) > u8
    for k in range(4):
        F=h-k; t=long_type(acc,reg,F)
        if t=='s32': return 3-2*k
        if t=='u8x4': return 0
        if t=='s16x2': return 1-2*(k&1)
    for k in range(2):                               # mot s16 : il faut une part d'acces mot notable
        F=h-k; w=g(F,2); b=g(F,1)+g(F+1,1)
        if w and w >= 0.1*b: return 1-2*k
    return 0

if __name__=="__main__":
    buf=open(verify.RO3,"rb").read()
    pairs=json.load(open(os.path.join(D,"layout_pairs.json")))
    acc=access_stats(buf)
    loc={}
    for name in ('global','local puis global'):
        ok=collections.Counter(); tot=collections.Counter(); base=collections.Counter(); bad=collections.Counter()
        for sz,reg,h,dd,fa,fb,*_ in pairs:
            a=acc
            if name!='global':
                if (fa,fb) not in loc: loc[(fa,fb)]=access_stats(buf,fa,fb)
                lc=loc[(fa,fb)]
                if any(lc.get((reg,(h&~3)+k)) for k in range(-4,6)):
                    a=collections.defaultdict(collections.Counter)
                    for k2,c in acc.items(): a[k2]=c
                    for k2,c in lc.items(): a[k2]=a[k2]+c       # le local s'AJOUTE (pondere)
                    for k2,c in lc.items(): a[k2]=a[k2]+c
            pr=predict_typed(a,reg,sz,h); tot[sz]+=1; base[sz]+=dd==0; ok[sz]+=pr==dd
            if pr!=dd: bad[(reg,h,sz,dd,pr)]+=1
        print("TYPE (%-18s) B %3.0f%%  W %3.0f%%  L %3.0f%% | global %.1f%%   [identite : %.1f%%]"%(name,
              *(100*ok[s]/max(1,tot[s]) for s in 'BWL'),100*sum(ok.values())/sum(tot.values()),
              100*sum(base.values())/sum(tot.values())))
        print("  echecs les plus frequents (registre, hote, taille, reel, predit) :")
        for k,c in bad.most_common(10): print("    A%d $%x.%s  reel %+d  predit %+d   x%d"%(k+(c,)))
