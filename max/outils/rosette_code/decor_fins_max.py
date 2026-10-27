"""Sprites de DÉCOR des fins MAX (images propres au pac de la fin) -> tuiles CPS2 + frames 68K + pas arcade de 8 o, 2026-10-10.
PSP : état de fin +$118[n] = pas8 (section 0x20002) indexés par 0x20004[n] ; frames du trio du pac (0x1000019 frames,
0x2000019 tuiles, 0x4000019 palettes ; case = UNE tuile 16×16 ; attributs : bit 7 miroir H, bit 6 miroir V, bits 0-4
palette relative à la base de l'objet).
Arcade : les classes de décor animent en pas de 8 o (avance $1B6B6 / $1B6F8) : dc.b durée, drapeaux (bit 7 reprise,
bit 6 fin), 2 octets ; dc.l frame ; après un pas à reprise, dc.l pas de reprise (lu en +8). Tables globales ($81522
classe $48/01, $2F4284 classe $49/00-$11, $301FA2 classes $4A/$4E) : HSFA y ajoute de nouveaux n° -> nos labels.
Tuiles : banque graphique PAR FIN d'Upper (emplacement 4) -> codes LOCAUX (0 = 1re tuile du fichier de fin).
Conversion des pixels / palettes identique aux persos (convert_max, palettes_max) : brut = 15 − ((16 − i) mod 16),
couleur CPS2 [r] = PSP [r + 1].
Sorties : decor_fin_XX.s (frames FD%02X_n + table FIN118_%02X, ORG $D78000 + $40000 k), symboles dans
symboles_anims_max.s ; ~/.cache/sfa3max/converti/plXX/fin/decor/{tuiles.bin, palettes_cps2.bin, decor.json}.
Usage : python3 decor_fins_max.py"""
import os, sys, json, struct
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
sys.path.insert(0, os.path.join(ICI, "..", "convert"))
from plpac import split
from frames import frames
from maxtile import tiles, decode
import palettes_max
PAC = os.path.expanduser("~/.cache/sfa3max/data/textes/end%02x_e.pac")
CONV = os.path.expanduser("~/.cache/sfa3max/converti")
BASES = {0x26: 0xD78000, 0x27: 0xDB8000, 0x28: 0xDF8000, 0x29: 0xE38000}
TAILLE = 0x28000
NOMS = {0x26: "eagle", 0x27: "maki", 0x28: "yun", 0x29: "ingrid"}


def lire(cid):
    E = split(open(PAC % cid, "rb").read()); D = {t: d for t, d in E}
    F = frames(D[0x1000019]); g = D[0x2000019]; T = tiles(g)
    idx = list(struct.unpack_from("<%dH" % (len(D[0x20004]) // 2), D[0x20004]))
    idx = idx[:idx.index(0xFFFF)] if 0xFFFF in idx else idx
    return D, F, g, T, idx


def pas8(D, idx):
    """n° -> [(d, fl, frame, écart)] ; pas absolus partagés (même suite que la PSP)"""
    st = D[0x20002]; S = {}
    for v in idx:
        for k in range(80):
            p = v + k
            if 8 * p + 8 > len(st): break
            d, fl = struct.unpack_from("<2H", st, 8 * p); fr, ec = struct.unpack_from("<Hh", st, 8 * p + 4)
            S.setdefault(p, (d, fl, fr, ec))
            if d & 0xC000: break
    return S


def construire(cid):
    D, F, g, T, idx = lire(cid); S = pas8(D, idx)
    utiles = sorted({fr for (_, _, fr, _) in S.values() if fr < len(F)})
    hors = sorted({fr for (_, _, fr, _) in S.values() if fr >= len(F) and fr != 0x8000})
    tuiles, code_de = [], {}                       # dédoublonnage des tuiles (valeurs brutes CPS2)
    def code(i):
        t = decode(g, T[i][0])[0]
        px = [n for b in t for n in (b & 0xF, b >> 4)]
        brut = bytes(15 - ((16 - v) % 16) for v in px)
        b = bytes(brut[2 * k] | (brut[2 * k + 1] << 4) for k in range(128))
        if b not in code_de: code_de[b] = len(tuiles); tuiles.append(b)
        return code_de[b]
    base = BASES[cid]; b = bytearray(); adr = {}; asm = []; fix = []
    asm += ["; décor de la fin $%02X (%s) : frames du pac (FD%02X_n, codes LOCAUX de la banque gfx de fin) et pas de 8 o"
            " (FIN118_%02X, n° PSP de +$118) — généré par decor_fins_max.py" % (cid, NOMS[cid], cid, cid),
            "        org     $%06X" % base]
    def aligne():                                  # remplissage explicite (l'alignement de vasm met des NOP $4E71)
        k = -len(b) % 4
        if k: b.extend(bytes(k)); asm.append("        dcb.b   %d, 0" % k)
    for n in utiles:
        fr = F[n]; objs = []
        for k, cell in enumerate(fr["cells"]):
            if cell is None: continue
            c16 = fr["c"] & 0xFFFF; c16 -= 0x10000 if c16 & 0x8000 else 0      # ancre Y : mot signé (bit 16 = drapeau)
            dx, dy = (k % fr["w"]) * 16 - fr["a"], (k // fr["w"]) * 16 - c16
            attr = (0x20 if cell[1] & 0x80 else 0) | (0x40 if cell[1] & 0x40 else 0) | (cell[1] & 0x1F)
            objs.append((dx, dy, code(cell[0]), attr))
        aligne(); adr["FD%02X_%d" % (cid, n)] = base + len(b)
        if not objs:
            b += struct.pack(">H", 0x12); asm += ["FD%02X_%d:" % (cid, n), "        dc.w    $0012"]; continue
        b += struct.pack(">HHHH", 2, len(objs), len(objs) - 1, 0); ip = len(b); b += bytes(4)
        for _, _, c, a in objs: b += struct.pack(">HH", c, a)
        asm += ["FD%02X_%d:" % (cid, n), "        dc.w    2, %d, %d, 0" % (len(objs), len(objs) - 1),
                "        dc.l    PFD%02X_%d" % (cid, n)] + ["        dc.w    $%04x, $%04x" % (c, a) for _, _, c, a in objs]
        aligne(); struct.pack_into(">I", b, ip, base + len(b))
        for dx, dy, _, _ in objs: b += struct.pack(">hh", dx, dy)
        asm += ["PFD%02X_%d:" % (cid, n)] + ["        dc.w    %d, %d" % (dx, dy) for dx, dy, _, _ in objs]
    # table +$118 (mots relatifs) puis pas de 8 o
    aligne(); nom = "FIN118_%02X" % cid; adr[nom] = base + len(b); asm += ["%s:" % nom]
    lab = lambda p: "P8_%02X_%d" % (cid, p)
    for n, v in enumerate(idx):
        fix.append((len(b), lab(v), nom)); b += bytes(2); asm.append("        dc.w    %s-%s          ; n° %d" % (lab(v), nom, n))
    aligne()
    alertes = ["frames hors du pac (efct ?) : %s -> image vide" % hors] if hors else []
    for p in sorted(S):
        d, fl, fr, ec = S[p]; adr[lab(p)] = base + len(b)
        b += bytes([d & 0xFF, d >> 8, fl & 0xFF, fl >> 8])
        asm += ["%s:" % lab(p), "        dc.b    $%02x, $%02x, $%02x, $%02x" % (d & 0xFF, d >> 8, fl & 0xFF, fl >> 8)]
        f = "FD%02X_%d" % (cid, fr)
        if fr < len(F): fix.append((len(b), f, None)); b += bytes(4); asm.append("        dc.l    %s" % f)
        else: b += bytes(4); asm.append("        dc.l    0                  ; frame PSP %d hors du pac" % fr)
        if not d & 0xC000 and ec != 1: alertes.append("pas %d : écart %d hors fin (suite non consécutive)" % (p, ec))
        if d & 0x8000:
            q = p + ec
            if q not in S: alertes.append("pas %d : reprise %d hors des pas émis" % (p, q)); q = p
            fix.append((len(b), lab(q), None)); b += bytes(4); asm.append("        dc.l    %s          ; reprise" % lab(q))
    for o, cible, rel in fix:
        if rel is None: struct.pack_into(">I", b, o, adr[cible])
        else:
            dv = adr[cible] - adr[rel]; assert 0 <= dv <= 0x7FFF; struct.pack_into(">H", b, o, dv)
    assert len(b) <= TAILLE, len(b)
    _, ram = palettes_max.convert(D[0x4000019])
    return bytes(b), adr, asm, tuiles, ram, {"frames": len(utiles), "tuiles": len(tuiles), "anims": len(idx),
                                             "pas": len(S), "palettes": len(ram) // 16, "octets": len(b)}, alertes


if __name__ == "__main__":
    sym = []
    for cid in sorted(BASES):
        b, adr, asm, tuiles, ram, st, al = construire(cid)
        open(os.path.join(ICI, "decor_fin_%s.s" % NOMS[cid]), "w").write("\n".join(asm) + "\n")
        d = os.path.join(CONV, "pl%02x" % cid, "fin", "decor"); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "tuiles.bin"), "wb").write(b"".join(tuiles))
        open(os.path.join(d, "palettes_cps2.bin"), "wb").write(struct.pack("<%dH" % len(ram), *ram))
        open(os.path.join(d, "decor.bin"), "wb").write(b)
        json.dump(st, open(os.path.join(d, "decor.json"), "w"))
        sym.append("FIN118_%02X equ $%06X" % (cid, adr["FIN118_%02X" % cid]))
        print("$%02X %-6s : %s%s" % (cid, NOMS[cid], st, "".join("\n    ⚠ " + x for x in al)))
    f = os.path.join(ICI, "symboles_anims_max.s")
    L = [l for l in open(f).read().splitlines() if not l.startswith("FIN118_")]
    open(f, "w").write("\n".join(L + sym) + "\n")
