#!/usr/bin/env python3
"""Encodage des flux musique ADX de Y_DATA.BIN en Ogg Vorbis pour le coeur FBNeo HSFA (docs/rapports/PLAN-VORBIS.md).

Chaine, pour chaque entree :
  1. decodage exact par fluxtool (hsfa_flux.h : le meme decodeur que le coeur) -> PCM 16 bits stereo, boucle ADX ;
  2. encodage hsfa_oggenc (oggenc/ : libvorbis 1.3.7 en IEEE strict, MEMES OCTETS sur tous les systemes ; qualite
     HSFA_OGG_QUALITE, defaut 2, ~96 kbit/s en stereo 48 kHz), commentaires LOOPSTART / LOOPEND (fin exclue, en
     echantillons), HSFA_ADX_MD5, HSFA_ENC ;
  3. controle : l'Ogg relu par fluxtool (stb_vorbis, comme le coeur) a le meme nombre d'echantillons et la meme boucle,
     une correlation de forme d'onde >= 0,90 et un niveau a +-0,5 dB du PCM ADX. Un echec garde l'ADX pour cette entree.
     Le controle attrape les erreurs (duree, boucle, decodage, decalage : correlation proche de 0, niveau) ; il ne juge
     pas la fidelite a l'oreille (reglage HSFA_OGG_QUALITE). Sur la vraie musique d'Hyper a q2, la correlation de forme
     d'onde va de 0,94 a 0,99 (2026-10-16) : un seuil a 0,99 refusait 125 flux sur 173.
Cache : <cache>/Y<entree>_<md5 ADX>_q<qualite>.ogg (un Ogg n'est refait que si l'ADX ou le reglage change).
Dependances : numpy ; g++ et gcc (fluxtool et hsfa_oggenc, compiles une fois dans le cache ; hsfa_oggenc depuis les
sources officielles de HSFA_OGGENC_SOURCES, voir oggenc/construit_oggenc.py --telecharge). Binaires preconstruits
(constructeur tout-en-un, tools/constructeur) : HSFA_FLUXTOOL, HSFA_OGGENC. Plus de ffmpeg (VERSION 3).

Usage direct (essai) : flux_ogg.py <Y_DATA.BIN ou ISO> <entree> [<entree> ...]   (cache : HSFA_OGG_CACHE ou /tmp)
Depuis paquet_fbneo.py : HSFA_FLUX_FORMAT=ogg.
"""
import hashlib, os, shutil, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

ICI = os.path.dirname(os.path.abspath(__file__))
VERSION = "3"                                   # a changer si la chaine change : invalide le cache
                                                # (2 : -fflags +bitexact, Ogg reproductibles a l'octet ;
                                                #  3 : hsfa_oggenc, memes octets sur tous les systemes)


def qualite():
    return os.environ.get("HSFA_OGG_QUALITE", "2")


def outil(cache):
    """chemin de fluxtool, compile si besoin (sources plus recentes que l'executable)"""
    if os.environ.get("HSFA_FLUXTOOL"):           # binaire preconstruit (constructeur tout-en-un) : ni gcc ni g++
        os.makedirs(cache, exist_ok=True)
        return os.environ["HSFA_FLUXTOOL"]
    exe = os.path.join(cache, "fluxtool")
    srcs = [os.path.join(ICI, f) for f in ("fluxtool.cpp", "hsfa_flux.h", "stb_vorbis.c",
                                         os.path.join("tests", "stb_vorbis_impl.c"))]
    if os.path.exists(exe) and os.path.getmtime(exe) >= max(os.path.getmtime(s) for s in srcs):
        return exe
    os.makedirs(cache, exist_ok=True)
    obj = os.path.join(cache, "stb_vorbis_impl.o")
    subprocess.run(["gcc", "-O2", "-c", "-w", "-I", ICI, "-o", obj, srcs[3]], check=True)
    subprocess.run(["g++", "-O2", "-DHSFA_FLUX_VORBIS", "-I", ICI, "-o", exe, srcs[0], obj], check=True)
    return exe


def encodeur(cache):
    """chemin de hsfa_oggenc : HSFA_OGGENC, sinon compile dans le cache (sources officielles de HSFA_OGGENC_SOURCES,
    defaut <cache>/sources_oggenc) ; refuse un encodeur dont le signal d'essai n'a pas l'empreinte de reference"""
    kit = os.path.join(ICI, "oggenc")
    if kit not in sys.path: sys.path.insert(0, kit)
    import construit_oggenc as C
    exe = os.environ.get("HSFA_OGGENC")
    if not exe:
        exe = os.path.join(cache, "hsfa_oggenc" + (".exe" if os.name == "nt" else ""))
        srcs = [os.path.join(r, f) for r, _, fs in os.walk(kit) for f in fs if f.endswith((".c", ".h", ".py"))]
        if not (os.path.exists(exe) and os.path.getmtime(exe) >= max(os.path.getmtime(s) for s in srcs)):
            sources = os.environ.get("HSFA_OGGENC_SOURCES") or os.path.join(cache, "sources_oggenc")
            if not all(os.path.exists(os.path.join(sources, n)) for n in C.SOURCES):
                raise RuntimeError("sources de hsfa_oggenc absentes de %s : python3 %s --sources %s --telecharge "
                                   "(ou --flux-format adx)" % (sources, os.path.join(kit, "construit_oggenc.py"),
                                                               sources))
            os.makedirs(cache, exist_ok=True)
            C.construit(sources, exe, cc=os.environ.get("CC") or "gcc")
    if C.verifie(exe) is None:
        raise RuntimeError("%s ne s'execute pas sur ce systeme" % exe)
    return exe


def pcm(exe, source, entree, sortie):
    r = subprocess.run([exe, "pcm", source, str(entree), sortie], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr.strip())
    freq, n, d, f = (int(x) for x in r.stdout.split())
    return freq, n, d, f


def _afs_un(chemin_ogg, sortie):
    """AFS d'une seule entree autour d'un fichier (pour relire un Ogg avec fluxtool)"""
    d = open(chemin_ogg, "rb").read()
    open(sortie, "wb").write(b"AFS\0" + struct.pack("<III", 1, 2048, len(d)) + bytes(2048 - 16) + d)


def controle(ref, test, nref):
    import numpy as np
    a = np.fromfile(ref, dtype="<i2").astype(np.float64)
    b = np.fromfile(test, dtype="<i2").astype(np.float64)
    if len(a) != len(b): return "longueur %d au lieu de %d" % (len(b) // 2, len(a) // 2)
    ea, eb = (a * a).sum(), (b * b).sum()
    if ea < 1e3 * len(a) / 1e6:                   # quasi silence : seul le niveau compte
        return None if eb <= 4 * ea + len(a) else "silence non respecte"
    cor = (a * b).sum() / np.sqrt(ea * eb)
    db = 10 * np.log10(eb / ea)
    if cor < 0.90: return "correlation %.4f" % cor
    if abs(db) > 0.5: return "niveau %+.2f dB" % db
    return None


def encode(source, entree, md5_adx, cache, exe=None, enc=None):
    """chemin de l'Ogg de l'entree (cache), ou None si l'entree doit rester en ADX ; et un message"""
    q = qualite()
    dest = os.path.join(cache, "Y%d_%s_q%s_v%s.ogg" % (entree, md5_adx[:12], q, VERSION))
    if os.path.exists(dest): return dest, "cache"
    exe = exe or outil(cache)
    enc = enc or encodeur(cache)
    with tempfile.TemporaryDirectory(dir=cache) as t:
        ref = os.path.join(t, "ref.raw")
        try:
            freq, n, d, f = pcm(exe, source, entree, ref)
        except RuntimeError as e:
            return None, "ADX non decode (%s) : garde en ADX" % e
        meta = ["HSFA_ADX_MD5=" + md5_adx, "HSFA_ENC=libvorbis q%s v%s" % (q, VERSION)]
        if f > d: meta += ["LOOPSTART=%d" % d, "LOOPEND=%d" % f]
        ogg = os.path.join(t, "e.ogg")
        # hsfa_oggenc : numero de serie fixe, IEEE strict -> meme Ogg a chaque construction et sur tout systeme
        r = subprocess.run([enc, ref, ogg, str(freq), q] + meta, capture_output=True, text=True)
        if r.returncode: return None, "hsfa_oggenc : %s : garde en ADX" % r.stderr.strip()
        afs = os.path.join(t, "e.afs"); _afs_un(ogg, afs)
        test = os.path.join(t, "test.raw")
        try:
            f2, n2, d2, e2 = pcm(exe, afs, 0, test)
        except RuntimeError as e:
            return None, "Ogg illisible (%s) : garde en ADX" % e
        err = "boucle [%d, %d) au lieu de [%d, %d)" % (d2, e2, d, f) if (d2, e2) != ((d, f) if f > d else (0, 0)) \
            else controle(ref, test, n)
        if err: return None, "controle : %s : garde en ADX" % err
        shutil.move(ogg, dest)
    return dest, "encode"


def encode_tous(source, entrees, cache, travaux=None):
    """{entree: chemin Ogg ou None} pour [(entree, md5 ADX)], en parallele ; affiche un bilan"""
    exe = outil(cache)
    q = qualite()
    manque = any(not os.path.exists(os.path.join(cache, "Y%d_%s_q%s_v%s.ogg" % (i, m[:12], q, VERSION)))
                 for i, m in entrees)
    enc = encodeur(cache) if manque else None           # tout en cache : pas besoin de l'encodeur
    res, bilan = {}, {}
    with ThreadPoolExecutor(max_workers=travaux or os.cpu_count() or 2) as ex:
        futs = {i: ex.submit(encode, source, i, m, cache, exe, enc) for i, m in entrees}
        for i, fu in futs.items():
            chemin, msg = fu.result(); res[i] = chemin
            k = msg if msg in ("cache", "encode") else "ADX garde"
            bilan[k] = bilan.get(k, 0) + 1
            if k == "ADX garde": print("  Y%d : %s" % (i, msg))
    print("  Ogg Vorbis q%s : %s" % (qualite(), ", ".join("%d %s" % (v, k) for k, v in sorted(bilan.items()))))
    return res


if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    cache = os.environ.get("HSFA_OGG_CACHE") or os.path.join(tempfile.gettempdir(), "hsfa_ogg")
    src = sys.argv[1]
    ent = []
    for x in sys.argv[2:]:
        ent.append((int(x), hashlib.md5(("%s:%s" % (os.path.abspath(src), x)).encode()).hexdigest()))
    for i, c in encode_tous(src, ent, cache).items():
        print("Y%d -> %s (%d o)" % (i, c, os.path.getsize(c)) if c else "Y%d -> ADX" % i)
