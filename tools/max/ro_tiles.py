"""Tuiles de l'Anthology, dans l'espace de pixels de FBNeo, via `src/hsfa/anthgfx.py` (HANDOFF §45).

Unité = un code de tuile CPS2 = 16 « slots » (lignes de 16 pixels) : 16x16 m -> 1 unité, 32x32 m -> 4 unités
(4m..4m+3, lignes de 32 px coupées en 2 slots), 8x8 ignorées (demi-unités dupliquées).
L'Anthology stocke les valeurs BRUTES de la ROM CPS2 ; FBNeo affiche 15 - brute : on convertit ici, si bien que
le transparent vaut 0 comme dans `cps2_tiles.py` et après la permutation PSP (i -> 16-i).
⚠️ Une première version (lecture via gfx.py, valeurs brutes, 3 conteneurs) donnait un FAUX NÉGATIF (12 % / 5 %)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pickle, glob
sys.path.insert(0, paths.UNTRANSPILE)
import anthgfx

def units(buf):
    """-> [bytes(256)] unités CPS2 d'un conteneur, pixels en espace FBNeo (15 - brute)."""
    out = []
    for k, m, px in anthgfx.tiles(buf):
        if px is None or k == 0: continue
        s = anthgfx.to_slots(k, px)                        # (16 ou 64, 16)
        for u in range(0, s.shape[0], 16):
            out.append(bytes((15 - s[u:u+16]).astype("uint8").ravel()))
    return out

def tileset(module, conts=None):
    """Ensemble des unités de tous les conteneurs graphiques du module (roN_usa_gfx_*.bin)."""
    cache = os.path.join(paths.CACHE, f"anthology_{module}_units.pkl")
    if os.path.exists(cache): return pickle.load(open(cache, "rb"))
    files = sorted(glob.glob(os.path.join(paths.anthology(), f"{module}_usa_gfx_*.bin")))
    if conts: files = [f for f in files if any(c in os.path.basename(f) for c in conts)]
    s = set()
    for f in files:
        buf = open(f, "rb").read()
        if anthgfx.is_container(buf): s.update(units(buf))
    pickle.dump(s, open(cache, "wb")); return s
