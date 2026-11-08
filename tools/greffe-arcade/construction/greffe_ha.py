#!/usr/bin/env python3
"""greffe_ha.py -- etape « greffe » du jeu hyperarcade : enchaine la greffe (copie figee ro9a35b, fige35.py ;
HA_FIGE=fige_ro9a22 + fige.py pour l'ancienne) comme
outils/construit_e3.sh, dans un dossier materialise, a partir d'entrees donnees par variables.

  python3 greffe_ha.py --dest DIR --nom NOM [--audit] [--vars "K=V ..."] HA_CLE=chemin ...
Cles (marques de fige.py) : HA_EXTRACT (anthology_extract : manifest.csv + decompressed/), HA_ANIMS (cache des
anims), HA_XDATA (X_DATA.BIN), HA_MODULES_SON (module ro9 corrige + bloc $E70000), HA_MAME_RO9 / HA_MAME_RO5
(dossiers de travail d'Hyper / d'Upper : banques_hx/). Les outils (HA_G, HA_EU, HA_CARTO, HA_UT) et HA_MAME (dossier
vide roms/sfa3ud : aucun lien vers une ROM) sont dans DIR. Toute autre marque -> chemin absent (fuite = echec).
--audit : journal de tous les fichiers ouverts (DIR/audit/ouverts_<pid>.txt), sous-processus compris.
Sortie : DIR/outils/greffe/constructions/NOM/ (b9/roms_ro9/sfa3ud, b9/ext_*.bin, banques_hx/, ...).
"""
import argparse, os, subprocess, sys, hashlib

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import fige35 as fige

SITECUSTOMIZE = r'''
import os, sys
_d = os.environ.get("HA_AUDIT_DIR")
if _d:
    _f = open(os.path.join(_d, "ouverts_%d.txt" % os.getpid()), "a")
    _f.write("# argv %r\n" % (sys.argv,))
    _vus = set()
    def _h(ev, args):
        if ev == "open" and args and isinstance(args[0], (str, bytes)):
            p = os.path.abspath(args[0] if isinstance(args[0], str) else args[0].decode("utf-8", "replace"))
            m = args[1] if len(args) > 1 else "r"
            k = (p, "w" if (m and any(c in str(m) for c in "wax+")) else "r")
            if k not in _vus:
                _vus.add(k); _f.write("%s %s\n" % (k[1], p)); _f.flush()
    sys.addaudithook(_h)
    _stat = os.stat
    def _st(p, *a, **k):                       # os.path.exists / isfile : lectures conditionnelles
        try:
            q = os.path.abspath(os.fsdecode(p)) if isinstance(p, (str, bytes)) else None
            if q and not q.startswith(("/usr/", "/proc/", "/sys/", "/dev/")) and ("s", q) not in _vus:
                _vus.add(("s", q)); _f.write("s %s\n" % q); _f.flush()
        except Exception: pass
        return _stat(p, *a, **k)
    os.stat = _st
'''

def lance(cmd, cwd, env, log):
    with open(log, "a") as f:
        f.write("\n=== %s (cwd %s)\n" % (" ".join(cmd), cwd)); f.flush()
        r = subprocess.run((["nice", "-n", "19"] if os.name == "posix" else []) + cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode: sys.exit("echec (%d) : %s ; voir %s" % (r.returncode, " ".join(cmd), log))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True); ap.add_argument("--nom", default="ha")
    ap.add_argument("--audit", action="store_true"); ap.add_argument("--vars", default="")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--code", help="partie CODE de la copie figee (defaut : copie complete fige_ro9a35b/)")
    ap.add_argument("--releves", help="RELEVES de la greffe (journaux MAME, pkl d'analyses) a joindre au code")
    ap.add_argument("cles", nargs="*")
    a = ap.parse_args()
    D = os.path.abspath(a.dest); O = os.path.join(D, "outils"); G = os.path.join(O, "greffe")
    val = {"@HA_G@": G, "@HA_EU@": os.path.join(O, "eu"), "@HA_CARTO@": os.path.join(O, "carto"),
           "@HA_UT@": os.path.join(O, "ut"), "@HA_MAME@": os.path.join(D, "mame_vide")}
    for c in a.cles:
        k, v = c.split("=", 1); val["@%s@" % k] = os.path.abspath(v)
    os.makedirs(os.path.join(D, "mame_vide", "roms", "sfa3ud"), exist_ok=True)
    rac = None
    if a.releves and os.path.exists(os.path.join(a.releves, "RELEVES_TSV")):   # releves en TSV (depot) -> fichiers lus
        import releves_tsv
        R = os.path.join(D, "releves"); 
        if os.path.isdir(R): import shutil; shutil.rmtree(R)
        releves_tsv.reconstituer(os.path.abspath(a.releves), R); a.releves = R
    if a.code:
        rac = [os.path.abspath(a.code)] + ([os.path.abspath(a.releves)] if a.releves else [])
    fige.materialiser(O, val.items(), rac)
    # environnement propre (determinisme) ; Windows : variables systeme indispensables a Python ; constructeur
    # tout-en-un : chargeur PyInstaller (_PYI_*, sinon chaque etape re-extrait l'executable)
    GARDE = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "WINDIR", "COMSPEC", "USERPROFILE",
             "LOCALAPPDATA", "APPDATA", "PATHEXT")
    env = {k: v for k, v in os.environ.items() if k.upper() in GARDE or k.startswith("_PYI_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if a.audit:
        sc = os.path.join(D, "audit_site"); os.makedirs(sc, exist_ok=True)
        open(os.path.join(sc, "sitecustomize.py"), "w").write(SITECUSTOMIZE)
        os.makedirs(os.path.join(D, "audit"), exist_ok=True)
        env["PYTHONPATH"] = sc; env["HA_AUDIT_DIR"] = os.path.join(D, "audit")
    for kv in a.vars.split():                  # interrupteurs ; marques @HA_*@ permises (fichiers de la copie)
        k, v = kv.split("=", 1)
        for m, x in val.items(): v = v.replace(m, x)
        env[k] = v
    log = os.path.join(D, "greffe_ha.log"); py = a.python
    # = outils/construit_e3.sh NOM : plan seul -> table A5 -> module, bloc, traduction
    lance([py, "etape3/greffe3.py"], G, dict(env, NOM=a.nom, PLAN_SEUL="1"), log)
    lance([py, "etape3/relogement_a5_v3.py"], G, dict(env, GREFFER_PKL="donnees/greffe_v3.pkl"), log)
    lance([py, "etape3/greffe3.py", "--construire"], G, dict(env, NOM=a.nom), log)
    P = os.path.join(G, "constructions", a.nom)
    r = os.path.join(P, "b9", "roms_ro9", "sfa3ud", "sz3ud.03c")
    print("sz3ud.03c", hashlib.md5(open(r, "rb").read()).hexdigest())
    print(open(os.path.join(P, "construction.log")).read().splitlines()[-1])

if __name__ == "__main__":
    main()
