#!/usr/bin/env python3
"""HSFA builder: one executable that turns YOUR disc images into the HSFA game archives.
Constructeur HSFA : un seul executable, de VOS images de disque aux archives des jeux HSFA.

  hsfa-constructeur                          window (or text prompts without a display) / fenetre (ou questions)
  hsfa-constructeur IMAGE [--psp ISO_PSP] [--sortie DIR]
      IMAGE   : Street Fighter Alpha Anthology (PS2, USA, SLUS-21317), .iso or .chd
      ISO_PSP : optional / facultatif : Street Fighter Alpha 3 MAX (PSP, Europe, ULES-00235), .iso or .chd
                -> also builds Upper MAX (sfa3umhsfa.zip) / construit aussi Upper MAX
      Windows : drag the PS2 image onto the executable / glisser l'image PS2 sur l'executable
  options : --console ; anything after « -- » goes to hsfa_build.py as is / le reste apres « -- » va a hsfa_build.py

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


def _role_python(argv):
    """True si l'executable est lance comme interpreteur Python (etape de hsfa_build, test de numpy, sous-script)"""
    a = argv[1:]
    while a and a[0] in ("-u", "-B", "-E", "-s", "-S", "-I"): a = a[1:]     # options sans effet ici
    if not a: return False
    if a[0] in ("-c", "-m"):
        sys.path.insert(0, "")                                         # comme python -c / -m : dossier courant
    if a[0] == "-c" and len(a) >= 2:
        _outils_natifs()
        sys.argv = ["-c"] + a[2:]
        exec(compile(a[1], "<-c>", "exec"), {"__name__": "__main__"})
        return True
    if a[0] == "-m" and len(a) >= 2:
        sys.argv = [a[1]] + a[2:]
        runpy.run_module(a[1], run_name="__main__", alter_sys=True)
        return True
    if a[0].endswith(".py") and os.path.isfile(a[0]):
        _outils_natifs()
        sys.argv = a
        sys.path.insert(0, os.path.dirname(os.path.abspath(a[0])))      # comme « python script.py »
        runpy.run_path(a[0], run_name="__main__")
        return True
    return False


def _hsfa_build():
    sys.path.insert(0, os.path.join(DEPOT, "scripts", "construction"))
    import hsfa_build
    return hsfa_build


def _image_vers_iso(image, sortie, psp=False, journal=print):
    """.chd -> .iso <sortie>/cache/iso_chd[_psp]/<nom>.iso (meme nom de base : hsfa_info.txt identique a une
    construction depuis l'ISO du meme nom) ; PS2 : ISO creuse (fichiers utiles) ; PSP : image complete (250 Mo)"""
    if not image.lower().endswith(".chd"):
        return image
    import chd_iso
    nom = os.path.splitext(os.path.basename(image))[0] + ".iso"
    d = os.path.join(sortie, "cache", "iso_chd_psp" if psp else "iso_chd"); os.makedirs(d, exist_ok=True)
    iso = os.path.join(d, nom)
    marque = iso + ".source"
    sig = "%s %d %d\n" % (os.path.abspath(image), os.path.getsize(image), int(os.path.getmtime(image)))
    if os.path.exists(iso) and os.path.exists(marque) and open(marque).read() == sig:
        journal("CHD deja decompresse / CHD already unpacked: %s" % iso); return iso
    journal("CHD -> ISO%s: %s" % ("" if psp else " (fichiers utiles seulement / needed files only)", iso))
    vu = set()
    def progres(n, t):                       # une ligne tous les 10 %
        p = 100 * n // t // 10 * 10
        if p not in vu: vu.add(p); journal("  %d %%" % p)
    chd_iso.vers_iso(image, iso, tout=psp, progres=progres)
    open(marque, "w").write(sig)
    return iso


def construit(image, sortie, psp=None, extra=(), journal=print):
    """construction complete ; rend le code de sortie de hsfa_build"""
    _outils_natifs()
    H = _hsfa_build()
    sortie = os.path.abspath(sortie); os.makedirs(sortie, exist_ok=True)
    iso = _image_vers_iso(os.path.abspath(image), sortie, False, journal)
    jeux = "sfa3,upper,hyper" + (",uppermax" if psp else "")
    argv = ["hsfa_build.py", "--anthology", iso, "--sortie", sortie, "--jeux", jeux, "--flux-format", "ogg"]
    if psp: argv += ["--psp-iso", _image_vers_iso(os.path.abspath(psp), sortie, True, journal)]
    sys.argv = argv + list(extra)
    r = H.main()
    if r == 0:
        A = os.path.join(sortie, "archives")
        journal("")
        journal("Termine / Done. Archives : %s" % A)
        for f in sorted(os.listdir(A)):
            if f.endswith(".zip"): journal("  " + f)
        journal("Copiez-les dans le dossier des ROM de FinalBurn Neo HSFA / copy them to your FBNeo HSFA ROM folder.")
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


def console(image=None, sortie=None, psp=None, extra=(), questions=True):
    print("Constructeur HSFA %s / HSFA builder" % VERSION)
    if not image:
        image = _demande("Image PS2 de l'Anthology (.iso ou .chd ; glissez le fichier ici) / PS2 disc image: ")
        if questions and psp is None:
            psp = _demande("ISO PSP de SFA3 MAX (Europe), facultatif : Entree pour passer / optional PSP ISO, "
                           "Enter to skip: ") or None
    if not os.path.isfile(image):
        print("Introuvable / not found: %s" % image); return 1
    if psp and not os.path.isfile(psp):
        print("Introuvable / not found: %s" % psp); return 1
    return construit(image, sortie or sortie_defaut(), psp, extra)


def fenetre(image=None, sortie=None, psp=None):
    import queue, tkinter as tk
    from tkinter import filedialog, scrolledtext
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
    log = scrolledtext.ScrolledText(f, width=100, height=24, state="disabled")
    log.grid(row=5, column=0, columnspan=3, pady=6)
    f.columnconfigure(1, weight=1)
    q = queue.Queue()

    class Flux:
        def write(self, s): q.put(s)
        def flush(self): pass

    def pompe():
        try:
            while True:
                s = q.get_nowait(); log.configure(state="normal"); log.insert("end", s); log.see("end")
                log.configure(state="disabled")
        except queue.Empty:
            pass
        racine.after(200, pompe)

    def lance():
        img, ps = v_img.get().strip(), v_psp.get().strip() or None
        for p in [img] + ([ps] if ps else []):
            if not os.path.isfile(p):
                q.put("Introuvable / not found: %s\n" % p); return
        bouton.configure(state="disabled")

        def travail():
            sys.stdout = sys.stderr = Flux()
            try:
                r = construit(img, v_out.get().strip(), ps, journal=lambda m: q.put(m + "\n"))
                q.put("\n%s\n" % ("OK" if r == 0 else "ECHEC / FAILED (journal.txt)"))
            except BaseException as x:          # noqa : SystemExit de hsfa_build compris
                q.put("\nERREUR / ERROR: %s\n" % x)
            finally:
                racine.after(0, lambda: bouton.configure(state="normal"))
        threading.Thread(target=travail, daemon=True).start()

    bouton = tk.Button(f, text="Construire / Build", command=lance); bouton.grid(row=4, column=1, pady=6)
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
                    help="ISO ou .chd PSP de SFA3 MAX (Europe, ULES-00235), facultatif : Upper MAX en plus")
    ap.add_argument("--sortie", "--output", dest="sortie")
    ap.add_argument("--console", action="store_true", help="sans fenetre / no window")
    ap.add_argument("--version", action="version", version="hsfa-constructeur %s" % VERSION)
    args, extra = argv[1:], []
    if "--" in args:
        k = args.index("--"); args, extra = args[:k], args[k + 1:]
    a = ap.parse_args(args)
    graphique = not a.console and (os.name == "nt" or sys.platform == "darwin" or os.environ.get("DISPLAY")
                                   or os.environ.get("WAYLAND_DISPLAY"))
    if a.image or not graphique:
        return console(a.image, a.sortie, a.psp, extra, questions=not a.image)
    try:
        return fenetre(a.image, a.sortie, a.psp)
    except Exception:                                     # pas de Tk / pas d'ecran : questions en texte
        return console(None, a.sortie, a.psp, extra)


if __name__ == "__main__":
    if GELE:
        import multiprocessing; multiprocessing.freeze_support()
    r = main(sys.argv) or 0
    if GELE and os.name == "nt" and len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
        input("Entree pour fermer / press Enter to close")   # image glissee sur l'exe : garder la console ouverte
    sys.exit(r)
