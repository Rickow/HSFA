#!/usr/bin/env python3
"""INJECTION DE DECOR WIDESCREEN dans le programme TRADUIT (fork MAME sfa3hx, coeur FBNeo HSFA) — INJECTION-FORK.md.

Entree : la sortie de reimport.py pour un decor (carte etendue en codes ARCADE + blocs de tuiles neuves de la region
:gfx arcade + palettes neuves), l'image traduite du module (ROM programme), la memoire de decor rangee pour le fork
(hsfa_plans.bin, mode « base » : scroll1 base $300, scroll2 $340, scroll3 $3A0).

1. Tuiles : chaque case nouvelle (n/r) de la carte etendue est rendue en pens depuis la region arcade corrigee, puis
   cherchee (4 retournements) dans la memoire de decor du fork ; sinon tuile neuve, rangee a un code LOCAL libre
   (scroll1 a partir de $6000 : codes jamais utilises par la bibliotheque de super-tuiles (max $5514) ; scroll2 a
   partir de la fin de la vue 16x16 (35 328 = $8A00) ; scroll3 a partir de 4 096). -> hsfa_plans_decor.bin (copie
   corrigee) + blocs (fichier@decalage pour HSFA_GFX).
2. Bloc externe (ext_<base>.bin, mots gros-boutistes, a charger par HSFA_EXT / banc_mem / paquet_fbneo) :
   copies RELOGEES des tables de listes (scroll1/2/3), des bibliotheques de blocs (scroll1 + super-tuiles, scroll2,
   scroll3) et des tables de palettes (32 palettes completes par decor), plus les blocs, super-tuiles, listes propres
   et palettes neuves du decor. Bibliotheques : numeros neufs au-dela de la capacite d'origine (scroll1/2) ou parmi
   les libres de blocs_libres.json (scroll3).
3. Programme : les operandes des « LEA base.L,An » (sites de blocs_tr.MOD) pointent sur les copies relogees.
4. Verification : tilemaps recomposees depuis l'image corrigee + le bloc externe, rendues en (pens, palette) avec la
   region du fork corrigee = carte etendue rendue avec la region arcade corrigee (cases nouvelles : 0 ecart exige).

Plusieurs decors en une passe : --decor-spec DOSSIER:0C[+28] (repetable ; « +28 » = decors lies, memes listes et
palettes, ex. $28 qui reprend les donnees du temple $0C). Adresses des donnees et sites : reperes dans
carte_image.txt par leurs adresses PS2 (blocs_tr.depuis_carte), donc valables apres toute reconstruction.

Usage : ../venv/bin/python injection_fork.py --decor-spec ../reimport/test_0C:0C --sortie sorties/test_0C
        [--module ro3] [--roms trav/roms_tr/sfa3ud] [--carte-image trav/carte_image.txt] [--plans trav/hsfa_plans.bin]
        [--ext-base C80000]
        (forme courte pour un decor : --carte DOSSIER --decor 0C [--decors-lies 28])
"""
import os, sys, json, argparse, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "py"), "<workspace>/work/decors_ws/reimport"]
import numpy as np
import cpsenc as E
import blocs_tr as BT
import image

ORG = 0x3000000
OFF = {1: 0x0000000, 2: 0x0400000, 3: 0x0A00000}          # hsfa_plans.py (relatifs a $3000000)
BASES = {L: (ORG + OFF[L]) >> 16 for L in (1, 2, 3)}
TBF = {1: 64, 2: 128, 3: 512}                              # octets par element dans la region du fork
NCODE = {1: 0x10000, 2: 0xC000, 3: 0x4000}                 # codes locaux adressables (scroll2 : avant la zone 32x32)
NBX = {1: 4, 2: 4, 3: 8}; NT = {1: 32, 2: 16, 3: 8}; WT = {1: 128, 2: 64, 3: 64}; HT = {1: 64, 2: 64, 3: 64}


# ------------------------------------------------------------------ region du fork (vue locale)
class RegionFork:
    def __init__(self, path, debut_neuf):
        self.r = bytearray(open(path, "rb").read())
        need = OFF[3] + 0x4000 * 512
        if len(self.r) < need: self.r.extend(b"\0" * (need - len(self.r)))
        self.suiv = dict(debut_neuf)
        self.neuves = {1: [], 2: [], 3: []}
        self.index = {}

    def tuile(self, L, code):
        o = OFF[L] + code * TBF[L]
        if L == 1:
            return E.dec_rows(self.r[o:o + 64], 8, 16)[:, :8]
        ts = E.TS[L]
        return E.dec_rows(self.r[o:o + TBF[L]], ts, ts)

    def construit_index(self, L, n):
        """pens (retournes) -> (code, fx, fy), plus petit code d'abord"""
        ts = E.TS[L]; tb = TBF[L]
        raw = np.frombuffer(bytes(self.r[OFF[L]:OFF[L] + n * tb]), np.uint8)
        if L == 1:
            a = raw.reshape(n, 8, 2, 4)[:, :, 0, :]                       # moitie gauche (= droite)
            px = np.zeros((n, 8, 8), np.uint8)
            for bit in range(4): px |= (np.unpackbits(a[:, :, bit:bit + 1], axis=2) << bit).astype(np.uint8)
        else:
            a = raw.reshape(n, ts, ts // 8, 4)
            px = np.zeros((n, ts, ts // 8, 8), np.uint8)
            for bit in range(4): px |= (np.unpackbits(a[:, :, :, bit:bit + 1], axis=3) << bit).astype(np.uint8)
            px = px.reshape(n, ts, ts)
        idx = {}
        for fx in (0, 1):
            for fy in (0, 1):
                v = px
                if fx: v = v[:, :, ::-1]
                if fy: v = v[:, ::-1, :]
                v = np.ascontiguousarray(v).reshape(n, -1)
                for c in range(n - 1, -1, -1):
                    idx[v[c].tobytes()] = (c, fx, fy)
        self.index[L] = idx

    def cherche_ou_ajoute(self, L, pens):
        k = np.ascontiguousarray(pens).tobytes()
        if k in self.index[L]:
            return self.index[L][k], False
        c = self.suiv[L]; self.suiv[L] += 1
        assert c < NCODE[L], "plus de codes locaux libres pour le plan %d" % L
        o = OFF[L] + c * TBF[L]
        assert not any(self.r[o:o + TBF[L]]) or L == 1, "code local %X du plan %d non vide" % (c, L)
        raw = E.encode_code(1, (pens, pens)) if L == 1 else E.encode_code(L, pens)
        self.r[o:o + len(raw)] = raw
        self.neuves[L].append(c)
        for fx in (0, 1):
            for fy in (0, 1):
                self.index[L].setdefault(np.ascontiguousarray(E.flip(pens, fx, fy)).tobytes(), (c, fx, fy))
        return (c, 0, 0), True


# ------------------------------------------------------------------ memoire 68000 : image + bloc externe
class Mem:
    def __init__(self, img, base, taille):
        self.img = img; self.base = base; self.ext = bytearray(taille); self.fin = 0

    def __getitem__(self, a):
        if isinstance(a, slice):
            return bytes(self[i] for i in range(a.start, a.stop))
        return self.ext[a - self.base] if a >= self.base else self.img[a]

    def lire(self, a, n):
        return bytes(self.ext[a - self.base:a - self.base + n]) if a >= self.base else bytes(self.img[a:a + n])

    def alloue(self, n, align=4):
        self.fin = (self.fin + align - 1) // align * align
        a = self.base + self.fin; self.fin += n
        assert self.fin <= len(self.ext), "bloc externe trop petit"
        return a

    def ecrit(self, a, data):
        assert a >= self.base
        self.ext[a - self.base:a - self.base + len(data)] = data


def w_(m, a): return struct.unpack(">H", m.lire(a, 2))[0]


def charge_carte(dossier, gfx_arcade):
    ce = json.load(open(os.path.join(dossier, "carte_etendue.json")))
    pn = json.load(open(os.path.join(dossier, "palettes_nouvelles.json")))
    rega = bytearray(open(gfx_arcade, "rb").read())          # region arcade corrigee par les blocs de reimport.py
    for b_ in json.load(open(os.path.join(dossier, "blocs.json"))):
        o = int(b_["decalage_region"][1:], 16); data = open(os.path.join(dossier, b_["fichier"]), "rb").read()
        rega[o:o + len(data)] = data
    return ce, pn, bytes(rega)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--decor-spec", action="append", default=[], help="DOSSIER_REIMPORT:DECOR[+LIE...] (repetable)")
    ap.add_argument("--carte", help="(forme courte) dossier de sortie de reimport.py")
    ap.add_argument("--decor", default="0C")
    ap.add_argument("--decors-lies", default="")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--module", default="ro3")
    ap.add_argument("--roms", default=os.path.join(HERE, "trav/roms_tr/sfa3ud"))
    ap.add_argument("--carte-image", default=None, help="carte_image.txt (defaut : dossier de travail des ROM)")
    ap.add_argument("--plans", default=os.path.join(HERE, "trav/hsfa_plans.bin"))
    ap.add_argument("--gfx-arcade", default="<workspace>/work/decors_ws/gfx/gfx_region.bin")
    ap.add_argument("--ext-base", default="C80000")
    ap.add_argument("--ext-taille", default="80000")
    ap.add_argument("--codes", default="6000,8A00,1000", help="premiers codes locaux neufs scroll1,scroll2,scroll3 (hexa)")
    ap.add_argument("--forcer-palettes", action="store_true", help="accepter une palette neuve deja utilisee hors course")
    ap.add_argument("--libres3", default="<workspace>/work/decors_ws/reimport/blocs_libres.json")
    a = ap.parse_args()
    specs = []
    for sp in a.decor_spec:
        dos, d_ = sp.rsplit(":", 1); ds = [int(x, 16) for x in d_.split("+")]
        specs.append((dos, ds))
    if a.carte:
        specs.append((a.carte, [int(a.decor, 16)] + [int(x, 16) for x in a.decors_lies.split(",") if x]))
    assert specs, "aucun decor (--decor-spec ou --carte)"
    carte_img = a.carte_image or os.path.join(os.path.dirname(os.path.dirname(a.roms.rstrip("/"))), "carte_image.txt")
    M = BT.depuis_carte(carte_img, a.module)
    os.makedirs(a.sortie, exist_ok=True)
    img0 = bytes(image.lit(a.roms)); img = bytearray(img0)
    EXT = int(a.ext_base, 16)
    mem = Mem(img, EXT, int(a.ext_taille, 16))
    cs = [int(x, 16) for x in a.codes.split(",")]
    RF = RegionFork(a.plans, {1: cs[0], 2: cs[1], 3: cs[2]})
    for L in (1, 2, 3):
        RF.construit_index(L, RF.suiv[L])          # seulement les codes en dessous des codes neufs (jamais reecrits)
    nd = M["ndec"]
    tous = [x for _, ds in specs for x in ds]
    assert len(tous) == len(set(tous)), "decor en double dans les specs"
    rapport = dict(module=a.module, ext_base="$%06X" % EXT, carte_image=carte_img,
                   donnees={k: "$%06X" % M[k] for k in ("type1", "list1", "list2", "list3", "b1", "st1", "b2", "b3")},
                   palettes_tables={"scroll%d" % L: "$%06X" % M["pal"][L] for L in (1, 2, 3)}, decors=[])

    # ---------------- 1. cases nouvelles de chaque decor -> codes locaux ----------------
    D_ = []                                                     # par spec : dict de travail
    for dos, ds in specs:
        dec = ds[0]
        ce, pn, rega = charge_carte(dos, a.gfx_arcade)
        T0 = {L: BT.cases_tilemap(img0, M, L, dec) for L in (1, 2, 3)}
        neuf = {}; stats = {}
        for L in (1, 2, 3):
            cp = ce["plans"]["scroll%d" % L]; ts = cp["taille_tuile"]
            c0 = cp["monde_tilemap_px"]["x0"] // ts; r0 = cp["monde_tilemap_px"]["y0"] // ts
            st = collections.Counter(); neuf[L] = {}; n0 = len(RF.neuves[L])
            for r, row in enumerate(cp["cases"]):
                for c, e in enumerate(row):
                    if e[6] not in "nr": continue
                    col = (c0 + c) % WT[L]; rg = (r0 + r) % HT[L]
                    pens = E.flip(E.decode_tile(rega, L, e[0], c0 + c), e[2], e[3])
                    pal = e[1]
                    v0 = T0[L].get((col, rg))
                    if v0 is not None:
                        p0 = E.flip(RF.tuile(L, v0[0]), v0[1] & 0x20, v0[1] & 0x40)
                        if (v0[1] & 0x1F) == pal and (p0 == pens).all():
                            st["deja_identiques"] += 1; continue
                    (code, fx, fy), cree = RF.cherche_ou_ajoute(L, pens)
                    st["tuiles_neuves" if cree else "reprises_memoire_decor"] += 1
                    attr = (e[5] & ~0x7F) | pal | (fx << 5) | (fy << 6)
                    if L != 1: attr &= 0xFF
                    bx, by = (col // NT[L]) % NBX[L], rg // NT[L]
                    neuf[L].setdefault(by * NBX[L] + bx, {})[(col % NT[L], rg % NT[L])] = (code, attr)
            stats[L] = dict(st, codes_neufs=["$%X" % x for x in RF.neuves[L][n0:]])
            print("decor %02X scroll%d : %s ; positions de liste touchees %s" % (dec, L, dict(st), sorted(neuf[L])))
        # palettes neuves : emplacement interdit s'il sert a une case QUELCONQUE des tilemaps completes (donnees du
        # programme : cases hors de la course enregistree, visibles quand la camera monte ; tuiles animees) ; scroll3
        # $7F : la routine du jeu (arcade $1FC70, ro3 $639A/$660E) ne copie que 31 palettes et force $7F au blanc
        import palettes_libres as PL
        for dd in ds:
            u = PL.utilisees(img0, M, dd)
            for L in (1, 2, 3):
                for k in pn.get("scroll%d" % L, {}):
                    assert int(k[1:], 16) != 0x7F, "palette $7F : forcee au blanc par le jeu, inutilisable"
                    assert int(k[1:], 16) not in u[L] or a.forcer_palettes, (
                        "palette neuve %s deja utilisee par la tilemap complete du decor %02X (hors course enregistree) ; "
                        "emplacements surs : py/palettes_libres.py" % (k, dd))
        D_.append(dict(dos=dos, ds=ds, dec=dec, ce=ce, pn=pn, rega=rega, T0=T0, neuf=neuf, stats=stats))

    # ---------------- 2. relogement : listes, bibliotheques -> bloc externe ----------------
    reloc = {}
    for L, cle in ((1, "list1"), (2, "list2"), (3, "list3")):
        t = M[cle]
        offs = [struct.unpack_from(">H", img0, t + 2 * i)[0] for i in range(nd)]
        n = max(offs) + 128                                   # + 128 o : la copie du jeu lit 128 o par liste
        na = mem.alloue(n + 128 * len(tous) + 64)
        mem.ecrit(na, img0[t:t + n])
        reloc[cle] = na
    cap1 = (M["st1"] - M["b1"]) // 0x80
    nst = (M["b2"] - M["st1"]) // 0x40
    cap2 = (M["b3"] - M["b2"]) // 0x300
    cap3 = 256
    rapport["capacites_origine"] = dict(blocs1=cap1, supertuiles1=nst, blocs2=cap2, blocs3=cap3)
    nb_neufs = {L: sum(len(x["neuf"][L]) for x in D_) for L in (1, 2, 3)}
    b1n = mem.alloue((cap1 + nb_neufs[1]) * 0x80); mem.ecrit(b1n, img0[M["b1"]:M["b1"] + cap1 * 0x80])
    b2n = mem.alloue((cap2 + nb_neufs[2]) * 0x300); mem.ecrit(b2n, img0[M["b2"]:M["b2"] + cap2 * 0x300])
    b3n = mem.alloue(cap3 * 0xC0); mem.ecrit(b3n, img0[M["b3"]:M["b3"] + cap3 * 0xC0])
    reloc.update(b1=b1n, b2=b2n, b3=b3n)
    st_lib = {}
    for i in range(nst):
        st_lib.setdefault(bytes(img0[M["st1"] + 0x40 * i:M["st1"] + 0x40 * i + 0x40]), i)
    st_neuves = []
    # scroll3 : numeros AU-DELA du plus grand bloc cite par les listes de decor (fin reelle de la bibliotheque : les
    # « blocs » suivants sont d'autres donnees), et libres selon blocs_libres.json (fins, appels a numero immediat)
    max3 = max(n for dd in range(0, 2 * nd, 2) for n in BT.liste(img0, M, 3, dd)[1])
    libres3 = [n for n in (int(x[1:], 16) for x in json.load(open(a.libres3))[a.module]["scroll3"]["libres"]) if n > max3]
    numeros = {1: cap1, 2: cap2}
    assert cap1 + nb_neufs[1] <= 256 and cap2 + nb_neufs[2] <= 256 and nb_neufs[3] <= len(libres3), "plus de numeros de blocs"
    for x in D_:
        x["blocs"] = {}; x["listes"] = {}
        for L in (1, 2, 3):
            x["blocs"][L] = []
            typ, lst, adr_l = BT.liste(img0, M, L, x["dec"])
            lst = list(lst); assert adr_l % 2 == 0
            for pos, cases in sorted(x["neuf"][L].items()):
                ancien = lst[pos]
                cur = BT.bloc(img0, M, L, ancien)
                cur.update(cases)
                num = libres3.pop(0) if L == 3 else numeros[L]
                if L != 3: numeros[L] += 1
                if L == 1:
                    idx = []
                    for k in range(64):
                        scol, srow = k >> 3, k & 7
                        raw = b"".join(struct.pack(">HH", cur[(scol * 4 + (j >> 2), srow * 4 + (j & 3))][1],   # long PS2 :
                                                   cur[(scol * 4 + (j >> 2), srow * 4 + (j & 3))][0])   # (attr, code)
                                       for j in range(16))
                        if raw not in st_lib:
                            st_lib[raw] = nst + len(st_neuves); st_neuves.append(raw)
                        idx.append(st_lib[raw])
                    mem.ecrit(b1n + num * 0x80, b"".join(struct.pack(">H", i) for i in idx))
                else:
                    nb = 256 if L == 2 else 64; sh = 4 if L == 2 else 3; msk = (1 << sh) - 1
                    add = M["add2"] if L == 2 else M["add3"]
                    codes = b"".join(struct.pack(">H", (cur[(k >> sh, k & msk)][0] - add) & 0xFFFF) for k in range(nb))
                    attrs = bytearray(nb)
                    for k in range(nb): attrs[k ^ 1] = cur[(k >> sh, k & msk)][1] & 0xFF   # octets : paires echangees
                    mem.ecrit((b2n if L == 2 else b3n) + num * BT.TAILLE[L], codes + bytes(attrs))
                lst[pos] = num
                x["blocs"][L].append(dict(position=pos, bloc_avant="$%02X" % ancien, bloc_neuf="$%02X" % num, cases=len(cases)))
            x["listes"][L] = lst
    stn = mem.alloue(nst * 0x40 + len(st_neuves) * 0x40)
    mem.ecrit(stn, img0[M["st1"]:M["st1"] + nst * 0x40] + b"".join(st_neuves))
    reloc["st1"] = stn
    assert nst + len(st_neuves) <= 0x10000
    # listes propres a chaque decor (et a ses decors lies) dans les tables relogees
    for L, cle in ((1, "list1"), (2, "list2"), (3, "list3")):
        t = reloc[cle]
        offs = [struct.unpack_from(">H", img0, M[cle] + 2 * i)[0] for i in range(nd)]
        fin = (t + max(offs) + 128 + 1) // 2 * 2
        j = 0
        for x in D_:
            for dd in x["ds"]:
                src = M[cle] + struct.unpack_from(">H", img0, M[cle] + dd)[0]
                na = fin + 128 * j; j += 1
                data = bytearray(img0[src:src + 128])
                for k, n in enumerate(x["listes"][L]): data[k ^ 1] = n                  # octet k lu a l'adresse k^1
                mem.ecrit(na, bytes(data))
                mem.ecrit(t + dd, struct.pack(">H", na - t))
                assert 0 < na - t < 0x8000

    # ---------------- 3. palettes : tables relogees, 32 palettes completes par decor ----------------
    for L in (1, 2, 3):
        t0 = M["pal"][L]
        blocs = [t0 + struct.unpack_from(">h", img0, t0 + 2 * i)[0] for i in range(nd)]
        h = nd // 2
        zone = mem.alloue(nd * 1024 + 2 * nd + 64, 32)
        tn = zone + h * 1024                                    # table au milieu : decalages signes 16 bits
        for i in range(nd):
            dst = zone + i * 1024 if i < h else (tn + 2 * nd + (i - h) * 1024 + 31) // 32 * 32
            mem.ecrit(dst, img0[blocs[i]:blocs[i] + 1024])
            o = dst - tn; assert -0x8000 <= o < 0x8000
            mem.ecrit(tn + 2 * i, struct.pack(">h", o))
        reloc["pal%d" % L] = tn
        for x in D_:
            x.setdefault("pal_info", {})
            for k, mots in sorted(x["pn"].get("scroll%d" % L, {}).items()):
                p = int(k[1:], 16) - E.PAL0[L]
                assert all(int(m_, 16) >> 12 == 0xF for m_ in mots[:15]), "palette %s : luminosite != F" % k
                for dd in x["ds"]:
                    adr = tn + struct.unpack(">h", mem.lire(tn + dd, 2))[0] + 32 * p
                    mem.ecrit(adr, b"".join(struct.pack(">H", int(m_, 16) & 0x0FFF) for m_ in mots))
                    x["pal_info"]["%02X %s" % (dd, k)] = "$%06X" % adr

    # ---------------- 4. programme : operandes des LEA ----------------
    patch = {}
    for nom, cle in (("bloc1", "b1"), ("st1", "st1"), ("bloc2", "b2"), ("bloc3", "b3"),
                     ("liste1", "list1"), ("liste2", "list2"), ("liste3", "list3"),
                     ("pal1", "pal1"), ("pal2", "pal2"), ("pal3", "pal3")):
        ancien = M[cle] if cle in M else M["pal"][int(cle[-1])]
        for s0 in M["sites"][nom]:
            s = s0 + 2                                        # site = adresse de l'instruction ; operande long a +2
            op = struct.unpack_from(">H", img, s0)[0]
            assert op & 0xF1FF == 0x41F9, "site %X : pas un LEA abs.L (%04X)" % (s0, op)
            assert struct.unpack_from(">I", img, s)[0] == ancien, "site %X : operande %X != %X" % (s0, struct.unpack_from(">I", img, s)[0], ancien)
            struct.pack_into(">I", img, s, reloc[cle]); patch["$%06X" % s0] = "$%06X -> $%06X" % (ancien, reloc[cle])
    ext = bytes(mem.ext[:mem.fin + (mem.fin & 1)])

    # ---------------- 5. verification ----------------
    MR = dict(M, b1=reloc["b1"], st1=reloc["st1"], b2=reloc["b2"], b3=reloc["b3"], list1=reloc["list1"],
              list2=reloc["list2"], list3=reloc["list3"], pal={1: reloc["pal1"], 2: reloc["pal2"], 3: reloc["pal3"]})
    D = bytearray(EXT + len(ext)); D[:len(img)] = img; D[EXT:] = ext      # memoire 68000 : image corrigee + bloc externe
    verif = {}
    for x in D_:
        ce, pn, rega, T0 = x["ce"], x["pn"], x["rega"], x["T0"]
        for dd in x["ds"]:
            for L in (1, 2, 3):
                cp = ce["plans"]["scroll%d" % L]; ts = cp["taille_tuile"]
                c0 = cp["monde_tilemap_px"]["x0"] // ts; r0 = cp["monde_tilemap_px"]["y0"] // ts
                T = BT.cases_tilemap(D, MR, L, dd)
                Tdd = BT.cases_tilemap(img0, M, L, dd)
                st = collections.Counter()
                for r, row in enumerate(cp["cases"]):
                    for c, e in enumerate(row):
                        k = ((c0 + c) % WT[L], (r0 + r) % HT[L])
                        v = T.get(k); v0 = Tdd.get(k)
                        if e[6] in "nr":
                            att = E.flip(E.decode_tile(rega, L, e[0], c0 + c), e[2], e[3])
                            got = E.flip(RF.tuile(L, v[0]), v[1] & 0x20, v[1] & 0x40)
                            ok = (got == att).all() and (v[1] & 0x1F) == e[1]
                            st["nouvelles_egales" if ok else "nouvelles_DIFFERENTES"] += 1
                        else:
                            st["origine_inchangees" if v == v0 else "origine_MODIFIEES"] += 1
                dom = {((c0 + c) % WT[L], (r0 + r) % HT[L]) for r in range(len(cp["cases"])) for c in range(len(cp["cases"][0]))}
                st["hors_monde_modifiees"] = sum(1 for kk in T if kk not in dom and T[kk] != Tdd.get(kk))
                at = MR["pal"][L] + struct.unpack_from(">h", D, MR["pal"][L] + dd)[0]
                a0 = M["pal"][L] + struct.unpack_from(">h", img0, M["pal"][L] + dd)[0]
                neuves = {int(y[1:], 16) - E.PAL0[L] for y in pn.get("scroll%d" % L, {})}
                st["palettes_identiques"] = sum(1 for p in range(32) if p not in neuves and D[at + 32 * p:at + 32 * p + 32] == img0[a0 + 32 * p:a0 + 32 * p + 32])
                st["palettes_neuves"] = len(neuves)
                verif["%02X_scroll%d" % (dd, L)] = dict(st)
    autres = 0; compares = 0
    for dd in range(0, 2 * nd, 2):
        if dd in tous: continue
        for L in (1, 2, 3):
            try:
                T1 = BT.cases_tilemap(D, MR, L, dd); T0_ = BT.cases_tilemap(img0, M, L, dd)
            except (IndexError, struct.error):
                continue
            compares += 1; autres += T1 != T0_
            at = MR["pal"][L] + struct.unpack_from(">h", D, MR["pal"][L] + dd)[0]
            a0 = M["pal"][L] + struct.unpack_from(">h", img0, M["pal"][L] + dd)[0]
            autres += D[at:at + 1024] != img0[a0:a0 + 1024]
    verif["autres_decors"] = dict(plans_compares=compares, modifies=autres)
    print("VERIFICATION", json.dumps(verif))
    ok = all(v.get("nouvelles_DIFFERENTES", 0) == 0 and v.get("origine_MODIFIEES", 0) == 0 and v.get("hors_monde_modifiees", 0) == 0
             and v.get("palettes_identiques", 32) + v.get("palettes_neuves", 0) == 32
             for k, v in verif.items() if k != "autres_decors") and autres == 0

    # ---------------- 6. sorties ----------------
    rom = os.path.join(a.sortie, "roms", "sfa3hx")
    image.ecrit(img, rom, modele=a.roms)
    extd = os.path.join(a.sortie, "ext"); os.makedirs(extd, exist_ok=True)
    open(os.path.join(extd, "ext_%06x.bin" % EXT), "wb").write(ext)
    src_ext = os.path.abspath(os.path.dirname(os.path.dirname(a.roms.rstrip("/"))))   # dossier du module (ext_*.bin)
    for f in sorted(os.listdir(src_ext)):
        if f.startswith("ext_") and f.endswith(".bin") and f != "ext_%06x.bin" % EXT:
            p = os.path.join(extd, f)
            if os.path.islink(p) and not os.path.exists(p): os.unlink(p)        # lien casse d'une execution precedente
            if not os.path.exists(p): os.symlink(os.path.join(src_ext, f), p)
            assert os.path.exists(p), "bloc externe introuvable : %s" % p
    liste = sorted({l.strip() for l in open(os.path.join(src_ext, "ext_liste.txt")) if l.strip()} | {"%06x" % EXT})
    open(os.path.join(extd, "ext_liste.txt"), "w").write("\n".join(liste) + "\n")
    open(os.path.join(a.sortie, "hsfa_plans_decor.bin"), "wb").write(bytes(RF.r).rstrip(b"\0"))
    gfx = []                                     # tuiles neuves seules (fichier@decalage, a charger APRES hsfa_plans.bin)
    os.makedirs(os.path.join(a.sortie, "tuiles"), exist_ok=True)
    for L in (1, 2, 3):
        for c in RF.neuves[L]:
            o = OFF[L] + c * TBF[L]
            nom = "t%d_%04X.bin" % (L, c)
            open(os.path.join(a.sortie, "tuiles", nom), "wb").write(bytes(RF.r[o:o + TBF[L]]))
            gfx.append("%s@%X" % (os.path.abspath(os.path.join(a.sortie, "tuiles", nom)), ORG + o))
    open(os.path.join(a.sortie, "hsfa_gfx.txt"), "w").write(",".join(gfx) + "\n")
    nmod = sum(1 for p_, q_ in zip(img0, img) if p_ != q_)
    for x in D_:
        rapport["decors"].append(dict(carte=os.path.abspath(x["dos"]), decors=["$%02X" % d_ for d_ in x["ds"]],
                                      stats={"scroll%d" % L: x["stats"][L] for L in (1, 2, 3)},
                                      blocs={"scroll%d" % L: x["blocs"][L] for L in (1, 2, 3)},
                                      listes={"scroll%d" % L: x["listes"][L] for L in (1, 2, 3)},
                                      palettes_neuves=x.get("pal_info", {})))
    rapport.update(supertuiles_neuves=len(st_neuves), tuiles_neuves={"scroll%d" % L: len(RF.neuves[L]) for L in (1, 2, 3)},
                   relogement={k: "$%06X" % v for k, v in reloc.items()}, sites=patch,
                   octets_programme_modifies=nmod, bloc_externe_octets=len(ext), verification=verif, ok=ok,
                   bases_plans="HSFA_PLANS=%x,%x,%x" % (BASES[1], BASES[2], BASES[3]))
    json.dump(rapport, open(os.path.join(a.sortie, "rapport_fork.json"), "w"), indent=1)
    print("programme : %d octets modifies (%d sites) ; bloc externe $%06X : %d octets ; super-tuiles neuves %d ; tuiles neuves %s"
          % (nmod, len(patch), EXT, len(ext), len(st_neuves), {L: len(RF.neuves[L]) for L in (1, 2, 3)}))
    print("OK" if ok else "ECARTS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
