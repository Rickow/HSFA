#!/usr/bin/env python3
"""Extracteur de carto pour X_DATA.BIN (AFS) de SF Alpha Anthology.

- Classe les 553 entrees AFS par type (sniff de tete + heuristiques).
- Ecrit un manifeste CSV complet (toutes entrees).
- Extrait sur disque les entrees "jeu" : MWo3 (programme 68k, nomme par son
  nom interne), programmes son Z80/QSound (0x48000), gros blobs gfx (>=2Mo).
- Produit un regroupement sequentiel : chaque MWo3 + les entrees qui suivent
  jusqu'au MWo3 suivant = un "groupe jeu" (la TOC est ordonnee par jeu).

Sortie : E:/CLAUDE CODE/anthology_extract/
"""
import os, struct, mmap, re

PATH = r"E:/ROMS/PS2/Street Fighter Alpha Anthology/Street Fighter Alpha Anthology (USA)/X_DATA.BIN"
OUTDIR = r"E:/CLAUDE CODE/anthology_extract"

def classify(mm, o, s):
    h = mm[o:o+8]
    if h[2:6] == b"MWo3":
        seg = mm[o+0x20:o+0x80]
        m = re.search(rb"[A-Za-z0-9_]+\.bin", seg)
        return "MWo3", (m.group().decode() if m else "noname")
    if h[2:6] == b"TIM2": return "TIM2", None
    if h[2:6] == b"MOMO": return "MOMO", None
    # Z80 QSound program: commence par f3 (DI) et taille 0x48000 typique
    if h[0] == 0xf3 and s in (0x48000, 0x40000, 0x50000):
        return "Z80", None
    if s >= 2_000_000:
        return "GFX", None
    return "DATA", None

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    with open(PATH, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        count = struct.unpack_from("<I", mm, 4)[0]
        toc = [struct.unpack_from("<II", mm, 8+8*i) for i in range(count)]

        # 1) manifeste complet
        kinds = []
        with open(os.path.join(OUTDIR, "manifest.csv"), "w", encoding="utf-8") as c:
            c.write("idx,offset,size,kind,name\n")
            for i,(o,s) in enumerate(toc):
                k, nm = classify(mm, o, s)
                kinds.append((k, nm))
                c.write(f"{i},{o},{s},{k},{nm or ''}\n")

        # 2) regroupement par jeu (segments delimites par les MWo3)
        groups = []
        cur = None
        for i,(o,s) in enumerate(toc):
            k, nm = kinds[i]
            if k == "MWo3":
                cur = {"mwo3_idx": i, "name": nm, "members": []}
                groups.append(cur)
            if cur is not None:
                cur["members"].append((i, k, nm, o, s))

        # 3) extraction des entrees jeu + rapport groupe
        report = []
        report.append(f"X_DATA.BIN : {count} entrees")
        from collections import Counter
        cnt = Counter(k for k,_ in kinds)
        report.append("Types: " + ", ".join(f"{k}={v}" for k,v in cnt.most_common()))
        report.append("")
        for g in groups:
            name = g["name"].replace(".bin","")
            report.append(f"=== GROUPE {name}  (MWo3 e{g['mwo3_idx']}) ===")
            for (i,k,nm,o,s) in g["members"]:
                tag = ""
                # extraire MWo3 / Z80 / GFX
                if k in ("MWo3","Z80","GFX"):
                    suffix = {"MWo3":"_prog68k.mwo3","Z80":"_z80.bin","GFX":f"_gfx_e{i}.bin"}[k]
                    fn = f"{name}{suffix}" if k!="GFX" else f"{name}_gfx_e{i}.bin"
                    with open(os.path.join(OUTDIR, fn), "wb") as out:
                        out.write(mm[o:o+s])
                    tag = f" -> {fn}"
                report.append(f"  e{i:<4} {k:5} {s:>10,}  {nm or ''}{tag}")
            report.append("")
        rep = "\n".join(report)
        with open(os.path.join(OUTDIR, "carto.txt"), "w", encoding="utf-8") as r:
            r.write(rep)
        print(rep)
        mm.close()

if __name__ == "__main__":
    main()
