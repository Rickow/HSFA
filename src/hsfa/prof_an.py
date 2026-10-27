"""Analyse du profil des adaptateurs (HANDOFF §138) : python3 prof_an.py <travail> <profil> <fin_code_hex> [idle_lo-idle_hi]"""
import array,os,glob,sys,subprocess,re,collections,tempfile
TMP=os.path.join(tempfile.gettempdir(),'prof_an_xx.bin')
T,P,FIN=sys.argv[1],sys.argv[2],int(sys.argv[3],16)
idle=[int(x,16) for x in sys.argv[4].split('-')] if len(sys.argv)>4 else None
d=glob.glob(T+'/roms*/*/')[0]
names=[n for n in os.listdir(d) if not os.path.islink(d+n) and n.split('.')[-1][:2] in ('03','04','05','06','07','08','09','10')]
names=sorted(names,key=lambda n:int(n.split('.')[-1][:2]))
b=b''.join(open(d+n,'rb').read() for n in names); a=array.array('H',b); a.byteswap(); b=a.tobytes()
cache=T+'/dis_%x.txt'%FIN
if not os.path.exists(cache):
    with open(cache,'w') as out:
        for lo,hi in ((0,FIN),(0x3E0000,0x400000)):
            open(TMP,'wb').write(b[lo:hi])
            out.write(subprocess.run(['unidasm','-arch','m68000','-basepc',hex(lo),TMP],capture_output=True,text=True).stdout)
RX=re.compile(r'^\s*([0-9a-f]+): ((?:[0-9a-f]{4} )+)\s*(\S+)\s*(.*)$')
ins={}; order=[]
for l in open(cache):
    m=RX.match(l)
    if m:
        ad=int(m.group(1),16); ins[ad]=(len(m.group(2).split()),m.group(3),m.group(4).strip()); order.append(ad)
start={}
for ad in order:
    for k in range(ins[ad][0]): start[ad+2*k]=ad
L=open(P).read().split('\n'); nimg=int(L[0].split()[2]); cnt=collections.Counter()
for l in L[1:]:
    if l: x,c=l.split(); cnt[int(x,16)]+=int(c)
tot=sum(cnt.values())
idle_n=sum(c for x,c in cnt.items() if idle and idle[0]<=x<idle[1])
per=collections.Counter(); 
for x,c in cnt.items():
    if idle and idle[0]<=x<idle[1]: continue
    per[start.get(x,x)]+=c
# categories
pos={ad:i for i,ad in enumerate(order)}
def nb(ad,k):
    i=pos.get(ad); 
    if i is None: return None
    j=i+k; return order[j] if 0<=j<len(order) else None
def cat(ad):
    if 0x400<=ad<0x800: return 'conv_donnees(talons $400)'
    if 0x3FF000<=ad<0x400000: return 'conv_code(talons $3FF000)'
    if 0x3E0000<=ad<0x3FF000: return 'conv_code(carte $3E0000)'
    if ad<0x1000: return 'noyau/autres talons'
    n,mn,op=ins.get(ad,(1,'?',''))
    if mn in ('jsr','jmp') and re.match(r'\$[0-7][0-9a-f]{2}\.(w|l)$',op): return 'appel conv (JSR talon)'
    if mn=='swap': return 'swap (longs echanges)'
    if mn=='move' and op in ('SR, -(A7)',) : return 'MOVE SR/CCR (drapeaux preserves)'
    if mn=='move' and op.endswith(', CCR'): return 'MOVE SR/CCR (drapeaux preserves)'
    if mn=='eori.b' and op.startswith('#$1, ($3,A7)'): return 'octet XOR 1 (bascule)'
    for k in (1,2,-1,-2,-3):
        q=nb(ad,k)
        if q and ins[q][1]=='eori.b' and ins[q][2].startswith('#$1, ($3,A7)'): return 'octet XOR 1 (bascule)'
    if '$87e' in op or '$87f' in op or '-$781' in op or '-$780' in op: return 'registres pretes A8/D8'
    if mn.startswith('movem') or (mn.startswith('move') and ('-(A7)' in op or '(A7)+' in op)): return 'pile (sauvegardes temporaires)'
    return 'code utile'
c=collections.Counter()
for ad,n in per.items(): c[cat(ad)]+=n
work=sum(per.values())
print('images de combat %d ; mots lus/image %.0f ; attente %.1f%% ; travail/image %.0f'%(nimg,tot/nimg,100*idle_n/tot,work/nimg))
for k,v in c.most_common(): print('  %-36s %5.1f%%  (%.0f mots/image)'%(k,100*v/work,v/nimg))
top=collections.Counter()
for ad,n in per.items():
    top[ad&~0xff]+=n
print('zones chaudes (256 o) :',' '.join('%06x:%.1f%%'%(z,100*v/work) for z,v in top.most_common(10)))
