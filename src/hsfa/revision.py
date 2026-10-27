# (HANDOFF §96) # Quelle revision de SFA3 l'Anthology traduit-elle ? fonctions traduites -> identite avec USA 980904 vs Japon 980629
import os, sys, struct, bisect, random, collections, json, re
sys.path.insert(0,'<workspace>/scripts/untranspile')
import translate as T, verify
from assemble import assemble
from mips import decode, CODE0, CODE1
sw=lambda d: bytes(b for i in range(0,len(d)-1,2) for b in (d[i+1],d[i]))
D=os.environ.get('SFZ3JR2','')   # dossier des ROM programme sfz3jr2dl (sz3jdl.03/04, sz3.05..10), avec / final
J=sw(b''.join(open(D+n,'rb').read() for n in ('sz3jdl.03','sz3jdl.04','sz3.05','sz3.06','sz3.07','sz3.08','sz3.09','sz3.10')))
U=open('<workspace>/work/cps2/sfa3ud_prog.bin','rb').read()
imgs={'USA':struct.unpack('>%dH'%(0x100000//2),U[:0x100000]),'JPN':struct.unpack('>%dH'%(0x100000//2),J[:0x100000])}
idx={}
for k,kw in imgs.items():
    d=collections.defaultdict(list)
    for j in range(len(kw)-3): d[(kw[j],kw[j+1],kw[j+2])].append(j)
    idx[k]=d
buf=open(verify.RO3,'rb').read()
starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
random.seed(4); cand=[s for s in starts]; random.shuffle(cand)
def best(kw,d,words):
    bs=(0,None)
    for s in range(0,min(6,len(words)-3)):
        for j in d.get(tuple(words[s:s+3]),[])[:200]:
            j0=j-s
            if j0<0: continue
            sc=sum(1 for t in range(min(16,len(words))) if j0+t<len(kw) and kw[j0+t]==words[t])
            if sc>bs[0]: bs=(sc,j0)
    return bs
res=collections.Counter(); diffs=[]
n=0
for a in cand:
    if n>=250: break
    k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
    if b-a>0x2000 or b-a<0x60: continue
    try: its,words,unres=assemble(buf,a,b,base=0,external=T.mips_to_68k)
    except Exception: continue
    if len(words)<12: continue
    sc={}
    for name in imgs:
        s,j=best(imgs[name],idx[name],words)
        if j is None: sc[name]=0; continue
        ref=imgs[name][j:j+len(words)]
        sc[name]=sum(1 for x,y in zip(words,ref) if x==y)/len(words)
    if max(sc.values())<0.5: continue
    n+=1
    if abs(sc['USA']-sc['JPN'])<0.01: res['egal']+=1
    elif sc['USA']>sc['JPN']: res['USA']+=1; diffs.append(('USA',hex(a),round(sc['USA'],2),round(sc['JPN'],2)))
    else: res['JPN']+=1; diffs.append(('JPN',hex(a),round(sc['USA'],2),round(sc['JPN'],2)))
print(n,'fonctions comparees :',dict(res))
for d in diffs[:25]: print(d)
