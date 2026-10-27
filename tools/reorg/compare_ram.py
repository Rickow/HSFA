#!/usr/bin/env python3
"""COMPARAISON DE RAM TRADUCTION <-> ARCADE (ETAPE A : oracle des etapes B-E).
Usage : compare_ram.py SORTIE [--tournee DIR_REF DIR_TR] [--attr DIR_REF DIR_TR] ...
  --tournee : vidages cN de tournee.lua (DUMPC/DOUT), apparies par numero de manche ET verifies (decor $FF8100,
              perso de J2 $FF8902) ; les manches dont le decor ou l'adversaire different sont ecartees.
  --attr    : vidages <etat>_<occurrence>.bin de runs/attr.lua (points synchronises sur les changements de mode).
Vidages : RAM $FF0000-$FFFFFF, 64 Ko, mots gros-boutistes (vue du 68000).
Pour chaque variable A5 (adresse traduction/taille, carte_vars.py -> vars.json) et chaque champ des structures
joueur ($FF8400/$FF8800, deplacements A6 < $400), l'adresse arcade est prise du vote des instructions alignees
('paires'), sinon de la RECETTE (octet XOR 1, mot meme adresse, long meme adresse moities echangees, zone basse
relogee) ; le modele type (typed_rule.py) est evalue en parallele. Valeur traduction lue selon la recette :
  B : octet a t ; W : mot a t ; L : (mot(t+2) << 16) | mot(t)
Formes alternatives essayees pour un long : 's16x2' (long natif = mots a leur place) et 'u8x4' (octets XOR 1).
Verdicts : identique / identique (nul) / identique sous une autre forme / different / propre au portage."""
import os, sys, json, collections
A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = json.load(open(os.path.join(A, "vars.json")))
B0 = 0xFF0000

def rd(m, a, T):
    o = a - B0
    if o < 0 or o + {"B": 1, "W": 2, "L": 4}[T] > len(m): return None
    if T == "B": return m[o]
    if T == "W": return (m[o] << 8) | m[o + 1]
    return int.from_bytes(m[o:o + 4], "big")
def tval(m, t, T, forme="recette"):
    """valeur 'arcade' d'une variable de la traduction selon la forme de rangement"""
    if T == "W" and forme == "u8x2":
        v = rd(m, t, "W"); return None if v is None else ((v >> 8) | ((v & 0xff) << 8))
    if T != "L" or forme == "s16x2": return rd(m, t, T)
    if forme == "recette":
        lo, hi = rd(m, t, "W"), rd(m, t + 2, "W")
        return None if lo is None or hi is None else (hi << 16) | lo
    if forme == "u8x4":
        o = t - B0
        if o < 0 or o + 4 > len(m): return None
        return int.from_bytes(bytes(m[o + (k ^ 1)] for k in range(4)), "big")

def paires_tournee(dref, dtr):
    out = []
    for n in range(1, 100):
        pa, pt = os.path.join(dref, "c%d" % n), os.path.join(dtr, "c%d" % n)
        if not (os.path.exists(pa) and os.path.exists(pt)): continue
        a, t = open(pa, "rb").read(), open(pt, "rb").read()
        ia = (rd(a, 0xFF8100, "W"), a[0x8902]); it = (rd(t, 0xFF8100, "W"), t[0x8902 ^ 1])
        out.append(("manche%d" % n, a, t, ia == it, "decor %04x adv %02x / %04x %02x" % (ia + it)))
    return out
def paires_synchro(dref, dtr):
    """vidages de runs/synchro.lua : m<manche>_s<image>.bin, index.txt (manche image k decor adversaire)"""
    def idx(d):
        r = {}
        for l in open(os.path.join(d, "index.txt")):
            m, s_, k, dec, adv = l.split(); r["m%s_s%s" % (m, s_)] = (dec, adv)
        return r
    ia, it = idx(dref), idx(dtr); out = []
    for lab in sorted(ia, key=lambda x: [int(v) for v in x[1:].split("_s")]):
        if lab not in it: continue
        a, t = open(os.path.join(dref, lab + ".bin"), "rb").read(), open(os.path.join(dtr, lab + ".bin"), "rb").read()
        out.append(("sync_" + lab, a, t, ia[lab] == it[lab], "decor/adv %s %s / %s %s" % (ia[lab] + it[lab])))
    return out

def paires_attr(dref, dtr):
    out = []
    for f in sorted(os.listdir(dref)):
        if not f.endswith(".bin") or not os.path.exists(os.path.join(dtr, f)): continue
        if f.startswith("0000_0000_0000"): continue             # amorcage (RAM en cours d'effacement)
        out.append(("attr_" + f[:-4], open(os.path.join(dref, f), "rb").read(), open(os.path.join(dtr, f), "rb").read(), True, ""))
    return out

def couverts(src):
    """octets de RAM touches par l'arcade (acces A5 de toutes tailles)"""
    s = set()
    for k in src:
        a, T = k.split("/"); a = int(a, 16)
        for i in range({"B": 1, "W": 2, "L": 4}[T]): s.add(a + i)
    return s

def analyse(vars_, base_list, P, arc_couv, reg):
    res = {}
    for k, e in vars_.items():
        t0, T = k.split("/"); t0 = int(t0, 16)
        prim = e["paires"] if e["paires"] is not None else e["recette"]
        cands = {"paires": e["paires"], "recette": e["recette"], "type": e["type"]}
        formes = ("recette", "s16x2", "u8x4") if T == "L" else (("recette", "u8x2") if T == "W" else ("recette",))
        eq = collections.Counter(); eqnz = collections.Counter(); n = 0; nul = 0; ex = []; ptr = 0; ndiff = 0; tag = 0
        for lab, ma, mt, ok, _ in P:
            if not ok: continue
            for base in base_list:
                t = t0 + base; tv = tval(mt, t, T)
                av = rd(ma, prim + base, T)
                if tv is None or av is None: continue
                n += 1
                if tv == 0 and av == 0: nul += 1
                for cn, ca in cands.items():
                    if ca is None: continue
                    a2 = rd(ma, ca + base, T)
                    for f in formes:
                        if a2 is not None and tval(mt, t, T, f) == a2:
                            eq[cn, f] += 1
                            if a2: eqnz[cn, f] += 1
                if tv != av:
                    ndiff += 1
                    if T == "L" and (tv >> 24) == 1 and (tv & 0xFFFFFF) == av: tag += 1
                    if T == "L" and (0x1000 <= tv < 0x400000 or 0xFF0000 <= tv <= 0xFFFFFF) and (av < 0x400000 or 0xFF0000 <= av <= 0xFFFFFF): ptr += 1
                if tv != av and len(ex) < 4: ex.append("%s%s: trad %x arcade %x" % (lab, "" if not base else "+%x" % base, tv, av))
        prim_n = "paires" if e["paires"] is not None else "recette"
        adr_arc = prim if reg == 6 else prim
        portage = False
        if reg == 5:
            if 0xFF4000 <= t0 < 0xFF5000: portage = True
            elif e["paires"] is None and not any((prim + i) in arc_couv for i in range({"B": 1, "W": 2, "L": 4}[T])): portage = True
        else:
            if e["paires"] is None and not any((prim + i) in arc_couv for i in range({"B": 1, "W": 2, "L": 4}[T])): portage = True
        if n == 0: st = "non compare"
        elif portage: st = "propre au portage"
        elif eq[prim_n, "recette"] == n: st = "identique (nul)" if nul == n else "identique"
        else:
            alt = [(c, f) for (c, f), m in eq.items() if m == n]
            altnz = [(c, f) for (c, f), m in eqnz.items() if m > 0 and (c, f) != (prim_n, "recette")]
            if alt: st = "identique sous %s" % ",".join("%s/%s" % x for x in sorted(alt))
            elif eqnz[prim_n, "recette"] > 0: st = "dynamique (egal quand l'etat est le meme)"
            elif eq[prim_n, "recette"] >= 0.9 * n: st = "dynamique (rarement non nul)"
            elif ptr == ndiff: st = "pointeur (valeur propre a la disposition ROM)"
            elif tag == ndiff: st = "pointeur materiel etiquete $01 (convention du banc)"
            elif altnz: st = "forme %s (dynamique)" % ",".join("%s/%s" % x for x in sorted(altnz))
            else: st = "structurel (jamais egal)"
        res[k] = {"statut": st, "arcade": "%06x" % prim if reg == 5 else "%03x" % prim, "source": prim_n, "votes": e["votes"],
                  "comparaisons": n, "egales": eq[prim_n, "recette"], "egales_non_nulles": eqnz[prim_n, "recette"], "nulles": nul, "acces_trad": e["n"],
                  "egal_par": {"%s/%s" % c: m for c, m in eq.items()}, "exemples": ex}
    return res

def zones(P):
    """comparaison brute par bloc de 256 octets (mots non nuls des deux cotes)"""
    Z = {}
    for lab, ma, mt, ok, _ in P:
        if not ok: continue
        for blk in range(0, 0x10000, 0x100):
            z = Z.setdefault(blk, collections.Counter())
            for o in range(blk, blk + 0x100, 2):
                wa, wt = (ma[o] << 8) | ma[o + 1], (mt[o] << 8) | mt[o + 1]
                if wa == 0 and wt == 0: continue
                z["mots"] += 1
                if wa == wt: z["identite"] += 1
                elif wa == ((wt >> 8) | ((wt & 0xff) << 8)) & 0xffff: z["octets_echanges"] += 1
                else:
                    o2 = o ^ 2                                  # moitie de long echangee ?
                    if o2 < 0x10000 and ((mt[o2] << 8) | mt[o2 + 1]) == wa: z["moities_echangees"] += 1
                    else: z["differents"] += 1
    return Z

def main():
    pref = sys.argv[1]; P = []
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--tournee": P += paires_tournee(sys.argv[i + 1], sys.argv[i + 2]); i += 3
        elif sys.argv[i] == "--synchro": P += paires_synchro(sys.argv[i + 1], sys.argv[i + 2]); i += 3
        elif sys.argv[i] == "--attr": P += paires_attr(sys.argv[i + 1], sys.argv[i + 2]); i += 3
        else: raise SystemExit("argument ? " + sys.argv[i])
    ok = [p for p in P if p[3]]
    arc5 = couverts(V["arc_a5"]); arc6 = couverts(V["arc_a6"])
    r5 = analyse(V["var_a5"], [0], P, arc5, 5)
    r6 = analyse(V["var_a6"], [0xFF8400, 0xFF8800], P, arc6, 6)
    Z = zones(P)
    js = {"paires": [[p[0], p[3], p[4]] for p in P], "a5": r5, "joueurs": r6,
          "zones": {"%06x" % (B0 + b): dict(z) for b, z in Z.items() if z["mots"]}}
    json.dump(js, open(pref + ".json", "w"), indent=0)
    with open(pref + ".tsv", "w") as f:
        f.write("type\tvariable_trad\tadresse_arcade\tsource\tvotes\tstatut\tcomparaisons\tegales\tnulles\tacces_trad\tegal_par\texemples\n")
        for nm, R in (("A5", r5), ("joueur", r6)):
            for k in sorted(R):
                e = R[k]
                f.write("%s\t%s\t%s\t%s\t%d\t%s\t%d\t%d\t%d\t%d\t%s\t%s\n" % (nm, k, e["arcade"], e["source"], e["votes"], e["statut"],
                        e["comparaisons"], e["egales"], e["nulles"], e["acces_trad"],
                        " ".join("%s=%d" % x for x in sorted(e["egal_par"].items())), " | ".join(e["exemples"])))
    o = open(pref + ".txt", "w")
    def Pr(*x): print(*x, file=o)
    Pr("paires de vidages : %d retenues sur %d" % (len(ok), len(P)))
    for p in P:
        if not p[3]: Pr("  ecartee : %s (%s)" % (p[0], p[4]))
    for nm, R in (("variables A5", r5), ("champs joueur (J1+J2)", r6)):
        c = collections.Counter(e["statut"].split(" sous")[0].split(" (")[0].split(" ")[0] + (" sous ..." if " sous" in e["statut"] else "") + ((" " + e["statut"].split(" (")[1].rstrip(")")) if "(" in e["statut"] and " sous" not in e["statut"] else "") for e in R.values())
        Pr("\n%s : %d (adresse traduction/taille)" % (nm, len(R)))
        for s, n in c.most_common(): Pr("  %-28s %5d" % (s, n))
        alt = collections.Counter(e["statut"] for e in R.values() if " sous" in e["statut"] or e["statut"].startswith("forme"))
        for s, n in alt.most_common(8): Pr("     %-50s %4d" % (s, n))
        srcs = collections.Counter((e["source"], e["statut"].split(" ")[0]) for e in R.values())
        Pr("  par source d'adresse : " + ", ".join("%s/%s %d" % (a, b, n) for (a, b), n in sorted(srcs.items())))
    tot = collections.Counter()
    for z in Z.values(): tot.update(z)
    Pr("\nRAM brute $FF0000-$FFFFFF (mots non nuls d'un cote au moins, toutes paires) : %d" % tot["mots"])
    for k in ("identite", "octets_echanges", "moities_echangees", "differents"):
        Pr("  %-18s %8d (%.1f %%)" % (k, tot[k], 100 * tot[k] / max(1, tot["mots"])))
    Pr("\npar zone de 4 Ko (identite / octets echanges / moities / differents, en % des mots non nuls) :")
    for zb in range(0, 0x10000, 0x1000):
        t = collections.Counter()
        for b in range(zb, zb + 0x1000, 0x100):
            if b in Z: t.update(Z[b])
        if t["mots"]:
            Pr("  $%06x %7d mots : %5.1f %5.1f %5.1f %5.1f" % (B0 + zb, t["mots"], *(100 * t[k] / t["mots"] for k in ("identite", "octets_echanges", "moities_echangees", "differents"))))
    o.close(); print(open(pref + ".txt").read())

if __name__ == "__main__":
    main()
