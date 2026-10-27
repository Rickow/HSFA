"""Palettes PSP (entrée [2] des plXX_e.pac, ABGR1555, index 0 = transparent) -> format du module Anthology ro3.

Validé sur Ryu (pl00) : ses 30 palettes PSP = les 30 palettes du module en fichier 0x451270, 30/30 identiques.
Conversion : couleur CPS2 [r] = PSP [r + 1] (r = 0..14), composantes 5 -> 4 bits (>> 1), mot 0x0RGB.
Format module (par palette, 16 mots u16 petit-boutistes) : 15 couleurs 0x0RGB (luminosité 0 : le moteur la pose),
puis le mot 15 = numéro de la palette dans le perso (0..29 chez Ryu).
Table moteur : fichier 0x451230 (PS2 0x641230) = 32 décalages u16 relatifs à elle-même, indexés par l'ID ($103) ;
30 palettes (0x3C0 o) par perso ; groupe choisi = ((ism + 1) * 2 + octet $129) * 5 palettes.
Palettes d'EFFETS : table moteur fichier 0x457B70 (PS2 0x647B70, 32 décalages s16, 24 palettes chez Ryu, 24-37 selon
le perso) ; côté PSP, bloc de 36 palettes (Ingrid 72) dans l'entrée [6] (section 22 en général), même conversion.
Sur les 26 persos arcade : palettes 8-23 identiques au module, 0-7 en grande partie RECOLORÉES sur PSP (aucune
règle simple) ⟹ pour les persos MAX, 0-7 sont à vérifier en jeu.
Sorties : ~/.cache/sfa3max/converti/plXX/palettes_module.bin (+ palettes_cps2.bin = même chose avec 0xF000, mot 15 = 0,
pour écrire directement la RAM de palettes CPS2 dans le banc) ; idem palettes_effets_module.bin / palettes_effets_cps2.bin."""
import sys, os, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split

def convert(pal):
    mod, ram = [], []
    for k in range(len(pal) // 32):
        cols = []
        for r in range(15):
            v = struct.unpack_from("<H", pal, 32*k + 2*(r + 1))[0]
            cols.append(((v & 31) >> 1) << 8 | (((v >> 5) & 31) >> 1) << 4 | ((v >> 10) & 31) >> 1)
        mod += cols + [k]; ram += [0xF000 | c for c in cols] + [0]
    return mod, ram

def bloc_effets(b6):
    """palettes d'effets dans l'entrée [6] : première suite de blocs de 32 o dont les mots 1-14 ont le bit 15
    (alpha PSP) ; 36 palettes chez la plupart des persos (Ingrid 72). Même permutation que les palettes de perso."""
    ispal = lambda a: a + 32 <= len(b6) and all(x & 0x8000 for x in struct.unpack_from("<16H", b6, a)[1:15])
    a = 0
    while a < len(b6) - 32:
        if ispal(a):
            n = 0
            while ispal(a + 32*n): n += 1
            if n >= 4: return a, n
            a += 32
        else: a += 2
    return None, 0

def verifier_effets_ryu():
    """table moteur fichier 0x457B70 (PS2 0x647B70) : 32 décalages s16 par ID, 24 palettes chez Ryu ;
    attendu : 8-23 identiques, 0-4 et 6 recolorées sur PSP"""
    b = open(os.environ["ANTHOLOGY_DIR"] + "/decompressed/ro3_usa_prog68k.bin", "rb").read()
    off = 0x457B70 + struct.unpack_from("<h", b, 0x457B70)[0]
    b6 = split(open(os.path.join(paths.pac_dir(), "pl00_e.pac"), "rb").read())[6][1]
    a, n = bloc_effets(b6)
    mod, _ = convert(b6[a:a + 32*n])
    return "".join("x" if mod[16*k:16*k+16] == list(struct.unpack_from("<16H", b, off + 32*k)) else "." for k in range(24))

def verifier_ryu():
    b = open(os.environ["ANTHOLOGY_DIR"] + "/decompressed/ro3_usa_prog68k.bin", "rb").read()
    off = 0x451230 + struct.unpack_from("<H", b, 0x451230)[0]          # ID 0 = Ryu
    mod, _ = convert(split(open(os.path.join(paths.pac_dir(), "pl00_e.pac"), "rb").read())[2][1])
    ref = struct.unpack_from(f"<{len(mod)}H", b, off)
    return sum(mod[16*k:16*k+16] == list(ref[16*k:16*k+16]) for k in range(len(mod) // 16)), len(mod) // 16

if __name__ == "__main__":
    print("Ryu : palettes identiques au module %d/%d" % verifier_ryu())
    print("Ryu : palettes d'effets identiques au module (0-23) :", verifier_effets_ryu())
    for pl in ("pl26", "pl27", "pl28", "pl29"):
        mod, ram = convert(split(open(os.path.join(paths.pac_dir(), f"{pl}_e.pac"), "rb").read())[2][1])
        d = os.path.join(paths.CACHE, "converti", pl); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "palettes_module.bin"), "wb").write(struct.pack(f"<{len(mod)}H", *mod))
        open(os.path.join(d, "palettes_cps2.bin"), "wb").write(struct.pack(f"<{len(ram)}H", *ram))
        b6 = split(open(os.path.join(paths.pac_dir(), f"{pl}_e.pac"), "rb").read())[6][1]
        a, n = bloc_effets(b6)
        emod, eram = convert(b6[a:a + 32*n])
        open(os.path.join(d, "palettes_effets_module.bin"), "wb").write(struct.pack(f"<{len(emod)}H", *emod))
        open(os.path.join(d, "palettes_effets_cps2.bin"), "wb").write(struct.pack(f"<{len(eram)}H", *eram))
        print(pl, len(mod) // 16, "palettes ;", n, "palettes d'effets ([6] + %#x)" % a)
