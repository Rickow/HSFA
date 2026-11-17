#!/usr/bin/env python3
"""HSFA builder: one executable that turns YOUR disc images into the HSFA game archives.
Constructeur HSFA : un seul executable, de VOS images de disque aux archives des jeux HSFA.

  hsfa-constructeur                          window (or text prompts without a display) / fenetre (ou questions)
  hsfa-constructeur IMAGE [--psp ISO_PSP] [--sortie DIR]
      IMAGE   : Street Fighter Alpha Anthology (PS2, USA, SLUS-21317), .iso or .chd
      ISO_PSP : optional / facultatif : Street Fighter Alpha 3 MAX (PSP, USA ULUS-10062 or Europe ULES-00235), .iso or .chd
                -> also builds Upper MAX (sfa3umhsfa.zip) / construit aussi Upper MAX
      Windows : drag the PS2 image onto the executable / glisser l'image PS2 sur l'executable
  --jeux / --games sfa3,upper,hyper,uppermax,hyperarcade : games to build / jeux a construire (default / defaut :
      sfa3,upper,hyper, + uppermax with / avec --psp ; hyperarcade = Hyper + Arcade, experimental, also builds Upper and
      Hyper with their zips / construit aussi Upper et Hyper avec leurs zips) ; the window has one check box per game /
      la fenetre a une case par jeu
  options : --console ; --cible fbneo-hsfa (default / defaut) | fbneo-autonome | mister | cps2-banques ; --oui / --yes ;
            anything after « -- » goes to hsfa_build.py as is / le reste apres « -- » va a hsfa_build.py
  fbneo-autonome (standalone FBNeo HSFA for Windows, test build): its concession is announced and confirmed, then the
  SAME archives as fbneo-hsfa are built / annonce et confirmation, puis les MEMES archives que fbneo-hsfa.
  mister, cps2-banques: not available yet; the builder announces their concessions per game and the measured budgets,
  asks for confirmation, and builds nothing (report mode) / pas encore disponibles : annonce des concessions par jeu et
  des budgets mesures, confirmation, rien n'est construit (bilan).
  Language of these announcements / langue des annonces : HSFA_LANGUE=fr|en, else the system's / sinon celle du systeme.

Embeds / embarque : Python, NumPy, the HSFA scripts (scripts/, src/, tools/, max/), hsfa_oggenc (portable Ogg Vorbis
encoder, tools/flux/oggenc), fluxtool (tools/flux), hsfa_rejeu_iso (Hyper's replay table from the ISO,
tools/son-hyper/rejeu_iso) and libchdr. No game data / aucune donnee de jeu. Licences: TIERS.md.

The same executable also plays the « python » that the build starts for each step / sert aussi d'interpreteur :
  <exe> SCRIPT.py ARGS...     <exe> -c CODE     <exe> -m MODULE ARGS...
"""
import os, runpy, sys, threading, time

GELE = getattr(sys, "frozen", False)
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = getattr(sys, "_MEIPASS", ICI)
# depot : dans l'executable, copie embarquee sous <BASE>/depot ; hors executable, racine du depot (tools/constructeur/../..)
DEPOT = os.path.join(BASE, "depot") if GELE else os.path.normpath(os.path.join(ICI, "..", ".."))
BIN = os.path.join(BASE, "bin") if GELE else os.environ.get("HSFA_CONSTRUCTEUR_BIN", os.path.join(ICI, "bin"))
X = ".exe" if os.name == "nt" else ""
VERSION = "0.2"


def _outils_natifs():
    """outils embarques -> variables lues par tools/flux/flux_ogg.py et transmises par hsfa_build.env()"""
    for var, nom in (("HSFA_FLUXTOOL", "fluxtool" + X), ("HSFA_OGGENC", "hsfa_oggenc" + X),
                     ("HSFA_REJEU_ISO", "hsfa_rejeu_iso" + X)):          # (rejeu_iso) lu par gen_rejeu_iso.py
        p = os.path.join(BIN, nom)
        if os.path.exists(p): os.environ.setdefault(var, p)


# ----------------------------------------------------------------------------------------------------------------------
# Role d'interpreteur : l'executable gele (PyInstaller) demarre Python isole (sys.flags.isolated = 1 : ni PYTHONPATH, ni
# PYTHONDONTWRITEBYTECODE, ni PYTHONUNBUFFERED, ni dossier courant). Les etapes (hsfa_build, regen_max d'Upper MAX...)
# attendent un VRAI « python » : ce qui en depend est refait ici, a la main, comme CPython le fait au demarrage.
# Ne peut pas etre refait apres le demarrage : PYTHONUTF8 (mode UTF-8 TOUJOURS actif, option du .spec ; hsfa_build le
# demande de toute facon), PYTHONHASHSEED (hachage NON aleatoire dans l'executable, graine 0 ; rien n'en depend).
# ----------------------------------------------------------------------------------------------------------------------
ARGV_ORIGINE = list(sys.argv)          # avant _role_python, qui remplace sys.argv par celui de l'etape lancee
ROLE_PYTHON = False                    # True : l'executable sert d'interpreteur a une etape (jamais d'attente d'Entree)
OPTIONS_PYTHON = set("bBdEIOPqsSuv")    # options d'une lettre de CPython admises (seules ou groupees : -uB)


def _options_python(a):
    """options de l'interpreteur avant -c / -m / script : rend (lettres, reste). « -X v » / « -W v » : sans effet ici
    (-X utf8 : deja actif). S'arrete au premier argument qui n'en est pas une (options du constructeur : --console...)"""
    lettres = set()
    while a:
        o = a[0]
        if o in ("-X", "-W") and len(a) >= 2:
            a = a[2:]; continue
        if o.startswith(("-X", "-W")) and len(o) > 2:
            a = a[1:]; continue
        if len(o) >= 2 and o[0] == "-" and set(o[1:]) <= OPTIONS_PYTHON:
            lettres |= set(o[1:]); a = a[1:]; continue
        break
    return lettres, a


def _environnement_python(lettres, chemin0):
    """ce que CPython fait au demarrage et que l'executable isole ne fait pas : sys.path[0], PYTHONPATH,
    PYTHONDONTWRITEBYTECODE / -B, PYTHONPYCACHEPREFIX, PYTHONUNBUFFERED / -u, PYTHONIOENCODING ; -E / -I : variables
    PYTHON* ignorees ; -I / -P / PYTHONSAFEPATH : rien devant sys.path"""
    env = {} if lettres & {"E", "I"} else os.environ
    devant = []
    if chemin0 is not None and not lettres & {"I", "P"} and not env.get("PYTHONSAFEPATH"):
        devant.append(chemin0)
    devant += [os.path.abspath(p) for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]   # comme getpath.py
    sys.path[:0] = devant                    # avant les modules embarques : une copie sur disque l'emporte (regen_max)
    # executable gele : les sources sont dans un dossier extrait NOUVEAU a chaque lancement : du bytecode ecrit (meme
    # sous PYTHONPYCACHEPREFIX) ne resservirait jamais et s'entasserait (cache/pyc/tmp/_MEI...) : jamais ecrit
    sys.dont_write_bytecode = GELE or "B" in lettres or bool(env.get("PYTHONDONTWRITEBYTECODE"))
    if env.get("PYTHONPYCACHEPREFIX"):
        sys.pycache_prefix = os.path.abspath(env["PYTHONPYCACHEPREFIX"])
    enc = env.get("PYTHONIOENCODING", "")
    codage, _, erreurs = enc.partition(":")
    sans_tampon = "u" in lettres or bool(env.get("PYTHONUNBUFFERED"))
    for nom in ("stdin", "stdout", "stderr"):
        f = getattr(sys, nom, None)
        if f is None or not hasattr(f, "reconfigure"):
            continue
        k = {}
        if codage: k["encoding"] = codage
        if erreurs: k["errors"] = erreurs
        if sans_tampon and nom != "stdin": k.update(line_buffering=True, write_through=True)
        if k:
            try: f.reconfigure(**k)
            except (ValueError, LookupError, OSError): pass


def _role_python(argv):
    """True si l'executable est lance comme interpreteur Python (etape de hsfa_build, test de numpy, sous-script) ;
    l'etape s'execute alors ici, comme « python [options] -c CODE | -m MODULE | SCRIPT.py ARGS... »"""
    global ROLE_PYTHON
    lettres, a = _options_python(argv[1:])
    if not a: return False
    if a[0] in ("-c", "-m") and len(a) >= 2: mode = a[0]
    elif a[0].lower().endswith(".py"): mode = "script"
    else: return False
    ROLE_PYTHON = True
    _outils_natifs()
    if mode == "script" and not os.path.isfile(a[0]):
        sys.stderr.write("%s: can't open file %r: [Errno 2] No such file or directory\n" % (os.path.basename(argv[0]), a[0]))
        raise SystemExit(2)                                            # comme python (et pas « image introuvable »)
    if mode == "-c": chemin0 = ""                                      # dossier courant
    elif mode == "-m": chemin0 = os.getcwd()
    else:                                                              # dossier du script (liens resolus, sauf Windows)
        chemin0 = os.path.dirname(os.path.abspath(a[0]) if os.name == "nt" else os.path.realpath(a[0]))
    _environnement_python(lettres, chemin0)
    try:
        if mode == "-c":
            sys.argv = ["-c"] + a[2:]
            exec(compile(a[1], "<string>", "exec"), {"__name__": "__main__", "__builtins__": __builtins__})
        elif mode == "-m":
            sys.argv = [a[1]] + a[2:]
            runpy.run_module(a[1], run_name="__main__", alter_sys=True)
        else:
            sys.argv = a
            runpy.run_path(a[0], run_name="__main__")
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise SystemExit(130)
    except BaseException:                    # comme python : trace sur stderr, code 1 (sans le message du chargeur)
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
    return True


def _garder_console_ouverte(argv_origine, role_python, windows=os.name == "nt"):
    """Windows : image glissee sur l'executable (un seul argument, pas une option) -> attendre Entree avant que la
    console ne se ferme. Jamais quand l'executable sert d'interpreteur a une etape (v0.1.10 : chaque etape a un seul
    argument attendait Entree, construction d'Upper MAX bloquee)"""
    return (windows and not role_python and len(argv_origine) == 2 and not argv_origine[1].startswith("-")
            and not argv_origine[1].lower().endswith(".py"))


def _hsfa_build():
    sys.path.insert(0, os.path.join(DEPOT, "scripts", "construction"))
    import hsfa_build
    return hsfa_build


def _iso_de(image, sortie, psp=False):
    """chemin de l'ISO tiree d'un .chd : <sortie>/cache/iso_chd[_psp]/<nom>.iso ; l'image elle-meme sinon"""
    if not image.lower().endswith(".chd"):
        return image
    nom = os.path.splitext(os.path.basename(image))[0] + ".iso"
    return os.path.join(sortie, "cache", "iso_chd_psp" if psp else "iso_chd", nom)


def _chd_a_jour(image, iso):
    """True si le .chd a deja ete decompresse dans iso (marque <iso>.source : chemin, taille, date)"""
    sig = "%s %d %d\n" % (os.path.abspath(image), os.path.getsize(image), int(os.path.getmtime(image)))
    marque = iso + ".source"
    return os.path.exists(iso) and os.path.exists(marque) and open(marque).read() == sig, sig


def _image_vers_iso(image, sortie, psp=False, journal=print):
    """.chd -> .iso <sortie>/cache/iso_chd[_psp]/<nom>.iso (meme nom de base : hsfa_info.txt identique a une
    construction depuis l'ISO du meme nom) ; PS2 : ISO creuse (fichiers utiles) ; PSP : image complete (250 Mo)"""
    if not image.lower().endswith(".chd"):
        return image
    import chd_iso
    iso = _iso_de(image, sortie, psp); os.makedirs(os.path.dirname(iso), exist_ok=True)
    marque = iso + ".source"
    a_jour, sig = _chd_a_jour(image, iso)
    if a_jour:
        journal("CHD déjà décompressé / CHD already unpacked: %s" % iso); return iso
    journal("CHD -> ISO%s: %s" % ("" if psp else " (fichiers utiles seulement / needed files only)", iso))
    vu = set()
    def progres(n, t):                       # une ligne tous les 10 %
        p = 100 * n // t // 10 * 10
        if p not in vu: vu.add(p); journal("  %d %%" % p)
    chd_iso.vers_iso(image, iso, tout=psp, progres=progres)
    open(marque, "w").write(sig)
    return iso


CIBLE_DEFAUT = "fbneo-hsfa"


def _cibles():
    d = os.path.join(DEPOT, "scripts", "construction")
    if d not in sys.path:
        sys.path.insert(0, d)
    import cibles
    return cibles


# Jeux proposes (cases de la fenetre, --jeux) : ordre de hsfa_build.JEUX. Pas hyperarcademax (pilote sfa3hamhsfa) : il
# demande le patch 0033 du coeur, absent des coeurs publies. Hyper + Arcade (greffe experimentale) : la version de la
# greffe est celle que fixe hsfa_build (HA_ETAT, HA_RECETTE), rien ici ne la choisit ; Upper MAX : UM_ETAT.
JEUX_CHOIX = ["sfa3", "upper", "hyper", "uppermax", "hyperarcade"]
JEUX_DEFAUT = ["sfa3", "upper", "hyper"]                 # + uppermax avec l'ISO PSP (comportement d'avant --jeux)


def jeux_construits(psp=None, jeux=None):
    """jeux demandes, dans l'ordre de JEUX_CHOIX ; jeux=None : le choix par defaut (+ Upper MAX avec l'ISO PSP)"""
    if jeux is None:
        return JEUX_DEFAUT + (["uppermax"] if psp else [])
    return [j for j in JEUX_CHOIX if j in jeux]


def verifie_jeux(texte, psp=None):
    """« sfa3,hyper » (--jeux) -> liste des jeux ; ValueError avec un message clair (francais / anglais) sinon"""
    jeux = [j.strip().lower() for j in texte.replace(" ", ",").split(",") if j.strip()]
    if "hyperarcademax" in jeux:
        raise ValueError("hyperarcademax : pas proposé, il demande le patch 0033 du cœur, absent des cœurs publiés / "
                         "not offered: it needs core patch 0033, not in the published cores")
    inconnus = [j for j in jeux if j not in JEUX_CHOIX]
    if inconnus or not jeux:
        raise ValueError("jeux inconnus / unknown games: %s (connus / known: %s)" % (",".join(inconnus) or "(aucun / none)",
                                                                                  ",".join(JEUX_CHOIX)))
    if "uppermax" in jeux and not psp:
        raise ValueError("uppermax : il faut l'ISO PSP de SFA3 MAX (--psp) / Upper MAX needs the PSP ISO (--psp)")
    return jeux_construits(psp, jeux)


_PLANS = {}


def _plan(jeux, psp):
    """plan REEL de hsfa_build pour « --jeux JEUX » (Construction.etapes() et prevoit(), sans rien lancer), fait dans un
    dossier temporaire : la vraie sortie n'est jamais touchee (pas de rangement, pas de journal). Mis en cache."""
    cle = (tuple(jeux), bool(psp))
    if cle not in _PLANS:
        import shutil, tempfile
        H = _hsfa_build()
        T = tempfile.mkdtemp(prefix="hsfa_plan_")
        try:
            argv = ["--anthology", os.path.join(T, "a.iso"), "--sortie", T, "--jeux", ",".join(jeux)]
            if psp: argv += ["--psp-iso", os.path.join(T, "p.iso")]
            c = H.Construction(H.parseur().parse_args(argv))
            try:
                E = c.etapes()
                _PLANS[cle] = ([e[0] for e in E], c.prevoit(E))   # [(etape, a_faire, s, jeu)] : sortie vide, tout a faire
            finally:
                c.log.f.close()                    # Windows : un fichier ouvert empeche d'effacer le dossier
        finally:
            shutil.rmtree(T, ignore_errors=True)
    return _PLANS[cle]


def selection(jeux, psp=None):
    """ce que hsfa_build construit VRAIMENT pour ces jeux (lu dans son plan, rien de code en dur ici) :
      jeux      : jeux demandes (ordre fixe) ; argument --jeux
      archives  : jeux dont le zip est produit (etape paquet_<jeu> dans le plan), demandes ou non
      aussi     : {jeu dont le zip est produit sans etre demande : [jeux demandes qui l'entrainent]}
      etapes    : {jeu sans zip : [ses etapes qui tournent quand meme]} (ex. Hyper seul : son_upper, gfx_upper)
      pour      : {jeu de « etapes » : [jeux demandes qui ont besoin de ces etapes]}
      durees    : [(libelle, s)] par jeu, total : s (sortie vide, durees de reference de hsfa_build)"""
    H = _hsfa_build()
    jeux = jeux_construits(psp, jeux)
    if "uppermax" in jeux and not psp:
        raise ValueError("uppermax sans ISO PSP / without the PSP ISO")
    noms, prevu = _plan(jeux, psp)
    archives = [j for j in H.JEUX_AFFICHES if "paquet_" + j in noms]
    aussi = {}
    for a in archives:
        if a not in jeux:
            aussi[a] = [r for r in jeux if "paquet_" + a in _plan([r], psp)[0]]
    etapes = {}
    for n in noms:                                 # gfx_upper, son_upper... : suffixe = un jeu sans zip
        j = n.rsplit("_", 1)[-1]
        if j in H.JEUX and j not in archives and not n.startswith("paquet_"):
            etapes.setdefault(j, []).append(n)
    pour = {j: [r for r in jeux if any(n in _plan([r], psp)[0] for n in et)] for j, et in etapes.items()}
    par_jeu = {}
    for _n, _f, s, j in prevu:
        if j: par_jeu[j] = par_jeu.get(j, 0) + s
    durees = [(H.JEUX_LIBELLES[j], par_jeu[j]) for j in H.JEUX_AFFICHES if j in par_jeu]
    return dict(jeux=jeux, archives=archives, aussi=aussi, etapes=etapes, pour=pour, durees=durees,
                total=sum(s for _n, _f, s, _j in prevu))


def libelle(j):
    return _hsfa_build().JEUX_LIBELLES[j]


def texte_selection(sel):
    """lignes d'information (fenetre et console) : ce qui est construit en plus des jeux demandes, sans mentir"""
    L = []
    noms = lambda js: ", ".join(libelle(r) for r in js)
    groupes = {}                                   # meme demandeur : une seule ligne (« Upper, Hyper »)
    for a, par in sel["aussi"].items():
        groupes.setdefault(tuple(par), []).append(a)
    for par, js in groupes.items():
        L.append("+ %s : construit%s aussi, zip%s compris (requis par %s) / also built, zip%s included (needed by %s)"
                 % (noms(js), "s" if len(js) > 1 else "", "s" if len(js) > 1 else "", noms(par),
                    "s" if len(js) > 1 else "", noms(par)))
    for j, et in sel["etapes"].items():
        p = noms(sel["pour"].get(j, []))
        L.append("+ %s : étapes %s seulement, sans son zip (requises par %s) / only steps %s, no zip (needed by %s)"
                 % (libelle(j), ", ".join(et), p, ", ".join(et), p))
    return L


def texte_duree(sel):
    H = _hsfa_build()
    return "Durée estimée (sortie vide) / estimated time (empty output): %s ; total %s" % (
        ", ".join("%s %s" % (lib, H.duree_texte(s)) for lib, s in sel["durees"]), H.duree_texte(sel["total"]))


def etat_cases(choix, psp):
    """(fenetre) etat des cases : choix = {jeu: coche par le joueur}. Rend (cases, sel) : cases = {jeu: (coche, actif)} ;
    une case entrainee par un autre jeu (zip produit aussi) est cochee et grisee ; Upper MAX grisee sans ISO PSP ;
    sel = selection() des jeux demandes, None si aucun"""
    demandes = [j for j in JEUX_CHOIX if choix.get(j) and (j != "uppermax" or psp)]
    sel = selection(demandes, psp) if demandes else None
    cases = {}
    for j in JEUX_CHOIX:
        if j == "uppermax" and not psp:
            cases[j] = (False, False)
        elif sel and j in sel["aussi"]:
            cases[j] = (True, False)
        else:
            cases[j] = (bool(choix.get(j)), True)
    return cases, sel


def environ(s):
    """« ≈ 3 min », « ≈ 1 h 05 » (au moins 1 min)"""
    m = max(1, int(s / 60 + 0.5))
    return "≈ %d min" % m if m < 60 else "≈ %d h %02d" % (m // 60, m % 60)


def durees_cases(choix, psp, sel=None):
    """(fenetre) duree approximative sous chaque case et total : ({jeu: texte}, total). Jeu construit (coche ou
    entraine) : sa part du plan (« ≈ 3 min ») ; case libre : ce que la cocher ajoute (« +≈ 3 min ») ; Upper MAX sans ISO
    PSP : rien. Durees de selection() (sortie vide), donc la somme des parts = le total."""
    demandes = [j for j in JEUX_CHOIX if choix.get(j) and (j != "uppermax" or psp)]
    if sel is None and demandes: sel = selection(demandes, psp)
    parts = dict(sel["durees"]) if sel else {}
    if parts:                                      # parts arrondies a la minute en gardant leur somme = total affiche
        cible = max(1, int(sel["total"] / 60 + 0.5))
        m = {k: int(v // 60) for k, v in parts.items()}
        for k in sorted(parts, key=lambda k: parts[k] / 60 - m[k], reverse=True)[:max(0, cible - sum(m.values()))]:
            m[k] += 1
        parts = {k: v * 60 for k, v in m.items()}
    textes = {}
    for j in JEUX_CHOIX:
        if libelle(j) in parts:
            textes[j] = environ(parts[libelle(j)])
        elif j == "uppermax" and not psp:
            textes[j] = ""
        else:
            textes[j] = "+" + environ(selection(demandes + [j], psp)["total"] - (sel["total"] if sel else 0))
    return textes, ("Total " + environ(sel["total"]) if sel else "")


def temps_texte(s):
    """« 45 s », « 12 min 05 s », « 1 h 02 min 05 s »"""
    s = int(s + 0.5)
    if s < 60: return "%d s" % s
    if s < 3600: return "%d min %02d s" % (s // 60, s % 60)
    return "%d h %02d min %02d s" % (s // 3600, s % 3600 // 60, s % 60)


def produit(cible):
    """True si le format produit des archives (fbneo-hsfa, fbneo-autonome en essai) ; False : bilan seulement"""
    return cible == CIBLE_DEFAUT or _cibles().CIBLES[cible]["dispo"]


def annonce(cible, psp=None, journal=print, demande=None, oui=False, jeux=None):
    """format autre que fbneo-hsfa : annonce (concessions, budgets) puis confirmation ; True = confirme.
    demande(cible, langue) -> bool : question par la fenetre ; None : question dans le terminal"""
    K = _cibles(); lg = K.langue_defaut()
    jeux = jeux_construits(psp, jeux)
    if demande is None or oui:                            # console (ou --oui) : question dans le terminal
        ok = K.confirme(cible, jeux, oui=oui, ecrit=journal, langue=lg)
    else:                                                 # fenetre : texte au journal, question par la fenetre
        journal(K.rapport(cible, jeux, lg))
        ok = demande(cible, lg)
    journal("")
    if not ok:
        journal("Format non confirmé : rien n'est fait." if lg == "fr" else "Format not confirmed: nothing done.")
    elif produit(cible):
        journal("Format confirmé : construction des mêmes archives que pour FinalBurn Neo HSFA." if lg == "fr" else
                "Format confirmed: building the same archives as for FinalBurn Neo HSFA.")
    return ok


def bilan(cible, psp=None, journal=print, demande=None, oui=False, jeux=None):
    """format qui ne produit rien (mister, cps2-banques) : annonce, confirmation, AUCUNE sortie ; rend 0 / 2"""
    if not annonce(cible, psp, journal, demande, oui, jeux):
        return 2
    lg = _cibles().langue_defaut()
    journal("Mode bilan : format pas encore disponible ; aucune archive n'est produite." if lg == "fr" else
            "Report mode: format not available yet; no archive is produced.")
    return 0


def construit(image, sortie, psp=None, extra=(), journal=print, cible=CIBLE_DEFAUT, demande=None, oui=False,
              confirme=False, avancement=None, jeux=None):
    """construction des jeux choisis (jeux=None : le choix par defaut) ; rend le code de sortie de hsfa_build. Format qui
    ne produit rien : bilan seulement ; fbneo-autonome : annonce et confirmation (sauf confirme=True, deja faites), puis
    les memes archives que fbneo-hsfa. avancement(evenement, **infos) : duree estimee et etapes (hsfa_build.AVANCEMENT),
    appele depuis ce fil"""
    if not produit(cible):
        return bilan(cible, psp, journal, demande, oui, jeux)
    if cible != CIBLE_DEFAUT and not confirme and not annonce(cible, psp, journal, demande, oui, jeux):
        return 2
    _outils_natifs()
    H = _hsfa_build()
    H.AVANCEMENT = avancement
    try:
        return _construit(H, image, sortie, psp, extra, journal, cible, jeux)
    finally:
        H.AVANCEMENT = None


def zip_de(j):
    """nom du zip d'un jeu (hsfa_build.JEUX), sans .zip"""
    return _hsfa_build().JEUX[j]["zip"]


def zips_construits(sortie, psp=None, jeux=None):
    """archives des jeux construits (zips produits par le plan, entraines compris) presentes a la racine de la sortie
    (v0.1.11 : plus de sous-dossier archives/)"""
    j = jeux_construits(psp, jeux)
    if "uppermax" in j and not psp: j = [x for x in j if x != "uppermax"]
    archives = selection(j, psp)["archives"] if j else []
    return [zip_de(a) + ".zip" for a in archives if os.path.isfile(os.path.join(sortie, zip_de(a) + ".zip"))]


def message_fin(r, sortie, psp=None, jeux=None):
    """message de fin (console, journal et boite de la fenetre) : « Terminé : N jeux dans … » ou l'echec"""
    sortie = os.path.abspath(sortie)
    if r == 0:
        n = len(zips_construits(sortie, psp, jeux))
        return "Terminé : %d jeux dans %s\nDone: %d games in %s" % (n, sortie, n, sortie)
    j = os.path.join(sortie, "hsfa-travail", "journal.txt")
    return ("ÉCHEC de la construction (code %s) : voir %s\nBuild FAILED (code %s): see %s" % (r, j, r, j))


def signal_fin(ok=True):
    """son systeme sans dependance : winsound sous Windows, sinon la cloche du terminal (la fenetre ajoute bell() de Tk)"""
    try:
        import winsound                                   # Windows seulement
        winsound.MessageBeep(winsound.MB_OK if ok else winsound.MB_ICONHAND)
        return
    except Exception:                                     # noqa : pas Windows, ou pas de son
        pass
    try:
        if sys.stdout and sys.stdout.isatty():
            sys.stdout.write("\a"); sys.stdout.flush()
    except (AttributeError, ValueError, OSError):
        pass


def _construit(H, image, sortie, psp, extra, journal, cible, jeux=None):
    t0 = time.monotonic()
    sortie = os.path.abspath(sortie); os.makedirs(sortie, exist_ok=True)
    image = os.path.abspath(image); psp = psp and os.path.abspath(psp)
    jeux = jeux_construits(psp, jeux)
    if "uppermax" not in jeux: psp = None       # ISO PSP donnee sans Upper MAX choisi : ni lue ni decompressee
    elif not psp: raise ValueError("uppermax sans ISO PSP / without the PSP ISO")
    if not any(x == "--jeux" or x.startswith("--jeux=") for x in extra):   # (« -- --jeux ... » : hsfa_build decide)
        journal("Jeux / games: %s" % ", ".join(libelle(j) for j in jeux))
        for l in texte_selection(selection(jeux, psp)):
            journal(l)
    T = H.dossier_travail(sortie)              # hsfa-travail/ (une sortie de l'ancienne forme y est rangee d'abord)
    argv = ["--anthology", _iso_de(image, T), "--sortie", sortie, "--jeux", ",".join(jeux), "--flux-format", "ogg"]
    if psp: argv += ["--psp-iso", _iso_de(psp, T, True)]
    argv += list(extra)
    chd = [i for i, p in ((image, False), (psp, True)) if i and i.lower().endswith(".chd")
           and not _chd_a_jour(i, _iso_de(i, T, p))[0]]
    if chd:                                     # duree annoncee AVANT la decompression du .chd (hsfa_build l'annonce
        try:                                    # sinon au debut de la construction)
            H.prevision(argv)
            journal("(+ décompression du CHD / + unpacking the CHD)")
        except Exception as x:                  # noqa : une estimation impossible n'empeche pas la construction
            journal("(durée estimée indisponible / no estimated time: %s)" % x)
    r = 1
    try:
        argv[1] = _image_vers_iso(image, T, False, journal)
        if psp: _image_vers_iso(psp, T, True, journal)
        sys.argv = ["hsfa_build.py"] + argv
        r = H.main()
    finally:                                    # duree totale (decompression du .chd comprise), echec compris
        duree_totale(time.monotonic() - t0, T, journal)
    journal("")
    journal(message_fin(r, sortie, psp, jeux))
    if r == 0:
        for f in zips_construits(sortie, psp, jeux):
            journal("  " + f)
        journal("Copiez-les dans le dossier des ROM de FinalBurn Neo HSFA / copy them to your FBNeo HSFA ROM folder.")
        journal("(fichiers de travail / work files: %s)" % T)
        if cible == "fbneo-autonome":
            journal("FinalBurn Neo HSFA autonome : fbneo64.exe (4:3) ou fbneo64ws.exe (16:9) / standalone: fbneo64.exe "
                    "(4:3) or fbneo64ws.exe (16:9).")
    return r


def duree_totale(s, T, journal=print):
    """ligne « Durée totale » : journal (fenetre / terminal) et fin de hsfa-travail/journal.txt"""
    ligne = "Durée totale / total time: %s" % temps_texte(s)
    journal(ligne)
    try:
        with open(os.path.join(T, "journal.txt"), "a", encoding="utf-8") as f:
            f.write("%s    %s (constructeur / builder)\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), ligne))
    except OSError:
        pass


def sortie_defaut():
    base = os.path.dirname(sys.executable if GELE else os.path.abspath(__file__))
    if sys.platform == "darwin" and (".app/" in base or base.startswith("/private/")): base = os.path.expanduser("~")
    return os.path.join(base, "HSFA-sortie")


# ----------------------------------------------------------------------------------------------------------------------
# Interface
# ----------------------------------------------------------------------------------------------------------------------
def _demande(texte):
    return input(texte).strip().strip("\"'")


def _choix_cible():
    K = _cibles(); noms = list(K.CIBLES)
    print("Format de sortie / output format :")
    for k, n in enumerate(noms, 1):
        print("  %d. %s / %s" % (k, K.libelle(n, "fr"), K.libelle(n, "en")))
    r = _demande("Choix / choice [1] : ")
    return noms[int(r) - 1] if r.isdigit() and 1 <= int(r) <= len(noms) else noms[0]


def console(image=None, sortie=None, psp=None, extra=(), questions=True, cible=None, oui=False, jeux=None):
    """jeux : liste deja verifiee (verifie_jeux) ou None (choix par defaut : SFA3, Upper, Hyper, + Upper MAX avec l'ISO
    PSP)"""
    print("Constructeur HSFA %s / HSFA builder" % VERSION)
    if cible is None:
        cible = _choix_cible() if questions else CIBLE_DEFAUT
    if not produit(cible):
        if questions and psp is None and jeux is None and sys.stdin and sys.stdin.isatty():
            psp = _demande("Upper MAX aussi (ISO PSP) ? o/N / Upper MAX too? y/N : ").lower() in ("o", "y") or None
        return bilan(cible, psp, oui=oui, jeux=jeux)
    confirme = False
    if cible != CIBLE_DEFAUT and not image:              # annonce avant les questions sur les images
        if not annonce(cible, psp, oui=oui, jeux=jeux):
            return 2
        confirme = True
    if not image:
        image = _demande("Image PS2 de l'Anthology (.iso ou .chd ; glissez le fichier ici) / PS2 disc image: ")
        if questions and psp is None and (jeux is None or "uppermax" in jeux):
            psp = _demande("ISO PSP de SFA3 MAX (USA ou Europe), facultatif : Entrée pour passer / optional PSP ISO, "
                           "Enter to skip: ") or None
    if not os.path.isfile(image):
        print("Introuvable / not found: %s" % image); return 1
    if psp and not os.path.isfile(psp):
        print("Introuvable / not found: %s" % psp); return 1
    if jeux is not None and "uppermax" in jeux and not psp:
        print("uppermax : il faut l'ISO PSP de SFA3 MAX (--psp) / Upper MAX needs the PSP ISO (--psp)"); return 2
    r = construit(image, sortie or sortie_defaut(), psp, extra, cible=cible, oui=oui, confirme=confirme, jeux=jeux)
    signal_fin(r == 0)
    return r


def _boite_confirmation(cible, langue):
    """boite « Confirmer malgre ces concessions ? » (fenetre) ; True = oui"""
    from tkinter import messagebox
    K = _cibles(); nom = K.CIBLES[cible][langue]
    if langue == "fr":
        texte = ("Format « %s » : les concessions et les budgets sont dans le journal ci-dessous.\n\n"
                 "Confirmer malgré ces concessions ?" % nom)
        texte += ("\n\n(Les archives seront les mêmes que pour FinalBurn Neo HSFA.)" if produit(cible) else
                  "\n\n(Rien ne sera construit : format pas encore disponible.)")
    else:
        texte = ("Format \u201c%s\u201d: the concessions and budgets are in the log below.\n\n"
                 "Confirm despite these concessions?" % nom)
        texte += ("\n\n(The archives will be the same as for FinalBurn Neo HSFA.)" if produit(cible) else
                  "\n\n(Nothing will be built: format not available yet.)")
    return messagebox.askyesno("HSFA", texte)


def texte_avancement(evenement, infos):
    """(fenetre) texte de l'etiquette sous la barre, en francais et en anglais"""
    H = _hsfa_build()
    if evenement == "plan":
        jeux = ", ".join("%s %s" % (lib, H.duree_texte(s) if s else "à jour / up to date") for lib, s in infos["jeux"])
        return "Durée estimée / estimated time: %s ; total %s" % (jeux, H.duree_texte(infos["total"]))
    return "Étape / step %d / %d : %s%s — reste / left %s" % (infos["n"], infos["N"], infos["nom"],
                                                             " ✓" if infos["fait"] else "…", H.duree_texte(infos["reste"]))


def chrono_texte(s):
    """(fenetre) compteur du temps ecoule : « 4:07 », « 1:02:05 »"""
    s = int(s)
    return "%d:%02d" % (s // 60, s % 60) if s < 3600 else "%d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)


def fenetre(image=None, sortie=None, psp=None, cible=None, jeux=None):
    import queue, tkinter as tk
    from tkinter import filedialog, scrolledtext, ttk
    racine = tk.Tk(); racine.title("HSFA – constructeur / builder %s" % VERSION)
    v_img, v_out = tk.StringVar(value=image or ""), tk.StringVar(value=sortie or sortie_defaut())
    v_psp = tk.StringVar(value=psp or "")
    f = tk.Frame(racine, padx=10, pady=10); f.pack(fill="both", expand=True)

    def ligne(r, texte, var, choisir):
        tk.Label(f, text=texte, anchor="w").grid(row=r, column=0, sticky="w")
        tk.Entry(f, textvariable=var, width=70).grid(row=r, column=1, sticky="we", padx=4)
        tk.Button(f, text="…", command=choisir).grid(row=r, column=2)
    ligne(0, "Anthology (PS2, .iso / .chd)", v_img, lambda: v_img.set(filedialog.askopenfilename(
        filetypes=[("Image PS2", "*.iso *.chd"), ("*", "*")]) or v_img.get()))
    ligne(1, "SFA3 MAX (PSP, facultatif / optional)", v_psp, lambda: v_psp.set(filedialog.askopenfilename(
        filetypes=[("ISO PSP", "*.iso *.chd"), ("*", "*")]) or v_psp.get()))
    ligne(2, "Sortie / output", v_out, lambda: v_out.set(filedialog.askdirectory() or v_out.get()))
    tk.Label(f, text="Avec l'ISO PSP : Upper MAX possible / with the PSP ISO: Upper MAX available",
             fg="grey").grid(row=3, column=1, sticky="w")
    K = _cibles()
    lg = K.langue_defaut()
    libelles = {K.libelle(n, lg): n for n in K.CIBLES}
    v_cib = tk.StringVar(value=[l for l, n in libelles.items() if n == (cible or CIBLE_DEFAUT)][0])
    tk.Label(f, text="Format de sortie / output", anchor="w").grid(row=4, column=0, sticky="w")
    tk.OptionMenu(f, v_cib, *libelles).grid(row=4, column=1, sticky="w")
    # jeux : une case par jeu (JEUX_CHOIX) ; ce que la selection entraine (selection(), lu dans le plan de hsfa_build)
    # est montre sans mentir : zip produit aussi -> case cochee et grisee ; etapes seules -> mention grise
    tk.Label(f, text="Jeux / games", anchor="w").grid(row=5, column=0, sticky="nw")
    cadre = tk.Frame(f); cadre.grid(row=5, column=1, columnspan=2, sticky="w")
    choix = {j: j in (jeux if jeux is not None else jeux_construits(psp)) for j in JEUX_CHOIX}
    v_cases, cases, v_durees, v_total = {}, {}, {}, tk.StringVar(value="")
    v_info, v_etat, v_chrono = tk.StringVar(value=""), tk.StringVar(value=""), tk.StringVar(value="")
    etat = {"en_cours": False, "t0": 0.0, "psp": bool(psp)}

    def clic(j):
        choix[j] = bool(v_cases[j].get()); rafraichit()

    for k, j in enumerate(JEUX_CHOIX):
        v_cases[j] = tk.BooleanVar(value=choix[j])
        texte = libelle(j) + (" (expérimental / experimental)" if j == "hyperarcade" else "")
        cases[j] = tk.Checkbutton(cadre, text=texte, variable=v_cases[j], command=lambda j=j: clic(j))
        cases[j].grid(row=0, column=k, sticky="w", padx=(0, 8))
        v_durees[j] = tk.StringVar(value="")                      # duree approximative sous la case (durees_cases)
        tk.Label(cadre, textvariable=v_durees[j], fg="grey", anchor="w").grid(row=1, column=k, sticky="w", padx=(22, 8))
    tk.Label(cadre, textvariable=v_total, anchor="w").grid(row=1, column=len(JEUX_CHOIX), sticky="w", padx=(8, 0))
    tk.Label(f, textvariable=v_info, fg="grey", anchor="w", justify="left", wraplength=720).grid(
        row=6, column=1, columnspan=2, sticky="w")

    def demandes():
        return [j for j in JEUX_CHOIX if choix[j] and (j != "uppermax" or v_psp.get().strip())]

    def rafraichit(*_):
        """cases, mention de ce qui est construit aussi, duree estimee : suivent la selection et l'ISO PSP"""
        ps = bool(v_psp.get().strip())
        if ps and not etat["psp"]: choix["uppermax"] = True       # ISO PSP donnee : Upper MAX coche (comme avant)
        etat["psp"] = ps
        try:
            et, sel = etat_cases(choix, ps)
        except Exception as x:                                     # noqa : jamais de fenetre cassee par l'apercu
            v_info.set("(aperçu indisponible / no preview: %s)" % x); return
        for j, (coche, actif) in et.items():
            v_cases[j].set(coche)
            cases[j].configure(state="normal" if actif and not etat["en_cours"] else "disabled")
        try:
            textes, total = durees_cases(choix, ps, sel)
        except Exception:                                          # noqa : l'apercu des durees ne casse rien
            textes, total = {}, ""
        for j in JEUX_CHOIX: v_durees[j].set(textes.get(j, ""))
        v_total.set(total)
        lignes = texte_selection(sel) if sel else []
        if not ps: lignes.append("Upper MAX : donnez l'ISO PSP / give the PSP ISO")
        v_info.set("\n".join(lignes))
        if not etat["en_cours"]:
            v_etat.set(("Durée estimée (sortie vide ; détail sous les cases) / estimated time (empty output; details "
                        "under the boxes): " + environ(sel["total"])) if sel else "Aucun jeu choisi / no game selected")
            bouton.configure(state="normal" if sel else "disabled")
    v_psp.trace_add("write", rafraichit)

    # avancement : etape n / N et temps restant (hsfa_build.AVANCEMENT, recu par la file comme le journal) ; compteur
    # discret du temps ecoule a droite de la barre
    barre = ttk.Progressbar(f, orient="horizontal", mode="determinate", maximum=1, value=0)
    barre.grid(row=8, column=0, columnspan=2, sticky="we", pady=(6, 0))
    tk.Label(f, textvariable=v_chrono, fg="grey", anchor="e").grid(row=8, column=2, sticky="e", pady=(6, 0))
    tk.Label(f, textvariable=v_etat, anchor="w", justify="left", wraplength=960).grid(row=9, column=0, columnspan=3, sticky="we")
    log = scrolledtext.ScrolledText(f, width=100, height=22, state="disabled")
    log.grid(row=10, column=0, columnspan=3, pady=6, sticky="nsew")
    f.columnconfigure(1, weight=1)
    f.rowconfigure(10, weight=1)                  # le journal prend la place gagnee quand on agrandit la fenetre
    q = queue.Queue()

    class Flux:
        def write(self, s): q.put(s)
        def flush(self): pass

    plan = {"texte": ""}

    def tic():                                    # fil principal : compteur, une fois par seconde pendant la construction
        if etat["en_cours"]:
            v_chrono.set("⏱ %s" % chrono_texte(time.monotonic() - etat["t0"]))
            racine.after(1000, tic)

    def avance(evenement, infos):                 # fil principal seulement (appele par pompe)
        if evenement == "plan":
            plan["texte"] = texte_avancement("plan", infos)
            barre.configure(maximum=max(infos["N"], 1), value=0)
            v_etat.set(plan["texte"] if infos["N"] else plan["texte"] + "\n" + "Rien à refaire / nothing to redo")
        elif evenement == "etape":
            barre.configure(maximum=max(infos["N"], 1), value=infos["n"] - (0 if infos["fait"] else 1))
            v_etat.set(plan["texte"] + "\n" + texte_avancement("etape", infos))
        elif evenement == "fin":
            etat["en_cours"] = False
            v_chrono.set("⏱ %s" % chrono_texte(time.monotonic() - etat["t0"]))
            if infos["ok"]: barre.configure(value=barre.cget("maximum"))
            v_etat.set(plan["texte"] + "\n" + ("Terminé / done" if infos["ok"] else "ÉCHEC / FAILED"))
            bouton.configure(state="normal")
            for j, c in cases.items():
                c.configure(state="normal")
            rafraichit_cases()
            fin_visible(infos["ok"], infos.get("message") or ("OK" if infos["ok"] else "ÉCHEC / FAILED"))

    def rafraichit_cases():                       # apres la construction : cases seulement (le texte de fin reste)
        etat["en_cours"] = True
        try: rafraichit()
        finally: etat["en_cours"] = False
        et, _sel = etat_cases(choix, bool(v_psp.get().strip()))
        for j, (_c, actif) in et.items():
            cases[j].configure(state="normal" if actif else "disabled")

    def fin_visible(ok, message):                 # fil principal : son, fenetre au premier plan, message clair
        from tkinter import messagebox
        try: racine.bell()
        except tk.TclError: pass
        signal_fin(ok)
        try:
            racine.deiconify(); racine.lift(); racine.attributes("-topmost", True); racine.focus_force()
            racine.after(800, lambda: racine.attributes("-topmost", False))
        except tk.TclError:
            pass
        (messagebox.showinfo if ok else messagebox.showerror)("HSFA", message, parent=racine)

    def pompe():
        try:
            while True:
                s = q.get_nowait()
                if isinstance(s, tuple):
                    avance(*s); continue
                log.configure(state="normal"); log.insert("end", s); log.see("end")
                log.configure(state="disabled")
        except queue.Empty:
            pass
        racine.after(200, pompe)

    def lance():
        img = v_img.get().strip()
        jeux = demandes()
        ps = (v_psp.get().strip() or None) if "uppermax" in jeux else None    # ISO PSP lue seulement pour Upper MAX
        cib = libelles[v_cib.get()]
        if not jeux:
            q.put("Aucun jeu choisi / no game selected\n"); return
        if not produit(cib):                             # bilan : ni image ni sortie necessaires
            r = bilan(cib, ps, journal=lambda m: q.put(m + "\n"), demande=_boite_confirmation, jeux=jeux)
            q.put("\n%s\n" % (("BILAN" if lg == "fr" else "REPORT") if r == 0 else
                               ("ANNULÉ" if lg == "fr" else "CANCELLED"))); return
        for p in [img] + ([ps] if ps else []):
            if not os.path.isfile(p):
                q.put("Introuvable / not found: %s\n" % p); return
        if cib != CIBLE_DEFAUT and not annonce(cib, ps, journal=lambda m: q.put(m + "\n"), demande=_boite_confirmation,
                                               jeux=jeux):
            q.put("\n%s\n" % ("ANNULÉ" if lg == "fr" else "CANCELLED")); return
        bouton.configure(state="disabled")
        for c in cases.values():
            c.configure(state="disabled")
        plan["texte"] = ""; barre.configure(maximum=1, value=0)
        v_etat.set("Préparation / preparing…")
        etat["en_cours"] = True; etat["t0"] = time.monotonic(); tic()

        def travail():
            sys.stdout = sys.stderr = Flux()
            r, sortie = 1, v_out.get().strip()
            message = None
            try:
                r = construit(img, sortie, ps, journal=lambda m: q.put(m + "\n"), cible=cib, confirme=True,
                              avancement=lambda e, **i: q.put((e, i)), jeux=jeux)
                message = message_fin(r, sortie, ps, jeux)
            except BaseException as x:          # noqa : SystemExit de hsfa_build compris
                q.put("\nERREUR / ERROR: %s\n" % x)
                message = "ERREUR / ERROR: %s\n\n%s" % (x, message_fin(1, sortie, ps, jeux))
            finally:   # son, premier plan et boite par pompe() : aucun widget touche depuis ce fil
                q.put(("fin", {"ok": r == 0, "message": message}))
        threading.Thread(target=travail, daemon=True).start()

    bouton = tk.Button(f, text="Construire / Build", command=lance); bouton.grid(row=7, column=1, pady=6)
    rafraichit()
    pompe(); racine.mainloop()
    return 0


def auto_test():
    """controle de l'executable sans donnee de jeu (CI) : numpy, libchdr, hsfa_oggenc (signal d'essai), fluxtool,
    hsfa_rejeu_iso (programme Z80 d'essai)"""
    import subprocess
    _outils_natifs(); ok = True
    def rapport(nom, res, err=None):
        nonlocal ok
        ok &= res; print("%-12s %s%s" % (nom, "OK" if res else "ECHEC", (" : %s" % err) if err else ""))
    try:
        import numpy; rapport("numpy", True, numpy.__version__)
    except Exception as x: rapport("numpy", False, x)
    for m in ("PIL.Image", "capstone"):                  # etapes d'Upper MAX
        try:
            __import__(m); rapport(m, True)
        except Exception as x: rapport(m, False, x)
    try:
        import chd_iso; chd_iso.charge_libchdr(); rapport("libchdr", True)
    except Exception as x: rapport("libchdr", False, x)
    try:
        sys.path.insert(0, os.path.join(DEPOT, "tools", "flux", "oggenc"))
        import construit_oggenc
        m = construit_oggenc.verifie(os.environ["HSFA_OGGENC"]); rapport("hsfa_oggenc", m is not None, m)
    except Exception as x: rapport("hsfa_oggenc", False, x)
    try:
        r = subprocess.run([os.environ["HSFA_FLUXTOOL"]], capture_output=True, text=True)
        rapport("fluxtool", "usage" in (r.stdout + r.stderr).lower(), (r.stdout + r.stderr).strip().splitlines()[:1])
    except Exception as x: rapport("fluxtool", False, x)
    try:
        sys.path.insert(0, os.path.join(DEPOT, "tools", "son-hyper", "rejeu_iso"))
        import gen_rejeu_iso, tempfile
        with tempfile.TemporaryDirectory() as t: m = gen_rejeu_iso.essai_synthetique(os.environ["HSFA_REJEU_ISO"], t)
        rapport("hsfa_rejeu_iso", m == gen_rejeu_iso.ESSAI_MD5, m)
    except Exception as x: rapport("hsfa_rejeu_iso", False, x)
    try:
        H = _hsfa_build(); rapport("hsfa_build", hasattr(H, "main"))
    except Exception as x: rapport("hsfa_build", False, x)
    try:     # plan de Hyper + Arcade (code fige et releves de la greffe embarques) ; ce qu'il entraine : test_selection.py
        s = selection(["hyperarcade"])
        rapport("plan", "hyperarcade" in s["archives"], "hyperarcade -> %s" % ",".join(zip_de(a) for a in s["archives"]))
    except Exception as x: rapport("plan", False, x)
    return 0 if ok else 1


def main(argv):
    if _role_python(argv):
        return 0
    if argv[1:] == ["--auto-test"]:
        return auto_test()
    import argparse
    ap = argparse.ArgumentParser(description="HSFA builder / constructeur HSFA %s" % VERSION)
    ap.add_argument("image", nargs="?", help=".iso ou .chd de Street Fighter Alpha Anthology (PS2, USA, SLUS-21317)")
    ap.add_argument("--psp", "--psp-iso", dest="psp",
                    help="ISO ou .chd PSP de SFA3 MAX (USA ULUS-10062 ou Europe ULES-00235), facultatif : Upper MAX en plus")
    ap.add_argument("--sortie", "--output", dest="sortie")
    ap.add_argument("--console", action="store_true", help="sans fenêtre / no window")
    ap.add_argument("--cible", choices=("fbneo-hsfa", "fbneo-autonome", "mister", "cps2-banques"), default=None,
                    help="format de sortie / output format (défaut / default : fbneo-hsfa)")
    ap.add_argument("--oui", "--yes", dest="oui", action="store_true",
                    help="(--cible autre que fbneo-hsfa) confirmer sans question / confirm without asking")
    ap.add_argument("--jeux", "--games", dest="jeux",
                    help="jeux à construire / games to build: %s (défaut / default : sfa3,upper,hyper, + uppermax avec "
                         "/ with --psp ; hyperarcade = Hyper + Arcade, expérimental, construit aussi Upper et Hyper / "
                         "experimental, also builds Upper and Hyper)" % ",".join(JEUX_CHOIX))
    ap.add_argument("--version", action="version", version="hsfa-constructeur %s" % VERSION)
    args, extra = argv[1:], []
    if "--" in args:
        k = args.index("--"); args, extra = args[:k], args[k + 1:]
    a = ap.parse_args(args)
    graphique = not a.console and (os.name == "nt" or sys.platform == "darwin" or os.environ.get("DISPLAY")
                                   or os.environ.get("WAYLAND_DISPLAY"))
    jeux = None
    if a.jeux is not None:                     # fenetre : l'ISO PSP peut encore y etre choisie (Upper MAX grise sinon)
        try:
            jeux = verifie_jeux(a.jeux, a.psp if (a.image or not graphique) else True)
        except ValueError as x:
            ap.error(str(x))
    if a.image or not graphique:
        return console(a.image, a.sortie, a.psp, extra, questions=not a.image,
                       cible=a.cible or (CIBLE_DEFAUT if a.image else None), oui=a.oui, jeux=jeux)
    try:
        return fenetre(a.image, a.sortie, a.psp, a.cible, jeux)
    except Exception:                                     # pas de Tk / pas d'ecran : questions en texte
        return console(None, a.sortie, a.psp, extra, cible=a.cible, oui=a.oui, jeux=jeux)


if __name__ == "__main__":
    if GELE:
        import multiprocessing; multiprocessing.freeze_support()
    r = main(sys.argv) or 0
    if GELE and _garder_console_ouverte(ARGV_ORIGINE, ROLE_PYTHON) and sys.stdin and sys.stdin.isatty():
        try: input("Entrée pour fermer / press Enter to close")   # image glissee sur l'exe : garder la console ouverte
        except (EOFError, OSError): pass
    sys.exit(r)
