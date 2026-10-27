# Remet bout a bout le programme traduit d'Upper (copie locale) : prog.bin (gros-boutiste, vue 68K)
import sys
R='ro5/roms_fork/sfa3hx/'
noms=['sz3ud.03c','sz3ud.04c','sz3.05c','sz3.06c','sz3.07c','sz3.08c','sz3.09c','sz3.10b']
b=bytearray()
for n in noms:
    d=bytearray(open(R+n,'rb').read())
    d[0::2],d[1::2]=d[1::2],d[0::2]
    b+=d
open('prog.bin','wb').write(b)
print(len(b))
