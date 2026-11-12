#!/usr/bin/env python3
"""liens.py -- liens portables pour la construction (Windows : os.symlink exige le mode developpeur ou les droits
d'administrateur, sinon « OSError: [WinError 1314] A required privilege is not held by the client »).

  lien(cible, chemin)            comme os.symlink(cible, chemin) ; une cible relative l'est au dossier de « chemin »
  lien_si_absent(cible, chemin)  idem si « chemin » n'existe pas encore (une copie perimee est refaite)
  reel(chemin)                   comme os.path.realpath, en suivant aussi les copies faites a la place d'un lien

Procedes, dans l'ordre (rend le nom de celui employe) :
  1. "symbolique" : lien symbolique, exactement comme avant (Linux, macOS, Windows en mode developpeur) ;
  2. dossier : "jonction" NTFS (Windows : _winapi.CreateJunction, sinon « mklink /J »), sans droit particulier ;
     fichier : "copie" (shutil.copy2, date gardee).
Pas de lien physique pour un fichier : du code qui fait « si islink : unlink » avant d'ecrire (greffe3, f545.bin)
ecrirait sinon DANS la cible (constate : banque f545 d'Hyper modifiee par la greffe, essai du 11/11). Les fichiers
lies ne sont que lus par la construction : la copie donne les memes octets. Chaque copie est notee dans le fichier
REGISTRE de son dossier (nom, cible, taille, date) : reel() la suit tant qu'elle n'a pas ete reecrite, pour que
paquet_fbneo ecrive dans hsfa_info.txt la meme source qu'avec un lien symbolique (realpath).
Un dossier n'est jamais copie (son contenu est souvent ecrit APRES la creation du lien, et ~/.cache/sfa3max -> R se
contient lui-meme) : sans jonction possible (cle exFAT / FAT32, partage reseau), erreur explicite.

HSFA_SANS_LIENS=1 (essai, sous Linux / macOS, de la voie Windows sans droit de lien symbolique) : jamais de lien
symbolique de fichier (copie) ; dossier : « jonction simulee » = lien symbolique vers le chemin ABSOLU de la cible (ce
qu'est une jonction). Sous Windows, HSFA_SANS_LIENS=1 saute l'essai du lien symbolique (jonction / copie d'emblee).
"""
import os, shutil, subprocess

PROCEDES = ("symbolique", "jonction", "copie")
REGISTRE = ".hsfa_liens"          # dans le dossier d'une copie : « nom TAB cible TAB taille TAB date_ns »


def _mode():
    m = os.environ.get("HSFA_SANS_LIENS", "").strip().lower()
    return "" if m in ("", "0") else m


def _absolue(cible, chemin):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(chemin)), cible))


def est_jonction(chemin):
    f = getattr(os.path, "isjunction", None)            # Python 3.12+
    return bool(f and f(chemin))


def _jonction(cible_abs, chemin):
    if os.name == "nt":
        try:
            import _winapi
            _winapi.CreateJunction(cible_abs, chemin)
            return
        except (ImportError, AttributeError, OSError) as x:
            err = x
        r = subprocess.run(["cmd", "/c", "mklink", "/J", chemin, cible_abs], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        if r.returncode == 0 and os.path.isdir(chemin):
            return
        raise OSError("jonction impossible %s -> %s (%s ; mklink /J : %s). Il faut un disque NTFS (pas une cle exFAT / "
                      "FAT32 ni un partage reseau), ou activer le mode developpeur de Windows (liens symboliques)."
                      % (chemin, cible_abs, err, r.stdout.decode("oem", "replace").strip()))
    os.symlink(cible_abs, chemin, target_is_directory=True)   # essai POSIX : jonction simulee (cible absolue)


def _copie(cible_abs, chemin):
    shutil.copy2(cible_abs, chemin)
    st = os.stat(chemin)
    with open(os.path.join(os.path.dirname(os.path.abspath(chemin)), REGISTRE), "a", encoding="utf-8", newline="\n") as f:
        f.write("%s\t%s\t%d\t%d\n" % (os.path.basename(chemin), cible_abs, st.st_size, st.st_mtime_ns))


def lien(cible, chemin):
    """cree « chemin » qui designe « cible » ; rend le procede employe (PROCEDES)"""
    mode = _mode(); cible_abs = _absolue(cible, chemin)
    if not mode:
        try:
            if os.name == "nt":                              # type du lien = type de la cible (dossier / fichier)
                os.symlink(cible, chemin, target_is_directory=os.path.isdir(cible_abs))
            else:
                os.symlink(cible, chemin)
            return "symbolique"
        except (FileExistsError, FileNotFoundError):
            raise                                            # memes erreurs qu'os.symlink : rien a contourner
        except (OSError, NotImplementedError, AttributeError):
            pass                                             # WinError 1314, EPERM (FAT), ... : autre procede
    if os.path.lexists(chemin):
        raise FileExistsError(17, "existe deja", chemin)
    if os.path.isdir(cible_abs):
        _jonction(cible_abs, chemin)
        return "jonction"
    if not os.path.isfile(cible_abs):
        raise FileNotFoundError(2, "cible absente (lien %s ; sans lien symbolique, la cible doit exister)" % chemin,
                                cible_abs)
    _copie(cible_abs, chemin)
    return "copie"


def _note(chemin):
    """(cible, taille, date_ns) de la derniere copie notee pour « chemin », ou None"""
    p = os.path.join(os.path.dirname(chemin), REGISTRE); nom = os.path.basename(chemin); r = None
    try:
        with open(p, encoding="utf-8") as f:
            for l in f:
                c = l.rstrip("\n").split("\t")
                if len(c) == 4 and c[0] == nom:
                    r = (c[1], int(c[2]), int(c[3]))
    except OSError:
        pass
    return r


def lien_si_absent(cible, chemin):
    """comme « os.path.lexists(chemin) or os.symlink(cible, chemin) » ; une copie presente qui n'est plus a jour
    (cible plus recente ou de taille differente) est refaite. Rend le procede employe, ou None si rien n'a ete fait."""
    if os.path.lexists(chemin):
        if os.path.islink(chemin) or est_jonction(chemin) or os.path.isdir(chemin):
            return None
        try:
            a, b = os.stat(chemin), os.stat(_absolue(cible, chemin))   # copy2 garde la date de la cible
            if a.st_size == b.st_size and a.st_mtime_ns == b.st_mtime_ns:
                return None
        except OSError:
            pass
        os.remove(chemin)
    return lien(cible, chemin)


def reel(chemin):
    """os.path.realpath(chemin), puis, tant que le resultat est une copie notee (et non reecrite depuis), sa cible"""
    p = os.path.realpath(chemin)
    for _ in range(40):
        n = _note(p)
        if not n:
            break
        try:
            st = os.stat(p)
        except OSError:
            break
        if (st.st_size, st.st_mtime_ns) != n[1:]:
            break                                            # copie reecrite depuis (greffe3 : f545.bin, plan2.bin)
        p = os.path.realpath(n[0])
    return p
