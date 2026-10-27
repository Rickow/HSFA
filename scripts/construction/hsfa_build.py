#!/usr/bin/env python3
"""hsfa_build.py -- reconstruit les jeux HSFA (SFA3, Upper, Hyper ; a terme MAX) a partir de l'ISO de l'utilisateur.

Le depot ne contient que des outils et des modifications : toutes les donnees de jeu sont lues dans l'ISO PS2 de
*Street Fighter Alpha Anthology* (USA, SLUS-21317) fournie par l'utilisateur. La ROM graphique CPS2 de SFA3 est
reconstruite depuis l'ISO (rom_iso.py) ; --arcade (facultatif) donne a la place celle de l'arcade. Les etapes appellent les scripts existants du projet PAR SOUS-PROCESSUS (aucune
copie) ; les chemins codes en dur dans ces scripts sont remplaces a l'execution (voir PARAMETRAGES et BUILD.md).

Usage :
  python3 hsfa_build.py --anthology ISO --sortie DIR [--jeux sfa3,upper,hyper] [--arcade DIR|ZIP ...] (facultatif)
                        [--max ISO_PSP] [--etape NOM] [--jusqua NOM] [--force] [--liste] [--comparer DIR]
                        [--date-source SECONDES] [--plans-fenetre auto|oui|non] [--flux-format ogg|adx]
                        [--sans-flux] [--rejeu-table FICHIER] [--sans-redirection]
  --date-source : date fixe des membres des zips (defaut $SOURCE_DATE_EPOCH, sinon 1980-01-01) : zips identiques a l'octet.
  --plans-fenetre : tables plan1/plan2 limitees aux codes que le banc honore (auto : oui sans --arcade).
Etapes : voir --liste.  Chaque etape est idempotente : elle est sautee si ses entrees, ses outils et ses
parametres n'ont pas change depuis la derniere execution reussie (etat.json) et que ses sorties sont intactes.
Dependances : Python 3.8+ ; numpy pour les etapes graphiques (gfx_*), cherche dans --python-numpy, sinon
l'interpreteur courant, sinon <HSFA>/venv/bin/python. Rien d'autre (ni MAME, ni vasm, ni unidasm).
"""
import argparse, hashlib, importlib, json, os, shutil, struct, subprocess, sys, time, zipfile

ICI = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------------------------------------------------
# Outils du projet (chemins de CE poste ; surchargeables par variable d'environnement ou option --outils-*)
# --------------------------------------------------------------------------------------------------------------------
DEPOT = os.path.normpath(os.path.join(ICI, "..", ".."))      # racine du depot (scripts/construction/..)
_d = lambda *p: os.path.join(DEPOT, *p)
OUTILS_DEFAUT = {
    # traducteur MIPS -> 68000 et scripts graphiques
    "untranspile": os.environ.get("HSFA_OUTILS_UNTRANSPILE", _d("src", "hsfa")),
    # extract_anthology.py (carte AFS de X_DATA + extraction des entrees)
    "extraction": os.environ.get("HSFA_OUTILS_EXTRACTION", _d("src", "hsfa")),
    # mwo3_codec.py (decompresseur LZSS MWo3)
    "mwo3": os.environ.get("HSFA_OUTILS_MWO3", _d("src", "hsfa")),
    # gen_hybride.py + z80son.py (ROM son hybride d'Upper)
    "son_hybride": os.environ.get("HSFA_OUTILS_SON", _d("src", "hsfa")),
    # paquet_fbneo.py (archives du coeur FBNeo HSFA)
    "paquet": os.environ.get("HSFA_OUTILS_PAQUET", _d("tools", "fbneo-hsfa")),
    # gen_table_flux.py (table code son -> flux ADX de Y_DATA, lecteur de flux)
    "flux": os.environ.get("HSFA_OUTILS_FLUX", _d("tools", "flux")),
    # table_son.py (lecture de la table native des commandes son du module)
    "son_table": os.environ.get("HSFA_OUTILS_SON_TABLE", _d("src", "hsfa")),
    # gen_redirection.py + ids_102.tsv + correspondance.tsv (redirection des voix d'Hyper, SON-HYPER-ROM.md §13)
    "son_hyper": os.environ.get("HSFA_OUTILS_SON_HYPER", _d("tools", "son-hyper")),
}
PYTHON_NUMPY_DEFAUT = os.environ.get("HSFA_PYTHON_NUMPY", _d("venv", "bin", "python"))

# --------------------------------------------------------------------------------------------------------------------
# Empreintes de reference (relevees le 2026-10-10 sur l'ISO USA de l'utilisateur et la chaine du projet).
# Ce ne sont que des sommes de controle : aucune donnee de jeu.
# --------------------------------------------------------------------------------------------------------------------
REF_ISO = {   # fichiers cles de l'ISO (ISO 9660) : taille, md5 (None = taille seulement)
    "SYSTEM.CNF": (57, "b28f4071bad98c50b51cf02db9c451a2"),
    "SLUS_213.17": (572352, "11e411ffa03dded28a26fd4241523c35"),
    "X_DATA.BIN": (200214528, None),           # verifie par groupes de jeu (REF_GROUPES) : des variantes existent
    "Y_DATA.BIN": (1823404032, None),          # flux ADX (lecteur de flux) : taille seulement (1,8 Go)
}
REF_XDATA = {   # X_DATA.BIN complet : variantes connues
    "97a0b8de2b7437898602415077bac31f": "USA d'origine (SLUS-21317)",
    "53821dc5ccee55d7068609f4736c90b8": "variante « All Unlocked » (b_usa e203 et gfx ro6 e527 modifies : sans effet ici)",
}
# Groupes de jeu de X_DATA (AFS) : entrees [debut, fin) delimitees par les modules MWo3, md5 de leur concatenation
REF_GROUPES = {
    "b":   (203, 206, "e535bb5cb3bc86032052596d8da07db5"), "ro1": (206, 224, "b93119d8cf293ecf72310a5b5e73e765"),
    "ro2": (224, 253, "dfdbe6bcd605475de4d3b8bb58139fd8"), "ro3": (253, 348, "be7e3bab59326a91132eed56e576d4d1"),
    "ro4": (348, 350, "44b7dd98aacc75512f939647ce21e646"), "ro5": (350, 526, "e3741dd9ce3a3cd8cdea66d30cdfb8ed"),
    "ro6": (526, 536, "0b0e4d1a0626e0e7e800a5131da781b8"), "ro7": (536, 543, "0cd8e0a95a77ae17c402236492cbde9c"),
    "ro8": (543, 544, "68f5a143d03bdd28db23cda949c835d9"), "ro9": (544, 553, "7fc8e6e0b44d23d8b3fea41a3c9a633f"),
}
# (SFA3 lit aussi des entrees du groupe ro5 : banques 391-412 et 456-457 de sa carte, anims communes)
GROUPES_REQUIS = {"sfa3": ["ro3", "ro5"], "upper": ["ro5", "ro3"], "hyper": ["ro9", "ro5", "ro3", "ro2", "ro1"]}
REF_MANIFESTE = "673d96d827900d31ea9397838f82e677"   # manifest.csv (fins de ligne LF ; 76a76db5... avec CRLF sous Windows)
REF_MODULES = {   # modules MIPS decompresses (anthology_extract/decompressed)
    "ro3": "e4826fe46eae0631e2e42cdcefd95459",
    "ro5": "17e475920b467d9d0131eba67619de17",
    "ro9": "b4662de92db7ba9a3db2036084f974a0",
}
REF_ARCADE_GFX = {   # ROM graphique CPS2 de SFA3 (commune a tous les jeux sfa3*), fournie par l'utilisateur
    "sz3.13m": "47cd1261e9affa4340752f333cd9d1bd", "sz3.14m": "5a50dd038a8c6d442be3d969eedce032",
    "sz3.15m": "d1a50389059d4d2e3b977808401f7766", "sz3.16m": "7612958e66c88b17e30d376f876b77c7",
    "sz3.17m": "4087aabf55ef7e7fe5e24d141c744962", "sz3.18m": "ee582226a3430d844c54924f3f4a652b",
    "sz3.19m": "5a0b9c825183d6efe62698e772fa0022", "sz3.20m": "50bd0e58150ea9e65ffa54353ba007a3",
}
REF_ISO_GFX = {   # la meme ROM reconstruite depuis l'ISO seule (rom_iso.py) : quarts 2-3 (14m/16m/18m/20m) = arcade ;
    # quarts 0-1 (13m/15m/17m/19m) : tuiles de sprites des banques rangees dans un autre ordre (BUILD.md, « Voie ISO seule »)
    "sz3.13m": "03209d40778fe8bdb9efdd31e0042319", "sz3.14m": "5a50dd038a8c6d442be3d969eedce032",
    "sz3.15m": "e941f0517d7ec3e7cc0d833e7a3c69d6", "sz3.16m": "7612958e66c88b17e30d376f876b77c7",
    "sz3.17m": "aa08a44c45b7f48b58b2de1e8a5cbb28", "sz3.18m": "ee582226a3430d844c54924f3f4a652b",
    "sz3.19m": "73fb9e595fd853cd0ff6216f8d915195", "sz3.20m": "50bd0e58150ea9e65ffa54353ba007a3",
}
REF_SON_SFA3 = {   # = ROM son d'arcade de sfa3ud, retrouvee octet pour octet dans X_DATA (e287/e288)
    "sz3.01": "e85da4cc9e1c6562f6be603bfaf8ab11", "sz3.02": "d115146a1e467e038a7acad06193b16d",
    "sz3.11m": "30223d24607f151e2f122c1b2e816817", "sz3.12m": "5356922e2303c320e8d2b0a94c7ed8f7",
}
REF_SON_UPPER = {   # ROM son hybride d'Upper (gen_hybride.py, 2026-10-04)
    "hx3.01": "3ddd95abe2ff1d17db44d24e1bf19ec3", "hx3.02": "c7e3d5a6a1ff43c395c2c52688e6808a",
    "hx3.11m": "8da6a5e4272125bc0a7accada5e249e8", "hx3.12m": "19fb75dc70f4c0029a1ff64a9aba2702",
    "hx3.13m": "30223d24607f151e2f122c1b2e816817", "hx3.14m": "5356922e2303c320e8d2b0a94c7ed8f7",
}
REF_SON_HYPER = {   # redirection des voix d'Hyper (gen_redirection.py, sans voix d'arcade) : = livraison v151
    "ro9_usa_prog68k.bin": "dcda2bbac9751efa89122cb2f1cd0457",   # module ro9 corrige (70 mots)
    "son_donnees_ro9.bin": "ebefd8b2eed7447e6cb78f2f439dea7a",   # bloc de donnees $E70000 (19 712 o)
}
PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
PHOENIX_KEY = b"\xff" * 20     # cle du jeu Phoenix sfa3ud (programme non chiffre) : 20 x $FF (HANDOFF §59)

# Jeux : module de l'Anthology, dossier de travail (meme disposition que <workspace>/work pour paquet_fbneo.py)
JEUX = {
    "sfa3": dict(module="ro3", travail="mame", roms="roms_tr", b32=312, zip="sfa3hsfa", paquet="sfa3"),
    "upper": dict(module="ro5", travail="mame_ro5", roms="roms_ro5", b32=525, zip="sfa3uhsfa", paquet="upper"),
    "hyper": dict(module="ro9", travail="mame_ro9", roms="roms_ro9", b32=548, zip="sfa3hhsfa", paquet="hyper"),
}

# Chemins codes en dur dans les scripts existants, remplaces a l'execution (module, attribut) -> role.
# A rendre parametrables dans les scripts eux-memes (variable d'environnement), voir BUILD.md.
PARAMETRAGES = [
    ("extract_anthology", "PATH", "X_DATA.BIN (chemin Windows E:/ROMS/...)"),
    ("extract_anthology", "OUTDIR", "dossier d'extraction (E:/CLAUDE CODE/anthology_extract)"),
    ("profils", "EXTRACT", "modules decompresses (<workspace>/anthology_extract/decompressed)"),
    ("profils", "PROFILS[*].travail", "dossiers de travail work/mame* (contourne par TRAVAIL)"),
    ("assets_natifs", "EXTRACT", "manifest.csv (<workspace>/anthology_extract)"),
    ("assets_natifs", "CACHE", "cache des anims LU EN PREMIER (<workspace>/work/cps2/anims)"),
    ("census", "RO3", "module (<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin)"),
    ("banques", "MANIF", "manifest.csv"), ("banques", "ROMDIR", "ROM arcade sfa3ud (work/mame/roms/sfa3ud)"),
    ("banques", "OUT / MOD['out']", "tables de banques (work/mame*/banques, PAS de TRAVAIL)"),
    ("gen_son", "XDATA / EXTRACT / ARCADE", "X_DATA, extraction, ROM arcade"),
    ("gen_hybride", "ARCADE", "ROM arcade (recoupement facultatif)"),
    ("mame_test", "main() : src des liens", "liens vers <workspace>/work/mame/roms/sfa3ud (os.listdir neutralise)"),
    ("hsfa_plans / banques.plans256", "sys.path", "mwo3_codec dans <workspace>/anthology_extract"),
]

# --------------------------------------------------------------------------------------------------------------------
# Journal
# --------------------------------------------------------------------------------------------------------------------
class Journal:
    def __init__(self, chemin):
        self.f = open(chemin, "a", encoding="utf-8")
    def __call__(self, msg, niveau="  "):
        ligne = "%s %s%s" % (time.strftime("%Y-%m-%d %H:%M:%S"), niveau, msg)
        print(ligne, flush=True)
        self.f.write(ligne + "\n"); self.f.flush()

def md5_fichier(p, bloc=1 << 22):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(bloc), b""):
            h.update(b)
    return h.hexdigest()

def md5_octets(d): return hashlib.md5(d).hexdigest()

class Echec(Exception):
    pass

# --------------------------------------------------------------------------------------------------------------------
# ISO 9660 (lecture seule, sans dependance) : un DVD PS2 porte un systeme ISO 9660 classique (secteurs de 2 048 o)
# --------------------------------------------------------------------------------------------------------------------
SECTEUR = 2048

def iso_fichiers(iso):
    """{nom (sans ';1') -> (lba, taille)} du repertoire racine"""
    with open(iso, "rb") as f:
        f.seek(16 * SECTEUR); pvd = f.read(SECTEUR)
        if len(pvd) < SECTEUR or pvd[0] != 1 or pvd[1:6] != b"CD001":
            raise Echec("%s : pas de descripteur de volume ISO 9660 au secteur 16 (image .bin/.chd/.cso ? "
                        "il faut une image .iso a 2 048 o/secteur ; pour un .chd : chdman extractdvd -i X.chd -o X.iso)" % iso)
        racine = pvd[156:156 + 34]
        lba, taille = struct.unpack_from("<I", racine, 2)[0], struct.unpack_from("<I", racine, 10)[0]
        f.seek(lba * SECTEUR); rep = f.read(taille)
    res = {}; o = 0
    while o < len(rep):
        n = rep[o]
        if n == 0:                                   # fin du secteur : passer au suivant
            o = (o // SECTEUR + 1) * SECTEUR; continue
        lba_f, t_f = struct.unpack_from("<I", rep, o + 2)[0], struct.unpack_from("<I", rep, o + 10)[0]
        ln = rep[o + 32]; nom = rep[o + 33:o + 33 + ln].decode("ascii", "replace")
        if nom not in ("\x00", "\x01"):
            res[nom.split(";")[0]] = (lba_f, t_f)
        o += n
    return res

def iso_copie(iso, lba, taille, dest=None):
    """lit (et copie si dest) un fichier de l'ISO ; rend son md5"""
    h = hashlib.md5(); reste = taille
    out = open(dest + ".tmp", "wb") if dest else None
    with open(iso, "rb") as f:
        f.seek(lba * SECTEUR)
        while reste:
            b = f.read(min(reste, 1 << 22))
            if not b: raise Echec("ISO tronquee")
            h.update(b); reste -= len(b)
            if out: out.write(b)
    if out:
        out.close(); os.replace(dest + ".tmp", dest)
    return h.hexdigest()

# --------------------------------------------------------------------------------------------------------------------
# Lanceur interne : execute un script existant dans un sous-processus, apres avoir remplace ses chemins en dur
#   python3 hsfa_build.py _lancer spec.json
# --------------------------------------------------------------------------------------------------------------------
def _lancer(spec_chemin):
    spec = json.load(open(spec_chemin, encoding="utf-8"))
    for p in reversed(spec.get("sys_path", [])):
        sys.path.insert(0, p)
    os.chdir(spec["cwd"])
    if spec.get("neutraliser_listdir"):
        # mame_test.main() lie les fichiers de <workspace>/work/mame/roms/sfa3ud dans la sortie : on n'en veut pas
        # (chemin absolu de ce poste ou « <workspace>/work/mame/roms/sfa3ud » dans la copie publiee : on compare la fin)
        suffixe = os.path.normpath(spec["neutraliser_listdir"]); _ls = os.listdir
        def listdir(p="."):
            return [] if os.path.normpath(os.path.abspath(str(p))).endswith(suffixe) else _ls(p)
        os.listdir = listdir
    for mod, attr, val in spec.get("patchs", []):
        m = importlib.import_module(mod)
        if "." in attr:
            a, k = attr.split(".", 1); getattr(m, a)[k] = val
        else:
            setattr(m, attr, val)
        print("[hsfa_build] %s.%s = %r" % (mod, attr, val), flush=True)
    sys.argv = spec["argv"]
    if spec.get("code"):
        exec(compile(spec["code"], "<hsfa_build:%s>" % spec.get("nom", "code"), "exec"), {"__name__": "__hsfa__"})
    else:
        m = importlib.import_module(spec["module"])
        getattr(m, spec.get("fonction", "main"))()

# --------------------------------------------------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------------------------------------------------
class Construction:
    def __init__(self, a):
        self.a = a
        self.S = os.path.abspath(a.sortie)
        for d in ("journaux", "cache", "travail", "archives", "specs"):
            os.makedirs(os.path.join(self.S, d), exist_ok=True)
        self.log = Journal(os.path.join(self.S, "journal.txt"))
        self.etat_chemin = os.path.join(self.S, "etat.json")
        self.etat = json.load(open(self.etat_chemin)) if os.path.exists(self.etat_chemin) else {}
        self.O = dict(OUTILS_DEFAUT)
        for k in list(self.O):
            v = getattr(a, "outils_" + k, None)
            if v: self.O[k] = v
        self.jeux = [j.strip() for j in a.jeux.split(",") if j.strip()]
        for j in self.jeux:
            if j not in JEUX: raise Echec("jeu inconnu : %s (connus : %s)" % (j, ", ".join(JEUX)))
        self.cache = os.path.join(self.S, "cache")
        self.xdata = os.path.join(self.cache, "iso", "X_DATA.BIN")
        self.ext = os.path.join(self.cache, "anthology_extract")
        self.dec = os.path.join(self.ext, "decompressed")
        self.anims = os.path.join(self.cache, "anims")
        self.arcade = os.path.join(self.cache, "arcade", "sfa3ud")
        self.W = os.path.join(self.S, "travail")          # = <workspace>/work pour paquet_fbneo.py
        self.modules_son = os.path.join(self.cache, "modules_son")   # module ro9 corrige + bloc $E70000 (Hyper)

    # ---- etat -------------------------------------------------------------------------------------------------------
    def sauve_etat(self):
        tmp = self.etat_chemin + ".tmp"
        json.dump(self.etat, open(tmp, "w"), indent=1, sort_keys=True); os.replace(tmp, self.etat_chemin)

    def empreinte_outils(self, fichiers):
        h = hashlib.sha1()
        for p in sorted(fichiers):
            if os.path.isdir(p):
                for f in sorted(os.listdir(p)):
                    if f.endswith((".py", ".json")):
                        h.update(f.encode()); h.update(open(os.path.join(p, f), "rb").read())
            elif os.path.exists(p):
                h.update(os.path.basename(p).encode()); h.update(open(p, "rb").read())
        return h.hexdigest()

    def cle(self, nom, deps, outils, params):
        h = hashlib.sha1(json.dumps([nom, params], sort_keys=True).encode())
        for d in deps:
            e = self.etat.get(d)
            if not e or not e.get("fait"): raise Echec("etape %s : depend de %s, pas encore faite" % (nom, d))
            h.update(json.dumps(e.get("sorties", {}), sort_keys=True).encode())
        h.update(self.empreinte_outils(outils).encode())
        return h.hexdigest()

    def sorties_intactes(self, e):
        for p, (taille, _md5) in e.get("sorties", {}).items():
            q = os.path.join(self.S, p)
            if not os.path.exists(q) or os.path.getsize(q) != taille: return False
        return True

    def note_sorties(self, chemins):
        r = {}
        for p in chemins:
            if os.path.isfile(p):
                r[os.path.relpath(p, self.S)] = (os.path.getsize(p), md5_fichier(p))
        return r

    # ---- sous-processus ---------------------------------------------------------------------------------------------
    def env(self, **kw):
        garde = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "USERPROFILE")
        e = {k: v for k, v in os.environ.items() if k in garde}   # environnement PROPRE : aucun reglage d'essai
        e["PYTHONPYCACHEPREFIX"] = os.path.join(self.cache, "pyc")  # rien n'est ecrit dans les dossiers d'outils
        e["PYTHONIOENCODING"] = "utf-8"
        e.update({k: str(v) for k, v in kw.items()})
        return e

    def lance(self, etape, spec, env, python=None, nice=True):
        spec.setdefault("nom", etape)
        sp = os.path.join(self.S, "specs", "%s_%d.json" % (etape, len(os.listdir(os.path.join(self.S, "specs")))))
        json.dump(spec, open(sp, "w", encoding="utf-8"), indent=1)
        cmd = [python or sys.executable, os.path.abspath(__file__), "_lancer", sp]
        if nice and os.name == "posix" and shutil.which("nice"): cmd = ["nice", "-n", "19"] + cmd
        logp = os.path.join(self.S, "journaux", etape + ".log")
        t0 = time.time()
        with open(logp, "a", encoding="utf-8") as lg:
            lg.write("\n=== %s  %s\n=== env : %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), " ".join(cmd),
                     {k: v for k, v in env.items() if k not in ("PATH", "HOME")}))
            lg.flush()
            r = subprocess.run(cmd, env=env, stdout=lg, stderr=subprocess.STDOUT)
        if r.returncode:
            raise Echec("%s : le script a echoue (code %d), voir %s" % (etape, r.returncode, logp))
        self.log("%s : %.0f s (journal : %s)" % (spec.get("module") or spec["nom"], time.time() - t0,
                                                   os.path.relpath(logp, self.S)))

    def python_numpy(self):
        cands = [self.a.python_numpy, sys.executable, PYTHON_NUMPY_DEFAUT]
        for p in cands:
            if p and os.path.exists(p) and subprocess.run([p, "-c", "import numpy"], capture_output=True).returncode == 0:
                return p
        raise Echec("numpy introuvable (etapes graphiques) : installer numpy (pip install numpy) ou donner --python-numpy")

    def travail(self, jeu):
        return os.path.join(self.W, JEUX[jeu]["travail"])

    def roms(self, jeu):
        return os.path.join(self.travail(jeu), JEUX[jeu]["roms"], "sfa3ud")

    def patchs_communs(self, module):
        U = self.O["untranspile"]
        return [
            ["profils", "EXTRACT", self.dec],
            ["assets_natifs", "EXTRACT", self.ext],
            ["assets_natifs", "CACHE", self.anims],
            ["assets_natifs", "CACHE_ECRIT", self.anims],
            # census.RO3 : lu a l'import par natmiss (hooks_fork, mame_test.main) ; sans lui, chemin <workspace>
            ["census", "RO3", os.path.join(self.dec, module + "_usa_prog68k.bin")],
        ]

    # ---- etapes ------------------------------------------------------------------------------------------------------
    def e_iso(self):
        src = os.path.abspath(self.a.anthology)
        os.makedirs(os.path.dirname(self.xdata), exist_ok=True)
        ok = True
        if os.path.isdir(src):                       # dossier extrait de l'ISO (contenant X_DATA.BIN)
            self.log("dossier extrait : %s" % src)
            p = os.path.join(src, "X_DATA.BIN")
            if not os.path.exists(p): raise Echec("%s : pas de X_DATA.BIN" % src)
            shutil.copyfile(p, self.xdata + ".tmp"); os.replace(self.xdata + ".tmp", self.xdata)
            mx = md5_fichier(self.xdata)
        elif os.path.isfile(src):
            self.log("ISO : %s (%.2f Go)" % (src, os.path.getsize(src) / 1e9))
            fs = iso_fichiers(src)
            manque = [n for n in REF_ISO if n not in fs]
            if manque:
                raise Echec("l'ISO ne contient pas %s : ce n'est pas Street Fighter Alpha Anthology (USA, SLUS-21317)"
                            % ", ".join(manque))
            mx = None
            for nom, (taille, md5) in REF_ISO.items():
                lba, t = fs[nom]
                if t != taille:
                    self.log("%s : taille %d, attendu %d" % (nom, t, taille), "!! "); ok = False; continue
                if nom == "X_DATA.BIN":
                    mx = iso_copie(src, lba, t, self.xdata); continue
                if md5 is None:
                    self.log("%s : taille conforme (%d o), contenu non verifie" % (nom, t)); continue
                m = iso_copie(src, lba, t)
                # SLUS / SYSTEM.CNF ne servent pas a la chaine : une difference est signalee, pas bloquante
                self.log("%s : md5 %s %s" % (nom, m, "conforme" if m == md5 else "DIFFERENT (attendu %s ; autre "
                         "region ou ISO modifiee ?)" % md5), "   " if m == md5 else "!! ")
            if mx is None: raise Echec("X_DATA.BIN illisible")
        else:
            raise Echec("ISO introuvable : %s" % src)
        self.log("X_DATA.BIN : md5 %s (%s)" % (mx, REF_XDATA.get(mx, "variante inconnue : verification par groupes")))
        # verification par groupe de jeu (seuls les groupes utiles aux jeux demandes sont exiges)
        with open(self.xdata, "rb") as f:
            a = f.read()
        n = struct.unpack_from("<I", a, 4)[0]
        if a[:4] != b"AFS\0" or n != 553:
            raise Echec("X_DATA.BIN : archive AFS inattendue (%r, %d entrees au lieu de 553)" % (a[:4], n))
        toc = [struct.unpack_from("<II", a, 8 + 8 * i) for i in range(n)]
        requis = sorted({g for j in self.jeux for g in GROUPES_REQUIS[j]})
        for g, (d, fn, md5) in REF_GROUPES.items():
            h = hashlib.md5()
            for i in range(d, fn):
                o, s = toc[i]; h.update(a[o:o + s])
            m = h.hexdigest()
            if m == md5: self.log("groupe %-4s (e%d-e%d) : conforme" % (g, d, fn - 1))
            elif g in requis:
                self.log("groupe %-4s (e%d-e%d) : DIFFERENT (%s), requis pour %s" % (g, d, fn - 1, m, ",".join(self.jeux)), "!! ")
                ok = False
            else:
                self.log("groupe %-4s (e%d-e%d) : different, inutilise pour ces jeux" % (g, d, fn - 1))
        if not ok:
            if not self.a.iso_differente:
                raise Echec("ISO differente de la reference (autre version, ISO modifiee ou corrompue). Il faut "
                            "l'ISO USA d'origine de Street Fighter Alpha Anthology (SLUS-21317). --iso-differente "
                            "force la suite (resultats non garantis).")
            self.log("ISO differente de la reference : suite forcee (--iso-differente)", "!! ")
        return [self.xdata]

    def e_afs(self):
        os.makedirs(self.ext, exist_ok=True)
        spec = dict(cwd=self.ext, sys_path=[self.O["extraction"]], argv=["extract_anthology.py"],
                    patchs=[["extract_anthology", "PATH", self.xdata], ["extract_anthology", "OUTDIR", self.ext]],
                    module="extract_anthology")
        self.lance("afs", spec, self.env())
        m = md5_octets(open(os.path.join(self.ext, "manifest.csv"), "rb").read().replace(b"\r\n", b"\n"))
        # (la variante « All Unlocked » change la taille de e203 : manifeste different, groupes utiles identiques)
        self.log("manifest.csv : %s %s" % (m, "conforme" if m == REF_MANIFESTE else
                 "different de celui de l'ISO d'origine (%s) : les groupes ont ete verifies a l'etape iso" % REF_MANIFESTE),
                 "   " if m == REF_MANIFESTE else "!! ")
        return [os.path.join(self.ext, f) for f in os.listdir(self.ext) if os.path.isfile(os.path.join(self.ext, f))]

    def modules_voulus(self):
        mods = {JEUX[j]["module"] for j in self.jeux}
        if "upper" in self.jeux or "hyper" in self.jeux: mods.add("ro3")   # MAX_DEMO Upper relit ro3 ; banques communes
        if not self.a.sans_flux: mods.add("ro9")                            # table du lecteur de flux (= ro3 = ro5)
        return sorted(mods)

    def e_module(self, m):
        os.makedirs(self.dec, exist_ok=True)
        code = ("import os\nfrom mwo3_codec import decompress\n"
                "d = decompress(open(os.path.join(%r, %r + '_usa_prog68k.mwo3'), 'rb').read())\n"
                "open(os.path.join(%r, %r + '_usa_prog68k.bin'), 'wb').write(d)\n"
                "print(%r, len(d))\n") % (self.ext, m, self.dec, m, m)
        self.lance("module_" + m, dict(cwd=self.dec, sys_path=[self.O["mwo3"]], argv=["mwo3"], code=code), self.env())
        p = os.path.join(self.dec, m + "_usa_prog68k.bin"); h = md5_fichier(p)
        self.log("module %s : md5 %s %s" % (m, h, "conforme" if h == REF_MODULES[m] else "DIFFERENT"),
                 "   " if h == REF_MODULES[m] else "!! ")
        if h != REF_MODULES[m] and not self.a.iso_differente: raise Echec("module %s different" % m)
        return [p]

    def e_arcade(self):
        """ROM graphique CPS2 de SFA3 (banques.py : codes des tuiles = indices dans cette ROM ; archives FBNeo).
        Sans --arcade : reconstruite depuis l'ISO (rom_iso.py, HANDOFF §45). Avec --arcade : celle de l'utilisateur."""
        os.makedirs(self.arcade, exist_ok=True)
        if not self.a.arcade:
            return self.e_arcade_iso()
        trouve = {}
        # noms acceptes : sz3.13m (MAME ancien, FBNeo) ou sz3.13 (sets MAME recents) ; le md5 est controle ensuite
        alias = lambda n: (n, n[:-1]) if n.endswith("m") else (n,)
        for src in (self.a.arcade or []):
            if os.path.isdir(src):
                for n in REF_ARCADE_GFX:
                    for a in alias(n):
                        p = os.path.join(src, a)
                        if n not in trouve and os.path.exists(p): trouve[n] = open(p, "rb").read()
            elif zipfile.is_zipfile(src):
                with zipfile.ZipFile(src) as z:
                    noms = {os.path.basename(i.filename).lower(): i for i in z.infolist()}
                    for n in REF_ARCADE_GFX:
                        for a in alias(n):
                            if n not in trouve and a in noms: trouve[n] = z.read(noms[a])
        manque = [n for n in REF_ARCADE_GFX if n not in trouve and not os.path.exists(os.path.join(self.arcade, n))]
        if manque:
            raise Echec("ROM graphique d'arcade de SFA3 manquante (%s). Donner --arcade <sfa3.zip ou dossier> "
                        "(fichiers sz3.13m a sz3.20m de sa propre copie de Street Fighter Alpha 3)." % ", ".join(manque))
        out = []
        for n, md5 in REF_ARCADE_GFX.items():
            p = os.path.join(self.arcade, n)
            if n in trouve:
                if md5_octets(trouve[n]) != md5: raise Echec("%s : md5 %s, attendu %s" % (n, md5_octets(trouve[n]), md5))
                open(p, "wb").write(trouve[n])
            out.append(p)
        open(os.path.join(self.arcade, "phoenix.key"), "wb").write(PHOENIX_KEY)
        self.log("ROM graphique d'arcade : 8 fichiers conformes ; phoenix.key generee (20 x $FF)")
        return out + [os.path.join(self.arcade, "phoenix.key")]

    def e_arcade_iso(self):
        U = self.O["untranspile"]
        code = ("import sys, rom_iso\nT, st = rom_iso.reconstruit(%r, %r)\nmd5 = rom_iso.ecrit(T, %r)\n"
                "for n in rom_iso.FICHIERS: print(md5[n], n)\n") % (
                    self.xdata, os.path.join(self.ext, "manifest.csv"), self.arcade)
        spec = dict(cwd=self.arcade, sys_path=[ICI, U, os.path.dirname(U.rstrip("/"))], argv=["rom_iso.py"], code=code)
        self.lance("arcade", spec, self.env(), python=self.python_numpy())
        out = []
        for n, md5 in REF_ISO_GFX.items():
            p = os.path.join(self.arcade, n); h = md5_fichier(p); out.append(p)
            ref = REF_ARCADE_GFX[n]
            self.log("%s : %s %s" % (n, h, "= arcade" if h == ref else ("reconstruction conforme (quarts 0-1 : autre ordre "
                     "que l'arcade)" if h == md5 else "DIFFERENT de la reconstruction de reference")),
                     "!! " if h not in (md5, ref) else "   ")
        open(os.path.join(self.arcade, "phoenix.key"), "wb").write(PHOENIX_KEY)
        self.log("ROM graphique reconstruite depuis l'ISO (rom_iso.py) ; phoenix.key generee (20 x $FF)")
        return out + [os.path.join(self.arcade, "phoenix.key")]

    def e_son_sfa3(self):
        out = self.roms("sfa3"); os.makedirs(out, exist_ok=True)
        U = self.O["untranspile"]
        code = ("import os, gen_son\nz, q = gen_son.lire('ro3')\n"
                "for n, d in gen_son.decoupe(z, q).items():\n"
                "    open(os.path.join(%r, n), 'wb').write(d); print(n, len(d))\n") % out
        spec = dict(cwd=out, sys_path=[U], argv=["gen_son.py", "ro3", out], code=code,
                    patchs=[["gen_son", "XDATA", self.xdata], ["gen_son", "EXTRACT", self.ext + os.sep],
                            ["gen_son", "ARCADE", self.arcade + os.sep]])
        self.lance("son_sfa3", spec, self.env())
        res = []
        for n, md5 in REF_SON_SFA3.items():
            p = os.path.join(out, n); h = md5_fichier(p); res.append(p)
            self.log("%s : %s %s" % (n, h, "= arcade" if h == md5 else "DIFFERENT de l'arcade"), "   " if h == md5 else "!! ")
        return res

    def e_son_upper(self):
        out = os.path.join(self.W, "agent_son_ro5", "hybride", "roms_hybride"); os.makedirs(out, exist_ok=True)
        U = self.O["untranspile"]
        spec = dict(cwd=out, sys_path=[U, self.O["son_hybride"]], argv=["gen_hybride.py", out], module="gen_hybride",
                    patchs=[["gen_son", "XDATA", self.xdata], ["gen_son", "EXTRACT", self.ext + os.sep],
                            ["gen_son", "ARCADE", self.arcade + os.sep],
                            ["gen_hybride", "ARCADE", self.arcade + os.sep],
                            ["z80son", "X", self.ext + os.sep]])
        self.lance("son_upper", spec, self.env())
        res = []
        for n, md5 in REF_SON_UPPER.items():
            p = os.path.join(out, n); h = md5_fichier(p); res.append(p)
            self.log("%s : %s %s" % (n, h, "conforme" if h == md5 else "DIFFERENT de la reference du 2026-10-04"),
                     "   " if h == md5 else "!! ")
        return res

    def e_prog(self, jeu):
        J = JEUX[jeu]; W = self.travail(jeu); os.makedirs(W, exist_ok=True)
        U = self.O["untranspile"]
        patchs = self.patchs_communs(J["module"]); env = {}
        if jeu == "hyper" and self.redirection():
            # redirection des voix (SON-HYPER-ROM.md §13) : le traducteur lit le module ro9 CORRIGE (profils.EXTRACT ;
            # census garde le module d'origine, comme la livraison v151) et sert le bloc $E70000 (HSFA_SON_DONNEES)
            patchs.append(["profils", "EXTRACT", self.modules_son])
            env["HSFA_SON_DONNEES"] = os.path.join(self.modules_son, "son_donnees_ro9.bin")
        spec = dict(cwd=W, sys_path=[U, self.O["mwo3"]], argv=["mame_test.py"], module="mame_test",
                    patchs=patchs, neutraliser_listdir=os.path.join("work", "mame", "roms", "sfa3ud"))
        # MEMMODE=cps2 avant tout import de translate (census, remplace ci-dessus, l'importe avant mame_test)
        self.lance("prog_" + jeu, spec, self.env(MODULE=J["module"], TRAVAIL=W, XDATA=self.xdata, ANIM_CACHE=self.anims,
                                                 MEMMODE="cps2", **env))
        roms = self.roms(jeu)
        out = [os.path.join(roms, n) for n in PRG]
        out += [os.path.join(W, f) for f in sorted(os.listdir(W)) if f.startswith("ext_")]
        out += [os.path.join(W, f) for f in ("carte_image.txt", "chutes.json", "audit_exacts.txt") if os.path.exists(os.path.join(W, f))]
        self.log("%s : sz3ud.03c md5 %s" % (jeu, md5_fichier(out[0])))
        return out

    # ---- son d'Hyper : redirection des voix par version + table du rejeu (SON-HYPER-ROM.md §12-13) ----------------
    def table_rejeu_source(self):
        """table du rejeu (traces QSound de SFA1 / SFA2, hors depot) : --rejeu-table, sinon
        tools/son-hyper/rejeu/hsfa_rejeu_table.txt si elle est la ; None sinon"""
        if self.a.rejeu_table: return os.path.abspath(self.a.rejeu_table)
        p = os.path.join(self.O["son_hyper"], "rejeu", "hsfa_rejeu_table.txt")
        return p if os.path.exists(p) else None

    def redirection(self):
        """redirection des voix d'Hyper : seulement avec la table du rejeu (sans elle, les codes $2000+ / $4000+
        n'auraient pas de son : Hyper garde alors les voix SFA3) ; --sans-redirection la coupe"""
        return not self.a.sans_redirection and self.table_rejeu_source() is not None

    def e_son_hyper(self):
        """module ro9 corrige + bloc de donnees $E70000 (gen_redirection.py, depuis le module extrait de l'ISO) ;
        table du rejeu completee de la section des cris par version"""
        red = os.path.join(self.cache, "son_hyper"); os.makedirs(red, exist_ok=True)
        os.makedirs(self.modules_son, exist_ok=True)
        src = self.table_rejeu_source()
        argv = ["gen_redirection.py", "--module", os.path.join(self.dec, "ro9_usa_prog68k.bin"), "--sortie", red,
                "--voix-arcade", "non",          # = livraison v151 : le paquet applique ensuite voix_arcade.tsv
                "--ids", os.path.join(self.O["son_hyper"], "ids_102.tsv"),
                "--correspondance", os.path.join(self.O["son_hyper"], "correspondance.tsv")]
        table = os.path.join(red, "hsfa_rejeu_table.txt")
        if os.path.exists(table): os.remove(table)
        if src: argv += ["--table-rejeu", src, "--table-sortie", table]
        self.lance("son_hyper", dict(cwd=red, sys_path=[self.O["son_hyper"]], argv=argv,
                                     code="import gen_redirection\ngen_redirection.main(%r)\n" % argv[1:]), self.env())
        out = []
        for n, f in (("ro9_usa_prog68k.bin", "ro9_usa_prog68k_son.bin"), ("son_donnees_ro9.bin", "donnees.bin")):
            p = os.path.join(self.modules_son, n)
            shutil.copyfile(os.path.join(red, f), p); h = md5_fichier(p); out.append(p)
            self.log("%s : %s %s" % (n, h, "conforme (v151)" if h == REF_SON_HYPER[n] else "DIFFERENT de la v151"),
                     "   " if h == REF_SON_HYPER[n] else "!! ")
        if src:
            self.log("table du rejeu : %s + cris par version -> %s (%d o)" % (src, os.path.relpath(table, self.S),
                                                                          os.path.getsize(table)))
            out.append(table)
        if self.redirection():
            self.log("redirection des voix d'Hyper : active (module corrige + bloc $E70000 + table du rejeu)")
        else:
            self.log("redirection des voix d'Hyper : INACTIVE (%s) : Hyper garde les voix SFA3"
                     % ("--sans-redirection" if self.a.sans_redirection else "pas de table du rejeu"), "!! ")
        return out

    def patchs_banques(self, jeu):
        W = self.travail(jeu); B = os.path.join(W, "banques")
        return self.patchs_communs(JEUX[jeu]["module"]) + [
            ["census", "RO3", os.path.join(self.dec, JEUX[jeu]["module"] + "_usa_prog68k.bin")],
            ["banques", "MANIF", os.path.join(self.ext, "manifest.csv")],
            ["banques", "XDATA", self.xdata],
            ["banques", "ROMDIR", self.arcade],
            ["banques", "OUT", B], ["banques", "MOD.out", B]]

    def plans_fenetre(self):
        """tables plan1/plan2 : preferer les codes de la fenetre que le banc / FBNeo honorent (banques.py,
        HSFA_PLANS_FENETRE). auto = oui pour la ROM reconstruite depuis l'ISO, non avec --arcade (tables = banc)."""
        v = self.a.plans_fenetre
        return (not self.a.arcade) if v == "auto" else v == "oui"

    def e_gfx(self, jeu):
        J = JEUX[jeu]; W = self.travail(jeu); U = self.O["untranspile"]
        py = self.python_numpy()
        env = self.env(MODULE=J["module"], TRAVAIL=W, XDATA=self.xdata, ANIM_CACHE=self.anims)
        if self.plans_fenetre():                  # banques.py plans : codes dans la fenetre du plan d'abord (BUILD.md)
            env["HSFA_PLANS_FENETRE"] = "1"
        sp = [U, self.O["mwo3"]]
        for d in ("banques", "banques_hx"):        # dossiers propres (aucune table d'une version precedente) ; hsfa_gfx.py
            if os.path.isdir(os.path.join(W, d)): shutil.rmtree(os.path.join(W, d))   # est idempotent depuis le 2026-10-10
        for args in (["tout"], [str(J["b32"])], ["plans"]):
            self.lance("gfx_" + jeu, dict(cwd=W, sys_path=sp, argv=["banques.py"] + args, module="banques",
                                          patchs=self.patchs_banques(jeu)), env, python=py)
        if jeu in ("upper", "hyper"):
            env2 = dict(env)
            if jeu == "hyper":                      # ROM etendue d'Upper reprise en tete (HANDOFF §133)
                env2["HSFA_GFX_BASE"] = os.path.join(self.travail("upper"), "hsfa_gfx.bin")
            self.lance("gfx_" + jeu, dict(cwd=W, sys_path=sp, argv=["hsfa_gfx.py"], module="hsfa_gfx",
                                          patchs=self.patchs_banques(jeu)), env2, python=py)
            self.lance("gfx_" + jeu, dict(cwd=W, sys_path=sp, argv=["hsfa_plans.py"], module="hsfa_plans",
                                          patchs=self.patchs_banques(jeu)), env, python=py)
        out = []
        for d in ("banques", "banques_hx"):
            p = os.path.join(W, d)
            if os.path.isdir(p): out += [os.path.join(p, f) for f in sorted(os.listdir(p))]
        out += [os.path.join(W, f) for f in ("hsfa_gfx.bin", "hsfa_plans.bin") if os.path.exists(os.path.join(W, f))]
        return out

    def e_paquet(self, jeu):
        J = JEUX[jeu]
        roms = self.roms(jeu)
        for n in list(REF_ARCADE_GFX) + ["phoenix.key"]:      # ROM graphique + cle a cote du programme traduit
            d = os.path.join(roms, n)
            if os.path.lexists(d): os.remove(d)
            shutil.copyfile(os.path.join(self.arcade, n), d)
        dest = os.path.join(self.S, "archives"); os.makedirs(dest, exist_ok=True)
        spec = dict(cwd=dest, sys_path=[self.O["paquet"]], argv=["paquet_fbneo.py", J["paquet"]],
                    code="import paquet_fbneo\npaquet_fbneo.construit(%r)\n" % J["paquet"])
        # archives deterministes (SOURCE_DATE_EPOCH : dates fixes) et liste explicite des fichiers du jeu (HSFA_STRICT)
        self.lance("paquet_" + jeu, spec, self.env(HSFA_WORK=self.W, HSFA_SORTIE=dest, HSFA_STRICT="1",
                                                    SOURCE_DATE_EPOCH=self.a.date_source, **self.env_paquet()), nice=False)
        return [os.path.join(dest, J["zip"] + ".zip")]

    def env_paquet(self):
        """membres lus sur place par le coeur (paquet_fbneo.py) : flux musique (Upper, Hyper ; Ogg Vorbis par defaut,
        decision D6), rejeu SFA1 / SFA2 (Hyper, si --rejeu-table) ; sources = l'ISO de l'utilisateur"""
        e = dict(HSFA_XDATA=self.xdata, HSFA_OGG_CACHE=os.path.join(self.cache, "flux_ogg"),
                 HSFA_FLUX_FORMAT=self.a.flux_format)
        if self.a.sans_flux:
            e["HSFA_SANS_FLUX"] = "1"
        else:
            src = os.path.abspath(self.a.anthology)
            e["HSFA_YDATA"] = os.path.join(src, "Y_DATA.BIN") if os.path.isdir(src) else src
            e["HSFA_FLUX_TABLE"] = os.path.join(self.O["flux"], "hsfa_flux_table.txt")
            e["HSFA_CODES_HYPER"] = os.path.join(self.O["flux"], "codes_musique_hyper.txt")
        table = os.path.join(self.cache, "son_hyper", "hsfa_rejeu_table.txt")
        if self.redirection() and os.path.exists(table):
            e["HSFA_REJEU_TABLE"] = table       # table du rejeu completee (e_son_hyper)
        else:
            e["HSFA_SANS_REJEU"] = "1"          # sans table : archive sans rejeu (sons SFA3)
        return e

    def e_flux(self):
        """table code son -> flux ADX de Y_DATA pour le lecteur de flux du coeur FBNeo HSFA (dossier systeme de
        RetroArch : fbneo/hsfa/) ; la musique elle-meme reste dans l'ISO de l'utilisateur (ydata.txt -> ISO)."""
        out = os.path.join(self.S, "systeme", "fbneo", "hsfa"); os.makedirs(out, exist_ok=True)
        table = os.path.join(out, "hsfa_flux_table.txt")
        spec = dict(cwd=out, sys_path=[self.O["flux"], self.O["son_table"]], module="gen_table_flux",
                    argv=["gen_table_flux.py", "--module", "ro9", "--toc", "", "-o", table],
                    patchs=[["table_son", "DEC", os.path.join(self.dec, "%s_usa_prog68k.bin")],
                            ["gen_table_flux", "SON", self.O["son_table"]]])
        self.lance("flux", spec, self.env())
        open(os.path.join(out, "ydata.txt"), "w").write(os.path.abspath(self.a.anthology) + "\n")
        ref = os.path.join(self.O["flux"], "hsfa_flux_table.txt")
        if os.path.exists(ref):        # comparaison hors commentaires (durees lues dans Y_DATA par l'outil d'origine)
            code = lambda p: [l.split("#")[0].strip() for l in open(p) if l.strip() and not l.startswith("#")]
            a, b = code(table), code(ref)
            self.log("table de flux : %d codes, %s" % (len(a), "identique a la reference (hors commentaires)" if a == b
                     else "DIFFERENTE de %s" % ref), "   " if a == b else "!! ")
        return [table]

    def e_max(self):
        if not self.a.max:
            self.log("pas d'ISO PSP (--max) : etape MAX ignoree"); return []
        raise Echec("squelette : persos MAX (ISO PSP SFA3 MAX, ULES00235/ULUS10062) non implementes")

    def e_empreintes(self):
        lignes = ["# Empreintes des ROM et archives produites par hsfa_build.py (%s)" % time.strftime("%Y-%m-%d %H:%M:%S"),
                  "# md5  taille  fichier"]
        cibles = []
        for j in self.jeux:
            r = self.roms(j)
            if os.path.isdir(r): cibles += [os.path.join(r, f) for f in sorted(os.listdir(r))]
            W = self.travail(j)
            if os.path.isdir(W):
                cibles += [os.path.join(W, f) for f in sorted(os.listdir(W)) if f.startswith("ext_") or f.startswith("hsfa_")]
        sh = os.path.join(self.W, "agent_son_ro5", "hybride", "roms_hybride")
        if "upper" in self.jeux and os.path.isdir(sh): cibles += [os.path.join(sh, f) for f in sorted(os.listdir(sh))]
        ar = os.path.join(self.S, "archives")
        cibles += [os.path.join(ar, f) for f in sorted(os.listdir(ar)) if f.endswith(".zip")]
        for p in cibles:
            if os.path.isfile(p):
                lignes.append("%s  %9d  %s" % (md5_fichier(p), os.path.getsize(p), os.path.relpath(p, self.S)))
        for p in cibles:                                  # contenu des archives (independant de la date du zip)
            if p.endswith(".zip") and os.path.isfile(p):
                with zipfile.ZipFile(p) as z:
                    for i in z.infolist():
                        if i.filename == "hsfa_info.txt": continue
                        lignes.append("%s  %9d  %s:%s" % (md5_octets(z.read(i)), i.file_size, os.path.relpath(p, self.S), i.filename))
        chem = os.path.join(self.S, "EMPREINTES.txt")
        open(chem, "w").write("\n".join(lignes) + "\n")
        self.log("empreintes : %d fichiers -> EMPREINTES.txt" % (len(lignes) - 2))
        if self.a.comparer:
            self.compare(self.a.comparer)
        return [chem]

    def compare(self, banc):
        """compare les ROM programme produites a celles d'un banc (<workspace>/work)"""
        for j in self.jeux:
            a = self.roms(j); b = os.path.join(banc, JEUX[j]["travail"], JEUX[j]["roms"], "sfa3ud")
            if not os.path.isdir(a) or not os.path.isdir(b): continue
            diff = [n for n in PRG if os.path.exists(os.path.join(a, n)) and
                    md5_fichier(os.path.join(a, n)) != md5_fichier(os.path.join(b, n))]
            self.log("comparaison %s avec %s : %s" % (j, b, "IDENTIQUES (8/8)" if not diff else "differences : " + ", ".join(diff)),
                     "   " if not diff else "!! ")

    # ---- table des etapes -------------------------------------------------------------------------------------------
    def etapes(self):
        U = self.O["untranspile"]; X = self.O["extraction"]; M = self.O["mwo3"]
        E = [("iso", [], [], self.e_iso, "verifier l'ISO (empreintes) et extraire X_DATA.BIN"),
             ("afs", ["iso"], [os.path.join(X, "extract_anthology.py")], self.e_afs,
              "carte AFS de X_DATA + extraction des entrees (extract_anthology.py)"),
             ] + [("module_" + m, ["afs"], [os.path.join(M, "mwo3_codec.py")], lambda m=m: self.e_module(m),
                   "decompresser le module %s (MWo3, mwo3_codec.py)" % m) for m in self.modules_voulus()]
        if "sfa3" in self.jeux:
            E.append(("son_sfa3", ["afs"], [os.path.join(U, "gen_son.py")], self.e_son_sfa3,
                      "ROM son de SFA3 depuis X_DATA (gen_son.py ro3)"))
        if "upper" in self.jeux or "hyper" in self.jeux:          # (Hyper reprend la ROM son hybride d'Upper)
            E.append(("son_upper", ["afs"], [os.path.join(U, "gen_son.py"), self.O["son_hybride"]], self.e_son_upper,
                      "ROM son hybride d'Upper (gen_hybride.py)"))
        if "hyper" in self.jeux:
            sh = self.O["son_hyper"]
            E.append(("son_hyper", ["module_ro9"], [os.path.join(sh, f) for f in ("gen_redirection.py", "gen_rejeu.py",
                      "ids_102.tsv", "correspondance.tsv")] + ([self.table_rejeu_source()] if self.table_rejeu_source() else []),
                      self.e_son_hyper, "redirection des voix d'Hyper : module ro9 corrige, bloc $E70000, table du rejeu "
                      "(gen_redirection.py)"))
        for j in self.jeux:
            E.append(("prog_" + j, ["module_" + JEUX[j]["module"], "afs"] + (["son_hyper"] if j == "hyper" else []),
                      [U, M], lambda j=j: self.e_prog(j),
                      "programme 68K traduit de %s (mame_test.py, MODULE=%s)" % (j, JEUX[j]["module"])))
        # (place ici : son et programmes se construisent meme sans la ROM d'arcade)
        if self.a.arcade:
            E.append(("arcade", [], [], self.e_arcade, "ROM graphique d'arcade de SFA3 (--arcade) + phoenix.key"))
        else:
            E.append(("arcade", ["afs"], [os.path.join(ICI, "rom_iso.py"), os.path.join(U, "anthgfx.py"), os.path.join(U, "cps2rom.py"),
                                       os.path.join(os.path.dirname(U.rstrip("/")), "lz148778.py")],
                      self.e_arcade, "ROM graphique de SFA3 reconstruite depuis l'ISO (rom_iso.py) + phoenix.key"))
        for j in self.jeux:
            deps = ["module_" + JEUX[j]["module"], "afs", "arcade"] + (["gfx_upper"] if j == "hyper" else [])
            E.append(("gfx_" + j, deps, [U, M, os.path.dirname(U.rstrip("/"))], lambda j=j: self.e_gfx(j),
                      "tables de banques" + (" + ROM etendue + plans (hsfa_gfx/hsfa_plans)" if j != "sfa3" else "") + " de " + j))
        for j in self.jeux:
            son = {"sfa3": ["son_sfa3"], "upper": ["son_upper"], "hyper": ["son_upper", "son_hyper"]}.get(j, [])
            E.append(("paquet_" + j, ["prog_" + j, "gfx_" + j, "arcade"] + son, [self.O["paquet"]],
                      lambda j=j: self.e_paquet(j), "archive FBNeo %s.zip (paquet_fbneo.py)" % (JEUX[j]["zip"] or j)))
        if not self.a.sans_flux:
            E.append(("flux", ["module_ro9"], [self.O["flux"], self.O["son_table"]], self.e_flux,
                      "table du lecteur de flux ADX (gen_table_flux.py) -> systeme/fbneo/hsfa/"))
        E.append(("max", [], [], self.e_max, "persos MAX depuis l'ISO PSP (squelette, --max)"))
        E.append(("empreintes", [], [], self.e_empreintes, "empreintes de toutes les ROM et archives produites"))
        return E

    def liste(self):
        for nom, deps, _o, _f, desc in self.etapes():
            e = self.etat.get(nom, {})
            st = "faite %s" % e.get("date", "") if e.get("fait") else ("ECHEC : " + e.get("erreur", "")[:80] if e.get("erreur") else "a faire")
            print("%-14s %-60s [%s]" % (nom, desc, st))

    def run(self):
        E = self.etapes(); noms = [e[0] for e in E]
        debut = noms.index(self.a.etape) if self.a.etape else 0
        if self.a.etape and self.a.etape not in noms: raise Echec("etape inconnue : %s (voir --liste)" % self.a.etape)
        fin = noms.index(self.a.jusqua) + 1 if self.a.jusqua else len(E)
        self.log("=== hsfa_build : jeux %s, sortie %s" % (",".join(self.jeux), self.S), "")
        for k, (nom, deps, outils, f, desc) in enumerate(E[:fin]):
            if k < debut:
                if not self.etat.get(nom, {}).get("fait"):
                    raise Echec("--etape %s : l'etape anterieure %s n'est pas faite" % (self.a.etape, nom))
                continue
            params = dict(iso=os.path.abspath(self.a.anthology), outils=self.O)      # seulement ce qui change la sortie
            if nom == "max": params["max"] = self.a.max and os.path.abspath(self.a.max)
            if nom.startswith("paquet_"):
                params.update(date_source=self.a.date_source, flux=self.a.flux_format, sans_flux=self.a.sans_flux,
                              rejeu=self.table_rejeu_source(), redirection=self.redirection())
            if nom in ("son_hyper", "prog_hyper"):
                params.update(rejeu=self.table_rejeu_source(), redirection=self.redirection())
            if nom == "arcade": params["source"] = "arcade" if self.a.arcade else "iso"
            if nom.startswith("gfx_"): params["plans_fenetre"] = self.plans_fenetre()
            if nom == "iso": params["groupes"] = sorted({g for j in self.jeux for g in GROUPES_REQUIS[j]})
            cle = self.cle(nom, [d for d in deps if d in noms], outils, params)
            e = self.etat.get(nom, {})
            force = self.a.force or (self.a.etape and k == debut) or nom == "empreintes"
            if not force and e.get("fait") and e.get("cle") == cle and self.sorties_intactes(e):
                self.log("[%s] a jour, sautee" % nom, ">> "); continue
            self.log("[%s] %s" % (nom, desc), ">> ")
            t0 = time.time()
            try:
                sorties = f()
            except Echec as x:
                self.etat[nom] = dict(fait=False, erreur=str(x), date=time.strftime("%Y-%m-%d %H:%M:%S"))
                self.sauve_etat()
                self.log("[%s] ECHEC : %s" % (nom, x), "!! ")
                if nom == "max":
                    continue                          # squelettes : on continue
                return 1
            self.etat[nom] = dict(fait=True, cle=cle, date=time.strftime("%Y-%m-%d %H:%M:%S"),
                                  duree=round(time.time() - t0), sorties=self.note_sorties(sorties))
            self.sauve_etat()
            self.log("[%s] faite (%.0f s, %d sorties)" % (nom, time.time() - t0, len(sorties)), "ok ")
        self.log("=== termine", "")
        return 0


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "_lancer":
        return _lancer(sys.argv[2])
    ap = argparse.ArgumentParser(description="Construit les jeux HSFA a partir de l'ISO de l'utilisateur.")
    ap.add_argument("--anthology", required=True, help="ISO PS2 de Street Fighter Alpha Anthology (USA, SLUS-21317)")
    ap.add_argument("--max", help="ISO PSP de Street Fighter Alpha 3 MAX (persos MAX : etape non implementee)")
    ap.add_argument("--sortie", required=True, help="dossier de sortie (cache, travail, archives, journal)")
    ap.add_argument("--jeux", default="sfa3,upper,hyper", help="sfa3,upper,hyper (defaut : les trois)")
    ap.add_argument("--arcade", action="append", help="(facultatif) ROM d'arcade de SFA3 (sfa3.zip ou dossier) : sz3.13m-20m ; "
                    "sans elle, la ROM graphique est reconstruite depuis l'ISO")
    ap.add_argument("--etape", help="reprendre a cette etape (les precedentes doivent etre faites)")
    ap.add_argument("--jusqua", help="s'arreter apres cette etape")
    ap.add_argument("--force", action="store_true", help="refaire toutes les etapes")
    ap.add_argument("--liste", action="store_true", help="lister les etapes et leur etat")
    ap.add_argument("--comparer", help="dossier <workspace>/work dont comparer les ROM programme (empreintes)")
    ap.add_argument("--iso-differente", action="store_true", help="continuer meme si les empreintes different")
    ap.add_argument("--sans-flux", action="store_true", help="ne pas produire la table du lecteur de flux ni mettre "
                    "les flux musique dans les archives d'Upper et d'Hyper")
    ap.add_argument("--flux-format", choices=("ogg", "adx"), default="ogg",
                    help="flux musique des archives : ogg (defaut, decision D6 ; ffmpeg avec libvorbis, gcc, g++) ou adx")
    ap.add_argument("--rejeu-table", help="(Hyper) hsfa_rejeu_table.txt : rejeu QSound des sons SFA1 / SFA2 (defaut : "
                    "tools/son-hyper/rejeu/hsfa_rejeu_table.txt si presente). Avec elle : redirection des voix (programme "
                    "= v151) et rejeu ; sans elle : Hyper garde les voix SFA3, archive sans rejeu")
    ap.add_argument("--sans-redirection", action="store_true", help="(Hyper) ni redirection des voix ni rejeu, meme "
                    "avec la table")
    ap.add_argument("--date-source", default=os.environ.get("SOURCE_DATE_EPOCH") or "315532800",
                    help="date fixe des archives (secondes Unix ; defaut : $SOURCE_DATE_EPOCH, sinon 1980-01-01) : zips "
                         "identiques a l'octet d'une construction a l'autre")
    ap.add_argument("--plans-fenetre", choices=("auto", "oui", "non"), default="auto",
                    help="tables de plans : preferer les codes de la fenetre du plan (defaut auto : oui sans --arcade, "
                         "non avec --arcade, pour des tables identiques a celles du banc)")
    ap.add_argument("--python-numpy", help="interpreteur Python avec numpy (etapes graphiques)")
    for k in OUTILS_DEFAUT:
        ap.add_argument("--outils-" + k.replace("_", "-"), dest="outils_" + k, help="dossier des outils : " + k)
    a = ap.parse_args()
    try:
        c = Construction(a)
        if a.liste: c.liste(); return 0
        return c.run()
    except Echec as x:
        print("ERREUR : %s" % x, file=sys.stderr); return 1

if __name__ == "__main__":
    sys.exit(main())
