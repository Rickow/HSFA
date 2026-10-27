"""Recense dans l'image traduite (ou arcade) tous les accès à $100(A5) (numéro de décor x 2) par motif d'opcode."""
import sys, struct, subprocess
img = open(sys.argv[1], "rb").read()
lim = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x94000
out = []
for a in range(0, lim, 2):
    op = struct.unpack_from(">H", img, a)[0]
    mode = (op >> 3) & 7; reg = op & 7
    # EA source (d16,A5) dans les 6 bits bas ; extension = $0100
    if mode == 5 and reg == 5 and struct.unpack_from(">H", img, a + 2)[0] == 0x0100:
        out.append(a)
    # cmpi.w #imm,(d16,A5) : 0c6d iiii 0100 ; move.w (d16,A5),(d16,A5) : 3b6d 0100 xxxx / 3b6d xxxx 0100
    if op == 0x0c6d and struct.unpack_from(">H", img, a + 4)[0] == 0x0100: out.append(a)
    if (op & 0xF1FF) == 0x3b40 - 0x40 + 0x40 and False: pass
    if op in (0x3b6d, 0x3b7c, 0x3b7b) and struct.unpack_from(">H", img, a + 4)[0] == 0x0100: out.append(a)
    if (op & 0xFFF8) == 0x3b40 and struct.unpack_from(">H", img, a + 2)[0] == 0x0100: out.append(a)   # move.w Dn,($100,A5)
for a in sorted(set(out)):
    r = subprocess.run(["unidasm", sys.argv[1], "-arch", "m68000", "-basepc", "%x" % a, "-skip", str(a), "-count", "6"],
                       capture_output=True, text=True).stdout.strip().splitlines()
    print(r[0] if r else hex(a))
