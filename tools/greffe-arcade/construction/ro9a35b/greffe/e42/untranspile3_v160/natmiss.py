#!/usr/bin/env python3
"""Repartit les MANQUES du recensement entre code recompile (68K) et code NATIF du portage
(fonctions C PS2 : pas de banc de registres 68K 0x7000_11xx, cadres de pile > 16 o, sq/lq...)."""
import sys,os,struct,bisect,collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, CODE0
import translate as T, census
buf=open(census.RO3,'rb').read(); end=struct.unpack_from('<I',buf,12)[0]
L=list(decode(buf,CODE0,end))
starts=sorted({x.tgt-T.RUNTIME_BASE for x in L if x.m=='jal'} | {CODE0})
starts=[s for s in starts if CODE0<=s<end]
def fidx(va): return bisect.bisect_right(starts,va)-1
feat=collections.defaultdict(lambda:[0,0,0])   # [lui7000, instr, natif-signes]
for x in L:
    f=fidx(x.va); feat[f][1]+=1
    if x.m=='lui' and x.imm==0x7000: feat[f][0]+=1
    if x.m in ('sq','lq','mult','multu','div','divu','mfhi','mflo') or (x.m=='addiu' and x.rs==29 and x.rt==29 and x.simm<-16 and x.simm>-0x400 and x.simm%16==0 and x.simm!=-16): feat[f][2]+=1
# relais : petite fonction faisant un jalr vers une adresse CONSTANTE du module (lui/addiu)
veneer=set()
_lu={}
for x in L:
    if x.m=='lui': _lu[x.rt]=x.imm
    elif x.m=='addiu' and x.rs in _lu: _lu[x.rt]=(_lu[x.rs]<<16)+x.simm
    elif x.m=='jalr' and x.rs in _lu and 0x1f0000+CODE0 <= _lu[x.rs] < 0x1f0000+end: veneer.add(fidx(x.va))
    elif x.m=='jal' and 0x1f0000+CODE0 <= x.tgt < 0x1f0000+end: veneer.add(fidx(x.va))
def native(f):
    a,n,s=feat[f]
    if a==0 and n<=24 and f in veneer: return False        # relais 68K (JSR/JMP vers le module), pas du C
    if a==0 and n<=8: return False                          # fonction vide (RTS partage), pas du C
    return a==0 or (s>0 and a*20<n)
def main():
  tot=collections.Counter()
  x=CODE0
  while x<end:
      b=min(x+census.CHUNK,end)
      out,_=T.translate(buf,x,b); em={va for va,_,ws in out}
      LL=list(decode(buf,x,b))
      for i,ins in enumerate(LL):
          m=ins.m
          if m in census.BR or (m in ('sb','sh','sw') and ins.rs!=29) or m in('jal','jalr','jr'):
              if m in ('sb','sh','sw') and i>0 and LL[i-1].m=='lui' and LL[i-1].imm==0x7000 and ins.imm in (0x1150,0x1158): continue
              if any(v in em for v in (ins.va-8,ins.va-4,ins.va,ins.va+4)): continue
              nat=native(fidx(ins.va)); tot[nat]+=1
      x=b
  print("manques en code recompile : %d   en code natif du portage : %d"%(tot[False],tot[True]))
  print("fonctions natives : %d / %d"%(sum(1 for f in feat if native(f)),len(feat)))

if __name__=='__main__': main()
