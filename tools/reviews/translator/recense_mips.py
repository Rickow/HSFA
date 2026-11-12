#!/usr/bin/env python3
"""recense_mips.py roN -- census of the MIPS mnemonics of the recompiled 68K zone (decoder of the repository), with
examples for the rare ones. Starting point to look for unhandled instructions.
Environment: HSFA_MODULES (modules), HSFA_BUILD or CARTE (build / map); see paths.py.
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, struct, collections
sys.dont_write_bytecode=True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
from mips import decode
mod=sys.argv[1]
buf=paths.module(mod)
e=struct.unpack_from('<I',buf,12)[0]; c0=0x22de0 if e==0x3bf140 else 0x22b00
print(mod,'code %x-%x'%(c0,e), 'magic',buf[:4], [hex(x) for x in struct.unpack_from('<8I',buf,0)])
c=collections.Counter(); ex={}
for x in decode(buf,c0,e):
    m=x.m
    if m=='sll' and x.w==0: m='nop'
    if x.op==0 and x.fn==0x2d: m='daddu(%s)'%('zero' if 0 in (x.rs,x.rt) else 'NONZERO')
    c[m]+=1; ex.setdefault(m,[]).append(x.va)
for m,n in sorted(c.items(), key=lambda t:-t[1]):
    print("%-16s %8d  %s"%(m,n,' '.join('%x'%v for v in ex[m][:6]) if n<200 else ''))
