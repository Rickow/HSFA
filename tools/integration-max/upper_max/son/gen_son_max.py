#!/usr/bin/env python3
"""ROM son « MAX corrigée » = COPIE de agent_voix_max/roms_voix (voix MAX v2, jamais modifiée) + trois ajouts :

1. CRIS DE DÉGÂTS : par perso MAX, un bloc de 9 commandes consécutives base+0..8 (+ le même bloc à +$500, côté 2),
   qui jouent les échantillons v2 déjà présents (rôle n = voix PSP n° n, table de la session MAX ; « None » = muet,
   commande laissée vide). Chaque rôle reprend la priorité et la voie QSound des cris d'arcade (mesurées sur les 30
   blocs de SFA3/Upper, identiques partout) : n0 K.O. $20 voie 12, côté 2 voie 14 (arcade : 11+12 / 11+14, écho ;
   les K.O. MAX ont déjà leur traîne et durent 2-3 s : sur la voie 11 ils refusaient la voix de victoire du gagnant,
   priorité $0A, envoyée ~2,5-3 s après le K.O. -> seule la 2e voie de l'arcade est gardée, correctif du 24/10), n1-2 $0A voie 11, n3 $10 voie 12, n4 $0B voie 11, n5-8 $10 voie 12 ; côté 2,
   les rôles de la voie 12 passent en voie 14 (comme l'arcade : J1 et J2 ne se coupent pas). Quand le rôle a la
   priorité et la voie d'une voix v2 ($0A, voie 11), la commande pointe sur le morceau v2 lui-même ; sinon, morceau
   neuf (même piste que la v2 : tempo, volume, programme).
2. VOIX D'INGRID A_095-A_103 (se_mid, banque A) : 9 échantillons QSound neufs (même chaîne que gen_voix_max :
   fréquence QSound >= 22 050 Hz, sinc de Kaiser, crête 124/127, fondus, 16 octets nuls), programmes 29-37 de la table
   NEWPT[22] d'Ingrid (prolongée), 9 morceaux $0A voie 11, commandes c et c+$500.
3. SÉQUENCES se_mid : $0D (séquence 10 = programme 9, I_009) = bruitage arcade $020E existant (appariement fort,
   sequences/appariement_sequences.tsv) : rien à ajouter ; $2C (séquence 37 = programme 16, I_016, coupé à la fin de
   la note, 0,667 s) : sans équivalent arcade -> importé (échantillon, programme 38 de NEWPT[22], morceau $10 voie 15
   comme son plus proche $0242, volume VOL_2C).

Numéros (analyse_numeros.py, ETAT.md) : blocs dans le bloc de perso $05E0 que ni SFA3, ni Upper, ni Hyper n'emploient
($05D9-$05F8) et en $06F6-$06FE ; voix d'Ingrid sur 8 des paires libres au sens strict de numeros.py + $05EC ($06FF exclu : côté 2 $0BFF = dernière
entrée de la table, dont le 4e octet, $BC05, est le début des musiques).
Vérification statique : les 3 072 commandes de roms_voix hors ajouts ont un contenu résolu identique, les octets
QSound référencés sont intacts, le code du pilote est inchangé, chaque ajout résout vers son échantillon.
Sorties : roms_son_max/ (hx3.*, z80_son_max.bin, md5.txt, attribution.json, zones.txt), commandes_son_max.s.
Usage : gen_son_max.py [dossier_sortie]"""
import os, sys, json, struct, hashlib, zlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ.get("SON_MAX_SRC_HSFA", "src/hsfa"))
import gen_voix_max as G                    # lecture seule : fonctions de la chaîne v2
from z80son import lin2reg

ICI = os.path.dirname(os.path.abspath(__file__))
V2 = os.environ.get("SON_MAX_VOIX", "roms_voix")      # sortie de gen_voix_max.py
MD5_V2 = {"hx3.01": "922642bfeb080212803d2242fb865c49", "hx3.02": "10cfead0d45b015098d2a13f75ab0a9f",
          "hx3.11m": "8da6a5e4272125bc0a7accada5e249e8", "hx3.12m": "2920bde5bea33dbca952d49edeb06329",
          "hx3.13m": "65c573eb71d7963c7fbe7f22f86b114c", "hx3.14m": "a29885802c1afe5f61783c56ef65a07a"}
PSP = os.path.join(os.environ.get("SON_MAX_COMMUNS", "communs"), "psp")

# 1. cris : perso -> (pl, base, voix PSP par rôle 0..8 ; None = muet)
CRIS = {
    "Eagle":  ("pl26", 0x05D9, [0, 1, 2, 3, None, 9, 19, 8, 17]),
    "Maki":   ("pl27", 0x05E2, [0, 1, 2, 3, None, 9, None, 8, 22]),
    "Yun":    ("pl28", 0x05F0, [0, 1, 2, 3, None, 9, None, 8, 21]),
    "Ingrid": ("pl29", 0x06F6, [0, 4, 4, 5, None, 5, None, 4, 1]),
}
ID_PERSO = {"Eagle": 0x26, "Maki": 0x27, "Yun": 0x2D, "Ingrid": 0x2E}
# (priorité, voie côté 1, voie côté 2) : mesuré sur les 30 blocs de cris (base+n et base+n+$500) de SFA3/Upper
ROLE = {0: (0x20, 12, 14),   # K.O. : 2e voie de l'arcade (12 / 14) ; la voie 11 reste libre pour la voix de victoire (correctif 24/10)
        1: (0x0A, 11, 11), 2: (0x0A, 11, 11), 3: (0x10, 12, 14), 4: (0x0B, 11, 11),
        5: (0x10, 12, 14), 6: (0x10, 12, 14), 7: (0x10, 12, 14), 8: (0x10, 12, 14)}
# 2. voix d'Ingrid : A_095..A_103 -> commandes (côté 1)
VOIX_INGRID = list(zip(range(95, 104), [0x05FE, 0x05FF, 0x063C, 0x063F, 0x069F, 0x06DD, 0x06DE, 0x06DF, 0x05EC]))
# ($06FF exclu : le 4e octet de l'entrée $0BFF, $BC05, est le 1er octet des musiques -> réserve $05EC)
# 3. séquences
SEQ_EXISTANTE = {0x0D: 0x020E}
SEQ_2C = (0x2C, 0x05EB, os.path.join(os.environ.get("SON_MAX_SEQ", os.path.join(ICI, "sequences")), "seq_2C.wav"))
PRIO_2C, VOIE_2C, VOIE2_2C = 0x10, 15, 13       # comme $0242 / $0742 (bruitages : voies 14-15 / 12-13)
VOL_2C = int(os.environ.get("VOL_2C", "0x75"), 0)     # niveau : $020E (= $0D) + écart PSP I_016/I_009 (+4,5 dB) -> $75 (mesuré)
NT_INGRID = 22                                        # NEWPT[22] = table de programmes d'Ingrid (v2 : 29 entrées)
MORC_DEB = 0x4DE9A                                    # banque 15 : suite des morceaux v2 (0x4C600-0x4DE99)
MORC_ZONES = [(0x4DE9A, 0x50000), (0x29B55, 0x2BC00)]  # banque 15 puis banque 6 libre (avant les musiques 0x2BC05)
# Voix « par pas » : priorité et voies des voix natives (511 sur 519 commandes base+7..$1F des 30 blocs de SFA3/Upper :
# $10, voie 12 au côté 1, voie 14 au côté 2 ; ex. voix de victoire de Ken $0335/$0835, Sagat $0472/$0972). La v2 les
# jouait toutes en $0A sur la voie 11, celle des cris de K.O. ($20, ~3,5 s) : la voix de victoire du gagnant était
# refusée (correctif du 24/10, PAS_V2=0 pour l'ancien comportement).
PAS_V2 = os.environ.get("PAS_V2", "1") != "0"
PRIO_PAS, VOIE_PAS, VOIE2_PAS = (0x10, 12, 14) if PAS_V2 else (G.PRIO, G.VOIE, G.VOIE)


def lit_v2():
    for n, m in MD5_V2.items():
        assert hashlib.md5(open(os.path.join(V2, n), "rb").read()).hexdigest() == m, "roms_voix modifiée : " + n
    z, q = G.lit_base(V2)
    att = json.load(open(os.path.join(V2, "attribution.json")))
    return bytearray(z), bytearray(q), att


def morceau(prio, voie, piste):
    ent = bytearray(33); ent[0] = prio
    struct.pack_into(">H", ent, 1 + 2 * voie, 33)
    return bytes(ent) + bytes(piste)


def piste(tt, vol, nt, i):
    return [0x05, tt, 0x06, 0xFF, 0x07, vol, 0x1F, nt, 0x08, i, 0x09, G.OCTAVE, G.NOTE, 0x17]


def echantillon(f, H):
    """conversion QSound identique à gen_voix_max.construit"""
    x, fr = G.lit_wav(f)
    prm, fq = G.choix_param(fr, len(x), H)
    y = G.reechantillonne(x, fr, fq) if abs(fq - fr) > 0.5 else x.copy()
    pic = np.abs(y).max()
    g = min(G.GAIN_MAX, G.CRETE / 127.0 / pic) if pic > 0 else 1.0
    s8 = np.clip(np.round(y * g * 127.0), -128, 127).astype(np.int8)
    nf = max(1, int(0.002 * fq)); s8[:nf] = np.round(s8[:nf] * np.linspace(0, 1, nf)).astype(np.int8)
    s8[-nf:] = np.round(s8[-nf:] * np.linspace(1, 0, nf)).astype(np.int8)
    data = s8.tobytes() + bytes(16)
    return dict(wav=f, fr_orig=fr, param=prm, fr_qs=round(fq, 2), hauteur=H[120 - prm], gain=round(g, 3),
                octets=len(data), duree=round(len(s8) / fq, 3), rms8=round(float(np.sqrt(np.mean(s8.astype(float) ** 2))), 1),
                _data=data)


def construit(z, q, att, journal=print):
    z0, q0 = bytes(z), bytes(q)
    p0 = G.pilote(z0)
    H = G.hauteurs(z0)
    v2 = {(v["pl"], v["n"]): v for v in att}
    ajouts = []                                    # commandes ajoutées : dict(cmd, cmd2, genre, ...)
    occupees = set()

    def pose(c, L, L2=None):
        for x, L in ((c, L), (c + 0x500, L if L2 is None else L2)):
            assert x not in occupees and p0.cmd(x)[0] == 0, "%04X non vide" % x
            _, Lc = p0.cmd(x); r = lin2reg(Lc)
            assert z[r:r + 4] == bytes(4)
            z[r:r + 4] = bytes([L >> 16, (L >> 8) & 0xff, L & 0xff, 0]); occupees.add(x)

    zones = [list(x) for x in MORC_ZONES]
    for a_, b_ in zones: assert z[a_:b_] == bytes(b_ - a_), "zone de morceaux non libre 0x%05X" % a_
    reg = MORC_DEB

    def range_morceau(m):
        nonlocal reg
        while True:
            zz = zones[0]
            r = zz[0]
            if (r & 0x3FFF) + len(m) > 0x4000: r = (r | 0x3FFF) + 1      # pas de morceau à cheval sur 2 banques
            if r + len(m) <= zz[1]: break
            zones.pop(0); assert zones, "plus de place pour les morceaux"
        z[r:r + len(m)] = m; zz[0] = r + len(m); reg = zz[0]
        return r - 0x8000

    cote2_v2 = {}
    # --- 0. voix v2 « par pas » : côté 1 = morceau v2 modifié en place ($10, voie 12) ; côté 2 = morceau neuf (voie 14)
    if PAS_V2:
        for v in att:
            r0 = v["morceau"] + 0x8000
            assert z[r0] == G.PRIO and z[r0 + 1 + 2 * G.VOIE:r0 + 3 + 2 * G.VOIE] == bytes([0, 33])
            pst = bytes(z[r0 + 33:r0 + 47]); assert pst[-1] == 0x17
            z[r0] = PRIO_PAS; z[r0 + 1 + 2 * G.VOIE:r0 + 3 + 2 * G.VOIE] = bytes(2)
            z[r0 + 1 + 2 * VOIE_PAS:r0 + 3 + 2 * VOIE_PAS] = bytes([0, 33])
            L2 = range_morceau(morceau(PRIO_PAS, VOIE2_PAS, pst))
            c2 = int(v["cmd2"], 16); _, Lc = p0.cmd(c2); rr = lin2reg(Lc)
            assert z[rr:rr + 3] == bytes([v["morceau"] >> 16, (v["morceau"] >> 8) & 0xff, v["morceau"] & 0xff])
            z[rr:rr + 3] = bytes([L2 >> 16, (L2 >> 8) & 0xff, L2 & 0xff])
            occupees.update((int(v["cmd"], 16), c2))
            cote2_v2[v["cmd"]] = L2
            ajouts.append(dict(genre="voix_v2", perso=v["perso"], id={"pl26": 0x26, "pl27": 0x27, "pl28": 0x2D, "pl29": 0x2E}[v["pl"]],
                               voix="v%02d" % v["n"], cmd=v["cmd"], cmd2=v["cmd2"], ech=v["ech"], entree=v["entree"],
                               hauteur=v["hauteur"], duree_note=v["duree_note"], prio=PRIO_PAS, voie=VOIE_PAS,
                               voie2=VOIE2_PAS, morceau=v["morceau"], morceau2=L2, prog=v["prog"]))

    # --- 1. cris
    for nom, (pl, base, roles) in CRIS.items():
        for n, vn in enumerate(roles):
            c = base + n
            a = dict(genre="cri", perso=nom, id=ID_PERSO[nom], role=n, cmd="%04X" % c, cmd2="%04X" % (c + 0x500))
            if vn is None:
                for x in (c, c + 0x500):
                    assert p0.cmd(x)[0] == 0 and x not in occupees; occupees.add(x)
                a.update(voix=None, muet=True); ajouts.append(a); continue
            v = v2[(pl, vn)]
            prio, voie, voie2 = ROLE[n]
            pst = piste(v["tempo"], G.VOLUME, v["prog"][0], v["prog"][1])
            if (prio, voie, voie2) == (PRIO_PAS, VOIE_PAS, VOIE2_PAS) or (not PAS_V2 and (prio, voie, voie2) == (G.PRIO, G.VOIE, G.VOIE)):
                L = v["morceau"]; L2 = cote2_v2.get(v["cmd"], L); a["morceau_v2"] = True
            else:
                L = range_morceau(morceau(prio, voie, pst))
                L2 = L if voie2 == voie else range_morceau(morceau(prio, voie2, pst))
                a["morceau_v2"] = False
            pose(c, L, L2)
            a.update(voix="v%02d" % vn, cmd_voix=v["cmd"], ech=v["ech"], entree=v["entree"], hauteur=v["hauteur"],
                     duree_note=v["duree_note"], prio=prio, voie=voie, voie2=voie2, morceau=L, morceau2=L2, prog=v["prog"])
            ajouts.append(a)
    # --- 2 et 3. échantillons neufs
    neufs = []
    for k, c in VOIX_INGRID:
        e = echantillon(os.path.join(PSP, "A_%03d.wav" % k), H)
        e.update(genre="voix_ingrid", perso="Ingrid", id=0x2E, source="A_%03d" % k, cmd="%04X" % c, cmd2="%04X" % (c + 0x500),
                 prio=PRIO_PAS, voie=VOIE_PAS, voie2=VOIE2_PAS, volume=G.VOLUME)
        neufs.append(e)
    code, c, f = SEQ_2C
    e = echantillon(f, H)
    e.update(genre="sequence", code_psp="$%02X" % code, source="se_mid seq 37 / I_016", cmd="%04X" % c,
             cmd2="%04X" % (c + 0x500), prio=PRIO_2C, voie=VOIE_2C, voie2=VOIE2_2C, volume=VOL_2C)
    neufs.append(e)
    # QSound : banques entières qu'aucune entrée de roms_voix ne référence (règle de gen_voix_max)
    ref, _ = G.zones_referencees(p0, z0)
    libres = G.zones_libres(q0, ref)
    journal("QSound : %d banques entières libres avant ajout : %s" % (len(libres), " ".join("%02X" % x[0] for x in libres)))
    for e in sorted(neufs, key=lambda e: -e["octets"]):
        for zl in libres:
            if zl[2] - zl[1] + 1 >= e["octets"]:
                bank, u0 = zl[0], zl[1]; zl[1] += e["octets"] + (-(e["octets"]) % 16); break
        else:
            raise SystemExit("plus de place dans la ROM QSound")
        u = np.arange(u0, u0 + e["octets"]); assert u[-1] <= 0xFFFF
        for i, o in enumerate((bank << 16) | (u ^ 0x8000)): q[o] = e["_data"][i]
        deb, fin = u0 ^ 0x8000, u[-1] ^ 0x8000
        e.update(adresse=(bank << 16) | deb, traverse_ffff=bool(deb > fin),
                 entree=(bytes([bank]) + struct.pack("<HHH", deb, (fin - 1) & 0xFFFF, fin) + bytes([e["param"]])).hex(" "))
    restant = [zl for zl in libres if zl[1] == 0]
    journal("QSound : %d banques entières encore libres après ajout (%d o)" % (len(restant), 0x10000 * len(restant)))
    # Z80 : programmes 29.. de NEWPT[22], puis entrées d'échantillons alignées sur $4975 + 8n
    tab = struct.unpack_from("<H", z, G.NEWPT + 2 * NT_INGRID)[0]
    n_ing = sum(1 for v in att if v["pl"] == "pl29")
    a_prog = tab + 4 * n_ing
    n0 = -(-(a_prog + 4 * len(neufs) - G.TECH) // 8)
    a_ech = G.TECH + 8 * n0
    a_fin = a_ech + 8 * len(neufs)
    assert a_prog == 0x77D5 and z[a_prog:a_fin] == bytes(a_fin - a_prog) and a_fin <= G.FIXE_FIN, "zone fixe"
    for i, e in enumerate(neufs):
        e["ech"] = n0 + i; e["prog"] = (NT_INGRID, n_ing + i)
        z[G.TECH + 8 * e["ech"]:G.TECH + 8 * e["ech"] + 8] = bytes.fromhex(e["entree"])
        z[a_prog + 4 * i:a_prog + 4 * i + 4] = struct.pack("<H", e["ech"]) + b"\x00\x40"
        tt, dn = G.tempo_pour(e["duree"], z)
        e.update(tempo=tt, duree_note=round(dn, 3))
        pst = piste(tt, e["volume"], NT_INGRID, n_ing + i)
        L = range_morceau(morceau(e["prio"], e["voie"], pst))
        L2 = L if e["voie2"] == e["voie"] else range_morceau(morceau(e["prio"], e["voie2"], pst))
        e["morceau"], e["morceau2"] = L, L2
        pose(int(e["cmd"], 16), L, L2)
        ajouts.append(e)
    journal("Z80 : %d programmes NEWPT[%d] %d-%d ($%04X-$%04X), %d entrées d'échantillons %d-%d ($%04X-$%04X), "
            "morceaux 0x%05X-0x%05X" % (len(neufs), NT_INGRID, n_ing, n_ing + len(neufs) - 1, a_prog, a_prog + 4 * len(neufs) - 1,
            len(neufs), n0, n0 + len(neufs) - 1, a_ech, a_fin - 1, MORC_DEB, reg - 1))
    # existante pour $0D : vérifier qu'elle existe des deux côtés
    for code, c in SEQ_EXISTANTE.items():
        assert p0.cmd(c)[0] and p0.cmd(c + 0x500)[0]
        ajouts.append(dict(genre="sequence", code_psp="$%02X" % code, source="se_mid seq 10 / I_009", cmd="%04X" % c,
                           cmd2="%04X" % (c + 0x500), existante=True))
    return bytes(z), bytes(q), ajouts, occupees, ref


def verifie(z0, q0, z, q, ajouts, occupees, ref, journal=print):
    p0, p = G.pilote(z0), G.pilote(z)
    ok = diff = 0
    for c in range(0xC00):
        if c in occupees: continue
        if p0.resolution(c) == p.resolution(c): ok += 1
        else: diff += 1; journal("  DIFFERENCE %04X" % c)
    journal("vérification statique : %d commandes de roms_voix identiques, %d différentes" % (ok, diff))
    nb = 0
    for a in ajouts:
        if a.get("existante") or a.get("muet"): continue
        for c, vo in ((int(a["cmd"], 16), a["voie"]), (int(a["cmd2"], 16), a["voie2"])):
            r = p.resolution(c)
            e = [t for t in r if t[0] == "08"]
            voies = [t[1] for t in r if t[0] == "piste" and t[2] is None]
            assert r[0] == ("prio", a["prio"]) and len(e) == 1 and e[0][3] == bytes.fromhex(a["entree"]), "%04X" % c
            assert vo not in voies and len(voies) == 15, "%04X voie" % c
            nb += 1
    for a in ajouts:
        if a.get("muet"):
            assert p.cmd(int(a["cmd"], 16))[0] == 0 and p.cmd(int(a["cmd2"], 16))[0] == 0
    journal("ajouts : %d commandes résolues vers leur échantillon (priorité et voie conformes)" % nb)
    for a, b in ref:
        assert q[a:b + 1] == q0[a:b + 1], "zone référencée 0x%06X modifiée" % a
    assert z[:0x3800] == z0[:0x3800], "code du pilote modifié"
    chg = sum(1 for k in range(len(z0)) if z0[k] != z[k])
    chq = sum(1 for k in range(len(q0)) if q0[k] != q[k])
    journal("QSound : zones référencées intactes (%d octets écrits ailleurs) ; Z80 : %d octets changés" % (chq, chg))
    return diff == 0


def ecrit(out, z, q, ajouts):
    os.makedirs(out, exist_ok=True)
    roms = {"hx3.01": z[0:0x8000] + z[0x10000:0x28000], "hx3.02": z[0x28000:0x50000]}
    for k, n in enumerate(("hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m")):
        b = q[0x400000 * k:0x400000 * (k + 1)]
        s = bytearray(len(b)); s[0::2] = b[1::2]; s[1::2] = b[0::2]; roms[n] = bytes(s)
    lignes = []
    for n, d in roms.items():
        open(os.path.join(out, n), "wb").write(d)
        lignes.append("%s  %s  CRC %08x  SHA1 %s" % (hashlib.md5(d).hexdigest(), n, zlib.crc32(d), hashlib.sha1(d).hexdigest()))
    open(os.path.join(out, "z80_son_max.bin"), "wb").write(z)
    lignes.append("%s  z80_son_max.bin" % hashlib.md5(z).hexdigest())
    open(os.path.join(out, "md5.txt"), "w").write("\n".join(lignes) + "\n")
    att = [{k: v for k, v in a.items() if not k.startswith("_")} for a in ajouts]
    json.dump(att, open(os.path.join(out, "attribution.json"), "w"), indent=1, ensure_ascii=False)
    # zones QSound écrites (pour le tap de lecture de la non-régression) : « début fin nom » en décimal
    with open(os.path.join(out, "zones.txt"), "w") as f:
        for a in ajouts:
            if "octets" in a:
                e = bytes.fromhex(a["entree"]); bank = e[0]; deb = e[1] | e[2] << 8
                u0 = deb ^ 0x8000
                for x0, x1 in ([(u0, u0 + a["octets"] - 1)]):
                    # ordre signé : u -> adresse physique ; au plus 2 morceaux
                    pa = [(bank << 16) | (u ^ 0x8000) for u in (x0, min(x1, 0x7FFF))] if x0 <= 0x7FFF else []
                    if x0 <= 0x7FFF: f.write("%d %d %s\n" % (pa[0], pa[1], a["cmd"]))
                    if x1 >= 0x8000:
                        f.write("%d %d %s\n" % ((bank << 16) | (max(x0, 0x8000) ^ 0x8000), (bank << 16) | (x1 ^ 0x8000), a["cmd"]))
    for l in lignes: print(l)


def ecrit_equ(f, ajouts):
    L = ["; Commandes QSound ajoutées pour les persos MAX (agent_son_max/gen_son_max.py ; ROM son roms_son_max/ = roms_voix v2",
         "; + cris + voix d'Ingrid A_095-A_103 + séquence $2C). Côté 2 = commande + $500 (ajouté par $3938, présent dans le Z80).",
         "; Exige HSFA_SON=<...>/agent_son_max/roms_son_max (sinon : commandes vides, muettes).",
         ";", "; 1. Bases de cris par perso (mot à poser dans la table PS2 0x613490[ID], agrandie à 48 ; cri = base + n) :"]
    for nom, (pl, base, roles) in CRIS.items():
        L.append("CRI_BASE_%02X equ $%04x    ; %s : n0..8 = %s" % (ID_PERSO[nom], base, nom,
                 " ".join("v%02d" % v if v is not None else "--" for v in roles)))
    L.append(";"); L.append("; 2. Voix propres d'Ingrid (se_mid banque A, codes PSP $447-$44F) :")
    for a in ajouts:
        if a["genre"] == "voix_ingrid":
            L.append("CMD_VOIX_29_%s equ $%s    ; %.2f s, %d Hz -> %d Hz" % (a["source"], a["cmd"].lower(), a["duree"], a["fr_orig"], round(a["fr_qs"])))
    L.append(";"); L.append("; 3. Séquences MIDI de se_mid (type $100) :")
    for a in ajouts:
        if a["genre"] == "sequence":
            L.append("CMD_SEQ_%s equ $%s    ; %s%s" % (a["code_psp"][1:], a["cmd"].lower(), a["source"],
                     " = bruitage arcade existant (appariement fort)" if a.get("existante") else " importée (sans équivalent arcade)"))
    open(f, "w").write("\n".join(L) + "\n")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "roms_son_max_pas")
    z0, q0, att = lit_v2()
    zr, qr = bytes(z0), bytes(q0)                 # copies intactes de roms_voix (construit écrit dans z0/q0)
    z, q, ajouts, occ, ref = construit(z0, q0, att)
    assert verifie(zr, qr, z, q, ajouts, occ, ref)
    ecrit(out, z, q, ajouts)
    ecrit_equ(os.path.join(os.environ.get("SON_MAX_EQU", ICI), "commandes_son_max.s"), ajouts)
    tot = sum(a.get("octets", 0) for a in ajouts)
    print("ajouts : %d commandes (x2 côtés), %d o de QSound (%.2f Mo) ; écrit dans %s" % (len(ajouts), tot, tot / 2 ** 20, out))


if __name__ == "__main__":
    main()
