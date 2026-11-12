#!/usr/bin/env python3
"""tables_sauts.py roN -- jump tables of the recompiler (T_xxxxxx, PS2 u32 pointers) as the map announces them ("table
de N entrees") against the module's data:
  TRONQUEE?  the words after the N entries are still valid code pointers, and T+4N is NOT itself a known jump table;
  TROUS      null entries inside;
  BORNE      an ANDI.W #m mask on the index in the 8 preceding lines that allows an index >= N.
Review E4 (found sound).
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, re, struct, collections
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import CODE0
import carte
mod=sys.argv[1]
buf=paths.module(mod)
CODE1=struct.unpack_from('<I',buf,12)[0]; RB=0x1f0000
E=carte.lit(mod)
T={}; sites=collections.defaultdict(list)
for k,(a,v,t) in enumerate(E):
    m=re.search(r'(JMP|JSR) T_([0-9a-f]{6})\(PC,D(\d)\.W\)\s+\[table de (\d+) entrees\]',t)
    if m:
        tb=int(m.group(2),16); n=int(m.group(4)); T[tb]=n; sites[tb].append(k)
def code(v): return CODE0<=v-RB<CODE1 and v%4==0
print("%s : %d tables d'aiguillage, %d sites"%(mod,len(T),sum(len(x) for x in sites.values())))
nt=nh=nb=0
for tb in sorted(T):
    n=T[tb]; o=tb-RB
    ent=[struct.unpack_from('<I',buf,o+4*i)[0] for i in range(n)]
    trous=[i for i,x in enumerate(ent) if x==0]
    # suite
    j=n; suite=0
    while o+4*j+4<=len(buf) and code(struct.unpack_from('<I',buf,o+4*j)[0]) and suite<64: suite+=1; j+=1
    fin=tb+4*n
    msg=[]
    nx=min((x for x in T if x>tb), default=None)
    if suite and not (nx is not None and nx<=fin): msg.append("TRONQUEE? %d pointeurs de code suivent (T+4N=%06x n'est pas une table connue)"%(suite,fin)); nt+=1
    if trous: nh+=1
    for k in sites[tb]:
        for j in range(k-1,max(0,k-9),-1):
            h=carte.tete(E[j][2])
            if h.startswith(('RTS','JMP','BRA','JSR')): break
            mm=re.match(r'^ANDI\.W #\$([0-9a-f]+),D\d',h)
            if mm:
                mk=int(mm.group(1),16)
                if mk//2+1>n and mk<0x100: msg.append("BORNE site %06x masque $%x -> jusqu'a %d entrees"%(E[k][0],mk,mk//2+1)); nb+=1
                break
    if msg: print("  T_%06x N=%d sites %s : %s"%(tb,n,','.join('%06x'%E[k][0] for k in sites[tb][:4]),' ; '.join(msg)))
print("  tronquees? %d ; avec trous %d ; bornes larges %d"%(nt,nh,nb))
