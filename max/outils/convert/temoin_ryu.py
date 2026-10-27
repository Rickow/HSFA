"""TÉMOIN d'échelle (demande HSFA / utilisateur, 2026-10-18) : Ryu PSP (pl00) passé par EXACTEMENT la chaîne des persos MAX
(convert_max.convert -> frames_max.construire -> table de tuiles façon gfx_fork -> palettes_max.convert), pour l'afficher
par le même chemin qu'une frame d'Eagle à côté du Ryu natif d'Upper.
Sorties (~/.cache/sfa3max/converti/pl00_temoin/) :
  bank.bin, frames.json            : comme converti/plXX/ (convert_max) ;
  frames_00.s / frames_00.bin      : frames F00_n au format des frames MAX (frames_max.construire), ORG $D40000 (bloc
                                     d'Eagle : à charger À LA PLACE de frames_26.bin dans la construction d'essai) ;
  pl00_hx.bin                      : table code local -> code global (u32 LE), règle de gfx_fork (ROM SFA3, puis
                                     Upper, puis max_gfx) ; tuiles introuvables -> max_gfx_temoin.bin (codes à la suite) ;
  palettes_module.bin / palettes_cps2.bin : palettes de combat PSP de Ryu converties (palettes_max.convert) ;
  correspondance.json              : n° de frame PSP -> frame NATIVE de Ryu dans Upper (frame_map_ro5 : décalage du
                                     module, adresse exécutable) + poses choisies (garde, debout, accroupi, coups).
Usage : python temoin_ryu.py"""
import os, sys, json, struct
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "rosette_code")); sys.path.insert(0, os.path.join(ICI, "..", "frames289"))
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import numpy as np
import paths
from plpac import split
import convert_max as CM, palettes_max as PM, gfx_fork as G
import frames_max as FM
from cps2_tiles import cps2_pixels
SORTIE = os.path.join(paths.CACHE, "converti", "pl00_temoin")


def main():
    os.makedirs(SORTIE, exist_ok=True)
    C = CM.convert("pl00")
    with open(os.path.join(SORTIE, "bank.bin"), "wb") as f:
        for t in C["bank"]:
            t = t or bytes([15] * 256); f.write(bytes(t[2 * i] | (t[2 * i + 1] << 4) for i in range(128)))
    frames = [{"T": fr["T"], "objs": fr["objs"]} for fr in C["frames"]]
    json.dump(frames, open(os.path.join(SORTIE, "frames.json"), "w"))
    # frames 68K : frames_max.construire avec le même code, perso $00 au bloc d'Eagle
    FM.CONV = os.path.join(paths.CACHE, "converti"); FM.BASES = {0x00: 0xD40000}; FM.NOMS = {0x00: "ryu_temoin"}
    import builtins
    vrai_open = builtins.open
    def ouvre(p, *a, **k):                      # frames.json du témoin à la place de converti/pl00/frames.json
        if p == os.path.join(FM.CONV, "pl00", "frames.json"): p = os.path.join(SORTIE, "frames.json")
        return vrai_open(p, *a, **k)
    FM.open = ouvre
    b, adr, asm, al = FM.construire(0x00, set(range(len(frames))))
    open(os.path.join(SORTIE, "frames_00.s"), "w").write("\n".join(asm) + "\n")
    open(os.path.join(SORTIE, "frames_00.bin"), "wb").write(b)
    open(os.path.join(SORTIE, "symboles_frames_00.s"), "w").write("\n".join("F00_%d equ $%06X" % (n, a) for n, a in sorted(adr.items())) + "\n")
    # table de tuiles (règle de gfx_fork, sans rien écrire dans ~/.cache/sfa3max/fork)
    idx = {}
    for c, t in enumerate(cps2_pixels()): idx.setdefault(bytes(15 - v for v in t), c)
    up = open(G.HSFA_GFX, "rb").read(); nU = len(up) // 128
    for k in range(nU): idx.setdefault(G.decode(up[128 * k:128 * k + 128]).tobytes(), G.EXT0 + k)
    F = os.path.join(paths.CACHE, "fork") + "/"
    mg = open(F + "max_gfx.bin", "rb").read(); base = G.EXT0 + nU
    for k in range(len(mg) // 128): idx.setdefault(G.decode(mg[128 * k:128 * k + 128]).tobytes(), base + k)
    nP = os.path.getsize(F + "max_portraits_gfx.bin") // 128
    base_plus = base + len(mg) // 128 + nP
    px = np.fromfile(os.path.join(SORTIE, "bank.bin"), np.uint8).reshape(-1, 16, 8)
    pix = np.empty((px.shape[0], 16, 16), np.uint8); pix[:, :, 0::2] = px & 15; pix[:, :, 1::2] = px >> 4
    VIDE = idx[bytes([15] * 256)]; tab = []; neuves = bytearray(); st = {"ROM SFA3": 0, "Upper": 0, "MAX": 0, "neuves": 0, "vides": 0}
    for l in range(len(pix)):
        if not (pix[l] != 15).any(): tab.append(VIDE); st["vides"] += 1; continue
        cle = pix[l].tobytes()
        if cle in idx:
            c = idx[cle]; tab.append(c); st["ROM SFA3" if c < G.EXT0 else "Upper" if c < base else "MAX"] += 1; continue
        c = base_plus + len(neuves) // 128; neuves += G.encode(pix[l]); idx[cle] = c; tab.append(c); st["neuves"] += 1
    open(os.path.join(SORTIE, "pl00_hx.bin"), "wb").write(struct.pack("<%dI" % len(tab), *tab))
    if neuves: open(os.path.join(SORTIE, "max_gfx_temoin.bin"), "wb").write(neuves)
    # palettes
    mod, ram = PM.convert(split(open(os.path.join(paths.pac_dir(), "pl00_e.pac"), "rb").read())[2][1])
    open(os.path.join(SORTIE, "palettes_module.bin"), "wb").write(struct.pack("<%dH" % len(mod), *mod))
    open(os.path.join(SORTIE, "palettes_cps2.bin"), "wb").write(struct.pack("<%dH" % len(ram), *ram))
    # correspondance PSP -> frame native d'Upper
    from frame_map_ro5 import build_map5
    p2r, nrec = build_map5()
    corr = {str(n): {"module": "%#x" % o, "exec": "%#x" % (o + 0x1F0000), "similarite": s} for n, (o, s) in sorted(p2r.items())}
    import tables_anim as TA
    A = TA.animations("pl00")
    poses = {}
    for nom, (t, n) in {"garde": ("$2B0", 0), "marche_avant": ("$2B0", 1), "accroupi": ("$2B0", 6),
                        "poing_debout_fort": ("$2B4", 2), "pied_accroupi_fort": ("$2B4", 17)}.items():
        x = next((x for x in A.get(t, []) if x["n"] == n), None)
        frs = [st_["frame"] for st_ in (x or {}).get("steps") or []][:4]
        poses[nom] = {"table": t, "n": n, "frames_psp": frs, "upper": [corr.get(str(f)) for f in frs]}
    json.dump({"poses": poses, "psp_vers_upper": corr, "frames_psp": len(frames), "appariees": len(corr)},
              open(os.path.join(SORTIE, "correspondance.json"), "w"), indent=1)
    print("frames %d (%d o, %s) ; tuiles %s ; correspondance %d / %d" % (len(frames), len(b), al or "sans alerte", st, len(corr), len(frames)))
    print(json.dumps(poses, indent=1)[:1500])


if __name__ == "__main__":
    main()
