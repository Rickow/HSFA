#!/usr/bin/env python3
"""sons_ps2.py : SONS PROPRES AU PORTAGE PS2 d'Hyper, absents de tout Z80 CPS2, ajoutés à une COPIE de la ROM son
hybride (ticket public n° 1 : « No Parry sound effect in B-ISM »).

Constat (docs/rapports/SONS-PS2-HYPER.md) : le 68K d'Hyper envoie des commandes son dont l'entrée de la table native PS2 (0x5CB300) mène à un
échantillon SPU2 que la SPU2 joue, mais qui sont VIDES dans le Z80 (SFA3, Upper, hybride) : le cœur et le banc restent
muets. Inventaire (jeu, table « par pas », immédiats) : parade de la Mazi S-ISM 027C/077C, 0245, activation du custom
combo (ZERO 2 / ALPHA) 027D, Birdie 040F/041F, Sagat en Saikyo S-ISM 047A, Cammy ALPHA (14 sons), Dee Jay 057D.
Le pilote PS2 lit l'indice o4 dans la TABLE SE du conteneur MOMO de la banque (4e partie) : indice -> programme +
touche -> Sset -> VAG (ce n'est PAS le n° de Sset : e344 décale de 5, e314 de +8 pour l'indice 7).

Ajout (rien d'autre ne change ; vérifié par l'outil : contenu résolu des autres commandes identique, zones QSound
référencées intactes, pilote intact) :
  - QSound : chaque échantillon, décodé depuis le X_DATA.BIN de l'utilisateur (aucune donnée dans le dépôt), lu au taux
    mesuré sur la SPU2 (natif ; parade : une octave plus bas), rééchantillonné à la hauteur QSound, 8 bits signés, dans
    des banques jamais référencées par l'hybride ni par les voix MAX (BANQUES, de $FF vers le bas) ;
  - Z80 : entrées d'échantillon 1535 et suivantes en descendant, une table de programmes en $7F80 (NEWPT[23]), deux
    morceaux par son en banque 15 (région 0x4F400 et suivantes), entrées des commandes (côté 1 et côté 2 = +$500),
    priorité et piste de la commande voisine ; volume (op 07) calibré sur le niveau PS2 (VOLUMES).
Interrupteur : HSFA_SONS_PS2=0 (ou HSFA_PARADE=0) -> ROM de base recopiée telle quelle (md5 identiques) ;
HSFA_SONS_PS2=nom1,nom2 -> seulement ces sons (noms de SONS_SPEC).

Usage : sons_ps2.py --base DOSSIER_HX3 --xdata X_DATA.BIN --manifeste manifest.csv --sortie DOSSIER [--journal F]
"""
import os, sys, struct, hashlib, zlib, argparse, shutil, wave
import numpy as np

DEPOT = os.environ.get("HSFA_DEPOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(DEPOT, "src", "hsfa")); sys.path.insert(0, os.path.join(DEPOT, "src"))
from gen_hybride import Pilote, NEWPT           # noqa: E402  (lecture du pilote, résolution des commandes)
from z80son import lin2reg                     # noqa: E402

ROMS = ("hx3.01", "hx3.02", "hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m")
QS_HZ = 60e6 / 2 / 1248                        # sortie QSound (24 038,46 Hz)
TAB_HAUTEUR, TAB_TEMPO, TECH = 0x21BA, 0x3492, 0x4975
N_ECH0 = 1535                                  # entrées d'échantillon 1535, 1534, … ($796D en descendant ; zone libre $77D5-$7974)
A_PROG = 0x7F80                                # table de programmes (4 o par son, 32 au plus) : $7F80-$7FFF (zone libre)
NT = 23                                        # NEWPT[23] ($6B3E) : dernier mot libre avant $6B40 (tables SFA3)
# banques QSound jamais référencées par l'hybride (règle prudente de gen_voix_max.py) et hors voix MAX (7D-D5), prises
# de la fin de la ROM vers le début ; l'outil vérifie qu'aucune n'est référencée par la ROM de base
BANQUES = (0xFF, 0xFD, 0xFC, 0xF7, 0xF5, 0xF2, 0xF1, 0xF0, 0xEF, 0xEE, 0xED, 0xEC, 0xEA, 0xE8, 0xE2)
MORC = 0x4F400                                 # région audiocpu (banque 15, zone libre 0x4DE9A-0x4FFFF) : morceaux de 47 o
NOTE, OCTAVE = 0xB9, 3
CRETE, GAIN_MAX = 124, 4.0
VOL_REF, G_REF = 0x10DF, 0.98                  # parade : op 07 $75 (table $2E92 = $10DF) pour un gain de conversion 0,98,
                                               # calibré au cœur contre 0703 (rapport PS2) ; autres sons : T(VV) ~ VOL_REF x G_REF / g
# Sons PS2 seuls : (nom, commandes côté 1, banque SCEI, indices o4 de la table native) ; côté 2 = +$500. Résolution
# comme le pilote PS2 : indice -> TABLE SE du conteneur MOMO (4e partie, 16 o : [0] actif, [5] volume, [8] programme,
# [9] touche - 12) -> zone du programme -> Sset -> VAG, lu au taux natif (pitch SPU2 mesuré : e345 VAG 2, 47, 89, 90,
# 91, e314/e315, e344 VAG 4/5/14), sauf la parade (VAG 92 lu une octave plus bas, pitch $03E3 mesuré). Priorité et piste :
# celles de la commande Z80 non vide la plus proche (même bloc de $20 d'abord). Indices d'émission : docs/rapports/SONS-PS2-HYPER.md §8.
SONS_SPEC = [
    ("parade", [0x027C], 345, [124], 48000.0 * 0x03E3 / 4096),     # Mazi S-ISM (bleue) : parade (jeu, PS2 mesuré)
    ("poussee", [0x0245], 345, [69], None),                        # envoi immédiat $8C0FA après une poussée de l'adversaire
    ("custom_combo", [0x027D], 345, [77], None),                   # ZERO 2 / ALPHA : activation du custom combo (jeu, PS2)
    ("birdie", [0x040F, 0x041F], 322, [15, 31], None),             # Birdie : table « par pas » ; 041F joué en Z / Z2 / A
    ("sagat_saikyo", [0x047A], 325, [26], None),                   # Sagat, Saikyo S-ISM (rose) (jeu)
    ("cammy_alpha", [0x0549, 0x054A, 0x054B, 0x054C, 0x054D, 0x054F, 0x0550, 0x0551, 0x0553, 0x0554, 0x0555, 0x0556,
                     0x055D, 0x055E], 344, [9, 10, 11, 12, 13, 15, 16, 17, 19, 20, 21, 22, 29, 30], None),   # Cammy ALPHA ($7E)
    ("dee_jay", [0x057D], 342, [29], None),                        # Dee Jay, toutes versions (jeu)
]


VOLUMES = {  # op 07 par commande (côté 2 identique), calibré au cœur (outils/calibre.py sur des rendus isolés) :
             # niveau / PCM PS2 = 0,0012 x o5 de la table native (références arcade = PS2 : 024F, 0703) ; 027D au plafond (-1 dB)
    0x0245: 0x71, 0x027D: 0x7F, 0x040F: 0x7F, 0x041F: 0x7E, 0x047A: 0x78, 0x0549: 0x7C, 0x054A: 0x7D, 0x054B: 0x7B,
    0x054C: 0x7C, 0x054D: 0x7C, 0x054F: 0x79, 0x0550: 0x77, 0x0551: 0x77, 0x0553: 0x7B, 0x0554: 0x7B, 0x0555: 0x78,
    0x0556: 0x7C, 0x055D: 0x78, 0x055E: 0x7D, 0x057D: 0x6E}


def lit_base(d):
    z1 = open(os.path.join(d, "hx3.01"), "rb").read(); z2 = open(os.path.join(d, "hx3.02"), "rb").read()
    assert len(z1) == 0x20000 and len(z2) == 0x28000
    z = bytearray(0x50000); z[0:0x8000] = z1[:0x8000]; z[0x10000:0x28000] = z1[0x8000:]; z[0x28000:0x50000] = z2
    q = bytearray()
    for n in ROMS[2:]:
        b = open(os.path.join(d, n), "rb").read(); assert len(b) == 0x400000
        s = bytearray(len(b)); s[0::2] = b[1::2]; s[1::2] = b[0::2]; q += s
    return z, q


def pilote(z):
    p = Pilote(bytes(z), 0x3800, NEWPT, 0x6305); p.pt_mus = NEWPT + 32
    return p


# ---------------------------------------------------------------- source : e345 (banque SCEI HD/BD, conteneur MOMO)
def fichier_xdata(xdata, manifeste, e):
    for l in open(manifeste, encoding="utf-8").read().splitlines()[1:]:
        i, off, n, kind, name = l.split(",", 4)
        if int(i) == e:
            with open(xdata, "rb") as f: f.seek(int(off)); return f.read(int(n))
    raise SystemExit("e%d absent du manifeste" % e)


def se_pcm(d, indice):
    """PCM et taux de l'échantillon que la SPU2 joue pour l'indice o4 (table SE -> programme -> Sset -> Smpl -> VAG)"""
    assert d[:4] == b"MOMO", "banque SCEI inattendue"
    o, n = struct.unpack_from("<II", d, 8); o2, n2 = struct.unpack_from("<II", d, 16); o4, n4 = struct.unpack_from("<II", d, 32)
    h, bd, se = d[o:o + n], d[o2:o2 + n2], d[o4:o4 + n4]
    def tab(tag):
        p = h.find(tag); mx = struct.unpack_from("<I", h, p + 12)[0]
        return [None if x == 0xFFFFFFFF else p + x for x in struct.unpack_from("<%dI" % (mx + 1), h, p + 16)]
    pr, ss, sm, vg = tab(b"IECSgorP"), tab(b"IECStesS"), tab(b"IECSlpmS"), tab(b"IECSigaV")
    e = se[16 * indice:16 * indice + 16]; assert e[0] and e[5], "indice %d inactif ou muet" % indice
    b = pr[e[8]]; sset = None
    for k in range(h[b + 4]):
        z = h[b + 0x24 + 20 * k:b + 0x24 + 20 * k + 20]
        if z[2] <= 12 + e[9] <= z[3]: sset = struct.unpack_from("<H", z)[0]; break
    assert sset is not None, "indice %d : touche hors programme" % indice
    bb = ss[sset]; assert h[bb + 3] == 1, "Sset %d : %d échantillons" % (sset, h[bb + 3])
    j = struct.unpack_from("<H", h, bb + 4)[0]; v = struct.unpack_from("<H", h, sm[j])[0]
    off, sr = struct.unpack_from("<IH", h, vg[v])
    return adpcm(bd, off), sr, sset, v


def vag(d, num, sr_attendu):
    """PCM d'un VAG d'une banque SCEI (conteneur MOMO) ; contrôle du taux d'origine"""
    assert d[:4] == b"MOMO", "banque SCEI inattendue"
    o, n = struct.unpack_from("<II", d, 8); o2, n2 = struct.unpack_from("<II", d, 16)
    h, bd = d[o:o + n], d[o2:o2 + n2]
    p = h.find(b"IECSigaV"); mx = struct.unpack_from("<I", h, p + 12)[0]; assert num <= mx
    b = p + struct.unpack_from("<I", h, p + 16 + 4 * num)[0]
    off, sr = struct.unpack_from("<IH", h, b); assert sr == sr_attendu, (num, sr)
    return adpcm(bd, off)


COEF = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]
def adpcm(bd, off):
    out = []; s1 = s2 = 0; p = off
    while p + 16 <= len(bd):
        sh = bd[p] & 15; f = bd[p] >> 4; fl = bd[p + 1]; c1, c2 = COEF[f] if f < 5 else (0, 0)
        for k in range(14):
            for nib in (bd[p + 2 + k] & 15, bd[p + 2 + k] >> 4):
                v = ((nib - 16 if nib >= 8 else nib) << 12) >> sh
                v = max(-32768, min(32767, v + (s1 * c1 + s2 * c2) // 64)); out.append(v); s2, s1 = s1, v
        p += 16
        if fl & 1: break
    return np.array(out, dtype=np.int16)


# ---------------------------------------------------------------- conversion (mêmes règles que les voix MAX)
def reechantillonne(x, fin, fout, demi=32, beta=8.6):
    r = fout / fin; n = int(np.floor(len(x) * r)); t = np.arange(n) / r; fc = 0.95 * min(1.0, r)
    k0 = np.floor(t).astype(int); y = np.zeros(n); w = np.kaiser(2 * demi + 1, beta)
    xp = np.concatenate([np.zeros(demi + 1), x, np.zeros(demi + 2)])
    for j in range(-demi, demi + 1):
        idx = k0 + j; d = t - idx
        y += xp[idx + demi + 1] * fc * np.sinc(fc * d) * np.interp(d, np.arange(-demi, demi + 1), w, left=0, right=0)
    return y


def choix_param(z, fr, nech):
    """hauteur : plus petite fréquence >= fr qui tienne en 64 Ko ; sinon la plus haute qui tienne (comme gen_voix_max)"""
    H = [struct.unpack_from("<H", z, TAB_HAUTEUR + 2 * i)[0] for i in range(108)]
    best = None
    for idx in range(30, 61):
        f = QS_HZ * H[idx] / 4096
        if int(nech * f / fr) + 16 > 0xFFFF: continue
        if f >= fr * 0.995: return 120 - idx, f, H[idx]
        best = (120 - idx, f, H[idx])
    if best: return best
    raise SystemExit("hauteur introuvable")


def tempo_pour(z, duree):
    T = [struct.unpack_from("<H", z, TAB_TEMPO + 2 * i)[0] for i in range(256)]
    ok = [i for i in range(256) if T[i] and 0x30 * 1024 / 250.0 / T[i] >= duree + 0.03]
    return max(ok), 0x30 * 1024 / 250.0 / T[max(ok)]


def zones_referencees(p):
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
        s, l, f = struct.unpack("<HHH", e[1:7])
        if s == l == f == 0 and e[0] == 0: continue
        a = (e[0] & 0xff) << 16; zr.append((a + min(s, l, f), a + max(s, l, f)))
    return sorted(zr)


def convertit(pcm, fr, z):
    x = pcm.astype(float) / 32768.0
    prm, f, haut = choix_param(z, fr, len(x))
    y = reechantillonne(x, fr, f)
    g = min(GAIN_MAX, CRETE / 127.0 / np.abs(y).max())
    s8 = np.clip(np.round(y * g * 127.0), -128, 127).astype(np.int8)
    nf = max(1, int(0.002 * f)); s8[:nf] = np.round(s8[:nf] * np.linspace(0, 1, nf)).astype(np.int8)
    s8[-nf:] = np.round(s8[-nf:] * np.linspace(1, 0, nf)).astype(np.int8)
    return s8.tobytes() + bytes(16), prm, f, haut, g, len(s8) / f


def voisin(p, c):
    """priorité et piste de la commande Z80 non vide la plus proche : d'abord en dessous dans le même bloc de $20 (sons
    du même perso), puis dans la même page"""
    cands = [x for x in range(c - 1, (c & ~0x1F) - 1, -1)] + [x for d in range(1, 0x100) for x in (c - d, c + d)]
    for x in cands:
        if x >> 8 != c >> 8 or not p.cmd(x)[0]: continue
        pr, t = p.morceau(p.cmd(x)[0])
        pistes = [k for k, a in enumerate(t) if a]
        if pr and pistes: return pr, pistes[0], x
    raise SystemExit("pas de voisin pour %04X" % c)


def construit(z0, q0, sons, journal=print):
    """sons : [dict(nom, cmd, pcm, taux)] (une entrée par échantillon ; cmd = côté 1, côté 2 = +$500)"""
    z = bytearray(z0); q = bytearray(q0); p0 = pilote(z0)
    ref = zones_referencees(p0)
    banques = [b for b in BANQUES if not any(a >> 16 <= b <= f >> 16 for a, f in ref)]
    assert len(sons) <= 32 and len(sons) <= N_ECH0 - 1499
    assert z[A_PROG:0x8000] == bytes(0x8000 - A_PROG) and z[NEWPT + 2 * NT:NEWPT + 2 * NT + 2] == bytes(2), "zone non libre"
    struct.pack_into("<H", z, NEWPT + 2 * NT, A_PROG)
    T = [struct.unpack_from("<H", z, 0x2E92 + 2 * i)[0] for i in range(128)]
    conv = [convertit(so["pcm"], so["taux"], z) for so in sons]
    libre = {b: 0 for b in banques}; place = {}
    for i in sorted(range(len(sons)), key=lambda i: -len(conv[i][0])):      # plus grands d'abord, première banque qui convient
        n = len(conv[i][0])
        b = next((b for b in banques if libre[b] + n <= 0x10000), None)
        assert b is not None, "plus de place dans les banques QSound libres"
        place[i] = (b, libre[b]); libre[b] += n + (-n % 16)
    reg = MORC; infos = []
    for i, so in enumerate(sons):
        data, prm, f, haut, g, duree = conv[i]; bq, u0 = place[i]
        u = np.arange(u0, u0 + len(data))
        for k, o in enumerate((bq << 16) | (u ^ 0x8000)): q[o] = data[k]
        deb, fin = u0 ^ 0x8000, int(u[-1]) ^ 0x8000
        entree = bytes([bq]) + struct.pack("<HHH", deb, (fin - 1) & 0xFFFF, fin) + bytes([prm])
        n = N_ECH0 - i; a_e = TECH + 8 * n
        assert z[a_e:a_e + 8] == bytes(8), "entrée %d non libre" % n
        z[a_e:a_e + 8] = entree
        z[A_PROG + 4 * i:A_PROG + 4 * i + 4] = struct.pack("<H", n) + b"\x00\x40"
        tt, dn = tempo_pour(z, duree)
        vol = VOLUMES.get(so["cmd"]) or so.get("volume") or min(range(128), key=lambda v: abs(T[v] - VOL_REF * G_REF / g))
        cmds = []
        for c in (so["cmd"], so["cmd"] + 0x500):
            pr, piste, vx = voisin(p0, c); cmds.append((c, piste, pr, vx))
            tr = bytes([0x05, tt, 0x06, 0xFF, 0x07, vol, 0x1F, NT, 0x08, i, 0x09, OCTAVE, NOTE, 0x17])
            ent = bytearray(33); ent[0] = pr
            struct.pack_into(">H", ent, 1 + 2 * piste, 33)          # décalage relatif à l'en-tête : la piste le suit
            m = bytes(ent) + tr
            assert z[reg:reg + len(m)] == bytes(len(m)) and (reg & 0x3FFF) + len(m) <= 0x4000 and reg + len(m) <= 0x50000
            z[reg:reg + len(m)] = m
            L = reg - 0x8000
            _, Lc = p0.cmd(c); r = lin2reg(Lc); assert z[r:r + 4] == bytes(4), "%04X non vide" % c
            z[r:r + 4] = bytes([L >> 16, (L >> 8) & 0xff, L & 0xff, 0])
            reg += len(m)
        info = dict(nom=so["nom"], cmds=" ".join("%04X(piste %d prio %02X comme %04X)" % x for x in cmds), source=so["src"],
                    echantillon=n, qsound="%02X%04X" % (bq, deb), param=prm, fr_ps2=round(so["taux"], 1), fr_qs=round(f, 1),
                    gain=round(float(g), 3), octets=len(data), duree=round(duree, 3), tempo=tt, volume=vol)
        journal("son PS2 : %s" % info); infos.append(info); so["cmds"] = [(c, pi) for c, pi, _, _ in cmds]
    journal("QSound : banques %s ; Z80 : entrées %d-%d, morceaux 0x%05X-0x%05X" % (
        " ".join("%02X(%d o)" % (b, libre[b]) for b in banques if libre[b]), N_ECH0 - len(sons) + 1, N_ECH0, MORC, reg - 1))
    return bytes(z), bytes(q), ref, infos


def verifie(z0, q0, z, q, ref, sons, journal=print):
    p0, p = pilote(z0), pilote(z)
    CMDS = [x for so in sons for x in so["cmds"]]
    nouv = set(c for c, _ in CMDS); diff = 0
    for c in range(0xC00):
        if c in nouv: assert p0.cmd(c)[0] == 0; continue
        if p0.resolution(c) != p.resolution(c): diff += 1; journal("  DIFFERENCE %04X" % c)
    for c, _ in CMDS:
        r = p.resolution(c); e = [t for t in r if t[0] == "08"]
        assert len(e) == 1 and e[0][3][0] in BANQUES, "%04X" % c
    for a, b in ref: assert q[a:b + 1] == q0[a:b + 1], "zone référencée 0x%06X modifiée" % a
    assert z[:0x3800] == z0[:0x3800], "code du pilote modifié"
    chz = sum(1 for k in range(len(z0)) if z0[k] != z[k]); chq = sum(1 for k in range(len(q0)) if q0[k] != q[k])
    journal("vérification : %d commandes anciennes identiques, %d différentes ; Z80 %d o changés ; QSound %d o changés"
            % (0xC00 - len(nouv) - diff, diff, chz, chq))
    return diff == 0


def ecrit(out, z, q, journal=print):
    os.makedirs(out, exist_ok=True)
    roms = {"hx3.01": z[0:0x8000] + z[0x10000:0x28000], "hx3.02": z[0x28000:0x50000]}
    for k, n in enumerate(ROMS[2:]):
        b = q[0x400000 * k:0x400000 * (k + 1)]; s = bytearray(len(b)); s[0::2] = b[1::2]; s[1::2] = b[0::2]; roms[n] = bytes(s)
    for n, d in roms.items():
        open(os.path.join(out, n), "wb").write(d)
        journal("%s  %s  CRC %08x" % (hashlib.md5(d).hexdigest(), n, zlib.crc32(d)))


def choisis():
    v = os.environ.get("HSFA_SONS_PS2", os.environ.get("HSFA_PARADE", "1"))
    if v == "0": return []
    if v == "1": return list(SONS_SPEC)
    noms = set(v.split(",")); return [x for x in SONS_SPEC if x[0] in noms]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--base", required=True); a.add_argument("--sortie", required=True)
    a.add_argument("--xdata"); a.add_argument("--manifeste"); a.add_argument("--journal")
    o = a.parse_args()
    spec = choisis()
    if not spec:
        os.makedirs(o.sortie, exist_ok=True)
        for n in ROMS: shutil.copyfile(os.path.join(o.base, n), os.path.join(o.sortie, n))
        print("HSFA_SONS_PS2=0 : ROM son recopiée sans changement"); return
    sons, banques = [], {}
    for nom, cmds, e, indices, taux in spec:
        if e not in banques: banques[e] = fichier_xdata(o.xdata, o.manifeste, e)
        for c, i in zip(cmds, indices):
            pcm, sr, sset, v = se_pcm(banques[e], i)
            sons.append(dict(nom=nom, cmd=c, pcm=pcm, taux=taux or float(sr), src="e%d indice %d Sset %d VAG %d" % (e, i, sset, v)))
            print("source %s %04X : e%d indice %d -> Sset %d VAG %d, %d échantillons à %d Hz, md5 PCM %s" % (
                nom, c, e, i, sset, v, len(pcm), sr, hashlib.md5(pcm.tobytes()).hexdigest()))
    z0, q0 = lit_base(o.base)
    os.makedirs(o.sortie, exist_ok=True)
    j = open(o.journal, "w", encoding="utf-8", newline="\n") if o.journal else None
    def jr(t): print(t); j and j.write(t + "\n")
    z, q, ref, infos = construit(z0, q0, sons, jr)
    assert verifie(z0, q0, z, q, ref, sons, jr)
    ecrit(o.sortie, z, q, jr)


if __name__ == "__main__":
    main()
