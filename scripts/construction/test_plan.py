#!/usr/bin/env python3
"""test_plan.py -- checks of hsfa_build.py's step plan and estimated duration, WITHOUT game data and without building
anything (no step is run; the steps are replaced by empty functions in the run test). Standard library only.

  python3 scripts/construction/test_plan.py [-v]

1. plan: for every combination of games (sfa3, upper, hyper, uppermax, hyperarcade, hyperarcademax), with and
   without the PSP ISO, --sans-flux, --arcade and HSFA_ETAPES_PLUS=sons_ps2_hypermax: the plan is built (every
   dependency is in it, before the step: etapes() checks it), it holds the archive of every game asked for, and the
   order of --jeux changes nothing (« --jeux hyper,upper » = « --jeux upper,hyper »);
2. each game alone: its steps (like --liste), printed with -v;
3. durations: every step has a reference duration (DUREES_REF); the per-game durations add up to the total;
4. cache: steps already done (same key, outputs there) do not count; a changed step counts with all the steps
   that depend on it;
5. run: run() with empty steps: one line and one AVANCEMENT event per step, n = 1..N, nothing left at the end; a second
   run redoes only « empreintes ».
Exit code 0 if everything passes.
"""
import io, itertools, os, shutil, sys, tempfile
from contextlib import redirect_stdout

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import hsfa_build as H

JEUX = ["sfa3", "upper", "hyper", "uppermax", "hyperarcade", "hyperarcademax"]
ECHECS = []
VERBEUX = "-v" in sys.argv


def verifie(nom, ok, detail=""):
    if not ok:
        ECHECS.append(nom)
        print("ECHEC %s %s" % (nom, detail))
    return ok


def construction(sortie, jeux, psp=False, sans_flux=False, arcade=False):
    argv = ["--anthology", os.path.join(sortie, "a.iso"), "--sortie", sortie, "--jeux", jeux]
    if psp: argv += ["--psp-iso", os.path.join(sortie, "p.iso")]
    if sans_flux: argv += ["--sans-flux"]
    if arcade: argv += ["--arcade", os.path.join(sortie, "sfa3.zip")]
    with redirect_stdout(io.StringIO()):
        return H.Construction(H.parseur().parse_args(argv))


def archives_attendues(jeux, psp):
    a = set()
    for j in jeux:
        if j == "uppermax": a.add("paquet_uppermax" if psp else "paquet_upper")
        elif j == "hyperarcademax": a.add("paquet_hyperarcademax" if psp else "paquet_hyperarcade")
        else: a.add("paquet_" + j)
        if j.startswith("hyperarcade"): a |= {"paquet_upper", "paquet_hyper"}
    return a


def plan(c):
    return [(e[0], list(e[1])) for e in c.etapes()]


def test_combinaisons(S):
    n = 0
    for k in range(1, len(JEUX) + 1):
        for combo in itertools.combinations(JEUX, k):
            for psp, sf, arc, plus in itertools.product((0, 1), repeat=4):
                os.environ["HSFA_ETAPES_PLUS"] = "sons_ps2_hypermax" if plus else ""
                nom = "%s psp=%d sans_flux=%d arcade=%d plus=%d" % (",".join(combo), psp, sf, arc, plus)
                try:
                    p = plan(construction(S, ",".join(combo), psp, sf, arc))
                except H.Echec as x:
                    verifie("plan " + nom, False, x); continue
                noms = [e[0] for e in p]
                manque = archives_attendues(combo, psp) - set(noms)
                verifie("archives " + nom, not manque, sorted(manque))
                verifie("durees " + nom, all(e in H.DUREES_REF for e in noms),
                        [e for e in noms if e not in H.DUREES_REF])
                if k > 1 and not plus:                # order of --jeux: reversed = same plan
                    q = plan(construction(S, ",".join(reversed(combo)), psp, sf, arc))
                    verifie("ordre " + nom, p == q)
                n += 1
    os.environ["HSFA_ETAPES_PLUS"] = ""
    print("plan : %d combinaisons" % n)


def test_seuls(S):
    for j in JEUX:
        for psp in (0, 1):
            c = construction(S, j, psp)
            p = plan(c)
            noms = [e[0] for e in p]
            if VERBEUX:
                print("--jeux %s%s : %s" % (j, " --psp-iso" if psp else "", " ".join(noms)))
            if j == "hyper":   # the bug of 14/11: Hyper alone needs Upper's graphics step (and module ro5), not its archive
                verifie("hyper seul : gfx_upper avant gfx_hyper", "gfx_upper" in noms and "module_ro5" in noms
                        and noms.index("gfx_upper") < noms.index("gfx_hyper"))
                verifie("hyper seul : pas d'archive d'Upper", "paquet_upper" not in noms and "prog_upper" not in noms)
            pv = c.prevoit()
            verifie("seul %s : tout a faire (sortie vide)" % j, all(f for _n, f, _s, _j in pv))
            par_jeu = {}
            for _n, _f, s, jj in pv: par_jeu[jj] = par_jeu.get(jj, 0) + s
            verifie("seul %s : somme par jeu = total" % j, abs(sum(par_jeu.values()) - sum(s for _n, _f, s, _j in pv)) < 1e-6)
            jeu_affiche = "uppermax" if (j == "uppermax" and psp) else "upper" if j == "uppermax" else \
                ("hyperarcademax" if psp else "hyperarcade") if j == "hyperarcademax" else j
            verifie("seul %s : jeu annonce" % j, jeu_affiche in par_jeu, sorted(par_jeu))
    print("jeux seuls : %d plans" % (2 * len(JEUX)))


def test_cache(S):
    c = construction(S, "sfa3,upper,hyper")
    E = c.etapes()
    for nom, deps, outils, _f, _d in E:                  # everything done, with the right keys (no output files)
        c.etat[nom] = dict(fait=True, cle=c.cle(nom, deps, outils, c.params(nom)), sorties={}, duree=10)
    pv = c.prevoit(E)
    verifie("cache : seule empreintes a faire", [n for n, f, _s, _j in pv if f] == ["empreintes"],
            [n for n, f, _s, _j in pv if f])
    verifie("cache : duree mesuree sur ce poste", dict((n, s) for n, f, s, _j in pv if f) == {"empreintes": 10})
    c.etat["gfx_upper"]["cle"] = "autre"
    a_faire = [n for n, f, _s, _j in c.prevoit(E) if f]
    verifie("cache : gfx_upper change -> ses dependantes", a_faire ==
            ["gfx_upper", "gfx_hyper", "paquet_upper", "paquet_hyper", "empreintes"], a_faire)


def test_run(S):
    evenements = []
    H.AVANCEMENT = lambda e, **i: evenements.append((e, i))
    vides = H.Construction.etapes
    def etapes(self):                                      # same plan, empty steps
        return [(n, d, o, (lambda: []), desc) for n, d, o, _f, desc in vides(self)]
    H.Construction.etapes = etapes
    try:
        for passe in (1, 2):
            del evenements[:]
            c = construction(S, "hyper")
            with redirect_stdout(io.StringIO()) as sortie:
                r = c.run()
            lignes = sortie.getvalue().splitlines()
            plan_ = [i for e, i in evenements if e == "plan"]
            pas = [i for e, i in evenements if e == "etape" and i["fait"]]
            verifie("run %d : code 0" % passe, r == 0)
            verifie("run %d : duree annoncee avant la premiere etape" % passe,
                    any("Durée estimée / estimated time" in l for l in lignes[:3]), lignes[:3])
            N = plan_[0]["N"] if plan_ else -1
            if passe == 1:
                verifie("run 1 : N = toutes les etapes", N == len(vides(c)), N)
            else:
                verifie("run 2 : seule empreintes refaite", N == 1 and [l for l in lignes if "] faite (" in l][0].split("]")[0]
                        .endswith("[empreintes"), N)
            fins = [i["n"] for i in pas]
            debuts = [i["n"] for e, i in evenements if e == "etape" and not i["fait"]]
            verifie("run %d : chaque etape commence puis finit" % passe, debuts == fins, (debuts, fins))
            verifie("run %d : etapes 1..N" % passe, sorted(set(fins)) == list(range(1, N + 1)), fins)
            verifie("run %d : rien ne reste a la fin" % passe, pas and pas[-1]["reste"] == 0 and pas[-1]["n"] == N)
            verifie("run %d : lignes « faite » avec n/N" % passe,
                    all(("/%d, reste/left" % N) in l for l in lignes if "] faite (" in l))
    finally:
        H.Construction.etapes = vides
        H.AVANCEMENT = None


def main():
    S = tempfile.mkdtemp(prefix="hsfa_test_plan_")
    try:
        test_combinaisons(os.path.join(S, "a"))
        test_seuls(os.path.join(S, "b"))
        test_cache(os.path.join(S, "c"))
        test_run(os.path.join(S, "d"))
    finally:
        shutil.rmtree(S, ignore_errors=True)
    print("OK" if not ECHECS else "%d ECHECS" % len(ECHECS))
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
