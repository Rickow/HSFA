#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""fabrique_attendu.py VASM : (maintenance, demande vasm) fabrique attendu.json pour verifie.py.
Pour chaque source générée par genere.py : lignes refusées par vasm (mises en commentaire, itérativement), puis md5 du
binaire et de la liste produits par vasm sur la source nettoyée (nom relatif, dossier temporaire)."""
import hashlib, json, os, re, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIERS = ["s01_deux.s", "s02_imm.s", "s03_un.s", "s04_divers.s", "s05_bas.s", "s06b_branches_isoles.s", "s07_chaines.s",
            "s08_donnees.s", "s09_directives.s"]
MSG = re.compile(r"^(?:fatal )?error (\d+) in line (\d+) of")


def main():
    vasm = sys.argv[1]
    d = tempfile.mkdtemp(prefix="asm68k_attendu_")
    subprocess.run([sys.executable, os.path.join(ICI, "genere.py"), d], check=True, stdout=subprocess.DEVNULL)
    res = {}
    for f in FICHIERS:
        lignes = open(os.path.join(d, f), encoding="latin-1").read().split("\n")
        refus = {}
        propre = f.replace(".s", ".propre.s")
        while True:
            open(os.path.join(d, propre), "w", encoding="latin-1").write("\n".join(lignes))
            r = subprocess.run([vasm, "-m68000", "-spaces", "-Fbin", "-quiet", "-maxerrors=1000000", "-L", "a.lst", "-o",
                                "a.bin", propre], cwd=d, capture_output=True, text=True, errors="replace")
            e = [(int(m.group(2)), int(m.group(1))) for m in map(MSG.match, (r.stdout + r.stderr).splitlines()) if m]
            if not e:
                break
            for n, num in e:
                refus[n] = num
                lignes[n - 1] = ";REFUS " + lignes[n - 1].strip()
        md5 = lambda p: hashlib.md5(open(os.path.join(d, p), "rb").read()).hexdigest()
        res[f] = {"refus": sorted(refus), "bin": md5("a.bin"), "lst": md5("a.lst"), "lignes": len(lignes)}
        print(f, len(refus), "refusées", res[f]["bin"][:8], res[f]["lst"][:8])
    json.dump(res, open(os.path.join(ICI, "attendu.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
