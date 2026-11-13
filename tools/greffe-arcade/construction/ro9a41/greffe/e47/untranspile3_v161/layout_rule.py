#!/usr/bin/env python3
"""Evalue des REGLES de prediction de la disposition memoire contre les paires
mesurees (layout_pairs.json : taille, registre, deplacement hote, XOR reel)."""
import sys, os, json, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, CODE0, CODE1
import verify

def access_stats(buf, a=CODE0, b=CODE1):
    """largeurs d'acces par (registre d'adresse, deplacement hote), sur [a,b)."""
    acc=collections.defaultdict(collections.Counter); base={}
    W={'lb':1,'lbu':1,'sb':1,'lh':2,'lhu':2,'sh':2,'lw':4,'sw':4}
    for x in decode(buf,a,b):
        if x.m=='lw' and 0x1100<=x.imm<0x111c: base[x.rt]=((x.imm-0x1100)//4,0); continue
        if x.m=='addiu' and base.get(x.rs): b=base[x.rs]; base[x.rt]=(b[0],(b[1]+x.simm)&0xffff); continue
        if x.m in W and base.get(x.rs):
            b=base[x.rs]; acc[(b[0],(b[1]+x.simm)&0xffff)][W[x.m]]+=1
        d=x.rt if x.m in ('lb','lbu','lh','lhu','lw','addiu','andi','ori','lui') else (x.rd if x.op==0 else None)
        if d and d in base: base.pop(d,None)
    return acc

def predict(rule, acc, reg, sz, d):
    g4=d&~3; g2=d&~1
    L=sum(acc.get((reg,g4),{}).get(4,0) for _ in [0])
    Wd=acc.get((reg,g2),{}).get(2,0)
    Wg=sum(acc.get((reg,g4+k),{}).get(2,0) for k in (0,2))
    B=sum(acc.get((reg,g4+k),{}).get(1,0) for k in range(4))
    if rule=='identite': mode='B'
    elif rule=='long_si_lw':  mode='L' if L else ('W' if Wd else 'B')
    elif rule=='majorite':
        m=max((('L',L*4),('W',Wg*2),('B',B)),key=lambda t:t[1]); mode=m[0]
    elif rule=='long_si_lw_domine':
        mode='L' if L and L*4>=B else ('W' if Wd and Wd*2>=acc.get((reg,g2),{}).get(1,0) else 'B')
    # XOR predit selon le mode de stockage et la taille de l'acces
    if mode=='L': return {'L':0,'W':2,'B':3}[sz]
    if mode=='W': return {'L':0,'W':0,'B':1}[sz]
    return 0

if __name__=="__main__" and len(sys.argv)==1:
    buf=open(verify.RO3,"rb").read()
    acc=access_stats(buf)
    pairs=json.load(open(os.path.join(D,"layout_pairs.json")))
    loc_cache={}
    def local(a,b):
        if (a,b) not in loc_cache: loc_cache[(a,b)]=access_stats(buf,a,b)
        return loc_cache[(a,b)]
    for rule in ('identite','majorite','long_si_lw_domine','LOCAL puis global'):
        ok=collections.Counter(); tot=collections.Counter()
        for sz,reg,d,x,fa,fb,*_ in pairs:
            tot[sz]+=1
            if rule=='LOCAL puis global':
                lc=local(fa,fb); g4=d&~3
                has=any(lc.get((reg,g4+k)) for k in range(4))
                pr=predict('long_si_lw_domine', lc if has else acc, reg, sz, d)
            else: pr=predict(rule,acc,reg,sz,d)
            ok[sz]+= pr==x
        print("%-20s  B %3.0f%%   W %3.0f%%   L %3.0f%%   | global %.1f%%  (%d paires)"%(rule,
              *(100*ok[s]/max(1,tot[s]) for s in 'BWL'), 100*sum(ok.values())/sum(tot.values()), sum(tot.values())))

# ---------------------------------------------------------------------------
# REGLE RELATIVE AU CHAMP (2026-09-27) : un champ long qui commence en F (adresse
# 68K = adresse hote, alignement 2 suffit sur 68K) est stocke en long natif LE a
# partir de F. Donc mot hote F -> 68K F+2 ; mot hote F+2 -> 68K F ; octet hote F+k ->
# 68K F+3-k. Un champ mot en F : octet hote F -> 68K F+1, F+1 -> 68K F.
# Decouvert en RAM vivante : les pointeurs de routine stockes en long natif sont a
# des positions 2 mod 4 (jamais 4-alignees) => l'ancienne regle 'XOR 2 sur le groupe
# aligne 4' etait fausse pour ces champs.
def predict_field(acc, reg, sz, h, mode='dominant'):
    """rend la difference (68K - hote) predite"""
    if sz=='L': return 0
    g=lambda d,w: acc.get((reg,d&0xffff),{}).get(w,0)
    if sz=='W':
        own=g(h,2)
        c0,c2=g(h,4),g(h-2,4)
        if mode=='dominant':
            if c0 and c0>=c2 and c0*1>=own*0.25: return +2
            if c2 and c2*1>=own*0.25: return -2
            return 0
        if c0>=c2 and c0: return +2
        if c2: return -2
        return 0
    # octet
    best=None
    for k in range(4):
        F=h-k; c=g(F,4)
        if c and (best is None or c>best[0]): best=(c, 3-2*k)
    if best: return best[1]
    for k in range(2):
        F=h-k
        if g(F,2): return 1-2*k
    return 0

if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="champ":
    buf=open(verify.RO3,"rb").read(); acc=access_stats(buf)
    pairs=json.load(open(os.path.join(D,"layout_pairs.json")))
    for mode in ('toute','dominant'):
        ok=collections.Counter(); tot=collections.Counter(); base=collections.Counter()
        for sz,reg,h,dd,fa,fb,*_ in pairs:
            tot[sz]+=1; base[sz]+= dd==0
            ok[sz]+= predict_field(acc,reg,sz,h,mode)==dd
        print("RELATIVE AU CHAMP (%-8s) B %3.0f%%  W %3.0f%%  L %3.0f%% | global %.1f%%   [sans correction : %.1f%%]  (%d paires)"%(mode,
              *(100*ok[s]/max(1,tot[s]) for s in 'BWL'),100*sum(ok.values())/sum(tot.values()),
              100*sum(base.values())/sum(tot.values()),sum(tot.values())))

def rom_access_stats(k68):
    """largeurs d'acces du CODE 68K d'origine par (registre, deplacement 68K) : toutes
    les instructions a EA (d16,An) - MOVE (source et destination), TST, CLR, CMP, ADD..."""
    import struct, m68k
    n=0x100000//2; w=struct.unpack('>%dH'%n,k68[:0x100000]); i=0
    acc=collections.defaultdict(collections.Counter)
    while i<n:
        r=m68k.decode_one(w,i,n)
        if r is None: i+=1; continue
        L,ext=r; op=w[i]; h=op>>12
        disps=[w[idx] for idx,kind in ext if kind=='disp' and idx<n]
        eas=[]
        if h in (1,2,3):
            sz={1:1,3:2,2:4}[h]
            eas=[(op&0x3f,sz), ((((op>>6)&7)<<3)|((op>>9)&7),sz)]
        elif (op&0xff00) in (0x4a00,0x4200,0x4400,0x4600,0x0c00,0x0000,0x0200,0x0400,0x0600,0x0a00) and ((op>>6)&3)<3:
            eas=[(op&0x3f,{0:1,1:2,2:4}[(op>>6)&3])]
        elif (op&0xf000) in (0x5000,0x9000,0xd000,0xb000,0xc000,0x8000) and ((op>>6)&3)<3:
            eas=[(op&0x3f,{0:1,1:2,2:4}[(op>>6)&3])]
        k=0
        for ea,sz in eas:
            if (ea&0x38)==0x28 and k<len(disps):
                acc[(ea&7,disps[k])][sz]+=1
            if (ea&0x38) in (0x28,0x30) or ea in (0x38,0x39,0x3a,0x3b,0x3c): k+=1
        i+=L
    return acc

def predict_rom(racc, reg, sz, d68):
    """disposition predite par les largeurs du code 68K : rend (hote - 68K)"""
    if sz=='L': return 0
    g=lambda d,w: racc.get((reg,d&0xffff),{}).get(w,0)
    if sz=='W':
        if g(d68,4): return +2          # moitie haute d'un long en d68 -> hote d68+2
        if g(d68-2,4): return -2        # moitie basse d'un long en d68-2 -> hote d68-2
        return 0
    for k in range(4):
        if g(d68-k,4): return (3-2*k)
    for k in range(2):
        if g(d68-k,2): return (1-2*k)
    return 0

if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="rom":
    k68=open(verify.K68,"rb").read(); racc=rom_access_stats(k68)
    pairs=json.load(open(os.path.join(D,"layout_pairs.json")))
    ok=collections.Counter(); tot=collections.Counter(); base=collections.Counter(); miss=collections.Counter()
    for sz,reg,h,dd,fa,fb,*_ in pairs:
        d68=(h+dd)&0xffff
        tot[sz]+=1; base[sz]+= dd==0
        pr=predict_rom(racc,reg,sz,d68)
        ok[sz]+= pr==-dd
        if pr!=-dd: miss[(sz,pr,-dd)]+=1
    print("REGLE 'largeurs du CODE 68K' : B %3.0f%%  W %3.0f%%  L %3.0f%% | global %.1f%%   [sans correction %.1f%%]"%(
        *(100*ok[s]/max(1,tot[s]) for s in 'BWL'),100*sum(ok.values())/sum(tot.values()),100*sum(base.values())/sum(tot.values())))
    print("erreurs (taille, predit hote-68K, reel) :",', '.join('%s %+d/%+d x%d'%(k[0],k[1],k[2],v) for k,v in miss.most_common(8)))

def rom_access_stats_range(k68, lo, hi):
    """memes statistiques, restreintes a la routine 68K [lo,hi)"""
    import struct, m68k
    n=0x100000//2; w=struct.unpack('>%dH'%n,k68[:0x100000]); i=lo//2
    acc=collections.defaultdict(collections.Counter)
    while i<min(n,hi//2):
        r=m68k.decode_one(w,i,n)
        if r is None: i+=1; continue
        L,ext=r; op=w[i]; h=op>>12
        disps=[w[idx] for idx,kind in ext if kind=='disp' and idx<n]
        eas=[]
        if h in (1,2,3):
            sz={1:1,3:2,2:4}[h]; eas=[(op&0x3f,sz), ((((op>>6)&7)<<3)|((op>>9)&7),sz)]
        elif ((op>>6)&3)<3 and ((op&0xff00) in (0x4a00,0x4200,0x4400,0x4600,0x0c00,0x0000,0x0200,0x0400,0x0600,0x0a00)
                                or (op&0xf000) in (0x5000,0x9000,0xd000,0xb000,0xc000,0x8000)):
            eas=[(op&0x3f,{0:1,1:2,2:4}[(op>>6)&3])]
        k=0
        for ea,sz in eas:
            if (ea&0x38)==0x28 and k<len(disps): acc[(ea&7,disps[k])][sz]+=1
            if (ea&0x38) in (0x28,0x30) or ea in (0x38,0x39,0x3a,0x3b,0x3c): k+=1
        i+=L
    return acc

if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="romlocal":
    k68=open(verify.K68,"rb").read()
    pairs=json.load(open(os.path.join(D,"layout_pairs.json")))
    for marge in (0, 0x100, 0x400):
        ok=collections.Counter(); tot=collections.Counter(); cache={}
        for sz,reg,h,dd,fa,fb,rj,rl in pairs:
            key=(rj,rl)
            if key not in cache: cache[key]=rom_access_stats_range(k68, max(0,rj-marge), rj+rl+marge)
            d68=(h+dd)&0xffff
            tot[sz]+=1; ok[sz]+= predict_rom(cache[key],reg,sz,d68)==-dd
        print("largeurs du code 68K de la ROUTINE (marge %#5x) : B %3.0f%%  W %3.0f%%  L %3.0f%% | global %.1f%%"%(
            marge,*(100*ok[s]/max(1,tot[s]) for s in 'BWL'),100*sum(ok.values())/sum(tot.values())))

def xor_to_signed(h, x):
    return (((h ^ x) - h + 0x8000) & 0xffff) - 0x8000

if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="famille":
    import bisect
    buf=open(verify.RO3,"rb").read(); acc=access_stats(buf)
    F=json.load(open(os.path.join(D,"families.json")))
    fam={int(k,16):int(v,16) for k,v in F["fam"].items()}; starts=F["starts"]
    members=collections.defaultdict(list)
    for s,f in fam.items(): members[f].append(s)
    def fend(s):
        k=bisect.bisect_right(starts,s); return starts[k] if k<len(starts) else CODE1
    fcache={}
    def fam_stats(f):
        if f not in fcache:
            a=collections.defaultdict(collections.Counter)
            for s in members[f]:
                for key,c in access_stats(buf,s,fend(s)).items(): a[key].update(c)
            fcache[f]=a
        return fcache[f]
    def family_of(fa,fb):
        k0=bisect.bisect_left(starts,fa); fs=collections.Counter()
        while k0<len(starts) and starts[k0]<fb:
            if starts[k0] in fam: fs[fam[starts[k0]]]+=1
            k0+=1
        return fs.most_common(1)[0][0] if fs else None
    pairs=json.load(open(os.path.join(D,"layout_pairs.json")))
    rules={
      'aucune correction':           lambda sz,reg,h,f: 0,
      'long domine (global)':        lambda sz,reg,h,f: xor_to_signed(h,predict('long_si_lw_domine',acc,reg,sz,h)),
      'champ (global)':              lambda sz,reg,h,f: predict_field(acc,reg,sz,h),
      'long domine (FAMILLE)':       lambda sz,reg,h,f: xor_to_signed(h,predict('long_si_lw_domine',f,reg,sz,h)) if f else 0,
      'champ (FAMILLE, sinon 0)':    lambda sz,reg,h,f: predict_field(f,reg,sz,h) if f else 0,
      'champ (FAMILLE, sinon glob.)':lambda sz,reg,h,f: predict_field(f if f else acc,reg,sz,h),
    }
    covered=0
    only_sure = len(sys.argv)>2 and sys.argv[2]=="sures"
    if only_sure:
        pairs=[p for p in pairs if len(p)>8 and p[8]]
        dist=collections.Counter((p[0],p[3]) for p in pairs)
        print("PAIRES SURES (voisins identiques des deux cotes) : %d"%len(pairs))
        for szz in 'BWL': print("   %s : %s"%(szz,', '.join('%+d:%d'%(d,dist[(szz,d)]) for d in range(-3,4) if dist[(szz,d)])))
    res={r:(collections.Counter(),collections.Counter()) for r in rules}
    for sz,reg,h,dd,fa,fb,*_ in pairs:
        fid=family_of(fa,fb); fs=fam_stats(fid) if fid is not None else None
        covered+= fs is not None
        for name,fn in rules.items():
            ok,tot=res[name]; tot[sz]+=1; ok[sz]+= fn(sz,reg,h,fs)==dd
    print("paires dont la fonction appartient a une famille : %d / %d\n"%(covered,len(pairs)))
    for name,(ok,tot) in res.items():
        print("  %-30s B %3.0f%%  W %3.0f%%  L %3.0f%% | global %.1f%%"%(name,
              *(100*ok[s]/max(1,tot[s]) for s in 'BWL'),100*sum(ok.values())/sum(tot.values())))

if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="zone":
    import bisect
    buf=open(verify.RO3,"rb").read()
    RG={int(k,16):(v[0],set(v[1])) for k,v in json.load(open(os.path.join(D,"regions.json"))).items()}
    rva=sorted(RG)
    W={'lb':1,'lbu':1,'sb':1,'lh':2,'lhu':2,'sh':2,'lw':4,'sw':4}
    # statistiques de largeur restreintes aux acces dont la zone est la RAM
    accR=collections.defaultdict(collections.Counter); base={}
    for x in decode(buf,CODE0,CODE1):
        if x.m=='lw' and 0x1100<=x.imm<0x111c: base[x.rt]=((x.imm-0x1100)//4,0); continue
        if x.m=='addiu' and base.get(x.rs): b=base[x.rs]; base[x.rt]=(b[0],(b[1]+x.simm)&0xffff); continue
        if x.m in W and base.get(x.rs):
            b=base[x.rs]; z=RG.get(x.va,(None,set()))[1]
            if 'RAM' in z: accR[(b[0],(b[1]+x.simm)&0xffff)][W[x.m]]+=1
        d=x.rt if x.m in ('lb','lbu','lh','lhu','lw','addiu','andi','ori','lui') else (x.rd if x.op==0 else None)
        if d and d in base: base.pop(d,None)
    def zone_at(va, reg):
        """zone de l'acces memoire le plus proche AVANT l'instruction traduite (meme registre)"""
        k=bisect.bisect_right(rva, va)-1
        while k>=0 and va-rva[k]<=0x40:
            n,z=RG[rva[k]]
            if n==reg: return z
            k-=1
        return None
    pairs=[p for p in json.load(open(os.path.join(D,"layout_pairs.json"))) if len(p)>9]
    sure=len(sys.argv)>2 and sys.argv[2]=="sures"
    if sure: pairs=[p for p in pairs if p[8]]
    zc=collections.Counter(); ok=collections.Counter(); ok0=collections.Counter(); tot=collections.Counter()
    for sz,reg,h,dd,fa,fb,rj,rl,sr,va in pairs:
        z=zone_at(va,reg) if va is not None else None
        zk='RAM' if z and 'RAM' in z and len(z)==1 else ('VIDEO/ROM' if z and z<= {'VIDEO','ROMDATA'} else 'autre/inconnu')
        zc[(zk,sz,dd!=0)]+=1
        if zk=='VIDEO/ROM': pr=0
        elif zk=='RAM': pr=xor_to_signed(h,predict('long_si_lw_domine',accR,reg,sz,h))
        else: pr=0
        tot[sz]+=1; ok[sz]+= pr==dd; ok0[sz]+= dd==0
    print("paires %s : %d"%("SURES" if sure else "toutes",len(pairs)))
    for zk in ('RAM','VIDEO/ROM','autre/inconnu'):
        print("   zone %-14s : "%zk+', '.join('%s %s:%d'%(s,'decale' if f else 'identique',zc[(zk,s,f)]) for s in 'BWL' for f in (False,True) if zc[(zk,s,f)]))
    print("REGLE PAR ZONE : B %3.0f%%  W %3.0f%%  L %3.0f%% | global %.1f%%   [sans correction : %.1f%%]"%(
        *(100*ok[s]/max(1,tot[s]) for s in 'BWL'),100*sum(ok.values())/sum(tot.values()),100*sum(ok0.values())/sum(tot.values())))

# ---------------------------------------------------------------------------
# HYPOTHESE H2 (2026-09-27, appuyee par la RAM en direct : positions X/Y des joueurs
# = long natif, partie entiere en +$12/+$16) : un champ long est stocke en long NATIF
# quand le code CALCULE avec lui (addition d'une vitesse, pointeur...). Un long seulement
# RECOPIE tel quel (lw -> sw sans transformation) ne prouve rien : une copie brute
# marche quelle que soit la disposition.
def semantic_long_stats(buf):
    """par (registre, deplacement) : nombre d'acces long 'semantiques' (la valeur lue est
    utilisee dans un calcul, ou la valeur ecrite vient d'un calcul) et de 'copies'."""
    L=list(decode(buf,CODE0,CODE1)); base={}; st=collections.defaultdict(collections.Counter)
    origin={}                                   # registre MIPS -> 'lw' si charge par un lw brut
    for i,x in enumerate(L):
        if x.m=='lw' and 0x1100<=x.imm<0x111c: base[x.rt]=((x.imm-0x1100)//4,0); continue
        if x.m=='addiu' and base.get(x.rs): b=base[x.rs]; base[x.rt]=(b[0],(b[1]+x.simm)&0xffff); continue
        if x.m=='lw' and base.get(x.rs):
            key=(base[x.rs][0],(base[x.rs][1]+x.simm)&0xffff); r=x.rt; kind='copie'
            for y in L[i+1:i+10]:
                uses = r in (y.rs, y.rt) if y.m not in ('lui',) else False
                if y.m in ('sw',) and y.rt==r: kind='copie'; break
                if uses and y.m not in ('sw',): kind='calcul'; break
                if (y.m in ('lw','lh','lb','lui','addiu','addu','andi') and y.rt==r) or (y.op==0 and y.rd==r): break
            st[key][kind]+=1
            origin[x.rt]='lw'
        elif x.m=='sw' and base.get(x.rs) and not (0x1100<=x.imm<0x1160):
            key=(base[x.rs][0],(base[x.rs][1]+x.simm)&0xffff)
            st[key]['copie' if origin.get(x.rt)=='lw' else 'calcul']+=1
        d=x.rt if x.m in ('lb','lbu','lh','lhu','lw','addiu','andi','ori','lui') else (x.rd if x.op==0 else None)
        if d is not None:
            if d in base and not (x.m=='lw' and 0x1100<=x.imm<0x111c): base.pop(d,None)
            if not (x.m=='lw' and base.get(x.rs)): origin.pop(d,None)
    return st

def predict_h2(sem, reg, sz, h, seuil=1):
    """mot en h : long natif en h (moitie basse cote hote) -> +2 ; en h-2 -> -2"""
    if sz!='W': return 0
    if sem.get((reg,h),{}).get('calcul',0)>=seuil: return +2
    if sem.get((reg,(h-2)&0xffff),{}).get('calcul',0)>=seuil: return -2
    return 0

if __name__=="__main__" and len(sys.argv)>1 and sys.argv[1]=="h2":
    buf=open(verify.RO3,"rb").read(); sem=semantic_long_stats(buf)
    print("champs A6 : calcul / copie")
    for d in (0x10,0x14,0x18,0x1c,0x20,0x40,0x48,0x50,0x0c,0x04):
        c=sem.get((6,d),{}); print("   A6 $%02x : calcul %4d  copie %4d"%(d,c.get('calcul',0),c.get('copie',0)))
    for d in (0x10,0x14,0x18,0x1c,0x40): 
        c=sem.get((4,d),{}); print("   A4 $%02x : calcul %4d  copie %4d"%(d,c.get('calcul',0),c.get('copie',0)))
    pairs=[p for p in json.load(open(os.path.join(D,"layout_pairs.json"))) if len(p)>8 and p[8]]
    for seuil in (1,3,10):
        ok=collections.Counter(); tot=collections.Counter()
        for sz,reg,h,dd,*_ in pairs:
            tot[sz]+=1; ok[sz]+= predict_h2(sem,reg,sz,h,seuil)==dd
        print("H2 (seuil %2d) paires sures : W %3.0f%%  (B %3.0f%%, L %3.0f%%)  global %.1f%%  [sans correction 93.7%%]"%(
            seuil,100*ok['W']/tot['W'],100*ok['B']/tot['B'],100*ok['L']/tot['L'],100*sum(ok.values())/sum(tot.values())))
