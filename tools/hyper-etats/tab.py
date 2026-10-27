#!/usr/bin/env python3
"""tab.py adr_exec n : vide n longs (adresses exec MIPS) d'une table de ro9 ; affiche aussi le fichier (exec-0x1F0000)"""
import sys
b=open("<workspace>/anthology_extract/decompressed/ro9_usa_prog68k.bin","rb").read()
a=int(sys.argv[1],16); n=int(sys.argv[2])
for i in range(n):
    o=a-0x1F0000+4*i; v=int.from_bytes(b[o:o+4],'little')
    print("%2d  %08x  fichier %06x" % (i, v, v-0x1F0000 if v else 0))
