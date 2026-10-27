#!/usr/bin/env python3
"""verifier_liens.py -- verifie les liens Markdown internes et les references de chemins de la documentation.

Pour chaque fichier .md suivi par git :
  1. liens Markdown `[texte](cible)` et images `![...](cible)` : la cible (relative au fichier) doit exister ;
     une ancre `#titre` doit correspondre a un titre du fichier vise (regle des ancres de GitHub) ;
  2. references de chemins du depot ecrites en code (`docs/...`, `tools/...`, `src/hsfa/...`, `scripts/<dossier du
     depot>/...`, `patches/...`, `legacy/...`, `max/...`) : le chemin doit exister depuis la racine du depot (ou depuis le dossier du
     fichier) ; `*` et `…` valent un joker.
Exceptions comptees a part (pas des erreurs) :
  - docs/journal/HANDOFF.md : journal historique, contenu INCHANGE (ses anciens chemins sont traduits par la table
    de docs/journal/README.md) ;
  - max/ et tools/max/ : dossiers de la session MAX, non modifies par la reorganisation ;
  - docs/journal/README.md : sa table cite volontairement les anciens chemins (ses liens restent verifies).
Usage : python3 scripts/qualite/verifier_liens.py [--detail]   (code 1 s'il reste un lien ou un chemin casse)
"""
import glob, os, re, subprocess, sys, unicodedata

RACINE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
JOURNAL = ("docs/journal/HANDOFF.md",)
# tables de correspondance qui citent volontairement les ANCIENS chemins (liens verifies, chemins en code ignores)
ANCIENS_CHEMINS = ("docs/journal/README.md",)
MAX = ("max/", "tools/max/")
LIEN = re.compile(r"!?\[(?:[^\]\[]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
CODE = re.compile(r"`([^`\n]+)`")
# src/ et scripts/ : seuls les sous-dossiers du depot sont pris (src/mame/..., src/burn/... designent les arbres des
# forks MAME / FBNeo ; scripts/untranspile est l'ancien nom de src/hsfa et doit etre signale)
CHEMIN = re.compile(r"(?<![\w/<.-])((?:\.\./)*(?:docs|tools|patches|legacy|max|src/hsfa|"
                    r"scripts/(?:validation|construction|qualite|untranspile|localiser\.py|correspondances\.tsv))"
                    r"(?:/[\w.…*/+-]*[\w*…/])?)")


def ancres(md):
    """ancres GitHub des titres d'un fichier Markdown"""
    res, vus = set(), {}
    dans_code = False
    for l in open(md, encoding="utf-8", errors="replace"):
        if l.lstrip().startswith("```"):
            dans_code = not dans_code
        if dans_code:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", l)
        if not m:
            continue
        t = re.sub(r"`([^`]*)`", r"\1", m.group(2))
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
        t = unicodedata.normalize("NFC", t).lower()
        t = "".join(c for c in t if c.isalnum() or c in " -_")
        t = t.replace(" ", "-")
        n = vus.get(t, 0); vus[t] = n + 1
        res.add(t if n == 0 else "%s-%d" % (t, n))
    return res


def existe(chemin_rel, base):
    for racine in (RACINE, base):
        c = os.path.normpath(os.path.join(racine, chemin_rel))
        if "*" in c or "…" in c:
            if glob.glob(c.replace("…", "*")):
                return True
        elif os.path.exists(c):
            return True
    return False


def main():
    detail = "--detail" in sys.argv
    mds = subprocess.run(["git", "-C", RACINE, "ls-files", "*.md"], capture_output=True, text=True,
                         check=True).stdout.split()
    cache, n_liens, n_chem = {}, 0, 0
    erreurs, journal, maxx = [], [], []
    for f in mds:
        p = os.path.join(RACINE, f)
        base = os.path.dirname(p)
        txt = open(p, encoding="utf-8", errors="replace").read()
        dest = journal if f in JOURNAL else maxx if f.startswith(MAX) else erreurs
        # 1. liens Markdown (hors blocs de code)
        sans_code = re.sub(r"```.*?```", "", txt, flags=re.S)
        for m in LIEN.finditer(sans_code):
            cible = m.group(1)
            if re.match(r"^[a-z][a-z0-9+.-]*:", cible, re.I):
                continue                                         # http:, https:, mailto:...
            n_liens += 1
            chemin, _, ancre = cible.partition("#")
            vise = os.path.normpath(os.path.join(base, chemin)) if chemin else p
            ligne = txt.count("\n", 0, txt.find(m.group(0))) + 1
            if chemin and not os.path.exists(vise):
                dest.append("%s:%d lien casse : %s" % (f, ligne, cible)); continue
            if ancre and vise.endswith(".md"):
                if vise not in cache:
                    cache[vise] = ancres(vise)
                if ancre.lower() not in cache[vise]:
                    dest.append("%s:%d ancre introuvable : %s" % (f, ligne, cible))
        # 2. references de chemins en code
        for m in (CODE.finditer(txt) if f not in ANCIENS_CHEMINS else ()):
            code = m.group(1)
            if "<" in code or "://" in code:
                continue
            for c in CHEMIN.findall(code):
                c = c.rstrip(".,;:)")
                if c.endswith("/"):
                    c = c[:-1]
                n_chem += 1
                if not existe(c, base):
                    ligne = txt.count("\n", 0, m.start()) + 1
                    dest.append("%s:%d chemin introuvable : %s" % (f, ligne, c))
    print("Fichiers Markdown : %d ; liens internes : %d ; references de chemins : %d" % (len(mds), n_liens, n_chem))
    print("Liens ou chemins casses : %d" % len(erreurs))
    print("Journal (docs/journal/HANDOFF.md, contenu inchange) : %d anciens chemins (voir docs/journal/README.md)"
          % len(journal))
    print("Exception max/ et tools/max/ (non modifies) : %d" % len(maxx))
    for e in erreurs:
        print("  " + e)
    if detail:
        for e in journal + maxx:
            print("  [exception] " + e)
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
