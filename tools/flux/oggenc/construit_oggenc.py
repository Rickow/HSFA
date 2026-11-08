#!/usr/bin/env python3
"""construit_oggenc.py -- fabrique hsfa_oggenc (PCM -> Ogg Vorbis, memes octets sur tous les systemes).

Sources officielles, verifiees par SHA-256 (SOURCES ci-dessous) : libogg 1.3.6 et libvorbis 1.3.7 (xiph.org,
BSD-3), musl 1.1.21 (musl.libc.org, MIT : 15 fichiers de fonctions mathematiques fdlibm). Rien d'autre que le compilateur C.
Portabilite (voir hsfa_portable.h) :
  - IEEE strict : -fno-fast-math -ffp-contract=off (pas de FMA implicite, en particulier sur ARM) ;
  - sin, cos, exp, log, pow, atan, acos, floor, ceil, rint, ldexp et qsort = une seule implementation, compilee ici ;
  - libvorbis os.h : vorbis_ftoi generique (floor(f+.5)) partout, au lieu de l'instruction SSE2 (arrondi pair) sur
    x86_64 et de floor(f+.5) ailleurs ; pas de rint(x) = floor(x+.5) propre a Windows.
Usage :
  construit_oggenc.py --sources DIR [--telecharge] [--sortie FICHIER] [--cc "CC ..."] [--wasm WASI_SDK] [--travail DIR]
  construit_oggenc.py --verifie EXE
  --cc   : compilateur et options de cible (defaut : $CC, sinon cc) ; ex. "zig cc -target aarch64-linux-musl",
           "x86_64-w64-mingw32-gcc", "clang -arch arm64" ;
  --wasm : chemin de wasi-sdk : module WebAssembly (wasm32-wasi), le meme fichier partout.
Le programme verifie a la fin son signal d'essai (--signal) contre l'empreinte de reference SIGNAL_MD5 quand il peut
s'executer sur la machine de construction (sinon : a verifier sur la machine cible, `hsfa_oggenc --signal x.ogg`).
"""
import argparse, hashlib, io, os, shlex, shutil, subprocess, sys, tarfile, tempfile, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
SOURCES = {   # nom : (url officielle, sha256)
    "libogg-1.3.6.tar.xz": ("https://downloads.xiph.org/releases/ogg/libogg-1.3.6.tar.xz",
                            "5c8253428e181840cd20d41f3ca16557a9cc04bad4a3d04cce84808677fa1061"),
    "libvorbis-1.3.7.tar.xz": ("https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.xz",
                               "b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b"),
    "musl-1.1.21.tar.gz": ("https://musl.libc.org/releases/musl-1.1.21.tar.gz",
                           "c742b66f6f49c9e5f52f64d8b79fecb5a0f6e0203fca176c70ca20f6be285f44"),
}
VORBIS = ["analysis", "bitrate", "block", "codebook", "envelope", "floor0", "floor1", "info", "lookup", "lpc", "lsp",
          "mapping0", "mdct", "psy", "registry", "res0", "sharedbook", "smallft", "synthesis", "vorbisenc", "window"]
OGG = ["bitwise", "framing"]
MUSL = ["sin", "cos", "__sin", "__cos", "__rem_pio2", "__rem_pio2_large", "exp", "log", "pow", "atan", "acos",
        "floor", "ceil", "rint", "scalbn"]
DRAPEAUX = ["-O2", "-fno-fast-math", "-ffp-contract=off", "-fno-math-errno", "-w"]
SIGNAL_MD5 = "387bd0bdb0b85f2b7fad207e3459c45c"   # `hsfa_oggenc --signal` : identique sur 9 chaines (README)

# os.h de libvorbis 1.3.7 : (texte d'origine, remplacement) ; chaque texte doit apparaitre exactement une fois
RUSTINES_OS_H = [
    ("#if defined(__i386__) && defined(__GNUC__) && !defined(__BEOS__) && !defined(__SSE2_MATH__)",
     "#if 0 /* HSFA : vorbis_ftoi generique partout (hsfa_portable.h) */"),
    ("#if defined(_MSC_VER) && defined(_M_IX86) && !defined(_WIN32_WCE)",
     "#if 0 /* HSFA : vorbis_ftoi generique partout */"),
    ("#if (defined(_MSC_VER) && defined(_M_X64)) || (defined(__GNUC__) && defined (__SSE2_MATH__))",
     "#if 0 /* HSFA : vorbis_ftoi generique partout */"),
    ("#  include <malloc.h>\n#  define rint(x)   (floor((x)+0.5f))",
     "#  include <malloc.h>\n/* HSFA : rint du C (hsfa_rint), pas floor(x+.5) propre a Windows */"),
]


def sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def sources(dossier, telecharge=False):
    os.makedirs(dossier, exist_ok=True)
    for nom, (url, empreinte) in SOURCES.items():
        p = os.path.join(dossier, nom)
        if not os.path.exists(p):
            if not telecharge: sys.exit("source absente : %s (--telecharge, ou la deposer depuis %s)" % (p, url))
            print("telechargement", url)
            with urllib.request.urlopen(url, timeout=120) as r: d = r.read()
            open(p + ".part", "wb").write(d); os.replace(p + ".part", p)
        if sha256(p) != empreinte: sys.exit("%s : SHA-256 %s au lieu de %s" % (p, sha256(p), empreinte))


def extrait(dossier, travail):
    """sources extraites dans travail/ ; os.h rustine ; renvoie les chemins des .c dans l'ordre de compilation"""
    for nom in SOURCES:
        with tarfile.open(os.path.join(dossier, nom)) as t:
            membres = [m for m in t.getmembers() if m.isfile() and ".." not in m.name.split("/")
                       and not m.name.startswith("/")]
            if "musl" in nom:
                membres = [m for m in membres if m.name.split("/")[-2:-1] == ["math"] and "/src/math/" in m.name
                           and m.name.count("/") == 3]
            for m in membres:
                d = os.path.join(travail, m.name)
                os.makedirs(os.path.dirname(d), exist_ok=True)
                with t.extractfile(m) as f, open(d, "wb") as g: g.write(f.read())
    V = os.path.join(travail, "libvorbis-1.3.7"); O = os.path.join(travail, "libogg-1.3.6")
    M = os.path.join(travail, "musl-1.1.21", "src", "math")
    p = os.path.join(V, "lib", "os.h"); t = open(p, encoding="latin-1").read()
    for a, b in RUSTINES_OS_H:
        if t.count(a) != 1: sys.exit("os.h : rustine inapplicable (%r)" % a[:50])
        t = t.replace(a, b)
    open(p, "w", encoding="latin-1", newline="\n").write(t)
    cs = [os.path.join(V, "lib", f + ".c") for f in VORBIS] + [os.path.join(O, "src", f + ".c") for f in OGG] + \
         [os.path.join(M, f + ".c") for f in MUSL] + [os.path.join(ICI, "shim", "ldexp.c"),
                                                      os.path.join(ICI, "hsfa_portable.c"),
                                                      os.path.join(ICI, "hsfa_oggenc.c")]
    inc = [os.path.join(ICI, "shim"), os.path.join(V, "include"), os.path.join(V, "lib"), os.path.join(O, "include")]
    # ogg/config_types.h : celui de shim/ (le configure de libogg n'est pas lance)
    os.makedirs(os.path.join(travail, "inc", "ogg"), exist_ok=True)
    shutil.copy(os.path.join(ICI, "shim", "config_types.h"), os.path.join(travail, "inc", "ogg", "config_types.h"))
    return cs, [os.path.join(travail, "inc")] + inc


def construit(dossier_sources, sortie, cc=None, wasm=None, travail=None, telecharge=False, drapeaux=None,
              liaison=None, verbeux=False):
    sources(dossier_sources, telecharge)
    garde = travail is not None
    travail = travail or tempfile.mkdtemp(prefix="hsfa_oggenc_")
    try:
        cs, inc = extrait(dossier_sources, travail)
        if wasm:
            wasm = os.path.abspath(wasm)
            cc = [os.path.join(wasm, "bin", "clang"), "--target=wasm32-wasip1",
                  "--sysroot=" + os.path.join(wasm, "share", "wasi-sysroot")]
        else:
            cc = shlex.split(cc or os.environ.get("CC") or "cc")
        fl = list(DRAPEAUX if drapeaux is None else drapeaux)
        base = ["-include", os.path.join(ICI, "hsfa_portable.h")] + sum((["-I", i] for i in inc), [])
        objs = []
        for i, c in enumerate(cs):
            o = os.path.join(travail, "o", "%02d_%s.o" % (i, os.path.basename(c)[:-2]))
            os.makedirs(os.path.dirname(o), exist_ok=True)
            cmd = cc + fl + base + ["-c", c, "-o", o]
            if verbeux: print(" ".join(cmd))
            subprocess.run(cmd, check=True)
            objs.append(o)
        if liaison is None:
            liaison = [] if wasm or "darwin" in " ".join(cc) or "macos" in " ".join(cc) or sys.platform == "darwin" \
                else ["-static"]
        os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True)
        subprocess.run(cc + fl + objs + ["-o", sortie] + liaison + ["-lm"], check=True)   # -lm : sqrt (IEEE exact) a -O0
    finally:
        if not garde: shutil.rmtree(travail, ignore_errors=True)
    return sortie


def verifie(exe, lanceur=()):
    """md5 du signal d'essai de exe (None s'il ne s'execute pas ici : autre systeme) ; Echec si different"""
    with tempfile.TemporaryDirectory() as d:
        o = os.path.join(d, "signal.ogg")
        try:
            r = subprocess.run(list(lanceur) + [exe, "--signal", o], capture_output=True)
        except OSError:
            return None
        if r.returncode or not os.path.exists(o): return None
        m = hashlib.md5(open(o, "rb").read()).hexdigest()
    if m != SIGNAL_MD5:
        raise RuntimeError("%s : signal d'essai %s au lieu de %s (encodeur NON portable : ne pas l'utiliser)"
                           % (exe, m, SIGNAL_MD5))
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources")
    ap.add_argument("--telecharge", action="store_true")
    ap.add_argument("--sortie", default="hsfa_oggenc" + (".exe" if os.name == "nt" else ""))
    ap.add_argument("--cc")
    ap.add_argument("--wasm")
    ap.add_argument("--travail")
    ap.add_argument("--drapeaux", help="remplace -O2 ... (essais : \"-O0 -fno-fast-math -ffp-contract=off\")")
    ap.add_argument("--liaison", help="options de liaison (defaut : -static sauf macOS / WASM)")
    ap.add_argument("--verifie", metavar="EXE", help="seulement verifier le signal d'essai d'un hsfa_oggenc")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    if not a.verifie and not a.sources: ap.error("--sources requis")
    if a.verifie:
        m = verifie(a.verifie)
        sys.exit("%s : ne s'execute pas ici" % a.verifie if m is None else print("signal d'essai %s : OK" % m))
    s = construit(a.sources, a.sortie, a.cc, a.wasm, a.travail, a.telecharge,
                  shlex.split(a.drapeaux) if a.drapeaux else None,
                  shlex.split(a.liaison) if a.liaison is not None else None, a.v)
    print("%s  %s" % (sha256(s), s))
    if not a.wasm:
        m = verifie(s)
        print("signal d'essai : " + ("OK (%s)" % m if m else "non verifie (autre systeme : `%s --signal x.ogg`)" % s))


if __name__ == "__main__":
    main()
