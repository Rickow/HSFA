#!/usr/bin/env python3
"""Tournee complete d'Hyper dans le coeur FBNeo : un VERSUS pilote par perso et par version (J2 = perso essaye,
J1 = Ryu ZERO 3 ; en ZERO 3, les trois ISM). Releve les musiques demandees (journal HSFA_FLUX_LOG du coeur), les
choix reellement faits ($102, ISM) et les blocages. Aucune donnee de jeu dans le depot : le zip est donne en argument.

  tournee_complete.py <joue_linux> <coeur.so> <sfa3hhsfa.zip> <dossier_system> <dossier_sortie> [-j 4] [-n 8000]
  [--seul 00.Z3.iX,...]

Sortie : <dossier_sortie>/tournee.tsv (une ligne par essai) et un dossier par essai (tournee.log, flux.log).
"""
import argparse, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ICI = os.path.dirname(os.path.abspath(__file__))
ISM = {"iX": 0xFF, "iA": 0x00, "iV": 0x01}
Z3_DEFAUT = "iX,iA,iV"


def vers():
    """table VERS de tournee.h : 4 colonnes (Z, Z2, A, Z3) par perso de base"""
    s = open(os.path.join(ICI, "tournee.h")).read()
    m = re.search(r"VERS\[\] = \{([^}]*)\}", s)
    v = [int(x, 16) for x in m.group(1).split(",")]
    return [v[i:i + 4] for i in range(0, len(v), 4)]


def famille(i):
    return "Z3" if i < 0x30 else "Z" if i < 0x40 else "Z2" if i < 0x60 else "A"


def essais(z3=Z3_DEFAUT, extra=""):
    """un essai par id jouable ($102) ; les lignes de VERS qui repetent un id deja vu (alias) sont sautees"""
    out, vus = [], set()
    for b, ligne in enumerate(vers()):
        for i in ligne:
            if i == 0xFF or i in vus:
                continue
            vus.add(i)
            f = famille(i)
            if f == "Z3":
                for k in z3.split(","):            # ex. "iA.m3" (CLASSIC), "iA.m1.e+1" (MAZI + Start + droite)
                    m = re.search(r"\.m(\d)", k)
                    ism = None if m and m.group(1) != "0" else ISM[k[:2]]   # MAZI / SAIKYO / CLASSIC peuvent imposer l'ISM
                    out.append(("%02x.Z3.%s" % (b, k), b, i, ism))
            else:
                out.append(("%02x.%s" % (b, f), b, i, None))
                for e in extra.split(","):          # ex. "A:vS" : ALPHA, Start tenu a la validation (versions EX)
                    if e.startswith(f + ":"):
                        out.append(("%02x.%s.%s" % (b, f, e.split(":")[1]), b, None, None))
    return out


def lance(a, nom):
    d = os.path.join(a.sortie, nom.replace(".", "_"))
    os.makedirs(d, exist_ok=True)
    env = dict(os.environ, HSFA_TOURNEE="00.Z3.iA/" + nom,
               HSFA_TOURNEE_LOG=os.path.join(d, "tournee.log"), HSFA_FLUX_LOG=os.path.join(d, "flux.log"))
    if not a.roulette:
        env["HSFA_NOROUL"] = "1"                 # roulette neutralisee (comme le banc) ; --roulette : comportement normal
    with open(os.path.join(d, "sortie.log"), "w") as e:
        r = subprocess.run([a.joue, a.coeur, a.zip, a.sys, str(a.n), os.devnull], env=env, cwd=d,
                           stdout=e, stderr=subprocess.STDOUT, timeout=900)
    return d, r.returncode


def lit(d):
    t = open(os.path.join(d, "tournee.log")).read() if os.path.exists(os.path.join(d, "tournee.log")) else ""
    f = open(os.path.join(d, "flux.log")).read() if os.path.exists(os.path.join(d, "flux.log")) else ""
    ch = re.findall(r"CHOIX J2 image \d+ : \$102=(\w+) base=\w+ ism=(\w+)(?: \$116=\w+ \$122=\w+ \$123=(\w+) \$15F=(\w+))?", t)
    manches = len(re.findall(r"^MANCHE ", t, re.M))
    musiques = re.findall(r"^([0-9A-F]{4}) -> (flux Y\d+ ECHEC.*|flux Y\d+|Z80 \(QSound\))", f, re.M)
    fin = re.search(r"FIN (\d+) selections (\d+) manches (\d+)", t)
    return ch, manches, musiques, fin


def main():
    p = argparse.ArgumentParser()
    p.add_argument("joue"); p.add_argument("coeur"); p.add_argument("zip"); p.add_argument("sys"); p.add_argument("sortie")
    p.add_argument("-j", type=int, default=4); p.add_argument("-n", type=int, default=8000)
    p.add_argument("--seul", default="")
    p.add_argument("--roulette", action="store_true", help="sans HSFA_NOROUL (roulette sur la touche Piece, patch 11)")
    p.add_argument("--extra", default="", help="variantes par famille, ex. A:vS (seules jouees si donnees)")
    p.add_argument("--z3", default=Z3_DEFAUT, help="variantes ZERO 3 : ism (iX/iA/iV), mode (.m0-.m3), Start (.e+1/.e-1)")
    a = p.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    liste = essais(a.z3, a.extra)
    if a.extra:
        liste = [e for e in liste if e[2] is None]
    if a.z3 != Z3_DEFAUT:                     # variantes demandees : seulement les persos ZERO 3
        liste = [e for e in liste if ".Z3." in e[0]]
    if a.seul:
        garde = set(a.seul.split(","))
        liste = [e for e in liste if e[0] in garde]
    print("%d essais" % len(liste), file=sys.stderr)
    with ThreadPoolExecutor(a.j) as ex:
        res = list(ex.map(lambda e: (e, lance(a, e[0])), liste))
    lignes = ["essai\tid_attendu\tism_attendu\t$102\tism\t$123\t$15F\tmanches\tetat\tmusiques"]
    bilan = {}
    for (nom, b, i, ism), (d, rc) in res:
        ch, manches, mus, fin = lit(d)
        j102, jism, j123, j15f = (ch[0] if ch else ("-", "-", "-", "-"))
        etat = "ok"
        if rc != 0:
            etat = "plantage(%d)" % rc
        elif not ch:
            etat = "pas_de_choix"
        elif (i is not None and int(j102, 16) != i) or (ism is not None and int(jism, 16) != ism):
            etat = "autre_perso"
        elif manches < 2:
            etat = "manches=%d" % manches
        elif any("ECHEC" in m[1] for m in mus):
            etat = "flux_en_echec"
        bilan[etat] = bilan.get(etat, 0) + 1
        seq = " ".join("%s>%s" % (c, x.replace("flux ", "").replace("Z80 (QSound)", "QS")) for c, x in mus)
        lignes.append("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s" % (nom, "-" if i is None else "%02x" % i, "-" if ism is None else "%02x" % ism, j102,
                                                               jism, j123 or "-", j15f or "-", manches, etat, seq))
    open(os.path.join(a.sortie, "tournee.tsv"), "w").write("\n".join(lignes) + "\n")
    print("bilan : " + ", ".join("%s %d" % kv for kv in sorted(bilan.items())))


if __name__ == "__main__":
    main()
