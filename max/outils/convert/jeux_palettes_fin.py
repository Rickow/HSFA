"""Jeux de palettes des fins MAX : sémantique PSP exacte -> images de palettes OBJ toutes faites pour l'arcade (2026-10-18).
PSP (EBOOT) : table maîtresse 0x2B34B0[fin] -> petite table, [1] = liste de pointeurs, un par jeu k (0 = jeu vide).
Jeu k = suite d'enregistrements de 4 octets (drapeaux, destination, source, nombre), bit 7 des drapeaux = dernier ;
copié seulement si (drapeaux & $7F) == 0 (FUN_001DC25C) : palettes OBJ [destination…] <- palettes de fin
(entrée 0x4000019 du pac = palettes_fin_cps2.bin) [source…]. Toutes les destinations sont des palettes OBJ (0-31).
Quatre emplacements (OBJ, S1, S2, S3 : état de fin +$7E…+$84, posés par la scène 1109 args 5-8 et par x5 args 2-5) ;
FUN_001DB62C compare chaque emplacement à son cache (+$18…+$1E) à chaque image et rejoue le jeu s'il a changé, dans
l'ordre OBJ, S1, S2, S3 (la PSP n'a pas de palettes de plans : les 4 jeux écrivent les palettes OBJ). x9 (0904) :
jeu a2 rejoué tel quel (+$96), a3 / a4 ignorés.
Arcade (pour mémoire) : scène 1108 -> a5 chargé en OBJ 0-29 (30 palettes, $26710) ; x5 ($2735C) NE charge rien
(-$5102 = $FF -> $260F8 saute $26710 ; seulement groupe d'acteurs a1 / $1CA) ; x9 ($273EC -> $266BC) : jeu a2,
a4 palettes à partir de l'octet a3 du tampon a1.
Sortie (~/.cache/sfa3max/converti/plXX/fin/) : jeux_palettes_cps2.bin (images de 32 palettes CPS2 à la suite ; une
palette jamais écrite reprend celle de l'image précédente, noire au départ) et jeux_palettes.json (jeux PSP décodés,
événements du script PSP dans l'ordre -> n° d'image).
Usage : python jeux_palettes_fin.py"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from relocs import img as I
import script_fin
T_FINS = 0x2B34B0
CONV = os.path.expanduser("~/.cache/sfa3max/converti")
PL = {0x26: "pl26", 0x27: "pl27", 0x28: "pl28", 0x29: "pl29"}


def jeux_psp(fin):
    a = struct.unpack_from("<I", I, T_FINS + 4 * fin)[0]; t = struct.unpack_from("<I", I, a + 4)[0]
    J, k = [], 0
    while True:
        p = struct.unpack_from("<I", I, t + 4 * k)[0]
        if p and not 0x200000 <= p < 0x2D0000: break
        L = []
        while p:
            f, d, s, n = I[p:p + 4]; L.append((f & 0x7F, d, s, n)); p += 4
            if f & 0x80: break
        J.append(L); k += 1
    return J


def simuler(fin):
    J = jeux_psp(fin); pal = open(os.path.join(CONV, PL[fin], "fin", "palettes_fin_cps2.bin"), "rb").read()
    npal = len(pal) // 32
    obj = [None] * 32; cache = [None] * 4; images, evts = [], []
    def jouer(k):
        for f, d, s, n in J[k]:
            if f: continue
            for i in range(n):
                assert d + i < 32 and s + i < npal, (fin, k, d, s, n)
                obj[d + i] = s + i
    def image():
        cle = list(obj)
        if cle not in images: images.append(cle)
        return images.index(cle)
    for off, att, op, args in script_fin.psp("%02x" % fin):
        cl, sub = (op >> 4) & 7, (op >> 8) & 0xF
        if cl: continue
        if sub == 1 and len(args) >= 8: slots = list(args[4:8]); nom = "scene"
        elif sub == 5 and (op >> 12) != 0xF and len(args) >= 5: slots = list(args[1:5]); nom = "x5"
        elif sub == 9: jouer(args[1]); evts.append({"off": off, "op": "x9", "jeu": args[1], "image": image()}); continue
        else: continue
        joues = []
        for e in range(4):
            if slots[e] != cache[e]: cache[e] = slots[e]; jouer(slots[e]); joues.append(slots[e])
        evts.append({"off": off, "op": nom, "emplacements": slots, "jeux_rejoues": joues, "image": image()})
    # images CPS2 : palette jamais écrite -> celle de l'image précédente (noire au départ)
    out, prec = bytearray(), [bytes(32)] * 32
    for im in images:
        cur = [pal[32 * s:32 * s + 32] if s is not None else prec[d] for d, s in enumerate(im)]
        out += b"".join(cur); prec = cur
    return J, images, evts, bytes(out), npal


if __name__ == "__main__":
    for fin, pl in PL.items():
        J, images, evts, b, npal = simuler(fin)
        d = os.path.join(CONV, pl, "fin")
        open(os.path.join(d, "jeux_palettes_cps2.bin"), "wb").write(b)
        json.dump({"palettes_fin": npal, "jeux_psp": J, "images": images, "evenements": evts},
                  open(os.path.join(d, "jeux_palettes.json"), "w"), indent=1)
        print("fin $%X : %d palettes, %d jeux PSP, %d images" % (fin, npal, len(J), len(images)))
        for k, L in enumerate(J): print("   jeu %d : %s" % (k, " ".join("%d<-%d×%d%s" % (d_, s, n, "" if not f else "(ignoré %d)" % f) for f, d_, s, n in L) or "vide"))
        for e in evts: print("   %06x %-5s %s -> image %d" % (e["off"], e["op"], e.get("emplacements", e.get("jeu")), e["image"]))
