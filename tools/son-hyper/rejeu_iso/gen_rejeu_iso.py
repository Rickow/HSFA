#!/usr/bin/env python3
"""Replay table of Hyper (hsfa_rejeu_table.txt) rebuilt from the player's ISO, without MAME and without any file of the
workshop: the original sound drivers of SFA1 and SFA2 (X_DATA e221 / e250, CPS2 Z80 drivers v1.05A / v1.05C) run
offline in hsfa_rejeu_iso (rejeu_iso.cpp, Z80 of z80.h), with the sweep protocol of the workshop measurement
(tools/son-hyper/gen_rejeu.py, docs/rapports/SON-HYPER-ROM.md §12), and their QSound register writes become the table.

Protocol (constants below, integers only): one session per game ; the 68000 hands over at cycle POIGNEE (stereo:
CFFE != 0) ; from frame DEBUT on, per command: FF00 (stop all) at frame 0, the command at frame AVANCE, next one at
frame PAS ; commands = every command of the driver with a priority $01-$7F, in increasing order (gen_rejeu.py rule).
Table rules = gen_rejeu.py (window up to 0.0670 s before the next command, truncated sound = still writing in the last
0.25 s, the voices' STOP answer added 1 ms after its last write, side 2 REF lines). Times: Z80 cycles -> us by
integer rounding. The table contains no sample data: only register writes, as before (format: gen_rejeu.py).

Usage: gen_rejeu_iso.py --xdata X_DATA.BIN --sortie hsfa_rejeu_table.txt [--travail DIR] [--outil EXE] [--garde]
       gen_rejeu_iso.py --essai EXE      self-test of a built hsfa_rejeu_iso, without game data (CI, builder)
  outil: HSFA_REJEU_ISO, or hsfa_rejeu_iso next to HSFA_FLUXTOOL (all-in-one builder), or compiled in --travail
  by the C++ compiler of the system (CXX, default g++).
"""
import argparse, os, shutil, struct, subprocess, sys, zlib

ICI = os.path.dirname(os.path.abspath(__file__))
SON = os.path.dirname(ICI)
sys.path.insert(0, SON)
from z80v105 import Z80                                   # noqa: E402
from gen_rejeu import canal, cote2                         # noqa: E402

X = ".exe" if os.name == "nt" else ""
VERSION = "1"                  # change it if the output changes (enters the build cache key through this file)
HORLOGE = 8000000              # Z80 cycles per second
# entries of X_DATA.BIN (AFS) and their CRC32: another edition of the disc is refused
JEUX = {"sfa1": dict(z80=221, qs=222, crc_z80=0xF81A556D, crc_qs=0xBD7D4B0B, base=0x00, code=0x2000),
        "sfa2": dict(z80=250, qs=251, crc_z80=0xEA61AE3B, crc_qs=0x4492C6D8, base=0x40, code=0x3000)}
# sweep protocol of the workshop measurement (Z80 cycles from power-on; frame = 134 144 cycles). Three constants are
# phases of that session, set once against its journal (no game data): image0 = phase of the frame ends against the
# Z80 IRQ grid (in MAME the IRQ timer restarts when the 68000 releases the Z80 reset: frame ends at line 240 = 122 880
# with a release at 12 400 mod 32 000 cycles give the same phase) ; poignee = handshake of the 68000, in an IRQ period
# = 2 mod 4 (phase of the driver's 4-tick sequencer) ; cffe = 1: stereo (the 68000 program had left CFFE != 0).
PROTOCOLE = dict(modele=1, poignee=8016000, image0=110480, debut=1100, pas=240, avance=4, dsp=0, cffe=1)
FENETRE = 536000               # 0.0670 s: a write is kept if it comes before the next command minus this
MARGE_TRONQUE = 2000000        # 0.25 s


def entrees_afs(xdata, numeros):
    """{numero: (decalage, octets)} of X_DATA.BIN (AFS archive)"""
    res = {}
    with open(xdata, "rb") as f:
        tete = f.read(8)
        if tete[:4] != b"AFS\0": raise SystemExit("%s: not an AFS archive" % xdata)
        n = struct.unpack_from("<I", tete, 4)[0]
        toc = f.read(8 * n)
        for e in numeros:
            o, t = struct.unpack_from("<II", toc, 8 * e)
            f.seek(o); res[e] = (o, t, f.read(t))
    return res


def outil(travail):
    """path of hsfa_rejeu_iso: prebuilt (HSFA_REJEU_ISO, or next to HSFA_FLUXTOOL), else compiled in travail"""
    if os.environ.get("HSFA_REJEU_ISO"): return os.environ["HSFA_REJEU_ISO"]
    if os.environ.get("HSFA_FLUXTOOL"):
        p = os.path.join(os.path.dirname(os.environ["HSFA_FLUXTOOL"]), "hsfa_rejeu_iso" + X)
        if os.path.exists(p): return p
    exe = os.path.join(travail, "hsfa_rejeu_iso" + X)
    srcs = [os.path.join(ICI, "rejeu_iso.cpp"), os.path.join(SON, "tests", "z80.h")]
    if not (os.path.exists(exe) and os.path.getmtime(exe) >= max(os.path.getmtime(s) for s in srcs)):
        subprocess.run([os.environ.get("CXX") or "g++", "-O2", "-std=c++11", "-I", os.path.join(SON, "tests"),
                        "-o", exe, srcs[0]], check=True)
    return exe


# self-test without game data: a 12-byte Z80 loop of our own (waits for QSound ready, writes the mailbox and an IRQ
# counter to the QSound registers) under a short protocol; the journal must be the same on every system
ESSAI_PROGRAMME = {0x0000: "F3ED5631FFFFFB" "3A07D00730FA" "3A00C03200D0" "3A04F03201D0" "3A01C03202D0" "18E6",
                   0x0038: "F53A04F03C3204F0F1FBC9"}
ESSAI_OPTIONS = ["--debut", "2", "--pas", "3", "--avance", "1", "--image0", "110480", "--poignee", "100", "--cffe", "1"]
ESSAI_MD5 = "32771f227f071fcb6e37b381be2c4eb6"   # Linux x86_64 (g++, clang), Windows (mingw, wine), 15/11/2026


def essai_synthetique(exe, dossier):
    """md5 of the journal of the self-test (no game data), or None if the tool fails"""
    img = bytearray(0x48000)
    for a, h in ESSAI_PROGRAMME.items(): img[a:a + len(h) // 2] = bytes.fromhex(h)
    os.makedirs(dossier, exist_ok=True)
    open(os.path.join(dossier, "essai_z80.bin"), "wb").write(bytes(img))
    open(os.path.join(dossier, "essai_codes.txt"), "wb").write(b"0102,0304\n")
    r = subprocess.run([os.path.abspath(exe), "essai_z80.bin", "essai_codes.txt", "essai_journal.txt"] + ESSAI_OPTIONS,
                       cwd=dossier, stdin=subprocess.DEVNULL, capture_output=True)
    j = os.path.join(dossier, "essai_journal.txt")
    if r.returncode or not os.path.exists(j): return None
    import hashlib
    return hashlib.md5(open(j, "rb").read()).hexdigest()


def commandes(image):
    """[(commande, priorite)] : every command of the driver with a priority $01-$7F (rule of the workshop sweep)"""
    z = Z80(image)
    res = []
    for c in range(z.n):
        m = z.morceau(c)
        if m is not None and 0 < m["prio"] < 0x80: res.append((c, m["prio"]))
    return res


def lit_journal(p):
    """-> (init, stop, [(commande, cycle de la commande, [(cycle, reg, val)])]) ; the window rule is applied later"""
    init, stop, cmds, fin = [], [], [], None
    vu_f = False
    with open(p, "rb") as f:
        for l in f.read().decode("ascii").split("\n"):
            t = l.split()
            if not t: continue
            if t[0] == "Q":
                e = (int(t[1]), int(t[2], 16), int(t[3], 16))
                if cmds: cmds[-1][2].append(e)
                elif vu_f: stop.append(e[1:])
                else: init.append(e[1:])
            elif t[0] == "F": vu_f = True
            elif t[0] == "C": cmds.append((int(t[2], 16), int(t[1]), []))
            elif t[0] == "E": fin = int(t[1])
    if fin is None or not cmds: raise SystemExit("%s: incomplete journal" % p)
    return init, stop, cmds


def section(jeu, J, init, stop, cmds, prios):
    """lines INIT / STOP / CODE / REF of one game (rules of gen_rejeu.py)"""
    L = ["INIT %s %d" % (jeu, len(init))] + ["%02x %04x" % rv for rv in init]
    L += ["STOP %s %d" % (jeu, len(stop))] + ["%02x %04x" % rv for rv in stop]
    stop_par_voie = {}
    for r, v in stop: stop_par_voie.setdefault(canal(r), []).append((r, v))
    defini, nb = {}, dict(codes=0, tronques=0, vides=0, lignes=0)
    for k, (c, tc, ev) in enumerate(cmds):
        dernier = k + 1 == len(cmds)
        tfin = None if dernier else cmds[k + 1][1] - FENETRE
        tr = [(t - tc, r, v) for t, r, v in ev if dernier or t < tfin]
        if not tr: nb["vides"] += 1; continue
        tronq = not dernier and tr[-1][0] > (tfin - tc) - MARGE_TRONQUE
        us = lambda cyc: (cyc * 1000000 + HORLOGE // 2) // HORLOGE
        corps = ["%d %02x %04x" % (us(t), r, v) for t, r, v in tr]
        if tronq:
            tf = us(tr[-1][0]) + 1000
            for vo in sorted({canal(r) for _, r, _ in tr if canal(r) >= 0}):
                corps += ["%d %02x %04x" % (tf, r, v) for r, v in stop_par_voie.get(vo, [])]
            nb["tronques"] += 1
        code = J["code"] + c
        L.append("CODE %04X %s %04X %02X %d%s" % (code, jeu, c, prios[c], len(corps), " T" if tronq else ""))
        L += corps
        defini[c] = code; nb["codes"] += 1; nb["lignes"] += len(corps)
    n2 = 0
    for c in sorted(defini):
        if cote2(jeu, c) in defini:
            L.append("REF %04X %04X" % (J["code"] + 0x500 + c, defini[cote2(jeu, c)])); n2 += 1
    nb["cote2"] = n2
    return L, nb


def main(argv=None):
    if argv is None: argv = sys.argv[1:]
    if argv[:1] == ["--essai"] and len(argv) == 2:
        import tempfile
        with tempfile.TemporaryDirectory() as t: m = essai_synthetique(argv[1], t)
        print("hsfa_rejeu_iso --essai : %s" % ("OK %s" % m if m == ESSAI_MD5 else "ECHEC %s (attendu %s)" % (m, ESSAI_MD5)))
        return 0 if m == ESSAI_MD5 else 1
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xdata", required=True); ap.add_argument("--sortie", required=True)
    ap.add_argument("--travail", help="working folder (default: next to --sortie)")
    ap.add_argument("--outil", help="hsfa_rejeu_iso to use (default: see outil())")
    ap.add_argument("--garde", action="store_true", help="keep the driver journals in --travail")
    a = ap.parse_args(argv)
    T = os.path.abspath(a.travail or os.path.join(os.path.dirname(os.path.abspath(a.sortie)), "rejeu_iso"))
    os.makedirs(T, exist_ok=True)
    ent = entrees_afs(a.xdata, sorted(e for J in JEUX.values() for e in (J["z80"], J["qs"])))
    for jeu, J in JEUX.items():
        for k in ("z80", "qs"):
            crc = zlib.crc32(ent[J[k]][2]) & 0xFFFFFFFF
            if crc != J["crc_" + k]:
                raise SystemExit("X_DATA e%d (%s): CRC %08X, expected %08X (another edition of the disc?)"
                                 % (J[k], jeu, crc, J["crc_" + k]))
    exe = a.outil or outil(T)
    m = essai_synthetique(exe, os.path.join(T, "essai"))
    if m != ESSAI_MD5:
        raise SystemExit("%s: self-test %s, expected %s (tool broken or built differently)" % (exe, m, ESSAI_MD5))
    opts = [x for k, v in sorted(PROTOCOLE.items()) for x in ("--" + k, str(v))]
    procs, prios = {}, {}
    for jeu, J in JEUX.items():             # both drivers at the same time (one process each)
        img = os.path.join(T, jeu + "_z80.bin")
        open(img, "wb").write(ent[J["z80"]][2])
        cs = commandes(img)
        prios[jeu] = dict(cs)
        open(os.path.join(T, jeu + "_codes.txt"), "wb").write((",".join("%04x" % c for c, _ in cs) + "\n").encode())
        # file names relative to the working folder: ASCII only, whatever the user's folder (narrow main on Windows)
        procs[jeu] = subprocess.Popen([os.path.abspath(exe), jeu + "_z80.bin", jeu + "_codes.txt", jeu + "_journal.txt"]
                                      + opts, cwd=T, stdin=subprocess.DEVNULL)
    for jeu, p in procs.items():
        if p.wait(): raise SystemExit("hsfa_rejeu_iso (%s): exit code %d" % (jeu, p.returncode))
    L = ["# hsfa_rejeu_table.txt : rejeu QSound des sons de SFA1 et SFA2, recree depuis l'ISO (gen_rejeu_iso.py v%s)" % VERSION,
         "# aucune donnee d'echantillon ici : la ROM QSound est lue dans le X_DATA.BIN de l'utilisateur",
         "VIDE 0000"]
    for jeu, J in JEUX.items():
        o, t, d = ent[J["qs"]]
        L.append("SOURCE %s %X %X %02X %08X" % (jeu, o, t, J["base"], zlib.crc32(d) & 0xFFFFFFFF))
    bilan = {}
    for jeu, J in JEUX.items():
        j = os.path.join(T, jeu + "_journal.txt")
        init, stop, cmds = lit_journal(j)
        if [c for c, _, _ in cmds] != sorted(prios[jeu]): raise SystemExit("%s: commands of the journal differ" % jeu)
        S, bilan[jeu] = section(jeu, J, init, stop, cmds, prios[jeu])
        L += S
        if not a.garde:
            for f in (j, os.path.join(T, jeu + "_z80.bin"), os.path.join(T, jeu + "_codes.txt")): os.remove(f)
    if not a.garde: shutil.rmtree(os.path.join(T, "essai"), ignore_errors=True)
    tmp = a.sortie + ".tmp"
    with open(tmp, "wb") as f: f.write(("\n".join(L) + "\n").encode("ascii"))
    os.replace(tmp, a.sortie)
    print("table du rejeu (ISO) : %s -> %s (%d o)" % (bilan, a.sortie, os.path.getsize(a.sortie)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
