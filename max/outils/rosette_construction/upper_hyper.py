"""Comparaison des données de combat Upper (ro5) ↔ Hyper (ro9), tous les persos SFA3 (2026-10-11).
Blocs : Upper T_749838 (PS2 0x749838, 40 places) ; Hyper 0x6A7A94 (128 places). Pour chaque perso : nombre de lignes de
16 o du bloc ($2B0/$2B8/$2B4/$2BC par ligne), taille des 4 tables de la 1re ligne, animations identiques au même n°
(durées, drapeaux, frames comparées par leurs octets : type, T, n, objets ; le pointeur de positions est exclu car
Upper range les positions dans le fichier 390 et Hyper dans le 547). Sortie : tableau imprimé + upper_hyper.json."""
import struct, json, os, hashlib, collections
X = 0x1F0000; D = __import__("os").path.join(__import__("os").environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "")
U5 = open(D + "ro5_usa_prog68k.bin", "rb").read(); H9 = open(D + "ro9_usa_prog68k.bin", "rb").read()
L = lambda b, a: struct.unpack_from("<I", b, a - X)[0]; H = lambda b, a: struct.unpack_from("<H", b, a - X)[0]
NOMS = ("$2B0", "$2B8", "$2B4", "$2BC")


def dans(b, a): return X <= a < X + len(b) - 24


def lignes(b, blk, suivants):
    out = []
    for r in range(16):
        a = blk + 16 * r
        if r and a in suivants: break
        v = [L(b, a + 4 * k) for k in range(4)]
        if not all(dans(b, x) for x in v): break
        out.append(v)
    return out


def tables(b, row):
    out = {}
    for k, t in enumerate(row):
        lim = min([s for s in row if s > t] + [t + 0x1000]); o = []; i = 0
        while t + 2 * i < lim and i < 400:
            w = H(b, t + 2 * i)
            if w == 0 or w % 2 or not dans(b, t + w): break
            o.append(t + w); lim = min(lim, t + w); i += 1
        out[NOMS[k]] = o
    return out


def fh(b, fp):
    if not dans(b, fp): return "?"
    t, T, n1 = struct.unpack_from("<3H", b, fp - X)
    if t != 2 or n1 > 64: return "t%x" % t
    p = (fp + 6 + 3) & ~3
    return hashlib.md5(b[fp - X:fp - X + 6] + b[p + 4 - X:p + 4 - X + 4 * (n1 + 1)]).hexdigest()[:10]


def anim(b, a):
    out = []
    for k in range(80):
        p = a + 20 * k
        if not dans(b, p): break
        d, fl = b[p - X], b[p - X + 1]; out.append((d, fl & 0xC0, fh(b, L(b, p + 4))))
        if fl & 0xC0: break
    return tuple(out)


if __name__ == "__main__":
    BU = [L(U5, 0x749838 + 4 * c) for c in range(40)]; BH = [L(H9, 0x6A7A94 + 4 * c) for c in range(128)]
    res = {}; tot = collections.Counter()
    print("perso | lignes U/H | tables 1re ligne U ($2B0/$2B8/$2B4/$2BC) | H | anims identiques / communes")
    for c in range(0x26):
        if c in (0x12, 0x14, 0x17) and BU[c] == BU[0]: pass
        ru = lignes(U5, BU[c], set(BU) - {BU[c]}); rh = lignes(H9, BH[c], set(BH) - {BH[c]})
        if not ru or not rh: continue
        tu, th = tables(U5, ru[0]), tables(H9, rh[0]); ident = comm = 0
        for nom in NOMS:
            for n in range(min(len(tu[nom]), len(th[nom]))):
                comm += 1; ident += anim(U5, tu[nom][n]) == anim(H9, th[nom][n])
        tot["ident"] += ident; tot["comm"] += comm
        res["%02x" % c] = {"lignes": [len(ru), len(rh)], "tailles_U": [len(tu[k]) for k in NOMS],
                           "tailles_H": [len(th[k]) for k in NOMS], "identiques": ident, "communes": comm,
                           "bloc_U": "%x" % BU[c], "bloc_H": "%x" % BH[c]}
        print("%02x | %d/%d | %s | %s | %d/%d" % (c, len(ru), len(rh), [len(tu[k]) for k in NOMS], [len(th[k]) for k in NOMS], ident, comm))
    print("TOTAL animations identiques %d / %d communes" % (tot["ident"], tot["comm"]))
    json.dump(res, open(os.path.expanduser("~/.cache/sfa3max/rosette/upper_hyper.json"), "w"), indent=1)
