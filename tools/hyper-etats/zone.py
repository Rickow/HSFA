#!/usr/bin/env python3
"""zone.py debut fin [mips|68k] : lignes de carte_image.txt pour une plage d'adresses MIPS fichier (defaut) ou 68K"""
import sys
C="<workspace>/work/mame_ro9/carte_image.txt"
a,b=int(sys.argv[1],16),int(sys.argv[2],16); m=sys.argv[3] if len(sys.argv)>3 else "mips"
for l in open(C):
    x,va,mn=l.rstrip("\n").split(" ",2); x=int(x,16); va=int(va,16)
    v = va if m=="mips" else x
    if a<=v<b: print(l.rstrip("\n"))
