#!/usr/bin/env python3
"""ROM son HYBRIDE d'Upper (option C, SON-ro5.md §3.2) : programme Z80 d'Upper + musiques de SFA3.

Sources (X_DATA, index du manifeste ; recoupees avec les ROM d'arcade de sfa3ud si presentes) :
  Upper : Z80 = entree 388, QSound = entree 389 ; SFA3 : Z80 = 287, QSound = 288 (= sz3.01/02/11m/12m d'arcade).

Pilote (identique dans les deux Z80, seules les adresses de donnees changent, cf. RAPPORT-option-C.md) :
  - adresses LINEAIRES 24 bits : L < $8000 = zone fixe, sinon fenetre $8000-$BFFF, banque (L >> 14) - 2,
    region = L + $8000 (16 banques de 16 Ko, region audiocpu 0x10000-0x4FFFF) ;
  - en-tete ($3C00 SFA3 / $3800 Upper) : +1 table des commandes (lineaire $8C00 : n = $0C00, entrees de 4 o
    = pointeur 24 bits BE du morceau + 1 o), +3 table des echantillons (8 o : banque, debut, boucle, fin LE16,
    parametre), +5 table des pointeurs de tables de programmes (op $1F n -> mot en +5+2n) ;
  - morceau : priorite (0 = musique, voies $F700 ; sinon effet, voies $F200) + 16 decalages BE relatifs ;
    pistes : notes >= $20 (1 o), opcodes $00-$1F a arguments fixes, sauts RELATIFS (op $0E-$16) ;
  - op $08 i : programme = table courante + 4i : echantillon LE16 (bit 15 = drapeau), 1 o, enveloppe
    (index x8 depuis $8000 SFA3 / $6305 Upper : tables identiques) ; op $1C k v : repere $C010+k = v.

Construction (image 0x50000 de la region audiocpu, 16 banques ; QSound 16 Mo) :
  1. Z80 d'Upper tel quel ;
  2. bloc des 44 musiques de SFA3 (lineaire $BC05-$2C5FC, contigu, seulement des decalages relatifs) copie en
     lineaire DEST_MUS (zone libre d'Upper + banque 15) ; arguments des op $1F n -> n + 16 ;
  3. nouvelle table des pointeurs de programmes NEWPT (zone fixe libre) : 0-15 = celle d'Upper, 16-18 = tables
     0-2 de SFA3 recopiees en zone fixe avec les numeros d'echantillons renumerotes ;
  4. entrees d'echantillons de SFA3 ajoutees a la table d'Upper (banque + $80 -> e288 en QSound $800000+) ;
  5. code : op $1F lit NEWPT (`ld bc,$3805` en $1919) ; depart d'une musique (priorite 0, $0907) :
     `ld hl,($3805)` -> `ld hl,(NEWPT+32)` (Upper n'a aucun morceau de priorite 0) ;
  6. table des commandes : entrees des musiques 00xx de SFA3 (relogees) ;
  7. QSound = e389 (Upper) en 0-8 Mo + e288 (SFA3) en 8-16 Mo.

Sorties (format MAME : decoupage de sz3.01/02, QSound mots echanges comme ROM_LOAD16_WORD_SWAP) :
  hx3.01 (0x20000 = region[0:0x8000] + region[0x10000:0x28000]), hx3.02 (0x28000 = region[0x28000:0x50000]),
  hx3.11m/hx3.12m (= e389, comme gen_son.py ro5), hx3.13m/hx3.14m (= e288 = sz3.11m/sz3.12m d'arcade).
Chargees par le fork (sfa3hx) si HSFA_SON=<dossier> (cf. cps2.cpp, init_hsfa).

Usage : gen_hybride.py [dossier_sortie]   (defaut : ./roms_hybride/)
"""
import os, sys, struct, zlib, hashlib
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import gen_son                      # lecture X_DATA (manifeste), decoupage, swap16
from z80son import Z80, lin2reg, ARGS, SAUT

ARCADE = "<workspace>/work/mame/roms/sfa3ud/"
REGION = 0x50000                    # region audiocpu (QSOUND_SIZE) : 0x10000 + 16 banques
DEST_MUS = 0x23C05                  # lineaire (region 0x2BC05) : debut du bloc des musiques ; = SFA3 ($BC05) modulo $4000 -> memes
                                    # passages de banque (memes cycles Z80, audio identique a l'echantillon pres)
NEWPT = 0x6B10                      # zone fixe libre d'Upper : apres $6305 + 8x256 (enveloppes 128-255 = 0, lues par 023C/073C)
PROG_DEST = 0x6B40                  # tables de programmes 0-2 de SFA3 recopiees
DECAL_1F = 16                       # op $1F n (musique SFA3) -> n + 16
CODE_1F = 0x1919                    # ld bc,$3805 (op $1F)
CODE_MUS = 0x0907                   # ld hl,($3805) (depart d'un morceau de priorite 0, voies $F700)
CODE_EFF = 0x05F7                   # ld hl,($3805) (depart d'un effet, voies $F200) : inchange
CODE_SENT = 0x0910                  # ld (ix+$2F),$FF : echantillon « sentinelle » $FF00 d'une voie de musique au depart
SENT_MUS = 0x86                     # sentinelle des musiques dans l'hybride : $8600 -> entree $4975 + 8x$600 = $7975


def sources():
    z5, q5 = gen_son.lire("ro5")
    z3, q3 = gen_son.lire("ro3")
    if os.path.isdir(ARCADE):       # recoupement avec l'arcade (identite octet pour octet, cf. SON-ro5.md 1.1)
        roms = gen_son.decoupe(z3, q3)
        for n, d in roms.items():
            p = os.path.join(ARCADE, n)
            if os.path.exists(p):
                assert open(p, "rb").read() == d, "%s : X_DATA (ro3) different de l'arcade" % n
    return z3, q3, z5, q5


class Pilote(Z80):
    """Z80 + resolution des programmes/echantillons (table de pointeurs de programmes et table initiale)."""
    def __init__(self, data, hdr, pt_1f, env):
        self.z = bytearray(data); self.h = hdr; self.mod = None
        self.pt_1f, self.env = pt_1f, env
    def w16(self, L): return self.rb(L) | (self.rb(L + 1) << 8)
    def table_init(self, prio):
        return self.w16(self.pt_mus) if (prio == 0 and hasattr(self, "pt_mus")) else self.w16(self.h + 5)
    def echantillon(self, n):
        """entree de la table des echantillons (calcul du pilote $1466 : base + (8n mod 2^16), 24 bits)"""
        L = self.hdr()["tabech"] + ((8 * n) & 0xFFFF)
        return bytes(self.rb(L + k) for k in range(8))
    def parcours(self, L, tab0):
        """chemins d'une piste avec la table de programmes courante ; renvoie [(adr, op, args, table)]"""
        vus, res, pile = set(), [], [(L, tab0)]
        while pile:
            a, tab = pile.pop()
            while (a, tab) not in vus:
                vus.add((a, tab))
                op = self.rb(a)
                if op >= 0x20: a += 1; continue
                n = ARGS[op]
                arg = [self.rb(a + 1 + k) for k in range(n)]
                res.append((a, op, arg, tab))
                if op == 0x1f: tab = self.w16(self.pt_1f + 2 * arg[0])
                if op in SAUT:
                    rel = (arg[-2] << 8) | arg[-1]
                    rel -= 0x10000 if rel >= 0x8000 else 0
                    cible = a + 1 + n + rel
                    if op == 0x16: a = cible; continue
                    pile.append((cible, tab))
                if op == 0x17: break
                a += n + 1
        return res
    def resolution(self, c):
        """pour une commande : suite des opcodes (sans adresses) + contenu resolu des programmes (echantillon,
        enveloppe) -> sert a comparer deux Z80 a contenu egal"""
        p, _ = self.cmd(c)
        if not p: return None
        prio, pistes = self.morceau(p)
        out = [("prio", prio)]
        for k, L in enumerate(pistes):
            if L is None: out.append(("piste", k, None)); continue
            for a, op, arg, tab in sorted(self.parcours(L, self.table_init(prio))):
                if op == 0x08:
                    P = tab + 4 * (arg[0] & 0x7f)
                    prog = bytes(self.rb(P + j) for j in range(4))
                    n = (prog[0] | (prog[1] << 8))
                    ech = self.echantillon(n & 0x7fff)
                    env = bytes(self.z[self.env + 8 * prog[3] + j] if self.env < 0x8000 else
                                self.rb(self.env + 8 * prog[3] + j) for j in range(8))
                    out.append(("08", n & 0x8000, prog[2], ech, env))
                elif op == 0x1f:
                    out.append(("1f",))
                else:
                    out.append((op, tuple(arg)))
        return out


def construit(z3, q3, z5, q5, journal=print):
    s = Pilote(z3, 0x3C00, 0x3C05, 0x8000)
    u = Pilote(z5, 0x3800, 0x3805, 0x6305)
    hz = bytearray(z5) + bytes(REGION - len(z5))
    assert hz[0x8000:0x10000] == bytes(0x8000)

    # --- musiques de SFA3 : commandes 00xx de priorite 0 ; etendue et appartenance du bloc
    base, ncmd = s.cmdtab()
    assert u.cmdtab() == (base, ncmd)
    mus = [c for c in range(0x100) if s.cmd(c)[0] and s.morceau(s.cmd(c)[0])[0] == 0]
    assert not [c for c in range(ncmd) if u.cmd(c)[0] and u.morceau(u.cmd(c)[0])[0] == 0], "Upper a des musiques ?"
    assert all(u.cmd(c)[0] == 0 for c in mus), "commande de musique deja utilisee par Upper"
    octets, ops1f, progs = set(), set(), set()
    for c in mus:
        p, _ = s.cmd(c)
        prio, pistes = s.morceau(p)
        octets |= set(range(p, p + 33))
        for L in pistes:
            if L is None: continue
            for a, op, arg, tab in s.parcours(L, s.table_init(0)):
                octets |= set(range(a, a + 1 + len(arg)))
                if op == 0x1f: ops1f.add(a)
                if op == 0x08: progs.add((tab, arg[0] & 0x7f))
            v, _ = s.piste(L); octets |= v
    deb, fin = min(octets), max(octets) + 1
    autres = set()
    for c in range(ncmd):
        if c in mus or not s.cmd(c)[0]: continue
        p, _ = s.cmd(c); autres.add(p)
    assert not [p for p in autres if deb <= p < fin], "un effet de SFA3 est dans le bloc des musiques"
    taille = fin - deb
    assert DEST_MUS > len(z5.rstrip(b"\0")) - 0x8000, "DEST_MUS chevauche les donnees d'Upper"
    assert DEST_MUS + taille <= REGION - 0x8000, "bloc des musiques trop grand"
    delta = DEST_MUS - deb
    journal("musiques : %d commandes (%s) ; bloc SFA3 lineaire $%05X-$%05X (%d o) -> $%05X-$%05X (region 0x%05X-0x%05X)"
            % (len(mus), " ".join("%02X" % c for c in mus), deb, fin - 1, taille, DEST_MUS, DEST_MUS + taille - 1,
               lin2reg(DEST_MUS), lin2reg(DEST_MUS + taille - 1)))
    for k in range(taille):
        hz[lin2reg(DEST_MUS + k)] = s.rb(deb + k)
    tabs_1f = sorted(set(s.z[a + 1] for a in [lin2reg(x) for x in ops1f] if True))
    for a in sorted(ops1f):
        r = lin2reg(a + delta + 1)
        assert hz[r] < DECAL_1F
        hz[r] += DECAL_1F
    journal("op $1F dans les musiques : %d (tables %s -> +%d)" % (len(ops1f), tabs_1f, DECAL_1F))

    # --- tables de programmes 0..max de SFA3 -> zone fixe ; renumerotation des echantillons
    pt3 = [s.w16(0x3C05 + 2 * k) for k in range(16)]
    ntab = max(tabs_1f) + 1
    assert all(t in pt3[:ntab] for t, _ in progs)
    pdeb = pt3[0]
    pfin = max(t + 4 * i + 4 for t, i in progs)
    assert pdeb == min(pt3[:ntab]) and pfin <= 0x8000
    blocp = bytearray(s.z[pdeb:pfin])
    ech_utiles = sorted(set((blocp[4 * k] | (blocp[4 * k + 1] << 8)) & 0x7fff for k in range(len(blocp) // 4)))
    # nouvelles entrees : adresse = base Upper + 8n (le pilote calcule base + (8n mod 2^16))
    tech5 = u.hdr()["tabech"]
    a_ech = PROG_DEST + len(blocp)
    a_ech += (tech5 - a_ech) % 8
    n0 = (a_ech - tech5) // 8
    assert n0 * 8 < 0x10000 and n0 + len(ech_utiles) < 0x8000
    renum = {n: n0 + k for k, n in enumerate(ech_utiles)}
    fin_fixe = a_ech + 8 * len(ech_utiles)
    assert fin_fixe <= 0x8000 and hz[NEWPT:fin_fixe] == bytes(fin_fixe - NEWPT), "zone fixe non libre"
    for k in range(len(blocp) // 4):
        n = blocp[4 * k] | (blocp[4 * k + 1] << 8)
        m = renum[n & 0x7fff] | (n & 0x8000)
        blocp[4 * k], blocp[4 * k + 1] = m & 0xff, m >> 8
    hz[PROG_DEST:PROG_DEST + len(blocp)] = blocp
    for k, n in enumerate(ech_utiles):
        e = bytearray(s.echantillon(n))
        assert e[0] < 0x80
        e[0] |= 0x80                                     # e288 en QSound $800000+
        hz[a_ech + 8 * k:a_ech + 8 * k + 8] = e
    journal("tables de programmes SFA3 $%04X-$%04X (%d entrees, tables 0-%d) -> $%04X ; %d programmes utilises"
            % (pdeb, pfin - 1, len(blocp) // 4, ntab - 1, PROG_DEST, len(progs)))
    journal("echantillons SFA3 references : %d -> entrees Upper %d-%d ($%04X-$%04X), banque + $80"
            % (len(ech_utiles), n0, n0 + len(ech_utiles) - 1, a_ech, fin_fixe - 1))

    # --- NEWPT : 16 pointeurs d'Upper + tables de SFA3 relogees
    pt5 = [u.w16(0x3805 + 2 * k) for k in range(16)]
    for k, v in enumerate(pt5):
        struct.pack_into("<H", hz, NEWPT + 2 * k, v)
    for k in range(ntab):
        struct.pack_into("<H", hz, NEWPT + 2 * (DECAL_1F + k), PROG_DEST + pt3[k] - pdeb)
    journal("NEWPT $%04X : Upper %s + SFA3 %s" % (NEWPT, " ".join("%04X" % v for v in pt5),
            " ".join("%04X" % (PROG_DEST + pt3[k] - pdeb) for k in range(ntab))))

    # --- code
    assert hz[CODE_1F:CODE_1F + 3] == b"\x01\x05\x38", hz[CODE_1F:CODE_1F + 3].hex()
    assert hz[CODE_MUS:CODE_MUS + 3] == b"\x2a\x05\x38" and hz[CODE_EFF:CODE_EFF + 3] == b"\x2a\x05\x38"
    hz[CODE_1F:CODE_1F + 3] = bytes([0x01, NEWPT & 0xff, NEWPT >> 8])
    pm = NEWPT + 2 * DECAL_1F
    hz[CODE_MUS:CODE_MUS + 3] = bytes([0x2a, pm & 0xff, pm >> 8])
    journal("code : $%04X ld bc,$%04X (op $1F) ; $%04X ld hl,($%04X) (depart musique)" % (CODE_1F, NEWPT, CODE_MUS, pm))

    # --- sentinelle : au depart d'une musique, chaque voie recoit l'echantillon (ix+$2F:$2E) = $FF00 (bit 15 =
    # drapeau, numero $7F00) avant son premier programme ; le pilote lit alors l'entree base + ($7F00 x 8 mod 2^16) :
    # SFA3 $6000+$F800 = lineaire $15800 (donnees de musique : banque $AD, son parasite audible, cf. RAPPORT),
    # Upper $4975+$F800 = $14175 (donnees d'Upper, autre son). On reproduit celui de SFA3 : sentinelle $86 (numero
    # $0600, drapeau garde) -> entree en zone fixe libre, copie de celle de SFA3 (banque $80 | b : miroir de 8 Mo).
    assert hz[CODE_SENT:CODE_SENT + 4] == b"\xdd\x36\x2f\xff"
    a_sent = tech5 + ((8 * ((SENT_MUS & 0x7f) << 8)) & 0xFFFF)
    assert fin_fixe <= a_sent and a_sent + 8 <= 0x8000 and hz[a_sent:a_sent + 8] == bytes(8)
    assert (SENT_MUS & 0x80) and all(((SENT_MUS << 8) & 0x7fff) != (renum[n]) for n in renum)
    e = bytearray(s.echantillon(0x7F00)); e[0] = 0x80 | (e[0] & 0x7f)
    hz[a_sent:a_sent + 8] = e
    hz[CODE_SENT + 3] = SENT_MUS
    journal("sentinelle des musiques : $%04X ld (ix+$2F),$%02X -> entree $%04X = %s (SFA3 : lineaire $%05X)"
            % (CODE_SENT, SENT_MUS, a_sent, e.hex(" "), s.hdr()["tabech"] + 0xF800))

    # --- table des commandes
    for c in mus:
        p, Ls = s.cmd(c)
        q = p + delta
        r = lin2reg(Ls)
        assert hz[r:r + 4] == bytes(4)
        hz[r:r + 4] = bytes([q >> 16, (q >> 8) & 0xff, q & 0xff, s.rb(Ls + 3)])

    hq = bytes(q5) + bytes(q3)
    assert len(hq) == 0x1000000
    return bytes(hz), hq, mus


def verifie(z3, z5, hz, mus, journal=print):
    """verification statique : le Z80 hybride donne, commande par commande, les memes opcodes et le meme contenu
    resolu (programme, echantillon, enveloppe) que SFA3 pour les musiques et qu'Upper pour tout le reste."""
    s = Pilote(z3, 0x3C00, 0x3C05, 0x8000)
    u = Pilote(z5, 0x3800, 0x3805, 0x6305)
    h = Pilote(hz, 0x3800, NEWPT, 0x6305); h.pt_mus = NEWPT + 2 * DECAL_1F
    base, n = u.cmdtab()
    ok = diff = 0
    for c in range(n):
        if c in mus:
            a = s.resolution(c); b = h.resolution(c)
            # echantillons : banque + $80 dans l'hybride
            b = [(t[0], t[1], t[2], bytes([t[3][0] & 0x7f]) + t[3][1:], t[4]) if t[0] == "08" else t for t in b]
        else:
            a = u.resolution(c); b = h.resolution(c)
        if a == b: ok += 1
        else:
            diff += 1
            if diff < 5: journal("  DIFFERENCE commande %04X" % c)
    journal("verification statique : %d commandes identiques, %d differentes" % (ok, diff))
    # le code hors des 2 instructions modifiees est intact
    d = [k for k in range(0x3800) if hz[k] != z5[k]]
    journal("code modifie : %s" % " ".join("%04X" % k for k in d))
    assert d == [0x0908, 0x0909, 0x0913, 0x191A, 0x191B], d
    return diff == 0


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "roms_hybride")
    z3, q3, z5, q5 = sources()
    hz, hq, mus = construit(z3, q3, z5, q5)
    assert verifie(z3, z5, hz, mus)
    roms = {
        "hx3.01": hz[0x0000:0x8000] + hz[0x10000:0x28000],
        "hx3.02": hz[0x28000:0x50000],
        "hx3.11m": gen_son.swap16(hq[0x000000:0x400000]),
        "hx3.12m": gen_son.swap16(hq[0x400000:0x800000]),
        "hx3.13m": gen_son.swap16(hq[0x800000:0xC00000]),
        "hx3.14m": gen_son.swap16(hq[0xC00000:0x1000000]),
    }
    os.makedirs(out, exist_ok=True)
    for n, d in roms.items():
        open(os.path.join(out, n), "wb").write(d)
        print("%-8s %8d o  CRC %08x  SHA1 %s" % (n, len(d), zlib.crc32(d), hashlib.sha1(d).hexdigest()))
    open(os.path.join(out, "z80_hybride.bin"), "wb").write(hz)     # image brute de la region audiocpu (analyse)
    print("ecrit dans", out)


if __name__ == "__main__":
    main()
