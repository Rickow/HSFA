"""En-têtes et tables de boîtes des projectiles MAX au format arcade (2026-10-07).
PSP : $60 (PSP 0x80) -> en-tête de 5 LONGS absolus (tables -> 0xD0..0xE0 par 0x72998) ; $88 (PSP 0xC8) -> table d'index
de boîtes (4 octets par pas). Arcade ($3323A, $331D0) : en-tête de 5 MOTS relatifs -> $90..$A0 ; tables 0-3 = boîtes de
8 o (4 mots x, y, l, h : ordre des octets à inverser), table 4 = attaques de 32 o (boîte 4 mots, puis 24 octets) ;
table $88 : octets identiques. Vérifié sur le Hadoken de Ryu (attaques PSP 0x2830AA / arcade $72DE8 de sfa3ud) :
attaques identiques SAUF les octets $12 et $14 (sous-type de l'étincelle d'impact) = ×2 dans l'arcade (2026-10-11).
Sortie : donnees_projectiles_max.s (TABP_<en-tête>, TABS_<table $88>) + projectiles_max.json (adresse PSP -> symbole)."""
import struct, json, re, glob
from traduire import img, refs_code
U = lambda a: struct.unpack_from("<I", img, a)[0]
consts = set()
for f in glob.glob("brouillon_*.s"):
    for m in re.finditer(r"move\.l\s+#(?:\$|TABP_|TABS_)([0-9a-f]+), \$(60|88)\(a[0-6]\)", open(f).read()):
        consts.add((int(m.group(1), 16), m.group(2)))
entetes = sorted(a for a, c in consts if c == "60"); sous = sorted(a for a, c in consts if c == "88")
bornes = sorted(set(refs_code()) | set(entetes) | set(sous) | {U(h + 4 * k) for h in entetes for k in range(5)})
fin = lambda a: min([b for b in bornes if b > a] + [a + 0x200])
out = ["; Projectiles MAX : en-têtes / boîtes au format arcade ($3323A, $331D0) — projectiles_max.py"]; sym = {}
faites = set()
for h in entetes:
    t = [U(h + 4 * k) for k in range(5)]
    out.append("TABP_%x:   ; en-tête PSP %#x" % (h, h))
    out += ["        dc.w    %s_%x-TABP_%x" % ("A" if k == 4 else "B", x, h) for k, x in enumerate(t)]
    sym[h] = "TABP_%x" % h
    for k, x in enumerate(t):
        cle = ("A" if k == 4 else "B", x)
        if cle in faites: continue
        faites.add(cle); n = fin(x) - x
        if k < 4:
            out.append("B_%x:   ; boîtes PSP %#x (%d entrées de 8 o)" % (x, x, n // 8))
            for e in range(n // 8):
                out.append("        dc.w    " + ", ".join("$%04x" % (v & 0xFFFF) for v in struct.unpack_from("<4h", img, x + 8 * e)))
        else:
            out.append("A_%x:   ; attaques PSP %#x (%d entrées de 32 o)" % (x, x, n // 32))
            for e in range(n // 32):
                b = x + 32 * e
                out.append("        dc.w    " + ", ".join("$%04x" % (v & 0xFFFF) for v in struct.unpack_from("<4h", img, b)))
                r = bytearray(img[b + 8:b + 32])
                for o in (0x12, 0x14):              # (2026-10-11) sous-type d'étincelle d'impact : ×2 dans l'arcade
                    assert r[o - 8] * 2 <= 0xFF, "attaque %#x : octet $%x = %#x" % (b, o, r[o - 8])
                    r[o - 8] *= 2                   # (Hadoken de Ryu 0x2830AA = $72DE8 de sfa3ud : seuls écarts)
                out.append("        dc.b    " + ", ".join("$%02x" % v for v in r))
for s0 in sous:
    n = fin(s0) - s0
    out.append("TABS_%x:   ; index de boîtes PSP %#x (%d entrées de 4 o)" % (s0, s0, n // 4))
    out.append("        dc.b    " + ", ".join("$%02x" % v for v in img[s0:s0 + n]))
    sym[s0] = "TABS_%x" % s0
open("donnees_projectiles_max.s", "w").write("\n".join(out) + "\n")
json.dump({"%x" % k: v for k, v in sym.items()}, open("projectiles_max.json", "w"), indent=0)
print(len(entetes), "en-têtes,", len(sous), "tables $88")
