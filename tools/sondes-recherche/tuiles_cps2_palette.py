import sys, numpy as np
sys.path.insert(0,'/home/user/SFA-Anthology-PS2-mods/tools/sondes-recherche')
import tuiles_cps2 as T
pix=T.decode(T.charge('sfa3rom')); n=len(pix)
for transp in (15,0):
    t=pix[(pix!=transp).reshape(n,-1).any(axis=1)].reshape(-1,256)
    u_exact=len(np.unique(T.hachage(t.reshape(-1,16,16))))
    # forme canonique : indices renumérotés par ordre d'apparition, l'indice transparent fixé
    c=np.full_like(t,255)
    m=np.zeros((len(t),16),dtype=np.int16)-1
    nxt=np.zeros(len(t),dtype=np.int16)
    rows=np.arange(len(t))
    for i in range(256):
        v=t[:,i].astype(np.int16)
        tr=v==transp
        known=m[rows,v]
        new=(known<0)&~tr
        m[rows[new],v[new]]=nxt[new]; nxt[new]+=1
        c[:,i]=np.where(tr,255,m[rows,v])
    u_perm=len(np.unique(T.hachage(c.reshape(-1,16,16))))
    print(f"indice transparent {transp} : uniques exactes {u_exact}, uniques à palette près {u_perm} (gain {100*(1-u_perm/u_exact):.2f} %), couleurs moyennes/tuile {nxt.mean():.1f}")
