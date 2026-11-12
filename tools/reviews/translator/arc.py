#!/usr/bin/env python3
"""arc.py cherche HEX [before=0x20] [size=0x60] | arc.py dis ADR [size] -- search / disassemble the decrypted arcade
program (sfa3ud). Needs capstone (pip install capstone). Input: HSFA_ARCADE_PROG = decrypted program file (68K byte
order). Read-only; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, capstone
P=os.environ.get('HSFA_ARCADE_PROG')
if not P: sys.exit('arc.py: set HSFA_ARCADE_PROG (decrypted sfa3ud program file)')
with open(P,'rb') as f: d=f.read()
md=capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000)
def dis(a,n):
    e=a+n
    while a<e:
        got=False
        for i in md.disasm(d[a:a+12],a):
            print('%06x %s %s'%(i.address,i.mnemonic,i.op_str)); a+=i.size; got=True; break
        if not got: print('%06x dc.w $%04x'%(a,int.from_bytes(d[a:a+2],'big'))); a+=2
if sys.argv[1]=='dis': dis(int(sys.argv[2],16), int(sys.argv[3],16) if len(sys.argv)>3 else 0x60)
else:
    p=bytes.fromhex(sys.argv[2]); av=int(sys.argv[3],16) if len(sys.argv)>3 else 0x20; n=int(sys.argv[4],16) if len(sys.argv)>4 else 0x60
    k=d.find(p)
    while k>=0:
        if k%2==0:
            print('-- $%06x'%k); dis(k-av,n)
        k=d.find(p,k+1)
