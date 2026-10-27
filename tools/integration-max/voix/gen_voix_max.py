#!<workspace>/venv/bin/python
"""Voix des 4 persos MAX (Eagle pl26, Maki pl27, Yun pl28, Ingrid pl29) ajoutees a une COPIE de la ROM son hybride
d'Upper (agent_son_ro5/hybride/roms_hybride/hx3.*, option C du §127). La ROM hybride n'est jamais modifiee.

Pilote Z80 (Capcom CPS2, cf. agent_son_ro5/hybride/RAPPORT-option-C.md et VOIX-MAX.md) :
  - commande c -> table des commandes (lineaire $8C06 + 4 (c mod $C00)) : pointeur 24 bits BE du morceau + 1 o ;
  - morceau : priorite + 16 decalages BE relatifs (une piste par voie d'effet) ; les voix de SFA3/Upper sont en
    priorite $0A, voie 11, piste « 05 TT 06 FF 07 VV 1F NN 08 II 09 03 B9 17 » :
      05 TT = tempo (table $3492 : mot ~ 3,27 (TT+1)) -> duree de la note B9 (0x30 tics) = 196,6 / tempo(TT) s,
      07 VV = volume (table $2E92 ; $6A, cf. VOLUME), 1F NN = table de programmes NEWPT[NN],
      08 II = programme II (4 o : echantillon LE16, $00, enveloppe $40), 09 03 = octave 3, B9 = note (72) ;
  - echantillon n : entree tabech ($4975) + 8n : banque, debut LE16, boucle LE16, fin LE16, parametre ;
    hauteur QSound = TABLE_HAUTEUR[48 + 72 - parametre] (Z80 $21BA ; $48 -> $0800), frequence de lecture =
    24 038,46 Hz x hauteur / $1000 (QSound : 60 MHz / 2 / 1248) ;
  - QSound : PCM 8 bits signe, adresse = banque << 16 | adresse 16 bits ; le DSP compare debut/fin en 16 bits SIGNES :
    un echantillon tient dans une banque et ne traverse pas $7FFF -> $8000 (mais peut passer $FFFF -> $0000 : il est
    alors range en $8000-$FFFF puis $0000-..., 64 Ko au plus) ; boucle de 1 octet nul en fin (comme les voix d'Upper).
  - cote 2 : le 68K ($3938) ajoute $500 a la commande -> chaque voix a DEUX commandes (c et c + $500), meme morceau
    (SFA3 : 03xx/08xx, voies identiques).

Construction :
  1. Z80 : entrees d'echantillons 1283.. ($718D.., zone fixe libre, a la suite de l'hybride), 4 tables de programmes
     (une par perso, NEWPT[19..22]), 134 morceaux (en-tete + piste) en banque 15 libre (region 0x4C600..), entrees de
     la table des commandes (c et c + $500) ;
  2. QSound : chaque voix -> reechantillonnage (sinc fenetre de Kaiser) a la frequence de la hauteur choisie (la plus
     petite >= frequence d'origine ; plus basse si la voix ne tient pas dans 64 Ko), normalisation de crete prudente
     (crete 124/127, gain <= 4), 8 bits signes ; place : banques de 64 Ko ENTIERES jamais referencees par l'hybride
     (fin nulle de e389 : $7D-$7F ; e288 : banques dont aucune entree d'echantillon ne se sert), cf. zones_libres() ;
  3. verification statique : les 3 072 commandes de l'hybride donnent le meme contenu resolu qu'avant (sauf les
     commandes ajoutees, auparavant vides), les octets QSound references par l'hybride sont intacts, chaque nouvelle
     commande resout vers sa voix.

Sorties (dossier, defaut ./roms_voix/) : hx3.01, hx3.02, hx3.11m..hx3.14m (format de gen_hybride.py, chargees par
le fork avec HSFA_SON=<dossier>), z80_voix.bin (image audiocpu), md5.txt, attribution.json (commande, echantillon,
adresse, hauteur...), commandes_voix_max.s (un equ par echantillon).
Usage : gen_voix_max.py [dossier_sortie]
"""
import os, sys, json, wave, struct, hashlib, zlib, csv
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
HYB = "<workspace>/work/agent_son_ro5/hybride"
sys.path.insert(0, HYB); sys.path.insert(0, os.path.dirname(HYB))
from gen_hybride import Pilote, NEWPT          # lecture du pilote (resolution des commandes)
from z80son import lin2reg

BASE = os.path.join(HYB, "roms_hybride")
VOIX = os.path.expanduser("~/.cache/sfa3max/converti")
PS2 = "<workspace>/work/agent_hyper_son/table_son_ro9.csv"   # identique ro3/ro5 (SON-HYPER.md §0.2)
PERSOS = [("pl26", 26, "Eagle"), ("pl27", 27, "Maki"), ("pl28", 28, "Yun"), ("pl29", 29, "Ingrid")]
QS_HZ = 60e6 / 2 / 1248                        # frequence de sortie du QSound (24 038,46 Hz)
TAB_HAUTEUR = 0x21BA                           # Z80 : 108 mots LE (demi-tons ; indice 48 = $0800)
TAB_TEMPO = 0x3492                             # Z80 : mots LE (op 05)
TECH = 0x4975                                  # table des echantillons d'Upper
N0_ECH = 1283                                  # premier numero libre (hybride : 1169-1282 ; $4975 + 8 x 1283 = $718D)
FIXE_FIN = 0x7975                              # entree « sentinelle » de l'hybride ($7975-$797C) : ne pas atteindre
NT_BASE = 19                                   # NEWPT[19..22] : tables de programmes MAX (hybride : 0-18)
MORC_REG = 0x4C600                             # region audiocpu : morceaux (banque 15, apres les musiques 0x4C5FC)
MORC_FIN = 0x50000
PRIO, VOIE = 0x0A, 11                          # comme les voix de SFA3 / Upper (priorite $0A : 52 voix sur 82, $0B : 30)
VOLUME = 0x6A                                  # op 07 : niveau (echantillon x table $2E92) median = celui des 82 voix
                                               # SFA3/Upper (les voix MAX sont normalisees plus fort : RMS 8 bits ~38 contre ~24)
NOTE, OCTAVE, PARAM_REF = 0xB9, 3, 0x48        # note 72 ; parametre 72 -> hauteur $0800
CRETE, GAIN_MAX = 124, 4.0

# numeros de commande (cote 1 ; cote 2 = +$500), choisis par trous_commandes() et figes ici (cf. VOIX-MAX.md §2)
ATTRIBUTION = {   # renumerotation du 2026-10-10 (VOIX-MAX.md §9) : paires libres dans SFA3, Upper ET Hyper (numeros.py),
                  # pages 02-06 hors bloc de Cammy ALPHA ($0540-$055F), entree PS2 vide ou de perso, ordre des adresses
    "pl26": [(0x0246, 0x024B), (0x027E, 0x027F), (0x02A4, 0x02A9), (0x02B4, 0x02C0), (0x02FD, 0x02FE)],   # 29
    "pl27": [(0x02FF, 0x02FF), (0x0314, 0x031F), (0x033B, 0x033F), (0x0354, 0x035F), (0x0376, 0x037E)],   # 39
    "pl28": [(0x037F, 0x037F), (0x039B, 0x039F), (0x03B7, 0x03BF), (0x03D9, 0x03DF), (0x03F7, 0x03FF), (0x041E, 0x041E),
             (0x045B, 0x045F)],   # 37
    "pl29": [(0x047B, 0x047F), (0x051A, 0x051F), (0x0533, 0x0536), (0x057E, 0x057F), (0x05B9, 0x05BF), (0x05F9, 0x05FD)],   # 29
}
LIBRES = os.path.join(ICI, "numeros_libres.json")   # ecrit par numeros.py (criteres des trois jeux)


def lit_base(d):
    z1 = open(os.path.join(d, "hx3.01"), "rb").read(); z2 = open(os.path.join(d, "hx3.02"), "rb").read()
    assert len(z1) == 0x20000 and len(z2) == 0x28000
    z = bytearray(0x50000)
    z[0:0x8000] = z1[:0x8000]; z[0x10000:0x28000] = z1[0x8000:]; z[0x28000:0x50000] = z2
    q = bytearray()
    for n in ("hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m"):
        b = open(os.path.join(d, n), "rb").read(); assert len(b) == 0x400000
        s = bytearray(len(b)); s[0::2] = b[1::2]; s[1::2] = b[0::2]; q += s
    ref = os.path.join(d, "z80_hybride.bin")
    if os.path.exists(ref): assert open(ref, "rb").read() == bytes(z), "hx3.01/02 != z80_hybride.bin"
    return z, q


def pilote(z):
    p = Pilote(bytes(z), 0x3800, NEWPT, 0x6305); p.pt_mus = NEWPT + 32
    return p


def table_ps2():
    return {int(r["cmd"], 16): r["genre"] for r in csv.DictReader(open(PS2))}


def trous_commandes(p, ps2):
    """paires (c, c + $500) vides dans le Z80 ; classe : 'libre' (aussi vide dans la table PS2), 'remplissage'
    (PS2 = programme de perso mecanique, cf. VOIX-MAX.md), sinon exclu (musique ADX, banque commune)."""
    out = {}
    for c in range(0x700):
        if p.cmd(c)[0] or p.cmd(c + 0x500)[0]: continue
        g = (ps2[c], ps2[c + 0x500])
        if g == ("-", "-"): out[c] = "libre"
        elif all(x in ("-", "SPU2perso") for x in g): out[c] = "remplissage"
    return out


def commandes_vues():
    """commandes envoyees par le 68K dans les journaux des agents (SFA3, Upper, Hyper) : a ne pas prendre"""
    vues = set()
    import glob, re
    for f in glob.glob("<workspace>/work/agent_son_ro5/journaux/*.txt") + \
             glob.glob("<workspace>/work/agent_son_ro5/hybride/journaux/*.txt"):
        for l in open(f, errors="replace"):
            if l.startswith("C "):
                t = l.split()
                if len(t) >= 3 and len(t[2]) == 4: vues.add(int(t[2], 16))
    for f in glob.glob("<workspace>/work/agent_hyper_son/essais/*.son"):
        for m in re.finditer(r"cmd ([0-9a-f]{4})", open(f, errors="replace").read()): vues.add(int(m.group(1), 16))
    return vues


def zones_referencees(p, z):
    """intervalles QSound [a, b] lus par l'hybride : echantillons resolus des 3 072 commandes + toutes les entrees
    des plages de la table (Upper 0-817, hybride 1169-1282, sentinelle $600) + entree $7F00 (sentinelle des effets)"""
    ents = set()
    for c in range(0xC00):
        r = p.resolution(c)
        if r:
            for t in r:
                if t[0] == "08": ents.add(t[3])
    for n in list(range(0, 818)) + list(range(1169, 1283)) + [0x600, 0x7F00]:
        ents.add(p.echantillon(n))
    zr = []
    for e in ents:
        b = (e[0] & 0x7f) | (0x80 if e[0] & 0x80 else 0)
        s, l, f = struct.unpack("<HHH", e[1:7])
        if s == l == f == 0 and e[0] == 0: continue
        a = (e[0] & 0xff) << 16
        lo, hi = min(s, l, f), max(s, l, f)
        zr.append((a + lo, a + hi))
    zr.sort()
    m = []
    for a, b in zr:
        if m and a <= m[-1][1] + 1: m[-1][1] = max(m[-1][1], b)
        else: m.append([a, b])
    return m, ents


def zones_libres(q, ref):
    """banques QSound de 64 Ko ENTIERES qu'aucune entree d'echantillon de l'hybride ne reference (fin nulle de e389 :
    $7D-$7F ; e288 : banques sans donnees utilisees). Pourquoi des banques entieres : quand le Z80 change d'echantillon
    sur une voie, il ecrit le debut AVANT la banque ; le DSP lit alors quelques octets a (ancienne banque, nouveau
    debut) (vu par tap de lecture sur la musique 0006 : a7defb). Toute banque deja utilisee peut donc etre lue hors des
    plages des entrees ; une banque jamais utilisee ne l'est que par une voix MAX (ou juste apres, sur la voie 11).
    Ordre SIGNE u = adresse ^ $8000 : le DSP compare debut/fin en 16 bits signes (un echantillon ne peut pas traverser
    $7FFF -> $8000 mais peut passer $FFFF -> $0000 ; cf. VOIX-MAX.md). Renvoie des [banque, u_debut, u_fin]."""
    utilisees = set()
    for a, b in ref:
        utilisees.update(range(a >> 16, (b >> 16) + 1))
    fin_bas = max(i for i in range(0x7C0000, 0x800000) if q[i]) + 1
    out = []
    for bank in range(0x7C, 0x100):
        if bank in utilisees or (bank << 16) < fin_bas: continue
        assert bank >= 0x80 or not any(q[bank << 16:(bank + 1) << 16]), "banque basse non nulle"
        out.append([bank, 0, 0xFFFF])
    return out


def reechantillonne(x, fin, fout, demi=32, beta=8.6):
    """sinc fenetre (Kaiser) a rapport quelconque ; coupure a 0,95 x min(Nyquist)"""
    r = fout / fin
    n = int(np.floor(len(x) * r))
    t = np.arange(n) / r
    fc = 0.95 * min(1.0, r)
    k0 = np.floor(t).astype(int)
    y = np.zeros(n)
    w = np.kaiser(2 * demi + 1, beta)
    xp = np.concatenate([np.zeros(demi + 1), x, np.zeros(demi + 2)])
    for j in range(-demi, demi + 1):
        idx = k0 + j
        d = t - idx
        h = fc * np.sinc(fc * d) * np.interp(d, np.arange(-demi, demi + 1), w, left=0, right=0)
        y += xp[idx + demi + 1] * h
    return y


def lit_wav(f):
    w = wave.open(f)
    assert w.getnchannels() == 1 and w.getsampwidth() == 2
    return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768.0, w.getframerate()


def hauteurs(z):
    return [struct.unpack_from("<H", z, TAB_HAUTEUR + 2 * i)[0] for i in range(108)]


def choix_param(fr, nech, H):
    """parametre (hauteur) : plus petite frequence >= fr qui tienne en 64 Ko (sinon la plus haute qui tienne)"""
    best = None
    for idx in range(30, 61):
        f = QS_HZ * H[idx] / 4096
        long = int(nech * f / fr) + 16
        if long > 0xFFFF: continue
        if f >= fr * 0.995: return 120 - idx, f
        best = (120 - idx, f)
    assert best, "voix trop longue"
    return best


def tempo_pour(duree, z):
    """plus grand indice TT (note la plus courte) dont la duree 196,6/tempo >= duree + 30 ms"""
    T = [struct.unpack_from("<H", z, TAB_TEMPO + 2 * i)[0] for i in range(256)]
    ok = [i for i in range(256) if T[i] and 0x30 * 1024 / 250.0 / T[i] >= duree + 0.03]
    return max(ok), 0x30 * 1024 / 250.0 / T[max(ok)]


def construit(z, q, journal=print):
    z = bytearray(z); q = bytearray(q)
    p0 = pilote(z)
    ps2 = table_ps2()
    trous = trous_commandes(p0, ps2)
    vues = commandes_vues()
    libres_3jeux = set(json.load(open(LIBRES))["libres"])
    H = hauteurs(z)
    ref, _ = zones_referencees(p0, z)
    libres = zones_libres(q, ref)
    journal("QSound : %d banques entieres jamais referencees (%d o) : %s" % (len(libres), sum(b - a + 1 for _, a, b in libres),
            " ".join("%02X" % x[0] for x in libres)))
    # --- voix
    voix = []
    for pl, num, nom in PERSOS:
        js = json.load(open(os.path.join(VOIX, pl, "voix", "voix.json")))
        ech = [e for e in js["echantillons"] if not e.get("vide")]
        cmds = [c for a, b in ATTRIBUTION[pl] for c in range(a, b + 1)]
        assert len(cmds) == len(ech), (pl, len(cmds), len(ech))
        for e, c in zip(ech, cmds):
            assert trous.get(c) in ("libre", "remplissage"), "%04X non libre" % c
            assert "%04X" % c in libres_3jeux, "%04X : pas libre dans les trois jeux (numeros.py)" % c
            assert c not in vues and c + 0x500 not in vues, "%04X envoyee par un jeu" % c
            voix.append(dict(pl=pl, perso=nom, num=num, n=e["n"], cmd=c, cmd2=c + 0x500,
                             wav=os.path.join(VOIX, pl, "voix", "v%02d.wav" % e["n"])))
    assert len(set(v["cmd"] for v in voix)) == len(voix)
    # --- echantillons QSound : conversion puis placement (plus grands d'abord, premiere zone qui convient)
    for v in voix:
        x, fr = lit_wav(v["wav"])
        prm, f = choix_param(fr, len(x), H)
        y = reechantillonne(x, fr, f) if abs(f - fr) > 0.5 else x.copy()
        pic = np.abs(y).max()
        g = min(GAIN_MAX, CRETE / 127.0 / pic) if pic > 0 else 1.0
        s8 = np.clip(np.round(y * g * 127.0), -128, 127).astype(np.int8)
        # fondu de 2 ms aux deux bouts (pas de clic) puis 16 octets nuls (boucle de 1 octet sur un zero)
        nf = max(1, int(0.002 * f)); s8[:nf] = np.round(s8[:nf] * np.linspace(0, 1, nf)).astype(np.int8)
        s8[-nf:] = np.round(s8[-nf:] * np.linspace(1, 0, nf)).astype(np.int8)
        data = s8.tobytes() + bytes(16)
        v.update(fr_orig=fr, param=prm, fr_qs=round(f, 2), hauteur=H[120 - prm], gain=round(g, 3), octets=len(data),
                 duree=round(len(s8) / f, 3), rms8=round(float(np.sqrt(np.mean(s8.astype(float) ** 2))), 1),
                 _data=data)
    for v in sorted(voix, key=lambda v: -v["octets"]):
        for zl in libres:
            if zl[2] - zl[1] + 1 >= v["octets"]:
                bank, u0 = zl[0], zl[1]; zl[1] += v["octets"] + (-(v["octets"]) % 16)
                break
        else:
            raise SystemExit("plus de place dans la ROM QSound")
        u = np.arange(u0, u0 + v["octets"])
        assert u[-1] <= 0xFFFF
        phys = (bank << 16) | (u ^ 0x8000)
        for i, o in enumerate(phys): q[o] = v["_data"][i]
        deb, fin = u0 ^ 0x8000, u[-1] ^ 0x8000
        v["adresse"] = (bank << 16) | deb
        v["traverse_ffff"] = bool(deb > fin)
        v["entree"] = bytes([bank]) + struct.pack("<HHH", deb, (fin - 1) & 0xFFFF, fin) + bytes([v["param"]])
    # --- Z80 : entrees d'echantillons, tables de programmes, morceaux, table des commandes
    a_ech = TECH + 8 * N0_ECH
    a_prog = a_ech + 8 * len(voix)
    a_fin = a_prog + 4 * len(voix)
    assert a_ech == 0x718D and a_fin <= FIXE_FIN and z[a_ech:a_fin] == bytes(a_fin - a_ech), "zone fixe non libre"
    assert z[NEWPT + 2 * NT_BASE:NEWPT + 2 * (NT_BASE + 4)] == bytes(8), "NEWPT[19..22] non libre"
    assert z[MORC_REG:MORC_FIN] == bytes(MORC_FIN - MORC_REG), "banque 15 non libre"
    reg = MORC_REG
    tables = {}
    for k, (pl, num, nom) in enumerate(PERSOS):
        vs = [v for v in voix if v["pl"] == pl]
        assert len(vs) <= 128
        tables[pl] = (NT_BASE + k, a_prog)
        struct.pack_into("<H", z, NEWPT + 2 * (NT_BASE + k), a_prog)
        for i, v in enumerate(vs):
            v["ech"] = N0_ECH + voix.index(v)
            z[TECH + 8 * v["ech"]:TECH + 8 * v["ech"] + 8] = v["entree"]
            z[a_prog + 4 * i:a_prog + 4 * i + 4] = struct.pack("<H", v["ech"]) + b"\x00\x40"
            v["prog"] = (NT_BASE + k, i)
            tt, dn = tempo_pour(v["duree"], z)
            v["tempo"], v["duree_note"] = tt, round(dn, 3)
            piste = bytes([0x05, tt, 0x06, 0xFF, 0x07, VOLUME, 0x1F, NT_BASE + k, 0x08, i, 0x09, OCTAVE, NOTE, 0x17])
            ent = bytearray(33); ent[0] = PRIO
            struct.pack_into(">H", ent, 1 + 2 * VOIE, 33)
            m = bytes(ent) + piste
            if (reg & 0x3FFF) + len(m) > 0x4000: reg = (reg | 0x3FFF) + 1      # pas de morceau a cheval sur 2 banques
            assert reg + len(m) <= MORC_FIN
            z[reg:reg + len(m)] = m
            L = reg - 0x8000                                                    # adresse lineaire du pilote
            v["morceau"] = L
            for c in (v["cmd"], v["cmd2"]):
                _, Lc = p0.cmd(c); r = lin2reg(Lc)
                assert z[r:r + 4] == bytes(4)
                z[r:r + 4] = bytes([L >> 16, (L >> 8) & 0xff, L & 0xff, 0])
            reg += len(m)
        a_prog += 4 * len(vs)
    journal("Z80 : %d entrees d'echantillons %d-%d ($%04X-$%04X), tables de programmes NEWPT[%d-%d] ($%04X-$%04X), "
            "morceaux region 0x%05X-0x%05X (%d o)" % (len(voix), N0_ECH, N0_ECH + len(voix) - 1, a_ech, a_ech + 8 * len(voix) - 1,
            NT_BASE, NT_BASE + 3, a_ech + 8 * len(voix), a_fin - 1, MORC_REG, reg - 1, reg - MORC_REG))
    return bytes(z), bytes(q), voix, ref


def verifie(z0, q0, z, q, voix, ref, journal=print):
    p0, p = pilote(z0), pilote(z)
    nouv = set(v["cmd"] for v in voix) | set(v["cmd2"] for v in voix)
    ok = diff = 0
    for c in range(0xC00):
        if c in nouv:
            assert p0.cmd(c)[0] == 0
            continue
        if p0.resolution(c) == p.resolution(c): ok += 1
        else: diff += 1; journal("  DIFFERENCE %04X" % c)
    journal("verification statique : %d commandes anciennes identiques, %d differentes" % (ok, diff))
    for v in voix:
        for c in (v["cmd"], v["cmd2"]):
            r = p.resolution(c)
            e = [t for t in r if t[0] == "08"]
            assert r[0] == ("prio", PRIO) and len(e) == 1 and e[0][3] == v["entree"], "%04X" % c
    journal("nouvelles commandes : %d x 2 resolues vers leur echantillon" % len(voix))
    for a, b in ref:
        assert q[a:b + 1] == q0[a:b + 1], "zone referencee 0x%06X modifiee" % a
    chg = [k for k in range(0, len(z0)) if z0[k] != z[k]]
    journal("QSound : zones referencees intactes ; Z80 : %d octets changes" % len(chg))
    assert z[:0x3800] == z0[:0x3800], "code du pilote modifie"
    return diff == 0


def ecrit(out, z, q, voix, journal=print):
    os.makedirs(out, exist_ok=True)
    roms = {"hx3.01": z[0:0x8000] + z[0x10000:0x28000], "hx3.02": z[0x28000:0x50000]}
    for k, n in enumerate(("hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m")):
        b = q[0x400000 * k:0x400000 * (k + 1)]
        s = bytearray(len(b)); s[0::2] = b[1::2]; s[1::2] = b[0::2]; roms[n] = bytes(s)
    lignes = []
    for n, d in roms.items():
        open(os.path.join(out, n), "wb").write(d)
        lignes.append("%s  %s  CRC %08x  SHA1 %s" % (hashlib.md5(d).hexdigest(), n, zlib.crc32(d), hashlib.sha1(d).hexdigest()))
    open(os.path.join(out, "z80_voix.bin"), "wb").write(z)
    lignes.append("%s  z80_voix.bin" % hashlib.md5(z).hexdigest())
    open(os.path.join(out, "md5.txt"), "w").write("\n".join(lignes) + "\n")
    for l in lignes: journal(l)
    att = [{k: (("%04X" % x) if k in ("cmd", "cmd2") else x) for k, x in v.items() if not k.startswith("_") and k != "entree"}
           | {"entree": v["entree"].hex(" ")} for v in voix]
    json.dump(att, open(os.path.join(out, "attribution.json"), "w"), indent=1, ensure_ascii=False)


def ecrit_equ(f, voix):
    L = ["; Commandes QSound des voix MAX (agent_voix_max/gen_voix_max.py, ROM son roms_voix/ = hybride d'Upper + voix MAX).",
         "; UNE commande par echantillon (sons/voix_max.py : plXX/voix/vNN.wav) ; cote 2 = commande + $500 (ajoute par $3938,",
         "; aussi present dans le Z80). Exige HSFA_SON=<...>/agent_voix_max/roms_voix (sinon muet : entrees vides)."]
    for v in voix:
        L.append("CMD_VOIX_%d_E%02d equ $%04x    ; %s v%02d.wav, %.2f s, %d Hz -> %d Hz" % (
            v["num"], v["n"], v["cmd"], v["perso"], v["n"], v["duree"], v["fr_orig"], round(v["fr_qs"])))
    open(f, "w").write("\n".join(L) + "\n")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "roms_voix")
    z0, q0 = lit_base(BASE)
    z, q, voix, ref = construit(z0, q0)
    assert verifie(z0, q0, z, q, voix, ref)
    ecrit(out, z, q, voix)
    ecrit_equ(os.path.join(ICI, "commandes_voix_max.s"), voix)
    tot = sum(v["octets"] for v in voix)
    print("voix : %d, %d o de QSound (%.2f Mo) ; ecrit dans %s" % (len(voix), tot, tot / 2 ** 20, out))


if __name__ == "__main__":
    main()
