"""Désassemblage MIPS avec les instructions du coprocesseur flottant (COP1, LWC1/SWC1) — 2026-10-07.
python fpu.py debut [fin] : comme desasm.py, en décodant les ?op11/?op31/?op39."""
import sys, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
from relocs import img
from mips import decode, REG
from charcode2 import fend
FMT = {16: "s", 20: "w"}
FN = {0: "add", 1: "sub", 2: "mul", 3: "div", 4: "sqrt", 5: "abs", 6: "mov", 7: "neg", 12: "round.w", 13: "trunc.w",
      14: "ceil.w", 15: "floor.w", 32: "cvt.s", 36: "cvt.w"}
def fpu(w):
    op = w >> 26
    if op in (0x31, 0x39):
        base, ft, off = (w >> 21) & 31, (w >> 16) & 31, ((w & 0xFFFF) ^ 0x8000) - 0x8000
        return "%s $f%d, %d(%s)" % ("lwc1" if op == 0x31 else "swc1", ft, off, REG[base])
    if op != 0x11: return None
    fmt, ft, fs, fd, fn = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w >> 6) & 31, w & 63
    if fmt == 4: return "mtc1 %s, $f%d" % (REG[ft], fs)
    if fmt == 0: return "mfc1 %s, $f%d" % (REG[ft], fs)
    if fmt == 8: return "bc1%s %+d" % ("tf"[(ft & 1)], (((w & 0xFFFF) ^ 0x8000) - 0x8000) * 4 + 4)
    if fmt in FMT:
        if fn >= 48: return "c.%d.%s $f%d, $f%d" % (fn & 15, FMT[fmt], fs, ft)
        return "%s.%s $f%d, $f%d, $f%d" % (FN.get(fn, "f%d" % fn), FMT[fmt], fd, fs, ft)
    return "cop1 %08x" % w
if __name__ == "__main__":
    f = int(sys.argv[1], 16); e = int(sys.argv[2], 16) if len(sys.argv) > 2 else fend(f)
    for a in range(f, e, 4):
        w = struct.unpack_from("<I", img, a)[0]
        t = fpu(w)
        if t is None: t = repr(next(iter(decode(img, a, a + 4))))
        if (w >> 16) == 0x3C04 or (w >> 16) & 0xFC1F == 0x3C00: t += "      ; (float %r si mtc1)" % struct.unpack("<f", struct.pack("<I", (w & 0xFFFF) << 16))[0]
        print("%7x  %s" % (a, t))
