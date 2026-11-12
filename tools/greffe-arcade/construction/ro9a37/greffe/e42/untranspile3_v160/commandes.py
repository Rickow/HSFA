#!/usr/bin/env python3
"""(HANDOFF §93) Compare le test des commandes (work/mame/commandes.lua) entre la ROM arcade et la traduction :
pour chaque action, suite des ETATS distincts du joueur concerne (octets ROM $4-$7) et deplacement X/Y.
Usage : commandes.py ref.txt tr.txt"""
import sys, collections
TOURS=collections.defaultdict(dict)
def lit(p):
    acts=[]; F=collections.defaultdict(dict)
    for l in open(p):
        t=l.split()
        if t[0]=='A': acts.append((int(t[1]), t[2], ' '.join(t[3:])))
        elif t[0]=='C': TOURS[p][int(t[1])]=int(t[2])
        elif t[0]=='F': F[int(t[2])][int(t[1])]=(tuple(t[3:7]), int(t[7],16), int(t[8],16))
    return acts, F
ar, Fr = lit(sys.argv[1]); at, Ft = lit(sys.argv[2])
def resume(F, j, d, f):
    """etats distincts de l'action ; les etats d'UNE image sont ignores (echantillonnage : la traduction, plus
    lente, saute ou double des tours de jeu par image -- HANDOFF §93)"""
    seq=[]; x0=y0=None; ymin=None; xs=[]
    for r in range(d, f):
        e=F.get(j,{}).get(r)
        if not e: continue
        s,x,y=e
        if x0 is None: x0,y0=x,y
        if seq and seq[-1][0]==s: seq[-1][1]+=1
        else: seq.append([s,1])
        ymin=y if ymin is None else max(ymin,y); xs.append(x)
    seq=[s for s,n in seq if n>1]
    seq=[s for k,s in enumerate(seq) if k==0 or s!=seq[k-1]]
    return ['%s%s/%s%s'%s for s in seq], (xs[-1]-x0 if xs else 0), (ymin-y0 if ymin is not None else 0)
nok=0
for k,(d,j,nom) in enumerate(ar):
    f=ar[k+1][0] if k+1<len(ar) else d+90
    jn=int(j[1])
    sr,dxr,dyr=resume(Fr,jn,d,f); st,dxt,dyt=resume(Ft,jn,d,f)
    ok = sr==st and dxr==dxt and dyr==dyt
    nok+=not ok
    print('%s %-3s %-16s ref dx=%-5d dy=%-4d %s' % ('OK ' if ok else '!! ', j, nom, dxr, dyr, ' '.join(sr)))
    if not ok: print('    %-20s tr  dx=%-5d dy=%-4d %s' % ('', dxt, dyt, ' '.join(st)))
print('%d actions, %d differentes' % (len(ar), nok))
for p in sys.argv[1:3]:
    t=TOURS[p]
    if t:
        a,b=min(t),max(t); n=(t[b]-t[a])&0xffff
        print('%s : %d tours de jeu en %d images (%.1f %%)' % (p.split('/')[-1], n, b-a, 100.0*n/max(1,b-a)))
