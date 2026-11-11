import sys, numpy as np, collections
sys.path.insert(0,'/home/user/SFA-Anthology-PS2-mods/tools/sondes-recherche')
import tuiles_cps2 as T
pix=T.decode(T.charge('sfa3rom')); n=len(pix)
t=pix[pix.reshape(n,-1).any(axis=1)]
h=T.hachage(t); _,idx=np.unique(h,return_index=True); u=t[idx].reshape(len(idx),256)
N=len(u); K=4
blocks=[(0,52),(52,103),(103,154),(154,205),(205,256)]   # K+1 blocs : si <=K pixels diffèrent, un bloc est identique
best=np.full(N,999,dtype=np.int16)
for a,b in blocks:
    hb=T.hachage(u[:,a:b].reshape(N,1,b-a).astype(np.uint8).reshape(N,-1,1)) if False else None
    v=u[:,a:b].astype(np.uint64); hh=np.zeros(N,dtype=np.uint64)
    for i in range(v.shape[1]): hh=hh*np.uint64(1099511628211)^v[:,i]
    order=np.argsort(hh,kind='stable'); hs=hh[order]
    cuts=np.flatnonzero(np.diff(hs))+1
    for g in np.split(order,cuts):
        if len(g)<2 or len(g)>3000: continue
        sub=u[g]
        d=(sub[:,None,:]!=sub[None,:,:]).sum(2)
        np.fill_diagonal(d,999)
        best[g]=np.minimum(best[g],d.min(1))
for k in (1,2,4):
    print(f"tuiles uniques ayant une voisine à <= {k} pixel(s) près : {(best<=k).sum()} ({100*(best<=k).mean():.2f} %)")
