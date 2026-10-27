"""Textes du PROLOGUE de l'Arcade (bio du perso, pages de 2 lignes) au format d'Upper, 2026-10-17.
Upper (ro5, module) : routine MIPS 0x44D0D0 (page suivante, compteur $145 de l'écran, ID en $146 = $102 du joueur) :
  - liste des pages du perso : table 0x960090 (40 mots s16 relatifs à la table, un par ID) -> octets = n° de page
    1-based, le DERNIER marqué du bit 7 (Ryu : 01 02 83) ; liste finie -> fin du prologue (0x44D680) ;
  - texte : réserve 0x61C0C0[$92] (Upper : 0x681FD2) = mots u16 relatifs à la réserve (116 pages) puis les pages ;
    page = [position] ligne 1 \\0 [position] ligne 2 \\0 (mêmes octets que la PSP sans l'octet « total » ni le remplissage).
  - n° de page sur 7 bits (andi #$7F, -1) : 127 pages au plus ; les 116 d'Upper sont toutes employées (11 places libres).
PSP : opXX_e.pac entrée 3 (0x10000), enregistrements de 0x80 o = [total] puis les mêmes lignes.
Contrôle : les pages d'Upper des persos d'arcade = les bios PSP converties (valider()).
⚠ Intégration (HSFA, 2026-10-17) : les pages doivent être rangées dans l'ORDRE D'OCTETS PS2 (octets échangés par paire,
lecture octet du module en adresse XOR 1), sinon le texte sort brouillé ; prologue_max.s les donne dans l'ordre logique.
Sortie : ~/.cache/sfa3max/converti/prologue_max.s (réserve PROLOGUE_MAX + listes PROLOGUE_MAX_xx) + prologue_max.json.
Usage : python prologue_max.py [valider]"""
import os, sys, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textes_max as TX
UPPER = os.path.join(os.environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed/ro5_usa_prog68k.bin")
X = 0x1F0000
RESERVE, LISTES = 0x681FD2, 0x960090
MAX = {0x26: "eagle", 0x27: "maki", 0x28: "yun", 0x29: "ingrid"}
ID_UPPER = {0x26: 0x26, 0x27: 0x27, 0x28: 0x2D, 0x29: 0x2E}      # ID d'Upper (intégration HSFA)


def pages_psp(cid):
    """bio PSP -> pages au format Upper (octets)"""
    d = TX.entree("op%02x_e.pac" % cid, 0x10000); out = []
    for r in range(0, len(d) - 0x7F, 0x80):
        rec = d[r:r + 0x80]
        if not rec[0]: continue
        i, p = 1, b""
        while i < len(rec) and rec[i]:
            j = rec.index(0, i + 1); p += rec[i:j + 1]; i = j + 1
        out.append(p)
    return out


def upper():
    U = open(UPPER, "rb").read()
    b = RESERVE - X; n = struct.unpack_from("<H", U, b)[0] // 2
    offs = struct.unpack_from("<%dH" % n, U, b)
    def page(k):
        a = b + offs[k]; e = a
        for _ in range(2): e = U.index(0, e + 1) + 1
        return U[a:e]
    lb = LISTES - X; lo = struct.unpack_from("<40h", U, lb)
    listes = []
    for o in lo:
        L, k = [], 0
        while True:
            v = U[lb + o + k]; L.append(v & 0x7F); k += 1
            if v & 0x80 or not v: break
        listes.append(L)
    return [page(k) for k in range(n)], listes


def valider():
    P, L = upper(); ok = tot = 0
    for cid in range(0x26):
        try: q = pages_psp(cid)
        except Exception: continue
        u = [P[n - 1] for n in L[cid]] if cid < len(L) else []
        tot += 1; ok += q == u
        if q != u: print("ID %02X : PSP %d pages / Upper %d" % (cid, len(q), len(u)), [x[:30] for x in q][:2], [x[:30] for x in u][:2])
    print("persos dont les pages PSP converties = pages d'Upper : %d / %d" % (ok, tot))


def ecrire():
    L = ["; Textes du prologue de l'Arcade des persos MAX (format d'Upper : réserve 0x681FD2, listes 0x960090) — prologue_max.py",
         "; Réserve PROPRE aux MAX (les 116 pages d'Upper occupent déjà les n° 1-116 et le n° est sur 7 bits : 11 places",
         "; libres pour 14 pages) : PROLOGUE_MAX = mots relatifs à la réserve, puis les pages ; listes : n° 1-based dans",
         "; PROLOGUE_MAX, dernier | $80.", "PROLOGUE_MAX:"]
    pages, listes, info = [], {}, {}
    for cid, nom in MAX.items():
        q = pages_psp(cid); listes[cid] = list(range(len(pages) + 1, len(pages) + len(q) + 1)); pages += q
        info[nom] = {"id_upper": "$%02X" % ID_UPPER[cid], "pages": [p.decode("ascii", "replace").replace("\0", " | ") for p in q]}
    L += ["        dc.w    PM_%d-PROLOGUE_MAX" % k for k in range(len(pages))]
    for k, p in enumerate(pages):
        L.append("PM_%d:   ; %s" % (k, p.decode("ascii", "replace").replace("\0", " / ")[:70]))
        L.append("        dc.b    " + ", ".join("$%02x" % x for x in p))
    L.append("        even")
    for cid, nom in MAX.items():
        n = listes[cid]
        L.append("PROLOGUE_MAX_%02X:      ; %s (ID Upper $%02X)" % (cid, nom, ID_UPPER[cid]))
        L.append("        dc.b    " + ", ".join("$%02x" % (v | (0x80 if i == len(n) - 1 else 0)) for i, v in enumerate(n)))
    L.append("        even")
    d = os.path.expanduser("~/.cache/sfa3max/converti")
    open(os.path.join(d, "prologue_max.s"), "w").write("\n".join(L) + "\n")
    json.dump(info, open(os.path.join(d, "prologue_max.json"), "w"), indent=1, ensure_ascii=False)
    return len(pages), sum(map(len, pages))


if __name__ == "__main__":
    if sys.argv[1:] == ["valider"]: valider()
    else: print("pages, octets :", ecrire())
