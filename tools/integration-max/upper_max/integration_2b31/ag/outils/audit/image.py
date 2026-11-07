"""(agent_audit_id) accès en ordre PS2 aux données d'une construction (ROM programme + blocs externes)"""
import os, struct
RB = 0x1F0000
PS2 = open("@UM_EXTRACT@/decompressed/ro5_usa_prog68k.bin", "rb").read()
ROMS = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
def sw(b): return bytes(x for i in range(0, len(b) - 1, 2) for x in (b[i + 1], b[i]))
class Banc:
    def __init__(self, d):
        self.d = d
        self.rom = b"".join(open(os.path.join(d, "roms_ro5/sfa3ud", f), "rb").read() for f in ROMS)  # ordre fichier
        import re, collections
        c = collections.Counter()
        for l in open(os.path.join(d, "carte_image.txt"), encoding="utf-8", errors="replace"):
            m = re.search(r"\$([0-9a-f]+)\.L,A[0-7]  \[PS2 00([0-9a-f]{6})\]", l)
            if m:
                a, p = int(m.group(1), 16), int(m.group(2), 16)
                if 0xC80000 <= a < 0xD80000: c[a - p] += 1
        self.dext = c.most_common(1)[0][0]
        self.coupure = 0xC80000 - self.dext
        self.ext = {}
        for f in os.listdir(d):
            if f.startswith("ext_") and f.endswith(".bin"):
                self.ext[int(f[4:10], 16)] = sw(open(os.path.join(d, f), "rb").read())
    def img(self, a, n):
        """octets en ordre PS2 à l'adresse 68K a"""
        a &= 0xFFFFFF
        if a < 0x400000: return self.rom[a:a + n]
        for b, x in self.ext.items():
            if b <= a < b + len(x): return x[a - b:a - b + n]
        return None
    def ps2(self, p, n):
        """données PS2 (adresse d'exécution) telles que la construction les a : image (< 0x904AE0) ou bloc $C80000"""
        return self.img(self.a68(p), n)
    def a68(self, p):
        return p - 0x569CC0 if p < self.coupure else p + self.dext
    def p_de(self, a):
        """adresse 68K -> adresse PS2 (données natives), ou None"""
        a &= 0xFFFFFF
        if 0xA1000 <= a < 0x3A0000: return a + 0x569CC0
        if 0xC80000 <= a < 0xC80000 + len(self.ext.get(0xC80000, b"")): return a - self.dext
        return None
def natif(p, n): return PS2[p - RB:p - RB + n]
