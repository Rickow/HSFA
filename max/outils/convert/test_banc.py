"""Paquet de test pour le banc MAME d'HSFA : Eagle à la place de Ryu (garde, accroupi, marches, coup léger).
Sortie : ~/.cache/sfa3max/converti/pl26/test_banc/{bank_test.bin, frames_test.json, LISEZMOI.md}
Banque COMPACTE : seules les cases PSP utilisées par les frames retenues, renumérotées avec la même règle
(case j' -> bloc 2x2 b, b+1, b+16, b+17 ; b = 32*(j'//8) + 2*(j'%8)) : codes locaux < 1 000, sous la taille de e258."""
import sys, os, json, struct
sys.path.insert(0, "../frames289"); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from convert_max import convert, bank_code
from frame_map import build_map
from frames import frames
from plpac import split
# correspondance frame PSP de Ryu -> frame PSP d'Eagle (choisie sur images ; marches de Ryu = « probables »)
MAP = {"garde": [(0, 0), (1, 2), (2, 5), (3, 7), (4, 9)],
       "accroupi": [(5, 13), (6, 14)],
       "marche avant (probable)": [(7, 17), (8, 19), (9, 20), (10, 22), (11, 23), (12, 25)],
       "marche arrière (probable)": [(13, 26), (14, 24), (15, 22), (16, 20), (17, 18)],
       "coup léger": [(36, 44), (37, 43)]}
def main():
    ryu = build_map()["psp2rec"]
    E = split(open(os.path.join(paths.pac_dir(), "pl26_e.pac"), "rb").read())
    F = frames(E[0][1]); C = convert("pl26")
    used = sorted({cell[0] for _, pairs in MAP.items() for _, e in pairs for cell in F[e]["cells"] if cell})
    newj = {j: k for k, j in enumerate(used)}
    nb = 32 * ((len(used) + 7) // 8)
    bank = [None] * nb
    for j, k in newj.items():
        _, old = bank_code(j); _, new = bank_code(k)
        for o, n in zip(old, new): bank[n] = C["bank"][o]
    out = os.path.join(paths.CACHE, "converti", "pl26", "test_banc"); os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "bank_test.bin"), "wb") as f:
        for t in bank:
            t = t or bytes([15] * 256)
            f.write(bytes(t[2*i] | (t[2*i+1] << 4) for i in range(128)))
    entries = []
    for action, pairs in MAP.items():
        for r, e in pairs:
            objs = []
            for (dx, dy, code, attr) in C["frames"][e]["objs"]:
                j = next(jj for jj in used if bank_code(jj)[0] == code)
                objs.append((dx, dy, bank_code(newj[j])[0], attr))
            entries.append({"action": action, "ryu_psp_frame": r,
                            "ryu_frame_fichier": hex(ryu[r]), "ryu_frame_execution": hex(ryu[r] + 0x1F0000),
                            "eagle_psp_frame": e, "T": 4 * len(objs), "objs": objs})
    json.dump(entries, open(os.path.join(out, "frames_test.json"), "w"), indent=1)
    # palettes : entrée PSP [2] (ABGR1555, index 0 = transparent) -> mots CPS2 0xFRGB (luminosité F) ;
    # pixel brut CPS2 r = index PSP i - 1 (r = 15 = transparent), donc palette CPS2[r] = PSP[r + 1], [15] = 0
    pal = E[2][1]; pw = []
    for k in range(len(pal) // 32):
        for r in range(16):
            v = struct.unpack_from("<H", pal, 32*k + 2*(r + 1))[0] if r < 15 else 0
            pw.append(0xF000 | ((v & 31) >> 1) << 8 | (((v >> 5) & 31) >> 1) << 4 | ((v >> 10) & 31) >> 1 if r < 15 else 0)
    open(os.path.join(out, "palettes_cps2.bin"), "wb").write(struct.pack(f"<{len(pw)}H", *pw))
    print("sous-palettes utilisées :", sorted({o[3] & 31 for e in entries for o in e["objs"]}), "; palettes :", len(pw) // 16)
    print(f"{len(used)} cases -> banque de test {nb} tuiles ({os.path.getsize(os.path.join(out, 'bank_test.bin'))} o) ; {len(entries)} frames -> {out}")
    return out, entries
if __name__ == "__main__":
    main()
