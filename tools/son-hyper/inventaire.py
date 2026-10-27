#!<workspace>/venv/bin/python
"""Inventaire de la place recuperable dans la ROM son (roms_hyper = hybride d'Upper + voix MAX v2 + voix d'origine) :
echantillons QSound, entrees d'echantillons, programmes et morceaux Z80 qu'AUCUNE commande atteignable ne reference.

Commande ATTEIGNABLE (criteres de agent_voix_max/numeros.py, appliques a TOUTES les commandes 0000-0BFF, durcis) :
  a. table native PS2 (0x1200 entrees, identique ro3/ro5/ro9) : contenu reel pour un code x tel que x mod $C00 = c
     (le Z80 fait c mod $C00) ; contenu reel = ADX (types 1/2, le fork peut jouer le Z80 a la place), banque commune
     (types 3/4 : o4 present dans e345/e346), banque de perso (type >= 5 : o4 present dans N'IMPORTE QUELLE banque
     e314-e344, plus strict que numeros.py qui ne regarde que la banque du perso du type) ;
  b. tables « sons par pas » de tous les programmes (sfa3ud, ro3, ro5, ro9) + 128 tables d'Hyper (0x6AE614) ;
  c. cris et K.O. : base + 0..6 (40 bases de 0x3D9A90 d'Hyper + tout debut de bloc $300 + $20k) ;
  d. commandes envoyees EN JEU dans les journaux 68K des agents (ro5, hybride, hyper_son, flux, son_hyper_rom) ;
  e. chaque code envoyable l'est aussi a +-$500 (cote 2), modulo $C00 ;
  f. pages 00 et 01 (et leur cote 2, 05 et 06) : TOUJOURS atteignables (musique, systeme, annonceur, bruitages
     communs : envoyes par des immediats 68K que les criteres a-e ne couvrent pas ; numeros.py les exclut aussi) ;
  g. voix MAX (roms_voix v2, attribution.json, c et c + $500) et nouvelles commandes du prototype (redirection.txt).
Une commande non vide du Z80 qui ne remplit AUCUN de ces criteres est « inatteignable ».

Echantillon LIBERABLE : octets QSound references seulement par des entrees que n'atteint aucune commande atteignable
(ni les sentinelles du pilote : entrees $600 = $7975 et $7F00 ; ni les entrees des plages completes que
zones_referencees() garde par prudence : elles sont listees a part). Bloc par bloc : banques ENTIERES rendues libres
(seules utilisables sans changer la lecture transitoire, regle de VOIX-MAX.md) et octets epars.
Ecrit catalogue/inventaire.json et affiche le bilan. Ne modifie rien."""
import os, sys, json, struct, glob, re
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
import numpy as np
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "<workspace>/work/agent_voix_max"); sys.path.insert(0, "<workspace>/work/agent_son_ro5/hybride")
import numeros as N
import gen_voix_max as G
from z80son import lin2reg, ARGS
sys.path.insert(0, "<workspace>/work/agent_hyper_son")
from table_son import charger

ROM = os.environ.get("ROM", os.path.join(ICI, "roms_hyper"))
SENTINELLES = (0x600, 0x7F00)


def banques_scei():
    """o4 presents par fichier e313-e346 (meme lecture que numeros.programmes_scei, etendue a e345/e346)"""
    m = {}
    for l in open(N.MANI).read().splitlines()[1:]:
        i, off, n, kind, name = l.split(",", 4); m[int(i)] = (int(off), int(n))
    out = {}
    with open(N.XD, "rb") as f:
        for e in range(314, 347):
            f.seek(m[e][0]); d = f.read(m[e][1])
            if d[:4] != b"MOMO": continue
            o, n = struct.unpack_from("<II", d, 8)
            h = d[o:o + n]
            ps = h.find(b"IECStesS")
            ok = set(range(struct.unpack_from("<I", h, ps + 12)[0] + 1)) if ps >= 0 else set()
            p = h.find(b"IECSgorP")
            if p >= 0:
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


def motifs():
    """code Z80 (0..BFF) -> ensemble des motifs qui le rendent atteignable"""
    mot = {}
    def ajoute(x, m):
        x %= 0xC00
        for y in (x, (x + 0x500) % 0xC00, (x - 0x500) % 0xC00):
            mot.setdefault(y, set()).add(m)
    # a. PS2
    d9, _, _, _, ents, pt = charger("ro9")
    sc = banques_scei()
    perso = set().union(*[sc[e] for e in range(314, 345) if e in sc])
    for x in range(0x1200):
        e = ents[x]; t = e[0] & 0x7f
        if t == 0: continue
        if t in (1, 2): ajoute(x, "PS2 ADX"); continue
        if t in (3, 4):
            if e[4] in sc.get(345 + t - 3, set()): ajoute(x, "PS2 commun")
            continue
        if e[4] in perso: ajoute(x, "PS2 perso")
    # b. tables par pas
    a = bytearray(open("<workspace>/work/mame/roms/sfa3ud/sz3ud.03c", "rb").read() + open("<workspace>/work/mame/roms/sfa3ud/sz3ud.04c", "rb").read())
    s = bytearray(len(a)); s[0::2] = a[1::2]; s[1::2] = a[0::2]
    for c in N.tables_pas(bytes(s), True): ajoute(c, "table sfa3ud")
    for mod in ("ro3", "ro5", "ro9"):
        for c in N.tables_pas(open(N.DEC % mod, "rb").read(), False): ajoute(c, "table " + mod)
    th = json.load(open(os.path.join(ICI, "catalogue/tables_hyper.json")))
    for v in th.values():
        for c in v["codes"]:
            if int(c, 16): ajoute(int(c, 16), "tables_hyper")
    # c. cris
    bases = {struct.unpack_from("<H", d9, 0x3D9A90 + 2 * i)[0] for i in range(40)} | set(range(0x300, 0x700, 0x20))
    for b in bases:
        if b:
            for n in range(7): ajoute(b + n, "cris")
    # d. journaux
    W = "<workspace>/work/"
    jeux = [f for f in glob.glob(W + "agent_son_ro5/journaux/*.txt") if not re.search(r"/(tab_|inj_|regs)", f)] + \
        glob.glob(W + "agent_son_ro5/hybride/journaux/[BC]_*.txt") + glob.glob(W + "agent_hyper_son/essais/*.son") + \
        glob.glob(W + "agent_flux/essais/*.son") + glob.glob(W + "agent_son_hyper_rom/essais/*.son")
    for f in jeux:
        t = open(f, errors="replace").read()
        for mm in re.finditer(r"(?:^C \S+ |cmd )([0-9a-fA-F]{4})\b", t, re.M):
            v = int(mm.group(1), 16)
            if v < 0x1200: ajoute(v, "journal")
    # f. pages 00-01 (+ cote 2)
    for c in list(range(0x000, 0x200)):
        ajoute(c, "page 00-01")
    # g. MAX + prototype
    for v in json.load(open("<workspace>/work/agent_voix_max/roms_voix/attribution.json")):
        ajoute(int(v["cmd"], 16), "voix MAX")
    for l in open(os.path.join(ROM, "redirection.txt")):
        t = l.split()
        if len(t) >= 3 and not l.startswith("#"): ajoute(int(t[2], 16), "roms_hyper")
    return mot


def plage_u(e):
    """entree d'echantillon -> (banque, u_lo, u_hi) en ordre signe u = adresse ^ $8000 (le DSP compare en signe)"""
    s, l, f = struct.unpack("<HHH", e[1:7])
    us = [x ^ 0x8000 for x in (s, l, f)]
    return e[0], min(us), max(us)


def octets_z80(p, c):
    """octets Z80 (regions) d'une commande : en-tete du morceau, pistes, programmes (table + 4i)"""
    a, _ = p.cmd(c)
    pr, pistes = p.morceau(a)
    o = set(lin2reg(a + k) for k in range(33))
    progs, ents = set(), set()
    for L in pistes:
        if L is None: continue
        for adr, op, arg, tab in p.parcours(L, p.table_init(pr)):
            o.update(lin2reg(adr + k) for k in range(1 + len(arg)))
            if op == 0x08:
                P = tab + 4 * (arg[0] & 0x7f)
                progs.add(P)
                prog = bytes(p.rb(P + j) for j in range(4))
                ents.add((prog[0] | (prog[1] << 8)) & 0x7fff)
    return o, progs, ents


def main():
    z, q = G.lit_base(ROM)
    p = G.pilote(z)
    mot = motifs()
    non_vides = [c for c in range(0xC00) if p.cmd(c)[0]]
    att = [c for c in non_vides if c in mot]
    inat = [c for c in non_vides if c not in mot]
    info = {}
    for c in non_vides:
        o, pr, en = octets_z80(p, c)
        info[c] = (o, pr, en)
    ent_att = set(SENTINELLES); z_att = set(); pr_att = set()
    for c in att:
        ent_att |= info[c][2]; z_att |= info[c][0]; pr_att |= info[c][1]
    ent_inat = set(); z_inat = set(); pr_inat = set()
    for c in inat:
        ent_inat |= info[c][2]; z_inat |= info[c][0]; pr_inat |= info[c][1]
    ent_lib = ent_inat - ent_att
    # entrees jamais resolues (aucune commande) dans les plages que l'hybride garde par prudence
    plages = set(range(0, 818)) | set(range(1169, 1283))
    ent_mortes = plages - ent_att - ent_inat
    # QSound : masque des octets gardes (entrees atteignables) en ordre physique
    def masque(ensemble):
        m = np.zeros(len(q), bool)
        for n in ensemble:
            e = p.echantillon(n)
            b, ulo, uhi = plage_u(e)
            if e[0] == 0 and e[1:7] == bytes(6): continue
            u = np.arange(ulo, uhi + 1)
            m[(b << 16) | (u ^ 0x8000)] = True
        return m
    m_att = masque(ent_att)
    m_lib = masque(ent_lib) & ~m_att
    m_mort = masque(ent_mortes) & ~m_att & ~masque(ent_inat)
    ban_att = set(np.nonzero(m_att.reshape(256, 0x10000).any(1))[0].tolist())
    ban_lib = sorted(b for b in set(np.nonzero((m_lib | m_mort).reshape(256, 0x10000).any(1))[0].tolist()) if b not in ban_att)
    z_lib = z_inat - z_att
    res = dict(
        commandes_non_vides=len(non_vides), atteignables=len(att), inatteignables=["%04X" % c for c in inat],
        motifs={("%04X" % c): sorted(mot[c]) for c in non_vides if c in mot},
        entrees_liberables=sorted(ent_lib), entrees_mortes=sorted(ent_mortes),
        octets_qsound_liberables=int(m_lib.sum()), octets_qsound_morts=int(m_mort.sum()),
        banques_entieres_liberees=["%02X" % b for b in ban_lib],
        octets_z80_morceaux_liberables=len(z_lib), programmes_liberables=len(pr_inat - pr_att),
    )
    # detail par banque
    par_banque = {}
    for b in range(256):
        s = slice(b << 16, (b + 1) << 16)
        a, l, mo = int(m_att[s].sum()), int(m_lib[s].sum()), int(m_mort[s].sum())
        if l or mo: par_banque["%02X" % b] = dict(garde=a, liberable=l, mort=mo)
    res["par_banque"] = par_banque
    json.dump(res, open(os.path.join(ICI, "catalogue", "inventaire.json"), "w"), indent=1)
    print("commandes non vides %d : atteignables %d, inatteignables %d" % (len(non_vides), len(att), len(inat)))
    pages = {}
    for c in inat: pages[c >> 8] = pages.get(c >> 8, 0) + 1
    print("  inatteignables par page :", {"%02X" % k: v for k, v in sorted(pages.items())})
    print("entrees d'echantillons : atteignables %d, liberables (seulement inatteignables) %d, jamais resolues (plages) %d"
          % (len(ent_att), len(ent_lib), len(ent_mortes)))
    print("QSound liberable : %d o (%.2f Mo) + entrees jamais resolues %d o (%.2f Mo)"
          % (m_lib.sum(), m_lib.sum() / 2 ** 20, m_mort.sum(), m_mort.sum() / 2 ** 20))
    print("banques entieres rendues libres : %d (%s)" % (len(ban_lib), " ".join(res["banques_entieres_liberees"])))
    print("Z80 : octets de morceaux/pistes liberables %d ; programmes liberables %d" % (len(z_lib), len(pr_inat - pr_att)))
    return res


if __name__ == "__main__":
    main()
