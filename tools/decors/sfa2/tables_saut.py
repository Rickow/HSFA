"""Tables de sauts en ligne (move.w (d8,PC,D0.w),D1 ; jsr/jmp (d8,PC,D1.w)) : cibles par décor."""
import struct, sys
def lit(img, s, n=32):
    op = struct.unpack_from(">H", img, s + 4)[0]; ext = struct.unpack_from(">H", img, s + 6)[0]
    assert op & 0xF1FF == 0x303B or op & 0xF1FF == 0x323B, hex(op)
    t1 = s + 6 + (ext & 0xFF if ext & 0x80 == 0 else (ext & 0xFF) - 0x100)
    op2 = struct.unpack_from(">H", img, s + 8)[0]; ext2 = struct.unpack_from(">H", img, s + 10)[0]
    d2 = ext2 & 0xFF; d2 = d2 - 0x100 if d2 & 0x80 else d2
    t2 = s + 10 + d2
    kind = {0x4EBB: "jsr", 0x4EFB: "jmp"}[op2]
    return kind, t1, t2, [t2 + struct.unpack_from(">h", img, t1 + 2 * i)[0] for i in range(n)]
if __name__ == "__main__":
    img = open(sys.argv[1], "rb").read()
    for s in sys.argv[2:]:
        k, t1, t2, c = lit(img, int(s, 16))
        print("%s %s table $%06X base $%06X :" % (s, k, t1, t2), " ".join("%d:%X" % (i, x) for i, x in enumerate(c)))
