#!<workspace>/venv/bin/python
"""Numeros de commande VRAIMENT libres pour les voix MAX (renumerotation du 2026-10-10, conflit Cammy ALPHA / Maki).
Une paire (c, c + $500), c < $700, est libre si, pour c ET c + $500 :
  1. Z80 hybride : entree vide ;
  2. table native PS2 d'Hyper (0x1200 entrees, identique ro3/ro5/ro9) : rien, ou une entree SANS VRAI CONTENU :
     type >= 5 (banque de perso PERSO[type-5] -> fichier T_5af2b0[perso]) dont le programme o4 n'existe pas dans la
     banque SCEI (chunk « Prog » du HD, X_DATA e314-e344) ; type 3/4 idem avec e345/e346 ; ADX = toujours du contenu ;
  3. aucun code 68K de SFA3 / Upper / Hyper ne peut l'envoyer :
     - tables « sons par pas » ($E6) : balayage de TOUS les programmes (arcade sfa3ud BE ; modules ro3/ro5/ro9 LE ;
       entrees [code, code_alt, 0, 0], codes $200-$6FF, >= 4 entrees) + tables_hyper.json (0x6AE614, 128 versions) ;
     - cris et K.O. : base + 0..6 pour chaque base de la table 0x3D9A90 d'Hyper (40 mots) et pour tout debut de bloc
       de perso $300 + $20 k (regle prudente : meme mecanisme dans SFA3/Upper) ;
     - commandes envoyees par le 68K EN JEU dans les journaux des agents (ro5, hybride, hyper_son, flux, son_hyper_rom) ;
     - chaque code envoyable l'est aussi + $500 (cote 2) ;
  4. pas une nouvelle commande du prototype roms_hyper (agent_son_hyper_rom/redirection.txt) ;
Ecrit numeros_libres.json (paires libres + codes interdits par motif) et affiche le bilan."""
import os, sys, json, struct, glob, re, csv
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
from gen_voix_max import lit_base, pilote, BASE
DEC = "<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin"
XD = "<workspace>/work/xdata/X_DATA.BIN"
MANI = "<workspace>/anthology_extract/manifest.csv"
sys.path.insert(0, "<workspace>/work/agent_hyper_son")
from table_son import charger


def tables_pas(d, be):
    """codes des tables « sons par pas » : entrees de 8 o [code, code_alt, 0, 0]"""
    out = set()
    a = np.frombuffer(d, np.uint8)
    for al in (0, 2, 4, 6):
        n = (len(a) - al) // 8
        w = a[al:al + 8 * n].reshape(n, 4, 2).astype(np.uint32)
        w = (w[:, :, 0] << 8) | w[:, :, 1] if be else (w[:, :, 1] << 8) | w[:, :, 0]
        c, x = w[:, 0], w[:, 1]
        ok = (w[:, 2] == 0) & (w[:, 3] == 0) & ((c == 0) | ((c >= 0x200) & (c <= 0x6ff))) & ((x == 0) | ((x >= 0x200) & (x <= 0x6ff)))
        i = 0
        while i < n:
            if not ok[i]: i += 1; continue
            j = i
            while j < n and ok[j]: j += 1
            if j - i >= 4 and int((c[i:j] != 0).sum()) >= 3:
                out.update(int(v) for v in c[i:j] if v); out.update(int(v) for v in x[i:j] if v)
            i = j
    return out


def programmes_scei():
    """fichier e3xx -> ensemble des o4 qui ont un son dans la banque SCEI (HD du conteneur MOMO). Le HD n'a que 1 a 3
    programmes ; le programme 0 a une zone (split) par touche 12 + i -> jeu d'echantillons i. Pour rester prudent,
    o4 « a du contenu » s'il est <= au dernier jeu d'echantillons (Sset) OU si une zone d'un programme couvre la
    touche o4 + 12."""
    m = {}
    for l in open(MANI).read().splitlines()[1:]:
        i, off, n, kind, name = l.split(",", 4); m[int(i)] = (int(off), int(n))
    out = {}
    with open(XD, "rb") as f:
        for e in range(314, 347):
            f.seek(m[e][0]); d = f.read(m[e][1])
            assert d[:4] == b"MOMO"
            o, n = struct.unpack_from("<II", d, 8)
            h = d[o:o + n]
            ps = h.find(b"IECStesS")
            ok = set(range(struct.unpack_from("<I", h, ps + 12)[0] + 1))
            p = h.find(b"IECSgorP")
            mx = struct.unpack_from("<I", h, p + 12)[0]
            for o2 in struct.unpack_from("<%dI" % (mx + 1), h, p + 16):
                if o2 == 0xFFFFFFFF: continue
                b = p + o2; nz = h[b + 4]
                for k in range(nz):
                    z = h[b + 0x24 + 20 * k:b + 0x24 + 20 * k + 20]
                    if len(z) < 20: break
                    ok.update(t - 12 for t in range(z[2], z[3] + 1) if t >= 12)
            out[e] = ok
    return out


def main():
    z, q = lit_base(BASE); p = pilote(z)
    d9, _, _, _, ents, pt = charger("ro9")
    T = [struct.unpack_from("<H", d9, 0x5AF2B0 - 0x1F0000 + 2 * i)[0] for i in range(128)]
    prog = programmes_scei()

    def ps2_contenu(c):
        e = ents[c]; t = e[0] & 0x7f
        if t == 0: return None
        if t in (1, 2): return "ADX"
        if t in (3, 4): f = 345 + (t - 3)
        else: f = T[pt[t - 5]]
        return ("e%d son %d" % (f, e[4])) if e[4] in prog.get(f, set()) else None

    motif = {}
    def interdit(c, m):
        for x in (c, c + 0x500, c - 0x500):
            if 0 <= x < 0xC00: motif.setdefault(x, set()).add(m)
    # 3a. tables « sons par pas »
    a = bytearray(open("<workspace>/work/mame/roms/sfa3ud/sz3ud.03c", "rb").read() + open("<workspace>/work/mame/roms/sfa3ud/sz3ud.04c", "rb").read())
    s = bytearray(len(a)); s[0::2] = a[1::2]; s[1::2] = a[0::2]
    for c in tables_pas(bytes(s), True): interdit(c, "table arcade SFA3")
    for mod in ("ro3", "ro5", "ro9"):
        for c in tables_pas(open(DEC % mod, "rb").read(), False): interdit(c, "table %s" % mod)
    th = json.load(open("<workspace>/work/agent_son_hyper_rom/catalogue/tables_hyper.json"))
    for v in th.values():
        for c in v["codes"]:
            if int(c, 16): interdit(int(c, 16), "tables_hyper 0x6AE614")
    # 3b. cris / K.O.
    bases = {struct.unpack_from("<H", d9, 0x3D9A90 + 2 * i)[0] for i in range(40)} | set(range(0x300, 0x700, 0x20))
    for b in bases:
        if b:
            for n in range(7): interdit(b + n, "cris base %04X" % b)
    # 3c. journaux de tous les agents
    vus = set()
    W = "<workspace>/work/"
    jeux = [f for f in glob.glob(W + "agent_son_ro5/journaux/*.txt") if not re.search(r"/(tab_|inj_|regs)", f)] + \
        glob.glob(W + "agent_son_ro5/hybride/journaux/[BC]_*.txt") + glob.glob(W + "agent_hyper_son/essais/*.son") + \
        glob.glob(W + "agent_flux/essais/*.son") + glob.glob(W + "agent_son_hyper_rom/essais/*.son")
    for f in jeux:       # journaux du 68K EN JEU (pas les balayages par injection, qui contiennent tous les codes)
        t = open(f, errors="replace").read()
        for mm in re.finditer(r"(?:^C \S+ |cmd )([0-9a-fA-F]{4})\b", t, re.M): vus.add(int(mm.group(1), 16))
    for c in vus:
        if c < 0xC00: interdit(c, "journal")
    # 4. prototype roms_hyper
    for l in open("<workspace>/work/agent_son_hyper_rom/redirection.txt"):
        t = l.split()
        if len(t) >= 3 and not l.startswith("#"): interdit(int(t[2], 16), "roms_hyper")
    libres, raisons = [], {}
    for c in range(0x700):
        r = []
        for x in (c, c + 0x500):
            if p.cmd(x)[0]: r.append("%04X Z80" % x)
            k = ps2_contenu(x)
            if k: r.append("%04X PS2 %s" % (x, k))
            if x in motif: r.append("%04X %s" % (x, "/".join(sorted(motif[x]))))
        if r: raisons[c] = r
        else: libres.append(c)
    json.dump({"libres": ["%04X" % c for c in libres], "raisons": {"%04X" % c: r for c, r in raisons.items()}},
              open(os.path.join(ICI, "numeros_libres.json"), "w"), indent=0)
    return libres, raisons


if __name__ == "__main__":
    libres, raisons = main()
    print(len(libres), "paires libres")
    runs, s = [], None
    for c in libres + [None]:
        if s is not None and (c is None or c != e + 1): runs.append((s, e)); s = None
        if c is not None:
            if s is None: s = c
            e = c
    print(" ".join("%04X-%04X(%d)" % (a, b, b - a + 1) for a, b in runs))
    a = json.load(open(os.path.join(ICI, "roms_voix/attribution.json")))
    bad = [(v["perso"], v["cmd"], raisons[int(v["cmd"], 16)]) for v in a if int(v["cmd"], 16) in raisons]
    print("voix actuelles en conflit :", len(bad))
    for x in bad: print("  ", x)
