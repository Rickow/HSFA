#!/usr/bin/env python3
"""Voix « par pas » d'Hyper rattachees a l'arcade, entree par entree (methode des marqueurs).

Pour une version d'Hyper (ZERO / ZERO 2 / ALPHA) :
  1. sa table de voix ($E6 du joueur, lue en RAM en plein combat ; mot haut / mot bas inverses) est localisee : bloc de
     la redirection (exec $E70000+ = hsfa_ext.bin + EXT_E7) ou table d'origine du module (programme 68K, exec - PROG) ;
  2. la table d'origine (codes SFA3) est retrouvee dans le programme (meme contenu hors codes redirigees) ;
  3. dans une copie du zip, chaque entree de voix recoit un code marqueur ($2E00 + k mot 0, $2F00 + k mot 1) ;
  4. la suite de gestes de compare_voix_arcade.py est rejouee ; chaque voix entendue designe son entree, donc son code
     SFA3 d'origine ; elle est appariee, dans l'ordre, aux voix de l'arcade pour le meme geste (dossier de
     compare_voix_arcade.py).
Sortie : une ligne par (code SFA3, voix d'arcade) avec le nombre d'occurrences et les gestes.

  marque_voix.py <joue_linux> <coeur_diag.so> <sfa3hhsfa.zip> <system> <dossier compare_voix_arcade> <nom> <spec>
                 <sortie>         (ex. ... lot Ken_Z 01.Z marques)
"""
import collections, os, re, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_voix_arcade as C

EXT_E7 = 0x28E200                 # hsfa_ext.bin : decalage de l'adresse d'execution $E70000 (bloc de la redirection)
PROG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
NMAX = 80


def depart(err):
    cs = C.commandes(err)
    mus = [cs[i + 1][0] for i in range(len(cs) - 1) if cs[i][0] > 1100 and cs[i][1] == 0xFF07
           and (0x01 <= cs[i + 1][1] < 0x60 or 0x180 <= cs[i + 1][1] < 0x300)]
    return (mus[0] + 25) if mus else 1340


def entrees_voix(t):
    """indices des entrees de la table (stop a la premiere entree hors voix / bruitage)"""
    n = 0
    for k, (a, b) in enumerate(t):
        if a and not (0x200 <= a < 0x600 or 0x2000 <= a < 0x4000) and k > 4: break
        n = k + 1
    return n


def main():
    joue, coeur, zh, sysd, dcmp, nom, spec, sortie = sys.argv[1:9]
    sup = "--super" in sys.argv[9:]                            # super-coups (prelude de coups speciaux : jauge)
    LISTE = C.SUPERS if sup else C.GESTES
    out = os.path.join(sortie, nom); os.makedirs(out, exist_ok=True)
    env = dict(HSFA_QSLOG="1", HSFA_TOURNEE="%s/00.Z3.iA" % spec, HSFA_TOURNEE_PASSIF="1", HSFA_TOURNEE_PV="1",
               HSFA_TOURNEE_LOG="t.log")
    C.lance([joue, coeur, zh, sysd, "1700", os.devnull], env, out)
    deb = depart(os.path.join(out, "err.log"))
    open(os.path.join(out, "e.txt"), "w").write("".join("%d %d %d %d\n" % e for e in (C.prelude(deb) if sup else [])))
    if sup: deb += C.PRELUDE
    env["HSFA_ENTREES"] = "e.txt"
    C.lance([joue, coeur, zh, sysd, str(deb + 2), os.devnull, str(deb)], dict(env, HSFA_RAM_DUMP="1"), out)
    ram = open(os.path.join(out, "ram_%06d.bin" % deb), "rb").read()
    w = lambda a: ram[a] | ram[a + 1] << 8
    P = w(0x8400 + 0xE8) << 16 | w(0x8400 + 0xE6)               # mots inverses
    v = ram[(0x8400 + 0x103) ^ 1]
    z = zipfile.ZipFile(zh)
    ext = bytearray(z.read("hsfa_ext.bin"))
    prog = bytearray(b"".join(z.read(n) for n in PROG))
    lit = lambda buf, o: [struct.unpack_from("<2H", buf, o + 8 * k) for k in range(NMAX)]
    if 0xE70000 <= P < 0xE80000:
        cible, off = ext, EXT_E7 + (P - 0xE70000)
    else:
        cible, off = None, None
    # table d'origine dans le programme : meme contenu que la table en jeu, hors codes rediriges
    pat = struct.pack("<8H", 0x220, 0x220, 0, 0, 0x221, 0x221, 0, 0)
    t_jeu = lit(ext, off) if cible is ext else None
    orig_off = None
    for m in re.finditer(re.escape(pat), prog):
        o = m.start() - 8
        t = lit(prog, o)
        if t_jeu is None:
            continue
        n = entrees_voix(t_jeu)
        if all(t_jeu[k] == t[k] for k in range(n) if not any(0x2000 <= x < 0x4000 for x in t_jeu[k])):
            orig_off = o; break
    if cible is None:                                           # version non redirigee : table du module = l'origine
        # adresse d'execution -> programme : par le decalage d'une table connue (sonde : premier motif qui suit P)
        cands = [m.start() - 8 for m in re.finditer(re.escape(pat), prog)]
        orig_off = min(cands, key=lambda o: abs((o + 0x51B140) - P)) if cands else None
        if orig_off is None or (orig_off + 0x51B140) != P:
            print("%s : table $%06X introuvable dans le programme" % (nom, P)); return
        cible, off = prog, orig_off
        t_jeu = lit(prog, off)
    t_org = lit(prog, orig_off)
    n = entrees_voix(t_jeu)
    # marqueurs
    for k in range(n):
        for m_ in (0, 1):
            x = t_org[k][m_]
            if 0x300 <= x < 0x540: struct.pack_into("<H", cible, off + 8 * k + 2 * m_, (0x2E00 if m_ == 0 else 0x2F00) + k)
    zt = os.path.join(out, "sfa3hhsfa.zip")
    with zipfile.ZipFile(zt, "w") as zo:
        for info in z.infolist():
            if info.filename == "hsfa_ext.bin": d = bytes(ext)
            elif info.filename in PROG:
                i = PROG.index(info.filename); d = bytes(prog[i * 0x80000:(i + 1) * 0x80000])
            else: d = z.read(info)
            zo.writestr(info, d, compress_type=info.compress_type)
    open(os.path.join(out, "g.txt"), "w").write("".join("%d %d %d %d %d\n" % e for e in C.gestes(LISTE)))
    C.lance([joue, coeur, zt, sysd, str(deb + 1), os.devnull],
            dict(env, HSFA_GESTES="g.txt", HSFA_GESTES_DEBUT=str(deb), HSFA_GESTES_DUREE=str(C.DUREE)), out)
    os.remove(zt)
    pg = C.par_geste(os.path.join(out, "err.log"))
    jeu = "sfa1" if 0x30 <= v < 0x40 else "sfa2"
    pa = C.par_geste(os.path.join(dcmp, nom, "arcade", "err.log"))
    votes = collections.defaultdict(collections.Counter)
    gestes = collections.defaultdict(set)
    seul_h, seul_a = [], []
    for g, (gn, _) in enumerate(LISTE):
        mk = [c for c in pg.get(g, []) if 0x2E00 <= c < 0x3000]
        va = [c for c in pa.get(g, []) if C.voix_arcade(c, jeu)]
        if sup and len(mk) != len(va):                         # super sorti differemment (jauge, distance) :
            seul_h += ["%04X@%s" % (t_org[h & 0xFF][0 if h < 0x2F00 else 1], gn) for h in mk]   # pas d'appariement
            seul_a += ["%04X@%s" % (a, gn) for a in va]
            continue
        for i in range(max(len(mk), len(va))):
            h = mk[i] if i < len(mk) else None
            a = va[i] if i < len(va) else None
            c3 = None if h is None else t_org[h & 0xFF][0 if h < 0x2F00 else 1]
            if c3 is not None and a is not None:
                votes[c3][a] += 1; gestes[c3].add(gn)
            elif c3 is not None: seul_h.append("%04X@%s" % (c3, gn))
            elif a is not None: seul_a.append("%04X@%s" % (a, gn))
    with open(os.path.join(sortie, nom + (".super" if sup else "") + ".tsv"), "w") as f:
        f.write("# %s : version $%02X, table $%06X (%s), %d entrees, origine prog+%X\n" %
                (nom, v, P, "redirection" if cible is ext else "module", n, orig_off))
        f.write("jeu\tversion\tcode_SFA3\tarcade\toccurrences\tautres\tgestes\n")
        for c3, cnt in sorted(votes.items()):
            (a, k), autres = cnt.most_common(1)[0], ["%04X:%d" % x for x in cnt.most_common()[1:]]
            f.write("%s\t%02X\t%04X\t%04X\t%d\t%s\t%s\n" % (jeu, v, c3, a, k, " ".join(autres), " ; ".join(sorted(gestes[c3]))))
        f.write("# voix Hyper sans voix d'arcade : %s\n" % " ".join(seul_h))
        f.write("# voix d'arcade sans voix Hyper : %s\n" % " ".join(seul_a))
    print("%s : %d codes SFA3 apparies" % (nom, len(votes)))


if __name__ == "__main__":
    main()
