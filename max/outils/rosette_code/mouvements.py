"""Définitions de mouvements (reconnaissance des manipulations) PSP <-> arcade (2026-10-07).
Arcade : entrée k = $2D5E2 + 8k (LEA déf(pc),A3 ; BRA tronc commun $2D7E6/…), déf. = mots BE : directions, dernière
direction | $10, puis boutons ($0F00 poings, $F000 pieds). PSP : table 0x2178C8[id] -> mots LE : directions, dernière
| $400, puis boutons ($4070 poings, $8380 pieds). Données arcade lues dans sfa3ud_prog.bin (sfa3_prog.bin a des zones de
données faussées par le déchiffrement des opcodes). Sortie : mouvements.json {id PSP: {"k": k arcade, "entree": adr}}"""
import struct, json
from arc68k import B as BC
D = open(__import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "cps2", "sfa3ud_prog.bin"), "rb").read()
from traduire import img
def arcade():
    arc = {}
    for k in range(0x40):
        a = 0x2d5e2 + 8 * k
        if BC[a:a + 2] != b"\x47\xfa": break
        arc[k] = (a, a + 2 + struct.unpack_from(">h", BC, a + 2)[0])
    out = {}
    for k, (e, d) in arc.items():
        w = []
        for j in range(16):
            x = struct.unpack_from(">H", D, d + 2 * j)[0]; w.append(x)
            if x & 0xFF00 and not x & 0xFF: break                     # mot de boutons : fin
        out[k] = (e, tuple(w))
    return out
def psp():
    u32 = lambda a: struct.unpack_from("<I", img, a)[0]
    out = {}
    for i in range(48):
        p = u32(0x2178C8 + 4 * i)
        if not 0 < p < len(img): break
        w = []
        for j in range(16):
            x = struct.unpack_from("<H", img, p + 2 * j)[0]; w.append(x)
            if x & 0xC000 and not x & 0x1000: break                   # bouton final (0x1000 = on continue)
        out[i] = tuple(w)
    return out
# variante PSP 0x64220 (pressions, tenue 0x2000) = routine arcade $2D900 (bit 7 = tenue) ; déf. PSP sans mot de
# boutons (0x2004, 0x2408 puis données voisines) : appariée à la main (k=31 : $84, $98)
COURTES = {32: 31}
def vers_arcade(w):
    """déf. PSP -> forme arcade attendue"""
    r = []
    for x in w:
        if x & 0xC000:
            b = 0
            if x & 0x0070: b |= 0x0F00
            if x & 0x0380: b |= 0xF000
            if x & 0x1000: b |= 0x40                                  # suite de séquence ($FF40 arcade)
            r.append(b)
        else:                                                         # 0x400 = dernière direction ($10), 0x2000 =
            r.append((0x10 if x & 0x400 else 0) | (0x80 if x & 0x2000 else 0) | (x & 0xFF))   # tenue ($80)
    return tuple(r)
if __name__ == "__main__":
    A, P = arcade(), psp()
    par_forme = {}
    for k, (e, w) in A.items(): par_forme.setdefault(w, []).append(k)
    res, manque = {}, []
    for i, w in P.items():
        ks = par_forme.get(vers_arcade(w))
        if not ks and i in COURTES: ks = [COURTES[i]]
        if ks: res[i] = {"k": ks[0], "entree": "%x" % A[ks[0]][0], "psp": [hex(x) for x in w]}
        else: manque.append((i, [hex(x) for x in w], [hex(x) for x in vers_arcade(w)]))
    json.dump(res, open("mouvements.json", "w"), indent=1)
    print("appariés %d / %d ; arcade : %d mouvements" % (len(res), len(P), len(A)))
    print({i: (v["k"], v["entree"]) for i, v in res.items()})
    for m in manque: print("sans équivalent :", m)
    print("TAB_MANIPS:      ; n° de manip PSP (table 0x2178C8) -> entrée arcade $2D5E2 + 8k (0 = sans équivalent)")
    for i in range(0, len(P), 4):
        print("        dc.l    " + ", ".join("$%s" % res[j]["entree"] if j in res else "0" for j in range(i, min(i + 4, len(P)))))
