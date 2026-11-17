#!/usr/bin/env python3
"""test_selection.py -- checks of the builder's game selection (--jeux, the window's check boxes), WITHOUT game data,
without Tk and without building anything (hsfa_build.main is replaced by a recorder). Standard library only.

  python3 tools/constructeur/test_selection.py [-v]

1. selection(): for every set of games the builder offers (with and without the PSP ISO), the plan of hsfa_build holds
   the archive of every game asked for; the games whose archive comes along (Hyper + Arcade -> Upper and Hyper, Upper
   MAX -> Upper) and the steps run without their archive (Hyper -> son_upper, gfx_upper of Upper) are read from that
   plan; the per-game durations add up to the total; no temporary folder is left behind;
2. --jeux: order and case normalised, hyperarcademax refused (core patch 0033), uppermax refused without the PSP ISO;
3. compatibility: without --jeux the build runs « --jeux sfa3,upper,hyper » (+ « ,uppermax --psp-iso » with the PSP
   ISO), as before; a PSP ISO given without Upper MAX chosen is not passed on;
4. end of build: « Durée totale » line (log and hsfa-travail/journal.txt), failure included; « Done: N games » counts
   the zips of the games built;
5. window logic (etat_cases): a game pulled in by another is ticked and greyed, Upper MAX greyed without the PSP ISO;
   durations under the boxes (durees_cases): 5 games = « Total ≈ 12 min », rounded parts adding up to the total;
6. main(): --jeux reaches the console and the window, a wrong --jeux stops with exit code 2.
Exit code 0 if everything passes.
"""
import io, os, shutil, sys, tempfile
from contextlib import redirect_stdout, redirect_stderr
from itertools import combinations

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import hsfa_constructeur as C

H = C._hsfa_build()
ECHECS = []
VERBEUX = "-v" in sys.argv


def verifie(nom, ok, detail=""):
    if not ok:
        ECHECS.append(nom)
        print("ECHEC %s %s" % (nom, detail))
    elif VERBEUX:
        print("ok    %s" % nom)
    return ok


def plans_temporaires():
    t = tempfile.gettempdir()
    return {d for d in os.listdir(t) if d.startswith("hsfa_plan_")}


def test_selection():
    avant = plans_temporaires()
    n = 0
    for k in range(1, len(C.JEUX_CHOIX) + 1):
        for combo in combinations(C.JEUX_CHOIX, k):
            for psp in ((None, "p.iso") if "uppermax" not in combo else ("p.iso",)):
                s = C.selection(list(combo), psp)
                nom = "%s psp=%s" % (",".join(combo), bool(psp))
                verifie("jeux " + nom, s["jeux"] == list(combo), s["jeux"])
                verifie("archives demandees " + nom, set(combo) <= set(s["archives"]), s["archives"])
                verifie("aussi " + nom, set(s["aussi"]) == set(s["archives"]) - set(combo), s["aussi"])
                verifie("etapes sans zip " + nom, not set(s["etapes"]) & set(s["archives"]), s["etapes"])
                verifie("duree " + nom, abs(sum(x for _l, x in s["durees"]) - s["total"]) < 1e-6 and s["total"] > 0)
                attendu = set()
                if "hyperarcade" in combo: attendu |= {"upper", "hyper"}
                if "uppermax" in combo: attendu |= {"upper"}
                verifie("entraines " + nom, set(s["aussi"]) == attendu - set(combo), (s["aussi"], attendu))
                if "hyper" in combo and not {"upper", "uppermax", "hyperarcade"} & set(combo):
                    verifie("hyper sans upper : etapes d'Upper " + nom, "gfx_upper" in s["etapes"].get("upper", [])
                            and s["pour"]["upper"] == ["hyper"], s["etapes"])
                else:
                    verifie("pas d'etapes seules " + nom, not s["etapes"], s["etapes"])
                n += 1
    verifie("aucun dossier temporaire laisse", plans_temporaires() <= avant, plans_temporaires() - avant)
    s = C.selection(["hyperarcade"])
    verifie("hyperarcade : 3 zips", [C.zip_de(a) for a in s["archives"]] == ["sfa3uhsfa", "sfa3hhsfa", "sfa3hahsfa"],
            s["archives"])
    verifie("texte : Upper et Hyper construits aussi", len(C.texte_selection(s)) == 1
            and all("Upper, Hyper : construits aussi, zips" in l and "Hyper + Arcade" in l for l in C.texte_selection(s)),
            C.texte_selection(s))
    verifie("hyperarcademax jamais propose", "hyperarcademax" not in C.JEUX_CHOIX)
    print("selection : %d combinaisons" % n)


def test_jeux():
    verifie("--jeux ordre", C.verifie_jeux("Hyper, sfa3,hyper") == ["sfa3", "hyper"])
    verifie("--jeux uppermax avec PSP", C.verifie_jeux("uppermax,sfa3", "p.iso") == ["sfa3", "uppermax"])
    for texte, psp in (("hyperarcademax", "p.iso"), ("uppermax", None), ("bidule", None), ("", None), (",", None)):
        try:
            C.verifie_jeux(texte, psp); verifie("--jeux %r refuse" % texte, False)
        except ValueError as x:
            verifie("--jeux %r refuse" % texte, bool(str(x)))
    verifie("defaut", C.jeux_construits() == ["sfa3", "upper", "hyper"])
    verifie("defaut avec PSP", C.jeux_construits("p.iso") == ["sfa3", "upper", "hyper", "uppermax"])
    verifie("temps_texte", [C.temps_texte(x) for x in (5, 754, 3725)] == ["5 s", "12 min 34 s", "1 h 02 min 05 s"])
    verifie("chrono_texte", [C.chrono_texte(x) for x in (5, 754, 3725)] == ["0:05", "12:34", "1:02:05"])


def test_construit():
    T = tempfile.mkdtemp(prefix="hsfa_test_sel_")
    vrai_main, vu = H.main, []
    def faux_main():                                       # comme hsfa_build : cree hsfa-travail/
        vu.append(list(sys.argv))
        os.makedirs(os.path.join(sys.argv[sys.argv.index("--sortie") + 1], H.TRAVAIL), exist_ok=True)
        return 0
    H.main = faux_main
    try:
        img = os.path.join(T, "a.iso"); psp = os.path.join(T, "p.iso")
        for p in (img, psp): open(p, "wb").write(b"x")
        cas = [(None, None, "sfa3,upper,hyper", False), (None, psp, "sfa3,upper,hyper,uppermax", True),
               (["hyperarcade"], psp, "hyperarcade", False), (["sfa3", "hyper"], None, "sfa3,hyper", False),
               (["uppermax", "hyper"], psp, "hyper,uppermax", True)]
        for jeux, ps, attendu, avec_psp in cas:
            del vu[:]; lignes = []
            S = os.path.join(T, "s_%s_%s" % (attendu.replace(",", "_"), bool(ps)))
            with redirect_stdout(io.StringIO()):
                r = C.construit(img, S, ps, journal=lignes.append, jeux=jeux)
            a = vu[0][1:] if vu else []
            nom = "construit %s psp=%s" % (jeux, bool(ps))
            verifie(nom + " : code 0", r == 0)
            verifie(nom + " : --jeux " + attendu, a[a.index("--jeux") + 1] == attendu if "--jeux" in a else False, a)
            verifie(nom + " : --psp-iso %s" % avec_psp, ("--psp-iso" in a) == avec_psp, a)
            verifie(nom + " : ligne Durée totale", any(l.startswith("Durée totale / total time: ") for l in lignes), lignes)
            j = open(os.path.join(S, "hsfa-travail", "journal.txt"), encoding="utf-8").read()
            verifie(nom + " : Durée totale dans journal.txt", "Durée totale / total time" in j)
        # echec de hsfa_build : la ligne de duree est la aussi
        def main_qui_casse():
            raise RuntimeError("essai")
        H.main = main_qui_casse
        lignes = []
        try:
            with redirect_stdout(io.StringIO()):
                C.construit(img, os.path.join(T, "s_echec"), None, journal=lignes.append, jeux=["sfa3"])
        except RuntimeError:
            pass
        verifie("echec : ligne Durée totale", any(l.startswith("Durée totale") for l in lignes), lignes)
        # message de fin : les zips des jeux construits seulement
        S = os.path.join(T, "s_zips"); os.makedirs(S)
        for z in ("sfa3hsfa", "sfa3uhsfa", "sfa3hhsfa", "sfa3hahsfa", "sfa3umhsfa"):
            open(os.path.join(S, z + ".zip"), "wb").write(b"PK")
        verifie("fin hyperarcade : 3 jeux", "Terminé : 3 jeux" in C.message_fin(0, S, None, ["hyperarcade"]))
        verifie("fin sfa3,hyper : 2 jeux", "Terminé : 2 jeux" in C.message_fin(0, S, None, ["sfa3", "hyper"]))
        verifie("fin defaut sans PSP : 3 jeux", "Terminé : 3 jeux" in C.message_fin(0, S))
        verifie("fin defaut avec PSP : 4 jeux", "Terminé : 4 jeux" in C.message_fin(0, S, psp))
    finally:
        H.main = vrai_main
        shutil.rmtree(T, ignore_errors=True)


def test_cases():
    et, sel = C.etat_cases({"hyperarcade": True}, False)
    verifie("cases hyperarcade", et["upper"] == (True, False) and et["hyper"] == (True, False)
            and et["hyperarcade"] == (True, True) and et["sfa3"] == (False, True), et)
    verifie("cases : Upper MAX grisee sans PSP", et["uppermax"] == (False, False), et)
    et, sel = C.etat_cases({"uppermax": True}, False)
    verifie("cases : Upper MAX seul sans PSP = rien", sel is None and et["uppermax"] == (False, False), et)
    et, sel = C.etat_cases({"uppermax": True, "sfa3": True}, True)
    verifie("cases : Upper MAX avec PSP", et["uppermax"] == (True, True) and et["upper"] == (True, False)
            and sel["jeux"] == ["sfa3", "uppermax"], et)
    et, sel = C.etat_cases({"hyper": True}, False)
    verifie("cases : Hyper seul, Upper libre", et["upper"] == (False, True) and "upper" in sel["etapes"], et)
    et, sel = C.etat_cases({}, True)
    verifie("cases : rien de choisi", sel is None)
    # durees sous les cases : 5 jeux = 12 min (mesure d'un i5-13500H, ECHELLE_REF), parts arrondies de somme = total
    tous = dict.fromkeys(C.JEUX_CHOIX, True)
    tx, total = C.durees_cases(tous, True)
    verifie("durees : 5 jeux = Total ≈ 12 min", total == "Total ≈ 12 min", total)
    verifie("durees : somme des parts = total", sum(int(t.split()[1]) for t in tx.values()) == 12, tx)
    tx, total = C.durees_cases({"hyper": True}, False)
    verifie("durees : Upper MAX vide sans PSP, cases libres en +", tx["uppermax"] == "" and tx["sfa3"].startswith("+≈ ")
            and tx["hyper"].startswith("≈ ") and total.startswith("Total ≈ "), (tx, total))
    tx, total = C.durees_cases({}, True)
    verifie("durees : rien de choisi", total == "" and all(t.startswith("+≈ ") for t in tx.values()), tx)


def test_main():
    vu = {}
    vrais = C.console, C.fenetre
    C.console = lambda *a, **k: vu.update(console=k.get("jeux"), a=a) or 0
    C.fenetre = lambda *a, **k: vu.update(fenetre=a[4] if len(a) > 4 else k.get("jeux")) or 0
    try:
        C.main(["x", "a.iso", "--jeux", "hyper,sfa3"])
        verifie("main --jeux -> console", vu.get("console") == ["sfa3", "hyper"], vu)
        vu.clear(); C.main(["x", "a.iso"])
        verifie("main sans --jeux -> None (comportement d'avant)", "console" in vu and vu["console"] is None, vu)
        vu.clear(); C.main(["x", "a.iso", "--psp", "p.iso", "--games", "uppermax"])
        verifie("main --games uppermax --psp", vu.get("console") == ["uppermax"], vu)
        for mauvais in (["--jeux", "hyperarcademax"], ["--jeux", "uppermax"], ["--jeux", "rien"]):
            try:
                with redirect_stderr(io.StringIO()):
                    C.main(["x", "a.iso"] + mauvais)
                verifie("main %s refuse" % mauvais, False)
            except SystemExit as x:
                verifie("main %s refuse (code 2)" % mauvais, x.code == 2, x.code)
        vu.clear(); ancien = os.environ.get("DISPLAY"); os.environ["DISPLAY"] = ":essai"
        try:
            C.main(["x", "--jeux", "uppermax,hyperarcade"])        # fenetre : l'ISO PSP peut y etre choisie ensuite
        finally:
            if ancien is None: os.environ.pop("DISPLAY")
            else: os.environ["DISPLAY"] = ancien
        verifie("main --jeux -> fenetre", vu.get("fenetre") == ["uppermax", "hyperarcade"] or os.name == "nt"
                or sys.platform == "darwin", vu)
    finally:
        C.console, C.fenetre = vrais


def main():
    test_selection()
    test_jeux()
    test_construit()
    test_cases()
    test_main()
    print("OK" if not ECHECS else "%d ECHECS" % len(ECHECS))
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
