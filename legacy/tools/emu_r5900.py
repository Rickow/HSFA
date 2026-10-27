import struct

class Emu:
    """Emulateur R5900 user-mode minimal (32-bit, pas de FPU/MMI) pour rejouer le composer BG."""
    def __init__(s, ram, spr):
        s.ram = bytearray(ram); s.spr = bytearray(spr)
        s.r = [0]*32; s.hi = 0; s.lo = 0
        s.writes = []
        s.calls = []
    def mem(s, a):
        if 0x70000000 <= a < 0x70004000: return s.spr, a - 0x70000000
        return s.ram, a & 0x1ffffff
    def r8(s, a):  m, o = s.mem(a); return m[o]
    def r16(s, a): m, o = s.mem(a); return struct.unpack_from('<H', m, o)[0]
    def r32(s, a): m, o = s.mem(a); return struct.unpack_from('<I', m, o)[0]
    def w8(s, a, v):  m, o = s.mem(a); m[o] = v & 0xff; s.writes.append((a, 1, v & 0xff))
    def w16(s, a, v): m, o = s.mem(a); struct.pack_into('<H', m, o, v & 0xffff); s.writes.append((a, 2, v & 0xffff))
    def w32(s, a, v): m, o = s.mem(a); struct.pack_into('<I', m, o, v & 0xffffffff); s.writes.append((a, 4, v & 0xffffffff))
    M64 = (1 << 64) - 1
    @staticmethod
    def sx16(v): return v - 0x10000 if v & 0x8000 else v
    @staticmethod
    def sx8(v): return v - 0x100 if v & 0x80 else v
    @staticmethod
    def sx32(v):
        v &= 0xffffffff
        return v - 0x100000000 if v & 0x80000000 else v
    @classmethod
    def s64(cls, v):
        v &= cls.M64
        return v - (1 << 64) if v & (1 << 63) else v
    @classmethod
    def se32(cls, v):
        return cls.sx32(v) & cls.M64

    def step(s, pc):
        """Execute l'instruction a pc. Retourne (npc, branch_target|None)."""
        R = s.r
        w = s.r32(pc)
        op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; rd = (w >> 11) & 31
        sa = (w >> 6) & 31; fn = w & 0x3f
        imm = w & 0xffff; simm = s.sx16(imm)
        take = None; npc = pc + 4
        if op == 0:
            if fn == 0x00: R[rd] = s.se32(R[rt] << sa)
            elif fn == 0x02: R[rd] = s.se32((R[rt] & 0xffffffff) >> sa)
            elif fn == 0x03: R[rd] = s.se32(s.sx32(R[rt]) >> sa)
            elif fn == 0x04: R[rd] = s.se32(R[rt] << (R[rs] & 31))
            elif fn == 0x06: R[rd] = s.se32((R[rt] & 0xffffffff) >> (R[rs] & 31))
            elif fn == 0x07: R[rd] = s.se32(s.sx32(R[rt]) >> (R[rs] & 31))
            elif fn == 0x08: take = R[rs] & 0xffffffff
            elif fn == 0x09:
                R[rd] = pc + 8; take = R[rs] & 0xffffffff; s.calls.append(take)
            elif fn == 0x0a:
                if R[rt] == 0: R[rd] = R[rs]
            elif fn == 0x0b:
                if R[rt] != 0: R[rd] = R[rs]
            elif fn == 0x10: R[rd] = s.hi
            elif fn == 0x11: s.hi = R[rs]
            elif fn == 0x12: R[rd] = s.lo
            elif fn == 0x13: s.lo = R[rs]
            elif fn == 0x18:
                p = s.sx32(R[rs]) * s.sx32(R[rt]); s.lo = s.se32(p); s.hi = s.se32(p >> 32)
            elif fn == 0x19:
                p = (R[rs] & 0xffffffff) * (R[rt] & 0xffffffff); s.lo = p & 0xffffffff; s.hi = (p >> 32) & 0xffffffff
            elif fn == 0x1a:
                a = s.sx32(R[rs]); b = s.sx32(R[rt])
                if b:
                    q = abs(a) // abs(b)
                    if (a < 0) != (b < 0): q = -q
                    s.lo = q & 0xffffffff; s.hi = (a - q * b) & 0xffffffff
            elif fn == 0x1b:
                a = R[rs] & 0xffffffff; b = R[rt] & 0xffffffff
                if b: s.lo = (a // b) & 0xffffffff; s.hi = (a % b) & 0xffffffff
            elif fn in (0x20, 0x21): R[rd] = s.se32(R[rs] + R[rt])
            elif fn in (0x22, 0x23): R[rd] = s.se32(R[rs] - R[rt])
            elif fn == 0x24: R[rd] = R[rs] & R[rt]
            elif fn == 0x25: R[rd] = R[rs] | R[rt]
            elif fn == 0x26: R[rd] = R[rs] ^ R[rt]
            elif fn == 0x27: R[rd] = ~(R[rs] | R[rt]) & 0xffffffff
            elif fn == 0x2a: R[rd] = 1 if s.s64(R[rs]) < s.s64(R[rt]) else 0
            elif fn == 0x2b: R[rd] = 1 if (R[rs] & s.M64) < (R[rt] & s.M64) else 0
            elif fn == 0x14: R[rd] = (R[rt] << (R[rs] & 63)) & s.M64          # dsllv
            elif fn == 0x16: R[rd] = (R[rt] & s.M64) >> (R[rs] & 63)            # dsrlv
            elif fn == 0x17: R[rd] = (s.s64(R[rt]) >> (R[rs] & 63)) & s.M64     # dsrav
            elif fn in (0x2c, 0x2d): R[rd] = (R[rs] + R[rt]) & s.M64            # dadd(u)
            elif fn in (0x2e, 0x2f): R[rd] = (R[rs] - R[rt]) & s.M64            # dsub(u)
            elif fn == 0x38: R[rd] = (R[rt] << sa) & s.M64                      # dsll
            elif fn == 0x3a: R[rd] = (R[rt] & s.M64) >> sa                      # dsrl
            elif fn == 0x3b: R[rd] = (s.s64(R[rt]) >> sa) & s.M64               # dsra
            elif fn == 0x3c: R[rd] = (R[rt] << (sa + 32)) & s.M64               # dsll32
            elif fn == 0x3e: R[rd] = (R[rt] & s.M64) >> (sa + 32)               # dsrl32
            elif fn == 0x3f: R[rd] = (s.s64(R[rt]) >> (sa + 32)) & s.M64        # dsra32
            else: raise Exception("special fn=%#x @%x w=%08x" % (fn, pc, w))
        elif op == 1:
            if rt in (0, 2):
                if s.s64(R[rs]) < 0: take = pc + 4 + (simm << 2)
                elif rt == 2: npc = pc + 8
            elif rt in (1, 3):
                if s.s64(R[rs]) >= 0: take = pc + 4 + (simm << 2)
                elif rt == 3: npc = pc + 8
            else: raise Exception("regimm rt=%d @%x" % (rt, pc))
        elif op == 2: take = ((pc + 4) & 0xf0000000) | ((w & 0x3ffffff) << 2)
        elif op == 3:
            R[31] = pc + 8; take = ((pc + 4) & 0xf0000000) | ((w & 0x3ffffff) << 2); s.calls.append(take)
        elif op == 4:
            if R[rs] == R[rt]: take = pc + 4 + (simm << 2)
        elif op == 5:
            if R[rs] != R[rt]: take = pc + 4 + (simm << 2)
        elif op == 6:
            if s.s64(R[rs]) <= 0: take = pc + 4 + (simm << 2)
        elif op == 7:
            if s.s64(R[rs]) > 0: take = pc + 4 + (simm << 2)
        elif op == 0x14:
            if R[rs] == R[rt]: take = pc + 4 + (simm << 2)
            else: npc = pc + 8
        elif op == 0x15:
            if R[rs] != R[rt]: take = pc + 4 + (simm << 2)
            else: npc = pc + 8
        elif op == 0x16:
            if s.s64(R[rs]) <= 0: take = pc + 4 + (simm << 2)
            else: npc = pc + 8
        elif op == 0x17:
            if s.s64(R[rs]) > 0: take = pc + 4 + (simm << 2)
            else: npc = pc + 8
        elif op in (8, 9): R[rt] = s.se32(R[rs] + simm)
        elif op == 0x0a: R[rt] = 1 if s.s64(R[rs]) < simm else 0
        elif op == 0x0b: R[rt] = 1 if (R[rs] & s.M64) < (simm & s.M64) else 0
        elif op == 0x0c: R[rt] = R[rs] & imm
        elif op == 0x0d: R[rt] = R[rs] | imm
        elif op == 0x0e: R[rt] = R[rs] ^ imm
        elif op == 0x0f: R[rt] = s.se32(imm << 16)
        elif op == 0x19: R[rt] = (R[rs] + simm) & s.M64  # daddiu
        elif op == 0x20: R[rt] = s.sx8(s.r8((R[rs] + simm) & 0xffffffff)) & 0xffffffff
        elif op == 0x21: R[rt] = s.sx16(s.r16((R[rs] + simm) & 0xffffffff)) & 0xffffffff
        elif op == 0x23: R[rt] = s.se32(s.r32((R[rs] + simm) & s.M64 & 0xffffffff))
        elif op == 0x24: R[rt] = s.r8((R[rs] + simm) & 0xffffffff)
        elif op == 0x25: R[rt] = s.r16((R[rs] + simm) & 0xffffffff)
        elif op == 0x28: s.w8((R[rs] + simm) & 0xffffffff, R[rt])
        elif op == 0x29: s.w16((R[rs] + simm) & 0xffffffff, R[rt])
        elif op == 0x2b: s.w32((R[rs] + simm) & 0xffffffff, R[rt])
        elif op == 0x27: R[rt] = s.r32((R[rs] + simm) & 0xffffffff)   # lwu
        elif op == 0x37:
            a = (R[rs] + simm) & 0xffffffff
            R[rt] = s.r32(a) | (s.r32(a + 4) << 32)               # ld
        elif op == 0x1a or op == 0x1b: pass                        # ldl/ldr approx (ignore)
        elif op == 0x3f:
            a = (R[rs] + simm) & 0xffffffff
            s.w32(a, R[rt] & 0xffffffff); s.w32(a + 4, (R[rt] >> 32) & 0xffffffff)  # sd
        elif op == 0x22:  # lwl
            a = (R[rs] + simm) & 0xffffffff; b = a & 3; v = s.r32(a - b); sh = (3 - b) * 8
            R[rt] = ((v << sh) | (R[rt] & ((1 << sh) - 1))) & 0xffffffff if sh else v
        elif op == 0x26:  # lwr
            a = (R[rs] + simm) & 0xffffffff; b = a & 3; v = s.r32(a - b); sh = b * 8
            R[rt] = ((R[rt] & ~(0xffffffff >> sh) & 0xffffffff) | ((v & 0xffffffff) >> sh)) if sh else v
        elif op == 0x2a:  # swl
            a = (R[rs] + simm) & 0xffffffff; b = a & 3; al = a - b; v = s.r32(al); sh = (3 - b) * 8
            nv = ((v & ~(0xffffffff >> sh) & 0xffffffff) | ((R[rt] & 0xffffffff) >> sh)) if sh else (R[rt] & 0xffffffff)
            s.w32(al, nv)
        elif op == 0x2e:  # swr
            a = (R[rs] + simm) & 0xffffffff; b = a & 3; al = a - b; v = s.r32(al); sh = b * 8
            nv = (((R[rt] << sh) & 0xffffffff) | (v & ((1 << sh) - 1))) if sh else (R[rt] & 0xffffffff)
            s.w32(al, nv)
        else:
            raise Exception("op=%#x @%x w=%08x" % (op, pc, w))
        R[0] = 0
        return npc, take

    def run(s, pc, max_ins=3_000_000, r_init=None):
        R = s.r
        if r_init:
            for k, v in r_init.items(): R[k] = v
        R[31] = 0xDEAD0000
        if not R[29]: R[29] = 0x01f00000
        n = 0
        while n < max_ins:
            if pc == 0xDEAD0000: return n
            npc, take = s.step(pc)
            n += 1
            if take is not None:
                dnpc, dtake = s.step(pc + 4)  # delay slot
                n += 1
                if dtake is not None: raise Exception("branch in delay slot @%x" % (pc + 4))
                pc = take
            else:
                pc = npc
        raise Exception("max instructions atteint")
