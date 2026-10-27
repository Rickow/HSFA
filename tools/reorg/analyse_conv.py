#!/usr/bin/env python3
"""ANALYSE DU JOURNAL DES CONVERSIONS (ETAPE A). Usage :
  analyse_conv.py SORTIE_PREFIXE journal1.txt [journal2.txt ...]
Entrees : journaux de journal_conv.lua ; image programme (prog_tr.bin) et carte_image.txt du dossier de l'agent
(copies figees, md5 dans md5_roms_tr.txt). Sorties : PREFIXE.json (detail) et PREFIXE.txt (resume)."""
import sys, os, struct, bisect, json, collections
A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = open(os.path.join(A, "prog_tr.bin"), "rb").read()
CARTE = []
for l in open(os.path.join(A, "carte_image.txt")):
    a, va, mn = l.rstrip("\n").split(" ", 2); CARTE.append((int(a, 16), int(va, 16), mn))
CK = [c[0] for c in CARTE]
def carte(a):
    if a < 0x1000: return (a, 0, "noyau68k" if a >= 0xB00 else "?")
    k = bisect.bisect_right(CK, a) - 1
    return CARTE[k] if k >= 0 else (a, 0, "?")

DST = [0x400, 0x41E, 0x440, 0x462, 0x484, 0x4A6, 0x4C8]
CST = [0x3FF000, 0x3FF01E, 0x3FF040, 0x3FF062, 0x3FF084, 0x3FF0A6, 0x3FF0C8]
# --- plages lues dans la ROM (talons) : verification
assert struct.unpack_from(">I", IMG, 0x404)[0] == 0x583C40 and struct.unpack_from(">I", IMG, 0x40E)[0] == 0xA97630
CODE_LO, CODE_HI = struct.unpack_from(">I", IMG, 0x3FF004)[0], struct.unpack_from(">I", IMG, 0x3FF00E)[0]
HASH = {}
for i in range(1 << 14):
    k, v = struct.unpack_from(">II", IMG, 0x3C0000 + 8 * i)
    if k: HASH[k] = v
DATA_ADD = -0x4F0C40           # donnees PS2 [$583C40,$88C700) -> ROM 68K (lu dans l'arbre du coeur : ADDA.L #$FFB0F3C0)
assert struct.unpack_from(">I", IMG, 0x5BA)[0] == (DATA_ADD & 0xffffffff)
DATA_LO68, DATA_HI68 = 0x583C40 + DATA_ADD, 0x88C700 + DATA_ADD
ASSET_LO68 = 0xA80000 + struct.unpack_from(">i", IMG, 0x528)[0]

def zone_ps2(v):
    """zone d'une valeur dans la carte PS2 (talons de donnees) : (zone, convertie ?)"""
    if v == 0: return "nul", False
    if 0x583C40 <= v < 0x88C700: return "donnees PS2", True
    if 0x88C700 <= v < 0x900000: return "variables du portage", True
    if 0x900000 <= v < 0x910000: return "RAM PS2", True
    if 0x910000 <= v < 0x914000: return "objets PS2", True
    if 0x914000 <= v < 0x920000: return "trou $914000 (laisse)", False
    if 0x920000 <= v < 0x950000: return "video PS2", True
    if 0x950000 <= v < 0x960000: return "variables du portage 2", True
    if 0x960000 <= v < 0x962000: return "QSound PS2", True
    if 0x962000 <= v < 0x980000: return "variables du portage 3", True
    if 0x980000 <= v < 0xA80000: return "trou $980000 (laisse ; bloc externe $A04000)", False
    if 0xA80000 <= v < 0xA97630: return "tables natives PS2", True
    if CODE_LO <= v < CODE_HI:
        # chevauchement : [$212B00, $3C0000) est AUSSI la plage des donnees ROM 68K ; debut de fonction connu => code
        if v in HASH: return "code PS2 (laisse)", False
        if v < 0x3C0000: return "68K ROM donnees", False
        return "code PS2 hors table (laisse)", False
    if v < 0x1000: return "68K bas (<$1000)", False
    if v < 0x93000: return "68K code", False
    if v < 0x400000: return "68K ROM donnees", False
    if 0xFF0000 <= v <= 0xFFFFFF: return "68K RAM", False
    if (v >> 24) == 1: return "68K materiel (etiquete $01)", False
    if 0xF00000 <= v < 0xFF0000: return "68K RAM du portage", False
    return "autre (laisse)", False

def zone_cell(a):
    if a == 0: return "inconnue"
    if DATA_LO68 <= a < DATA_HI68: return "ROM donnees"
    if ASSET_LO68 <= a < 0x3C0000: return "ROM tables natives"
    if 0x93000 <= a < 0x3C0000: return "ROM autre"
    if 0xFF0000 <= a <= 0xFFFFFF: return "RAM"
    if 0xF00000 <= a < 0xFF0000: return "RAM du portage"
    return "autre"

NSTAT = [0, 0]
for o_ in range(0xB00, 0x3C0000, 2):
    w_ = struct.unpack_from(">H", IMG, o_)[0]
    if w_ == 0x4EB8 and struct.unpack_from(">H", IMG, o_ + 2)[0] in DST: NSTAT[0] += 1
    elif w_ == 0x4EB9 and struct.unpack_from(">I", IMG, o_ + 2)[0] in CST: NSTAT[1] += 1

CONVZ = {"donnees PS2", "variables du portage", "RAM PS2", "objets PS2", "video PS2", "variables du portage 2", "QSound PS2",
         "variables du portage 3", "tables natives PS2", "code PS2 -> 68K"}

def site_of(pc):
    """adresse de retour -> site du JSR"""
    if struct.unpack_from(">H", IMG, pc - 4)[0] == 0x4EB8: return pc - 4
    if struct.unpack_from(">H", IMG, pc - 6)[0] == 0x4EB9: return pc - 6
    return pc

def main():
    pref, files = sys.argv[1], sys.argv[2:]
    ev = collections.Counter(); nim = 0; nev = 0
    for fn in files:
        for l in open(fn):
            if l.startswith("#"):
                p = l.split(); nim += int(p[2]); nev += int(p[4]); continue
            p = l.split()
            pc, t, v, a, f, w1, w2, n = int(p[1], 16), int(p[2]), int(p[3], 16), int(p[4], 16), p[5], int(p[6], 16), int(p[7], 16), int(p[8])
            ev[(pc, t, v, a, f, w1, w2)] += n
    sites = {}; cells = {}; tot = collections.Counter(); totz = collections.Counter(); croise = collections.Counter()
    for (pc, t, v, a, f, w1, w2), n in ev.items():
        s = site_of(pc); code = t >= 10
        if code:
            if CODE_LO <= v < CODE_HI: z, conv = ("code PS2 -> 68K", True) if v in HASH else ("code PS2 ABSENT de la table", False)
            else: z, conv = zone_ps2(v)[0] + " (laisse)", False
        else: z, conv = zone_ps2(v)
        zc = zone_cell(a)
        croise["code" if code else "donnees", zc, z] += n
        tot["code" if code else "donnees", conv] += n
        totz["code" if code else "donnees", z] += n
        S = sites.setdefault(s, {"site": "%06x" % s, "talon": ("CCONV_A%d" if code else "CONV_A%d") % (t % 10),
                                 "va": "%07x" % carte(s)[1], "src": carte(s)[2][:120], "n": 0, "convertis": 0,
                                 "zones": collections.Counter(), "origines": collections.Counter(), "valeurs": set()})
        S["n"] += n; S["convertis"] += n if conv else 0; S["zones"][z] += n; S["origines"]["%06x %s" % (a, zc)] += n
        if len(S["valeurs"]) < 2000: S["valeurs"].add(v)
        C = cells.setdefault(a, {"case": "%06x" % a, "zone": zc, "n": 0, "convertis": 0, "formes": collections.Counter(),
                                 "valeurs": collections.Counter(), "zones": collections.Counter(), "sites": collections.Counter(),
                                 "ecrivains": collections.Counter()})
        C["n"] += n; C["convertis"] += n if conv else 0; C["formes"][f] += n; C["zones"][z] += n
        C["sites"]["%06x" % s] += n
        if len(C["valeurs"]) < 64 or v in C["valeurs"]: C["valeurs"][v] += n
        if zc.startswith("RAM"):
            for w in {w1, w2}:
                if w: C["ecrivains"]["%06x" % w] += n
    # ---- sorties
    def cnt(c, k=12): return [[x, y] for x, y in c.most_common(k)]
    js = {"images": nim, "evenements": nev, "totaux": {"%s|%s" % k: n for k, n in tot.items()},
          "zones_valeurs": {"%s|%s" % k: n for k, n in totz.items()},
          "sites": [], "cases": []}
    for s in sorted(sites):
        S = sites[s]
        js["sites"].append({**{k: S[k] for k in ("site", "talon", "va", "src", "n", "convertis")},
                            "zones": cnt(S["zones"]), "origines": cnt(S["origines"], 20),
                            "nb_valeurs": len(S["valeurs"]), "valeurs": ["%x" % x for x in sorted(S["valeurs"])[:16]]})
    ecr_info = {}
    for a in sorted(cells):
        C = cells[a]
        e = {k: C[k] for k in ("case", "zone", "n", "convertis")}
        if a and C["zone"].startswith("ROM") and a < DATA_HI68: e["ps2"] = "%06x" % (a - DATA_ADD)
        if 0xFF0000 <= a: e["a5"] = "%+05x" % (a - 0xFF8000)
        e.update({"formes": cnt(C["formes"]), "zones": cnt(C["zones"]), "nb_valeurs": len(C["valeurs"]),
                  "valeurs": [["%x" % x, y] for x, y in C["valeurs"].most_common(16)], "sites": cnt(C["sites"]),
                  "ecrivains": cnt(C["ecrivains"])})
        for w, _ in C["ecrivains"].most_common(12):
            ecr_info[w] = "%07x %s" % (carte(int(w, 16))[1], carte(int(w, 16))[2][:120])
        js["cases"].append(e)
    js["ecrivains"] = ecr_info
    json.dump(js, open(pref + ".json", "w"), indent=1)
    # ---- resume
    o = open(pref + ".txt", "w")
    def P(*x): print(*x, file=o)
    P("journal des conversions : %d images, %d appels de talons authentiques" % (nim, nev))
    for k in ("donnees", "code"):
        a_, b_ = tot[k, True], tot[k, False]
        if a_ + b_: P("  %-8s : %9d appels, convertis %9d (%.1f %%), laisses %9d" % (k, a_ + b_, a_, 100 * a_ / (a_ + b_), b_))
    P("valeurs vues, par zone :")
    for (k, z), n in sorted(totz.items(), key=lambda x: -x[1]): P("  %-8s %-45s %9d" % (k, z, n))
    zs = collections.Counter(); zsc = collections.Counter(); zn = collections.Counter()
    for a, C in cells.items():
        zs[C["zone"]] += 1; zn[C["zone"]] += C["n"]
        if C["convertis"]: zsc[C["zone"]] += 1
    P("cases d'origine (adresse lue juste avant le talon) :")
    for z in zs: P("  %-20s %6d cases (%6d avec au moins une conversion), %9d appels" % (z, zs[z], zsc[z], zn[z]))
    nc_ = sum(1 for S in sites.values() if S["talon"].startswith("CC"))
    P("sites d'appel actifs : %d (donnees %d, code %d) sur %d sites statiques (donnees %d, code %d)" % (len(sites), len(sites) - nc_, nc_,
      NSTAT[0] + NSTAT[1], NSTAT[0], NSTAT[1]))
    P("sites qui ne convertissent JAMAIS (talon inutile sur ce parcours) : %d" % sum(1 for S in sites.values() if S["convertis"] == 0))
    P("sites qui convertissent TOUJOURS : %d" % sum(1 for S in sites.values() if S["convertis"] == S["n"]))
    P("\n20 sites les plus appeles :")
    for S in sorted(sites.values(), key=lambda S: -S["n"])[:20]:
        P("  %s %-9s va %s n=%8d conv=%5.1f%% %s" % (S["site"], S["talon"], S["va"], S["n"], 100 * S["convertis"] / S["n"], S["src"][:70]))
    P("\ncases RAM (pointeurs PS2 convertis), par nombre d'appels :")
    for C in sorted((C for C in cells.values() if C["zone"].startswith("RAM") and C["convertis"]), key=lambda C: -C["n"])[:40]:
        P("  %s (A5%+05x) n=%7d conv=%7d valeurs=%3d ecrivains=%s" % (C["case"], int(C["case"], 16) - 0xFF8000, C["n"], C["convertis"],
          len(C["valeurs"]), ",".join(w for w, _ in C["ecrivains"].most_common(4))))
    P("\norigine x zone de la valeur (appels) :")
    for (k, zc, z), n in sorted(croise.items(), key=lambda x: -x[1]): P("  %-8s %-20s %-45s %9d" % (k, zc, z, n))
    # classement des sites pour les etapes B-D
    cls = collections.Counter(); clsn = collections.Counter(); det = {}
    for S in sites.values():
        conv_or = set()
        for oz, n in S["origines"].items(): pass
        zs_ = {z for z in S["zones"]}
        convz = [z for z in zs_ if z in CONVZ]
        orz = {o.split(" ", 1)[1] for o in S["origines"]}
        if S["convertis"] == 0: c = "jamais de conversion (talon superflu sur ce parcours)"
        elif orz <= {"ROM donnees", "ROM tables natives", "ROM autre"}: c = "conversions venues de tables ROM seulement"
        elif orz <= {"RAM", "RAM du portage"}: c = "conversions venues de cases RAM seulement"
        elif "inconnue" in orz and len(orz) == 1: c = "valeur calculee (pas de lecture correspondante)"
        else: c = "mixte (" + "+".join(sorted(orz)) + ")"
        cls[S["talon"][:2] == "CC" and "code" or "donnees", c] += 1; clsn[S["talon"][:2] == "CC" and "code" or "donnees", c] += S["n"]
        S["classe"] = c
    P("\nclassement des sites actifs :")
    for (k, c), n in sorted(cls.items()): P("  %-8s %-65s %4d sites %9d appels" % (k, c, n, clsn[k, c]))
    P("\nsites a origine inconnue ou mixte :")
    for S in sorted(sites.values(), key=lambda S: -S["n"]):
        if S["classe"].startswith("valeur") or S["classe"].startswith("mixte"):
            P("  %s %-9s va %s n=%8d conv=%5.1f%% %s | %s" % (S["site"], S["talon"], S["va"], S["n"], 100 * S["convertis"] / S["n"], S["src"][:60],
              ", ".join("%s:%d" % x for x in S["origines"].most_common(4))))
    # tables ROM : grappes contigues (ecart <= 16 octets)
    rc = sorted(a for a, C in cells.items() if C["zone"].startswith("ROM"))
    gr = []
    for a in rc:
        if gr and a - gr[-1][-1] <= 16: gr[-1].append(a)
        else: gr.append([a])
    P("\ntables ROM (grappes de cases lues, ecart <= 16 o) : %d grappes, %d cases" % (len(gr), len(rc)))
    nconv = sum(1 for g in gr if any(cells[a]["convertis"] for a in g))
    P("  grappes avec au moins une conversion : %d ; cases ROM dont la valeur est convertie : %d ; dont la valeur est deja 68K / code : %d" % (
      nconv, sum(1 for a in rc if cells[a]["convertis"]), sum(1 for a in rc if not cells[a]["convertis"])))
    for g in sorted(gr, key=lambda g: -sum(cells[a]["n"] for a in g))[:25]:
        zz = collections.Counter()
        for a in g: zz.update(cells[a]["zones"])
        P("  $%06x-$%06x (PS2 %06x) %4d cases %9d appels : %s" % (g[0], g[-1] + 3, g[0] - DATA_ADD, len(g), sum(cells[a]["n"] for a in g),
          ", ".join("%s %d" % x for x in zz.most_common(3))))
    js["tables_rom"] = [{"debut": "%06x" % g[0], "fin": "%06x" % (g[-1] + 4), "ps2": "%06x" % (g[0] - DATA_ADD), "cases": len(g),
                         "appels": sum(cells[a]["n"] for a in g)} for g in gr]
    for S in js["sites"]: S["classe"] = sites[int(S["site"], 16)]["classe"]
    json.dump(js, open(pref + ".json", "w"), indent=1)
    P("\ncases RAM : detail (toutes)")
    for C in sorted((C for C in cells.values() if C["zone"].startswith("RAM")), key=lambda C: -C["n"]):
        P("  %s n=%8d conv=%8d valeurs=%3d %s | ecrivains %s" % (C["case"], C["n"], C["convertis"], len(C["valeurs"]),
          ",".join("%s" % z for z, _ in C["zones"].most_common(2)),
          "; ".join("%s=%s" % (w, ecr_info.get(w, "?")[:60]) for w, _ in C["ecrivains"].most_common(2))))
    o.close()
    print(open(pref + ".txt").read())

if __name__ == "__main__":
    main()
