"""Affiche une paire de routines appariées : 68K arcade puis MIPS PSP."""
import sys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
from arc68k import md, B as AB
from relocs import img
from mips import decode
def show(a, p, na=26, np_=34):
    print("=" * 30, "arcade %06x  <->  PSP %06x" % (a, p))
    n = 0
    for i in md.disasm(AB[a:a+0x80], a):
        print("   A %06x  %-8s %s" % (i.address, i.mnemonic, i.op_str)); n += 1
        if i.mnemonic in ("rts", "jmp", "bra", "bra.b", "bra.w") or n > na: break
    n = 0
    for i in decode(img, p, p + 0x100):
        print("   P %06x  %r" % (i.va, i)); n += 1
        if (i.m == "jr" and i.rs == 31) or n > np_: break
if __name__ == "__main__":
    for x in sys.argv[1:]:
        a, p = x.split(":"); show(int(a, 16), int(p, 16))
