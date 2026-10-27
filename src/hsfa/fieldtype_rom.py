#!/usr/bin/env python3
"""VERIFICATION DU TYPAGE PAR CHAMP contre la ROM : pour chaque constante longue V ecrite par le
MIPS a d(An), on cherche dans la ROM 'MOVE.L #X,d'(An)' avec X = V (champ s32 natif),
X = echange des moities (deux s16) ou X = octets inverses (u8[4]), et d' = d ou le deplacement
68K correspondant. Donne, par deplacement, la relation observee."""
import sys,os,struct,collections
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
from mips import decode, CODE0
import census
buf=open(census.RO3,'rb').read(); end=struct.unpack_from('<I',buf,12)[0]
rom=open('<workspace>/work/cps2/sfa3_prog.bin','rb').read()
def hs(v): return ((v&0xffff)<<16)|(v>>16)
def bs(v): return int.from_bytes(v.to_bytes(4,'little'),'big')
LL=list(decode(buf,CODE0,end))
def evidence(AN):
  SLOT=0x1100+4*AN
  L=LL
  val={}; base=set(); l7=set(); stores=collections.defaultdict(set)
  for x in L:
    m=x.m
    if m=='lui':
        (l7.add if x.imm==0x7000 else l7.discard)(x.rt); base.discard(x.rt)
        val[x.rt]=(x.imm<<16)&0xffffffff if x.imm!=0x7000 else None; continue
    if m=='addiu' and x.rs==0: val[x.rt]=x.simm&0xffffffff; base.discard(x.rt); l7.discard(x.rt); continue
    if m=='ori' and val.get(x.rs) is not None and x.rs not in l7: val[x.rt]=val[x.rs]|x.imm; continue
    if m=='addiu' and val.get(x.rs) is not None and x.rs not in l7: val[x.rt]=(val[x.rs]+x.simm)&0xffffffff; continue
    if m=='lw' and x.rs in l7 and x.imm==SLOT: base.add(x.rt); l7.discard(x.rt); val.pop(x.rt,None); continue
    if m=='sw' and x.rs in base and val.get(x.rt) not in (None,0):
        stores[x.simm].add(val[x.rt])
    if m in ('lb','lh','lw','lbu','lhu','addu','subu','and','or','sll','sra','srl','dsll32','dsra32','andi','jal','jalr'):
        r=x.rd if m in ('addu','subu','and','or','sll','sra','srl','dsll32','dsra32') else x.rt
        if m in ('jal','jalr'): base.clear(); l7.clear(); val.clear()
        else: base.discard(r); l7.discard(r); val.pop(r,None)
  op=0x2d7c if AN==6 else (0x207c|0x0d00|0x40|0x3c)  # MOVE.L #imm,d16(A6)
  opw=(0x2000|(AN<<9)|(5<<6)|0x3c)
  res=collections.defaultdict(collections.Counter)
  for d,vs in sorted(stores.items()):
    for v in vs:
        for name,x in (('natif',v),('moities',hs(v)),('octets',bs(v))):
            if x==v and name!='natif': continue
            pat=struct.pack('>HIH',opw,x,d&0xffff)
            if rom.find(pat)>=0 and rom.find(pat)%2==0: res[d][name]+=1
        # constante absente telle quelle a ce deplacement : essayer d^2 (moitie deplacee)
  return res, stores
if __name__=="__main__":
  AN=int(sys.argv[1]) if len(sys.argv)>1 else 6
  res,stores=evidence(AN)
  print("A%d : deplacement -> relation constante MIPS / constante ROM (nb de valeurs distinctes)"%AN)
  for d in sorted(res):
    if d<0x100: print("  $%03x  %s   (%d valeurs MIPS)"%(d,dict(res[d]),len(stores[d])))
