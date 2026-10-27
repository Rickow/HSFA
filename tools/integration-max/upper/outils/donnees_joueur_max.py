#!/usr/bin/env python3
"""(agent_integration_max) Données de combat PAR PERSO d'un perso MAX, au format de l'IMAGE d'Upper, tirées des sections
de l'entrée [6] du pac PSP (plXX_e.pac, ~/.cache/sfa3max/pac, lecture seule).

Correspondance section PSP -> table arcade, mesurée sur Ryu, Ken, Akuma, Chun-Li, Dan (octets identiques à l'arcade) :
  s08/s09/s10/s11 = boîtes $90/$94/$98/$9C (mots)  ; s12 = attaques $A0 (32 o : mots $0-$7 petit-boutistes, octets $8-$1F = arcade)
  -> bloc « en-tête » ($DD012 -> $60 : 3 pointeurs d'isme -> en-tête de 5 mots relatifs, puis les 5 tables)
  s13 = table $88 ($DD092, 4 o / entrée, octets) ; s14 = table $C0 ($DD112, octets)
  s17 / s18 = octets par coup normal ($DCB12 : 3 mots de décalage par isme, Ryu [s18, s18, s17]) ; s19 = table $264 ($DF892, mots)
Format image (recette cps2) : mots natifs ; tables d'octets = octets échangés dans chaque mot ; attaques = mots $0-$7
natifs, octets $8-$1F échangés par mot ; longs = moitiés échangées. Contrôle : `--controle` recalcule Ryu et le compare
aux tables d'Upper (module ro5)."""
import os, sys, struct
sys.path.insert(0, "<workspace>/github/tools/max")
PAC = os.path.expanduser(os.environ.get("SFA3MAX_PAC_DIR", "~/.cache/sfa3max/pac"))

def sections(pl):
    from plpac import split
    E = split(open(os.path.join(PAC, "%s_e.pac" % pl), "rb").read()); b6 = E[6][1]
    Hs = [v + 0x208 for v in struct.unpack_from("<67I", b6, 0)]
    pts = sorted(set(Hs) | {len(b6)})
    return {k: b6[v:min(x for x in pts if x > v)] for k, v in enumerate(Hs) if v < len(b6)}

def swapw(b):
    b = bytes(b) + bytes(len(b) & 1)
    return bytes(x for i in range(0, len(b), 2) for x in (b[i + 1], b[i]))

def attaques_image(raw):
    """PSP : mots $0-$7 petit-boutistes, octets $8-$1F = octets arcade (mesuré sur Ryu, 91/93 entrées) ; image : mots
    natifs, octets échangés par mot -> image = mots échangés de la section PSP entière (contrôlé contre Upper).
    Octets $12 et $14 de chaque entrée : valeur ×2 dans l'arcade (sous-type de l'étincelle d'impact $14, champ $12),
    valeur PSP n (mesuré : Ryu 42+78, Ken 84+122, Akuma 60+93 entrées « ×2 », les autres nulles) ; sans cela l'étincelle
    (objet de classe 4) recevait un sous-type impair -> erreur d'adresse (relevé au banc)."""
    b = bytearray(raw)
    for i in range(0, len(b) - 31, 32):
        for k in (18, 20): b[i + k] = (2 * b[i + k]) & 0xFF
        # (2b22) types de recul MAX 28-32 (+9) -> 40-44 (rangs libres de la table de recul : prepare_max.RECUL_MAX)
        if 28 <= b[i + 9] <= 32: b[i + 9] += 12
    return swapw(bytes(b))

# n° de section (= élément n du sous-en-tête + 2) par table. L'en-tête de [6] est un SOUS-EN-TÊTE de 64 éléments :
# décalage +8+4n, nombre +264+4n (lu par 0x6A638 / 0x6AB48). Disposition standard : éléments 1-4 = listes de pas des
# animations, 5 = jeux de boîtes, 6-10 = $90/$94/$98/$9C/$A0, 11 = $88, 12 = $C0, 15/16 = octets des coups normaux,
# 17 = $264. YUN (pl28) : ses animations sont dans l'EBOOT et ses jeux de boîtes au début de [6] : mêmes tables
# décalées de 5 éléments (1-5 = boîtes et attaques, 6 = $88, 7 = $C0, 10/11 = coups normaux, 12 = $264), mesuré par
# les tailles (Yun $A0 = 3 008 o = 94 attaques, $88 = 272 o).
SECTIONS = {"standard": dict(b90=8, b94=9, b98=10, b9c=11, a0=12, t88=13, tc0=14, d17=17, d18=18, t264=19),
            "pl28": dict(b90=3, b94=4, b98=5, b9c=6, a0=7, t88=8, tc0=9, d17=12, d18=13, t264=14)}

def blocs(pl):
    """-> dict nom -> octets image (ordre d'assemblage), + décalages internes"""
    S = sections(pl); K = SECTIONS.get(pl, SECTIONS["standard"])
    S = dict(S); S[8], S[9], S[10], S[11], S[12], S[13], S[14], S[17], S[18], S[19] = (S[K[k]] for k in
        ("b90", "b94", "b98", "b9c", "a0", "t88", "tc0", "d17", "d18", "t264"))
    t = [swapw(S[8]), swapw(S[9]), swapw(S[10]), swapw(S[11]), attaques_image(S[12])]
    hdr, o = [], 10
    for x in t: hdr.append(o); o += len(x)
    entete = struct.pack(">5H", *hdr) + b"".join(t)
    dcb = struct.pack(">3H", 6 + len(S[17]), 6 + len(S[17]), 6) + swapw(S[17]) + swapw(S[18])
    return {"entete": entete, "t88": swapw(S[13]), "tc0": swapw(S[14]), "dcb12": dcb, "t264": swapw(S[19])}

def asm(pl, p):
    """texte vasm (disposition image) : étiquettes <p>_ENTETE_ISM (3 longs), <p>_ENTETE, <p>_T88, <p>_TC0, <p>_DCB12, <p>_T264"""
    B = blocs(pl); L = ["; ---- données de combat de %s (sections PSP [6], donnees_joueur_max.py)" % pl, "        even"]
    sw = lambda s: "((%s>>16)&$ffff)|((%s&$ffff)<<16)" % (s, s)
    L += ["%s_ENTETE_ISM:" % p] + ["        dc.l    %s" % sw("%s_ENTETE" % p)] * 3
    for nom in ("entete", "t88", "tc0", "dcb12", "t264"):
        d = B[nom]; L.append("%s_%s:" % (p, nom.upper()))
        for i in range(0, len(d), 16):
            L.append("        dc.b    " + ",".join("$%02x" % x for x in d[i:i + 16]))
        L.append("        even")
    return "\n".join(L) + "\n"

def controle():
    """Ryu (pl00) recalculé contre les tables d'Upper (module ro5 : données PS2 -> image = mots échangés)"""
    buf = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read()
    RB = 0x1F0000; u = lambda a: struct.unpack_from("<I", buf, a - RB)[0]
    img = lambda a, n: swapw(buf[a - RB:a - RB + n])
    B = blocs("pl00"); res = {}
    pe = u(u(0x749338)); n = len(B["entete"]); res["entete"] = img(pe, n) == B["entete"], sum(x == y for x, y in zip(img(pe, n), B["entete"])), n
    for nom, T in (("t88", 0x7493d8), ("tc0", 0x749478), ("t264", 0x74c5d8), ("dcb12", 0x748cf8)):
        d = B[nom]; g = img(u(T), len(d)); res[nom] = (g == d, sum(x == y for x, y in zip(g, d)), len(d))
    for k, v in res.items(): print("Ryu %-7s identique=%s  octets égaux %d/%d" % (k, *v))

if __name__ == "__main__":
    if "--controle" in sys.argv: controle()
    else: print(asm(sys.argv[1], sys.argv[2]))

def palettes_corps(pl, fichier="palettes_module.bin"):
    """30 palettes du corps (format du module, petit-boutiste) dans l'ordre du moteur d'Upper (groupe = couleur x 5).
    INGRID (pl29) : 48 palettes = 6 couleurs x 8 (périodicité 8 mesurée : palettes 8k+4 / 8k+5 voisines dans chaque
    groupe) ; ses frames n'emploient que les sous-palettes 0-3 (fusion haut + bas) -> palettes 8k..8k+4 par couleur."""
    import max_cache as MC
    d = open(MC.CV + "%s/%s" % (pl, fichier), "rb").read()
    if pl == "pl29" and fichier == "palettes_module.bin":
        d = b"".join(d[32 * 8 * k:32 * (8 * k + 5)] for k in range(6))
    d = d[:0x3C0]
    return d + bytes(0x3C0 - len(d))
