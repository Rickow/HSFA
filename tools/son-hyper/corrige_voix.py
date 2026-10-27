#!/usr/bin/env python3
"""Voix « par pas » des versions ZERO / ZERO 2 / ALPHA d'Hyper : applique voix_arcade.tsv (voix mesurees sur
l'arcade, marque_voix.py + fusionne_voix_arcade.py) aux tables $E6 du bloc de la redirection, dans un zip deja construit.

Les tables redirigees (gen_redirection.py) sont dans hsfa_ext.bin (bloc d'execution $E70000) : une entree de 8 octets
[code, code_alt, 0, 0] en mots LE. Pour chaque version, la table d'origine (codes SFA3) est retrouvee dans le programme
(meme contenu hors codes rediriges) ; chaque mot dont le code SFA3 d'origine a une ligne « a_corriger » ou
« voix_SFA3 » dans voix_arcade.tsv recoit le code de rejeu de la voix d'arcade ($2000 + c SFA1, $3000 + c SFA2).
Les versions dont la table est celle du module (non redirigee, partagee avec la version ZERO 3) ne peuvent pas etre
corrigees ainsi : elles sont listees (correction par gen_redirection.py et retraduction).

  corrige_voix.py <sfa3hhsfa.zip> <sortie.zip> [voix_arcade.tsv]
Idempotent. Aucune autre donnee du zip ne change.
"""
import collections, csv, os, re, struct, sys, zipfile

ICI = os.path.dirname(os.path.abspath(__file__))
PROG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
CB = {"sfa1": 0x2000, "sfa2": 0x3000}
NMAX = 80


def corrections(tsv):
    c = {}
    for r in csv.DictReader(open(tsv), delimiter="\t"):
        if r["statut"] in ("a_corriger", "voix_SFA3"):
            c[(r["jeu"], int(r["base"], 16), int(r["code_SFA3"], 16))] = int(r["arcade"], 16)
    return c


def lit(buf, o, n=NMAX): return [struct.unpack_from("<2H", buf, o + 8 * k) for k in range(n)]


def n_voix(t):
    n = 0
    for k, (a, b) in enumerate(t):
        if a and not (0x200 <= a < 0x600 or 0x2000 <= a < 0x4000) and k > 4: break
        n = k + 1
    return n


def applique(ext, prog, corr, journal):
    """ext, prog : bytearray (modifie ext en place) -> liste des versions non corrigeables"""
    i = ext.find(struct.pack("<3H", 0x4180, 0x4188, 0x4190))         # T_CRIS_V[$30..$32] : debut du bloc $E70000
    if i < 0: raise SystemExit("hsfa_ext.bin : bloc de la redirection introuvable (Hyper sans voix par version ?)")
    ext_e7 = i - 2 * 0x30
    j = prog.find(struct.pack("<2I", 0xE70000 + 0x200, 0xE70000 + 0x480))   # pointeurs 0x6AE614 : versions $30, $31
    if j < 0: raise SystemExit("programme : table des pointeurs de voix introuvable")
    ptr = j - 4 * 0x30
    pat = struct.pack("<8H", 0x220, 0x220, 0, 0, 0x221, 0x221, 0, 0)
    origines = [m.start() - 8 for m in re.finditer(re.escape(pat), prog)]
    faites, non = set(), []
    for v in range(0x30, 0x80):
        P = struct.unpack_from("<I", prog, ptr + 4 * v)[0]
        jeu = "sfa1" if v < 0x40 else "sfa2"
        if not 0xE70000 <= P < 0xE80000:
            non.append(v); continue
        if P in faites: continue
        off = ext_e7 + (P - 0xE70000)
        t = lit(ext, off); n = n_voix(t)
        org = None
        for o in origines:
            to = lit(prog, o, n)
            communs = [k for k in range(n) if not any(0x2000 <= x < 0x4000 for x in t[k])]
            if len(communs) >= 3 and all(t[k] == to[k] for k in communs):
                org = to; break
        if org is None:
            journal.append("version $%02X : table d'origine introuvable, non corrigee" % v); continue
        voix = [x for e in org for x in e if 0x300 <= x < 0x540]
        base = collections.Counter((x - 0x300) // 0x20 for x in voix).most_common(1)[0][0]
        faites.add(P)
        for k in range(n):
            for m in (0, 1):
                a = corr.get((jeu, base, org[k][m]))
                if a is None: continue
                nouveau = CB[jeu] + a
                ancien = struct.unpack_from("<H", ext, off + 8 * k + 2 * m)[0]
                if ancien != nouveau:
                    struct.pack_into("<H", ext, off + 8 * k + 2 * m, nouveau)
                    journal.append("version $%02X (table $%06X) entree %d mot %d : SFA3 %04X : %04X -> %04X" %
                                   (v, P, k, m, org[k][m], ancien, nouveau))
    return non


def main():
    src, dst = sys.argv[1], sys.argv[2]
    corr = corrections(sys.argv[3] if len(sys.argv) > 3 else os.path.join(ICI, "voix_arcade.tsv"))
    z = zipfile.ZipFile(src)
    ext = bytearray(z.read("hsfa_ext.bin"))
    prog = bytearray(b"".join(z.read(n) for n in PROG))
    j = []
    non = applique(ext, prog, corr, j)
    with zipfile.ZipFile(dst, "w") as zo:
        for info in z.infolist():
            d = bytes(ext) if info.filename == "hsfa_ext.bin" else z.read(info)
            zo.writestr(info, d, compress_type=info.compress_type)
    for x in j: print(x)
    a_faire = sorted({v for v in non for (jeu, b, c) in corr if (jeu == ("sfa1" if v < 0x40 else "sfa2"))})
    print("%d mot(s) change(s) ; versions a table du module (retraduction necessaire si elles ont des corrections) : %s"
          % (len([x for x in j if "->" in x]), " ".join("$%02X" % v for v in non)), file=sys.stderr)


if __name__ == "__main__":
    main()
