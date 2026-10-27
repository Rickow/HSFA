#!<workspace>/venv/bin/python
"""ROM son PROPRE A HYPER (prototype) : copie de la ROM son avec voix MAX (agent_voix_max/roms_voix, elle-meme hybride
d'Upper + voix MAX) + voix d'origine SFA1 (versions ZERO) et SFA2 (versions ZERO 2 et ALPHA) sur des numeros de
commande libres, + table de redirection « version d'Hyper ($102) x code SFA3 -> nouvelle commande ».
La ROM roms_voix n'est jamais modifiee (lecture seule).

Entrees :
  catalogue/correspondance.json (outils/correspondance.py) : code SFA3 du bloc du perso de base -> echantillon source
      (decision « voix » ou « cri » ; « identique » = SFA3 joue deja l'echantillon d'origine ; « aucun » = on garde SFA3) ;
  catalogue/<jeu>.json (outils/catalogue.py) : echantillons des balayages (banque, debut, fin, frequence) ;
  src/<jeu>_qs.bin : image QSound d'origine (X_DATA e222 = SFA1, e251 = SFA2) ;
  agent_hyper_index/ids_102.tsv : versions d'Hyper (famille, perso de base).
Construction (memes regles que gen_voix_max.py, cf. VOIX-MAX.md : adresses QSound signees, banques ENTIERES jamais
referencees, rien a cheval sur 2 banques Z80) :
  - echantillons : 8 bits signes d'origine, recopies tels quels si la frequence d'origine est une hauteur exacte du
    pilote (SFA2 : 12 019 Hz = $0800 ; SFA1 : 20 188 / 24 038 Hz...), sinon reechantillonnes (sinc de Kaiser) a la plus
    petite hauteur >= ; aucun gain applique : le niveau est rattrape par l'octet de volume (op 07) ;
  - Z80 : entrees d'echantillons dans la zone fixe libre $797D-$7FFF (indices 1537.., la sentinelle 1536 = $7975 est
    gardee), programmes : suite de la table NEWPT[22] (Ingrid, programmes 29-127, $77D5..) puis NEWPT[23] (nouvelle) ;
  - morceaux : COPIE du morceau SFA3 remplace (priorite, voies, volumes, echos du K.O.), dont on change le programme
    (1F NN / 08 II), le tempo des pistes a une seule note (duree = voix + 30 ms) et les volumes (rapport des RMS) ;
    places dans les zones nulles de la banque 6 (0x29B55-0x2BC04) et 15 (0x4DE9A-0x4FFFF) ;
  - commandes : numeros libres partout (Z80 vide, table PS2 « - », jamais vus dans les journaux) ; une seule commande
    par voix (le cote 2 n'a pas besoin d'un double : la redirection rend le meme numero pour les deux cotes).
Priorites si la place manque : Ryu et Ken d'abord, puis voix longues, puis cris.
Sorties : roms_hyper/ (hx3.*, z80_hyper.bin, md5.txt, attribution.json), redirection.txt (« version code nouvelle »,
cote 1), redirection_hyper.tsv (lisible)."""
import os, sys, json, csv, struct, glob, re
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "<workspace>/work/agent_voix_max"); sys.path.insert(0, "<workspace>/work/agent_son_ro5/hybride")
sys.path.insert(0, os.path.join(ICI, "outils"))
import gen_voix_max as G
from z80son import lin2reg, ARGS

BASE = "<workspace>/work/agent_voix_max/roms_voix"
QS_HZ = G.QS_HZ
TAB_VOL = 0x2E92
NEWPT = 0x6B10
FIXE_A = (0x77D5, 0x7975)           # suite de la table de programmes NEWPT[22] (Ingrid : 29 programmes)
FIXE_B = (0x797D, 0x8000)           # entrees d'echantillons (alignees sur $4975 + 8n) + table NEWPT[23]
N_INGRID = 29
MORC = [(0x29B55, 0x2BC00), (0x4DE9A, 0x50000)]
FAMILLE_JEU = {"ZERO": "sfa1", "ZERO 2": "sfa2", "ZERO 2 ALPHA": "sfa2"}
PRIO_PERSOS = (0x00, 0x01)
# frequence maximale des echantillons ajoutes : les voix SFA2 (et SFA3) sont a 12 019 Hz ; celles de SFA1 a 20-24 kHz ne
# tiennent pas toutes dans les 1,3 Mo libres -> ramenees par defaut a 12 019 Hz (HSFA_HZ_SFA1 pour changer)
HZ_MAX = {"sfa1": float(os.environ.get("HSFA_HZ_SFA1", "12019.3")), "sfa2": 48000.0}
SEUIL_SILENCE = 2


def cat(jeu): return json.load(open(os.path.join(ICI, "catalogue", jeu + ".json")))


def pcm_source(jeu, e):
    q = open(os.path.join(ICI, "src", jeu + "_qs.bin"), "rb").read()
    b, d, f = e["banque"], e["debut"], e["fin"]
    base = b << 16
    raw = q[base + d: base + f + 1] if f >= d else q[base + d: base + 0x10000] + q[base: base + f + 1]
    return np.frombuffer(raw, np.int8)


def rms_actif(x):
    x = np.asarray(x, float)
    if len(x) == 0: return 0.0
    s = 0.03 * np.abs(x).max()
    a = x[np.abs(x) > s]
    return float(np.sqrt(np.mean(a ** 2))) if len(a) else 0.0


def pistes_brutes(p, c):
    """morceau SFA3 de la commande c : priorite + [(voie, octets de la piste jusqu'a $17 inclus)]"""
    a, _ = p.cmd(c)
    pr, pistes = p.morceau(a)
    out = []
    for k, L in enumerate(pistes):
        if L is None: continue
        b, i = bytearray(), L
        while True:
            op = p.rb(i)
            if op >= 0x20: b.append(op); i += 1; continue
            n = ARGS[op]
            b += bytes(p.rb(i + j) for j in range(n + 1))
            i += n + 1
            if op == 0x17: break
            assert op not in (0x0e, 0x0f, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16), "saut dans une piste de voix %04X" % c
        out.append((k, bytes(b)))
    return pr, out


def ops(b):
    i, r = 0, []
    while i < len(b):
        op = b[i]
        if op >= 0x20: r.append((i, op, [])); i += 1; continue
        n = ARGS[op]; r.append((i, op, list(b[i + 1:i + 1 + n]))); i += n + 1
    return r


def vol_proche(T, cible):
    return int(np.argmin([abs(t - cible) for t in T[:128]]))


def commandes_libres(z, p):
    ps2 = {int(r["cmd"], 16): r["genre"] for r in csv.DictReader(open("<workspace>/work/agent_hyper_son/table_son_ro9.csv"))}
    vues = G.commandes_vues()
    for f in glob.glob("<workspace>/work/agent_flux/essais/*.son") + glob.glob("<workspace>/work/agent_hyper_etats/essais/*.son"):
        for m in re.finditer(r"cmd ([0-9a-f]{4})", open(f, errors="replace").read()): vues.add(int(m.group(1), 16))
    T = json.load(open(os.path.join(ICI, "catalogue", "tables_hyper.json")))
    tables = set(int(c, 16) for v in T.values() for c in v["codes"])
    out = []
    for c in range(0xC00):
        if p.cmd(c)[0]: continue
        if ps2.get(c) != "-": continue
        if c in vues or c in tables or (c - 0x500) in tables: continue
        out.append(c)
    # d'abord la page 07 (cote 2 de la page 02 : $0780-$07FC), puis 00/01
    return sorted(out, key=lambda c: (0 if 0x780 <= c < 0x800 else 1, c))


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "roms_hyper")
    z0, q0 = G.lit_base(BASE)
    z, q = bytearray(z0), bytearray(q0)
    p0 = G.pilote(z0)
    H = G.hauteurs(z0)
    TV = [struct.unpack_from("<H", z0, TAB_VOL + 2 * i)[0] for i in range(256)]
    ref, _ = G.zones_referencees(p0, z0)
    libres = G.zones_libres(q0, ref)
    print("QSound : %d banques entieres libres (%d o)" % (len(libres), len(libres) * 0x10000))
    corr = [r for r in json.load(open(os.path.join(ICI, "catalogue", "correspondance.json"))) if r["decision"] in ("voix", "cri", "ko")]
    cats = {j: cat(j) for j in ("sfa1", "sfa2", "sfa3")}
    # --- echantillons sources necessaires, par ordre de priorite
    def prio(r): return (0 if r["base"] in PRIO_PERSOS else 1, {"ko": 0, "voix": 1}.get(r["decision"], 2), r["jeu"], r["base"], r["code"])
    corr.sort(key=prio)
    voix, index = [], {}
    for r in corr:
        k = (r["jeu"], r["ech"])
        if k in index: continue
        e = cats[r["jeu"]]["echantillons"][r["ech"]]
        x = pcm_source(r["jeu"], e)
        nz = np.where(np.abs(x.astype(int)) > SEUIL_SILENCE)[0]          # silences de debut et de fin retires
        if len(nz): x = x[max(0, nz[0] - 8): nz[-1] + 9]
        fr = e["hz"]
        prm, f = G.choix_param(min(fr, HZ_MAX[r["jeu"]]), len(x), H)
        if abs(f - fr) / fr < 0.003:
            y = x.astype(np.int8); f = fr; exact = True
        else:
            y = np.clip(np.round(G.reechantillonne(x.astype(float), fr, f)), -128, 127).astype(np.int8); exact = False
        data = y.tobytes() + bytes(16)
        index[k] = len(voix)
        voix.append(dict(jeu=r["jeu"], ech=r["ech"], src=r["src"], hz_src=fr, hz=round(f, 1), param=prm, exact=exact,
                         octets=len(data), duree=round(len(y) / f, 3), rms=rms_actif(y), _data=data, prio=prio(r)))
    # --- placement QSound (ordre de priorite ; au premier echec, la voix et les suivantes sont abandonnees)
    zl = [list(x) for x in libres]
    if os.environ.get("HSFA_TROUS") == "1":
        # OPTION ABANDONNEE (decision du 2026-10-10 : une zone jamais lue peut etre du code ou des donnees non identifies).
        # Hors regle de VOIX-MAX.md : aussi les trous NON REFERENCES des banques deja utilisees (surtout des
        # copies mortes de e288). Effet connu : quand une voie change d'echantillon, le DSP lit quelques octets a
        # (ancienne banque, nouveau debut) ; ces octets etaient deja des donnees mortes, ils deviennent nos voix : son
        # inchange a l'oreille mais plus identique a l'octet (cf. VOIX-MAX.md §1, decouverte 2).
        mask = np.zeros(len(q0), bool)
        for a, b in ref: mask[a:b + 1] = True
        utilisees = sorted(set(a >> 16 for a, b in ref) | set(b >> 16 for a, b in ref))
        for bk in utilisees:
            for moitie in (0x8000, 0x0000):                     # ordre signe : $8000-$FFFF puis $0000-$7FFF
                lo = (bk << 16) | moitie; m = mask[lo:lo + 0x8000]
                i = 0
                while i < 0x8000:
                    if m[i]: i += 1; continue
                    j = i
                    while j < 0x8000 and not m[j]: j += 1
                    if j - i >= 0x1000:                          # trous de 4 Ko et plus, marge de 256 o de chaque cote
                        u0 = ((moitie + i + 0x100) ^ 0x8000) & 0xFFFF; u1 = ((moitie + j - 0x100 - 1) ^ 0x8000) & 0xFFFF
                        zl.append([bk, u0, u1])
                    i = j
    gardees = []
    max_voix = (FIXE_B[1] - FIXE_B[0] + 4 * (128 - N_INGRID)) // 12     # entrees (8 o) + programmes (4 o) en zone fixe
    for v in voix:
        if len(gardees) >= max_voix: v["place"] = None; continue
        for b in zl:
            if b[2] - b[1] + 1 >= v["octets"]:
                v["place"] = (b[0], b[1]); b[1] += v["octets"] + (-v["octets"] % 16); break
        else:
            v["place"] = None; continue
        bank, u0 = v["place"]
        u = np.arange(u0, u0 + v["octets"])
        phys = (bank << 16) | (u ^ 0x8000)
        for i, o in enumerate(phys): q[o] = v["_data"][i]
        deb, fin = u0 ^ 0x8000, u[-1] ^ 0x8000
        v["adresse"] = "%06X" % ((bank << 16) | deb)
        v["entree"] = bytes([bank]) + struct.pack("<HHH", deb, (fin - 1) & 0xFFFF, fin) + bytes([v["param"]])
        gardees.append(v)
    abandon = [v for v in voix if not v.get("entree")]
    occ = sum(v["octets"] for v in gardees)
    print("echantillons : %d places (%d o = %.2f Mo), %d abandonnes faute de place" % (len(gardees), occ, occ / 2 ** 20, len(abandon)))
    # --- Z80 : entrees d'echantillons et programmes
    n0 = (FIXE_B[0] - G.TECH) // 8
    assert G.TECH + 8 * n0 == FIXE_B[0]
    ng = len(gardees)
    nA = min(ng, 128 - N_INGRID)                 # programmes en suite de NEWPT[22]
    nB = ng - nA
    fin_ent = FIXE_B[0] + 8 * ng
    tabB = fin_ent
    assert tabB + 4 * nB <= FIXE_B[1], "zone fixe pleine"
    assert FIXE_A[0] + 4 * nA <= FIXE_A[1]
    assert z[FIXE_A[0]:FIXE_A[0] + 4 * nA] == bytes(4 * nA) and z[FIXE_B[0]:tabB + 4 * nB] == bytes(tabB + 4 * nB - FIXE_B[0])
    assert struct.unpack_from("<H", z, NEWPT + 2 * 22)[0] + 4 * N_INGRID == FIXE_A[0]
    assert struct.unpack_from("<H", z, NEWPT + 2 * 23)[0] == 0
    if nB: struct.pack_into("<H", z, NEWPT + 2 * 23, tabB)
    for i, v in enumerate(gardees):
        v["n_ech"] = n0 + i
        z[G.TECH + 8 * v["n_ech"]:G.TECH + 8 * v["n_ech"] + 8] = v["entree"]
        if i < nA: v["prog"] = (22, N_INGRID + i); P = FIXE_A[0] + 4 * i
        else: v["prog"] = (23, i - nA); P = tabB + 4 * (i - nA)
        z[P:P + 4] = struct.pack("<H", v["n_ech"]) + b"\x00\x40"
    # --- morceaux et commandes
    libres_c = commandes_libres(z0, p0)
    zones = [list(m) for m in MORC]
    for a, b in MORC: assert z[a:b] == bytes(b - a), "zone morceaux non nulle %X" % a
    cmd_de = {}
    redir = []
    fs3 = {}
    for r in corr:
        k = (r["jeu"], r["ech"])
        v = voix[index[k]] if voix[index[k]].get("entree") else None
        if v is None: r["nouvelle"] = None; continue
        c3 = int(r["code"], 16)
        pr, pistes = pistes_brutes(p0, c3)
        e3 = cats["sfa3"]["echantillons"][r["ech3"]]
        if r["ech3"] not in fs3:
            fs3[r["ech3"]] = rms_actif(np.frombuffer(open(os.path.join(ICI, "wav", "sfa3", "ech_%s.wav" % r["ech3"]), "rb").read()[44:], "<i2") / 256.0)
        rap = fs3[r["ech3"]] / v["rms"] if v["rms"] else 1.0
        nouv = []
        for voie, b in pistes:
            b = bytearray(b); O = ops(b)
            notes = [o for o in O if o[1] >= 0x20]
            tempos = [o for o in O if o[1] == 0x05]
            for i, op, arg in O:
                if op == 0x1f: b[i + 1] = v["prog"][0]
                elif op == 0x08: b[i + 1] = v["prog"][1]
                elif op == 0x07: b[i + 1] = min(127, vol_proche(TV, TV[arg[0]] * rap))
            if len(notes) == 1 and len(tempos) == 1:
                tt, _ = G.tempo_pour(v["duree"], z0)
                b[tempos[0][0] + 1] = tt
            nouv.append((voie, bytes(b)))
        ent = bytearray(33); ent[0] = pr
        corps = b""
        for voie, b in nouv:
            struct.pack_into(">H", ent, 1 + 2 * voie, 33 + len(corps)); corps += b
        m = bytes(ent) + corps
        if m not in cmd_de:
            if not libres_c: r["nouvelle"] = None; continue
            for zz in zones:
                a = zz[0]
                if (a & 0x3FFF) + len(m) > 0x4000: a = (a | 0x3FFF) + 1
                if a + len(m) <= zz[1]: break
            else:
                raise SystemExit("plus de place pour les morceaux")
            z[a:a + len(m)] = m; zz[0] = a + len(m)
            L = a - 0x8000
            c = libres_c.pop(0)
            _, Lc = p0.cmd(c); rr = lin2reg(Lc)
            assert z[rr:rr + 4] == bytes(4)
            z[rr:rr + 4] = bytes([L >> 16, (L >> 8) & 0xff, L & 0xff, 0])
            cmd_de[m] = c
            v.setdefault("commandes", []).append("%04X" % c)
        r["nouvelle"] = "%04x" % cmd_de[m]
    # --- table de redirection par version
    ids = list(csv.DictReader(open("<workspace>/work/agent_hyper_index/ids_102.tsv"), delimiter="\t"))
    lignes, tsv = [], ["version\tid\tnom\tfamille\tcode_SFA3\tnouvelle_commande\tsource\tcode_source\tdecision\tdistance"]
    for row in ids:
        vid = int(row["id"][1:], 16); fam = row["version"].strip()
        jeu = FAMILLE_JEU.get(fam)
        if not jeu or not row["base"].startswith("$"): continue
        base = int(row["base"][1:], 16)
        for r in corr:
            if r["jeu"] == jeu and r["base"] == base and r.get("nouvelle"):
                lignes.append("%02x %s %s" % (vid, r["code"], r["nouvelle"]))
                tsv.append("%s\t%02X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.3f" % (fam, vid, row["nom"], fam, r["code"].upper(), r["nouvelle"].upper(),
                           jeu.upper(), r["src"].upper(), r["decision"], r["d"]))
    open(os.path.join(ICI, "redirection.txt"), "w").write(
        "# version($102) code_SFA3(cote 1) nouvelle_commande ; cote 2 (code + $500) -> meme nouvelle commande\n" + "\n".join(lignes) + "\n")
    open(os.path.join(ICI, "redirection_hyper.tsv"), "w").write("\n".join(tsv) + "\n")
    # --- verification statique
    p = G.pilote(bytes(z))
    nouv = set(cmd_de.values())
    diff = 0
    for c in range(0xC00):
        if c in nouv: continue
        if p0.resolution(c) != p.resolution(c): diff += 1; print("  DIFFERENCE %04X" % c)
    for a, b in ref: assert q[a:b + 1] == q0[a:b + 1], "zone referencee modifiee %X" % a
    assert bytes(z[:0x3800]) == bytes(z0[:0x3800])
    for m, c in cmd_de.items():
        rr = p.resolution(c); e = [t for t in rr if t[0] == "08"]
        assert e and all(t[3] in [v["entree"] for v in gardees] for t in e), "%04X" % c
    print("verification : %d commandes anciennes identiques, %d differentes ; %d nouvelles commandes resolues"
          % (0xC00 - len(nouv) - diff, diff, len(nouv)))
    G.ecrit(out_dir, bytes(z), bytes(q), [])
    os.rename(os.path.join(out_dir, "z80_voix.bin"), os.path.join(out_dir, "z80_hyper.bin"))
    md = open(os.path.join(out_dir, "md5.txt")).read().replace("z80_voix.bin", "z80_hyper.bin")
    open(os.path.join(out_dir, "md5.txt"), "w").write(md)
    att = [{k: (x.hex(" ") if isinstance(x, bytes) else x) for k, x in v.items() if not k.startswith("_")} for v in voix]
    json.dump(dict(voix=att, correspondance=corr), open(os.path.join(out_dir, "attribution.json"), "w"), indent=1)
    rest = sum(b[2] - b[1] + 1 for b in zl)
    print("commandes : %d nouvelles (%s..), redirections : %d lignes ; QSound restant : %d o ; morceaux : %s"
          % (len(cmd_de), min(cmd_de.values()) if cmd_de else 0, len(lignes), rest, ["%X/%X" % tuple(x) for x in zones]))


if __name__ == "__main__":
    main()
