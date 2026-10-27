"""Frames de combat des persos MAX (symboles F%02X_n des pas d'animation) -> données 68K en DISPOSITION ARCADE.
Accord HSFA (2026-10-10) : codes LOCAUX à la banque du perso (conversion locale -> globale au rendu par plXX_hx.bin) ;
données hors ROM programme, dans les blocs externes du fork : $D40000 (Eagle), $D80000 (Maki), $DC0000 (Yun),
$E00000 (Ingrid), 256 Ko chacun ; la mise en disposition image est faite par convertit_max.py (HSFA).
Format (frame de type 2 du moteur, notes frames289/README.md) :
  F%02X_n : dc.w 2, T (Σ tuiles), n−1 ; bourrage jusqu'au multiple de 4 ; dc.l POS ; n × dc.w code, attributs
  POS     : n × dc.w dx, dy (aligné sur 4)
  frame sans objet : dc.w $0012 (frame vide d'un mot).
Sorties : frames_XX.s (assemblable seul, ORG du bloc), frames_XX.bin (octets calculés ici, contrôle), et
symboles_frames_max.s (F%02X_n equ adresse) inclus dans l'assemblage du code.
Usage : python3 frames_max.py   (tous les persos : toutes les frames de frames.json + n° hors plage référencés)"""
import os, re, json, struct
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max"))           # (2026-10-18) racine du cache (version : SFA3MAX_CACHE)
CONV = os.path.join(RACINE, "converti")
SORTIE_S = os.environ.get("SFA3MAX_SORTIE_S", ICI)   # dossier des .s produits (défaut : rosette_code)
BASES = {0x26: 0xD40000, 0x27: 0xD80000, 0x28: 0xDC0000, 0x29: 0xE00000}
TAILLE_BLOC = 0x40000
NOMS = {0x26: "eagle", 0x27: "maki", 0x28: "yun", 0x29: "ingrid"}


def references():
    """symboles F%02X_n employés par les sources 68K"""
    refs = {c: set() for c in BASES}
    for f in os.listdir(ICI):
        if f.endswith(".s") and not f.startswith(("frames_", "symboles_frames")):
            for c, n in re.findall(r"\bF(2[6-9])_(\d+)\b", open(os.path.join(ICI, f)).read()):
                refs[int(c, 16)].add(int(n))
    return refs


def construire(cid, nums):
    F = json.load(open(os.path.join(CONV, "pl%02x" % cid, "frames.json")))
    base = BASES[cid]; b = bytearray(); adr = {}; asm = []; alertes = []
    def aligne4():
        while len(b) % 4: b.extend(b"\0")
    asm += ["; frames de combat du perso $%02X (%s) — généré par frames_max.py, DISPOSITION ARCADE" % (cid, NOMS[cid]),
            "        org     $%06X" % base]
    for n in sorted(nums):
        fr = F[n] if n < len(F) else None
        objs = (fr or {}).get("objs") or []
        aligne4(); asm.append("        cnop    0,4")
        adr[n] = base + len(b)
        if n >= len(F):
            alertes.append("F%02X_%d : n° hors de frames.json (%d) -> frame vide (PSP 0x%X, à vérifier)" % (cid, n, len(F), n))
        if not objs:
            b += struct.pack(">H", 0x12)
            asm += ["F%02X_%d:" % (cid, n), "        dc.w    $0012              ; frame vide"]
            continue
        T = sum(((a >> 8 & 15) + 1) * ((a >> 12 & 15) + 1) for _, _, _, a in objs)
        if fr.get("T") not in (None, T): alertes.append("F%02X_%d : T json %s ≠ %d" % (cid, n, fr.get("T"), T))
        pos_lab = "POS%02X_%d" % (cid, n)
        b += struct.pack(">HHHH", 2, T, len(objs) - 1, 0)          # en-tête 6 o + bourrage (début aligné sur 4)
        i_ptr = len(b); b += b"\0\0\0\0"
        for _, _, code, attr in objs: b += struct.pack(">HH", code & 0xFFFF, attr & 0xFFFF)
        aligne4(); pos = base + len(b); struct.pack_into(">I", b, i_ptr, pos)
        for dx, dy, _, _ in objs: b += struct.pack(">hh", dx, dy)
        asm += ["F%02X_%d:" % (cid, n), "        dc.w    2, %d, %d, 0" % (T, len(objs) - 1), "        dc.l    %s" % pos_lab]
        asm += ["        dc.w    $%04x, $%04x" % (code & 0xFFFF, attr & 0xFFFF) for _, _, code, attr in objs]
        asm += ["        cnop    0,4", "%s:" % pos_lab]
        asm += ["        dc.w    %d, %d" % (dx, dy) for dx, dy, _, _ in objs]
    assert len(b) <= TAILLE_BLOC, "perso $%02X : %d o > bloc de 256 Ko" % (cid, len(b))
    return bytes(b), adr, asm, alertes


if __name__ == "__main__":
    refs = references(); sym = ["; adresses des frames MAX (blocs externes du fork) — généré par frames_max.py"]
    for cid in sorted(BASES):
        nf = len(json.load(open(os.path.join(CONV, "pl%02x" % cid, "frames.json"))))
        b, adr, asm, al = construire(cid, set(range(nf)) | refs[cid])   # toutes les frames (pas d'animation d'HSFA aussi)
        open(os.path.join(SORTIE_S, "frames_%s.s" % NOMS[cid]), "w").write("\n".join(asm) + "\n")
        open(os.path.join(RACINE, "frames_%02x.bin" % cid), "wb").write(b)
        sym += ["F%02X_%d equ $%06X" % (cid, n, a) for n, a in sorted(adr.items())]
        print("$%02X %-6s : %4d frames, %6d octets (bloc $%06X)%s" % (
            cid, NOMS[cid], len(adr), len(b), BASES[cid], "".join("\n    ⚠ " + x for x in al)))
    open(os.path.join(SORTIE_S, "symboles_frames_max.s"), "w").write("\n".join(sym) + "\n")
