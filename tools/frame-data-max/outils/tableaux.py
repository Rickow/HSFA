"""(frame_data_max) Tableaux comparés PSP / Upper : resultats/<cand>/frame_data_<perso>.tsv et .md, ecarts.tsv, bilan.md.
Appelé par fd.py mesure <candidat> (après fd.py upper pour chaque perso / isme)."""
import collections, json, os, re
import fd, coups as C

ICI = fd.ICI
PERSOS = ("eagle", "maki", "yun", "ingrid")
NOMS = {"eagle": "Eagle", "maki": "Maki", "yun": "Yun", "ingrid": "Ingrid"}
G = ["demarrage", "actif", "morceaux", "recuperation", "total", "avantage_touche", "avantage_garde", "degats", "touches", "contact", "pre_special"]
NUM = ["demarrage", "actif", "recuperation", "total", "avantage_touche", "avantage_garde", "degats", "touches", "contact", "pre_special"]
TITRE = {"demarrage": "dém.", "actif": "actifs", "morceaux": "morceaux actifs (trous)", "recuperation": "récup.", "total": "total",
         "avantage_touche": "av. touche", "avantage_garde": "av. garde", "degats": "dégâts", "touches": "touches", "contact": "contact",
         "pre_special": "normal avant spécial"}


def valeurs(c, tests, cote):
    """grandeurs d'un coup d'un côté ; tests = {lettre: trace}"""
    v, src = {}, {}
    # images de ralentissement du 68000 (Upper) par essai, dans la fenêtre mesurée : « w/h/b » (à vide / touche / garde)
    if cote == "upper":
        ral = {e: fd.mesure(tests[e], c["cat"]).get("ralentis") for e in "whb" if e in tests}
        if any(ral.values()):
            v["_ralentis"] = "/".join("-" if ral.get(e) is None else str(ral[e]) for e in "whb")
    base = "w" if "w" in tests else ("h" if "h" in tests else None)
    if base:
        m = fd.mesure(tests[base], c["cat"])
        if "i0" not in m:
            return {"_absent": True}
        for g in ("demarrage", "actif", "morceaux", "recuperation", "total", "pre_special"):
            if g in m:
                v[g] = m[g]
        if c["cat"] == "saut":
            v.pop("recuperation", None); v.pop("total", None)
    if "h" in tests:
        m = fd.mesure(tests["h"], c["cat"])
        if m.get("degats"):
            v["degats"], v["touches"] = m["degats"], m["touches"]
            if "contact" in m:
                v["contact"] = m["contact"]
            if "avantage" in m and c["cat"] not in ("saut",):
                v["avantage_touche"] = ("chute %+d" % m["avantage"]) if m.get("chute") else m["avantage"]
        else:
            v["_sans_contact"] = True
    if "b" in tests:
        m = fd.mesure(tests["b"], c["cat"])
        if "avantage" in m:
            v["avantage_garde"] = ("chute %+d" % m["avantage"]) if m.get("chute") else m["avantage"]
        if m.get("degats"):
            v["_degats_garde"] = m["degats"]
    return v


def num(x):
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        mm = re.search(r"[+-]?\d+$", x)
        return int(mm.group(0)) if mm else None
    return None


def charge(cand, perso, ism, mode=None):
    cache = os.path.join(ICI, "psp_cache", "%s_%s.json" % (perso, ism))
    log = os.path.join(ICI, "essais", os.path.basename(os.path.normpath(cand)), "%s_%s" % (perso, ism), "log.txt")
    if not os.path.exists(cache):
        return None
    P = json.load(open(cache))
    U, X = fd.traces_upper(log, mode) if os.path.exists(log) else ({}, {})
    return P, U, X


def comparer(cand, mode=None):
    lignes = []
    for perso in PERSOS:
        for ism in "AXV":
            d = charge(cand, perso, ism, mode)
            if not d:
                continue
            P, U, X = d
            cs = C.pour_ism(perso, ism)
            parnom = {c["nom"]: c for c in cs}
            for c in cs:
                tp = {e: P[c["id"] + e]["tr"] for e in c["essais"] if c["id"] + e in P}
                if not tp:
                    continue
                tu = {e: U[c["id"] + e] for e in c["essais"] if c["id"] + e in U}
                posture = ""
                if "b" in tp and c["id"] + "c" in U:
                    # posture de garde Upper : celle qui pare comme le mannequin PSP (réaction de J2, pas plus de vie perdue que sur PSP)
                    mp = fd.mesure(tp["b"], c["cat"])
                    def pare(tr):
                        # J2 a paré : réaction de garde ($7 = 4 : 02020004) et aucune réaction de coup reçu (02020002)
                        e2 = {x[6] for x in tr}
                        return "02020004" in e2 and "02020002" not in e2
                    if c["id"] + "b" in U and pare(U[c["id"] + "b"]):
                        posture = "debout"
                    elif pare(U[c["id"] + "c"]):
                        tu["b"] = U[c["id"] + "c"]; posture = "accroupie"
                    else:
                        posture = "aucune ne pare"
                if not tu and not X:
                    continue        # Upper pas encore joué pour ce perso / isme
                dist = P.get(c["id"] + "h", P.get(c["id"] + "w"))["dist"]
                vp, vu = valeurs(c, tp, "psp"), (valeurs(c, tu, "upper") if tu else {"_non_joue": True})
                note = []
                if c["cat"] == "proche":
                    # proche : même animation que le coup de loin -> sans objet
                    loin = parnom.get(c["nom"].replace("proche", "debout"))
                    if loin and loin["id"] + "w" in P and fd.pas_actif(P[loin["id"] + "w"]["tr"], "normal") == fd.pas_actif(tp.get("h", []), "proche"):
                        continue
                exc = [X[c["id"] + e] for e in c["essais"] if c["id"] + e in X]
                if exc:
                    note.append("exception Upper pc=%s" % exc[0])
                if vp.get("_absent"):
                    note.append("ne sort pas sur PSP")
                if vu.get("_absent"):
                    note.append("ne sort pas dans Upper")
                if vu.get("_non_joue"):
                    note.append("Upper non joué")
                if vp.get("_sans_contact"):
                    note.append("pas de contact PSP à 0x%x" % dist)
                if vu.get("_sans_contact") and not vp.get("_sans_contact"):
                    note.append("pas de contact Upper")
                if vp.get("_degats_garde") or vu.get("_degats_garde"):
                    note.append("dégâts en garde %s / %s" % (vp.get("_degats_garde", 0), vu.get("_degats_garde", 0)))
                if c["note"]:
                    note.append(c["note"])
                if posture and posture != "debout":
                    note.append("garde Upper %s" % posture)
                ec = {}
                for g in NUM:
                    a, b = num(vp.get(g)), num(vu.get(g))
                    if a is not None and b is not None:
                        ec[g] = b - a
                    elif (a is None) != (b is None) and not vp.get("_absent") and not vu.get("_absent"):
                        ec[g] = "?"
                if vp.get("morceaux") is not None and vu.get("morceaux") is not None and vp["morceaux"] != vu["morceaux"]:
                    ec["morceaux"] = "≠"
                if isinstance(vp.get("avantage_touche"), str) != isinstance(vu.get("avantage_touche"), str) and "avantage_touche" in vp and "avantage_touche" in vu:
                    ec["avantage_touche"] = "chute≠"
                if vp.get("_absent") or vu.get("_absent") or vu.get("_non_joue") or exc:
                    verdict = "absent/exception"
                else:
                    nums = [abs(x) for x in ec.values() if isinstance(x, int)]
                    autres = [x for x in ec.values() if not isinstance(x, int)]
                    mx = max(nums) if nums else 0
                    if mx == 0 and not autres:
                        verdict = "identique"
                    elif mx <= 1 and not autres:
                        verdict = "écart 1"
                    else:
                        verdict = "écart >1"
                lignes.append(dict(perso=perso, ism=ism, id=c["id"], coup=c["nom"], cat=c["cat"], dist="0x%x" % dist, psp=vp, upper=vu,
                                   ecart=ec, verdict=verdict, note="; ".join(note), ralentis=vu.get("_ralentis", "")))
    return lignes


def cel(v):
    if v is None:
        return ""
    return str(v)


def ecrire(cand, lignes, mode="tours"):
    nc = os.path.basename(os.path.normpath(cand))
    out = os.path.join(ICI, "resultats", nc) if mode == "tours" else os.path.join(ICI, "resultats", nc, "images")
    sources = sorted(set(v for k, v in fd.SOURCE.items() if "/%s/" % nc in k))
    unite = ("**tours de jeu** (Upper : relevé au début de chaque tour, images de ralentissement du 68000 retirées et comptées à part, "
             "colonne `ralentis` = w/h/b : à vide / touche / garde ; source des traces Upper : %s)" % ", ".join(sources)) if mode == "tours" else \
            ("**images brutes** Upper (ancien mode, une ligne par image MAME, ralentissements compris ; colonne `ralentis` = images sans "
             "tour de jeu dans la fenêtre mesurée) ; PSP en tours")
    os.makedirs(out, exist_ok=True)
    cols = ["perso", "ism", "id", "coup", "cat", "dist"] + ["%s_%s" % (g, s) for g in G for s in ("psp", "upper", "ecart")] + ["ralentis_upper", "verdict", "note"]
    for perso in PERSOS:
        L = [l for l in lignes if l["perso"] == perso]
        if not L:
            continue
        with open(os.path.join(out, "frame_data_%s.tsv" % perso), "w") as f:
            f.write("\t".join(cols) + "\n")
            for l in L:
                r = [l[k] for k in ("perso", "ism", "id", "coup", "cat", "dist")]
                for g in G:
                    r += [cel(l["psp"].get(g)), cel(l["upper"].get(g)), cel(l["ecart"].get(g))]
                r += [l["ralentis"], l["verdict"], l["note"]]
                f.write("\t".join(str(x) for x in r) + "\n")
        md = ["# Données d'images — %s (PSP SFA3 MAX / Upper MAX `%s`)" % (NOMS[perso], nc), "",
              "Unité : " + unite + " (voir RAPPORT.md §1). Cellule : `v` = même valeur des deux côtés ; `P / U` = PSP / Upper quand elles diffèrent. "
              "Adversaire Ryu (A), distance imposée = colonne `dist` (px). Tableau complet (écarts, morceaux actifs) : `frame_data_%s.tsv`." % perso, ""]
        for ism in "AXV":
            LI = [l for l in L if l["ism"] == ism]
            if not LI:
                continue
            cpt = collections.Counter(l["verdict"] for l in LI)
            md += ["## %s-isme (%s)" % (ism, ", ".join("%s %d" % kv for kv in sorted(cpt.items()))), "",
                   "| coup | dist | dém. | actifs (trous) | récup. | total | av. touche | av. garde | dégâts | touches | ralentis | verdict | note |",
                   "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
            for l in LI:
                def c2(g):
                    a, b = l["psp"].get(g), l["upper"].get(g)
                    if a is None and b is None:
                        return ""
                    return cel(a) if a == b else "**%s / %s**" % (cel(a) if a is not None else "–", cel(b) if b is not None else "–")
                act = c2("morceaux") if ("(" in str(l["psp"].get("morceaux", "")) or "(" in str(l["upper"].get("morceaux", ""))) else c2("actif")
                md.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    l["coup"], l["dist"], c2("demarrage"), act, c2("recuperation"), c2("total"), c2("avantage_touche"), c2("avantage_garde"),
                    c2("degats"), c2("touches"), l["ralentis"], l["verdict"], l["note"]))
            md.append("")
        open(os.path.join(out, "frame_data_%s.md" % perso), "w").write("\n".join(md) + "\n")
    # écarts (une ligne par grandeur différente)
    with open(os.path.join(out, "ecarts.tsv"), "w") as f:
        f.write("perso\tism\tid\tcoup\tgrandeur\tpsp\tupper\tecart\tralentis_upper\tverdict\tnote\n")
        for l in lignes:
            for g, e in l["ecart"].items():
                if e != 0:
                    f.write("\t".join(str(x) for x in (l["perso"], l["ism"], l["id"], l["coup"], g, cel(l["psp"].get(g)), cel(l["upper"].get(g)), e,
                                                       l["ralentis"], l["verdict"], l["note"])) + "\n")
    cpt = collections.Counter((l["perso"], l["verdict"]) for l in lignes)
    tot = collections.Counter(l["verdict"] for l in lignes)
    nral = sum(1 for l in lignes if l["ralentis"])
    b = ["# Bilan `%s` (mesure en %s)" % (nc, "tours de jeu" if mode == "tours" else "images brutes"), "", "Unité : " + unite + ".",
         "Couples dont un essai Upper contient au moins une image de ralentissement : %d." % nral, "", "| perso | coups×ismes | identique | écart 1 | écart >1 | absent/exception |", "|---|---|---|---|---|---|"]
    for p in PERSOS:
        n = sum(v for (pp, _), v in cpt.items() if pp == p)
        b.append("| %s | %d | %d | %d | %d | %d |" % (NOMS[p], n, cpt[(p, "identique")], cpt[(p, "écart 1")], cpt[(p, "écart >1")], cpt[(p, "absent/exception")]))
    b.append("| **total** | %d | %d | %d | %d | %d |" % (len(lignes), tot["identique"], tot["écart 1"], tot["écart >1"], tot["absent/exception"]))
    b += ["", "## Écarts de plus d'un tour et coups absents", "", "| perso | isme | coup | grandeurs (PSP → Upper) | note |", "|---|---|---|---|---|"]
    for l in lignes:
        if l["verdict"] in ("écart >1", "absent/exception"):
            gs = ", ".join("%s %s → %s" % (TITRE[g], cel(l["psp"].get(g)), cel(l["upper"].get(g))) for g, e in l["ecart"].items() if e != 0)
            b.append("| %s | %s | %s | %s | %s |" % (NOMS[l["perso"]], l["ism"], l["coup"], gs, l["note"] + (" ; ralentis %s" % l["ralentis"] if l["ralentis"] else "")))
    open(os.path.join(out, "bilan.md"), "w").write("\n".join(b) + "\n")
    json.dump(lignes, open(os.path.join(out, "lignes.json"), "w"), ensure_ascii=False)
    print("\n".join(b[:12]))


def tout(cand, mode="tours"):
    ecrire(cand, comparer(cand, mode), mode)
