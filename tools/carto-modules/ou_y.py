#!/usr/bin/env python3
"""Pour chaque module (ro1..ro9, b), cherche les enregistrements 'flux ADX' (type 1, 8 octets) des tables son natives
et liste les plages de Y_DATA qu'ils referencent, par table (debut de serie). Usage : ou_y.py"""
import struct
for mod in ("b","ro1","ro2","ro3","ro4","ro5","ro6","ro7","ro8","ro9"):
    d=open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin"%mod,"rb").read()
    def rec(o):
        e=d[o:o+8]
        if e[0]!=1 or e[1]|e[2]|e[3] or e[7]: return None
        return ((e[6]&0x7f)<<8)|e[4]
    series=[]; o=0; n=len(d)-16
    while o<n:
        f=rec(o)
        if f is not None and f>0 and rec(o+8) is not None:
            # serie de >= 4 enregistrements type 1 consecutifs
            k=o; fs=[]
            while k<n and rec(k) is not None: fs.append(rec(k)); k+=8
            if len([x for x in fs if x])>=4: series.append((o,fs)); o=k; continue
        o+=4
    for o,fs in series:
        nz=sorted(set(x for x in fs if x))
        rng=[];
        for x in nz:
            if rng and x==rng[-1][1]+1: rng[-1][1]=x
            else: rng.append([x,x])
        print("%s exec 0x%X (%d enreg.) : Y_DATA %s"%(mod,o+0x1F0000,len(fs)," ".join("%d-%d"%tuple(r) if r[0]!=r[1] else str(r[0]) for r in rng)))
