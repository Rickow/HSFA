import os, sys, pickle, collections
os.environ.setdefault("GRAIN","routine")
sys.path.insert(0,"<workspace>/work/greffe_arcade/outils"); sys.path.insert(0,"<workspace>/work/greffe_arcade/etape2")
import greffe as GR, verifie_reutil as VR
H=pickle.load(open('donnees/homologues.pkl','rb'))['code']
c=collections.Counter()
for a,(p,n,cf) in H.items():
    i=GR.INV.get(a,{}); q=i.get('partenaire')
    if q==p: c['accord']+=1; continue
    m1 = a in GR.INV and VR.meme_routine(a,p)
    m2 = q is not None and a in GR.INV and VR.meme_routine(a,q)
    c[('prop_meme' if m1 else 'prop_diff', 'inv_meme' if m2 else 'inv_diff', 'maj' if n>cf else 'min')]+=1
for k,v in sorted(c.items(), key=str): print(k,v)
