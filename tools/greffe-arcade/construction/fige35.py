#!/usr/bin/env python3
"""fige35.py -- copie figee des outils de la greffe Arcade (figee a l'etat ro9a35b le 08/11 ; ro9a36 = report du diff de greffe3.py, ro9a37 = traducteur de la greffe v161, LISEZMOI) et materialisation parametree.
(derive de fige.py, etat ro9a22 du 01/11)

  python3 fige.py figer        : copie (UNE fois) les outils de l'atelier dans fige_ro9a22/ ; les chemins d'atelier
                                 sont remplaces par des marques @HA_xxx@ (aucune adresse d'atelier dans la copie).
                                 Fichiers de l'etat ro9a22 : greffe3 / donnees2 = etape4/*_avant_e31.py ;
                                 translate / mame_test / assemble = e31/avant/*.py (MD5SUMS de e31/avant).
  python3 fige.py materialiser DEST CLE=VAL ... : recopie fige_ro9a22/ dans DEST en remplacant les marques.
                                 Marque non donnee -> /chemin/atelier/absent/<marque> (une fuite echoue).

Lecture seule sur l'atelier ; n'ecrit que dans ce dossier (figer) ou DEST (materialiser).
"""
import os, sys, shutil, hashlib, glob

ICI = os.path.dirname(os.path.abspath(__file__))
FIGE = os.path.join(ICI, os.environ.get("HA_FIGE", "fige_ro9a35b"))
A = os.environ.get("HSFA_ATELIER", "<atelier>")   # atelier (seulement pour 'figer' ; hors depot)
W = A + "/hsfa/work"
GA = W + "/greffe_arcade"

# chemin d'atelier -> marque (ordre : du plus long au plus court)
MARQUES = [
    (GA, "@HA_G@"),
    (W + "/etude_upper_hyper", "@HA_EU@"),
    (W + "/carto_ro9", "@HA_CARTO@"),
    (A + "/hsfa/scripts/untranspile", "@HA_UT@"),
    (os.environ.get("HSFA_ATELIER_EXTRACT", A + "/anthology_extract"), "@HA_EXTRACT@"),
    (W + "/cps2/anims", "@HA_ANIMS@"),
    (W + "/xdata/X_DATA.BIN", "@HA_XDATA@"),
    (W + "/modules_son", "@HA_MODULES_SON@"),
    (W + "/mame_ro9", "@HA_MAME_RO9@"),
    (W + "/mame_ro5", "@HA_MAME_RO5@"),
    (W + "/mame", "@HA_MAME@"),
    (W + "/cps2", "@HA_CPS2@"),
    (W, "@HA_WORK@"),
    (A + "/hsfa", "@HA_HSFA@"),
    (A, "@HA_HOME@"),
]

# (source dans l'atelier, destination dans la copie) ; les remplacements ro9a22 d'abord
REMPLACE = {}     # ro9a35b : outils courants de l'atelier (aucun code modifie apres e45c, 08/11 19 h 46)
MD5_RO9A22 = {}

def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()

def sources():
    """liste (dest relative, source absolue) de la copie figee"""
    L = []
    def dossier(src, dst, motif="*", rec=False):
        for p in sorted(glob.glob(os.path.join(src, "**", motif) if rec else os.path.join(src, motif), recursive=rec)):
            if os.path.isfile(p) and "__pycache__" not in p:
                L.append((os.path.join(dst, os.path.relpath(p, src)), p))
    # outils de la greffe (code)
    for d in ("outils", "etape2", "etape3"):
        dossier(os.path.join(GA, d), "greffe/" + d, "*.py")
    # traducteur fusionne (code + json de donnees du traducteur)
    dossier(os.path.join(GA, "untranspile3"), "greffe/untranspile3", "*.py")
    dossier(os.path.join(GA, "untranspile3"), "greffe/untranspile3", "*.json")
    # donnees de la greffe (decisions, relevés, pkl intermediaires)
    dossier(os.path.join(GA, "donnees"), "greffe/donnees", "*")
    dossier(os.path.join(GA, "decors"), "greffe/decors", "*", rec=True)
    # journaux de lecture MAME d'Upper utilises a la construction (u_lu*, defi_lu)
    for p in sorted(glob.glob(os.path.join(GA, "traces", "u_lu*", "lu.txt")) + glob.glob(os.path.join(GA, "traces", "defi_lu", "*", "lu.txt"))):
        L.append(("greffe/" + os.path.relpath(p, GA), p))
    # (ro9a35b) journaux des objets de decor (OBJETS_DECOR, greffe3 : traces/objets_lu/lu_*/lu.txt)
    for p in sorted(glob.glob(os.path.join(GA, "traces", "objets_lu", "lu_*", "lu.txt"))):
        L.append(("greffe/" + os.path.relpath(p, GA), p))
    # (ro9a35b) traducteur de la greffe v160 (TRAD=@HA_G@/e42/untranspile3_v160) et fichiers des interrupteurs
    dossier(os.path.join(GA, "e42", "untranspile3_v160"), "greffe/e42/untranspile3_v160", "*.py")
    dossier(os.path.join(GA, "e42", "untranspile3_v160"), "greffe/e42/untranspile3_v160", "*.json")
    # (ro9a37) traducteur de la greffe v161 (TRAD=@HA_G@/e47/untranspile3_v161 = v160 + diff v160 -> v161 du traducteur)
    dossier(os.path.join(GA, "e47", "untranspile3_v161"), "greffe/e47/untranspile3_v161", "*.py")
    dossier(os.path.join(GA, "e47", "untranspile3_v161"), "greffe/e47/untranspile3_v161", "*.json")
    for f in ("e35/hom_partages_50.txt", "e42/ptr_exclus_pal_att.txt", "e43/ptr_exclus_e43.txt"):
        L.append(("greffe/" + f, os.path.join(GA, f)))
    # traces RAM (MAME) d'Hyper et d'Upper lues par relogement_a5_v3.py (carte_dyn ; absentes -> autre table A5)
    for t in ("h_versus", "h_training", "u_gagne00", "u_perdu00", "u_versus"):
        L.append(("greffe/traces/%s/ram.txt" % t, GA + "/traces/%s/ram.txt" % t))
    # carte d'image d'Upper (CARTE5 de donnees2) et hooks du traducteur d'origine (plan.py)
    L.append(("greffe/constructions/u5_temoin7/carte_image.txt", GA + "/constructions/u5_temoin7/carte_image.txt"))
    if os.path.exists(GA + "/untranspile/hooks_fork_ro9.json"):
        L.append(("greffe/untranspile/hooks_fork_ro9.json", GA + "/untranspile/hooks_fork_ro9.json"))
    # analyses communes : carto_ro9 (commun.py), traducteur d'origine (mips.py...), etude_upper_hyper (pkl)
    dossier(W + "/carto_ro9", "carto", "*.py")
    dossier(A + "/hsfa/scripts/untranspile", "ut", "*.py")
    dossier(A + "/hsfa/scripts/untranspile", "ut", "*.json")
    dossier(W + "/etude_upper_hyper", "eu", "*.pkl")
    dossier(W + "/etude_upper_hyper", "eu", "*.py")
    L = [(d, REMPLACE.get(d, s)) for d, s in L]
    return L

def marque(t):
    for a, m in MARQUES: t = t.replace(a, m)
    return t

def figer():
    if os.path.exists(FIGE): sys.exit("%s existe deja (copie figee : ne pas refaire)" % FIGE)
    n = nm = 0; lignes = []
    for d, s in sources():
        q = os.path.join(FIGE, d); os.makedirs(os.path.dirname(q), exist_ok=True)
        if d in MD5_RO9A22: assert md5(s) == MD5_RO9A22[d], (d, s, md5(s))
        if d.endswith((".py", ".sh", ".lua")):
            t = open(s, encoding="utf-8", errors="surrogateescape").read(); t2 = marque(t)
            if t2 != t: nm += 1
            open(q, "w", encoding="utf-8", errors="surrogateescape").write(t2)
        else:
            shutil.copyfile(s, q)
        lignes.append("%s  %s  <- %s" % (md5(s), d, s.replace(W, "<atelier>")))
        n += 1
    open(os.path.join(FIGE, "SOURCES.txt"), "w").write("# md5 de la SOURCE (avant marques)  copie  <- source\n" + "\n".join(lignes) + "\n")
    print("figer : %d fichiers, %d avec marques -> %s" % (n, nm, FIGE))

def materialiser(dest, valeurs, racines=None):
    """recopie les racines (defaut : la copie figee complete ; sinon code + releves) dans dest, marques remplacees"""
    val = dict(valeurs)
    if os.sep == "\\":   # Windows : chemins en « / » (ils vont dans des chaines Python : « C:\Users », « \t »... casseraient)
        val = {m: v.replace("\\", "/") for m, v in val.items()}
    for _a, m in MARQUES:
        val.setdefault(m, "/chemin/atelier/absent/" + m.strip("@"))
    n = 0
    for R in (racines or [FIGE]):
      for racine, _ds, fs in os.walk(R):
        for f in fs:
            s = os.path.join(racine, f); r = os.path.relpath(s, R); q = os.path.join(dest, r)
            os.makedirs(os.path.dirname(q), exist_ok=True)
            if f.endswith((".py", ".sh", ".lua")):
                t = open(s, encoding="utf-8", errors="surrogateescape").read()
                for m, v in val.items(): t = t.replace(m, v)
                open(q, "w", encoding="utf-8", errors="surrogateescape").write(t)
            else:
                shutil.copyfile(s, q)                  # copie (pas de lien dur : les outils reecrivent donnees/*.pkl)
            n += 1
    print("materialiser : %d fichiers -> %s" % (n, dest))

if __name__ == "__main__":
    if sys.argv[1:2] == ["figer"]: figer()
    elif sys.argv[1:2] == ["materialiser"]:
        materialiser(sys.argv[2], [a.split("=", 1) for a in sys.argv[3:]])
    else: sys.exit(__doc__)
