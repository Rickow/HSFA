#!/usr/bin/env python3
"""Comparaison famille par famille A ARMES EGALES : sur les fonctions d'origine localisees dans
la ROM (comme e2e.py), on compte les instructions de la ROM et celles de NOTRE traduction de la
MEME fonction. Pas de donnees parasites (contrairement au decodage lineaire du 1er Mo)."""
import sys, os, re, json, struct, random, bisect, collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T, verify, e2e, m68k
from assemble import assemble
from opclass import klass
from mips import decode, CODE0, CODE1
buf=open(verify.RO3,"rb").read(); k68=open(verify.K68,"rb").read()[:0x100000]
kw=struct.unpack('>%dH'%(len(k68)//2),k68)
fz=json.load(open(os.path.join(D,"hooks_a5.json"))); foreign={int(k,16) for k in fz["foreign"]}
bad={0x05,0x18,0x19,0x1a,0x1b,0x38,0x39,0x02,0x03,0x04}
starts=sorted({x.tgt-T.RUNTIME_BASE for x in decode(buf,CODE0,CODE1) if x.m=='jal'})
random.seed(9); cand=[s for s in starts if (s>>16) not in bad]; random.shuffle(cand)
ext=e2e.snapped_external(kw); rom=collections.Counter(); tr=collections.Counter(); nf=0
def count(words, ctr):
    i=0
    while i<len(words):
        r=m68k.decode_one(words,i,len(words))
        ctr[klass(words[i])]+=1; i+=r[0] if r else 1
for a in cand[:700]:
    k=bisect.bisect_right(starts,a); b=starts[k] if k<len(starts) else CODE1
    if b-a>0x3000 or b-a<0x40: continue
    k0=T.mips_to_68k(a)
    if k0 is None: continue
    its,words,u=assemble(buf,a,b,external=ext)
    if len(words)<8 or any(int(d,16) in foreign for it in its for d in re.findall(r'\$([0-9a-f]{4})\(A5\)',it.mn)): continue
    sc,j=e2e.locate_mapped(kw,words,k0)
    if j is None or sc<6: continue
    its,words,u=assemble(buf,a,b,base=j*2,external=ext)
    nf+=1; count(list(words),tr); count(list(kw[j:j+len(words)]),rom)
rt=sum(rom.values()); tt=sum(tr.values())
print("fonctions comparees : %d   instructions : ROM %d | traduction %d"%(nf,rt,tt))
print("\n%-26s %6s %6s %7s"%("famille","ROM","nous","rapport"))
for k in sorted(rom,key=lambda k:-rom[k])[:40]:
    r=tr[k]/rom[k]
    flag="  <== MANQUE" if rom[k]>=8 and r<0.5 else ("  (trop ?)" if rom[k]>=8 and r>1.5 else "")
    print("%-26s %6d %6d %7.2f%s"%(k,rom[k],tr[k],r,flag))
