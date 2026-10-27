#!/usr/bin/env python3
"""desas68.py IMAGE ADRESSE N : desassemble N instructions 68K d'une image gros-boutiste (capstone ; mot illisible -> « ? »).
Image d'une construction HSFA : fichiers sz3ud.03c .. sz3.10b concatenes, octets echanges par mot (voir rustine_angle.py)."""
import sys,capstone
img=open(sys.argv[1],'rb').read(); a=int(sys.argv[2],16); n=int(sys.argv[3])
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
k=0
while k<n:
  got=False
  for i in md.disasm(img[a:a+16],a):
    print("%06x  %-20s %-8s %s"%(i.address,i.bytes.hex(),i.mnemonic,i.op_str)); a+=i.size; got=True; break
  if not got: print("%06x  %04x ?"%(a,int.from_bytes(img[a:a+2],'big'))); a+=2
  k+=1
