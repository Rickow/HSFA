#!/usr/bin/env python3
"""fige.py -- matérialise la copie figée de l'intégration MAX (integration_2b31/ : état du lot 2b31 = banc_max52,
traducteur v154 + crochets MAX, + PRETE_TEST / MEMSWAPD de la v159, + PRETE_CMP de la v160) dans un dossier de travail, en remplaçant les marques de chemins @UM_xxx@.
Une marque non donnée devient /chemin/atelier/absent/<marque> : une fuite vers l'atelier échoue au lieu de lire
silencieusement un fichier du poste de développement."""
import os, re, shutil

ICI = os.path.dirname(os.path.abspath(__file__))
FIGE = os.path.join(ICI, "integration_2b31")
MARQUES = ["@UM_AG@", "@UM_RELEVES@", "@UM_EBOOT@", "@UM_DEPOT@", "@UM_EXTRACT@", "@UM_ANIMS@", "@UM_XDATA@",
           "@UM_MAME_RO5@", "@UM_MAME@", "@UM_VASM@", "@UM_CLAUDE_CODE@", "@UM_CACHE_NON_ETIRE@", "@UM_WORK@",
           "@UM_HSFA@", "@UM_HOME@"]
TEXTE = (".py", ".sh", ".lua")


def materialiser(dest, valeurs, fige=None):
    fige = fige or FIGE; val = dict(valeurs)
    for m in MARQUES: val.setdefault(m, "/chemin/atelier/absent/" + m.strip("@"))
    cles = sorted(val, key=len, reverse=True); n = 0
    for racine, ds, fs in os.walk(fige):
        ds[:] = sorted(d for d in ds if d != "__pycache__")
        for f in sorted(fs):
            s = os.path.join(racine, f); q = os.path.join(dest, os.path.relpath(s, fige))
            os.makedirs(os.path.dirname(q), exist_ok=True)
            if f.endswith(TEXTE):
                t = open(s, encoding="utf-8", errors="surrogateescape").read()
                for m in cles: t = t.replace(m, val[m])
                open(q, "w", encoding="utf-8", errors="surrogateescape").write(t); shutil.copymode(s, q)
            else:
                shutil.copyfile(s, q)
            n += 1
    reste = sorted({m for r, _, fs in os.walk(dest) for f in fs if f.endswith(TEXTE)
                    for m in re.findall(r"@UM_[A-Z_]+@", open(os.path.join(r, f), errors="replace").read())})
    if reste: raise SystemExit("marques non remplacées : %s" % ", ".join(reste))
    return n
