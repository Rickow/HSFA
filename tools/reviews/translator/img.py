#!/usr/bin/env python3
"""img.py roN ADR [size] -- disassembles the TRANSLATED image (program ROMs sz3ud.03c ... sz3.10b of a build, words put
back in order) at 68K address ADR. Folder: IMG, else the first $HSFA_BUILD/roms_*/sfa3ud. Needs capstone.
Also a library: image(mod) -> bytes of the image (used by fragments_atteints.py).
Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, os, glob, capstone
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "..", "..", "src", "hsfa"))
import paths
def _lit(p):
    with open(p,'rb') as f: return f.read()
def image(mod):
    d=os.environ.get('IMG') or sorted(glob.glob(os.path.join(paths.construction(mod),'roms_*','sfa3ud')))[0]
    b=b''.join(_lit(os.path.join(d,n)) for n in ["sz3ud.03c","sz3ud.04c","sz3.05c","sz3.06c","sz3.07c","sz3.08c","sz3.09c","sz3.10b"])
    return bytes(x for i in range(0,len(b),2) for x in (b[i+1],b[i]))
if __name__=='__main__':
    d=image(sys.argv[1]); a=int(sys.argv[2],16); e=a+(int(sys.argv[3],16) if len(sys.argv)>3 else 0x40)
    md=capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000)
    while a<e:
        got=False
        for i in md.disasm(d[a:a+12],a):
            print('%06x %s %s'%(i.address,i.mnemonic,i.op_str)); a+=i.size; got=True; break
        if not got: print('%06x dc.w $%04x'%(a,int.from_bytes(d[a:a+2],'big'))); a+=2
