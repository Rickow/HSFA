#!/usr/bin/env python3
"""test_windows.py -- essais de la construction sous Windows (CI : windows-latest ; Linux en temoin), SANS donnee de jeu :
tous les fichiers sont fabriques ici (dossiers temporaires, signal synthetique en entiers).

  test_windows.py [--parties P,P...] [--natifs BIN] [--exe EXE] [--non-admin] [--rapport FICHIER]
  parties : liens maison fige encodage git flux (defaut) ; exe, interprete (avec --exe : l'executable PyInstaller) ;
            etape (seulement DANS l'executable : une etape lancee comme hsfa_build le fait)
  --non-admin : relance « liens » avec un jeton SANS droit d'administrateur ni privilege (comme un compte limite, ou un
                administrateur sous UAC sans elevation) ; l'enfant verifie qu'os.symlink y echoue (WinError 1314)
  --exige-sans-droit : (enfant) echec si le processus est administrateur ou peut creer un lien symbolique

Points couverts (src/hsfa/liens.py, ticket #2 et PIEGES_WINDOWS) :
  liens     jonction NTFS d'un dossier (lecture, ecriture a travers), copie d'un fichier + .hsfa_liens, liens.reel(),
            « unlink puis ecrit » sans toucher la source, copie perimee refaite, mklink /J, rmtree / os.walk et jonction,
            paquet_fbneo.lit() (CRLF -> LF, chemin en « / » dans le journal de hsfa_info.txt)
  maison    os.path.expanduser lit USERPROFILE (Windows) / HOME
  fige      fige.py / fige35.py : chemin « C:\\Users\\...\\t...\\a... » dans du code genere, importe sans SyntaxError
  encodage  texte accentue avec et sans PYTHONUTF8 ; fins de ligne du mode texte
  git       copie Git du runner : core.autocrlf, git ls-files --eol, aucune table .txt / .tsv en CRLF ; temoin sans
            .gitattributes
  coeur     ydata.txt (chemin de l'ISO relu par fopen dans le coeur) : hsfa_build.chemin_pour_coeur ; fluxtool et
            chemins accentues (dans / hors de la page de code ANSI)
  umprog    etape d'Upper MAX lancee avec l'environnement filtre d'um_prog.py (ni USERPROFILE, ni TEMP, ni _PYI_*)
  flux      hsfa_oggenc / fluxtool : ADX synthetique -> PCM -> Ogg (flux_ogg.encode, chaine de la construction) ->
            PCM ; empreintes = celles de Linux (REF_FLUX)
  exe       hsfa-constructeur --auto-test ; PYTHONUTF8 honore ; l'exe comme « python » (-c, script .py)
  interprete l'exe comme « python » des etapes, reponses comparees au vrai python : PYTHONPATH, dossier courant, -I, -B,
            PYTHONDONTWRITEBYTECODE, codes de sortie, script a un argument stdin ouvert (attente d'Entree de la v0.1.10)
"""
import argparse, hashlib, os, shutil, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
WIN = os.name == "nt"
TEXTE_ACCENTUE = "Kikōken → Chun-Li, « é à ç » ✓"      # « ō », « → », « ✓ » : absents de cp1252
# empreintes Linux (natifs zig linux-x86_64, Python 3.14, 11/11/2026) du signal synthetique de flux() ; le temoin Linux
# de la CI doit les retrouver aussi
REF_FLUX = {
    "adx": "df1e82441dbb38e6aad9e7f1fa20da70",
    "pcm_adx": "b1e72b30299c64300aac9cec28f262b0",
    "ogg": "116cdb94e6e0e1b5c47558dd34e2840b",
    "pcm_ogg": "66d22f1075eea358667efd355799c181",
    "boucle_ogg": "48000 120000",
}

resultats = []


def note(etat, nom, detail=""):
    resultats.append((etat, nom, str(detail)))
    print("%-5s %s%s" % (etat, nom, (" : %s" % detail) if detail != "" else ""), flush=True)


def verifie(nom, condition, detail=""):
    note("OK" if condition else "ECHEC", nom, detail)
    return condition


def protege(nom):
    """decorateur : une exception dans une partie = un ECHEC note, les autres parties continuent"""
    def d(f):
        def g(*a, **k):
            try:
                return f(*a, **k)
            except Exception as x:   # noqa
                import traceback
                note("ECHEC", nom + "/exception", "%s: %s" % (type(x).__name__, x))
                traceback.print_exc()
        return g
    return d


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def depot():
    return os.environ.get("HSFA_DEPOT_ESSAI") or os.path.normpath(os.path.join(ICI, "..", ".."))


def est_admin():
    if not WIN:
        return os.geteuid() == 0
    import ctypes
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def mode_developpeur():
    if not WIN:
        return None
    import winreg
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock")
        return winreg.QueryValueEx(k, "AllowDevelopmentWithoutDevLicense")[0]
    except OSError:
        return "absent"


def symlink_possible(t):
    a, b = os.path.join(t, "_sl_cible"), os.path.join(t, "_sl_lien")
    open(a, "w").close()
    try:
        os.symlink(a, b)
        os.remove(b)
        return True, ""
    except OSError as x:
        return False, "WinError %s" % getattr(x, "winerror", None) if WIN else str(x)
    finally:
        os.remove(a)


# ----------------------------------------------------------------------------------------------------------------------
@protege("liens")
def liens_(exige_sans_droit=False):
    sys.path.insert(0, os.path.join(depot(), "src", "hsfa"))
    import liens
    T = tempfile.mkdtemp(prefix="hsfa_liens_")
    try:
        _liens(liens, T, exige_sans_droit)
    finally:
        shutil.rmtree(T, ignore_errors=True)


def _liens(liens, T, exige_sans_droit):
    admin = est_admin(); sl, pourquoi = symlink_possible(T)
    note("INFO", "liens/contexte", "admin=%s, lien symbolique possible=%s %s, mode developpeur=%s, HSFA_SANS_LIENS=%r, "
         "Python %s, TEMP=%s" % (admin, sl, pourquoi, mode_developpeur(), os.environ.get("HSFA_SANS_LIENS", ""),
                                 sys.version.split()[0], T))
    if exige_sans_droit:
        verifie("liens/sans_droit/pas_admin", not admin)
        if WIN:
            r = subprocess.run(["whoami", "/groups", "/priv"], capture_output=True, text=True)
            note("INFO", "liens/sans_droit/whoami", " | ".join(l.strip()[:90] for l in r.stdout.splitlines()
                                                              if any(m in l for m in ("Admin", "S-1-16", "Se"))))
        verifie("liens/sans_droit/symlink_refuse", not sl and (not WIN or "1314" in pourquoi), pourquoi)
    sans = WIN and (not sl or liens._mode())
    attendu_d = "jonction" if sans else ("jonction" if liens._mode() else "symbolique")
    attendu_f = "copie" if (sans or liens._mode()) else "symbolique"

    # dossier : chemin avec espace et accents (dossier personnel « C:\Users\Rémi Ø »)
    S = os.path.join(T, "Source dossier é ø"); os.makedirs(S)
    open(os.path.join(S, "a.txt"), "wb").write(b"contenu\n")
    L = os.path.join(T, "home", ".cache", "sfa3max"); os.makedirs(os.path.dirname(L))
    p = liens.lien(S, L)
    verifie("liens/dossier/procede", p == attendu_d, "%s (attendu %s)" % (p, attendu_d))
    if p == "jonction" and WIN:
        verifie("liens/dossier/est_jonction", liens.est_jonction(L) and not os.path.islink(L),
                "isjunction=%s islink=%s" % (liens.est_jonction(L), os.path.islink(L)))
    verifie("liens/dossier/lecture", open(os.path.join(L, "a.txt"), "rb").read() == b"contenu\n")
    open(os.path.join(L, "b.bin"), "wb").write(b"\x00\x01ecrit a travers")
    verifie("liens/dossier/ecriture_visible_dans_source",
            open(os.path.join(S, "b.bin"), "rb").read() == b"\x00\x01ecrit a travers")
    os.makedirs(os.path.join(L, "sous", "dossier")); open(os.path.join(S, "sous", "dossier", "c"), "w").write("x")
    verifie("liens/dossier/sous_dossier", os.path.isfile(os.path.join(L, "sous", "dossier", "c")))
    verifie("liens/dossier/realpath", os.path.normcase(os.path.realpath(L)) == os.path.normcase(os.path.realpath(S)),
            os.path.realpath(L))
    verifie("liens/dossier/lien_si_absent_rien", liens.lien_si_absent(S, L) is None)
    # lien qui designe un autre endroit (dossier de sortie deplace / range en hsfa-travail, v0.1.11) : refait
    S2 = os.path.join(T, "Source deplacee"); os.makedirs(S2); open(os.path.join(S2, "a.txt"), "wb").write(b"neuf\n")
    L2 = os.path.join(T, "lien_perime"); liens.lien(S, L2)
    r = liens.lien_si_absent(S2, L2)
    verifie("liens/dossier/lien_perime_refait", r is not None and open(os.path.join(L2, "a.txt"), "rb").read() == b"neuf\n"
            and os.path.isfile(os.path.join(S, "a.txt")), "%s ; source d'origine intacte : %s" % (r, os.path.isfile(os.path.join(S, "a.txt"))))
    # cible relative (relative au dossier du lien, comme os.symlink)
    os.makedirs(os.path.join(T, "r")); p2 = liens.lien(os.path.join("..", "Source dossier é ø"), os.path.join(T, "r", "rel"))
    verifie("liens/dossier/cible_relative", os.path.isfile(os.path.join(T, "r", "rel", "a.txt")), p2)
    try:
        liens.lien(S, L); verifie("liens/dossier/existe_deja", False, "pas d'erreur")
    except FileExistsError:
        verifie("liens/dossier/existe_deja", True)
    # boucle ~/.cache/sfa3max -> R (regen_max) : jonction vers un parent
    R = os.path.join(T, "R"); os.makedirs(os.path.join(R, "home", ".cache"))
    pb = liens.lien(R, os.path.join(R, "home", ".cache", "sfa3max"))
    verifie("liens/dossier/boucle_vers_parent", os.path.isdir(os.path.join(R, "home", ".cache", "sfa3max", "home")), pb)
    # mklink /J (si _winapi.CreateJunction manque)
    if WIN and p == "jonction":
        import _winapi
        vrai = getattr(_winapi, "CreateJunction", None)
        def refus(*a): raise AttributeError("essai : pas de CreateJunction")
        _winapi.CreateJunction = refus
        try:
            liens._jonction(S, os.path.join(T, "par_mklink"))
            verifie("liens/dossier/mklink_J", liens.est_jonction(os.path.join(T, "par_mklink")) and
                    os.path.isfile(os.path.join(T, "par_mklink", "a.txt")))
        finally:
            if vrai: _winapi.CreateJunction = vrai
    # rmtree d'un dossier qui contient une jonction / un lien : la cible reste intacte
    C = os.path.join(T, "conteneur"); os.makedirs(C); liens.lien(S, os.path.join(C, "j"))
    n_walk = sum(len(fs) for _r, _d, fs in os.walk(C))
    note("INFO", "liens/dossier/os.walk_entre_dans_le_lien", "%s (%d fichiers vus sous le conteneur)" % (n_walk > 0, n_walk))
    shutil.rmtree(C)
    verifie("liens/dossier/rmtree_garde_la_cible", os.path.isfile(os.path.join(S, "a.txt")) and not os.path.exists(C))
    try:
        os.unlink(os.path.join(T, "r", "rel"))
    except OSError:
        os.rmdir(os.path.join(T, "r", "rel"))           # Windows : lien de dossier / jonction
    verifie("liens/dossier/suppression_du_lien_seul", os.path.isfile(os.path.join(S, "a.txt")))

    # fichier : copie + .hsfa_liens + reel()
    F = os.path.join(S, "f545.bin"); open(F, "wb").write(b"banque d'origine")
    D = os.path.join(T, "greffe"); os.makedirs(D); LF = os.path.join(D, "f545.bin")
    pf = liens.lien(F, LF)
    verifie("liens/fichier/procede", pf == attendu_f, "%s (attendu %s)" % (pf, attendu_f))
    verifie("liens/fichier/lecture", open(LF, "rb").read() == b"banque d'origine")
    if pf == "copie":
        reg = open(os.path.join(D, liens.REGISTRE), encoding="utf-8").read()
        verifie("liens/fichier/registre", reg.startswith("f545.bin\t" + F + "\t"), reg.strip())
    verifie("liens/fichier/reel", os.path.normcase(liens.reel(LF)) == os.path.normcase(os.path.realpath(F)), liens.reel(LF))
    verifie("liens/fichier/lien_si_absent_a_jour", liens.lien_si_absent(F, LF) is None)
    if pf == "copie":                                   # cible modifiee : copie perimee refaite
        open(F, "ab").write(b"+"); st = os.stat(F); os.utime(F, ns=(st.st_atime_ns, st.st_mtime_ns + 2 * 10 ** 9))
        r = liens.lien_si_absent(F, LF)
        verifie("liens/fichier/copie_perimee_refaite", r == "copie" and open(LF, "rb").read() == b"banque d'origine+", r)
    avant = open(F, "rb").read()
    # greffe3 : « si islink : unlink » puis ecrit
    if os.path.islink(LF): os.unlink(LF)
    open(LF, "wb").write(b"banque greffee")
    verifie("liens/fichier/unlink_puis_ecrit_source_intacte", open(F, "rb").read() == avant)
    verifie("liens/fichier/reel_apres_reecriture", os.path.normcase(liens.reel(LF)) == os.path.normcase(os.path.realpath(LF)),
            liens.reel(LF))
    erreur_attendue = attendu_f != "symbolique"       # un lien symbolique peut pendre ; une copie, non
    try:
        liens.lien(os.path.join(S, "absent.bin"), os.path.join(D, "x.bin"))
        verifie("liens/fichier/cible_absente", not erreur_attendue, "pas d'erreur")
    except FileNotFoundError:
        verifie("liens/fichier/cible_absente", erreur_attendue, "FileNotFoundError")

    # paquet_fbneo.lit : texte CRLF -> octets de Linux ; journal (hsfa_info.txt) : chemin de la source, en « / »
    W = os.path.join(T, "work"); os.makedirs(os.path.join(W, "src", "sous"))
    open(os.path.join(W, "src", "sous", "carte.txt"), "w").write("ligne 1\nligne 2\n")   # mode texte : CRLF sous Windows
    os.makedirs(os.path.join(W, "dst")); liens.lien(os.path.join(W, "src", "sous", "carte.txt"), os.path.join(W, "dst", "carte.txt"))
    for nom, w in (("realpath", os.path.realpath(W)), ("tel_quel", W)):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import paquet_fbneo as P; "
                "d = P.lit(sys.argv[2]); print(repr(d)); print(P.journal[-1].split('  ')[2])")
        r = subprocess.run([sys.executable, "-c", code, os.path.join(depot(), "tools", "fbneo-hsfa"),
                            os.path.join(w, "dst", "carte.txt")], capture_output=True, text=True,
                           env=dict(os.environ, HSFA_WORK=w, HSFA_OUTILS=os.path.join(depot(), "tools")))
        l = r.stdout.splitlines()
        ok = r.returncode == 0 and l[:1] == ["b'ligne 1\\nligne 2\\n'"] and l[1:2] == ["src/sous/carte.txt"]
        verifie("liens/paquet_fbneo.lit/" + nom, ok, (l + [r.stderr.strip()[-300:]]) if not ok else l[1])


# ----------------------------------------------------------------------------------------------------------------------
@protege("maison")
def maison():
    var = "USERPROFILE" if WIN else "HOME"
    T = tempfile.mkdtemp(prefix="hsfa_maison_")
    e = dict(os.environ, HOME=os.path.join(T, "home_HOME"), USERPROFILE=os.path.join(T, "home_USERPROFILE"))
    r = subprocess.run([sys.executable, "-c", "import os; print(os.path.expanduser('~/.cache/sfa3max'))"],
                       capture_output=True, text=True, env=e)
    att = os.path.join(e[var], ".cache/sfa3max") if not WIN else os.path.join(e[var], ".cache/sfa3max")
    verifie("maison/expanduser_lit_" + var, os.path.normpath(r.stdout.strip()) == os.path.normpath(att), r.stdout.strip())
    # les deux outils qui fixent le dossier personnel des etapes de MAX donnent les deux variables
    for f in ("tools/integration-max/upper_max/regen_max.py", "tools/integration-max/upper_max/son/chaine_son.py"):
        t = open(os.path.join(depot(), f), encoding="utf-8").read()
        verifie("maison/USERPROFILE_dans_" + os.path.basename(f), "USERPROFILE=os.path.join(R, \"home\")" in t)
    shutil.rmtree(T)


# ----------------------------------------------------------------------------------------------------------------------
@protege("fige")
def fige():
    T = tempfile.mkdtemp(prefix="hsfa_fige_")
    try:
        brut = r"C:\Users\test\atelier\a_dossier" if WIN else "/home/test/atelier/a_dossier"
        try:
            compile('P = "%s"\n' % r"C:\Users\test\atelier", "<temoin>", "exec")
            note("INFO", "fige/temoin_sans_correctif", "pas de SyntaxError ?")
        except SyntaxError as x:
            note("OK", "fige/temoin_sans_correctif", "SyntaxError attendue : %s" % x.msg)
        # fige.py (Upper MAX)
        sys.path.insert(0, os.path.join(depot(), "tools", "integration-max", "upper_max"))
        import fige as F
        src = os.path.join(T, "fige_um"); os.makedirs(os.path.join(src, "outils"))
        open(os.path.join(src, "outils", "mod_um.py"), "w", encoding="utf-8").write(
            'P = "@UM_HOME@/.cache/sfa3max"\nQ = \'@UM_WORK@\'\nR = "@UM_AG@" + "/x"\n')
        n = F.materialiser(os.path.join(T, "um"), {"@UM_HOME@": brut, "@UM_WORK@": brut + "\\travail" if WIN else brut,
                                                   "@UM_AG@": os.path.join(T, "ag")}, fige=src)
        sys.path.insert(0, os.path.join(T, "um", "outils"))
        import mod_um
        att = brut.replace("\\", "/")
        verifie("fige/fige.py/import", mod_um.P == att + "/.cache/sfa3max", "%d fichier(s), P=%s" % (n, mod_um.P))
        verifie("fige/fige.py/sans_antislash", "\\" not in mod_um.Q + mod_um.R, mod_um.R)
        # fige35.py (greffe Hyper Arcade)
        sys.path.insert(0, os.path.join(depot(), "tools", "greffe-arcade", "construction"))
        import fige35
        src = os.path.join(T, "fige_ha"); os.makedirs(os.path.join(src, "greffe", "outils"))
        open(os.path.join(src, "greffe", "outils", "mod_ha.py"), "w", encoding="utf-8").write(
            'G = "@HA_G@/donnees"\nH = "@HA_HOME@"\n')
        fige35.materialiser(os.path.join(T, "ha"), [("@HA_G@", brut + "\\greffe" if WIN else brut),
                                                    ("@HA_HOME@", os.path.join(T, "h"))], racines=[src])
        sys.path.insert(0, os.path.join(T, "ha", "greffe", "outils"))
        import mod_ha
        verifie("fige/fige35.py/import", mod_ha.G.startswith(att) and "\\" not in mod_ha.G + mod_ha.H, mod_ha.G)
    finally:
        shutil.rmtree(T, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------------------
CODE_ENC = r"""
import locale, sys
p = sys.argv[1]; t = sys.argv[2]
print("utf8_mode=%d prefere=%s" % (sys.flags.utf8_mode, locale.getpreferredencoding(False)))
try:
    open(p, "w").write(t + "\n")
    print("ecrit", open(p, "rb").read().hex())
    print("relu_ok", open(p).read() == t + "\n")
except UnicodeError as x:
    print("UnicodeError", type(x).__name__)
"""


def _encodage(python, nom, T, exige_utf8=True):
    sans = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    res = {}
    for cas, env in (("sans_PYTHONUTF8", sans), ("PYTHONUTF8=1", dict(sans, PYTHONUTF8="1"))):
        p = os.path.join(T, "t_%s.txt" % cas.replace("=", ""))
        r = subprocess.run(python + ["-c", CODE_ENC, p, TEXTE_ACCENTUE], capture_output=True, env=env)
        out = r.stdout.decode("utf-8", "replace").strip().splitlines(); res[cas] = out
        if cas == "sans_PYTHONUTF8":
            note("INFO", "%s/%s" % (nom, cas), " | ".join(out) or r.stderr.decode("utf-8", "replace")[-300:])
        else:
            nl = "0d0a" if WIN else "0a"
            ok = r.returncode == 0 and out[:1] == ["utf8_mode=1 prefere=utf-8"] and \
                ("ecrit " + (TEXTE_ACCENTUE.encode("utf-8").hex() + nl)) in out and "relu_ok True" in out
            (verifie if exige_utf8 else lambda n, c, d: note("OK" if c else "INFO", n, d))(
                "%s/%s" % (nom, cas), ok, " | ".join(x[:60] for x in out) or r.stderr.decode("utf-8", "replace")[-300:])
    return res


@protege("encodage")
def encodage():
    T = tempfile.mkdtemp(prefix="hsfa_enc_")
    try:
        _encodage([sys.executable], "encodage/python", T)
        open(os.path.join(T, "nl.txt"), "w").write("a\n")
        note("INFO", "encodage/fin_de_ligne_mode_texte", open(os.path.join(T, "nl.txt"), "rb").read())
    finally:
        shutil.rmtree(T, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------------------
@protege("git")
def git():
    D = depot()
    g = lambda *a, **k: subprocess.run(["git"] + list(a), capture_output=True, text=True, **k)
    note("INFO", "git/version", g("--version").stdout.strip())
    note("INFO", "git/core.autocrlf", (g("config", "--show-origin", "--get-all", "core.autocrlf", cwd=D).stdout.strip()
                                      or "(non defini)").replace("\n", " ; "))
    r = g("ls-files", "--eol", cwd=D)
    if not verifie("git/ls-files", r.returncode == 0, r.stderr.strip()):
        return
    crlf, lus, total = [], 0, 0
    for l in r.stdout.splitlines():
        meta, _, nom = l.partition("\t")
        c = meta.split()
        if len(c) < 3: continue
        total += 1
        i, w = c[0], c[1]
        if nom.endswith((".txt", ".tsv")) and nom.startswith(("tools/", "scripts/", "src/", "max/")): lus += 1
        if w == "w/crlf" and i not in ("i/crlf", "i/mixed") and "eol=crlf" not in meta:   # .bat : CRLF voulu
            crlf.append(nom)
    verifie("git/aucun_fichier_converti_en_CRLF", not crlf, "%d / %d fichiers (dont .txt/.tsv des outils : %d) ; %s"
            % (len(crlf), total, lus, crlf[:5]))
    for f in ("tools/flux/hsfa_flux_table.txt", "tools/flux/codes_musique_hyper.txt"):
        p = os.path.join(D, f)
        if os.path.exists(p):
            verifie("git/LF/" + os.path.basename(f), b"\r\n" not in open(p, "rb").read())
    # temoin : la meme chose SANS .gitattributes (montre ce que ferait la copie Git de cette machine)
    T = tempfile.mkdtemp(prefix="hsfa_git_")
    try:
        a = os.path.join(T, "a"); os.makedirs(a)
        idt = ["-c", "user.name=essai", "-c", "user.email=essai@example.invalid", "-c", "init.defaultBranch=x"]
        g(*idt, "init", "-q", a); open(os.path.join(a, "t.txt"), "wb").write(b"l1\nl2\n")
        g(*idt, "add", "t.txt", cwd=a); g(*idt, "commit", "-qm", "x", cwd=a)
        g("clone", "-q", a, os.path.join(T, "b"))
        b = open(os.path.join(T, "b", "t.txt"), "rb").read()
        note("INFO", "git/temoin_sans_gitattributes", "copie %s" % ("en CRLF (autocrlf actif)" if b"\r\n" in b else "en LF"))
    finally:
        shutil.rmtree(T, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------------------
C1, C2 = 7400, -3342          # coefficients ADX (passe-haut 500 Hz, 48 kHz) ; ceux du decodeur (hsfa_flux.h, en double)


def signal_synthetique(n):
    """stereo 16 bits, en entiers seulement (memes octets partout) : triangles, enveloppe, petit bruit (LCG)"""
    g, d, x = [], [], 12345
    for i in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        bruit = (x >> 16) % 401 - 200
        t1 = i % 218; tri1 = (t1 * 4 * 6000 // 218 - 6000) if t1 < 109 else (18000 - t1 * 4 * 6000 // 218)
        t2 = i % 145; tri2 = (t2 * 4 * 3000 // 145 - 3000) if t2 < 72 else (9000 - t2 * 4 * 3000 // 145)
        env = 50 + (i // 480) % 50
        g.append(max(-32768, min(32767, (tri1 * env) // 100 + tri2 // 2 + bruit)))
        d.append(max(-32768, min(32767, (tri2 * env) // 100 + tri1 // 3 - bruit)))
    return g, d


def adx_synthetique(n=144000, debut=48000, fin=120000, freq=48000):
    """ADX type 3, 4 bits, stereo, boucle [debut, fin) (en-tete version 3) ; encodeur simple en entiers"""
    g, d = signal_synthetique(n)
    co = 0x3C
    h = bytearray(co + 4)
    h[0:2] = b"\x80\x00"; h[2:4] = struct.pack(">H", co)
    h[4], h[5], h[6], h[7] = 3, 18, 4, 2
    h[8:12] = struct.pack(">I", freq); h[12:16] = struct.pack(">I", n); h[16:18] = struct.pack(">H", 500)
    h[18], h[19] = 3, 0
    h[0x16:0x18] = struct.pack(">H", 1); h[0x18:0x1C] = struct.pack(">I", 1)
    h[0x1C:0x20] = struct.pack(">I", debut); h[0x24:0x28] = struct.pack(">I", fin)
    h[co - 2:co + 4] = b"(c)CRI"
    hist = [[0, 0], [0, 0]]; corps = bytearray()
    for b0 in range(0, n, 32):
        for k, ch in enumerate((g, d)):
            bloc = [ch[b0 + j] if b0 + j < n else 0 for j in range(32)]
            h1, h2 = hist[k]
            m = 0; a1, a2 = h1, h2                       # echelle : residu maximal en boucle ouverte
            for s in bloc:
                m = max(m, abs(s - ((C1 * a1 + C2 * a2) >> 12))); a2, a1 = a1, s
            sc = max(1, min(0x10000, (m + 6) // 7))
            nib = []
            for s in bloc:
                pred = (C1 * h1 + C2 * h2) >> 12
                q = max(-8, min(7, (2 * (s - pred) + sc) // (2 * sc)))
                v = max(-32768, min(32767, q * sc + pred)); h2, h1 = h1, v; nib.append(q & 15)
            hist[k] = [h1, h2]
            corps += struct.pack(">H", sc - 1) + bytes((nib[2 * j] << 4) | nib[2 * j + 1] for j in range(16))
    return bytes(h) + bytes(corps) + b"\x80\x01\x00\x0e" + bytes(14)


def afs(entrees):
    o = 2048; tab = []; c = b""
    for e in entrees:
        tab.append((o, len(e))); p = e + bytes((-len(e)) % 2048); c += p; o += len(p)
    t = b"AFS\0" + struct.pack("<I", len(entrees)) + b"".join(struct.pack("<II", *x) for x in tab)
    return t + bytes(2048 - len(t)) + c


@protege("flux")
def flux(natifs=None):
    X = ".exe" if WIN else ""
    if natifs:
        os.environ["HSFA_OGGENC"] = os.path.abspath(os.path.join(natifs, "hsfa_oggenc" + X))
        os.environ["HSFA_FLUXTOOL"] = os.path.abspath(os.path.join(natifs, "fluxtool" + X))
    if not (os.environ.get("HSFA_OGGENC") and os.environ.get("HSFA_FLUXTOOL")):
        note("ECHEC", "flux/outils", "--natifs ou HSFA_OGGENC / HSFA_FLUXTOOL requis"); return
    sys.path.insert(0, os.path.join(depot(), "tools", "flux")); sys.path.insert(0, os.path.join(depot(), "tools", "flux", "oggenc"))
    import flux_ogg, construit_oggenc
    m = construit_oggenc.verifie(os.environ["HSFA_OGGENC"])
    verifie("flux/hsfa_oggenc_signal_d_essai", m == construit_oggenc.SIGNAL_MD5, m)
    T = tempfile.mkdtemp(prefix="hsfa_flux_")
    try:
        adx = adx_synthetique(); A = os.path.join(T, "y.afs"); open(A, "wb").write(afs([adx]))
        e = {"adx": hashlib.md5(adx).hexdigest()}
        r = subprocess.run([os.environ["HSFA_FLUXTOOL"], "pcm", A, "0", os.path.join(T, "adx.raw")],
                           capture_output=True, text=True)
        verifie("flux/fluxtool_adx", r.returncode == 0, (r.stdout + r.stderr).strip())
        e["pcm_adx"] = md5(os.path.join(T, "adx.raw"))
        cache = os.path.join(T, "cache")
        ogg, msg = flux_ogg.encode(A, 0, e["adx"], cache)
        verifie("flux/flux_ogg.encode", ogg is not None and msg == "encode", msg)
        if ogg:
            e["ogg"] = md5(ogg)
            B = os.path.join(T, "o.afs"); flux_ogg._afs_un(ogg, B)
            fr, n, dd, ff = flux_ogg.pcm(os.environ["HSFA_FLUXTOOL"], B, 0, os.path.join(T, "ogg.raw"))
            e["pcm_ogg"] = md5(os.path.join(T, "ogg.raw")); e["boucle_ogg"] = "%d %d" % (dd, ff)
        for k in REF_FLUX:
            verifie("flux/meme_que_linux/" + k, e.get(k) == REF_FLUX[k], "%s (Linux : %s)" % (e.get(k), REF_FLUX[k]))
        print("REF_FLUX = %r" % e)
    finally:
        shutil.rmtree(T, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------------------
@protege("exe")
def exe_(exe):
    exe = os.path.abspath(exe)
    r = subprocess.run([exe, "--auto-test"], capture_output=True, text=True)
    verifie("exe/auto-test", r.returncode == 0, " | ".join((r.stdout + r.stderr).strip().splitlines()))
    T = tempfile.mkdtemp(prefix="hsfa_exe_")
    try:
        _encodage([exe], "exe/encodage", T)
        r = subprocess.run([exe, "-c", "import sys; print(sys.flags.utf8_mode, sys.flags.ignore_environment, "
                            "sys.flags.isolated)"], capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8="1"))
        note("INFO", "exe/drapeaux(utf8_mode ignore_environment isolated)", r.stdout.strip() + r.stderr.strip()[-200:])
        # l'exe comme « python » d'un script (hsfa_build : <exe> etape.py ...), avec les parties sans natifs externes
        sans = {k: v for k, v in os.environ.items() if k not in ("HSFA_OGGENC", "HSFA_FLUXTOOL")}
        r = subprocess.run([exe, os.path.abspath(__file__), "--parties", "fige,encodage,flux,coeur,etape"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(sans, HSFA_DEPOT_ESSAI=depot(), PYTHONUTF8="1", PYTHONIOENCODING="utf-8"))
        for l in r.stdout.splitlines():
            c = l.split(None, 1)
            if c and c[0] in ("OK", "ECHEC", "INFO"):
                note(c[0], "exe/script/" + c[1].strip())
        verifie("exe/script/code_de_sortie", r.returncode == 0, r.stderr.strip()[-500:])
    finally:
        shutil.rmtree(T, ignore_errors=True)


@protege("etape")
def etape():
    """DANS l'executable : une etape lancee comme hsfa_build.Construction.lance (sys.executable, env() propre +
    PYTHONUTF8=1 + _PYI_*), qui ecrit un texte accentue en mode texte par defaut (textes_max.py)"""
    if not getattr(sys, "frozen", False):
        note("INFO", "etape", "hors executable : rien a faire"); return
    garde = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "USERPROFILE")
    e = {k: v for k, v in os.environ.items() if k in garde or k.startswith("_PYI_")}
    e["PYTHONIOENCODING"] = "utf-8"; e["PYTHONUTF8"] = "1"
    T = tempfile.mkdtemp(prefix="hsfa_etape_")
    try:
        p = os.path.join(T, "textes_max.txt")
        r = subprocess.run([sys.executable, "-c", CODE_ENC, p, TEXTE_ACCENTUE], capture_output=True, env=e)
        out = r.stdout.decode("utf-8", "replace").strip()
        verifie("etape/PYTHONUTF8_honore_par_l_exe", r.returncode == 0 and "utf8_mode=1 prefere=utf-8" in out
                and "relu_ok True" in out, out.replace("\n", " | ") + r.stderr.decode("utf-8", "replace")[-300:])
    finally:
        shutil.rmtree(T, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------------------
def _fopen_c(octets):
    """fopen() « etroit » de la bibliotheque C (comme le coeur FBNeo et fluxtool) : True si le fichier s'ouvre"""
    import ctypes, ctypes.util
    libc = ctypes.cdll.msvcrt if WIN else ctypes.CDLL(ctypes.util.find_library("c"))
    libc.fopen.restype = ctypes.c_void_p; libc.fopen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    libc.fclose.argtypes = [ctypes.c_void_p]
    f = libc.fopen(octets, b"rb")
    if f: libc.fclose(f)
    return bool(f)


@protege("coeur")
def coeur():
    """ydata.txt : chemin de l'ISO relu par le coeur (fopen) ; hsfa_build.chemin_pour_coeur, en mode UTF-8 ou non"""
    sys.path.insert(0, os.path.join(depot(), "scripts", "construction"))
    import hsfa_build as H
    T = tempfile.mkdtemp(prefix="hsfa_coeur_")
    try:
        for nom, d in (("accents_cp1252", "Rémi Ø"), ("hors_cp1252", "Łukasz ō")):
            D = os.path.join(T, d); os.makedirs(D); iso = os.path.join(D, "anthology é.iso"); open(iso, "wb").write(b"x")
            b = H.chemin_pour_coeur(iso)
            note("INFO", "coeur/%s/octets" % nom, "utf8_mode=%d : %r" % (sys.flags.utf8_mode, b[-40:]))
            verifie("coeur/%s/fopen_du_coeur" % nom, _fopen_c(b), b[-40:])
            note("INFO", "coeur/%s/temoin_utf8" % nom, "fopen(UTF-8) %s" % ("ouvre" if _fopen_c(iso.encode("utf-8"))
                                                                         else "n'ouvre PAS"))
            # fluxtool (main « etroit » : arguments convertis en page de code ANSI sous Windows) sur un AFS de ce dossier
            if os.environ.get("HSFA_FLUXTOOL"):
                A = os.path.join(D, "y é.afs"); open(A, "wb").write(afs([adx_synthetique(3200, 0, 0)]))
                r = subprocess.run([os.environ["HSFA_FLUXTOOL"], "pcm", A, "0", os.path.join(D, "s é.raw")],
                                   capture_output=True)       # octets : un message d'erreur est en page de code ANSI
                (verifie if nom == "accents_cp1252" else lambda n, c, dd: note("OK" if c else "INFO", n, dd))(
                    "coeur/%s/fluxtool_chemin" % nom, r.returncode == 0,
                    (r.stdout + r.stderr).decode("utf-8", "replace").strip()[-200:])
    finally:
        shutil.rmtree(T, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------------------
GARDE_UM_PROG = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "SYSTEMROOT", "HSFA_ASM", "HSFA_VASM",
                 "HSFA_SANS_LIENS", "PYTHONUTF8")          # um_prog.py AVANT correctif (main du 11/11) : temoin
GARDE_HSFA_BUILD = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "USERPROFILE")


def _garde_um_prog():
    """liste des variables gardees par um_prog.py tel qu'il est dans ce depot (tuple contenant "PATH" et "HOME")"""
    import ast
    a = ast.parse(open(os.path.join(depot(), "tools", "integration-max", "upper_max", "um_prog.py"), encoding="utf-8").read())
    for n in ast.walk(a):
        if isinstance(n, ast.Tuple):
            v = {e.value for e in n.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
            if "PATH" in v and "HOME" in v: return v
    return set()


@protege("umprog")
def umprog(exe=None):
    """etapes d'Upper MAX : um_prog.py relance « python » (l'exe dans le constructeur) avec un environnement filtre
    (GARDE_UM_PROG : ni USERPROFILE, ni TEMP / TMP, ni _PYI_*) ; l'etape demarre-t-elle, ou ecrit-elle son dossier
    temporaire, et que vaut « ~ » ?"""
    code = ("import os, sys, tempfile; print('maison=%s' % os.path.expanduser('~/.cache/sfa3max')); "
            "print('temp=%s' % tempfile.gettempdir()); print('exe=%s' % sys.executable)")
    for nom, py in (("python", sys.executable), ("exe", exe and os.path.abspath(exe))):
        if not py: continue
        for cas, garde in (("env_um_prog", GARDE_UM_PROG), ("env_hsfa_build", GARDE_HSFA_BUILD),
                           ("env_um_prog_actuel", _garde_um_prog())):
            e = {k: v for k, v in os.environ.items() if k.upper() in garde}
            if cas != "env_um_prog": e.update({k: v for k, v in os.environ.items() if k.startswith("_PYI_")})
            try:
                r = subprocess.run([py, "-c", code], capture_output=True, text=True, env=e, timeout=300)
                out = (r.stdout + r.stderr).strip().replace("\n", " | ")
                maison_ok = "maison=~" not in r.stdout
                v = r.returncode == 0 and (maison_ok or not WIN)
                (verifie if cas != "env_um_prog" else lambda n, c, d: note("OK" if c else "INFO", n, d))(
                    "umprog/%s/%s" % (nom, cas), v, "code %d : %s" % (r.returncode, out[-400:]))
            except Exception as x:
                note("INFO" if cas == "env_um_prog" else "ECHEC", "umprog/%s/%s" % (nom, cas), "%s: %s" % (type(x).__name__, x))


# ----------------------------------------------------------------------------------------------------------------------
INTERPRETE_SCRIPT = r"""import json, os, sys
print("SCRIPT " + json.dumps({"argv": sys.argv, "nom": __name__, "pyc": sys.dont_write_bytecode}))
"""


@protege("interprete")
def interprete(exe=None):
    """l'executable comme « python » des etapes, compare au vrai python (memes reponses attendues) : PYTHONPATH (regen_max :
    dialogues_max « -c import iso_psp »), dossier courant pour -c, copie sur disque prioritaire sur un module embarque,
    -I, PYTHONDONTWRITEBYTECODE / -B, codes de sortie (sys.exit, exception, script absent), script a UN argument avec
    stdin ouvert (v0.1.10 Windows : attente d'Entree), et la regle d'attente elle-meme (_garder_console_ouverte)"""
    T = tempfile.mkdtemp(prefix="hsfa_interp_")
    try:
        pp, cwd, sd = (os.path.join(T, d) for d in ("pp", "cwd", "s"))
        for d in (pp, cwd, sd): os.makedirs(d)
        open(os.path.join(pp, "hsfa_essai_pp.py"), "w", encoding="utf-8").write("print('PP_OK')\n")
        open(os.path.join(pp, "chd_iso.py"), "w", encoding="utf-8").write("print('DISQUE')\n")      # meme nom qu'un module embarque
        open(os.path.join(cwd, "hsfa_essai_cwd.py"), "w", encoding="utf-8").write("print('CWD_OK')\n")
        open(os.path.join(sd, "etape.py"), "w", encoding="utf-8").write(INTERPRETE_SCRIPT)
        propre = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        regen = ("import os, runpy, sys, hsfa_essai_pp\nsys.argv = ['etape.py', 'source']\n"
                 "runpy.run_path(%r, run_name='__main__')\n" % os.path.join(sd, "etape.py"))
        cas = [   # nom, argv, env en plus, attendu (code, texte present dans la sortie)
            ("pythonpath_-c", ["-c", "import hsfa_essai_pp"], {"PYTHONPATH": pp}, (0, "PP_OK")),
            ("forme_regen_max", ["-c", regen], {"PYTHONPATH": pp}, (0, '"source"')),
            ("dossier_courant_-c", ["-c", "import hsfa_essai_cwd"], {}, (0, "CWD_OK")),
            ("disque_avant_embarque", ["-c", "import chd_iso"], {"PYTHONPATH": pp}, (0, "DISQUE")),
            ("-I_ignore_pythonpath", ["-I", "-c", "import hsfa_essai_pp"], {"PYTHONPATH": pp}, (1, "ModuleNotFoundError")),
            ("pythondontwritebytecode", ["-c", "import sys; print('PYC', sys.dont_write_bytecode)"],
             {"PYTHONDONTWRITEBYTECODE": "1"}, (0, "PYC True")),
            ("-B", ["-B", "-c", "import sys; print('PYC', sys.dont_write_bytecode)"], {}, (0, "PYC True")),
            ("-u", ["-u", "-c", "print('U_OK')"], {}, (0, "U_OK")),
            ("sys.exit(3)", ["-c", "import sys; sys.exit(3)"], {}, (3, "")),
            ("exception", ["-c", "raise ValueError('essai')"], {}, (1, "ValueError: essai")),
            ("script_absent", [os.path.join(T, "absent.py")], {}, (2, "absent.py")),
            ("script_un_argument_stdin_ouvert", [os.path.join(sd, "etape.py"), "source"], {}, (0, '"source"')),
        ]
        for nom, py in (("python", sys.executable), ("exe", exe and os.path.abspath(exe))):
            if not py: continue
            for c, args, plus, (code, texte) in cas:
                # stdin = tube jamais ferme par l'essai : une attente d'Entree se voit au delai depasse
                p = subprocess.Popen([py] + args, cwd=cwd, env=dict(propre, **plus), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                try:
                    out = p.communicate(timeout=120)[0].decode("utf-8", "replace")
                except subprocess.TimeoutExpired:
                    p.kill(); p.communicate()
                    verifie("interprete/%s/%s" % (nom, c), False, "delai depasse : attente (stdin ?)"); continue
                verifie("interprete/%s/%s" % (nom, c), p.returncode == code and texte in out,
                        "code %d : %s" % (p.returncode, out.strip().replace("\n", " | ")[-300:]))
        # regle d'attente d'Entree de l'executable (Windows, image glissee) : jamais en role d'interpreteur
        sys.path.insert(0, ICI)
        try:
            import hsfa_constructeur as H
            g = H._garder_console_ouverte
            verifie("interprete/attente/image_glissee", g(["exe", "C:\\jeux\\anthology.iso"], False, windows=True))
            verifie("interprete/attente/role_python", not g(["exe", "C:\\jeux\\anthology.iso"], True, windows=True))
            verifie("interprete/attente/script_un_argument", not g(["exe", "convert_max.py"], False, windows=True))
            verifie("interprete/attente/option", not g(["exe", "--console"], False, windows=True))
            verifie("interprete/attente/hors_windows", not g(["exe", "anthology.iso"], False, windows=False))
        finally:
            sys.path.remove(ICI)
    finally:
        shutil.rmtree(T, ignore_errors=True)


def lance_non_admin(argv):
    """relance argv avec un jeton restreint (groupe Administrateurs en refus seul, aucun privilege, integrite moyenne :
    comme un compte limite / UAC sans elevation) ; rend le code de sortie"""
    import ctypes
    from ctypes import wintypes as W
    a = ctypes.WinDLL("advapi32", use_last_error=True); k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = W.HANDLE; k.GetCurrentProcess.argtypes = []
    k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    k.GetExitCodeProcess.argtypes = [W.HANDLE, ctypes.POINTER(W.DWORD)]
    a.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, ctypes.POINTER(W.HANDLE)]
    a.GetLengthSid.argtypes = [ctypes.c_void_p]; a.GetLengthSid.restype = W.DWORD

    def ok(v, nom):
        if not v: raise OSError(ctypes.get_last_error(), "%s : %s" % (nom, ctypes.FormatError(ctypes.get_last_error())))

    class SAA(ctypes.Structure): _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", W.DWORD)]

    class SI(ctypes.Structure):
        _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR), ("lpTitle", W.LPWSTR),
                    ("dwX", W.DWORD), ("dwY", W.DWORD), ("dwXSize", W.DWORD), ("dwYSize", W.DWORD),
                    ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD), ("dwFillAttribute", W.DWORD),
                    ("dwFlags", W.DWORD), ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
                    ("lpReserved2", ctypes.c_void_p), ("hStdInput", W.HANDLE), ("hStdOutput", W.HANDLE),
                    ("hStdError", W.HANDLE)]

    class PI(ctypes.Structure):
        _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE), ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]

    tok = W.HANDLE(); ok(a.OpenProcessToken(k.GetCurrentProcess(), 0xF01FF, ctypes.byref(tok)), "OpenProcessToken")
    sid = ctypes.create_string_buffer(68); n = W.DWORD(68)
    ok(a.CreateWellKnownSid(26, None, sid, ctypes.byref(n)), "CreateWellKnownSid")      # BUILTIN\Administrateurs
    dis = SAA(ctypes.cast(sid, ctypes.c_void_p), 0)
    nt = W.HANDLE()
    ok(a.CreateRestrictedToken(tok, 0x1 | 0x4, 1, ctypes.byref(dis), 0, None, 0, None, ctypes.byref(nt)),
       "CreateRestrictedToken")                     # DISABLE_MAX_PRIVILEGE | LUA_TOKEN
    psid = ctypes.c_void_p(); ok(a.ConvertStringSidToSidW("S-1-16-8192", ctypes.byref(psid)), "ConvertStringSidToSid")
    lab = SAA(psid, 0x20)                           # integrite moyenne (SE_GROUP_INTEGRITY)
    ok(a.SetTokenInformation(nt, 25, ctypes.byref(lab), ctypes.sizeof(lab) + a.GetLengthSid(psid)),
       "SetTokenInformation(TokenIntegrityLevel)")
    si = SI(); si.cb = ctypes.sizeof(si); pi = PI()
    ligne = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
    if not a.CreateProcessAsUserW(nt, None, ligne, None, None, False, 0x08000000 | 0x400, None, os.getcwd(),
                                  ctypes.byref(si), ctypes.byref(pi)):
        err = ctypes.get_last_error()
        note("INFO", "non_admin/CreateProcessAsUser", "erreur %d ; essai CreateProcessWithTokenW" % err)
        ok(a.CreateProcessWithTokenW(nt, 0, None, ligne, 0x08000000 | 0x400, None, os.getcwd(), ctypes.byref(si),
                                     ctypes.byref(pi)), "CreateProcessWithTokenW")
    k.WaitForSingleObject(pi.hProcess, 0xFFFFFFFF)
    code = W.DWORD(); k.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
    return code.value


DEFAUT = "liens,maison,fige,encodage,git,flux,coeur"


def main():
    for f in (sys.stdout, sys.stderr):              # console Windows en cp1252 : pas d'arret sur un caractere
        try: f.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError): pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parties", default=DEFAUT)
    ap.add_argument("--natifs")
    ap.add_argument("--exe")
    ap.add_argument("--non-admin", action="store_true")
    ap.add_argument("--exige-sans-droit", action="store_true")
    ap.add_argument("--rapport")
    a = ap.parse_args()
    if a.non_admin:
        if not WIN:
            print("--non-admin : Windows seulement"); return 0
        T = tempfile.mkdtemp(prefix="hsfa_na_"); rap = os.path.join(T, "rapport.txt")
        cmd = [sys.executable, os.path.abspath(__file__), "--parties", a.parties if a.parties != DEFAUT else
               "liens,encodage", "--exige-sans-droit", "--rapport", rap]
        if a.exe: cmd += ["--exe", os.path.abspath(a.exe)]
        code = lance_non_admin(cmd)
        print(open(rap, encoding="utf-8").read() if os.path.exists(rap) else "(pas de rapport de l'enfant)")
        print("code de sortie de l'enfant (jeton sans droit) : %d" % code)
        return code
    P = a.parties.split(",")
    if "liens" in P: liens_(a.exige_sans_droit)
    if "maison" in P: maison()
    if "fige" in P: fige()
    if "encodage" in P: encodage()
    if "git" in P: git()
    if "flux" in P: flux(a.natifs)
    if "coeur" in P: coeur()
    if "exe" in P: exe_(a.exe)
    if "umprog" in P: umprog(a.exe)
    if "interprete" in P: interprete(a.exe)
    if "etape" in P: etape()
    n = sum(1 for r in resultats if r[0] == "ECHEC")
    bilan = "BILAN : %d OK, %d ECHEC, %d INFO (%s, %s)" % (sum(1 for r in resultats if r[0] == "OK"), n,
                                                          sum(1 for r in resultats if r[0] == "INFO"), sys.platform,
                                                          "exe" if getattr(sys, "frozen", False) else sys.version.split()[0])
    print(bilan)
    if a.rapport:
        with open(a.rapport, "w", encoding="utf-8") as f:
            for r in resultats: f.write("%-5s %s%s\n" % (r[0], r[1], (" : %s" % r[2]) if r[2] else ""))
            f.write(bilan + "\n")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
