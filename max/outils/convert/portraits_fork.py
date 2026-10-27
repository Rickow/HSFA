"""Tuiles des portraits MAX pour le fork sfa3hx (à la suite de max_gfx.bin, premier code $5C06C).
Sortie ~/.cache/sfa3max/fork/ :
  max_portraits_gfx.bin : format interne de MAME (encode de gfx_fork), à charger au code $5C06C (octet $2E03600 de la
                          région) ou à concaténer après max_gfx.bin ;
  pXX_portraits_hx.bin  : table locale -> code global (u32 LE).
PAS de dédoublonnage : un objet CPS2 de largeur w lit code, code+1… (le quartet bas reboucle dans sa ligne de 16), donc
les codes globaux doivent garder la disposition locale : global = début du perso + local, début aligné sur 16
(tuiles transparentes de bourrage). Ordre fixe pl26, pl27, pl28, pl29 (codes consécutifs pour les 4 persos)."""
import os, numpy as np
from gfx_fork import encode
import paths
F = os.path.join(paths.CACHE, "fork"); C = os.path.join(paths.CACHE, "converti")   # (2026-10-18) racine SFA3MAX_CACHE
from gfx_fork import EXT0, HSFA_GFX
# (2026-10-18) premier code = juste après max_gfx.bin de la même racine ($5C06C avec la banque non étirée)
DEBUT = EXT0 + os.path.getsize(HSFA_GFX) // 128 + os.path.getsize(os.path.join(F, "max_gfx.bin")) // 128
def main():
    blob, code, rap = bytearray(), DEBUT, []
    vide = encode(np.full((16, 16), 15, np.uint8))
    for pl in ("pl26", "pl27", "pl28", "pl29"):
        p = os.path.join(C, pl, "portraits.bin")
        if not os.path.exists(p): continue
        while code % 16: blob += vide; code += 1
        b = np.fromfile(p, np.uint8).reshape(-1, 16, 8)
        px = np.empty((len(b), 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
        for t in px: blob += encode(t)
        tab = np.arange(code, code + len(px), dtype="<u4"); tab.tofile(os.path.join(F, "p%s_portraits_hx.bin" % pl[2:]))
        rap.append("%s : %d tuiles, codes $%X-$%X" % (pl, len(px), code, code + len(px) - 1)); code += len(px)
    ic = os.path.join(C, "icones", "icones.bin")          # icônes de la grille (icones_max.py), à la suite
    if os.path.exists(ic):
        while code % 16: blob += vide; code += 1
        b = np.fromfile(ic, np.uint8).reshape(-1, 16, 8)
        px = np.empty((len(b), 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
        for t in px: blob += encode(t)
        import json
        J = json.load(open(os.path.join(C, "icones", "icones.json")))
        for v in J.values(): v["code_global"] = "$%X" % (code + v["code_local"])
        json.dump(J, open(os.path.join(C, "icones", "icones.json"), "w"), indent=1, ensure_ascii=False)
        rap.append("icones : %d tuiles, codes $%X-$%X (icône k = code + 2k, bloc 2x2 : +1, +16, +17)" % (len(px), code, code + len(px) - 1))
        code += len(px)
    no = os.path.join(C, "noms", "noms.bin")              # cartouches de nom (noms_max.py), à la suite
    if os.path.exists(no):
        while code % 16: blob += vide; code += 1
        b = np.fromfile(no, np.uint8).reshape(-1, 16, 8)
        px = np.empty((len(b), 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
        for t in px: blob += encode(t)
        import json
        J = json.load(open(os.path.join(C, "noms", "noms.json")))
        for v in J.values(): v["code_global"] = "$%X" % (code + v["code_local"])
        json.dump(J, open(os.path.join(C, "noms", "noms.json"), "w"), indent=1, ensure_ascii=False)
        rap.append("noms : %d tuiles, codes $%X-$%X (nom = code_global, largeur_tuiles tuiles consécutives)" % (len(px), code, code + len(px) - 1))
        code += len(px)
    bn = os.path.join(C, "bandeau_noms", "tuiles.bin")    # (2026-10-18) noms des frises « 1P nom » (bandeau_noms_max.py)
    if os.path.exists(bn):
        while code % 16: blob += vide; code += 1
        b = np.fromfile(bn, np.uint8).reshape(-1, 16, 8)
        px = np.empty((len(b), 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
        for t in px: blob += encode(t)
        import json
        J = json.load(open(os.path.join(C, "bandeau_noms", "bandeau_noms.json")))
        for v in J.values(): v["code_global"] = "$%X" % (code + v["code_local"])
        json.dump(J, open(os.path.join(C, "bandeau_noms", "bandeau_noms.json"), "w"), indent=1, ensure_ascii=False)
        rap.append("bandeau_noms : %d tuiles, codes $%X-$%X (nom = code_global, largeur_tuiles tuiles consécutives)" % (len(px), code, code + len(px) - 1))
        code += len(px)
    wn = os.path.join(C, "winner_noms", "tuiles.bin")     # (2026-10-18) « WINNER:<nom> » vertical (winner_noms_max.py)
    if os.path.exists(wn):
        while code % 16: blob += vide; code += 1
        b = np.fromfile(wn, np.uint8).reshape(-1, 16, 8)
        px = np.empty((len(b), 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
        for t in px: blob += encode(t)
        import json
        J = json.load(open(os.path.join(C, "winner_noms", "winner_noms.json")))
        for v in J.values(): v["code_global"] = "$%X" % (code + v["code_local"])
        json.dump(J, open(os.path.join(C, "winner_noms", "winner_noms.json"), "w"), indent=1, ensure_ascii=False)
        rap.append("winner_noms : %d tuiles, codes $%X-$%X (nom k : colonne k, tuiles code + 16·y)" % (len(px), code, code + len(px) - 1))
        code += len(px)
    cn = os.path.join(C, "carte_noms", "tuiles.bin")      # (2026-10-18) colonne de nom de la carte du monde (carte_noms_max.py)
    if os.path.exists(cn):
        while code % 16: blob += vide; code += 1
        b = np.fromfile(cn, np.uint8).reshape(-1, 16, 8)
        px = np.empty((len(b), 16, 16), np.uint8); px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
        for t in px: blob += encode(t)
        import json
        J = json.load(open(os.path.join(C, "carte_noms", "carte_noms.json")))
        for v in J.values(): v["code_global"] = "$%X" % (code + v["code_local"])
        json.dump(J, open(os.path.join(C, "carte_noms", "carte_noms.json"), "w"), indent=1, ensure_ascii=False)
        rap.append("carte_noms : %d tuiles, codes $%X-$%X (nom k : colonne k, tuiles code + 16·y)" % (len(px), code, code + len(px) - 1))
        code += len(px)
    open(os.path.join(F, "max_portraits_gfx.bin"), "wb").write(blob)
    rap.append("max_portraits_gfx.bin : %d tuiles (%d o) à partir du code $%X ; prochain code libre $%X"
               % (len(blob) // 128, len(blob), DEBUT, code))
    open(os.path.join(F, "rapport_portraits.txt"), "w").write("\n".join(rap) + "\n"); print("\n".join(rap))
if __name__ == "__main__":
    main()
