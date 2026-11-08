#!/usr/bin/env python3
"""natifs.py -- outils natifs embarques par le constructeur tout-en-un, pour UNE cible, depuis les sources officielles.

  hsfa_oggenc  tools/flux/oggenc (libvorbis 1.3.7, libogg 1.3.6, musl 1.1.21 : IEEE strict, memes Ogg partout)
  fluxtool     tools/flux/fluxtool.cpp + stb_vorbis (decodeur ADX exact et relecture des Ogg ; MIT / domaine public)
  libchdr      lecture des .chd (BSD-3 ; commit LIBCHDR_COMMIT de github.com/rtissera/libchdr), bibliotheque partagee

Compilateur : zig (ziglang.org, version et empreinte dans .github/workflows/constructeur.yml) pour toutes les cibles,
depuis Linux ; ou le compilateur du systeme (--cc gcc --cxx g++). Executables lies statiquement (sauf macOS).
Usage : natifs.py --cible linux-x86_64|linux-aarch64|windows-x86_64|macos-arm64|macos-x86_64|hote
                  --sortie BIN --sources DIR [--telecharge] [--libchdr DIR] [--zig ZIG | --cc CC --cxx CXX]
"""
import argparse, os, shlex, shutil, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.normpath(os.path.join(ICI, "..", ".."))
FLUX = os.path.join(DEPOT, "tools", "flux")
LIBCHDR_DEPOT = "https://github.com/rtissera/libchdr.git"
LIBCHDR_COMMIT = "47d794151b2b64f6aba60304e6480f4f5a2bc24b"
CIBLES = {   # nom : (cible zig des executables, cible zig de la bibliotheque, systeme)
    "linux-x86_64": ("x86_64-linux-musl", "x86_64-linux-gnu.2.28", "linux"),
    "linux-aarch64": ("aarch64-linux-musl", "aarch64-linux-gnu.2.28", "linux"),
    "windows-x86_64": ("x86_64-windows-gnu", "x86_64-windows-gnu", "windows"),
    "macos-arm64": ("aarch64-macos.11.0", "aarch64-macos.11.0", "macos"),
    "macos-x86_64": ("x86_64-macos.11.0", "x86_64-macos.11.0", "macos"),
}


def lance(cmd, **kw):
    print("  " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def libchdr_sources(dossier, telecharge):
    d = os.path.join(dossier, "libchdr")
    if not os.path.isdir(os.path.join(d, ".git")):
        if not telecharge: sys.exit("libchdr absent : %s (--telecharge ou --libchdr)" % d)
        lance(["git", "clone", "-q", LIBCHDR_DEPOT, d])
    lance(["git", "-C", d, "checkout", "-q", LIBCHDR_COMMIT])
    r = subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    if r.stdout.strip() != LIBCHDR_COMMIT: sys.exit("libchdr : commit %s" % r.stdout.strip())
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cible", required=True, choices=sorted(CIBLES) + ["hote"])
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--sources", required=True, help="archives officielles (hsfa_oggenc) et clone de libchdr")
    ap.add_argument("--telecharge", action="store_true")
    ap.add_argument("--libchdr", help="clone de libchdr deja present (sinon <sources>/libchdr)")
    ap.add_argument("--zig")
    ap.add_argument("--cc"); ap.add_argument("--cxx")
    a = ap.parse_args()
    out = os.path.abspath(a.sortie); os.makedirs(out, exist_ok=True)
    if a.cible == "hote":
        systeme = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")
        cc, cxx, cclib = shlex.split(a.cc or "cc"), shlex.split(a.cxx or "c++"), None
    else:
        exe_t, lib_t, systeme = CIBLES[a.cible]
        if a.zig:
            z = shlex.split(a.zig)
            cc, cxx, cclib = z + ["cc", "-target", exe_t], z + ["c++", "-target", exe_t], z + ["cc", "-target", lib_t]
        else:
            cc, cxx, cclib = shlex.split(a.cc or "cc"), shlex.split(a.cxx or "c++"), None
    cclib = cclib or cc
    x = ".exe" if systeme == "windows" else ""
    statique = [] if systeme == "macos" else ["-static"]

    # 1. hsfa_oggenc
    sys.path.insert(0, os.path.join(FLUX, "oggenc"))
    import construit_oggenc as C
    C.construit(a.sources, os.path.join(out, "hsfa_oggenc" + x), cc=" ".join(shlex.quote(c) for c in cc),
                telecharge=a.telecharge, liaison=statique + ([] if systeme == "macos" else ["-s"]))
    # 2. fluxtool (memes commandes que tools/flux/flux_ogg.py)
    with tempfile.TemporaryDirectory() as t:
        o = os.path.join(t, "stb_vorbis_impl.o")
        lance(cc + ["-O2", "-c", "-w", "-I", FLUX, "-o", o, os.path.join(FLUX, "tests", "stb_vorbis_impl.c")])
        lance(cxx + ["-O2", "-DHSFA_FLUX_VORBIS", "-I", FLUX, "-o", os.path.join(out, "fluxtool" + x),
                     os.path.join(FLUX, "fluxtool.cpp"), o] + statique + ([] if systeme == "macos" else ["-s"]))
    # 3. libchdr (construction « unity » : unity.c + le codec avhuff qu'il n'inclut pas ; sans cmake)
    L = os.path.abspath(a.libchdr) if a.libchdr else libchdr_sources(a.sources, a.telecharge)
    nom = {"windows": "chdr.dll", "macos": "libchdr.dylib"}.get(systeme, "libchdr.so")
    lance(cclib + ["-O2", "-shared", "-fPIC", "-w", "-DCHD_DLL", "-DCHD_DLL_EXPORTS", "-DWANT_SUBCODE=0",
                   "-DWANT_RAW_DATA_SECTOR=1", "-I", os.path.join(L, "include"),
                   "-I", os.path.join(L, "deps", "lzma-26.02", "include"), "-I", os.path.join(L, "deps", "miniz-3.1.2"),
                   "-I", os.path.join(L, "deps", "zstd-1.5.7"), "-o", os.path.join(out, nom),
                   os.path.join(L, "unity.c"), os.path.join(L, "src", "libchdr_codec_avhuff.c")]   # absent de unity.c
          + (["-lm", "-Wl,--no-undefined"] if systeme == "linux" else []))
    shutil.copy(os.path.join(L, "LICENSE.txt"), os.path.join(out, "LICENSE-libchdr.txt"))
    for f in os.listdir(out):                    # symboles de debogage et bibliotheque d'import (Windows) : inutiles
        if f.endswith((".pdb", ".lib", ".exp")): os.remove(os.path.join(out, f))
    print("natifs (%s) -> %s : %s" % (a.cible, out, " ".join(sorted(os.listdir(out)))))
    m = C.verifie(os.path.join(out, "hsfa_oggenc" + x))
    print("hsfa_oggenc --signal : " + ("OK %s" % m if m else "a verifier sur la cible"))


if __name__ == "__main__":
    main()
