import sys, io, contextlib, numpy as np
sys.path.insert(0,'/home/user/SFA-Anthology-PS2-mods/tools/sondes-recherche')
import tuiles_cps2 as T
pix=T.decode(T.charge('sfa3rom'))
n=len(pix); t=pix[pix.reshape(n,-1).any(axis=1)]
h=T.hachage(t); u,idx=np.unique(h,return_index=True)
cap={}
orig=T.decalages
# rejouer decalages en capturant l'ensemble
import types
src=open(T.__file__).read()
trouves=set()
def dec(pix,uh):
    global trouves
    g={}
    exec(compile(src.split('def decalages')[1].split('def apercu')[0].replace('(pix, uniques_h):','def _d(pix, uniques_h):',1).replace('print(f"tuiles uniques','return trouves\n    print(f"x'),'x','exec'),T.__dict__,g)
    return g['_d'](pix,uh)
with contextlib.redirect_stdout(io.StringIO()):
    tr=dec(pix,u)
tr=np.array(sorted(tr),dtype=np.uint64)
pos=np.searchsorted(u,tr); tiles=t[idx[pos]]
nz=(tiles>0).reshape(len(tiles),-1).sum(1)
ncol=np.array([len(np.unique(x)) for x in tiles])
allnz=(t[idx]>0).reshape(len(idx),-1).sum(1)
for s in (32,64,128,192):
    print(f">= {s} px : {(nz>=s).sum()} retrouvées / {(allnz>=s).sum()} uniques ({100*(nz>=s).sum()/(allnz>=s).sum():.2f} %)")
print('retrouvées avec >=3 couleurs et >=64 px :',((nz>=64)&(ncol>=3)).sum())
