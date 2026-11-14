#!/usr/bin/env python3
"""HSFA builder: one executable that turns YOUR disc images into the HSFA game archives.
Constructeur HSFA : un seul executable, de VOS images de disque aux archives des jeux HSFA.

  hsfa-constructeur                          window (or text prompts without a display) / fenetre (ou questions)
  hsfa-constructeur IMAGE [--psp ISO_PSP] [--sortie DIR]
      IMAGE   : Street Fighter Alpha Anthology (PS2, USA, SLUS-21317), .iso or .chd
      ISO_PSP : optional / facultatif : Street Fighter Alpha 3 MAX (PSP, USA ULUS-10062 or Europe ULES-00235), .iso or .chd
                -> also builds Upper MAX (sfa3umhsfa.zip) / construit aussi Upper MAX
      Windows : drag the PS2 image onto the executable / glisser l'image PS2 sur l'executable
  options : --console ; --cible fbneo-hsfa (default / defaut) | fbneo-autonome | mister | cps2-banques ; --oui / --yes ;
            anything after « -- » goes to hsfa_build.py as is / le reste apres « -- » va a hsfa_build.py
  fbneo-autonome (standalone FBNeo HSFA for Windows, test build): its concession is announced and confirmed, then the
  SAME archives as fbneo-hsfa are built / annonce et confirmation, puis les MEMES archives que fbneo-hsfa.
  mister, cps2-banques: not available yet; the builder announces their concessions per game and the measured budgets,
  asks for confirmation, and builds nothing (report mode) / pas encore disponibles : annonce des concessions par jeu et
  des budgets mesures, confirmation, rien n'est construit (bilan).
  Language of these announcements / langue des annonces : HSFA_LANGUE=fr|en, else the system's / sinon celle du systeme.

Embeds / embarque : Python, NumPy, the HSFA scripts (scripts/, src/, tools/, max/), hsfa_oggenc (portable Ogg Vorbis
encoder, tools/flux/oggenc), fluxtool (tools/flux) and libchdr. No game data / aucune donnee de jeu. Licences: TIERS.md.

The same executable also plays the « python » that the build starts for each step / sert aussi d'interpreteur :
  <exe> SCRIPT.py ARGS...     <exe> -c CODE     <exe> -m MODULE ARGS...
"""
import os, runpy, sys, threading

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
    for var, nom in (("HSFA_FLUXTOOL", "fluxtool" + X), ("HSFA_OGGENC", "hsfa_oggenc" + X)):
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


def jeux_construits(psp=None):
    return ["sfa3", "upper", "hyper"] + (["uppermax"] if psp else [])


def produit(cible):
    """True si le format produit des archives (fbneo-hsfa, fbneo-autonome en essai) ; False : bilan seulement"""
    return cible == CIBLE_DEFAUT or _cibles().CIBLES[cible]["dispo"]


def annonce(cible, psp=None, journal=print, demande=None, oui=False):
    """format autre que fbneo-hsfa : annonce (concessions, budgets) puis confirmation ; True = confirme.
    demande(cible, langue) -> bool : question par la fenetre ; None : question dans le terminal"""
    K = _cibles(); lg = K.langue_defaut()
    jeux = jeux_construits(psp)
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


def bilan(cible, psp=None, journal=print, demande=None, oui=False):
    """format qui ne produit rien (mister, cps2-banques) : annonce, confirmation, AUCUNE sortie ; rend 0 / 2"""
    if not annonce(cible, psp, journal, demande, oui):
        return 2
    lg = _cibles().langue_defaut()
    journal("Mode bilan : format pas encore disponible ; aucune archive n'est produite." if lg == "fr" else
            "Report mode: format not available yet; no archive is produced.")
    return 0


def construit(image, sortie, psp=None, extra=(), journal=print, cible=CIBLE_DEFAUT, demande=None, oui=False,
              confirme=False, avancement=None):
    """construction complete ; rend le code de sortie de hsfa_build. Format qui ne produit rien : bilan seulement ;
    fbneo-autonome : annonce et confirmation (sauf confirme=True, deja faites), puis les memes archives que fbneo-hsfa.
    avancement(evenement, **infos) : duree estimee et etapes (hsfa_build.AVANCEMENT), appele depuis ce fil"""
    if not produit(cible):
        return bilan(cible, psp, journal, demande, oui)
    if cible != CIBLE_DEFAUT and not confirme and not annonce(cible, psp, journal, demande, oui):
        return 2
    _outils_natifs()
    H = _hsfa_build()
    H.AVANCEMENT = avancement
    try:
        return _construit(H, image, sortie, psp, extra, journal, cible)
    finally:
        H.AVANCEMENT = None


ZIPS = {"sfa3": "sfa3hsfa", "upper": "sfa3uhsfa", "hyper": "sfa3hhsfa", "uppermax": "sfa3umhsfa"}


def zips_construits(sortie, psp=None):
    """archives des jeux presentes a la racine de la sortie (v0.1.11 : plus de sous-dossier archives/)"""
    return [ZIPS[j] + ".zip" for j in jeux_construits(psp) if os.path.isfile(os.path.join(sortie, ZIPS[j] + ".zip"))]


def message_fin(r, sortie, psp=None):
    """message de fin (console, journal et boite de la fenetre) : « Terminé : N jeux dans … » ou l'echec"""
    sortie = os.path.abspath(sortie)
    if r == 0:
        n = len(zips_construits(sortie, psp))
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


def _construit(H, image, sortie, psp, extra, journal, cible):
    sortie = os.path.abspath(sortie); os.makedirs(sortie, exist_ok=True)
    image = os.path.abspath(image); psp = psp and os.path.abspath(psp)
    T = H.dossier_travail(sortie)              # hsfa-travail/ (une sortie de l'ancienne forme y est rangee d'abord)
    jeux = "sfa3,upper,hyper" + (",uppermax" if psp else "")
    argv = ["--anthology", _iso_de(image, T), "--sortie", sortie, "--jeux", jeux, "--flux-format", "ogg"]
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
    argv[1] = _image_vers_iso(image, T, False, journal)
    if psp: _image_vers_iso(psp, T, True, journal)
    sys.argv = ["hsfa_build.py"] + argv
    r = H.main()
    journal("")
    journal(message_fin(r, sortie, psp))
    if r == 0:
        for f in zips_construits(sortie, psp):
            journal("  " + f)
        journal("Copiez-les dans le dossier des ROM de FinalBurn Neo HSFA / copy them to your FBNeo HSFA ROM folder.")
        journal("(fichiers de travail / work files: %s)" % T)
        if cible == "fbneo-autonome":
            journal("FinalBurn Neo HSFA autonome : fbneo64.exe (4:3) ou fbneo64ws.exe (16:9) / standalone: fbneo64.exe "
                    "(4:3) or fbneo64ws.exe (16:9).")
    return r


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


def console(image=None, sortie=None, psp=None, extra=(), questions=True, cible=None, oui=False):
    print("Constructeur HSFA %s / HSFA builder" % VERSION)
    if cible is None:
        cible = _choix_cible() if questions else CIBLE_DEFAUT
    if not produit(cible):
        if questions and psp is None and sys.stdin and sys.stdin.isatty():
            psp = _demande("Upper MAX aussi (ISO PSP) ? o/N / Upper MAX too? y/N : ").lower() in ("o", "y") or None
        return bilan(cible, psp, oui=oui)
    confirme = False
    if cible != CIBLE_DEFAUT and not image:              # annonce avant les questions sur les images
        if not annonce(cible, psp, oui=oui):
            return 2
        confirme = True
    if not image:
        image = _demande("Image PS2 de l'Anthology (.iso ou .chd ; glissez le fichier ici) / PS2 disc image: ")
        if questions and psp is None:
            psp = _demande("ISO PSP de SFA3 MAX (USA ou Europe), facultatif : Entrée pour passer / optional PSP ISO, "
                           "Enter to skip: ") or None
    if not os.path.isfile(image):
        print("Introuvable / not found: %s" % image); return 1
    if psp and not os.path.isfile(psp):
        print("Introuvable / not found: %s" % psp); return 1
    r = construit(image, sortie or sortie_defaut(), psp, extra, cible=cible, oui=oui, confirme=confirme)
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


def fenetre(image=None, sortie=None, psp=None, cible=None):
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
    tk.Label(f, text="Avec l'ISO PSP : Upper MAX en plus / with the PSP ISO: Upper MAX too",
             fg="grey").grid(row=3, column=1, sticky="w")
    K = _cibles()
    lg = K.langue_defaut()
    libelles = {K.libelle(n, lg): n for n in K.CIBLES}
    v_cib = tk.StringVar(value=[l for l, n in libelles.items() if n == (cible or CIBLE_DEFAUT)][0])
    tk.Label(f, text="Format de sortie / output", anchor="w").grid(row=4, column=0, sticky="w")
    tk.OptionMenu(f, v_cib, *libelles).grid(row=4, column=1, sticky="w")
    # avancement : etape n / N et temps restant (hsfa_build.AVANCEMENT, recu par la file comme le journal)
    v_etat = tk.StringVar(value="")
    barre = ttk.Progressbar(f, orient="horizontal", mode="determinate", maximum=1, value=0)
    barre.grid(row=6, column=0, columnspan=3, sticky="we", pady=(6, 0))
    tk.Label(f, textvariable=v_etat, anchor="w", justify="left", wraplength=760).grid(row=7, column=0, columnspan=3, sticky="we")
    log = scrolledtext.ScrolledText(f, width=100, height=24, state="disabled")
    log.grid(row=8, column=0, columnspan=3, pady=6)
    f.columnconfigure(1, weight=1)
    q = queue.Queue()

    class Flux:
        def write(self, s): q.put(s)
        def flush(self): pass

    plan = {"texte": ""}

    def avance(evenement, infos):                 # fil principal seulement (appele par pompe)
        if evenement == "plan":
            plan["texte"] = texte_avancement("plan", infos)
            barre.configure(maximum=max(infos["N"], 1), value=0)
            v_etat.set(plan["texte"] if infos["N"] else plan["texte"] + "\n" + "Rien à refaire / nothing to redo")
        elif evenement == "etape":
            barre.configure(maximum=max(infos["N"], 1), value=infos["n"] - (0 if infos["fait"] else 1))
            v_etat.set(plan["texte"] + "\n" + texte_avancement("etape", infos))
        elif evenement == "fin":
            if infos["ok"]: barre.configure(value=barre.cget("maximum"))
            v_etat.set(plan["texte"] + "\n" + ("Terminé / done" if infos["ok"] else "ÉCHEC / FAILED"))
            bouton.configure(state="normal")
            fin_visible(infos["ok"], infos.get("message") or ("OK" if infos["ok"] else "ÉCHEC / FAILED"))

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
        img, ps = v_img.get().strip(), v_psp.get().strip() or None
        cib = libelles[v_cib.get()]
        if not produit(cib):                             # bilan : ni image ni sortie necessaires
            r = bilan(cib, ps, journal=lambda m: q.put(m + "\n"), demande=_boite_confirmation)
            q.put("\n%s\n" % (("BILAN" if lg == "fr" else "REPORT") if r == 0 else
                               ("ANNULÉ" if lg == "fr" else "CANCELLED"))); return
        for p in [img] + ([ps] if ps else []):
            if not os.path.isfile(p):
                q.put("Introuvable / not found: %s\n" % p); return
        if cib != CIBLE_DEFAUT and not annonce(cib, ps, journal=lambda m: q.put(m + "\n"), demande=_boite_confirmation):
            q.put("\n%s\n" % ("ANNULÉ" if lg == "fr" else "CANCELLED")); return
        bouton.configure(state="disabled")
        plan["texte"] = ""; barre.configure(maximum=1, value=0)
        v_etat.set("Préparation / preparing…")

        def travail():
            sys.stdout = sys.stderr = Flux()
            r, sortie = 1, v_out.get().strip()
            message = None
            try:
                r = construit(img, sortie, ps, journal=lambda m: q.put(m + "\n"), cible=cib, confirme=True,
                              avancement=lambda e, **i: q.put((e, i)))
                message = message_fin(r, sortie, ps)
            except BaseException as x:          # noqa : SystemExit de hsfa_build compris
                q.put("\nERREUR / ERROR: %s\n" % x)
                message = "ERREUR / ERROR: %s\n\n%s" % (x, message_fin(1, sortie, ps))
            finally:   # son, premier plan et boite par pompe() : aucun widget touche depuis ce fil
                q.put(("fin", {"ok": r == 0, "message": message}))
        threading.Thread(target=travail, daemon=True).start()

    bouton = tk.Button(f, text="Construire / Build", command=lance); bouton.grid(row=5, column=1, pady=6)
    pompe(); racine.mainloop()
    return 0


def auto_test():
    """controle de l'executable sans donnee de jeu (CI) : numpy, libchdr, hsfa_oggenc (signal d'essai), fluxtool"""
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
        H = _hsfa_build(); rapport("hsfa_build", hasattr(H, "main"))
    except Exception as x: rapport("hsfa_build", False, x)
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
    ap.add_argument("--version", action="version", version="hsfa-constructeur %s" % VERSION)
    args, extra = argv[1:], []
    if "--" in args:
        k = args.index("--"); args, extra = args[:k], args[k + 1:]
    a = ap.parse_args(args)
    graphique = not a.console and (os.name == "nt" or sys.platform == "darwin" or os.environ.get("DISPLAY")
                                   or os.environ.get("WAYLAND_DISPLAY"))
    if a.image or not graphique:
        return console(a.image, a.sortie, a.psp, extra, questions=not a.image,
                       cible=a.cible or (CIBLE_DEFAUT if a.image else None), oui=a.oui)
    try:
        return fenetre(a.image, a.sortie, a.psp, a.cible)
    except Exception:                                     # pas de Tk / pas d'ecran : questions en texte
        return console(None, a.sortie, a.psp, extra, cible=a.cible, oui=a.oui)


if __name__ == "__main__":
    if GELE:
        import multiprocessing; multiprocessing.freeze_support()
    r = main(sys.argv) or 0
    if GELE and _garder_console_ouverte(ARGV_ORIGINE, ROLE_PYTHON) and sys.stdin and sys.stdin.isatty():
        try: input("Entrée pour fermer / press Enter to close")   # image glissee sur l'exe : garder la console ouverte
        except (EOFError, OSError): pass
    sys.exit(r)
