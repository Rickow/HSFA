"""Frames de sprites de l'Anthology (module ro3 + fichier 289 de X_DATA).
Format CORRIGÉ d'après la routine d'affichage traduite (note HSFA `hsfa/work/notes/frames-anthology-emetteur.md`) :
les frames sont rangées au MOT près (adresse paire) et commencent par un u16 TYPE.
Type 2 (format courant) : u16 type=2, u16 T (= Σ largeur×hauteur, budget de la liste d'objets), u16 n−1,
  bourrage jusqu'au multiple de 4, u32 pointeur → fichier 289 (0xA04000) : n × (s16 dx, s16 dy),
  puis n × (u16 code, u16 attributs CPS2). Code LOCAL à la banque du perso (types 00/02/04/06).
Types 0x12/0x18/0x1A/0x1C/0x1E = frame vide d'un seul mot. Autres types : voir la note HSFA.
⚠️ Une première lecture (u32 alignés) voyait des « moitiés échangées » : artefact de désalignement."""
import struct, collections
P = open(__import__("os").path.join(__import__("os").environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro3_usa_prog68k.bin"), "rb").read()
F = open(__import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "cps2", "anims", "f289.bin"), "rb").read()
BASE, FBASE = 0x1F0000, 0xA04000
def records():
    """{décalage fichier: [(dx, dy, code, attr)]} pour toutes les frames de type 2 visées par un pointeur."""
    W = struct.unpack_from(f"<{len(P)//4}I", P)
    out = {}
    for w in W:
        o = w - BASE
        if not (0 <= o < len(P) - 8) or o % 2 or o in out: continue
        t, T, n1 = struct.unpack_from("<3H", P, o)
        if t != 2 or n1 >= 64: continue
        p = (o + 6 + 3) & ~3
        ptr = struct.unpack_from("<I", P, p)[0]
        if not (FBASE <= ptr < FBASE + len(F)): continue
        objs = struct.unpack_from(f"<{2*(n1+1)}H", P, p + 4)
        pos = [struct.unpack_from("<hh", F, ptr - FBASE + 4*i) for i in range(n1 + 1)]
        out[o] = [(dx, dy, c, a) for (dx, dy), c, a in zip(pos, objs[0::2], objs[1::2])]
    return out
def expand(objs):
    """objets -> {(x, y, code local)} tuile par tuile (arithmétique CPS2 : code + i + 16 j)."""
    s = set()
    for dx, dy, code, attr in objs:
        w, h = ((attr >> 8) & 15) + 1, ((attr >> 12) & 15) + 1
        for j in range(h):
            for i in range(w):
                ii = (w - 1 - i) if attr & 0x20 else i
                jj = (h - 1 - j) if attr & 0x40 else j
                s.add((dx + 16*i, dy + 16*j, code + ii + 16*jj))
    return s
