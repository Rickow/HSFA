#!/usr/bin/env python3
"""Qu'est-ce qui pourrait etre 'branche' de Hyper (ro9) dans Upper (ro5) ?

1. Chaque fonction de Hyper est classee par rapport a Upper : COMMUNE (identique, adresses
   masquees), MODIFIEE (ressemblance >= 70 %), PROPRE a Hyper.
2. Les fonctions modifiees/propres reliees par des appels forment des COMPOSANTS.
3. Pour chaque composant : points de branchement (fonctions communes qui l'appellent),
   dependances (fonctions communes qu'il appelle, donc deja presentes dans Upper),
   variables globales A5 (existent-elles dans Upper ?).
"""
import sys, os, bisect, collections, struct
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from modcompare import module, sig, grams
BASE=0x1f0000

def funcs(mod):
    buf,s,e,st,L=mod; vas=[x.va for x in L]; out=[]
    for k,a in enumerate(st):
        b=st[k+1] if k+1<len(st) else e
        seg=L[bisect.bisect_left(vas,a):bisect.bisect_left(vas,b)]
        out.append((a,b,seg))
    return out

def a5vars(seg):
    base={}; c=collections.Counter()
    for x in seg:
        if x.m=='lw' and x.imm==0x1114: base[x.rt]=0; continue
        if x.m=='addiu' and x.rs in base: base[x.rt]=(base[x.rs]+x.simm)&0xffff; continue
        if x.m in ('lb','lbu','lh','lhu','lw','sb','sh','sw') and x.rs in base: c[(base[x.rs]+x.simm)&0xffff]+=1
        d=x.rt if x.m in ('lb','lbu','lh','lhu','lw','andi','lui','ori') else (x.rd if x.op==0 else None)
        if d is not None and not (x.m=='lw' and x.imm==0x1114): base.pop(d,None)
    return c

if __name__=="__main__":
    m5=module('ro5'); m9=module('ro9')
    F5=funcs(m5); F9=funcs(m9)
    ex5={sig(seg,a,b,False)[0] for a,b,seg in F5}
    G5=[(a,grams(seg)) for a,b,seg in F5]
    inv=collections.defaultdict(list)
    for k,(a,g) in enumerate(G5):
        for x in g: inv[x].append(k)
    v5=collections.Counter()
    for a,b,seg in F5: v5.update(a5vars(seg))
    cls={}; size={}
    for a,b,seg in F9:
        size[a]=b-a
        if sig(seg,a,b,False)[0] in ex5: cls[a]='commune'; continue
        g=grams(seg); cnt=collections.Counter()
        for x in g:
            l=inv.get(x)
            if l and len(l)<40: cnt.update(l)
        best=max((len(g&G5[k][1])/len(g|G5[k][1]) for k,_ in cnt.most_common(8)),default=0.0) if g else 0.0
        cls[a]='modifiee' if best>=0.7 else 'propre'
    tot=sum(size.values())
    for c in ('commune','modifiee','propre'):
        print("Hyper, fonctions %-9s : %5.1f %% du code (%d fonctions)"%(c,100*sum(size[a] for a in cls if cls[a]==c)/tot,sum(1 for a in cls if cls[a]==c)))
    # graphe d'appels de Hyper
    starts=sorted(size); calls=collections.defaultdict(set); callers=collections.defaultdict(set)
    for a,b,seg in F9:
        for x in seg:
            if x.m=='jal':
                t=x.tgt-BASE
                if t in size: calls[a].add(t); callers[t].add(a)
    # composants : fonctions non communes reliees par des appels
    parent={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    nc=[a for a in cls if cls[a]!='commune']
    for a in nc:
        find(a)
        for t in calls[a]:
            if cls.get(t)!='commune': parent[find(a)]=find(t)
    comp=collections.defaultdict(list)
    for a in nc: comp[find(a)].append(a)
    rows=[]
    for r,mem in comp.items():
        ms=set(mem); sz=sum(size[a] for a in mem)
        plug={c for a in mem for c in callers[a] if cls.get(c)=='commune'}
        deps={t for a in mem for t in calls[a] if cls.get(t)=='commune'}
        vs=collections.Counter()
        for a,b,seg in F9:
            if a in ms: vs.update(a5vars(seg))
        new=[d for d in vs if d not in v5]
        rows.append((sz,len(mem),len(plug),len(deps),len(vs),len(new),sum(1 for a in mem if cls[a]=='propre'),min(mem)))
    rows.sort(reverse=True)
    print("\nCOMPOSANTS propres/modifies de Hyper (les plus gros) :")
    print("  taille   fonctions(propres)  branchements  dependances  variables A5 (dont absentes d'Upper)")
    for sz,n,pl,dp,nv,nn,npr,a in rows[:15]:
        print("  %6d o   %4d (%4d)          %4d          %4d        %4d (%d)     ex. %07x"%(sz,n,npr,pl,dp,nv,nn,a))
    iso=[r for r in rows if r[2]<=2]
    print("\ncomposants a <= 2 points de branchement : %d, soit %.1f %% du code propre/modifie"%(
        len(iso),100*sum(r[0] for r in iso)/max(1,sum(r[0] for r in rows))))

    # --- PISTE 1 : les variables globales que Hyper est seul a utiliser (absentes d'Upper) ---
    comp_of={}
    for idx,(r,mem) in enumerate(sorted(comp.items(),key=lambda kv:-sum(size[a] for a in kv[1]))):
        for a in mem: comp_of[a]=idx
    use=collections.defaultdict(lambda: collections.Counter())
    rw=collections.defaultdict(collections.Counter)
    for a,b,seg in F9:
        base={}
        for x in seg:
            if x.m=='lw' and x.imm==0x1114: base[x.rt]=0; continue
            if x.m=='addiu' and x.rs in base: base[x.rt]=(base[x.rs]+x.simm)&0xffff; continue
            if x.m in ('lb','lbu','lh','lhu','lw','sb','sh','sw') and x.rs in base:
                d=(base[x.rs]+x.simm)&0xffff
                if d not in v5:
                    use[d][comp_of.get(a,'commun')]+=1
                    rw[d]['ecrit' if x.m[0]=='s' else 'lu']+=1
                    rw[d]['.%s'%{'b':'B','h':'W','w':'L'}[x.m[1]]]+=1
            dd=x.rt if x.m in ('lb','lbu','lh','lhu','lw','andi','lui','ori') else (x.rd if x.op==0 else None)
            if dd is not None and not (x.m=='lw' and x.imm==0x1114): base.pop(dd,None)
    print("\nPISTE 1 - variables globales (A5) propres a Hyper : %d"%len(use))
    print("  (composant n = rang par taille ci-dessus, 0 = le plus gros)")
    for d,c in sorted(use.items(),key=lambda kv:-sum(kv[1].values()))[:30]:
        comps=', '.join('%s:%d'%(k if k=='commun' else 'C%d'%k,v) for k,v in c.most_common(5))
        r=rw[d]
        print("   $%04x  acces %3d (lu %d, ecrit %d, tailles %s)   par : %s"%(d,sum(c.values()),r['lu'],r['ecrit'],
              '/'.join(t for t in ('.B','.W','.L') if r[t]),comps))
