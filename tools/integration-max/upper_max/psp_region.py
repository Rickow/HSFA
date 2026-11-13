#!/usr/bin/env python3
"""psp_region.py -- editions of the SFA3 MAX PSP disc accepted by the Upper MAX build, and their conversion to the
layout of the reference edition (Europe, ULES-00235 v1.01) that the MAX tools (max/, tools/max/) are written for.

Accepted editions (DISC_ID of PSP_GAME/PARAM.SFO):
  ULES00235  Europe v1.01  reference: files used as they are.
  ULUS10062  USA v1.00     same data files (PL26-29, SE_MID, ...), stored in USRDIR/USA/DATA with the suffix _U;
                           BOOT.BIN differs:
                           - .text is 8 bytes shorter (one screen function of the engine, 0xBDAB4, has two
                             instructions less), so all the code after 0xBDAC4, the 41 character modules included,
                             sits 8 bytes lower;
                           - .rodata / .data / .bss are at the same addresses.
                           `relaie()` moves the code back to the European addresses (2 nops inserted at 0xBDAC4;
                           branches, j/jal, HI16/LO16 pairs and R_MIPS_32 words fixed through the PRX relocation
                           tables; section and program headers).
                           What still differs from the European BOOT.BIN is not read by the build: that screen
                           function, one .bss variable, an embedded PNG, region strings, 4 sprite numbers of a
                           screen animation.
                           6 lines of text (END26, END29, BD26, BD28) spell "Shadowloo" where the European disc and
                           the Anthology spell "Shadaloo": `normalise()` rewrites them, so the build gets the same
                           files as from the European disc (fingerprints checked).
  ULJM*      Japan         refused (other code layout and Japanese texts; not converted).

No game data here: only sizes, md5 fingerprints, addresses and the 6 text rules (record, line, x shift).
"""
import hashlib, os, struct, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "..", "max"))      # tools/max (iso_psp.py)
import iso_psp

BOOT = "PSP_GAME/SYSDIR/BOOT.BIN"
SFO = "PSP_GAME/PARAM.SFO"
PERSOS = (("26", "Eagle"), ("27", "Maki"), ("28", "Yun"), ("29", "Ingrid"))
PL_MD5 = {"26": (1705984, "7209750992a71f3b2a685ba9ddbb84f4"), "27": (1746944, "c6d5cee6395d8738f82c99a261ae3c8b"),
          "28": (1886208, "3a41b2100a3aded66a084e66b66351b2"), "29": (2078720, "c025bc2509aa1ea6d78ad0c83220866f")}
# BOOT.BIN of the reference edition (Europe), as the MAX tools expect it
BOOT_EU = (3693304, "df6d60fd9f843165b8040c5c23984e7d")

VERSIONS = {
    "ULES00235": dict(
        nom="europeen (ULES-00235 v1.01)", region="EUR", suffixe="_E", disc_version="1.01",
        boot=BOOT_EU, relais=None, boot_cache=BOOT_EU[1], textes={}),
    "ULUS10062": dict(
        nom="americain (ULUS-10062 v1.00)", region="USA", suffixe="_U", disc_version="1.00",
        boot=(3693304, "e1a537226325ea22f9408f0f67141ade"),
        relais=(0xBDAC4, 8, 0x1F8FF0),            # insertion point, bytes inserted, start of .rodata (does not move)
        boot_cache="74c029eef75bf257080d7599992b5c1f",  # BOOT.BIN after relaie() (European layout)
        # text files: md5 on the disc -> md5 after normalise() (= the European file)
        textes={"end26_e.pac": ("3f204da6670711de12d87749731cbe49", "6eec1a4360885f37639a267a3deb9108"),
                "end29_e.pac": ("55bf3649a4fca14e32e49ca3db05556b", "eaca0930fbe52482632961866ef468cc"),
                "bd26_e.pac": ("b5a0e27a878d1dfacae77ec061fbecdc", "fb8a71d465c034d48536c290c7867feb"),
                "bd28_e.pac": ("a76592f9ebfb43dd1a76b306a19ab6e8", "2a8761b1aaff8a102bccf2f3a4669af2")}),
}
REFUSES = {"ULJM": "japonaise (Street Fighter Zero 3 Double Upper)", "ULKS": "coreenne", "ULAS": "asiatique",
           "NPEH": "PSN Europe", "NPUH": "PSN USA", "NPJH": "PSN Japon"}

# "Shadowloo" -> "Shadaloo" : (file, text entry type, 0x80-byte record, line) -> shift of the line's x position
# (the line is re-centred: one character less). Record byte 0 (character count) loses 1.
TEXTES_REGLES = {("end26_e.pac", 0x10003, 7, 0): 4, ("end29_e.pac", 0x10003, 25, 0): 4,
                 ("bd26_e.pac", 0x10001, 7, 1): 3, ("bd28_e.pac", 0x10001, 13, 1): 3,
                 ("bd28_e.pac", 0x10001, 22, 1): 4, ("bd28_e.pac", 0x10001, 36, 1): 4}
MOT_US, MOT_EU = b"Shadowloo", b"Shadaloo"


class Refus(Exception):
    pass


def md5(d):
    return hashlib.md5(d).hexdigest()


def disc_id(iso):
    """DISC_ID of PARAM.SFO ("ULES00235"...) ; raises Refus if the file is not a readable PSP ISO"""
    try:
        sfo = iso_psp.lit(iso, SFO)
    except Exception as x:
        raise Refus("%s : pas une ISO de jeu PSP lisible (ISO 9660, PSP_GAME/PARAM.SFO) : %s. Un .cso / .chd se convertit "
                    "d'abord en .iso." % (iso, x))
    for cand in (b"ULES", b"ULUS", b"ULJM", b"ULKS", b"ULAS", b"NPEH", b"NPUH", b"NPJH"):
        i = sfo.find(cand)
        if i >= 0: return sfo[i:i + 9].decode("ascii", "replace")
    return "?"


def version(iso):
    """(disc id, VERSIONS entry) ; Refus with a message naming the edition if it is not accepted"""
    ident = disc_id(iso)
    if ident in VERSIONS: return ident, VERSIONS[ident]
    acceptees = " ou ".join(v["nom"] for v in VERSIONS.values())
    quoi = REFUSES.get(ident[:4])
    raise Refus("ISO PSP %s : %s n'est pas prise en charge%s. Acceptees : le disque d'origine de Street Fighter "
                "Alpha 3 MAX, %s." % (ident, "l'edition %s" % quoi if quoi else "cette ISO",
                                      " (autre disposition du code, autres textes : non convertie)"
                                      if ident[:4] == "ULJM" else "", acceptees))


def dossier(v):
    return "PSP_GAME/USRDIR/%s/DATA" % v["region"]


def nom_eu(nom, v):
    """name of a DATA file on the disc -> lower-case name of the European file (pl26_u.pac -> pl26_e.pac)"""
    low = nom.lower(); suf = v["suffixe"].lower() + ".pac"
    return low[:-len(suf)] + "_e.pac" if low.endswith(suf) else low


def _split(d):
    n = struct.unpack_from("<I", d, 0)[0]; out, off = [], 0x800
    for i in range(n):
        t, sz = struct.unpack_from("<2I", d, 8 + 8 * i); out.append((t, off, sz)); off += (sz + 0x7FF) & ~0x7FF
    return out


def normalise(nom, d):
    """text entries of a DATA file (European name) : MOT_US -> MOT_EU with TEXTES_REGLES ; other files unchanged"""
    regles = {k[1:]: dx for k, dx in TEXTES_REGLES.items() if k[0] == nom}
    if not regles: return d
    d = bytearray(d); faites = set()
    for typ, off, sz in _split(bytes(d)):
        for r in range(sz // 0x80):
            a = off + 0x80 * r; rec = bytes(d[a:a + 0x80])
            if MOT_US not in rec: continue
            p = 1; lignes = []
            while p < 0x80 and rec[p]:
                e = rec.index(0, p + 1); lignes.append([rec[p], rec[p + 1:e]]); p = e + 1
            for k, l in enumerate(lignes):
                if MOT_US in l[1]:
                    if (typ, r, k) not in regles:
                        raise Refus("%s : texte inattendu (entree %X, enregistrement %d, ligne %d)" % (nom, typ, r, k))
                    l[1] = l[1].replace(MOT_US, MOT_EU); l[0] += regles[(typ, r, k)]; faites.add((typ, r, k))
            neuf = bytes([rec[0] - 1]) + b"".join(bytes([x]) + t + b"\0" for x, t in lignes)
            d[a:a + 0x80] = neuf + bytes(0x80 - len(neuf))
    if faites != set(regles): raise Refus("%s : regles de texte non appliquees : %s" % (nom, sorted(set(regles) - faites)))
    return bytes(d)


def donnees(iso, v):
    """yields (European lower-case name, bytes) for every file of the edition's DATA folder, texts normalised and
    checked against the European fingerprints"""
    for nom in sorted(iso_psp.liste(iso, dossier(v))):
        n = nom_eu(nom, v); d = iso_psp.lit(iso, dossier(v) + "/" + nom)
        if n in v["textes"]:
            avant, apres = v["textes"][n]
            if md5(d) != avant: raise Refus("%s : md5 %s, attendu %s (ISO modifiee ?)" % (nom, md5(d), avant))
            d = normalise(n, d)
            if md5(d) != apres: raise Refus("%s : md5 apres normalisation des textes %s, attendu %s" % (nom, md5(d), apres))
        yield n, d


def _sext16(x):
    return x - 0x10000 if x & 0x8000 else x


def relaie(d, P, N, FIN):
    """PRX BOOT.BIN -> same module with N zero bytes (nops) inserted at address P of segment 0 ; addresses >= FIN
    (start of .rodata, aligned: the padding before it absorbs N) do not move. Returns (bytes, counters)."""
    shoff = struct.unpack_from("<I", d, 0x20)[0]; shn = struct.unpack_from("<H", d, 0x30)[0]
    hs = [list(struct.unpack_from("<10I", d, shoff + 40 * i)) for i in range(shn)]
    st = hs[struct.unpack_from("<H", d, 0x32)[0]][4]
    nom = lambda h: d[st + h[0]:d.index(b"\0", st + h[0])].decode("ascii", "replace")
    ph = [list(struct.unpack_from("<8I", d, 52 + 32 * i)) for i in range(struct.unpack_from("<H", d, 0x2C)[0])]
    o0 = ph[0][1]                                                 # file offset of segment 0 (vaddr 0)
    txt = [h for h in hs if nom(h) == ".text"][0]
    if not (txt[3] == 0 and txt[4] == o0 and P < txt[5]): raise Refus("BOOT.BIN : disposition de .text inattendue")

    def f(a):                                                     # old -> new address in segment 0
        return a + N if P <= a < FIN else a

    seg = d[o0:o0 + ph[0][4]]
    fin_bas = max(h[3] + h[5] for h in hs if h[3] and h[3] < FIN and h[1] != 8)
    if fin_bas + N > FIN or any(seg[fin_bas:FIN]): raise Refus("BOOT.BIN : pas de place pour %d octets avant %X" % (N, FIN))
    neuf = bytearray(seg[:P]) + bytearray(N) + bytearray(seg[P:FIN - N]) + bytearray(seg[FIN:])
    lit = lambda a: struct.unpack_from("<I", neuf, a)[0]
    def ecrit(a, v): struct.pack_into("<I", neuf, a, v & 0xFFFFFFFF)

    # relative branches and j/jal of the executable sections
    fin_code = max(h[3] + h[5] for h in hs if h[2] & 4 and h[1] == 1)
    nb = nj = 0
    for a in range(0, fin_code, 4):                               # a = old address
        na = f(a); x = lit(na); op = x >> 26
        branche = op in (4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17) \
            or (op == 1 and ((x >> 16) & 0x1F) in (0, 1, 2, 3, 0x10, 0x11, 0x12, 0x13)) \
            or (op in (0x11, 0x12) and ((x >> 21) & 0x1F) == 8)
        if branche:
            no = (f(a + 4 + _sext16(x & 0xFFFF) * 4) - na - 4) // 4
            if no != _sext16(x & 0xFFFF):
                if not -0x8000 <= no < 0x8000: raise Refus("BOOT.BIN : branche hors de portee en %X" % a)
                ecrit(na, (x & 0xFFFF0000) | (no & 0xFFFF)); nb += 1
        elif op in (2, 3):
            t = (x & 0x3FFFFFF) << 2
            if f(t) != t: ecrit(na, (x & 0xFC000000) | (f(t) >> 2)); nj += 1

    # relocation tables (outside segment 0, in place): offsets and relocated values
    out = bytearray(d); nh = n32 = 0
    for h in hs:
        if h[1] != 0x700000A0: continue                           # SHT_PSP_REL
        ents = [list(struct.unpack_from("<2I", d, h[4] + 8 * k)) for k in range(h[5] // 8)]
        hi = None                                                 # last HI16 (new address) towards segment 0
        for e in ents:
            o, inf = e; typ, ob, ab = inf & 0xFF, (inf >> 8) & 0xFF, (inf >> 16) & 0xFF
            if ob not in (0, 1) or ab not in (0, 1) or typ not in (0, 2, 4, 5, 6):
                raise Refus("BOOT.BIN : relocation inattendue %08X" % inf)
            if ob == 1:                                           # word in segment 1 (does not move)
                if typ == 2 and ab == 0:
                    fo = ph[1][1] + o; v = struct.unpack_from("<I", out, fo)[0]
                    if f(v) != v: struct.pack_into("<I", out, fo, f(v)); n32 += 1
                continue
            e[0] = no = f(o)
            if typ == 2 and ab == 0:
                v = lit(no)
                if f(v) != v: ecrit(no, f(v)); n32 += 1
            elif typ == 5 and ab == 0:
                hi = no
            elif typ == 6 and ab == 0:                            # a HI16 may serve several LO16
                if hi is None: raise Refus("BOOT.BIN : LO16 sans HI16 en %X" % o)
                lo = lit(no); hv = lit(hi)
                v = ((hv & 0xFFFF) << 16) + _sext16(lo & 0xFFFF); nv = f(v)
                if nv != v:
                    nlo = nv & 0xFFFF; nhi = ((nv - _sext16(nlo)) >> 16) & 0xFFFF
                    ecrit(no, (lo & 0xFFFF0000) | nlo); ecrit(hi, (hv & 0xFFFF0000) | nhi); nh += 1
            # typ 4 (j/jal): done by the scan above ; values towards segment 1: unchanged
        for k, e in enumerate(ents): struct.pack_into("<2I", out, h[4] + 8 * k, *e)

    out[o0:o0 + len(neuf)] = neuf
    for i, h in enumerate(hs):                                    # section headers
        if h[1] == 0x700000A0: continue
        if nom(h) == ".text": h[5] += N
        elif P <= h[3] < FIN and h[2] & 2: h[3] += N; h[4] += N   # allocated sections after P
        struct.pack_into("<10I", out, shoff + 40 * i, *h)
    if P <= ph[0][3] - o0 < FIN: ph[0][3] += N                    # p_paddr = file offset of sceModuleInfo
    struct.pack_into("<8I", out, 52, *ph[0])
    return bytes(out), dict(branches=nb, sauts=nj, hi_lo=nh, mots32=n32)


def boot_eu(iso, v, controle=True):
    """BOOT.BIN of the disc -> (BOOT.BIN in the European layout, message) ; checks both fingerprints (controle=False:
    --iso-differente, no check)"""
    d = iso_psp.lit(iso, BOOT)
    if controle and (len(d), md5(d)) != tuple(v["boot"]):
        raise Refus("%s : md5 %s (%d o), attendu %s (%d o) pour le disque %s (ISO modifiee, patchee 16:9, ou corrompue)"
                    % (BOOT, md5(d), len(d), v["boot"][1], v["boot"][0], v["nom"]))
    if not v["relais"]: return d, "BOOT.BIN tel quel"
    r, n = relaie(d, *v["relais"])
    if controle and md5(r) != v["boot_cache"]: raise Refus("BOOT.BIN remis en disposition europeenne : md5 %s, attendu %s"
                                              % (md5(r), v["boot_cache"]))
    return r, ("BOOT.BIN remis en disposition europeenne (+%d o en %X : %d branches, %d j/jal, %d HI16/LO16, "
               "%d mots)" % (v["relais"][1], v["relais"][0], n["branches"], n["sauts"], n["hi_lo"], n["mots32"]))


if __name__ == "__main__":
    iso = sys.argv[1]; ident, v = version(iso); print(ident, v["nom"])
    b, m = boot_eu(iso, v); print(m, md5(b))
    for n, d in donnees(iso, v):
        if n in v["textes"]: print(n, md5(d), "(textes normalises)")
