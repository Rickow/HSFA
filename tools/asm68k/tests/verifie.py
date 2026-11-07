#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""verifie.py : tests de non-régression de hsfa_asm68k SANS vasm. Génère le corpus synthétique (genere.py : toutes
les instructions × tailles × modes d'adressage, valeurs limites des optimisations, branchements, directives), puis
vérifie : mêmes lignes refusées que vasm, et binaire + liste identiques (md5) à ceux de vasm (attendu.json)."""
import hashlib, json, os, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
import hsfa_asm68k  # noqa: E402


def main():
    att = json.load(open(os.path.join(ICI, "attendu.json")))
    d = tempfile.mkdtemp(prefix="asm68k_verifie_")
    subprocess.run([sys.executable, os.path.join(ICI, "genere.py"), d], check=True, stdout=subprocess.DEVNULL)
    ok = True
    cwd = os.getcwd()
    os.chdir(d)
    try:
        for f, a in att.items():
            lignes = open(f, encoding="latin-1").read().split("\n")
            r0 = hsfa_asm68k.assemble_fichier(f)
            refus = sorted({l[1] for l, num, msg in r0.erreurs})
            for n in a["refus"]:
                lignes[n - 1] = ";REFUS " + lignes[n - 1].strip()
            propre = f.replace(".s", ".propre.s")
            open(propre, "w", encoding="latin-1").write("\n".join(lignes))
            code = hsfa_asm68k.lance(["-m68000", "-spaces", "-Fbin", "-quiet", "-L", "a.lst", "-o", "a.bin", propre]).returncode
            md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
            res = (refus == a["refus"], code == 0 and md5("a.bin") == a["bin"], code == 0 and md5("a.lst") == a["lst"])
            ok &= all(res)
            print("%-26s refus %s ; binaire %s ; liste %s" % (f, *("OK" if x else "ÉCART" for x in res)))
            for p in ("a.bin", "a.lst"):
                if os.path.exists(p):
                    os.remove(p)
    finally:
        os.chdir(cwd)
    print("RÉSULTAT :", "TOUT IDENTIQUE À VASM" if ok else "ÉCARTS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
