#!/usr/bin/env python3
"""autour.py mod debut fin : chaines du module dont le decalage fichier est dans [debut, fin)"""
import sys
m, a, b = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
for l in open('chaines_%s.txt' % m):
    o = int(l[:7], 16)
    if a <= o < b: print(l.rstrip())
