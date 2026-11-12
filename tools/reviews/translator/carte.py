#!/usr/bin/env python3
"""carte.py -- reader of a build's carte_image.txt (image address, MIPS file offset, text). Library for the other
tools: lit(mod) -> [(image address, MIPS offset, text)], cibles(E), tete(text). Path: CARTE, else
$HSFA_BUILD/carte_image.txt (paths.py). Read-only.
Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import re, os
import paths
def chemin(mod): return paths.chemin_carte(mod)
def lit(mod):
    E=[]
    for l in open(chemin(mod),encoding='utf-8',errors='replace'):
        p=l.rstrip('\n').split(' ',2)
        if len(p)<3: continue
        try: a=int(p[0],16); v=int(p[1],16)
        except ValueError: continue
        E.append((a,v,p[2]))
    return E
_C=re.compile(r'\(cible ([0-9a-f]{8})\)')
def cibles(E):
    s=set()
    for a,v,t in E:
        m=_C.search(t)
        if m: s.add(int(m.group(1),16))
    return s
def tete(t):
    """partie instruction (avant les annotations entre crochets)"""
    return t.split('  [')[0].strip()
