#!/usr/bin/env python3
"""paires_exg.py IMAGE FIN : cherche les paires « MOVE.x Dy,Dx ; MOVE.x Dx,Dy » de $1000 a FIN (hexa). Dans du code juste la
2e copie ne sert a rien : c'est la signature d'un EXG Dx,Dy dont le traducteur a perdu le temporaire (D-SONDES §4).
Sortie : une ligne par paire ; a confronter a l'arcade (EXG au meme endroit)."""
import sys,capstone
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
img=open(sys.argv[1],'rb').read(); fin=int(sys.argv[2],16)
res=[]
for a in range(0x1000,fin,2):
  w1=int.from_bytes(img[a:a+2],'big'); w2=int.from_bytes(img[a+2:a+4],'big')
  for sz,base in (('b',0x1000),('w',0x3000),('l',0x2000)):
    if w1&0xF1F8==base and w2&0xF1F8==base:
      x=(w1>>9)&7; y=w1&7
      if x!=y and w2==base|(y<<9)|x: res.append((a,sz,y,x))
for a,sz,y,x in res:
  print('%06x move.%s d%d,d%d ; move.%s d%d,d%d'%(a,sz,y,x,sz,x,y))
print(len(res),'paires',file=sys.stderr)
