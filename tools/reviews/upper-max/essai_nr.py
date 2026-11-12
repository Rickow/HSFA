#!/usr/bin/env python3
"""essai_nr.py -- Upper MAX arbitrations (A2): negative tests of the "blocking UNRESOLVED" check
(prepare_max.controle_non_resolus, ag/conv/non_resolus_admis.tsv), without rebuilding: on the preparation of an Upper
MAX build (<build>/outils_max/ag), with a modified allow-list or modified sources in a temporary folder. 9 tests: the
list as is passes; Yun's $32D line removed fails by name (passes with CONV_NON_RESOLUS_LIBRES=1); whitespace is
normalised; a new unresolved access fails; one admitted instruction too many fails; the dead zones of Eagle are
re-checked; a cited label fails; an admitted line that disappeared gives a notice.
When Yun's $32D fix is merged, update the tests that use it (psp_1bc300).

Usage:  SFA3MAX_CACHE=<cache>/max_regen python3 -I essai_nr.py BUILD
        BUILD = folder of an Upper MAX build made by um_prog.py / hsfa_build (holds outils_max/ag/prep and outils/)
        SFA3MAX_CACHE is read by max_cache when prepare_max is imported (the build's max_regen cache).
Output: one verdict per test; exit code 1 if a test failed. Writes only in a temporary folder.
"""
import os, sys, shutil, tempfile, contextlib, io
sys.dont_write_bytecode = True   # no __pycache__ in the build folder

if len(sys.argv) < 2: sys.exit(__doc__)
if not os.environ.get("SFA3MAX_CACHE"): sys.exit("set SFA3MAX_CACHE (<cache>/max_regen of the build)")
C = os.path.abspath(sys.argv[1]); AG = os.path.join(C, "outils_max", "ag"); PREP = os.path.join(AG, "prep")
sys.path.insert(0, os.path.join(AG, "outils")); os.chdir(os.path.join(AG, "outils"))
import importlib
PM = importlib.import_module("prepare_max")   # the BUILD's copy (outils_max/ag/outils), resolved at run time
ADMIS0 = PM.NR_ADMIS
T = tempfile.mkdtemp(prefix="essai_nr_")

def lance(admis=None, src=None, nr_plus=None, env=None, nr_sans=None):
    """rend (code de sortie, texte) de controle_non_resolus sur des copies modifiées"""
    out = os.path.join(T, "prep"); shutil.rmtree(out, ignore_errors=True); os.makedirs(os.path.join(out, "conv"))
    t = open(os.path.join(PREP, "conv", "non_resolus.tsv"), encoding="utf-8").read()
    if nr_sans: t = "".join(l for l in t.splitlines(True) if nr_sans not in l)
    open(os.path.join(out, "conv", "non_resolus.tsv"), "w", encoding="utf-8").write(t + (nr_plus or ""))
    PM.NR_ADMIS = ADMIS0
    if admis is not None:
        PM.NR_ADMIS = os.path.join(T, "admis.tsv"); open(PM.NR_ADMIS, "w", encoding="utf-8").write(admis)
    s = os.path.join(PREP, "src")
    if src is not None:
        s = os.path.join(T, "src"); shutil.rmtree(s, ignore_errors=True); shutil.copytree(os.path.join(PREP, "src"), s)
        for f, avant, apres in src:
            p = os.path.join(s, f); x = open(p, encoding="utf-8").read(); assert avant in x, (f, avant)
            open(p, "w", encoding="utf-8").write(x.replace(avant, apres, 1))
    old = dict(os.environ); os.environ.update(env or {})
    buf = io.StringIO(); code = 0
    try:
        with contextlib.redirect_stdout(buf): PM.controle_non_resolus(out, s)
    except SystemExit as e: code, msg = 1, str(e); buf.write("\n" + msg)
    finally: os.environ.clear(); os.environ.update(old)
    return code, buf.getvalue()

A = open(ADMIS0, encoding="utf-8").read()
ESSAIS = [
    ("liste telle quelle : passe", dict(), 0, "dont 0 non admis"),
    ("ligne de Yun $32D retirée de la liste : échec nommé", dict(admis="".join(l for l in A.splitlines(True) if "psp_1bc300" not in l)), 1, "brouillon_yun.s:1504"),
    ("idem avec CONV_NON_RESOLUS_LIBRES=1 : passe, défaut listé", dict(admis="".join(l for l in A.splitlines(True) if "psp_1bc300" not in l), env={"CONV_NON_RESOLUS_LIBRES": "1"}), 0, "NON ADMIS : brouillon_yun.s:1504"),
    ("blancs ajoutés dans une instruction admise : passe (normalisation)", dict(admis=A.replace("tst.w $50(a1)", "tst.w   $50( a1 )".replace("( ", "("))), 0, "dont 0 non admis"),
    ("nouveau NON RÉSOLU (accès non typé ajouté) : échec", dict(nr_plus="brouillon_maki.s\t999\tchamp objet $33B.b non typé\ttst.b $33b(a1)\tpsp_1b5000\n"), 1, "brouillon_maki.s:999"),
    ("même instruction admise une fois de trop : échec", dict(nr_plus="moteur_max_main.s\t2000\tregistre a1 de genre inconnu\ttst.w   $50(a1)\tpsp_cf72c\n"), 1, "2 fois, 1 admis"),
    ("« bra » des intros croisées d'Eagle retiré : les 4 lignes « mortes » d'Eagle échouent", dict(src=[("brouillon_eagle.s", "        bra     L_1b0440           ; (agent_integration_max) intros croisées retirées\n", "")]), 1, "hors de la zone sautée"),
    ("étiquette de la zone sautée citée ailleurs : échec", dict(src=[("brouillon_maki.s", "\n", "\n        bra     L_1b0410\n")]), 1, "est citée en"),
    ("admis disparu (Yun corrigé) : AVIS, passe", dict(nr_sans="psp_1bc300"), 0, "admis absent (0/1) : brouillon_yun.s"),
]
rate = 0
for nom, kw, code_att, motif in ESSAIS:
    c, txt = lance(**kw)
    ok = c == code_att and motif in txt
    rate += not ok
    print("%s  %s  (code %d ; « %s » %s)" % ("OK  " if ok else "RATÉ", nom, c, motif, "trouvé" if motif in txt else "ABSENT"))
    if not ok: print("   " + txt.replace("\n", "\n   ")[:1500])
shutil.rmtree(T, ignore_errors=True)
sys.exit(1 if rate else 0)
